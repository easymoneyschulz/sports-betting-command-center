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

        st.markdown("### 🧩 SUNDAY PARLAY LAB")
        st.caption("Research calculator · Enter your actual sportsbook odds · No automatic betting recommendations")
        sunday=data.copy()
        if "kickoff_utc" in sunday:
            sunday=sunday[pd.to_datetime(sunday["kickoff_utc"],utc=True,errors="coerce").dt.tz_convert("America/Chicago").dt.dayofweek==6]
        sunday=sunday.sort_values("td_probability",ascending=False).head(20).copy()
        if sunday.empty:
            st.info("No Sunday research projections available yet.")
        else:
            sunday["display"]=sunday["player_name"].astype(str)+" · "+sunday["team"].astype(str)+" vs "+sunday["opponent"].astype(str)
            choices=st.multiselect("Select 2–4 Sunday TD scorers",sunday["display"].tolist(),max_selections=4)
            stake=st.number_input("Parlay stake ($)",min_value=1.0,max_value=1000.0,value=10.0,step=5.0)
            if len(choices)>=2:
                import math
                chosen=sunday[sunday["display"].isin(choices)].copy()
                decimals=[]
                for _,leg in chosen.iterrows():
                    odds=st.number_input("American odds · "+str(leg["player_name"]),min_value=-10000,max_value=10000,value=100,step=5,key="td_odds_"+str(leg["player_id"]))
                    if -99<=odds<=99:
                        st.warning("Valid American odds must be at least +100 or at most -100.")
                        decimals=[]
                        break
                    decimals.append(1+odds/100 if odds>0 else 1+100/abs(odds))
                if decimals:
                    combined=math.prod(decimals)
                    naive=math.prod(chosen["td_probability"].astype(float))
                    a,b,c=st.columns(3)
                    a.metric("Potential total payout",f"${stake*combined:,.2f}")
                    b.metric("Break-even chance",f"{1/combined:.1%}")
                    c.metric("Naive model chance",f"{naive:.1%}")
                    st.caption("Naive probability assumes independence. Same-game legs may be correlated; this is not a validated parlay probability or certified edge.")
            else:
                st.caption("Select at least two players to build a parlay.")
    except Exception as e:
        st.error("Touchdown snapshot failed validation; projections are hidden.")
