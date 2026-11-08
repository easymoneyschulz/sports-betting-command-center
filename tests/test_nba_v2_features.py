"""Regression tests for the frozen NBA V2 rolling rules."""
import unittest
import numpy as np
import pandas as pd
from automation.nba_v2_features import prepare, features

class TestV2Features(unittest.TestCase):
    def test_thresholds_and_zero_minutes(self):
        rows = []
        for i in range(21):
            rows.append(dict(player_id="1", game_id=str(i), game_date=f"2026-01-{i+1:02d}",
                             season=2026, minutes_raw=0 if i == 0 else 20,
                             pts=i, usg_pct=.2, fga=10, fg3a=4, fta=2))
        hist = prepare(pd.DataFrame(rows))
        for count, available in [(2, []), (3, [5]), (5, [5, 10]),
                                 (8, [5, 10, 20])]:
            day = pd.Timestamp("2026-01-02") + pd.Timedelta(days=count)
            f = features(hist, "1", day, 2026, 1)
            self.assertEqual(f["prior_games"], count)
            for window in (5, 10, 20):
                self.assertEqual(not np.isnan(f[f"pts_last{window}"]), window in available)
            self.assertEqual(not np.isnan(f["pts_std_last10"]), count >= 5)
            self.assertEqual(not np.isnan(f["season_pts_avg_prior"]), count >= 3)

    def test_no_future_leakage(self):
        rows = [
            dict(player_id="1", game_id=str(i), game_date=f"2026-01-{i+1:02d}",
                 season=2026, minutes_raw=20, pts=i * 10,
                 usg_pct=.2, fga=10, fg3a=4, fta=2)
            for i in range(6)
        ]
        h = prepare(pd.DataFrame(rows))
        result = features(h, "1", "2026-01-06", 2026, 0)
        self.assertEqual(result["prior_games"], 5)
        self.assertEqual(result["pts_last5"], 20)
        self.assertEqual(result["pts_last10"], 20)

if __name__ == "__main__":
    unittest.main()
