import os
import json
from dataclasses import dataclass

import aiofiles
import asyncio
import aiofiles.os as aios
from datetime import datetime
from typing import BinaryIO, List, Optional, Tuple

from server.storages.base import File, SortOrder, FilterBy


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
        }
        print(metadata)
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
        metadata_path = f"{file_path}.meta"

        try:
            await asyncio.gather(aios.remove(file_path), aios.remove(metadata_path))
        except FileNotFoundError:
            pass  # Ignore if files don't exist

    async def get(self, uid: str) -> File:
        metadata_path = os.path.join(self.root_dir, f"{uid}.meta")

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"File with UID {uid} not found")

        async with aiofiles.open(metadata_path, "r") as f:
            metadata = json.loads(await f.read())

        return File(**metadata, storage=self)

    async def list(
        self,
        prefix: str = "",
        limit: int = 10,
        offset: int = 0,
        sort_by: FilterBy = "created_at",
        sort_order: SortOrder = SortOrder.DESC,
    ) -> List[File] | list:
        files = os.listdir(self.root_dir)

        # # Apply sorting
        # if sort_by == "created_at":
        #     files.sort(
        #         key=lambda x: x.created_at, reverse=(sort_order == SortOrder.DESC)
        #     )
        # elif sort_by == "size":
        #     files.sort(key=lambda x: x.size, reverse=(sort_order == SortOrder.DESC))
        # elif sort_by == "name":
        #     files.sort(key=lambda x: x.uid, reverse=(sort_order == SortOrder.DESC))

        # Apply offset and limit
        files = files[offset : offset + limit]

        return files if files else []

    async def search(
        self,
        query: str = "",
        file_type: Optional[str] = None,
        owner: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 10,
        offset: int = 0,
        sort_by: FilterBy = "created_at",
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
