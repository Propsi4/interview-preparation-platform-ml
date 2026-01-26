"""Configuration module for the Interview Preparation Platform."""

# Standart library imports
from dotenv import load_dotenv
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings

load_dotenv(override=True)


class OpenAIConfig(BaseSettings):
    """OpenAI configuration for the interview preparation platform."""

    API_KEY: str = Field(
        ...,
        description="OpenAI API key for authentication",
        alias="OPENAI_API_KEY",
    )
    EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="OpenAI model to be used for the interview preparation platform",
    )
    EMBEDDING_DIMENSION: int = Field(
        default=1536,
        description="Dimension of the OpenAI embedding model",
    )
    LLM_MODEL: str = Field(
        default="openai/gpt-4.1-mini",
        description="LLM model to be used for the interview preparation platform",
    )
    LLM_TEMPERATURE: float = Field(
        default=0.0,
        description="Temperature for the LLM model to use for the interview preparation platform",
    )
    LLM_MAX_TOKENS: int = Field(
        default=32_000,
        description="Maximum number of tokens for the LLM model to use for the interview preparation platform",
    )
    ADDITIONAL_LLM_KWARGS: dict = Field(
        default={},
        description="Additional kwargs for the LLM model to use for the interview preparation platform",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "API_KEY": "sk-proj-1234567890",
                "EMBEDDING_MODEL": "text-embedding-3-small",
                "EMBEDDING_DIMENSION": 1536,
                "LLM_MODEL": "openai/gpt-4.1-mini",
                "LLM_TEMPERATURE": 0.0,
                "LLM_MAX_TOKENS": 32000,
                "ADDITIONAL_LLM_KWARGS": {},
            }
        }
    )


openai_config = OpenAIConfig()
