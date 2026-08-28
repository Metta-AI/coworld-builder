blocking: 0

# phase-60 verdict — gen-generals-io

Head: `Metta-AI/cogame-gen-generals-io` @ `e8be315f` · cow `cow_faf3b0f4-c6b0-43e0-88b8-772046e5c61d` v0.1.0
Checklist: `docs/SPEC.md` §Definition of done (phase 60, all fetched, never assumed) — items 1–8, read in full before VERIFY.md.
Independent read written before reading VERIFY.md: **yes** — I re-ran every check against the live API/S3/repo/committed artifacts first (fetched 2026-08-28, this session), then audited the verifier's pasted bytes against my own.

## Standing blocking findings

None.

## Checklist pass (independent, at head)

Note the ladder has advanced since VERIFY.md was written: round 4 is now `completed` and the featured match is now round 4. Nothing regressed; items 1–3 and 6 are strictly stronger at head.

| item | status | my evidence (fetched fresh) | verifier's evidence held up |
|---|---|---|---|
| 1 | TRUE | `GET /rounds?league_id=$L` → rounds 2, 3, **4** `completed`; round 1 `failed` with error verbatim `Temporal RoundWorkflow failed before settling the round.` (pre-filler auto-round; does not count). Fillers were demonstrably in force for every counted round: rounds 2 and 3 seat `is_filler:true` participants, and rounds 3 (created 08:17:10Z) and 4 (completed 08:37:38Z) postdate even the latest reading of the filler-registration log line (08:12:40Z), so ≥2 post-filler completed rounds hold under the strictest timestamp reading. | yes — verifier's round list, error string, and filler-version cross-check all match my fetch |
| 2 | TRUE | `GET /divisions/$D/leaderboard` → exactly 2 rows: `1 daveey-1 gen-generals-io-regicide:v1 1043.75 3 3.0`, `2 daveey gen-generals-io-landgrab:v1 956.25 3 0.0`; fillers absent | yes — verifier saw the same two rows at `rounds_played:2`; board has since advanced to 3, confirming it is live |
| 3 | TRUE | Round 3: `GET /rounds/round_6ef8dba1…/episode-requests` → `ereq_c07776fa… completed`, `replay_url` = `…/16454404-…be1.replay`; participants seat 0 `daveey`/landgrab `is_filler:false`, seat 1 `daveey-1`/regicide `is_filler:false`, seats 2–3 crown `is_filler:true`. At head the latest completed round is 4: `ereq_1209c7e7… completed` with `replay_url` = `…/ac948cb8-….replay` — item holds either way. (Flat `GET /episode-requests?round_id=` really is 405; nested route per playbook.) | yes — byte-identical participants and scores |
| 4 | TRUE | Fetched the S3 bytes (40 655 B). They are the **binary `COWLDGEN` container**, not raw JSON — `jq -e` on raw bytes fails. This is the format the accepted design note declares (`design.md` §Replay bytes: starter coworld-ctf's codec, with `tools/replay_summary.py` named as "the phase-60 substitute for SPEC check 4"), and the manifest/PROTOCOL.md document it. I ran the repo's `tools/replay_summary.py` @ e8be315f myself: strict UTF-8 JSON ok; `protocol "gen-generals-io/v1"` (matches manifest/declared value); `results.reason "complete"`, `endRule "conquest"` (the normal case — the declared-acceptable `deadline` exception was not needed); `land add = 129 > 40`; per-seat plans: seat 0 = 7/7 llm, seat 1 = 30/30 llm (all 37 with non-empty, situation-specific notes — fog reads, raid targets, crown threats), seats 2–3 scripted (the fillers, as designed); **0 fallbacks**, 0 rejected directives. Champion seats are doing the thing the game is about. | yes — every number in VERIFY.md §4 matches my independent decode |
| 5 | TRUE | `GET /episode-requests/ereq_c07776fa…/artifacts/logs` (elevated) → grep for `falling back|LLM provider is unavailable|cut off at max_tokens|rejected` = **CLEAN** on both raw and decoded text; game container shows a healthy episode (`episode complete (complete/conquest) after 234 turns`), every Bedrock call 200 OK | yes — verifier additionally decoded the `b'…'` reprs before grepping, which is stricter than the prompt's command |
| 6 | TRUE | Raw-HTML iframe grep empty (client-rendered — documented non-signal); `/coworlds` `featured_match` null platform-wide (documented non-signal). The two real sources per playbook §Featured match: **SSR payload `state.playlist[0]`** on `https://softmax.com/gen-generals-io` → featured match present (at head: round 4, `ac948cb8-…`, matchup daveey-1 #1 vs daveey #2); **`POST /coworlds/replays/session`** → `viewer_url` = `…/v2/coworlds/replays/static/cow_faf3b0f4…/sha256%3A6fd4384…/index.html?v=2#replay=<s3 url>`, `ready:true`. `<sha>` = the coworld's `manifest_hash` = `STATE.coworld.manifest_sha`. The `#replay=` fragment form is the documented 2026-08-28 shape of the same static route. No `/client/replay` pod URL anywhere. | yes — I reproduced the session call and got the identical static URL (for round 4's replay at head) |
| 7 | TRUE | Committed `runs/2026-08-28-gen-generals-io/release-result.json` → `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)` — required string present verbatim, read from the committed copy | yes |
| 8 | TRUE | (a) `viewer-smoke.json`: `loaded:true`, `data_replay_loaded:"true"`, `failure:null`, first frame at 2 005 ms — CI run `33155441744` conclusion **success** (checked myself via `gh run view`). (b) Three scrub clocks **differ**: `TURN 2/240…` → `TURN 171/240 … GREEN LEADS 73 LAND` → `FINAL GAME OVER`. (c) I viewed `viewer-smoke.png` myself: full endcard frame — four-plate scorebug, 16×10 board with garrison integers, beat toast `GREEN TAKES BLUE'S CROWN — INHERITS 17 TILES AND 16 ARMIES`, endcard `GENERALS — BASELINE WINS` / `LAST CROWN STANDING` with a COMMANDER/LAND/ARMY/CITIES/CROWNS table whose numbers reconcile **exactly** with the replay record (`land[2]=129, army[2]=1132, cities[2]=10, generalsCaptured[2]=3, eliminatedTurn=[49,233,-1,195], rank=[3,1,0,2]`), and the starter's chrome verbatim (transport strip, spoilers toggle, speed chips, scrubber with LAND momentum graph and beat ticks). The round-2 probe artifact (`probe-round2/`, run `33154949153`) corroborates on a second episode (`GENERALS — DAVEEY-1 WINS`, 125/482/8/2 = round-2 results). Both artifacts committed under `runs/<run>/viewer-check/`. The judgment paragraph in VERIFY.md is written from the rendered evidence and claims nothing the pixels don't show. | yes |

## Refuted

None — I attempted to refute all eight verdicts and every one survived. No pasted output disagreed with a fresh fetch; no endpoint, field, or id was wrong; no verdict rested on inference where a fetch was required.

## The four flagged observations — blocking or not

**(1) `REPLAY HASH MISMATCH — SHOWING RECORDED PLANS` banner lit on both hosted replays — NOT blocking, but a real defect to record.**
Grounding in the SPEC: item 8 is true iff (a) `loaded:true`, (b) the three clock readouts differ, (c) the judgment paragraph is legible and shows the game. All three hold on the evidence: the viewer drew a frame and signalled it, the replay advances turn 2 → 171 → final, and the rendered frame reconciles exactly with the recorded results (endcard, scorebug, eliminations, ranks — verified against `results` above). No definition-of-done item names the hash chain; hash parity is a design claim (`design.md` §Tests: re-stepping from plan records "reproduces every recorded gameHash"), and `#mmwarn` is the starter's **designed** degrade surface (design.md line 1368; degrade-never-hang is a SPEC design pin). What the banner proves is that the wasm re-simulation is not bit-identical to the hosted episode in production even though CI's parity tests pass — an environment-dependent determinism bug that falsifies a design claim and degrades the mid-game board's authority. That is a genuine defect for a follow-up fix (and it is systematic: both hosted replays show it), but it does not falsify item 8's text, and "loaded, advancing, judged from what it drew" is exactly what happened. Settled by: reproducing the hosted replay bytes against the shipped wasm viewer locally, finding the first `mismatchTick`, and diffing sim state there.

**(2) Banner overlaps the endcard `GAME OVER` line and clips the fog-lens chips — NOT blocking.**
Item 8(c)'s bar is "legible, and it shows the game". I read the frame myself: the collision is real (the banner is itself clipped and sits over the small `GAME OVER` caption and the chip row's top edge) but every load-bearing readout — scorebug plates, endcard title/table, transport, scrubber, momentum graph — is fully legible. This is a layout blemish at one busy moment, the kind of legibility finding phase 30 exists for, not a failed render. Settled by: a z-index/offset fix moving `#mmwarn` out of the scorebug/endcard band.

**(3) Feed cards stack overlapping on the round-2 probe frame — NOT blocking.**
No definition-of-done item names the feed; item 8's measured signals (loaded, scrub clocks) and judgment paragraph don't depend on it, and the probe shows the feed *does* render and quotes the commander's reasoning — overlapping card layout is a polish defect. `feed_lines:0` in the JSON was sampled at the first drawn frame, before any event exists, so it carries no signal either way. Settled by: a stacking/expiry fix for `.feed` cards, verified by a re-dispatch of viewer-check.

**(4) `canvas_text: 0 drawn` — NOT blocking, not a defect.**
The instrument counts canvas-drawn text; this viewer renders all chrome text as DOM (which is how the smoke tool could read `#clock` and the scorebug at all). Zero is the expected reading — "not applicable", not "nothing drawn". Nothing to fix.

## Verifier report audit

| claim in VERIFY.md | I verified | agrees |
|---|---|---|
| rounds 2+3 completed, round 1 failed w/ that exact error | fresh fetch (now 2,3,4 completed) + round-1 detail | yes |
| leaderboard: 2 rows, champions only | fresh fetch | yes (now `rounds_played:3`) |
| ereq_c07776fa completed + replay_url + participants | fresh fetch | yes, byte-identical |
| COWLDGEN bytes → summary: protocol/reason/plans/fallbacks | re-ran `replay_summary.py` @ e8be315f on re-fetched bytes | yes, every number |
| logs CLEAN both rounds | re-fetched round-3 log, grepped raw + read game container | yes |
| SSR playlist + session → static route, ready:true | reproduced both calls | yes (featured now round 4) |
| `Replay liveness: skipped (static replay bundle declared` | read committed release-result.json | yes, verbatim |
| viewer-check run 33155441744 success, loaded:true, 3 differing clocks | `gh run view` + committed json + viewed both pngs | yes |
| screenshot description & reconciliation with results | viewed viewer-smoke.png and probe-round2 png myself | yes — accurate, nothing overclaimed |

## Non-blocking observations (for the close/learnings)

- The hash-mismatch determinism bug (observation 1) is the one item I would want tracked to an actual fix, with the banner-overlap (2) and feed-stacking (3) riding along in the same viewer pass.
- Round 3 seated `crown` in both filler seats (round-robin drew the same filler twice) — scheduler behaviour, already recorded by the verifier, no action.
- log.md's filler-registration line (08:12:40Z) postdates round 2's completion (08:06:14Z) even though round 2 demonstrably seated fillers — the log line was appended late. Harmless here (rounds 3 and 4 settle item 1 regardless), but worth logging registration timestamps at call time.

BLOCKING: 0
