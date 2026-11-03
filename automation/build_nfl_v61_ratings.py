
import numpy as np
import pandas as pd

BASE_STATS = ['off_epa', 'off_success', 'pass_rate', 'pass_epa', 'rush_epa', 'turnovers', 'def_epa_allowed', 'def_success_allowed', 'def_pass_epa_allowed', 'def_rush_epa_allowed', 'def_turnovers_forced']
ADJUSTED_STATS = ['adjusted_off_epa', 'adjusted_def_epa_allowed']

def build_ratings(metrics, target_season, target_week):
    data = metrics.copy()

    required = [
        "game_id", "season", "week",
        "team", "opponent"
    ] + BASE_STATS

    missing = set(required) - set(data.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    data = data[
        (data["season"] == target_season) &
        (data["week"] < target_week)
    ].copy()

    if data.empty:
        raise ValueError("No prior-game metrics available")

    if data.duplicated(
        ["season", "week", "team"]
    ).any():
        raise ValueError("Duplicate team-week records")

    data = data.sort_values(
        ["week", "game_id", "team"]
    ).reset_index(drop=True)

    data["prior_league_epa"] = np.nan
    data["prior_weekly_off_epa"] = np.nan
    data["prior_weekly_def_epa"] = np.nan

    for week in sorted(data["week"].unique()):
        prior = data[data["week"] < week]

        if prior.empty:
            continue

        # ORIGINAL V6.1 CONVENTION:
        # Equal weight to each completed week's EPA mean.
        league_epa = (
            prior.groupby("week")["off_epa"]
            .mean()
            .mean()
        )

        off_by_team = prior.groupby("team")[
            "off_epa"
        ].mean()

        def_by_team = prior.groupby("team")[
            "def_epa_allowed"
        ].mean()

        mask = data["week"] == week

        data.loc[mask, "prior_league_epa"] = league_epa

        data.loc[mask, "prior_weekly_off_epa"] = (
            data.loc[mask, "team"].map(off_by_team)
        )

        data.loc[mask, "prior_weekly_def_epa"] = (
            data.loc[mask, "team"].map(def_by_team)
        )

    opponent_lookup = data[
        ["game_id", "team",
         "prior_weekly_off_epa",
         "prior_weekly_def_epa"]
    ].rename(columns={
        "team": "opponent",
        "prior_weekly_off_epa":
            "opponent_prior_off_epa",
        "prior_weekly_def_epa":
            "opponent_prior_def_epa"
    })

    data = data.merge(
        opponent_lookup,
        on=["game_id", "opponent"],
        how="left",
        validate="one_to_one"
    )

    data["adjusted_off_epa"] = (
        data["off_epa"]
        - data["opponent_prior_def_epa"]
        + data["prior_league_epa"]
    ).fillna(data["off_epa"])

    data["adjusted_def_epa_allowed"] = (
        data["def_epa_allowed"]
        - data["opponent_prior_off_epa"]
        + data["prior_league_epa"]
    ).fillna(data["def_epa_allowed"])

    rows = []

    for team, history in data.groupby("team"):
        history = history.sort_values(
            ["week", "game_id"]
        )

        row = {
            "season": target_season,
            "week": target_week,
            "team": team,
            "prior_games": len(history)
        }

        for stat in BASE_STATS + ADJUSTED_STATS:
            for window in (3, 8):
                row[f"pregame_{stat}_last{window}"] = (
                    history[stat].tail(window).mean()
                )

        rows.append(row)

    return pd.DataFrame(rows).sort_values(
        "team"
    ).reset_index(drop=True)
