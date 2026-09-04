"""Shared operator and automation entry point for public Edition publication."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .publication import ObjectStorage, PublicationReceipt, Publisher
from .r2 import R2ObjectStorage


def publish_snapshot(
    snapshot_path: Path,
    storage: ObjectStorage,
    *,
    deployment_identifier: str | None = None,
    published_at: str | None = None,
) -> PublicationReceipt:
    snapshot: Mapping[str, Any] = json.loads(snapshot_path.read_text(encoding="utf-8-sig"))
    timestamp = published_at or datetime.now(timezone.utc).isoformat()
    return Publisher(storage).publish(
        snapshot, published_at=timestamp, deployment_identifier=deployment_identifier,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publish one canonical Edition Snapshot to R2")
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--deployment-identifier")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not args.snapshot.is_file():
        raise SystemExit(f"Edition Snapshot not found: {args.snapshot}")
    receipt = publish_snapshot(
        args.snapshot,
        R2ObjectStorage.from_environment(),
        deployment_identifier=args.deployment_identifier,
    )
    print(json.dumps(receipt.as_dict(), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
