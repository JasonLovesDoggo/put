import boto3
from botocore.exceptions import ClientError
import io
from dataclasses import dataclass
from datetime import datetime
from typing import BinaryIO, List, Optional

from server.storages.base import File, SortOrder, OrderBy


@dataclass
class S3Settings:
    """
    S3-compatible implementation of the Storage protocol.
    """

    bucket_name: str
    secret_access_key: str
    access_key_id: str
    endpoint_url: str
    region_name: str


class S3Storage:
    """
    S3-compatible implementation of the Storage protocol.
    """

    def __init__(self, settings: S3Settings) -> None:
        if settings.bucket_name:
            self.bucket_name = settings.bucket_name
        self.s3 = boto3.client(
            settings.endpoint_url,
            region_name=settings.region_name,
            aws_access_key_id=settings.access_key_id,
            aws_secret_access_key=settings.secret_access_key,
        )

    async def upload(self, file: File, data: BinaryIO) -> None:
        try:
            self.s3.upload_fileobj(
                data,
                self.bucket_name,
                file.uid,
                ExtraArgs={
                    "Metadata": file.metadata,
                    "ContentLength": file.size,
                },
            )
        except ClientError as e:
            print(f"Error uploading file: {e}")
            raise

    async def download(self, uid: str) -> tuple[File, BinaryIO]:
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=uid)
            file = File(
                uid=uid,
                metadata=response["Metadata"],
                size=response["ContentLength"],
                created_at=int(response["LastModified"].timestamp()),
                storage=self.__class__,
            )
            data = io.BytesIO(response["Body"].read())
            return file, data
        except ClientError as e:
            print(f"Error downloading file: {e}")
            raise

    async def delete(self, uid: str) -> None:
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=uid)
        except ClientError as e:
            print(f"Error deleting file: {e}")
            raise

    async def get(self, uid: str) -> File:
        try:
            response = self.s3.head_object(Bucket=self.bucket_name, Key=uid)
            return File(
                uid=uid,
                metadata=response["Metadata"],
                size=response["ContentLength"],
                created_at=int(response["LastModified"].timestamp()),
                storage=self,
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundError(f"File with UID {uid} not found")
            else:
                print(f"Error retrieving file metadata: {e}")
                raise

    async def list(
        self,
        prefix: str = "",
        limit: int = 10,
        offset: int = 0,
        sort_by: OrderBy = "created_at",
        sort_order: SortOrder = SortOrder.DESC,
    ) -> List[File] | None:
        try:
            paginator = self.s3.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)

            files = []
            for page in page_iterator:
                for obj in page.get("Contents", []):
                    files.append(
                        File(
                            uid=obj["Key"],
                            metadata={},  # We need to fetch metadata separately
                            size=obj["Size"],
                            created_at=int(obj["LastModified"].timestamp()),
                            storage=self,
                        )
                    )

            # Apply sorting
            if sort_by == "created_at":
                files.sort(
                    key=lambda x: x.created_at, reverse=(sort_order == SortOrder.DESC)
                )
            elif sort_by == "size":
                files.sort(key=lambda x: x.size, reverse=(sort_order == SortOrder.DESC))
            elif sort_by == "name":
                files.sort(key=lambda x: x.uid, reverse=(sort_order == SortOrder.DESC))

            # Apply offset and limit
            files = files[offset : offset + limit]

            return files if files else None
        except ClientError as e:
            print(f"Error listing files: {e}")
            raise

    async def search(
        self,
        query: str = "",
        file_type: Optional[str] = None,
        owner: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 10,
        offset: int = 0,
        sort_by: OrderBy = "created_at",
        sort_order: SortOrder = SortOrder.DESC,
    ) -> List[File] | None:
        try:
            # Note: S3 doesn't provide a built-in search functionality.
            # This implementation will fetch all objects and filter them in memory.
            # For large datasets, this approach may not be efficient.

            all_files = self.list(limit=1000000)  # Fetch all files
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
        except ClientError as e:
            print(f"Error searching files: {e}")
            raise
