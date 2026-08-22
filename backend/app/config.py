import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application configurations and secrets loaded from environment variables.
    """
    ENV: str = "development"  # development, demo, production
    DATABASE_URL: str = "sqlite:///./tathya.db"
    JWT_SECRET: str = "tathya_secret_key_evidence_before_action_2026"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Bright Data API Settings
    BRIGHT_DATA_API_TOKEN: str = ""
    DEFAULT_YAHOO_COLLECTOR_ID: str = ""
    DEFAULT_GOOGLE_COLLECTOR_ID: str = ""
    
    # Market Intelligence (Finnhub) Settings
    MARKET_NEWS_API_KEY: str = ""

    # CORS configuration
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    def __init__(self, **values):
        super().__init__(**values)
        secret_key = os.getenv("JWT_SECRET_KEY")
        if secret_key:
            self.JWT_SECRET = secret_key

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create a singleton settings object
settings = Settings()
