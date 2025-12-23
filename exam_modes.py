"""
Module 4 — Exam Modes

Responsibilities:
- Rapid Review Mode
- Image Sprint Mode (one item at a time)

Read-only. No content creation.
"""

import streamlit as st
import time
from datetime import date

import data_layer

# =========================
# SESSION STATE
# =========================

def init_exam_state():
    st.session_state.setdefault("sprint_index", 0)
    st.session_state.setdefault("last_sprint_subject", None)


# =========================
# RAPID REVIEW MODE
# =========================

def render_rapid_review():
    st.subheader("⚡ Rapid Review")

    init_exam_state()

    pyqs = data_layer.load_pyqs()
    cards = data_layer.load_cards()

    if pyqs.empty:
        st.info("No PYQs available.")
        return

    subjects = ["All"] + sorted(pyqs.subject.unique().tolist())
    subject = st.selectbox("Subject", subjects)

    if subject != "All":
        pyqs = pyqs[pyqs.subject == subject]

    candidates = pyqs[
        (
            (pyqs.get("revision_count", 0) == 0)
            | (pyqs.get("fail_count", 0) > 0)
            | (data_layer.is_due(pyqs))
        )
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

    content_shown = False

    # =========================
    # STUDY CARD CONTENT
    # =========================
    card_df = cards[cards.topic_id == row.id]

    if not card_df.empty:
        card = card_df.iloc[0]

        if isinstance(card.bullets, str) and card.bullets.strip():
            for line in card.bullets.splitlines():
                st.write(line)
            content_shown = True

        if isinstance(card.image_paths, str) and card.image_paths.strip():
            st.markdown("#### 🖼️ Study Card Images")
            for p in card.image_paths.split(";"):
                st.image(p)
            content_shown = True

    # =========================
    # PYQ IMAGES (fallback)
    # =========================
    # =========================
    # PYQ IMAGE DISPLAY (FIXED)
    # =========================
    if "pyq_image_paths" in pyqs.columns:
        pyq_images = pyqs.loc[pyqs.id == row.id,   "pyq_image_paths"].values

        if (
            len(pyq_images) > 0
            and isinstance(pyq_images[0], str)
            and pyq_images[0].strip()
        ):
            st.markdown("#### 🖼️ PYQ Image")
            for p in pyq_images[0].split(";"):
                st.image(p)
            content_shown = True

    # =========================
    # TRIGGER LINE (last fallback)
    # =========================
    if not content_shown and isinstance(row.trigger_line, str) and row.trigger_line.strip():
        st.info("No study card yet for this topic.")
        st.markdown(f"**Trigger line:** {row.trigger_line}")
        content_shown = True

    if not content_shown:
        st.warning("No content available for this topic yet.")

    # =========================
    # ACTIONS
    # =========================

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Revised"):
            pyqs.loc[pyqs.id == row.id, "revision_count"] += 1
            pyqs.loc[pyqs.id == row.id, "fail_count"] = (
                pyqs.loc[pyqs.id == row.id, "fail_count"].clip(lower=0)
            )
            pyqs.loc[pyqs.id == row.id, "last_revised"] = date.today()
            data_layer.save_pyqs(pyqs)
            st.rerun()

    with col2:
        if st.button("❌ Weak"):
            pyqs.loc[pyqs.id == row.id, "fail_count"] += 1
            pyqs.loc[pyqs.id == row.id, "last_revised"] = date.today()
            data_layer.save_pyqs(pyqs)
            st.rerun()


# =========================
# IMAGE SPRINT MODE
# =========================

def render_image_sprint():
    st.subheader("🖼️ Image Sprint")

    init_exam_state()

    pyqs = data_layer.load_pyqs()
    cards = data_layer.load_cards()

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

    auto = st.toggle("Auto-advance", value=False)

    if st.session_state.last_sprint_subject != subject:
        st.session_state.sprint_index = 0
        st.session_state.last_sprint_subject = subject

    if st.session_state.sprint_index >= len(cards):
        st.success("Sprint completed 🎉")
        return

    card = cards.iloc[st.session_state.sprint_index]
    topic = pyqs[pyqs.id == card.topic_id].topic.values[0]

    st.markdown(f"### {topic}")

    if isinstance(card.image_paths, str) and card.image_paths.strip():
        for p in card.image_paths.split(";"):
            st.image(p)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Next ▶️"):
            st.session_state.sprint_index += 1
            st.rerun()

    with col2:
        if auto:
            time.sleep(delay)
            st.session_state.sprint_index += 1
            st.rerun()


# =========================
# MAIN ENTRY
# =========================

def render_exam_modes():
    if st.session_state.app_mode != "Exam":
        st.info("Switch to ⚡ Exam Mode to access exam features.")
        return

    view = st.session_state.get("current_view")

    if view == "image_sprint":
        render_image_sprint()
    elif view == "rapid_review":
        render_rapid_review()
    else:
        st.info("Select an exam tool to begin.")