"""Authentication utilities for backend access."""

# Thirdparty imports
import httpx

# Local imports
from ui.config.settings import settings


async def fetch_backend_token(username: str, password: str) -> str:
    """
    Retrieve a DRF token from the backend.

    Parameters
    ----------
    username : str
        Backend username for token auth.
    password : str
        Backend password for token auth.

    Returns
    -------
    str
        Token string issued by the backend.

    Raises
    ------
    RuntimeError
        If credentials are missing or token retrieval fails.
    """
    if not username or not password:
        raise RuntimeError("Backend credentials are not configured.")

    url = f"{settings.BACKEND_BASE_URL}/api/token_auth/"
    payload = {"username": username, "password": password}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to obtain token: {response.text}")
        data = response.json()
        token = data.get("token")
        if not token:
            raise RuntimeError("Token not found in backend response.")
        return token
