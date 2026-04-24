# ERA System Architecture and Boundaries

**Date:** 2026-04-23  
**Time:** EDT  
**Owner:** BDS / Charlie  
**System posture:** Internal business systems control surface  

---

## 1. Architecture ruling

ERA should not feed Self-Healing directly.

ERA should feed **Centipede**. Centipede should reconcile, package, and project ERA evidence. Self-Healing should consume Centipede evidence and projections through the existing intake path.

Correct chain:

```text
ERA local run
  -> ERA artifacts
  -> ERA-to-Centipede adapter
  -> CentipedeIntakeBundle
  -> Centipede ledger
  -> Centipede evidence bundles + projection outbox
  -> Self-Healing Centipede adapter / projection intake
  -> Self-Healing incident queue
  -> ForgeCommand operator review
  -> SMITH / forge-smithy governed patch candidate
  -> post-patch ERA verification
  -> AAR / calibration / future control candidate
```

---

## 2. System responsibility split

| System | Role |
|---|---|
| Cortex | Observes structure, syntax, files, symbols, and future impact data |
| Centipede | Reconciles observations, packages evidence, projects downstream implications |
| ERA | Evaluates accuracy, redundancy, and efficiency evidence |
| forge-contract-core | Owns canonical cross-repo contracts |
| DataForge Local | Stores durable local evidence and run records |
| ForgeCommand | Presents operator review and decision surfaces |
| SMITH / forge-smithy | Governs mutation, patch receipts, approvals, and bounded repair |
| ForgeAgents | Executes governed workflows using ERA as a tool surface |
| Self-Healing | Operator-facing incident pipeline; not execution authority |
| DoppelCore | Receives Self-Healing incident intake receipts / source identity trail |
| AAR pipeline | Converts accepted findings/outcomes into lessons and future controls |

---

## 3. Current ForgeCommand bridge points

The current `Forge_Command` code already includes these integration surfaces:

```text
src-tauri/src/centipede/mod.rs
src-tauri/src/centipede/intake.rs
src-tauri/src/models/centipede.rs
src-tauri/src/centipede/contracts/projection.rs
src-tauri/src/centipede/persistence/models.rs
src-tauri/src/self_healing/centipede_evidence.rs
src-tauri/src/self_healing/projection_intake.rs
src-tauri/src/doppelcore/intake.rs
src/routes/self-healing/+page.svelte
src/lib/types/selfHealing.ts
```

The existing architecture already supports:

```text
Centipede intake bundles
lane admissions
decision traces
evidence bundles
self-healing projections
projection outbox
Self-Healing evidence adaptation
Self-Healing projection intake
DoppelCore intake receipts
operator UI queue
```

ERA should use these existing seams instead of creating a separate Self-Healing feed.

---

## 4. ERA's place in the loop

ERA is the **verification and evidence producer**.

It should produce:

```text
accuracy gate evidence
redundancy evidence
efficiency benchmark evidence
toolchain availability evidence
read-only invariant evidence
test-selection evidence
post-patch verification evidence
```

ERA should not produce:

```text
patches
merge decisions
approval decisions
operator decisions
runtime execution decisions
final remediation claims
```

---

## 5. Centipede as the evidence boundary

ERA should export Centipede-compatible bundles:

```text
CentipedeIntakeBundle
  run
  lane_admissions
  decision_traces
  evidence_bundles
  self_healing_projections
  registry_projections
  final_runtime_mode
```

This makes Centipede the durable reconciliation layer.

ERA findings enter the broader system only after becoming Centipede ledger records or projections.

---

## 6. Self-Healing as consumer, not authority

Self-Healing should consume only evidence/projections that have passed through Centipede.

Self-Healing may:

```text
map evidence into incidents
show proposal candidates
require operator review
hold blocked incidents
track projection receipts
feed DoppelCore intake receipts
```

Self-Healing may not:

```text
execute repairs
apply patches
close ERA-originated incidents without verification
override ERA evidence
override Centipede projections
override SMITH
```

---

## 7. SMITH / forge-smithy boundary

SMITH / forge-smithy owns governed mutation.

ERA-originated repair flow:

```text
ERA finding
  -> Centipede evidence bundle
  -> Centipede self_healing projection
  -> Self-Healing incident
  -> ForgeCommand operator approval
  -> SMITH patch-candidate generation
  -> receipt-backed patch application
  -> ERA post-patch verification
  -> incident transition
```

No direct ERA-to-patch path is allowed.

---

## 8. Architecture invariant

```text
Cortex observes.
ERA evaluates.
Centipede reconciles.
Self-Healing queues.
ForgeCommand reviews.
SMITH mutates.
ERA verifies.
AAR learns.
```
