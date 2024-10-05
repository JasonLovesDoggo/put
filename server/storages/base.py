from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, BinaryIO, Dict, List, Literal, Optional


class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"


OrderBy = Literal["created_at", "size", "name"]


@dataclass
class File:
    uid: str
    name: str
    size: int
    created_at: int
    expires: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

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
    async def list(
        self,
        prefix: str = "",
        limit: int = 10,
        offset: int = 0,
        sort_by: OrderBy = "created_at",
        sort_order: SortOrder = SortOrder.DESC,
    ) -> List[File]:
        pass

    @abstractmethod
    async def search(
        self,
        query: str = "",
        file_type: Optional[str] = None,
        owner: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 10,
        offset: int = 0,
        sort_by: OrderBy = "created_at",
        sort_order: SortOrder = SortOrder.DESC,
    ) -> List[File]:
        pass
