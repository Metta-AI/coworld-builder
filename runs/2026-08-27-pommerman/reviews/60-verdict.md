blocking: 0

# Phase 60 verdict — pommerman (2026-08-27)
Head: cogame-pommerman ec8f1fb ("60-check5: the attempt-1 notice announces a retry, not a fallback")
Checklist: docs/SPEC.md §Definition of done (via prompts/60-verify.md)
Independent read: VERIFY.md re-adjudicated with fresh re-fetches at ~2026-08-27T22:0xZ; fixer self-reports not consulted (phase 60 has none; phase-30 r1-* files not read).

## Per-item verdicts

1. **≥2 completed rounds after fillers set — PASS.** Re-fetched `GET /rounds?league_id=league_7b53400d…` myself: rounds 2–8 `completed`, round 1 `failed` ("Temporal RoundWorkflow failed before settling the round.", excluded correctly); rounds 3–7 created 20:25:31Z–21:25:36Z, all after the filler registration at 20:11:28Z (log.md:36 "50 fillers registered 200: sapper 95cc7892, camper 2dec3894").
2. **Both champions ranked — PASS.** Re-fetched `GET /divisions/div_7c2c9172…/leaderboard` myself: daveey rank 1 `pommerman-firestarter:v1` rounds_played 7, daveey-1 rank 2 `pommerman-cornerman:v1` rounds_played 7; exactly two rows, fillers absent (sapper/camper appear nowhere on the board).
3. **Latest round's episode request completed with replay — PASS.** Re-fetched `GET /episode-requests/ereq_1274172a…` myself: `status=completed`, replay_url `…/1dc81bbf….replay`, coworld_id `cow_ab2d905c…` / coworld_version `0.1.1` (proving round 7 ran the canonical re-release), participants daveey (seat 0) and daveey-1 (seat 1) non-filler, camper/sapper `is_filler: true`.
4. **Replay bytes valid and show the game — PASS.** The binary COWLDPOM format plus `tools/replay_summary.py` substitute is genuinely design-declared (design.md:959–986 "The phase-60 substitute for SPEC §Definition of done check 4", verified in the run's committed design copy). I re-fetched the 199,040-byte replay and re-ran the tool at head ec8f1fb myself: strict-JSON parse ok, `protocol == "pommerman/v1"` (matches source pin `src/pommerman/sim_types.nim:20`), `results.reason == "complete"`, 72/72 champion orders `source=="llm"`, `fallbackTurns [0,0,0,0]`, 72 distinct non-empty-but-one says, 81/144 non-trivial radio pairs — every number in VERIFY.md §4 reproduced exactly.
5. **Hosted game log clean — PASS.** I re-fetched `…/artifacts/logs` (154,131 bytes) and decoded the byte-string reprs myself (0 unparsed lines): the specified grep → **CLEAN**. The only case-insensitive near-miss is the camelCase `ordersRejected` key inside the results JSON (my decoded line 324) — a field name, not a match. Exactly two "attempt 1 failed, will retry" lines, no "out of attempts": the round-7 (0.1.1) episode had zero actual fallbacks.
6. **Public page uses the static replay path — PASS.** Re-fetched `https://softmax.com/pommerman` myself: zero occurrences of `/client/replay`; SSR playlist present and current (now `pommerman.r8.e1`, still coworldId `cow_ab2d905c…` 0.1.1 with both ranked champions in the matchup). Re-POSTed `/coworlds/replays/session` myself: `…/v2/coworlds/replays/static/cow_ab2d905c…/sha256%3Af143a646…/index.html?replay=…`, sha equal to the live `manifest_hash` I re-fetched from `GET /coworlds/$COW`. Canonical is the new cow (0.1.1 `canonical: true`); the stale `cow_224b5627` is `canonical: false` and referenced nowhere.
7. **Certification declared the static bundle — PASS.** Read the committed `runs/2026-08-27-pommerman/release-result.json` myself: `.certify.replay_liveness` = "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)", `version 0.1.1`, `cow_id cow_ab2d905c…`, `certify.ok true`, ten `[pass]` cert steps in `output_tail` — the 0.1.1 artifact, not the 0.1.0 one (overwritten 21:14:13Z per log.md:47).
8. **Viewer executed and judged — PASS.** Verified run 33119081304 via `gh run view`: `conclusion: success`, created 21:38:31Z (matches the dispatch). Committed `viewer-smoke.json`: `loaded: true` at 2055 ms via `data_replay_loaded: "true"`, `failure: null`, and three differing scrub readouts (turn 1/tick 0 → turn 31/tick 122 → turn 36/tick 141, caption advancing to the collapsed 5×5). I examined `viewer-smoke.png` myself: legible starter chrome (scorebug, transport strip, scrubber with "BOMBERS STANDING" momentum graph, speed chips, endcard) showing "RED TAKES IT — BLUE WIPED AT TICK 141", `SCORE +105 / -105`, `end rule: wipe · 141 ticks · wood 6–21 · complete`, team tables (RED-1·DAVEEY 0/8/6/3·5 etc.) — every figure reconciles exactly with the replay results I extracted independently (`bombsPlaced [8,5,0,14]`, `teamWood [6,21]`, `finalTick 141`). The judgment paragraph exists and matches the picture.

## Blocking findings

None.

## Pre-disclosed attention items — none falsifies a DoD item

- `feed_lines: 0` is a harness-selector mismatch, confirmed in source: `templates/tools/ci/viewer_smoke.mjs:425` queries `#feed, .feed, #log`; the shell's feed is `id="killfeed"` (`client/replay_broadcast.html:1002`). The feed content is visible in the PNG. Not a check-8 predicate (loaded + advancing clocks both hold).
- Camper `bombsPlaced == 0`: the design's own substitute clause ("non-zero bombsPlaced on every seat", design.md:984) is unmet on baseline seat 2 — but SPEC item 4's predicate is about the **champion** seats doing the thing, which they demonstrably do (8 and 5 bombs, 72/72 LLM orders). A filler-quality issue, not a DoD failure.
- `kicks [0,0,0,0]` — no hosted episode has exercised the kick beat; no DoD item requires it.
- `canvas_text.total: 0` — OffscreenCanvas/worker rendering blinds the main-frame fillText hook; not a check-8 predicate, and the PNG is direct rendered evidence.
- Scorebug name truncation at 1280 px — cosmetic.
- Committed release-result.json says `hosted_certification: "certifying"` (in-flight at artifact-capture time); DoD item 7's predicate is only the replay-liveness string, which is present, and the coworld is canonical and running hosted episodes.

BLOCKING: 0
