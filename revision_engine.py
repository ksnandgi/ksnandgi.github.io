"""
Module 3 — Revision Engine

Responsibilities:
- Subject-wise revision (always available)
- Weak-first prioritization
- Spaced repetition handling
- Revised / Weak actions
- Image-only revision mode
- Implicit uncertainty detection (time-based)
- Session-level suppression
- Today’s target indicator
- Subject interleaving
- Quiet revision streak
"""

import streamlit as st
import pandas as pd
import time
from datetime import date

import data_layer

# =========================
# SESSION STATE INIT
# =========================

def init_revision_session():
    st.session_state.setdefault("session_seen", set())
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
    cards = load_cards()

    # Only topics with study cards
    pyqs = pyqs[pyqs.id.isin(cards.topic_id)]

    if pyqs.empty:
        st.info("No topics available for revision yet.")
        return

    subjects = ["All"] + sorted(pyqs.subject.unique().tolist())
    subject = st.selectbox("Subject", subjects)

    if subject != "All":
        pyqs = pyqs[pyqs.subject == subject]

    # =========================
    # 🔑 FIX: REVISION CANDIDATES
    # =========================
    candidates = pyqs[
        (pyqs.revision_count == 0) |     # never revised
        (pyqs.fail_count > 0) |           # weak topics
        (is_due(pyqs))                    # due by schedule
    ]

    if candidates.empty:
        st.info("No topics available for revision yet.")
        return

    candidates = prioritize(candidates)

    # Session-level suppression
    candidates = candidates[
        ~candidates.id.isin(st.session_state.session_seen)
    ]

    if candidates.empty:
        st.info("You have revised all available topics in this session.")
        return

    row = candidates.iloc[0]
    card = cards[cards.topic_id == row.id].iloc[0]

    st.markdown(f"### {row.topic}")
    st.caption(row.subject)

    # ---- Image-only mode ----
    image_only = st.toggle("Image-only revision", value=False)

    if card.image_paths:
        for p in card.image_paths.split(";"):
            st.image(p)

    if not image_only:
        for line in card.bullets.splitlines():
            st.write(line)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Revised"):
            row.revision_count += 1
            row.fail_count = max(row.fail_count - 1, 0)
            row.last_revised = date.today()
            row.next_revision_date = compute_next_revision(row)

            pyqs.loc[pyqs.id == row.id, :] = row
            save_pyqs(pyqs)

            st.session_state.session_seen.add(row.id)
            st.session_state.revised_today += 1
            st.rerun()

    with col2:
        if st.button("❌ Weak"):
            row.fail_count += 1
            row.last_revised = date.today()
            row.next_revision_date = compute_next_revision(row)

            pyqs.loc[pyqs.id == row.id, :] = row
            save_pyqs(pyqs)

            st.session_state.session_seen.add(row.id)
            st.rerun()

    # ---- Quiet streak ----
    today = date.today()
    if st.session_state.last_revision_date != today:
        st.session_state.revision_streak += 1
        st.session_state.last_revision_date = today

    st.caption(f"Revision streak: {st.session_state.revision_streak} days")
