# Twitch New-Channel Recommendation

This repository implements the full experiment specified in
[`Twitch_New_Channel_Recommendation_Plan.md`](Twitch_New_Channel_Recommendation_Plan.md):
recommend ten channels that a viewer has not previously watched, compare popularity,
item-item collaborative filtering, BPR, and a hybrid, and measure both accuracy and
diversity under a chronological, leakage-safe protocol.

## What is implemented

- Official UCSD Twitch 100k download and five-column validation
- Relative 24-hour day indices and whole-day 70/15/15 chronological split
- Train-only channel/user encodings and binary sparse feedback
- First-new-channel user/day targets and candidate coverage
- Distinct-user popularity and recent seven-day popularity
- Batched sparse top-k item cosine collaborative filtering
- From-scratch BPR with negative sampling, regularization, and fixed seeds
- Validation grids for item neighbors, BPR factors/regularization/epochs, hybrid alpha,
  and popularity penalty lambda
- Train+validation refit followed by a single test evaluation
- Recall@10, NDCG@10, Hit Rate@10, catalog coverage, novelty, and long-tail exposure
- Seven-day active-candidate proxy, complementarity, user-history groups, channel
  popularity groups, EDA tables/figures, named recommendation examples, and a report
- Unit tests and a results-reading notebook

The choices left open by the plan are documented in
[`ASSUMPTIONS_AND_DECISIONS.md`](ASSUMPTIONS_AND_DECISIONS.md).

## Setup and run

Python 3.10+ is supported.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
twitch-recs all --config configs/full.yaml
```

`all` downloads `100k_a.csv` from the official UCSD directory if it is absent, runs
EDA, tunes on validation, refits, evaluates test, and writes the final report. The raw
dataset and generated artifacts are gitignored.

For a fast end-to-end verification that evaluates a deterministic user sample and uses
a small training grid:

```bash
twitch-recs all --config configs/quick.yaml
```

Individual stages are also available:

```bash
twitch-recs download --config configs/full.yaml
twitch-recs eda --config configs/full.yaml
twitch-recs run --config configs/full.yaml
twitch-recs finalize --config configs/full.yaml  # recover optional analysis/report from completed primary artifacts
pytest
```

For the complete-file scalability experiments, first place the source file at
`data/raw/full_a.csv.gz`. The exact one-million-user cohort and its disk-backed
experiment are reproduced with:

```bash
twitch-recs extract-million --config configs/million.yaml
twitch-recs run-million --config configs/million.yaml
```

This uses all selected users for model training and deterministic capped validation
and test user samples for ranking. See
[`reports/MILLION_USER_REPORT.md`](reports/MILLION_USER_REPORT.md) for the results,
scope, and limitations.

Assignment-specific validity, temporal-robustness, feature-ablation, data-quality,
and scaling analyses are reproduced after the main 100k experiment with:

```bash
twitch-recs assignment-analysis --config configs/full.yaml
```

The resulting tables and presentation-ready figures are written under
`outputs/assignment2/`; their interpretation is summarized in
[`reports/ASSIGNMENT_EXPERIMENTS.md`](reports/ASSIGNMENT_EXPERIMENTS.md).

Additional no-metadata models (LightGCN, SASRec, GRU4Rec, time-decayed ItemKNN,
and a clearly labelled LiveRec-like seven-day availability proxy) are reproduced with:

```bash
python -m pip install -e '.[advanced]'
./scripts/run_advanced.sh configs/full.yaml
```

They use the same chronological split and test labels and write separately under
`outputs/advanced/`. The wrapper works around the Intel ITT linkage issue in the
project machine's installed PyTorch; on a normal PyTorch installation it simply runs
the CLI. The checked-in interpretation is in
[`report.md`](report.md#7-新增模型實驗lightgcn-與序列模型); full generated tables remain
local experiment artifacts under the ignored output directory.

## Repository layout

```text
configs/                 Reproducible full, quick, and million-user settings
data/raw/                Downloaded source data (ignored)
data/processed/          Optional local caches (ignored)
notebooks/               Presentation-oriented results notebook
outputs/figures/         Generated EDA and result charts (ignored)
outputs/tables/          Metrics, subgroups, and recommendations (ignored)
reports/                 Generated final report
src/twitch_recs/         Data, models, evaluation, reporting, and CLI code
tests/                   Synthetic leakage/model/metric tests
```

## Output contract

Important artifacts include:

- `reports/FINAL_REPORT.md`
- `reports/FULL_DATASET_COHORT_REPORT.md`
- `reports/MILLION_USER_REPORT.md`
- `outputs/split.json` and `outputs/selected_hyperparameters.json`
- `outputs/tables/validation_grid.csv` and `outputs/tables/test_results.csv`
- `outputs/tables/recommendations_*.csv`
- `outputs/tables/item_mapping.csv`, `user_mapping.csv`, and `recommendation_examples.csv`
- `outputs/tables/user_history_subgroups.csv`
- `outputs/tables/channel_popularity_subgroups.csv`
- `outputs/tables/active_7d_results.csv`
- `outputs/model_complementarity.json`
- `outputs/active_7d_experiment.json`
- `outputs/figures/*.png`
- `outputs_million/tables/validation_grid.csv` and `test_results.csv`
- `outputs_million/cohort_manifest.json` and candidate-coverage JSON files

## Methodological guardrails

Time slots are relative and are never treated as calendar dates. Test interactions do
not enter matrices, popularity, similarities, or model fitting. Channels absent from a
fit period are reported through candidate coverage but cannot be ranked by these
collaborative models. Unwatched channels are BPR comparison samples, not dislikes.

