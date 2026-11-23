# Twitch New-Channel Recommendation: One-Million-User Rerun

## Scope

This rerun increases the training cohort to exactly **1,000,000 users**, or
**6.4415%** of the 15,524,309 users in the complete source file. The systematic,
deterministic cohort preserves every interaction belonging to a selected user and
contains **30,585,070 interactions** (6.4433% of source rows), **464,657 channels**,
and all 43 relative days.

The complete source was previously validated as 474,676,930 interactions,
15,524,309 users, and 790,100 raw channel names. Selection details are recorded in
`outputs_million/cohort_manifest.json`.

## Evaluation protocol

The leakage-safe chronological split is unchanged:

- train: relative days 0--29;
- validation: days 30--35;
- final refit: days 0--35;
- test: days 36--42.

Candidates are fit-period channels that the user has not previously watched. A
positive is the first target-period occurrence of a previously unseen user-channel
pair. Recall@10, NDCG@10, and Hit Rate@10 are macro-averaged over user/day cases.

Training uses all one million selected users. To keep exact ranking over hundreds
of thousands of channels within the available memory, evaluation uses deterministic
fixed-seed user samples capped at 2,000 validation users and 5,000 test users. After
candidate filtering, the evaluated sets contain **1,931 validation users / 3,659
cases** and **4,895 test users / 9,748 cases**. These are evaluation samples, not the
number of users used to train the models.

Validation candidate coverage is **84.92%**; test candidate coverage is **87.84%**.
Coverage includes all novel positives in the denominator, including channels absent
from the fit-period catalog.

## Models and selected settings

The rerun evaluates overall popularity, seven-day recent popularity, binary
ItemKNN, BPR, standardized-score hybrids, and popularity penalties. Validation
searched ItemKNN `k` in 50/100/200 and eight BPR combinations across 32/64 factors,
regularization 0.0025/0.01, and 10/20 epochs.

Validation selected:

```json
{
  "item_knn": {"neighbors": 200},
  "bpr": {
    "factors": 64,
    "learning_rate": 0.03,
    "regularization": 0.0025,
    "epochs": 20,
    "negative_samples": 1,
    "seed": 258
  },
  "hybrid_model_name": "hybrid_a0.75"
}
```

The selected hybrid assigns 75% weight to standardized BPR scores and 25% to
standardized ItemKNN scores, following `alpha * BPR + (1 - alpha) * ItemKNN`.
Validation did not select a popularity penalty.

## Held-out test results

| Model | Recall@10 | NDCG@10 | Hit Rate@10 | Catalog Coverage | Novelty (bits) | Long-tail Exposure |
|---|---:|---:|---:|---:|---:|---:|
| Hybrid alpha=0.75 | **0.221204** | **0.131703** | **0.277595** | 0.020932 | 12.3292 | 0.046987 |
| ItemKNN | 0.218741 | 0.130398 | 0.274518 | **0.023258** | **12.6043** | **0.066210** |
| BPR | 0.081065 | 0.043017 | 0.107304 | 0.001381 | 9.7705 | 0.000000 |
| Popularity | 0.057247 | 0.035717 | 0.077349 | 0.000070 | 7.6470 | 0.000000 |
| Recent popularity | 0.056563 | 0.035291 | 0.076323 | 0.000061 | 7.8533 | 0.000000 |

Hybrid remains the best accuracy model. Relative to ItemKNN, it improves NDCG@10
by **1.00%** and Recall@10 by **1.13%**. Relative to the stronger popularity
baseline in this test sample, hybrid improves NDCG@10 by **268.73%** and Recall@10
by **286.41%**.

ItemKNN remains substantially stronger than BPR alone, while BPR still supplies
complementary hits. At the evaluated positive-pair level, BPR alone retrieves 421,
ItemKNN alone retrieves 2,254, both retrieve 675, and neither retrieves 11,279.

## Comparison with the independent approximately-100k cohort

| Model | 100k Recall@10 | 1m Recall@10 | 100k NDCG@10 | 1m NDCG@10 | NDCG change |
|---|---:|---:|---:|---:|---:|
| Hybrid alpha=0.75 | 0.224644 | 0.221204 | 0.132178 | 0.131703 | -0.000475 |
| ItemKNN | 0.215126 | 0.218741 | 0.126534 | 0.130398 | +0.003864 |
| BPR | 0.093488 | 0.081065 | 0.053731 | 0.043017 | -0.010715 |
| Recent popularity | 0.061265 | 0.056563 | 0.037562 | 0.035291 | -0.002271 |
| Popularity | 0.060668 | 0.057247 | 0.037277 | 0.035717 | -0.001560 |

The central conclusion is stable: hybrid is best, ItemKNN is the strongest single
personalized model, and alpha 0.75 remains optimal. Hybrid NDCG changes by only
-0.000475 (-0.36%) despite a tenfold larger training cohort. ItemKNN improves,
whereas BPR alone declines on this test sample.

These rows are not a controlled learning-curve estimate: the 100k run evaluates all
52,794 eligible users in that cohort, while the one-million run evaluates a fixed
sample of 4,895 eligible users from a different cohort. Differences therefore mix
training-size, cohort, catalog, and finite-test-sample effects. Catalog coverage is
especially not directly comparable because its denominator expands with the much
larger fitted catalog.

## Limitations

- The test metrics estimate performance on a fixed-seed sample, not every eligible
  test user in the one-million-user cohort.
- Fit-period unseen channels remain cold-start items and cannot be ranked by these
  collaborative models.
- The data cannot establish whether a channel was live at a precise recommendation
  instant; recent popularity is an activity proxy only.
- Unobserved interactions used by BPR are sampled comparisons, not explicit dislikes.
- The count-weighted ItemKNN sensitivity model and seven-day active-candidate
  sensitivity analysis were not rerun at one-million-user scale. Their 100k results
  remain available, but should not be presented as one-million-user results.

## Reproducibility

The cohort is generated with `twitch-recs extract-million --config
configs/million.yaml`. The experiment is run with `twitch-recs run-million --config
configs/million.yaml`. Raw metrics, coverage, complementarity, selected settings,
and the complete validation grid are stored under `outputs_million/`.

