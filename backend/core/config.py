import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = DATA_DIR / "reports"
UPLOADS_DIR = DATA_DIR / "uploads"

DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    # GLM-5.3 / Z.ai Configuration
    ZAI_API_KEY: str = Field(default="", description="API Key for Z.ai or OpenAI-compatible endpoint")
    ZAI_BASE_URL: str = Field(default="https://api.z.ai/api/coding/paas/v4", description="Base URL for GLM API")
    MODEL_NAME: str = Field(default="glm-5.3", description="Model name to use")
    REASONING_EFFORT: str = Field(default="max", description="Reasoning effort: low, high, max")
    TEMPERATURE: float = Field(default=0.2, description="Sampling temperature")
    MAX_TOKENS: int = Field(default=4096, description="Max response tokens")
    
    # Application & Database Configuration
    DATABASE_URL: str = Field(default_factory=lambda: f"sqlite+aiosqlite:///{(DATA_DIR / 'autovalidate.db').as_posix()}")
    SECRET_KEY: str = Field(default="autovalidate-pro-secret-key-change-in-prod")
    DEBUG: bool = Field(default=False)
    
    # Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    REPORTS_DIR: Path = REPORTS_DIR
    UPLOADS_DIR: Path = UPLOADS_DIR
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=[str(BASE_DIR / ".env"), str(BASE_DIR.parent / ".env")],
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
