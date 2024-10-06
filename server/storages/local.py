import os
import shutil
import json
from datetime import datetime
from typing import List, Optional, BinaryIO

from fastapi import HTTPException

from .base import AbstractStorage, File, OrderBy, SortOrder


class LocalStorage(AbstractStorage):
    def __init__(self) -> None:
        self.base_path = "/home/json/PycharmProjects/put/static"
        self.metadata_file = os.path.join(self.base_path, "metadata.json")
        self._ensure_base_path()
        self._load_metadata()

    def _ensure_base_path(self):
        os.makedirs(self.base_path, exist_ok=True)

    def _load_metadata(self):
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, "r") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}

    def _save_metadata(self):
        # Validate metadata
        json.dumps(self.metadata)
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f)

    def _get_file_path(self, file: File) -> str:
        if file.category:
            return os.path.join(self.base_path, file.category, file.uid)
        else:
            return os.path.join(self.base_path, file.uid)

    async def upload(self, file: File, data: BinaryIO) -> None:
        file_path = self._get_file_path(file)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(data, f)
        now = int(datetime.now().timestamp())
        metadata = {
            "uid": file.uid,
            "name": file.name,
            "size": file.size,
            "created_at": now,
            "updated_at": now,
            "category": file.category,
            "mime_type": file.mime_type,
            "metadata": file.metadata,
        }
        self.metadata[file.uid] = metadata
        self._save_metadata()

    async def download(self, uid: str) -> tuple[File, BinaryIO]:
        if uid not in self.metadata:
            raise HTTPException(status_code=404, detail="File not found")
        metadata = self.metadata[uid]
        file = File(
            uid=uid, **metadata, path=self._get_file_path(File(uid=uid, **metadata))
        )
        file_path = file.path
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        data = open(file_path, "rb")
        return file, data

    async def delete(self, uid: str) -> None:
        if uid not in self.metadata:
            raise HTTPException(status_code=404, detail="File not found")
        metadata = self.metadata[uid]
        file_path = self._get_file_path(File(uid=uid, **metadata))
        if os.path.exists(file_path):
            os.remove(file_path)
        del self.metadata[uid]
        self._save_metadata()

    async def get(self, uid: str) -> File:
        if uid not in self.metadata:
            raise HTTPException(status_code=404, detail="File not found")
        metadata = self.metadata[uid]
        file = File(
            uid=uid, **metadata, path=self._get_file_path(File(uid=uid, **metadata))
        )
        if not os.path.exists(file.path):
            raise HTTPException(status_code=404, detail="File not found")
        return file

    async def list_files(
        self,
        category: Optional[str] = None,
        prefix: str = "",
        limit: int = 100,
        offset: int = 0,
        sort_by: OrderBy = "created_at",
        sort_order: SortOrder = SortOrder.DESC,
    ) -> List[File]:
        files = []
        for uid, metadata in self.metadata.items():
            if category and metadata.get("category") != category:
                continue
            if prefix and not metadata["name"].startswith(prefix):
                continue
            print(metadata)
            if metadata.get("category") is None:
                metadata["category"] = "unsorted"
            del metadata["updated_at"]
            if metadata.get("path") is None:
                metadata["path"] = os.path.join(
                    self.base_path,
                    metadata["category"],
                    metadata["uid"],
                    metadata["name"],
                )
            files.append(File(**metadata))
        reverse = sort_order == SortOrder.DESC
        files.sort(key=lambda x: getattr(x, sort_by), reverse=reverse)
        return files[offset : offset + limit]

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
        files = []
        for uid, metadata in self.metadata.items():
            if category and metadata.get("category") != category:
                continue
            if mime_type and metadata.get("mime_type") != mime_type:
                continue
            if query and query.lower() not in metadata["name"].lower():
                continue
            created_at = datetime.fromtimestamp(metadata["created_at"])
            if created_after and created_at < created_after:
                continue
            if created_before and created_at > created_before:
                continue
            file = File(
                uid=uid, **metadata, path=self._get_file_path(File(uid=uid, **metadata))
            )
            files.append(file)
        reverse = sort_order == SortOrder.DESC
        files.sort(key=lambda x: getattr(x, sort_by), reverse=reverse)
        return files[offset : offset + limit]
