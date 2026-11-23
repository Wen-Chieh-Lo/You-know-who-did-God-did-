from __future__ import annotations

import numpy as np
from scipy import sparse
from tqdm.auto import tqdm


class ItemKNN:
    """Top-k item cosine model without materializing a dense item-item matrix."""

    def __init__(self, neighbors: int = 100, batch_size: int = 512):
        self.neighbors = int(neighbors)
        self.batch_size = int(batch_size)
        self.similarity_: sparse.csr_matrix | None = None

    def fit(self, interactions: sparse.csr_matrix) -> "ItemKNN":
        x = interactions.astype(np.float32).tocsr()
        n_items = x.shape[1]
        norms = np.sqrt(np.asarray(x.power(2).sum(axis=0)).ravel())
        norms[norms == 0] = 1.0
        row_parts: list[np.ndarray] = []
        col_parts: list[np.ndarray] = []
        data_parts: list[np.ndarray] = []

        for start in tqdm(range(0, n_items, self.batch_size), desc="Item-CF blocks", leave=False):
            stop = min(start + self.batch_size, n_items)
            cooc = (x[:, start:stop].T @ x).tocsr()
            for local_row in range(stop - start):
                source = start + local_row
                left, right = cooc.indptr[local_row:local_row + 2]
                cols = cooc.indices[left:right]
                values = cooc.data[left:right] / (norms[source] * norms[cols])
                keep = cols != source
                cols, values = cols[keep], values[keep]
                if len(values) > self.neighbors:
                    chosen = np.argpartition(values, -self.neighbors)[-self.neighbors:]
                    cols, values = cols[chosen], values[chosen]
                if len(values):
                    order = np.lexsort((cols, -values))
                    cols, values = cols[order], values[order]
                    row_parts.append(np.full(len(cols), source, dtype=np.int32))
                    col_parts.append(cols.astype(np.int32, copy=False))
                    data_parts.append(values.astype(np.float32, copy=False))
        if data_parts:
            rows = np.concatenate(row_parts)
            cols = np.concatenate(col_parts)
            data = np.concatenate(data_parts)
        else:
            rows = cols = np.empty(0, dtype=np.int32)
            data = np.empty(0, dtype=np.float32)
        self.similarity_ = sparse.csr_matrix((data, (rows, cols)), shape=(n_items, n_items))
        return self

    def score_user(self, user_row: sparse.csr_matrix) -> np.ndarray:
        if self.similarity_ is None:
            raise RuntimeError("Call fit before scoring")
        return (user_row @ self.similarity_).toarray().ravel().astype(np.float32)

