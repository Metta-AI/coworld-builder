# Phase 40 — Release report — 2026-09-08-battlecode-2023

Repo: `Metta-AI/cogame-battlecode` (MOD run: bc23 year module merged into the existing
battlecode coworld repo). Branch `main` @ `47f360011e0b46fe6ede8e8f71a702a63fe84c74`
(CI green, run 34244272097).

Version pin: **0.6.0** (previous release 0.5.0 from the sibling bc25 run,
`cow_id cow_e58e703d-3d34-4d27-b8eb-4464a6209170`). Retries bump 0.6.1, 0.6.2.

## Preflight

- `gh secret list -R Metta-AI/cogame-battlecode` → `ANTHROPIC_API_KEY` and `SOFTMAX_TOKEN`
  both present (set 2026-09-03T20:14:29Z). No `propagate-secrets.yml` dispatch needed.
- `tools/ci/policies.json` on `main` has 24 entries; the four bc23 ones are
  `battlecode-bc23-duel` (PLAYER_PROMPT, no `player`),
  `battlecode-bc23-alchemist` (PLAYER_PROMPT, `player: ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`),
  `battlecode-lemonade` (PLAYER_SCRIPTED=lemonade),
  `battlecode-examplefuncsplayer23` (PLAYER_SCRIPTED=examplefuncsplayer23).
  No `policies` dispatch override will be passed.
- Manifest preflight: all six variants (`bc26 bc20 bc21 bc24 bc25 bc23`) set
  `num_agents: 2`; `certification.game_config.num_agents: 2`;
  `game.replay_viewer.bundle: "static-replay-viewer"` (static bundle declared, so
  replay-liveness must report skipped).
- `.github/workflows/coworld-release.yml` step order verified: build manifest → certify →
  upload policies → upload coworld → **wait for canonical** → put secret → assemble
  release-result. No reordering needed.

## Dispatches

### Dispatch 1 — version 0.6.0 — run 34252334397 — SUCCESS (first attempt, no retries used)

- Dispatched `gh workflow run coworld-release.yml -R Metta-AI/cogame-battlecode --ref main
  -f version=0.6.0 -f put_secret=true` at `2026-09-08T16:38:51Z`; no `policies` override,
  no `skip_certify`. Run found with the dispatch-then-watch recipe (createdAt
  `2026-09-08T16:38:53Z` > dispatched_at), not `-L 1`.
- Run: <https://github.com/Metta-AI/cogame-battlecode/actions/runs/34252334397> —
  job `release` completed **success** in 7m30s. `step_failed: null`, `errors: []`.
- Decision: **accept**. `release-result.json` satisfies every exit-criterion clause (below).
  No bump, no manifest fix, no workflow-order fix needed. 2 of 3 dispatches unused.

## Exit criterion — read from release-result.json (not the run colour)

| clause | value | verdict |
|---|---|---|
| `ok` | `true` | pass |
| `canonical` | `true` | pass |
| `certify` non-null, `certify.ok` | `true` | pass |
| `certify.replay_liveness` | `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)` | pass |
| `policies[]` count | 24 requested / 24 returned, all labels distinct | pass |
| champion #2 `battlecode-bc23-alchemist` `player_id` | `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d` | pass |
| `secret_put` | `true` | pass |
| `policy_version_id` | `null` for all 24 | expected (phase 50 resolves UUIDs) |
| `hosted_smoke` / `hosted_certification` | `passed` / `certifying` at assemble time | pass |

## Release facts

| field | value |
|---|---|
| release run id | `34252334397` |
| release run URL | <https://github.com/Metta-AI/cogame-battlecode/actions/runs/34252334397> |
| coworld version | `0.6.0` |
| `cow_id` | `cow_93baa4e4-ec4b-40c7-9f0f-694c97c5dfe7` |
| manifest sha | `sha256:a4ae44ab88615b434ccef7b6d6edc82bb8cdc6aec397d9f3efcaa89c70ef133e` |
| repo / branch / commit | `Metta-AI/cogame-battlecode` / `main` / `47f360011e0b46fe6ede8e8f71a702a63fe84c74` |

### The four bc23 policy labels

| role | label | owner (`player_id`) |
|---|---|---|
| champion #1 (LLM prompt) | `battlecode-bc23-duel:v1` | `null` (daveey, the CI token's own player) |
| champion #2 (LLM prompt) | `battlecode-bc23-alchemist:v1` | `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d` (daveey-1) |
| filler (scripted `lemonade`) | `battlecode-lemonade:v1` | `null` |
| filler (scripted `examplefuncsplayer23`) | `battlecode-examplefuncsplayer23:v1` | `null` |

All four are `v1` — first upload of these four names. The other 20 entries (bc26/bc20/bc21/bc24/bc25
year modules, re-uploaded from the same `policies.json`) landed at v4/v4/v3/v2/v2 respectively;
each year's four labels are internally distinct, so no dedupe collapsed a champion into a filler.

### Post-release confirmation from the sandbox CLI

`coworld status cow_93baa4e4-ec4b-40c7-9f0f-694c97c5dfe7 --json` (via
`uvx --from 'coworld[auth]==0.1.43'`) reports:

- `coworld`: name `battlecode`, version `0.6.0`, `canonical: true`,
  `manifest_hash sha256:a4ae44ab8861…ef133e` (matches the result file), size 30508 bytes.
- `certification`: `state: "certified"`, `certified: true`, `failed_step: null`,
  `failure: null`, contract `main-6cb6ef84cdf9`, completed `2026-09-08T16:45:49Z`.
  All ten checks pass: source-resolves, images-reachable, fixture-conforms, smoke-episode,
  results-conform, replay-present, replay-loadable, players-run, supporting-roles
  (+ manifest validation).
- 5 hosted smoke episodes recorded.

So the hosted certification that was still `certifying` when the workflow assembled the result
has since settled to `certified`.

### Note on `cow_id` — a new id, and that is normal for this repo

The brief expected the sibling bc25 release's `cow_id`
(`cow_e58e703d-3d34-4d27-b8eb-4464a6209170`) to come back. It did not; 0.6.0 minted
`cow_93baa4e4-ec4b-40c7-9f0f-694c97c5dfe7`. This is **not** a defect: the platform mints a
fresh coworld id per uploaded version of the same `game.name`, and every prior release from
this same repo did the same thing —

| run | version | cow_id |
|---|---|---|
| 2026-09-03-battlecode | 0.1.5 | `cow_6f3468fa-5cf5-4c4b-95cf-1d87dc41bfa2` |
| 2026-09-04-battlecode-2020-soup | 0.2.0 | `cow_d9fc2f21-c095-4131-bd86-d35848e046f8` |
| 2026-09-04-battlecode-2021 | 0.3.0 | `cow_455dff0d-7f57-4b21-a28d-6603d9c458d0` |
| 2026-09-07-battlecode-2025 | 0.5.0 | `cow_e58e703d-3d34-4d27-b8eb-4464a6209170` |
| **2026-09-08-battlecode-2023** | **0.6.0** | **`cow_93baa4e4-ec4b-40c7-9f0f-694c97c5dfe7`** |

The name `battlecode` is stable and 0.6.0 is the canonical version, so phase 50 should seat the
league on `cow_93baa4e4-ec4b-40c7-9f0f-694c97c5dfe7`.

## Files written by this phase

- `runs/2026-09-08-battlecode-2023/release-result.json` — the release-result artifact of run
  34252334397, copied from `/tmp/rr` (added).
- `runs/2026-09-08-battlecode-2023/release-report.md` — this file (added).

No files were changed in `Metta-AI/cogame-battlecode`: the release needed no fix, so `main`
is still at `47f360011e0b46fe6ede8e8f71a702a63fe84c74`.

STATE.json was left to the coordinator (single-writer). Values it needs:
`coworld.version=0.6.0`, `coworld.cow_id=cow_93baa4e4-ec4b-40c7-9f0f-694c97c5dfe7`,
`coworld.manifest_sha=sha256:a4ae44ab88615b434ccef7b6d6edc82bb8cdc6aec397d9f3efcaa89c70ef133e`,
`coworld.release_run_id=34252334397`, `policies.champion1=battlecode-bc23-duel:v1`,
`policies.champion2=battlecode-bc23-alchemist:v1`,
`policies.fillers=["battlecode-lemonade:v1","battlecode-examplefuncsplayer23:v1"]`,
`phase_attempts["40"]=1`.
