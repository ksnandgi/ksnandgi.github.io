import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, date
import os

# ================= CONFIG =================
st.set_page_config(
    page_title="NEET PG Revision",
    page_icon="🧠",
    layout="wide"
)

DATA_FILE = Path("pyq_topics.csv")
IMAGE_DIR = Path("images")
IMAGE_DIR.mkdir(exist_ok=True)

COLUMNS = [
    "id","topic","subject","pyq_years","key_line",
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

# ================= DATA HELPERS =================
def load_data():
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)

        # ---- schema safety ----
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = None

        # ---- type safety ----
        df["revision_count"] = pd.to_numeric(df["revision_count"], errors="coerce").fillna(0).astype(int)
        df["fail_count"] = pd.to_numeric(df["fail_count"], errors="coerce").fillna(0).astype(int)

        for col in ["last_revised", "next_revision_date", "created_at"]:
            df[col] = pd.to_datetime(df[col], errors="coerce")

        return df

    return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def next_revision_date(count):
    schedule = [0, 1, 3, 7, 15, 30]
    days = schedule[min(count, len(schedule)-1)]
    return datetime.now() + timedelta(days=days)

df = load_data()
today_ts = pd.Timestamp(date.today())

# ================= SAFE DATE FILTER =================
def is_due(df):
    """
    SAFE replacement for .dt.date comparisons
    """
    return df["next_revision_date"].isna() | (df["next_revision_date"] <= today_ts)

# ================= EXAM SETTINGS =================
st.sidebar.header("🧪 Exam Settings")
exam_date = st.sidebar.date_input("Exam Date")

days_left = (exam_date - date.today()).days if exam_date else None

def exam_mode(days):
    if days is None: return "Normal"
    if days > 60: return "Normal"
    if 30 < days <= 60: return "High Yield Focus"
    if 15 < days <= 30: return "Weak + High Yield"
    return "Final Sprint"

mode = exam_mode(days_left)

# ================= UI =================
st.title("🧠 NEET PG – PYQ Revision Assistant")
st.caption(f"📅 Mode: **{mode}**")

tabs = st.tabs(["📊 Dashboard","➕ Add PYQ","🔁 Revise"])

# =====================================================
# 📊 DASHBOARD
# =====================================================
with tabs[0]:
    st.subheader("📊 Dashboard")

    if df.empty:
        st.info("No topics added yet.")
    else:
        due = df[is_due(df)]
        weak = df[(df.revision_count >= 2) & (df.fail_count >= 2)]

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total Topics", len(df))
        c2.metric("Due Today", len(due))
        c3.metric("Weak Topics", len(weak))
        c4.metric("Days to Exam", days_left if days_left is not None else "-")

        st.markdown("### 🔴 Weak Areas (Subject-wise)")
        if not weak.empty:
            st.bar_chart(weak.subject.value_counts())
        else:
            st.success("No weak areas detected 🎉")

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
        images = st.file_uploader("Upload Images", accept_multiple_files=True)

        if st.form_submit_button("Add"):
            if not topic.strip() or not key.strip():
                st.error("Topic and key concept are required.")
            else:
                paths = []
                for img in images:
                    fname = f"{datetime.now().timestamp()}_{img.name}"
                    path = IMAGE_DIR / fname
                    with open(path, "wb") as f:
                        f.write(img.read())
                    paths.append(str(path))

                new_row = {
                    "id": int(df.id.max()) + 1 if not df.empty else 1,
                    "topic": topic.strip(),
                    "subject": subject,
                    "pyq_years": pyq.strip(),
                    "key_line": key.strip(),
                    "status": "not_revised",
                    "high_yield": "yes" if hy else "no",
                    "revision_count": 0,
                    "fail_count": 0,
                    "last_revised": None,
                    "next_revision_date": pd.Timestamp.now(),
                    "image_paths": ";".join(paths),
                    "created_at": pd.Timestamp.now()
                }

                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success("Topic added successfully")

# =====================================================
# 🔁 REVISION
# =====================================================
with tabs[2]:
    st.subheader("🔁 Revision")

    due = df[is_due(df)]

    # ---- exam-mode filtering ----
    if mode == "High Yield Focus":
        due = due[due.high_yield == "yes"]
    elif mode == "Weak + High Yield":
        due = due[(due.high_yield == "yes") | (due.fail_count >= 2)]
    elif mode == "Final Sprint":
        due = due[due.fail_count >= 2]

    if due.empty:
        st.success("Nothing due today 🎉")
    else:
        for idx, row in due.iterrows():
            with st.expander(f"{row.topic} ({row.subject})"):
                st.markdown(f"**Key Concept:** {row.key_line}")
                st.markdown(f"**PYQ Years:** {row.pyq_years}")

                if pd.notna(row.image_paths):
                    for p in row.image_paths.split(";"):
                        if os.path.exists(p):
                            st.image(p)

                c1, c2 = st.columns(2)

                with c1:
                    if st.button("✅ Revised", key=f"rev_{idx}"):
                        df.at[idx, "revision_count"] += 1
                        df.at[idx, "last_revised"] = pd.Timestamp.now()
                        df.at[idx, "next_revision_date"] = next_revision_date(
                            df.at[idx, "revision_count"]
                        )
                        save_data(df)
                        st.rerun()

                with c2:
                    if st.button("🔁 Still Weak", key=f"fail_{idx}"):
                        df.at[idx, "fail_count"] += 1
                        df.at[idx, "next_revision_date"] = pd.Timestamp.now() + timedelta(days=1)
                        save_data(df)
                        st.rerun()