#!/usr/bin/env python3
"""Fetch verified anytime TD prices from The Odds API; never invent missing prices."""
import os
import re
from pathlib import Path
import pandas as pd
import requests

BASE="https://api.the-odds-api.com/v4/sports/americanfootball_nfl"
def norm(s):
    return re.sub(r"[^a-z0-9]","",str(s).lower())
def main():
    key=os.environ.get("ODDS_API_KEY")
    if not key: raise RuntimeError("ODDS_API_KEY is missing")
    src=Path("public_data/nfl_td_v3_latest.csv")
    predictions=pd.read_csv(src,dtype={"game_id":str,"player_id":str})
    now=pd.Timestamp.now(tz="UTC")
    predictions["kickoff_utc"]=pd.to_datetime(predictions.kickoff_utc,utc=True)
    predictions=predictions[predictions.kickoff_utc>now]
    if predictions.empty: raise RuntimeError("No upcoming model projections")
    session=requests.Session()
    def get(url,params):
        response=session.get(url,params={"apiKey":key,**params},timeout=35)
        response.raise_for_status()
        return response.json()
    events=get(BASE+"/events",{})
    rows=[]
    for event in events:
        kickoff=pd.to_datetime(event.get("commence_time"),utc=True,errors="coerce")
        if pd.isna(kickoff) or kickoff<=now: continue
        # Match to nflverse game using kickoff and both team names, never name alone.
        teams={norm(event.get("home_team")),norm(event.get("away_team"))}
        game_candidates=predictions[
            (predictions.kickoff_utc-kickoff).abs()<=pd.Timedelta(hours=3)]
        games=[]
        for game_id,g in game_candidates.groupby("game_id"):
            if len(g) and {norm(g.iloc[0].team),norm(g.iloc[0].opponent)}==teams:
                games.append((game_id,g))
        # nflverse team values are abbreviations; resolve from canonical names.
        aliases=dict(zip("ARI ATL BAL BUF CAR CHI CIN CLE DAL DEN DET GB HOU IND JAX KC LAC LAR LV MIA MIN NE NO NYG NYJ PHI PIT SEA SF TB TEN WAS".split(),
          "Arizona_Cardinals Atlanta_Falcons Baltimore_Ravens Buffalo_Bills Carolina_Panthers Chicago_Bears Cincinnati_Bengals Cleveland_Browns Dallas_Cowboys Denver_Broncos Detroit_Lions Green_Bay_Packers Houston_Texans Indianapolis_Colts Jacksonville_Jaguars Kansas_City_Chiefs Los_Angeles_Chargers Los_Angeles_Rams Las_Vegas_Raiders Miami_Dolphins Minnesota_Vikings New_England_Patriots New_Orleans_Saints New_York_Giants New_York_Jets Philadelphia_Eagles Pittsburgh_Steelers Seattle_Seahawks San_Francisco_49ers Tampa_Bay_Buccaneers Tennessee_Titans Washington_Commanders".split()))
        aliases.update({"JAC":aliases["JAX"],"WSH":aliases["WAS"],"LA":aliases["LAR"]})
        if not games:
            for game_id,g in game_candidates.groupby("game_id"):
                if {norm(aliases.get(str(g.iloc[0].team),g.iloc[0].team).replace("_"," ")),
                    norm(aliases.get(str(g.iloc[0].opponent),g.iloc[0].opponent).replace("_"," "))}==teams:
                    games.append((game_id,g))
        if len(games)!=1: continue
        game_id,g=games[0]
        data=get(BASE+"/events/"+event["id"]+"/odds",{
            "regions":"us","markets":"player_anytime_td","oddsFormat":"american",
            "bookmakers":"draftkings,fanduel"})
        for book in data.get("bookmakers",[]):
            if book.get("key") not in ("draftkings","fanduel"):continue
            for market in book.get("markets",[]):
                if market.get("key")!="player_anytime_td":continue
                updated=pd.to_datetime(market.get("last_update"),utc=True,errors="coerce")
                if pd.isna(updated) or updated>now or updated<now-pd.Timedelta(hours=6):continue
                for outcome in market.get("outcomes",[]):
                    if str(outcome.get("name","")).lower() not in ("yes","over"):continue
                    player=norm(outcome.get("description",""))
                    matches=g[g.player_name.map(norm)==player]
                    if len(matches)!=1:continue
                    price=outcome.get("price")
                    if not isinstance(price,(int,float)) or (-100<price<100):continue
                    p=matches.iloc[0]
                    rows.append(dict(game_id=game_id,player_id=str(p.player_id),
                        american_odds=int(price),sportsbook=book["key"],
                        odds_timestamp_utc=updated.isoformat()))
    # One sportsbook for entire parlay; prefer DK then FanDuel.
    out=Path("public_data/nfl_td_verified_odds.csv")
    columns=["game_id","player_id","american_odds","sportsbook","odds_timestamp_utc"]
    df=pd.DataFrame(rows,columns=columns)
    if not df.empty:
        df=df.sort_values("sportsbook",key=lambda s:s.map({"draftkings":0,"fanduel":1}))
        df=df.drop_duplicates(["game_id","player_id"],keep="first")
    df.to_csv(out,index=False)
    print(f"Verified {len(df)} player anytime-TD prices; no synthetic odds")
if __name__=="__main__":main()
