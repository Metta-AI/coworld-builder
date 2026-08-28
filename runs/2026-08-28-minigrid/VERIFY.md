# VERIFY — minigrid   (2026-08-28T22:55Z)

Verdict: **3 items false** (checks 5, 6, 8) — checks 1, 2, 3, 4, 7 TRUE.

Run: `2026-08-28-minigrid` · slug `minigrid` · `$COW` `cow_5201d3e2-0aa8-45ef-b6de-ebd76a45f329`
version `0.1.0` · `$L` `league_78d5b417-52a0-4459-8fd6-3b9aeacfe1ca`
`$D` `div_721f571a-ece7-4ed9-8b1c-15eb2cd072be` · manifest_sha
`sha256:90039809a9670a2d6c5c8a0769b2d1cf92da10c8bbcf7e8b8fbf1d2e417b09c4`

All ids read from `runs/2026-08-28-minigrid/STATE.json`. Every fetch below was made in this
verifier session (2026-08-28 22:14Z – 22:55Z); nothing is reused from an earlier phase except
check 7 (the committed `release-result.json`, as `prompts/60-verify.md` §7 directs) and check 8's
rendered evidence (the `viewer-check.yml` runs dispatched by this session at 22:38, 22:40 and
22:41Z).

Headers on every Observatory call: `Authorization: Bearer $SOFTMAX_TOKEN` and
`User-Agent: coworld-builder/1.0`; `X-Use-Elevated-Privileges: true` added on the two reads that
require it (`/artifacts/logs`, `/leagues/$L/filler-policies`). Values are never printed.

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_78d5b417-52a0-4459-8fd6-3b9aeacfe1ca
D=div_721f571a-ece7-4ed9-8b1c-15eb2cd072be
COW=cow_5201d3e2-0aa8-45ef-b6de-ebd76a45f329
```

Poll log (checks 1 and 3, per `prompts/60-verify.md` §Waiting; bound 75 min from 22:14Z):

| UTC | rounds seen |
|---|---|
| 22:14:15 | round 1 `pending` |
| 22:15:26 | round 1 `pending` |
| 22:20:23 | round 1 **completed** 22:15:37Z |
| 22:26:04 | round 1 completed; no round 2 yet |
| 22:30:53 | round 2 `pending` |
| 22:35:47 | round 2 **completed** 22:32:00Z → bound satisfied (2 completed rounds, 21 min in) |
| 22:49:23 | round 3 **completed** 22:46:09Z |

---

## 1. ≥2 completed rounds after the fillers were set

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq 'if type=="array" then . else .entries end
       | [.[]|{id,round_number,status,error,created_at,completed_at,
               entrants:.round_config.entrant_policy_version_ids}]'
```

Fetched 2026-08-28T22:35:57Z:

```json
[
  {
    "id": "round_a4ab0f21-6588-4b6c-8eb0-5d25565535ee",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T22:27:00.890259Z",
    "completed_at": "2026-08-28T22:32:00.838673Z",
    "entrants": [
      "6eed9b32-93bb-42db-9c06-2a33a41678ae",
      "8e8fff3c-dfee-4dfc-81ba-841de3a7e355"
    ]
  },
  {
    "id": "round_d23b23fc-be7d-4e96-aa40-b147106b3eda",
    "round_number": 1,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T22:12:00.490449Z",
    "completed_at": "2026-08-28T22:15:37.416229Z",
    "entrants": [
      "6eed9b32-93bb-42db-9c06-2a33a41678ae",
      "8e8fff3c-dfee-4dfc-81ba-841de3a7e355"
    ]
  }
]
```

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end
          | [.[]|select(.status=="completed")]|length'
```
```
2
```

Re-fetched 2026-08-28T22:49:23Z (a third round landed while check 8 was running):

```json
[{"round_number":3,"status":"completed","completed_at":"2026-08-28T22:46:09.421195Z"},
 {"round_number":2,"status":"completed","completed_at":"2026-08-28T22:32:00.838673Z"},
 {"round_number":1,"status":"completed","completed_at":"2026-08-28T22:15:37.416229Z"}]
```

No round has status `failed` or `discarded`; every `error` is `null`.

**Fillers were set before round 1.** `runs/2026-08-28-minigrid/log.md:45`:

```
2026-08-28T22:13:04Z 50 fillers registered BEFORE trigger: scout=dd96f37f bumper=bc769311
  (POST filler-policies 200, response lists exactly these two)
```

and the live read confirms exactly those two are the league's fillers now:

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}" | jq .
```
```json
{
  "filler_policy_versions": [
    {"policy_version_id": "dd96f37f-ce9e-485c-8e13-412e923e816a",
     "policy_name": "minigrid-scout", "version": 1, "player_name": "daveey"},
    {"policy_version_id": "bc769311-e87c-49ff-86b7-67794b891c6b",
     "policy_name": "minigrid-bumper", "version": 1, "player_name": "daveey"}
  ]
}
```
(rows trimmed to the identifying fields; `policy_id` / `display_name` omitted.)

Status: **TRUE** — rounds 1, 2 and 3 are `completed` (22:15:37Z, 22:32:00Z, 22:46:09Z), all after
the fillers were registered at 22:13:04Z; both completed rounds seated only the two champion
policy versions (`6eed9b32…` = cartographer, `8e8fff3c…` = missionfirst).

---

## 2. Both champions ranked; fillers absent or Baseline

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```

Fetched 2026-08-28T22:35:57Z (bare list, as `playbooks/observatory-api.md` §11 says):

```json
[
  {"rank": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
   "score": 1030.5304984710244, "score_label": "MMR", "rounds_played": 2, "episode_wins": 2.0,
   "win_rate": 1.0, "policy_label": "minigrid-cartographer:v1"},
  {"rank": 2, "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
   "score": 969.4695015289755, "score_label": "MMR", "rounds_played": 2, "episode_wins": 0.0,
   "win_rate": 0.0, "policy_label": "minigrid-missionfirst:v1"}
]
```

Re-fetched 2026-08-28T22:49:23Z, after round 3:

```
1	daveey	minigrid-cartographer:v1	1058.3447599852047	3	4.0
2	richard	co-gas-minigrid-subgoal-router-richard:v1	1000.0	1	1.0
3	daveey-1	minigrid-missionfirst:v1	941.655240014795	3	0.0
```

Status: **TRUE** — `daveey` (`minigrid-cartographer:v1`) and `daveey-1`
(`minigrid-missionfirst:v1`) are both ranked with `rounds_played = 3 ≥ 1`. Neither filler
(`minigrid-scout:v1`, `minigrid-bumper:v1`) appears on the leaderboard at all, and no row is
labelled `Baseline` — the fillers were never needed, because the division always had ≥2 entrants.
Note for the coordinator: a third, **external** entrant appeared between the two fetches —
`richard` / `co-gas-minigrid-subgoal-router-richard:v1` (`rounds_played 1`). It is a submitted
third-party policy, not one of this run's fillers, and it does not affect this check.

---

## 3. The latest round's episode requests completed with a replay

The flat route in the prompt is dead — `playbooks/observatory-api.md` §9 records
`GET $BASE/episode-requests?round_id=…` returning **HTTP 405** since 2026-08-26. The nested route
is used instead, exactly as that playbook directs:

```bash
R=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
    | jq -r 'if type=="array" then . else .entries end
             |[.[]|select(.status=="completed")]|max_by(.round_number).id')
# R=round_aa501498-e555-4a71-b4cb-bae6c84076b1   (round 3, latest completed, 22:49:23Z)
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" \
 | jq -c 'if type=="array" then . else .entries end|[.[]|{id,status}]'
```
```json
[{"id":"ereq_e90fc9d0-5fc2-431a-a563-0cf62ad169db","status":"completed"},
 {"id":"ereq_a6cb6363-5621-4d40-a99c-ebbe390656a7","status":"completed"},
 {"id":"ereq_243aa916-6b55-4d88-800b-3469c4f356d5","status":"completed"}]
```

```bash
for E in …; do curl -sS "$BASE/episode-requests/$E" "${AUTH[@]}" \
  | jq -c '{status, replay_url, participants:[.participants[]|{policy_name,player_name,is_filler}],
            participant_scores}'; done
```
```json
{"status":"completed","replay_url":"https://softmax-public.s3.amazonaws.com/replays/2f0f47fd-0110-4fe5-8190-84a00820c8a8.replay","participants":[{"policy_name":"co-gas-minigrid-subgoal-router-richard","player_name":"richard","is_filler":false}],"participant_scores":[{"position":0,"score":108000.0}]}
{"status":"completed","replay_url":"https://softmax-public.s3.amazonaws.com/replays/70a0e17b-ae6c-4f4f-99bd-cdf0e8b0ab61.replay","participants":[{"policy_name":"minigrid-missionfirst","player_name":"daveey-1","is_filler":false}],"participant_scores":[{"position":0,"score":106100.0}]}
{"status":"completed","replay_url":"https://softmax-public.s3.amazonaws.com/replays/5eb66cb5-6917-4dee-a4c5-3f00c60d27d8.replay","participants":[{"policy_name":"minigrid-cartographer","player_name":"daveey","is_filler":false}],"participant_scores":[{"position":0,"score":209090.0}]}
```

Round 2 (the latest completed round when checks 3–5 were first executed, 22:35–22:37Z, and the
round whose replay check 8 rendered) — full untrimmed detail, both champion episodes:

```json
=== ereq_b5878b96-ceb5-42b4-87f3-d99d725aa322
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/9d6c6eac-46b7-47d1-b936-d70761c155e2.replay",
  "participants": [
    {"position": 0, "kind": "policy",
     "policy_version_id": "8e8fff3c-dfee-4dfc-81ba-841de3a7e355",
     "policy_name": "minigrid-missionfirst", "version": 1,
     "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
     "is_filler": false, "is_seed": false}
  ],
  "participant_scores": [{"position": 0, "score": 7000.0}]
}
=== ereq_87f22275-7a55-46a8-936f-dd64f6d9a373
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/5c5bd71e-0bbb-4f75-b114-e94f419e232d.replay",
  "participants": [
    {"position": 0, "kind": "policy",
     "policy_version_id": "6eed9b32-93bb-42db-9c06-2a33a41678ae",
     "policy_name": "minigrid-cartographer", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "is_filler": false, "is_seed": false}
  ],
  "participant_scores": [{"position": 0, "score": 104000.0}]
}
```

**One participant per episode request is by design, not a missing seat.**
`runs/2026-08-28-minigrid/design.md:102-105` §Seats and aliases: *"`num_agents` = 1. Exactly one
seat, always … Every episode is a solo time-trial; policies are compared across episodes, not
within one."* The round therefore fans out into one episode per entrant, and `daveey` and
`daveey-1` are both named across the round's episode requests (round 2: two episodes, one each;
round 3: three, one per entrant).

Status: **TRUE** — every episode request of the latest completed round is `completed` with a
non-null `replay_url`; `player_name` is `daveey` on one and `daveey-1` on another, `is_filler` is
`false` on both, and no `Baseline (N)` seat appears.

---

## 4. Replay bytes are valid and show the game

The replay is the starter's **binary `COWLDMGD`** format, kept deliberately
(`design.md:1197-1223` §Replay bytes: a JSON replay would mean rewriting `replays.nim`,
`replay_runtime.nim`, `static_replay_worker.js` and `wasm_replay_smoke.cjs`). The design note
declares the strict-UTF-8-JSON evidence path for this check: `tools/replay_summary.py` from the
coworld repo, whose output is one strict-UTF-8 JSON object.

```bash
git clone --depth 1 https://github.com/Metta-AI/cogame-minigrid /tmp/cogame-minigrid   # b19bc08
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/5eb66cb5-6917-4dee-a4c5-3f00c60d27d8.replay" \
     -o /tmp/r3-cart.replay              # HTTP 200 bytes=79215
python3 /tmp/cogame-minigrid/tools/replay_summary.py /tmp/r3-cart.replay > /tmp/r3-cart.json
jq -e . /tmp/r3-cart.json >/dev/null && echo "strict UTF-8 JSON: ok"
```

Latest round (3), champion #1 `daveey` / cartographer, and champion #2 `daveey-1` / missionfirst:

```
r3-cart HTTP 200 bytes=79215
r3-cart strict UTF-8 JSON: ok
protocol=minigrid/v1 reason=complete endRule=gauntletComplete tasksSolved=2 llmTurns=46 fallbackTurns=0 plans=46 says=46 fallbackRecords=0 name=cartographer
{"llm":46}

r3-mf HTTP 200 bytes=68817
r3-mf strict UTF-8 JSON: ok
protocol=minigrid/v1 reason=complete endRule=gauntletComplete tasksSolved=1 llmTurns=35 fallbackTurns=1 plans=36 says=35 fallbackRecords=6 name=missionfirst
{"fallback":1,"llm":35}
```

Round 2, cartographer (`5c5bd71e…` — the replay check 8 rendered), full `results`:

```json
{
  "names": ["cartographer"], "aliases": ["Alpha"], "scores": [104000],
  "reason": "complete", "endRule": "gauntletComplete", "variant": "gauntlet",
  "seed": 1249637142, "taskCount": 5, "parTasks": 3, "tasksSolved": 1,
  "progressTotal": 4, "speedTotal": 0,
  "taskFamilies": ["lavagap","doorkey","multiroom","keycorridor","babyai"],
  "taskMissions": ["get to the green goal square",
                   "use the yellow key to open the door and then get to the green goal square",
                   "get to the green goal square", "pick up the blue ball",
                   "put the red ball next to the blue key"],
  "taskSolved": [false,true,false,false,false],
  "taskOutcome": ["died","solved","timeout","timeout","timeout"],
  "taskTurns": [8,11,11,11,11], "taskTicks": [43,65,69,51,86],
  "taskProgress": [1,3,0,0,0], "deaths": 1, "crashes": 0,
  "taskCellsSeen": [160,153,49,103,169], "cellsTotal": 169,
  "doorsOpened": 1, "objectsPickedUp": 1, "productionsFired": 0,
  "primitivesExecuted": 313, "actionsDropped": 0, "macrosUnreachable": 4,
  "repliesRepaired": 0, "finalTick": 314, "turnsPlayed": 52,
  "policyKinds": ["llm"], "llmTurns": 52, "fallbackTurns": 0,
  "deadSeats": [false], "stopDetail": ""
}
```

```bash
jq -c '[.plans[].source]|group_by(.)|map({(.[0]):length})|add' /tmp/r2-cart.json
```
```json
{"llm":52}
```

**Champion decisions are LLM decisions with non-trivial content, not fallbacks.** Every plan in
the round-2 cartographer replay has `source == "llm"` (52 of 52, `fallbackTurns: 0`), and the
round-2 missionfirst replay is 45 of 45 llm, `fallbackTurns: 0`. In the latest round, cartographer
is 46 of 46 llm / 0 fallback turns and missionfirst is 35 llm + **1** fallback turn of 36
(2.8 % — a small minority, as the check requires). The verbs and `say` lines are the game being
played, not filler (round 2 cartographer, task 2 = `doorkey`, the task it solved):

```
turn  task  source  verbs                                            say
16    1     llm     goto pickup goto      Getting yellow key, then exploring south/east unknowns for goal
17    1     llm     goto toggle           Going to yellow locked door at (7,5) to open it with my yellow key.
18    1     llm     forward forward right forward forward left forward forward right forward forward forward
                                          Moving through open yellow door, exploring east/south for green goal
19    1     llm     goto                  Going to goal at (11,8)
```

`results.reason` is `complete` on every replay checked (rounds 2 and 3, both champions) — the
healthy value; the design's declared-acceptable `deadline` was never needed
(`design.md:410-440` §End conditions). `protocol` is `minigrid/v1`, which matches the manifest
(`design.md:1208`).

Status: **TRUE** — bytes fetched from S3, parsed to strict UTF-8 JSON by the repo's documented
summary path, `protocol` matches, `results.reason == "complete"`, and the champion seats' plans
are LLM-sourced with real verbs (`goto`, `pickup`, `toggle`, `forward`) and non-empty `say` lines.

---

## 5. Hosted game log is clean

```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o raw
python3 declogs.py raw > decoded.txt     # ast.literal_eval per b'…' repr, per playbook §10
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' decoded.txt \
  || echo CLEAN
```

**Round 2 (both champion episodes) — CLEAN:**

```
cart logs HTTP 200 bytes=116408      (ereq_87f22275…, daveey / cartographer)
--- cart GREP: CLEAN
mf logs HTTP 200 bytes=97729         (ereq_b5878b96…, daveey-1 / missionfirst)
--- mf GREP: CLEAN
```

game container, round 2 / cartographer, verbatim:

```
===== container: game =====
minigrid llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
minigrid: serving on 0.0.0.0:8080 seed 1249637142 variant gauntlet
minigrid: player connected on slot 0
minigrid: seat 0 registered as cartographer (llm)
Dropped message to disconnected client
minigrid llm: seat 0 attempt 1 failed, will retry: input(1, 33) Error: string literal as key expected
minigrid llm: seat 0 attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 0 attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 0 attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid: episode complete — reason complete endRule gauntletComplete solved 1/5 score 104000
```

Those four are **attempt-1 notices**, which the grep does not match and which the design
distinguishes on purpose (`design.md:561-563`: *"The attempt-1 notice says `will retry`; only a
genuine second failure logs `falling back`"*). All four turns recovered on attempt 2 —
`results.fallbackTurns` is `0` for this episode (check 4).

**Round 3 (latest completed round) — champion #1 CLEAN, champion #2 NOT clean:**

```
r3-cart logs HTTP 200 bytes=95328    (ereq_243aa916…, daveey / cartographer)
--- r3-cart GREP: CLEAN

r3-mf logs HTTP 200 bytes=83971      (ereq_a6cb6363…, daveey-1 / missionfirst)
--- r3-mf GREP:
178:minigrid llm: seat 0 falling back to scout (parse_error) on turn 21
```

game container, round 3 / missionfirst, verbatim:

```
===== container: game =====
minigrid llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
minigrid: serving on 0.0.0.0:8080 seed 1250538234 variant gauntlet
minigrid: player connected on slot 0
minigrid: seat 0 registered as missionfirst (llm)
Dropped message to disconnected client
minigrid llm: seat 0 attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 0 attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 0 attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 0 attempt 2 failed: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 0 falling back to scout (parse_error) on turn 21
minigrid llm: seat 0 attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid: episode complete — reason complete endRule gauntletComplete solved 1/5 score 106100
```

**Is this the SPEC's documented platform-wide cause? No — cross-checked, and it is not.**
`prompts/60-verify.md` §5 allows the exception only if another LLM coworld's latest log shows the
same symptom. The parallel run `2026-08-28-procgen` (phase 60, same minutes, same Bedrock sidecar,
same model `claude-haiku-4-5`) was checked:

```bash
PL=league_2b1f9007-0749-4e3c-a669-a630283894f1     # runs/2026-08-28-procgen/STATE.json
… /rounds/$PR/episode-requests → ereq_9a55d352-9aac-471f-bf21-ba8dbcb7cba9
curl -sS "$BASE/episode-requests/$PE/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" | decode | grep -nE …
```
```
procgen logs HTTP 200 bytes=148640
--- procgen grep: CLEAN
--- procgen "Timeout was reached" lines: 0
===== container: game =====
procgen: seed not pinned; randomized
procgen llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
procgen: episode complete (gauntlet_complete) after 282 frames, 72 turns; unseen 181 seen 251
```

The provider itself is healthy for both coworlds — **every** Bedrock call in every episode checked
returned `ok:true, status 200`. What differs is latency against minigrid's client-side deadline
(`design.md:516` `attempt1Ms = 6.0 s`, `retryMs = 3.0 s`), computed from the sidecar's own
`bedrock_sidecar_complete` records in the logs above:

| episode | calls | all ok | p50 latency | p90 | max | calls > 6 000 ms |
|---|---|---|---|---|---|---|
| r2 cartographer | 56 | 56 | 4 608 ms | 5 648 ms | 6 272 ms | 3 |
| r3 cartographer | 46 | 46 | 4 075 ms | 4 931 ms | 5 919 ms | 0 |
| r3 missionfirst | 40 | 40 | 2 467 ms | 6 011 ms | 6 712 ms | 4 |
| **procgen** (same window) | 72 | 72 | 1 786 ms | 2 343 ms | 2 924 ms | **0** |

minigrid's prompts (~1 740–1 913 input tokens) sit close enough to the 6.0 s attempt-1 deadline
that a handful of calls per episode exceed it; on turn 21 of the round-3 missionfirst episode
*both* attempts exceeded it, producing the one `falling back` line. The episode still ended
`complete` with 1/5 solved and 1 fallback turn in 36 (2.8 %), i.e. the designed degrade path
worked — but SPEC check 5 requires **zero** matching lines and the platform-wide exception does
not apply here.

Two further observations for the coordinator (not part of the verdict):
- the fallback's `cause` is logged as `parse_error` although both attempts failed with a
  transport timeout; `design.md:560` lists `timeout` / `transport_error` as the causes that fit.
  The cause label looks mis-attributed.
- the actionable fix is client-side: raise `attempt1Ms` above 6.0 s (or shorten the prompt), not
  a provider/capacity change. `retryMs` 3.0 s means a second attempt gets less headroom than the
  first, so a slow-but-healthy call that misses attempt 1 will usually miss attempt 2 too.

Status: **FALSE** — round 2's two champion logs are CLEAN, but on the **latest** completed round
the champion-#2 game log contains one matching line:
`minigrid llm: seat 0 falling back to scout (parse_error) on turn 21`. Not zero, and the
documented platform-wide exception is ruled out by the procgen cross-check above.

---

## 6. The public page uses the static replay path

**Source A — raw HTML grep (`prompts/60-verify.md` §6, first form).** Fetched 22:14Z, 22:36Z and
22:49:10Z:

```bash
curl -sS "https://softmax.com/minigrid" -o page.html   # HTTP 200 bytes=761193 (22:49:10Z)
grep -o '<iframe[^>]*src="[^"]*"' page.html
```
```
(no match — 0 occurrences of the string "iframe" in the document)
```

Not a false negative: the page is client-rendered for the iframe, exactly as
`playbooks/observatory-api.md` §Featured match records ("Answered (lighthouse run, 2026-08-22)").

**Source B — the coworld detail API.**

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end|.[]
          |select(.name=="minigrid")|{id,name,canonical,replay_viewer,featured_match}'
```
```json
{
  "id": "cow_5201d3e2-0aa8-45ef-b6de-ebd76a45f329",
  "name": "minigrid",
  "canonical": true,
  "replay_viewer": null,
  "featured_match": null
}
```
(`featured_match: null` is null platform-wide and is not evidence either way — same playbook §.)

**Source C — the page's SSR payload (`state`), which is where the featured match actually lives.**
Parsed out of the same `page.html` (22:49:10Z), after unescaping:

```json
{"leagueId":"league_78d5b417-52a0-4459-8fd6-3b9aeacfe1ca",
 "playlist": [],
 "pool": {"replays": [ …3 entries, round 3 / round 2 episodes… ], "live": null},
 "divisionId":"div_721f571a-ece7-4ed9-8b1c-15eb2cd072be",
 "divisionName":"Competition","divisionCount":1,"playerCount":3,
 "activeRound": null, "newestCompletedAt":"2026-08-28T22:46:09.421195Z"}
```

and the rendered stage says, verbatim:

```html
<span class="chip chip-warn">Between rounds</span>
<h1 …>No featured match yet</h1>
<div …>The next round is expected in ~10m.</div>
```

`state.pool.replays[0]` does carry this coworld's episodes (`replay_url`,
`coworld_id: cow_5201d3e2…`, `participants: [{player_name: "daveey-1", …}]`), so the page has the
material — it is `state.playlist` that is empty, and the featured stage reads from the playlist.

**Why the playlist is empty — cross-check against five other coworld pages, all fetched
22:36–22:49Z:**

| page | `playlist` | `pool.replays` | participants per episode | players | newest completed |
|---|---|---|---|---|---|
| **minigrid** | **0** | 3 | **1** | 3 | 22:46:09Z |
| procgen (parallel run, phase 60) | **0** | 3 | **1** | 3 | 22:32:23Z |
| atari-57 | 1 | 1 | 4 | 3 | 22:31:04Z |
| snake-royale | 1 | 1 | 4 | 3 | 22:31:06Z |
| vizdoom-deathmatch | 1 | 1 | 8 | 3 | 22:25:44Z |
| gnomic | 1 | 1 | 3 | 3 | 2026-08-28T05:29Z |
| cogriculture | 0 | 4 | 2 | 5 | 2026-08-10T19:51Z (stale) |

Every recent coworld whose episodes seat **≥2 participants** has a featured match; both recent
coworlds whose episodes seat **exactly one** (minigrid and the platform's own procgen) show
"No featured match yet". `state.playlist[0].matchup` on gnomic is a `{first, second}` pair, i.e.
the stage is built around a head-to-head. minigrid is single-seat by design
(`design.md:102` `num_agents = 1`, the idea's own "Seats: 1"), so it produces no head-to-head
episode. This is an observed correlation across seven pages, not a claim about the platform's
source; and it is **not** a documented exception in SPEC or in the design note, so it does not
excuse the check.

**The static route itself — the call the page's own JS makes** (`playbooks/observatory-api.md`
§Featured match: *"The iframe `src` comes from … `POST $BASE/coworlds/replays/session`"*):

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" \
  -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_5201d3e2-0aa8-45ef-b6de-ebd76a45f329",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/5c5bd71e-0bbb-4f75-b114-e94f419e232d.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_5201d3e2-0aa8-45ef-b6de-ebd76a45f329/sha256%3A90039809a9670a2d6c5c8a0769b2d1cf92da10c8bbcf7e8b8fbf1d2e417b09c4/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F5c5bd71e-0bbb-4f75-b114-e94f419e232d.replay",
  "ready": true
}
```

That is `/v2/coworlds/replays/static/<cow_id>/<manifest_sha>/index.html` with the replay as the
URL-encoded fragment — the form the playbook records for 2026-08-28 — with `ready: true`,
`<cow_id>` = `cow_5201d3e2-0aa8-45ef-b6de-ebd76a45f329` and `<sha>` =
`sha256:90039809a9670a2d6c5c8a0769b2d1cf92da10c8bbcf7e8b8fbf1d2e417b09c4`, which is exactly
`STATE.coworld.manifest_sha`. **The string `/client/replay` does not occur anywhere in the page
(0 occurrences) or in any session response.** The same call for the round-1 replay returned the
same static path.

Status: **FALSE** (one half true, one half false, evidenced):
- **static replay path — TRUE.** Every viewer URL this coworld produces is the static route with
  the right `cow_id` and manifest sha, `ready: true`; no `/client/replay` pod URL anywhere.
- **featured match present — FALSE.** `state.playlist` is `[]` and the page renders
  "No featured match yet" at 22:36Z and again at 22:49Z, after three completed rounds and with
  three ranked players. The prompt's stated cause for absence ("fewer than two ranked players")
  does not apply; the observed cause is that the page features head-to-head episodes and this
  game seats one policy per episode by design. Reported, not excused.

Sources used: raw-HTML grep (A), `/coworlds` detail (B), the page's SSR `state` payload (C), and
the `replays/session` POST — four attempts, all recorded above.

---

## 7. Certification declared the static bundle

Read from the **committed** artifact `runs/2026-08-28-minigrid/release-result.json` (the copy
phase 40 downloaded from release run `33215083433`), not from `/tmp` and not re-downloaded — the
file was present, so the `gh run download` fallback in `prompts/60-verify.md` §7 was not needed.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-28-minigrid/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

```bash
jq -r '.certify|keys' runs/2026-08-28-minigrid/release-result.json
```
```json
["ok", "output_tail", "replay_liveness"]
```

Status: **TRUE** — the certification output contains
`Replay liveness: skipped (static replay bundle declared`, read from the committed
`runs/2026-08-28-minigrid/release-result.json`.

---

## 8. Spectator judgment — the viewer EXECUTED, then judged

### (a) Dispatch

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_5201d3e2-0aa8-45ef-b6de-ebd76a45f329/sha256%3A90039809a9670a2d6c5c8a0769b2d1cf92da10c8bbcf7e8b8fbf1d2e417b09c4/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F5c5bd71e-0bbb-4f75-b114-e94f419e232d.replay'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -c 'sort_by(.createdAt)|reverse|.[0:3]'
```
```json
[{"createdAt":"2026-08-28T22:38:57Z","databaseId":33217607488,"event":"workflow_dispatch","status":"in_progress"},
 {"createdAt":"2026-08-28T22:18:25Z","databaseId":33216261052,"event":"workflow_dispatch","status":"completed"},
 {"createdAt":"2026-08-28T21:08:08Z","databaseId":33211231543,"event":"workflow_dispatch","status":"completed"}]
```
Dispatched 22:38:58Z; the run created at 22:38:57Z is the new one (the previous newest was
22:18:25Z, another run's verifier — this workflow is shared, which is why the run is found by
sorting on `createdAt` and not by taking "the latest").

```bash
gh run watch 33217607488 -R Metta-AI/coworld-builder --exit-status
```
```
✓ viewer-check in 35s (ID 99004650648)
  ✓ Install Playwright (pinned 1.55.0)
  ✓ Load the viewer
  ✓ Upload the evidence
  ✓ Fail if the viewer did not load
```
Green run. Artifact downloaded and committed:

```bash
gh run download 33217607488 -R Metta-AI/coworld-builder -n viewer-check \
  -D runs/2026-08-28-minigrid/viewer-check
```
```
runs/2026-08-28-minigrid/viewer-check/viewer-smoke.json   (3910 B)
runs/2026-08-28-minigrid/viewer-check/viewer-smoke.png    (547117 B)
runs/2026-08-28-minigrid/viewer-check/smoke-stdout.txt
runs/2026-08-28-minigrid/viewer-check/smoke-stderr.txt    (empty)
```

Two retries (different `timeout`, then a **different replay**) were dispatched under the check's
retry budget and are committed under `viewer-check/retries/`:
`33217711224` (22:40:43Z, same replay, timeout 150) and `33217780204` (22:41:52Z, round-2
missionfirst replay `9d6c6eac…`).

### (b) The readouts

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-28-minigrid/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":2730,"clock":"SOLVED 0/5 TASK 1/5 · TURN 0/11 · TICK 141 · SEEN 35/169 · SCORE 0","scorebug":"— CARTOGRAPHER Carrying 0/5 ALPHA · SCORE 0 SOLVED 0/5 TASK 1/5 · TURN 0/11 · TICK 141 · SEEN 35/169 · SCORE 0","feed_lines":0}
```

```bash
jq -c '.signals' runs/2026-08-28-minigrid/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/2026-08-28-minigrid/viewer-check/viewer-smoke.json
```
```
no failure
```

```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-28-minigrid/viewer-check/viewer-smoke.json
```

| scrub | clock readout |
|---|---|
| 0 % | `SOLVED 0/5 TASK 1/5 · TURN 0/11 · TICK 141 · SEEN 35/169 · SCORE 0` |
| 50 % | `SOLVED 1/5 TASK 3/5 · TURN 7/11 · TICK 299 · SEEN 49/169 · SCORE 104000` |
| 100 % | `SOLVED 1/5 TASK 3/5 · TURN 7/11 · TICK 299 · SEEN 49/169 · SCORE 104000` |

**The 50 % and 100 % readouts are identical.** Reproduced on both retries:

`retries/attempt2-33217711224` (same replay, timeout 150):

| scrub | clock readout |
|---|---|
| 0 % | `SOLVED 0/5 TASK 1/5 · TURN 2/11 · TICK 143 · SEEN 37/169 · SCORE 0` |
| 50 % | `SOLVED 1/5 TASK 3/5 · TURN 7/11 · TICK 299 · SEEN 49/169 · SCORE 104000` |
| 100 % | `SOLVED 1/5 TASK 3/5 · TURN 7/11 · TICK 299 · SEEN 49/169 · SCORE 104000` |

`retries/attempt3-33217780204` (**different replay** — round-2 missionfirst, `9d6c6eac…`):

| scrub | clock readout |
|---|---|
| 0 % | `SOLVED 0/5 TASK 1/5 · TURN 1/11 · TICK 158 · SEEN 37/169 · SCORE 0` |
| 50 % | `SOLVED 0/5 TASK 3/5 · TURN 11/11 · TICK 281 · SEEN 105/169 · SCORE 3000` |
| 100 % | `SOLVED 0/5 TASK 3/5 · TURN 11/11 · TICK 281 · SEEN 105/169 · SCORE 3000` |

All three runs: `loaded: true`, `data_replay_loaded: "true"`, `failure: null`, a `#scrub` element
present (the json records real readouts rather than `"(no #scrub…)"`), and 0 % ≠ 50 % = 100 %.

Console tail from `viewer-smoke.json` (verbatim, deduplicated):

```
[http 404] …/static/cow_5201d3e2…/sha256%3A90039809…/soldier_red_front_gun.png
[http 404] …/static/cow_5201d3e2…/sha256%3A90039809…/soldier_green_front.png
[http 404] …/static/cow_5201d3e2…/sha256%3A90039809…/soldier_blue_front_gun.png
[warning] Unknown sprite protocol message type: 34      (×22)
```

### (c) What the viewer was asked to draw

From the same replay's summary (`/tmp/r2-cart.json`, check 4) — ordered excerpts:

early (turns 1–6, task 1 `lavagap`):
```
1  0 llm  face goto                                    Task 1: Reach the GREEN GOAL square. Exploring to find it.
2  0 llm  right forward forward right                  Turning west to explore large ? region. Need to find the green goal square.
3  0 llm  goto                                         Continuing west exploration to map unknown regions and locate green goal.
4  0 llm  right forward forward forward right forward  Exploring north from (1,5) to map ? region and find goal
5  0 llm  left forward forward forward right forward   Continuing north to explore ? cells and find the green goal
6  0 llm  forward forward forward right forward forward Exploring E and S to find goal G
```

middle (turns 20–26, task 3 `multiroom`):
```
20 2 llm  forward right forward forward forward left forward right forward  Exploring south and east toward goal area at (11,8)
23 2 llm  forward forward right forward forward forward                     Continuing SE exploration to find green goal
26 2 llm  face goto                                                         Heading east to continue mapping and search for green goal
```

late (last 6 turns, task 5 `babyai`):
```
47 4 llm  goto                       Searching for blue key in bottom-left unknown region
49 4 llm  goto forward right         Exploring west y=12 for blue key; red ball at (7,9) ready to place.
52 4 llm  goto pickup                Carry blue key, then position red ball next to it.
```

`results`: `reason complete`, `endRule gauntletComplete`, `tasksSolved 1`,
`taskOutcome ["died","solved","timeout","timeout","timeout"]`, `finalTick 314`, `turnsPlayed 52`,
`llmTurns 52`, `fallbackTurns 0`, `doorsOpened 1`, `objectsPickedUp 1`, `deaths 1`.

### Spectator judgment

**It is legible, and it plainly shows this game — and it is the starter's chrome, not a rewrite.**
`viewer-smoke.png` (1280 × 800, committed) is a full-frame broadcast, not a loading screen: a
13 × 13 board drawn edge to edge with bevelled masonry walls on the border ring, gridlined floor,
and real objects on it — a blue key, a green key, a blue box, a red ball, a grey obstacle ball —
with the cog itself (the composited red soldier rig) standing at the middle-left under a yellow
direction wedge. Unseen cells carry the heavy dark wash and seen-but-not-visible cells the lighter
one, so at a glance you can see how much of the board the cog knows: the design's "single most
important readout" is doing its job. The top band is the starter's scorebug — `SOLVED 1/5` as the
big numeral, caption `TASK 3/5 · TURN 7/11 · TICK 299 · SEEN 49/169 · SCORE 104000`, and a single
left plate reading `1/5 Carrying CARTOGRAPHER` over `ALPHA · SCORE 104000` with the carrying chip
showing `—`. The mission ribbon reads the sentence in full — *"get to the green goal square"* —
the five task pips are there in ladder order with the right semantics (red-slashed = failed,
green = solved, amber ring = current, hollow = pending), the `AGENT VIEW 7×7` inset draws the
agent-up window with `ALPHA · FACING E…` beneath it, and the bottom is the starter's transport
strip verbatim: restart / back / play / +5s / forward / loop / skip-lulls / `spoilers`, a
`158 / 315` tick readout, speed chips `1× 2× 3× 4× 8× 16×`, and the scrubber with beat markers in
red, orange and green above the `PROGRESS` momentum line. That is the paintbot/ctf chrome
family — transport strip, scrubber with momentum graph, scorebug, endcard machinery — with this
game's mission ribbon, task pips and 7 × 7 inset added, exactly as `design.md` §Chrome provenance
describes. It is not the cogame-gridlock failure mode.

It also **advances**: between the 0 % and 50 % readouts the clock moves from
`SOLVED 0/5 … TICK 141 … SCORE 0` to `SOLVED 1/5 … TICK 299 … SCORE 104000`, and that matches the
record — the replay's task 2 (`doorkey`) is the one solved, on turns 16–19, where the LLM says
*"Going to yellow locked door at (7,5) to open it with my yellow key"* and the plan is
`goto toggle`. The picture and the record agree.

**Three defects in what was rendered, all in the chrome, none fatal to "it draws":**
1. **The scrubber's click-to-seek is mis-scaled and the clock stops tracking the playhead.** In
   the screenshot — taken after the 100 % click — the transport reads `158 / 315`, i.e. the
   playhead sits at the *middle* of the timeline after a click at the far right edge of `#scrub`,
   while `#clock-caption` simultaneously reads `TICK 299 · SEEN 49/169 · SCORE 104000` (end-of-
   episode values, and `TASK 3/5` when the episode's last task was 5/5). The two readouts
   disagree with each other and neither follows the click. This is what produces the identical
   50 %/100 % rows above, and it reproduced on a second replay.
2. **The match feed is empty.** `feed_lines: 0` in all three runs, including the reading taken at
   the moment of load while the replay was auto-playing at tick 141, and no feed rows are visible
   anywhere in the frame. `design.md` readout 8 makes the feed the place *"where a spectator sees
   the LLM playing"* — the `say` lines quoted above never reach the screen.
3. **Cosmetic:** the five task-pip family captions overlap into an unreadable smear
   (`LAVAGDORMILET·KEYCORBABYAIR`) at 1280 px; the mission ribbon and the `AGENT VIEW 7×7` inset
   are drawn *over* the board's left edge rather than in the letterbox gutters; the line above the
   ribbon (`TASK n/5 · FAMILY`) is clipped by the top band; and three starter sprites 404
   (`soldier_red_front_gun.png`, `soldier_green_front.png`, `soldier_blue_front_gun.png`) with 22
   `Unknown sprite protocol message type: 34` warnings.

Status: **FALSE** — criterion (a) passes: `loaded: true` in 2 730 ms with
`data_replay_loaded: "true"` and no failure. Criterion (b) does **not**: the three clock readouts
do not differ — 50 % and 100 % are byte-identical, in three dispatched runs across two different
replays. Motion itself is proven (0 % → 50 %), so this is not the cogame-lantern "never draws a
frame" failure; it is the scrubber seek/clock defect described above, and by the rule as written
(`prompts/60-verify.md` §8: *"Item 8 is TRUE only if both hold"*) the item is false.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** (3 completed: 22:15:37Z, 22:32:00Z, 22:46:09Z) |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** (daveey #1, daveey-1 #3, 3 rounds each) |
| 3 | Latest round's episode requests completed w/ replay | **TRUE** |
| 4 | Replay bytes valid, protocol, reason, not all fallbacks | **TRUE** (`minigrid/v1`, `complete`, 46/46 and 35/36 llm) |
| 5 | Hosted game log clean | **FALSE** (1 `falling back` line, round 3 / daveey-1; not platform-wide) |
| 6 | Public page: featured match + static iframe src | **FALSE** (static path TRUE; featured match absent) |
| 7 | Certification declared the static bundle | **TRUE** |
| 8 | Viewer executed: loaded + advances + judgment | **FALSE** (`loaded:true`, but 50 % = 100 % readouts) |

For STATE:
- `verify.rounds`: `[{1,"round_d23b23fc-be7d-4e96-aa40-b147106b3eda"}, {2,"round_a4ab0f21-6588-4b6c-8eb0-5d25565535ee"}, {3,"round_aa501498-e555-4a71-b4cb-bae6c84076b1"}]`
- `verify.replay`: `https://softmax-public.s3.amazonaws.com/replays/5c5bd71e-0bbb-4f75-b114-e94f419e232d.replay` (round 2, daveey/cartographer — the replay check 8 rendered); latest round's champion replays are `5eb66cb5-6917-4dee-a4c5-3f00c60d27d8` (daveey) and `70a0e17b-ae6c-4f4f-99bd-cdf0e8b0ab61` (daveey-1)
- `verify.iframe_static`: `true`
- `verify.viewer_check_run`: `33217607488` (retries `33217711224`, `33217780204`)
