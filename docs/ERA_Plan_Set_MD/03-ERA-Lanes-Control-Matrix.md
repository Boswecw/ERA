# ERA Lanes and Control Matrix

**Date:** 2026-04-23  
**Time:** EDT  
**Owner:** BDS / Charlie  
**System posture:** Internal business systems control surface  

---

## 1. Lane overview

ERA has three primary lanes:

```text
ERA-A = Accuracy
ERA-R = Redundancy
ERA-E = Efficiency
```

Each lane emits evidence into a common review model, but no lane parser writes `ERAFinding.v1` directly.

Required normalization chain:

```text
raw tool output
  -> ToolRawArtifact.v1
  -> ToolNormalizedResult.v1
  -> LaneFindingDraft.v1
  -> ERAFinding.v1
  -> ERAReviewArtifact.v1
```

---

## 2. Accuracy lane

### Purpose

Determine whether code behavior is supported by evidence.

### Checks

```text
parse / compile
typecheck
unit tests
integration tests
contract tests
schema validation
migration checks
regression checks
snapshot/golden checks
property tests later
mutation score later
post-patch verification
```

### First target commands

For `Forge_Command`:

```bash
cargo check --manifest-path src-tauri/Cargo.toml
cargo test --manifest-path src-tauri/Cargo.toml
bun test
bun run build
```

Commands must be auto-detected and skipped honestly when unavailable.

### Accuracy classifications

```text
accurate_enough_for_review
accurate_with_degradation
inaccurate
unproven
blocked_by_missing_evidence
blocked_by_missing_tool
```

---

## 3. Redundancy lane

### Purpose

Find potentially harmful duplication, dead code, unused dependencies, duplicated contracts, and authority overlap.

### Checks

```text
duplicate code
near-miss clones
dead code candidates
unused exports
unused dependencies
duplicated contracts
authority overlap
intentional duplication exceptions
```

### Candidate tools

```text
jscpd
knip
cargo tree --duplicates
cargo machete
cargo udeps later if acceptable
custom import graph checks
```

### Required safety posture

Redundancy findings are review candidates, not defects.

Allowed classifications:

```text
harmful_redundancy_candidate
intentional_redundancy_candidate
generated_or_fixture_duplication
boundary_preserving_duplication
needs_operator_review
ignored_with_reason
```

No automatic deletion.

---

## 4. Efficiency lane

### Purpose

Determine whether code wastes runtime, build time, memory, I/O, query cost, model calls, or operator time.

### Checks

```text
runtime benchmark
build time
test time
memory usage
I/O usage
database query cost
model call cost
operator time burden
benchmark stability
baseline regression
```

### Candidate tools

```text
hyperfine
criterion
pytest-benchmark
perf
flamegraph
custom workload manifests
```

### Required rule

```text
No efficiency claim without a workload.
No improvement or regression claim without a baseline.
No unstable benchmark treated as proof.
```

---

## 5. Cross-cutting controls

| Control | Applies to | Required behavior |
|---|---|---|
| Read-only invariant | All lanes | Capture before/after target repo state |
| Tool availability | All lanes | Missing tools create blocked gates, not false failures |
| Evidence hashing | All lanes | Raw evidence hash chain required |
| Operator review | All lanes | Findings do not become fixes |
| Exception expiry | Redundancy primarily | Intentional exceptions expire or review later |
| RTS metadata | Accuracy | Selected tests require `TestSelectionArtifact.v1` |
| Attestation readiness | All lanes | Artifacts structured for later signing |
| Supply-chain posture | All lanes | Security/supply-chain metadata may attach to lane outputs |
| Reviewer-of-reviewer | All lanes | ERA must explain why it selected/skipped checks |

---

## 6. Evidence strength scale

| Strength | Meaning | Example |
|---|---|---|
| exact | Direct mechanical evidence proves condition | Test failed with deterministic compiler error |
| high | Strong repeatable evidence | Repeated benchmark regression with stable variance |
| moderate | Evidence likely but incomplete | Tool finding with affected file and line but no repro |
| low | Weak signal | Heuristic duplicate candidate |
| none | No usable evidence | Parser could not run |
| advisory_only | LLM or human interpretation without mechanical proof | Model suggests code smell |
| blocked | Evidence unavailable due to missing tool/config | `bun` missing |
| unproven | No proof either way | Gate skipped with no substitute |

---

## 7. Finding triage policy

ERA must prevent operator overload.

Required triage controls:

```text
group related findings
deduplicate repeated findings
rank by risk and confidence separately
flag new vs recurring findings
support suppress-with-reason
support intentional redundancy exception
support review-after date
support changed-files mode
support release-gate full mode
```

---

## 8. Control matrix

| Control area | Accuracy | Redundancy | Efficiency |
|---|---:|---:|---:|
| Mechanical evidence required | yes | yes | yes |
| Raw artifact hashing | yes | yes | yes |
| False-positive controls | moderate | high | high |
| Operator review required | yes | yes | yes |
| Auto-fix allowed | no | no | no |
| Centipede evidence export | yes | yes | yes |
| Self-Healing projection eligible | selected failures | selected high-confidence issues | selected baseline regressions |
| Post-patch verification required | yes | yes when patch occurs | yes when patch occurs |
| Differential mode useful | yes | yes | yes |
| Full release-gate mode required | yes | not always | baseline dependent |

---

## 9. Lane invariant

```text
A lane may produce evidence.
A lane may produce findings.
A lane may recommend review.
A lane may not approve or perform repair.
```
