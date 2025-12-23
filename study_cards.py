"""
Module 2 — Study Cards
"""

import streamlit as st
import pandas as pd
import re

import data_layer

# =========================
# AUTO CARD GENERATOR (MANUAL NOTES)
# =========================

def auto_generate_bullets(text: str, max_bullets: int = 5) -> str:
    sentences = re.split(r"[.;\n]", text)
    bullets = []

    for s in sentences:
        s = s.strip()
        if 5 < len(s) < 120:
            bullets.append(s)

    bullets = bullets[:max_bullets]
    return "\n".join(f"• {b}" for b in bullets)


# =========================
# SUBJECT-BASED STRUCTURE
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

def generate_structured_template(topic: str, subject: str) -> str:
    template = CARD_TEMPLATES.get(
        subject,
        ["Definition", "Key points", "Clinical relevance"]
    )
    return "\n".join(f"• {section}:" for section in template)


# =========================
# IMAGE HANDLING
# =========================

def save_uploaded_images(files, topic_id: int) -> list[str]:
    paths = []
    data_layer.IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    for f in files:
        path = data_layer.IMAGE_DIR / f"{topic_id}_{f.name}"
        with open(path, "wb") as out:
            out.write(f.getbuffer())
        paths.append(str(path))

    return paths


# =========================
# MAIN UI
# =========================

def render_study_cards():
    # ---- VIEW GUARD ----
    if st.session_state.current_view != "study_cards":
        return

    # ---- MODE GUARD ----
    if st.session_state.app_mode != "Build":
        st.session_state.edit_card = False
        return

    st.subheader("🗂️ Study Cards")

    pyqs = data_layer.load_pyqs()
    cards = data_layer.load_cards()

    if pyqs.empty:
        st.info("No PYQ topics found yet.")
        return

    # =========================
    # 🔍 SEARCH
    # =========================
    st.markdown("### 🔍 Find Topic")

    query = st.text_input(
        "Search topic",
        placeholder="e.g. pneumo, anemia, stroke"
    )

    filtered = (
        pyqs[pyqs["topic"].str.contains(query, case=False, na=False)]
        if query else pyqs
    )

    if filtered.empty:
        st.info("No matching topics found.")
        return

    filtered = filtered.copy()
    filtered["label"] = filtered["topic"] + " (" + filtered["subject"] + ")"
    topic_map = dict(zip(filtered["label"], filtered["id"]))

    # =========================
    # AUTO-SELECT FROM PYQ → STUDY CARD
    # =========================
    auto_topic_id = st.session_state.get("auto_card_topic_id")

    if auto_topic_id and auto_topic_id in filtered["id"].values:
        selected_label = filtered.loc[
            filtered.id == auto_topic_id, "label"
        ].iloc[0]
        st.session_state.pop("auto_card_topic_id", None)
    else:
        selected_label = st.selectbox(
            "Select Topic",
            list(topic_map.keys())
        )

    topic_id = topic_map[selected_label]
    topic_row = pyqs[pyqs.id == topic_id].iloc[0]
    card_df = cards[cards.topic_id == topic_id]

    st.caption(f"Subject: {topic_row.subject}")
    st.markdown("---")

    # =========================
    # 📄 PREVIEW MODE
    # =========================
    if not card_df.empty and not st.session_state.get("edit_card", False):
        card = card_df.iloc[0]

        st.markdown("### 📄 Study Card Preview")

        for line in card.bullets.splitlines():
            st.write(line)

        if isinstance(card.image_paths, str) and card.image_paths.strip():
            st.markdown("#### 🖼️ Images")
            for p in card.image_paths.split(";"):
                st.image(p)

        if isinstance(card.external_url, str) and card.external_url.strip():
            st.markdown(f"[🔗 External Reference]({card.external_url})")

        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("✏️ Edit Card"):
                st.session_state.edit_card = True
                st.rerun()

        with col2:
            if st.button("🗑️ Delete Card", type="secondary"):
                data_layer.delete_card(topic_id)
                st.session_state.edit_card = False
                st.rerun()

        with col3:
            if st.button("← Back"):
                st.session_state.edit_card = False
                st.session_state.current_view = "dashboard"
                st.rerun()

        return

    # =========================
    # ✍️ CREATE / EDIT MODE
    # =========================
    st.markdown("### 🧠 Key Points")

    # -------- BULLET SOURCE PRIORITY --------
    if st.session_state.get("auto_card_draft"):
        default_bullets = st.session_state.auto_card_draft
    elif not card_df.empty:
        default_bullets = card_df.iloc[0].bullets
    else:
        default_bullets = ""

    # -------- UX HINT --------
    if not default_bullets:
        st.info(
            "💡 Tip: Click **Generate Structured Draft** to get an exam-oriented template."
        )

    # -------- STRUCTURED TEMPLATE BUTTON --------
    if st.button("🧠 Generate Structured Draft"):
        st.session_state.auto_card_draft = generate_structured_template(
            topic=topic_row.topic,
            subject=topic_row.subject
        )
        st.rerun()

    # -------- AUTO DRAFT FROM NOTES --------
    with st.expander("✍️ Auto Draft from Notes (Optional)"):
        raw_text = st.text_area("Paste textbook / notes", height=150)
        if st.button("Generate from Notes") and raw_text.strip():
            st.session_state["draft_bullets"] = auto_generate_bullets(raw_text)
            st.rerun()

    bullets = st.text_area(
        "One concept per line",
        value=st.session_state.get("draft_bullets", default_bullets),
        height=200
    )

    # =========================
    # 🖼️ IMAGES
    # =========================
    st.markdown("### 🖼️ Images (Optional)")

    images = st.file_uploader(
        "Upload X-ray / CT / ECG images",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    st.markdown("---")

    # =========================
    # ACTIONS
    # =========================
    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Study Card", type="primary"):
            bullet_lines = [b for b in bullets.splitlines() if b.strip()]
            if len(bullet_lines) < 3:
                st.error("Minimum 3 bullet points required.")
                return

            image_paths = save_uploaded_images(images, topic_id) if images else []

            data_layer.upsert_card(
                topic_id=topic_id,
                card_title=topic_row.topic,
                bullets="\n".join(bullet_lines),
                image_paths=";".join(image_paths),
                external_url=""
            )

            # 🔑 CLEAR STATES
            st.session_state.pop("draft_bullets", None)
            st.session_state.pop("auto_card_draft", None)
            st.session_state.edit_card = False

            st.success("Study card saved.")
            st.rerun()

    with col2:
        if st.button("← Cancel"):
            st.session_state.pop("draft_bullets", None)
            st.session_state.pop("auto_card_draft", None)
            st.session_state.edit_card = False
            st.session_state.current_view = "dashboard"
            st.rerun()