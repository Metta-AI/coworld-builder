blocking: 0

# Phase-60 verdict — sumo-traffic-signals

Judge read order: SPEC §Definition of done (docs/SPEC.md:148–184) → committed evidence
(`viewer-check/viewer-smoke.json`, `viewer-smoke.png`, `release-result.json`) → VERIFY.md →
live re-fetches. Independent spot-checks were re-fetched at ~18:20–18:24Z on 2026-08-28
(SOFTMAX API, S3, gh); the ladder had by then produced round 4, which is noted where it
matters. VERIFY.md's evidence is command-plus-response throughout — no item rests on an
assertion — and every spot-check reproduced it.

## Item-by-item

### 1. ≥2 completed rounds after fillers were set — TRUE, evidence is fetched and holds
VERIFY.md pastes `GET /rounds?league_id=` with full round objects. My live re-fetch reproduces
it exactly: rounds 2 (completed 17:51:03.878390Z) and 3 (completed 18:06:09.079927Z) are
`completed`; round 1 is `failed` with the verbatim error `Temporal RoundWorkflow failed before
settling the round.` at 17:44:00.6Z — the documented pre-filler placement failure
(playbooks/observatory-api.md:113–114), correctly excluded per the SPEC's "not failed/discarded".
The "fillers set ~17:44Z" timing is an inference from log.md line 36 plus round-creation
timestamps, but the *fetched* proof is decisive: I additionally pulled **round 2's** episode
request (`ereq_e20e536b-4ae0-4b8d-b6d1-43cac8310737`) and it seats `signals-fixedcycle` twice
with `is_filler: true` — so fillers were live for both counted rounds, not just round 3 (which
VERIFY.md proved via item 3). No round is `discarded`.

### 2. Both champions ranked, fillers absent — TRUE
VERIFY.md pastes the leaderboard GET. My re-fetch (post-round-3 state matches VERIFY's snapshot;
scores have since moved with round 4, as expected): `daveey` / `signals-greenwave:v1` rank 1,
`daveey-1` / `signals-gatekeeper:v1` rank 2, both `rounds_played ≥ 1`. The list has exactly two
rows; neither filler appears — the "absent" branch of the SPEC's "absent or labelled Baseline".

### 3. Latest round's episode request completed with replay_url — TRUE
VERIFY.md pastes both GETs (nested `/rounds/<id>/episode-requests`, then the request detail).
Re-fetched: `ereq_75e2c1eb-1a8d-498e-ae67-26edcd34e6fd` is `completed`, `replay_url` =
`https://softmax-public.s3.amazonaws.com/replays/4c2c2a45-861a-4bfb-b275-adcac8a11cf7.replay`,
participants name `daveey` (signals-greenwave, `is_filler:false`), `daveey-1`
(signals-gatekeeper, `is_filler:false`) and two `signals-fixedcycle` filler seats
(`is_filler:true`, version id `9ccb76ef-…` from the filler list, distinct from the champions').
The API-shows-policy-name / viewer-shows-`Baseline (N)` split is real: the replay `names` array
and the screenshot both render the filler seats as `Baseline` / `Baseline (2)`.

### 4. Replay bytes valid and show the game — TRUE under the design-declared substitute
VERIFY.md says explicitly the substitute is in force and quotes design.md §Replay bytes
(design.md:1114–1139), which pins `tools/replay_summary.py` + `jq -e .` verbatim — I confirmed
the design text matches the quote. I re-ran the substitute end-to-end myself: fetched the S3
bytes (88687 bytes, magic `COWLDSIG`), cloned `Metta-AI/cogame-sumo-traffic-signals` (HEAD
`e20601a`, the certified sha), ran `replay_summary.py`, `jq -e` passed. Results:
`protocol == "signals/v1"`, `results.reason == "complete"` (no deadline escape needed),
`throughput == 134 > 0`; 256 `source=="llm"` orders confined to champion slots 0 and 1
(128 each, verbs phase/hold/auto/wave), exactly 3 `wave` orders with delay 5; 64 non-empty
radio lines (first: "Column 1 eastbound is my wave: A1 at +0, A2 at +6"); `fallbacks: 3`
against `fallbackTurns [0,0,0,0]` and `llmTurns [32,32,0,0]` — 3 retried attempt-1 transport
timeouts, zero degraded turns. Every bar of the substitute is met, and none of it is asserted:
all reproduced from bytes.

### 5. Hosted game log clean — TRUE; the single `rejected` hit is game vocabulary
I re-fetched `/artifacts/logs` with the elevated header (141557 bytes) and re-ran the grep.
Counts: `falling back` 0, `LLM provider is unavailable` 0, `cut off at max_tokens` 0,
`rejected` 1. The one hit is the game's own `signals results:` JSON line containing
`"rejected":27` (cars turned away) and `"ordersRejected":[1,0,0,0]` — confirmed from the raw
bytes, not from VERIFY.md's paste; it sits in the game's results emission, not in any
LLM-transport or provider line. The three `seat N attempt 1 failed, will retry` lines match the
replay's 3 fallback records one-for-one, and design.md:534–535 does pin `will retry` as the
attempt-1 notice with `falling back` reserved for a genuine second failure (quote verified).
No exception clause was needed.

### 6. Public page uses the static replay path — TRUE on SPEC intent
VERIFY.md records which sources it used (SSR payload + session endpoint) and why the raw-HTML
grep is *unknown* rather than false — both per prompts/60-verify.md:82–93 and
playbooks/observatory-api.md:314–340. I reproduced both: (a) the raw grep finds no iframe
(client-rendered, as documented); (b) the SSR `state.playlist[0]` carries a featured match with
both ranked champions (at my fetch time it had rolled to round 4, `sumo-traffic-signals.r4.e1` —
consistent with VERIFY's round-3 snapshot at 18:09–18:17Z, and featured-match-present holds
either way); (c) `POST /coworlds/replays/session` returns byte-identical `viewer_url`:
static route `/v2/coworlds/replays/static/cow_ec8a6c5d-…/sha256%3A7757…3298/index.html?v=2`
with the replay as a `#replay=` URL-encoded fragment, `ready: true`. cow_id and manifest_sha
match STATE. The SPEC's literal string says `index.html?replay=`; the fragment form is the
documented 2026-08-28 evolution of the same static route (observatory-api.md:326: "both are the
static route") and the SPEC's operative clause — static, **never** `/client/replay` — is
satisfied. No pod URL anywhere.

### 7. Certification declared the static bundle — TRUE
Read from the committed `runs/2026-08-28-sumo-traffic-signals/release-result.json` myself:
`.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared;
/client/replay and /replay not required)` — the exact SPEC string plus tail; `.certify.ok` =
`true`; the `output_tail` shows all 10 transcript steps `[pass]`. VERIFY.md names the committed
file as its source (the documented exception), which is what prompts/60-verify.md:96–98
requires.

### 8. Viewer executed + spectator judgment — TRUE, all three sub-conditions
(a) **loaded:** CI run 33198007349 verified via `gh api`: `workflow_dispatch`, created
2026-08-28T18:09:26Z (2 s after the claimed dispatch time — the find-the-new-run discipline was
followed, not "latest run"), conclusion `success`. I re-downloaded its `viewer-check` artifact:
**byte-identical** to the committed `viewer-check/` files (json diff empty, `cmp` clean on the
png). `viewer-smoke.json`: `loaded: true` at 2494 ms via `data-replay-loaded="true"`,
`data_replay_error: null`, `failure: null`. The json's `url` field is exactly the item-6 iframe
src, fragment and all.
(b) **advances:** the three scrub readouts differ (THROUGH 0 → 46 → 134, WAITING 0 → 16182 →
48093, DEMAND 4 → 328 → 422) and the 100 % readout equals the replay results I decoded
independently.
(c) **judgment:** the paragraph exists and is written from the render. I opened the committed
png myself: it shows the endcard over the dimmed 4×4 grid — `134/422 CARS THROUGH · PAR 260
MISSED`, `FULL PERIOD` badge, the controller table (daveey 24/12517, daveey-1 24/14785,
Baseline 42/10832, Baseline (2) 44/9959, waves 0, spillbacks 73), `CITY SCORE 133759850`, four
quadrant cards with phase changes 66/80/124/123, transport strip with `256 / 256`, speed chips,
and the scrubber with a rising `THROUGHPUT` momentum trace. **Every one of those numbers is in
the replay bytes I decoded** (`served [24,24,42,44]`, `seatWaitTicks [12517,14785,10832,9959]`,
`phaseChanges [66,80,124,123]`, `scores [1337598{50,20,70,80}]`, `rejected 27`, `endRule
"fullPeriod"`, `finalTick 256`). The `feed_lines: 0` explanation is correct: I fetched the live
shell and its feed element is `id="killfeed"`, which the probe's selector list misses — a probe
gap, not a viewer gap; the feed content is visible in the png. The chrome-provenance diff (47
shared starter ids, FPV/minimap/zoom dropped per design, five signal chips added) is consistent
with the id set I pulled from the live shell.

## Non-blocking observations
- Item 0/1: the "~17:44Z" filler-registration time is inferred (log.md line 36 is stamped
  17:45:17Z and batches fillers→unpause→trigger). The fetched facts carry the item regardless:
  round 1's instant pre-filler failure, and `is_filler:true` seats in **both** counted rounds
  (round 2's ereq re-fetched by me; VERIFY.md only closed that loop for round 3).
- Item 4: the replay carries 3 `k:"fallback"` records with `attempt:1` while design.md:530–534
  describes fallback records as written on the *second* failure. `fallbackTurns [0,0,0,0]`
  shows these are retry notices, so the substitute's bar is met on either reading — but the
  record vocabulary is slightly looser than the design text.
- Item 6: SPEC's literal `?replay=` vs the live `?v=2#replay=` fragment — documented platform
  change, same static route; suggest updating SPEC's literal string at the next edit.
- Item 8: `viewer_smoke.mjs`'s feed selector (`#feed, .feed, #log, [id$="-feed"]`) misses the
  starter's own `#killfeed` id — worth widening in templates, as VERIFY.md itself flags.

## Summary
All eight items rest on fetched evidence (items 7 and 8 under their documented exceptions:
committed release-result.json, and CI-produced artifacts committed in-repo). Every spot-check I
re-ran — rounds, leaderboard, episode requests for rounds 2 *and* 3, replay bytes decoded from
S3 with the pinned tool at the certified sha, hosted logs grep, SSR playlist, session endpoint,
CI run conclusion, artifact byte-comparison, live shell ids — reproduced VERIFY.md's evidence.
Nothing was substituted or assumed beyond the declared, design-pinned substitute for item 4,
which VERIFY.md names and satisfies. No item is blocking.

BLOCKING: 0
