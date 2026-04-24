from __future__ import annotations

import argparse
import sys
from pathlib import Path

from era_cli.commands import report, run, validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="era_cli", description="ERA local proof CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Execute an ERA run")
    run.register(run_parser)

    report_parser = subparsers.add_parser("report", help="Print a review artifact")
    report.register(report_parser)

    validate_parser = subparsers.add_parser("validate", help="Validate a run artifact set")
    validate.register(validate_parser)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:  # pragma: no cover - top-level error boundary
        print(str(exc), file=sys.stderr)
        return 1
