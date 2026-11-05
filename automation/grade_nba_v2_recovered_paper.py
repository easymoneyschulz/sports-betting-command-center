"""Append-only NBA V2 paper-pick snapshots and automatic ESPN result grading.

Never overwrite a previously recorded selection, price or line.
A player without a confirmed boxscore appearance is DNP/VOID, not a loss.
"""
import io
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
import requests

ROOT=Path(__file__).resolve().parents[1]/"public_data"
CURRENT=ROOT/"nba_v2_recovered_prop_comparison.csv"
TRACKER=ROOT/"nba_v2_recovered_paper_tracker.csv"
KEY=["game_date","game_id","player_id","model_version"]
COLUMNS=KEY+["player_name","team","opponent","decision","v2_projection","market_line","sportsbook","over_price","under_price","edge","odds_timestamp_utc","locked_at_utc","lineup_status","actual_points","result","net_units","graded_at_utc"]

def fetch_boxscore(game_id):
    r=requests.get("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary",params={"event":str(game_id)},timeout=30)
    r.raise_for_status()
    data=r.json()
    completed=bool(data.get("header",{}).get("competitions",[{}])[0].get("status",{}).get("type",{}).get("completed",False))
    if not completed:
        completed=bool(data.get("boxscore",{}).get("teams")) and data.get("header",{}).get("competitions",[{}])[0].get("status",{}).get("type",{}).get("name")=="STATUS_FINAL"
    if not completed:return False,{}
    scores={}
    for team in data.get("boxscore",{}).get("players",[]):
        for group in team.get("statistics",[]):
            labels=[str(v).upper() for v in group.get("labels",[])]
            if "PTS" not in labels:continue
            pos=labels.index("PTS")
            for a in group.get("athletes",[]):
                athlete=a.get("athlete",{})
                pid=str(athlete.get("id",""))
                vals=a.get("stats",[])
                if pid and len(vals)>pos:
                    try:scores[pid]=float(vals[pos])
                    except (ValueError,TypeError):pass
    return True,scores

def payoff(price,won):
    if not won:return -1.0
    if pd.isna(price) or float(price)==0:return float("nan")
    price=float(price)
    return round(price/100 if price>0 else 100/abs(price),5)

def main():
    if TRACKER.exists():
        old=pd.read_csv(TRACKER,dtype={"game_id":str,"player_id":str})
    else:old=pd.DataFrame(columns=COLUMNS)
    if not old.empty and old.duplicated(KEY).any():raise ValueError("Duplicate tracker keys; refusing to grade")
    if CURRENT.exists():
        fresh=pd.read_csv(CURRENT,dtype={"game_id":str,"player_id":str})
        needed=set(KEY+["decision","market_line","sportsbook","over_price","under_price","v2_projection"])
        if not needed.issubset(fresh):raise ValueError("Incomplete prediction comparison")
        fresh=fresh[fresh.decision.isin(["OVER","UNDER"])].copy()
        fresh=fresh.dropna(subset=["market_line","sportsbook"])
        if not fresh.empty:
            fresh["locked_at_utc"]=datetime.now(ZoneInfo("UTC")).isoformat()
            fresh["lineup_status"]="UNCONFIRMED"
            fresh["actual_points"]=float("nan")
            fresh["result"]="PENDING"
            fresh["net_units"]=float("nan")
            fresh["graded_at_utc"]=""
            existing=set(tuple(row) for row in old[KEY].itertuples(index=False,name=None))
            fresh=fresh[[tuple(row) not in existing for row in fresh[KEY].itertuples(index=False,name=None)]]
            if not fresh.empty:
                old=pd.concat([old,fresh.reindex(columns=COLUMNS)],ignore_index=True)
                print("New locked paper selections:",len(fresh))
    if old.empty:
        print("No verified paper selections to grade");return
    now=datetime.now(ZoneInfo("America/Chicago")).date()
    old["game_date"]=old["game_date"].astype(str).str[:10]
    # Previously unverified missing boxscore entries must be checked again.
    unverified=old["result"].eq("DNP_VOID") & old["lineup_status"].eq("DID_NOT_PLAY_OR_UNVERIFIED")
    old.loc[unverified,"result"]="PENDING"
    old.loc[unverified,"lineup_status"]="UNVERIFIED"
    old.loc[unverified,"net_units"]=float("nan")
    old.loc[unverified,"graded_at_utc"]=""
    eligible=old[(old.result=="PENDING") & (pd.to_datetime(old.game_date,errors="coerce").dt.date<=now)]
    for game_id,rows in eligible.groupby("game_id"):
        try:completed,points=fetch_boxscore(game_id)
        except (requests.RequestException,KeyError,IndexError,ValueError) as exc:
            print("Boxscore unavailable:",game_id,str(exc)[:120]);continue
        if not completed:continue
        matched=sum(str(pid) in points for pid in rows.player_id)
        if matched==0:
            print(f"GRADING DATA MISMATCH: game {game_id}, {len(rows)} tracked picks, 0 matching ESPN boxscore athlete IDs; preserving PENDING")
        for idx,r in rows.iterrows():
            pid=str(r.player_id)
            if pid not in points:
                # Missing ESPN athlete stats do not establish a DNP.
                old.at[idx,"result"]="PENDING"
                old.at[idx,"lineup_status"]="UNVERIFIED"
                old.at[idx,"net_units"]=float("nan")
            else:
                actual=points[pid]
                line=float(r.market_line)
                old.at[idx,"actual_points"]=actual
                old.at[idx,"lineup_status"]="PLAYED_CONFIRMED"
                if actual==line:
                    old.at[idx,"result"]="PUSH"
                    old.at[idx,"net_units"]=0.0
                else:
                    won=(actual>line) if r.decision=="OVER" else (actual<line)
                    old.at[idx,"result"]="WIN" if won else "LOSS"
                    price=r.over_price if r.decision=="OVER" else r.under_price
                    old.at[idx,"net_units"]=payoff(price,won)
            if old.at[idx,"result"]!="PENDING":
                old.at[idx,"graded_at_utc"]=datetime.now(ZoneInfo("UTC")).isoformat()
    TRACKER.parent.mkdir(parents=True,exist_ok=True)
    tmp=TRACKER.with_suffix(".tmp")
    old.reindex(columns=COLUMNS).to_csv(tmp,index=False)
    tmp.replace(TRACKER)
    print("Tracker:",len(old),"results:",old.result.value_counts().to_dict())
    if not old.empty and not old.result.isin(["WIN","LOSS","PUSH"]).any():
        print("WARNING: No verified graded results yet; do not report 0-0 as a completed record.")
if __name__=="__main__":main()
