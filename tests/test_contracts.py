from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from era_cli.commands.run import execute_run
from era_core.contracts import (
    build_era_scores,
    build_tool_normalized_result,
    promote_normalized_results,
)
from era_core.models import CommandResult
from tests.test_artifact_generation import init_git_repo


class ContractTests(unittest.TestCase):
    def test_promoted_findings_preserve_lane_details(self) -> None:
        normalized_results = [
            build_tool_normalized_result(
                run_id="run-1",
                command_id="jscpd_scan",
                raw_artifact_refs=["jscpd_scan:stdout", "jscpd_scan:stderr"],
                normalizer_name="era_redundancy_normalizer",
                normalizer_version="0.1.0",
                tool_name="jscpd",
                tool_version="1.0.0",
                summary_status="passed",
                parsed_findings=[
                    {
                        "finding_type": "ignored_with_reason",
                        "summary": "Generated mirror file is intentionally redundant.",
                        "target_files": ["src/generated/file.ts"],
                        "target_symbols": [],
                        "risk_level": "low",
                        "confidence": "moderate",
                        "evidence_strength": "moderate",
                        "recommended_action": "review_exception_after_date",
                        "blocked_reason": "Generated mirror file",
                        "exception_id": "ex-1",
                    }
                ],
                parse_warnings=[],
                parse_errors=[],
                created_at="2026-04-24T00:00:01Z",
            )
        ]
        raw_artifacts = [
            {
                "schema_version": "ToolRawArtifact.v1",
                "raw_artifact_id": "jscpd_scan:stdout",
                "run_id": "run-1",
                "command_id": "jscpd_scan",
                "tool_name": "jscpd",
                "tool_version": "1.0.0",
                "artifact_kind": "stdout",
                "path": "/tmp/stdout.txt",
                "sha256": "hash-a",
                "created_at": "2026-04-24T00:00:01Z",
            },
            {
                "schema_version": "ToolRawArtifact.v1",
                "raw_artifact_id": "jscpd_scan:stderr",
                "run_id": "run-1",
                "command_id": "jscpd_scan",
                "tool_name": "jscpd",
                "tool_version": "1.0.0",
                "artifact_kind": "stderr",
                "path": "/tmp/stderr.txt",
                "sha256": "hash-b",
                "created_at": "2026-04-24T00:00:01Z",
            },
        ]
        lane_drafts, findings = promote_normalized_results(
            run_id="run-1",
            repo_id="repo-1",
            commit_sha="abc123",
            normalized_results=normalized_results,
            raw_artifacts=raw_artifacts,
            command_lanes={"jscpd_scan": "redundancy"},
            default_target_files_by_lane=None,
            created_at="2026-04-24T00:00:02Z",
        )
        scores = build_era_scores(
            run_id="run-1",
            repo_id="repo-1",
            commit_sha="abc123",
            lane_classifications={"redundancy": "needs_operator_review"},
            command_results=[
                CommandResult(
                    lane="redundancy",
                    command_id="jscpd_scan",
                    label="jscpd scan",
                    command=["jscpd", "."],
                    cwd="/tmp",
                    started_at="2026-04-24T00:00:00Z",
                    completed_at="2026-04-24T00:00:01Z",
                    duration_ms=1000,
                    exit_code=0,
                    status="passed",
                    stdout_path="/tmp/stdout.txt",
                    stderr_path="/tmp/stderr.txt",
                    stdout_sha256="hash-a",
                    stderr_sha256="hash-b",
                    tool_name="jscpd",
                    tool_version="1.0.0",
                )
            ],
            lane_drafts=lane_drafts,
            findings=findings,
            overall_classification="completed",
            created_at="2026-04-24T00:00:03Z",
        )

        self.assertEqual(lane_drafts[0]["summary"], "Generated mirror file is intentionally redundant.")
        self.assertEqual(lane_drafts[0]["lane_details"]["exception_id"], "ex-1")
        self.assertEqual(findings[0]["operator_decision"], "accepted_exception")
        self.assertFalse(findings[0]["safe_to_autofix"])
        self.assertTrue(findings[0]["requires_operator_review"])
        lane_score = next(item for item in scores if item["scope"] == "lane")
        self.assertEqual(lane_score["confidence_counts"]["moderate"], 1)
        self.assertEqual(lane_score["safe_to_autofix_count"], 0)

    def test_real_run_writes_era_scores(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            temp_path = Path(temp_root)
            era_root = temp_path / "era"
            repo = temp_path / "repo"
            era_root.mkdir()
            repo.mkdir()
            init_git_repo(repo)
            run_dir = execute_run(
                repo_path=repo,
                lanes=["accuracy"],
                mode="full",
                artifacts_root=era_root / "artifacts" / "era-runs",
            )
            findings = json.loads((run_dir / "findings.json").read_text(encoding="utf-8"))
            score_ids = {item["score_id"] for item in findings["era_scores"]}
            self.assertIn("score:overall", score_ids)
            self.assertIn("score:lane:accuracy", score_ids)


if __name__ == "__main__":
    unittest.main()
