import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, date

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="NEET PG Revision",
    page_icon="🧠",
    layout="wide"
)

DATA_FILE = Path("pyq_topics.csv")

COLUMNS = [
    "id",
    "topic",
    "subject",
    "pyq_years",
    "key_line",
    "status",
    "high_yield",
    "revision_count",
    "last_revised",
    "next_revision_date",
    "created_at"
]

SUBJECTS = [
    "Medicine","Surgery","ObG","Pediatrics","Pathology",
    "Pharmacology","Microbiology","PSM","Anatomy",
    "Physiology","Biochemistry"
]

# ---------------- DATA HELPERS ----------------
def load_data():
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)

        # 🔒 SCHEMA FIX (auto-upgrade old CSVs)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = None

        # 🔒 TYPE FIXES
        df["revision_count"] = pd.to_numeric(
            df["revision_count"], errors="coerce"
        ).fillna(0).astype(int)

        for dcol in ["last_revised", "next_revision_date", "created_at"]:
            df[dcol] = pd.to_datetime(df[dcol], errors="coerce")

        return df

    return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def compute_next_revision(count):
    schedule = [0, 1, 3, 7, 15, 30]
    days = schedule[min(count, len(schedule) - 1)]
    return datetime.now() + timedelta(days=days)

df = load_data()
today = date.today()

# ---------------- UI ----------------
st.title("🧠 NEET PG – PYQ Revision Assistant")

tabs = st.tabs(["📊 Dashboard", "➕ Add PYQ", "🔁 Revise"])

# =====================================================
# 📊 DASHBOARD
# =====================================================
with tabs[0]:
    st.subheader("📅 Topics Due Today")

    if df.empty:
        st.info("No topics added yet.")
    else:
        due_mask = (
            df["next_revision_date"].isna()
            | (df["next_revision_date"].dt.date <= today)
        )

        due = df[due_mask]

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Topics", len(df))
        c2.metric("Due Today", len(due))
        c3.metric(
            "High-Yield Due",
            len(due[due["high_yield"] == "yes"])
        )

        st.dataframe(
            due[["topic","subject","revision_count","high_yield"]],
            use_container_width=True
        )

# =====================================================
# ➕ ADD PYQ
# =====================================================
with tabs[1]:
    st.subheader("➕ Add PYQ Topic")

    with st.form("add"):
        topic = st.text_input("Topic")
        subject = st.selectbox("Subject", SUBJECTS)
        pyq = st.text_input("PYQ Years")
        key = st.text_area("One-line concept")
        hy = st.checkbox("High Yield")

        if st.form_submit_button("Add"):
            if topic.strip() == "" or key.strip() == "":
                st.error("Topic and key concept are required.")
            else:
                new_row = {
                    "id": int(df["id"].max()) + 1 if not df.empty else 1,
                    "topic": topic.strip(),
                    "subject": subject,
                    "pyq_years": pyq.strip(),
                    "key_line": key.strip(),
                    "status": "not_revised",
                    "high_yield": "yes" if hy else "no",
                    "revision_count": 0,
                    "last_revised": None,
                    "next_revision_date": datetime.now(),
                    "created_at": datetime.now()
                }

                df = pd.concat(
                    [df, pd.DataFrame([new_row])],
                    ignore_index=True
                )
                save_data(df)
                st.success("Topic added successfully ✅")

# =====================================================
# 🔁 REVISE
# =====================================================
with tabs[2]:
    st.subheader("🔁 Revision Mode")

    if df.empty:
        st.info("No topics available.")
    else:
        due_mask = (
            df["next_revision_date"].isna()
            | (df["next_revision_date"].dt.date <= today)
        )

        due = df[due_mask]

        if due.empty:
            st.success("Nothing due today 🎉")
        else:
            for idx, row in due.iterrows():
                with st.expander(f"{row.topic} ({row.subject})"):
                    st.markdown(f"**Key Concept:** {row.key_line}")
                    st.markdown(f"**PYQ Years:** {row.pyq_years}")

                    c1, c2 = st.columns(2)

                    with c1:
                        if st.button("✅ Revised", key=f"rev_{idx}"):
                            df.at[idx, "revision_count"] += 1
                            df.at[idx, "last_revised"] = datetime.now()
                            df.at[idx, "next_revision_date"] = compute_next_revision(
                                df.at[idx, "revision_count"]
                            )
                            save_data(df)
                            st.rerun()

                    with c2:
                        if st.button("🔁 Revise Again Tomorrow", key=f"again_{idx}"):
                            df.at[idx, "next_revision_date"] = datetime.now() + timedelta(days=1)
                            save_data(df)
                            st.rerun()