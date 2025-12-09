"""
Core configuration module for the Cyber Defense Platform.
Handles environment variable loading and application settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Cyber Defense Platform"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./cyber_defense.db"
    
    # LLM API Configuration
    llm_api_key: str = ""
    llm_api_url: str = "https://api.anthropic.com/v1/messages"
    llm_model: str = "claude-3-haiku-20240307"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # File Upload
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    allowed_audio_formats: List[str] = [".mp3", ".wav", ".m4a", ".ogg"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
