"""Fail-closed NBA V2 input checks. No predictions, bets, or file writes."""
from pathlib import Path
import argparse
import pandas as pd

FEATURES = ['home','prior_games','pts_last5','pts_last10','pts_last20','minutes_last5','minutes_last10','minutes_last20','usg_pct_last5','usg_pct_last10','usg_pct_last20','fga_last5','fga_last10','fga_last20','fg3a_last5','fg3a_last10','fg3a_last20','fta_last5','fta_last10','fta_last20','pts_std_last10','season_pts_avg_prior']
SLATE_COLS = ['game_id','game_date','season','player_id','player_name','team_id','opp_team_id','home']

def check_slate(df, date):
    missing=set(SLATE_COLS)-set(df.columns)
    if missing: raise ValueError(f'Missing slate fields: {sorted(missing)}')
    if df.empty: raise ValueError('Empty slate')
    if not pd.to_datetime(df.game_date).dt.strftime('%Y-%m-%d').eq(date).all():
        raise ValueError('Wrong slate date')
    if df.duplicated(['game_id','player_id']).any():
        raise ValueError('Duplicate player/game')
    if not df.home.isin([0,1]).all():
        raise ValueError('Invalid home flag')
    return len(df)

def check_advanced_updates(df):
    required=['game_id','player_id','game_date','minutes_raw','usg_pct','pts','fga','fg3a','fta']
    missing=set(required)-set(df.columns)
    if missing: raise ValueError(f'Missing advanced-stat fields: {sorted(missing)}')
    if df[required].isna().any().any():
        raise ValueError('Incomplete advanced stats; refusing to use ESPN boxscores as complete history')
    if df.duplicated(['game_id','player_id']).any():
        raise ValueError('Duplicate advanced-stat game')
    return len(df)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--slate')
    p.add_argument('--date')
    p.add_argument('--advanced-updates')
    a=p.parse_args()
    if a.slate:
        if not a.date: p.error('--date required with --slate')
        print('SLATE ROWS:',check_slate(pd.read_csv(a.slate,dtype={'game_id':str,'player_id':str}),a.date))
    if a.advanced_updates:
        path=Path(a.advanced_updates)
        df=pd.read_parquet(path) if path.suffix=='.parquet' else pd.read_csv(path)
        print('COMPLETE ADVANCED ROWS:',check_advanced_updates(df))
    if not (a.slate or a.advanced_updates): p.error('Supply --slate or --advanced-updates')
