"""Application configuration using pydantic ``BaseSettings``.

Settings are read from environment variables, with sensible defaults provided for
non-sensitive values.  This allows the service to be configured via a .env file
or container environment.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # External APIs
    gemini_api_key: str | None = None

    # Model / similarity configuration
    similarity_threshold: float = 0.65
    gemini_model: str = "gemini-3-flash-preview"
    max_skills_for_explanation: int = 6
    sentence_model_name: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
