blocking: 0

# Phase-60 verdict — atari-57
Head: Metta-AI/cogame-atari-57 main@c8498ce · cow_4b06234f-97d8-4b65-8553-e2f967e89d8c v0.1.0
Checklist: prompts/60-verify.md (the eight checks) + docs/SPEC.md §Definition of done
Independent read written before reading VERIFY.md: yes — every API call, the S3 replay, the
hosted log, the session POST, the SSR payload, run 33216261052 and its artifact were re-fetched
by the judge before VERIFY.md was opened.

## Per-check adjudication (verifier's verdict → judge's verdict)

### 1. ≥2 completed rounds after fillers — TRUE → **AGREE**
Re-fetched `GET /rounds?league_id=league_942b4588…` at adjudication time: round 3
(`round_4441a16c…`, completed 22:14:55Z), round 2 (`round_ed18a4d8…`, completed 21:59:28Z),
round 1 (`round_f754b121…`, **failed**, error verbatim `Temporal RoundWorkflow failed before
settling the round.` — quoted in VERIFY.md L85 as required, excluded from the count), round 4
pending. Count of completed = 2. "After the fillers" is proven the strong way: I re-fetched both
counted rounds' episode requests — round 2 (`ereq_54a595a6…`) seats `d0712eac…` (hoover) and
`44a28876…` (arcader); round 3 (`ereq_c6f8d48c…`) seats hoover twice, `is_filler: true` — so the
fillers demonstrably existed before every counted round ran. I also re-fetched
`GET /leagues/$L/filler-policies`: exactly arcader:v1 + hoover:v1, matching VERIFY.md L97-102.

### 2. Both champions ranked — TRUE → **AGREE**
Re-fetched the division leaderboard (bare list): `1 daveey atari-57-highroller:v1
1030.5304984710244 2 2.0` / `2 daveey-1 atari-57-onecredit:v1 969.4695015289755 2 0.0` —
digit-for-digit what VERIFY.md L148-149 pastes. Both champions present, `rounds_played` 2 ≥ 1
each, exactly two rows, neither filler on the board.

### 3. Latest round's episode request — TRUE → **AGREE**
Note: the checklist's flat route `GET /episode-requests?round_id=` now returns
`405 Method Not Allowed` (I reproduced this); the verifier's nested
`GET /rounds/<id>/episode-requests` is the working route and is honestly documented
(VERIFY.md L163-165). Re-fetched `ereq_c6f8d48c…`: `status: "completed"`, `replay_url`
`…/replays/820b851b-….replay`, participants = daveey (highroller, pos 0), daveey-1 (onecredit,
pos 1), hoover ×2 (`is_filler: true`, pos 2/3), scores 38.4/13.6/13.3/13.3 — identical to
VERIFY.md's paste.

### 4. Replay bytes valid and show the game — TRUE, via the documented deviation → **AGREE, deviation ACCEPTED**
The deviation is genuinely design-declared, not improvised: design.md L1286-1290 pins the
replay as "the starter's **binary `COWLDA57`** format", L1294-1299 names
`tools/replay_summary.py` as the repo's forensics reader, and L1300-1308 spells out the
exact phase-60 substitute commands. The script (fetched by me from the repo at c8498ce)
self-declares in its docstring: "it is what phase 60 substitutes for SPEC §Definition of
done check 4" (tools/replay_summary.py:8-9), with `MAGIC = b"COWLDA57"`,
`PROTOCOL = "atari-57/v1"` (L24-25).
I re-ran the whole chain myself: S3 fetch → sha256
`0439459eb5c9ec9d97326535f5c4d52057abee8c7a2b8b04ec8fdac5dd0d7439`, **byte-identical to the
committed `ep.replay`** (73 374 B both); first 8 bytes `COWLDA57`; summary is strict-parser
JSON (`jq -e` exit 0); `protocol atari-57/v1`, `rom chomper`, `results.reason complete`,
`endRule full_time`, points sum 7 760 > 0; **38 LLM stances, `fallbacks: 0`**; seat 0 modes
{clear,hunt,safe,strike} across 6 zones, seat 1 modes {bank,clear,strike} — varying, non-constant,
non-trivial (turn-0/10/23 stance records I extracted match VERIFY.md's quotes verbatim).
Seat 1's 10 `scripted` turns (14-23, note "the credit is spent") are the **designed** lane-Over
drop, not degradation: design.md L495-497 — "If `lives == 0` → lane phase `Over` … this seat is
dropped from every later LLM batch"; `fallbackTurns == [0,0,0,0]`.

### 5. Hosted log clean — TRUE → **AGREE**
Re-fetched the elevated log myself (80 214 B, 4 containers as claimed). Raw grep for
`falling back|LLM provider is unavailable|cut off at max_tokens|rejected` → zero hits; I also
replicated the verifier's decode-the-`b'…'`-reprs method → zero hits. The verifier's
429-cross-check finding (the only `429` substring is inside a request UUID on an `ok:true,
status_code:200` record) is correct diligence. No platform-throttle exception needed.

### 6. Static replay path + featured match — TRUE, via the documented deviation → **AGREE, deviation ACCEPTED**
I reproduced all three sources myself: (a) raw-HTML grep of `https://softmax.com/atari-57`
finds no iframe (client-rendered — exactly what playbooks/observatory-api.md L329-331 records
platform-wide, including `featured_match: null` on `/coworlds`, which I also observed);
(b) the page's SSR payload contains `state.playlist[0]` = episode `4e814b9f…`, round 3, code
`atari-57.r3.e1`, `replayUrl` byte-identical to check 3's — **featured match present**;
(c) `POST /coworlds/replays/session` returned to me the byte-identical
`viewer_url` VERIFY.md pastes:
`…/v2/coworlds/replays/static/cow_4b06234f-…/sha256%3A81b1272cf2…/index.html?v=2#replay=<url-encoded s3 url>`,
`ready: true`. The `<sha>` equals STATE's `manifest_sha` (`sha256:81b1272cf2…`), the path is the
static route, no `/client/replay` anywhere. The `?v=2#replay=` fragment shape is documented as
current since 2026-08-28 (playbook L326). VERIFY.md records which source produced the verdict
(L488-490), as the checklist requires.

### 7. Certification declared the static bundle — TRUE → **AGREE**
Read the committed `runs/2026-08-28-atari-57/release-result.json` myself:
`.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared;
/client/replay and /replay not required)` — contains the required string verbatim;
`.certify.ok: true`. Source used is the committed artifact, not `/tmp`, as the checklist
requires.

### 8. Viewer executed and judged — TRUE → **AGREE**
Run 33216261052 (Metta-AI/coworld-builder, workflow viewer-check): I fetched it via the GitHub
API myself — `status: completed`, `conclusion: success`, created 2026-08-28T22:18:25Z. I
re-downloaded the `viewer-check` artifact and diffed: **committed `viewer-smoke.json` and
`viewer-smoke.png` are sha256-identical to the CI artifact** (json `c2127026…`, png `80cac7c4…`)
— the evidence is untampered. The artifact's own `url` field is byte-identical to the check-6
session `viewer_url`, so the run provably tested this coworld's live iframe src.
Gate (a): `loaded: true` at 2 984 ms via `data_replay_loaded: "true"`, `failure: null`. Gate
(b): the three scrub readouts differ on both axes — `2:00…TURN 1/24` / `1:00…TURN 13/24` /
`0:00…TURN 24/24`. Gate (c): the judgment paragraph exists (VERIFY.md L656-694) and I checked
it against the png myself: four chomper lanes with pellets, hunters and avatars; GAME OVER
banners on exactly the three lanes with `livesLeft == 0`; per-lane points 3730/1360/1330/1330
reconciling with `results.points` (the −10 on lane 0 is the scrub position 2875/2880 vs
`lastScoreTick` 3073 — the verifier's explanation is correct); scorebug with DAVEEY 38.300 /
DA… 13.600 / BA… 13.300 ×2; and the starter's chrome — transport strip (⟲ ◀ ▶ +5s ▶ ↻ ▶▶),
`spoilers` toggle, tick counter, 1×-16× speed ladder, scrubber with the four-trace momentum
graph, stance chips and feed. It is the coworld-ctf shell, not a gridlock-style rewrite. The
`feed_lines: 0` anomaly is honestly disclosed and correctly triaged: the png plainly shows a
four-line feed and chip row, so it is a probe-selector mismatch, not a missing feed —
phase-30-grade legibility observation, not a definition-of-done gate.

## Refuted verifier claims
None. Every pasted readout I re-fetched (rounds, leaderboard, episode request, filler list,
replay bytes, log, SSR payload, session POST, run conclusion, artifact bytes) reproduced
digit-for-digit. Nothing was overstated; the two deviations are both pre-documented (design.md
L1286-1311; playbook §Featured match) rather than post-hoc rationalizations.

## Non-blocking observations (not tied to a definition-of-done item)
- `feed_lines: 0` probe/selector mismatch — already flagged by the verifier; the feed renders.
- Tick-accounting curiosity: `results.finalTick == 3075` while config `maxTicks == 2880` and
  the viewer's counter shows `2875 / 2880` — the sim tick counter evidently includes non-clock
  phases (e.g. 24-tick Dying freezes) beyond the 2880 game-clock scale. Replay, hosted log
  (`credit spent — complete/full_time at tick 3075`) and viewer all agree with each other, the
  clock advances and the episode is `complete/full_time`, so no DoD item is touched; worth a
  line in learnings if the tick scale ever needs to be read forensically.

## Checklist pass (independent)
| # | item | status | evidence |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers | TRUE | rounds 2+3 completed (API re-fetch); fillers seated in both counted rounds' ereqs; r1 failed, error quoted |
| 2 | both champions ranked | TRUE | leaderboard re-fetch: daveey #1 (2 rounds), daveey-1 #2 (2 rounds); no fillers |
| 3 | latest round ereq completed + replay | TRUE | ereq_c6f8d48c… completed, replay_url present, participants correct (re-fetch) |
| 4 | replay valid, shows the game | TRUE | S3 bytes ≡ committed ep.replay (sha256); COWLDA57 → summary strict JSON; atari-57/v1, complete/full_time; 38 LLM / 0 fallback; design-declared substitute |
| 5 | hosted log clean | TRUE | 80 214 B re-fetched; raw and decoded greps both zero hits |
| 6 | static replay path + featured match | TRUE | session POST re-run: static route, manifest_hash sha, ?v=2#replay= (documented), ready:true; SSR playlist[0] present |
| 7 | cert declared static bundle | TRUE | committed release-result.json: required string verbatim |
| 8 | viewer executed + judged | TRUE | run 33216261052 success (API); artifact ≡ committed (sha256); loaded:true; 3 differing clocks; judgment paragraph checked against png |

## Verifier report audit
| claim | verifier said | I verified | agrees |
|---|---|---|---|
| completed-round count | 2 (rounds 2, 3) | API re-fetch: 2 | yes |
| r1 error verbatim | Temporal RoundWorkflow failed before settling the round. | identical | yes |
| leaderboard rows | 1030.5304984710244 / 969.4695015289755 | identical to the digit | yes |
| ereq status/replay/participants | completed, 820b851b…, daveey/daveey-1/hoover×2 | identical | yes |
| replay size/format | 73 374 B binary COWLDA57 | 73 374 B, magic verified, sha matches committed copy | yes |
| LLM/fallback counts | 38 / 0 | 38 / 0 from my own summary run | yes |
| seat-1 scripted turns = lane over | credit spent at tick 1834 | design.md L495-497 + stance notes "the credit is spent" | yes |
| log CLEAN | CLEAN (decoded) | CLEAN raw and decoded | yes |
| session viewer_url | static route, ?v=2#replay=, ready:true | byte-identical on my own POST | yes |
| cert liveness string | skipped (static replay bundle declared… | read committed file myself | yes |
| run 33216261052 | success, 35 s | API: completed/success, created 22:18:25Z | yes |
| committed viewer evidence | from run artifact | sha256-identical to re-downloaded artifact | yes |
| clock readouts | 2:00 / 1:00 / 0:00, turns 1/13/24 | identical in artifact json | yes |

No blocking items.

BLOCKING: 0
