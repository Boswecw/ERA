from __future__ import annotations

from pathlib import Path

from era_core.models import CommandResult


def determine_accuracy_classification(
    command_results: list[CommandResult],
    read_only_invariant_status: str,
) -> str:
    if read_only_invariant_status in {"read_only_invariant_failed", "head_changed_during_run"}:
        return "blocked_by_missing_evidence"
    if any(item.status in {"failed_to_execute", "timed_out"} for item in command_results):
        return "blocked_by_missing_evidence"
    if any(item.status == "failed" for item in command_results):
        return "inaccurate"
    if any(item.status == "blocked_by_missing_tool" for item in command_results):
        return "blocked_by_missing_evidence"
    if not any(item.status not in {"skipped", "blocked_by_missing_tool"} for item in command_results):
        return "unproven"
    return "accurate_enough_for_review"


def _fmt_path(path_value: str | None) -> str:
    return path_value or "n/a"


def write_review(
    run_artifact: dict[str, object],
    target_manifest: dict[str, object],
    tool_report: dict[str, object],
    selection_artifact: dict[str, object],
    evidence_bundle: dict[str, object],
    accuracy_classification: str,
    output_path: Path,
) -> None:
    command_results = [CommandResult(**item) for item in evidence_bundle["command_results"]]
    failed = [item for item in command_results if item.status in {"failed", "timed_out", "failed_to_execute"}]
    skipped_or_blocked = [item for item in command_results if item.status in {"skipped", "blocked_by_missing_tool"}]

    lines: list[str] = [
        "# ERA Accuracy Review",
        "",
        f"Run ID: `{run_artifact['run_id']}`",
        f"Target Repo: `{run_artifact['repo_path']}`",
        f"Commit SHA: `{run_artifact['commit_sha']}`",
        f"Branch: `{run_artifact['branch']}`",
        f"Working Tree Dirty Status: `{run_artifact['is_dirty']}`",
        f"Started / Completed: `{run_artifact['started_at']}` / `{run_artifact['completed_at']}`",
        f"Overall Status: `{run_artifact['status']}`",
        "",
        "## Delta / RTS Summary",
        f"- baseline: `{selection_artifact['baseline_ref'] or 'n/a'}`",
        f"- changed files: `{len(selection_artifact['changed_files'])}`",
        f"- selected tests: `{', '.join(selection_artifact['selected_tests']) or 'none'}`",
        f"- full gates run or not: `{selection_artifact['full_run_executed']}`",
        f"- selection method: `{selection_artifact['selection_method']}`",
        f"- confidence classification: `{selection_artifact['selection_safety_class']}`",
        f"- fallback reason: `{selection_artifact['fallback_reason'] or 'n/a'}`",
        "",
        "## Tool Availability",
        "| tool | status | version | note |",
        "|---|---|---|---|",
    ]
    for tool in tool_report["tools"]:
        lines.append(
            f"| {tool['tool']} | {tool['status']} | {tool['version'] or 'n/a'} | {tool['note'] or 'n/a'} |"
        )

    lines.extend(
        [
            "",
            "## Command Summary",
            "| label | status | exit code | duration ms | stdout | stderr |",
            "|---|---|---:|---:|---|---|",
        ]
    )
    for result in command_results:
        lines.append(
            "| "
            + " | ".join(
                [
                    result.label,
                    result.status,
                    str(result.exit_code) if result.exit_code is not None else "n/a",
                    str(result.duration_ms),
                    _fmt_path(result.stdout_path),
                    _fmt_path(result.stderr_path),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Accuracy Classification",
            accuracy_classification,
            "",
            "## Failed Commands",
        ]
    )
    if failed:
        for item in failed:
            lines.append(
                f"- `{item.label}` status=`{item.status}` exit_code=`{item.exit_code}` stdout=`{_fmt_path(item.stdout_path)}` stderr=`{_fmt_path(item.stderr_path)}`"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Skipped / Blocked Commands"])
    if skipped_or_blocked:
        for item in skipped_or_blocked:
            lines.append(
                f"- `{item.label}` status=`{item.status}` reason=`{item.blocked_reason or 'n/a'}`"
            )
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Read-Only Invariant",
            f"- status: `{run_artifact['read_only_invariant_status']}`",
            f"- before: `{run_artifact['pre_run_git_status_short'] or 'clean'}`",
            f"- after: `{run_artifact['post_run_git_status_short'] or 'clean'}`",
            f"- notes: `{run_artifact['read_only_invariant_notes']}`",
            "",
            "## Operator Notes",
            "- No automatic action was taken.",
            "- ERA is read-only.",
        ]
    )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
