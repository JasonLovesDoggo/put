from dataclasses import dataclass
from enum import Enum

import toml  # Add toml library

from server.storages import (  # Import necessary classes
    AsyncLocalStorage,
    S3Storage,
    S3Settings,
    LocalSettings,
    Storage,
)


class StorageTypes(Enum):
    LOCAL = "local"
    S3 = "s3"


@dataclass
class Settings:
    storage_type: Storage
    local: LocalSettings | None = None
    s3: S3Settings | None = None


def load_settings(config_file: str = "config.toml") -> Settings:
    """
    Loads settings from a TOML file and returns a Settings object.
    """
    with open(config_file, "r") as f:
        config = toml.load(f)

    storage_type = StorageTypes(config["storage"]["type"])

    settings = Settings(storage_type=storage_type)

    if storage_type == StorageTypes.LOCAL:
        settings.local = LocalSettings(location=config["storage"]["local"]["location"])
    elif storage_type == StorageTypes.S3:
        settings.s3 = S3Settings(
            bucket_name=config["storage"]["s3"]["bucket_name"],
            endpoint_url=config["storage"]["s3"]["endpoint_url"],
            region_name=config["storage"]["s3"]["region_name"],
            access_key_id=config["storage"]["s3"]["access_key_id"],
            secret_access_key=config["storage"]["s3"]["secret_access_key"],
        )
    return settings


def create_storage(settings: Settings) -> Storage:
    """
    Creates and returns the appropriate storage object based on the provided settings.
    """
    if settings.storage_type == StorageTypes.LOCAL:
        if not settings.local:
            raise ValueError("Missing local settings")
        return AsyncLocalStorage(settings.local)
    elif settings.storage_type == StorageTypes.S3:
        if not settings.s3:
            raise ValueError("Missing S3 settings")
        return S3Storage(settings.s3)
    else:
        raise ValueError(f"Invalid storage type: {settings.storage_type}")
