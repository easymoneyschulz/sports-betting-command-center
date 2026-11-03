"""Read-only NFL V6.1 research dashboard. No sportsbook or pick publishing."""
from __future__ import annotations

import html
from pathlib import Path

import pandas as pd
import streamlit as st

import io
import zipfile
import requests

GITHUB_REPO = "easymoneyschulz/sports-betting-command-center"
WORKFLOW_NAME = "NFL V6.1 Research Automation"

@st.cache_data(ttl=900, show_spinner=False)
def _latest_github_snapshot(token: str):
    """Read-only artifact retrieval. Credentials never appear in the page."""
    api = f"https://api.github.com/repos/{GITHUB_REPO}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    runs_response = requests.get(
        f"{api}/actions/runs",
        headers=headers,
        params={"status": "success", "per_page": 30},
        timeout=15,
    )
    runs_response.raise_for_status()
    runs = runs_response.json().get("workflow_runs", [])
    for run in runs:
        if run.get("name") != WORKFLOW_NAME:
            continue
        artifacts_response = requests.get(
            f"{api}/actions/runs/{run['id']}/artifacts",
            headers=headers,
            params={"per_page": 100},
            timeout=15,
        )
        artifacts_response.raise_for_status()
        artifacts = artifacts_response.json().get("artifacts", [])
        for artifact in artifacts:
            if artifact.get("expired") or not artifact.get("name", "").startswith("nfl-v61-research-"):
                continue
            download = requests.get(
                artifact["archive_download_url"],
                headers=headers,
                timeout=30,
            )
            download.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(download.content)) as archive:
                candidates = sorted(
                    (n for n in archive.namelist()
                     if n.split("/")[-1].startswith("nfl_v61_research_projection_")
                     and n.endswith(".csv")),
                    reverse=True,
                )
                if not candidates:
                    continue
                with archive.open(candidates[0]) as handle:
                    frame = pd.read_csv(handle)
            if frame.empty or not REQUIRED.issubset(frame.columns):
                continue
            if len(frame) > 32:
                continue
            picks = None
            with zipfile.ZipFile(io.BytesIO(download.content)) as pick_archive:
                pick_files = sorted((n for n in pick_archive.namelist()
                if n.split("/")[-1].startswith("nfl_v61_paper_picks_")
                and n.endswith(".csv")), reverse=True)
                if pick_files:
                    with pick_archive.open(pick_files[0]) as handle:
                        picks = pd.read_csv(handle)
            return frame, f"GitHub Actions run {run['id']} / {candidates[0]}", picks
    raise ValueError("No valid unexpired NFL research projection artifact found")


@st.cache_data(ttl=120, show_spinner=False)
def _public_paper_snapshot():
    root = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/public_data"
    response = requests.get(f"{root}/nfl_v61_latest_paper_picks.csv", timeout=15)
    response.raise_for_status()
    picks = pd.read_csv(io.StringIO(response.text))
    response = requests.get(f"{root}/nfl_v61_latest_projection.csv", timeout=15)
    response.raise_for_status()
    frame = pd.read_csv(io.StringIO(response.text))
    if frame.empty or not REQUIRED.issubset(frame.columns):
        raise ValueError("Invalid public projection snapshot")
    return frame, "Latest public NFL paper snapshot", picks


def _load_research_snapshot(base: Path):
    try:
        return _public_paper_snapshot()
    except (requests.RequestException, ValueError, pd.errors.ParserError, OSError):
        pass
    token = ""
    try:
        token = st.secrets.get("GITHUB_READ_TOKEN", "")
    except (FileNotFoundError, KeyError):
        pass
    if token:
        try:
            return _latest_github_snapshot(token)
        except (requests.RequestException, ValueError, KeyError, zipfile.BadZipFile, OSError):
            pass
    paths = _snapshot_paths(base)
    if not paths:
        return None, None, None
    for path in paths:
        try:
            frame = pd.read_csv(path)
            if not frame.empty and REQUIRED.issubset(frame.columns):
                return frame, f"Local snapshot: {path.name}", None
        except (OSError, pd.errors.ParserError, UnicodeError):
            continue
    return None, None, None


TEAM_NAMES = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LAC": "Los Angeles Chargers", "LAR": "Los Angeles Rams",
    "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}
ALIASES = {"JAC": "JAX", "LA": "LAR", "WSH": "WAS"}
LOGO_IDS = {"WAS": "wsh", "LAR": "lar", "JAX": "jax"}
REQUIRED = {"home_team", "away_team", "model_home_margin", "season", "week"}


def _team(code):
    code = ALIASES.get(str(code).strip().upper(), str(code).strip().upper())
    return code, TEAM_NAMES.get(code, code)


def _logo(code, name):
    logo_id = LOGO_IDS.get(code, code.lower())
    return (f'<img class="nfl-r-logo" loading="lazy" '
            f'src="https://a.espncdn.com/i/teamlogos/nfl/500/{logo_id}.png" '
            f'alt="{html.escape(name, quote=True)} logo">')


def _snapshot_paths(base: Path):
    # Local files only. GitHub workflow artifacts are not automatically downloaded.
    roots = [base / "public_data", base / "verification"]
    found = []
    for root in roots:
        if root.is_dir():
            found.extend(root.rglob("nfl_v61_research_projection_*.csv"))
    # Filename includes UTC timestamp; this avoids relying on copied-file mtime.
    return sorted(found, key=lambda p: (p.name, str(p)), reverse=True)


def render_nfl_research(base: Path):
    st.subheader("NFL V6.1 — Weekly Model Projections")
    st.caption("RESEARCH ONLY · Not sportsbook odds, betting recommendations, or published picks")

    df, source_label, picks = _load_research_snapshot(base)
    if df is None:
        st.info("No valid NFL research snapshot is available. The latest successful GitHub run may still be processing.")
        return

    season = str(df.iloc[0]["season"])
    week = str(df.iloc[0]["week"])
    st.caption(f"Season {season} · Week {week} · {len(df)} matchups · Source: {source_label}")
    if "publication_status" in df.columns:
        statuses = set(df["publication_status"].dropna().astype(str).str.upper())
        if statuses and statuses != {"PUBLISHED"}:
            st.caption("Source publication status: " + ", ".join(sorted(statuses)))

    st.subheader("NFL V6.1 — Forward Paper Picks")
    if picks is None:
        st.warning("This source does not contain the latest sportsbook picks. The GitHub artifact reader may need a valid GITHUB_READ_TOKEN in Streamlit secrets.")
    elif picks.empty:
        st.info("No verified upcoming sportsbook spreads in this snapshot.")
    else:
        qualified = picks[picks["decision"] == "PAPER_PICK"].copy()
        if qualified.empty:
            st.info("No qualifying paper picks this run. All verified games are PASS.")
        else:
            st.markdown("""
            <style>
            .nfl-picks-banner{background:linear-gradient(110deg,#111c2d,#08101b 65%,#092b32);
              border:1px solid #234d68;border-radius:16px;padding:19px 24px;margin:12px 0 18px;
              box-shadow:0 8px 24px #0005}
            .nfl-picks-banner .top{color:#6fd6ff;font-size:12px;font-weight:850;letter-spacing:2px}
            .nfl-picks-banner .main{font-size:clamp(22px,3vw,34px);font-weight:950;color:#fff;
              letter-spacing:.5px;margin-top:3px}
            .nfl-picks-banner .bottom{color:#a2b5c9;font-size:12px;margin-top:6px}
            .nfl-pick-card{display:flex;align-items:center;gap:18px;
              background:linear-gradient(105deg,#1a2535,#0e1520 62%,#102c2b);
              border:1px solid #304357;border-left:5px solid #28d1b0;border-radius:14px;
              padding:14px 22px;margin:11px 0;min-height:102px;box-shadow:0 5px 16px #0004}
            .nfl-pick-rank{color:#71879e;font-weight:900;font-size:23px;width:34px;flex-shrink:0}
            .nfl-pick-logo{width:76px;height:76px;object-fit:contain;flex-shrink:0}
            .nfl-pick-info{flex:1;min-width:0}
            .nfl-pick-kicker{font-size:11px;color:#64cbd7;font-weight:800;letter-spacing:1.5px}
            .nfl-pick-name{font-size:clamp(17px,2vw,24px);font-weight:900;color:#fff;line-height:1.2}
            .nfl-pick-meta{color:#9aacc0;font-size:12px;margin-top:5px}
            .nfl-pick-right{text-align:right;min-width:140px}
            .nfl-pick-spread{color:#fff;font-size:clamp(26px,3vw,38px);font-weight:950;line-height:1}
            .nfl-pick-odds{font-size:13px;color:#aebdc9;margin-top:5px}
            .nfl-pick-edge{color:#51e8b1;font-size:13px;font-weight:850;margin-top:7px}
            @media(max-width:650px){
              .nfl-pick-card{gap:10px;padding:12px 10px;min-height:85px}
              .nfl-pick-rank{width:18px;font-size:15px}
              .nfl-pick-logo{width:48px;height:48px}
              .nfl-pick-name{font-size:15px}
              .nfl-pick-right{min-width:86px}
              .nfl-pick-spread{font-size:25px}
              .nfl-pick-meta{font-size:10px}
              .nfl-pick-edge{font-size:11px}
            }
            </style>
            """, unsafe_allow_html=True)
            st.markdown(
                '<div class="nfl-picks-banner"><div class="top">NFL V6.1 / LIVE DATA SNAPSHOT</div>'
                '<div class="main">WEEK {} &nbsp;·&nbsp; {} PAPER PICKS</div>'
                '<div class="bottom">MODEL-RANKED SPREADS · ODDS AT SNAPSHOT · RESEARCH ONLY</div></div>'.format(
                    html.escape(week), len(qualified)), unsafe_allow_html=True)
            for rank, (_, pick) in enumerate(
                qualified.sort_values("edge_points", ascending=False).iterrows(), 1
            ):
                name = str(pick["selected_team"])
                code = next((c for c, n in TEAM_NAMES.items() if n == name), "")
                logo = _logo(code, name) if code else ""
                spread = float(pick["selected_spread"])
                price = int(pick["selected_price"])
                edge = float(pick["edge_points"])
                book = html.escape(str(pick["sportsbook"]).title())
                card = (
                    f'<div class="nfl-pick-card">'
                    f'<div class="nfl-pick-rank">{rank:02d}</div>'
                    f'<div class="nfl-pick-logo">{logo}</div>'
                    f'<div class="nfl-pick-info">'
                    f'<div class="nfl-pick-kicker">MODEL SELECTION</div>'
                    f'<div class="nfl-pick-name">{html.escape(name)}</div>'
                    f'<div class="nfl-pick-meta">{book} · PAPER TEST</div></div>'
                    f'<div class="nfl-pick-right">'
                    f'<div class="nfl-pick-spread">{spread:+g}</div>'
                    f'<div class="nfl-pick-odds">ODDS {price:+d}</div>'
                    f'<div class="nfl-pick-edge">EDGE +{edge:.2f} PTS</div>'
                    f'</div></div>'
                )
                st.markdown(card, unsafe_allow_html=True)
        with st.expander("All verified matchups — picks and passes"):
            cols = ["away_team","home_team","decision","selected_team",
                    "selected_spread","selected_price","edge_points",
                    "sportsbook","odds_timestamp_utc","prediction_timestamp_utc"]
            st.dataframe(picks[[c for c in cols if c in picks.columns]],
                         hide_index=True, use_container_width=True)
    st.caption("Paper testing only. No wagers placed.")
    st.divider()

    st.markdown("""
    <style>
    .nfl-r-card{background:linear-gradient(130deg,#1c1e25,#101116);border:1px solid #34363e;
      border-left:4px solid #ed3848;border-radius:14px;padding:18px;margin:8px 0 16px;min-height:184px}
    .nfl-r-eyebrow{font-size:11px;color:#adb0bb;letter-spacing:1.1px;font-weight:800}
    .nfl-r-match{display:flex;align-items:center;gap:10px;margin:15px 0 12px}
    .nfl-r-team{flex:1;min-width:0;color:white;font-weight:750;font-size:15px;line-height:1.3}
    .nfl-r-logo{height:42px;width:42px;object-fit:contain;flex-shrink:0}
    .nfl-r-at{color:#aaa;font-size:13px}
    .nfl-r-proj{color:#ff5665;font-weight:850;font-size:20px}
    .nfl-r-foot{color:#9296a3;font-size:11px;margin-top:10px}
    @media(max-width:640px){.nfl-r-card{padding:14px}.nfl-r-logo{height:30px;width:30px}
      .nfl-r-team{font-size:12px}.nfl-r-proj{font-size:17px}}
    </style>
    """, unsafe_allow_html=True)

    for i in range(0, len(df), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j >= len(df):
                continue
            row = df.iloc[i + j]
            away_code, away_name = _team(row["away_team"])
            home_code, home_name = _team(row["home_team"])
            margin = pd.to_numeric(row["model_home_margin"], errors="coerce")
            if pd.isna(margin):
                projection = "Margin unavailable"
            elif margin > 0:
                projection = f"{home_name} by {margin:.1f} pts"
            elif margin < 0:
                projection = f"{away_name} by {abs(margin):.1f} pts"
            else:
                projection = "Projected tie"
            card = f'''<div class="nfl-r-card">
              <div class="nfl-r-eyebrow">NFL V6.1 · WEEK {html.escape(week)} · RESEARCH</div>
              <div class="nfl-r-match">
                {_logo(away_code, away_name)}<div class="nfl-r-team">{html.escape(away_name)}</div>
                <span class="nfl-r-at">@</span>
                {_logo(home_code, home_name)}<div class="nfl-r-team">{html.escape(home_name)}</div>
              </div>
              <div class="nfl-r-proj">{html.escape(projection)}</div>
              <div class="nfl-r-foot">PROJECTED GAME MARGIN · NOT A BETTING PICK</div>
            </div>'''
            with col:
                st.markdown(card, unsafe_allow_html=True)
    st.caption("Latest successful GitHub artifact is checked every 15 minutes when a secure read token is configured. Local snapshots are fallback only.")
    st.divider()
