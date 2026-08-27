blocking: 0

# phase-60 verdict — trick-taking

Judge with fresh context, 2026-08-27. Read order followed: SPEC §Definition of done →
`prompts/60-verify.md` → `runs/2026-08-26-trick-taking/VERIFY.md` → committed
`viewer-check/viewer-smoke.json` + `viewer-smoke.png` (viewed) → committed `release-result.json`
→ `design.md` (§2 degrade path, §Replay event table, §Replay bytes). Every check below was
re-derived from the pasted evidence and, where cheap, **re-fetched live in this session**
(rounds, leaderboard, episode request, replay bytes, hosted logs for r4/r2/fog-of-war-boards,
replay session URL, public page SSR payload, viewer-check run conclusion, coworld manifest).
No re-fetch contradicted VERIFY.md.

Head facts confirmed against STATE.json: cow_id `cow_0de16cf6-8d0f-4601-8ca7-1c60fc3544d0`,
version 0.1.0, manifest sha `sha256:51bc9a90…eabf1`, release run 33036293815.

---

## 1. ≥2 completed rounds after fillers set — TRUE

Re-fetched `GET /rounds?league_id=league_4764b49e…`: rounds 2 (created 03:40:17Z), 3
(03:55:17Z), 4 (04:10:18Z) all `completed`; round 5 now pending; round 1 `failed` with the
verbatim error `Temporal RoundWorkflow failed before settling the round.` — created 03:40:00.779Z,
failed 219 ms later, the documented pre-filler auto-fire race; it does not count and its error is
recorded, as the check requires.

One nit in VERIFY.md, immaterial: it says the filler POST was "issued at 03:40Z" while quoting
the log line stamped `2026-08-27T03:42:12Z` (phase-50 log lines 52–58 share one batch timestamp).
Whether fillers landed at 03:40Z or 03:42Z, **rounds 3 and 4 are unambiguously post-filler**,
which is ≥2 on its own; round 2's episode seated `Baseline` / `Baseline (2)`, only possible with
fillers set. Re-fetched `GET /leagues/$L/filler-policies`: `trick-taking-follow` v1
(`a23ccfa9…`) and `trick-taking-tracker` v1 (`e6d34146…`), matching the coordinator's ids and
neither a champion. **Standing: TRUE.**

## 2. Both champions ranked, fillers absent — TRUE

Re-fetched `GET /divisions/div_a46cc2cd…/leaderboard` (bare list): exactly two rows —
rank 1 `daveey-1` / `trick-taking-counter:v1` / rounds_played 3, rank 2 `daveey` /
`trick-taking-signaller:v1` / rounds_played 3. Both ≥1; the two filler policies are absent.
**TRUE.**

## 3. Latest round's episode request completed with a replay — TRUE

Re-fetched `GET /episode-requests/ereq_1485dd71-d828-4b16-ac94-8a306561520b` (round 4):
`status: "completed"`, `replay_url` non-null
(`…/replays/ec71e84c-f086-4198-907e-c24b27f3a317.replay`), seat 0 `daveey` /
`trick-taking-signaller` v1 and seat 1 `daveey-1` / `trick-taking-counter` v1 with
`is_filler: false`; seats 2–3 are the two registered fillers with `is_filler: true`. The
verifier's use of the nested `GET /rounds/$R/episode-requests` route after the flat route's 405
is a legitimate second approach, documented in VERIFY.md. **TRUE.**

## 4. Replay bytes valid and show the game — TRUE (schema-deviation ruling below)

Re-fetched the S3 bytes myself: http 200, 69818 bytes, `jq -e` strict parse ok, `protocol` =
`tricks.replay.v1`, `results.reason` = `complete` — the strongest of the design's declared enum
`complete|deadline|budget` (design.md §Results), no deadline exception needed. `handsScored: 8`
of 8. Protocol match: the manifest (fetched from `GET /coworlds/$COW`) carries the paired live
protocols (`tricks.player.v1` in `manifest.game.protocols.player`) and no separate
replay-protocol key; `tricks.replay.v1` is the protocol design.md §Replay declares for the bytes.
Consistent.

**Ruling on the event-schema deviation.** The prompt's jq filters (`.type=="decision"`,
`.fallback==true`) are illustrative commands for SPEC item 4's actual requirement: champion
seats doing the thing the game is about — non-scripted decisions with non-trivial content, not
all fallbacks, fallbacks a small minority. This coworld's replay language is `kind` + `scripted`
+ `results.fallbacks[]`, exactly as design.md §Replay event table (lines 653–664) and §Results
(line 734) declare — the deviation is from the prompt's example filters, not from the design.
I re-derived the equivalent counts from the fetched bytes, independently of the verifier's jq:

- Champion seats (slots 0, 1): 100 decision events (`bid|play|pass|discard`); **64 with
  `scripted: false`**, all 64 carrying substantive `text` (I read several: genuine euchre
  reasoning about bowers, voids, following suit, protecting a march — not boilerplate).
- The 36 scripted champion events decompose as **35 plays whose `legal` set has exactly one
  card** (forced moves — no decision exists to delegate to an LLM) and **1 genuine fallback**,
  matching the engine's own tally `results.fallbacks == [1,0,0,0]` (the §5 throttle event).
- Filler seats (slots 2, 3): 100 % `scripted: true`, as baselines must be.

Fallbacks are 1 of 100 champion decision events (1 of 65 free-choice decisions) — a small
minority by any reading. **The required properties are established. TRUE.**

## 5. Hosted game log — literal grep NOT CLEAN; ruling: the platform-capacity exception applies. TRUE

I re-fetched the round-4 hosted log myself (elevated header, 141650 bytes), decoded the
python-bytes container reprs, and re-ran the grep. Exactly the two lines VERIFY.md pasted, no
others; `LLM provider is unavailable`, `cut off at max_tokens` and `rejected` appear nowhere:

```
299: trick-taking llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
301: trick-taking llm: slot 0 falling back to a scripted decision
```

with the cause named between them: `llm throttled (429): {"message":"Too many tokens per day,
please wait before trying again."}`, and the sidecar log carrying the structured record:
`"status_code":429,"error_kind":"upstream_client","error_type":"ThrottlingException"` at
04:10:52Z, followed at 04:11:36Z by the Sonnet failover succeeding (`"ok":true,"status_code":200`).

**Ruling.** The exception clause exists to distinguish a **platform-wide shared-capacity
symptom** from a **defect in this coworld**. The prompt names `LLM provider is unavailable` as
*an example* of that symptom class ("a platform-wide Bedrock **capacity** symptom"); SPEC item 5
states the exception more generally: "or a documented platform-wide cause checked against
another LLM coworld." A Bedrock 429 `ThrottlingException` — "Too many tokens per day" — is a
**per-account daily token quota**, the one resource all parallel runs share (SPEC §Parallelism).
It is the same underlying event reported by a different layer's byte string; nothing about it is
attributable to this coworld's code, model id, prompt size or output cap. The three tests the
exception implies all pass on evidence I re-fetched myself:

1. **Platform-wide, contemporaneous:** `fog-of-war-boards`' hosted log
   (`ereq_d273ce15-8095-4400-b57e-b9df696ec399`, re-fetched, 26444 bytes) carries the identical
   `ThrottlingException` / "Too many tokens per day" / `unusable (throttled)` lines at
   04:00:17Z — a different coworld, same minute-scale window, same quota.
2. **Not persistent / not this coworld:** round 2's hosted log
   (`ereq_c1f7fb50…`, re-fetched, 139451 bytes) has **zero** hits — same coworld, same code,
   clean when the quota wasn't exhausted. The verifier also polled inside the 75-minute bound
   rather than going Blocked, as the check instructs.
3. **Handled by design, not by hanging:** design.md §2 "Degrade, never hang" declares exactly
   this path — "HTTP 429 → no retry; scripted move immediately" plus model-candidate failover —
   and the log shows both firing: one scripted decision (`results.fallbacks == [1,0,0,0]`),
   failover to Sonnet, all subsequent calls 200, episode `complete` with 8/8 hands scored.
   Cost: 1 scripted decision in 100 champion decision events.

The verifier recorded the exception rather than hiding the hit and flagged it for
adjudication — the correct behaviour. **The exception legitimately covers these bytes.
Check 5 is TRUE; not blocking.** (If the byte-string mismatch is worth closing, the fix is a
one-line prompt edit adding `ThrottlingException`/429 to the named capacity symptoms — a
prompts hygiene item, not a defect in this run.)

## 6. Public page uses the static replay path — TRUE

Re-fetched all three sources myself. (a) Raw HTML of `https://softmax.com/trick-taking`
(http 200, 659 kB): no literal `<iframe src>` — the page is client-rendered, so per the prompt
this is *unknown*, not a failure, and the fallback sources govern; the SSR payload embeds
`playlist[0]` = episode `3b1a41ce…`, `coworldName trick-taking`, round 4 episode 1
(`trick-taking.r4.e1`), `replayUrl …/ec71e84c….replay` — **featured match present**.
(b) `POST /coworlds/replays/session` returns
`https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_0de16cf6-8d0f-4601-8ca7-1c60fc3544d0/sha256%3A51bc9a90…eabf1/index.html?replay=<the s3 url>&v=2`
with `ready: true` — the static route with cow_id and manifest sha both matching STATE, and
**not** a `/client/replay` pod URL (zero occurrences of `client/replay` in the page). **TRUE.**

## 7. Certification declared the static bundle — TRUE

Read the committed `runs/2026-08-26-trick-taking/release-result.json` myself:
`.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared;
/client/replay and /replay not required)` — contains the required string. Source is the
committed artifact of release run 33036293815 (matching `STATE.coworld.release_run_id`), not
`/tmp`. **TRUE.**

## 8. Viewer executed, then judged — TRUE (all three parts held)

CI fact re-checked, not accepted: run **33039031390** (`viewer-check`), created
2026-08-27T04:18:51Z — after the 04:18:49Z dispatch — `status: completed`,
`conclusion: success` (re-fetched via `gh run view`). Evidence committed under
`runs/2026-08-26-trick-taking/viewer-check/` and read directly, not via the summary:

- **(a) loaded:** `viewer-smoke.json` line 2: `"loaded": true`, in 1705 ms;
  `signals.data_replay_loaded: "true"`, `bridge: ["loading","ready"]`, `bridge_ready: true`,
  `bridge_error: []`, `failure: null`. Verified from the committed JSON. ✅
- **(b) the replay advances:** the three scrub readouts from the committed JSON, verbatim —
  0 % `HAND 1 / 8 · NO TRUMP`; 50 % `HAND 5 / 8 · NO TRUMP · TRICK 1 / 5 · RATCHET TO PLAY`;
  100 % `HAND 8 / 8 · ♠ TRUMP · TRICK 5 / 5 · FINAL`. All three differ. ✅
- **(c) judgment:** I viewed `viewer-smoke.png` independently. It shows the 100 %-scrub frame:
  TRICK·TAKING masthead with an EUCHRE variant chip and `«LOG` toggle; the clock reading
  `HAND 8 / 8 · ♠ TRUMP · TRICK 5 / 5 · FINAL`; a four-seat scorebug (`daveey-1 4 POINTS ·
  Ratchet 5 · daveey 4 · Piston 5`) with team pips and trick tallies; four cog avatars around an
  elliptical table with per-seat note bubbles in readable prose; a centred endcard —
  `FINAL — 8 HANDS / Ratchet & Piston TAKE THE TABLE` with a SCORE/POINTS/TRICKS/BID-MADE
  table; and the transport strip with play button, tick-marked scrubber and `266 / 266`. The
  endcard numbers reconcile seat-for-seat with the replay bytes I fetched in §4:
  `results.points [4,4,5,5]`, `results.tricks [7,9,6,18]`, `win [false,false,true,true]`,
  266 events. The chrome is recognisably the babel/parley starter's (transport strip, momentum
  scrubber, scorebug band, endcard) — not the gridlock rewrite failure. Legible, advancing,
  shows the game. ✅

The verifier's two legibility observations (scorebug mixes player names with cog aliases for
the filler seats; the endcard scrim dims the final frame heavily) are fair, correctly
classified as non-blocking, and I concur — neither is named by any definition-of-done item.

---

## Verdict

All eight definition-of-done items are TRUE at the current head, each re-derived from committed
artifacts or fresh fetches. The one literal-grep failure (check 5) falls squarely under the
exception the prompt provides for platform-wide Bedrock capacity symptoms, with the cross-check,
the clean same-coworld round, and the designed degrade path all evidenced. No check's evidence
was missing from VERIFY.md, and no re-fetch contradicted it. Nothing blocking.

Non-blocking observations (for the coordinator, not gate items):
- Prompt hygiene: `prompts/60-verify.md` §5 could name `ThrottlingException`/HTTP 429 alongside
  `LLM provider is unavailable` as a capacity symptom, so future verifiers need not flag it.
- VERIFY.md's "issued at 03:40Z" gloss on the 03:42:12Z filler log line is a harmless
  batch-timestamp ambiguity; checks 1's verdict does not depend on it.

BLOCKING: 0
