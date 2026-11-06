#!/usr/bin/env python3
"""Validate the newest TD research snapshot before public website publication."""
import argparse
from pathlib import Path
import pandas as pd

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--snapshots",default="research_snapshots/nfl_td")
    parser.add_argument("--destination",default="public_data/nfl_td_v3_latest.csv")
    args=parser.parse_args()
    candidates=sorted(Path(args.snapshots).glob("nfl_td_v3_*.csv"))
    if not candidates: raise SystemExit("No model snapshot generated; refusing to publish.")
    source=candidates[-1]
    df=pd.read_csv(source,dtype={"player_id":str,"game_id":str})
    required={"player_id","player_name","position","team","opponent","game_id",
              "kickoff_utc","td_probability","run_timestamp_utc","status","odds_status"}
    if not required.issubset(df.columns) or df.empty:
        raise SystemExit("Missing required columns or empty TD snapshot.")
    df["td_probability"]=pd.to_numeric(df["td_probability"],errors="coerce")
    if not df["td_probability"].between(0,1).all():
        raise SystemExit("Invalid TD probabilities.")
    if df[list(required)].isna().any().any():
        raise SystemExit("Null values in required TD fields.")
    if df.duplicated(["player_id","game_id"]).any():
        raise SystemExit("Duplicate player-game rows.")
    if not df["position"].isin(["QB","RB","WR","TE"]).all():
        raise SystemExit("Invalid position.")
    now=pd.Timestamp.now(tz="UTC")
    kick=pd.to_datetime(df["kickoff_utc"],utc=True,errors="coerce")
    stamp=pd.to_datetime(df["run_timestamp_utc"],utc=True,errors="coerce")
    if kick.isna().any() or stamp.isna().any() or not (kick>now).all():
        raise SystemExit("Stale or invalid kickoff timestamps; refusing publication.")
    if ((now-stamp).abs()>pd.Timedelta(hours=2)).any():
        raise SystemExit("Research run is stale.")
    if not (df["status"]=="RESEARCH_ONLY_UNVERIFIED_ROSTER").all():
        raise SystemExit("Unexpected betting publication status.")
    if not (df["odds_status"]=="NO_ANYTIME_TD_ODDS").all():
        raise SystemExit("Unexpected odds status.")
    dest=Path(args.destination)
    dest.parent.mkdir(parents=True,exist_ok=True)
    df.sort_values("td_probability",ascending=False).to_csv(dest,index=False)
    print(f"Validated {len(df)} research projections and staged {dest}")

if __name__=="__main__":
    main()
