import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, date
import os

# ---------------- CONFIG ----------------
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
    "image_paths",
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

        for col in COLUMNS:
            if col not in df.columns:
                df[col] = None

        df["revision_count"] = pd.to_numeric(df["revision_count"], errors="coerce").fillna(0).astype(int)
        df["fail_count"] = pd.to_numeric(df["fail_count"], errors="coerce").fillna(0).astype(int)

        for dcol in ["last_revised","next_revision_date","created_at"]:
            df[dcol] = pd.to_datetime(df[dcol], errors="coerce")

        return df

    return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def next_revision(count):
    schedule = [0,1,3,7,15,30]
    return datetime.now() + timedelta(days=schedule[min(count,5)])

df = load_data()
today = date.today()

# ---------------- EXAM SETTINGS ----------------
st.sidebar.header("🧪 Exam Settings")
exam_date = st.sidebar.date_input("Exam Date")
days_left = (exam_date - today).days if exam_date else None

# ---------------- MODE ----------------
def exam_mode(days):
    if days is None:
        return "Normal"
    if days > 60:
        return "Normal"
    if 30 < days <= 60:
        return "High Yield Focus"
    if 15 < days <= 30:
        return "Weak + High Yield"
    return "Final Sprint"

mode = exam_mode(days_left)

# ---------------- UI ----------------
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
        due = df[
            df.next_revision_date.isna() |
            (df.next_revision_date.dt.date <= today)
        ]

        weak = df[(df.revision_count >= 2) & (df.fail_count >= 2)]

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total Topics", len(df))
        c2.metric("Due Today", len(due))
        c3.metric("Weak Topics", len(weak))
        c4.metric("Days to Exam", days_left if days_left else "-")

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
            paths = []
            for img in images:
                p = IMAGE_DIR / f"{datetime.now().timestamp()}_{img.name}"
                with open(p, "wb") as f:
                    f.write(img.read())
                paths.append(str(p))

            row = {
                "id": int(df.id.max()) + 1 if not df.empty else 1,
                "topic": topic,
                "subject": subject,
                "pyq_years": pyq,
                "key_line": key,
                "status": "not_revised",
                "high_yield": "yes" if hy else "no",
                "revision_count": 0,
                "fail_count": 0,
                "last_revised": None,
                "next_revision_date": datetime.now(),
                "image_paths": ";".join(paths),
                "created_at": datetime.now()
            }

            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            save_data(df)
            st.success("Topic added")

# =====================================================
# 🔁 REVISION
# =====================================================
with tabs[2]:
    st.subheader("🔁 Revision")

    due = df[
        df.next_revision_date.isna() |
        (df.next_revision_date.dt.date <= today)
    ]

    if mode == "High Yield Focus":
        due = due[due.high_yield=="yes"]
    elif mode == "Weak + High Yield":
        due = due[(due.high_yield=="yes") | (due.fail_count>=2)]
    elif mode == "Final Sprint":
        due = due[due.fail_count>=2]

    if due.empty:
        st.success("Nothing due 🎉")
    else:
        for idx,row in due.iterrows():
            with st.expander(f"{row.topic} ({row.subject})"):
                st.markdown(row.key_line)

                if pd.notna(row.image_paths):
                    for p in row.image_paths.split(";"):
                        if os.path.exists(p):
                            st.image(p)

                c1,c2 = st.columns(2)

                with c1:
                    if st.button("✅ Revised", key=f"rev{idx}"):
                        df.at[idx,"revision_count"] += 1
                        df.at[idx,"last_revised"] = datetime.now()
                        df.at[idx,"next_revision_date"] = next_revision(df.at[idx,"revision_count"])
                        save_data(df)
                        st.rerun()

                with c2:
                    if st.button("🔁 Still Weak", key=f"fail{idx}"):
                        df.at[idx,"fail_count"] += 1
                        df.at[idx,"next_revision_date"] = datetime.now() + timedelta(days=1)
                        save_data(df)
                        st.rerun()