# 100k vs. One-Million-User Experiment

| Model | 100k Recall@10 | 1m Recall@10 | 100k NDCG@10 | 1m NDCG@10 |
|---|---:|---:|---:|---:|
| Hybrid alpha=0.75 | 0.224644 | 0.221204 | 0.132178 | 0.131703 |
| ItemKNN | 0.215126 | 0.218741 | 0.126534 | 0.130398 |
| BPR | 0.093488 | 0.081065 | 0.053731 | 0.043017 |
| Recent popularity | 0.061265 | 0.056563 | 0.037562 | 0.035291 |
| Popularity | 0.060668 | 0.057247 | 0.037277 | 0.035717 |

The one-million-user cohort contains exactly 1,000,000 users and 30,585,070
interactions. It uses every selected user for training, with a fixed-seed evaluation
sample of 1,931 validation and 4,895 test users after eligibility filtering.

The ranking is unchanged: Hybrid > ItemKNN > BPR > popularity baselines. Hybrid
NDCG is nearly unchanged (-0.36% relative), and ItemKNN improves by 3.05% relative.
BPR declines by 19.94% relative on the sampled test set.

This is a robustness comparison, not a controlled learning curve. The 100k results
use all 52,794 eligible test users from a different cohort; the one-million results
use a deterministic sample. Cohort, candidate-catalog, and evaluation-sample changes
are therefore confounded with training size.

See `MILLION_USER_REPORT.md` for the full protocol, diversity metrics, candidate
coverage, limitations, and reproducibility commands.
