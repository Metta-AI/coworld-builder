blocking: 0

# phase-60 verdict — negotiation-games
Head: b064779   Checklist: docs/SPEC.md §Definition of done (phase 60, all fetched, never assumed)
Independent read written before reading fixes: yes (order followed: SPEC → VERIFY.md → committed artifacts → context; no fixer report exists in phase 60)

Adjudicated: `runs/2026-08-26-negotiation-games/VERIFY.md` (verdict all-true 8/8) against the
8 definition-of-done items. Every item was spot-checked by re-fetching live where cheap; none
was accepted on the verifier's assertion alone.

---

## Item 1 — ≥2 completed rounds after fillers set — STANDS (TRUE)

VERIFY.md pastes the full `/rounds?league_id=` body: rounds 1 and 2 both `status: "completed"`,
`error: null`, plus the elevated `/leagues/<L>/filler-policies` read (haggler:v2 =
`f8763013-…`, hardliner:v2 = `44c9e9fc-…`) and — stronger than timestamp inference — the
actual filler seating (`is_filler: true` at position 2) in both rounds' episodes.

Re-fetched myself:
- `GET /rounds?league_id=league_88e9052f…&limit=20` → round 2 `round_0f649abe-…` completed
  2026-08-27T00:41:44Z, round 1 `round_cd269017-…` completed 00:26:46Z, both `completed`,
  no error. Matches VERIFY.md verbatim.
- `GET /episode-requests/ereq_801e833e-…` (round 1) → position 2 =
  `negotiation-games-haggler` v2, `is_filler: true`. Matches VERIFY.md's quoted body.
- `GET /episode-requests/ereq_7670e849-…` (round 2) → position 2 =
  `negotiation-games-hardliner` v2, `is_filler: true`.

Both completed rounds seated a registered filler → fillers were set before both. Established.

## Item 2 — both champions ranked, fillers absent/Baseline — STANDS (TRUE)

VERIFY.md pastes the leaderboard verbatim (bare array — the known shape alternation, not a
defect). Re-fetched `GET /divisions/div_5699e6c3-…/leaderboard` myself: exactly two rows,
rank 1 `daveey-1` (`negotiation-games-integrative:v2`, rounds_played 2, score 1030.53…),
rank 2 `daveey` (`negotiation-games-anchor:v2`, rounds_played 2, score 969.47…). No
haggler/hardliner row anywhere — the "fillers absent" branch is satisfied. Byte-for-byte
identical to VERIFY.md's paste. Established.

## Item 3 — latest round's episode completed with replay_url, participants named — STANDS (TRUE)

VERIFY.md uses the nested `/rounds/<R>/episode-requests` route (flat route documented 405) and
pastes the full episode body. Re-fetched `GET /episode-requests/ereq_7670e849-43da-4d31-86b2-77aa8b4c7a2a`
myself: `status: "completed"`, `replay_url:
https://softmax-public.s3.amazonaws.com/replays/369d7c2e-4faf-4fbd-84f7-efd0fd860ae9.replay`,
seat 0 = daveey / anchor:v2 (`is_filler: false`), seat 1 = daveey-1 / integrative:v2
(`is_filler: false`), seat 2 = hardliner:v2 (`is_filler: true`). Matches VERIFY.md exactly.
Established.

## Item 4 — replay bytes valid UTF-8 JSON, protocol/reason correct, champions doing the thing — STANDS (TRUE)

Re-downloaded the replay from the S3 URL myself: `http=200 bytes=11216` (same size), `jq -e`
parses it strictly, `protocol == "negotiation.replay.v1"` (matches design.md §replay schema and
`replay_check.py:25` which VERIFY.md quotes from the repo at main), `results.reason ==
"complete"` — the preferred value, no deadline argument needed. `results` verbatim identical to
VERIFY.md's paste: `fallbacks [0,0,0]`, scores `[0.65, 0.85, 0.875]` all in [0,1] per design,
6/6 matches, names `["daveey","daveey-1","Baseline"]` (filler correctly rendered Baseline).
Re-ran the seat/scripted grouping myself: seat 0 → 9 decisions all `scripted: false`, seat 1 →
5 all `scripted: false`, seat 2 (filler) → 7 all `scripted: true`. Champion decision text is
substantive and game-shaped — e.g. match 0 turn 1 seat 0: "I need the hat most - it's worth
everything to me. Happy to negotiate on books and balls."; match 4 turn 4 seat 0: "I'm conceding
one ball. You get 1 ball + 2 hats…" — real bargaining moves, not fallbacks or boilerplate.
All 6 `matchEnd` events are `outcome: "deal"`. Established.

Minor note (not a finding): VERIFY.md's item-4 "non-trivial content" quote is labelled as coming
from the *round-1* replay; the round-2 replay's own champion texts (excerpted in VERIFY.md §8c
and re-verified by me above) independently satisfy the non-trivial-content clause, so nothing
rests on the round-1 quote.

## Item 5 — hosted game log clean — STANDS (TRUE)

Re-fetched `GET /episode-requests/ereq_7670e849-…/artifacts/logs` with the elevated header
myself: `http=200 bytes=34608` (same size as VERIFY.md). Decoded the python `b'…'` reprs with
`ast.literal_eval` (34338 chars decoded) and grepped
`falling back|LLM provider is unavailable|cut off at max_tokens|rejected`: **0 hits** in the
decoded text and, belt-and-braces, 0 hits in the raw form too. Consistent with the replay's
`fallbacks: [0,0,0]`. No Bedrock symptom → no cross-coworld check owed. Established.

## Item 6 — public page: featured match, static iframe src, never /client/replay — STANDS (TRUE)

Re-fetched `https://softmax.com/negotiation-games` myself: `http=200`, the SSR payload contains
the round-2 replay URL (`replays/369d7c2e-4faf-4fbd-84f7-efd0fd860ae9.replay`) in the playlist
and **zero** occurrences of `client/replay` anywhere in the 640 KB page. Re-ran the
`POST /coworlds/replays/session` call the page's JS makes, myself, with the same body:

`viewer_url = https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e3bccc46-a2fb-474b-9fc2-6e5ea91085c5/sha256%3A06acbd012316b207fcd998ba50bde7d7c32447b9e93587d7203ede334219cca1/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F369d7c2e-4faf-4fbd-84f7-efd0fd860ae9.replay&v=2`, `ready: true`

— identical to VERIFY.md's paste: the static route, the right `cow_id` (matches
STATE.coworld.cow_id), the right manifest sha (matches STATE.coworld.manifest_sha and the
canonical v0.1.1 coworld row VERIFY.md quotes), `index.html?replay=<s3 url>`. Established.

## Item 7 — certification "Replay liveness: skipped (static replay bundle declared" — STANDS (TRUE)

Read the committed `runs/2026-08-26-negotiation-games/release-result.json` myself:
`certify.replay_liveness = "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"`,
and the same line appears inside `certify.output_tail` (10/10 cert steps passed,
`hosted_certification: "certified"`). The checklist's required substring is present exactly.
Reading the committed artifact rather than re-fetching is the checklist's own instruction
("read from the committed runs/<run>/release-result.json"), so the verifier's documented
exception is correct, not a gap. Established.

## Item 8 — viewer executed, three-part gate, spectator judgment — STANDS (TRUE)

(a) `loaded: true` — verified in the committed `viewer-check/viewer-smoke.json`: `loaded: true`
in 2909 ms, `signals.data_replay_loaded == "true"`, `bridge: ["loading","ready"]`,
`bridge_ready: true`, `data_replay_error: null`, `bridge_error: []`, `failure: null`. The
recorded `url` field is character-identical to item 6's iframe src. I re-ran
`gh run view 33027843730 -R Metta-AI/coworld-builder` myself: `workflowName: viewer-check`,
`createdAt: 2026-08-27T00:44:34Z`, `status: completed`, `conclusion: success`.

(b) replay advances — the committed json's `scrub` array holds three distinct clocks:
0% `MATCH 0 / 6`, 50% `MATCH 4 / 6 · TURN 2 / 10 · DAVEEY TO MOVE`, 100% `FINAL · 6 MATCHES`.
All three differ. The 50% readout reconciles with the replay JSON: the event list's midpoint
sits in match 4 at turn 2 with seat 0 (daveey) to move — I confirmed that event
(`match 4, turn 2, seat 0, offer`) exists in my re-downloaded replay.

(c) judgment — VERIFY.md carries a genuine multi-paragraph spectator judgment written from the
artifacts. I viewed `viewer-smoke.png` myself: it shows the end state exactly as described —
`NEGOTIATE` wordmark, `FINAL · 6 MATCHES` clock, three-seat scorebug reading
`daveey 26 PTS 0.65 · daveey-1 34 PTS 0.85 · Ratchet 35 PTS 0.88` (= `results.points`/`scores`),
six deal chips `DEAL 10-10 · DEAL 6-10 · DEAL 10-9 · DEAL 10-6 · DEAL 0-8 · DEAL 8-8` matching
the six `matchEnd` payoffs in the replay JSON in order, the endcard
`Ratchet TAKES THE TABLE` with a standings table (0.88/35/4/-2.8, 0.85/34/4/0.8, 0.65/26/4/2.0 —
`results.scores/points/deals/giveaway` rounded, in rank order), two cog avatars at a table with
per-seat valuation strips, a greyed `SITTING OUT` third seat, and a beat-marked scrubber with
frame counter `35 / 35` (= the event count I verified). Picture, readouts, and replay JSON agree
with no interpretation needed. The judgment is legible and shows the game. Established.

The verifier's disclosed double-dispatch (run `33027506937` rendered the then-featured round-1
replay; superseded, not used, not committed) is a disclosure, not a finding — per the brief.

---

## Refuted

None — no verifier claim failed re-checking. Every re-fetch (leaderboard, rounds, both episode
requests, replay bytes, hosted logs, public page, replay session, gh run) returned what
VERIFY.md pasted.

## Checklist pass (independent)

| item | status | evidence |
|---|---|---|
| 1 ≥2 completed rounds after fillers | TRUE | re-fetch `/rounds` → 2×completed; `is_filler:true` seat in both episodes (ereq_801e833e, ereq_7670e849) |
| 2 champions ranked, fillers absent | TRUE | re-fetch `/divisions/div_5699e6c3…/leaderboard` → 2 rows, daveey-1 #1, daveey #2, no filler row |
| 3 latest episode completed + replay_url | TRUE | re-fetch ereq_7670e849 → completed, replay_url set, seats 0/1 champions |
| 4 replay valid, protocol, reason, champions act | TRUE | re-downloaded 11216 B, jq-strict, `negotiation.replay.v1`, `complete`, fallbacks [0,0,0], 14/14 champion decisions scripted:false with substantive text |
| 5 hosted log clean | TRUE | re-fetched + decoded 34338 chars → 0 pattern hits (decoded and raw) |
| 6 static iframe src, featured match | TRUE | page SSR has r2 replay in playlist, 0×`client/replay`; session POST → static path + `ready:true` |
| 7 cert liveness-skipped string | TRUE | committed release-result.json `certify.replay_liveness` exact match |
| 8 viewer rendered + judged | TRUE | run 33027843730 success (re-checked); committed json `loaded:true`, 3 distinct scrub clocks; PNG viewed and reconciled beat-for-beat |

## Verifier report audit

| item | verifier said | I verified | agrees |
|---|---|---|---|
| 1 | TRUE, both rounds completed, fillers seated | re-fetched rounds + both episodes | yes |
| 2 | TRUE, 2 rows, no fillers | re-fetched leaderboard, byte-identical | yes |
| 3 | TRUE, ereq completed w/ replay_url | re-fetched episode request | yes |
| 4 | TRUE, valid/complete/non-scripted | re-downloaded + re-parsed replay | yes |
| 5 | TRUE, CLEAN | re-fetched + re-decoded logs, 0 hits | yes |
| 6 | TRUE, static path | re-fetched page + session POST | yes |
| 7 | TRUE, string present | read committed artifact | yes |
| 8 | TRUE, 3-part gate | re-checked run, json, viewed png | yes |

## Non-blocking observations

- VERIFY.md item 4 labels its "non-trivial content" quote as taken from the round-1 replay while
  the item is adjudicated on round 2's; harmless because round 2's own champion texts (VERIFY.md
  §8c, re-verified by me) satisfy the clause independently.
- The verifier's own legibility note (opaque endcard covering the table at 100%) is a fair
  phase-30 observation and does not touch any item.

BLOCKING: 0
