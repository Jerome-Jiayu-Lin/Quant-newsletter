"""Cloudflare R2 adapter for the provider-independent publication interface."""

from __future__ import annotations

import os
from typing import Any, Mapping, Protocol

from .publication import StorageConflict, StoredObject


class S3Client(Protocol):
    def get_object(self, **kwargs: Any) -> Mapping[str, Any]: ...

    def put_object(self, **kwargs: Any) -> Mapping[str, Any]: ...


def _error_code(error: Exception) -> str | None:
    response = getattr(error, "response", None)
    if not isinstance(response, Mapping):
        return None
    details = response.get("Error")
    if not isinstance(details, Mapping):
        return None
    code = details.get("Code")
    return str(code) if code is not None else None


class R2ObjectStorage:
    """Translate the publication storage protocol to R2's S3-compatible API."""

    def __init__(self, client: S3Client, bucket: str) -> None:
        if not bucket.strip():
            raise ValueError("R2 bucket name is required")
        self.client = client
        self.bucket = bucket

    @classmethod
    def from_environment(cls) -> "R2ObjectStorage":
        required = {
            name: os.environ.get(name, "").strip()
            for name in ("CLOUDFLARE_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME")
        }
        missing = sorted(name for name, value in required.items() if not value)
        if missing:
            raise RuntimeError(f"missing R2 publication settings: {', '.join(missing)}")
        try:
            import boto3
        except ImportError as error:
            raise RuntimeError("install the publication dependency with: pip install '.[publication]'") from error
        client = boto3.client(
            "s3",
            endpoint_url=f"https://{required['CLOUDFLARE_ACCOUNT_ID']}.r2.cloudflarestorage.com",
            aws_access_key_id=required["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=required["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
        )
        return cls(client, required["R2_BUCKET_NAME"])

    def read(self, key: str) -> StoredObject | None:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
        except Exception as error:
            if _error_code(error) in {"NoSuchKey", "404", "NotFound"}:
                return None
            raise
        body = response["Body"].read()
        etag = str(response["ETag"])
        return StoredObject(body=body, version=etag)

    def write(self, key: str, body: bytes, expected_version: str | None) -> StoredObject:
        request: dict[str, Any] = {
            "Bucket": self.bucket,
            "Key": key,
            "Body": body,
            "ContentType": "application/json; charset=utf-8",
        }
        if expected_version is None:
            request["IfNoneMatch"] = "*"
        else:
            request["IfMatch"] = expected_version
        try:
            response = self.client.put_object(**request)
        except Exception as error:
            if _error_code(error) in {"PreconditionFailed", "ConditionalRequestConflict", "409", "412"}:
                raise StorageConflict(key) from error
            raise
        return StoredObject(body=body, version=str(response["ETag"]))
