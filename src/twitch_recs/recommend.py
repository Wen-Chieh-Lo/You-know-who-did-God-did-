from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd
from scipy import sparse
from tqdm.auto import tqdm

from .models import BPR, ItemKNN


def _standardize(scores: np.ndarray, eligible: np.ndarray) -> np.ndarray:
    result = np.full_like(scores, -np.inf, dtype=np.float32)
    values = scores[eligible].astype(np.float64)
    if len(values) == 0:
        return result
    std = values.std()
    if std < 1e-12:
        result[eligible] = 0.0
    else:
        result[eligible] = ((values - values.mean()) / std).astype(np.float32)
    return result


def _top_k(scores: np.ndarray, k: int) -> np.ndarray:
    eligible_count = int(np.isfinite(scores).sum())
    use_k = min(k, eligible_count)
    if use_k == 0:
        return np.empty(0, dtype=np.int32)
    selected = np.argpartition(scores, -use_k)[-use_k:]
    order = np.lexsort((selected, -scores[selected]))
    return selected[order].astype(np.int32)


def popularity_recommendations(users: Iterable[int], interactions: sparse.csr_matrix,
                               popularity: np.ndarray, k: int = 10,
                               candidate_mask: np.ndarray | None = None) -> pd.DataFrame:
    rows = []
    base_mask = np.ones(interactions.shape[1], dtype=bool) if candidate_mask is None else candidate_mask
    candidates = np.flatnonzero(base_mask)
    ranked = candidates[np.lexsort((candidates, -popularity[candidates]))]
    for user in users:
        seen = set(interactions[user].indices.tolist())
        chosen = []
        for item in ranked:
            if int(item) not in seen:
                chosen.append(int(item))
                if len(chosen) == k:
                    break
        for rank, item in enumerate(chosen, 1):
            rows.append((int(user), rank, item, float(popularity[item])))
    return pd.DataFrame(rows, columns=["user_idx", "rank", "item_idx", "score"])


def single_model_recommendations(users: Iterable[int], interactions: sparse.csr_matrix,
                                 score_user, k: int = 10,
                                 candidate_mask: np.ndarray | None = None) -> pd.DataFrame:
    rows = []
    base_mask = np.ones(interactions.shape[1], dtype=bool) if candidate_mask is None else candidate_mask
    for user in tqdm(list(users), desc="Recommending", leave=False):
        eligible = base_mask.copy()
        eligible[interactions[user].indices] = False
        scores = np.asarray(score_user(int(user)), dtype=np.float32)
        scores[~eligible] = -np.inf
        for rank, item in enumerate(_top_k(scores, k), 1):
            rows.append((int(user), rank, int(item), float(scores[item])))
    return pd.DataFrame(rows, columns=["user_idx", "rank", "item_idx", "score"])


def factor_recommendations(users: Iterable[int], interactions: sparse.csr_matrix,
                           user_factors: np.ndarray, item_factors: np.ndarray,
                           k: int = 10, candidate_mask: np.ndarray | None = None,
                           batch_size: int = 64, device: str | None = None) -> pd.DataFrame:
    """GPU-batched exact top-k for dot-product recommenders."""
    try:
        import torch
    except (ImportError, OSError) as exc:
        raise RuntimeError("factor_recommendations requires a working PyTorch installation") from exc
    selected_device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    users = np.asarray(list(users), dtype=np.int64)
    item_tensor = torch.as_tensor(item_factors, dtype=torch.float32, device=selected_device)
    allowed = None
    if candidate_mask is not None:
        allowed = torch.as_tensor(candidate_mask, dtype=torch.bool, device=selected_device)
    rows: list[tuple[int, int, int, float]] = []
    for start in tqdm(range(0, len(users), batch_size), desc="Factor top-k", leave=False):
        batch_users = users[start:start + batch_size]
        batch_factors = torch.as_tensor(
            user_factors[batch_users], dtype=torch.float32, device=selected_device
        )
        scores = batch_factors @ item_tensor.T
        if allowed is not None:
            scores[:, ~allowed] = -torch.inf
        for row, user in enumerate(batch_users):
            seen = torch.as_tensor(interactions[int(user)].indices, dtype=torch.long,
                                   device=selected_device)
            scores[row, seen] = -torch.inf
        values, items = torch.topk(scores, k=min(k, scores.shape[1]), dim=1, sorted=True)
        values_np = values.detach().cpu().numpy()
        items_np = items.detach().cpu().numpy()
        for row, user in enumerate(batch_users):
            for rank, (item, score) in enumerate(zip(items_np[row], values_np[row]), 1):
                if np.isfinite(score):
                    rows.append((int(user), rank, int(item), float(score)))
    return pd.DataFrame(rows, columns=["user_idx", "rank", "item_idx", "score"])


def personalized_recommendations(
    users: Iterable[int], interactions: sparse.csr_matrix, item_model: ItemKNN,
    bpr_model: BPR, popularity: np.ndarray, k: int = 10,
    alphas: Iterable[float] = (0.5,), lambdas: Iterable[float] = (0.0,),
    candidate_mask: np.ndarray | None = None,
) -> dict[str, pd.DataFrame]:
    """Produce item-CF, BPR, hybrid, and popularity-adjusted hybrid lists."""
    users = np.asarray(list(users), dtype=np.int32)
    base_mask = np.ones(interactions.shape[1], dtype=bool) if candidate_mask is None else candidate_mask
    candidate_items = np.flatnonzero(base_mask).astype(np.int32)
    model_rows: dict[str, list[tuple[int, int, int, float]]] = {
        "item_knn": [], "bpr": []
    }
    for alpha in alphas:
        model_rows[f"hybrid_a{alpha:g}"] = []
        for penalty in lambdas:
            if penalty > 0:
                model_rows[f"hybrid_a{alpha:g}_p{penalty:g}"] = []
    candidate_log_popularity = np.log1p(popularity[candidate_items]).astype(np.float32)

    for user in tqdm(users, desc="Recommending", leave=False):
        seen = interactions[user].indices
        eligible = ~np.isin(candidate_items, seen, assume_unique=True)
        cf_raw = item_model.score_user(interactions[user])[candidate_items]
        if bpr_model.user_factors_ is None or bpr_model.item_factors_ is None:
            raise RuntimeError("BPR model must be fitted before recommendation")
        bpr_raw = (
            bpr_model.item_factors_[candidate_items] @ bpr_model.user_factors_[int(user)]
        ).astype(np.float32)
        cf = _standardize(cf_raw, eligible)
        bpr = _standardize(bpr_raw, eligible)
        for name, scores in (("item_knn", cf), ("bpr", bpr)):
            for rank, local_item in enumerate(_top_k(scores, k), 1):
                item = candidate_items[local_item]
                model_rows[name].append((int(user), rank, int(item), float(scores[local_item])))
        for alpha in alphas:
            hybrid = np.full_like(cf, -np.inf)
            hybrid[eligible] = (
                alpha * bpr[eligible] + (1.0 - alpha) * cf[eligible]
            )
            base_name = f"hybrid_a{alpha:g}"
            for rank, local_item in enumerate(_top_k(hybrid, k), 1):
                item = candidate_items[local_item]
                model_rows[base_name].append((int(user), rank, int(item), float(hybrid[local_item])))
            for penalty in lambdas:
                if penalty <= 0:
                    continue
                adjusted = np.full_like(hybrid, -np.inf)
                adjusted[eligible] = hybrid[eligible] - penalty * candidate_log_popularity[eligible]
                name = f"hybrid_a{alpha:g}_p{penalty:g}"
                for rank, local_item in enumerate(_top_k(adjusted, k), 1):
                    item = candidate_items[local_item]
                    model_rows[name].append((int(user), rank, int(item), float(adjusted[local_item])))
    columns = ["user_idx", "rank", "item_idx", "score"]
    return {name: pd.DataFrame(rows, columns=columns) for name, rows in model_rows.items()}
