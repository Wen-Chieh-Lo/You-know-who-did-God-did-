# Twitch New-Channel Recommendation

## Recording transcript

> **Speakers:** Wen-Chieh Lo, Cheng-Yi Chen, and Cheng-Yan Juang  
> **Course:** CSE 258 · Fall 2026  
> **Planned duration:** 20 minutes  
> **Transcript length:** 3,714 words

## Slide guide

| Slide | Topic | Planned timing |
| ---: | --- | --- |
| 1 | Twitch New-Channel Recommendation | 0:00–0:38 (38 sec) |
| 2 | Motivation | 0:38–1:41 (63 sec) |
| 3 | Research Objective | 1:41–2:26 (45 sec) |
| 4 | Dataset Overview | 2:26–3:26 (60 sec) |
| 5 | Experimental Protocol | 3:26–4:37 (71 sec) |
| 6 | Compared Models | 4:37–5:50 (73 sec) |
| 7 | Model Selection | 5:50–6:56 (66 sec) |
| 8 | Evaluation and Inference | 6:56–8:04 (68 sec) |
| 9 | Experiment 1: Model Comparison | 8:04–9:25 (81 sec) |
| 10 | Experiment 2: BPR Analysis | 9:25–11:06 (101 sec) |
| 11 | Experiment 3: Subgroup Analysis | 11:06–12:42 (96 sec) |
| 12 | Experiment 4: Temporal Robustness | 12:42–13:52 (70 sec) |
| 13 | Experiment 5: Scalability | 13:52–15:26 (94 sec) |
| 14 | Connection to Prior Work | 15:26–16:49 (83 sec) |
| 15 | Limitations and Next Steps | 16:49–18:22 (93 sec) |
| 16 | Conclusions | 18:22–20:00 (98 sec) |

---

## Slide 1 — Twitch New-Channel Recommendation

**Planned timing:** 0:00–0:38 (38 sec)

Hi we would like to present our final prrject. Twitch New Channel recommendation. I am Wen-Chieh Lo together wuith my teammate Cheng-Yi Chen Cheng-Yan Juang. Most recommendation systems are happy when a viewer returns to something familiar, but our target is discovery: we want to predict the next channel that viewer will watch for the first time. A new channel is therefore user-specific. It does not have to be newly created; it simply has not appeared anywhere in that viewer's observed history. This is a natural recommendation problem because the Twitch catalog is far too large for anyone to explore manually. Our job is to narrow that catalog to ten relevant unseen choices. To understand why that is difficult, the next slide looks at how uneven the available interaction evidence really is.

---

## Slide 2 — Motivation

**Planned timing:** 0:38–1:41 (63 sec)

The first thing to notice is the mismatch between catalog size and behavioral evidence. The benchmark contains more than 162,000 channels, while an average viewer contributes only about thirty interactions. The chart is an empirical cumulative distribution: moving from left to right, it tells us what share of channels have no more than a given number of observations. At one interaction, we already cover 45 percent of the catalog. At two interactions, that rises to 60 percent, and by five interactions it reaches 77 percent. So for most channels, the model has almost no evidence from which to learn. Attention is concentrated at the other end as well: the top one percent of channels receives 60 percent of all interactions. That is why popularity is not a trivial baseline; it is a strong description of what viewers already do, and personalization has to beat it. There is one more complication. Twitch is a live platform, so a missing view may mean the viewer was not interested, but it may also mean the channel was offline or never exposed. With that motivation in place, the next slide turns these data constraints into a precise research question.

---

## Slide 3 — Research Objective

**Planned timing:** 1:41–2:26 (45 sec)

Given those constraints, our central question is simple to state: can past viewing history predict which unseen Twitch channel a viewer will discover next? We organize the answer around three objectives. The first is ranking quality. We compare a strong popularity baseline with ItemKNN, BPR, and a hybrid, all producing a Top-10 list from channels the viewer has never watched. The second is explanation. A leaderboard alone is not enough, so we study why the methods differ, which signals help, and which users or channels remain difficult. The third is robustness. We repeat the comparison across time and from 100,000 to one million users. Across every experiment, the outcome is the same: a future first-time channel view in a chronological holdout. Before describing the protocol, the next slide clarifies exactly what information the dataset does—and does not—give us.

---

## Slide 4 — Dataset Overview

**Planned timing:** 2:26–3:26 (60 sec)

The complete Twitch source is genuinely large: 15.5 million users, almost 475 million viewing interactions, and roughly 790,000 channel identifiers over forty-three relative days. Our main model comparison uses the official 100,000-user benchmark, which still contains 3.05 million interactions and 162,625 channels. The larger source returns later when we test scalability. The more important point is what each row means. These are viewing sessions, not ratings. A recorded view is positive implicit feedback, but an absent row is not a statement that the viewer disliked the channel. It may simply reflect no exposure or no live availability. The five fields are an anonymous user, a stream identifier, a channel identifier, and start and stop slots. We do not have game class, language, creator profile, text, or any other semantic category. That means we cannot group channels by class or ask a content-based model to generalize to a new item. The system must learn almost entirely from who watched what and when. Because temporal order is the strongest structure we do have, the next slide shows how we use it to create a realistic and leakage-safe experiment.

---

## Slide 5 — Experimental Protocol

**Planned timing:** 3:26–4:37 (71 sec)

This protocol is designed to make the offline experiment resemble a real recommendation decision. Read the top row from left to right. Days zero through twenty-nine train the candidate models. Days thirty through thirty-five are validation: we choose neighborhood size, factor settings, and hybrid weights there, without looking at the final answer. Once those choices are frozen, we refit the selected model on all data through day thirty-five. Days thirty-six through forty-two are then used exactly once as the simulated future. The second row shows what happens for one test case. We take the viewer's history available before that target day, remove every channel they have already watched, score the remaining channels that appeared in the fit period, and keep the Top-10. A hit occurs when a channel viewed for the first time in the future appears in that list. The filtering step is important because otherwise a model could look good by recommending familiar favorites, which is not our research target. Every mapping, popularity count, similarity, and embedding is built from past data only. The held-out test contains 53,212 users and 104,818 user-day cases. Since the same viewer can contribute several cases, we estimate uncertainty by resampling whole users in 10,000 bootstrap draws. With that evaluation contract fixed, we can now compare models without changing the definition of success.

---

## Slide 6 — Compared Models

**Planned timing:** 4:37–5:50 (73 sec)

The comparison moves from the simplest explanation of behavior to increasingly personalized ones. Popularity recommends the channels with the most distinct viewers, and recent popularity repeats that idea using only the latest seven fit days. These baselines tell us whether a complex model is adding value or merely rediscovering the global head of the catalog. ItemKNN is the first personalized model. For every channel a viewer has watched, it looks for other channels with overlapping audiences, using cosine similarity between binary user sets. The intuition is local and easy to explain: people who watched these channels also tended to watch those channels. We also build a count-weighted version to test whether repeated viewing should make a known channel more influential. For a discovery task, that is not obviously helpful, because repeat behavior describes loyalty rather than novelty. BPR takes a different view. It learns latent user and channel factors and trains an observed channel to score above a sampled unobserved channel. In principle, that can capture global structure beyond immediate neighbors. Finally, the hybrid standardizes the BPR and ItemKNN scores separately for each user, combines them with weight alpha, and can subtract a popularity penalty. This design lets validation decide whether the two personalized models make useful different errors. The next question is how we choose those settings without letting the test set influence the answer.

---

## Slide 7 — Model Selection

**Planned timing:** 5:50–6:56 (66 sec)

Every setting on this slide is selected using validation data before we inspect the final test. For ItemKNN, we compare 50, 100, and 200 retained neighbors, and validation chooses 200. That suggests useful co-view evidence is spread across a reasonably broad local neighborhood rather than only a few nearly identical channels. For BPR, the grid varies factor dimension, regularization, and training duration. The selected configuration uses 64 factors, learning rate 0.03, regularization 0.0025, and twenty epochs. The chart on the left is especially informative because alpha moves from ItemKNN alone at zero toward BPR alone at one. Performance stays high while ItemKNN dominates and then drops sharply near pure BPR. The best validation setting is alpha 0.75 with no popularity penalty, so BPR receives meaningful but secondary weight. In other words, validation expects complementarity, not replacement. There is also a practical engineering issue. A dense similarity matrix for more than 162,000 channels would contain tens of billions of entries. We avoid creating it by multiplying sparse blocks and keeping only the top 200 neighbors per item. The seed, search grid, and selected configuration are recorded so the experiment can be reproduced. With the models fixed, the next slide explains exactly how we judge them.

---

## Slide 8 — Evaluation and Inference

**Planned timing:** 6:56–8:04 (68 sec)

Before looking at the leaderboard, we need to separate several meanings of better. Recall at ten asks what fraction of the viewer's future first-time channels appears anywhere in the Top-10. If two relevant channels exist and we retrieve one, recall is one half. NDCG adds position: a correct answer at rank one earns more credit than the same answer at rank ten. Because recommendation lists are ordered, NDCG at ten is our primary validation metric. Hit rate is easier to interpret at the case level: did this user-day receive at least one successful suggestion? Coverage asks a different question—what fraction of the fit catalog is ever exposed across all recommendations? A model can have strong NDCG and poor coverage if it repeatedly relies on the same safe channels. Novelty and long-tail exposure give two more views of that concentration. Candidate coverage prevents us from blaming the ranker for an impossible answer. If a future positive channel never appeared in the fit catalog, no collaborative model could score it. Finally, all model comparisons are paired on the same cases. We bootstrap whole users, not individual days, and use Holm correction across tests. Now that we know how to read both accuracy and breadth, we can turn to the main result.

---

## Slide 9 — Experiment 1: Model Comparison

**Planned timing:** 8:04–9:25 (81 sec)

This first experiment asks the most direct question in the project: when every model receives the same history and ranks the same unseen catalog, which one places future discoveries closest to the top? The hybrid finishes first with NDCG 0.13148 and Recall 0.22342. ItemKNN is the strongest individual model at 0.12584 NDCG, while BPR reaches only 0.05420 and recent popularity reaches 0.03779. Because the head of this catalog attracts so much attention, beating popularity by this margin is meaningful: it tells us that a viewer's own history contains information that cannot be recovered from aggregate traffic alone. The hybrid improves NDCG by 4.48 percent over ItemKNN, and later we test whether that difference is reliable. BPR is weak as a complete recommender, yet some part of its latent representation must be correcting mistakes made by the neighborhood model. Otherwise adding it could not improve the ranking. Accuracy, however, is only one side of the result. The hybrid exposes 26.36 percent of the catalog, versus 36.71 percent for binary ItemKNN. Count-weighted ItemKNN reaches 40.50 percent coverage, even though its NDCG falls to 0.11694. If our sole objective is putting the most likely discovery near the top, the hybrid is the best choice. If we also care about giving a broader set of creators an opportunity to be seen, ItemKNN or a second-stage diversity rule may be preferable. The most interesting question is why a model that performs poorly alone can still improve the winner. That is the focus of the next experiment.

---

## Slide 10 — Experiment 2: BPR Analysis

**Planned timing:** 9:25–11:06 (101 sec)

The surprising result is not simply that BPR loses to ItemKNN. The more useful question is why it loses, and why it still helps the winning hybrid. BPR learns one vector for every user and every channel. That works best when each vector receives enough evidence. Here, most channels sit in the extreme long tail, so many item factors are updated from only a handful of positive observations. A local co-view method can reuse concrete audience overlap, while a latent model estimates dozens of parameters from the same scarce evidence. The definition of a negative is another mismatch. BPR samples an unobserved channel and trains the observed one to rank above it. On Twitch, unobserved does not necessarily mean disliked. The channel may have been offline, the viewer may never have encountered it, or it may not have been available in the viewer's time zone. Uniform sampling also selects irrelevant tail items, creating easy comparisons that do not resemble the difficult decision among plausible Top-10 candidates. Finally, BPR optimizes a sampled pairwise objective, whereas evaluation ranks the full catalog. More users therefore do not automatically fix the objective. Five random seeds show the poor result is not one unlucky initialization. The overlap counts explain why we did not discard BPR. ItemKNN alone finds 22,559 successful cases, both models find 7,648, and BPR uniquely finds another 5,540 that ItemKNN misses. Those unique hits are relatively few, but they contain complementary information. Adding BPR raises NDCG by 0.005638 over ItemKNN. The 95 percent confidence interval, from 0.005201 to 0.006088, stays entirely above zero, and the Holm-adjusted p-value is 0.0024. The interpretation is not that BPR is generally better; it is that BPR makes different errors, and a carefully weighted version improves the local model. That leads naturally to the next question: do these conclusions hold equally for every kind of viewer and channel?

---

## Slide 11 — Experiment 3: Subgroup Analysis

**Planned timing:** 11:06–12:42 (96 sec)

An overall average can hide the fact that a method works well for one person and poorly for another, so this experiment separates the result by representation, target popularity, and user history. We begin with the left chart. Binary ItemKNN treats a channel as either present or absent in the viewer's history. The count version gives additional weight to channels watched repeatedly. Binary performs better, with NDCG 0.12584 compared with 0.11694. For a discovery task, that result is intuitive. Repetition is a strong sign of loyalty to something the viewer already knows, but it can make the profile narrower and dominate the signal from less frequent interests. A set of distinct watched channels gives a cleaner description of which communities the viewer has explored. The larger inequality appears on the channel side. Recall is 0.0328 for targets in the least-popular quartile, then rises steadily and exceeds 0.40 for the most-popular quartile. Tail channels have fewer co-view links for ItemKNN and fewer positive updates for BPR, so both models have much less evidence exactly where discovery could be most valuable. The models are not uniformly good or bad; quality depends on how much evidence exists for the future target. User history creates a second pattern. People with a small but nonzero set of distinct channels often give ItemKNN a focused neighborhood from which to expand. As history becomes very long and varied, the profile mixes several interests, and easy neighboring channels have already been removed by the unseen-item filter. At the extreme, a viewer with zero usable history cannot receive collaborative personalization at all. The responsible behavior is then a fallback such as recent popularity, context, or an onboarding signal. Having identified these subgroup effects, we next ask whether the model ordering remains stable when the target period changes.

---

## Slide 12 — Experiment 4: Temporal Robustness

**Planned timing:** 12:42–13:52 (70 sec)

Time can change the available evidence, so one final week might be unusually easy or difficult. To test this, we repeat the entire comparison with rolling origins. In each window, training remains in the past and the target remains in the future; we move the boundary rather than allowing future information to enter the model. The absolute values do change. Hybrid NDCG falls from 0.1591 in the early window to 0.1491 in the middle and 0.1315 in the late window. ItemKNN, BPR, and popularity decline in the same direction. That may reflect changes in active channels, audience behavior, or harder discoveries. The important robustness result is that the ordering never changes. Hybrid remains first, ItemKNN second, BPR third, and popularity last in every window. This makes the relative conclusion much stronger than a result from one holdout. At the same time, stable ordering should not be confused with stable product performance. A deployment team would still need to monitor the absolute NDCG, candidate coverage, and the distribution of active channels. Retraining should be triggered when those quantities drift. Time supports the comparison while also warning us that no single offline score is permanent. The next experiment changes a different dimension: instead of moving the time window, we increase the system from 100,000 users to one million.

---

## Slide 13 — Experiment 5: Scalability

**Planned timing:** 13:52–15:26 (94 sec)

Scalability has two meanings in this experiment. The first is computational: can the same pipeline train and rank a much larger cohort? The second is statistical: when more interactions arrive, do the conclusions remain stable? We repeat the comparison at 100,000, 200,000, 500,000, and one million users. Every run uses seed 258, the same validation limit of 2,000 users, the same test limit of 5,000 users, the same hyperparameter search, and full-catalog ranking. Keeping those choices matched prevents a larger cohort from receiving an easier protocol. Hybrid and ItemKNN are remarkably stable. Hybrid stays between 0.1289 and 0.1317 NDCG, while ItemKNN remains between 0.1261 and 0.1304. This suggests that the local co-view structure used by ItemKNN is already estimated reasonably well at the smaller scale. BPR behaves differently. It begins at 0.0558 for 100,000 users and falls to about 0.042 or 0.043 at the two largest scales. More user interactions arrive, but the channel catalog expands at the same time, creating more sparse factors and a harder negative-sampling space. Scale amplifies the mismatch seen earlier. There is an important limitation to the claim. These cohorts are independently constructed rather than nested subsets of the same population, so catalog composition and user mix can change with training size. This is evidence of robustness and engineering scalability, not a causal learning curve. A strict data-size experiment would hold the test users and catalog fixed while adding nested training data. What we can conclude is that the ranking Hybrid above ItemKNN, BPR, and popularity survives at one million users, and that more data alone does not repair a poorly matched learning objective. To place that contribution in context, the next slide compares our target with the closest prior work on the same Twitch source.

---

## Slide 14 — Connection to Prior Work

**Planned timing:** 15:26–16:49 (83 sec)

The closest prior work is LiveRec by Rappaz, McAuley, and Aberer, because it introduced and studied this Twitch source. Sharing a dataset does not mean sharing a prediction task. LiveRec recommends streams that are currently available and treats repeat viewing as a central behavioral signal. Our study removes every previously watched channel and asks which unfamiliar channel the viewer will discover next. That change affects the labels, candidates, features, and metrics. A method that is excellent at returning viewers to a favorite creator may receive no credit in our experiment. Availability is another key distinction. LiveRec can reason about what is live at recommendation time. Our benchmark lacks a complete availability mask, so we use recent activity as a proxy. This makes missing views ambiguous and negative sampling difficult. We should not compare our NDCG directly with LiveRec's values, because the model answers a different question over a different catalog. On the methodological side, Rendle and colleagues introduced Bayesian Personalized Ranking, the pairwise objective used in our latent model. Our result adds a useful boundary condition: an objective designed for implicit ranking can struggle when items are sparse and non-observation reflects live availability. LightGCN is a natural next extension because it propagates information through the user-item graph without heavy transformations, although it still inherits the candidate and negative definitions. Prior work gives us both a foundation and a warning: a more advanced architecture does not remove a mismatch between data and task. That point becomes clearer when we state the limitations of the current study directly.

---

## Slide 15 — Limitations and Next Steps

**Planned timing:** 16:49–18:22 (93 sec)

The limitations show why improvement should begin with the system definition rather than adding another model. First, about twelve percent of future positive channels never appear in the fit catalog. For those cases, ItemKNN has no neighbors and BPR has no learned item vector, so the correct channel is impossible to rank. This is catalog cold-start, not a ranking failure. A content-aware candidate generator could use creator identity, game category, language, title text, or other metadata, but the current dataset supplies only identifiers and interaction times. We therefore cannot perform that experiment here. Second, exact live status is unknown. Treating every unobserved user-channel pair as a possible negative mixes together dislike, lack of exposure, and simple unavailability. The cleanest next dataset would include a timestamped availability mask, so training compares only channels the viewer could watch. BPR could also use popularity-aware or hard negatives drawn from active, plausible channels. That would create more informative comparisons than uniform sampling, although it would not fully eliminate exposure bias. Third, our best model reduces catalog coverage. That is not automatically wrong, but the choice depends on the platform objective. A two-stage system could first retrieve accurate candidates with the hybrid and then rerank them under an explicit diversity or creator-exposure constraint. We would report the accuracy cost of additional coverage rather than hiding the trade-off in one score. Finally, all evidence is offline. NDCG cannot tell us whether a recommendation creates satisfying watch time, improves retention, or distributes opportunity fairly. The decisive follow-up is an online A/B test that measures viewer response and creator exposure together. These limitations qualify the result, but they do not erase the consistent pattern we observed. The final slide summarizes what that pattern teaches us.

---

## Slide 16 — Conclusions

**Planned timing:** 18:22–20:00 (98 sec)

Let me close by returning to the question from the beginning: can a viewer's past behavior identify a channel they have never watched before? In this dataset, the answer is yes. The hybrid reaches about 0.1315 NDCG, compared with roughly 0.037 for global popularity. That gap is large enough to show that personalization is not merely reproducing the most visible part of Twitch. Even under highly sparse implicit feedback, the pattern of channels a person has explored contains useful information about what they may discover next. Among the individual models, ItemKNN fits the observed structure best. It can turn local audience overlap into a recommendation without estimating a high-dimensional representation for every rare channel. BPR is much weaker alone because sparse item factors, ambiguous negatives, and uniform sampling do not align well with full-catalog discovery. Yet BPR is not useless. It produces a smaller set of unique hits that ItemKNN misses, and after validation assigns it the right weight, that complementary signal gives the hybrid a statistically credible improvement. The winning score comes with two cautions. Hybrid coverage is lower than ItemKNN coverage, so improving viewer accuracy may concentrate creator exposure. And when we increase the cohort to one million users, BPR does not recover, because the channel space becomes larger and sparser at the same time. More data is useful only when it provides needed evidence; volume cannot compensate for missing availability, cold items, or a mismatched learning objective. The broader lesson is not that the most complex algorithm wins. A reliable system begins by defining the behavior we truly want—in our case, first-time discovery—then aligning the candidate set, representation, training objective, and evaluation protocol with that behavior. Here, a transparent local model provides the strongest foundation, a latent model contributes selective complementary information, and the hybrid works because their roles are validated rather than assumed. Thank you.

---
