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
    
    # Groq API (primary)
    groq_api_key: str = Field(..., env="GROQ_API_KEY")
    
    # HuggingFace API (disabled until API issues resolved)
    # huggingface_api_token: Optional[str] = Field(None, env="HUGGINGFACE_API_TOKEN")
    # huggingface_model_name: str = Field(default="Qwen/Qwen2.5-7B-Instruct", env="HUGGINGFACE_MODEL_NAME")
    
    # Anthropic (optional - fallback)
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    
    # Gemini API (optional - fallback)
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")
    
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
    
    # Working Hours Configuration
    weekday_start_time: str = Field(default="07:30", env="WEEKDAY_START_TIME")
    weekday_end_time: str = Field(default="18:30", env="WEEKDAY_END_TIME")
    weekend_start_time: str = Field(default="10:30", env="WEEKEND_START_TIME")
    weekend_end_time: str = Field(default="16:30", env="WEEKEND_END_TIME")
    working_hours_timezone: str = Field(default="America/New_York", env="WORKING_HOURS_TIMEZONE")
    
    # Chat Settings
    max_conversation_history: int = Field(default=20, env="MAX_CONVERSATION_HISTORY")
    session_timeout_minutes: int = Field(default=30, env="SESSION_TIMEOUT_MINUTES")
    
    # HuggingFace Settings
    tokenizers_parallelism: Optional[str] = Field(default="false", env="TOKENIZERS_PARALLELISM")
    
    # Peter's Contact Information
    my_phone_number: str = Field(..., env="MY_PHONE_NUMBER")
    my_email_address: str = Field(..., env="MY_EMAIL_ADDRESS")
    
    # Email Service Configuration
    smtp_server: str = Field(default="smtp.gmail.com", env="SMTP_SERVER")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(None, env="SMTP_PASSWORD")
    email_from_name: str = Field(default="ChatCal.ai", env="EMAIL_FROM_NAME")
    
    # Testing Configuration
    testing_mode: bool = Field(default=True, env="TESTING_MODE")  # Set to True to ignore Peter's email validation
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

# Debug logging for critical settings
import logging
logger = logging.getLogger(__name__)
logger.info(f"🔧 Settings Debug - Google Client ID: {settings.google_client_id[:20] if settings.google_client_id else 'NOT_SET'}...")
logger.info(f"🔧 Settings Debug - Google Client Secret: {'SET' if settings.google_client_secret else 'NOT_SET'}")
logger.info(f"🔧 Settings Debug - App Env: {settings.app_env}")
logger.info(f"🔧 Settings Debug - Calendar ID: {settings.google_calendar_id}")