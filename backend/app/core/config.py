import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel

_env_file = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_file.exists():
    load_dotenv(dotenv_path=_env_file)
else:
    load_dotenv()


class Settings(BaseModel):
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    APP_NAME: str = "DukaanFlow API"
    APP_VERSION: str = "1.0.0"
    DEFAULT_TIMEZONE: str = os.getenv("DEFAULT_TIMEZONE", "Asia/Kolkata")
    DEFAULT_CURRENCY: str = "INR"
    DEFAULT_SAFETY_BUFFER_PAISE: int = 1500000  # ₹15,000
    AI_FEATURES_ENABLED: bool = os.getenv("AI_FEATURES_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    AI_REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("AI_REQUEST_TIMEOUT_SECONDS", "12"))
    AI_MAX_OUTPUT_TOKENS: int = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "512"))
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dukaanflow-insecure-dev-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", str(3600 * 8)))  # 8 hours


settings = Settings()
