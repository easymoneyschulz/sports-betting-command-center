"""Frozen NBA V2 daily paper projections. Fail closed on missing inputs."""
import os
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import duckdb, joblib, numpy as np, pandas as pd, requests

ROOT=Path(__file__).resolve().parents[1]
MODEL=ROOT/"automation/models/nba_v2_frozen_2026_model.joblib"
OUTPUT=ROOT/"public_data/nba_v2_recovered_paper_predictions.csv"
DB="https://basketball-data.billmill.org/nba/nba.duckdb"
FEATURES=["home","prior_games"]+[f"{c}_last{w}" for c in ("pts","minutes","usg_pct","fga","fg3a","fta") for w in (5,10,20)]+["pts_std_last10","season_pts_avg_prior"]
TEAM_IDS={"ATL":1610612737,"BOS":1610612738,"BKN":1610612751,"CHA":1610612766,"CHI":1610612741,"CLE":1610612739,"DAL":1610612742,"DEN":1610612743,"DET":1610612765,"GSW":1610612744,"HOU":1610612745,"IND":1610612754,"LAC":1610612746,"LAL":1610612747,"MEM":1610612763,"MIA":1610612748,"MIL":1610612749,"MIN":1610612750,"NOP":1610612740,"NYK":1610612752,"OKC":1610612760,"ORL":1610612753,"PHI":1610612755,"PHX":1610612756,"POR":1610612757,"SAC":1610612758,"SAS":1610612759,"TOR":1610612761,"UTA":1610612762,"WAS":1610612764}
ALIASES={"GS":"GSW","NY":"NYK","NO":"NOP","SA":"SAS","UTAH":"UTA","WSH":"WAS"}

def minutes(x):
    if pd.isna(x): return np.nan
    if isinstance(x,str) and ":" in x:
        a,b=x.split(":",1)
        return float(a)+float(b)/60
    return pd.to_numeric(x,errors="coerce")

def get_schedule(day):
    r=requests.get("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",params={"dates":day.strftime("%Y%m%d"),"limit":100},timeout=35)
    r.raise_for_status()
    out=[]
    for e in r.json().get("events",[]):
        if e.get("status",{}).get("type",{}).get("completed"): continue
        sides={c.get("homeAway"):c for c in e.get("competitions",[{}])[0].get("competitors",[])}
        if not {"home","away"}<=sides.keys(): continue
        for side in ("home","away"):
            t=sides[side]["team"];opp=sides["away" if side=="home" else "home"]["team"]
            ab=ALIASES.get(t.get("abbreviation"),t.get("abbreviation"))
            oa=ALIASES.get(opp.get("abbreviation"),opp.get("abbreviation"))
            if ab in TEAM_IDS and oa in TEAM_IDS:
                out.append({"game_date":day.isoformat(),"game_id":str(e["id"]),"team_id":TEAM_IDS[ab],"opponent":oa,"home":int(side=="home")})
    return out

def get_history():
    con=duckdb.connect()
    try:
        con.execute("INSTALL httpfs; LOAD httpfs")
        con.execute(f"ATTACH '{DB}' AS nba")
        return con.execute("""
            SELECT l.season,l.game_id,l.player_id,p.name AS player_name,
                   l.team_id,l.game_date,l.home,l.min AS minutes_raw,
                   l.pts,l.fga,l.fg3a,l.fta,l.usg_pct
            FROM nba.player_game_logs l
            JOIN nba.players p ON l.player_id=p.player_id
            JOIN nba.games g ON l.game_id=g.game_id AND l.season=g.season
            WHERE l.season BETWEEN 2023 AND 2027 AND g.game_type='regular_season'
        """).df()
    finally: con.close()

def main():
    if not MODEL.is_file(): raise FileNotFoundError("Frozen model missing; no projections published")
    now=datetime.now(ZoneInfo("America/Chicago"))
    schedule=get_schedule(now.date())
    if not schedule: schedule=get_schedule(now.date()+timedelta(days=1))
    if not schedule:
        print("No future games on selected slate; no output changes");return
    df=get_history()
    if df.empty: raise ValueError("Empty source history")
    df["game_date"]=pd.to_datetime(df["game_date"])
    df["minutes"]=df["minutes_raw"].map(minutes)
    for c in ("pts","usg_pct","fga","fg3a","fta"):
        df[c]=pd.to_numeric(df[c],errors="coerce")
    df=df[df["game_date"].notna() & df["pts"].notna() & (df["minutes"]>0)].copy()
    df["game_id"]=df["game_id"].astype(str)
    df=df.drop_duplicates(["season","game_id","player_id"],keep="last")
    df=df.sort_values(["player_id","game_date","game_id"])
    # Only completed games enter the historical sequence.
    latest=df.groupby("player_id",sort=False).tail(1).copy()
    latest=latest[latest["season"]==2027]
    # Exclude players who have not appeared in the current season.
    if latest.empty: raise ValueError("No current-season players")
    records=[]
    for s in schedule:
        selected=latest[latest["team_id"].astype(str)==str(s["team_id"])]
        for _,p in selected.iterrows():
            records.append({**s,"player_id":p["player_id"],"player_name":p["player_name"],"season":2027})
    future=pd.DataFrame(records)
    if future.empty: raise ValueError("No players matched slate teams; no output")
    future["game_date"]=pd.to_datetime(future["game_date"])
    # Append future rows with missing target; shift(1) prevents target leakage.
    future["pts"]=np.nan
    for c in ("minutes","usg_pct","fga","fg3a","fta"):future[c]=np.nan
    future["is_future"]=True
    df["is_future"]=False
    combined=pd.concat([df,future],ignore_index=True,sort=False)
    combined=combined.sort_values(["player_id","game_date","game_id"],kind="stable")
    combined["prior_games"]=combined.groupby("player_id").cumcount()
    for c in ("pts","minutes","usg_pct","fga","fg3a","fta"):
        for w,m in ((5,3),(10,5),(20,8)):
            combined[f"{c}_last{w}"]=combined.groupby("player_id")[c].transform(lambda x:x.shift(1).rolling(w,min_periods=m).mean())
    combined["pts_std_last10"]=combined.groupby("player_id")["pts"].transform(lambda x:x.shift(1).rolling(10,min_periods=5).std())
    combined["season_pts_avg_prior"]=combined.groupby(["player_id","season"])["pts"].transform(lambda x:x.shift(1).expanding(min_periods=3).mean())
    rows=combined[combined["is_future"]].copy()
    if rows.duplicated(["game_id","player_id"]).any():raise ValueError("Duplicate future player-game rows")
    # Model contains fitted preprocessing; do not fit or modify it.
    model=joblib.load(MODEL)
    predictions=model.predict(rows[FEATURES])
    if len(predictions)!=len(rows) or not np.isfinite(predictions).all():raise ValueError("Invalid model predictions")
    rows["v2_projection"]=predictions
    rows["model_version"]="NBA_V2_RECOVERED_FROZEN_PAPER"
    rows["generated_at_utc"]=pd.Timestamp.now(tz="UTC").isoformat()
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    tmp=OUTPUT.with_suffix(".tmp")
    rows[["game_date","game_id","player_id","player_name","opponent","v2_projection","model_version","generated_at_utc"]].assign(game_date=lambda x:x.game_date.dt.strftime("%Y-%m-%d")).to_csv(tmp,index=False)
    os.replace(tmp,OUTPUT)
    print("PAPER projections:",len(rows),"date:",rows.game_date.min().date(),"file:",OUTPUT)
    print("Historical picks and official V2 source unchanged")

if __name__=="__main__":main()
