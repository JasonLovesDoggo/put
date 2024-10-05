import os
import json

from pydantic import BaseModel, Field

from server.metadata import FileMetadata


class PUTMetadata(BaseModel):
    uid: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Name of the file")
    metadata: dict = Field(
        default={}, description="Metadata associated with the object"
    )
    size: int = Field(..., description="Size of the object in bytes")
    created_at: int = Field(..., description="Creation timestamp")
    expires: int = Field(..., description="Expiration timestamp")


def _read_metadata(uid: str) -> FileMetadata | None:
    fpath = os.path.join("/home/json/PycharmProjects/put/static", uid, "meta.json")
    print(fpath)
    if not os.path.exists(fpath):
        return None
    with open(fpath, "r") as f:
        return PUTMetadata(**json.load(f))
