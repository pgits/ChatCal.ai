import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Application
    app_name: str = Field(default="ChatCal.ai", env="APP_NAME")
    app_env: str = Field(default="development", env="APP_ENV")
    app_host: str = Field(default="0.0.0.0", env="APP_HOST")
    app_port: int = Field(default=8000, env="APP_PORT")
    
    # Anthropic (optional - fallback)
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    
    # Gemini API
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    
    # Google Calendar
    google_calendar_id: str = Field(default="pgits.job@gmail.com", env="GOOGLE_CALENDAR_ID")
    google_client_id: Optional[str] = Field(None, env="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(None, env="GOOGLE_CLIENT_SECRET")
    google_credentials_path: str = Field(default="credentials/google_calendar_credentials.json", env="GOOGLE_CREDENTIALS_PATH")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    cors_origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:8000"], env="CORS_ORIGINS")
    
    # Timezone
    default_timezone: str = Field(default="America/New_York", env="DEFAULT_TIMEZONE")
    
    # Chat Settings
    max_conversation_history: int = Field(default=20, env="MAX_CONVERSATION_HISTORY")
    session_timeout_minutes: int = Field(default=30, env="SESSION_TIMEOUT_MINUTES")
    
    # HuggingFace Settings
    tokenizers_parallelism: Optional[str] = Field(default="false", env="TOKENIZERS_PARALLELISM")
    
    # Peter's Contact Information
    my_phone_number: str = Field(..., env="MY_PHONE_NUMBER")
    my_email_address: str = Field(..., env="MY_EMAIL_ADDRESS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()