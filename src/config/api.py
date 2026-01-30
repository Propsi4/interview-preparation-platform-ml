"""Configuration module for the Interview Preparation Platform."""

# Standart library imports
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv(override=True)


class APIConfig(BaseSettings):
    """API configuration for the interview preparation platform."""

    API_HOST: str = Field(
        default="0.0.0.0",
        description="Host address for the API server of the interview preparation platform",
    )
    API_PORT: int = Field(
        default=8080,
        description="Port for the API server of the interview preparation platform",
    )
    DEBUG: bool = Field(
        default=False,
        description="Debug mode for the API server of the interview preparation platform",
    )
    RELOAD_ON_CODE_CHANGE: bool = Field(
        default=False,
        description="Reload the API server on code change",
    )
    CORS_ALLOWED_ORIGINS: list[str] = Field(
        default=["*"],
        description="List of allowed CORS origins",
    )


api_config = APIConfig()
