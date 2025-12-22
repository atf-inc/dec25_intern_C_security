# backend/app/core/config.py
"""
Core configuration module for the Cyber Defense Platform.
Handles environment variable loading and application settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from dotenv import load_dotenv
from pathlib import Path
import os

def configure_dotenv():
    # load .env from backend/ root by default
    import os
    from pathlib import Path
    
    # Try multiple paths to find .env file
    possible_paths = [
        ".env",  # Current directory (when running from backend/)
        "../.env",  # Parent directory
        "backend/.env",  # From project root
        Path(__file__).parent.parent.parent / ".env",  # Relative to this file
        Path(__file__).parent.parent.parent / "backend" / ".env",  # Explicit backend path
    ]
    
    for env_path in possible_paths:
        if Path(env_path).exists():
            print(f"🔧 Loading .env from: {env_path}")
            load_dotenv(env_path, override=True)
            
            # Verify key variables loaded
            if os.getenv("GEMINI_API_KEY"):
                print(f"✅ GEMINI_API_KEY loaded successfully")
            if os.getenv("LLM_PROVIDER"):
                print(f"✅ LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
            
            return
    
    print("⚠️ No .env file found in any expected location")
    print(f"   Current working directory: {os.getcwd()}")
    print(f"   Searched paths: {[str(p) for p in possible_paths]}")

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
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    # File upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

# Force environment loading before creating settings
configure_dotenv()

# single settings instance used across app
settings = Settings()
