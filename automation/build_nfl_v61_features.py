
from pathlib import Path
import pandas as pd
import numpy as np

from build_nfl_v61_live_data import (
    download_pbp, build_team_metrics
)
from build_nfl_v61_ratings import build_ratings

SCHEDULE_URL = (
    "https://github.com/nflverse/nflverse-data/"
    "releases/download/schedules/games.csv"
)

def build_features(season, target_week):
    schedule = pd.read_csv(SCHEDULE_URL)

    games = schedule[
        (schedule["season"] == season) &
        (schedule["game_type"] == "REG")
    ].copy()

    games["gameday"] = pd.to_datetime(games["gameday"])

    target = games[
        games["week"] == target_week
    ].copy()

    if target.empty:
        raise ValueError("No games found for requested week")

    pbp = download_pbp(season)

    metrics = build_team_metrics(
        pbp, season, target_week
    )

    ratings = build_ratings(
        metrics, season, target_week
    )

    team_games = pd.concat([
        games[["game_id", "gameday", "home_team"]]
            .rename(columns={"home_team": "team"}),
        games[["game_id", "gameday", "away_team"]]
            .rename(columns={"away_team": "team"})
    ], ignore_index=True)

    team_games = team_games.sort_values(
        ["team", "gameday", "game_id"]
    )

    team_games["previous_game"] = (
        team_games.groupby("team")["gameday"].shift(1)
    )

    team_games["days_since_previous"] = (
        team_games["gameday"]
        - team_games["previous_game"]
    ).dt.days

    rest = team_games[
        ["game_id", "team", "days_since_previous"]
    ]

    rows = []

    rating_features = [
        c for c in ratings.columns
        if c.startswith("pregame_")
    ]

    for _, game in target.iterrows():
        home = ratings[
            ratings["team"] == game["home_team"]
        ]

        away = ratings[
            ratings["team"] == game["away_team"]
        ]

        if len(home) != 1 or len(away) != 1:
            raise ValueError(
                "Missing team ratings: "
                f"{game['away_team']} at {game['home_team']}"
            )

        home = home.iloc[0]
        away = away.iloc[0]

        home_rest = rest[
            (rest["game_id"] == game["game_id"]) &
            (rest["team"] == game["home_team"])
        ]["days_since_previous"]

        away_rest = rest[
            (rest["game_id"] == game["game_id"]) &
            (rest["team"] == game["away_team"])
        ]["days_since_previous"]

        if home_rest.empty or away_rest.empty:
            raise ValueError("Missing rest data")

        row = {
            "game_id": game["game_id"],
            "season": season,
            "week": target_week,
            "gameday": game["gameday"].strftime(
                "%Y-%m-%d"
            ),
            "gametime": game["gametime"],
            "away_team": game["away_team"],
            "home_team": game["home_team"],
            "rest_advantage": (
                home_rest.iloc[0] - away_rest.iloc[0]
            )
        }

        for feature in rating_features:
            row[f"diff_{feature}"] = (
                home[feature] - away[feature]
            )

        rows.append(row)

    return pd.DataFrame(rows).sort_values(
        ["gameday", "gametime", "game_id"]
    ).reset_index(drop=True)
