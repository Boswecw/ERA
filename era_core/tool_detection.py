from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from era_core.artifact_paths import utc_now_text


def _default_version_command(tool: str) -> list[str]:
    if tool == "python":
        return [sys.executable, "--version"]
    return [tool, "--version"]


def _probe_tool(tool: str, version_command: list[str], applicable: bool) -> dict[str, object]:
    if not applicable:
        return {
            "tool": tool,
            "status": "not_applicable",
            "version": None,
            "note": "Target manifests do not require this tool for the requested ERA lanes.",
        }

    executable = sys.executable if tool == "python" else shutil.which(tool)
    if not executable:
        return {
            "tool": tool,
            "status": "missing",
            "version": None,
            "note": f"{tool} was not found on PATH.",
        }

    try:
        completed = subprocess.run(
            version_command,
            capture_output=True,
            text=True,
            check=False,
        )
    except PermissionError:
        return {
            "tool": tool,
            "status": "permission_denied",
            "version": None,
            "note": f"Permission denied while probing {tool}.",
        }
    except OSError as exc:
        return {
            "tool": tool,
            "status": "failed_to_execute",
            "version": None,
            "note": str(exc),
        }

    if completed.returncode != 0:
        return {
            "tool": tool,
            "status": "failed_to_execute",
            "version": None,
            "note": completed.stderr.strip() or "Version probe failed.",
        }

    version = completed.stdout.strip() or completed.stderr.strip()
    return {
        "tool": tool,
        "status": "available",
        "version": version,
        "note": None,
    }


def build_tool_availability_report(
    repo_path: Path,
    repo_id: str,
    extra_tools: list[str] | None = None,
) -> dict[str, object]:
    has_cargo_manifest = (repo_path / "src-tauri" / "Cargo.toml").exists() or (repo_path / "Cargo.toml").exists()
    has_package_json = (repo_path / "package.json").exists()
    tools = [
        _probe_tool("git", ["git", "--version"], applicable=True),
        _probe_tool("python", [sys.executable, "--version"], applicable=True),
        _probe_tool("cargo", ["cargo", "--version"], applicable=has_cargo_manifest),
        _probe_tool("bun", ["bun", "--version"], applicable=has_package_json),
        _probe_tool("jscpd", ["jscpd", "--version"], applicable=has_package_json),
        _probe_tool("knip", ["knip", "--version"], applicable=has_package_json),
        _probe_tool("hyperfine", ["hyperfine", "--version"], applicable=True),
    ]
    existing = {item["tool"] for item in tools}
    for tool in extra_tools or []:
        if tool in existing:
            continue
        tools.append(_probe_tool(tool, _default_version_command(tool), applicable=True))
        existing.add(tool)
    return {
        "schema_version": "ERAToolAvailabilityReport.v1",
        "repo_id": repo_id,
        "repo_path": str(repo_path),
        "captured_at": utc_now_text(),
        "tools": tools,
    }
