"""API Client for communicating with the backend."""

# Standart library imports
import json
from typing import Any, AsyncGenerator, Dict, List

# Thirdparty imports
import httpx

# Local imports
from ui.config.settings import settings
from ui.utils.auth import fetch_backend_token


class PETClient:
    """Client for the Project Estimation Tool API."""

    def __init__(self):
        """Initialize the client."""
        self.ml_base_url = settings.ML_API_BASE_URL
        self.backend_base_url = settings.BACKEND_BASE_URL
        self.timeout = None

    async def chat_stream(
        self,
        message: str,
        session_id: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream chat response from the orchestrator.

        Parameters
        ----------
        message : str
            The user's message.
        session_id : str
            The session ID.

        Yields
        ------
        Dict[str, Any]
            Chunks of the response or final payload.
        """
        url = f"{self.ml_base_url}/inference/chat/stream/"
        payload = {
            "message": message,
            "session_id": session_id,
        }

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
                        if isinstance(event, dict):
                            yield event
                    except json.JSONDecodeError:
                        continue

    async def get_history(self, session_id: str) -> Dict[str, Any]:
        """
        Get chat history for a session.

        Parameters
        ----------
        session_id : str
            The session ID.

        Returns
        -------
        Dict[str, Any]
            The chat history.
        """
        url = f"{self.ml_base_url}/management/details/{session_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def get_session_price(self, session_id: str) -> float:
        """
        Get the current price for a session.

        Fetches the total accumulated cost for the given chat session.

        Parameters
        ----------
        session_id : str
            The session ID.

        Returns
        -------
        float
            The session price.
        """
        url = f"{self.ml_base_url}/management/price/{session_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            payload = response.json()
            return float(payload.get("price", 0.0))

    async def list_conversations(self) -> List[Dict[str, Any]]:
        """
        List all conversation sessions.

        Returns
        -------
        List[Dict[str, Any]]
            List of conversations with metadata.
        """
        url = f"{self.ml_base_url}/management/list"
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
            The session ID.
        new_title : str
            The new title.

        Returns
        -------
        Dict[str, Any]
            Response from the API.
        """
        url = f"{self.ml_base_url}/management/{session_id}/title"
        payload = {"title": new_title}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.patch(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def delete_history(self, session_id: str) -> Dict[str, Any]:
        """
        Delete chat history for a session.

        Parameters
        ----------
        session_id : str
            The session ID.

        Returns
        -------
        Dict[str, Any]
            Response from the API.
        """
        url = f"{self.ml_base_url}/management/{session_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(url)
            response.raise_for_status()
            return response.json()

    async def get_specialist_profiles(self) -> List[Dict[str, Any]]:
        """
        Retrieve all available Assignees (Specialist Profiles).

        Returns
        -------
        List[Dict[str, Any]]
            List of specialist profiles without database IDs.
        """
        url = f"{self.backend_base_url}/api/specialist_profiles/"
        token = await fetch_backend_token(
            settings.DJANGO_SUPERUSER_USERNAME,
            settings.DJANGO_SUPERUSER_PASSWORD,
        )
        headers = {"Authorization": f"Token {token}"} if token else {}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            profiles: List[Dict[str, Any]] = response.json()
            return self._parse_specialist_profiles(profiles)

    @staticmethod
    def _strip_ids(payload: Any) -> Any:
        """
        Recursively remove ``id`` keys from dictionaries or lists.

        Parameters
        ----------
        payload : Any
            JSON-like structure returned from the backend.

        Returns
        -------
        Any
            Same structure with all ``id`` keys removed.
        """
        if isinstance(payload, list):
            return [PETClient._strip_ids(item) for item in payload]
        if isinstance(payload, dict):
            return {key: PETClient._strip_ids(value) for key, value in payload.items() if key != "id"}
        return payload

    @staticmethod
    def _parse_specialist_profiles(profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parse the specialist profiles.

        Parameters
        ----------
        profiles : List[Dict[str, Any]]
            JSON-like structure returned from the backend.
        """
        parsed_profiles = []
        for profile in profiles:
            profile["past_projects"] = [project["description"] for project in profile["past_projects"]]
            parsed_profiles.append(profile)
        return parsed_profiles

    async def check_health(self) -> bool:
        """
        Check if the API is healthy.

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
