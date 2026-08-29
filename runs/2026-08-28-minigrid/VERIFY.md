# VERIFY — minigrid   (2026-08-29T06:45Z)

Verdict: **all-true** — checks 1–8 all TRUE.

**Round 3 — supersedes the 0.1.1 verification.** The previous verification of this run
(2026-08-29T02:15Z, preserved in git history) ran against release **0.1.1** / `cow_753b4d23` and
returned **one FALSE: check 5**. Its evidence was `falling back … (transport_timeout)` lines in
every round it sampled (4 in round 16, 4 in round 15, 5 in round 17) with **89/89 sidecar calls
returning HTTP 200** — a client-side deadline problem, not a provider problem. The cause it
identified: `attempt1Ms = 11000` had been derived from a *single-seat* latency distribution
(observed max 6 712 ms), but the four-lane redesign issues **three concurrent LLM calls per turn**,
which pushed batch p90 to ~10.1 s and the batch maximum to exactly 11 000 ms — the deadline itself.

What changed since: the **v2.1 design addendum** re-derived the ladder for three-concurrent-call
batches (`attempt1Ms 18000` / `retryMs 12000` / `turnBudgetMs 30000`, with `turnSpacingMs 11000`
left unchanged), made `fallbackCauses` record **both** attempts and added `retriedTurns`, added the
`goto` **Case C partial walk** (bumping the replay header's GameVersion to 3), re-pinned the
prompts, and fixed `replay_summary.py`'s slot ordering. That shipped as **0.1.2**
(`cow_70e4993f`, manifest `sha256:efc95d48…763e97`, release run `33230336307`), and the league
rolled over to **v3** policies at 2026-08-29T03:17Z. **All eight checks below were re-executed from
scratch** in this verifier session (2026-08-29 06:37Z – 06:45Z) against 0.1.2 and the v3 policy
set; nothing is carried over from round 2. Check 5 is now **TRUE**, and the round-2 non-check
finding about champion task-solving has substantially improved (see §4).

Run: `2026-08-28-minigrid` · slug `minigrid` · version `0.1.2`
`$COW` `cow_70e4993f-58ea-4678-8d19-ffa1866214b1`
`$L` `league_78d5b417-52a0-4459-8fd6-3b9aeacfe1ca`
`$D` `div_721f571a-ece7-4ed9-8b1c-15eb2cd072be`
manifest_sha `sha256:efc95d4886a5dfde4d7773c302ebe870e677bf1f48879f17d13e516566763e97`
repo `Metta-AI/cogame-minigrid` @ `85a2f68` (cloned fresh this session for `tools/replay_summary.py`)

**Qualifying rounds for every check are `round_number ≥ 22`** — round 22 was the first round
snapshotted with both **v3** champions after the 03:17Z rollover.

All ids read from `runs/2026-08-28-minigrid/STATE.json`. Documented exceptions to "fetch fresh":
**check 7** reads the committed `runs/2026-08-28-minigrid/release-result.json` (as
`prompts/60-verify.md` §7 directs), and **check 8**'s rendered evidence is the artifact of the
`viewer-check.yml` run this session dispatched at 06:41:25Z (run `33239074400`).

Headers on every Observatory call: `Authorization: Bearer $SOFTMAX_TOKEN` and
`User-Agent: coworld-builder/1.0`; `X-Use-Elevated-Privileges: true` added on the reads that
require it (`/artifacts/logs`, `/leagues/$L/filler-policies`). Values are never printed.

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_78d5b417-52a0-4459-8fd6-3b9aeacfe1ca
D=div_721f571a-ece7-4ed9-8b1c-15eb2cd072be
COW=cow_70e4993f-58ea-4678-8d19-ffa1866214b1
```

### API substitution used throughout (differs from the phase prompt)

`prompts/60-verify.md` §3 prints `GET $BASE/episode-requests?round_id=…`. That flat route no
longer accepts GET. Verified live this session before substituting:

```bash
curl -sS -D - "$BASE/episode-requests?round_id=round_f8ba8e4f-a3c2-4841-a4cb-59a03507c465&limit=20" "${AUTH[@]}"
```

```
HTTP 405
allow: POST
{"detail":"Method Not Allowed"}
```

Every episode-request lookup below therefore uses the **nested** route from
`playbooks/observatory-api.md` §9 (lines 153-154), `GET $BASE/rounds/$R/episode-requests`, which
returns HTTP 200. The individual `GET $BASE/episode-requests/$EREQ` and its `/artifacts/*`
subroutes are unaffected and were used as printed.

### Poll log (`prompts/60-verify.md` §Waiting; bound 75 min from 06:37Z, i.e. expiring 07:52Z)

| UTC | observation |
|---|---|
| 06:38:03Z | live filler set fetched — the **v3** pair, matching STATE |
| 06:38:0xZ | `/rounds` — **35** rounds, **all 35 `completed`**, zero failed/discarded; rounds 22–35 all carry the all-v3 entrant set. The ≥2 bound was already satisfied at the first poll |
| 06:38:18Z | leaderboard — both champions on their **v3** labels |
| 06:38:2x–06:38:39Z | round **35** (the latest completed, finished 06:37:18Z) episode request + replay bytes |
| 06:39–06:40Z | hosted logs fetched for **all 14** qualifying rounds (22–35) |
| 06:41:07Z | `softmax.com/minigrid` — featured match has already rolled to `minigrid.r35.e1` on `cow_70e4993f`/`0.1.2` |
| 06:41:17Z | replay-session endpoint → static viewer URL |
| 06:41:25Z | `viewer-check.yml` dispatched; run `33239074400` created 06:41:27Z, concluded `success` |
| 06:42:0xZ | `viewer-check` artifact downloaded and committed |

**Bound used: 5 of 75 minutes.** No waiting was needed — the ladder had already produced 14
qualifying rounds, and round 35 completed 45 s before the first poll (06:37:18.658Z vs 06:38:03Z). Checks 3, 4, 6 and 8 were
all executed against **round 35**, the same round the public page was featuring, so there is no
"moving target" caveat this time.

---

## 1. ≥2 completed rounds after the fillers were set

**TRUE** — **fourteen** qualifying rounds (22–35), all `completed`, all seating both v3 champions
against the live v3 filler set. No round in this league has ever been `failed` or `discarded`.

First, the live filler set — the "after the fillers were set" reference point. This read needs the
elevated header even though it is a read (`playbooks/observatory-api.md` §6):

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}" | jq .
```

Fetched 2026-08-29T06:38:03Z — HTTP 200:

```json
{
  "filler_policy_versions": [
    {
      "policy_version_id": "2b6d21f5-c38f-40f9-9b4b-940992d59558",
      "policy_id": "4551842d-05d0-4fd0-9aeb-bf6a8c7deefc",
      "policy_name": "minigrid-scout",
      "version": 3,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "display_name": null
    },
    {
      "policy_version_id": "8a3c9bde-be76-4b80-9001-40766483e943",
      "policy_id": "d885f184-1d7d-4eaf-ad0f-739597087f74",
      "policy_name": "minigrid-bumper",
      "version": 3,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "display_name": null
    }
  ]
}
```

Both uuids are exactly `STATE.policies.filler_version_ids`, both are **v3**, and neither is a
champion uuid. `log.md` records the v3 filler replacement at `2026-08-29T03:17:07Z`, immediately
before round 22.

Then the rounds:

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=40" "${AUTH[@]}" \
 | jq 'if type=="array" then . else .entries end | group_by(.status)|map({(.[0].status):length})|add'
```

Fetched 2026-08-29T06:38:0xZ — HTTP 200:

```json
{"completed": 35}
```

**35 rounds returned, all 35 `"status":"completed"`, all `"error": null`.** Zero `failed`, zero
`discarded`, so there is no `error` string to record verbatim. The v2 → v3 rollover is visible in
the entrant sets:

```bash
… | jq -r '…|sort_by(.round_number)|.[]|select(.round_number>=20)
            |[.round_number,.status,.completed_at,(.round_config.entrant_policy_version_ids|join(","))]|@tsv'
```

```
20  completed  2026-08-29T02:48:39.453278Z  52906971-…,bdf22f53-…,9b23f82c-…
21  completed  2026-08-29T03:03:26.157711Z  52906971-…,bdf22f53-…,9b23f82c-…
22  completed  2026-08-29T03:22:24.993091Z  489c3351-…,73a45366-…,9b23f82c-…   ← first all-v3 round
23  completed  2026-08-29T03:37:39.008517Z  489c3351-…,73a45366-…,9b23f82c-…
24  completed  2026-08-29T03:52:29.645112Z  489c3351-…,73a45366-…,9b23f82c-…
25  completed  2026-08-29T04:07:41.505662Z  489c3351-…,73a45366-…,9b23f82c-…
26  completed  2026-08-29T04:22:15.090524Z  489c3351-…,73a45366-…,9b23f82c-…
27  completed  2026-08-29T04:37:03.809184Z  489c3351-…,73a45366-…,9b23f82c-…
28  completed  2026-08-29T04:52:39.132243Z  489c3351-…,73a45366-…,9b23f82c-…
29  completed  2026-08-29T05:07:48.748070Z  489c3351-…,73a45366-…,9b23f82c-…
30  completed  2026-08-29T05:23:10.485474Z  489c3351-…,73a45366-…,9b23f82c-…
31  completed  2026-08-29T05:37:39.190794Z  489c3351-…,73a45366-…,9b23f82c-…
32  completed  2026-08-29T05:52:08.110258Z  489c3351-…,73a45366-…,9b23f82c-…
33  completed  2026-08-29T06:07:28.816515Z  489c3351-…,73a45366-…,9b23f82c-…
34  completed  2026-08-29T06:23:41.501155Z  489c3351-…,73a45366-…,9b23f82c-…
35  completed  2026-08-29T06:37:18.658481Z  489c3351-…,73a45366-…,9b23f82c-…
```

The uuids resolve, fetched fresh 2026-08-29T06:38:1xZ:

```bash
curl -sS "$BASE/policy-versions?limit=200" "${AUTH[@]}" \
 | jq -r '.[]|select(.policy_name!=null)|select(.policy_name|test("minigrid"))
          |[.policy_name,.version,.policy_version_id,.player_name]|@tsv' | sort
```

```
minigrid-bumper         3  8a3c9bde-be76-4b80-9001-40766483e943  daveey
minigrid-cartographer   3  489c3351-a8f6-41dd-8bd3-859f923a4807  daveey
minigrid-missionfirst   3  73a45366-9dae-4ff0-a16e-72ec8ebe2c92  daveey-1
minigrid-scout          3  2b6d21f5-c38f-40f9-9b4b-940992d59558  daveey
minigrid-bumper         2  d984c287-a3d7-4dcd-9248-f8200df6cc8a  daveey
minigrid-cartographer   2  52906971-a8a1-414d-b538-847d072173df  daveey
minigrid-missionfirst   2  bdf22f53-d38d-463b-b0ca-07deb733981c  daveey-1
minigrid-scout          2  1f17a736-1407-4eac-bde7-6400d0b3b0ed  daveey
```

so `489c3351` = `minigrid-cartographer:v3` (daveey) and `73a45366` = `minigrid-missionfirst:v3`
(daveey-1). The third uuid `9b23f82c` is the independent third-party entrant
`co-gas-minigrid-subgoal-router-richard:v1` (player `richard`), not a filler.

Corroboration that the **v3 filler pair** was actually seated in those rounds (the round config
lists only entrants; the filler shows up in the episode). Fetched 06:43:1xZ:

```bash
for e in ereq_c17d03a3-… ereq_ec136116-… ; do
  curl -sS "$BASE/episode-requests/$e" "${AUTH[@]}" \
   | jq -c '{status,[.participants[]|{position,policy_name,version,player_name,is_filler}]}'
done
```

```json
round 22 (ereq_c17d03a3-4a3e-41ea-8ac8-d702c2f59754): {"status":"completed","p":[
 {"position":0,"policy_name":"minigrid-cartographer","version":3,"player_name":"daveey","is_filler":false},
 {"position":1,"policy_name":"minigrid-missionfirst","version":3,"player_name":"daveey-1","is_filler":false},
 {"position":2,"policy_name":"co-gas-minigrid-subgoal-router-richard","version":1,"player_name":"richard","is_filler":false},
 {"position":3,"policy_name":"minigrid-bumper","version":3,"player_name":"daveey","is_filler":true}]}

round 34 (ereq_ec136116-6ae7-44f0-aab6-390b65e8cc7f): {"status":"completed","p":[
 {"position":0,"policy_name":"minigrid-cartographer","version":3,"player_name":"daveey","is_filler":false},
 {"position":1,"policy_name":"minigrid-missionfirst","version":3,"player_name":"daveey-1","is_filler":false},
 {"position":2,"policy_name":"co-gas-minigrid-subgoal-router-richard","version":1,"player_name":"richard","is_filler":false},
 {"position":3,"policy_name":"minigrid-bumper","version":3,"player_name":"daveey","is_filler":true}]}
```

Status: **TRUE** — the v3 filler pair (`minigrid-scout:v3`, `minigrid-bumper:v3`) is the live
filler set, set at 03:17:07Z; rounds **22 through 35** — fourteen rounds, the earliest completed
03:22:24Z and the latest 06:37:18Z — all completed after it was set and all seat both champions on
v3. That is seven times the required minimum of two. No round in the league failed or was
discarded.

---

## 2. Both champions ranked

**TRUE.**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq .
```

Fetched 2026-08-29T06:38:18Z — HTTP 200, bare JSON list (not `.entries`):

```json
[
  {"rank":1,"player_id":"ply_ded11f40-3e30-4921-b019-f7f6bc3e9c83","player_name":"richard",
   "score":1118.4206573845156,"score_label":"MMR","score_value_type":"integer",
   "rounds_played":33,"episode_wins":43.0,"episodes_played":null,
   "win_rate":0.6515151515151515,"policy_label":"co-gas-minigrid-subgoal-router-richard:v1",
   "recent_rounds":null},
  {"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
   "score":980.1472315227924,"score_label":"MMR","score_value_type":"integer",
   "rounds_played":35,"episode_wins":35.0,"episodes_played":null,
   "win_rate":0.5147058823529411,"policy_label":"minigrid-cartographer:v3",
   "recent_rounds":null},
  {"rank":3,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
   "score":901.4321110926909,"score_label":"MMR","score_value_type":"integer",
   "rounds_played":35,"episode_wins":23.0,"episodes_played":null,
   "win_rate":0.3382352941176471,"policy_label":"minigrid-missionfirst:v3",
   "recent_rounds":null}
]
```

as the prompt's `@tsv` projection:

```
rank  player_name  policy_label                                 score     rounds  wins
1     richard      co-gas-minigrid-subgoal-router-richard:v1    1118.421  33      43.0
2     daveey       minigrid-cartographer:v3                      980.147  35      35.0
3     daveey-1     minigrid-missionfirst:v3                      901.432  35      23.0
```

Status: **TRUE** — `daveey` (rank 2, `minigrid-cartographer:v3`, `rounds_played` 35) and
`daveey-1` (rank 3, `minigrid-missionfirst:v3`, `rounds_played` 35) are both present with
`rounds_played ≥ 1`, both carrying their **v3** labels. The two filler policies
(`minigrid-scout`, `minigrid-bumper`) are **absent** from the leaderboard entirely — the stronger
of the two conditions the check allows. `richard` at rank 1 is an independent third-party entrant
(`ply_ded11f40`), not a filler and not one of this run's policies.

---

## 3. The latest round's episode request completed with a replay

**TRUE.** Latest completed round = **35** (`round_f8ba8e4f-a3c2-4841-a4cb-59a03507c465`, completed
2026-08-29T06:37:18.658481Z) — and it stayed the latest for the whole session, so unlike round 2
there is no "executed against an older round" caveat.

```bash
R=round_f8ba8e4f-a3c2-4841-a4cb-59a03507c465
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" \
 | jq -c '{count:(.entries|length), ids:[.entries[].id], status:[.entries[].status]}'
```

Fetched 2026-08-29T06:38:2xZ — HTTP 200:

```json
{"count":1,"ids":["ereq_3d489c10-6032-4824-a88d-54459f0b25ab"],"status":["completed"]}
```

```bash
curl -sS "$BASE/episode-requests/ereq_3d489c10-6032-4824-a88d-54459f0b25ab" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```

Fetched 2026-08-29T06:38:39Z — HTTP 200:

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/2e5030b6-fdcd-422a-9d4a-c1c6d6eeed9e.replay",
  "participants": [
    {"position":0,"kind":"policy","policy_version_id":"489c3351-a8f6-41dd-8bd3-859f923a4807",
     "policy_id":"4ffce33f-34cc-46bc-94af-d408bf46cd32","policy_name":"minigrid-cartographer",
     "version":3,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
     "is_filler":false,"is_seed":false},
    {"position":1,"kind":"policy","policy_version_id":"73a45366-9dae-4ff0-a16e-72ec8ebe2c92",
     "policy_id":"b590fcad-8703-4277-97d0-56e868f24ae7","policy_name":"minigrid-missionfirst",
     "version":3,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
     "is_filler":false,"is_seed":false},
    {"position":2,"kind":"policy","policy_version_id":"9b23f82c-29fc-4167-a802-1cf15eca7c53",
     "policy_id":"8027bb2d-b1d4-4b78-acc3-5bb9a53541d6",
     "policy_name":"co-gas-minigrid-subgoal-router-richard","version":1,
     "player_id":"ply_ded11f40-3e30-4921-b019-f7f6bc3e9c83","player_name":"richard",
     "is_filler":false,"is_seed":false},
    {"position":3,"kind":"policy","policy_version_id":"2b6d21f5-c38f-40f9-9b4b-940992d59558",
     "policy_id":"4551842d-05d0-4fd0-9aeb-bf6a8c7deefc","policy_name":"minigrid-scout",
     "version":3,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
     "is_filler":true,"is_seed":false}
  ],
  "participant_scores": [
    {"position":0,"score":105050.0},
    {"position":1,"score":106050.0},
    {"position":2,"score":107050.0},
    {"position":3,"score":414090.0}
  ]
}
```

Status: **TRUE** — `status == "completed"`, `replay_url` non-null, and the participants name
**`daveey`** (position 0, cartographer **v3**) and **`daveey-1`** (position 1, missionfirst **v3**),
plus the third-party `richard` and one filler seat carrying `"is_filler": true`
(`minigrid-scout:v3`). The four `participant_scores` match the replay's `results.scores`
`[105050, 106050, 107050, 414090]` exactly (§4), so the API record and the replay agree.

---

## 4. The replay bytes are valid and show the game

**TRUE.**

The minigrid replay is a **binary `COWLDMGD`** container, not JSON, so `jq -e .` on the raw bytes
is not the right strict parser — the repo ships `tools/replay_summary.py` for exactly this and the
design note declares it the phase-60 evidence path (`design.md:1208-1220`). Both facts were
re-established from the bytes this session:

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/2e5030b6-fdcd-422a-9d4a-c1c6d6eeed9e.replay" \
     -o /tmp/ep.replay
python3 -c "d=open('/tmp/ep.replay','rb').read(); print(d[:48].hex()); d.decode('utf-8')"
```

```
HTTP 200 bytes 154361
434f574c444d4744010008006d696e6967726964010033f8f5374ca0010000af027b2273656564223a31323738373336
printable:  COWLDMGD....minigrid..3..7L......{"seed":1278736
replay bytes decode as UTF-8: no — 'utf-8' codec can't decode byte 0xf8 in position 23
```

The header decodes as magic `COWLDMGD`, format version `1`, length-prefixed gameName `minigrid`
(len 8), length-prefixed **gameVersion `3`** (len 1) — the v2.1 build, exactly as the addendum
declared. Then the strict parse of the summary:

```bash
python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json   # repo @ 85a2f68
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
```

```
strict UTF-8 JSON: ok
```

```bash
jq -c '{protocol, gameVersion, variant, seed, tickCount,
        reason:.results.reason, endRule:.results.endRule,
        names:.results.names, aliases:.results.aliases, policyKinds:.results.policyKinds,
        llmTurns:.results.llmTurns, fallbackTurns:.results.fallbackTurns,
        fallbackCauses:.results.fallbackCauses, retriedTurns:.results.retriedTurns,
        tasksSolved:.results.tasksSolved, scores:.results.scores,
        turnsPlayed:.results.turnsPlayed, deaths:.results.deaths,
        crashes:.results.crashes, actionsDropped:.results.actionsDropped}' /tmp/ep.json
```

```json
{"protocol":"minigrid/v1","gameVersion":"3","variant":"gauntlet","seed":1278736055,
 "tickCount":578,"reason":"complete","endRule":"allLanesComplete",
 "names":["cartographer","missionfirst","prompt","scout"],
 "aliases":["Alpha","Beta","Gamma","Delta"],
 "policyKinds":["llm","llm","llm","scripted"],
 "llmTurns":[25,21,21,0],"fallbackTurns":[0,0,0,0],
 "fallbackCauses":[{},{},{},{}],"retriedTurns":[0,0,0,0],
 "tasksSolved":[1,1,1,4],"scores":[105050,106050,107050,414090],
 "turnsPlayed":25,"deaths":[0,1,1,0],"crashes":[0,0,0,0],
 "actionsDropped":[0,0,0,0]}
```

`results.reason == "complete"` (not `deadline`), so no documented exception is needed.
`policyKinds` is now seat-ordered — the round-2 cosmetic ordering bug the v2.1 addendum listed is
fixed.

**Honesty note on `protocol`.** `protocol: "minigrid/v1"` is emitted as a **constant** by
`tools/replay_summary.py` (line 79: `protocol = "minigrid/v1"`); it is not read out of the replay
bytes. The bytes' own game identity is the header decoded above — gameName `minigrid`,
gameVersion `3` — which matches the manifest's `game.name` (`coworld_manifest_template.json`
→ `"name": "minigrid"`) and the v2.1 addendum's GameVersion bump. The `minigrid/v1` string is
pinned by the repo in two places that gate every build:
`tests/test_minigrid_replay.nim:178` and `.github/workflows/ci.yml:252`
(`assert summary["protocol"] == "minigrid/v1"`). Recording this so nobody reads the tool constant
as an independent measurement.

Decision counts and the fallback minority:

```bash
jq -c '[.plans[]|.source]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.json
jq -c '{plansBySeat:(.plansBySeat|map(length)), fallbacks:(.fallbacks|length), budgetGuards:(.budgetGuards|length)}' /tmp/ep.json
```

```json
{"llm":67,"scripted":21}
{"plansBySeat":[25,21,21,21],"fallbacks":0,"budgetGuards":0}
```

**88 recorded decisions, 67 of them LLM directives and ZERO fallbacks** — 0.0 %. Not "a small
minority": none.

| seat | alias | policy | kind | LLM turns | fallback turns | retried turns | causes |
|---|---|---|---|---|---|---|---|
| 0 | Alpha | `minigrid-cartographer:v3` (daveey) | llm | 25 | **0** | 0 | `{}` |
| 1 | Beta | `minigrid-missionfirst:v3` (daveey-1) | llm | 21 | **0** | 0 | `{}` |
| 2 | Gamma | `co-gas-…-richard:v1` (third party) | llm | 21 | **0** | 0 | `{}` |
| 3 | Delta | `minigrid-scout:v3` (filler) | scripted | 0 | 0 | 0 | `{}` |

The champion decisions are non-scripted and non-trivial. Early, middle and late excerpts of
`.plans[]` (`turn`, seat/alias, `source`, executed-primitive count, `say`):

```
=== EARLY (turns 1–3) ===
 1  0 Alpha/cartographer     llm       ex=4   Turn 1: Exploring north into the ? region to find the green goal.
 1  1 Beta/missionfirst      llm       ex=8   get to green goal square; not seen yet; exploring south and east
 1  2 Gamma/prompt(richard)  llm       ex=12  Exploring south along lava boundary to find the gap and the goal.
 1  3 Delta/scout(filler)    scripted  ex=7
 2  0 Alpha/cartographer     llm       ex=4   Turning north to explore the ? region, crossing into unknown
 2  1 Beta/missionfirst      llm       ex=15  get to green goal; crossing south to explore, then east around lava
 3  0 Alpha/cartographer     llm       ex=6   Exploring north into ? region to find the green goal.
=== MIDDLE (turns 12–14) ===
12  0 Alpha/cartographer     llm       ex=14  Going to yellow door with key, opening it, then exploring beyond to fi…
12  1 Beta/missionfirst      llm       ex=11  use yellow key to open door, then get to green goal; key carried; door…
12  2 Gamma/prompt(richard)  llm       ex=20  Unlocking yellow door at (5,1) then exploring for goal
13  2 Gamma/prompt(richard)  llm       ex=9   Crossing room boundary at blue door (6,2), moving east into room 1.
14  1 Beta/missionfirst      llm       ex=8   get to the green goal square; G unseen; sweeping north to edge then ea…
=== LATE (turns 24–25) ===
24  0 Alpha/cartographer     llm       ex=4   Final turn: rotating to explore south before timer ends. Blue ball loc…
24  1 Beta/missionfirst      llm       ex=24  pick up blue ball; not located; final sweep east
24  2 Gamma/prompt(richard)  llm       ex=4   Final turn: moving to red locked door at (7,10) and attempting toggle.
25  0 Alpha/cartographer     llm       ex=3   Green ball found at (10,2). Moving there now.
25  1 Beta/missionfirst      llm       ex=4   go to the green ball; found at (10,2); moving to it now
25  2 Gamma/prompt(richard)  llm       ex=3   Green ball visible at (10,2). Moving to pickup to complete go-to-green…
```

The seats read the mission sentence, name the objective, cite coordinates they have discovered,
and issue movement/toggle/pickup verbs against it. Per-seat action work:

```json
seat 0 (cartographer): {"plans":25,"verbs":158,"executed":195,"unreachable":0,"dropped":0,"says":25}
seat 1 (missionfirst):  {"plans":21,"verbs":237,"executed":295,"unreachable":1,"dropped":0,"says":21}
seat 2 (richard):       {"plans":21,"verbs":126,"executed":166,"unreachable":1,"dropped":0,"says":21}
seat 3 (scout filler):  {"plans":21,"verbs":55, "executed":179,"unreachable":0,"dropped":0,"says":0}
```

and the game's own outcome record shows the five-task gauntlet being worked:

```json
"taskFamilies":["lavagap","doorkey","multiroom","keycorridor","babyai"],
"taskMissions":["get to the green goal square",
                "use the yellow key to open the door and then get to the green goal square",
                "get to the green goal square","pick up the blue ball","go to the green ball"],
"taskOutcome":[["timeout","timeout","timeout","timeout","solved"],
               ["died","timeout","timeout","timeout","solved"],
               ["died","timeout","timeout","timeout","solved"],
               ["solved","solved","solved","timeout","solved"]],
"tasksSolved":[1,1,1,4],"progressTotal":[5,6,7,14],"speedTotal":[5,5,5,9],
"doorsOpened":[0,1,2,7],"objectsPickedUp":[1,1,1,2],
"primitivesExecuted":[194,284,165,178],
"macrosUnreachable":[0,1,1,0],"macrosPartial":[1,4,1,0],
"repliesRepaired":[0,0,0,0],"crashes":[0,0,0,0],
"finalTick":578,"winner":3,"win":[false,false,false,true],"laneEndRule":["gauntletComplete","gauntletComplete","gauntletComplete","gauntletComplete"]
```

The protocol's score identity holds for every seat (checked, not assumed):

```
seat 0  scores 105050  expected 100000*1 + 1000*5  + 10*5 = 105050  ok
seat 1  scores 106050  expected 100000*1 + 1000*6  + 10*5 = 106050  ok
seat 2  scores 107050  expected 100000*1 + 1000*7  + 10*5 = 107050  ok
seat 3  scores 414090  expected 100000*4 + 1000*14 + 10*9 = 414090  ok
```

### Corroboration — every qualifying round, not just the latest

All 14 qualifying replays were downloaded and strict-parsed (each HTTP 200, each
`jq -e .` ok):

```
rnd  protocol      gv  reason    fallbackTurns  retriedTurns  tasksSolved  maxBatchLatMs  llmPlans  fallbackPlans
22   minigrid/v1   3   complete  [0,0,0,0]      [0,0,0,0]     [1,0,1,0]    10139          81        0
23   minigrid/v1   3   complete  [0,0,0,0]      [0,0,0,0]     [0,1,0,0]    11746          86        0
24   minigrid/v1   3   complete  [0,0,0,0]      [0,0,0,0]     [1,1,1,3]    10353          75        0
25   minigrid/v1   3   complete  [0,0,0,0]      [0,1,0,0]     [1,1,1,3]    11937          76        0
26   minigrid/v1   3   complete  [0,0,0,0]      [0,0,1,0]     [0,0,0,3]    11589          82        0
27   minigrid/v1   3   complete  [0,0,0,0]      [0,0,0,0]     [1,1,3,1]    10920          69        0
28   minigrid/v1   3   complete  [0,0,0,0]      [0,0,0,0]     [1,1,0,0]    11440          78        0
29   minigrid/v1   3   complete  [0,0,0,0]      [0,0,0,0]     [2,1,1,4]    12210          80        0
30   minigrid/v1   3   complete  [0,0,0,0]      [0,0,0,0]     [1,1,2,4]    12275          71        0
31   minigrid/v1   3   complete  [0,0,0,0]      [0,0,0,0]     [1,1,0,0]    11566          82        0
32   minigrid/v1   3   complete  [0,0,0,0]      [0,0,0,0]     [2,1,1,0]    10764          72        0
33   minigrid/v1   3   complete  [0,0,0,0]      [0,0,0,0]     [2,1,2,0]    12477          65        0
34   minigrid/v1   3   complete  [0,0,0,0]      [0,0,0,0]     [0,0,0,0]     9917          87        0
35   minigrid/v1   3   complete  [0,0,0,0]      [0,0,0,0]     [1,1,1,4]    12000          67        0
```

**1 071 LLM decisions across the fourteen qualifying rounds. Zero fallback plans. Zero fallback
turns. Every episode `reason: complete`.**

Status: **TRUE** — strict-UTF-8 JSON parse ok; the container header carries `minigrid` /
GameVersion 3 matching the manifest, and `protocol` is the repo-pinned `minigrid/v1`;
`results.reason == "complete"`; 67 LLM decisions and **zero** fallbacks in the latest round, and
zero across all 1 071 LLM decisions in all fourteen qualifying rounds. Fallbacks are not a small
minority — they are absent.

**Round-2 follow-up: champion task-solving (bears on "non-trivial content").** Round 2 reported
champions solving **0 of 5** tasks with `macrosUnreachable = 6` each, while the scripted filler
solved 3 — the `goto` macro was not resolving. The 0.1.2 Case C partial walk changed that. Solves
per round across the fourteen qualifying rounds:

```
Alpha  cartographer (daveey)    [1,0,1,1,0,1,1,2,1,1,2,2,0,1]   total 14   mean 1.00
Beta   missionfirst (daveey-1)  [0,1,1,1,0,1,1,1,1,1,1,1,0,1]   total 11   mean 0.79
Gamma  richard (third party)    [1,0,1,1,0,3,0,1,2,0,1,2,0,1]   total 13   mean 0.93
Delta  scripted filler          [0,0,3,3,3,1,0,4,4,0,0,0,0,4]   total 22   mean 1.57
```

and the macro accounting that explains it:

```
rnd  macrosUnreachable  macrosPartial      (round 2, v2 build: champions were [6,6,…] / [0,0,…])
22   [0,0,0,0]          [3,1,1,0]
23   [2,4,0,0]          [0,12,0,0]
24   [1,1,0,0]          [1,6,1,0]
29   [1,1,1,0]          [0,3,2,0]
33   [0,0,1,0]          [3,1,1,0]
35   [0,1,1,0]          [1,4,1,0]
```

`macrosUnreachable` for the champions has fallen from a flat 6 per episode to 0–5 (median 1), and
`macrosPartial` — the Case C counter, which did not exist in 0.1.1 — is now firing 1–12 times per
episode. Each champion now solves at least one task in **11 of the 14** qualifying rounds, and each
out-solves the scripted filler in **5** of them. The filler still has the higher mean (1.57 vs 1.00
/ 0.79), so the LLM champions have not overtaken their own baseline; that
remains a policy-quality observation for phase 30, not a definition-of-done item. But the
round-2 failure mode — champions solving *nothing* — is gone.

---

## 5. The hosted game log is clean

**TRUE.** Not one matching line in **any** of the fourteen qualifying rounds. This is the check
round 2 found FALSE; the v2.1 ladder fixed it.

The logs body is python `b'…'` byte-string reprs under `===== container: <name> =====` headers, so
every body was decoded with `ast.literal_eval` per repr **before** grepping
(`playbooks/observatory-api.md` §10) — a line-based grep on the raw bytes undercounts.

### Attempt 1 — the latest round's episode request (round 35)

```bash
curl -sS "$BASE/episode-requests/ereq_3d489c10-6032-4824-a88d-54459f0b25ab/artifacts/logs" \
     "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs35.raw          # HTTP 200, 8946 bytes
python3 declog.py /tmp/logs35.raw > /tmp/logs35.txt        # ast.literal_eval per b'…' repr
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs35.txt \
  || echo CLEAN
```

Fetched 2026-08-29T06:39:2xZ:

```
CLEAN
```

The whole `game` container, verbatim and complete — there is nothing elided here:

```
minigrid llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
minigrid: serving on 0.0.0.0:8080 seed 1278736055 variant gauntlet
minigrid: player connected on slot 2
minigrid: player connected on slot 3
minigrid: player connected on slot 0
minigrid: seat 2 registered as prompt (llm)
minigrid: seat 3 registered as scout (scripted)
minigrid: seat 0 registered as cartographer (llm)
minigrid: player connected on slot 1
minigrid: seat 1 registered as missionfirst (llm)
Dropped message to disconnected client
minigrid: episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 1/5 (105050) Beta 1/5 (106050) Gamma 1/5 (107050) Delta 4/5 (414090)
```

No `attempt 1 failed`, no `attempt 2 failed`, no `falling back`. Compare round 2's round-16
container, which carried nine attempt-failure lines and four `falling back` lines.

### Attempt 2 (and 3, and 4 … ) — every qualifying round, 22 through 35

Rather than sample three rounds, all fourteen qualifying rounds were fetched. Same decode, same
grep, one row per round:

```bash
while read -r n rid e; do
  curl -sS "$BASE/episode-requests/$e/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o logs_r$n.raw
  python3 declog.py logs_r$n.raw > logs_r$n.txt
  grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs_r$n.txt
  grep -c 'openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"' logs_r$n.txt
  grep -cE 'HTTP/1.1 (4|5)[0-9][0-9]' logs_r$n.txt
done < ereqs.tsv
```

Fetched 2026-08-29T06:39–06:40Z, every request HTTP 200:

```
r22  http=200  matches=0  sidecar200s=81  non2xx=0  episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 1/5 (104030) Beta 0/5 (5000) Gamma 1/5 (107000) Delta 0/5 (3000)
r23  http=200  matches=0  sidecar200s=86  non2xx=0  episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 0/5 (5000) Beta 1/5 (105010) Gamma 0/5 (4000) Delta 0/5 (1000)
r24  http=200  matches=0  sidecar200s=75  non2xx=0  episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 1/5 (103030) Beta 1/5 (104040) Gamma 1/5 (107000) Delta 3/5 (313040)
r25  http=200  matches=0  sidecar200s=77  non2xx=0  episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 1/5 (104030) Beta 1/5 (105000) Gamma 1/5 (106020) Delta 3/5 (313070)
r26  http=200  matches=0  sidecar200s=83  non2xx=0  episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 0/5 (2000) Beta 0/5 (5000) Gamma 0/5 (6000) Delta 3/5 (313060)
r27  http=200  matches=0  sidecar200s=69  non2xx=0  episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 1/5 (103050) Beta 1/5 (106050) Gamma 3/5 (309060) Delta 1/5 (104050)
r28  http=200  matches=0  sidecar200s=78  non2xx=0  episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 1/5 (106020) Beta 1/5 (103030) Gamma 0/5 (7000) Delta 0/5 (2000)
r29  http=200  matches=0  sidecar200s=80  non2xx=0  episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 2/5 (206050) Beta 1/5 (106000) Gamma 1/5 (107040) Delta 4/5 (414090)
r30  http=200  matches=0  sidecar200s=71  non2xx=0  episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 1/5 (106030) Beta 1/5 (103020) Gamma 2/5 (206060) Delta 4/5 (414090)
r31  http=200  matches=0  sidecar200s=82  non2xx=0  episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 1/5 (105030) Beta 1/5 (106030) Gamma 0/5 (4000) Delta 0/5 (3000)
r32  http=200  matches=0  sidecar200s=72  non2xx=0  episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 2/5 (207020) Beta 1/5 (106010) Gamma 1/5 (108030) Delta 0/5 (2000)
r33  http=200  matches=0  sidecar200s=65  non2xx=0  episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 2/5 (207050) Beta 1/5 (104050) Gamma 2/5 (207070) Delta 0/5 (3000)
r34  http=200  matches=0  sidecar200s=87  non2xx=0  episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 0/5 (3000) Beta 0/5 (0) Gamma 0/5 (5000) Delta 0/5 (1000)
r35  http=200  matches=0  sidecar200s=67  non2xx=0  episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 1/5 (105050) Beta 1/5 (106050) Gamma 1/5 (107050) Delta 4/5 (414090)
```

**Fourteen rounds. Zero matching lines. 1 073 sidecar calls, 1 073 × HTTP 200, zero non-2xx.**

```bash
cat logs_r2[2-9].txt logs_r3[0-5].txt | grep -c 'openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"'  # 1073
cat logs_r2[2-9].txt logs_r3[0-5].txt | grep -cE 'HTTP/1.1 (4|5)[0-9][0-9]'                        # 0
```

### The two attempt-level lines that do exist — and why they are not matches

Two of the fourteen rounds contain one `attempt 1 failed, will retry` line each. Neither is
matched by the check's pattern, and in both the **retry succeeded**, so no `falling back` line
followed. Verbatim `game` containers:

```
=== r25 game container (excerpt) ===
minigrid llm: seat 1 attempt 1 failed, will retry (schema_error): reply has neither actions nor say
minigrid: episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 1/5 (104030) Beta 1/5 (105000) Gamma 1/5 (106020) Delta 3/5 (313070)

=== r26 game container (excerpt) ===
minigrid llm: seat 2 attempt 1 failed, will retry (schema_error): reply has neither actions nor say
minigrid: episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 0/5 (2000) Beta 0/5 (5000) Gamma 0/5 (6000) Delta 3/5 (313060)
```

The replays record exactly these two events under the v2.1 `retriedTurns` counter and **not** in
`fallbackCauses` — `r25.results.retriedTurns == [0,1,0,0]`, `r26.results.retriedTurns ==
[0,0,1,0]`, both with `fallbackTurns == [0,0,0,0]` and `fallbackCauses == [{},{},{},{}]`. That is
the semantics `docs/PROTOCOL.md` now states: *"a turn whose attempt 1 failed and whose attempt 2
SUCCEEDED is counted instead by `retriedTurns[s]` and stays out of the map."* The round-2 finding
that `fallbackCauses` silently dropped the first attempt's cause is addressed by the same change.

### Why the ladder now holds — the number the v2.1 addendum was derived from

Per-turn batch latency (`plans[].latency_ms` is the wall clock of the whole concurrent LLM batch
and is identical across the seats of a turn), round 35, all 25 turns:

```
turn  seats  ms       turn  seats  ms       turn  seats  ms
 1     3     6275     10     3     7691     19     3     4470
 2     3     5710     11     3     5070     20     3     9027
 3     1     4259     12     3     7114     21     3     5955
 4     1     1831     13     3     2313     22     3    12000
 5     1     4031     14     3     8197     23     3     2988
 6     1     1992     15     3     4892     24     3     9605
 7     3     7007     16     3     8932     25     3     4121
 8     3     4944     17     3     5696
 9     3     5331     18     3     9896
```

```
round 35, LLM plans (n=67):                  min 1831  p50 5710  p90 9605  max 12000
round 35, three-concurrent-call turns (n=21): min 2313  p50 5955  p90 9605  max 12000
across all 14 qualifying rounds, per-round max batch latency:
  10139 11746 10353 11937 11589 10920 11440 12210 12275 11566 10764 12477  9917 12000
  → OVERALL MAXIMUM 12 477 ms   (round 33)
```

`attempt1Ms` is **18 000 ms**. The worst batch observed in fourteen consecutive production rounds
is **12 477 ms** — **5 523 ms of headroom, 1.44×**. Under 0.1.1's `attempt1Ms = 11 000`, **nine of
these fourteen rounds** (23, 25, 26, 28, 29, 30, 31, 33, 35) had a batch that exceeded the old
deadline and would have produced fallbacks; the round-2 distribution was right-censored *at* that
deadline, exactly as the v2.1 addendum argued (`design.md:2875` — *"The 11.0 s maximum is
right-censored at `attempt1Ms`"*). The shipped ladder is confirmed in the manifest the release was
cut from:

```bash
grep -o '"attempt1Ms": [0-9]*\|"retryMs": [0-9]*\|"turnBudgetMs": [0-9]*\|"turnSpacingMs": [0-9]*\|"num_agents": [0-9]*' coworld_manifest_template.json | sort -u
```

```
"attempt1Ms": 18000
"num_agents": 4
"retryMs": 12000
"turnBudgetMs": 30000
"turnSpacingMs": 11000
```

### Documented-exception rules — not invoked, and not needed

`prompts/60-verify.md` §5 allows one documented exception, for `LLM provider is unavailable` as a
platform-wide Bedrock **capacity** symptom cross-checked against another LLM coworld. That string
does not appear in any of the fourteen logs, and no exception of any kind is being claimed here:
the grep is genuinely empty. No cross-check against another coworld was required, and none is
being offered as a substitute for evidence.

Status: **TRUE** — CLEAN in all fourteen qualifying rounds (22–35), including the latest round 35
fetched ~2 minutes after it completed. 1 073 sidecar calls, all HTTP 200, zero non-2xx, zero
`falling back`, zero `LLM provider is unavailable`, zero `cut off at max_tokens`, zero `rejected`.
Two `schema_error` retries in fourteen rounds, both recovered on attempt 2 and both correctly
booked to `retriedTurns` rather than to `fallbackCauses`.

---

## 6. The public page uses the static replay path

**TRUE.** Source used: **the SSR payload of `https://softmax.com/minigrid` plus the replay-session
endpoint the page's own JS calls** — the raw-HTML iframe grep finds nothing, which
`prompts/60-verify.md` §6 and `playbooks/observatory-api.md` §Featured match both direct is to be
treated as *unknown*, not as a failure.

```bash
curl -sS "https://softmax.com/minigrid" -o /tmp/page.html
grep -o '<iframe[^>]*src="[^"]*"' /tmp/page.html || echo "NO IFRAME IN RAW HTML"
grep -c 'iframe' /tmp/page.html
```

Fetched 2026-08-29T06:41:07Z:

```
HTTP 200 bytes 772671
NO IFRAME IN RAW HTML
0
```

(`iframe` appears 0 times in the whole document; the page is client-rendered, as the lighthouse
run recorded.) The featured match **is** server-rendered into the SSR payload at
`state.playlist[0]` — unescaped excerpt from the same 06:41:07Z fetch:

```json
"state":{"leagueId":"league_78d5b417-52a0-4459-8fd6-3b9aeacfe1ca",
 "playlist":[{"episodeId":"ee79bb23-f432-4d70-9794-4614250bea42",
   "coworldId":"cow_70e4993f-58ea-4678-8d19-ffa1866214b1",
   "coworldName":"minigrid","coworldVersion":"0.1.2",
   "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/2e5030b6-fdcd-422a-9d4a-c1c6d6eeed9e.replay",
   "finishedAt":"2026-08-29T06:37:11.414022Z","roundNumber":35,"episodeNumber":1,
   "code":"minigrid.r35.e1",
   "matchup":{"divisionId":"div_721f571a-ece7-4ed9-8b1c-15eb2cd072be","divisionName":"Competition",
     "first":{"rank":1,"player_id":"ply_ded11f40-…","player_name":"richard","score":1118.4206573845156,
              "score_label":"MMR","rounds_played":33,"episode_wins":43,"win_rate":0.6515151515151515,
              "policy_label":"co-gas-minigrid-subgoal-router-richard:v1"},
     "second":{"rank":2,"player_id":"ply_44ae9048-…","player_name":"daveey","score":980.1472315227924,
               "score_label":"MMR","rounds_played":35,"episode_wins":35,"win_rate":0.5147058823529411,
               "policy_label":"minigrid-cartographer:v3"}},
   "inspectUrl":"/observatory/v2?tab=overview&detail=episode-request:ereq_3d489c10-6032-4824-a88d-54459f0b25ab",
   "outcome":null}],
 "pool":{"replays":[{"kind":"replay","round":{"id":"round_f8ba8e4f-a3c2-4841-a4cb-59a03507c465",
   "round_number":35,"commissioner_key":"platform","execution_backend":"dispatch", …
```

**A featured match is present** — `minigrid.r35.e1`, on `cow_70e4993f` / **`0.1.2`**, and it is the
**qualifying round 35 episode** verified in §§3–5 (same `episodeId` replay, same `ereq_3d489c10…`
in `inspectUrl`). The 0.1.1 `cow_753b4d23` route the brief warned about is **not** what the page
serves; the playlist had already rolled to 0.1.2. A two-player matchup card is attached.

The iframe `src` is produced by the call the page's JS makes:

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_70e4993f-58ea-4678-8d19-ffa1866214b1",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/2e5030b6-fdcd-422a-9d4a-c1c6d6eeed9e.replay"}'
```

Fetched 2026-08-29T06:41:17Z — HTTP 200:

```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_70e4993f-58ea-4678-8d19-ffa1866214b1/sha256%3Aefc95d4886a5dfde4d7773c302ebe870e677bf1f48879f17d13e516566763e97/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F2e5030b6-fdcd-422a-9d4a-c1c6d6eeed9e.replay",
  "ready": true
}
```

Decomposed:

| part | value | required |
|---|---|---|
| route | `/v2/coworlds/replays/static/…/index.html` | static route ✔ (no `/client/replay` anywhere) |
| `<cow_id>` | `cow_70e4993f-58ea-4678-8d19-ffa1866214b1` | = STATE `coworld.cow_id` (0.1.2) ✔ |
| `<sha>` | `sha256%3Aefc95d4886a5dfde4d7773c302ebe870e677bf1f48879f17d13e516566763e97` | = the coworld's `manifest_hash` ✔ |
| replay | `#replay=…2e5030b6-fdcd-422a-9d4a-c1c6d6eeed9e.replay` | the round-35 replay, URL-encoded fragment form ✔ |
| `ready` | `true` | static delivery ✔ |

The URL-encoded **fragment** (`?v=2#replay=`) rather than `?replay=` is the documented 2026-08-28
change (`playbooks/observatory-api.md:326`); both are the static route.

Independently, the coworld detail API confirms `cow_70e4993f` is the canonical `minigrid` at
`0.1.2` and that its `manifest_hash` is the sha in that path (fetched 06:41:1xZ):

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end|.[]|select(.name=="minigrid")|{id,version,canonical,manifest_hash}'
```

```json
{"id":"cow_70e4993f-58ea-4678-8d19-ffa1866214b1","version":"0.1.2","canonical":true,
 "manifest_hash":"sha256:efc95d4886a5dfde4d7773c302ebe870e677bf1f48879f17d13e516566763e97"}
{"id":"cow_753b4d23-00cd-417a-99eb-b643f0f0f526","version":"0.1.1","canonical":false,
 "manifest_hash":"sha256:fdd3b4cbd21f370c1639693a1001400fb80e3c8a7542ec9fae9b7581dc656032"}
{"id":"cow_5201d3e2-0aa8-45ef-b6de-ebd76a45f329","version":"0.1.0","canonical":false,
 "manifest_hash":"sha256:90039809a9670a2d6c5c8a0769b2d1cf92da10c8bbcf7e8b8fbf1d2e417b09c4"}
```

(The `/coworlds` list returns a **bare array**, not `{entries:…}`; the 0.1.0 and 0.1.1 coworlds are
still listed but `canonical: false`. `featured_match` is not a key on these rows at all — the SSR
payload is the source, as the playbook records.)

Status: **TRUE** — a featured match is present (`minigrid.r35.e1`), it is a **qualifying** round on
the **current** coworld, and its iframe `src` is the static route carrying `cow_70e4993f` and the
0.1.2 manifest sha with `ready: true`. No `/client/replay` anywhere.

---

## 7. Certification declared the static bundle

**TRUE.** Source read: **the committed `runs/2026-08-28-minigrid/release-result.json`** in this
repo (the copy phase 40 wrote for release 0.1.2) — not `/tmp`, and no re-download was needed.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-28-minigrid/release-result.json
```

```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Contains the required `Replay liveness: skipped (static replay bundle declared`. The same file
confirms this is the **0.1.2** artifact and that certification passed in full:

```bash
jq -c '{version, ok, cow_id, manifest_sha, canonical, hosted_smoke, certify_ok:.certify.ok, secret_put, errors}' \
   runs/2026-08-28-minigrid/release-result.json
```

```json
{"version":"0.1.2","ok":true,"cow_id":"cow_70e4993f-58ea-4678-8d19-ffa1866214b1",
 "manifest_sha":"sha256:efc95d4886a5dfde4d7773c302ebe870e677bf1f48879f17d13e516566763e97",
 "canonical":true,"hosted_smoke":"passed","certify_ok":true,"secret_put":true,"errors":[]}
```

and the certify tail shows 10 of 10 transcript steps passing, ending on the liveness line:

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

Provenance check — the file is committed (clean working tree) and byte-identical to the artifact of
the release run STATE records:

```bash
git status --porcelain runs/2026-08-28-minigrid/release-result.json     # (empty — committed, unmodified)
gh run download 33230336307 -R Metta-AI/cogame-minigrid -n release-result -D /tmp/rrcheck
diff <(jq -S . /tmp/rrcheck/release-result.json) <(jq -S . runs/2026-08-28-minigrid/release-result.json)
md5sum /tmp/rrcheck/release-result.json runs/2026-08-28-minigrid/release-result.json
```

```
IDENTICAL to release run 33230336307 artifact
ae87a49ba6770cdc48a7bb20632ea79d  /tmp/rrcheck/release-result.json
ae87a49ba6770cdc48a7bb20632ea79d  runs/2026-08-28-minigrid/release-result.json
```

Status: **TRUE** — read from the run directory's committed `release-result.json`, verified
byte-identical to release run `33230336307`'s artifact (the run STATE records for 0.1.2), and it
carries `Replay liveness: skipped (static replay bundle declared`.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged

**TRUE on both mechanical criteria** (`loaded: true`; three pairwise-distinct clock readouts).

*(a) Dispatch.* The iframe `src` from §6 was opened in headless chromium by CI. Nothing was
rendered locally; this sandbox has no browser and no screen. The URL dispatched is exactly the one
§6's session call returned at 06:41:17Z — the live featured match, `minigrid.r35.e1`, on the
current coworld and a qualifying round. Because round 35 stayed the newest completed round for the
whole session, the render below exercises exactly the bundle and exactly the replay the public page
was serving at the moment of verification. One `viewer-check.yml` run was dispatched.

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_70e4993f-58ea-4678-8d19-ffa1866214b1/sha256%3Aefc95d4886a5dfde4d7773c302ebe870e677bf1f48879f17d13e516566763e97/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F2e5030b6-fdcd-422a-9d4a-c1c6d6eeed9e.replay'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
# dispatched 2026-08-29T06:41:25Z
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status,conclusion -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:5][]|[.databaseId,.createdAt,.status,(.conclusion//"-")]|@tsv'
```

```
33239074400	2026-08-29T06:41:27Z	in_progress	-        ← THIS run (createdAt > dispatch 06:41:25Z)
33233844065	2026-08-29T04:27:03Z	completed	success  ← not this run
33233650158	2026-08-29T04:22:11Z	completed	success  ← not this run
33233338285	2026-08-29T04:14:31Z	completed	success  ← not this run
33227616497	2026-08-29T01:54:33Z	completed	success  ← round 2's run, NOT reused
```

The run was found by sorting on `createdAt` and matching against the dispatch timestamp, not by
taking "the latest run" blind. It finished **green**:

```bash
gh run view 33239074400 -R Metta-AI/coworld-builder --json status,conclusion,createdAt,jobs
```

```json
{"status":"completed","conclusion":"success","createdAt":"2026-08-29T06:41:27Z",
 "steps":[{"name":"Set up job","conclusion":"success"},
          {"name":"Run actions/checkout@v5","conclusion":"success"},
          {"name":"Run actions/setup-node@v4","conclusion":"success"},
          {"name":"Install Playwright (pinned 1.55.0)","conclusion":"success"},
          {"name":"Load the viewer","conclusion":"success"},
          {"name":"Summary","conclusion":"success"},
          {"name":"Upload the evidence","conclusion":"success"},
          {"name":"Fail if the viewer did not load","conclusion":"success"},
          {"name":"Post Run actions/setup-node@v4","conclusion":"success"},
          {"name":"Post Run actions/checkout@v5","conclusion":"success"},
          {"name":"Complete job","conclusion":"success"}]}
```

```bash
rm -rf runs/2026-08-28-minigrid/viewer-check && mkdir -p runs/2026-08-28-minigrid/viewer-check
gh run download 33239074400 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-28-minigrid/viewer-check
```

→ `viewer-smoke.json` (1 752 B), `viewer-smoke.png` (531 864 B), `smoke-stdout.txt` (956 B),
`smoke-stderr.txt` (0 B). The round-2 artifact at that path was **overwritten**, not merged. (The
pre-existing `viewer-check/retries/` subdirectory holds the *0.1.0* round's three attempts and was
left untouched; it is historical, not this round's evidence, and nothing in this file rests on it.)
These four files are this run's only rendered evidence; the CI sandbox that made them is gone.

*(b) The readouts, verbatim from `runs/2026-08-28-minigrid/viewer-check/viewer-smoke.json`.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-28-minigrid/viewer-check/viewer-smoke.json
```

```json
{"loaded":true,"ms":1933,"clock":"TURN 1/30 · PHASE 1/5 · LAVAGAP TICK 2/720 · ALPHA 0 · BETA 0 · GAMMA 0 · DELTA 0","scorebug":"— CARTOGRAPHER Carrying 0/5 ALPHA · SCORE 0 — PROMPT Carrying 0/5 GAMMA · SCORE 0 TURN 1/30 · PHASE 1/5 · LAVAGAP TICK 2/720 · ALPHA 0 · BETA 0 · GAMMA 0 · DELTA 0 — MISSIONFIRST Carrying 0/5 BETA · SCORE 0 — SCOUT Carrying 0/5 DELTA · SCORE 0","feed_lines":20}
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

Also in the artifact: `"status":"OPEN"`, `"loading_text":null` (no stuck "Loading replay…"),
`"console_tail":[]`, `"soak":null`, and
`canvas_text {"total":0,"outside":0,"ellipsized":0,"never_inside":0}` — no text drawn outside the
canvas and nothing ellipsized. The `url` recorded in the artifact is the §6 `src` character for
character.

**The three clock readouts** (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub | clock readout |
|---|---|
| **0 %** | `TURN 1/30 · PHASE 1/5 · LAVAGAP TICK 2/720 · ALPHA 0 · BETA 0 · GAMMA 0 · DELTA 0` |
| **50 %** | `TURN 13/30 · PHASE 3/5 · MULTIROOM TICK 290/720 · ALPHA 0 · BETA 0 · GAMMA 0 · DELTA 2` |
| **100 %** | `TURN 25/30 · PHASE 5/5 · BABYAI TICK 578/720 · ALPHA 0 · BETA 0 · GAMMA 0 · DELTA 3` |

**All three differ pairwise** — turn 1 → 13 → 25, tick 2 → 290 → 578, phase 1 → 3 → 5 with the
family name changing LAVAGAP → MULTIROOM → BABYAI, and DELTA's solve counter advancing 0 → 2 → 3.
`loaded: true` via `data-replay-loaded="true"` at **1 933 ms**. (`bridge_ready` is `false` and
`bridge` is empty: this shell signals readiness through the DOM attribute rather than the
`coworld-replay` postMessage bridge — the check accepts either, and the attribute is present and
`"true"`.) A `#scrub` element **is** present; there is no `"(no #scrub…)"` fallback string in the
json, so motion is judged from the readouts, not inferred.

*(c) Reconciliation against the replay JSON.* The rendered clock and the recorded episode agree on
the frames the viewer reached, and disagree in exactly one respect, which is documented below.

- `TURN 25/30` matches `results.turnsPlayed: 25` and the replay's 25 planned turns.
- `TICK 578/720` matches `results.finalTick: 578` (and `tickCount: 578`); 720 is the cap
  (`maxTicks`), not the episode length.
- `PHASE 5/5 · BABYAI` matches `taskFamilies[4] == "babyai"`; the left-gutter mission sentence
  *"go to the green ball"* matches `taskMissions[4]` verbatim.
- The 50 % readout's `PHASE 3/5 · MULTIROOM` matches `taskFamilies[2] == "multiroom"`, and its
  `DELTA 2` matches `taskSolved[3] == [true,true,true,false,true]` with Delta's third solve
  (multiroom) still in progress at tick 290.
- **Discrepancy, reported not smoothed:** the 100 % readout reads `ALPHA 0 · BETA 0 · GAMMA 0 ·
  DELTA 3`, whereas `results.tasksSolved` is `[1,1,1,4]`. The cause is visible in the replay and in
  the transport strip. `results.taskTicks[*][4] == 2` for every lane — all four seats solved the
  final babyai task in the **last two ticks** — and the transport strip in the screenshot reads
  **`578 / 579`**: the 100 % scrub position lands on tick 578 of a 579-tick timeline, one frame
  before the credit is applied. The endcard, which is what the starter draws on the true final
  frame, therefore never appeared in this render. See the legibility findings below; this is a
  one-frame off-by-one in the scrubber's right edge, not a data disagreement — the replay's
  `results` and the API's `participant_scores` (§3) match each other exactly.

### Spectator-judgment paragraph

The screenshot (`runs/2026-08-28-minigrid/viewer-check/viewer-smoke.png`, 1280×800) is a
**legible, populated, unmistakably-minigrid frame** captured at `TURN 25/30 · PHASE 5/5 · BABYAI`,
tick 578 of 579 — the last playable frame before the endcard. The four-lane quad layout renders
cleanly: four gridworld boards in a 2×2 arrangement, each tinted to its lane's colour (top-left red
= ALPHA, top-right blue = BETA, bottom-left green labelled **GAMMA**, bottom-right yellow labelled
**DELTA**), each showing the same seeded babyai board — a green ball, a purple box, a red ball, two
dark spheres and a low tan wall segment, on a dotted 13×13 grid. In every lane the agent is drawn
as a lane-coloured rover sprite (red in ALPHA, tan-orange in DELTA) standing immediately east of
the green ball behind a yellow wall bar; the four lanes are at nearly the same board position,
which is what the replay records — at turn 25 all three LLM seats say the green ball is at (10,2)
and are moving to it (`.plans[]` late excerpt, §4), and all four lanes solve that task
(`taskOutcome[*][4] == "solved"`). So the picture and the record agree even in the fine detail of
where the agents are standing. The **left gutter** carries the mission ribbon exactly as the
addendum specified — `PHASE 5/5 · BABYAI` above the sentence *"go to the green ball"* — and beneath
it the five-task **pip stack**, LAVAGAP / DOORKEY / MULTIROOM / KEYCORRIDOR / BABYAI, each with a
four-quadrant per-lane status badge. The **right gutter** carries the **POV inset**:
`AGENT VIEW 7×7`, a real 7×7 cell grid with four coloured cells (an orange object on the top row,
two blue cells and a yellow key), captioned `DELTA · FACING WEST`, then
`POV DELTA · 3/5 · SCORE 311040`, then the feed line
`PHASE 5/5 — BABYAI: "go to the green ball"`. `feed_lines` is **20** in the JSON — round 2 measured
4, and the 0.1.0 round measured 0, so the killfeed is now carrying a full history. Across the top
runs the per-lane carrying banner (`0/5 Carrying` ×2, `Carrying 0/5`, `Carrying 3/5`) with the big
clock `TURN 25/30 · PHASE 5/5 · BABYAI` centred, and under it the summary line `TICK 578/720 ·
ALPHA 0 · BETA 0 · GAMMA 0 · DELTA 3` flanked by four colour-chipped score readouts
(`ALPHA · SCORE 2000`, `GAMMA · SCORE 4000`, `BETA · SCORE 3000`, `DELTA · SCORE 311040`). A
spectator looking at this frame can tell, without reading any JSON, which lane is which, what the
current task is, who is ahead, and how far through the gauntlet the episode is. It is **not empty,
not frozen and not unreadable**: the three scrub readouts prove it advances (turn 1 → 13 → 25, tick
2 → 290 → 578, phase 1 → 3 → 5), and the mission ribbon plus the score chips prove it explains
itself. What it does **not** show is the endcard, because the render stopped one frame short of the
end (below).

**Does it look like the starter's chrome?** Yes. The bottom transport strip is coworld-ctf's:
restart / step-back / play / `+5s` / step-forward / loop / fast-forward buttons, a `spoilers`
toggle, a `578 / 579` frame readout, the `1× 2× 3× 4× 8× 16×` speed selector with `1×` active, and
the **`PROGRESS` scrubber with the momentum graph** — four coloured traces (yellow, green, blue,
orange) climbing across the timeline in visible step functions, with per-lane event tick marks above
them in each lane's colour — which is the same widget paintbot/raid/hive ship. The scorebug, the
colour language and the gutter layout are the same family. This is a fork of the starter, not the
cogame-gridlock failure mode of a rewrite that merely shares ids. I can attest to the transport
strip, the momentum-graph scrubber and the scorebug **from this render**; I **cannot** attest to the
endcard from this render, because it never came on screen — round 2's render did capture it, but
that is a different session's evidence and is not being borrowed here.

**Legibility observations for phase 30 (non-blocking; none of them makes this item false).**
(i) **The endcard is unreachable from the scrubber's right edge.** The transport reads `578 / 579`
at 100 % scrub, so a spectator who drags to the end lands one frame before the final one and sees
pre-credit lane scores — `ALPHA 0 · BETA 0 · GAMMA 0 · DELTA 3` with `ALPHA · SCORE 2000` — instead
of the true outcome `[1,1,1,4]` / `[105050,106050,107050,414090]`. In this episode all four lanes
solved the last task in the final two ticks, so the entire visible story of the endgame is on the
one frame the scrubber cannot reach. This is the most consequential of the four.
(ii) **The top two lanes carry no text label.** GAMMA and DELTA are lettered above their boards;
ALPHA and BETA are not — the label band above the top row contains only the centred `👁 DELTA`
POV badge, straddling the divider between the two unlabelled lanes. The top lanes are identifiable
only by border colour and by the score chips in the header strip.
(iii) The header strip groups the four score chips by board *column* — `ALPHA · SCORE 2000` and
`GAMMA · SCORE 4000` to the left of the big clock, `BETA · SCORE 3000` and `DELTA · SCORE 311040`
to the right — so the header's left-to-right order (A, G, B, D) does not match the reading order of
the top row of boards (A, B). Defensible, but it took a second look to confirm which chip belonged
to which quadrant.
(iv) The four carrying banners alternate word order: the left pair read `0/5 Carrying` and the
right pair read `Carrying 0/5` / `Carrying 3/5`. Each has a small chip below it holding an em-dash
where the carried item's name goes; at this frame nothing is carried in any lane, so the empty slot
is correct behaviour rather than a bug — but four banners in two different word orders is not.

Status: **TRUE** — `loaded: true` at 1 933 ms, three pairwise-distinct clock readouts,
`feed_lines: 20`, a scorebug naming all four seats, `failure: null`, and a rendered frame that is
legible, that shows the game, and that reads as the starter's chrome.

---

## Summary — verdict table

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — 14 qualifying rounds (22–35), all `completed`, all seating both v3 champions against the live v3 filler pair set 03:17:07Z; 35/35 rounds in the league `completed`, zero failed/discarded |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — `daveey` rank 2 `minigrid-cartographer:v3` (35 rounds), `daveey-1` rank 3 `minigrid-missionfirst:v3` (35 rounds); both fillers absent from the leaderboard |
| 3 | Latest round's episode request completed with replay | **TRUE** — round 35 → `ereq_3d489c10…` `status:"completed"`, non-null `replay_url`, 4 participants naming `daveey` + `daveey-1`, filler flagged `is_filler:true` |
| 4 | Replay bytes valid and show the game | **TRUE** — strict UTF-8 JSON parse ok; header `COWLDMGD`/`minigrid`/GameVersion 3; `protocol` `minigrid/v1`; `reason:"complete"`; 67 LLM decisions and **0** fallbacks in round 35, **0 of 1 071** across all 14 qualifying rounds; score identity verified per seat |
| 5 | Hosted game log clean | **TRUE** — CLEAN in all 14 qualifying rounds (22–35); 1 073 sidecar calls all HTTP 200, 0 non-2xx; 2 `schema_error` retries, both recovered and booked to `retriedTurns`. Max observed batch latency 12 477 ms vs `attempt1Ms` 18 000 (1.44× headroom). Round 2's FALSE is resolved |
| 6 | Public page uses the static replay path | **TRUE** — featured match `minigrid.r35.e1` on `cow_70e4993f`/`0.1.2` (a qualifying round); iframe `src` is the static route with the 0.1.2 manifest sha and `ready:true`; never `/client/replay` |
| 7 | Certification declared the static bundle | **TRUE** — committed `release-result.json` (0.1.2, byte-identical to release run 33230336307's artifact) carries `Replay liveness: skipped (static replay bundle declared…` |
| 8 | Spectator judgment (executed viewer) | **TRUE** — run `33239074400` green; `loaded:true` at 1 933 ms, three pairwise-distinct clocks, `feed_lines:20`, `failure:null`; legible quad frame with the starter's transport strip, momentum-graph scrubber and scorebug |

**Verdict: all-true (8 of 8).**

Non-blocking findings for the coordinator, in priority order:
1. **Viewer**: the 100 % scrub lands on frame 578 of 579, so the endcard and the final task credits
   are unreachable from the scrubber's right edge (§8 legibility (i)).
2. **Viewer**: the ALPHA and BETA lanes carry no text label (§8 legibility (ii)); the header groups
   score chips by board column rather than reading order (iii); the four carrying banners alternate
   word order (iv).
3. **Policy quality**: champions now solve a mean of 1.00 (cartographer) and 0.79 (missionfirst)
   tasks per round, up from 0 in round 2 — the `goto` Case C fix worked — but the scripted filler
   still averages 1.57, so the LLM champions have not yet beaten their own baseline (§4).
4. **Tooling**: `replay_summary.py` emits `protocol` as a hard-coded constant rather than reading it
   from the container; the real on-the-wire identity is the header's gameName + GameVersion (§4).

For STATE:

```
verify.rounds       = [{"n":33,"id":"round_5aa199f3-78cf-4087-a953-28df22c7779e"},
                       {"n":34,"id":"round_676b07e5-17d4-4029-8d12-1ab4733bf6f1"},
                       {"n":35,"id":"round_f8ba8e4f-a3c2-4841-a4cb-59a03507c465"}]
                      # all of rounds 22-35 qualify (both champions on v3, v3 fillers live);
                      # checks 3/4/6/8 were all executed against round 35, the latest completed
verify.replay       = "https://softmax-public.s3.amazonaws.com/replays/2e5030b6-fdcd-422a-9d4a-c1c6d6eeed9e.replay"
verify.iframe_static = true
verify.viewer_check_run = "33239074400"
```
