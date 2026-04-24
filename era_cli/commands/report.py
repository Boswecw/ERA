from __future__ import annotations

import argparse
from pathlib import Path

from era_core.artifact_paths import default_artifacts_root, find_latest_run


def register(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--latest", action="store_true", help="Report on the latest run")
    parser.add_argument("--run-id", help="Explicit run id")
    parser.add_argument("--artifacts-root", help="Override artifacts root")
    parser.set_defaults(func=main)


def _resolve_run_dir(run_id: str | None, latest: bool, artifacts_root: Path) -> Path:
    if run_id:
        run_dir = artifacts_root / run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"Run id not found: {run_id}")
        return run_dir
    if latest:
        return find_latest_run(artifacts_root)
    raise ValueError("Provide --latest or --run-id.")


def main(args: argparse.Namespace) -> int:
    artifacts_root = (
        Path(args.artifacts_root).resolve()
        if args.artifacts_root
        else default_artifacts_root()
    )
    run_dir = _resolve_run_dir(args.run_id, args.latest, artifacts_root)
    review_path = run_dir / "review.md"
    print(review_path.read_text(encoding="utf-8"))
    return 0
