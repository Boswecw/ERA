from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from era_core.hashing import write_json


_PRODUCER_ID = "era-cli"
_CENTIPEDE_BUNDLE_SCHEMA = "centipede.intake.v1"
_CENTIPEDE_RECORD_SCHEMA = "centipede.v1"
_CENTIPEDE_EVIDENCE_SCHEMA = "centipede.evidence_bundle.v1"


class CentipedeValidationResult(dict):
    """Dict-compatible and list-compatible validation result.

    Some callers inspect result["ok"]. Older validation call sites may also
    extend an error list with the return value directly. Iterating over this
    object yields only error strings, never dictionary keys.
    """

    def __iter__(self):
        return iter(self.get("errors", []))

    def __len__(self) -> int:
        return len(self.get("errors", []))

    def __bool__(self) -> bool:
        return bool(self.get("errors", []))


def _validation_result(ok: bool, errors: list[str]) -> CentipedeValidationResult:
    return CentipedeValidationResult({"ok": ok, "errors": errors})


def _sha_prefix(value: str | None) -> str:
    if not value:
        return "sha256:missing"
    return value if value.startswith("sha256:") else f"sha256:{value}"


def _runtime_mode(status: str | None) -> str:
    mapping = {
        "completed": "completed",
        "completed_partial": "completed_partial",
        "failed": "failed",
        "blocked": "completed_partial",
        "aborted": "aborted",
    }
    return mapping.get(status or "", "completed_partial")


def _lane_name(lane: str) -> str:
    return f"era_{lane}"


def _lane_health_from_status(status: str | None) -> str:
    if status in {"completed", "passed"}:
        return "available"
    if status in {"blocked", "blocked_by_missing_tool", "blocked_by_missing_evidence"}:
        return "unavailable"
    if status in {"failed", "failed_to_execute", "timed_out", "completed_partial"}:
        return "degraded"
    return "degraded"


def _disposition_from_command_status(status: str | None) -> str:
    if status == "passed":
        return "passed"
    if status in {"blocked_by_missing_tool", "blocked_by_unsupported_version"}:
        return "blocked"
    if status == "skipped":
        return "skipped"
    if status in {"failed", "failed_to_execute", "timed_out"}:
        return "failed"
    return status or "unknown"


def _confidence_from_finding(confidence: str | None) -> str:
    mapping = {
        "exact": "exact",
        "high": "high",
        "moderate": "moderate",
        "medium": "moderate",
        "low": "low",
        "none": "none",
    }
    return mapping.get((confidence or "").lower(), "moderate")


def _observed_at(run_artifact: dict[str, Any]) -> str:
    return run_artifact.get("completed_at") or run_artifact.get("started_at")


def _revision_anchor(run_artifact: dict[str, Any]) -> str:
    return run_artifact.get("commit_sha") or "UNCOMMITTED"


def _run_created(run_artifact: dict[str, Any]) -> dict[str, Any]:
    run_id = run_artifact["run_id"]
    lanes = ",".join(run_artifact.get("lanes", [])) or "unknown"
    mode = run_artifact.get("mode") or "unknown"
    return {
        "record_id": f"era-run:{run_id}",
        "record_type": "centipede.run_created",
        "schema_version": _CENTIPEDE_RECORD_SCHEMA,
        "repository_id": run_artifact["repo_id"],
        "revision_anchor": _revision_anchor(run_artifact),
        "run_id": run_id,
        "observed_at": run_artifact.get("started_at") or _observed_at(run_artifact),
        "producer_id": _PRODUCER_ID,
        "producer_version": run_artifact.get("runner_version") or "unknown",
        "run_class": "verification_only_run",
        "runtime_mode": "created",
        "operator_note": f"ERA {lanes} run in {mode} mode. ERA is read-only and exports evidence to Centipede.",
    }


def _lane_admission(
    *,
    run_artifact: dict[str, Any],
    lane_name: str,
    admitted: bool,
    lane_health_state: str,
    reason: str | None,
) -> dict[str, Any]:
    run_id = run_artifact["run_id"]
    return {
        "record_id": f"era-lane:{run_id}:{lane_name}",
        "record_type": "centipede.lane_admission_result",
        "schema_version": _CENTIPEDE_RECORD_SCHEMA,
        "repository_id": run_artifact["repo_id"],
        "revision_anchor": _revision_anchor(run_artifact),
        "run_id": run_id,
        "observed_at": _observed_at(run_artifact),
        "producer_id": _PRODUCER_ID,
        "producer_version": run_artifact.get("runner_version") or "unknown",
        "lane_name": lane_name,
        "admitted": admitted,
        "lane_health_state": lane_health_state,
        "reason": reason,
    }


def _command_results_from_bundle(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    results = bundle.get("command_results", [])
    return results if isinstance(results, list) else []


def _raw_artifacts_from_bundle(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = bundle.get("tool_raw_artifacts", [])
    return artifacts if isinstance(artifacts, list) else []


def _build_lane_admissions(
    *,
    run_artifact: dict[str, Any],
    selection_artifact: dict[str, Any] | None,
    evidence_bundles: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    admissions: list[dict[str, Any]] = []

    for lane in run_artifact.get("lanes", []):
        command_results = _command_results_from_bundle(evidence_bundles.get(lane, {}))
        blocked = [item for item in command_results if item.get("status") == "blocked_by_missing_tool"]
        failed = [
            item
            for item in command_results
            if item.get("status") in {"failed", "failed_to_execute", "timed_out"}
        ]
        executed = [item for item in command_results if item.get("status") not in {"skipped", "blocked_by_missing_tool"}]
        if blocked and not executed:
            admitted = False
            health = "unavailable"
            reason = "Required lane tooling was unavailable."
        elif failed or blocked:
            admitted = True
            health = "degraded"
            reason = "Lane produced evidence with failures, blocked gates, or degraded checks."
        else:
            admitted = True
            health = "available"
            reason = "Lane evidence was captured."

        admissions.append(
            _lane_admission(
                run_artifact=run_artifact,
                lane_name=_lane_name(lane),
                admitted=admitted,
                lane_health_state=health,
                reason=reason,
            )
        )

    read_only_status = run_artifact.get("read_only_invariant_status")
    read_only_ok = read_only_status in {"clean_verified", "preexisting_dirty_tree"}
    admissions.append(
        _lane_admission(
            run_artifact=run_artifact,
            lane_name="era_read_only_invariant",
            admitted=read_only_ok,
            lane_health_state="available" if read_only_ok else "degraded",
            reason=run_artifact.get("read_only_invariant_notes"),
        )
    )

    all_command_results = [
        result
        for bundle in evidence_bundles.values()
        for result in _command_results_from_bundle(bundle)
    ]
    blocked_tools = [item for item in all_command_results if item.get("status") == "blocked_by_missing_tool"]
    admissions.append(
        _lane_admission(
            run_artifact=run_artifact,
            lane_name="era_toolchain_availability",
            admitted=not blocked_tools,
            lane_health_state="unavailable" if blocked_tools else "available",
            reason=(
                "One or more configured gates were blocked by missing tools."
                if blocked_tools
                else "Required detected tools were available or not applicable."
            ),
        )
    )

    if selection_artifact is not None:
        safety = selection_artifact.get("selection_safety_class")
        fallback = selection_artifact.get("fallback_reason")
        admissions.append(
            _lane_admission(
                run_artifact=run_artifact,
                lane_name="era_rts_selection",
                admitted=safety in {"full_retest_all", "safe", "safe_enough"},
                lane_health_state="available" if safety == "full_retest_all" else "degraded",
                reason=fallback or selection_artifact.get("selection_rationale"),
            )
        )

    admissions.append(
        _lane_admission(
            run_artifact=run_artifact,
            lane_name="era_evidence_hash_chain",
            admitted=True,
            lane_health_state="available",
            reason="ERA artifacts include hash-chain validation inputs.",
        )
    )

    return admissions


def _decision_trace(
    *,
    run_artifact: dict[str, Any],
    trace_id: str,
    decision_stage: str,
    decision_key: str,
    disposition: str,
    rationale: str | None,
    evidence_payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "trace_id": trace_id,
        "run_id": run_artifact["run_id"],
        "repository_id": run_artifact["repo_id"],
        "revision_anchor": _revision_anchor(run_artifact),
        "decision_stage": decision_stage,
        "decision_key": decision_key,
        "disposition": disposition,
        "rationale": rationale,
        "evidence_payload_json": json.dumps(evidence_payload, sort_keys=True),
        "observed_at": _observed_at(run_artifact),
        "producer_id": _PRODUCER_ID,
        "producer_version": run_artifact.get("runner_version") or "unknown",
    }


def _build_decision_traces(
    *,
    run_artifact: dict[str, Any],
    selection_artifact: dict[str, Any] | None,
    evidence_bundles: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    traces: list[dict[str, Any]] = []
    for lane, bundle in evidence_bundles.items():
        for result in _command_results_from_bundle(bundle):
            command_id = result.get("command_id") or "unknown_command"
            traces.append(
                _decision_trace(
                    run_artifact=run_artifact,
                    trace_id=f"era-trace:{run_artifact['run_id']}:{command_id}",
                    decision_stage=f"era_{lane}_gate",
                    decision_key=command_id,
                    disposition=_disposition_from_command_status(result.get("status")),
                    rationale=result.get("blocked_reason")
                    or result.get("reason")
                    or f"{result.get('label', command_id)} recorded status {result.get('status')}.",
                    evidence_payload={
                        "command_id": command_id,
                        "label": result.get("label"),
                        "exit_code": result.get("exit_code"),
                        "status": result.get("status"),
                        "stdout_sha256": result.get("stdout_sha256"),
                        "stderr_sha256": result.get("stderr_sha256"),
                    },
                )
            )

    traces.append(
        _decision_trace(
            run_artifact=run_artifact,
            trace_id=f"era-trace:{run_artifact['run_id']}:read_only_invariant",
            decision_stage="era_read_only_invariant",
            decision_key="target_repo_status",
            disposition=(
                "passed"
                if run_artifact.get("read_only_invariant_status") in {"clean_verified", "preexisting_dirty_tree"}
                else "failed"
            ),
            rationale=run_artifact.get("read_only_invariant_notes"),
            evidence_payload={
                "pre_run_git_status_short": run_artifact.get("pre_run_git_status_short"),
                "post_run_git_status_short": run_artifact.get("post_run_git_status_short"),
                "pre_run_head": run_artifact.get("pre_run_head"),
                "post_run_head": run_artifact.get("post_run_head"),
                "read_only_invariant_status": run_artifact.get("read_only_invariant_status"),
            },
        )
    )

    if selection_artifact is not None:
        traces.append(
            _decision_trace(
                run_artifact=run_artifact,
                trace_id=f"era-trace:{run_artifact['run_id']}:rts_selection",
                decision_stage="era_rts_selection",
                decision_key=selection_artifact.get("mode") or "unknown",
                disposition=(
                    "full_retest_all"
                    if selection_artifact.get("selection_safety_class") == "full_retest_all"
                    else "fallback_to_full"
                    if selection_artifact.get("full_run_required")
                    else "metadata_only"
                ),
                rationale=selection_artifact.get("selection_rationale"),
                evidence_payload={
                    "baseline_ref": selection_artifact.get("baseline_ref"),
                    "baseline_commit": selection_artifact.get("baseline_commit"),
                    "current_commit": selection_artifact.get("current_commit"),
                    "selection_method": selection_artifact.get("selection_method"),
                    "selection_safety_class": selection_artifact.get("selection_safety_class"),
                    "changed_files": selection_artifact.get("changed_files", []),
                    "full_run_required": selection_artifact.get("full_run_required"),
                    "full_run_executed": selection_artifact.get("full_run_executed"),
                    "fallback_reason": selection_artifact.get("fallback_reason"),
                },
            )
        )

    return traces


def _finding_command_id(finding: dict[str, Any]) -> str | None:
    lane_details = finding.get("lane_details") or {}
    if isinstance(lane_details, dict) and lane_details.get("command_id"):
        return str(lane_details["command_id"])
    for ref in finding.get("evidence_refs", []) or []:
        if isinstance(ref, str) and ref.startswith("normalized:"):
            return ref.split("normalized:", 1)[1]
    finding_id = finding.get("finding_id")
    if isinstance(finding_id, str) and finding_id.startswith("finding:"):
        parts = finding_id.split(":")
        if len(parts) >= 3:
            return ":".join(parts[1:-1])
    return None


def _target_scope_for_finding(finding: dict[str, Any]) -> list[dict[str, str]]:
    scopes: list[dict[str, str]] = []
    for path in finding.get("target_files", []) or []:
        scopes.append({"target_type": "file", "target_key": str(path)})
    for symbol in finding.get("target_symbols", []) or []:
        scopes.append({"target_type": "symbol", "target_key": str(symbol)})
    if not scopes:
        command_id = _finding_command_id(finding)
        if command_id:
            scopes.append({"target_type": "command", "target_key": command_id})
        else:
            scopes.append({"target_type": "repo", "target_key": finding.get("lane") or "unknown"})
    return scopes


def _target_scope_for_lane(lane: str) -> list[dict[str, str]]:
    return [{"target_type": "repo", "target_key": lane}]


def _confidence_for_lane(bundle: dict[str, Any]) -> str:
    command_results = _command_results_from_bundle(bundle)
    if any(result.get("status") == "passed" for result in command_results):
        return "high"
    if any(result.get("status") in {"failed", "failed_to_execute", "timed_out"} for result in command_results):
        return "high"
    if any(result.get("status") == "blocked_by_missing_tool" for result in command_results):
        return "none"
    return "moderate"


def _raw_artifacts_by_id(evidence_bundles: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    raw_by_id: dict[str, dict[str, Any]] = {}
    for bundle in evidence_bundles.values():
        for raw in _raw_artifacts_from_bundle(bundle):
            raw_id = raw.get("raw_artifact_id")
            if raw_id:
                raw_by_id[str(raw_id)] = raw
    return raw_by_id


def _command_result_by_id(evidence_bundles: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result_by_id: dict[str, dict[str, Any]] = {}
    for bundle in evidence_bundles.values():
        for result in _command_results_from_bundle(bundle):
            command_id = result.get("command_id")
            if command_id:
                result_by_id[str(command_id)] = result
    return result_by_id


def _payloads_for_finding(
    *,
    finding: dict[str, Any],
    raw_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    raw_refs = finding.get("raw_evidence_refs", []) or []
    raw_hashes = finding.get("raw_evidence_hashes", []) or []
    for index, raw_ref in enumerate(raw_refs):
        raw = raw_by_id.get(str(raw_ref), {})
        expected_hash = raw.get("sha256") or (raw_hashes[index] if index < len(raw_hashes) else None)
        payloads.append(
            {
                "payload_id": str(raw_ref),
                "payload_kind": raw.get("artifact_kind") or "raw_artifact",
                "payload_sha256": _sha_prefix(expected_hash),
                "authority_posture": "derived",
                "source_ref": raw.get("path") or str(raw_ref),
            }
        )
    if not payloads:
        payloads.append(
            {
                "payload_id": f"{finding.get('finding_id', 'unknown')}:finding",
                "payload_kind": "era_finding",
                "payload_sha256": _sha_prefix(finding.get("sha256")),
                "authority_posture": "derived",
                "source_ref": finding.get("finding_id"),
            }
        )
    return payloads


def _build_finding_evidence_bundle(
    *,
    run_artifact: dict[str, Any],
    finding: dict[str, Any],
    raw_by_id: dict[str, dict[str, Any]],
    command_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    finding_id = finding.get("finding_id") or "unknown_finding"
    command_id = _finding_command_id(finding)
    command_result = command_by_id.get(command_id or "", {})
    observed_artifact_set = [str(command_id)] if command_id else []
    observed_artifact_set.extend(str(path) for path in finding.get("target_files", []) or [])
    if not observed_artifact_set:
        observed_artifact_set.append(str(finding.get("lane") or "unknown"))

    return {
        "evidence_bundle_id": f"era-evidence:{run_artifact['run_id']}:{finding_id}",
        "record_type": "centipede.evidence_bundle",
        "schema_version": _CENTIPEDE_EVIDENCE_SCHEMA,
        "source_run_id": run_artifact["run_id"],
        "repository_id": run_artifact["repo_id"],
        "revision_anchor": _revision_anchor(run_artifact),
        "finding_id": finding_id,
        "detector_id": f"era.{finding.get('lane') or 'unknown'}",
        "detector_version": run_artifact.get("runner_version") or "unknown",
        "detector_config_hash": None,
        "execution_environment": json.dumps(run_artifact.get("environment", {}), sort_keys=True),
        "observed_artifact_set": sorted(set(observed_artifact_set)),
        "confidence_posture": _confidence_from_finding(finding.get("confidence")),
        "affected_scope": _target_scope_for_finding(finding),
        "non_affected_scope": [],
        "reproduction_contract": {
            "era_run_id": run_artifact["run_id"],
            "repo_path": run_artifact.get("repo_path"),
            "mode": run_artifact.get("mode"),
            "lane": finding.get("lane"),
            "finding_type": finding.get("finding_type"),
            "command_id": command_id,
            "command": command_result.get("command"),
            "cwd": command_result.get("cwd"),
            "status": command_result.get("status"),
            "exit_code": command_result.get("exit_code"),
        },
        "evidence_payloads": _payloads_for_finding(finding=finding, raw_by_id=raw_by_id),
        "contradiction_bundles": [],
        "repo_shape": None,
        "downstream_consumer_hints": ["operator_review"],
        "produced_at": _observed_at(run_artifact),
        "producer_id": _PRODUCER_ID,
        "producer_version": run_artifact.get("runner_version") or "unknown",
    }


def _build_lane_evidence_summary(
    *,
    run_artifact: dict[str, Any],
    lane: str,
    bundle: dict[str, Any],
) -> dict[str, Any]:
    command_results = _command_results_from_bundle(bundle)
    raw_artifacts = _raw_artifacts_from_bundle(bundle)
    payloads = [
        {
            "payload_id": raw.get("raw_artifact_id") or f"{lane}:raw:{index}",
            "payload_kind": raw.get("artifact_kind") or "raw_artifact",
            "payload_sha256": _sha_prefix(raw.get("sha256")),
            "authority_posture": "derived",
            "source_ref": raw.get("path"),
        }
        for index, raw in enumerate(raw_artifacts, start=1)
    ]
    if not payloads:
        payloads.append(
            {
                "payload_id": f"{lane}:evidence_bundle",
                "payload_kind": "era_evidence_bundle",
                "payload_sha256": _sha_prefix(bundle.get("sha256")),
                "authority_posture": "derived",
                "source_ref": lane,
            }
        )

    return {
        "evidence_bundle_id": f"era-evidence:{run_artifact['run_id']}:{lane}:summary",
        "record_type": "centipede.evidence_bundle",
        "schema_version": _CENTIPEDE_EVIDENCE_SCHEMA,
        "source_run_id": run_artifact["run_id"],
        "repository_id": run_artifact["repo_id"],
        "revision_anchor": _revision_anchor(run_artifact),
        "finding_id": f"era:{lane}:evidence",
        "detector_id": f"era.{lane}",
        "detector_version": run_artifact.get("runner_version") or "unknown",
        "detector_config_hash": None,
        "execution_environment": json.dumps(run_artifact.get("environment", {}), sort_keys=True),
        "observed_artifact_set": [item.get("command_id", "unknown_command") for item in command_results],
        "confidence_posture": _confidence_for_lane(bundle),
        "affected_scope": _target_scope_for_lane(lane),
        "non_affected_scope": [],
        "reproduction_contract": {
            "era_run_id": run_artifact["run_id"],
            "repo_path": run_artifact.get("repo_path"),
            "mode": run_artifact.get("mode"),
            "lanes": run_artifact.get("lanes", []),
            "commands": [
                {
                    "command_id": item.get("command_id"),
                    "command": item.get("command"),
                    "cwd": item.get("cwd"),
                    "status": item.get("status"),
                    "exit_code": item.get("exit_code"),
                }
                for item in command_results
            ],
        },
        "evidence_payloads": payloads,
        "contradiction_bundles": [],
        "repo_shape": None,
        "downstream_consumer_hints": ["operator_review"],
        "produced_at": _observed_at(run_artifact),
        "producer_id": _PRODUCER_ID,
        "producer_version": run_artifact.get("runner_version") or "unknown",
    }


def _build_centipede_evidence_bundles(
    *,
    run_artifact: dict[str, Any],
    evidence_bundles: dict[str, dict[str, Any]],
    findings: dict[str, Any],
) -> list[dict[str, Any]]:
    mapped: list[dict[str, Any]] = []
    era_findings = findings.get("era_findings", []) if isinstance(findings, dict) else []
    raw_by_id = _raw_artifacts_by_id(evidence_bundles)
    command_by_id = _command_result_by_id(evidence_bundles)

    for finding in era_findings:
        if not isinstance(finding, dict):
            continue
        mapped.append(
            _build_finding_evidence_bundle(
                run_artifact=run_artifact,
                finding=finding,
                raw_by_id=raw_by_id,
                command_by_id=command_by_id,
            )
        )

    lanes_with_findings = {
        str(finding.get("lane"))
        for finding in era_findings
        if isinstance(finding, dict) and finding.get("lane")
    }
    for lane, bundle in evidence_bundles.items():
        # If there are ERA findings for this lane, the finding-scoped bundles above
        # carry the actionable evidence. If there are no findings, keep an
        # evidence-only summary so Centipede can still import the run record.
        if lane in lanes_with_findings:
            continue
        mapped.append(
            _build_lane_evidence_summary(
                run_artifact=run_artifact,
                lane=lane,
                bundle=bundle,
            )
        )

    return mapped



_ACTIONABLE_SELF_HEALING_FINDING_TYPES = {
    "accuracy_gate_failed",
    "harmful_redundancy_candidate",
    "efficiency_regression_with_baseline",
}

_BLOCKED_SELF_HEALING_EVIDENCE_STRENGTHS = {
    "none",
    "advisory_only",
    "blocked",
    "unproven",
}


def _severity_from_risk(risk_level: str | None) -> str:
    mapping = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "moderate": "medium",
        "low": "low",
        "info": "info",
        "none": "info",
    }
    return mapping.get((risk_level or "").lower(), "medium")


def _projection_evidence_bundle_id(run_artifact: dict[str, Any], finding: dict[str, Any]) -> str:
    return f"era-evidence:{run_artifact['run_id']}:{finding.get('finding_id') or 'unknown_finding'}"


def _suggested_remediation_kind(finding: dict[str, Any]) -> str | None:
    finding_type = finding.get("finding_type")
    if finding_type == "accuracy_gate_failed":
        return "verification_failure_triage"
    if finding_type == "harmful_redundancy_candidate":
        return "redundancy_review"
    if finding_type == "efficiency_regression_with_baseline":
        return "efficiency_regression_review"
    return None


def _proposal_required_for_finding(finding: dict[str, Any]) -> bool:
    finding_type = finding.get("finding_type")
    target_files = finding.get("target_files") or []
    if finding_type == "accuracy_gate_failed":
        return False
    if finding_type in {"harmful_redundancy_candidate", "efficiency_regression_with_baseline"}:
        return bool(target_files)
    return False


def _execution_reach_for_finding(finding: dict[str, Any]) -> str:
    lane = finding.get("lane")
    if lane == "accuracy":
        return "test_only"
    if lane in {"redundancy", "efficiency"}:
        return "build_only"
    return "unknown"


def _proof_type_for_finding(finding: dict[str, Any]) -> str:
    if finding.get("finding_type") == "accuracy_gate_failed":
        return "dynamic_reproduction"
    return "static_evidence"


def _finding_has_raw_evidence(finding: dict[str, Any]) -> bool:
    refs = finding.get("raw_evidence_refs") or []
    hashes = finding.get("raw_evidence_hashes") or []
    return bool(refs) and bool(hashes) and len(refs) == len(hashes)


def _is_self_healing_projection_eligible(finding: dict[str, Any]) -> bool:
    finding_type = finding.get("finding_type")
    if finding_type not in _ACTIONABLE_SELF_HEALING_FINDING_TYPES:
        return False
    if finding.get("operator_decision") == "accepted_exception":
        return False
    if finding.get("blocked_reason"):
        return False
    if not _finding_has_raw_evidence(finding):
        return False
    if finding.get("safe_to_autofix") is not False:
        return False
    if finding.get("requires_operator_review") is False:
        return False

    evidence_strength = str(finding.get("evidence_strength") or "").lower()
    if evidence_strength in _BLOCKED_SELF_HEALING_EVIDENCE_STRENGTHS:
        return False

    confidence = str(finding.get("confidence") or "").lower()
    if confidence not in {"high", "exact"}:
        return False

    risk = str(finding.get("risk_level") or "").lower()
    if risk not in {"high", "critical"}:
        return False

    return bool(_target_scope_for_finding(finding))


def _supporting_lane_ids_for_finding(run_artifact: dict[str, Any], finding: dict[str, Any]) -> list[str]:
    lane = finding.get("lane") or "unknown"
    return [f"era-lane:{run_artifact['run_id']}:{_lane_name(str(lane))}"]


def _supporting_trace_ids_for_finding(run_artifact: dict[str, Any], finding: dict[str, Any]) -> list[str]:
    command_id = _finding_command_id(finding)
    if command_id:
        return [f"era-trace:{run_artifact['run_id']}:{command_id}"]
    return [f"era-trace:{run_artifact['run_id']}:read_only_invariant"]


def _build_self_healing_projection(
    *,
    run_artifact: dict[str, Any],
    finding: dict[str, Any],
) -> dict[str, Any]:
    finding_id = finding.get("finding_id") or "unknown_finding"
    scope = _target_scope_for_finding(finding)[0]
    produced_at = _observed_at(run_artifact)
    return {
        "projection_id": f"era-sh-projection:{run_artifact['run_id']}:{finding_id}",
        "record_type": "centipede.self_healing_projection",
        "schema_version": "centipede.self_healing_projection.v1",
        "source_run_id": run_artifact["run_id"],
        "repository_id": run_artifact["repo_id"],
        "revision_anchor": _revision_anchor(run_artifact),
        "run_class": "verification_only_run",
        "finding_id": finding_id,
        "finding_class": finding.get("finding_type") or "unknown",
        "severity": _severity_from_risk(finding.get("risk_level")),
        "confidence_posture": _confidence_from_finding(finding.get("confidence")),
        "exploitability_posture": "unknown",
        "execution_reach": _execution_reach_for_finding(finding),
        "trigger_requirements": [
            "operator_review",
            "centipede_import_receipt",
            "self_healing_intake_receipt",
        ],
        "proof_type": _proof_type_for_finding(finding),
        "affected_target_type": scope["target_type"],
        "affected_target_key": scope["target_key"],
        "evidence_bundle_id": _projection_evidence_bundle_id(run_artifact, finding),
        "supporting_lane_ids": _supporting_lane_ids_for_finding(run_artifact, finding),
        "supporting_trace_ids": _supporting_trace_ids_for_finding(run_artifact, finding),
        "suggested_remediation_kind": _suggested_remediation_kind(finding),
        "proposal_required": _proposal_required_for_finding(finding),
        "operator_review_required": True,
        "blocked_reason": None,
        "produced_at": produced_at,
        "valid_until": None,
        "stale_after": None,
        "superseded_by": None,
        "invalidated_reason": None,
        "producer_id": _PRODUCER_ID,
        "producer_version": run_artifact.get("runner_version") or "unknown",
    }


def _build_self_healing_projections(
    *,
    run_artifact: dict[str, Any],
    findings: dict[str, Any],
) -> list[dict[str, Any]]:
    era_findings = findings.get("era_findings", []) if isinstance(findings, dict) else []
    projections: list[dict[str, Any]] = []
    for finding in era_findings:
        if not isinstance(finding, dict):
            continue
        if not _is_self_healing_projection_eligible(finding):
            continue
        projections.append(
            _build_self_healing_projection(
                run_artifact=run_artifact,
                finding=finding,
            )
        )
    return projections


def _validate_self_healing_projection_contracts(bundle: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    run = bundle.get("run") or {}
    run_id = run.get("run_id")
    repository_id = run.get("repository_id")
    revision_anchor = run.get("revision_anchor")
    evidence_bundle_ids = {
        item.get("evidence_bundle_id")
        for item in bundle.get("evidence_bundles", [])
        if isinstance(item, dict)
    }
    lane_ids = {
        item.get("record_id")
        for item in bundle.get("lane_admissions", [])
        if isinstance(item, dict)
    }
    trace_ids = {
        item.get("trace_id")
        for item in bundle.get("decision_traces", [])
        if isinstance(item, dict)
    }

    registry_projections = bundle.get("registry_projections", [])
    if registry_projections:
        errors.append("centipede_bundle.json registry_projections must remain empty until registry-specific rules exist.")

    for projection in bundle.get("self_healing_projections", []):
        if not isinstance(projection, dict):
            errors.append("Self-Healing projection must be an object.")
            continue
        projection_id = projection.get("projection_id", "unknown")
        if projection.get("schema_version") != "centipede.self_healing_projection.v1":
            errors.append(f"Self-Healing projection {projection_id} has invalid schema_version.")
        if projection.get("record_type") != "centipede.self_healing_projection":
            errors.append(f"Self-Healing projection {projection_id} has invalid record_type.")
        if projection.get("source_run_id") != run_id:
            errors.append(f"Self-Healing projection {projection_id} source_run_id does not match run.run_id.")
        if projection.get("repository_id") != repository_id:
            errors.append(f"Self-Healing projection {projection_id} repository_id does not match run.repository_id.")
        if projection.get("revision_anchor") != revision_anchor:
            errors.append(f"Self-Healing projection {projection_id} revision_anchor does not match run.revision_anchor.")
        if projection.get("operator_review_required") is not True:
            errors.append(f"Self-Healing projection {projection_id} must require operator review.")
        if projection.get("blocked_reason") is not None:
            errors.append(f"Self-Healing projection {projection_id} must not carry blocked_reason.")
        if projection.get("evidence_bundle_id") not in evidence_bundle_ids:
            errors.append(f"Self-Healing projection {projection_id} references missing evidence_bundle_id.")
        for lane_id in projection.get("supporting_lane_ids", []):
            if lane_id not in lane_ids:
                errors.append(f"Self-Healing projection {projection_id} references missing supporting lane {lane_id}.")
        for trace_id in projection.get("supporting_trace_ids", []):
            if trace_id not in trace_ids:
                errors.append(f"Self-Healing projection {projection_id} references missing supporting trace {trace_id}.")
    return errors


def write_centipede_export(
    *,
    run_artifact: dict[str, Any],
    selection_artifact: dict[str, Any] | None,
    evidence_bundles: dict[str, dict[str, Any]],
    findings: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    """Write a ForgeCommand-compatible CentipedeIntakeBundle.

    ERA-CENT-02 emits conservative, evidence-backed Self-Healing projections.
    ERA remains read-only and never executes or writes repairs.
    """

    bundle = {
        "schema_version": _CENTIPEDE_BUNDLE_SCHEMA,
        "source_system": "era",
        "run": _run_created(run_artifact),
        "lane_admissions": _build_lane_admissions(
            run_artifact=run_artifact,
            selection_artifact=selection_artifact,
            evidence_bundles=evidence_bundles,
        ),
        "decision_traces": _build_decision_traces(
            run_artifact=run_artifact,
            selection_artifact=selection_artifact,
            evidence_bundles=evidence_bundles,
        ),
        "evidence_bundles": _build_centipede_evidence_bundles(
            run_artifact=run_artifact,
            evidence_bundles=evidence_bundles,
            findings=findings,
        ),
        "self_healing_projections": _build_self_healing_projections(
            run_artifact=run_artifact,
            findings=findings,
        ),
        "registry_projections": [],
        "final_runtime_mode": _runtime_mode(run_artifact.get("status")),
        "final_runtime_mode_observed_at": run_artifact.get("completed_at") or _observed_at(run_artifact),
    }

    validation = validate_centipede_export_bundle(bundle, run_artifact=run_artifact, findings=findings)
    if not validation["ok"]:
        raise ValueError("Invalid Centipede export bundle: " + "; ".join(validation["errors"]))

    write_json(output_path, bundle)
    return bundle


def _parse_validator_args(
    args: tuple[Any, ...],
    run_artifact: dict[str, Any] | None,
    findings: dict[str, Any] | None,
    errors: list[str] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str] | None]:
    for arg in args:
        if isinstance(arg, list):
            errors = arg
            continue
        if not isinstance(arg, dict):
            continue
        schema = arg.get("schema_version")
        if schema == "ERAEvaluationRun.v1" or ("commit_sha" in arg and "repo_id" in arg and "status" in arg):
            run_artifact = arg
            continue
        if schema == "ERAFindingSet.v1" or "era_findings" in arg:
            findings = arg
            continue
    return run_artifact, findings, errors


def validate_centipede_export_bundle(
    bundle: dict[str, Any],
    *args: Any,
    run_artifact: dict[str, Any] | None = None,
    findings: dict[str, Any] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    """Validate the ERA-CENT-01 bundle shape before ForgeCommand import.

    This helper accepts multiple call styles so `era_core.validation` can pass
    either a run artifact, findings bundle, shared error list, or all three.
    """

    run_artifact, findings, errors = _parse_validator_args(args, run_artifact, findings, errors)
    local_errors: list[str] = []

    required_top_level = {
        "schema_version",
        "source_system",
        "run",
        "lane_admissions",
        "decision_traces",
        "evidence_bundles",
        "self_healing_projections",
        "registry_projections",
        "final_runtime_mode",
        "final_runtime_mode_observed_at",
    }
    for field in sorted(required_top_level):
        if field not in bundle:
            local_errors.append(f"centipede_bundle.json is missing {field}.")

    if local_errors:
        if errors is not None:
            errors.extend(local_errors)
        return _validation_result(False, local_errors)

    if bundle.get("schema_version") != _CENTIPEDE_BUNDLE_SCHEMA:
        local_errors.append("centipede_bundle.json schema_version must be centipede.intake.v1.")
    if bundle.get("source_system") != "era":
        local_errors.append("centipede_bundle.json source_system must be era.")
    if not isinstance(bundle.get("run"), dict):
        local_errors.append("centipede_bundle.json run must be an object.")
    if not isinstance(bundle.get("lane_admissions"), list):
        local_errors.append("centipede_bundle.json lane_admissions must be a list.")
    if not isinstance(bundle.get("decision_traces"), list):
        local_errors.append("centipede_bundle.json decision_traces must be a list.")
    if not isinstance(bundle.get("evidence_bundles"), list):
        local_errors.append("centipede_bundle.json evidence_bundles must be a list.")
    if not isinstance(bundle.get("self_healing_projections"), list):
        local_errors.append("centipede_bundle.json self_healing_projections must be a list.")
    if not isinstance(bundle.get("registry_projections"), list):
        local_errors.append("centipede_bundle.json registry_projections must be a list.")

    if local_errors:
        if errors is not None:
            errors.extend(local_errors)
        return _validation_result(False, local_errors)

    run = bundle["run"]
    run_required = {
        "record_id",
        "record_type",
        "schema_version",
        "repository_id",
        "revision_anchor",
        "run_id",
        "observed_at",
        "producer_id",
        "producer_version",
        "run_class",
        "runtime_mode",
        "operator_note",
    }
    for field in sorted(run_required):
        if field not in run:
            local_errors.append(f"centipede run record is missing {field}.")
    if run.get("runtime_mode") != "created":
        local_errors.append("centipede run.runtime_mode must remain created.")
    if run.get("run_class") != "verification_only_run":
        local_errors.append("centipede run.run_class must be verification_only_run for ERA-CENT-01.")

    if isinstance(run_artifact, dict):
        if run.get("run_id") != run_artifact.get("run_id"):
            local_errors.append("centipede run_id does not match run.json.")
        if run.get("repository_id") != run_artifact.get("repo_id"):
            local_errors.append("centipede repository_id does not match run.json repo_id.")
        if run.get("revision_anchor") != _revision_anchor(run_artifact):
            local_errors.append("centipede revision_anchor does not match run.json commit_sha.")

    final_runtime_modes = {
        "completed",
        "completed_partial",
        "failed",
        "aborted",
        "reconciliation_required",
    }
    if bundle.get("final_runtime_mode") not in final_runtime_modes:
        local_errors.append("centipede final_runtime_mode is invalid.")

    binding_sets = (
        ("lane admission", bundle.get("lane_admissions", []), "run_id", "repository_id", "revision_anchor"),
        ("decision trace", bundle.get("decision_traces", []), "run_id", "repository_id", "revision_anchor"),
        ("evidence bundle", bundle.get("evidence_bundles", []), "source_run_id", "repository_id", "revision_anchor"),
    )
    for label, records, run_key, repo_key, revision_key in binding_sets:
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                local_errors.append(f"centipede {label} #{index + 1} must be an object.")
                continue
            if record.get(run_key) != run.get("run_id"):
                local_errors.append(f"centipede {label} #{index + 1} run binding does not match bundle run.")
            if record.get(repo_key) != run.get("repository_id"):
                local_errors.append(f"centipede {label} #{index + 1} repository binding does not match bundle run.")
            if record.get(revision_key) != run.get("revision_anchor"):
                local_errors.append(f"centipede {label} #{index + 1} revision binding does not match bundle run.")

    lane_names = [item.get("lane_name") for item in bundle.get("lane_admissions", []) if isinstance(item, dict)]
    if len(lane_names) != len(set(lane_names)):
        local_errors.append("centipede lane_admissions contains duplicate lane_name values.")

    trace_ids = [item.get("trace_id") for item in bundle.get("decision_traces", []) if isinstance(item, dict)]
    if len(trace_ids) != len(set(trace_ids)):
        local_errors.append("centipede decision_traces contains duplicate trace_id values.")

    evidence_ids = [
        item.get("evidence_bundle_id")
        for item in bundle.get("evidence_bundles", [])
        if isinstance(item, dict)
    ]
    if len(evidence_ids) != len(set(evidence_ids)):
        local_errors.append("centipede evidence_bundles contains duplicate evidence_bundle_id values.")

    finding_ids = set()
    if isinstance(findings, dict):
        finding_ids = {
            str(item.get("finding_id"))
            for item in findings.get("era_findings", [])
            if isinstance(item, dict) and item.get("finding_id")
        }

    evidence_required = {
        "evidence_bundle_id",
        "record_type",
        "schema_version",
        "source_run_id",
        "repository_id",
        "revision_anchor",
        "finding_id",
        "detector_id",
        "detector_version",
        "observed_artifact_set",
        "confidence_posture",
        "affected_scope",
        "evidence_payloads",
        "produced_at",
        "producer_id",
        "producer_version",
    }
    for index, evidence_bundle in enumerate(bundle.get("evidence_bundles", []), start=1):
        if not isinstance(evidence_bundle, dict):
            continue
        for field in sorted(evidence_required):
            if field not in evidence_bundle:
                local_errors.append(f"centipede evidence bundle #{index} is missing {field}.")
        finding_id = evidence_bundle.get("finding_id")
        if finding_ids and finding_id not in finding_ids and not str(finding_id).startswith("era:"):
            local_errors.append(f"centipede evidence bundle #{index} finding_id is not backed by ERA findings.")
        if evidence_bundle.get("schema_version") != _CENTIPEDE_EVIDENCE_SCHEMA:
            local_errors.append(f"centipede evidence bundle #{index} has invalid schema_version.")
        if not isinstance(evidence_bundle.get("evidence_payloads", []), list):
            local_errors.append(f"centipede evidence bundle #{index} evidence_payloads must be a list.")

    # ERA-CENT-01 exports evidence only. Projection generation is intentionally deferred.
    if bundle.get("registry_projections"):
        local_errors.append("ERA-CENT-01 must not emit registry_projections.")

    local_errors.extend(_validate_self_healing_projection_contracts(bundle))

    if errors is not None:
        errors.extend(local_errors)
    return _validation_result(not local_errors, local_errors)
