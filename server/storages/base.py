import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import BinaryIO, List, Literal, Optional, Protocol, Any, Dict

OrderBy = Literal["created_at", "size", "name"]


class SortOrder(Enum):
    """Enum for specifying the sort order of search results."""

    ASC = "asc"
    DESC = "desc"


@dataclass
class File:
    """
    Represents a file stored in the storage.
    """

    uid: str  # Unique identifier of the file
    name: str  # Name of the file
    size: int  # Size of the file in bytes
    created_at: int  # UNIX timestamp of when the file was created
    expires: Optional[int] = (
        None  # UNIX timestamp of when the file expires (if None, it never expires)
    )
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )  # Metadata of the file, such as name, type, etc.
    storage: Optional["Storage"] = None  # Storage object that the file is stored in

    def is_expired(self) -> bool:
        """
        Checks if the file is expired.

        Returns:
            True if the file is expired, False otherwise.
        """
        if self.expires is None:
            return False
        return self.expires < time.time()


class Storage(Protocol):
    """
    Defines the interface for a swappable storage backend.
    """

    def __init__(self, location: Optional[str] = None) -> None:
        """
        Initializes the storage with an optional location.

        Args:
            location: The location of the storage (e.g., a directory path or a bucket name).
        """

    async def upload(self, file: File, data: BinaryIO) -> None:
        """
        Uploads a file to the storage.

        Args:
            file: The File object representing the file to upload.
            data: A binary stream of the file data.
        """

    async def download(self, uid: str) -> tuple[File, BinaryIO]:
        """
        Downloads a file from the storage.

        Args:
            uid: The unique identifier of the file to download.

        Returns:
            A tuple containing the File object and a binary stream of the file data.
        """

    async def delete(self, uid: str) -> None:
        """
        Deletes a file from the storage.

        Args:
            uid: The unique identifier of the file to delete.
        """

    async def get(self, uid: str) -> File:
        """
        Retrieves the metadata of a file from the storage.

        Args:
            uid: The unique identifier of the file to retrieve.

        Returns:
            The File object representing the file.

        Raises:
            FileNotFoundError: If the file is not found.
        """

    async def list(
        self,
        prefix: str = "",
        limit: int = 10,
        offset: int = 0,
        sort_by: OrderBy = "created_at",
        sort_order: SortOrder = SortOrder.DESC,
    ) -> list[File] | None:
        """
        Lists files in the storage, optionally filtered by a prefix.

        Args:
            prefix: An optional prefix to filter the files (e.g., a directory or folder path).
            limit: The maximum number of results to return.
            offset: The starting offset for the results.
            sort_by: The field to sort by ("created_at", "size", or "name").
            sort_order: The sort order (SortOrder.ASC or SortOrder.DESC).

        Returns:
            A list of File objects, or None if no files are found.
        """

    async def search(
        self,
        query: str = "",  # Changed from 'search' to 'query' for clarity
        file_type: Optional[str] = None,  # New filter for file type
        owner: Optional[str] = None,  # New filter for file owner
        created_after: Optional[datetime] = None,  # New filter for creation date
        created_before: Optional[datetime] = None,  # New filter for creation date
        limit: int = 10,
        offset: int = 0,
        sort_by: OrderBy = "created_at",
        sort_order: SortOrder = SortOrder.DESC,
    ) -> List[File] | None:
        """
        Searches for files matching the given criteria.

        Args:
            query: A search query string.
            file_type: The type of file to search for (e.g., "pdf", "jpg").
            owner: The owner of the file.
            created_after: The earliest creation date for the file.
            created_before: The latest creation date for the file.
            limit: The maximum number of results to return.
            offset: The starting offset for the results.
            sort_by: The field to sort by ("created_at", "size", or "name").
            sort_order: The sort order (SortOrder.ASC or SortOrder.DESC).

        Returns:
            A list of File objects matching the search criteria, or None if no files are found.
        """
