# VERIFY — paintball, coworld version **0.1.3** (fetched 2026-08-25 18:11Z–18:13Z)

Verdict: **all 8 items TRUE.**

Checks 1–7 were re-fetched in this pass (18:11Z–18:13Z) and checks **3, 4 and 5 are pinned to
round 22** (`round_5494143d-a59c-426f-8cb8-8f5b0fe02aee`, completed 18:07:38Z), the latest
completed round. The earlier pass in this same phase (17:02Z–17:09Z, pinned to rounds 17/18) found
checks 4 and 5 false while the Bedrock daily-token quota was exhausted; that evidence is kept
below as **§Trend record** because it is what shows the difference is the quota window and not the
build. Nothing in this file rests on the 13:45Z (0.1.2) verify.

Two documented exceptions to "fetch fresh, every item, this run":
- **check 7** — the evidence is the committed `runs/2026-08-25-paintball/release-result.json`
  (phase 40's artifact copy), re-read from the working tree at 18:13:30Z;
- **check 8** — the rendered evidence is `viewer-check.yml` run **32875824479**, dispatched by me
  earlier in this phase (17:05:25Z) and committed under `runs/2026-08-25-paintball/viewer-check/`.
  It is not re-dispatched here because the bundle it rendered is byte-for-byte the bundle the page
  serves now: the static path re-fetched at 18:13:06Z carries the **same** `cow_09dcacad-…` and the
  **same** `sha256:669e79cd…`, and only the `?replay=` target moved. See check 8.

Ids under test:
- coworld `cow_09dcacad-01fb-488b-9d93-5eddf6a1a37a` v0.1.3,
  manifest `sha256:669e79cde247aa82428d6a26c7cfeb652b3cf89f492df9ee697ca3225a123f71`
- league `league_bd940066-00c4-4ade-87ae-06dac0818bc4`, division `div_97b4e1b9-6f9b-44ab-8583-73789a4ee057`
- champions `daveey → paintball-holdcentre:v2`, `daveey-1 → paintball-splitpaint:v2`
- fillers `paintball-holdline:v1`, `paintball-sprayer:v1`

Auth on every Observatory call: headers `Authorization: Bearer $SOFTMAX_TOKEN` and
`User-Agent: coworld-builder/1.0`; artifact reads additionally send
`X-Use-Elevated-Privileges: true`. Header **values are never printed**.
`BASE=https://softmax.com/api/observatory/v2`.

| # | Check | Verdict | Evidence pinned to |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | **TRUE** | 20 of 22 rounds completed; 11 of them on the 0.1.3 champions |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** | daveey rank 2, daveey-1 rank 3, 20 rounds each; fillers registered but absent |
| 3 | Latest round's episode completed with a replay | **TRUE** | round 22 · `ereq_d0bfc14c` (daveey vs daveey-1) |
| 4 | Replay bytes valid; champions really playing | **TRUE** | round 22 · 61 of 80 directives `llm`, 19 fallback (24 %), **0 scripted** |
| 5 | Hosted game log clean | **TRUE via SPEC item 5's exception branch** | round 22 · 39 matching lines, every one Bedrock-throttle-caused; cross-checked against collab_cooking 18:02:40Z |
| 6 | Public page featured match on the **static** replay path | **TRUE** | featured `paintball.r22.e5`, static path, `ready: true` |
| 7 | Certification declared the static bundle | **TRUE** | committed `release-result.json` (0.1.3) |
| 8 | Viewer actually renders and advances | **TRUE** | run 32875824479 — `loaded: true`, three differing clocks |

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

Fillers were registered at **12:48:11Z** (`log.md` line 47), before round 1 was triggered.

```
GET $BASE/rounds?league_id=league_bd940066-00c4-4ade-87ae-06dac0818bc4&limit=30
  headers: Authorization, User-Agent                          (fetched 18:11:26Z)
```

`jq -r '… | [.round_number,.id,.status,.created_at,.completed_at]|@tsv'` — tail of the list
(rounds 1–14 are in §Trend record and unchanged):

```
15	round_a297b9d9-be6a-4aab-b372-d81d422576c9	completed	2026-08-25T16:17:08.717323Z	2026-08-25T16:23:11.135440Z
16	round_c86242f5-1cab-47db-8d04-4c5dabfec952	completed	2026-08-25T16:32:10.142350Z	2026-08-25T16:36:44.330804Z
17	round_df0cb96e-c8d9-457d-8f03-cacb2071cc52	completed	2026-08-25T16:47:10.511574Z	2026-08-25T16:52:15.257563Z
18	round_6effd321-1b70-45f0-a390-acaf7a2e01ef	completed	2026-08-25T17:02:49.788948Z	2026-08-25T17:07:26.336477Z
19	round_8d17a529-d595-4ffc-b41b-22de4655f1df	completed	2026-08-25T17:17:50.665948Z	2026-08-25T17:23:48.358461Z
20	round_1714d7c7-59aa-4a02-b42e-9467862b3cf4	completed	2026-08-25T17:32:51.333898Z	2026-08-25T17:39:41.413069Z
21	round_33ea46be-6666-456e-b237-2f320e086002	failed	2026-08-25T17:47:52.653886Z	2026-08-25T17:52:50.081367Z
22	round_5494143d-a59c-426f-8cb8-8f5b0fe02aee	completed	2026-08-25T18:02:53.045456Z	2026-08-25T18:07:38.880302Z
```

`jq '[…|select(.status=="completed")]|length'` → **20**.

The two non-completed rounds, `error` verbatim:

```
11	failed	only 4/6 planned slots produced scoring evidence; the round requires at most 0% of planned slots failed
21	failed	only 5/6 planned slots produced scoring evidence; the round requires at most 0% of planned slots failed
```

Failed rounds do not count toward this check.

Rounds carrying the **0.1.3** champions (`policy_version_id f07e43ed-…` = `paintball-holdcentre:v2`
in `round_config.entrant_attributions`) are 10 through 22; of those, **11 completed**
(10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22).

Status: **TRUE** — 20 completed rounds, all after the fillers were set at 12:48:11Z, 11 of them on
the 0.1.3 build.

---

## 2. Both champions ranked; fillers absent or Baseline — TRUE

```
GET $BASE/divisions/div_97b4e1b9-6f9b-44ab-8583-73789a4ee057/leaderboard
  headers: Authorization, User-Agent                          (fetched 18:11:27Z)
```

Bare list. `jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'`:

```
1	richard	co-gas-paintball-holdline-richard:v1	1166.519026118595	15	37.0
2	daveey	paintball-holdcentre:v2	1053.1195160214138	20	25.0
3	daveey-1	paintball-splitpaint:v2	957.9276290521693	20	23.0
4	relh	co-gas-paintball-holdline-relhalpha:v2	822.4338288078224	15	9.0
```

Both champions present at **v2** (the 0.1.3 build) with `rounds_played = 20` each; daveey has
climbed to rank 2 since the 17:02Z fetch. `richard` and `relh` are external players who joined the
open ladder with their own policies — expected, not fillers.

Fillers are absent from the leaderboard and still registered (this read needs the elevated header):

```
GET $BASE/leagues/league_bd940066-.../filler-policies
  headers: Authorization, User-Agent, X-Use-Elevated-Privileges  → HTTP 200 (fetched 17:08:56Z)
```
```json
{"filler_policy_versions": [
  {"policy_version_id": "b39fb2e0-2feb-4c33-b764-4d7b82a0788b", "policy_name": "paintball-holdline",
   "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"},
  {"policy_version_id": "f24ea073-f96e-4022-940b-1d7a8a52f7f9", "policy_name": "paintball-sprayer",
   "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"}]}
```

Both filler version ids differ from the champions' (`f07e43ed-…`, `83ba1515-…`). Neither filler
name appears in the 18:11:27Z leaderboard above.

Status: **TRUE** — daveey and daveey-1 both ranked with 20 rounds played; fillers registered,
distinct from the champions, and absent from the leaderboard.

---

## 3. Latest round's episode request completed with a replay — TRUE

Latest completed round: **22**, `round_5494143d-a59c-426f-8cb8-8f5b0fe02aee`, completed
18:07:38.880302Z (round 21 failed; see check 1).

```
GET $BASE/episode-requests?round_id=round_5494143d-a59c-426f-8cb8-8f5b0fe02aee&limit=20
  headers: Authorization, User-Agent                          (fetched 18:11:35Z)
```
```
ereq_466403bd-fc45-4e16-8131-8c9c6d1744fa	completed	daveey-1 vs richard
ereq_f22c7703-69b4-4e2e-a4a4-f259093e1f57	completed	daveey vs richard
ereq_d0bfc14c-9992-4aea-aeab-27d03a34dca6	completed	daveey vs daveey-1
ereq_1f510ac1-1c29-4239-89f5-0565ddd5c2b2	completed	relh vs richard
ereq_a111d275-c184-4604-bf9d-7904f61b4c55	completed	relh vs daveey-1
ereq_d3674ea3-9726-41f8-a751-ec8870dd81fc	completed	relh vs daveey
```

The round holds **six** episode requests because two external players joined the ladder.
**I selected `ereq_d0bfc14c-9992-4aea-aeab-27d03a34dca6`** — the champion-vs-champion episode —
because it is the only one of the six whose two participants are the champions this run owns
(`daveey` and `daveey-1`), which is what checks 3–5 are about; every other pairing seats an
external player's policy on one side.

```
GET $BASE/episode-requests/ereq_d0bfc14c-9992-4aea-aeab-27d03a34dca6
  headers: Authorization, User-Agent                          (fetched 18:11:41Z)
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/035e0bfe-cf7d-4e3f-bc33-81381ed1ee77.replay",
  "participants": [
    {"position": 0, "policy_name": "paintball-holdcentre", "version": 2,
     "player_name": "daveey", "is_filler": false},
    {"position": 1, "policy_name": "paintball-splitpaint", "version": 2,
     "player_name": "daveey-1", "is_filler": false}
  ],
  "participant_scores": [{"position": 0, "score": 0.529}, {"position": 1, "score": 0.471}]
}
```

Status: **TRUE** — `completed`, non-null `replay_url`, participants exactly `daveey`
(holdcentre:v2) and `daveey-1` (splitpaint:v2), neither a filler.

---

## 4. Replay bytes valid and showing the game — TRUE

The paintball replay is **binary** (`COWLDPNT` magic), so `jq` on the raw bytes fails by design.
The design note (§Replay bytes, "The phase-60 substitute for SPEC §Definition of done check 4")
prescribes `tools/replay_summary.py`, which prints one strict-UTF-8 JSON object. Repo cloned fresh
this phase at `main` = `2a58c99`.

```
curl -sSL https://softmax-public.s3.amazonaws.com/replays/035e0bfe-cf7d-4e3f-bc33-81381ed1ee77.replay -o ep22.replay
→ HTTP 200 bytes 148306                                       (fetched 18:11:50Z)
python3 tools/replay_summary.py ep22.replay > ep22.json
jq -e . ep22.json  → strict UTF-8 JSON: ok
jq -r '.protocol, .gameVersion'  → paintball/v1
                                    1
```

`protocol == "paintball/v1"` matches the manifest.

`jq -r '.results'` — decoded from the replay's own `result` control record (fix `d8f05e0`), not
from the platform:

```json
{"names":["daveey","daveey-1"],"scores":[0.529,0.471],"win":[true,false],"team":["red","blue"],
 "residentScore":[0.559,0.441],"visitorScore":[0.5,0.5],"hillTicks":[103,18],
 "residentHillTicks":[103,18],"visitorHillTicks":[0,0],"paintTiles":[134,108],
 "tagsDealt":[16,13],"tagsTaken":[17,12],"llmTurns":[30,31],"fallbackTurns":[10,9],
 "reason":"complete","endRule":"full_time","games":2,"finalTick":4924,"seed":1378798727}
```

`results.reason == "complete"` with `endRule == "full_time"` — **the normal ending** in design.md's
table (both games played their 2160 ticks); no `deadline` exception is needed.

Cross-check against the hosted artifact:

```
GET $BASE/episode-requests/ereq_d0bfc14c-.../artifacts/results
  headers: Authorization, User-Agent, X-Use-Elevated-Privileges → HTTP 200, 418 bytes (18:12:06Z)
python3 -c "…json.load(results22.json) == json.load(ep22.json)['results']"  → identical: True
```

The `result` record in the S3 bytes is **identical** to the hosted results document — the replay is
self-sufficient, which is what 0.1.2 lacked.

Both seats registered as **LLM** policies — the `register` control records in the same bytes:

```json
[{"k":"register","seat":1,"team":"blue","policy":"splitpaint","kind":"llm","baseline":"holdline"},
 {"k":"register","seat":0,"team":"red","policy":"holdcentre","kind":"llm","baseline":"holdline"}]
```

Directive sources, per seat
(`jq '[.directives[]|{seat,source}]|group_by(.seat)|map({seat, llm, fallback, scripted})'`):

```json
[{"seat": 0, "llm": 30, "fallback": 10, "scripted": 0},
 {"seat": 1, "llm": 31, "fallback": 9,  "scripted": 0}]
```

`jq -r '.directives|length'` → `80` · `jq -r '.fallbacks'` → `39` (fallback *records*; 19 turns
ended on a fallback directive) · `jq -r '.budgetGuards'` → `0` (the budget guard never fired).

- **61 of 80 directives (76 %) are `llm`**; fallbacks are 19 of 80 (**24 %**) — a clear minority,
  and the results document agrees (`llmTurns [30,31]`, `fallbackTurns [10,9]`).
- **Zero `scripted` directives on either champion seat** — the 0.1.3 registration fix (`d3ee912`)
  holds; a scripted policy seated as a champion would be a failure state and there is none.
- Mean LLM latency 2842 ms, inside the 6000 ms attempt-1 deadline.
- The 19 fallback turns are scattered, not a block:
  `g1t0s1 g1t1s0 g1t1s1 g1t9s0 g1t11s1 g1t19s0 g2t0s1 g2t1s1 g2t2s0 g2t4s0 g2t5s0 g2t6s0 g2t6s1
  g2t7s0 g2t10s0 g2t10s1 g2t11s0 g2t11s1 g2t13s1`.

The LLM directives carry **non-trivial, situational content** — first turn, mid-episode and last
turn:

```
game 1 turn 0  seat 0 llm 5999ms  "Game start: all cogs moving to hill. Alpha closest, holds hill centre. Beta paints hill edge. Gamma guards left flank. Delta paints reinforcement path."
game 1 turn 10 seat 0 llm 2604ms  "Alpha down, gamma on enemy paint near hill. Beta + gamma paint hill edges simultaneously. Delta guards west flank with paint lane back."
game 1 turn 10 seat 1 llm 2604ms  "Two cogs dead; alpha alive far away. Hunt RED-gamma (nearest, on hill) with alpha. Hold hill with alpha (closest alive to hill). Gamma paint_path toward enemy h…"
game 2 turn 19 seat 0 llm 3294ms  "Own 76%, need 4% more. Alpha closest to hill at 75px - HOLD_HILL at centre. Defend the north edge where all 4 blues cluster."
game 2 turn 19 seat 1 llm 3294ms  "RED-beta at 1 HP is critical. Close and spray. Own hold cog must defend hill."
```

and they compile into real per-cog orders and in-game shouts (game 1 turn 10):

```
seat 0 llm  RED-alpha:paint_hill/"paint"  RED-beta:paint_hill/"Paint W"  RED-gamma:paint_hill/"Paint E"  RED-delta:guard/"Guard W"
seat 1 llm  BLUE-alpha:hunt/"Hunt!"  BLUE-beta:hunt/"Hunt!"  BLUE-gamma:hold_hill/"Hold!"  BLUE-delta:hunt/"Hunt!"
```

These are the game's own intents (`paint_hill`, `hold_hill`, `hunt`, `guard`, `paint_path`) applied
to the hill and to named enemies — the champion seats doing the thing the game is about, with the
hill actually changing hands (`hillTicks [103,18]`, `paintTiles [134,108]`, `tagsDealt [16,13]`).

Status: **TRUE** — strict-UTF-8 JSON, `protocol paintball/v1`, `complete`/`full_time`, the result
record inside the bytes matching the hosted artifact, zero scripted directives on a champion seat,
and LLM directives a 76 % majority with substantive content. SPEC item 4's bar ("non-scripted
decisions with non-trivial content; not all fallbacks") is met.

---

## 5. Hosted game log — TRUE, via SPEC item 5's **exception branch**

SPEC §Definition of done item 5, verbatim:

> 5. Hosted game log (`/episode-requests/<id>/artifacts/logs`, elevated header): zero lines
>    matching `falling back|LLM provider is unavailable|cut off at max_tokens|rejected` —
>    **or a documented platform-wide cause checked against another LLM coworld.**

The first branch is **not** satisfied (39 matching lines). The check is satisfied by the **second
branch**, and the paragraphs below are that documentation: every one of the 39 lines traces to the
platform-wide Bedrock daily-token throttle, none to a paintball-side cause, and the cross-check
against another LLM coworld was made in this same session.

The logs body is python `b'…'` reprs under `===== container: … =====` headers; every repr was
`ast.literal_eval`-decoded before grepping (a line-based grep on the raw body undercounts badly).

```
GET $BASE/episode-requests/ereq_d0bfc14c-9992-4aea-aeab-27d03a34dca6/artifacts/logs
  headers: Authorization, User-Agent, X-Use-Elevated-Privileges
→ HTTP 200 bytes 177586, 1063 decoded lines                   (fetched 18:12:15Z)
grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' <decoded>
```
```
falling back                   39
LLM provider is unavailable     0
cut off at max_tokens           0
rejected                        0
```

**Every matching line, classified by cause** (regex over the decoded text):

```
attempt-failure lines (20):
   18 × 'llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}'
    1 × 'anthropic error 503: {"message":"Bedrock is unable to process your request."}'
    1 × 'llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke'
fallback lines (19):
   19 × 'falling back to holdline (throttled)'      ← cause 'throttled' for all 19; zero parse_error,
                                                      zero timeout, zero no_credentials, zero budget_guard
```

Verbatim samples:

```
[game] paintball llm: seat 1 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
[game] paintball llm: seat 1 attempt 2 failed, falling back if it fails again: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
[game] paintball llm: seat 1 falling back to holdline (throttled) on turn 0
[game] paintball llm: seat 0 attempt 1 failed, falling back if it fails again: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
[game] paintball llm: seat 1 attempt 1 failed, falling back if it fails again: anthropic error 503: {"message":"Bedrock is unable to process your request."}
[game] paintball llm: seat 1 falling back to holdline (throttled) on turn 13
```

The single non-429 attempt line is a transport timeout against **`http://127.0.0.1:9100`** — the
platform's own injected Bedrock sidecar, not an external endpoint; the same turn's attempt 2 came
back `429 Too many tokens per day` and the turn's recorded cause is `throttled`. The 503 line is
the sidecar relaying Bedrock's own `503 Service Unavailable`, visible in the sidecar container in
the same log:

```
[bedrock-sidecar] 2026-08-25 18:03:18,373 INFO httpx HTTP Request: POST https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke "HTTP/1.1 503 Service Unavailable"
```

The sidecar's structured record of a throttled call in this very episode:

```json
{"timestamp": "2026-08-25T18:03:16.038951Z",
 "episode_request_id": "d0bfc14c-9992-4aea-aeab-27d03a34dca6",
 "model": "global.anthropic.claude-haiku-4-5-20251001-v1:0", "operation": "InvokeModel",
 "ok": false, "status_code": 429, "error_kind": "upstream_client",
 "error_type": "ThrottlingException",
 "message": "Too many tokens per day, please wait before trying again.", "latency_ms": 55.87}
```

**Nothing paintball-side appears.** Zero `cut off at max_tokens` (the 900-token setting holds),
zero `rejected`, zero `LLM provider is unavailable`, zero `parse_error` fallbacks, zero scripted
directives on a champion seat, and no sonnet-4-5 timeout cascade (the 0.1.2 amplifier removed by
`f317951`; the model line in the log is `paintball llm: bedrock transport, model
us.anthropic.claude-haiku-4-5-20251001-v1:0`, haiku only).

### Cross-check against another LLM coworld — same session

`collab_cooking` (`cow_19938c0f-195a-45f8-95da-761f0ffe04cb`), its **latest** episode
`ereq_47c45455-8e0c-4916-9c5c-42e01a05c3d1` (created 17:57:48Z, completed **18:02:40Z** — running
during paintball's round 22), logs fetched at 18:12:35Z with the elevated header (HTTP 200,
93951 bytes, 418 decoded lines):

```
Too many tokens per day: 10     ThrottlingException: 5     429: 16     falling back: 0
```
```json
{"timestamp": "2026-08-25T17:58:51.089594Z",
 "episode_request_id": "47c45455-8e0c-4916-9c5c-42e01a05c3d1",
 "model": "global.anthropic.claude-haiku-4-5-20251001-v1:0", "operation": "InvokeModel",
 "ok": false, "status_code": 429, "error_kind": "upstream_client",
 "error_type": "ThrottlingException",
 "message": "Too many tokens per day, please wait before trying again.", "latency_ms": 76.73}
```

Same sidecar, same model string, same `ThrottlingException` / "Too many tokens per day" —
a different coworld, a different game, the same platform quota, in the same minutes.
(`collab_cooking` shows 0 `falling back` lines only because its game code does not print that
phrase; the 429s are in the shared `bedrock-sidecar` container.)

**One-line justification.** *All 39 matching lines are the platform-wide Bedrock daily-token
throttle — 19 of 19 fallbacks recorded `cause: throttled`, the only two non-429 lines are the
sidecar's own 503 and a timeout to the sidecar's local port on a turn whose retry returned 429 —
and collab_cooking's latest episode, completed 18:02:40Z, shows the identical
`ThrottlingException: Too many tokens per day` from the same sidecar and model, so the cause is
platform-wide and documented, which is exactly SPEC item 5's second branch.*

Status: **TRUE** under SPEC §Definition of done item 5's exception branch ("or a documented
platform-wide cause checked against another LLM coworld"). The first branch (zero lines) is not
met and I do not claim it. Trend note: the same grep returned 112 lines in round 18 (17:07Z) and
22 in round 17 — the throttle is easing, and paintball's LLM-turn share rose from 26 % to 76 % on
the identical build.

---

## 6. The public page uses the static replay path — TRUE

```
curl -sS https://softmax.com/paintball            → HTTP 200, 581828 bytes   (fetched 18:12:55Z)
grep -o '<iframe[^>]*src="[^"]*"'                 → no match
```

The iframe is client-rendered, so per `prompts/60-verify.md` check 6 and
`playbooks/observatory-api.md` §Featured match I used the **second source**: the page's own SSR
payload (`state.playlist[0]`) plus the session call the page's JS makes. Which source was used:
**the SSR payload + `POST /coworlds/replays/session`**, both pasted below.

`state.playlist[0]` (unescaped from the page bytes) — the featured match has **moved forward** to a
round-22 episode since the 17:05Z fetch:

```json
{"episodeId":"80b52540-4122-4f03-97a0-c2daa41a04bf",
 "coworldId":"cow_09dcacad-01fb-488b-9d93-5eddf6a1a37a",
 "coworldName":"paintball","coworldVersion":"0.1.3",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/85c3c3a2-15a7-415d-bfcc-a31dad221e90.replay",
 "finishedAt":"2026-08-25T18:06:38.541046Z","roundNumber":22,"episodeNumber":5,
 "code":"paintball.r22.e5",
 "matchup":{"divisionId":"div_97b4e1b9-6f9b-44ab-8583-73789a4ee057","divisionName":"Competition",
   "first":{"rank":1,"player_name":"richard","score":1166.519026118595,
            "policy_label":"co-gas-paintball-holdline-richard:v1"},
   "second":{"rank":2,"player_name":"daveey","score":1053.1195160214138,"rounds_played":20,
             "episode_wins":25,"policy_label":"paintball-holdcentre:v2"}},
 "inspectUrl":"…detail=episode-request:ereq_f22c7703-69b4-4e2e-a4a4-f259093e1f57","outcome":"second"}
```

A featured match **is** present, it is a **0.1.3** episode (`coworldId` = the 0.1.3 cow id,
`coworldVersion` `0.1.3`), and it is from the latest completed round (22).

```
POST $BASE/coworlds/replays/session
  headers: Authorization, User-Agent, content-type
  body: {"coworld_id":"cow_09dcacad-01fb-488b-9d93-5eddf6a1a37a",
         "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/85c3c3a2-15a7-415d-bfcc-a31dad221e90.replay"}
→ HTTP 200                                                     (fetched 18:13:06Z)
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_09dcacad-01fb-488b-9d93-5eddf6a1a37a/sha256%3A669e79cde247aa82428d6a26c7cfeb652b3cf89f492df9ee697ca3225a123f71/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F85c3c3a2-15a7-415d-bfcc-a31dad221e90.replay&v=2",
  "ready": true
}
```

Field by field: `/v2/coworlds/replays/**static**/` ✓ ·
`cow_09dcacad-01fb-488b-9d93-5eddf6a1a37a` = STATE's 0.1.3 cow id ✓ ·
`sha256%3A669e79cde247aa82428d6a26c7cfeb652b3cf89f492df9ee697ca3225a123f71` = the 0.1.3 manifest
sha ✓ · ends `/index.html?replay=<s3 url>` ✓ · **no `/client/replay` anywhere** ✓ · `ready: true` ✓.

Status: **TRUE** — featured match `paintball.r22.e5` on coworld 0.1.3, served from the static
bundle at the unchanged cow id and manifest sha.

---

## 7. Certification declared the static bundle — TRUE

Source read: the **committed** `runs/2026-08-25-paintball/release-result.json` (phase 40's artifact
copy, committed in `92e02c5` "paintball: 0.1.3 released after the phase-60 fix round",
2026-08-25 14:46:40Z), re-read from the working tree at 18:13:30Z. It was present; no re-download
was needed.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-25-paintball/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Same file, the identifying fields:

```json
{"version": "0.1.3", "ok": true,
 "cow_id": "cow_09dcacad-01fb-488b-9d93-5eddf6a1a37a",
 "manifest_sha": "sha256:669e79cde247aa82428d6a26c7cfeb652b3cf89f492df9ee697ca3225a123f71",
 "step_failed": null, "certify_ok": true}
```

`certify.output_tail` shows all ten transcript steps passed, including
`[pass] replay-loadable: the replay artifact has a declared viewer path` and `[pass] players-run`,
ending `Certified dist/coworld_manifest.json`.

Status: **TRUE** — the required string is present in the release artifact for exactly the cow id
and manifest sha under test.

---

## 8. The viewer was EXECUTED, and it renders and advances — TRUE

**Rendered evidence: `viewer-check.yml` run 32875824479**, dispatched by me at 17:05:25Z in this
phase against the then-current featured `viewer_url`, artifacts committed under
`runs/2026-08-25-paintball/viewer-check/` (top level and `attempt-32875824479/`).

**Why it is not re-dispatched in this pass:** what check 8 executes is the **bundle**, addressed by
`<cow_id>/<manifest sha>`. The path re-fetched at 18:13:06Z (check 6) is
`…/static/cow_09dcacad-01fb-488b-9d93-5eddf6a1a37a/sha256%3A669e79cde247aa82428d6a26c7cfeb652b3cf89f492df9ee697ca3225a123f71/index.html`
— **the same cow id and the same manifest sha** as the URL that was rendered; only the `?replay=`
query moved from `b1b22848…` (r17.e6) to `85c3c3a2…` (r22.e5). No release happened between the two
fetches (`release-result.json` still reports 0.1.3 / the same sha, check 7), so the executed bytes
are the served bytes.

Dispatch and run selection (by creation time newer than the dispatch, never `-L 1` blind):

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_09dcacad-01fb-488b-9d93-5eddf6a1a37a/sha256%3A669e79cde247aa82428d6a26c7cfeb652b3cf89f492df9ee697ca3225a123f71/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fb1b22848-79d4-4118-a5e8-341cd0ec42f8.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=120
# dispatched 17:05:25Z
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10
32875824479	2026-08-25T17:05:27Z	in_progress	workflow_dispatch     ← newer than the 17:05:25Z dispatch
32868690580	2026-08-25T15:54:30Z	completed	workflow_dispatch
gh run view 32875824479 → {"conclusion":"success","createdAt":"2026-08-25T17:05:27Z","status":"completed"}
gh run download 32875824479 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-25-paintball/viewer-check
```

`jq -c '{loaded, ms, clock, scorebug, feed_lines}' viewer-smoke.json` — verbatim:

```json
{"loaded":true,"ms":4450,"clock":"1:30 TIME LEFT GAME 1/2 · RESIDENT · TURN 1/20","scorebug":"0% RED HILL 0:00 0 TAGS · 4 UP 1:30 TIME LEFT GAME 1/2 · RESIDENT · TURN 1/20 0% BLUE HILL 0:00 0 TAGS · 4 UP","feed_lines":0}
```

`jq -c '.signals'`:

```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

`jq -r '.failure // "no failure"'` → `no failure`.
`jq -c '.canvas_text'` → `{"total":0,"outside":0,"ellipsized":0,"never_inside":0,…}` (the board is a
wasm canvas; the chrome text is DOM, so nothing is drawn through the instrumented text API).

The three scrub readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | clock readout |
|---|---|
| 0 % | `1:30 TIME LEFT GAME 1/2 · RESIDENT · TURN 1/20` |
| 50 % | `1:15 TIME LEFT GAME 1/2 · RESIDENT · TURN 4/20` |
| 100 % | `0:55 TIME LEFT GAME 1/2 · RESIDENT · TURN 8/20` |

All **three differ** and advance monotonically (turn 1 → 4 → 8; the screenshot taken after the last
readout shows the tick counter at `847 / 4614`). `loaded: true` came from
`data-replay-loaded="true"` on `<html>`, which the shell sets only after the Worker's first frame
reached BroadcastCore. First frame at **4450 ms**.

Status: **TRUE** — `loaded: true` **and** three differing clock readouts.

Two observations for the coordinator (neither affects the verdict):

1. **The seek lags its target.** `viewer_smoke.mjs` clicks `#scrub` and reads 700 ms later
   (`templates/tools/ci/viewer_smoke.mjs`, the scrub block). The 50 % click landed at tick ~360 of
   4614 and the 100 % click at tick 847 — the 0.1.3 bounded `SeekTicksPerFrame` convergence (fix
   `6ffead7`) is still converging when the sample is taken. Motion is proven, but a spectator
   dragging to the end of a 4614-tick episode waits seconds for the picture to arrive rather than
   jumping. A legibility item for a later pass; it is a large improvement on 0.1.2, where two of
   the three readouts were identical.
2. **`feed_lines: 0` is a selector mismatch, not an empty feed.** The smoke script counts children
   of `#feed, .feed, #log`; paintball's chrome (inherited from coworld-ctf) renders the match feed
   into `#killfeed` and the command lines into `#bannerlane`. The screenshot shows four populated
   feed rows, so the readout is a false zero.

### Spectator judgment

**`viewer-smoke.png` (896 KB, committed) shows a real, legible paintball match, and it is the
starter's chrome.** Top strip: the scorebug — a red `76%` coverage chip, `0:00 HILL RED`,
`12 TAGS · 4 UP` with four red life pips on the left; the centre clock column `0:55 / TIME LEFT /
GAME 1/2 · RESIDENT · TURN 8/20`; and the mirrored blue plate on the right (`BLUE HILL 0:00`,
`9 TAGS · 4 UP`, `23%`). The regime is on screen at all times, as the design demands. The board
fills the frame: the hand-tuned arena with its spinning diamonds, glass stubs and two team spawn
discs, and — the thing the game is about — **the floor is visibly two-thirds painted**, a large red
territory across the west and centre-left and a blue one across the east, with a contested seam
through the middle where a white spray cone is firing. Eight cogs are drawn as real sprites with
intent shout bubbles above them (`HILL`, `PAINT`, `HUNT`, `TAGT`, `watch`, `paint`, `fold`), several
lying tagged out. Under the board the feed carries the commander lines in plain language:
`RED command: ALPHA DEAD. DELTA ON ENEMY PAINT→PROMOTE TO PAINT_HILL. BETA+GAMMA HUNT BLUE-ALPHA
(NEAREST, CLOSEST TO HILL). HOLD HILL WITH FALLBACK COG.` and `…GAMMA CLOSEST TO HILL (285 VS 471).
ALPHA DEAD, GAMMA DEAD (0HP). BETA NEAR HILL ON OWN PAINT - KEEP IT THERE AS ANCHOR. DELTA PROMOTE
TO PAINT_HILL TARGET`, against `BLUE command: HOLD THE HILL` twice. Below that the full transport
strip — restart, step-back, play, `+5s`, step, loop, fast-forward, a `spoilers` toggle, the tick
readout `847 / 4614` and the speed ladder `1× 2× 3× 4× 8× 16×` — and beneath it the scrubber with
the momentum graph.

**Reconciled against the record.** The rendered replay is `b1b22848-…` (`paintball.r17.e6`,
`ereq_3200f97b`), fetched and summarised in this phase: `protocol paintball/v1`, register records
`seat 0 = splitpaint (kind llm, red)` and `seat 1 = holdline (kind scripted, blue)` — daveey-1's
champion against external player richard's scripted baseline. Its directive stream at exactly the
rendered moment matches the two feed lines **verbatim**:

```
game 1 turn 6 seat 0 llm 2129ms  "Alpha dead. Delta on enemy paint→promote to paint_hill. Beta+Gamma hunt BLUE-alpha (nearest, closest to hill). Hold hill with fallback cog."
game 1 turn 7 seat 0 llm 2715ms  "BLUE-gamma closest to hill (285 vs 471). Alpha dead, Gamma dead (0hp). Beta near hill on own paint - keep it there as anchor. Delta promote to paint_hill target"
game 1 turn 7 seat 1 scripted    "hold the hill"
```

and the cog bubbles match the same turn's per-cog `say` fields
(`RED-alpha:hunt/HUNT  RED-beta:hold_hill/HOLD  RED-gamma:hunt/HUNT  RED-delta:paint_hill/PAINT`
against `BLUE-alpha:hunt/"on it"  BLUE-beta:guard/"watch"  BLUE-gamma:paint_hill/"paint"
BLUE-delta:paint_hill/"paint"`). Early and late ends of the same stream (`game 1 turn 0` seat 0
`fallback "hold the hill"`; `game 2 turn 19` seat 0 llm *"5 sec left, hill 57% ours. Alpha on enemy
paint—promote to paint_hill now to flip it back…"*) and the episode's result record
(`hillTicks [23,212]`, `paintTiles [119,129]`, `tagsDealt [13,20]`, `reason complete`,
`endRule mercy`, `llmTurns [35,0]`, `fallbackTurns [4,0]`) agree with what the picture shows: a
lopsided paint fight in which blue banks the hill time. The picture is not empty, not frozen and
not unreadable. The round-22 episode verified in checks 3–5 is the same game with both seats on LLM
policies and a 76 % LLM-directive share, so the spectator experience there is at least as rich.

**Chrome provenance:** it is the starter's. The transport strip, the `spoilers` toggle, the tick
`n / total` readout, the speed ladder, the two-plate scorebug with life pips, the banner-lane feed
and the momentum bar are the coworld-ctf/paintbot layout with paintball's numbers substituted into
the plates — not a rewrite that reuses the ids (the cogame-gridlock failure). `#viewpanel` /
minimap / zoombar are absent as the design says they should be. Two cosmetic snags worth logging:
the momentum bar is still captioned **`LIVES LEAD`** (design §Viewer 6 retargets that series to the
hill-tick difference — the series is retargeted, the caption was not), and the endcard could not be
judged because the sampled frame is mid-game. Neither is a blocker.

**Command feed: real LLM commands, not wall-to-wall fallbacks.** Every RED command line in the
picture is an LLM directive with specific, situational content (35 of 39 seat-0 directives are
`llm`). The blue "HOLD THE HILL" lines are *correct*: that seat is richard's **scripted** `holdline`
policy, whose fixed note is "hold the hill", not a paintball fallback.

---

## Trend record — the same checks earlier in this phase (evidence fetched 17:02Z–17:09Z)

Kept because it is what distinguishes a quota window from a broken build: **the build did not
change between these rows.** Same coworld 0.1.3, same manifest sha, same champion policy versions
(`f07e43ed…` / `83ba1515…`).

| Round | Champion-vs-champion episode | completed | `llmTurns` | `fallbackTurns` | scripted on a champion seat | `reason`/`endRule` | log lines matching the grep |
|---|---|---|---|---|---|---|---|
| 17 | `ereq_2bae9f12-8015-4d7f-95f2-373c655a7f6a` | 16:52Z | [33, 33] | [5, 5] | 0 | complete / mercy | 22 (19 throttle/503, 3 one parse_error) |
| 18 | `ereq_705b8fb6-9973-47d6-bd43-9037dddcd723` | 17:07Z | [9, 11] | [29, 27] | 0 | complete / mercy | 112 (111 throttle, 1 parse attempt that recovered) |
| **22** | **`ereq_d0bfc14c-9992-4aea-aeab-27d03a34dca6`** | **18:07Z** | **[30, 31]** | **[10, 9]** | **0** | **complete / full_time** | **39 (all throttle-caused)** |

Round 17 replay `f98e5584-…` (143513 bytes) and round 18 replay `3365b4ec-…` (145981 bytes) were
both fetched from S3 in this phase, both parsed strict-UTF-8 by `tools/replay_summary.py`, both
`protocol paintball/v1`, both with a `result` record in the bytes and zero scripted champion
directives. Round 18 was the one round where fallbacks were a **majority** (56 of 76, 74 %) and was
recorded FALSE on check 4 at the time; the platform 429 volume peaked in exactly that window
(collab_cooking's 17:02Z episode: 106 `Too many tokens per day` lines, versus 10 in its 18:02Z
episode). Round 22 is the current pin and is judged on its own evidence above.

---

## Retry / budget notes

- No polling was needed in this pass: round 22 had already completed when it started.
  Wall clock 18:11:15Z–18:13:30Z; the earlier pass ran 17:02Z–17:09Z. Both are inside the
  75-minute bound.
- No fetch failed; no check consumed its retry budget.
- Nothing was created, triggered, paused or modified. The only dispatch in this phase was
  `viewer-check.yml` run 32875824479 in coworld-builder, which touches no coworld, league or
  policy.
