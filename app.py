import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Easy Money Picks", page_icon="🏆", layout="wide")
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "public_data"

st.markdown("""<style>
.stApp {background:#0b1220;color:#eaf0fc}
.block-container{max-width:1150px;padding-top:1.5rem}
[data-testid="stMetric"]{background:#162239;border:1px solid #30415b;border-radius:12px;padding:14px}
</style>""", unsafe_allow_html=True)
st.title("🏆 EASY MONEY PICKS")
st.caption("Sports Betting Command Center · Model research and forward paper testing")
tabs = st.tabs(["🏠 Overview", "🏈 NFL", "🏟️ College Football", "🏀 NBA Points", "📊 Results"])

@st.cache_data(ttl=120, show_spinner=False)
def read_csv(name):
    path=DATA/name
    if not path.is_file():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, low_memory=False)
    except (OSError, ValueError, pd.errors.ParserError):
        return pd.DataFrame()

def section(title, files, preferred=None, limit=50):
    st.subheader(title)
    for filename in files:
        df=read_csv(filename)
        if df.empty:
            continue
        if "game_date" in df.columns:
            dt=pd.to_datetime(df["game_date"],errors="coerce")
            df=df.assign(_sort_date=dt).sort_values("_sort_date",ascending=False).drop(columns="_sort_date")
        st.caption(f"Source: {filename} · {len(df):,} rows")
        if preferred:
            cols=[c for c in preferred if c in df.columns]
            if cols: df=df[cols]
        st.dataframe(df.head(limit),use_container_width=True,hide_index=True)
        return
    st.info("No published data available for this section yet. The model will appear here after its publishing workflow succeeds.")

with tabs[0]:
    st.subheader("Model status")
    a,b,c=st.columns(3)
    a.metric("NFL","V6.1")
    b.metric("College Football","V4")
    c.metric("NBA Points","V2")
    st.write("Published model outputs are displayed below when available. Empty data is not represented as a betting pick.")
    section("Latest published predictions",["public_predictions.csv"],["model","test_type","selection","prediction","market_line","result","game_date"],20)

with tabs[1]:
    section("NFL V6.1 projections",["nfl_v61_latest_projection.csv","nfl_v61_latest_paper_picks.csv"],limit=40)
    section("NFL historical model records",["public_predictions.csv"],["model","season","selection","prediction","market_line","actual","result"],20)

with tabs[2]:
    section("CFB V4 paper picks",["cfb_v4_latest_paper_picks.csv","ncaa_v4_latest_predictions.csv"],limit=50)
    st.caption("CFB V4 live publishing is not yet verified. Historical results do not imply current picks.")

with tabs[3]:
    section("NBA V2 player points and sportsbook comparisons",["nba_v2_recovered_prop_comparison.csv","nba_v2_recovered_paper_predictions.csv"],["game_date","player_name","team","opponent","v2_projection","market_line","edge","decision","sportsbook","status"],50)
    section("NBA V2 grading",["nba_v2_recovered_paper_tracker.csv"],limit=30)

with tabs[4]:
    section("Paper-tracking results",["nba_v2_recovered_paper_tracker.csv","public_predictions.csv"],["model","test_type","game_date","selection","prediction","actual","result","net_units"],50)

st.divider()
st.caption("Research and paper testing only. Historical backtests do not guarantee future results.")
