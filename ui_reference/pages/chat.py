"""Chat page implementation."""

# Standart library imports
import asyncio
import json
from typing import Any, Dict, List

# Thirdparty imports
import streamlit as st

# Local imports
from ui.api.client import PETClient
from ui.components.chat import render_message
from ui.components.sidebar import render_sidebar
from ui.config.settings import settings
from ui.utils.state import (
    add_message,
    get_messages,
    get_session_id,
    get_session_price,
    init_session_state,
    set_messages,
    set_session_price,
)

st.set_page_config(page_title=f"Chat - {settings.PAGE_TITLE}", page_icon="💬", layout=settings.LAYOUT)

# Initialize state and client
init_session_state()
client = PETClient()

# Sidebar
render_sidebar()

# Main content
st.title("💬 Chat with Project Estimation Tool")
st.caption(f"Session cost: ${get_session_price():.4f}")

session_id = get_session_id()

# --- Specialist Profile Insertion Logic ---


@st.cache_data(ttl=300)
def get_profiles():
    """Fetch specialist profiles from backend."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        profiles = loop.run_until_complete(client.get_specialist_profiles())
        loop.close()
        # Extra safeguard to ensure IDs are stripped even if cached data persists.
        return PETClient._strip_ids(profiles)
    except Exception as e:
        st.error(f"Failed to fetch profiles: {e}")
        return []


with st.expander("Insert Specialist Profile"):

    profiles = get_profiles()

    if profiles:
        # Create a mapping for selection
        profile_options = {
            f"{p.get('name')} | {p.get('area_of_expertise', {}).get('name', 'Unknown')} | {p.get('years_experience', 0)} years": p
            for p in profiles
        }
        selected_option = st.selectbox("Select a Profile", options=list(profile_options.keys()))

        if st.button("Insert Profile JSON"):
            if selected_option:
                profile_data = profile_options[selected_option]
                # Insert into session state to populate the text area
                st.session_state["pending_insert"] = json.dumps(profile_data, indent=2)
                st.rerun()
    else:
        st.info("No specialist profiles found (or backend unreachable).")

# Handle pending insert
if "pending_insert" in st.session_state:
    st.session_state["chat_input_area"] = st.session_state["pending_insert"]
    del st.session_state["pending_insert"]

# --- Chat History Loading ---


def load_history_if_needed(session_key: str) -> None:
    """Load chat history once per session."""
    if st.session_state.get("last_loaded_session") == session_key:
        return

    messages: List[Dict[str, Any]] = []
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        history = loop.run_until_complete(client.get_history(session_key))
        messages = history.get("messages", [])
        set_session_price(history.get("price", 0.0))

        # Sort messages by ID to ensure correct order
        messages.sort(key=lambda x: x.get("id", 0))
    except Exception as exc:
        st.warning(f"Could not load history for session {session_key}: {exc}")
        return
    finally:
        loop.close()

    set_messages(messages)
    st.session_state.last_loaded_session = session_key
    st.rerun()


load_history_if_needed(session_id)

# Display chat history
messages = get_messages()
for msg in messages:
    render_message(msg)

# --- Chat Input ---

# Clear text area on rerun if requested
if st.session_state.get("clear_chat_input", False):
    st.session_state["chat_input_area"] = ""
    st.session_state["clear_chat_input"] = False

# Text Area for input (allows multi-line JSON)
prompt = st.text_area("Your message", key="chat_input_area", height=150)

if st.button("Send", type="primary"):
    user_input = prompt

    if user_input.strip():
        # Request clearing the text area on next rerun
        st.session_state["clear_chat_input"] = True

        # Add user message
        add_message("user", user_input)
        render_message({"role": "user", "content": user_input})

        # Get assistant response
        with st.chat_message("assistant"):
            # 1. Initialize UI Placeholders (to maintain order: Status -> Reasoning -> Answer)
            status_slot = st.empty()
            reasoning_slot = st.empty()
            answer_placeholder = st.empty()

            async def stream_response() -> Dict[str, Any]:
                """Stream and assemble the response."""
                # Containers are initialized lazily
                status_container = None
                reasoning_placeholder = None

                result_text = ""
                reasoning_text = ""
                final_attachments = []

                async for event in client.chat_stream(
                    message=user_input,
                    session_id=session_id,
                ):
                    event_type = event.get("type")
                    data = event.get("data", {})

                    if event_type == "intermediate_steps":
                        if status_container is None:
                            status_container = status_slot.status("Thinking...", expanded=True)

                        status = data.get("status", "")
                        if status:
                            status_container.write(status)

                    elif event_type == "reasoning":
                        if reasoning_placeholder is None:
                            reasoning_expander = reasoning_slot.expander("Reasoning", expanded=True)
                            reasoning_placeholder = reasoning_expander.empty()

                        token = data.get("token", "")
                        reasoning_text += token
                        reasoning_placeholder.markdown(reasoning_text + "▌")

                    elif event_type == "answer":
                        token = data.get("token", "")
                        result_text += token
                        answer_placeholder.markdown(result_text + "▌")

                    elif event_type == "complete":
                        final_response = data.get("response", result_text)
                        final_attachments = data.get("attachments", [])
                        result_text = final_response

                        # Finalize UI
                        if status_container:
                            status_container.update(label="Complete", state="complete", expanded=False)
                        if reasoning_placeholder:
                            reasoning_placeholder.markdown(reasoning_text)
                        answer_placeholder.markdown(result_text)

                    elif event_type == "error":
                        error_msg = data.get("error", "Streaming error")
                        if status_container is None:
                            status_container = status_slot.status("Error", state="error", expanded=True)
                        else:
                            status_container.update(label="Error", state="error", expanded=True)
                        raise RuntimeError(error_msg)

                updated_price = await client.get_session_price(session_id)
                set_session_price(updated_price)
                return {"content": result_text, "attachments": final_attachments}

            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                final_result = loop.run_until_complete(stream_response())
                loop.close()

                # Add assistant message to history with attachments
                add_message("assistant", final_result["content"], attachments=final_result["attachments"])

                # Rerun to clear the text area visually and update history fully
                st.rerun()

            except Exception as e:
                st.error(f"Error: {str(e)}")
