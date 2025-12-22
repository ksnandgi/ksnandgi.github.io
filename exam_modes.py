"""
Module 4 — Exam Modes

Responsibilities:
- Rapid Review Mode
- Image Sprint Mode (auto-advance)
- Last-seen visual cue
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

    # Only topics WITH cards
    pyqs = pyqs[pyqs.id.isin(cards.topic_id)]

    if pyqs.empty:
        st.info("No consolidated topics available.")
        return

    subjects = ["All"] + sorted(pyqs.subject.unique().tolist())
    subject = st.selectbox("Subject", subjects)

    if subject != "All":
        pyqs = pyqs[pyqs.subject == subject]

    # =========================
    # 🔑 FIX: EXAM CANDIDATES
    # =========================
    candidates = pyqs[
        (pyqs.revision_count == 0) |     # never revised
        (pyqs.fail_count > 0) |           # weak
        (is_due(pyqs))                    # due
    ]

    if candidates.empty:
        st.info("No topics available for rapid review.")
        return

    candidates = candidates.sort_values(
        by=["fail_count", "revision_count"],
        ascending=[False, True]
    )

    row = candidates.iloc[0]
    card = cards[cards.topic_id == row.id].iloc[0]

    st.markdown(f"### {row.topic}")
    st.caption(row.subject)

    if card.image_paths:
        for p in card.image_paths.split(";"):
            st.image(p)

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

            st.success("Marked revised.")
            st.rerun()

    with col2:
        if st.button("❌ Weak"):
            row.fail_count += 1
            row.last_revised = date.today()
            row.next_revision_date = compute_next_revision(row)

            pyqs.loc[pyqs.id == row.id, :] = row
            save_pyqs(pyqs)

            st.warning("Marked weak.")
            st.rerun()


# =========================
# IMAGE SPRINT MODE
# =========================

def render_image_sprint():
    st.subheader("🖼️ Image Sprint")

    init_exam_state()

    cards = load_cards()
    pyqs = load_pyqs()

    subjects = sorted(pyqs.subject.unique().tolist())
    subject = st.selectbox("Subject (mandatory)", subjects)

    topic_ids = pyqs[pyqs.subject == subject].id
    cards = cards[cards.topic_id.isin(topic_ids)]

    if cards.empty:
        st.info("No image cards for this subject.")
        return

    speed = st.selectbox("Sprint speed", ["Slow", "Normal", "Fast"])
    delay = {"Slow": 4, "