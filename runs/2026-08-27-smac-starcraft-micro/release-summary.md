# Phase 40 — release summary (cogame-smac-starcraft-micro)

**Accepted release: version `0.1.2`.**

| field | value |
|---|---|
| version | `0.1.2` |
| `cow_id` | `cow_476a8db4-f5df-4d93-b0c2-1c302ba201bc` |
| `manifest_sha` | `sha256:4575435fea3737665c72aa4ed75fc6621b6d5407b82234eb8359d66c75df8c38` |
| release run id | `33060960111` (conclusion: success) |
| release run url | https://github.com/Metta-AI/cogame-smac-starcraft-micro/actions/runs/33060960111 |
| head sha of the run | `bb0323da3cbe12a21cfd92bf280b170a7f545d12` |
| `ok` / `canonical` | `true` / `true` (`upload-coworld` itself printed `Canonical: yes`) |
| `hosted_smoke` / `hosted_certification` | `passed` / `certified` |
| `certify.ok` | `true` |
| `certify.replay_liveness` | `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)` |
| `secret_put` | `true` (`secret://coworld/smac-starcraft-micro/anthropic_api_key`) |

## Policy versions (all four distinct, `policy_version_id` null is normal)

| label | role | owner (`player_id`) |
|---|---|---|
| `smac-starcraft-micro-marshal:v3` | champion #1, `PLAYER_PROMPT` | daveey (`null`) |
| `smac-starcraft-micro-skirmish:v3` | champion #2, `PLAYER_PROMPT` | daveey-1 (`ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`) |
| `smac-starcraft-micro-focusfire:v3` | filler, `PLAYER_SCRIPTED=focusfire` | daveey (`null`) |
| `smac-starcraft-micro-charge:v3` | filler, `PLAYER_SCRIPTED=charge` | daveey (`null`) |

Versions are `v3` because each of the three dispatches uploaded the four policies
(v1 on 0.1.0, v2 on 0.1.1, v3 on 0.1.2). Filler versions differ from champion versions only
by name; the four labels are distinct, which is what phase 50 resolves against.

## Dispatch log

| # | version | run | outcome | triage / change made |
|---|---|---|---|---|
| 1 | 0.1.0 | [33058450245](https://github.com/Metta-AI/cogame-smac-starcraft-micro/actions/runs/33058450245) | `step_failed: "Upload the Coworld"` — hosted smoke failed 1 of 5 episodes: `player_error` "player slot 4 never joined the lobby within 1440 lobby ticks (~60s)" | Real bug, not a race to retry: `fastMode` skips the frame limiter whenever every *connected* seat has sent the Sprite v1 Ready packet, so as soon as the first player pod joined the lobby ran flat out and the 1440-tick join grace expired in seconds instead of 60 s. Fixed in `src/smac/server.nim`: the limiter paces at wall clock while the lobby is short of `minPlayers`. |
| 2 | 0.1.1 | [33060010957](https://github.com/Metta-AI/cogame-smac-starcraft-micro/actions/runs/33060010957) | hosted smoke **passed** (5/5 — the lobby fix worked); failed `Enforce canonical` with `canonical: false`, `hosted_certification: "certifying"` | Documented completion race. `coworld status` on that same `cow_id` said `Canonical: yes` (the platform's certification `completed_at` was seconds after the upload's read). Bumped the version **and** added a bounded post-upload re-read of `coworld status` to `coworld-release.yml` so the race cannot cost a dispatch. |
| 3 | 0.1.2 | [33060960111](https://github.com/Metta-AI/cogame-smac-starcraft-micro/actions/runs/33060960111) | **success**, exit criterion met | — |

On 0.1.2 the new re-read step was a no-op (`canonical=yes - nothing to re-read`): `upload-coworld`
reported `Canonical: yes` on its own, so the accepted `canonical: true` comes from the upload's own
output.

## Commits pushed to `main` during this phase (Git Data API route, no force-push)

| sha | what |
|---|---|
| `97b4c7bd4dcb2a4068e8ae9cab00365e42b90c9f` | `fix(server): wall-pace the lobby join budget so a slow player pod is not a no-show` — `src/smac/server.nim` |
| `bb0323da3cbe12a21cfd92bf280b170a7f545d12` | `ci(release): re-read canonical from the platform after upload-coworld` — `.github/workflows/coworld-release.yml` |

`ci.yml` is green on both (runs `33059575925` and `33060952804`, all three jobs: test, docker-smoke,
wasm-viewer).

## Template delta to fold back into `coworld-builder/templates/coworld-release.yml`

A `Confirm the Coworld is canonical` step after `Put the Coworld secret` (i.e. after
`upload-coworld`, leaving the load-bearing order untouched) that, when the upload printed
`Canonical: no`, polls `coworld status <cow_id>` for up to 600 s at 20 s intervals and refreshes
`upload.json`'s `canonical` / `hosted_certification` (recording `canonical_source`) before
`release-result.json` is assembled. It only reads platform state; it cannot manufacture a `yes`.
