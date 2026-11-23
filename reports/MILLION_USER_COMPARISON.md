# 100k vs. 200k vs. 500k vs. One-Million-User Experiment

All four runs use seed 258, the same hyperparameter grid, at most 2,000 validation
users and 5,000 test users, and exact full-catalog ranking.

| Model | 100k Recall@10 | 200k Recall@10 | 500k Recall@10 | 1m Recall@10 | 100k NDCG@10 | 200k NDCG@10 | 500k NDCG@10 | 1m NDCG@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Hybrid alpha=0.75 | 0.223404 | 0.221330 | 0.221675 | 0.221204 | 0.131664 | 0.130060 | 0.128898 | 0.131703 |
| ItemKNN | 0.216272 | 0.214995 | 0.217265 | 0.218741 | 0.126656 | 0.126065 | 0.126900 | 0.130398 |
| BPR | 0.099274 | 0.092004 | 0.080066 | 0.081065 | 0.055802 | 0.052964 | 0.041878 | 0.043017 |
| Recent popularity | 0.064194 | 0.062528 | 0.056566 | 0.056563 | 0.038313 | 0.038261 | 0.034819 | 0.035291 |
| Popularity | 0.061701 | 0.062150 | 0.056558 | 0.057247 | 0.037433 | 0.037716 | 0.034773 | 0.035717 |

| Cohort | Interactions | Channels | Validation users | Test users | Wall-clock minutes |
|---:|---:|---:|---:|---:|---:|
| 100k | 3,060,364 | 162,166 | 1,880 | 4,789 | 8.12 |
| 200k | 6,137,983 | 232,868 | 1,896 | 4,818 | 13.80 |
| 500k | 15,271,133 | 355,257 | 1,904 | 4,870 | 33.59 |
| 1m | 30,585,070 | 464,657 | 1,931 | 4,895 | 77.08 |

The model order is unchanged at all four scales: Hybrid > ItemKNN > BPR >
popularity baselines. Hybrid NDCG remains in a narrow 0.1289--0.1317 band, and
ItemKNN improves slightly at 1m. BPR does not improve with more users: it falls from
0.0558 at 100k to 0.0419 at 500k and remains at 0.0430 at 1m. The validation search
selects 32 factors at 500k and 64 factors at the other scales, so the best capacity is
not constant as the channel catalog expands.

This is matched-protocol scalability and robustness evidence, not a causal learning
curve. The cohorts are not nested; their users, candidate catalogs, and eligible
evaluation targets differ. A causal training-size experiment would keep the test set
and catalog fixed while adding nested training data.

See `MILLION_USER_REPORT.md` for the full protocol, diversity metrics, candidate
coverage, limitations, and reproducibility commands.
