import json
from io import BytesIO

import boto3
from botocore.client import Config

from app.config import settings


class StorageService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                config=Config(signature_version="s3v4"),
                region_name="us-east-1",
            )
            # Ensure bucket exists
            try:
                self._client.head_bucket(Bucket=settings.s3_bucket)
            except Exception:
                self._client.create_bucket(Bucket=settings.s3_bucket)
        return self._client

    async def upload_bytes(self, data: bytes, key: str) -> None:
        self.client.put_object(Bucket=settings.s3_bucket, Key=key, Body=data)

    async def upload_file(self, local_path: str, key: str) -> None:
        self.client.upload_file(local_path, settings.s3_bucket, key)

    async def download_to_file(self, key: str, local_path: str) -> None:
        self.client.download_file(settings.s3_bucket, key, local_path)

    async def download_json(self, key: str) -> dict:
        obj = self.client.get_object(Bucket=settings.s3_bucket, Key=key)
        return json.loads(obj["Body"].read())

    def upload_bytes_sync(self, data: bytes, key: str) -> None:
        self.client.put_object(Bucket=settings.s3_bucket, Key=key, Body=data)

    def upload_file_sync(self, local_path: str, key: str) -> None:
        self.client.upload_file(local_path, settings.s3_bucket, key)

    def download_to_file_sync(self, key: str, local_path: str) -> None:
        self.client.download_file(settings.s3_bucket, key, local_path)


storage = StorageService()
