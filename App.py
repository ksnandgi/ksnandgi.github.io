import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

st.set_page_config("NEET PG Revision", "🧠", layout="wide")

DATA_FILE = Path("pyq_topics.csv")

COLUMNS = [
    "id","topic","subject","pyq_years","key_line",
    "status","high_yield",
    "revision_count","last_revised","next_revision_date",
    "created_at"
]

SUBJECTS = [
    "Medicine","Surgery","ObG","Pediatrics","Pathology",
    "Pharmacology","Microbiology","PSM","Anatomy",
    "Physiology","Biochemistry"
]

# ---------------- HELPERS ----------------
def load_data():
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
        for col in ["last_revised","next_revision_date","created_at"]:
            df[col] = pd.to_datetime(df[col], errors="coerce")
        return df
    return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def next_revision_date(count):
    schedule = [0,1,3,7,15,30]
    days = schedule[min(count,5)]
    return datetime.now() + timedelta(days=days)

df = load_data()
today = datetime.now().date()

# ---------------- UI ----------------
st.title("🧠 NEET PG – PYQ Revision Assistant")

tabs = st.tabs(["📊 Dashboard","➕ Add PYQ","🔁 Revise"])

# ================= DASHBOARD =================
with tabs[0]:
    st.subheader("📅 Topics Due Today")

    if df.empty:
        st.info("No topics added yet.")
    else:
        due = df[
            (df.next_revision_date.isna()) |
            (df.next_revision_date.dt.date <= today)
        ]

        st.metric("Due Today", len(due))
        st.metric("High-Yield Due", len(due[due.high_yield=="yes"]))

        st.dataframe(
            due[["topic","subject","revision_count","high_yield"]],
            use_container_width=True
        )

# ================= ADD PYQ =================
with tabs[1]:
    st.subheader("➕ Add PYQ Topic")

    with st.form("add"):
        topic = st.text_input("Topic")
        subject = st.selectbox("Subject", SUBJECTS)
        pyq = st.text_input("PYQ Years")
        key = st.text_area("One-line concept")
        hy = st.checkbox("High Yield")

        if st.form_submit_button("Add"):
            if topic and key:
                row = {
                    "id": len(df)+1,
                    "topic": topic,
                    "subject": subject,
                    "pyq_years": pyq,
                    "key_line": key,
                    "status": "not_revised",
                    "high_yield": "yes" if hy else "no",
                    "revision_count": 0,
                    "last_revised": None,
                    "next_revision_date": datetime.now(),
                    "created_at": datetime.now()
                }
                df = pd.concat([df,pd.DataFrame([row])], ignore_index=True)
                save_data(df)
                st.success("Added")

# ================= REVISE =================
with tabs[2]:
    st.subheader("🔁 Revision Mode")

    due = df[
        (df.next_revision_date.isna()) |
        (df.next_revision_date.dt.date <= today)
    ]

    if due.empty:
        st.success("Nothing due today 🎉")
    else:
        for idx,row in due.iterrows():
            with st.expander(f"{row.topic} ({row.subject})"):
                st.markdown(row.key_line)

                c1,c2 = st.columns(2)

                with c1:
                    if st.button("✅ Revised", key=f"rev{idx}"):
                        df.at[idx,"revision_count"] += 1
                        df.at[idx,"last_revised"] = datetime.now()
                        df.at[idx,"next_revision_date"] = next_revision_date(
                            df.at[idx,"revision_count"]
                        )
                        save_data(df)
                        st.experimental_rerun()

                with c2:
                    if st.button("🔁 Revise Again", key=f"again{idx}"):
                        df.at[idx,"next_revision_date"] = datetime.now() + timedelta(days=1)
                        save_data(df)
                        st.experimental_rerun()