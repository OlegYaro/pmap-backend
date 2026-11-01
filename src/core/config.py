from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    REDIS_URL: str
    LOG_LEVEL: str = "INFO"
    # Extraction API: Backend reads transactions and starts runs through it.
    EXTRACTION_URL: str = "http://localhost:8000"
    EXTRACTION_API_KEY: SecretStr | None = None
    EXTRACTION_TIMEOUT_S: float = 30.0
    S3_BUCKET: str | None = None
    S3_REGION: str = "eu-north-1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
