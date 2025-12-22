import streamlit as st

# ---- Import Modules ----
from pyq_capture import render_pyq_capture
from study_cards import render_study_cards
from revision_engine import render_revision_engine
from exam_modes import render_exam_modes
from dashboard import render_dashboard

# =========================
# SESSION STATE INIT (GLOBAL)
# =========================
st.session_state.setdefault("app_mode", "Study")
st.session_state.setdefault("current_view", "dashboard")

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

if st.session_state.current_view not in ["backup", "restore"]:
    render_mode_bar()

st.markdown("---")

# =========================
# SIDEBAR NAVIGATION
# =========================
st.sidebar.title("🗄️ Backup & Restore")

if st.sidebar.button("💾 Backup Data"):
    st.session_state.current_view = "backup"

if st.sidebar.button("⬆️ Restore Data"):
    st.session_state.current.view = "restore"

view = st.session_state.current_view

if view == "dashboard":
    render_dashboard()

elif view == "add_pyq":
    render_pyq_capture()

elif view == "study_cards":
    render_study_cards()

elif view == "revision":
    render_revision_engine()

elif view == "exam":
    render_exam_modes()

elif view == "backup":
    render_backup_page()   # new page

elif view == "restore":
    render_restore_page()  # new page