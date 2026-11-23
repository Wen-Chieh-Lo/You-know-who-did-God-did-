from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

COLUMNS = ["user_id", "stream_id", "channel", "time_start", "time_stop"]


@dataclass(frozen=True)
class DaySplit:
    train_days: np.ndarray
    validation_days: np.ndarray
    test_days: np.ndarray

    @property
    def train_end(self) -> int:
        return int(self.train_days.max())

    @property
    def validation_end(self) -> int:
        return int(self.validation_days.max())


@dataclass
class EncodedData:
    frame: pd.DataFrame
    user_names: np.ndarray
    item_names: np.ndarray
    matrix: sparse.csr_matrix
    popularity: np.ndarray


def download_dataset(url: str, destination: str | Path, force: bool = False) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not force:
        return destination
    temporary = destination.with_suffix(destination.suffix + ".part")
    urllib.request.urlretrieve(url, temporary)
    temporary.replace(destination)
    return destination


def load_interactions(path: str | Path, slots_per_day: int = 144) -> pd.DataFrame:
    path = Path(path)
    frame = pd.read_csv(
        path,
        header=None,
        names=COLUMNS,
        dtype={"user_id": "string", "stream_id": "string", "channel": "string",
               "time_start": "int32", "time_stop": "int32"},
    )
    if frame.isna().any().any():
        raise ValueError(f"Dataset contains missing values: {frame.isna().sum().to_dict()}")
    if (frame["time_stop"] < frame["time_start"]).any():
        raise ValueError("Found time_stop before time_start")
    origin = int(frame["time_start"].min())
    frame["day"] = ((frame["time_start"] - origin) // slots_per_day).astype("int16")
    frame["duration_slots"] = (frame["time_stop"] - frame["time_start"]).clip(lower=1).astype("int32")
    return frame


def chronological_split(frame: pd.DataFrame, train_fraction: float = 0.70,
                        validation_fraction: float = 0.15) -> DaySplit:
    days = np.sort(frame["day"].unique())
    if len(days) < 3:
        raise ValueError("At least three observed day blocks are required")
    train_n = max(1, int(np.floor(len(days) * train_fraction)))
    val_n = max(1, int(np.floor(len(days) * validation_fraction)))
    if train_n + val_n >= len(days):
        val_n = 1
        train_n = len(days) - 2
    return DaySplit(days[:train_n], days[train_n:train_n + val_n], days[train_n + val_n:])


def encode_fit_period(frame: pd.DataFrame, fit_days: np.ndarray) -> EncodedData:
    # Keep time_start so sequential models can reconstruct within-day order.  The
    # original sparse CF pipeline ignores this extra column.
    fit = frame.loc[
        frame["day"].isin(fit_days), ["user_id", "channel", "day", "time_start"]
    ].copy()
    user_names = np.sort(fit["user_id"].unique().astype(str))
    item_names = np.sort(fit["channel"].unique().astype(str))
    user_map = pd.Series(np.arange(len(user_names), dtype=np.int32), index=user_names)
    item_map = pd.Series(np.arange(len(item_names), dtype=np.int32), index=item_names)
    fit["user_idx"] = fit["user_id"].map(user_map).astype("int32")
    fit["item_idx"] = fit["channel"].map(item_map).astype("int32")
    unique = fit[["user_idx", "item_idx"]].drop_duplicates()
    matrix = sparse.csr_matrix(
        (np.ones(len(unique), dtype=np.float32), (unique["user_idx"], unique["item_idx"])),
        shape=(len(user_names), len(item_names)), dtype=np.float32,
    )
    matrix.sort_indices()
    popularity = np.asarray(matrix.sum(axis=0)).ravel().astype(np.float32)
    return EncodedData(fit, user_names, item_names, matrix, popularity)


def make_evaluation_labels(frame: pd.DataFrame, fit: EncodedData,
                           target_days: np.ndarray) -> tuple[pd.DataFrame, dict[str, float]]:
    target = frame.loc[frame["day"].isin(target_days), ["user_id", "channel", "day", "time_start"]].copy()
    user_map = pd.Series(np.arange(len(fit.user_names), dtype=np.int32), index=fit.user_names)
    item_map = pd.Series(np.arange(len(fit.item_names), dtype=np.int32), index=fit.item_names)
    target["user_idx"] = target["user_id"].map(user_map)
    target["item_idx"] = target["channel"].map(item_map)
    eligible_users = target["user_idx"].notna()
    target_known_user = target.loc[eligible_users].copy()

    seen_pairs = fit.frame[["user_id", "channel"]].drop_duplicates().assign(seen=True)
    merged = target_known_user.merge(seen_pairs, on=["user_id", "channel"], how="left")
    novel = merged.loc[merged["seen"].isna()].copy()
    novel.sort_values(["user_id", "channel", "time_start", "day"], inplace=True)
    first = novel.drop_duplicates(["user_id", "channel"], keep="first")
    in_catalog = first["item_idx"].notna()
    labels = first.loc[in_catalog, ["user_idx", "item_idx", "day"]].astype("int32")
    labels = labels.drop_duplicates().sort_values(["user_idx", "day", "item_idx"]).reset_index(drop=True)
    total_novel = len(first)
    stats = {
        "target_rows": int(len(target)),
        "known_user_target_rows": int(eligible_users.sum()),
        "novel_user_channel_positives": int(total_novel),
        "candidate_covered_positives": int(in_catalog.sum()),
        "candidate_coverage": float(in_catalog.mean()) if total_novel else float("nan"),
        "evaluation_cases": int(labels[["user_idx", "day"]].drop_duplicates().shape[0]),
    }
    return labels, stats


def recent_item_mask(frame: pd.DataFrame, fit: EncodedData, fit_end_day: int,
                     recent_days: int) -> np.ndarray:
    active = frame.loc[
        frame["day"].between(fit_end_day - recent_days + 1, fit_end_day), "channel"
    ].unique()
    # np.isin performs a quadratic element-wise fallback for object/string arrays.
    # pandas uses a hash table here, which keeps the full 100k catalog practical.
    return np.asarray(pd.Index(fit.item_names).isin(pd.Index(active)), dtype=bool)


def interaction_count_matrix(fit: EncodedData) -> sparse.csr_matrix:
    """User-item matrix retaining repeated fit-period interaction rows."""
    matrix = sparse.csr_matrix(
        (np.ones(len(fit.frame), dtype=np.float32),
         (fit.frame["user_idx"].to_numpy(), fit.frame["item_idx"].to_numpy())),
        shape=fit.matrix.shape, dtype=np.float32,
    )
    matrix.sort_indices()
    return matrix


def save_split(split: DaySplit, path: str | Path) -> None:
    payload = {
        "train_days": split.train_days.tolist(),
        "validation_days": split.validation_days.tolist(),
        "test_days": split.test_days.tolist(),
        "train_end_day": split.train_end,
        "validation_end_day": split.validation_end,
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
