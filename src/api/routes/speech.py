"""FastAPI router for ElevenLabs speech endpoints."""

# Standart library imports
import base64
import os
import tempfile
from typing import Any

# Thirdparty imports
from fastapi import APIRouter, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

# Local imports
from src.api.schemas import (
    SpeechAudioFrameSchema,
    SpeechEndFrameSchema,
    SpeechSynthesisRequestSchema,
    SpeechStartFrameSchema,
    SpeechStreamEventSchema,
    SpeechTranscriptionResponseSchema,
    TechnicalInterviewChatRequestSchema,
)
from src.config.openai import openai_config
from src.core.logging import logger
from src.jobs.pipelines.chat import ensure_interview_not_finished, iter_technical_interview_events
from src.services.openai_speech import stream_tts_audio, transcribe_audio

router = APIRouter()


def _parse_speech_frame(payload: dict[str, Any]) -> SpeechStartFrameSchema | SpeechAudioFrameSchema | SpeechEndFrameSchema:
    """Parse a WebSocket speech frame payload.

    Parameters
    ----------
    payload : dict[str, Any]
        Incoming JSON payload.

    Returns
    -------
    SpeechStartFrameSchema | SpeechAudioFrameSchema | SpeechEndFrameSchema
        Parsed frame schema.
    """
    frame_type = payload.get("type")
    if frame_type == "start":
        return SpeechStartFrameSchema(**payload)
    if frame_type == "audio":
        return SpeechAudioFrameSchema(**payload)
    if frame_type == "end":
        return SpeechEndFrameSchema(**payload)
    raise ValueError("Unsupported frame type.")


async def _emit_event(websocket: WebSocket, event_type: str, data: dict[str, Any]) -> None:
    """Send a speech stream event to the client.

    Parameters
    ----------
    websocket : WebSocket
        Active WebSocket connection.
    event_type : str
        Event type label.
    data : dict[str, Any]
        Event payload.

    Returns
    -------
    None
        Sends a message over the WebSocket connection.
    """
    await websocket.send_json(SpeechStreamEventSchema(type=event_type, data=data).model_dump())


def _resolve_tts_media_type(output_format: str) -> str:
    """Resolve the HTTP media type for a TTS output format.

    Parameters
    ----------
    output_format : str
        ElevenLabs output format identifier.

    Returns
    -------
    str
        HTTP media type for the audio payload.
    """
    normalized_format = output_format.lower()
    if "mp3" in normalized_format:
        return "audio/mpeg"
    if "wav" in normalized_format or "pcm" in normalized_format:
        return "audio/wav"
    if "ogg" in normalized_format:
        return "audio/ogg"
    return "application/octet-stream"


def _resolve_tts_file_suffix(output_format: str) -> str:
    """Resolve a temporary file suffix for a TTS output format.

    Parameters
    ----------
    output_format : str
        ElevenLabs output format identifier.

    Returns
    -------
    str
        File suffix for the audio payload.
    """
    normalized_format = output_format.lower()
    if "mp3" in normalized_format:
        return ".mp3"
    if "wav" in normalized_format or "pcm" in normalized_format:
        return ".wav"
    if "ogg" in normalized_format:
        return ".ogg"
    return ".bin"


@router.post("/transcribe", response_model=SpeechTranscriptionResponseSchema)
async def transcribe_speech_audio(
    audio_file: UploadFile = File(...),
) -> SpeechTranscriptionResponseSchema:
    """
    Transcribe an uploaded audio file using OpenAI Whisper.

    Parameters
    ----------
    audio_file : UploadFile
        Uploaded audio file to transcribe.

    Returns
    -------
    SpeechTranscriptionResponseSchema
        Transcription response payload.
    """
    try:
        audio_bytes = await audio_file.read()
        text = transcribe_audio(audio_bytes=audio_bytes, file_name=audio_file.filename or "speech_input.wav")
        return SpeechTranscriptionResponseSchema(text=text)
    except Exception as exc:
        logger.error(f"Failed to transcribe audio: {exc}")
        raise HTTPException(status_code=500, detail="Failed to transcribe audio") from exc


@router.post("/tts")
async def synthesize_speech_audio(
    payload: SpeechSynthesisRequestSchema,
) -> FileResponse:
    """
    Synthesize speech audio from text using OpenAI TTS.

    Parameters
    ----------
    payload : SpeechSynthesisRequestSchema
        TTS request payload with the text to synthesize.

    Returns
    -------
    Response
        Complete audio payload.
    """
    try:
        output_format = openai_config.TTS_OUTPUT_FORMAT
        audio_bytes = b"".join(
            stream_tts_audio(
                text=payload.text,
                output_format=output_format,
            )
        )
        if not audio_bytes:
            raise ValueError("No audio data returned from TTS.")
        temp_suffix = _resolve_tts_file_suffix(output_format)
        with tempfile.NamedTemporaryFile(delete=False, suffix=temp_suffix) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        media_type = _resolve_tts_media_type(output_format)
        return FileResponse(
            path=temp_path,
            media_type=media_type,
            background=BackgroundTask(os.remove, temp_path),
        )
    except Exception as e:
        logger.error(f"Failed to synthesize speech: {e}")
        raise HTTPException(status_code=500, detail="Failed to synthesize speech") from e


@router.websocket("/stream")
async def speech_stream(websocket: WebSocket) -> None:
    """
    Stream speech input and optionally return synthesized speech.

    Parameters
    ----------
    websocket : WebSocket
        WebSocket connection for streaming speech input/output.

    Returns
    -------
    None
        Sends speech events over the WebSocket connection.
    """
    await websocket.accept()
    audio_chunks: list[bytes] = []
    start_frame: SpeechStartFrameSchema | None = None

    try:
        while True:
            payload = await websocket.receive_json()
            frame = _parse_speech_frame(payload)
            if isinstance(frame, SpeechStartFrameSchema):
                start_frame = frame
                await ensure_interview_not_finished(start_frame.session_id)
                await _emit_event(websocket, "info", {"message": "Speech session started."})
            elif isinstance(frame, SpeechAudioFrameSchema):
                if start_frame is None:
                    raise ValueError("Start frame must be sent before audio frames.")
                audio_chunks.append(base64.b64decode(frame.chunk))
            elif isinstance(frame, SpeechEndFrameSchema):
                if start_frame is None:
                    raise ValueError("Start frame must be sent before end frame.")
                audio_bytes = b"".join(audio_chunks)
                if not audio_bytes:
                    raise ValueError("No audio data received.")
                transcript = transcribe_audio(
                    audio_bytes=audio_bytes,
                    file_name=start_frame.audio_file_name,
                    file_format=start_frame.audio_format,
                    language_code=start_frame.language_code,
                )
                await _emit_event(websocket, "transcript", {"text": transcript})

                payload = TechnicalInterviewChatRequestSchema(
                    search_query_id=start_frame.search_query_id,
                    query=transcript,
                )
                response_text = ""
                async for event in iter_technical_interview_events(
                    session_id=start_frame.session_id,
                    payload=payload,
                ):
                    event_type = event.get("type")
                    data = event.get("data", {})
                    if event_type in {"reasoning", "answer"}:
                        token = data.get("token", "")
                        await _emit_event(websocket, event_type, {"token": token})
                        if event_type == "answer":
                            response_text += token
                    elif event_type == "complete":
                        response_text = data.get("response", response_text)
                        await _emit_event(websocket, "complete", data)
                    elif event_type == "error":
                        await _emit_event(websocket, "error", data)

                if start_frame.tts_enabled and response_text:
                    for chunk in stream_tts_audio(text=response_text):
                        await _emit_event(
                            websocket,
                            "audio_chunk",
                            {"chunk": base64.b64encode(chunk).decode("ascii")},
                        )
                await _emit_event(websocket, "info", {"message": "Speech session completed."})
                break
    except WebSocketDisconnect:
        logger.info("Speech WebSocket disconnected.")
    except Exception as exc:
        logger.error(f"Speech stream error: {exc}")
        await _emit_event(websocket, "error", {"error": "Speech stream error"})
        await websocket.close()
