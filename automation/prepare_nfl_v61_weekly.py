#!/usr/bin/env python3
"""
Prepare NFL V6.1 weekly feature snapshots.

Research-only. Does not retrieve sportsbook odds,
run betting selections, or publish predictions.
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from build_nfl_v61_features import build_features

SCHEDULE_URL = (
    "https://github.com/nflverse/nflverse-data/"
    "releases/download/schedules/games.csv"
)

def select_week(schedule, now):
    games = schedule[
        (schedule["game_type"] == "REG")
    ].copy()

    games["kickoff_utc"] = pd.to_datetime(
        games["gameday"].astype(str)
        + " "
        + games["gametime"].astype(str),
        errors="coerce",
        utc=True
    )

    # The nflverse gametime field is Eastern local time.
    # Convert using America/New_York to respect DST.
    naive = pd.to_datetime(
        games["gameday"].astype(str)
        + " "
        + games["gametime"].astype(str),
        errors="coerce"
    )

    games["kickoff_utc"] = (
        naive.dt.tz_localize(
            "America/New_York",
            ambiguous="NaT",
            nonexistent="NaT"
        ).dt.tz_convert("UTC")
    )

    games = games[
        games["kickoff_utc"].notna()
        & (games["kickoff_utc"] > now)
    ].sort_values("kickoff_utc")

    if games.empty:
        raise ValueError("No future regular-season NFL games found")

    first = games.iloc[0]
    return int(first["season"]), int(first["week"])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--season", type=int)
    parser.add_argument("--week", type=int)
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    schedule = pd.read_csv(SCHEDULE_URL)

    if args.season is not None or args.week is not None:
        if args.season is None or args.week is None:
            raise ValueError("Provide both --season and --week")
        season, week = args.season, args.week
    else:
        season, week = select_week(schedule, now)

    features = build_features(season, week)

    games = schedule[
        (schedule["season"] == season)
        & (schedule["week"] == week)
        & (schedule["game_type"] == "REG")
    ].copy()

    naive = pd.to_datetime(
        games["gameday"].astype(str)
        + " "
        + games["gametime"].astype(str),
        errors="coerce"
    )

    games["kickoff_utc"] = (
        naive.dt.tz_localize(
            "America/New_York",
            ambiguous="NaT",
            nonexistent="NaT"
        ).dt.tz_convert("UTC")
    )

    if games["kickoff_utc"].isna().any():
        raise ValueError("Invalid kickoff time in schedule")

    upcoming_ids = set(
        games.loc[
            games["kickoff_utc"] > now,
            "game_id"
        ]
    )

    features["run_timestamp_utc"] = now.isoformat()
    features["game_status"] = features["game_id"].apply(
        lambda x: "UPCOMING" if x in upcoming_ids else "STARTED"
    )
    features["publication_status"] = "NOT_PUBLISHED"
    features["odds_status"] = "NOT_VERIFIED"

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / (
        f"nfl_v61_{season}_week{week}_{stamp}_features.csv"
    )

    if path.exists():
        raise FileExistsError(path)

    features.to_csv(path, index=False)

    print("=" * 65)
    print("NFL V6.1 WEEKLY RESEARCH SNAPSHOT")
    print("=" * 65)
    print("Season:", season)
    print("Week:", week)
    print("Games:", len(features))
    print("Upcoming:", (features["game_status"] == "UPCOMING").sum())
    print("Started:", (features["game_status"] == "STARTED").sum())
    print("Snapshot:", path)
    print("Odds: NOT VERIFIED")
    print("Publishing: DISABLED")

if __name__ == "__main__":
    main()
