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

def render_backup_page():
    st.subheader("💾 Backup Data")

    st.info("Download a full backup of your data. Keep this file safe.")

    if st.button("⬇️ Download Full Backup"):
        # call your existing backup logic here
        st.success("Backup prepared. Download should start.")

    if st.button("⬅ Back to Dashboard"):
        st.session_state.current_view = "dashboard"


def render_restore_page():
    st.subheader("⬆️ Restore Data")

    st.warning("Restoring will overwrite existing data.")

    file = st.file_uploader("Upload backup ZIP", type=["zip"])

    confirm = st.checkbox("I understand this will overwrite current data")

    if file and confirm and st.button("Restore Backup"):
        # call restore logic here
        st.success("Backup restored successfully.")
        st.session_state.current_view = "dashboard"

    if st.button("⬅ Back to Dashboard"):
        st.session_state.current_view = "dashboard"


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
    st.session_state.current_view = "restore"

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