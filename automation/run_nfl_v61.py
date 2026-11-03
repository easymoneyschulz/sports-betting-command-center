
from pathlib import Path
import json
import joblib
import pandas as pd
import numpy as np


def run_nfl(model_dir, features_file, market_file):
    model_dir = Path(model_dir)

    bundle = joblib.load(
        model_dir / "nfl_v61_frozen_2026_model.joblib"
    )

    with open(
        model_dir / "nfl_v61_step32_frozen_rules.json",
        encoding="utf-8"
    ) as f:
        rules = json.load(f)

    features = pd.read_csv(features_file)
    market = pd.read_csv(market_file)

    feature_cols = bundle["features"]

    if feature_cols != rules["model"]["features"]:
        raise ValueError("Frozen model feature mismatch")

    required = ["game_id", *feature_cols]
    missing = [c for c in required if c not in features]
    if missing:
        raise ValueError(f"Missing features: {missing}")

    if features["game_id"].duplicated().any():
        raise ValueError("Duplicate feature game IDs")

    required_market = [
        "game_id", "spread_line",
        "away_spread_odds", "home_spread_odds"
    ]
    missing_market = [
        c for c in required_market if c not in market
    ]
    if missing_market:
        raise ValueError(f"Missing market columns: {missing_market}")

    if market["game_id"].duplicated().any():
        raise ValueError("Duplicate market game IDs")

    X = features[feature_cols].apply(
        pd.to_numeric, errors="coerce"
    )

    if not np.isfinite(X.to_numpy()).all():
        raise ValueError("Invalid model features")

    predictions = features[
        ["game_id", "season", "week",
         "gameday", "away_team", "home_team"]
    ].copy()

    predictions["model_correction"] = (
        bundle["pipeline"].predict(X)
    )

    predictions = predictions.merge(
        market[required_market],
        on="game_id",
        how="left",
        validate="one_to_one"
    )

    for col in required_market[1:]:
        predictions[col] = pd.to_numeric(
            predictions[col], errors="coerce"
        )

    # nflverse schedule convention:
    # spread_line > 0 means home team favored.
    # The frozen model predicts market residual.
    predictions["market_home_margin"] = (
        predictions["spread_line"]
    )

    predictions["projected_home_margin"] = (
        predictions["market_home_margin"]
        + predictions["model_correction"]
    )

    predictions["edge"] = predictions[
        "model_correction"
    ].abs()

    predictions["selected_side"] = np.where(
        predictions["model_correction"] > 0,
        predictions["home_team"],
        predictions["away_team"]
    )

    predictions["selected_spread"] = np.where(
        predictions["model_correction"] > 0,
        -predictions["market_home_margin"],
        predictions["market_home_margin"]
    )

    predictions["selected_price"] = np.where(
        predictions["model_correction"] > 0,
        predictions["home_spread_odds"],
        predictions["away_spread_odds"]
    )

    minimum = rules["selection"]["min_abs_edge_inclusive"]
    maximum = rules["selection"]["max_abs_edge_exclusive"]
    limit = rules["selection"]["max_picks_per_week"]

    predictions["decision"] = "PASS"

    eligible = (
        predictions["edge"].ge(minimum)
        & predictions["edge"].lt(maximum)
        & predictions["selected_price"].notna()
    )

    ranked = predictions.loc[eligible].sort_values(
        ["season", "week", "edge", "game_id"],
        ascending=[True, True, False, True]
    )

    selected_indices = (
        ranked.groupby(["season", "week"])
        .head(limit)
        .index
    )

    predictions.loc[
        selected_indices, "decision"
    ] = "PAPER LEAN"

    return predictions.sort_values(
        ["season", "week", "edge"],
        ascending=[True, True, False]
    ).reset_index(drop=True)


if __name__ == "__main__":
    root = Path(
        "/content/drive/MyDrive/NFL_Betting_Model_V1"
    )

    results = run_nfl(
        model_dir=root,
        features_file=(
            root / "nfl_v61_2026_step45_week9_features.csv"
        ),
        market_file=(
            root / "nfl_v61_2026_step44_week9_schedule.csv"
        )
    )

    print("=" * 65)
    print("NFL V6.1 — AUTOMATION TEST")
    print("=" * 65)

    columns = [
        "game_id", "selected_side",
        "selected_spread", "selected_price",
        "edge", "decision"
    ]

    print(results[columns].to_string(index=False))
    print("\nPaper leans:",
          (results["decision"] == "PAPER LEAN").sum())
    print("Passes:",
          (results["decision"] == "PASS").sum())
    print("\nTEST ONLY — NOTHING PUBLISHED")
