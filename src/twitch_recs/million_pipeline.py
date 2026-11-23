from __future__ import annotations

import gc
import itertools
import json
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy import sparse

from .metrics import complementarity, evaluate_ranking
from .models import BPR, ItemKNN
from .recommend import (personalized_recommendations, popularity_recommendations,
                        single_model_recommendations)


@dataclass
class DiskFit:
    matrix: sparse.csr_matrix
    popularity: np.ndarray
    user_names: np.ndarray
    item_names: np.ndarray
    recent_popularity: np.ndarray


def _connection(config: dict) -> duckdb.DuckDBPyConnection:
    db_path = Path(config["data"]["database_path"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute("SET memory_limit='3GB'")
    con.execute(f"SET temp_directory='{db_path.parent / 'duckdb_tmp'}'")
    con.execute("SET threads=4")
    return con


def build_disk_store(config: dict, force: bool = False) -> dict:
    con = _connection(config)
    exists = con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name='interactions'"
    ).fetchone()[0]
    if force and exists:
        con.execute("DROP TABLE interactions")
        exists = 0
    if not exists:
        path = str(Path(config["data"]["raw_path"]).resolve()).replace("'", "''")
        con.execute(f"""
            CREATE TABLE interactions AS
            SELECT user_id, stream_id, channel, time_start, time_stop,
                   CAST(floor(time_start / {int(config['split']['slots_per_day'])}) AS UTINYINT) AS day
            FROM read_csv('{path}', header=false, columns={{
                'user_id':'INTEGER', 'stream_id':'BIGINT', 'channel':'VARCHAR',
                'time_start':'INTEGER', 'time_stop':'INTEGER'
            }})
        """)
    summary = con.execute("""
        SELECT count(*) interactions, count(DISTINCT user_id) users,
               count(DISTINCT channel) channels, min(time_start) min_start,
               max(time_stop) max_stop, count(DISTINCT day) relative_days
        FROM interactions
    """).fetchone()
    result = dict(zip(
        ["interactions", "users", "channels", "time_start_min", "time_stop_max", "relative_days"],
        map(int, summary),
    ))
    con.close()
    return result


def _prepare_fit(con: duckdb.DuckDBPyConnection, end_day: int, suffix: str,
                 recent_days: int) -> DiskFit:
    for table in (f"users_{suffix}", f"items_{suffix}", f"pairs_{suffix}"):
        con.execute(f"DROP TABLE IF EXISTS {table}")
    con.execute(f"""
        CREATE TABLE users_{suffix} AS
        SELECT CAST(row_number() OVER (ORDER BY user_id)-1 AS INTEGER) user_idx, user_id
        FROM (SELECT DISTINCT user_id FROM interactions WHERE day <= {end_day})
    """)
    con.execute(f"""
        CREATE TABLE items_{suffix} AS
        SELECT CAST(row_number() OVER (ORDER BY channel)-1 AS INTEGER) item_idx, channel
        FROM (SELECT DISTINCT channel FROM interactions WHERE day <= {end_day})
    """)
    con.execute(f"""
        CREATE TABLE pairs_{suffix} AS
        SELECT u.user_idx, i.item_idx
        FROM (SELECT DISTINCT user_id, channel FROM interactions WHERE day <= {end_day}) p
        JOIN users_{suffix} u USING(user_id)
        JOIN items_{suffix} i USING(channel)
    """)
    user_names = con.execute(f"SELECT user_id FROM users_{suffix} ORDER BY user_idx").fetchnumpy()["user_id"]
    item_names = con.execute(f"SELECT channel FROM items_{suffix} ORDER BY item_idx").fetchnumpy()["channel"]
    pairs = con.execute(f"SELECT user_idx,item_idx FROM pairs_{suffix} ORDER BY user_idx,item_idx").fetchnumpy()
    rows = pairs["user_idx"].astype(np.int32, copy=False)
    cols = pairs["item_idx"].astype(np.int32, copy=False)
    matrix = sparse.csr_matrix(
        (np.ones(len(rows), dtype=np.float32), (rows, cols)),
        shape=(len(user_names), len(item_names)), dtype=np.float32,
    )
    matrix.sort_indices()
    popularity = np.asarray(matrix.sum(axis=0)).ravel().astype(np.float32)
    recent = con.execute(f"""
        SELECT i.item_idx, count(DISTINCT x.user_id) AS viewer_count
        FROM interactions x JOIN items_{suffix} i USING(channel)
        WHERE x.day BETWEEN {end_day - recent_days + 1} AND {end_day}
        GROUP BY i.item_idx
    """).fetchnumpy()
    recent_popularity = np.zeros(len(item_names), dtype=np.float32)
    recent_popularity[recent["item_idx"].astype(int)] = recent["viewer_count"].astype(np.float32)
    del pairs, rows, cols
    return DiskFit(matrix, popularity, user_names, item_names, recent_popularity)


def _labels(con: duckdb.DuckDBPyConnection, suffix: str, fit_end: int,
            target_start: int, target_end: int, max_users: int | None,
            seed: int) -> tuple[pd.DataFrame, dict]:
    con.execute("DROP TABLE IF EXISTS target_first")
    con.execute(f"""
        CREATE TEMP TABLE target_first AS
        SELECT t.user_id, t.channel, min(t.day) AS first_day
        FROM interactions t
        LEFT JOIN (SELECT DISTINCT user_id,channel FROM interactions WHERE day <= {fit_end}) h
          USING(user_id,channel)
        WHERE t.day BETWEEN {target_start} AND {target_end} AND h.user_id IS NULL
        GROUP BY t.user_id,t.channel
    """)
    total = int(con.execute("SELECT count(*) FROM target_first").fetchone()[0])
    covered = int(con.execute(f"""
        SELECT count(*) FROM target_first t
        JOIN users_{suffix} u USING(user_id) JOIN items_{suffix} i USING(channel)
    """).fetchone()[0])
    limit = "" if max_users is None else f"LIMIT {int(max_users)}"
    con.execute("DROP TABLE IF EXISTS evaluation_users")
    con.execute(f"""
        CREATE TEMP TABLE evaluation_users AS
        SELECT u.user_idx FROM target_first t JOIN users_{suffix} u USING(user_id)
        GROUP BY u.user_idx ORDER BY hash(u.user_idx, {seed}) {limit}
    """)
    labels = con.execute(f"""
        SELECT u.user_idx, i.item_idx, CAST(t.first_day AS INTEGER) AS day
        FROM target_first t JOIN users_{suffix} u USING(user_id)
        JOIN items_{suffix} i USING(channel)
        JOIN evaluation_users e USING(user_idx)
        ORDER BY u.user_idx,t.first_day,i.item_idx
    """).fetch_df().astype({"user_idx":"int32", "item_idx":"int32", "day":"int32"})
    stats = {
        "novel_user_channel_positives": total,
        "candidate_covered_positives": covered,
        "candidate_coverage": covered / total if total else float("nan"),
        "evaluated_users": int(labels.user_idx.nunique()),
        "evaluation_cases": int(labels[["user_idx", "day"]].drop_duplicates().shape[0]),
    }
    return labels, stats


def _metric(name: str, recs: pd.DataFrame, labels: pd.DataFrame, fit: DiskFit,
            config: dict) -> dict:
    _, result = evaluate_ranking(
        recs, labels, config["model"]["top_k"], fit.popularity, fit.matrix.shape[1],
        config["evaluation"]["long_tail_quantile"],
    )
    result["model"] = name
    return result


def run_million_experiment(config: dict) -> dict:
    out = Path(config["outputs_dir"]); (out / "tables").mkdir(parents=True, exist_ok=True)
    summary = build_disk_store(config)
    (out / "dataset_summary.json").write_text(json.dumps(summary, indent=2))
    con = _connection(config)
    seed = int(config["seed"]); k = int(config["model"]["top_k"])

    train = _prepare_fit(con, 29, "train", config["model"]["recent_days"])
    val_labels, val_coverage = _labels(
        con, "train", 29, 30, 35, config["evaluation"]["max_validation_users"], seed)
    val_users = np.sort(val_labels.user_idx.unique()).astype(np.int32)
    val_rows = []
    val_rows.append(_metric("popularity", popularity_recommendations(
        val_users, train.matrix, train.popularity, k), val_labels, train, config))
    val_rows.append(_metric("recent_popularity", popularity_recommendations(
        val_users, train.matrix, train.recent_popularity, k), val_labels, train, config))

    best_cf = None; best_cf_score = -1.0; best_cf_params = None
    for neighbors in config["model"]["item_knn_neighbors"]:
        model = ItemKNN(neighbors, config["model"]["item_knn_batch_size"]).fit(train.matrix)
        recs = single_model_recommendations(
            val_users, train.matrix, lambda u, m=model: m.score_user(train.matrix[u]), k)
        row = _metric(f"item_knn_k{neighbors}", recs, val_labels, train, config); val_rows.append(row)
        if row["ndcg_at_10"] > best_cf_score:
            best_cf, best_cf_score, best_cf_params = model, row["ndcg_at_10"], {"neighbors":neighbors}
        else:
            del model
        gc.collect()

    best_bpr = None; best_bpr_score = -1.0; best_bpr_params = None
    for factors, lr, reg, epochs in itertools.product(
        config["model"]["bpr_factors"], config["model"]["bpr_learning_rates"],
        config["model"]["bpr_regularizations"], config["model"]["bpr_epochs"]):
        params = {"factors":factors,"learning_rate":lr,"regularization":reg,"epochs":epochs,
                  "negative_samples":config["model"]["bpr_negative_samples"],"seed":seed}
        model = BPR(**params).fit(train.matrix)
        recs = single_model_recommendations(val_users, train.matrix, model.score_user, k)
        row = _metric(f"bpr_f{factors}_r{reg:g}_e{epochs}", recs, val_labels, train, config); val_rows.append(row)
        if row["ndcg_at_10"] > best_bpr_score:
            best_bpr, best_bpr_score, best_bpr_params = model, row["ndcg_at_10"], params
        else:
            del model
        gc.collect()

    hybrid = personalized_recommendations(
        val_users, train.matrix, best_cf, best_bpr, train.popularity, k,
        config["model"]["alphas"], config["model"]["popularity_lambdas"])
    best_name = None; best_score = -1.0
    for name, recs in hybrid.items():
        if name in ("item_knn", "bpr"): continue
        row = _metric(name, recs, val_labels, train, config); val_rows.append(row)
        if row["ndcg_at_10"] > best_score: best_name, best_score = name, row["ndcg_at_10"]
    validation = pd.DataFrame(val_rows).sort_values("ndcg_at_10", ascending=False)
    validation.to_csv(out / "tables" / "validation_grid.csv", index=False)
    selected = {"item_knn":best_cf_params,"bpr":best_bpr_params,"hybrid_model_name":best_name}
    (out / "selected_hyperparameters.json").write_text(json.dumps(selected, indent=2))
    (out / "validation_candidate_coverage.json").write_text(json.dumps(val_coverage, indent=2))
    del train, best_cf, best_bpr, hybrid; gc.collect()

    final = _prepare_fit(con, 35, "final", config["model"]["recent_days"])
    test_labels, test_coverage = _labels(
        con, "final", 35, 36, 42, config["evaluation"]["max_test_users"], seed)
    users = np.sort(test_labels.user_idx.unique()).astype(np.int32)
    cf = ItemKNN(selected["item_knn"]["neighbors"], config["model"]["item_knn_batch_size"]).fit(final.matrix)
    bpr = BPR(**selected["bpr"]).fit(final.matrix)
    alpha = float(best_name.split("_a",1)[1].split("_",1)[0]); penalty = 0.0
    if "_p" in best_name: penalty = float(best_name.rsplit("_p",1)[1])
    personalized = personalized_recommendations(
        users, final.matrix, cf, bpr, final.popularity, k, [alpha], sorted({0.0, penalty}))
    recs = {
        "popularity":popularity_recommendations(users,final.matrix,final.popularity,k),
        "recent_popularity":popularity_recommendations(users,final.matrix,final.recent_popularity,k),
        "item_knn":personalized["item_knn"], "bpr":personalized["bpr"],
        f"hybrid_a{alpha:g}":personalized[f"hybrid_a{alpha:g}"],
    }
    if penalty > 0: recs[best_name] = personalized[best_name]
    rows = [_metric(name, frame, test_labels, final, config) for name,frame in recs.items()]
    test = pd.DataFrame(rows).sort_values("ndcg_at_10",ascending=False)
    test.to_csv(out / "tables" / "test_results.csv",index=False)
    (out / "test_candidate_coverage.json").write_text(json.dumps(test_coverage,indent=2))
    comp = complementarity(test_labels,recs["bpr"],recs["item_knn"])
    (out / "model_complementarity.json").write_text(json.dumps(comp,indent=2))
    con.close()
    return {"summary":summary,"selected":selected,"test_results":test.to_dict("records")}
