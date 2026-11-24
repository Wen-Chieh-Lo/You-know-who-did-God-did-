# Group 9 Twitch presentation — speaker notes

Deck: `Group_9_Presentation_Twitch.pptx`

The planned narration totals 20 minutes.

## 1. Twitch New-Channel Recommendation

Timing: 0:00–0:30 (30 sec)

This project differs from repeat-view recommendation: we rank channels that are new to each viewer and evaluate whether they receive a future first-time view.
Here, new means absent from that viewer's observed history—not newly created—and recommendation is a natural fit for personalized discovery in a catalog too large to explore manually.

## 2. Motivation

Timing: 0:30–1:25 (55 sec)

Twitch is a difficult discovery setting: the benchmark contains more than 162,000 channels, while an average viewer contributes only about thirty interactions.
The curve shows extreme item sparsity: 45 percent of channels appear once, 60 percent at most twice, and 77 percent at most five times.
Attention is also concentrated, with the top one percent receiving 60 percent of interactions, so global popularity is a strong baseline that personalization must beat.
Finally, a missing view is ambiguous because a channel may have been offline, making unseen-channel discovery harder than ordinary supervised classification.

## 3. Research Objective

Timing: 1:25–2:10 (45 sec)

Our central question is whether past implicit viewing history can predict which unseen Twitch channels a viewer will discover next.
We first compare ranking quality, then explain method differences through BPR diagnostics, feature ablations, and user and channel subgroup analysis.
Finally, we test robustness across time and user scale, always using future first-time channel views in a chronological holdout as the prediction target.

## 4. Dataset Overview

Timing: 2:10–3:25 (75 sec)

The complete Twitch source contains 15.5 million users, 474.7 million viewing interactions, and about 790,000 channel identifiers across forty-three relative days.
Our primary experiment uses the official 100,000-user benchmark, with 3.05 million interactions and 162,625 channels over the same time span.
The observations are viewing sessions rather than ratings, so a recorded view is positive implicit feedback and an unrecorded view is not an explicit dislike.
Only user, stream, channel, start, and stop fields are available; there are no channel class or category labels for grouping items or building content features.
Consequently, the models must learn from interaction structure, while the later scalability experiment uses separate cohorts drawn from the complete source.

## 5. Experimental Protocol

Timing: 3:25–4:45 (80 sec)

Read the protocol from past to future: days 0–29 train candidate models, and days 30–35 choose settings without looking at the held-out test.
After validation, we refit the selected model on all observations through day 35, then evaluate exactly once on days 36–42.
For each user-day case, we use earlier history, remove already-watched channels, rank the remaining fit catalog, and check whether a future first-time view enters the Top-10.
Every mapping, popularity statistic, similarity, and embedding uses past data only, preventing future information from leaking into training or candidate generation.
The test covers 53,212 users and 104,818 cases; because users contribute multiple days, uncertainty is estimated with 10,000 bootstrap draws that resample whole users.

## 6. Compared Models

Timing: 4:45–6:15 (90 sec)

Popularity and recent popularity are non-personalized baselines: they test whether user history adds value beyond recommending channels that are globally or recently popular.
ItemKNN represents each watched channel by its co-viewers and recommends neighboring channels with high cosine similarity, preserving local co-view structure.
BPR instead learns latent user and item factors by training observed channels to score above sampled unobserved channels.
Count-weighted ItemKNN tests whether repeated views carry useful extra signal, while binary ItemKNN treats one view and many views identically.
The hybrid standardizes BPR and ItemKNN scores for each user before combining them, so neither score scale automatically dominates.
A popularity penalty is also searched as a diversity control, allowing validation to decide whether less popular candidates should receive an explicit boost.

## 7. Model Selection

Timing: 6:15–7:30 (75 sec)

All settings are chosen on validation data before the final test, so the reported test results do not select their own hyperparameters.
For ItemKNN, validation compares 50, 100, and 200 neighbors and selects 200, retaining more useful local co-view connections.
For BPR, the search covers factor dimension, regularization, and training epochs; the selected run uses 64 factors, learning rate 0.03, and twenty epochs.
The hybrid search selects alpha 0.75 and no popularity penalty, meaning ItemKNN receives most of the weight while BPR contributes a smaller complementary signal.
Sparse block multiplication and top-neighbor pruning avoid constructing the dense 162,000-by-162,000 similarity matrix, making the experiment computationally feasible.

## 8. Evaluation and Inference

Timing: 7:30–8:45 (75 sec)

Recall at ten asks what fraction of future first-time views appear anywhere in the recommendation list, without distinguishing rank one from rank ten.
NDCG at ten gives more credit when a correct channel appears near the top, so it is our primary model-selection metric.
Hit rate asks whether a user-day has at least one success, while catalog coverage measures how broadly the system distributes exposure across available channels.
Novelty and long-tail exposure diagnose concentration, and candidate coverage separates ranking errors from channels that were absent from the fit catalog and therefore impossible to retrieve.
For paired model comparisons, we bootstrap whole users and apply Holm correction, preserving within-user dependence while controlling multiple statistical tests.

## 9. Experiment 1: Model Comparison

Timing: 8:45–10:30 (105 sec)

Experiment one asks which model best ranks unseen channels and whether higher ranking accuracy changes how broadly the system exposes the catalog.
Hybrid ranks first with NDCG 0.13148 and Recall 0.22342, while ItemKNN is the strongest individual model with NDCG 0.12584.
BPR is far lower at 0.05420 NDCG, and recent popularity reaches only 0.03779, so personalization clearly adds predictive value beyond the strong head-item baseline.
The hybrid improves NDCG by 4.48 percent over ItemKNN, showing that BPR contributes some useful information even though it is weak by itself.
However, hybrid catalog coverage is 26.36 percent compared with 36.71 percent for ItemKNN, so the accuracy gain comes with more concentrated exposure.
Count-weighted ItemKNN is less accurate than binary ItemKNN but reaches the highest coverage, 40.50 percent, which reinforces this accuracy–breadth trade-off.
Therefore, hybrid is the best choice for ranking accuracy, while ItemKNN or a reranking stage may be better when creator-side exposure is also a primary objective.

## 10. Experiment 2: BPR Analysis

Timing: 10:30–12:10 (100 sec)

Experiment two asks why BPR underperforms ItemKNN and whether its different errors still make it useful in the hybrid.
The long tail gives many channels too few positive observations to estimate stable item factors, whereas ItemKNN can preserve a useful local co-view relation directly.
Unobserved pairs are also noisy negatives on Twitch: a viewer may not watch a channel simply because it was offline, unavailable, or never exposed.
With one uniformly sampled negative per positive, many comparisons are too easy, and the pairwise training objective does not exactly match full-catalog Top-10 ranking.
Five independent random seeds remain far below ItemKNN, so the gap is unlikely to be explained by a single unlucky initialization.
Even so, BPR uniquely retrieves 5,540 positives that ItemKNN misses, while ItemKNN uniquely retrieves 22,559, demonstrating complementary error patterns.
Combining those signals produces a 0.005638 NDCG gain, with a user-clustered confidence interval above zero after Holm correction.

## 11. Experiment 3: Subgroup Analysis

Timing: 12:10–13:40 (90 sec)

Experiment three asks whether repeated-view counts improve the representation and which user or channel subgroups remain hardest.
Binary ItemKNN reaches NDCG 0.12584, compared with 0.11694 for count weighting, so distinct channel history is more useful than repeatedly amplifying familiar channels.
This fits the discovery target: repeated views describe loyalty to known channels, while our outcome is a first-time view of something unseen.
Target popularity has the largest effect: recall is only 0.0328 in the least-popular quartile but exceeds 0.40 for the most-popular quartile.
NDCG also falls as viewer history grows, likely because easy neighboring channels have already been consumed and the remaining candidates are less obvious.
For viewers with no usable history, collaborative models cannot personalize at all, so a popularity or recent-popularity fallback remains necessary.

## 12. Experiment 4: Temporal Robustness

Timing: 13:40–14:55 (75 sec)

Experiment four tests whether our main conclusion depends on one favorable test period by repeating the comparison in early, middle, and late rolling-origin windows.
Hybrid NDCG declines from 0.1591 in the early window to 0.1315 in the late window, and every other model also loses absolute accuracy.
Despite that drift, every window preserves the same ordering: Hybrid first, ItemKNN second, BPR third, and popularity last.
The stable ordering makes the relative model conclusion more credible than a result from one held-out week alone.
At the same time, the declining values warn that offline accuracy is time-dependent, so a deployed system would need monitoring and periodic retraining.

## 13. Experiment 5: Scalability

Timing: 14:55–16:10 (75 sec)

Experiment five asks whether the conclusions survive larger cohorts, using 100,000, 200,000, 500,000, and one million users under the same seed and search protocol.
Hybrid NDCG stays between 0.1289 and 0.1317, while ItemKNN remains between 0.1261 and 0.1304, showing stable ranking quality at larger scale.
BPR instead falls from 0.0558 to about 0.043 as the channel catalog expands, suggesting that additional rows do not compensate for a much larger and sparser item space.
All runs use full-catalog ranking with validation capped at 2,000 users and testing capped at 5,000 users, which keeps the evaluation protocol comparable.
Because the cohorts and catalogs are not nested, this is evidence of robustness and engineering scalability, not a causal learning curve for the effect of training size.

## 14. Connection to Prior Work

Timing: 16:10–17:25 (75 sec)

LiveRec uses the same underlying Twitch source, but it recommends currently available streams and treats repeat consumption as an important signal.
Our target is different: we exclude channels already watched and evaluate future first-time discovery, so the two studies answer different recommendation questions.
LiveRec models exact availability, whereas our data supports only a recent-activity proxy; this limitation helps explain why missing interactions are noisy negatives.
Rendle and colleagues provide the pairwise BPR objective used here, while LightGCN represents a natural graph collaborative-filtering extension for future experiments.
Because tasks, candidate sets, and evaluation metrics differ, we use prior work to motivate design choices rather than making direct numerical performance claims.

## 15. Limitations and Next Steps

Timing: 17:25–18:45 (80 sec)

The first limitation is candidate cold-start: about twelve percent of future positive channels are absent from the fit catalog, so no collaborative ranker can retrieve them.
Adding creator, language, game, or textual metadata could generate candidates for those channels, but this dataset provides only identifiers and interaction times.
Second, exact live status is unknown, so an unobserved pair may represent unavailability rather than dislike; timestamped availability masks would create cleaner negatives.
Third, uniform BPR negatives are often easy, motivating popularity-aware or hard-negative sampling that more closely matches full-catalog ranking.
Finally, offline NDCG does not measure satisfaction or creator impact; an online test should track watch time, retention, and exposure, potentially with a diversity-aware reranker.

## 16. Conclusions

Timing: 18:45–20:00 (75 sec)

First, personalization is valuable: Hybrid reaches NDCG 0.1315, compared with roughly 0.037 for global or recent popularity.
Second, ItemKNN is the strongest individual model because local co-view relationships remain reliable under extreme sparsity, while the current BPR factors do not.
Third, BPR still contributes complementary hits, so the hybrid produces a statistically supported accuracy gain over ItemKNN alone.
That gain is not universal: hybrid catalog coverage is lower, and increasing data scale does not automatically repair BPR as the item space also grows.
The main lesson is that recommendation quality depends on aligning the data, the new-channel target, and the learning objective rather than simply choosing a more complex model.
