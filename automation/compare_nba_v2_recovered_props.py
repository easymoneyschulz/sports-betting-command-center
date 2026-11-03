"""Match frozen NBA V2 projections to independently fetched, verified sportsbook lines."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]/"public_data"
PROJ=ROOT/"nba_v2_recovered_paper_predictions.csv"
ODDS=ROOT/"nba_v2_propline_odds.csv"
OUT=ROOT/"nba_v2_recovered_prop_comparison.csv"
CODES={"ATL":"Atlanta Hawks","BOS":"Boston Celtics","BKN":"Brooklyn Nets","CHA":"Charlotte Hornets","CHI":"Chicago Bulls","CLE":"Cleveland Cavaliers","DAL":"Dallas Mavericks","DEN":"Denver Nuggets","DET":"Detroit Pistons","GSW":"Golden State Warriors","HOU":"Houston Rockets","IND":"Indiana Pacers","LAC":"LA Clippers","LAL":"Los Angeles Lakers","MEM":"Memphis Grizzlies","MIA":"Miami Heat","MIL":"Milwaukee Bucks","MIN":"Minnesota Timberwolves","NOP":"New Orleans Pelicans","NYK":"New York Knicks","OKC":"Oklahoma City Thunder","ORL":"Orlando Magic","PHI":"Philadelphia 76ers","PHX":"Phoenix Suns","POR":"Portland Trail Blazers","SAC":"Sacramento Kings","SAS":"San Antonio Spurs","TOR":"Toronto Raptors","UTA":"Utah Jazz","WAS":"Washington Wizards"}
def main():
    if not PROJ.exists():raise FileNotFoundError("No recovered model output")
    p=pd.read_csv(PROJ,dtype={"game_id":str,"player_id":str})
    required={"game_date","player_name","team","opponent","v2_projection","model_version"}
    if not required.issubset(p):raise ValueError("Missing model fields; refusing unverified odds joins")
    p=p[p.model_version=="NBA_V2_RECOVERED_FROZEN_PAPER"].copy()
    p["market_line"]=float("nan")
    p["over_price"]=float("nan")
    p["under_price"]=float("nan")
    p["sportsbook"]=""
    p["odds_timestamp_utc"]=""
    p["edge"]=float("nan")
    p["decision"]="WAIT"
    p["status"]="PAPER"
    if ODDS.exists():
        o=pd.read_csv(ODDS)
        needed={"commence_time","home_team","away_team","player_name","sportsbook","market_line","over_price","under_price","odds_timestamp_utc"}
        if not needed.issubset(o):raise ValueError("Missing sportsbook fields")
        now=pd.Timestamp.now(tz="UTC")
        o["commence_time"]=pd.to_datetime(o.commence_time,utc=True,errors="coerce")
        o["odds_timestamp_utc"]=pd.to_datetime(o.odds_timestamp_utc,utc=True,errors="coerce")
        o=o[(o.commence_time>now)&(o.odds_timestamp_utc<=now)&(o.odds_timestamp_utc>=now-pd.Timedelta(hours=24))].copy()
        for col in ("market_line","over_price","under_price"):o[col]=pd.to_numeric(o[col],errors="coerce")
        o=o.dropna(subset=["market_line","over_price","under_price"])
        o["game_date"]=o.commence_time.dt.tz_convert("America/Chicago").dt.strftime("%Y-%m-%d")
        o["player_key"]=o.player_name.astype(str).str.casefold().str.strip()
        p["player_key"]=p.player_name.astype(str).str.casefold().str.strip()
        # Both team and opponent must belong to the SAME sportsbook event.
        o["teams"]=o.apply(lambda r:{str(r.home_team).casefold(),str(r.away_team).casefold()},axis=1)
        matches=p.reset_index().merge(o,on=["game_date","player_key"],suffixes=("","_book"),how="inner")
        matches=matches[matches.apply(lambda r:CODES.get(r.team,"").casefold() in r.teams and CODES.get(r.opponent,"").casefold() in r.teams,axis=1)]
        if not matches.empty:
            matches=matches.sort_values("odds_timestamp_utc_book",ascending=False).drop_duplicates("index")
            for _,r in matches.iterrows():
                idx=int(r["index"])
                for col in ("market_line","over_price","under_price","sportsbook"):
                    p.at[idx,col]=r[col+"_book"] if col in p.columns else r[col]
                p.at[idx,"odds_timestamp_utc"]=r["odds_timestamp_utc_book"].isoformat()
                edge=float(p.at[idx,"v2_projection"])-float(p.at[idx,"market_line"])
                p.at[idx,"edge"]=edge
                p.at[idx,"decision"]="OVER" if edge>=3 else "UNDER" if edge<=-3 else "PASS"
    p=p.drop(columns=["player_key"],errors="ignore")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    p.to_csv(OUT,index=False)
    print("Model projections:",len(p),"verified sportsbook matches:",p.market_line.notna().sum(),"paper leans:",p.decision.isin(["OVER","UNDER"]).sum())
if __name__=="__main__":main()
