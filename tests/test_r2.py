from __future__ import annotations

import os
import unittest
from io import BytesIO
from unittest.mock import patch

from quantbrief.publication import StorageConflict
from quantbrief.r2 import R2ObjectStorage


class ClientError(Exception):
    def __init__(self, code: str) -> None:
        self.response = {"Error": {"Code": code}}


class FakeS3Client:
    def __init__(self) -> None:
        self.get_response: dict[str, object] | Exception = ClientError("NoSuchKey")
        self.put_response: dict[str, object] | Exception = {"ETag": '"new"'}
        self.put_request: dict[str, object] | None = None

    def get_object(self, **kwargs: object) -> dict[str, object]:
        if isinstance(self.get_response, Exception):
            raise self.get_response
        return self.get_response

    def put_object(self, **kwargs: object) -> dict[str, object]:
        self.put_request = kwargs
        if isinstance(self.put_response, Exception):
            raise self.put_response
        return self.put_response


class R2ObjectStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = FakeS3Client()
        self.storage = R2ObjectStorage(self.client, "preview-bucket")

    def test_missing_object_returns_none(self) -> None:
        self.assertIsNone(self.storage.read("missing.json"))

    def test_read_preserves_r2_etag_as_conditional_version(self) -> None:
        self.client.get_response = {"Body": BytesIO(b"payload"), "ETag": '"etag-1"'}
        stored = self.storage.read("edition.json")
        self.assertEqual(stored.body, b"payload")  # type: ignore[union-attr]
        self.assertEqual(stored.version, '"etag-1"')  # type: ignore[union-attr]

    def test_create_uses_if_none_match(self) -> None:
        stored = self.storage.write("edition.json", b"{}", None)
        self.assertEqual(self.client.put_request["IfNoneMatch"], "*")  # type: ignore[index]
        self.assertNotIn("IfMatch", self.client.put_request)  # type: ignore[operator]
        self.assertEqual(stored.version, '"new"')

    def test_replace_uses_if_match(self) -> None:
        self.storage.write("index.json", b"{}", '"etag-1"')
        self.assertEqual(self.client.put_request["IfMatch"], '"etag-1"')  # type: ignore[index]
        self.assertNotIn("IfNoneMatch", self.client.put_request)  # type: ignore[operator]

    def test_precondition_failure_maps_to_storage_conflict(self) -> None:
        self.client.put_response = ClientError("PreconditionFailed")
        with self.assertRaises(StorageConflict):
            self.storage.write("index.json", b"{}", '"stale"')

    def test_environment_configuration_reports_every_missing_secret(self) -> None:
        names = ("CLOUDFLARE_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME")
        with patch.dict(os.environ, {name: "" for name in names}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "CLOUDFLARE_ACCOUNT_ID.*R2_BUCKET_NAME"):
                R2ObjectStorage.from_environment()


if __name__ == "__main__":
    unittest.main()
