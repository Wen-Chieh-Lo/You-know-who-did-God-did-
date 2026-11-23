# Assignment 2 Supplemental Experiments

## Purpose and protocol

These experiments address the Assignment 2 requirements concerning statistical
validity, comparison of feature representations, temporal robustness, data quality,
and scaling. The official Twitch 100k experiment remains the primary evaluation
because it ranks for every eligible test user and stores case-level scores.

All temporal robustness models use settings selected by the original validation
period: ItemKNN with 200 neighbors, BPR with 64 factors, regularization 0.0025 and
20 epochs, and the hybrid

`0.75 * standardized BPR + 0.25 * standardized ItemKNN`.

The earlier windows are retrospective robustness checks. Their results are not used
to change hyperparameters.

## User-clustered paired bootstrap

The original held-out test contains multiple day cases for some users, so treating
all 104,818 cases as independent would understate uncertainty. We therefore merge
model results on `(user_idx, day)`, resample the 53,212 users with replacement, retain
all cases belonging to each sampled user, and repeat this process 10,000 times.

| Paired comparison | Metric | Difference | 95% user-clustered CI | Two-sided p |
|---|---|---:|---:|---:|
| Hybrid - ItemKNN | Recall@10 | +0.009047 | [0.008128, 0.009964] | <0.001 |
| Hybrid - ItemKNN | NDCG@10 | +0.005638 | [0.005201, 0.006088] | <0.001 |
| Hybrid - ItemKNN | Hit Rate@10 | +0.011210 | [0.010118, 0.012292] | <0.001 |
| Hybrid - BPR | NDCG@10 | +0.077280 | [0.075766, 0.078835] | <0.001 |
| Hybrid - Recent popularity | NDCG@10 | +0.093688 | [0.092080, 0.095314] | <0.001 |
| Binary ItemKNN - count-weighted ItemKNN | NDCG@10 | +0.008897 | [0.008041, 0.009746] | <0.001 |

The smallest attainable nonzero two-sided p-value with the finite-sample correction
used here is approximately 0.0002; all intervals above exclude zero. The hybrid's
modest point improvement over ItemKNN is therefore statistically distinguishable,
not merely a ranking of two noisy point estimates.

Holm family-wise correction across all 12 reported daily-case comparisons gives
adjusted p-values of 0.00240, so every conclusion remains significant at 0.05. These
intervals are conditional on the fitted models and quantify test-user sampling
uncertainty; the separate multi-seed experiment below addresses training randomness.

## Protocol-aligned static-period evaluation

The deployed offline protocol produces one Top-10 list per user after day 35. The
original daily-case metric evaluates this same static list against each target day.
To align the evaluation unit exactly with the recommendation unit, we additionally
collapse all first-time novel channels from days 36-42 into one target set per user.
This period-level protocol is the preferred primary interpretation; daily-case macro
averages remain a sensitivity analysis.

| Model | Candidate Recall@10 | End-to-end Recall@10 | Candidate NDCG@10 | Cold-start-adjusted NDCG@10 | Hit Rate@10 |
|---|---:|---:|---:|---:|---:|
| Hybrid | **0.242122** | **0.221125** | **0.169206** | **0.156841** | **0.413481** |
| ItemKNN | 0.231724 | 0.211851 | 0.161636 | 0.149917 | 0.396100 |
| Count-weighted ItemKNN | 0.215265 | 0.196822 | 0.150358 | 0.139385 | 0.371034 |
| BPR | 0.103273 | 0.094426 | 0.070993 | 0.065851 | 0.201049 |
| Recent popularity | 0.067085 | 0.061124 | 0.048877 | 0.045176 | 0.138868 |
| Popularity | 0.066359 | 0.060391 | 0.048113 | 0.044443 | 0.135152 |

Candidate metrics condition on positives present in the fit-period catalog. End-to-end
metrics retain all novel positives in their denominators; catalog-cold channels are
unavailable and therefore cannot be hits. Among 55,693 known users with a novel test
positive, 2,481 have no catalog-covered positive at all. The model ordering remains
unchanged under both definitions.

At period level, Hybrid improves cold-start-adjusted NDCG over ItemKNN by 0.006924,
with user-paired 95% CI [0.006371, 0.007475] and Holm-adjusted p=0.000600. Its
end-to-end Recall improvement is 0.009275, CI [0.008298, 0.010258].

## Eligibility funnel

| Stage | Users |
|---|---:|
| All dataset users | 100,000 |
| Active during days 36-42 | 74,265 |
| Test-active and known in fit | 72,887 |
| Known users with a novel-channel positive | 55,693 |
| With at least one catalog-covered positive | 53,212 |

The original candidate-conditioned daily evaluation contains 104,818 user/day cases;
including all-cold-start cases yields 114,310. This makes explicit that reported
ranking accuracy is conditional on users who are active and produce at least one novel
target, rather than all 100,000 source users.

## BPR training-seed stability

The selected BPR settings were retrained with seeds 258, 1258, 2258, 3258, and 4258.
Every run uses the same deterministic sample of 5,000 test users and 9,974 user/day
cases; seeds are summarized rather than selected by test performance.

| Model | Seeds | Recall@10 mean +/- SD | NDCG@10 mean +/- SD | Hit Rate@10 mean +/- SD |
|---|---:|---:|---:|---:|
| BPR | 5 | 0.094215 +/- 0.002335 | 0.054568 +/- 0.001843 | 0.122599 +/- 0.003446 |
| Hybrid | 5 | 0.217245 +/- 0.000467 | 0.128741 +/- 0.000179 | 0.270323 +/- 0.000397 |

BPR varies modestly across negative-sampling and initialization seeds, but remains far
below ItemKNN. Hybrid is substantially more stable because the deterministic ItemKNN
signal and score standardization damp BPR variation. The original single-seed ranking
is therefore not an unlucky-seed artifact.

## Validation-user sample stability

The full tuning pipeline uses a deterministic 5,000-user validation sample for
tractability. To test whether that sample happened to favor the reported settings, we
repeat the comparison on samples generated with seeds 258, 1258, 2258, 3258, and
4258. The restricted stability grid compares ItemKNN k=100/200, BPR weights
alpha=0.5/0.75, and popularity penalties lambda=0/0.05 while keeping the trained
models and all other settings fixed.

| Validation sample seed | Selected ItemKNN | Selected hybrid | Best hybrid NDCG@10 |
|---:|---|---|---:|
| 258 | k=200 | alpha=0.75, lambda=0 | 0.129923 |
| 1258 | k=200 | alpha=0.75, lambda=0 | 0.133970 |
| 2258 | k=200 | alpha=0.75, lambda=0 | 0.137643 |
| 3258 | k=200 | alpha=0.75, lambda=0 | 0.139262 |
| 4258 | k=200 | alpha=0.75, lambda=0 | 0.139361 |

All five samples select the same k, alpha, and zero popularity penalty. Across samples,
hybrid alpha=0.75 has mean validation NDCG 0.136032 (SD 0.004053), versus 0.132474
for alpha=0.5 and 0.129878 for ItemKNN k=200. The reported configuration is therefore
stable to validation-user sampling within the plausible alternatives surrounding the
original optimum. This is a selection-sample sensitivity analysis, not a replacement
for the original full hyperparameter grid.

## Rolling-origin temporal robustness

| Target window | Model | Recall@10 | NDCG@10 | Hit Rate@10 |
|---|---|---:|---:|---:|
| days 18-23 | Hybrid | **0.267506** | **0.159087** | **0.329685** |
| days 18-23 | ItemKNN | 0.247780 | 0.146691 | 0.305245 |
| days 18-23 | BPR | 0.123876 | 0.072287 | 0.158300 |
| days 18-23 | Best popularity baseline | 0.072602 | 0.042709 | 0.095600 |
| days 24-29 | Hybrid | **0.251737** | **0.149104** | **0.310317** |
| days 24-29 | ItemKNN | 0.238066 | 0.140716 | 0.293407 |
| days 24-29 | BPR | 0.120820 | 0.068055 | 0.155035 |
| days 24-29 | Best popularity baseline | 0.068416 | 0.041146 | 0.092417 |
| days 36-42 | Hybrid | **0.223415** | **0.131477** | **0.276308** |
| days 36-42 | ItemKNN | 0.214368 | 0.125840 | 0.265098 |
| days 36-42 | BPR | 0.093284 | 0.054197 | 0.120485 |
| days 36-42 | Best popularity baseline | 0.061952 | 0.037789 | 0.082085 |

The early and middle folds evaluate all 52,605 and 52,874 eligible users,
respectively. Their candidate coverage is 87.12% and 87.99%; final-test coverage is
88.02%. Absolute accuracy declines in later windows, but the model ordering is stable:
Hybrid > ItemKNN > BPR > popularity. The hybrid advantage over ItemKNN narrows from
0.01240 NDCG in the early window to 0.00564 in the final window, while remaining
positive and statistically significant in the held-out final test.

## Feature and candidate ablations already completed

Binary feedback is better aligned with discovery than repeated-interaction counts.
On the held-out test, binary ItemKNN reaches NDCG@10 0.125840 versus 0.116943 for
count-weighted ItemKNN; the paired bootstrap interval above confirms this difference.

The validation grid crosses BPR weight `alpha` in 0/0.25/0.5/0.75/1 with popularity
penalty `lambda` in 0/0.05/0.10/0.20. It selects alpha 0.75 and lambda 0. A nonzero
penalty increases novelty and long-tail exposure but does not improve the selection
metric. The seven-day active-channel proxy raises hybrid NDCG from 0.13148 to 0.13542,
but reduces overall positive candidate coverage to 80.21%; activity is not exact live
status.

## Subgroup behavior

Hybrid NDCG falls from 0.16794 for users with approximately 1-6 previously watched
channels to 0.09012 for users with 25-266. Similarly, recall is 0.03278 for targets in
the least-popular channel quartile and 0.40755 in the most-popular quartile. These
results expose the primary limitation: discovery is hardest for long-history users and
long-tail target channels.

## Data-quality audit

The 3,051,733 official-source rows contain zero missing cells, exact duplicate rows,
stop-before-start rows, zero-duration rows, nonpositive user IDs, or blank channel
names. Cold-start is the material data limitation rather than malformed records:
approximately 12% of final-period novel user-channel positives are outside the fitted
catalog.

## Observed scaling

| Run | Users | Interactions | Channels | End-to-end minutes |
|---|---:|---:|---:|---:|
| Official 100k | 100,000 | 3,051,733 | 162,625 | 28.23 |
| Independent approximately-100k | 99,660 | 3,034,146 | 161,021 | 32.95 |
| One million | 1,000,000 | 30,585,070 | 464,657 | 77.08 |

Times are filesystem birth-to-final-write intervals for the saved run logs, not a
controlled hardware benchmark. The one-million run uses capped validation/test ranking
samples, whereas the 100k runs evaluate all eligible test users, so runtime ratios must
not be interpreted as an algorithmic scaling exponent.

## Reproducibility and artifacts

Run `twitch-recs assignment-analysis --config configs/full.yaml`. Raw outputs are in
`outputs/assignment2/tables/`; presentation-ready figures are in
`outputs/assignment2/figures/`. The bootstrap cluster unit, sample count, backtest day
boundaries, selected model settings, and random seed are recorded in code and config.
