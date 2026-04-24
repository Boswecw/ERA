from __future__ import annotations

from collections import Counter
from typing import Any

from era_core.hashing import sha256_json
from era_core.models import CommandResult

_PARSED_FINDING_BASE_FIELDS = {
    "finding_type",
    "summary",
    "target_files",
    "target_symbols",
    "risk_level",
    "confidence",
    "evidence_strength",
    "recommended_action",
    "blocked_reason",
    "lane_details",
}


def _sorted_counts(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(value for value in values if value).items()))


def _merged_lane_details(parsed: dict[str, Any]) -> dict[str, Any] | None:
    merged = dict(parsed.get("lane_details") or {})
    for key, value in parsed.items():
        if key in _PARSED_FINDING_BASE_FIELDS:
            continue
        merged[key] = value
    return merged or None


def build_tool_raw_artifacts(
    run_id: str,
    command_results: list[CommandResult],
) -> list[dict[str, Any]]:
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


def build_tool_normalized_result(
    *,
    run_id: str,
    command_id: str,
    raw_artifact_refs: list[str],
    normalizer_name: str,
    normalizer_version: str,
    tool_name: str,
    tool_version: str | None,
    summary_status: str,
    parsed_findings: list[dict[str, Any]],
    parse_warnings: list[str],
    parse_errors: list[str],
    created_at: str,
) -> dict[str, Any]:
    payload = {
        "schema_version": "ToolNormalizedResult.v1",
        "normalized_result_id": f"normalized:{command_id}",
        "run_id": run_id,
        "raw_artifact_refs": raw_artifact_refs,
        "normalizer_name": normalizer_name,
        "normalizer_version": normalizer_version,
        "tool_name": tool_name,
        "tool_version": tool_version,
        "summary_status": summary_status,
        "parsed_findings": parsed_findings,
        "parse_warnings": parse_warnings,
        "parse_errors": parse_errors,
        "created_at": created_at,
    }
    payload["sha256"] = sha256_json(payload)
    return payload


def promote_normalized_results(
    *,
    run_id: str,
    repo_id: str,
    commit_sha: str,
    normalized_results: list[dict[str, Any]],
    raw_artifacts: list[dict[str, Any]],
    command_lanes: dict[str, str],
    default_target_files_by_lane: dict[str, list[str]] | None,
    created_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw_by_command: dict[str, list[dict[str, Any]]] = {}
    for artifact in raw_artifacts:
        raw_by_command.setdefault(artifact["command_id"], []).append(artifact)

    lane_drafts: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for normalized in normalized_results:
        parsed_findings = normalized.get("parsed_findings", [])
        if not parsed_findings:
            continue
        command_id = normalized["normalized_result_id"].split("normalized:", 1)[1]
        lane = command_lanes[command_id]
        raw_refs = raw_by_command.get(command_id, [])

        for index, parsed in enumerate(parsed_findings, start=1):
            lane_details = _merged_lane_details(parsed)
            target_files = parsed.get("target_files") or (default_target_files_by_lane or {}).get(lane, [])
            target_symbols = parsed.get("target_symbols") or []
            draft = {
                "schema_version": "LaneFindingDraft.v1",
                "draft_id": f"draft:{command_id}:{index}",
                "run_id": run_id,
                "lane": lane,
                "finding_type": parsed["finding_type"],
                "summary": parsed.get("summary"),
                "target_files": target_files,
                "target_symbols": target_symbols,
                "evidence_refs": [normalized["normalized_result_id"]],
                "risk_level": parsed["risk_level"],
                "confidence": parsed["confidence"],
                "evidence_strength": parsed["evidence_strength"],
                "recommended_action": parsed["recommended_action"],
                "blocked_reason": parsed.get("blocked_reason"),
                "created_at": created_at,
            }
            if lane_details:
                draft["lane_details"] = lane_details
            draft["sha256"] = sha256_json(draft)
            lane_drafts.append(draft)

            finding = {
                "schema_version": "ERAFinding.v1",
                "finding_id": f"finding:{command_id}:{index}",
                "run_id": run_id,
                "repo_id": repo_id,
                "commit_sha": commit_sha,
                "lane": lane,
                "finding_type": parsed["finding_type"],
                "summary": parsed.get("summary"),
                "target_files": target_files,
                "target_symbols": target_symbols,
                "evidence_refs": [normalized["normalized_result_id"], draft["draft_id"]],
                "raw_evidence_refs": [item["raw_artifact_id"] for item in raw_refs],
                "raw_evidence_hashes": [item["sha256"] for item in raw_refs],
                "risk_level": parsed["risk_level"],
                "confidence": parsed["confidence"],
                "evidence_strength": parsed["evidence_strength"],
                "recommended_action": parsed["recommended_action"],
                "safe_to_autofix": False,
                "requires_operator_review": True,
                "operator_decision": "accepted_exception" if lane_details and lane_details.get("exception_id") else "pending",
                "blocked_reason": parsed.get("blocked_reason"),
                "created_at": created_at,
            }
            if lane_details:
                finding["lane_details"] = lane_details
            finding["sha256"] = sha256_json(finding)
            findings.append(finding)

    return lane_drafts, findings


def build_era_scores(
    *,
    run_id: str,
    repo_id: str,
    commit_sha: str,
    lane_classifications: dict[str, str],
    command_results: list[CommandResult],
    lane_drafts: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    overall_classification: str,
    created_at: str,
) -> list[dict[str, Any]]:
    scores: list[dict[str, Any]] = []
    lane_names = sorted({item.lane for item in command_results} | set(lane_classifications))

    for lane in lane_names:
        lane_commands = [item for item in command_results if item.lane == lane]
        lane_draft_items = [item for item in lane_drafts if item["lane"] == lane]
        lane_findings = [item for item in findings if item["lane"] == lane]
        payload = {
            "schema_version": "ERAScore.v1",
            "score_id": f"score:lane:{lane}",
            "run_id": run_id,
            "repo_id": repo_id,
            "commit_sha": commit_sha,
            "scope": "lane",
            "lane": lane,
            "classification": lane_classifications.get(lane, "unproven"),
            "command_count": len(lane_commands),
            "draft_count": len(lane_draft_items),
            "finding_count": len(lane_findings),
            "command_status_counts": _sorted_counts([item.status for item in lane_commands]),
            "finding_type_counts": _sorted_counts([item["finding_type"] for item in lane_findings]),
            "risk_counts": _sorted_counts([item["risk_level"] for item in lane_findings]),
            "confidence_counts": _sorted_counts([item["confidence"] for item in lane_findings]),
            "evidence_strength_counts": _sorted_counts([item["evidence_strength"] for item in lane_findings]),
            "requires_operator_review_count": sum(1 for item in lane_findings if item["requires_operator_review"]),
            "safe_to_autofix_count": sum(1 for item in lane_findings if item["safe_to_autofix"]),
            "created_at": created_at,
        }
        payload["sha256"] = sha256_json(payload)
        scores.append(payload)

    overall = {
        "schema_version": "ERAScore.v1",
        "score_id": "score:overall",
        "run_id": run_id,
        "repo_id": repo_id,
        "commit_sha": commit_sha,
        "scope": "overall",
        "lane": None,
        "classification": overall_classification,
        "command_count": len(command_results),
        "draft_count": len(lane_drafts),
        "finding_count": len(findings),
        "command_status_counts": _sorted_counts([item.status for item in command_results]),
        "finding_type_counts": _sorted_counts([item["finding_type"] for item in findings]),
        "risk_counts": _sorted_counts([item["risk_level"] for item in findings]),
        "confidence_counts": _sorted_counts([item["confidence"] for item in findings]),
        "evidence_strength_counts": _sorted_counts([item["evidence_strength"] for item in findings]),
        "requires_operator_review_count": sum(1 for item in findings if item["requires_operator_review"]),
        "safe_to_autofix_count": sum(1 for item in findings if item["safe_to_autofix"]),
        "created_at": created_at,
    }
    overall["sha256"] = sha256_json(overall)
    scores.append(overall)
    return scores


def build_findings_bundle(
    *,
    run_id: str,
    repo_id: str,
    lane_drafts: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    era_scores: list[dict[str, Any]],
    created_at: str,
) -> dict[str, Any]:
    payload = {
        "schema_version": "ERAFindingSet.v1",
        "run_id": run_id,
        "repo_id": repo_id,
        "lane_finding_drafts": lane_drafts,
        "era_findings": findings,
        "era_scores": era_scores,
        "created_at": created_at,
    }
    payload["sha256"] = sha256_json(payload)
    return payload
