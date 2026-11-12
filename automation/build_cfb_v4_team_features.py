"""Build reproducible pregame CFB V4 team form from ESPN collector exports.

Historical games are sorted by kickoff; every team snapshot uses only games
completed before its target kickoff. Does not fabricate missing market odds.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "automation/data/cfb"
FEATURES = ROOT / "automation/models/cfb_v4_features.json"

def fraction(value):
    try:
        a, b = str(value).replace("-", "/").split("/", 1)
        return float(a) / float(b) if float(b) else np.nan
    except (ValueError, TypeError):
        return np.nan

def second(value):
    try:
        return float(str(value).replace("-", "/").split("/", 1)[-1])
    except (ValueError, TypeError):
        return np.nan

def possession(value):
    try:
        minutes, seconds = str(value).split(":")
        return float(minutes) + float(seconds) / 60
    except (ValueError, TypeError):
        return np.nan

def build():
    schedule = pd.read_csv(DATA / "cfb_schedules_2026.csv", dtype={"game_id": str, "home_id": str, "away_id": str})
    box = pd.read_csv(DATA / "team_box_2026.csv", dtype={"game_id": str, "team_id": str})
    schedule["kickoff"] = pd.to_datetime(schedule["start_date"], utc=True)
    schedule["completed"] = schedule["completed"].astype(str).str.lower().eq("true")
    assert schedule.game_id.is_unique, "Duplicate schedule games"
    assert not box.duplicated(["game_id", "team_id"]).any(), "Duplicate box score team-game rows"
    for field in ["totalYards", "netPassingYards", "rushingYards", "yardsPerPass",
                  "yardsPerRushAttempt", "turnovers", "interceptions", "fumblesLost"]:
        box[field] = pd.to_numeric(box[field], errors="coerce")
    box["third_down_rate"] = box["thirdDownEff"].map(fraction)
    box["fourth_down_pct"] = box["fourthDownEff"].map(fraction)
    box["completion_pct"] = box["completionAttempts"].map(fraction)
    box["penalty_yards"] = box["totalPenaltiesYards"].map(second)
    box["possession_minutes"] = box["possessionTime"].map(possession)
    rows = []
    for game in schedule.loc[schedule.completed].itertuples(index=False):
        for side in ("home", "away"):
            team = str(getattr(game, side + "_id"))
            opponent = str(getattr(game, ("away" if side == "home" else "home") + "_id"))
            own = box[(box.game_id == game.game_id) & (box.team_id == team)]
            opp = box[(box.game_id == game.game_id) & (box.team_id == opponent)]
            if len(own) != 1 or len(opp) != 1:
                continue
            own, opp = own.iloc[0], opp.iloc[0]
            scored = float(getattr(game, side + "_score"))
            allowed = float(getattr(game, ("away" if side == "home" else "home") + "_score"))
            row = {"game_id": game.game_id, "kickoff": game.kickoff, "team_id": team,
                   "opponent_id": opponent, "points_scored": scored, "points_allowed": allowed,
                   "margin": scored - allowed, "yards_allowed": opp.totalYards,
                   "passing_allowed": opp.netPassingYards, "rushing_allowed": opp.rushingYards,
                   "turnovers_forced": opp.turnovers}
            for field in ["totalYards", "netPassingYards", "rushingYards", "yardsPerPass",
                          "yardsPerRushAttempt", "turnovers", "third_down_rate",
                          "fourth_down_pct", "completion_pct", "penalty_yards",
                          "possession_minutes", "interceptions", "fumblesLost"]:
                row[field] = own[field]
            rows.append(row)
    hist = pd.DataFrame(rows).sort_values(["kickoff", "game_id"])
    if len(hist) < 500:
        raise ValueError("Insufficient validated historical team-game rows")
    history = {str(team): group.sort_values("kickoff").reset_index(drop=True)
               for team, group in hist.groupby("team_id")}
    # Exclude target kickoff and later games: protects against look-ahead leakage.
    def team_form(team, cutoff):
        h = history.get(str(team))
        if h is None:
            return None
        h = h.loc[h.kickoff < cutoff]
        if len(h) < 3:
            return None
        recent = h.tail(5)
        out = {"prior_games": len(h), "pregame_margin_last5": recent.margin.mean(),
               "pregame_points_scored_last5": recent.points_scored.mean()}
        mapping = {"totalYards": "totalYards", "netPassingYards": "netPassingYards",
                   "rushingYards": "rushingYards", "yardsPerPass": "yardsPerPass",
                   "yardsPerRushAttempt": "yardsPerRushAttempt", "turnovers": "turnovers",
                   "third_down_rate": "third_down_rate", "yards_allowed": "yards_allowed",
                   "passing_allowed": "passing_allowed", "rushing_allowed": "rushing_allowed",
                   "turnovers_forced": "turnovers_forced", "points_allowed": "points_allowed",
                   "completion_pct": "completion_pct", "fourth_down_pct": "fourth_down_pct",
                   "penalty_yards": "penalty_yards", "possession_minutes": "possession_minutes",
                   "interceptions_thrown": "interceptions", "fumbles_lost": "fumblesLost"}
        for dest, src in mapping.items():
            out["pregame_" + dest] = recent[src].mean()
        # Opponent-strength estimate: opponents' own earlier margins, never future results.
        sos = []
        for g in recent.itertuples(index=False):
            opp = history.get(str(g.opponent_id))
            if opp is None:
                continue
            earlier = opp.loc[opp.kickoff < g.kickoff].tail(5)
            if len(earlier):
                sos.append(float(earlier.margin.mean()))
        out["pregame_sos_last5"] = float(np.mean(sos)) if sos else np.nan
        out["pregame_adjusted_margin"] = out["pregame_margin_last5"] + out["pregame_sos_last5"]
        return out
    upcoming = schedule.loc[~schedule.completed & (schedule.kickoff > pd.Timestamp.now(tz="UTC"))].copy()
    records = []
    for g in upcoming.itertuples(index=False):
        home, away = team_form(g.home_id, g.kickoff), team_form(g.away_id, g.kickoff)
        if home is None or away is None:
            continue
        record = {"game_id": g.game_id, "verified_kickoff": g.kickoff.isoformat(),
                  "home_team": g.home_team, "away_team": g.away_team,
                  "home_id": g.home_id, "away_id": g.away_id,
                  "neutral_site_feature": int(str(g.neutral_site).lower() == "true"),
                  "conference_game_feature": int(str(g.conference_game).lower() == "true")}
        for key in home:
            record["diff_" + key] = home[key] - away[key]
        records.append(record)
    out = pd.DataFrame(records)
    # market_margin and over_under deliberately not supplied: require live sportsbook odds.
    expected = json.loads(FEATURES.read_text())
    present = [f for f in expected if f in out.columns]
    missing = [f for f in expected if f not in out.columns]
    DATA.mkdir(parents=True, exist_ok=True)
    out.to_csv(DATA / "cfb_v4_team_features_2026.csv", index=False)
    print(json.dumps({"historical_team_games": len(hist), "upcoming_teams_covered": len(out),
                      "present_features": len(present), "missing_features": missing,
                      "note": "Recent-form and opponent-pre-game-margin calculations follow notebook Steps 85-87; market fields require verified odds."}, indent=2))
    if len(out) == 0:
        raise RuntimeError("No upcoming matchups with sufficient historical data")
    return out

if __name__ == "__main__":
    build()
