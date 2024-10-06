from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException

from .storages.local import LocalStorage
from .storages.base import File, SortOrder

router = APIRouter()


def get_storage() -> LocalStorage:
    return LocalStorage()


@router.get("/files", response_model=List[File])
async def list_files(
    category: Optional[str] = None,
    prefix: str = "",
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", enum=["created_at", "size", "name"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    storage: LocalStorage = Depends(get_storage),
):
    files = await storage.list_files(
        category=category,
        prefix=prefix,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=SortOrder(sort_order),
    )
    return files


@router.get("/files/search", response_model=List[File])
async def search_files(
    query: str = "",
    category: Optional[str] = None,
    mime_type: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", enum=["created_at", "size", "name"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    storage: LocalStorage = Depends(get_storage),
):
    files = await storage.search_files(
        query=query,
        category=category,
        mime_type=mime_type,
        created_after=created_after,
        created_before=created_before,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=SortOrder(sort_order),
    )
    return files


@router.get("/files/{uid}")
async def get_file(uid: str, storage: LocalStorage = Depends(get_storage)):
    try:
        file, data = await storage.download(uid)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")

    from fastapi.responses import StreamingResponse

    response = StreamingResponse(
        data,
        media_type=file.mime_type,
    )
    response.headers["Content-Disposition"] = f'attachment; filename="{file.name}"'
    response.headers["Content-Length"] = str(file.size)
    return response


@router.delete("/files/{uid}")
async def delete_file(uid: str, storage: LocalStorage = Depends(get_storage)):
    await storage.delete(uid)
    return {"status": "success"}
