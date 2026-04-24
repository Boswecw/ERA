# Implementation Prompt — ERA-01A Local Read-Only Accuracy Proof

**Date:** 2026-04-23  
**Time:** EDT  
**Owner:** BDS / Charlie  
**System posture:** Internal business systems control surface  

---

Use this prompt with Opus/Codex/manual implementation when ready.

```text
You are acting as a senior repository architect and implementation engineer for the Forge ecosystem.

Task:
Build ERA-01A — Local Read-Only Accuracy Proof.

Context:
ERA means Evidence Review & Assurance. It is a bounded read-only internal-control subsystem for evaluating code accuracy, redundancy, and efficiency. This slice only implements the local accuracy proof. ERA must not mutate the target repository.

Target ERA repo:
~/Forge/ecosystem/ERA

Evaluation target repo:
~/Forge/ecosystem/Forge_Command

Implement:
1. ERA repo skeleton if missing.
2. Python CLI entry point with:
   - python -m era_cli run
   - python -m era_cli report
   - python -m era_cli validate
3. Target manifest capture.
4. Git metadata capture.
5. Pre-run and post-run git snapshots.
6. Tool availability checks for git, python, cargo when Cargo.toml exists, and bun when package.json exists.
7. Accuracy command selection for:
   - cargo check --manifest-path src-tauri/Cargo.toml
   - cargo test --manifest-path src-tauri/Cargo.toml
   - bun test when package.json has test script
   - bun run build when package.json has build script
8. Command runner with stdout/stderr capture.
9. SHA-256 hashing for raw stdout/stderr.
10. ToolRawArtifact.v1 local JSON.
11. ToolNormalizedResult.v1 local JSON.
12. LaneFindingDraft.v1 local JSON where findings are generated.
13. ERAFinding.v1 local JSON where findings are promoted.
14. TestEvidenceBundle.v1 local JSON.
15. TestSelectionArtifact.v1 for changed-files mode.
16. Markdown review artifact writer.
17. Artifact validation command.
18. Report latest command.
19. Unit tests for artifact generation and validation.
20. Optional local Centipede export stub that writes centipede_bundle.json but does not require ForgeCommand import yet.

Required CLI:
python -m era_cli run --repo ~/Forge/ecosystem/Forge_Command --lanes accuracy --mode full
python -m era_cli run --repo ~/Forge/ecosystem/Forge_Command --lanes accuracy --mode changed-files --baseline main
python -m era_cli report --latest
python -m era_cli validate --latest

Required artifacts:
- run.json
- target_manifest.json
- tool_availability.json
- test_selection_artifact.json when changed-files mode is used
- evidence/accuracy/test_evidence_bundle.json
- evidence/accuracy/commands/*.stdout.txt
- evidence/accuracy/commands/*.stderr.txt
- findings.json
- review.md
- hashes.json

Rules:
- Do not modify the evaluation target repo.
- Do not apply patches.
- Do not install packages.
- Do not run formatters in write mode.
- Do not run fix commands.
- Do not stage, commit, checkout, reset, stash, or clean.
- Do not hide failed, skipped, or blocked commands.
- Mark missing evidence as missing, skipped, blocked, or unproven.
- Mark missing tools as blocked_by_missing_tool.
- Store artifacts under ERA/artifacts/era-runs/<run_id>/.
- Keep contracts local for this slice; forge-contract-core integration comes later.
- No tool parser may write ERAFinding.v1 directly.
- No selected-test run without TestSelectionArtifact.v1.
- If changed-files mode cannot safely select tests, fall back to full accuracy gates and record fallback reason.

Acceptance:
- `python -m era_cli run --repo ~/Forge/ecosystem/Forge_Command --lanes accuracy --mode full` creates a complete run artifact.
- `python -m era_cli run --repo ~/Forge/ecosystem/Forge_Command --lanes accuracy --mode changed-files --baseline main` creates TestSelectionArtifact.v1 and either selected-test evidence or full-run fallback evidence.
- `python -m era_cli report --latest` prints the latest review summary.
- `python -m era_cli validate --latest` validates required artifacts and hash references.
- No source files are changed inside Forge_Command.
- Pre-run and post-run git snapshots are captured.
- Read-only invariant status is recorded.
- Failed target tests are recorded as evidence, not ERA crashes.
- Missing tools are recorded as blocked gates, not false code failures.
- Review markdown includes Delta / RTS Summary, Tool Availability, Command Summary, Accuracy Classification, Failed Commands, Skipped / Blocked Commands, Read-Only Invariant, and Operator Notes.
```
