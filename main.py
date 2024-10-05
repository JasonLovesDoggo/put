import asyncio
from datetime import datetime
from tempfile import mkdtemp

from aiofiles import os as aios
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from server.metadata import FileMetadata
from server.routes import router as api_router
from server.storages import LocalStorage, S3Storage
from server.storages.base import File
from server.tus import create_api_router
from setting import settings
import logging

VERSION = "1.0.1"
COMPATIBLE_VERSIONS = [VERSION]

if settings.storage_type == "local":
    storage = LocalStorage()
else:
    storage = S3Storage(
        bucket_name=settings.s3_storage.bucket_name,
        endpoint_url=settings.s3_storage.endpoint_url,
        region_name=settings.s3_storage.region_name,
        access_key_id=settings.s3_storage.access_key_id,
        secret_access_key=settings.s3_storage.secret_access_key,
    )

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_headers=settings.api.cors_headers,
)

# Configure logging

logging.basicConfig(level=settings.logging.level, format=settings.logging.format)

# Use settings in your TUS implementation
tus_config = {
    "max_size": settings.tus.max_size,
    "expiration_period": settings.tus.expiration_period,
}


def on_upload_complete(file_path: str, metadata: FileMetadata) -> None:
    print(f"Upload complete: {file_path}")
    print(f"Metadata: {metadata}")

    from_timestamp = lambda string, datestring: int(  # noqa: E731
        datetime.strptime(string, datestring).timestamp()
    )

    print("E")
    file = File(
        name=metadata.metadata["filename"],
        created_at=from_timestamp(metadata.created_at, "%Y-%m-%d %H:%M:%S.%f"),
        expires=from_timestamp(metadata.expires, "%Y-%m-%dT%H:%M:%S.%f"),
        size=metadata.size,
        uid=metadata.uid,
    )

    asyncio.run(
        post_upload(
            file,
            file_path,
        )
    )


async def post_upload(file, filepath):
    print(f"Uploading file: {filepath}")
    await storage.upload(
        file_path=filepath, category="unsorted", mime_type="application/octet-stream"
    )

    await aios.remove(filepath)
    await aios.remove(filepath + ".info")


KB = 1024
MB = KB * 1024
GB = MB * 1024

app.include_router(
    create_api_router(
        files_dir=mkdtemp(),
        max_size=settings.tus.max_size * GB,
        on_upload_complete=on_upload_complete,
    ),
)


# Add a health check endpoint
@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


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


app.include_router(api_router)
