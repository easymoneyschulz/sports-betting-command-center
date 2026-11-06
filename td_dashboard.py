"""Professional, read-only NFL anytime touchdown research dashboard."""
from pathlib import Path
from datetime import datetime, timezone
from html import escape
import pandas as pd
import streamlit as st

def render():
    st.markdown("""
    <style>
    .td-hero{background:linear-gradient(125deg,#300609,#100e16 60%,#080b12);
      border:1px solid #8c1b26;border-radius:20px;padding:30px 32px;margin:14px 0 22px}
    .td-eyebrow{font-size:12px;letter-spacing:3px;color:#ff727c;font-weight:800}
    .td-title{font-size:clamp(28px,4vw,48px);font-weight:900;color:#fff;margin:9px 0}
    .td-sub{font-size:14px;color:#c8b8be}
    .td-card{background:linear-gradient(125deg,#1d1720,#11141d);border:1px solid #463039;
      border-radius:16px;padding:19px;margin:9px 0}
    .td-player{font-weight:800;font-size:20px;color:white}
    .td-matchup{color:#aaa1ab;font-size:13px;margin-top:5px}
    .td-percent{font-size:31px;font-weight:900;color:#fff;text-align:right}
    .td-meter{height:6px;background:#35242d;border-radius:20px;margin-top:14px;overflow:hidden}
    .td-fill{height:100%;background:linear-gradient(90deg,#9d1425,#ff485c);border-radius:20px}
    </style>
    <div class="td-hero">
      <div class="td-eyebrow">EASYMONEYSCHULZ / NFL ANALYTICS</div>
      <div class="td-title">ANYTIME <span style="color:#f04454">TOUCHDOWN</span></div>
      <div class="td-sub">V3 probability engine · Rushing + receiving TD · Research projections only</div>
    </div>""",unsafe_allow_html=True)
    path=Path(__file__).resolve().parent/"public_data"/"nfl_td_v3_latest.csv"
    if not path.exists():
        st.info("Automated touchdown projections are awaiting the first validated research snapshot.")
        return
    try:
        data=pd.read_csv(path)
        needed={"player_name","position","team","opponent","td_probability","game_id"}
        if data.empty or not needed.issubset(data):
            raise ValueError("Invalid touchdown data schema")
        data["td_probability"]=pd.to_numeric(data["td_probability"],errors="raise")
        if not data["td_probability"].between(0,1).all(): raise ValueError("Invalid probabilities")
        data=data.drop_duplicates(["game_id","player_name"])
        if "kickoff_utc" in data:
            kick=pd.to_datetime(data["kickoff_utc"],utc=True,errors="coerce")
            upcoming=kick>=pd.Timestamp.now(tz="UTC")
            if upcoming.any():
                data=data[upcoming].copy()
            else:
                st.warning("Latest snapshot contains no future games. Showing archived research only.")
        st.caption("Research only · No confirmed active roster or sportsbook odds · Not betting recommendations")
        a,b,c=st.columns(3)
        a.metric("Players modeled",f"{len(data):,}")
        b.metric("Highest TD estimate",f"{data.td_probability.max():.1%}")
        c.metric("Model version","V3")
        matchups=sorted(set(data["team"].astype(str)+" vs "+data["opponent"].astype(str)))
        selected=st.selectbox("Filter matchup",["All games"]+matchups)
        if selected!="All games":
            data=data[(data["team"].astype(str)+" vs "+data["opponent"].astype(str))==selected]
        positions=st.multiselect("Positions",["QB","RB","WR","TE"],default=["QB","RB","WR","TE"])
        data=data[data["position"].isin(positions)]
        for _,p in data.sort_values("td_probability",ascending=False).head(20).iterrows():
            name=escape(str(p["player_name"]))
            team=escape(str(p["team"]))
            opp=escape(str(p["opponent"]))
            pos=escape(str(p["position"]))
            pct=float(p["td_probability"])*100
            st.markdown(f"""<div class="td-card"><div style="display:flex;justify-content:space-between;gap:12px">
              <div><div class="td-player">{name}</div><div class="td-matchup">{pos} · {team} vs {opp}</div></div>
              <div class="td-percent">{pct:.1f}%</div></div>
              <div class="td-meter"><div class="td-fill" style="width:{pct:.1f}%"></div></div></div>""",
              unsafe_allow_html=True)

        st.markdown("### 🔥 SUNDAY TOP 15")
        st.caption("Automatically ranked by model touchdown probability · Unverified research estimates")
        sunday=data.copy()
        if "kickoff_utc" in sunday:
            sunday=sunday[pd.to_datetime(sunday["kickoff_utc"],utc=True,errors="coerce").dt.tz_convert("America/Chicago").dt.dayofweek==6]
        sunday=sunday.sort_values("td_probability",ascending=False).head(15)
        if sunday.empty:
            st.info("Sunday research projections are not available yet.")
        else:
            for rank,(_,p) in enumerate(sunday.iterrows(),1):
                name=escape(str(p["player_name"]))
                team=escape(str(p["team"]))
                opp=escape(str(p["opponent"]))
                pct=float(p["td_probability"])*100
                st.markdown(f"""<div class="td-card"><div style="display:flex;justify-content:space-between;align-items:center;gap:12px">
                  <div><div class="td-eyebrow">#{rank:02d} · SUNDAY TD RANKING</div><div class="td-player">{name}</div>
                  <div class="td-matchup">{team} vs {opp} · {escape(str(p["position"]))}</div></div>
                  <div class="td-percent">{pct:.1f}%</div></div>
                  <div class="td-meter"><div class="td-fill" style="width:{pct:.1f}%"></div></div></div>""",unsafe_allow_html=True)
        st.markdown("### 🧩 AUTOMATIC SUNDAY PARLAY")
        st.caption("The model builds a parlay only when independently verified odds and roster status establish qualifying value.")
        # No invented lines, implied independence, or unsupported betting edges.
        required={"sportsbook","american_odds","roster_verified","odds_timestamp_utc"}
        if not required.issubset(sunday.columns):
            st.warning("NO QUALIFYING PARLAY — live sportsbook odds and verified player status are not connected yet.")
        else:
            import math
            qualified=sunday.copy()
            qualified["american_odds"]=pd.to_numeric(qualified["american_odds"],errors="coerce")
            qualified["odds_timestamp_utc"]=pd.to_datetime(qualified["odds_timestamp_utc"],utc=True,errors="coerce")
            qualified=qualified[(qualified["roster_verified"]==True)&
                ((pd.Timestamp.now(tz="UTC")-qualified["odds_timestamp_utc"])<=pd.Timedelta(minutes=30))]
            qualified=qualified[(qualified["american_odds"]<=-100)|(qualified["american_odds"]>=100)].copy()
            qualified["decimal_odds"]=qualified["american_odds"].apply(
                lambda x: 1+x/100 if x>0 else 1+100/abs(x))
            qualified["edge"]=qualified["td_probability"]-1/qualified["decimal_odds"]
            qualified=qualified[qualified["edge"]>=0.05].sort_values("edge",ascending=False)
            # Only independent-game legs are considered for the simple joint-probability estimate.
            qualified=qualified.drop_duplicates("game_id").head(3)
            if len(qualified)<2:
                st.warning("NO QUALIFYING PARLAY — fewer than two independently matched, value-qualified games.")
            else:
                st.success(f"Research parlay candidate: {len(qualified)} legs · Requires further validation")
                for _,leg in qualified.iterrows():
                    st.markdown(f"**{escape(str(leg['player_name']))}** · {leg['team']} vs {leg['opponent']} · "
                        f"{float(leg['td_probability']):.1%} model · {int(leg['american_odds']):+d} odds · "
                        f"{float(leg['edge']):+.1%} estimated edge")
                st.caption("Different games reduce direct game-level correlation, but outcomes are not guaranteed independent. No wager is placed.")
    except Exception as e:
        st.error("Touchdown snapshot failed validation; projections are hidden.")
