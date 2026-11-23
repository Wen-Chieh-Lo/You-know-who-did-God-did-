import numpy as np
import pandas as pd

from twitch_recs.assignment_analysis import (add_holm_correction,
                                              evaluate_static_protocol,
                                              paired_user_bootstrap)
from twitch_recs.metrics import complementarity, evaluate_ranking


def test_case_level_ranking_metrics():
    recs = pd.DataFrame({"user_idx": [0, 0, 0], "rank": [1, 2, 3],
                         "item_idx": [2, 3, 4], "score": [3.0, 2.0, 1.0]})
    labels = pd.DataFrame({"user_idx": [0, 0], "day": [5, 5], "item_idx": [2, 4]})
    cases, summary = evaluate_ranking(recs, labels, k=3, popularity=np.ones(5), catalog_size=5)
    assert cases.iloc[0]["recall_at_10"] == 1.0
    assert cases.iloc[0]["hit_rate_at_10"] == 1.0
    assert 0 < summary["ndcg_at_10"] <= 1


def test_complementarity_counts_unique_positive_pairs():
    labels = pd.DataFrame({"user_idx": [0, 0, 1], "item_idx": [1, 2, 3]})
    first = pd.DataFrame({"user_idx": [0], "item_idx": [1]})
    second = pd.DataFrame({"user_idx": [0], "item_idx": [2]})
    result = complementarity(labels, first, second)
    assert result == {"BPR_only": 1, "ItemKNN_only": 1, "both": 0, "neither": 1}


def test_paired_user_bootstrap_detects_consistent_improvement():
    left = pd.DataFrame({
        "user_idx": [0, 0, 1, 2], "day": [1, 2, 1, 1],
        "recall_at_10": [1.0, 1.0, 1.0, 1.0],
        "ndcg_at_10": [1.0, 1.0, 1.0, 1.0],
        "hit_rate_at_10": [1.0, 1.0, 1.0, 1.0],
    })
    right = left.copy()
    right[["recall_at_10", "ndcg_at_10", "hit_rate_at_10"]] = 0.0

    rows = paired_user_bootstrap(left, right, "left", "right", samples=200, seed=1)

    assert len(rows) == 3
    assert all(row["point_difference"] == 1.0 for row in rows)
    assert all(row["ci_95_lower"] == 1.0 for row in rows)
    assert all(row["ci_95_upper"] == 1.0 for row in rows)


def test_static_protocol_counts_cold_start_in_end_to_end_denominator():
    recs = pd.DataFrame({
        "user_idx": [0, 0], "rank": [1, 2], "item_idx": [2, 3], "score": [2.0, 1.0]
    })
    targets = pd.DataFrame({
        "user_idx": [0, 0], "day": [5, 6], "channel": ["known", "cold"],
        "item_idx": [2.0, np.nan], "candidate_covered": [True, False],
    })

    cases, summary = evaluate_static_protocol(recs, targets, k=2, by_day=False)

    assert cases.iloc[0]["candidate_recall_at_10"] == 1.0
    assert cases.iloc[0]["end_to_end_recall_at_10"] == 0.5
    assert summary["users"] == 1


def test_holm_correction_controls_familywise_error():
    frame = pd.DataFrame({"two_sided_p_value": [0.01, 0.03, 0.2]})
    result = add_holm_correction(frame)
    assert np.allclose(result["holm_adjusted_p"], [0.03, 0.06, 0.2])
    assert result["significant_after_holm_0_05"].tolist() == [True, False, False]

