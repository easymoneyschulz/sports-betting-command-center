"""Conservative NBA pregame participation verification from ESPN event data.

Never infer a starting lineup from prior games. Only explicit starter/out flags
are reported; otherwise status remains UNCONFIRMED.
"""
from pathlib import Path
import pandas as pd
import requests
ROOT=Path(__file__).resolve().parents[1]/"public_data"
FILE=ROOT/"nba_v2_recovered_prop_comparison.csv"
def main():
    if not FILE.exists():return
    df=pd.read_csv(FILE,dtype={"game_id":str,"player_id":str})
    if not {"game_id","player_id","decision"}.issubset(df):raise ValueError("Invalid comparison schema")
    df["lineup_status"]="UNCONFIRMED"
    df["participation_source"]="ESPN_EVENT_SUMMARY"
    for gid,idx in df.groupby("game_id").groups.items():
        try:
            r=requests.get("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary",params={"event":gid},timeout=25)
            r.raise_for_status()
            data=r.json()
            athletes={}
            # Pregame roster info is often absent. Do not infer from projected starters.
            for team in data.get("boxscore",{}).get("players",[]):
                for group in team.get("statistics",[]):
                    for a in group.get("athletes",[]):
                        person=a.get("athlete",{})
                        pid=str(person.get("id",""))
                        if pid:athletes[pid]=a
            for row in idx:
                pid=str(df.at[row,"player_id"])
                a=athletes.get(pid)
                if a is None:continue
                if a.get("didNotPlay") is True:
                    df.at[row,"lineup_status"]="OUT_CONFIRMED"
                    df.at[row,"decision"]="WAIT"
                elif a.get("starter") is True:
                    df.at[row,"lineup_status"]="STARTER_CONFIRMED"
                elif a.get("starter") is False and a.get("didNotPlay") is False:
                    df.at[row,"lineup_status"]="BENCH_CONFIRMED"
        except (requests.RequestException,ValueError,KeyError) as e:
            print("Lineup source unavailable for",gid,str(e)[:100])
    df.to_csv(FILE,index=False)
    print("Participation verification:",df.lineup_status.value_counts().to_dict())
if __name__=="__main__":main()
