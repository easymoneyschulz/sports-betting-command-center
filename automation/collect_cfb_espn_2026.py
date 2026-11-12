"""Collect authentic 2026 FBS ESPN schedules and completed-game team box scores.
No predictions are generated; outputs are raw source data for V4 feature reconstruction.
"""
import csv
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "automation" / "data" / "cfb"
BASE = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/"

def fetch(endpoint, **params):
    url = BASE + endpoint + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "SportsBettingCommandCenter/1.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=35) as response:
                return json.load(response)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    events = {}
    for week in range(1, 17):
        payload = fetch("scoreboard", dates=2026, week=week, seasontype=2, groups=80, limit=500)
        weekly = payload.get("events", [])
        print(f"Week {week}: {len(weekly)} events")
        for event in weekly:
            events[str(event["id"])] = event
        time.sleep(.15)
    if len(events) < 300:
        raise RuntimeError(f"Suspiciously incomplete FBS schedule: {len(events)} games")
    schedule, box = [], []
    for event in events.values():
        comp = (event.get("competitions") or [{}])[0]
        teams = comp.get("competitors", [])
        if len(teams) != 2:
            continue
        home = next((t for t in teams if t.get("homeAway") == "home"), None)
        away = next((t for t in teams if t.get("homeAway") == "away"), None)
        if not home or not away:
            continue
        done = bool(event.get("status", {}).get("type", {}).get("completed"))
        schedule.append({"game_id": event["id"], "start_date": event.get("date"),
            "home_id": home["team"]["id"], "away_id": away["team"]["id"],
            "home_team": home["team"].get("location", home["team"].get("displayName")),
            "away_team": away["team"].get("location", away["team"].get("displayName")),
            "home_score": home.get("score", ""), "away_score": away.get("score", ""),
            "completed": done, "neutral_site": comp.get("neutralSite", False),
            "conference_game": comp.get("conferenceCompetition", False)})
        if not done:
            continue
        try:
            summary = fetch("summary", event=event["id"])
            for team in summary.get("boxscore", {}).get("teams", []):
                row = {"game_id": event["id"], "team_id": team.get("team", {}).get("id")}
                for stat in team.get("statistics", []):
                    row[stat.get("name", "")] = stat.get("displayValue", "")
                box.append(row)
        except Exception as exc:
            print(f"Summary unavailable for {event['id']}: {type(exc).__name__}")
        time.sleep(.05)
    if len(box) < 500:
        raise RuntimeError(f"Too few team box-score rows: {len(box)}")
    def write(name, rows):
        fields = sorted({key for row in rows for key in row})
        with (OUT / name).open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    write("cfb_schedules_2026.csv", schedule)
    write("team_box_2026.csv", box)
    (OUT / "collection_metadata.json").write_text(json.dumps({
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "games": len(schedule), "team_box_rows": len(box),
        "source": "ESPN site API v2", "season": 2026
    }, indent=2) + "\n")
    print(f"Saved {len(schedule)} games and {len(box)} team box-score rows")

if __name__ == "__main__":
    main()
