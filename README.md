# ERA

Evidence Review & Assurance is a bounded internal-control subsystem for the Forge ecosystem.

Current slice:

```text
ERA-01A — Local Read-Only Accuracy Proof
ERA-01B — Redundancy Scan Proof
ERA-01C — Efficiency Workload Proof
ERA-02  — Unified Finding Normalization
ERA-03  — Evidence Hash Chain
ERA-04  — Differential / RTS Scaffolding
```

Core doctrine:

```text
ERA finds.
ERA measures.
ERA proves.
ERA reports.
ERA does not fix.
```

## Usage

Run from the `ERA/` directory:

```bash
python -m era_cli run --repo /home/charlie/Forge/ecosystem/Forge_Command --lanes accuracy --mode full
python -m era_cli run --repo /home/charlie/Forge/ecosystem/Forge_Command --lanes accuracy --mode changed-files --baseline main
python -m era_cli run --repo /home/charlie/Forge/ecosystem/Forge_Command --lanes redundancy --mode full
python -m era_cli run --repo /home/charlie/Forge/ecosystem/Forge_Command --lanes efficiency --mode full
python -m era_cli run --repo /home/charlie/Forge/ecosystem/Forge_Command --lanes accuracy,redundancy --mode full
python -m era_cli run --repo /home/charlie/Forge/ecosystem/Forge_Command --lanes accuracy,redundancy,efficiency --mode full
python -m era_cli report --latest
python -m era_cli validate --latest
```

Artifacts are written under:

```text
ERA/artifacts/era-runs/<run_id>/
```

ERA never writes inside the evaluated target repository.

## Redundancy Exceptions

Optional operator-approved redundancy exceptions live at:

```text
ERA/config/intentional_redundancy_exceptions.json
```

Each entry should use the local `IntentionalRedundancyException.v1` shape and is treated as review context, not as a parser instruction to delete evidence.

## Efficiency Workloads

Efficiency workloads are declared in:

```text
ERA/config/workload_manifests/<repo_name>.json
```

ERA-01C only makes efficiency regression or improvement claims when:

```text
a workload manifest exists
the workload ran successfully
timing variance is not unstable
a baseline efficiency artifact exists
```

## Unified Finding Model

ERA-02 standardizes the internal evidence chain as:

```text
ToolRawArtifact.v1
ToolNormalizedResult.v1
LaneFindingDraft.v1
ERAFinding.v1
ERAScore.v1
```

Tool parsers only emit `ToolNormalizedResult.v1`. Promotion into lane drafts, final findings, and scores happens in the shared contract layer so risk, confidence, raw evidence references, and lane-specific details stay aligned across all lanes.

## Evidence Hash Chain

ERA-03 writes `hashes.json` with both file hashes and a structural `ERAEvidenceHashChain.v1` section:

```text
raw artifacts
normalized results
lane finding drafts
ERA findings
ERA scores
review artifact
```

`validate --latest` recomputes file hashes, embedded object hashes, review hash references, and finding-to-raw-evidence references.

## Differential / RTS Scaffolding

Changed-files accuracy runs emit `TestSelectionArtifact.v1` with:

```text
baseline and current commit
changed files and file classifications
candidate and selected tests
RTS level cap
selection safety class
full-gate fallback rationale
```

ERA-04 records Level 1 changed-file metadata and an advisory Level 2 path for directly changed test files. It still falls back to full configured accuracy gates unless a future targeted runner can prove a safer selective execution path.
