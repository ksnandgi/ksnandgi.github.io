import streamlit as st
import pandas as pd
import data_layer

# =========================
# CONSTANTS
# =========================

SUBJECTS = [
    "Medicine", "Surgery", "ObG", "Pediatrics",
    "Pathology", "Pharmacology", "Microbiology",
    "PSM", "Anatomy", "Physiology", "Biochemistry",
    "Radiology", "Dermatology", "Orthopaedics"
]

# =========================
# AUTO STUDY CARD DRAFT
# =========================

CARD_TEMPLATES = {
    "Medicine": [
        "Definition",
        "Etiology / Causes",
        "Clinical features",
        "Complications",
        "Management"
    ],
    "Surgery": [
        "Definition",
        "Etiology",
        "Clinical features",
        "Indications for surgery",
        "Complications"
    ],
    "Pharmacology": [
        "Drug class",
        "Mechanism of action",
        "Uses",
        "Adverse effects",
        "Contraindications"
    ],
    "Anatomy": [
        "Definition / Location",
        "Relations",
        "Blood supply",
        "Nerve supply",
        "Clinical significance"
    ],
}

def generate_study_card_draft(topic: str, subject: str, trigger: str) -> str:
    template = CARD_TEMPLATES.get(
        subject,
        ["Definition", "Key points", "Clinical relevance"]
    )

    bullets = []

    for section in template:
        if section == "Definition":
            bullets.append(f"• {section}: {topic}")
        elif "Clinical" in section and trigger:
            bullets.append(f"• {section}: {trigger}")
        else:
            bullets.append(f"• {section}:")

    return "\n".join(bullets)

# =========================
# MAIN UI
# =========================

def render_pyq_capture():
    if st.session_state.app_mode != "Build":
        st.info("Switch to 🛠️ Build Mode to add PYQs.")
        return

    st.subheader("➕ Add PYQ")

    # Initialize storage
    st.session_state.setdefault("last_added_pyq", None)
    image_paths: list[str] = []

    # ---------------------
    # PYQ FORM
    # ---------------------
    with st.form("pyq_form", clear_on_submit=True):
        topic = st.text_input("Topic")
        subject = st.selectbox("Subject", SUBJECTS)
        trigger = st.text_input("Trigger line (one-liner)")
        years = st.text_input("PYQ Years (comma separated)")

        pyq_images = st.file_uploader(
            "Upload PYQ image (optional)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True
        )

        submitted = st.form_submit_button("Save PYQ")

    # ---------------------
    # SAVE PYQ
    # ---------------------
    if submitted:
        if not topic.strip():
            st.error("Topic is required.")
            return

        pyqs = data_layer.load_pyqs()

        if not pyqs[pyqs.topic.str.lower() == topic.strip().lower()].empty:
            st.warning("A PYQ with this topic already exists.")
            return

        new_id = data_layer.safe_next_id(pyqs["id"])

        if pyq_images:
            data_layer.IMAGE_DIR.mkdir(parents=True, exist_ok=True)
            for f in pyq_images:
                path = data_layer.IMAGE_DIR / f"pyq_{new_id}_{f.name}"
                with open(path, "wb") as out:
                    out.write(f.getbuffer())
                image_paths.append(str(path))

        row = data_layer.new_pyq_row(
            topic=topic.strip(),
            subject=subject,
            trigger_line=trigger.strip(),
            pyq_years=years.strip()
        )

        row["id"] = new_id
        row["pyq_image_paths"] = ";".join(image_paths)
        row["pyq_years"] = years.strip()

        pyqs = pd.concat([pyqs, pd.DataFrame([row])], ignore_index=True)
        data_layer.save_pyqs(pyqs)

        # 🔑 CRITICAL: Persist for next action
        st.session_state.last_added_pyq = row

        st.success("✅ PYQ added successfully.")

    # ---------------------
    # POST-SAVE ACTIONS
    # ---------------------
    if st.session_state.last_added_pyq:
        st.markdown("---")

        if st.button("🧠 Create Study Card (Auto Draft)"):
            pyq = st.session_state.last_added_pyq

            st.session_state.auto_card_draft = generate_study_card_draft(
                topic=pyq["topic"],
                subject=pyq["subject"],
                trigger=pyq["trigger_line"]
            )
            st.session_state.auto_card_topic_id = pyq["id"]

            st.session_state.current_view = "study_cards"
            st.session_state.app_mode = "Build"

            # Cleanup
            st.session_state.last_added_pyq = None

            st.rerun()

        if st.button("🏠 Back to Dashboard"):
            st.session_state.last_added_pyq = None
            st.session_state.current_view = "dashboard"
            st.rerun()