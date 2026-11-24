# Group 9 Twitch presentation — speaker notes

Deck: `Group_9_Presentation_Twitch.pptx`

The planned narration totals 20 minutes.

## 1. Twitch New-Channel Recommendation

Timing: 0:00–0:30 (30 sec)

Let me start with what we mean by new-channel recommendation. We are not trying to bring a viewer back to a channel they already know; we are trying to predict the next channel they will discover. Here, new means absent from that viewer's history, not newly created, which makes this a natural recommendation problem in a catalog far too large to explore manually.

## 2. Motivation

Timing: 0:30–1:25 (55 sec)

The challenge becomes clear when we look at the data. We have more than 162,000 channels, but an average viewer gives us only about thirty interactions. The curve shows how severe that imbalance is: 45 percent of channels appear once, and 77 percent appear no more than five times. At the same time, the top one percent receives 60 percent of all attention. That makes popularity a strong baseline, because a model should prove it can do more than recommend the obvious head channels. And on a live platform, no view does not necessarily mean dislike—the channel may simply have been offline.

## 3. Research Objective

Timing: 1:25–2:10 (45 sec)

So the research question is straightforward: can past viewing history tell us which unseen channel a viewer will discover next? We answer that in three layers. We compare the ranking quality of several models, we investigate why their performance differs instead of stopping at a leaderboard, and we test whether the same conclusions survive changes in time and dataset scale. Throughout the study, success means predicting a future first-time channel view in a chronological holdout.

## 4. Dataset Overview

Timing: 2:10–3:25 (75 sec)

The full Twitch source is very large—15.5 million users and almost 475 million viewing interactions over forty-three relative days. For the main experiment, we use the official 100,000-user benchmark, which still contains more than three million interactions and 162,625 channels. What matters here is not only the size, but also what the data does not contain. These are viewing sessions, not ratings, so an unrecorded view is not an explicit negative. We also have only identifiers and time fields, with no game, language, or channel category. That means we cannot group channels by class or build a content-based recommender; the models have to learn almost entirely from the interaction structure.

## 5. Experimental Protocol

Timing: 3:25–4:45 (80 sec)

Here is how we make the evaluation behave like a real recommendation decision. We move strictly from past to future: days zero through twenty-nine train the models, and the next six days choose the settings without touching the test set. Once the settings are fixed, we refit on everything through day thirty-five and use days thirty-six through forty-two exactly once. For each user-day, we look only at earlier history, remove channels the viewer already knows, rank the remaining catalog, and ask whether a future first-time view appears in the Top-10. All statistics are built from past data, and because one viewer can contribute several days, the bootstrap resamples entire users rather than pretending those cases are independent.

## 6. Compared Models

Timing: 4:45–6:15 (90 sec)

The model comparison is designed to move from the simplest explanation to more personalized ones. Popularity and recent popularity tell us how far we can get by recommending what everyone already watches. ItemKNN then asks a local question: given the channels this viewer knows, which other channels share the same audience? BPR takes a more global approach by learning latent user and item factors from pairwise preferences. We also compare binary and count-weighted ItemKNN to see whether repeated viewing helps or just reinforces familiar channels. Finally, the hybrid combines standardized ItemKNN and BPR scores, with an optional popularity penalty, so validation can decide whether their different signals are genuinely complementary.

## 7. Model Selection

Timing: 6:15–7:30 (75 sec)

Before looking at the test results, we use validation data to make every modeling choice. ItemKNN performs best with 200 neighbors, which suggests that a fairly broad local co-view neighborhood is useful. For BPR, the selected configuration uses 64 factors, a learning rate of 0.03, and twenty epochs. The curve on the left shows that the hybrid is strongest when ItemKNN carries most of the weight: validation chooses alpha 0.75 and no popularity penalty. There is also an engineering constraint behind this experiment. A dense 162,000-by-162,000 similarity matrix is not practical, so we multiply sparse blocks and retain only the best neighbors for each channel.

## 8. Evaluation and Inference

Timing: 7:30–8:45 (75 sec)

Before reading the results, it helps to separate accuracy from breadth. Recall asks how many future discoveries appear anywhere in the Top-10, while NDCG gives more credit when the correct channel appears near the top, so NDCG is the metric we use to choose models. Hit rate answers a simpler question—did this user-day get at least one useful recommendation? Coverage, novelty, and long-tail exposure tell us whether the system keeps showing the same head channels or spreads attention more broadly. Candidate coverage is also important because some future channels never appeared during fitting and were impossible for any collaborative model to retrieve. For uncertainty, we compare models with user-level bootstrap samples and correct for multiple tests.

## 9. Experiment 1: Model Comparison

Timing: 8:45–10:30 (105 sec)

This first experiment gives us the overall ranking. The hybrid is best, with NDCG 0.13148 and Recall 0.22342, while ItemKNN is the strongest single model at 0.12584 NDCG. The larger message is that every personalized method beats popularity by a wide margin, so the viewer's own history contains real predictive signal. The hybrid improves NDCG by 4.48 percent over ItemKNN, which means BPR is contributing something useful even though it performs poorly alone. But that gain is not free: hybrid coverage falls to 26.36 percent, compared with 36.71 percent for ItemKNN, and count-weighted ItemKNN reaches 40.50 percent coverage despite lower accuracy. So if the objective is pure ranking quality, hybrid wins; if broader creator exposure matters, ItemKNN or a diversity-aware reranker may be the better operating choice.

## 10. Experiment 2: BPR Analysis

Timing: 10:30–12:10 (100 sec)

The surprising result is not simply that BPR loses; it is that BPR still helps the winning hybrid. The long tail is one reason for the weak standalone result, because many channels do not have enough positive examples to learn stable factors. The negatives are noisy as well: a viewer may miss a channel because it was offline or never exposed, not because they disliked it. Uniform negative sampling then gives BPR many easy comparisons, and its pairwise objective is not exactly the same as ranking the full catalog. We checked five random seeds, so this is not just an unlucky run. Still, BPR finds 5,540 positives that ItemKNN misses. That complementary signal lifts the hybrid by 0.005638 NDCG, and the confidence interval remains above zero after correction, so the smaller contribution is statistically credible.

## 11. Experiment 3: Subgroup Analysis

Timing: 12:10–13:40 (90 sec)

We then looked beyond the overall average to understand where the models succeed and fail. Binary ItemKNN beats the count-weighted version, 0.12584 versus 0.11694 NDCG, which makes sense for this task: repeated views tell us about loyalty to channels the viewer already knows, while we are trying to predict a first-time discovery. The much larger gap appears across target popularity. Recall is only 0.0328 for the least-popular quartile, but rises above 0.40 for the most-popular quartile. Performance also declines for viewers with long histories, probably because the easiest neighboring channels have already been consumed and the remaining choices are less obvious. At the extreme, a viewer with no usable history cannot be personalized by these collaborative models at all, so the product still needs a popularity fallback.

## 12. Experiment 4: Temporal Robustness

Timing: 13:40–14:55 (75 sec)

A single test week can always be unusually easy or hard, so we repeated the comparison in early, middle, and late windows. Absolute accuracy does decline: the hybrid moves from 0.1591 NDCG early to 0.1315 late, and the other models show the same direction. What gives us confidence is that the ordering never changes. Hybrid stays first, ItemKNN stays second, BPR stays third, and popularity stays last. That consistency makes the relative conclusion much stronger than a result from one lucky holdout. At the same time, the falling scores are an operational warning: viewer behavior and channel availability drift, so a deployed model would need monitoring and regular retraining rather than assuming one offline score will remain valid.

## 13. Experiment 5: Scalability

Timing: 14:55–16:10 (75 sec)

We also wanted to know whether the story survives when the system grows. Using the same seed and search protocol, we repeated the experiment from 100,000 users up to one million. Hybrid and ItemKNN remain remarkably stable: hybrid stays between 0.1289 and 0.1317 NDCG, and ItemKNN stays in a similarly narrow range. BPR moves in the opposite direction, falling from 0.0558 to roughly 0.043 as the catalog expands. In other words, adding interactions does not automatically solve the problem when it also creates a much larger and sparser item space. These cohorts are not nested, so I would not call this a causal learning curve. What we can say is that the overall conclusion is robust and that the pipeline can support the larger experiment.

## 14. Connection to Prior Work

Timing: 16:10–17:25 (75 sec)

This work is closely related to LiveRec because it uses the same Twitch source, but it is not a direct replication. LiveRec recommends streams that are currently available and treats repeat consumption as an important signal. We deliberately ask a different question by removing channels the viewer already knows and measuring future first-time discovery. LiveRec also models exact availability, while we only have a recent-activity proxy, which is one reason our missing interactions are difficult to interpret. Methodologically, Rendle and colleagues provide the BPR objective we test, and LightGCN is a natural next graph-based extension. Because the targets, candidates, and metrics differ, prior work guides our design, but its numerical results should not be compared directly with ours.

## 15. Limitations and Next Steps

Timing: 17:25–18:45 (80 sec)

The remaining gaps are larger than a single model upgrade. About twelve percent of future positive channels never appear in the fit catalog, so a collaborative ranker has no representation to score. Solving that requires creator, game, language, or text features, but this dataset gives us identifiers and interaction times only. We also do not know exact live status, which means an unobserved pair may reflect unavailability rather than dislike. For BPR, harder or popularity-aware negatives would make training look more like the full-catalog decision. And finally, offline NDCG cannot tell us whether viewers were satisfied or whether exposure was fair to creators. The practical next step is an online test that measures watch time, retention, and exposure, potentially followed by a diversity-aware reranker.

## 16. Conclusions

Timing: 18:45–20:00 (75 sec)

Let me close with the practical takeaway. Personalization clearly matters: the hybrid reaches 0.1315 NDCG, compared with about 0.037 for popularity. ItemKNN is the strongest individual model because local co-view relationships remain useful even when the data is extremely sparse. BPR is much weaker on its own, but it finds some channels ItemKNN misses, and that complementary signal gives the hybrid a statistically credible gain. The trade-off is lower catalog coverage, and simply adding more users does not repair BPR when the item space grows at the same time. So the main lesson is not that the most complex model wins. The better system is the one whose data representation, training objective, and evaluation target all match the discovery problem we actually want to solve.
