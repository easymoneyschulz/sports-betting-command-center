"""NBA V2 automation deployment contract.
Daily scheduled checks must fail closed until all required inputs exist.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    ROOT / "nba_v2_recovery/models/nba_v2_rebuilt_candidate.joblib",
    ROOT / "nba_v2_recovery/nba_original_player_games.parquet",
    ROOT / "automation/nba_v2_daily.py",
]

def main():
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED if not p.is_file()]
    if missing:
        print("NBA V2 NOT DEPLOYED: missing assets:", ", ".join(missing))
        print("No picks published; historical predictions unchanged.")
        return 1
    print("NBA V2 core assets available. Live advanced-stat feed and verified slate still required.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
