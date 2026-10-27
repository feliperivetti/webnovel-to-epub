from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional
from pathlib import Path


# Generated files live outside the source tree, independent of the shell's cwd.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"
LOG_DIR = OUTPUT_DIR / "logs"
DIAGNOSTICS_DIR = OUTPUT_DIR / "diagnostics"
BENCHMARKS_FILE = OUTPUT_DIR / "benchmarks.jsonl"

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "Novel Scraper API"
    DEBUG: bool = False
    
    # Security
    API_JWT_SECRET: Optional[str] = None
    
    # Scraper Config
    MAX_CHAPTERS_LIMIT: int = 1000
    DEFAULT_TIMEOUT: int = 15
    MAX_WORKERS: int = 2
    PROXY_URL: Optional[str] = None
    PROXY_URL_FALLBACK: Optional[str] = None
    
    model_config = SettingsConfigDict(env_file=".env")

@lru_cache()
def get_settings():
    return Settings()
