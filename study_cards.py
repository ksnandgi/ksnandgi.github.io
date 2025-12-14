"""
Module 2 — Study Cards

Responsibilities:
- Manual Study Card creation (1 card per topic)
- Auto Study Card Generator (draft-only)
- Image support (including image-based MCQs)
- External deep-dive URL
- Highlight topics without cards

No revision logic. No analytics.
"""

import streamlit as st
import pandas as pd
import re
from pathlib import Path

from data_layer import (
    load_pyqs,
    load_cards,
    save_cards,
    safe_next_id,
    new_card_row,
    card_exists_for_topic,
    IMAGE_DIR
)

# =========================
# AUTO CARD GENERATOR
# =========================

def auto_generate_bullets(text: str, max_bullets: int = 5) -> str:
    """
    Draft-only bullet generator.
    Heuristic-based (not AI-heavy).
    """
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
    """Save uploaded images locally and return paths."""
    paths = []

    for f in files:
        path = IMAGE_DIR / f"{topic_id}_{f.name}"
        with open(path, "wb") as out:
            out.write(f.read())
        paths.append(str(path))

    return paths


# =========================
# MAIN UI
# =========================

def render_study_cards():
    st.subheader("🗂️ Study Cards")

    pyqs = load_pyqs()
    cards = load_cards()

    # ---- Topic selection ----
    pyqs["label"] = pyqs["topic"] + " (" + pyqs["subject"] + ")"
    topic_map = dict(zip(pyqs["label"], pyqs["id"]))

    selected_label = st.selectbox(
        "Select PYQ Topic",
        options=topic_map.keys()
    )

    topic_id = topic_map[selected_label]
    topic_row = pyqs[pyqs["id"] == topic_id].iloc[0]

    # ---- Card existence check ----
    if card_exists_for_topic(cards, topic_id):
        st.success("Study Card already exists for this topic.")
        st.info("Editing cards is intentionally disabled in this version.")
        return

    st.markdown("### ➕ Create Study Card")

    # ---- Auto Draft ----
    with st.expander("✍️ Auto Study Card Draft (Optional)"):
        raw_text = st.text_area(
            "Paste textbook / notes paragraph",
            height=150
        )

        if st.button("Generate Draft"):
            if raw_text.strip():
                draft = auto_generate_bullets(raw_text)
                st.session_state["draft_bullets"] = draft
            else:
                st.warning("Paste content first.")

    bullets_default = st.session_state.get("draft_bullets", "")

    # ---- Card Form ----
    with st.form("card_form"):
        card_title = st.text_input(
            "Card Title (optional)",
            value=topic_row.topic
        )

        bullets = st.text_area(
            "Bullets (3–7 lines, exam language)",
            value=bullets_default,
            height=180
        )

        external_url = st.text_input(
            "External URL (optional)"
        )

        images = st.file_uploader(
            "Upload images (optional)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True
        )

        submitted = st.form_submit_button("Save Study Card")

        # ---- Validation & Save ----
        if submitted:
            bullet_lines = [b for b in bullets.splitlines() if b.strip()]

            if len(bullet_lines) < 3:
                st.error("Minimum 3 bullets required.")
                return

            image_paths = save_uploaded_images(images, topic_id) if images else []

            row = new_card_row(
                topic_id=topic_id,
                bullets="\n".join(bullet_lines),
                card_title=card_title,
                external_url=external_url,
                image_paths=image_paths
            )

            row["card_id"] = safe_next_id(cards["card_id"])

            cards = pd.concat(
                [cards, pd.DataFrame([row])],
                ignore_index=True
            )

            save_cards(cards)

            st.success("Study Card saved successfully.")
            st.session_state.pop("draft_bullets", None)
            st.rerun()

    # ---- Topics without cards ----
    st.markdown("---")
    st.markdown("### 📌 Topics Without Study Cards")

    topics_with_cards = set(cards["topic_id"])
    missing = pyqs[~pyqs["id"].isin(topics_with_cards)]

    if missing.empty:
        st.success("All topics have Study Cards.")
    else:
        st.write(missing[["topic", "subject"]])