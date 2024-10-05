import asyncio
from datetime import datetime

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from server.metadata import FileMetadata
from server.storages.base import File
from server.tus import create_api_router
from setting import create_storage, load_settings
from server.routes import router as api_router

VERSION = "1.0.1"
COMPATIBLE_VERSIONS = [VERSION]
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = load_settings("config.toml")
storage = create_storage(settings)


FILES_DIR = "content"

app.mount("/file", StaticFiles(directory=FILES_DIR), name="static")


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
        storage=storage,
        uid=metadata.uid,
    )

    asyncio.run(storage.upload(file, open(file_path, "rb")))


KB = 1024
MB = KB * 1024
GB = MB * 1024
TB = GB * 1024

app.include_router(
    create_api_router(
        files_dir=FILES_DIR,  # OPTIONAL
        max_size=120 * GB,  # OPTIONAL
        on_upload_complete=on_upload_complete,  # OPTIONAL
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
