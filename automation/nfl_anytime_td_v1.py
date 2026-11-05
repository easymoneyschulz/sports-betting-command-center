"""NFL anytime offensive touchdown probability research (not live picks).

Input: one row per player/game with columns:
season, week, game_id, player_id, player_name, position, team,
rush_attempts, targets, rushing_tds, receiving_tds
Optional: opponent, game_date. Inputs must be actual historical game logs.
No future game information is used in feature construction.
Run: python automation/nfl_anytime_td_v1.py --input data/player_games.csv --out outputs/td_v1
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

REQUIRED = {"season","week","game_id","player_id","player_name","position","team",
            "rush_attempts","targets","rushing_tds","receiving_tds"}
NUMERIC = ["rush_attempts","targets","rushing_tds","receiving_tds"]
FEATURES = ["prior_games","rushes_last3","targets_last3","rushes_last8",
            "targets_last8","td_rate_last8","team","position"]
POSITIONS = {"QB","RB","WR","TE"}

def prepare(raw):
    missing = REQUIRED - set(raw.columns)
    if missing:
        raise ValueError("Missing input columns: " + ", ".join(sorted(missing)))
    df = raw.copy()
    df = df[df.position.astype(str).str.upper().isin(POSITIONS)].copy()
    if df.empty:
        raise ValueError("No eligible QB/RB/WR/TE game rows")
    df["position"] = df.position.str.upper()
    for col in NUMERIC + ["season","week"]:
        df[col] = pd.to_numeric(df[col], errors="raise")
    if (df[NUMERIC] < 0).any().any():
        raise ValueError("Negative opportunity or touchdown counts")
    if df.duplicated(["game_id","player_id"]).any():
        raise ValueError("Duplicate player/game rows")
    df = df.sort_values(["player_id","season","week","game_id"]).reset_index(drop=True)
    df["any_td"] = ((df.rushing_tds + df.receiving_tds) >= 1).astype(int)
    # Player-specific lagged rolling features: game N cannot see game N's result.
    grouped = df.groupby("player_id", sort=False)
    df["prior_games"] = grouped.cumcount()
    for col, prefix in [("rush_attempts","rushes"),("targets","targets")]:
        for n in (3,8):
            df[f"{prefix}_last{n}"] = grouped[col].transform(
                lambda s: s.shift(1).rolling(n, min_periods=1).mean()
            )
    df["td_rate_last8"] = grouped["any_td"].transform(
        lambda s: s.shift(1).rolling(8, min_periods=1).mean()
    )
    return df

def make_pipeline():
    numeric = [x for x in FEATURES if x not in ("team","position")]
    transform = ColumnTransformer([
        ("num", Pipeline([("fill", SimpleImputer(strategy="constant",fill_value=0)),
                          ("scale",StandardScaler())]), numeric),
        ("cat", OneHotEncoder(handle_unknown="ignore"), ["team","position"])
    ])
    return Pipeline([("features",transform),
                     ("model",LogisticRegression(max_iter=1000, C=0.5))])

def backtest(df, first_test_season=2023):
    # Strict season-forward evaluation; train only on earlier seasons.
    rows, metrics = [], []
    for season in sorted(df.season.unique()):
        if season < first_test_season:
            continue
        train = df[(df.season < season) & (df.prior_games >= 1)]
        test = df[(df.season == season) & (df.prior_games >= 1)]
        if len(train) < 100 or len(test) < 20 or train.any_td.nunique() < 2:
            continue
        model = make_pipeline()
        model.fit(train[FEATURES], train.any_td)
        probs = model.predict_proba(test[FEATURES])[:,1]
        scored = test[["season","week","game_id","player_id","player_name","position",
                       "team","any_td"]].copy()
        scored["p_any_td"] = probs
        rows.append(scored)
        metrics.append({
            "test_season":int(season), "train_games":len(train), "test_games":len(test),
            "brier":float(brier_score_loss(test.any_td,probs)),
            "log_loss":float(log_loss(test.any_td,probs,labels=[0,1])),
            "auc":float(roc_auc_score(test.any_td,probs)) if test.any_td.nunique()==2 else np.nan,
            "actual_td_rate":float(test.any_td.mean()),
            "mean_predicted_td_rate":float(probs.mean())
        })
    return (pd.concat(rows,ignore_index=True) if rows else pd.DataFrame(),
            pd.DataFrame(metrics))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",required=True)
    parser.add_argument("--out",default="outputs/nfl_anytime_td_v1")
    parser.add_argument("--first-test-season",type=int,default=2023)
    args=parser.parse_args()
    df=prepare(pd.read_csv(args.input))
    predictions,metrics=backtest(df,args.first_test_season)
    if metrics.empty:
        raise SystemExit("Insufficient earlier-season data for a legitimate forward backtest.")
    out=Path(args.out)
    out.mkdir(parents=True,exist_ok=True)
    predictions.to_csv(out/"season_forward_predictions.csv",index=False)
    metrics.to_csv(out/"season_forward_metrics.csv",index=False)
    print(metrics.to_string(index=False))
    print("Research only: no odds, value picks, or live publishing.")

if __name__=="__main__":
    main()
