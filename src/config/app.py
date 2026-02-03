"""App configuration for the Interview Preparation Platform."""

from pydantic import Field
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """Application configuration."""

    MAX_CHAT_HISTORY_LEN: int = Field(
        default=8,
        description="Maximum number of messages to keep in history before summarization.",
    )


app_config = AppConfig()
