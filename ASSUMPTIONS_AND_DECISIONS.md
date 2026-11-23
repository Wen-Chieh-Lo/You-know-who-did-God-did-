# Assumptions and implementation decisions

This document records choices that were not completely fixed by the experiment plan.

1. **Dataset.** Use `100k_a.csv` from the official UCSD directory. The 6.5 GB
   `full_a.csv.gz` is not the 100k-user subset described in the plan.
2. **Day boundaries.** A day index is `floor((time_start - min(time_start))/144)`.
   These are relative 24-hour blocks, never calendar dates or weekdays.
3. **Whole-day split.** Sort observed day indices and assign the first 70% to train,
   the next 15% to validation, and the remainder to test. Boundaries are saved.
4. **Model fitting.** Tune on a train-fitted model and validation labels. After
   selecting settings, refit on train+validation and evaluate once on test.
5. **New-channel labels.** Within an evaluation period, a user's first interaction
   with each channel absent from that user's fit-period history is a positive. It is
   assigned to the day of that first interaction. Empty-target user-days are omitted.
6. **Candidate set.** The primary candidate catalog is every channel observed in the
   relevant fit period. User-seen channels are excluded. Candidate coverage counts
   all new positives, including positives whose channels are outside this catalog.
7. **Repeated rows.** Models use binary user-channel feedback. Duration and repeated
   interactions are retained for EDA and the optional interaction-weighted analysis.
8. **Hybrid scaling.** Scores are standardized per user over eligible candidates.
   This is one of the two scale-alignment choices explicitly permitted by the plan.
9. **Tie-breaking.** Equal scores are resolved by encoded item ID, making output
   deterministic under the fixed seed.
10. **Computational profiles.** `full.yaml` uses a fixed-seed 5,000-user validation
    sample for tractable grid search, then evaluates every eligible test user.
    `quick.yaml` samples both periods and exists only for smoke tests; it is never
    presented as the final full-population result.
11. **Active-channel experiment.** A seven-day candidate option is implemented as an
    additional analysis only; it is described as recent activity, not proof that a
    streamer was live at recommendation time.
12. **Primary selection metric.** Validation NDCG@10 selects hyperparameters, alpha,
    and popularity penalty. Test results do not influence selection.
13. **Static recommendation unit.** The fitted system produces one list per user at
    the end of the fit period. Whole-period user-level metrics are therefore the
    protocol-aligned primary interpretation; daily-case macro metrics are retained as
    a temporal-target sensitivity analysis.
14. **Cold-start denominators.** Candidate-conditioned metrics are reported alongside
    end-to-end metrics that retain fit-catalog-unseen novel positives as unavoidable
    misses. Candidate coverage and the eligibility funnel make this distinction
    explicit.
15. **Training uncertainty.** User-clustered bootstrap intervals quantify test-user
    sampling uncertainty conditional on fitted models. Five BPR seeds separately
    quantify initialization and negative-sampling variability; seeds are summarized,
    never selected using test performance.

