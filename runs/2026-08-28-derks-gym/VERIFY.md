# VERIFY — derks-gym   (2026-08-28T13:45Z)

Verdict: **3 items false — 4 (champion draft decisions are the scripted rule), 5 (player-side
`draft_fallback` grep NOT FETCHED), 8 (viewer loads; motion not demonstrated)**

| # | item | verdict |
|---|---|---|
| 1 | ≥2 completed rounds after the fillers were set | **TRUE** — rounds 2 and 3 |
| 2 | both champions ranked, fillers absent/Baseline | **TRUE** |
| 3 | latest round's episode request completed + replay + participants | **TRUE** |
| 4 | replay bytes valid and show the game | **FALSE** (4a–4f TRUE; 4g "champion decisions non-scripted" FALSE) |
| 5 | hosted game log clean | **FALSE** (four generic patterns CLEAN; `draft_fallback=scripted` NOT FETCHED — no player containers in the artifact) |
| 6 | public page uses the static replay path | **TRUE** |
| 7 | certification declared the static bundle | **TRUE** |
| 8 | executed viewer + spectator judgment | **FALSE** (`loaded: true` TRUE; three differing clock readouts NOT OBTAINABLE — no `#scrub`) |

Ids used: `$L=league_44e55a9f-aa40-4523-9ed0-7f86ccc73d08`,
`$D=div_1bc6a659-31e8-40fe-a99b-726c82426998`, `$COW=cow_81624b16-c509-470a-8fc2-69da83d64a3e`,
slug `derks-gym`, coworld version `0.1.0`, manifest_sha
`sha256:f1338b1f06b6534eaf22a49dd19dbcc336b5cd2e605d64a9c7248abbb4349c71`.

Every fetch in this file was made fresh during this phase-60 run (2026-08-28 13:21Z–13:45Z), with
the two documented exceptions: item 7 (the committed `release-result.json` from phase 40) and item
8's rendered evidence (the `viewer-check.yml` run **33176460797**, dispatched by me at 13:40:17Z).

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")   # values never printed
ELEV=(-H "X-Use-Elevated-Privileges: true")
```

**Response-shape adaptations actually observed this run** (they differ from what phase 50 saw, so
they are recorded rather than assumed):

```
$ curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" | jq -r '[type,(keys|join(","))]|@tsv'
object	entries,limit,offset,total_count
$ curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq -r 'type'
array
$ curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" | jq -r 'type'
array
$ curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" | jq -r '[type,(keys|join(","))]|@tsv'
object	entries,next_cursor
```

`/rounds` is `{entries:…}` **today** (phase 50 logged a bare array at 13:22Z), `/coworlds` is a
bare array, `/divisions/$D/leaderboard` is a bare array. Every jq below therefore uses
`if type=="array" then . else .entries end`. The flat `GET /episode-requests?round_id=` route the
prompt shows is dead (405 per `playbooks/observatory-api.md` §9); I used the nested
`GET /rounds/$R/episode-requests`, which returned 200.

---

## 1. ≥2 completed rounds after fillers were set — TRUE

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq 'if type=="array" then . else .entries end
       | map({id,round_number,status,error,created_at,completed_at,
              entrant_policy_version_ids:.round_config.entrant_policy_version_ids})'
```

```json
[
  {
    "id": "round_d6cac504-fed0-4c97-a069-209f983240b4",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T13:33:38.590131Z",
    "completed_at": "2026-08-28T13:34:32.230792Z",
    "entrant_policy_version_ids": [
      "7574f00d-b281-4f8e-b355-c5b8eb2d8fe0",
      "4309e33f-4218-4ec0-a09b-ffe607e5fc5b"
    ]
  },
  {
    "id": "round_9181ba5e-03c0-4660-becf-8755cf7e5a61",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T13:18:38.229740Z",
    "completed_at": "2026-08-28T13:19:30.990210Z",
    "entrant_policy_version_ids": [
      "7574f00d-b281-4f8e-b355-c5b8eb2d8fe0",
      "4309e33f-4218-4ec0-a09b-ffe607e5fc5b"
    ]
  },
  {
    "id": "round_c08d5ca8-c1df-4587-baba-b55dc34a369b",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-28T13:18:01.032419Z",
    "completed_at": "2026-08-28T13:18:01.843103Z",
    "entrant_policy_version_ids": [
      "7574f00d-b281-4f8e-b355-c5b8eb2d8fe0"
    ]
  }
]
```

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '[ (if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
2
```

Round 1's `error` verbatim: `Temporal RoundWorkflow failed before settling the round.` — it does
not count. It carries a **single** entrant policy version and no filler, which is exactly the
pre-filler failure `playbooks/observatory-api.md` §6 documents ("A `trigger-round` issued before
any filler exists fails instantly with `Temporal RoundWorkflow failed before settling the round`").

**"After the fillers were set" — the ordering evidence.** The run log records the filler POST at
13:21:00Z (sandbox clock) while the server stamps round 2 at 13:18:38Z; the two clocks disagree by
~3 minutes, so I do **not** rest this item on either timestamp. The direct evidence that both
counted rounds ran *with* the fillers in place is that both seated them:

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"0d434975-efba-4ffd-b071-24ab8f4fc6e0","policy_name":"derk-puffer-forge","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey"},
 {"policy_version_id":"4b650c45-b098-40ee-af64-58e2a16d98ac","policy_name":"derk-lane-brawler","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey"}]}
```

and both rounds' episode requests seat four filler versions alongside the two champions (round 2:
`["7574f00d…","4309e33f…","4b650c45…","0d434975…","0d434975…","4b650c45…"]`; round 3:
`["7574f00d…","4309e33f…","0d434975…","4b650c45…","0d434975…","4b650c45…"]` — pasted in full under
item 3), with `is_filler: true` on positions 2–5 and `names` in both replays reading
`["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"]`.

Status: **TRUE** — rounds 2 (`completed_at 13:19:30.990210Z`) and 3 (`completed_at
13:34:32.230792Z`), both round_number ≥ 2, both with the fillers seated; round 1 failed pre-filler
and is excluded.

---

## 2. Both champions ranked, fillers absent — TRUE

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey	derk-drafter-v1:v1	1000.0	2	0.0
2	daveey-1	derk-metagamer-v1:v1	1000.0	2	0.0
```

Full rows (bare array, two entries only):
```json
[
 {"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1000.0,"score_label":"MMR","score_value_type":"integer","rounds_played":2,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"derk-drafter-v1:v1","recent_rounds":null},
 {"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":1000.0,"score_label":"MMR","score_value_type":"integer","rounds_played":2,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"derk-metagamer-v1:v1","recent_rounds":null}]
```

Status: **TRUE** — `daveey` (`derk-drafter-v1:v1`) and `daveey-1` (`derk-metagamer-v1:v1`) both
present with `rounds_played: 2 ≥ 1`; `derk-puffer-forge` and `derk-lane-brawler` are **absent**
from the leaderboard entirely (the permitted "fillers absent" branch). `episode_wins: 0.0` with
`score` at the `initial_rating` 1000.0 for both is the elo ranking's own bookkeeping for a mirror
in which both champions sat on the same (winning) team — see item 3's `participant_scores`.

---

## 3. Latest completed round's episode request — TRUE

```bash
R=round_d6cac504-fed0-4c97-a069-209f983240b4        # max round_number among completed (round 3)
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}"
```
```json
{"entries":[{"id":"ereq_6eecaf06-8cf5-43c1-85a5-0d5163334152","status":"completed",
 "coworld_id":"cow_81624b16-c509-470a-8fc2-69da83d64a3e",
 "round_id":"round_d6cac504-fed0-4c97-a069-209f983240b4",
 "replay_url":"https://softmax-public.s3.amazonaws.com/replays/02c16518-1131-4968-ba7e-05031eac8934.replay",
 "policy_version_ids":["7574f00d-b281-4f8e-b355-c5b8eb2d8fe0","4309e33f-4218-4ec0-a09b-ffe607e5fc5b",
 "0d434975-efba-4ffd-b071-24ab8f4fc6e0","4b650c45-b098-40ee-af64-58e2a16d98ac",
 "0d434975-efba-4ffd-b071-24ab8f4fc6e0","4b650c45-b098-40ee-af64-58e2a16d98ac"],
 "created_at":"2026-08-28T13:33:38.900600Z"}],"next_cursor":null}
```

```bash
EREQ=ereq_6eecaf06-8cf5-43c1-85a5-0d5163334152
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants:[.participants[]|{position,policy_name,player_name,is_filler}], participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/02c16518-1131-4968-ba7e-05031eac8934.replay",
  "participants": [
    {"position": 0, "policy_name": "derk-drafter-v1",   "player_name": "daveey",   "is_filler": false},
    {"position": 1, "policy_name": "derk-metagamer-v1", "player_name": "daveey-1", "is_filler": false},
    {"position": 2, "policy_name": "derk-puffer-forge", "player_name": "daveey",   "is_filler": true},
    {"position": 3, "policy_name": "derk-lane-brawler", "player_name": "daveey",   "is_filler": true},
    {"position": 4, "policy_name": "derk-puffer-forge", "player_name": "daveey",   "is_filler": true},
    {"position": 5, "policy_name": "derk-lane-brawler", "player_name": "daveey",   "is_filler": true}
  ],
  "participant_scores": [
    {"position": 0, "score": 1.0}, {"position": 1, "score": 1.0}, {"position": 2, "score": 1.0},
    {"position": 3, "score": 0.0}, {"position": 4, "score": 0.0}, {"position": 5, "score": 0.0}
  ]
}
```

Round 2's episode request, fetched the same way, for the record:
`ereq_4d519cdf-8f97-412d-add5-38ad2b5b6d6a`, `status: "completed"`, `replay_url:
https://softmax-public.s3.amazonaws.com/replays/9b3eb476-02db-4879-a8f5-926ec1591967.replay`,
participants positions 0/1 = `derk-drafter-v1`/`daveey` and `derk-metagamer-v1`/`daveey-1`
(`is_filler: false`), positions 2–5 fillers, `participant_scores` `[1,1,1,0,0,0]`.

Status: **TRUE** — `status == "completed"`, non-null `replay_url`, `participants` naming `daveey`
and `daveey-1` at positions 0 and 1. Note the API labels the four filler seats with their real
policy names plus `is_filler: true` rather than `Baseline (N)`; the `Baseline (N)` renaming shows
up on the **game** side, in `results.names` and the replay header (item 4), which is where the
prompt's expectation actually lands.

---

## 4. Replay bytes are valid and show the game — FALSE (4g only)

The prompt's jq lines assume a JSON replay. **This coworld's replay is binary** — format v2, magic
`DERK`, `version u8 = 2`, `u32le header_len`, header JSON (UTF-8), then `tick_count × 60` bytes of
post-clamp actions (`design.md` §Replay format v2; ground truth
`server/cogame_derks_gym/replay.py`, which declares `MAGIC = b"DERK"` and `FORMAT_VERSION = 2`,
fetched from the repo at main this run). So the strict-parse step is done in python3 with
`errors="strict"`, not with `jq -e .`.

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/02c16518-1131-4968-ba7e-05031eac8934.replay" \
     -o /tmp/ep3.replay -w "HTTP %{http_code} size=%{size_download}\n"
HTTP 200 size=341567
```

```python
b = open('/tmp/ep3.replay','rb').read()
# magic / version / header_len / strict-UTF-8 JSON header / body length
```
```
total bytes: 341567 first8: 4445524b02524c00 magic: b'DERK' version: 2
header_len: 19538
strict UTF-8 JSON parse: ok            # json.loads(hdr.decode('utf-8', errors='strict'))
tick_count: 5367 body: 322020 ==tick*60: True
end_reason: ancient winner: 0 final_tick: 5367 ancient_healths: [4500.0, 0.0]
names: ['daveey', 'daveey-1', 'Baseline', 'Baseline (2)', 'Baseline (3)', 'Baseline (4)']
scores: [1.0, 1.0, 1.0, 0.0, 0.0, 0.0]
draft_fallbacks: [False, False, False, False, False, False]
noop_ticks: [0, 0, 0, 0, 0, 0] dead_seats: [False, False, False, False, False, False]
loadout_digest: 1755002934 final_state_digest: 4052752543 format_version: 2 catalog_version: v1
events: 120 draft records: 10
```

Sub-item verdicts:

| | requirement | verdict |
|---|---|---|
| 4a | valid under a strict UTF-8 parser | TRUE — `json.loads(hdr.decode('utf-8', errors='strict'))` succeeded on all 19538 header bytes |
| 4b | format matches the manifest / repo declaration | TRUE — magic `DERK` (`4445524b`), version byte `02`, `format_version: 2`, `catalog_version: "v1"`; body `322020 == 5367 × 60` |
| 4c | `results.end_reason` acceptable | TRUE — `"ancient"`: an Ancient actually fell (`ancient_healths: [4500.0, 0.0]`). Not even a deadline outcome; no documented exception needed. Inside the manifest's closed enum `["ancient","tick_cap","wall_clock","sim_fault"]`; **not** `sim_fault` |
| 4d | `draft` has 10 records; the 6 seat records name both champions | TRUE — 10 records, `source:"seat"` for pids 0,1,2,5,6,7 and `source:"house"` for 3,4,8,9; `player_name` `daveey` (pid 0) and `daveey-1` (pid 1) |
| 4e | `events` non-empty; `loadout_digest` present | TRUE — 120 events; `loadout_digest: 1755002934` |
| 4f | non-trivial content: a drafted (non-neutral) loadout by ≥1 champion seat | TRUE — both champion seats drafted non-neutral loadouts (quoted below) |
| **4g** | **champion decisions non-scripted, not all fallbacks** | **FALSE** — both champions' draft records are byte-identical to `puffer-forge`'s scripted role table, at `decision_ms: 1`, with an empty `note` |

**4d / 4f — the two champion seat records verbatim (round 3):**

```json
{"pid": 0, "seat": 0, "alias": "Cog-Alpha", "player_name": "daveey", "team": "radiant", "role": "support",
 "picks": {"arm": "arm_blaster", "tail": "tail_plate", "misc": "misc_battery"}, "note": "",
 "source": "seat", "fallback": false, "fallback_cause": "none", "decision_ms": 1,
 "applied": {"base_health": 700.0, "base_mana": 400.0, "base_damage": 65.0, "basic_attack_cd": 10,
             "move_speed": 1.0, "hp_gain_per_level": 100, "mana_gain_per_level": 80,
             "damage_gain_per_level": 10}}
{"pid": 1, "seat": 1, "alias": "Cog-Bravo", "player_name": "daveey-1", "team": "radiant", "role": "assassin",
 "picks": {"arm": "arm_needler", "tail": "tail_rotor", "misc": "misc_focus"}, "note": "",
 "source": "seat", "fallback": false, "fallback_cause": "none", "decision_ms": 1,
 "applied": {"base_health": 300.0, "base_mana": 300.0, "base_damage": 50.0, "basic_attack_cd": 5,
             "move_speed": 1.149999976158142, "hp_gain_per_level": 75, "mana_gain_per_level": 65,
             "damage_gain_per_level": 10}}
```

Both are non-neutral (Blaster + Iron Plate + Mana Battery → `base_damage 50→65`, `base_health
500→700`, `base_mana 250→400`, `basic_attack_cd 8→10`; Needler + Rotor Tail + Focus Chip →
`basic_attack_cd 8→5`, `move_speed 1.0→1.15`, `base_health 400→300`), so item 4f's game-specific
"non-trivial content" evidence is satisfied and the draft is physically real in the sim.

**4g — why this is FALSE.** `decision_ms` is measured server-side as the seat's own answer time
(`server/cogame_derks_gym/draft.py::_one_seat`: `started = time.monotonic()` before
`asyncio.wait_for(source.get_draft(...))`, `int((time.monotonic()-started)*1000)` after). Both
champion seats answered in **1 ms**. No HTTPS round trip to `api.anthropic.com` — the design's
20 s-timeout Messages API call — can complete in 1 ms. And the picks are not merely fast, they are
**exactly** `puffer-forge`'s documented draft table for the seat's role (`design.md` §Scripted
baselines: support → `arm_blaster/tail_plate/misc_battery`; assassin →
`arm_needler/tail_rotor/misc_focus`), with `note: ""` — while `derk-metagamer-v1`'s own system
prompt *requires* a note ("Your note field must name, in a few words, the enemy build you are
countering").

The same fingerprint appears in **both** counted rounds, i.e. two independent episodes:

```
round 2 draft records — (pid, player_name, decision_ms, fallback, note):
[(0,'daveey',1,False,''), (1,'daveey-1',1,False,''), (2,'Baseline',1,False,''),
 (3,None,0,False,''), (4,None,0,False,''), (5,'Baseline (2)',1,False,'brawl build'),
 (6,'Baseline (3)',1,False,''), (7,'Baseline (4)',1,False,'brawl build'),
 (8,None,0,False,''), (9,None,0,False,'')]
round 2 picks: pid0 support arm_blaster/tail_plate/misc_battery ; pid1 assassin arm_needler/tail_rotor/misc_focus
round 3 picks: pid0 support arm_blaster/tail_plate/misc_battery ; pid1 assassin arm_needler/tail_rotor/misc_focus
```

The control is in round 3's own record set: seat 2 is a **declared** `derk-puffer-forge` filler
(position 2 of `policy_version_ids`, `0d434975…`) in the burst role and its record reads
`arm_blaster / tail_stinger / misc_battery` — puffer-forge's burst row. The champions' records are
their own roles' rows of the same table. Under the brief's split of this criterion, the
**server-side** conjunct is TRUE (`fallback: false`, `fallback_cause: "none"`,
`results.draft_fallbacks == [false × 6]` — the server did not substitute anything, because the
players submitted legal picks) and the **player-side** conjunct is what fails.

Two things this is **not**: it is not a broken episode (the champions' per-tick micro is fully
live), and it is not a server-side degrade. The per-tick action body proves the micro layer:

```
pid0 daveey micro:   5367 ticks, NOOP rows=0 (0.00%), distinct rows=412, ticks 0-4=[[0,4,2,1,1,0],[0,6,0,0,1,1],[3,6,1,1,1,1],[0,6,0,0,1,1],[3,6,0,0,0,1]]
pid1 daveey-1 micro: 5367 ticks, NOOP rows=0 (0.00%), distinct rows=522, ticks 0-4=[[0,5,2,1,1,1],[0,6,0,0,1,1],[0,6,1,1,1,1],[0,6,0,0,1,1],[0,6,0,0,0,1]]
```
(NOOP is `[3,3,0,0,0,0]`; round 2 was the same — pid0 1 NOOP row in 4341 ticks, pid1 zero.)

**Ordered event excerpts — the champion seats doing the thing the game is about** (round 3, the
replay the featured match points at):

```
events: 120  by kind: {'draft': 1, 'level_spike': 70, 'first_blood': 1, 'kill': 40, 'tower': 7, 'end': 1}
--- EARLY (first 8) ---
{"tick": 0, "kind": "draft", "pids": [0, 1, 2, 5, 6, 7]}
{"tick": 0, "kind": "level_spike", "pid": 0, "level": 1}
{"tick": 0, "kind": "level_spike", "pid": 1, "level": 1}
{"tick": 0, "kind": "level_spike", "pid": 2, "level": 1}
{"tick": 0, "kind": "level_spike", "pid": 3, "level": 1}
{"tick": 0, "kind": "level_spike", "pid": 4, "level": 1}
{"tick": 0, "kind": "level_spike", "pid": 5, "level": 1}
{"tick": 0, "kind": "level_spike", "pid": 6, "level": 1}
--- MIDDLE (idx 56-63) ---
{"tick": 1509, "kind": "level_spike", "pid": 2, "level": 6}
{"tick": 1510, "kind": "kill", "pid": 6, "victim_pid": 3}
{"tick": 1510, "kind": "level_spike", "pid": 6, "level": 4}
{"tick": 1619, "kind": "level_spike", "pid": 0, "level": 3}
{"tick": 1621, "kind": "kill", "pid": 6, "victim_pid": 2}
{"tick": 1699, "kind": "level_spike", "pid": 7, "level": 6}
{"tick": 1788, "kind": "kill", "pid": 6, "victim_pid": 4}
{"tick": 1788, "kind": "level_spike", "pid": 6, "level": 5}
--- LATE (last 8) ---
{"tick": 4896, "kind": "tower", "pid": 7, "team": 1}
{"tick": 5055, "kind": "level_spike", "pid": 4, "level": 6}
{"tick": 5077, "kind": "level_spike", "pid": 6, "level": 12}
{"tick": 5080, "kind": "kill", "pid": 6, "victim_pid": 4}
{"tick": 5280, "kind": "level_spike", "pid": 3, "level": 8}
{"tick": 5310, "kind": "level_spike", "pid": 5, "level": 9}
{"tick": 5366, "kind": "tower", "pid": 4, "team": 0}
{"tick": 5367, "kind": "end", "reason": "ancient"}

pid0 seat0 daveey/derk-drafter-v1:      3 events; kills at []; towers at []; level_spikes 3; died at [1963]
pid1 seat1 daveey-1/derk-metagamer-v1: 20 events; kills at [523, 693, 1032, 1485, 3577, 3688, 3889];
                                       towers at [2952, 3890]; level_spikes 11;
                                       died at [2643, 2952, 3090, 3367, 3984, 4062]
```

```
agent_stats (10 heroes, round 3):
  pid 0: {"level": 3, "kills": 0, "deaths": 4, "towers_killed": 0, "creeps_killed": 0, "neutrals_killed": 14, "xp": 490, "damage_dealt": 12368, "damage_received": 5978, "healing_dealt": 1582, "healing_received": 1526}
  pid 1: {"level": 12, "kills": 7, "deaths": 16, "towers_killed": 2, "creeps_killed": 53, "neutrals_killed": 48, "xp": 7313, "damage_dealt": 59805, "damage_received": 16759, "healing_dealt": 0, "healing_received": 0}
  pid 2: {"level": 7, "kills": 5, "deaths": 7, "towers_killed": 2, "creeps_killed": 24, "neutrals_killed": 14, "xp": 3096, "damage_dealt": 23814, "damage_received": 7097, "healing_dealt": 0, "healing_received": 0}
  pid 6: {"level": 12, "kills": 11, "deaths": 10, "towers_killed": 0, "creeps_killed": 41, "neutrals_killed": 0, "xp": 7454, "damage_dealt": 21488, "damage_received": 7483, "healing_dealt": 0, "healing_received": 0}
  pid 7: {"level": 11, "kills": 9, "deaths": 8, "towers_killed": 1, "creeps_killed": 61, "neutrals_killed": 0, "xp": 6312, "damage_dealt": 41250, "damage_received": 17956, "healing_dealt": 0, "healing_received": 909}
  (pids 3,4,5,8,9 elided — full array in the fetched bytes; every hero has nonzero damage_dealt)
```

Round 2's replay (`9b3eb476-…`, 279839 bytes) parsed identically: magic `DERK`, version 2,
`header_len 19370`, strict parse ok, `tick_count 4341`, body `260460 == 4341 × 60`,
`end_reason "ancient"`, `ancient_healths [4500.0, 0.0]`, 116 events, `loadout_digest 3613223773`,
champion seats with 1 kill / 3 kills + 1 tower respectively.

Status: **FALSE on 4g** — 4a–4f are TRUE and the episode is a real, complete, Ancient-decided MOBA
match, but the champions' *decisions* — the one decision this coworld gives an LLM — are the
scripted `puffer-forge` rule, not an LLM draft. Evidence: `decision_ms: 1`, `note: ""`, picks
identical to the scripted role table, in two consecutive episodes.

---

## 5. Hosted game log — FALSE (CLEAN on the four patterns; `draft_fallback` NOT FETCHED)

```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs_r3.raw
# HTTP 200 size=2045   — then ast.literal_eval each b'…' repr (playbook §10) before grepping
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs_r3.txt || echo CLEAN
CLEAN
grep -nE 'draft_fallback|ANTHROPIC' /tmp/logs_r3.txt || echo "NOT PRESENT"
NOT PRESENT
```

The decoded artifact in full (round 3 — 2045 raw bytes, four containers):

```
containers: ['coworld-init-config', 'bedrock-sidecar', 'game', 'worker']

===== container: coworld-init-config =====
(empty)
===== container: bedrock-sidecar =====
2026-08-28 13:18:46,137 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1",…}
[2026-08-28 13:18:46 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)
===== container: game =====
cogame-derks-gym serving on 0.0.0.0:8080 (6 seats, one hero each; house heroes (3, 4, 8, 9); draft_enabled=True)
seat 3 (Baseline (2)) connected at tick 0
seat 4 (Baseline (3)) connected at tick 0
seat 2 (Baseline) connected at tick 0
seat 0 (daveey) connected at tick 0
seat 1 (daveey-1) connected at tick 0
seat 5 (Baseline (4)) connected at tick 0
draft Cog-Alpha (support): arm_blaster / tail_plate / misc_battery [none, 1ms]
draft Cog-Bravo (assassin): arm_needler / tail_rotor / misc_focus [none, 1ms]
draft Cog-Charlie (burst): arm_blaster / tail_stinger / misc_battery [none, 1ms]
draft Cog-Delta (support): arm_cleaver / tail_plate / misc_focus [none, 1ms]
draft Cog-Echo (assassin): arm_needler / tail_rotor / misc_focus [none, 1ms]
draft Cog-Foxtrot (burst): arm_needler / tail_rotor / misc_regen [none, 1ms]
house heroes (3, 4, 8, 9) driven by the vendored pretrained network (neutral loadout)
seat 0 (daveey) disconnected at tick 5366
… (all six seats) …
episode over: winner=0 end_reason=ancient tick=5367
===== container: worker =====
(empty)
```

**The `draft_fallback=scripted` line is NOT FETCHED**, and it is not fetchable: the logs artifact
contains only the **game pod's** containers. The player pods' stdout/stderr — where
`players/derk_player.py` prints `draft_fallback=scripted reason=<no_key|no_time|timeout|parse|
illegal|transport>` (line 313) and `ANTHROPIC_API_KEY is not set: no LLM call at all` (line 319)
— is not exposed by any route I could find. Three different approaches, all this run:

| attempt | request | result |
|---|---|---|
| 1 | `GET /episode-requests/ereq_4d51…/artifacts/logs` (round 2) | HTTP 200, 2043 bytes, containers `coworld-init-config, bedrock-sidecar, game, worker` — no player container |
| 2 | `GET …/artifacts` · `…/artifacts/player-logs` · `…/artifacts/logs?container=player` · `?role=player` · `?slot=0` · `?all=true` · `GET /episodes/43b05140-…/artifacts/logs` · `GET /episode-requests/…/logs` | `{"detail":"Not Found"}` (404) · `{"detail":"Unknown artifact type: player-logs"}` (400) · the five query-string variants each returned the **same** game-pod-only body (filters ignored) · 404 · 404 |
| 3 | `GET /episode-requests/ereq_6eecaf06…/artifacts/logs` (round 3 — a different round) | HTTP 200, 2045 bytes, same four containers, no player container |

Status: **FALSE.** The prompt's own grep is **CLEAN** — none of `falling back`, `LLM provider is
unavailable`, `cut off at max_tokens`, `rejected` appears in either round's decoded log, and there
is no Bedrock-capacity symptom to wait out. But the brief's additional, game-specific grep
(`draft_fallback=scripted`) could not be run at all, so I cannot mark this item true from the
absence of a line in a log that does not contain player output. Per the item-4g evidence the
player-side fallback did occur; the exact `reason=` token (`no_key` vs `transport` vs `timeout`)
is **unproven**. The strongest available inference — stated as an inference, not as evidence — is
`no_key`: `players/derk_player.py:450` reads only `os.environ["ANTHROPIC_API_KEY"]`, while
`tools/ci/policies.json` and the manifest's `drafter` entry set only
`ANTHROPIC_API_KEY_URI=secret://coworld/derks-gym/anthropic_api_key`, and `no_key` is the one
fallback branch that returns without any network I/O — i.e. in 1 ms.

---

## 6. The public page uses the static replay path — TRUE

Source used: **the replay-session endpoint** (`playbooks/observatory-api.md` §Featured match /
replay route), after the raw-HTML grep found nothing and `/coworlds`' `featured_match` came back
null — both of which the playbook records as expected platform behaviour, not evidence.

```bash
curl -sS "https://softmax.com/derks-gym" | grep -o '<iframe[^>]*src="[^"]*"'
# (no output; HTTP 200, 737727 bytes) -> page is client-rendered, per playbook. NOT a false negative.

curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -c 'if type=="array" then . else .entries end | .[]|select(.name=="derks-gym")|{id,name,version,canonical,replay_viewer,featured_match}'
{"id":"cow_81624b16-c509-470a-8fc2-69da83d64a3e","name":"derks-gym","version":"0.1.0","canonical":true,"replay_viewer":null,"featured_match":null}
```

**Featured match — server-rendered into the page's SSR payload at `state.playlist[0]`** (fetched
13:39Z, unescaped):

```json
"playlist":[{"episodeId":"579839db-2cb1-491e-a75c-eea65b9ad058",
 "coworldId":"cow_81624b16-c509-470a-8fc2-69da83d64a3e","coworldName":"derks-gym",
 "coworldVersion":"0.1.0",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/02c16518-1131-4968-ba7e-05031eac8934.replay",
 "finishedAt":"2026-08-28T13:34:22.721926Z","roundNumber":3,"episodeNumber":1,
 "code":"derks-gym.r3.e1",
 "matchup":{"divisionId":"div_1bc6a659-31e8-40fe-a99b-726c82426998","divisionName":"Competition",
  "first":{"rank":1,"player_name":"daveey","policy_label":"derk-drafter-v1:v1","rounds_played":2,…},
  "second":{"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",…}}}]
```

A featured match is present and it is **round 3's episode** — the same replay as item 3/4. (At
13:25Z the same field held round 2's `9b3eb476-…`; it rolled forward when round 3 landed, which is
why item 8 was re-dispatched against the round-3 src.)

**The iframe `src` the page's JS builds:**

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
 -d '{"coworld_id":"cow_81624b16-c509-470a-8fc2-69da83d64a3e","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/02c16518-1131-4968-ba7e-05031eac8934.replay"}'
```
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_81624b16-c509-470a-8fc2-69da83d64a3e/sha256%3Af1338b1f06b6534eaf22a49dd19dbcc336b5cd2e605d64a9c7248abbb4349c71/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F02c16518-1131-4968-ba7e-05031eac8934.replay","ready":true}
```

Status: **TRUE** — `ready: true`, the path is
`/v2/coworlds/replays/static/<cow_id>/<manifest_sha, URL-encoded>/index.html`, the `<sha>` is the
coworld's `manifest_sha` from STATE
(`sha256:f1338b1f06b6534eaf22a49dd19dbcc336b5cd2e605d64a9c7248abbb4349c71`), and the replay rides
as the `#replay=` fragment — the 2026-08-28 form the playbook documents. **No `/client/replay` pod
URL anywhere.** A featured match is present.

---

## 7. Certification declared the static bundle — TRUE

Source: **the committed `runs/2026-08-28-derks-gym/release-result.json`** (the copy phase 40
downloaded from release run 33173805205 and committed) — not `/tmp`, and no re-download was needed.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-28-derks-gym/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Contains the required string `Replay liveness: skipped (static replay bundle declared`. For
context, from the same file: `.certify.ok == true`, `.canonical`, `.version == "0.1.0"`,
`.secret_put == true`, and the transcript tail shows all 10 certification steps `[pass]`, including
`replay-loadable: the replay artifact has a declared viewer path` and `players-run: every declared
player actually started on the smoke episode`.

Status: **TRUE.**

---

## 8. Spectator judgment — the viewer was EXECUTED — FALSE (loads; motion not demonstrated)

*(a) Dispatch.* Dispatched at **2026-08-28T13:40:17Z** against the item-6 `src` verbatim (fragment
and all):

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_81624b16-c509-470a-8fc2-69da83d64a3e/sha256%3Af1338b1f06b6534eaf22a49dd19dbcc336b5cd2e605d64a9c7248abbb4349c71/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F02c16518-1131-4968-ba7e-05031eac8934.replay'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -c 'sort_by(.createdAt)|reverse|.[0:3]'
[{"createdAt":"2026-08-28T13:40:19Z","databaseId":33176460797,"status":"in_progress"},
 {"createdAt":"2026-08-28T13:25:59Z","databaseId":33175355596,"status":"completed"},
 {"createdAt":"2026-08-28T09:25:16Z","databaseId":33159290682,"status":"completed"}]
```

Run **33176460797** was created 2 s after my dispatch (found by sorting on `createdAt`, not by
`-L 1`). `gh run watch 33176460797 --exit-status` → exit 0;
`{"conclusion":"success","status":"completed","createdAt":"2026-08-28T13:40:19Z","updatedAt":"2026-08-28T13:41:15Z"}`.
Artifact downloaded to and committed at `runs/2026-08-28-derks-gym/viewer-check/`
(`viewer-smoke.json`, `viewer-smoke.png`, `smoke-stdout.txt`, `smoke-stderr.txt`; stderr is
0 bytes). Run 33175355596 (13:25:59Z) was an earlier dispatch of mine against round 2's replay,
superseded when the featured match rolled to round 3; its readouts were identical
(`{"loaded":true,"ms":2956,"clock":null,"scorebug":null,"feed_lines":0}`) and it is not the
committed evidence.

*(b) The readouts, verbatim.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-28-derks-gym/viewer-check/viewer-smoke.json
{"loaded":true,"ms":1774,"clock":null,"scorebug":null,"feed_lines":0}

jq -c '.signals' runs/2026-08-28-derks-gym/viewer-check/viewer-smoke.json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}

jq -r '.failure // "no failure"' runs/2026-08-28-derks-gym/viewer-check/viewer-smoke.json
no failure

jq -c '{status,loading_text,soak,canvas_text}' …/viewer-smoke.json
{"status":"","loading_text":null,"soak":null,
 "canvas_text":{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"samples":[]}}

cat runs/2026-08-28-derks-gym/viewer-check/smoke-stdout.txt
{"loaded":true,"ms":1774,"clock":null,"scorebug":null,"feed_lines":0}
canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
artifacts: /home/runner/work/coworld-builder/coworld-builder/viewer-smoke.png …/viewer-smoke.json
```

**The three clock readouts (0 % / 50 % / 100 %):**

```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-28-derks-gym/viewer-check/viewer-smoke.json
# (no output — the array is empty)
jq -c '.scrub' …/viewer-smoke.json
[]
```

| at | clock |
|---|---|
| 0 % | **NOT FETCHED** — `"scrub": []` |
| 50 % | **NOT FETCHED** — `"scrub": []` |
| 100 % | **NOT FETCHED** — `"scrub": []` |

`scrub` is empty because `viewer_smoke.mjs` only scrubs when its readout reports
`has_scrub: !!document.querySelector("#scrub")` (line 435, gated at line 570), and this shell has
no element with id `scrub`. Its summary step renders that as **"(no #scrub in this shell)"**. The
same selector mismatch explains `clock: null`, `scorebug: null` and `feed_lines: 0`: the script
probes `#clock`, `#tick-clock, #tick, .tick-clock`, `#scorebug` and `#feed, .feed, #log`, while
this viewer's readouts are `derk-`-prefixed. Fetched proof of the shell's actual ids:

```bash
curl -sS "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/$COW/sha256%3Af1338b1f…/index.html" "${AUTH[@]}"
# HTTP 200 size=12238
grep -oE 'id="[a-z-]+"' shell.html | sort -u
id="canvas" id="controls" id="derk" id="derk-bar-dire" id="derk-bar-radiant" id="derk-beats"
id="derk-cameras" id="derk-clock" id="derk-draft" id="derk-draft-close" id="derk-draft-cols"
id="derk-draft-count" id="derk-draft-inner" id="derk-endcard" id="derk-endcard-inner"
id="derk-feed" id="derk-hp-dire" id="derk-hp-radiant" id="derk-kills-dire" id="derk-kills-radiant"
id="derk-minimap" id="derk-roster" id="derk-scorebug" id="derk-towers-dire" id="derk-towers-radiant"
id="derk-viewpanel" id="dire-names" id="endcard" id="playpause" id="radiant-names" id="seek"
id="speed" id="stage" id="status" id="teams" id="tickinfo" id="warn"
```

So the scrubber exists — it is the starter's `#seek` range input — and the clock is `#derk-clock`;
the instrument simply does not look for either. `viewer-check.yml` exposes only `url` and
`timeout` inputs (no `--soak`), and I may not edit it, so no dispatch available to me can produce
the three readouts. **This is an instrument limitation, not an observation that the viewer is
frozen** — and it is a legibility finding for the coordinator: this coworld's viewer is invisible
to the standard smoke selectors (`#scrub`, `#clock`, `#scorebug`, `#feed`), and either the shell
should carry those ids as aliases or `viewer_smoke.mjs` should learn `#seek`/`#derk-*`.

**Item 8 verdict: FALSE.** Condition 1 (`loaded: true`, via `data-replay-loaded="true"`, in
1774 ms, `data_replay_error: null`, `failure: null`) is **TRUE and pasted above**. Condition 2
(three differing clock readouts) is **not demonstrated**, and I will not mark it true from the
screenshot alone. Per `prompts/60-verify.md` check 8 §2 the absent scrubber is judged from the
screenshot plus the replay instead — that judgment is below, and it is favourable but single-frame.

*(c) Spectator judgment.* Evidence: `runs/2026-08-28-derks-gym/viewer-check/viewer-smoke.png`
(1280×800, 83046 bytes, taken by CI a few hundred ms after the load signal — `viewer_smoke.mjs`
screenshots at line 608, immediately after the text-bounds read, with no soak and no scrub in
between), reconciled against the round-3 replay header's events quoted in item 4.

The picture is **not empty and not a "Loading replay…" shell**. It is legible and it plainly shows
this game. Top band: the `#derk-scorebug` (`RADIANT  4500 ▬▬▬▬  ·  0 towers  0 kills` and the dire
mirror) and `#derk-clock` reading `tick 1 / 5367 · 0:00`, with the header `cogame-derks-gym replay
viewer` — all three visible but dimmed because the draft-reveal overlay is on top of them. Middle:
`#derk-draft`, the draft-reveal screen, captioned **`Draft reveal (closes in 6s)`** in two columns
`Radiant` / `Dire`, one card per drafted cog: `Cog-Alpha  daveey  support` / `Blaster · Iron Plate
· Mana Battery` / `base_damage +15  base_health +200  base_mana +150  basic_attack_cd +2
mana_gain_per_level +30` / `hp 700 · mana 400 · dmg 65 · cd 10 · spd 1 · /lvl 100/80/10`, and
opposite it `Cog-Delta  Baseline (2)  support` / `Cleaver · Iron Plate · Focus Chip` / `… hp 700 ·
mana 250 · dmg 95 · cd 13 · spd 1 · /lvl 75/50/10` / *`brawl build`* in italics. `Cog-Bravo
daveey-1 assassin` and `Cog-Echo Baseline (3) assassin` are visible below, clipped by the
screenshot's fold. Every card carries three item glyph badges from `derk_items.svg`, the alias,
**and the real player name beside it** — the two-name-space rule rendered exactly as designed.
Behind the overlay: the raylib canvas, drawing the upstream 128×128 Dota-shaped map through its
41×23 camera — five heroes as distinct sprites with cyan/green/red team-tinted health-and-mana bars
and `Level: 1` labels above each, magenta tower-vision outlines, the lane geometry, and the
starter's in-canvas HUD (`Experience: 0`, `Mana: 300/300`, `Health: 350/350`, `Q: · W: · E:`
cooldown boxes, `Stun: 0  Move: 0`) plus the raylib FPS counter in the canvas's top-left, which in
the committed png reads **`80 FPS`** (dimmed under the overlay; enlarged crop of the same png to
read it). Under the canvas, the `#derk-roster` delta strip is drawn as green `+1 +12 +4 +7 +3 +5 …`
badges.

Reconciliation with the record: the frame is `tick 1 / 5367`, and 5367 is exactly the replay's
`tick_count`, so the viewer parsed the same header this file parsed. `Level: 1` on every hero and
`0 towers 0 kills` on both sides match the events at tick 0 (`draft`, then ten `level_spike … level
1`); the first kill in the record is at tick 523 and the first tower at 2952, both far ahead of the
drawn frame, so the empty scorebug is correct rather than broken. The overlay's own countdown
(`closes in 6s`) is the design's "auto-shown for the first 6 s of playback" just started. What this
frame **cannot** show is advancement: one screenshot at tick 1 is consistent both with normal
playback (5 ticks/s → tick 1 at ~0.2 s) and with a viewer that draws one frame and stops. I have
no evidence of the latter (`failure: null`, no page errors, no `data-replay-error`, and the
in-canvas FPS counter reading `80 FPS` — the render loop is alive) and none of the former either.
**Motion: unproven.**

**Chrome provenance — the starter's page, not a rewrite.** Every id in
`/workspace/starters/cogame-moba/viewer/index.html` survives in the served shell:

```bash
comm -23 <(grep -oE 'id="[a-z-]+"' /workspace/starters/cogame-moba/viewer/index.html | sort -u) \
         <(grep -oE 'id="[a-z-]+"' shell.html | sort -u)
# (no output — zero starter ids missing)
```

`#stage`, `#canvas`, `#status`, `#controls`/`#playpause`/`#speed`/`#seek`/`#tickinfo`, `#endcard`,
`#warn`, `#teams`, `#radiant-names`, `#dire-names` are all present, and the additions are all
`derk-`-prefixed. The screenshot agrees: the same transport strip, the same canvas + status
overlay, the same two-team name panel, with the `#derk` scorebug / roster / feed / draft-reveal
block appended. This is cogame-moba's viewer with a game block added — **not** the cogame-gridlock
failure of a rewrite sharing only the ids.

---

## Observations for the coordinator (not checklist items)

1. **The champions never call the LLM (the blocking finding).** Item 4g. Both champion policies'
   env is `PLAYER_PROMPT=…` + `ANTHROPIC_API_KEY_URI=secret://coworld/derks-gym/anthropic_api_key`
   (`tools/ci/policies.json`, fetched from main this run; the manifest's `drafter` player entry
   matches), while `players/derk_player.py:450` reads `os.environ.get("ANTHROPIC_API_KEY", "")`
   only. If the platform does not materialise `<VAR>_URI` into `<VAR>` inside the player pod, the
   `no_key` branch (line 318-321) fires with no network I/O — which is what a 1 ms `decision_ms`
   looks like. Unverified because player logs are unreachable; the fix and the check both belong
   to the builder, not to me.
2. **Player-pod logs are unobservable.** The `artifacts/logs` route returns the game pod only
   (`coworld-init-config, bedrock-sidecar, game, worker`). Any check that depends on a player-side
   log line — including this coworld's documented `draft_fallback=scripted reason=…` contract in
   `docs/DRAFT.md` — cannot be verified through the Observatory API as it stands. Consider having
   the **game** log the per-seat cause it already receives, or a `results` field.
3. **No `ancient` event is emitted even though an Ancient fell.** Both replays end
   `{"kind":"end","reason":"ancient"}` with `ancient_healths [4500.0, 0.0]`, and the tick before
   the end is a `tower` event by a house hero (round 3: `{"tick":5366,"kind":"tower","pid":4,
   "team":0}`); `design.md` §Event vocabulary specifies a distinct `ancient` event. The viewer's
   `.beat-ancient` scrubber beat and feed line will therefore never appear. Cosmetic, but it is a
   design-vs-implementation gap.
4. **The smoke instrument is blind to this viewer's readouts** (item 8): `#scrub`/`#clock`/
   `#scorebug`/`#feed` vs this shell's `#seek`/`#derk-clock`/`#derk-scorebug`/`#derk-feed`. Until
   one side learns the other's names, check 8's motion condition is unprovable for this coworld.
5. **`/rounds` shape changed mid-run**: a bare array at 13:22Z (phase 50), `{entries,limit,offset,
   total_count}` at 13:42Z. The dual-shape jq is mandatory, not optional.
