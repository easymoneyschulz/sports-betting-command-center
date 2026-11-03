
import streamlit as st
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh
from pathlib import Path

st.set_page_config(
    page_title="Sports Betting Command Center",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

BASE = Path(__file__).resolve().parent
DATA_PATH = BASE / "public_data/public_predictions.csv"

@st.cache_data(ttl=60)
def load_data():
    return pd.read_csv(DATA_PATH, dtype={"event_id": str})

df = load_data()

# Optional automated model exports. Only validated, model-produced rows are shown.
@st.cache_data(ttl=120, show_spinner=False)
def load_model_export(model, filename):
    url = f"https://raw.githubusercontent.com/easymoneyschulz/sports-betting-command-center/main/public_data/{filename}"
    try:
        response = requests.get(url, timeout=12)
        response.raise_for_status()
        fresh = pd.read_csv(__import__("io").StringIO(response.text))
        required = {"model", "test_type", "selection", "prediction", "game_date"}
        if fresh.empty or not required.issubset(fresh.columns):
            return pd.DataFrame()
        fresh = fresh[(fresh["model"] == model) &
                      (fresh["test_type"].isin(["FORWARD_PAPER", "PROJECTION_TEST"]))].copy()
        return fresh
    except (requests.RequestException, ValueError, pd.errors.ParserError):
        return pd.DataFrame()


st.markdown("""
<style>
.stApp {
    background: #080e19;
    color: #edf3ff;
}
.block-container {
    max-width: 1450px;
    padding-top: 1.5rem;
}
[data-testid="stHeader"] {
    background: #080e19;
}
[data-testid="stMetric"] {
    background: #141e30;
    padding: 22px;
    border: 1px solid #29364c;
    border-radius: 14px;
}
[data-testid="stMetricLabel"] {
    color: #a5b5ce;
}
[data-testid="stMetricValue"] {
    color: #ffffff;
}
h1, h2, h3 {
    color: #f2f6ff !important;
}
.hero {
    background: linear-gradient(120deg,#142d4c,#0b1628);
    border: 1px solid #304660;
    border-radius: 18px;
    padding: 32px;
    margin-bottom: 22px;
}
.eyebrow {
    color: #51e2a1;
    font-size: 13px;
    letter-spacing: 3px;
    font-weight: 700;
}
.hero-title {
    color: white;
    font-size: clamp(28px,4vw,48px);
    font-weight: 900;
    margin: 10px 0;
}
.hero-sub {
    color: #a8bbd5;
    font-size: 15px;
}
.pick-card {
    background: #141e30;
    border: 1px solid #30445f;
    border-radius: 16px;
    padding: 24px;
    margin: 12px 0;
}
.pick-title {
    color: white;
    font-size: 25px;
    font-weight: 800;
}
.pick-meta {
    color: #a8bbd5;
    font-size: 14px;
    margin-top: 8px;
}
.status {
    color: #ffd479;
    font-weight: 700;
}
div[data-testid="stDataFrame"] {
    border: 1px solid #29364c;
    border-radius: 12px;
}

/* COMMAND CENTER — NAVIGATION UPGRADE */
div[data-testid="stRadio"] div[role="radiogroup"] {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 14px 0 22px;
}

div[data-testid="stRadio"] label {
    background: #17253b !important;
    border: 1px solid #354965 !important;
    border-radius: 10px !important;
    padding: 12px 17px !important;
    cursor: pointer;
}

div[data-testid="stRadio"] label p {
    color: #f1f5ff !important;
    font-weight: 700 !important;
    font-size: 14px !important;
}

div[data-testid="stRadio"] label:has(input:checked) {
    background: #164638 !important;
    border-color: #41d99b !important;
}

div[data-testid="stRadio"] label:has(input:checked) p {
    color: #78ffc3 !important;
}

div[data-testid="stRadio"] label > div:first-child {
    display: none !important;
}


/* EASYMONEYSCHULZ PICKS — ANIMATED BRAND */
@keyframes emsBounceIn {
    0% {
        opacity: 0;
        transform: translateY(-110px) scale(0.65);
    }
    55% {
        opacity: 1;
        transform: translateY(18px) scale(1.06);
    }
    72% {
        transform: translateY(-10px) scale(0.98);
    }
    86% {
        transform: translateY(5px) scale(1.01);
    }
    100% {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

.ems-brand {
    text-align: center;
    padding: 28px 12px 32px;
    margin-bottom: 22px;
}

.ems-brand-title {
    font-size: clamp(30px, 5.5vw, 76px);
    font-weight: 950;
    letter-spacing: 2px;
    line-height: 1.12;
    color: #ffffff;
    text-shadow:
        0 0 12px rgba(65, 217, 155, 0.55),
        0 0 38px rgba(65, 217, 155, 0.28);
    animation: emsBounceIn 1.5s cubic-bezier(.22,1,.36,1) both;
}

.ems-brand-title span {
    color: #41d99b;
}

.ems-brand-subtitle {
    color: #a8bbd5;
    font-size: 13px;
    letter-spacing: 4px;
    margin-top: 14px;
    animation: emsBounceIn 1.8s ease-out both;
}

@media (prefers-reduced-motion: reduce) {
    .ems-brand-title,
    .ems-brand-subtitle {
        animation: none;
    }
}


/* EASYMONEYSCHULZ — FLOATING TEXT NAVIGATION */
div[role="radiogroup"] {
    display: flex !important;
    flex-wrap: wrap !important;
    justify-content: center !important;
    gap: 12px 30px !important;
    background: transparent !important;
    border: none !important;
    padding: 8px 0 20px !important;
}

div[role="radiogroup"] label {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    padding: 12px 2px !important;
    cursor: pointer !important;
    transition: color 0.2s ease !important;
}

div[role="radiogroup"] label p {
    font-size: 17px !important;
    font-weight: 900 !important;
    letter-spacing: 0.7px !important;
    color: #f5f8ff !important;
}

div[role="radiogroup"] label:hover p {
    color: #41d99b !important;
}

div[role="radiogroup"] label:has(input:checked) {
    border-bottom: 3px solid #41d99b !important;
}

div[role="radiogroup"] label:has(input:checked) p {
    color: #41d99b !important;
    text-shadow: 0 0 12px rgba(65,217,155,.35);
}

div[role="radiogroup"] label > div:first-child {
    display: none !important;
}

@media (max-width: 700px) {
    div[role="radiogroup"] {
        gap: 5px 16px !important;
    }
    div[role="radiogroup"] label p {
        font-size: 13px !important;
    }
}


/* STEP 55 — PREMIUM ANIMATED TEXT NAVIGATION */

/* The actual radio group */
div[role="radiogroup"] {
    display: flex !important;
    flex-wrap: wrap !important;
    justify-content: center !important;
    align-items: center !important;
    gap: 14px 36px !important;
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}

/* Floating text links */
div[role="radiogroup"] label {
    position: relative !important;
    display: inline-flex !important;
    align-items: center !important;
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
    border: 0 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    padding: 14px 0 !important;
    margin: 0 !important;
    transform: translateY(0);
    transition:
        transform .25s ease,
        filter .25s ease !important;
}

/* Hide Streamlit radio indicators */
div[role="radiogroup"] label input,
div[role="radiogroup"] label [data-testid="stRadioIcon"],
div[role="radiogroup"] label [data-baseweb="radio"] > div:first-child,
div[role="radiogroup"] label > div:first-child {
    display: none !important;
}

/* Remove leftover colored backgrounds from inner wrappers */
div[role="radiogroup"] label > div,
div[role="radiogroup"] label > div > div {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* Typography */
div[role="radiogroup"] label p {
    font-size: 18px !important;
    font-weight: 900 !important;
    letter-spacing: 1px !important;
    color: #f5f8ff !important;
    transition:
        color .25s ease,
        text-shadow .25s ease !important;
}

/* Animated underline */
div[role="radiogroup"] label::after {
    content: "";
    position: absolute;
    bottom: 4px;
    left: 0;
    width: 100%;
    height: 3px;
    border-radius: 4px;
    background: #41d99b;
    box-shadow: 0 0 14px rgba(65,217,155,.6);
    transform: scaleX(0);
    transform-origin: center;
    transition: transform .3s ease;
}

/* Hover animation */
div[role="radiogroup"] label:hover {
    transform: translateY(-4px);
}

div[role="radiogroup"] label:hover p {
    color: #41d99b !important;
    text-shadow: 0 0 16px rgba(65,217,155,.55);
}

div[role="radiogroup"] label:hover::after {
    transform: scaleX(1);
}

/* Active selection */
div[role="radiogroup"] label:has(input:checked) {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

div[role="radiogroup"] label:has(input:checked) p {
    color: #41d99b !important;
    text-shadow: 0 0 15px rgba(65,217,155,.45);
}

div[role="radiogroup"] label:has(input:checked)::after {
    transform: scaleX(1);
}

/* Keyboard accessibility */
div[role="radiogroup"] label:focus-within {
    outline: 2px solid #41d99b !important;
    outline-offset: 4px;
}

/* Mobile */
@media (max-width: 700px) {
    div[role="radiogroup"] {
        gap: 6px 20px !important;
    }

    div[role="radiogroup"] label p {
        font-size: 13px !important;
    }
}

@media (prefers-reduced-motion: reduce) {
    div[role="radiogroup"] label,
    div[role="radiogroup"] label p,
    div[role="radiogroup"] label::after {
        transition: none !important;
        transform: none !important;
    }
}


/* STEP 56 — PROFESSIONAL RED / BLACK THEME */

:root {
    --ems-bg: #0c0d10;
    --ems-surface: #181a20;
    --ems-border: #30333b;
    --ems-red: #e0353e;
    --ems-white: #f3f4f6;
    --ems-muted: #a1a6b0;
}

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stHeader"] {
    background: var(--ems-bg) !important;
    color: var(--ems-white) !important;
}

[data-testid="stMainBlockContainer"] {
    padding-top: 2rem !important;
}

.ems-pro-header {
    text-align: center;
    padding: 20px 10px 22px;
    border-bottom: 1px solid #262930;
    margin-bottom: 12px;
}

.ems-pro-wordmark {
    color: var(--ems-white);
    font-size: clamp(30px, 4.8vw, 60px);
    font-weight: 900;
    letter-spacing: -1.5px;
    line-height: 1.1;
}

.ems-pro-wordmark span {
    color: var(--ems-red);
}

.ems-pro-tagline {
    color: var(--ems-muted);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 3px;
    margin-top: 12px;
}

.ems-pro-tagline span {
    color: var(--ems-red);
    padding: 0 8px;
}

/* Clean navigation, no circles or boxes */
div[role="radiogroup"] {
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
    justify-content: center !important;
    gap: 10px 30px !important;
}

div[role="radiogroup"] label,
div[role="radiogroup"] label:has(input:checked) {
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
    border: 0 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    padding: 12px 0 !important;
    transform: none !important;
}

div[role="radiogroup"] label > div:first-child,
div[role="radiogroup"] label [data-testid="stRadioIcon"],
div[role="radiogroup"] label [data-baseweb="radio"] {
    display: none !important;
}

div[role="radiogroup"] label > div,
div[role="radiogroup"] label > div > div {
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}

div[role="radiogroup"] label p {
    color: #d6d8dc !important;
    font-size: 15px !important;
    font-weight: 800 !important;
    letter-spacing: .6px !important;
    text-shadow: none !important;
    transition: color .2s ease !important;
}

div[role="radiogroup"] label:hover {
    transform: none !important;
}

div[role="radiogroup"] label:hover p,
div[role="radiogroup"] label:has(input:checked) p {
    color: var(--ems-red) !important;
    text-shadow: none !important;
}

div[role="radiogroup"] label::after {
    background: var(--ems-red) !important;
    box-shadow: none !important;
    height: 2px !important;
}

/* Override existing card palette */
.pick-card,
.metric-card,
.hero,
[data-testid="stMetric"] {
    background: var(--ems-surface) !important;
    border: 1px solid var(--ems-border) !important;
    box-shadow: none !important;
    border-radius: 10px !important;
}

.pick-card *,
.metric-card * {
    text-shadow: none !important;
}

/* Existing green accent classes */
.eyebrow,
.status {
    color: var(--ems-red) !important;
}

/* Standardize common text */
h1, h2, h3 {
    color: var(--ems-white) !important;
    letter-spacing: -.4px;
}

/* Mobile */
@media (max-width: 700px) {
    .ems-pro-wordmark {
        font-size: 29px;
        letter-spacing: -1px;
    }
    div[role="radiogroup"] {
        gap: 4px 15px !important;
    }
    div[role="radiogroup"] label p {
        font-size: 12px !important;
    }
}

@media (prefers-reduced-motion: reduce) {
    div[role="radiogroup"] label,
    div[role="radiogroup"] label::after {
        transition: none !important;
    }
}


/* STEP 57 — SWINGING EMS SHIELD */

.ems-pro-header {
    position: relative;
    overflow: visible;
}

.ems-badge-hanger {
    position: absolute;
    right: 20px;
    top: -18px;
    width: 88px;
    display: flex;
    flex-direction: column;
    align-items: center;
    transform-origin: 50% 0;
    animation: emsSwing 4.2s ease-in-out infinite;
    pointer-events: none;
    z-index: 2;
}

.ems-badge-string {
    height: 24px;
    width: 2px;
    background: linear-gradient(#777b85, #33363e);
}

.ems-badge {
    width: 76px;
    height: 88px;
    background: linear-gradient(
        145deg, #393b42, #111216 45%, #090a0c
    );
    border: 2px solid #b92c35;
    clip-path: polygon(
        50% 0, 96% 14%, 96% 70%,
        50% 100%, 4% 70%, 4% 14%
    );
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 18px rgba(0,0,0,.35);
}

.ems-badge-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
}

.ems-badge-inner strong {
    color: #f3f4f6;
    font-size: 21px;
    font-weight: 900;
    letter-spacing: 1px;
}

.ems-badge-inner small {
    color: #e0353e;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 2px;
}

@keyframes emsSwing {
    0%, 100% { transform: rotate(-7deg); }
    50% { transform: rotate(7deg); }
}

@media (max-width: 800px) {
    .ems-badge-hanger {
        right: 0;
        top: -12px;
        transform: scale(.7);
        animation: none;
    }

    .ems-badge {
        width: 52px;
        height: 60px;
    }

    .ems-badge-inner strong {
        font-size: 14px;
    }

    .ems-badge-inner small {
        font-size: 7px;
    }
}

@media (prefers-reduced-motion: reduce) {
    .ems-badge-hanger {
        animation: none !important;
    }
}


/* STEP 58 — CINEMATIC RED LIGHT SWEEP */

.ems-pro-wordmark {
    position: relative;
    display: inline-block;
    isolation: isolate;
    overflow: hidden;
    padding: 3px 6px;
}

/* Narrow moving reflection */
.ems-pro-wordmark .ems-light-sweep {
    position: absolute;
    inset: 0;
    z-index: 1;
    pointer-events: none;
    background: linear-gradient(
        105deg,
        transparent 0%,
        transparent 38%,
        rgba(225, 35, 48, 0.08) 44%,
        rgba(255, 75, 85, 0.45) 48%,
        rgba(255, 210, 210, 0.72) 50%,
        rgba(255, 65, 75, 0.38) 52%,
        transparent 60%,
        transparent 100%
    );
    width: 45%;
    mix-blend-mode: screen;
    transform: translateX(-250%) skewX(-12deg);
    animation: emsLightSweep 6s ease-in-out infinite;
}

/* One sweep followed by a pause */
@keyframes emsLightSweep {
    0%, 12% {
        transform: translateX(-250%) skewX(-12deg);
        opacity: 0;
    }
    16% {
        opacity: 1;
    }
    48% {
        transform: translateX(350%) skewX(-12deg);
        opacity: 1;
    }
    52%, 100% {
        transform: translateX(350%) skewX(-12deg);
        opacity: 0;
    }
}

/* Respect reduced-motion preferences */
@media (prefers-reduced-motion: reduce) {
    .ems-pro-wordmark .ems-light-sweep {
        animation: none !important;
        display: none !important;
    }
}


/* STEP 59B — BORDERLESS PICK ROWS */

.ems-editorial-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    padding: 22px 12px;
    border-bottom: 1px solid #303138;
    background: transparent;
    transition: background .2s ease, padding-left .2s ease;
}

.ems-editorial-row:hover {
    background: rgba(224,53,62,.055);
    padding-left: 20px;
}

.ems-editorial-info {
    flex: 1;
    min-width: 0;
}

.ems-editorial-category {
    color: #e0353e;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.4px;
    margin-bottom: 8px;
}

.ems-editorial-name {
    color: #f4f5f7;
    font-size: 21px;
    font-weight: 800;
    margin-bottom: 6px;
}

.ems-editorial-detail {
    color: #a1a6b0;
    font-size: 13px;
}

.ems-editorial-value-block {
    text-align: right;
    flex-shrink: 0;
}

.ems-editorial-value {
    color: #f4f5f7;
    font-size: 30px;
    font-weight: 900;
    font-variant-numeric: tabular-nums;
}

.ems-editorial-footnote {
    color: #a1a6b0;
    font-size: 11px;
    margin-top: 5px;
}

@media (max-width: 600px) {
    .ems-editorial-row {
        padding: 18px 4px;
        gap: 12px;
    }
    .ems-editorial-name {
        font-size: 17px;
    }
    .ems-editorial-value {
        font-size: 24px;
    }
    .ems-editorial-footnote {
        font-size: 10px;
    }
}

@media (prefers-reduced-motion: reduce) {
    .ems-editorial-row {
        transition: none;
    }
}


/* STEP 63 — LIVE SCOREBOARD */

.ems-score-row {
    display: grid;
    grid-template-columns: 105px minmax(130px,1fr) minmax(130px,1fr);
    align-items: center;
    gap: 12px;
    padding: 18px 10px;
    border-bottom: 1px solid #303138;
    transition: background .2s ease;
}

.ems-score-row:hover {
    background: rgba(224,53,62,.055);
}

.ems-score-status {
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 1px;
}

.ems-status-dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: currentColor;
    margin-right: 7px;
}

.ems-score-team {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    color: #f3f4f6;
    font-size: 14px;
    font-weight: 700;
}

.ems-score-team strong {
    font-size: 19px;
    font-variant-numeric: tabular-nums;
}

.ems-score-detail {
    grid-column: 2 / 4;
    color: #a1a6b0;
    font-size: 11px;
}

.ems-score-venue {
    grid-column: 2 / 4;
    color: #777e89;
    font-size: 10px;
}

@media(max-width:650px) {
    .ems-score-row {
        grid-template-columns: 75px 1fr 1fr;
        gap: 8px;
        padding: 15px 3px;
    }
    .ems-score-team {
        font-size: 11px;
    }
    .ems-score-team strong {
        font-size: 16px;
    }
}


/* STEP 65B — TRANSPARENT TEAM LOGOS */

.ems-logo-score-row {
    display: block !important;
    padding: 20px 10px !important;
    background: transparent !important;
    border-bottom: 1px solid #303138 !important;
}

.ems-logo-matchup {
    display: grid;
    grid-template-columns: 1fr 35px 1fr;
    align-items: center;
    gap: 12px;
    margin: 12px 0;
}

.ems-logo-team {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 7px;
    color: #f4f4f5;
    font-size: 13px;
    font-weight: 700;
    text-align: center;
}

.ems-team-logo {
    width: 58px;
    height: 58px;
    object-fit: contain;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

.ems-team-fallback {
    color: #e0353e;
    font-size: 15px;
    font-weight: 900;
    min-height: 58px;
    display: flex;
    align-items: center;
}

.ems-logo-team strong {
    font-size: 24px;
    color: #ffffff;
    font-variant-numeric: tabular-nums;
}

.ems-logo-vs {
    color: #777e89;
    font-size: 10px;
    font-weight: 900;
    text-align: center;
}

.ems-logo-score-row .ems-score-detail,
.ems-logo-score-row .ems-score-venue {
    text-align: center;
    margin-top: 7px;
}

@media(max-width:600px) {
    .ems-team-logo {
        width: 45px;
        height: 45px;
    }

    .ems-logo-team {
        font-size: 11px;
    }

    .ems-logo-team strong {
        font-size: 20px;
    }
}


/* STEP 69 — PREMIUM SPORTS NAVIGATION */

/* Dark clickable sports tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #0b0d12 !important;
    border-bottom: 1px solid #303138 !important;
    gap: 8px !important;
}

.stTabs [data-baseweb="tab"] {
    background: #15171d !important;
    color: #e6e6e6 !important;
    border: 1px solid #303138 !important;
    border-radius: 7px 7px 0 0 !important;
    padding: 12px 18px !important;
    font-weight: 900 !important;
    transition: all .2s ease !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #ffffff !important;
    background: #24252b !important;
}

.stTabs [aria-selected="true"] {
    color: #ffffff !important;
    background: #24252b !important;
    border-bottom: 3px solid #e0353e !important;
}

/* Red and black refresh button */
.stButton > button {
    background: #15171d !important;
    color: #ffffff !important;
    border: 1px solid #e0353e !important;
    border-radius: 7px !important;
    font-weight: 900 !important;
    letter-spacing: 1px !important;
    transition: all .2s ease !important;
}

.stButton > button:hover {
    background: #e0353e !important;
    color: #ffffff !important;
    border: 1px solid #ff555d !important;
}

.stButton > button:focus {
    color: #ffffff !important;
    box-shadow: 0 0 0 2px rgba(224,53,62,.35) !important;
}

/* Keep tabs dark */
.stTabs [data-baseweb="tab-panel"] {
    background: transparent !important;
    padding-top: 18px !important;
}


/* STEP 70 — EASYMONEYSCHULZ 3D SPORTS NAV */

.stTabs [data-baseweb="tab-list"] {
    display: flex !important;
    gap: 16px !important;
    border: none !important;
    background: transparent !important;
    padding: 15px 4px 22px 4px !important;
    overflow: visible !important;
}

.stTabs [data-baseweb="tab"] {
    flex: 1 1 0 !important;
    min-width: 0 !important;
    min-height: 82px !important;
    justify-content: center !important;
    background: linear-gradient(
        145deg, #252832, #111319
    ) !important;
    color: #f5f5f5 !important;
    border: 1px solid #414653 !important;
    border-bottom: 4px solid #08090c !important;
    border-radius: 12px !important;
    padding: 18px 12px !important;
    font-size: 19px !important;
    font-weight: 950 !important;
    letter-spacing: .8px !important;
    box-shadow:
        0 7px 0 #050609,
        0 12px 22px rgba(0,0,0,.45),
        inset 0 1px 0 rgba(255,255,255,.09) !important;
    transition:
        transform .22s ease,
        box-shadow .22s ease,
        background .22s ease,
        border-color .22s ease !important;
}

.stTabs [data-baseweb="tab"]:hover {
    transform: translateY(-5px) !important;
    background: linear-gradient(
        145deg, #353943, #191b23
    ) !important;
    border-color: #e0353e !important;
    box-shadow:
        0 10px 0 #08090c,
        0 17px 28px rgba(224,53,62,.22) !important;
    color: #ffffff !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    transform: translateY(-3px) !important;
    background: linear-gradient(
        145deg, #a8242d, #4c1017
    ) !important;
    color: #ffffff !important;
    border: 1px solid #ff5962 !important;
    border-bottom: 5px solid #e0353e !important;
    box-shadow:
        0 7px 0 #21080b,
        0 12px 30px rgba(224,53,62,.35),
        inset 0 1px 0 rgba(255,255,255,.2) !important;
}

.stTabs [data-baseweb="tab"] p {
    font-size: 19px !important;
    font-weight: 950 !important;
    color: #ffffff !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    background: #ff3544 !important;
    height: 4px !important;
}

.stTabs [data-baseweb="tab-panel"] {
    padding-top: 22px !important;
}

/* Premium refresh control */
.stButton > button {
    min-height: 58px !important;
    background: linear-gradient(
        145deg, #282b33, #101116
    ) !important;
    color: #ffffff !important;
    border: 1px solid #e0353e !important;
    border-bottom: 4px solid #8e1720 !important;
    border-radius: 10px !important;
    font-size: 16px !important;
    font-weight: 950 !important;
    box-shadow: 0 6px 15px rgba(0,0,0,.4) !important;
    transition: all .2s ease !important;
}

.stButton > button:hover {
    transform: translateY(-3px) !important;
    background: linear-gradient(
        145deg, #a8242d, #4c1017
    ) !important;
    color: #ffffff !important;
    box-shadow: 0 9px 22px rgba(224,53,62,.3) !important;
}

@media(max-width:650px) {
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 12px !important;
        padding: 12px 5px !important;
        min-height: 68px !important;
    }

    .stTabs [data-baseweb="tab"] p {
        font-size: 12px !important;
    }
}

@media(prefers-reduced-motion: reduce) {
    .stTabs [data-baseweb="tab"],
    .stButton > button {
        transition: none !important;
        transform: none !important;
    }
}


/* STEP 71B — BROADCAST GAME CARDS */

.stVerticalBlockBorderWrapper {
    background: linear-gradient(145deg, #1b1e26, #0e1016) !important;
    border: 1px solid #343946 !important;
    border-radius: 15px !important;
    box-shadow:
        0 7px 0 #07080c,
        0 12px 25px rgba(0,0,0,.35),
        inset 0 1px 0 rgba(255,255,255,.06) !important;
    margin-bottom: 19px !important;
    transition: border-color .2s ease, transform .2s ease !important;
}

.stVerticalBlockBorderWrapper:hover {
    border-color: #8f2931 !important;
    transform: translateY(-2px);
}

.ems-broadcast-live {
    color: #ff4652;
    font-weight: 950;
    font-size: 13px;
    letter-spacing: 2px;
}

.ems-broadcast-dot {
    display: inline-block;
    width: 9px;
    height: 9px;
    background: #ff3945;
    border-radius: 50%;
    margin-right: 9px;
    box-shadow: 0 0 12px #ff3945;
    animation: ems-pulse 1.3s infinite;
}

@keyframes ems-pulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 12px #ff3945; }
    50% { opacity: .45; box-shadow: 0 0 3px #ff3945; }
}

.ems-broadcast-status {
    font-weight: 950;
    font-size: 12px;
    letter-spacing: 2px;
}

.ems-broadcast-venue {
    color: #8f98a9;
    font-size: 11px;
    text-align: right;
}

.ems-broadcast-detail {
    text-align: center;
    color: #c2c9d5;
    font-weight: 850;
    font-size: 13px;
    letter-spacing: 1.5px;
    margin: 8px 0 16px 0;
}

.ems-broadcast-team {
    text-align: center;
    width: 100%;
}

.ems-broadcast-team-name {
    color: #f4f5f7;
    font-size: 16px;
    font-weight: 900;
    margin-top: 8px;
    min-height: 24px;
    text-align: center;
}

.ems-broadcast-score {
    font-size: 54px;
    line-height: 1.2;
    font-weight: 950;
    font-variant-numeric: tabular-nums;
    text-align: center;
    margin: 5px 0;
    text-shadow: 0 3px 12px rgba(0,0,0,.5);
}

.ems-broadcast-center {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100px;
}

.ems-broadcast-vs {
    color: #e0353e;
    font-weight: 950;
    font-size: 18px;
    letter-spacing: 2px;
    text-align: center;
}

@media(max-width:650px) {
    .ems-broadcast-score {
        font-size: 34px;
    }

    .ems-broadcast-team-name {
        font-size: 12px;
    }

    .ems-broadcast-detail {
        font-size: 11px;
    }

    .ems-broadcast-vs {
        font-size: 12px;
    }
}

@media(prefers-reduced-motion: reduce) {
    .ems-broadcast-dot {
        animation: none;
    }

    .stVerticalBlockBorderWrapper {
        transition: none !important;
    }
}


/* STEP 70D — CUSTOM 3D SPORTS BUTTONS */

.ems-sport-divider {
    height: 2px;
    background: linear-gradient(
        90deg, transparent, #a8242d, transparent
    );
    margin: 8px 0 22px 0;
}

div[data-testid="stButton"] {
    width: 100%;
}

div[data-testid="stButton"] button {
    width: 100% !important;
    min-height: 100px !important;
    border-radius: 14px !important;
    font-size: 21px !important;
    font-weight: 950 !important;
    letter-spacing: 1px !important;
    color: #ffffff !important;
    background: linear-gradient(
        145deg, #292d38, #11131a
    ) !important;
    border: 1px solid #505665 !important;
    border-bottom: 6px solid #050609 !important;
    box-shadow:
        0 8px 0 #050609,
        0 13px 24px rgba(0,0,0,.5) !important;
    transition: transform .2s ease,
                box-shadow .2s ease,
                background .2s ease !important;
}

div[data-testid="stButton"] button:hover {
    transform: translateY(-5px) !important;
    border-color: #ff4652 !important;
    color: #ffffff !important;
    box-shadow:
        0 11px 0 #050609,
        0 18px 28px rgba(224,53,62,.3) !important;
}

/* Selected sport */
div[data-testid="stButton"] button[kind="primary"],
div[data-testid="stButton"] button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(
        145deg, #b72b35, #511018
    ) !important;
    border: 1px solid #ff606a !important;
    border-bottom: 6px solid #ff3945 !important;
    color: #ffffff !important;
    box-shadow:
        0 8px 0 #21070a,
        0 13px 32px rgba(224,53,62,.4) !important;
}

@media(max-width:650px) {
    div[data-testid="stButton"] button {
        min-height: 76px !important;
        font-size: 12px !important;
        letter-spacing: 0 !important;
        padding: 5px !important;
    }
}

@media(prefers-reduced-motion: reduce) {
    div[data-testid="stButton"] button {
        transition: none !important;
        transform: none !important;
    }
}


/* STEP 72D — LIVE SPORTS WIRE */

.ems-ticker-shell {
    width: 100%;
    overflow: hidden;
    background: linear-gradient(90deg,#101116,#1b1d25,#101116);
    border-top: 1px solid #8e252e;
    border-bottom: 2px solid #e0353e;
    border-radius: 9px;
    margin: 14px 0 20px;
    box-shadow: 0 6px 20px rgba(0,0,0,.4);
}

.ems-ticker-heading {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    color: white;
    font-size: 12px;
    font-weight: 950;
    letter-spacing: 2px;
    border-bottom: 1px solid #303138;
}

.ems-ticker-light {
    width: 9px;
    height: 9px;
    flex-shrink: 0;
    background: #ff3945;
    border-radius: 50%;
    box-shadow: 0 0 12px #ff3945;
    animation: ems-ticker-pulse 1.3s infinite;
}

.ems-ticker-heading-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg,#e0353e,transparent);
}

.ems-ticker-window {
    width: 100%;
    overflow: hidden;
    padding: 14px 0;
}

.ems-ticker-track {
    display: flex;
    width: max-content;
    animation: ems-ticker-scroll 75s linear infinite;
}

.ems-ticker-track:hover {
    animation-play-state: paused;
}

.ems-ticker-group {
    display: flex;
    align-items: center;
    flex-shrink: 0;
}

.ems-ticker-item {
    display: flex;
    align-items: center;
    gap: 11px;
    padding: 0 25px;
    min-height: 30px;
    color: #ffffff;
    white-space: nowrap;
    border-right: 1px solid #393b44;
    font-size: 13px;
}

.ems-ticker-sport {
    color: #a1a6b0;
    font-size: 10px;
    font-weight: 900;
}

.ems-ticker-status {
    font-size: 10px;
    font-weight: 950;
}

.ems-ticker-live { color: #ff4652; }
.ems-ticker-final { color: #a1a6b0; }
.ems-ticker-upcoming { color: #d6a84b; }

.ems-ticker-score {
    font-size: 18px;
    font-weight: 950;
    font-variant-numeric: tabular-nums;
}

.ems-ticker-detail {
    color: #a1a6b0;
    font-size: 11px;
}

.ems-ticker-separator {
    color: #e0353e;
    font-weight: 900;
}

@keyframes ems-ticker-scroll {
    from { transform: translateX(0); }
    to { transform: translateX(-50%); }
}

@keyframes ems-ticker-pulse {
    0%,100% { opacity: 1; }
    50% { opacity: .35; }
}

@media(prefers-reduced-motion: reduce) {
    .ems-ticker-track,
    .ems-ticker-light {
        animation: none !important;
    }
}

</style>
""", unsafe_allow_html=True)







# ============================================================
# EASYMONEYSCHULZ LIVE SCOREBOARD
# ESPN public scoreboard feeds — unofficial data source
# ============================================================

EMS_SCOREBOARD_ENDPOINTS = {
    "NFL": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    "College Football": "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard",
    "NBA": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
}


def ems_team_logo(team):
    """Extract the first usable ESPN team logo URL."""
    if not isinstance(team, dict):
        return ""

    direct = team.get("logo")
    if isinstance(direct, str) and direct.startswith("https://"):
        return direct

    logos = team.get("logos", [])
    if isinstance(logos, list):
        for item in logos:
            if isinstance(item, dict):
                url = item.get("href", "")
                if url.startswith("https://"):
                    return url

    return ""

@st.cache_data(ttl=180, show_spinner=False)
def ems_fetch_scores(sport):
    url = EMS_SCOREBOARD_ENDPOINTS[sport]

    response = requests.get(
        url,
        params={"limit": 100},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=12
    )
    response.raise_for_status()

    payload = response.json()
    games = []

    for event in payload.get("events", []):
        competitions = event.get("competitions", [])
        if not competitions:
            continue

        competition = competitions[0]
        competitors = competition.get("competitors", [])

        home = next(
            (c for c in competitors if c.get("homeAway") == "home"),
            {}
        )
        away = next(
            (c for c in competitors if c.get("homeAway") == "away"),
            {}
        )

        status = competition.get("status", event.get("status", {}))
        status_type = status.get("type", {})

        games.append({
            "event_id": str(event.get("id", "")),
            "date": event.get("date", ""),
            "away": away.get("team", {}).get("displayName", "TBD"),
            "home": home.get("team", {}).get("displayName", "TBD"),
            "away_abbr": away.get("team", {}).get("abbreviation", ""),
            "home_abbr": home.get("team", {}).get("abbreviation", ""),
            "away_score": away.get("score", "—"),
            "away_logo": ems_team_logo(away.get("team", {})),
            "home_score": home.get("score", "—"),
            "home_logo": ems_team_logo(home.get("team", {})),
            "state": status_type.get("state", "pre"),
            "status": status_type.get("shortDetail", "Scheduled"),
            "clock": status.get("displayClock", ""),
            "period": status.get("period", 0),
            "venue": competition.get("venue", {}).get("fullName", ""),
        })

    return games





def ems_render_score_row(game):
    import html

    state = game.get("state", "pre")

    if state == "in":
        label = "LIVE"
        color = "#ff3945"
    elif state == "post":
        label = "FINAL"
        color = "#9298a2"
    else:
        label = "UPCOMING"
        color = "#d6a84b"

    away_name = str(game.get("away", "Away"))
    home_name = str(game.get("home", "Home"))

    away_score = game.get("away_score", "—")
    home_score = game.get("home_score", "—")

    def numeric_score(value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    away_num = numeric_score(away_score)
    home_num = numeric_score(home_score)

    away_color = "#ffffff"
    home_color = "#ffffff"

    if state in ("in", "post"):
        if away_num is not None and home_num is not None:
            if away_num > home_num:
                away_color = "#ff4652"
            elif home_num > away_num:
                home_color = "#ff4652"

    period = game.get("period", "")
    clock = game.get("clock", "")
    status = game.get("status", "Scheduled")

    if state == "in":
        detail = f"PERIOD {period}  ·  {clock}"
    else:
        detail = status

    venue = game.get("venue", "")

    # Premium native Streamlit game card
    with st.container(border=True):

        status_col, venue_col = st.columns([1, 2])

        with status_col:
            if state == "in":
                st.markdown(
                    '<div class="ems-broadcast-live">'
                    '<span class="ems-broadcast-dot"></span>'
                    'LIVE NOW</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="ems-broadcast-status" '
                    f'style="color:{color}">{label}</div>',
                    unsafe_allow_html=True
                )

        with venue_col:
            if venue:
                st.markdown(
                    f'<div class="ems-broadcast-venue">'
                    f'{html.escape(str(venue))}</div>',
                    unsafe_allow_html=True
                )

        st.markdown(
            f'<div class="ems-broadcast-detail">'
            f'{html.escape(str(detail))}</div>',
            unsafe_allow_html=True
        )

        st.markdown('<div class="ems-broadcast-matchup">', 
                    unsafe_allow_html=True)

        away_col, center_col, home_col = st.columns(
            [1.2, 0.8, 1.2],
            vertical_alignment="center"
        )

        with away_col:
            st.markdown(
                '<div class="ems-broadcast-team">',
                unsafe_allow_html=True
            )

            away_logo = game.get("away_logo", "")
            if away_logo and str(away_logo).startswith("https://"):
                st.image(away_logo, width=90)
            else:
                st.markdown(
                    f"### {html.escape(str(game.get('away_abbr', '?')))}"
                )

            st.markdown(
                f'<div class="ems-broadcast-team-name">'
                f'{html.escape(away_name)}</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="ems-broadcast-score" '
                f'style="color:{away_color}">'
                f'{html.escape(str(away_score))}</div>',
                unsafe_allow_html=True
            )

        with center_col:
            st.markdown(
                '<div class="ems-broadcast-center">'
                '<div class="ems-broadcast-vs">VS</div>'
                '</div>',
                unsafe_allow_html=True
            )

        with home_col:
            st.markdown(
                '<div class="ems-broadcast-team">',
                unsafe_allow_html=True
            )

            home_logo = game.get("home_logo", "")
            if home_logo and str(home_logo).startswith("https://"):
                st.image(home_logo, width=90)
            else:
                st.markdown(
                    f"### {html.escape(str(game.get('home_abbr', '?')))}"
                )

            st.markdown(
                f'<div class="ems-broadcast-team-name">'
                f'{html.escape(home_name)}</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="ems-broadcast-score" '
                f'style="color:{home_color}">'
                f'{html.escape(str(home_score))}</div>',
                unsafe_allow_html=True
            )

        st.markdown('</div>', unsafe_allow_html=True)



# STEP 70B — FORCE PREMIUM SPORTS TABS
st.markdown("""
<style>

/* Full-width sports navigation */
div[data-testid="stTabs"] {
    width: 100% !important;
}

div[data-testid="stTabs"] [data-baseweb="tab-list"] {
    display: flex !important;
    width: 100% !important;
    gap: 18px !important;
    border: none !important;
    background: transparent !important;
    padding: 18px 5px 24px 5px !important;
}

/* Large dimensional buttons */
div[data-testid="stTabs"] button[data-baseweb="tab"],
div[data-testid="stTabs"] button[role="tab"] {
    flex: 1 1 0 !important;
    min-width: 0 !important;
    height: 92px !important;
    background: linear-gradient(
        145deg, #292d38, #11131a
    ) !important;
    border: 1px solid #505665 !important;
    border-bottom: 5px solid #050609 !important;
    border-radius: 13px !important;
    color: #ffffff !important;
    font-size: 21px !important;
    font-weight: 950 !important;
    letter-spacing: 1px !important;
    box-shadow:
        0 8px 0 #050609,
        0 13px 24px rgba(0,0,0,.55),
        inset 0 1px 0 rgba(255,255,255,.13) !important;
    transition: all .22s ease !important;
}

/* Make tab lettering larger */
div[data-testid="stTabs"] button[data-baseweb="tab"] p,
div[data-testid="stTabs"] button[role="tab"] p {
    color: #ffffff !important;
    font-size: 21px !important;
    font-weight: 950 !important;
}

/* Hover lift */
div[data-testid="stTabs"] button[data-baseweb="tab"]:hover,
div[data-testid="stTabs"] button[role="tab"]:hover {
    transform: translateY(-5px) !important;
    border-color: #ff3945 !important;
    box-shadow:
        0 11px 0 #050609,
        0 18px 30px rgba(224,53,62,.3) !important;
}

/* Selected red metallic panel */
div[data-testid="stTabs"] button[aria-selected="true"] {
    background: linear-gradient(
        145deg, #b72b35, #511018
    ) !important;
    border: 1px solid #ff606a !important;
    border-bottom: 5px solid #ff3945 !important;
    color: #ffffff !important;
    box-shadow:
        0 8px 0 #21070a,
        0 13px 32px rgba(224,53,62,.4),
        inset 0 1px 0 rgba(255,255,255,.2) !important;
}

/* Hide default underline indicator */
div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    background: #ff3945 !important;
    height: 5px !important;
}

@media(max-width:650px) {
    div[data-testid="stTabs"] button[data-baseweb="tab"],
    div[data-testid="stTabs"] button[role="tab"] {
        height: 72px !important;
        font-size: 13px !important;
        padding: 8px 3px !important;
    }

    div[data-testid="stTabs"] button[data-baseweb="tab"] p {
        font-size: 13px !important;
    }
}

@media(prefers-reduced-motion: reduce) {
    div[data-testid="stTabs"] button {
        transition: none !important;
        transform: none !important;
    }
}

</style>
""", unsafe_allow_html=True)


pages = [
    "🏠 Overview",
    "🏈 NFL Picks",
    "🏟️ College Football",
    "🏀 NBA Projections",
    "📊 Model Performance",
    "📈 Weekly Units",
    "🔴 Live Scores"
]



# STEP 73B — GLOBAL EMS SPORTS WIRE
# Runs above branding on every navigation page.



# STEP 72D — LIVE SPORTS WIRE

import html

ticker_games = []
ticker_errors = []

for ticker_sport in ["NFL", "College Football", "NBA"]:
    try:
        for game in ems_fetch_scores(ticker_sport):
            item = dict(game)
            item["ticker_sport"] = ticker_sport
            ticker_games.append(item)
    except requests.RequestException:
        ticker_errors.append(ticker_sport)

state_order = {"in": 0, "pre": 1, "post": 2}
ticker_games.sort(
    key=lambda g: state_order.get(g.get("state"), 3)
)

ticker_items = []

for game in ticker_games:
    state = game.get("state", "pre")

    away = html.escape(str(
        game.get("away_abbr") or game.get("away", "AWAY")
    ))
    home = html.escape(str(
        game.get("home_abbr") or game.get("home", "HOME")
    ))

    away_score = html.escape(str(game.get("away_score", "—")))
    home_score = html.escape(str(game.get("home_score", "—")))

    if state == "in":
        status = "LIVE"
        detail = "Q{} {}".format(
            game.get("period", ""),
            game.get("clock", "")
        )
        status_class = "ems-ticker-live"
    elif state == "post":
        status = "FINAL"
        detail = game.get("status", "Final")
        status_class = "ems-ticker-final"
    else:
        status = "UPCOMING"
        detail = game.get("status", "Scheduled")
        status_class = "ems-ticker-upcoming"

    sport = html.escape(game["ticker_sport"].upper())
    detail = html.escape(str(detail))

    ticker_items.append(
        '<div class="ems-ticker-item">'
        '<span class="ems-ticker-sport">' + sport + '</span>'
        '<span class="ems-ticker-status ' + status_class + '">'
        + status + '</span>'
        '<strong>' + away + '</strong>'
        '<span class="ems-ticker-score">' + away_score + '</span>'
        '<span class="ems-ticker-separator">—</span>'
        '<span class="ems-ticker-score">' + home_score + '</span>'
        '<strong>' + home + '</strong>'
        '<span class="ems-ticker-detail">' + detail + '</span>'
        '</div>'
    )

if ticker_items:
    ticker_content = "".join(ticker_items)

    ticker_html = (
        '<div class="ems-ticker-shell">'
        '<div class="ems-ticker-heading">'
        '<span class="ems-ticker-light"></span>'
        'EMS SPORTS WIRE'
        '<span class="ems-ticker-heading-line"></span>'
        '</div>'
        '<div class="ems-ticker-window">'
        '<div class="ems-ticker-track">'
        '<div class="ems-ticker-group">' + ticker_content + '</div>'
        '<div class="ems-ticker-group" aria-hidden="true">'
        + ticker_content +
        '</div></div></div></div>'
    )

    st.markdown(ticker_html, unsafe_allow_html=True)
else:
    st.info("Sports ticker waiting for ESPN game data.")

if ticker_errors:
    st.caption(
        "Temporarily unavailable: " + ", ".join(ticker_errors)
    )


st.markdown("""
<div class="ems-pro-header">
  <div class="ems-badge-hanger" aria-hidden="true">
    <div class="ems-badge-string"></div>
    <div class="ems-badge">
      <div class="ems-badge-inner">
        <strong>EMS</strong>
        <small>PICKS</small>
      </div>
    </div>
  </div>

  <div class="ems-pro-wordmark">
    EASYMONEY<span>SCHULZ</span>
    <span class="ems-light-sweep" aria-hidden="true"></span>
  </div>
  <div class="ems-pro-tagline">
    PICKS <span>/</span> SPORTS ANALYTICS
  </div>
</div>
""", unsafe_allow_html=True)


page = st.radio(
    "Navigate",
    pages,
    horizontal=True,
    label_visibility="collapsed"
)

historical = df[df["test_type"] == "HISTORICAL_BACKTEST"]
forward = df[df["test_type"].isin(["FORWARD_PAPER","PROJECTION_TEST"])]
for model_name, export_name in [
    ("CFB V4", "cfb_v4_latest_paper_picks.csv"),
    ("NBA V2", "nba_v2_latest_player_points.csv"),
]:
    exported = load_model_export(model_name, export_name)
    if not exported.empty:
        forward = pd.concat(
            [forward[forward["model"] != model_name], exported],
            ignore_index=True,
        )


nfl_hist = historical[historical["model"] == "NFL V6.1"]
wins = int((nfl_hist["result"] == "WIN").sum())
losses = int((nfl_hist["result"] == "LOSS").sum())
pushes = int((nfl_hist["result"] == "PUSH").sum())
win_rate = 100*wins/(wins+losses) if wins+losses else None

def show_pick(selection, subtitle, detail, status):
    st.markdown(f"""
    <div class="pick-card">
        <div class="pick-title">{selection}</div>
        <div class="pick-meta">{subtitle}</div>
        <div class="pick-meta">{detail}</div>
        <div class="pick-meta status">{status}</div>
    </div>
    """, unsafe_allow_html=True)


def show_nba_prop_card(row):
    from html import escape

    player = escape(str(row["selection"]))
    opponent = escape(str(row.get("opponent", "TBD")))
    date = escape(str(row.get("game_date", "TBD")))

    projection = pd.to_numeric(
        row["prediction"], errors="coerce"
    )
    market = pd.to_numeric(
        row.get("sportsbook_points_line"), errors="coerce"
    )

    if pd.notna(projection) and pd.notna(market):
        edge = projection - market
        direction = (
            "HIGHER" if edge > 0
            else "LOWER" if edge < 0
            else "EVEN"
        )
        market_text = f"{market:.1f}"
        edge_text = f"{edge:+.1f} points"
    else:
        direction = "AWAITING LINE"
        market_text = "—"
        edge_text = "Not available"

    projection_text = (
        f"{projection:.1f}"
        if pd.notna(projection) else "—"
    )

    st.markdown(f"""
    <div class="pick-card">
        <div class="eyebrow">NBA V2 · {date}</div>
        <div class="pick-title">{player}</div>
        <div class="pick-meta">Opponent: {opponent}</div>
        <div class="pick-meta">
            MODEL PROJECTION: <b>{projection_text} PTS</b>
        </div>
        <div class="pick-meta">
            SPORTSBOOK LINE: <b>{market_text}</b>
        </div>
        <div class="pick-meta">
            MODEL EDGE: <b>{edge_text}</b>
        </div>
        <div class="pick-meta status">{direction}</div>
        <div class="pick-meta">
            Paper projection · Not a verified wager
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_editorial_pick(label, category, detail, value, footnote=""):
    from html import escape

    label = escape(str(label))
    category = escape(str(category))
    detail = escape(str(detail))
    value = escape(str(value))
    footnote = escape(str(footnote))

    st.markdown(f"""
    <div class="ems-editorial-row">
      <div class="ems-editorial-info">
        <div class="ems-editorial-category">{category}</div>
        <div class="ems-editorial-name">{label}</div>
        <div class="ems-editorial-detail">{detail}</div>
      </div>
      <div class="ems-editorial-value-block">
        <div class="ems-editorial-value">{value}</div>
        <div class="ems-editorial-footnote">{footnote}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

if page == "🏠 Overview":
    st.subheader("Command Center Overview")

    a,b,c,d = st.columns(4)
    a.metric("NFL Historical Win %", f"{win_rate:.2f}%" if win_rate is not None else "N/A")
    b.metric("NFL Historical Record", f"{wins}-{losses}-{pushes}")
    c.metric("Forward Tests", len(forward))
    d.metric("Pending Results", int((forward["result"]=="PENDING").sum()))



    st.subheader("Featured Model Selections")
    st.caption("Forward paper testing — not verified wagers")

    cfb = forward[forward["model"] == "CFB V4"]

    for _, row in cfb.iterrows():
        spread = pd.to_numeric(row["market_line"], errors="coerce")
        spread_text = f"{spread:+g}" if pd.notna(spread) else "N/A"

        show_editorial_pick(
            f"{row['selection']} {spread_text}",
            "CFB V4 · PAPER LEAN",
            "vs Boise State · Nov 7, 2026",
            "3.08",
            "Model edge · points"
        )

    st.subheader("NBA Player Point Projections")
    st.caption(
        "Projected points only — sportsbook lines not yet imported"
    )

    nba = forward[forward["model"] == "NBA V2"]

    for _, row in nba.iterrows():
        points = pd.to_numeric(
            row["prediction"], errors="coerce"
        )
        projection = f"{points:.1f}" if pd.notna(points) else "—"

        opponent = row.get("opponent", "TBD")
        date = row.get("game_date", "TBD")

        show_editorial_pick(
            row["selection"],
            "NBA V2 · POINTS PROJECTION",
            f"vs {opponent} · {date}",
            projection,
            "Projected PTS · Line pending"
        )

elif page == "🏈 NFL Picks":
    import html as nfl_html

    st.markdown("""
    <style>
    .ems-nfl-pick {
        background: #17191f;
        border: 1px solid #30323a;
        border-radius: 12px;
        padding: 28px 30px;
        margin: 22px 0;
    }
    .ems-nfl-top {
        display: flex;
        justify-content: space-between;
        gap: 15px;
        margin-bottom: 22px;
        color: #a1a1aa;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .ems-nfl-status {
        color: #ff4555;
    }
    .ems-nfl-main {
        display: flex;
        align-items: center;
        gap: 22px;
    }
    .ems-nfl-logo {
        width: 92px;
        height: 92px;
        object-fit: contain;
        flex-shrink: 0;
    }
    .ems-nfl-team {
        flex: 1;
        min-width: 0;
    }
    .ems-nfl-team-name {
        color: #fff;
        font-size: 29px;
        font-weight: 850;
        line-height: 1.15;
    }
    .ems-nfl-opponent {
        color: #a8aab5;
        font-size: 15px;
        margin-top: 8px;
    }
    .ems-nfl-edge {
        color: #b8bbc6;
        font-size: 13px;
        margin-top: 10px;
    }
    .ems-nfl-spread {
        color: #fff;
        font-size: clamp(36px, 5vw, 66px);
        font-weight: 900;
        letter-spacing: -2px;
        text-align: right;
        white-space: nowrap;
        line-height: 1;
    }
    .ems-nfl-spread-label {
        color: #ff4555;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 1.5px;
        text-align: right;
        margin-top: 10px;
    }
    .ems-nfl-footer {
        border-top: 1px solid #34363e;
        padding-top: 15px;
        margin-top: 22px;
        color: #a8aab5;
        font-size: 13px;
    }
    @media (max-width: 650px) {
        .ems-nfl-pick { padding: 18px 14px; }
        .ems-nfl-main { gap: 10px; }
        .ems-nfl-logo { width: 48px; height: 48px; }
        .ems-nfl-team-name { font-size: 18px; }
        .ems-nfl-opponent { font-size: 12px; }
        .ems-nfl-spread { font-size: 32px; }
    }
    </style>
    """, unsafe_allow_html=True)


    # NFL V6.1 - read-only weekly research matchup cards
    from nfl_research_dashboard import render_nfl_research
    render_nfl_research(BASE)

    # Forward paper selections are displayed above by render_nfl_research,
    # directly from the latest GitHub Actions odds-backed artifact.

    st.caption(
        f"Historical backtest win rate: {win_rate:.2f}%. "
        "Historical results are not real-money results."
    )

elif page == "🏟️ College Football":
    import html as cfb_html

    st.markdown("""
    <style>
    .ems-cfb-pick {
        background: #17191f;
        border: 1px solid #30323a;
        border-radius: 12px;
        padding: 28px 30px;
        margin: 22px 0;
    }
    .ems-cfb-top {
        display: flex;
        justify-content: space-between;
        gap: 15px;
        margin-bottom: 22px;
        color: #a1a1aa;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .ems-cfb-status {
        color: #ff4555;
    }
    .ems-cfb-main {
        display: flex;
        align-items: center;
        gap: 22px;
    }
    .ems-cfb-logo {
        width: 92px;
        height: 92px;
        object-fit: contain;
        flex-shrink: 0;
    }
    .ems-cfb-team {
        flex: 1;
        min-width: 0;
    }
    .ems-cfb-team-name {
        color: #fff;
        font-size: 29px;
        font-weight: 850;
        line-height: 1.15;
    }
    .ems-cfb-opponent {
        color: #a8aab5;
        font-size: 15px;
        margin-top: 8px;
    }
    .ems-cfb-edge {
        color: #b8bbc6;
        font-size: 13px;
        margin-top: 10px;
    }
    .ems-cfb-spread {
        color: #fff;
        font-size: clamp(36px, 5vw, 66px);
        font-weight: 900;
        letter-spacing: -2px;
        text-align: right;
        white-space: nowrap;
        line-height: 1;
    }
    .ems-cfb-spread-label {
        color: #ff4555;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 1.5px;
        text-align: right;
        margin-top: 10px;
    }
    .ems-cfb-footer {
        border-top: 1px solid #34363e;
        padding-top: 15px;
        margin-top: 22px;
        color: #a8aab5;
        font-size: 13px;
    }
    @media (max-width: 650px) {
        .ems-cfb-pick { padding: 18px 14px; }
        .ems-cfb-main { gap: 10px; }
        .ems-cfb-logo { width: 48px; height: 48px; }
        .ems-cfb-team-name { font-size: 18px; }
        .ems-cfb-opponent { font-size: 12px; }
        .ems-cfb-spread { font-size: 32px; }
    }
    </style>
    """, unsafe_allow_html=True)

    st.subheader("CFB V4 — Qualified Paper Picks")
    cfb = forward[forward["model"] == "CFB V4"].copy()

    # ESPN logo ID for the currently qualified selection.
    # Other teams show a fallback until their IDs are mapped.
    cfb_logo_ids = {
        "Colorado State": "36"
    }

    if cfb.empty:
        st.info("No qualifying CFB paper selections.")
    else:
        for _, record in cfb.iterrows():
            team = str(record["selection"])
            line = pd.to_numeric(record["market_line"], errors="coerce")
            projection = pd.to_numeric(record["prediction"], errors="coerce")
            status = str(record["result"]).upper()

            logo_id = cfb_logo_ids.get(team)
            if logo_id:
                logo_html = (
                    '<img class="ems-cfb-logo" '
                    f'src="https://a.espncdn.com/i/teamlogos/ncaa/500/{logo_id}.png" '
                    f'alt="{cfb_html.escape(team, quote=True)} logo">'
                )
            else:
                logo_html = '<div class="ems-cfb-logo"></div>'

            spread = f"{line:+g}" if pd.notna(line) else "—"

            # Model projection is the selected team's expected margin.
            model_margin = (
                f"{projection:+.2f}"
                if pd.notna(projection) else "—"
            )
            edge = (
                f"{projection + line:+.2f}"
                if pd.notna(projection) and pd.notna(line)
                else "—"
            )

            card = f"""
            <div class="ems-cfb-pick">
                <div class="ems-cfb-top">
                    <span>CFB V4 · QUALIFIED PAPER PICK</span>
                    <span class="ems-cfb-status">{cfb_html.escape(status)}</span>
                </div>
                <div class="ems-cfb-main">
                    {logo_html}
                    <div class="ems-cfb-team">
                        <div class="ems-cfb-team-name">{cfb_html.escape(team)}</div>
                        <div class="ems-cfb-opponent">vs {cfb_html.escape(str(record.get("opponent", "Opponent TBD")))}</div>
                        <div class="ems-cfb-edge">Model edge: {edge} pts</div>
                    </div>
                    <div>
                        <div class="ems-cfb-spread">{spread}</div>
                        <div class="ems-cfb-spread-label">THE PICK</div>
                    </div>
                </div>
                <div class="ems-cfb-footer">
                    Model projected margin: {model_margin} pts · Paper testing only
                </div>
            </div>
            """
            st.markdown(card, unsafe_allow_html=True)

elif page == "🏀 NBA Projections":
    import html as nba_html

    st.markdown("""
    <style>
    .ems-nba-date {
        color: #f4f4f6;
        font-size: 23px;
        font-weight: 800;
        margin: 25px 0 10px;
    }
    .ems-nba-count {
        color: #999ba7;
        font-size: 13px;
        font-weight: 500;
        margin-left: 12px;
    }
    .ems-nba-scroll {
        width: 100%;
        overflow-x: auto;
        margin-bottom: 22px;
    }
    .ems-nba-table {
        width: 100%;
        border-collapse: collapse;
        background: #111318;
        color: #f1f1f4;
        font-size: 14px;
        min-width: 720px;
    }
    .ems-nba-table th {
        text-align: left;
        background: #181a21;
        color: #f04450;
        padding: 13px 12px;
        font-size: 11px;
        letter-spacing: 1px;
        font-weight: 800;
        border-bottom: 1px solid #9f2934;
    }
    .ems-nba-table td {
        padding: 13px 12px;
        border-bottom: 1px solid #292b33;
        white-space: nowrap;
    }
    .ems-nba-table tr:hover td {
        background: #1c2029;
    }
    .ems-nba-player {
        font-weight: 700;
        color: #ffffff;
    }
    .ems-nba-projection {
        color: #ff505e;
        font-weight: 800;
    }
    .ems-nba-muted {
        color: #999ba7;
    }
    .ems-nba-over {
        color: #55d6a0;
        font-weight: 800;
    }
    .ems-nba-under {
        color: #ffb86c;
        font-weight: 800;
    }
    .ems-nba-footnote {
        color: #999ba7;
        font-size: 12px;
        margin-top: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.subheader("🏀 NBA Player Points — OVER / UNDER")
    st.caption("Paper-testing dashboard. OVER/UNDER only appears when a sportsbook line matches the player and game.")
    @st.cache_data(ttl=120, show_spinner=False)
    def load_nba_top5():
        import io
        url = "https://raw.githubusercontent.com/easymoneyschulz/sports-betting-command-center/main/public_data/nba_v2_daily_top5.csv"
        try:
            response = requests.get(url, timeout=12)
            response.raise_for_status()
            return pd.read_csv(io.StringIO(response.text))
        except (requests.RequestException, ValueError, pd.errors.ParserError):
            return pd.DataFrame()

    top5 = load_nba_top5()
    central_today = pd.Timestamp.now(tz="America/Chicago").date()
    if not top5.empty and "game_date" in top5.columns:
        top5["game_date"] = pd.to_datetime(top5["game_date"], errors="coerce").dt.date
        top5 = top5[top5["game_date"] >= central_today]
        if not top5.empty:
            top5 = top5[top5["game_date"] == top5["game_date"].min()]
    if not top5.empty:
        st.markdown("**Upcoming OVER / UNDER paper picks**")
        for _, pick in top5.head(5).iterrows():
            st.markdown(f"**{pick['player_name']} — {pick['side']} {float(pick['market_line']):.1f} points** · {pick['sportsbook']} ({int(pick['price']):+d})")
            st.caption(f"Model: {pick.get('model_version', 'NBA V2')} · Projection {float(pick['v2_projection']):.1f} · Edge {float(pick['edge']):+.1f} pts · PAPER")
    else:
        st.info("No qualifying OVER / UNDER picks for the upcoming slate. The model does not force selections.")
    st.divider()

    st.caption("Only verified, qualifying OVER / UNDER selections are shown above. Other player projections are not picks. Paper testing only.")

elif page == "📊 Model Performance":
    st.subheader("NFL V6.1 — Historical Backtest")
    a,b = st.columns(2)
    a.metric("Historical Record",f"{wins}-{losses}-{pushes}")
    b.metric("Win Rate",f"{win_rate:.2f}%")

    st.subheader("Forward Test Status")
    st.dataframe(
        forward.groupby(["model","result"]).size().reset_index(name="Count"),
        use_container_width=True,
        hide_index=True
    )




elif page == "📈 Weekly Units":
    import pandas as units_pd
    import html as units_html
    from pathlib import Path as UnitsPath

    st.markdown("""
    <style>
    .ems-u-head {
        color:#fff;font-size:30px;font-weight:900;
        letter-spacing:-.6px;margin:15px 0 4px;
    }
    .ems-u-sub {
        color:#a1a1aa;font-size:12px;font-weight:700;
        letter-spacing:1px;margin-bottom:23px;
    }
    .ems-u-stats {
        display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
        gap:12px;margin-bottom:22px;
    }
    .ems-u-stat {
        background:#17191f;border:1px solid #30323a;
        border-radius:12px;padding:20px;
    }
    .ems-u-label {
        color:#a1a1aa;font-size:11px;font-weight:800;
        letter-spacing:1px;
    }
    .ems-u-number {
        color:#fff;font-size:31px;font-weight:900;
        margin-top:7px;
    }
    .ems-u-chart {
        background:#17191f;border:1px solid #30323a;
        border-radius:12px;padding:25px;margin-bottom:26px;
    }
    .ems-u-chart-title {
        color:#fff;font-size:20px;font-weight:850;
        margin-bottom:5px;
    }
    .ems-u-chart-desc {
        color:#a1a1aa;font-size:12px;margin-bottom:20px;
    }
    .ems-u-svg {
        width:100%;height:auto;display:block;
    }
    .ems-u-section {
        color:#fff;font-size:21px;font-weight:850;
        margin:25px 0 13px;
    }
    .ems-u-win {
        display:flex;align-items:center;gap:18px;
        background:#17191f;border:1px solid #30323a;
        border-left:4px solid #ff4555;
        border-radius:12px;padding:19px 23px;
    }
    .ems-u-logo {
        width:72px;height:72px;object-fit:contain;
        flex-shrink:0;
    }
    .ems-u-team {flex:1;min-width:0;}
    .ems-u-team-name {
        color:#fff;font-size:23px;font-weight:850;
    }
    .ems-u-meta {
        color:#a1a1aa;font-size:12px;margin-top:6px;
    }
    .ems-u-result {
        text-align:right;white-space:nowrap;
    }
    .ems-u-result-spread {
        color:#fff;font-size:32px;font-weight:900;
    }
    .ems-u-result-win {
        color:#49d394;font-size:13px;
        font-weight:850;letter-spacing:1px;
    }
    .ems-u-result-units {
        color:#49d394;font-size:16px;
        font-weight:850;margin-top:5px;
    }
    @media(max-width:650px) {
        .ems-u-stat {padding:12px 9px;}
        .ems-u-number {font-size:21px;}
        .ems-u-label {font-size:9px;}
        .ems-u-chart {padding:15px;}
        .ems-u-win {gap:10px;padding:13px;}
        .ems-u-logo {width:46px;height:46px;}
        .ems-u-team-name {font-size:16px;}
        .ems-u-result-spread {font-size:23px;}
        .ems-u-meta {font-size:10px;}
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="ems-u-head">WEEKLY PERFORMANCE</div>'
        '<div class="ems-u-sub">'
        'EASYMONEYSCHULZ · VERIFIED BETTING RESULTS · UNITS ONLY'
        '</div>',
        unsafe_allow_html=True
    )

    units_file = (
        UnitsPath(__file__).resolve().parent
        / "public_data" / "weekly_units.csv"
    )

    if not units_file.exists():
        st.info("No weekly results published yet.")
    else:
        weekly = units_pd.read_csv(units_file)
        weekly["week_start"] = units_pd.to_datetime(
            weekly["week_start"], errors="coerce"
        )
        for col in ["net_units", "wins", "losses"]:
            weekly[col] = units_pd.to_numeric(
                weekly[col], errors="coerce"
            )

        weekly = weekly.dropna(
            subset=["week_start", "net_units"]
        ).sort_values("week_start")

        if weekly.empty:
            st.info("No verified weekly results published yet.")
        else:
            net = float(weekly["net_units"].sum())
            wins = int(weekly["wins"].fillna(0).sum())
            losses = int(weekly["losses"].fillna(0).sum())
            rate = 100*wins/(wins+losses) if wins+losses else 0

            net_color = "#49d394" if net >= 0 else "#ff4555"

            st.markdown(f"""
            <div class="ems-u-stats">
              <div class="ems-u-stat">
                <div class="ems-u-label">NET UNITS</div>
                <div class="ems-u-number" style="color:{net_color}">
                  {net:+.2f}u
                </div>
              </div>
              <div class="ems-u-stat">
                <div class="ems-u-label">WIN RATE</div>
                <div class="ems-u-number">{rate:.1f}%</div>
              </div>
              <div class="ems-u-stat">
                <div class="ems-u-label">RECORD</div>
                <div class="ems-u-number">{wins}-{losses}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # EMS DAILY CUMULATIVE GROWTH GRAPH
            # Only known daily results are plotted.
            from datetime import date, timedelta

            today = date.today()
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)

            days = [monday + timedelta(days=i) for i in range(7)]

            # Chicago is our only currently recorded daily result.
            daily_changes = {}
            chicago_row = weekly[
                weekly["week_start"] == units_pd.Timestamp("2026-11-02")
            ]
            if (
                monday == date(2026, 11, 2)
                and len(chicago_row) == 1
                and float(chicago_row.iloc[0]["net_units"]) == 2.0
                and int(chicago_row.iloc[0]["wins"]) == 1
                and int(chicago_row.iloc[0]["losses"]) == 0
            ):
                daily_changes[date(2026, 11, 2)] = 2.0

            W, H = 850, 360
            L, R, T, B = 72, 35, 30, 60
            plot_w, plot_h = W-L-R, H-T-B

            cumulative = 0.0
            plotted = [(0.0, 0.0)]

            for i, day in enumerate(days):
                if day > today:
                    break
                cumulative += daily_changes.get(day, 0.0)
                plotted.append((i + 1.0, cumulative))

            vals = [v for _, v in plotted]
            low = min(0.0, min(vals))
            high = max(2.0, max(vals))
            padding = max(0.5, (high-low)*0.15)
            ymin = min(0.0, low-padding)
            ymax = high+padding

            def xcoord(day_index):
                return L + day_index * plot_w / 7

            def ycoord(units):
                return T + (ymax-units)/(ymax-ymin)*plot_h

            grid = []
            for j in range(5):
                v = ymin+(ymax-ymin)*j/4
                y = ycoord(v)
                grid.append(
                    f'<line x1="{L}" y1="{y:.1f}" '
                    f'x2="{W-R}" y2="{y:.1f}" '
                    'stroke="#343943" stroke-dasharray="4 6"/>'
                    f'<text x="{L-12}" y="{y+4:.1f}" '
                    'text-anchor="end" fill="#a1a1aa" '
                    f'font-size="12">{v:.1f}u</text>'
                )

            labels = []
            for i, day in enumerate(days):
                labels.append(
                    f'<text x="{xcoord(i+0.5):.1f}" y="{H-20}" '
                    'text-anchor="middle" fill="#a1a1aa" '
                    f'font-size="12">{day.strftime("%a").upper()}</text>'
                )

            points = [
                (xcoord(i), ycoord(value))
                for i, value in plotted
            ]
            line_points = " ".join(
                f"{x:.1f},{y:.1f}" for x, y in points
            )

            last_x, last_y = points[-1]
            latest = plotted[-1][1]

            # Gradient fill below the line, down to zero baseline.
            baseline_y = ycoord(0.0)
            area_points = (
                line_points
                + f" {last_x:.1f},{baseline_y:.1f}"
                + f" {L:.1f},{baseline_y:.1f}"
            )

            svg = (
                f'<svg class="ems-u-svg" viewBox="0 0 {W} {H}" '
                'xmlns="http://www.w3.org/2000/svg">'
                '<defs>'
                '<linearGradient id="emsGrowthFill" '
                'x1="0" y1="0" x2="0" y2="1">'
                '<stop offset="0%" stop-color="#ff4555" '
                'stop-opacity=".32"/>'
                '<stop offset="100%" stop-color="#ff4555" '
                'stop-opacity="0"/>'
                '</linearGradient>'
                '</defs>'
                + "".join(grid)
                + "".join(labels)
                + f'<polygon points="{area_points}" '
                'fill="url(#emsGrowthFill)"/>'
                + f'<polyline points="{line_points}" '
                'fill="none" stroke="#ff4555" '
                'stroke-width="4" stroke-linecap="round" '
                'stroke-linejoin="round"/>'
                + f'<circle cx="{last_x:.1f}" cy="{last_y:.1f}" '
                'r="7" fill="#ff4555" stroke="#fff" '
                'stroke-width="2"/>'
                + f'<text x="{min(last_x+16,W-100):.1f}" '
                f'y="{max(20,last_y-16):.1f}" '
                'fill="#fff" font-size="18" font-weight="900">'
                f'{latest:+.2f}u</text>'
                '</svg>'
            )

            st.markdown(
                '<div class="ems-u-chart">'
                '<div class="ems-u-chart-title">WEEKLY UNIT GROWTH</div>'
                '<div class="ems-u-chart-desc">'
                f'{monday.strftime("%b %d")} – '
                f'{sunday.strftime("%b %d, %Y")} '
                '· Cumulative daily net units'
                '</div>'
                + svg + '</div>',
                unsafe_allow_html=True
            )

            # Initial verified personal wager.
            # This is not counted as an NFL V6.1 model selection.
            chicago_week = weekly[
                weekly["week_start"] == units_pd.Timestamp("2026-11-02")
            ]
            chicago_recorded = (
                not chicago_week.empty
                and float(chicago_week.iloc[0]["net_units"]) >= 2
                and int(chicago_week.iloc[0]["wins"]) >= 1
            )

            st.markdown(
                '<div class="ems-u-section">WEEKLY WINS</div>',
                unsafe_allow_html=True
            )

            if chicago_recorded:
                st.markdown("""
                <div class="ems-u-win">
                  <img class="ems-u-logo"
                       src="https://a.espncdn.com/i/teamlogos/nfl/500/chi.png"
                       alt="Chicago Bears logo">
                  <div class="ems-u-team">
                    <div class="ems-u-team-name">Chicago Bears</div>
                    <div class="ems-u-meta">
                      Nov 2, 2026 · NFL · Personal wager
                    </div>
                    <div class="ems-u-meta">
                      NFL V6.1 decision: PASS
                    </div>
                  </div>
                  <div class="ems-u-result">
                    <div class="ems-u-result-spread">+3.5</div>
                    <div class="ems-u-result-win">✓ WIN</div>
                    <div class="ems-u-result-units">+2.00u</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.caption("No individual winning wagers listed yet.")

    st.caption(
        "Personal wager results are separate from official "
        "model forward tests. No monetary amounts are displayed."
    )

elif page == "🔴 Live Scores":

    from datetime import datetime

    st.subheader("LIVE SPORTS SCOREBOARD")
    st.caption("NFL · COLLEGE FOOTBALL · NBA")

    st_autorefresh(
        interval=30_000,
        key="ems_live_score_refresh"
    )

    # Manual refresh
    _, refresh_col = st.columns([3, 1])

    with refresh_col:
        if st.button(
            "↻ REFRESH",
            key="ems_manual_score_refresh",
            use_container_width=True
        ):
            ems_fetch_scores.clear()
            st.rerun()

    # Three clickable sports tabs


    def ems_show_sport(sport):

        try:
            games = ems_fetch_scores(sport)

            live_games = [
                g for g in games if g["state"] == "in"
            ]
            upcoming_games = [
                g for g in games if g["state"] == "pre"
            ]
            completed_games = [
                g for g in games if g["state"] == "post"
            ]

            updated_at = datetime.now().astimezone().strftime(
                "%I:%M:%S %p %Z"
            )

            a, b, c, d = st.columns(4)
            a.metric("LIVE", len(live_games))
            b.metric("UPCOMING", len(upcoming_games))
            c.metric("FINAL", len(completed_games))
            d.metric("TOTAL", len(games))

            st.caption(f"Last updated: {updated_at}")

            st.divider()
            st.markdown("### 🔴 LIVE GAMES")

            if live_games:
                for game in live_games:
                    ems_render_score_row(game)
            else:
                st.info("No games currently live.")

            st.divider()
            st.markdown("### UPCOMING GAMES")

            if upcoming_games:
                for game in upcoming_games:
                    ems_render_score_row(game)
            else:
                st.caption("No upcoming games listed.")

            with st.expander(
                f"FINAL SCORES ({len(completed_games)})"
            ):
                if completed_games:
                    for game in completed_games:
                        ems_render_score_row(game)
                else:
                    st.caption("No completed games.")

            if not games:
                st.info("No games returned by the feed.")

        except requests.RequestException as error:
            st.error("Scoreboard connection unavailable.")
            st.caption(str(error))

        except Exception as error:
            st.error("Unable to process scoreboard data.")
            st.caption(str(error))


    # CUSTOM SPORTS SELECTOR — SESSION CONTROLLED

    if "ems_selected_sport" not in st.session_state:
        st.session_state["ems_selected_sport"] = "NFL"

    selected = st.session_state["ems_selected_sport"]

    nfl_col, cfb_col, nba_col = st.columns(3)

    with nfl_col:
        if st.button(
            "🏈 NFL",
            key="ems_sport_nfl",
            type="primary" if selected == "NFL" else "secondary",
            use_container_width=True
        ):
            st.session_state["ems_selected_sport"] = "NFL"
            st.rerun()

    with cfb_col:
        if st.button(
            "🏟️ COLLEGE FOOTBALL",
            key="ems_sport_cfb",
            type="primary" if selected == "College Football" else "secondary",
            use_container_width=True
        ):
            st.session_state["ems_selected_sport"] = "College Football"
            st.rerun()

    with nba_col:
        if st.button(
            "🏀 NBA",
            key="ems_sport_nba",
            type="primary" if selected == "NBA" else "secondary",
            use_container_width=True
        ):
            st.session_state["ems_selected_sport"] = "NBA"
            st.rerun()

    st.markdown(
        '<div class="ems-sport-divider"></div>',
        unsafe_allow_html=True
    )

    ems_show_sport(st.session_state["ems_selected_sport"])



st.divider()
st.caption(
    "Research and paper testing only. "
    "Historical backtests do not guarantee future results."
)
