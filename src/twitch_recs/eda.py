from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def dataset_summary(frame: pd.DataFrame) -> dict[str, int | float]:
    return {
        "interactions": int(len(frame)),
        "users": int(frame["user_id"].nunique()),
        "channels": int(frame["channel"].nunique()),
        "streams": int(frame["stream_id"].nunique()),
        "time_start_min": int(frame["time_start"].min()),
        "time_stop_max": int(frame["time_stop"].max()),
        "relative_days": int(frame["day"].nunique()),
        "missing_values": int(frame.isna().sum().sum()),
    }


def create_eda(frame: pd.DataFrame, output_dir: str | Path) -> dict[str, pd.DataFrame]:
    output_dir = Path(output_dir)
    figures = output_dir / "figures"
    tables = output_dir / "tables"
    figures.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    user_channels = frame.groupby("user_id")["channel"].nunique().rename("distinct_channels")
    channel_interactions = frame.groupby("channel").agg(
        interactions=("user_id", "size"), distinct_users=("user_id", "nunique")
    ).sort_values("interactions", ascending=False)
    daily = frame.groupby("day").agg(
        interactions=("user_id", "size"), users=("user_id", "nunique"),
        channels=("channel", "nunique")
    ).reset_index()

    ordered = frame.sort_values(["user_id", "time_start", "channel"])
    first_seen = ~ordered.duplicated(["user_id", "channel"])
    new_return = ordered.assign(interaction_type=np.where(first_seen, "new channel", "return"))
    new_return_daily = new_return.groupby(["day", "interaction_type"]).size().rename("interactions").reset_index()

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(np.log1p(user_channels), bins=50, ax=ax)
    ax.set(xlabel="log(1 + distinct channels per user)", title="User history breadth")
    fig.tight_layout(); fig.savefig(figures / "user_distinct_channels.png", dpi=160); plt.close(fig)

    ranks = np.arange(1, len(channel_interactions) + 1)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.loglog(ranks, channel_interactions["interactions"].to_numpy())
    ax.set(xlabel="Channel popularity rank", ylabel="Interactions", title="Long-tail channel popularity")
    fig.tight_layout(); fig.savefig(figures / "channel_long_tail.png", dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.lineplot(data=daily, x="day", y="interactions", marker="o", ax=ax)
    ax.set(xlabel="Relative 24-hour block (day index)", title="Interactions by relative day")
    fig.tight_layout(); fig.savefig(figures / "daily_interactions.png", dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.lineplot(data=new_return_daily, x="day", y="interactions", hue="interaction_type", ax=ax)
    ax.set(xlabel="Relative 24-hour block (day index)", title="New-channel and return interactions")
    fig.tight_layout(); fig.savefig(figures / "new_vs_return.png", dpi=160); plt.close(fig)

    user_channels.describe(percentiles=[.25, .5, .75, .9, .95, .99]).to_csv(tables / "user_history_summary.csv")
    channel_interactions.to_csv(tables / "channel_popularity.csv")
    daily.to_csv(tables / "daily_activity.csv", index=False)
    new_return_daily.to_csv(tables / "new_vs_return.csv", index=False)
    return {"daily": daily, "channel_popularity": channel_interactions,
            "new_vs_return": new_return_daily}
