# Self-Healing Feed and Post-Patch Verification Plan

**Date:** 2026-04-23  
**Time:** EDT  
**Owner:** BDS / Charlie  
**System posture:** Internal business systems control surface  

---

## 1. Ruling

ERA feeds Self-Healing only through Centipede.

Self-Healing should never treat ERA as a direct repair engine.

Correct feed:

```text
ERA finding
  -> Centipede evidence bundle
  -> Centipede self_healing projection
  -> Self-Healing projection intake
  -> Self-Healing incident queue
  -> ForgeCommand operator review
```

---

## 2. Existing Self-Healing intake modes

### Path A — Current evidence adaptation

```text
Centipede run
  -> selfHealingAdaptCentipedeRunEvidence(run_id)
  -> Self-Healing incident
```

Use when the operator needs to review evidence without a repair projection.

### Path B — Projection intake

```text
Centipede self_healing projection outbox
  -> selfHealingIntakeCentipedeProjection(projection_id)
  -> Self-Healing incident
  -> DoppelCore intake receipt
  -> projection marked consumed / blocked
```

Use when the ERA finding may become a governed repair candidate.

---

## 3. Self-Healing incident status mapping

| ERA / Centipede condition | Self-Healing posture |
|---|---|
| Evidence present, no projection | `evidence_ready` |
| Projection valid and proposal required | `proposal_candidate` |
| Evidence missing / confidence none / projection invalid | `blocked` |
| Projection consumed | receipt-backed consumed state |
| Projection superseded / expired | blocked or skipped |

---

## 4. Proposal candidate requirements

A Self-Healing incident may become proposal candidate only when:

```text
Centipede projection kind is self_healing
projection lifecycle is valid
evidence bundle exists
evidence bundle matches source run/repo/revision
confidence_posture is not none
supporting lanes/traces are present when referenced
evidence payloads or traces exist
operator_review_required is true
proposal_required is true
```

---

## 5. SMITH handoff

ForgeCommand should allow a SMITH / forge-smithy patch-candidate request only when:

```text
operator explicitly approves proposal generation
Self-Healing incident is proposal_candidate
Centipede projection receipt exists or can be created
ERA evidence bundle exists
raw evidence hash validates
affected scope exists
repo state still matches revision or drift is acknowledged
patch scope is bounded
receipt generation is required
```

---

## 6. Post-patch verification rule

Hard rule:

```text
No ERA-originated Self-Healing incident may close from a repair unless a post-patch ERA verification run succeeds.
```

Post-patch flow:

```text
SMITH applies patch with receipt
  -> ERA reruns accuracy lane
  -> ERA creates post_patch_verification run
  -> ERA exports Centipede bundle
  -> Centipede imports verification evidence
  -> Self-Healing links verification to incident
  -> operator reviews closure
  -> AAR candidate generated
```

---

## 7. PostPatchVerificationResult.v1

Required fields:

```text
schema_version
verification_id
source_incident_id
source_projection_id
source_patch_receipt_id
repo_id
pre_patch_commit
post_patch_commit
era_run_id
centipede_run_id
verification_status
accuracy_status
regression_status
read_only_invariant_status
failed_gates
evidence_bundle_refs
review_artifact_ref
operator_review_required
created_at
```

Status values:

```text
passed
failed
blocked
unproven
requires_operator_review
```

---

## 8. Closure policy

| Verification outcome | Incident action |
|---|---|
| passed | eligible for operator-reviewed closure |
| failed | remain open / escalate |
| blocked | remain blocked |
| unproven | remain open |
| requires_operator_review | hold in review queue |

No automatic closure.

---

## 9. AAR feedback

After accepted repair or failure:

```text
ERA finding
operator decision
patch candidate outcome
post-patch verification result
regression status
incident context
```

becomes:

```text
AARLessonArtifact.v1
AAREvalCandidate.v1
AARControlCandidate.v1
```

AAR may propose:

```text
new test
new contract gate
new ERA normalizer check
new suppression policy
new workload manifest
new documentation control
new operator warning
```

AAR does not train or mutate anything directly.

---

## 10. ERA-SH-01 slice

### Objective

Prove ERA-originated Centipede projection appears in Self-Healing.

### Acceptance

```text
Centipede bundle imported
Self-Healing evidence synced
self_healing projection intake works
incident appears in queue
incident has raw_evidence_sha256
incident has normalized_digest_sha256
proposal_posture is correct
review_posture is operator_review_required or blocked
projection receipt is recorded
DoppelCore intake receipt exists when projection is consumed
```

---

## 11. ERA-SH-02 slice

### Objective

Require post-patch ERA verification before incident closure.

### Acceptance

```text
patch receipt exists
ERA post-patch run exists
Centipede imports post-patch verification evidence
incident remains open unless verification evidence passes
operator reviews closure
AAR candidate generated
```

---

## 12. Self-Healing invariant

```text
Self-Healing is an incident and operator decision surface.
Self-Healing is not an execution engine.
Self-Healing must not close ERA-originated repair incidents without ERA verification.
```
