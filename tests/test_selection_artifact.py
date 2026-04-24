from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from era_cli.commands.run import execute_run
from tests.test_artifact_generation import init_git_repo


class SelectionArtifactTests(unittest.TestCase):
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
            self.assertEqual(selection["schema_version"], "TestSelectionArtifact.v1")
            self.assertIn("README.md", selection["changed_files"])

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
            self.assertIn("fell back", selection["selection_rationale"])


if __name__ == "__main__":
    unittest.main()
