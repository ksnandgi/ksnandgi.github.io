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

No capture, no editing, no analytics dashboards.
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
        by=["fail_count", "revision_count", "next_revision_date"],
        ascending=[False, False, True]
    )


def interleave_subjects(df: pd.DataFrame) -> pd.DataFrame:
    """Avoid long runs of same subject."""
    result = []
    groups = {k: list(v.itertuples()) for k, v in df.groupby("subject")}

    while any(groups.values()):
        for subject in list(groups.keys()):
            if groups[subject]:
                result.append(groups[subject].pop(0))

    return pd.DataFrame(result)


# =========================
# DAILY TARGET
# =========================

def compute_daily_target(pyqs: pd.DataFrame, cap: int = 10) -> int:
    due = pyqs[is_due(pyqs)]
    weak = pyqs[pyqs.fail_count >= 2]
    return min(cap, max(len(due), len(weak), 5))


# =========================
# MAIN UI
# =========================

def render_revision_engine():
    st.subheader("🔁 Revision")

    init_revision_session()

    pyqs = load_pyqs()
    cards = load_cards()

    # ---- Subject Filter ----
    subjects = ["All"] + sorted(pyqs["subject"].dropna().unique().tolist())
    subject_filter = st.selectbox("Subject", subjects)

    if subject_filter != "All":
        pyqs = pyqs[pyqs.subject == subject_filter]

    # ---- Filter Due / Weak ----
    pyqs = pyqs[is_due(pyqs) | (pyqs.fail_count > 0)]

    if pyqs.empty:
        st.success("No topics due for revision today.")
        return

    # ---- Session-level suppression ----
    pyqs = pyqs[~pyqs.id.isin(st.session_state.session_seen)]

    if pyqs.empty:
        st.success("Session complete.")
        return

    # ---- Ordering ----
    ordered = prioritize(pyqs)
    ordered = interleave_subjects(ordered)

    # ---- Daily Target ----
    target = compute_daily_target(pyqs)
    st.markdown(f"**Today’s target:** {target} topics")
    st.markdown(f"**Completed:** {st.session_state.revised_today} / {target}")

    # ---- Image-only toggle ----
    image_only = st.toggle("🖼️ Image-only revision", value=False)

    # ---- Pick next topic ----
    row = ordered.iloc[0]
    topic_id = row.id
    topic_start = time.time()

    st.markdown(f"### {row.topic}")
    st.caption(row.subject)

    # ---- Study Card or Trigger ----
    card = cards[cards.topic_id == topic_id]

    if not card.empty:
        card = card.iloc[0]

        if card.image_paths:
            for p in card.image_paths.split(";"):
                st.image(p)

        if not image_only:
            for line in card.bullets.splitlines():
                st.write(line)

            if card.external_url:
                st.markdown(f"[External reference]({card.external_url})")
    else:
        st.warning("No Study Card — trigger only")
        st.markdown(f"**{row.trigger_line}**")

    # ---- Actions ----
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Revised"):
            duration = time.time() - topic_start

            # Implicit uncertainty
            if duration > 20:
                row.fail_count += 1

            row.revision_count += 1
            row.last_revised = pd.Timestamp.now()
            row.next_revision_date = compute_next_revision(row.revision_count)

            pyqs.loc[pyqs.id == topic_id, row.index] = row.values
            save_pyqs(pyqs)

            st.session_state.session_seen.add(topic_id)
            st.session_state.revised_today += 1

            st.rerun()

    with col2:
        if st.button("❌ Weak"):
            row.fail_count += 1
            row.last_revised = pd.Timestamp.now()
            row.next_revision_date = pd.Timestamp(date.today()) + pd.Timedelta(days=1)

            pyqs.loc[pyqs.id == topic_id, row.index] = row.values
            save_pyqs(pyqs)

            st.session_state.session_seen.add(topic_id)
            st.session_state.revised_today += 1

            st.rerun()

    # ---- Quiet Streak ----
    today = date.today()
    if st.session_state.last_revision_date != today:
        st.session_state.revision_streak += 1
        st.session_state.last_revision_date = today

    st.caption(f"Revision streak: {st.session_state.revision_streak} days")