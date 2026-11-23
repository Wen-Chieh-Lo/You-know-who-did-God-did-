from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data import (chronological_split, encode_fit_period, load_interactions,
                   make_evaluation_labels, recent_item_mask)
from .metrics import evaluate_ranking
from .models import ItemKNN, LightGCN, SequentialRecommender, time_decayed_matrix
from .recommend import factor_recommendations, single_model_recommendations


def _users(labels: pd.DataFrame, maximum: int | None, seed: int) -> np.ndarray:
    values = np.sort(labels["user_idx"].unique()).astype(np.int32)
    if maximum is not None and len(values) > maximum:
        values = np.sort(np.random.default_rng(seed).choice(values, maximum, replace=False))
    return values


def _evaluate(name: str, recs: pd.DataFrame, labels: pd.DataFrame, fit, config: dict) -> dict:
    _, summary = evaluate_ranking(
        recs, labels, config["model"]["top_k"], fit.popularity, fit.matrix.shape[1],
        config["evaluation"]["long_tail_quantile"],
    )
    summary["model"] = name
    return summary


def _fit_models(fit, settings: dict, seed: int):
    lightgcn = LightGCN(
        factors=settings["factors"], layers=settings["lightgcn_layers"],
        epochs=settings["lightgcn_epochs"], learning_rate=settings["lightgcn_learning_rate"],
        regularization=settings["lightgcn_regularization"],
        samples_per_epoch=settings["lightgcn_samples_per_epoch"], seed=seed,
    ).fit(fit.matrix)
    sasrec = SequentialRecommender(
        "sasrec", factors=settings["factors"], max_length=settings["max_sequence_length"],
        epochs=settings["sequential_epochs"], batch_size=settings["sequential_batch_size"],
        learning_rate=settings["sequential_learning_rate"], seed=seed,
    ).fit(fit)
    gru4rec = SequentialRecommender(
        "gru4rec", factors=settings["factors"], max_length=settings["max_sequence_length"],
        epochs=settings["sequential_epochs"], batch_size=settings["sequential_batch_size"],
        learning_rate=settings["sequential_learning_rate"], seed=seed,
    ).fit(fit)
    weighted = time_decayed_matrix(fit, settings["time_decay"])
    time_knn = ItemKNN(settings["item_knn_neighbors"], settings["item_knn_batch_size"]).fit(weighted)
    return {"lightgcn": lightgcn, "sasrec": sasrec, "gru4rec": gru4rec,
            "time_decayed_item_knn": (time_knn, weighted)}


def _recommend(models: dict, users: np.ndarray, fit, frame: pd.DataFrame,
               fit_end_day: int, config: dict) -> dict[str, pd.DataFrame]:
    settings = config["advanced"]
    k = config["model"]["top_k"]
    batch = settings["ranking_batch_size"]
    recs: dict[str, pd.DataFrame] = {}
    for name in ("lightgcn", "sasrec", "gru4rec"):
        model = models[name]
        recs[name] = factor_recommendations(
            users, fit.matrix, model.user_factors_, model.item_factors_, k,
            batch_size=batch,
        )
    time_knn, weighted = models["time_decayed_item_knn"]
    recs["time_decayed_item_knn"] = single_model_recommendations(
        users, fit.matrix, lambda user: time_knn.score_user(weighted[user]), k,
    )
    # The fixed dataset has no exact recommendation-time availability snapshot.
    # This row is therefore deliberately named a proxy: SASRec scores are ranked
    # only among channels observed in the last seven fit days.
    active = recent_item_mask(frame, fit, fit_end_day, config["model"]["recent_days"])
    sasrec = models["sasrec"]
    recs["liverec_proxy_active_7d"] = factor_recommendations(
        users, fit.matrix, sasrec.user_factors_, sasrec.item_factors_, k,
        candidate_mask=active, batch_size=batch,
    )
    return recs


def _write_named_recs(recs: dict[str, pd.DataFrame], fit, directory: Path) -> None:
    for name, frame in recs.items():
        named = frame.copy()
        named["user_id"] = fit.user_names[named["user_idx"].to_numpy(dtype=int)]
        named["channel"] = fit.item_names[named["item_idx"].to_numpy(dtype=int)]
        named.to_csv(directory / f"recommendations_{name}.csv", index=False)


def _render_report(path: Path, validation: pd.DataFrame, test: pd.DataFrame,
                   settings: dict, coverage: dict) -> None:
    table = test.to_markdown(index=False, floatfmt=".5f")
    validation_table = validation.to_markdown(index=False, floatfmt=".5f")
    content = f"""# 進階推薦模型比較

本實驗在不使用 metadata 的限制下加入 LightGCN、SASRec、GRU4Rec、
time-decayed ItemKNN，以及 LiveRec-like availability proxy。所有模型使用與主要實驗
相同的 chronological split、未看過頻道 targets、fit catalog 與 Top-10 metrics。

## Test 結果

{table}

## Validation 結果

{validation_table}

## 結論

- **沒有新增模型超越 Hybrid 或 binary ItemKNN。** Hybrid NDCG@10 為 0.13148，
  ItemKNN 為 0.12584，仍是前兩名。
- **LightGCN 比 BPR 好，但幅度不足以取代 ItemKNN。** LightGCN NDCG@10 為
  0.05981，相對 BPR 的 0.05420 高約 10.4%，但只有 ItemKNN 的約 47.5%。
- **Time-decayed ItemKNN 是最有用的新增模型。** NDCG@10 為 0.12046，低於
  binary ItemKNN 約 4.3%，但 catalog coverage 從 36.71% 增至 43.61%，且長尾曝光
  從 14.59% 增至 21.59%。近期加權改善多樣性，卻沒有改善主要準確度。
- **SASRec 與 GRU4Rec 不適合直接套用目前 labels。** 訓練資料中的 next-item
  大量是回訪既有頻道，但本任務在 inference 時排除所有已看過頻道，只評估新頻道。
  因此 sequence models 學到的 repeat-consumption 訊號被評估規則刻意移除。很高的
  novelty/long-tail 數值伴隨極低 Recall，代表它們主要推薦了非常冷門但不正確的頻道。
- **LiveRec proxy 不是原始 LiveRec。** 固定資料沒有推薦瞬間的精確 online-channel
  snapshot；本 row 只是把 SASRec 分數限制在 fit period 最後七天出現過的頻道。

這些 deep models 使用預先固定的合理設定，沒有進行與原始模型同規模的超參數 grid。
因此結果足以回答「目前版本是否立即勝過既有四種方法」，答案是否定的；但不能證明
所有可能調參、loss 或 negative sampling 下的 LightGCN/SASRec 永遠較差。

## 固定設定

```json
{json.dumps(settings, indent=2)}
```

Test fit-catalog candidate coverage 為 {coverage['candidate_coverage']:.4%}。

`liverec_proxy_active_7d` 並非原始 LiveRec：資料不含推薦時刻的精確 availability
snapshot。它重用 SASRec scores，並將 candidates 限制為 fit period 最後七天出現過的
頻道；proxy 以外的 positives 仍計為 misses。
"""
    path.write_text(content, encoding="utf-8")


def run_advanced_experiment(config: dict) -> dict:
    output = Path(config["advanced"].get("outputs_dir", "outputs/advanced"))
    tables = output / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    frame = load_interactions(config["data"]["raw_path"], config["split"]["slots_per_day"])
    split = chronological_split(frame, config["split"]["train_fraction"],
                                config["split"]["validation_fraction"])

    train_fit = encode_fit_period(frame, split.train_days)
    val_labels, _ = make_evaluation_labels(frame, train_fit, split.validation_days)
    val_users = _users(val_labels, config["evaluation"]["max_validation_users"], config["seed"])
    val_labels = val_labels[val_labels["user_idx"].isin(val_users)].copy()
    train_models = _fit_models(train_fit, config["advanced"], config["seed"])
    val_recs = _recommend(train_models, val_users, train_fit, frame, split.train_end, config)
    validation = pd.DataFrame([
        _evaluate(name, rec, val_labels, train_fit, config) for name, rec in val_recs.items()
    ]).sort_values("ndcg_at_10", ascending=False)
    validation.to_csv(tables / "validation_results.csv", index=False)
    del train_models, val_recs

    final_days = np.concatenate([split.train_days, split.validation_days])
    final_fit = encode_fit_period(frame, final_days)
    test_labels, test_coverage = make_evaluation_labels(frame, final_fit, split.test_days)
    test_users = _users(test_labels, config["evaluation"]["max_test_users"], config["seed"])
    test_labels = test_labels[test_labels["user_idx"].isin(test_users)].copy()
    final_models = _fit_models(final_fit, config["advanced"], config["seed"])
    test_recs = _recommend(final_models, test_users, final_fit, frame, split.validation_end, config)
    _write_named_recs(test_recs, final_fit, tables)
    advanced_test = pd.DataFrame([
        _evaluate(name, rec, test_labels, final_fit, config) for name, rec in test_recs.items()
    ])

    baseline_path = Path(config["outputs_dir"]) / "tables" / "test_results.csv"
    if baseline_path.exists() and config["evaluation"]["max_test_users"] is None:
        baseline = pd.read_csv(baseline_path)
        comparison = pd.concat([baseline, advanced_test], ignore_index=True)
    else:
        comparison = advanced_test
    comparison = comparison.sort_values("ndcg_at_10", ascending=False)
    comparison.to_csv(tables / "test_results.csv", index=False)
    (output / "settings.json").write_text(
        json.dumps(config["advanced"], indent=2), encoding="utf-8"
    )
    (output / "test_candidate_coverage.json").write_text(
        json.dumps(test_coverage, indent=2), encoding="utf-8"
    )
    report_path = output / "ADVANCED_MODEL_REPORT.md"
    _render_report(report_path, validation, comparison, config["advanced"], test_coverage)
    return {"report": str(report_path), "test_results": comparison.to_dict(orient="records")}
