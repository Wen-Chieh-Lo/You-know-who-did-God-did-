from __future__ import annotations

import csv
import gzip
import hashlib
import json
import time
from collections import Counter
from pathlib import Path


def _selected(user_id: str, seed: int, modulus: int) -> bool:
    digest = hashlib.blake2b(f"{seed}:{user_id}".encode(), digest_size=8).digest()
    return int.from_bytes(digest, "little") % modulus == 0


def extract_deterministic_user_cohort(config: dict) -> dict:
    """Scan the complete file and materialize a reproducible user cohort.

    The complete Twitch file is ordered by numeric user ID. Streaming preserves all
    interactions for selected users without loading the full dataset into memory.
    Global activity and distinct-viewer popularity statistics use every source row.
    """
    source = Path(config["data"]["full_source_path"])
    destination = Path(config["data"]["raw_path"])
    manifest_path = Path(config["data"]["manifest_path"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    seed = int(config["seed"])
    modulus = int(config["data"]["sample_modulus"])
    slots_per_day = int(config["split"]["slots_per_day"])
    train_val_end = 35

    rows = users = sampled_rows = sampled_users = 0
    channels: set[str] = set()
    sampled_channels: set[str] = set()
    day_counts: Counter[int] = Counter()
    final_fit_popularity: Counter[str] = Counter()
    recent_popularity: Counter[str] = Counter()
    current_user: str | None = None
    current_numeric = -1
    current_selected = False
    fit_seen: set[str] = set()
    recent_seen: set[str] = set()
    min_start, max_stop = 10**9, -1
    started = time.time()

    def finish_user() -> None:
        final_fit_popularity.update(fit_seen)
        recent_popularity.update(recent_seen)

    with gzip.open(source, "rt", newline="") as input_handle, temporary.open(
        "w", newline="", encoding="utf-8"
    ) as output_handle:
        writer = csv.writer(output_handle, lineterminator="\n")
        for line_number, line in enumerate(input_handle, 1):
            parts = line.rstrip("\n").split(",")
            if len(parts) != 5:
                raise ValueError(f"Malformed source row {line_number}: {parts!r}")
            user_id, stream_id, channel, start_text, stop_text = parts
            if user_id != current_user:
                if current_user is not None:
                    finish_user()
                numeric = int(user_id)
                if numeric <= current_numeric:
                    raise ValueError(
                        "Full-data streaming requires strictly increasing grouped user IDs; "
                        f"observed {numeric} after {current_numeric}"
                    )
                current_user, current_numeric = user_id, numeric
                current_selected = _selected(user_id, seed, modulus)
                fit_seen = set()
                recent_seen = set()
                users += 1
                sampled_users += int(current_selected)
            start, stop = int(start_text), int(stop_text)
            day = start // slots_per_day
            rows += 1
            channels.add(channel)
            day_counts[day] += 1
            min_start, max_stop = min(min_start, start), max(max_stop, stop)
            if day <= train_val_end:
                fit_seen.add(channel)
                if day >= train_val_end - 6:
                    recent_seen.add(channel)
            if current_selected:
                writer.writerow((user_id, stream_id, channel, start, stop))
                sampled_rows += 1
                sampled_channels.add(channel)
        if current_user is not None:
            finish_user()
    temporary.replace(destination)

    popularity_path = manifest_path.parent / "full_catalog_popularity.csv"
    with popularity_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("channel", "fit_distinct_users", "recent_distinct_users"))
        for channel in sorted(final_fit_popularity):
            writer.writerow((channel, final_fit_popularity[channel], recent_popularity[channel]))

    manifest = {
        "source_path": str(source),
        "source_bytes": source.stat().st_size,
        "source_rows": rows,
        "source_users": users,
        "source_channels": len(channels),
        "time_start_min": min_start,
        "time_stop_max": max_stop,
        "relative_days": len(day_counts),
        "day_interactions": dict(sorted(day_counts.items())),
        "sampling": {
            "method": "blake2b(seed:user_id) modulo sample_modulus equals zero",
            "seed": seed,
            "sample_modulus": modulus,
            "sampled_users": sampled_users,
            "sampled_rows": sampled_rows,
            "sampled_channels": len(sampled_channels),
        },
        "cohort_path": str(destination),
        "full_catalog_popularity_path": str(popularity_path),
        "elapsed_seconds": round(time.time() - started, 2),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def extract_systematic_exact_cohort(config: dict) -> dict:
    """Extract exactly N evenly spaced anonymized user IDs in one complete scan."""
    source = Path(config["data"]["full_source_path"])
    destination = Path(config["data"]["raw_path"])
    manifest_path = Path(config["data"]["manifest_path"])
    source_manifest = json.loads(Path(config["data"]["source_manifest_path"]).read_text())
    total_users = int(source_manifest["source_users"])
    target_users = int(config["data"]["target_users"])
    if not 0 < target_users <= total_users:
        raise ValueError("target_users must be between 1 and source user count")
    destination.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    rows = selected_rows = selected_users = users = 0
    channels: set[str] = set()
    current_user: str | None = None
    current_numeric = 0
    selected = False
    started = time.time()
    with gzip.open(source, "rt", newline="") as input_handle, temporary.open(
        "w", newline="", encoding="utf-8"
    ) as output_handle:
        writer = csv.writer(output_handle, lineterminator="\n")
        for line_number, line in enumerate(input_handle, 1):
            parts = line.rstrip("\n").split(",")
            if len(parts) != 5:
                raise ValueError(f"Malformed source row {line_number}")
            user_id = parts[0]
            if user_id != current_user:
                numeric = int(user_id)
                if numeric != current_numeric + 1:
                    raise ValueError(
                        "Exact systematic extraction expects consecutive IDs; "
                        f"observed {numeric} after {current_numeric}"
                    )
                current_user, current_numeric = user_id, numeric
                users += 1
                selected = ((numeric * target_users) // total_users !=
                            ((numeric - 1) * target_users) // total_users)
                selected_users += int(selected)
            rows += 1
            if selected:
                writer.writerow(parts)
                selected_rows += 1
                channels.add(parts[2])
    if users != total_users or selected_users != target_users:
        raise ValueError(
            f"Extraction invariant failed: users={users}, selected={selected_users}, "
            f"expected={total_users}/{target_users}"
        )
    temporary.replace(destination)
    manifest = {
        "source_path": str(source), "source_rows": rows, "source_users": users,
        "target_users": target_users, "selected_users": selected_users,
        "selected_rows": selected_rows, "selected_channels": len(channels),
        "selection": "exact systematic sample over consecutive anonymized user IDs",
        "cohort_path": str(destination),
        "elapsed_seconds": round(time.time() - started, 2),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
