#!/usr/bin/env python3
"""NFL anytime TD V3 scheduled RESEARCH predictions. No wagers or publishing."""
import argparse, json, base64, zlib
from datetime import datetime, timezone
from pathlib import Path
import joblib
import nflreadpy as nfl
import numpy as np
import pandas as pd

RAW = ["carries","targets","receptions","rushing_yards","receiving_yards","total_tds",
       "rush_inside_20","rush_inside_10","rush_inside_5",
       "targets_inside_20","targets_inside_10","targets_inside_5"]
DEF = ["rush_tds_allowed","receiving_tds_allowed","total_tds_allowed"]
POSITIONS = ["QB","RB","TE","WR"]

def frame(x):
    return x.to_pandas() if hasattr(x,"to_pandas") else pd.DataFrame(x)

def kickoff_times(g):
    naive = pd.to_datetime(g["gameday"].astype(str)+" "+g["gametime"].astype(str), errors="coerce")
    return naive.dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")

def run(outdir, modeldir):
    now = pd.Timestamp.now(tz="UTC")
    season = now.year
    schedules = frame(nfl.load_schedules(list(range(max(2021, season-5), season+1))))
    games = schedules[(schedules["game_type"]=="REG")].copy()
    games["kickoff_utc"] = kickoff_times(games)
    future = games[(games["kickoff_utc"]>now) & games["home_score"].isna() & games["away_score"].isna()].sort_values("kickoff_utc")
    if future.empty:
        print("No future regular-season games; exiting safely.")
        return
    week = int(future.iloc[0]["week"])
    future = future[future["week"]==week].copy()
    past = games[(games["kickoff_utc"]<now) & games["home_score"].notna() & games["away_score"].notna()]
    completed = set(past["game_id"].astype(str))
    if not completed:
        raise RuntimeError("No verified completed games")
    years = list(range(max(2021,season-5),season+1))
    stats = frame(nfl.load_player_stats(years))
    stats = stats[(stats["season_type"]=="REG") & stats["game_id"].astype(str).isin(completed)].copy()
    stats = stats[stats["position"].isin(POSITIONS)].copy()
    stats["player_id"] = stats["player_id"].astype(str)
    for c in ["carries","targets","receptions","rushing_yards","receiving_yards","rushing_tds","receiving_tds"]:
        if c not in stats: raise ValueError("Missing stats column "+c)
        stats[c] = pd.to_numeric(stats[c],errors="coerce").fillna(0)
    stats["total_tds"] = stats["rushing_tds"] + stats["receiving_tds"]
    pbp = frame(nfl.load_pbp(years))
    pbp = pbp[pbp["game_id"].astype(str).isin(completed)].copy()
    for c in ["yardline_100","rush_attempt","pass_attempt"]:
        if c not in pbp: raise ValueError("Missing PBP column "+c)
    pbp["yardline_100"] = pd.to_numeric(pbp["yardline_100"],errors="coerce")
    redzone = []
    for role,idcol,flag in [("rush","rusher_player_id","rush_attempt"),("targets","receiver_player_id","pass_attempt")]:
        if idcol not in pbp: raise ValueError("Missing PBP player ID "+idcol)
        subset = pbp[(pbp[flag]==1) & pbp["yardline_100"].between(1,20)].copy()
        subset["player_id"] = subset[idcol].astype(str)
        for limit in [20,10,5]:
            subset[f"{role}_inside_{limit}"] = (subset["yardline_100"]<=limit).astype(int)
        grouped = subset.groupby(["game_id","player_id"],as_index=False)[[f"{role}_inside_{x}" for x in [20,10,5]]].sum()
        redzone.append(grouped)
    for rz in redzone:
        stats = stats.merge(rz,on=["game_id","player_id"],how="left",validate="many_to_one")
    for c in RAW:
        stats[c] = pd.to_numeric(stats[c],errors="coerce").fillna(0)
    stats = stats.sort_values(["player_id","season","week","game_id"])
    recent = stats[(stats["season"]==season)].sort_values(["week","game_id"]).drop_duplicates("player_id",keep="last")
    last_week = int(past[past["season"]==season]["week"].max()) if (past["season"]==season).any() else 0
    # Never infer a player is active merely from historical stats.
    recent = recent[(last_week-recent["week"])<=2].copy()
    counts = stats.groupby("player_id").size()
    recent = recent[recent["player_id"].map(counts).fillna(0)>=3]
    matchups = pd.concat([
        future[["game_id","home_team","away_team","kickoff_utc"]].rename(columns={"home_team":"team","away_team":"opponent"}),
        future[["game_id","away_team","home_team","kickoff_utc"]].rename(columns={"away_team":"team","home_team":"opponent"})
    ],ignore_index=True)
    # Historical player-game ID must not shadow the upcoming matchup game ID.
    recent = recent.rename(columns={"game_id":"last_played_game_id"})
    pool = recent.merge(matchups,on="team",how="inner",validate="many_to_one")
    if pool.empty: raise RuntimeError("No eligible candidate players")
    feature_rows=[]
    for pid,g in stats.groupby("player_id"):
        g=g.tail(5)
        row={"player_id":pid}
        for col in RAW:
            for n in (3,5): row[f"{col}_last{n}"]=float(g[col].tail(n).mean())
        feature_rows.append(row)
    pool=pool.merge(pd.DataFrame(feature_rows),on="player_id",how="left",validate="many_to_one")
    # TDs conceded are aggregated from opponent player-game stats, matching V3 training.
    defensive=stats.groupby(["game_id","opponent_team"],as_index=False).agg(
        rush_tds_allowed=("rushing_tds","sum"),
        receiving_tds_allowed=("receiving_tds","sum"),
        total_tds_allowed=("total_tds","sum"))
    defensive=defensive.rename(columns={"opponent_team":"opponent"})
    defensive=defensive.merge(past[["game_id","season","week"]],on="game_id",how="inner",validate="many_to_one")
    defensive=defensive.sort_values(["opponent","season","week","game_id"])
    def_rows=[]
    for opponent,g in defensive.groupby("opponent"):
        g=g.tail(5)
        row={"opponent":opponent}
        for col in DEF:
            for n in (3,5): row[f"{col}_last{n}"]=float(g[col].tail(n).mean())
        def_rows.append(row)
    pool=pool.merge(pd.DataFrame(def_rows),on="opponent",how="left",validate="many_to_one")
    for pos in POSITIONS: pool[f"position_{pos}"]=(pool["position"]==pos).astype(int)
    compressed=(modeldir/"fitted_coefficients.txt").read_text().strip()
    fitted=json.loads(zlib.decompress(base64.b64decode(compressed)))
    cols=fitted["features"]
    if len(cols)!=34 or len(pool)!=len(pool[["game_id","player_id"]].drop_duplicates()):
        raise RuntimeError("Feature count or candidate uniqueness failed")
    X=pool[cols].apply(pd.to_numeric,errors="coerce")
    if not np.isfinite(X.to_numpy()).all(): raise RuntimeError("Invalid model features")
    # Exact StandardScaler + LogisticRegression + sigmoid-calibrator arithmetic.
    z=(X.to_numpy(dtype=float)-np.array(fitted["mean"]))/np.array(fitted["scale"])
    linear=z@np.array(fitted["coef"])+fitted["intercept"]
    raw=1/(1+np.exp(-np.clip(linear,-700,700)))
    raw=np.clip(raw,1e-6,1-1e-6)
    logit=np.log(raw/(1-raw))
    calibrated_linear=logit*fitted["cal_coef"]+fitted["cal_intercept"]
    p=1/(1+np.exp(-np.clip(calibrated_linear,-700,700)))
    out=pool[["player_id","player_name","position","team","opponent","game_id","kickoff_utc"]].copy()
    out["td_probability"]=p
    out["run_timestamp_utc"]=now.isoformat()
    out["status"]="RESEARCH_ONLY_UNVERIFIED_ROSTER"
    out["odds_status"]="NO_ANYTIME_TD_ODDS"
    out=out.sort_values("td_probability",ascending=False)
    outdir.mkdir(parents=True,exist_ok=True)
    dest=outdir/f"nfl_td_v3_{season}_week{week}_{now.strftime('%Y%m%dT%H%M%SZ')}.csv"
    out.to_csv(dest,index=False)
    print(f"Saved {len(out)} unverified research projections to {dest}; no betting picks published.")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",default="research_snapshots/nfl_td")
    parser.add_argument("--model-dir",default="automation/models/nfl_td_v3")
    args=parser.parse_args()
    run(Path(args.output_dir),Path(args.model_dir))
