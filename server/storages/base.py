import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, BinaryIO, Dict, List, Optional, Literal


# SortOrder Enum
class SortOrder(str):
    ASC = "asc"
    DESC = "desc"


OrderBy = Literal["created_at", "size", "name"]


@dataclass
class File:
    uid: str
    name: str
    size: int
    created_at: int
    path: str
    mime_type: str = "application/octet-stream"
    expires: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    category: Optional[str] = None

    @classmethod
    def resolve_absolute_path(cls, path: str, base_path: str) -> str:
        if path.startswith(base_path):
            return path
        return os.path.abspath(os.path.join(base_path, path))

    def is_expired(self) -> bool:
        return self.expires is not None and self.expires < datetime.now().timestamp()


class AbstractStorage(ABC):
    @abstractmethod
    async def upload(self, file: File, data: BinaryIO) -> None:
        pass

    @abstractmethod
    async def download(self, uid: str) -> tuple[File, BinaryIO]:
        pass

    @abstractmethod
    async def delete(self, uid: str) -> None:
        pass

    @abstractmethod
    async def get(self, uid: str) -> File:
        pass

    @abstractmethod
    async def list_files(
        self,
        category: Optional[str] = None,
        prefix: str = "",
        limit: int = 100,
        offset: int = 0,
        sort_by: OrderBy = "created_at",
        sort_order: SortOrder = SortOrder.DESC,
    ) -> List[File]:
        pass

    @abstractmethod
    async def search_files(
        self,
        query: str = "",
        category: Optional[str] = None,
        mime_type: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: OrderBy = "created_at",
        sort_order: SortOrder = SortOrder.DESC,
    ) -> List[File]:
        pass
