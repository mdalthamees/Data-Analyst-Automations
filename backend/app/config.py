import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    BASE_DIR: Path = BASE_DIR
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Paths
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    EXPORT_DIR: Path = BASE_DIR / "data" / "exports"
    SAMPLES_DIR: Path = BASE_DIR / "data" / "samples"
    
    # AI / LLM Configuration
    LLM_PROVIDER: str = "none" # 'none', 'gemini', 'openai', 'anthropic', 'ollama'
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Performance & Safeguards
    MAX_UPLOAD_SIZE_MB: int = 250
    QUERY_TIMEOUT_SECONDS: int = 60
    MAX_PREVIEW_ROWS: int = 1000
    DUCKDB_MEMORY_LIMIT: str = "2GB"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
settings.SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
