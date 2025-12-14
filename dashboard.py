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
    st.subheader("📊 Dashboard")

    pyqs = load_pyqs()
    cards = load_cards()

    if pyqs.empty:
        st.info("Start by adding PYQ topics.")

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

    st.markdown("---")
    st.markdown("## 💾 Backup & Restore")

    st.caption(
        "Streamlit Cloud resets data on reboot. "
        "Use Full Backup regularly to avoid data loss."
    )

# =========================
# FULL BACKUP / RESTORE
# =========================

    st.markdown("### 🟢 Full Backup (Recommended)")

    full_backup = create_full_backup()
    st.download_button(
        "⬇️ Download Full Backup (ZIP)",
        data=full_backup,
        file_name="neet_pg_full_backup.zip"
    )

    full_restore = st.file_uploader(
        "⬆️ Restore Full Backup (ZIP)",
        type="zip"
    )

    if full_restore:
        restore_full_backup(full_restore)
        st.success("Full backup restored. Please reload the app.")

# =========================
# BACKUP SECTION
# =========================
    st.markdown("### ⬇️ Backup")

    if os.path.exists("pyq_topics.csv"):
        st.download_button(
            "Download PYQs CSV",
            data=open("pyq_topics.csv", "rb"),
            file_name="pyq_topics.csv"
        )

    if os.path.exists("study_cards.csv"):
        st.download_button(
            "Download Study Cards CSV",
            data=open("study_cards.csv", "rb"),
            file_name="study_cards.csv"
        )

    if os.path.exists("card_images"):
        img_zip = zip_images()
        st.download_button(
            "Download Card Images (ZIP)",
            data=img_zip,
            file_name="card_images.zip"
        )

# =========================
# RESTORE SECTION
# =========================
    st.markdown("### ⬆️ Restore")

    pyq_file = st.file_uploader("Restore PYQs CSV", type="csv")
    if pyq_file:
        with open("pyq_topics.csv", "wb") as f:
            f.write(pyq_file.getbuffer())
        st.success("PYQs restored. Reload the app.")

    card_file = st.file_uploader("Restore Study Cards CSV", type="csv")
    if card_file:
        with open("study_cards.csv", "wb") as f:
            f.write(card_file.getbuffer())
        st.success("Study Cards restored. Reload the app.")

    img_zip_file = st.file_uploader("Restore Card Images (ZIP)", type="zip")
    if img_zip_file:
        with zipfile.ZipFile(img_zip_file) as z:
            z.extractall("card_images")
        st.success("Images restored. Reload the app.")
