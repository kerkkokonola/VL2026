"""
VL2026 — Veikkausliiga 2026 ennustemalli
Streamlit entry point
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

st.set_page_config(
    page_title="VL2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.views import team_page, match_page, schedule_page, bets_page, analysis_page
from data.overrides import load_raw_overrides

PAGES = {
    "Otteluohjelma": schedule_page,
    "Matsianalyysi": match_page,
    "Joukkueet": team_page,
    "Vedot": bets_page,
    "Analyysi": analysis_page,
}

# Allow schedule page to navigate directly to match analysis
if "raw_overrides" not in st.session_state:
    st.session_state["raw_overrides"] = load_raw_overrides()
if "page" not in st.session_state:
    st.session_state["page"] = "Otteluohjelma"
if "team_detail" not in st.session_state:
    st.session_state["team_detail"] = None

with st.sidebar:
    st.title("⚽ VL2026")
    st.divider()
    st.markdown("""
    <style>
    div[data-testid="stSidebar"] div[data-testid="stRadio"] > label:first-child {
        display: none;
    }
    div[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] {
        gap: 2px;
    }
    div[data-testid="stSidebar"] div[data-testid="stRadio"] label {
        padding: 0.45rem 0.75rem;
        border-radius: 6px;
        width: 100%;
        font-size: 0.95rem;
        cursor: pointer;
    }
    div[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
        background: rgba(255, 255, 255, 0.07);
    }
    div[data-testid="stSidebar"] div[data-testid="stRadio"] label[aria-checked="true"] {
        background: rgba(255, 255, 255, 0.12);
        font-weight: 600;
    }
    div[data-testid="stSidebar"] div[data-testid="stRadio"] label span:first-child {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)
    selected = st.radio("Navigaatio", list(PAGES.keys()),
                        index=list(PAGES.keys()).index(st.session_state["page"]),
                        label_visibility="collapsed")
    if selected != st.session_state["page"]:
        st.session_state["page"] = selected
        st.rerun()

PAGES[st.session_state["page"]].render()
