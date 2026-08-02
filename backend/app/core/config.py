import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered Automated Code Reviewer"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-in-production-2026-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://code_reviewer:code_reviewer_password@127.0.0.1:3306/code_reviewer?charset=utf8mb4",
    )
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]
    CORS_ORIGIN_REGEX: str = r"http://(localhost|127\.0\.0\.1):\d+"
    
    # Docker Sandbox Limits
    SANDBOX_TIMEOUT_SECONDS: int = 5
    SANDBOX_MEMORY_LIMIT: str = "256m"
    SANDBOX_CPU_LIMIT: float = 0.5

    model_config = SettingsConfigDict(case_sensitive=True)


settings = Settings()
