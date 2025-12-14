"""
Module 1 — PYQ Capture

Responsibilities:
- Text-based PYQ capture
- Voice-based capture (optional)
- Capture mode toggle
- Quick Save flow
- Topic normalization
- Soft duplicate hint with preview

No Study Card logic. No Revision logic.
"""

import streamlit as st
import pandas as pd
import speech_recognition as sr
import re

from data_layer import (
    load_pyqs,
    save_pyqs,
    safe_next_id,
    new_pyq_row
)

# =========================
# CONSTANTS
# =========================

SUBJECTS = [
    "Medicine", "Surgery", "ObG", "Pediatrics", "Pathology",
    "Pharmacology", "Microbiology", "PSM", "Anatomy",
    "Physiology", "Biochemistry", "Radiology", "Dermatology"
]

# =========================
# NORMALIZATION & DUPLICATES
# =========================

def normalize_topic(text: str) -> str:
    """Normalize topic text silently."""
    text = re.sub(r"\s+", " ", text.strip())
    return text.title()


def find_soft_duplicates(pyq_df: pd.DataFrame, topic: str, limit: int = 2) -> pd.DataFrame:
    """Return soft-matching duplicate topics."""
    norm = normalize_topic(topic)
    return pyq_df[
        pyq_df["topic"].str.lower().str.strip() == norm.lower()
    ].head(limit)


# =========================
# VOICE INPUT
# =========================

def voice_to_text() -> str:
    """Capture voice input and convert to text."""
    audio = st.audio_input("🎙️ Tap to record PYQ concept")
    if not audio:
        return ""

    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data)
            st.success(f"Recognized: {text}")
            return text
    except sr.UnknownValueError:
        st.error("Could not understand audio")
    except sr.RequestError:
        st.error("Speech recognition service unavailable")
    return ""


# =========================
# MAIN UI
# =========================

def render_pyq_capture():
    st.subheader("➕ PYQ Capture")

    pyqs = load_pyqs()

    # ---- Capture Mode ----
    mode = st.radio(
        "Capture mode",
        ["Text", "Voice"],
        horizontal=True
    )

    voice_text = ""
    if mode == "Voice":
        voice_text = voice_to_text()

    # ---- Form ----
    with st.form("pyq_capture_form", clear_on_submit=True):
        topic = st.text_input(
            "Topic (mandatory)",
            value=voice_text
        )

        subject = st.selectbox(
            "Subject",
            SUBJECTS,
            index=0
        )

        pyq_years = st.text_input(
            "PYQ Years (optional)"
        )

        trigger = st.text_area(
            "One-line trigger (mandatory)",
            value=voice_text,
            height=80
        )

        submitted = st.form_submit_button("Save PYQ")

        # ---- Validation ----
        if submitted:
            if not topic.strip() or not trigger.strip():
                st.error("Topic and Trigger are mandatory.")
                return

            topic_norm = normalize_topic(topic)

            # ---- Soft Duplicate Hint ----
            duplicates = find_soft_duplicates(pyqs, topic_norm)

            if not duplicates.empty:
                st.info("ℹ️ Similar topic already exists:")
                for _, row in duplicates.iterrows():
                    st.markdown(
                        f"""
                        **Topic:** {row.topic}  
                        **Subject:** {row.subject}  
                        **Trigger:** {row.trigger_line}  
                        **PYQ Years:** {row.pyq_years or "—"}
                        """
                    )

            # ---- Save ----
            new_row = new_pyq_row(
                topic=topic_norm,
                subject=subject,
                trigger_line=trigger,
                pyq_years=pyq_years
            )

            new_row["id"] = safe_next_id(pyqs["id"])

            pyqs = pd.concat(
                [pyqs, pd.DataFrame([new_row])],
                ignore_index=True
            )

            save_pyqs(pyqs)

            st.success("PYQ saved successfully")
            st.rerun()