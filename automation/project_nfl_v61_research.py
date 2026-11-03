import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "models/nfl_v61_frozen_2026_model.joblib"
RULES_PATH = ROOT / "models/nfl_v61_step32_frozen_rules.json"

EXPECTED_MODEL_SHA = (
    "18ee19e1f38908d40ca420d06c05213ae802418a99ea6a999de378e139e5483e"
)
EXPECTED_RULES_SHA = (
    "f927f3a6153d4cf3597a67d39c41e43e2cd8bd1b4da70ec2713bda32dc5ea66b"
)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    if sha256(MODEL_PATH) != EXPECTED_MODEL_SHA:
        raise RuntimeError("Frozen model hash mismatch")

    if sha256(RULES_PATH) != EXPECTED_RULES_SHA:
        raise RuntimeError("Frozen rules hash mismatch")

    import json
    rules = json.loads(RULES_PATH.read_text())

    model = joblib.load(MODEL_PATH)
    features = pd.read_csv(args.features)

    required_meta = [
        "game_id",
        "season",
        "week",
        "home_team",
        "away_team",
        "game_status",
    ]

    missing_meta = [
        col for col in required_meta
        if col not in features.columns
    ]

    if missing_meta:
        raise RuntimeError(
            f"Missing metadata columns: {missing_meta}"
        )

    features = features[
        features["game_status"] == "UPCOMING"
    ].copy()

    if features.empty:
        print("No upcoming games. No projection file generated.")
        return

    # The frozen model is a dictionary containing
    # the trained pipeline and its ordered feature list.
    if not isinstance(model, dict):
        raise RuntimeError("Unexpected frozen model structure")

    if "pipeline" not in model or "features" not in model:
        raise RuntimeError("Missing frozen model components")

    feature_columns = model["features"]
    frozen_rule_features = rules["model"]["features"]

    if (
        not isinstance(feature_columns, list)
        or len(feature_columns) != 27
        or feature_columns != frozen_rule_features
    ):
        raise RuntimeError(
            "Frozen model features do not match frozen rules"
        )

    missing_features = [
        col for col in feature_columns
        if col not in features.columns
    ]

    if missing_features:
        raise RuntimeError(
            f"Missing model features: {missing_features}"
        )

    X = features[feature_columns].apply(
        pd.to_numeric, errors="coerce"
    )

    if not np.isfinite(X.to_numpy(dtype=float)).all():
        raise RuntimeError(
            "Invalid or missing numeric model features"
        )

    predictions = model['pipeline'].predict(X)

    result = features[
        [
            "game_id",
            "season",
            "week",
            "home_team",
            "away_team",
        ]
    ].copy()

    result["model_home_margin"] = predictions
    result["model_away_margin"] = -predictions
    result["prediction_type"] = "RESEARCH_PROJECTION"
    result["odds_status"] = "NOT_VERIFIED"
    result["betting_decision"] = "NO_BET"
    result["publication_status"] = "NOT_PUBLISHED"
    result["run_timestamp_utc"] = (
        datetime.now(timezone.utc).isoformat()
    )
    result["source_features_sha256"] = sha256(args.features)
    result["frozen_model_sha256"] = EXPECTED_MODEL_SHA

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    season = int(result["season"].iloc[0])
    week = int(result["week"].iloc[0])

    output = output_dir / (
        f"nfl_v61_research_projection_"
        f"{season}_week{week}_{stamp}.csv"
    )

    if output.exists():
        raise FileExistsError(output)

    result.to_csv(output, index=False)

    print("Saved:", output)
    print("Games projected:", len(result))
    print("Odds: NOT_VERIFIED")
    print("Betting decisions: NO_BET")
    print("Publication: DISABLED")


if __name__ == "__main__":
    main()
