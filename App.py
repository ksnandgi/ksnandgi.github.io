import streamlit as st

# ---- Import Modules ----
from pyq_capture import render_pyq_capture
from study_cards import render_study_cards
from revision_engine import render_revision_engine
from exam_modes import render_exam_modes
from dashboard import render_dashboard

# =========================
# SESSION STATE
# =========================
st.session_state.setdefault("exam_day_mode", False)
st.session_state.setdefault("app_mode", "Study")

# =========================
# GLOBAL MODE BAR
# =========================
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

# =========================
# APP CONFIG
# =========================
st.set_page_config(
    page_title="NEET PG Study System",
    page_icon="📘",
    layout="wide"
)

# =========================
# MAIN LAYOUT
# =========================
st.title("📘 NEET PG Study System")

render_mode_bar()

st.markdown("---")

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

# =========================
# TAB ROUTING
# =========================
if active_tab == "Dashboard":
    render_dashboard()
elif active_tab == "Add PYQ":
    render_pyq_capture()
elif active_tab == "Study Cards":
    render_study_cards()
elif active_tab == "Revision":
    if st.session_state.pop("_force_revision", False):
    render_revision_engine()
    return
elif active_tab == "Exam Modes":
    render_exam_modes()
