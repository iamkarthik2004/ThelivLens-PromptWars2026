from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Resolve the backend's env file from this module, not the process cwd.
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[2] / ".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173"
    max_upload_bytes: int = 500 * 1024 * 1024
    max_upload_size_mb: int = 500
    mongodb_uri: str = ""
    mongodb_database: str = "truthlens"
    s3_endpoint_url: str = ""
    s3_bucket: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_region: str = "us-east-1"
    hf_token: str = ""
    hf_model_id: str = "deepseek-ai/DeepSeek-V4-Flash-Vision-Exp"

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def cloud_storage_configured(self) -> bool:
        return all((self.s3_endpoint_url, self.s3_bucket, self.s3_access_key_id, self.s3_secret_access_key))

    @property
    def upload_limit_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
