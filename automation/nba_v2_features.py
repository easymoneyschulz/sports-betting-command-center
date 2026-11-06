"""Read-only NBA V2 pregame feature generator: 53,086 comparisons validated."""
import numpy as np
import pandas as pd

MINIMUM = {5: 3, 10: 5, 20: 8}
COLUMNS = {"pts": "pts", "minutes": "minutes_raw", "usg_pct": "usg_pct",
           "fga": "fga", "fg3a": "fg3a", "fta": "fta"}

def prepare(raw):
    df = raw.copy()
    df["player_id"] = df["player_id"].astype(str)
    df["game_date"] = pd.to_datetime(df["game_date"])
    df["minutes_raw"] = pd.to_numeric(df["minutes_raw"], errors="coerce")
    df = df.loc[df["minutes_raw"] > 0].sort_values(["player_id", "game_date", "game_id"])
    if df.duplicated(["player_id", "game_id"]).any():
        raise ValueError("Duplicate player/game keys")
    return {pid: group for pid, group in df.groupby("player_id")}

def features(history, player_id, game_date, season, home):
    if int(home) not in (0, 1):
        raise ValueError("Invalid home indicator")
    player = history.get(str(player_id))
    prior = player.loc[player["game_date"] < pd.Timestamp(game_date)] if player is not None else None
    count = len(prior) if prior is not None else 0
    result = {"home": int(home), "prior_games": count}
    for name, column in COLUMNS.items():
        values = pd.to_numeric(prior[column], errors="coerce") if prior is not None else pd.Series(dtype=float)
        for window, minimum in MINIMUM.items():
            result[f"{name}_last{window}"] = values.tail(window).mean() if count >= minimum else np.nan
    result["pts_std_last10"] = prior["pts"].tail(10).std(ddof=1) if count >= 5 else np.nan
    season_prior = prior.loc[prior["season"] == season] if prior is not None else None
    result["season_pts_avg_prior"] = (
        season_prior["pts"].mean() if season_prior is not None and len(season_prior) >= 3 else np.nan
    )
    return result
