# Phase 40 — Release report (run 2026-09-07-battlecode-2025)

Repo: `Metta-AI/cogame-battlecode` · branch `main` @ `6885a0625687c7caec19b879e0ea09613ebd74f0`

**Status: DONE — released on the first dispatch.**

| field | value |
|---|---|
| coworld version | **0.5.0** |
| release run id | **34189611273** (`coworld-release.yml`, conclusion **success**) |
| run URL | https://github.com/Metta-AI/cogame-battlecode/actions/runs/34189611273 |
| `cow_id` | `cow_e58e703d-3d34-4d27-b8eb-4464a6209170` |
| `manifest_sha` | `sha256:28e952e1db3f2d7c479160ac522a91f420b0dd2c5fdf2b83d44ade8d7bdce7fe` |

## Exit criterion — checked against the artifact, not the workflow colour

`release-result` artifact downloaded from run 34189611273 and copied to
`runs/2026-09-07-battlecode-2025/release-result.json`.

| requirement | observed | ✓ |
|---|---|---|
| `ok` | `true` | ✓ |
| `canonical` | `true` (workflow's "Wait for the uploaded version to become canonical" + "Enforce canonical" both passed: `Coworld is canonical.`) | ✓ |
| `certify.ok` | `true` | ✓ |
| `certify.replay_liveness` | `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)` | ✓ |
| `policies[]` | 20 entries, one per `tools/ci/policies.json` entry, **20 distinct `name:vN` labels** | ✓ |
| champion #2 ownership | every `"player"`-field entry (incl. `battlecode-bc25-siege`) reports `player_id = ply_bac48eb1-662e-44f8-973d-f3e016dccf5d` | ✓ |
| `secret_put` | `true` | ✓ |
| `step_failed` / `errors` | `null` / `[]` | ✓ |
| `hosted_smoke` | `passed` | ✓ |

`policy_version_id` is `null` on all 20 entries — normal (`upload-policy` prints no uuid); phase 50
resolves UUIDs from `GET /policy-versions` with a client-side filter.

## bc25 policy labels (for phase 50)

| role | label | owner |
|---|---|---|
| champion #1 (LLM) | `battlecode-bc25-coverage:v1` | daveey (`player_id` null) |
| champion #2 (LLM) | `battlecode-bc25-siege:v1` | daveey-1 (`ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`) |
| filler (scripted) | `battlecode-spaark:v1` | daveey |
| filler (scripted) | `battlecode-examplefuncsplayer25:v1` | daveey |

All other 16 labels cut by this release (do **not** reuse remembered labels for the sibling
leagues — these are the current ones):
`battlecode-loyalist:v3`, `battlecode-opportunist:v3`, `battlecode-awu:v3`, `battlecode-scaffold:v3`,
`battlecode-bc20-latticer:v3`, `battlecode-bc20-rusher:v3`, `battlecode-bowl-of-chowder:v3`,
`battlecode-examplefuncsplayer:v3`, `battlecode-bc21-turtle:v2`, `battlecode-bc21-muckrush:v2`,
`battlecode-california-roll:v2`, `battlecode-examplefuncsplayer21:v2`, `battlecode-bc24-fortress:v1`,
`battlecode-bc24-flagrush:v1`, `battlecode-gone-sharkin:v1`, `battlecode-examplefuncsplayer24:v1`.

## Dispatch history

| # | version | run id | step_failed | decision |
|---|---|---|---|---|
| 1 | 0.5.0 | 34189611273 | `null` (success) | accepted — all exit-criterion fields satisfied; no retry needed (2 of 3 dispatches unused) |

Dispatch command: `gh workflow run coworld-release.yml -R Metta-AI/cogame-battlecode --ref main
-f version=0.5.0 -f put_secret=true`. `skip_certify` never passed. Run located with the
dispatch-then-watch recipe (`dispatched_at=2026-09-08T05:10:15Z`), not `-L 1`.

## Commits landed

None. No fixes were needed; `main` is unchanged at `6885a0625687c7caec19b879e0ea09613ebd74f0`.

## Deviation from the design note (deliberate, per the coordinator brief)

The design note §"Release dispatch shape, decided" preferred a `policies` **override** limited to the
four bc25 entries, so the four existing leagues' seated policies would not be recut. The coordinator
brief directed the file-authoritative shape (no override), which the same design paragraph explicitly
allows ("Either shape works"). Consequence, already flagged there: all 20 policies were recut, so the
bc26/bc20/bc21 sets moved to `v3`/`v3`/`v2` and bc24 stayed at `v1`. **Phase 50 must take every label
from this release's `release-result.json`** (reproduced above) and never from remembered ones. The
already-seated league members are unaffected until someone submits the new versions.

## Files written

- `runs/2026-09-07-battlecode-2025/release-result.json` (artifact from run 34189611273)
- `runs/2026-09-07-battlecode-2025/release-report.md` (this file)
