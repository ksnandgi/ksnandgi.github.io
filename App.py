import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, date
import os

# ================= CONFIG =================
st.set_page_config("NEET PG Study System", "🧠", layout="wide")

PYQ_FILE = Path("pyq_topics.csv")
CARD_FILE = Path("study_cards.csv")
IMAGE_DIR = Path("card_images")
IMAGE_DIR.mkdir(exist_ok=True)

# ================= SCHEMAS =================
PYQ_COLS = [
    "id","topic","subject","pyq_years","trigger_line",
    "revision_count","fail_count",
    "last_revised","next_revision_date","created_at"
]

CARD_COLS = [
    "card_id","topic_id","card_title",
    "bullets","external_url","image_paths",
    "created_at"
]

SUBJECTS = [
    "Medicine","Surgery","ObG","Pediatrics","Pathology",
    "Pharmacology","Microbiology","PSM","Anatomy",
    "Physiology","Biochemistry","Radiology","Dermatology"
]

# ================= HELPERS =================
def load_csv(path, cols):
    if path.exists():
        df = pd.read_csv(path)
        for c in cols:
            if c not in df.columns:
                df[c] = None
        return df
    return pd.DataFrame(columns=cols)

def save_csv(df, path):
    df.to_csv(path, index=False)

def next_revision_date(count):
    schedule = [0,1,3,7,15,30]
    return pd.Timestamp.now() + timedelta(days=schedule[min(count,5)])

def is_due(df):
    today = pd.Timestamp(date.today())
    return df["next_revision_date"].isna() | (df["next_revision_date"] <= today)

# ================= LOAD DATA =================
pyq = load_csv(PYQ_FILE, PYQ_COLS)
cards = load_csv(CARD_FILE, CARD_COLS)

for c in ["last_revised","next_revision_date","created_at"]:
    pyq[c] = pd.to_datetime(pyq[c], errors="coerce")

# ================= UI =================
st.title("🧠 NEET PG – Compact Study & Revision System")

tabs = st.tabs([
    "📊 Dashboard",
    "➕ PYQ Capture",
    "🗂️ Study Cards",
    "🔁 Revision",
    "🖼️ Image Sprint"
])

# =====================================================
# ➕ PYQ CAPTURE (FIXED)
# =====================================================
with tabs[1]:
    st.subheader("➕ PYQ Capture")

    with st.form("pyq_add", clear_on_submit=True):
        topic = st.text_input("Topic (mandatory)")
        subject = st.selectbox("Subject", SUBJECTS)
        years = st.text_input("PYQ Years (optional)")
        trigger = st.text_area("One-line trigger (mandatory)")

        submitted = st.form_submit_button("Save PYQ")

        if submitted:
            if not topic.strip() or not trigger.strip():
                st.error("Topic and trigger line are mandatory")
            else:
                next_id = (
                    1 if pyq.empty or pyq["id"].isna().all()
                    else int(pyq["id"].max()) + 1
                )

                row = {
                    "id": next_id,
                    "topic": topic.strip(),
                    "subject": subject,
                    "pyq_years": years.strip(),
                    "trigger_line": trigger.strip(),
                    "revision_count": 0,
                    "fail_count": 0,
                    "last_revised": None,
                    "next_revision_date": pd.Timestamp.now(),
                    "created_at": pd.Timestamp.now()
                }

                pyq = pd.concat([pyq, pd.DataFrame([row])], ignore_index=True)
                save_csv(pyq, PYQ_FILE)
                st.success("PYQ added successfully")
                st.rerun()