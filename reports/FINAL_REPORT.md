# Twitch New-Channel Recommendation: Experimental Report

## Research question

This experiment asks whether item-item collaborative filtering or Bayesian Personalized Ranking (BPR) better predicts channels a viewer has never watched, and whether their standardized-score hybrid improves Top-10 accuracy without collapsing recommendation diversity.

## Data

The UCSD Twitch 100k interaction file contains **3,051,733 interactions**, **100,000 users**, and **162,625 channels**. It spans 43 observed relative 24-hour blocks. Time values are relative 10-minute slots—not calendar timestamps—so no weekday or calendar-date interpretation is made.

The five source columns are anonymous user ID, stream/session ID, streamer username, start slot, and stop slot. Streamer username is the stable recommendation item; stream ID is used only for checks.

The source dataset and metadata are published by the UCSD McAuley Lab ([dataset page](https://cseweb.ucsd.edu/~jmcauley/datasets.html#twitch)).

## Leakage-safe task and split

Whole day indices were split chronologically into train `0–29`, validation `30–35`, and test `36–42`. Validation tunes settings using a train-only fit. The final models are then refit on train+validation and evaluated once on test.

Candidates are channels present in the fit period, excluding each viewer's previously watched channels. A positive is the first target-period occurrence of a viewer-channel pair absent from fit history, grouped by the relative day on which it first appears. Empty-target cases are omitted.

The fixed-seed tuning sample contains **5,000 validation users**. Final evaluation includes **all 53,212 eligible test users** and **104,818 user/day cases**.

Validation candidate coverage was **85.01%** and test candidate coverage was **88.02%**. Positives outside the fit catalog are a cold-start limitation and are excluded from rank evaluation but included in this coverage denominator.

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

## Test results

| model                   |   recall_at_10 |   ndcg_at_10 |   hit_rate_at_10 |   catalog_coverage |   novelty_bits |   long_tail_exposure |
|:------------------------|---------------:|-------------:|-----------------:|-------------------:|---------------:|---------------------:|
| hybrid_a0.75            |        0.22342 |      0.13148 |          0.27631 |            0.26363 |       12.07110 |              0.08031 |
| item_knn                |        0.21437 |      0.12584 |          0.26510 |            0.36708 |       12.85157 |              0.14585 |
| item_knn_count_weighted |        0.19862 |      0.11694 |          0.24539 |            0.40495 |       13.61158 |              0.20307 |
| bpr                     |        0.09328 |      0.05420 |          0.12049 |            0.00617 |        9.30445 |              0.00162 |
| recent_popularity       |        0.06195 |      0.03779 |          0.08209 |            0.00020 |        7.86368 |              0.00000 |
| popularity              |        0.06068 |      0.03702 |          0.08018 |            0.00023 |        7.66045 |              0.00000 |

Recall@10, NDCG@10, and Hit Rate@10 are computed for each user/day case and then macro-averaged. Catalog coverage is the fraction of the fit-period catalog appearing in recommendations. Novelty is mean self-information in bits under fit-period distinct-user popularity. Long-tail exposure is the share of recommended channels at or below the configured popularity quantile.

## Model complementarity

At the positive user-channel level, BPR alone recovered **5540**, item-item alone recovered **22559**, both recovered **7648**, and neither recovered **117530**. Nonzero model-only counts indicate potentially useful complementarity; whether the hybrid realizes it is determined by its held-out NDCG rather than by test-driven weight selection.

## Seven-day active-candidate sensitivity

|   cases |   users |   recall_at_10 |   ndcg_at_10 |   hit_rate_at_10 |   catalog_coverage |   novelty_bits |   long_tail_exposure | model                  |   coverage_within_primary_catalog |   overall_positive_candidate_coverage |
|--------:|--------:|---------------:|-------------:|-----------------:|-------------------:|---------------:|---------------------:|:-----------------------|----------------------------------:|--------------------------------------:|
|  104818 |   53212 |        0.23008 |      0.13542 |          0.28454 |            0.18733 |       11.95782 |              0.06112 | hybrid_a0.75_active_7d |                           0.91124 |                               0.80208 |
|  104818 |   53212 |        0.22304 |      0.13093 |          0.27559 |            0.22868 |       12.57866 |              0.10594 | item_knn_active_7d     |                           0.91124 |                               0.80208 |
|  104818 |   53212 |        0.09426 |      0.05482 |          0.12174 |            0.00548 |        9.29969 |              0.00065 | bpr_active_7d          |                           0.91124 |                               0.80208 |
|  104818 |   53212 |        0.06069 |      0.03702 |          0.08020 |            0.00022 |        7.66045 |              0.00000 | popularity_active_7d   |                           0.91124 |                               0.80208 |

All rows use the same seven-day active-channel proxy. This cannot prove that a channel was live at a recommendation instant. `overall_positive_candidate_coverage` includes fit-catalog cold-start positives in its denominator; `coverage_within_primary_catalog` isolates the incremental seven-day restriction.

## Concrete recommendation examples

|   user_id |   rank | channel        |
|----------:|-------:|:---------------|
|         1 |      1 | grimnax        |
|         1 |      2 | videoyun       |
|         1 |      3 | elwind         |
|         1 |      4 | mirandakerry   |
|         1 |      5 | rammus53       |
|         1 |      6 | beatpug        |
|         1 |      7 | sizophren      |
|         1 |      8 | pintipanda     |
|         1 |      9 | uthenera       |
|         1 |     10 | levo           |
|       100 |      1 | rakanoolive    |
|       100 |      2 | singelguy      |
|       100 |      3 | ffearfful      |
|       100 |      4 | rub1ckgod      |
|       100 |      5 | inoid          |
|       100 |      6 | shongxbong     |
|       100 |      7 | rexser_g       |
|       100 |      8 | jmo0oli        |
|       100 |      9 | joker_sb3      |
|       100 |     10 | i6rba5_x       |
|      1000 |      1 | ninja          |
|      1000 |      2 | chap           |
|      1000 |      3 | cloakzy        |
|      1000 |      4 | fortnite       |
|      1000 |      5 | sypherpk       |
|      1000 |      6 | timthetatman   |
|      1000 |      7 | tsm_daequan    |
|      1000 |      8 | drlupo         |
|      1000 |      9 | highdistortion |
|      1000 |     10 | 72hrs          |

## Interpretation and limitations

Supplemental reviewer-oriented analysis in `ASSIGNMENT_EXPERIMENTS.md` evaluates the
static Top-10 against one whole-period target per user, includes catalog-cold positives
in end-to-end denominators, applies user-clustered bootstrap confidence intervals with
Holm correction, and repeats BPR across five training seeds. Those checks preserve the
same model ordering and should be used alongside the daily candidate-conditioned table
below.

The primary comparison should be read directly from the test table: personalized models beat the baseline only when their held-out rows have larger accuracy values. Diversity gains are visible through coverage, novelty, and long-tail exposure and may trade off against accuracy.

The dataset cannot establish whether a channel was actually live at a recommendation instant. The recent seven-day restriction is therefore only an activity proxy. Fit-period unseen channels cannot be learned by these collaborative models. Unobserved channels are sampled comparisons in BPR, not explicit dislikes. Finally, results are not directly comparable to the source paper unless its task, split, candidates, and metrics match this new-channel protocol.

## Related research

Rappaz, McAuley, and Aberer (RecSys 2021), *Recommendation on Live-Streaming Platforms: Dynamic Availability and Repeat Consumption* ([paper](https://cseweb.ucsd.edu/~jmcauley/pdfs/recsys21b.pdf), [DOI](https://doi.org/10.1145/3460231.3474267)), introduced the dataset and LiveRec. Their work emphasizes time-varying stream availability and repeat consumption. This project deliberately asks a different question—discovery of viewer-unseen channels—and uses different candidates, chronological labels, and metrics, so the numeric results are not treated as a direct replication.

## Conclusion

**Personalization wins.** The selected hybrid reaches NDCG@10 **0.13148** and Recall@10 **0.22342**, versus **0.03779** and **0.06195** for recent_popularity; hybrid NDCG is 247.9% higher.

**Item-item is much stronger than BPR alone.** Their NDCG@10 values are **0.12584** and **0.05420**, respectively. BPR still uniquely recovers **5,540** positive pairs, while item-CF uniquely recovers **22,559**, demonstrating complementary hits.

**The hybrid uses that complementarity.** Validation selected `hybrid_a0.75`; its test NDCG is 4.5% above item-CF. Alpha and the popularity penalty were frozen before test.

**The gain trades away some diversity.** Hybrid catalog coverage is **0.264** versus **0.367** for item-CF, while novelty is **12.07** versus **12.85** bits. Validation selected no nonzero popularity penalty, so the adjusted variant did not merit a separate final row.

## Reproducibility

The repository records the seed, day boundaries, candidate definition, validation grid, selected settings, package constraints, per-case metrics, recommendations, mappings, tables, and figures. Run `twitch-recs all --config configs/full.yaml` to reproduce the complete experiment.
