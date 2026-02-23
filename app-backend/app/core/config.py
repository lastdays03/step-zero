from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from functools import lru_cache
from typing import List
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "StepZero API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    # CORS (환경변수에서는 쉼표로 구분된 문자열로 받음)
    BACKEND_CORS_ORIGINS_STR: str = "http://localhost:3000"

    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        return [i.strip() for i in self.BACKEND_CORS_ORIGINS_STR.split(",") if i.strip()]

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security (JWT)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SQL_ECHO: bool = False
    
    # OpenAI
    OPENAI_API_KEY: str | None = None
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str | None = None

    # Feature Flags
    ENABLE_SOCIAL_MOCK: bool = False
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBED_MODEL: str = "text-embedding-3-small"

    # Storage (local only for now)
    STORAGE_LOCAL_ROOT: str | None = None
    GROWTH_CLUB_MAX_IMAGE_MB: int = 20
    GROWTH_CLUB_MAX_FILE_MB: int = 50
    GROWTH_CLUB_MAX_TOTAL_MB: int = 200
    GROWTH_CLUB_MAX_IMAGE_COUNT: int = 10
    GROWTH_CLUB_MAX_FILE_COUNT: int = 10

    @staticmethod
    def _normalize_optional_secret(value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        placeholders = {
            "REPLACE_ME",
            "CHANGE_ME",
            "CHANGE_ME_IN_PROD",
            "YOUR_API_KEY",
        }
        return None if cleaned in placeholders else cleaned

    @model_validator(mode="after")
    def validate_security(self) -> "Settings":
        if not self.SECRET_KEY.strip():
            raise ValueError("SECRET_KEY must be set")
        if self.ENVIRONMENT.lower() == "production" and self.SECRET_KEY == "CHANGE_ME_IN_PROD":
            raise ValueError("SECRET_KEY must not use a default value in production")
        self.OPENAI_API_KEY = self._normalize_optional_secret(self.OPENAI_API_KEY)
        self.GOOGLE_CLIENT_ID = self._normalize_optional_secret(self.GOOGLE_CLIENT_ID)
        return self

    @property
    def STORAGE_ROOT_PATH(self) -> Path:
        if self.STORAGE_LOCAL_ROOT and self.STORAGE_LOCAL_ROOT.strip():
            return Path(self.STORAGE_LOCAL_ROOT).expanduser()

        backend_root = Path(__file__).resolve().parents[2]
        return backend_root / "uploads"

    @property
    def ACTIONKIT_STORAGE_PATH(self) -> Path:
        return self.STORAGE_ROOT_PATH / "actionkit"
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=(".env", ".env.local"),
        env_file_encoding='utf-8',
        extra="ignore"
    )

@lru_cache
def get_settings():
    return Settings()
