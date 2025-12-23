"""
Module 3 — Revision Engine

Responsibilities:
- Subject-wise revision (always available)
- Weak-first prioritization
- Spaced repetition handling
- Revised / Weak actions
- Image-only revision mode
- Today’s target indicator
- Quiet revision streak

(Session suppression intentionally disabled during development)
"""

import streamlit as st
import pandas as pd
from datetime import date
import time

import data_layer

# =========================
# SESSION STATE INIT
# =========================

def init_revision_session():
    st.session_state.setdefault("start_time", time.time())
    st.session_state.setdefault("revised_today", 0)
    st.session_state.setdefault("revision_streak", 0)
    st.session_state.setdefault("last_revision_date", None)


# =========================
# PRIORITIZATION
# =========================

def prioritize(pyqs: pd.DataFrame) -> pd.DataFrame:
    return pyqs.sort_values(
        by=["fail_count", "revision_count"],
        ascending=[False, True]
    )


# =========================
# MAIN UI
# =========================

def render_revision_engine():
    # ---- MODE GUARD ----
    if st.session_state.app_mode != "Study":
        st.info("Switch to 📘 Study Mode to start revision.")
        return

    st.subheader("📚 Revision")

    init_revision_session()

    pyqs = data_layer.load_pyqs()
    cards = data_layer.load_cards()

    # Only topics WITH study cards
    pyqs = pyqs[pyqs.id.isin(cards.topic_id)]

    if pyqs.empty:
        st.info("No topics available for revision yet.")
        return

    # -------------------------
    # SUBJECT FILTER
    # -------------------------
    subjects = ["All"] + sorted(pyqs.subject.unique().tolist())
    subject = st.selectbox("Subject", subjects)

    if subject != "All":
        pyqs = pyqs[pyqs.subject == subject]

    # -------------------------
    # REVISION CANDIDATES
    # -------------------------
    candidates = pyqs[
        (pyqs.revision_count == 0) |
        (pyqs.fail_count > 0) |
        (data_layer.is_due(pyqs))
    ]

    if candidates.empty:
        st.info("No topics available for revision right now.")
        return

    candidates = prioritize(candidates)

    row = candidates.iloc[0]
    card = cards[cards.topic_id == row.id].iloc[0]

    # -------------------------
    # DISPLAY
    # -------------------------
    st.markdown(f"### {row.topic}")
    st.caption(row.subject)

    image_only = st.toggle("Image-only revision", value=False)

    if isinstance(card.image_paths, str) and card.image_paths.strip():
        for p in card.image_paths.split(";"):
            st.image(p)

    if not image_only:
        for line in card.bullets.splitlines():
            st.write(line)

    # -------------------------
    # ACTIONS
    # -------------------------
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Revised"):
            new_revision_count = int(row.revision_count) + 1
            new_fail_count = max(int(row.fail_count) - 1, 0)
            next_date = data_layer.compute_next_revision(new_revision_count)

            pyqs.loc[pyqs.id == row.id, "revision_count"] = new_revision_count
            pyqs.loc[pyqs.id == row.id, "fail_count"] = new_fail_count
            pyqs.loc[pyqs.id == row.id, "last_revised"] = date.today()
            pyqs.loc[pyqs.id == row.id, "next_revision_date"] = next_date

            data_layer.save_pyqs(pyqs)

            st.session_state.revised_today += 1
            st.rerun()

    with col2:
        if st.button("❌ Weak"):
            new_fail_count = int(row.fail_count) + 1
            next_date = data_layer.compute_next_revision(int(row.revision_count))

            pyqs.loc[pyqs.id == row.id, "fail_count"] = new_fail_count
            pyqs.loc[pyqs.id == row.id, "last_revised"] = date.today()
            pyqs.loc[pyqs.id == row.id, "next_revision_date"] = next_date

            data_layer.save_pyqs(pyqs)
            st.rerun()

    # -------------------------
    # QUIET STREAK
    # -------------------------
    today = date.today()
    if st.session_state.last_revision_date != today:
        st.session_state.revision_streak += 1
        st.session_state.last_revision_date = today

    st.caption(f"Revision streak: {st.session_state.revision_streak} days")

    if st.session_state.get("revision_filter") == "weak":
        st.info("Showing weak topics first")