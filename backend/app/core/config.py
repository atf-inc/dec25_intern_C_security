# backend/app/core/config.py
"""
Core configuration module for the Cyber Defense Platform.
Handles environment variable loading and application settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from dotenv import load_dotenv
import os

def configure_dotenv():
    # load .env from backend/ root by default
    load_dotenv()

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./cyber_defense.db"

    # Gemini / LLM config
    LLM_PROVIDER: str = "mock"  # "mock", "gemini", "openai"
    GEMINI_API_KEY: str = ""
    GEMINI_API_BASE: str = "https://generativelanguage.googleapis.com/v1beta/models"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TIMEOUT: int = 20

    # Heuristics gating
    HEURISTIC_THRESHOLD: int = 30

    # App Misc
    APP_NAME: str = "Cyber Defense Platform"
    DEBUG: bool = False

    # CORS (optional)
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # File upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

# single settings instance used across app
settings = Settings()
