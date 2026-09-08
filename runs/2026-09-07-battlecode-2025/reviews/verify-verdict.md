blocking: 0

# Phase-60 verdict — battlecode-2025
Head evidence: `runs/2026-09-07-battlecode-2025/VERIFY.md` (2026-09-08T05:47Z) adjudicated against
SPEC.md §Definition of done and `prompts/60-verify.md`. Independent read of the committed evidence
(viewer-check/, release-result.json, STATE.json, log.md, design.md) and adversarial spot-checks of
the cited URLs/APIs were done **before** accepting any VERIFY.md verdict. Fixer/verifier
self-report was treated as claims to be checked, not summary.

Spot-checks I ran myself (fresh fetches, 2026-09-08):
- Replay bytes from the cited S3 URL: HTTP 200, 97355 bytes, `jq -e` strict-parses;
  `protocol=cogame.battlecode.v1`, `.result.reason=complete`, `year=bc25`, `game_version=GV08`;
  0 `fallback` events, both `seats[].fallback` null, both seats `policy:"llm"`; event-kind
  histogram identical to VERIFY.md's (113 events); `result.wins=[2,0]`,
  `scores=[465.5,33.5]`, `points=[[55,76],[44,23]]`, two games both `more_squares_painted`
  at round 2000; per-seat sheets exactly as pasted (paint_eco/70-15-15/srp 70/ruin 16 vs
  tower_rush/35-20-45/srp 15/ruin 7).
- `POST /coworlds/replays/session` for this cow_id + replay: returns the **same** static
  `viewer_url` VERIFY.md pasted (`…/replays/static/cow_e58e703d…/sha256%3A28e952e1…/index.html?v=2#replay=…`),
  `ready:true`. Not a `/client/replay` pod URL.
- `https://softmax.com/battlecode/bc25`: HTTP 200, no `<iframe` in raw HTML (client-rendered,
  as VERIFY.md and the playbook state); the SSR payload contains this run's league id
  `league_7edecd14-…` and the **only** replay URL in the page is this run's round-2 replay
  `a0418bda-…` — featured match present and it is this run's.
- `gh run view 34191692693`: `viewer-check`, `completed`/`success`, created 2026-09-08T05:43:04Z —
  matching the dispatch instant VERIFY.md logged.
- `runs/…/release-result.json` (committed): `.certify.replay_liveness` =
  `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)`.
- `runs/…/viewer-check/viewer-smoke.{json,png}` (committed): read directly; the png was viewed and
  matches the verifier's spectator paragraph in every detail cited (see check 8).
- Run facts cross-checked against STATE.json and the coordinator brief: cow id, version 0.5.0,
  league/division ids, champions, fillers, replay URL, viewer-check run id — all agree.

## Per-check adjudication

### 1. ≥2 completed rounds after fillers — TRUE (stands), with one narrative flaw (non-blocking)
The rounds fetch is real evidence: rounds 1 and 2 both `"completed"`, `error: null`, zero
failed/discarded; a pending-state intermediate poll is on the record. STATE.verify.rounds lists the
same two round ids.
**Flaw found (adversarial read):** VERIFY.md says "the filler policies were registered at
2026-09-08T05:23:47Z per log.md … round 1 … was still pending when the fillers landed". Taken
literally that is self-contradictory: round 1 *completed* at 05:23:46.749995Z, one second **before**
05:23:47Z. But 05:23:47Z is the **batch log-write timestamp** of log.md's phase-50 line, which
records the action sequence `champion1 submit … champion2 submit … fillers 200 … unpause 200 …
trigger 200 … round 1 pending` — fillers precede the unpause and the trigger in the recorded order,
and round 1 (created 05:22:44Z, i.e. during that batch, after the fillers step) is the first round
that ever existed in this league. The prompt's own rule is "log.md records it", and the log's
ordering does establish fillers-before-round-1. The check's substance survives; the verifier's
gloss of the log timestamp as the registration instant is wrong and should not be repeated.
Non-blocking: conclusion correct, evidence (log ordering + only-two-rounds-exist) sufficient.

### 2. Both champions ranked — TRUE (stands)
Two leaderboard fetches pasted verbatim (05:25:38Z rounds_played=1, 05:41:43Z rounds_played=2 —
a consistent progression, not a stale paste). `daveey` rank 1 `battlecode-bc25-coverage:v1`,
`daveey-1` rank 2 `battlecode-bc25-siege:v1`, both `rounds_played: 2` ≥ 1; exactly two rows, no
filler rows — the "fillers absent" branch. Real fetch, satisfies the letter.

### 3. Latest round's episode request — TRUE (stands)
The flat `?round_id=` route 405s on this deployment (documented in the playbook §9); the nested
`/rounds/<id>/episode-requests` route used instead is a documented equivalent, not an inference.
`ereq_30eabb74-…` `completed`, non-null `replay_url` (= the S3 URL I fetched), participants name
`daveey`/`battlecode-bc25-coverage` v1 and `daveey-1`/`battlecode-bc25-siege` v1 with the STATE
policy_version ids, both `is_filler: false`; no filler seats needed for a 2-seat game with two
ranked players. Scores non-degenerate. Satisfies the letter.

### 4. Replay bytes valid and show the game — TRUE (stands; independently re-verified)
Every claim re-fetched and confirmed by me (see spot-checks). The `result` (singular) vs SPEC's
`results` key is declared in design.md line ~1170 (`"result":{ /* identical to COGAME_RESULTS_URI */ }`)
— a documented schema fact, not a dodge. Protocol matches the manifest via docs/PROTOCOL.md line 1
and the manifest's bc25 variant row (pasted; plausible and consistent with the replay's
`year=bc25`/`GV08`). The game's decision unit is the one-shot doctrine turn (design §Match shape);
2/2 decisions answered on attempt 1, `defaults_applied: 0`, 0 fallback events, `seats[].fallback`
null — "not all fallbacks" is satisfied at 0 of 2, and the sheets are non-default, mutually
distinct, and differ from round 1's (fresh generation, not canned).
**Best-of-three clinch note adjudicated:** 2 games with `gamesPerMatch=3` is the early-majority
break in `match.nim` (`winsNeeded(3)=2`, `wins=[2,0]`, loop breaks with `epComplete`) — quoted
from the repo, not inferred. `.result.reason == "complete"` is the primary branch of the check's
letter; no `deadline` exception is invoked, so nothing hangs on the design declaring one. Does not
falsify check 4.

### 5. Hosted game log clean — TRUE (stands)
The **full decoded body** is pasted (1725 bytes, both containers), which is stronger evidence than
a bare `CLEAN` echo: I grepped the pasted body myself — zero matches for
`falling back|LLM provider is unavailable|cut off at max_tokens|rejected`. Both LLM calls returned
200; no capacity exception claimed. The `refused a seat-0 connection: … wrong connection token`
line contains none of the four patterns, the real seat 0 connects and registers on the next lines,
and the episode completed — correctly filed as an observation, not a failure. Round-1 log also
checked per VERIFY.md. Satisfies the letter.

### 6. Public page uses the static replay path — TRUE (stands), documented deviation accepted
This is the check where the letter ("https://softmax.com/<slug>", "?replay=") and the deployment
diverge, and the verifier handled it the way the prompt and playbook prescribe rather than
asserting: (a) raw-HTML grep attempted first, found nothing, correctly recorded as *unknown*
(client-rendered — playbook: the grep "finds nothing for any coworld" since the lighthouse run);
(b) coworld detail API fetched, `featured_match: null` — the documented platform-wide behaviour,
recorded, not hidden; (c) the SSR payload `state.playlist[0]` — the playbook's stated source for
the featured match — shows this run's league id and this run's round-2 replay as the featured
match (I re-fetched the page and confirmed both strings are in the HTML today); (d) the iframe
`src` from `POST /coworlds/replays/session` — "the call the page's own JS makes" per the playbook —
returns the static route with the coworld's `manifest_sha` (= STATE.coworld.manifest_sha) and
`ready: true` (I re-ran the POST; identical answer). The `?v=2#replay=` fragment form is the
documented post-2026-08-28 shape of the same static route (playbook §Featured match, quoted
verbatim in my read). Not a `/client/replay` pod URL. The bc25-vs-/battlecode deviation is proven,
not asserted (the default page's SSR shows a different league id and a different replay). Crucially,
check 8 then **executed this exact URL** in a real browser and it rendered this replay — the
residual inference ("the page's iframe will carry what the session call returns") is the
playbook-documented mechanism plus a live execution of its output. No false negative, nothing
asserted-not-fetched. Satisfies the substance of the letter under a recorded deviation.

### 7. Certification declared the static bundle — TRUE (stands; re-read myself)
Read from the committed `release-result.json` (source stated; `/tmp` not consulted). I ran the jq
myself: `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not
required)` — contains the required string verbatim. Satisfies the letter.

### 8. Viewer executed and judged — TRUE (stands; artifacts inspected directly)
- Dispatch is real: run 34191692693, created at the dispatch instant, `success` (I re-checked via
  `gh run view`); found by createdAt sort, not "latest". Artifacts committed under
  `runs/…/viewer-check/` as required (json 1994 B, png 446 KB, stdout, empty stderr).
- Gate (a) `loaded: true` — `viewer-smoke.json` shows `data_replay_loaded:"true"` **and** bridge
  `ready`; `data_replay_error: null`, `bridge_error: []`, `failure: null`. Verified in the file, not
  the report.
- Gate (b) three scrub clocks differ — `2:32 GAME 1 OF 2 — DEFAULTLARGE` / `1:23 GAME 2 OF 2 —
  LEAVEMEALONE` / `FINAL MATCH OVER`: three distinct readouts naming the replay's two maps in play
  order. The 15 s soak additionally advanced unattended (round 2 → 314 → 362), `page_errors: []`.
- Gate (c) the judgment paragraph — I viewed `viewer-smoke.png` myself. Every cited detail is in
  the picture: `ASH 41% … 13% BASIL`, `560 / 955 to win · 626 bare`, both clans with players and
  their replay mottoes, live points 76/23 (= `result.points` game 2, which I confirmed from the
  replay's own `game_end` event `points:[76,23]`), the endcard headline and `score 465.5 — 33.5`
  (= `result.scores`), doctrine cards whose numbers are the seats' sheets verbatim, the stat block,
  a feed whose 8 lines match the replay's late events line-for-line and round-for-round, and the
  full transport strip with momentum scrubber at `round 2000 / 2000`. Legible; shows this game;
  broadcast-shell chrome (transport strip, momentum scrubber, scorebug band, endcard) — not a
  gridlock-style rewrite. The corroborating r1 run (34190741103, round-1 replay, different maps
  FOSSIL/RAIN, also loaded with three differing clocks) strengthens rather than substitutes.
Satisfies all three prongs of the letter.

## The two advisory items and the clinch note — adjudicated
1. **bc26 nouns on the bc25 endcard** ("the alliance held · kings built 0/0 · cheese delivered
   0/0 · cats damaged 0/0") — confirmed present in the png. It is one wrong-vocabulary caption line
   on an otherwise correct, correct-year endcard; the frame remains legible and shows the game, so
   it does not falsify check 8 (whose gate is load + advance + legible judgment) nor any
   Definition-of-done line. Correctly filed as phase-30 item-14 legibility residue. Advisory.
2. **Doctrine cards clip their last line without ellipsis** — confirmed in the png (both cards end
   mid-sentence at the card edge). DOM text, so the canvas-text detector's `0 ellipsized` is not a
   contradiction. A polish defect, not a rendering failure; no check or DoD line requires unclipped
   prose cards. Advisory.
3. **Best-of-three clinch (2 games, not 3)** — code-documented early-majority exit with
   `reason=complete`; the replay, the manifest (`gamesPerMatch: 3`), and `match.nim` reconcile.
   Falsifies nothing.

## Non-blocking observations (for the record, no checklist item attached)
- VERIFY.md check 1's timestamp narrative conflates the phase-50 batch log-write time (05:23:47Z)
  with the filler-registration instant; as written it contradicts round 1's completed_at
  (05:23:46.75Z). The correct evidence is log.md's recorded action ordering (fillers → unpause →
  trigger → round 1), which does establish the requirement. Wording should not be copied forward.
- The hosted log's bedrock-sidecar container shows `POST https://openrouter.ai/api/v1/messages`
  while the game log says `bedrock transport` — both calls 200, no forbidden strings; platform
  plumbing, noted only for the record.
- `viewer-smoke.json` scrub 0% clock (`2:32`) differs from soak `before` (`2:47`) — the scrub pass
  runs after the soak; consistent, not a contradiction.

## Verdict
All eight checks are established by fetched (or, for check 8, executed) evidence; the two flagged
advisory items and the clinch note are residue, not falsifiers. Nothing was asserted-not-fetched:
the one place the letter could not be followed verbatim (check 6) is a recorded, playbook-sanctioned
deviation whose output was then executed live. Zero blocking findings.

BLOCKING: 0
