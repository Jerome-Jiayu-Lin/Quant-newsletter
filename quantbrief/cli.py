from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

from .archive import CardArchive
from .pipeline import Pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build today's Quant Brief knowledge cards")
    parser.add_argument("--config", type=Path, default=Path("config/sources.toml"))
    parser.add_argument("--output", type=Path, default=Path("web/data/cards.json"))
    parser.add_argument("--state", type=Path, default=Path("data/http-state.json"))
    parser.add_argument("--archive", type=Path, help="optionally append this edition to a local SQLite archive")
    parser.add_argument("--env-file", type=Path, help="load local provider settings without overwriting existing variables")
    parser.add_argument("--require-ai", action="store_true", help="fail instead of silently using source summaries")
    return parser


def load_env_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"environment file not found: {path}")
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"invalid environment entry at {path}:{line_number}")
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise ValueError(f"invalid environment key at {path}:{line_number}")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def main() -> None:
    args = build_parser().parse_args()
    if args.env_file:
        load_env_file(args.env_file)
    try:
        pipeline = Pipeline.configured(args.state, require_ai=args.require_ai)
    except ValueError as error:
        raise SystemExit(f"configuration error: {error}") from error
    report = pipeline.run(args.config, args.output)
    if args.archive:
        CardArchive(args.archive).ingest_file(args.output)
    print(f"fetched={report.fetched} unique={report.deduplicated} selected={report.selected}")
    for source, error in report.source_errors.items():
        print(f"warning[{source}] {error}")


if __name__ == "__main__":
    main()
