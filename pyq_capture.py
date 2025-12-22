"""
Module 1 — PYQ Capture
"""

import streamlit as st
import pandas as pd
import re
import speech_recognition as sr

from data_layer import (
    load_pyqs,
    save_pyqs,
    safe_next_id,
    new_pyq_row
)

# =========================
# MAIN UI
# =========================

def render_pyq_capture():
    # ---- MODE GUARD ----
    if st.session_state.app_mode != "Build":
        st.info("Switch to 🛠️ Build Mode to add PYQ topics.")
        return

    st.subheader("➕ Add PYQ")

    pyqs = load_pyqs()

    topic = st.text_input("Topic")
    subject = st.selectbox(
        "Subject",
        [
            "Medicine", "Surgery", "ObG", "Pediatrics",
            "Pathology", "Pharmacology", "Microbiology",
            "PSM", "Anatomy", "Physiology", "Biochemistry",
            "Radiology", "Dermatology"
        ]
    )

    trigger = st.text_input("Trigger line (one-liner)")
    years = st.text_input("PYQ Years (comma separated)", placeholder="2019, 2021")

    if st.button("Save PYQ"):
        if not topic.strip():
            st.error("Topic is required.")
            return

        row = new_pyq_row(
            topic=topic.strip(),
            subject=subject,
            trigger_line=trigger.strip(),
            pyq_years=years.strip()
        )

        row["id"] = safe_next_id(pyqs["id"])
        pyqs = pd.concat([pyqs, pd.DataFrame([row])], ignore_index=True)
        save_pyqs(pyqs)

        st.success("PYQ added successfully.")
        st.rerun()
