# VERIFY — hive   (2026-08-23T08:02Z)

Verdict: **all-true** (8 of 8 TRUE)

Run `2026-08-23-hive` · coworld `cow_89df098f-6f9b-42ee-adc0-ecf1252103cd` v`0.1.1` ·
manifest sha `sha256:8e16a28a45164d671865fee2068f719bf1f57fc2117702d0420b4ede01cf9b2b` ·
league `league_2d1d904b-5465-4b84-9845-b28164d22f7e` ·
division `div_86b9824f-b420-4d0a-8902-a7878b2102c7`.

Every fetch below was made fresh during this phase-60 sub-agent session (07:42Z–08:02Z).
The one documented exception is check 7, whose evidence is by design the committed
`runs/2026-08-23-hive/release-result.json` (see that section).

Headers sent on every Observatory call, values never printed:
`Authorization: Bearer $SOFTMAX_TOKEN`, `User-Agent: coworld-builder/1.0`, and on the
artifacts/logs read additionally `X-Use-Elevated-Privileges: true`.

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | **TRUE** |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** |
| 3 | Latest round's episode request completed with a replay | **TRUE** |
| 4 | Replay bytes valid and show the game | **TRUE** |
| 5 | Hosted game log clean | **TRUE** |
| 6 | Public page uses the static replay path | **TRUE** |
| 7 | Certification declared the static bundle | **TRUE** |
| 8 | Spectator judgment (viewer EXECUTED in headless chromium) | **TRUE** |

---

## 1. ≥2 completed rounds after the fillers were set

Fillers `hive-marcher:v1` (`79e9d9b4-…`) and `hive-driftling:v1` (`ab07597a-…`) were registered
at **2026-08-23T07:41:09Z** (`runs/2026-08-23-hive/log.md` line: *"50 fillers registered: …
(response lists exactly these two, neither champion)"*), i.e. **before round 2 was triggered**.
Round 1 was auto-created at 07:40:00Z — before the fillers and before champion #2 — and failed.
Only rounds **≥ 2** are counted.

```
GET https://softmax.com/api/observatory/v2/rounds?league_id=league_2d1d904b-5465-4b84-9845-b28164d22f7e&limit=20
```

Shape observed this run: **`{entries: [...], limit, offset, total_count}`** (an object, *not*
the bare array phase 50 saw on `/leagues`). Defensive filter used everywhere:
`(if type=="array" then . else .entries end)`.

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)|map(select(.status=="completed"))|length'
```
```
2
```

Full body (fetched 2026-08-23T07:59:13Z):

```json
{
  "total_count": 3,
  "entries": [
    {
      "id": "round_0eaae974-ba6c-4c00-9d9b-9c2a506e900f",
      "round_number": 3,
      "status": "completed",
      "error": null,
      "created_at": "2026-08-23T07:55:24.741491Z",
      "updated_at": null
    },
    {
      "id": "round_11ff8df8-81ec-4085-bb39-4224f27d03c5",
      "round_number": 2,
      "status": "completed",
      "error": null,
      "created_at": "2026-08-23T07:40:24.383711Z",
      "updated_at": null
    },
    {
      "id": "round_497af483-2674-458b-b88c-39d78090e357",
      "round_number": 1,
      "status": "failed",
      "error": "Temporal RoundWorkflow failed before settling the round.",
      "created_at": "2026-08-23T07:40:00.435327Z",
      "updated_at": null
    }
  ]
}
```

**Round 1's `error` verbatim, as required:** `Temporal RoundWorkflow failed before settling the
round.` — the documented signature of a `trigger-round` issued before any filler exists
(`playbooks/observatory-api.md` §6). It predates the filler registration (07:40:00Z vs
07:41:09Z) and both champions' seating, and is not counted.

Both counted rounds seated both champions. `round_config.entrant_attributions` for round 3:

```json
[{"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player",
  "policy_version_id":"5db1a013-76c1-48f3-8589-6892dfb84f35",
  "league_policy_membership_id":"lpm_ea1204ff-00e2-43a4-a95b-640791dfc455"},
 {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","subject_type":"player",
  "policy_version_id":"08245c7d-8554-4cb8-b1ae-e5b3d5fc7ecb",
  "league_policy_membership_id":"lpm_24a00a1f-59f3-4425-826b-ffa9e52fb218"}]
```

(round 1's, for contrast, lists **only** `ply_44ae9048…` — champion #2 was not yet submitted.)

Round 3 arrived on the ladder's own 15-minute cadence; **no `trigger-round` was issued by this
verifier.** Polls logged: 07:45:47Z (r2 only), 07:51:19Z (r2 only), 07:55:57Z (r3 pending),
07:59:04Z (r3 completed). Elapsed inside the 75-minute bound: 17 minutes.

**Status: TRUE** — rounds **2** (created 07:40:24Z, `completed`) and **3** (created 07:55:24Z,
`completed`), both after the fillers were set at 07:41:09Z.

---

## 2. Both champions ranked; fillers absent or Baseline

```
GET https://softmax.com/api/observatory/v2/divisions/div_86b9824f-b420-4d0a-8902-a7878b2102c7/leaderboard
```

Shape observed: **bare JSON list** (not `.entries`), as `playbooks/observatory-api.md` §11 says.

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey-1	hive-swarmraid:v1	1001.4695015289755	2	1.0
2	daveey	hive-pathwright:v1	998.5304984710245	2	1.0
```

Raw body (fetched 2026-08-23T07:59:13Z):

```json
[{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
  "score":1001.4695015289755,"score_label":"Elo","score_value_type":"integer",
  "rounds_played":2,"episode_wins":1.0,"episodes_played":null,"win_rate":0.5,
  "policy_label":"hive-swarmraid:v1","recent_rounds":null},
 {"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
  "score":998.5304984710245,"score_label":"Elo","score_value_type":"integer",
  "rounds_played":2,"episode_wins":1.0,"episodes_played":null,"win_rate":0.5,
  "policy_label":"hive-pathwright:v1","recent_rounds":null}]
```
```bash
$ curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq 'length'
2
```

- `daveey` present, `rounds_played = 2` ≥ 1, `policy_label = hive-pathwright:v1` (champion #1). ✅
- `daveey-1` present, `rounds_played = 2` ≥ 1, `policy_label = hive-swarmraid:v1` (champion #2). ✅
- The leaderboard has exactly **2 rows**: neither filler (`hive-marcher:v1`, `hive-driftling:v1`)
  appears at all — the "fillers absent" branch of the requirement. ✅

**Status: TRUE.**

---

## 3. The latest completed round's episode request completed, with a replay and the right participants

Latest completed round = **round 3**, `round_0eaae974-ba6c-4c00-9d9b-9c2a506e900f`
(`max_by(.round_number)` over the completed set in check 1).

```
GET https://softmax.com/api/observatory/v2/episode-requests?round_id=round_0eaae974-ba6c-4c00-9d9b-9c2a506e900f&limit=20
```
```json
{"keys":["entries","next_cursor"],"n":1}
{"id":"ereq_4dce5786-0067-4298-983c-fb8cb143fa66","status":"completed"}
```

```
GET https://softmax.com/api/observatory/v2/episode-requests/ereq_4dce5786-0067-4298-983c-fb8cb143fa66
```
```bash
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants: [.participants[]|{position,policy_name,player_name,is_filler}], participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/334e0e3a-c0bb-40d6-81a3-e3bb09d6780d.replay",
  "participants": [
    {"position": 0, "policy_name": "hive-pathwright",  "player_name": "daveey",   "is_filler": false},
    {"position": 1, "policy_name": "hive-swarmraid",   "player_name": "daveey-1", "is_filler": false},
    {"position": 2, "policy_name": "hive-marcher",     "player_name": "daveey",   "is_filler": true},
    {"position": 3, "policy_name": "hive-driftling",   "player_name": "daveey",   "is_filler": true}
  ],
  "participant_scores": [
    {"position": 0, "score": 0.11848341232227488},
    {"position": 1, "score": 0.36492890995260663},
    {"position": 2, "score": 0.3886255924170616},
    {"position": 3, "score": 0.12796208530805686}
  ]
}
```

`status == "completed"` ✅ · `replay_url` non-null ✅ · participants name **`daveey`** (seat 0,
champion #1) and **`daveey-1`** (seat 1, champion #2), both `is_filler: false`, and the two
fillers carry `is_filler: true` ✅. Scores sum to 1.0 exactly (constant-sum, per design §Scoring).

Inside the replay, the fillers are anonymised to `Baseline` / `Baseline (2)`:
`.names.players == ["daveey","daveey-1","Baseline","Baseline (2)"]` (pasted in check 4).

For completeness, round 2's episode request — fetched at 07:43Z, the same shape — was
`ereq_948b0444-f981-475f-905d-3a162bff515f`, `status: "completed"`,
`replay_url: …/88876cb8-52e0-4278-b7c4-28f82e39ff8e.replay`, same four participants.

**Status: TRUE.**

---

## 4. Replay bytes are valid and show the game

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/334e0e3a-c0bb-40d6-81a3-e3bb09d6780d.replay" -o /tmp/ep3.replay -w 'http=%{http_code} bytes=%{size_download}\n'
```
```
http=200 bytes=211002
```
(The S3 URL is plain, not presigned; no query string, nothing redacted.)

**Strict UTF-8 JSON** — two independent strict parsers:

```bash
jq -e . /tmp/ep3.replay >/dev/null && echo "strict UTF-8 JSON: ok"
python3 -c "d=open('/tmp/ep3.replay','rb').read(); d.decode('utf-8'); print('python strict utf-8 decode: ok, %d bytes' % len(d))"
```
```
strict UTF-8 JSON: ok
python strict utf-8 decode: ok, 211002 bytes
```

**Protocol and end condition:**

```bash
jq -r '.protocol, .results.reason, .results.end_rule' /tmp/ep3.replay
```
```
hive.replay.v1
complete
full_time
```

`protocol == "hive.replay.v1"` matches the manifest / design note §Replay bytes. ✅
`results.reason == "complete"` with `end_rule == "full_time"` — the **normal** ending, so the
design note's declared-acceptable `deadline`/`wall_clock` exception is **not needed here.** ✅

**Champion-seat decisions.** Hive does not emit a generic `decision` event; its decision record
is the `doctrines` array (one entry per seat per turn, `source: "llm"|"scripted"|"fallback"`)
plus `doctrine` / `fallback` events — design note §Event vocabulary:
*"a champion seat's `doctrine` events must carry `source: "llm"` with varying parameter values
and real `note` content, not all fallbacks."* The check-4 jq is adapted accordingly:

```bash
# which seats are champions (LLM) vs fillers (scripted)
jq -c '.names' /tmp/ep3.replay
```
```json
{"players":["daveey","daveey-1","Baseline","Baseline (2)"],
 "aliases":["Magenta","Amber","Teal","Lime"],
 "policy_kinds":["llm","llm","scripted","scripted"],
 "colours":["#e26db5","#f2c14e","#4ecdc4","#9fd356"]}
```
Seats 0 and 1 are the `llm` seats = `daveey` / `daveey-1` = the two champions.

```bash
# doctrine source, per seat  (the analogue of "[.events[]|select(.type=="decision")]|length")
jq -c '[.doctrines[]|{seat,source}]|group_by(.seat)
       |map({seat:.[0].seat,n:length,by_source:(group_by(.source)|map({(.[0].source):length})|add)})' /tmp/ep3.replay
```
```json
[{"seat":0,"n":20,"by_source":{"llm":20}},
 {"seat":1,"n":20,"by_source":{"llm":20}},
 {"seat":2,"n":20,"by_source":{"scripted":20}},
 {"seat":3,"n":20,"by_source":{"scripted":20}}]
```

```bash
# the analogue of "[.events[]|select(.fallback==true)]|length"
jq -r '[.events[]|select(.type=="fallback")]|length'          /tmp/ep3.replay
jq -r '[.doctrines[]|select(.source=="fallback")]|length'     /tmp/ep3.replay
```
```
0
0
```

**Zero fallbacks out of 40 champion decisions** — not merely "a small minority", none at all.
Confirmed independently in the results document: `"turns_llm":[20,20,0,0]`,
`"fallback_turns":[0,0,0,0]`, and every `fallback_causes` bucket zero.

```bash
# non-trivial, varying content
jq -c '[.doctrines[]|select(.seat<2)]|group_by(.seat)
       |map({seat:.[0].seat,turns:length,sources:([.[].source]|unique),
             distinct_notes:([.[].note]|unique|length),
             distinct_param_tuples:([.[]|"\(.scouts)/\(.trail_gain)/\(.poach)/\(.spread)/\(.lay_food)/\(.lay_home)/\(.recall)/\(.focus|tostring)/\(.focus_weight)"]|unique|length)})' /tmp/ep3.replay
```
```json
[{"seat":0,"turns":20,"sources":["llm"],"distinct_notes":19,"distinct_param_tuples":3},
 {"seat":1,"turns":20,"sources":["llm"],"distinct_notes":20,"distinct_param_tuples":7}]
```

First 14 rows of the champion doctrine stream
(`turn, seat, source, scouts, trail_gain, poach, spread, lay_food, lay_home, recall, focus, focus_weight, latency_ms`):

```bash
jq -r '.doctrines[]|select(.seat<2)|[.turn,.seat,.source,.scouts,.trail_gain,.poach,.spread,.lay_food,.lay_home,.recall,(.focus|tostring),.focus_weight,.latency_ms]|@tsv' /tmp/ep3.replay | head -14
```
```
0	0	llm	60	25	15	30	50	55	false	null	0	4116
0	1	llm	35	70	75	65	55	75	false	[10,5]	75	4116
1	0	llm	60	25	15	30	50	55	false	[15,8]	70	2529
1	1	llm	35	70	75	65	55	75	false	[10,5]	75	2529
2	0	llm	12	85	15	30	90	55	false	[15,8]	80	3755
2	1	llm	35	70	75	65	55	75	false	[4,2]	75	3755
3	0	llm	12	85	15	30	90	55	false	[15,8]	80	2682
3	1	llm	35	80	75	70	55	75	false	[9,4]	75	2682
4	0	llm	12	85	15	30	90	55	false	[15,8]	80	2953
4	1	llm	35	80	75	70	55	75	false	[10,4]	75	2953
5	0	llm	12	85	15	30	90	55	false	[15,8]	80	2746
5	1	llm	35	80	75	70	55	75	false	[10,4]	75	2746
6	0	llm	12	85	15	30	90	55	false	[15,8]	80	2710
6	1	llm	35	80	75	70	55	75	false	[10,4]	95	2710
```

Both seats share a `latency_ms` per turn — the design's one-parallel-batch-per-turn shape
(§Decisions), visible in the data. Seat 0 (`hive-pathwright`) does exactly what its prompt says:
opens `scouts 60 / trail_gain 25` with no focus, then at turn 2 inverts to
`scouts 12 / trail_gain 85 / lay_food 90 / focus [15,8] @ 80`. Seat 1 (`hive-swarmraid`) holds
`poach 75` the whole match and moves its focus block from turn to turn.

Real `note` content (turns 0/6/12/19, both champion seats):

```bash
jq -r '.doctrines[]|select(.seat<2 and (.turn==0 or .turn==6 or .turn==12 or .turn==19))|[.turn,.seat,.note,.say]|@tsv' /tmp/ep3.replay
```
```
0	0	Turn 0: No roads yet, no caches found. High scouts to explore, low trail_gain to avoid reinforcing nothing. Lay minimal trails while searchi	Spreading out to find food
0	1	Early game: establish poach doctrine. Rival grid empty so hold scouts at 35 to gather intel. Focus centre-left block to intercept rival road	Hunt their roads, not food
6	0	delivered_last_turn=3, up from 2. Road to [127,70] is alive. Cache has 42 units. Hold doctrine—three turns builds roads, one turn breaks the	Road builds. Hold steady.
6	1	Turn 6: Leading 56-52. Centre bonanza [10,4] is prime target - all colonies converge there. Rival grid shows Teal/Magenta lanes fading at [0	Centre bonanza - poach and pile 
12	0	Cache [127,70] at 42 units. Carrying=16, delivered_last_turn=0 but road is live and building. Hold doctrine—trails take turns to build, one 	Road holds. Feed it.
12	1	Turn 12: Leading 74-72 over Teal by 2pts. Rival grid shows Teal roads concentrated top-right [16-19,0-1] and scattered mid-field. Centre bon	Raid Teal roads, hold lead
19	0	Cache [127,70] at 42 units still live. carrying=16 confirms road holds. delivered_last_turn=0 is normal mid-haul. Hold doctrine—trails take 	Road holds. Stay locked.
19	1	Turn 19: Trailing Teal 76-82 by 6. Rival grid shows Teal density at [9-11,9-10]. Maintain aggressive poach raid on their southern cluster. H	Raid Teal south cluster
```

These cite live view fields (`delivered_last_turn`, `carrying`, specific cells, the rival grid,
the running scoreboard) that only a policy actually reading the observation could produce. The
scripted filler seats, by contrast, emit the fixed templates `marcher: opening` / `driftling:
drift` — so the two kinds are distinguishable in the bytes.

**The champion seats doing the thing the game is about** — food carried home and roads raided:

```bash
jq -c '[.events[].type]|group_by(.)|map({(.[0]):length})|add' /tmp/ep3.replay
jq -c '[.events[]|select(.type=="deliver")|.c]|group_by(.)|map({seat:.[0],delivers:length})' /tmp/ep3.replay
jq -c '[.events[]|select(.type=="raid")]|group_by(.colony)|map({colony:.[0].colony,raids:length})' /tmp/ep3.replay
```
```json
{"deliver":211,"doctrine":80,"end":1,"harvest":235,"match_start":1,"raid":13,"recall":2,
 "source_gone":32,"source_spawn":11,"trail_war":27,"turn_start":20}
[{"seat":0,"delivers":25},{"seat":1,"delivers":77},{"seat":2,"delivers":82},{"seat":3,"delivers":27}]
[{"colony":"Amber","raids":10},{"colony":"Lime","raids":2},{"colony":"Teal","raids":1}]
```

`Amber` is seat 1 = `daveey-1` = `hive-swarmraid`, the champion whose whole prompt is *"Let the
others find the food. Take it off their road."* — it ran **10 of the match's 13 raids** and
delivered 77 units. The strategy in the prompt is legible in the event stream.

Results document:

```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],
 "policy_kinds":["llm","llm","scripted","scripted"],
 "scores":[0.11848341232227488,0.36492890995260663,0.3886255924170616,0.12796208530805686],
 "delivered":[25,77,82,27],"total_delivered":211,
 "turns_llm":[20,20,0,0],"fallback_turns":[0,0,0,0],
 "winner":2,"reason":"complete","end_rule":"full_time","final_tick":4800,"seed":1139974405}
```

**Status: TRUE** — 211 002 bytes, strict UTF-8 JSON under both `jq -e` and Python;
`protocol: "hive.replay.v1"` matches the manifest; `results.reason: "complete"` /
`end_rule: "full_time"`; 40/40 champion decisions `source: "llm"`, **0 fallbacks**, 39 distinct
notes across 40 turns.

---

## 5. Hosted game log is clean

```
GET https://softmax.com/api/observatory/v2/episode-requests/ereq_4dce5786-0067-4298-983c-fb8cb143fa66/artifacts/logs
     headers: Authorization, User-Agent, X-Use-Elevated-Privileges
```
```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs3.txt -w 'http=%{http_code} bytes=%{size_download}\n'
wc -lc /tmp/logs3.txt
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs3.txt || echo CLEAN
```
```
http=200 bytes=83767
   11 83767 /tmp/logs3.txt
CLEAN
```

The fetch is real and non-empty (83 767 bytes) and covers all four containers:

```bash
grep -oE '^===== container: [a-z0-9-]+ =====' /tmp/logs3.txt
```
```
===== container: coworld-init-config =====
===== container: bedrock-sidecar =====
===== container: game =====
===== container: worker =====
```

First 900 bytes **verbatim** (`head -c 900 /tmp/logs3.txt`), showing this is the right episode's
log and that the LLM was really invoked from the game pod. Nothing token-shaped appears; the
`episode_request_id` / `job_request_id` match check 3's `ereq_4dce5786-…` and the round-3 replay
uuid `334e0e3a-…`:

```
===== container: coworld-init-config =====
b''

===== container: bedrock-sidecar =====
b'2026-08-23 07:55:32,255 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1","has_role_arn":true,"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar","episode_request_id":"4dce5786-0067-4298-983c-fb8cb143fa66","job_request_id":"334e0e3a-c0bb-40d6-81a3-e3bb09d6780d","role":"game","slot":"game","image_digest":"sha256:b75297f5f792305d9744505e43f10385900e046c52f0b910a4283b3409bc665b"}\n[2026-08-23 07:55:32 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)\n2026-08-23 07:55:32,444 INFO hypercorn.error Running on http://127.0.0.1:9100 (CTRL + C to quit)\n2026-08-23 07:55:55,492 INFO __main__ bedrock_sidecar_call {"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar","episode_request_id":"4dce5786-006
```

No documented-exception clause is needed: there is no `LLM provider is unavailable` line to
excuse. (Round 2's log, fetched at 07:44Z, was also `CLEAN` at 83 774 bytes.)

**Status: TRUE.**

---

## 6. The public page uses the static replay path

**Source (a) — raw HTML grep.** Attempted first, per the prompt:

```bash
curl -sS "https://softmax.com/hive" -o /tmp/hive_page2.html -w 'http=%{http_code} bytes=%{size_download}\n'
grep -o '<iframe[^>]*src="[^"]*"' /tmp/hive_page2.html || echo "NO MATCH"
```
```
http=200 bytes=353078
NO MATCH — page is client-rendered (documented: playbooks/observatory-api.md §Featured match)
```
Recorded as **unknown, not a failure**, exactly as the prompt directs.

**Source (b) — the coworld detail API.** Also attempted; also not evidence, as the playbook's
lighthouse note says (`featured_match` is `null` platform-wide):

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)[]|select(.name=="hive")|{id,canonical,replay_viewer,featured_match}'
```
```json
{"id":"cow_89df098f-6f9b-42ee-adc0-ecf1252103cd","canonical":true,"replay_viewer":null,"featured_match":null}
```

**Source (c) — the two things that ARE evidence, and the ones I used.**

*(c1) The featured match, server-rendered into the page's SSR payload at `state.playlist[0]`*
(extracted from the 353 078 bytes fetched above; backslash-escapes unescaped for readability):

```json
"playlist":[{"episodeId":"50773220-5b97-4519-ac94-a38d6c1c4566",
  "coworldId":"cow_89df098f-6f9b-42ee-adc0-ecf1252103cd",
  "coworldName":"hive","coworldVersion":"0.1.1",
  "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/334e0e3a-c0bb-40d6-81a3-e3bb09d6780d.replay",
  "finishedAt":"2026-08-23T07:57:17.083017Z","roundNumber":3,"episodeNumber":1,
  "code":"hive.r3.e1",
  "matchup":{"divisionId":"div_86b9824f-b420-4d0a-8902-a7878b2102c7","divisionName":"Competition",
    "first":{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
             "player_name":"daveey-1","score":1001.4695015289755,"score_label":"Elo", ...
```

A featured match **is present** (`hive.r3.e1`), and it is the round-3 replay verified in check 4.
The `matchup` names both ranked players — the "two ranked players" precondition holds.

*(c2) The iframe `src`, from the call the page's own JS makes:*

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_89df098f-6f9b-42ee-adc0-ecf1252103cd",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/334e0e3a-c0bb-40d6-81a3-e3bb09d6780d.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_89df098f-6f9b-42ee-adc0-ecf1252103cd/sha256%3A8e16a28a45164d671865fee2068f719bf1f57fc2117702d0420b4ede01cf9b2b/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F334e0e3a-c0bb-40d6-81a3-e3bb09d6780d.replay&v=2",
  "ready": true
}
```

Matched against the required shape
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`:

| Segment | Required | Got |
|---|---|---|
| route | `/v2/coworlds/replays/static/` | `/v2/coworlds/replays/static/` ✅ |
| `<cow_id>` | `cow_89df098f-6f9b-42ee-adc0-ecf1252103cd` | same ✅ |
| `<sha>` | manifest hash, URL-encoded | `sha256%3A8e16a28a…01cf9b2b` = `sha256:8e16a28a45164d671865fee2068f719bf1f57fc2117702d0420b4ede01cf9b2b` ✅ |
| tail | `/index.html?replay=<s3 url>` | `/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F334e0e3a….replay&v=2` ✅ |
| forbidden | no `/client/replay` pod URL | the string `/client/replay` does not occur ✅ |
| static delivery | `ready: true` and path ends `/index.html` | both ✅ |

**Which source I used:** the raw-HTML grep found nothing (client-rendered) and `/coworlds`
returned `featured_match: null`; the verdict rests on the page's own SSR payload
(`state.playlist[0]`, for the featured match) plus `POST /coworlds/replays/session`
(for the iframe `src`) — the two the playbook's lighthouse note establishes as the real sources.

**Status: TRUE** — featured match present, iframe `src` is the static route, `ready: true`,
no `/client/replay`.

---

## 7. Certification declared the static bundle

**Source read: the committed `runs/2026-08-23-hive/release-result.json`** — the artifact phase 40
downloaded and committed in `e058fa8 "40: hive 0.1.1 canonical+certified (run 32625651640);
phase -> 50"`. The file was present, so **no `gh run download` was needed** and `/tmp` was never
consulted.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-23-hive/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Surrounding fields, for context:

```bash
jq -c '{ok, version, canonical, certify:{ok:.certify.ok, replay_liveness:.certify.replay_liveness}}' runs/2026-08-23-hive/release-result.json
```
```json
{"ok":true,"version":"0.1.1","canonical":true,
 "certify":{"ok":true,
  "replay_liveness":"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"}}
```

Contains the required substring `Replay liveness: skipped (static replay bundle declared`. ✅

**Status: TRUE.**

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged

### 8(a) Dispatch

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_89df098f-6f9b-42ee-adc0-ecf1252103cd/sha256%3A8e16a28a45164d671865fee2068f719bf1f57fc2117702d0420b4ede01cf9b2b/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F334e0e3a-c0bb-40d6-81a3-e3bb09d6780d.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
```
Dispatched **2026-08-23T08:00:25Z**; the run created after the dispatch is
**`32627090556`** (createdAt `2026-08-23T08:00:27Z`).

```bash
gh run view 32627090556 -R Metta-AI/coworld-builder --json status,conclusion
```
```json
{"conclusion":"success","status":"completed"}
```
```bash
gh run download 32627090556 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-23-hive/viewer-check
ls -l runs/2026-08-23-hive/viewer-check/
```
```
-rw-r--r-- 1 root root      0 Aug 23 08:01 smoke-stderr.txt
-rw-r--r-- 1 root root    413 Aug 23 08:01 smoke-stdout.txt
-rw-r--r-- 1 root root   1178 Aug 23 08:01 viewer-smoke.json
-rw-r--r-- 1 root root 424962 Aug 23 08:01 viewer-smoke.png
```

(An earlier dispatch, run `32626367708` at 07:44Z, loaded the round-2 replay and also returned
`loaded: true` with three differing clocks. It was superseded and deleted when round 3 became the
featured match; the committed artifact is the round-3 one, which matches checks 3/4/6.)

### 8(b) The readouts

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-23-hive/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":6611,"clock":"3:19 TURN 0/20","scorebug":"daveey FOOD 0 Magenta Baseline FOOD 0 Teal 3:19 TURN 0/20 daveey-1 FOOD 0 Amber Baseline (2) FOOD 0 Lime","feed_lines":0}
```
```bash
jq -c '.signals' runs/2026-08-23-hive/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```
```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-23-hive/viewer-check/viewer-smoke.json
```

| scrub position | `#clock` readout |
|---|---|
| 0 % | `3:19 TURN 0/20` |
| 50 % | `1:37 TURN 10/20` |
| 100 % | `FINAL GAME OVER` |

```bash
jq -r '.failure // "no failure"' runs/2026-08-23-hive/viewer-check/viewer-smoke.json
jq -c '.console_tail'            runs/2026-08-23-hive/viewer-check/viewer-smoke.json
wc -c runs/2026-08-23-hive/viewer-check/smoke-stderr.txt
```
```
no failure
["[bridge] loading","[bridge] ready"]
0 runs/2026-08-23-hive/viewer-check/smoke-stderr.txt
```

**Both gate conditions hold:**
1. `loaded: true` — the viewer drew a frame and said so **twice**: `data-replay-loaded="true"`
   *and* the `coworld-replay` bridge's `ready`. First frame at **6 611 ms**. ✅
2. **The three clock readouts differ** — `3:19 TURN 0/20` → `1:37 TURN 10/20` →
   `FINAL GAME OVER`. The replay advances; it is not one frozen frame. ✅

### 8(b′) Supporting: the static bundle's assets (all fetched this run)

Every asset the shell references, fetched from the same iframe-`src` base
`…/replays/static/cow_89df098f-…/sha256%3A8e16a28a…/`:

| Asset (as referenced) | Referenced by | HTTP | Bytes | Content-Type |
|---|---|---|---|---|
| `index.html` | the iframe `src` | 200 | 117 563 | `text/html; charset=utf-8` |
| `./wire_constants.js` | `index.html <script src>` | 200 | 164 | `text/javascript; charset=utf-8` |
| `./chrome_common.js` | `index.html <script src>` | 200 | 40 022 | `text/javascript; charset=utf-8` |
| `./hive_replay.js` | `index.html <script src>` (emscripten loader) | 200 | 62 516 | `text/javascript; charset=utf-8` |
| `./static_replay.js` | `index.html <script src>` | 200 | 7 640 | `text/javascript; charset=utf-8` |
| `./broadcast_core.js` | `index.html <script src>` | 200 | 11 871 | `text/javascript; charset=utf-8` |
| `hive_replay.wasm` | named in `hive_replay.js` | 200 | 227 909 | `application/wasm` |
| `hive_replay.data` | named in `hive_replay.js` | 200 | 391 704 | `application/octet-stream` |
| `./font.ttf` | `index.html @font-face` (fallback; the primary is inlined base64) | 200 | 390 340 | `application/octet-stream` |
| `art/meadow_floor.jpg` | `broadcast_core.js` `loadArt()` | 200 | 1 579 | `image/jpeg` |
| `art/rock.png` | `broadcast_core.js` `loadArt()` | 200 | 4 844 | `image/png` |
| `art/nest_amber.png` | `broadcast_core.js` `loadArt()` | 200 | 5 046 | `image/png` |
| `art/nest_teal.png` | `broadcast_core.js` `loadArt()` | 200 | 4 927 | `image/png` |
| `art/nest_lime.png` | `broadcast_core.js` `loadArt()` | 200 | 4 964 | `image/png` |
| `art/nest_magenta.png` | `broadcast_core.js` `loadArt()` | 200 | 5 181 | `image/png` |
| `art/food_cache.png` | `broadcast_core.js` `loadArt()` | 200 | 3 783 | `image/png` |
| `art/ant.png` | `broadcast_core.js` `loadArt()` | 200 | 650 | `image/png` |
| `art/ant_laden.png` | `broadcast_core.js` `loadArt()` | 200 | 672 | `image/png` |

All 200, all non-trivial, none an HTML error page (the `.wasm` is served as `application/wasm`
and the images as `image/*`). The asset list was derived from the served files, not assumed:

```bash
grep -oE '<script[^>]*src="[^"]*"|<link[^>]*href="[^"]*"' index.html
```
```
<script src="./wire_constants.js"
<script src="./chrome_common.js"
<script src="./hive_replay.js"
<script src="./static_replay.js"
<script src="./broadcast_core.js"
```
```bash
grep -oE '[A-Za-z0-9_.-]+\.(wasm|data)' hive_replay.js | sort -u
```
```
hive_replay.data
hive_replay.wasm
```
```bash
grep -n 'assetBase' broadcast_core.js static_replay.js
```
```
broadcast_core.js:39:    this.assetBase = assetBase || './art';
broadcast_core.js:61:      return loadImage(self.assetBase + '/' + n);
static_replay.js:154:      assetBase: "./art"
```

*One 404, and why it is not a defect:* `static_replay_worker.js` returns
`404 (48 bytes, application/json)`. It is **not referenced by anything in the bundle** —
`grep -n 'Worker' static_replay.js` returns nothing; the builder shipped the main-thread viewer
instead of paintbot's OffscreenCanvas-Worker shell, a deviation recorded at phase 20
(`log.md`: *"builder deviations noted for review: main-thread viewer instead of worker shell"*)
and cleared by the r1 judge. The browser never requests it, which the executed run confirms:
`bridge_error: []`, `data_replay_error: null`, `smoke-stderr.txt` 0 bytes.

### 8(b″) The viewer shell's error markers / bridge

```bash
grep -n 'coworld-replay\|tell(' static_replay.js
```
```
10:// the wasm module instead of the binary one, and bullwhip's `coworld-replay`
25:  function tell(type, message) {
27:    var envelope = { src: "coworld-replay", type: type };
31:  tell("loading");
61:    tell("error", message);
165:          tell("ready");
```

The `coworld-replay` postMessage bridge is present in the **served** JS, including
`tell("ready")` — and, unlike cogame-lantern, it actually fired: the executed run's
`console_tail` is `["[bridge] loading","[bridge] ready"]`.

### 8(c) The replay JSON the viewer was asked to draw

```bash
jq -r '.events[]|[.t,(.seat//.c//.colony//"-"),.type,((.say//.victim//.reason//.block//"")|tostring)]|@tsv' /tmp/ep3.replay | head -30
```
```
0	-	match_start	
0	-	turn_start	
0	0	doctrine	Spreading out to find food
0	1	doctrine	Hunt their roads, not food
0	2	doctrine	
0	3	doctrine	
0	-	source_spawn	
48	2	harvest	
48	3	harvest	
48	0	harvest	
59	0	deliver	
62	3	deliver	
64	3	deliver	
72	0	deliver	
96	0	harvest	
120	2	harvest	
144	0	harvest	
144	0	harvest	
145	2	deliver	
168	3	harvest	
169	3	deliver	
178	0	deliver	
192	3	harvest	
208	3	deliver	
216	2	harvest	
240	-	turn_start	
240	0	doctrine	Building road to nearby cache
240	1	doctrine	Intercept Lime's roads
240	2	doctrine	
240	3	doctrine	
```

Middle (ticks 2400–2600):
```
2400	-	turn_start	
2400	0	doctrine	Road holds. Feed it.
2400	1	doctrine	Paint centre, raid Teal roads
2400	2	doctrine	
2400	3	doctrine	
2400	1	harvest	
2424	2	harvest	
2448	2	harvest	
2488	1	deliver	
2491	2	deliver	
2504	2	deliver	
2520	2	harvest	
2544	3	harvest	
2568	2	harvest	
2592	2	harvest	
2592	0	harvest	
2592	2	harvest	
```

Late (`tail -18`):
```
4500	-	source_gone	
4500	-	source_gone	
4500	-	source_gone	
4512	-	trail_war	[0,4]
4512	2	harvest	
4536	2	harvest	
4560	-	turn_start	
4560	0	doctrine	Road holds. Stay locked.
4560	1	doctrine	Raid Teal south cluster
4560	2	doctrine	
4560	3	doctrine	
4560	-	trail_war	[0,4]
4608	-	trail_war	[0,4]
4631	1	deliver	
4656	-	trail_war	[0,4]
4704	-	trail_war	[0,4]
4752	-	trail_war	[0,4]
4800	-	end	complete
```
```bash
jq -c '.keyframes[0], (.keyframes[-1]|{t,d,del,car})' /tmp/ep3.replay   # abridged to the header fields
jq -r '"keyframes: \(.keyframes|length)  tick_count: \(.tick_count)  ants_b64 len: \(.ants_b64|length)"' /tmp/ep3.replay
```
```
{"t":0,"d":1448417106,"del":[0,0,0,0],"car":[0,0,0,0]}
{"t":4776,"d":4075722135,"del":[25,77,82,27],"car":[16,18,14,23]}
keyframes: 200  tick_count: 4800  ants_b64 len: 76800
```
```bash
jq -r '.results' /tmp/ep3.replay   # key fields
```
```json
{"scores":[0.11848341232227488,0.36492890995260663,0.3886255924170616,0.12796208530805686],
 "delivered":[25,77,82,27],"total_delivered":211,"winner":2,
 "reason":"complete","end_rule":"full_time","final_tick":4800,"seed":1139974405}
```

### 8 — the spectator-judgment paragraph

**It is legible, and it shows the game.** The screenshot
(`runs/2026-08-23-hive/viewer-check/viewer-smoke.png`, 424 962 bytes, taken at the 100 % scrub
position) is a finished broadcast, not a placeholder: a four-plate scorebug across the top reads
`25 FOOD daveey / Magenta`, `82 FOOD Baseline / Teal`, `77 FOOD daveey-1 / Amber`,
`27 FOOD Baseline (2) / Lime` — real player names next to colony aliases and colour chips, with
`FINAL · GAME OVER` centred between them; the endcard says **"Teal wins — 82 of 211 (38.9 %)"**
over the caption *"MOST FOOD CARRIED HOME. SCORE IS YOUR SHARE OF ALL FOOD RETURNED."* and the
line `complete / full_time · 4800 ticks · seed 1139974405`; below it, four per-colony cards give
`25 RETURNED · 11.8 % · RAIDS 0`, `77 RETURNED · 36.5 % · RAIDS 10`, `82 RETURNED · 38.9 % ·
RAIDS 1`, `27 RETURNED · 12.8 % · RAIDS 2`. Every one of those numbers reconciles **exactly**
with the replay JSON pasted above (`delivered: [25,77,82,27]`, `total_delivered: 211`,
`winner: 2`, `seed 1139974405`) and with the leaderboard and participant scores in checks 2–3 —
so the picture is drawing this episode, not a cached or generic one. The chrome behind the
endcard is alive too: `CACHES 12`, a nest-counter strip (`Magenta 25 · Amber 77 · Teal 82 ·
Lime 27`), doctrine chips reading `sc 15 · tr 78 · po 12` and `sc 70 · tr 25 · po 45`, the full
transport row (restart / back / pause / +5 s / step / loop / fast-forward / spoilers), speed
chips with **4×** selected as the design specifies, and a `FOOD RETURNED` scrub bar carrying four
separate delivery curves plus tick marks — the dense yellow run of marks in the last quarter is
the `trail_war` burst at ticks 4512–4752 that the event tail shows. The board itself is dimmed
under the endcard overlay but is not blank: the painted meadow floor and faint pheromone-glow
rings are visible through it. Motion is proved separately from the picture, by the three
differing clock readouts (`3:19 TURN 0/20` → `1:37 TURN 10/20` → `FINAL GAME OVER`): the viewer
seeks and advances, it does not render one frame and stall. The one weakness worth naming for a
future phase-30 review is `feed_lines: 0` — the `#killfeed` doctrine feed had no lines at the
sampled instants, so the LLM's per-turn reasoning (which the replay carries in full: 39 distinct
`note` strings, quoted in check 4) is not on screen in this frame; the `say` lines and doctrine
chips carry some of that load, but the feed is the intended place for it. That is a legibility
nit, not a failure of the check: the viewer loads, advances, and says who is winning and by how
much.

**Status: TRUE** — `loaded: true` (both `data-replay-loaded` and the bridge's `ready`), three
differing clock readouts, no failure, empty stderr, and a screenshot whose numbers reconcile with
the replay bytes.

---

## Notes for the coordinator

- **API shapes observed this run** (they differ from phase 50's): `GET /rounds?league_id=…`
  returned an **object** `{entries, limit, offset, total_count}`, not the bare array phase 50 saw
  on `/leagues`. `GET /episode-requests?round_id=…` returned `{entries, next_cursor}`.
  `GET /divisions/$D/leaderboard` returned a **bare array**. All list reads used
  `(if type=="array" then . else .entries end)`.
- **No writes were made by this verifier.** No league, division, round, policy or filler was
  created, triggered, paused or modified; round 3 arrived on the ladder's own 15-minute cadence
  and no `trigger-round` was issued. The only non-read calls were
  `POST /coworlds/replays/session` (the page's own read-only viewer-URL call, required by check 6),
  the `viewer-check.yml` dispatches (check 8's instrument), and the heartbeat writes to `log.md`
  and the Asana `heartbeat_at` custom field.
- **Files written locally** (the coordinator commits; `git push` does not work in this sandbox):
  `runs/2026-08-23-hive/VERIFY.md`, `runs/2026-08-23-hive/viewer-check/{viewer-smoke.json,
  viewer-smoke.png,smoke-stdout.txt,smoke-stderr.txt}`, and heartbeat/poll lines appended to
  `runs/2026-08-23-hive/log.md`.
- **No secrets printed.** Header names only. The replay S3 URLs are plain, unsigned public
  objects with no query string, so nothing needed truncation at `?`.
