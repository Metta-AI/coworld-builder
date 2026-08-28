# VERIFY — halite   (2026-08-28T08:33Z)

Verdict: **1 item false — check 4 (champion decisions are 100 % scripted; the LLM never answered)**

| # | item | verdict |
|---|---|---|
| 1 | ≥2 completed rounds after the fillers were set | **TRUE** |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** |
| 3 | Latest round's episode request completed with a replay | **TRUE** |
| 4 | Replay bytes valid **and show the game** | **FALSE** |
| 5 | Hosted game log clean | **TRUE** |
| 6 | Public page uses the static replay path, featured match present | **TRUE** |
| 7 | Certification declared the static bundle | **TRUE** |
| 8 | Spectator judgment — viewer executed, `loaded:true`, clock advances | **TRUE** |

- Run `2026-08-27-halite` · slug `halite` · repo `Metta-AI/cogame-halite` · version `0.1.0`
- `COW` = `cow_97d89fb8-8a54-423b-ac60-7080b318271a` · manifest `sha256:1c51119aacefa5ae5f99f1e1c06e992578486333a81e3d8395d60745dcd7630b`
- `L` = `league_82571537-04b2-4611-8200-59349283a022` · `D` = `div_165193cb-f037-4f20-ac3d-25a3a4a7d440`
- `BASE` = `https://softmax.com/api/observatory/v2`
- Headers on every Observatory call: `Authorization: Bearer <redacted>`, `User-Agent: coworld-builder/1.0`;
  `X-Use-Elevated-Privileges: true` added on `artifacts/logs` and on the filler-policies read. No header
  value is reproduced anywhere in this file.
- Evidence-source choices: **check 6** used the **SSR-payload + replay-session route** (the raw-HTML iframe
  grep and `/coworlds`' `featured_match` both came back empty — both pasted below); **check 7** used the
  **committed `runs/2026-08-27-halite/release-result.json`** (no re-download needed).
- Wall clock: verification opened 08:07:57Z, last round poll 08:26:23Z — **~19 min of the 75-min bound used**.
- Replay under test (latest completed round = round 2):
  `https://softmax-public.s3.amazonaws.com/replays/ce7c0511-7ba9-4287-8397-a7212fa2d7db.replay`
- Rendered evidence: `runs/2026-08-27-halite/viewer-check/` from **viewer-check run `33155420501`**
  (dispatched by this verifier at 08:27:34Z; identity confirmed from the run log's own `url:` line).

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" -o c1.json -w 'HTTP %{http_code}\n'
jq 'if type=="array" then . else .entries end | map({id,round_number,status,error,created_at,completed_at})' c1.json
jq -r '[ (if type=="array" then . else .entries end)[]|select(.status=="completed")]|length' c1.json
```
```
HTTP 200          (fetched 2026-08-28T08:26:32Z)
[
  {
    "id": "round_2a2453f5-1c47-4277-ad08-ad498be65dbc",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T08:21:01.950027Z",
    "completed_at": "2026-08-28T08:25:04.327230Z"
  },
  {
    "id": "round_24dc0f54-2b9c-4d75-90e7-baef10e7c454",
    "round_number": 1,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T08:06:00.440407Z",
    "completed_at": "2026-08-28T08:10:38.738998Z"
  }
]
```
```
2
```

`/rounds?league_id=` returned a **bare array** (playbook §2), so the prompt's `.entries[]` snippet was run
through `if type=="array" then . else .entries end`. No round is `failed` or `discarded`, so there is no
`error` string to quote.

Poll trail — each line an independent `GET /rounds?league_id=$L&limit=20`, HTTP 200 every time:

| poll (UTC) | round 1 | round 2 |
|---|---|---|
| 08:07:57Z | pending | — (not yet created) |
| 08:13:01Z | **completed** 08:10:38Z | — |
| 08:18:25Z | completed | — |
| 08:21:28Z | completed | pending (created 08:21:01Z) |
| 08:26:23Z | completed | **completed** 08:25:04Z |

**Fillers were in effect for both counted rounds.** `log.md` records the filler registration at
`2026-08-28T08:06:53Z 50 fillers 200 registered tidewalker=dc3af747… corsair=633dd3f6…`, i.e. before the
first trigger, so *every* round of this league qualifies. That is not left to the log line — the live
filler set and both rounds' seatings were fetched:

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}" -w 'HTTP %{http_code}\n'
```
```
HTTP 200          (fetched 2026-08-28T08:31Z)
{
  "filler_policy_versions": [
    {"policy_version_id": "dc3af747-7ccb-4cdd-9c25-2e14d93b1467", "policy_name": "halite-tidewalker",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"},
    {"policy_version_id": "633dd3f6-2647-4438-b407-6416b1c9f144", "policy_name": "halite-corsair",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"}
  ]
}
```

```bash
# round 1's episode: were the fillers actually seated?
curl -sS "$BASE/episode-requests/ereq_18dcbc0b-57c0-4b27-9fa6-296e6fc3a84a" "${AUTH[@]}" \
 | jq -c '[.participants[]|{position,policy_name,player_name,is_filler}]'
```
```
[{"position":0,"policy_name":"halite-tidereader","player_name":"daveey","is_filler":false},
 {"position":1,"policy_name":"halite-privateer","player_name":"daveey-1","is_filler":false},
 {"position":2,"policy_name":"halite-corsair","player_name":"daveey","is_filler":true},
 {"position":3,"policy_name":"halite-tidewalker","player_name":"daveey","is_filler":true}]
```

Round 2's seating is in §3 below (same shape, two `is_filler: true` seats). Both rounds' replay headers
name the filler seats `Baseline` / `Baseline (2)` (§4), which is the rename the filler list causes.

**Status: TRUE** — rounds 1 and 2 completed (08:10:38Z, 08:25:04Z), both with the filler set in force.

---

## 2. Both champions ranked — TRUE

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" -o c2.json -w 'HTTP %{http_code}\n'
jq . c2.json
```
```
HTTP 200          (fetched 2026-08-28T08:26:32Z)
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
    "policy_label": "halite-tidereader:v1",
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
    "policy_label": "halite-privateer:v1",
    "recent_rounds": null
  }
]
```
```bash
jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv' c2.json
```
```
1	daveey	halite-tidereader:v1	1030.5304984710244	2	2.0
2	daveey-1	halite-privateer:v1	969.4695015289755	2	0.0
```

The endpoint returned a bare list, as the playbook §11 says. Two rows, exactly the two champions:
`daveey` with `halite-tidereader:v1` and `daveey-1` with `halite-privateer:v1`, each `rounds_played = 2`
(≥ 1). The fillers `halite-tidewalker` / `halite-corsair` are **absent** from the board entirely — they are
seat-fillers, never ranked entrants.

**Status: TRUE.**

---

## 3. Latest round's episode request completed with a replay — TRUE

```bash
R=round_2a2453f5-1c47-4277-ad08-ad498be65dbc            # max_by(round_number) over completed rounds, §1
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" -w 'HTTP %{http_code}\n'   # nested route (playbook §9)
```
```
HTTP 200          (fetched 2026-08-28T08:26:50Z)
[{"id":"ereq_bdbd9a3f-4dba-4b6f-869d-e3e7abeefc9e","status":"completed","created_at":"2026-08-28T08:21:02.300926Z"}]
```

The flat route the prompt's snippet uses is gone; confirmed live this run, not assumed:

```bash
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}" -w 'HTTP %{http_code}\n'
```
```
{"detail":"Method Not Allowed"}
HTTP 405
```

```bash
EREQ=ereq_bdbd9a3f-4dba-4b6f-869d-e3e7abeefc9e
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants: [.participants[]|{position,policy_name,player_name,is_filler}], participant_scores}'
```
```
HTTP 200          (fetched 2026-08-28T08:26:50Z)
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/ce7c0511-7ba9-4287-8397-a7212fa2d7db.replay",
  "participants": [
    {"position": 0, "policy_name": "halite-tidereader", "player_name": "daveey",   "is_filler": false},
    {"position": 1, "policy_name": "halite-privateer",  "player_name": "daveey-1", "is_filler": false},
    {"position": 2, "policy_name": "halite-tidewalker", "player_name": "daveey",   "is_filler": true},
    {"position": 3, "policy_name": "halite-corsair",    "player_name": "daveey",   "is_filler": true}
  ],
  "participant_scores": [
    {"position": 0, "score": 709.0},
    {"position": 1, "score": 261.0},
    {"position": 2, "score": 1308.0},
    {"position": 3, "score": 1953.0}
  ]
}
```

`status == "completed"`, `replay_url` non-null, seats 0 and 1 are the champions owned by `daveey` and
`daveey-1`, seats 2–3 are the two fillers (`is_filler: true`, rendered `Baseline` / `Baseline (2)` in the
replay and the scorebug). Scores are present for all four seats.

**Status: TRUE.**

---

## 4. Replay bytes are valid and show the game — **FALSE**

The bytes are valid and the *game* is there. What is **not** there is the champions: both LLM seats
answered every single directive turn with the scripted fallback because the LLM call returned HTTP 403.

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/ce7c0511-7ba9-4287-8397-a7212fa2d7db.replay" \
     -o /tmp/ev/ep.replay -w 'HTTP %{http_code} bytes=%{size_download} type=%{content_type}\n'
jq -e . /tmp/ev/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
python3 -c "open('/tmp/ev/ep.replay','rb').read().decode('utf-8'); print('strict utf-8 decode: ok')"
jq -r '.format, .version, .gameVersion, .protocol, .coworld, .seed' /tmp/ev/ep.replay
```
```
HTTP 200 bytes=1368961 type=application/octet-stream
strict UTF-8 JSON: ok
strict utf-8 decode: ok
cogame-halite-replay
1
1.0.0
halite/1
halite
378163377
```

`protocol` = `halite/1`, which is the string the coworld's own replay contract pins — from the live
manifest read this run, `GET $BASE/coworlds/$COW` → `docs.pages[id=replay.md]`:
`{"format":"cogame-halite-replay","version":1,"gameVersion":"1.0.0","protocol":"halite/1", …}`. Match.

```bash
jq -r '.names, .aliases, .policySources' /tmp/ev/ep.replay
jq -c '.results|{reason,end_rule,final_turn,scores,placement,winner,banked,mined,stolen,collisions_won,collisions_lost,llm_turns,fallbacks,dead_seats,eliminated_turn,stop_detail}' /tmp/ev/ep.replay
jq -c '.stop' /tmp/ev/ep.replay
```
```
["daveey","daveey-1","Baseline","Baseline (2)"]
["FLEET-ALPHA","FLEET-BRAVO","FLEET-CHARLIE","FLEET-DELTA"]
["llm","llm","scripted:tidewalker","scripted:corsair"]
```
```
{"reason":"complete","end_rule":"full_time","final_turn":399,
 "scores":[709,261,1308,1953],"placement":[3,4,2,1],"winner":3,
 "banked":[709,261,1308,1953],"mined":[18107,12010,18020,10643],"stolen":[2060,1045,2499,8313],
 "collisions_won":[9,5,10,30],"collisions_lost":[18,20,20,15],
 "llm_turns":[0,0,0,0],
 "fallbacks":[{"timeout":0,"malformed":0,"wrong_turn":0,"disconnected":0,"host_error":0},
              {"timeout":0,"malformed":0,"wrong_turn":0,"disconnected":0,"host_error":0},
              {"timeout":0,"malformed":0,"wrong_turn":0,"disconnected":0,"host_error":0},
              {"timeout":0,"malformed":0,"wrong_turn":0,"disconnected":0,"host_error":0}],
 "dead_seats":[false,false,false,false],"eliminated_turn":[null,null,null,null],"stop_detail":""}
```
```
{"rule":"full_time","turn":399}
```

`results.reason == "complete"` with `end_rule: full_time` — the `deadline` exception was not needed.

The game mechanics are recorded and rich (this replay stores events per turn under `.turns[].events`, not
a flat `.events[]`, so the prompt's `.events[]` filters were rewritten accordingly):

```bash
jq -r '[.turns[].events[]|.k]|group_by(.)|map("\(.[0])\t\(length)")|.[]' /tmp/ev/ep.replay
```
```
collide	61
convert	13
deposit	163
lead	64
mine	6640
note	40
spawn	123
yardraze	5
```

**The failure.** Every one of the 40 `note` events — the champions' own decision records, two per
directive turn across 20 directive turns — carries `source: "scripted"` and the *same* provider error:

```bash
jq -r '[.turns[].events[]|select(.k=="note")|.source]|group_by(.)|map("\(.[0])\t\(length)")|.[]' /tmp/ev/ep.replay
jq -r '[.turns[].events[]|select(.k=="note")|.text]|unique|.[]' /tmp/ev/ep.replay
```
```
scripted	40
```
```
holding the last directive (PermissionDeniedError: Error code: 403 - {'Message': 'Invalid API Key format: Must start with pre-defined prefix
```

```bash
jq -c '[.turns[]|{t:.t, notes:[.events[]|select(.k=="note")|{seat,source,latencyMs}]}|select(.notes|length>0)]|.[0:3][]' /tmp/ev/ep.replay
```
```
{"t":0,  "notes":[{"seat":0,"source":"scripted","latencyMs":1107},{"seat":1,"source":"scripted","latencyMs":1122}]}
{"t":20, "notes":[{"seat":0,"source":"scripted","latencyMs":25},  {"seat":1,"source":"scripted","latencyMs":21}]}
{"t":40, "notes":[{"seat":0,"source":"scripted","latencyMs":20},  {"seat":1,"source":"scripted","latencyMs":22}]}
```

So the fallback share of champion decisions is **40/40 = 100 %**, and `results.llm_turns == [0,0,0,0]`
says the same thing from the engine's side: **not one turn in the episode was answered by an LLM.** The
check requires "champion seats' decisions are non-scripted with non-trivial content — not all fallbacks";
here they are *all* the scripted `tidewalker` compile, and the only "content" is one repeated 403 string.

**Three attempts, three different approaches, same answer:**

1. *This round's replay* (round 2, above): `llm_turns [0,0,0,0]`, 40/40 notes scripted.
2. *A different round* — round 1's replay
   `https://softmax-public.s3.amazonaws.com/replays/ba9b16ec-f8ee-4498-81c6-c1b25e10d677.replay`,
   fetched separately this run:
   ```
   strict UTF-8 JSON: ok · protocol halite/1 · results.reason complete · end_rule full_time
   llm_turns: [0,0,0,0] · note sources: scripted 40 · same 403 text
   ```
3. *Is it the documented platform-wide LLM cause?* **No — cross-checked live against two other LLM
   coworlds' latest completed episodes in the same window**, per the prompt's requirement to cite the
   cross-check rather than assume the exception:
   ```bash
   # snake-royale, league_9f435441-…, latest completed round → ereq_7e684a08-5abe-419d-bacf-d0bdde8265a1
   curl -sS "$BASE/episode-requests/$E/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}"   # decoded
   ```
   ```
   game | snake-royale llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
   game | snake-royale llm: seat 1 attempt 1 failed, will retry: llm transport: Timeout was reached
          POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
   ```
   ```bash
   # gen-generals-io, league_03508cde-…, latest completed round → ereq_ba808905-92bf-4932-b4f2-36e87de53cd3
   ```
   ```
   bedrock-sidecar | … bedrock_sidecar_call {"episode_request_id":"ba808905-…"}     ← the sidecar was CALLED
   game | gen-generals-io llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
   ```
   Both healthy coworlds reach Bedrock by **POSTing the episode's local sidecar**,
   `http://127.0.0.1:9100/model/<model>/invoke`, and `gen-generals-io`'s sidecar logs actual
   `bedrock_sidecar_call` entries. halite's sidecar logs **only** `bedrock_sidecar_started` and never a
   single call (§5 log, pasted there), and halite's error is an AWS **API-key-format** 403, not a capacity
   symptom. So this is not the SPEC-documented "platform-wide Bedrock capacity" exception; it is specific
   to this coworld. No documented exception covers it → the item is false.

**Observation for the fixer (reported, not fixed — code was read, not touched):** in
`Metta-AI/cogame-halite@main`, `players/llm.py:248-263` builds `AnthropicBedrock()` with no `base_url`
when `USE_BEDROCK=true`, i.e. it talks to the real Bedrock endpoint from the **player** pod, while the
episode's sidecar is attached to the **game** pod (`bedrock-sidecar` log line in §5:
`"role":"game","slot":"game"`). `tools/ci/policies.json` does set `"USE_BEDROCK":"true"` on both champion
policies, so the intended path was chosen — it just isn't the path the platform provides. The two
coworlds that work today make the call from the game container against `127.0.0.1:9100`.

**Status: FALSE** — bytes valid, protocol matched, `reason == "complete"`, but the champion seats made
**zero** LLM decisions (`llm_turns [0,0,0,0]`, 40/40 notes `source: "scripted"`, all carrying
`403 … Invalid API Key format`). The episode shows the game; it does not show the champions playing it.

Ordered event excerpts (early / middle / late), reused in §8:

```bash
jq -r '.turns[]|select(.t<=3)|.t as $t|.events[]|[$t,(.seat//""),.k,((.amount//.text//.pos//.bank//"")|tostring)]|@tsv' /tmp/ev/ep.replay
jq -r '.turns[]|select(.t>=200 and .t<=201)| …' ; jq -r '.turns[]|select(.t>=397)| …'
```
```
early
0	0	note	holding the last directive (PermissionDeniedError: Error code: 403 - {'Message': 'Invalid API Key format…
0	1	note	holding the last directive (PermissionDeniedError: Error code: 403 - {'Message': 'Invalid API Key format…
1	0	convert	110          1	1	convert	120       1	2	convert	320      1	3	convert	330
1	0	lead	4500
2	0	spawn	110          2	1	spawn	120         2	2	spawn	320        2	3	spawn	330
middle
200	0	mine	1 … 200	0	mine	3   (8 mine events for seat 0, 3 for seat 1, 3 for seat 2, 4 for seat 3)
200	0	note	holding the last directive (PermissionDeniedError: …)
200	1	note	holding the last directive (PermissionDeniedError: …)
late
398	0	deposit	205
398	2	deposit	43
398	3	deposit	30
398	3	deposit	182
```
```bash
jq -c '[.turns[]|.t as $t|.events[]|select(.k=="collide")|{t:$t,pos,survivor,lost,stolen}]|.[0:3][]' /tmp/ev/ep.replay
jq -c '[.turns[]|.t as $t|.events[]|select(.k=="yardraze")|{t:$t,pos,yardSeat,shipSeat}]|.[]' /tmp/ev/ep.replay
jq -c '.turns[398]|{t,hash,banks:[.players[]|.[0]]}' /tmp/ev/ep.replay
```
```
{"t":13,"pos":45,"survivor":{"seat":0,"ship":"6-1"},"lost":[{"seat":0,"ship":"2-1","cargo":188}],"stolen":188}
{"t":13,"pos":59,"survivor":{"seat":1,"ship":"6-2"},"lost":[{"seat":1,"ship":"2-2","cargo":188}],"stolen":188}
{"t":13,"pos":381,"survivor":{"seat":2,"ship":"6-3"},"lost":[{"seat":2,"ship":"2-3","cargo":188}],"stolen":188}
{"t":120,"pos":222,"yardSeat":1,"shipSeat":3}
{"t":247,"pos":110,"yardSeat":0,"shipSeat":3}
{"t":383,"pos":98,"yardSeat":0,"shipSeat":1}
{"t":392,"pos":120,"yardSeat":1,"shipSeat":3}
{"t":395,"pos":222,"yardSeat":1,"shipSeat":3}
{"t":398,"hash":"4d63b255b6dc7ea9","banks":[709,261,1308,1953]}
```

---

## 5. Hosted game log is clean — TRUE

The logs body is python byte-string reprs under `===== container: … =====` headers, so it was decoded with
`ast.literal_eval` per repr before grepping (playbook §10) — a line-based grep on the raw bytes undercounts.

```bash
curl -sS "$BASE/episode-requests/ereq_bdbd9a3f-4dba-4b6f-869d-e3e7abeefc9e/artifacts/logs" \
     "${AUTH[@]}" "${ELEV[@]}" -o logs.raw -w 'HTTP %{http_code} bytes=%{size_download}\n'
python3 …ast.literal_eval per container… > logs.txt      # 4 containers, 1702 decoded bytes
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs.txt || echo CLEAN
```
```
HTTP 200 bytes=1738
decoded bytes: 1702 containers: 4
CLEAN
```

The whole decoded log, verbatim (it is short):

```
===== container: coworld-init-config =====

===== container: bedrock-sidecar =====
2026-08-28 08:21:12,517 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1","has_role_arn":true,"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar","episode_request_id":"bdbd9a3f-4dba-4b6f-869d-e3e7abeefc9e","job_request_id":"ce7c0511-7ba9-4287-8397-a7212fa2d7db","role":"game","slot":"game","image_digest":"sha256:692c2d21788c38e1b70c064e72b552fd737a3056383facd26825f86be4e7c413"}
[2026-08-28 08:21:12 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-08-28 08:21:12,716 INFO hypercorn.error Running on http://127.0.0.1:9100 (CTRL + C to quit)

===== container: game =====
cogame-halite 1.0.0 listening on 0.0.0.0:8080; seats=4 turns=400 seed=378163377
seat 3 (FLEET-DELTA) connected
seat 3 registered policy='scripted:corsair' label='corsair'
seat 2 (FLEET-CHARLIE) connected
seat 2 registered policy='scripted:tidewalker' label='tidewalker'
seat 0 (FLEET-ALPHA) connected
seat 0 registered policy='llm' label='Play the bank. Mine the richest cell wit'
seat 1 (FLEET-BRAVO) connected
seat 1 registered policy='llm' label='Play the collision rule. Keep your hulls'
episode end: reason=complete end_rule=full_time turn=399 scores=[709, 261, 1308, 1953] llm_turns=[0, 0, 0, 0] dead=[False, False, False, False]
wrote results (1075 bytes) to file:///coworld/results.json
wrote replay (1368961 bytes) to file:///coworld/replay
episode settled 197.1s after the episode began (hard stop 660s; this container has been up 197.1s)
seat 2 disconnected
seat 0 disconnected
seat 1 disconnected
seat 3 disconnected

===== container: worker =====
```

**Status: TRUE** — zero matches for `falling back|LLM provider is unavailable|cut off at max_tokens|rejected`.

**Caveat the judge should read with §4:** this CLEAN result is *not* evidence that the LLM path is healthy
here, and must not be used as such. Two reasons, both visible in the bytes above: (a) the artifacts endpoint
returns only `coworld-init-config`, `bedrock-sidecar`, `game` and `worker` — the **player pods**, where
halite makes its LLM calls, have no container in this bundle, so the 403 never reaches this log; and
(b) `players/llm.py` deliberately logs `will retry` and never `falling back` (its own docstring: "never
``falling back`` — the phase-60 grep distinguishes them"). The same log's own
`llm_turns=[0, 0, 0, 0]` line is the tell, and the sidecar logs `bedrock_sidecar_started` but never a
single `bedrock_sidecar_call` (contrast `gen-generals-io`'s sidecar in §4, which logs calls).

---

## 6. The public page uses the static replay path — TRUE

*Source used: the SSR payload + the replay-session route.* Both cheaper sources were tried first and are
recorded here as empty, not as failures:

```bash
curl -sS "https://softmax.com/halite" -o page.html -w 'HTTP %{http_code} bytes=%{size_download}\n'
grep -o '<iframe[^>]*src="[^"]*"' page.html || echo '(no match — grep found nothing)'
```
```
HTTP 200 bytes=730314          (fetched 2026-08-28T08:27:18Z)
(no match — grep found nothing)
```
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)|.[]|select(.name=="halite")|{id,canonical,replay_viewer,featured_match}'
```
```
{
  "id": "cow_97d89fb8-8a54-423b-ac60-7080b318271a",
  "canonical": true,
  "replay_viewer": null,
  "featured_match": null
}
```

Both empty results are the platform-wide behaviour the playbook §Featured match records (client-rendered
iframe; `featured_match` null for every coworld). The featured match **is** server-rendered into the page's
SSR payload at `state.playlist[0]` — extracted from the same `page.html` fetched above:

```
"playlist":[{"episodeId":"e63c2005-4106-4102-bb25-2a40ea6e94e8",
 "coworldId":"cow_97d89fb8-8a54-423b-ac60-7080b318271a","coworldName":"halite","coworldVersion":"0.1.0",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/ce7c0511-7ba9-4287-8397-a7212fa2d7db.replay",
 "finishedAt":"2026-08-28T08:24:55.398351Z","roundNumber":2,"episodeNumber":1,"code":"halite.r2.e1",
 "matchup":{"divisionId":"div_165193cb-f037-4f20-ac3d-25a3a4a7d440","divisionName":"Competition",
  "first":{"rank":1,"player_name":"daveey","score":1030.5304984710244,"rounds_played":2,"episode_wins":2,
           "win_rate":1,"policy_label":"halite-tidereader:v1"},
  "second":{"rank":2,"player_name":"daveey-1","score":969.4695015289755,"rounds_played":2,"episode_wins":0,
            "win_rate":0,"policy_label":"halite-privateer:v1"}}, …
```

A featured match is present (`halite.r2.e1`), it is the round-2 episode of §3, and its matchup names both
ranked champions — so this is not the "fewer than two ranked players" absence.

The iframe `src` is what the page's own JS asks for:

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_97d89fb8-8a54-423b-ac60-7080b318271a",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/ce7c0511-7ba9-4287-8397-a7212fa2d7db.replay"}' \
  -w 'HTTP %{http_code}\n'
```
```
HTTP 200          (fetched 2026-08-28T08:27:25Z)
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_97d89fb8-8a54-423b-ac60-7080b318271a/sha256%3A1c51119aacefa5ae5f99f1e1c06e992578486333a81e3d8395d60745dcd7630b/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fce7c0511-7ba9-4287-8397-a7212fa2d7db.replay",
  "ready": true
}
```
```bash
curl -sS -o /dev/null -w 'iframe src GET HTTP %{http_code} type=%{content_type}\n' "${SRC%%#*}"
```
```
iframe src GET HTTP 200 type=text/html; charset=utf-8
```

The path is `/v2/coworlds/replays/static/<cow_id>/<manifest_sha, URL-encoded>/index.html`, `ready: true`,
and the replay arrives as the URL-encoded **`#replay=` fragment** — the form the playbook records for
2026-08-28; both fragment and query form are the static route. `<sha>` is the coworld's manifest hash and
matches STATE exactly (`sha256:1c51119aacefa5ae5f99f1e1c06e992578486333a81e3d8395d60745dcd7630b`). There
is **no** `/client/replay` pod URL anywhere in it.

**Status: TRUE.**

---

## 7. Certification declared the static bundle — TRUE

*Source used: the committed `runs/2026-08-27-halite/release-result.json`* (phase 40's artifact, committed in
`8b09815 40 halite: release 0.1.0 canonical+certified`). No re-download was needed and `/tmp` was not read.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-27-halite/release-result.json
git log --oneline -1 -- runs/2026-08-27-halite/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
8b09815 40 halite: release 0.1.0 canonical+certified
```

Contains the required string `Replay liveness: skipped (static replay bundle declared`.

**Status: TRUE.**

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — TRUE

*(a) Dispatch.* The iframe `src` from §6 (fragment and all) was opened in headless chromium by
`viewer-check.yml` in `Metta-AI/coworld-builder`, dispatched by this verifier at **08:27:34Z**:

```bash
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:4][]|[.databaseId,.createdAt,.status]|@tsv'
```
```
33155441744	2026-08-28T08:27:56Z	in_progress     ← another run, NOT mine
33155420501	2026-08-28T08:27:36Z	in_progress     ← mine (2 s after the dispatch)
33154949153	2026-08-28T08:20:24Z	completed
33153918882	2026-08-28T08:04:55Z	completed
```

Two runs were created seconds apart (the fleet runs in parallel), so "the latest run" would have been the
wrong one. Ownership was proven from the run's own log line rather than from timing alone:

```bash
gh run view 33155420501 -R Metta-AI/coworld-builder --log | grep -m1 'url:'
```
```
viewer-check	Load the viewer	2026-08-28T08:28:08.05Z url: https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_97d89fb8-8a54-423b-ac60-7080b318271a/sha256%3A1c51119aacefa5ae5f99f1e1c06e992578486333a81e3d8395d60745dcd7630b/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fce7c0511-7ba9-4287-8397-a7212fa2d7db.replay
```
```bash
gh run watch 33155420501 -R Metta-AI/coworld-builder --exit-status ; echo "watch exit=$?"
gh run download 33155420501 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-27-halite/viewer-check
ls -l runs/2026-08-27-halite/viewer-check/
```
```
watch exit=0        (green: the workflow's own "Fail if the viewer did not load" gate passed)
-rw-r--r-- 1 root root      0 smoke-stderr.txt
-rw-r--r-- 1 root root    687 smoke-stdout.txt
-rw-r--r-- 1 root root   1521 viewer-smoke.json
-rw-r--r-- 1 root root 794966 viewer-smoke.png
```

That directory is committed with this file.

*(b) The readouts, verbatim.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-27-halite/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":2106,"clock":"TURN 8 / 399 MINING","scorebug":"ALPHA daveey 2500 ♔ AFLOAT 218 4 SHIPS · 1 YARDS AT RISK 0 CHARLIE Baseline 2500 AFLOAT 218 4 SHIPS · 1 YARDS AT RISK 0 TURN 8 / 399 MINING BRAVO daveey-1 2500 AFLOAT 218 4 SHIPS · 1 YARDS AT RISK 0 DELTA Baseline (2) 2500 AFLOAT 218 4 SHIPS · 1 YARDS AT RISK 0","feed_lines":0}
```
```bash
jq -c '.signals' … ; jq -r '.failure // "no failure"' … ; jq -c '.canvas_text' …
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["ready"],"bridge_ready":true,"bridge_error":[]}
```
```
no failure
{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
console_tail: ["[bridge] ready"]
```

The three scrub readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | clock readout |
|---|---|
| 0 % | `TURN 8 / 399 MINING` |
| 50 % | `TURN 200 / 399 MINING` |
| 100 % | `TURN 398 / 399 HAULING` |

**Both conditions hold: `loaded: true` (via `data-replay-loaded="true"` *and* the `coworld-replay` bridge's
`ready`, first frame at 2106 ms) and the three clock readouts differ** (turn 8 → 200 → 398, and the phase
word changes `MINING` → `HAULING`). The shell does expose `#scrub`; no "(no #scrub…)" caveat is needed.
`canvas_text.total == 0` means the renderer draws no text inside the canvas at all (labels live in the DOM
chrome), so the `never_inside` guard is vacuously 0 — no caption is stranded off-canvas.

*(c) Spectator judgment.* The screenshot (`viewer-check/viewer-smoke.png`, 1280×800, taken at the 100 %
scrub position) shows a **legible, complete game**, and it is the game the replay records. Top-left and
top-right are four scorebug plates — `ALPHA daveey 709`, `CHARLIE Baseline 1308`, `BRAVO daveey-1 261`,
`DELTA Baseline (2) 1953`, each with `AFLOAT`, ship and yard counts and an `AT RISK` figure, a crown on the
leader — and those four banked numbers are **exactly** `results.scores == [709, 261, 1308, 1953]` from §4,
seat for seat. Centre-top is the transport clock `TURN 398 / 399` with the phase caption `HAULING`. The
board fills the middle: a 21 × 21 torus of pale halite-crystal cells over a dark ground, cell shading
thinning where fleets have mined it out, with ships in four distinct fleet colours (orange, teal, pink,
green), fat cargo pips on the loaded hulls, and boxed shipyard tiles. Bottom-left is the starter's transport
strip — restart, step-back, play, `+5`, step, loop, fast-forward, a `spoilers` toggle and the endcard chip
`DELTA WINS 398 / 399` (matching `results.winner == 3`); bottom-right the `1×…16×` speed selector; across
the bottom the scrubber with its momentum graph and coloured beat markers spread across the whole strip in
clusters (the replay has 61 `collide`, 13 `convert`, 5 `yardraze` and 64 `lead` beats to place). Bottom-right of the board is the feed, showing
`DELTA banks 182`, `DELTA banks 30`, `CHARLIE banks 43`, `ALPHA banks 205` — which reconciles line for line
with the late excerpt in §4: `398 3 deposit 182`, `398 3 deposit 30`, `398 2 deposit 43`, `398 0 deposit
205`. The DOM `feed_lines: 0` is not a contradiction: that field was captured at the initial paint (turn 8,
before any deposit had happened), and the rendered feed at turn 398 is visibly populated. Nothing is empty,
frozen or unreadable: the clock advances under the scrubber, the picture is dense with state, and a
spectator can read who is winning (DELTA, 1953 banked) and why (30 collisions won and 8313 halite stolen,
per §4's results).

**Chrome provenance:** the screenshot looks like the starter family — the same dark transport strip with the
`+5`/loop/fast-forward cluster and `spoilers` toggle, the same scrubber-with-momentum-graph and beat
markers, the same corner scorebug plates and the same endcard win chip as coworld-ctf / paintbot / raid /
hive. Design note declared `coworld-ctf` as the single chrome source (`client/chrome_common.js` and
`client/broadcast_core.js` byte-for-byte), and what rendered is consistent with that. This is not a
gridlock-style rewrite that merely shares ids.

**One legibility observation for the coordinator (not a check-8 failure):** what the viewer shows is a
well-drawn *scripted* game. Because of §4, both `daveey` plates are being driven by the fallback compile,
so the `note` speech lines a spectator would read as the champions' reasoning are all the same 403 error
string. The picture is honest about the episode it was given; the episode is the problem.

**Status: TRUE** (`loaded: true`, three differing clock readouts, rendered evidence committed).

---

## Definition-of-done summary

Seven of eight items are TRUE on fetched evidence. **Check 4 is FALSE** and no documented exception covers
it: in both completed rounds, both champion seats produced `llm_turns == 0` and 40/40 `note` events with
`source: "scripted"` carrying `PermissionDeniedError: Error code: 403 … 'Invalid API Key format: Must start
with pre-defined prefix'`, while two other LLM coworlds' episodes in the same window reached Bedrock
normally through the episode sidecar at `http://127.0.0.1:9100`. The ladder, the leaderboard, the static
viewer path, the certification and the rendered viewer are all sound; the champions never played.
