# VERIFY — pommerman   (2026-08-27T21:43Z)

Verdict: **all-true** (8/8)

Second pass. The first pass (20:44Z, coworld 0.1.0 `cow_224b5627…`) returned check 5 **FALSE**
— 11 `falling back` lines in the hosted log, caused by attempt-1 LLM deadlines set below the
observed hosted p90. The coworld was re-released as **0.1.1** (`cow_ab2d905c-54e0-42a9-b4e1-d4e0aaa3cf47`,
manifest `sha256:f143a646…`, release run 33116243915) with `attempt1Ms` 8000→12000,
`retryMs` 3000→5000, `turnBudgetMs` 12000→18000, and the attempt-1 retry notice reworded so it
no longer claims a fallback it did not make. **Every check below was re-fetched fresh at 21:35–21:43Z**;
nothing is carried over from the first pass.

Evidence round: **round 7** = `round_36e8e498-8d55-4628-91a9-b593df5c5d3e` (round_number 7), the
newest **completed** round at fetch time and the first episode to run the 0.1.1 image.
Episode request: `ereq_1274172a-9257-4e94-9454-893f48bb0c97`
(episode `0c442902-761c-4548-832a-7fb09df78a81`).
Replay: `https://softmax-public.s3.amazonaws.com/replays/1dc81bbf-936a-49f4-bb67-bdad75bf6792.replay`.
Round 8 (`round_5d720d81-be96-4bf2-a880-55caf8784e4c`, created 21:40:36Z) was still `pending`
at 21:41:27Z, so round 7 remained the newest completed throughout.

Common preamble for every `curl` below (header **names** only; `$SOFTMAX_TOKEN` is never printed):

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_7b53400d-b780-4024-924a-59bc2818dc8d
D=div_7c2c9172-a9dd-449b-8911-e5d072c11d25
COW=cow_ab2d905c-54e0-42a9-b4e1-d4e0aaa3cf47
```

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '[.entries[]|select(.status=="completed")]|length'
```

```
6
```

The rows themselves (fetched 21:35:01Z; `/rounds` returned the wrapped shape
`{entries,limit,offset,total_count}` this time — the dual-shape jq was applied anyway):

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)|sort_by(.round_number)
          |.[]|[.round_number,.id,.status,.created_at,(.error//"null")]|@tsv'
```

```
1	round_e4540277-b34c-49c0-acab-da5b4307e005	failed	2026-08-27T20:10:01.494362Z	Temporal RoundWorkflow failed before settling the round.
2	round_5020c3b6-8969-4f18-b94b-4c1661ee3006	completed	2026-08-27T20:10:31.210752Z	null
3	round_7868a38d-5b62-4fd2-8fa7-40433bc25f76	completed	2026-08-27T20:25:31.602261Z	null
4	round_a39e9482-1458-4da6-bf94-30f227fd95de	completed	2026-08-27T20:40:34.813056Z	null
5	round_04027971-1383-4789-bb6d-691c1d70afd2	completed	2026-08-27T20:55:35.534120Z	null
6	round_534e7c35-e94a-4beb-8db8-73f5995b8339	completed	2026-08-27T21:10:35.896118Z	null
7	round_36e8e498-8d55-4628-91a9-b593df5c5d3e	completed	2026-08-27T21:25:36.440278Z	null
```

Re-polled at 21:41:27Z, one extra row appeared and is not counted:

```
8	round_5d720d81-be96-4bf2-a880-55caf8784e4c	pending	2026-08-27T21:40:36.812141Z
```

Round 1's `error`, verbatim, as required for a non-counting round:
`Temporal RoundWorkflow failed before settling the round.` — the auto-scheduled round that fired
before any filler existed (`playbooks/observatory-api.md` §6 documents exactly this failure). It is
`failed`, so it does not count.

The fillers were registered at **2026-08-27T20:11:28Z** (`log.md`, phase-50 line
"fillers registered 200: sapper 95cc7892, camper 2dec3894"). They are still registered now:

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}" | jq .
```

```json
{
  "filler_policy_versions": [
    {"policy_version_id": "95cc7892-4e3c-405a-a467-c7480fa55cb9", "policy_id": "425498c8-82a4-4f1a-a761-82f540d329e2",
     "policy_name": "pommerman-sapper", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey", "display_name": null},
    {"policy_version_id": "2dec3894-c52a-458e-915d-fcbd88b1a9df", "policy_id": "d6b1ff29-2670-4ca7-86a9-454edb049a12",
     "policy_name": "pommerman-camper", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey", "display_name": null}
  ]
}
```

Status: **TRUE** — 6 completed rounds. Taking the *latest possible* filler-set time (20:11:28Z),
rounds **3, 4, 5, 6 and 7** (created 20:25:31Z … 21:25:36Z) are unambiguously after it — five
rounds, against a requirement of two. Round 2 (created 20:10:31Z) straddles the phase-50 heartbeat
and is **not** relied on. No `discarded` rounds exist.

---

## 2. Both champions ranked, fillers absent or Baseline — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```

```
1	daveey	pommerman-firestarter:v1	1017.546259199346	6	3.0
2	daveey-1	pommerman-cornerman:v1	982.453740800654	6	2.0
```

Full body (bare list, not `.entries`), fetched 21:35:01Z:

```json
[
  {"rank": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
   "score": 1017.546259199346, "score_label": "MMR", "score_value_type": "integer",
   "rounds_played": 6, "episode_wins": 3.0, "episodes_played": null, "win_rate": 0.5,
   "policy_label": "pommerman-firestarter:v1", "recent_rounds": null},
  {"rank": 2, "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
   "score": 982.453740800654, "score_label": "MMR", "score_value_type": "integer",
   "rounds_played": 6, "episode_wins": 2.0, "episodes_played": null, "win_rate": 0.3333333333333333,
   "policy_label": "pommerman-cornerman:v1", "recent_rounds": null}
]
```

Status: **TRUE** — `daveey` (rank 1, `pommerman-firestarter:v1`, 6 rounds played) and `daveey-1`
(rank 2, `pommerman-cornerman:v1`, 6 rounds played) are both present with `rounds_played ≥ 1`.
The leaderboard has exactly two rows: `pommerman-sapper` and `pommerman-camper` are **absent**, as
required of fillers. (In the episode itself they are renamed `Baseline` / `Baseline (2)` — see
check 3 and check 4.) The league entrants are the **v1** submissions; the 0.1.1 release minted v2
policy versions because the image ref changed, but decisions are taken in the GAME container,
which is canonical 0.1.1 — confirmed independently by the resolved config embedded in the round-7
replay (check 4).

---

## 3. Latest round's episode request completed with a replay — **TRUE**

The flat `?round_id=` route is HTTP 405 (`playbooks/observatory-api.md` line 153); the **nested**
route was used:

```bash
R=round_36e8e498-8d55-4628-91a9-b593df5c5d3e
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)|.[]|{id,status,created_at}'
```

```json
{"id":"ereq_1274172a-9257-4e94-9454-893f48bb0c97","status":"completed","created_at":"2026-08-27T21:25:36.738764Z"}
```

```bash
EREQ=ereq_1274172a-9257-4e94-9454-893f48bb0c97
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/1dc81bbf-936a-49f4-bb67-bdad75bf6792.replay",
  "participants": [
    {"position": 0, "kind": "policy", "policy_version_id": "8f3eef38-df2d-4b89-878e-5dea55713411",
     "policy_id": "eb97ea73-bf63-4fd4-a89c-fb9323a8b17a", "policy_name": "pommerman-firestarter", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "is_filler": false, "is_seed": false},
    {"position": 1, "kind": "policy", "policy_version_id": "a69f2a4f-5347-4e29-a3d5-467507ed6f5a",
     "policy_id": "b9049af8-9763-43a9-80db-7920471b5aca", "policy_name": "pommerman-cornerman", "version": 1,
     "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
     "is_filler": false, "is_seed": false},
    {"position": 2, "kind": "policy", "policy_version_id": "2dec3894-c52a-458e-915d-fcbd88b1a9df",
     "policy_id": "d6b1ff29-2670-4ca7-86a9-454edb049a12", "policy_name": "pommerman-camper", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "is_filler": true, "is_seed": false},
    {"position": 3, "kind": "policy", "policy_version_id": "95cc7892-4e3c-405a-a467-c7480fa55cb9",
     "policy_id": "425498c8-82a4-4f1a-a761-82f540d329e2", "policy_name": "pommerman-sapper", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "is_filler": true, "is_seed": false}
  ],
  "participant_scores": [
    {"position": 0, "score": 105.0},
    {"position": 1, "score": -105.0},
    {"position": 2, "score": 105.0},
    {"position": 3, "score": -105.0}
  ]
}
```

The same request also carries the coworld binding — this is what proves round 7 is a **0.1.1**
episode:

```bash
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{coworld_id,coworld_name,coworld_version,variant_name,episode_id,created_at,completed_at,error,error_type}'
```

```json
{
  "coworld_id": "cow_ab2d905c-54e0-42a9-b4e1-d4e0aaa3cf47",
  "coworld_name": "pommerman",
  "coworld_version": "0.1.1",
  "variant_name": "2v2 Team Radio (11x11)",
  "episode_id": "0c442902-761c-4548-832a-7fb09df78a81",
  "created_at": "2026-08-27T21:25:36.738764Z",
  "completed_at": "2026-08-27T21:32:39.756517Z",
  "error": null,
  "error_type": null
}
```

And the round's own attributions, showing the ladder seated both champions:

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq '.entries[]|select(.id=="round_36e8e498-8d55-4628-91a9-b593df5c5d3e")|{round_number,status,round_config}'
```

```json
{
  "round_number": 7,
  "status": "completed",
  "round_config": {
    "stages": null,
    "purpose": "ladder",
    "entrant_attributions": [
      {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
       "policy_version_id": "8f3eef38-df2d-4b89-878e-5dea55713411",
       "league_policy_membership_id": "lpm_2054f169-7ba4-4eb2-bb99-11ad78dfecb7"},
      {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
       "policy_version_id": "a69f2a4f-5347-4e29-a3d5-467507ed6f5a",
       "league_policy_membership_id": "lpm_f857e461-79bf-43f6-a2c8-f0b1a430742f"}
    ],
    "entrant_policy_version_ids": ["8f3eef38-df2d-4b89-878e-5dea55713411",
                                   "a69f2a4f-5347-4e29-a3d5-467507ed6f5a"]
  }
}
```

Status: **TRUE** — `status == "completed"`, non-null `replay_url`, and the four participants name
`daveey` (seat 0) and `daveey-1` (seat 1) as non-fillers, with `pommerman-camper` and
`pommerman-sapper` flagged `is_filler: true` (seats 2 and 3, rendered `Baseline` / `Baseline (2)`
in the episode — see check 4). Scores are exactly zero-sum, +105/−105 per seat, as the design
requires.

---

## 4. Replay bytes are valid and show the game — **TRUE**

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/1dc81bbf-936a-49f4-bb67-bdad75bf6792.replay" \
  -o /tmp/ep.replay -w 'http=%{http_code} bytes=%{size_download}\n'
head -c 32 /tmp/ep.replay | od -c | head -2
```

```
http=200 bytes=199040
0000000   C   O   W   L   D   P   O   M 001  \0  \t  \0  \0  \0   p   o
0000020   m   m   e   r   m   a   n 001  \0  \0  \0   1 311 002  \0  \0
```

The replay is the **binary COWLDPOM** container the static wasm viewer parses, so raw `jq` cannot
read it. The **design-declared substitute** is used (`runs/2026-08-27-pommerman/design.md`
lines 970–983 and 1617 specify the JSON view and the exact predicates; `tools/replay_summary.py`
is stdlib-only and emits one strict-UTF-8 JSON object). The checkout is at 0.1.1's tip:

```bash
git -C /workspace/cogame-pommerman log --oneline -3
```

```
ec8f1fb 60-check5: the attempt-1 notice announces a retry, not a fallback
02653fa 60-check5: raise the LLM deadlines above the measured hosted p90
9fa80f8 F5 (cont.): the remaining declared deltas in the errata
```

```bash
python3 /workspace/cogame-pommerman/tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
jq 'with_entries(select(.value|type!="array" and type!="object"))' /tmp/ep.json
```

```
strict UTF-8 JSON: ok
{
  "protocol": "pommerman/v1",
  "game": "pommerman",
  "gameVersion": "1",
  "seed": 94311912,
  "boardSize": 11,
  "tickCount": 271,
  "fallbacks": 2
}
```

**Protocol match.** The published manifest declares `game.protocols.{player,global}` as URIs to
`docs/PROTOCOL.md` and carries no inline wire-id, so the protocol identifier is pinned in source
and design: `src/pommerman/sim_types.nim:20  ProtocolId* = "pommerman/v1"`, and `design.md:1617`
requires `protocol == "pommerman/v1"`. The replay says `pommerman/v1`. Additionally the
**resolved config embedded in the replay** carries the manifest's variant settings and proves the
0.1.1 deadlines were the ones in force:

```bash
jq -c '{protocol:.config.protocol, attempt1Ms:.config.attempt1Ms, retryMs:.config.retryMs,
        turnBudgetMs:.config.turnBudgetMs, num_agents:.config.num_agents, maxTicks:.config.maxTicks,
        collapseTicks:.config.collapseTicks, wallClockBudgetSeconds:.config.wallClockBudgetSeconds}' /tmp/ep.json
```

```json
{"protocol":"pommerman/v1","attempt1Ms":12000,"retryMs":5000,"turnBudgetMs":18000,"num_agents":4,"maxTicks":144,"collapseTicks":[96,120],"wallClockBudgetSeconds":640}
```

**Results.**

```bash
jq '.results' /tmp/ep.json
```

```json
{
  "names": ["daveey", "daveey-1", "Baseline", "Baseline (2)"],
  "aliases": ["RED-1", "BLUE-1", "RED-2", "BLUE-2"],
  "teams": ["RED", "BLUE", "RED", "BLUE"],
  "scores": [105, -105, 105, -105],
  "win": [true, false, true, false],
  "winner": "RED",
  "reason": "complete",
  "endRule": "wipe",
  "teamScores": [105, -105],
  "teamAlive": [1, 0],
  "teamKills": [0, 0],
  "teamWood": [6, 21],
  "alive": [true, false, false, false],
  "kills": [0, 0, 0, 0],
  "deaths": [0, 1, 1, 1],
  "suicides": [0, 0, 0, 1],
  "bombsPlaced": [8, 5, 0, 14],
  "woodCleared": [6, 6, 0, 15],
  "kicks": [0, 0, 0, 0],
  "pickups": [3, 3, 0, 6],
  "radioSent": [36, 36, 36, 36],
  "finalTick": 141,
  "turnsPlayed": 36,
  "seed": 94311912,
  "policyKinds": ["llm", "llm", "scripted", "scripted"],
  "llmTurns": [36, 36, 0, 0],
  "fallbackTurns": [0, 0, 0, 0],
  "ordersRejected": [1, 1, 0, 0],
  "deadSeats": [false, false, false, false],
  "stopDetail": ""
}
```

**Champion decisions are LLM, not scripted, and not fallbacks.**

```bash
jq -r '[.orders[]|select(.slot<2)]|group_by(.source)|map({source:.[0].source,n:length})' /tmp/ep.json
jq -r '[.orders[]|select(.slot>=2)]|group_by(.source)|map({source:.[0].source,n:length})' /tmp/ep.json
jq -r '[.orders[]|select(.slot==0)|.verb]|group_by(.)|map("\(.[0]):\(length)")|join(" ")' /tmp/ep.json
jq -r '[.orders[]|select(.slot==1)|.verb]|group_by(.)|map("\(.[0]):\(length)")|join(" ")' /tmp/ep.json
jq '{champ_directives:([.directives[]|select(.slot<2)]|length),
     distinct_say:([.directives[]|select(.slot<2)|.say]|unique|length),
     empty_say:([.directives[]|select(.slot<2 and (.say==""))]|length),
     say_chars_mean:(([.directives[]|select(.slot<2)|(.say|length)]|add)/72|floor)}' /tmp/ep.json
jq -r '[.radio[]|select(.a!=1 or .b!=1)]|length' /tmp/ep.json
jq -c '[.radio[]|select(.slot<2)|"\(.a),\(.b)"]|group_by(.)|map({p:.[0],n:length})' /tmp/ep.json
```

```
[{"source":"llm","n":72}]
[{"source":"scripted","n":72}]
break:10 go:15 hide:4 hunt:7
break:9 go:5 hide:22
{
  "champ_directives": 72,
  "distinct_say": 72,
  "empty_say": 1,
  "say_chars_mean": 62
}
81
[{"p":"1,1","n":23},{"p":"1,4","n":2},{"p":"2,1","n":5},{"p":"3,1","n":4},{"p":"3,5","n":8},{"p":"4,1","n":14},{"p":"4,2","n":6},{"p":"5,1","n":1},{"p":"5,2","n":1},{"p":"5,4","n":1},{"p":"5,5","n":5},{"p":"8,1","n":2}]
```

**The two `fallback` records, verbatim** — brace-matched out of the raw COWLDPOM chat records:

```json
{"k":"fallback","turn":8,"slot":1,"attempt":1,"cause":"timeout","detail":"llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke"}
{"k":"fallback","turn":35,"slot":1,"attempt":1,"cause":"timeout","detail":"llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke"}
```

Both are `attempt: 1` records — a failed *attempt*, retried and answered. `results.fallbackTurns`
is `[0,0,0,0]`: **no turn in this episode was actually decided by a fallback.** The top-level
`fallbacks: 2` counter in the summary counts attempt-failure records, not fallback turns (see
`tools/replay_summary.py` lines 182/211 and `src/pommerman/decide.nim:155`). Both retries landed:
turn 8 seat 1 answered in 1940 ms, turn 35 seat 1 in 3599 ms.

```bash
jq -c '.directives[]|select(.slot<2 and ((.turn>=7 and .turn<=9) or (.turn>=34 and .turn<=36)))
       |{turn,slot,source,latency_ms,verb}' /tmp/ep.json
```

```json
{"turn":7,"slot":0,"source":"llm","latency_ms":2681,"verb":"hide"}
{"turn":7,"slot":1,"source":"llm","latency_ms":2681,"verb":"break"}
{"turn":8,"slot":0,"source":"llm","latency_ms":12000,"verb":"go"}
{"turn":8,"slot":1,"source":"llm","latency_ms":1940,"verb":"break"}
{"turn":9,"slot":0,"source":"llm","latency_ms":7360,"verb":"go"}
{"turn":9,"slot":1,"source":"llm","latency_ms":7360,"verb":"go"}
{"turn":34,"slot":0,"source":"llm","latency_ms":3095,"verb":"hunt"}
{"turn":34,"slot":1,"source":"llm","latency_ms":3095,"verb":"hide"}
{"turn":35,"slot":0,"source":"llm","latency_ms":12001,"verb":"hide"}
{"turn":35,"slot":1,"source":"llm","latency_ms":3599,"verb":"hide"}
{"turn":36,"slot":0,"source":"llm","latency_ms":3801,"verb":"hunt"}
{"turn":36,"slot":1,"source":"llm","latency_ms":3801,"verb":"hide"}
```

Status: **TRUE** — valid strict-UTF-8 JSON view of the bytes; `protocol == "pommerman/v1"`;
`results.reason == "complete"` (no deadline exception needed); **72/72** champion orders have
`source == "llm"` and **0** are scripted; **0** champion turns fell back; 71 of 72 champion
directives carry a distinct non-empty `say`; radio is non-trivial (81 of 144 pairs are something
other than `1·1`, across 12 distinct pairs for the champion seats). The champion seats are visibly
playing the game the coworld is about: breaking wood, moving into the collapsing arena, hiding
from fuses, and hunting the last enemy.

---

## 5. Hosted game log is clean — **TRUE**  *(this is the check that was FALSE last pass)*

```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs7.raw \
  -w 'http=%{http_code} bytes=%{size_download}\n'
```

```
http=200 bytes=154131
```

The body is python `b'…'` byte-string reprs under `===== container: <name> =====` headers, so it
was **decoded before grepping** (`ast.literal_eval` per repr — `playbooks/observatory-api.md` §10).
Decoder report:

```
containers: ['coworld-init-config', 'bedrock-sidecar', 'game', 'worker']
decoded bytes: 153795
raw-unparsed lines: 0        # every repr decoded; no line was skipped
```

```bash
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' \
  /tmp/logs7.decoded.txt || echo CLEAN
```

```
CLEAN
```

Case-insensitive control run, to show what is in there and why the specified grep is not merely
lucky:

```bash
grep -inE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs7.decoded.txt
```

```
321:results: {"names":["daveey","daveey-1","Baseline","Baseline (2)"],…,"llmTurns":[36,36,0,0],"fallbackTurns":[0,0,0,0],"ordersRejected":[1,1,0,0],"deadSeats":[false,false,false,false],"stopDetail":""}
```

The single case-insensitive hit is the camelCase **`ordersRejected`** key inside the results JSON
line — a field name, not a rejection message, and it does not match the specified lowercase
`rejected` pattern. The two attempt-1 events now announce themselves honestly:

```bash
grep -nE 'will retry|out of attempts|throttled' /tmp/logs7.decoded.txt
```

```
316:pommerman llm: seat 1 attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
317:pommerman llm: seat 1 attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
```

No `out of attempts` line exists, i.e. no attempt-2 failure and therefore no genuine fallback — the
genuine-fallback line still contains the greppable phrase and simply never fired.

Sidecar cross-check, parsed out of the same decoded log (`bedrock_sidecar_complete` records):

```
completes: 74
status codes: {200: 74}
latency ms: min 1939  p50 6082  p90 7570  max 9638
calls over 12000 ms (new attempt1Ms): 0
calls over  8000 ms (old attempt1Ms): 4
ok=false: 0
```

Status: **TRUE** — `CLEAN`. Zero throttling, zero non-200 Bedrock calls, and the raised deadline
now sits above the whole observed hosted distribution (max 9638 ms vs `attempt1Ms` 12000). No
platform-wide-LLM exception is being claimed; this is simply clean.

*Attention item (not a check-5 predicate):* two attempt-1 client timeouts still occurred (turn 8
and turn 35, both seat 1, 2 of 72 champion turns = 2.8 %), even though no single Bedrock call
exceeded 9638 ms at the sidecar. The client deadline covers the whole parallel batch plus sidecar
queueing, so batch-level wall time can cross 12 s while each individual call does not. Both were
recovered by the retry at zero cost to the episode, and the log is clean — but if the coordinator
wants attempt-1 timeouts at literally zero, the remaining lever is per-seat rather than per-batch
deadlines, not a bigger number.

---

## 6. The public page uses the static replay path — **TRUE**

**Source used: the SSR payload + the session API** (the raw-HTML iframe grep found nothing, which
`playbooks/observatory-api.md` §Featured match records as *unknown*, not a failure). All three
sources are shown.

*(a) The raw-HTML grep — no match:*

```bash
curl -sS "https://softmax.com/pommerman" -o /tmp/page.html -w 'http=%{http_code} bytes=%{size_download}\n'
grep -o '<iframe[^>]*src="[^"]*"' /tmp/page.html || echo "(no match)"
```

```
http=200 bytes=699265
(no match)
```

*(b) The `/coworlds` fallback the prompt names — present, but `featured_match` is `null`
platform-wide, so it is recorded and not relied on:*

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)|.[]|select(.name=="pommerman")
          |{id,name,version,canonical,replay_viewer,featured_match}'
```

```json
{"id":"cow_ab2d905c-54e0-42a9-b4e1-d4e0aaa3cf47","name":"pommerman","version":"0.1.1","canonical":true,"replay_viewer":null,"featured_match":null}
{"id":"cow_224b5627-9e46-46e5-ad55-1b2692cc503b","name":"pommerman","version":"0.1.0","canonical":false,"replay_viewer":null,"featured_match":null}
```

**The canonical coworld is the new one:** `cow_ab2d905c…` at 0.1.1 is `canonical: true`; the old
`cow_224b5627…` at 0.1.0 is `canonical: false`. The API is *not* still pointing at the old cow.

*(c) The featured match, server-rendered into the page's SSR payload at `state.playlist[0]`
(fetched 21:39Z, JSON unescaped for readability):*

```json
"playlist":[{"episodeId":"0c442902-761c-4548-832a-7fb09df78a81","coworldId":"cow_ab2d905c-54e0-42a9-b4e1-d4e0aaa3cf47","coworldName":"pommerman","coworldVersion":"0.1.1","replayUrl":"https://softmax-public.s3.amazonaws.com/replays/1dc81bbf-936a-49f4-bb67-bdad75bf6792.replay","finishedAt":"2026-08-27T21:32:39.756517Z","roundNumber":7,"episodeNumber":1,"code":"pommerman.r7.e1","matchup":{"divisionId":"div_7c2c9172-a9dd-449b-8911-e5d072c11d25","divisionName":"Competition","first":{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1017.546259199346,"score_label":"MMR","score_value_type":"integer","rounds_played":6,"episode_wins":3,"episodes_played":null,"win_rate":0.5,"policy_label":"pommerman-firestarter:v1","recent_rounds":null},"second":{"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":982.453740800654,"score_label":"MMR","score_value_type":"integer","rounds_played":6,"episode_wins":2,"episodes_played":null,"win_rate":0.3333333333333333,"policy_label":"pommerman-cornerman:v1","recent_rounds":null}},"inspectUrl":"/observatory/v2?tab=overview&detail=episode-request:ereq_1274172a-9257-4e94-9454-893f48bb0c97","outcome":"first"}]
```

A featured match **is** present — `pommerman.r7.e1`, the **round-7 / 0.1.1** episode, on the new
`cow_ab2d905c…`, with both ranked players in the matchup. The "fewer than two ranked players"
failure does not apply.

*(d) The iframe `src`, from the call the page's own JS makes:*

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_ab2d905c-54e0-42a9-b4e1-d4e0aaa3cf47",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/1dc81bbf-936a-49f4-bb67-bdad75bf6792.replay"}'
```

`http=200`

```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_ab2d905c-54e0-42a9-b4e1-d4e0aaa3cf47/sha256%3Af143a6463712214a07f9613aa14b22feaf2fb80bf8bf57c9af04e410cab878b8/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F1dc81bbf-936a-49f4-bb67-bdad75bf6792.replay&v=2","ready":true}
```

```bash
curl -sS -o /dev/null -w 'http=%{http_code}\n' "$viewer_url"
```

```
http=200
```

The `<sha>` segment is checked against the live coworld record, not against memory:

```bash
curl -sS "$BASE/coworlds/$COW" "${AUTH[@]}" | jq -r '.manifest_hash, .version, .canonical, .name'
```

```
sha256:f143a6463712214a07f9613aa14b22feaf2fb80bf8bf57c9af04e410cab878b8
0.1.1
true
pommerman
```

Status: **TRUE** — the path is
`/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`, with `<cow_id>` =
`cow_ab2d905c-54e0-42a9-b4e1-d4e0aaa3cf47` (the **new** 0.1.1 coworld) and `<sha>` = the
URL-encoded `sha256:f143a646…`, which equals both `STATE.coworld.manifest_sha` and the live
`manifest_hash`. `ready: true`, the URL returns 200, and it is **not** a `/client/replay` pod URL.

---

## 7. Certification declared the static bundle — **TRUE**

Source: **the committed `runs/2026-08-27-pommerman/release-result.json`** (phase 40's artifact,
overwritten with the 0.1.1 copy at 21:14Z per `log.md`). It was present, so no re-download from
run 33116243915 was needed.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-27-pommerman/release-result.json
```

```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

That the committed file is the **0.1.1** artifact, not the stale 0.1.0 one:

```bash
jq '{ok, version, cow_id, canonical, manifest_sha, secret_put, step_failed, errors}' \
  runs/2026-08-27-pommerman/release-result.json
```

```json
{
  "ok": true,
  "version": "0.1.1",
  "cow_id": "cow_ab2d905c-54e0-42a9-b4e1-d4e0aaa3cf47",
  "canonical": true,
  "manifest_sha": "sha256:f143a6463712214a07f9613aa14b22feaf2fb80bf8bf57c9af04e410cab878b8",
  "secret_put": true,
  "step_failed": null,
  "errors": []
}
```

The certification tail, from the same file (`.certify.output_tail`), all ten steps passed:

```
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
…
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Corroborated live: the published manifest declares a static viewer bundle —

```bash
curl -sS "$BASE/coworlds/$COW" "${AUTH[@]}" | jq -c '.manifest.game.replay_viewer'
```

```json
{"bundle":"sha256:5b70acabed96d2f256c49de09d895e6ceb17475d43e5effe52c6719db1f353e9"}
```

Status: **TRUE** — the required string `Replay liveness: skipped (static replay bundle declared`
is present, in the 0.1.1 artifact, with `certify.ok: true`.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

*(a) Dispatch.* Dispatched at **21:38:29Z** against the exact iframe `src` from check 6:

```bash
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder \
  -f url="https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_ab2d905c-54e0-42a9-b4e1-d4e0aaa3cf47/sha256%3Af143a6463712214a07f9613aa14b22feaf2fb80bf8bf57c9af04e410cab878b8/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F1dc81bbf-936a-49f4-bb67-bdad75bf6792.replay&v=2" \
  -f timeout=90
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[]|[.databaseId,.createdAt,.status,.conclusion]|@tsv'
```

```
33119081304	2026-08-27T21:38:31Z	in_progress	
33114175789	2026-08-27T20:36:49Z	completed	success
33113882071	2026-08-27T20:33:16Z	completed	success
33106609970	2026-08-27T19:03:57Z	completed	success
33087427495	2026-08-27T15:22:13Z	completed	success
```

(first five of ten rows shown; `33114175789` is the **previous** pass's run and is not reused.)

The new run is **33119081304**, created 21:38:31Z, two seconds after the dispatch — found by
sorting on `createdAt`, not by taking "the latest" blind.

```bash
gh run watch 33119081304 -R Metta-AI/coworld-builder --exit-status
```

```
✓ main viewer-check · 33119081304
✓ viewer-check in 38s (ID 98681128648)
  ✓ Load the viewer   ✓ Summary   ✓ Upload the evidence   ✓ Fail if the viewer did not load
watch exit=0
```

```bash
gh run download 33119081304 -R Metta-AI/coworld-builder -n viewer-check \
  -D runs/2026-08-27-pommerman/viewer-check
```

```
smoke-stderr.txt (0 bytes)  smoke-stdout.txt (699)  viewer-smoke.json (1501)  viewer-smoke.png (452902)
```

*(b) The readouts, verbatim.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-27-pommerman/viewer-check/viewer-smoke.json
```

```json
{"loaded":true,"ms":2055,"clock":"turn 1/36 TICK 0/144 · WALLS CLOSE IN 96","scorebug":"RED DAVEEY · BASELINE RED-11/2 RED-21/2 ALIVE 2 0 ≋ 1·1 turn 1/36 TICK 0/144 · WALLS CLOSE IN 96 BLUE DAVEEY-1 · BASELINE (2) BLUE-11/2 BLUE-21/2 ALIVE 2 0 ≋ 1·1","feed_lines":0}
```

```bash
jq -c '.signals' runs/2026-08-27-pommerman/viewer-check/viewer-smoke.json
```

```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/2026-08-27-pommerman/viewer-check/viewer-smoke.json
jq -c '.canvas_text' runs/2026-08-27-pommerman/viewer-check/viewer-smoke.json
jq -c '.status, .loading_text, .console_tail' runs/2026-08-27-pommerman/viewer-check/viewer-smoke.json
```

```
no failure
{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
"CONNECTING"
null
[]
```

*The three clock readouts (`#scrub` exists in this shell, so all three were taken):*

| scrub position | `#clock` readout |
|---|---|
| 0 % | `turn 1/36 TICK 0/144 · WALLS CLOSE IN 96` |
| 50 % | `turn 31/36 TICK 122/144 · THE ARENA IS THE MIDDLE 5X5` |
| 100 % | `turn 36/36 TICK 141/144 · THE ARENA IS THE MIDDLE 5X5` |

All three **differ**, and they differ in the right direction: turn 1 → 31 → 36, tick 0 → 122 → 141,
and the caption changes from the pre-collapse warning to the collapsed 5×5 arena. `loaded: true`
after 2055 ms via `data-replay-loaded="true"`. No page error, no console output, no failure.

Two instrumentation notes, neither of which is a rendering defect:
- `feed_lines: 0` — the harness looks for `#feed, .feed, #log` (`templates/tools/ci/viewer_smoke.mjs:425`).
  This shell names its feed **`#killfeed`** (ids in `client/replay_broadcast.html`), so the selector
  simply misses. The feed **is** drawing: it is legible in the screenshot (see below). The readout
  is also taken at the load instant (turn 1, tick 0), before any `say` has been queued.
- `canvas_text.total: 0` — this shell renders on an OffscreenCanvas in a worker, so the
  `fillText`/`strokeText` hook in the main frame sees nothing. Recorded, not judged on
  (the r1 review already established the same for the local smoke and proved non-vacuity with a
  renderer fixture that measures real `broadcast_core` draws).

*(c) What the viewer was asked to draw — ordered excerpts of the replay record:*

```bash
jq -r '.directives[]|select(.turn<=3)|[.turn,.alias,.source,.verb,"radio \(.radio[0])·\(.radio[1])",.say]|@tsv' /tmp/ep.json
```

```
1	RED-1	llm	break	radio 1·1	Breaking wood from NW corner
1	BLUE-1	llm	break	radio 2·1	Turn 1: breaking wood in my quadrant
1	RED-2	scripted	hide	radio 1·1
1	BLUE-2	scripted	break	radio 2·1
2	RED-1	llm	break	radio 1·1	Turn 2: continuing break phase, gaining lanes and hunting for power-ups
2	BLUE-1	llm	break	radio 1·1	NE quadrant clearing. Safe setup phase.
3	RED-1	llm	break	radio 1·1	Breaking east in Q1, bomb detonates soon, hunting power-ups
3	BLUE-1	llm	break	radio 1·1	Turn 3: continuing quadrant break, searching for range/ammo power-ups
```

```
18	RED-1	llm	break	radio 1·4	Breaking toward middle, range 3, safe. Partner in SW quad also breaking.
18	BLUE-1	llm	hide	radio 4·1	Holding corridor mouth. No enemies in range. Safe sector. Awaiting approach.
18	BLUE-2	scripted	break	radio 3·1
19	RED-1	llm	go {"x":5,"y":5}	radio 5·4	Moving to middle 5x5 zone before collapse at tick 96. 24 ticks to reach safety.
19	BLUE-1	llm	hide	radio 4·1	Holding corridor mouth, all safe. Both reds far. Partner secure.
19	BLUE-2	scripted	bomb	radio 4·1
```

```
35	RED-1	llm	hide	radio 5·5	BLUE-2 trapped by own bomb, we win in 1 tick
35	BLUE-1	llm	hide	radio 4·2	BLUE-1 dead; BLUE-2 at (7,5) with bomb fuse 5. Holding safe.
35	RED-2	scripted	hide	radio 1·1
35	BLUE-2	scripted	bomb	radio 3·2
36	RED-1	llm	hunt BLUE-2	radio 3·5	End game: hunting BLUE-2 in middle zone. One opponent left.
36	BLUE-1	llm	hide	radio 1·1	I am dead. BLUE-2 must survive and win.
36	RED-2	scripted	hide	radio 1·1
36	BLUE-2	scripted	bomb	radio 3·2
```

**Spectator judgment.** The screenshot (`runs/2026-08-27-pommerman/viewer-check/viewer-smoke.png`,
1280×800, taken after the 100 % seek) shows a finished match, and it is legible. Across the top is
the starter's scorebug: `RED  DAVEEY ·…` on the left with per-bomber chips `RED-1 1/4` and a
struck-through `RED-2 1/2`, `ALIVE 1`; the centre reads **`turn 36/36`** over
`TICK 141/144 · THE ARENA IS THE MIDDLE 5X5`; the right side mirrors it for
`BLUE  DAVEEY-1 · BASELINE (2)` with both `BLUE-1` and `BLUE-2` struck through and `ALIVE 0`, and a
yellow `DANGER` badge in the corner. The 11×11 board fills the stage behind a dimmed endcard
overlay, tiles drawn with the coworld's own art. The endcard headline is
**“RED TAKES IT — BLUE WIPED AT TICK 141”**, under it the chip `SCORE +105 / -105` and the line
`end rule: wipe · 141 ticks · wood 6–21 · complete`, then two team tables (RED / BLUE) with columns
`BOMBER · KILLS · BOMBS · WOOD · RADIO`: `RED-1 · DAVEEY 0 8 6 3·5`, `RED-2 · BASELINE 0 0 0 1·1`,
`BLUE-1 · DAVEEY… 0 5 6 1·1`, `BLUE-2 · BASELI… 0 14 15 3·2`, and `BOMBERS LEFT 1` vs `0`.
Every one of those numbers reconciles exactly with the replay record: `bombsPlaced [8,5,0,14]`,
`woodCleared [6,6,0,15]`, `kills [0,0,0,0]`, `teamWood [6,21]`, `teamAlive [1,0]`, `finalTick 141`,
`endRule "wipe"`, `reason "complete"`, and the turn-36 radio pairs `3·5 / 1·1 / 1·1 / 3·2`. Bottom
right, the killfeed is rendering live lines — `RED-2 → hide`, `RED radios 1·1`, `BLUE-2 → bomb`,
`BLUE radios 4·2` — which match the turn-35/36 orders above (RED-2 the camper hiding, BLUE-2 the
sapper still bombing). Along the bottom is the starter's transport strip: restart, step-back,
pause, `+5s`, play, loop, fast-forward, a highlighted `spoilers` toggle, the status readout
`RED WINS 231 / 231`, and speed chips `1× 2× 3× 4× 8× 16×` with `1×` lit; beneath it the full-width
scrubber, its beat markers (yellow / white / red / blue ticks at the firstblood, death and collapse
beats) and the momentum graph labelled `BOMBERS STANDING`. This is the same chrome as
paintbot / raid / hive — transport strip, scrubbed timeline with momentum graph, scorebug, endcard
— not a lookalike rewrite, so the cogame-gridlock failure mode does not apply. The picture is
neither empty nor frozen: the three clock readouts advance turn 1 → 31 → 36, and the picture at
100 % is the endcard the record says should be there. The one legibility nit is unchanged from the
first pass and remains cosmetic: the scorebug truncates the owner names to `DAVEEY ·…` and
`DAVE…` at 1280 px width.

Status: **TRUE** — `loaded: true` **and** the three clock readouts differ.

---

## Summary

| # | Check | Verdict | Evidence from |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** | `/rounds?league_id=` — 6 completed; rounds 3–7 all after 20:11:28Z |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** | `/divisions/$D/leaderboard` — daveey #1, daveey-1 #2, 6 rounds each |
| 3 | Latest round's episode request completed w/ replay | **TRUE** | round 7 → `ereq_1274172a…`, `completed`, replay `1dc81bbf…`, coworld_version 0.1.1 |
| 4 | Replay bytes valid and show the game | **TRUE** | `1dc81bbf….replay`, `pommerman/v1`, `reason complete`, 72/72 llm, 0 fallback turns |
| 5 | Hosted game log clean | **TRUE** | `ereq_1274172a…/artifacts/logs`, decoded, grep → `CLEAN` |
| 6 | Public page uses the static replay path | **TRUE** | SSR `playlist[0]` (r7, cow_ab2d905c) + `/coworlds/replays/session` → static index.html, sha f143a646 |
| 7 | Certification declared the static bundle | **TRUE** | committed `runs/2026-08-27-pommerman/release-result.json` (0.1.1) |
| 8 | Viewer executed and judged | **TRUE** | viewer-check run **33119081304**, `loaded:true`, clocks 1→31→36 |

Non-blocking attention items for the coordinator (none is a definition-of-done predicate):

1. **Attempt-1 timeouts persist at 2.8 %** (2/72 champion turns) despite the raised deadline; both
   recovered by retry, zero fallback turns, log clean. Root cause is batch-level rather than
   per-call timing (§5).
2. **`bombsPlaced[RED-2] == 0` again.** The camper baseline placed no bomb in round 7 either
   (`bombsPlaced [8,5,0,14]`, `woodCleared [6,6,0,15]`), and it was seated as RED-2 while sapper
   took BLUE-2. The design's clause that every seat contributes bombs is still unmet by the camper.
3. **`kicks [0,0,0,0]`** — no production episode has yet exercised the kick beat, so that beat
   button and its killfeed line remain unevidenced in a hosted replay (phase-20 already flagged the
   CI replay has no kick).
4. **`feed_lines` is structurally unmeasurable** by the shared harness for this coworld: the shell
   names its feed `#killfeed`, the harness looks for `#feed, .feed, #log`. Renaming the id (or
   adding `class="feed"`) would let future runs measure it instead of reading it off the picture.
5. **Scorebug name truncation** at 1280 px (`DAVEEY ·…`, `DAVE…`) — cosmetic, unchanged.
