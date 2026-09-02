"""Restore the public history index to a previously verified publication state."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .publication import ObjectStorage, Publisher, RestoreReceipt
from .r2 import R2ObjectStorage


def restore_publication(
    index_hash: str,
    storage: ObjectStorage,
    *,
    deployment_identifier: str | None = None,
    restored_at: str | None = None,
    receipt_path: Path | None = None,
) -> RestoreReceipt:
    receipt = Publisher(storage).restore(
        index_hash, restored_at=restored_at or datetime.now(timezone.utc).isoformat(),
        deployment_identifier=deployment_identifier,
    )
    if receipt_path is not None:
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt.as_dict(), indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore a verified public history index")
    parser.add_argument("index_hash")
    parser.add_argument("--deployment-identifier")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    receipt = restore_publication(
        args.index_hash, R2ObjectStorage.from_environment(),
        deployment_identifier=args.deployment_identifier, receipt_path=args.receipt,
    )
    print(json.dumps(receipt.as_dict(), sort_keys=True))


if __name__ == "__main__":
    main()
