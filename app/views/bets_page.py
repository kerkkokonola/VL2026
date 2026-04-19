"""
Bets view: table of placed bets with rationale and closing line tracking.
Read-only — edits via Claude or source.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
from data.bets import load_bets


def render():
    st.title("Vedot")

    bets = load_bets()

    # --- Summary stats ---
    open_bets = [b for b in bets if b["result"] is None]
    settled = [b for b in bets if b["profit_units"] is not None]
    total_pl = sum(b["profit_units"] for b in settled)
    total_staked = sum(b["stake_units"] for b in settled)
    roi = (total_pl / total_staked * 100) if total_staked else 0.0

    clv_vals = [b["clv_percent"] for b in settled if b.get("clv_percent") is not None]
    avg_clv = sum(clv_vals) / len(clv_vals) if clv_vals else None

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Avoimet vedot", len(open_bets))
    c2.metric("Selvitetty", len(settled))
    c3.metric("P/L (u)", f"{total_pl:+.2f}" if settled else "—")
    c4.metric("ROI", f"{roi:+.1f} %" if settled else "—")
    c5.metric("CLV ka.", f"{avg_clv:+.2f} %" if avg_clv is not None else "—")

    st.divider()

    # --- Bets table ---
    if not bets:
        st.info("Ei kirjattuja vetoja.")
        return

    rows = []
    for b in bets:
        rows.append({
            "Pvm": b["date_placed"],
            "Ottelu": b["match"],
            "Markkina": b["market"],
            "Sivusto": b["bookmaker"],
            "Kerroin": b["odds"],
            "Malli %": round(b["model_prob"] * 100, 1),
            "EV %": round((b["model_prob"] * b["odds"] - 1) * 100, 1),
            "Panos (u)": b["stake_units"],
            "P.close": b.get("closing_odds"),
            "No-vig %": round(b["closing_no_vig_prob"] * 100, 1) if b.get("closing_no_vig_prob") else None,
            "CLV %": b.get("clv_percent"),
            "Tulos": b["result"] or "—",
            "P/L (u)": b["profit_units"],
        })

    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Kerroin": st.column_config.NumberColumn(format="%.3f"),
            "Malli %": st.column_config.NumberColumn(format="%.1f"),
            "EV %": st.column_config.NumberColumn(format="%+.1f"),
            "P.close": st.column_config.NumberColumn(format="%.3f"),
            "No-vig %": st.column_config.NumberColumn(format="%.1f"),
            "CLV %": st.column_config.NumberColumn(format="%+.1f"),
            "P/L (u)": st.column_config.NumberColumn(format="%+.2f"),
        },
    )

    st.divider()

    # --- Bet detail cards ---
    st.subheader("Vetojen tiedot")
    for b in bets:
        label = f"{b['date_placed']} · {b['match']} · {b['market']} @ {b['odds']}"
        with st.expander(label):
            # Core info
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Kerroin", f"{b['odds']:.3f}")
            c2.metric("Malli", f"{b['model_prob']*100:.1f} %")
            ev = b["model_prob"] * b["odds"] - 1
            c3.metric("EV", f"{ev*100:+.1f} %")
            c4.metric("Panos", f"{b['stake_units']} u")

            if b.get("closing_odds") or b.get("closing_no_vig_prob"):
                st.markdown("**Sulkeutumiset**")
                cc1, cc2, cc3 = st.columns(3)
                if b.get("closing_odds"):
                    cc1.metric("Pinnacle close", f"{b['closing_odds']:.3f}")
                if b.get("closing_no_vig_prob"):
                    cc2.metric("No-vig close", f"{b['closing_no_vig_prob']*100:.1f} %")
                if b.get("clv_percent") is not None:
                    cc3.metric("CLV", f"{b['clv_percent']:+.1f} %")

            if b.get("rationale"):
                st.markdown("**Perustelu**")
                st.markdown(b["rationale"])

            if b.get("notes"):
                st.caption(b["notes"])
