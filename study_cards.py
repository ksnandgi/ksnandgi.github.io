"""
Module 2 — Study Cards

Responsibilities:
- Manual Study Card creation
- Auto Study Card draft generator
- Image support
- External URL
- Delete whole Study Card safely
"""

import streamlit as st
import pandas as pd
import re
import os

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

    if not files:
        return paths

    for f in files:
        path = IMAGE_DIR / f"{topic_id}_{f.name}"
        # Ensure parent directory exists
        try:
            os.makedirs(path.parent, exist_ok=True)
        except Exception:
            pass

        # f is a Streamlit UploadedFile-like object; read() returns bytes
        with open(path, "wb") as out:
            out.write(f.read())
        paths.append(str(path))

    return paths


# =========================
# DELETE STUDY CARD
# =========================

def delete_study_card(cards_df: pd.DataFrame, topic_id: int) -> pd.DataFrame:
    card_rows = cards_df[cards_df.topic_id == topic_id]

    if card_rows.empty:
        return cards_df

    card = card_rows.iloc[0]

    # Delete images (image_paths expected to be semicolon-separated string)
    image_paths_str = card.get("image_paths", "") if isinstance(card, pd.Series) else ""
    if pd.notna(image_paths_str) and image_paths_str:
        for path in str(image_paths_str).split(";"):
            path = path.strip()
            if not path:
                continue
            try:
                os.remove(path)
            except Exception:
                pass

    # Remove card row
    return cards_df[cards_df.topic_id != topic_id].reset_index(drop=True)


# =========================
# MAIN UI
# =========================

def render_study_cards():
    st.subheader("🗂️ Study Cards")

    pyqs = load_pyqs()
    cards = load_cards()

    # ---- Empty PYQ guard ----
    if pyqs.empty:
        st.info("No PYQ topics found yet.")
        st.markdown("➡️ Add PYQs first, then come back to create Study Cards.")
        return

    pyqs = pyqs.copy()
    pyqs["label"] = pyqs["topic"] + " (" + pyqs["subject"] + ")"

    labels = pyqs["label"].tolist()
    ids = pyqs["id"].tolist()

    if not labels:
        st.warning("No valid PYQ topics available.")
        return

    selected_label = st.selectbox("Select PYQ Topic", labels)
    topic_id = ids[labels.index(selected_label)]
    topic_row = pyqs[pyqs.id == topic_id].iloc[0]

    # If a Study Card already exists for this topic, show existing-card UI first
    if card_exists_for_topic(cards, topic_id):
        st.success("Study Card already exists for this topic.")
        st.warning("If something is wrong, you can delete and recreate the Study Card.")

        confirm = st.checkbox("I understand this will permanently delete the Study Card")

        if st.button("🗑️ Delete Study Card", disabled=not confirm):
            cards = delete_study_card(cards, topic_id)
            save_cards(cards)
            st.success("Study Card deleted. You can now recreate it.")
            st.rerun()

        # Don't show creation form if a card already exists
        return

    # ---- Create Card ----
    st.markdown("### ➕ Create Study Card")

    with st.expander("✍️ Auto Study Card Draft (Optional)"):
        raw_text = st.text_area("Paste textbook / notes", height=150)
        if st.button("Generate Draft") and raw_text.strip():
            st.session_state["draft_bullets"] = auto_generate_bullets(raw_text)

    bullets_default = st.session_state.get("draft_bullets", "")

    with st.form("card_form"):
        card_title = st.text_input("Card Title (optional)", value=topic_row.topic)
        bullets = st.text_area("Bullets (min 3)", value=bullets_default, height=180)
        external_url = st.text_input("External URL (optional)")
        images = st.file_uploader(
            "Upload images (optional)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True
        )

        submitted = st.form_submit_button("Save Study Card")

        if submitted:
            bullet_lines = [b for b in bullets.splitlines() if b.strip()]
            if len(bullet_lines) < 3:
                st.error("Minimum 3 bullets required.")
                # preserve current bullets as draft so user doesn't lose work
                st.session_state["draft_bullets"] = bullets
                return

            # Save uploaded images and serialize paths as semicolon-separated string
            image_paths = save_uploaded_images(images, topic_id) if images else []
            image_paths_str = ";".join(image_paths) if image_paths else ""

            row = new_card_row(
                topic_id=topic_id,
                bullets="\n".join(bullet_lines),
                card_title=card_title,
                external_url=external_url,
                image_paths=image_paths_str
            )

            # Determine next card_id safely
            if "card_id" in cards.columns and not cards["card_id"].empty:
                row["card_id"] = safe_next_id(cards["card_id"])
            else:
                # start IDs at 1 if no existing cards
                row["card_id"] = 1

            cards = pd.concat([cards, pd.DataFrame([row])], ignore_index=True)
            save_cards(cards)

            st.success("Study Card saved successfully.")
            st.session_state.pop("draft_bullets", None)
            st.rerun()
