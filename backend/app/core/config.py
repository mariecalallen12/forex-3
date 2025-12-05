"""
Cấu hình ứng dụng - Application Configuration
Digital Utopia Platform

Quản lý tất cả cấu hình môi trường cho PostgreSQL, Redis, JWT, và các dịch vụ khác
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache
import os


class Settings(BaseSettings):
    """
    Cấu hình ứng dụng chính
    Đọc từ biến môi trường hoặc file .env
    """
    
    # =============== Cấu hình ứng dụng ===============
    APP_NAME: str = "Digital Utopia Platform"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # =============== Cấu hình API ===============
    API_V1_STR: str = "/api"
    # QUAN TRỌNG: Phải thay đổi SECRET_KEY trong production thông qua biến môi trường
    SECRET_KEY: str = "CHANGE-THIS-IN-PRODUCTION-USE-ENV-VAR"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # =============== Cấu hình PostgreSQL ===============
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "digital_utopia"
    
    @property
    def DATABASE_URL(self) -> str:
        """Tạo URL kết nối PostgreSQL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def DATABASE_URL_ASYNC(self) -> str:
        """Tạo URL kết nối PostgreSQL cho async"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # =============== Cấu hình Redis ===============
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # Redis cache TTL settings (seconds)
    REDIS_SESSION_TTL: int = 86400  # 24 hours
    REDIS_CACHE_TTL: int = 300  # 5 minutes
    REDIS_RATE_LIMIT_TTL: int = 3600  # 1 hour
    REDIS_MARKET_DATA_TTL: int = 5  # 5 seconds for real-time data
    
    @property
    def REDIS_URL(self) -> str:
        """Tạo URL kết nối Redis"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # =============== Cấu hình CORS ===============
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:3002",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8080"
    ]
    
    # =============== Cấu hình Email ===============
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: str = "noreply@digitalutopia.com"
    EMAILS_FROM_NAME: str = "Digital Utopia Platform"
    
    # =============== Cấu hình File Upload ===============
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "pdf", "doc", "docx"]
    
    # =============== Cấu hình Rate Limiting ===============
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # =============== Cấu hình Logging ===============
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Lấy instance settings (cached)
    Sử dụng lru_cache để tránh đọc file .env nhiều lần
    """
    return Settings()


# Global settings instance
settings = get_settings()
