"""Fetch DraftKings/FanDuel NCAAF odds and verify both school names and kickoff.

Requires ODDS_API_KEY in environment. Unmatched games are excluded, not guessed.
"""
import json
import os
import re
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "automation/data/cfb"
ALIASES = {"miami oh":"miami ohio", "utsa":"texas san antonio", "smu":"southern methodist",
           "tcu":"texas christian", "ucf":"central florida", "uconn":"connecticut",
           "byu":"brigham young", "app state":"appalachian state", "ole miss":"mississippi",
           "hawai i":"hawaii", "fiu":"florida international", "fau":"florida atlantic",
           "pitt":"pittsburgh", "southern miss":"southern mississippi"}
def clean(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", " ", s.lower().replace("&", "and")).strip()
    return ALIASES.get(s, s)
def main():
    key = os.environ.get("ODDS_API_KEY")
    if not key:
        raise RuntimeError("ODDS_API_KEY secret is not configured")
    params = urllib.parse.urlencode({"apiKey":key,"regions":"us","markets":"spreads,totals",
        "oddsFormat":"american","bookmakers":"draftkings,fanduel"})
    req=urllib.request.Request("https://api.the-odds-api.com/v4/sports/americanfootball_ncaaf/odds/?"+params,
                               headers={"User-Agent":"SportsBettingCommandCenter/1.0"})
    with urllib.request.urlopen(req,timeout=45) as response:
        odds=json.load(response)
    source=pd.read_csv(DATA/"cfb_v4_team_features_2026.csv",dtype={"game_id":str})
    source["verified_kickoff"]=pd.to_datetime(source["verified_kickoff"],utc=True)
    schools=set(source.home_team.map(clean)).union(source.away_team.map(clean))
    def school(name):
        n=clean(name)
        matches=[s for s in schools if n==s or n.startswith(s+" ")]
        return max(matches,key=len) if matches else None
    rows=[]
    for game in odds:
        book=next((b for name in ("draftkings","fanduel") for b in game.get("bookmakers",[]) if b.get("key")==name),None)
        if not book: continue
        markets={m["key"]:m.get("outcomes",[]) for m in book.get("markets",[])}
        h=next((x for x in markets.get("spreads",[]) if x.get("name")==game["home_team"]),None)
        a=next((x for x in markets.get("spreads",[]) if x.get("name")==game["away_team"]),None)
        total=next((x for x in markets.get("totals",[]) if x.get("name")=="Over"),None)
        if not all((h,a,total)):continue
        rows.append({"odds_home":school(game["home_team"]),"odds_away":school(game["away_team"]),
          "verified_kickoff":pd.to_datetime(game["commence_time"],utc=True),
          "home_spread":h.get("point"),"home_price":h.get("price"),"away_price":a.get("price"),
          "over_under":total.get("point"),"sportsbook":book["key"],"api_game_id":game["id"]})
    market=pd.DataFrame(rows)
    if market.empty:raise RuntimeError("No complete spreads and totals returned by sportsbooks")
    market=market.dropna(subset=["odds_home","odds_away"])
    if market.duplicated(["odds_home","odds_away","verified_kickoff"]).any():
        raise RuntimeError("Ambiguous sportsbook games: duplicate team/kickoff")
    source["home_key"]=source.home_team.map(clean)
    source["away_key"]=source.away_team.map(clean)
    matched=source.merge(market,left_on=["home_key","away_key"],
        right_on=["odds_home","odds_away"],how="inner",validate="one_to_one",suffixes=("_espn","_odds"))
    matched=matched.loc[(matched.verified_kickoff_espn - matched.verified_kickoff_odds).abs() <= pd.Timedelta(hours=2)].copy()
    matched["start_date"]=matched["verified_kickoff_espn"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    matched["market_margin"]=-pd.to_numeric(matched.home_spread,errors="coerce")
    matched=matched.dropna(subset=["market_margin","over_under","home_price","away_price"])
    expected=json.loads((DATA.parents[1]/"models/cfb_v4_features.json").read_text())
    matched=matched.dropna(subset=expected)
    if matched.empty:raise RuntimeError("No fully verified, complete 27-feature matchups; no picks published")
    matched["odds_retrieved_at_utc"]=datetime.now(timezone.utc).isoformat()
    output=DATA/"cfb_v4_model_input_2026.csv"
    matched.to_csv(output,index=False)
    print(f"Verified {len(matched)} of {len(source)} feature-complete games; saved {output}")
if __name__=="__main__":main()
