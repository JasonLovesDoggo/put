from typing import Any

from fastapi import APIRouter
from starlette import status

from server.storages.base import SortOrder, OrderBy
from setting import load_settings, create_storage

storage = create_storage(load_settings())
router = APIRouter(prefix="/api")


@router.get("/list")
async def list_files(
    limit: int = 10,
    offset: int = 0,
    sort_by: OrderBy = "created_at",
    sort_order: SortOrder = SortOrder.DESC,
) -> Any:
    return await storage.list(
        limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
    )


@router.delete(
    "/{uid}", status_code=status.HTTP_204_NO_CONTENT | status.HTTP_404_NOT_FOUND
)
async def delete_file(uid: str) -> None:
    try:
        await storage.delete(uid)
    except FileNotFoundError:
        return status.HTTP_404_NOT_FOUND


# @router.get("/{uid}")
# async def get_file(uid: str) -> Any:
#     return await storage.get(uid)


@router.get("/{uid}", status_code=status.HTTP_404_NOT_FOUND | status.HTTP_200_OK)
async def get_file(uid: str) -> Any:
    return await storage.get(uid)
