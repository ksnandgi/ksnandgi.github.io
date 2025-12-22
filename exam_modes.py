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

    # ---- Exam candidates ----
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

    # ---- Optional study card ----
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
        st.markdown(f"**Trigger line:** {row.trigger_line}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Revised"):
            # Exam Mode: no spaced repetition update
            pyqs.loc[pyqs.id == row.id, "revision_count"] += 1
            pyqs.loc[pyqs.id == row.id, "fail_count"] = (
                pyqs.loc[pyqs.id == row.id, "fail_count"].clip(lower=0)
            )
            pyqs.loc[pyqs.id == row.id, "last_revised"] = date.today()

            save_pyqs(pyqs)
            st.rerun()

    with col2:
        if st.button("❌ Weak"):
            pyqs.loc[pyqs.id == row.id, "fail_count"] += 1
            pyqs.loc[pyqs.id == row.id, "last_revised"] = date.today()

            save_pyqs(pyqs)
            st.rerun()

# =========================
# IMAGE SPRINT MODE
# =========================

def render_image_sprint():
    st.subheader("🖼️ Image Sprint")

    init_exam_state()

    cards = load_cards()
    pyqs = load_pyqs()

    if cards.empty:
        st.info("No study cards with images available.")
        return

    subjects = sorted(pyqs.subject.unique().tolist())
    subject = st.selectbox("Subject (mandatory)", subjects)

    topic_ids = pyqs[pyqs.subject == subject].id
    cards = cards[cards.topic_id.isin(topic_ids)]

    if cards.empty:
        st.info("No image cards for this subject.")
        return

    speed = st.selectbox("Sprint speed", ["Slow", "Normal", "Fast"])
    delay = {"Slow": 4, "Normal": 2, "Fast": 1}[speed]

    auto = st.toggle("Auto-advance", value=True)

    for _, card in cards.iterrows():
        topic = pyqs[pyqs.id == card.topic_id].topic.values[0]
        st.markdown(f"### {topic}")

        if card.image_paths:
            for p in card.image_paths.split(";"):
                st.image(p)

        if auto:
            time.sleep(delay)

    today = date.today()
    if st.session_state.last_sprint_date != today:
        st.session_state.sprint_count_today = 0
        st.session_state.last_sprint_date = today

    st.session_state.sprint_count_today += 1

    if st.session_state.sprint_count_today >= 2:
        st.info("You’ve completed a full image sprint today.")


# =========================
# EXAM DAY MODE
# =========================

def render_exam_day_toggle():
    st.session_state.exam_day_mode = st.toggle(
        "🧠 Exam Day Mode",
        value=st.session_state.get("exam_day_mode", False)
    )

    if st.session_state.exam_day_mode:
        st.warning("Exam Day Mode is ON. Editing & capture are disabled.")


# =========================
# MAIN ENTRY
# =========================

def render_exam_modes():
    if st.session_state.app_mode != "Exam":
        st.info("Switch to ⚡ Exam Mode to access exam features.")
        return

    render_exam_day_toggle()

    mode = st.radio(
        "Select Exam Mode",
        ["Rapid Review", "Image Sprint"],
        horizontal=True
    )

    if mode == "Rapid Review":
        render_rapid_review()
    else:
        render_image_sprint()