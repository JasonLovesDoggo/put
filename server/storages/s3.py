import io
from dataclasses import dataclass
from datetime import datetime
from typing import BinaryIO, List, Optional

import boto3
from botocore.exceptions import ClientError

from .base import AbstractStorage, File, OrderBy, SortOrder


@dataclass
class S3Settings:
    bucket_name: str
    secret_access_key: str
    access_key_id: str
    endpoint_url: str
    region_name: str


class S3Storage(AbstractStorage):
    def __init__(self, settings: S3Settings):
        self.bucket_name = settings.bucket_name
        self.s3 = boto3.client(
            "s3",
            endpoint_url=settings.endpoint_url,
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
            raise IOError(f"Error uploading file: {e}")

    async def download(self, uid: str) -> tuple[File, BinaryIO]:
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=uid)
            file = File(
                uid=uid,
                name=response["Metadata"].get("filename", uid),
                metadata=response["Metadata"],
                size=response["ContentLength"],
                created_at=int(response["LastModified"].timestamp()),
            )
            data = io.BytesIO(response["Body"].read())
            return file, data
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundError(f"File with UID {uid} not found")
            raise IOError(f"Error downloading file: {e}")

    async def delete(self, uid: str) -> None:
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=uid)
        except ClientError as e:
            raise IOError(f"Error deleting file: {e}")

    async def get(self, uid: str) -> File:
        try:
            response = self.s3.head_object(Bucket=self.bucket_name, Key=uid)
            return File(
                uid=uid,
                name=response["Metadata"].get("filename", uid),
                metadata=response["Metadata"],
                size=response["ContentLength"],
                created_at=int(response["LastModified"].timestamp()),
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundError(f"File with UID {uid} not found")
            raise IOError(f"Error retrieving file metadata: {e}")

    async def list(
        self,
        prefix: str = "",
        limit: int = 10,
        offset: int = 0,
        sort_by: OrderBy = "created_at",
        sort_order: SortOrder = SortOrder.DESC,
    ) -> List[File]:
        try:
            paginator = self.s3.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)

            files = []
            for page in page_iterator:
                for obj in page.get("Contents", []):
                    files.append(
                        File(
                            uid=obj["Key"],
                            name=obj["Key"].split("/")[-1],
                            metadata={},
                            size=obj["Size"],
                            created_at=int(obj["LastModified"].timestamp()),
                        )
                    )

            files.sort(
                key=lambda x: getattr(x, sort_by),
                reverse=(sort_order == SortOrder.DESC),
            )

            return files[offset : offset + limit]
        except ClientError as e:
            raise IOError(f"Error listing files: {e}")

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
    ) -> List[File]:
        # Implement search functionality
        # This is a basic implementation and might not be efficient for large datasets
        all_files = await self.list(limit=1000000)
        filtered_files = [
            f
            for f in all_files
            if (not query or query.lower() in f.name.lower())
            and (not file_type or f.name.lower().endswith(file_type.lower()))
            and (not owner or f.metadata.get("owner") == owner)
            and (not created_after or f.created_at >= created_after.timestamp())
            and (not created_before or f.created_at <= created_before.timestamp())
        ]

        filtered_files.sort(
            key=lambda x: getattr(x, sort_by), reverse=(sort_order == SortOrder.DESC)
        )

        return filtered_files[offset : offset + limit]
