"""Build the English CSE 258 Assignment 2 presentation."""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches

from build_assignment2_slides import (
    BLUE,
    CYAN,
    GREEN,
    GRID,
    INK,
    LIGHT,
    MUTED,
    NAVY,
    ORANGE,
    OUT_DIR,
    PURPLE,
    RED,
    ROOT,
    SLIDES,
    WHITE,
    add_bullets,
    add_card,
    add_footer as _add_footer,
    add_header,
    add_metric,
    add_notes,
    add_picture_fit,
    add_rect,
    add_table,
    add_text,
    arrow,
    set_background,
)


PPTX_PATH = OUT_DIR / "cse258_assignment2_20min_en.pptx"
NOTES_PATH = OUT_DIR / "cse258_assignment2_speaker_notes_en.md"


def add_footer(slide, text: str = "CSE 258 · Assignment 2 · Twitch New-Channel Recommendation") -> None:
    _add_footer(slide, text)


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SLIDES.clear()
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # 1 — Title
    slide = prs.slides.add_slide(blank)
    set_background(slide, NAVY)
    add_rect(slide, 0, 0, 0.18, 7.5, fill=CYAN, radius=False)
    add_text(slide, "CSE 258 · ASSIGNMENT 2", 0.75, 0.65, 6.0, 0.35,
             size=14, color=CYAN, bold=True)
    add_text(slide, "Twitch New-Channel Recommendation", 0.75, 1.35, 11.8, 0.9,
             size=36, color=WHITE, bold=True)
    add_text(slide,
             "Learning from highly sparse implicit feedback to recommend channels "
             "a viewer has never watched before",
             0.78, 2.42, 10.8, 0.95, size=21, color=LIGHT)
    add_rect(slide, 0.78, 3.68, 5.75, 1.24, fill=BLUE)
    add_text(slide, "MAIN RESULT", 1.05, 3.88, 2.0, 0.3,
             size=12, color=WHITE, bold=True)
    add_text(slide, "Hybrid NDCG@10 = 0.1315", 1.05, 4.25, 5.0, 0.38,
             size=23, color=WHITE, bold=True)
    add_text(slide, "Web Mining and Recommender Systems · 20-minute presentation",
             0.78, 6.65, 9.0, 0.3, size=12, color=GRID)
    add_notes(slide, "Twitch New-Channel Recommendation", "0:00–0:35 (35 sec)",
              "Hello. This project studies new-channel recommendation on Twitch. "
              "Instead of predicting whether a viewer returns to a familiar streamer, "
              "we use past viewing history to recommend ten channels that the viewer "
              "has never watched but may discover in the future. I will organize the "
              "presentation around the five required CSE 258 Assignment 2 sections.")

    # 2 — Requirement mapping
    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_header(slide, "How this deck maps to the Assignment 2 requirements",
               "Rubric roadmap", 2)
    cards = [
        ("1", "Predictive task", "Task, baselines,\nand validity", BLUE),
        ("2", "Data and EDA", "Collection, preprocessing,\nplots, and phenomena", CYAN),
        ("3", "Modeling", "Formulation, tradeoffs,\nand code walkthrough", ORANGE),
        ("4", "Evaluation", "Metrics, results,\nand significance", GREEN),
        ("5", "Related work", "Prior use, differences,\nand limitations", PURPLE),
    ]
    for i, (num, title, body, color) in enumerate(cards):
        x = 0.6 + i * 2.52
        add_rect(slide, x, 1.62, 2.24, 3.65, fill=LIGHT, line=GRID)
        add_rect(slide, x + 0.72, 1.92, 0.8, 0.8, fill=color)
        add_text(slide, num, x + 0.72, 2.04, 0.8, 0.42, size=23,
                 color=WHITE, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, title, x + 0.13, 3.02, 1.98, 0.46, size=16.5,
                 color=NAVY, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, body, x + 0.12, 3.72, 2.0, 1.0, size=12.5,
                 color=MUTED, align=PP_ALIGN.CENTER)
    add_text(slide,
             "Narrative: EDA findings → model choices → leakage-safe evaluation → explanations",
             1.15, 5.82, 11.0, 0.5, size=20, color=NAVY, bold=True,
             align=PP_ALIGN.CENTER)
    add_footer(slide, "CSE 258 Assignment 2: five sections × approximately five marks")
    add_notes(slide, "Assignment requirements", "0:35–1:15 (40 sec)",
              "The official specification grades five sections. This deck explicitly "
              "covers all five and keeps the organization visible to peer graders. "
              "The central narrative is not just a list of experiments: each EDA "
              "finding motivates a feature, model, metric, or limitation. I also "
              "explain negative results because the rubric asks that all results make "
              "sense, including methods that did not work well.")

    # 3 — Task
    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_header(slide, "Predictive task: rank channels the viewer has never watched",
               "1 · Predictive task", 3)
    boxes = [
        (0.6, "INPUT", "Binary viewing history\nin the fit period", BLUE),
        (3.9, "RANK", "Score the full fit catalog\nand remove seen channels", ORANGE),
        (7.25, "OUTPUT", "A personalized\nTop-10 list", GREEN),
        (10.25, "TARGET", "Future first-time\nuser-channel pairs", PURPLE),
    ]
    for i, (x, title, body, color) in enumerate(boxes):
        add_card(slide, x, 1.55, 2.45, 2.05, title, body,
                 accent=color, body_size=15)
        if i < len(boxes) - 1:
            arrow(slide, x + 2.55, 2.35, 0.42)
    add_rect(slide, 0.6, 4.17, 12.1, 1.75, fill=LIGHT, line=GRID)
    add_text(slide, "This is a ranking problem—not rating prediction",
             0.9, 4.43, 4.8, 0.42, size=20, color=BLUE, bold=True)
    add_bullets(slide, [
        "A missing interaction is not an explicit dislike; the channel may have been offline.",
        "Required baselines: global popularity and recent seven-day popularity.",
        "Validity: chronological holdout, full-catalog ranking, and paired inference.",
    ], 5.3, 4.28, 7.0, 1.3, size=14.5, spacing=3)
    add_footer(slide)
    add_notes(slide, "Predictive task", "1:15–2:25 (70 sec)",
              "The input is a viewer's past binary channel history. The model scores "
              "every channel known during fitting, excludes channels already seen, and "
              "returns ten recommendations. A positive is a channel first watched in "
              "the future target period. This is a ranking task rather than a rating or "
              "ordinary classification task. A non-interaction is ambiguous, especially "
              "on a live platform, so global and recent popularity are important sanity-check baselines.")

    # 4 — Dataset
    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_header(slide, "Dataset: 100K viewers, 3.05M interactions, 43 days",
               "2 · Dataset and EDA", 4)
    metrics = [
        ("100,000", "viewers", BLUE), ("162,625", "channels", ORANGE),
        ("3,051,733", "interactions", GREEN), ("739,991", "stream sessions", PURPLE),
        ("43", "relative days", CYAN),
    ]
    for i, (value, label, color) in enumerate(metrics):
        add_metric(slide, 0.65 + i * 2.47, 1.45, 2.25, value, label, color)
    add_card(slide, 0.65, 2.95, 5.72, 2.72, "Source and fields",
             "UCSD McAuley Lab Twitch dataset\nAnonymous user ID, stream ID, streamer name, "
             "start and stop time slots\nOne slot is ten minutes; no ratings or content metadata",
             accent=BLUE, body_size=14.5)
    add_card(slide, 6.62, 2.95, 6.05, 2.72, "Quality and the real challenge",
             "Missing cells, duplicates, invalid durations, and blank names: all zero\n"
             "The theoretical user-channel matrix has over 16.2 billion cells\n"
             "The main problems are sparsity, long-tail items, and catalog cold-start",
             accent=RED, body_size=14.5)
    add_text(slide,
             "Implicit feedback: observed viewing is positive; the meaning of missing is unknown",
             1.0, 6.1, 11.3, 0.45, size=19, color=NAVY, bold=True,
             align=PP_ALIGN.CENTER)
    add_footer(slide, "Source: UCSD Twitch dataset; Rappaz, McAuley, and Aberer (RecSys 2021)")
    add_notes(slide, "Dataset", "2:25–3:30 (65 sec)",
              "The data comes from the public UCSD Twitch dataset and records chat "
              "connections in ten-minute slots. The official subset contains one "
              "hundred thousand users, over one hundred sixty-two thousand channels, "
              "and just over three million interactions. The audit found no basic "
              "quality failures. The challenge is the enormous, highly sparse matrix "
              "and the absence of language, game category, text, or other content features.")

    # 5 — Long tail
    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_header(slide, "EDA finding 1: channel popularity is extremely long-tailed",
               "2 · Dataset and EDA", 5)
    add_picture_fit(slide, ROOT / "outputs/figures/channel_long_tail.png",
                    0.55, 1.35, 7.45, 5.35)
    add_card(slide, 8.25, 1.55, 4.35, 1.32, "Observation",
             "A small head receives many interactions, while most channels have very little data.",
             accent=ORANGE, body_size=13.5)
    add_card(slide, 8.25, 3.05, 4.35, 1.32, "Model implication",
             "Popularity is a meaningful baseline; long-tail BPR embeddings may be poorly estimated.",
             accent=RED, body_size=13.5)
    add_card(slide, 8.25, 4.55, 4.35, 1.62, "Evaluation implication",
             "Accuracy alone can hide concentration, so we also measure coverage, novelty, and long-tail exposure.",
             accent=GREEN, body_size=13.5)
    add_footer(slide)
    add_notes(slide, "EDA: long-tail popularity", "3:30–4:40 (70 sec)",
              "Both axes are logarithmic, yet popularity still spans several orders "
              "of magnitude. This directly motivates three design choices. Popularity "
              "must be a baseline. Long-tail channels may not provide enough data for "
              "stable latent factors. Finally, we cannot judge the system using NDCG "
              "alone because a concentrated recommender may be accurate while exposing "
              "almost none of the catalog.")

    # 6 — Repeat and cold-start
    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_header(slide, "EDA finding 2: repeat viewing grows, but our target is discovery",
               "2 · Dataset and EDA", 6)
    add_picture_fit(slide, ROOT / "outputs/figures/new_vs_return.png",
                    0.55, 1.38, 7.6, 5.3)
    add_card(slide, 8.35, 1.55, 4.25, 1.45, "Repeat viewing is strong",
             "Return interactions increase over time and are central to live-stream behavior.",
             accent=BLUE, body_size=13.5)
    add_card(slide, 8.35, 3.25, 4.25, 1.45, "But repeats are not targets",
             "The primary representation is binary so heavy repeat viewing does not dominate discovery.",
             accent=ORANGE, body_size=13.5)
    add_card(slide, 8.35, 4.95, 4.25, 1.35, "Cold-start ceiling",
             "About 12% of novel test positives are outside the fit catalog and cannot be retrieved.",
             accent=RED, body_size=13.5)
    add_footer(slide)
    add_notes(slide, "EDA: repeat viewing and cold-start", "4:40–5:40 (60 sec)",
              "Repeat viewing becomes more common, which agrees with the original "
              "LiveRec motivation. Our task deliberately isolates discovery, so repeat "
              "channels are excluded from the test target and the main matrix is binary. "
              "We evaluate count weighting separately. A second key result is that about "
              "twelve percent of future novel positives were never observed in fitting. "
              "Pure collaborative filtering cannot retrieve those items.")

    # 7 — Split and validity
    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_header(slide, "Chronological splitting prevents future-information leakage",
               "1 and 4 · Validity", 7)
    add_rect(slide, 0.75, 1.55, 7.9, 0.86, fill=BLUE)
    add_text(slide, "TRAIN · DAYS 0–29 · FIT CANDIDATE MODELS", 0.95, 1.77, 7.45, 0.32,
             size=17, color=WHITE, bold=True)
    add_rect(slide, 8.65, 1.55, 1.65, 0.86, fill=ORANGE)
    add_text(slide, "VALIDATION\n30–35", 8.65, 1.64, 1.65, 0.57,
             size=13, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    add_rect(slide, 10.30, 1.55, 2.25, 0.86, fill=GREEN)
    add_text(slide, "TEST · 36–42", 10.30, 1.77, 2.25, 0.32,
             size=17, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    add_card(slide, 0.75, 2.92, 3.75, 2.75, "Leakage prevention",
             "Mappings, popularity, similarities, and embeddings use only the fit period\n\n"
             "Validation selects settings; test is used once",
             accent=BLUE, body_size=14.5)
    add_card(slide, 4.78, 2.92, 3.75, 2.75, "Full-catalog ranking",
             "No evaluation against a handful of sampled negatives\n\n"
             "Every known channel is ranked after removing seen items",
             accent=ORANGE, body_size=14.5)
    add_card(slide, 8.81, 2.92, 3.75, 2.75, "Statistical validity",
             "53,212 users and 104,818 user-day cases\n\n"
             "10,000 user-clustered paired bootstrap draws plus Holm correction",
             accent=GREEN, body_size=14.5)
    add_footer(slide)
    add_notes(slide, "Split and validity", "5:40–6:55 (75 sec)",
              "The first thirty days are used to fit candidate models, the next six "
              "select hyperparameters, and the final seven form the test. Every mapping, "
              "popularity statistic, similarity, and learned factor is computed only from "
              "the relevant fit period. Evaluation ranks the full catalog, rather than a "
              "small set of easy negatives. Because users contribute multiple day cases, "
              "the paired confidence intervals resample users and preserve all cases from "
              "a sampled user.")

    # 8 — Models
    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_header(slide, "Models: from co-view neighborhoods to latent factors",
               "3 · Modeling", 8)
    model_cards = [
        (0.65, "Popularity", "Same ranking for most users\n+ Fast and interpretable\n− Almost no personalization", MUTED),
        (3.70, "ItemKNN", "Cosine similarity from co-viewers\n+ Preserves local structure\n− Neighbor computation cost", BLUE),
        (6.75, "BPR", "User and item embeddings\nscore(u,i) > score(u,j)\n− Depends on negative sampling", ORANGE),
        (9.80, "Hybrid", "Standardize and combine scores\n+ Complementary hits\n− Less coverage than ItemKNN", GREEN),
    ]
    for x, title, body, color in model_cards:
        add_card(slide, x, 1.42, 2.88, 2.25, title, body,
                 accent=color, body_size=13.5)
    add_rect(slide, 1.05, 4.25, 11.2, 1.3, fill=LIGHT, line=GRID)
    add_text(slide,
             "Hybrid = α · z(BPR) + (1 − α) · z(ItemKNN) − λ · log(1 + popularity)",
             1.25, 4.57, 10.8, 0.48, size=20, color=NAVY, bold=True,
             align=PP_ALIGN.CENTER)
    add_text(slide,
             "Why not ordinary classification? Missing pairs are abundant, ambiguous, and the output must be ranked.",
             1.05, 5.95, 11.2, 0.5, size=17.5, color=MUTED,
             align=PP_ALIGN.CENTER)
    add_footer(slide, "BPR: Rendle et al. (UAI 2009)")
    add_notes(slide, "Models", "6:55–8:25 (90 sec)",
              "Popularity is the necessary non-personalized baseline. ItemKNN computes "
              "channel cosine similarity from shared viewers and directly preserves local "
              "co-view structure. BPR learns user and item embeddings with a pairwise "
              "objective. The hybrid standardizes each score distribution per user and "
              "combines them. Ordinary binary classification is not a natural fit because "
              "there are enormous numbers of ambiguous missing pairs and the deployment "
              "output is a ranked top-ten list.")

    # 9 — Code walkthrough
    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_header(slide, "Implementation: sparse, disk-backed, and reproducible",
               "3 · Code walkthrough", 9)
    stages = [
        ("YAML config\nseed 258", BLUE), ("DuckDB\nchronological split", CYAN),
        ("Sparse ItemKNN\nBPR SGD", ORANGE), ("Validation\n33 settings", PURPLE),
        ("Full-catalog\nTop-10", GREEN),
    ]
    for i, (body, color) in enumerate(stages):
        x = 0.72 + i * 2.48
        add_rect(slide, x, 1.6, 1.95, 1.25, fill=color)
        add_text(slide, body, x + 0.08, 1.85, 1.79, 0.7, size=14.5,
                 color=WHITE, bold=True, align=PP_ALIGN.CENTER)
        if i < len(stages) - 1:
            arrow(slide, x + 2.02, 2.03, 0.35)
    add_card(slide, 0.72, 3.38, 3.78, 2.2, "ItemKNN scaling",
             "Sparse block multiplication\nNo 162K × 162K dense matrix\nKeep only top-200 neighbors per item",
             accent=BLUE, body_size=13.5)
    add_card(slide, 4.77, 3.38, 3.78, 2.2, "Model selection",
             "Three neighborhood sizes, eight BPR settings, and twenty hybrid settings\n"
             "The test set never selects parameters",
             accent=ORANGE, body_size=13.5)
    add_card(slide, 8.82, 3.38, 3.78, 2.2, "Repository map",
             "models/item_knn.py · models/bpr.py\npipeline.py · evaluation.py\nassignment_analysis.py",
             accent=GREEN, body_size=13.5)
    add_text(slide,
             "The same pipeline completed matched-protocol runs at 100K, 200K, 500K, and 1M users",
             1.05, 6.05, 11.2, 0.45, size=17.5, color=NAVY, bold=True,
             align=PP_ALIGN.CENTER)
    add_footer(slide)
    add_notes(slide, "Code walkthrough", "8:25–9:20 (55 sec)",
              "The YAML configuration fixes the seed and search space. DuckDB supports "
              "the larger cohort runs. ItemKNN uses sparse block multiplication so the "
              "full dense item-item matrix is never materialized, and only the strongest "
              "two hundred neighbors per channel are retained. The validation and test "
              "stages are separate. During the recording, I would briefly show these model, "
              "pipeline, evaluation, and analysis files in the notebook or repository.")

    # 10 — Hyperparameters
    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_header(slide, "Hyperparameters are selected on validation only",
               "3 · Model selection", 10)
    add_picture_fit(slide, ROOT / "outputs/assignment2/figures/hybrid_ablation.png",
                    0.55, 1.38, 7.65, 5.25)
    add_card(slide, 8.40, 1.55, 4.15, 1.28, "ItemKNN",
             "k ∈ {50, 100, 200}\nSelected k = 200", accent=BLUE, body_size=14)
    add_card(slide, 8.40, 3.03, 4.15, 1.45, "BPR",
             "64 factors · learning rate 0.03\nregularization 0.0025 · 20 epochs\n1 negative per positive",
             accent=ORANGE, body_size=13.5)
    add_card(slide, 8.40, 4.70, 4.15, 1.52, "Hybrid",
             "α ∈ {0, .25, .5, .75, 1}\nλ ∈ {0, .05, .1, .2}\nSelected α = .75 and λ = 0",
             accent=GREEN, body_size=13.5)
    add_footer(slide)
    add_notes(slide, "Hyperparameter selection", "9:20–10:25 (65 sec)",
              "This validation ablation varies the BPR mixing weight on the x-axis and "
              "the popularity penalty across lines. Alpha equal to one means BPR alone, "
              "which explains the large drop at the right edge. The validation optimum is "
              "alpha point seven five, while no nonzero popularity penalty improves NDCG. "
              "ItemKNN selects two hundred neighbors, and BPR selects sixty-four factors "
              "and twenty epochs. None of these choices uses test performance.")

    # 11 — Metrics
    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_header(slide, "Different metrics answer different product questions",
               "4 · Evaluation", 11)
    add_card(slide, 0.65, 1.45, 3.7, 2.15, "Recall@10",
             "Of the channels actually discovered, how many appear in the top ten?\n\n"
             "It does not distinguish rank one from rank ten.", accent=BLUE, body_size=14)
    add_card(slide, 4.56, 1.45, 3.7, 2.15, "NDCG@10 · primary",
             "Rewards both retrieval and placing correct channels near the top.\n\n"
             "This selects validation hyperparameters.", accent=ORANGE, body_size=14)
    add_card(slide, 8.47, 1.45, 3.86, 2.15, "Catalog coverage",
             "What fraction of fit-catalog channels is recommended at least once?\n\n"
             "Breadth is not the same as correctness.", accent=GREEN, body_size=14)
    add_table(slide, [
        ["Supporting metric", "Question answered"],
        ["Hit Rate@10", "Does the list contain at least one hit?"],
        ["Novelty", "Does the model avoid only the most popular items?"],
        ["Long-tail exposure", "How much recommendation space reaches small channels?"],
        ["Candidate coverage", "Could the fit catalog contain the correct answer?"],
    ], 1.15, 4.12, 11.0, 1.82, widths=[3.0, 8.0], font_size=12.5)
    add_text(slide, "A useful decision must consider accuracy × diversity × cold-start feasibility",
             1.1, 6.25, 11.1, 0.4, size=18, color=NAVY, bold=True,
             align=PP_ALIGN.CENTER)
    add_footer(slide)
    add_notes(slide, "Evaluation metrics", "10:25–11:35 (70 sec)",
              "Recall measures how many future discoveries the top ten retrieves. NDCG "
              "also rewards placing correct channels earlier and is our primary selection "
              "metric. Catalog coverage asks a different question: how broadly recommendations "
              "are distributed. Hit rate, novelty, long-tail exposure, and candidate coverage "
              "complete the picture. A model should not be called universally better based on "
              "a single accuracy number.")

    # 12 — Results
    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_header(slide, "Main result: Hybrid is most accurate; ItemKNN is the best single model",
               "4 · Main results", 12)
    add_picture_fit(slide, ROOT / "outputs/figures/test_accuracy.png",
                    0.45, 1.30, 7.85, 5.25)
    add_metric(slide, 8.55, 1.48, 3.75, "0.13148", "Hybrid NDCG@10", GREEN)
    add_metric(slide, 8.55, 2.75, 3.75, "+247.9%", "vs. recent popularity NDCG", BLUE)
    add_card(slide, 8.55, 4.05, 3.75, 1.82, "Accuracy–diversity tradeoff",
             "Hybrid improves NDCG over ItemKNN by 4.48%\n"
             "but catalog coverage falls from 36.71% to 26.36%",
             accent=ORANGE, body_size=13.5)
    add_text(slide, "Every personalized model beats the popularity baselines",
             8.50, 6.10, 3.85, 0.45, size=16, color=NAVY, bold=True,
             align=PP_ALIGN.CENTER)
    add_footer(slide)
    add_notes(slide, "Main results", "11:35–13:10 (95 sec)",
              "Hybrid has the highest recall, NDCG, and hit rate. ItemKNN reaches NDCG "
              "point one two five eight and is the strongest individual model. BPR is much "
              "lower at point zero five four two, although it still beats popularity. Hybrid "
              "improves NDCG over recent popularity by about two hundred forty-eight percent. "
              "However, Hybrid recommends from only about twenty-six percent of the catalog, "
              "versus thirty-seven percent for ItemKNN. Count-weighted ItemKNN is less accurate "
              "but has the greatest diversity, so the choice depends on product goals.")

    # 13 — Interpretation
    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_header(slide, "Why is BPR weak, and why can it still improve the hybrid?",
               "4 · Interpretation", 13)
    add_card(slide, 0.65, 1.42, 5.85, 3.65, "BPR mismatch",
             "1. Long-tail channels provide too little data for stable embeddings\n"
             "2. A missing view may mean offline—not disliked\n"
             "3. One uniform negative per positive is usually too easy\n"
             "4. A 64-dimensional space compresses many local relationships\n"
             "5. Random pairwise training differs from unseen-channel Top-10 evaluation",
             accent=RED, body_size=14.5)
    add_card(slide, 6.80, 1.42, 5.85, 2.08, "Complementary hits",
             "ItemKNN only: 22,559\nBPR only: 5,540\nBoth: 7,648",
             accent=GREEN, body_size=18)
    add_card(slide, 6.80, 3.75, 5.85, 1.83, "Small but statistically supported gain",
             "Hybrid − ItemKNN NDCG = +0.005638\n"
             "95% user-clustered CI [0.005201, 0.006088]\n"
             "Holm-adjusted p = 0.0024",
             accent=BLUE, body_size=13.5)
    add_rect(slide, 0.95, 5.78, 11.45, 0.68, fill=LIGHT, line=GRID)
    add_text(slide,
             "BPR is weak overall but contributes ranking signals that ItemKNN misses",
             1.15, 5.96, 11.05, 0.3, size=18, color=NAVY, bold=True,
             align=PP_ALIGN.CENTER)
    add_footer(slide)
    add_notes(slide, "Explaining BPR and Hybrid", "13:10–14:50 (100 sec)",
              "BPR's poor result is not explained by one bug. Long-tail factors are poorly "
              "estimated, missing views are noisy negatives, and one uniform negative per "
              "positive is often trivial. The low-dimensional representation may also lose "
              "the local relationships preserved by ItemKNN, and its training objective is "
              "not identical to unseen-channel top-ten evaluation. Five training seeds remain "
              "far below ItemKNN, so this is not an unlucky seed. Still, BPR uniquely retrieves "
              "over five thousand positives, which produces a small but statistically clear hybrid gain.")

    # 14 — Subgroups
    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_header(slide, "Who is difficult to recommend for? Long-tail targets and long histories",
               "4 · Subgroup analysis", 14)
    add_picture_fit(slide, ROOT / "outputs/assignment2/figures/channel_popularity_subgroups.png",
                    0.45, 1.35, 6.25, 4.55)
    add_picture_fit(slide, ROOT / "outputs/assignment2/figures/user_history_subgroups.png",
                    6.70, 1.35, 6.15, 4.55)
    add_rect(slide, 0.75, 5.98, 5.6, 0.64, fill=LIGHT, line=GRID)
    add_text(slide, "Least-popular target quartile: Recall@10 = 0.0328",
             0.95, 6.14, 5.2, 0.3, size=15.5, color=RED, bold=True,
             align=PP_ALIGN.CENTER)
    add_rect(slide, 6.98, 5.98, 5.55, 0.64, fill=LIGHT, line=GRID)
    add_text(slide, "1–6 history items: NDCG 0.1679; 25+: 0.0901",
             7.12, 6.14, 5.27, 0.3, size=15.5, color=BLUE, bold=True,
             align=PP_ALIGN.CENTER)
    add_footer(slide)
    add_notes(slide, "Subgroup behavior", "14:50–16:05 (75 sec)",
              "Average performance hides large subgroup differences. Recall is only point "
              "zero three three for targets in the least-popular quartile, compared with over "
              "point four for the most popular quartile. NDCG also falls as a user's history "
              "grows, possibly because easy similar channels have already been consumed. Truly "
              "zero-history users cannot be personalized and require a popularity fallback, "
              "which reaches NDCG around point zero five three.")

    # 15 — Robustness and scale
    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_header(slide, "Robustness: model ordering survives time shifts and scale increases",
               "4 · Robustness and scalability", 15)
    add_picture_fit(slide, ROOT / "outputs/assignment2/figures/rolling_backtest.png",
                    0.45, 1.30, 6.25, 4.65)
    add_picture_fit(slide, ROOT / "outputs/assignment2/figures/scalability_ndcg.png",
                    6.75, 1.30, 6.15, 4.65)
    add_text(slide, "Absolute accuracy declines over time; ordering remains unchanged",
             0.65, 6.05, 5.9, 0.42, size=15, color=NAVY, bold=True,
             align=PP_ALIGN.CENTER)
    add_text(slide, "100K / 200K / 500K / 1M: Hybrid > ItemKNN > BPR",
             6.92, 6.05, 5.75, 0.42, size=15, color=NAVY, bold=True,
             align=PP_ALIGN.CENTER)
    add_footer(slide)
    add_notes(slide, "Robustness and scalability", "16:05–17:20 (75 sec)",
              "Rolling-origin evaluation shows lower absolute accuracy in later windows, "
              "but the ordering remains Hybrid, ItemKNN, BPR, then popularity. The scaling "
              "runs use seed 258, the same search grid, and the same validation and test caps "
              "at one hundred thousand through one million users. Hybrid and ItemKNN are stable; "
              "BPR weakens as the catalog expands. Because the cohorts and catalogs are not fixed "
              "or nested, this is scalability and robustness evidence—not a causal learning curve.")

    # 16 — Related work
    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_header(slide, "Related work: our discovery task differs from LiveRec",
               "5 · Related work and limitations", 16)
    add_table(slide, [
        ["Aspect", "LiveRec (Rappaz et al., 2021)", "This project"],
        ["Target", "Rank currently available streams", "Discover never-watched channels"],
        ["Repeat viewing", "Core signal", "Excluded from the primary target"],
        ["Availability", "Explicit live-status modeling", "Seven-day activity proxy"],
        ["Models", "Self-attention plus availability", "Popularity, ItemKNN, BPR, Hybrid"],
    ], 0.65, 1.45, 12.0, 2.55, widths=[2.0, 5.0, 5.0], font_size=12)
    add_card(slide, 0.65, 4.35, 3.78, 1.55, "Limitation 1 · cold-start",
             "About 12% of novel positives are outside the fit catalog and cannot be retrieved.",
             accent=RED, body_size=12.5)
    add_card(slide, 4.78, 4.35, 3.78, 1.55, "Limitation 2 · availability",
             "Exact live status is missing, so observed non-interactions are noisy negatives.",
             accent=ORANGE, body_size=12.5)
    add_card(slide, 8.91, 4.35, 3.78, 1.55, "Next steps",
             "Hard negatives, live availability, content metadata, two-stage reranking, and online A/B tests.",
             accent=GREEN, body_size=12.5)
    add_text(slide,
             "Other relevant methods: BPR (Rendle et al., 2009); LightGCN (He et al., 2020)",
             1.2, 6.30, 10.9, 0.3, size=12.5, color=MUTED,
             align=PP_ALIGN.CENTER)
    add_footer(slide)
    add_notes(slide, "Related work and limitations", "17:20–18:45 (85 sec)",
              "LiveRec uses the same source data but studies a different target: currently "
              "available live streams and repeat behavior. Our project isolates new-channel "
              "discovery and lacks exact live status, so numerical results are not directly "
              "comparable. The key transferable lesson is that availability should be modeled. "
              "BPR provides the pairwise ranking foundation, and LightGCN is a relevant graph-based "
              "extension. The next version should improve hard-negative sampling, add availability "
              "and content metadata, rerank for diversity, and ultimately run an online experiment.")

    # 17 — Conclusion
    slide = prs.slides.add_slide(blank)
    set_background(slide, NAVY)
    add_text(slide, "Conclusions", 0.75, 0.65, 4.0, 0.55,
             size=30, color=WHITE, bold=True)
    conclusions = [
        ("01", "Personalization works",
         "Hybrid NDCG@10 is 0.1315, compared with 0.0370 for popularity.", CYAN),
        ("02", "Inductive bias matters",
         "ItemKNN matches the strong local co-view signal; BPR suffers from sparsity and noisy negatives.", ORANGE),
        ("03", "Best depends on the objective",
         "Hybrid is most accurate; ItemKNN is broader; cold-start and availability remain unresolved.", GREEN),
    ]
    for i, (num, title, body, color) in enumerate(conclusions):
        y = 1.55 + i * 1.48
        add_rect(slide, 0.78, y, 0.72, 0.72, fill=color)
        add_text(slide, num, 0.78, y + 0.14, 0.72, 0.35,
                 size=18, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, title, 1.78, y - 0.02, 3.25, 0.4,
                 size=20, color=WHITE, bold=True)
        add_text(slide, body, 5.0, y - 0.01, 7.1, 0.75,
                 size=15.5, color=LIGHT)
    add_rect(slide, 0.78, 6.28, 11.65, 0.04, fill=BLUE, radius=False)
    add_text(slide,
             "Takeaway: more data or a more complex model is not automatically better; the model must match the task.",
             0.85, 6.55, 11.5, 0.45, size=18.5, color=CYAN, bold=True,
             align=PP_ALIGN.CENTER)
    add_notes(slide, "Conclusions", "18:45–20:00 (75 sec)",
              "There are three main conclusions. First, personalization clearly works: Hybrid "
              "substantially outperforms popularity. Second, ItemKNN's local co-view inductive "
              "bias is a better fit for this sparse discovery task than the current BPR setup. "
              "Third, the best model depends on the product objective. Hybrid is most accurate, "
              "while ItemKNN covers more of the catalog, and neither solves catalog cold-start "
              "or exact live availability. The main takeaway is that additional data or model "
              "complexity does not guarantee improvement unless the assumptions match the task. Thank you.")

    prs.save(PPTX_PATH)
    notes_lines = [
        "# CSE 258 Assignment 2 — 20-minute English speaker notes",
        "",
        "Deck: `cse258_assignment2_20min_en.pptx`",
        "",
        "The timing totals approximately 20 minutes. During slide 9, briefly switch to "
        "the workbook or repository for the code walkthrough recommended by the assignment.",
        "",
    ]
    for index, item in enumerate(SLIDES, 1):
        notes_lines.extend([
            f"## {index}. {item['title']}", "", f"Timing: {item['timing']}", "",
            item["notes"], "",
        ])
    NOTES_PATH.write_text("\n".join(notes_lines), encoding="utf-8")
    print(f"Wrote {PPTX_PATH}")
    print(f"Wrote {NOTES_PATH}")


if __name__ == "__main__":
    build()
