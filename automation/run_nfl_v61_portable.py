#!/usr/bin/env python3
"""
NFL V6.1 portable paper-test runner.

Requires independently supplied feature and market CSV files.
Does not download sportsbook odds or publish predictions.
"""

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent

MODEL_HASH = (
    "18ee19e1f38908d40ca420d06c05213ae802418a99ea6a999de378e139e5483e"
)
RULES_HASH = (
    "f927f3a6153d4cf3597a67d39c41e43e2cd8bd1b4da70ec2713bda32dc5ea66b"
)

def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", required=True)
    parser.add_argument("--market", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--odds-verified",
        action="store_true",
        help="Operator attests odds are genuine pregame sportsbook snapshots."
    )
    args = parser.parse_args()

    features_path = Path(args.features).resolve()
    market_path = Path(args.market).resolve()
    output_path = Path(args.output).resolve()
    model_dir = BASE / "models"

    for path in [features_path, market_path]:
        if not path.is_file():
            raise FileNotFoundError(path)

    model_path = model_dir / "nfl_v61_frozen_2026_model.joblib"
    rules_path = model_dir / "nfl_v61_step32_frozen_rules.json"

    if file_hash(model_path) != MODEL_HASH:
        raise RuntimeError("Frozen model hash mismatch")

    if file_hash(rules_path) != RULES_HASH:
        raise RuntimeError("Frozen rules hash mismatch")

    features = pd.read_csv(features_path)
    market = pd.read_csv(market_path)

    required_market = {
        "game_id",
        "spread_line",
        "away_spread_odds",
        "home_spread_odds",
    }

    missing = required_market - set(market.columns)
    if missing:
        raise ValueError(f"Missing market columns: {sorted(missing)}")

    if features.empty or market.empty:
        raise ValueError("Feature or market file is empty")

    if features["game_id"].duplicated().any():
        raise ValueError("Duplicate feature game IDs")

    if market["game_id"].duplicated().any():
        raise ValueError("Duplicate market game IDs")

    if not args.odds_verified:
        print("WARNING: Odds are not independently verified.")
        print("Output will be marked RESEARCH_ONLY.")

    spec = importlib.util.spec_from_file_location(
        "frozen_nfl_v61_runner",
        BASE / "run_nfl_v61.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    result = module.run_nfl(
        model_dir,
        features_path,
        market_path
    )

    if not isinstance(result, pd.DataFrame):
        raise TypeError(
            f"Expected DataFrame; got {type(result).__name__}"
        )

    if result.empty:
        raise ValueError("Frozen runner returned no games")

    result = result.copy()
    result["run_timestamp_utc"] = (
        datetime.now(timezone.utc).isoformat()
    )
    result["data_status"] = (
        "OPERATOR_ATTESTED_ODDS"
        if args.odds_verified
        else "RESEARCH_ONLY"
    )
    result["publication_status"] = "NOT_PUBLISHED"
    result["features_sha256"] = file_hash(features_path)
    result["market_sha256"] = file_hash(market_path)

    if output_path.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing snapshot: {output_path}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)

    print("=" * 65)
    print("NFL V6.1 PORTABLE PAPER RUN")
    print("=" * 65)
    print("Games:", len(result))
    print("Output:", output_path)
    print("Odds status:", result["data_status"].iloc[0])
    print("Publication: DISABLED")
    print("Model hash verified: True")
    print("Rules hash verified: True")
    print("Historical predictions: UNCHANGED")

if __name__ == "__main__":
    main()
