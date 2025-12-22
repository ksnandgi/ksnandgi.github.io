"""
Module 0 — Data Layer (Foundation)

Responsibilities:
- CSV schema definitions
- Safe loading & saving
- Schema healing
- Safe ID generation
- Date handling
- Invariants enforcement (1 Study Card per Topic)

No UI logic. No Streamlit dependencies.
"""

from pathlib import Path
from datetime import datetime, timedelta, date
import pandas as pd
from io import BytesIO
import zipfile
import os
import shutil


# =========================
# GLOBAL CONFIG
# =========================

BASE_DIR = Path(".")
DATA_VERSION = "v1"

PYQ_FILE = BASE_DIR / "pyq_topics.csv"
CARD_FILE = BASE_DIR / "study_cards.csv"
IMAGE_DIR = BASE_DIR / "card_images"
IMAGE_DIR.mkdir(exist_ok=True)

# =========================
# SCHEMA DEFINITIONS
# =========================

PYQ_COLUMNS = [
    "id",
    "topic",
    "subject",
    "pyq_years",
    "trigger_line",
    "revision_count",
    "fail_count",
    "last_revised",
    "next_revision_date",
    "created_at",
    "schema_version"
]

CARD_COLUMNS = [
    "card_id",
    "topic_id",
    "card_title",
    "bullets",
    "external_url",
    "image_paths",
    "created_at",
    "schema_version"
]

DATE_COLUMNS_PYQ = [
    "last_revised",
    "next_revision_date",
    "created_at"
]

DATE_COLUMNS_CARD = [
    "created_at"
]

# =========================
# CORE LOAD / SAVE
# =========================

def load_csv(path: Path, columns: list, date_cols: list | None = None) -> pd.DataFrame:
    """
    Load CSV safely.
    - Heals missing columns
    - Parses date columns safely
    """
    if path.exists():
        df = pd.read_csv(path)
    else:
        df = pd.DataFrame(columns=columns)

    # Heal missing columns
    for col in columns:
        if col not in df.columns:
            df[col] = None

    # Parse date columns safely
    if date_cols:
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df[columns]


def save_csv(df: pd.DataFrame, path: Path) -> None:
    """Persist CSV without index."""
    df.to_csv(path, index=False)


# =========================
# SAFE ID GENERATION
# =========================

def safe_next_id(series: pd.Series) -> int:
    """
    Generate next integer ID safely.
    Handles:
    - Empty DataFrame
    - All-NaN columns
    """
    if series.empty or series.isna().all():
        return 1
    return int(series.max()) + 1


# =========================
# SPACED REPETITION LOGIC
# =========================

def compute_next_revision(revision_count: int) -> pd.Timestamp:
    """
    Spaced repetition schedule.
    """
    schedule_days = [0, 1, 3, 7, 15, 30]
    idx = min(revision_count, len(schedule_days) - 1)
    return pd.Timestamp.now() + timedelta(days=schedule_days[idx])


def is_due(df: pd.DataFrame) -> pd.Series:
    """
    Returns boolean mask of topics due for revision.
    """
    today = pd.Timestamp(date.today())
    return df["next_revision_date"].isna() | (df["next_revision_date"] <= today)


# =========================
# DATA ACCESS HELPERS
# =========================

def load_pyqs() -> pd.DataFrame:
    return load_csv(PYQ_FILE, PYQ_COLUMNS, DATE_COLUMNS_PYQ)


def load_cards() -> pd.DataFrame:
    return load_csv(CARD_FILE, CARD_COLUMNS, DATE_COLUMNS_CARD)


def save_pyqs(df: pd.DataFrame) -> None:
    save_csv(df, PYQ_FILE)


def save_cards(df: pd.DataFrame) -> None:
    save_csv(df, CARD_FILE)


# =========================
# INVARIANTS
# =========================

def card_exists_for_topic(cards_df: pd.DataFrame, topic_id: int) -> bool:
    """
    Enforces invariant:
    - One Study Card per Topic
    """
    return not cards_df[cards_df["topic_id"] == topic_id].empty


# =========================
# FACTORY HELPERS
# =========================

def new_pyq_row(
    topic: str,
    subject: str,
    trigger_line: str,
    pyq_years: str | None = None
) -> dict:
    """
    Create a new PYQ row with defaults.
    """
    return {
        "id": None,  # filled at insertion
        "topic": topic.strip(),
        "subject": subject,
        "pyq_years": pyq_years.strip() if pyq_years else "",
        "trigger_line": trigger_line.strip(),
        "revision_count": 0,
        "fail_count": 0,
        "last_revised": None,
        "next_revision_date": pd.Timestamp.now(),
        "created_at": pd.Timestamp.now(),
        "schema_version": DATA_VERSION
    }


def new_card_row(
    topic_id: int,
    bullets: str,
    card_title: str | None = None,
    external_url: str | None = None,
    image_paths: list[str] | None = None
) -> dict:
    """
    Create a new Study Card row.
    """
    return {
        "card_id": None,  # filled at insertion
        "topic_id": topic_id,
        "card_title": card_title.strip() if card_title else "",
        "bullets": bullets.strip(),
        "external_url": external_url.strip() if external_url else "",
        "image_paths": ";".join(image_paths) if image_paths else "",
        "created_at": pd.Timestamp.now(),
        "schema_version": DATA_VERSION
    }



def create_full_backup():
    buffer = BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        # CSV files
        if os.path.exists("pyq_topics.csv"):
            z.write("pyq_topics.csv")

        if os.path.exists("study_cards.csv"):
            z.write("study_cards.csv")

        # Images
        if os.path.exists("card_images"):
            for root, _, files in os.walk("card_images"):
                for f in files:
                    path = os.path.join(root, f)
                    z.write(path)

    buffer.seek(0)
    return buffer



def restore_full_backup(uploaded_file):
    # Clean existing data
    for f in ["pyq_topics.csv", "study_cards.csv"]:
        if os.path.exists(f):
            os.remove(f)

    if os.path.exists("card_images"):
        shutil.rmtree("card_images")

    # Extract uploaded zip
    with zipfile.ZipFile(uploaded_file, "r") as z:
        z.extractall(".")

    return True



def upsert_card(
    topic_id: int,
    card_title: str,
    bullets: str,
    image_paths: str = "",
    external_url: str = ""
):
    cards = load_cards()

    if not cards[cards.topic_id == topic_id].empty:
        cards.loc[cards.topic_id == topic_id, "card_title"] = card_title
        cards.loc[cards.topic_id == topic_id, "bullets"] = bullets
        cards.loc[cards.topic_id == topic_id, "image_paths"] = image_paths
        cards.loc[cards.topic_id == topic_id, "external_url"] = external_url

    else:
        new_row = {
            "card_id": safe_next_id(cards, "card_id"),
            "topic_id": topic_id,
            "card_title": card_title,
            "bullets": bullets,
            "image_paths": image_paths,
            "external_url": external_url,
            "created_at": date.today()
        }
        cards = pd.concat([cards, pd.DataFrame([new_row])], ignore_index=True)

    save_cards(cards)



def delete_card(topic_id: int):
    cards = load_cards()

    cards = cards[cards.topic_id != topic_id]

    save_cards(cards)