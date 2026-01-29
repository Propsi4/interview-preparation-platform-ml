"""Chat page for interview interactions."""

# Standart library imports
import asyncio
from typing import Any, Dict, List, Optional

# Thirdparty imports
import httpx
import streamlit as st
import base64

# Local imports
from ui.api.client import InterviewAPIClient
from ui.components.chat import render_message
from ui.components.sidebar import render_sidebar
from ui.config.settings import settings
from ui.utils.state import (
    add_message,
    add_search_query,
    get_evaluated,
    get_interview_finished,
    get_messages,
    get_search_query_id,
    get_search_queries,
    get_session_id,
    init_session_state,
    set_interview_finished,
    set_messages,
    set_progress,
    set_evaluated,
    set_search_query_id,
    set_search_queries,
)

st.set_page_config(page_title=f"Chat - {settings.PAGE_TITLE}", page_icon="💬", layout=settings.LAYOUT)

init_session_state()
render_sidebar()

client = InterviewAPIClient()
session_id = get_session_id()

st.title("💬 Interview Chat")
st.caption(f"Session: `{session_id}`")


def _run_async(coro) -> Any:
    """
    Run an async coroutine in a dedicated event loop.

    Parameters
    ----------
    coro : Any
        Coroutine to execute.

    Returns
    -------
    Any
        Coroutine result.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _load_history_if_needed(target_session_id: str) -> None:
    """
    Load chat history when the session changes.

    Parameters
    ----------
    target_session_id : str
        Chat session identifier.

    Returns
    -------
    None
        Updates session state.
    """
    if st.session_state.get("last_loaded_session") == target_session_id:
        return
    try:
        history = _run_async(client.get_session_details(target_session_id))
        messages = history.get("messages", [])
        messages.sort(key=lambda item: item.get("id", 0))
        set_messages([{"role": msg.get("role"), "content": msg.get("content")} for msg in messages])
        set_search_query_id(history.get("search_query_id"))
        set_interview_finished(bool(history.get("interview_finished", False)))
        set_evaluated(bool(history.get("evaluated", False)))
        st.session_state.last_loaded_session = target_session_id
        st.session_state.evaluation_results = None
        if get_evaluated():
            try:
                results = _run_async(client.get_evaluation_results(target_session_id))
                st.session_state.evaluation_results = results
            except Exception:
                pass
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code in {404, 500}:
            set_messages([])
            set_interview_finished(False)
            set_evaluated(False)
            st.session_state.last_loaded_session = target_session_id
            st.session_state.evaluation_results = None
            st.info("No history yet for this session.")
        else:
            st.warning(f"Could not load session history: {exc}")
    except Exception as exc:
        st.warning(f"Could not load session history: {exc}")


def _load_search_queries() -> None:
    """
    Load search queries from the ML API.

    Returns
    -------
    None
        Updates search query cache.
    """
    try:
        queries = _run_async(client.list_search_queries())
        entries = [{"id": item["id"], "query": item["query"]} for item in queries]
        set_search_queries(entries)
    except Exception as exc:
        st.warning(f"Could not load search queries: {exc}")


def _load_evaluation_results_if_needed(target_session_id: str) -> None:
    """
    Load evaluation results if they are not cached or still pending.

    Parameters
    ----------
    target_session_id : str
        Chat session identifier.

    Returns
    -------
    None
        Updates evaluation results cache when available.
    """
    cached_results = st.session_state.get("evaluation_results")
    should_fetch = cached_results is None or (get_evaluated() and not cached_results)
    if not should_fetch:
        return
    try:
        results = _run_async(client.get_evaluation_results(target_session_id))
        st.session_state.evaluation_results = results
    except Exception:
        pass


_load_history_if_needed(session_id)
_load_search_queries()
_load_evaluation_results_if_needed(session_id)

st.subheader("Create Search Query")
search_query = st.text_input("Search query", placeholder="e.g. Data Scientist, Backend Engineer")

if st.button("Create Search Query", type="primary", key="create_search_query_btn"):
    if not search_query.strip():
        st.warning("Please enter a search query.")
    else:
        try:
            new_id = _run_async(client.create_search_query(search_query.strip()))
            set_search_query_id(new_id)
            add_search_query(new_id, search_query.strip())
            st.success(f"Search query created. ID: {new_id}")
        except Exception as exc:
            st.error(f"Failed to create search query: {exc}")

st.divider()

st.subheader("OR")
st.divider()

st.subheader("Select Existing Search Query")
current_search_query_id = get_search_query_id()
search_queries = get_search_queries()
selector_options = [entry["id"] for entry in search_queries]


def _is_existing_session(target_session_id: str) -> bool:
    """
    Check if the session exists on the ML side.

    Parameters
    ----------
    target_session_id : str
        Chat session identifier.

    Returns
    -------
    bool
        True if session exists in the backend.
    """
    try:
        sessions = _run_async(client.list_sessions())
        return any(
            session.get("session_id") == target_session_id and session.get("search_query_id") is not None
            for session in sessions
        )
    except Exception:
        return False


lock_search_query_selector = _is_existing_session(session_id)


def _format_search_query(option: int | str) -> str:
    entry = next((item for item in search_queries if item["id"] == option), None)
    if entry:
        return f"{entry.get('query', 'Search Query')} : {entry.get('id')}"
    return str(option)


selected_index = 0
if current_search_query_id in selector_options:
    selected_index = selector_options.index(current_search_query_id)

selected_option = st.selectbox(
    "Active search_query_id",
    options=selector_options,
    index=selected_index,
    format_func=_format_search_query,
    help="Select a search query to chat and evaluate.",
    disabled=lock_search_query_selector,
)

if selected_option:
    set_search_query_id(int(selected_option))

st.subheader("Scrape Progress")
if get_search_query_id() is None:
    st.info("Set a search_query_id to track progress.")
else:
    if st.button("Refresh Progress", key="refresh_progress"):
        try:
            progress = _run_async(client.get_progress(int(get_search_query_id())))
            set_progress(progress)
        except Exception as exc:
            st.error(f"Failed to fetch progress: {exc}")

    progress = st.session_state.get("progress", {})
    ratio = float(progress.get("progress", 0.0))
    st.progress(min(max(ratio, 0.0), 1.0))
    st.write(
        f"Processed {progress.get('processed_results', 0)} / "
        f"{progress.get('total_results') or 'unknown'} results"
    )

st.divider()

st.subheader("Chat")
for message in get_messages():
    render_message(message)

can_chat = get_search_query_id() is not None and not get_interview_finished()
if not can_chat:
    if get_search_query_id() is None:
        st.info("Set a search_query_id to start chatting.")
    elif get_interview_finished():
        st.info("Interview is finished. Start a new session to continue.")

if st.session_state.get("clear_chat_input", False):
    st.session_state["chat_input"] = ""
    st.session_state["clear_chat_input"] = False

if "voice_input_key" not in st.session_state:
    st.session_state.voice_input_key = 0

voice_expanded = st.session_state.get("voice_expanded", True)
with st.expander("Voice Message", expanded=voice_expanded):
    voice_enabled = st.checkbox("Enable voice response", value=True, disabled=not can_chat)
    input_key = f"voice_audio_input_{st.session_state.voice_input_key}"
    recorded_audio = st.audio_input("Record a voice message", disabled=not can_chat, key=input_key)

    if recorded_audio:
        st.session_state["voice_audio_bytes"] = recorded_audio.getvalue()
        st.session_state["voice_audio_name"] = recorded_audio.name or "streamlit_recording.wav"
        st.session_state["voice_audio_type"] = recorded_audio.type

    voice_audio_bytes = st.session_state.get("voice_audio_bytes")
    voice_audio_name = st.session_state.get("voice_audio_name", "streamlit_recording.wav")
    voice_audio_type = st.session_state.get("voice_audio_type", "audio/wav")
    if voice_audio_bytes:
        st.audio(voice_audio_bytes, format=voice_audio_type)

    voice_response_audio = st.session_state.get("voice_response_audio")
    if voice_response_audio:
        st.caption("Latest voice response")
        st.audio(voice_response_audio, format="audio/mp3")

    send_voice_clicked = st.button("Send voice message", disabled=not can_chat or not voice_audio_bytes)

if send_voice_clicked and voice_audio_bytes:
    try:
        with st.chat_message("assistant"):
            answer_slot = st.empty()

            async def stream_voice_response() -> Dict[str, Any]:
                """
                Stream voice response events and return the final payload.

                Returns
                -------
                Dict[str, Any]
                    Streamed transcript, response, and audio bytes.
                """
                transcript_text: Optional[str] = None
                answer_text = ""
                interview_finished = False
                audio_chunks: list[bytes] = []

                async for event in client.speech_stream_events(
                    session_id=session_id,
                    search_query_id=int(get_search_query_id()),
                    audio_bytes=voice_audio_bytes,
                    tts_enabled=voice_enabled,
                    audio_file_name=voice_audio_name,
                ):
                    event_type = event.get("type")
                    data = event.get("data", {})
                    if event_type == "transcript":
                        transcript_text = data.get("text")
                    elif event_type == "answer":
                        answer_text += data.get("token", "")
                        answer_slot.markdown(answer_text + "▌")
                    elif event_type == "complete":
                        answer_text = data.get("response", answer_text)
                        interview_finished = bool(data.get("interview_finished", False))
                        answer_slot.markdown(answer_text)
                    elif event_type == "audio_chunk":
                        chunk = data.get("chunk")
                        if chunk:
                            audio_chunks.append(base64.b64decode(chunk))
                    elif event_type == "error":
                        error_msg = data.get("error", "Speech stream error")
                        raise RuntimeError(error_msg)

                return {
                    "transcript": transcript_text,
                    "response": answer_text,
                    "audio_bytes": b"".join(audio_chunks) if audio_chunks else None,
                    "interview_finished": interview_finished,
                }

        result = _run_async(stream_voice_response())
        transcript = result.get("transcript") or "Voice message"
        response_text = result.get("response") or ""
        interview_finished = bool(result.get("interview_finished", False))

        add_message("user", transcript)
        add_message("assistant", response_text)
        set_interview_finished(interview_finished)

        audio_bytes = result.get("audio_bytes")
        if audio_bytes:
            st.session_state["voice_response_audio"] = audio_bytes

        st.session_state["voice_audio_bytes"] = None
        st.session_state["voice_audio_name"] = None
        st.session_state["voice_audio_type"] = None
        st.session_state["voice_expanded"] = False
        st.session_state.voice_input_key += 1
        st.rerun()
    except Exception as exc:
        st.error(f"Failed to send voice message: {exc}")

st.divider()

user_input = st.text_area("Your message", height=120, key="chat_input")
send_clicked = st.button("Send", type="primary", disabled=not can_chat)

if send_clicked and user_input.strip():
    add_message("user", user_input.strip())
    render_message({"role": "user", "content": user_input.strip()})

    with st.chat_message("assistant"):
        reasoning_slot = st.empty()
        answer_slot = st.empty()

        async def stream_response() -> Dict[str, Any]:
            """
            Stream a response and return the final payload.

            Returns
            -------
            Dict[str, Any]
                Response payload with text and interview completion.
            """
            reasoning_text = ""
            answer_text = ""
            interview_finished = False

            reasoning_placeholder = None

            async for event in client.chat_stream(
                session_id=session_id,
                search_query_id=int(get_search_query_id()),
                message=user_input.strip(),
            ):
                event_type = event.get("type")
                data = event.get("data", {})
                if event_type == "reasoning":
                    if reasoning_placeholder is None:
                        reasoning_expander = reasoning_slot.expander("Reasoning", expanded=True)
                        reasoning_placeholder = reasoning_expander.empty()
                    reasoning_text += data.get("token", "")
                    reasoning_placeholder.markdown(reasoning_text + "▌")
                elif event_type == "answer":
                    answer_text += data.get("token", "")
                    answer_slot.markdown(answer_text + "▌")
                elif event_type == "complete":
                    answer_text = data.get("response", answer_text)
                    interview_finished = bool(data.get("interview_finished", False))
                    answer_slot.markdown(answer_text)
                    if reasoning_placeholder:
                        reasoning_placeholder.markdown(reasoning_text)
                elif event_type == "error":
                    error_msg = data.get("error", "Streaming error")
                    raise RuntimeError(error_msg)

            return {"response": answer_text, "interview_finished": interview_finished}

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(stream_response())
            loop.close()
            add_message("assistant", result["response"])
            set_interview_finished(result["interview_finished"])
            st.session_state["clear_chat_input"] = True
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to stream response: {exc}")

st.divider()

st.subheader("Evaluate Interview")
evaluation_disabled = (
    not get_interview_finished()
    or get_search_query_id() is None
    or get_evaluated()
)
if not get_interview_finished():
    st.info("Evaluation is enabled once the interview is finished.")
elif get_evaluated():
    st.info("Evaluation already dispatched for this session.")

if st.button("Evaluate Interview", disabled=evaluation_disabled, key="evaluate_interview"):
    try:
        _run_async(client.evaluate_interview(session_id, int(get_search_query_id())))
        set_evaluated(True)
        results = _run_async(client.get_evaluation_results(session_id))
        st.session_state["evaluation_results"] = results
        st.success("Evaluation dispatched. Results loaded.")
    except Exception as exc:
        st.error(f"Failed to evaluate interview: {exc}")

evaluation_results: Optional[List[Dict[str, Any]]] = st.session_state.get("evaluation_results")
if evaluation_results:
    st.subheader("Evaluation Results")
    result_rows = [
        {
            "Score": item.get("score"),
            "Strong Sides": item.get("strong_sides"),
            "Weak Sides": item.get("weak_sides"),
            "Created": item.get("created_at"),
        }
        for item in evaluation_results
    ]
    st.dataframe(result_rows, width="content")
