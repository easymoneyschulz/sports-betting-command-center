"""Automated official NBA box-score ingestion; refuses incomplete usage stats."""
from datetime import date, timedelta
from pathlib import Path
import time
import pandas as pd

def ingest(root, target_date):
    from nba_api.stats.endpoints import leaguegamelog, boxscoreadvancedv2
    root=Path(root)
    raw=pd.read_parquet(root/'nba_v2_recovery/nba_original_player_games.parquet')
    start=pd.to_datetime(raw.game_date).max().date()+timedelta(days=1)
    end=date.fromisoformat(target_date)-timedelta(days=1)
    if start>end: return None
    if (end-start).days>45: raise ValueError('History too stale for unattended import')
    season=f'{start.year if start.month>=10 else start.year-1}-{str((start.year if start.month>=10 else start.year-1)+1)[-2:]}'
    logs=leaguegamelog.LeagueGameLog(
        player_or_team_abbreviation='P',season=season,
        season_type_all_star='Regular Season',
        date_from_nullable=start.strftime('%m/%d/%Y'),
        date_to_nullable=end.strftime('%m/%d/%Y'),timeout=35
    ).get_data_frames()[0]
    if logs.empty: raise ValueError('No official game logs; refusing to guess')
    logs['GAME_ID']=logs.GAME_ID.astype(str).str.zfill(10)
    advanced=[]
    for gid in sorted(logs.GAME_ID.unique()):
        frame=boxscoreadvancedv2.BoxScoreAdvancedV2(game_id=gid,timeout=35).get_data_frames()[0]
        if frame.empty: raise ValueError(f'Missing advanced stats {gid}')
        frame['GAME_ID']=frame.GAME_ID.astype(str).str.zfill(10)
        advanced.append(frame[['GAME_ID','PLAYER_ID','USG_PCT','MIN']])
        time.sleep(.8)
    stats=pd.concat(advanced,ignore_index=True)
    joined=logs.merge(stats,on=['GAME_ID','PLAYER_ID'],how='left',validate='one_to_one',suffixes=('','_ADV'))
    joined=joined[pd.to_numeric(joined.MIN,errors='coerce').fillna(0)>0].copy()
    def minute_value(v):
        t=str(v)
        if ':' in t:
            m,s=t.split(':',1);return float(m)+float(s)/60
        return float(t)
    joined['minutes_raw']=joined.MIN_ADV.map(minute_value)
    joined['usg_pct']=pd.to_numeric(joined.USG_PCT,errors='coerce')
    if joined[['minutes_raw','usg_pct','PTS','FGA','FG3A','FTA']].isna().any().any():
        raise ValueError('Missing required advanced stats; no update saved')
    joined['game_date']=pd.to_datetime(joined.GAME_DATE).dt.strftime('%Y-%m-%d')
    joined['season']=joined.game_date.map(lambda x:int(x[:4]) if x[5:7]>='10' else int(x[:4])-1)
    joined['home']=joined.MATCHUP.str.contains('vs.',regex=False).astype(int)
    opponents={}
    for gid,g in joined.groupby('GAME_ID'):
        teams=set(g.TEAM_ID.astype(str))
        if len(teams)!=2:raise ValueError('Missing opponent team')
        for team in teams:opponents[(gid,team)]=next(iter(teams-{team}))
    out=pd.DataFrame({
        'game_id':joined.GAME_ID,'game_date':joined.game_date,'season':joined.season,
        'player_id':joined.PLAYER_ID.astype(str),'player_name':joined.PLAYER_NAME,
        'team_id':joined.TEAM_ID.astype(str),
        'opp_team_id':[opponents[(g,str(t))] for g,t in zip(joined.GAME_ID,joined.TEAM_ID)],
        'home':joined.home,'minutes_raw':joined.minutes_raw,
        'pts':joined.PTS,'fga':joined.FGA,'fg3a':joined.FG3A,
        'fta':joined.FTA,'usg_pct':joined.usg_pct})
    if out.duplicated(['game_id','player_id']).any():raise ValueError('Duplicate games')
    dest=root/'nba_v2_outputs'/'staging'/f'official_updates_through_{end:%Y%m%d}.csv'
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('x') as file:out.to_csv(file,index=False)
    return dest
