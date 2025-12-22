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

    for f in files:
        path = data_layer.IMAGE_DIR / f"{topic_id}_{f.name}"
        with open(path, "wb") as out:
            out.write(f.read())
        paths.append(str(path))

    return paths


# =========================
# DELETE STUDY CARD
# =========================

def delete_study_card(cards_df: pd.DataFrame, topic_id: int) -> pd.DataFrame:
    card = cards_df[cards_df.topic_id == topic_id]

    if card.empty:
        return cards_df

    card = card.iloc[0]

    if card.image_paths:
        for path in card.image_paths.split(";"):
            try:
                os.remove(path)
            except Exception:
                pass

    return cards_df[cards_df.topic_id != topic_id]


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

    pyqs = pyqs.copy()
    pyqs["label"] = pyqs["topic"] + " (" + pyqs["subject"] + ")"

    labels = pyqs["label"].tolist()
    ids = pyqs["id"].tolist()

    selected_label = st.selectbox("Select PYQ Topic", labels)
    topic_id = ids[labels.index(selected_label)]
    topic_row = pyqs[pyqs.id == topic_id].iloc[0]

    # ---- Existing card ----
    if data_layer.card_exists_for_topic(cards, topic_id):
        st.success("Study Card already exists for this topic.")
        st.warning("If something is wrong, you can delete and recreate the Study Card.")

        confirm = st.checkbox("I understand this will permanently delete the Study Card")

        if st.button("🗑️ Delete Study Card", disabled=not confirm):
            cards = delete_study_card(cards, topic_id)
            save_cards(cards)
            st.success("Study Card deleted. You can now recreate it.")
            st.rerun()

        return

    # ---- Create card ----
    st.markdown("### ➕ Create Study Card")

    with st.expander("✍️ Auto Draft (Optional)"):
        raw_text = st.text_area("Paste textbook / notes", height=150)
        if st.button("Generate Draft") and raw_text.strip():
            st.session_state["draft_bullets"] = auto_generate_bullets(raw_text)

    bullets_default = st.session_state.get("draft_bullets", "")

    with st.form("card_form"):
        card_title = st.text_input("Card Title", value=topic_row.topic)
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
                return

            image_paths = save_uploaded_images(images, topic_id) if images else []

            row = data_layer.new_card_row(
                topic_id=topic_id,
                bullets="\n".join(bullet_lines),
                card_title=card_title,
                external_url=external_url,
                image_paths=image_paths
            )

            row["card_id"] = data_layer.safe_next_id(cards["card_id"])
            cards = pd.concat([cards, pd.DataFrame([row])], ignore_index=True)
            data_layer.save_cards(cards)

            st.success("Study Card saved successfully.")
            st.session_state.pop("draft_bullets", None)
            st.rerun()
