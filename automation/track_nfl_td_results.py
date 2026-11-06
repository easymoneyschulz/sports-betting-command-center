#!/usr/bin/env python3
"""Freeze first pregame TD projections and grade completed games without changing predictions."""
from pathlib import Path
import pandas as pd
import nflreadpy as nfl

ROOT=Path("public_data")
HISTORY=ROOT/"nfl_td_projection_history.csv"
LEGS=ROOT/"nfl_td_parlay_history.csv"
def frame(v): return v.to_pandas() if hasattr(v,"to_pandas") else pd.DataFrame(v)
def main():
    current=ROOT/"nfl_td_v3_latest.csv"
    if not current.exists(): raise SystemExit("No published TD snapshot")
    fresh=pd.read_csv(current,dtype={"player_id":str,"game_id":str})
    required={"player_id","game_id","kickoff_utc","td_probability","player_name","position","team","opponent","run_timestamp_utc"}
    if not required.issubset(fresh): raise ValueError("Missing snapshot fields")
    fresh["kickoff_utc"]=pd.to_datetime(fresh.kickoff_utc,utc=True)
    fresh["run_timestamp_utc"]=pd.to_datetime(fresh.run_timestamp_utc,utc=True)
    fresh=fresh[fresh.run_timestamp_utc<fresh.kickoff_utc].copy()
    old=pd.read_csv(HISTORY,dtype={"player_id":str,"game_id":str}) if HISTORY.exists() else pd.DataFrame()
    # First eligible published prediction is immutable; no postgame hindsight.
    if not old.empty:
        fresh=fresh[~pd.MultiIndex.from_frame(fresh[["game_id","player_id"]]).isin(
            pd.MultiIndex.from_frame(old[["game_id","player_id"]]))]
    fresh["model_version"]="V3"
    fresh["result"]="PENDING"
    fresh["actual_rushing_tds"]=pd.NA
    fresh["actual_receiving_tds"]=pd.NA
    combined=pd.concat([old,fresh],ignore_index=True)
    combined=combined.drop_duplicates(["game_id","player_id"],keep="first")
    if combined.empty: return
    years=sorted(set(pd.to_numeric(combined.game_id.str.slice(0,4),errors="coerce").dropna().astype(int)))
    schedules=frame(nfl.load_schedules(years))
    done=schedules[(schedules.game_type=="REG")&schedules.home_score.notna()&schedules.away_score.notna()]
    finished=set(done.game_id.astype(str))
    pending=combined[(combined.result=="PENDING")&combined.game_id.isin(finished)]
    if not pending.empty:
        stats=frame(nfl.load_player_stats(years))
        stats=stats[stats.game_id.astype(str).isin(finished)].copy()
        stats.player_id=stats.player_id.astype(str)
        for c in ("rushing_tds","receiving_tds"):
            stats[c]=pd.to_numeric(stats[c],errors="coerce").fillna(0)
        totals=stats.groupby(["game_id","player_id"],as_index=False)[["rushing_tds","receiving_tds"]].sum()
        lookup={(str(r.game_id),str(r.player_id)):(int(r.rushing_tds),int(r.receiving_tds)) for r in totals.itertuples()}
        for i,r in pending.iterrows():
            rush,rec=lookup.get((str(r.game_id),str(r.player_id)),(0,0))
            combined.at[i,"actual_rushing_tds"]=rush
            combined.at[i,"actual_receiving_tds"]=rec
            combined.at[i,"result"]="HIT" if rush+rec>0 else "MISS"
    combined.to_csv(HISTORY,index=False)
    # Freeze a single Sunday parlay per week, drawn from the first available pregame snapshot.
    combined["kickoff_utc"]=pd.to_datetime(combined.kickoff_utc,utc=True)
    combined["run_timestamp_utc"]=pd.to_datetime(combined.run_timestamp_utc,utc=True)
    combined["week_key"]=combined.kickoff_utc.dt.tz_convert("America/Chicago").dt.strftime("%G-W%V")
    sunday=combined[combined.kickoff_utc.dt.tz_convert("America/Chicago").dt.dayofweek==6]
    existing=pd.read_csv(LEGS,dtype={"player_id":str,"game_id":str}) if LEGS.exists() else pd.DataFrame()
    rows=[]
    for wk,g in sunday.groupby("week_key"):
        if not existing.empty and wk in set(existing.week_key): continue
        first=g.run_timestamp_utc.min()
        # Only one frozen publication cohort, not a cherry-picked combination of runs.
        cohort=g[g.run_timestamp_utc==first].sort_values("td_probability",ascending=False)
        chosen=cohort.drop_duplicates("game_id").head(3)
        if len(chosen)!=3: continue
        for rank,r in enumerate(chosen.itertuples(),1):
            rows.append(dict(week_key=wk,leg=rank,game_id=r.game_id,player_id=r.player_id,
                player_name=r.player_name,team=r.team,opponent=r.opponent,
                td_probability=r.td_probability,run_timestamp_utc=r.run_timestamp_utc))
    legs=pd.concat([existing,pd.DataFrame(rows)],ignore_index=True)
    if not legs.empty:
        graded=combined.set_index(["game_id","player_id"])["result"]
        legs["result"]=[graded.get((r.game_id,r.player_id),"PENDING") for r in legs.itertuples()]
        legs["parlay_result"]="PENDING"
        for wk,group in legs.groupby("week_key"):
            if len(group)!=3: continue
            outcomes=set(group.result)
            verdict="WIN" if outcomes=={"HIT"} else ("LOSS" if "MISS" in outcomes else "PENDING")
            legs.loc[group.index,"parlay_result"]=verdict
        legs.to_csv(LEGS,index=False)
    print(f"Tracked {len(combined)} immutable player-game projections, {len(legs)//3} frozen Sunday parlays")
if __name__=="__main__": main()
