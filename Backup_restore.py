




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