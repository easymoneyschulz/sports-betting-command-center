#!/usr/bin/env python3
"""Fail-closed research-only NFL anytime TD V3 model runner.

Requires frozen model artifacts and a pregame feature CSV produced by an
independently audited data builder. No wagers or website publication.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

def run(model_dir: Path, input_file: Path, output_dir: Path):
    with (model_dir / "metadata.json").open(encoding="utf-8") as f:
        metadata = json.load(f)
    names = metadata["v3_features"]
    if len(names) != 34 or len(set(names)) != 34:
        raise ValueError("Expected exactly 34 distinct frozen features")
    model = joblib.load(model_dir / "nfl_td_v3.joblib")
    calibrator = joblib.load(model_dir / "nfl_td_sigmoid.joblib")
    if list(model.feature_names_in_) != names:
        raise ValueError("Model and metadata feature order differ")
    data = pd.read_csv(input_file)
    required = ["player_id", "player_name", "position", "team", "opponent",
                "game_id", "kickoff_utc", *names]
    missing = sorted(set(required) - set(data.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if data.player_id.duplicated().any():
        raise ValueError("Duplicate player IDs")
    kickoff = pd.to_datetime(data.kickoff_utc, utc=True, errors="coerce")
    now = pd.Timestamp.now(tz="UTC")
    if kickoff.isna().any() or (kickoff <= now).any():
        raise ValueError("Started games or invalid kickoff times: fail closed")
    x = data[names].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(x.to_numpy()).all():
        raise ValueError("Invalid model inputs")
    for pos in ("QB", "RB", "WR", "TE"):
        if not (data[f"position_{pos}"] == data.position.eq(pos).astype(int)).all():
            raise ValueError("Position indicator mismatch")
    raw = model.predict_proba(x)[:, 1]
    p = np.clip(raw, 1e-6, 1 - 1e-6)
    calibrated = calibrator.predict_proba(
        np.log(p / (1 - p)).reshape(-1, 1)
    )[:, 1]
    result = data[["player_id", "player_name", "position", "team", "opponent",
                   "game_id", "kickoff_utc"]].copy()
    result["raw_probability"] = raw
    result["td_probability"] = calibrated
    result["status"] = "RESEARCH_ONLY_UNVERIFIED"
    result["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    result = result.sort_values("td_probability", ascending=False)
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / ("nfl_td_v3_research_" +
                         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".csv")
    result.to_csv(dest, index=False)
    print(f"Research predictions: {len(result)} | {dest}")
    print("Betting picks: DISABLED | Website publishing: DISABLED")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, default=Path("automation/models/nfl_td_v3"))
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("research_snapshots/nfl_td"))
    args = parser.parse_args()
    run(args.model_dir, args.features, args.output_dir)
