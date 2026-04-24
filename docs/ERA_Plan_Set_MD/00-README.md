# ERA Plan Set — Evidence Review & Assurance

**Date:** 2026-04-23  
**Time:** EDT  
**Owner:** BDS / Charlie  
**System posture:** Internal business systems control surface  
**Package:** Markdown plan set  
**Status:** Planning baseline for implementation  

---

## Purpose

This plan set defines **ERA — Evidence Review & Assurance** as a bounded internal-control subsystem for the Forge/BDS ecosystem.

ERA evaluates code health through three primary lanes:

```text
ERA-A = Accuracy
ERA-R = Redundancy
ERA-E = Efficiency
```

ERA also carries cross-cutting controls for:

```text
read-only invariants
evidence hashing
tool normalization
test-selection metadata
Centipede projection
Self-Healing feed
post-patch verification
operator review
AAR feedback
```

---

## Core doctrine

```text
ERA finds.
ERA measures.
ERA proves.
ERA reports.
ERA does not fix.
```

ERA must not mutate code, delete files, apply patches, weaken tests, consolidate contracts, or approve its own findings.

All mutation remains downstream:

```text
ERA evidence
  -> Centipede reconciliation / projection
  -> Self-Healing incident queue
  -> ForgeCommand operator review
  -> SMITH / forge-smithy governed patch workflow
  -> ERA post-patch verification
  -> AAR / calibration
```

---

## File index

| File | Purpose |
|---|---|
| `01-ERA-Executive-Charter.md` | Defines ERA purpose, scope, doctrine, and authority boundaries |
| `02-System-Architecture-Boundaries.md` | Places ERA among Cortex, Centipede, DataForge, ForgeCommand, SMITH, and Self-Healing |
| `03-ERA-Lanes-Control-Matrix.md` | Defines Accuracy, Redundancy, Efficiency, and cross-cutting controls |
| `04-Contracts-Artifacts-and-Evidence-Model.md` | Defines artifacts, evidence chain, finding model, and Centipede mapping |
| `05-ERA-01A-Local-Read-Only-Accuracy-Proof.md` | First implementation slice for local accuracy proof |
| `06-RTS-and-Differential-ERA-Plan.md` | Differential mode, Regression Test Selection levels, and `TestSelectionArtifact.v1` |
| `07-ERA-to-Centipede-Integration-Plan.md` | How ERA exports evidence into Centipede intake bundles |
| `08-Self-Healing-Feed-and-Post-Patch-Verification.md` | How Centipede-projected ERA findings feed Self-Healing safely |
| `09-Implementation-Roadmap-and-Slices.md` | Ordered implementation slices and acceptance gates |
| `10-Operator-Controls-Risks-and-Governance.md` | Risk controls, operator burden controls, exception policy, and guardrails |
| `11-Implementation-Prompt-ERA-01A.md` | Copy/paste implementation prompt for the first build slice |

---

## Non-negotiable rules

```text
No direct repair from ERA.
No automatic deletion.
No automatic contract consolidation.
No selected-test run without TestSelectionArtifact.v1.
No Self-Healing closure without post-patch ERA verification.
No parser writes ERAFinding.v1 directly.
No LLM output may become proof without mechanical evidence.
```

---

## Recommended first action

Start with:

```text
ERA-01A — Local Read-Only Accuracy Proof
```

This creates a Python CLI that runs read-only accuracy gates against `Forge_Command`, writes local artifacts, verifies target repo invariants, and optionally exports a Centipede-compatible bundle later.
