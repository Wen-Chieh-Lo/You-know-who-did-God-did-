# 100k vs. 500k vs. One-Million-User Experiment

| Model | 100k Recall@10 | 500k Recall@10 | 1m Recall@10 | 100k NDCG@10 | 500k NDCG@10 | 1m NDCG@10 |
|---|---:|---:|---:|---:|---:|---:|
| Hybrid alpha=0.75 | 0.224644 | 0.221675 | 0.221204 | 0.132178 | 0.128898 | 0.131703 |
| ItemKNN | 0.215126 | 0.217265 | 0.218741 | 0.126534 | 0.126900 | 0.130398 |
| BPR | 0.093488 | 0.080066 | 0.081065 | 0.053731 | 0.041878 | 0.043017 |
| Recent popularity | 0.061265 | 0.056566 | 0.056563 | 0.037562 | 0.034819 | 0.035291 |
| Popularity | 0.060668 | 0.056558 | 0.057247 | 0.037277 | 0.034773 | 0.035717 |

The 500k cohort contains 15,271,133 interactions and 355,257 channels; its fixed-seed
evaluation contains 1,904 validation and 4,870 test users after eligibility filtering.
Its full model run completed in 33.59 wall-clock minutes. The one-million-user cohort
contains 30,585,070 interactions and uses 1,931 validation and 4,895 test users.

The ranking is unchanged at all three scales: Hybrid > ItemKNN > BPR > popularity
baselines. Hybrid NDCG stays within 0.1289--0.1322, while ItemKNN rises slightly by
1m. BPR is lower at both larger scales. The 500k validation search selects 32 factors;
the 100k and 1m searches select 64, so hyperparameters are not assumed constant.

This is scalability and robustness evidence, not a controlled learning curve. The
100k results use all 52,794 eligible test users from a different cohort; the 500k and
one-million results use deterministic samples. Cohort, candidate catalog, and
evaluation sample therefore change together with training size.

See `MILLION_USER_REPORT.md` for the full protocol, diversity metrics, candidate
coverage, limitations, and reproducibility commands.
