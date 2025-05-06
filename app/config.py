from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    APP_NAME: str = "Video Script Generator"
    APP_VERSION: str = "0.1.0"

    # API config
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Gemini API configuration
    GEMINI_API_KEY: str
    GEMINI_MODEL: str

    # MongoDB configuration
    MONGODB_URL: str
    MONGODB_DB: str

    class Config:
        env_file = ".env"


settings = Settings()
