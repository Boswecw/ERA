# ERA Executive Charter

**Date:** 2026-04-23  
**Time:** EDT  
**Owner:** BDS / Charlie  
**System posture:** Internal business systems control surface  

---

## 1. Executive ruling

Build **ERA — Evidence Review & Assurance** as a bounded internal subsystem for evaluating code accuracy, redundancy, and efficiency across Forge/BDS repositories.

ERA is not an MVP. ERA is not a public SaaS feature. ERA is not an autonomous fixer.

ERA is an **internal assurance subsystem**.

```text
ERA finds.
ERA measures.
ERA proves.
ERA reports.
ERA does not fix.
```

---

## 2. Primary purpose

ERA exists to answer three evidence-backed questions:

| Lane | Question |
|---|---|
| Accuracy | Does the code do the correct thing according to tests, contracts, state rules, and intended behavior? |
| Redundancy | Is there harmful duplication, dead code, unused dependency weight, duplicated contracts, or overlapping authority? |
| Efficiency | Is the code wasting time, memory, I/O, database cost, model calls, build time, or operator time? |

ERA must turn these answers into reproducible artifacts, not loose model opinions.

---

## 3. Internal business system posture

ERA must be described as:

```text
internal business system
internal-control proof
assurance subsystem
governed evidence pipeline
operator-review control surface
```

ERA must not be described as:

```text
MVP
public SaaS feature
autonomous repair product
agentic fixer
self-modifying code assistant
```

---

## 4. What ERA owns

ERA owns:

```text
repo evaluation manifests
tool availability diagnostics
accuracy evidence normalization
redundancy evidence normalization
efficiency evidence normalization
test-selection metadata
finding classification
risk scoring
evidence hash chain
review artifact generation
local run artifacts
Centipede bundle export
post-patch verification evidence
```

---

## 5. What ERA does not own

ERA does not own:

```text
canonical schema authority
operator approval
code mutation
patch application
agent orchestration
service authority
repo source of truth
long-term memory authority
final architectural truth
```

Canonical contract authority should remain in `forge-contract-core`.

Durable evidence storage should be in DataForge Local after local JSON proof is stable.

Mutation authority remains with SMITH / forge-smithy.

Operator decision surface remains ForgeCommand.

---

## 6. Required boundary behavior

ERA must enforce its boundary in code, documentation, and artifacts.

Required surfaces:

```text
README.md
AGENTS.md
docs/system/00-era-charter.md
CLI help output
review.md footer
Centipede export metadata
Self-Healing projection notes
SMITH handoff documentation
```

Required invariant text:

```text
ERA is read-only by default.
ERA does not apply patches.
ERA does not delete files.
ERA does not weaken tests.
ERA does not consolidate contracts.
ERA does not approve its own findings.
ERA does not close Self-Healing incidents.
```

---

## 7. First internal-control proof

The first build slice is:

```text
ERA-01A — Local Read-Only Accuracy Proof
```

Scope:

```text
Target ERA repo: ~/Forge/ecosystem/ERA
Evaluation target repo: ~/Forge/ecosystem/Forge_Command
Lane: accuracy only
Mutation: disabled
Persistence: local JSON/Markdown artifacts only
Centipede export: planned, not required for first CLI proof
DataForge Local: not required in first proof
ForgeCommand UI: not required in first proof
```

---

## 8. Final charter rule

```text
ERA may inspect.
ERA may run tests.
ERA may run scans.
ERA may benchmark.
ERA may classify findings.
ERA may recommend review.
ERA may export evidence to Centipede.
ERA may request governed patch-candidate creation through downstream systems.

ERA may not mutate code.
ERA may not approve remediation.
ERA may not suppress findings without operator decision.
ERA may not replace Centipede, DataForge, ForgeCommand, SMITH, or forge-contract-core.
```
