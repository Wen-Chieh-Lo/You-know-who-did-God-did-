from __future__ import annotations

import gc
import json
import re
import subprocess
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .data import COLUMNS, encode_fit_period, load_interactions, make_evaluation_labels
from .metrics import evaluate_ranking
from .models import BPR, ItemKNN
from .recommend import (personalized_recommendations, popularity_recommendations,
                        single_model_recommendations)


METRICS = ("recall_at_10", "ndcg_at_10", "hit_rate_at_10")


def paired_user_bootstrap(
    left: pd.DataFrame,
    right: pd.DataFrame,
    left_name: str,
    right_name: str,
    samples: int = 10_000,
    seed: int = 258,
    batch_size: int = 50,
    metrics: tuple[str, ...] = METRICS,
    keys: tuple[str, ...] | None = None,
) -> list[dict]:
    """Paired cluster bootstrap, resampling users and retaining all their day cases."""
    merge_keys = list(keys or (("user_idx", "day") if "day" in left.columns else ("user_idx",)))
    needed = merge_keys + list(metrics)
    merged = left[needed].merge(right[needed], on=merge_keys, suffixes=("_left", "_right"),
                                validate="one_to_one")
    if len(merged) != len(left) or len(merged) != len(right):
        raise ValueError(f"Case mismatch for {left_name} and {right_name}")
    differences = pd.DataFrame({
        "user_idx": merged["user_idx"],
        **{metric: merged[f"{metric}_left"] - merged[f"{metric}_right"]
           for metric in metrics},
    })
    grouped = differences.groupby("user_idx", sort=True)
    sums = grouped[list(metrics)].sum().to_numpy(dtype=np.float64)
    counts = grouped.size().to_numpy(dtype=np.float64)
    n_users = len(sums)
    rng = np.random.default_rng(seed)
    draws = np.empty((samples, len(metrics)), dtype=np.float64)
    offset = 0
    while offset < samples:
        take = min(batch_size, samples - offset)
        sampled = rng.integers(0, n_users, size=(take, n_users))
        denominator = counts[sampled].sum(axis=1)
        draws[offset:offset + take] = sums[sampled].sum(axis=1) / denominator[:, None]
        offset += take
    rows = []
    for column, metric in enumerate(metrics):
        values = draws[:, column]
        lower, upper = np.quantile(values, [0.025, 0.975])
        nonpositive = int(np.count_nonzero(values <= 0))
        nonnegative = int(np.count_nonzero(values >= 0))
        p_value = min(1.0, 2.0 * (min(nonpositive, nonnegative) + 1) / (samples + 1))
        rows.append({
            "left_model": left_name,
            "right_model": right_name,
            "metric": metric,
            "cases": len(merged),
            "users": n_users,
            "point_difference": float(differences[metric].mean()),
            "ci_95_lower": float(lower),
            "ci_95_upper": float(upper),
            "two_sided_p_value": float(p_value),
            "bootstrap_samples": samples,
            "cluster_unit": "user_idx",
        })
    return rows


def add_holm_correction(frame: pd.DataFrame, p_column: str = "two_sided_p_value") -> pd.DataFrame:
    """Add family-wise Holm adjusted p-values without an optional stats dependency."""
    result = frame.copy()
    values = result[p_column].to_numpy(dtype=float)
    order = np.argsort(values)
    adjusted = np.empty(len(values), dtype=float)
    running = 0.0
    total = len(values)
    for rank, index in enumerate(order):
        running = max(running, (total - rank) * values[index])
        adjusted[index] = min(1.0, running)
    result["holm_adjusted_p"] = adjusted
    result["significant_after_holm_0_05"] = adjusted < 0.05
    return result


def run_bootstrap(primary_output: Path, assignment_output: Path, samples: int,
                  seed: int) -> pd.DataFrame:
    case_dir = primary_output / "tables"
    comparisons = [
        ("hybrid_a0.75", "item_knn"),
        ("hybrid_a0.75", "bpr"),
        ("hybrid_a0.75", "recent_popularity"),
        ("item_knn", "item_knn_count_weighted"),
    ]
    rows: list[dict] = []
    for index, (left_name, right_name) in enumerate(comparisons):
        left = pd.read_csv(case_dir / f"cases_{left_name}.csv")
        right = pd.read_csv(case_dir / f"cases_{right_name}.csv")
        rows.extend(paired_user_bootstrap(
            left, right, left_name, right_name, samples, seed + index, batch_size=50
        ))
    result = add_holm_correction(pd.DataFrame(rows))
    result.to_csv(assignment_output / "tables" / "bootstrap_significance.csv", index=False)
    return result


def _recent_popularity(fit, end_day: int, days: int) -> np.ndarray:
    recent = fit.frame.loc[fit.frame["day"].between(end_day - days + 1, end_day)]
    counts = recent[["user_idx", "item_idx"]].drop_duplicates().groupby("item_idx").size()
    values = np.zeros(fit.matrix.shape[1], dtype=np.float32)
    values[counts.index.to_numpy(dtype=int)] = counts.to_numpy(dtype=np.float32)
    return values


def _evaluate(name: str, recommendations: pd.DataFrame, labels: pd.DataFrame,
              fit, config: dict) -> dict:
    _, row = evaluate_ranking(
        recommendations, labels, config["model"]["top_k"], fit.popularity,
        fit.matrix.shape[1], config["evaluation"]["long_tail_quantile"],
    )
    row["model"] = name
    return row


def run_rolling_backtest(frame: pd.DataFrame, config: dict, assignment_output: Path,
                         folds: list[dict]) -> pd.DataFrame:
    selected = json.loads((Path(config["outputs_dir"]) /
                           "selected_hyperparameters.json").read_text())
    alpha_match = re.search(r"_a([0-9.]+)", selected["hybrid_model_name"])
    if alpha_match is None:
        raise ValueError("Cannot parse selected hybrid alpha")
    alpha = float(alpha_match.group(1))
    top_k = int(config["model"]["top_k"])
    all_rows: list[dict] = []
    coverage_rows: list[dict] = []
    for fold in folds:
        started = time.time()
        fit_end = int(fold["fit_end_day"])
        target_start = int(fold["target_start_day"])
        target_end = int(fold["target_end_day"])
        fit = encode_fit_period(frame, np.arange(0, fit_end + 1, dtype=np.int16))
        target_days = np.arange(target_start, target_end + 1, dtype=np.int16)
        labels, coverage = make_evaluation_labels(frame, fit, target_days)
        users = np.sort(labels["user_idx"].unique()).astype(np.int32)
        cf = ItemKNN(selected["item_knn"]["neighbors"],
                     config["model"]["item_knn_batch_size"]).fit(fit.matrix)
        bpr = BPR(**selected["bpr"]).fit(fit.matrix)
        personalized = personalized_recommendations(
            users, fit.matrix, cf, bpr, fit.popularity, top_k, [alpha], [0.0]
        )
        recent_popularity = _recent_popularity(
            fit, fit_end, int(config["model"]["recent_days"])
        )
        recommendations = {
            "popularity": popularity_recommendations(
                users, fit.matrix, fit.popularity, top_k),
            "recent_popularity": popularity_recommendations(
                users, fit.matrix, recent_popularity, top_k),
            "item_knn": personalized["item_knn"],
            "bpr": personalized["bpr"],
            f"hybrid_a{alpha:g}": personalized[f"hybrid_a{alpha:g}"],
        }
        for name, recs in recommendations.items():
            row = _evaluate(name, recs, labels, fit, config)
            row.update({
                "fold": str(fold["name"]),
                "fit_days": f"0-{fit_end}",
                "target_days": f"{target_start}-{target_end}",
            })
            all_rows.append(row)
        coverage_rows.append({
            "fold": str(fold["name"]),
            "fit_days": f"0-{fit_end}",
            "target_days": f"{target_start}-{target_end}",
            **coverage,
            "evaluated_users": len(users),
            "elapsed_seconds": round(time.time() - started, 2),
        })
        del fit, labels, cf, bpr, personalized, recommendations
        gc.collect()
    primary_output = Path(config["outputs_dir"])
    late_results = pd.read_csv(primary_output / "tables" / "test_results.csv")
    late_models = {"popularity", "recent_popularity", "item_knn", "bpr",
                   selected["hybrid_model_name"]}
    late_results = late_results.loc[late_results["model"].isin(late_models)].copy()
    late_results["fold"] = "late"
    late_results["fit_days"] = "0-35"
    late_results["target_days"] = "36-42"
    all_rows.extend(late_results.to_dict("records"))
    late_coverage = json.loads((primary_output / "test_candidate_coverage.json").read_text())
    coverage_rows.append({
        "fold": "late", "fit_days": "0-35", "target_days": "36-42",
        **late_coverage,
        "evaluated_users": int(late_results["users"].iloc[0]),
        "elapsed_seconds": np.nan,
    })
    results = pd.DataFrame(all_rows)
    results.to_csv(assignment_output / "tables" / "rolling_backtest.csv", index=False)
    pd.DataFrame(coverage_rows).to_csv(
        assignment_output / "tables" / "rolling_backtest_coverage.csv", index=False
    )
    return results


def data_quality_audit(frame: pd.DataFrame, output: Path) -> dict:
    raw = frame[COLUMNS]
    audit = {
        "rows": int(len(frame)),
        "missing_cells": int(raw.isna().sum().sum()),
        "exact_duplicate_rows": int(raw.duplicated().sum()),
        "stop_before_start": int((frame["time_stop"] < frame["time_start"]).sum()),
        "zero_duration_rows": int((frame["time_stop"] == frame["time_start"]).sum()),
        "nonpositive_user_ids": int((pd.to_numeric(frame["user_id"], errors="coerce") <= 0).sum()),
        "blank_channel_names": int(frame["channel"].str.strip().eq("").sum()),
    }
    output.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return audit


def full_novel_targets(frame: pd.DataFrame, fit, target_days: np.ndarray) -> pd.DataFrame:
    """Return first novel user-channel events, retaining catalog-cold channels."""
    target = frame.loc[
        frame["day"].isin(target_days),
        ["user_id", "channel", "day", "time_start"],
    ].copy()
    user_map = pd.Series(np.arange(len(fit.user_names), dtype=np.int32), index=fit.user_names)
    item_map = pd.Series(np.arange(len(fit.item_names), dtype=np.int32), index=fit.item_names)
    target["user_idx"] = target["user_id"].map(user_map)
    target = target.loc[target["user_idx"].notna()].copy()
    seen = fit.frame[["user_id", "channel"]].drop_duplicates().assign(seen=True)
    target = target.merge(seen, on=["user_id", "channel"], how="left")
    novel = target.loc[target["seen"].isna()].copy()
    novel.sort_values(["user_id", "channel", "time_start", "day"], inplace=True)
    first = novel.drop_duplicates(["user_id", "channel"], keep="first").copy()
    first["item_idx"] = first["channel"].map(item_map)
    first["candidate_covered"] = first["item_idx"].notna()
    first["user_idx"] = first["user_idx"].astype("int32")
    first["day"] = first["day"].astype("int16")
    return first[["user_idx", "day", "channel", "item_idx", "candidate_covered"]].reset_index(drop=True)


def evaluate_static_protocol(recommendations: pd.DataFrame, targets: pd.DataFrame,
                             k: int, by_day: bool) -> tuple[pd.DataFrame, dict]:
    """Evaluate one static list either once per period or against daily targets."""
    rec_map = {
        int(user): group.sort_values("rank").head(k)["item_idx"].astype(int).tolist()
        for user, group in recommendations.groupby("user_idx")
    }
    group_columns = ["user_idx", "day"] if by_day else ["user_idx"]
    discounts = 1.0 / np.log2(np.arange(2, k + 2))
    rows = []
    grouper = group_columns if len(group_columns) > 1 else group_columns[0]
    for key, group in targets.groupby(grouper, sort=True):
        if by_day:
            user, day = map(int, key)
        else:
            user, day = int(key), None
        all_count = int(len(group))
        known = set(group.loc[group["candidate_covered"], "item_idx"].astype(int))
        ranked = rec_map.get(user, [])[:k]
        hits = np.asarray([item in known for item in ranked], dtype=np.float64)
        hit_count = int(hits.sum())
        dcg = float((hits * discounts[:len(hits)]).sum())
        candidate_ideal = float(discounts[:min(k, len(known))].sum())
        all_ideal = float(discounts[:min(k, all_count)].sum())
        row = {
            "user_idx": user,
            "target_count_all": all_count,
            "target_count_catalog": len(known),
            "hits": hit_count,
            "candidate_recall_at_10": hit_count / len(known) if known else np.nan,
            "end_to_end_recall_at_10": hit_count / all_count,
            "candidate_ndcg_at_10": dcg / candidate_ideal if candidate_ideal else np.nan,
            "coverage_adjusted_ndcg_at_10": dcg / all_ideal if all_ideal else 0.0,
            "hit_rate_at_10": float(hit_count > 0),
        }
        if by_day:
            row["day"] = day
        rows.append(row)
    cases = pd.DataFrame(rows)
    summary = {
        "cases": int(len(cases)),
        "users": int(cases["user_idx"].nunique()),
        "candidate_recall_at_10": float(cases["candidate_recall_at_10"].mean()),
        "end_to_end_recall_at_10": float(cases["end_to_end_recall_at_10"].mean()),
        "candidate_ndcg_at_10": float(cases["candidate_ndcg_at_10"].mean()),
        "coverage_adjusted_ndcg_at_10": float(cases["coverage_adjusted_ndcg_at_10"].mean()),
        "hit_rate_at_10": float(cases["hit_rate_at_10"].mean()),
        "cases_with_no_catalog_positive": int((cases["target_count_catalog"] == 0).sum()),
    }
    return cases, summary


def run_protocol_sensitivity(frame: pd.DataFrame, config: dict,
                             assignment_output: Path) -> dict:
    primary = Path(config["outputs_dir"])
    final_fit = encode_fit_period(frame, np.arange(0, 36, dtype=np.int16))
    targets = full_novel_targets(frame, final_fit, np.arange(36, 43, dtype=np.int16))
    table_dir = assignment_output / "tables"
    models = ["popularity", "recent_popularity", "item_knn", "bpr",
              "hybrid_a0.75", "item_knn_count_weighted"]
    period_rows = []
    daily_rows = []
    period_cases: dict[str, pd.DataFrame] = {}
    for model in models:
        recs = pd.read_csv(primary / "tables" / f"recommendations_{model}.csv")
        cases, summary = evaluate_static_protocol(
            recs, targets, int(config["model"]["top_k"]), by_day=False
        )
        summary["model"] = model
        period_rows.append(summary)
        cases.to_csv(table_dir / f"period_cases_{model}.csv", index=False)
        period_cases[model] = cases
        _, daily = evaluate_static_protocol(
            recs, targets, int(config["model"]["top_k"]), by_day=True
        )
        daily["model"] = model
        daily_rows.append(daily)
    period = pd.DataFrame(period_rows).sort_values(
        "coverage_adjusted_ndcg_at_10", ascending=False
    )
    daily = pd.DataFrame(daily_rows).sort_values(
        "coverage_adjusted_ndcg_at_10", ascending=False
    )
    period.to_csv(table_dir / "period_level_results.csv", index=False)
    daily.to_csv(table_dir / "daily_coverage_adjusted_results.csv", index=False)
    bootstrap_metrics = (
        "end_to_end_recall_at_10", "coverage_adjusted_ndcg_at_10", "hit_rate_at_10"
    )
    period_bootstrap = paired_user_bootstrap(
        period_cases["hybrid_a0.75"], period_cases["item_knn"],
        "hybrid_a0.75", "item_knn", samples=10_000, seed=int(config["seed"]),
        metrics=bootstrap_metrics, keys=("user_idx",),
    )
    add_holm_correction(pd.DataFrame(period_bootstrap)).to_csv(
        table_dir / "period_level_bootstrap.csv", index=False
    )
    target = frame.loc[frame["day"].between(36, 42)]
    known_target_users = set(target["user_id"].astype(str)) & set(final_fit.user_names.astype(str))
    covered = targets.loc[targets["candidate_covered"]]
    funnel = {
        "total_dataset_users": int(frame["user_id"].nunique()),
        "users_active_in_test": int(target["user_id"].nunique()),
        "test_active_users_known_in_fit": len(known_target_users),
        "known_users_with_novel_positive": int(targets["user_idx"].nunique()),
        "known_users_with_catalog_covered_positive": int(covered["user_idx"].nunique()),
        "all_novel_positives": int(len(targets)),
        "catalog_covered_novel_positives": int(targets["candidate_covered"].sum()),
        "all_novel_user_day_cases": int(targets[["user_idx", "day"]].drop_duplicates().shape[0]),
        "catalog_covered_user_day_cases": int(covered[["user_idx", "day"]].drop_duplicates().shape[0]),
    }
    (assignment_output / "eligibility_funnel.json").write_text(json.dumps(funnel, indent=2))
    del final_fit, targets, period_cases
    gc.collect()
    return {"period_results": period, "daily_results": daily, "funnel": funnel}


def run_bpr_seed_stability(frame: pd.DataFrame, config: dict, assignment_output: Path,
                           seeds: list[int], maximum_users: int = 5_000) -> pd.DataFrame:
    primary = Path(config["outputs_dir"])
    selected = json.loads((primary / "selected_hyperparameters.json").read_text())
    alpha = float(re.search(r"_a([0-9.]+)", selected["hybrid_model_name"]).group(1))
    fit = encode_fit_period(frame, np.arange(0, 36, dtype=np.int16))
    labels, _ = make_evaluation_labels(frame, fit, np.arange(36, 43, dtype=np.int16))
    eligible = np.sort(labels["user_idx"].unique()).astype(np.int32)
    rng = np.random.default_rng(int(config["seed"]))
    users = np.sort(rng.choice(eligible, size=min(maximum_users, len(eligible)), replace=False))
    labels = labels.loc[labels["user_idx"].isin(users)].copy()
    cf = ItemKNN(selected["item_knn"]["neighbors"],
                 config["model"]["item_knn_batch_size"]).fit(fit.matrix)
    rows = []
    for seed in seeds:
        params = dict(selected["bpr"])
        params["seed"] = int(seed)
        started = time.time()
        bpr = BPR(**params).fit(fit.matrix)
        recs = personalized_recommendations(
            users, fit.matrix, cf, bpr, fit.popularity,
            int(config["model"]["top_k"]), [alpha], [0.0],
        )
        for model, key in (("bpr", "bpr"), (f"hybrid_a{alpha:g}", f"hybrid_a{alpha:g}")):
            row = _evaluate(model, recs[key], labels, fit, config)
            row["seed"] = int(seed)
            row["sample_users"] = len(users)
            row["sample_cases"] = int(labels[["user_idx", "day"]].drop_duplicates().shape[0])
            row["fit_and_recommend_seconds"] = round(time.time() - started, 2)
            rows.append(row)
        del bpr, recs
        gc.collect()
    result = pd.DataFrame(rows)
    result.to_csv(assignment_output / "tables" / "bpr_seed_results.csv", index=False)
    summary = result.groupby("model").agg(
        seeds=("seed", "nunique"),
        recall_mean=("recall_at_10", "mean"), recall_std=("recall_at_10", "std"),
        ndcg_mean=("ndcg_at_10", "mean"), ndcg_std=("ndcg_at_10", "std"),
        hit_rate_mean=("hit_rate_at_10", "mean"), hit_rate_std=("hit_rate_at_10", "std"),
    ).reset_index()
    summary.to_csv(assignment_output / "tables" / "bpr_seed_summary.csv", index=False)
    return result


def run_validation_sample_stability(frame: pd.DataFrame, config: dict,
                                    assignment_output: Path, seeds: list[int],
                                    sample_users: int = 5_000) -> pd.DataFrame:
    """Check whether plausible k/alpha choices change across validation user samples."""
    primary = Path(config["outputs_dir"])
    selected = json.loads((primary / "selected_hyperparameters.json").read_text())
    fit = encode_fit_period(frame, np.arange(0, 30, dtype=np.int16))
    labels, _ = make_evaluation_labels(frame, fit, np.arange(30, 36, dtype=np.int16))
    eligible = np.sort(labels["user_idx"].unique()).astype(np.int32)
    samples = {}
    for seed in seeds:
        rng = np.random.default_rng(int(seed))
        samples[int(seed)] = np.sort(
            rng.choice(eligible, size=min(sample_users, len(eligible)), replace=False)
        )
    union_users = np.unique(np.concatenate(list(samples.values()))).astype(np.int32)
    cf100 = ItemKNN(100, config["model"]["item_knn_batch_size"]).fit(fit.matrix)
    cf200 = ItemKNN(200, config["model"]["item_knn_batch_size"]).fit(fit.matrix)
    bpr = BPR(**selected["bpr"]).fit(fit.matrix)
    top_k = int(config["model"]["top_k"])
    recs = personalized_recommendations(
        union_users, fit.matrix, cf200, bpr, fit.popularity, top_k,
        alphas=[0.5, 0.75], lambdas=[0.0, 0.05],
    )
    recs["item_knn_k100"] = single_model_recommendations(
        union_users, fit.matrix, lambda user: cf100.score_user(fit.matrix[user]), top_k
    )
    recs["item_knn_k200"] = recs["item_knn"]
    candidate_names = ["item_knn_k100", "item_knn_k200", "hybrid_a0.5",
                       "hybrid_a0.5_p0.05", "hybrid_a0.75", "hybrid_a0.75_p0.05"]
    rows = []
    selections = []
    for seed, users in samples.items():
        sample_labels = labels.loc[labels["user_idx"].isin(users)].copy()
        sample_rows = []
        for name in candidate_names:
            sample_recs = recs[name].loc[recs[name]["user_idx"].isin(users)]
            row = _evaluate(name, sample_recs, sample_labels, fit, config)
            row["validation_sample_seed"] = seed
            row["sample_users"] = len(users)
            rows.append(row)
            sample_rows.append(row)
        sample_frame = pd.DataFrame(sample_rows)
        item_best = sample_frame.loc[
            sample_frame["model"].str.startswith("item_knn_k")
        ].sort_values("ndcg_at_10", ascending=False).iloc[0]
        hybrid_best = sample_frame.loc[
            sample_frame["model"].str.startswith("hybrid_")
        ].sort_values("ndcg_at_10", ascending=False).iloc[0]
        selections.append({
            "validation_sample_seed": seed,
            "selected_item_knn": item_best["model"],
            "selected_hybrid": hybrid_best["model"],
            "item_ndcg_at_10": float(item_best["ndcg_at_10"]),
            "hybrid_ndcg_at_10": float(hybrid_best["ndcg_at_10"]),
        })
    result = pd.DataFrame(rows)
    result.to_csv(assignment_output / "tables" / "validation_sample_stability.csv", index=False)
    pd.DataFrame(selections).to_csv(
        assignment_output / "tables" / "validation_sample_selections.csv", index=False
    )
    return result


def _log_runtime_minutes(path: Path) -> float | None:
    if not path.exists():
        return None
    for line in reversed(path.read_text(errors="replace").splitlines()):
        if line.startswith("real "):
            try:
                return float(line.split()[1]) / 60
            except (IndexError, ValueError):
                break
    try:
        values = subprocess.check_output(
            ["stat", "-c", "%W %Y", str(path)], text=True
        ).strip().split()
        birth, modified = map(int, values)
        return (modified - birth) / 60 if birth > 0 and modified >= birth else None
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def scaling_table(root: Path, assignment_output: Path) -> pd.DataFrame:
    specifications = [
        ("official_100k", root / "outputs/dataset_summary.json",
         root / "outputs/logs/full_run.log"),
        ("independent_100k", root / "outputs_full/dataset_summary.json",
         root / "outputs_full/logs/full_cohort_run.log"),
        ("half_million", root / "outputs_500k/dataset_summary.json",
         root / "outputs_500k/run.log"),
        ("one_million", root / "outputs_million/dataset_summary.json",
         root / "outputs_million/run.log"),
    ]
    rows = []
    for name, summary_path, log_path in specifications:
        summary = json.loads(summary_path.read_text())
        rows.append({
            "experiment": name,
            "users": int(summary["users"]),
            "interactions": int(summary["interactions"]),
            "channels": int(summary["channels"]),
            "wall_clock_minutes": _log_runtime_minutes(log_path),
            "runtime_source": (
                "GNU time real seconds recorded in run log"
                if any(line.startswith("real ") for line in
                       log_path.read_text(errors="replace").splitlines())
                else "filesystem birth-to-final-write interval of run log"
            ),
        })
    result = pd.DataFrame(rows)
    result.to_csv(assignment_output / "tables" / "scaling.csv", index=False)
    return result


def _save_figure(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()


def create_assignment_figures(primary_output: Path, assignment_output: Path,
                              backtest: pd.DataFrame, scaling: pd.DataFrame) -> None:
    figure_dir = assignment_output / "figures"
    validation = pd.read_csv(primary_output / "tables" / "validation_grid.csv")
    hybrid = validation.loc[validation["model"].str.startswith("hybrid_a")].copy()
    parsed = hybrid["model"].str.extract(r"hybrid_a(?P<alpha>[0-9.]+)(?:_p(?P<penalty>[0-9.]+))?")
    hybrid["alpha"] = parsed["alpha"].astype(float)
    hybrid["penalty"] = parsed["penalty"].fillna("0").astype(float)
    plt.figure(figsize=(7.2, 4.5))
    for penalty, group in hybrid.groupby("penalty"):
        group = group.sort_values("alpha")
        plt.plot(group["alpha"], group["ndcg_at_10"], marker="o", label=f"lambda={penalty:g}")
    plt.xlabel("BPR weight (alpha)")
    plt.ylabel("Validation NDCG@10")
    plt.title("Hybrid-weight and popularity-penalty ablation")
    plt.legend(ncol=2)
    plt.grid(alpha=0.25)
    _save_figure(figure_dir / "hybrid_ablation.png")

    test = pd.read_csv(primary_output / "tables" / "test_results.csv").set_index("model")
    feature = test.loc[["item_knn", "item_knn_count_weighted"],
                       ["recall_at_10", "ndcg_at_10"]].copy()
    feature.index = ["Binary feedback", "Count-weighted feedback"]
    feature.plot.bar(figsize=(7.2, 4.5), rot=0)
    plt.ylabel("Score")
    plt.title("ItemKNN feature-representation comparison")
    plt.grid(axis="y", alpha=0.25)
    _save_figure(figure_dir / "feature_representation.png")

    history = pd.read_csv(primary_output / "tables" / "user_history_subgroups.csv")
    plt.figure(figsize=(7.2, 4.5))
    plt.plot(history["history_group"], history["ndcg_at_10"], marker="o")
    plt.xlabel("Number of previously watched channels")
    plt.ylabel("Hybrid NDCG@10")
    plt.title("New-channel recommendation becomes harder with longer histories")
    plt.xticks(rotation=15)
    plt.grid(alpha=0.25)
    _save_figure(figure_dir / "user_history_subgroups.png")

    popularity = pd.read_csv(primary_output / "tables" / "channel_popularity_subgroups.csv")
    plt.figure(figsize=(7.2, 4.5))
    plt.bar(popularity["popularity_group"], popularity["recall"])
    plt.xlabel("Target-channel popularity quartile")
    plt.ylabel("Hybrid Recall@10")
    plt.title("Long-tail channels are substantially harder to retrieve")
    plt.xticks(rotation=15)
    plt.grid(axis="y", alpha=0.25)
    _save_figure(figure_dir / "channel_popularity_subgroups.png")

    selected_models = ["hybrid_a0.75", "item_knn", "bpr", "recent_popularity"]
    plot = backtest.loc[backtest["model"].isin(selected_models)].copy()
    plot["fold"] = pd.Categorical(
        plot["fold"], categories=["early", "middle", "late"], ordered=True
    )
    pivot = plot.pivot(index="fold", columns="model", values="ndcg_at_10").sort_index()
    pivot = pivot[["hybrid_a0.75", "item_knn", "bpr", "recent_popularity"]].rename(
        columns={"hybrid_a0.75": "Hybrid", "item_knn": "ItemKNN", "bpr": "BPR",
                 "recent_popularity": "Recent popularity"}
    )
    pivot.plot.bar(figsize=(8, 4.8), rot=0)
    plt.xlabel("Evaluation window")
    plt.ylabel("NDCG@10")
    plt.title("Rolling-origin temporal robustness")
    plt.legend(title="Model", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.grid(axis="y", alpha=0.25)
    _save_figure(figure_dir / "rolling_backtest.png")

    plt.figure(figsize=(7.2, 4.5))
    plt.plot(scaling["users"], scaling["wall_clock_minutes"], marker="o")
    for row in scaling.itertuples():
        rightmost = row.users == scaling["users"].max()
        plt.annotate(row.experiment, (row.users, row.wall_clock_minutes),
                     xytext=(-5 if rightmost else 5, 5), textcoords="offset points",
                     ha="right" if rightmost else "left")
    plt.xscale("log")
    plt.xlabel("Training-cohort users (log scale)")
    plt.ylabel("End-to-end wall-clock minutes")
    plt.title("Observed experiment scaling")
    plt.grid(alpha=0.25)
    _save_figure(figure_dir / "scaling.png")

    root = assignment_output.parent.parent
    scale_runs = [
        ("100k", 99_660, root / "outputs_full/tables/test_results.csv"),
        ("500k", 500_000, root / "outputs_500k/tables/test_results.csv"),
        ("1m", 1_000_000, root / "outputs_million/tables/test_results.csv"),
    ]
    model_names = {
        "hybrid_a0.75": "Hybrid",
        "item_knn": "ItemKNN",
        "bpr": "BPR",
        "recent_popularity": "Recent popularity",
        "popularity": "Popularity",
    }
    accuracy_rows = []
    for scale_label, users, result_path in scale_runs:
        frame = pd.read_csv(result_path)
        for model, display_name in model_names.items():
            value = frame.loc[frame["model"] == model, "ndcg_at_10"]
            accuracy_rows.append({
                "scale": scale_label,
                "users": users,
                "model": display_name,
                "ndcg_at_10": float(value.iloc[0]),
            })
    accuracy = pd.DataFrame(accuracy_rows)
    accuracy.to_csv(assignment_output / "tables" / "scalability_ndcg.csv", index=False)
    plt.figure(figsize=(7.6, 4.8))
    for model, group in accuracy.groupby("model", sort=False):
        group = group.sort_values("users")
        plt.plot(group["users"], group["ndcg_at_10"], marker="o", label=model)
    plt.xscale("log")
    plt.xticks([100_000, 500_000, 1_000_000], ["100k", "500k", "1m"])
    plt.xlabel("Training-cohort users (log scale)")
    plt.ylabel("Test NDCG@10")
    plt.title("Model ranking remains stable across three cohort scales")
    plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.grid(alpha=0.25)
    _save_figure(figure_dir / "scalability_ndcg.png")

    period_path = assignment_output / "tables" / "period_level_results.csv"
    if period_path.exists():
        period = pd.read_csv(period_path).set_index("model")
        order = ["hybrid_a0.75", "item_knn", "bpr", "recent_popularity"]
        names = ["Hybrid", "ItemKNN", "BPR", "Recent popularity"]
        values = period.loc[order, ["candidate_ndcg_at_10",
                                    "coverage_adjusted_ndcg_at_10"]].copy()
        values.index = names
        values.columns = ["Candidate-conditioned", "End-to-end / cold-start adjusted"]
        values.plot.bar(figsize=(8, 4.8), rot=0)
        plt.xlabel("Model")
        plt.ylabel("Period-level NDCG@10")
        plt.title("Static-list evaluation with and without cold-start positives")
        plt.grid(axis="y", alpha=0.25)
        _save_figure(figure_dir / "period_level_cold_start.png")

    seed_path = assignment_output / "tables" / "bpr_seed_summary.csv"
    if seed_path.exists():
        seeds = pd.read_csv(seed_path)
        labels = seeds["model"].replace({"hybrid_a0.75": "Hybrid", "bpr": "BPR"})
        plt.figure(figsize=(6.8, 4.5))
        plt.bar(labels, seeds["ndcg_mean"], yerr=seeds["ndcg_std"], capsize=7)
        plt.ylabel("NDCG@10 (mean +/- SD)")
        plt.title("Five-seed training stability on the same 5,000 test users")
        plt.grid(axis="y", alpha=0.25)
        _save_figure(figure_dir / "bpr_seed_stability.png")

    funnel_path = assignment_output / "eligibility_funnel.json"
    if funnel_path.exists():
        funnel = json.loads(funnel_path.read_text())
        labels = ["All dataset users", "Active in test", "Known in fit",
                  "With novel positive", "With catalog-covered positive"]
        values = [funnel["total_dataset_users"], funnel["users_active_in_test"],
                  funnel["test_active_users_known_in_fit"],
                  funnel["known_users_with_novel_positive"],
                  funnel["known_users_with_catalog_covered_positive"]]
        plt.figure(figsize=(8, 4.8))
        bars = plt.barh(labels[::-1], values[::-1])
        for bar, value in zip(bars, values[::-1]):
            plt.text(value + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                     f"{value:,}", va="center")
        plt.xlim(0, max(values) * 1.16)
        plt.xlabel("Users")
        plt.title("Evaluation eligibility funnel")
        plt.grid(axis="x", alpha=0.25)
        _save_figure(figure_dir / "eligibility_funnel.png")

    validation_path = assignment_output / "tables" / "validation_sample_stability.csv"
    if validation_path.exists():
        validation = pd.read_csv(validation_path)
        summary = validation.groupby("model")["ndcg_at_10"].agg(["mean", "std"])
        order = ["item_knn_k100", "item_knn_k200", "hybrid_a0.5",
                 "hybrid_a0.5_p0.05", "hybrid_a0.75", "hybrid_a0.75_p0.05"]
        display_names = ["KNN k100", "KNN k200", "Hybrid a.5", "a.5 + p.05",
                         "Hybrid a.75", "a.75 + p.05"]
        summary = summary.loc[order]
        plt.figure(figsize=(9, 4.8))
        plt.bar(display_names, summary["mean"], yerr=summary["std"], capsize=5)
        plt.ylabel("Validation NDCG@10 (mean +/- SD)")
        plt.title("Model selection across five validation-user samples")
        plt.xticks(rotation=18)
        plt.grid(axis="y", alpha=0.25)
        _save_figure(figure_dir / "validation_sample_stability.png")


def run_assignment_analysis(config: dict) -> dict:
    root = Path.cwd()
    primary_output = Path(config["outputs_dir"])
    settings = config.get("assignment_analysis", {})
    assignment_output = Path(settings.get("outputs_dir", primary_output / "assignment2"))
    (assignment_output / "tables").mkdir(parents=True, exist_ok=True)
    (assignment_output / "figures").mkdir(parents=True, exist_ok=True)
    bootstrap = run_bootstrap(
        primary_output, assignment_output,
        int(settings.get("bootstrap_samples", 10_000)), int(config["seed"]),
    )
    frame = load_interactions(config["data"]["raw_path"], config["split"]["slots_per_day"])
    quality = data_quality_audit(frame, assignment_output / "data_quality.json")
    protocol = run_protocol_sensitivity(frame, config, assignment_output)
    seed_results = run_bpr_seed_stability(
        frame, config, assignment_output,
        [int(value) for value in settings.get(
            "bpr_stability_seeds", [258, 1258, 2258, 3258, 4258]
        )],
        int(settings.get("bpr_stability_max_users", 5_000)),
    )
    validation_stability = run_validation_sample_stability(
        frame, config, assignment_output,
        [int(value) for value in settings.get(
            "validation_sample_seeds", [258, 1258, 2258, 3258, 4258]
        )],
        int(settings.get("validation_sample_users", 5_000)),
    )
    folds = settings.get("backtest_folds", [
        {"name": "early", "fit_end_day": 17, "target_start_day": 18, "target_end_day": 23},
        {"name": "middle", "fit_end_day": 23, "target_start_day": 24, "target_end_day": 29},
    ])
    backtest_path = assignment_output / "tables" / "rolling_backtest.csv"
    if bool(settings.get("reuse_completed_backtest", True)) and backtest_path.exists():
        backtest = pd.read_csv(backtest_path)
    else:
        backtest = run_rolling_backtest(frame, config, assignment_output, folds)
    scaling = scaling_table(root, assignment_output)
    create_assignment_figures(primary_output, assignment_output, backtest, scaling)
    result = {
        "outputs_dir": str(assignment_output),
        "bootstrap_rows": len(bootstrap),
        "backtest_rows": len(backtest),
        "period_level_rows": len(protocol["period_results"]),
        "bpr_seed_rows": len(seed_results),
        "validation_stability_rows": len(validation_stability),
        "data_quality": quality,
        "figures": sorted(path.name for path in (assignment_output / "figures").glob("*.png")),
    }
    (assignment_output / "manifest.json").write_text(json.dumps(result, indent=2))
    return result
