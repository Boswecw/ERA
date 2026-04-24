from __future__ import annotations

import argparse
import getpass
import platform
from pathlib import Path
from typing import Any

from era_cli import __version__
from era_core.artifact_paths import (
    build_run_paths,
    ensure_run_dirs,
    generate_run_id,
    utc_now_text,
)
from era_core.command_runner import run_planned_commands
from era_core.git_info import (
    capture_git_snapshot,
    capture_target_manifest,
    collect_changed_files,
    detect_repo_id,
    ensure_git_repo,
    resolve_baseline_commit,
)
from era_core.hashing import sha256_json, sha256_path, write_json
from era_core.models import CommandResult
from era_core.review_writer import determine_accuracy_classification, write_review
from era_core.selection import (
    apply_selection_and_tooling,
    build_selection_artifact,
    detect_accuracy_commands,
)
from era_core.tool_detection import build_tool_availability_report
from era_core.validation import validate_run_dir
from era_integrations.centipede_export import write_centipede_export


def register(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", required=True, help="Target repository path")
    parser.add_argument("--lanes", required=True, help="Comma-separated ERA lanes")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["full", "changed-files"],
        help="Execution mode",
    )
    parser.add_argument("--baseline", help="Baseline ref for changed-files mode")
    parser.add_argument(
        "--artifacts-root",
        help="Override artifacts root for testing or local redirection",
    )
    parser.set_defaults(func=main)


def _build_raw_artifacts(run_id: str, command_results: list[CommandResult]) -> list[dict[str, Any]]:
    raw_artifacts: list[dict[str, Any]] = []
    for result in command_results:
        if not result.stdout_path or not result.stderr_path:
            continue
        for artifact_kind, path_value, sha_value in (
            ("stdout", result.stdout_path, result.stdout_sha256),
            ("stderr", result.stderr_path, result.stderr_sha256),
        ):
            raw_artifacts.append(
                {
                    "schema_version": "ToolRawArtifact.v1",
                    "raw_artifact_id": f"{result.command_id}:{artifact_kind}",
                    "run_id": run_id,
                    "command_id": result.command_id,
                    "tool_name": result.tool_name,
                    "tool_version": result.tool_version,
                    "artifact_kind": artifact_kind,
                    "path": path_value,
                    "sha256": sha_value,
                    "created_at": result.completed_at,
                }
            )
    return raw_artifacts


def _build_normalized_results(
    run_id: str,
    command_results: list[CommandResult],
    raw_artifacts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    raw_refs_by_command: dict[str, list[str]] = {}
    for artifact in raw_artifacts:
        raw_refs_by_command.setdefault(artifact["command_id"], []).append(artifact["raw_artifact_id"])

    normalized_results: list[dict[str, Any]] = []
    for result in command_results:
        if result.status in {"skipped", "blocked_by_missing_tool"}:
            continue
        parsed_findings: list[dict[str, Any]] = []
        if result.status in {"failed", "timed_out", "failed_to_execute"}:
            parsed_findings.append(
                {
                    "finding_type": "accuracy_gate_failed",
                    "command_id": result.command_id,
                    "label": result.label,
                    "exit_code": result.exit_code,
                    "status": result.status,
                }
            )
        record = {
            "schema_version": "ToolNormalizedResult.v1",
            "normalized_result_id": f"normalized:{result.command_id}",
            "run_id": run_id,
            "raw_artifact_refs": raw_refs_by_command.get(result.command_id, []),
            "normalizer_name": "era_command_normalizer",
            "normalizer_version": __version__,
            "tool_name": result.tool_name,
            "tool_version": result.tool_version,
            "summary_status": result.status,
            "parsed_findings": parsed_findings,
            "parse_warnings": [],
            "parse_errors": [],
            "created_at": result.completed_at,
        }
        record["sha256"] = sha256_json(record)
        normalized_results.append(record)
    return normalized_results


def _build_findings(
    run_id: str,
    repo_id: str,
    commit_sha: str,
    changed_files: list[str],
    normalized_results: list[dict[str, Any]],
    raw_artifacts: list[dict[str, Any]],
    created_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw_by_command: dict[str, list[dict[str, Any]]] = {}
    for artifact in raw_artifacts:
        raw_by_command.setdefault(artifact["command_id"], []).append(artifact)

    lane_drafts: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for normalized in normalized_results:
        if not normalized["parsed_findings"]:
            continue
        command_id = normalized["normalized_result_id"].split("normalized:", 1)[1]
        raw_refs = raw_by_command.get(command_id, [])
        target_files = changed_files[:] if changed_files else []
        draft = {
            "schema_version": "LaneFindingDraft.v1",
            "draft_id": f"draft:{command_id}",
            "run_id": run_id,
            "lane": "accuracy",
            "finding_type": "accuracy_gate_failed",
            "target_files": target_files,
            "target_symbols": [],
            "evidence_refs": [normalized["normalized_result_id"]],
            "risk_level": "high",
            "confidence": "high",
            "evidence_strength": "mechanical",
            "recommended_action": "operator_review",
            "blocked_reason": None,
            "created_at": created_at,
        }
        draft["sha256"] = sha256_json(draft)
        lane_drafts.append(draft)

        finding = {
            "schema_version": "ERAFinding.v1",
            "finding_id": f"finding:{command_id}",
            "run_id": run_id,
            "repo_id": repo_id,
            "commit_sha": commit_sha,
            "lane": "accuracy",
            "finding_type": "accuracy_gate_failed",
            "target_files": target_files,
            "target_symbols": [],
            "evidence_refs": [normalized["normalized_result_id"], draft["draft_id"]],
            "raw_evidence_refs": [item["raw_artifact_id"] for item in raw_refs],
            "raw_evidence_hashes": [item["sha256"] for item in raw_refs],
            "risk_level": "high",
            "confidence": "high",
            "evidence_strength": "mechanical",
            "recommended_action": "operator_review",
            "safe_to_autofix": False,
            "requires_operator_review": True,
            "operator_decision": "pending",
            "blocked_reason": None,
            "created_at": created_at,
        }
        finding["sha256"] = sha256_json(finding)
        findings.append(finding)

    return lane_drafts, findings


def _determine_read_only_invariant(
    pre_snapshot: dict[str, Any],
    post_snapshot: dict[str, Any],
) -> tuple[str, str]:
    if pre_snapshot["head"] != post_snapshot["head"]:
        return (
            "head_changed_during_run",
            "Target HEAD changed during the ERA run.",
        )
    if pre_snapshot["status_short"] == post_snapshot["status_short"]:
        if pre_snapshot["is_dirty"]:
            return (
                "preexisting_dirty_tree",
                "The target repository was already dirty before the run and remained unchanged.",
            )
        return ("clean_verified", "Pre-run and post-run git state matched.")
    return (
        "read_only_invariant_failed",
        "Post-run target git status differed from the pre-run snapshot.",
    )


def _determine_run_status(command_results: list[CommandResult], accuracy_classification: str) -> str:
    executed = [item for item in command_results if item.status not in {"skipped", "blocked_by_missing_tool"}]
    blocked = [item for item in command_results if item.status == "blocked_by_missing_tool"]
    skipped = [item for item in command_results if item.status == "skipped"]
    degraded = [item for item in command_results if item.status in {"failed_to_execute", "timed_out"}]
    if blocked and not executed:
        return "blocked"
    if blocked or skipped or degraded or accuracy_classification in {"unproven", "blocked_by_missing_evidence"}:
        return "completed_partial"
    return "completed"


def _build_hash_manifest(run_id: str, run_root: Path) -> dict[str, Any]:
    entries: list[dict[str, str]] = []
    for path in sorted(run_root.rglob("*")):
        if not path.is_file() or path.name == "hashes.json":
            continue
        entries.append(
            {
                "path": path.relative_to(run_root).as_posix(),
                "sha256": sha256_path(path),
            }
        )
    return {
        "schema_version": "ERAHashManifest.v1",
        "run_id": run_id,
        "entries": entries,
        "created_at": utc_now_text(),
    }


def execute_run(
    repo_path: Path,
    lanes: list[str],
    mode: str,
    baseline_ref: str | None = None,
    artifacts_root: Path | None = None,
) -> Path:
    if lanes != ["accuracy"]:
        raise ValueError("ERA-01A only supports the accuracy lane.")

    repo_path = repo_path.resolve()
    if not repo_path.exists():
        raise ValueError(f"Target repo path does not exist: {repo_path}")
    ensure_git_repo(repo_path)

    started_at = utc_now_text()
    run_id = generate_run_id()
    run_paths = build_run_paths(run_id, artifacts_root)
    ensure_run_dirs(run_paths)

    pre_snapshot = capture_git_snapshot(repo_path)
    repo_id = detect_repo_id(repo_path)
    target_manifest = capture_target_manifest(repo_path, repo_id, pre_snapshot)

    tool_report = build_tool_availability_report(repo_path, repo_id)
    tool_versions = {
        item["tool"]: item["version"]
        for item in tool_report["tools"]
        if item["status"] == "available"
    }
    baseline_commit = resolve_baseline_commit(repo_path, baseline_ref) if baseline_ref else None
    changed_files = collect_changed_files(repo_path, baseline_ref) if mode == "changed-files" else []
    selection_artifact = build_selection_artifact(
        run_id=run_id,
        repo_id=repo_id,
        baseline_ref=baseline_ref,
        baseline_commit=baseline_commit,
        current_commit=pre_snapshot["head"] or "UNCOMMITTED",
        mode=mode,
        changed_files=changed_files,
    )

    detected_commands = detect_accuracy_commands(repo_path)
    planned_commands = apply_selection_and_tooling(
        detected_commands,
        tool_report["tools"],
        selection_artifact,
    )
    command_results = run_planned_commands(planned_commands, run_paths.commands_dir, tool_versions)
    if mode == "changed-files":
        selection_artifact["full_run_executed"] = any(
            item.status not in {"skipped", "blocked_by_missing_tool"} for item in command_results
        )

    raw_artifacts = _build_raw_artifacts(run_id, command_results)
    normalized_results = _build_normalized_results(run_id, command_results, raw_artifacts)
    lane_drafts, findings = _build_findings(
        run_id=run_id,
        repo_id=repo_id,
        commit_sha=pre_snapshot["head"] or "UNCOMMITTED",
        changed_files=selection_artifact["changed_files"],
        normalized_results=normalized_results,
        raw_artifacts=raw_artifacts,
        created_at=utc_now_text(),
    )

    evidence_bundle = {
        "schema_version": "TestEvidenceBundle.v1",
        "run_id": run_id,
        "repo_id": repo_id,
        "lane": "accuracy",
        "command_results": [item.to_dict() for item in command_results],
        "tool_raw_artifacts": raw_artifacts,
        "tool_normalized_results": normalized_results,
        "created_at": utc_now_text(),
    }
    evidence_bundle["sha256"] = sha256_json(evidence_bundle)

    findings_bundle = {
        "schema_version": "ERAFindingSet.v1",
        "run_id": run_id,
        "repo_id": repo_id,
        "lane_finding_drafts": lane_drafts,
        "era_findings": findings,
        "created_at": utc_now_text(),
    }

    post_snapshot = capture_git_snapshot(repo_path)
    read_only_invariant_status, read_only_invariant_notes = _determine_read_only_invariant(
        pre_snapshot,
        post_snapshot,
    )
    accuracy_classification = determine_accuracy_classification(
        command_results,
        read_only_invariant_status,
    )
    completed_at = utc_now_text()
    run_status = _determine_run_status(command_results, accuracy_classification)

    run_artifact = {
        "schema_version": "ERAEvaluationRun.v1",
        "run_id": run_id,
        "repo_id": repo_id,
        "repo_path": str(repo_path),
        "commit_sha": pre_snapshot["head"] or "UNCOMMITTED",
        "branch": pre_snapshot["branch"],
        "working_tree_status": pre_snapshot["status_short"],
        "is_dirty": pre_snapshot["is_dirty"],
        "lanes": lanes,
        "mode": mode,
        "baseline_ref": baseline_ref,
        "baseline_commit": baseline_commit,
        "started_at": started_at,
        "completed_at": completed_at,
        "status": run_status,
        "operator_requested_by": getpass.getuser(),
        "runner_version": __version__,
        "tool_versions": tool_versions,
        "environment": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
        },
        "artifact_root": str(run_paths.root),
        "target_manifest_path": str(run_paths.target_manifest),
        "tool_availability_path": str(run_paths.tool_availability),
        "test_selection_artifact_path": (
            str(run_paths.test_selection) if mode == "changed-files" else None
        ),
        "evidence_bundle_refs": [str(run_paths.test_evidence_bundle)],
        "finding_refs": [str(run_paths.findings)],
        "review_artifact_ref": str(run_paths.review),
        "pre_run_git_status_short": pre_snapshot["status_short"],
        "post_run_git_status_short": post_snapshot["status_short"],
        "pre_run_head": pre_snapshot["head"],
        "post_run_head": post_snapshot["head"],
        "pre_run_dirty": pre_snapshot["is_dirty"],
        "post_run_dirty": post_snapshot["is_dirty"],
        "read_only_invariant_status": read_only_invariant_status,
        "read_only_invariant_notes": read_only_invariant_notes,
    }

    write_json(run_paths.target_manifest, target_manifest)
    write_json(run_paths.tool_availability, tool_report)
    if mode == "changed-files":
        write_json(run_paths.test_selection, selection_artifact)
    write_json(run_paths.test_evidence_bundle, evidence_bundle)
    write_json(run_paths.findings, findings_bundle)
    write_json(run_paths.run_json, run_artifact)

    write_centipede_export(
        run_artifact=run_artifact,
        selection_artifact=selection_artifact,
        evidence_bundle=evidence_bundle,
        findings=findings_bundle,
        output_path=run_paths.centipede_bundle,
    )
    write_review(
        run_artifact=run_artifact,
        target_manifest=target_manifest,
        tool_report=tool_report,
        selection_artifact=selection_artifact,
        evidence_bundle=evidence_bundle,
        accuracy_classification=accuracy_classification,
        output_path=run_paths.review,
    )

    hashes = _build_hash_manifest(run_id, run_paths.root)
    write_json(run_paths.hashes, hashes)

    validation = validate_run_dir(run_paths.root)
    if not validation["ok"]:
        raise RuntimeError("ERA wrote artifacts but validation failed.")

    return run_paths.root


def main(args: argparse.Namespace) -> int:
    artifacts_root = Path(args.artifacts_root).resolve() if args.artifacts_root else None
    run_dir = execute_run(
        repo_path=Path(args.repo),
        lanes=[item.strip() for item in args.lanes.split(",") if item.strip()],
        mode=args.mode,
        baseline_ref=args.baseline,
        artifacts_root=artifacts_root,
    )
    print(run_dir)
    return 0
