"""
Schedule page: shows all 2026 fixtures grouped by round.
Clicking a match navigates to match analysis with teams pre-filled.
"""

import json
from pathlib import Path

import streamlit as st
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from api.football_api import get_fixtures
from config import VEIKKAUSLIIGA_ID, SEASON_2026


_MANUAL_RESULTS_PATH = Path(__file__).parent.parent.parent / "data" / "manual_results.json"


def _load_manual_results() -> dict:
    if _MANUAL_RESULTS_PATH.exists():
        with open(_MANUAL_RESULTS_PATH, encoding="utf-8") as f:
            return {int(k): v for k, v in json.load(f).items()}
    return {}


@st.cache_data(ttl=3600, show_spinner=False)
def _load_fixtures(force_refresh: bool = False):
    fixtures = get_fixtures(VEIKKAUSLIIGA_ID, SEASON_2026, force_refresh=force_refresh)
    manual = _load_manual_results()
    rounds = {}
    for f in fixtures:
        fixture_id = f["fixture"]["id"]
        status = f["fixture"]["status"]["short"]
        round_name = f["league"]["round"]
        date = f["fixture"]["date"][:10]
        home = f["teams"]["home"]["name"]
        away = f["teams"]["away"]["name"]
        home_id = f["teams"]["home"]["id"]
        away_id = f["teams"]["away"]["id"]
        goals_home = f["goals"]["home"]
        goals_away = f["goals"]["away"]

        if goals_home is None and fixture_id in manual:
            goals_home = manual[fixture_id]["home_goals"]
            goals_away = manual[fixture_id]["away_goals"]

        if round_name not in rounds:
            rounds[round_name] = []
        rounds[round_name].append({
            "fixture_id": fixture_id,
            "date": date,
            "home": home,
            "away": away,
            "home_id": home_id,
            "away_id": away_id,
            "status": status,
            "goals_home": goals_home,
            "goals_away": goals_away,
        })
    return rounds


def _round_number(round_name: str) -> int:
    try:
        return int(round_name.split("-")[-1].strip())
    except ValueError:
        return 999


def render():
    st.title("Otteluohjelma 2026")

    with st.spinner("Ladataan otteluohjelma..."):
        rounds = _load_fixtures()

    sorted_rounds = sorted(rounds.keys(), key=_round_number)

    # Filter controls
    col1, col2 = st.columns([2, 1])
    with col1:
        show_played = st.toggle("Näytä pelatut ottelut", value=True)
    with col2:
        jump_to = st.selectbox("Hyppää kierrokselle", ["—"] + sorted_rounds, label_visibility="collapsed")

    # Active round = first round with unplayed matches; fallback to last round
    _active_round = next(
        (r for r in sorted_rounds if any(m["goals_home"] is None for m in rounds[r])),
        sorted_rounds[-1] if sorted_rounds else None,
    )

    if jump_to != "—":
        sorted_rounds = [r for r in sorted_rounds if r == jump_to] + \
                        [r for r in sorted_rounds if r != jump_to]

    for round_name in sorted_rounds:
        matches = rounds[round_name]
        has_unplayed = any(m["goals_home"] is None for m in matches)

        if not show_played and not has_unplayed:
            continue

        dates = sorted(set(m["date"] for m in matches))
        date_str = dates[0] if len(dates) == 1 else f"{dates[0]} – {dates[-1]}"
        round_num = _round_number(round_name)

        with st.expander(f"**Kierros {round_num}** — {date_str}", expanded=(round_name == _active_round)):
            for m in sorted(matches, key=lambda x: x["date"]):
                if not show_played and m["goals_home"] is not None:
                    continue

                col_date, col_match, col_analysoi = st.columns([1.2, 3, 1])

                with col_date:
                    st.caption(m["date"])

                with col_match:
                    if m["goals_home"] is not None and m["goals_away"] is not None:
                        score = f"{m['goals_home']}–{m['goals_away']}"
                        st.write(f"{m['home']} **{score}** {m['away']}")
                    else:
                        st.write(f"**{m['home']}** vs **{m['away']}**")

                with col_analysoi:
                    if st.button("Analysoi →", key=f"match_{m['home']}_{m['away']}_{m['date']}"):
                        st.session_state["match_home"] = m["home"]
                        st.session_state["match_away"] = m["away"]
                        st.session_state["page"] = "Matsianalyysi"
                        st.rerun()
