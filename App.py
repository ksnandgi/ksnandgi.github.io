import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, date
import re, os

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
    "status","revision_count","fail_count",
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
    "Physiology","Biochemistry"
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
def export_cards_to_pdf(subject_filter=None):
    file_path = Path("study_cards_export.pdf")
    doc = SimpleDocTemplate(str(file_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    merged = pyq.merge(cards, left_on="id", right_on="topic_id")

    if subject_filter:
        merged = merged[merged.subject == subject_filter]

    for _, row in merged.iterrows():
        story.append(Paragraph(f"<b>{row.topic} ({row.subject})</b>", styles["Heading3"]))

        for line in row.bullets.splitlines():
            story.append(Paragraph(line, styles["Normal"]))

        if pd.notna(row.image_paths):
            for p in row.image_paths.split(";"):
                if os.path.exists(p):
                    story.append(RLImage(p, width=250, height=180))

        story.append(Paragraph("<br/>", styles["Normal"]))

    doc.build(story)
    return file_path

# ================= UI =================
st.title("🧠 NEET PG – Compact Study & Revision System")

rapid_mode = st.toggle("⚡ Rapid Review Mode", value=False)

tabs = st.tabs([
    "📊 Dashboard",
    "➕ PYQ Capture",
    "🗂️ Study Cards",
    "🔁 Revision"
])

# =====================================================
# 📊 DASHBOARD
# =====================================================
with tabs[0]:
    with_cards = set(cards.topic_id.dropna())
    no_cards = pyq[~pyq.id.isin(with_cards)]

    c1,c2,c3 = st.columns(3)
    c1.metric("Total PYQs", len(pyq))
    c2.metric("Study Cards", len(cards))
    c3.metric("Needs Consolidation", len(no_cards))

    st.markdown("### 📄 Export Study Cards")
    subject_for_pdf = st.selectbox("Export Subject (optional)", ["All"] + SUBJECTS)
    if st.button("Export PDF"):
        path = export_cards_to_pdf(None if subject_for_pdf=="All" else subject_for_pdf)
        st.success("PDF generated")
        st.download_button("Download PDF", open(path, "rb"), file_name="neet_pg_study_cards.pdf")

# =====================================================
# ➕ PYQ CAPTURE
# =====================================================
with tabs[1]:
    with st.form("pyq_add"):
        topic = st.text_input("Topic")
        subject = st.selectbox("Subject", SUBJECTS)
        years = st.text_input("PYQ Years")
        trigger = st.text_area("One-line trigger")

        if st.form_submit_button("Save PYQ"):
            row = {
                "id": int(pyq.id.max())+1 if not pyq.empty else 1,
                "topic": topic,
                "subject": subject,
                "pyq_years": years,
                "trigger_line": trigger,
                "status": "not_revised",
                "revision_count": 0,
                "fail_count": 0,
                "last_revised": None,
                "next_revision_date": pd.Timestamp.now(),
                "created_at": pd.Timestamp.now()
            }
            pyq = pd.concat([pyq, pd.DataFrame([row])], ignore_index=True)
            save_csv(pyq, PYQ_FILE)
            st.success("PYQ added")

# =====================================================
# 🗂️ STUDY CARDS
# =====================================================
with tabs[2]:
    pyq_no_card = pyq[~pyq.id.isin(cards.topic_id)]
    if pyq_no_card.empty:
        st.success("All topics consolidated 🎉")
    else:
        topic_map = {
            f"{r.topic} ({r.subject})": r.id
            for _, r in pyq_no_card.iterrows()
        }
        selected = st.selectbox("Select topic", topic_map.keys())
        topic_id = topic_map[selected]

        title = st.text_input("Card Title")
        bullets = st.text_area("Study Card Bullets (3–7 lines)")
        imgs = st.file_uploader("Upload images", accept_multiple_files=True)
        url = st.text_input("External URL (optional)")

        if st.button("Save Study Card"):
            paths = []
            for img in imgs:
                p = IMAGE_DIR / f"{datetime.now().timestamp()}_{img.name}"
                with open(p,"wb") as f:
                    f.write(img.read())
                paths.append(str(p))

            card = {
                "card_id": int(cards.card_id.max())+1 if not cards.empty else 1,
                "topic_id": topic_id,
                "card_title": title,
                "bullets": bullets,
                "external_url": url,
                "image_paths": ";".join(paths),
                "created_at": pd.Timestamp.now()
            }
            cards = pd.concat([cards, pd.DataFrame([card])], ignore_index=True)
            save_csv(cards, CARD_FILE)
            st.success("Study Card saved")

# =====================================================
# 🔁 REVISION (SUBJECT-WISE RAPID REVIEW)
# =====================================================
with tabs[3]:
    due = pyq[is_due(pyq)]

    if rapid_mode:
        subject_filter = st.selectbox("Select Subject", SUBJECTS)
        due = due[
            (due.subject == subject_filter) &
            (due.id.isin(cards.topic_id))
        ]
        due = due.sort_values(
            ["fail_count","revision_count"],
            ascending=False
        )

    for idx,row in due.iterrows():
        card = cards[cards.topic_id == row.id]
        with st.expander(f"{row.topic} ({row.subject})"):
            if not card.empty:
                c = card.iloc[0]
                for line in c.bullets.splitlines():
                    st.markdown(f"- {line}")

                if pd.notna(c.image_paths):
                    for p in c.image_paths.split(";"):
                        if os.path.exists(p):
                            st.image(p)

                if c.external_url:
                    st.link_button("🔗 Full Topic", c.external_url)
            else:
                st.markdown(row.trigger_line)

            if not rapid_mode:
                if st.button("✅ Revised", key=f"rev_{idx}"):
                    pyq.at[idx,"revision_count"] += 1
                    pyq.at[idx,"next_revision_date"] = next_revision_date(
                        pyq.at[idx,"revision_count"]
                    )
                    save_csv(pyq, PYQ_FILE)
                    st.rerun()