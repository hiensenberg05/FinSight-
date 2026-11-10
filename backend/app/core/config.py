import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "FinSight Modular Financial Intelligence API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./finsight.db"

    # Gnani AI Credentials
    GNANI_API_KEY: str = os.getenv("GNANI_API_KEY", "")
    GNANI_STT_URL: str = "https://api.vachana.ai/stt/v3"
    GNANI_TTS_URL: str = "https://api.vachana.ai/api/v1/tts/inference"

    # Reasoning / LLM
    REASONING_PROVIDER: str = "groq"
    REASONING_MODEL: str = "openai/gpt-oss-120b"
    GENERATION_PROVIDER: str = "groq"
    GENERATION_MODEL: str = "openai/gpt-oss-120b"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_APT_KEY") or ""

    # Security
    SECRET_KEY: str = "finsight_dev_secret_key_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"

    # Slack Integration
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_USER_TOKEN: str = os.getenv("SLACK_USER_TOKEN", "")
    SLACK_CHANNEL_ID: str = os.getenv("SLACK_CHANNEL_ID", "C09M5ETUMPF")
    SLACK_CHANNEL_NAME: str = os.getenv("SLACK_CHANNEL_NAME", "#engineering-inventory-tracker")

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*",
    ]


settings = Settings()
