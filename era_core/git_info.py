from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from era_core.artifact_paths import utc_now_text
from era_core.hashing import sha256_path


class GitError(RuntimeError):
    pass


def _run_git(repo_path: Path, args: list[str], allow_failure: bool = False) -> str | None:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        if allow_failure:
            return None
        raise GitError(completed.stderr.strip() or "git command failed")
    return completed.stdout.strip()


def ensure_git_repo(repo_path: Path) -> None:
    inside = _run_git(repo_path, ["rev-parse", "--is-inside-work-tree"], allow_failure=True)
    if inside != "true":
        raise ValueError(f"Target path is not a git repository: {repo_path}")


def capture_git_snapshot(repo_path: Path) -> dict[str, Any]:
    status_short = _run_git(repo_path, ["status", "--short"], allow_failure=False) or ""
    head = _run_git(repo_path, ["rev-parse", "HEAD"], allow_failure=True)
    branch = _run_git(repo_path, ["branch", "--show-current"], allow_failure=True) or "(detached)"
    return {
        "captured_at": utc_now_text(),
        "head": head,
        "branch": branch,
        "status_short": status_short,
        "is_dirty": bool(status_short.strip()),
    }


def detect_repo_id(repo_path: Path) -> str:
    origin = _run_git(repo_path, ["remote", "get-url", "origin"], allow_failure=True)
    return origin or repo_path.name


def resolve_baseline_commit(repo_path: Path, baseline_ref: str | None) -> str | None:
    if not baseline_ref:
        return None
    return _run_git(repo_path, ["rev-parse", baseline_ref], allow_failure=True)


def collect_changed_files(repo_path: Path, baseline_ref: str | None) -> list[str]:
    changed: set[str] = set()
    if baseline_ref:
        committed = _run_git(
            repo_path,
            ["diff", "--name-only", f"{baseline_ref}...HEAD"],
            allow_failure=True,
        )
        if committed:
            changed.update(line for line in committed.splitlines() if line.strip())

    for args in (
        ["diff", "--name-only"],
        ["diff", "--name-only", "--cached"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        output = _run_git(repo_path, args, allow_failure=True)
        if output:
            changed.update(line for line in output.splitlines() if line.strip())

    return sorted(changed)


def _collect_lockfile_hashes(repo_path: Path) -> dict[str, str]:
    lockfiles = (
        "bun.lock",
        "package-lock.json",
        "Cargo.lock",
        "pnpm-lock.yaml",
        "yarn.lock",
        "poetry.lock",
        "uv.lock",
        "requirements.txt",
    )
    hashes: dict[str, str] = {}
    for name in lockfiles:
        candidate = repo_path / name
        if candidate.exists():
            hashes[name] = sha256_path(candidate)
    return hashes


def _detect_languages(repo_path: Path) -> list[str]:
    languages: list[str] = []
    if (repo_path / "src-tauri" / "Cargo.toml").exists() or (repo_path / "Cargo.toml").exists():
        languages.append("rust")
    if (repo_path / "package.json").exists():
        languages.append("javascript")
    if (repo_path / "tsconfig.json").exists():
        languages.append("typescript")
    if (repo_path / "pyproject.toml").exists():
        languages.append("python")
    return languages


def _detect_toolchains(repo_path: Path) -> list[str]:
    toolchains = ["git", "python"]
    if (repo_path / "src-tauri" / "Cargo.toml").exists() or (repo_path / "Cargo.toml").exists():
        toolchains.append("cargo")
    if (repo_path / "package.json").exists():
        toolchains.append("bun")
    return toolchains


def capture_target_manifest(
    repo_path: Path,
    repo_id: str,
    snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repo_snapshot = snapshot or capture_git_snapshot(repo_path)
    if not repo_snapshot["head"] and not repo_snapshot["is_dirty"]:
        raise ValueError("Target manifest requires a commit SHA or a dirty working tree marker.")

    return {
        "schema_version": "ERATargetManifest.v1",
        "repo_path": str(repo_path),
        "repo_name": repo_path.name,
        "repo_id": repo_id,
        "git_commit_sha": repo_snapshot["head"] or "UNCOMMITTED",
        "git_branch": repo_snapshot["branch"],
        "working_tree_status": repo_snapshot["status_short"],
        "is_dirty": repo_snapshot["is_dirty"],
        "lockfile_hashes": _collect_lockfile_hashes(repo_path),
        "detected_languages": _detect_languages(repo_path),
        "detected_toolchains": _detect_toolchains(repo_path),
        "captured_at": utc_now_text(),
    }
