"""API Client for communicating with the ML service."""

# Standart library imports
import json
from typing import Any, AsyncGenerator, Dict, List, Optional

# Thirdparty imports
import httpx

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
