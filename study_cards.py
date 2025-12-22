"""
Module 2 — Study Cards
"""

import streamlit as st
import pandas as pd
import re
import os

import data_layer

# =========================
# AUTO CARD GENERATOR
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
# IMAGE HANDLING
# =========================

def save_uploaded_images(files, topic_id: int) -> list[str]:
    paths = []

    # Ensure directory exists (Streamlit Cloud safe)
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
    # ---- MODE GUARD ----
    if st.session_state.app_mode != "Build":
        st.info("Switch to 🛠️ Build Mode to create or manage Study Cards.")
        return

    st.subheader("🗂️ Study Cards")

    pyqs = data_layer.load_pyqs()
    cards = data_layer.load_cards()

    # ---- Empty PYQ guard ----
    if pyqs.empty:
        st.info("No PYQ topics found yet.")
        st.markdown("➡️ Add PYQs first, then come back to create Study Cards.")
        return

    # =========================
    # SECTION 1 — SEARCH & CONTEXT
    # =========================

    st.markdown("### 🔍 Find Topic")

    query = st.text_input(
        "Search topic (type 2–3 letters)",
        placeholder="e.g. pneumo, anemia, stroke"
    )

    filtered = pyqs[
        pyqs["topic"].str.contains(query, case=False, na=False)
    ] if query else pyqs

    if filtered.empty:
        st.info("No matching topics found.")
        return

    filtered = filtered.copy()
    filtered["label"] = filtered["topic"] + " (" + filtered["subject"] + ")"

    topic_map = dict(zip(filtered["label"], filtered["id"]))

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
    # PREVIEW MODE (IF CARD EXISTS)
    # =========================
    if not card_df.empty and not st.session_state.get("edit_card", False):
        st.session_state.focus_mode = True
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
                st.session_state.focus_mode = True
                st.rerun()

        with col2:
            if st.button("🗑️ Delete Card", type="secondary"):
                data_layer.delete_card(topic_id)
                st.success("Study card deleted. You can recreate it anytime.")
                st.session_state.edit_card = False
                st.session_state.focus_mode = False
                st.rerun()

        with col3:
            if st.button("← Back"):
                st.session_state.edit_card = False
                st.session_state.focus_mode = False
                st.rerun()

        return

    # =========================
    # SECTION 2 — CORE LEARNING
    # =========================
    st.markdown("### 🧠 Key Points")

    default_bullets = (
        card_df.iloc[0].bullets if not card_df.empty else ""
    )

    # Auto-draft expander
    with st.expander("✍️ Auto Draft (Optional)"):
        raw_text = st.text_area("Paste textbook / notes", height=150)
        if st.button("Generate Draft") and raw_text.strip():
            st.session_state["draft_bullets"] = auto_generate_bullets(raw_text)

    bullets = st.text_area(
        "One concept per line (exam-oriented)",
        value=st.session_state.get("draft_bullets", default_bullets),
        height=180,
        placeholder="• Sudden chest pain\n• Hyperresonance\n• Tracheal deviation (tension pneumothorax)"
    )

    st.caption("Tip: Keep bullets short and high-yield.")

    # =========================
    # SECTION 3 — IMAGES
    # =========================
    st.markdown("### 🖼️ Attach Images (Optional)")

    images = st.file_uploader(
        "Upload X-ray / CT / ECG images",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    st.caption("Images improve recall. You can add them later.")

    # =========================
    # SECTION 4 — ACTIONS
    # =========================
    st.markdown("---")

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

            st.success("Study card saved successfully.")
            st.session_state.pop("draft_bullets", None)
            st.session_state.edit_card = False
            st.session_state.focus_mode = False
            st.rerun()

    with col2:
        if st.button("← Cancel"):
            st.session_state.edit_card = False
            st.session_state.focus_mode = False
            st.rerun()