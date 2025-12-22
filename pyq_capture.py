import streamlit as st
import pandas as pd

import data_layer

SUBJECTS = [
    "Medicine", "Surgery", "ObG", "Pediatrics",
    "Pathology", "Pharmacology", "Microbiology",
    "PSM", "Anatomy", "Physiology", "Biochemistry",
    "Radiology", "Dermatology"
]


def render_pyq_capture():
    if st.session_state.app_mode != "Build":
        st.info("Switch to 🛠️ Build Mode to add PYQs.")
        return

    st.subheader("➕ Add PYQ")

    with st.form("pyq_form", clear_on_submit=True):
        topic = st.text_input("Topic")
        subject = st.selectbox("Subject", SUBJECTS)
        trigger = st.text_input("Trigger line (one-liner)")
        years = st.text_input(
            "PYQ Years (comma separated)",
            placeholder="2019, 2021"
        )

        submitted = st.form_submit_button("Save PYQ")

    if submitted:
        if not topic.strip():
            st.error("Topic is required.")
            return

        pyqs = data_layer.load_pyqs()

        row = new_pyq_row(
            topic=topic.strip(),
            subject=subject,
            trigger_line=trigger.strip(),
            pyq_years=years.strip()
        )

        row["id"] = safe_next_id(pyqs["id"])
        pyqs = pd.concat([pyqs, pd.DataFrame([row])], ignore_index=True)
        save_pyqs(pyqs)

        st.success("✅ PYQ added successfully.")

        col1, col2 = st.columns(2)

        with col1:
            st.info("Form cleared. You can add another PYQ.")

        with col2:
            if st.button("🏠 Back to Dashboard"):
                st.session_state.current_view = "dashboard"
                st.rerun()
