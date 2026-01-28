"""Configuration settings for the Streamlit UI."""

# Thirdparty imports
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

load_dotenv(override=True)


class Settings(BaseSettings):
    """UI Configuration settings."""

    # API Settings
    ML_API_BASE_URL: str = Field(default="http://localhost:32453/api/v1", description="Base URL of the ML API")

    HOST: Optional[str] = Field(default=None, description="Host of the application", alias="STREAMLIT_HOST")
    PORT: int = Field(default=8501, description="Port of the application", alias="STREAMLIT_PORT")

    # Page Configuration
    PAGE_TITLE: str = Field(default="Interview Preparation Platform", description="Title of the application")
    PAGE_ICON: str = Field(default="🎓", description="Icon of the application")
    LAYOUT: str = Field(default="wide", description="Layout of the application")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")


settings = Settings()
