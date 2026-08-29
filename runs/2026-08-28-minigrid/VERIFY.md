# VERIFY — minigrid   (2026-08-29T02:15Z)

Verdict: **1 item false** (check 5) — checks 1, 2, 3, 4, 6, 7, 8 TRUE.

**Round 2 — this file supersedes the 0.1.0 verification.** The first verification of this run
(2026-08-28T22:55Z, preserved in git history) ran against release **0.1.0** / `cow_5201d3e2` and
returned checks 5, 6 and 8 FALSE: check 6 because a single-seat episode can never produce a
featured match, check 8 because the viewer's 50 % and 100 % scrub readouts were identical, and
check 5 because of one champion-seat fallback against a 6 000 ms attempt-1 deadline. The coworld
was redesigned to **four isolated lanes** (`num_agents` 1 → 4), the viewer seek/clock contract was
fixed, the deadline ladder was widened to `attempt1Ms 11000` / `retryMs 6000`, and the result was
re-released as **0.1.1** (`cow_753b4d23`, manifest `sha256:fdd3b4cb…656032`, release run
`33226095645`). Every one of the eight checks below was **re-executed from scratch** in this
verifier session (2026-08-29 01:50Z – 02:15Z) against 0.1.1; nothing is carried over from the
0.1.0 round. Checks 6 and 8 are now TRUE — the featured match exists and the three clock readouts
are pairwise distinct. Check 5 is **still FALSE**, but for a different and better-understood
reason, documented in §5.

Run: `2026-08-28-minigrid` · slug `minigrid` · version `0.1.1`
`$COW` `cow_753b4d23-00cd-417a-99eb-b643f0f0f526`
`$L` `league_78d5b417-52a0-4459-8fd6-3b9aeacfe1ca`
`$D` `div_721f571a-ece7-4ed9-8b1c-15eb2cd072be`
manifest_sha `sha256:fdd3b4cbd21f370c1639693a1001400fb80e3c8a7542ec9fae9b7581dc656032`
repo `Metta-AI/cogame-minigrid` @ `8a78a6bf`

All ids read from `runs/2026-08-28-minigrid/STATE.json`. Documented exceptions to "fetch fresh":
**check 7** reads the committed `runs/2026-08-28-minigrid/release-result.json` (as
`prompts/60-verify.md` §7 directs), and **check 8**'s rendered evidence is the artifact of the
`viewer-check.yml` run this session dispatched at 01:54:33Z (run `33227616497`).

Headers on every Observatory call: `Authorization: Bearer $SOFTMAX_TOKEN` and
`User-Agent: coworld-builder/1.0`; `X-Use-Elevated-Privileges: true` added on the reads that
require it (`/artifacts/logs`, `/leagues/$L/filler-policies`). Values are never printed.

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_78d5b417-52a0-4459-8fd6-3b9aeacfe1ca
D=div_721f571a-ece7-4ed9-8b1c-15eb2cd072be
COW=cow_753b4d23-00cd-417a-99eb-b643f0f0f526
```

Poll log (`prompts/60-verify.md` §Waiting; bound 75 min from 01:50Z, i.e. expiring 03:05Z):

| UTC | observation |
|---|---|
| 01:51:0xZ | rounds 1–16 all `completed`; 15 and 16 carry the all-v2 entrant set → the ≥2 bound was already satisfied at the first poll |
| 01:56:25Z | no round 17 yet; checks 3/4/6/8 executed against round 16 (the latest completed) |
| 02:00:54Z | round 17 `pending` (created 01:58:13Z) |
| 02:10:49Z | round 17 **completed** 02:04:47Z → fetched as check-5 retry attempt 3 (§5) |
| 02:11:31Z | `softmax.com/minigrid` re-fetched; featured match has rolled to `minigrid.r17.e1` (§6) |

Bound used: 21 of 75 minutes. The ladder produces a round every ~15 minutes, so "the latest
completed round" is a moving target; §§3, 4, 6 and 8 were executed against **round 16**, which was
the latest completed round at the moment each was run (01:52–01:55Z). Round 17 completed at
02:04:47Z, afterwards. Where that matters it is stated in the section, and §5 and §6 were both
re-run against round 17 rather than left stale.

---

## 1. ≥2 completed rounds after the fillers were set

**TRUE** — rounds **15** and **16** completed after the v2 filler pair went live, both with the
all-v2 entrant set. No round in this league has ever been `failed` or `discarded`.

First, what the live filler set actually is (this is the "after the fillers were set" reference
point; the read needs the elevated header even though it is a read):

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}" | jq .
```

Fetched 2026-08-29T01:52:0xZ — HTTP 200:

```json
{
  "filler_policy_versions": [
    {
      "policy_version_id": "1f17a736-1407-4eac-bde7-6400d0b3b0ed",
      "policy_id": "4551842d-05d0-4fd0-9aeb-bf6a8c7deefc",
      "policy_name": "minigrid-scout",
      "version": 2,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "display_name": null
    },
    {
      "policy_version_id": "d984c287-a3d7-4dcd-9248-f8200df6cc8a",
      "policy_id": "d885f184-1d7d-4eaf-ad0f-739597087f74",
      "policy_name": "minigrid-bumper",
      "version": 2,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "display_name": null
    }
  ]
}
```

Both are **v2** and neither uuid is a champion uuid (champions are `52906971…` and `bdf22f53…`).
`log.md` records the replacement at `2026-08-29T01:31Z`, immediately before round 14.

Then the rounds:

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=30" "${AUTH[@]}" \
 | jq 'if type=="array" then . else .entries end
       | [.[]|{id,round_number,status,error,created_at,completed_at,
               entrants:.round_config.entrant_policy_version_ids}] | sort_by(.round_number)'
```

Fetched 2026-08-29T01:51:0xZ — HTTP 200. Sixteen rounds returned, **all `"status":"completed"`,
all `"error": null`** (zero `failed`, zero `discarded`). Trimmed to rounds 13–16, which is where
the v1 → v2 rollover happens:

```json
[
  { "id": "round_a27653e9-e82a-43fc-bd28-a20da01ec8b1", "round_number": 13,
    "status": "completed", "error": null,
    "created_at": "2026-08-29T01:15:46.654439Z", "completed_at": "2026-08-29T01:19:19.075534Z",
    "entrants": ["6eed9b32-93bb-42db-9c06-2a33a41678ae",
                 "8e8fff3c-dfee-4dfc-81ba-841de3a7e355",
                 "9b23f82c-29fc-4167-a802-1cf15eca7c53"] },
  { "id": "round_65144971-4922-40a5-ab8d-be00b7bcad5e", "round_number": 14,
    "status": "completed", "error": null,
    "created_at": "2026-08-29T01:30:43.353011Z", "completed_at": "2026-08-29T01:36:33.210483Z",
    "entrants": ["52906971-a8a1-414d-b538-847d072173df",
                 "8e8fff3c-dfee-4dfc-81ba-841de3a7e355",
                 "9b23f82c-29fc-4167-a802-1cf15eca7c53"] },
  { "id": "round_a4dba3c3-d5c7-4e62-9eda-40ce114e6f1c", "round_number": 15,
    "status": "completed", "error": null,
    "created_at": "2026-08-29T01:36:34.023729Z", "completed_at": "2026-08-29T01:42:21.159750Z",
    "entrants": ["52906971-a8a1-414d-b538-847d072173df",
                 "bdf22f53-d38d-463b-b0ca-07deb733981c",
                 "9b23f82c-29fc-4167-a802-1cf15eca7c53"] },
  { "id": "round_6f2dadf4-b743-4f29-b9f4-119141ca8db7", "round_number": 16,
    "status": "completed", "error": null,
    "created_at": "2026-08-29T01:43:13.039669Z", "completed_at": "2026-08-29T01:49:21.551025Z",
    "entrants": ["52906971-a8a1-414d-b538-847d072173df",
                 "bdf22f53-d38d-463b-b0ca-07deb733981c",
                 "9b23f82c-29fc-4167-a802-1cf15eca7c53"] }
]
```

Round 13 seats **cartographer v1** (`6eed9b32`) and **missionfirst v1** (`8e8fff3c`). Round 14
seats cartographer **v2** but missionfirst still **v1** (the placement snapshot was taken before
the v2 submission landed). Rounds **15 and 16** seat both champions on **v2** — `52906971` =
`minigrid-cartographer:v2` (daveey) and `bdf22f53` = `minigrid-missionfirst:v2` (daveey-1). The
third uuid `9b23f82c` is the third-party entrant `co-gas-minigrid-subgoal-router-richard:v1`
(player `richard`), not a filler.

Corroboration that the **v2** filler pair was actually seated in those rounds (the round config
lists only entrants; the filler shows up in the episode):

```bash
for r in round_65144971-… round_a4dba3c3-… ; do
  e=$(curl -sS "$BASE/rounds/$r/episode-requests" "${AUTH[@]}" | jq -r '.entries[0].id')
  curl -sS "$BASE/episode-requests/$e" "${AUTH[@]}" \
   | jq -c '[.participants[]|{position,policy_name,version,player_name,is_filler}]'
done
```

Fetched 2026-08-29T01:57:5xZ:

```json
round 14 (ereq_33e1b859-c6ca-4a9d-bbf3-16c556224d95):
[{"position":0,"policy_name":"minigrid-cartographer","version":2,"player_name":"daveey","is_filler":false},
 {"position":1,"policy_name":"minigrid-missionfirst","version":1,"player_name":"daveey-1","is_filler":false},
 {"position":2,"policy_name":"co-gas-minigrid-subgoal-router-richard","version":1,"player_name":"richard","is_filler":false},
 {"position":3,"policy_name":"minigrid-bumper","version":2,"player_name":"daveey","is_filler":true}]

round 15 (ereq_6c612420-5975-40b7-a538-8014744efe3e):
[{"position":0,"policy_name":"minigrid-cartographer","version":2,"player_name":"daveey","is_filler":false},
 {"position":1,"policy_name":"minigrid-missionfirst","version":2,"player_name":"daveey-1","is_filler":false},
 {"position":2,"policy_name":"co-gas-minigrid-subgoal-router-richard","version":1,"player_name":"richard","is_filler":false},
 {"position":3,"policy_name":"minigrid-bumper","version":2,"player_name":"daveey","is_filler":true}]
```

Status: **TRUE** — the v2 filler pair (`minigrid-scout:v2`, `minigrid-bumper:v2`) is the live
filler set; rounds **15** (completed 2026-08-29T01:42:21Z) and **16** (completed
2026-08-29T01:49:21Z) both completed after it was set and both seat both champions on v2 — two
qualifying completed rounds. Fourteen further rounds (1–14) also completed; none failed or was
discarded, so there is no `error` string to record.

---

## 2. Both champions ranked

**TRUE.**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq .
```

Fetched 2026-08-29T01:52:0xZ — HTTP 200, bare JSON list:

```json
[
  {"rank":1,"player_id":"ply_ded11f40-3e30-4921-b019-f7f6bc3e9c83","player_name":"richard",
   "score":1039.2124455408778,"score_label":"MMR","rounds_played":14,"episode_wins":15.0,
   "win_rate":0.5357142857142857,"policy_label":"co-gas-minigrid-subgoal-router-richard:v1"},
  {"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
   "score":1001.0113369839092,"score_label":"MMR","rounds_played":16,"episode_wins":18.0,
   "win_rate":0.6,"policy_label":"minigrid-cartographer:v2"},
  {"rank":3,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
   "score":959.7762174752124,"score_label":"MMR","rounds_played":16,"episode_wins":11.0,
   "win_rate":0.36666666666666664,"policy_label":"minigrid-missionfirst:v2"}
]
```

```
rank  player_name  policy_label                                 score     rounds  wins
1     richard      co-gas-minigrid-subgoal-router-richard:v1    1039.212  14      15.0
2     daveey       minigrid-cartographer:v2                     1001.011  16      18.0
3     daveey-1     minigrid-missionfirst:v2                      959.776  16      11.0
```

Status: **TRUE** — `daveey` (rank 2, `minigrid-cartographer:v2`, `rounds_played` 16) and
`daveey-1` (rank 3, `minigrid-missionfirst:v2`, `rounds_played` 16) are both present with
`rounds_played ≥ 1`, and both are carrying their **v2** labels. The two filler policies
(`minigrid-scout`, `minigrid-bumper`) are **absent** from the leaderboard entirely, which is the
stronger of the two conditions the check allows. `richard` at rank 1 is an independent third-party
entrant (`ply_ded11f40`), not a filler and not one of this run's policies.

---

## 3. The latest round's episode request completed with a replay

**TRUE.** Latest completed round **at the time this check ran (01:52Z)** = **16**
(`round_6f2dadf4-b743-4f29-b9f4-119141ca8db7`, completed 01:49:21Z). Round 17 completed later, at
02:04:47Z; its episode request `ereq_924bca47-0f9f-4ee7-b814-236c19ec9211` was fetched for §5 and
is also `"status":"completed"` with the same four-participant shape (daveey cartographer v2,
daveey-1 missionfirst v2, richard v1, scout v2 `is_filler`) and a non-null `replay_url`, so the
check holds for it too.

```bash
R=round_6f2dadf4-b743-4f29-b9f4-119141ca8db7
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" | jq '{count:(.entries|length), …}'
```

Fetched 2026-08-29T01:52:4xZ — HTTP 200. One episode request:
`ereq_737c8831-0e00-4a7c-868e-732a2ca0df67`.

```bash
curl -sS "$BASE/episode-requests/ereq_737c8831-0e00-4a7c-868e-732a2ca0df67" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```

Fetched 2026-08-29T01:53:0xZ — HTTP 200:

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/3fe6e480-ef59-4b89-89af-01e4c825cd6b.replay",
  "participants": [
    {"position":0,"kind":"policy","policy_version_id":"52906971-a8a1-414d-b538-847d072173df",
     "policy_name":"minigrid-cartographer","version":2,
     "player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
     "is_filler":false,"is_seed":false},
    {"position":1,"kind":"policy","policy_version_id":"bdf22f53-d38d-463b-b0ca-07deb733981c",
     "policy_name":"minigrid-missionfirst","version":2,
     "player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
     "is_filler":false,"is_seed":false},
    {"position":2,"kind":"policy","policy_version_id":"9b23f82c-29fc-4167-a802-1cf15eca7c53",
     "policy_name":"co-gas-minigrid-subgoal-router-richard","version":1,
     "player_id":"ply_ded11f40-3e30-4921-b019-f7f6bc3e9c83","player_name":"richard",
     "is_filler":false,"is_seed":false},
    {"position":3,"kind":"policy","policy_version_id":"1f17a736-1407-4eac-bde7-6400d0b3b0ed",
     "policy_name":"minigrid-scout","version":2,
     "player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
     "is_filler":true,"is_seed":false}
  ],
  "participant_scores": [
    {"position":0,"score":3000.0},
    {"position":1,"score":5000.0},
    {"position":2,"score":211010.0},
    {"position":3,"score":312040.0}
  ]
}
```

Status: **TRUE** — `status == "completed"`, `replay_url` non-null, and the participants name
**`daveey`** (position 0, cartographer v2) and **`daveey-1`** (position 1, missionfirst v2). The
episode now has **four** participants, as 0.1.1's `num_agents: 4` requires: the two champions, the
third-party entrant `richard`, and one filler seat carrying `"is_filler": true`
(`minigrid-scout:v2`). The four `participant_scores` match the replay's `results.scores`
`[3000, 5000, 211010, 312040]` exactly (see §4), so the API record and the replay agree.

---

## 4. The replay bytes are valid and show the game

**TRUE.**

The minigrid replay is a **binary `COWLDMGD`** container, not JSON, so `jq -e .` on the raw bytes
is not the right strict parser — the repo ships `tools/replay_summary.py` for exactly this, and
the design note (`docs/plans/2026-08-28-minigrid-design.md` lines 1208-1220) declares it the
phase-60 evidence path. The repo was cloned fresh at `8a78a6bf` (the sha this release was cut from) for
this check.

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/3fe6e480-ef59-4b89-89af-01e4c825cd6b.replay" \
     -o /tmp/ep.replay                 # HTTP 200, 190974 bytes
python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
```

```
200 190974
strict UTF-8 JSON: ok
```

```bash
jq -c '{protocol, gameVersion, variant, seed, tickCount,
        reason:.results.reason, endRule:.results.endRule,
        names:.results.names, aliases:.results.aliases,
        policyKinds:.results.policyKinds,
        llmTurns:.results.llmTurns, fallbackTurns:.results.fallbackTurns,
        fallbackCauses:.results.fallbackCauses,
        tasksSolved:.results.tasksSolved, scores:.results.scores,
        turnsPlayed:.results.turnsPlayed, deaths:.results.deaths,
        crashes:.results.crashes, actionsDropped:.results.actionsDropped}' /tmp/ep.json
```

```json
{"protocol":"minigrid/v1","gameVersion":"2","variant":"gauntlet","seed":1261404912,
 "tickCount":720,"reason":"complete","endRule":"allLanesComplete",
 "names":["cartographer","missionfirst","prompt","scout"],
 "aliases":["Alpha","Beta","Gamma","Delta"],
 "policyKinds":["llm","llm","llm","scripted"],
 "llmTurns":[30,25,25,0],"fallbackTurns":[0,0,4,0],
 "fallbackCauses":[{},{},{"transport_timeout":4},{}],
 "tasksSolved":[0,0,2,3],"scores":[3000,5000,211010,312040],
 "turnsPlayed":30,"deaths":[0,1,0,0],"crashes":[0,0,0,0],
 "actionsDropped":[0,0,0,0]}
```

`protocol` is `minigrid/v1`, which is what the manifest's protocol document declares and what the
v2 addendum explicitly pinned: *"`tools/replay_summary.py` output gains `aliases` (4), `lanes` (4),
per-seat `plans`, per-seat `says`, and `fallbackCauses`; `protocol` stays `minigrid/v1`"*
(`docs/plans/2026-08-28-minigrid-design.md:2472`). `gameVersion` is `"2"` — the four-lane build.
`results.reason == "complete"` (not `deadline`), so no documented exception is needed.

Decision counts and the fallback minority, per seat:

```bash
jq -r '[.plans[]|.source]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.json
jq -c '{plansBySeat:(.plansBySeat|map(length)), fallbacks, budgetGuards}' /tmp/ep.json
```

```json
{"fallback":4,"llm":80,"scripted":26}
{"plansBySeat":[30,25,29,26],"fallbacks":9,"budgetGuards":0}
```

**110 recorded decisions in total, 80 of them LLM directives and 4 fallbacks — 3.6 % of all
decisions, and 4.8 % of the 84 decisions taken on LLM seats.** The two **champion** seats have
**zero** fallbacks:

| seat | alias | policy | kind | LLM turns | fallback turns | causes |
|---|---|---|---|---|---|---|
| 0 | Alpha | `minigrid-cartographer:v2` (daveey) | llm | 30 | **0** | `{}` |
| 1 | Beta | `minigrid-missionfirst:v2` (daveey-1) | llm | 25 | **0** | `{}` |
| 2 | Gamma | `co-gas-…-richard:v1` (third party) | llm | 25 | 4 | `{"transport_timeout":4}` |
| 3 | Delta | `minigrid-scout:v2` (filler) | scripted | 0 | 0 | `{}` |

(The top-level `fallbacks: 9` counts *attempt-level* `k:"fallback"` control records — two per
fallen-back turn plus one attempt-1 timeout at turn 19 whose retry succeeded. All nine carry
`"slot": 2`. `results.fallbackTurns` sums to the 4 turns that actually fell through to the
scripted plan. Both numbers are consistent; they count different things.)

The champion decisions are non-scripted and non-trivial. Early, middle and late excerpts of
`.plans[]` (`turn`, seat, `source`, executed-primitive count, `say`):

```
=== EARLY (turns 1–3) ===
  1  ALPHA/cartographer     llm       ex=0   Turn 1: Mapping the world. Goal is GREEN GOAL square. Exploring east s…
  1  BETA/missionfirst      llm       ex=24  get to green goal square; unseen; sweeping north then east to corner
  1  GAMMA/prompt(richard)  llm       ex=6   Exploring eastward along lava boundary to find the gap and green goal.
  1  DELTA/scout(filler)    scripted  ex=7
  2  ALPHA/cartographer     llm       ex=1   Exploring south to map large ? region
  3  ALPHA/cartographer     llm       ex=9   Exploring south to map the goal location
=== MIDDLE (turns 15–18) ===
 15  ALPHA/cartographer     llm       ex=7   Exploring north-west to find goal and keys before time runs out
 15  BETA/missionfirst      llm       ex=13  get to the green goal square; unseen; sweeping NE corner
 16  BETA/missionfirst      llm       ex=14  get to the green goal square; not in known map; sweeping to northeast…
 18  GAMMA/prompt(richard)  fallback  ex=8
=== LATE (turns 29–30) ===
 29  ALPHA/cartographer     llm       ex=0   Searching for green key in unmapped region. Purple key carried. 1 turn…
 29  BETA/missionfirst      llm       ex=1   put purple key next to green key; both keys located; dropping purple k…
 30  ALPHA/cartographer     llm       ex=3   FINAL TURN: Searching for unknown green key in south/east ? regions
 30  BETA/missionfirst      llm       ex=1   put the purple key next to the green key; purple key in hand; green ke…
 30  GAMMA/prompt(richard)  llm       ex=1   Task 5 complete: purple key placed next to green key as required.
```

The seats are reading the mission sentence, naming the objective, and issuing movement/toggle/
pickup verbs against it — this is minigrid being played, not a scripted loop. Aggregate per-seat
action work confirms it:

```json
seat 0 (cartographer): {"plans":30,"verbs":152,"executed":187,"unreachable":6,"dropped":0,"says":30}
seat 1 (missionfirst):  {"plans":25,"verbs":234,"executed":253,"unreachable":6,"dropped":0,"says":25}
seat 2 (richard):       {"plans":29,"verbs":139,"executed":222,"unreachable":0,"dropped":0,"says":25}
seat 3 (scout filler):  {"plans":26,"verbs":74, "executed":237,"unreachable":0,"dropped":0}
```

and the game's own outcome record shows the five-task gauntlet actually being worked:

```json
"taskFamilies":["lavagap","doorkey","multiroom","keycorridor","babyai"],
"taskMissions":["get to the green goal square",
                "use the yellow key to open the door and then get to the green goal square",
                "get to the green goal square","pick up the blue ball",
                "put the purple key next to the green key"],
"taskOutcome":[["timeout","timeout","timeout","timeout","timeout"],
               ["died","timeout","timeout","timeout","timeout"],
               ["solved","solved","timeout","timeout","timeout"],
               ["solved","solved","solved","timeout","timeout"]],
"doorsOpened":[0,2,5,6],"objectsPickedUp":[1,3,3,3],
"primitivesExecuted":[187,241,219,237],"macrosUnreachable":[6,6,0,0],
"repliesRepaired":[0,0,0,0],"crashes":[0,0,0,0]
```

Corroboration from the **other** qualifying round (15,
`https://softmax-public.s3.amazonaws.com/replays/fb3965a5-9041-486c-bc47-fa4d8c44a579.replay`,
HTTP 200, same strict parse):

```json
{"protocol":"minigrid/v1","gameVersion":"2","reason":"complete","endRule":"allLanesComplete",
 "names":["cartographer","missionfirst","prompt","bumper"],
 "policyKinds":["llm","llm","llm","scripted"],
 "llmTurns":[25,26,23,0],"fallbackTurns":[0,1,3,0],
 "fallbackCauses":[{},{"transport_timeout":1},{"transport_timeout":3},{}],
 "tasksSolved":[1,0,0,0],"scores":[103010,2000,3000,1000]}
```

Status: **TRUE** — strict-UTF-8 JSON parse ok; `protocol` `minigrid/v1` as the manifest and the
design pin; `results.reason == "complete"`; 80 LLM decisions against 4 fallbacks (3.6 % of all
decisions), and **both champion seats fell back zero times** in the latest round (round 15:
1 of 26 turns on one champion, 3.8 %). Fallbacks are a small minority on every seat.

**Observations for the coordinator, not check failures.**
(a) In round 16 both champions solved **0 of 5** tasks while the *scripted filler* `scout` solved
3 and `richard` solved 2; in round 15 `cartographer` solved 1 and everyone else 0. The LLM
champions are currently losing to their own scripted baseline. `macrosUnreachable` is 6 for each
champion and 0 for the two seats that scored, and several champion turns executed **0 or 1**
primitives (`ex=0` at turns 1 and 29 for cartographer) because the `goto` macro did not resolve —
that is the mechanism by which the champions burn turns. This is a policy-quality / macro-
resolution finding for phase 30, not a definition-of-done item.
(b) `replay_summary.py`'s **top-level** `policyKinds` is emitted in `register`-record arrival order
(`["llm","llm","scripted","llm"]`) rather than seat order, while `results.policyKinds`
(`["llm","llm","llm","scripted"]`) is seat-ordered and agrees with the `plans[].slot` stream and
with the API's `participants`. Cosmetic tool bug; noted so nobody reads the wrong array.

---

## 5. The hosted game log is clean

**FALSE.** The grep is not empty. Three attempts, three different rounds (16, 15, 17). The
third-party seat falls back in every one of them, and a **champion** seat falls back in two of the
three — in round 17 *both* champions did, on the same turn as the third-party seat.

### Attempt 1 — the latest round's episode request (round 16)

```bash
curl -sS "$BASE/episode-requests/ereq_737c8831-0e00-4a7c-868e-732a2ca0df67/artifacts/logs" \
     "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs16.raw          # HTTP 200, 13220 bytes
# the body is python b'…' byte-string reprs under "===== container: … =====" headers;
# decoded with ast.literal_eval per repr BEFORE grepping (playbooks/observatory-api.md §10)
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs16.txt
```

Fetched 2026-08-29T01:54:0xZ:

```
111:minigrid llm: seat 2 falling back to scout (transport_timeout) on turn 7
114:minigrid llm: seat 2 falling back to scout (transport_timeout) on turn 18
118:minigrid llm: seat 2 falling back to scout (transport_timeout) on turn 22
121:minigrid llm: seat 2 falling back to scout (transport_timeout) on turn 25
```

**NOT CLEAN — 4 matching lines.** Zero of the four are `LLM provider is unavailable`, zero are
`cut off at max_tokens`, zero are `rejected`. The full `game` container, verbatim and complete:

```
minigrid llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
minigrid: serving on 0.0.0.0:8080 seed 1261404912 variant gauntlet
minigrid: player connected on slot 2
minigrid: seat 2 registered as prompt (llm)
minigrid: player connected on slot 1
minigrid: seat 1 registered as missionfirst (llm)
minigrid: player connected on slot 3
minigrid: player connected on slot 0
minigrid: seat 3 registered as scout (scripted)
minigrid: seat 0 registered as cartographer (llm)
Dropped message to disconnected client
minigrid llm: seat 2 attempt 1 failed, will retry (transport_timeout): Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 2 attempt 2 failed (transport_timeout): Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 2 falling back to scout (transport_timeout) on turn 7
minigrid llm: seat 2 attempt 1 failed, will retry (transport_timeout): Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 2 attempt 2 failed (transport_timeout): Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 2 falling back to scout (transport_timeout) on turn 18
minigrid llm: seat 2 attempt 1 failed, will retry (transport_timeout): Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 2 attempt 1 failed, will retry (transport_timeout): Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 2 attempt 2 failed (transport_timeout): Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 2 falling back to scout (transport_timeout) on turn 22
minigrid llm: seat 2 attempt 1 failed, will retry (transport_timeout): Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 2 attempt 2 failed (transport_timeout): Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 2 falling back to scout (transport_timeout) on turn 25
minigrid: episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 0/5 (3000) Beta 0/5 (5000) Gamma 2/5 (211010) Delta 3/5 (312040)
```

Seat 2 is `richard`'s third-party entrant. **Both champion seats (0 and 1) are entirely absent
from the failure lines.** The fallback labelling is now truthful, as the v2 addendum required
(`design.md:2246-2252`): attempt 1 and attempt 2 are logged separately with their own cause, and
the cause is `transport_timeout`, not the mislabelled `parse_error` of 0.1.0.

### Attempt 2 — the other qualifying round (round 15)

```bash
curl -sS "$BASE/episode-requests/ereq_6c612420-5975-40b7-a538-8014744efe3e/artifacts/logs" \
     "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs15.raw          # HTTP 200
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs15.txt
```

Fetched 2026-08-29T01:55:1xZ:

```
103:minigrid llm: seat 2 falling back to scout (transport_timeout) on turn 7
106:minigrid llm: seat 2 falling back to scout (transport_timeout) on turn 19
111:minigrid llm: seat 1 falling back to scout (transport_timeout) on turn 25
112:minigrid llm: seat 2 falling back to scout (transport_timeout) on turn 25
113:minigrid: episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 1/5 (103010) Beta 0/5 (2000) Gamma 0/5 (3000) Delta 0/5 (1000)
```

**NOT CLEAN — 4 matching lines, and line 111 is `seat 1` = `minigrid-missionfirst:v2`, a
champion.** So the failure is not confined to the third-party entrant; it reaches champion seats
too, at roughly 1 turn in 26.

### Attempt 3 — round 17

Round **17** (`round_44adaf2b-3ee7-44db-8076-05fc55ce7b6f`) completed at
2026-08-29T02:04:47.668814Z, i.e. **after** checks 3/4/6/8 had already been executed against the
then-latest round 16. It was fetched as the third and final attempt at this check, on the theory
that the round-16 result might be a one-off.

```bash
R=$(curl -sS "$BASE/rounds?league_id=$L&limit=3" "${AUTH[@]}" \
    | jq -r 'if type=="array" then . else .entries end|map(select(.status=="completed"))|max_by(.round_number)|.id')
# R=round_44adaf2b-3ee7-44db-8076-05fc55ce7b6f
EREQ=$(curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" | jq -r '.entries[0].id')
# EREQ=ereq_924bca47-0f9f-4ee7-b814-236c19ec9211  (status completed, 4 participants,
#   daveey cartographer v2 / daveey-1 missionfirst v2 / richard v1 / scout v2 is_filler)
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs17.raw
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs17.txt
```

Fetched 2026-08-29T02:10:5xZ — HTTP 200:

```
110:minigrid llm: seat 2 falling back to scout (transport_timeout) on turn 15
113:minigrid llm: seat 2 falling back to scout (transport_timeout) on turn 24
120:minigrid llm: seat 0 falling back to scout (transport_timeout) on turn 29
121:minigrid llm: seat 1 falling back to scout (transport_timeout) on turn 29
122:minigrid llm: seat 2 falling back to scout (transport_timeout) on turn 29
```

**NOT CLEAN — 5 matching lines, and this time all three LLM seats fell back on the same turn**
(turn 29: seat 0 = cartographer, seat 1 = missionfirst, seat 2 = richard). The surrounding
attempt-level lines are the diagnosis — note especially seat 0's **attempt 1**, which failed for a
different reason (`schema_error: reply has neither actions nor say`) before its attempt 2 timed
out:

```
minigrid llm: seat 0 attempt 1 failed, will retry (schema_error): reply has neither actions nor say
minigrid llm: seat 1 attempt 1 failed, will retry (transport_timeout): Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 2 attempt 1 failed, will retry (transport_timeout): Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 0 attempt 2 failed (transport_timeout): Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 1 attempt 2 failed (transport_timeout): Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 2 attempt 2 failed (transport_timeout): Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
minigrid llm: seat 0 falling back to scout (transport_timeout) on turn 29
minigrid llm: seat 1 falling back to scout (transport_timeout) on turn 29
minigrid llm: seat 2 falling back to scout (transport_timeout) on turn 29
minigrid: episode complete — reason complete endRule allLanesComplete seats 4 — Alpha 0/5 (5000) Beta 0/5 (3000) Gamma 0/5 (6000) Delta 3/5 (312020)
```

Its replay (`https://softmax-public.s3.amazonaws.com/replays/0746b9a3-3bf0-453b-9045-eb8a334849c0.replay`,
HTTP 200, strict parse ok) agrees and quantifies it:

```json
{"protocol":"minigrid/v1","gameVersion":"2","reason":"complete",
 "names":["cartographer","missionfirst","prompt","scout"],
 "policyKinds":["llm","llm","llm","scripted"],
 "llmTurns":[28,25,27,0],"fallbackTurns":[1,1,3,0],
 "fallbackCauses":[{"transport_timeout":1},{"transport_timeout":1},{"transport_timeout":3},{}],
 "tasksSolved":[0,0,0,3],"scores":[5000,3000,6000,312020]}
```

Per-turn batch latency around the three fallback turns, from `.plans[].latency_ms`:

```
turn 14: 0:llm 5500   1:llm 5500   2:llm 5500      3:scripted
turn 15: 0:llm 11000  1:llm 11000  2:FALLBACK      3:scripted   ← == attempt1Ms exactly
turn 23: 0:llm 5480   1:llm 5480   2:llm 5480      3:scripted
turn 24: 0:llm 10999  1:llm 10999  2:FALLBACK      3:scripted
turn 28: 0:llm 4839   1:llm 4839   2:llm 4839      3:scripted
turn 29: 0:FALLBACK   1:FALLBACK   2:FALLBACK      3:scripted   ← ALL THREE LLM seats at once
turn 30: 0:llm 9966   1:llm 9966   2:llm 9966      3:scripted
```

Turn 29 is decisive: the three LLM seats failed **together**. That rules out "richard's v1 policy
is the problem" and confirms the batch-latency reading below — when the concurrent batch goes over
the deadline, whichever seats are still outstanding all fall back at once. Both champions are
affected: cartographer 1 fallback turn in 29 (3.4 %), missionfirst 1 in 26 (3.8 %).

One more thing this round exposes, reported because it is a small gap in the "truthful causes"
commitment rather than a check of its own: seat 0's two attempts failed for **different** reasons —
attempt 1 `schema_error` ("reply has neither actions nor say"), attempt 2 `transport_timeout` — but
`results.fallbackCauses[0]` records only `{"transport_timeout": 1}`. The per-attempt `fallback`
control records in the replay do carry both causes, as `design.md:2246` requires; it is the
per-seat *summary* map that keeps the last cause and silently drops the first. A reader of
`fallbackCauses` alone would not learn that a champion produced one malformed reply.

Retry budget: **3 of 3 used** (round 16, round 15, round 17 — three different rounds, one of them
fetched fresh after the ladder had produced it). The check is false in all three.


### Is this the documented platform-wide exception? No — cross-check says no

`prompts/60-verify.md` §5 allows exactly one documented exception, for
`LLM provider is unavailable` as a platform-wide Bedrock **capacity** symptom, confirmed by
another LLM coworld's latest log showing the same. That string does not appear here at all, and
the cross-check comes back negative anyway. Two other **LLM** coworlds, latest episode each,
fetched fresh 2026-08-29T01:57:1xZ with the same decode-then-grep:

| coworld | episode request | Bedrock calls in log | matching lines |
|---|---|---|---|
| `procgen` (`cow_84cce351…`) | `ereq_f7e42fb2-9ab9-4130-a761-99514ad05149`, created 01:45:40Z | 80 | **0** |
| `atari-57` (`cow_4b06234f…`) | `ereq_fa821a9f-921f-46b1-9112-d16e4af45c2e`, created 01:41:55Z | 66 | **0** |

```bash
grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' x_procgen.txt  # 0
grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' x_atari57.txt  # 0
```

Both ran inside the same six-minute window as minigrid round 16 and both are clean. Bedrock is
**not** degraded platform-wide right now. There is no documented exception that covers this, so
per the verifier standard ("an undocumented exception is a failure") the item is FALSE.

### What the evidence says the cause actually is

Every upstream call in minigrid's own sidecar **succeeded**:

```bash
grep -c 'openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"' /tmp/logs16.txt   # 89
grep -cE 'HTTP/1.1 (4|5)[0-9][0-9]' /tmp/logs16.txt                        # 0
```

89 calls, 89 × `HTTP/1.1 200 OK`, zero non-2xx. Nothing was refused, throttled or truncated. The
timeouts are the **client-side deadline** expiring first. The replay's per-turn latency (the
directive `latency_ms` is the wall clock of the whole concurrent four-seat batch, identical across
the seats of a turn) shows why:

```
turn 17: 4732 ms   turn 18: 10001 ms  ← seat 2 fell back
turn 19: 10999 ms  turn 20: 6138 ms
turn 21: 5317 ms   turn 22: 11000 ms  ← seat 2 fell back  (== attempt1Ms exactly)
turn 23: 9150 ms   turn 24: 4296 ms
turn 25: 10000 ms  ← seat 2 fell back
turn 28: 10052 ms  turn 30: 5847 ms
per-seat over LLM turns:  median ≈ 5.7–6.2 s,  p90 ≈ 8.6–10.1 s,  max 11.0 s
```

The v2 addendum set `attempt1Ms = 11000` / `retryMs = 6000` on the explicit premise that *"a
`falling back` line now requires one call over 11 s and a second over 6 s against a provider whose
observed maximum is 6 712 ms — which is the fix for VERIFY check 5"*
(`docs/plans/2026-08-28-minigrid-design.md:2254-2256`). That premise no longer holds in
production: the 6 712 ms maximum was measured on the **single-seat** 0.1.0 build, and 0.1.1 issues
**three concurrent LLM calls per turn** (one per LLM lane). Batch latency now reaches the 11 000 ms
cap exactly. The ladder's headroom at p90 is about 1 second, so the slowest seat in the slowest
turn tips over — and it is usually, but not always, `richard`'s seat. The fix addressed the right
mechanism with a number derived from a distribution the four-lane redesign invalidated.

Status: **FALSE** — 4 matching lines in round 16, 4 in round 15 and 5 in round 17; none is
covered by the one documented exception, and the cross-check against two other LLM coworlds in the
same window shows the platform is healthy. Mitigating facts for the adjudicator, offered as context
and not as a pass: the fallback rate stays a small minority of decisions (3.6 % of 110 in round 16,
3.7 % of 108 in round 15, 4.4 % of 113 in round 17), the causes are now recorded truthfully as the v2
addendum required, every episode still ended `reason: complete`, and no episode was lost. The
champion seats were entirely clean in round 16 — but not in 15 or 17, so this cannot be written off
as a third-party-entrant artefact.

---

## 6. The public page uses the static replay path

**TRUE.** Source used: **the SSR payload of `https://softmax.com/minigrid` plus the session
endpoint the page's own JS calls** — the raw-HTML iframe grep finds nothing, which
`prompts/60-verify.md` §6 and `playbooks/observatory-api.md` §Featured match both say to treat as
*unknown*, not as a failure.

```bash
curl -sS "https://softmax.com/minigrid" -o /tmp/page.html      # HTTP 200, 761738 bytes
grep -o '<iframe[^>]*src="[^"]*"' /tmp/page.html || echo "NO IFRAME IN RAW HTML"
```

```
200 761738
NO IFRAME IN RAW HTML
```

(`iframe` appears 0 times in the whole document; the page is client-rendered, as the lighthouse
run recorded.) The featured match **is** server-rendered into the SSR payload at
`state.playlist[0]` — unescaped excerpt, fetched 2026-08-29T01:53:5xZ:

```json
"state":{"leagueId":"league_78d5b417-52a0-4459-8fd6-3b9aeacfe1ca",
 "playlist":[{"episodeId":"10fb10ad-0527-4933-9a17-9994a913aa7a",
   "coworldId":"cow_753b4d23-00cd-417a-99eb-b643f0f0f526",
   "coworldName":"minigrid","coworldVersion":"0.1.1",
   "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/3fe6e480-ef59-4b89-89af-01e4c825cd6b.replay",
   "finishedAt":"2026-08-29T01:49:20.705846Z","roundNumber":16,"episodeNumber":1,
   "code":"minigrid.r16.e1",
   "matchup":{"divisionId":"div_721f571a-ece7-4ed9-8b1c-15eb2cd072be","divisionName":"Competition",
     "first":{"rank":1,"player_name":"richard","score":1039.2124455408778,
              "policy_label":"co-gas-minigrid-subgoal-router-richard:v1"},
     "second":{"rank":2,"player_name":"daveey","score":1001.0113369839092,
               "policy_label":"minigrid-cartographer:v2"}},
   "inspectUrl":"/observatory/v2?tab=overview&detail=episode-request:ereq_737c8831-0e00-4a7c-868e-732a2ca0df67",
   "outcome":null}],
 …"playerCount":3,"newestCompletedAt":"2026-08-29T01:49:21.551025Z"}
```

**A featured match is present** — `minigrid.r16.e1`, the round-16 episode of §3, on
`cow_753b4d23` / `0.1.1`, with a two-player matchup card. This is the item the 0.1.0 round found
FALSE: with `num_agents: 1` the playlist was empty because a single-participant episode has no
matchup. Four-lane episodes fixed it.

The iframe `src` is produced by the call the page's JS makes:

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_753b4d23-00cd-417a-99eb-b643f0f0f526",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/3fe6e480-ef59-4b89-89af-01e4c825cd6b.replay"}'
```

Fetched 2026-08-29T01:54:1xZ — HTTP 200:

```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_753b4d23-00cd-417a-99eb-b643f0f0f526/sha256%3Afdd3b4cbd21f370c1639693a1001400fb80e3c8a7542ec9fae9b7581dc656032/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F3fe6e480-ef59-4b89-89af-01e4c825cd6b.replay",
  "ready": true
}
```

Decomposed:

| part | value | required |
|---|---|---|
| route | `/v2/coworlds/replays/static/…/index.html` | static route ✔ (no `/client/replay`) |
| `<cow_id>` | `cow_753b4d23-00cd-417a-99eb-b643f0f0f526` | = STATE `coworld.cow_id` ✔ |
| `<sha>` | `sha256%3Afdd3b4cbd21f370c1639693a1001400fb80e3c8a7542ec9fae9b7581dc656032` | = the coworld's `manifest_hash` ✔ |
| replay | `#replay=…3fe6e480-ef59-4b89-89af-01e4c825cd6b.replay` | the round-16 replay, URL-encoded fragment form ✔ |
| `ready` | `true` | static delivery ✔ |

The URL-encoded **fragment** (`?v=2#replay=`) rather than `?replay=` is the documented
2026-08-28 change (`playbooks/observatory-api.md:326`): both are the static route.

Independently, the coworld detail API confirms `cow_753b4d23` is the canonical `minigrid` at
`0.1.1` and that its `manifest_hash` is the sha in that path:

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end|.[]|select(.name=="minigrid")|{id,version,canonical,manifest_hash}'
```

```json
{"id":"cow_753b4d23-00cd-417a-99eb-b643f0f0f526","version":"0.1.1","canonical":true,
 "manifest_hash":"sha256:fdd3b4cbd21f370c1639693a1001400fb80e3c8a7542ec9fae9b7581dc656032"}
{"id":"cow_5201d3e2-0aa8-45ef-b6de-ebd76a45f329","version":"0.1.0","canonical":false, …}
```

(The `/coworlds` list returns a **bare array** here, not `{entries:…}`; the 0.1.0 coworld is still
listed but `canonical: false`. `featured_match` is not a key on these rows at all — the SSR
payload is the source, as the playbook records.)

**Re-fetched after round 17 completed**, to be sure the finding is not an artefact of one
episode. `https://softmax.com/minigrid` fetched again 2026-08-29T02:11:31Z — HTTP 200; the playlist
has rolled forward:

```json
"playlist":[{"episodeId":"b9968dc8-e539-4534-be29-c1c4bc24b9c1",
  "coworldId":"cow_753b4d23-00cd-417a-99eb-b643f0f0f526","coworldName":"minigrid",
  "coworldVersion":"0.1.1",
  "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/0746b9a3-3bf0-453b-9045-eb8a334849c0.replay",
  "finishedAt":"2026-08-29T02:04:42.329702Z","roundNumber":17,"episodeNumber":1,
  "code":"minigrid.r17.e1","matchup":{…}}]
```

and its session call (fetched 02:11:4xZ — HTTP 200) returns the same static route with the same
coworld id and the same manifest sha, differing only in the `#replay=` fragment:

```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_753b4d23-00cd-417a-99eb-b643f0f0f526/sha256%3Afdd3b4cbd21f370c1639693a1001400fb80e3c8a7542ec9fae9b7581dc656032/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F0746b9a3-3bf0-453b-9045-eb8a334849c0.replay",
  "ready": true
}
```

Status: **TRUE** — a featured match is present at both readings (`minigrid.r16.e1` at 01:53Z,
`minigrid.r17.e1` at 02:11Z), and in both the iframe `src` is the static route carrying
`cow_753b4d23` and the current manifest sha with `ready: true`. No `/client/replay` anywhere.

---

## 7. Certification declared the static bundle

**TRUE.** Source read: **the committed `runs/2026-08-28-minigrid/release-result.json`** in this
repo (the copy phase 40 wrote for release 0.1.1) — not `/tmp`, and not a re-download.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-28-minigrid/release-result.json
```

```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Contains the required `Replay liveness: skipped (static replay bundle declared`. The same file
confirms this is the **0.1.1** artifact and that certification passed in full:

```bash
jq -c '{version, ok, cow_id, manifest_sha, canonical, hosted_smoke, certify_ok:.certify.ok, secret_put, errors}' \
   runs/2026-08-28-minigrid/release-result.json
```

```json
{"version":"0.1.1","ok":true,"cow_id":"cow_753b4d23-00cd-417a-99eb-b643f0f0f526",
 "manifest_sha":"sha256:fdd3b4cbd21f370c1639693a1001400fb80e3c8a7542ec9fae9b7581dc656032",
 "canonical":true,"hosted_smoke":"passed","certify_ok":true,"secret_put":true,"errors":[]}
```

and the certify tail shows 10 of 10 transcript steps passing, ending on the liveness line:

```
  [pass] matriculate: manifest conforms to the Coworld schema
  [pass] source-resolves: … source_url that resolves to publicly accessible source
  [pass] images-reachable: every declared image is pullable or inspectable
  [pass] fixture-conforms: the certification fixture validates against game.config_schema …
  [pass] smoke-episode: the game and certification players run one episode
  [pass] results-conform: episode results validate against results_schema
  [pass] replay-present: a replay artifact was produced
  [pass] replay-loadable: the replay artifact has a declared viewer path
  [pass] players-run: every declared player actually started on the smoke episode …
  [pass] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks
Certified dist/coworld_manifest.json
Transcript: coworld-executable (10 steps passed)
…
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Bookkeeping note, stated because the prompt asks which source was used: the file **is present** in
the run directory and is the 0.1.1 artifact, so no re-download was needed — but `git log` shows the
last *commit* touching it is `3b1d983` ("40 minigrid: release-result 0.1.0"), i.e. the 0.1.1
contents are in the working tree still awaiting the coordinator's publish
(`git status` → ` M runs/2026-08-28-minigrid/release-result.json`). To make sure the working-tree
copy is genuinely this run's artifact and not a local edit, it was diffed byte-for-byte against
the artifact of the recorded release run:

```bash
gh run download 33226095645 -R Metta-AI/cogame-minigrid -n release-result -D /tmp/rrcheck
diff <(jq -S . /tmp/rrcheck/release-result.json) \
     <(jq -S . runs/2026-08-28-minigrid/release-result.json)
```

```
IDENTICAL to release run 33226095645 artifact
md5  bcf782e156a73ec3171f71fa61b78ada  (both files)
```

Status: **TRUE** — read from the run directory's `release-result.json`, verified identical to
release run `33226095645`'s artifact, and it carries
`Replay liveness: skipped (static replay bundle declared`.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged

**TRUE on both mechanical criteria** (`loaded: true`; three pairwise-distinct clock readouts).

*(a) Dispatch.* The iframe `src` from §6 was opened in headless chromium by CI. Nothing here was
rendered locally; this sandbox has no browser and no screen. The URL dispatched is the one §6's
session call returned at 01:54:1xZ — the featured match at that moment, `minigrid.r16.e1`. Round 17
completed ten minutes later and the page's featured match rolled to it; as §6 records, its viewer
URL is the identical static route with the identical coworld id and manifest sha, differing only in
the `#replay=` fragment, so the render below exercises exactly the bundle the page serves now. Only
one `viewer-check.yml` run was dispatched this session; chasing each new round would never
terminate, since the ladder produces one every 15 minutes.

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_753b4d23-00cd-417a-99eb-b643f0f0f526/sha256%3Afdd3b4cbd21f370c1639693a1001400fb80e3c8a7542ec9fae9b7581dc656032/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F3fe6e480-ef59-4b89-89af-01e4c825cd6b.replay'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
# dispatched 2026-08-29T01:54:33Z
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:4][]|[.databaseId,.createdAt,.status]|@tsv'
```

```
33227616497	2026-08-29T01:54:33Z	in_progress     ← this run (createdAt == the dispatch time)
33217780204	2026-08-28T22:41:52Z	completed       ← 0.1.0 round, not used
33217711224	2026-08-28T22:40:43Z	completed       ← 0.1.0 round, not used
33217648127	2026-08-28T22:39:40Z	completed       ← 0.1.0 round, not used
```

The run was found by sorting on `createdAt`, not by taking "the latest run" blind. It finished
**green**:

```bash
gh run view 33227616497 -R Metta-AI/coworld-builder --json status,conclusion,jobs
```

```json
{"status":"completed","conclusion":"success",
 "steps":[ …, {"name":"Load the viewer","conclusion":"success"},
               {"name":"Upload the evidence","conclusion":"success"},
               {"name":"Fail if the viewer did not load","conclusion":"success"}, … ]}
```

```bash
gh run download 33227616497 -R Metta-AI/coworld-builder -n viewer-check \
   -D runs/2026-08-28-minigrid/viewer-check
```

→ `viewer-smoke.json` (1727 B), `viewer-smoke.png` (393 990 B), `smoke-stdout.txt`,
`smoke-stderr.txt` (0 B). These files are this run's only rendered evidence; the CI sandbox that
made them is gone.

*(b) The readouts, verbatim from `runs/2026-08-28-minigrid/viewer-check/viewer-smoke.json`.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-28-minigrid/viewer-check/viewer-smoke.json
```

```json
{"loaded":true,"ms":2678,"clock":"TURN 0/30 · PHASE 1/5 · TICK 0/720 · ALPHA 0 · BETA 0 · GAMMA 0 · DELTA 0","scorebug":"— CARTOGRAPHER Carrying 0/5 ALPHA · SCORE 0 — PROMPT Carrying 0/5 GAMMA · SCORE 0 TURN 0/30 · PHASE 1/5 · TICK 0/720 · ALPHA 0 · BETA 0 · GAMMA 0 · DELTA 0 — MISSIONFIRST Carrying 0/5 BETA · SCORE 0 — SCOUT Carrying 0/5 DELTA · SCORE 0","feed_lines":4}
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
`"console_tail":[]`, and `canvas_text` `{"total":0,"outside":0,"ellipsized":0,"never_inside":0}` —
no text drawn outside the canvas and nothing ellipsized.

**The three clock readouts** (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub | clock readout |
|---|---|
| **0 %** | `TURN 0/30 · PHASE 1/5 · TICK 0/720 · ALPHA 0 · BETA 0 · GAMMA 0 · DELTA 0` |
| **50 %** | `TURN 16/30 · PHASE 3/5 · MULTIROOM TICK 361/720 · ALPHA 0 · BETA 0 · GAMMA 2 · DELTA 2` |
| **100 %** | `TURN 30/30 · PHASE 5/5 · BABYAI TICK 720/720 · ALPHA 0 · BETA 0 · GAMMA 2 · DELTA 3` |

**All three differ pairwise** — turn 0 → 16 → 30, tick 0 → 361 → 720, phase 1 → 3 → 5, and the
per-lane scores advance 0/0/0/0 → 0/0/2/2 → 0/0/2/3. This is the item the 0.1.0 round found FALSE
(50 % and 100 % were identical because click-to-seek was mis-scaled); it is fixed. `loaded: true`
via `data-replay-loaded="true"` at 2678 ms. (`bridge_ready` is `false` and `bridge` is empty: this
shell signals readiness through the DOM attribute rather than the `coworld-replay` postMessage
bridge — the check accepts either, and the attribute is present and `"true"`.)

*(c) Reconciliation against the replay JSON.* The 100 % readout says `GAMMA 2 · DELTA 3`; the
replay's `results.tasksSolved` is `[0,0,2,3]` and `results.scores` is `[3000,5000,211010,312040]`,
which is also what the API's `participant_scores` returned in §3. Tick 720/720 matches
`results.finalTick: 720`; `TURN 30/30` matches `results.turnsPlayed: 30`; `PHASE 5/5 · BABYAI`
matches `taskFamilies[4] == "babyai"`. The 50 % readout's `PHASE 3/5 · MULTIROOM` matches
`taskFamilies[2] == "multiroom"`, and its `GAMMA 2 · DELTA 2` matches the replay's
`taskSolved[2] = [true,true,false,false,false]` and `taskSolved[3] = [true,true,true,false,false]`
with Delta's third solve still ahead at that point. The picture and the record agree.

### Spectator-judgment paragraph

The screenshot (`runs/2026-08-28-minigrid/viewer-check/viewer-smoke.png`, 1280×800) is a
**legible, populated, unmistakably-minigrid frame**, captured at the end of the replay with the
endcard up. The four-lane quad layout renders: the central field is divided into four quadrants by
faint dividers, with the bottom two lanes labelled **GAMMA** and **DELTA** in their lanes' colours
and gridworld furniture — keys (small ⚷ glyphs), balls, doors, walls — drawn in each; the top two
quadrants are dimmed under the endcard overlay, which is the starter's normal end-of-replay
behaviour, so ALPHA's and BETA's boards are visible as layout but their labels are covered. The
**left gutter** carries the mission ribbon exactly as the addendum specified: `PHASE 5/5 · BABYAI`
above the sentence *"put the purple key next to the green key"*, and below it the five-task **pip
stack** — LAVAGAP, DOORKEY, MULTIROOM, KEYCORRIDOR, BABYAI — each with its own icon. The **right
gutter** carries the **POV inset**: `AGENT VIEW 7×7`, a real 7×7 cell grid with two coloured cells
(an orange object and a yellow key), captioned `DELTA · FACING WEST`, then
`POV DELTA · 3/5 · SCORE 312040`, then the feed line
`PHASE 5/5 — BABYAI: "put the purple key next to the green key"`. `feed_lines` is **4** (> 0) in
the JSON — the 0.1.0 round measured `feed_lines: 0`, so the killfeed id mismatch is fixed; at the
final frame only one feed line remains on screen, the rest having aged out. Across the top runs a
per-lane carrying banner (`0/5 Carrying PURPLE KEY`, `2/5 Carrying`, `Carrying 0/5`,
`Carrying 3/5`) with the big clock `TURN 30/30 · PHASE 5/5 · BABYAI` centred. The endcard itself
is the clearest thing on the page: **"DELTA TAKES IT — 3 OF 5 SOLVED"**, the badge
`ENDED COMPLETE (ALLLANESCOMPLETE)`, the one-line story *"30 turns across four isolated lanes,
13 doors opened, 1 death, 4 fallback turns"*, and a four-row table
`LANE / POLICY / SOLVED / CREDITS / SCORE` reading ALPHA cartographer 0/5 3/15 3000, BETA
missionfirst 0/5 5/15 5000, GAMMA prompt 2/5 11/15 211010, DELTA scout 3/5 12/15 312040 — which is
`results.scores`, `results.tasksSolved` and `results.progressTotal` verbatim. Its one-line story
reconciles too: `results.turnsPlayed` is 30, `sum(results.doorsOpened)` = 0+2+5+6 = **13**,
`sum(results.deaths)` = **1**, `sum(results.fallbackTurns)` = **4**. A spectator can therefore tell who is winning
and why without reading any JSON. It is **not empty, not frozen and not unreadable**: the scrub
table proves it advances, and the endcard proves it explains itself.

**Does it look like the starter's chrome?** Yes. The bottom transport strip is coworld-ctf's:
restart / step-back / play / `+5s` / step-forward / loop / fast-forward buttons, a `spoilers`
toggle, a `DELTA — PAR MET 720 / 721` status readout, the `1× 2× 3× 4× 8× 16×` speed selector,
and the **`PROGRESS` scrubber with the momentum graph** — four coloured traces climbing across the
timeline with per-lane tick marks above them — which is the same widget paintbot/raid/hive ship.
The scorebug, endcard and colour language are the same family. This is a fork of the starter, not
the cogame-gridlock failure mode of a rewrite that merely shares ids.

**Legibility observations for phase 30 (non-blocking, none of them make this item false).**
(i) The top strip is crowded at 1280 px: the small per-lane score chips collide —
`ALPHA SCORE 3000` and `GAMMA SCORE 211010` overlap around x≈380-460, and the centred
`TICK 720/720 · ALPHA 0 · BETA 0 · GAMMA 2 · DELTA 3` line is squeezed between them. (ii) The
second lane's carrying banner shows a bare `—` where the carried item name should be. (iii) At the
final frame only one feed line survives on screen even though four were counted at load, so the
right gutter looks sparser than it is mid-replay. (iv) The endcard is opaque enough to hide the
top two lanes' labels entirely, so a spectator who arrives at the end cannot tell which quadrant
was ALPHA and which was BETA without scrubbing back.

Status: **TRUE** — `loaded: true`, three pairwise-distinct clock readouts, `feed_lines: 4`, a
scorebug naming all four seats, no failure, and a rendered frame that is legible, that shows the
game, and that reads as the starter's chrome.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 15 and 16 (both all-v2 entrants) completed after the v2 filler pair went live; round 17 followed; zero failed/discarded in the whole league |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey r2 / daveey-1 r3, 16 rounds each; fillers absent |
| 3 | Latest round's episode request completed with replay | **TRUE** — `ereq_737c8831…` completed, 4 participants, daveey + daveey-1 |
| 4 | Replay bytes valid and show the game | **TRUE** — strict JSON, `minigrid/v1`, reason `complete`, 80 LLM / 4 fallback decisions, champions 0 fallbacks |
| 5 | Hosted game log clean | **FALSE** — `falling back … (transport_timeout)`: 4 lines in round 16 (all third-party seat), 4 in round 15 (one champion seat), 5 in round 17 (both champion seats, all three LLM seats on turn 29); no documented exception applies |
| 6 | Public page uses the static replay path | **TRUE** — featured match present at both readings (`minigrid.r16.e1` 01:53Z, `minigrid.r17.e1` 02:11Z); static route, `cow_753b4d23`, manifest sha, `ready:true`, never `/client/replay` |
| 7 | Certification declared the static bundle | **TRUE** — `Replay liveness: skipped (static replay bundle declared…` |
| 8 | Spectator judgment (executed viewer) | **TRUE** — `loaded:true` at 2678 ms, three distinct clocks, `feed_lines:4`, legible quad frame |

For STATE:

```
verify.rounds       = [{"n":15,"id":"round_a4dba3c3-d5c7-4e62-9eda-40ce114e6f1c"},
                       {"n":16,"id":"round_6f2dadf4-b743-4f29-b9f4-119141ca8db7"},
                       {"n":17,"id":"round_44adaf2b-3ee7-44db-8076-05fc55ce7b6f"}]
                      # all three are qualifying (both champions on v2, v2 fillers live);
                      # checks 3/4/6/8 were executed against round 16, round 17 completed after
verify.replay       = "https://softmax-public.s3.amazonaws.com/replays/3fe6e480-ef59-4b89-89af-01e4c825cd6b.replay"
verify.iframe_static = true
verify.viewer_check_run = "33227616497"
```
