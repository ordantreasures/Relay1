from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postman@localhost:5432/relay"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    secret_key: str = "483f0ba336871d0c0489edb16c23d4d0"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # API Keys
    gemini_api_key: Optional[str] = None
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "https://relaey.netlify.app/"]
    
    # Environment
    environment: str = "dev"
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    # File Upload
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: List[str] = ["image/jpeg", "image/png", "image/gif"]
    
    class Config:
        env_file = ".env"
        extra = "allow"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()