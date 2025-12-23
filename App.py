import streamlit as st
import time

# =========================
# APP CONFIG (MUST BE FIRST)
# =========================
st.set_page_config(
    page_title="NEET PG Study System",
    page_icon="📘",
    layout="wide"
)

# ---- Import Modules ----
from pyq_capture import render_pyq_capture
from study_cards import render_study_cards
from revision_engine import render_revision_engine
from exam_modes import render_exam_modes
from dashboard import render_dashboard
import data_layer

# =========================
# SESSION STATE INIT (GLOBAL)
# =========================
st.session_state.setdefault("app_mode", "Study")
st.session_state.setdefault("current_view", "dashboard")
st.session_state.setdefault("focus_mode", False)
st.session_state.setdefault("edit_card", False)
st.session_state.setdefault("revision_filter", None)

# =========================
# GLOBAL MODE BAR
# =========================
def render_mode_bar():
    st.markdown("##### Mode")

    cols = st.columns(3)
    modes = ["Study", "Build", "Exam"]

    for col, mode in zip(cols, modes):
        if col.button(
            f"{'📘' if mode=='Study' else '🛠️' if mode=='Build' else '⚡'} {mode}",
            use_container_width=True,
            type="primary" if st.session_state.app_mode == mode else "secondary",
        ):
            # 🔑 Hard reset transient UI states
            st.session_state.focus_mode = False
            st.session_state.edit_card = False
            st.session_state.revision_filter = None

            st.session_state.app_mode = mode
            st.session_state.current_view = "dashboard"
            st.rerun()


# =========================
# BACKUP / RESTORE PAGES
# =========================
def render_backup_page():
    st.subheader("💾 Backup Data")
    st.info("Download a full backup of your data. Keep this file safe.")

    buffer = data_layer.create_full_backup()

    st.download_button(
        label="⬇️ Download Full Backup",
        data=buffer,
        file_name="neet_pg_backup.zip",
        mime="application/zip"
    )

    if st.button("← Back to Dashboard"):
        st.session_state.current_view = "dashboard"
        st.rerun()


def render_restore_page():
    st.subheader("♻️ Restore Data")
    st.warning("This will overwrite your current data.")

    uploaded = st.file_uploader(
        "Upload backup ZIP",
        type=["zip"]
    )

    if uploaded:
        if st.button("Restore Now"):
            data_layer.restore_full_backup(uploaded)
            st.success("Restore completed. Reloading app…")
            time.sleep(1)
            st.rerun()

    if st.button("← Back to Dashboard"):
        st.session_state.current_view = "dashboard"
        st.rerun()


# =========================
# MAIN LAYOUT
# =========================
st.markdown("#### 📘 NEET PG Study System")

if st.session_state.current_view not in ["backup", "restore"]:
    render_mode_bar()

st.markdown("---")

# =========================
# SIDEBAR (SECONDARY ONLY)
# =========================
st.sidebar.title("🗄️ Backup & Restore")

if st.sidebar.button("💾 Backup Data"):
    st.session_state.current_view = "backup"
    st.rerun()

if st.sidebar.button("⬆️ Restore Data"):
    st.session_state.current_view = "restore"
    st.rerun()


# =========================
# VIEW ROUTER
# =========================
view = st.session_state.current_view

if view == "dashboard":
    render_dashboard()

elif view == "add_pyq":
    render_pyq_capture()

elif view == "study_cards":
    render_study_cards()

elif view == "revision":
    st.session_state.revision_filter = None
    render_revision_engine()

elif view == "revision_weak":
    st.session_state.revision_filter = "weak"
    render_revision_engine()

elif view in ["rapid_review", "image_sprint"]:
    render_exam_modes()

elif view == "backup":
    render_backup_page()

elif view == "restore":
    render_restore_page()

else:
    st.session_state.current_view = "dashboard"
    st.rerun()