"""
Application settings and configuration management.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application settings
    app_name: str = Field(default="Instagram Content Analyzer", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    
    # Security settings
    secret_key: str = Field(..., alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS settings
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        alias="ALLOWED_ORIGINS"
    )
    
    # Database settings
    mongodb_url: str = Field(..., alias="MONGODB_URL")
    database_name: str = Field(default="instagram_analyzer", alias="DATABASE_NAME")
    
    # OpenAI settings
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-vision-preview", alias="OPENAI_MODEL")
    openai_audio_model: str = Field(default="whisper-1", alias="OPENAI_AUDIO_MODEL")
    
    # Instagram settings
    instagram_username: Optional[str] = Field(default=None, alias="INSTAGRAM_USERNAME")
    instagram_password: Optional[str] = Field(default=None, alias="INSTAGRAM_PASSWORD")
    
    # Browser automation settings
    selenium_headless: bool = Field(default=True, alias="SELENIUM_HEADLESS")
    selenium_timeout: int = Field(default=30, alias="SELENIUM_TIMEOUT")
    
    # Content processing settings
    max_file_size_mb: int = Field(default=100, alias="MAX_FILE_SIZE_MB")
    temp_dir: str = Field(default="./temp", alias="TEMP_DIR")
    
    # Rate limiting settings
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, alias="RATE_LIMIT_WINDOW")  # seconds
    
    # Logging settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, alias="LOG_FILE")


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()