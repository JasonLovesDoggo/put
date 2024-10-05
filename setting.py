from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

import tomllib
from pydantic import BaseModel, Field, validator


class TusConfig(BaseModel):
    max_size: int = Field(1024 * 1024 * 1024, description="Maximum file size in bytes")
    expiration_period: int = Field(
        86400, description="Expiration period for incomplete uploads in seconds"
    )


class LocalStorageConfig(BaseModel):
    base_path: Path = Field(..., description="Base path for local file storage")


class S3StorageConfig(BaseModel):
    bucket_name: str = Field(..., description="S3 bucket name")
    endpoint_url: Optional[str] = Field(
        None, description="S3 endpoint URL (for non-AWS S3-compatible storage)"
    )
    region_name: str = Field("us-east-1", description="S3 region name")
    access_key_id: str = Field(..., description="S3 access key ID")
    secret_access_key: str = Field(..., description="S3 secret access key")


class APIConfig(BaseModel):
    prefix: str = Field("/api", description="API route prefix")
    cors_origins: list[str] = Field(["*"], description="Allowed CORS origins")
    cors_headers: list[str] = Field(["*"], description="Allowed CORS headers")


class LoggingConfig(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        "INFO", description="Logging level"
    )
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format"
    )


class Settings(BaseModel):
    app_name: str = Field("Self-Hosted Drive", description="Application name")
    debug: bool = Field(False, description="Debug mode")
    storage_type: Literal["local", "s3"] = Field(
        "local", description="Storage type (local or s3)"
    )
    local_storage: LocalStorageConfig
    s3_storage: Optional[S3StorageConfig] = None
    tus: TusConfig = Field(default_factory=TusConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @validator("s3_storage", always=True)
    def validate_s3_storage(cls, v, values):
        if values["storage_type"] == "s3" and v is None:
            raise ValueError(
                "S3 storage configuration is required when storage_type is set to 's3'"
            )
        return v


def load_settings(config_path: str | Path = "config.toml") -> Settings:
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("rb") as f:
        config_data = tomllib.load(f)

    return Settings(**config_data)


# Usage example:
if __name__ == "__main__":
    settings = load_settings()
    print(f"App Name: {settings.app_name}")
    print(f"Storage Type: {settings.storage_type}")
    if settings.storage_type == "local":
        print(f"Local Storage Path: {settings.local_storage.base_path}")
    else:
        print(f"S3 Bucket: {settings.s3_storage.bucket_name}")
    print(f"API Prefix: {settings.api.prefix}")
    print(f"TUS Max Size: {settings.tus.max_size}")


settings = load_settings("config.toml")
