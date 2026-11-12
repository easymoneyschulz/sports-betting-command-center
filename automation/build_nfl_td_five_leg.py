#!/usr/bin/env python3
"""Build a research-only five-leg TD parlay from frozen V3 predictions and verified odds."""
import argparse
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

def decimal_odds(american):
    a=float(american)
    if a==0 or -100<a<100: raise ValueError("Invalid American odds")
    return 1+a/100 if a>0 else 1+100/abs(a)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--predictions",default="public_data/nfl_td_v3_latest.csv")
    p.add_argument("--odds",default="public_data/nfl_td_verified_odds.csv")
    p.add_argument("--output",default="public_data/nfl_td_five_leg_latest.json")
    a=p.parse_args()
    now=pd.Timestamp.now(tz="UTC")
    result={"generated_at_utc":now.isoformat(),"strategy":"V3 five-leg TD long shot","status":"NO_PLAY",
            "reason":"No verified current anytime TD odds available","legs":[]}
    odds_path=Path(a.odds)
    if odds_path.exists():
        pred=pd.read_csv(a.predictions,dtype={"game_id":str,"player_id":str})
        odds=pd.read_csv(odds_path,dtype={"game_id":str,"player_id":str})
        required={"game_id","player_id","american_odds","sportsbook","odds_timestamp_utc"}
        if not required.issubset(odds.columns): raise ValueError("Odds missing required fields")
        if odds.duplicated(["game_id","player_id"]).any(): raise ValueError("Ambiguous odds: duplicate player/game")
        odds["odds_timestamp_utc"]=pd.to_datetime(odds.odds_timestamp_utc,utc=True,errors="coerce")
        if odds.odds_timestamp_utc.isna().any(): raise ValueError("Invalid odds timestamp")
        merged=pred.merge(odds,on=["game_id","player_id"],how="inner",validate="one_to_one")
        if not merged.empty:
            merged["kickoff_utc"]=pd.to_datetime(merged.kickoff_utc,utc=True,errors="coerce")
            merged["run_timestamp_utc"]=pd.to_datetime(merged.run_timestamp_utc,utc=True,errors="coerce")
            merged["td_probability"]=pd.to_numeric(merged.td_probability,errors="coerce")
            merged["american_odds"]=pd.to_numeric(merged.american_odds,errors="coerce")
            merged=merged[(merged.kickoff_utc>now)&(merged.run_timestamp_utc<merged.kickoff_utc)&
                          (merged.odds_timestamp_utc<=now)&(merged.odds_timestamp_utc>=now-pd.Timedelta(hours=24))&
                          merged.td_probability.between(.20,.95)&merged.american_odds.notna()&
                          merged.sportsbook.notna()]
            merged=merged.copy()
            if not merged.empty:
                merged["decimal_odds"]=merged.american_odds.map(decimal_odds)
                merged["edge"]=merged.td_probability-1/merged.decimal_odds
                merged=merged.sort_values(["edge","td_probability"],ascending=False).head(35)
                best=None
                best_target=None
                # Show a clearly labeled research candidate even when the target
                # payout/edge conditions cannot all be satisfied.
                for combo in itertools.combinations(merged.to_dict("records"),5):
                    if len({x["game_id"] for x in combo})!=5: continue
                    if len({x["sportsbook"] for x in combo})!=1: continue
                    payout=1.
                    prob=1.
                    for x in combo:
                        payout*=x["decimal_odds"]
                        prob*=x["td_probability"]
                    american=(payout-1)*100
                    expected_multiplier=prob*payout
                    # Prefer higher estimated probability, then estimated value,
                    # for long shots within the requested payout range.
                    if 2000<=american<=6000:
                        score=(prob,expected_multiplier)
                        if best_target is None or score>best_target[0]:
                            best_target=(score,combo,american,prob)
                    # Fallback: nearest odds range, then strongest hit probability.
                    distance=max(2000-american,0,american-6000)
                    fallback_score=(-distance,prob,expected_multiplier)
                    if best is None or fallback_score>best[0]:
                        best=(fallback_score,combo,american,prob)
                selected=best_target if best_target is not None else best
                best=selected
                if best:
                    _,combo,american,prob=best
                    result.update(status="PAPER_PICK",reason=("Research candidate within target odds; not a recommended wager" if best_target else "Closest available five-leg research candidate; outside target odds"),
                                  combined_american_odds=round(american),estimated_hit_probability_independence=round(prob,5),
                                  estimated_profit_on_20=round(20*american/100,2),
                                  legs=[{"player_name":x["player_name"],"player_id":x["player_id"],
                                         "game_id":x["game_id"],"team":x["team"],"opponent":x["opponent"],
                                         "td_probability":round(x["td_probability"],4),
                                         "american_odds":int(x["american_odds"]),"sportsbook":x["sportsbook"],
                                         "edge":round(x["edge"],4)} for x in combo])
                else:
                    result["reason"]="Fewer than five eligible players from distinct games at one sportsbook"
    out=Path(a.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print(result["status"],result["reason"])
if __name__=="__main__": main()
