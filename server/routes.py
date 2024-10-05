from typing import Any

from fastapi import APIRouter
from setting import load_settings, create_storage

storage = create_storage(load_settings())
router = APIRouter(prefix="/api")


@router.get("/list")
async def list_files() -> Any:
    return await storage.list()
