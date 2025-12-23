"""
Module 0 — Data Layer (Foundation)
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
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# SCHEMA DEFINITIONS
# =========================

PYQ_COLUMNS = [
    "id",
    "topic",
    "subject",
    "pyq_years",
    "trigger_line",
    "pyq_image_paths"
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

DATE_COLUMNS_PYQ = ["last_revised", "next_revision_date", "created_at"]
DATE_COLUMNS_CARD = ["created_at"]

# =========================
# CORE LOAD / SAVE
# =========================

def load_csv(path: Path, columns: list, date_cols: list | None = None) -> pd.DataFrame:
    if path.exists():
        df = pd.read_csv(path)
    else:
        df = pd.DataFrame(columns=columns)

    for col in columns:
        if col not in df.columns:
            df[col] = None

    if date_cols:
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df[columns]


def save_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)


# =========================
# SAFE ID GENERATION
# =========================

def safe_next_id(series: pd.Series) -> int:
    if series.empty or series.isna().all():
        return 1
    return int(series.max()) + 1


# =========================
# SPACED REPETITION
# =========================

def compute_next_revision(revision_count: int) -> pd.Timestamp:
    schedule_days = [0, 1, 3, 7, 15, 30]
    idx = min(int(revision_count), len(schedule_days) - 1)
    return pd.Timestamp.now() + timedelta(days=schedule_days[idx])


def is_due(df: pd.DataFrame) -> pd.Series:
    today = pd.Timestamp(date.today())
    return df["next_revision_date"].isna() | (df["next_revision_date"] <= today)


# =========================
# DATA ACCESS
# =========================

def load_pyqs() -> pd.DataFrame:
    df = load_csv(PYQ_FILE, PYQ_COLUMNS, DATE_COLUMNS_PYQ)

    # =========================
    # 🔧 SCHEMA HEALING (CRITICAL)
    # =========================

    # Case 1: Corrupted merged column (image paths accidentally merged)
    if "pyq_image_pathsrevision_count" in df.columns:
        # Salvage image paths
        df["pyq_image_paths"] = df["pyq_image_pathsrevision_count"]

        # Ensure revision_count exists separately
        if "revision_count" not in df.columns:
            df["revision_count"] = 0

        # Drop corrupted column
        df = df.drop(columns=["pyq_image_pathsrevision_count"])

    # Case 2: Missing image column
    if "pyq_image_paths" not in df.columns:
        df["pyq_image_paths"] = ""

    # Case 3: Missing revision_count
    if "revision_count" not in df.columns:
        df["revision_count"] = 0

    # Case 4: Missing fail_count (defensive)
    if "fail_count" not in df.columns:
        df["fail_count"] = 0

    # Ensure numeric safety
    df["revision_count"] = df["revision_count"].fillna(0).astype(int)
    df["fail_count"] = df["fail_count"].fillna(0).astype(int)

    return df


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
    return not cards_df[cards_df["topic_id"] == topic_id].empty


# =========================
# FACTORIES
# =========================

def new_pyq_row(
    topic: str,
    subject: str,
    trigger_line: str,
    pyq_years: str | None = None
) -> dict:
    return {
        "id": None,
        "topic": topic.strip(),
        "subject": subject,
        "pyq_years": pyq_years.strip() if pyq_years else "",
        "trigger_line": trigger_line.strip(),
        "pyq_image_paths":"",
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
    return {
        "card_id": None,
        "topic_id": topic_id,
        "card_title": card_title.strip() if card_title else "",
        "bullets": bullets.strip(),
        "external_url": external_url.strip() if external_url else "",
        "image_paths": ";".join(image_paths) if image_paths else "",
        "created_at": pd.Timestamp.now(),
        "schema_version": DATA_VERSION
    }


# =========================
# BACKUP / RESTORE
# =========================

def create_full_backup():
    buffer = BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        if PYQ_FILE.exists():
            z.write(PYQ_FILE)

        if CARD_FILE.exists():
            z.write(CARD_FILE)

        if IMAGE_DIR.exists():
            for root, _, files in os.walk(IMAGE_DIR):
                for f in files:
                    z.write(os.path.join(root, f))

    buffer.seek(0)
    return buffer


def restore_full_backup(uploaded_file):
    for f in [PYQ_FILE, CARD_FILE]:
        if f.exists():
            f.unlink()

    if IMAGE_DIR.exists():
        shutil.rmtree(IMAGE_DIR)

    with zipfile.ZipFile(uploaded_file, "r") as z:
        z.extractall(".")

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    return True


# =========================
# CARD UPSERT / DELETE
# =========================

def upsert_card(
    topic_id: int,
    card_title: str,
    bullets: str,
    image_paths: str = "",
    external_url: str = ""
):
    cards = load_cards()

    if not cards[cards.topic_id == topic_id].empty:
        cards.loc[cards.topic_id == topic_id, [
            "card_title",
            "bullets",
            "image_paths",
            "external_url"
        ]] = [card_title, bullets, image_paths, external_url]

    else:
        new_row = {
            "card_id": safe_next_id(cards["card_id"]),
            "topic_id": topic_id,
            "card_title": card_title,
            "bullets": bullets,
            "image_paths": image_paths,
            "external_url": external_url,
            "created_at": pd.Timestamp.now(),
            "schema_version": DATA_VERSION
        }
        cards = pd.concat([cards, pd.DataFrame([new_row])], ignore_index=True)

    save_cards(cards)


def delete_card(topic_id: int):
    cards = load_cards()
    cards = cards[cards.topic_id != topic_id]
    save_cards(cards)