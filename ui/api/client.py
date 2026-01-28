"""API Client for communicating with the ML service."""

# Standart library imports
import base64
import json
from typing import Any, AsyncGenerator, Dict, List, Optional
from urllib.parse import urlparse, urlunparse

# Thirdparty imports
import httpx
import websockets

# Local imports
from ui.config.settings import settings


class InterviewAPIClient:
    """Client for the Interview Preparation Platform ML API."""

    def __init__(self) -> None:
        """Initialize the client."""
        self.ml_base_url = settings.ML_API_BASE_URL.rstrip("/")
        self.timeout: Optional[float] = None

    async def create_search_query(self, search_query: str) -> int:
        """
        Create a new search query scraping task.

        Parameters
        ----------
        search_query : str
            Search query string for scraping.

        Returns
        -------
        int
            Created search query identifier.
        """
        url = f"{self.ml_base_url}/scrapers/scrape"
        payload = {"search_query": search_query}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return int(data["search_query_id"])

    async def get_progress(self, search_query_id: int) -> Dict[str, Any]:
        """
        Get scraping progress for a search query.

        Parameters
        ----------
        search_query_id : int
            Search query identifier.

        Returns
        -------
        Dict[str, Any]
            Progress response payload.
        """
        url = f"{self.ml_base_url}/scrapers/progress/{search_query_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def list_search_queries(self) -> List[Dict[str, Any]]:
        """
        List all search queries.

        Returns
        -------
        List[Dict[str, Any]]
            Search query list payload.
        """
        url = f"{self.ml_base_url}/scrapers/queries"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all chat sessions with metadata.

        Returns
        -------
        List[Dict[str, Any]]
            Session list payload.
        """
        url = f"{self.ml_base_url}/conversation_history/sessions"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def get_session_details(self, session_id: str) -> Dict[str, Any]:
        """
        Get session details and messages.

        Parameters
        ----------
        session_id : str
            Chat session identifier.

        Returns
        -------
        Dict[str, Any]
            Session details payload.
        """
        url = f"{self.ml_base_url}/conversation_history/session/{session_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def rename_session(self, session_id: str, new_title: str) -> Dict[str, Any]:
        """
        Rename a chat session.

        Parameters
        ----------
        session_id : str
            Chat session identifier.
        new_title : str
            New session title.

        Returns
        -------
        Dict[str, Any]
            Status response payload.
        """
        url = f"{self.ml_base_url}/conversation_history/session/{session_id}/title"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.patch(url, params={"new_title": new_title})
            response.raise_for_status()
            return response.json()

    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        Delete a chat session and its messages.

        Parameters
        ----------
        session_id : str
            Chat session identifier.

        Returns
        -------
        Dict[str, Any]
            Status response payload.
        """
        url = f"{self.ml_base_url}/conversation_history/session/{session_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(url)
            response.raise_for_status()
            return response.json()

    async def chat(self, session_id: str, search_query_id: int, message: str) -> Dict[str, Any]:
        """
        Send a chat message to the interview agent.

        Parameters
        ----------
        session_id : str
            Chat session identifier.
        search_query_id : int
            Search query identifier.
        message : str
            User message.

        Returns
        -------
        Dict[str, Any]
            Response payload containing interview state.
        """
        url = f"{self.ml_base_url}/chat/interview/{session_id}"
        payload = {"search_query_id": search_query_id, "query": message}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def chat_stream(
        self,
        session_id: str,
        search_query_id: int,
        message: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream chat response events from the interview agent.

        Parameters
        ----------
        session_id : str
            Chat session identifier.
        search_query_id : int
            Search query identifier.
        message : str
            User message.

        Yields
        ------
        Dict[str, Any]
            Stream event payload.
        """
        url = f"{self.ml_base_url}/chat/interview/{session_id}/stream"
        payload = {"search_query_id": search_query_id, "query": message}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    payload_str = line[5:].strip()
                    if not payload_str:
                        continue
                    try:
                        event = json.loads(payload_str)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(event, dict):
                        yield event

    async def speech_stream(
        self,
        session_id: str,
        search_query_id: int,
        audio_bytes: bytes,
        tts_enabled: bool = True,
        audio_format: Optional[str] = None,
        audio_file_name: str = "speech_input.wav",
        language_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Stream speech input and return transcript, response, and audio bytes.

        Parameters
        ----------
        session_id : str
            Chat session identifier.
        search_query_id : int
            Search query identifier.
        audio_bytes : bytes
            Recorded audio payload.
        tts_enabled : bool
            Whether to request TTS audio output.
        audio_format : Optional[str]
            Optional format hint for STT (e.g., 'pcm_s16le_16').
        audio_file_name : str
            File name hint for STT.
        language_code : Optional[str]
            Optional ISO-639 language code for STT.

        Returns
        -------
        Dict[str, Any]
            Transcript, response text, and synthesized audio bytes.
        """
        transcript: Optional[str] = None
        response_text = ""
        interview_finished = False
        audio_chunks: list[bytes] = []

        async for payload in self.speech_stream_events(
            session_id=session_id,
            search_query_id=search_query_id,
            audio_bytes=audio_bytes,
            tts_enabled=tts_enabled,
            audio_format=audio_format,
            audio_file_name=audio_file_name,
            language_code=language_code,
        ):
            event_type = payload.get("type")
            data = payload.get("data", {})

            if event_type == "transcript":
                transcript = data.get("text")
            elif event_type == "answer":
                response_text += data.get("token", "")
            elif event_type == "complete":
                response_text = data.get("response", response_text)
                interview_finished = bool(data.get("interview_finished", False))
            elif event_type == "audio_chunk":
                chunk = data.get("chunk")
                if chunk:
                    audio_chunks.append(base64.b64decode(chunk))

        return {
            "transcript": transcript,
            "response": response_text,
            "audio_bytes": b"".join(audio_chunks) if audio_chunks else None,
            "interview_finished": interview_finished,
        }

    async def speech_stream_events(
        self,
        session_id: str,
        search_query_id: int,
        audio_bytes: bytes,
        tts_enabled: bool = True,
        audio_format: Optional[str] = None,
        audio_file_name: str = "speech_input.wav",
        language_code: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream speech events from the WebSocket endpoint.

        Parameters
        ----------
        session_id : str
            Chat session identifier.
        search_query_id : int
            Search query identifier.
        audio_bytes : bytes
            Recorded audio payload.
        tts_enabled : bool
            Whether to request TTS audio output.
        audio_format : Optional[str]
            Optional format hint for STT (e.g., 'pcm_s16le_16').
        audio_file_name : str
            File name hint for STT.
        language_code : Optional[str]
            Optional ISO-639 language code for STT.

        Yields
        ------
        Dict[str, Any]
            Speech stream event payload.
        """
        ws_url = self._build_speech_ws_url()
        start_frame = {
            "type": "start",
            "session_id": session_id,
            "search_query_id": search_query_id,
            "tts_enabled": tts_enabled,
            "audio_format": audio_format,
            "audio_file_name": audio_file_name,
            "language_code": language_code,
        }
        audio_frame = {
            "type": "audio",
            "chunk": base64.b64encode(audio_bytes).decode("ascii"),
        }
        end_frame = {"type": "end"}

        async with websockets.connect(ws_url, ping_interval=None) as websocket:
            await websocket.send(json.dumps(start_frame))
            await websocket.send(json.dumps(audio_frame))
            await websocket.send(json.dumps(end_frame))

            while True:
                try:
                    message = await websocket.recv()
                except websockets.ConnectionClosed:
                    break
                payload = json.loads(message)
                event_type = payload.get("type")
                data = payload.get("data", {})

                if event_type == "info" and data.get("message") == "Speech session completed.":
                    break
                if event_type == "error":
                    raise RuntimeError(data.get("error", "Speech stream error"))
                if isinstance(payload, dict):
                    yield payload

    def _build_speech_ws_url(self) -> str:
        """
        Build the speech WebSocket URL from the ML API base URL.

        Returns
        -------
        str
            WebSocket endpoint URL.
        """
        parsed = urlparse(self.ml_base_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        base_path = parsed.path.rstrip("/")
        speech_path = f"{base_path}/speech/stream"
        return urlunparse((scheme, parsed.netloc, speech_path, "", "", ""))

    async def evaluate_interview(self, session_id: str, search_query_id: int) -> Dict[str, Any]:
        """
        Dispatch an interview evaluation job.

        Parameters
        ----------
        session_id : str
            Chat session identifier.
        search_query_id : int
            Search query identifier.

        Returns
        -------
        Dict[str, Any]
            Dispatch response payload.
        """
        url = f"{self.ml_base_url}/evaluation/evaluate"
        payload = {"chat_session_id": session_id, "search_query_id": search_query_id}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def get_evaluation_results(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Fetch evaluation results for a session.

        Parameters
        ----------
        session_id : str
            Chat session identifier.

        Returns
        -------
        List[Dict[str, Any]]
            Evaluation results payload.
        """
        url = f"{self.ml_base_url}/evaluation/session/{session_id}/results"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def check_health(self) -> bool:
        """
        Check if the ML API is healthy.

        Returns
        -------
        bool
            True if healthy, False otherwise.
        """
        url = f"{self.ml_base_url}/health"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False
