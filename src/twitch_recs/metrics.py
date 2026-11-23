from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import sparse


def evaluate_ranking(recommendations: pd.DataFrame, labels: pd.DataFrame, k: int = 10,
                     popularity: np.ndarray | None = None,
                     catalog_size: int | None = None,
                     long_tail_quantile: float = 0.80) -> tuple[pd.DataFrame, dict[str, float]]:
    rec_map = {
        int(user): group.sort_values("rank").head(k)["item_idx"].astype(int).tolist()
        for user, group in recommendations.groupby("user_idx")
    }
    case_rows = []
    discounts = 1.0 / np.log2(np.arange(2, k + 2))
    for (user, day), group in labels.groupby(["user_idx", "day"]):
        truth = set(group["item_idx"].astype(int))
        ranked = rec_map.get(int(user), [])
        hits = np.array([item in truth for item in ranked[:k]], dtype=np.float64)
        dcg = float((hits * discounts[:len(hits)]).sum())
        ideal = float(discounts[:min(k, len(truth))].sum())
        case_rows.append({
            "user_idx": int(user), "day": int(day), "target_count": len(truth),
            "hits": int(hits.sum()), "recall_at_10": float(hits.sum() / len(truth)),
            "ndcg_at_10": dcg / ideal if ideal else 0.0,
            "hit_rate_at_10": float(hits.any()),
        })
    cases = pd.DataFrame(case_rows)
    recommended_items = recommendations["item_idx"].to_numpy(dtype=int)
    summary = {
        "cases": int(len(cases)),
        "users": int(cases["user_idx"].nunique()) if len(cases) else 0,
        "recall_at_10": float(cases["recall_at_10"].mean()) if len(cases) else float("nan"),
        "ndcg_at_10": float(cases["ndcg_at_10"].mean()) if len(cases) else float("nan"),
        "hit_rate_at_10": float(cases["hit_rate_at_10"].mean()) if len(cases) else float("nan"),
        "catalog_coverage": float(pd.Series(recommended_items).nunique() / catalog_size)
        if catalog_size and len(recommended_items) else 0.0,
    }
    if popularity is not None and len(recommended_items):
        probabilities = popularity / max(float(popularity.sum()), 1.0)
        summary["novelty_bits"] = float((-np.log2(np.maximum(probabilities[recommended_items], 1e-12))).mean())
        positive_pop = popularity[popularity > 0]
        threshold = float(np.quantile(positive_pop, long_tail_quantile)) if len(positive_pop) else 0.0
        summary["long_tail_exposure"] = float((popularity[recommended_items] <= threshold).mean())
    return cases, summary


def user_history_subgroups(cases: pd.DataFrame, interactions: sparse.csr_matrix) -> pd.DataFrame:
    lengths = np.diff(interactions.indptr)
    result = cases.copy()
    result["history_length"] = lengths[result["user_idx"].to_numpy(dtype=int)]
    unique = result[["user_idx", "history_length"]].drop_duplicates()
    try:
        unique["history_group"] = pd.qcut(unique["history_length"], 4, duplicates="drop")
    except ValueError:
        unique["history_group"] = "all"
    result = result.merge(unique[["user_idx", "history_group"]], on="user_idx", how="left")
    return result.groupby("history_group", observed=True).agg(
        users=("user_idx", "nunique"), cases=("day", "size"),
        recall_at_10=("recall_at_10", "mean"), ndcg_at_10=("ndcg_at_10", "mean"),
        hit_rate_at_10=("hit_rate_at_10", "mean"),
    ).reset_index()


def channel_popularity_subgroups(recommendations: pd.DataFrame, labels: pd.DataFrame,
                                 popularity: np.ndarray, k: int = 10) -> pd.DataFrame:
    positive = labels.copy()
    positive["popularity"] = popularity[positive["item_idx"].to_numpy(dtype=int)]
    positive["popularity_group"] = pd.qcut(
        positive["popularity"].rank(method="first"), 4,
        labels=["least popular", "lower-middle", "upper-middle", "most popular"]
    )
    rec_pairs = set(zip(recommendations["user_idx"].astype(int), recommendations["item_idx"].astype(int)))
    positive["hit"] = [
        (int(u), int(i)) in rec_pairs for u, i in zip(positive["user_idx"], positive["item_idx"])
    ]
    return positive.groupby("popularity_group", observed=True).agg(
        positives=("item_idx", "size"), channels=("item_idx", "nunique"), recall=("hit", "mean")
    ).reset_index()


def complementarity(labels: pd.DataFrame, first: pd.DataFrame, second: pd.DataFrame,
                    first_name: str = "BPR", second_name: str = "ItemKNN") -> dict[str, int]:
    positives = set(zip(labels["user_idx"].astype(int), labels["item_idx"].astype(int)))
    first_hits = positives & set(zip(first["user_idx"].astype(int), first["item_idx"].astype(int)))
    second_hits = positives & set(zip(second["user_idx"].astype(int), second["item_idx"].astype(int)))
    return {
        f"{first_name}_only": len(first_hits - second_hits),
        f"{second_name}_only": len(second_hits - first_hits),
        "both": len(first_hits & second_hits),
        "neither": len(positives - first_hits - second_hits),
    }
