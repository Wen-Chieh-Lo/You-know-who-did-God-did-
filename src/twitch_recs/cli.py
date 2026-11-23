from __future__ import annotations

import argparse
import json

from .config import load_config
from .data import download_dataset, load_interactions
from .eda import create_eda, dataset_summary
from .pipeline import finalize_existing_experiment, run_experiment
from .million_pipeline import build_disk_store, run_million_experiment
from .full_scale import extract_deterministic_user_cohort, extract_systematic_exact_cohort
from .assignment_analysis import run_assignment_analysis
from .advanced_pipeline import run_advanced_experiment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Twitch new-channel recommendation experiment")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("download", "eda", "run", "all", "finalize", "extract-full",
                 "extract-million", "run-million", "assignment-analysis", "advanced"):
        command = subparsers.add_parser(name)
        command.add_argument("--config", default="configs/full.yaml")
        if name == "download":
            command.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(args.config)
    if args.command in ("download", "all"):
        path = download_dataset(config["data"]["url"], config["data"]["raw_path"],
                                getattr(args, "force", False))
        print(f"Dataset: {path}")
    if args.command == "download":
        return
    if args.command == "eda":
        frame = load_interactions(config["data"]["raw_path"], config["split"]["slots_per_day"])
        print(json.dumps(dataset_summary(frame), indent=2))
        create_eda(frame, config["outputs_dir"])
        return
    if args.command == "extract-full":
        print(json.dumps(extract_deterministic_user_cohort(config), indent=2))
        return
    if args.command == "extract-million":
        print(json.dumps(extract_systematic_exact_cohort(config), indent=2))
        return
    if args.command == "run-million":
        print(json.dumps(run_million_experiment(config), indent=2))
        return
    if args.command == "assignment-analysis":
        print(json.dumps(run_assignment_analysis(config), indent=2))
        return
    if args.command == "advanced":
        print(json.dumps(run_advanced_experiment(config), indent=2))
        return
    if args.command == "finalize":
        print(json.dumps(finalize_existing_experiment(config), indent=2))
        return
    result = run_experiment(config)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
