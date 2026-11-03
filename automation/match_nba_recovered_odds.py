"""Match current two-sided PropLine quotes to roster-verified recovered NBA V2 cards.
Never create model predictions or infer missing sportsbook prices.
"""
from pathlib import Path
import pandas as pd
import unicodedata

ROOT = Path(__file__).resolve().parents[1] / "public_data"
CARDS = ROOT / "nba_v2_recovered_prop_comparison.csv"
ODDS = ROOT / "nba_v2_propline_odds.csv"
CODES = dict(zip(
    ["Atlanta Hawks","Boston Celtics","Brooklyn Nets","Charlotte Hornets","Chicago Bulls",
     "Cleveland Cavaliers","Dallas Mavericks","Denver Nuggets","Detroit Pistons",
     "Golden State Warriors","Houston Rockets","Indiana Pacers","LA Clippers",
     "Los Angeles Clippers","Los Angeles Lakers","Memphis Grizzlies","Miami Heat",
     "Milwaukee Bucks","Minnesota Timberwolves","New Orleans Pelicans","New York Knicks",
     "Oklahoma City Thunder","Orlando Magic","Philadelphia 76ers","Phoenix Suns",
     "Portland Trail Blazers","Sacramento Kings","San Antonio Spurs","Toronto Raptors",
     "Utah Jazz","Washington Wizards"],
    ["ATL","BOS","BKN","CHA","CHI","CLE","DAL","DEN","DET","GSW","HOU","IND",
     "LAC","LAC","LAL","MEM","MIA","MIL","MIN","NOP","NYK","OKC","ORL","PHI",
     "PHX","POR","SAC","SAS","TOR","UTA","WAS"]
))
def key(s):
    return "".join(c for c in unicodedata.normalize("NFKD",str(s)) if c.isalnum()).casefold()

def main():
    if not CARDS.exists() or not ODDS.exists():
        print("No verified comparison or odds; preserving snapshot")
        return
    cards = pd.read_csv(CARDS, dtype={"player_id":str})
    odds = pd.read_csv(ODDS)
    required_cards = {"game_date","player_name","team","opponent","roster_verified","v2_projection"}
    required_odds = {"commence_time","player_name","home_team","away_team","market_line",
                     "over_price","under_price","sportsbook","odds_timestamp_utc"}
    if not required_cards.issubset(cards) or not required_odds.issubset(odds):
        raise ValueError("Missing required comparison or odds columns")
    now = pd.Timestamp.now(tz="UTC")
    odds["tip"] = pd.to_datetime(odds.commence_time,utc=True,errors="coerce")
    odds["quoted"] = pd.to_datetime(odds.odds_timestamp_utc,utc=True,errors="coerce")
    odds["date"] = odds.tip.dt.tz_convert("America/Chicago").dt.strftime("%Y-%m-%d")
    odds["home_code"] = odds.home_team.map(CODES)
    odds["away_code"] = odds.away_team.map(CODES)
    odds["name_key"] = odds.player_name.map(key)
    for col in ("market_line","over_price","under_price"):
        odds[col] = pd.to_numeric(odds[col],errors="coerce")
    odds = odds[(odds.tip > now) & (odds.quoted <= now) &
                (odds.quoted >= now-pd.Timedelta(hours=24)) &
                odds[["market_line","over_price","under_price"]].notna().all(axis=1)].copy()
    cards["name_key"] = cards.player_name.map(key)
    cards["date"] = pd.to_datetime(cards.game_date,errors="coerce").dt.strftime("%Y-%m-%d")
    cards["row_id"] = range(len(cards))
    valid = cards.roster_verified.astype(str).str.lower().eq("true")
    joined = cards[valid].merge(odds,on=["name_key","date"],suffixes=("","_odds"))
    joined = joined[((joined.team==joined.home_code)&(joined.opponent==joined.away_code)) |
                    ((joined.team==joined.away_code)&(joined.opponent==joined.home_code))]
    # Fail closed when two games could match a single player.
    ambiguity = joined.groupby("row_id")["tip"].nunique()
    joined = joined[~joined.row_id.isin(ambiguity[ambiguity>1].index)]
    joined = joined.sort_values(["quoted","sportsbook"],ascending=[False,True]).drop_duplicates("row_id")
    for field in ("market_line","over_price","under_price","sportsbook","odds_timestamp_utc","edge"):
        if field not in cards: cards[field] = pd.NA
    cards["decision"] = "WAIT"
    cards[["market_line","over_price","under_price","sportsbook","odds_timestamp_utc","edge"]] = pd.NA
    for _, q in joined.iterrows():
        i=int(q.row_id)
        projection=pd.to_numeric(cards.at[i,"v2_projection"],errors="coerce")
        if pd.isna(projection): continue
        edge=float(projection)-float(q.market_line)
        for field in ("market_line","over_price","under_price","sportsbook","odds_timestamp_utc"):
            cards.at[i,field]=q[field]
        cards.at[i,"edge"]=edge
        cards.at[i,"decision"]="PASS" if abs(edge)<3 else ("OVER" if edge>0 else "UNDER")
    cards=cards.drop(columns=["name_key","date","row_id"])
    cards.to_csv(CARDS,index=False)
    print(f"Matched {len(joined)} verified player/game sportsbook lines of {len(cards)} cards")
    print(cards.decision.value_counts().to_dict())

if __name__=="__main__": main()
