"""Configuration settings for the UI."""

# Thirdparty imports
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(override=True)


class Settings(BaseSettings):
    """UI Configuration settings."""

    # API Settings
    ML_API_BASE_URL: str = Field(default="http://localhost:32453/api/v1", description="Base URL of the ML API")
    BACKEND_BASE_URL: str = Field(default="http://localhost:8000", description="Base URL of the Django Backend")
    DJANGO_SUPERUSER_USERNAME: str = Field(default="", description="Username for backend token authentication")
    DJANGO_SUPERUSER_PASSWORD: str = Field(default="", description="Password for backend token authentication")

    # Page Configuration
    PAGE_TITLE: str = Field(default="Project Estimation Tool", description="Title of the application")
    PAGE_ICON: str = Field(default="🎓", description="Icon of the application")
    LAYOUT: str = Field(default="wide", description="Layout of the application")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")


settings = Settings()
