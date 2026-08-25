# VERIFY — paintball   (2026-08-25T13:45Z, all fetches this run)

Verdict: **3 items false** (4, 5, 8). Checks 1, 2, 3, 6, 7 TRUE.

- coworld `cow_4ac3644c-c0f0-4b39-93ae-adb2dd39518d` v0.1.2, manifest
  `sha256:484a082c1f95ece0c295209173ab9a5064c376c35c0fe12946a5db07557a3374`
- league `league_bd940066-00c4-4ade-87ae-06dac0818bc4`, division `div_97b4e1b9-6f9b-44ab-8583-73789a4ee057`
- Every request below sent `Authorization: Bearer <SOFTMAX_TOKEN>` + `User-Agent: coworld-builder/1.0`
  (values never printed); artifact reads additionally sent `X-Use-Elevated-Privileges: true`.
- Headline: the ladder runs, the page and the static viewer are correct, **but the LLM barely
  decides anything**. Rounds 1→4 recorded 15, 9, 4 and 2 LLM-sourced directives out of ~72–78 per
  episode; everything else was the scripted holdline fallback. Champion #2 (`daveey-1`) has had
  **zero** LLM-sourced directives in all four rounds. Trigger is a platform-wide Bedrock haiku
  daily-token 429 (cross-checked below), amplified by two paintball-side choices: the
  `us.anthropic.claude-sonnet-4-5` fallback candidate (times out on every sidecar call — the
  documented raid 2026-08-23 scar) and a 4 s first-attempt deadline (`attempt1Ms: 4500`, floored to
  4 s by curly's whole-second timeout) against a sidecar whose median call in this coworld measured
  4.6 s.

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

Fillers were registered **before** the first trigger (`log.md` 2026-08-25T12:48:11Z: "fillers
registered 200: holdline=b39fb2e0… sprayer=f24ea073…"; the same line records `trigger-round 200;
round 1 pending`), so every completed round counts.

```
GET /api/observatory/v2/rounds?league_id=league_bd940066-00c4-4ade-87ae-06dac0818bc4&limit=20
```

```json
[
  {"id":"round_b10985a5-c9b2-4c75-a6d0-214cadf67bf6","round_number":4,"status":"completed","error":null,
   "created_at":"2026-08-25T13:32:02.017005Z","completed_at":"2026-08-25T13:38:20.581820Z"},
  {"id":"round_b589408b-350d-47ce-96f3-4a5335844166","round_number":3,"status":"completed","error":null,
   "created_at":"2026-08-25T13:17:01.513720Z","completed_at":"2026-08-25T13:25:10.853455Z"},
  {"id":"round_e362afc6-1048-426e-956c-7d37cf07cb3d","round_number":2,"status":"completed","error":null,
   "created_at":"2026-08-25T13:02:01.127562Z","completed_at":"2026-08-25T13:07:11.075093Z"},
  {"id":"round_f869a120-6fdf-4fdf-bb35-f1aa5cb9f3ae","round_number":1,"status":"completed","error":null,
   "created_at":"2026-08-25T12:47:00.788297Z","completed_at":"2026-08-25T12:53:15.488017Z"}
]
```

```
$ … | jq -r '[.entries[]|select(.status=="completed")]|length'
4
```

Status: **TRUE** — rounds 1, 2, 3, 4 completed at 12:53:15Z, 13:07:11Z, 13:25:10Z and 13:38:20Z;
fillers were set at 12:48:11Z, before round 1 was triggered. No `failed`/`discarded` rounds; every
`error` is `null`.

---

## 2. Both champions ranked, fillers absent — TRUE

```
GET /api/observatory/v2/divisions/div_97b4e1b9-6f9b-44ab-8583-73789a4ee057/leaderboard
```

The endpoint returns a **bare list** (handled with `if type=="array" then . else .entries end`):

```
rank  player_name  policy_label               score               rounds_played  episode_wins
1     daveey-1     paintball-splitpaint:v1    1013.4536022359164  4              2.0
2     daveey       paintball-holdcentre:v1     986.5463977640836  4              1.0
```

Status: **TRUE** — `daveey` and `daveey-1` both present with `rounds_played = 4 ≥ 1`; only two rows,
so the fillers (`paintball-holdline:v1`, `paintball-sprayer:v1`) are absent and no row is labelled
`Baseline`. Neither champion was renamed `Baseline (N)`.

---

## 3. The latest round's episode request completed with a replay — TRUE

Latest completed round = `round_b10985a5-c9b2-4c75-a6d0-214cadf67bf6` (round_number 4).

```
GET /api/observatory/v2/episode-requests?round_id=round_b10985a5-c9b2-4c75-a6d0-214cadf67bf6&limit=20
```

```json
[{"id":"ereq_b98ed068-c4f1-4430-8b35-c6a774f548b8","status":"completed",
  "replay_url":"https://softmax-public.s3.amazonaws.com/replays/9b5c5885-2453-473c-aac6-9e1e10d99886.replay"}]
```

```
GET /api/observatory/v2/episode-requests/ereq_b98ed068-c4f1-4430-8b35-c6a774f548b8
```

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/9b5c5885-2453-473c-aac6-9e1e10d99886.replay",
  "participants": [
    {"position": 0, "policy_name": "paintball-holdcentre", "version": 1, "player_name": "daveey",   "is_filler": false},
    {"position": 1, "policy_name": "paintball-splitpaint", "version": 1, "player_name": "daveey-1", "is_filler": false}
  ],
  "participant_scores": [{"position": 0, "score": 0.282}, {"position": 1, "score": 0.718}]
}
```

Status: **TRUE** — `status == "completed"`, non-null `replay_url`, participants name `daveey`
(seat 0, holdcentre v1) and `daveey-1` (seat 1, splitpaint v1), neither a filler.

---

## 4. Replay bytes are valid and show the game — **FALSE**

The paintball replay is **binary** (`COWLDPNT`), so `jq -e .` on the raw bytes is not the test the
design specifies; the strict-UTF-8 JSON view is `tools/replay_summary.py` from
`Metta-AI/cogame-paintball` (cloned fresh at `/workspace/cogame-paintball`, design note
§"The replay"). Exactly what I ran:

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/9b5c5885-2453-473c-aac6-9e1e10d99886.replay" -o /tmp/ep.replay
python3 /workspace/cogame-paintball/tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol' /tmp/ep.json
jq -r '[.directives[]|select(.source=="llm")]|length'      /tmp/ep.json   # decision records, source llm
jq -r '[.directives[]|select(.source=="fallback")]|length' /tmp/ep.json
jq -r '[.directives[]|select(.source=="scripted")]|length' /tmp/ep.json
jq -r '.directives|length, .fallbacks, .budgetGuards'      /tmp/ep.json
jq -c '.results' /tmp/ep.json
```

```
replay HTTP 200 bytes 161507
$ od -c /tmp/ep.replay | head -2
0000000   C   O   W   L   D   P   N   T 001  \0  \t  \0   p   a   i   n
0000020   t   b   a   l   l 001  \0   1
strict UTF-8 JSON: ok
paintball/v1
2          <- llm directives
68         <- fallback directives
0          <- scripted directives
70         <- total directives
204        <- fallback records
0          <- budget guards
{}         <- results: EMPTY (no `{"k":"result"}` record in the replay bytes)
```

`protocol` = `paintball/v1`, which is what the manifest's `game.protocols` document and
`tests/test_replay.nim:285` pin (`check node["protocol"].getStr() == "paintball/v1"`). Header magic
`COWLDPNT` + game name `paintball` matches the coworld.

Because the replay carries **no `result` record** (a byte count of `reason` and of `{"k":"result` in
the raw bytes is 0 for rounds 1, 3 and 4 — the three replays I fetched this run), `results.reason`
had to come from the hosted artifact:

```
GET /api/observatory/v2/episode-requests/ereq_b98ed068-c4f1-4430-8b35-c6a774f548b8/artifacts/results
   (+ X-Use-Elevated-Privileges: true)
```

```json
{"reason":"complete","endRule":"mercy","scores":[0.282,0.718],"win":[false,true],
 "llmTurns":[2,0],"fallbackTurns":[33,35],"hillTicks":[0,631],"residentHillTicks":[0,84],
 "visitorHillTicks":[0,547],"paintTiles":[140,136],"tagsDealt":[9,27],"games":2,"finalTick":4405}
```

`reason == "complete"` with `endRule == "mercy"` — a legal, normal ending
(design.md §"End conditions and legal `results.reason` values": *`complete` / `mercy` — the final
game's hill lead exceeded the ticks remaining. The rules ended it; still a complete episode*). No
`deadline`, no `fault`. That part passes.

**What fails is the decision mix.** The definition of done requires the champion seats' decisions to
be non-scripted and *"not all fallbacks (fallback count must be a small minority of decisions)"*.
Here fallbacks are 68 of 70 directives (97 %) and `llmTurns` is `[2, 0]` — seat 1 (`daveey-1`) made
**no** LLM decision at all. Ordered excerpts of the directive stream (early / middle / late), which
is what the viewer's command feed draws:

```
$ jq -r '.directives[]|[.game,.turn,.seat,.team,.regime,.source,.latency_ms,(.note[0:60])]|@tsv' /tmp/ep.json | head -8
1  0  0  red   resident  fallback  0  hold the hill
1  0  1  blue  resident  fallback  0  hold the hill
1  1  0  red   resident  fallback  0  hold the hill
1  1  1  blue  resident  fallback  0  hold the hill
1  2  0  red   resident  fallback  0  hold the hill
1  2  1  blue  resident  fallback  0  hold the hill
1  3  0  red   resident  fallback  0  hold the hill
1  3  1  blue  resident  fallback  0  hold the hill
… (sed -n '33,40p' — middle) …
1 16 0 red resident fallback 0 hold the hill   … 1 19 1 blue resident fallback 0 hold the hill
… (tail -6 — late) …
2 12 0 red visitor fallback 0 hold the hill    … 2 14 1 blue visitor fallback 0 hold the hill
```

The only two LLM directives in the episode are real and game-aware (so the LLM path is wired
correctly when a call returns in time):

```json
[{"k":"directive","game":2,"turn":4,"seat":0,"team":"red","regime":"visitor","source":"llm","latency_ms":4000,
  "note":"Hill contested! Alpha hurt but closest - hold center. Beta guard our side. Three enemies RIGHT ON TOP OF US - emergency paint their edges to break their 80%!",
  "cogs":[{"id":"RED-alpha","intent":"hold_hill","target":[617,329],"say":"HOLD!","face":[714,247]}]},
 {"k":"directive","game":2,"turn":5,"seat":0,"team":"red","regime":"visitor","source":"llm","latency_ms":3999,
  "note":"Alpha tagged out, they own hill 76%. Emergency: send everyone to paint different hill edges simultaneously to break their 80% and flip ownership to us NOW.",
  "cogs":[{"id":"RED-alpha","intent":"paint_hill","target":[544,238],"say":"TOP EDGE","face":[617,329]}]}]
```

Trend across all four completed rounds (same commands, per round):

| round | ereq | reason / endRule | llmTurns | fallbackTurns | llm / total directives |
|---|---|---|---|---|---|
| 1 | ereq_49f4feb1-196b-4251-84bd-74958e815c98 | complete / full_time | [15, 0] | [21, 36] | 15 / 72 |
| 2 | ereq_c2565de0-87e0-4a68-99da-1d6c2a22a2a0 | complete / mercy | [9, 0] | [29, 38] | 9 / 76 |
| 3 | ereq_09cc1d41-9856-493a-9c53-fca6c3ad8791 | complete / mercy | [4, 0] | [35, 0] | 4 / 78 (39 **scripted**) |
| 4 | ereq_b98ed068-c4f1-4430-8b35-c6a774f548b8 | complete / mercy | [2, 0] | [33, 35] | 2 / 70 |

Round 3 additionally shows a champion seat playing the **scripted** baseline: only seat 0 ever sent
a `register` record, and the hosted game log reads `player connected: daveey-1` followed by
`Dropped message to disconnected client`, so seat 1's 39 directives are `source: scripted`
(holdline) — a scripted policy on a champion seat, which the design calls a failure state.

Status: **FALSE** — valid strict-UTF-8 JSON view, correct `protocol`, acceptable
`results.reason == "complete"` (endRule `mercy`), but 68 of 70 decisions are fallbacks and champion
#2 has no LLM decision at all. The exception the checklist allows (a `deadline` the design declares
acceptable) does not apply: this fails on the fallback-majority clause, not on `reason`.

---

## 5. Hosted game log is clean — **FALSE**

The logs body is python `b'…'` reprs under `===== container: … =====` headers, so it is
`ast.literal_eval`-decoded per repr **before** grepping (playbook §10, escrow 2026-08-23):

```bash
curl -sS "$BASE/episode-requests/ereq_b98ed068-c4f1-4430-8b35-c6a774f548b8/artifacts/logs" \
  -H "Authorization: …" -H "User-Agent: …" -H "X-Use-Elevated-Privileges: true" -o /tmp/logs.raw
# decode every b'…' repr per container, then:
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.txt
```

```
logs HTTP 200 bytes 195910
containers: coworld-init-config, bedrock-sidecar, game, worker
total matching lines: 205   {'falling back': 205, 'LLM provider is unavailable': 0,
                             'cut off at max_tokens': 0, 'rejected': 0}
323:paintball llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
324:paintball llm: seat 0 attempt 1 failed, falling back if it fails again: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
325:paintball llm: seat 1 attempt 1 failed, falling back if it fails again: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
326:paintball llm: seat 0 attempt 2 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-sonnet-4-5-20250929-v1:0/invoke
327:paintball llm: seat 1 attempt 2 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-sonnet-4-5-20250929-v1:0/invoke
328:paintball llm: seat 0 falling back to holdline (parse_error) on turn 0
…
1106:paintball llm: seat 0 falling back to holdline (parse_error) on turn 14
1107:paintball llm: seat 1 falling back to holdline (parse_error) on turn 14
```

Sidecar side of the same log (4 throttle lines):

```
2026-08-25 13:32:20,857 WARNING __main__ bedrock_sidecar_complete {… "episode_request_id":"b98ed068-…"
  … ThrottlingException … "Too many tokens per day, please wait before trying again." …}
```

**Platform-wide cross-check (the checklist's documented exception), fetched this run:** another LLM
coworld's latest episode, `collab_cooking` `ereq_394e25ff-92dd-420a-ac8a-2f488bfa236c`
(created 13:27:37Z, `GET …/artifacts/logs` HTTP 200, 118 947 bytes) shows the same Bedrock symptom:

```
Too many tokens: 98 lines | ThrottlingException: 49 | 429: 148
2026-08-25 13:28:14,920 WARNING __main__ bedrock_sidecar_complete {… "episode_request_id":"394e25ff-…" …}
```

(Its earlier episode `ereq_c88e512c…` at 12:57Z: 42 ThrottlingExceptions. Coordinator also reports
the `coins` run hitting the same 429 at 03:23Z.) So the **haiku daily-token 429 is platform-wide**
and not a paintball defect.

Two things in this log are **not** platform-wide, however, and I measured both:

1. After the first 429 paintball switches its model candidate to `us.anthropic.claude-sonnet-4-5`
   and then **every** sonnet call times out — `model/…sonnet-4-5…/invoke` appears 133 times in
   round 2's log, always as `Timeout was reached`, 0 successes. This is the documented raid
   2026-08-23 scar ("the ladder fallback sonnet **times out on every sidecar call** … keep haiku,
   drop that candidate") reproduced with sonnet-4-5.
2. Paintball's own sidecar latencies in round 2 (85 calls): median **4 618 ms**, max 12 382 ms,
   56 of 85 above 4 000 ms — against a first-attempt deadline of `attempt1Ms: 4500` that curly
   floors to **4 s** whole seconds (`src/paintball/decide.nim:401` comment) and a 2 s retry. All
   15 successful LLM directives in round 1 report `latency_ms` 3999–4001, i.e. they land exactly on
   the deadline. By contrast `coins`' sidecar (12:44Z, 22 calls) measured a 1 984 ms median — paintball's
   4 000-token prompt / 900-token reply is simply slower than its own deadline.

Status: **FALSE** — 205 matching lines, must be `CLEAN`. The trigger (haiku daily-token 429) is a
documented platform-wide capacity symptom cross-checked against `collab_cooking` above; the
amplifiers (sonnet fallback candidate, 4 s deadline) are paintball-side. I kept polling to the
75-minute bound (rounds 1→4, 12:53Z→13:38Z) and the ratio got **worse** each round, not better.

---

## 6. The public page uses the static replay path — TRUE

```bash
curl -sS "https://softmax.com/paintball" | grep -o '<iframe[^>]*src="[^"]*"'
```

```
page HTTP 200 bytes 557278
NO IFRAME IN RAW HTML (client-rendered)
```

Empty grep = unknown, not a failure (playbook §Featured match: the page is client-rendered for the
iframe, platform-wide). **Source used: the page's own SSR payload + the call the page's JS makes.**

Featured match, from the SSR payload `state.playlist[0]` in that same HTML:

```json
{"episodeId":"697703bb-6e35-4ce2-90ce-a83557366488","coworldId":"cow_4ac3644c-c0f0-4b39-93ae-adb2dd39518d",
 "coworldName":"paintball","coworldVersion":"0.1.2",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/9b5c5885-2453-473c-aac6-9e1e10d99886.replay",
 "finishedAt":"2026-08-25T13:38:12.073273Z","roundNumber":4,"episodeNumber":1,"code":"paintball.r4.e1",
 "matchup":{"divisionId":"div_97b4e1b9-6f9b-44ab-8583-73789a4ee057","divisionName":"Competition",
 "first":{"rank":1,"player_name":"daveey-1","score":1013.4536022359164,"policy_label":"paintball-splitpaint:v1"…}}}
```

The iframe `src` the page requests:

```
POST /api/observatory/v2/coworlds/replays/session
     {"coworld_id":"cow_4ac3644c-c0f0-4b39-93ae-adb2dd39518d",
      "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/9b5c5885-2453-473c-aac6-9e1e10d99886.replay"}
```

```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_4ac3644c-c0f0-4b39-93ae-adb2dd39518d/sha256%3A484a082c1f95ece0c295209173ab9a5064c376c35c0fe12946a5db07557a3374/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F9b5c5885-2453-473c-aac6-9e1e10d99886.replay&v=2",
  "ready": true
}
```

(For completeness, the detail API's own fields are null platform-wide, as the playbook records:
`GET /coworlds?limit=200` → `{"id":"cow_4ac3644c-…","canonical":true,"replay_viewer":null,"featured_match":null}`.)

Status: **TRUE** — a featured match is present (`paintball.r4.e1`, both ranked players), and the
`src` is the static route `…/v2/coworlds/replays/static/<cow_id>/<manifest sha256, URL-encoded>/index.html?replay=<s3 url>`
with `ready: true`. No `/client/replay` pod URL anywhere.

---

## 7. Certification declared the static bundle — TRUE

Source read: the **committed** `runs/2026-08-25-paintball/release-result.json` (phase 40's artifact
from release run 32847347580); no re-download was needed.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-25-paintball/release-result.json
```

```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

```bash
jq -c '{ok, canonical, version, cow_id, certify_ok: .certify.ok}' runs/2026-08-25-paintball/release-result.json
{"ok":true,"canonical":true,"version":"0.1.2","cow_id":"cow_4ac3644c-c0f0-4b39-93ae-adb2dd39518d","certify_ok":true}
```

Status: **TRUE** — contains `Replay liveness: skipped (static replay bundle declared`.

---

## 8. Spectator judgment — the viewer was EXECUTED — **FALSE**

Dispatched (this run, 4 dispatches; the committed artifact is the last one, against the current
featured match):

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_4ac3644c-c0f0-4b39-93ae-adb2dd39518d/sha256%3A484a082c1f95ece0c295209173ab9a5064c376c35c0fe12946a5db07557a3374/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F9b5c5885-2453-473c-aac6-9e1e10d99886.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=120
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 5 \
  | jq -r 'sort_by(.createdAt)|reverse|.[0].databaseId'        # -> 32854934931 (created 13:42:15Z)
gh run watch 32854934931 -R Metta-AI/coworld-builder --exit-status                 # green, 0
gh run download 32854934931 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-25-paintball/viewer-check
```

`runs/2026-08-25-paintball/viewer-check/viewer-smoke.json`, verbatim:

```json
{"loaded":true,"ms":4146,"clock":"1:30 TIME LEFT GAME 1/2 · RESIDENT · TURN 1/20","scorebug":"0% RED HILL 0:00 0 TAGS · 4 UP 1:30 TIME LEFT GAME 1/2 · RESIDENT · TURN 1/20 0% BLUE HILL 0:00 0 TAGS · 4 UP","feed_lines":0}
```

```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

```json
"failure": null
"canvas_text": {"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
```

The three clock readouts (the shell **does** expose `#scrub`, so these are real seeks, not
`"(no #scrub…)"`):

| at | clock |
|---|---|
| 0 % | `1:30 TIME LEFT GAME 1/2 · RESIDENT · TURN 1/20` |
| 50 % | `1:30 TIME LEFT GAME 1/2 · RESIDENT · TURN 1/20` |
| 100 % | `FINAL GAME OVER GAME 2/2 · VISITOR · TURN 20/20` |

**0 % and 50 % are identical**, so the "three readouts differ" criterion is not met. Reproduced by
all four dispatches, including one against a *different* replay, so it is deterministic and not
replay-specific (each json is committed under `viewer-check/attempt-<run id>/`):

| run | replay | loaded | ms | 0 % | 50 % | 100 % |
|---|---|---|---|---|---|---|
| 32851786955 | r2 (048419e0) | true | 4172 | `1:30 … GAME 1/2 · RESIDENT · TURN 1/20` | *same* | `FINAL GAME OVER GAME 2/2 · VISITOR · TURN 20/20` |
| 32852051931 | r2 (048419e0) | true | 5916 | `1:30 … GAME 1/2 · RESIDENT · TURN 1/20` | *same* | `FINAL GAME OVER GAME 2/2 · VISITOR · TURN 20/20` |
| 32852194317 | r1 (a6bad02d) | true | 3809 | `1:30 … GAME 1/2 · RESIDENT · TURN 1/20` | *same* | `0:00 TIME LEFT GAME 2/2 · VISITOR · TURN 20/20` |
| **32854934931** (committed) | r4 (9b5c5885) | true | 4146 | `1:30 … GAME 1/2 · RESIDENT · TURN 1/20` | *same* | `FINAL GAME OVER GAME 2/2 · VISITOR · TURN 20/20` |

Status: **FALSE** — criterion 1 (`loaded: true`, first frame in 4.1 s, `data-replay-loaded="true"`,
no `data-replay-error`, no page error, no failure) passes; criterion 2 (three differing clock
readouts) fails because the mid-replay seek does not land inside the smoke's 700 ms settle window.
Read-only observation on cause, for phase 30 rather than for me to fix: click-to-seek in
`client/replay_broadcast.html:3655` sends `s:<tick>` to the wasm worker behind
`if (!lastState || !lastState.en) return;` — the end-seek readout does change, and the screenshot
proves the board reaches the final frame, so this looks like a slow/dropped **mid**-seek, not a
frozen viewer. `feed_lines: 0` is a second legibility observation: the command feed is plainly drawn
in the screenshot, so the smoke's `#feed` selector does not match this shell's feed container.

### The spectator-judgment paragraph

`viewer-check/viewer-smoke.png` (1280×800, headless chromium, round 4's featured replay) is a
**legible, complete broadcast of this game**, and it is the starter's chrome, not a lookalike: the
top strip carries the twin scorebug (`33%` / `0:00 HILL RED`, `19 TAGS · 4 UP` and `BLUE HILL 0:03`,
`35 TAGS · 4 UP`, `66%`), the centre carries the endcard (`FINAL / GAME OVER / GAME 2/2 · VISITOR ·
TURN 20/20`, `BLUE WINS`, the chip `MERCY — LEAD BEYOND THE CLOCK` and the sentence "RED holds 0:00
— BLUE 0:03 · game 2/2 · VISITOR — the lead was bigger than the clock left, so the rules ended it"),
and the bottom carries paintbot's transport strip (restart / back / play / +5s / step / loop /
skip / `spoilers`, speed chips 1×–16×, `BLUE WINS 2086 / 4172`) over the scrubber with its `LIVES
LEAD` momentum graph. The arena itself is the game: red and blue floor paint spread across the map,
cogs with `paint` / `hold` / `watch` badges, the two team hills at either side, and a per-cog table
(`DAVEEY` RED-alpha…delta 95 paint each; `DAVEEY-1` BLUE-alpha…delta 132 paint each, tags 7–12).
That reconciles with the record: `results` for the same episode says `win [false,true]`,
`endRule "mercy"`, `hillTicks [0,631]`, `paintTiles [140,136]`, `tagsDealt [9,27]` — blue owned the
hill, both sides painted heavily, and blue landed three times the tags. The picture is neither empty
nor unreadable, and it is not a single frozen frame: the 100 % readout and the endcard are the last
frame, while 0 % is the first.

The one thing the picture shows too honestly is check 4's failure: the command feed on the right
reads `RED command : HOLD THE HILL` / `BLUE command : HOLD THE HILL` on every visible line — the
scripted holdline fallback — because 68 of this episode's 70 directives were fallbacks. A spectator
watching paintball right now sees a well-made broadcast of two baselines, not of two LLMs. Also
worth sending back to phase 30: the mid-replay seek that does not respond within 700 ms (above), and
`feed_lines: 0` from a feed that is visibly populated.

---

## Definition-of-done summary

| # | Item | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | TRUE (4 rounds) |
| 2 | both champions ranked, fillers absent/Baseline | TRUE |
| 3 | latest round's episode completed, replay_url, correct participants | TRUE |
| 4 | replay valid, protocol matches, reason acceptable, decisions not all fallbacks | **FALSE** (68/70 fallback; `llmTurns [2,0]`) |
| 5 | hosted game log clean | **FALSE** (205 `falling back` lines; platform-wide haiku 429 cross-checked, plus paintball-side sonnet fallback + 4 s deadline) |
| 6 | public page uses the static replay path, featured match present | TRUE |
| 7 | certification declared the static bundle | TRUE |
| 8 | viewer executed: loaded AND three clock readouts differ | **FALSE** (loaded true; 0 % == 50 %) |
