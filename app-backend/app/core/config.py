from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "StepZero API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS (환경변수에서는 쉼표로 구분된 문자열로 받음)
    BACKEND_CORS_ORIGINS_STR: str = "http://localhost:3000"

    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        return [i.strip() for i in self.BACKEND_CORS_ORIGINS_STR.split(",") if i.strip()]

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/stepzero"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security (JWT)
    SECRET_KEY: str = "CHANGE_ME_IN_PROD"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    OPENAI_API_KEY: str | None = None
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str | None = None
    
    model_config = SettingsConfigDict(
        case_sensitive=True, 
        env_file=".env", 
        env_file_encoding='utf-8', 
        extra="ignore"
    )

@lru_cache
def get_settings():
    return Settings()
