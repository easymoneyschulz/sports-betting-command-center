"""Stage current V4 research selections for the existing CFB publisher.

Only verified, future games within seven days are eligible. No wagers are placed.
Feature reconstruction is not independently backtested: outputs are PAPER research.
"""
import argparse
from pathlib import Path
import pandas as pd

REQUIRED = ["game_id","start_date","home_team","away_team","selected_side",
            "selected_spread","selected_price","predicted_edge","decision",
            "sportsbook","model_home_margin","edge_points","odds_retrieved_at_utc"]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    df=pd.read_csv(args.input,dtype={"game_id":str})
    missing=sorted(set(REQUIRED)-set(df.columns))
    if missing:raise ValueError(f"Missing prediction columns: {missing}")
    if df.game_id.duplicated().any():raise ValueError("Duplicate games in prediction output")
    now=pd.Timestamp.now(tz="UTC")
    kickoff=pd.to_datetime(df.start_date,utc=True,errors="coerce")
    odds_at=pd.to_datetime(df.odds_retrieved_at_utc,utc=True,errors="coerce")
    df=df.loc[(kickoff>now)&(kickoff<=now+pd.Timedelta(days=7))&
              (odds_at>=now-pd.Timedelta(hours=2))].copy()
    if df.empty:raise ValueError("No future games with fresh odds: refusing to publish")
    for field in ["edge_points","predicted_edge","model_home_margin","selected_spread","selected_price"]:
        df[field]=pd.to_numeric(df[field],errors="coerce")
    df=df.dropna(subset=["edge_points","predicted_edge","model_home_margin","selected_spread","selected_price"])
    if df.empty:raise ValueError("No finite predictions")
    df=df.sort_values("edge_points",ascending=False).head(5).copy()
    df["decision"]=df["decision"].where(df["decision"].eq("PAPER LEAN"),"PASS")
    df["research_status"]="UNVALIDATED FEATURE RECONSTRUCTION — PAPER ONLY"
    args.output.parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(args.output,index=False)
    print(f"Staged {len(df)} V4 research rows, {sum(df.decision=='PAPER LEAN')} paper leans")
if __name__=="__main__":main()
