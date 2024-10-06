import logging
from datetime import datetime

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from server.storages import S3Settings
from server.storages.local import LocalStorage
from server.storages.base import File
from server.tus import create_api_router
from server.metadata import FileMetadata
from server.routes import router as api_router
from setting import settings

# Constants
VERSION = "1.0.1"
COMPATIBLE_VERSIONS = [VERSION]
KB = 1024
MB = KB * 1024
GB = MB * 1024

# Configure Storage
if settings.storage_type == "local":
    storage = LocalStorage()
else:
    storage = S3Settings(
        bucket_name=settings.s3_storage.bucket_name,
        endpoint_url=settings.s3_storage.endpoint_url,
        region_name=settings.s3_storage.region_name,
        access_key_id=settings.s3_storage.access_key_id,
        secret_access_key=settings.s3_storage.secret_access_key,
    )

# Initialize FastAPI app
app = FastAPI(title=settings.app_name, debug=settings.debug)

# Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_headers=settings.api.cors_headers,
)

# Configure logging
logging.basicConfig(level=settings.logging.level, format=settings.logging.format)

# TUS Configuration
tus_config = {
    "files_dir": str(settings.tus.files_dir),
    "max_size": settings.tus.max_size,
    "expiration_period": settings.tus.expiration_period,
}


# Health Check Endpoint
@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


# On Upload Complete Callback
async def on_upload_complete(file_path: str, metadata: FileMetadata):
    print(f"Upload complete: {file_path}")
    print(f"Metadata: {metadata}")

    file = File(
        uid=metadata.uid,
        name=metadata.metadata.get("filename", metadata.uid),
        size=metadata.offset,
        created_at=int(datetime.now().timestamp()),
        path=file_path,
        mime_type=metadata.metadata.get("mime_type", "application/octet-stream"),
        metadata=metadata.metadata,
        category=metadata.metadata.get("category", "unsorted"),
    )

    with open(file_path, "rb") as f:
        await storage.upload(file, f)


# Include TUS API Router
app.include_router(
    create_api_router(
        files_dir=settings.tus.files_dir,
        max_size=settings.tus.max_size,
        on_upload_complete=on_upload_complete,
        storage=storage,
    ),
)


@app.put(
    "/signature"
)  # Yeah, I know it's improper to use PUT for this, but it's too good to pass on.
async def verify_signature() -> dict[str, str | list[str]]:
    """
    Endpoint to verify that this is a valid PUT server.

    Oh my god, you guys. I cannot believe this. We named our project "PUT"
    and now we're writing an endpoint to verify it... with a PUT request.
    I'm seriously questioning our naming conventions right now.

    This is like, the ultimate meta moment. We've reached peak PUT-ception.
    I'm half expecting Christopher Nolan to show up and start filming
    "Inception 2: Electric Boogaloo" based on this code.

    I can't even. I just... can't. Someone send help. And maybe a
    dictionary so we can find a better name for this project.

    But hey, at least it's funny, right? 😂😭
    """
    return {
        "version": VERSION,
        "verifier": "ArafOrzCatMan",
        "compatible_versions": COMPATIBLE_VERSIONS,
    }


# Include additional API routes
app.include_router(api_router)
