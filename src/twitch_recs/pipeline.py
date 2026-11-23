from __future__ import annotations

import itertools
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy import sparse

from .data import (DaySplit, chronological_split, encode_fit_period,
                   interaction_count_matrix, load_interactions, make_evaluation_labels,
                   recent_item_mask, save_split)
from .eda import create_eda, dataset_summary
from .metrics import (channel_popularity_subgroups, complementarity, evaluate_ranking,
                      user_history_subgroups)
from .models import BPR, ItemKNN
from .recommend import (personalized_recommendations, popularity_recommendations,
                        single_model_recommendations)
from .reporting import create_results_plot, render_report


def _json_dump(value, path: Path) -> None:
    path.write_text(json.dumps(value, indent=2, default=str), encoding="utf-8")


def _evaluation_users(labels: pd.DataFrame, maximum: int | None, seed: int) -> np.ndarray:
    users = np.sort(labels["user_idx"].unique()).astype(np.int32)
    if maximum is not None and len(users) > maximum:
        users = np.sort(np.random.default_rng(seed).choice(users, size=maximum, replace=False))
    return users


def _labels_for_users(labels: pd.DataFrame, users: np.ndarray) -> pd.DataFrame:
    return labels.loc[labels["user_idx"].isin(users)].copy()


def _recent_popularity(fit, end_day: int, days: int) -> np.ndarray:
    recent = fit.frame.loc[fit.frame["day"].between(end_day - days + 1, end_day)]
    counts = recent[["user_idx", "item_idx"]].drop_duplicates().groupby("item_idx").size()
    result = np.zeros(fit.matrix.shape[1], dtype=np.float32)
    result[counts.index.to_numpy(dtype=int)] = counts.to_numpy(dtype=np.float32)
    return result


def _evaluate(name: str, recs: pd.DataFrame, labels: pd.DataFrame, fit, config: dict,
              case_dir: Path | None = None) -> dict:
    cases, summary = evaluate_ranking(
        recs, labels, k=config["model"]["top_k"], popularity=fit.popularity,
        catalog_size=fit.matrix.shape[1],
        long_tail_quantile=config["evaluation"]["long_tail_quantile"],
    )
    summary["model"] = name
    if case_dir is not None:
        cases.to_csv(case_dir / f"cases_{name}.csv", index=False)
    return summary


def _tune_models(fit, labels: pd.DataFrame, users: np.ndarray, config: dict,
                 output_dir: Path):
    k = config["model"]["top_k"]
    rows: list[dict] = []
    pop_recs = popularity_recommendations(users, fit.matrix, fit.popularity, k)
    rows.append(_evaluate("popularity", pop_recs, labels, fit, config))
    recent_pop = _recent_popularity(fit, int(fit.frame["day"].max()), config["model"]["recent_days"])
    recent_recs = popularity_recommendations(users, fit.matrix, recent_pop, k)
    rows.append(_evaluate("recent_popularity", recent_recs, labels, fit, config))

    best_cf = None
    best_cf_score = -np.inf
    best_cf_params = None
    best_cf_recs = None
    for neighbors in config["model"]["item_knn_neighbors"]:
        model = ItemKNN(neighbors, config["model"]["item_knn_batch_size"]).fit(fit.matrix)
        recs = single_model_recommendations(
            users, fit.matrix, lambda u, m=model: m.score_user(fit.matrix[u]), k
        )
        summary = _evaluate(f"item_knn_k{neighbors}", recs, labels, fit, config)
        rows.append(summary)
        if summary["ndcg_at_10"] > best_cf_score:
            best_cf_score, best_cf, best_cf_params, best_cf_recs = (
                summary["ndcg_at_10"], model, {"neighbors": neighbors}, recs
            )

    best_bpr = None
    best_bpr_score = -np.inf
    best_bpr_params = None
    best_bpr_recs = None
    bpr_grid = itertools.product(
        config["model"]["bpr_factors"], config["model"]["bpr_learning_rates"],
        config["model"]["bpr_regularizations"], config["model"]["bpr_epochs"],
    )
    for factors, lr, reg, epochs in bpr_grid:
        params = {"factors": factors, "learning_rate": lr, "regularization": reg,
                  "epochs": epochs, "negative_samples": config["model"]["bpr_negative_samples"],
                  "seed": config["seed"]}
        model = BPR(**params).fit(fit.matrix)
        recs = single_model_recommendations(users, fit.matrix, model.score_user, k)
        name = f"bpr_f{factors}_r{reg:g}_e{epochs}"
        summary = _evaluate(name, recs, labels, fit, config)
        rows.append(summary)
        if summary["ndcg_at_10"] > best_bpr_score:
            best_bpr_score, best_bpr, best_bpr_params, best_bpr_recs = (
                summary["ndcg_at_10"], model, params, recs
            )

    hybrid_recs = personalized_recommendations(
        users, fit.matrix, best_cf, best_bpr, fit.popularity, k,
        config["model"]["alphas"], config["model"]["popularity_lambdas"],
    )
    best_hybrid_name, best_hybrid_score = None, -np.inf
    for name, recs in hybrid_recs.items():
        if name in ("item_knn", "bpr"):
            continue
        summary = _evaluate(name, recs, labels, fit, config)
        rows.append(summary)
        if summary["ndcg_at_10"] > best_hybrid_score:
            best_hybrid_name, best_hybrid_score = name, summary["ndcg_at_10"]

    validation = pd.DataFrame(rows).sort_values("ndcg_at_10", ascending=False)
    validation.to_csv(output_dir / "tables" / "validation_grid.csv", index=False)
    selected = {"item_knn": best_cf_params, "bpr": best_bpr_params,
                "hybrid_model_name": best_hybrid_name}
    return selected, validation, best_cf_recs, best_bpr_recs


def _parse_hybrid_name(name: str) -> tuple[float, float]:
    pieces = name.split("_")
    alpha = float(next(piece[1:] for piece in pieces if piece.startswith("a")))
    penalty = float(next((piece[1:] for piece in pieces if piece.startswith("p")), 0.0))
    return alpha, penalty


def run_experiment(config: dict) -> dict:
    output_dir = Path(config["outputs_dir"])
    (output_dir / "tables").mkdir(parents=True, exist_ok=True)
    (output_dir / "figures").mkdir(parents=True, exist_ok=True)
    raw_path = Path(config["data"]["raw_path"])
    frame = load_interactions(raw_path, config["split"]["slots_per_day"])
    summary = dataset_summary(frame)
    _json_dump(summary, output_dir / "dataset_summary.json")
    create_eda(frame, output_dir)
    split = chronological_split(frame, config["split"]["train_fraction"],
                                config["split"]["validation_fraction"])
    save_split(split, output_dir / "split.json")

    train_fit = encode_fit_period(frame, split.train_days)
    val_labels, val_coverage = make_evaluation_labels(frame, train_fit, split.validation_days)
    val_users = _evaluation_users(val_labels, config["evaluation"]["max_validation_users"], config["seed"])
    val_labels_eval = _labels_for_users(val_labels, val_users)
    selected, validation, val_cf_recs, val_bpr_recs = _tune_models(
        train_fit, val_labels_eval, val_users, config, output_dir
    )
    _json_dump(val_coverage, output_dir / "validation_candidate_coverage.json")

    final_days = np.concatenate([split.train_days, split.validation_days])
    final_fit = encode_fit_period(frame, final_days)
    pd.DataFrame({"item_idx": np.arange(len(final_fit.item_names)),
                  "channel": final_fit.item_names}).to_csv(
        output_dir / "tables" / "item_mapping.csv", index=False)
    pd.DataFrame({"user_idx": np.arange(len(final_fit.user_names)),
                  "user_id": final_fit.user_names}).to_csv(
        output_dir / "tables" / "user_mapping.csv", index=False)
    test_labels, test_coverage = make_evaluation_labels(frame, final_fit, split.test_days)
    test_users = _evaluation_users(test_labels, config["evaluation"]["max_test_users"], config["seed"])
    test_labels_eval = _labels_for_users(test_labels, test_users)
    k = config["model"]["top_k"]
    cf = ItemKNN(selected["item_knn"]["neighbors"],
                 config["model"]["item_knn_batch_size"]).fit(final_fit.matrix)
    bpr = BPR(**selected["bpr"]).fit(final_fit.matrix)
    alpha, penalty = _parse_hybrid_name(selected["hybrid_model_name"])
    penalties = sorted(set([0.0, penalty]))
    personalized = personalized_recommendations(
        test_users, final_fit.matrix, cf, bpr, final_fit.popularity, k,
        alphas=[alpha], lambdas=penalties,
    )
    recs_by_name = {
        "popularity": popularity_recommendations(test_users, final_fit.matrix, final_fit.popularity, k),
        "recent_popularity": popularity_recommendations(
            test_users, final_fit.matrix,
            _recent_popularity(final_fit, split.validation_end, config["model"]["recent_days"]), k),
        "item_knn": personalized["item_knn"],
        "bpr": personalized["bpr"],
        f"hybrid_a{alpha:g}": personalized[f"hybrid_a{alpha:g}"],
    }
    if penalty > 0:
        adjusted_name = f"hybrid_a{alpha:g}_p{penalty:g}"
        recs_by_name[adjusted_name] = personalized[adjusted_name]

    # Supplemental comparison requested in the plan: preserve repeated viewing
    # counts instead of binarizing feedback for item-item similarity and scoring.
    count_matrix = interaction_count_matrix(final_fit)
    count_cf = ItemKNN(selected["item_knn"]["neighbors"],
                       config["model"]["item_knn_batch_size"]).fit(count_matrix)
    recs_by_name["item_knn_count_weighted"] = single_model_recommendations(
        test_users, final_fit.matrix,
        lambda u: count_cf.score_user(count_matrix[u]), k,
    )

    test_rows = []
    case_dir = output_dir / "tables"
    for name, recs in recs_by_name.items():
        test_rows.append(_evaluate(name, recs, test_labels_eval, final_fit, config, case_dir))
        named = recs.copy()
        named["user_id"] = final_fit.user_names[named["user_idx"].to_numpy(dtype=int)]
        named["channel"] = final_fit.item_names[named["item_idx"].to_numpy(dtype=int)]
        named.to_csv(output_dir / "tables" / f"recommendations_{name}.csv", index=False)
        if name == selected["hybrid_model_name"]:
            example_users = named["user_idx"].drop_duplicates().head(5)
            named.loc[named["user_idx"].isin(example_users)].to_csv(
                output_dir / "tables" / "recommendation_examples.csv", index=False)
    test_results = pd.DataFrame(test_rows).sort_values("ndcg_at_10", ascending=False)
    test_results.to_csv(output_dir / "tables" / "test_results.csv", index=False)
    create_results_plot(test_results, output_dir / "figures" / "test_accuracy.png")
    _json_dump(test_coverage, output_dir / "test_candidate_coverage.json")
    _json_dump(selected, output_dir / "selected_hyperparameters.json")

    # Subgroup analysis is anchored to the validation-selected hybrid, not selected
    # after inspecting which row happened to win on test.
    analysis_name = selected["hybrid_model_name"]
    best_recs = recs_by_name[analysis_name]
    best_cases, _ = evaluate_ranking(best_recs, test_labels_eval, k, final_fit.popularity,
                                     final_fit.matrix.shape[1], config["evaluation"]["long_tail_quantile"])
    user_history_subgroups(best_cases, final_fit.matrix).to_csv(
        output_dir / "tables" / "user_history_subgroups.csv", index=False)
    channel_popularity_subgroups(best_recs, test_labels_eval, final_fit.popularity, k).to_csv(
        output_dir / "tables" / "channel_popularity_subgroups.csv", index=False)
    comp = complementarity(test_labels_eval, recs_by_name["bpr"], recs_by_name["item_knn"])
    _json_dump(comp, output_dir / "model_complementarity.json")

    active_mask = recent_item_mask(frame, final_fit, split.validation_end,
                                   config["model"]["recent_days"])
    active_hits = int(active_mask[test_labels_eval["item_idx"].to_numpy(dtype=int)].sum())
    active_conditional_coverage = float(active_hits / len(test_labels_eval))
    active_overall_coverage = (
        float(active_hits / test_coverage["novel_user_channel_positives"])
        if config["evaluation"]["max_test_users"] is None else float("nan")
    )
    active_personalized = personalized_recommendations(
        test_users, final_fit.matrix, cf, bpr, final_fit.popularity, k,
        alphas=[alpha], lambdas=penalties, candidate_mask=active_mask,
    )
    active_recs = {
        "popularity_active_7d": popularity_recommendations(
            test_users, final_fit.matrix, final_fit.popularity, k, active_mask),
        "item_knn_active_7d": active_personalized["item_knn"],
        "bpr_active_7d": active_personalized["bpr"],
        f"hybrid_a{alpha:g}_active_7d": active_personalized[f"hybrid_a{alpha:g}"],
    }
    if penalty > 0:
        active_recs[f"hybrid_a{alpha:g}_p{penalty:g}_active_7d"] = active_personalized[
            f"hybrid_a{alpha:g}_p{penalty:g}"
        ]
    active_rows = []
    for name, recs in active_recs.items():
        row = _evaluate(name, recs, test_labels_eval, final_fit, config)
        row["coverage_within_primary_catalog"] = active_conditional_coverage
        row["overall_positive_candidate_coverage"] = active_overall_coverage
        active_rows.append(row)
    pd.DataFrame(active_rows).sort_values("ndcg_at_10", ascending=False).to_csv(
        output_dir / "tables" / "active_7d_results.csv", index=False)
    _json_dump({"coverage_within_primary_catalog": active_conditional_coverage,
                "overall_positive_candidate_coverage": active_overall_coverage},
               output_dir / "active_7d_experiment.json")

    split_payload = json.loads((output_dir / "split.json").read_text(encoding="utf-8"))
    report = render_report(output_dir, summary, split_payload, validation, test_results,
                           val_coverage, test_coverage, selected, comp)
    versions = {"python": sys.version, "platform": platform.platform(), "numpy": np.__version__,
                "pandas": pd.__version__, "scipy": scipy.__version__}
    _json_dump(versions, output_dir / "versions.json")
    return {"report": str(report), "selected": selected,
            "test_results": test_results.to_dict(orient="records")}


def finalize_existing_experiment(config: dict) -> dict:
    """Rebuild only the optional active-catalog analysis and final report.

    This recovery entry point intentionally requires completed primary artifacts. It
    is useful after a report/rendering failure and does not rerun or overwrite the
    validation grid or primary test recommendations.
    """
    output_dir = Path(config["outputs_dir"])
    required = [
        output_dir / "dataset_summary.json", output_dir / "split.json",
        output_dir / "selected_hyperparameters.json",
        output_dir / "validation_candidate_coverage.json",
        output_dir / "test_candidate_coverage.json",
        output_dir / "model_complementarity.json",
        output_dir / "tables" / "validation_grid.csv",
        output_dir / "tables" / "test_results.csv",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Cannot finalize; missing primary artifacts: {missing}")

    selected = json.loads((output_dir / "selected_hyperparameters.json").read_text())
    split_payload = json.loads((output_dir / "split.json").read_text())
    frame = load_interactions(config["data"]["raw_path"], config["split"]["slots_per_day"])
    final_days = np.asarray(split_payload["train_days"] + split_payload["validation_days"])
    test_days = np.asarray(split_payload["test_days"])
    final_fit = encode_fit_period(frame, final_days)
    pd.DataFrame({"item_idx": np.arange(len(final_fit.item_names)),
                  "channel": final_fit.item_names}).to_csv(
        output_dir / "tables" / "item_mapping.csv", index=False)
    pd.DataFrame({"user_idx": np.arange(len(final_fit.user_names)),
                  "user_id": final_fit.user_names}).to_csv(
        output_dir / "tables" / "user_mapping.csv", index=False)
    test_labels, _ = make_evaluation_labels(frame, final_fit, test_days)
    test_users = _evaluation_users(test_labels, config["evaluation"]["max_test_users"], config["seed"])
    test_labels = _labels_for_users(test_labels, test_users)
    k = config["model"]["top_k"]
    cf = ItemKNN(selected["item_knn"]["neighbors"],
                 config["model"]["item_knn_batch_size"]).fit(final_fit.matrix)
    bpr = BPR(**selected["bpr"]).fit(final_fit.matrix)
    alpha, penalty = _parse_hybrid_name(selected["hybrid_model_name"])
    penalties = sorted(set([0.0, penalty]))
    active_mask = recent_item_mask(
        frame, final_fit, int(split_payload["validation_end_day"]), config["model"]["recent_days"]
    )
    active_hits = int(active_mask[test_labels["item_idx"].to_numpy(dtype=int)].sum())
    active_conditional_coverage = float(active_hits / len(test_labels))
    test_coverage = json.loads((output_dir / "test_candidate_coverage.json").read_text())
    active_overall_coverage = (
        float(active_hits / test_coverage["novel_user_channel_positives"])
        if config["evaluation"]["max_test_users"] is None else float("nan")
    )
    personalized = personalized_recommendations(
        test_users, final_fit.matrix, cf, bpr, final_fit.popularity, k,
        alphas=[alpha], lambdas=penalties, candidate_mask=active_mask,
    )
    active_recs = {
        "popularity_active_7d": popularity_recommendations(
            test_users, final_fit.matrix, final_fit.popularity, k, active_mask),
        "item_knn_active_7d": personalized["item_knn"],
        "bpr_active_7d": personalized["bpr"],
        f"hybrid_a{alpha:g}_active_7d": personalized[f"hybrid_a{alpha:g}"],
    }
    if penalty > 0:
        active_recs[f"hybrid_a{alpha:g}_p{penalty:g}_active_7d"] = personalized[
            f"hybrid_a{alpha:g}_p{penalty:g}"
        ]
    active_rows = []
    for name, recs in active_recs.items():
        row = _evaluate(name, recs, test_labels, final_fit, config)
        row["coverage_within_primary_catalog"] = active_conditional_coverage
        row["overall_positive_candidate_coverage"] = active_overall_coverage
        active_rows.append(row)
    active_results = pd.DataFrame(active_rows).sort_values("ndcg_at_10", ascending=False)
    active_results.to_csv(output_dir / "tables" / "active_7d_results.csv", index=False)
    _json_dump({"coverage_within_primary_catalog": active_conditional_coverage,
                "overall_positive_candidate_coverage": active_overall_coverage},
               output_dir / "active_7d_experiment.json")

    report = render_report(
        output_dir,
        json.loads((output_dir / "dataset_summary.json").read_text()), split_payload,
        pd.read_csv(output_dir / "tables" / "validation_grid.csv"),
        pd.read_csv(output_dir / "tables" / "test_results.csv"),
        json.loads((output_dir / "validation_candidate_coverage.json").read_text()),
        json.loads((output_dir / "test_candidate_coverage.json").read_text()),
        selected, json.loads((output_dir / "model_complementarity.json").read_text()),
    )
    versions = {"python": sys.version, "platform": platform.platform(), "numpy": np.__version__,
                "pandas": pd.__version__, "scipy": scipy.__version__}
    _json_dump(versions, output_dir / "versions.json")
    return {"report": str(report), "active_results": active_results.to_dict(orient="records")}
