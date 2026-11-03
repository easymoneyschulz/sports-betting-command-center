"""Fetch free PropLine NBA player-points odds, without publishing model picks.

Requires PROPLINE_API_KEY in GitHub Actions secrets. Never logs credentials.
One bulk request for the whole NBA slate. Saves only two-sided, matched
Over/Under quotes and their source timestamps. No synthetic odds.
"""
import os
from pathlib import Path
import pandas as pd
import requests

API = "https://api.prop-line.com/v1/sports/basketball_nba/odds"
DEST = Path(__file__).resolve().parents[1] / "public_data" / "nba_v2_propline_odds.csv"
COLS = ["event_id", "commence_time", "home_team", "away_team", "player_name",
        "sportsbook", "market_line", "over_price", "under_price", "odds_timestamp_utc"]


def fetch():
    key = os.environ.get("PROPLINE_API_KEY")
    if not key:
        raise RuntimeError("Missing PROPLINE_API_KEY Actions secret")
    response = requests.get(API, headers={"X-API-Key": key},
                            params={"markets": "player_points", "bookmakers": "draftkings,fanduel,bovada,betmgm,betrivers"},
                            timeout=45)
    response.raise_for_status()
    events = response.json()
    if isinstance(events, dict):
        events = events.get("events", events.get("data", []))
    if not isinstance(events, list):
        raise ValueError("Unexpected PropLine response format")
    rows = []
    for event in events:
        for book in event.get("bookmakers", []):
            for market in book.get("markets", []):
                if market.get("key") != "player_points" or market.get("period"):
                    continue
                pairs = {}
                for outcome in market.get("outcomes", []):
                    side = outcome.get("name")
                    player = str(outcome.get("description") or "").strip()
                    point = outcome.get("point")
                    if side not in ("Over", "Under") or not player or point is None:
                        continue
                    try:
                        line = float(point)
                        price = int(outcome["price"])
                    except (ValueError, TypeError, KeyError):
                        continue
                    pairs.setdefault((player, line), {})[side] = price
                for (player, line), sides in pairs.items():
                    if "Over" not in sides or "Under" not in sides:
                        continue
                    rows.append({
                        "event_id": str(event.get("id", "")),
                        "commence_time": event.get("commence_time"),
                        "home_team": event.get("home_team"),
                        "away_team": event.get("away_team"),
                        "player_name": player,
                        "sportsbook": book.get("key"),
                        "market_line": line,
                        "over_price": sides["Over"],
                        "under_price": sides["Under"],
                        "odds_timestamp_utc": market.get("last_update"),
                    })
    # Sanity check: one event must not contain props from unrelated teams.
    # Reject suspicious slates instead of silently publishing them as verified.
    known_team_players = {
        "LeBron James": "Los Angeles Lakers",
        "Jaylen Brown": "Boston Celtics",
        "Tyrese Maxey": "Philadelphia 76ers",
        "Cade Cunningham": "Detroit Pistons",
    }
    for quote in rows:
        expected_team = known_team_players.get(quote["player_name"])
        if expected_team and expected_team not in (quote["home_team"], quote["away_team"]):
            raise ValueError(
                "PropLine matchup integrity failed: player "
                + quote["player_name"] + " is not on either team for event "
                + quote["event_id"] + ". No new odds will be published."
            )
    if not rows:
        print("No two-sided NBA player-points odds returned; preserving prior snapshot")
        return
    data = pd.DataFrame(rows, columns=COLS)
    if data["event_id"].eq("").any() or data["odds_timestamp_utc"].isna().any():
        raise ValueError("Odds missing event identity or timestamp")
    data = data.drop_duplicates(subset=["event_id", "player_name", "sportsbook", "market_line"])
    DEST.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(DEST, index=False)
    print(f"Saved {len(data)} verified two-sided player-point quotes for {data.event_id.nunique()} games")


if __name__ == "__main__":
    fetch()
