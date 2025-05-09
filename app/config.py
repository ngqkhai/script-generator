from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    APP_NAME: str = "Video Script Generator"
    APP_VERSION: str = "0.1.0"

    # API config
    HOST: str = "0.0.0.0"
    PORT: int = 8002

    # Gemini API configuration
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-pro"

    # MongoDB configuration
    MONGODB_URL: str
    MONGODB_DB: str = "script_generator"

    # RabbitMQ configuration
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    DATA_COLLECTED_QUEUE: str = "data_collected"
    SCRIPT_GENERATED_EXCHANGE: str = "script_generated"
    SCRIPT_GENERATED_ROUTING_KEY: str = "script.generated"

    # Logging configuration
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
