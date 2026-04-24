# RTS and Differential ERA Plan

**Date:** 2026-04-23  
**Time:** EDT  
**Owner:** BDS / Charlie  
**System posture:** Internal business systems control surface  

---

## 1. Core ruling

Regression Test Selection should become a first-class ERA Accuracy-lane concept.

ERA must distinguish:

```text
safe RTS
safe-enough RTS
heuristic changed-file selection
full retest-all fallback
```

These are not interchangeable.

ERA must never imply that heuristic changed-files mode is fully safe unless the selection method supports that claim.

---

## 2. Progressive RTS levels

```text
Level 0 — Full Retest-All
Runs all configured gates. Highest confidence, highest cost.

Level 1 — Changed-File Metadata
Captures baseline and changed files, but still runs full gates unless safe selection is obvious.

Level 2 — File-Level Heuristic Selection
Runs tests directly associated with changed files. Fast and useful, but not fully safe.

Level 3 — Manifest-Based Selection
Uses project-owned mappings of source files, packages, routes, contracts, and tests.

Level 4 — Coverage-Assisted Selection
Uses prior coverage data to select tests that exercised changed files/symbols.

Level 5 — Symbol / Call-Graph Selection
Uses Cortex or equivalent structural analysis to map changed symbols to affected tests and workflows.

Level 6 — CFG-Based Safe RTS
Uses control-flow / modification-traversing analysis for selected high-assurance paths.
```

ERA-01A implements:

```text
Level 0 required
Level 1 required
Level 2 allowed only when obvious and safely explainable
```

ERA-01A does not implement:

```text
coverage-assisted RTS
Cortex symbol-level selection
CFG-based safe RTS
edge coverage history
external RTS tool integration
```

---

## 3. TestSelectionArtifact.v1

Required fields:

```text
schema_version
run_id
repo_id
baseline_ref
baseline_commit
current_commit
mode
selection_level
selection_method
selection_safety_class
changed_files
changed_symbols
candidate_tests
selected_tests
excluded_tests
full_run_required
full_run_executed
fallback_reason
coverage_snapshot_ref
manifest_mapping_ref
rts_tool_name
rts_tool_version
selection_rationale
created_at
```

Safety classifications:

```text
full_retest_all
safe
safe_enough
heuristic
advisory_only
unknown
```

---

## 4. Accuracy lane RTS rules

Hard rules:

```text
No selected-test run without TestSelectionArtifact.v1.
No selected-test result may be presented as equivalent to full accuracy unless the selection_safety_class supports that claim.
Release-gate and post-patch SMITH verification default to full run.
```

Changed-files mode rule:

```text
If changed-files mode cannot safely map changes to specific tests, ERA must run the full configured accuracy gate and record why selective execution was not used.
```

---

## 5. Differential mode commands

Required:

```bash
python -m era_cli run --repo ~/Forge/ecosystem/Forge_Command --lanes accuracy --mode full

python -m era_cli run --repo ~/Forge/ecosystem/Forge_Command --lanes accuracy --mode changed-files --baseline main
```

Future:

```bash
python -m era_cli run --repo ~/Forge/ecosystem/Forge_Command --lanes accuracy --mode targeted --target src-tauri/src/centipede

python -m era_cli run --repo ~/Forge/ecosystem/Forge_Command --lanes accuracy,redundancy,efficiency --mode release-gate
```

---

## 6. Mode policy

| Mode | Allowed RTS level | Use |
|---|---:|---|
| quick | 1–2 | Daily local triage |
| changed-files | 1–2 | Developer loop |
| targeted | 2–3 | Specific subsystem work |
| full | 0 | Complete gate run |
| release-gate | 0 by default; 5–6 only if validated | High confidence |
| post-patch | 0 by default | Self-Healing closure gate |
| audit | 0 plus metadata comparison | Deep review |

---

## 7. Cortex future integration

Future flow:

```text
git diff
  -> Cortex structural scan
  -> changed symbols / affected symbols
  -> TestSelectionArtifact.v1
  -> ERA Accuracy run
  -> ERAReviewArtifact.v1
  -> Centipede bundle
```

Cortex remains observational. ERA consumes Cortex output as evidence input. ERA does not make Cortex an authority.

---

## 8. Review output

`review.md` must include:

```text
Delta / RTS Summary
- baseline
- current commit
- changed files
- selected tests
- full gates run or not
- selection method
- selection safety class
- fallback reason
```

---

## 9. Acceptance criteria

ERA-01A RTS support is complete when:

```text
changed-files mode captures baseline and changed files.
full mode runs configured accuracy gates normally.
changed-files mode produces TestSelectionArtifact.v1.
changed-files mode can fall back to full gate execution.
review.md reports selection method and fallback reason.
selected-test output is not overstated as full proof.
validation verifies TestSelectionArtifact.v1 when changed-files mode is used.
unit tests cover no-baseline, no-changes, changed-source, changed-test, and fallback-to-full cases.
```
