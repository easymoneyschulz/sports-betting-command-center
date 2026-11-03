import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
from html import escape

st.set_page_config(page_title="Easy Money Picks",page_icon="🏆",layout="wide",initial_sidebar_state="collapsed")
DATA=Path(__file__).resolve().parent/"public_data"
st.markdown("""<style>
.stApp{background:#080f1e;color:#edf3ff}
.block-container{max-width:1080px;padding:1.1rem 1rem 4rem}
header[data-testid="stHeader"]{background:#080f1e}
h1,h2,h3{color:#f5f8ff!important}
div[data-testid="stRadio"] [role="radiogroup"]{display:flex;flex-wrap:wrap;gap:8px}
div[data-testid="stRadio"] label{background:#17233a;border:1px solid #304361;border-radius:12px;padding:9px 12px;margin:0}
div[data-testid="stRadio"] label p{font-weight:700;font-size:13px}
div[data-testid="stRadio"] label:has(input:checked){border-color:#4ce0a1;background:#12392f}
div[data-testid="stRadio"] label>div:first-child{display:none}
.hero{padding:22px 20px;border:1px solid #314664;border-radius:18px;background:linear-gradient(125deg,#142c46,#0c182a);margin-bottom:22px}
.eyebrow{color:#59e6aa;font-weight:800;font-size:11px;letter-spacing:2px}
.brand{font-size:clamp(29px,6vw,47px);font-weight:950;letter-spacing:-1px;margin:7px 0}
.muted{color:#a4b5cc;font-size:13px}
.game{border:1px solid #30405a;background:#131e30;border-radius:16px;padding:18px;margin:12px 0}
.game-head{display:flex;align-items:center;justify-content:space-between;gap:12px}
.game-title{font-weight:850;font-size:clamp(17px,4.5vw,23px);color:#fff}
.tag{border-radius:50px;padding:5px 9px;background:#28374e;color:#bcd0e7;font-size:11px;font-weight:850;white-space:nowrap}
.tag.over{color:#5de6ac;background:#123c33}.tag.under{color:#ffc07e;background:#44301e}
.game-sub{color:#9fb0c9;font-size:12px;margin-top:5px}
.stats{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:16px}
.stat{background:#0c1626;border:1px solid #273650;border-radius:10px;padding:11px}
.stat-label{color:#9eafc8;font-size:10px;letter-spacing:.6px;text-transform:uppercase}
.stat-value{color:#fff;font-size:21px;font-weight:900;margin-top:5px}
.section{font-size:21px;font-weight:850;margin:24px 0 10px}
@media(max-width:650px){.block-container{padding:1rem .8rem 3rem}.hero{padding:18px}.game{padding:15px}.stat-value{font-size:18px}}
</style>""",unsafe_allow_html=True)
st.markdown('<div class="hero"><div class="eyebrow">THE SPORTS BETTING COMMAND CENTER</div><div class="brand">🏆 EASY MONEY PICKS</div><div class="muted">NFL V6.1 · College Football V4 · NBA Points V2<br>Model projections and forward paper testing</div></div>',unsafe_allow_html=True)
page=st.radio("Sections",["🏠 Home","🏈 NFL","🏟️ College","🏀 NBA","📊 Results"],horizontal=True,label_visibility="collapsed")
@st.cache_data(ttl=120,show_spinner=False)
def load(name):
    p=DATA/name
    if not p.is_file():return pd.DataFrame()
    try:return pd.read_csv(p,low_memory=False)
    except (OSError,ValueError,pd.errors.ParserError):return pd.DataFrame()
def clean(v):
    if pd.isna(v):return "—"
    return escape(str(v))
def num(v,suffix="",signed=False):
    try:
        n=float(v)
        return f"{n:+.1f}{suffix}" if signed else f"{n:.1f}{suffix}"
    except (ValueError,TypeError):return "—"
def card(title,subtitle,status,fields):
    kind=str(status).upper()
    color="over" if kind in ("OVER","LEAN","BET") else ("under" if kind=="UNDER" else "")
    parts=''.join(f'<div class="stat"><div class="stat-label">{escape(str(label))}</div><div class="stat-value">{escape(str(value))}</div></div>' for label,value in fields)
    st.markdown(f'<div class="game"><div class="game-head"><div class="game-title">{escape(str(title))}</div><div class="tag {color}">{escape(str(status))}</div></div><div class="game-sub">{escape(str(subtitle))}</div><div class="stats">{parts}</div></div>',unsafe_allow_html=True)
def note(msg):st.info(msg)
def nfl():
    st.markdown('<div class="section">NFL V6.1 · Game projections</div>',unsafe_allow_html=True)
    df=load("nfl_v61_latest_projection.csv")
    picks=load("nfl_v61_latest_paper_picks.csv")
    if df.empty:return note("No NFL projections have been published yet.")
    if "week" in df:st.caption(f"Season {clean(df.iloc[0].get('season',''))} · Week {clean(df.iloc[0].get('week',''))} · {len(df)} games")
    for _,r in df.head(20).iterrows():
        home=str(r.get("home_team","HOME"));away=str(r.get("away_team","AWAY"))
        margin=r.get("model_home_margin")
        decision=str(r.get("betting_decision","RESEARCH"))
        if not picks.empty and "game_id" in picks:
            m=picks[picks.game_id.astype(str)==str(r.get("game_id"))]
            if not m.empty:decision=str(m.iloc[0].get("decision",decision))
        card(f"{away} @ {home}","Frozen model · research projection",decision,[("Projected home margin",num(margin,signed=True)),("Projected winner",home if pd.notna(margin) and float(margin)>0 else away)])
    st.caption("Research projections are not verified sportsbook picks.")
def college():
    st.markdown('<div class="section">College Football V4</div>',unsafe_allow_html=True)
    df=load("cfb_v4_latest_paper_picks.csv")
    if df.empty:return note("V4 automatic publishing is not ready yet. No current picks are being claimed.")
    for _,r in df.head(20).iterrows():
        card(f"{clean(r.get('away_team','Away'))} @ {clean(r.get('home_team','Home'))}",clean(r.get("game_date","Forward paper tracking")),clean(r.get("decision","PAPER")),[("Selection",clean(r.get("selected_side","—"))),("Model edge",num(r.get("edge_points"),signed=True))])
def nba():
    st.markdown('<div class="section">NBA V2 · Player points</div>',unsafe_allow_html=True)
    df=load("nba_v2_recovered_prop_comparison.csv")
    if df.empty:return note("No NBA V2 player projections published yet.")
    df["game_date"]=pd.to_datetime(df["game_date"],errors="coerce").dt.date
    dates=sorted(df.game_date.dropna().unique())
    if not dates:return note("No dated NBA projections available.")
    today=datetime.now().date()
    future=[d for d in dates if d>=today]
    selected=st.selectbox("Game day",future if future else dates,index=0,format_func=lambda d:d.strftime("%a, %b %d"))
    subset=df[df.game_date==selected].copy()
    status=st.radio("Show",["All","OVER","UNDER","WAIT","PASS"],horizontal=True)
    if status!="All":subset=subset[subset.decision==status]
    query=st.text_input("Find player",placeholder="Search by player name")
    if query.strip():subset=subset[subset.player_name.str.contains(query,case=False,regex=False,na=False)]
    if "edge" in subset:subset=subset.assign(_edge=pd.to_numeric(subset.edge,errors="coerce").abs()).sort_values("_edge",ascending=False,na_position="last")
    total=len(subset);pages=max(1,(total+11)//12)
    page_no=st.number_input("Page",min_value=1,max_value=pages,value=1,step=1) if pages>1 else 1
    st.caption(f"{total} players · Showing up to 12 per page")
    for _,r in subset.iloc[(page_no-1)*12:page_no*12].iterrows():
        card(clean(r.get("player_name","Player")),f"{clean(r.get('team',''))} vs {clean(r.get('opponent',''))} · {selected}",clean(r.get("decision","WAIT")),[("Model points",num(r.get("v2_projection"))),("Sportsbook line",num(r.get("market_line"))),("Model edge",num(r.get("edge"),signed=True)),("Sportsbook",clean(r.get("sportsbook","Awaiting odds")))])
    if total==0:note("No players match these filters.")
    st.caption("WAIT means no confirmed actionable line. All picks are paper testing only.")
def results():
    st.markdown('<div class="section">Paper tracking</div>',unsafe_allow_html=True)
    df=load("nba_v2_recovered_paper_tracker.csv")
    if df.empty:return note("No graded NBA V2 paper selections published yet.")
    if "result" in df:
        graded=df[df.result.isin(["WIN","LOSS"])]
        a,b=st.columns(2);a.metric("Graded selections",len(graded));b.metric("Wins",int((graded.result=="WIN").sum()))
    st.dataframe(df.tail(30),use_container_width=True,hide_index=True)
if page=="🏠 Home":
    st.markdown('<div class="section">Model dashboard</div>',unsafe_allow_html=True)
    a,b,c=st.columns(3)
    a.metric("NFL","V6.1");b.metric("CFB","V4");c.metric("NBA","V2")
    st.caption("Choose a sport above to see game cards and model projections.")
    nfl()
elif page=="🏈 NFL":nfl()
elif page=="🏟️ College":college()
elif page=="🏀 NBA":nba()
else:results()
st.divider()
st.caption("Easy Money Picks · Research and paper testing only. No guaranteed returns.")
