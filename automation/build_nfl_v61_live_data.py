
from io import BytesIO
import requests
import pandas as pd
import numpy as np

PBP_URL = (
    "https://github.com/nflverse/nflverse-data/releases/"
    "download/pbp/play_by_play_{season}.parquet"
)

def download_pbp(season):
    url = PBP_URL.format(season=season)
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    return pd.read_parquet(BytesIO(response.content))

def build_team_metrics(pbp, season, target_week):
    required = [
        "game_id", "season", "week",
        "season_type", "posteam", "defteam",
        "play_type", "epa", "success",
        "interception", "fumble_lost"
    ]

    missing = set(required) - set(pbp.columns)
    if missing:
        raise ValueError(
            f"Missing play-by-play fields: {sorted(missing)}"
        )

    plays = pbp[
        (pbp["season"] == season) &
        (pbp["season_type"] == "REG") &
        (pbp["week"] < target_week) &
        pbp["play_type"].isin(["pass", "run"]) &
        pbp["posteam"].notna() &
        pbp["defteam"].notna() &
        pbp["epa"].notna()
    ].copy()

    if plays.empty:
        raise ValueError("No completed-game plays found")

    plays["is_pass"] = (
        plays["play_type"] == "pass"
    ).astype(int)

    plays["turnover_event"] = (
        plays["interception"].fillna(0) +
        plays["fumble_lost"].fillna(0)
    )

    offense = plays.groupby(
        ["game_id", "season", "week", "posteam"]
    ).agg(
        plays=("epa", "size"),
        off_epa=("epa", "mean"),
        off_success=("success", "mean"),
        pass_rate=("is_pass", "mean"),
        turnovers=("turnover_event", "sum")
    ).reset_index().rename(
        columns={"posteam": "team"}
    )

    for play_type, metric in [
        ("pass", "pass_epa"),
        ("run", "rush_epa")
    ]:
        values = (
            plays[plays["play_type"] == play_type]
            .groupby(["game_id", "posteam"])["epa"]
            .mean().rename(metric).reset_index()
            .rename(columns={"posteam": "team"})
        )

        offense = offense.merge(
            values,
            on=["game_id", "team"],
            how="left",
            validate="one_to_one"
        )

    defense = plays.groupby(
        ["game_id", "defteam"]
    ).agg(
        def_epa_allowed=("epa", "mean"),
        def_success_allowed=("success", "mean"),
        def_turnovers_forced=("turnover_event", "sum")
    ).reset_index().rename(
        columns={"defteam": "team"}
    )

    for play_type, metric in [
        ("pass", "def_pass_epa_allowed"),
        ("run", "def_rush_epa_allowed")
    ]:
        values = (
            plays[plays["play_type"] == play_type]
            .groupby(["game_id", "defteam"])["epa"]
            .mean().rename(metric).reset_index()
            .rename(columns={"defteam": "team"})
        )

        defense = defense.merge(
            values,
            on=["game_id", "team"],
            how="left",
            validate="one_to_one"
        )

    metrics = offense.merge(
        defense,
        on=["game_id", "team"],
        validate="one_to_one"
    )

    metrics["opponent"] = metrics.apply(
        lambda row: (
            plays.loc[
                (plays["game_id"] == row["game_id"]) &
                (plays["posteam"] == row["team"]),
                "defteam"
            ].iloc[0]
        ),
        axis=1
    )

    return metrics.sort_values(
        ["week", "game_id", "team"]
    ).reset_index(drop=True)
