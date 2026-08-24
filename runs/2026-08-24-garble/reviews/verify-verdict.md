blocking: 0

# Phase-60 verdict — garble
Head: 953d35e83375e976b687a0526d9daa55fc18c1d0   Checklist: docs/SPEC.md §Definition of done (phase 60, all fetched, never assumed) — 8 items
Independent read written before reading VERIFY.md: yes. I fetched every item's evidence myself
(observatory API, S3 replay bytes, hosted log, softmax.com page + session route, committed
release-result.json, committed viewer-smoke.{json,png}, `gh` for the CI run and the cited source
lines) before opening VERIFY.md. All timestamps below are my own re-fetches on 2026-08-24 unless
marked "VERIFY.md".

## Item-by-item ruling

### 1. ≥2 completed rounds after fillers were set — TRUE
- My fetch of `GET /rounds?league_id=league_4eb352ae-…`: rounds 1/2/3 `status:"completed"`,
  `error:null` (completed 08:58:13Z, 09:16:07Z, 09:31:06Z); round 4 `pending`. None failed/discarded.
- Rounds 2 and 3 are substantive: `ereq_f12e854e…` and `ereq_00f32fd9…` both `completed` with
  non-null `replay_url` and five `participant_scores` each (my fetch).
- "After the fillers were set": round 1's own episode request (`ereq_79eb44a8…`, created
  08:58:02Z) already seats `garble-quoter` ×3 with `is_filler:true` (my fetch) — filler
  registration preceded every round; rounds 2 and 3 trivially post-date it.
- VERIFY.md's pasted rounds list, poll table, filler-policies fetch and r1-participants fetch all
  match my re-fetches byte-for-byte on the material fields.

### 2. Both champions ranked, fillers absent/Baseline — TRUE
- My fetch of `GET /divisions/div_6540c330-…/leaderboard`: exactly 2 rows —
  rank 1 `daveey-1` / `garble-shortwave:v1` / Elo 1016.0 / rounds_played 2 / episode_wins 1.0;
  rank 2 `daveey` / `garble-signal:v1` / Elo 984.0 / rounds_played 2. Both `rounds_played ≥ 1`.
  Neither `garble-quoter` nor `garble-shark` appears — fillers absent, the permitted outcome.
- Matches VERIFY.md's pasted rows exactly.

### 3. Latest round's episode request completed with replay; participants named correctly — TRUE
- My fetch: latest completed round is round 3 (`round_16088d65…`); its
  `ereq_00f32fd9-cab8-456f-bd8c-8037f601dec0` is `status:"completed"`,
  `replay_url: https://softmax-public.s3.amazonaws.com/replays/f062ea29-….replay`,
  participants: seat 0 `garble-signal`/`daveey` (is_filler false), seat 1
  `garble-shortwave`/`daveey-1` (is_filler false), seats 2–4 the registered fillers
  (is_filler true); five participant_scores. Matches VERIFY.md exactly.

### 4. Replay bytes valid, protocol match, reason complete, champions non-scripted — TRUE
- I fetched the S3 bytes myself (31 266 bytes): strict `utf-8` decode + `json.loads` pass;
  `protocol: "garble.replay.v1"`; `results.reason: "complete"`; `results.names` =
  `["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)"]` (policy names, fillers
  Baseline-labelled); 112 events (`say=60 confirm=19 void=16 turn=12 deal=3 start=1 end=1`).
- Champion seats doing the thing the game is about: seats 0 and 1 have **12/12 and 12/12
  non-scripted says** (0 fallbacks out of 24), with substantive texts and notes — e.g. seat 0 t02
  `SELL 4 4 TAR TAR AT 13 13` with notes "At 95% interference (STORM peak), using full repetition
  format…", seat 1 t06 notes "Confirmed #29 (Rivet SELL 5 TAR AT 16): said once, clean…". Both
  channel modes used (radio `-1` and private lines). Not scripted, not trivial, not fallbacks.
- Protocol "matches": the platform manifest declares no replay-protocol string (I verified
  `garble.replay.v1` is absent from the fetched manifest — protocols there are player/global);
  the declared source is the design note (design.md §Replay payload, `"protocol":"garble.replay.v1"`)
  and the shipped code. I verified VERIFY.md's two code citations via `gh`:
  `src/garble/server.nim:607` — `"protocol": payload{"protocol"}.getStr("garble.replay.v1")` —
  and `replay-viewer/garble_replay.nim:46` — same literal. The fetched bytes carry exactly that id.
- VERIFY.md's stated jq adaptation (`kind`/`scripted` instead of the prompt's `type`/`fallback`)
  is correct and declared; its numbers match mine exactly.

### 5. Hosted game log clean — TRUE
- I fetched `GET /episode-requests/ereq_00f32fd9…/artifacts/logs` with
  `X-Use-Elevated-Privileges: true` myself: 57 836 bytes (matches VERIFY.md's byte count).
  `grep -E 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected'` → **0
  matches** on the raw bytes. VERIFY.md additionally decoded the `b'…'` reprs and grepped the
  decoded text (also 0) — stronger than required.
- I verified the excerpts VERIFY.md quotes are really in the log: `garble llm: seat 0 attempt 0
  failed: input(7, 1) Error: EOF expected` (turn 2; the seat still transmitted an LLM line that
  turn — a recovered retry, matching item 4's zero fallbacks), all 12 turn lines (episode done in
  ~140 s of the 720 s budget), four containers, five `Dropped message to disconnected client`
  teardown lines. Honest reporting, correctly not counted against the four patterns.

### 6. Public page uses the static replay path; featured match present — TRUE
- My fetch of `https://softmax.com/garble` raw HTML: no `<iframe` (client-rendered, the documented
  platform behaviour) — but the SSR payload contains `state.playlist[0]` = episode
  `53b8371a…`, `code "garble.r3.e1"`, `replayUrl` = the round-3 replay, matchup naming daveey-1
  (rank 1) and daveey (rank 2). Featured match present.
- My own `POST /coworlds/replays/session` for that cow_id + replay_uri returned
  `viewer_url: …/v2/coworlds/replays/static/cow_cb2293f4-…/sha256%3A41c6b5f1…/index.html?replay=<s3 url>&v=2`,
  `ready: true`. The `<sha>` equals the coworld's `manifest_hash` (my fetch of
  `GET /coworlds/cow_cb2293f4-…`: `sha256:41c6b5f1c725f042aa93bf56748e906b5218fede82b16156c18010549321a012`).
  **No `/client/replay` pod URL.** VERIFY.md names all three sources it used, as the prompt requires.

### 7. Certification declared the static bundle — TRUE
- I read the committed `runs/2026-08-24-garble/release-result.json` myself:
  `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared;
  /client/replay and /replay not required)` — contains the required string exactly;
  `.certify.ok` true; the output_tail shows all 10 certification steps `[pass]`.
  VERIFY.md read the committed copy, not `/tmp`, as required.

### 8. Viewer executed; loaded, advances, judged — TRUE
- **Execution is real:** I verified run 32712220489 via `gh run view`:
  `{"status":"completed","conclusion":"success"}`, workflow `viewer-check`, created
  2026-08-24T09:33:48Z — after the dispatch time VERIFY.md records (09:33:46Z), so the
  find-the-new-run selection was sound. Evidence is committed at
  `runs/2026-08-24-garble/viewer-check/` (commit 3b5eb6d), and the smoke URL inside
  `viewer-smoke.json` is exactly the item-6 iframe src.
- **(a) loaded:** `viewer-smoke.json` — `loaded: true`, `data_replay_loaded: "true"`,
  `bridge: ["loading","ready"]`, `bridge_ready: true`, `data_replay_error: null`,
  `failure: null`. Holds.
- **(b) advances:** the three recorded scrub readouts are pairwise distinct strings —
  `TURN 1 / 12 · HAZY 30%` / `TURN 1 / 12 · HAZY 30% · WAITING ON 5` / `FINAL — DAVEEY-1 1.10×`.
  Ruling below (verifier note 2). Holds.
- **(c) judgment paragraph:** present, legible, and accurate. I inspected
  `viewer-smoke.png` myself: it is a fully-drawn final frame — GARBLE wordmark, scorebug strip
  (`daveey 380 … daveey-1 397 … Gasket 480 … Rivet 409 … Sproc… 380`), the interference meter with
  `STATIC BURST` / `50% ROUGH`, five distinct cog sprites with `RADIO`/`LEADS` chips, the
  SAID-vs-HEARD panel with red garble blocks and a `TICKET #60` badge, the three-line deal tape
  (`#4 Rivet sold 5 TAR to Gasket at 15`, `#29 … at 16`, `#34 … (partial 2/5)`), the price strip
  `ORE 13 ▼ OAT 17 ▲ TIN 12 ▲ TAR 13 =`, transport strip with colour-ticked scrubber at
  `112 / 112` and the `♪ STATIC` toggle, and the endcard `FINAL — 12 TURNS / DAVEEY-1 LEADS THE
  TABLE` with the five ranked rows. I reconciled every number in that frame against the replay
  bytes I fetched: endcard scores/credits/deals/misheard/airtime = `results.scores`
  `[1.00,1.10,1.04,1.08,1.00]`, `portfolio [380,397,480,409,380]`, `deals [0,2,1,3,0]`,
  `misheard [0,0,0,0,0]`, `airtimeUsed [378,509,335,392,335]` row for row; the tape lines are the
  replay's three `deal` events (tickets 4/29/34, fill 2/5 partial on #34); 112/112 matches the
  event count. Picture and record agree. The chrome is the babel-lineage shell (transport strip,
  scrubber, scorebug, feed toggle, endcard), not a gridlock-style rewrite.

## Ruling on the two verifier notes

**Note 1 — hollow round 1 vs item 1's "≥2 completed rounds": SATISFIED.**
Round 1 (`ereq_79eb44a8…`) is verifiably hollow — I confirmed `completed_at` 7 s after
`created_at`, `replay_url: null`, `participant_scores: []`, `episode_id: null`. Its round status
is nonetheless `completed` (not `failed`/`discarded`), so even the literal count is 3. The
verifier did the right thing twice over: it disclosed the hollowness verbatim (including the
three artifact 404s) instead of hiding it, and it rested the verdict on rounds 2 and 3, which I
independently confirmed are real — both completed, both with S3 replays, both scored, both
seated after filler registration (fillers already appear as participants in round 1, created
08:58:02Z). Two substantive completed rounds exist; the checklist item holds on the strict
reading without needing round 1 at all. The hollow round is a platform-side anomaly worth the
coordinator's note it got; it is not a defect in this coworld and not a blocking finding.

**Note 2 — 50 % scrub readout vs SPEC item 8(b): SATISFIED.**
SPEC 8(b)'s operative sentence is: "the clock text differs across the three scrub readouts
(0 %, 50 %, 100 %) recorded in viewer-smoke.json. A frame that renders once and freezes is a
failure." The three recorded strings are pairwise distinct — the 50 % readout carries the
`· WAITING ON 5` suffix the 0 % readout lacks, and the 100 % readout is `FINAL — DAVEEY-1 1.10×`.
The letter of the item holds. So does its purpose (anti-freeze): the 100 % state is the episode's
end, and the load-time scorebug in viewer-smoke.json (all seats `300 CREDITS 1.00×`) versus the
screenshot's final scorebug (`380/397/480/409/380`, ratios to `1.10×`) proves the board moved
through the whole episode — a frozen viewer produces identical strings at every position and an
unchanged scorebug. The residual oddity — 50 % of 112 events should sit around turn 5–6, not
`TURN 1` — is real (I reconciled it against the replay myself) and means the mid-bar seek either
re-animates from the head or needs more than the harness's settle time; that is a
legibility/harness question for a phase-30 pass, exactly as the verifier filed it, not evidence
of a frozen viewer and not a failure of the item as written. Marking item 8 TRUE with the note
disclosed was the correct call.

## Verifier report audit

| item | verifier said | I verified | agrees |
|---|---|---|---|
| 1 | 3 completed, r1 hollow, fillers pre-r1 | same, own fetches (rounds, ereqs, r1 participants) | yes |
| 2 | 2 rows, both champions, rp=2, fillers absent | same leaderboard bytes | yes |
| 3 | ereq_00f32fd9 completed + replay + correct participants | same | yes |
| 4 | utf-8 JSON, garble.replay.v1, complete, 0/24 champion fallbacks | same from my own S3 fetch; code citations confirmed via gh | yes |
| 5 | CLEAN, 57 836 bytes, one recovered retry disclosed | 0 grep matches on my own fetch; quoted lines present | yes |
| 6 | client-rendered page; playlist[0]=garble.r3.e1; session→static URL ready:true | same from my own page fetch + session POST; sha = manifest_hash | yes |
| 7 | committed release-result.json contains the string | read the committed file myself | yes |
| 8 | run 32712220489 success; loaded:true; 3 differing readouts; judgment paragraph | gh run view success; json/png inspected and reconciled myself | yes |

Every pasted block in VERIFY.md is genuine fetched output (command + response); nothing was
asserted without evidence, the two prompt deviations (jq field adaptation in item 4, log
decoding in item 5) are declared, and the two anomalies were disclosed rather than smoothed over.

## Non-blocking observations
- The 50 % scrub sample under-reports (TURN 1 at mid-bar) — mid-seek re-animation or settle time
  in the harness; a future phase-30 legibility item, per the ruling above.
- Round 1's hollow completion (7 s, no episode, artifact 404s) is a platform-side scheduling
  artifact; it cost nothing here but is worth the learnings entry the verifier flagged.
- Trivia: VERIFY.md records the page at 487 445 bytes; my later fetch got 487 639 — SSR payload
  drift between fetches (round 4 now pending), not a discrepancy in evidence.

## Checklist pass (independent)
| item | status | evidence |
|---|---|---|
| 1 ≥2 completed rounds after fillers | TRUE | my fetch: rounds 2 & 3 completed+scored; fillers seated in r1 ereq (created 08:58:02Z) |
| 2 both champions ranked | TRUE | my fetch: daveey-1 1016 rp=2 / daveey 984 rp=2; fillers absent |
| 3 latest round ereq + replay + participants | TRUE | my fetch: ereq_00f32fd9 completed, replay f062ea29, seats 0/1 champions |
| 4 replay bytes valid + show the game | TRUE | my S3 fetch: strict JSON, garble.replay.v1, complete, 24/24 champion says non-scripted |
| 5 hosted log clean | TRUE | my elevated fetch: 0 matches of the four patterns |
| 6 static replay path + featured match | TRUE | my page fetch (playlist[0]) + my session POST (static URL, ready:true) |
| 7 cert declared static bundle | TRUE | committed release-result.json, `.certify.replay_liveness` |
| 8 viewer executed, advances, judged | TRUE | run 32712220489 success (gh); committed json/png inspected + reconciled |

BLOCKING: 0
