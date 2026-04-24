from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from era_cli.commands.run import execute_run
from era_core.hashing import sha256_json
from era_core.validation import validate_run_dir
from tests.test_artifact_generation import init_git_repo


class HashChainTests(unittest.TestCase):
    def test_real_run_writes_structural_hash_chain(self) -> None:
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

            hashes = json.loads((run_dir / "hashes.json").read_text(encoding="utf-8"))
            review = (run_dir / "review.md").read_text(encoding="utf-8")
            chain = hashes["evidence_hash_chain"]

            self.assertEqual(chain["schema_version"], "ERAEvidenceHashChain.v1")
            self.assertEqual(chain["review_artifact"]["path"], "review.md")
            self.assertIn("score:overall", {item["score_id"] for item in chain["era_scores"]})
            self.assertIn(chain["findings_bundle"]["sha256"], review)
            result = validate_run_dir(run_dir)
            self.assertTrue(result["ok"], msg="\n".join(result["errors"]))

    def test_validation_fails_when_hash_chain_score_hash_is_stale(self) -> None:
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

            hashes_path = run_dir / "hashes.json"
            hashes = json.loads(hashes_path.read_text(encoding="utf-8"))
            hashes["evidence_hash_chain"]["era_scores"][0]["sha256"] = "stale"
            hashes_path.write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = validate_run_dir(run_dir)
            self.assertFalse(result["ok"])
            self.assertTrue(any("stale score hash" in error for error in result["errors"]))

    def test_validation_fails_when_clear_issue_lacks_raw_evidence(self) -> None:
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

            findings_path = run_dir / "findings.json"
            findings = json.loads(findings_path.read_text(encoding="utf-8"))
            findings["era_findings"].append(
                {
                    "schema_version": "ERAFinding.v1",
                    "finding_id": "finding:clear_issue_without_raw",
                    "run_id": findings["run_id"],
                    "repo_id": findings["repo_id"],
                    "commit_sha": "abc123",
                    "lane": "accuracy",
                    "finding_type": "clear_issue",
                    "summary": "Synthetic validation fixture.",
                    "target_files": [],
                    "target_symbols": [],
                    "evidence_refs": [],
                    "raw_evidence_refs": [],
                    "raw_evidence_hashes": [],
                    "risk_level": "high",
                    "confidence": "high",
                    "evidence_strength": "mechanical",
                    "recommended_action": "operator_review",
                    "safe_to_autofix": False,
                    "requires_operator_review": True,
                    "operator_decision": "pending",
                    "blocked_reason": None,
                    "created_at": "2026-04-24T00:00:00Z",
                }
            )
            comparable = dict(findings)
            comparable.pop("sha256", None)
            findings["sha256"] = sha256_json(comparable)
            findings_path.write_text(json.dumps(findings, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = validate_run_dir(run_dir)
            self.assertFalse(result["ok"])
            self.assertTrue(any("clear_issue" in error and "raw_evidence" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
