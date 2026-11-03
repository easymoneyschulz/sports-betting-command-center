
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="Sports Betting Command Center",
    page_icon="🏈",
    layout="wide"
)

BASE = Path(__file__).resolve().parent
DATA_PATH = BASE / "public_data/public_predictions.csv"

@st.cache_data(ttl=60)
def load_data():
    return pd.read_csv(DATA_PATH, dtype={"event_id": str})

df = load_data()

st.title("🏆 Sports Betting Command Center")
st.caption("NFL V6.1 • CFB V4 • NBA V2")
st.info(
    "Model research and paper testing. "
    "Historical results are not live betting performance."
)

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "NFL Picks",
        "College Football",
        "NBA Projections",
        "Model Performance"
    ]
)

historical = df[
    df["test_type"] == "HISTORICAL_BACKTEST"
]
forward = df[
    df["test_type"].isin([
        "FORWARD_PAPER", "PROJECTION_TEST"
    ])
]

if page == "Overview":
    st.header("Command Center Overview")

    nfl = historical[historical["model"] == "NFL V6.1"]

    wins = (nfl["result"] == "WIN").sum()
    losses = (nfl["result"] == "LOSS").sum()
    pushes = (nfl["result"] == "PUSH").sum()

    rate = (
        100 * wins / (wins + losses)
        if wins + losses else None
    )

    a, b, c, d = st.columns(4)

    a.metric(
        "NFL Historical Win %",
        f"{rate:.2f}%" if rate is not None else "N/A"
    )
    b.metric("NFL Historical Record",
             f"{wins}-{losses}-{pushes}")
    c.metric("Forward Tests", len(forward))
    d.metric(
        "Pending Results",
        int((forward["result"] == "PENDING").sum())
    )

    st.subheader("Current Model Activity")
    st.dataframe(
        forward[
            ["model", "selection", "prediction",
             "market_line", "result"]
        ],
        use_container_width=True,
        hide_index=True
    )

elif page == "NFL Picks":
    st.header("🏈 NFL V6.1")

    nfl_forward = df[
        (df["model"] == "NFL V6.1") &
        (df["test_type"] == "FORWARD_PAPER")
    ]

    if nfl_forward.empty:
        st.warning(
            "No finalized NFL forward picks published yet. "
            "Next model rerun is planned for Wednesday."
        )
    else:
        st.dataframe(
            nfl_forward,
            use_container_width=True,
            hide_index=True
        )

elif page == "College Football":
    st.header("🏟️ College Football V4")

    cfb = df[
        (df["model"] == "CFB V4") &
        (df["test_type"] == "FORWARD_PAPER")
    ]

    st.caption("Qualified forward paper selections")
    st.dataframe(
        cfb,
        use_container_width=True,
        hide_index=True
    )

elif page == "NBA Projections":
    st.header("🏀 NBA V2 Player Points")

    nba = df[
        (df["model"] == "NBA V2") &
        (df["test_type"] == "PROJECTION_TEST")
    ]

    st.caption(
        "Point projections only. "
        "These are not confirmed over/under bets."
    )

    st.dataframe(
        nba[
            ["selection", "prediction", "actual", "result"]
        ],
        use_container_width=True,
        hide_index=True
    )

    graded = nba[nba["result"] == "GRADED"]

    if not graded.empty:
        error = (
            pd.to_numeric(graded["prediction"]) -
            pd.to_numeric(graded["actual"])
        ).abs()

        st.metric("Projection MAE", f"{error.mean():.2f}")

elif page == "Model Performance":
    st.header("📊 Historical Model Performance")

    nfl = historical[historical["model"] == "NFL V6.1"]

    wins = (nfl["result"] == "WIN").sum()
    losses = (nfl["result"] == "LOSS").sum()
    pushes = (nfl["result"] == "PUSH").sum()

    st.metric(
        "NFL V6.1 Historical Record",
        f"{wins}-{losses}-{pushes}"
    )

    st.caption(
        "Backtested 2022–2025 selections. "
        "Not verified real-money wagers."
    )

    st.subheader("Forward Testing")
    st.dataframe(
        forward.groupby(["model", "result"])
        .size()
        .reset_index(name="Count"),
        use_container_width=True,
        hide_index=True
    )

st.divider()
st.caption(
    "Sports Betting Command Center | "
    "Research and informational use only."
)
