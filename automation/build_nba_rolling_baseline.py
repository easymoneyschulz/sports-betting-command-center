"""Free ESPN NBA box-score collection and rolling points projections.

Reconstructed rolling baseline (NOT the original trained NBA V2 model).
Fetches completed NBA games for recent dates and upcoming slate from ESPN.
Fail closed when insufficient samples; no fabricated projections.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]/"public_data"
CACHE=ROOT/"nba_rolling_game_logs.csv"
DEST=ROOT/"nba_daily_rebuilt_projections.csv"
SOURCE=ROOT/"nba_v2_source_predictions.csv"
BASE="https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
SESSION=requests.Session()
SESSION.headers.update({"User-Agent":"SportsBettingCommandCenter/1.0"})
TEAM_MAP={"ATL":"Atlanta Hawks","BOS":"Boston Celtics","BKN":"Brooklyn Nets","CHA":"Charlotte Hornets","CHI":"Chicago Bulls","CLE":"Cleveland Cavaliers","DAL":"Dallas Mavericks","DEN":"Denver Nuggets","DET":"Detroit Pistons","GS":"Golden State Warriors","GSW":"Golden State Warriors","HOU":"Houston Rockets","IND":"Indiana Pacers","LAC":"LA Clippers","LAL":"Los Angeles Lakers","MEM":"Memphis Grizzlies","MIA":"Miami Heat","MIL":"Milwaukee Bucks","MIN":"Minnesota Timberwolves","NO":"New Orleans Pelicans","NOP":"New Orleans Pelicans","NY":"New York Knicks","NYK":"New York Knicks","OKC":"Oklahoma City Thunder","ORL":"Orlando Magic","PHI":"Philadelphia 76ers","PHX":"Phoenix Suns","POR":"Portland Trail Blazers","SAC":"Sacramento Kings","SA":"San Antonio Spurs","SAS":"San Antonio Spurs","TOR":"Toronto Raptors","UTAH":"Utah Jazz","UTA":"Utah Jazz","WSH":"Washington Wizards","WAS":"Washington Wizards"}
def get(url,params=None):
    r=SESSION.get(url,params=params,timeout=30);r.raise_for_status();return r.json()
def slate(date):
    data=get(BASE+"/scoreboard",{"dates":date.strftime("%Y%m%d"),"limit":1000})
    return data.get("events",[])
def event_teams(event):
    competition=event.get("competitions",[{}])[0]
    teams=competition.get("competitors",[])
    return {t.get("homeAway"):t.get("team",{}) for t in teams}
def collect_box(event_id,game_date):
    payload=get(BASE+"/summary",{"event":event_id})
    out=[]
    for team in payload.get("boxscore",{}).get("players",[]):
        for block in team.get("statistics",[]):
            labels=[str(x).upper() for x in block.get("labels",[])]
            if "PTS" not in labels:continue
            pi=labels.index("PTS");mi=labels.index("MIN") if "MIN" in labels else None
            for athlete in block.get("athletes",[]):
                stats=athlete.get("stats",[])
                if len(stats)<=pi or not athlete.get("athlete"):continue
                try: points=float(stats[pi])
                except (ValueError,TypeError):continue
                try: minutes=float(stats[mi]) if mi is not None else None
                except (ValueError,TypeError):minutes=None
                if minutes is not None and minutes<=0:continue
                a=athlete["athlete"]
                out.append({"game_id":str(event_id),"game_date":game_date.isoformat(),"player_id":str(a.get("id","")),"player_name":a.get("displayName"),"team":team.get("team",{}).get("displayName"),"points":points,"minutes":minutes})
    return out
def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    now=datetime.now(ZoneInfo("America/Chicago"));today=now.date()
    old=pd.read_csv(CACHE,dtype={"game_id":str,"player_id":str}) if CACHE.exists() else pd.DataFrame()
    # First run backfills 21 days, then only the latest 3 days.
    days=21 if old.empty else 3
    rows=[]
    for n in range(days,0,-1):
        date=today-timedelta(days=n)
        for event in slate(date):
            if event.get("status",{}).get("type",{}).get("completed") is not True:continue
            try:rows.extend(collect_box(event["id"],date))
            except (requests.RequestException,KeyError,ValueError) as exc:
                print("Skipped box score",event.get("id"),type(exc).__name__)
    recent=pd.DataFrame(rows)
    logs=pd.concat([old,recent],ignore_index=True) if not old.empty else recent
    if logs.empty:
        print("No completed box-score data; no projections");return
    logs=logs.drop_duplicates(["game_id","player_id"],keep="last")
    logs.to_csv(CACHE,index=False)
    logs["game_date"]=pd.to_datetime(logs["game_date"],errors="coerce")
    logs["points"]=pd.to_numeric(logs["points"],errors="coerce")
    logs["minutes"]=pd.to_numeric(logs["minutes"],errors="coerce")
    target_date=today
    upcoming=slate(target_date)
    if not any(not e.get("status",{}).get("type",{}).get("completed") for e in upcoming):
        target_date=today+timedelta(days=1)
        upcoming=slate(target_date)
    out=[]
    for event in upcoming:
        if event.get("status",{}).get("type",{}).get("completed"):continue
        teams=event_teams(event)
        if not all(x in teams for x in ("home","away")):continue
        for side in ("home","away"):
            team=teams[side].get("displayName")
            opponent=teams["away" if side=="home" else "home"].get("displayName")
            player_logs=logs[logs["team"]==team]
            for player_id,group in player_logs.groupby("player_id"):
                g=group.sort_values("game_date").tail(10)
                if len(g)<5:continue
                last5=g.tail(5)
                avg10=g["points"].mean();avg5=last5["points"].mean()
                # Conservative transparent rolling estimate, not original V2.
                projection=round(0.65*avg10+0.35*avg5,4)
                if not 0<=projection<=65:continue
                out.append({"game_date":target_date.isoformat(),"game_id":str(event["id"]),"player_id":str(player_id),"player_name":g["player_name"].iloc[-1],"opponent":opponent,"team":team,"v2_projection":projection,"model_version":"ROLLING_REBUILD_V0","sample_games":len(g)})
    result=pd.DataFrame(out)
    if result.empty:
        print("No eligible players with >=5 completed games; no new projection export");return
    result.to_csv(DEST,index=False)
    print("Rebuilt baseline projections:",len(result),"for",target_date)
    # Publish the full-slate rolling baseline separately, even when a five-player
    # original V2 snapshot exists. Never overwrite or relabel original V2.
    result.to_csv(ROOT/"nba_daily_active_projections.csv",index=False)
    print("Published full-slate ROLLING_REBUILD_V0 paper projections; original V2 untouched.")
if __name__=="__main__":main()
