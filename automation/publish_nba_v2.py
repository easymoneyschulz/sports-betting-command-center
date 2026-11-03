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
LINES = ROOT / "nba_v2_verified_lines.csv"
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
        lines = pd.read_csv(LINES)
        if not LINE_COLS.issubset(lines.columns):
            raise ValueError("Verified lines missing required columns")
        if lines.duplicated(["game_id", "player_id"]).any():
            raise ValueError("Ambiguous sportsbook lines: one line per player/game required")
        lines["market_line"] = pd.to_numeric(lines["market_line"], errors="coerce")
        if lines["market_line"].isna().any():
            raise ValueError("Invalid sportsbook points line")
        joined = src[["game_id", "player_id"]].merge(
            lines[["game_id", "player_id", "market_line"]],
            on=["game_id", "player_id"], how="left", validate="one_to_one")
        out["sportsbook_points_line"] = joined["market_line"].to_numpy()
        out["market_line"] = joined["market_line"].to_numpy()
        edge = out["prediction"] - pd.to_numeric(out["market_line"], errors="coerce")
        out["points_edge"] = edge
        out["higher_lower"] = edge.map(
            lambda e: "WAIT" if pd.isna(e) else "OVER" if e > 0 else "UNDER" if e < 0 else "PASS")
    ROOT.mkdir(parents=True, exist_ok=True)
    out.to_csv(DEST, index=False)
    print(f"Published {len(out)} ORIGINAL V2 projections; {out['market_line'].notna().sum()} verified lines")


if __name__ == "__main__":
    main()
