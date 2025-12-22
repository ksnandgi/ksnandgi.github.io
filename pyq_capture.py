import streamlit as st
import pandas as pd

from data_layer import load_pyqs, save_pyqs, safe_next_id, new_pyq_row

SUBJECTS = [
    "Medicine", "Surgery", "ObG", "Pediatrics",
    "Pathology", "Pharmacology", "Microbiology",
    "PSM", "Anatomy", "Physiology", "Biochemistry",
    "Radiology", "Dermatology"
]


def render_pyq_capture():
    # -------- Mode Guard --------
    if st.session_state.app_mode != "Build":
        st.info("Switch to 🛠️ Build Mode to add PYQs.")
        return

    st.subheader("➕ Add PYQ")

    # -------- PYQ FORM --------
    with st.form("pyq_form"):
        topic = st.text_input(
            "Topic",
            key="pyq_topic"
        )

        subject = st.selectbox(
            "Subject",
            SUBJECTS,
            key="pyq_subject"
        )

        trigger = st.text_input(
            "Trigger line (one-liner)",
            key="pyq_trigger"
        )

        years = st.text_input(
            "PYQ Years (comma separated)",
            placeholder="2019, 2021",
            key="pyq_years"
        )

        submitted = st.form_submit_button("Save PYQ")

    # -------- SAVE LOGIC --------
    if submitted:
        if not topic.strip():
            st.error("Topic is required.")
            return

        pyqs = load_pyqs()

        row = new_pyq_row(
            topic=topic.strip(),
            subject=subject,
            trigger_line=trigger.strip(),
            pyq_years=years.strip()
        )

        row["id"] = safe_next_id(pyqs["id"])

        pyqs = pd.concat(
            [pyqs, pd.DataFrame([row])],
            ignore_index=True
        )

        save_pyqs(pyqs)

        st.success("✅ PYQ added successfully.")

        # -------- POST-SAVE ACTIONS --------
        col1, col2 = st.columns(2)

        with col1:
            if st.button("➕ Add Another PYQ"):
                # CLEAR FORM KEYS
                for k in [
                    "pyq_topic",
                    "pyq_subject",
                    "pyq_trigger",
                    "pyq_years"
                ]:
                    st.session_state.pop(k, None)

                st.rerun()

        with col2:
            if st.button("🏠 Back to Dashboard"):
                st.session_state.current_view = "dashboard"
                st.rerun()