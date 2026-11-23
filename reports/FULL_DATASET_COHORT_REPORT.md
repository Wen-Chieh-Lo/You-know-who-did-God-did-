# Twitch New-Channel Recommendation: Complete-File Cohort Rerun

## Research question

This experiment asks whether item-item collaborative filtering or Bayesian Personalized Ranking (BPR) better predicts channels a viewer has never watched, and whether their standardized-score hybrid improves Top-10 accuracy without collapsing recommendation diversity.

## Data

The complete source scan contains **474,676,930 interactions**, **15,524,309 users**, and **790,100 raw channel names**. A deterministic independent cohort contains **3,034,146 interactions**, **99,660 users**, and **161,021 channels**. It spans 43 observed relative 24-hour blocks. Time values are relative 10-minute slots—not calendar timestamps—so no weekday or calendar-date interpretation is made.

The five source columns are anonymous user ID, stream/session ID, streamer username, start slot, and stop slot. Streamer username is the stable recommendation item; stream ID is used only for checks.

The source dataset and metadata are published by the UCSD McAuley Lab ([dataset page](https://cseweb.ucsd.edu/~jmcauley/datasets.html#twitch)).

## Leakage-safe task and split

Whole day indices were split chronologically into train `0–29`, validation `30–35`, and test `36–42`. Validation tunes settings using a train-only fit. The final models are then refit on train+validation and evaluated once on test.

Candidates are channels present in the fit period, excluding each viewer's previously watched channels. A positive is the first target-period occurrence of a viewer-channel pair absent from fit history, grouped by the relative day on which it first appears. Empty-target cases are omitted.

The fixed-seed tuning sample contains **5,000 validation users**. Final evaluation includes **all 52,794 eligible test users** and **103,930 user/day cases**.

Validation candidate coverage was **84.75%** and test candidate coverage was **88.23%**. Positives outside the fit catalog are a cold-start limitation and are excluded from rank evaluation but included in this coverage denominator.

## Models

- **Recent popularity:** distinct viewers per channel, with a seven-day variant.
- **Item-item CF:** binary user-channel cosine similarity, retaining only each item's top-k neighbors.
- **BPR:** pairwise implicit-feedback matrix factorization trained with sampled unobserved comparisons.
- **Hybrid:** per-user standardized BPR and item-CF scores combined by validation-selected alpha.
- **Popularity-adjusted hybrid:** subtracts lambda times `log(1 + channel popularity)`.
- **Count-weighted sensitivity model:** repeats item-CF with interaction counts instead of binary feedback.

Selected validation settings:

```json
{
  "item_knn": {
    "neighbors": 200
  },
  "bpr": {
    "factors": 32,
    "learning_rate": 0.03,
    "regularization": 0.0025,
    "epochs": 20,
    "negative_samples": 1,
    "seed": 258
  },
  "hybrid_model_name": "hybrid_a0.75"
}
```

## Test results

| model                   |   recall_at_10 |   ndcg_at_10 |   hit_rate_at_10 |   catalog_coverage |   novelty_bits |   long_tail_exposure |
|:------------------------|---------------:|-------------:|-----------------:|-------------------:|---------------:|---------------------:|
| hybrid_a0.75            |        0.22464 |      0.13218 |          0.27723 |            0.26583 |       12.08438 |              0.08005 |
| item_knn                |        0.21513 |      0.12653 |          0.26493 |            0.36542 |       12.83886 |              0.14291 |
| item_knn_count_weighted |        0.20094 |      0.11789 |          0.24732 |            0.40231 |       13.60326 |              0.20021 |
| bpr                     |        0.09349 |      0.05373 |          0.11962 |            0.00597 |        9.21530 |              0.00001 |
| recent_popularity       |        0.06126 |      0.03756 |          0.08141 |            0.00020 |        7.86319 |              0.00000 |
| popularity              |        0.06067 |      0.03728 |          0.07968 |            0.00023 |        7.65699 |              0.00000 |

Recall@10, NDCG@10, and Hit Rate@10 are computed for each user/day case and then macro-averaged. Catalog coverage is the fraction of the fit-period catalog appearing in recommendations. Novelty is mean self-information in bits under fit-period distinct-user popularity. Long-tail exposure is the share of recommended channels at or below the configured popularity quantile.

## Model complementarity

At the positive user-channel level, BPR alone recovered **5317**, item-item alone recovered **22192**, both recovered **7777**, and neither recovered **116065**. Nonzero model-only counts indicate potentially useful complementarity; whether the hybrid realizes it is determined by its held-out NDCG rather than by test-driven weight selection.

## Seven-day active-candidate sensitivity

|   cases |   users |   recall_at_10 |   ndcg_at_10 |   hit_rate_at_10 |   catalog_coverage |   novelty_bits |   long_tail_exposure | model                  |   coverage_within_primary_catalog |   overall_positive_candidate_coverage |
|--------:|--------:|---------------:|-------------:|-----------------:|-------------------:|---------------:|---------------------:|:-----------------------|----------------------------------:|--------------------------------------:|
|  103930 |   52794 |        0.23116 |      0.13594 |          0.28541 |            0.18812 |       11.96334 |              0.06002 | hybrid_a0.75_active_7d |                           0.91084 |                               0.80365 |
|  103930 |   52794 |        0.22466 |      0.13170 |          0.27691 |            0.22789 |       12.56509 |              0.10260 | item_knn_active_7d     |                           0.91084 |                               0.80365 |
|  103930 |   52794 |        0.09444 |      0.05447 |          0.12084 |            0.00559 |        9.21607 |              0.00039 | bpr_active_7d          |                           0.91084 |                               0.80365 |
|  103930 |   52794 |        0.06067 |      0.03728 |          0.07968 |            0.00023 |        7.65699 |              0.00000 | popularity_active_7d   |                           0.91084 |                               0.80365 |

All rows use the same seven-day active-channel proxy. This cannot prove that a channel was live at a recommendation instant. `overall_positive_candidate_coverage` includes fit-catalog cold-start positives in its denominator; `coverage_within_primary_catalog` isolates the incremental seven-day restriction.

## Concrete recommendation examples

|   user_id |   rank | channel         |
|----------:|-------:|:----------------|
|  10000141 |      1 | denly           |
|  10000141 |      2 | tenderlybae     |
|  10000141 |      3 | hardgamechannel |
|  10000141 |      4 | follentass      |
|  10000141 |      5 | dinik           |
|  10000141 |      6 | gladiatorpwnz   |
|  10000141 |      7 | stintik         |
|  10000141 |      8 | b_u_l_o_c_h_k_a |
|  10000141 |      9 | tati            |
|  10000141 |     10 | manyrin         |
|  10000439 |      1 | mickalow        |
|  10000439 |      2 | xewer           |
|  10000439 |      3 | doigby          |
|  10000439 |      4 | domingo         |
|  10000439 |      5 | maxalibur       |
|  10000439 |      6 | kamet0          |
|  10000439 |      7 | robi            |
|  10000439 |      8 | willokhlass     |
|  10000439 |      9 | sardoche        |
|  10000439 |     10 | jltomy          |
|  10000621 |      1 | punkdagod       |
|  10000621 |      2 | daigothebeastv  |
|  10000621 |      3 | nycfurby        |
|  10000621 |      4 | ceroblast       |
|  10000621 |      5 | vesperarcade    |
|  10000621 |      6 | stupendous      |
|  10000621 |      7 | floe            |
|  10000621 |      8 | chris_tatarian  |
|  10000621 |      9 | sajam           |
|  10000621 |     10 | zaferino1       |

## Interpretation and limitations

The primary comparison should be read directly from the test table: personalized models beat the baseline only when their held-out rows have larger accuracy values. Diversity gains are visible through coverage, novelty, and long-tail exposure and may trade off against accuracy.

The dataset cannot establish whether a channel was actually live at a recommendation instant. The recent seven-day restriction is therefore only an activity proxy. Fit-period unseen channels cannot be learned by these collaborative models. Unobserved channels are sampled comparisons in BPR, not explicit dislikes. Finally, results are not directly comparable to the source paper unless its task, split, candidates, and metrics match this new-channel protocol.

## Related research

Rappaz, McAuley, and Aberer (RecSys 2021), *Recommendation on Live-Streaming Platforms: Dynamic Availability and Repeat Consumption* ([paper](https://cseweb.ucsd.edu/~jmcauley/pdfs/recsys21b.pdf), [DOI](https://doi.org/10.1145/3460231.3474267)), introduced the dataset and LiveRec. Their work emphasizes time-varying stream availability and repeat consumption. This project deliberately asks a different question—discovery of viewer-unseen channels—and uses different candidates, chronological labels, and metrics, so the numeric results are not treated as a direct replication.

## Conclusion

**Personalization wins.** The selected hybrid reaches NDCG@10 **0.13218** and Recall@10 **0.22464**, versus **0.03756** and **0.06126** for recent_popularity; hybrid NDCG is 251.9% higher.

**Item-item is much stronger than BPR alone.** Their NDCG@10 values are **0.12653** and **0.05373**, respectively. BPR still uniquely recovers **5,317** positive pairs, while item-CF uniquely recovers **22,192**, demonstrating complementary hits.

**The hybrid uses that complementarity.** Validation selected `hybrid_a0.75`; its test NDCG is 4.5% above item-CF. Alpha and the popularity penalty were frozen before test.

**The gain trades away some diversity.** Hybrid catalog coverage is **0.266** versus **0.365** for item-CF, while novelty is **12.08** versus **12.84** bits. Validation selected no nonzero popularity penalty, so the adjusted variant did not merit a separate final row.

## Reproducibility

The repository records the seed, day boundaries, candidate definition, validation grid, selected settings, package constraints, per-case metrics, recommendations, mappings, tables, and figures. Run `twitch-recs all --config configs/full.yaml` to reproduce the complete experiment.
