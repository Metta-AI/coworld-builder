# VERIFY — battlecode-2021   (2026-09-04T16:16Z)

Verdict: **1 item false** (item 8 — the scrub gate; items 1–7 TRUE)

Coworld `battlecode` v0.3.0 `cow_455dff0d-7f57-4b21-a28d-6603d9c458d0` (canonical),
league `league_cb515f3b-3c07-4512-bbf8-b72324f3cbf5` (key `bc21`, public page
`https://softmax.com/battlecode/bc21`), division `div_5beaa66e-36ec-4db2-bc46-31a501eebaa6`.

All headers are named, never their values:
`AUTH = -H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0"`,
`ELEV = -H "X-Use-Elevated-Privileges: true"`.
Every fetch below was made fresh in this heartbeat (2026-09-04 15:49Z–16:16Z). The two
documented exceptions are item 7 (the committed `release-result.json` from phase 40) and item 8
(the artifacts of the three `viewer-check.yml` runs dispatched in this heartbeat).

| # | Item | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | TRUE |
| 2 | Both champions ranked, fillers absent | TRUE |
| 3 | Latest round's episode request completed with a replay | TRUE |
| 4 | Replay bytes valid and show the game | TRUE |
| 5 | Hosted game log clean | TRUE |
| 6 | Public page uses the **static** replay path | TRUE |
| 7 | Certification declared the static bundle | TRUE |
| 8 | Viewer EXECUTED: `loaded:true` **and** three differing clock readouts | **FALSE** (`loaded:true`, but all three readouts identical — the worker never advances past round 5 inside the harness's window; a control run isolates the cause, see below) |

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

```bash
BASE=https://softmax.com/api/observatory/v2
L=league_cb515f3b-3c07-4512-bbf8-b72324f3cbf5
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}"
# HTTP 200 bytes=6988   (shape: {"entries":[…]})
```

Response, trimmed to the fields the check reads (the full body repeats the whole `division`
object under every row):

```json
[
  {
    "id": "round_dc7a247d-a8ad-4d52-bb68-283eb7ee07f0",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "skip_kind": null,
    "scheduled_by": "ladder",
    "created_at": "2026-09-04T16:01:26.688221Z",
    "completed_at": "2026-09-04T16:02:28.858789Z",
    "round_config": {
      "stages": null,
      "purpose": "ladder",
      "entrant_attributions": [
        {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
         "policy_version_id": "f47ed7be-d5a6-476a-809a-77ba16cd2093",
         "league_policy_membership_id": "lpm_de8faad2-9a85-4976-8af9-572ebfe592de"},
        {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
         "policy_version_id": "95c4e0e1-c79c-4664-a8e5-a94c85627967",
         "league_policy_membership_id": "lpm_47375ab7-bef5-4358-9894-d562cf8baf07"}
      ],
      "entrant_policy_version_ids": [
        "f47ed7be-d5a6-476a-809a-77ba16cd2093",
        "95c4e0e1-c79c-4664-a8e5-a94c85627967"
      ]
    }
  },
  {
    "id": "round_6feca3e3-6cbd-4787-b167-2d9a8cb254d1",
    "round_number": 1,
    "status": "completed",
    "error": null,
    "skip_kind": null,
    "scheduled_by": "ladder",
    "created_at": "2026-09-04T15:46:26.063873Z",
    "completed_at": "2026-09-04T15:47:38.902629Z",
    "round_config": {
      "stages": null,
      "purpose": "ladder",
      "entrant_attributions": [
        {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
         "policy_version_id": "f47ed7be-d5a6-476a-809a-77ba16cd2093",
         "league_policy_membership_id": "lpm_de8faad2-9a85-4976-8af9-572ebfe592de"},
        {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
         "policy_version_id": "95c4e0e1-c79c-4664-a8e5-a94c85627967",
         "league_policy_membership_id": "lpm_47375ab7-bef5-4358-9894-d562cf8baf07"}
      ],
      "entrant_policy_version_ids": [
        "f47ed7be-d5a6-476a-809a-77ba16cd2093",
        "95c4e0e1-c79c-4664-a8e5-a94c85627967"
      ]
    }
  }
]
```

```
completed count: 2
non-completed rows: []          <- no failed / discarded row exists, so no `error` to quote
```

Fillers are set on the league, fetched fresh this run (this read 403s on bare AUTH —
`ELEV` sent, `playbooks/observatory-api.md` §6):

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"     # HTTP 200
```
```json
{
  "filler_policy_versions": [
    {"policy_version_id": "45c48b3f-c363-4a17-8256-a09438a0ac7b",
     "policy_id": "de8e5607-8c39-4086-88ef-cdfd9caa70fa",
     "policy_name": "battlecode-california-roll", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "display_name": null},
    {"policy_version_id": "28b535fa-170b-4060-a799-bb42840534ba",
     "policy_id": "f8213e03-934a-4fc1-929a-ea3675667611",
     "policy_name": "battlecode-examplefuncsplayer21", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "display_name": null}
  ]
}
```

Both filler ids differ from both champion ids
(`f47ed7be-…` turtle / `95c4e0e1-…` muckrush), as §6 requires.

Status: **TRUE** — 2 completed rounds, both `error: null`, no `failed`/`discarded` rows exist.

Ordering against the filler registration: `log.md` records phase 50's whole batch under one
stamp — `2026-09-04T15:47:24Z 50 fillers 200: battlecode-california-roll:v1=45c48b3f… ,
battlecode-examplefuncsplayer21:v1=28b535fa… (neither champion)` followed by
`2026-09-04T15:47:24Z 50 unpaused 200; trigger-round 200 (ladder workflow); round_6feca3e3
round 1 pending`. That 15:47:24Z stamp is the batch write, not a per-call clock, so it is later
than round 1's `created_at` (15:46:26Z) without meaning the fillers came later. Round 1 is
after the filler write by the documented platform rule in `playbooks/observatory-api.md` §6:
*"A `trigger-round` issued before any filler exists fails instantly with `Temporal
RoundWorkflow failed before settling the round`."* Round 1 settled `completed` with
`error: null`, so a filler existed when it was triggered. Round 2 (`created_at`
16:01:26.688221Z) is unambiguously after the batch write on any reading. Both rounds therefore
count; the criterion needs only two.

---

## 2. Both champions ranked, fillers absent — TRUE

```bash
D=div_5beaa66e-36ec-4db2-bc46-31a501eebaa6
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}"     # HTTP 200, bare list
```
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
    "policy_label": "battlecode-bc21-turtle:v1",
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
    "policy_label": "battlecode-bc21-muckrush:v1",
    "recent_rounds": null
  }
]
```

Status: **TRUE** — `daveey` (`battlecode-bc21-turtle:v1`, `rounds_played` 2) and `daveey-1`
(`battlecode-bc21-muckrush:v1`, `rounds_played` 2) are both ranked, each ≥ 1 round. The board
has exactly two rows: neither filler (`battlecode-california-roll:v1`,
`battlecode-examplefuncsplayer21:v1`) appears, and no `Baseline (N)` row appears — with two
ranked champions the ladder never needed a filler seat. The board moved between polls
(1016.0 / 984.0 after round 1 at 15:49Z → 1030.53 / 969.47 after round 2), which is the ELO
updating, not a stale read.

---

## 3. Latest round's episode request completed with a replay — TRUE

The latest completed round is `round_dc7a247d-a8ad-4d52-bb68-283eb7ee07f0` (round_number 2,
from item 1). The flat list route is still dead for GET, confirmed this run:

```bash
curl -sS -w "\nHTTP %{http_code}\n" \
  "$BASE/episode-requests?round_id=round_dc7a247d-a8ad-4d52-bb68-283eb7ee07f0&limit=20" "${AUTH[@]}"
{"detail":"Method Not Allowed"}
HTTP 405
```

The nested route works (`playbooks/observatory-api.md` §9):

```bash
R=round_dc7a247d-a8ad-4d52-bb68-283eb7ee07f0
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}"     # HTTP 200
```
```json
{
  "entries": [
    {
      "id": "ereq_1f12242c-5743-46a7-ba5d-1db20d8f4e5e",
      "status": "completed",
      "coworld_id": "cow_455dff0d-7f57-4b21-a28d-6603d9c458d0",
      "round_id": "round_dc7a247d-a8ad-4d52-bb68-283eb7ee07f0",
      "replay_url": "https://softmax-public.s3.amazonaws.com/replays/9d29794c-516e-40af-9239-7c7f0653759b.replay",
      "policy_version_ids": [
        "f47ed7be-d5a6-476a-809a-77ba16cd2093",
        "95c4e0e1-c79c-4664-a8e5-a94c85627967"
      ],
      "created_at": "2026-09-04T16:01:27.137884Z"
    }
  ],
  "next_cursor": null
}
```

```bash
EREQ=ereq_1f12242c-5743-46a7-ba5d-1db20d8f4e5e
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/9d29794c-516e-40af-9239-7c7f0653759b.replay",
  "participants": [
    {
      "position": 0,
      "kind": "policy",
      "policy_version_id": "f47ed7be-d5a6-476a-809a-77ba16cd2093",
      "policy_id": "6ea2fb15-bb5f-4958-85c7-729aca231863",
      "policy_name": "battlecode-bc21-turtle",
      "version": 1,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": false,
      "is_seed": false
    },
    {
      "position": 1,
      "kind": "policy",
      "policy_version_id": "95c4e0e1-c79c-4664-a8e5-a94c85627967",
      "policy_id": "287b1e55-6086-49df-9b32-d338af99c507",
      "policy_name": "battlecode-bc21-muckrush",
      "version": 1,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
      "player_name": "daveey-1",
      "is_filler": false,
      "is_seed": false
    }
  ],
  "participant_scores": [
    {"position": 0, "score": 267.5},
    {"position": 1, "score": 31.5}
  ]
}
```

Status: **TRUE** — `status: "completed"`, non-null `replay_url`, participants are `daveey`
(turtle, seat 0) and `daveey-1` (muckrush, seat 1), both `is_filler: false`, and the two policy
version ids match STATE's champions byte-for-byte.

---

## 4. Replay bytes are valid and show the game — TRUE

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/9d29794c-516e-40af-9239-7c7f0653759b.replay" \
  -o /tmp/ep.replay
# HTTP 200 bytes=71618

jq -e . /tmp/ep.replay >/dev/null && echo "jq strict: ok"
jq strict: ok

python3 -c "
import json
raw=open('/tmp/ep.replay','rb').read(); s=raw.decode('utf-8')   # strict UTF-8, not a browser
d=json.loads(s); print('strict UTF-8 JSON: ok  bytes=%d'%len(raw))"
strict UTF-8 JSON: ok  bytes=71618
```

**Header** — `protocol` matches the manifest:

```
format       = 'cogame-battlecode-replay'
version      = 1
protocol     = 'cogame.battlecode.v1'
game_version = 'GV06'
year         = 'bc21'
seed         = 1694713001
names        = ['daveey', 'daveey-1']
aliases      = ['Clan Ash', 'Clan Basil']
```

Cross-check against the manifest this release certified
(`/workspace/cogame-battlecode@d292243`, `coworld_manifest_template.json`):

```bash
jq -c '.game.protocols' coworld_manifest_template.json
{"player":{"type":"uri","value":"https://github.com/Metta-AI/cogame-battlecode/blob/main/docs/PROTOCOL.md"},
 "global":{"type":"uri","value":"https://github.com/Metta-AI/cogame-battlecode/blob/main/docs/PROTOCOL.md"}}

grep -n 'GV06' docs/PROTOCOL.md
222:{"protocol":"cogame.battlecode.v1","game_version":"GV06","year":"bc21",
```
The manifest's declared protocol document is `docs/PROTOCOL.md`, titled `# cogame.battlecode.v1`
(line 1), whose bc21 section pins `game_version GV06`, `year bc21`. The replay's three header
values are exactly those. **Match.**

**`.result`** (episode-level, minus the per-game array — note this game's replay uses `.result`
singular and `.kind` for events, so the phase prompt's `.results` / `.type` queries return empty
on this schema; the values below are read with the right keys):

```json
{
  "names": ["daveey", "daveey-1"],
  "aliases": ["Clan Ash", "Clan Basil"],
  "scores": [267.5, 31.5],
  "wins": [2, 0],
  "points": [[62, 73], [37, 26]],
  "seed": 1694713001,
  "year": "bc21",
  "policy_kind": ["llm", "llm"],
  "sheet_defaults_applied": [[], []],
  "fallbacks": [0, 0],
  "decision_ms": [5383, 5383],
  "sim_seconds": 9.361,
  "reason": "complete",
  "wall_clock_seconds": 22.453,
  "game_version": "GV06"
}
```

`reason == "complete"` — the expected pass. The design note's `deadline` exception
(`design.md` line 446: *"`deadline` is **declared acceptable** for this coworld at phase-60
check 4"*) is **not** needed and is not being leaned on. `results.reason`'s closed enum in the
design note is `complete | deadline | fault` (design.md lines 438-444); `complete` is defined
there as *"a side won 2 games, or all scheduled games finished"* — this episode is the first
branch: Clan Ash took games 1 and 2, so the scheduled third map (`FrogOrBath`) was never
needed. The hosted log agrees: `battlecode: reason=complete games=2`.

**Fallback census — the doctrine sheets are real LLM output, not fallbacks.**
The prompt's `select(.fallback==true)` returns `[]`, and so does every equivalent on this
schema:

```
events with fallback==true : []
doctrine_fallback events   : []
events with .type=="decision" : []      # this schema uses .kind, not .type
result.fallbacks           : [0, 0]
result.policy_kind         : ["llm", "llm"]
result.sheet_defaults_applied : [[], []]
seats[0].fallback = None   seats[0].fallback_detail = None   sheet_unknown_fields = []
seats[1].fallback = None   seats[1].fallback_detail = None   sheet_unknown_fields = []
```

Both sheets arrived on attempt 1, from the replay's own events:

```
kind='doctrine_requested' ms=0    slot=0 attempt=1 deadline_ms=20000
kind='doctrine_requested' ms=0    slot=1 attempt=1 deadline_ms=20000
kind='doctrine_received'  ms=5383 slot=0 attempt=1 latency_ms=5383 defaults_applied=0 unknown_fields=0
kind='doctrine_received'  ms=5383 slot=1 attempt=1 latency_ms=5383 defaults_applied=0 unknown_fields=0
```

Fallback count is **0 of 2 decisions** — not a minority, none.

**The two sheets differ materially.** Recorded verbatim in the replay (`seats[n]`):

*seat 0 — daveey / Clan Ash / `battlecode-bc21-turtle:v1`*
```json
{"opening":"slanderer_turtle","slanderer_ratio":70,"muck_ratio":15,
 "politician_size_curve":"ramp","bid_policy":"escalate_when_ahead",
 "expansion":"neutral_centers_first","flank_policy":"screen_home",
 "empower_threshold":140,"convert_over_kill":true,"eco_exponential_round":1050}
```
motto: `"Print money. Buy the election. Hold the line."`
notes: `"Build 130-influence slanderers → 6/round for 51 rounds, then free politicians. Compound until round 1050, then spend aggressively on votes. Expect to out-earn enemy by round 650–700. If muckraker rush pre-200: pivot muck_ratio to 40%, screen home aggressively, sacrifice slanderer"` *(cut at the design's 280-rune cap)*

*seat 1 — daveey-1 / Clan Basil / `battlecode-bc21-muckrush:v1`*
```json
{"opening":"muck_spam","slanderer_ratio":12,"muck_ratio":65,
 "politician_size_curve":"cheap","bid_policy":"never",
 "expansion":"neutral_centers_first","flank_policy":"flank_wide",
 "empower_threshold":25,"convert_over_kill":false,"eco_exponential_round":280}
```
motto: `"No economy. Only muckrakers and ashes."`
notes: `"Muckraker rush: swarm early to flank their slanderers before they mature. Expose their economy (0.1% buff per slanderer). Cheap politicians arrive during buff window for annihilation. If turtle survives to r600, pivot to neutral center control and vote warfare."`

They differ on **9 of 10** knobs (only `expansion` agrees) and in the direction the two prompts
name: turtle opens `slanderer_turtle` at `slanderer_ratio 70` / `muck_ratio 15`, bids
`escalate_when_ahead`, empowers only at 140 and compounds to round 1050; muckrush opens
`muck_spam` at `muck_ratio 65` / `slanderer_ratio 12`, never bids, empowers at 25 and switches
on at round 280. Not one template with two names.

**The games were contested; nobody idled.** `.result.games[]`:

```json
{"map": "Bog", "side": ["A", "B"], "rounds_played": 1500, "winner": 0, "end_reason": "more_votes", "centers_owned": [1, 3], "centers_captured": [0, 2], "centers_lost": [0, 0], "neutrals_captured": [0, 2], "votes": [1381, 0], "bids_placed": [1381, 0], "bid_influence_spent": [3181, 0], "top_bid": [4, 0], "influence_spent": [9732, 17818], "influence_end": [5003, 8492], "income_end": [8, 24], "units_built": [444, 1764], "politicians_built": [66, 1553], "slanderers_built": [299, 8], "muckrakers_built": [79, 203], "units_alive": [121, 297], "politicians_alive": [79, 91], "slanderers_alive": [0, 0], "muckrakers_alive": [41, 203], "empowers": [18, 1470], "empower_conviction": [6, 537], "conversions": [0, 2], "exposes": [0, 265], "buff_peak": [0, 1789], "camouflaged": [31, 8], "robots_lost": [324, 1470], "votes_tied": 119, "rounds_no_bid": 119}
{"map": "Arena", "side": ["B", "A"], "rounds_played": 1500, "winner": 0, "end_reason": "more_votes", "centers_owned": [2, 1], "centers_captured": [2, 2], "centers_lost": [1, 2], "neutrals_captured": [0, 1], "votes": [1406, 0], "bids_placed": [2118, 0], "bid_influence_spent": [4089, 0], "top_bid": [4, 0], "influence_spent": [28712, 9704], "influence_end": [26411, 2966], "income_end": [16, 8], "units_built": [332, 651], "politicians_built": [98, 442], "slanderers_built": [175, 7], "muckrakers_built": [59, 202], "units_alive": [225, 192], "politicians_alive": [164, 8], "slanderers_alive": [0, 0], "muckrakers_alive": [59, 183], "empowers": [83, 442], "empower_conviction": [857, 1377], "conversions": [3, 4], "exposes": [0, 25], "buff_peak": [0, 212], "camouflaged": [150, 7], "robots_lost": [111, 464], "votes_tied": 94, "rounds_no_bid": 94}
```

Both games ran the full 1500 rounds on two different maps with the sides **swapped**
(`side: ["A","B"]` on Bog, `["B","A"]` on Arena — the symmetric-map fairness swap the design
calls for), and `end_reason` is the engine's `MORE_VOTES` in both. The doctrines are visibly
doing what they said: Clan Basil (muckrush) built 1764 units on Bog against Clan Ash's 444,
1553 of them politicians, with 1470 empowers, 265 exposes and a `buff_peak` of 1789 —
`empower_threshold 25` and `muck_ratio 65` in action. Clan Ash (turtle) built 299 slanderers to
Basil's 8, bid on **1381 of 1500** rounds to Basil's 0 (`bid_policy: "never"`), and took the
election 1381 votes to 0. `votes_tied: 119` / `rounds_no_bid: 119` are the rounds nobody bid, so
the bid auction was genuinely contested for the other 1381. The series was a 2–0, not a split,
but neither game was a walkover: Basil out-spent Ash on influence in game 1 (17818 vs 9732) and
captured two Centers to Ash's zero, and still lost the vote — the muck rush killing robots
while the turtle bought the election is exactly the tension the design describes.

**Event census** (89 events; `.kind`, not `.type`):

```
Counter({'bid_spike': 30, 'expose_wave': 24, 'first_build': 12, 'center_taken': 6,
         'empower_big': 6, 'doctrine_requested': 2, 'doctrine_received': 2,
         'game_start': 2, 'game_end': 2, 'episode_start': 1, 'vote_lead': 1,
         'episode_end': 1})
```

Status: **TRUE** — strict UTF-8 JSON under two independent strict parsers, `protocol`
matches the manifest's `docs/PROTOCOL.md`, `reason == "complete"`, zero fallbacks on either
champion seat, two materially different LLM doctrines, two full-length contested games.

---

## 5. Hosted game log is clean — TRUE

```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs.raw
# HTTP 200 bytes=1728  — python b'…' reprs under ===== container: … ===== headers,
# decoded per-line with ast.literal_eval before grepping (playbook §10)
grep -nEi 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.decoded || echo CLEAN
CLEAN
```

The whole decoded body (1670 chars), pasted rather than summarised:

```
=== container: coworld-init-config ===

=== container: bedrock-sidecar ===
2026-09-04 16:01:34,573 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1","has_role_arn":true,"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar","episode_request_id":"1f12242c-5743-46a7-ba5d-1db20d8f4e5e","job_request_id":"9d29794c-516e-40af-9239-7c7f0653759b","role":"game","slot":"game","image_digest":"sha256:6dc27f30dbdbfd583e3e0a497fbc8a006b8f368bb06f00e16ab9e11bc630fd51"}
[2026-09-04 16:01:34 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-09-04 16:01:34,828 INFO hypercorn.error Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-09-04 16:01:44,028 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-04 16:01:46,777 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"

=== container: game ===
battlecode config: year=bc21 pool=mixed seed=1694713001 games=3 maxRounds=1500 num_agents=2 matchBudget=340s
battlecode: listening on 0.0.0.0:8080
battlecode: waiting for seats
battlecode: refused a seat-0 connection: seat 0 was given the wrong connection token
battlecode: a spectator joined /global
battlecode: seat 0 connected
battlecode: seat 0 registered kind=llm label=turtle
battlecode: seat 1 connected
battlecode: seat 1 registered kind=llm label=muckrush
battlecode: doctrine
battlecode llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
battlecode: match
battlecode: settled: complete
battlecode: reason=complete games=2 scores=[267.5, 31.5] sim=9.361s wall=22.453s

=== container: worker ===
```

Status: **TRUE** — zero matches for any of the four gated patterns (grepped
case-insensitively, on the decoded text). Both LLM calls returned `HTTP/1.1 200 OK`; there is
**no** `LLM provider is unavailable` line, so the Bedrock-capacity exception is not invoked and
no cross-check against another LLM coworld was needed. Two lines worth naming so nobody
mis-reads them later: `refused a seat-0 connection: seat 0 was given the wrong connection
token` is the seat-token guard turning away a stray connect — it is followed two lines later by
`seat 0 connected` / `seat 0 registered kind=llm label=turtle`, it contains none of the four
gated strings, and both seats registered `kind=llm`. (The same line appears in the bc20 run's
log from this morning, so it is the guard's normal handshake noise, not new.)

---

## 6. The public page uses the static replay path — TRUE

**Source used: the page's SSR payload (`state.playlist[0]`) + the session endpoint the page's
own JS calls.** The raw-HTML grep is a documented dead end
(`playbooks/observatory-api.md` §Featured match, lighthouse 2026-08-22) and it was again here —
recorded, not treated as a false negative:

```bash
curl -sS "https://softmax.com/battlecode/bc21" | grep -o '<iframe[^>]*src="[^"]*"'
# HTTP 200, 875562 bytes — NO MATCH
curl -sS "https://softmax.com/battlecode"      | grep -o '<iframe[^>]*src="[^"]*"'
# HTTP 200, 893261 bytes — NO MATCH
```

The documented API fallback is null platform-wide, exactly as the playbook says — recorded, not
used as evidence:

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)[]|select(.name=="battlecode")
          |{id,name,canonical,version,replay_viewer,featured_match}'
{"id":"cow_455dff0d-7f57-4b21-a28d-6603d9c458d0","name":"battlecode","canonical":true,"version":"0.3.0","replay_viewer":null,"featured_match":null}
{"id":"cow_d9fc2f21-c095-4131-bd86-d35848e046f8","name":"battlecode","canonical":false,"version":"0.2.0","replay_viewer":null,"featured_match":null}
{"id":"cow_cfddca58-fa27-4dfd-bab8-38619b06fee7","name":"battlecode","canonical":false,"version":"0.1.6","replay_viewer":null,"featured_match":null}
{"id":"cow_6f3468fa-5cf5-4c4b-95cf-1d87dc41bfa2","name":"battlecode","canonical":false,"version":"0.1.5","replay_viewer":null,"featured_match":null}
```
(The `canonical: true` row is the 0.3.0 `cow_455dff0d-…` this run released — matching on
`canonical`, per the playbook, not on version string.)

**The featured match, server-rendered into `/battlecode/bc21` at `state.playlist[0]`** (excerpt
of the SSR payload, fetched 16:05Z, un-escaped only for width):

```json
"leagueId":"league_cb515f3b-3c07-4512-bbf8-b72324f3cbf5",
"playlist":[{"episodeId":"b0d0ece4-1a66-4201-9c6e-0e9a85437be0",
 "coworldId":"cow_455dff0d-7f57-4b21-a28d-6603d9c458d0",
 "coworldName":"battlecode","coworldVersion":"0.3.0",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/9d29794c-516e-40af-9239-7c7f0653759b.replay",
 "finishedAt":"2026-09-04T16:02:25.904367Z","roundNumber":2,"episodeNumber":1,
 "code":"battlecode.r2.e1",
 "matchup":{"divisionId":"div_5beaa66e-36ec-4db2-bc46-31a501eebaa6","divisionName":"Competition",
   "first":{"rank":1,"player_id":"ply_44ae9048-…","player_name":"daveey","score":1030.5304984710244,
            "policy_label":"battlecode-bc21-turtle:v1","rounds_played":2,"episode_wins":2,"win_rate":1},
   "second":{"rank":2,"player_id":"ply_bac48eb1-…","player_name":"daveey-1","score":969.4695015289755,
            "policy_label":"battlecode-bc21-muckrush:v1","rounds_played":2,"episode_wins":0,"win_rate":0}},
 "seats":2,"roster":["daveey","daveey-1"],
 "inspectUrl":"/observatory/v2?tab=overview&detail=episode-request:ereq_1f12242c-5743-46a7-ba5d-1db20d8f4e5e",
 "outcome":"first"}]
```

A featured match is present, it is round 2's episode, and its `replayUrl` and
`ereq_1f12242c-…` are the same ones item 3 fetched.

**The iframe `src`, from the call the page's JS makes:**

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_455dff0d-7f57-4b21-a28d-6603d9c458d0",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/9d29794c-516e-40af-9239-7c7f0653759b.replay"}'
# HTTP 200
```
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_455dff0d-7f57-4b21-a28d-6603d9c458d0/sha256%3A8ec16f221973a3e3949d36aaaecd826ba0e66e81f458f5dc9fb73e94876f3a6e/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F9d29794c-516e-40af-9239-7c7f0653759b.replay","ready":true}
```

Status: **TRUE** — the path is
`/v2/coworlds/replays/static/<cow_id>/<manifest sha, URL-encoded>/index.html`, with the replay
delivered as the URL-encoded fragment `#replay=<s3 url>` (the documented 2026-08-28 variant of
the static route, `playbooks/observatory-api.md` §Featured match). `ready: true`. The `<sha>` is
`sha256:8ec16f221973a3e3949d36aaaecd826ba0e66e81f458f5dc9fb73e94876f3a6e`, byte-identical to
`STATE.coworld.manifest_sha`. **No `/client/replay` pod URL anywhere.** The query form of the
same route also serves the live viewer — item 8 attempt 2 loaded
`…/index.html?replay=<encoded s3 url>` successfully (`loaded:true` in 2359 ms) and rendered the
same frame.

---

## 7. Certification declared the static bundle — TRUE

**Source: the committed `runs/2026-09-04-battlecode-2021/release-result.json`** — the artifact
phase 40 downloaded from release run `33890103949` and committed. It was present; **no
re-download was needed** (`gh run download` was not run).

```bash
jq -r '.certify.replay_liveness' runs/2026-09-04-battlecode-2021/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE** — contains `Replay liveness: skipped (static replay bundle declared`, read
from the committed artifact, not from `/tmp`.

---

## 8. Spectator judgment — the viewer, EXECUTED — **FALSE** (by the scrub rule)

Three `viewer-check.yml` runs were dispatched against `Metta-AI/coworld-builder` in this
heartbeat; all three artifacts are committed under
`runs/2026-09-04-battlecode-2021/viewer-check/`.

| attempt | run id | url | artifact dir | conclusion |
|---|---|---|---|---|
| 1 (primary) | `33893228440` | the item-6 `src` verbatim (`?v=2#replay=…9d29794c…`) | `viewer-check/` | success |
| 2 (query form / reproducibility) | `33893758738` | `?replay=<encoded s3 …9d29794c…>` | `viewer-check/attempt-2-query-form/` | success |
| 3 (**control**: same bc21 shell, bc20's lighter replay) | `33893927786` | `?replay=<encoded s3 …bb7e21c2…>` | `viewer-check/attempt-3-control-bc20-replay/` | success |

No run was red; the harness itself never failed, so no harness-level re-dispatch was consumed.

### (a) Dispatch — attempt 1, the primary

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_455dff0d-7f57-4b21-a28d-6603d9c458d0/sha256%3A8ec16f221973a3e3949d36aaaecd826ba0e66e81f458f5dc9fb73e94876f3a6e/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F9d29794c-516e-40af-9239-7c7f0653759b.replay'
# dispatch stamp: 2026-09-04T16:05:58Z
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:4][]|[.databaseId,.createdAt,.status,(.conclusion//"-")]|@tsv'
33893228440	2026-09-04T16:06:00Z	in_progress	-        <- created AFTER the dispatch stamp
33854861020	2026-09-04T08:44:05Z	completed	success
33854088585	2026-09-04T08:34:26Z	completed	success
33853943737	2026-09-04T08:32:38Z	completed	success

gh run watch 33893228440 -R Metta-AI/coworld-builder --exit-status     # green
gh run view  33893228440 -R Metta-AI/coworld-builder --json conclusion,status,createdAt,updatedAt
{"conclusion":"success","createdAt":"2026-09-04T16:06:00Z","status":"completed","updatedAt":"2026-09-04T16:06:41Z"}

gh run download 33893228440 -R Metta-AI/coworld-builder -n viewer-check \
  -D runs/2026-09-04-battlecode-2021/viewer-check
```

### (b) The readouts — attempt 1 (the primary)

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/…/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":1851,"clock":"2:05 GAME 1 OF 2 — BOG doctrines","scorebug":"CLAN ASH daveey · Print money. Buy the election. Hold the line. 67 2:05 GAME 1 OF 2 — BOG doctrines CLAN BASIL daveey-1 · No economy. Only muckrakers and ashes. 32","feed_lines":4}
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
jq -c '.console_tail' runs/…/viewer-check/viewer-smoke.json
["[bridge] ready"]
jq -c '.canvas_text' runs/…/viewer-check/viewer-smoke.json
{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
# total 0 = the board is drawn by the OffscreenCanvas worker, so the text-bounds
# hook saw nothing. Recorded, not judged on.
jq -c '.status,.loading_text' runs/…/viewer-check/viewer-smoke.json
"OPEN"
null
```

**The three clock readouts (attempt 1):**

| scrub position | `#clock` readout |
|---|---|
| 0 %   | `2:05 GAME 1 OF 2 — BOG doctrines` |
| 50 %  | `2:05 GAME 1 OF 2 — BOG doctrines` |
| 100 % | `2:05 GAME 1 OF 2 — BOG doctrines` |

**Attempt 2 (canonical `?replay=` query form) reproduces it exactly.** Dispatch:

```bash
SRC2='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_455dff0d-7f57-4b21-a28d-6603d9c458d0/sha256%3A8ec16f221973a3e3949d36aaaecd826ba0e66e81f458f5dc9fb73e94876f3a6e/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F9d29794c-516e-40af-9239-7c7f0653759b.replay'
# dispatch stamp: 2026-09-04T16:11:41Z
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC2" -f timeout=90
33893758738	2026-09-04T16:11:43Z	in_progress      <- created AFTER the dispatch stamp
gh run view 33893758738 -R Metta-AI/coworld-builder --json conclusion,createdAt,updatedAt
{"conclusion":"success","createdAt":"2026-09-04T16:11:43Z","updatedAt":"2026-09-04T16:12:26Z"}
gh run download 33893758738 -R Metta-AI/coworld-builder -n viewer-check \
  -D runs/2026-09-04-battlecode-2021/viewer-check/attempt-2-query-form
```


```json
{"loaded":true,"ms":2359,"clock":"2:05 GAME 1 OF 2 — BOG doctrines","scorebug":"CLAN ASH daveey · Print money. Buy the election. Hold the line. 67 2:05 GAME 1 OF 2 — BOG doctrines CLAN BASIL daveey-1 · No economy. Only muckrakers and ashes. 32","feed_lines":4}
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["ready"],"bridge_ready":true,"bridge_error":[]}
0%	2:05 GAME 1 OF 2 — BOG doctrines
50%	2:05 GAME 1 OF 2 — BOG doctrines
100%	2:05 GAME 1 OF 2 — BOG doctrines
no failure
```
Its `viewer-smoke.png` is visually indistinguishable from attempt 1's — same `round 5 / 1500`
on the tick-clock, same board state, same four feed lines, same playhead at the far left. Not
byte-identical, and I am not claiming it is: `sha256sum` gives
`e9333261…` (248 573 bytes, attempt 1) vs `6993e914…` (248 596 bytes, attempt 2), both 1280×800.
The difference is PNG encoding of an otherwise matching frame; every readout the check reads is
the same.

### Verdict on item 8, and why

Condition 1 **holds**: `loaded: true` on all three runs, via **both** signals
(`data-replay-loaded="true"` **and** the `coworld-replay` bridge `ready`), in 1.9–2.4 s, with
`failure: null` and a console tail of exactly `[bridge] ready`. The viewer draws a frame and
says so.

Condition 2 does **not** hold: the three readouts are identical, and the screenshot shows the
playhead pinned at the far left with `round 5 / 1500`. **Item 8 is FALSE.** I am not marking it
true on an inference.

### The control run that isolates the cause — attempt 3

This is **not** the bc20 mis-targeted-scrubber bug from this morning: the harness fix
(`SCRUB_SELECTORS = ['#scrub', '#seek', 'input[type="range"]']`, resolved in preference order)
is in `templates/tools/ci/viewer_smoke.mjs` at head and is demonstrably working — the zoom
slider reads `FIT` with its knob at the left in both screenshots, where the bc20 failure pinned
it at `12.0×`.

Attempt 3 points **the same bc21 shell, from the same manifest sha, through the same harness**
at the *bc20* replay (`…/replays/bb7e21c2-3fe7-4dcf-b299-19b7ed1d1d1b.replay`, `sim_seconds
0.598`):

```bash
SRC3='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_455dff0d-7f57-4b21-a28d-6603d9c458d0/sha256%3A8ec16f221973a3e3949d36aaaecd826ba0e66e81f458f5dc9fb73e94876f3a6e/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fbb7e21c2-3fe7-4dcf-b299-19b7ed1d1d1b.replay'
# dispatch stamp: 2026-09-04T16:13:29Z
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC3" -f timeout=90
33893927786	2026-09-04T16:13:31Z	in_progress      <- created AFTER the dispatch stamp
gh run view 33893927786 -R Metta-AI/coworld-builder --json conclusion   ->  {"conclusion":"success"}
gh run download 33893927786 -R Metta-AI/coworld-builder -n viewer-check \
  -D runs/2026-09-04-battlecode-2021/viewer-check/attempt-3-control-bc20-replay
```


```json
{"loaded":true,"ms":2352,"clock":"2:24 GAME 1 OF 3 — CLIMB","feed_lines":3}
```
| scrub position | `#clock` readout |
|---|---|
| 0 %   | `2:24 GAME 1 OF 3 — CLIMB` |
| 50 %  | `1:11 GAME 2 OF 3 — ALANDDIVIDED doctrines` |
| 100 % | `FINAL MATCH OVER doctrines` |
```
failure: no failure
```

The seek crosses game boundaries and lands on the endcard; its screenshot shows
`round 464 / 1500`, the scrub track filled end-to-end and the full endcard. So in this shell,
with this harness, on this runner: **`#scrub` click-to-seek works.** The variable that changes
the outcome is the replay, not the viewer shell and not the instrument.

**What the evidence says the cause is.** The bc21 episode is far heavier per round than the
bc20 one, and the viewer's Worker cannot keep up inside the ~3.5 s the harness observes:

- `result.sim_seconds` **9.361 s / 3000 rounds** = 3.12 ms per round (bc21, native, in the game
  container) against bc20's **0.598 s / 3462 rounds** = 0.17 ms per round — **18× heavier**.
- Unit counts scale the same way: bc21 game 1 built 444 + 1764 = 2208 robots with 1470 empowers
  and 265 exposes; bc20's heaviest game built 49 + 43 = 92 units.
- The shell's own clock arithmetic says the intended playback rate is 12 rounds/s
  (`2:05` = 125 s remaining at `round 5 / 1500`). Both bc21 runs screenshot at `round 5 / 1500`
  after ~1.4 s of post-load wall clock — **the same round and the same board in two
  independent runs** — so this is deterministic Worker starvation, not runner flake
  and not a slow-but-moving playback that happened to be sampled badly.
- `static_replay.js` (fetched from this bundle, lines 130-137) names exactly this mode:
  ```js
  // A batch of six frames is a catch-up for a Worker that is keeping up.
  // When the previous batch overran its own frame budget — the
  // background precompute walk on a long replay, or a seek converging —
  // the Worker is the bottleneck, and a batch is exactly how long a
  // click's seek then sits in the message queue. Drop to one frame per
  // message so an input waits at most one frame.
  ```
  The harness waits a fixed **700 ms** after each scrub click before reading the clock
  (`viewer_smoke.mjs`, `await sleep(700)`); a seek that has to converge over thousands of
  re-derived bc21 rounds cannot land inside that window.

**This is a real spectator finding, and I am not softening it:** for at least the first ~3.5 s
after load, this bc21 replay's board is frozen at round 5 and a scrubber click produces no
visible response. How long that lasts I **cannot** measure from these artifacts — the harness
exposes no soak and no post-click wait through the workflow's two inputs (`url`, `timeout`, and
`timeout` gates only the load signal), and the shell's bootstrap reads only `replay` from the
hash, so there is no deep-link that could start later or seek. Retry budget spent: 3 of 3
(primary / query-form reproduction / bc20-replay control). I did not edit the harness and did
not touch the coworld.

**For the judge, the two candidate readings, with what separates them:**
1. *A coworld-builder instrument limit* — the fixed 700 ms post-click wait is too short for a
   CPU-heavy replay. Supported by: the control run passing on a lighter replay through the same
   shell.
2. *A coworld performance finding* — the bc21 viewer is unusably slow to start playing and to
   seek. Supported by: two identical frames at `round 5 / 1500`, and 18× the per-round sim cost
   of the sibling year that does render smoothly.
   The two are not exclusive, and the measurement that would separate them (does the viewer
   free up after N seconds?) needs a `--soak`/longer-wait input this workflow does not expose.
   That measurement is the phase-30 follow-up I would ask for.

### (c) The replay JSON — what the viewer was asked to draw

Ordered event excerpts from `/tmp/ep.replay` (item 4's bytes; `.kind`, not `.type`):

**Early**
```
kind='episode_start' ms=0 seed=1694713001 year='bc21' maps=['Bog', 'Arena', 'FrogOrBath'] aliases=['Clan Ash', 'Clan Basil']
kind='doctrine_requested' ms=0 slot=0 attempt=1 deadline_ms=20000
kind='doctrine_requested' ms=0 slot=1 attempt=1 deadline_ms=20000
kind='doctrine_received' ms=5383 slot=0 attempt=1 latency_ms=5383 defaults_applied=0 unknown_fields=0
kind='doctrine_received' ms=5383 slot=1 attempt=1 latency_ms=5383 defaults_applied=0 unknown_fields=0
kind='game_start' game=0 round=0 map='Bog' width=32 height=32 sides=['Clan Ash', 'Clan Basil']
kind='first_build' game=0 round=1 alias='Clan Ash' unit='slanderer'
kind='first_build' game=0 round=1 alias='Clan Basil' unit='slanderer'
kind='first_build' game=0 round=3 alias='Clan Basil' unit='muckraker'
kind='first_build' game=0 round=9 alias='Clan Ash' unit='politician'
kind='first_build' game=0 round=62 alias='Clan Basil' unit='politician'
kind='bid_spike' game=0 round=100 alias='Clan Ash' bid=3 influence_before=150
kind='center_taken' game=0 round=126 alias='Clan Basil' from='neutral' x=31 y=23 influence=62
kind='empower_big' game=0 round=126 alias='Clan Basil' conviction=98 victims=88 converted='1/1'
kind='center_taken' game=0 round=186 alias='Clan Basil' from='neutral' x=30 y=9 influence=6
kind='empower_big' game=0 round=186 alias='Clan Basil' conviction=35 victims=6 converted='4/1'
kind='bid_spike' game=0 round=200 alias='Clan Ash' bid=3 influence_before=55
kind='first_build' game=0 round=245 alias='Clan Ash' unit='muckraker'
kind='bid_spike' game=0 round=300 alias='Clan Ash' bid=3 influence_before=140
kind='expose_wave' game=0 round=380 alias='Clan Basil' exposed_total=5 buff_pct=6.0
kind='expose_wave' game=0 round=382 alias='Clan Basil' exposed_total=6 buff_pct=17.4
kind='expose_wave' game=0 round=383 alias='Clan Basil' exposed_total=7 buff_pct=26.0
```

**Middle**
```
kind='expose_wave' game=0 round=447 alias='Clan Basil' exposed_total=31 buff_pct=111.4
kind='expose_wave' game=0 round=451 alias='Clan Basil' exposed_total=34 buff_pct=122.2
kind='expose_wave' game=0 round=452 alias='Clan Basil' exposed_total=35 buff_pct=125.5
kind='expose_wave' game=0 round=458 alias='Clan Basil' exposed_total=41 buff_pct=136.3
kind='bid_spike' game=0 round=500 alias='Clan Ash' bid=3 influence_before=133
kind='bid_spike' game=0 round=600 alias='Clan Ash' bid=3 influence_before=96
kind='bid_spike' game=0 round=700 alias='Clan Ash' bid=3 influence_before=105
kind='bid_spike' game=0 round=800 alias='Clan Ash' bid=3 influence_before=119
kind='bid_spike' game=0 round=900 alias='Clan Ash' bid=3 influence_before=139
kind='bid_spike' game=0 round=1000 alias='Clan Ash' bid=3 influence_before=144
kind='bid_spike' game=0 round=1100 alias='Clan Ash' bid=4 influence_before=200
kind='bid_spike' game=0 round=1200 alias='Clan Ash' bid=4 influence_before=217
kind='bid_spike' game=0 round=1300 alias='Clan Ash' bid=4 influence_before=500
kind='bid_spike' game=0 round=1400 alias='Clan Ash' bid=4 influence_before=365
kind='bid_spike' game=0 round=1500 alias='Clan Ash' bid=4 influence_before=795
kind='game_end' game=0 round=1500 winner_alias='Clan Ash' winner_slot=0 end_reason='more_votes' points=[62, 37]
```

**Late**
```
kind='bid_spike' game=1 round=800 alias='Clan Ash' bid=4 influence_before=536
kind='expose_wave' game=1 round=822 alias='Clan Basil' exposed_total=5 buff_pct=5.2
kind='expose_wave' game=1 round=834 alias='Clan Basil' exposed_total=9 buff_pct=10.1
kind='expose_wave' game=1 round=847 alias='Clan Basil' exposed_total=13 buff_pct=15.7
kind='expose_wave' game=1 round=875 alias='Clan Basil' exposed_total=22 buff_pct=20.5
kind='bid_spike' game=1 round=900 alias='Clan Ash' bid=4 influence_before=3003
kind='bid_spike' game=1 round=1000 alias='Clan Ash' bid=4 influence_before=3435
kind='bid_spike' game=1 round=1100 alias='Clan Ash' bid=4 influence_before=436
kind='bid_spike' game=1 round=1200 alias='Clan Ash' bid=4 influence_before=1747
kind='bid_spike' game=1 round=1300 alias='Clan Ash' bid=4 influence_before=1209
kind='bid_spike' game=1 round=1400 alias='Clan Ash' bid=4 influence_before=1134
kind='bid_spike' game=1 round=1500 alias='Clan Ash' bid=4 influence_before=1748
kind='game_end' game=1 round=1500 winner_alias='Clan Ash' winner_slot=0 end_reason='more_votes' points=[73, 26]
kind='episode_end' ms=0 reason='complete'
```

### The spectator judgment

**It is legible, it plainly shows this game — and it is frozen.** `viewer-smoke.png`
(attempts 1 and 2, visually the same frame) is a clean, readable broadcast frame at 1280×800. The 32×32
**Bog** board fills the centre in warm ochre with dark swamp shelves cut through it and a fine
checker grid; Clan Ash's red robots are clustered at their Enlightenment Center top-centre
(four red glyphs on a terraced shelf) and Clan Basil's blue ones at theirs bottom-centre (three
blue glyphs), with four neutral Centers as pale caged icons out at the map's edges — the rotational symmetry
the replay header declares (`"symmetry":"rotational"`) is visible on sight. Across the top is
the scorebug: `CLAN ASH` / `daveey · Print money. Buy the election. Hold the line.` / `67`
against `CLAN BASIL` / `daveey-1 · No economy. Only muckrakers and ashes.` / `32`, each seat's
real name and its own recorded motto, with `GAME 1 OF 2 — BOG` and a `doctrines` chip between
them. The bc21 readout pill sits at top centre — `Clan Ash 1 ▬▬▬ Clan Basil` / `751 to clinch`
— which is exactly the number bc21 is about (votes toward the 751 majority). Bottom-right the
killfeed narrates in plain sentences: `Clan Basil builds its first muckraker — game 1, round 3`,
`Clan Basil builds its first slanderer — game 1, round 1`, `Clan Ash builds its first slanderer
— game 1, round 1`, `Game 1 begins on Bog`. Under it the per-clan stat rail reads
`influence 31 / 137`, `income 1/r / 1/r`, `centres 1/6 / 1/6`. Along the bottom is the
transport strip: restart / step-back / pause / `+25` / play / loop / fast-forward, a `spoilers`
toggle, `round 5 / 1500`, the speed chips `1× 2× 4× 8× 16×`, and the scrubber with its coloured
momentum ticks. Top-right is the zoom bar reading `FIT` with the knob at rest.

**Picture and record agree.** Every feed line in the png is one of the replay's own early
events: `first_build … round 1 … slanderer` for both clans and `first_build … round 3 … Clan
Basil … muckraker` are verbatim the first three `first_build` events above. `centres 1 / 6` at
round 5 matches the prompt's map card (`your_centers` 1, `neutral_centers` 4, `enemy_centers` 1
= 6 on the board). `Clan Ash 1 … 751 to clinch` matches a game whose final vote was 1381 of
1500 — the first vote has just been bought. The momentum ticks cluster early and then thin out,
matching an event stream that is dense at rounds 1–3 and then spaced at the bid centuries.
Nothing on screen contradicts the JSON.

**But it is one frame.** The board is at round 5 of 1500 in both runs, the clock did not move
between the three samples, and clicking the scrubber changed nothing within 700 ms. What a
spectator gets in the first seconds is a beautiful, correct, **static** picture. That is the
whole of item 8's failure, and it is why I will not call it a pass: a replay that does not
visibly advance is a screenshot.

**It looks like the starter's chrome.** Same transport strip with the same seven buttons and
`spoilers` toggle, same scrubber-with-momentum-graph, same scorebug with mottos and plate
points, same `#killfeed` / `#endcard` / `#speedchips` / `#tick-clock` ids as
paintbot/raid/hive and as this morning's bc20 run, with a bc21 block (`#bc21-votes`,
`#bc21-units`, `#bc21-influence`, `#bc21-doctrines`, `#bc21-bids`) appended beside the bc20 one
rather than substituted — both year blocks are present in the same shell, which is what the
year-module design promised. Attempt 3's control screenshot proves it directly: the *same*
bundle renders the bc20 replay with the bc20 water pill, the bc20 endcard and the bc20
doctrines cards. This is not the cogame-gridlock failure; it is the family shell with a second
year block added.

**Two legibility observations for the coordinator** (neither is item 8's cause; both are
phase-30 material):
1. *Top-centre collision.* The bc21 votes pill (`Clan Ash 1 ▬▬ Clan Basil · 751 to clinch`) is
   drawn over the match clock, so `2:05` reads through it as a smeared amber `05` and both are
   hard to read. The same collision appears in the bc20 control screenshot (`WATER 2.00 …` over
   `FINAL`), so it is inherited shared-chrome behaviour rather than new to bc21 — but it is
   still the most prominent readout on the page being illegible.
2. *Bottom-right stacking.* The fourth killfeed line (`Game 1 begins on Bog`) is drawn over the
   unit-tally strip (`Clan Basil Po 0 Sl 1 Mu 2 ×1,000`), so both are unreadable where they
   overlap. This is the same corner the r1 review's F1/`--statrail` work targeted; the rail
   itself (`influence / income / centres`) is clear, only the feed's last line collides with the
   tally line above it.

---

## What is false, and what to do about it

Item 8 only. `loaded: true` twice over on both signals, no `failure`, a legible screenshot that
matches the replay event-for-event — but the required proof that the replay **advances** was
never obtained, because this replay's viewer Worker does not move past round 5 or answer a
scrub click inside the harness's observation window. A control run through the same shell on a
replay ~16× cheaper to simulate (0.598 s vs 9.361 s) seeks perfectly, so the shell's seek machinery and the (already-fixed)
scrub-target selector are both sound. I did not mark it true, and I did not touch the harness or
the coworld. The judge's call is whether that is a coworld performance defect, a
coworld-builder instrument limit, or both.
