# VERIFY — sumo-traffic-signals   (2026-08-28T18:17Z)

Verdict: **all-true** (8 / 8)

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | TRUE |
| 2 | Both champions ranked, fillers absent | TRUE |
| 3 | Latest round's episode request completed with a replay | TRUE |
| 4 | Replay bytes valid and show the game (design-declared substitute) | TRUE |
| 5 | Hosted game log clean | TRUE |
| 6 | Public page uses the static replay path, featured match present | TRUE |
| 7 | Certification declared the static bundle | TRUE |
| 8 | Spectator judgment — viewer EXECUTED in CI, `loaded:true`, clock advances | TRUE |

Run facts: league `league_0a4b0ef0-557c-4c54-b439-788cede68a73`, division
`div_013d13d5-8ef6-430d-bc77-592c81a0aa5a`, coworld `cow_ec8a6c5d-d31e-4c81-9b8d-2f5d404c1944`
v0.1.0, manifest `sha256:77577277184749d6d02741c62a62de8109ac4b6c2b752ac788970570e3653298`.

All calls used `-H "Authorization: Bearer $SOFTMAX_TOKEN"` and `-H "User-Agent: coworld-builder/1.0"`;
where noted, additionally `-H "X-Use-Elevated-Privileges: true"`. Header **values** are never printed
here. `BASE=https://softmax.com/api/observatory/v2`.

Every item below was fetched fresh during this verification pass (17:46–18:17Z on 2026-08-28), with
the two documented exceptions: item 7 (reads the committed `release-result.json` from phase 40) and
item 8's rendered evidence (downloaded from the `viewer-check.yml` run **this pass dispatched**,
33198007349).

---

## 0. Precondition — when the fillers were set (context for item 1)

```
GET $BASE/leagues/league_0a4b0ef0-557c-4c54-b439-788cede68a73/filler-policies
  headers: Authorization, User-Agent, X-Use-Elevated-Privileges
HTTP 200
```
```json
{
  "filler_policy_versions": [
    {
      "policy_version_id": "f0398934-b4f8-4630-935f-911242fe31da",
      "policy_id": "af08bf0f-4648-487c-a680-4e61720efca5",
      "policy_name": "signals-greedy",
      "version": 1,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "display_name": null
    },
    {
      "policy_version_id": "9ccb76ef-ea5a-4c7a-bbc7-c9ebabcdf8c3",
      "policy_id": "02d2bea7-f503-4811-b1d5-bd09d90f9e82",
      "policy_name": "signals-fixedcycle",
      "version": 1,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "display_name": null
    }
  ]
}
```

`log.md` records the filler POST at `2026-08-28T17:45:17Z 50 fillers POST 200: signals-greedy
f0398934 + signals-fixedcycle 9ccb76ef (neither champion); unpause 200; trigger 200`, i.e. the
fillers were registered at ~17:44Z — **after** round 1 was created (17:44:00.426Z) and **before**
round 2 was created (17:44:23.140Z). The independent, fetched proof that fillers were live for
rounds 2 and 3 is item 3's `participants`, which seat `signals-fixedcycle` twice with
`"is_filler": true`, and item 4's replay `names` array, which renders those seats as
`"Baseline"` / `"Baseline (2)"`.

---

## 1. ≥2 completed rounds after the fillers were set

```
GET $BASE/rounds?league_id=league_0a4b0ef0-557c-4c54-b439-788cede68a73&limit=20
  headers: Authorization, User-Agent
HTTP 200
```

Response (field-selected with
`jq 'if type=="array" then . else .entries end | map({id,round_number,status,error,created_at,completed_at,entrants:(.round_config.entrant_attributions)})'`;
the body carries these fields verbatim):

```json
[
  {
    "id": "round_9b109538-0b2b-49b5-900c-eecc06c07195",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T17:59:23.490457Z",
    "completed_at": "2026-08-28T18:06:09.079927Z",
    "entrants": [
      {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
       "policy_version_id": "b3c84416-c4d3-4463-b9c3-2f6eb60dc67e",
       "league_policy_membership_id": "lpm_39fcc5f8-e3ef-457a-93a2-ea136370f34c"},
      {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
       "policy_version_id": "3613691b-1e83-4cff-978d-3623362d46d7",
       "league_policy_membership_id": "lpm_916b827b-9adc-4f8a-83d6-a5bf379874c4"}
    ]
  },
  {
    "id": "round_f5180f54-e557-442c-bdcc-29d44a2f0b06",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T17:44:23.140304Z",
    "completed_at": "2026-08-28T17:51:03.878390Z",
    "entrants": [
      {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
       "policy_version_id": "b3c84416-c4d3-4463-b9c3-2f6eb60dc67e",
       "league_policy_membership_id": "lpm_39fcc5f8-e3ef-457a-93a2-ea136370f34c"},
      {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
       "policy_version_id": "3613691b-1e83-4cff-978d-3623362d46d7",
       "league_policy_membership_id": "lpm_916b827b-9adc-4f8a-83d6-a5bf379874c4"}
    ]
  },
  {
    "id": "round_22e4273c-cb24-4308-9218-95c55dac45ee",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-28T17:44:00.426580Z",
    "completed_at": "2026-08-28T17:44:00.693058Z",
    "entrants": [
      {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
       "policy_version_id": "b3c84416-c4d3-4463-b9c3-2f6eb60dc67e",
       "league_policy_membership_id": "lpm_39fcc5f8-e3ef-457a-93a2-ea136370f34c"},
      {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
       "policy_version_id": "3613691b-1e83-4cff-978d-3623362d46d7",
       "league_policy_membership_id": "lpm_916b827b-9adc-4f8a-83d6-a5bf379874c4"}
    ]
  }
]
```

```
$ jq -r 'if type=="array" then . else .entries end | [.[]|select(.status=="completed")]|length'
2
```

Round 1's `error`, verbatim: `Temporal RoundWorkflow failed before settling the round.` It was
created at 17:44:00.426Z and failed 267 ms later, i.e. at placement time and **before** the filler
POST — the documented `playbooks/observatory-api.md` §6 pattern (*"A `trigger-round` issued before
any filler exists fails instantly with `Temporal RoundWorkflow failed before settling the round`"*).
It is excluded, not counted.

**Status: TRUE** — rounds **2** (completed 2026-08-28T17:51:03.878390Z) and **3** (completed
2026-08-28T18:06:09.079927Z) are `completed`, both `round_number` ≥ 2 and both created after the
fillers were registered (~17:44Z). No round is `discarded`.

Polls taken while waiting (heartbeat written to Asana `1217748424048134` on task
`1217950132700140` at each, HTTP 200 each time):

| Poll (UTC) | rounds |
|---|---|
| 17:46:21 | 2 pending, 1 failed |
| 17:51:29 | 2 **completed**, 1 failed |
| 17:57:19 | 2 completed, 1 failed |
| 18:02:12 | 3 pending, 2 completed, 1 failed |
| 18:07:14 | 3 **completed**, 2 completed, 1 failed |

Elapsed against the 75-minute bound at the point both rounds were in hand: **21 minutes**.

---

## 2. Both champions ranked; fillers absent

```
GET $BASE/divisions/div_013d13d5-8ef6-430d-bc77-592c81a0aa5a/leaderboard
  headers: Authorization, User-Agent
HTTP 200
```
```json
[
  {
    "rank": 1,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 1016.0,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 1.0,
    "episodes_played": null,
    "win_rate": 0.5,
    "policy_label": "signals-greenwave:v1",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 984.0,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 0.0,
    "episodes_played": null,
    "win_rate": 0.0,
    "policy_label": "signals-gatekeeper:v1",
    "recent_rounds": null
  }
]
```

```
$ jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
1	daveey	signals-greenwave:v1	1016.0	2	1.0
2	daveey-1	signals-gatekeeper:v1	984.0	2	0.0
```

**Status: TRUE** — `daveey` (`signals-greenwave:v1`, rank 1, MMR 1016, `rounds_played` 2) and
`daveey-1` (`signals-gatekeeper:v1`, rank 2, MMR 984, `rounds_played` 2) are both ranked with
`rounds_played ≥ 1`. The leaderboard is a two-row bare list: neither filler (`signals-greedy:v1`,
`signals-fixedcycle:v1`) appears at all, which satisfies "fillers absent **or** `policy_label`
starting `Baseline`" by the absent branch.

---

## 3. Latest completed round's episode request completed with a replay

Latest completed round = `round_9b109538-0b2b-49b5-900c-eecc06c07195` (round 3), from item 1.

```
GET $BASE/rounds/round_9b109538-0b2b-49b5-900c-eecc06c07195/episode-requests
  headers: Authorization, User-Agent          # nested route; the flat ?round_id= route is 405
HTTP 200
```
```json
{"entries": [{"id": "ereq_75e2c1eb-1a8d-498e-ae67-26edcd34e6fd", "status": "completed",
              "created_at": "2026-08-28T17:59:23.813065Z"}]}
```

```
GET $BASE/episode-requests/ereq_75e2c1eb-1a8d-498e-ae67-26edcd34e6fd
  headers: Authorization, User-Agent
HTTP 200
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/4c2c2a45-861a-4bfb-b275-adcac8a11cf7.replay",
  "participants": [
    {"position": 0, "kind": "policy",
     "policy_version_id": "b3c84416-c4d3-4463-b9c3-2f6eb60dc67e",
     "policy_id": "0a614187-c8aa-4bfa-933e-7e986b7b6899",
     "policy_name": "signals-greenwave", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "is_filler": false, "is_seed": false},
    {"position": 1, "kind": "policy",
     "policy_version_id": "3613691b-1e83-4cff-978d-3623362d46d7",
     "policy_id": "e8bdcd35-e2be-4ade-aa37-198cb1b622f8",
     "policy_name": "signals-gatekeeper", "version": 1,
     "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
     "is_filler": false, "is_seed": false},
    {"position": 2, "kind": "policy",
     "policy_version_id": "9ccb76ef-ea5a-4c7a-bbc7-c9ebabcdf8c3",
     "policy_id": "02d2bea7-f503-4811-b1d5-bd09d90f9e82",
     "policy_name": "signals-fixedcycle", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "is_filler": true, "is_seed": false},
    {"position": 3, "kind": "policy",
     "policy_version_id": "9ccb76ef-ea5a-4c7a-bbc7-c9ebabcdf8c3",
     "policy_id": "02d2bea7-f503-4811-b1d5-bd09d90f9e82",
     "policy_name": "signals-fixedcycle", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "is_filler": true, "is_seed": false}
  ],
  "participant_scores": [
    {"position": 0, "score": 133759850.0},
    {"position": 1, "score": 133759820.0},
    {"position": 2, "score": 133759870.0},
    {"position": 3, "score": 133759880.0}
  ]
}
```

**Status: TRUE** — `status == "completed"`; `replay_url` non-null
(`https://softmax-public.s3.amazonaws.com/replays/4c2c2a45-861a-4bfb-b275-adcac8a11cf7.replay`);
`participants` names both champions (`daveey` at position 0 with `signals-greenwave` v1,
`daveey-1` at position 1 with `signals-gatekeeper` v1, both `is_filler: false`) and the two
scripted filler seats at positions 2 and 3 with `is_filler: true`, `policy_version_id`
`9ccb76ef-…` — a filler id from item 0, distinct from either champion's. The API surfaces fillers
here by their policy name; the `Baseline (N)` renaming is what the **game and viewer** receive, and
it is visible in item 4's replay `names` (`["daveey","daveey-1","Baseline","Baseline (2)"]`) and in
the item-8 screenshot.

Cross-check that this is the same round: the SSR playlist entry in item 6 gives
`"code":"sumo-traffic-signals.r3.e1"`,
`"inspectUrl":"/observatory/v2?tab=overview&detail=episode-request:ereq_75e2c1eb-1a8d-498e-ae67-26edcd34e6fd"`.

---

## 4. Replay bytes are valid and show the game

**Documented substitute in force.** This coworld's replay is the coworld-ctf starter's **binary
`COWLDSIG`** format, not JSON. `runs/2026-08-28-sumo-traffic-signals/design.md`
§*Server → Replay bytes (self-sufficient)* (lines 1114–1139) declares that format and pins the
phase-60 substitute for SPEC check 4 verbatim:

> The replay stays the starter's **binary `COWLDSIG`** format — the static wasm viewer parses
> exactly this […] **The phase-60 substitute for SPEC §Definition of done check 4:**
> `curl -sSL "$replay_url" -o /tmp/ep.replay` / `python3 tools/replay_summary.py /tmp/ep.replay >
> /tmp/ep.json` / `jq -e . /tmp/ep.json` / `jq -r '.protocol, .results.reason, .results.throughput,
> .results.greenWaves' /tmp/ep.json` / `jq -r '[.orders[]|select(.source=="llm")]|length,
> .fallbacks, (.radio|length)' /tmp/ep.json`.
> Require `protocol == "signals/v1"`, `results.reason == "complete"` (or the declared-acceptable
> `deadline`), `results.throughput > 0`, and the champion seats' orders with `source == "llm"`, real
> verbs (including at least one `wave`) and non-empty radio lines — not all fallbacks.

`tools/replay_summary.py` ships in the coworld repo and is Python-3-stdlib only. It was run from a
fresh clone at `/workspace/scratch/cogame-sumo-traffic-signals` (`git pull` → `Already up to date.`,
HEAD `e20601a`, the sha phase 30 certified).

### 4a. Fetch and confirm the container format

```
GET https://softmax-public.s3.amazonaws.com/replays/4c2c2a45-861a-4bfb-b275-adcac8a11cf7.replay
HTTP 200  bytes=88687
```
```
$ python3 -c "d=open('/tmp/ep.replay','rb').read(); print('magic:', d[:8]); print('size:', len(d))"
magic: b'COWLDSIG'
size: 88687

$ jq -e . /tmp/ep.replay >/dev/null 2>&1 && echo "raw is JSON" || echo "raw is NOT JSON"
raw is NOT JSON        # binary COWLDSIG, as design.md declares
```

### 4b. Strict UTF-8 JSON under the declared decoder

```
$ python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
$ jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok
```

### 4c. Protocol, reason, throughput

```
$ jq -r '.protocol, .results.reason, .results.throughput, .results.greenWaves' /tmp/ep.json
signals/v1
complete
134
0
```

`protocol == "signals/v1"` matches the manifest's declared protocol. `results.reason ==
"complete"` — the clean end, so the `deadline` escape hatch is **not** used. `results.throughput
= 134 > 0`.

### 4d. Champion-seat decisions are real LLM output, not fallbacks

```
$ jq -c '{names,aliases,tickCount,radio_lines:(.radio|length),orders_total:(.orders|length),
          orders_llm:([.orders[]|select(.source=="llm")]|length),
          fallback_records:.fallbacks,budgetGuards}' /tmp/ep.json
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],"aliases":["Alpha","Beta","Gamma","Delta"],
 "tickCount":256,"radio_lines":64,"orders_total":1024,"orders_llm":256,
 "fallback_records":3,"budgetGuards":0}

$ jq -r '[.orders[]|select(.source=="llm")]|group_by([.slot,.verb])
         |map({slot:.[0].slot,verb:.[0].verb,n:length})|.[]|"slot=\(.slot) verb=\(.verb) n=\(.n)"'
slot=0 verb=auto n=10
slot=0 verb=hold n=47
slot=0 verb=phase n=68
slot=0 verb=wave n=3
slot=1 verb=auto n=4
slot=1 verb=hold n=41
slot=1 verb=phase n=83

$ jq -c '[.orders[]|select(.source=="llm" and .verb=="wave")]' /tmp/ep.json
[{"at":"A2","verb":"wave","phase":"EWG","delay":5,"source":"llm","turn":1,"slot":0},
 {"at":"A2","verb":"wave","phase":"EWG","delay":5,"source":"llm","turn":2,"slot":0},
 {"at":"A2","verb":"wave","phase":"EWG","delay":5,"source":"llm","turn":17,"slot":0}]
```

Slot 0 = `greenwave` / `daveey` / Alpha / NW; slot 1 = `gatekeeper` / `daveey-1` / Beta / NE.
Each champion seat issued **128** `source=="llm"` orders (32 turns × 4 intersections), spanning
all four verbs the design defines (`phase`, `hold`, `auto`, `wave`), including **3 `wave` orders
with a non-zero `delay` of 5 ticks** — the green-wave verb the whole game is about.

Non-empty radio, first three and last two of 64 lines:

```
$ jq -r '.radio[0:3][]' /tmp/ep.json
Column 1 eastbound is my wave: A1 at +0, A2 at +6
Beta starting. All exits empty, running auto. Will coordinate green waves eastbound on row A and B at standard offsets.
Alpha wave avenue: A1-A2 eastbound at +0,+5. Standard offsets maintained.

$ jq -r '.radio[-2:][]' /tmp/ep.json
A1 forcing EWL for W (52t blocked); A2 holding, A2>A3 full. B2 forcing EWL for S (25t blocked).
Beta: A3→EWG to drain W/E queues. A4→NSL (N blocked 60t, forced override imminent). B3→EWL to clear W queue (30t blocked)…
```

Fallbacks are a small minority and, in fact, cost **zero** turns:

```
$ jq -r '.fallbacks' /tmp/ep.json
3
$ jq -c '.results|{llmTurns,fallbackTurns,ordersRejected,deadSeats}' /tmp/ep.json
{"llmTurns":[32,32,0,0],"fallbackTurns":[0,0,0,0],"ordersRejected":[1,0,0,0],
 "deadSeats":[false,false,false,false]}
```

The three `k:"fallback"` records, verbatim:

```json
{"k":"fallback","turn":4,"slot":1,"attempt":1,"cause":"timeout","detail":"llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke"}
{"k":"fallback","turn":18,"slot":1,"attempt":1,"cause":"timeout","detail":"llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke"}
{"k":"fallback","turn":19,"slot":0,"attempt":1,"cause":"timeout","detail":"llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke"}
```

All three are `"attempt": 1` retry notices; `design.md` line 534–535 pins that reading (*"The
attempt-1 notice says **`will retry`**; only a genuine second failure logs **`falling back`**"*).
`results.fallbackTurns == [0,0,0,0]` and `llmTurns == [32,32,0,0]` prove every one of the 64
champion turns was decided by the model: 3 retried transport timeouts out of 64 turns (4.7 %), zero
turns actually degraded.

Full `results`:

```json
{"names":["greenwave","gatekeeper","fixedcycle","fixedcycle"],"aliases":["Alpha","Beta","Gamma","Delta"],
 "quadrants":["NW","NE","SW","SE"],"scores":[133759850,133759820,133759870,133759880],
 "win":[false,false,false,false],"winner":null,"reason":"complete","endRule":"fullPeriod",
 "throughput":134,"parThroughput":260,"demandGenerated":422,"rejected":27,"networkWaitTicks":48093,
 "seatWaitTicks":[12517,14785,10832,9959],"netWaitK":240,"seatWaitK":[15,18,13,12],
 "served":[24,24,42,44],"travelTicksTotal":15371,"stopsTotal":877,"greenWaves":0,"spillbacks":73,
 "spillbackTicks":247,"gridlocks":0,"gridlockTicks":0,"longestGridlockTicks":0,"starvations":39,
 "deferredSwitches":10,"phaseChanges":[66,80,124,123],"finalTick":256,"turnsPlayed":32,
 "seed":1370318455,"variant":"grid4x4","policyKinds":["llm","llm","scripted","scripted"],
 "crossPlay":true,"llmTurns":[32,32,0,0],"fallbackTurns":[0,0,0,0],"ordersRejected":[1,0,0,0],
 "deadSeats":[false,false,false,false],"stopDetail":""}
```

**Status: TRUE** — under the design-declared substitute: decoder output is strict UTF-8 JSON;
`protocol == "signals/v1"`; `results.reason == "complete"` (no `deadline` exception needed);
`results.throughput == 134 > 0`; both champion seats issued 128 `source=="llm"` orders each across
four verbs including 3 `wave` orders; 64 non-empty radio lines; 3 attempt-1 fallback notices with
`fallbackTurns == [0,0,0,0]`, i.e. not all fallbacks and not even a minority — none.

---

## 5. Hosted game log is clean

```
GET $BASE/episode-requests/ereq_75e2c1eb-1a8d-498e-ae67-26edcd34e6fd/artifacts/logs
  headers: Authorization, User-Agent, X-Use-Elevated-Privileges
HTTP 200  bytes=141557
```

Body is python `b'…'` byte-string reprs under `===== container: … =====` headers; decoded per repr
with `ast.literal_eval` before grepping (per `playbooks/observatory-api.md` §10). 314 decoded lines,
4 containers: `coworld-init-config`, `bedrock-sidecar`, `game`, `worker`.

```
$ grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.txt
311:signals results: {"names":["greenwave","gatekeeper","fixedcycle","fixedcycle"],…,"reason":"complete",…,"rejected":27,…,"llmTurns":[32,32,0,0],"fallbackTurns":[0,0,0,0],"ordersRejected":[1,0,0,0],"deadSeats":[false,false,false,false],"stopDetail":""}
```

Per-phrase counts over the decoded text:

| phrase | hits |
|---|---|
| `falling back` | **0** |
| `LLM provider is unavailable` | **0** |
| `cut off at max_tokens` | **0** |
| `rejected` | 1 |

The single `rejected` hit is line 311, the game's own `signals results:` JSON — it is the coworld's
results keys `"rejected":27` (cars turned away at a full gate queue) and `"ordersRejected":[1,0,0,0]`
(malformed-order counter). Both are declared game vocabulary in `design.md` §Scoring/§Results, not
an LLM failure. No hit lies in an LLM-transport or provider line.

The retry notices that *did* occur, verbatim from the `game` container, matching the three
`k:"fallback"` records in item 4 one-for-one:

```
303:signals llm: seat 1 attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
305:signals llm: seat 1 attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
306:signals llm: seat 0 attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
```

These say `will retry`, which `design.md` line 534–535 pins as the attempt-1 notice; the phrase the
check greps for, `falling back`, is emitted only on a genuine second failure and appears **0** times.

Game-container tail (decoded, verbatim):

```
signals llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
signals: listening on 0.0.0.0:8080
player connected: slot 0
signals: seat 0 (Alpha, NW) registered as greenwave kind=llm
…
signals: seat 1 (Beta, NE) registered as gatekeeper kind=llm
signals: episode settled — tick 256/256 turn 32/32 through 134 demand 422 on-net 152 queued 109 wait 48093 spillback 27 gridlock 0 waves 0 reason=complete endRule=fullPeriod
signals results: {…}
signals: shutting down
```

**Status: TRUE** — zero hits on `falling back`, `LLM provider is unavailable` and `cut off at
max_tokens`. The one `rejected` hit is the coworld's own results key, attributed above; no
documented-exception clause was needed and no cross-run Bedrock outage had to be invoked.

---

## 6. The public page uses the static replay path

### 6a. Raw-HTML grep — finds nothing (not a failure; page is client-rendered for the iframe)

```
$ curl -sS "https://softmax.com/sumo-traffic-signals" | grep -o '<iframe[^>]*src="[^"]*"'
(no match)
HTTP 200  bytes=745062
```

Per `prompts/60-verify.md` check 6 and `playbooks/observatory-api.md` §Featured match, an empty grep
is *unknown*, not false. **The source actually used is the API the page itself reads.**

### 6b. `/coworlds` detail — `featured_match` is null platform-wide, so not evidence either

```
GET $BASE/coworlds?limit=200   headers: Authorization, User-Agent      HTTP 200
$ jq -r 'if type=="array" then . else .entries end
         | .[]|select(.name=="sumo-traffic-signals")|{id,canonical,replay_viewer,featured_match}'
{
  "id": "cow_ec8a6c5d-d31e-4c81-9b8d-2f5d404c1944",
  "canonical": true,
  "replay_viewer": null,
  "featured_match": null
}
```

`canonical: true`. `featured_match: null` is the documented platform-wide behaviour (lighthouse run,
2026-08-22) — not a finding about this coworld.

### 6c. The featured match, read from the page's SSR payload at `state.playlist[0]` — PRESENT

```
$ curl -sS "https://softmax.com/sumo-traffic-signals" -o /tmp/page2.html   # HTTP 200
$ python3 …unescape the SSR JSON around "playlist"…
```
```json
"playlist":[{"episodeId":"a9057c3b-1cf3-4a8c-bab8-97868e5ba5ad",
  "coworldId":"cow_ec8a6c5d-d31e-4c81-9b8d-2f5d404c1944",
  "coworldName":"sumo-traffic-signals","coworldVersion":"0.1.0",
  "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/4c2c2a45-861a-4bfb-b275-adcac8a11cf7.replay",
  "finishedAt":"2026-08-28T18:06:07.103816Z","roundNumber":3,"episodeNumber":1,
  "code":"sumo-traffic-signals.r3.e1",
  "matchup":{"divisionId":"div_013d13d5-8ef6-430d-bc77-592c81a0aa5a","divisionName":"Competition",
    "first":{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
             "score":1016,"score_label":"MMR","rounds_played":2,"episode_wins":1,"win_rate":0.5,
             "policy_label":"signals-greenwave:v1"},
    "second":{"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
              "score":984,"score_label":"MMR","rounds_played":2,"episode_wins":0,"win_rate":0,
              "policy_label":"signals-gatekeeper:v1"}},
  "inspectUrl":"/observatory/v2?tab=overview&detail=episode-request:ereq_75e2c1eb-1a8d-498e-ae67-26edcd34e6fd",
  "outcome":"first"}]
```

A featured match is present and it is round 3's episode — the same episode request verified in
item 3, with both ranked champions in the matchup.

### 6d. The iframe `src` — from the call the page's own JS makes

```
POST $BASE/coworlds/replays/session
  headers: Authorization, User-Agent, content-type: application/json
  body: {"coworld_id":"cow_ec8a6c5d-d31e-4c81-9b8d-2f5d404c1944",
         "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/4c2c2a45-861a-4bfb-b275-adcac8a11cf7.replay"}
HTTP 200
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_ec8a6c5d-d31e-4c81-9b8d-2f5d404c1944/sha256%3A77577277184749d6d02741c62a62de8109ac4b6c2b752ac788970570e3653298/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F4c2c2a45-861a-4bfb-b275-adcac8a11cf7.replay",
  "ready": true
}
```

**Source used: 6c + 6d (the SSR payload and the session endpoint), not the raw-HTML grep**, which
found nothing because the page is client-rendered for the iframe.

Path analysis of `viewer_url`:

| element | value | required |
|---|---|---|
| host | `api.observatory.softmax-research.net` | the documented static host |
| route | `/v2/coworlds/replays/static/…` | **static**, not `/client/replay` |
| `<cow_id>` | `cow_ec8a6c5d-d31e-4c81-9b8d-2f5d404c1944` | matches STATE |
| `<sha>` | `sha256%3A77577277184749d6d02741c62a62de8109ac4b6c2b752ac788970570e3653298` | = STATE `coworld.manifest_sha`, URL-encoded |
| shell | `/index.html?v=2` | ends `index.html` |
| replay | `#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F4c2c2a45-861a-4bfb-b275-adcac8a11cf7.replay` | the round-3 S3 replay from item 3 |
| `ready` | `true` | static delivery |

The replay arrives as a URL-encoded **fragment** (`#replay=`) rather than a query parameter. That is
the documented 2026-08-28 form of the same static route
(`playbooks/observatory-api.md` §Featured match: *"since 2026-08-28 the session endpoint returns
the replay as a URL-encoded **fragment** instead, `…/index.html?v=2#replay=<s3 url>`; both are the
static route"*).

**Status: TRUE** — featured match present (round 3, both champions); iframe `src` is the static
`/v2/coworlds/replays/static/<cow_id>/<manifest_sha>/index.html` route with `ready: true`. No
`/client/replay` pod URL anywhere.

---

## 7. Certification declared the static bundle

Source read: **the committed `runs/2026-08-28-sumo-traffic-signals/release-result.json`** — the
artifact phase 40 downloaded from release run `33195026416` and committed. It was present; no
re-download was needed.

```
$ jq -r '.certify.replay_liveness' runs/2026-08-28-sumo-traffic-signals/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Surrounding certification transcript from the same file (`.certify.output_tail`), verbatim:

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
…
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

```
$ jq -r '.certify.ok' runs/2026-08-28-sumo-traffic-signals/release-result.json
true
```

**Status: TRUE** — the string contains `Replay liveness: skipped (static replay bundle declared`,
read from the committed `release-result.json`, and all ten certification steps passed.

---

## 8. Spectator judgment — the viewer EXECUTED, then judged

### 8a. Dispatch

```
$ date -u                                   → dispatch_at = 2026-08-28T18:09:24Z
$ SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_ec8a6c5d-d31e-4c81-9b8d-2f5d404c1944/sha256%3A77577277184749d6d02741c62a62de8109ac4b6c2b752ac788970570e3653298/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F4c2c2a45-861a-4bfb-b275-adcac8a11cf7.replay'
$ gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
$ sleep 12
$ gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
  | jq -r 'sort_by(.createdAt)|reverse|.[]|"\(.databaseId)\t\(.createdAt)\t\(.status)"'
33198007349	2026-08-28T18:09:26Z	in_progress      <-- created AFTER dispatch_at 18:09:24Z; this run
33187402013	2026-08-28T15:54:21Z	completed
33184965298	2026-08-28T15:24:14Z	completed
33176460797	2026-08-28T13:40:19Z	completed
…
```

The URL is exactly the item-6 iframe `src`, fragment and all. The run was identified by
`createdAt > dispatch_at`, not by taking "the latest run".

```
$ gh run watch 33198007349 -R Metta-AI/coworld-builder --exit-status
✓ main viewer-check · 33198007349
✓ viewer-check in 34s (ID 98940022214)
  ✓ Set up job / ✓ checkout / ✓ setup-node / ✓ Install Playwright (pinned 1.55.0)
  ✓ Load the viewer / ✓ Summary / ✓ Upload the evidence / ✓ Fail if the viewer did not load
  ✓ Complete job
watch_exit=0        # green run
```

```
$ gh run download 33198007349 -R Metta-AI/coworld-builder -n viewer-check \
    -D runs/2026-08-28-sumo-traffic-signals/viewer-check
$ ls -la runs/2026-08-28-sumo-traffic-signals/viewer-check/
-rw-r--r-- 1 root root      0 smoke-stderr.txt
-rw-r--r-- 1 root root   1042 smoke-stdout.txt
-rw-r--r-- 1 root root   1838 viewer-smoke.json
-rw-r--r-- 1 root root 438110 viewer-smoke.png
```

`viewer-check` run id: **33198007349** (job 98940022214). `smoke-stderr.txt` is empty (0 bytes).

### 8b. The readouts, verbatim from the downloaded artifact

```
$ jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/…/viewer-check/viewer-smoke.json
{"loaded":true,"ms":2494,"clock":"THROUGH 0 / 260 PAR DEMAND 4 · WAITING 0 · SPILLBACK 0 · GRIDLOCK 0 · WAVES 0","scorebug":"DAVEEY NW SERVED 0 0 car-s waiting BASELINE SW SERVED 0 0 car-s waiting THROUGH 0 / 260 PAR DEMAND 4 · WAITING 0 · SPILLBACK 0 · GRIDLOCK 0 · WAVES 0 DAVEEY-1 NE SERVED 0 0 car-s waiting BASELINE (2) SE SERVED 0 0 car-s waiting ALPHA daveey 0 out 0 car-s BETA daveey-1 0 out 0 car-s GAMMA Baseline 0 out 0 car-s DELTA Baseline (2) 0 out 0 car-s A B C D 1 2 3 4","feed_lines":0}
```

```
$ jq -c '.signals' runs/…/viewer-check/viewer-smoke.json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

```
$ jq -r '.failure // "no failure"' runs/…/viewer-check/viewer-smoke.json
no failure
```

```
$ jq -c '.canvas_text' runs/…/viewer-check/viewer-smoke.json
{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
```

Three clock readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | `#clock` readout |
|---|---|
| **0 %** | `THROUGH 0 / 260 PAR DEMAND 4 · WAITING 0 · SPILLBACK 0 · GRIDLOCK 0 · WAVES 0` |
| **50 %** | `THROUGH 46 / 260 PAR DEMAND 328 · WAITING 16182 · SPILLBACK 3 · GRIDLOCK 0 · WAVES 0` |
| **100 %** | `THROUGH 134 / 260 PAR DEMAND 422 · WAITING 48093 · SPILLBACK 3 · GRIDLOCK 0 · WAVES 0` |

The three readouts are **all different**, and they move monotonically in the direction the episode
did. The 100 % readout equals the recorded results exactly: `throughput 134`, `parThroughput 260`,
`demandGenerated 422`, `networkWaitTicks 48093`, `gridlocks 0`, `greenWaves 0` (item 4). `loaded`
was signalled by the shell attribute `data-replay-loaded="true"` after **2494 ms**; the
`coworld-replay` bridge is not used by this shell (`bridge_ready:false`, `bridge_error:[]` — no
error, just not the signalling path). `canvas_text.never_inside == 0`: no caption was ever drawn
outside the canvas.

`feed_lines: 0` is a **probe-selector artefact, not an empty feed.** `viewer_smoke.mjs` looks for
`#feed, .feed, #log, [id$="-feed"]`; the live shell names its feed `#killfeed`, the starter's id.
Fetched fresh from the live shell:

```
$ curl -sS "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_ec8a6c5d-d31e-4c81-9b8d-2f5d404c1944/sha256%3A7757…3298/index.html" | grep -oE 'id="[a-zA-Z0-9_-]+"' | sort -u
HTTP 200  bytes=133212
id="bannerlane" id="board" id="btn-back" id="btn-end" id="btn-fwd" id="btn-loop" id="btn-play"
id="btn-restart" id="btn-skip" id="btn-spoilers" id="chip-ring" id="chip-spill" id="chrome"
id="clock" id="clock-caption" id="clock-time" id="ec-headline" id="ec-how" id="ec-replay"
id="ec-teams" id="ec-wincond" id="endcard" id="ffwd-chip" id="ffwd-mini" id="grain" id="killfeed"
id="lightpool" id="lk-art" id="lk-bg" id="lk-cap" id="lk-sprites" id="lockerroom" id="lulls"
id="mmwarn" id="momentum" id="plates-l" id="plates-r" id="scorebug" id="scrub" id="scrub-fill"
id="scrub-head" id="scrub-win" id="sigchips" id="sigpressure" id="sigtally" id="speedchips"
id="stage" id="status" id="tick-clock" id="transport" id="viewport" id="win-chip"
```

`#scrub` **is** present (that is why the three readouts exist). The feed's content is visible in the
screenshot and described in 8d.

### 8c. Chrome provenance — the same shell as the starter, not a rewrite

Diffing the live shell's element ids against the coworld-ctf starter's
`client/replay_broadcast.html`:

```
$ comm -12 starter_ids live_ids     # 47 ids present in BOTH
bannerlane board btn-back btn-end btn-fwd btn-loop btn-play btn-restart btn-skip btn-spoilers
chrome clock clock-caption clock-time ec-headline ec-how ec-replay ec-teams ec-wincond endcard
ffwd-chip ffwd-mini grain killfeed lightpool lk-art lk-bg lk-cap lk-sprites lockerroom lulls
mmwarn momentum plates-l plates-r scorebug scrub scrub-fill scrub-head scrub-win speedchips
stage status tick-clock transport viewport win-chip

$ comm -23 starter_ids live_ids     # starter only — the FPV/minimap/zoom panel
fpv fpv-canvas fpv-cap fpv-gear fpv-grip fpv-hp fpv-hud fpv-map fpv-map-canvas fpv-name
minimap minimap-canvas povBadge viewpanel zoom-in zoom-out zoom-read zoom-slider zoombar

$ comm -13 starter_ids live_ids     # live only — this game's five signal chips
chip-ring chip-spill sigchips sigpressure sigtally
```

47 of the starter's chrome ids are carried verbatim; the only omissions are the first-person /
minimap / zoom panel that `design.md` §Viewer explicitly declares dropped (log.md phase-10
checklist: `chrome-provenance+removed-list+zoom-dropped=x`); the only additions are five
game-specific signal chips. This is the starter's chrome, not the cogame-gridlock "rewrite that
shares only the ids" failure.

### 8d. What the render shows — reconciled against the replay

`viewer-smoke.png`, 1280 × 800, taken after the 100 % scrub, so it captures the **endcard** state.
Description of the downloaded image:

- **Top scorebug strip.** Four plates flanking a centre readout. Left: a red-liveried
  `24 SERVED · NW · DAVE…` plate with `12517 car-s waiting` beneath it, and a green
  `42 SERVED · SW · BASE…` plate with `10832 car-s waiting`. Right: a blue `DAVE… · NE · SERVED 24`
  with `14785 car-s waiting`, and a yellow `BASE… · SE · SERVED 44` with `9959 car-s waiting`.
  Centre, in large type: **`THROUGH 134 / 260 PAR`**, and under it
  `DEMAND 422 · WAITING 48093 · SPILLBACK 3 · GRIDLOCK 0 · WAVES 0`.
- **The city, behind the overlay.** The 4 × 4 grid is drawn across the stage with intersection
  labels `A1 A2 A3 A4 / B1 … B4 / C1 … C4 / D1 … D4` readable at their nodes, the link cells
  between them picked out as small blocks, and column/row rails `A B C D` / `1 2 3 4`. Individual
  vehicle cells are visible on the links. It is dimmed under the endcard, as the starter's endcard
  does.
- **Feed and banner lane** (top-left of the stage, under the overlay dim): four per-seat status
  lines — `DELTA  Bas…  44 out  9959 car-s`, `GAMMA …`, `ALPHA  dav…  24 out  12517 car-s`,
  `BETA  dav…  24 out  14785 car-s` — and an amber alert banner reading
  **`SPILLBACK A1>A2 · A2>A3 · A3>A4`**. That is the game's own vocabulary naming the exact links
  that backed up.
- **Endcard.** Headline **`134/422 CARS THROUGH · PAR 260 MISSED`**, an amber `FULL PERIOD` badge,
  then a table `CONTROLLER / SERVED / WAITING / WAVES / SPILLBACKS`:
  `daveey 24 12517 0 73`, `daveey-1 24 14785 0 73`, `Baseline 42 10832 0 73`,
  `Baseline (2) 44 9959 0 73`; a summary line
  `0 green waves, 73 spillbacks, 0 gridlock, 48093 car-seconds lost, 27 turned away`; and
  `CITY SCORE 133759850`. Below it four quadrant cards — `ALPHA · NW daveey` (cars out 24,
  car-seconds lost 12517, phase changes 66, score 133759850), `BETA · NE daveey-1`
  (24 / 14785 / 80 / 133759820), `GAMMA · SW Baseline` (42 / 10832 / 124 / 133759870),
  `DELTA · SE Baseline (2)` (44 / 9959 / 123 / 133759880).
- **Transport strip and scrubber.** Along the bottom: restart, step-back, pause, `+5s`, step-forward,
  loop, fast-forward, a `spoilers` toggle (underlined amber, active), a `256 / 256` tick counter,
  and speed chips `1× 2× 4× 8× 16×` with `1×` selected. Under it the scrubber: a full-width
  tick-mark rail of per-turn event marks, an orange playhead pinned at the far right, and a
  **momentum graph labelled `THROUGHPUT`** with a green trace rising steadily from flat to its
  final height and a yellow trace beneath it.

**Reconciliation with the replay record.** Every number the picture shows is in the replay bytes of
item 4: `served [24,24,42,44]`, `seatWaitTicks [12517,14785,10832,9959]`,
`phaseChanges [66,80,124,123]`, `scores [133759850,133759820,133759870,133759880]`,
`throughput 134`, `demandGenerated 422`, `parThroughput 260`, `rejected 27` (rendered "27 turned
away"), `networkWaitTicks 48093`, `spillbacks 73`, `gridlocks 0`, `greenWaves 0`,
`endRule "fullPeriod"` (the `FULL PERIOD` badge), `finalTick 256` (the `256 / 256` counter). The
seat names on screen — `daveey`, `daveey-1`, `Baseline`, `Baseline (2)` — are exactly the replay's
`names` array, so the champions are identified by player and the fillers are correctly de-named.

Ordered excerpts of the record the viewer was drawing (`directives`, turn / slot / source / orders /
radio), which the scrub readouts sit on top of:

*Early — turns 1–3:*
```
1	0	llm	A1:phase/EWG A2:wave/EWG+5 B1:auto B2:auto	Column 1 eastbound is my wave: A1 at +0, A2 at +6
1	1	llm	A3:auto A4:auto B3:auto B4:auto	Beta starting. All exits empty, running auto. Will coordinate green waves eastbound on row A and B at standard offsets.
1	2	scripted	C1:phase/NSG C2:phase/NSG D1:phase/NSG D2:phase/NSG
1	3	scripted	C3:phase/NSG C4:phase/NSG D3:phase/NSG D4:phase/NSG
2	0	llm	A1:phase/EWG A2:wave/EWG+5 B1:auto B2:auto	Alpha wave avenue: A1-A2 eastbound at +0,+5. Standard offsets maintained.
2	1	llm	A3:hold A4:phase/EWG B3:hold B4:phase/EWG	Beta: A3 NSG +0, A4 EWG +0, B3 NSG +0, B4 EWG +0. Clearing E queues at A4 (1 car, 3 ticks blocked)…
3	0	llm	A1:phase/EWG A2:hold B1:auto B2:auto	Alpha: row A eastbound wave A1 at +0, A2 at +5. A2 north approach blocked 9 ticks by full link ahead.
3	1	llm	A3:hold A4:hold B3:hold B4:hold	Beta holding all phases. A4 N queue 2 blocked 6t on EWG—will force NSL next turn if not cleared. Monitoring nA2 spillback…
```

*Middle — turns 16–17 (the 50 % scrub sits here):*
```
16	0	llm	A1:phase/NSL A2:phase/EWG B1:hold B2:hold	Alpha: N-S avenue: A1 NSL to clear N/S backlog (3N,3S blocked 27/20t); A2 EWG to drain A1>A2 link. B1/B2 hold; B2>A2 full…
16	1	llm	A3:phase/NSG A4:phase/EWG B3:phase/NSG B4:phase/NSG	Beta draining spillback: A3 NSG to clear A4, A4 EWG to eA4, B3/B4 NSG to open B2. All exits clear after this turn.
17	0	llm	A1:phase/EWG A2:wave/EWG+5 B1:hold B2:hold	Alpha row A eastbound wave: A1 at +0, A2 at +5. B-row holding to prevent backpressure into full exits.
17	1	llm	A3:phase/NSL A4:phase/EWL B3:phase/EWL B4:phase/EWL	Beta draining spillback: A3 NSL (N queue 3, exit A2 open); A4 EWL (S blocked 58t); B3 EWL (W blocked 18t); B4 EWL (E blo…
```

*Late — turns 31–32 (the 100 % scrub and the screenshot):*
```
31	0	llm	A1:hold A2:phase/NSG B1:phase/NSL B2:phase/EWG	A1 held (exits full). A2 NSG to drain W queue 6. B1 NSL (S blocked 48t). B2 EWG (E queue 3, S can wait).
31	1	llm	A3:hold A4:phase/NSG B3:hold B4:phase/EWG	Beta: A4 N-exit starved 42t, forcing NSG to clear. B4 E-exit full 50t, switching to EWG. A3>A4 spillback—holding A3 EWG…
32	0	llm	A1:phase/EWL A2:hold B1:hold B2:phase/EWL	A1 forcing EWL for W (52t blocked); A2 holding, A2>A3 full. B2 forcing EWL for S (25t blocked).
32	1	llm	A3:phase/EWG A4:phase/NSL B3:phase/EWL B4:hold	Beta: A3→EWG to drain W/E queues. A4→NSL (N blocked 60t, forced override imminent). B3→EWL to clear W queue (30t blocked…
```

### Spectator judgment

**It is legible, and it shows the game.** The picture is not empty, not frozen and not unreadable.
A stranger opening this page sees, without being told anything: a 4×4 city with named intersections
and cars queued on the links; a headline number, `THROUGH 134 / 260 PAR`, that says at a glance the
network under-performed its benchmark; four coloured plates naming who ran which quadrant
(`daveey` NW, `daveey-1` NE, the two `Baseline` fillers SW/SE) with each one's cars-out and
car-seconds-waiting; an amber banner calling out the exact failure — `SPILLBACK A1>A2 · A2>A3 ·
A3>A4`, one champion's green becoming the next controller's queue, which is the thesis of the game
stated on screen in the game's own words; and an endcard that ranks all four controllers on served /
waiting / waves / spillbacks and prints the city score. The `WAVES 0` counter is a legible verdict
too: the champions *attempted* green waves (three `wave` orders with a +5 tick offset, and the radio
line "Column 1 eastbound is my wave: A1 at +0, A2 at +6"), and the viewer honestly reports that none
of them landed.

**It moves.** The three scrub readouts differ and rise monotonically (through 0 → 46 → 134, waiting
0 → 16182 → 48093, demand 4 → 328 → 422) and land exactly on the recorded results; the momentum
graph under the scrubber shows the throughput trace climbing across the whole episode rather than a
flat line; the tick counter reads `256 / 256`. This is a replay advancing through 32 turns, not a
single frame held still.

**It is the starter's chrome.** Transport strip, scrubber with momentum graph, scorebug plates,
endcard, locker-room and banner-lane are the coworld-ctf/paintbot furniture — 47 shared element ids
(8c), with only the FPV/minimap/zoom panel dropped as the design declared and five signal-specific
chips added. It reads as the same product family, not a look-alike rewrite.

**Two legibility observations for the coordinator (neither affects any verdict):**
1. The transport-strip counter reads `SPILLBACK 3` while the endcard reads `73 spillbacks` — a live
   count of currently-spilled links versus the cumulative total. Both are correct against the
   replay (`spillbacks: 73`), but the two labels are identical and could be mistaken for a
   contradiction.
2. `viewer_smoke.mjs` reports `feed_lines: 0` because the feed element is named `#killfeed` (the
   starter's id) and the probe's selector list is `#feed, .feed, #log, [id$="-feed"]`. That is a
   gap in the shared CI probe, not in this coworld's viewer — the feed is present and populated in
   the screenshot. Worth widening the selector in `templates/tools/ci/viewer_smoke.mjs`.

**Status: TRUE** — `loaded: true` (`data-replay-loaded="true"` at 2494 ms, `failure: null`, green
CI run) **and** the three clock readouts differ. Rendered evidence committed at
`runs/2026-08-28-sumo-traffic-signals/viewer-check/` from run **33198007349**.

---

## Definition-of-done summary

All eight checks TRUE, every one on evidence fetched during this pass (items 7 and 8 under their
documented exceptions). No `NOT FETCHED` item, no inferred verdict, no undocumented exception
claimed. Elapsed inside the 75-minute bound: rounds 2 and 3 were both complete 21 minutes in;
verification finished 31 minutes in.

- Completed rounds: **2** and **3** (round 1 `failed` at placement time, pre-filler, excluded with
  its verbatim error).
- Verified episode: `ereq_75e2c1eb-1a8d-498e-ae67-26edcd34e6fd` (round 3, `sumo-traffic-signals.r3.e1`).
- Replay: `https://softmax-public.s3.amazonaws.com/replays/4c2c2a45-861a-4bfb-b275-adcac8a11cf7.replay`
- Iframe `src`: `https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_ec8a6c5d-d31e-4c81-9b8d-2f5d404c1944/sha256%3A77577277184749d6d02741c62a62de8109ac4b6c2b752ac788970570e3653298/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F4c2c2a45-861a-4bfb-b275-adcac8a11cf7.replay`
- `viewer-check` run: **33198007349**
