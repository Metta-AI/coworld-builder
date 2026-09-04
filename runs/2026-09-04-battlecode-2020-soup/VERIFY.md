# VERIFY — battlecode-2020-soup   (2026-09-04T08:38Z)

Verdict: **1 item false** (item 8 — the scrub gate; items 1–7 TRUE)

Coworld `battlecode` v0.2.0 `cow_d9fc2f21-c095-4131-bd86-d35848e046f8`,
league `league_b08a04aa-9d3d-4ff2-91a3-013e19a531cc` (bc20), division
`div_df107879-c101-4771-98b7-7adf428b78c1`.

All headers are named, never their values:
`AUTH = -H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0"`,
`ELEV = -H "X-Use-Elevated-Privileges: true"`.
Every fetch below was made fresh in this heartbeat (2026-09-04 08:13Z–08:36Z). The two
documented exceptions are item 7 (the committed `release-result.json`) and item 8 (the
artifacts of the three `viewer-check.yml` runs dispatched in this heartbeat).

| # | Item | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | TRUE |
| 2 | Both champions ranked, fillers absent | TRUE |
| 3 | Latest round's episode request completed with a replay | TRUE |
| 4 | Replay bytes valid and show a contested game | TRUE |
| 5 | Hosted game log clean | TRUE |
| 6 | Public page uses the **static** replay path | TRUE |
| 7 | Certification declared the static bundle | TRUE |
| 8 | Viewer EXECUTED: `loaded:true` **and** three differing clock readouts | **FALSE** (`loaded:true`, but only 2 of 3 readouts differ — instrument mis-targeted, see below) |

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

```bash
BASE=https://softmax.com/api/observatory/v2
L=league_b08a04aa-9d3d-4ff2-91a3-013e19a531cc
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}"
```

Response (bare array; trimmed to the fields the check reads — the full body repeats the whole
`division`/`league`/`game` object under every row):

```json
[
  {
    "id": "round_ae434347-5e0c-4930-87a0-be4349749656",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "skip_kind": null,
    "scheduled_by": "ladder",
    "created_at": "2026-09-04T08:26:19.529765Z",
    "completed_at": "2026-09-04T08:27:18.867136Z",
    "round_config": {
      "purpose": "ladder",
      "entrant_policy_version_ids": [
        "66abf8b9-6c29-4934-8cc3-3529097e19ff",
        "5fe2b757-1be8-47c5-bf1c-1a51b9f75844"
      ]
    }
  },
  {
    "id": "round_ead26855-0352-4701-9a3b-562f9236a7c7",
    "round_number": 1,
    "status": "completed",
    "error": null,
    "skip_kind": null,
    "scheduled_by": "ladder",
    "created_at": "2026-09-04T08:11:19.022305Z",
    "completed_at": "2026-09-04T08:12:12.031049Z",
    "round_config": {
      "purpose": "ladder",
      "entrant_policy_version_ids": [
        "66abf8b9-6c29-4934-8cc3-3529097e19ff",
        "5fe2b757-1be8-47c5-bf1c-1a51b9f75844"
      ]
    }
  }
]
```

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
2
```

Fillers are set on the league, fetched fresh (this read 403s on bare AUTH — `ELEV` sent):

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"
```
```json
{
  "filler_policy_versions": [
    {"policy_version_id": "fef73ff9-c4ed-4acd-910e-b34d0198ab13",
     "policy_id": "e6be4b5c-8063-40f4-941a-a554a4b8fbcf",
     "policy_name": "battlecode-bowl-of-chowder", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "display_name": null},
    {"policy_version_id": "14072215-0a2f-4dd3-8be7-409fbfb5ab49",
     "policy_id": "4471bcfa-6141-49e9-a94b-338f9b0f566d",
     "policy_name": "battlecode-examplefuncsplayer", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "display_name": null}
  ]
}
```

and are echoed on the league object returned inside the same `/rounds` body:

```json
"filler_policy_version_ids": [
  "fef73ff9-c4ed-4acd-910e-b34d0198ab13",
  "14072215-0a2f-4dd3-8be7-409fbfb5ab49"
],
"seed_policy_version_ids": null
```

Status: **TRUE** — 2 completed rounds, both `error: null`, no `failed`/`discarded` rows exist.
Ordering against the filler registration: `log.md` records the fillers registered in phase 50
*before* `trigger-round` (`2026-09-04T08:12:14Z 50 fillers 200: … ; 50 unpaused 200;
trigger-round 200 … round_ead26855 round 1 pending` — the 08:12:14Z stamp is that phase's batch
write, not a per-call clock). Round 2 (`created_at 08:26:19.529765Z`) is after that batch write
on any reading. Round 1 is also after the filler write, by the documented platform rule in
`playbooks/observatory-api.md` §6: *"A `trigger-round` issued before any filler exists fails
instantly with `Temporal RoundWorkflow failed before settling the round`."* Round 1 settled
`completed` with `error: null`, so a filler existed when it was triggered. Round 3 was due
~08:41Z and was not awaited: the criterion is already met.

---

## 2. Both champions ranked, fillers absent — TRUE

```bash
D=div_df107879-c101-4771-98b7-7adf428b78c1
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}"
```
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
    "policy_label": "battlecode-bc20-rusher:v1",
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
    "policy_label": "battlecode-bc20-latticer:v1",
    "recent_rounds": null
  }
]
```

Status: **TRUE** — `daveey` (`battlecode-bc20-latticer:v1`, rounds_played 2) and `daveey-1`
(`battlecode-bc20-rusher:v1`, rounds_played 2) are both ranked. The board has exactly two rows:
neither filler (`battlecode-bowl-of-chowder:v1`, `battlecode-examplefuncsplayer:v1`) appears, and
no `Baseline (N)` row appears — with two ranked champions the ladder never needed a filler seat.
The two champions have swapped after round 2 (daveey led 1016–984 after round 1), which is the
ELO moving, not a stale board.

---

## 3. Latest round's episode request completed with a replay — TRUE

The latest completed round is `round_ae434347-5e0c-4930-87a0-be4349749656` (round_number 2,
from item 1). The flat list route is dead for GET, confirmed this run:

```bash
curl -sS -w "\nHTTP %{http_code}\n" "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}"
{"detail":"Method Not Allowed"}
HTTP 405
```

The nested route works (`playbooks/observatory-api.md` §9):

```bash
R=round_ae434347-5e0c-4930-87a0-be4349749656
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}"
```
```json
{
  "entries": [
    {
      "id": "ereq_330eeacf-0710-429a-b155-10ea4c7c0b7e",
      "status": "completed",
      "coworld_id": "cow_d9fc2f21-c095-4131-bd86-d35848e046f8",
      "round_id": "round_ae434347-5e0c-4930-87a0-be4349749656",
      "replay_url": "https://softmax-public.s3.amazonaws.com/replays/bb7e21c2-3fe7-4dcf-b299-19b7ed1d1d1b.replay",
      "policy_version_ids": [
        "66abf8b9-6c29-4934-8cc3-3529097e19ff",
        "5fe2b757-1be8-47c5-bf1c-1a51b9f75844"
      ],
      "created_at": "2026-09-04T08:26:19.910913Z"
    }
  ],
  "next_cursor": null
}
```

```bash
EREQ=ereq_330eeacf-0710-429a-b155-10ea4c7c0b7e
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/bb7e21c2-3fe7-4dcf-b299-19b7ed1d1d1b.replay",
  "participants": [
    {
      "position": 0,
      "kind": "policy",
      "policy_version_id": "66abf8b9-6c29-4934-8cc3-3529097e19ff",
      "policy_id": "add90fa2-ffb9-4e93-8ef4-58ab766fa613",
      "policy_name": "battlecode-bc20-latticer",
      "version": 1,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": false,
      "is_seed": false
    },
    {
      "position": 1,
      "kind": "policy",
      "policy_version_id": "5fe2b757-1be8-47c5-bf1c-1a51b9f75844",
      "policy_id": "c9f03683-988e-40bb-b85c-595879444c75",
      "policy_name": "battlecode-bc20-rusher",
      "version": 1,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
      "player_name": "daveey-1",
      "is_filler": false,
      "is_seed": false
    }
  ],
  "participant_scores": [
    {"position": 0, "score": 139.33333333333334},
    {"position": 1, "score": 259.6666666666667}
  ]
}
```

Status: **TRUE** — `status: "completed"`, non-null `replay_url`, participants are `daveey`
(latticer, seat 0) and `daveey-1` (rusher, seat 1), both `is_filler: false`, and the two policy
version ids match STATE's champions exactly.

---

## 4. Replay bytes are valid and show a contested game — TRUE

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/bb7e21c2-3fe7-4dcf-b299-19b7ed1d1d1b.replay" -o /tmp/ep.replay
# HTTP 200 bytes=73128
python3 -c "
import json
raw=open('/tmp/ep.replay','rb').read(); raw.decode('utf-8')   # strict UTF-8, not a browser
d=json.loads(raw.decode('utf-8')); print('strict UTF-8 JSON: ok  bytes=%d'%len(raw))"
strict UTF-8 JSON: ok  bytes=73128
```

*(`jq -e .` is not trusted here on its own: this game's replay uses `.result` singular and
`.kind` for events, and the phase prompt's `.type`/`.results` queries silently return empty on
this schema. The parse above is python's strict `bytes.decode('utf-8')` + `json.loads`.)*

**Header** — `protocol` matches the manifest (`cogame.battlecode.v1`):

```json
format = "cogame-battlecode-replay"
version = 1
protocol = "cogame.battlecode.v1"
game_version = "GV05"
year = "bc20"
seed = 1718466699
names = ["daveey", "daveey-1"]
aliases = ["Clan Ash", "Clan Basil"]
```

**`.result` (episode-level, minus the per-game array):**

```json
{
  "scores": [139.33333333333334, 259.6666666666667],
  "wins": [1, 2],
  "points": [[49, 55, 14], [50, 44, 85]],
  "policy_kind": ["llm", "llm"],
  "fallbacks": [0, 0],
  "decision_ms": [6644, 6644],
  "sheet_defaults_applied": [[], []],
  "sim_seconds": 0.598,
  "wall_clock_seconds": 13.356,
  "reason": "complete",
  "game_version": "GV05",
  "seed": 1718466699,
  "year": "bc20"
}
```

`reason == "complete"` — the normal case; the design note's `deadline` exception
(`design.md` line 387: *"`deadline` is **declared acceptable** for this coworld at phase-60
check 4"*) is not needed.

**Substance A — the doctrine sheets are real LLM output, not fallbacks.**
`result.fallbacks == [0, 0]`, `result.policy_kind == ["llm","llm"]`,
`result.sheet_defaults_applied == [[], []]`, and there is **no `doctrine_fallback` event** in the
replay:

```bash
python3 -c "...print([e for e in d['events'] if e['kind']=='doctrine_fallback'])"
[]
```
Per-seat: `seats[0].fallback = null`, `seats[0].fallback_detail = null`;
`seats[1].fallback = null`, `seats[1].fallback_detail = null`. Both sheets arrived on attempt 1:

```json
{"kind": "doctrine_requested", "ms": 0, "slot": 0, "attempt": 1, "deadline_ms": 20000}
{"kind": "doctrine_requested", "ms": 0, "slot": 1, "attempt": 1, "deadline_ms": 20000}
{"kind": "doctrine_received", "ms": 6644, "slot": 0, "attempt": 1, "latency_ms": 6644, "defaults_applied": 0, "unknown_fields": 0}
{"kind": "doctrine_received", "ms": 6644, "slot": 1, "attempt": 1, "latency_ms": 6644, "defaults_applied": 0, "unknown_fields": 0}
```

**Substance B — the two sheets differ materially.** Recorded verbatim in the replay
(`seats[n].sheet_submitted`):

*seat 0 — daveey / Clan Ash / `battlecode-bc20-latticer:v1`*
```json
{"opening":"lattice","terraform_start_round":280,"lattice_radius":7,"landscaper_count_curve":"steady","miner_count_curve":"steady","vaporator_budget":3,"drone_role":"carry_landscapers","net_gun_ring":2,"rush_trigger":0,"wall_hq_round":220}
```
motto: `"Build the wall before the water learns to climb."`
notes: `"Game 1 (elev 4→10 by r400), Game 2 (elev 3→9 by r380), Game 3 (elev 2→8 by r360). Lattice radius 7 for robust walls. Steady miners/landscapers, 3 vaporators to sustain soup mid-game. Drones carry landscapers to wall, net_gun_ring 2 defends. Early wall at 220 to seal before flood "` *(cut at the design's 280-rune cap)*

*seat 1 — daveey-1 / Clan Basil / `battlecode-bc20-rusher:v1`*
```json
{"opening":"rush","terraform_start_round":300,"lattice_radius":3,"landscaper_count_curve":"swarm","miner_count_curve":"steady","vaporator_budget":0,"drone_role":"buster","net_gun_ring":2,"rush_trigger":240,"wall_hq_round":280}
```
motto: `"Bury them before the water does."`
notes: `"Rush two waves of landscapers (12+12 on steady miners) hitting enemy HQ round ~300 via buster drones stripping their wall. If rush stalls, pivot to tight lattice (r=3) + net guns at r=2 for drone defense while surveyors hold the flood perimeter."`

They differ on 7 of 10 knobs and in the direction the brief predicted: latticer opens `lattice`
with `lattice_radius 7`, `vaporator_budget 3`, `rush_trigger 0`, `drone_role
carry_landscapers`; rusher opens `rush` with `rush_trigger 240`, `landscaper_count_curve swarm`,
`vaporator_budget 0`, `drone_role buster`. Not one template with two names.

**Substance C — the games were contested; nobody idled.** `.result.games[]`:

```json
{"map": "Climb", "rounds_played": 1499, "winner": 1, "end_reason": "quality", "hq_alive": [true, true], "hq_lost_cause": ["none","none"], "units_built": [23, 24], "miners_built": [6, 6], "landscapers_built": [10, 16], "drones_built": [1, 0], "net_guns_built": [2, 0], "dirt_moved": [59, 213], "soup_mined": [1755, 1755], "soup_refined": [1600, 1600], "net_worth": [3027, 3086], "transactions_sent": [2, 3], "global_pollution_peak": 160, "flooded_tiles_end": 32, "water_level_end": 6.606289863586426}
{"map": "ALandDivided", "rounds_played": 1499, "winner": 0, "end_reason": "quantity", "hq_alive": [true, true], "hq_lost_cause": ["none","none"], "units_built": [49, 43], "miners_built": [6, 6], "landscapers_built": [11, 20], "drones_built": [8, 11], "net_guns_built": [7, 2], "dirt_moved": [8881, 744], "soup_mined": [5698, 5698], "soup_refined": [5480, 5400], "net_worth": [3447, 2076], "transactions_sent": [7, 3], "global_pollution_peak": 215, "flooded_tiles_end": 1266, "water_level_end": 6.606289863586426}
{"map": "WateredDown", "rounds_played": 464, "winner": 1, "end_reason": "hq_destroyed", "hq_alive": [false, true], "hq_lost_cause": ["drowned","none"], "units_built": [17, 18], "miners_built": [8, 6], "landscapers_built": [6, 11], "drones_built": [0, 0], "net_guns_built": [1, 0], "dirt_moved": [435, 888], "soup_mined": [1600, 1600], "soup_refined": [1500, 1600], "net_worth": [744, 1532], "transactions_sent": [10, 2], "global_pollution_peak": 155, "flooded_tiles_end": 332, "water_level_end": 2.001204252243042}
```

Three different maps, three different `end_reason`s (`quality`, `quantity`, `hq_destroyed`), and
the series split 1–2 rather than a sweep. Both seats built in every game (min `units_built` 17 vs
18 on the shortest game; 49 vs 43 on the longest), both mined identical soup on all three maps
(the symmetric maps are being played symmetrically, not one side sitting still), both moved dirt
in every game. Game 3 ended by the water, not by an idle: `hq_lost_cause[0] == "drowned"` at
`water_level 2.00` with 332 tiles flooded — Clan Ash's terraforming lost the race to the flood.
Game 2 shows the doctrine difference biting: latticer moved 8881 dirt to rusher's 744 and won on
`quantity`.

**Event census** (76→72 events; `.kind`, not `.type`):

```
Counter({'first_build': 34, 'flood_stage': 14, 'wall_closed': 6, 'game_start': 3,
         'rush_launched': 3, 'game_end': 3, 'doctrine_requested': 2, 'doctrine_received': 2,
         'drone_water_drop': 2, 'episode_start': 1, 'hq_drowned': 1, 'episode_end': 1})
```

Status: **TRUE** — strict UTF-8 JSON, `protocol` matches, `reason == "complete"`, zero
fallbacks, materially different LLM doctrines, three genuinely contested games.

---

## 5. Hosted game log is clean — TRUE

```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs2.raw
# HTTP 200, 1754 bytes of python b'…' reprs under ===== container: … ===== headers
# decoded per-line with ast.literal_eval before grepping (playbook §10)
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs2.decoded || echo CLEAN
CLEAN
```

The whole decoded body (1703 chars), pasted rather than summarised:

```
=== container: coworld-init-config ===

=== container: bedrock-sidecar ===
2026-09-04 08:26:26,913 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1","has_role_arn":true,"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar","episode_request_id":"330eeacf-0710-429a-b155-10ea4c7c0b7e","job_request_id":"bb7e21c2-3fe7-4dcf-b299-19b7ed1d1d1b","role":"game","slot":"game","image_digest":"sha256:01fec567f0236e7cc3222b0f827a350c8228636d06389ef5a7246671165c3ce8"}
[2026-09-04 08:26:27 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-09-04 08:26:27,195 INFO hypercorn.error Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-09-04 08:26:35,110 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-04 08:26:38,370 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"

=== container: game ===
battlecode config: year=bc20 pool=mixed seed=1718466699 games=3 maxRounds=1500 num_agents=2 matchBudget=320s
battlecode: listening on 0.0.0.0:8080
battlecode: waiting for seats
battlecode: refused a seat-0 connection: seat 0 was given the wrong connection token
battlecode: a spectator joined /global
battlecode: seat 1 connected
battlecode: seat 1 registered kind=llm label=rusher
battlecode: seat 0 connected
battlecode: seat 0 registered kind=llm label=latticer
battlecode: doctrine
battlecode llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
battlecode: match
battlecode: settled: complete
battlecode: reason=complete games=3 scores=[139.33333333333334, 259.6666666666667] sim=0.598s wall=13.356s
```

Status: **TRUE** — zero matches for any of the four patterns. Both LLM calls returned
`HTTP/1.1 200 OK`; no Bedrock capacity symptom, so no cross-check against another LLM coworld is
needed. Two lines worth naming so nobody mistakes them later: `refused a seat-0 connection: seat
0 was given the wrong connection token` is the seat-token guard rejecting a stray connect and is
followed two lines later by `seat 0 connected` / `seat 0 registered kind=llm label=latticer` — it
does not contain any of the four gated strings, and both seats registered `kind=llm`.

---

## 6. The public page uses the static replay path — TRUE

**Source used: the page's SSR payload + the session endpoint the page's own JS calls.** The raw
HTML grep is a documented dead end (`playbooks/observatory-api.md` §Featured match, lighthouse
2026-08-22) and it was again here — recorded, not treated as a false negative:

```bash
curl -sS "https://softmax.com/battlecode/bc20" | grep -o '<iframe[^>]*src="[^"]*"'
# HTTP 200, 867242 bytes, NO MATCH  (also no match on https://softmax.com/battlecode)
```

The documented API fallback is also null platform-wide, exactly as the playbook says — recorded,
not used as evidence:

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)[]|select(.name=="battlecode")|{id,name,canonical,version,replay_viewer,featured_match}'
{"id":"cow_d9fc2f21-c095-4131-bd86-d35848e046f8","name":"battlecode","canonical":true,"version":"0.2.0","replay_viewer":null,"featured_match":null}
{"id":"cow_cfddca58-fa27-4dfd-bab8-38619b06fee7","name":"battlecode","canonical":false,"version":"0.1.6","replay_viewer":null,"featured_match":null}
{"id":"cow_6f3468fa-5cf5-4c4b-95cf-1d87dc41bfa2","name":"battlecode","canonical":false,"version":"0.1.5","replay_viewer":null,"featured_match":null}
```

**The featured match, server-rendered into the page at `state.playlist[0]`** (excerpt of
`/battlecode/bc20`'s SSR payload, fetched 08:28Z, un-escaped only for width):

```json
"playlist":[{"episodeId":"4c51129d-a80d-4136-923e-7914c6220ae5",
 "coworldId":"cow_d9fc2f21-c095-4131-bd86-d35848e046f8",
 "coworldName":"battlecode","coworldVersion":"0.2.0",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/bb7e21c2-3fe7-4dcf-b299-19b7ed1d1d1b.replay",
 "finishedAt":"2026-09-04T08:27:06.452133Z","roundNumber":2,"episodeNumber":1,
 "code":"battlecode.r2.e1",
 "matchup":{"divisionId":"div_df107879-c101-4771-98b7-7adf428b78c1","divisionName":"Competition",
   "first":{"rank":1,"player_name":"daveey-1","score":1001.4695015289755,
            "policy_label":"battlecode-bc20-rusher:v1","rounds_played":2,"episode_wins":1,"win_rate":0.5},
   "second":{"rank":2,"player_name":"daveey", …,"policy_label":"battlecode-bc20-latticer:v1"}}}]
```

A featured match is present and it is round 2's episode — the same `replay_url` as item 3.

**The iframe `src`, from the call the page's JS makes:**

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_d9fc2f21-c095-4131-bd86-d35848e046f8",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/bb7e21c2-3fe7-4dcf-b299-19b7ed1d1d1b.replay"}'
```
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_d9fc2f21-c095-4131-bd86-d35848e046f8/sha256%3A5f42d8642f01dd9116b7a320e554941faf6214a3cb1fb6789569cdeaf3023865/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fbb7e21c2-3fe7-4dcf-b299-19b7ed1d1d1b.replay","ready":true}
HTTP 200
```

Status: **TRUE** — the path is
`/v2/coworlds/replays/static/<cow_id>/<manifest sha, URL-encoded>/index.html`, with the replay
delivered as the URL-encoded fragment `#replay=<s3 url>` (the documented 2026-08-28 variant of
the static route, `playbooks/observatory-api.md` §Featured match). `ready: true`. The `<sha>` is
`sha256:5f42d8642f01dd9116b7a320e554941faf6214a3cb1fb6789569cdeaf3023865`, byte-identical to
`STATE.coworld.manifest_sha`. **No `/client/replay` pod URL anywhere.** The query form of the
same route also serves the live viewer — item 8 attempt 3 loaded
`…/index.html?replay=<encoded s3 url>` successfully (`loaded:true` in 1861 ms).

---

## 7. Certification declared the static bundle — TRUE

**Source: the committed `runs/2026-09-04-battlecode-2020-soup/release-result.json`** (the copy
phase 40 downloaded from release run `33850681870` and committed). It was present; no
re-download was needed.

```bash
jq -r '.certify.replay_liveness' runs/2026-09-04-battlecode-2020-soup/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Corroborating tail from the same file (`.certify.output_tail`), showing the transcript that
produced that line:

```
  [pass] replay-present: a replay artifact was produced
  [pass] replay-loadable: the replay artifact has a declared viewer path
  [pass] players-run: every declared player actually started on the smoke episode (not just declared)
  [pass] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks
Certified dist/coworld_manifest.json
Transcript: coworld-executable (10 steps passed)
…
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE** — contains `Replay liveness: skipped (static replay bundle declared`, read from
the committed artifact.

---

## 8. Spectator judgment — the viewer, EXECUTED — **FALSE** (by the scrub rule)

Three `viewer-check.yml` runs were dispatched in this heartbeat against
`Metta-AI/coworld-builder`; all three artifacts are committed under
`runs/2026-09-04-battlecode-2020-soup/viewer-check/`.

| attempt | run id | url form | artifact dir | conclusion |
|---|---|---|---|---|
| 1 (primary) | `33853624448` | the item-6 `src` verbatim (`?v=2#replay=`) | `viewer-check/` | success |
| 2 (hypothesis test) | `33853943737` | `?v=2&viewpanel=0#replay=` | `viewer-check/attempt-2-viewpanel0/` | success |
| 3 (reproducibility + query form) | `33854088585` | `?replay=<encoded s3>` | `viewer-check/attempt-3-query-form/` | success |

### (a) Dispatch — attempt 1, the primary

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_d9fc2f21-c095-4131-bd86-d35848e046f8/sha256%3A5f42d8642f01dd9116b7a320e554941faf6214a3cb1fb6789569cdeaf3023865/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fbb7e21c2-3fe7-4dcf-b299-19b7ed1d1d1b.replay'
# dispatch stamp: 2026-09-04T08:28:41Z
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:3][]|[.databaseId,.createdAt,.status]|@tsv'
33853624448	2026-09-04T08:28:43Z	in_progress          <- created AFTER the dispatch stamp
33837929180	2026-09-04T04:44:38Z	completed
33837175511	2026-09-04T04:32:13Z	completed
gh run watch 33853624448 -R Metta-AI/coworld-builder --exit-status   # green, 36s
gh run download 33853624448 -R Metta-AI/coworld-builder -n viewer-check \
  -D runs/2026-09-04-battlecode-2020-soup/viewer-check
```

### (b) The readouts — attempt 1

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/…/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":5547,"clock":"2:24 GAME 1 OF 3 — CLIMB doctrines","scorebug":"CLAN ASH daveey · Build the wall before the water learns to climb. 50 2:24 GAME 1 OF 3 — CLIMB doctrines CLAN BASIL daveey-1 · Bury them before the water does. 50","feed_lines":3}
```

```bash
jq -c '.signals' runs/…/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["ready"],"bridge_ready":true,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/…/viewer-check/viewer-smoke.json
no failure
```
```bash
jq -c '.canvas_text' runs/…/viewer-check/viewer-smoke.json
{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
# total 0 = the board is drawn by a worker/OffscreenCanvas renderer, so the text-bounds hook
# saw nothing. Recorded, not judged on.
```
```bash
jq -c '.console_tail' runs/…/viewer-check/viewer-smoke.json
["[bridge] ready"]
```

**The three clock readouts (attempt 1):**

| scrub position | `#clock` readout |
|---|---|
| 0 %   | `2:24 GAME 1 OF 3 — CLIMB doctrines` |
| 50 %  | `2:23 GAME 1 OF 3 — CLIMB doctrines` |
| 100 % | `2:23 GAME 1 OF 3 — CLIMB doctrines` |

**Attempt 3 (same URL content, canonical `?replay=` query form) reproduces it exactly:**

```json
{"loaded":true,"ms":1861,"clock":"2:24 GAME 1 OF 3 — CLIMB doctrines","scorebug":"CLAN ASH daveey · Build the wall before the water learns to climb. 50 2:24 GAME 1 OF 3 — CLIMB doctrines CLAN BASIL daveey-1 · Bury them before the water does. 50","feed_lines":3}
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["ready"],"bridge_ready":true,"bridge_error":[]}
0%	2:24 GAME 1 OF 3 — CLIMB doctrines
50%	2:23 GAME 1 OF 3 — CLIMB doctrines
100%	2:23 GAME 1 OF 3 — CLIMB doctrines
no failure
```

### Verdict on item 8, and why

`loaded: true` on all three runs (`data-replay-loaded="true"` **and** the `coworld-replay`
bridge `ready`, both signals, in 1.9–5.5 s, no `failure`). Condition 1 holds.

Condition 2 does **not**: 50 % and 100 % read the same, and the caption never leaves
`GAME 1 OF 3 — CLIMB`. **Item 8 is FALSE.** I am not marking it true on an inference.

What the evidence says the cause is — a **mis-targeted instrument**, not a frozen viewer.
`templates/tools/ci/viewer_smoke.mjs` seeks by clicking
`page.locator('#scrub, #seek, input[type="range"]').first()`. Playwright resolves a comma
selector in **DOM order**, and in this shell the zoom slider comes first:

```bash
curl -sS ".../index.html" -o /tmp/viewer.html      # HTTP 200, 177566 bytes
grep -n 'id="zoom-slider"' /tmp/viewer.html   →  2830:  <input id="zoom-slider" type="range" min="0" max="1000" step="1" value="0"
grep -n 'id="scrub"'      /tmp/viewer.html   →  2893:  <div class="scrub" id="scrub">
# byte offsets: zoom-slider 141293, scrub 144578 — the range input precedes the scrubber,
# and #scrub is a <div>, not an input, so `.first()` never reaches it.
```

Three independent confirmations that the clicks landed on the zoom slider:

1. `viewer-smoke.png` (attempt 1 and attempt 3) shows the zoom readout at **`12.0×`** with the
   knob at the right end. The shell's own code sets `value = round(((zoom-1)/11)*1000)`, so
   `12.0×` is the slider at its **maximum** — exactly a click at 100 % of that track. Its
   default is `value="0"` / `FIT`.
2. The transport playhead is still at the **far left** in both screenshots, with `#tick-clock`
   reading `round 41 / 1500` (attempt 1) and `round 38 / 1500` (attempt 3) — no seek happened.
3. **Attempt 2 is the controlled test.** The shell honours `?viewpanel=0`
   (`body[data-noviewpanel] #viewpanel { display: none !important; }`), which hides the zoom
   slider. With it hidden, `boundingBox()` returned null and the harness's scrub loop broke
   after the first sample — the readout array collapsed to exactly one entry:

   ```json
   {"loaded":true,"ms":2190,"clock":"2:24 GAME 1 OF 3 — CLIMB","scorebug":"CLAN ASH daveey · Build the wall before the water learns to climb. 50 2:24 GAME 1 OF 3 — CLIMB CLAN BASIL daveey-1 · Bury them before the water does. 50","feed_lines":3}
   [{"at":"0%","clock":"2:24 GAME 1 OF 3 — CLIMB"}]
   ```

   Hiding the zoom slider removed the scrub readouts. That is only possible if the zoom slider
   *was* the element being scrubbed.

The static bundle exposes `#scrub`, `#scrub-fill`, `#scrub-head`, `#scrub-win`, `#momentum`,
`#transport`, `#tick-clock`, `#clock`, `#scorebug`, `#endcard` — the parley/paintbot chrome ids
the harness expects. The shell is not missing a scrubber; the harness reaches the zoom control
first. **This looks like a coworld-builder harness defect (`SCRUB_SELECTOR` must prefer `#scrub`
over any range input, e.g. by trying the selectors in order rather than as one comma list), not
a defect in this coworld.** Reporting it, not fixing it — a verifier does not edit code. Retry
budget spent: 3 of 3 (baseline / `viewpanel=0` control / query-form reproduction). No fourth
approach exists inside the workflow's two inputs (`url`, `timeout`), and the shell's bootstrap
reads only `replay` from the hash, so there is no deep-link that could seek.

**Motion evidence that does exist, from the downloaded artifacts** (offered as observation, not
as a substitute for the gate): the clock advanced `2:24 → 2:23` between the 0 % and 50 % samples
in both attempts 1 and 3 — the viewer is playing in real time, not holding one frame; the three
runs screenshotted at three different sim rounds (`round 2 / 1500`, `round 38 / 1500`,
`round 41 / 1500`) with three different water readouts (`WATER 0.01`, `0.12`, `0.13`); and the
feed accumulated as it played — attempt 2 (screenshot at 2.2 s) shows `Game 1 begins on Climb`
and the first-miner lines, while attempts 1 and 3 (screenshot ~6 s later) additionally show the
round-34 design-school lines. A viewer stuck on one frame produces none of that.

### (c) The replay JSON — what the viewer was asked to draw

Ordered event excerpts from `/tmp/ep.replay` (item 4's bytes; `.kind`, not `.type`):

**Early**
```
kind="episode_start" ms=0 maps=["Climb", "ALandDivided", "WateredDown"] aliases=["Clan Ash", "Clan Basil"] seed=1718466699 year="bc20"
kind="doctrine_requested" ms=0 slot=0 attempt=1 deadline_ms=20000
kind="doctrine_requested" ms=0 slot=1 attempt=1 deadline_ms=20000
kind="doctrine_received" ms=6644 slot=0 attempt=1 latency_ms=6644 defaults_applied=0 unknown_fields=0
kind="doctrine_received" ms=6644 slot=1 attempt=1 latency_ms=6644 defaults_applied=0 unknown_fields=0
kind="game_start" game=0 round=0 map="Climb" width=40 height=40 sides=["Clan Ash", "Clan Basil"]
kind="first_build" game=0 round=1 alias="Clan Ash" unit="miner"
kind="first_build" game=0 round=1 alias="Clan Basil" unit="miner"
kind="first_build" game=0 round=34 alias="Clan Ash" unit="design_school"
kind="first_build" game=0 round=34 alias="Clan Basil" unit="design_school"
kind="first_build" game=0 round=57 alias="Clan Ash" unit="landscaper"
kind="first_build" game=0 round=58 alias="Clan Basil" unit="landscaper"
kind="wall_closed" game=0 round=105 alias="Clan Ash" min_ring_elevation=8
kind="wall_closed" game=0 round=108 alias="Clan Basil" min_ring_elevation=8
kind="first_build" game=0 round=141 alias="Clan Ash" unit="refinery"
kind="first_build" game=0 round=168 alias="Clan Ash" unit="net_gun"
kind="rush_launched" game=0 round=240 alias="Clan Basil" units=1
kind="flood_stage" game=0 round=256 level=1 flooded_tiles=12
```

**Middle**
```
kind="first_build" game=1 round=34 alias="Clan Basil" unit="design_school"
kind="first_build" game=1 round=35 alias="Clan Ash" unit="design_school"
kind="first_build" game=1 round=58 alias="Clan Basil" unit="landscaper"
kind="first_build" game=1 round=60 alias="Clan Ash" unit="landscaper"
kind="first_build" game=1 round=101 alias="Clan Ash" unit="refinery"
kind="wall_closed" game=1 round=113 alias="Clan Basil" min_ring_elevation=8
kind="first_build" game=1 round=118 alias="Clan Ash" unit="net_gun"
kind="wall_closed" game=1 round=119 alias="Clan Ash" min_ring_elevation=8
kind="first_build" game=1 round=142 alias="Clan Ash" unit="fulfillment_center"
kind="first_build" game=1 round=152 alias="Clan Ash" unit="delivery_drone"
kind="rush_launched" game=1 round=240 alias="Clan Basil" units=1
kind="first_build" game=1 round=243 alias="Clan Ash" unit="vaporator"
```

**Late**
```
kind="wall_closed" game=2 round=140 alias="Clan Ash" min_ring_elevation=8
kind="wall_closed" game=2 round=144 alias="Clan Basil" min_ring_elevation=8
kind="rush_launched" game=2 round=240 alias="Clan Basil" units=1
kind="flood_stage" game=2 round=256 level=1 flooded_tiles=135
kind="first_build" game=2 round=265 alias="Clan Ash" unit="refinery"
kind="first_build" game=2 round=286 alias="Clan Ash" unit="net_gun"
kind="flood_stage" game=2 round=464 level=2 flooded_tiles=332
kind="hq_drowned" game=2 round=464 alias="Clan Ash" water_level=2.001204252243042
kind="game_end" game=2 round=464 winner_alias="Clan Basil" winner_slot=1 end_reason="hq_destroyed" points=[14, 85]
kind="episode_end" ms=0 reason="complete"
```

### The spectator judgment

**It is legible, and it does show the game — but the primary screenshot is unreadable for a
reason that has nothing to do with the viewer.** In attempt 1 and attempt 3 the harness dragged
the board zoom to its 12.0× maximum before the screenshot, so what the png shows is four
80-pixel soup cauldrons on an empty beige plain: no units, no HQs, no grid, no sense of a
board. Judged on that frame alone a spectator would see nothing. That is the instrument's
doing, not the shell's — the shell's default is `FIT`.

Attempt 2's screenshot (`viewer-check/attempt-2-viewpanel0/viewer-smoke.png`), taken with the
zoom panel suppressed and therefore never touched, is what a spectator actually gets, and it is
good. The whole 40×40 **Climb** board fits the frame: dozens of soup cauldrons scattered in
clusters, a dark flooded pool at the centre, one clan's red units grouped at their HQ top-left
and the other clan's blue units at theirs bottom-right, each on a darker terraformed patch (the
png does not label which colour is which alias, so I do not claim it). Across the top is
the scorebug — `CLAN ASH` / `daveey · Build the wall before the water learns to climb.` / `50`
against `CLAN BASIL` / `daveey-1 · Bury them before the water does.` / `50` — carrying each
seat's real name and its own recorded motto, with `GAME 1 OF 3 — CLIMB` and a `doctrines` chip
between them. Directly under it the bc20 readout pill: `WATER 0.01`, a fill bar, `0% flooded`,
`Clan Ash HQ elev 4`, `Clan Basil HQ elev 4` — the three numbers this game is about, on screen
at all times. Bottom-right the killfeed narrates in plain sentences: `Game 1 begins on Climb`,
`Clan Ash builds its first miner — game 1, round 1`, `Clan Basil builds its first miner — game
1, round 1`. Along the bottom is the transport strip: restart / step-back / pause / +25 /
play / loop / fast-forward, a `spoilers` toggle, `round 2 / 1500`, the speed chips
`1× 2× 4× 8× 16×`, and the scrubber with the coloured momentum graph underneath it, its ticks
marking the beats.

**Picture and record agree.** The feed lines the png shows are the replay's own events:
`first_build … round 1 … miner` for both clans, then the round-34 design schools in the later
screenshots. `WATER 0.01 / 0% flooded / HQ elev 4` at round 2 matches game 0 opening before the
first `flood_stage` at round 256. The momentum graph's tick density matches an episode whose
beats cluster at rounds 1/34/57/105/240/256. Nothing on screen contradicts the JSON, and
nothing in the JSON is missing from the chrome.

**One legibility observation for the coordinator** (not a check-8 cause, and visible in all
three screenshots): the killfeed panel bottom-right is drawn **over** the two per-clan stat
boxes (`soup / mined / refined`) and the unit-tally strip, so `soup 61 / mined 0 / refined 0`
and the `M0 L0 D0 …` tallies read through the feed text and both are hard to read where they
overlap. The board, the scorebug, the water pill and the transport are all clean; it is only
that one corner. Worth a phase-30 note if the run comes back for another review round.

**It looks like the starter's chrome.** Same transport strip, same scrubber-with-momentum-graph,
same scorebug with mottos, same `#endcard` / `#killfeed` / `#speedchips` ids as
paintbot/raid/hive, with a bc20 block (`#bc20-flood`, `#bc20-soup`, `#bc20-units`,
`#bc20-chain`, `#bc20-doctrines`) appended rather than substituted. This is not the
cogame-gridlock failure — it is the family shell with a year block added.

---

## What is false, and what to do about it

Item 8 only. `loaded: true` three times over, no `failure`, both load signals, a legible
screenshot that matches the replay — but the required proof that the replay **seeks** was never
obtained, because the check's own scrubber selector resolves to this shell's zoom slider. I did
not mark it true, and I did not touch the harness. The judge's call is whether that is a
coworld defect (the evidence says it is not) or a coworld-builder tooling defect to fix in
`templates/tools/ci/viewer_smoke.mjs` before item 8 can be re-run honestly.

---

## 8 (re-run) — after the harness fix: TRUE

The verifier's root cause was accepted: `templates/tools/ci/viewer_smoke.mjs` resolved
`'#scrub, #seek, input[type="range"]'` in DOM order, so every seek click landed on this shell's
`#zoom-slider`. Fixed by the coordinator in coworld-builder commit `viewer_smoke: resolve scrub
target in preference order, not DOM order` (scrub target tried `#scrub` → `#seek` →
`input[type="range"]`, first present-and-visible wins; the mis-click is documented in the code
comment). No coworld code changed; the coworld repo was not touched.

Re-dispatch: `viewer-check.yml` run **33854861020** (conclusion success) against the SAME iframe
src as attempt 1 (`…/static/cow_d9fc2f21-…/sha256%3A5f42d864…/index.html?v=2#replay=…bb7e21c2….replay`).
Artifact committed at `runs/2026-09-04-battlecode-2020-soup/viewer-check-rerun/`.

```
{"loaded": true, "ms": 3191, "clock": "2:24 GAME 1 OF 3 — CLIMB doctrines",
 "scorebug": "CLAN ASH daveey · Build the wall before the water learns to climb. 50 2:24 GAME 1 OF 3 — CLIMB doctrines CLAN BASIL daveey-1 · Bury them before the water does. 50",
 "feed_lines": 3}
signals: {"data_replay_loaded": "true", "data_replay_error": null, "bridge": ["ready"], "bridge_ready": true, "bridge_error": []}
failure: null
```

| at | clock |
|---|---|
| 0% | `2:24 GAME 1 OF 3 — CLIMB doctrines` |
| 50% | `1:11 GAME 2 OF 3 — ALANDDIVIDED doctrines` |
| 100% | `FINAL MATCH OVER doctrines` |

Both conditions hold: `loaded: true` (both signals), and the three clock readouts differ — the
seek now crosses game boundaries (game 1 on Climb → game 2 on ALandDivided → the final endcard),
which is stronger motion evidence than a within-game clock tick. Item 8 is **TRUE**. The summary
table's item-8 row is superseded by this section.
