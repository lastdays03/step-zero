
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "StepZero API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # Security (JWT)
    SECRET_KEY: str = "CHANGE_ME_IN_PROD" # Should be loaded from env in prod
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    OPENAI_API_KEY: str | None = None
    
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", env_file_encoding='utf-8')

@lru_cache
def get_settings():
    return Settings()
