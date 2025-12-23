"""
Module 5 — Dashboard & Guidance

Responsibilities:
- Dashboard as entry point
- Daily revision suggestions
- Weak-area overview
- Minimal progress indicators
- Next Best Action prompts
- Exam-mode shortcuts

No editing. No pressure metrics. No comparisons.
"""

import streamlit as st
import pandas as pd

import data_layer


# =========================
# MAIN DASHBOARD
# =========================

def render_dashboard():

    mode = st.session_state.app_mode

    # =========================
    # 📘 STUDY MODE DASHBOARD
    # =========================
    if mode == "Study":
        st.subheader("📘 Suggested topics to revise")

        pyqs = data_layer.load_pyqs()
        cards = data_layer.load_cards()

        # Only topics WITH study cards
        pyqs = pyqs[pyqs.id.isin(cards.topic_id)]

        if pyqs.empty:
            st.info("No topics ready for revision yet.")
            st.markdown("➡️ Add PYQs and Study Cards in Build Mode.")
            return

        # Due or weak topics
        due = pyqs[data_layer.is_due(pyqs)]
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
        st.subheader("Quick Actions")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🖼️ Image Sprint"):
                st.session_state.app_mode = "Exam"
                st.session_state.current_view = "image_sprint"
                st.session_state.sprint_index = 0
                st.session_state.last_sprint_subject = None
                st.rerun()

        with col2:
            if st.button("⚠️ Weak Areas"):
                st.session_state.app_mode = "Study"
                st.session_state.current_view = "revision_weak"
                st.rerun()

        # -------------------------
        # Progress Overview
        # -------------------------
        st.markdown("---")
        st.subheader("Progress Overview")

        revised = int(pyqs.revision_count.sum())
        weak_count = int((pyqs.fail_count > 0).sum())

        st.caption(f"Topics revised (total): {revised}")
        if weak_count:
            st.caption(f"Topics marked weak (total): {weak_count}")

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
            if st.button("🗂️ Create / Update Study Card", use_container_width=True):
                st.session_state.current_view = "study_cards"
                st.rerun()

        st.markdown("---")

        pyqs = data_layer.load_pyqs()
        cards = data_layer.load_cards()

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
                st.session_state.current_view = "rapid_review"
                st.rerun()

        with col2:
            if st.button("🖼️ Image Sprint", use_container_width=True):
                st.session_state.current_view = "image_sprint"
                st.session_state.sprint_index = 0
                st.session_state.last_sprint_subject = None
                st.rerun()

        st.markdown("---")