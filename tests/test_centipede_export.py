from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from era_integrations.centipede_export import write_centipede_export


def _run_artifact(temp_dir: Path) -> dict:
    return {
        "schema_version": "ERAEvaluationRun.v1",
        "run_id": "20260424T120000Z-test0001",
        "repo_id": "git@github.com:Boswecw/Forge_Command.git",
        "repo_path": "/home/charlie/Forge/ecosystem/Forge_Command",
        "commit_sha": "abc123",
        "branch": "main",
        "working_tree_status": "",
        "is_dirty": False,
        "lanes": ["accuracy"],
        "mode": "full",
        "baseline_ref": None,
        "baseline_commit": None,
        "started_at": "2026-04-24T12:00:00Z",
        "completed_at": "2026-04-24T12:01:00Z",
        "status": "completed_partial",
        "operator_requested_by": "charlie",
        "runner_version": "0.1.0",
        "tool_versions": {"cargo": "cargo 1.75.0"},
        "environment": {"platform": "linux", "python_version": "3.11"},
        "artifact_root": str(temp_dir),
        "target_manifest_path": str(temp_dir / "target_manifest.json"),
        "tool_availability_path": str(temp_dir / "tool_availability.json"),
        "test_selection_artifact_path": None,
        "evidence_bundle_refs": [str(temp_dir / "evidence/accuracy/test_evidence_bundle.json")],
        "finding_refs": [str(temp_dir / "findings.json")],
        "review_artifact_ref": str(temp_dir / "review.md"),
        "pre_run_git_status_short": "",
        "post_run_git_status_short": "",
        "pre_run_head": "abc123",
        "post_run_head": "abc123",
        "pre_run_dirty": False,
        "post_run_dirty": False,
        "read_only_invariant_status": "clean_verified",
        "read_only_invariant_notes": "Pre-run and post-run git state matched.",
    }


def _accuracy_evidence_bundle() -> dict:
    return {
        "schema_version": "TestEvidenceBundle.v1",
        "run_id": "20260424T120000Z-test0001",
        "repo_id": "git@github.com:Boswecw/Forge_Command.git",
        "lane": "accuracy",
        "command_results": [
            {
                "command_id": "cargo_check",
                "label": "cargo check",
                "command": ["cargo", "check", "--manifest-path", "src-tauri/Cargo.toml"],
                "cwd": "/home/charlie/Forge/ecosystem/Forge_Command",
                "started_at": "2026-04-24T12:00:01Z",
                "completed_at": "2026-04-24T12:00:20Z",
                "duration_ms": 19000,
                "exit_code": 101,
                "status": "failed",
                "stdout_path": "/tmp/cargo_check.stdout.txt",
                "stderr_path": "/tmp/cargo_check.stderr.txt",
                "stdout_sha256": "0" * 64,
                "stderr_sha256": "1" * 64,
                "tool_name": "cargo",
                "tool_version": "cargo 1.75.0",
                "blocked_reason": None,
            }
        ],
        "tool_raw_artifacts": [
            {
                "schema_version": "ToolRawArtifact.v1",
                "raw_artifact_id": "cargo_check:stdout",
                "run_id": "20260424T120000Z-test0001",
                "command_id": "cargo_check",
                "tool_name": "cargo",
                "tool_version": "cargo 1.75.0",
                "artifact_kind": "stdout",
                "path": "/tmp/cargo_check.stdout.txt",
                "sha256": "0" * 64,
                "created_at": "2026-04-24T12:00:20Z",
            },
            {
                "schema_version": "ToolRawArtifact.v1",
                "raw_artifact_id": "cargo_check:stderr",
                "run_id": "20260424T120000Z-test0001",
                "command_id": "cargo_check",
                "tool_name": "cargo",
                "tool_version": "cargo 1.75.0",
                "artifact_kind": "stderr",
                "path": "/tmp/cargo_check.stderr.txt",
                "sha256": "1" * 64,
                "created_at": "2026-04-24T12:00:20Z",
            },
        ],
        "tool_normalized_results": [],
        "created_at": "2026-04-24T12:01:00Z",
        "sha256": "2" * 64,
    }


def _findings_bundle() -> dict:
    return {
        "schema_version": "ERAFindingSet.v1",
        "run_id": "20260424T120000Z-test0001",
        "repo_id": "git@github.com:Boswecw/Forge_Command.git",
        "lane_finding_drafts": [],
        "era_findings": [
            {
                "schema_version": "ERAFinding.v1",
                "finding_id": "finding:cargo_check:1",
                "run_id": "20260424T120000Z-test0001",
                "repo_id": "git@github.com:Boswecw/Forge_Command.git",
                "commit_sha": "abc123",
                "lane": "accuracy",
                "finding_type": "accuracy_gate_failed",
                "summary": "cargo check did not complete successfully.",
                "target_files": [],
                "target_symbols": [],
                "evidence_refs": ["normalized:cargo_check", "draft:cargo_check:1"],
                "raw_evidence_refs": ["cargo_check:stdout", "cargo_check:stderr"],
                "raw_evidence_hashes": ["0" * 64, "1" * 64],
                "risk_level": "high",
                "confidence": "high",
                "evidence_strength": "mechanical",
                "recommended_action": "operator_review",
                "safe_to_autofix": False,
                "requires_operator_review": True,
                "operator_decision": "pending",
                "blocked_reason": None,
                "created_at": "2026-04-24T12:01:00Z",
                "lane_details": {"command_id": "cargo_check"},
                "sha256": "3" * 64,
            }
        ],
        "era_scores": [],
        "created_at": "2026-04-24T12:01:00Z",
        "sha256": "4" * 64,
    }


class CentipedeExportTests(unittest.TestCase):
    def test_writes_import_shaped_centipede_intake_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            run_dir = Path(temp_root)
            bundle = write_centipede_export(
                run_artifact=_run_artifact(run_dir),
                selection_artifact=None,
                evidence_bundles={"accuracy": _accuracy_evidence_bundle()},
                findings=_findings_bundle(),
                output_path=run_dir / "centipede_bundle.json",
            )

            self.assertEqual(bundle["schema_version"], "centipede.intake.v1")
            self.assertEqual(bundle["source_system"], "era")
            self.assertEqual(bundle["run"]["runtime_mode"], "created")
            self.assertEqual(bundle["run"]["run_class"], "verification_only_run")
            self.assertEqual(bundle["final_runtime_mode"], "completed_partial")

            self.assertEqual(bundle["lane_admissions"][0]["lane_name"], "era_accuracy")
            self.assertEqual(bundle["decision_traces"][0]["decision_stage"], "era_accuracy_gate")
            self.assertEqual(bundle["evidence_bundles"][0]["finding_id"], "finding:cargo_check:1")
            self.assertEqual(bundle["evidence_bundles"][0]["confidence_posture"], "high")

            self.assertEqual(len(bundle["self_healing_projections"]), 1)
            projection = bundle["self_healing_projections"][0]
            self.assertEqual(projection["schema_version"], "centipede.self_healing_projection.v1")
            self.assertEqual(projection["record_type"], "centipede.self_healing_projection")
            self.assertEqual(projection["finding_id"], "finding:cargo_check:1")
            self.assertEqual(projection["finding_class"], "accuracy_gate_failed")
            self.assertEqual(projection["severity"], "high")
            self.assertEqual(projection["confidence_posture"], "high")
            self.assertEqual(projection["execution_reach"], "test_only")
            self.assertEqual(projection["proof_type"], "dynamic_reproduction")
            self.assertEqual(projection["affected_target_type"], "command")
            self.assertEqual(projection["affected_target_key"], "cargo_check")
            self.assertEqual(
                projection["evidence_bundle_id"],
                bundle["evidence_bundles"][0]["evidence_bundle_id"],
            )
            self.assertEqual(
                projection["supporting_lane_ids"],
                ["era-lane:20260424T120000Z-test0001:era_accuracy"],
            )
            self.assertEqual(
                projection["supporting_trace_ids"],
                ["era-trace:20260424T120000Z-test0001:cargo_check"],
            )
            self.assertTrue(projection["operator_review_required"])
            self.assertFalse(projection["proposal_required"])
            self.assertIsNone(projection["blocked_reason"])
            self.assertEqual(bundle["registry_projections"], [])

            self.assertNotIn("lane_results", bundle)
            self.assertNotIn("projection_candidates", bundle)
            self.assertTrue((run_dir / "centipede_bundle.json").exists())

    def test_missing_raw_evidence_stays_evidence_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            run_dir = Path(temp_root)
            findings = _findings_bundle()
            findings["era_findings"][0]["raw_evidence_refs"] = []
            findings["era_findings"][0]["raw_evidence_hashes"] = []

            bundle = write_centipede_export(
                run_artifact=_run_artifact(run_dir),
                selection_artifact=None,
                evidence_bundles={"accuracy": _accuracy_evidence_bundle()},
                findings=findings,
                output_path=run_dir / "centipede_bundle.json",
            )

            self.assertEqual(bundle["evidence_bundles"][0]["finding_id"], "finding:cargo_check:1")
            self.assertEqual(bundle["self_healing_projections"], [])

    def test_intentional_exception_stays_evidence_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            run_dir = Path(temp_root)
            findings = _findings_bundle()
            findings["era_findings"][0]["operator_decision"] = "accepted_exception"
            findings["era_findings"][0]["lane_details"]["exception_id"] = "exception:test"

            bundle = write_centipede_export(
                run_artifact=_run_artifact(run_dir),
                selection_artifact=None,
                evidence_bundles={"accuracy": _accuracy_evidence_bundle()},
                findings=findings,
                output_path=run_dir / "centipede_bundle.json",
            )

            self.assertEqual(bundle["evidence_bundles"][0]["finding_id"], "finding:cargo_check:1")
            self.assertEqual(bundle["self_healing_projections"], [])


if __name__ == "__main__":
    unittest.main()
