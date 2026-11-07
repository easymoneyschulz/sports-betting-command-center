"""Run the frozen CFB V4 model on a freshly built 27-feature weekly CSV.

This does not fetch schedules/odds or mutate historical trackers.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


def run(source: Path, model_path: Path, features_path: Path, output: Path):
    features = json.loads(features_path.read_text())
    model = joblib.load(model_path)
    df = pd.read_csv(source)
    if df.empty:
        raise ValueError("No games supplied")
    required = set(features) | {"game_id", "start_date", "home_team", "away_team",
                                 "home_spread", "home_price", "away_price", "over_under"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing input columns: {missing}")
    if df.game_id.astype(str).duplicated().any():
        raise ValueError("Duplicate game IDs")
    if list(getattr(model, "feature_names_in_", features)) != features:
        raise ValueError("Frozen model feature order mismatch")
    X = df[features].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(X.to_numpy(dtype=float)).all():
        raise ValueError("Missing or nonfinite model features; refusing to guess")
    kickoff = pd.to_datetime(df["start_date"], utc=True, errors="coerce")
    if kickoff.isna().any():
        raise ValueError("Invalid kickoff timestamp")
    now = pd.Timestamp.now(tz="UTC")
    if (kickoff <= now).any():
        raise ValueError("Input contains started games; refusing to republish stale picks")
    if (kickoff > now + pd.Timedelta(days=14)).any():
        raise ValueError("Input contains games more than 14 days away")
    correction = model.predict(X)
    if not np.isfinite(correction).all():
        raise ValueError("Nonfinite model predictions")
    out = df.copy()
    out["model_correction"] = correction
    out["market_home_margin"] = -pd.to_numeric(out["home_spread"])
    out["model_home_margin"] = out["market_home_margin"] + correction
    out["predicted_edge"] = correction
    out["edge_points"] = np.abs(correction)
    home = correction > 0
    out["selected_side"] = np.where(home, out["home_team"], out["away_team"])
    out["selected_spread"] = np.where(home, out["home_spread"], -out["home_spread"])
    out["selected_price"] = np.where(home, out["home_price"], out["away_price"])
    out["decision"] = np.where(out["edge_points"] >= 3, "PAPER LEAN", "PASS")
    out["prediction_timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    out["model_version"] = "V4"
    out = out.sort_values("edge_points", ascending=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".tmp")
    out.to_csv(temp, index=False)
    temp.replace(output)
    print(f"Generated {len(out)} predictions; {(out.decision == 'PAPER LEAN').sum()} paper leans")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.input, args.model, args.features, args.output)
