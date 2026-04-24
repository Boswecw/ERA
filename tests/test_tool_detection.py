from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from era_core.selection import apply_selection_and_tooling, detect_accuracy_commands


class ToolDetectionTests(unittest.TestCase):
    def test_missing_tool_is_blocked_not_failed_accuracy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            repo = Path(temp_root)
            (repo / "src-tauri").mkdir()
            (repo / "src-tauri" / "Cargo.toml").write_text("[package]\nname='x'\nversion='0.1.0'\n", encoding="utf-8")
            commands = detect_accuracy_commands(repo)
            selection = {
                "mode": "full",
                "full_run_required": True,
                "fallback_reason": None,
            }
            planned = apply_selection_and_tooling(
                commands,
                [
                    {"tool": "cargo", "status": "missing"},
                    {"tool": "bun", "status": "not_applicable"},
                ],
                selection,
            )
            cargo_items = [item for item in planned if item.tool_name == "cargo"]
            self.assertTrue(cargo_items)
            self.assertTrue(all(item.planned_status == "blocked_by_missing_tool" for item in cargo_items))


if __name__ == "__main__":
    unittest.main()
