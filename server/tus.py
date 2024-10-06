import base64
import json
import os
from datetime import datetime, timedelta
from typing import Callable, Optional
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
from starlette.responses import StreamingResponse

from .metadata import FileMetadata


def default_auth():
    pass


def create_api_router(
    files_dir="/tmp/files",
    max_size=128849018880,
    on_upload_complete: Optional[Callable[[str, FileMetadata], None]] = None,
    auth: Optional[Callable[[], None]] = default_auth,
    days_to_keep: int = 5,
    prefix: str = "files",
    storage=None,
):
    router = APIRouter(prefix=f"/{prefix}")

    tus_version = "1.0.0"
    tus_extension = (
        "creation,creation-defer-length,creation-with-upload,expiration,termination"
    )

    def _ensure_dir(path):
        if not os.path.exists(path):
            os.makedirs(path)

    async def _write_chunk(request: Request, uuid: str) -> None:
        meta = _read_metadata(uuid)
        if not meta or not _file_exists(uuid):
            raise HTTPException(status_code=404, detail="Upload not found")

        file_path = os.path.join(files_dir, uuid)
        expected_offset = meta.offset

        upload_offset = int(request.headers.get("Upload-Offset", 0))
        if upload_offset != expected_offset:
            raise HTTPException(status_code=409, detail="Upload offset mismatch")

        max_chunk_size = max_size - meta.offset
        if max_chunk_size <= 0:
            raise HTTPException(
                status_code=413, detail="Upload exceeds maximum allowed size"
            )

        with open(file_path, "ab") as f:
            bytes_received = 0
            async for chunk in request.stream():
                chunk_size = len(chunk)
                if bytes_received + chunk_size > max_chunk_size:
                    chunk = chunk[: max_chunk_size - bytes_received]
                    f.write(chunk)
                    bytes_received += len(chunk)
                    meta.offset += len(chunk)
                    _write_metadata(meta)
                    raise HTTPException(
                        status_code=413, detail="Upload exceeds maximum allowed size"
                    )
                f.write(chunk)
                bytes_received += chunk_size
                meta.offset += chunk_size

        _write_metadata(meta)

    @router.head("/{uuid}", status_code=status.HTTP_200_OK)
    def get_upload_metadata(response: Response, uuid: str, _=Depends(auth)) -> Response:
        meta = _read_metadata(uuid)
        if meta is None or not _file_exists(uuid):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        response.headers["Tus-Resumable"] = tus_version
        response.headers["Upload-Length"] = (
            str(meta.size) if meta.size is not None else ""
        )
        response.headers["Upload-Offset"] = str(meta.offset)
        response.headers["Cache-Control"] = "no-store"
        if meta.metadata:
            upload_metadata = []
            for k, v in meta.metadata.items():
                encoded_value = base64.b64encode(v.encode("utf-8")).decode("utf-8")
                upload_metadata.append(f"{k} {encoded_value}")
            response.headers["Upload-Metadata"] = ",".join(upload_metadata)
        response.status_code = status.HTTP_200_OK
        return response

    @router.patch("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
    async def upload_chunk(
        request: Request,
        response: Response,
        uuid: str,
        content_type: str = Header(None),
        upload_offset: int = Header(...),
        _=Depends(auth),
    ) -> Response:
        if content_type != "application/offset+octet-stream":
            raise HTTPException(status_code=415, detail="Invalid Content-Type")

        await _write_chunk(request, uuid)

        meta = _read_metadata(uuid)

        response.headers["Tus-Resumable"] = tus_version
        response.headers["Upload-Offset"] = str(meta.offset)
        if meta.expires:
            response.headers["Upload-Expires"] = meta.expires
        response.status_code = status.HTTP_204_NO_CONTENT

        if not meta.defer_length and meta.size is not None and meta.offset == meta.size:
            if on_upload_complete:
                await on_upload_complete(os.path.join(files_dir, uuid), meta)

        return response

    @router.options("/", status_code=status.HTTP_204_NO_CONTENT)
    def options_create_upload(response: Response, __=Depends(auth)) -> Response:
        response.headers["Tus-Extension"] = tus_extension
        response.headers["Tus-Resumable"] = tus_version
        response.headers["Tus-Version"] = tus_version
        response.headers["Tus-Max-Size"] = str(max_size)
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @router.post("/", status_code=status.HTTP_201_CREATED)
    async def create_upload(
        request: Request,
        response: Response,
        upload_metadata: str = Header(None),
        upload_length: int = Header(None),
        upload_defer_length: int = Header(None),
        _=Depends(auth),
    ) -> Response:
        defer_length = upload_defer_length == "1"

        if upload_length is None and not defer_length:
            raise HTTPException(status_code=400, detail="Missing Upload-Length header")

        if upload_length is not None and int(upload_length) > max_size:
            raise HTTPException(
                status_code=413, detail="Upload exceeds maximum allowed size"
            )

        metadata = {}
        if upload_metadata:
            for kv_pair in upload_metadata.split(","):
                kv_pair = kv_pair.strip()
                if " " in kv_pair:
                    key, value = kv_pair.split(" ", 1)
                    value = base64.b64decode(value).decode("utf-8")
                else:
                    key = kv_pair
                    value = ""
                metadata[key] = value

        uuid = str(uuid4().hex)
        file_path = os.path.join(files_dir, uuid)
        _ensure_dir(files_dir)
        with open(file_path, "wb"):
            pass  # Create an empty file

        date_expiry = datetime.utcnow() + timedelta(days=days_to_keep)
        meta = FileMetadata(
            uid=uuid,
            size=int(upload_length) if upload_length is not None else None,
            offset=0,
            metadata=metadata,
            created_at=datetime.utcnow().isoformat(),
            defer_length=defer_length,
            expires=date_expiry.isoformat(),
        )
        _write_metadata(meta)

        response.headers["Location"] = _build_location_url(request=request, uuid=uuid)
        response.headers["Tus-Resumable"] = tus_version
        response.status_code = status.HTTP_201_CREATED
        return response

    @router.options("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
    def options_upload_chunk(
        response: Response, uuid: str, _=Depends(auth)
    ) -> Response:
        meta = _read_metadata(uuid)
        if meta is None or not _file_exists(uuid):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        response.headers["Tus-Extension"] = tus_extension
        response.headers["Tus-Resumable"] = tus_version
        response.headers["Tus-Version"] = tus_version
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @router.get("/{uuid}")
    async def get_upload(uuid: str) -> StreamingResponse:
        file_path = os.path.join(files_dir, uuid)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        meta = _read_metadata(uuid)
        if not meta:
            raise HTTPException(status_code=404, detail="Metadata not found")

        file_size = os.path.getsize(file_path)
        file = open(file_path, "rb")

        response = StreamingResponse(
            file,
            media_type=meta.metadata.get("mime_type", "application/octet-stream"),
        )
        filename = meta.metadata.get("filename", uuid)
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.headers["Content-Length"] = str(file_size)
        response.headers["Tus-Resumable"] = tus_version
        return response

    @router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_upload(uuid: str, response: Response, _=Depends(auth)) -> Response:
        file_path = os.path.join(files_dir, uuid)
        meta_path = os.path.join(files_dir, f"{uuid}.info")
        if not os.path.exists(file_path) and not os.path.exists(meta_path):
            raise HTTPException(status_code=404, detail="Upload not found")

        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(meta_path):
            os.remove(meta_path)

        response.headers["Tus-Resumable"] = tus_version
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    def _write_metadata(meta: FileMetadata) -> None:
        _ensure_dir(files_dir)
        with open(os.path.join(files_dir, f"{meta.uid}.info"), "w") as f:
            json.dump(meta.dict(), f)

    def _read_metadata(uid: str) -> Optional[FileMetadata]:
        meta_path = os.path.join(files_dir, f"{uid}.info")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                data = json.load(f)
                return FileMetadata(**data)
        return None

    def _file_exists(uid: str) -> bool:
        return os.path.exists(os.path.join(files_dir, uid))

    def _build_location_url(request: Request, uuid: str) -> str:
        proto = request.headers.get("X-Forwarded-Proto", request.url.scheme)
        host = request.headers.get("X-Forwarded-Host", request.headers.get("host"))
        base_url = f"{proto}://{host}"
        return f"{base_url}/{prefix}/{uuid}"

    return router
