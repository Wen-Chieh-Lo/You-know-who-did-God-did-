import gzip
import json

import numpy as np
import pandas as pd

from twitch_recs.data import (chronological_split, encode_fit_period,
                              interaction_count_matrix, make_evaluation_labels,
                              recent_item_mask)
from twitch_recs.full_scale import extract_systematic_exact_cohort


def frame():
    rows = [
        ("u1", "s1", "a", 0, 1, 0, 1),
        ("u1", "s2", "b", 150, 151, 1, 1),
        ("u1", "s3", "c", 300, 301, 2, 1),
        ("u2", "s4", "a", 1, 2, 0, 1),
        ("u2", "s5", "b", 301, 302, 2, 1),
        ("u3", "s6", "d", 0, 1, 0, 1),
    ]
    return pd.DataFrame(rows, columns=["user_id", "stream_id", "channel", "time_start",
                                       "time_stop", "day", "duration_slots"])


def test_split_is_chronological_and_disjoint():
    split = chronological_split(frame(), 1 / 3, 1 / 3)
    assert split.train_days.tolist() == [0]
    assert split.validation_days.tolist() == [1]
    assert split.test_days.tolist() == [2]


def test_labels_only_known_users_catalog_and_unseen_pairs():
    data = frame()
    fit = encode_fit_period(data, np.array([0, 1]))
    labels, stats = make_evaluation_labels(data, fit, np.array([2]))
    names = set(fit.item_names[labels["item_idx"].to_numpy()])
    assert names == {"b"}  # c is cold-start; b is new to u2 but is in catalog.
    assert stats["novel_user_channel_positives"] == 2
    assert stats["candidate_coverage"] == 0.5


def test_recent_item_mask_handles_string_catalog():
    data = frame()
    fit = encode_fit_period(data, np.array([0, 1]))
    mask = recent_item_mask(data, fit, fit_end_day=1, recent_days=1)
    assert set(fit.item_names[mask]) == {"b"}


def test_count_matrix_preserves_repeated_rows():
    data = pd.concat([frame(), frame().iloc[[0]]], ignore_index=True)
    fit = encode_fit_period(data, np.array([0]))
    counts = interaction_count_matrix(fit)
    user = int(np.flatnonzero(fit.user_names == "u1")[0])
    item = int(np.flatnonzero(fit.item_names == "a")[0])
    assert counts[user, item] == 2


def test_systematic_cohort_selects_exact_user_count(tmp_path):
    source = tmp_path / "source.csv.gz"
    destination = tmp_path / "cohort.csv"
    manifest = tmp_path / "cohort.json"
    source_manifest = tmp_path / "source.json"
    rows = [
        "1,10,a,0,1\n",
        "2,20,b,0,1\n",
        "3,30,c,0,1\n",
        "3,31,d,2,3\n",
        "4,40,e,0,1\n",
        "5,50,f,0,1\n",
    ]
    with gzip.open(source, "wt") as handle:
        handle.writelines(rows)
    source_manifest.write_text(json.dumps({"source_users": 5}))
    config = {
        "data": {
            "full_source_path": str(source),
            "raw_path": str(destination),
            "manifest_path": str(manifest),
            "source_manifest_path": str(source_manifest),
            "target_users": 2,
        }
    }

    result = extract_systematic_exact_cohort(config)

    assert result["selected_users"] == 2
    assert result["selected_rows"] == 3
    selected_ids = {line.split(",", 1)[0] for line in destination.read_text().splitlines()}
    assert selected_ids == {"3", "5"}

