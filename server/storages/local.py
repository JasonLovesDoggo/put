import os
import json
import shutil
from dataclasses import dataclass

import aiofiles
import aiofiles.os as aios
from datetime import datetime
from typing import BinaryIO, List, Optional, Tuple, Union

from starlette.responses import FileResponse

from server.storages.base import File, SortOrder, OrderBy
from server.storages.utils.meta import _read_metadata


@dataclass
class LocalSettings:
    location: str
    # Add other LocalStorage specific settings here


class AsyncLocalStorage:
    """
    Asynchronous local storage implementation of the Storage protocol.
    """

    def __init__(self, settings: LocalSettings) -> None:
        self.root_dir = settings.location or os.path.join(os.getcwd(), "local_storage")
        os.makedirs(self.root_dir, exist_ok=True)

    def load_file_from_uid(self, uid: str) -> File:
        """
        Loads file metadata from a JSON file and returns a File instance.
        """
        content_path = os.path.join(self.root_dir, uid)
        content_files = os.listdir(content_path)
        content_name = [
            file
            for file in content_files
            if not file.endswith(".json") and not file.endswith(".preview")
        ][0]
        with open(os.path.join(content_path, "meta.json"), "r") as f:
            data = json.load(f)

        # Construct a File instance using the loaded data
        return File(
            uid=uid,
            name=content_name,
            size=data["size"],
            created_at=data["created_at"],
            expires=data.get("expires"),
            metadata=data.get("metadata", {}),
        )

    async def upload(self, file: File, data: BinaryIO) -> None:
        file_root = os.path.join(self.root_dir, file.uid)

        await aios.makedirs(file_root, exist_ok=True)
        async with aiofiles.open(os.path.join(file_root, file.name), "wb") as f:
            await f.write(data.read())

        metadata = {
            "uid": file.uid,
            "metadata": file.metadata,
            "size": file.size,
            "created_at": file.created_at,
            "expires": file.expires,
            "name": file.name,
        }
        async with aiofiles.open(
            os.path.join(file_root, "meta.json"), "w"
        ) as f:  # todo: change to meta (no jso)
            await f.write(json.dumps(metadata))

    async def download(self, file_name: str) -> Tuple[File, BinaryIO]:
        file_path = os.path.join(self.root_dir, file_name)
        metadata_path = f"{file_path}.meta"

        if not os.path.exists(file_path) or not os.path.exists(metadata_path):
            raise FileNotFoundError(f"File with name {file_name} not found")

        async with aiofiles.open(metadata_path, "r") as f:
            metadata = json.loads(await f.read())

        file = File(**metadata, storage=self)

        data = await aiofiles.open(file_path, "rb")
        return (
            file,
            data,
        )

    async def delete(self, uid: str) -> None:
        file_path = os.path.join(self.root_dir, uid)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File with UID {uid} not found")
        shutil.rmtree(file_path, ignore_errors=True)

    async def get(self, uid: str) -> FileResponse:
        meta = _read_metadata(uid)

        if meta is None:
            raise FileNotFoundError(f"File with UID {uid} not found")

        return FileResponse(
            os.path.join(self.root_dir, uid, meta.name),
            media_type=meta.metadata.get("type", "application/octet-stream"),
            filename=meta.name,
            headers={"Content-Length": str(meta.size)},
        )

    async def list(
        self,
        limit: int = 10,
        offset: int = 0,
        sort_by: OrderBy = "created_at",
        sort_order: SortOrder = SortOrder.DESC,
    ) -> Union[List[File], list]:
        files = []

        # Asynchronously read all JSON files in the specified directory
        for uid in os.listdir(self.root_dir):
            file_instance = self.load_file_from_uid(uid)
            files.append(file_instance)

        # Sorting files based on sort_by and sort_order
        files.sort(
            key=lambda x: getattr(x, sort_by), reverse=(sort_order == SortOrder.DESC)
        )

        # Apply pagination
        paginated_files = files[offset : offset + limit]

        return paginated_files

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
    ) -> List[File] | None:
        all_files = await self.list(limit=1000000)  # Fetch all files
        if not all_files:
            return None

        filtered_files = []
        for file in all_files:
            if query and query.lower() not in file.uid.lower():
                continue
            if file_type and not file.uid.lower().endswith(file_type.lower()):
                continue
            if owner and file.metadata.get("owner") != owner:
                continue
            if created_after and file.created_at < created_after.timestamp():
                continue
            if created_before and file.created_at > created_before.timestamp():
                continue
            filtered_files.append(file)

        # Apply sorting
        if sort_by == "created_at":
            filtered_files.sort(
                key=lambda x: x.created_at, reverse=(sort_order == SortOrder.DESC)
            )
        elif sort_by == "size":
            filtered_files.sort(
                key=lambda x: x.size, reverse=(sort_order == SortOrder.DESC)
            )
        elif sort_by == "name":
            filtered_files.sort(
                key=lambda x: x.uid, reverse=(sort_order == SortOrder.DESC)
            )

        # Apply offset and limit
        filtered_files = filtered_files[offset : offset + limit]

        return filtered_files if filtered_files else None
