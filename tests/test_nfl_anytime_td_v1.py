"""Smoke tests: no current-game leakage, touchdown labeling, and input validation."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"automation"))
import pandas as pd
import pytest
from nfl_anytime_td_v1 import prepare

def sample():
    return pd.DataFrame([
        dict(season=2022,week=w,game_id=f"g{w}",player_id="p1",player_name="Player",
             position="RB",team="DAL",rush_attempts=10*w,targets=w,
             rushing_tds=int(w==2),receiving_tds=0)
        for w in (1,2,3)
    ])

def test_lagged_features_do_not_see_current_game():
    df=prepare(sample())
    assert pd.isna(df.iloc[0].rushes_last3)
    assert df.iloc[1].rushes_last3==10
    assert df.iloc[2].rushes_last3==15
    assert df.iloc[1].any_td==1
    assert df.iloc[2].td_rate_last8==0.5

def test_receiving_touchdown_counts():
    d=sample()
    d.loc[0,"receiving_tds"]=1
    assert prepare(d).iloc[0].any_td==1

def test_duplicate_games_rejected():
    d=sample()
    with pytest.raises(ValueError,match="Duplicate"):
        prepare(pd.concat([d,d.iloc[[0]]],ignore_index=True))
