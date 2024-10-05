import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from pydantic import BaseModel

from setting import settings


class FileMetadata(BaseModel):
    id: str
    name: str
    size: int
    created_at: int
    updated_at: int
    category: str
    mime_type: str


class LocalStorage:
    def __init__(self):
        self.base_path = settings.local_storage.base_path
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
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f)

    def _get_category_path(self, category: str) -> str:
        return os.path.join(self.base_path, category)

    async def upload(self, file_path: str, category: str, mime_type: str) -> str:
        file_id = os.path.basename(file_path)
        category_path = self._get_category_path(category)
        os.makedirs(category_path, exist_ok=True)

        destination = os.path.join(category_path, file_id)
        shutil.copy2(file_path, destination)

        file_stat = os.stat(destination)

        now = int(datetime.now().timestamp())
        metadata = FileMetadata(
            id=file_id,
            name=os.path.basename(file_path),
            size=file_stat.st_size,
            created_at=now,
            updated_at=now,
            category=category,
            mime_type=mime_type,
        )

        self.metadata[file_id] = metadata.model_dump()
        self._save_metadata()

        return file_id

    async def download(self, file_id: str) -> bytes:
        if file_id not in self.metadata:
            raise HTTPException(status_code=404, detail="File not found")

        file_path = os.path.join(
            self.base_path, self.metadata[file_id]["category"], file_id
        )
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        with open(file_path, "rb") as f:
            return f.read()

    async def delete(self, file_id: str) -> None:
        if file_id not in self.metadata:
            raise HTTPException(status_code=404, detail="File not found")

        file_path = os.path.join(
            self.base_path, self.metadata[file_id]["category"], file_id
        )
        if os.path.exists(file_path):
            os.remove(file_path)

        del self.metadata[file_id]
        self._save_metadata()

    async def list_files(
        self,
        category: Optional[str] = None,
        mime_type: Optional[str] = None,
        start_date: Optional[int] = None,  # Unix timestamp
        end_date: Optional[int] = None,  # Unix timestamp
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        sort_by: str = "name",
        sort_order: str = "asc",
    ) -> List[Dict[str, Any]]:
        files = list(self.metadata.values())

        # Apply filters
        if category:
            files = [f for f in files if f["category"] == category]
        if mime_type:
            files = [f for f in files if f["mime_type"] == mime_type]
        if start_date:
            files = [f for f in files if f["created_at"] >= start_date]
        if end_date:
            files = [f for f in files if f["created_at"] <= end_date]
        if min_size is not None:
            files = [f for f in files if f["size"] >= min_size]
        if max_size is not None:
            files = [f for f in files if f["size"] <= max_size]

        # Sort files
        reverse = sort_order.lower() == "desc"
        files.sort(key=lambda x: x[sort_by], reverse=reverse)

        return files
