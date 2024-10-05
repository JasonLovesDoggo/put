from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query

from server.storages.local import LocalStorage

router = APIRouter()


def get_storage() -> LocalStorage:
    return LocalStorage()


@router.get("/files")
async def list_files(
    storage: LocalStorage = Depends(get_storage),
    category: Optional[str] = None,
    mime_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    sort_by: str = Query("name", enum=["name", "size", "created_at", "updated_at"]),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
) -> List[Dict[str, Any]]:
    return await storage.list_files(
        category=category,
        mime_type=mime_type,
        start_date=start_date,
        end_date=end_date,
        min_size=min_size,
        max_size=max_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post("/files")
async def upload_file(
    file_path: str,
    category: str,
    mime_type: str,
    storage: LocalStorage = Depends(get_storage),
) -> Dict[str, str]:
    file_id = await storage.upload(file_path, category, mime_type)
    return {"file_id": file_id}


@router.get("/files/{file_id}")
async def download_file(
    file_id: str, storage: LocalStorage = Depends(get_storage)
) -> bytes:
    return await storage.download(file_id)


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str, storage: LocalStorage = Depends(get_storage)
) -> Dict[str, str]:
    await storage.delete(file_id)
    return {"status": "success"}
