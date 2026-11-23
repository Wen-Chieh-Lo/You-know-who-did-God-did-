# Group 9 Twitch presentation — speaker notes

Deck: `Group_9_Presentation_Twitch.pptx`

The planned narration totals 20 minutes.

## 1. Twitch New-Channel Recommendation

Timing: 0:00–0:30 (30 sec)

This project studies new-channel recommendation on Twitch. Rather than predicting repeat viewing, we rank channels that a viewer has never watched before and ask whether those channels are discovered in the future. The main question is which modeling assumptions work under extremely sparse implicit feedback.

## 2. Research Question and Contributions

Timing: 0:30–2:00 (90 sec)

The prediction task is to recommend ten channels that are new to the viewer. The project makes four contributions. First, it uses a chronological, full-catalog evaluation that prevents future leakage. Second, it compares strong simple baselines with personalized neighborhood and latent-factor methods. Third, it studies diversity, cold-start, subgroups, time shifts, and scale rather than reporting one number. Finally, it diagnoses the weak BPR result instead of treating it as an unexplained failure.

## 3. Dataset and Exploratory Analysis

Timing: 2:00–3:30 (90 sec)

The public UCSD Twitch subset contains one hundred thousand users, over one hundred sixty-two thousand channels, and about three million interactions across forty-three relative days. There are no ratings, categories, or text features. The popularity curve spans several orders of magnitude even on log scales, so the catalog is strongly long-tailed. With only about thirty interactions per user, latent representations for tail channels are difficult to estimate. About twelve percent of novel test positives are absent from the fit catalog entirely.

## 4. Prediction Task and Evaluation Protocol

Timing: 3:30–5:00 (90 sec)

The first thirty days fit candidate models, the next six select hyperparameters, and the final seven form the held-out test. After selection, the models are refit through day thirty-five. Each user is ranked against the full fit catalog after removing channels already watched. Every mapping and statistic uses only past data. Because users contribute multiple daily cases, the paired bootstrap resamples users and keeps all cases belonging to each sampled user.

## 5. Models

Timing: 5:00–6:45 (105 sec)

Popularity and recent popularity establish whether personalization is useful. ItemKNN uses cosine similarity between channels based on shared viewers, directly retaining local co-view relationships. BPR learns user and item factors with a pairwise objective. Because the two personalized models make different errors, the hybrid standardizes their candidate score distributions per user and combines them. A popularity penalty was also evaluated as a diversity control.

## 6. Implementation and Hyperparameter Selection

Timing: 6:45–8:05 (80 sec)

ItemKNN is computed with sparse block multiplication and only the top two hundred neighbors per channel are retained, so the dense item-item matrix is never created. Validation compares three neighborhood sizes, eight BPR configurations, and twenty hybrid settings. The selected hybrid uses alpha point seven five and no popularity penalty. The sharp drop at alpha one is BPR alone, illustrating that BPR is much weaker than the mixed model. Test performance is not used for any of these choices.

## 7. Evaluation Metrics

Timing: 8:05–9:25 (80 sec)

Recall measures how many future discoveries are recovered. NDCG additionally rewards placing correct channels earlier and is the primary validation metric. Hit rate asks whether a case has at least one success. Coverage asks how much of the catalog is ever shown, which is not the same as correctness. Novelty and long-tail exposure measure concentration, while candidate coverage identifies answers that no collaborative model could retrieve because the channel was absent during fitting.

## 8. Main Test Results

Timing: 9:25–11:25 (120 sec)

Hybrid is the most accurate model with NDCG point one three one five and recall point two two three four. ItemKNN is the strongest single model. All personalized methods beat popularity, establishing that viewer history contains predictive signal. The hybrid gain over ItemKNN is four point four eight percent in NDCG, but coverage falls from about thirty-seven to twenty-six percent. Count-weighted ItemKNN is less accurate yet exposes the largest share of the catalog. Thus the hybrid is best for ranking accuracy, but not for every diversity objective.

## 9. Why BPR Underperforms—and Still Helps

Timing: 11:25–13:25 (120 sec)

BPR is disadvantaged by the long tail because many item factors receive little data. A missing interaction is also a noisy negative on a live platform, and one uniformly sampled negative per positive is typically trivial. Finally, random pairwise training does not exactly match unseen-channel top-ten ranking. Five independent seeds remain far below ItemKNN, so this is not an unlucky initialization. Nevertheless, BPR uniquely retrieves more than five thousand positives. That complementary signal yields a modest hybrid gain whose user-clustered confidence interval excludes zero after correction.

## 10. Feature Ablation and Subgroup Behavior

Timing: 13:25–15:10 (105 sec)

Binary ItemKNN outperforms count weighting for new-channel discovery, indicating that the set of distinct channels matters more than repeatedly amplifying familiar channels. The subgroup analysis reveals a larger limitation. Recall is only about point zero three three for targets in the least-popular quartile, compared with over point four for the most-popular quartile. NDCG also declines as viewer history grows, likely because easy similar channels have already been consumed. Zero-history viewers require a popularity fallback.

## 11. Temporal Robustness and Scalability

Timing: 15:10–16:40 (90 sec)

Rolling-origin evaluation shows that absolute performance declines in later windows, but the ordering remains Hybrid, ItemKNN, BPR, then popularity. Matched-protocol scale runs at one hundred thousand, two hundred thousand, five hundred thousand, and one million users also preserve the ordering. Hybrid and ItemKNN remain stable, whereas BPR declines as the item catalog expands. Because cohorts and catalogs are not nested, these results establish engineering scalability and robustness, not a causal learning curve for training size.

## 12. Relation to Prior Work

Timing: 16:40–17:55 (75 sec)

LiveRec uses the same underlying Twitch data, but its target is currently available live content and repeat behavior. This project isolates discovery of never-watched channels and only has a seven-day activity proxy, so numerical results should not be compared directly. The key lesson borrowed from LiveRec is that exact availability matters. BPR provides the pairwise ranking foundation, while LightGCN is a relevant graph extension for future work.

## 13. Limitations and Future Work

Timing: 17:55–19:10 (75 sec)

The main limitations are not only model capacity. Catalog-cold channels cannot be ranked without content or creator features. Missing exact live status makes negative feedback noisy. Uniform BPR negatives are usually easy and should be replaced with hard or popularity-aware sampling. Offline NDCG cannot establish viewer satisfaction or creator impact, so an online test should measure watch time, retention, and exposure. Finally, the accuracy-diversity tradeoff motivates a two-stage reranker rather than optimizing only NDCG.

## 14. Conclusions

Timing: 19:10–20:00 (50 sec)

Personalization strongly outperforms popularity. ItemKNN is the strongest individual model because local co-view structure matches this sparse discovery task. The hybrid produces a statistically supported accuracy gain, but reduces catalog coverage, so it is not universally best. Scaling adds interactions but also expands the long tail, and BPR does not improve automatically. The central conclusion is that recommendation quality depends on aligning the data, prediction target, and training objective. Thank you.
