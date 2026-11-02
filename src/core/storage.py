import asyncio
from functools import cached_property
from pathlib import Path

import boto3
from botocore.config import Config

from core.config import settings


class ExportStorage:
    """Export files in S3."""

    @cached_property
    def _client(self):
        """Created on first use, so importing this module never looks up AWS credentials."""
        config = Config(s3={"addressing_style": "virtual"})
        return boto3.client("s3", region_name=settings.S3_REGION, config=config)

    async def put_file(self, key: str, path: Path) -> None:
        """Upload a file."""
        await asyncio.to_thread(self._client.upload_file, str(path), settings.S3_BUCKET, key)

    def download_url(self, key: str) -> str:
        """A link to download the file; it expires after an hour."""
        return self._client.generate_presigned_url(
            "get_object", Params={"Bucket": settings.S3_BUCKET, "Key": key}
        )


storage = ExportStorage()
