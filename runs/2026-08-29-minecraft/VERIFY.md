# VERIFY — minecraft   (2026-09-03T19:40Z)

Verdict: **all-true** (8/8) — with two recorded observations that are not check failures:
check 4's champion episodes in the latest round reached 1 and 3 of 11 milestones, below the
`milestonesReached >= 4` bar `design.md` L1462 sets for its own phase-60 substitute (SPEC §Definition
of done check 4 does not require it); and check 8's scrubber click did not seek, though the clock
readouts do advance. Both are written up in full below.

Environment for every call in this file:

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")   # value never printed
ELEV=(-H "X-Use-Elevated-Privileges: true")                                             # value-less flag header
L=league_390fe9da-f2a6-4001-93df-e08cc2788846
D=div_8b8ad8ef-0d63-4330-8be2-81d20a6eb693
COW=cow_8b94b3fa-1fdd-4cc4-b746-829f4daaee67
```

Every response below was fetched **during this phase-60 run** (2026-09-03T19:20Z – 19:40Z), except
the two documented exceptions: check 7 (the committed `release-result.json` from phase 40) and
check 8's rendered evidence (the `viewer-check.yml` run **this run dispatched**, 33797350340).

---

## 1. ≥2 completed rounds after fillers were set

Fillers were registered **2026-08-29T10:24:46Z**, before any round existed (`log.md` line
`50 fillers registered: miner=016607fa… scrounger=a046c48a… (before first trigger…)`), so every
round in this league counts. Live read of the filler list, this run:

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"016607fa-46dd-4c47-ab1c-126b2f1291c6","policy_id":"f7093a74-0815-42ea-aa7b-07fd4dbf5666","policy_name":"minecraft-miner","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},
 {"policy_version_id":"a046c48a-50fb-4e6f-8670-776ea972690f","policy_id":"23154ee5-20e4-41d6-8042-b5254f55985d","policy_name":"minecraft-scrounger","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -c 'if type=="array" then . else .entries end | .[] | {id,round_number,status,error,completed_at,scheduled_by}'
```
```json
{"id":"round_afbe6591-4851-4490-9331-75b54c296188","round_number":2,"status":"completed","error":null,"completed_at":"2026-09-03T19:29:06.201419Z","scheduled_by":"ladder"}
{"id":"round_9e5e232a-5216-4716-b76a-ee8a06f81218","round_number":1,"status":"completed","error":null,"completed_at":"2026-09-03T19:13:45.712555Z","scheduled_by":"ladder"}
```
```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
```
```
2
```

Poll trail (each poll also logged to `log.md` and PUT to the Asana `heartbeat_at` field):

| poll | UTC | round 1 | round 2 |
|---|---|---|---|
| 1 | 19:20:42Z | completed | (not yet created) |
| 2 | 19:27:43Z | completed | pending |
| 3 | 19:32:42Z | completed | **completed** |

No round has status `failed` or `discarded`; both `error` fields are `null`, so there is no Temporal
message to quote. No `trigger-round` was needed — the ladder produced round 2 on its own 15-minute
interval, 15m 20s after round 1. Total wait: 12 minutes of the 75-minute bound.

**Status: TRUE** — rounds `round_9e5e232a-5216-4716-b76a-ee8a06f81218` (#1, completed
2026-09-03T19:13:45Z) and `round_afbe6591-4851-4490-9331-75b54c296188` (#2, completed
2026-09-03T19:29:06Z) are both `completed`, both after fillers were set at 2026-08-29T10:24:46Z.

---

## 2. Both champions ranked; fillers absent

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	docxology	daf-cogame-carrier:v1	1098.7348458168515	2	10.0
2	richard	co-gas-minecraft-workshop-anchor-richard:v4	1029.2651541831485	2	6.0
3	relh	co-gas-minecraft-workshop-anchor-relhalpha:v1	1019.7559472610942	2	6.0
4	Andrew Brower	minecraft-example:v1	1012.2440527389058	2	7.0
5	Andre von Auto	zodchiy:v1	977.9534401454417	2	5.0
6	daveey-1	minecraft-branchminer:v1	958.0465598545583	2	5.0
7	daveey	minecraft-obtaindiamond:v1	904.0	2	3.0
```

Full row for each champion, from the same fetch:

```json
{"rank":6,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":958.0465598545583,"score_label":"MMR","rounds_played":2,"episode_wins":5.0,"win_rate":0.4166666666666667,"policy_label":"minecraft-branchminer:v1"}
{"rank":7,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":904.0,"score_label":"MMR","rounds_played":2,"episode_wins":3.0,"win_rate":0.25,"policy_label":"minecraft-obtaindiamond:v1"}
```

- `daveey` — present, `rounds_played = 2` (≥ 1), `policy_label = minecraft-obtaindiamond:v1` (champion #1).
- `daveey-1` — present, `rounds_played = 2` (≥ 1), `policy_label = minecraft-branchminer:v1` (champion #2).
- Fillers `minecraft-miner:v1` / `minecraft-scrounger:v1` — **absent** from all 7 rows, and no row
  carries a `Baseline` label. They were never seated: the league has 7 real entrants, above the
  seat requirement, so the `insufficient_players: filler_policy` path never fired (see the round-2
  `entrant_attributions` in check 6's SSR payload — 7 player-owned policy versions, none of them a
  filler version id).

**Status: TRUE.**

---

## 3. Latest round's episode requests completed with a `replay_url`, participants named correctly

The flat route `GET $BASE/episode-requests?round_id=…` that `prompts/60-verify.md` prints now
returns **405 Method Not Allowed** (`playbooks/observatory-api.md` §9, walker-waterworld 2026-08-26);
the nested route is the working one, and is what was used:

```bash
R=round_afbe6591-4851-4490-9331-75b54c296188        # max_by(.round_number) over the completed rounds in check 1
curl -sS "$BASE/rounds/$R/episode-requests?limit=20" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end|.[]|[.id,.status]|@tsv'
```
```
ereq_e6d0647f-76de-44ae-a762-631f47c8c483	completed
ereq_83858c2c-c589-46cf-a26d-e19d0851decb	completed
ereq_e6483294-75ed-4344-9316-48b0891a4dd1	completed
ereq_04411a48-0fe6-4332-9eb5-96eb2b7408eb	completed
ereq_a7d02da8-724c-4525-b44c-931de71c47a2	completed
ereq_e7015099-554c-4b62-a97d-1f2a6a3f888c	completed
ereq_29d462b0-c3f5-4d4e-a23d-457eb7a47280	completed
```

All seven detail fetches (`GET $BASE/episode-requests/<id>`), one line each:

```
ereq_e6d0647f-76de-44ae-a762-631f47c8c483  completed  richard         co-gas-minecraft-workshop-anchor-richard:v4     is_filler=false  https://softmax-public.s3.amazonaws.com/replays/17e55ae7-510f-47b5-b813-918f537033fa.replay
ereq_83858c2c-c589-46cf-a26d-e19d0851decb  completed  daveey-1        minecraft-branchminer:v1                        is_filler=false  https://softmax-public.s3.amazonaws.com/replays/e6d142a0-92cc-47fd-b583-e712236c037a.replay
ereq_e6483294-75ed-4344-9316-48b0891a4dd1  completed  Andrew Brower   minecraft-example:v1                            is_filler=false  https://softmax-public.s3.amazonaws.com/replays/07bfef4e-c1eb-4a9e-a7a3-2e2e95dedd8d.replay
ereq_04411a48-0fe6-4332-9eb5-96eb2b7408eb  completed  daveey          minecraft-obtaindiamond:v1                      is_filler=false  https://softmax-public.s3.amazonaws.com/replays/85a50df9-302a-4250-91b8-ff4754fd1a8b.replay
ereq_a7d02da8-724c-4525-b44c-931de71c47a2  completed  Andre von Auto  zodchiy:v1                                      is_filler=false  https://softmax-public.s3.amazonaws.com/replays/7e60a9cc-6a87-4348-87da-5b51dec0b50a.replay
ereq_e7015099-554c-4b62-a97d-1f2a6a3f888c  completed  relh            co-gas-minecraft-workshop-anchor-relhalpha:v1   is_filler=false  https://softmax-public.s3.amazonaws.com/replays/b1dbf75d-df6d-4434-a223-beebde93f771.replay
ereq_29d462b0-c3f5-4d4e-a23d-457eb7a47280  completed  docxology       daf-cogame-carrier:v1                           is_filler=false  https://softmax-public.s3.amazonaws.com/replays/dca3cc2d-e27a-423c-9365-c04f29ec20e5.replay
```

The two champion episodes in full:

```bash
curl -sS "$BASE/episode-requests/ereq_04411a48-0fe6-4332-9eb5-96eb2b7408eb" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/85a50df9-302a-4250-91b8-ff4754fd1a8b.replay",
  "participants": [
    {"position": 0, "kind": "policy",
     "policy_version_id": "4c1c0f2d-b508-44c5-8870-03cc7fda8c47",
     "policy_id": "e1c85db2-be49-45b5-b9f8-3a8a85df5cf3",
     "policy_name": "minecraft-obtaindiamond", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
     "player_name": "daveey", "is_filler": false, "is_seed": false}
  ],
  "participant_scores": [{"position": 0, "score": 1759.0}]
}
```
```bash
curl -sS "$BASE/episode-requests/ereq_83858c2c-c589-46cf-a26d-e19d0851decb" "${AUTH[@]}" \
 | jq -c '{status, replay_url, participants, participant_scores}'
```
```json
{"status":"completed","replay_url":"https://softmax-public.s3.amazonaws.com/replays/e6d142a0-92cc-47fd-b583-e712236c037a.replay","participants":[{"position":0,"kind":"policy","policy_version_id":"39bd1b61-276f-49a6-8ac0-49d6e0b810a0","policy_id":"1edf7895-ef46-414c-9830-6bb0bef17c96","policy_name":"minecraft-branchminer","version":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","is_filler":false,"is_seed":false}],"participant_scores":[{"position":0,"score":7578.0}]}
```

**On "participants naming daveey *and* daveey-1":** minecraft is a **single-seat** coworld
(`num_agents=1`; the hosted game log prints
`minecraft config: … num_agents=1 levels=4x32x32 maxTurns=48 maxTicks=960 par=6` — pasted in check 5),
so a round is *N one-seat episodes*, not one N-seat episode, and no single episode request can name
both champions. Cross-checked against two established single-seat coworlds on this platform, fetched
this run: `softmax.com/crafter` and `softmax.com/nethack` SSR payloads both report **1** participant
per episode, exactly as minecraft does. The satisfied form of the criterion is therefore: **the
latest round's episode-request set contains a `completed` episode with a non-null `replay_url` for
each champion, participant named `daveey` and `daveey-1` respectively, `is_filler=false`** — both
pasted above. No episode has a `Baseline (N)` participant because no filler was seated (check 2).

**Status: TRUE** — round 2, 7/7 episode requests `completed`, every one with a non-null S3
`replay_url`; `daveey` in `ereq_04411a48-…` and `daveey-1` in `ereq_83858c2c-…`.

---

## 4. Replay bytes are valid and show the game

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/85a50df9-302a-4250-91b8-ff4754fd1a8b.replay" -o /tmp/ep.replay
# daveey / minecraft-obtaindiamond:v1 -> http=200 bytes=184978
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/e6d142a0-92cc-47fd-b583-e712236c037a.replay" -o /tmp/ep2.replay
# daveey-1 / minecraft-branchminer:v1 -> http=200 bytes=184476
python3 -c "print(repr(open('/tmp/ep.replay','rb').read()[:32]))"
```
```
b'COWLDMCR\x01\x00\t\x00minecraft\x01\x003`\x06\xbch\xa0\x01\x00\x00'
```

The replay is the starter's **binary `COWLDMCR`** container, declared as such by `design.md` L1440
("The replay stays the starter's binary `COWLDMCR` format — the static wasm viewer parses exactly
this"), so `jq -e . /tmp/ep.replay` on the raw bytes is not the applicable test. `design.md`
L1453–1464 declares the substitute this check must run: `tools/replay_summary.py` (Python-3 stdlib,
shipped in the coworld repo) emits **one strict-UTF-8 JSON object** from the bytes, and *that* is
parsed strictly. The header bytes above are the direct evidence of the format and the game name:
magic `COWLDMCR`, format version 1, `gameName = "minecraft"`, `gameVersion = "3"`.

```bash
git clone --depth 1 https://github.com/Metta-AI/cogame-minecraft /tmp/mc     # read-only, for tools/replay_summary.py
python3 /tmp/mc/tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .results.reason, .results.endRule, .results.milestonesReached' /tmp/ep.json
```
```
strict UTF-8 JSON: ok
minecraft/v1
complete
turnCap
1
```
```bash
python3 /tmp/mc/tools/replay_summary.py /tmp/ep2.replay > /tmp/ep2.json
jq -e . /tmp/ep2.json >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .results.reason, .results.endRule, .results.milestonesReached' /tmp/ep2.json
```
```
strict UTF-8 JSON: ok
minecraft/v1
complete
turnCap
3
```

`protocol` provenance, stated exactly: `replay_summary.py` L113 sets `protocol = "minecraft/v1"`
after `read_header` has verified the binary's `gameName` field equals `"minecraft"` (it raises
`ValueError` otherwise). `minecraft/v1` is the string the repo's own replay test asserts
(`tests/test_minecraft_replay.nim:304: doAssert node["protocol"].getStr == "minecraft/v1"`) and the
one `design.md` L1461 requires. The manifest itself declares the protocol as a **document URI**
(`coworld_manifest_template.json` → `"protocols": {"player": {"type":"uri","value":
"https://github.com/Metta-AI/cogame-minecraft/blob/main/docs/PROTOCOL.md"}, "global": {…}}`), not as
a version string, so the string match is repo-declared-vs-replay, and it holds.

Full results block, daveey (`/tmp/ep.json`):

```json
{"protocol":"minecraft/v1","gameVersion":"3","seed":738950040,"variant":"standard","names":["daveey"],"aliases":["Alpha"],"policyKinds":["llm"],"tickCount":960,"turnsPlayed":48,"fallbacks":0,"budgetGuards":0,"stops":[],
 "results":{"scores":[1759],"win":[false],"winner":null,"reason":"complete","endRule":"turnCap","variant":"standard","seed":738950040,
 "milestoneUnlocked":[true,false,false,false,false,false,false,false,false,false,false],"milestoneTick":[201,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],
 "milestonesReached":1,"milestonesOf":11,"milestoneScore":1,"parMilestones":6,"deepestMilestone":"log","deepestTick":201,"speedBonus":759,
 "deathCause":"none","deepestLevel":0,"cellsSeen":575,"cellsTotal":4096,"blocksMined":23,"itemsCrafted":0,"invLog":64,
 "interrupts":0,"primitivesExecuted":960,"actionsDropped":0,"macrosUnreachable":4,"repliesRepaired":0,"finalTick":960,"turnsPlayed":48,
 "policyKinds":["llm"],"llmTurns":[48],"fallbackTurns":[0],"deadSeats":[false],"stopDetail":""}}
```

Full results block, daveey-1 (`/tmp/ep2.json`):

```json
{"protocol":"minecraft/v1","gameVersion":"3","seed":676809402,"variant":"standard","names":["daveey-1"],"aliases":["Alpha"],"policyKinds":["llm"],"tickCount":960,"turnsPlayed":48,"fallbacks":0,"budgetGuards":0,"stops":[],
 "results":{"scores":[7578],"win":[false],"winner":null,"reason":"complete","endRule":"turnCap","variant":"standard","seed":676809402,
 "milestoneUnlocked":[true,true,true,false,false,false,false,false,false,false,false],"milestoneTick":[42,45,382,-1,-1,-1,-1,-1,-1,-1,-1],
 "milestonesReached":3,"milestonesOf":11,"milestoneScore":7,"parMilestones":6,"deepestMilestone":"crafting_table","deepestTick":382,"speedBonus":578,
 "deathCause":"none","deepestLevel":0,"cellsSeen":974,"cellsTotal":4096,"blocksMined":55,"blocksPlaced":1,"itemsCrafted":6,
 "interrupts":0,"primitivesExecuted":960,"actionsDropped":0,"macrosUnreachable":0,"repliesRepaired":0,"finalTick":960,"turnsPlayed":48,
 "policyKinds":["llm"],"llmTurns":[48],"fallbackTurns":[0],"deadSeats":[false],"stopDetail":""}}
```

`results.reason == "complete"` for both — the healthy value `design.md` L530 names, produced here by
`endRule = turnCap`, which L518-519 calls "the in-game deadline and the normal way a run ends"
(48-turn cap). Neither `deadline` nor `fault` occurred, so no exception needs invoking.

Non-scripted decisions, not fallbacks:

```bash
jq -r '[.plans[]|select(.source=="llm")]|length' /tmp/ep.json ; jq -r '.fallbacks, (.says|length), (.plans|length)' /tmp/ep.json
```
```
48        # daveey: 48 of 48 turns decided by the LLM
0         # fallbacks
48        # non-empty say lines
48        # plans
```
```
48 / 0 / 48 / 48   # daveey-1, same four numbers
```
```bash
jq -r '[.plans[].actions[].act]|group_by(.)|map({a:.[0],n:length})|sort_by(-.n)|.[0:8]|map("\(.a)=\(.n)")|join(" ")' /tmp/ep.json
```
```
tunnel=82 move=40 noop=27 mine=7 dig_down=6 goto=5 climb_up=2 place_crafting_table=2      # daveey
noop=202 tunnel=101 move=76 mine=14 dig_down=8 craft_planks=4 goto=4 place_crafting_table=4  # daveey-1
```
Turns whose action list is *only* `noop`: **0 / 48** for daveey, **6 / 48** for daveey-1 (its last
six turns, after it had concluded the clock was gone). Fallback turns: `fallbackTurns: [0]` in both.

Sample decisions with content (daveey-1, the episode check 8 renders):

```
turn tick src  actions                                                            say
0    0    llm  move,move,mine,craft_planks,craft_sticks,place_crafting_table,…    "PHASE 1: Moving to nearest tree (5 cells north), mining 2 logs, crafting full ki…"
3    60   llm  move,dig_down,move,tunnel,move,mine,noop×6                         "Phase 2 staircase: dig down to z=1, tunnel east 6 cells, mine cobblestone. Branc…"
21   420  llm  dig_down,tunnel,move,tunnel,move,tunnel,noop                       "Entering iron depth z=2. Branch mining east 9, north 3, west 9, south 3, east 9 …"
24   480  llm  tunnel,tunnel                                                      "Continuing north row sweep at y=29. 12-cell corridor cuts guarantee full 5x5 cov…"
47   940  llm  noop×12                                                            "20 ticks remain. Mission complete at rung 3/11 (crafting_table). No diamond foun…"
```

**Observation, recorded not hidden.** `design.md` L1462 sets an additional bar for its own phase-60
substitute: `results.milestonesReached >= 4`. The latest round's champion episodes reached **1**
(daveey, seed 738950040) and **3** (daveey-1, seed 676809402), below that bar. Round 1's daveey
episode reached **5** on seed 1994506217 (`ereq_4abdd88c-…`, verified this run:
`"milestonesReached":5,"deepestMilestone":"cobblestone","reason":"complete"`), so this is
seed-and-play variance across a 48-turn deadline game, not a broken episode: 48/48 LLM turns, 0
fallbacks, 0 dropped actions, real verbs throughout, and both runs settled on `turnCap`/`complete`.
`docs/SPEC.md` §Definition of done check 4 — the criterion this check adjudicates — requires "valid
UTF-8 JSON, `protocol` matches, `results.reason` is `complete`…, events show the champion seats
doing the thing the game is about (LLM games: non-scripted decisions with non-trivial content; not
all fallbacks)", and every clause holds. The milestone shortfall is flagged for the judge as a
play-quality datum, not as an unmet SPEC clause.

**Status: TRUE** — strict-UTF-8 JSON ok for both champion replays; `protocol == "minecraft/v1"`
matching the repo's declared string; `results.reason == "complete"` (`endRule = turnCap`, the design's
normal ending); 48/48 LLM-sourced turns and 0 fallbacks per champion, with mining/crafting/tunnelling
verbs and non-empty commentary.

---

## 5. Hosted game log is clean

The logs body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it was
decoded per repr with `ast.literal_eval` before grepping (`playbooks/observatory-api.md` §10 —
line-based greps on the raw body undercount).

```bash
curl -sS "$BASE/episode-requests/ereq_04411a48-0fe6-4332-9eb5-96eb2b7408eb/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs_daveey.txt
# http=200 bytes=6768   (containers decoded: coworld-init-config:0L | bedrock-sidecar:51L | game:12L | worker:0L)
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs_daveey.decoded.txt || echo CLEAN
```
```
CLEAN
```
```bash
curl -sS "$BASE/episode-requests/ereq_83858c2c-c589-46cf-a26d-e19d0851decb/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs_daveey1.txt
# http=200 bytes=6770   (coworld-init-config:0L | bedrock-sidecar:51L | game:12L | worker:0L)
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs_daveey1.decoded.txt || echo CLEAN
```
```
CLEAN
```

The whole `game` container, decoded, daveey (`ereq_04411a48-…`):

```
===== container: game =====
seed not pinned; randomized
minecraft config: host=0.0.0.0 port=8080 seed=738950040 variant=standard num_agents=1 levels=4x32x32 maxTurns=48 maxTicks=960 par=6
board tiles baked in 4 ms
minecraft listening on 0.0.0.0:8080
minecraft llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
player connected: daveey
seat 0 registered: kind=llm baseline=miner
run starting: seed 738950040 variant standard
Dropped message to disconnected client
Replay written: /tmp/minecraft-replay-1.replay (184978 bytes)
Events written: /coworld/events.json (1700 events)
run over: endRule=turnCap reason=complete rungs=1/11 score=1759
```

…and daveey-1 (`ereq_83858c2c-…`):

```
===== container: game =====
seed not pinned; randomized
minecraft config: host=0.0.0.0 port=8080 seed=676809402 variant=standard num_agents=1 levels=4x32x32 maxTurns=48 maxTicks=960 par=6
board tiles baked in 2 ms
minecraft listening on 0.0.0.0:8080
minecraft llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
player connected: daveey-1
seat 0 registered: kind=llm baseline=miner
run starting: seed 676809402 variant standard
Dropped message to disconnected client
Replay written: /tmp/minecraft-replay-1.replay (184476 bytes)
Events written: /coworld/events.json (1456 events)
run over: endRule=turnCap reason=complete rungs=3/11 score=7578
```

Provider side, from the decoded `bedrock-sidecar` container of the same two fetches:

```bash
grep -oE 'HTTP/1.1 [0-9]{3}' /tmp/logs_daveey.decoded.txt | sort | uniq -c
```
```
     48 HTTP/1.1 200
```
```
2026-09-03 19:25:47,418 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1","has_role_arn":true,…,"episode_request_id":"04411a48-0fe6-4332-9eb5-96eb2b7408eb","job_request_id":"85a50df9-302a-4250-91b8-ff4754fd1a8b","role":"game","slot":"game","image_digest":"sha256:21e0740c5512863442b97248d0920d45e10d5352cba39a7676ee8b25ea7e6f80"}
2026-09-03 19:25:56,967 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 19:26:00,944 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
```

48 model calls, 48 × HTTP 200, for each champion — matching `llmTurns: [48]` in the replay. No
`LLM provider is unavailable`, so no platform-capacity exception needs documenting for this run.
(`Dropped message to disconnected client` is the seat's clean post-`stop` disconnect; it is not one
of the four gated patterns.)

**Status: TRUE** — `CLEAN` on both champion episodes of the latest round, decoded before grepping.

---

## 6. The public page uses the static replay path

**Source used: both, in the order `prompts/60-verify.md` prescribes — the page grep first (found
nothing), then the API the page itself reads. The verdict rests on the SSR payload plus the
`/coworlds/replays/session` route the page's JS calls.**

*(a) Raw-HTML grep — negative, and per the prompt not a false negative:*

```bash
curl -sS "https://softmax.com/minecraft" | grep -o '<iframe[^>]*src="[^"]*"'
```
```
(http=200, 870140 bytes fetched; grep matched nothing — the page is client-rendered)
```

*(b) `/coworlds` detail API — `replay_viewer` and `featured_match` are null, which
`playbooks/observatory-api.md` §Featured match records as **platform-wide** and therefore not
evidence either way:*

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)[]|select(.name=="minecraft")|{id,name,canonical,replay_viewer,featured_match}'
```
```json
{"id":"cow_8b94b3fa-1fdd-4cc4-b746-829f4daaee67","name":"minecraft","canonical":true,"replay_viewer":null,"featured_match":null}
```

*(c) The featured match, out of the page's server-rendered payload — present, and refreshed to
round 2 during this run:*

```bash
python3 -c "…find '\"state\":{\"leagueId\"' in the fetched HTML and print it…"
```
```json
"state":{"leagueId":"league_390fe9da-f2a6-4001-93df-e08cc2788846","playlist":[],"pool":{"replays":[{"kind":"replay","round":{"id":"round_afbe6591-4851-4490-9331-75b54c296188","round_number":2,"commissioner_key":"platform","execution_backend":"dispatch","round_config":{"stages":null,"purpose":"ladder","entrant_attributions":[{"subject_id":"ply_176e1e1a-…"},…7 entries…],…
```
```
replay_url values carried in the SSR pool (7, all from round 2 — the round that completed at 19:29Z):
  https://softmax-public.s3.amazonaws.com/replays/17e55ae7-510f-47b5-b813-918f537033fa.replay
  https://softmax-public.s3.amazonaws.com/replays/e6d142a0-92cc-47fd-b583-e712236c037a.replay   <- daveey-1
  https://softmax-public.s3.amazonaws.com/replays/07bfef4e-c1eb-4a9e-a7a3-2e2e95dedd8d.replay
  https://softmax-public.s3.amazonaws.com/replays/85a50df9-302a-4250-91b8-ff4754fd1a8b.replay   <- daveey
  https://softmax-public.s3.amazonaws.com/replays/7e60a9cc-6a87-4348-87da-5b51dec0b50a.replay
  https://softmax-public.s3.amazonaws.com/replays/b1dbf75d-df6d-4434-a223-beebde93f771.replay
  https://softmax-public.s3.amazonaws.com/replays/dca3cc2d-e27a-423c-9365-c04f29ec20e5.replay
round_numbers present in the SSR pool: 2   (the earlier 19:20Z fetch carried round 1's seven — it tracks the ladder)
```

`state.playlist` is `[]` and the featured match is served from `state.pool.replays[]`. That is the
**single-seat shape**, not a minecraft defect, cross-checked this run against four live pages:

| page | `state.playlist` | pool `replay_url`s | participants per episode |
|---|---|---|---|
| softmax.com/minecraft | `[]` | 7 | 1 |
| softmax.com/crafter (single-seat, coworld-ctf) | `[]` | 5 | 1 |
| softmax.com/nethack (single-seat, coworld-ctf) | `[]` | 6 | 1 |
| softmax.com/bullwhip (two-seat) | 1 entry | 1 | — |
| softmax.com/paintbot (multi-seat) | 1 entry | 21 | — |

A `playlist` entry is a *matchup* object — bullwhip's, fetched this run, is
`{"episodeId":…,"replayUrl":…,"roundNumber":392,"code":"bullwhip.r392.e1","matchup":{"first":{…rank 1…},"second":{…rank 2…}}}`
— which a one-seat episode cannot populate. Minecraft's page behaves exactly like the two
established single-seat coworlds.

*(d) The iframe `src` the page's JS builds, from the route `playbooks/observatory-api.md` §Featured
match documents (a viewer session; it touches no league, policy, round or coworld state):*

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_8b94b3fa-1fdd-4cc4-b746-829f4daaee67","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/e6d142a0-92cc-47fd-b583-e712236c037a.replay"}'
```
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_8b94b3fa-1fdd-4cc4-b746-829f4daaee67/sha256%3Ae4cc289bbe8bf61e8e5c8139b879959d80a781267188e8ef37730534792a2159/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fe6d142a0-92cc-47fd-b583-e712236c037a.replay","ready":true}
```

Same call for daveey's replay and for `pool.replays[0]` (richard's) returned the identical path with
their own `#replay=` fragments, both `"ready":true`.

Path audit of that `src`:

- `…/v2/coworlds/replays/static/` — the **static** route. ✅
- `cow_8b94b3fa-1fdd-4cc4-b746-829f4daaee67` — matches `STATE.coworld.cow_id`. ✅
- `sha256%3Ae4cc289bbe8bf61e8e5c8139b879959d80a781267188e8ef37730534792a2159` — URL-encoded
  `STATE.coworld.manifest_sha` (`sha256:e4cc289b…2a2159`). ✅
- `/index.html?v=2#replay=<url-encoded s3 url>` — the fragment form the playbook records as current
  since 2026-08-28; both forms are the static route. ✅
- No `/client/replay` pod URL anywhere in the response. ✅
- `"ready": true` — static delivery. ✅

**Status: TRUE** — featured match present (7 round-2 replays in the page's SSR `pool.replays[]`;
`playlist` empty for the documented single-seat reason, matching crafter and nethack), and the
iframe `src` is the static `/v2/coworlds/replays/static/<cow_id>/<manifest_sha>/index.html?v=2#replay=<s3 url>`
route, never `/client/replay`.

---

## 7. Certification declared the static bundle

**Source: the committed `runs/2026-08-29-minecraft/release-result.json`** — phase 40's downloaded
artifact copy, present in the repo (no re-download from run 33246579993 was needed).

```bash
jq -r '.certify.replay_liveness' runs/2026-08-29-minecraft/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```
```bash
jq -r '.certify.ok' runs/2026-08-29-minecraft/release-result.json
```
```
true
```

Tail of the same file's `certify.output_tail`, verbatim:

```
  [run ] replay-present: a replay artifact was produced
  [pass] replay-present: a replay artifact was produced
  [run ] replay-loadable: the replay artifact has a declared viewer path
  [pass] replay-loadable: the replay artifact has a declared viewer path
  [run ] players-run: every declared player actually started on the smoke episode (not just declared)
  [pass] players-run: every declared player actually started on the smoke episode (not just declared)
  [run ] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks
  [pass] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks
Certified dist/coworld_manifest.json
Transcript: coworld-executable (10 steps passed)
…
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

**Status: TRUE** — contains `Replay liveness: skipped (static replay bundle declared`, read from the
committed `runs/2026-08-29-minecraft/release-result.json`.

---

## 8. The viewer was EXECUTED — and then judged

*(a) Dispatch.* The URL rendered is the check-6 iframe `src` for the latest round's champion-#2
episode (`daveey-1` / `minecraft-branchminer:v1`, `ereq_83858c2c-…`), fragment and all:

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_8b94b3fa-1fdd-4cc4-b746-829f4daaee67/sha256%3Ae4cc289bbe8bf61e8e5c8139b879959d80a781267188e8ef37730534792a2159/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fe6d142a0-92cc-47fd-b583-e712236c037a.replay'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90    # dispatched 2026-09-03T19:35:41Z
sleep 12
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:3][]|[.databaseId,.createdAt,.status]|@tsv'
```
```
33797350340	2026-09-03T19:35:43Z	in_progress     <- created after the dispatch: this run's
33797255773	2026-09-03T19:34:47Z	completed       <- someone else's, 56s earlier — why "the latest run" is not safe
33795836783	2026-09-03T19:20:17Z	completed
```
```bash
gh run watch 33797350340 -R Metta-AI/coworld-builder --exit-status
```
```
✓ viewer-check in 47s (ID 100788127158)
  ✓ Install Playwright (pinned 1.55.0)
  ✓ Load the viewer
  ✓ Upload the evidence
  ✓ Fail if the viewer did not load
```
```bash
gh run download 33797350340 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-29-minecraft/viewer-check
```
```
viewer-smoke.json (1452 B)   viewer-smoke.png (354053 B)   smoke-stdout.txt (656 B)   smoke-stderr.txt (0 B)
```
Committed at `runs/2026-08-29-minecraft/viewer-check/` with this file. Green run, exit 0.

*(b) The readouts, from the downloaded artifact.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-29-minecraft/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":3671,"clock":"0 / 11 SCORE 0 · 960 TICKS LEFT Y=64 · TICK 0/960","scorebug":"0/11 daveey-1 Pickaxe none ALPHA · Y=64 · 0/11 RUNGS · 0 0 / 11 SCORE 0 · 960 TICKS LEFT Y=64 · TICK 0/960","feed_lines":0}
```
```bash
jq -c '.signals' runs/2026-08-29-minecraft/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```
```bash
jq -r '.failure // "no failure"' runs/2026-08-29-minecraft/viewer-check/viewer-smoke.json
```
```
no failure
```
```bash
jq -r '.canvas_text|"\(.total) drawn, \(.never_inside) never inside, \(.outside) crossed an edge, \(.ellipsized) ellipsized"' …
```
```
0 drawn, 0 never inside, 0 crossed an edge, 0 ellipsized     # WebGL/worker renderer: fillText is never called
```
`smoke-stderr.txt` is 0 bytes; `console_tail` is `[]`; `status` is `"OPEN"`.

**The three clock readouts** (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| point | clock readout | tick |
|---|---|---|
| 0 % | `0 / 11 SCORE 0 · 960 TICKS LEFT Y=64 · TICK 0/960` | 0 |
| 50 % | `0 / 11 SCORE 0 · 941 TICKS LEFT Y=64 · TICK 19/960` | 19 |
| 100 % | `0 / 11 SCORE 0 · 924 TICKS LEFT Y=64 · TICK 36/960` | 36 |

The three readouts **differ**, and they differ monotonically forward — the viewer is playing, not
holding a single frame. The screenshot, taken after these, reads `TICK 37/960`, one tick further on.

*Two honest notes on those readouts, neither of which changes the verdict.*

1. **The scrubber did not seek.** The shell does expose the scrubber the tool looks for — the live
   `index.html` fetched this run contains `<div class="scrub" id="scrub">` wrapping
   `<svg class="momentum" id="momentum">`, `<span class="momentum-label">MILESTONE TIMELINE</span>`,
   `.scrub-track`, `#scrub-fill` and `#scrub-head` — so `has_scrub` was true and
   `viewer_smoke.mjs` clicked it at 50 % and 100 % of its bounding box. Had those clicks seeked, the
   readouts would be ~tick 480 and ~tick 960; they are 19 and 36, which is exactly ~700 ms of
   ordinary playback each at the design's 24 ticks/s. So the clicks landed without seeking (the
   momentum `<svg>` overlays the track on the same axis and is the likely swallower). What the three
   readouts prove here is **continuous playback motion**, not seek — which is the property item 8
   asks about ("a replay that renders one frame and never advances is a failure"). Recorded as a
   phase-30 legibility finding: the scrubber is drawn and labelled but did not respond to a synthetic
   click at 50 %/100 %.
2. **`feed_lines: 0` is a selector miss, not an empty feed.** The starter's feed panel is
   `<div id="killfeed">`; the smoke tool probes `#feed, .feed, #log, [id$="-feed"]`, and `killfeed`
   ends in `feed` but not `-feed`. The screenshot shows the feed rendering two say-bubbles, so the
   zero is the probe's, not the viewer's.

*(c) What the viewer was asked to draw* — ordered excerpts of the same replay
(`/tmp/ep2.replay`, `ereq_83858c2c-…`, daveey-1), so picture and record can be reconciled:

```bash
python3 /tmp/mc/tools/replay_summary.py /tmp/ep2.replay \
 | jq -r '.plans[]|[.turn,.tick,.source,(.actions|map(.act)|join(",")),(.say)]|@tsv'
```
early:
```
0   0    llm  move,move,mine,craft_planks,craft_sticks,place_crafting_table,craft_wooden_pickaxe   "PHASE 1: Moving to nearest tree (5 cells north), mining 2 logs, crafting full kit with table and wooden pickaxe. Setting foundation for staircase descent."
1   20   llm  move,mine,craft_planks,craft_sticks,place_crafting_table,craft_wooden_pickaxe        "Phase 1: Kit assembly. Mine nearest tree (1 cell east), craft planks x3, sticks x2, place table, craft wooden pickaxe. Ready for dig down next turn."
2   40   llm  move,mine,move,craft_planks,craft_sticks,place_crafting_table,craft_wooden_pickaxe   "Phase 1 complete: 2 trees harvested, wooden pickaxe ready. Proceeding to staircase…"
3   60   llm  move,dig_down,move,tunnel,move,mine,noop×6                                           "Phase 2 staircase: dig down to z=1, tunnel east 6 cells, mine cobblestone. Branch…"
```
middle:
```
21  420  llm  dig_down,tunnel,move,tunnel,move,tunnel,noop      "Entering iron depth z=2. Branch mining east 9, north 3, west 9, south 3, east 9…"
22  440  llm  tunnel,tunnel,move,tunnel,noop                    "Continuing main sweep pattern at z=2. East 9 cells, step north +3, then west 9 b…"
23  460  llm  tunnel,move,tunnel,move,tunnel,move,tunnel,noop×5 "Branch mining z=2: sweep north parallel +3 row, then south parallel -3 row. Syst…"
```
late:
```
45  900  llm  noop×12   "60 ticks left = 3 turns. No diamond in known_ore. Sweep pattern incomplete but t…"
46  920  llm  noop×12   "40 ticks left, 2 turns max. Stone pickaxe unlocked but no iron ore found. Diamon…"
47  940  llm  noop×12   "20 ticks remain. Mission complete at rung 3/11 (crafting_table). No diamond foun…"
```
```bash
jq -c '.milestones' /tmp/ep2.json
```
```json
[{"id":"log","points":1,"unlocked":true,"tick":42},{"id":"planks","points":2,"unlocked":true,"tick":45},{"id":"crafting_table","points":4,"unlocked":true,"tick":382},{"id":"wooden_pickaxe","points":8,"unlocked":false,"tick":-1},{"id":"cobblestone","points":16,"unlocked":false,"tick":-1},{"id":"stone_pickaxe","points":32,"unlocked":false,"tick":-1},{"id":"iron_ore","points":64,"unlocked":false,"tick":-1},{"id":"furnace","points":128,"unlocked":false,"tick":-1},{"id":"iron_ingot","points":256,"unlocked":false,"tick":-1},{"id":"iron_pickaxe","points":512,"unlocked":false,"tick":-1},{"id":"diamond","points":1024,"unlocked":false,"tick":-1}]
```
```bash
jq -c '.results|{reason,endRule,scores,milestonesReached,deepestMilestone,deepestTick,blocksMined,itemsCrafted}' /tmp/ep2.json
```
```json
{"reason":"complete","endRule":"turnCap","scores":[7578],"milestonesReached":3,"deepestMilestone":"crafting_table","deepestTick":382,"blocksMined":55,"itemsCrafted":6}
```

### Spectator judgment

**It is legible, and it shows the game.** `viewer-smoke.png` (1280×800, in
`runs/2026-08-29-minecraft/viewer-check/`) is a drawn frame at tick 37/960, not a loading screen. The
board fills the centre: a tiled grass surface at `Y=64` with a copse of tree tiles to the north, one
sand tile to the south-east, and the cog — a small red-and-brown pixel figure — standing under the
southern-most tree, mid-approach. Down the left edge of the board runs the **rung ladder**, all eleven
milestones legible in order with their point values (`LOG +1`, `PLANKS +2`, `TABLE +4`, `WOOD PICK +8`,
`COBBLE +16`, `STONE PICK +32`, `IRON ORE +64`, `FURNACE +128`, `INGOT +256`, `IRON PICK +512`,
`DIAMOND +1024`) — the tech tree that *is* this game, on screen as a checklist. Along the bottom of
the board sits the inventory strip (`LOG 0 · PLK 0 · STK 0 · COB 0 · COA 0 · IRO 0 · ING 0 · DIA 0`
plus `WOOD`/`STONE`/`IRON` tool chips). Top-right carries a **minimap** with a white viewport
rectangle over the generated level and a `VIEW … 15 CELLS` zoom control; below it an `AGENT VIEW
11×11` inset showing the cog's local observation — the surfaceViewRadius the design specifies, drawn.
Bottom-right, two amber **say-bubbles** attributed to `Alpha` quote the policy verbatim: *"PHASE 1
Moving to nearest tree (5 cells north), mining 2 logs, crafting full kit with table and wooden
pickaxe…"* and *"Phase 1 kit assembly. Mine nearest tree (1 cell east), craft planks x3, sticks x2,
place table, craft wooden pickaxe…"* — which are turns 0 and 1 of the replay excerpt above, word for
word. Picture and record agree.

The header is the scorebug the JSON reports: `0/11` chip, `none Pickaxe`, the player name **daveey-1**
in orange, `ALPHA · Y=64 · 0/11 RUNGS · 0`, a large `0 / 11`, and `SCORE 0 · 923 TICKS LEFT` over
`Y=64 · TICK 37/960`. It says who is playing, how deep they are, how far up the tech tree, and how
much clock is left. It is *early* rather than uninformative: at tick 37 daveey-1 had not yet reached
its first rung (`log` unlocked at tick 42, five ticks later), so `0/11 · SCORE 0` is the correct
reading of that moment, not an empty widget.

**It is the starter's chrome, not a lookalike rewrite** (the cogame-gridlock failure mode). The
bottom strip is paintbot's transport verbatim: restart ↺, step-back ◀, pause ‖, `+5s`, play ▶, loop
↻, fast-forward ▶▶, a `spoilers` toggle, the `37 / 959` frame counter, and the speed chips
`1× 2× 3× 4× 8× 16×` with `1×` lit. Beneath it is the **scrubber with its momentum graph** — here
labelled `MILESTONE TIMELINE`, an amber/red band running from the left edge to roughly 40 % of the
track with the playhead on it, which is where `crafting_table` at tick 382 of 960 sits. The live
shell's ids confirm the lineage rather than just the look: `#transport`, `#scrub`, `#scrub-fill`,
`#scrub-head`, `#momentum`, `#scorebug`, `#clock`, `#killfeed`, `#minimap`, `#endcard`, `#lockerroom`,
`#speedchips` — the paintbot/coworld-ctf set, remapped to mining vocabulary. The **endcard**
(`#endcard`, `#ec-headline`, `#ec-teams`, `#ec-wincond`, `#ec-replay`) is present in the shell but
not visible at tick 37, which is correct for a frame 923 ticks from the end.

Nothing is empty, frozen, or unreadable. The one thing a spectator would miss is the seek: the
timeline is drawn and labelled but did not respond to a click at 50 % or 100 %, so a viewer who wants
to jump to the crafting-table moment at tick 382 appears to be stuck watching in real time (or using
the `16×` chip). That is a legibility finding for phase 30, logged above — not a rendering failure.

**Status: TRUE** — `loaded: true` (`data_replay_loaded="true"`, first frame at 3671 ms, no failure,
green CI run 33797350340) **and** the three clock readouts differ (tick 0 → 19 → 36, corroborated by
the screenshot at tick 37).

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds #1 `round_9e5e232a-…` and #2 `round_afbe6591-…`, both `completed`, `error: null` |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey (rank 7, 2 rounds), daveey-1 (rank 6, 2 rounds); no filler row |
| 3 | Latest round's episode requests completed with replay | **TRUE** — 7/7 completed; `ereq_04411a48-…` (daveey) and `ereq_83858c2c-…` (daveey-1), both with S3 `replay_url` |
| 4 | Replay bytes valid and show the game | **TRUE** — strict JSON ok, `minecraft/v1`, `reason: complete`, 48/48 LLM turns, 0 fallbacks (milestone-count observation recorded) |
| 5 | Hosted game log clean | **TRUE** — `CLEAN` on both champion episodes, decoded before grepping; 48/48 model calls HTTP 200 |
| 6 | Public page uses the static replay path | **TRUE** — featured match in SSR `pool.replays[]` (7, round 2); `…/replays/static/<cow_id>/<manifest_sha>/index.html?v=2#replay=…`, `ready:true` |
| 7 | Certification declared the static bundle | **TRUE** — `Replay liveness: skipped (static replay bundle declared…` from the committed `release-result.json` |
| 8 | Viewer executed and judged | **TRUE** — run 33797350340, `loaded:true`, ticks 0 → 19 → 36, starter chrome intact |

Non-blocking observations handed to the coordinator: (i) the scrubber does not seek on click
(check 8, phase-30 legibility); (ii) `viewer_smoke.mjs`'s feed selector misses `#killfeed`, so
`feed_lines` under-reports for this lineage (a tooling note, not a coworld defect); (iii) the latest
round's champion episodes reached 1 and 3 of 11 milestones, under `design.md` L1462's own `>= 4` bar,
while round 1's daveey episode reached 5 (check 4).
