# Original 100k vs. Complete-File Cohort Rerun

## Scope

The uploaded `full_a.csv.gz` passed gzip validation and was scanned completely:

- 474,676,930 interaction rows
- 15,524,309 users
- 790,100 raw channel names
- 43 relative 24-hour blocks

Exact BPR training and exact 790k-channel ranking for all 15.5 million users cannot
fit safely in the available 7.5 GiB RAM. The robustness rerun therefore selected an
independent deterministic user cohort with
`blake2b(seed:user_id) % 155 == 0`, preserving every interaction for those users.
The resulting cohort has 99,660 users, 3,034,146 interactions, and 161,021 channels.
All complete-file rows were still validated and used to generate global activity and
distinct-viewer popularity statistics.

## Held-out test comparison

| Model | Original Recall@10 | Rerun Recall@10 | Original NDCG@10 | Rerun NDCG@10 | NDCG change |
|---|---:|---:|---:|---:|---:|
| Hybrid α=0.75 | 0.223415 | 0.224644 | 0.131477 | 0.132178 | +0.000701 |
| Item-item CF | 0.214368 | 0.215126 | 0.125840 | 0.126534 | +0.000694 |
| Count-weighted Item-item | 0.198621 | 0.200938 | 0.116943 | 0.117895 | +0.000952 |
| BPR | 0.093284 | 0.093488 | 0.054197 | 0.053731 | −0.000466 |
| Recent popularity | 0.061952 | 0.061265 | 0.037789 | 0.037562 | −0.000227 |
| Popularity | 0.060680 | 0.060668 | 0.037021 | 0.037277 | +0.000256 |

The rerun evaluates 52,794 eligible users and 103,930 user/day cases. Test candidate
coverage is 88.23%, compared with 88.02% in the original run.

## Selected settings

Both experiments selected:

- Item-item neighbors: 200
- Hybrid α: 0.75
- Popularity penalty: 0
- BPR regularization: 0.0025
- BPR epochs: 20

The only selected-setting difference is BPR dimension: the original cohort selected
64 factors, while the independent cohort selected 32. Because BPR alone remains well
below item-item and the hybrid result is stable, this does not change the conclusion.

## Complete-source popularity check

Using distinct-viewer popularity calculated from all 15,524,309 source users, while
keeping the same cohort candidate catalog and test users, gives:

| Baseline | Recall@10 | NDCG@10 |
|---|---:|---:|
| Full-source recent popularity | 0.061506 | 0.037638 |
| Full-source overall popularity | 0.060590 | 0.037108 |

These are almost identical to cohort-only popularity and remain far below the hybrid.

## Conclusion

The original conclusions replicate on an independently sampled cohort from the
complete file. Hybrid remains best, item-item remains much stronger than BPR alone,
α=0.75 remains optimal, and the accuracy/diversity trade-off is essentially unchanged.
The Hybrid NDCG difference between runs is only +0.000701 (about +0.53% relative), so
there is no evidence that the original result was an artifact of that particular 100k
subset.
