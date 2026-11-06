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
        st.caption("Three highest-probability Sunday touchdown candidates from separate games · No sportsbook odds used")
        candidates=sunday.sort_values("td_probability",ascending=False).drop_duplicates("game_id").head(3)
        if len(candidates)<3:
            st.warning("Not enough distinct Sunday games for a three-player parlay.")
        else:
            st.warning("RESEARCH PARLAY ONLY — player availability is unverified; check active rosters before betting.")
            for rank,(_,leg) in enumerate(candidates.iterrows(),1):
                st.markdown(f"**{rank}. {escape(str(leg['player_name']))} — Anytime TD** · "
                    f"{escape(str(leg['team']))} vs {escape(str(leg['opponent']))} · "
                    f"{float(leg['td_probability']):.1%} model probability")
            st.caption("Ranked by individual touchdown probability, not sportsbook value. "
                "Different games reduce direct game-level correlation, but the legs are not guaranteed independent.")
        st.markdown("### 📊 TOUCHDOWN MODEL TRACKER")
        history_path=path.parent/"nfl_td_projection_history.csv"
        parlay_path=path.parent/"nfl_td_parlay_history.csv"
        if history_path.exists():
            history=pd.read_csv(history_path)
            graded=history[history["result"].isin(["HIT","MISS"])]
            wins=int((graded["result"]=="HIT").sum())
            losses=int((graded["result"]=="MISS").sum())
            x,y,z=st.columns(3)
            x.metric("Graded player picks",len(graded))
            y.metric("Anytime TD hits",wins)
            z.metric("Hit rate",f"{wins/len(graded):.1%}" if len(graded) else "Pending")
            st.caption(f"Frozen player-game predictions: {len(history)} · Awaiting final scores: {int((history['result']=='PENDING').sum())}")
            if len(graded):
                st.dataframe(graded[["player_name","team","opponent","td_probability","result"]].tail(100),hide_index=True,use_container_width=True)
        else:
            st.info("Historical grading starts after the first daily tracking workflow runs.")
        if parlay_path.exists():
            tracked=pd.read_csv(parlay_path)
            groups=tracked.groupby("week_key").agg(result=("parlay_result","first"),legs=("leg","count"))
            completed=groups[groups.result.isin(["WIN","LOSS"])]
            st.markdown("#### Sunday 3-leg parlay record")
            st.metric("Completed parlays",f"{int((completed.result=='WIN').sum())} W – {int((completed.result=='LOSS').sum())} L")
            st.dataframe(tracked.tail(60),hide_index=True,use_container_width=True)
        st.caption("Model research record only; no wager stake, sportsbook payout or ROI is assumed.")
    except Exception as e:
        st.error("Touchdown snapshot failed validation; projections are hidden.")
