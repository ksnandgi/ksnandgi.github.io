"""
FINAL ASSEMBLY — NEET PG STUDY SYSTEM
Single-file Streamlit App

Modules:
0. data_layer.py
1. pyq_capture.py
2. study_cards.py
3. revision_engine.py
4. exam_modes.py
5. dashboard.py
"""

import streamlit as st

# ---- Import Modules ----
from pyq_capture import render_pyq_capture
from study_cards import render_study_cards
from revision_engine import render_revision_engine
from exam_modes import render_exam_modes
from dashboard import render_dashboard

# =========================
# APP CONFIG
# =========================

st.set_page_config(
    page_title="NEET PG Study System",
    page_icon="📘",
    layout="wide"
)

st.title("📘 NEET PG Study System")

def render_mode_bar():
    st.markdown("### Mode")

    cols = st.columns(3)

    modes = ["Study", "Build", "Exam"]

    for col, mode in zip(cols, modes):
        if col.button(
            f"{'📘' if mode=='Study' else '🛠️' if mode=='Build' else '⚡'} {mode}",
            use_container_width=True,
            type="primary" if st.session_state.app_mode == mode else "secondary",
        ):
            st.session_state.app_mode = mode


render_mode_bar()

st.markdown("---")


# =========================
# SESSION STATE
# =========================

st.session_state.setdefault("exam_day_mode", False)

# =========================
# GLOBAL APP MODE
# =========================
st.session_state.setdefault("app_mode", "Study")


# =========================
# SIDEBAR NAVIGATION
# =========================

st.sidebar.title("📘 NEET PG")

tabs = [
    "Dashboard",
    "Add PYQ",
    "Study Cards",
    "Revision",
    "Exam Modes"
]

active_tab = st.sidebar.radio("Navigate", tabs)

st.sidebar.markdown("---")

# Exam Day Mode indicator
if st.session_state.exam_day_mode:
    st.sidebar.warning("🧠 Exam Day Mode ON")

# =========================
# TAB ROUTING
# =========================

if active_tab == "Dashboard":
    render_dashboard()

elif active_tab == "Add PYQ":
    if st.session_state.exam_day_mode:
        st.warning("Exam Day Mode is ON. PYQ capture is disabled.")
    else:
        render_pyq_capture()

elif active_tab == "Study Cards":
    if st.session_state.exam_day_mode:
        st.warning("Exam Day Mode is ON. Editing Study Cards is disabled.")
    else:
        render_study_cards()

elif active_tab == "Revision":
    render_revision_engine()

elif active_tab == "Exam Modes":
    render_exam_modes()
