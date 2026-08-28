from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import Pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build today's Quant Brief knowledge cards")
    parser.add_argument("--config", type=Path, default=Path("config/sources.toml"))
    parser.add_argument("--output", type=Path, default=Path("web/data/cards.json"))
    parser.add_argument("--state", type=Path, default=Path("data/http-state.json"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report = Pipeline.configured(args.state).run(args.config, args.output)
    print(f"fetched={report.fetched} unique={report.deduplicated} selected={report.selected}")
    for source, error in report.source_errors.items():
        print(f"warning[{source}] {error}")


if __name__ == "__main__":
    main()

