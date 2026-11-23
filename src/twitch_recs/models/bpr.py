from __future__ import annotations

import numpy as np
from numba import njit
from scipy import sparse


@njit(cache=True)
def _contains(sorted_values: np.ndarray, value: int) -> bool:
    lo, hi = 0, len(sorted_values)
    while lo < hi:
        mid = (lo + hi) // 2
        if sorted_values[mid] < value:
            lo = mid + 1
        else:
            hi = mid
    return lo < len(sorted_values) and sorted_values[lo] == value


@njit(cache=True)
def _sigmoid_negative(x: float) -> float:
    # sigmoid(-x), written stably.
    if x >= 0:
        z = np.exp(-x)
        return z / (1.0 + z)
    z = np.exp(x)
    return 1.0 / (1.0 + z)


@njit(cache=True)
def _train_bpr(user_factors: np.ndarray, item_factors: np.ndarray,
               indptr: np.ndarray, indices: np.ndarray, positive_users: np.ndarray,
               positive_items: np.ndarray, epochs: int, learning_rate: float,
               regularization: float, negative_samples: int, seed: int) -> None:
    np.random.seed(seed)
    n_items = item_factors.shape[0]
    order = np.arange(len(positive_users))
    for _ in range(epochs):
        np.random.shuffle(order)
        for position in order:
            u = positive_users[position]
            i = positive_items[position]
            history = indices[indptr[u]:indptr[u + 1]]
            if len(history) >= n_items:
                continue
            for _sample in range(negative_samples):
                j = np.random.randint(0, n_items)
                while _contains(history, j):
                    j = np.random.randint(0, n_items)
                diff = 0.0
                for f in range(user_factors.shape[1]):
                    diff += user_factors[u, f] * (item_factors[i, f] - item_factors[j, f])
                gradient = _sigmoid_negative(diff)
                for f in range(user_factors.shape[1]):
                    old_u = user_factors[u, f]
                    old_i = item_factors[i, f]
                    old_j = item_factors[j, f]
                    user_factors[u, f] += learning_rate * (
                        gradient * (old_i - old_j) - regularization * old_u
                    )
                    item_factors[i, f] += learning_rate * (
                        gradient * old_u - regularization * old_i
                    )
                    item_factors[j, f] += learning_rate * (
                        -gradient * old_u - regularization * old_j
                    )


class BPR:
    """Pairwise matrix factorization for binary implicit feedback."""

    def __init__(self, factors: int = 64, learning_rate: float = 0.03,
                 regularization: float = 0.01, epochs: int = 20,
                 negative_samples: int = 1, seed: int = 258):
        self.factors = int(factors)
        self.learning_rate = float(learning_rate)
        self.regularization = float(regularization)
        self.epochs = int(epochs)
        self.negative_samples = int(negative_samples)
        self.seed = int(seed)
        self.user_factors_: np.ndarray | None = None
        self.item_factors_: np.ndarray | None = None

    def fit(self, interactions: sparse.csr_matrix) -> "BPR":
        x = interactions.astype(np.float32).tocsr(copy=True)
        x.sort_indices()
        users, items = x.nonzero()
        rng = np.random.default_rng(self.seed)
        scale = 0.1 / np.sqrt(max(1, self.factors))
        self.user_factors_ = rng.normal(0, scale, (x.shape[0], self.factors)).astype(np.float32)
        self.item_factors_ = rng.normal(0, scale, (x.shape[1], self.factors)).astype(np.float32)
        _train_bpr(
            self.user_factors_, self.item_factors_, x.indptr.astype(np.int64),
            x.indices.astype(np.int32), users.astype(np.int32), items.astype(np.int32),
            self.epochs, self.learning_rate, self.regularization,
            self.negative_samples, self.seed,
        )
        return self

    def score_user(self, user_idx: int) -> np.ndarray:
        if self.user_factors_ is None or self.item_factors_ is None:
            raise RuntimeError("Call fit before scoring")
        return (self.item_factors_ @ self.user_factors_[user_idx]).astype(np.float32)

