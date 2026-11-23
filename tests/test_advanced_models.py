import numpy as np
import pandas as pd
from scipy import sparse

from twitch_recs.models.advanced import _sample_unseen, time_decayed_matrix


def test_sample_unseen_never_returns_observed_item():
    matrix = sparse.csr_matrix(np.array([
        [1, 1, 0, 0],
        [0, 0, 1, 0],
    ], dtype=np.float32))
    users = np.array([0, 0, 1, 1], dtype=np.int64)
    sampled = _sample_unseen(matrix.indptr, matrix.indices, users, 4, 7)
    for user, item in zip(users, sampled):
        assert item not in matrix[int(user)].indices


def test_time_decay_gives_recent_interaction_more_weight():
    class Fit:
        matrix = sparse.csr_matrix((1, 2), dtype=np.float32)
        frame = pd.DataFrame({
            "user_idx": [0, 0], "item_idx": [0, 1], "day": [0, 10]
        })

    weighted = time_decayed_matrix(Fit(), decay=0.1)
    assert weighted[0, 1] > weighted[0, 0]
    assert weighted[0, 1] == 1.0
