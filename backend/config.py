from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "sqlite:///./instaguard.db"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # Auth
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Apify & Instagram
    APIFY_API_TOKEN: str = ""
    INSTAGRAM_SESSION_ID: str = ""   # sessionid cookie value from browser
    MAX_POSTS: int = 50              # default posts per scan

    # Model
    MODEL_PATH: str = "./data/instaguard_model.pth"
    MODEL_DEVICE: str = "cpu"
    CONFIDENCE_THRESHOLD: float = 0.5

    # App
    FRONTEND_URL: str = "http://localhost:3000"
    ENVIRONMENT: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
