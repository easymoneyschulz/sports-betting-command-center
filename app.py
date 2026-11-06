
import streamlit as st
import pandas as pd
import requests
from pathlib import Path

st.set_page_config(
    page_title="Easy Money Picks",
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
        response = requests.get(url, timeout=3)
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

@st.cache_data(ttl=600, show_spinner=False)
def ems_fetch_scores(sport):
    url = EMS_SCOREBOARD_ENDPOINTS[sport]

    response = requests.get(
        url,
        params={"limit": 100},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=3
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
    "🏈 Anytime TD",
    "🏟️ College Football",
    "🏀 NBA Projections",
    "📊 Model Performance",
    "📈 Weekly Units",
    "🔴 Live Scores",
    "👤 My Account"
]



page = st.radio(
    "Navigate",
    pages,
    horizontal=True,
    label_visibility="collapsed"
)

# STEP 73B — GLOBAL EMS SPORTS WIRE
# Runs above branding on every navigation page.



# STEP 72D — LIVE SPORTS WIRE

import html

ticker_games = []
ticker_errors = []

# Fetch all three score feeds concurrently, with a strict total wait budget.
# A slow ESPN response must never prevent the dashboard from rendering.
# Temporarily suspend live ticker network calls to keep the premium dashboard responsive.
# The original ticker markup and styling remain preserved below for re-enabling.
ticker_errors = []

state_order = {"in": 0, "pre": 1, "post": 2}
ticker_games.sort(
    key=lambda g: state_order.get(g.get("state"), 3)
)

ticker_items = []

for game in ticker_games[:18]:
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
elif page in ("🏠 Overview", "🔴 Live Scores"):
    st.caption("EMS Sports Wire · Live scores temporarily paused while we stabilize the dashboard.")

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



historical = df[df["test_type"] == "HISTORICAL_BACKTEST"]
forward = df[df["test_type"].isin(["FORWARD_PAPER","PROJECTION_TEST"])]
for model_name, export_name in [
    ("CFB V4", "cfb_v4_latest_paper_picks.csv"),
    ("NBA V2", "nba_v2_latest_player_points.csv"),
]:
    exported = pd.DataFrame()  # Avoid network requests on every initial page load
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

CFB_TEAM_IDS = {"Colorado State":36,"Boise State":68,"UConn":41,"North Carolina":153,"New Mexico State":166,"Liberty":2335,"Notre Dame":87,"Miami":2390,"Baylor":239,"Iowa State":66}
NBA_TEAM_IDS = {"ATL":1,"BOS":2,"BKN":17,"CHA":30,"CHI":4,"CLE":5,"DAL":6,"DEN":7,"DET":8,"GSW":9,"HOU":10,"IND":11,"LAC":12,"LAL":13,"MEM":29,"MIA":14,"MIL":15,"MIN":16,"NOP":3,"NYK":18,"OKC":25,"ORL":19,"PHI":20,"PHX":21,"POR":22,"SAC":23,"SAS":24,"TOR":28,"UTA":26,"WAS":27}
NBA_PLAYER_TEAM = {"Luka Dončić":"LAL","Tyrese Maxey":"PHI","Jamal Murray":"DEN","Toumani Camara":"POR","Peyton Watson":"DEN"}
def cfb_team_logo(name):
    team_id = CFB_TEAM_IDS.get(str(name))
    return f"https://a.espncdn.com/i/teamlogos/ncaa/500/{team_id}.png" if team_id else ""
def nba_team_logo(abbr):
    team_id = NBA_TEAM_IDS.get(str(abbr).upper())
    return f"https://a.espncdn.com/i/teamlogos/nba/500/{team_id}.png" if team_id else ""

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

    for _, row in cfb.head(5).iterrows():
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

    for _, row in nba.head(8).iterrows():
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

    st.markdown("""
    <style>
    .cfb-hero{padding:24px 26px;background:linear-gradient(115deg,#141c2a,#202a3a 65%,#172c30);border:1px solid #334155;border-radius:18px;margin:12px 0 20px}
    .cfb-eyebrow{color:#8fcfc4;font-size:11px;font-weight:800;letter-spacing:2px}
    .cfb-headline{color:#f8fafc;font-size:29px;font-weight:850;letter-spacing:-.8px;margin:7px 0}
    .cfb-description{color:#a9b7c8;font-size:13px;line-height:1.6}
    .cfb-card{display:flex;gap:17px;align-items:center;padding:19px 22px;background:linear-gradient(110deg,#181f2c,#202937);border:1px solid #334155;border-radius:15px;margin:12px 0}
    .cfb-logo{width:58px;height:58px;object-fit:contain;flex-shrink:0} .cfb-rank{color:#7d91aa;font-size:22px;font-weight:850;min-width:36px}
    .cfb-main{flex:1;min-width:0}
    .cfb-matchup{font-size:12px;color:#9aabc0;margin-bottom:6px}
    .cfb-selection{font-size:23px;font-weight:850;color:#f8fafc;line-height:1.25}
    .cfb-detail{font-size:12px;color:#9fb0c5;margin-top:8px}
    .cfb-side{text-align:right;min-width:125px}
    .cfb-edge{font-size:24px;font-weight:850;color:#e2e8f0}
    .cfb-edge-caption{font-size:10px;color:#91a4bb;text-transform:uppercase;letter-spacing:1px}
    .cfb-tag{display:inline-block;padding:5px 9px;border-radius:7px;background:#28384a;color:#b9cce0;font-size:10px;font-weight:800;letter-spacing:.7px;margin-top:8px}
    .cfb-tag-strong{background:#173f37;color:#8ce5c7}
    @media(max-width:620px){.cfb-hero{padding:19px}.cfb-headline{font-size:24px}.cfb-card{padding:14px 12px;gap:9px}.cfb-logo{width:38px;height:38px}.cfb-rank{font-size:17px;min-width:23px}.cfb-selection{font-size:17px}.cfb-side{min-width:90px}.cfb-edge{font-size:19px}.cfb-detail{font-size:11px}}
    </style>
    <div class="cfb-hero">
      <div class="cfb-eyebrow">EASY MONEY SCHULZ · COLLEGE FOOTBALL</div>
      <div class="cfb-headline">V4 Weekly Top Five</div>
      <div class="cfb-description">Five highest-ranked spread opportunities from the frozen V4 model. Ranked by projected edge, with confidence tiers shown separately.</div>
    </div>
    """, unsafe_allow_html=True)
    try:
        top5_url = "https://raw.githubusercontent.com/easymoneyschulz/sports-betting-command-center/main/public_data/cfb_v4_top5.csv"
        cfb_top5 = pd.read_csv(top5_url)
        cfb_top5["start_date"] = pd.to_datetime(cfb_top5["start_date"], utc=True, errors="coerce")
        cfb_top5 = cfb_top5[cfb_top5["start_date"].dt.tz_convert("America/Chicago").dt.date >= pd.Timestamp.now(tz="America/Chicago").date()]
        for rank, (_, pick) in enumerate(cfb_top5.sort_values("predicted_edge", ascending=False).head(5).iterrows(), 1):
            qualified = str(pick["decision"]).upper() == "PAPER LEAN"
            tier = "MODEL LEAN" if qualified else "SLIGHT LEAN"
            tier_class = "cfb-tag cfb-tag-strong" if qualified else "cfb-tag"
            kickoff = pick["start_date"].tz_convert("America/Chicago").strftime("%a %b %d, %I:%M %p CT").replace(" 0", " ")
            spread = float(pick["selected_spread"])
            edge = float(pick["predicted_edge"])
            selection = cfb_html.escape(str(pick["selected_side"]))
            matchup = cfb_html.escape(str(pick["away_team"]) + " @ " + str(pick["home_team"]))
            book = cfb_html.escape(str(pick["sportsbook"]).title())
            odds = int(pick["selected_price"])
            logo_url = cfb_team_logo(pick["selected_side"])
            logo_tag = f'<img class="cfb-logo" src="{logo_url}" alt="{selection} logo" loading="lazy">' if logo_url else ""
            card = f"""
            <div class="cfb-card">
              <div class="cfb-rank">{rank:02d}</div>
              {logo_tag}
              <div class="cfb-main">
                <div class="cfb-matchup">{matchup}</div>
                <div class="cfb-selection">{selection} {spread:+g}</div>
                <div class="cfb-detail">{kickoff} · {book} {odds:+d}</div>
              </div>
              <div class="cfb-side">
                <div class="cfb-edge">+{edge:.2f}</div>
                <div class="cfb-edge-caption">Model edge · pts</div>
                <span class="{tier_class}">{tier}</span>
              </div>
            </div>"""
            st.markdown(card, unsafe_allow_html=True)
        if cfb_top5.empty:
            st.info("No upcoming V4 selections in the current snapshot. A new model run is required.")
    except Exception:
        st.warning("The CFB weekly board is temporarily unavailable.")
    st.caption("V4 research rankings, not verified wagers. 'Model Lean' meets the 3-point paper-test threshold; 'Slight Lean' is below it. Weekly automatic reruns have not yet been verified.")

elif page == "🏈 Anytime TD":
    from td_dashboard import render
    render()

elif page == "🏀 NBA Projections":
    import html as nba_html

    # Frozen NBA V2 professional player cards; only verified sportsbook quotes show signals.
    import html as nba_card_html
    from io import StringIO as NBAStringIO
    from datetime import datetime as NBADatetime
    from zoneinfo import ZoneInfo as NBAZoneInfo
    st.markdown("### 🏀 NBA V2 — DAILY PLAYER PROPS")
    st.caption("Frozen model · Automated daily · Paper testing only · Top 10 OVER / Top 10 UNDER")

    # Distinct research feed: rolling baseline is NOT the frozen NBA V2 model.
    # Display it separately rather than silently dropping available paper ideas
    # or mislabeling them as V2 recommendations.
    with st.expander("OTHER NBA RESEARCH — ROLLING BASELINE (NOT V2)", expanded=True):
        st.caption("Experimental V0 paper comparisons only. These are NOT frozen V2 selections or verified wagers.")
        try:
            baseline_url = "https://raw.githubusercontent.com/easymoneyschulz/sports-betting-command-center/main/public_data/nba_v2_daily_top5.csv"
            baseline_response = requests.get(baseline_url, timeout=8)
            baseline_response.raise_for_status()
            baseline = pd.read_csv(NBAStringIO(baseline_response.text))
            required_baseline = {"game_date", "player_name", "side", "market_line", "edge", "model_version"}
            if not required_baseline.issubset(baseline.columns):
                st.warning("Baseline research file has missing columns.")
            else:
                today_str = NBADatetime.now(NBAZoneInfo("America/Chicago")).date().isoformat()
                baseline = baseline[
                    baseline["game_date"].astype(str).eq(today_str)
                    & baseline["model_version"].astype(str).str.contains("NOT NBA V2", regex=False, na=False)
                ].copy()
                if baseline.empty:
                    st.info("No current-day baseline research comparisons published.")
                else:
                    baseline["edge"] = pd.to_numeric(baseline["edge"], errors="coerce")
                    baseline["market_line"] = pd.to_numeric(baseline["market_line"], errors="coerce")
                    baseline = baseline.sort_values("edge", key=lambda x: x.abs(), ascending=False)
                    st.caption(f"{len(baseline)} baseline paper comparisons for {today_str}; excluded from frozen V2 records.")
                    st.dataframe(
                        baseline.rename(columns={"player_name":"Player", "side":"Side", "market_line":"Line", "edge":"Model edge", "sportsbook":"Book"})[
                            [c for c in ["Player", "Side", "Line", "Model edge", "Book"] if c in baseline.columns]
                        ], hide_index=True, use_container_width=True
                    )
        except (requests.RequestException, ValueError, pd.errors.ParserError) as err:
            st.warning(f"Baseline research feed unavailable: {type(err).__name__}")

    # Mobile-safe NBA panel styling; grading and model remain unchanged.
    st.markdown("""
    <style>
    @media (max-width: 700px) {
      [data-testid="stMetricValue"] {
        font-size: clamp(1.35rem, 5.4vw, 2rem) !important;
        overflow-wrap: anywhere !important;
        white-space: normal !important;
        line-height: 1.25 !important;
      }
      [data-testid="stMetric"] { min-width: 0 !important; padding: 14px !important; }
      [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
      [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        min-width: min(100%, 145px) !important;
        flex: 1 1 145px !important;
      }
      [data-testid="stExpander"] summary,
      [data-testid="stExpander"] summary * {
        background-color: #181a20 !important;
        color: #f3f4f6 !important;
        opacity: 1 !important;
      }
      .ems-pro-wordmark { overflow: visible !important; overflow-wrap: anywhere !important; }
    }
    </style>
    """, unsafe_allow_html=True)

    # Grade only locked pregame paper selections; exclude voids and pushes from win rate.
    try:
        nba_tracker_url = "https://raw.githubusercontent.com/easymoneyschulz/sports-betting-command-center/main/public_data/nba_v2_recovered_paper_tracker.csv"
        nba_tracker_response = requests.get(nba_tracker_url,timeout=5)
        if nba_tracker_response.ok:
            from io import StringIO as NBAHistoryIO
            nba_history = pd.read_csv(NBAHistoryIO(nba_tracker_response.text))
            if {"result","net_units"}.issubset(nba_history):
                nba_record = nba_history[nba_history.result.isin(["WIN","LOSS"])].copy()
                nba_wins = int((nba_record.result=="WIN").sum())
                nba_losses = int((nba_record.result=="LOSS").sum())
                nba_units = pd.to_numeric(nba_history.net_units,errors="coerce").fillna(0).sum()
                nba_staked = len(nba_record)
                nba_roi = (nba_units/nba_staked*100) if nba_staked else 0
                t1,t2,t3,t4 = st.columns(4)
                t1.metric("PAPER RECORD",f"{nba_wins}-{nba_losses}" if nba_staked else "Not graded")
                t2.metric("WIN RATE",f"{nba_wins/nba_staked*100:.1f}%" if nba_staked else "—")
                t3.metric("NET UNITS",f"{nba_units:+.2f}u")
                t4.metric("ROI",f"{nba_roi:+.1f}%" if nba_staked else "—")
                nba_pending = int(nba_history.result.isin(["PENDING","DNP_VOID"]).sum())
                st.caption(f"{nba_pending} selections awaiting verified grading · Locked selections only · 1-unit hypothetical stakes · Unverified and void picks excluded from win rate.")
                if nba_pending and not nba_staked:
                    st.warning("NBA results have not been verified against final player box scores. A 0–0 record would be misleading; grading is still pending.")
    except (requests.RequestException,ValueError,pd.errors.ParserError):
        pass

    nba_team_logos = {"ATL":"atl","BOS":"bos","BKN":"bkn","CHA":"cha","CHI":"chi","CLE":"cle","DAL":"dal","DEN":"den","DET":"det","GSW":"gs","HOU":"hou","IND":"ind","LAC":"lac","LAL":"lal","MEM":"mem","MIA":"mia","MIL":"mil","MIN":"min","NOP":"no","NYK":"ny","OKC":"okc","ORL":"orl","PHI":"phi","PHX":"phx","POR":"por","SAC":"sac","SAS":"sa","TOR":"tor","UTA":"utah","WAS":"wsh"}
    try:
        nba_url = "https://raw.githubusercontent.com/easymoneyschulz/sports-betting-command-center/main/public_data/nba_v2_recovered_prop_comparison.csv"
        nba_res = requests.get(nba_url, timeout=8)
        nba_res.raise_for_status()
        nba_props = pd.read_csv(NBAStringIO(nba_res.text), dtype={"player_id":str})
        nba_need = {"game_date","player_id","player_name","team","opponent","v2_projection","market_line","sportsbook","decision","edge","model_version"}
        if not nba_need.issubset(nba_props): raise ValueError("Incomplete NBA V2 comparison data")
        nba_props = nba_props[nba_props.model_version=="NBA_V2_RECOVERED_FROZEN_PAPER"].copy()
        # Never display betting signals from pre-validation or unverifiable roster snapshots.
        if "roster_verified" not in nba_props.columns:
            st.warning("NBA V2 picks paused: waiting for the new roster-verified model run. Existing historical tracking is preserved.")
            nba_props = nba_props.iloc[0:0].copy()
        else:
            nba_props = nba_props[nba_props["roster_verified"].astype(str).str.lower().eq("true")].copy()
        nba_props["game_date"] = pd.to_datetime(nba_props.game_date, errors="coerce").dt.date
        nba_today = NBADatetime.now(NBAZoneInfo("America/Chicago")).date()
        nba_props = nba_props[nba_props.game_date>=nba_today].copy()
        if nba_props.empty:
            st.info("Waiting for the next scheduled NBA V2 slate.")
        else:
            nba_dates = sorted(nba_props.game_date.dropna().unique())
            if st.session_state.get("nba_v2_selected_day") not in nba_dates:
                st.session_state["nba_v2_selected_day"] = nba_dates[0]
            st.markdown("""<style>
            .st-key-nba_v2_date_nav{background:linear-gradient(110deg,#172236,#0d1524);border:1px solid #334761;border-radius:18px;padding:16px 18px;margin:8px 0 22px;box-shadow:0 10px 32px #0004}
            .st-key-nba_v2_date_nav button{background:#18243a!important;border:1px solid #344863!important;color:#dbe6f8!important;border-radius:12px!important;font-size:14px!important;font-weight:800!important;min-height:53px!important}
            .st-key-nba_v2_date_nav button:hover{border-color:#f05a70!important;background:#26364f!important}
            .st-key-nba_v2_date_nav button:disabled{opacity:.3!important}
            .nba-v2-date-title{color:#ff657a;font-size:11px;font-weight:900;letter-spacing:2.4px;margin:2px 0 4px}
            .nba-v2-date-main{color:#fff;font-size:26px;font-weight:950;letter-spacing:-.7px;line-height:1.25}
            .nba-v2-date-sub{color:#9eafc9;font-size:12px;margin-top:5px}
            </style>""",unsafe_allow_html=True)
            nba_current_index = nba_dates.index(st.session_state["nba_v2_selected_day"])
            with st.container(key="nba_v2_date_nav"):
                nba_prev, nba_center, nba_next = st.columns([1,4,1],vertical_alignment="center")
                with nba_prev:
                    if st.button("◀ PREV",key="nba_v2_prev_day",disabled=nba_current_index==0,use_container_width=True):
                        st.session_state["nba_v2_selected_day"]=nba_dates[nba_current_index-1]
                        st.rerun()
                with nba_center:
                    nba_selected_label=st.session_state["nba_v2_selected_day"].strftime("%A, %B %d, %Y")
                    st.markdown(f'<div style="text-align:center"><div class="nba-v2-date-title">🏀 NBA PLAYER PROPS · GAME DAY</div><div class="nba-v2-date-main">{nba_selected_label}</div><div class="nba-v2-date-sub">{nba_current_index+1} OF {len(nba_dates)} AVAILABLE SLATES</div></div>',unsafe_allow_html=True)
                with nba_next:
                    if st.button("NEXT ▶",key="nba_v2_next_day",disabled=nba_current_index==len(nba_dates)-1,use_container_width=True):
                        st.session_state["nba_v2_selected_day"]=nba_dates[nba_current_index+1]
                        st.rerun()
            nba_day = st.session_state["nba_v2_selected_day"]
            nba_props = nba_props[nba_props.game_date==nba_day].copy()
            # Investor view: only the strongest verified OVER/UNDER signals,
            # up to ten on each side. No fabricated or forced recommendations.
            nba_props["edge"] = pd.to_numeric(nba_props["edge"], errors="coerce")
            nba_props["market_line"] = pd.to_numeric(nba_props["market_line"], errors="coerce")
            nba_props = nba_props[
                nba_props["decision"].isin(["OVER", "UNDER"])
                & nba_props["market_line"].notna()
                & nba_props["edge"].notna()
            ].copy()
            nba_props["abs_edge_rank"] = nba_props["edge"].abs()
            nba_props = (nba_props.sort_values(
                ["abs_edge_rank", "player_name"], ascending=[False, True]
            ).groupby("decision", group_keys=False).head(10).copy())
            st.caption("Top 10 verified OVERs and top 10 verified UNDERs by model-to-line edge. Fewer shown when fewer qualify; no forced picks.")
            st.markdown("""<style>
.st-key-nba_v2_cards_status [data-testid="stSegmentedControl"],.st-key-nba_v2_cards_status [role="radiogroup"]{background:transparent!important;border:0!important;gap:10px!important}
.st-key-nba_v2_cards_status button,.st-key-nba_v2_cards_status [role="radio"]{background:#151e2e!important;color:#dce5f4!important;border:1px solid #35455f!important;border-radius:11px!important;padding:10px 20px!important;min-height:46px!important;font-size:12px!important;font-weight:850!important;letter-spacing:1.2px!important;box-shadow:0 5px 16px #0003!important}
.st-key-nba_v2_cards_status button:hover,.st-key-nba_v2_cards_status [role="radio"]:hover{background:#22324a!important;border-color:#ed4e64!important;color:#fff!important}
.st-key-nba_v2_cards_status button[aria-checked="true"],.st-key-nba_v2_cards_status button[aria-pressed="true"],.st-key-nba_v2_cards_status [role="radio"][aria-checked="true"],.st-key-nba_v2_cards_status [data-state="checked"]{background:#542034!important;border-color:#ff5068!important;color:#fff!important;box-shadow:0 4px 20px #ed4e6429!important}
.st-key-nba_v2_cards_status button *,.st-key-nba_v2_cards_status [role="radio"] *{color:inherit!important}
</style>""",unsafe_allow_html=True)
            nba_filter = st.segmented_control("FILTER PLAYER PROPS", ["All","OVER","UNDER","PASS","WAIT"], default="All", key="nba_v2_cards_status")
            nba_search = st.text_input("Search players",placeholder="Player name",key="nba_v2_cards_search")
            if nba_filter!="All":nba_props=nba_props[nba_props.decision==nba_filter]
            if nba_search.strip():nba_props=nba_props[nba_props.player_name.str.contains(nba_search.strip(),case=False,regex=False,na=False)]
            nba_props["abs_edge"]=pd.to_numeric(nba_props.edge,errors="coerce").abs()
            nba_props=nba_props.sort_values(["abs_edge","v2_projection"],ascending=[False,False],na_position="last")
            nba_count=nba_props.decision.value_counts()
            a,b,c,d=st.columns(4)
            a.metric("OVER",int(nba_count.get("OVER",0)))
            b.metric("UNDER",int(nba_count.get("UNDER",0)))
            c.metric("PASS",int(nba_count.get("PASS",0)))
            d.metric("WAITING FOR LINES",int(nba_count.get("WAIT",0)))
            st.markdown("""
            <style>
            .nba-v2-responsive-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;width:100%;min-width:0}\n            .nba-v2-responsive-grid .nba-v2-card{min-width:0;max-width:100%;box-sizing:border-box;margin:0;overflow:hidden}\n            .nba-v2-responsive-grid .nba-v2-top>div:last-child{min-width:0;overflow-wrap:anywhere}\n            .nba-v2-responsive-grid .nba-v2-stats>div{min-width:0}\n            @media(max-width:850px){.nba-v2-responsive-grid{grid-template-columns:minmax(0,1fr)}.nba-v2-responsive-grid .nba-v2-card{padding:14px}.nba-v2-responsive-grid .nba-v2-name{font-size:17px}.nba-v2-responsive-grid .nba-v2-num{font-size:22px}.nba-v2-responsive-grid .nba-v2-portrait{width:76px;height:76px;flex-basis:76px}.nba-v2-responsive-grid .nba-v2-head{width:76px;height:76px}.nba-v2-responsive-grid .nba-v2-logo{width:30px;height:30px}.nba-v2-responsive-grid .nba-v2-stats{gap:6px}}\n            .nba-v2-card{background:linear-gradient(135deg,#171e2d,#10141e);border:1px solid #334057;border-radius:17px;padding:19px;margin:10px 0 18px;color:#edf3ff;min-height:238px}
            .nba-v2-top{display:flex;align-items:center;gap:12px}
            .nba-v2-head{height:94px;width:94px;object-fit:contain;object-position:center bottom;display:block}
            .nba-v2-portrait{height:96px;width:96px;flex:0 0 96px;overflow:hidden;border-radius:14px;background:#19253b url("https://raw.githubusercontent.com/easymoneyschulz/sports-betting-command-center/main/assets/emp_player_shield.svg") center / 82px 82px no-repeat;border:1px solid #33445d}
            .nba-v2-portrait object{height:94px;width:94px;display:block}
            .nba-v2-logo{height:38px;width:38px;object-fit:contain}
            .nba-v2-name{font-size:19px;font-weight:850;color:white}
            .nba-v2-match{color:#a8b6ca;font-size:12px}
            .nba-v2-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:16px;border-top:1px solid #303b50;padding-top:15px}
            .nba-v2-label{font-size:10px;color:#9daec7;letter-spacing:1px;text-transform:uppercase}
            .nba-v2-num{font-size:24px;font-weight:900;color:#fff}
            .nba-v2-foot{margin-top:14px;font-size:12px;color:#b5c5dc}
            .nba-v2-tag{display:inline-block;padding:4px 9px;border-radius:30px;font-size:11px;font-weight:900;background:#263247;color:#e9f0ff}
            </style>
            """,unsafe_allow_html=True)
            # Limit expensive player cards and remote images to one page.
            nba_page_size=16
            nba_total=len(nba_props)
            nba_page_count=max(1,(nba_total+nba_page_size-1)//nba_page_size)
            nba_page=st.number_input("PLAYER PAGE",min_value=1,max_value=nba_page_count,value=1,step=1,key="nba_v2_card_page") if nba_page_count>1 else 1
            st.caption(f"Showing {min(nba_total,(nba_page-1)*nba_page_size+1) if nba_total else 0}–{min(nba_total,nba_page*nba_page_size)} of {nba_total} players")
            if nba_props.empty:st.info("No players match these filters.")
            else:
                nba_rows=nba_props.iloc[(nba_page-1)*nba_page_size:nba_page*nba_page_size].to_dict("records")
                nba_card_markup = []
                for entry in nba_rows:
                name=nba_card_html.escape(str(entry["player_name"]))
                team=nba_card_html.escape(str(entry["team"]))
                opponent=nba_card_html.escape(str(entry["opponent"]))
                status=str(entry["decision"])
                color={"OVER":"#60e3ac","UNDER":"#ffb76c","PASS":"#b6c4da","WAIT":"#a6b0c1"}.get(status,"#a6b0c1")
                line=pd.to_numeric(entry["market_line"],errors="coerce")
                edge=pd.to_numeric(entry["edge"],errors="coerce")
                line_text=f"{line:.1f}" if pd.notna(line) else "—"
                edge_text=f"{edge:+.1f}" if pd.notna(edge) else "—"
                book=nba_card_html.escape(str(entry.get("sportsbook") or "Awaiting verified sportsbook"))
                participation=nba_card_html.escape(str(entry.get("lineup_status") or "UNCONFIRMED"))
                pid=str(entry["player_id"])
                pid=pid if pid.isdigit() else "0"
                logo=nba_team_logos.get(str(entry["team"]),"nba")

                    nba_card_markup.append(f"""<div class="nba-v2-card">
                            <div class="nba-v2-top"><div class="nba-v2-portrait"><img class="nba-v2-head" loading="lazy" decoding="async" src="https://cdn.nba.com/headshots/nba/latest/1040x760/{pid}.png" alt="{name} player headshot"></div>
                            <img class="nba-v2-logo" src="https://a.espncdn.com/i/teamlogos/nba/500/{logo}.png">
                            <div><div class="nba-v2-name">{name}</div><div class="nba-v2-match">{team} vs {opponent}</div><span class="nba-v2-tag" style="color:{color}">{status}</span></div></div>
                            <div class="nba-v2-stats"><div><div class="nba-v2-label">V2 projection</div><div class="nba-v2-num">{float(entry["v2_projection"]):.1f}</div></div>
                            <div><div class="nba-v2-label">Book line</div><div class="nba-v2-num">{line_text}</div></div>
                            <div><div class="nba-v2-label">Edge</div><div class="nba-v2-num" style="color:{color}">{edge_text}</div></div></div>
                            <div class="nba-v2-foot">{book} · {participation.replace("_"," ")} · Paper testing only</div></div>""")
                st.markdown('<div class="nba-v2-responsive-grid">' + "".join(nba_card_markup) + '</div>', unsafe_allow_html=True)
            st.caption("OVER/UNDER requires a verified same-game sportsbook line and at least a 3-point edge. WAIT means no matched line; PASS means edge below threshold. Odds and injury status should be checked before wagering.")
    except (requests.RequestException,ValueError,KeyError,pd.errors.ParserError) as nba_error:
        st.info("NBA V2 comparison cards are awaiting the next automated publish.")
        st.caption(str(nba_error))

elif page == "📊 Model Performance":
    import html as perf_html
    import io as perf_io

    st.markdown("""
    <style>
    .perf-hero{padding:27px 29px;border:1px solid #354052;border-radius:19px;background:linear-gradient(115deg,#161e2d,#202b3b 65%,#102b2b);margin:12px 0 22px}
    .perf-eyebrow{font-size:11px;font-weight:850;letter-spacing:2.2px;color:#8ed8c7}
    .perf-title{font-size:clamp(27px,4vw,39px);font-weight:900;color:#fff;letter-spacing:-1px;margin:8px 0}
    .perf-sub{color:#aab9cd;font-size:13px;line-height:1.6}
    .perf-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:13px;margin:17px 0 24px}
    .perf-stat{background:linear-gradient(145deg,#1b2433,#141a25);border:1px solid #344155;border-radius:15px;padding:19px}
    .perf-stat-label{color:#94a7bf;font-size:11px;letter-spacing:1.1px;font-weight:800}
    .perf-stat-value{color:#f8fafc;font-size:29px;font-weight:900;margin:9px 0 4px}
    .perf-stat-note{color:#8295ad;font-size:11px}
    .perf-section{color:#f4f7fb;font-size:21px;font-weight:850;margin:24px 0 10px}
    .perf-row{display:flex;align-items:center;gap:14px;background:#192231;border:1px solid #334155;border-radius:13px;padding:16px 19px;margin:10px 0}
    .perf-model{flex:1;min-width:0}.perf-model-name{font-size:17px;font-weight:850;color:#f4f7fb}
    .perf-model-note{color:#97aac2;font-size:12px;margin-top:5px}
    .perf-record{font-size:20px;font-weight:900;color:#f3f6fa;text-align:right}
    .perf-record-label{color:#96a8bd;font-size:10px;text-align:right;letter-spacing:.8px}
    .perf-status{font-size:10px;font-weight:850;color:#83e3c4;letter-spacing:1px}
    @media(max-width:620px){.perf-hero{padding:19px}.perf-stat{padding:14px}.perf-stat-value{font-size:23px}.perf-row{padding:13px}}
    </style>
    <div class="perf-hero">
      <div class="perf-eyebrow">EASY MONEY SCHULZ · ANALYTICS</div>
      <div class="perf-title">Model Performance</div>
      <div class="perf-sub">Historical backtests and forward paper-test results, separated so research results are never mistaken for verified bets.</div>
    </div>
    """, unsafe_allow_html=True)

    @st.cache_data(ttl=120, show_spinner=False)
    def perf_read_public(name):
        url = "https://raw.githubusercontent.com/easymoneyschulz/sports-betting-command-center/main/public_data/" + name
        try:
            response = requests.get(url, timeout=3)
            response.raise_for_status()
            return pd.read_csv(perf_io.StringIO(response.text))
        except (requests.RequestException, ValueError, pd.errors.ParserError):
            return pd.DataFrame()

    perf_data = perf_read_public("public_predictions.csv")
    if perf_data.empty:
        perf_data = df.copy()
    hist = perf_data[perf_data["test_type"] == "HISTORICAL_BACKTEST"].copy()
    nfl = hist[hist["model"] == "NFL V6.1"].copy()
    n_w = int((nfl["result"] == "WIN").sum())
    n_l = int((nfl["result"] == "LOSS").sum())
    n_p = int((nfl["result"] == "PUSH").sum())
    n_rate = 100 * n_w / (n_w + n_l) if n_w + n_l else 0
    stat_items = [
        ("NFL HISTORICAL RECORD", f"{n_w}-{n_l}-{n_p}", "Wins · losses · pushes"),
        ("NFL HISTORICAL HIT RATE", f"{n_rate:.1f}%", "Pushes excluded"),
        ("NFL GAMES TESTED", f"{len(nfl):,}", "Frozen backtest rows"),
    ]
    stat_html = "".join(
        '<div class="perf-stat"><div class="perf-stat-label">' + perf_html.escape(label) +
        '</div><div class="perf-stat-value">' + perf_html.escape(value) +
        '</div><div class="perf-stat-note">' + perf_html.escape(note) + '</div></div>'
        for label, value, note in stat_items
    )
    st.markdown('<div class="perf-grid">' + stat_html + '</div>', unsafe_allow_html=True)

    st.markdown('<div class="perf-section">Forward Research Tracker</div>', unsafe_allow_html=True)
    cfb_board = perf_read_public("cfb_v4_top5.csv")
    cfb_graded = perf_read_public("cfb_v4_graded.csv")
    nba_board = perf_read_public("nba_v2_daily_top5.csv")
    for model_name, board, graded, label in [
        ("CFB V4", cfb_board, cfb_graded, "Weekly spread rankings"),
        ("NBA V2", nba_board, pd.DataFrame(), "Daily player points"),
        ("NFL V6.1", pd.DataFrame(), pd.DataFrame(), "Weekly NFL research"),
    ]:
        if not graded.empty and "result" in graded.columns:
            results = graded["result"].astype(str).str.upper()
            w = int((results == "WIN").sum())
            l = int((results == "LOSS").sum())
            p = int((results == "PUSH").sum())
            record = f"{w}-{l}-{p}"
            record_label = "GRADED PAPER RESULTS"
        elif not board.empty:
            record = str(len(board))
            record_label = "FEATURED PROJECTIONS"
        else:
            record = "—"
            record_label = "AWAITING RESULTS"
        st.markdown(
            '<div class="perf-row"><div class="perf-model"><div class="perf-model-name">' +
            perf_html.escape(model_name) + '</div><div class="perf-model-note">' +
            perf_html.escape(label) + '</div></div><div><div class="perf-record">' +
            perf_html.escape(record) + '</div><div class="perf-record-label">' +
            perf_html.escape(record_label) + '</div></div></div>',
            unsafe_allow_html=True
        )
    if not cfb_graded.empty:
        with st.expander("CFB V4 — Graded game details"):
            st.dataframe(cfb_graded, hide_index=True, use_container_width=True)
    st.caption("This page reads published GitHub data with a 2-minute cache. Automatic refresh of displayed results is not the same as automatic model reruns or grading. Historical, paper, and real-money results remain separate.")

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
            # NBA model wager ledger is separate from existing NFL weekly history.
            nba_bets_path = UnitsPath(__file__).resolve().parent / "public_data" / "nba_model_wagers.csv"
            nba_bets = units_pd.read_csv(nba_bets_path) if nba_bets_path.exists() else units_pd.DataFrame()
            if not nba_bets.empty:
                nba_bets["date"] = units_pd.to_datetime(nba_bets["date"], errors="coerce")
                nba_bets["net_units"] = units_pd.to_numeric(nba_bets["net_units"], errors="coerce").fillna(0)
                nba_bets["net_profit_usd"] = units_pd.to_numeric(nba_bets["net_profit_usd"], errors="coerce").fillna(0)
                nba_bets = nba_bets[nba_bets["status"].isin(["won", "lost"])].copy()
            net = float(weekly["net_units"].sum()) + (float(nba_bets["net_units"].sum()) if not nba_bets.empty else 0)
            wins = int(weekly["wins"].fillna(0).sum()) + (int((nba_bets["status"] == "won").sum()) if not nba_bets.empty else 0)
            losses = int(weekly["losses"].fillna(0).sum()) + (int((nba_bets["status"] == "lost").sum()) if not nba_bets.empty else 0)
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

            # Include NBA model wagers in the existing weekly growth chart.
            daily_changes = {}
            if not nba_bets.empty:
                for _, nba_bet in nba_bets.iterrows():
                    if units_pd.notna(nba_bet["date"]):
                        bet_day = nba_bet["date"].date()
                        daily_changes[bet_day] = daily_changes.get(bet_day, 0.0) + float(nba_bet["net_units"])
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
                daily_changes[date(2026, 11, 2)] = daily_changes.get(date(2026, 11, 2), 0.0) + 2.0

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
            # Match the Chicago Bears card design for every NBA wager.
            # Keep the individual picks visible inside each card.
            def ems_nba_wager_card(bet):
                from html import escape as ems_escape
                is_win = bet["status"] == "won"
                title = ems_escape(str(bet["description"]))
                when = bet["date"].strftime("%b %d, %Y")
                legs = str(bet["legs"]).split("; ")
                picks_html = "".join(
                    '<div class="ems-u-meta">' + ems_escape(leg) + '</div>'
                    for leg in legs
                )
                outcome = "✓ WIN" if is_win else "✕ LOSS"
                result_color = "#49d394" if is_win else "#ff4555"
                border_color = "#ff4555" if is_win else "#a33440"
                units = float(bet["net_units"])
                stake = float(bet["stake_usd"])
                st.markdown(
                    f'<div class="ems-u-win" style="border-left-color:{border_color};margin-bottom:12px">'
                    '<div class="ems-u-logo" style="display:flex;align-items:center;justify-content:center;'
                    'font-size:39px" aria-label="Basketball">🏀</div>'
                    '<div class="ems-u-team">'
                    f'<div class="ems-u-team-name">{title}</div>'
                    f'<div class="ems-u-meta">{when} · NBA V2 · Model wager</div>'
                    f'{picks_html}'
                    '</div>'
                    '<div class="ems-u-result">'
                    f'<div class="ems-u-result-spread">${stake:.0f}</div>'
                    f'<div class="ems-u-result-win" style="color:{result_color}">{outcome}</div>'
                    f'<div class="ems-u-result-units" style="color:{result_color}">{units:+.2f}u</div>'
                    '</div></div>',
                    unsafe_allow_html=True
                )

            if not nba_bets.empty:
                winning_nba = nba_bets[nba_bets["status"] == "won"]
                for _, nba_bet in winning_nba.sort_values("date", ascending=False).iterrows():
                    ems_nba_wager_card(nba_bet)

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
                if nba_bets.empty or not (nba_bets["status"] == "won").any():
                    st.caption("No individual winning wagers listed yet.")

            if not nba_bets.empty:
                losing_nba = nba_bets[nba_bets["status"] == "lost"]
                if not losing_nba.empty:
                    st.markdown('<div class="ems-u-section">WEEKLY LOSSES</div>', unsafe_allow_html=True)
                    for _, nba_bet in losing_nba.sort_values("date", ascending=False).iterrows():
                        ems_nba_wager_card(nba_bet)

    st.caption(
        "Personal wager results are separate from official "
        "model forward tests. No monetary amounts are displayed."
    )

elif page == "🔴 Live Scores":

    from datetime import datetime

    st.subheader("LIVE SPORTS SCOREBOARD")
    st.caption("NFL · COLLEGE FOOTBALL · NBA")

    # Automatic browser refresh disabled: the live scores page remains
    # manually refreshable without mounting an additional frontend component.
    # This preserves the original dashboard layout and betting data.

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



elif page == "👤 My Account":
    st.title("My Account")
    st.caption("EasyMoneySchulz · Personal Betting Command Center")
    st.markdown("### Browse freely. Track privately.")
    st.info("Guest mode is available without signing in. Email accounts and permanent private bet storage require the secure account database to be connected.")
    guest_tab, account_tab = st.tabs(["Continue as Guest", "Create Account / Sign In"])
    with guest_tab:
        st.markdown("**Public access stays free.** Browse NFL, college football, NBA points projections, and live scores using the navigation above.")
        st.markdown("#### What an account will unlock")
        st.markdown("My Bets · Saved history · Personal bankroll · Profit / loss · ROI · Power Model Review")
    with account_tab:
        st.markdown("### Email account access")
        st.write("Email registration and sign-in will be enabled after secure authentication and per-user database permissions are configured. We won't collect passwords or claim bets are saved until that is ready.")
        st.caption("Planned account features: add your own NFL/CFB/NBA points picks or follow a published model selection; track each separately.")
    st.divider()
    st.subheader("Power Model Review")
    st.caption("Your private performance summary will appear here once you're signed in and have recorded bets.")
    a, b, c, d = st.columns(4)
    a.metric("Net Profit / Loss", "—")
    b.metric("Win Rate", "—")
    c.metric("ROI", "—")
    d.metric("Total Bets", "—")
    st.markdown("**Performance by category:** NFL · College Football · NBA Player Points")
    st.markdown("**Performance by source:** My Own Picks · EasyMoneySchulz Model Picks")
    st.caption("No sample or invented results are counted as real user performance.")

st.divider()
st.caption(
    "Research and paper testing only. "
    "Historical backtests do not guarantee future results."
)
