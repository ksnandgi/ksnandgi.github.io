import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, date
import os

from reportlab.platypus import SimpleDocTemplate, Paragraph, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

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

# ================= PDF EXPORT =================
def export_cards_to_pdf(subject=None):
    merged = pyq.merge(cards, left_on="id", right_on="topic_id")
    if subject:
        merged = merged[merged.subject == subject]

    file_path = Path("study_cards_export.pdf")
    doc = SimpleDocTemplate(str(file_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    for _, r in merged.iterrows():
        story.append(Paragraph(f"<b>{r.topic} ({r.subject})</b>", styles["Heading3"]))
        for line in r.bullets.splitlines():
            story.append(Paragraph(line, styles["Normal"]))
        if pd.notna(r.image_paths):
            for p in r.image_paths.split(";"):
                if os.path.exists(p):
                    story.append(RLImage(p, width=260, height=180))
        story.append(Paragraph("<br/>", styles["Normal"]))

    doc.build(story)
    return file_path

# ================= DAILY PLAN =================
def daily_revision_plan(df, limit=8):
    due = df[is_due(df)]
    weak = df[df.fail_count >= 2]
    strong = df[df.revision_count >= 3]

    plan = pd.concat([
        due,
        weak,
        strong.sample(min(len(strong), 2)) if not strong.empty else strong
    ]).drop_duplicates()

    return plan.head(limit)

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
# 📊 DASHBOARD
# =====================================================
with tabs[0]:
    plan = daily_revision_plan(pyq)

    st.markdown("### 📅 Today’s Revision Plan")
    if plan.empty:
        st.success("Nothing scheduled today 🎉")
    else:
        st.dataframe(plan[["topic","subject","fail_count"]], use_container_width=True)

    st.markdown("### 📄 Export Study Cards")
    subject_pdf = st.selectbox("Export subject", ["All"] + SUBJECTS)
    if st.button("Generate PDF"):
        path = export_cards_to_pdf(None if subject_pdf=="All" else subject_pdf)
        st.download_button("Download PDF", open(path,"rb"), file_name="neet_pg_study_cards.pdf")

# =====================================================
# 🔁 REVISION (ALWAYS SUBJECT-WISE)
# =====================================================
with tabs[3]:
    subject = st.selectbox("Subject", ["All"] + SUBJECTS)
    image_only = st.toggle("🖼️ Image-only Mode")

    due = pyq[is_due(pyq)]
    if subject != "All":
        due = due[due.subject == subject]

    due = due.sort_values(["fail_count","revision_count"], ascending=False)

    for idx, row in due.iterrows():
        card = cards[cards.topic_id == row.id]
        with st.expander(f"{row.topic} ({row.subject})"):
            if not card.empty:
                c = card.iloc[0]
                if not image_only:
                    for line in c.bullets.splitlines():
                        st.markdown(f"- {line}")
                if pd.notna(c.image_paths):
                    for p in c.image_paths.split(";"):
                        if os.path.exists(p):
                            st.image(p)
                if image_only:
                    st.info(c.bullets.splitlines()[0])
            else:
                st.warning("No Study Card")
                st.markdown(row.trigger_line)

# =====================================================
# 🖼️ IMAGE SPRINT (PER SUBJECT)
# =====================================================
with tabs[4]:
    sprint_subject = st.selectbox("Select Subject", SUBJECTS)
    sprint_cards = pyq[
        (pyq.subject == sprint_subject) &
        (pyq.id.isin(cards.topic_id))
    ]

    for _, row in sprint_cards.iterrows():
        c = cards[cards.topic_id == row.id].iloc[0]
        st.markdown(f"### {row.topic}")
        if pd.notna(c.image_paths):
            for p in c.image_paths.split(";"):
                if os.path.exists(p):
                    st.image(p)
        st.info(c.bullets.splitlines()[0])
        st.divider()