import os
from pydantic import BaseModel


class Settings(BaseModel):
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    APP_NAME: str = "DukaanFlow API"
    APP_VERSION: str = "1.0.0"
    DEFAULT_TIMEZONE: str = os.getenv("DEFAULT_TIMEZONE", "Asia/Kolkata")
    DEFAULT_CURRENCY: str = "INR"
    DEFAULT_SAFETY_BUFFER_PAISE: int = 1500000  # ₹15,000
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]


settings = Settings()
