from __future__ import annotations

from pathlib import Path
from typing import Any

from era_core.hashing import write_json


def write_centipede_export(
    *,
    run_artifact: dict[str, Any],
    selection_artifact: dict[str, Any],
    evidence_bundle: dict[str, Any],
    findings: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    bundle = {
        "schema_version": "CentipedeExportBundle.v1",
        "run_id": run_artifact["run_id"],
        "repo_id": run_artifact["repo_id"],
        "commit_sha": run_artifact["commit_sha"],
        "lane_results": [
            {
                "lane": "accuracy",
                "run_status": run_artifact["status"],
                "read_only_invariant_status": run_artifact["read_only_invariant_status"],
            }
        ],
        "selection": {
            "mode": selection_artifact["mode"],
            "selection_method": selection_artifact["selection_method"],
            "selection_safety_class": selection_artifact["selection_safety_class"],
        },
        "evidence_bundle_refs": run_artifact["evidence_bundle_refs"],
        "finding_ids": [item["finding_id"] for item in findings.get("era_findings", [])],
        "projection_candidates": [],
    }
    write_json(output_path, bundle)
    return bundle
