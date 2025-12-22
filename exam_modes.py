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

from data_layer import load_pyqs, load_cards, is_due

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

    pyqs = pyqs[is_due(pyqs)]

    if pyqs.empty:
        st.success("No topics due.")
        return

    pyqs = pyqs.sort_values(
        by=["fail_count", "revision_count"],
        ascending=[False, False]
    )

    row = pyqs.iloc[0]
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
            st.success("Marked revised.")
            st.rerun()

    with col2:
        if st.button("❌ Weak"):
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
    delay = {"Slow": 4, "Normal": 2, "Fast": 1}[speed]

    auto = st.toggle("Auto-advance", value=True)

    for _, card in cards.iterrows():
        st.markdown(f"### {pyqs[pyqs.id == card.topic_id].topic.values[0]}")

        if card.image_paths:
            for p in card.image_paths.split(";"):
                border = "🟢" if p in st.session_state.image_seen else "⚪"
                st.markdown(f"{border}")
                st.image(p)
                st.session_state.image_seen.add(p)

        time.sleep(delay if auto else 0)

    # ---- Soft daily cap ----
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
        value=st.session_state.exam_day_mode
    )

    if st.session_state.exam_day_mode:
        st.warning("Exam Day Mode is ON. Editing & capture are disabled.")


# =========================
# MAIN ENTRY
# =========================


def render_exam_modes():
    if st.session_state.app_mode != "Exam":
    st.info("Switch to ⚡ Exam Mode to access Rapid Review and Image Sprint.")
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

def require_mode(allowed_modes, message):
    if st.session_state.app_mode not in allowed_modes:
        st.info(message)
        return False
    return True
