# CSE 258 Assignment 2 — 20-minute English speaker notes

Deck: `cse258_assignment2_20min_en.pptx`

The timing totals approximately 20 minutes. During slide 9, briefly switch to the workbook or repository for the code walkthrough recommended by the assignment.

## 1. Twitch New-Channel Recommendation

Timing: 0:00–0:35 (35 sec)

Hello. This project studies new-channel recommendation on Twitch. Instead of predicting whether a viewer returns to a familiar streamer, we use past viewing history to recommend ten channels that the viewer has never watched but may discover in the future. I will organize the presentation around the five required CSE 258 Assignment 2 sections.

## 2. Assignment requirements

Timing: 0:35–1:15 (40 sec)

The official specification grades five sections. This deck explicitly covers all five and keeps the organization visible to peer graders. The central narrative is not just a list of experiments: each EDA finding motivates a feature, model, metric, or limitation. I also explain negative results because the rubric asks that all results make sense, including methods that did not work well.

## 3. Predictive task

Timing: 1:15–2:25 (70 sec)

The input is a viewer's past binary channel history. The model scores every channel known during fitting, excludes channels already seen, and returns ten recommendations. A positive is a channel first watched in the future target period. This is a ranking task rather than a rating or ordinary classification task. A non-interaction is ambiguous, especially on a live platform, so global and recent popularity are important sanity-check baselines.

## 4. Dataset

Timing: 2:25–3:30 (65 sec)

The data comes from the public UCSD Twitch dataset and records chat connections in ten-minute slots. The official subset contains one hundred thousand users, over one hundred sixty-two thousand channels, and just over three million interactions. The audit found no basic quality failures. The challenge is the enormous, highly sparse matrix and the absence of language, game category, text, or other content features.

## 5. EDA: long-tail popularity

Timing: 3:30–4:40 (70 sec)

Both axes are logarithmic, yet popularity still spans several orders of magnitude. This directly motivates three design choices. Popularity must be a baseline. Long-tail channels may not provide enough data for stable latent factors. Finally, we cannot judge the system using NDCG alone because a concentrated recommender may be accurate while exposing almost none of the catalog.

## 6. EDA: repeat viewing and cold-start

Timing: 4:40–5:40 (60 sec)

Repeat viewing becomes more common, which agrees with the original LiveRec motivation. Our task deliberately isolates discovery, so repeat channels are excluded from the test target and the main matrix is binary. We evaluate count weighting separately. A second key result is that about twelve percent of future novel positives were never observed in fitting. Pure collaborative filtering cannot retrieve those items.

## 7. Split and validity

Timing: 5:40–6:55 (75 sec)

The first thirty days are used to fit candidate models, the next six select hyperparameters, and the final seven form the test. Every mapping, popularity statistic, similarity, and learned factor is computed only from the relevant fit period. Evaluation ranks the full catalog, rather than a small set of easy negatives. Because users contribute multiple day cases, the paired confidence intervals resample users and preserve all cases from a sampled user.

## 8. Models

Timing: 6:55–8:25 (90 sec)

Popularity is the necessary non-personalized baseline. ItemKNN computes channel cosine similarity from shared viewers and directly preserves local co-view structure. BPR learns user and item embeddings with a pairwise objective. The hybrid standardizes each score distribution per user and combines them. Ordinary binary classification is not a natural fit because there are enormous numbers of ambiguous missing pairs and the deployment output is a ranked top-ten list.

## 9. Code walkthrough

Timing: 8:25–9:20 (55 sec)

The YAML configuration fixes the seed and search space. DuckDB supports the larger cohort runs. ItemKNN uses sparse block multiplication so the full dense item-item matrix is never materialized, and only the strongest two hundred neighbors per channel are retained. The validation and test stages are separate. During the recording, I would briefly show these model, pipeline, evaluation, and analysis files in the notebook or repository.

## 10. Hyperparameter selection

Timing: 9:20–10:25 (65 sec)

This validation ablation varies the BPR mixing weight on the x-axis and the popularity penalty across lines. Alpha equal to one means BPR alone, which explains the large drop at the right edge. The validation optimum is alpha point seven five, while no nonzero popularity penalty improves NDCG. ItemKNN selects two hundred neighbors, and BPR selects sixty-four factors and twenty epochs. None of these choices uses test performance.

## 11. Evaluation metrics

Timing: 10:25–11:35 (70 sec)

Recall measures how many future discoveries the top ten retrieves. NDCG also rewards placing correct channels earlier and is our primary selection metric. Catalog coverage asks a different question: how broadly recommendations are distributed. Hit rate, novelty, long-tail exposure, and candidate coverage complete the picture. A model should not be called universally better based on a single accuracy number.

## 12. Main results

Timing: 11:35–13:10 (95 sec)

Hybrid has the highest recall, NDCG, and hit rate. ItemKNN reaches NDCG point one two five eight and is the strongest individual model. BPR is much lower at point zero five four two, although it still beats popularity. Hybrid improves NDCG over recent popularity by about two hundred forty-eight percent. However, Hybrid recommends from only about twenty-six percent of the catalog, versus thirty-seven percent for ItemKNN. Count-weighted ItemKNN is less accurate but has the greatest diversity, so the choice depends on product goals.

## 13. Explaining BPR and Hybrid

Timing: 13:10–14:50 (100 sec)

BPR's poor result is not explained by one bug. Long-tail factors are poorly estimated, missing views are noisy negatives, and one uniform negative per positive is often trivial. The low-dimensional representation may also lose the local relationships preserved by ItemKNN, and its training objective is not identical to unseen-channel top-ten evaluation. Five training seeds remain far below ItemKNN, so this is not an unlucky seed. Still, BPR uniquely retrieves over five thousand positives, which produces a small but statistically clear hybrid gain.

## 14. Subgroup behavior

Timing: 14:50–16:05 (75 sec)

Average performance hides large subgroup differences. Recall is only point zero three three for targets in the least-popular quartile, compared with over point four for the most popular quartile. NDCG also falls as a user's history grows, possibly because easy similar channels have already been consumed. Truly zero-history users cannot be personalized and require a popularity fallback, which reaches NDCG around point zero five three.

## 15. Robustness and scalability

Timing: 16:05–17:20 (75 sec)

Rolling-origin evaluation shows lower absolute accuracy in later windows, but the ordering remains Hybrid, ItemKNN, BPR, then popularity. The scaling runs use seed 258, the same search grid, and the same validation and test caps at one hundred thousand through one million users. Hybrid and ItemKNN are stable; BPR weakens as the catalog expands. Because the cohorts and catalogs are not fixed or nested, this is scalability and robustness evidence—not a causal learning curve.

## 16. Related work and limitations

Timing: 17:20–18:45 (85 sec)

LiveRec uses the same source data but studies a different target: currently available live streams and repeat behavior. Our project isolates new-channel discovery and lacks exact live status, so numerical results are not directly comparable. The key transferable lesson is that availability should be modeled. BPR provides the pairwise ranking foundation, and LightGCN is a relevant graph-based extension. The next version should improve hard-negative sampling, add availability and content metadata, rerank for diversity, and ultimately run an online experiment.

## 17. Conclusions

Timing: 18:45–20:00 (75 sec)

There are three main conclusions. First, personalization clearly works: Hybrid substantially outperforms popularity. Second, ItemKNN's local co-view inductive bias is a better fit for this sparse discovery task than the current BPR setup. Third, the best model depends on the product objective. Hybrid is most accurate, while ItemKNN covers more of the catalog, and neither solves catalog cold-start or exact live availability. The main takeaway is that additional data or model complexity does not guarantee improvement unless the assumptions match the task. Thank you.
