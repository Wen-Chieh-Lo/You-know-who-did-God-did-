import numpy as np
from scipy import sparse

from twitch_recs.models import BPR, ItemKNN
from twitch_recs.recommend import personalized_recommendations


def matrix():
    return sparse.csr_matrix(np.array([
        [1, 1, 0, 0],
        [1, 1, 0, 0],
        [0, 0, 1, 1],
        [0, 0, 1, 1],
    ], dtype=np.float32))


def test_item_knn_finds_co_viewed_item():
    model = ItemKNN(neighbors=2, batch_size=2).fit(matrix())
    scores = model.score_user(sparse.csr_matrix([[1, 0, 0, 0]], dtype=np.float32))
    assert int(np.argmax(scores)) == 1
    assert scores[1] > scores[2]


def test_bpr_is_deterministic_and_finite():
    first = BPR(factors=4, epochs=5, seed=7).fit(matrix())
    second = BPR(factors=4, epochs=5, seed=7).fit(matrix())
    assert np.isfinite(first.score_user(0)).all()
    np.testing.assert_allclose(first.user_factors_, second.user_factors_)
    np.testing.assert_allclose(first.item_factors_, second.item_factors_)


def test_hybrid_endpoints_have_no_nan_and_match_component_rankings():
    x = matrix()
    item = ItemKNN(neighbors=2, batch_size=2).fit(x)
    bpr = BPR(factors=4, epochs=2, seed=7).fit(x)
    recs = personalized_recommendations(
        [0], x, item, bpr, np.asarray(x.sum(axis=0)).ravel(), k=2,
        alphas=[0.0, 1.0], lambdas=[0.0],
    )
    assert np.isfinite(recs["hybrid_a0"]["score"]).all()
    assert np.isfinite(recs["hybrid_a1"]["score"]).all()
    assert recs["hybrid_a0"]["item_idx"].tolist() == recs["item_knn"]["item_idx"].tolist()
    assert recs["hybrid_a1"]["item_idx"].tolist() == recs["bpr"]["item_idx"].tolist()


def test_personalized_candidate_mask_is_shared_by_every_model():
    x = matrix()
    item = ItemKNN(neighbors=2, batch_size=2).fit(x)
    bpr = BPR(factors=4, epochs=2, seed=7).fit(x)
    mask = np.array([False, False, True, True])
    recs = personalized_recommendations(
        [0], x, item, bpr, np.asarray(x.sum(axis=0)).ravel(), k=2,
        alphas=[0.5], lambdas=[0.1], candidate_mask=mask,
    )
    for frame in recs.values():
        assert set(frame["item_idx"]).issubset({2, 3})

