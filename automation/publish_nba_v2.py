"""Validate and publish NBA V2 points snapshots without altering model predictions.

Input: public_data/nba_v2_source_predictions.csv (exported from original V2).
Optional market file: public_data/nba_v2_verified_lines.csv
No lines => projection only; no betting signal.
"""
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

ROOT = Path(__file__).resolve().parents[1] / "public_data"
SOURCE = ROOT / "nba_v2_source_predictions.csv"
LINES = ROOT / "nba_v2_propline_odds.csv"
DEST = ROOT / "nba_v2_latest_player_points.csv"
REQUIRED = {"game_date", "game_id", "player_id", "player_name", "opponent", "v2_projection"}
LINE_COLS = {"game_id", "player_id", "sportsbook", "market_line", "odds_timestamp_utc"}


def main():
    if not SOURCE.exists():
        print("NO ORIGINAL V2 SOURCE: leaving published snapshot unchanged.")
        return
    src = pd.read_csv(SOURCE)
    if src.empty or not REQUIRED.issubset(src.columns):
        raise ValueError("Original V2 source is empty or missing required columns")
    # Never republish an old original-model snapshot as if it were today's picks.
    current_day = datetime.now(timezone.utc).astimezone(
        __import__("zoneinfo").ZoneInfo("America/Chicago")
    ).date()
    game_days = pd.to_datetime(src["game_date"], errors="coerce").dt.date
    if game_days.isna().any():
        raise ValueError("Invalid game dates in NBA V2 source")
    if not any(day >= current_day for day in game_days):
        print("NBA V2 source contains only past games; leaving current publication unchanged.")
        return
    src = src[game_days >= current_day].copy()
    if src.duplicated(["game_id", "player_id"]).any():
        raise ValueError("Duplicate game/player projections")
    src["v2_projection"] = pd.to_numeric(src["v2_projection"], errors="coerce")
    if src["v2_projection"].isna().any():
        raise ValueError("Non-numeric projections")
    out = pd.DataFrame({
        "model": "NBA V2",
        "test_type": "FORWARD_PAPER",
        "event_id": src["game_id"].astype(str) + "_" + src["player_id"].astype(str),
        "season": pd.to_datetime(src["game_date"], utc=True).dt.year,
        "selection": src["player_name"],
        "prediction": src["v2_projection"],
        "market_line": pd.NA,
        "actual": src.get("actual_points", pd.Series(index=src.index, dtype=float)),
        "result": src.get("result_status", pd.Series("PENDING", index=src.index)),
        "game_date": src["game_date"],
        "opponent": src["opponent"],
        "sportsbook_points_line": pd.NA,
        "higher_lower": "WAIT",
        "points_edge": pd.NA,
    })
    if LINES.exists():
        import unicodedata
        from zoneinfo import ZoneInfo

        lines = pd.read_csv(LINES)
        needed = {"player_name", "commence_time", "home_team", "away_team",
                  "sportsbook", "market_line", "odds_timestamp_utc",
                  "over_price", "under_price"}
        if not needed.issubset(lines.columns):
            raise ValueError("PropLine odds missing required columns")

        def normalized(value):
            value = unicodedata.normalize("NFKD", str(value))
            return "".join(ch for ch in value if ch.isalnum()).casefold()

        now = pd.Timestamp.now(tz="UTC")
        lines["tip"] = pd.to_datetime(lines["commence_time"], utc=True, errors="coerce")
        lines["quoted"] = pd.to_datetime(lines["odds_timestamp_utc"], utc=True, errors="coerce")
        lines["game_date"] = lines["tip"].dt.tz_convert(ZoneInfo("America/Chicago")).dt.strftime("%Y-%m-%d")
        lines["name_key"] = lines["player_name"].map(normalized)
        lines["market_line"] = pd.to_numeric(lines["market_line"], errors="coerce")
        lines = lines[
            lines["tip"].gt(now)
            & lines["quoted"].le(now)
            & lines["quoted"].ge(now - pd.Timedelta(hours=24))
            & lines["market_line"].notna()
            & lines["over_price"].notna()
            & lines["under_price"].notna()
        ].copy()
        # Match on date, player and opponent; never join an unrelated event.
        # Team names are mapped explicitly rather than guessed from player identity.
        team_codes = {
            "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
            "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
            "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
            "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
            "Los Angeles Clippers": "LAC", "LA Clippers": "LAC",
            "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM",
            "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
            "New Orleans Pelicans": "NOP", "New York Knicks": "NYK",
            "Oklahoma City Thunder": "OKC", "Orlando Magic": "ORL",
            "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
            "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC",
            "San Antonio Spurs": "SAS", "Toronto Raptors": "TOR",
            "Utah Jazz": "UTA", "Washington Wizards": "WAS"
        }
        lines["home_code"] = lines["home_team"].map(team_codes)
        lines["away_code"] = lines["away_team"].map(team_codes)
        src_keys = src[["game_date", "player_name", "opponent"]].copy()
        src_keys["name_key"] = src_keys["player_name"].map(normalized)
        src_keys["game_date"] = pd.to_datetime(src_keys["game_date"]).dt.strftime("%Y-%m-%d")
        src_keys["row_number"] = range(len(src_keys))
        matched = src_keys.merge(lines, on=["game_date", "name_key"], how="inner")
        matched = matched[
            (matched["opponent"] == matched["home_code"])
            | (matched["opponent"] == matched["away_code"])
        ].copy()
        # Multiple books/lines are legitimate. Pick a deterministic quote,
        # preferring newest timestamp and then sportsbook alphabetically.
        matched = matched.sort_values(
            ["quoted", "sportsbook"], ascending=[False, True]
        ).drop_duplicates("row_number")
        for _, quote in matched.iterrows():
            idx = out.index[int(quote["row_number"])]
            line = float(quote["market_line"])
            edge = float(out.at[idx, "prediction"]) - line
            out.at[idx, "market_line"] = line
            out.at[idx, "sportsbook_points_line"] = line
            out.at[idx, "points_edge"] = edge
            out.at[idx, "higher_lower"] = (
                "OVER" if edge > 0 else "UNDER" if edge < 0 else "PASS"
            )
        print(f"Matched {len(matched)} current, opponent-verified PropLine quotes")
    ROOT.mkdir(parents=True, exist_ok=True)
    out.to_csv(DEST, index=False)
    print(f"Published {len(out)} ORIGINAL V2 projections; {out['market_line'].notna().sum()} verified lines")


if __name__ == "__main__":
    main()
