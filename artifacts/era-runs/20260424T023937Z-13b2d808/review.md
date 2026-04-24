# ERA Accuracy Review

Run ID: `20260424T023937Z-13b2d808`
Target Repo: `/home/charlie/Forge/ecosystem/Forge_Command`
Commit SHA: `46c156d213bf2ada5d7979bf6286794dc6d487cc`
Branch: `main`
Working Tree Dirty Status: `True`
Started / Completed: `2026-04-24T02:39:37Z` / `2026-04-24T02:40:48Z`
Overall Status: `completed`

## Delta / RTS Summary
- baseline: `n/a`
- changed files: `0`
- selected tests: `none`
- full gates run or not: `True`
- selection method: `full_retest_all`
- confidence classification: `full_retest_all`
- fallback reason: `n/a`

## Tool Availability
| tool | status | version | note |
|---|---|---|---|
| git | available | git version 2.43.0 | n/a |
| python | available | Python 3.12.3 | n/a |
| cargo | available | cargo 1.93.0 (083ac5135 2025-12-15) | n/a |
| bun | available | 1.3.5 | n/a |

## Command Summary
| label | status | exit code | duration ms | stdout | stderr |
|---|---|---:|---:|---|---|
| cargo check | failed | 101 | 26757 | /home/charlie/Forge/ecosystem/ERA/artifacts/era-runs/20260424T023937Z-13b2d808/evidence/accuracy/commands/cargo_check.stdout.txt | /home/charlie/Forge/ecosystem/ERA/artifacts/era-runs/20260424T023937Z-13b2d808/evidence/accuracy/commands/cargo_check.stderr.txt |
| cargo test | failed | 101 | 33628 | /home/charlie/Forge/ecosystem/ERA/artifacts/era-runs/20260424T023937Z-13b2d808/evidence/accuracy/commands/cargo_test.stdout.txt | /home/charlie/Forge/ecosystem/ERA/artifacts/era-runs/20260424T023937Z-13b2d808/evidence/accuracy/commands/cargo_test.stderr.txt |
| bun test | failed | 1 | 1110 | /home/charlie/Forge/ecosystem/ERA/artifacts/era-runs/20260424T023937Z-13b2d808/evidence/accuracy/commands/bun_test.stdout.txt | /home/charlie/Forge/ecosystem/ERA/artifacts/era-runs/20260424T023937Z-13b2d808/evidence/accuracy/commands/bun_test.stderr.txt |
| bun run build | passed | 0 | 9721 | /home/charlie/Forge/ecosystem/ERA/artifacts/era-runs/20260424T023937Z-13b2d808/evidence/accuracy/commands/bun_build.stdout.txt | /home/charlie/Forge/ecosystem/ERA/artifacts/era-runs/20260424T023937Z-13b2d808/evidence/accuracy/commands/bun_build.stderr.txt |

## Accuracy Classification
inaccurate

## Failed Commands
- `cargo check` status=`failed` exit_code=`101` stdout=`/home/charlie/Forge/ecosystem/ERA/artifacts/era-runs/20260424T023937Z-13b2d808/evidence/accuracy/commands/cargo_check.stdout.txt` stderr=`/home/charlie/Forge/ecosystem/ERA/artifacts/era-runs/20260424T023937Z-13b2d808/evidence/accuracy/commands/cargo_check.stderr.txt`
- `cargo test` status=`failed` exit_code=`101` stdout=`/home/charlie/Forge/ecosystem/ERA/artifacts/era-runs/20260424T023937Z-13b2d808/evidence/accuracy/commands/cargo_test.stdout.txt` stderr=`/home/charlie/Forge/ecosystem/ERA/artifacts/era-runs/20260424T023937Z-13b2d808/evidence/accuracy/commands/cargo_test.stderr.txt`
- `bun test` status=`failed` exit_code=`1` stdout=`/home/charlie/Forge/ecosystem/ERA/artifacts/era-runs/20260424T023937Z-13b2d808/evidence/accuracy/commands/bun_test.stdout.txt` stderr=`/home/charlie/Forge/ecosystem/ERA/artifacts/era-runs/20260424T023937Z-13b2d808/evidence/accuracy/commands/bun_test.stderr.txt`

## Skipped / Blocked Commands
- none

## Read-Only Invariant
- status: `preexisting_dirty_tree`
- before: `M src-tauri/src/models/self_healing.rs
 M src-tauri/src/self_healing/centipede_evidence.rs
 M src/lib/types/selfHealing.ts`
- after: `M src-tauri/src/models/self_healing.rs
 M src-tauri/src/self_healing/centipede_evidence.rs
 M src/lib/types/selfHealing.ts`
- notes: `The target repository was already dirty before the run and remained unchanged.`

## Operator Notes
- No automatic action was taken.
- ERA is read-only.
