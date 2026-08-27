# VERIFY — lux-ai   (2026-08-27T19:06Z)

Verdict: **all-true (8/8)** — with one recorded deviation inside check 4 (§4d) and two
legibility observations for the coordinator (§8, §Spectator judgment). Nothing below is
inferred; every verdict sits under the bytes that produced it.

Constants used throughout (headers named, values never printed):

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_91cd77d4-0030-495d-81c4-37de0b298801
D=div_42529bfd-3620-42c3-93df-068da80201dc
COW=cow_85ac57ce-ce33-44dc-a00f-d74141fdd9fe          # version 0.1.4
```

---

## 1. ≥2 completed rounds after fillers were set

Fillers were registered **before the first trigger-round**, so every completed round counts.
The committed run log records it (`runs/2026-08-27-lux-ai/log.md:62`, quoted, not fetched — it is
this run's own log):

```
2026-08-27T18:43:11Z 50 fillers registered 200 BEFORE trigger: forester:v4=4269d16d
prospector:v4=3613cd05; unpause 200; trigger 200; round 1 pending; entrant_attributions = both champions
```

### Poll log (checks 1 + 3), every ~60 s inside the 75-minute bound (opened 18:44Z)

```
18:47:17Z  rounds=[{"n":1,"s":"completed"}]                       completed=1  — waiting
18:48:17Z  rounds=[{"n":1,"s":"completed"}]                       completed=1  — waiting
18:49:18Z  rounds=[{"n":1,"s":"completed"}]                       completed=1  — waiting
18:50:19Z  rounds=[{"n":1,"s":"completed"}]                       completed=1  — waiting
18:51:19Z  rounds=[{"n":1,"s":"completed"}]                       completed=1  — waiting
18:53:19Z  rounds=[{"n":1,"s":"completed"}]                       completed=1  — waiting
18:54:14Z  rounds=[{"n":1,"s":"completed"}]                       completed=1  — waiting
18:55:10Z  rounds=[{"n":1,"s":"completed"}]                       completed=1  — waiting
18:56:05Z  rounds=[{"n":1,"s":"completed"}]                       completed=1  — waiting
18:57:00Z  rounds=[{"n":1,"s":"completed"}]                       completed=1  — waiting
18:58:01Z  rounds=[{"n":2,"s":"pending"},{"n":1,"s":"completed"}] completed=1  — round 2 scheduled
18:58:56Z  rounds=[{"n":2,"s":"pending"},{"n":1,"s":"completed"}] completed=1  — waiting
18:59:52Z  rounds=[{"n":2,"s":"pending"},{"n":1,"s":"completed"}] completed=1  — waiting
19:00:47Z  rounds=[{"n":2,"s":"pending"},{"n":1,"s":"completed"}] completed=1  — waiting
19:01:43Z  rounds=[{"n":2,"s":"completed"},{"n":1,"s":"completed"}] completed=2 — BOUND SATISFIED
```

### Final fetch (fresh, 19:02Z)

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" -o /tmp/rounds.json -w "%{http_code}\n"
# 200 ; the body came back wrapped as {"entries":[…]} this run (dual-shape jq used anyway).
# Projection below (the raw round_config is ~4 KB of scheduler state per round):
jq 'if type=="array" then . else .entries end
    | map({id,round_number,status,error,created_at,completed_at,
           entrants:[.round_config.entrant_attributions[]?|{subject_id}]})' /tmp/rounds.json
```

```json
[
  {
    "id": "round_ee8f3123-7404-4d3a-a9a4-6f593e1c6b56",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-27T18:57:07.077490Z",
    "completed_at": "2026-08-27T19:01:22.858304Z",
    "entrants": [
      {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3"},
      {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"}
    ]
  },
  {
    "id": "round_83a470cc-d70e-4156-95f8-4aea43ff5b1e",
    "round_number": 1,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-27T18:42:06.478429Z",
    "completed_at": "2026-08-27T18:44:00.332925Z",
    "entrants": [
      {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3"},
      {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"}
    ]
  }
]
```

```bash
… | jq -r '[.entries[]|select(.status=="completed")]|length'
2
```

No round has status `failed` or `discarded`; `error` is `null` on both. Both rounds' seats are
the two champion players' ids (`ply_44ae9048…` = daveey, `ply_bac48eb1…` = daveey-1) — no filler
was seated.

**Status: TRUE** — rounds 1 (completed 18:44:00.332925Z) and 2 (completed 19:01:22.858304Z),
both after fillers were set at 18:43:11Z, both `error: null`.

---

## 2. Both champions ranked, fillers absent

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq .
# HTTP 200; bare JSON list (as playbook §11 says)
```

```json
[
  {
    "rank": 1,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 1030.5304984710244,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 2.0,
    "episodes_played": null,
    "win_rate": 1.0,
    "policy_label": "lux-ai-lumberjack:v4",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 969.4695015289755,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 0.0,
    "episodes_played": null,
    "win_rate": 0.0,
    "policy_label": "lux-ai-nightwatch:v4",
    "recent_rounds": null
  }
]
```

```
rank  player_name  policy_label            score    rounds_played  episode_wins
1     daveey       lux-ai-lumberjack:v4    1030.53  2              2.0
2     daveey-1     lux-ai-nightwatch:v4    969.47   2              0.0
```

The list has exactly two rows. Neither `lux-ai-forester:v4` nor `lux-ai-prospector:v4` appears,
and no row is labelled `Baseline (N)` — the fillers are **absent**, which the checklist allows.

**Status: TRUE** — both champions ranked with `rounds_played = 2 ≥ 1`; fillers absent.

---

## 3. Latest round's episode request completed with a replay

The flat `GET /episode-requests?round_id=` route is 405 as of 2026-08-26 (playbook §9), so the
nested route was used.

```bash
R=round_ee8f3123-7404-4d3a-a9a4-6f593e1c6b56          # max round_number among completed = 2
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}"
```

```json
[{"id": "ereq_336aa5ca-17f4-4729-86a5-874bb8974f59", "status": "completed"}]
```

```bash
EREQ=ereq_336aa5ca-17f4-4729-86a5-874bb8974f59
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
# HTTP 200
```

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/117bf12d-a428-47b0-a50c-ba62377cc8f9.replay",
  "participants": [
    {
      "position": 0,
      "kind": "policy",
      "policy_version_id": "8591b7b2-3be3-4fb7-b376-c71f3700ef45",
      "policy_id": "13e39031-1b1e-42c1-8b38-78d2101fa523",
      "policy_name": "lux-ai-lumberjack",
      "version": 4,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": false,
      "is_seed": false
    },
    {
      "position": 1,
      "kind": "policy",
      "policy_version_id": "4ff02033-1986-49de-b749-0e1882091d0b",
      "policy_id": "6a0910ea-cb9b-483c-965f-e6fc6dc74dfb",
      "policy_name": "lux-ai-nightwatch",
      "version": 4,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
      "player_name": "daveey-1",
      "is_filler": false,
      "is_seed": false
    }
  ],
  "participant_scores": [
    {"position": 0, "score": 1.0},
    {"position": 1, "score": 0.0}
  ]
}
```

The two `policy_version_id`s match STATE exactly (`8591b7b2-…` = champion 1, `4ff02033-…` =
champion 2); `is_filler` is `false` on both.

**Status: TRUE** — `status: "completed"`, non-null `replay_url`, participants are `daveey`
(lux-ai-lumberjack:v4) and `daveey-1` (lux-ai-nightwatch:v4).

---

## 4. Replay bytes are valid and show the game

### 4a. The bytes, and why `jq` alone is not the test here

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/117bf12d-a428-47b0-a50c-ba62377cc8f9.replay" \
     -o /tmp/ep.replay -w "HTTP:%{http_code} bytes:%{size_download}\n"
```

```
HTTP:200 bytes:252300
```

```bash
python3 -c "print(open('/tmp/ep.replay','rb').read()[:24])"
jq -e . /tmp/ep.replay
```

```
b'COWLDLUX\x01\x00\x06\x00lux-ai\x01\x001\xf8^\x95'
jq: parse error: Invalid numeric literal at line 1, column 32
```

This is the **documented exception**, declared in the design note *before* release:
`runs/2026-08-27-lux-ai/design.md` §"Replay bytes (self-sufficient)" (lines 1090–1117) states the
replay stays the starter's binary `COWLDLUX` container because the static wasm viewer parses
exactly that format, requires CI's `docker-smoke` to set `SMOKE_REQUIRE_REPLAY_JSON=0`, and
specifies the **phase-60 substitute verbatim** at lines 1105–1117: decode with the repo's
stdlib-only `tools/replay_summary.py`, which emits one strict-UTF-8 JSON object, and assert on
that. (Same precedent as `runs/2026-08-26-atari-cabinet` / `COWLDCAB`.)

### 4b. The substitute, run exactly as the design specifies, with the tool fetched fresh from the released repo

```bash
gh api repos/Metta-AI/cogame-lux-ai/contents/tools/replay_summary.py --jq '.content' \
 | base64 -d > /tmp/replay_summary.py        # 253 lines, python3 stdlib only
python3 /tmp/replay_summary.py /tmp/ep.replay > /tmp/ep.json
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
jq 'del(.directives)' /tmp/ep.json
```

```
strict UTF-8 JSON: ok
```

```json
{
  "protocol": "lux-ai/v1",
  "gameName": "lux-ai",
  "gameVersion": "1",
  "seed": 1601442680,
  "mapSize": 16,
  "maxTurns": 360,
  "names": ["daveey", "daveey-1"],
  "aliases": ["RED-alpha", "BLUE-alpha"],
  "policyKinds": ["llm", "llm"],
  "registrations": [
    {"seat": 0, "policy": "lux-ai-lumberjack", "kind": "llm"},
    {"seat": 1, "policy": "lux-ai-nightwatch", "kind": "llm"}
  ],
  "turnCount": 360,
  "tickCount": 514,
  "directiveRecords": 72,
  "fallbacks": 0,
  "stop": null,
  "results": {
    "names": ["daveey", "daveey-1"],
    "aliases": ["RED-alpha", "BLUE-alpha"],
    "scores": [1.0, 0.0],
    "win": [true, false],
    "reason": "complete",
    "endRule": "full_time",
    "cityTiles": [2, 0],
    "units": [2, 2],
    "fuel": [582, 0],
    "research": [34, 47],
    "cityTilesBuilt": [12, 6],
    "cityTilesLost": [10, 6],
    "unitsBuilt": [31, 7],
    "unitsLost": [29, 5],
    "resourcesMined": [[11573, 0, 0], [5055, 0, 0]],
    "nightsSurvived": [8, 7],
    "blockedMoves": [239, 73],
    "turnsPlayed": 360,
    "mapSize": 16,
    "seed": 1601442680,
    "policyKinds": ["llm", "llm"],
    "llmTurns": [36, 36],
    "fallbackTurns": [0, 0],
    "directivesRejected": [0, 0],
    "deadSeats": [false, false],
    "stopDetail": "",
    "winner": 0
  }
}
```

### 4c. `protocol` matches the declaration

`coworld_manifest_template.json` carries **no scalar top-level `protocol` field** — the only
`protocol`-keyed entries are the two prose blocks `game.protocols.player` and
`game.protocols.global`:

```bash
gh api repos/Metta-AI/cogame-lux-ai/contents/coworld_manifest_template.json --jq '.content' \
 | base64 -d | jq -r 'paths(scalars) as $p | select(($p|map(tostring)|join("."))|test("protocol")) | ($p|map(tostring)|join("."))'
```

```
game.protocols.player.type
game.protocols.player.value
game.protocols.global.type
game.protocols.global.value
```

The authoritative declaration of the replay protocol string is therefore the source constant the
manifest's `game.protocols.global` prose points at ("## The replay — Binary `COWLDLUX`"), plus
design.md line 1101:

```bash
gh api repos/Metta-AI/cogame-lux-ai/contents/src/lux/sim_types.nim --jq '.content' \
 | base64 -d | grep -n 'lux-ai/v1'
```

```
28:  ReplayProtocol* = "lux-ai/v1"
```

Replay says `"protocol": "lux-ai/v1"` → **match**. `gameName` `lux-ai` and `gameVersion` `1` also
match the manifest's `game.name` and the source's `GameVersion`.

### 4d. Decision content — not scripted, not fallbacks

```bash
jq '[.directives[]|select(.source=="llm")]|length'            # 72
jq '[.directives[]|select(.source!="llm")]|length'            # 0
jq '.fallbacks'                                               # 0
jq '[.directives[]|select(.note!="")]|length'                 # 72
jq '[.directives[]|select(.seat==0 and .source=="llm")]|length'   # 36
jq '[.directives[]|select(.seat==1 and .source=="llm")]|length'   # 36
jq -c '[.directives[].stance]|group_by(.)|map({s:.[0],n:length})'
```

```
72
0
0
72
36
36
[{"s":"contest","n":1},{"s":"expand","n":22},{"s":"fuel","n":41},{"s":"research","n":8}]
```

72/72 directives are `source: "llm"` with a non-empty `note`; **zero** fallbacks
(`results.fallbackTurns: [0,0]`, `directivesRejected: [0,0]`); both champion seats issued 36 LLM
directives each; four different stances were actually used.

**Deviation, recorded not hidden.** The design's substitute also asks for
`results.cityTiles[0] + results.cityTiles[1] > 2` ("somebody built something", design.md:1115).
The observed end-state is `cityTiles: [2, 0]` → sum **2**, which is **not > 2** — the threshold is
missed by one tile. The intent behind it is nonetheless directly evidenced by the same object:
`cityTilesBuilt: [12, 6]` (18 city tiles built over the episode), `cityTilesLost: [10, 6]`,
`nightsSurvived: [8, 7]`, `resourcesMined: [[11573,0,0],[5055,0,0]]`. The game's own win rule
("most city tiles standing at turn 360") resolved 2–0 to RED on standing tiles, so the end-state
number is small because night attrition is severe in this build, not because nothing was built.
Flagged for the judge; the four requirements `prompts/60-verify.md` check 4 itself lists are all
met.

**Status: TRUE** — strict-UTF-8 JSON via the design-declared substitute; `protocol` `lux-ai/v1`
matches; `results.reason == "complete"` (`endRule: full_time`, 360/360 turns — the
declared-acceptable `deadline` escape was not needed); 72/72 non-scripted LLM decisions, 0
fallbacks. One design-note content threshold (`cityTiles` sum > 2) not literally met — see above.

---

## 5. Hosted game log is clean

```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs.raw
```

```
HTTP:200 bytes:148558
```

The body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it was
decoded per-repr with `ast.literal_eval` before grepping (playbook §10):

```
decoded bytes per container: {'coworld-init-config': 0, 'bedrock-sidecar': 147751, 'game': 350, 'worker': 0}
```

```bash
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.txt || echo CLEAN
```

```
CLEAN
```

Belt and braces — the same grep against the **undecoded** bytes, and a bare `max_tokens` /
`stop_reason` sweep of the decoded text:

```bash
grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.raw   # 0
grep -o 'max_tokens' /tmp/logs.txt | wc -l                                                          # 0
grep -o '"stop_reason":"[a-z_]*"' /tmp/logs.txt | sort | uniq -c                                    # (no matches)
```

The whole decoded `game` container, verbatim:

```
lux-ai: listening on 0.0.0.0:8080
lux-ai llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
lux-ai: player connected on slot 0
lux-ai: seat 0 registered as LLM (lux-ai-lumberjack)
lux-ai: player connected on slot 1
lux-ai: seat 1 registered as LLM (lux-ai-nightwatch)
lux-ai: episode settled complete/full_time after 360 turns
```

Head of the `bedrock-sidecar` container (shows the sidecar bound to this exact episode request):

```
2026-08-27 18:57:14,823 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1",
"has_role_arn":true,"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar",
"episode_request_id":"336aa5ca-17f4-4729-86a5-874bb8974f59","job_request_id":"117bf12d-a428-47b0-a50c-ba62377cc8f9",
"role":"game","slot":"game","image_digest":"sha256:de9a7ee90d0c81224e41737d5632adb917e3ce0abb8a2204a640e126bc212a7f"}
[2026-08-27 18:57:15 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)
```

No Bedrock-capacity symptom appeared at all, so no cross-check against another LLM coworld was
needed.

**Status: TRUE** — zero matches for `falling back|LLM provider is unavailable|cut off at
max_tokens|rejected`, decoded and raw; the game container reports `episode settled
complete/full_time after 360 turns`.

---

## 6. The public page uses the static replay path

### 6a. Raw-HTML grep (source 1) — finds nothing, which is *unknown*, not false

```bash
curl -sS "https://softmax.com/lux-ai" -o /tmp/page2.html -w "HTTP:%{http_code} bytes:%{size_download}\n"
grep -o '<iframe[^>]*src="[^"]*"' /tmp/page2.html || echo "NO <iframe ...src=...> IN RAW HTML"
```

```
HTTP:200 bytes:686347
NO <iframe ...src=...> IN RAW HTML
```

Expected: the page is client-rendered for the iframe (playbook §Featured match, lighthouse
2026-08-22).

### 6b. Featured match — read from the page's own SSR payload (source 2, the one I used)

`GET https://softmax.com/lux-ai`, `state.playlist[0]`, unescaped:

```json
{"playlist":[{"episodeId":"aba8f475-a800-49de-9ee6-54df938b6671",
"coworldId":"cow_85ac57ce-ce33-44dc-a00f-d74141fdd9fe","coworldName":"lux-ai","coworldVersion":"0.1.4",
"replayUrl":"https://softmax-public.s3.amazonaws.com/replays/117bf12d-a428-47b0-a50c-ba62377cc8f9.replay",
"finishedAt":"2026-08-27T19:01:21.088110Z","roundNumber":2,"episodeNumber":1,"code":"lux-ai.r2.e1",
"matchup":{"divisionId":"div_42529bfd-3620-42c3-93df-068da80201dc","divisionName":"Competition",
"first":{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
"score":1030.5304984710244,"score_label":"MMR","rounds_played":2,"episode_wins":2,"win_rate":1,
"policy_label":"lux-ai-lumberjack:v4"},
"second":{"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
"score":969.4695015289755,"score_label":"MMR","rounds_played":2,"episode_wins":0,"win_rate":0,
"policy_label":"lux-ai-nightwatch:v4"}},"inspect…
```

A featured match **is** present, it is this run's round-2 episode (`lux-ai.r2.e1`, the same
`replayUrl` as checks 3–4), and its matchup is the two champions.

For completeness, the coworld detail API (source 3) — `featured_match` is `null` here, which is
the documented platform-wide behaviour and therefore not evidence either way:

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '.entries[]|select(.name=="lux-ai")|{id,canonical,replay_viewer,featured_match}'
```

```json
{"id":"cow_85ac57ce-ce33-44dc-a00f-d74141fdd9fe","name":"lux-ai","version":"0.1.4",
 "canonical":true,"replay_viewer":null,"featured_match":null}
{"id":"cow_48fbd033-9479-4b2d-bdf7-bedc94bc9e27","name":"lux-ai","version":"0.1.3","canonical":false, …}
{"id":"cow_cc4bb62c-d306-45bf-a2fa-bf6b4798330f","name":"lux-ai","version":"0.1.2","canonical":false, …}
{"id":"cow_29e6c50d-17ac-47d2-aca2-5d05167d4fdb","name":"lux-ai","version":"0.1.1","canonical":false, …}
```

`cow_85ac57ce…` v0.1.4 is `canonical: true` — the id in STATE is the canonical one.

### 6c. The iframe `src` itself — the call the page's own JS makes

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
 -d '{"coworld_id":"cow_85ac57ce-ce33-44dc-a00f-d74141fdd9fe",
      "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/117bf12d-a428-47b0-a50c-ba62377cc8f9.replay"}'
```

```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_85ac57ce-ce33-44dc-a00f-d74141fdd9fe/sha256%3Ae8483de3dd14a7549a44abdeada90e63bf37b6853f8101bd4e3e7c6e95d85e1c/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F117bf12d-a428-47b0-a50c-ba62377cc8f9.replay&v=2",
  "ready": true
}
```

Path shape: `/v2/coworlds/replays/**static**/<cow_id>/<sha>/index.html?replay=<s3 url>` — it is the
static bundle route, it ends `/index.html`, and `ready: true`. The `<sha>` is
`sha256:e8483de3dd14a7549a44abdeada90e63bf37b6853f8101bd4e3e7c6e95d85e1c` (URL-encoded), which is
byte-identical to `STATE.coworld.manifest_sha`. **No `/client/replay` pod URL appears anywhere.**

**Status: TRUE** — sources used: the page's SSR payload (`state.playlist[0]`) for the featured
match, and `POST /coworlds/replays/session` for the iframe `src`. Featured match present and it is
this run's round-2 champions-vs-champions episode; `src` is the static path.

---

## 7. Certification declared the static bundle

Source read: **the committed `runs/2026-08-27-lux-ai/release-result.json`** (the copy phase 40
downloaded and committed at 18:38 local, 3875 bytes). No re-download was needed, and `/tmp` was
not consulted.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-27-lux-ai/release-result.json
jq -r '.certify.ok'              runs/2026-08-27-lux-ai/release-result.json
```

```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
true
```

The required substring `Replay liveness: skipped (static replay bundle declared` is present
verbatim. (Cross-reference, quoted from this run's own log line 54: release run `33103630909`,
`canonical:true certify.ok:true replay_liveness=skipped-static`.)

**Status: TRUE** — read from the committed `runs/2026-08-27-lux-ai/release-result.json`.

---

## 8. The viewer, EXECUTED

### 8a. Dispatch (this run, 19:03:54Z)

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_85ac57ce-ce33-44dc-a00f-d74141fdd9fe/sha256%3Ae8483de3dd14a7549a44abdeada90e63bf37b6853f8101bd4e3e7c6e95d85e1c/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F117bf12d-a428-47b0-a50c-ba62377cc8f9.replay&v=2'
dispatched_at=2026-08-27T19:03:54Z
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status,event -L 10 \
 | jq -c 'sort_by(.createdAt)|reverse|.[0:3]'
```

```json
[{"createdAt":"2026-08-27T19:03:57Z","databaseId":33106609970,"event":"workflow_dispatch","status":"in_progress"},
 {"createdAt":"2026-08-27T15:22:13Z","databaseId":33087427495,"event":"workflow_dispatch","status":"completed"},
 {"createdAt":"2026-08-27T11:25:59Z","databaseId":33067338841,"event":"workflow_dispatch","status":"completed"}]
```

Run **33106609970** was created at 19:03:57Z, i.e. *after* `dispatched_at` 19:03:54Z — it is mine,
not the 15:22Z run.

```bash
gh run watch 33106609970 -R Metta-AI/coworld-builder --exit-status
```

```
✓ main viewer-check · 33106609970
✓ viewer-check in 42s (ID 98638037792)
  ✓ Install Playwright (pinned 1.55.0)
  ✓ Load the viewer
  ✓ Summary
  ✓ Upload the evidence
  ✓ Fail if the viewer did not load
watch exit=0
```

```bash
gh run download 33106609970 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-27-lux-ai/viewer-check
```

```
runs/2026-08-27-lux-ai/viewer-check/smoke-stderr.txt   (0 bytes)
runs/2026-08-27-lux-ai/viewer-check/smoke-stdout.txt   (753 bytes)
runs/2026-08-27-lux-ai/viewer-check/viewer-smoke.json  (1549 bytes)
runs/2026-08-27-lux-ai/viewer-check/viewer-smoke.png   (381223 bytes)
```

`smoke-stderr.txt` is empty — no thrown errors.

### 8b. The readouts, verbatim

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-27-lux-ai/viewer-check/viewer-smoke.json
```

```json
{"loaded":true,"ms":4048,"clock":"-- WAITING FOR PLAYERS","scorebug":"daveey RED-ALPHA 1 units · 0 fuel · 0 research 1 CITY TILES -- WAITING FOR PLAYERS 1 2 3 4 5 6 7 8 9 RESEARCH 0-200 · COAL 50 · URANIUM 200 daveey-1 BLUE-ALPHA 1 units · 0 fuel · 0 research 1 CITY TILES","feed_lines":0}
```

```bash
jq -c '.signals' runs/2026-08-27-lux-ai/viewer-check/viewer-smoke.json
```

```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"'  runs/2026-08-27-lux-ai/viewer-check/viewer-smoke.json   # null → no failure
jq -c '.status, .loading_text, .console_tail, .canvas_text' …
```

```
no failure
"OPEN"            # status
null              # loading_text — no "Loading replay…" stuck banner
[]                # console_tail — no console errors
{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
```

### 8c. The three clock readouts

```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-27-lux-ai/viewer-check/viewer-smoke.json
```

| scrub | clock readout |
|---|---|
| **0 %** | `-- WAITING FOR PLAYERS` |
| **50 %** | `TURN 198 / 360 · NIGHT 9/10 CYCLE 5 OF 9 · DIRECTIVE 20/36 · RED 10 – 4 BLUE` |
| **100 %** | `TURN 359 / 360 · NIGHT 10/10 CYCLE 9 OF 9 · DIRECTIVE 36/36 · RED 2 – 0 BLUE` |

Three **different** readouts; the shell does expose `#scrub` (no `"(no #scrub…)"` sentinel), and
the turn counter, cycle, directive counter and score all advance monotonically.

**Status: TRUE** — `loaded: true` (`data_replay_loaded: "true"`, 4048 ms, `failure: null`) **and**
the three clock readouts differ.

*Legibility observation for the coordinator (not a check failure):* the 0 % frame reads
`-- WAITING FOR PLAYERS` rather than `TURN 0 / 360` — the scrubber's left edge lands on the
pre-game lobby frame, so the very first thing a spectator sees is a lobby caption. Second,
`feed_lines: 0`: the DOM probe found no match-feed lines even though two directive bubbles are
plainly painted in the screenshot, so this game's directive commentary evidently lives outside the
element the probe counts. Both are phase-30 polish items, not correctness failures.

### 8d. The replay JSON the viewer was asked to draw (reconciliation source)

Early (`jq -c '.directives[]' /tmp/ep.json | head -4`):

```json
{"turn":0,"seat":0,"alias":"RED-alpha","source":"llm","latency_ms":3732,"stance":"expand","research":"coal","note":"Cycle 1: Six workers to richest wood. City at (5,7) will build more workers. Compact blob growth."}
{"turn":0,"seat":1,"alias":"BLUE-alpha","source":"llm","latency_ms":3732,"stance":"research","research":"coal","note":"Cycle 1: Build research bank. 4 workers on wood near start city, 1 cart. No 3rd tile yet—can't feed it. Research coal first, then pivot hard to coal mining."}
{"turn":10,"seat":0,"alias":"RED-alpha","source":"llm","latency_ms":1678,"stance":"expand","research":"coal","note":"Cycle 1: Six workers on richest wood tile at [4,6]. Build compact blob around [5,7]. Coal research proceeding. Shelter at night."}
{"turn":10,"seat":1,"alias":"BLUE-alpha","source":"llm","latency_ms":1678,"stance":"research","research":"coal","note":"Cycle 1 cont: 4 workers banking research for coal unlock. Hold at 1 city tile. Road to coal tile starts after coal researched."}
```

Middle (`jq -c '.directives[]|select(.turn>=180 and .turn<=210)' /tmp/ep.json`):

```json
{"turn":180,"seat":1,"alias":"BLUE-alpha","source":"llm","stance":"contest","research":"uranium","note":"5 tiles behind, turn 180. Contest RED's coal at [3,3] cluster. Deny their fuel engine. Build road to uranium [13,13] for phase 2."}
{"turn":190,"seat":0,"alias":"RED-alpha","source":"llm","stance":"expand","research":"none","note":"10 turns to dawn. City survives (1897 fuel, 10-turn margin). Wood at 17009; coal researched at 34/50. Continue wood-first expansion, shelter at night. Cart setu"}
{"turn":190,"seat":1,"alias":"BLUE-alpha","source":"llm","stance":"fuel","research":"uranium","note":"NIGHT TURN: fuel=18 turns safe. Shelter all units. Switch to fuel stance to bank resources for expansion. Contest failed; refocus on coal→city corridor and uran"}
{"turn":200,"seat":0,"alias":"RED-alpha","source":"llm","stance":"fuel","research":"none","note":"EMERGENCY: city survives only 2 turns. Haul all cargo home immediately. Switch to fuel stance. Focus on adjacent wood to rebuild. Night haul to survive."}
{"turn":200,"seat":1,"alias":"BLUE-alpha","source":"llm","stance":"fuel","research":"uranium","note":"CRITICAL: City survives tonight (8 turns fuel). RED leads 10-4 tiles. Fuel first, then expand. Coal research blocked by low research rate."}
```

Late (`jq -c '.directives[]' /tmp/ep.json | tail -4`):

```json
{"turn":340,"seat":0,"alias":"RED-alpha","source":"llm","stance":"expand","research":"none","note":"Turn 340: 2 city tiles, 4 workers, 24 turns fuel. Build workers to cap(8). Wood abundant. Hold position."}
{"turn":340,"seat":1,"alias":"BLUE-alpha","source":"llm","stance":"fuel","research":"none","note":"Turn 340: 0 cities vs RED's 2. Game nearly over. Shelter fuel, build nothing. Survive to 360."}
{"turn":350,"seat":0,"alias":"RED-alpha","source":"llm","stance":"fuel","research":"none","note":"Turn 350: city has 24 turns of fuel; switch to fuel+haul to ensure survival. Build workers to cap. Wood at 14838 is healthy."}
{"turn":350,"seat":1,"alias":"BLUE-alpha","source":"llm","stance":"fuel","research":"none","note":"Turn 350, night phase. 0 cities vs 2 RED. 2 workers with 200 wood cargo. Shelter through night 9, then reassess. Need immediate city or GG."}
```

```bash
jq -r '.results.scores, .results.win, .results.reason, .results.endRule, .results.cityTiles, .results.winner' /tmp/ep.json
```

```
[1,0]   [true,false]   "complete"   "full_time"   [2,0]   0
```

---

## Spectator judgment

**It is legible, it is moving, and it is unmistakably this game.** `viewer-smoke.png` (committed at
`runs/2026-08-27-lux-ai/viewer-check/viewer-smoke.png`, 381 KB, 1280×800) is a *full* frame of the
match at the 100 % scrub position, not a loading screen and not an empty canvas. Reading it
top-down: the headline clock reads **TURN 359 / 360 · NIGHT 10/10**, with
`CYCLE 9 OF 9 · DIRECTIVE 36/36 · RED 2 – 0 BLUE` on the sub-line; the scorebug flanks it with the
**real** policy owners on the outside and the in-game aliases underneath —
`daveey / RED-alpha / 2 units · 623 fuel · 34 research / **2** CITY TILES` on the left,
`daveey-1 / BLUE-alpha / 2 units · 0 fuel · 47 research / **0** CITY TILES` on the right — plus a
red/blue research bar captioned `RESEARCH 0-200 · COAL 50 · URANIUM 200`. Those numbers match the
replay's `results` object field for field (`units [2,2]`, `fuel [582,0]` ≈ the 623 shown one frame
earlier, `research [34,47]`, `cityTiles [2,0]`), so the picture and the record agree.

The board is a 16×16 night-lit island with visible terrain art, not placeholder blocks: grey rock
formations, ~35 green wood tiles in two mirror-symmetric clusters, two glowing red **city tiles**
in the upper right with gold outlines, and four unit chips (two red, two blue) with cargo pips
under them. Two directive bubbles are painted bottom-right, quoting the turn-350 notes *verbatim*
from the replay JSON above — `RED-alpha: "TURN 350: CITY HAS 24 TURNS OF FUEL; SWITCH TO FUEL+HAUL
TO ENSURE SURVIVAL…"` and `BLUE-alpha: "TURN 350, NIGHT PHASE. 0 CITIES VS 2 RED… NEED IMMEDIATE
CITY OR GG."` A spectator can therefore read *what* each side is doing and *why*, in the model's
own words, without leaving the frame.

Motion is proven by the three scrub readouts, not asserted: 0 % → lobby, 50 % → turn 198 with RED
ahead 10–4, 100 % → turn 359 with RED 2–0. That arc is exactly the arc in the replay: RED expands
to a ten-tile blob by mid-game (turn 190 note, `cityTilesBuilt: 12`), night attrition then guts
both sides (`cityTilesLost: [10, 6]`, RED's turn-200 "EMERGENCY: city survives only 2 turns"), and
RED limps to full time holding two tiles while BLUE holds none (`nightsSurvived [8,7]`,
`winner: 0`). The scrubber carries a two-colour area chart captioned **CITY TILES** plus **nine**
beat ticks (eight blue, one red) spaced across the 360 turns — the dusk / research / citylost / end
markers the design promised, each a clickable seek. Enlarging that strip (crop of the committed
png, `y 760–800`): a stepped trace runs left-to-right with a **red** band filling the first
roughly two thirds, a **blue** band appearing under it for a stretch in the last third, and both
collapsing to a flat line before the orange playhead at the right edge. The collapse at the right
matches `cityTiles: [2, 0]`; I cannot resolve the chart's axis convention (stacked per-side counts
vs. lead differential) at this resolution, so I am not claiming which side the blue band credits —
worth one human glance in phase 30, but it is a legibility question, not a correctness one.

**Chrome comparison — it is the starter's, not a rewrite.** Every element of the coworld-ctf
(paintbot/raid/hive) broadcast chrome is present and in its usual place: the bottom **transport
strip** with restart / step-back / pause / `+5s` / play / loop / fast-forward, the `spoilers`
toggle, the `359 / 359` frame counter, and the `1× 2× 4× 8× 16×` speed buttons at the right; the
**scrubber with the momentum graph** and clickable beat ticks directly under it; the **scorebug**
split left/right around the centre clock with the research bar between them; the letterboxed dark
board panel with the amber accent palette. This is not the cogame-gridlock failure mode — it looks
like the same product as the starter, with the game-specific block (day/night cycle, city tiles,
research thresholds) appended where the design said it would be. The one thing I cannot show from
this screenshot is the **endcard**, because the capture is at turn 359 of 360 — one frame short of
the end state — so the endcard is neither confirmed nor contradicted here; the last beat tick sits
near the scrubber's right edge.

Nothing is empty, frozen, or unreadable.

---

## Summary table

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 1 & 2, `error: null`, fillers set 18:43:11Z |
| 2 | Both champions ranked, fillers absent | **TRUE** — daveey #1 (2 rounds), daveey-1 #2 (2 rounds), no filler rows |
| 3 | Latest round's episode request completed w/ replay | **TRUE** — `ereq_336aa5ca…` completed, replay_url present, both champions seated |
| 4 | Replay bytes valid and show the game | **TRUE** — strict JSON via design-declared `replay_summary.py`; `lux-ai/v1`; `complete`/`full_time`; 72/72 LLM directives, 0 fallbacks. *Deviation: `cityTiles` sum 2, design asked > 2 (§4d).* |
| 5 | Hosted game log clean | **TRUE** — CLEAN, decoded and raw |
| 6 | Public page uses the static replay path | **TRUE** — featured match `lux-ai.r2.e1`; `…/replays/static/<cow>/<manifest_sha>/index.html?replay=…`, `ready:true` |
| 7 | Certification declared the static bundle | **TRUE** — committed `release-result.json`: `Replay liveness: skipped (static replay bundle declared…` |
| 8 | Viewer executed and judged | **TRUE** — run 33106609970, `loaded:true`, three differing clock readouts |
