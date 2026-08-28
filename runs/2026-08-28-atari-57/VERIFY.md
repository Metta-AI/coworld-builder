# VERIFY — atari-57   (2026-08-28T22:20:04Z)

Verdict: **all-true** (8/8)

Run: `2026-08-28-atari-57` · coworld `cow_4b06234f-97d8-4b65-8553-e2f967e89d8c` v0.1.0
League `league_942b4588-00ce-4b37-b5ae-9f1254d97db4` · division `div_6a44a425-829a-41ae-926f-a0139e8b95d3`

All calls used `BASE=https://softmax.com/api/observatory/v2` with headers
`Authorization: Bearer $SOFTMAX_TOKEN` and `User-Agent: coworld-builder/1.0`
(the elevated read on check 5 additionally sent `X-Use-Elevated-Privileges: true`).
Header values are never printed here.

Wall-clock: verifier started 2026-08-28T21:56:14Z, all evidence fetched by 22:20:04Z —
24 minutes, inside the 75-minute bound. Polls at 21:56, 22:01, 22:06, 22:11, 22:16Z.

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

```
GET $BASE/rounds?league_id=league_942b4588-00ce-4b37-b5ae-9f1254d97db4&limit=20
(fetched 2026-08-28T22:16:34Z)
```

```json
[
  {
    "id": "round_4441a16c-dcbf-49bf-84e8-634486759702",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T22:09:12.803682Z",
    "completed_at": "2026-08-28T22:14:55.040333Z",
    "entrant_attributions": [
      {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
       "policy_version_id": "e4a70dfc-8965-4bef-8bd0-07e3cbc1f4fc",
       "league_policy_membership_id": "lpm_eb845dce-cde6-44e6-be2a-2ab1c487db1f"},
      {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
       "policy_version_id": "efaec535-80ba-4a9c-bf0b-cecefe66d47d",
       "league_policy_membership_id": "lpm_4546dd7a-cfea-4689-90cc-5f16d73ef56d"}
    ]
  },
  {
    "id": "round_ed18a4d8-9494-46c6-86f4-185706ff994a",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T21:54:12.236771Z",
    "completed_at": "2026-08-28T21:59:28.533623Z",
    "entrant_attributions": [
      {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
       "policy_version_id": "e4a70dfc-8965-4bef-8bd0-07e3cbc1f4fc",
       "league_policy_membership_id": "lpm_eb845dce-cde6-44e6-be2a-2ab1c487db1f"},
      {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
       "policy_version_id": "efaec535-80ba-4a9c-bf0b-cecefe66d47d",
       "league_policy_membership_id": "lpm_4546dd7a-cfea-4689-90cc-5f16d73ef56d"}
    ]
  },
  {
    "id": "round_f754b121-8cee-471d-8bc0-d5cd3ac034e9",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-28T21:54:01.841774Z",
    "completed_at": "2026-08-28T21:54:02.145959Z",
    "entrant_attributions": [
      {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
       "policy_version_id": "e4a70dfc-8965-4bef-8bd0-07e3cbc1f4fc",
       "league_policy_membership_id": "lpm_eb845dce-cde6-44e6-be2a-2ab1c487db1f"},
      {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
       "policy_version_id": "efaec535-80ba-4a9c-bf0b-cecefe66d47d",
       "league_policy_membership_id": "lpm_4546dd7a-cfea-4689-90cc-5f16d73ef56d"}
    ]
  }
]
```

```
jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
2
```

**Failed round's `error`, verbatim (round 1, does NOT count):**

> `Temporal RoundWorkflow failed before settling the round.`

Per `playbooks/observatory-api.md` §6 this is exactly the message a `trigger-round` issued
before any filler exists produces; round 1 raced the filler registration during phase 50.

**Fillers were set before both counted rounds.** Registered list, fetched fresh:

```
GET $BASE/leagues/$L/filler-policies   (headers: Authorization, User-Agent, X-Use-Elevated-Privileges)
(fetched 2026-08-28T22:19Z)
```
```json
{"filler_policy_versions": [
  {"policy_version_id": "44a28876-eba6-4ec8-bcf6-6cfe647d9fc7", "policy_name": "atari-57-arcader",
   "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"},
  {"policy_version_id": "d0712eac-62b0-4f34-ad30-b562afebc3a3", "policy_name": "atari-57-hoover",
   "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"}
]}
```

Direct proof that both counted rounds were seated *after* the fillers existed — every episode
in rounds 2 and 3 seats filler policies with `is_filler: true` (round 1 never seated anything):

```
GET $BASE/episode-requests/ereq_54a595a6-364c-42f6-a83f-edb6a202ee85     # round 2
{"status":"completed",
 "replay_url":"https://softmax-public.s3.amazonaws.com/replays/1d6539ba-0ad8-4f77-849d-a699315074de.replay",
 "participants":[{"position":0,"policy_name":"atari-57-highroller","player_name":"daveey","is_filler":false},
                 {"position":1,"policy_name":"atari-57-onecredit","player_name":"daveey-1","is_filler":false},
                 {"position":2,"policy_name":"atari-57-hoover","player_name":"daveey","is_filler":true},
                 {"position":3,"policy_name":"atari-57-arcader","player_name":"daveey","is_filler":true}]}
```
(Round 3's equivalent is pasted in full under check 3; it likewise seats two `is_filler: true`
policies.)

Status: **TRUE** — rounds **2** and **3** completed at `2026-08-28T21:59:28.533623Z` and
`2026-08-28T22:14:55.040333Z`, both with the fillers registered and actually seated. Round 1
`failed` with the Temporal message quoted above and is excluded.

---

## 2. Both champions ranked, fillers absent/Baseline — **TRUE**

```
GET $BASE/divisions/div_6a44a425-829a-41ae-926f-a0139e8b95d3/leaderboard
(fetched 2026-08-28T22:16:40Z; bare JSON list, not {entries:…})
```

```json
[
  {"rank": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
   "score": 1030.5304984710244, "score_label": "MMR", "score_value_type": "integer",
   "rounds_played": 2, "episode_wins": 2.0, "episodes_played": null, "win_rate": 1.0,
   "policy_label": "atari-57-highroller:v1", "recent_rounds": null},
  {"rank": 2, "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
   "score": 969.4695015289755, "score_label": "MMR", "score_value_type": "integer",
   "rounds_played": 2, "episode_wins": 0.0, "episodes_played": null, "win_rate": 0.0,
   "policy_label": "atari-57-onecredit:v1", "recent_rounds": null}
]
```

```
jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
1	daveey	atari-57-highroller:v1	1030.5304984710244	2	2.0
2	daveey-1	atari-57-onecredit:v1	969.4695015289755	2	0.0
```

Status: **TRUE** — `daveey` (rank 1, `rounds_played` 2) and `daveey-1` (rank 2,
`rounds_played` 2) both present. Exactly two rows: neither filler
(`atari-57-arcader:v1`, `atari-57-hoover:v1`) appears on the leaderboard at all.

---

## 3. Latest completed round's episode request completed with a replay — **TRUE**

Latest completed round = **round 3**, `round_4441a16c-dcbf-49bf-84e8-634486759702`.

```
GET $BASE/rounds/round_4441a16c-dcbf-49bf-84e8-634486759702/episode-requests
(nested route — the flat ?round_id= route 405s per playbook §9)
[{"id":"ereq_c6f8d48c-980e-4f0e-9bb9-0725bee4b5f6","status":"completed"}]
```

```
GET $BASE/episode-requests/ereq_c6f8d48c-980e-4f0e-9bb9-0725bee4b5f6
(fetched 2026-08-28T22:16:47Z)
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/820b851b-5e44-4631-bb96-e5d0cebc6abd.replay",
  "participants": [
    {"position": 0, "kind": "policy", "policy_version_id": "e4a70dfc-8965-4bef-8bd0-07e3cbc1f4fc",
     "policy_id": "76c524b1-9606-43e8-869f-775e15cb6434", "policy_name": "atari-57-highroller",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
     "player_name": "daveey", "is_filler": false, "is_seed": false},
    {"position": 1, "kind": "policy", "policy_version_id": "efaec535-80ba-4a9c-bf0b-cecefe66d47d",
     "policy_id": "e22824d6-8d4e-4794-9f48-7638d260ef8c", "policy_name": "atari-57-onecredit",
     "version": 1, "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
     "player_name": "daveey-1", "is_filler": false, "is_seed": false},
    {"position": 2, "kind": "policy", "policy_version_id": "d0712eac-62b0-4f34-ad30-b562afebc3a3",
     "policy_id": "5ab34a2a-32cb-4b56-98e6-edf5689e2220", "policy_name": "atari-57-hoover",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
     "player_name": "daveey", "is_filler": true, "is_seed": false},
    {"position": 3, "kind": "policy", "policy_version_id": "d0712eac-62b0-4f34-ad30-b562afebc3a3",
     "policy_id": "5ab34a2a-32cb-4b56-98e6-edf5689e2220", "policy_name": "atari-57-hoover",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
     "player_name": "daveey", "is_filler": true, "is_seed": false}
  ],
  "participant_scores": [
    {"position": 0, "score": 38.4},
    {"position": 1, "score": 13.6},
    {"position": 2, "score": 13.3},
    {"position": 3, "score": 13.3}
  ]
}
```

Status: **TRUE** — `status == "completed"`, `replay_url` non-null, seats 0/1 are
`daveey` / `daveey-1` (`is_filler: false`), seats 2/3 are the filler `atari-57-hoover:v1`
(`is_filler: true`, rendered in-episode as `Baseline` / `Baseline (2)` — see the replay's
`names` array in check 4). Scores are non-degenerate and separate the two champions
(38.4 vs 13.6).

---

## 4. Replay bytes are valid and show the game — **TRUE**

```
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/820b851b-5e44-4631-bb96-e5d0cebc6abd.replay" \
     -o /tmp/ep.replay
http=200 bytes=73374
```
Saved to `runs/2026-08-28-atari-57/ep.replay` (73 374 B, under the 2 MB limit).

The artifact is the starter's **binary** `COWLDA57` container, not raw JSON — the first bytes are:

```
0000000   C   O   W   L   D   A   5   7 001  \0  \b  \0   a   t   a   r
0000020   i   -   5   7 001  \0   1   h 232   k   J 240 001  \0  \0   ;
0000040  \t   {   "   s   e   e   d   "   :   1   4   1   2   7   0   3
0000060   0   9   4   ,   "   n   u   m   _   a   g   e   n   t   s   "
0000100   :   4   ,   "   m   i   n   P   l   a   y   e   r   s   "   :   …
```

so `jq -e . /tmp/ep.replay` fails on byte 0 by construction. The repo declares this and ships
its own forensics reader for exactly this check —
`tools/replay_summary.py`, whose module docstring names phase 60 check 4 as its purpose:

> "The replay is the starter's BINARY format — the static wasm viewer parses exactly those
> bytes … This script is the repo's own forensics reader for it, and it is what phase 60
> substitutes for SPEC §Definition of done check 4".

That is the documented exception used here (design.md §Replay, L1286-1358; the repo's
`tests/test_replay.nim` re-sims and strict-UTF-8-parses for every end reason). Fetched fresh
this run from `Metta-AI/cogame-atari-57@main` and run against the S3 bytes:

```
python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json     # exit 0, no stderr
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok
```

```
jq -r '.protocol, .rom, .results.reason, .results.endRule' /tmp/ep.json
atari-57/v1
chomper
complete
full_time
```

`protocol` matches the manifest's declared protocol — `tools/replay_summary.py:25`
`PROTOCOL = "atari-57/v1"`, and the coworld detail API confirms the manifest hash the
viewer is served under (`sha256:81b1272c…`, check 6). `results.reason == "complete"` —
the design's declared-acceptable `deadline`/`wall_clock` fallback (design.md L595) was not
needed.

**Decisions are real LLM decisions, not fallbacks:**

```
jq -r '[.stances[]|select(.source=="llm")]|length'   ->  38
jq -r '.fallbacks'                                   ->  0
jq -r '[.stances[]]|length'                          ->  96
jq -c '[.stances[]|select(.source=="llm")|.mode]|unique'
["bank","clear","hunt","safe","strike"]
```

Per-seat breakdown (96 = 4 seats × 24 turns):

```json
[{"seat":0,"n":24,"by_source":{"llm":24}},
 {"seat":1,"n":24,"by_source":{"llm":14,"scripted":10}},
 {"seat":2,"n":24,"by_source":{"scripted":24}},
 {"seat":3,"n":24,"by_source":{"scripted":24}}]
```

Seats 0/1 are the champions, seats 2/3 the scripted fillers. Seat 1's 10 `scripted` turns are
not fallbacks: `results.fallbackTurns == [0,0,0,0]` and `results.ticksAlive[1] == 1834` of
3075 — lane 1's credit was spent at tick 1834 and the engine stops issuing LLM turns for a
dead lane (`llmTurns == [24,14,0,0]`). **Fallback count is 0 of 38 LLM decisions.**

```
jq '.results' /tmp/ep.json
{
  "names": ["daveey", "daveey-1", "Baseline", "Baseline (2)"],
  "aliases": ["RED", "BLUE", "GREEN", "YELLOW"],
  "lanes": [0, 1, 2, 3],
  "policyKinds": ["llm", "llm", "scripted", "scripted"],
  "scores": [38.4, 13.6, 13.3, 13.3],
  "win": [true, false, false, false],
  "placements": [1, 2, 3, 4],
  "rom": "chomper", "parScore": 2600,
  "points": [3740, 1360, 1330, 1330],
  "livesLeft": [1, 0, 0, 0],
  "deaths": [2, 3, 3, 3],
  "screensCleared": [1, 0, 0, 0],
  "bestChain": [2, 2, 3, 3],
  "shotsFired": [0, 0, 0, 0],
  "records": [true, false, false, false],
  "lastScoreTick": [3073, 1821, 846, 846],
  "ticksAlive": [3075, 1834, 853, 853],
  "llmTurns": [24, 14, 0, 0],
  "fallbackTurns": [0, 0, 0, 0],
  "finalTick": 3075,
  "reason": "complete", "endRule": "full_time",
  "seed": 1412703094
}
```

The two name spaces hold: in-episode aliases `RED/BLUE/GREEN/YELLOW`, real names only in
`names` / `aliases` on the results object; the fillers are `Baseline` / `Baseline (2)`.

**Champion seats doing the thing the game is about** (a raw LLM stance, verbatim, seat 0
turn 0):

```json
{"k":"stance","turn":0,"seat":0,"alias":"RED","lane":0,"source":"llm","latency_ms":4668,
 "note":"Turn 0: All hunters 72+ ticks away, no power pellets near. Nearest safe target is pellet cluster at (8,13) in 8 ticks worth 60 pts. Clear mode toward immediate ",
 "mode":"clear","zone":"centre","risk":0.5,"lead_ticks":14,"fire":"auto",
 "say":"Eating down the middle, building for chains."}
```
```json
{"k":"stance","turn":10,"seat":0,"alias":"RED","lane":0,"source":"llm","latency_ms":5250,
 "note":"Power active (75 ticks left), best_chain=2. Hunt nearest pellet cluster at ne (col 10, row 1, 40pts, 8 ticks). No threats. Strike mode to maximize chain.",
 "mode":"strike","zone":"ne","risk":0.85,"lead_ticks":10,"fire":"auto",
 "say":"Chasing the chain!"}
```
```json
{"k":"stance","turn":23,"seat":0,"alias":"RED","lane":0,"source":"llm","latency_ms":2592,
 "note":"Last life (1 remaining). Closest safe target: pellet cluster at (4,7) in 40 ticks. All threats >60 ticks away. Rule 7: halve risk to 0.125, cap at 0.35. Rule 6 ",
 "mode":"clear","zone":"nw","risk":0.175,"lead_ticks":14,"fire":"auto",
 "say":"Last life. Grinding safely in NW. Chain is over."}
```

Status: **TRUE** — strict-parser-clean JSON summary of the binary artifact, protocol
`atari-57/v1` matching the manifest, `reason: "complete"` / `endRule: "full_time"`,
38 LLM decisions with 0 fallbacks and five distinct modes exercised, and the champion seats
are visibly reasoning about pellets, power chains and hunter ETAs — which is what this
game is about.

---

## 5. Hosted game log is clean — **TRUE**

```
GET $BASE/episode-requests/ereq_c6f8d48c-980e-4f0e-9bb9-0725bee4b5f6/artifacts/logs
    (headers: Authorization, User-Agent, X-Use-Elevated-Privileges)
http=200 bytes=80214    (fetched 2026-08-28T22:17Z)
```

The body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it
was decoded per-repr with `ast.literal_eval` before grepping (playbook §10 — line greps
undercount otherwise). 4 containers, 79 993 decoded bytes:

```
===== container: coworld-init-config =====
===== container: bedrock-sidecar =====
===== container: game =====
===== container: worker =====
```

```
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.txt \
  || echo CLEAN
CLEAN
```

Throttling cross-check (the coins-2026-08-25 Bedrock-429 pattern the brief warned about) —
one substring hit, and it is a UUID, not a throttle:

```
grep -nE '429|[Tt]hrottl' /tmp/logs.txt
69: … bedrock_sidecar_complete {… "model":"global.anthropic.claude-haiku-4-5-20251001-v1:0",
    "operation":"InvokeModel","ok":true,"status_code":200,"latency_ms":2928.92…,
    "error_kind":null,"error_type":null,"message":null,
    "request_id":"cc5884e3-2f00-42fa-9498-654bdf80c429", …}
```

The `429` is inside `request_id`; the record itself is `ok:true, status_code:200`. **No
platform-wide-throttling exception was needed or claimed for this run.**

Decoded `game` container in full:

```
===== container: game =====
seed not pinned; randomized
atari-57 config: host=0.0.0.0 port=8080 seed=1412703094 rom=chomper num_agents=4 maxTicks=2880 minTicks=1440 turnTicks=120 wallClockBudgetSeconds=660
starting atari-57 on 0.0.0.0:8080
board render caches baked in 270 ms
atari-57 llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
player connected: Baseline (2)
player connected: Baseline
player connected: daveey
player connected: daveey-1
cabinet ready: 4 lanes, rom chomper
seat 3 registered: kind=scripted baseline=hoover
seat 2 registered: kind=scripted baseline=hoover
seat 1 registered: kind=llm baseline=arcader
seat 0 registered: kind=llm baseline=arcader
Dropped message to disconnected client
cabinet: credit inserted — rom chomper, seed 1412703094
cabinet: credit spent — complete/full_time at tick 3075
Replay written: /tmp/atari-57-replay-1.replay (73374 bytes)
Events written: /coworld/events.json (547 events)
results: {"names":["daveey","daveey-1","Baseline","Baseline (2)"], … "reason":"complete","endRule":"full_time","seed":1412703094}
```

Status: **TRUE** — grep returns `CLEAN`; the log shows 4 seats connecting, 2 LLM + 2 scripted
registering, and a normal `complete/full_time` shutdown at tick 3075.

---

## 6. The public page uses the static replay path — **TRUE**

**Source (a) — raw HTML grep. Not evidence, recorded for completeness:**

```
curl -sS "https://softmax.com/atari-57" | grep -o '<iframe[^>]*src="[^"]*"'
http=200 bytes=757878
NO IFRAME IN RAW HTML (client-rendered)
```

As the playbook records (§Featured match, lighthouse 2026-08-22), the page is client-rendered
for the iframe and this grep finds nothing for any coworld. Treated as *unknown*, not false.

**Source (b) — featured match, from the page's own SSR payload at `state.playlist[0]`** (this
is where the featured match is server-rendered; `/coworlds`' `featured_match` is `null`
platform-wide and is not evidence). Excerpt from the fetched HTML, un-escaped:

```json
"state":{"leagueId":"league_942b4588-00ce-4b37-b5ae-9f1254d97db4",
 "playlist":[{"episodeId":"4e814b9f-ff89-4a0d-bba2-20c77edd777a",
   "coworldId":"cow_4b06234f-97d8-4b65-8553-e2f967e89d8c",
   "coworldName":"atari-57","coworldVersion":"0.1.0",
   "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/820b851b-5e44-4631-bb96-e5d0cebc6abd.replay",
   "finishedAt":"2026-08-28T22:14:54.164993Z","roundNumber":3,"episodeNumber":1,
   "code":"atari-57.r3.e1",
   "matchup":{"divisionId":"div_6a44a425-829a-41ae-926f-a0139e8b95d3","divisionName":"Competition",
     "first":{"rank":1,"player_name":"daveey","score":1030.5304984710244,
              "rounds_played":2,"episode_wins":2,"win_rate":1,
              "policy_label":"atari-57-highroller:v1"},
     "second":{"rank":2,"player_id":"ply_ba…
 …"divisionName":"Competition","divisionCount":1,"playerCount":2,
 "newestCompletedAt":"2026-08-28T22:14:55.040333Z",
 "firstPlace":{"current":{"player_name":"daveey","rounds_held":2,"score":1030.5304984710244,
   "second_player_name":"daveey-1","gap_to_second":61.06099694204897, …
```

A featured match **is present** — `atari-57.r3.e1`, round 3, and its `replayUrl` is byte-for-byte
the `replay_url` from check 3.

**Source (c) — the iframe `src`, from the call the page's JS makes.** This is the source used
for the check-6 verdict and for the check-8 dispatch:

```
POST $BASE/coworlds/replays/session
     -d '{"coworld_id":"cow_4b06234f-97d8-4b65-8553-e2f967e89d8c",
          "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/820b851b-5e44-4631-bb96-e5d0cebc6abd.replay"}'
(fetched 2026-08-28T22:18Z)
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_4b06234f-97d8-4b65-8553-e2f967e89d8c/sha256%3A81b1272cf22d7b6440e5d6e2664f0a638178d9b2080db25d43f4f7b127a8f6a4/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F820b851b-5e44-4631-bb96-e5d0cebc6abd.replay",
  "ready": true
}
```

Path check, component by component:

| Required | Observed |
|---|---|
| `…/v2/coworlds/replays/static/` | `…/v2/coworlds/replays/static/` ✅ |
| `<cow_id>` | `cow_4b06234f-97d8-4b65-8553-e2f967e89d8c` ✅ (= STATE) |
| `<sha>` = manifest_hash, URL-encoded | `sha256%3A81b1272cf22d7b6440e5d6e2664f0a638178d9b2080db25d43f4f7b127a8f6a4` ✅ (= `GET /coworlds/$COW` `manifest_hash`) |
| `index.html` | `index.html?v=2` ✅ |
| replay handed in | `#replay=<url-encoded s3 url>` ✅ |
| **not** `/client/replay` | no `/client/replay` anywhere in the URL ✅ |

The `?v=2#replay=…` fragment form (rather than `?replay=…`) is the documented current shape —
`playbooks/observatory-api.md` §Featured match: "since 2026-08-28 the session endpoint returns
the replay as a URL-encoded **fragment** instead, `…/index.html?v=2#replay=<s3 url>`; both are
the static route." `ready: true` ⇔ static delivery.

Status: **TRUE** — source used: **(c) `POST /coworlds/replays/session`** for the `src`, with
(b) the SSR payload for the featured match; (a) the raw-HTML grep is empty as expected for the
client-rendered page and is not counted either way.

---

## 7. Certification declared the static bundle — **TRUE**

Source read: **the committed `runs/2026-08-28-atari-57/release-result.json`** (the artifact
phase 40 downloaded from release run `33213738190` and committed at 21:51Z). No re-download
was needed; `/tmp` was not consulted.

```
jq -r '.certify.replay_liveness' runs/2026-08-28-atari-57/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

```
jq '.certify | {ok, replay_liveness}' runs/2026-08-28-atari-57/release-result.json
{
  "ok": true,
  "replay_liveness": "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"
}
```

The certification transcript in the same artifact, all 10 steps:

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
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE** — contains `Replay liveness: skipped (static replay bundle declared`
verbatim.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

### 8(a) The dispatch

```
Dispatch at 2026-08-28T22:18:24Z
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder \
  -f url='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_4b06234f-97d8-4b65-8553-e2f967e89d8c/sha256%3A81b1272cf22d7b6440e5d6e2664f0a638178d9b2080db25d43f4f7b127a8f6a4/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F820b851b-5e44-4631-bb96-e5d0cebc6abd.replay' \
  -f timeout=90
```

Find-the-new-run (not "the latest run" blind) — the only run created after 22:18:24Z:

```
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10
33216261052	2026-08-28T22:18:25Z	in_progress     <- created 1s after my dispatch: MINE
33211231543	2026-08-28T21:08:08Z	completed
33198007349	2026-08-28T18:09:26Z	completed
33187402013	2026-08-28T15:54:21Z	completed
…
```

Ownership confirmed independently of timing: the artifact's own `url` field is byte-identical
to the `viewer_url` returned by the session call in check 6 (see the JSON below).

```
gh run watch 33216261052 -R Metta-AI/coworld-builder --exit-status
✓ viewer-check in 35s (ID 99000437648)  — conclusion: success
  ✓ Load the viewer   ✓ Summary   ✓ Upload the evidence   ✓ Fail if the viewer did not load
```

```
gh run download 33216261052 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-28-atari-57/viewer-check
-rw-r--r--  0      smoke-stderr.txt
-rw-r--r--  710    smoke-stdout.txt
-rw-r--r--  1506   viewer-smoke.json
-rw-r--r--  603131 viewer-smoke.png
```

### 8(b) The readouts, verbatim

```
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-28-atari-57/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":2984,"clock":"2:00 TIME LEFT CHOMPER · PAR 2600 · TURN 1/24","scorebug":"SCR 1 DAVEEY SCORE 3.000 0 PTS SCR 1 BASELINE SCORE 3.000 0 PTS 2:00 TIME LEFT CHOMPER · PAR 2600 · TURN 1/24 SCR 1 DAVEEY-1 SCORE 3.000 0 PTS SCR 1 BASELINE (2) SCORE 3.000 0 PTS","feed_lines":0}
```

```
jq -c '.signals' …/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

```
jq -r '.failure // "no failure"' …/viewer-smoke.json
no failure
```

**The three clock readouts:**

| scrub | clock |
|---|---|
| 0 % | `2:00 TIME LEFT CHOMPER · PAR 2600 · TURN 1/24` |
| 50 % | `1:00 TIME LEFT CHOMPER · PAR 2600 · TURN 13/24` |
| 100 % | `0:00 TIME LEFT CHOMPER · PAR 2600 · TURN 24/24` |

All three **differ**, on both axes (clock 2:00 → 1:00 → 0:00 and turn 1 → 13 → 24). The
`#scrub` control exists and responds; there is no `"(no #scrub…)"` placeholder.

The URL the browser actually opened, from the artifact:

```json
"url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_4b06234f-97d8-4b65-8553-e2f967e89d8c/sha256%3A81b1272cf22d7b6440e5d6e2664f0a638178d9b2080db25d43f4f7b127a8f6a4/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F820b851b-5e44-4631-bb96-e5d0cebc6abd.replay"
```

Other fields from the same artifact: `"status":"OPEN"`, `"loading_text":null`,
`"console_tail":[]`, `"canvas_text":{"total":0,"outside":0,"ellipsized":0,"never_inside":0}`
(no canvas-drawn text to bound-check; this shell paints its readouts in the DOM).

**Item 8 pass conditions:** `loaded: true` ✅ (via `data-replay-loaded="true"`, first frame at
2 984 ms) **and** the three clock readouts differ ✅.

### 8(c) The replay JSON the viewer was asked to draw

Ordered stance excerpts from `/tmp/ep.replay` → `tools/replay_summary.py`
(`turn seat alias source mode zone risk say`):

```
=== EARLY (turns 0-1) ===
0	0	RED	llm	clear	centre	0.5	Eating down the middle, building for chains.
0	1	BLUE	llm	bank	none	0.25	farming
0	2	GREEN	scripted	clear	none	1.0	vacuum
0	3	YELLOW	scripted	clear	none	1.0	vacuum
1	0	RED	llm	hunt	se	0.55	Power pellet chain priority
1	1	BLUE	llm	bank	none	0.25	Farming phase. Survive to endgame.
1	2	GREEN	scripted	clear	none	1.0	vacuum
1	3	YELLOW	scripted	clear	none	1.0	vacuum

=== MIDDLE (turn 12) ===
12	0	RED	llm	clear	nw	0.5	Hunting NW cluster
12	1	BLUE	llm	strike	ne	1.0	CHASING NE HUNTERS - HIGH VALUE CHAIN INCOMING
12	2	GREEN	scripted	safe	none	0.0	backing off
12	3	YELLOW	scripted	safe	none	0.0	backing off

=== LATE (turn 23) ===
23	0	RED	llm	clear	nw	0.175	Last life. Grinding safely in NW. Chain is over.
23	1	BLUE	scripted	safe	none	0.0	backing off
23	2	GREEN	scripted	safe	none	0.0	backing off
23	3	YELLOW	scripted	safe	none	0.0	backing off
```

```
jq -c '{tickCount, stopped, budgetGuards, inputRecords:(.inputRecords|length), formatVersion, gameName, gameVersion}'
{"tickCount":3075,"stopped":false,"budgetGuards":0,"inputRecords":359,"formatVersion":1,"gameName":"atari-57","gameVersion":"1"}
```

(`.results` is pasted in full under check 4.)

### The spectator-judgment paragraph

`viewer-smoke.png` (1280×800, 603 KB, captured at the 100 % scrub position) is **not empty and
not frozen**. It shows a 2×2 grid of four Chomper mazes — one lane per seat — drawn in the
arcade palette: dotted pellet fields, red hunter sprites, yellow power pellets, a red player
triangle in lane 0. Three of the four lanes carry a large `GAME OVER` banner in the seat's own
colour (blue for BLUE, green for GREEN, yellow for YELLOW); lane 0 (RED) does not, and that
matches the record exactly — `results.livesLeft == [1,0,0,0]`, i.e. only `daveey` still had a
credit at the end. Each lane prints its own points under the board: **3730 / 1360 / 1330 /
1330**, against `results.points == [3740,1360,1330,1330]` — the small delta on lane 0 is
because the screenshot sits at tick 2875/2880 (visible in the transport strip) and RED's
`lastScoreTick` is 3073, so the final 10 points had not yet landed. That is the picture and the
record agreeing, not disagreeing. Across the top runs the scorebug: four seat cards reading
`DAVEEY 38.300 · 3730 PTS`, `BA… 13.300 · 1330 PTS`, `DA… 13.600 · 1360 PTS`,
`BA… 13.300 · 1330 PTS`, with a centred clock block `0:00 / TIME LEFT / CHOMPER · PAR 2600 ·
TURN 24/24` — the same string the DOM readout returned at 100 %. At the bottom sit a stance
chip row (`RED CLEAR·NW  BLUE SAFE  GREEN SAFE  YELLOW SAFE`) and a four-line commentary feed,
whose top line reads `RED : CLEAR·NW — Lost life (1 remaining). Closest safe target pellet
cluster at (4,7) in 40 ticks. All threats >60 ticks away. Rule 7: halve risk to 0.125, cap at
0.35. Rule 6…` — which is the verbatim `note` of the turn-23 RED stance quoted in check 4. A
spectator can therefore read *who is winning* (scorebug + per-lane points + GAME OVER banners)
and *why* (the stance chips and the feed line, in the champion's own words). **It is legible
and it shows the game.**

**Chrome lineage:** yes — this is the paintbot / coworld-ctf shell, not a rewrite. The bottom
strip carries the same transport controls in the same order (restart ⟲, step-back ◀, play ▶,
`+5s`, step ▶, loop ↻, fast-forward ▶▶), the same `spoilers` toggle, the same
`2875 / 2880` tick counter, the same right-hand speed ladder `1× 2× 3× 4× 8× 16×`, and beneath
it the **scrubber with the momentum graph** — four coloured traces (red, blue, green, yellow)
tracking each seat's standing over the episode, with the playhead marker at the right edge.
Scorebug across the top, endcard-style `GAME OVER` overlays inside the board, feed under the
board: the starter's layout, with an atari-57 game block appended. No sign of the
cogame-gridlock failure mode (a different product sharing only the ids).

**One legibility observation for the coordinator (non-blocking, phase-30 grade):** the probe
reported `feed_lines: 0` while the screenshot plainly shows four feed lines and a chip row.
That is an instrumentation mismatch — the coworld's feed element does not carry the selector
`viewer-check.yml` counts — not a missing feed. The feed renders; the counter does not see it.
Worth a look if the shell is expected to expose the starter's feed selector.

Status: **TRUE** — `loaded: true` at 2 984 ms, `failure: null`, three differing clock readouts,
rendered evidence committed at `runs/2026-08-28-atari-57/viewer-check/`.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 2, 3 |
| 2 | Both champions ranked, fillers absent | **TRUE** — daveey #1, daveey-1 #2, 2 rounds each |
| 3 | Latest round's episode request completed with replay | **TRUE** — `ereq_c6f8d48c…` |
| 4 | Replay bytes valid, protocol match, shows the game | **TRUE** — `atari-57/v1`, complete/full_time, 0 fallbacks |
| 5 | Hosted game log clean | **TRUE** — grep CLEAN |
| 6 | Public page uses the static replay path | **TRUE** — static route, `ready: true` |
| 7 | Certification declared the static bundle | **TRUE** — from committed `release-result.json` |
| 8 | Viewer executed and judged | **TRUE** — `loaded: true`, clocks 2:00/1:00/0:00 |

Key artefacts:
- Replay: `https://softmax-public.s3.amazonaws.com/replays/820b851b-5e44-4631-bb96-e5d0cebc6abd.replay`
  (saved at `runs/2026-08-28-atari-57/ep.replay`, 73 374 B)
- Iframe `src`: `https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_4b06234f-97d8-4b65-8553-e2f967e89d8c/sha256%3A81b1272c…/index.html?v=2#replay=…`
- viewer-check run: `33216261052` (Metta-AI/coworld-builder, success)
- Rendered evidence: `runs/2026-08-28-atari-57/viewer-check/viewer-smoke.{json,png}`
