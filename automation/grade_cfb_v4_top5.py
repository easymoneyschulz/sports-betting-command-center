"""Grade published CFB V4 research selections from final ESPN game scores.
Does not run, retrain, or alter the frozen model. Unfinished games stay PENDING.
"""
from pathlib import Path
import io
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "public_data" / "cfb_v4_top5.csv"
OUTPUT = ROOT / "public_data" / "cfb_v4_graded.csv"

def result_for_game(game_id, side, spread):
    url = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/summary"
    response = requests.get(url, params={"event": str(game_id)}, timeout=20)
    response.raise_for_status()
    data = response.json()
    header = data.get("header", {})
    competitions = header.get("competitions") or []
    if not competitions:
        return "PENDING", None, None
    comp = competitions[0]
    status = comp.get("status") or {}
    if not status.get("type", {}).get("completed", False):
        return "PENDING", None, None
    competitors = comp.get("competitors") or []
    if len(competitors) != 2:
        return "PENDING", None, None
    teams = {}
    for item in competitors:
        name = item.get("team", {}).get("displayName", "")
        score = item.get("score")
        if isinstance(score, dict):
            score = score.get("displayValue", score.get("value"))
        teams[name] = float(score)
    if side not in teams:
        raise ValueError(f"Selection team {side!r} not found for ESPN game {game_id}: {list(teams)}")
    other = next(name for name in teams if name != side)
    adjusted = teams[side] - teams[other] + float(spread)
    outcome = "WIN" if adjusted > 0 else "LOSS" if adjusted < 0 else "PUSH"
    return outcome, int(teams[side]), int(teams[other])

def main():
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    picks = pd.read_csv(SOURCE, dtype={"game_id": str})
    required = {"game_id", "selected_side", "selected_spread", "decision"}
    if not required.issubset(picks.columns):
        raise ValueError("Missing required V4 top-five columns")
    if picks["game_id"].duplicated().any():
        raise ValueError("Duplicate game IDs")
    previous = pd.read_csv(OUTPUT, dtype={"game_id": str}) if OUTPUT.exists() else pd.DataFrame()
    previous_by_id = previous.set_index("game_id") if not previous.empty else None
    results = []
    for _, pick in picks.iterrows():
        game_id = str(pick["game_id"])
        try:
            outcome, scored, conceded = result_for_game(game_id, pick["selected_side"], pick["selected_spread"])
        except (requests.RequestException, ValueError, KeyError) as exc:
            print(f"ESPN lookup failed for {game_id}: {exc}")
            if previous_by_id is not None and game_id in previous_by_id.index:
                old = previous_by_id.loc[game_id]
                outcome = str(old["result"])
                scored, conceded = old["selected_score"], old["opponent_score"]
            else:
                outcome, scored, conceded = "PENDING", None, None
        row = pick.to_dict()
        row.update(result=outcome, selected_score=scored, opponent_score=conceded)
        results.append(row)
    result = pd.DataFrame(results)
    if len(result) != len(picks):
        raise AssertionError("Result row count changed")
    result.to_csv(OUTPUT, index=False)
    print(result[["game_id", "selected_side", "result"]].to_string(index=False))

if __name__ == "__main__":
    main()
