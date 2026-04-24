from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from era_cli.commands.run import execute_run
from tests.test_artifact_generation import init_git_repo


class GitSnapshotTests(unittest.TestCase):
    def test_pre_post_git_snapshot_recorded(self) -> None:
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
            run_artifact = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertIn("pre_run_git_status_short", run_artifact)
            self.assertIn("post_run_git_status_short", run_artifact)
            self.assertIn("read_only_invariant_status", run_artifact)


if __name__ == "__main__":
    unittest.main()
