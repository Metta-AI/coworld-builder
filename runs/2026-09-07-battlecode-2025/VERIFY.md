# VERIFY — battlecode-2025   (2026-09-08T05:47Z)

Verdict: **all-true — 8 / 8**

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | TRUE — rounds 1 and 2, both `completed`, 0 failed |
| 2 | Both champions ranked, fillers absent/Baseline | TRUE — daveey + daveey-1, `rounds_played: 2` each; no filler rows |
| 3 | Latest round's episode request completed with a replay | TRUE — `ereq_30eabb74-…` completed, replay_url non-null, both champions seated |
| 4 | Replay bytes valid and show the game | TRUE — strict UTF-8 JSON, `protocol` matches, `result.reason == "complete"`, 0 fallbacks of 2 decisions |
| 5 | Hosted game log clean | TRUE — CLEAN, zero matches for all four patterns |
| 6 | Public page uses the static replay path | TRUE — `…/replays/static/<cow_id>/<manifest_sha>/index.html?v=2#replay=…`, `ready: true` |
| 7 | Certification declared the static bundle | TRUE — `Replay liveness: skipped (static replay bundle declared…` |
| 8 | Viewer executed and judged | TRUE — `loaded: true`, three differing clock readouts, soak advanced |

Two **non-blocking legibility findings** are recorded under check 8 for phase 30: bc26 nouns
("kings built / cheese delivered / cats damaged / the alliance held") on the bc25 endcard, and
doctrine cards that clip their last line.

Run: `2026-09-07-battlecode-2025` · slug `battlecode-2025` · coworld `cow_e58e703d-3d34-4d27-b8eb-4464a6209170` v0.5.0
League `league_7edecd14-58d2-4a23-aadb-491577a60935` (bc25) · Division `div_a5c7f237-a2e2-484a-9e97-f1fd9b8dfd97`
Base: `BASE=https://softmax.com/api/observatory/v2`
Headers sent (values never printed): `Authorization: Bearer $SOFTMAX_TOKEN`, `User-Agent: coworld-builder/1.0`,
and on artifact/elevated reads `X-Use-Elevated-Privileges: true`.

Fillers (`battlecode-spaark:v1` `c5a81b50-2497-4c59-8041-93c57c6ef609`,
`battlecode-examplefuncsplayer25:v1` `db05ec98-1121-4019-b731-898bca3e139d`) were registered
**before round 1** was triggered (log.md 2026-09-08T05:23:47Z), so **every** completed round counts
toward check 1.

Wall-clock bound for polling: 75 minutes from 2026-09-08T05:25Z → 06:40Z. Two completed rounds were
reached at 05:41Z, 16 minutes in; the bound was not approached.

---
## 1. ≥2 completed rounds after fillers were set

Poll log (5-minute cadence, Asana `heartbeat_at` refreshed at each poll — all HTTP 200):
05:25Z (1 completed) · 05:27Z (1) · 05:33Z (1) · 05:38Z (round 2 `pending`) · **05:41Z (2 completed)**.

**Final fetch — 2026-09-08T05:41:35Z**

```
GET $BASE/rounds?league_id=league_7edecd14-58d2-4a23-aadb-491577a60935&limit=20
    -H Authorization: Bearer $SOFTMAX_TOKEN  -H User-Agent: coworld-builder/1.0
```
(this deployment returns a **bare array** on `/rounds`; normalised with
`jq 'if type=="array" then . else .entries end'`)

```json
[
  {
    "id": "round_e6a531d2-ad6b-4344-9ed7-3dbbe682d3d8",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-09-08T05:37:45.413688Z",
    "completed_at": "2026-09-08T05:38:39.897979Z"
  },
  {
    "id": "round_f276b67f-13e6-45eb-b01f-3bc5c1d0c10c",
    "round_number": 1,
    "status": "completed",
    "error": null,
    "created_at": "2026-09-08T05:22:44.741631Z",
    "completed_at": "2026-09-08T05:23:46.749995Z"
  }
]
```

Intermediate poll at 05:38:29Z, pasted so the progression is on the record:

```json
[{"round_number":2,"status":"pending","completed_at":null,"error":null},
 {"round_number":1,"status":"completed","completed_at":"2026-09-08T05:23:46.749995Z","error":null}]
```

Status: **TRUE** — rounds **1** and **2** both `"status": "completed"` (at 05:23:46.749995Z and
05:38:39.897979Z). Zero `failed` or `discarded` rounds; `error` is `null` on both. The filler
policies were registered at 2026-09-08T05:23:47Z per `log.md`, **before** round 1 was triggered
(round 1 created 05:22:44Z and was still `pending` when the fillers landed), so both completed
rounds are after-fillers rounds.

---

## 2. Both champions ranked; fillers absent / Baseline

```
GET $BASE/divisions/div_a5c7f237-a2e2-484a-9e97-f1fd9b8dfd97/leaderboard
    -H Authorization: Bearer $SOFTMAX_TOKEN  -H User-Agent: coworld-builder/1.0
```
fetched 2026-09-08T05:25:38Z — bare JSON list, pasted verbatim:

```json
[
  {
    "rank": 1,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 1016.0,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 1,
    "episode_wins": 1.0,
    "episodes_played": null,
    "win_rate": 1.0,
    "policy_label": "battlecode-bc25-coverage:v1",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 984.0,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 1,
    "episode_wins": 0.0,
    "episodes_played": null,
    "win_rate": 0.0,
    "policy_label": "battlecode-bc25-siege:v1",
    "recent_rounds": null
  }
]
```

**Re-fetched fresh after round 2 — 2026-09-08T05:41:43Z** (bare JSON list, pasted verbatim):

```json
[
  {
    "rank": 1,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 1030.5304984710244,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 2.0,
    "episodes_played": null,
    "win_rate": 1.0,
    "policy_label": "battlecode-bc25-coverage:v1",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 969.4695015289755,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 0.0,
    "episodes_played": null,
    "win_rate": 0.0,
    "policy_label": "battlecode-bc25-siege:v1",
    "recent_rounds": null
  }
]
```

Status: **TRUE** — `daveey` (`battlecode-bc25-coverage:v1`) rank 1, `rounds_played: 2`;
`daveey-1` (`battlecode-bc25-siege:v1`) rank 2, `rounds_played: 2`. Both ≥ 1. Neither filler
(`battlecode-spaark:v1`, `battlecode-examplefuncsplayer25:v1`) appears anywhere in the list —
the "fillers absent" branch of the requirement. The list has exactly two rows.


---

## 3. The latest round's episode request completed with a replay and the right participants

Latest completed round = **round 2**, `round_e6a531d2-ad6b-4344-9ed7-3dbbe682d3d8`
(from the check-1 fetch above).

The flat `GET $BASE/episode-requests?round_id=…` route 405s on this deployment
(`playbooks/observatory-api.md` §9), so the **nested** route was used:

```
GET $BASE/rounds/round_e6a531d2-ad6b-4344-9ed7-3dbbe682d3d8/episode-requests
    -H Authorization: Bearer $SOFTMAX_TOKEN  -H User-Agent: coworld-builder/1.0
```
fetched 2026-09-08T05:41:43Z:

```json
[
  {
    "id": "ereq_30eabb74-86fe-4ca7-89c8-549e1fb8d280",
    "status": "completed",
    "replay_url": "https://softmax-public.s3.amazonaws.com/replays/a0418bda-3045-4e27-94b1-ed27f2143faf.replay"
  }
]
```

```
GET $BASE/episode-requests/ereq_30eabb74-86fe-4ca7-89c8-549e1fb8d280
    -H Authorization: Bearer $SOFTMAX_TOKEN  -H User-Agent: coworld-builder/1.0
| jq '{status, replay_url, participants, participant_scores}'
```
fetched 2026-09-08T05:41:52Z:

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/a0418bda-3045-4e27-94b1-ed27f2143faf.replay",
  "participants": [
    {
      "position": 0,
      "kind": "policy",
      "policy_version_id": "eb7ca912-4b32-4b50-af9e-e9a094ce8ec4",
      "policy_id": "169e98d0-2c69-4202-a3aa-d3bf3029a687",
      "policy_name": "battlecode-bc25-coverage",
      "version": 1,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": false,
      "is_seed": false
    },
    {
      "position": 1,
      "kind": "policy",
      "policy_version_id": "ae894e70-dfb5-4e2f-9882-b981bb3d797c",
      "policy_id": "878642a4-ab14-499c-a30d-232ebeb110b4",
      "policy_name": "battlecode-bc25-siege",
      "version": 1,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
      "player_name": "daveey-1",
      "is_filler": false,
      "is_seed": false
    }
  ],
  "participant_scores": [
    { "position": 0, "score": 465.5 },
    { "position": 1, "score": 33.5 }
  ]
}
```

Status: **TRUE** — `"status": "completed"`, non-null `replay_url`, and `participants` names
`daveey` (`battlecode-bc25-coverage` v1, policy_version `eb7ca912-…`, the STATE champion-1
version id) and `daveey-1` (`battlecode-bc25-siege` v1, policy_version `ae894e70-…`, the STATE
champion-2 version id). Both `is_filler: false`; no filler seats were needed (two ranked players,
two seats). `participant_scores` are non-degenerate (465.5 vs 33.5).

---

## 4. Replay bytes are valid and show the game

```
curl -sSL 'https://softmax-public.s3.amazonaws.com/replays/a0418bda-3045-4e27-94b1-ed27f2143faf.replay' -o /tmp/ep.replay
```
```
HTTP 200 bytes=97355
```

Strict UTF-8 JSON parse (`jq -e . /tmp/ep.replay`, a strict parser — not a browser):

```
strict UTF-8 JSON: ok
```

`jq -r '.protocol, .result.reason, .format, .version, .game_version, .year' /tmp/ep.replay`
(this coworld's replay carries the episode result under the key **`result`** (singular), not
`results`; `.results` is `null` and `.result.reason` is the field the design pins —
`design.md` line 1151: `{"format":"cogame-battlecode-replay","version":1,"protocol":"cogame.battlecode.v1", …}`):

```
cogame.battlecode.v1
complete
cogame-battlecode-replay
1
GV08
bc25
```

**Protocol matches the manifest.** `coworld_manifest_template.json` declares
`game.protocols.{player,global}` as URIs to `docs/PROTOCOL.md`; that document's line 1 is the
protocol id, and the bc25 section restates it:

```
$ gh api repos/Metta-AI/cogame-battlecode/contents/docs/PROTOCOL.md -H 'Accept: application/vnd.github.raw' | grep -n 'cogame\.battlecode\.v1'
1:# `cogame.battlecode.v1`
38:{"protocol":"cogame.battlecode.v1","game_version":"GV03","year":"bc26",
127:The protocol id is **unchanged** — `cogame.battlecode.v1`. The wire shape is
```

and the manifest's variant table carries the bc25 variant the replay says it played:

```
$ jq -r '.variants[]|"\(.name)\t\(.game_config.year)\t\(.game_config.gamesPerMatch)\t\(.game_config.num_agents)"' coworld_manifest_template.json
Battlecode 2026 — Uneasy Alliances (2 seats)	bc26	3	2
Battlecode 2020 — Soup (2 seats)	bc20	3	2
Battlecode 2021 — Campaign (2 seats)	bc21	3	2
Battlecode 2024 — Breadwars (2 seats)	bc24	3	2
Battlecode 2025 — Chromatic Conflict (2 seats)	bc25	3	2
```

**Champion seats did the thing the game is about — non-scripted, non-trivial, zero fallbacks.**

`jq -r '.seats[]|[.slot,.alias,.name,.policy,.chassis,.motto,(.sheet|tostring),(.fallback|tostring)]|@tsv'`:

```
0	Clan Ash	daveey	llm	spaark	Paint the map. Towers mine forever. Territory wi	{"opening":"paint_eco","unit_mix":{"soldier":70,"mopper":15,"splasher":15},"srp_priority":70,"tower_type_order":["paint","money","defense"],"ruin_claim_radius":16,"defense_tower_chokes":"late","paint_reserve_floor":50,"mop_enemy_paint":25,"splash_targets":"territory","upgrade_policy":"paint_first"}	null
1	Clan Basil	daveey-1	llm	spaark	Paint towers, break towers, dominate.	{"opening":"tower_rush","unit_mix":{"soldier":35,"mopper":20,"splasher":45},"srp_priority":15,"tower_type_order":["money","defense","paint"],"ruin_claim_radius":7,"defense_tower_chokes":"early","paint_reserve_floor":20,"mop_enemy_paint":35,"splash_targets":"towers","upgrade_policy":"defense_first"}	null
```

Both seats are `policy: "llm"`; both sheets differ from the schema defaults
(`{"opening":"balanced","unit_mix":{"soldier":60,"mopper":25,"splasher":15},"srp_priority":35,
"tower_type_order":["money","paint","defense"],"ruin_claim_radius":10,…}`, quoted from the
`sheet_schema` embedded in the replay's own prompt) and differ from **each other** — coverage
opens `paint_eco` with 70 % soldiers and `srp_priority: 70`, siege opens `tower_rush` with 45 %
splashers and `srp_priority: 15`. `fallback` is `null` on both seats. The two sheets are also
*different from round 1's* (round 1 coverage had `srp_priority: 75`, siege `ruin_claim_radius: 6`,
different mottos) — these are freshly generated decisions, not a canned reply.

Decision / fallback counts (this game's "decision" is the one-shot doctrine turn per seat, per
`design.md` §Match shape: *"There is exactly one decision turn per episode"*):

```
$ jq -c '.events[]|select(.kind|test("doctrine"))' /tmp/ep.replay
{"kind":"doctrine_requested","ms":0,"slot":0,"attempt":1,"deadline_ms":20000}
{"kind":"doctrine_requested","ms":0,"slot":1,"attempt":1,"deadline_ms":20000}
{"kind":"doctrine_received","ms":5612,"slot":0,"attempt":1,"latency_ms":5612,"defaults_applied":0,"unknown_fields":0}
{"kind":"doctrine_received","ms":5612,"slot":1,"attempt":1,"latency_ms":5612,"defaults_applied":0,"unknown_fields":0}

$ jq -r '[.events[]|select(.kind|test("fallback"))]|length' /tmp/ep.replay
0
$ jq -r '[.seats[]|select(.fallback!=null)]|length' /tmp/ep.replay
0
```

2 of 2 decisions answered on attempt 1, `defaults_applied: 0`, `unknown_fields: 0`, **0 fallbacks**
(the design's fallback path emits a `doctrine_fallback` event and sets `seats[].fallback`; neither
is present).

Event stream — 113 events, all game-substance kinds:

```
$ jq -r '[.events[].kind]|group_by(.)|map("\(.[0])\t\(length)")|.[]' /tmp/ep.replay
coverage	10
doctrine_received	2
doctrine_requested	2
episode_end	1
episode_start	1
first_action	4
game_end	2
game_start	2
srp_active	12
srp_broken	5
srp_completed	16
starved	3
tower_built	22
tower_lost	3
tower_upgraded	28
```

Result:

```
$ jq -c '{reason:.result.reason,names:.result.names,scores:.result.scores,wins:.result.wins,points:.result.points,games:[.result.games[]|{map,end_reason,winner,rounds_played,squares_painted,towers_alive,coverage_permille}]}' /tmp/ep.replay
{"reason":"complete","names":["daveey","daveey-1"],"scores":[465.5,33.5],"wins":[2,0],"points":[[55,76],[44,23]],"games":[{"map":"DefaultLarge","end_reason":"more_squares_painted","winner":0,"rounds_played":2000,"squares_painted":[343,317],"towers_alive":[6,6],"coverage_permille":[232,215]},{"map":"leavemealone","end_reason":"more_squares_painted","winner":0,"rounds_played":2000,"squares_painted":[560,178],"towers_alive":[9,6],"coverage_permille":[411,130]}]}
```

**Two games, not three — this is the design's own best-of-three, and it is documented in code, not
inferred.** `plan.maps` lists three maps; `daveey` swept the first two, which clinches a
best-of-three, and the match loop stops:

```
$ gh api repos/Metta-AI/cogame-battlecode/contents/src/battlecode/match.nim … | sed -n '80p;301,318p'
proc winsNeeded*(games: int): int = games div 2 + 1
...
proc playMatch*(config: GameConfig, plan: var MatchPlan,
                events: var seq[MatchEvent]): (seq[GameOutcome], EpisodeReason) =
  ## Plays the planned games in order, stopping early once a seat has taken
  ## the majority. Returns the games that FINISHED plus the episode reason.
  var outcomes: seq[GameOutcome]
  var wins: array[2, int]
  var reason = epComplete
  let need = winsNeeded(plan.maps.len)
  ...
  for g in 0 ..< plan.maps.len:
    if wins[0] >= need or wins[1] >= need:
      break
```

`winsNeeded(3) = 2`; `wins == [2,0]` at the top of game 3, so the loop breaks with
`reason = epComplete`. This is **not** the `epDeadline` branch (which sets `reason = epDeadline`
when `matchBudgetSeconds` is exhausted) — no deadline exception is being claimed here.

Status: **TRUE** — valid strict-UTF-8 JSON; `protocol == "cogame.battlecode.v1"` matching the
manifest's protocol document; `.result.reason == "complete"`; both champion seats made real,
distinct, non-default LLM decisions with **0 fallbacks out of 2 decisions**; the episode played
2000 rounds on each of two real bc25 maps and produced a decided result.

---

## 5. Hosted game log is clean

```
GET $BASE/episode-requests/ereq_30eabb74-86fe-4ca7-89c8-549e1fb8d280/artifacts/logs
    -H Authorization: Bearer $SOFTMAX_TOKEN  -H User-Agent: coworld-builder/1.0
    -H X-Use-Elevated-Privileges: true
```
```
HTTP 200 bytes=1725
```

The body is python `b'…'` byte-string reprs under `===== container: … =====` headers; decoded per
repr with `ast.literal_eval` before grepping (26 decoded lines). **Full decoded body, verbatim:**

```
===== container: coworld-init-config =====

===== container: bedrock-sidecar =====
2026-09-08 05:37:53,665 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1","has_role_arn":true,"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar","episode_request_id":"30eabb74-86fe-4ca7-89c8-549e1fb8d280","job_request_id":"a0418bda-3045-4e27-94b1-ed27f2143faf","role":"game","slot":"game","image_digest":"sha256:b3f0e0e5850454e7d8e862b1da756c42bf9378e72c64bd9bfde1fcfbd5a32a62"}
[2026-09-08 05:37:53 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-09-08 05:37:53,955 INFO hypercorn.error Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-09-08 05:38:00,627 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-08 05:38:03,779 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"

===== container: game =====
battlecode config: year=bc25 pool=mixed seed=10999294 games=3 maxRounds=2000 num_agents=2 matchBudget=340s
battlecode: listening on 0.0.0.0:8080
battlecode: waiting for seats
battlecode: refused a seat-0 connection: seat 0 was given the wrong connection token
battlecode: a spectator joined /global
battlecode: seat 0 connected
battlecode: seat 0 registered kind=llm label=coverage
battlecode: seat 1 connected
battlecode: seat 1 registered kind=llm label=siege
battlecode: doctrine
battlecode llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
battlecode: match
battlecode: settled: complete
battlecode: reason=complete games=2 scores=[465.5, 33.5] sim=2.926s wall=13.645s

===== container: worker =====
```

```
$ grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs2.txt || echo CLEAN
CLEAN
```

Status: **TRUE** — zero matches for `falling back`, `LLM provider is unavailable`,
`cut off at max_tokens`, `rejected`. Both LLM calls returned `HTTP/1.1 200 OK`; no Bedrock-capacity
exception is being claimed. Round 1's log was fetched the same way at 05:26Z and was also `CLEAN`.

*Observation, not a failure:* the line `battlecode: refused a seat-0 connection: seat 0 was given
the wrong connection token` is the seat-token guard doing its job on a stray connect (the real
seat 0 connects on the next line and registers `kind=llm label=coverage`). It contains none of the
four forbidden strings and it did not affect the episode. Worth a phase-30 note only.

---

## 6. The public page uses the static replay path

**Deviation recorded (briefed by the coordinator, and confirmed here):** this coworld is the
multi-year `battlecode` and the run's league is the **bc25** league, reached at the short-name
route `https://softmax.com/battlecode/bc25`. `https://softmax.com/battlecode` opens the coworld's
*default* league (bc26), which is **not** this run's — proven below.

**Source (a) — raw HTML grep of the bc25 page. Attempted first, found nothing (client-rendered).**

```
$ curl -sS "https://softmax.com/battlecode/bc25" -o bc25page.html -w 'HTTP %{http_code} bytes=%{size_download}\n'
HTTP 200 bytes=901302
$ grep -o '<iframe[^>]*src="[^"]*"' bc25page.html
(no output — NO IFRAME IN RAW HTML)
```

Per `prompts/60-verify.md` check 6 and `playbooks/observatory-api.md` §Featured match, an empty
grep here is *unknown*, not a false negative — the iframe exists only after JS runs.

**Source (b) — the coworld detail API. Fetched, and it is `null` platform-wide, as the playbook
records; so it is not the evidence either.**

```
$ curl -sS "$BASE/coworlds?limit=200" -H Authorization… -H User-Agent… \
  | jq -r '…|select(.name=="battlecode")|{id,canonical,replay_viewer,featured_match}'
{ "id": "cow_e58e703d-3d34-4d27-b8eb-4464a6209170", "name": "battlecode", "canonical": true,
  "replay_viewer": null, "featured_match": null }
```

**Source (c) — the page's own SSR payload, `state.playlist[0]`. THIS IS THE SOURCE USED for the
featured match**, per `playbooks/observatory-api.md` §Featured match ("the featured match is
server-rendered into the page's SSR payload at `state.playlist[0]`"). Fetched fresh
2026-09-08T05:42:2xZ, unescaped and pasted:

```json
"leagueId":"league_7edecd14-58d2-4a23-aadb-491577a60935",
"playlist":[{"episodeId":"b019825b-6076-46b0-ae24-b2f2f923e0b7",
 "coworldId":"cow_e58e703d-3d34-4d27-b8eb-4464a6209170",
 "coworldName":"battlecode","coworldVersion":"0.5.0",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/a0418bda-3045-4e27-94b1-ed27f2143faf.replay",
 "finishedAt":"2026-09-08T05:38:32.769980Z","roundNumber":2,"episodeNumber":1,
 "code":"battlecode.r2.e1",
 "matchup":{"divisionId":"div_a5c7f237-a2e2-484a-9e97-f1fd9b8dfd97","divisionName":"Competition",…
```

```
$ grep -o 'softmax-public.s3.amazonaws.com/replays/[a-f0-9-]*\.replay' bc25page.html | sort -u
softmax-public.s3.amazonaws.com/replays/a0418bda-3045-4e27-94b1-ed27f2143faf.replay
```

The bc25 page's SSR `leagueId` is **this run's league**, and the only replay it references is
**this run's round-2 replay** — the same `replay_url` check 3 read off
`ereq_30eabb74-86fe-4ca7-89c8-549e1fb8d280`. So the featured match is present and belongs to the
bc25 league; the `featured_match: null` in (b) is the documented platform-wide behaviour, not
an absence here.

*Cross-check that `/battlecode` is a different league (the deviation, proven):*

```json
"leagueId":"league_24414477-8c64-4a71-b643-f8a1ef148e29",
"playlist":[{"episodeId":"6ee6f84f-cb6d-4e21-8cc0-df24981e80a3",
 "coworldId":"cow_e58e703d-3d34-4d27-b8eb-4464a6209170","coworldName":"battlecode",
 "coworldVersion":"0.5.0",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/5512eb22-c3c8-4d91-92b3-1e4ff8bbd629.replay",…
```

**Source (d) — the iframe `src` itself, from the call the page's JS makes.** This is the call
whose answer becomes the `src`:

```
POST $BASE/coworlds/replays/session
  -H Authorization: Bearer $SOFTMAX_TOKEN  -H User-Agent: coworld-builder/1.0
  -H content-type: application/json
  -d '{"coworld_id":"cow_e58e703d-3d34-4d27-b8eb-4464a6209170",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/a0418bda-3045-4e27-94b1-ed27f2143faf.replay"}'
```
fetched 2026-09-08T05:42:5xZ:

```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e58e703d-3d34-4d27-b8eb-4464a6209170/sha256%3A28e952e1db3f2d7c479160ac522a91f420b0dd2c5fdf2b83d44ade8d7bdce7fe/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fa0418bda-3045-4e27-94b1-ed27f2143faf.replay","ready":true}
```
```
HTTP 200
```

Status: **TRUE** — sources used: **(c)** the bc25 page's SSR `state.playlist[0]` for the featured
match, and **(d)** `POST /coworlds/replays/session` for the iframe `src`. (a) found no iframe
because the page is client-rendered; (b) is `null` platform-wide. The `src` is
`…/v2/coworlds/replays/static/cow_e58e703d-3d34-4d27-b8eb-4464a6209170/sha256%3A28e952e1…/index.html?v=2#replay=<s3 url>`
— the **static** route (`<sha>` is the coworld's `manifest_sha`
`sha256:28e952e1db3f2d7c479160ac522a91f420b0dd2c5fdf2b83d44ade8d7bdce7fe`, exactly
`STATE.coworld.manifest_sha`), with `ready: true`. It is **not** a `/client/replay` pod URL. The
replay is delivered as the URL-encoded **fragment** `#replay=` rather than `?replay=` — the
documented post-2026-08-28 form of the same static route
(`playbooks/observatory-api.md` §Featured match), and it is what check 8 below actually loaded and
rendered.

---

## 7. Certification declared the static replay bundle

Source read: **the committed `runs/2026-09-07-battlecode-2025/release-result.json`** — the copy
phase 40 downloaded from release run `34189611273` and committed. It was already present; no
re-download from `gh run download` was needed, and `/tmp` was not consulted.

```
$ jq -r '.certify.replay_liveness' runs/2026-09-07-battlecode-2025/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)

$ jq -r '.certify | keys' runs/2026-09-07-battlecode-2025/release-result.json
[
  "ok",
  "output_tail",
  "replay_liveness"
]
```

Status: **TRUE** — the string contains `Replay liveness: skipped (static replay bundle declared`
verbatim.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged

**(a) Dispatch.** `viewer-check.yml` in `Metta-AI/coworld-builder` was dispatched **this run**
against the exact iframe `src` from check 6, with the bc25 timings the design pins
(`design.md`: *"check-8 dispatch settle=20000 soak=15 pinned"*, viewer smoke at `--timeout 120`):

```
$ gh workflow run viewer-check.yml -R Metta-AI/coworld-builder \
    -f url='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e58e703d-3d34-4d27-b8eb-4464a6209170/sha256%3A28e952e1db3f2d7c479160ac522a91f420b0dd2c5fdf2b83d44ade8d7bdce7fe/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fa0418bda-3045-4e27-94b1-ed27f2143faf.replay' \
    -f timeout=120 -f settle=20000 -f soak=15
DISPATCHED  2026-09-08T05:43:04Z
```

The new run was found by sorting on `createdAt`, not by taking "the latest" blind:

```
$ gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
  | jq -r 'sort_by(.createdAt)|reverse|.[0:2][]|"\(.databaseId)\t\(.createdAt)\t\(.status)"'
34191692693	2026-09-08T05:43:04Z	in_progress
34190741103	2026-09-08T05:28:17Z	completed
```

`34191692693` is the run whose `createdAt` equals the dispatch instant.

```
$ gh run view 34191692693 -R Metta-AI/coworld-builder --json status,conclusion
completed success
$ gh run download 34191692693 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-09-07-battlecode-2025/viewer-check
```

Committed at `runs/2026-09-07-battlecode-2025/viewer-check/` — `viewer-smoke.json` (1994 B),
`viewer-smoke.png` (446264 B), `smoke-stdout.txt` (772 B), `smoke-stderr.txt` (0 B, empty).

*(An earlier viewer-check run this same session, `34190741103` dispatched 05:28:17Z against
round 1's replay `e78a10b9-…`, is kept at `runs/2026-09-07-battlecode-2025/viewer-check-r1/`. It
also returned `loaded: true` with three differing clocks. Item 8 is judged on **34191692693**,
which loaded the replay that check 6 actually reads off the live page.)*

**(b) The readouts.**

`jq -c '{loaded, ms, clock, scorebug, feed_lines}' viewer-check/viewer-smoke.json` — verbatim:

```json
{"loaded":true,"ms":1901,"clock":"2:32 GAME 1 OF 2 — DEFAULTLARGE doctrines","scorebug":"CLAN ASH daveey · Paint the map. Towers mine forever. Territory wi 54 2:32 GAME 1 OF 2 — DEFAULTLARGE doctrines CLAN BASIL daveey-1 · Paint towers, break towers, dominate. 45","feed_lines":8}
```

`jq -c '.signals' viewer-check/viewer-smoke.json`:

```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["ready"],"bridge_ready":true,"bridge_error":[]}
```

`jq -r '.failure // "no failure"'` → `no failure`.  `console_tail` → `["[bridge] ready"]`.
`smoke-stderr.txt` is empty; `soak.page_errors` is `[]`.

**The three clock readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):**

| scrub | clock readout | settle |
|---|---|---|
| 0 % | `2:32 GAME 1 OF 2 — DEFAULTLARGE doctrines` | — |
| 50 % | `1:23 GAME 2 OF 2 — LEAVEMEALONE doctrines` | 1004 ms |
| 100 % | `FINAL MATCH OVER doctrines` | 1506 ms |

Three readouts, **all three different**, and they name the two maps the replay JSON says were
played (`DefaultLarge`, `leavemealone`) in the right order.

Unattended playback also advanced on its own (15-second soak, from `smoke-stdout.txt`):

```
soak: 15s of playback kept advancing ("round 2 / 2000" -> "round 314 / 2000" -> "round 362 / 2000")
canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
```

**Item 8 gate: `loaded: true` ✓ (via `data-replay-loaded="true"` *and* the `coworld-replay`
bridge's `ready`), and the three clock readouts differ ✓. Status: TRUE.**

**(c) The replay JSON the viewer was asked to draw** — ordered excerpts from `/tmp/ep.replay`
(check 4's bytes), so the picture and the record can be reconciled.

Early (`game round kind alias detail`):

```
-	-	episode_start	-	
-	-	doctrine_requested	-	
-	-	doctrine_requested	-	
-	-	doctrine_received	-	
-	-	doctrine_received	-	
0	0	game_start	-	
0	1	first_action	Clan Basil	
0	1	first_action	Clan Ash	
0	15	tower_built	Clan Basil	money
0	37	tower_built	Clan Ash	paint
0	38	coverage	Clan Basil	100
0	45	coverage	Clan Ash	100
0	56	tower_built	Clan Basil	paint
0	80	tower_lost	Clan Ash	paint
0	106	tower_built	Clan Basil	paint
0	112	tower_built	Clan Ash	money
```

Middle:

```
0	992	srp_active	Clan Basil	
0	993	coverage	Clan Basil	200
0	995	tower_upgraded	Clan Ash	money
0	996	tower_upgraded	Clan Ash	money
0	1013	srp_active	Clan Basil	
0	1014	srp_completed	Clan Basil	
0	1015	srp_broken	Clan Basil	
0	1016	tower_built	Clan Basil	defense
0	1803	tower_lost	Clan Ash	defense
0	1807	tower_built	Clan Ash	defense
0	1808	tower_upgraded	Clan Ash	defense
0	2000	game_end	-	Clan Ash
```

Late:

```
1	1084	tower_upgraded	Clan Ash	paint
1	1136	tower_upgraded	Clan Ash	paint
1	1258	tower_upgraded	Clan Ash	money
1	1320	tower_upgraded	Clan Ash	paint
1	1389	tower_upgraded	Clan Ash	money
1	1812	starved	Clan Ash	5
1	1823	starved	Clan Ash	5
1	2000	game_end	-	Clan Ash
-	-	episode_end	-	complete
```

```
$ jq -r '.result' /tmp/ep.replay | jq -c '{reason,names,scores,wins,points}'
{"reason":"complete","names":["daveey","daveey-1"],"scores":[465.5,33.5],"wins":[2,0],"points":[[55,76],[44,23]]}
```

### Spectator judgment

**It is legible, and it shows this game.** The screenshot (`viewer-check/viewer-smoke.png`, taken
at the 100 % scrub position, so it is the end-of-match state) is a full broadcast frame, not a
blank canvas and not a loading shell:

- **Top strip / scorebug.** A momentum bar reading `ASH 41%` … `13% BASIL`, and beside it
  `560 / 955 to win · 626 bare` — the live territory count. Under it, both clans named with their
  real players and their *own* mottoes: `CLAN ASH — daveey · "Paint the map. Towers mine forever.
  Territory wi…"` with a live points number **76**, and `CLAN BASIL — daveey-1 · "Paint towers,
  break towers, dominate."` with **23**. Those two numbers are exactly the replay's
  `result.points[…][1] = [76, 23]` for game 2. A spectator can read who is winning and by how much
  in one glance.
- **The board.** The dark-olive painted map is visible behind the endcard overlay, with ruin and
  tower glyphs scattered across it — not an empty arena.
- **The endcard.** `CLAN ASH — DAVEEY`, `THE ROUND LIMIT RAN OUT AND THE POINTS DECIDED IT`
  (correct: both games ended `more_squares_painted` at round 2000), `score 465.5 — 33.5` matching
  `result.scores` exactly, then the two **doctrine cards** rendering each LLM's sheet back as
  English prose — "opens on paint economy, builds 70 % soldiers, 15 % moppers, 15 % splashers,
  banks 70 % of its chips for resource patterns, builds paint, then money, then defense towers,
  claims ruins within 16 tiles…" for Ash, and "rushes towers, builds 35 % soldiers, 20 % moppers,
  45 % splashers, banks 15 % of its chips for resource patterns, builds money, then defense, then
  paint towers, claims ruins within 7 tiles…" for Basil. Every one of those numbers is the seat's
  sheet from check 4. **This is the game being about something**: two different strategies, stated,
  then played out.
- **The stat block** under the cards: `Clan Ash — painted 1331, mopped 151, overpainted 103 · peak
  42%, final 41% · towers 7 built / 15 upgraded / 0 lost · chips 262210 earned / 212700 spent ·
  robots 494 built, 441 lost, 1331 robot-rounds at zero paint · SRP 4 completed / 2 active /
  2 broken`, and the matching Basil line. It explains *why* Ash won.
- **The feed** (right column, 8 lines): `Game 2 — Clan Ash wins (more squares painted)`,
  `Clan Ash runs dry: 5 robots end the round at zero paint — game 2, round 1823`, the same at
  `round 1812`, `Clan Ash upgrades a money tower to level 3 — game 2, round 1389`, `…paint tower
  to level 3 — game 2, round 1320`, `…round 1258`, `…round 1136`, `…round 1084`. Those are, line
  for line and round number for round number, the **late excerpt of the replay JSON above**. The
  picture and the record agree.
- **The transport strip** across the bottom: restart / step-back / play / `+25` / step / loop /
  fast-forward buttons, a `spoilers` toggle, `round 2000 / 2000`, speed buttons `1× 2× 3× 4× 8×
  16×`, and a full-width scrubber whose tick marks are the event momentum graph.

**Does it look like the starter's chrome?** Yes — this is the same broadcast shell as
paintbot/raid/hive: the same transport strip, the same scrubber-with-momentum-graph, the same
scorebug band and the same endcard layout. It is not a rewrite that merely shares ids
(the cogame-gridlock failure). The bc25 year block is an addition to
`client/replay_broadcast.html`, and the year-specific beats (tower built/upgraded/lost, SRP
active/completed/broken, robots starving, coverage) all render with bc25 vocabulary.

**Two legibility findings for the coordinator (neither makes item 8 false — the viewer loads,
advances, and reads correctly):**

1. **Wrong-year captions on the endcard.** The `score …` line reads
   `the alliance held / score 465.5 — 33.5 · kings built 0/0 · cheese delivered 0/0 · cats damaged
   0/0`. bc25 has no rat kings, no cheese and no cats — those are **bc26** ("Uneasy Alliances")
   nouns. `client/replay_broadcast.html` emits them unconditionally for every year:
   ```
   4983:    var betrayal = 'the alliance held';
   4994:      ' · kings built ' + (e[0].kings_built || 0) + '/' + (e[1].kings_built || 0) +
   4995:      ' · cheese delivered ' + (e[0].cheese || 0) + '/' + (e[1].cheese || 0) +
   4996:      ' · cats damaged ' + (e[0].cat_damage || 0) + '/' + (e[1].cat_damage || 0);
   ```
   On a bc25 replay these degrade to three `0/0` counters and a sentence about an alliance that
   does not exist in this year. A phase-30 item-14 legibility item: the `ec-how` line should be
   year-switched (bc25 would want e.g. painted / towers / SRP), or suppressed off-year.
2. **Doctrine cards clip their last line.** Both cards end mid-sentence at the card's bottom edge
   ("moppers spend 25 % of their turns erasing enemy paint," / "splashers aim at towers,") with no
   ellipsis and no scroll affordance. The prose is generated at a length the fixed-height card
   cannot hold. (Note `canvas_text` reports `0 ellipsized` — this is DOM text in the endcard, not
   canvas text, so the smoke test's clipping detector does not see it.)

Neither is a rendering failure and neither touches the check-8 gate.

