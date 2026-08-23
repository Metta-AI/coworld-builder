blocking: 0

# phase-60 verdict — contagion

Head: f4b0352   Checklist: docs/SPEC.md §Definition of done (phase 60, all fetched, never assumed)
Independent read written before reading VERIFY.md: yes — I fetched every API endpoint, the S3
replay, the slug page, the hosted log, the session URL and the PNG myself before opening
VERIFY.md. Nothing below rests on the verifier's pastes.

## Item-by-item (all evidence re-fetched or re-read by me)

### 1. ≥2 rounds completed after fillers set — **VERIFIED**
My fetch of `GET /rounds?league_id=league_53d9ccfb…`: round 2 `completed` 12:15:44.229Z, round 3
`completed` 12:30:26.807Z, round 1 `failed` (created 12:12:00.474Z, failed 0.25 s later,
`error: "Temporal RoundWorkflow failed before settling the round."`) — the pre-entrant
auto-round; no discarded rounds. The exclusion of round 1 is sound and the "after fillers"
condition holds on evidence stronger than timestamps: **both completed rounds' episodes
actually seated the fillers** — my fetch of the episode requests for rounds 2 and 3 shows 4
`is_filler: true` seats each, running `contagion-sentinel`/`contagion-laggard`, the exact
`filler_policy_version_ids` (90a1ef43…, d224d741…) I read off the league object. A round
cannot seat fillers that were not yet set. Both completions also post-date the log's filler
registration line (≤12:13:30Z).

### 2. Both champions ranked, fillers absent — **VERIFIED**
My fetch of `GET /divisions/div_16e3c809…/leaderboard` (bare array, 2 rows): rank 1 `daveey-1`
(`contagion-broker:v1`, Elo 1030.53, rounds_played 2), rank 2 `daveey` (`contagion-warden:v1`,
Elo 969.47, rounds_played 2). No filler rows at all — "absent" satisfied.

### 3. Latest round's episode request completed with replay_url — **VERIFIED**
My fetch of `GET /episode-requests?round_id=round_0d4c6b59…`: one entry,
`ereq_a423e065-fc6a-4c58-a0d5-71e38c0893a6`, `status: completed`,
`replay_url: https://softmax-public.s3.amazonaws.com/replays/af23e250-….replay`; participants
seat 0 = daveey/contagion-warden (is_filler false), seat 1 = daveey-1/contagion-broker
(is_filler false), seats 2–5 fillers (is_filler true). Named correctly.

### 4. Replay bytes valid, champions doing the thing — **VERIFIED**
I re-fetched the replay from S3 myself: sha256 `ec4b97c6…` — **byte-identical to the committed
`ep.replay`** (98,177 bytes). Decodes as strict UTF-8, parses as JSON; `protocol:
contagion.replay.v1`; `results.reason: complete` (weeks 20 = maxWeeks 20, no deadline
exception needed). My own event tally: 120 `dial` events; seat 0 (daveey) 20/20 dials
`scripted: false`, seat 1 (daveey-1) 20/20 `scripted: false` — **0/40 champion fallbacks** —
with substantive content (avg `say` ~150 chars, avg private `text` ~700 chars; e.g. seat 1
wk 19: "Wintermoor escalating to L3, sealing all borders. True prevalence 5.9%, deaths
438/wk…"). Baseline seats 2–5 are 20/20 scripted, which is their design, not degradation.

### 5. Hosted game log clean — **VERIFIED**
I re-fetched `GET /episode-requests/ereq_a423e065…/artifacts/logs` with the elevated header:
HTTP 200, 98,827 bytes, real container log (bedrock-sidecar + game containers populated).
`grep -Ec "falling back|LLM provider is unavailable|cut off at max_tokens|rejected"` → **0
matches** on my own copy. No platform exception invoked or needed.

### 6. Public page on the static replay path — **VERIFIED**
I re-fetched `https://softmax.com/contagion` (370,765 bytes): zero occurrences of
`client/replay`; the SSR flight payload carries `state.playlist[0]` = episode
`52bf0cd8…`, code `contagion.r3.e1`, round 3, `replayUrl` byte-identical to item 3's — the
featured match is the verified episode. I replayed the page's own resolution call myself:
`POST /coworlds/replays/session` with the cow_id + that replay URI returned
`viewer_url: …/v2/coworlds/replays/static/cow_6b43a43d-8aa2-41ea-aae6-4dd50f084c54/sha256%3A16630ba4…/index.html?replay=<s3 url>&v=2`,
`ready: true`. Static route, sha = STATE's `manifest_sha`, not a pod URL.

### 7. Certification declared static bundle — **VERIFIED**
I read the committed `runs/2026-08-23-contagion/release-result.json` myself: line 11,
`"replay_liveness": "Replay liveness: skipped (static replay bundle declared; /client/replay
and /replay not required)"`; same string in `.certify.output_tail`; `.certify.ok: true`,
10/10 transcript steps passed.

### 8. Viewer executed + spectator judgment — **VERIFIED**
(a) `viewer-smoke.json` (committed, I read it): `loaded: true` at 1682 ms via the
`coworld-replay` bridge (`bridge: ["loading","ready"]`, `bridge_ready: true`, no
`data-replay-error`, `bridge_error: []`, `failure: null`) — the bridge-`ready` path SPEC 8a
explicitly accepts; its `url` is exactly the item-6 `viewer_url`. I checked the run myself:
`gh run view 32639677937` → workflow `viewer-check`, `completed`/`success`.
(b) Three scrub readouts are three distinct strings, ending `WEEK 20 / 20 · VARIANT +25% ·
FINAL` — advancement 0 → 20, not a frozen frame (see (c): the 100 % frame is the rendered
final state).
(c) I looked at `viewer-smoke.png` myself: legible, and it shows the game — CONTAGION header,
final clock, six-seat scorebug, six-region map with road links and speech bubbles carrying
week-19 champion `say` text, infection chart ("dotted = what they REPORT"), 143/143 scrubber,
and an end card `FINAL — 20 WEEKS · 33,149 DEAD / Riverbend KEPT THE LIGHTS ON` whose
standings I reconciled **field-for-field against my own S3 replay fetch**: scores
(-3028, 7573, 11818, 9961, -28706, 10595), GDP, deaths and totalDeaths 33,149 all match
`results` exactly. VERIFY.md's judgment paragraph is present, legible, and consistent with
what I see. All four evidence files committed under `runs/…/viewer-check/` at head f4b0352.

## Refuted
None. No VERIFY.md verdict is unsupported by its evidence; every claim I re-fetched
reproduced.

## Non-blocking observations
- VERIFY item 1 states fillers were registered "12:10–12:12Z"; the log line recording it is
  timestamped 12:13:30Z, so the precise set-time is not pinned. Immaterial: both counted
  rounds *completed* after 12:13:30Z and both episodes demonstrably seated the fillers.
- The 50 % scrub readout still shows `WEEK 0 / 20` (` · WAITING ON 6` suffix). With 143
  roughly uniform frames the midpoint would be ~week 10, so this smells like the readout was
  captured mid-seek or the scrub mapping is non-linear — VERIFY's "intra-week deliberation"
  explanation is plausible but unproven. Gate 8b is nonetheless met by the letter (three
  distinct strings) and in substance (100 % reached the final frame, rendered).
- `scorebug: ""` / `feed_lines: 0` are harness selector misses, correctly disclosed in
  VERIFY.md rather than glossed; the screenshot shows both elements populated.

## Verifier report audit
| item | verifier said | I verified | agrees |
|---|---|---|---|
| 1 | rounds 2,3 completed; r1 failed pre-filler, excluded | same statuses/timestamps from my /rounds fetch; fillers seated in both episodes | yes |
| 2 | daveey-1 #1, daveey #2, fillers absent | identical leaderboard from my fetch | yes |
| 3 | ereq_a423e065 completed, replay_url, seats correct | identical from my fetch | yes |
| 4 | strict JSON, protocol/reason ok, 0/40 champion fallbacks | byte-identical S3 fetch, same counts from my own jq/python | yes |
| 5 | CLEAN, 98,827 bytes | 0 pattern hits on my own fetch, 98,827 bytes | yes |
| 6 | static viewer_url, ready:true, featured contagion.r3.e1 | same viewer_url from my own session POST; playlist[0] in my page fetch | yes |
| 7 | liveness-skipped string in committed artifact | read it at release-result.json:11 | yes |
| 8 | loaded:true, clocks differ, judgment from png | run 32639677937 success (gh), json/png re-read, numbers reconciled to replay | yes |

BLOCKING: 0
