blocking: 0

# Phase 60 verdict — commons-family
Head: 9e21b5d9abc132c83dcd6176a52bb26d34326144   Checklist: docs/SPEC.md §Definition of done (line 148) / prompts/60-verify.md   Independent read written before reading VERIFY.md: yes

I re-fetched every check myself before opening VERIFY.md (rounds, leaderboard, all three
completed rounds' episode requests, the round-4 replay bytes, the hosted game log, the public
page + SSR payload + `POST /coworlds/replays/session`, the committed `release-result.json`, the
committed `viewer-check/` artifacts including the png, and the viewer-check CI run conclusion).
Where VERIFY.md's evidence could be re-derived, it reproduced byte-for-byte.

## Standing blocking findings

None.

## The two flagged items

### Check 5 — one `rejected` grep hit → PROPERLY DOCUMENTED EXCEPTION, check stands TRUE
- I fetched `/episode-requests/ereq_5a0fca58-…/artifacts/logs` (elevated) myself: exactly one
  hit for the four-pattern regex, and it is
  `('127.0.0.1', 53286) - "WebSocket /player?slot=0&token=bad" 403` →
  `INFO: connection rejected (403 Forbidden)` — from localhost, at pod startup, **before any
  real player connected**; the real slot-0 player later connected with a valid token
  (`WebSocket /player?slot=0&token=GCtu9O05fq8ee1cfMcY4BA" [accepted]`). Zero hits for
  `falling back`, `LLM provider is unavailable`, `cut off at max_tokens`.
- I re-fetched the cited meadow cross-check myself
  (`ereq_a11d2a9c-bca5-4998-880b-ef49a60c2033/artifacts/logs`): identical
  `token=bad` 403 probe from 127.0.0.1, identical `connection rejected (403 Forbidden)` at
  line 9, 1 hit total under the same regex — exactly as VERIFY.md §5 claims.
- SPEC item 5 allows "a documented platform-wide cause checked against another LLM coworld".
  This is documented, cross-checked, and is a self-probe that proves token auth works, not an
  LLM degradation. Not a defeater.

### Round 3 replay_url null / scores [] → PROPERLY DOCUMENTED, defeats neither check 1 nor 3
- Verified at head: `GET /rounds?league_id=…` → rounds 2, 3, 4 `completed`, round 1 `failed`
  ("Temporal RoundWorkflow failed before settling the round.", quoted verbatim in VERIFY.md §1).
  Round 3's `ereq_fc8bb683-…` is `completed` with `replay_url: null`, `participant_scores: []`
  — I reproduced this.
- Check 1 requires ≥2 rounds `completed` (not failed/discarded) after fillers were set
  (21:19:30Z, log.md line 49). Strict reading: rounds 3 & 4 (created 21:33:53Z / 21:48:54Z) —
  2 rounds. Scored reading: rounds 2 & 4 (leaderboard `rounds_played: 2` corroborates). Either
  reading yields ≥2; all three completed rounds seated the fillers (I checked all three
  episode-request participant lists). VERIFY.md went further than required and fetched
  round 3's artifacts directly (elevated): a complete, distinct 20-round episode
  (`reason: complete`, seed 1309990201) whose Observatory record was simply never populated —
  a platform ingestion gap, reported not worked around.
- Check 3 concerns only the **latest** completed round, which is round 4:
  `ereq_5a0fca58-…` is `completed`, `replay_url` non-null (S3), champions at seats 0/1 as
  daveey/daveey-1 `is_filler:false`, fillers `is_filler:true` (rendered `Baseline (N)`
  spectator-side in the replay `seats`/`names`). Round 3's gap touches neither check.

## Checklist pass (independent)

| item | status | evidence |
|---|---|---|
| 1. ≥2 completed rounds after fillers | TRUE | my fetch: rounds 2/3/4 `completed`, 1 `failed` (error quoted); fillers 21:19:30Z (log.md:49) < rounds 3,4 created; leaderboard rounds_played=2 |
| 2. Both champions ranked, fillers absent | TRUE | my fetch: bare 2-row array — `1 daveey-1 commons-family-warden:v3 1030.53 2 2.0`, `2 daveey commons-family-steward:v3 969.47 2 0.0`; no filler rows |
| 3. Latest round's ereq completed + replay + participants | TRUE | my fetch of `ereq_5a0fca58-…`: `completed`, S3 `replay_url`, seats 0/1 champions, 2–5 fillers |
| 4. Replay bytes valid, protocol, shows the game | TRUE | my fetch: 112623 bytes, strict `jq -e` ok, `commons-family.replay.v1` (= design.md:721), `reason:complete`; champions 40/40 `src:"llm"`, 0 fallback/pass (both `.events[]` kind and `.rounds[].decisions[]` shapes reproduce VERIFY's numbers exactly, incl. message stats n=40/min=36/max=140/mean=106.4); results show champions carrying public_effort 19+21 and all 14 sanctions |
| 5. Hosted log clean | TRUE (documented exception) | my fetch: 1 `rejected` hit = pod-local `token=bad` probe; meadow cross-check re-fetched and confirmed identical |
| 6. Public page static replay path | TRUE | my fetch: no iframe in raw HTML (client-rendered, playbook-documented); SSR `state.playlist[0]` = round-4 featured match; `POST /coworlds/replays/session` → `/v2/coworlds/replays/static/cow_73578681-…/sha256%3Ad1ca4648…/index.html?replay=<s3>`, `ready:true`; sha = STATE `manifest_sha`; no `/client/replay` |
| 7. Cert declared static bundle | TRUE | committed `runs/…/release-result.json` → `.certify.replay_liveness` = "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)" |
| 8. Viewer executed + judged | TRUE | committed `viewer-check/viewer-smoke.json`: `loaded:true` (2722 ms), bridge `["loading","ready"]`, `data_replay_error:null`, scrub clocks `ROUND 1 OF 20 · WAITING ON 6` → `ROUND 10 OF 20 · WAITING ON 3` → `ROUND 20 OF 20 · FINAL` (three distinct), `failure: null`; CI run 32781916776 `completed/success` (checked via gh); smoke url = check-6 iframe src; I viewed viewer-smoke.png myself — legible, starter chrome (transport strip, scrubber + momentum graph, six-seat scorebug, centred endcard), endcard table matches `results.scores` [0.0,4.0,8.813,7.0,17.813,20.813] and welfare 58.4; judgment paragraph in VERIFY.md §8 accurately describes what the png shows |

## Verifier report audit

| claim (VERIFY.md) | I verified | agrees |
|---|---|---|
| §1 rounds 2/3/4 completed, round 1 failed with quoted error | re-fetched | yes |
| §1 round-3 ereq `replay_url:null, scores:[]` | re-fetched | yes |
| §2 leaderboard two rows exactly, values | re-fetched | yes (identical to the digit) |
| §3 ereq_5a0fca58 status/replay_url/participants/scores | re-fetched | yes |
| §4 replay 112623 bytes, protocol, event/decision counts, message stats | re-fetched, re-ran both jq shapes | yes, byte-identical outputs |
| §5 one `rejected` hit, probe context | re-fetched, re-grepped | yes |
| §5 meadow line-9 identical probe | re-fetched meadow's log | yes (1 hit, line 9) |
| §6 no iframe in HTML; playlist[0]; session POST static url, ready:true | re-fetched all three | yes |
| §7 committed release-result.json content | read committed file | yes |
| §8 run 32781916776 success; smoke json readouts; png description | gh run view + read committed artifacts + viewed png | yes |

## Non-blocking observations

- The round-4 game log contains `slot 0 unusable reply: '{...truncated json...}'` (round 8).
  VERIFY.md does not mention it. It matches none of check 5's four patterns, and the replay
  shows the design's retry-once path absorbed it (`llm_requests: 41` for 40 LLM decisions,
  `fallbacks: [0,0,0,0,0,0]`, slot-0 round-8 decision `src:"llm"`), so it defeats neither
  check 4 nor check 5. Worth a line in LEARNINGS: champion prompts that narrate at the
  140-rune limit occasionally emit truncated JSON.
- Round 2 was created at 21:18:53Z, 37 s **before** the fillers POST (21:19:30Z), yet its
  episode seated both fillers. VERIFY.md handles this honestly with its two readings; either
  reading independently satisfies item 1, so nothing turns on it.
- VERIFY.md's two legibility notes for phase 30 (endcard POLICY column prints aliases for
  Baseline seats; 100 %-scrub screenshot shows the endcard overlay) are accurate to the png I
  viewed and correctly classified as non-blocking.

BLOCKING: 0
