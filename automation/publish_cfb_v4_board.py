"""Publish a read-only CFB V4 board from frozen model selections; never regenerate picks."""
import csv
import html
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "public_data" / "cfb_v4_top5.csv"
OUT = ROOT / "public_data"
CT = ZoneInfo("America/Chicago")

def main():
    now = datetime.now(timezone.utc)
    with SOURCE.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    required = {"game_id", "start_date", "home_team", "away_team", "selected_side",
                "selected_spread", "predicted_edge", "decision", "model_home_margin"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("Missing or incomplete frozen CFB V4 source; refusing to publish")
    if len({r["game_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate game IDs; refusing to publish")
    current = []
    for row in rows:
        start = datetime.fromisoformat(row["start_date"].replace("Z", "+00:00"))
        if now - timedelta(hours=24) <= start <= now + timedelta(days=7):
            current.append(row)
    if not current:
        raise ValueError("No upcoming CFB games in source; refusing to republish stale picks")
    current.sort(key=lambda r: r["start_date"])
    payload = {"generated_at_utc": now.isoformat(), "source": "Frozen CFB V4 selections",
               "note": "Publisher does not run the model or refresh betting lines.",
               "picks": current}
    (OUT / "cfb_v4_board.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    cards = []
    for row in current:
        start = datetime.fromisoformat(row["start_date"].replace("Z", "+00:00")).astimezone(CT)
        spread = float(row["selected_spread"])
        sign = "+" if spread > 0 else ""
        label = html.escape(row["decision"])
        cards.append(f"""<article class="card"><div class="top"><span class="pill">{label}</span><time>{start:%a %b %d · %-I:%M %p} CT</time></div>
<h2>{html.escape(row["selected_side"])} <span>{sign}{spread:g}</span></h2>
<p>{html.escape(row["away_team"])} at {html.escape(row["home_team"])}</p>
<div class="metrics"><div><small>MODEL EDGE</small><strong>{float(row["predicted_edge"]):.2f} pts</strong></div><div><small>PROJECTED HOME MARGIN</small><strong>{float(row["model_home_margin"]):+.2f}</strong></div></div></article>""")
    page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CFB V4 | Research Board</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#0a0b0e;color:#f7f7f8;font-family:system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1080px;margin:auto;padding:34px 18px 64px}.eyebrow{font-weight:800;letter-spacing:.16em;color:#fa424b;font-size:.78rem}
h1{font-size:clamp(2rem,6vw,3.7rem);letter-spacing:-.05em;margin:8px 0}header p,.footer{color:#a4a5ac;line-height:1.6}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:16px;margin-top:28px}
.card{background:linear-gradient(160deg,#202126,#131418);border:1px solid #36373c;border-top:3px solid #ed2736;border-radius:15px;padding:22px;box-shadow:0 12px 30px #0005}
.top{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}.pill{font-size:.69rem;letter-spacing:.08em;font-weight:800;border:1px solid #6d2830;color:#ff929a;padding:6px 9px;border-radius:5px}
time{font-size:.78rem;color:#b5b6bd}.card h2{font-size:1.45rem;margin:22px 0 6px}.card h2 span{color:#ff4855;white-space:nowrap}.card p{color:#b4b5bd;margin:0}
.metrics{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:26px;border-top:1px solid #37383e;padding-top:18px}
small{display:block;font-size:.66rem;letter-spacing:.09em;color:#9a9ba5;margin-bottom:7px}strong{font-size:1.15rem}
.footer{margin-top:28px;font-size:.8rem}a{color:#ff717a}
</style></head><body><main><header><div class="eyebrow">EASYMONEYSCHULZ · COLLEGE FOOTBALL</div>
<h1>CFB V4 Research Board</h1><p>Frozen model selections · Times shown in Central · Research only, not a live sportsbook feed</p></header>
<section class="grid">""" + "\n".join(cards) + """</section><p class="footer">Published """ + now.astimezone(CT).strftime("%b %d, %Y at %-I:%M %p CT") + """. Source: existing frozen CFB V4 selections. This publisher does not recalculate predictions, refresh odds, or record bets. PASS means no recommended wager.</p></main></body></html>"""
    (OUT / "cfb_v4_board.html").write_text(page, encoding="utf-8")
    print(f"Published {len(current)} existing CFB selections; model and locked wagers unchanged.")

if __name__ == "__main__":
    main()
