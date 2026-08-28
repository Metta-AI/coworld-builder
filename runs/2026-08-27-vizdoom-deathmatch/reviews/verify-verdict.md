blocking: 0

# phase-60 verdict — vizdoom-deathmatch
Run: 2026-08-27-vizdoom-deathmatch   Checklist: docs/SPEC.md §Definition of done (phase 60, all fetched, never assumed), items 1–8
Independent read written before reading VERIFY.md: yes — I re-fetched rounds, leaderboard, episode-requests (both rounds), the replay bytes (re-ran `tools/replay_summary.py` myself), the hosted log, the public page, the coworld list/detail, and reproduced the `POST /coworlds/replays/session` call, and inspected `viewer-smoke.png`, all before opening VERIFY.md.

## Per-item verdicts

### 1. ≥2 completed rounds after fillers set — TRUE
My own fetch of `GET /rounds?league_id=league_00dcb926…` returns r2 `round_3eabfb3f` (completed 01:54:20Z) and r3 `round_b1b9548f` (completed 02:09:03Z); r1 `round_972ecc54` `failed` with error `"Temporal RoundWorkflow failed before settling the round."` (quoted verbatim in VERIFY.md:61) and is correctly excluded. Decisive post-filler evidence: I fetched **both** counted rounds' episode-requests and both seated the filler policy-version UUIDs (`009fc22a…` rusher, `8dd54435…` sentry — matching STATE.policies.filler_version_ids) in 6 of 8 seats, which is only possible if fillers were registered before those episodes ran; the live `filler-policies` list in VERIFY.md:84-95 shows the same two UUIDs and neither champion.

### 2. Both champions ranked, fillers absent — TRUE
My own leaderboard fetch: exactly two rows — daveey rank 1 `vzd-pointman:v1` 1001.4695 rounds_played 2, daveey-1 rank 2 `vzd-crossfire:v1` 998.5305 rounds_played 2 — identical to VERIFY.md:130-131; fillers absent entirely.

### 3. Latest round's episode request completed with replay — TRUE
I reproduced the 405 on the flat route (`GET /episode-requests?round_id=…` → `{"detail":"Method Not Allowed"}`) and the nested `GET /rounds/round_b1b9548f…/episode-requests` returns `ereq_c9f0e294…` `completed` with `replay_url` `…/ca0f7fc8-….replay`; its `policy_version_ids` are champion pvids `d4fdd9d3…`/`3a4fba26…` at seats 0/1 plus the two filler pvids, matching VERIFY.md's participants table (daveey/daveey-1 `is_filler:false`, six filler seats `is_filler:true`).

### 4. Replay bytes valid and show the game — TRUE
I downloaded the replay (106,174 bytes, magic `COWLDVZD`), fetched `tools/replay_summary.py` (196 lines) from the repo myself and re-ran it: strict JSON parses; `protocol == "vizdoom-deathmatch/v1"`; `results.reason == "complete"`, `endRule == "full_time"` (the declared-acceptable `deadline` exception, design.md:342-347, was not needed); `frags [2,2,5,0,0,6,6,2]` sum 23; champion seats 0/1 have `results.policyKinds ["llm","llm"]`, `llmTurns [24,24]`, 48 LLM directives with varied intents (move_to/flank/hold/hunt/retreat) and substantive non-empty radio lines, `fallbackTurns` all zero, 0 fallback records — every number in VERIFY.md §4 matches my independent parse exactly.

### 5. Hosted game log clean — TRUE
I fetched `GET /episode-requests/ereq_c9f0e294…/artifacts/logs` with `X-Use-Elevated-Privileges: true` myself (102,931 bytes — same byte count VERIFY.md:301 reports) and ran the four-pattern grep on the raw body: zero matches → CLEAN. VERIFY.md additionally decoded the container reprs and greps both forms, plus corroborating tallies (48/48 Bedrock calls HTTP 200, matching the replay's 48 LLM directives 1:1).

### 6. Public page uses the static replay path — TRUE
I re-fetched `https://softmax.com/vizdoom-deathmatch` (720 KB, zero `<iframe` in SSR — client-rendered, as VERIFY.md records); the SSR flight payload embeds the featured playlist entry `vizdoom-deathmatch.r3.e1` ("from the round daveey took 1st from daveey-1", `aria-current="true"`, "On screen") pointing at the **same** replay URL as check 3 — featured match present. I reproduced `POST /coworlds/replays/session` verbatim and got the identical `viewer_url`: `https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_4e53e339…/sha256%3A1cb9398b…/index.html?v=2#replay=<s3 url>`, `ready:true` — the static route with the run's exact cow_id and manifest_sha (matches STATE.coworld), no `/client/replay` anywhere in the page or the API response.

### 7. Certification declared the static bundle — TRUE
The committed `runs/2026-08-27-vizdoom-deathmatch/release-result.json` line 11 reads `"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"` — contains the required prefix; the same line appears in `certify.output_tail`, `certify.ok:true`, `canonical:true`. VERIFY.md read the committed copy, as the prompt requires.

### 8. Viewer executed and judged — TRUE
(a) `loaded:true` via `data_replay_loaded:"true"` at 3,551 ms in the committed `viewer-check/viewer-smoke.json`; I verified run 33135119698 myself via the GitHub API: `viewer-check completed success`, created 2026-08-28T02:10:50Z, matching the dispatch narrative. (b) The three scrub readouts differ and advance monotonically (tick 0 → 966 → 1446; turns 1 → 9 → 14; frags 0/0 → 6/4 → 8/7). (c) The judgment paragraph is present, specific, and accurate against the committed png, which I inspected myself: legible top-down arena with red/blue cogs, tracer lines, "on it" speech bubbles, eight seat cards, headline `tick 1446/2592 · turn 14/24`, scorebug DAVEEY+BASELINE 8 frags vs DAVEEY-1+BASELINE 7, feed lines `RED-gamma: HOLD A1 / BLUE-gamma: HUNT RED-DELTA / RED-delta: HUNT BLUE-GAMMA / BLUE-delta: HUNT RED-DELTA` that reconcile seat-for-seat with turn 13's scripted directives in my own replay parse, and the starter's transport strip (`⟲ ◂| ▶ +5s |▸ ↻ ▸▸ spoilers` + tick-clock + speed chips — I confirmed the glyph row against `starters/coworld-ctf/client/replay_broadcast.html:1556-1568`) with the momentum graph relabelled `FRAG LEAD`. Starter chrome, not a rewrite.

## Rulings on the declared substitutions

- **(a) Nested episode-requests route — SOUND.** I reproduced the 405 on the flat query myself; the nested `/rounds/$R/episode-requests` returns the same resource for the same round, and VERIFY.md records the dead route with its http code rather than silently working around it.
- **(b) `replay_summary.py` for the strict-UTF-8 check — SOUND.** The design note declares exactly this substitute for exactly this check (design.md:1096-1107, "The phase-60 substitute for SPEC §Definition of done check 4"), with the reason (binary `COWLDVZD` is what the static wasm viewer parses; design.md:1083-1089). I re-ran the tool independently and every asserted value matches. The check's substance — parseable, protocol match, healthy reason, champions genuinely LLM-deciding, not all fallbacks — is fully established.
- **(c) SSR payload + replays/session API, `#replay=` fragment — SOUND.** The page is verifiably client-rendered (no iframe in 720 KB of SSR); the session API is what the page's own JS calls, and I reproduced it byte-identically. The fragment form is the platform's own delivery of the same static route with the correct cow_id and manifest_sha; the SPEC's operative prohibition (`/client/replay` pod URL) is not violated, and check 8 executed that exact URL successfully. VERIFY.md records the difference from the prompt's literal `?replay=` shape explicitly (VERIFY.md:417-421) rather than papering over it.
- **(d) Counting rounds 2 and 3 as post-filler — SOUND in substance,** with one wording defect noted below. The strongest evidence is not the log ordering but the platform's own record: the filler policy versions physically played in both counted rounds' episodes (verified by my own fetches of both ereqs), which entails registration before those rounds ran. Round 1's failure signature is the documented pre-filler Temporal failure and it is excluded, not counted.

## Refuted
None. Every factual claim in VERIFY.md that I re-checked reproduced exactly (round ids/timestamps/error string, leaderboard rows to full float precision, ereq id and participants, all replay numbers, hosted-log byte count and CLEAN grep, session-API viewer_url byte-for-byte, CI run conclusion, both file:line citations for the feed_lines explanation).

## Non-blocking observations
1. **VERIFY.md:115-116 wording is internally inconsistent:** it says rounds 2 (created 01:51:14Z) and 3 are "both strictly after the filler registration at 01:52:30Z" — 01:51:14Z is *before* 01:52:30Z. The 01:52:30Z is the batched log-write timestamp, not the filler POST time. The conclusion survives on the stronger evidence above, but the sentence as written proves the opposite of what it claims for round 2.
2. `replay_summary.py`'s **top-level** `policyKinds` is emitted in register-record order (`["scripted","scripted","llm",…]`), misaligned with the seat-ordered `names` array; the authoritative `results.policyKinds` is correct (`["llm","llm",…]`) and is what VERIFY.md quoted. Worth a one-line sort in the tool so a future verifier isn't briefly alarmed, as I was.
3. `results.finalTick` 2826 > `maxTicks` 2592 — explained by the design's `gameOverTicks = 240` display hold after full time (design.md:340-341); the viewer clock correctly caps at /2592.
4. VERIFY.md's own observations (feed selector missing `#killfeed` — both citations verified; scrub clicks undershooting 100 %; inherited "hill red=0 blue=0" log line; `ordersRejected[0]=1`; turn-23 friendly-target `hunt`) are accurate and correctly classified as non-blocking.

## Verifier report audit
| item | verifier said | I verified | agrees |
|---|---|---|---|
| 1 | rounds 2+3 completed, r1 failed pre-filler | same rounds/statuses/error via my own fetch; fillers seated in both counted rounds' episodes | yes |
| 2 | daveey #1 / daveey-1 #2, no filler rows | identical rows, full precision | yes |
| 3 | flat route 405; nested ereq completed with replay_url | reproduced both | yes |
| 4 | protocol/reason/frags/48 LLM/0 fallbacks via declared substitute | re-ran the tool; every number matches | yes |
| 5 | CLEAN, 102,931 bytes, 48/48 Bedrock 200s | my raw-body grep CLEAN, same byte count | yes |
| 6 | SSR featured match r3.e1 + session API static viewer_url | reproduced byte-identically | yes |
| 7 | committed release-result.json contains the liveness-skipped line | read it at release-result.json:11 | yes |
| 8 | loaded:true, 3 differing clocks, run 33135119698 success, judgment paragraph | GitHub API confirms success; json/png match; citations check out | yes |

BLOCKING: 0
