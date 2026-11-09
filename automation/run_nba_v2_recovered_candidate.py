"""Generate NBA V2 recovered-candidate paper projections from ESPN box scores.

Requires the verified 22-feature model artifact in NBA_V2_MODEL_PATH.
Never substitutes a rolling average or silently fills missing usage features.
"""
import os
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import joblib
import hashlib
import numpy as np
import pandas as pd
from build_nba_rolling_baseline import ROOT, slate, event_teams, get, BASE

FEATURES = ['home','prior_games','pts_last5','pts_last10','pts_last20',
'minutes_last5','minutes_last10','minutes_last20','usg_pct_last5',
'usg_pct_last10','usg_pct_last20','fga_last5','fga_last10','fga_last20',
'fg3a_last5','fg3a_last10','fg3a_last20','fta_last5','fta_last10',
'fta_last20','pts_std_last10','season_pts_avg_prior']

def parse_number(value):
    try: return float(value)
    except (TypeError, ValueError): return np.nan

def box_rows(event_id, day):
    data = get(BASE + '/summary', {'event': event_id})
    rows = []
    for team in data.get('boxscore', {}).get('players', []):
        for block in team.get('statistics', []):
            labels = [str(x).upper() for x in block.get('labels', [])]
            if 'PTS' not in labels: continue
            for item in block.get('athletes', []):
                athlete = item.get('athlete', {})
                vals = dict(zip(labels, item.get('stats', [])))
                if not athlete.get('id'): continue
                def shot(key):
                    return parse_number(str(vals.get(key, '')).split('-')[0])
                minutes = str(vals.get('MIN', '')).split(':')
                mins = parse_number(minutes[0])
                if len(minutes) == 2 and pd.notna(mins):
                    mins += parse_number(minutes[1]) / 60
                if not pd.notna(mins) or mins <= 0: continue
                rows.append(dict(game_id=str(event_id), game_date=day.isoformat(),
                    player_id=str(athlete['id']), player_name=athlete.get('displayName'),
                    team=team.get('team', {}).get('displayName'),
                    pts=parse_number(vals.get('PTS')), minutes=mins,
                    fga=shot('FG'), fg3a=shot('3PT'), fta=shot('FT'),
                    usg_pct=parse_number(vals.get('USG%'))))
    return rows

def main():
    path = Path(os.environ.get('NBA_V2_MODEL_PATH', 'models/nba_v2_frozen_2026_model.joblib'))
    if not path.is_file():
        raise FileNotFoundError(f'Missing recovered V2 model artifact: {path}')
    expected = 'f5ac39a7f1e94ce3b1ec4e918986e9e74dce280557f03db4b38b344be0dcb27f'
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected: raise ValueError('Model artifact SHA-256 mismatch')
    artifact = joblib.load(path)
    if artifact['features'] != FEATURES:
        raise ValueError('Model feature order mismatch')
    today = datetime.now(ZoneInfo('America/Chicago')).date()
    events = slate(today)
    if not any(not e.get('status', {}).get('type', {}).get('completed') for e in events):
        today += timedelta(days=1)
        events = slate(today)
    # Fresh independent backfill: never infer missing values from the rolling baseline.
    rows = []
    for n in range(90, 0, -1):
        day = today - timedelta(days=n)
        for event in slate(day):
            if event.get('status', {}).get('type', {}).get('completed') is not True: continue
            try: rows.extend(box_rows(event['id'], day))
            except Exception as exc: print('Skipped ESPN event', event.get('id'), repr(exc))
    if not rows: raise RuntimeError('No historical box scores retrieved')
    logs = pd.DataFrame(rows).drop_duplicates(['game_id', 'player_id'])
    logs = logs.sort_values(['player_id', 'game_date'])
    result = []
    for event in events:
        if event.get('status', {}).get('type', {}).get('completed'): continue
        teams = event_teams(event)
        if not {'home', 'away'}.issubset(teams): continue
        for side in ('home', 'away'):
            team = teams[side].get('displayName')
            opponent = teams['away' if side == 'home' else 'home'].get('displayName')
            # Only players whose most recent recorded team is the slated team.\n            # Historical team rows can include traded players and ESPN boxscore\n            # team-label anomalies; do not claim they belong to this roster.\n            recent = logs.sort_values('game_date').drop_duplicates('player_id', keep='last')\n            eligible_ids = set(recent.loc[recent.team == team, 'player_id'])\n            for pid, g in logs[(logs.team == team) & logs.player_id.isin(eligible_ids)].groupby('player_id'):
                g = g.sort_values('game_date')
                # Early-season slates rarely have 20 current-season games.\n                # Permit >=5 observed games; the 10/20-game features use all\n                # available prior games, with the actual sample count retained.\n                if len(g) < 5: continue
                f = {'home': int(side == 'home'), 'prior_games': len(g)}
                for stat in ('pts','minutes','usg_pct','fga','fg3a','fta'):
                    for n in ((5,10,20) if stat != 'usg_pct' else (5,10,20)):
                        f[f'{stat}_last{n}'] = g[stat].tail(n).mean()
                f['pts_std_last10'] = g.pts.tail(10).std()
                f['season_pts_avg_prior'] = g.pts.mean()
                # Missing ESPN usage rates are handled by the SAVED TRAINING IMPUTER,
                # not fabricated or substituted with a rolling projection.
                if not all(np.isfinite(f[k]) for k in FEATURES if not k.startswith('usg_pct_')): continue
                x = pd.DataFrame([f], columns=FEATURES)
                pred = float(artifact['model'].predict(artifact['imputer'].transform(x))[0])
                if not 0 <= pred <= 65: continue
                result.append(dict(game_date=today.isoformat(), game_id=str(event['id']),
                    player_id=pid, player_name=g.player_name.iloc[-1], team=team,
                    opponent=opponent, v2_projection=round(pred, 4),
                    model_version='NBA V2 RECOVERED CANDIDATE PAPER'))
    if not result:
        raise RuntimeError(f'No eligible V2 projections: box_rows={len(logs)}, distinct_players={logs.player_id.nunique()}, upcoming_events={len(events)}')
    ROOT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(result).to_csv(ROOT / 'nba_v2_recovered_candidate_predictions.csv', index=False)
    print('Recovered candidate paper projections:', len(result))

if __name__ == '__main__': main()
