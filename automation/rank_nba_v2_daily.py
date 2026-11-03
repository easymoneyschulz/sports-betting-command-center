"""Daily NBA V2 top-five paper selection from validated V2 projections and live odds.

Never creates model projections. Requires the original model's daily source export.
One player per selection, no forced picks, and no fabricated sportsbook prices.
"""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1] / "public_data"
SOURCE = ROOT / "nba_v2_source_predictions.csv"
REBUILT = ROOT / "nba_daily_active_projections.csv"
ODDS = ROOT / "nba_v2_propline_odds.csv"
OUTPUT = ROOT / "nba_v2_daily_top5.csv"
MIN_EDGE = 3.0
MAX_ODDS_AGE_HOURS = 24


def implied_prob(american):
    american = float(american)
    return -american / (100 - american) if american < 0 else 100 / (100 + american)


def main():
    if not ODDS.exists():
        print("No original daily NBA V2 projection source or odds; not manufacturing picks.")
        return
    original = pd.read_csv(SOURCE) if SOURCE.exists() else pd.DataFrame()
    today = pd.Timestamp.now(tz="UTC").tz_convert("America/Chicago").date()
    target_date = today
    if ODDS.exists():
        odds_dates = pd.to_datetime(pd.read_csv(ODDS)["commence_time"], utc=True, errors="coerce").dt.tz_convert("America/Chicago").dt.date
        upcoming_dates = sorted(d for d in odds_dates.dropna().unique() if d >= today)
        if upcoming_dates:
            target_date = upcoming_dates[0]
    if not original.empty:
        original_future = sorted(d for d in pd.to_datetime(original["game_date"], errors="coerce").dt.date.dropna().unique() if d >= today)
        if original_future:
            target_date = original_future[0]
    # Prefer full-slate separately labeled rolling projections for screening.
    # The original frozen V2 export is never overwritten or presented as rebuilt.
    rebuilt = pd.read_csv(REBUILT) if REBUILT.exists() else pd.DataFrame()
    if not rebuilt.empty:
        rebuilt_dates = pd.to_datetime(rebuilt["game_date"], errors="coerce").dt.date
        rebuilt = rebuilt[rebuilt_dates == target_date].copy()
    if not rebuilt.empty:
        src = rebuilt
        model_label = "ROLLING REBUILD V0 (NOT NBA V2)"
    else:
        if not original.empty:
            original = original[pd.to_datetime(original["game_date"], errors="coerce").dt.date == target_date]
        if original.empty:
            print("No same-date original or rolling projections; no picks.")
            return
        src = original
        model_label = "NBA V2 ORIGINAL"
    odds = pd.read_csv(ODDS)
    required = {"game_date", "player_name", "v2_projection"}
    if src.empty or not required.issubset(src.columns):
        raise ValueError("NBA V2 source lacks required projection columns")
    src["game_date"] = pd.to_datetime(src["game_date"], errors="coerce").dt.date
    src = src[src["game_date"] == target_date].copy()
    if src.empty:
        print("No original V2 projections for today; preserving previous paper selections.")
        return
    src["v2_projection"] = pd.to_numeric(src["v2_projection"], errors="coerce")
    src = src.dropna(subset=["v2_projection"])
    if src["player_name"].duplicated().any():
        raise ValueError("Ambiguous duplicate player projections")
    odds["commence_time"] = pd.to_datetime(odds["commence_time"], utc=True, errors="coerce")
    odds["odds_timestamp_utc"] = pd.to_datetime(odds["odds_timestamp_utc"], utc=True, errors="coerce")
    now = pd.Timestamp.now(tz="UTC")
    odds = odds[(odds["commence_time"].dt.tz_convert("America/Chicago").dt.date == target_date)
                & (odds["commence_time"] > now)
                & (odds["odds_timestamp_utc"] <= now)
                & (odds["odds_timestamp_utc"] >= now - pd.Timedelta(hours=MAX_ODDS_AGE_HOURS))].copy()
    for col in ("market_line", "over_price", "under_price"):
        odds[col] = pd.to_numeric(odds[col], errors="coerce")
    odds = odds.dropna(subset=["market_line", "over_price", "under_price"])
    # Names alone aren't sufficient when the source has an opponent: check the event teams.
    merged = odds.merge(src, on="player_name", how="inner", validate="many_to_one")
    if "opponent" in merged:
        # Accept standard team abbreviations; never match a player to an unrelated game.
        codes = {"Philadelphia 76ers":"PHI","Detroit Pistons":"DET","Boston Celtics":"BOS","Los Angeles Lakers":"LAL","Sacramento Kings":"SAC","Washington Wizards":"WAS","Dallas Mavericks":"DAL","Toronto Raptors":"TOR","Phoenix Suns":"PHX","Oklahoma City Thunder":"OKC","Denver Nuggets":"DEN","New York Knicks":"NYK","Brooklyn Nets":"BKN","Atlanta Hawks":"ATL","Chicago Bulls":"CHI","Charlotte Hornets":"CHA","Cleveland Cavaliers":"CLE","Golden State Warriors":"GSW","Houston Rockets":"HOU","Indiana Pacers":"IND","LA Clippers":"LAC","Memphis Grizzlies":"MEM","Miami Heat":"MIA","Milwaukee Bucks":"MIL","Minnesota Timberwolves":"MIN","New Orleans Pelicans":"NOP","Orlando Magic":"ORL","Portland Trail Blazers":"POR","San Antonio Spurs":"SAS","Utah Jazz":"UTA"}
        def valid_match(row):
            opponent = str(row["opponent"]).strip().casefold()
            return any(opponent in (str(t).casefold(), codes.get(str(t), "").casefold())
                       for t in (row["home_team"], row["away_team"]))
        merged = merged[merged.apply(valid_match, axis=1)]
    if merged.empty:
        print("No verified matching games/players; no new selections.")
        return
    merged["edge"] = merged["v2_projection"] - merged["market_line"]
    merged["side"] = np.where(merged["edge"] > 0, "OVER", "UNDER")
    merged["price"] = np.where(merged["edge"] > 0, merged["over_price"], merged["under_price"])
    merged["absolute_edge"] = merged["edge"].abs()
    merged = merged[merged["absolute_edge"] >= MIN_EDGE].copy()
    merged["implied_probability"] = merged["price"].map(implied_prob)
    # This is a transparent screening score, NOT a calibrated win probability.
    merged["screening_score"] = merged["absolute_edge"] / np.sqrt(1 + merged["implied_probability"])
    merged = merged.sort_values(["screening_score", "absolute_edge", "odds_timestamp_utc"],
                                ascending=[False, False, False])
    merged = merged.drop_duplicates("player_name").head(5)
    cols = ["game_date", "player_name", "opponent", "v2_projection", "market_line",
            "edge", "side", "price", "sportsbook", "screening_score", "odds_timestamp_utc"]
    if merged.empty:
        print("No players meet the 3-point minimum edge; no forced picks.")
        return
    merged["status"] = "PAPER"
    merged["model_version"] = model_label
    merged[cols + ["status", "model_version"]].to_csv(OUTPUT, index=False)
    print(f"Published {len(merged)} distinct NBA V2 paper leans for {target_date}")


if __name__ == "__main__":
    main()
