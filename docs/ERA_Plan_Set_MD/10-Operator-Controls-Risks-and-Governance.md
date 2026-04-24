# ERA Operator Controls, Risks, and Governance

**Date:** 2026-04-23  
**Time:** EDT  
**Owner:** BDS / Charlie  
**System posture:** Internal business systems control surface  

---

## 1. Governance posture

ERA is a high-discipline internal control surface. It must reduce uncertainty without taking authority away from the operator.

Operator authority remains central.

```text
ERA reports.
Operator reviews.
SMITH governs mutation.
```

---

## 2. Major risks and controls

| Risk | Control |
|---|---|
| ERA becomes an uncontrolled agent | Keep ERA read-only and evidence-focused |
| Redundancy scan causes unsafe deletion | No automatic deletion; operator review only |
| Tool output becomes brittle | Use tool-specific normalizers and intermediate contracts |
| Operator overload | Group, dedupe, prioritize, suppress with reason |
| Efficiency tests become noisy | Require workload manifests, repeated runs, environment metadata |
| Accuracy gates become superficial | Add contract, property, mutation, and regression gates over time |
| Missing tools create false negatives | Classify as `blocked_by_missing_tool` |
| LLM triage becomes authority | Treat LLM analysis as advisory only |
| DataForge outage blocks work | Local artifact mode remains first-class |
| Self-Healing bypasses operator | Require Centipede projection and ForgeCommand review |
| Patch workflow bypasses governance | Route mutation through SMITH receipts |
| Incident closes without proof | Require post-patch ERA verification |
| Test selection creates false confidence | Require `TestSelectionArtifact.v1` and safety class |
| Read-only command changes repo | Capture before/after git state |

---

## 3. Operator decisions

Supported operator decisions:

```text
accept_finding
reject_finding
mark_intentional
needs_more_evidence
create_patch_candidate
suppress_until_changed
suppress_until_date
escalate_to_audit
```

Operator decision records should include:

```text
decision_id
finding_id
run_id
operator_id
decision
reason
created_at
review_after
linked_patch_candidate_id
linked_receipt_id
```

---

## 4. Intentional redundancy exception

`IntentionalRedundancyException.v1` fields:

```text
exception_id
repo_id
file_paths
symbol_refs
reason
approved_by
approved_at
review_after
source_finding_id
evidence_refs
```

Rules:

```text
Exceptions expire or require review.
Exceptions do not delete underlying evidence.
Exceptions are operator decisions, not parser decisions.
```

---

## 5. Finding budget policy

To avoid overload, ERA should support:

```text
max_high_risk_findings_displayed
group_low_confidence_findings
hide_repeated_suppressed_findings_by_default
show_new_or_worsened_first
show_blocked_gates separately
separate evidence failures from code failures
```

Suggested first budgets:

```text
show all high risk
show first 25 medium risk
group low-confidence redundancy candidates
always show read-only invariant failure
always show post-patch verification failure
```

---

## 6. Release-gate policy

Release-gate runs require stricter defaults:

```text
full accuracy run
no heuristic-only selected-test proof
all critical tools available
read-only invariant verified
artifact validation passed
hash chain complete
no blocked required gates
Centipede export valid
```

---

## 7. Post-patch policy

After patch application:

```text
ERA must rerun relevant accuracy gate.
Post-patch verification evidence must be imported into Centipede.
Self-Healing incident must remain open until verification is reviewed.
Failure becomes a new incident or escalation.
AAR must capture outcome.
```

---

## 8. LLM / NeuroForge advisory boundary

Allowed:

```text
LLM explains possible causes.
LLM compares findings.
LLM proposes review questions.
LLM suggests candidate controls.
LLM summarizes tradeoffs for the operator.
```

Forbidden:

```text
LLM upgrades a finding to proven.
LLM downgrades mechanical failures.
LLM approves remediation.
LLM replaces raw tool evidence.
LLM suppresses a finding without operator decision.
```

Field name:

```text
advisory_analysis_ref
```

Not:

```text
proof_ref
```

---

## 9. Rust hardening track

Rust may later strengthen:

```text
artifact hashing
process isolation
command allowlist enforcement
large artifact validation
signed receipt preparation
parallel runner supervision
```

Do not claim:

```text
Rust = federal-grade compliance
Rust = CMMC compliance
Rust = sufficient evidence integrity by itself
```

Correct posture:

```text
Rust may strengthen selected ERA controls where type safety, process control, and artifact integrity matter.
```

---

## 10. Operator-facing invariant

Every review artifact should include:

```text
ERA took no automatic repair action.
This finding is evidence for operator review.
Patch creation, application, and closure require downstream governance.
```
