# VERIFY — rware-warehouse   (2026-08-27T15:25Z)

Verdict: **all-true** (8/8 TRUE)

Run: `2026-08-27-rware-warehouse` · slug `rware-warehouse` · coworld `cow_66c038fc-7147-4993-bdf9-4a646358ef35` v0.1.0
League `L = league_05193716-123a-4941-a7c7-16a9643ebe37` · Division `D = div_042d04a9-e695-4c7b-a0b9-8f2bb2ae7765`

Every fetch below was made **this run** (verifier session, 2026-08-27 14:57Z–15:25Z), except the two
documented exceptions: check 7 (reads the committed `runs/<run>/release-result.json` artifact of
this run's phase-40 release) and check 8 (reads the artifact of the `viewer-check.yml` run this
verifier dispatched at 15:22:11Z).

Common header set (values never printed):

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_05193716-123a-4941-a7c7-16a9643ebe37
D=div_042d04a9-e695-4c7b-a0b9-8f2bb2ae7765
COW=cow_66c038fc-7147-4993-bdf9-4a646358ef35
```

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}"     # HTTP 200, 2026-08-27T15:20:08Z
jq -r 'type'                                                    # -> "object"  (this endpoint DOES wrap in .entries)
jq -r '(if type=="array" then . else .entries end)|[.[]|select(.status=="completed")]|length'
```

```
2
```

```bash
jq -c '(if type=="array" then . else .entries end)|[.[]|{id,round_number,status,error,completed_at}]'
```

```json
[
    {
        "id": "round_ce4a2085-a680-4c42-ad64-c28df3493ac5",
        "round_number": 3,
        "status": "completed",
        "error": null,
        "completed_at": "2026-08-27T15:15:06.856788Z"
    },
    {
        "id": "round_e8ab3923-5ec5-4b8b-88e9-c8d3af9971bb",
        "round_number": 2,
        "status": "completed",
        "error": null,
        "completed_at": "2026-08-27T15:00:05.668588Z"
    },
    {
        "id": "round_41868a9c-52c2-406f-b173-3f5e0b123310",
        "round_number": 1,
        "status": "failed",
        "error": "Temporal RoundWorkflow failed before settling the round.",
        "completed_at": "2026-08-27T14:54:03.018813Z"
    }
]
```

Round 1's `error` verbatim (it does **not** count toward the two):

```
Temporal RoundWorkflow failed before settling the round.
```

Fillers are registered on the league right now (fetched fresh; this read needs `ELEV` even
though it is a read):

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"   # HTTP 200
```

```json
{
  "filler_policy_versions": [
    {"policy_version_id": "b2b4ff06-d45a-4ef1-8d99-36dc810c44db", "policy_name": "rware-warehouse-shuttle",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey", "display_name": null},
    {"policy_version_id": "a7a6f802-c46a-4706-b126-3b81c45bf81f", "policy_name": "rware-warehouse-courteous",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey", "display_name": null}
  ]
}
```

Both completed rounds seated only the two champions as entrants:

```bash
jq -r '(if type=="array" then . else .entries end)|.[]|{round_number,status,entrant_attributions:.round_config.entrant_attributions}'
```

```json
{"round_number": 3, "status": "completed", "entrant_attributions": [
  {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
   "policy_version_id": "f7aae7bc-85cc-447b-b617-bdc4274cf5d3", "league_policy_membership_id": "lpm_73318a3c-4cbb-453e-b4e6-de0a83152e1f"},
  {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
   "policy_version_id": "0bbe6faa-7f6c-415e-9b8f-8aeb6a930371", "league_policy_membership_id": "lpm_a2fe73af-6a62-4ee0-b328-896829f97913"}]}
{"round_number": 2, "status": "completed", "entrant_attributions": [ …same two… ]}
{"round_number": 1, "status": "failed",    "entrant_attributions": [ …same two… ]}
```

Status: **TRUE** — rounds **2** and **3** completed (at 2026-08-27T15:00:05.668588Z and
2026-08-27T15:15:06.856788Z), both numbered **after** round 1, the round in which the fillers
were registered (`log.md` 14:55:40Z `50 filler-policies POST 200: shuttle+courteous UUIDs
registered, neither champion`). Round 1 (`failed`) is excluded and its Temporal error is quoted
above.

*Note recorded, not inferred over:* the `/rounds` rows carry `created_at` 14:54:02Z (r1) and
14:54:18Z (r2), which are earlier than log.md's 14:55:40Z stamp for the filler POST — phase 50's
log lines are not strictly monotonic, so I did not rely on either timestamp. The decisive fetched
evidence that fillers were in effect for **both** completed rounds is check 3's participant list
(round 3: positions 2 and 3 = `rware-warehouse-shuttle`, `is_filler: true`) and round 2's
equivalent (positions 2 and 3 = `rware-warehouse-courteous`, `is_filler: true`, fetched at
15:03Z), plus the replay's own `results.names = ["daveey","daveey-1","Baseline","Baseline (2)"]`
in check 4.

Round-2 participant evidence (fetched 2026-08-27T15:04Z, `GET $BASE/episode-requests/ereq_4794c322-95ca-4665-aac8-dac35b1c3454`), trimmed:

```json
{"position": 2, "policy_name": "rware-warehouse-courteous", "player_name": "daveey", "is_filler": true},
{"position": 3, "policy_name": "rware-warehouse-courteous", "player_name": "daveey", "is_filler": true}
```

---

## 2. Both champions ranked; fillers absent/Baseline — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}"    # HTTP 200, 2026-08-27T15:20Z
jq -r 'type'                                              # -> "array"  (bare list, as the playbook says)
jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```

```
1	daveey-1	rware-warehouse-router:v1	1014.5304984710245	2	1.0
2	daveey	rware-warehouse-picker:v1	985.4695015289755	2	0.0
```

Full body:

```json
[{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":1014.5304984710245,"score_label":"MMR","score_value_type":"integer","rounds_played":2,"episode_wins":1.0,"episodes_played":null,"win_rate":0.5,"policy_label":"rware-warehouse-router:v1","recent_rounds":null},
 {"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":985.4695015289755,"score_label":"MMR","score_value_type":"integer","rounds_played":2,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"rware-warehouse-picker:v1","recent_rounds":null}]
```

Status: **TRUE** — `daveey` (`rware-warehouse-picker:v1`) and `daveey-1`
(`rware-warehouse-router:v1`) are both present, each with `rounds_played = 2` (≥ 1). The two
filler policies (`rware-warehouse-shuttle`, `rware-warehouse-courteous`) are **absent** from the
board entirely — the leaderboard has exactly two rows.

---

## 3. Latest completed round's episode request completed with a replay — **TRUE**

Latest completed round = `round_ce4a2085-a680-4c42-ad64-c28df3493ac5` (round_number 3, from check 1).

The prompt's flat `GET $BASE/episode-requests?round_id=…` is dead (405, `playbooks/observatory-api.md` §9);
I used the nested route the playbook prescribes:

```bash
curl -sS "$BASE/rounds/round_ce4a2085-a680-4c42-ad64-c28df3493ac5/episode-requests" "${AUTH[@]}"   # HTTP 200
jq -c 'if type=="array" then . else .entries end | [.[]|{id,status}]'
```

```json
[{"id":"ereq_9cb0729b-3c11-4a5c-8680-b61d7848572b","status":"completed"}]
```

```bash
curl -sS "$BASE/episode-requests/ereq_9cb0729b-3c11-4a5c-8680-b61d7848572b" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'      # HTTP 200
```

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/bc4a674a-44e7-424e-b23c-4ee9e491345d.replay",
  "participants": [
    {"position": 0, "kind": "policy", "policy_version_id": "f7aae7bc-85cc-447b-b617-bdc4274cf5d3",
     "policy_id": "5f5fc31f-ffac-4aeb-9278-bbcea8146369", "policy_name": "rware-warehouse-picker", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey", "is_filler": false, "is_seed": false},
    {"position": 1, "kind": "policy", "policy_version_id": "0bbe6faa-7f6c-415e-9b8f-8aeb6a930371",
     "policy_id": "1963ae8a-cc43-488c-9a06-c2804e69e50b", "policy_name": "rware-warehouse-router", "version": 1,
     "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1", "is_filler": false, "is_seed": false},
    {"position": 2, "kind": "policy", "policy_version_id": "b2b4ff06-d45a-4ef1-8d99-36dc810c44db",
     "policy_id": "6039c3c6-e93b-4caf-a3c5-1dbe69d9c162", "policy_name": "rware-warehouse-shuttle", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey", "is_filler": true, "is_seed": false},
    {"position": 3, "kind": "policy", "policy_version_id": "b2b4ff06-d45a-4ef1-8d99-36dc810c44db",
     "policy_id": "6039c3c6-e93b-4caf-a3c5-1dbe69d9c162", "policy_name": "rware-warehouse-shuttle", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey", "is_filler": true, "is_seed": false}
  ],
  "participant_scores": [
    {"position": 0, "score": 501.0},
    {"position": 1, "score": 501.0},
    {"position": 2, "score": 501.0},
    {"position": 3, "score": 502.0}
  ]
}
```

Status: **TRUE** — `status: "completed"`, non-null `replay_url`
(`https://softmax-public.s3.amazonaws.com/replays/bc4a674a-44e7-424e-b23c-4ee9e491345d.replay`),
participants name **daveey** (seat 0, `rware-warehouse-picker:v1`) and **daveey-1** (seat 1,
`rware-warehouse-router:v1`); seats 2 and 3 are the filler `rware-warehouse-shuttle` with
`is_filler: true`, and the replay renames them `Baseline` / `Baseline (2)` (check 4).

---

## 4. Replay bytes are valid and show the game — **TRUE** (via the design's declared substitute)

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/bc4a674a-44e7-424e-b23c-4ee9e491345d.replay" -o /tmp/ep.replay
```

```
HTTP 200 bytes=154921
```

The prompt's `jq -e . /tmp/ep.replay` cannot apply directly: this game's replay is a **binary
`COWLDRWH` container**, not raw JSON. First 8 bytes, fetched:

```python
>>> open('/tmp/ep.replay','rb').read(8)
b'COWLDRWH'
```

```
raw bytes are NOT JSON (binary COWLDRWH container) — using declared substitute
```

The substitute is declared in the design note, `runs/2026-08-27-rware-warehouse/design.md` §Server,
line 923: *"**The phase-60 substitute for SPEC §Definition of done check 4:**"* — download the
replay, run the repo's stdlib-only `tools/replay_summary.py` over it, and apply the strict parser
plus the field requirements to its output. Executed from a fresh `git pull` of the coworld repo at
`/workspace/cogame-rware-warehouse` (`git rev-parse --short HEAD` → `d5b5686`, `Already up to date.`):

```bash
python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json     # 31197 bytes
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
```

```
strict UTF-8 JSON: ok
```

```bash
jq -r '.protocol, .results.reason, .results.teamDelivered' /tmp/ep.json
```

```
rware-warehouse/v1
complete
5
```

```bash
jq -r '([.orders[]|select(.source=="llm")]|length), .fallbacks, (.radio|length), (.orders|length)' /tmp/ep.json
```

```
50      # LLM-sourced orders
0       # fallback records
50      # radio lines
100     # total orders (25 turns × 4 seats)
```

```bash
jq -c '.results' /tmp/ep.json
```

```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],"aliases":["Alpha","Bravo","Charlie","Delta"],"scores":[501,501,501,502],"win":[false,false,false,false],"winner":null,"reason":"complete","teamDelivered":5,"parDeliveries":8,"delivered":[1,1,1,2],"stowed":[0,0,0,1],"blockedMoves":[151,154,457,410],"jams":12,"jamTicks":322,"longestJamTicks":141,"finalTick":500,"turnsPlayed":25,"seed":1239953709,"policyKinds":["llm","llm","scripted","scripted"],"crossPlay":true,"llmTurns":[25,25,0,0],"fallbackTurns":[0,0,0,0],"ordersRejected":[0,0,0,0],"deadSeats":[false,false,false,false],"stopDetail":""}
```

Champion seats decided for themselves, every turn, with real verbs:

```bash
jq -r '.orders|map(select(.source=="llm"))|group_by(.slot)|.[]|[(.[0].slot|tostring),([.[].verb]|unique|join(","))]|@tsv' /tmp/ep.json
```

```
0	deliver,fetch,yield
1	deliver,fetch,hold,stow,yield
```

```bash
jq -r '.orders|group_by(.source)|.[]|[.[0].source,length,([.[].verb]|unique|join(","))]|@tsv' /tmp/ep.json
```

```
llm	50	deliver,fetch,hold,stow,yield
scripted	50	deliver,fetch,stow
```

```bash
jq -r '([.radio[]|select((.text//"")|length>0)]|length), (.radio|length), ([.radio[]|.alias]|unique|@json)' /tmp/ep.json
```

```
50
50
["Alpha","Bravo"]
```

```bash
jq -c '.orders[0], .radio[0], .radio[1], .directives[0]' /tmp/ep.json
```

```json
{"tick":196,"turn":1,"slot":0,"verb":"fetch","shelf":"S05","source":"llm"}
{"turn":1,"alias":"Alpha","text":"taking S05, returning down column 1"}
{"turn":1,"alias":"Bravo","text":"Bravo LEFT-SIDE, taking S05 to W1. Lane discipline: small-y first."}
{"turn":1,"slot":0,"alias":"Alpha","source":"llm","latency_ms":5084,"verb":"fetch","arg":"S05","say":"taking S05, returning down column 1"}
```

```bash
jq -r '[.directives[]|select(.source=="llm")|.latency_ms]|{n:length,min:min,max:max,mean:(add/length)}|@json' /tmp/ep.json
```

```json
{"n":50,"min":3532,"max":6112,"mean":4466.56}
```

Status: **TRUE** — strict-parser-valid UTF-8 JSON; `protocol == "rware-warehouse/v1"` matches the
manifest; `results.reason == "complete"` (not even the declared-acceptable `deadline`);
`results.teamDelivered = 5 > 0`; both champion seats produced **25/25 LLM orders each**
(`llmTurns: [25,25,0,0]`) using five distinct real verbs, with 50/50 non-empty radio lines and
**zero** fallbacks (`fallbacks: 0`, `fallbackTurns: [0,0,0,0]`, `ordersRejected: [0,0,0,0]`) —
fallbacks are not merely a small minority, they are absent.

*Gameplay observation (not a gate item):* the round-3 episode was heavily congested —
`jams: 12`, `jamTicks: 322` of 500, `longestJamTicks: 141`, `blockedMoves: [151,154,457,410]` —
and the fleet delivered 5 against `parDeliveries: 8`, so `win: [false,false,false,false]`. Round 2
by contrast delivered 12 of par 8 with 2 jams. The game is producing genuinely different episodes,
not a fixed script.

---

## 5. Hosted game log is clean — **TRUE (CLEAN)**

The logs body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it
is decoded (`ast.literal_eval` per repr) before grepping, per the playbook §10.

```bash
curl -sS "$BASE/episode-requests/ereq_9cb0729b-3c11-4a5c-8680-b61d7848572b/artifacts/logs" \
     "${AUTH[@]}" "${ELEV[@]}" -o logs3.raw       # HTTP 200 bytes=104490
python3 decode_logs.py logs3.raw > logs3.txt      # 104257 bytes decoded
grep -n '===== container' logs3.txt
```

```
1:===== container: coworld-init-config =====
4:===== container: bedrock-sidecar =====
210:===== container: game =====
231:===== container: worker =====
```

```bash
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs3.txt || echo CLEAN
```

```
CLEAN
```

```bash
grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs3.txt
```

```
0
```

Counts for the record, as the brief asked: **0** `falling back`, **0** `LLM provider is
unavailable`, **0** `cut off at max_tokens`, **0** `rejected`. The single substring `fallback`
anywhere in the decoded log is inside the results JSON's own `"fallbackTurns":[0,0,0,0]` field
(line 226) — not a log event. No platform-wide-capacity procedure was needed; no 429s and no
Bedrock unavailability appear.

The `game` container tail, showing the episode ran end to end (pasted, trimmed to the tail):

```
rware llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
rware-warehouse listening on 0.0.0.0:8080 board=10x11 seats=4 shelves=32 requests=4
player connected: slot 3
player connected: slot 2
player connected: slot 0
seat 0 registered: kind=llm baseline=courteous
seat 3 registered: kind=scripted baseline=shuttle
seat 2 registered: kind=scripted baseline=shuttle
player connected: slot 1
seat 1 registered: kind=llm baseline=courteous
shift starts: 500 ticks, 25 command turns
Dropped message to disconnected client
shift over: tickCap, delivered 5 of par 8
Replay written: /coworld/replay (154921 bytes)
Events written: /coworld/events.json (1332 events)
results: {"names":["daveey","daveey-1","Baseline","Baseline (2)"],…,"reason":"complete",…}
labels: 27 in the manifest vocabulary
```

Status: **TRUE** — CLEAN on all four patterns.

*Observation for the coordinator (not a gate pattern):* one line reads
`Dropped message to disconnected client`, emitted after `shift over`. It is not in the gate's
grep set, the episode still settled `reason: "complete"` with all four seats alive
(`deadSeats: [false,false,false,false]`), and no seat lost a turn (`llmTurns: [25,25,0,0]` =
`turnsPlayed: 25`). Noting it so it is on the record rather than silently dropped.

---

## 6. The public page uses the static replay path — **TRUE**

**Source used: the `POST $BASE/coworlds/replays/session` route** (playbook §Featured match /
replay route, "Answered (lighthouse run, 2026-08-22)"). Both of the prompt's two sources were
tried first and both are non-evidence on this platform build; all three are recorded below.

**(a) Raw-HTML iframe grep — finds nothing (page is client-rendered):**

```bash
curl -sS "https://softmax.com/rware-warehouse" -o page3.html   # HTTP 200 bytes=680232, 15:21:53Z
grep -o '<iframe[^>]*src="[^"]*"' page3.html || echo "IFRAME-GREP: no match"
```

```
IFRAME-GREP: no match (page is client-rendered)
```

**(b) Coworld detail API — `replay_viewer` and `featured_match` are null (null platform-wide, per playbook):**

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end|.[]|select(.name=="rware-warehouse")|{id,name,canonical,replay_viewer,featured_match}'
```

```json
{
  "id": "cow_66c038fc-7147-4993-bdf9-4a646358ef35",
  "name": "rware-warehouse",
  "canonical": true,
  "replay_viewer": null,
  "featured_match": null
}
```

**(c) The featured match, server-rendered into the page's SSR payload at `state.playlist[0]`** —
pasted verbatim from `page3.html` (escaping is the page's own; trimmed after `matchup`):

```
\"playlist\":[{\"episodeId\":\"0a01a27a-ae4d-4610-a880-9ca183c0466c\",\"coworldId\":\"cow_66c038fc-7147-4993-bdf9-4a646358ef35\",\"coworldName\":\"rware-warehouse\",\"coworldVersion\":\"0.1.0\",\"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/bc4a674a-44e7-424e-b23c-4ee9e491345d.replay\",\"finishedAt\":\"2026-08-27T15:14:57.956422Z\",\"roundNumber\":3,\"episodeNumber\":1,\"code\":\"rware-warehouse.r3.e1\",\"matchup\":{\"divisionId\":\"div_042d04a9-e695-4c7b-a0b9-8f2bb2ae7765\",\"divisionName\":\"Competition\",\"first\":{\"rank\":1,\"player_id\":\"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d\",\"player_name\":\"daveey-1\",\"score\":1014.5304984710245,\"score_label\":\"MMR\",\"score_value_type\":\"integer\",\"rounds_played\":2,\"episode_wins\":1,\"episodes_played\":null,\"win_rate\":0.5,\"policy_label\":\"rware-warehouse-router:v1\",\"recent_rounds\":null},\"second\":{\"rank\":2,\"player_id\":\"ply_44ae9048-3242-4654-881f-6d9d43347fa3\",\"player_name\":\"daveey\",\"score\":985.4695015289755,\"score_label\":\"MMR\",\"score_value_type\":\"integer\",\"rounds_played\":2,\"episode_wins\":0,\"episodes_played\":null,\"win_rate\":0,\"policy_label\":\"rware-warehouse-picker:v1\",\"recent_rounds\":null}},\"inspectUrl\":\"/observatory/v2?tab=overview\u0026detail=episode-request:ereq_9cb0729b-3c11-4a5c-8680-b61d7848572b\",\"outcome\":null}]
```

(For contrast: the same page fetched at 14:58Z, before any round completed, carried
`\"playlist\":[]` and rendered the copy `No featured match yet` / `Between rounds`. The featured
match appeared only once round 2 settled, and now points at round 3.)

**(d) The iframe `src` — the exact call the page's own JS makes:**

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_66c038fc-7147-4993-bdf9-4a646358ef35",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/bc4a674a-44e7-424e-b23c-4ee9e491345d.replay"}'
```

```
HTTP 200
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_66c038fc-7147-4993-bdf9-4a646358ef35/sha256%3Ae131069cba756f2ca0fb46e89714dafa479e9e51b268cff91659fbb9cd8aaf35/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fbc4a674a-44e7-424e-b23c-4ee9e491345d.replay&v=2","ready":true}
```

Status: **TRUE** —
* A **featured match is present**: `state.playlist[0]`, `rware-warehouse.r3.e1`, `daveey-1` (rank 1)
  vs `daveey` (rank 2).
* The iframe `src` is on the **static** route:
  `…/v2/coworlds/replays/static/cow_66c038fc-7147-4993-bdf9-4a646358ef35/sha256%3Ae131069cba…8aaf35/index.html?replay=<s3 url>` —
  it is **not** a `/client/replay` pod URL.
* `<sha>` decodes to `sha256:e131069cba756f2ca0fb46e89714dafa479e9e51b268cff91659fbb9cd8aaf35`,
  which equals `STATE.coworld.manifest_sha` exactly.
* `"ready": true`, and the path ends `/index.html` — the playbook's two conditions for static
  delivery.

*API-shape deviations observed this run, recorded as the brief asked:* `GET /leagues?limit=200`
returns a **bare array** (`jq -r type` → `array`), and so does `GET /coworlds?limit=200`
(→ `array`), while `GET /rounds?league_id=…` and `GET /rounds/<id>/episode-requests` still wrap in
`.entries` (→ `object`, keys `["entries","limit","offset","total_count"]` and
`["entries","next_cursor"]` respectively). All jq above handles both shapes.

---

## 7. Certification declared the static bundle — **TRUE**

Source: **the committed `runs/2026-08-27-rware-warehouse/release-result.json`** (the artifact
phase 40 downloaded and committed from release run `33083560584`). The fallback re-download was
**not** needed — the file was present.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-27-rware-warehouse/release-result.json
```

```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Surrounding certification transcript from the same file (`.certify.output_tail`, pasted, trimmed
to the transcript body):

```
Certifying dist/coworld_manifest.json against transcript coworld-executable
  [pass] matriculate: manifest conforms to the Coworld schema
  [pass] source-resolves: whether each runnable declares a source_url that resolves to publicly accessible source
  [pass] images-reachable: every declared image is pullable or inspectable
  [pass] fixture-conforms: the certification fixture validates against game.config_schema after runner token injection
  [pass] smoke-episode: the game and certification players run one episode
  [pass] results-conform: episode results validate against results_schema
  [pass] replay-present: a replay artifact was produced
  [pass] replay-loadable: the replay artifact has a declared viewer path
  [pass] players-run: every declared player actually started on the smoke episode (not just declared)
  [pass] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks
Certified dist/coworld_manifest.json
Transcript: coworld-executable (10 steps passed)
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

```bash
jq -c '{ok:.ok, version:.version, certify_ok:.certify.ok, secret_put:.secret_put}' runs/2026-08-27-rware-warehouse/release-result.json
```

```json
{"ok":true,"version":"0.1.0","certify_ok":true,"secret_put":true}
```

Status: **TRUE** — the string contains `Replay liveness: skipped (static replay bundle declared`,
read from the **committed** `runs/2026-08-27-rware-warehouse/release-result.json` (not `/tmp`,
not a re-download).

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

**(a) The dispatch.** The URL is the iframe `src` from check 6, verbatim including `?replay=`:

```bash
DISPATCH_TS=2026-08-27T15:22:11Z
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_66c038fc-7147-4993-bdf9-4a646358ef35/sha256%3Ae131069cba756f2ca0fb46e89714dafa479e9e51b268cff91659fbb9cd8aaf35/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fbc4a674a-44e7-424e-b23c-4ee9e491345d.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
```

Run selected by `createdAt` **after** the dispatch stamp, never "the latest":

```bash
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[]|[.databaseId,.createdAt,.status]|@tsv'
```

```
33087427495	2026-08-27T15:22:13Z	in_progress     <- MINE (createdAt > dispatch 15:22:11Z)
33067338841	2026-08-27T11:25:59Z	completed
33066666879	2026-08-27T11:16:44Z	completed
33063761313	2026-08-27T10:36:18Z	completed
33063093381	2026-08-27T10:27:11Z	completed
33062642745	2026-08-27T10:21:00Z	completed
33042374554	2026-08-27T05:24:05Z	completed
33039031390	2026-08-27T04:18:51Z	completed
33036080393	2026-08-27T03:20:40Z	completed
33027843730	2026-08-27T00:44:34Z	completed
```

```bash
gh run watch 33087427495 -R Metta-AI/coworld-builder --exit-status
```

```
✓ main viewer-check · 33087427495
✓ viewer-check in 1m2s (ID 98570825381)
  ✓ Load the viewer
  ✓ Summary
  ✓ Upload the evidence
  ✓ Fail if the viewer did not load
watch exit=0
```

```bash
gh run download 33087427495 -R Metta-AI/coworld-builder -n viewer-check \
   -D runs/2026-08-27-rware-warehouse/viewer-check
```

```
-rw-r--r-- 1 root root      0 smoke-stderr.txt
-rw-r--r-- 1 root root    763 smoke-stdout.txt
-rw-r--r-- 1 root root   1559 viewer-smoke.json
-rw-r--r-- 1 root root 248717 viewer-smoke.png
```

(`runs/2026-08-27-rware-warehouse/viewer-check/` is written, not committed — the coordinator commits.)

**(b) The readouts, pasted verbatim.**

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-27-rware-warehouse/viewer-check/viewer-smoke.json
```

```json
{"loaded":true,"ms":2373,"clock":"DELIVERED 0 / 8 PAR · TICK 0/500 · TURN 1/25 · JAM 0 · BLOCKED 0","scorebug":"DAVEEY ALPHA 0 DAVEEY-1 BRAVO 0 DELIVERED 0 / 8 PAR · TICK 0/500 · TURN 1/25 · JAM 0 · BLOCKED 0 BASELINE CHARLIE 0 BASELINE (2) DELTA 0","feed_lines":0}
```

```bash
jq -c '.signals' runs/2026-08-27-rware-warehouse/viewer-check/viewer-smoke.json
```

```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/2026-08-27-rware-warehouse/viewer-check/viewer-smoke.json
```

```
no failure
```

**The three clock readouts:**

| Scrub position | `clock` readout |
|---|---|
| 0 %   | `DELIVERED 0 / 8 PAR · TICK 0/500 · TURN 1/25 · JAM 0 · BLOCKED 0` |
| 50 %  | `DELIVERED 5 / 8 PAR · TICK 288/500 · TURN 15/25 · JAM 9 · BLOCKED 700` |
| 100 % | `DELIVERED 5 / 8 PAR · TICK 500/500 · TURN 25/25 · JAM 12 · BLOCKED 1172` |

All three differ, in five independent fields each (delivered / tick / turn / jam / blocked), and
they advance monotonically.

Other fields from the same file:

```json
"status": "OPEN", "loading_text": null, "bundle": null, "replay": null, "console_tail": [],
"canvas_text": {"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
```

`canvas_text.total = 0` is the known F10 condition from the phase-30 review: this coworld renders
the board on an **OffscreenCanvas in a worker**, which the smoke harness's `CanvasRenderingContext2D`
hook cannot see. It is "not seen", not "zero text drawn" — the screenshot below plainly contains
drawn board text (`S13`, `S17`, `S29`, `W1`, `W2`), which is the direct refutation.
`bridge_ready: false` with `data_replay_loaded: "true"` is the shell signalling readiness via the
`data-replay-loaded` attribute rather than the `coworld-replay` bridge; the workflow's own gate
accepts either and the run went green.

**(c) The replay JSON the viewer was asked to draw** — ordered excerpts from `/tmp/ep.json`
(check 4), early / middle / late, for reconciliation:

```bash
jq -r '.orders[]|select(.turn<=3)|[.turn,.tick,.slot,.source,.verb,(.shelf//.station//.cell//"")]|@tsv' /tmp/ep.json
```

```
1	196	0	llm	fetch	S05
1	196	1	llm	fetch	S05
1	196	2	scripted	fetch	S18
1	196	3	scripted	fetch	S16
2	216	0	llm	fetch	S21
2	216	1	llm	deliver	W1
2	216	2	scripted	deliver	W1
2	216	3	scripted	deliver	W2
3	236	0	llm	deliver	W1
3	236	1	llm	deliver	W1
3	236	2	scripted	stow	
3	236	3	scripted	stow	
```

```bash
jq -r '.orders[]|select(.turn>=12 and .turn<=14)|[.turn,.tick,.slot,.source,.verb,(.shelf//.station//.cell//"")]|@tsv' /tmp/ep.json
```

```
12	416	0	llm	deliver	W1
12	416	1	llm	hold	
12	416	2	scripted	stow	
12	416	3	scripted	deliver	W1
13	436	0	llm	yield	
13	436	1	llm	hold	
13	436	2	scripted	stow	
13	436	3	scripted	deliver	W1
14	456	0	llm	deliver	W1
14	456	1	llm	deliver	W1
14	456	2	scripted	stow	
14	456	3	scripted	deliver	W1
```

```bash
jq -r '.orders[]|select(.turn>=23)|[.turn,.tick,.slot,.source,.verb,(.shelf//.station//.cell//"")]|@tsv' /tmp/ep.json
```

```
23	636	0	llm	deliver	W1
23	636	1	llm	hold	
23	636	2	scripted	stow	
23	636	3	scripted	deliver	W1
24	656	0	llm	deliver	W1
24	656	1	llm	hold	
24	656	2	scripted	stow	
24	656	3	scripted	deliver	W1
25	676	0	llm	deliver	W1
25	676	1	llm	deliver	W1
25	676	2	scripted	stow	
25	676	3	scripted	deliver	W1
```

```bash
jq -r '.radio[]|select(.turn<=2 or (.turn>=13 and .turn<=14) or .turn>=24)|[.turn,.alias,.text]|@tsv' /tmp/ep.json
```

```
1	Alpha	taking S05, returning down column 1
1	Bravo	Bravo LEFT-SIDE, taking S05 to W1. Lane discipline: small-y first.
2	Alpha	taking S21, returning down column 1
2	Bravo	Bravo LEFT-SIDE, delivering S05 to W1, stowing on left side
13	Alpha	yielding, come through
13	Bravo	Bravo holding at [2,9]; Alpha has priority to move. S05 ready for W1 after jam clears.
14	Alpha	resuming delivery W1 after yield
14	Bravo	Bravo RIGHT-SIDE committed to W2, but left side needs help - delivering S05→W1 then fetching S09 (y=3)
24	Alpha	Delivering S21 to W1, then stowing to clear queue lane
24	Bravo	Bravo holding left-side lane. Charlie-Delta jam resolving; I deliver S05→W1 next, then fetch S29.
25	Alpha	delivering S21 at W1, then stow to clear lane
25	Bravo	Bravo delivering S05 to W1, then fetching S29
```

```bash
jq -r '.results' /tmp/ep.json    # (full object pasted in check 4)
```

**Status: TRUE** — `loaded: true` (first frame at **2373 ms**) **and** the three clock readouts
differ and advance.

### Spectator-judgment paragraph

`viewer-smoke.png` (248,717 bytes, downloaded from run 33087427495's artifact — this is a
description of the picture CI actually took, at the 100 % scrub position where the harness left
the transport) shows a legible, finished broadcast. Along the top is the scorebug strip: `ALPHA`
with a red dot and `BRAVO` with a blue dot on the left, each with its delivery count (`ALPHA 1`,
`BRAVO 1`), the centre clock reading **`DELIVERED 5`** over `/ 8 PAR · TICK 500/500 · TURN 25/25 ·
JAM 12 · BLOCKED 1172`, and `CHARLIE` (1) and `DELTA` (2) mirrored on the right in green and
yellow — four seats, two real player names and two baselines, exactly the four the episode
request listed. Under it a jam banner reads `JAM — BRAVO · CHARLIE · DELTA, 1 TICKS`. The board is
visible behind a dimmed endcard: a dark 10×11 warehouse grid with shelf blocks labelled `S13`,
`S17`, `S29`, the two workstations drawn as large `W1` and `W2` pads at the bottom, a request-board
strip of shelf chips (`S13 S09 S17 S29`) top-left, and four coloured robot discs clustered in the
bottom-left approach lane — visibly bunched, which is what 12 jams and 1,172 blocked moves look
like. The endcard itself says **`5 SHELVES DELIVERED — PAR 8 MISSED`**, `TEAM SCORE 500`,
`12 jams, 322 ticks lost, longest 141 · complete`, and a `THE FLEET` table with per-robot
`DELIVERED / STOWED / BLOCKED / JAMS` rows: Alpha 1/0/151/12, Bravo 1/0/154/12, Charlie 1/0/457/12,
Delta 2/1/410/12, footed by `SHELVES DELIVERED 5`. **Every one of those numbers matches the replay
JSON exactly** — `delivered:[1,1,1,2]`, `stowed:[0,0,0,1]`, `blockedMoves:[151,154,457,410]` (sum
1172), `jams:12`, `jamTicks:322`, `longestJamTicks:141`, `reason:"complete"`, `teamDelivered:5`,
scores 501/501/501/502 = 500 + delivered. The picture and the record agree; nothing is invented and
nothing is missing. It advances, too: the 50 % readout (`TICK 288/500 · TURN 15/25 · JAM 9 ·
BLOCKED 700`) sits between the two ends, and the mid-episode replay orders it corresponds to are
the congestion story the endcard reports — turn 13 has Alpha `yield` and Bravo `hold` with the
radio lines "yielding, come through" and "Bravo holding at [2,9]; Alpha has priority to move." The
picture is neither empty nor frozen nor unreadable.

**Does it look like the starter's chrome?** Yes — this is unmistakably the paintbot/raid/hive
family shell, not a rewrite sharing ids. The bottom transport strip carries the same button row
(restart ⟲, step-back ◀, pause ⏸, `+5s`, play ▶, loop ↻, fast-forward ⏩), the `spoilers` toggle
(lit amber), the `DRAW  530 / 530` counter, and the `1× 2× 3× 4× 8× 16×` speed bank on the right
with `1×` selected; below it is the starter's scrubber with the **momentum graph** — a green
filled area curve captioned `DELIVERIES` — overlaid with red and green event tick marks, the white
playhead parked near the right end and the amber end-of-episode marker at the far right. The
endcard is the starter's centred card with headline, boxed team score, subtitle line and a
per-participant table, dimming the board behind it (and dismissible by seek, per the design). The
colour language (dark ground, per-seat accent dots, amber accents) is the same. Two legibility
notes for the coordinator, neither a gate failure: (i) `feed_lines: 0` in the JSON is the harness
reading the feed at load time (tick 0), when the broadcast feed is legitimately empty; the
rendered frame at 100 % does carry feed text bottom-right — legible in the png as
`BRAVO → deliver W1`, an italic radio quote `"…SIDE, delivering S05 to W1, then stowing and
fetching S29"`, `CHARLIE → stow 16`, `DELTA → deliver W1`, which match the turn-25 orders and
Bravo's turn-25 radio line above — but I have no counted DOM readout of it, so I record the
measured zero and do not claim otherwise; (ii) the board and the
fleet-table type are very small at 1280×800 (18 px/cell letterboxed, as designed), so the shelf
ids and the per-robot table are readable but tight — worth a look if phase 30 revisits legibility.

---

## Appendix — poll log (checks 1/3, every 5 min, bound 75 min from 14:57Z)

```
2026-08-27T14:57:15Z  bound opens (verifier start); STATE says round 2 pending
2026-08-27T14:58:26Z poll#1 http=200  rounds 2:pending 1:failed
2026-08-27T15:03:27Z poll#2 http=200  rounds 2:completed 1:failed        (1 of 2)
2026-08-27T15:08:29Z poll#3 http=200  rounds 2:completed 1:failed
2026-08-27T15:13:29Z poll#4 http=200  rounds 3:pending 2:completed 1:failed
2026-08-27T15:18:29Z poll#5 http=200  rounds 3:completed 2:completed 1:failed
2026-08-27T15:18:29Z  DONE completed_after_round1=2  — bound closed at 21 min of 75, unused budget 54 min
```

Other timeline entries this run:

```
2026-08-27T14:57:30Z  check 7 read from committed release-result.json -> TRUE
2026-08-27T14:58:10Z  check 6 first attempt: playlist:[] ("No featured match yet") — deferred, correct at the time
2026-08-27T15:20:08Z  checks 1,2,3 re-fetched fresh against round 3
2026-08-27T15:20:40Z  check 4 replay bc4a674a downloaded (154921 B) and summarised at repo d5b5686
2026-08-27T15:21:10Z  check 5 logs for ereq_9cb0729b decoded and grepped -> CLEAN
2026-08-27T15:21:53Z  check 6 re-fetched: playlist[0] = rware-warehouse.r3.e1; session POST -> static viewer_url, ready:true
2026-08-27T15:22:11Z  check 8 dispatched viewer-check.yml; run 33087427495 (createdAt 15:22:13Z)
2026-08-27T15:23:30Z  check 8 run green in 1m2s; artifact downloaded to runs/<run>/viewer-check/
```

## Appendix — no writes performed

This verifier made only reads, plus two non-mutating exceptions the prompt authorises:
`POST $BASE/coworlds/replays/session` (the read-only viewer-session call the public page's own JS
makes; it touches no league, division, round or policy) and `gh workflow run viewer-check.yml -R
Metta-AI/coworld-builder`. No league, division, round, policy, filler, Discord message, Asana
comment or STATE field was created, modified, paused or triggered. No git commit or push.
