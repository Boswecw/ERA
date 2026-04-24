from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from era_cli.commands.run import execute_run
from tests.test_artifact_generation import init_git_repo


class SelectionArtifactTests(unittest.TestCase):
    def test_changed_files_mode_without_baseline_records_unknown_full_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            temp_path = Path(temp_root)
            era_root = temp_path / "era"
            repo = temp_path / "repo"
            era_root.mkdir()
            repo.mkdir()
            init_git_repo(repo)
            (repo / "README.md").write_text("changed\n", encoding="utf-8")
            run_dir = execute_run(
                repo_path=repo,
                lanes=["accuracy"],
                mode="changed-files",
                artifacts_root=era_root / "artifacts" / "era-runs",
            )
            selection = json.loads((run_dir / "test_selection_artifact.json").read_text(encoding="utf-8"))
            self.assertEqual(selection["selection_safety_class"], "unknown")
            self.assertTrue(selection["full_run_required"])
            self.assertIn("No baseline ref", selection["fallback_reason"])

    def test_changed_files_mode_with_no_changes_records_advisory_noop(self) -> None:
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
                mode="changed-files",
                baseline_ref="main",
                artifacts_root=era_root / "artifacts" / "era-runs",
            )
            selection = json.loads((run_dir / "test_selection_artifact.json").read_text(encoding="utf-8"))
            self.assertEqual(selection["selection_method"], "changed_file_metadata_no_changes")
            self.assertEqual(selection["selection_safety_class"], "advisory_only")
            self.assertFalse(selection["full_run_required"])

    def test_changed_files_mode_writes_selection_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            temp_path = Path(temp_root)
            era_root = temp_path / "era"
            repo = temp_path / "repo"
            era_root.mkdir()
            repo.mkdir()
            init_git_repo(repo)
            (repo / "README.md").write_text("changed\n", encoding="utf-8")
            run_dir = execute_run(
                repo_path=repo,
                lanes=["accuracy"],
                mode="changed-files",
                baseline_ref="main",
                artifacts_root=era_root / "artifacts" / "era-runs",
            )
            selection = json.loads((run_dir / "test_selection_artifact.json").read_text(encoding="utf-8"))
            review = (run_dir / "review.md").read_text(encoding="utf-8")
            self.assertEqual(selection["schema_version"], "TestSelectionArtifact.v1")
            self.assertIn("README.md", selection["changed_files"])
            self.assertEqual(selection["changed_file_classification"]["documentation"], ["README.md"])
            self.assertIn("- current commit:", review)
            self.assertIn("- RTS level cap:", review)

    def test_changed_files_mode_falls_back_to_full_when_uncertain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            temp_path = Path(temp_root)
            era_root = temp_path / "era"
            repo = temp_path / "repo"
            era_root.mkdir()
            repo.mkdir()
            init_git_repo(repo)
            (repo / "src").mkdir()
            (repo / "src" / "app.ts").write_text("export const value = 1;\n", encoding="utf-8")
            run_dir = execute_run(
                repo_path=repo,
                lanes=["accuracy"],
                mode="changed-files",
                baseline_ref="main",
                artifacts_root=era_root / "artifacts" / "era-runs",
            )
            selection = json.loads((run_dir / "test_selection_artifact.json").read_text(encoding="utf-8"))
            self.assertTrue(selection["full_run_required"])
            self.assertEqual(selection["selection_level"], 1)
            self.assertIn("fell back", selection["selection_rationale"])

    def test_changed_test_file_records_advisory_level_two_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            temp_path = Path(temp_root)
            era_root = temp_path / "era"
            repo = temp_path / "repo"
            era_root.mkdir()
            repo.mkdir()
            init_git_repo(repo)
            (repo / "tests").mkdir()
            (repo / "tests" / "app.test.ts").write_text("test('x', () => {});\n", encoding="utf-8")
            run_dir = execute_run(
                repo_path=repo,
                lanes=["accuracy"],
                mode="changed-files",
                baseline_ref="main",
                artifacts_root=era_root / "artifacts" / "era-runs",
            )
            selection = json.loads((run_dir / "test_selection_artifact.json").read_text(encoding="utf-8"))
            self.assertEqual(selection["selection_level"], 2)
            self.assertEqual(selection["selection_method"], "changed_test_file_advisory_full_fallback")
            self.assertEqual(selection["selected_tests"], ["tests/app.test.ts"])
            self.assertTrue(selection["full_run_required"])


if __name__ == "__main__":
    unittest.main()
