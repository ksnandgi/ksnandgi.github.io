"""
Module 5 — Dashboard & Guidance

Responsibilities:
- Dashboard as entry point
- Daily auto-generated revision plan
- Weak-area overview
- Minimal progress indicators
- Next Best Action prompt
- "Why this today?" explanation
- Soft subject balance indicator
- Exam-mode readiness nudge

No editing. No pressure metrics. No comparisons.
"""

import streamlit as st
import pandas as pd
import os
import zipfile
from io import BytesIO
import shutil
from datetime import date

from data_layer import load_pyqs, load_cards, is_due

def create_full_backup():
    buffer = BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        # CSV files
        if os.path.exists("pyq_topics.csv"):
            z.write("pyq_topics.csv")
        if os.path.exists("study_cards.csv"):
            z.write("study_cards.csv")

        # Images
        if os.path.exists("card_images"):
            for root, _, files in os.walk("card_images"):
                for f in files:
                    path = os.path.join(root, f)
                    z.write(path)

    buffer.seek(0)
    return buffer

def restore_full_backup(uploaded_zip):
    with zipfile.ZipFile(uploaded_zip) as z:
        z.extractall(".")


def zip_images(folder="card_images"):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        if os.path.exists(folder):
            for root, _, files in os.walk(folder):
                for f in files:
                    path = os.path.join(root, f)
                    z.write(path, arcname=f)
    buffer.seek(0)
    return buffer

# =========================
# DAILY PLAN
# =========================

def generate_daily_plan(pyqs: pd.DataFrame, limit: int = 8) -> pd.DataFrame:
    due = pyqs[is_due(pyqs)]
    weak = pyqs[pyqs.fail_count >= 2]
    strong = pyqs[(pyqs.revision_count >= 3) & (~pyqs.id.isin(weak.id))]

    plan = pd.concat([
        due,
        weak,
        strong.sample(min(len(strong), 2)) if not strong.empty else strong
    ]).drop_duplicates()

    return plan.head(limit)


# =========================
# MAIN DASHBOARD
# =========================


def render_dashboard():
    st.subheader("🏠 Dashboard")

    mode = st.session_state.app_mode

    # =========================
    # 📘 STUDY MODE DASHBOARD
    # =========================
    if mode == "Study":
        st.markdown("## 📘 Today’s Revision")

        pyqs = data.layer.load_pyqs()
        cards = load_cards()

        # Only topics with study cards
        pyqs = pyqs[pyqs.id.isin(cards.topic_id)]

        if pyqs.empty:
            st.info("No topics ready for revision yet.")
            st.markdown("➡️ Add PYQs and Study Cards in Build Mode.")
            return

        # Due or weak topics
        due = pyqs[is_due(pyqs)]
        weak = pyqs[pyqs.fail_count > 0]

        today_list = (
            due if not due.empty else weak
        ).sort_values(
            by=["fail_count", "revision_count"],
            ascending=[False, True]
        ).head(5)

        if today_list.empty:
            st.success("You’re all caught up for today 🎉")
        else:
            for _, row in today_list.iterrows():
                st.markdown(
                    f"- **{row.topic}**  \n"
                    f"<small>{row.subject}</small>",
                    unsafe_allow_html=True
                )

            st.markdown("")

            if st.button("▶️ Start Revision", use_container_width=True):
                st.session_state.current_view = "revision"
                st.rerun()

        # -------------------------
        # Quick Actions
        # -------------------------
        st.markdown("---")
        st.markdown("### Quick Actions")

        col1, col2 = st.columns(2)

        with col1:
            st.button("🖼️ Image Sprint", use_container_width=True)

        with col2:
            st.button("📌 Weak Areas", use_container_width=True)

        # -------------------------
        # Light Progress Overview
        # -------------------------
        st.markdown("---")
        st.markdown("### Progress Overview")

        revised = pyqs.revision_count.sum()
        weak_count = (pyqs.fail_count > 0).sum()

        st.caption(f"Topics revised so far: {revised}")
        if weak_count:
            st.caption(f"Weak topics pending: {weak_count}")

        return

    # =========================
    # 🛠️ BUILD MODE DASHBOARD
    # =========================
    if mode == "Build":
        st.markdown("## 🛠️ Build Your Knowledge Base")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("➕ Add PYQ", use_container_width=True):
                st.session_state.current_view = "add_pyq"
                st.rerun()

        with col2:
            if st.button("🗂️ Create Study Card", use_container_width=True):
                st.session_state.current_view = "study_cards"
                st.rerun()

        # -------------------------
        # Contextual Info
        # -------------------------
        st.markdown("---")

        pyqs = data.layer.load_pyqs()
        cards = load_cards()

        total_pyqs = len(pyqs)
        total_cards = len(cards)
        pending_cards = pyqs[~pyqs.id.isin(cards.topic_id)]

        st.caption(f"Total PYQs added: {total_pyqs}")
        st.caption(f"Study Cards created: {total_cards}")

        if not pending_cards.empty:
            st.caption(f"Topics pending Study Cards: {len(pending_cards)}")

        return

    # =========================
    # ⚡ EXAM MODE DASHBOARD
    # =========================
    if mode == "Exam":
        st.markdown("## ⚡ Exam Recall")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("⚡ Rapid Review", use_container_width=True):
                st.session_state.current_view = "go_rapid_review"
                st.rerun()

        with col2:
            if st.button("🖼️ Image Sprint", use_container_width=True):
                st.session_state,current_view = "go_image_sprint"
                st.rerun()

        st.markdown("---")

        # Exam Day Mode guardrail
        exam_day = st.toggle(
            "🧠 Exam Day Mode",
            value=st.session_state.get("exam_day_mode", False)
        )
        st.session_state.current_view = "exam"

        if exam_day:
            st.warning("Exam Day Mode is ON. Editing and capture are disabled.")

        return
