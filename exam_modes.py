"""
Module 4 — Exam Modes

Responsibilities:
- Rapid Review Mode
- Image Sprint Mode (auto-advance)
- Exam-phase guardrails
- Exam Day Mode
- Soft daily cap

Read-only. No content creation.
"""

import streamlit as st
import pandas as pd
import time
from datetime import date

from data_layer import (
    load_pyqs,
    load_cards,
    save_pyqs,
    compute_next_revision,
    is_due
)

# =========================
# SESSION STATE
# =========================

def init_exam_state():
    st.session_state.setdefault("exam_day_mode", False)
    st.session_state.setdefault("image_seen", set())
    st.session_state.setdefault("sprint_count_today", 0)
    st.session_state.setdefault("last_sprint_date", None)


# =========================
# RAPID REVIEW MODE
# =========================

def render_rapid_review():
    st.subheader("⚡ Rapid Review")

    pyqs = load_pyqs()
    cards = load_cards()

    if pyqs.empty:
        st.info("No PYQs available.")
        return

    subjects = ["All"] + sorted(pyqs.subject.unique().tolist())
    subject = st.selectbox("Subject", subjects)

    if subject != "All":
        pyqs = pyqs[pyqs.subject == subject]

    # ---- EXAM CANDIDATES (IMPORTANT FIX) ----
    candidates = pyqs[
        (pyqs.revision_count == 0) |
        (pyqs.fail_count > 0) |
        (is_due(pyqs))
    ]

    if candidates.empty:
        st.info("No topics available for rapid review.")
        return

    candidates = candidates.sort_values(
        by=["fail_count", "revision_count"],
        ascending=[False, True]
    )

    row = candidates.iloc[0]

    st.markdown(f"### {row.topic}")
    st.caption(row.subject)

    # ---- STUDY CARD (OPTIONAL) ----
    card_df = cards[cards.topic_id == row.id]

    if not card_df.empty:
        card = card_df.iloc[0]

        if card.image_paths:
            for p in card.image_paths.split(";"):
                st.image(p)

        for line in card.bullets.splitlines():
            st.write(line)
    else:
        st.info("No study card yet for this topic.")
        st.markdown(f"**Trigger line:** {