# Phase 40 — release summary (cogame-smac-starcraft-micro)

**Accepted release: version `0.1.3`** (see the 0.1.3 section at the bottom; the 0.1.2
section below is kept as history).

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

---

# 0.1.3 — targeted re-release (phase-60 log-honesty fix)

Phase-60 verification failed exactly one check: the hosted game log must grep clean for
`falling back|LLM provider is unavailable|cut off at max_tokens|rejected`. It did not, and the
cause was a real (small) deviation from the design note rather than a hosted flake — a reply the
design says to REPAIR was being treated as a parse failure, and the interim per-attempt message
printed the phrase the grep reserves for a genuine degrade.

**Accepted release: version `0.1.3`.** `release-result.json` in this directory is the 0.1.3
artifact (the 0.1.2 one it replaced is reproduced in the table above).

| field | value |
|---|---|
| version | `0.1.3` |
| `cow_id` | `cow_345bfc54-561e-4606-8de1-e3086f37d58a` |
| `manifest_sha` | `sha256:3c1e7703ca64b59f9774673290450d9ca1f3429e39c01738e0b213521a4ed078` |
| release run id | `33065622007` (conclusion: success) |
| release run url | https://github.com/Metta-AI/cogame-smac-starcraft-micro/actions/runs/33065622007 |
| head sha of the run | `545afa9f610f9b15d3990da2297f920575365fea` |
| `ok` / `canonical` | `true` / `true` |
| `hosted_smoke` / `hosted_certification` | `passed` / `certified (main-893f1b64f31e)` |
| `certify.ok` | `true` |
| `certify.replay_liveness` | `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)` |
| `secret_put` | `true` |
| dispatches used | 1 (no triage needed) |

## Policy versions (v4 — one upload per dispatch, as before)

| label | role | owner (`player_id`) |
|---|---|---|
| `smac-starcraft-micro-marshal:v4` | champion #1, `PLAYER_PROMPT` | daveey (`null`) |
| `smac-starcraft-micro-skirmish:v4` | champion #2, `PLAYER_PROMPT` | daveey-1 (`ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`) |
| `smac-starcraft-micro-focusfire:v4` | filler, `PLAYER_SCRIPTED=focusfire` | daveey (`null`) |
| `smac-starcraft-micro-charge:v4` | filler, `PLAYER_SCRIPTED=charge` | daveey (`null`) |

The league's submitted policies are `v3` and are player-side; they are unaffected by this release,
which changes only the game-server image.

## The fix (two commits, both pinned by the design note)

| sha | what |
|---|---|
| `8968e88f0d3fb02e2c8f74cc82a05dd2e8f6f9cf` | `fix(directives): a reply that names no commanded cog is repaired, not a parse failure` — `src/smac/directives.nim`, `src/smac/decide.nim`, `tests/test_directives.nim`, `tests/test_engine.nim` |
| `545afa9f610f9b15d3990da2297f920575365fea` | `fix(decide): only the terminal degrade line may say "falling back"` — `src/smac/decide.nim`, `tests/test_engine.nim` |

1. **The repair table is now implemented as written** (design §Reply schema and per-field caps).
   `cogs[].id` — "an unmatched entry is assigned to the seat's unit by position" — already worked;
   `cogs` — "an empty or missing array keeps last turn's directive, else focusfire's" — did not:
   `parseSquadDirective` raised `DirectiveError("reply named no commanded cog")`, which burned the
   seat's retry, wrote a `fallback` record with cause `parse_error` and printed the terminal
   "falling back" line for a turn the design says should simply carry on. It no longer raises for a
   reply that parsed: unfilled cogs keep `fromReply = false` and `repairMissingOrders` resolves them
   to last turn's directive (else focusfire's), the turn stays `source: "llm"` with the model's own
   note, and the log records the benign, distinct line
   `smac llm: seat N repaired: reply named no commanded cog; kept <last turn's|focusfire's> directive on turn T`.
   Only text from which no JSON object can be recovered at all still raises.
2. **The interim attempt message no longer says "falling back."** It now reads
   `attempt 1 failed, will retry: …` (`no attempt left` on the last attempt). The terminal
   `seat N falling back to focusfire (<cause>) on turn T` is byte-identical to before — it is the
   honest signal the phase-60 grep exists to catch, and `tests/test_engine.nim` now asserts every
   non-comment `falling back` line in `decide.nim` is that terminal line.

Tests added/changed (no existing assertion weakened): `tests/test_directives.nim` — a wrong-id entry
lands by position, stays `fromReply`/`llm`-sourced; empty `cogs`, missing `cogs` and a `cogs` array
of non-objects all repair instead of raising, while unrecoverable text still raises.
`tests/test_engine.nim` — a repaired turn on turn 0 takes focusfire's order and on turn k>0 takes
turn k-1's order, staying `dsLlm` (i.e. never counted as a fallback turn); plus the source-grep test
above.

## CI

`ci.yml` green on `545afa9f610f9b15d3990da2297f920575365fea`, twice — the push-triggered run
[33064856452](https://github.com/Metta-AI/cogame-smac-starcraft-micro/actions/runs/33064856452) and
the dispatched run
[33064860833](https://github.com/Metta-AI/cogame-smac-starcraft-micro/actions/runs/33064860833).
Both conclusion **success**, all three jobs green in each (test, docker-smoke, wasm-viewer).

## Known deviation left in place (not part of this fix)

The design's tolerant-parsing paragraph also lists "accept a bare order object without the `cogs`
wrapper". `cogEntries` still reads only `payload{"cogs"}`, so a bare order object now takes the
repair path (last turn's directive) instead of being honoured as the model's order. That is benign
for the phase-60 grep and for the never-unactuated guarantee, but it is a real, small gap against
§Reply schema; it was left out of this targeted fix deliberately.
