# VERIFY — pommerman   (2026-08-27T20:45Z)

Verdict: **1 item false** — check 5 (hosted game log not CLEAN). Checks 1, 2, 3, 4, 6, 7, 8 TRUE.

Environment for every command below (values never printed):

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_7b53400d-b780-4024-924a-59bc2818dc8d
D=div_7c2c9172-a9dd-449b-8911-e5d072c11d25
COW=cow_224b5627-9e46-46e5-ad55-1b2692cc503b
```

All evidence below was fetched fresh in this heartbeat (2026-08-27 20:12Z–20:45Z), except the two
documented exceptions: check 7 (the committed `release-result.json`) and check 8 (the artifact of
the `viewer-check.yml` run dispatched by this verifier at 20:36:47Z).

---

## 1. ≥2 completed rounds after fillers were set — **TRUE**

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq 'if type=="array" then . else .entries end
       | map({id,round_number,status,error,created_at,completed_at})'
```

`http 200`

```json
[
  {
    "id": "round_7868a38d-5b62-4fd2-8fa7-40433bc25f76",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-27T20:25:31.602261Z",
    "completed_at": "2026-08-27T20:32:43.121716Z"
  },
  {
    "id": "round_5020c3b6-8969-4f18-b94b-4c1661ee3006",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-27T20:10:31.210752Z",
    "completed_at": "2026-08-27T20:17:29.671036Z"
  },
  {
    "id": "round_e4540277-b34c-49c0-acab-da5b4307e005",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-27T20:10:01.494362Z",
    "completed_at": "2026-08-27T20:10:01.756755Z"
  }
]
```

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
```

```
2
```

Round 1's `error`, recorded verbatim as required: `Temporal RoundWorkflow failed before settling the
round.` — the documented consequence of the auto-created round firing before any filler policy
existed (`playbooks/observatory-api.md` §6). It is `failed`, so it does not count.

**Fillers were in force from round 2 onward.** Registration, fetched fresh with the elevated header
(the read 403s on bare AUTH):

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"
```

```json
{"filler_policy_versions":[{"policy_version_id":"95cc7892-4e3c-405a-a467-c7480fa55cb9","policy_id":"425498c8-82a4-4f1a-a761-82f540d329e2","policy_name":"pommerman-sapper","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},{"policy_version_id":"2dec3894-c52a-458e-915d-fcbd88b1a9df","policy_id":"d6b1ff29-2670-4ca7-86a9-454edb049a12","policy_name":"pommerman-camper","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```

And the seating actually used in round **2** — the earlier of the two completed rounds — proves the
fillers were live before it ran, not merely registered:

```bash
curl -sS "$BASE/episode-requests/ereq_20741863-24b7-4aa8-be96-ffde53f3cd26" "${AUTH[@]}" \
 | jq -c '{status,replay_url,participants:[.participants[]|{position,policy_name,player_name,is_filler}]}'
```

```json
{"status":"completed","replay_url":"https://softmax-public.s3.amazonaws.com/replays/0503d141-5b35-43a4-9258-2bba23ba5314.replay","participants":[{"position":0,"policy_name":"pommerman-firestarter","player_name":"daveey","is_filler":false},{"position":1,"policy_name":"pommerman-cornerman","player_name":"daveey-1","is_filler":false},{"position":2,"policy_name":"pommerman-camper","player_name":"daveey","is_filler":true},{"position":3,"policy_name":"pommerman-camper","player_name":"daveey","is_filler":true}]}
```

Status: **TRUE** — rounds 2 and 3 completed (20:17:29Z and 20:32:43Z); both ran with `is_filler:true`
seats, i.e. both are after the fillers were set; round 1 is `failed` and excluded, its error quoted.

---

## 2. Both champions ranked, fillers absent/Baseline — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq .
```

`http 200` — bare list, as documented:

```json
[
  {
    "rank": 1,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 1001.4695015289755,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 1.0,
    "episodes_played": null,
    "win_rate": 0.5,
    "policy_label": "pommerman-cornerman:v1",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 998.5304984710245,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 1.0,
    "episodes_played": null,
    "win_rate": 0.5,
    "policy_label": "pommerman-firestarter:v1",
    "recent_rounds": null
  }
]
```

```bash
… | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```

```
1	daveey-1	pommerman-cornerman:v1	1001.4695015289755	2	1.0
2	daveey	pommerman-firestarter:v1	998.5304984710245	2	1.0
```

Status: **TRUE** — both `daveey` and `daveey-1` present, `rounds_played = 2` each (≥ 1); the two
filler policies (`pommerman-sapper`, `pommerman-camper`) are absent from the leaderboard entirely.

---

## 3. Latest completed round's episode request completed with a replay — **TRUE**

```bash
R=round_7868a38d-5b62-4fd2-8fa7-40433bc25f76      # max_by(round_number) over completed rounds
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" \
 | jq -c 'if type=="array" then . else .entries end|map({id,status,created_at})'
```

(the nested route; the flat `?round_id=` route is HTTP 405 since 2026-08-26)

```json
[{"id":"ereq_51dda9f7-4c41-48a6-b9ae-05022f0e329a","status":"completed","created_at":"2026-08-27T20:25:31.899259Z"}]
```

```bash
EREQ=ereq_51dda9f7-4c41-48a6-b9ae-05022f0e329a
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```

`http 200`

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/0ad28a03-2b00-46d3-bd99-1202c2251c00.replay",
  "participants": [
    {
      "position": 0,
      "kind": "policy",
      "policy_version_id": "8f3eef38-df2d-4b89-878e-5dea55713411",
      "policy_id": "eb97ea73-bf63-4fd4-a89c-fb9323a8b17a",
      "policy_name": "pommerman-firestarter",
      "version": 1,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": false,
      "is_seed": false
    },
    {
      "position": 1,
      "kind": "policy",
      "policy_version_id": "a69f2a4f-5347-4e29-a3d5-467507ed6f5a",
      "policy_id": "b9049af8-9763-43a9-80db-7920471b5aca",
      "policy_name": "pommerman-cornerman",
      "version": 1,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
      "player_name": "daveey-1",
      "is_filler": false,
      "is_seed": false
    },
    {
      "position": 2,
      "kind": "policy",
      "policy_version_id": "2dec3894-c52a-458e-915d-fcbd88b1a9df",
      "policy_id": "d6b1ff29-2670-4ca7-86a9-454edb049a12",
      "policy_name": "pommerman-camper",
      "version": 1,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": true,
      "is_seed": false
    },
    {
      "position": 3,
      "kind": "policy",
      "policy_version_id": "2dec3894-c52a-458e-915d-fcbd88b1a9df",
      "policy_id": "d6b1ff29-2670-4ca7-86a9-454edb049a12",
      "policy_name": "pommerman-camper",
      "version": 1,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": true,
      "is_seed": false
    }
  ],
  "participant_scores": [
    {"position": 0, "score": -110.0},
    {"position": 1, "score": 110.0},
    {"position": 2, "score": -110.0},
    {"position": 3, "score": 110.0}
  ]
}
```

Status: **TRUE** — `status == "completed"`, non-null `replay_url`, participants name `daveey`
(seat 0) and `daveey-1` (seat 1), the other two seats `is_filler: true` and rendered `Baseline` /
`Baseline (2)` in the replay's own `results.names` (see check 4). Scores are exactly zero-sum
(−110/+110/−110/+110), as the design requires.

**Observation, not a check failure:** the ladder seated `pommerman-camper` in **both** filler seats
in both completed rounds; `pommerman-sapper` was never seated as a filler even though it is
registered (check 1 output shows both in the filler list). Consequence in the episode: both
Baseline seats are the deliberately-passive camper, so `bombsPlaced` is 0 on both — see check 4.

---

## 4. Replay bytes are valid and show the game — **TRUE** (one design-note clause unmet; recorded below)

The replay is the starter's **binary `COWLDPOM`** format, not JSON. `runs/2026-08-27-pommerman/design.md`
§Server → "Replay bytes (self-sufficient)" (lines 959–986) declares the phase-60 substitute: pipe the
bytes through the repo's `tools/replay_summary.py`, which emits one strict-UTF-8 JSON object, and
apply the check-4 predicates to that. That is what is done here.

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/0ad28a03-2b00-46d3-bd99-1202c2251c00.replay" -o /tmp/ep.replay
```

```
http 200 bytes 193038
sha256(/tmp/ep.replay) = f0b33b2032949b7dc8c18d0c346c82f6746944ff5f6eb658cbf82dc7439bcfc0
magic: b'COWLDPOM'
```

```bash
python3 /workspace/cogame-pommerman/tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
```

```
strict UTF-8 JSON: ok
```

```bash
jq -c '{protocol,gameVersion,seed,names,aliases,teams,policyKinds,tickCount,fallbacks,boardSize}' /tmp/ep.json
```

```json
{"protocol":"pommerman/v1","gameVersion":"1","seed":724915574,"names":["daveey","daveey-1","Baseline","Baseline (2)"],"aliases":["RED-1","BLUE-1","RED-2","BLUE-2"],"teams":["RED","BLUE","RED","BLUE"],"policyKinds":["llm","llm","scripted","scripted"],"tickCount":274,"fallbacks":11,"boardSize":11}
```

```bash
jq -c '.registrations' /tmp/ep.json
```

```json
[{"slot":1,"alias":"BLUE-1","team":"blue","policy":"prompt","kind":"llm","baseline":"sapper"},{"slot":0,"alias":"RED-1","team":"red","policy":"prompt","kind":"llm","baseline":"sapper"},{"slot":2,"alias":"RED-2","team":"red","policy":"camper","kind":"scripted","baseline":"camper"},{"slot":3,"alias":"BLUE-2","team":"blue","policy":"camper","kind":"scripted","baseline":"camper"}]
```

```bash
jq -c '.results' /tmp/ep.json
```

```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],"aliases":["RED-1","BLUE-1","RED-2","BLUE-2"],"teams":["RED","BLUE","RED","BLUE"],"scores":[-110,110,-110,110],"win":[false,true,false,true],"winner":"BLUE","reason":"complete","endRule":"tickCap","teamScores":[-110,110],"teamAlive":[1,2],"teamKills":[0,0],"teamWood":[14,4],"alive":[true,true,false,true],"kills":[0,0,0,0],"deaths":[0,0,1,0],"suicides":[0,0,0,0],"bombsPlaced":[9,3,0,0],"woodCleared":[14,4,0,0],"kicks":[0,0,0,0],"pickups":[4,1,0,1],"radioSent":[36,36,36,36],"finalTick":144,"turnsPlayed":36,"seed":724915574,"policyKinds":["llm","llm","scripted","scripted"],"llmTurns":[35,36,0,0],"fallbackTurns":[1,0,0,0],"ordersRejected":[2,3,0,0],"deadSeats":[false,false,false,false],"stopDetail":""}
```

```bash
jq -r '.protocol, .results.reason' /tmp/ep.json
jq -r '[.orders[]|select(.source=="llm")]|length' /tmp/ep.json
jq -r '.fallbacks' /tmp/ep.json
jq -r '[.radio[]|select(.a!=1 or .b!=1)]|length' /tmp/ep.json
```

```
pommerman/v1
complete
71
11
50
```

Per-seat decision provenance and verbs:

```bash
jq -c '[.orders[]|{slot,source}]|group_by(.slot)
       |map({slot:.[0].slot,n:length,srcs:(map(.source)|group_by(.)|map({s:.[0],n:length}))})' /tmp/ep.json
```

```json
[{"slot":0,"n":36,"srcs":[{"s":"fallback","n":1},{"s":"llm","n":35}]},{"slot":1,"n":36,"srcs":[{"s":"llm","n":36}]},{"slot":2,"n":36,"srcs":[{"s":"scripted","n":36}]},{"slot":3,"n":36,"srcs":[{"s":"scripted","n":36}]}]
```

```bash
jq -c '[.orders[]|{slot,verb}]|group_by(.slot)
       |map({slot:.[0].slot,verbs:(map(.verb)|group_by(.)|map({v:.[0],n:length}))})' /tmp/ep.json
```

```json
[{"slot":0,"verbs":[{"v":"bomb","n":3},{"v":"break","n":12},{"v":"go","n":12},{"v":"hide","n":1},{"v":"hunt","n":8}]},{"slot":1,"verbs":[{"v":"break","n":4},{"v":"go","n":8},{"v":"hide","n":19},{"v":"hunt","n":5}]},{"slot":2,"verbs":[{"v":"go","n":2},{"v":"hide","n":34}]},{"slot":3,"verbs":[{"v":"go","n":2},{"v":"hide","n":34}]}]
```

Radio (the emergent-language channel the coworld exists for):

```bash
jq -c '[.radio[]|{slot,a,b}]|group_by(.slot)
       |map({slot:.[0].slot,n:length,nontrivial:(map(select(.a!=1 or .b!=1))|length),
             distinct_pairs:(map("\(.a),\(.b)")|unique|length)})' /tmp/ep.json
```

```json
[{"slot":0,"n":36,"nontrivial":19,"distinct_pairs":7},{"slot":1,"n":36,"nontrivial":31,"distinct_pairs":4},{"slot":2,"n":36,"nontrivial":0,"distinct_pairs":1},{"slot":3,"n":36,"nontrivial":0,"distinct_pairs":1}]
```

Status: **TRUE** against the phase-60 predicates —
strict-UTF-8 JSON parse ok; `protocol == "pommerman/v1"` matches what the design pins (design.md
lines 970, 983, 1617); `results.reason == "complete"` (end rule `tickCap`, the ordinary
survive-to-the-cap ending, not the `deadline` exception); champion seats' decisions are non-scripted
and non-trivial — 71 of 72 champion orders are `source == "llm"` with five distinct real verbs
(`bomb`, `break`, `go`, `hide`, `hunt`), and exactly **1 of 72 (1.4 %)** was a fallback, a small
minority; the champion radio stream is non-trivial (19/36 and 31/36 pairs are not the null `[1,1]`,
7 and 4 distinct pairs) while the two camper Baselines send `[1,1]` every turn, exactly as their
manifest description says.

**Design-note clause NOT met, recorded rather than waived:** the design's own substitute (design.md
line 984) also asks for "non-zero `bombsPlaced` on every seat". `bombsPlaced == [9,3,0,0]` — the two
Baseline seats laid no bombs. Cause is visible above: the ladder seated the passive `camper` in
both filler seats and never `sapper`, and camper "only bombs an adjacent enemy or a wall it has two
safe exits from" (its manifest description). This is a seating/luck outcome, not a broken
engine — both Baselines did act on all 36 turns (`hide` × 34, `go` × 2). Flagged for the
coordinator/judge; it does not affect any predicate in `prompts/60-verify.md` check 4.

---

## 5. Hosted game log is clean — **FALSE**

```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs.raw
# decode the python b'…' byte-string reprs per container (ast.literal_eval), then grep the text
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.txt || echo CLEAN
```

`http 200`, 170119 bytes; decoded containers: `coworld-init-config` 0 chars, `bedrock-sidecar`
166107 chars, `game` 3497 chars, `worker` 0 chars.

Grep output — **not CLEAN**, 11 matching lines:

```
345:pommerman llm: seat 0 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
346:pommerman llm: seat 1 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
347:pommerman llm: seat 0 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
348:pommerman llm: seat 0 attempt 2 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
349:pommerman llm: seat 0 falling back to sapper (parse_error) on turn 21
350:pommerman llm: seat 1 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
351:pommerman llm: seat 0 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
352:pommerman llm: seat 1 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
353:pommerman llm: seat 1 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
354:pommerman llm: seat 1 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
355:pommerman llm: seat 1 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
```

The other three patterns do not appear: no `LLM provider is unavailable`, no
`cut off at max_tokens`, no `rejected`.

### The cause is this coworld's own attempt-1 deadline, not a platform outage

The Bedrock sidecar in the very same pod answered **every** call successfully:

```bash
python3 -c "…count/percentile the sidecar's latency_ms…"   # over the decoded log text
```

```
bedrock calls: 81
min 1810  p50 5991  p90 7672  max 9758
calls over attempt1Ms=8000: 7
ok:false count: 0
status_code!=200: 0
```

```bash
grep -cE 'ThrottlingException|Too many tokens|TooManyRequests' /tmp/logs.txt
```

```
0
```

So: 81/81 InvokeModel calls returned HTTP 200; **zero** throttling, zero `ok:false`. The design pins
`attempt1Ms = 8000` (design.md line 174, and the manifest `config_schema` default) while this
coworld's own prompt takes p50 ≈ 6.0 s and up to 9.8 s on `claude-haiku-4-5` — so ~7 of 81 calls
overrun the 8 s attempt-1 deadline, the game retries (`retryMs` 3000, `turnBudgetMs` 12000), and the
retry almost always wins. Net damage to play is small (1 of 72 champion turns actually fell back,
check 4) but the log is not CLEAN, which is what this check measures.

**Cross-check against another live LLM coworld, as the phase prompt requires before blaming or
excusing the platform** — `flatland`'s latest completed episode
(`ereq_6b35ad65-75d5-4c60-ad2e-7bdbb0bac1e6`, coworld `cow_f29f97b1-da55-4662-8dbc-cefde73f528d`,
fetched fresh at 20:29Z with the same headers):

```
flatland bedrock calls: 63
min 2514  p50 3722  p90 4706  max 8059
over 8000ms: 1
ThrottlingException / "Too many tokens": 0
```

Bedrock is healthy platform-wide right now (no repeat of the coins 2026-08-25 "Too many tokens per
day" 429s). Pommerman's calls are simply ~1.6× slower than flatland's — consistent with its larger
per-turn prompt — so **the documented platform-capacity exception does not apply** and this is a
pommerman tuning defect. Round 2's log (`ereq_20741863-24b7-4aa8-be96-ffde53f3cd26`, also fetched
this run) shows the identical pattern: 10 `falling back` lines, 80/80 sidecar calls HTTP 200,
p50 6192 ms / max 11847 ms. It reproduces; it is not a one-off.

Status: **FALSE** — 11 lines match `falling back` in the hosted game log; no documented exception
covers them. Suggested remedy for the coordinator (verifier does not edit code): raise `attempt1Ms`
from 8000 to ≥ 12000 (with `turnBudgetMs` raised to match) and re-release, or demote the retry
notice below the log line the check greps.

---

## 6. Public page uses the static replay path — **TRUE**

**Source used: the API fallback**, because the raw-HTML grep found nothing (the page is
client-rendered for the iframe, exactly as `playbooks/observatory-api.md` §Featured match records).
Both sources are shown.

*(a) The raw-HTML grep — no match, therefore unknown, not a failure:*

```bash
curl -sS "https://softmax.com/pommerman" | grep -o '<iframe[^>]*src="[^"]*"'
```

```
http 200 bytes 699095
(no match — page is client-rendered)
```

*(b) The featured match, server-rendered into the page's SSR payload at `state.playlist[0]`
(unescaped for readability; fetched 20:35Z):*

```json
"playlist":[{"episodeId":"5c24ae8e-557b-4737-910d-5b20c713b5c3","coworldId":"cow_224b5627-9e46-46e5-ad55-1b2692cc503b","coworldName":"pommerman","coworldVersion":"0.1.0","replayUrl":"https://softmax-public.s3.amazonaws.com/replays/0ad28a03-2b00-46d3-bd99-1202c2251c00.replay","finishedAt":"2026-08-27T20:32:37.848538Z","roundNumber":3,"episodeNumber":1,"code":"pommerman.r3.e1","matchup":{"divisionId":"div_7c2c9172-a9dd-449b-8911-e5d072c11d25","divisionName":"Competition","first":{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":1001.4695015289755,"score_label":"MMR","score_value_type":"integer","rounds_played":2,"episode_wins":1,"episodes_played":null,"win_rate":0.5,"policy_label":"pommerman-cornerman:v1","recent_rounds":null},"second":{"rank":2,"player_id":
```

A featured match **is** present (`pommerman.r3.e1`, the round-3 episode, both ranked players in the
matchup) — so the "fewer than two ranked players" failure does not apply.

*(c) The iframe `src`, from the call the page's own JS makes:*

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_224b5627-9e46-46e5-ad55-1b2692cc503b",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/0ad28a03-2b00-46d3-bd99-1202c2251c00.replay"}'
```

`http 200`

```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_224b5627-9e46-46e5-ad55-1b2692cc503b/sha256%3Ac4073d59947d784d5b98cd1d213cba17519809f64cb100b1e64855ce58757343/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F0ad28a03-2b00-46d3-bd99-1202c2251c00.replay&v=2",
  "ready": true
}
```

```bash
curl -sS -o /dev/null -w "%{http_code}\n" "$viewer_url"
```

```
200
```

Status: **TRUE** — the path is
`/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`, with `<cow_id>` =
`cow_224b5627-9e46-46e5-ad55-1b2692cc503b` and `<sha>` = the URL-encoded manifest hash
`sha256:c4073d59947d784d5b98cd1d213cba17519809f64cb100b1e64855ce58757343`, which matches
`STATE.coworld.manifest_sha` exactly. `ready: true`, and the URL returns 200. It is **not** a
`/client/replay` pod URL.

---

## 7. Certification declared the static bundle — **TRUE**

Source read: **the committed `runs/2026-08-27-pommerman/release-result.json`** (phase 40's artifact,
committed in `74916fc 40 pommerman: release 0.1.0 canonical+certified; phase -> 50`). No
re-download from the release run was needed.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-27-pommerman/release-result.json
```

```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE** — the output contains the required string
`Replay liveness: skipped (static replay bundle declared`.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

*(a) Dispatch.* Dispatched at **2026-08-27T20:36:47Z** against the exact iframe `src` from check 6:

```bash
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
  | jq -r 'sort_by(.createdAt)|reverse|.[0:5][]|[.databaseId,.createdAt,.status,.event]|@tsv'
```

```
33114175789	2026-08-27T20:36:49Z	in_progress	workflow_dispatch
33113882071	2026-08-27T20:33:16Z	completed	workflow_dispatch
33106609970	2026-08-27T19:03:57Z	completed	workflow_dispatch
```

The run picked by sort-by-createdAt, **33114175789**, was created 2 s after the dispatch — it is
this verifier's run, not an inherited one.

```bash
gh run watch 33114175789 -R Metta-AI/coworld-builder --exit-status   # -> exit 0 (green), 47s
gh run download 33114175789 -R Metta-AI/coworld-builder -n viewer-check \
  -D runs/2026-08-27-pommerman/viewer-check
```

```
✓ viewer-check in 47s (ID 98664434063)
runs/2026-08-27-pommerman/viewer-check/
  smoke-stderr.txt        0 bytes
  smoke-stdout.txt      703 bytes
  viewer-smoke.json    1499 bytes
  viewer-smoke.png   450667 bytes
```

*(b) Readouts.* `runs/2026-08-27-pommerman/viewer-check/viewer-smoke.json`, verbatim:

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' …/viewer-smoke.json
```

```json
{"loaded":true,"ms":1951,"clock":"turn 1/36 TICK 0/144 · WALLS CLOSE IN 96","scorebug":"RED DAVEEY · BASELINE RED-11/2 RED-21/2 ALIVE 2 0 ≋ 1·1 ↯ turn 1/36 TICK 0/144 · WALLS CLOSE IN 96 BLUE DAVEEY-1 · BASELINE (2) BLUE-11/2 BLUE-21/2 ALIVE 2 0 ≋ 1·1","feed_lines":0}
```

```bash
jq -c '.signals' …/viewer-smoke.json
```

```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' …/viewer-smoke.json
```

```
no failure
```

```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' …/viewer-smoke.json
```

| scrub | clock readout |
|---|---|
| 0 % | `turn 1/36 TICK 0/144 · WALLS CLOSE IN 96` |
| 50 % | `turn 31/36 TICK 123/144 · THE ARENA IS THE MIDDLE 5X5` |
| 100 % | `turn 36/36 TICK 144/144 · THE ARENA IS THE MIDDLE 5X5` |

Also recorded by the harness: `canvas_text: {"total":0,"outside":0,"ellipsized":0,"never_inside":0}`
(this viewer paints its text as DOM, not canvas fillText, so the canvas-text overflow probe has
nothing to measure — the same reading the r1 review already adjudicated); `console_tail: []`.

**Verdict on the two gates:** `loaded: true` (via `data-replay-loaded="true"`, in 1951 ms) **and**
the three clock readouts all differ (tick 0 → 123 → 144, turn 1 → 31 → 36). Item 8 is **TRUE**.

*(c) What the viewer was asked to draw* — ordered excerpts from the replay summary of the same
episode (`/tmp/ep.json`, check 4), so the picture and the record can be reconciled:

```bash
jq -r '.directives[]|select(.turn<=3)|[.turn,.alias,.source,.verb,(.arg|tostring),(.radio|tostring),(.say|.[0:60])]|@tsv' /tmp/ep.json
```

```
1	RED-1	llm	break	null	[1,1]	Starting break sequence to build lanes and seek power-ups
1	BLUE-1	llm	break	null	[1,1]	Start breaking wood in SW quadrant
1	RED-2	scripted	hide	null	[1,1]	
1	BLUE-2	scripted	hide	null	[1,1]	
2	RED-1	llm	break	null	[1,1]	Breaking west, searching for power-ups. No threats yet.
2	BLUE-1	llm	break	null	[2,1]	Turn 2: Breaking wood in SE quadrant, no close enemies. Radi
3	RED-1	llm	go	{"x":2,"y":1}	[1,1]	Turn 3: Retreating from bomb, continuing break sequence. Col
3	BLUE-1	llm	break	null	[1,1]	Turn 3: Retreating from bomb, continuing SE break
```

```bash
jq -r '.directives[]|select(.turn>=19 and .turn<=22)|…|@tsv' /tmp/ep.json     # middle
```

```
19	RED-1	llm	break	null	[1,5]	In middle zone, continuing wood control. Bomb detonates next
19	BLUE-1	llm	hide	null	[2,1]	Phase 2: both enemies distant, holding position at corridor 
20	RED-1	llm	go	{"x":5,"y":5}	[5,1]	Moving to center (5,5). Partner must reach 5x5 middle before
20	BLUE-1	llm	hide	null	[2,1]	Turn 20: Both reds distant. Holding right corridor. One bomb
21	RED-1	fallback	bomb	null	[2,1]	
21	BLUE-1	llm	hide	null	[2,1]	Phase 2: defending top-right. Both reds distant. Partner sta
22	RED-1	llm	go	{"x":5,"y":5}	[1,1]	Moving to middle 5x5. Partner must move inward from (9,9) im
22	BLUE-1	llm	hide	null	[2,1]	Safe at (9,1), both enemies >5 cells away. Holding position.
```

```bash
jq -r '.directives[]|select(.turn>=34)|…|@tsv' /tmp/ep.json                   # late
```

```
34	RED-1	llm	bomb	null	[3,5]	Bombing BLUE-1 on row 3 - aligned, in range.
34	BLUE-1	llm	hunt	RED-1	[2,2]	Hunt RED-1 in final ring, danger clear
35	RED-1	llm	hide	null	[8,5]	Waiting out bomb fuse, then hunt remaining enemies.
35	BLUE-1	llm	hide	null	[2,1]	End game. Walls closing. 8 ticks left. Both alive but RED-2 
36	RED-1	llm	go	{"x":4,"y":3}	[5,5]	Moving onto bomb for detonation; BLUE-1 trapped outside, BLU
36	BLUE-1	llm	hunt	RED-1	[2,2]	RED-1 at (3,4) with bomb fuse 1. Closing in from (7,3). Fina
```

```bash
jq -r '.results' /tmp/ep.json     # pasted in full in check 4
```
→ `winner: BLUE`, `reason: complete`, `endRule: tickCap`, `scores [-110,110,-110,110]`,
`teamAlive [1,2]`, `teamWood [14,4]`, `bombsPlaced [9,3,0,0]`, `finalTick 144`.

### Spectator-judgment paragraph

**The picture is legible and it is unmistakably this game.** `viewer-smoke.png` (1280 × 800, taken at
the 100 % scrub position) shows a rendered 11 × 11 arena of wood-crate and stone tiles with bomber
sprites still on the board, a red banner across the top of the field reading
`THE WALLS CLOSE IN — RING 2`, and the endcard laid over the middle: **`BLUE TAKES IT — AHEAD 2-1 AT
TICK 144`**, a `SCORE −110 / +110` plate, and the line `end rule: tickCap · 144 ticks · wood 14-4 ·
complete`. Beneath it sit the two team plates — RED with `RED-1 · DAVEEY  kills 0  bombs 9  wood 14
radio 5·5` and `RED-2 · BASELINE  0 / 0 / 0 / 1·1`, `BOMBERS LEFT 1`; BLUE with `BLUE-1 · DAVEE…
0 / 3 / 4 / 2·2` and `BLUE-2 · BASELI…  0 / 0 / 0 / 1·1`, `BOMBERS LEFT 2`. Every one of those
numbers is the replay's own `results` object drawn on screen: `bombsPlaced [9,3,0,0]`, `woodCleared
[14,4,0,0]`, `kills [0,0,0,0]`, `teamAlive [1,2]`, `teamScores [-110,110]`, `endRule tickCap`,
`reason complete`, `finalTick 144` — and the `≋ 5·5` / `≋ 2·2` radio chips match the last radio pair
each champion seat actually sent (`jq '[.radio[]]|group_by(.slot)|map(...last...)'` →
`[{slot 0: 5,5},{slot 1: 2,2},{slot 2: 1,1},{slot 3: 1,1}]`). The picture and the record agree; the
scorebug says who is winning and the endcard says why.

**It is the starter's chrome, not a rewrite.** The transport strip along the bottom carries the
coworld-ctf/paintbot lineage byte for byte in shape: restart · step-back · pause · `+5s` · play ·
loop · fast-forward, then a `spoilers` toggle, then the outcome readout `BLUE WINS  234 / 234`, then
the speed ladder `1× 2× 3× 4× 8× 16×`. Under it is the scrubber with the beat-marker ticks
(orange, at the firstblood/collapse/fallback/end beats the design enumerates) and the momentum graph
labelled `BOMBERS STANDING`, filled blue for the trailing segment. Top-left and top-right are the
two scorebug plates (`RED DAVEE…` / `DAVE…` with per-bomber ammo·blast chips, `ALIVE`, kill count and
the `≋` radio chip), the centred clock `turn 36/36` over `TICK 144/144 · THE ARENA IS THE MIDDLE
5X5`, and the `DANGER` plate at top-right. This is the paintbot/raid/hive family, adapted — not the
cogame-gridlock failure mode of a lookalike sharing only element ids.

**It moves.** The three scrub readouts are three different game states (tick 0 → 123 → 144, turn
1 → 31 → 36), and the 50 % readout's phase label has already flipped from `WALLS CLOSE IN 96` to
`THE ARENA IS THE MIDDLE 5X5`, which is the ring collapse at ticks 96/120 shown as it happens. So
this is a replay, not a screenshot.

Three honest observations for the coordinator, none of them a check failure:

1. **`feed_lines: 0`** — the harness probes the feed at load, i.e. at turn 1/36 tick 0, before any
   directive has been spoken, so the count is legitimately zero at that instant rather than a dead
   feed. But it means *this run has no fetched evidence that the say/feed panel ever populates.* The
   screenshot is at 100 %, where the endcard covers the feed area, so it cannot settle the question
   either. Worth a look in phase 30 or a `viewer-check` probe at 50 % next time; the replay
   certainly has the content (36 turns × 2 champion `say` lines, quoted above).
2. **Names are truncated in the chrome** — `DAVEE…`, `BLUE-1 · DAVEE…`, `RED-2 · BASELINE`,
   `BLUE-2 · BASELI…`. Readable, but at 1280 px the two champions' plates both read `DAVEE…` in the
   top scorebug, so a spectator cannot tell `daveey` from `daveey-1` from the top strip alone (the
   endcard table does disambiguate). Legibility note, not a defect.
3. **No kick in this episode.** `results.kicks == [0,0,0,0]`, so — exactly as the builder warned at
   phase 20 about the CI smoke — the kick beat and its viewer marker remain unexercised by any real
   episode to date. Nothing in the rendered evidence contradicts the kick path; it simply has never
   fired in production.

The board itself is dimmed under the endcard overlay in this frame, which is the designed endcard
behaviour (`endcard var(--band)` + seek-to-dismiss), not an empty render: the wood tiles, the two
surviving bombers and the ring-collapse banner are all still visible through it.

---

## Summary table

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 2 and 3 |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** |
| 3 | Latest round's episode request completed with replay_url + right participants | **TRUE** |
| 4 | Replay bytes valid, protocol match, `complete`, champion decisions real | **TRUE** (one design-note clause unmet: `bombsPlaced` 0 on the two camper Baselines) |
| 5 | Hosted game log CLEAN | **FALSE** — 11 `falling back` lines; attempt1Ms=8000 too tight for this coworld's own prompt; Bedrock verified healthy |
| 6 | Public page uses the static replay path, featured match present | **TRUE** |
| 7 | Certification declared the static bundle | **TRUE** |
| 8 | Viewer executed: `loaded:true` + three differing clocks | **TRUE** — run 33114175789 |
