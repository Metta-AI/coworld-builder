# VERIFY — fruit-market   (2026-08-25T23:45Z)

Verdict: **all-true** (8/8)

Run: `2026-08-25-fruit-market` · coworld `cow_4a33390e-40e5-4bfc-826a-d2987347d8a8` v0.1.0 ·
league `league_758061e3-46cb-49db-aef0-a28fb10ba80e` · division `div_794ae52e-812a-4ad9-be2f-b4da9ae25a7f`.
All fetches below were made fresh during this phase-60 pass (23:37Z–23:41Z), except the two
documented exceptions: check 7 reads the committed `runs/2026-08-25-fruit-market/release-result.json`,
and check 8 reads the artifact of the `viewer-check.yml` run **this** pass dispatched (32911662736).

Headers sent on every Observatory call: `Authorization: Bearer $SOFTMAX_TOKEN` (value never
printed), `User-Agent: coworld-builder/1.0`; plus `X-Use-Elevated-Privileges: true` on
`artifacts/logs` and `filler-policies` reads.

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

```
GET https://softmax.com/api/observatory/v2/rounds?league_id=league_758061e3-46cb-49db-aef0-a28fb10ba80e&limit=20
```
(response is a bare array; `jq 'if type=="array" then . else .entries end'`)

```json
[
  {
    "id": "round_92b46dc0-bde6-43d4-8a1e-c981885a1b79",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-25T23:30:32.360592Z",
    "completed_at": "2026-08-25T23:36:00.621985Z",
    "entrants": [
      {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
       "policy_version_id": "7f91e5ee-5342-4dfa-8e8d-0e589bec4916",
       "league_policy_membership_id": "lpm_dbdb4eca-24a3-43fb-832e-d80b2af113bc"},
      {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
       "policy_version_id": "7a501e7e-9f8e-40f9-8c5c-cc511a5c4104",
       "league_policy_membership_id": "lpm_32cece97-c0c1-4866-9e96-f192307d2818"}
    ]
  },
  {
    "id": "round_fbba2cf3-68cc-4a67-9ea2-d5fc4f5a6e8e",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-25T23:15:29.708258Z",
    "completed_at": "2026-08-25T23:22:57.618993Z",
    "entrants": [
      {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
       "policy_version_id": "7f91e5ee-5342-4dfa-8e8d-0e589bec4916",
       "league_policy_membership_id": "lpm_dbdb4eca-24a3-43fb-832e-d80b2af113bc"},
      {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
       "policy_version_id": "7a501e7e-9f8e-40f9-8c5c-cc511a5c4104",
       "league_policy_membership_id": "lpm_32cece97-c0c1-4866-9e96-f192307d2818"}
    ]
  },
  {
    "id": "round_b02e405a-9c62-474c-b8c0-a1cc8dc82f84",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-25T23:15:00.919553Z",
    "completed_at": "2026-08-25T23:15:01.180523Z",
    "entrants": [
      {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
       "policy_version_id": "7f91e5ee-5342-4dfa-8e8d-0e589bec4916",
       "league_policy_membership_id": "lpm_dbdb4eca-24a3-43fb-832e-d80b2af113bc"}
    ]
  }
]
```

```
$ jq -r 'if type=="array" then . else .entries end | [.[]|select(.status=="completed")]|length'
2
```

**Fillers-were-set-first, proved from the round contents rather than from a log timestamp.**
The filler roster is registered on the league:

```
GET /leagues/$L/filler-policies      (headers: Authorization, User-Agent, X-Use-Elevated-Privileges)
HTTP 200
```
```json
{"filler_policy_versions": [
  {"policy_version_id": "65e8754a-90c1-4984-8440-bb0ca29420d3", "policy_name": "fruit-market-hauler",
   "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"},
  {"policy_version_id": "0e4a0b4f-2325-49ba-be18-5cbbd7de9680", "policy_name": "fruit-market-homesteader",
   "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"}
]}
```

and both completed rounds actually **seated** those fillers (round 2's episode request, fetched
fresh):

```
GET /episode-requests/ereq_174442dd-6b44-4879-85b8-85331b43747a
```
```json
{"status":"completed",
 "replay_url":"https://softmax-public.s3.amazonaws.com/replays/4f7f01f6-0883-4848-aee9-614fef306052.replay",
 "participants":[
  {"position":0,"policy_name":"fruit-market-broker","player_name":"daveey","is_filler":false},
  {"position":1,"policy_name":"fruit-market-ricardo","player_name":"daveey-1","is_filler":false},
  {"position":2,"policy_name":"fruit-market-hauler","player_name":"daveey","is_filler":true},
  {"position":3,"policy_name":"fruit-market-hauler","player_name":"daveey","is_filler":true},
  {"position":4,"policy_name":"fruit-market-homesteader","player_name":"daveey","is_filler":true},
  {"position":5,"policy_name":"fruit-market-homesteader","player_name":"daveey","is_filler":true},
  {"position":6,"policy_name":"fruit-market-homesteader","player_name":"daveey","is_filler":true},
  {"position":7,"policy_name":"fruit-market-hauler","player_name":"daveey","is_filler":true}]}
```

A round cannot seat a filler that was not registered when it was scheduled, so rounds 2 and 3 are
both post-filler. Round 3's participant list (pasted under check 3) is the same shape.

**Failed round recorded verbatim, as required:** round 1
(`round_b02e405a-9c62-474c-b8c0-a1cc8dc82f84`, `round_number: 1`) — `error`:
`"Temporal RoundWorkflow failed before settling the round."`. It was created at
23:15:00.919553Z and failed 0.26 s later, i.e. the league's automatic first trigger fired before
the filler POST landed — the exact failure `playbooks/observatory-api.md` §6 documents for a
`trigger-round` issued before any filler exists. It is `failed`, so it does not count toward the
two, and it is not one of the rounds under test.

Status: **TRUE** — rounds 2 (`round_fbba2cf3-68cc-4a67-9ea2-d5fc4f5a6e8e`, completed
2026-08-25T23:22:57Z) and 3 (`round_92b46dc0-bde6-43d4-8a1e-c981885a1b79`, completed
2026-08-25T23:36:00Z) are `completed`, both `round_number ≥ 2`, both seated the registered fillers.

---

## 2. Both champions ranked; fillers absent or Baseline — TRUE

```
GET https://softmax.com/api/observatory/v2/divisions/div_794ae52e-812a-4ad9-be2f-b4da9ae25a7f/leaderboard
```
(bare list, not `.entries`)

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
    "policy_label": "fruit-market-broker:v1",
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
    "policy_label": "fruit-market-ricardo:v1",
    "recent_rounds": null
  }
]
```

```
$ jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
1  daveey    fruit-market-broker:v1    1030.5304984710244  2  2
2  daveey-1  fruit-market-ricardo:v1    969.4695015289755  2  0
```

Status: **TRUE** — `daveey` (`fruit-market-broker:v1`) rank 1 and `daveey-1`
(`fruit-market-ricardo:v1`) rank 2, each `rounds_played = 2 ≥ 1`. The two filler policies
(`fruit-market-hauler:v1`, `fruit-market-homesteader:v1`) are **absent** from the leaderboard
entirely — the permitted outcome ("fillers absent or `policy_label` starting `Baseline`"); in the
episode they are renamed `Baseline`…`Baseline (6)` (see check 4's `results.names`).

---

## 3. Latest round's episode request completed with a replay — TRUE

Latest completed round = `round_92b46dc0-bde6-43d4-8a1e-c981885a1b79` (round_number 3, max of the
completed set in check 1).

```
GET /episode-requests?round_id=round_92b46dc0-bde6-43d4-8a1e-c981885a1b79&limit=20
```
```json
[{"id":"ereq_acad5282-4127-48b2-8377-43a4bb528db2","status":"completed"}]
```

```
GET /episode-requests/ereq_acad5282-4127-48b2-8377-43a4bb528db2
$ jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/8bc52824-0664-410c-8caf-3abc9469e4e4.replay",
  "participants": [
    {"position": 0, "kind": "policy", "policy_version_id": "7f91e5ee-5342-4dfa-8e8d-0e589bec4916",
     "policy_name": "fruit-market-broker", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "is_filler": false, "is_seed": false},
    {"position": 1, "kind": "policy", "policy_version_id": "7a501e7e-9f8e-40f9-8c5c-cc511a5c4104",
     "policy_name": "fruit-market-ricardo", "version": 1,
     "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
     "is_filler": false, "is_seed": false},
    {"position": 2, "policy_version_id": "0e4a0b4f-2325-49ba-be18-5cbbd7de9680",
     "policy_name": "fruit-market-homesteader", "player_name": "daveey", "is_filler": true},
    {"position": 3, "policy_version_id": "65e8754a-90c1-4984-8440-bb0ca29420d3",
     "policy_name": "fruit-market-hauler", "player_name": "daveey", "is_filler": true},
    {"position": 4, "policy_version_id": "65e8754a-90c1-4984-8440-bb0ca29420d3",
     "policy_name": "fruit-market-hauler", "player_name": "daveey", "is_filler": true},
    {"position": 5, "policy_version_id": "65e8754a-90c1-4984-8440-bb0ca29420d3",
     "policy_name": "fruit-market-hauler", "player_name": "daveey", "is_filler": true},
    {"position": 6, "policy_version_id": "65e8754a-90c1-4984-8440-bb0ca29420d3",
     "policy_name": "fruit-market-hauler", "player_name": "daveey", "is_filler": true},
    {"position": 7, "policy_version_id": "0e4a0b4f-2325-49ba-be18-5cbbd7de9680",
     "policy_name": "fruit-market-homesteader", "player_name": "daveey", "is_filler": true}
  ],
  "participant_scores": [
    {"position": 0, "score": 30.0}, {"position": 1, "score": 0.0},
    {"position": 2, "score": 52.0}, {"position": 3, "score": 36.0},
    {"position": 4, "score": 33.0}, {"position": 5, "score": 54.0},
    {"position": 6, "score": 135.0}, {"position": 7, "score": 52.0}
  ]
}
```

(The filler rows are trimmed to the fields that matter; every one carries
`"kind":"policy","version":1,"is_seed":false` like positions 0–1.)

Status: **TRUE** — `status == "completed"`, non-null `replay_url`, and the participant list names
`daveey` (seat 0, `fruit-market-broker:v1`) and `daveey-1` (seat 1, `fruit-market-ricardo:v1`)
with the other six seats `is_filler: true`, rendered `Baseline`…`Baseline (6)` in the replay.

Observation, not a check failure: seat 1 (`daveey-1` / ricardo) scored **0.0** here and 0 in round
2 as well — see the spectator judgment in check 8.

---

## 4. Replay bytes are valid and show the game — TRUE

```
GET https://softmax-public.s3.amazonaws.com/replays/8bc52824-0664-410c-8caf-3abc9469e4e4.replay  -o /tmp/ep.replay
-rw-r--r-- 1 root root 332562 Aug 25 23:37 /tmp/ep.replay
$ file /tmp/ep.replay
/tmp/ep.replay: JSON text data
```

**Strict UTF-8 JSON parse** (jq, not a browser):
```
$ jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok
```

**Protocol and ending** (manifest protocol is `fruit-market.replay.v1`):
```
$ jq -r '.protocol, .results.reason, .results.ending' /tmp/ep.replay
fruit-market.replay.v1
complete
round_limit
```
`reason == "complete"` — no `deadline` exception needed. `ending == "round_limit"`, one of the
design's legal endings (round_limit / famine / deadline / forfeit).

**Top-level keys and seat map:**
```
$ jq -r 'keys' /tmp/ep.replay
["beats","colors","config","events","farmTypes","frames","game","gameVersion","names",
 "policyNames","protocol","results","seed","series"]
$ jq -c '.policyNames, .names' /tmp/ep.replay
["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)","Baseline (5)","Baseline (6)"]
["Ash","Bram","Cedar","Dune","Elm","Fern","Gale","Holt"]
```
Champion seats are **0 (`daveey`/broker, alias Ash)** and **1 (`daveey-1`/ricardo, alias Bram)** —
cross-checked against check 3's `participants[].position`.

**Champion decisions are LLM, not fallbacks.** This replay keys decision rows `k=="order"` with a
`source` field:
```
$ jq -r '[.events[]|select(.k=="order")|.source]|group_by(.)|map("\(.[0]): \(length)")|join(", ")'
llm: 24, scripted: 72
$ jq -r '[.events[]|select(.k=="order" and (.seat==0 or .seat==1))|.source]|group_by(.)|map("\(.[0]): \(length)")|join(", ")'
llm: 24
$ jq -r '[.events[]|select(.k=="order" and (.seat==0 or .seat==1) and (.source=="fallback"))]|length'
0
$ jq -r '[.events[]|select(.fallback==true)]|length'
0
```
**24 of 24** champion orders are `source: "llm"`; **zero** `retry`, **zero** `fallback`, **zero**
`scripted`. The 72 `scripted` rows are the six filler seats, which is what they are supposed to be.
(The spec's literal `select(.type=="decision")` / `select(.fallback==true)` probes both return 0
because this protocol names the field `k`/`source`; the equivalent queries are the ones above.)

**Decision content is non-trivial** (the `say` string a spectator reads):
```
$ jq -r '[.events[]|select(.k=="order" and (.seat==0 or .seat==1))|(.say|length)]|{min,max,mean:(add/length)}'
{"min": 58, "max": 80, "mean": 77.75}
```

**The champions actually play the game — ordered champion orders (t, seat, source, job, fruit, offer, say):**
```
0	0	llm	harvest	banana	-	Round 1: harvesting bananas to build inventory for trading
0	1	llm	harvest	apple	-	Starting fresh: harvesting apples to build stock. Will trade at market once I h…
60	0	llm	market	banana	3banana->2apple	Book price: 3 bananas for 2 apples. Market maker at west stall.
60	1	llm	harvest	apple	-	Round 2: Harvesting apples in grove. Have 12 apples, need to build stock before…
120	0	llm	market	banana	3banana->2apple	Market maker at west stall, book price 3 bananas for 2 apples. Hunger dropping …
120	1	llm	market	apple	6apple->4banana	Heading to south stall with 6-for-4 offer. Have 12 apples at cap, hunger stable…
180	0	llm	market	banana	3banana->2apple	Book price at west stall: 3 bananas for 2 apples. Hunger critical, ready to tra…
180	1	llm	market	banana	6apple->4banana	At south stall with 12 apples, posting 6-for-4. Hunger critical at 16, need tra…
240	0	llm	market	banana	3banana->2apple	Book price at west stall: 3 banana for 2 apple. Apple farmers, come trade!
240	1	llm	market	apple	6apple->4banana	Hunger critical at 1/100. At south stall with 6-for-4 posted. Need to clear thi…
300	0	llm	market	banana	3banana->2apple	Market maker at west stall. Standing offer: 3 banana for 2 apple. Book price ho…
300	1	llm	rest	apple	-	Critical state: hunger 0, stamina 0. Must rest to regenerate stamina before any…
360	0	llm	market	banana	3banana->2apple	Posting book price at west stall. 4 bananas, 2 reserved. Hunger 51, need trades…
360	1	llm	rest	apple	-	Critical condition: hunger 0, stamina 0. Must rest to regenerate stamina before…
420	0	llm	market	banana	3banana->2apple	Book price at west stall. Fern nearby with inverse offer - waiting for executio…
420	1	llm	rest	apple	-	Stamina critically depleted at 0/100. Must rest to recover before any action po…
480	0	llm	market	banana	2banana->3apple	Market maker at west stall. Mirroring book price: 2 banana for 3 apple.
480	1	llm	rest	apple	-	Stamina critically low at 0/100. Must rest to recover before any action. Have 1…
540	0	llm	market	banana	3banana->2apple	Book price standing at west stall. Dune at (5,10) offers give 3 apple want 2 ba…
540	1	llm	rest	apple	-	Stamina 0/100, hunger 0/100 - stuck. Resting to regenerate. Have 12 apples read…
600	0	llm	harvest	banana	3banana->2apple	Harvesting bananas to fund my standing offer. Dune nearby with inverse offer bu…
600	1	llm	rest	apple	-	Stamina 0/100, hunger 0/100. Must rest to regenerate. Once stamina >0, will pos…
660	0	llm	market	banana	3banana->2apple	Market maker at west stall. Posting book price mirror: give 3 banana want 2 app…
660	1	llm	rest	apple	6apple->4banana	Stamina at 0, hunger at 0. Resting to recover. Posted 6 apples for 4 bananas at…
```
These are barter decisions with prices in them — harvest → post an offer at the book price
(3-for-2) → walk to a stall → execute. Not scripted, not degenerate.

**The market clears** (champion seat 0 among the counterparties):
```
$ jq -c '[.events[]|select(.k=="trade")][0:4]' /tmp/ep.replay
[{"k":"trade","t":83,"a":4,"b":6,"aGive":"apple","aGiveN":3,"bGive":"banana","bGiveN":2,"applesPerBanana":150,"x":20,"y":4,"dist":3},
 {"k":"trade","t":120,"a":4,"b":6,"aGive":"apple","aGiveN":3,"bGive":"banana","bGiveN":2,"applesPerBanana":150,"x":18,"y":4,"dist":1},
 {"k":"trade","t":180,"a":3,"b":6,"aGive":"apple","aGiveN":3,"bGive":"banana","bGiveN":2,"applesPerBanana":150,"x":26,"y":6,"dist":1},
 {"k":"trade","t":240,"a":5,"b":6,"aGive":"apple","aGiveN":3,"bGive":"banana","bGiveN":2,"applesPerBanana":150,"x":26,"y":8,"dist":1}]
$ jq -c '[.events[]|select(.k=="trade" and (.a==0 or .b==0))]' /tmp/ep.replay
[{"k":"trade","t":480,"a":0,"b":5,"aGive":"banana","aGiveN":2,"bGive":"apple","bGiveN":3,"applesPerBanana":150,"x":5,"y":8,"dist":1}]
```

**Event census and results:**
```
$ jq -r '[.events[]|.k]|group_by(.)|map({k:.[0],n:length})' /tmp/ep.replay
cross 54 · eat 162 · end 1 · exhausted 1 · harvest 103 · offer 56 · order 96 ·
round 12 · spill 17 · starve 1 · trade 11 · unfunded 5 · withdraw 1
$ jq -c '.results' /tmp/ep.replay
{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)","Baseline (5)","Baseline (6)"],
 "aliases":["Ash","Bram","Cedar","Dune","Elm","Fern","Gale","Holt"],
 "farm_types":["banana","apple","banana","apple","apple","apple","banana","banana"],
 "scores":[30,0,52,36,33,54,135,52],"win":[false,false,false,false,false,false,true,false],
 "craved_eaten":[3,0,6,6,6,10,27,6],"own_eaten":[15,0,22,6,3,4,0,22],
 "harvested":[26,12,32,21,18,31,24,32],"trades":[1,0,0,3,3,5,10,0],"volume":[2,0,0,9,9,15,20,0],
 "crossings":[3,1,9,5,4,6,5,10],"starving_ticks":[0,480,0,0,0,0,0,0],
 "mean_rate_x100":150,"total_trades":11,"rounds":12,"reason":"complete","ending":"round_limit"}
```

Status: **TRUE** — strict-parser-valid UTF-8 JSON (332 562 bytes); `protocol` =
`fruit-market.replay.v1`, matching the manifest; `results.reason == "complete"` (no `deadline`
exception invoked); champion seats' 24/24 orders are `source: "llm"` with 0 fallbacks and 58–80
character reasoning strings; 11 trades cleared at a mean 1.50 apples per banana.

---

## 5. Hosted game log is clean — TRUE (CLEAN)

```
GET /episode-requests/ereq_acad5282-4127-48b2-8377-43a4bb528db2/artifacts/logs
     (headers: Authorization, User-Agent, X-Use-Elevated-Privileges)
HTTP 200  bytes 52442
```

The body is python byte-string reprs under `===== container: … =====` headers, so it was decoded
per repr with `ast.literal_eval` before grepping (playbook §10 — a line-based grep on the raw body
undercounts):

```
$ python3 …decode…                       # 52 275 bytes decoded, 151 lines
$ grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs.txt || echo CLEAN
CLEAN
```

Zero matches for any of the four patterns. Because the grep is CLEAN, the Bedrock-429 triage path
(cross-check another LLM coworld / another in-flight run) was **not needed** and was not invoked.

Containers present in the decoded log, with excerpts proving the decode worked and the log is this
episode's:
```
1:===== container: coworld-init-config =====
3:===== container: bedrock-sidecar =====
104:===== container: game =====
151:===== container: worker =====

fruit-market: seed not pinned; randomized
fruit-market: variant=concentric-rivers seats=8 rounds=12 ticksPerRound=60 seed=1846331590
fruit-market: serving on 0.0.0.0:8080
fruit-market: player slot 6 connected (1/8)
fruit-market: player slot 3 connected (2/8)
fruit-market: slot 6 registered (0 chars, scripted hauler)
fruit-market: slot 3 registered (0 chars, scripted hauler)
fruit-market: player slot 5 connected (3/8)
…
fruit-market: artifacts written; holding /healthz and /global for 20s
fruit-market: episode complete, shutting down
```

Status: **TRUE** — CLEAN; no `falling back`, no `LLM provider is unavailable`, no
`cut off at max_tokens`, no `rejected`.

---

## 6. The public page uses the static replay path — TRUE

**Source used: the SSR payload of `https://softmax.com/fruit-market` for the featured match, plus
`POST /coworlds/replays/session` for the iframe `src`** — i.e. the documented client-rendered
fallback, not the raw-HTML grep.

Attempt 1 — raw-HTML grep (the spec's first command):
```
$ curl -sS "https://softmax.com/fruit-market" -o page.html   # HTTP 200, 563573 bytes
$ grep -o '<iframe[^>]*src="[^"]*"' page.html || echo "NO IFRAME IN RAW HTML"
NO IFRAME IN RAW HTML
```
Not a false negative: the page is client-rendered for the iframe (playbook §Featured match,
lighthouse run 2026-08-22). Recorded as *unknown*, not as failure.

Attempt 2 — `/coworlds` detail (the spec's stated fallback), for completeness:
```
$ curl -sS "$BASE/coworlds?limit=200" … | jq -r '…|select(.name=="fruit-market")|{id,canonical,replay_viewer,featured_match}'
{"id":"cow_4a33390e-40e5-4bfc-826a-d2987347d8a8","name":"fruit-market","canonical":true,
 "replay_viewer":null,"featured_match":null}
```
`featured_match: null` here is the known platform-wide value and is **not** evidence of absence
(playbook §Featured match, "Answered"). The real featured match is server-rendered into the page's
SSR payload:

**Featured match — from `page.html`, SSR `state.playlist[0]` (unescaped from the RSC payload):**
```json
{"leagueId":"league_758061e3-46cb-49db-aef0-a28fb10ba80e",
 "playlist":[{"episodeId":"98122b18-50f3-4ffc-9df6-55cf65c7410b",
   "coworldId":"cow_4a33390e-40e5-4bfc-826a-d2987347d8a8",
   "coworldName":"fruit-market","coworldVersion":"0.1.0",
   "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/8bc52824-0664-410c-8caf-3abc9469e4e4.replay",
   "finishedAt":"2026-08-25T23:35:56.667253Z","roundNumber":3,"episodeNumber":1,
   "code":"fruit-market.r3.e1",
   "matchup":{"divisionId":"div_794ae52e-812a-4ad9-be2f-b4da9ae25a7f","divisionName":"Competition",
     "first":{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3",…
```
…and the same payload carries the standings:
```json
"divisionName":"Competition","divisionCount":1,"playerCount":2,"activeRound":null,
"newestCompletedAt":"2026-08-25T23:36:00.621985Z",
"firstPlace":{"current":{"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
  "started_at":"2026-08-25T23:22:57.624555Z","rounds_held":2,…
```
A featured match **is** present: `fruit-market.r3.e1`, the round-3 episode from check 3, with a
two-player matchup.

**The iframe `src` — the exact call the page's own JS makes:**
```
POST https://softmax.com/api/observatory/v2/coworlds/replays/session
     content-type: application/json
     {"coworld_id":"cow_4a33390e-40e5-4bfc-826a-d2987347d8a8",
      "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/8bc52824-0664-410c-8caf-3abc9469e4e4.replay"}
HTTP 200
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_4a33390e-40e5-4bfc-826a-d2987347d8a8/sha256%3A041ac84194867475b2adf8e02ac063e464e18fffc06935dda742a7676e1d3626/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F8bc52824-0664-410c-8caf-3abc9469e4e4.replay&v=2",
  "ready": true
}
```

Path check, term by term:
`/v2/coworlds/replays/**static**/` + `cow_4a33390e-40e5-4bfc-826a-d2987347d8a8` (the run's cow_id) +
`sha256%3A041ac8…3626` (URL-encoded `manifest_sha` from STATE, exactly
`sha256:041ac84194867475b2adf8e02ac063e464e18fffc06935dda742a7676e1d3626`) + `/index.html` +
`?replay=<s3 url>`. `ready: true`. **No `/client/replay` pod URL anywhere.**

Status: **TRUE** — featured match present (`fruit-market.r3.e1`), iframe `src` is the static route
with the correct cow_id and manifest hash, ending `/index.html?replay=<s3 url>`.

---

## 7. Certification declared the static bundle — TRUE

**Source: the committed `runs/2026-08-25-fruit-market/release-result.json`** (the artifact phase 40
downloaded and committed). It was present, so no `gh run download` re-fetch was needed.

```
$ jq -r '.certify.replay_liveness' runs/2026-08-25-fruit-market/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE** — contains `Replay liveness: skipped (static replay bundle declared`, read from
the committed copy (not `/tmp`).

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — TRUE

**(a) Dispatch.** The `url` input is the *verbatim* iframe `src` from check 6, `?replay=` and all.

```
$ SRC=$(jq -r .viewer_url session.json)
$ gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
   dispatched 2026-08-25T23:38:22Z
$ gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
   | jq -c 'sort_by(.createdAt)|reverse|.[0:3][]'
{"conclusion":"","createdAt":"2026-08-25T23:38:22Z","databaseId":32911662736,"status":"in_progress"}
{"conclusion":"success","createdAt":"2026-08-25T22:53:05Z","databaseId":32908246409,"status":"completed"}
{"conclusion":"success","createdAt":"2026-08-25T22:17:31Z","databaseId":32905429599,"status":"completed"}
```
The new run is the one whose `createdAt` (23:38:22Z) equals the dispatch instant — found by sorting
on `createdAt`, not by taking "the latest" blind. The next-newest viewer-check run predates the
dispatch by 45 minutes and belongs to another run.

```
$ gh run watch 32911662736 -R Metta-AI/coworld-builder --exit-status     # exit 0
$ gh run view 32911662736 --json conclusion,status,displayTitle
{"conclusion":"success","status":"completed","displayTitle":"viewer-check"}
$ gh run download 32911662736 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-25-fruit-market/viewer-check
-rw-r--r-- 1 root root      0 smoke-stderr.txt
-rw-r--r-- 1 root root    563 smoke-stdout.txt
-rw-r--r-- 1 root root   1359 viewer-smoke.json
-rw-r--r-- 1 root root 712401 viewer-smoke.png
```
`runs/2026-08-25-fruit-market/viewer-check/` is committed alongside this file.

**(b) Readouts, verbatim.**

```
$ jq -c '{loaded, ms, clock, scorebug, feed_lines}' viewer-smoke.json
{"loaded":true,"ms":5101,"clock":"ROUND 1 / 12 TICK 0 OF 719","scorebug":"APPLE FARMERS SCORE 0 0 trades · 1.50 🍎/🍌 ROUND 1 / 12 TICK 0 OF 719 BANANA FARMERS SCORE 2 0 trades · 1.50 🍎/🍌","feed_lines":0}

$ jq -c '.signals' viewer-smoke.json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}

$ jq -r '.failure // "no failure"' viewer-smoke.json
no failure
```
Also from the same file: `"status":"OPEN"`, `"loading_text":null`, `"console_tail":[]`,
`"canvas_text":{"total":0,"outside":0,"ellipsized":0,"never_inside":0,…}` (0 canvas-drawn text
strings, so 0 crossed an edge and 0 were ellipsized — the chrome is DOM, not canvas text).

**The three clock readouts** (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub | clock |
|---|---|
| 0 % | `ROUND 1 / 12 TICK 0 OF 719` |
| 50 % | `ROUND 7 / 12 TICK 375 OF 719` |
| 100 % | `FINAL MARKET CLOSED` |

All three **differ**, and they differ in the right direction: tick 0 → tick 375 of 719 → the end
card. Together with `loaded: true` (via `data-replay-loaded="true"`; the `coworld-replay` bridge
was not used, `bridge_ready:false`, and the shell does not need it) both conditions for check 8 hold.

**(c) The replay JSON the viewer was asked to draw** — early, middle, late, from `/tmp/ep.replay`:

*early (t = 0):* every seat issues its opening order and the first harvests/offers land
```
0	0	order	Round 1: harvesting bananas to build inventory for trading
0	1	order	Starting fresh: harvesting apples to build stock. Will trade at market once I h…
0	2	order	I grow my own
0	3	order	3 apples for 2 bananas
0	6	order	2 bananas for 3 apples
0	7	order	I grow my own
0	0	harvest	 / 0 2 harvest / 0 5 harvest / 0 6 harvest / 0 7 harvest
0	3	offer	 / 0 4 offer / 0 5 offer / 0 6 offer
0	3	unfunded	 / 0 4 unfunded
0	2	eat	 / 0 7 eat
```

*middle — the spine of the episode (trades, and seat 1's collapse):*
```
83	-	trade	   120	-	trade	   180	-	trade	   240	-	trade
240	1	starve
289	1	exhausted
300	1	withdraw
300	-	trade	   360	-	trade	   430	-	trade	   480	-	trade
540	-	trade	   600	-	trade	   660	-	trade
```

*late (last 20 events):*
```
660	-	trade	  665 5 harvest	  668 0 cross	  672 2 eat	  672 3 eat	  672 7 eat
677	5	harvest	  679 0 eat	  683 6 eat	  689 5 harvest	  696 2 eat	  696 3 eat
696	7	eat	  703 0 eat	  705 5 harvest	  707 6 eat	  717 5 harvest	  717 5 spill
720	-	round	  719 - end
$ jq -c '[.events[]|select(.k=="end")]' /tmp/ep.replay
[{"k":"end","t":719,"reason":"complete","ending":"round_limit","scores":[30,0,52,36,33,54,135,52]}]
```

### Spectator-judgment paragraph

**It is legible, it advances, and it shows this game.** `viewer-smoke.png` (committed) is the frame
after the scrub to 100 %, so it is the end card over the live board. Top strip: a two-team scorebug
— `APPLE FARMERS 123` on the left, `BANANA FARMERS 269` on the right, each with a small inventory
row of 🍎/🍌 chips and the line `11 trades · 1.50 🍎/🍌` — and a centred `FINAL / MARKET CLOSED`
clock. Below it a roster strip of all eight cogs with live scores: `GALE Baselin… 135`,
`FERN Baselin… 54`, `CEDAR Base… 52`, `HOLT Baselin… 52`, `DUNE Baselin… 36`, `ELM Baseline… 33`,
`ASH dav… 30`, `BRAM dave… 0` — the champions are named and rank-ordered in the picture, and every
number matches `results.scores` = `[30,0,52,36,33,54,135,52]` seat-for-seat. The end card reads
`GALE WINS`, tagged `ROUND LIMIT`, `winner Baseline (5) on 135 points`, with per-team panels
(APPLE 123 / BANANA 269 and their four members each — the two team totals are exactly the sums of
the replay's per-seat scores split by `farm_types`) and a one-line summary:
`Ash 30 · Bram 0 · Cedar 52 · Dune 36 · Elm 33 · Fern 54 · Gale 135 · Holt 52 — 11 trades · mean
1.50 apples per banana · 1 cog starved`. That last clause is the picture reporting seat 1's
`starving_ticks: 480` and the `starve`/`exhausted`/`withdraw` events at t = 240/289/300 — the
screenshot and the record agree. Behind the dimmed end card the board itself is visible: the
concentric-rivers map with the four labelled market stalls (`WEST`, `NORTH`, `SOUTH`, `EAST`, each
drawn as a striped market awning), named cogs standing on it (`ASH`, `CEDAR`, `DUNE`, `ELM`,
`FERN`, `HOLT`, `GALE`), each carrying a small horizontal condition bar above its head, and
floating offer bubbles written in fruit glyphs — `3🍌 → 2🍎` above **ASH** at the west stall (seat
0, the broker champion, exactly the standing offer its t = 660 order posts), `6🍎 → 4🍌` at the
south stall under an **`EXHAUSTED`** badge (seat 1, Bram/ricardo — the badge is the `exhausted`
event at t = 289 rendered on the board), and `3🍎 → 2🍌` on the east side. You can read what is
being offered without any prose. On the right edge sits the **order book** panel, verified by
zooming into the png: `BRAM 6🍎 → 4🍌 south · ASH 3🍌 → 2🍎 west · ELM 3🍎 → 2🍌 east ·
FERN 3🍎 → 2🍌` — who is quoting what, and at which stall. Along the bottom is the starter's transport strip — restart, step-back, play,
`+5s`, step-forward, loop, fast-forward, a `spoilers` toggle, the outcome chip `BANANA WINS`,
`719 / 719`, and the `1× 2× 3× 4× 8× 16×` speed rail — over the scrubber with tick markers and,
under it, the `APPLES PER BANANA` momentum graph. That is the paintbot/raid/hive chrome, not a
lookalike rewrite: transport strip, scrubber + momentum graph, scorebug and endcard are all in
their expected places, and this is the same shell the CTF starter ships. **It advances**: the three
scrub readouts move from round 1 tick 0 through round 7 tick 375 to the closed market, so it is a
replay and not a screenshot. Does it show *who is winning and why*? Yes — the scorebug gives the
two team totals and the trade count and the live exchange rate, the roster strip ranks all eight
cogs, the offer bubbles and order book show the quotes that produce those points, and the end card
names the winner and the ending condition.

Two legibility observations for the coordinator (neither is a check failure, both are phase-30
material rather than a phase-60 verdict):

1. `feed_lines: 0` — the smoke run found no event-feed lines in the DOM at the sampled moments.
   The `say` strings the champions produce (58–80 characters each, quoted in check 4) are therefore
   not visibly surfaced as a running feed in this shell; the reasoning is in the replay but not on
   screen. The picture is still legible without it, because the offer bubbles and order book carry
   the same information graphically.
2. The end-card team panels label the score column **`LIVES LEFT`** and carry four all-zero columns
   headed **`K`, `D`, `CLSTR`, `CAP`** — unmapped labels inherited from the `coworld-ctf` starter.
   They are harmless (all zeros) but they are wrong words for a barter game, and a first-time
   spectator will read "123 LIVES LEFT" for what is a fruit score.

3. Gameplay note, not a viewer issue: champion #2 (`fruit-market-ricardo`, seat 1 / Bram) starved
   at t = 240 and rested at hunger 0 / stamina 0 for the last eight rounds, scoring **0 in both**
   completed rounds (round 2 and round 3). The design's checks are all satisfied — its orders are
   LLM, its offers are posted, the reason is `complete` — but the prompt appears to trade away or
   withhold food until it collapses. Worth a look before the next release.

Status: **TRUE** — `loaded: true` (`data_replay_loaded: "true"`, `failure: null`, first frame at
5 101 ms) **and** the three clock readouts differ.

---

## Summary

| # | Check | Verdict | Key evidence |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers | **TRUE** | rounds 2 `round_fbba2cf3…` @23:22:57Z, 3 `round_92b46dc0…` @23:36:00Z; both seated the registered fillers; round 1 `failed` (pre-filler race) excluded |
| 2 | Both champions ranked | **TRUE** | daveey `fruit-market-broker:v1` rank 1 (2 rounds), daveey-1 `fruit-market-ricardo:v1` rank 2 (2 rounds); fillers absent |
| 3 | Latest round's episode completed w/ replay | **TRUE** | `ereq_acad5282-4127-48b2-8377-43a4bb528db2` completed, replay_url set, seats 0/1 = daveey/daveey-1, 6 `is_filler` seats |
| 4 | Replay bytes valid, show the game | **TRUE** | strict JSON ok; `fruit-market.replay.v1`; `reason=complete`, `ending=round_limit`; champion orders 24/24 `source=llm`, 0 fallback; 11 trades @1.50 🍎/🍌 |
| 5 | Hosted log clean | **TRUE** | decoded 52 275 bytes, grep of all four patterns → `CLEAN`; no Bedrock triage needed |
| 6 | Static replay path + featured match | **TRUE** | SSR `playlist[0]` = `fruit-market.r3.e1`; session POST → `.../replays/static/cow_4a33…/sha256%3A041ac8…/index.html?replay=…`, `ready:true`; no `/client/replay` |
| 7 | Certification declared static bundle | **TRUE** | committed `release-result.json`: `Replay liveness: skipped (static replay bundle declared; …)` |
| 8 | Viewer executed and judged | **TRUE** | run 32911662736 (success): `loaded:true`, 5101 ms, clocks `TICK 0` → `TICK 375` → `FINAL MARKET CLOSED` |
