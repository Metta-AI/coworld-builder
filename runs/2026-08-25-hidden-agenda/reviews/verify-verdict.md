blocking: 0

# verify verdict — hidden-agenda (phase 60, fresh-context adjudication)

Head: e4460277870e2677e9401c080ca233352abef7ad   Checklist: docs/SPEC.md §Definition of done (as commands: prompts/60-verify.md)
Independent read written before reading fixer reports: yes — I read SPEC, the prompt, VERIFY.md, and the committed
viewer-check artifacts, then re-fetched every fetchable claim myself. I did not read `reviews/verify-r1-fixes.md`
or the r1 review/verdict at any point; this verdict is against VERIFY.md and the live platform only.

Object under adjudication: `runs/2026-08-25-hidden-agenda/VERIFY.md` (2026-08-26T05:30Z, attempt 2), against
version **0.1.2** / **cow_962d0488-144c-48f6-b0c7-08a19ac5ed89**, league `league_9c44cf05-…`, division
`div_cb85265c-…`. Every check below was re-fetched by me on 2026-08-26 (post-05:37Z) unless noted.

## Standing blocking findings

None.

## Refuted

None to refute — VERIFY.md's evidence survived every re-fetch I made. No claim in it was found asserted-without-
evidence, stale against the superseded 0.1.0 `cow_87de5e19` / 0.1.1 `cow_6f563cd4`, internally inconsistent, or
wrongly interpreted. The one place staleness *could* hide — evidence quietly carried over from attempt 1 or from
pre-reseat rounds 2–6 — is explicitly fenced: VERIFY relies only on rounds 7/8/9 for checks 3/4/5, and I confirmed
rounds 7/8/9 carry the v3 champion version ids (`de6e647d` sleuth, `cc10827d` shadow) in `entrant_attributions`
while round 6 carries the v1 ids (`7fcd857a`, `d5e5ead8`) — the cut-over line is real.

## Checklist pass (independent, item by item)

| # | definition-of-done item | status | evidence |
|---|---|---|---|
| 1 | ≥2 rounds completed after fillers set | **TRUE** | My fetch of `GET /rounds?league_id=$L`: rounds 2–9 all `completed`, round 1 `failed` (`Temporal RoundWorkflow failed before settling the round.` — the documented pre-filler round), round 10 now `pending`→completed. 8 completed ≥ 2. Under the stricter fresh-canonical reading, **3** rounds (7, 8, 9) completed after the v3 re-seat. Fillers live on the league are v3 (`GET /leagues/$L/filler-policies`, elevated: miner v3 `59a3061c`, lurker v3 `cd5bf260`), distinct from champion uuids; the same two ids are embedded in round 9's `round_config` (`filler_policy_version_ids":["59a3061c-…","cd5bf260-…"]` — I grepped the round record and found it nested, as VERIFY claimed). |
| 2 | both champions ranked, fillers absent/Baseline | **TRUE** | My leaderboard fetch matched VERIFY **byte for byte**: rank 1 `daveey-1` `hidden-agenda-shadow:v3` 1022.226… rounds_played 8; rank 2 `daveey` `hidden-agenda-sleuth:v3` 1017.749… rounds_played 8. No filler row at all. Ranks 3–4 (`richard`, `relh`) are third-party public-league entrants, not fillers. `GET /policy-versions` confirms sleuth v3 `de6e647d` is owned by `daveey` and shadow v3 `cc10827d` by `daveey-1`. |
| 3 | latest round's ereq completed w/ replay, participants correct | **TRUE** | My fetch: round 9 → `ereq_50c013dc-2b01-41bd-90df-25c3edfd0eb8`, `status:"completed"`, `replay_url` = s3 `2e2bca77-…`, participants: position 1 `hidden-agenda-sleuth` v3 `daveey` `is_filler:false`, position 2 `hidden-agenda-shadow` v3 `daveey-1` `is_filler:false`, position 4 `hidden-agenda-lurker` v3 `is_filler:true`. Identical to VERIFY. (The filler is flagged `is_filler:true` rather than renamed `Baseline (N)` in this payload; spectator-side the replay's `results.names[4]=="Baseline"` — the intent of the check is met; see observations.) |
| 4 | replay bytes valid, champions really deciding | **TRUE** | I fetched all three replays. Round 9: http 200, 232825 bytes, `jq -e` strict parse ok, `protocol` `hidden_agenda.replay.v1` (matches design.md's manifest, which I read at lines ~912/927), `results.reason:"complete"`, ending `impostor_ejected`. My own seat/source aggregation reproduces VERIFY's table exactly: r9 champions 14/14 `llm`; r7 10/10 `llm`+`retry`; r8 8 `llm` + 9 `fallback` of 17. 41 champion orders, 32 real = 78.0%; latest round 100%. Final eject `{"target":"YELLOW","tally":{"YELLOW":2,"skip":1},"wasImpostor":true}` — the champions caught the actual impostor. Quoted champion orders in VERIFY carry distinct, state-tracking `say`/`hunch` text with the fixed `at`/`who`/`room` sibling keys; commit `731ab43` ("fix(llm): honour the compact job form and spell the plan step's sibling keys", 2026-08-26T04:26:27Z, touches `src/hidden_agenda/llm.nim`) exists on `Metta-AI/cogame-hidden-agenda` — I fetched it via `gh api`. |
| 5 | hosted game log clean (or documented platform-wide cause) | **TRUE** | I re-fetched all three logs with the elevated header; byte counts matched VERIFY exactly (3872 / 24449 / 49693). My greps: round 9 **zero** hits and **zero** failed attempts; round 7 zero grep hits, one `attempt 1 failed: llm throttled (429)` absorbed by retry; round 8 **9× `falling back`**, 18 failed attempts **all** `llm throttled (429)`, **zero** parse-reject markers (`unknown job|needs at: one of|needs both` → 0 in all three). Cross-check re-fetched: coins coworld `ereq_1e00588b-…` (`cow_e5c32ad5-…`), `created_at` 2026-08-26T05:08:37Z — the same minute round 8 ran — with **44** `Too many tokens per day` events / **66** `429` occurrences. The round-8 exception is exactly SPEC item 5's "documented platform-wide cause checked against another LLM coworld", and the latest round's log is CLEAN outright. |
| 6 | public page uses static replay path, featured match present | **TRUE** | Raw-HTML iframe grep finds nothing (client-rendered — the documented fallback applies, and VERIFY said which source it used). My fetch of the SSR payload: `state.playlist[0]` present, now `hidden_agenda.r10.e1` on `coworldId` **`cow_962d0488-…`** / `coworldVersion` 0.1.2 (the featured match rolled forward from VERIFY's r9 snapshot — same canonical coworld, so VERIFY's snapshot was true then and the state still passes). My `POST /coworlds/replays/session` for cow_962d0488 + the r9 replay returned `ready:true` and `viewer_url` = `…/v2/coworlds/replays/static/cow_962d0488-…/sha256%3A9b4d9731…/index.html?replay=…` — byte-identical to VERIFY's, the sha URL-decodes to the `manifest_hash` my `/coworlds` fetch returned, and 0.1.0/0.1.1 both read `canonical:false`. No `/client/replay` anywhere. |
| 7 | certification declared static bundle (committed release-result.json) | **TRUE** | I read the committed `runs/2026-08-25-hidden-agenda/release-result.json` myself: `{"version":"0.1.2","cow_id":"cow_962d0488-…","manifest_sha":"sha256:9b4d9731…","canonical":true,"ok":true,"step_failed":null}` and `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)`. Release run `32931097733` on `Metta-AI/cogame-hidden-agenda`: `completed`/`success`, created 04:40:24Z — consistent with the 0.1.2 re-release timeline. |
| 8 | viewer executed; loaded, advances, judged | **TRUE** | CI fact checked: run `32934089374` (viewer-check, Metta-AI/coworld-builder) `completed`/`success`, created 05:27:08Z. Committed `viewer-check/viewer-smoke.json`: `loaded:true` @4210 ms via `data_replay_loaded:"true"`, `failure:null`, `url` byte-identical to the check-6 `viewer_url`, and three **differing** scrub clocks — `TICK 3 / 3000 DEPOSITS 0 / 32` → `TICK 795 / 3000 DEPOSITS 8 / 32` → `TICK 1557 / 3000 FINAL`, monotone in tick and deposits, final tick matching `results.ticks:1558`/the `end` event at t=1557. I looked at `viewer-smoke.png` myself: it is legible and it shows the game — scorebug `16 DEPOSITS · CREW · 16/32` / `TICK 1557/3000 FINAL` / `IMPOSTOR · CREW LEFT 2 · YELLOW · RICHARD`; endcard `CREW WIN — THE IMPOSTOR WAS EJECTED` with the rules line, the stat line `2 freezes · 0 witnessed · 1 ejection (right) · 0 fake deposits · 6 meetings` (equals `results` field for field), and the full role reveal (RED CREW relh / BLUE CREW daveey / GREEN CREW daveey-1 / YELLOW IMPOSTOR richard / PINK CREW Baseline); vote board `MEETING 6` with `BLUE → YELLOW`, `GREEN → YELLOW`, `RESOLVED` (= the tally `{"YELLOW":2,"skip":1}`); roster strip with YELLOW dimmed/struck; transport strip with spoilers toggle, `CREW WINS 1557 / 1557`, 1×–16× speed buttons; scrubber with meeting markers and the `RACE TO WIN` momentum band. It is recognisably the starter chrome family, not a gridlock-style rewrite. The judgment paragraph in VERIFY is written from this evidence and reconciles against the replay events; its claims check out. |

## Verifier report audit

| claim in VERIFY.md | I verified | agrees |
|---|---|---|
| 8 completed rounds (2–9), round 1 failed pre-filler | re-fetched `/rounds` | yes — identical rows, timestamps to the microsecond |
| rounds 7/8/9 carry v3 champion ids, round 6 carries v1 | re-fetched all four round records | yes |
| leaderboard rows (scores to full precision) | re-fetched | yes — byte-identical |
| ereq 50c013dc participants/scores | re-fetched | yes — identical |
| replay bytes 232825 / 367535 / 159044, strict-parse ok, `complete` ×3 | re-downloaded all three | yes |
| champion order/source table (r7 10/10, r8 8+9, r9 14/14) | recomputed with the same jq | yes — exact |
| logs: r9 CLEAN 3872 B, r7 CLEAN 24449 B, r8 9 hits 49693 B, 18×429, 0 parse rejects | re-fetched all three, elevated | yes — exact byte counts and counts |
| coins cross-check: 44 quota events / 66 429s, same minute | re-fetched coins ereq + logs | yes — 44 and 66, created 05:08:37Z |
| session POST → static viewer_url, ready:true | re-POSTed | yes — byte-identical URL |
| committed release-result.json is the 0.1.2 artifact with the liveness-skipped line | read the committed file | yes |
| viewer-check run 32934089374 green; artifacts committed | `gh run view` + read both files | yes |
| commit 731ab43 fixed the llm.nim schema hint | `gh api` the commit | yes — message and files match the narrative |

## Non-blocking observations

1. **Check 3, filler naming**: the participants payload shows the filler as `policy_name:"hidden-agenda-lurker"`,
   `player_name:"daveey"`, `is_filler:true` rather than the `Baseline (N)` display name the prompt's parenthetical
   describes. The spectator-side label is correct (`results.names[4]=="Baseline"` in the replay, `PINK CREW
   Baseline` on the rendered endcard), so the substance — champions named correctly, filler identified as such —
   holds. API display shape, not a defect.
2. **Round 8 in isolation** had a majority-fallback championship seat mix (9 of 17). The checklist's fallback bound
   is applied to the latest round's replay (14/14 real) and the cause of round 8's fallbacks is the verified
   platform-wide 429; VERIFY neither hid the bad round nor leaned on it. No action.
3. The featured match has rolled forward to r10 since VERIFY was written — still cow_962d0488 / 0.1.2 / static.
   Expected ladder behaviour, noted so nobody reads the r9 snapshot as stale.
4. `feed_lines: 0` in viewer-smoke.json vs a visible (dimmed) feed in the png — a smoke-harness selector mismatch,
   declared in VERIFY itself; not one of check 8's three criteria.

Everything in the definition of done was verifiable from VERIFY.md, the committed files, or my own re-fetch;
nothing had to be taken on assertion. Zero items blocking.

BLOCKING: 0
