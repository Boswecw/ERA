# ERA Implementation Roadmap and Slices

**Date:** 2026-04-23  
**Time:** EDT  
**Owner:** BDS / Charlie  
**System posture:** Internal business systems control surface  

---

## 1. Roadmap overview

```text
ERA-00     Charter, boundaries, vocabulary
ERA-01A    Local read-only accuracy proof
ERA-01B    Redundancy scan proof
ERA-01C    Efficiency workload proof
ERA-02     Unified finding normalization
ERA-03     Evidence hash chain and validation
ERA-04     Differential / RTS scaffolding
ERA-CENT-01 ERA-to-Centipede bundle export
ERA-CENT-02 Self-Healing projection rules
ERA-SH-01  Self-Healing incident mapping proof
ERA-SH-02  Post-patch verification gate
ERA-DF-01  DataForge Local persistence
ERA-FC-01  ForgeCommand review surface
ERA-AAR-01 AAR feedback loop
```

---

## 2. ERA-00 — Charter and vocabulary

Deliverables:

```text
README.md
AGENTS.md
docs/system/00-era-charter.md
docs/system/20-era-lanes.md
docs/system/BUILD.sh
```

Acceptance:

```text
ERA boundary is explicit.
ERA is read-only by default.
ERA does not own mutation authority.
ERA does not replace Cortex, Centipede, DataForge, ForgeCommand, SMITH, or ForgeAgents.
```

---

## 3. ERA-01A — Local read-only accuracy proof

Deliverables:

```text
Python CLI skeleton
target manifest capture
git metadata capture
tool availability checks
command runner
stdout/stderr capture
artifact hashing
review.md writer
validate command
changed-files metadata
TestSelectionArtifact.v1
```

Acceptance:

```text
accuracy lane runs against Forge_Command
target repo source truth is not modified
artifacts are written under ERA/artifacts/era-runs/<run_id>/
validation passes
```

---

## 4. ERA-01B — Redundancy scan proof

Deliverables:

```text
jscpd wrapper if available
knip wrapper if available
cargo tree --duplicates wrapper
redundancy normalizer
IntentionalRedundancyException.v1 local model
```

Acceptance:

```text
findings are review candidates, not defects
generated/test fixtures can be excluded
no automatic deletion recommendations
```

---

## 5. ERA-01C — Efficiency workload proof

Deliverables:

```text
workload manifest support
hyperfine wrapper or internal timer
baseline artifact model
benchmark variance classification
efficiency normalizer
```

Acceptance:

```text
no efficiency claim without workload
no regression/improvement claim without baseline
unstable results are marked unstable
```

---

## 6. ERA-02 — Unified finding normalization

Deliverables:

```text
ToolRawArtifact.v1
ToolNormalizedResult.v1
LaneFindingDraft.v1
ERAFinding.v1
ERAScore.v1
```

Acceptance:

```text
no tool parser writes ERAFinding.v1 directly
all lane findings share parent model
lane details are preserved
confidence and risk remain separate
```

---

## 7. ERA-03 — Evidence hash chain

Deliverables:

```text
hashes.json
raw artifact hashes
normalized result hashes
finding draft hashes
review artifact hash references
validate --latest hash verification
```

Acceptance:

```text
every mechanical finding traces to raw evidence
clear_issue requires raw_evidence_ref and raw_evidence_hash
validation fails on broken hash references
```

---

## 8. ERA-04 — Differential / RTS scaffolding

Deliverables:

```text
--mode full
--mode changed-files
--baseline
changed files capture
TestSelectionArtifact.v1
fallback to full gates
Delta / RTS Summary in review.md
```

Acceptance:

```text
changed-files mode never overstates proof
full run fallback works
selection safety class is recorded
```

---

## 9. ERA-CENT-01 — ERA-to-Centipede bundle export

Deliverables:

```text
centipede_bundle.json
RunCreated mapper
LaneAdmissionResult mapper
DecisionTrace mapper
CentipedeEvidenceBundle mapper
```

Acceptance:

```text
bundle imports through ForgeCommand Centipede intake
binding validation passes
import receipt reports counts correctly
```

---

## 10. ERA-CENT-02 — Self-Healing projection rules

Deliverables:

```text
projection eligibility policy
CentipedeSelfHealingProjection mapper
blocked/evidence-only behavior
projection lifecycle fields
```

Acceptance:

```text
only actionable evidence-backed findings produce projections
operator_review_required is always true
proposal_required only true when remediation is plausible
```

---

## 11. ERA-SH-01 — Self-Healing incident mapping proof

Deliverables:

```text
test fixture Centipede bundle with ERA projection
Self-Healing sync path proof
projection intake proof
DoppelCore intake receipt check
```

Acceptance:

```text
Self-Healing incident appears in queue
projection receipt exists
incident digest hashes exist
DoppelCore intake receipt exists when consumed
```

---

## 12. ERA-SH-02 — Post-patch verification gate

Deliverables:

```text
PostPatchVerificationResult.v1
incident closure policy
verification link from patch receipt to ERA run
Self-Healing closure guard
```

Acceptance:

```text
ERA-originated incident cannot close without passing post-patch ERA verification
failed verification keeps incident open
blocked verification remains blocked
```

---

## 13. ERA-DF-01 — DataForge Local persistence

Deliverables:

```text
local_era_run
local_era_finding
local_era_evidence_bundle
local_era_review_artifact
local_era_operator_decision
```

Acceptance:

```text
local artifact mode still works when DataForge Local unavailable
persistence is idempotent by run ID and artifact hash
ForgeCommand can query persisted ERA summaries
```

---

## 14. ERA-FC-01 — ForgeCommand review surface

Deliverables:

```text
ERA run list
ERA finding detail
artifact links
operator decisions
Centipede projection status
post-patch verification status
```

Acceptance:

```text
ForgeCommand does not claim ERA findings are fixes
operator can review evidence before action
patch candidate creation is separate from finding review
```

---

## 15. ERA-AAR-01 — AAR feedback loop

Deliverables:

```text
AARLessonArtifact.v1
AAREvalCandidate.v1
AARControlCandidate.v1
accepted lesson promotion flow
```

Acceptance:

```text
AAR proposes controls, tests, and evals
operator approval required for promotion
AAR does not train or mutate anything directly
```

---

## 16. Recommended build order

```text
01. Create ERA repo skeleton.
02. Implement ERA-01A local accuracy CLI.
03. Add evidence hashing and validation.
04. Add changed-files/RTS metadata.
05. Export Centipede bundle.
06. Import bundle into ForgeCommand Centipede ledger.
07. Add self-healing projection rules.
08. Prove Self-Healing incident intake.
09. Add redundancy lane.
10. Add efficiency lane.
11. Persist to DataForge Local.
12. Add ForgeCommand review surface.
13. Add SMITH patch-candidate handoff.
14. Add post-patch ERA verification.
15. Add AAR feedback.
```
