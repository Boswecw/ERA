# ERA-01A — Local Read-Only Accuracy Proof

**Date:** 2026-04-23  
**Time:** EDT  
**Owner:** BDS / Charlie  
**System posture:** Internal business systems control surface  

---

## 1. Objective

Build the first ERA proof as a local, read-only Python CLI that evaluates accuracy gates against one target repository and writes evidence artifacts.

This is an internal-control proof, not an MVP.

---

## 2. Scope

```text
Target ERA repo:
~/Forge/ecosystem/ERA

Evaluation target repo:
~/Forge/ecosystem/Forge_Command

Lane:
accuracy only

Mutation:
disabled

Persistence:
local JSON/Markdown artifacts only

Centipede export:
optional adapter output after local proof

DataForge Local:
not required in this slice

ForgeCommand UI:
not required in this slice
```

---

## 3. Required CLI commands

```bash
python -m era_cli run --repo ~/Forge/ecosystem/Forge_Command --lanes accuracy --mode full

python -m era_cli run --repo ~/Forge/ecosystem/Forge_Command --lanes accuracy --mode changed-files --baseline main

python -m era_cli report --latest

python -m era_cli validate --latest
```

---

## 4. Minimal file layout

```text
ERA/
  pyproject.toml
  README.md
  AGENTS.md
  era_cli/
    __init__.py
    __main__.py
    main.py
    commands/
      __init__.py
      run.py
      report.py
      validate.py
  era_core/
    __init__.py
    artifact_paths.py
    command_runner.py
    git_info.py
    hashing.py
    models.py
    review_writer.py
    tool_detection.py
    selection.py
    validation.py
  era_integrations/
    __init__.py
    centipede_export.py
  tests/
    test_artifact_generation.py
    test_validation.py
    test_git_snapshot.py
    test_tool_detection.py
    test_selection_artifact.py
  artifacts/
    .gitkeep
```

---

## 5. Accuracy command selection

Auto-detect but do not guess unsafely.

Detection rules:

```text
If src-tauri/Cargo.toml exists:
  enable cargo check and cargo test.

If package.json exists:
  inspect scripts.
  enable bun test only if a test script exists.
  enable bun run build only if a build script exists.

If command cannot be inferred:
  mark skipped, not passed.
```

Initial target commands:

```bash
cargo check --manifest-path src-tauri/Cargo.toml
cargo test --manifest-path src-tauri/Cargo.toml
bun test
bun run build
```

---

## 6. Read-only guardrails

Hard rule:

```text
Never write artifacts inside the evaluated repo.
```

Denylist:

```text
rm
mv
cp into target repo
sed -i
perl -pi
git checkout
git reset
git clean
git stash
git add
git commit
bun install
npm install
cargo fix
cargo fmt
cargo clippy --fix
```

Allowlist for ERA-01A:

```text
git status --short
git rev-parse HEAD
git branch --show-current
git ls-files
git diff --name-only <baseline>...HEAD
cargo check
cargo test
bun test
bun run build
```

---

## 7. Before/after repo snapshot

Every run captures:

```text
pre_run_git_status_short
post_run_git_status_short
pre_run_head
post_run_head
pre_run_dirty
post_run_dirty
read_only_invariant_status
read_only_invariant_notes
```

Read-only invariant classifications:

```text
clean_verified
preexisting_dirty_tree
post_run_changed_tree
head_changed_during_run
read_only_invariant_failed
```

Rule:

```text
If post-run target repo state differs from pre-run state, ERA must mark read_only_invariant_failed unless difference is explicitly explained by allowed ignored/cache files outside source truth.
```

---

## 8. Tool availability checks

Check:

```text
git
python
cargo if Rust manifest exists
bun if package.json exists
```

Tool status values:

```text
available
missing
version_unsupported
permission_denied
failed_to_execute
not_applicable
```

Missing required tools produce:

```text
blocked_by_missing_tool
```

ERA must not install tools.

---

## 9. Exit code policy

ERA exits `0` when:

```text
ERA completed the run and wrote artifacts, even if target tests failed.
```

ERA exits non-zero when:

```text
ERA itself crashed
artifact writing failed
validation failed
target repo path is invalid
local artifact schema is invalid
```

Target repo failure is evidence, not an ERA crash.

---

## 10. Review artifact

`review.md` must include:

```text
# ERA Accuracy Review

Run ID
Target Repo
Commit SHA
Branch
Working Tree Dirty Status
Started / Completed
Overall Status

## Delta / RTS Summary
baseline
changed files
selected tests
full gates run or not
selection method
confidence classification
fallback reason

## Tool Availability
tool, status, version, note

## Command Summary
label, status, exit code, duration, stdout, stderr

## Accuracy Classification
accurate_enough_for_review | inaccurate | unproven | blocked_by_missing_evidence

## Failed Commands
details and artifact links

## Skipped / Blocked Commands
why each command was skipped or blocked

## Read-Only Invariant
before/after state

## Operator Notes
No automatic action was taken.
ERA is read-only.
```

---

## 11. Validation rules

`python -m era_cli validate --latest` verifies:

```text
run.json exists
target_manifest.json exists
tool_availability.json exists
review.md exists
test_evidence_bundle.json exists
schema_version fields exist
run_id matches across artifacts
artifact paths exist
command stdout/stderr files exist for executed commands
hashes.json exists or is generated
hash references are valid
TestSelectionArtifact.v1 exists when changed-files mode is used
```

---

## 12. Unit tests

Minimum tests:

```text
test_run_id_generation
test_artifact_paths_created_outside_target_repo
test_target_manifest_requires_commit_or_dirty_marker
test_command_result_serialization
test_validation_fails_when_required_artifact_missing
test_review_markdown_created
test_skipped_command_is_not_marked_passed
test_missing_tool_is_blocked_not_failed_accuracy
test_pre_post_git_snapshot_recorded
test_changed_files_mode_writes_selection_artifact
test_changed_files_mode_falls_back_to_full_when_uncertain
```

Use temporary directories for tests. Do not require the real `Forge_Command` repo for unit tests.

---

## 13. Definition of done

ERA-01A is complete when:

```text
ERA repo skeleton exists.
CLI runs with python -m era_cli.
Accuracy lane runs against Forge_Command.
Artifacts are written under ERA/artifacts/era-runs/<run_id>/.
Target repo source truth is not modified.
Pre-run and post-run git snapshots are captured.
Read-only invariant status is recorded.
Tool availability is checked and recorded.
Skipped commands are recorded honestly.
Missing tools are recorded as blocked_by_missing_tool.
Failed target tests are recorded as evidence, not ERA crashes.
Raw stdout/stderr artifacts are hashed.
ToolRawArtifact records exist for executed commands.
ToolNormalizedResult records exist for parsed command outcomes.
LaneFindingDraft records exist where findings are generated.
ERAFinding records reference raw evidence hashes.
review.md includes a Delta / RTS Summary.
--mode full works.
--mode changed-files captures baseline and changed files.
Changed-files mode falls back to full gates when safe selection is uncertain.
Validation command verifies artifact completeness and hash references.
Unit tests cover artifact generation, validation, skipped commands, missing tools, and before/after snapshots.
```
