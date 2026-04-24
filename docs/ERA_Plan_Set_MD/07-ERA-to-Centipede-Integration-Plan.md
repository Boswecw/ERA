# ERA to Centipede Integration Plan

**Date:** 2026-04-23  
**Time:** EDT  
**Owner:** BDS / Charlie  
**System posture:** Internal business systems control surface  

---

## 1. Integration ruling

ERA should export evidence into Centipede, not directly into Self-Healing.

Correct path:

```text
ERA artifacts
  -> ERA-to-Centipede adapter
  -> CentipedeIntakeBundle
  -> Centipede ledger
  -> evidence bundles
  -> projection outbox
```

---

## 2. Required output

ERA creates:

```text
artifacts/era-runs/<run_id>/centipede_bundle.json
```

This file should be importable by the existing Centipede intake service.

---

## 3. Centipede bundle shape

ERA should generate:

```text
CentipedeIntakeBundle
  schema_version
  source_system
  run
  lane_admissions
  decision_traces
  evidence_bundles
  self_healing_projections
  registry_projections
  final_runtime_mode
  final_runtime_mode_observed_at
```

---

## 4. ERA run to RunCreated

Mapping:

| ERA field | Centipede RunCreated field |
|---|---|
| `run_id` | `run_id` |
| `repo_id` | `repository_id` |
| `commit_sha` / dirty anchor | `revision_anchor` |
| `started_at` | `observed_at` |
| `era-cli` | `producer_id` |
| ERA version | `producer_version` |
| mode/lane description | `operator_note` |

Recommended `run_class` mapping:

| ERA run | Centipede run_class |
|---|---|
| accuracy gate | `verification_only_run` |
| full A/R/E review | `targeted_reconciliation_run` |
| baseline comparison | `historical_comparison_run` |
| post-patch verification | `verification_only_run` |
| AAR/control tuning | `calibration_run` |

Initial runtime mode:

```text
created
```

Final runtime mode:

```text
completed
completed_partial
failed
reconciliation_required
```

---

## 5. ERA lanes to LaneAdmissionResult

ERA emits lane admissions such as:

```text
era_accuracy
era_redundancy
era_efficiency
era_read_only_invariant
era_toolchain_availability
era_rts_selection
era_evidence_hash_chain
```

Examples:

```text
lane_name: era_accuracy
admitted: true
lane_health_state: available
reason: cargo check/test evidence captured

lane_name: era_rts_selection
admitted: false
lane_health_state: degraded
reason: changed-files mode fell back to full run because test mapping was uncertain

lane_name: era_toolchain_availability
admitted: false
lane_health_state: unavailable
reason: bun missing; JS build/test gates blocked_by_missing_tool
```

---

## 6. ERA decisions to decision traces

ERA emits decision traces for hard gates.

Examples:

```text
decision_stage: era_accuracy_gate
decision_key: cargo_check
disposition: passed | failed | blocked | skipped
rationale: cargo check failed with compiler error / cargo unavailable / skipped because no Cargo.toml

decision_stage: era_read_only_invariant
decision_key: target_repo_status
disposition: passed | failed
rationale: pre/post git status matched / target repo changed during run

decision_stage: era_rts_selection
decision_key: changed_files_mode
disposition: fallback_to_full
rationale: no safe source-to-test mapping available
```

---

## 7. ERA findings to CentipedeEvidenceBundle

ERA finding classes:

```text
accuracy_gate_failed
read_only_invariant_failed
toolchain_blocked
evidence_hash_chain_failed
redundancy_candidate
efficiency_regression
rts_selection_uncertain
contract_accuracy_failed
post_patch_verification_failed
```

Mapping:

| ERA artifact | Centipede field |
|---|---|
| `ERAFinding.finding_id` | `finding_id` |
| raw stdout/stderr hashes | `EvidencePayloadRef.payload_sha256` |
| command / workload | `reproduction_contract` |
| affected file/symbol | `affected_scope` |
| unaffected scope | `non_affected_scope` |
| conflicting outputs | `contradiction_bundles` |
| target repo/commit | `repository_id`, `revision_anchor` |
| downstream hint | `downstream_consumer_hints` |

---

## 8. Self-Healing projection generation

ERA should create `CentipedeSelfHealingProjection` only when a finding qualifies.

Eligibility:

```text
finding is evidence-backed
affected scope is known
operator review is required
proposal generation may be useful
finding is not only informational
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

Projection mapping:

```text
finding_class: accuracy_gate_failed
severity: high | medium | low
confidence_posture: high | moderate | low
proof_type: static_evidence | dynamic_reproduction
execution_reach: build_only | test_only | runtime_reachable | unknown
affected_target_type: file | symbol | package | command | contract | repo
affected_target_key: exact file/symbol/command
suggested_remediation_kind: fix_compile | add_test | repair_contract | investigate_dependency | rerun_full_gate
proposal_required: true
operator_review_required: true
```

---

## 9. ERA-CENT-01 slice

### Objective

Build local ERA-to-Centipede export.

### Deliverable

```text
centipede_bundle.json
```

### Acceptance

```text
bundle has RunCreated
bundle has lane admissions
bundle has decision traces
bundle has evidence bundles
bundle validates through ForgeCommand Centipede intake
no self_healing_projection emitted unless finding qualifies
```

---

## 10. ERA-CENT-02 slice

### Objective

Add projection rules for Self-Healing-eligible findings.

### Acceptance

```text
only actionable evidence-backed findings produce projections
blocked findings remain evidence-only
operator_review_required always true
proposal_required only true when remediation is plausible
projection includes evidence_bundle_id
projection includes supporting lane ids
projection includes supporting trace ids
```

---

## 11. Integration invariant

```text
ERA evidence enters Centipede.
Centipede decides projection posture.
Self-Healing consumes Centipede projection.
```
