# NFL Anytime TD V1 — isolated research

**Status:** initial implementation, not yet trained/backtested on actual historical records. No betting recommendations or dashboard publishing.

## Target
Probability that a QB, RB, WR, or TE records at least one **rushing or receiving** TD in an NFL game. Passing TDs by a QB do not count as the QB scoring an anytime TD. Defensive and return TDs are excluded.

## Input
A historical CSV with one row per player-game: season, week, game_id, player_id, player_name, position, team, rush_attempts, targets, rushing_tds, receiving_tds. At least two earlier seasons plus evaluation seasons are recommended. Player logs should include games with zero TDs; missing games must not be treated as zero. The current prototype does not yet incorporate injury reports, depth charts, opponent defense, implied team points, or sportsbook odds.

## Commands
```bash
pip install pandas numpy scikit-learn pytest
pytest -q tests/test_nfl_anytime_td_v1.py
python automation/nfl_anytime_td_v1.py --input data/player_games.csv --out outputs/nfl_anytime_td_v1
```

## Backtest design
For each evaluation season (2023 onward), fit only on seasons before that season. Player features are lagged rolling opportunity rates from completed prior games. Report Brier score, log loss, AUC, and predicted versus observed TD rate. No claims of ROI without timestamped historical odds and a realistic vig/availability simulation.

## Next steps
1. Integrate and validate historical game-level rushing/receiving TD and usage feeds.
2. Run the season-forward backtest, check leakage and calibration, compare to a simple baseline.
3. Add opponent/team environment and availability features with strict pregame timestamps.
4. Add timestamped odds and paper tracking before any production publication.

This branch intentionally does not edit the existing NFL V6.1, NBA, CFB, Streamlit app, or GitHub Actions.
