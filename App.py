import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, date
import re, os

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

# ================= AUTO CARD DRAFT =================
KEYWORDS = {
    "most common": 3, "characteristic": 3, "except": 3,
    "difference": 3, "vs": 3,
    "associated": 2, "treatment": 2,
    "diagnosis": 2, "feature": 2
}

def generate_study_card(text, max_bullets=5):
    sentences = re.split(r'[.!?]\s+', text)
    scored = []
    for s in sentences:
        score = sum(w for k,w in KEYWORDS.items() if k in s.lower())
        scored.append((score, s.strip()))
    scored.sort(reverse=True)
    bullets = []
    for _, s in scored[:max_bullets]:
        words = s.split()[:12]
        bullets.append("• " + " ".join(words))
    return "\n".join(bullets)

# ================= LOAD DATA =================
pyq = load_csv(PYQ_FILE, PYQ_COLS)
cards = load_csv(CARD_FILE, CARD_COLS)

for c in ["last_revised","next_revision_date","created_at"]:
    pyq[c] = pd.to_datetime(pyq[c], errors="coerce")

# ================= UI =================
st.title("🧠 NEET PG – Compact Study & Revision System")

rapid_mode = st.toggle("⚡ Rapid Review Mode (Last 15 Days)", value=False)

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

# =====================================================
# ➕ PYQ CAPTURE
# =====================================================
with tabs[1]:
    st.subheader("➕ PYQ Capture")

    with st.form("pyq_add"):
        topic = st.text_input("Topic")
        subject = st.selectbox("Subject", SUBJECTS)
        years = st.text_input("PYQ Years")
        trigger = st.text_area("One-line trigger")

        if st.form_submit_button("Save PYQ"):
            row = {
                "id": int(pyq.id.max())+1 if not pyq.empty else 1,
                "topic": topic, "subject": subject,
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
# 🗂️ STUDY CARDS (WITH IMAGES)
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
        raw = st.text_area("Paste explanation (optional)")
        if st.button("Generate Draft"):
            st.session_state["draft"] = generate_study_card(raw)

        bullets = st.text_area(
            "Study Card Bullets",
            value=st.session_state.get("draft","")
        )

        imgs = st.file_uploader(
            "Upload images", accept_multiple_files=True,
            type=["png","jpg","jpeg"]
        )

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
# 🔁 REVISION + RAPID MODE
# =====================================================
with tabs[3]:
    due = pyq[is_due(pyq)]

    if rapid_mode:
        due = due[due.id.isin(cards.topic_id)]
        due = due.sort_values(["fail_count","revision_count"], ascending=False)

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