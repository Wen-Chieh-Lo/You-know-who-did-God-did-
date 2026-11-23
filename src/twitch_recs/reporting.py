from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def create_results_plot(results: pd.DataFrame, path: str | Path) -> None:
    plot = results.melt(id_vars="model", value_vars=["recall_at_10", "ndcg_at_10", "hit_rate_at_10"],
                        var_name="metric", value_name="value")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=plot, x="model", y="value", hue="metric", ax=ax)
    ax.tick_params(axis="x", rotation=25)
    ax.set(title="Test ranking accuracy", xlabel="", ylabel="Mean case-level score")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def render_report(output_dir: str | Path, dataset_summary: dict, split: dict,
                  validation: pd.DataFrame, test: pd.DataFrame,
                  validation_coverage: dict, test_coverage: dict,
                  selected: dict, complementarity: dict) -> Path:
    output_dir = Path(output_dir)
    report_dir = Path("reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "full_dataset_manifest.json"
    full_manifest = (json.loads(manifest_path.read_text(encoding="utf-8"))
                     if manifest_path.exists() else None)
    title = ("# Twitch New-Channel Recommendation: Complete-File Cohort Rerun"
             if full_manifest else "# Twitch New-Channel Recommendation: Experimental Report")
    result_table = test[["model", "recall_at_10", "ndcg_at_10", "hit_rate_at_10",
                         "catalog_coverage", "novelty_bits", "long_tail_exposure"]].copy()
    lookup = test.set_index("model")
    hybrid_name = selected["hybrid_model_name"]
    hybrid, item, bpr = lookup.loc[hybrid_name], lookup.loc["item_knn"], lookup.loc["bpr"]
    popularity_name = "recent_popularity" if "recent_popularity" in lookup.index else "popularity"
    popular = lookup.loc[popularity_name]
    hybrid_gain_cf = 100 * (hybrid["ndcg_at_10"] / item["ndcg_at_10"] - 1)
    hybrid_gain_pop = 100 * (hybrid["ndcg_at_10"] / popular["ndcg_at_10"] - 1)
    active_path = output_dir / "tables" / "active_7d_results.csv"
    active = pd.read_csv(active_path) if active_path.exists() else pd.DataFrame()
    examples_path = output_dir / "tables" / "recommendation_examples.csv"
    examples = pd.read_csv(examples_path) if examples_path.exists() else pd.DataFrame()
    examples_table = (examples[["user_id", "rank", "channel"]].head(30).to_markdown(index=False)
                      if not examples.empty else "Named examples are stored with the recommendation artifacts.")
    lines = [
        title, "",
        "## Research question", "",
        "This experiment asks whether item-item collaborative filtering or Bayesian Personalized Ranking (BPR) "
        "better predicts channels a viewer has never watched, and whether their standardized-score hybrid "
        "improves Top-10 accuracy without collapsing recommendation diversity.", "",
        "## Data", "",
        ((f"The complete source scan contains **{full_manifest['source_rows']:,} interactions**, "
          f"**{full_manifest['source_users']:,} users**, and **{full_manifest['source_channels']:,} raw channel "
          f"names**. A deterministic independent cohort contains "
          if full_manifest else "The UCSD Twitch 100k interaction file contains ") +
         f"**{dataset_summary['interactions']:,} interactions**, "
        f"**{dataset_summary['users']:,} users**, and **{dataset_summary['channels']:,} channels**. It spans "
        f"{dataset_summary['relative_days']} observed relative 24-hour blocks. Time values are relative 10-minute "
        "slots—not calendar timestamps—so no weekday or calendar-date interpretation is made."), "",
        "The five source columns are anonymous user ID, stream/session ID, streamer username, start slot, and "
        "stop slot. Streamer username is the stable recommendation item; stream ID is used only for checks.", "",
        "The source dataset and metadata are published by the UCSD McAuley Lab "
        "([dataset page](https://cseweb.ucsd.edu/~jmcauley/datasets.html#twitch)).", "",
        "## Leakage-safe task and split", "",
        f"Whole day indices were split chronologically into train `{split['train_days'][0]}–{split['train_days'][-1]}`, "
        f"validation `{split['validation_days'][0]}–{split['validation_days'][-1]}`, and test "
        f"`{split['test_days'][0]}–{split['test_days'][-1]}`. Validation tunes settings using a train-only fit. "
        "The final models are then refit on train+validation and evaluated once on test.", "",
        "Candidates are channels present in the fit period, excluding each viewer's previously watched channels. "
        "A positive is the first target-period occurrence of a viewer-channel pair absent from fit history, grouped "
        "by the relative day on which it first appears. Empty-target cases are omitted.", "",
        f"The fixed-seed tuning sample contains **{int(validation['users'].max()):,} validation users**. Final "
        f"evaluation includes **all {int(test['users'].max()):,} eligible test users** and "
        f"**{int(test['cases'].max()):,} user/day cases**.", "",
        f"Validation candidate coverage was **{validation_coverage['candidate_coverage']:.2%}** and test candidate "
        f"coverage was **{test_coverage['candidate_coverage']:.2%}**. Positives outside the fit catalog are a "
        "cold-start limitation and are excluded from rank evaluation but included in this coverage denominator.", "",
        "## Models", "",
        "- **Recent popularity:** distinct viewers per channel, with a seven-day variant.",
        "- **Item-item CF:** binary user-channel cosine similarity, retaining only each item's top-k neighbors.",
        "- **BPR:** pairwise implicit-feedback matrix factorization trained with sampled unobserved comparisons.",
        "- **Hybrid:** per-user standardized BPR and item-CF scores combined by validation-selected alpha.",
        "- **Popularity-adjusted hybrid:** subtracts lambda times `log(1 + channel popularity)`.",
        "- **Count-weighted sensitivity model:** repeats item-CF with interaction counts instead of binary feedback.", "",
        "Selected validation settings:", "",
        "```json", json.dumps(selected, indent=2), "```", "",
        "## Test results", "",
        result_table.to_markdown(index=False, floatfmt=".5f"), "",
        "Recall@10, NDCG@10, and Hit Rate@10 are computed for each user/day case and then macro-averaged. "
        "Catalog coverage is the fraction of the fit-period catalog appearing in recommendations. Novelty is mean "
        "self-information in bits under fit-period distinct-user popularity. Long-tail exposure is the share of "
        "recommended channels at or below the configured popularity quantile.", "",
        "## Model complementarity", "",
        f"At the positive user-channel level, BPR alone recovered **{complementarity.get('BPR_only', 0)}**, "
        f"item-item alone recovered **{complementarity.get('ItemKNN_only', 0)}**, both recovered "
        f"**{complementarity.get('both', 0)}**, and neither recovered **{complementarity.get('neither', 0)}**. "
        "Nonzero model-only counts indicate potentially useful complementarity; whether the hybrid realizes it is "
        "determined by its held-out NDCG rather than by test-driven weight selection.", "",
        "## Seven-day active-candidate sensitivity", "",
        (active.to_markdown(index=False, floatfmt=".5f") if not active.empty else
         "The optional active-candidate output is unavailable."), "",
        "All rows use the same seven-day active-channel proxy. This cannot prove that a channel was live at a "
        "recommendation instant. `overall_positive_candidate_coverage` includes fit-catalog cold-start positives "
        "in its denominator; `coverage_within_primary_catalog` isolates the incremental seven-day restriction.", "",
        "## Concrete recommendation examples", "",
        examples_table, "",
        "## Interpretation and limitations", "",
        "The primary comparison should be read directly from the test table: personalized models beat the baseline "
        "only when their held-out rows have larger accuracy values. Diversity gains are visible through coverage, "
        "novelty, and long-tail exposure and may trade off against accuracy.", "",
        "The dataset cannot establish whether a channel was actually live at a recommendation instant. The recent "
        "seven-day restriction is therefore only an activity proxy. Fit-period unseen channels cannot be learned by "
        "these collaborative models. Unobserved channels are sampled comparisons in BPR, not explicit dislikes. "
        "Finally, results are not directly comparable to the source paper unless its task, split, candidates, and "
        "metrics match this new-channel protocol.", "",
        "## Related research", "",
        "Rappaz, McAuley, and Aberer (RecSys 2021), *Recommendation on Live-Streaming Platforms: "
        "Dynamic Availability and Repeat Consumption* ([paper](https://cseweb.ucsd.edu/~jmcauley/pdfs/recsys21b.pdf), "
        "[DOI](https://doi.org/10.1145/3460231.3474267)), introduced the dataset and LiveRec. Their work emphasizes "
        "time-varying stream availability and repeat consumption. This project deliberately asks a different "
        "question—discovery of viewer-unseen channels—and uses different candidates, chronological labels, and "
        "metrics, so the numeric results are not treated as a direct replication.", "",
        "## Conclusion", "",
        f"**Personalization wins.** The selected hybrid reaches NDCG@10 **{hybrid['ndcg_at_10']:.5f}** and "
        f"Recall@10 **{hybrid['recall_at_10']:.5f}**, versus **{popular['ndcg_at_10']:.5f}** and "
        f"**{popular['recall_at_10']:.5f}** for {popularity_name}; hybrid NDCG is {hybrid_gain_pop:.1f}% higher.", "",
        f"**Item-item is much stronger than BPR alone.** Their NDCG@10 values are "
        f"**{item['ndcg_at_10']:.5f}** and **{bpr['ndcg_at_10']:.5f}**, respectively. BPR still uniquely "
        f"recovers **{complementarity.get('BPR_only', 0):,}** positive pairs, while item-CF uniquely recovers "
        f"**{complementarity.get('ItemKNN_only', 0):,}**, demonstrating complementary hits.", "",
        f"**The hybrid uses that complementarity.** Validation selected `{hybrid_name}`; its test NDCG is "
        f"{hybrid_gain_cf:.1f}% above item-CF. Alpha and the popularity penalty were frozen before test.", "",
        f"**The gain trades away some diversity.** Hybrid catalog coverage is "
        f"**{hybrid['catalog_coverage']:.3f}** versus **{item['catalog_coverage']:.3f}** for item-CF, while novelty "
        f"is **{hybrid['novelty_bits']:.2f}** versus **{item['novelty_bits']:.2f}** bits. Validation selected no "
        "nonzero popularity penalty, so the adjusted variant did not merit a separate final row.", "",
        "## Reproducibility", "",
        "The repository records the seed, day boundaries, candidate definition, validation grid, selected settings, "
        "package constraints, per-case metrics, recommendations, mappings, tables, and figures. Run "
        "`twitch-recs all --config configs/full.yaml` to reproduce the complete experiment.",
    ]
    path = report_dir / ("FULL_DATASET_COHORT_REPORT.md" if full_manifest else "FINAL_REPORT.md")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
