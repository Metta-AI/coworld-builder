# Phase 40 — Release report (run 2026-08-23-rumor)

## Result

| field | value |
|---|---|
| repo | `Metta-AI/cogame-rumor` |
| ref | `main` @ `5ac1631a1f1fdd5ecb63a6fe729281cb1181e760` |
| version | **0.1.0** |
| cow_id | **`cow_46b04bae-028d-4f7a-8444-c18590d68521`** |
| manifest_sha | `sha256:83e14e8087bf4e1fc862471588e251cb443b2b19dada715d9d0f0c3c97c56c51` |
| release run id | **32665829446** |
| run URL | https://github.com/Metta-AI/cogame-rumor/actions/runs/32665829446 |
| conclusion | success |

`release-result.json` (artifact `release-result`, copied to
`runs/2026-08-23-rumor/release-result.json`):
`ok: true`, `canonical: true`, `secret_put: true`, `step_failed: null`, `errors: []`,
`hosted_smoke: "passed"`, `hosted_certification: "certifying"`.

Certification: `certify.ok == true`, all 10 `coworld-executable` transcript steps passed, and
`certify.replay_liveness` =
`"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"`.

## Policies (4/4, distinct labels)

| role | label | owner (`player_id`) |
|---|---|---|
| champion #1 (LLM `PLAYER_PROMPT`) | `rumor-corroborate:v1` | daveey (`null` = CI token's player) |
| champion #2 (LLM `PLAYER_PROMPT`) | `rumor-skeptic:v1` | `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d` (daveey-1) |
| filler (`PLAYER_SCRIPTED=gossip`) | `rumor-gossip:v1` | daveey (`null`) |
| filler (`PLAYER_SCRIPTED=herd`) | `rumor-herd:v1` | daveey (`null`) |

`policy_version_id` is `null` on all four entries — expected (`upload-policy` prints no uuid);
phase 50 resolves the UUIDs from `GET /policy-versions` with a client-side filter.

## Dispatches (1 of a 3-dispatch budget used)

| # | version | run id | step_failed | change made |
|---|---|---|---|---|
| 1 | 0.1.0 | 32665829446 | `null` (success) | none — first dispatch of unchanged `main` @ `5ac1631`; policies read from `tools/ci/policies.json`, no `policies` override input, `put_secret=true`, no `skip_certify` |

No retries were needed: no version bump, no manifest fix, no workflow-order fix.

## Pre-flight checks

- `gh secret list -R Metta-AI/cogame-rumor` showed both `SOFTMAX_TOKEN` and `ANTHROPIC_API_KEY`
  (both set 2026-08-23T16:41:52Z in phase 20) — no re-propagation needed.
- `coworld-release.yml` step order verified load-bearing-correct before dispatch:
  Build manifest (L153) → Certify locally (L167) → Upload the policies (L206) →
  Upload the Coworld (L304) → Put the Coworld secret (L342).
- Run located with the `dispatch-then-watch` recipe (`dispatched_at=2026-08-23T20:53:58Z`,
  polled `gh run list --event workflow_dispatch` until a newer run appeared) — not `-L 1`.

## Files written

- `runs/2026-08-23-rumor/release-result.json` (this run's `release-result` artifact, verbatim)
- `runs/2026-08-23-rumor/release-report.md` (this file)

No code or workflow changes were made to `Metta-AI/cogame-rumor` during phase 40.
