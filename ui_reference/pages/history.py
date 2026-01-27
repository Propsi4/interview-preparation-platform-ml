"""Chat history page."""

# Standart library imports
import asyncio

# Thirdparty imports
import streamlit as st

# Local imports
from ui.api.client import PETClient
from ui.components.sidebar import render_sidebar
from ui.config.settings import settings
from ui.utils.state import get_session_id, init_session_state, set_session_id

st.set_page_config(page_title=f"History - {settings.PAGE_TITLE}", page_icon="📜", layout=settings.LAYOUT)

init_session_state()
client = PETClient()
render_sidebar()

st.title("📜 Chat History")

current_session = get_session_id()
st.info(f"Current Session: `{current_session}`")

if st.button("Clear History", type="primary"):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(client.delete_history(current_session))
        loop.close()
        st.success("History cleared!")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to clear history: {str(e)}")

st.divider()

st.subheader("Manage Other Sessions")
target_session = st.text_input("Enter Session ID to View/Manage")

if target_session:
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Switch to this Session"):
            set_session_id(target_session)
            st.success(f"Switched to session {target_session}")
            st.rerun()

    with c2:
        if st.button(f"Delete Session {target_session}", type="primary"):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(client.delete_history(target_session))
                loop.close()
                st.success(f"Session {target_session} deleted!")
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.divider()

st.subheader("All Conversations")
conversations_container = st.empty()

try:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    conversations = loop.run_until_complete(client.list_conversations())
    loop.close()

    if conversations:
        # Display as a simple table
        conv_rows = []
        for conv in conversations:
            conv_rows.append(
                {
                    "Session ID": conv.get("session_id", ""),
                    "Title": conv.get("title", "Untitled"),
                    "Messages": conv.get("message_count", 0),
                    "Updated": conv.get("updated_at", ""),
                }
            )
        conversations_container.dataframe(conv_rows, width="content")

        # Selection controls
        st.write("Select a session to switch, rename, or delete:")
        session_ids = [c.get("session_id") for c in conversations]
        selected_session = st.selectbox(
            "Session",
            session_ids,
            format_func=lambda x: next((c.get("title") for c in conversations if c.get("session_id") == x), x),
        )

        # Rename input
        current_title = next((c.get("title") for c in conversations if c.get("session_id") == selected_session), "")
        new_title = st.text_input("New Title", value=current_title)

        c3, c4, c5 = st.columns(3)
        with c3:
            if st.button("Switch to Session", key="switch_list_session"):
                set_session_id(selected_session)
                st.success(f"Switched to session {selected_session}")
                st.rerun()

        with c4:
            if st.button("Rename Session", key="rename_list_session"):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(client.rename_session(selected_session, new_title))
                    loop.close()
                    st.success(f"Session {selected_session} renamed!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error renaming session: {str(e)}")

        with c5:
            if st.button("Delete Session", key="delete_list_session"):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(client.delete_history(selected_session))
                    loop.close()
                    st.success(f"Session {selected_session} deleted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting session: {str(e)}")
    else:
        st.info("No conversations found.")
except Exception as e:
    st.error(f"Failed to list conversations: {str(e)}")
