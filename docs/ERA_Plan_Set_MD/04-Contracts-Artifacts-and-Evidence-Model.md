# ERA Contracts, Artifacts, and Evidence Model

**Date:** 2026-04-23  
**Time:** EDT  
**Owner:** BDS / Charlie  
**System posture:** Internal business systems control surface  

---

## 1. Contract family

ERA should define the following contract family.

```text
ERAEvaluationRun.v1
ERATargetManifest.v1
ERAToolAvailabilityReport.v1
ERACommandResult.v1
ToolRawArtifact.v1
ToolNormalizedResult.v1
LaneFindingDraft.v1
ERAFinding.v1
ERAEvidenceBundle.v1
ERAReviewArtifact.v1
ERAScore.v1
ERAOperatorDecision.v1
IntentionalRedundancyException.v1
TestSelectionArtifact.v1
CentipedeExportBundle.v1
PostPatchVerificationResult.v1
```

First slice may keep these as local JSON structures. Formal schema promotion to `forge-contract-core` comes after local proof.

---

## 2. ERAEvaluationRun.v1

Required fields:

```text
schema_version
run_id
repo_id
repo_path
commit_sha
branch
working_tree_status
is_dirty
lanes
mode
baseline_ref
baseline_commit
started_at
completed_at
status
operator_requested_by
runner_version
tool_versions
environment
artifact_root
target_manifest_path
tool_availability_path
test_selection_artifact_path
evidence_bundle_refs
finding_refs
review_artifact_ref
pre_run_git_status_short
post_run_git_status_short
read_only_invariant_status
```

Status values:

```text
completed
completed_partial
failed
blocked
aborted
```

---

## 3. ERATargetManifest.v1

Required fields:

```text
schema_version
repo_path
repo_name
repo_id
git_commit_sha
git_branch
working_tree_status
is_dirty
lockfile_hashes
detected_languages
detected_toolchains
captured_at
```

---

## 4. ERACommandResult.v1

Required fields:

```text
command_id
label
command
cwd
started_at
completed_at
duration_ms
exit_code
status
stdout_path
stderr_path
stdout_sha256
stderr_sha256
tool_name
tool_version
blocked_reason
```

Status values:

```text
passed
failed
skipped
blocked_by_missing_tool
blocked_by_unsupported_version
failed_to_execute
timed_out
```

---

## 5. ToolRawArtifact.v1

Purpose: Preserve raw evidence.

Required fields:

```text
raw_artifact_id
run_id
command_id
tool_name
tool_version
artifact_kind
path
sha256
created_at
```

No raw artifact means no clear mechanical finding.

---

## 6. ToolNormalizedResult.v1

Purpose: Convert raw tool output into a tool-neutral internal form.

Required fields:

```text
normalized_result_id
run_id
raw_artifact_refs
normalizer_name
normalizer_version
tool_name
tool_version
summary_status
parsed_findings
parse_warnings
parse_errors
created_at
sha256
```

Rule:

```text
Tool parsers write ToolNormalizedResult.v1, not ERAFinding.v1.
```

---

## 7. LaneFindingDraft.v1

Purpose: Convert normalized tool results into lane-specific finding drafts.

Required fields:

```text
draft_id
run_id
lane
finding_type
target_files
target_symbols
evidence_refs
risk_level
confidence
evidence_strength
recommended_action
blocked_reason
created_at
sha256
```

---

## 8. ERAFinding.v1

Canonical parent finding shape.

Required fields:

```text
finding_id
run_id
repo_id
commit_sha
lane
finding_type
target_files
target_symbols
evidence_refs
raw_evidence_refs
raw_evidence_hashes
risk_level
confidence
evidence_strength
recommended_action
safe_to_autofix
requires_operator_review
operator_decision
blocked_reason
created_at
```

Required rule:

```text
safe_to_autofix must be false for all initial internal-control slices.
```

---

## 9. TestSelectionArtifact.v1

Required for any selected-test / changed-files run.

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

Hard rules:

```text
No selected-test run without TestSelectionArtifact.v1.
No selected-test result may be presented as equivalent to full accuracy unless selection_safety_class supports that claim.
Release-gate and post-patch verification default to full run.
```

---

## 10. Artifact directory structure

Every ERA run writes:

```text
artifacts/era-runs/<run_id>/
  run.json
  target_manifest.json
  tool_availability.json
  test_selection_artifact.json
  review.md
  hashes.json
  evidence/
    accuracy/
      test_evidence_bundle.json
      commands/
        cargo_check.stdout.txt
        cargo_check.stderr.txt
        cargo_test.stdout.txt
        cargo_test.stderr.txt
        bun_test.stdout.txt
        bun_test.stderr.txt
        bun_build.stdout.txt
        bun_build.stderr.txt
    redundancy/
    efficiency/
  findings.json
  centipede_bundle.json
```

---

## 11. Evidence hash chain

Every mechanical finding must trace to raw evidence.

Required chain:

```text
raw stdout/stderr file
  -> sha256
  -> ToolRawArtifact.v1
  -> sha256
  -> ToolNormalizedResult.v1
  -> sha256
  -> LaneFindingDraft.v1
  -> sha256
  -> ERAFinding.v1
  -> included in ERAReviewArtifact.v1
```

No finding may be classified as `clear_issue` unless it includes:

```text
raw_evidence_ref
raw_evidence_hash
tool_name
tool_version
command_id
exit_code or parser_result
normalizer_name
normalizer_version
```

---

## 12. Centipede mapping

ERA local artifacts map into Centipede as follows.

| ERA artifact | Centipede equivalent |
|---|---|
| `ERAEvaluationRun.v1` | `RunCreated` |
| ERA lane status | `LaneAdmissionResult` |
| ERA hard-gate decisions | `CentipedeDecisionTraceRecord` |
| `ERAEvidenceBundle.v1` / finding evidence | `CentipedeEvidenceBundle` |
| Actionable ERA finding | `CentipedeSelfHealingProjection` |
| `centipede_bundle.json` | `CentipedeIntakeBundle` |

---

## 13. Self-Healing projection eligibility

Only create `CentipedeSelfHealingProjection` when all are true:

```text
finding is evidence-backed
affected scope is known
operator review is required
proposal generation may be useful
finding is not informational only
finding is not blocked by missing evidence
finding is not a known intentional exception
```

Projection candidates:

```text
accuracy_gate_failed
contract_accuracy_failed
read_only_invariant_failed
evidence_hash_chain_failed
post_patch_verification_failed
efficiency_regression_with_baseline
harmful_redundancy_with_drift
```

Non-candidates:

```text
missing tool with no target failure
informational benchmark result
intentional redundancy
low-confidence duplicate candidate
advisory-only RTS note
```
