from .base import AbstractStorage, File, OrderBy, SortOrder
from .local import LocalStorage
from .s3 import S3Settings, S3Storage

__all__ = [
    "AbstractStorage",
    "File",
    "SortOrder",
    "OrderBy",
    "S3Storage",
    "S3Settings",
    "StorageTypes",
    "LocalStorage",
]

StorageTypes = S3Storage | LocalStorage
