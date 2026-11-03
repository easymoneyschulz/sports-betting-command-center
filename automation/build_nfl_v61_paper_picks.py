"""Read-only NFL V6.1 paper selections from verified sportsbook spreads."""
import argparse
import os
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import requests

NAMES = dict(zip(
"ARI ATL BAL BUF CAR CHI CIN CLE DAL DEN DET GB HOU IND JAX KC LAC LAR LV MIA MIN NE NO NYG NYJ PHI PIT SEA SF TB TEN WAS".split(),
[x.replace("_"," ") for x in "Arizona_Cardinals Atlanta_Falcons Baltimore_Ravens Buffalo_Bills Carolina_Panthers Chicago_Bears Cincinnati_Bengals Cleveland_Browns Dallas_Cowboys Denver_Broncos Detroit_Lions Green_Bay_Packers Houston_Texans Indianapolis_Colts Jacksonville_Jaguars Kansas_City_Chiefs Los_Angeles_Chargers Los_Angeles_Rams Las_Vegas_Raiders Miami_Dolphins Minnesota_Vikings New_England_Patriots New_Orleans_Saints New_York_Giants New_York_Jets Philadelphia_Eagles Pittsburgh_Steelers Seattle_Seahawks San_Francisco_49ers Tampa_Bay_Buccaneers Tennessee_Titans Washington_Commanders".split()]
))
# Use explicit team aliases from nflverse.
ALIASES = {"JAC":"JAX", "LA":"LAR", "WSH":"WAS"}
def team(code):
    return NAMES[ALIASES.get(str(code),str(code))]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--projections",required=True)
    parser.add_argument("--output-dir",required=True)
    args=parser.parse_args()
    key=os.getenv("ODDS_API_KEY")
    if not key:
        raise RuntimeError("Missing ODDS_API_KEY")
    now=datetime.now(timezone.utc)
    frame=pd.read_csv(args.projections)
    if frame.empty:
        raise RuntimeError("Empty projections")
    response=requests.get(
        "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds/",
        params={"apiKey":key,"regions":"us","markets":"spreads",
                "oddsFormat":"american","bookmakers":"draftkings,fanduel"},
        timeout=30)
    response.raise_for_status()
    events={(e["home_team"],e["away_team"]):e for e in response.json()}
    rows=[]
    for _,p in frame.iterrows():
        home,away=team(p.home_team),team(p.away_team)
        event=events.get((home,away))
        if not event:
            continue
        kickoff=pd.to_datetime(event["commence_time"],utc=True)
        if kickoff.to_pydatetime()<=now:
            continue
        for book in sorted(event.get("bookmakers",[]),key=lambda b: 0 if b["key"]=="draftkings" else 1):
            if book["key"] not in ("draftkings","fanduel"):
                continue
            market=next((m for m in book["markets"] if m["key"]=="spreads"),None)
            if not market:
                continue
            sides={o["name"]:o for o in market["outcomes"]}
            if home not in sides or away not in sides:
                continue
            h,a=sides[home],sides[away]
            if abs(float(h["point"])+float(a["point"]))>0.01:
                continue
            correction=float(p.model_home_margin)
            side="HOME" if correction>0 else "AWAY"
            chosen=h if side=="HOME" else a
            rows.append({
                "game_id":p.game_id,"season":int(p.season),"week":int(p.week),
                "home_team":home,"away_team":away,
                "kickoff_utc":kickoff.isoformat(),"sportsbook":book["key"],
                "home_spread":float(h["point"]),
                "model_market_correction":correction,
                "model_home_margin":-float(h["point"])+correction,
                "edge_points":abs(correction),
                "selected_side":side,"selected_team":home if side=="HOME" else away,
                "selected_spread":float(chosen["point"]),
                "selected_price":int(chosen["price"]),
                "odds_timestamp_utc":market.get("last_update",book.get("last_update","")),
                "prediction_timestamp_utc":now.isoformat(),
                "decision":"PASS","test_mode":"PAPER_ONLY"})
            break
    ranked=sorted(rows,key=lambda r:(-r["edge_points"],str(r["game_id"])))
    for row in [r for r in ranked if 2<=r["edge_points"]<5][:5]:
        row["decision"]="PAPER_PICK"
    dest=Path(args.output_dir)
    dest.mkdir(parents=True,exist_ok=True)
    out=dest/("nfl_v61_paper_picks_%s_week%s_%s.csv"%(
        int(frame.iloc[0].season),int(frame.iloc[0].week),now.strftime("%Y%m%dT%H%M%SZ")))
    pd.DataFrame(rows,columns=[
        "game_id","season","week","home_team","away_team","kickoff_utc",
        "sportsbook","home_spread","model_market_correction","model_home_margin",
        "edge_points","selected_side","selected_team","selected_spread",
        "selected_price","odds_timestamp_utc","prediction_timestamp_utc",
        "decision","test_mode"]).to_csv(out,index=False)
    print("Saved:",out,"Paper picks:",sum(r["decision"]=="PAPER_PICK" for r in rows))

if __name__=="__main__":
    main()
