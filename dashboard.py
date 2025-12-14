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
from datetime import date

from data_layer import load_pyqs, load_cards, is_due


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
    st.subheader("📊 Dashboard")

    pyqs = load_pyqs()
    cards = load_cards()

    if pyqs.empty:
        st.info("Start by adding PYQ topics.")
        return

    # ---- Daily Plan ----
    plan = generate_daily_plan(pyqs)

    st.markdown("### 📅 Today’s Plan")

    if plan.empty:
        st.success("You’re all caught up for today.")
    else:
        for _, row in plan.iterrows():
            st.markdown(f"- **{row.topic}** ({row.subject})")

    st.caption(
        "Why this today? Focuses on due and weak topics to maximize recall efficiency."
    )

    # ---- Next Best Action ----
    weak_subjects = (
        pyqs[pyqs.fail_count >= 2]
        .subject.value_counts()
    )

    if not weak_subjects.empty:
        top_subject = weak_subjects.index[0]
        st.info(
            f"**Next best action:** Revise 3 weak topics from {top_subject}"
        )
    else:
        st.info(
            "**Next best action:** Continue regular revision to maintain strength"
        )

    # ---- Weak Area Overview ----
    st.markdown("---")
    st.markdown("### ⚠️ Weak Areas")

    if weak_subjects.empty:
        st.success("No persistent weak areas identified.")
    else:
        for subject, count in weak_subjects.items():
            st.markdown(f"- {subject}: {count} topics")

    # ---- Progress Indicators ----
    st.markdown("---")
    st.markdown("### 📈 Progress Overview")

    total_topics = len(pyqs)
    with_cards = pyqs.id.isin(cards.topic_id).sum()
    without_cards = total_topics - with_cards

    st.markdown(f"- Total topics captured: **{total_topics}**")
    st.markdown(f"- Topics with Study Cards: **{with_cards}**")
    st.markdown(f"- Topics needing consolidation: **{without_cards}**")

    # ---- Soft Subject Balance ----
    recent_focus = pyqs.sort_values(
        by="last_revised",
        ascending=False
    ).head(10)

    if not recent_focus.empty:
        dominant_subject = recent_focus.subject.mode().iloc[0]
        st.caption(f"Recent focus: {dominant_subject}-heavy")

    # ---- Exam Mode Nudge ----
    today = date.today()
    if today.month in [12, 1, 2, 3]:  # example exam window
        st.warning(
            "You’ve been revising consistently. Consider using Rapid Review or Image Sprint modes."
        )