blocking: 0

# Phase-60 verdict — grid-wars
Head: coworld-builder main (VERIFY.md commit a647dda per log.md)   Checklist: docs/SPEC.md §Definition of done   Independent read written before reading VERIFY.md: yes

Judge context was fresh. Order of reading: SPEC §Definition of done → prompts/60-verify.md →
design.md → STATE.json / log.md / release-result.json / viewer-check artifacts (viewer-smoke.json
and viewer-smoke.png viewed directly) → **independent live re-fetches of every re-checkable
claim** → only then VERIFY.md. Every Observatory number below was re-fetched by this judge at
~2026-08-24T17:10Z, not copied from the verifier.

## Standing blocking findings

None.

## Refuted

None — the verifier reported all-true and no reviewer findings exist to refute. Adversarial
re-checks were run against the verifier instead; none of its eight TRUE verdicts fell.

## Checklist pass (independent — every item re-fetched or re-read by this judge)

| item | status | evidence |
|---|---|---|
| 1. ≥2 rounds completed after fillers set | TRUE | Re-fetched `GET /rounds?league_id=league_f07f6eeb…`: rounds 2, 3, 4 `completed` (created 16:27:33Z / 16:42:34Z / 16:57:34Z), round 1 `failed` with error verbatim `"Temporal RoundWorkflow failed before settling the round."`. Fillers registered before the first trigger: log.md phase-50 line orders `fillers registered 200 … unpaused 200; trigger 200`, and the same line records round 1's failure as a trigger race with "fillers were already set". Even discounting round 3 (settled in 11 s with no episode), rounds 2 and 4 both played full episodes — ≥2 on either reading. |
| 2. Both champions ranked; fillers absent or Baseline | TRUE | Re-fetched `GET /divisions/div_352d6e5d…/leaderboard` (bare array): rank 1 `daveey-1` `grid-wars-cartographer:v1` 1030.53 rounds_played=2 wins=2; rank 2 `daveey` `grid-wars-tactician:v1` 969.47 rounds_played=2 wins=0. Exactly two rows — fillers absent. |
| 3. Latest round's episode request completed with replay; participants correct | TRUE | Re-fetched: round 4 → `ereq_4c689bac-7687-4c87-8cdf-2f958755b145` `status:"completed"`, `replay_url` non-null (S3 `cd187239-….replay`). Participants: seat 0 `grid-wars-tactician`/`daveey` `is_filler:false`, seat 1 `grid-wars-cartographer`/`daveey-1` `is_filler:false`, seats 2–3 `grid-wars-bomber` `is_filler:true` (version e8fb1301… ≠ champion versions 451aa64e…/2a5cd05c…). |
| 4. Replay bytes valid, protocol matches, reason complete, champions doing the thing | TRUE | Judge re-downloaded the replay (31,566 bytes): `jq -e` strict parse ok **and** python `bytes.decode('utf-8')` ok; `protocol` = `gridwars.replay.v1` (the manifest declares no replay-protocol string — `game.protocols` carries `gridwars.player.v1`; the match is against the repo/design declaration, which the verifier documented rather than assumed); `results.reason` = `"complete"`; champion seats 0/1: 10/10 submits `origin:"llm"`, `scripted:false`, 32–82 lines, zero compileErrors, distinct evolving banners per round; `fallbacks:[0,0,0,0]`, `faults:[0,0,0,0]`. Not all fallbacks — zero fallbacks. |
| 5. Hosted game log clean | TRUE | Judge re-fetched `GET /episode-requests/ereq_4c689bac…/artifacts/logs` with elevated header (24,129 bytes): `grep -nE 'falling back\|LLM provider is unavailable\|cut off at max_tokens\|rejected'` → no matches, CLEAN. No platform-wide exception claimed or needed. |
| 6. Public page uses the static replay path; featured match present | TRUE | Judge re-fetched `https://softmax.com/grid-wars` (client-rendered, no iframe in raw HTML — treated as unknown per prompt); SSR payload `state.playlist[0]` = featured match `grid-wars.r4.e1` (daveey-1 vs daveey, div_352d6e5d…); re-POSTed `/coworlds/replays/session` → `viewer_url` = `…/v2/coworlds/replays/static/cow_f009d83c-…/sha256%3A126e3dfb…/index.html?replay=<s3 url>&v=2`, `ready:true`. `<sha>` = manifest_hash matching STATE.coworld.manifest_sha. Not a `/client/replay` pod URL. |
| 7. Certification declared the static bundle | TRUE | Committed `runs/2026-08-24-grid-wars/release-result.json` read directly: `.certify.replay_liveness` = `"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"`. |
| 8. Viewer executed; replay advances; grounded judgment | TRUE | (a) `gh run view 32754228468` re-checked by judge: workflow `viewer-check`, `conclusion:"success"`, created 17:01:34Z; `viewer-smoke.json` `loaded:true` (2013 ms), `data_replay_loaded:"true"`, bridge `["loading","ready"]`, `data_replay_error:null`, no failure; smoke `url` is byte-identical to check 6's session `viewer_url` (verified by string compare). (b) three scrub clocks differ: `R1 / 5 · SUBMITTING` / `R3 / 5 · TICK 198 / 400` / `R5 / 5 · FINAL`. (c) judgment paragraph present and grounded — judge viewed `viewer-smoke.png` independently: endcard `daveey-1 OUTPAINTED THE FIELD` with table (+107.3/4/713/0, Gizmo −7.5, Piston −11.7, daveey −87.9) reconciling with `results` (scores −87.95/107.25/−11.75/−7.55; tiles 37/713/68/89; roundsWon 0/4/1/0); territory bar `200` vs `658 free` = 900 − (24+200+6+12) exactly matching round-5 tiles `[24,200,6,12]`; live GWL code pane with `LLM` badge and executing-line gutter; bullwhip-lineage chrome (wordmark/clock/scorebug/transport/scrubber-with-beats, position `2024 / 2024`). Legible; shows the game; not the gridlock failure mode. |

## Verifier report audit

| claim | verifier said | judge verified | agrees |
|---|---|---|---|
| rounds | 2,3,4 completed; r1 failed, error verbatim | re-fetched, identical incl. error text | yes |
| round 3 anomaly | completed in 11 s, no episode, disclosed | re-fetched round 3: completed, error null; created→completed = 11 s | yes |
| leaderboard | 2 rows, daveey-1 1030.53 / daveey 969.47, rounds_played 2 | re-fetched, identical to full float precision | yes |
| ereq | ereq_4c689bac completed, replay_url, participants/scores | re-fetched, identical | yes |
| replay | strict JSON, 31566 B, protocol, reason, 10/10 llm, 0 fallbacks | re-downloaded and re-parsed (jq + python utf-8), identical | yes |
| hosted log | CLEAN raw+decoded, 24129 B raw | re-fetched, 24,129 B, grep CLEAN | yes |
| featured/iframe | SSR playlist[0] + session POST, static path, ready:true | reproduced both calls, identical viewer_url | yes |
| release-result | committed copy, liveness string | read committed file, string present | yes |
| viewer-check | run 32754228468 green, loaded:true, 3 clocks differ | `gh run view`: success; json re-read; png viewed; smoke url == iframe src | yes |
| judgment numbers | endcard/scorebug/terrbar reconcile with results | recomputed from png vs replay JSON — all reconcile | yes |

## Non-blocking observations

1. **Check 1's timestamp phrasing is imprecise but its conclusion holds.** VERIFY.md says fillers
   were "registered at 16:29:56Z … before round 1 was triggered", yet round 1's `created_at` is
   16:27:00Z. 16:29:56Z is the log-*write* time of a batched phase-50 line; the ordering *within*
   that line (`fillers registered … unpaused … trigger`) and round 1's own recorded failure context
   ("fillers were already set") are what establish fillers-before-trigger. The inference is right;
   the cited timestamp is not the registration time.
2. `release-result.json` records `hosted_certification: "certifying"` (in-flight at phase-40
   capture). Not a DoD item — item 7 asks only for the replay-liveness string — and the live
   coworld is `canonical: true` (re-fetched). Noted for completeness.
3. Both filler seats in the featured episode were `grid-wars-bomber` (painter drew no seat that
   episode). Round-robin filler seating; no DoD item constrains it.
4. Verifier's own legibility note stands: claimed territory renders very dark at the final frame;
   mid-timeline frames show the painting better. Cosmetic.

BLOCKING: 0
