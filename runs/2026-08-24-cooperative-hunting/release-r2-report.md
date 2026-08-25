# Release r2 — cooperative-hunting

**Outcome: GREEN at version `0.1.4`** (release run `32809315564`). Two distinct fixes were needed
this round: the certify timeout, then a Coworld-secret namespace mismatch that only the upload
step could surface.

- `cow_id`: `cow_d5e3a72d-bae0-4418-bb3e-e39f2c5cc81d`
- `manifest_sha`: `sha256:0dfeeb8e92befffa524161af55b34e914cbf7620bca58d4a0d4a2d0e98cad122`
- version: `0.1.4` · `hosted_smoke: passed` · `hosted_certification: certified`
- release run id: **`32809315564`** —
  <https://github.com/Metta-AI/cogame-cooperative-hunting/actions/runs/32809315564>
- artifact persisted at `runs/2026-08-24-cooperative-hunting/release-result.json`

## Fixes pushed this round

| sha | change | why |
|---|---|---|
| `5ac03d9081cf8584bbf8f987c07d15efcc775edd` | `.github/workflows/coworld-release.yml` — "Certify locally" gains `--timeout-seconds 300` | `coworld certify` defaults to `--timeout-seconds 60` (confirmed against the 0.1.42 CLI), but the certification fixture is rounds=2 × ticksPerRound=480 = 1040 ticks @ tickHz=8 ≈ 130 s of play + `ShutdownGraceSeconds=20` ≈ 150 s to exit. 0.1.2 (run 32797631189) died `episode_timeout` after 62 s. Raised the timeout rather than shrinking the fixture, because `ci.yml`'s wasm-viewer `--soak` consumes the docker-smoke replay derived from the same fixture and needs >240 ticks. |
| `7e2f99792741eb9ebf7c3de76012b6d880611194` | `tools/build_manifest.py:641`, `coworld_manifest_template.json:27` → `secret://coworld/cooperative_hunting/anthropic_api_key`; `coworld-release.yml` `SLUG: cooperative_hunting` | 0.1.3 (run 32808207318) failed `upload-coworld` HTTP 400 `Coworld secret cooperative-hunting/anthropic_api_key cannot be used by Coworld 'cooperative_hunting'`. The server requires a `secret://coworld/<ns>/<key>` reference to name the Coworld's own namespace; `game.name` is the design-pinned underscored `cooperative_hunting` while the reference used the hyphenated repo slug. `SLUG`'s only uses in that workflow are `coworld secret put/list`, so it moves with the namespace. `ci.yml`'s `SLUG` is the image/repo slug and is unchanged; the Coworld was **not** renamed. Template re-verified byte-identical to `python3 tools/build_manifest.py` output. |

Both pushes went to `main` via the Git Data API (plain https push is unauthenticated for this
token) with `force=false`. No force pushes, no history rewrites.

CI on each fix sha, green before the dispatch that followed it:

| sha | ci.yml run | conclusion |
|---|---|---|
| `5ac03d9` | `32807756637` | success (test, docker-smoke, wasm-viewer) |
| `7e2f997` | `32808910707` | success (test, docker-smoke, wasm-viewer) |

Repo secrets were verified present before the first dispatch and never re-propagated:
`gh secret list -R Metta-AI/cogame-cooperative-hunting` → `SOFTMAX_TOKEN` and
`ANTHROPIC_API_KEY`, both `2026-08-24T15:42:19Z`.

## Exit criterion — `prompts/40-release.md` §Exit criterion

Checked against `runs/2026-08-24-cooperative-hunting/release-result.json`, the `release-result`
artifact of run **`32809315564`** (not a cached or neighbouring run).

| item | result | evidence |
|---|---|---|
| `ok: true` | **true** | `"ok": true`, `step_failed: null`, `errors: []` |
| `canonical: true` | **true** | `"canonical": true`; the workflow's "Enforce canonical" step passed |
| `certify` non-null and `certify.ok: true` | **true** | `certify.ok: true`; transcript `coworld-executable`, 10/10 steps passed |
| `certify.replay_liveness` contains `skipped (static replay bundle declared` | **true** | `"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"` |
| one `policies[]` entry per requested policy, distinct `<name>:vN` labels | **true** (4/4) | `cooperative-hunting-pack-caller:v2`, `cooperative-hunting-quartermaster:v2`, `cooperative-hunting-biggame:v2`, `cooperative-hunting-sidekick:v2` — four distinct labels, matching `tools/ci/policies.json` (2 LLM-prompt champions + 2 scripted baselines, unoverridden). `v2` because 0.1.3 had already created `v1` of each before it failed at upload; the new image digest makes the content differ, so these are fresh versions rather than dedupes. |
| champion #2 `player_id == ply_bac48eb1-662e-44f8-973d-f3e016dccf5d` | **true** | `cooperative-hunting-quartermaster` → `player_id: "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the other three `null` (owned by the CI token's own player, daveey) |
| `policy_version_id` null | expected, **not a failure** | `null` on all four — `upload-policy` prints no uuid; phase 50 resolves them from `GET /policy-versions` |
| `secret_put: true` | **true** | `"secret_put": true`; "Put the Coworld secret" ran **after** `upload-coworld`, per the load-bearing order |

Step order in the green run was build → certify → upload-policies → upload-coworld → secret put,
unchanged from the template.

## Dispatch history for this run

| version | run id | outcome |
|---|---|---|
| `0.1.0` | `32795666325` | `manifest_invalid` (tokens in `certification.game_config`) — fixed `b4b57b4f` (before r2) |
| `0.1.1` | `32796588037` | ping/pong `game_contract_violation` — fixed `c5eec79a` (before r2) |
| `0.1.2` | `32797631189` | certify `episode_timeout` after 62 s — fixed `5ac03d9` (this round) |
| `0.1.3` | `32808207318` | certify **passed** (first time), policies uploaded, then `upload-coworld` HTTP 400 on the secret namespace — fixed `7e2f997` (this round, on the coordinator's explicit go) |
| `0.1.4` | `32809315564` | **success** — every exit-criterion item true |

`release-result-0.1.3-failed.json` is kept alongside as the evidence for the 0.1.3 failure; the
authoritative artifact for `coworld.version = 0.1.4` is `release-result.json`.

## For the coordinator's STATE write

```
coworld.version         = "0.1.4"
coworld.cow_id          = "cow_d5e3a72d-bae0-4418-bb3e-e39f2c5cc81d"
coworld.manifest_sha    = "sha256:0dfeeb8e92befffa524161af55b34e914cbf7620bca58d4a0d4a2d0e98cad122"
coworld.release_run_id  = "32809315564"
policies.champion1      = "cooperative-hunting-pack-caller:v2"     (daveey)
policies.champion2      = "cooperative-hunting-quartermaster:v2"   (daveey-1, ply_bac48eb1-…)
policies.fillers        = ["cooperative-hunting-biggame:v2", "cooperative-hunting-sidekick:v2"]
```

I did not edit `STATE.json` or `log.md`.
