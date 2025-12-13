import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, date
import os

st.set_page_config("NEET PG Revision", "🧠", layout="wide")

DATA_FILE = Path("pyq_topics.csv")
IMAGE_DIR = Path("images")
IMAGE_DIR.mkdir(exist_ok=True)

COLUMNS = [
    "id","topic","subject","pyq_years","key_line",
    "study_card",
    "status","high_yield",
    "revision_count","fail_count",
    "last_revised","next_revision_date",
    "image_paths","created_at"
]

SUBJECTS = [
    "Medicine","Surgery","ObG","Pediatrics","Pathology",
    "Pharmacology","Microbiology","PSM","Anatomy",
    "Physiology","Biochemistry"
]

def load_data():
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = None
        df["revision_count"] = pd.to_numeric(df["revision_count"], errors="coerce").fillna(0).astype(int)
        df["fail_count"] = pd.to_numeric(df["fail_count"], errors="coerce").fillna(0).astype(int)
        for d in ["last_revised","next_revision_date","created_at"]:
            df[d] = pd.to_datetime(df[d], errors="coerce")
        return df
    return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def next_revision_date(count):
    schedule = [0,1,3,7,15,30]
    return pd.Timestamp.now() + timedelta(days=schedule[min(count,5)])

df = load_data()
today_ts = pd.Timestamp(date.today())

def is_due(df):
    return df["next_revision_date"].isna() | (df["next_revision_date"] <= today_ts)

# ---------------- UI ----------------
st.title("🧠 NEET PG – Study & Revision System")

tabs = st.tabs(["📊 Dashboard","➕ Add / Edit Topic","🔁 Revise"])

# ================= DASHBOARD =================
with tabs[0]:
    if df.empty:
        st.info("No topics added yet.")
    else:
        due = df[is_due(df)]
        weak = df[(df.revision_count >= 2) & (df.fail_count >= 2)]

        c1,c2,c3 = st.columns(3)
        c1.metric("Total Topics", len(df))
        c2.metric("Due Today", len(due))
        c3.metric("Weak Topics", len(weak))

# ================= ADD / EDIT =================
with tabs[1]:
    st.subheader("➕ Add / Edit PYQ Topic")

    topic_list = ["New Topic"] + df.topic.dropna().tolist()
    choice = st.selectbox("Select Topic", topic_list)

    if choice == "New Topic":
        topic = st.text_input("Topic")
        subject = st.selectbox("Subject", SUBJECTS)
        pyq = st.text_input("PYQ Years")
        key = st.text_area("One-line anchor")
        card = st.text_area(
            "Study Card (3–7 bullets, one per line)",
            placeholder="• Most common...\n• Key differentiator...\n• Classic association..."
        )
        hy = st.checkbox("High Yield")

        if st.button("Save Topic"):
            row = {
                "id": int(df.id.max()) + 1 if not df.empty else 1,
                "topic": topic,
                "subject": subject,
                "pyq_years": pyq,
                "key_line": key,
                "study_card": card,
                "status": "not_revised",
                "high_yield": "yes" if hy else "no",
                "revision_count": 0,
                "fail_count": 0,
                "last_revised": None,
                "next_revision_date": pd.Timestamp.now(),
                "image_paths": None,
                "created_at": pd.Timestamp.now()
            }
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            save_data(df)
            st.success("Saved")

# ================= REVISE =================
with tabs[2]:
    due = df[is_due(df)]

    if due.empty:
        st.success("Nothing due today 🎉")
    else:
        for idx,row in due.iterrows():
            with st.expander(f"{row.topic} ({row.subject})"):
                if pd.notna(row.study_card):
                    st.markdown("### 📌 Study Card")
                    for line in row.study_card.splitlines():
                        st.markdown(f"- {line}")

                st.markdown(f"**Anchor:** {row.key_line}")

                c1,c2 = st.columns(2)
                with c1:
                    if st.button("✅ Revised", key=f"rev_{idx}"):
                        df.at[idx,"revision_count"] += 1
                        df.at[idx,"next_revision_date"] = next_revision_date(df.at[idx,"revision_count"])
                        save_data(df)
                        st.rerun()
                with c2:
                    if st.button("🔁 Still Weak", key=f"fail_{idx}"):
                        df.at[idx,"fail_count"] += 1
                        df.at[idx,"next_revision_date"] = pd.Timestamp.now() + timedelta(days=1)
                        save_data(df)
                        st.rerun()