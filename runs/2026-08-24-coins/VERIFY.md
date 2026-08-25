# VERIFY — coins   (2026-08-25T03:16Z)

Verdict: **2 items false** (checks 4 and 5). Checks 1, 2, 3, 6, 7, 8 are TRUE.

Both false items have the **same single cause**, and it is not in this coworld's code: AWS Bedrock
returns `429 ThrottlingException {"message":"Too many tokens per day, please wait before trying
again."}` for `claude-haiku-4-5` on every episode of this league, so most champion decisions fall
back to the scripted `reciprocator` intent. The cross-check against another LLM coworld running at
the same time (`hanabi`) is pasted under check 5. Per `prompts/60-verify.md` §5 this is a
platform-wide Bedrock capacity symptom and the instruction is to *wait inside the 75-minute bound*;
that bound (2026-08-25T01:57:14Z → 03:12:14Z) expired with the condition still present across all
six rounds, so by that same paragraph it is now an outage for phase 90 rather than a defect to fix
here.

Common facts, fetched this run:

| | |
|---|---|
| BASE | `https://softmax.com/api/observatory/v2` |
| headers sent | `Authorization: Bearer …` (value never printed), `User-Agent: coworld-builder/1.0`; `X-Use-Elevated-Privileges: true` on `artifacts/logs` and `filler-policies` |
| `$L` | `league_e9506fcc-08c3-4372-90ac-0ced465c7d9c` |
| `$D` | `div_d7a79bf3-f8b7-40f7-b838-45aa275d7913` |
| `$COW` | `cow_e5c32ad5-8696-4d4f-8a39-458baa8c2a3e` (version 0.1.2, canonical) |
| latest completed round `$R` | `round_51c0c7e3-b57c-4125-8de0-d4e3047a571a` (round_number 6) |
| its episode request `$EREQ` | `ereq_e20c40b7-6c6f-46e7-87b7-4c5941938bcb` |
| replay | `https://softmax-public.s3.amazonaws.com/replays/c9b78e5f-ad7a-4a03-9321-e6d494207a88.replay` |
| viewer-check run | `32804445583` (Metta-AI/coworld-builder, dispatched 2026-08-25T03:14:50Z) |

---

## 1. ≥2 completed rounds after fillers were set — **TRUE**

Filler registration, read fresh (elevated header required on this read):

```
GET $BASE/leagues/$L/filler-policies      (AUTH + ELEV)
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"a652fffc-1816-448b-aeac-cdb6a9ba6840","policy_id":"93f81540-803a-40d6-b1e7-1db40553dfb9","policy_name":"coins-reciprocator","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},
 {"policy_version_id":"9356e1ac-3ed0-443b-a7da-b8685941ffcf","policy_id":"36c09d66-f3ee-46dc-ac3a-24e62c2a221d","policy_name":"coins-titfortat","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```

```
GET $BASE/rounds?league_id=$L&limit=20
```
```json
[
  {"id":"round_51c0c7e3-b57c-4125-8de0-d4e3047a571a","round_number":6,"status":"completed","error":null,"created_at":"2026-08-25T03:10:08.511009Z"},
  {"id":"round_8c676b41-aefd-41a8-bea7-906941aea28f","round_number":5,"status":"completed","error":null,"created_at":"2026-08-25T02:55:03.717489Z"},
  {"id":"round_a88d95be-8829-48ea-9b7c-b34312949819","round_number":4,"status":"completed","error":null,"created_at":"2026-08-25T02:40:03.337293Z"},
  {"id":"round_921b4c22-c9a8-4ff2-ba72-b81373c568d8","round_number":3,"status":"completed","error":null,"created_at":"2026-08-25T02:25:02.907815Z"},
  {"id":"round_e36cead8-75b5-4ce4-b089-d0017609da18","round_number":2,"status":"completed","error":null,"created_at":"2026-08-25T02:10:01.586005Z"},
  {"id":"round_daad8f3a-7d1e-4913-bf62-54687080087e","round_number":1,"status":"completed","error":null,"created_at":"2026-08-25T01:55:00.919115Z"}
]
```
```
$ … | jq -r 'if type=="array" then . else .entries end | [.[]|select(.status=="completed")]|length'
6
```
(`/rounds` returned a **bare array** on this call, not `{entries:…}`.)

Status: **TRUE** — 6 completed rounds, 0 `failed`, 0 `discarded`, every `error` is `null`.
`log.md` records the fillers registered **before the first `trigger-round`**
(`2026-08-25T01:56:08Z 50 fillers 200: a652fffc (reciprocator:v2) + 9356e1ac (titfortat:v2)
registered` … `unpause 200 paused=false; trigger-round 200`), i.e. before round 1. Even if one
declined to count round 1 because its `created_at` (01:55:00.9Z) is inside the same phase-50 log
batch as the filler POST, rounds **2–6** are unambiguously later and that is still ≥ 2.

---

## 2. Both champions ranked, fillers absent — **TRUE**

```
GET $BASE/divisions/$D/leaderboard
```
```
$ … | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
1	daveey-1	coins-ledger:v2	1012.3183726440252	6	3.0
2	daveey	coins-truce:v2	987.6816273559748	6	2.0
```
```json
[{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":1012.3183726440252,"score_label":"Elo","score_value_type":"integer","rounds_played":6,"episode_wins":3.0,"episodes_played":null,"win_rate":0.5,"policy_label":"coins-ledger:v2","recent_rounds":null},
 {"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":987.6816273559748,"score_label":"Elo","score_value_type":"integer","rounds_played":6,"episode_wins":2.0,"episodes_played":null,"win_rate":0.3333333333333333,"policy_label":"coins-truce:v2","recent_rounds":null}]
```

Status: **TRUE** — `daveey` (`coins-truce:v2`, rank 2, `rounds_played: 6`) and `daveey-1`
(`coins-ledger:v2`, rank 1, `rounds_played: 6`) are both ranked; the response is a bare list of
exactly two rows, so `coins-reciprocator` and `coins-titfortat` are **absent** (they were never
seated — this is a 2-seat game and both seats went to champions).

---

## 3. Latest round's episode request completed with a replay — **TRUE**

```
GET $BASE/episode-requests?round_id=round_51c0c7e3-b57c-4125-8de0-d4e3047a571a&limit=20
```
```json
[{"id":"ereq_e20c40b7-6c6f-46e7-87b7-4c5941938bcb","status":"completed","replay_url":"https://softmax-public.s3.amazonaws.com/replays/c9b78e5f-ad7a-4a03-9321-e6d494207a88.replay"}]
```

```
GET $BASE/episode-requests/ereq_e20c40b7-6c6f-46e7-87b7-4c5941938bcb
$ … | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/c9b78e5f-ad7a-4a03-9321-e6d494207a88.replay",
  "participants": [
    {"position":0,"kind":"policy","policy_version_id":"2da8b581-6545-4809-b43d-b8958e9015ff","policy_id":"8bc51715-7714-4c01-9069-8fbde6746cd4","policy_name":"coins-truce","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","is_filler":false,"is_seed":false},
    {"position":1,"kind":"policy","policy_version_id":"794abef0-f60a-49a2-83d0-21df66e9ff51","policy_id":"01381716-3e8d-4f57-916c-3497ddfe08d0","policy_name":"coins-ledger","version":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","is_filler":false,"is_seed":false}
  ],
  "participant_scores": [{"position":0,"score":22.0},{"position":1,"score":22.0}]
}
```

Status: **TRUE** — `status == "completed"`, `replay_url` non-null, participants are exactly
`daveey`/`coins-truce:v2` at seat 0 and `daveey-1`/`coins-ledger:v2` at seat 1, both
`is_filler: false`. A drawn episode, 22–22.

---

## 4. Replay bytes are valid and show the game — **FALSE** (one sub-condition fails: fallback share)

```
$ curl -sSL "https://softmax-public.s3.amazonaws.com/replays/c9b78e5f-ad7a-4a03-9321-e6d494207a88.replay" -o /tmp/ep.replay -w 'http=%{http_code} bytes=%{size_download}\n'
http=200 bytes=56048

$ jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok

$ python3 -c "d=open('/tmp/ep.replay','rb').read(); d.decode('utf-8'); print('python strict utf-8: ok, %d bytes'%len(d))"
python strict utf-8: ok, 56048 bytes

$ jq -c '{protocol,game,gameVersion,variant,seed,names,policyNames,colours,beats,endBeat,ticksPlayed}' /tmp/ep.replay
{"protocol":"coins.replay.v1","game":"coins","gameVersion":"1","variant":"standard","seed":551346274,"names":["Copper","Cobalt"],"policyNames":["coins-player","coins-player"],"colours":["copper","cobalt"],"beats":24,"endBeat":24,"ticksPlayed":480}

$ jq -r '.protocol, .results.reason' /tmp/ep.replay
coins.replay.v1
beat_cap

$ jq -c '.results' /tmp/ep.replay
{"names":["coins-player","coins-player"],"scores":[22.0,22.0],"win":[true,true],"aliases":["Copper","Cobalt"],"colours":["copper","cobalt"],"pickups":[22,22],"thefts":[0,0],"stolenFrom":[0,0],"restraint":[1.0,1.0],"firstTheftBeat":[null,null],"reciprocityLagBeats":[null,null],"beats":24,"endBeat":24,"ticks":480,"reason":"beat_cap"}

$ jq -c '[.events[].k]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.replay
{"beatclose":24,"blocked":3,"end":1,"leadchange":8,"order":48,"pickup":44,"spawn":39}

$ jq -r '[.events[]|select(.k=="order")]|length' /tmp/ep.replay
48
$ jq -c '[.events[]|select(.k=="order")|.source]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.replay
{"fallback":41,"llm":3,"retry":4}
$ jq -r '[.events[]|select(.k=="order")]|group_by(.seat)[]|{seat:.[0].seat,n:length,srcs:(map(.source)|group_by(.)|map({(.[0]):length})|add)}|@json' /tmp/ep.replay
{"seat":0,"n":24,"srcs":{"fallback":20,"llm":2,"retry":2}}
{"seat":1,"n":24,"srcs":{"fallback":21,"llm":1,"retry":2}}
```

The 7 non-fallback decisions are genuine, non-scripted and on-prompt — `say` text verbatim from the
replay:

```
$ jq -r '[.events[]|select(.k=="order" and .source!="fallback")]|.[]|[.beat,.seat,.source,.intent,.say]|@tsv' /tmp/ep.replay
5	0	retry	take_mine	Truce established. Taking only mine.
5	1	llm	take_mine	steady pace, no thefts yet
6	0	retry	take_mine	Truce holding. Taking only copper.
7	0	llm	take_mine	Truce holds. Your move.
7	1	retry	take_mine	Ledger balanced at 0-0 thefts. One cobalt coin …
15	1	retry	take_mine	Ledger level, playing safe
23	0	llm	take_mine	copper at (2,7), I'm coming
```

Sub-conditions, one by one:

| requirement | result |
|---|---|
| valid UTF-8 JSON under a strict parser | **PASS** — `jq -e` and python `bytes.decode('utf-8')` both clean, 56 048 bytes |
| `protocol` matches the manifest | **PASS** — `coins.replay.v1`, equal to `ReplayProtocol* = "coins.replay.v1"` at `src/coins/replays.nim:17` on `Metta-AI/cogame-coins` (fetched this run via `gh api repos/Metta-AI/cogame-coins/contents/src/coins/replays.nim`) and to `design.md` §The replay file. Note: the *hosted* manifest does not carry the literal string — `manifest.game.protocols.global.value` describes the route ("Replays are a STATIC file plus a browser wasm viewer, never a pod: the bundle is `index.html?replay=<url of the .replay file>`") rather than naming the protocol id. |
| `results.reason` acceptable | **PASS** — `beat_cap`. `design.md` §End conditions declares `random_end`, `beat_cap`, `deadline`, `forfeit` as the only legal values and `beat_cap` is the natural full-length end ("beat `maxBeats` closes without the draw having fired"). Not a `deadline`. |
| champion seats' decisions **not all fallbacks**, fallbacks a **small minority** | **FAIL** — 41 of 48 orders (85.4 %) are `source: "fallback"`; per seat 20/24 and 21/24. That is a large majority, not a small minority. |

The same ratio holds across every completed round this run (all six replays fetched and parsed):

```
round 1  {"orders":38,"by_source":{"fallback":30,"llm":5,"retry":3},"reason":"random_end","beats":19,"scores":[16.0,17.0],"thefts":[0,0]}
round 2  {"orders":26,"by_source":{"fallback":26},"reason":"random_end","beats":13,"scores":[14.0,11.0],"thefts":[0,0]}
round 3  {"orders":24,"by_source":{"fallback":21,"llm":2,"retry":1},"reason":"random_end","beats":12,"scores":[12.0,13.0],"thefts":[0,0]}
round 4  {"orders":48,"by_source":{"fallback":42,"llm":3,"retry":3},"reason":"beat_cap","beats":24,"scores":[24.0,21.0],"thefts":[0,0]}
round 5  {"orders":26,"by_source":{"fallback":16,"llm":5,"retry":5},"reason":"random_end","beats":13,"scores":[12.0,13.0],"thefts":[0,0]}
round 6  {"orders":48,"by_source":{"fallback":41,"llm":3,"retry":4},"reason":"beat_cap","beats":24,"scores":[22.0,22.0],"thefts":[0,0]}
```

Best round was round 5 at 16/26 = 61.5 % fallback; worst was round 2 at 26/26 = 100 %. No round
reached a "small minority".

Status: **FALSE** — the bytes are valid, the protocol matches and the end reason is legal, but the
champion seats are mostly **not** deciding: 85.4 % of this episode's intents came from the scripted
`reciprocator` fallback. Cause is the Bedrock throttle documented under check 5.

Consequence worth naming: because `reciprocator` plays `take_mine` until it has been stolen from
twice, an all-fallback room never steals — `thefts: [0,0]` and `firstTheftBeat: [null,null]` in
**every one of the six rounds**. The dilemma this coworld is about does not occur in any episode
the ladder has produced.

---

## 5. Hosted game log is clean — **FALSE** (platform-wide Bedrock cause, cross-checked)

```
GET $BASE/episode-requests/ereq_e20c40b7-6c6f-46e7-87b7-4c5941938bcb/artifacts/logs   (AUTH + ELEV)
http=200 bytes=156147
```
The body is python `b'…'` byte-string reprs under `===== container: <name> =====` headers, so it
was decoded per-repr with `ast.literal_eval` before grepping (per `playbooks/observatory-api.md`
§10 — a raw line-based grep undercounts: it finds **1** match, the decoded text finds **43**).

```
$ grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' <decoded>  | head -6
243:2026-08-25 03:12:00,091 WARNING __main__ bedrock_sidecar_rate_limited {"schema_version": "1", …, "reason": "engaged", "limit_per_minute": 30, "rejected_total": 1, "retry_after_seconds": 0.939}
277:2026-08-25 03:12:47,407 WARNING __main__ bedrock_sidecar_rate_limited {"schema_version": "1", …, "reason": "episode_total", "limit_per_minute": 30, "rejected_total": 6}
295:coins llm: seat 0 falling back to scripted intent
296:coins llm: seat 1 falling back to scripted intent
302:coins llm: seat 0 falling back to scripted intent
303:coins llm: seat 1 falling back to scripted intent

$ for p in 'falling back' 'LLM provider is unavailable' 'cut off at max_tokens' 'rejected'; do printf '%-30s %s\n' "$p" "$(grep -c "$p" <decoded>)"; done
falling back                   41
LLM provider is unavailable    0
cut off at max_tokens          0
rejected                       2
```

**Not CLEAN.** The upstream cause, verbatim and de-duplicated (86 occurrences in this one episode):

```
$ grep -oE 'llm throttled \(429\): .*' <decoded> | sort -u
llm throttled (429): {"message": "sidecar request rate limit reached (30 requests/minute)", "__type": "ThrottlingException"}
llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
$ grep -c 'llm throttled (429)' <decoded>
86
```

The sidecar's own record of the upstream refusal:

```json
{"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar","episode_request_id":"e20c40b7-6c6f-46e7-87b7-4c5941938bcb","job_request_id":"c9b78e5f-ad7a-4a03-9321-e6d494207a88","role":"game","slot":"game","image_digest":"sha256:fbeeda0ea06a5d814471112528e48cf256a0e1acdedeb7d8afeac752f7d5fe7d","model":"global.anthropic.claude-haiku-4-5-20251001-v1:0","operation":"InvokeModel","call_id":"1ec79b07-5b46-4e13-b5fa-5490737b135e","ok":false,"status_code":429,"latency_ms":226.59469100017304,"error_kind":"upstream_client","error_type":"ThrottlingException","message":"Too many tokens per day, please wait before trying again.","request_id":"35d8967d-2113-44bd-b673-e3760da3c71f"}
```

For contrast, the game's own startup lines show the coworld is wired correctly — the secret reached
the **game** container and the LLM client engaged; it is being refused, not absent:

```
coins: seats=2 variant=standard beats=12..24 endChance=120 coinCap=8 theftPenalty=2 seed=551346274
coins: player slot 0 connected (1/2)
coins: slot 0 registered (1037 prompt chars, llm)
coins: player slot 1 connected (2/2)
coins: slot 1 registered (940 prompt chars, llm)
coins: starting with 2/2 players connected
coins llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
…
coins: episode complete (beat_cap) after 480 ticks, 24 beats, score 22-22
coins: holding /healthz and /global for 20s
```

**Cross-check against another LLM coworld, fetched this run** (`prompts/60-verify.md` §5 allows the
exception only if another LLM coworld's latest log shows it too). Coworld **`hanabi`**
(`cow_2aedf124-df70-45ce-b307-fa693c6d1943`, a different run in flight), latest **completed**
episode request `ereq_003e88da-a788-4c78-ba75-8124b44014d1` (created 2026-08-25T02:09:27Z):

```
GET $BASE/episode-requests/ereq_003e88da-a788-4c78-ba75-8124b44014d1/artifacts/logs   (AUTH + ELEV)
http=200 bytes=86113

hanabi llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
hanabi llm: seat 0 attempt 0 rejected: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
```
```json
{"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar","episode_request_id":"003e88da-a788-4c78-ba75-8124b44014d1","job_request_id":"0380479b-c5b9-4c51-b748-d6fa48d8cb49","role":"game","slot":"game","image_digest":"sha256:9e38289af2cd5edd6679ed9311edde4ac127d2cf0cdf9c7b191d4700898eb3ca","model":"global.anthropic.claude-haiku-4-5-20251001-v1:0","operation":"InvokeModel","call_id":"68f11410-61da-4677-9f25-028282d49a8c","ok":false,"status_code":429,"latency_ms":249.67463599978146,"error_kind":"upstream_client","error_type":"ThrottlingException","message":"Too many tokens per day, please wait before trying again.","request_id":"bbd7f72e-3aff-4769-b1ce-38689e31ac41"}
```

Identical model, identical `error_type`, identical `message`, different coworld, different image
digest, same hour. This is the platform-wide Bedrock **capacity** symptom SPEC §Parallelism
describes, not a defect in `cogame-coins`. Note the asymmetry: hanabi survives it because its
ladder falls back **haiku → sonnet**; coins is deliberately **haiku-only** (`design.md` §Transport,
"the raid learning — the sonnet fallback times out on every sidecar call"), so it has nowhere to go
and degrades to scripted instead.

**Waiting was performed and the bound expired.** Polled every ~5 minutes from 2026-08-25T01:57:14Z
(logged in `log.md` as `heartbeat phase=60`, and the Asana `heartbeat_at` custom field updated at
each poll) to 2026-08-25T03:12:37Z — 75 minutes, 17 polls, six rounds observed. Every round was
throttled; the fallback share never fell below 61.5 %.

Status: **FALSE** — the log is not CLEAN. The cause is documented and cross-checked as platform-wide
Bedrock throttling, and per `prompts/60-verify.md` §5 the expiry of the 75-minute bound makes this
an outage for phase 90 rather than a coworld defect. `cut off at max_tokens` is **0**, so the
`maxOutputTokens` remedy does not apply here.

Two secondary observations for the coordinator (neither is a check verdict):
- `bedrock_sidecar_rate_limited … "reason": "episode_total", "limit_per_minute": 30,
  "rejected_total": 6` — 6 of the 86 429s were the *sidecar's own* 30 req/min cap, not the upstream
  daily quota. `design.md` §Cadence sizes the floor at "2 req / 5 s = 24 req/min", but a beat in
  which attempt 0 fails issues attempt 0 **and** a retry for both seats — 4 requests per 5 s floor
  = 48 req/min, over the cap. Under a healthy Bedrock this never fires; under throttling it
  compounds. Worth a design note.
- `results.names` / `replay.policyNames` are `["coins-player","coins-player"]`, the manifest
  `player[]` id, not the uploaded policy names `coins-truce` / `coins-ledger` (which the
  Observatory *does* know — see check 3's `participants`). The viewer therefore prints
  `COINS-PLAYER` on both scorebug plates and both endcard rows. Legibility finding, see check 8.

---

## 6. The public page uses the static replay path — **TRUE**

Source used: **the SSR payload plus the replay-session API**, because the raw-HTML iframe grep
finds nothing (the page is client-rendered — `playbooks/observatory-api.md` §Featured match).

```
$ curl -sS "https://softmax.com/coins" -o /tmp/ev/page.html -w 'http=%{http_code} bytes=%{size_download}\n'
http=200 bytes=530428
$ grep -o '<iframe[^>]*src="[^"]*"' /tmp/ev/page.html
(no match — client-rendered; treated as UNKNOWN, not as a failure)
```

Featured match, server-rendered into the page payload at `state.playlist[0]` (verbatim, escaping as
found in the HTML):

```
playlist\":[{\"episodeId\":\"c1f25502-7f4c-451b-8f64-e46c772081e0\",\"coworldId\":\"cow_e5c32ad5-8696-4d4f-8a39-458baa8c2a3e\",\"coworldName\":\"coins\",\"coworldVersion\":\"0.1.2\",\"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/c9b78e5f-ad7a-4a03-9321-e6d494207a88.replay\",\"finishedAt\":\"2026-08-25T03:13:02.973147Z\",\"roundNumber\":6,\"episodeNumber\":1,\"code\":\"coins.r6.e1\",\"matchup\":{\"divisionId\":\"div_d7a79bf3-f8b7-40f7-b838-45aa275d7913\",…
```

The iframe `src` is what the page's own JS asks for:

```
POST $BASE/coworlds/replays/session
  {"coworld_id":"cow_e5c32ad5-8696-4d4f-8a39-458baa8c2a3e",
   "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/c9b78e5f-ad7a-4a03-9321-e6d494207a88.replay"}
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e5c32ad5-8696-4d4f-8a39-458baa8c2a3e/sha256%3Aa0ef314213039a0b2224593c57b91b77022e5d11d5cfa181a8f04ab288c87f72/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fc9b78e5f-ad7a-4a03-9321-e6d494207a88.replay&v=2",
  "ready": true
}
```

For completeness, the `/coworlds` list route (which the playbook records as `null` platform-wide
and therefore not evidence either way):

```
$ curl -sS "$BASE/coworlds?limit=200" … | jq -r '…|select(.name=="coins")|{id,canonical,replay_viewer,featured_match}'
{"id":"cow_e5c32ad5-8696-4d4f-8a39-458baa8c2a3e","canonical":true,"replay_viewer":null,"featured_match":null}
{"id":"cow_8ca854a5-db34-430f-929a-00917049b9b5","canonical":false,"replay_viewer":null,"featured_match":null}
```

And the coworld detail confirms the declared bundle is a static digest, not a pod:

```
$ curl -sS "$BASE/coworlds/$COW" … | jq -c '.manifest.game.replay_viewer, .manifest.game.name, .version, .canonical'
{"bundle":"sha256:d55f44c6f26def2070e151d8449bdd01b49d068fd9fdcccb1f86c53c224ae2b8"}
"coins"
"0.1.2"
true
```

Status: **TRUE** — a featured match is present (round 6 episode 1, `coins.r6.e1`, both champions),
and the iframe `src` is
`…/v2/coworlds/replays/static/<cow_id>/<manifest_hash>/index.html?replay=<s3 url>` with
`ready: true`. `<sha>` = `sha256:a0ef31…c87f72`, URL-encoded, which is exactly
`STATE.coworld.manifest_sha`. **No `/client/replay` pod URL appears anywhere.**

---

## 7. Certification declared the static bundle — **TRUE**

Source read: the **committed** `runs/2026-08-24-coins/release-result.json` (phase 40's artifact,
present on disk, `-rw-r--r-- 3965 bytes, Aug 25 01:53`). No re-download from run `32798747762` was
needed; `/tmp` was not consulted.

```
$ jq -r '.certify.replay_liveness' runs/2026-08-24-coins/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Surrounding fields from the same file:

```
$ jq -c '{version, ok, cow_id, manifest_sha, canonical, hosted_smoke, certify_ok:.certify.ok, secret_put, errors, step_failed}' runs/2026-08-24-coins/release-result.json
{"version":"0.1.2","ok":true,"cow_id":"cow_e5c32ad5-8696-4d4f-8a39-458baa8c2a3e","manifest_sha":"sha256:a0ef314213039a0b2224593c57b91b77022e5d11d5cfa181a8f04ab288c87f72","canonical":true,"hosted_smoke":"passed","certify_ok":true,"secret_put":true,"errors":[],"step_failed":null}
```

and the transcript tail, verbatim from `.certify.output_tail`:

```
  [pass] replay-present: a replay artifact was produced
  [pass] replay-loadable: the replay artifact has a declared viewer path
  [pass] players-run: every declared player actually started on the smoke episode (not just declared)
  [pass] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks
Certified dist/coworld_manifest.json
Transcript: coworld-executable (10 steps passed)
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE** — the string `Replay liveness: skipped (static replay bundle declared` is present,
10/10 certification steps passed, `cow_id` and `manifest_sha` match the canonical 0.1.2 coworld
verified in check 6.

---

## 8. Spectator judgment — the viewer was EXECUTED — **TRUE**

Dispatched against the check-6 iframe `src`, in this run:

```
$ SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e5c32ad5-8696-4d4f-8a39-458baa8c2a3e/sha256%3Aa0ef314213039a0b2224593c57b91b77022e5d11d5cfa181a8f04ab288c87f72/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fc9b78e5f-ad7a-4a03-9321-e6d494207a88.replay&v=2'
$ gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
   dispatched 2026-08-25T03:14:51Z
$ gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
    | jq -r 'sort_by(.createdAt)|reverse|.[0:3][]|[.databaseId,.createdAt,.status]|@tsv'
32804445583	2026-08-25T03:14:50Z	in_progress
32803415305	2026-08-25T02:58:40Z	completed
32802744596	2026-08-25T02:47:40Z	completed
$ gh run watch 32804445583 -R Metta-AI/coworld-builder --exit-status
   ✓ viewer-check in 45s (ID 97671671082)   — green
$ gh run download 32804445583 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-24-coins/viewer-check
   viewer-smoke.json  viewer-smoke.png  smoke-stdout.txt  smoke-stderr.txt
```

Committed evidence: `runs/2026-08-24-coins/viewer-check/` (this run's only rendered evidence).

```
$ jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-24-coins/viewer-check/viewer-smoke.json
{"loaded":true,"ms":1648,"clock":"BEAT 1 / 24 TICK 0 OF 480 · 6 COINS ON THE BOARD","scorebug":"COINS-PLAYER 0 STOLE 0 took 22 · restraint 100% BEAT 1 / 24 TICK 0 OF 480 · 6 COINS ON THE BOARD COINS-PLAYER 0 STOLE 0 took 22 · restraint 100%","feed_lines":0}

$ jq -c '.signals' runs/2026-08-24-coins/viewer-check/viewer-smoke.json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}

$ jq -r '.failure // "no failure"' runs/2026-08-24-coins/viewer-check/viewer-smoke.json
no failure

$ jq -c '.canvas_text' runs/2026-08-24-coins/viewer-check/viewer-smoke.json
{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
```

The three scrub readouts:

| scrub position | `#clock` readout |
|---|---|
| 0 % | `BEAT 1 / 24 TICK 0 OF 480 · 6 COINS ON THE BOARD` |
| 50 % | `BEAT 13 / 24 TICK 256 OF 480 · 1 COIN ON THE BOARD` |
| 100 % | `FINAL 24 BEATS · BEAT_CAP` |

All three **differ**, and they differ in beat, tick and coins-on-board — the viewer is advancing,
not repainting one frame. `console_tail` records one non-fatal 404 (`…/font.ttf`) followed by
`[bridge] loading` → `[bridge] ready`.

Status: **TRUE** — `loaded: true` (via `data-replay-loaded="true"` **and** the `coworld-replay`
bridge's `ready`), first frame at 1 648 ms, and the three clock readouts differ.

### The replay JSON the viewer was asked to draw

Early (first events, ticks 0–52):

```
0	0	order	take_mine
0	1	order	take_mine
3	0	pickup	copper
3	1	pickup	cobalt
6	1	blocked	restraint
12	-	spawn	copper
15	1	pickup	cobalt
15	1	leadchange
19	-	beatclose
20	0	order	take_mine
20	1	order	take_mine
24	0	pickup	copper
24	-	spawn	copper
24	0	leadchange
30	0	pickup	copper
30	1	pickup	cobalt
```

Middle (ticks 260–316):

```
260	1	order	hold
280	0	order	take_mine
280	1	order	take_mine	Ledger level, playing safe
280	0	pickup	copper
283	1	pickup	cobalt
288	-	spawn	copper
292	1	blocked	restraint
295	1	pickup	cobalt
300	0	order	take_mine
300	1	order	hold
301	0	pickup	copper
316	0	pickup	copper
```

Late (final events):

```
440	0	order	take_mine	copper at (2,7), I'm coming
440	1	order	hold
456	-	spawn	copper
460	0	order	take_mine
460	0	pickup	copper
469	0	pickup	copper
478	0	pickup	copper
478	0	leadchange
479	-	beatclose
479	-	end	beat_cap
```

```
$ jq -c '.indices' /tmp/ep.replay
{"pickups":[22,22],"thefts":[0,0],"stolenFrom":[0,0],"restraint":[1.0,1.0],"firstTheftBeat":[null,null],"reciprocityLagBeats":[null,null]}
$ jq -c '[.events[]|select(.k=="blocked")]' /tmp/ep.replay
[{"k":"blocked","t":6,"seat":1,"x":6,"y":5,"why":"restraint"},{"k":"blocked","t":292,"seat":1,"x":5,"y":6,"why":"restraint"},{"k":"blocked","t":406,"seat":0,"x":7,"y":6,"why":"restraint"}]
```

### Spectator-judgment paragraph

**It is legible, it is unmistakably the starter's chrome, and the picture agrees with the record —
but what it is showing is a game with the dilemma taken out of it.** `viewer-smoke.png` (captured
at 100 % scrub, so the endcard is up) is paintbot-lineage in every part: the scorebug band across
the top with a coloured chip, policy name, large score and a `STOLE 0 · took 22 · restraint 100%`
sub-line on each plate, left and right of a centre clock reading `FINAL / 24 BEATS · BEAT_CAP`; the
letterboxed 504×504 vault-floor board between the bands, with the red Copper cog bottom-left, the
blue Cobalt cog bottom-right and a struck coin still on the floor; the endcard bounded at
`var(--band)` carrying `THE ROOM SPLITS EVEN`, the chip `24 BEATS · RAN THE FULL DISTANCE ·
44 COINS`, the one-sentence rule restatement, and a two-row table (POLICY / SCORE / COINS / THEFTS
/ STOLEN / RESTRAINT → `22 22 0 0 100%` twice); and the full transport strip along the bottom —
loop, step-back, pause, +5 s, play, loop, fast-forward, `spoilers`, a `DRAW` win-chip, the tick
readout `479 / 479`, the 1×–16× speed chips, and beneath them the scrubber with the `SCORE LEAD`
momentum graph drawn full-width with beat-marker ticks on it. This is the transport strip,
scrubber-with-momentum-graph, scorebug plates and endcard the starter ships — not a lookalike
rewrite (the cogame-gridlock failure). The scrubber is present and drives the clock: the three
readouts above were taken by clicking it at 0 %, 50 % and 100 %, and each returned a different
beat, tick and coin count, so a spectator can seek and the picture follows. `canvas_text` reports
**0 draws that never landed inside the canvas** under the fixed-arena bound.

Three honest deductions. First, **the plates are unreadable as identity**: both read `COINS-PLAYER`,
because the replay's `policyNames` are `["coins-player","coins-player"]` — the manifest `player[]`
id, not the uploaded `coins-truce` / `coins-ledger` names the Observatory shows in check 3's
`participants`. A spectator cannot tell which cog is which policy from the chrome; only the colour
chips distinguish them. That is a phase-30 legibility item, and it is in the *replay writer*, not
the viewer. Second, **`feed_lines: 0` at the sampled moment** — the killfeed had no rows visible
with the endcard up; the feed is not contradicted by the record, but this run did not capture it
populated. Third and most substantive: the picture and the record agree that **nothing happened
socially**. `thefts: [0,0]`, `stolenFrom: [0,0]`, `restraint: 100%` for both, `firstTheftBeat:
[null,null]`, exactly 3 `blocked why:"restraint"` events, zero `theft` and zero `truce` events in
480 ticks. Both cogs walked to their own colour and took it for 24 beats and drew 22–22. The
reciprocity timeline has nothing to draw, the theft counters never flash, the endcard headline is
`THE ROOM SPLITS EVEN`, and the idea's headline beat — "the moment one cog starts leaving the other's
coins alone" — cannot occur because no cog ever stopped leaving them alone. That is a direct
consequence of check 4/5: with 85 % of intents supplied by the `reciprocator` fallback, and
`reciprocator` playing `take_mine` until it has been stolen from twice, a room of two fallbacks is
a stable non-event. The viewer is fine. The episode is empty. Until the Bedrock throttle clears, the
featured match on `softmax.com/coins` will be a well-drawn, well-labelled, perfectly legible picture
of two cogs politely ignoring each other.

---

## Fetch log

| # | check | verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers | **TRUE** (6 completed, 0 failed/discarded) |
| 2 | both champions ranked, fillers absent | **TRUE** |
| 3 | latest round's episode request completed with replay | **TRUE** |
| 4 | replay bytes valid and show the game | **FALSE** — bytes/protocol/reason all pass; 41/48 (85.4 %) decisions are scripted fallbacks |
| 5 | hosted game log clean | **FALSE** — 41 `falling back`, 2 `rejected`; cause = Bedrock 429 daily-token throttle, cross-checked against `hanabi` |
| 6 | public page uses the static replay path | **TRUE** |
| 7 | certification declared the static bundle | **TRUE** |
| 8 | viewer executed and judged | **TRUE** — `loaded: true`, three differing clock readouts |

Waiting: polled 2026-08-25T01:57:14Z → 03:12:37Z (75 min, 17 polls), `log.md` `heartbeat phase=60`
lines and the Asana `heartbeat_at` field written at each. No extra `trigger-round` was issued — the
ladder produced rounds on its own 15-minute schedule and the 40-minute clause never applied.
No league, division, round or policy was created, triggered, paused or modified by this phase; the
only workflow dispatched was `viewer-check.yml` in `Metta-AI/coworld-builder` (run `32804445583`).
