blocking: 0

# r-phase60 verdict — hive
Head: coworld `cow_89df098f-6f9b-42ee-adc0-ecf1252103cd` v0.1.1, manifest `sha256:8e16a28a45164d671865fee2068f719bf1f57fc2117702d0420b4ede01cf9b2b`
Checklist: `docs/SPEC.md` §Definition of done (phase 60) / `prompts/60-verify.md`
Independent read written before reading VERIFY.md: **yes** — all live re-fetches (rounds, leaderboard, both episode requests, replay bytes, hosted logs, /hive page, /coworlds, replays/session, viewer bundle assets, gh run 32627090556) and the committed evidence (viewer-smoke.json, viewer-smoke.png viewed, release-result.json) were made and noted before VERIFY.md was opened.

## Per-check verdicts (one line each)

1. **TRUE** — re-fetched live: rounds 2 (`round_11ff8df8`, completed) and 3 (`round_0eaae974`, completed); round 1 failed with the verbatim error `Temporal RoundWorkflow failed before settling the round.` and is correctly excluded; round 2's episode participants include both fillers (`is_filler: true` × 2), proving it ran with fillers seated.
2. **TRUE** — re-fetched live: bare-array leaderboard has exactly 2 rows — daveey-1/hive-swarmraid:v1 Elo 1001.47 rp=2, daveey/hive-pathwright:v1 Elo 998.53 rp=2; no filler rows (the "fillers absent" branch).
3. **TRUE** — re-fetched live: `ereq_4dce5786` for round 3 is `completed`, `replay_url` = `…/334e0e3a-c0bb-40d6-81a3-e3bb09d6780d.replay`, participants `daveey`/`daveey-1` (`is_filler: false`) + `hive-marcher`/`hive-driftling` (`is_filler: true`), `policy_name` fields exactly as VERIFY pasted.
4. **TRUE** (adaptation ACCEPTED) — replay re-fetched (211 002 bytes), strict UTF-8 under Python `bytes.decode` + `json.loads`; `protocol: hive.replay.v1`; `complete/full_time`; 40/40 champion doctrines `source: "llm"`, 0 `fallback` events and 0 `source: "fallback"` doctrines, notes cite live view fields (`delivered_last_turn`, cache cells, rival grid, running score) — a policy reading the observation, not a template.
5. **TRUE** — logs re-fetched with elevated header (83 767 bytes, 4 containers); grep of `falling back|LLM provider is unavailable|cut off at max_tokens|rejected` → CLEAN; log shows real Bedrock `InvokeModel` calls, all HTTP 200, `episode_request_id`/`job_request_id` matching check 3's ereq and replay uuid.
6. **TRUE** (adaptation ACCEPTED) — reproduced all three legs: raw `/hive` HTML has no `<iframe` (client-rendered, prompt-documented); `/coworlds` `featured_match` is null for **all 200** coworlds (platform-wide, so the prompt's fallback is inert — verified, not taken on trust); the page SSR carries a playlist entry (featured match present) and `POST /coworlds/replays/session` returns `viewer_url` = `/v2/coworlds/replays/static/cow_89df098f…/sha256%3A8e16a28a…/index.html?replay=<s3>` with `ready: true`; the string `/client/replay` occurs nowhere in the page or the route.
7. **TRUE** — committed `runs/2026-08-23-hive/release-result.json` read: `certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)`; `cow_id`/`version 0.1.1`/`manifest_sha`/`canonical: true` all match STATE.
8. **TRUE** — gh run 32627090556 verified: `workflow_dispatch`, `success`, input URL is exactly the check-6 static route with the check-3 replay; committed viewer-smoke.json: `loaded: true` via **both** `data-replay-loaded="true"` and bridge `["loading","ready"]`, three differing clocks (`3:19 TURN 0/20` → `1:37 TURN 10/20` → `FINAL GAME OVER`), `failure: null`; the png (viewed) is a legible endcard whose every number reconciles with the replay bytes (`delivered [25,77,82,27]`, total 211, winner Teal 38.9 %, seed 1139974405, `complete/full_time · 4800 ticks`).

## Standing blocking findings

None. Every checklist item verified at head from fetched or committed evidence.

## Refuted

None — no reviewer findings existed to refute; this is the phase-60 adjudication of VERIFY.md, and no claim in it failed reproduction.

## The two verifier adaptations, judged

- **Check 4 → `doctrines` array instead of `type=="decision"` events: ACCEPTED.** I confirmed at the bytes that the replay has zero `decision`-type events (event vocabulary: doctrine/deliver/harvest/raid/trail_war/…), so the prompt's literal jq would return 0 on any hive replay by construction. The design note (§Event vocabulary, §Replay bytes) names `doctrine` records with `source: llm|scripted|fallback` as *the* decision record the phase-60 verifier reads. The adaptation preserves the check's substance exactly — per-seat, per-turn decision provenance plus a fallback count — and the champion seats are the `llm` seats (`policy_kinds: ["llm","llm","scripted","scripted"]` maps seats 0/1 to daveey/daveey-1).
- **Check 6 → SSR playlist + `POST /coworlds/replays/session` instead of iframe grep / coworld detail API: ACCEPTED.** I reproduced the failure of both prompt-listed sources myself (no iframe in raw HTML; `featured_match: null` on all 200 coworlds, so it signals nothing about this coworld), and I reproduced the substitute evidence live: the session endpoint — the call the page's own JS makes — returned the static route with the correct cow_id and manifest sha, `ready: true`. This is stronger evidence than the documented fallback, not weaker, and VERIFY.md records which source was used, as the prompt requires.

## Checklist pass (independent)

| item | status | evidence |
|---|---|---|
| 1. ≥2 completed rounds after fillers | TRUE | live `GET /rounds?league_id=league_2d1d904b…`: rounds 2+3 `completed`; round 2 episode `ereq_948b0444` seats 2×`is_filler: true`; log.md:50 fillers 07:41:09Z |
| 2. both champions ranked | TRUE | live `GET /divisions/div_86b9824f…/leaderboard`: 2 rows, daveey rp=2 + daveey-1 rp=2, no fillers |
| 3. latest round ereq completed + replay | TRUE | live `GET /episode-requests/ereq_4dce5786`: `completed`, replay_url `334e0e3a…`, participants correct |
| 4. replay bytes valid, show the game | TRUE | live S3 fetch: strict UTF-8 JSON, `hive.replay.v1`, `complete/full_time`, 40/40 llm, 0 fallbacks, 211 delivers / 13 raids / 27 trail_wars |
| 5. hosted log clean | TRUE | live elevated fetch: grep → CLEAN, 83 767 bytes, Bedrock calls all 200 |
| 6. static replay path, featured match | TRUE | live: no `/client/replay` anywhere; session viewer_url = static route with correct cow_id+sha; SSR playlist present |
| 7. cert declared static bundle | TRUE | committed `release-result.json`: required substring present verbatim |
| 8. viewer executed + judged | TRUE | gh run 32627090556 success (URL verified in run log); committed json/png; clocks differ; png legible + reconciles |

## Verifier report audit

| claim in VERIFY.md | I verified | agrees |
|---|---|---|
| rounds 2+3 completed, round 1 failed w/ verbatim Temporal error | live re-fetch, identical incl. created_at timestamps | ✅ |
| leaderboard rows/Elo/rp exactly as pasted | live re-fetch, identical to the digit | ✅ |
| ereq_4dce5786 participants incl. `policy_name` per seat | live re-fetch, identical | ✅ |
| replay 211 002 bytes, protocol/reason/doctrine tallies, distinct_param_tuples 3/7 | recomputed from live-fetched bytes; full-tuple counts 3 (seat 0) / 7 (seat 1) confirmed | ✅ |
| logs 83 767 bytes, 4 containers, CLEAN | live re-fetch, identical byte count, CLEAN | ✅ |
| no iframe in raw HTML; featured_match null platform-wide; session → static viewer_url | all three reproduced live (0/200 coworlds have featured_match) | ✅ |
| release-result.json replay_liveness string | committed file read, identical | ✅ |
| run 32627090556 success, URL = static route + round-3 replay, created 08:00:27Z | `gh api` + run log, identical | ✅ |
| bundle assets 200 (index.html 117 563 B, static_replay.js 7 640 B, wasm 227 909 B); `static_replay_worker.js` 404 but unreferenced | spot-fetched: byte-identical; served JS has bridge (`src: "coworld-replay"`) and zero `Worker` references; log.md:20 records the main-thread deviation at phase 20 | ✅ |

## Non-blocking observations

- **Check 1 timing nuance:** round 2's API `created_at` (07:40:24Z) precedes the 07:41:09Z filler log line — log.md lines 50–52 are batch-written, so strict wall-clock ordering of "fillers before round 2 was triggered" cannot be proven from timestamps alone. It does not matter materially: round 2's episode demonstrably seated both fillers (`is_filler: true`) and both champions, which is the substance of the requirement. VERIFY.md's phrasing ("before round 2 was triggered") is slightly stronger than its timestamp evidence; the participant evidence carries the check regardless.
- **Featured episode has since rotated:** my live page fetch shows the playlist now featuring a newer episode (`bb76aa2d…`, replay `3027ef96…`) — the ladder has advanced past round 3. This is expected drift, not a contradiction; the session endpoint still returns the same static route for the current replay, so check 6's property holds at the current head too.
- `feed_lines: 0` in the smoke json (the `#killfeed` had no lines at the sampled instants) — correctly disclosed by the verifier as a legibility nit for a future review, not a check-8 failure; the doctrine chips and endcard carry the winning/why load in the screenshot.
- `art/meadow_floor.jpg` is only 1 579 bytes — small for a painted tile, but the rendered screenshot shows a non-blank floor with pheromone glow, and check 8's gates are load/advance/judgment, all met.

BLOCKING: 0
