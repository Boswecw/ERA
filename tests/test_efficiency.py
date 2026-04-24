from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from era_cli.commands.run import execute_run
from era_core.validation import validate_run_dir
from tests.test_artifact_generation import init_git_repo


def write_efficiency_manifest(era_root: Path, repo_name: str, command: list[str], *, iterations: int = 3) -> None:
    manifests_dir = era_root / "config" / "workload_manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifests_dir / f"{repo_name.lower()}.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "EfficiencyWorkloadManifest.v1",
                "repo_id": repo_name,
                "baseline_selection_policy": "latest_prior_efficiency_run",
                "workloads": [
                    {
                        "workload_id": "sleep_probe",
                        "label": "sleep probe",
                        "category": "runtime_benchmark",
                        "command": command,
                        "cwd_subpath": ".",
                        "runner": "internal_timer",
                        "iterations": iterations,
                        "regression_threshold_pct": 500.0,
                        "improvement_threshold_pct": 500.0,
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


class EfficiencyTests(unittest.TestCase):
    def test_efficiency_without_manifest_is_unproven(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            temp_path = Path(temp_root)
            era_root = temp_path / "era"
            repo = temp_path / "repo"
            era_root.mkdir()
            repo.mkdir()
            init_git_repo(repo)
            run_dir = execute_run(
                repo_path=repo,
                lanes=["efficiency"],
                mode="full",
                artifacts_root=era_root / "artifacts" / "era-runs",
            )
            review = (run_dir / "review.md").read_text(encoding="utf-8")
            baseline = json.loads((run_dir / "evidence" / "efficiency" / "baseline_artifact.json").read_text(encoding="utf-8"))
            self.assertIn("## Efficiency Lane", review)
            self.assertFalse(baseline["baseline_found"])
            self.assertIn("Classification: `unproven`", review)

    def test_efficiency_manifest_run_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            temp_path = Path(temp_root)
            era_root = temp_path / "era"
            repo = temp_path / "repo"
            era_root.mkdir()
            repo.mkdir()
            init_git_repo(repo)
            write_efficiency_manifest(
                era_root,
                repo.name,
                ["python3", "-c", "import time; time.sleep(0.01)"],
            )
            run_dir = execute_run(
                repo_path=repo,
                lanes=["efficiency"],
                mode="full",
                artifacts_root=era_root / "artifacts" / "era-runs",
            )
            bundle = json.loads(
                (run_dir / "evidence" / "efficiency" / "efficiency_evidence_bundle.json").read_text(encoding="utf-8")
            )
            result = validate_run_dir(run_dir)
            self.assertEqual(bundle["schema_version"], "EfficiencyEvidenceBundle.v1")
            self.assertTrue(result["ok"], msg="\n".join(result["errors"]))

    def test_efficiency_second_run_uses_prior_run_as_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            temp_path = Path(temp_root)
            era_root = temp_path / "era"
            repo = temp_path / "repo"
            era_root.mkdir()
            repo.mkdir()
            init_git_repo(repo)
            write_efficiency_manifest(
                era_root,
                repo.name,
                ["python3", "-c", "import time; time.sleep(0.01)"],
            )
            execute_run(
                repo_path=repo,
                lanes=["efficiency"],
                mode="full",
                artifacts_root=era_root / "artifacts" / "era-runs",
            )
            second_run = execute_run(
                repo_path=repo,
                lanes=["efficiency"],
                mode="full",
                artifacts_root=era_root / "artifacts" / "era-runs",
            )
            baseline = json.loads((second_run / "evidence" / "efficiency" / "baseline_artifact.json").read_text(encoding="utf-8"))
            statuses = {item["comparison_status"] for item in baseline["comparisons"]}
            self.assertTrue(baseline["baseline_found"])
            self.assertTrue(statuses.intersection({"within_range", "unstable", "improvement", "regression"}))

    def test_efficiency_missing_tool_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            temp_path = Path(temp_root)
            era_root = temp_path / "era"
            repo = temp_path / "repo"
            era_root.mkdir()
            repo.mkdir()
            init_git_repo(repo)
            write_efficiency_manifest(
                era_root,
                repo.name,
                ["definitely_missing_tool_for_era", "--version"],
            )
            run_dir = execute_run(
                repo_path=repo,
                lanes=["efficiency"],
                mode="full",
                artifacts_root=era_root / "artifacts" / "era-runs",
            )
            bundle = json.loads(
                (run_dir / "evidence" / "efficiency" / "efficiency_evidence_bundle.json").read_text(encoding="utf-8")
            )
            self.assertEqual(bundle["command_results"][0]["status"], "blocked_by_missing_tool")


if __name__ == "__main__":
    unittest.main()
