# VERIFY — hidden-agenda   (2026-08-26T05:30Z, attempt 2)

Verdict: **all-true** — checks 1–8 TRUE.

This is a full re-verification after the phase-60 fix loop. Attempt 1 (2026-08-26T04:15Z) returned
checks 1, 2, 3, 6, 7, 8 TRUE and checks **4 and 5 FALSE**: 80–87.5 % of every champion decision was
a scripted fallback, caused (cause B) by `src/hidden_agenda/llm.nim`'s plan-step schema hint
`{"job":...}` omitting the `at`/`who`/`room` sibling keys the validator requires. Since then the
parse defect was fixed on `main` (`731ab43`, schema hint + compact-form tolerance), version
**0.1.2** was released canonical + certified as **`cow_962d0488-144c-48f6-b0c7-08a19ac5ed89`**, and
the champions and fillers were re-seated at **v3** at ~04:50Z. **Every fetch below is fresh, made
this run, against 0.1.2 / `cow_962d0488`.** Attempt-1 numbers appear only where explicitly labelled
as history.

Ids used throughout:

```
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_9c44cf05-76f9-4ca5-8299-0c16a5e41ed9
D=div_cb85265c-94ee-4f36-885f-f72c1e71f7e8
COW=cow_962d0488-144c-48f6-b0c7-08a19ac5ed89          # hidden_agenda 0.1.2, canonical
SHA=sha256:9b4d97318ad246f405db95efa82637091e7099250dd8d735715b579989f1741c
champion v3: sleuth  de6e647d-515c-4f91-827c-beddbf8fdf31  (daveey)
champion v3: shadow  cc10827d-9798-406c-ae06-def715154422  (daveey-1)
filler   v3: miner   59a3061c-78df-4046-92d8-78af81361d92
filler   v3: lurker  cd5bf260-f2b2-4bc2-9788-7dfd4b60836b
```

Header values are never printed; only header *names* are listed above.

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

### 1a. The v3 fillers are live on the league (fresh read; elevated header required on this read)

```
GET $BASE/leagues/$L/filler-policies   [Authorization, User-Agent, X-Use-Elevated-Privileges]
(fetched 2026-08-26T04:52:12Z)
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"59a3061c-78df-4046-92d8-78af81361d92","policy_id":"7c8ea289-49ff-4256-8b57-3d6b400cc04f","policy_name":"hidden-agenda-miner","version":3,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},
 {"policy_version_id":"cd5bf260-f2b2-4bc2-9788-7dfd4b60836b","policy_id":"d311a90e-e0a9-4282-a705-a384fd4559b6","policy_name":"hidden-agenda-lurker","version":3,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```

Both are `version: 3`, matching the ids the coordinator re-seated at ~04:50Z. Neither filler uuid
equals a champion uuid (`de6e647d-…` sleuth, `cc10827d-…` shadow). The same two ids are echoed by
the league settings embedded in every round record below as
`"filler_policy_version_ids":["59a3061c-78df-4046-92d8-78af81361d92","cd5bf260-f2b2-4bc2-9788-7dfd4b60836b"]`.

### 1b. The rounds

```
GET $BASE/rounds?league_id=$L&limit=20      (fetched 2026-08-26T05:28:31Z)
```
```json
[
 {"round_number":9,"id":"round_d1a894c7-a37d-4010-9747-afba6d950aff","status":"completed","error":null,"created_at":"2026-08-26T05:20:29.622443Z","completed_at":"2026-08-26T05:23:46.479996Z"},
 {"round_number":8,"id":"round_bed14b0b-3da0-4415-91cc-c26a9f8b92a7","status":"completed","error":null,"created_at":"2026-08-26T05:05:27.502547Z","completed_at":"2026-08-26T05:08:21.366478Z"},
 {"round_number":7,"id":"round_8e328266-84e5-4713-be4d-9dad1e3954b7","status":"completed","error":null,"created_at":"2026-08-26T04:50:27.074855Z","completed_at":"2026-08-26T04:52:19.714711Z"},
 {"round_number":6,"id":"round_f09dcd52-a3ae-4167-a350-dd51077466c5","status":"completed","error":null,"created_at":"2026-08-26T04:38:40.390722Z","completed_at":"2026-08-26T04:41:47.508307Z"},
 {"round_number":5,"id":"round_8b3656d6-f931-43aa-b9f7-3289cc69efe8","status":"completed","error":null,"created_at":"2026-08-26T04:23:39.499371Z","completed_at":"2026-08-26T04:27:04.319358Z"},
 {"round_number":4,"id":"round_6779cf17-c5c2-4c0a-b2a4-2e4e8b7936a2","status":"completed","error":null,"created_at":"2026-08-26T04:08:37.442644Z","completed_at":"2026-08-26T04:10:49.850570Z"},
 {"round_number":3,"id":"round_6f477b2c-9d25-45d3-8407-ca70172ed3ca","status":"completed","error":null,"created_at":"2026-08-26T03:53:37.037453Z","completed_at":"2026-08-26T03:55:18.848922Z"},
 {"round_number":2,"id":"round_43c151ab-64bf-4bf4-a1b5-987fdb4a706b","status":"completed","error":null,"created_at":"2026-08-26T03:38:36.314950Z","completed_at":"2026-08-26T03:41:50.440692Z"},
 {"round_number":1,"id":"round_9abab8d9-f4ac-40a6-bd41-2a35f8040ef1","status":"failed","error":"Temporal RoundWorkflow failed before settling the round.","created_at":"2026-08-26T03:38:01.987136Z","completed_at":"2026-08-26T03:38:02.732810Z"}
]
```
```
jq '[.entries[]|select(.status=="completed")]|length'  ->  8
```

### 1c. Rounds 7, 8, 9 are the post-re-seat rounds, on the 0.1.2 image with v3 champions

The three rounds this attempt relies on for checks 3/4/5 all carry the **v3 champion policy
version ids** in `round_config.entrant_attributions`. Verbatim, round 9:

```
GET $BASE/rounds/round_d1a894c7-a37d-4010-9747-afba6d950aff       (fetched 2026-08-26T05:26Z)
```
```json
{"round_number":9,"status":"completed","created_at":"2026-08-26T05:20:29.622443Z",
 "completed_at":"2026-08-26T05:23:46.479996Z",
 "entrant_attributions":[
  {"subject_id":"ply_18302115-9fc9-482d-a2f3-f4c592bf9e57","policy_version_id":"04721149-783a-490c-bd0f-c36b77ff3c11"},
  {"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","policy_version_id":"de6e647d-515c-4f91-827c-beddbf8fdf31"},
  {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","policy_version_id":"cc10827d-9798-406c-ae06-def715154422"},
  {"subject_id":"ply_ded11f40-3e30-4921-b019-f7f6bc3e9c83","policy_version_id":"d114008e-8ba4-476f-900e-4082b6f9f142"}]}
```

Round 8 (`round_bed14b0b-…`) and round 7 (`round_8e328266-…`) carry the identical
`entrant_policy_version_ids` list `["04721149-…","de6e647d-…","cc10827d-…","d114008e-…"]` — i.e.
`de6e647d` (sleuth **v3**) and `cc10827d` (shadow **v3**). By contrast round 6
(`round_f09dcd52-…`, completed 04:41:47Z, pre-re-seat) carries the **v1** ids
`7fcd857a-8a71-4c05-ad5b-15a135511646` and `d5e5ead8-3618-4efa-abac-ad91f0afc79b`, which is the
clean cut-over line between the two attempts.

The two other `subject_id`s are **not fillers**: `ply_18302115` = player `relh`
(`co-gas-hidden-agenda-miner-relhalpha:v1`) and `ply_ded11f40` = player `richard`
(`co-gas-hidden-agenda-miner-richard:v1`) — third-party submissions that joined this public league
between attempt 1 and attempt 2. They are recorded here because they change the seat layout in
checks 3 and 4.

### 1d. Poll log

```
/tmp/v2/poll.log — one line per 5-minute poll, round_number:status
2026-08-26T04:52:32Z  7:completed 6:completed 5:completed 4:completed 3:completed 2:completed 1:failed
2026-08-26T04:57:34Z  7:completed 6:completed 5:completed 4:completed 3:completed 2:completed 1:failed
2026-08-26T05:02:35Z  7:completed 6:completed 5:completed 4:completed 3:completed 2:completed 1:failed
2026-08-26T05:07:36Z  8:pending   7:completed 6:completed 5:completed 4:completed 3:completed 2:completed 1:failed
2026-08-26T05:12:37Z  8:completed 7:completed 6:completed 5:completed 4:completed 3:completed 2:completed 1:failed
2026-08-26T05:17:38Z  8:completed 7:completed 6:completed 5:completed 4:completed 3:completed 2:completed 1:failed
2026-08-26T05:22:39Z  9:pending   8:completed 7:completed 6:completed 5:completed 4:completed 3:completed 2:completed 1:failed
2026-08-26T05:27:40Z  9:completed 8:completed 7:completed 6:completed 5:completed 4:completed 3:completed 2:completed 1:failed
```

Status: **TRUE** — **8** rounds completed (2–9), all with `round_number ≥ 2`, i.e. after the
fillers were registered. Of those, **three (7, 8, 9)** completed *after the v3 re-seat* and are the
only ones used for checks 3/4/5. Round 1 `status:"failed"`,
`error:"Temporal RoundWorkflow failed before settling the round."` — the documented auto-created
pre-filler round (`playbooks/observatory-api.md` §6); it does not count and is not counted. No
round is `discarded`.

---

## 2. Both champions ranked, fillers absent/Baseline — **TRUE**

```
GET $BASE/divisions/$D/leaderboard      (fetched 2026-08-26T05:26:53Z; bare array, not .entries)
```
```json
[
 {"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
  "score":1022.2263799299311,"score_label":"MMR","rounds_played":8,"episode_wins":4.0,
  "win_rate":0.2222222222222222,"policy_label":"hidden-agenda-shadow:v3"},
 {"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
  "score":1017.7496788498975,"score_label":"MMR","rounds_played":8,"episode_wins":5.0,
  "win_rate":0.2777777777777778,"policy_label":"hidden-agenda-sleuth:v3"},
 {"rank":3,"player_id":"ply_ded11f40-3e30-4921-b019-f7f6bc3e9c83","player_name":"richard",
  "score":991.7606711857213,"score_label":"MMR","rounds_played":5,"episode_wins":4.0,
  "win_rate":0.26666666666666666,"policy_label":"co-gas-hidden-agenda-miner-richard:v1"},
 {"rank":4,"player_id":"ply_18302115-9fc9-482d-a2f3-f4c592bf9e57","player_name":"relh",
  "score":968.2632700344502,"score_label":"MMR","rounds_played":5,"episode_wins":3.0,
  "win_rate":0.2,"policy_label":"co-gas-hidden-agenda-miner-relhalpha:v1"}
]
```
```
rank  player     policy_label                            score               rounds  wins
1     daveey-1   hidden-agenda-shadow:v3                 1022.2263799299311  8       4.0
2     daveey     hidden-agenda-sleuth:v3                 1017.7496788498975  8       5.0
3     richard    co-gas-hidden-agenda-miner-richard:v1    991.7606711857213  5       4.0
4     relh       co-gas-hidden-agenda-miner-relhalpha:v1  968.2632700344502  5       3.0
```

Status: **TRUE** — both `daveey` and `daveey-1` are ranked, each with `rounds_played = 8 ≥ 1`, and
both `policy_label`s have flipped to **`:v3`**, confirming the platform is scoring the re-seated
policies. Elo has separated from the 1000.0 seed in both directions, so rounds actually scored.
**No filler row appears at all** — neither `hidden-agenda-miner` nor `hidden-agenda-lurker` is on
the board, which satisfies "fillers absent or `policy_label` starting `Baseline`". Ranks 3 and 4
are third-party player submissions (`relh`, `richard`), not fillers of this run; they are a normal
consequence of a public league and do not affect this check.

---

## 3. Latest round's episode request completed with a replay and correct participants — **TRUE**

Latest completed round at the time of this fetch is **round 9**:

```
R=$(GET $BASE/rounds?league_id=$L&limit=20 | jq '[.entries[]|select(.status=="completed")]|max_by(.round_number).id')
-> R=round_d1a894c7-a37d-4010-9747-afba6d950aff        (round_number 9, completed 05:23:46Z)
GET $BASE/episode-requests?round_id=$R&limit=20   -> EREQ=ereq_50c013dc-2b01-41bd-90df-25c3edfd0eb8
GET $BASE/episode-requests/$EREQ                  (fetched 2026-08-26T05:26:0xZ)
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/2e2bca77-137b-4c3d-b5b7-a7a15dbe07c1.replay",
  "participants": [
    {"position":0,"policy_name":"co-gas-hidden-agenda-miner-relhalpha","version":1,"player_name":"relh",    "is_filler":false},
    {"position":1,"policy_name":"hidden-agenda-sleuth",                "version":3,"player_name":"daveey",  "is_filler":false},
    {"position":2,"policy_name":"hidden-agenda-shadow",                "version":3,"player_name":"daveey-1","is_filler":false},
    {"position":3,"policy_name":"co-gas-hidden-agenda-miner-richard",  "version":1,"player_name":"richard", "is_filler":false},
    {"position":4,"policy_name":"hidden-agenda-lurker",                "version":3,"player_name":"daveey",  "is_filler":true}
  ],
  "participant_scores": [
    {"position":0,"score":1.0},{"position":1,"score":1.0},{"position":2,"score":1.0},
    {"position":3,"score":-4.0},{"position":4,"score":1.0}
  ]
}
```

Corroborating, the previous two post-re-seat rounds, fetched the same way:

```
round 8  round_bed14b0b-3da0-4415-91cc-c26a9f8b92a7  ->  ereq_01b3c6ca-374e-4855-a8fe-006082e86357
```
```json
{"status":"completed",
 "replay_url":"https://softmax-public.s3.amazonaws.com/replays/02f31d87-9393-4e20-814a-e0ce1659f788.replay",
 "participants":[{"position":0,"policy_name":"co-gas-hidden-agenda-miner-relhalpha","version":1,"player_name":"relh","is_filler":false},
  {"position":1,"policy_name":"hidden-agenda-sleuth","version":3,"player_name":"daveey","is_filler":false},
  {"position":2,"policy_name":"hidden-agenda-shadow","version":3,"player_name":"daveey-1","is_filler":false},
  {"position":3,"policy_name":"co-gas-hidden-agenda-miner-richard","version":1,"player_name":"richard","is_filler":false},
  {"position":4,"policy_name":"hidden-agenda-lurker","version":3,"player_name":"daveey","is_filler":true}],
 "participant_scores":[{"position":0,"score":-4.0},{"position":1,"score":1.0},{"position":2,"score":1.0},{"position":3,"score":1.0},{"position":4,"score":1.0}]}
```
```
round 7  round_8e328266-84e5-4713-be4d-9dad1e3954b7  ->  ereq_3784018c-84dc-4439-b807-8178419fde84
```
```json
{"status":"completed",
 "replay_url":"https://softmax-public.s3.amazonaws.com/replays/17333d6c-a893-45c9-acc6-2c67cdf3be4b.replay",
 "participants":[{"position":0,"policy_name":"co-gas-hidden-agenda-miner-relhalpha","version":1,"player_name":"relh","is_filler":false},
  {"position":1,"policy_name":"hidden-agenda-sleuth","version":3,"player_name":"daveey","is_filler":false},
  {"position":2,"policy_name":"hidden-agenda-shadow","version":3,"player_name":"daveey-1","is_filler":false},
  {"position":3,"policy_name":"co-gas-hidden-agenda-miner-richard","version":1,"player_name":"richard","is_filler":false},
  {"position":4,"policy_name":"hidden-agenda-miner","version":3,"player_name":"daveey","is_filler":true}],
 "participant_scores":[{"position":0,"score":1.0},{"position":1,"score":-4.0},{"position":2,"score":1.0},{"position":3,"score":1.0},{"position":4,"score":1.0}]}
```

Status: **TRUE** — `status == "completed"`, non-null `replay_url`, participants name both `daveey`
(position 1, `hidden-agenda-sleuth` **v3**, `is_filler:false`) and `daveey-1` (position 2,
`hidden-agenda-shadow` **v3**, `is_filler:false`). The single filler seat carries `is_filler:true`
and is a **v3** filler. Scores are non-degenerate (`+1 / −4`), i.e. the round genuinely settled.
Same shape in all three post-re-seat rounds.

---

## 4. Replay bytes valid and champion seats really deciding — **TRUE**

### 4a. Bytes, protocol and reason

Latest round (round 9), the round check 8 also rendered:
```
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/2e2bca77-137b-4c3d-b5b7-a7a15dbe07c1.replay" -o /tmp/v2/ep9.replay
-> http=200 bytes=232825
jq -e . /tmp/v2/ep9.replay >/dev/null   -> strict UTF-8 JSON: ok
jq -r '.protocol' /tmp/v2/ep9.replay
```
```
hidden_agenda.replay.v1
```
```
jq -c '.results' /tmp/v2/ep9.replay
```
```json
{"names":["relh","daveey","daveey-1","richard","Baseline"],
 "aliases":["RED","BLUE","GREEN","YELLOW","PINK"],
 "roles":["crew","crew","crew","impostor","crew"],
 "scores":[1,1,1,-4,1],"win":[true,true,true,false,true],"winner":"crew",
 "deposits":16,"depositTarget":32,"freezes":2,"witnessedFreezes":0,"ejections":1,
 "ejectedImpostor":true,"wrongEjections":0,"fakeDeposits":0,"meetings":6,"ticks":1558,
 "reason":"complete","ending":"impostor_ejected"}
```

Round 8 (`02f31d87-…`, http=200 bytes=367535, strict parse ok, `protocol` `hidden_agenda.replay.v1`):
```json
{"roles":["impostor","crew","crew","crew","crew"],"scores":[-4,1,1,1,1],"winner":"crew",
 "deposits":32,"depositTarget":32,"freezes":2,"witnessedFreezes":0,"ejections":0,
 "ejectedImpostor":false,"wrongEjections":0,"fakeDeposits":0,"meetings":9,"ticks":2504,
 "reason":"complete","ending":"crew_deposits"}
```

Round 7 (`17333d6c-…`, http=200 bytes=159044, strict parse ok, `protocol` `hidden_agenda.replay.v1`):
```json
{"roles":["crew","impostor","crew","crew","crew"],"scores":[1,-4,1,1,1],"winner":"crew",
 "deposits":15,"depositTarget":32,"freezes":0,"witnessedFreezes":0,"ejections":1,
 "ejectedImpostor":true,"wrongEjections":0,"fakeDeposits":0,"meetings":4,"ticks":1038,
 "reason":"complete","ending":"impostor_ejected"}
```

`protocol` matches the design manifest (`design.md` line 927: `"protocol":"hidden_agenda.replay.v1"`).
`results.reason` is `"complete"` in all three — no `deadline`, no `forfeit`, so no documented
exception is needed. Both legal endings the design lists appear across the sample
(`impostor_ejected` twice, `crew_deposits` once). `.policyNames` reads
`["relh","daveey","daveey-1","richard","Baseline"]` in all three, so the **champion seats are 1
(`daveey`, hidden-agenda-sleuth:v3) and 2 (`daveey-1`, hidden-agenda-shadow:v3)**.

### 4b. Champion decisions — the half that was FALSE in attempt 1

Decision records are `order` events with a `source` field (`design.md` line 912:
``| `order` | `t, seat, decision, plan, vote, switch, say, hunch, notes, source`
(`llm`|`retry`|`fallback`|`scripted`|`budget`)`, latencyMs` |``). `llm`/`retry` are real LLM
decisions; `fallback`/`scripted`/`budget` are not.

```
jq -r '[.events[]|select(.k=="order")]|group_by(.seat)[]|"seat \(.[0].seat): total=\(length) " + ([.[]|.source]|group_by(.)|map("\(.[0])=\(length)")|join(" "))' <replay>
```

Round 9 (`/tmp/v2/ep9.replay`, the latest):
```
seat 0: total=2  scripted=2
seat 1: total=7  llm=7
seat 2: total=7  llm=7
seat 3: total=7  scripted=7
seat 4: total=5  scripted=5
```

Round 8 (`/tmp/v2/ep8.replay`):
```
seat 0: total=10 scripted=10
seat 1: total=7  fallback=3 llm=4
seat 2: total=10 fallback=6 llm=4
seat 3: total=9  scripted=9
seat 4: total=10 scripted=10
```

Round 7 (`/tmp/v2/ep7.replay`):
```
seat 0: total=5 scripted=5
seat 1: total=5 llm=4 retry=1
seat 2: total=5 llm=5
seat 3: total=5 scripted=5
seat 4: total=5 scripted=5
```

Champion-seat totals (seats 1 + 2 only):

| round | champion orders | `llm`+`retry` | `fallback` | real-LLM share | cause of fallbacks |
|---|---|---|---|---|---|
| 7 | 10 | 10 |  0 | **100 %** | — |
| 8 | 17 |  8 |  9 | **47.1 %** | Bedrock 429 daily-quota (see check 5) |
| 9 | 14 | 14 |  0 | **100 %** | — |
| **all post-re-seat** | **41** | **32** | **9** | **78.0 %** | all 9 are 429; **zero parse rejects** |

```
jq -r '[.events[]|select(.fallback==true)]|length'   ->  0   (rounds 7, 8 and 9)
```
(the boolean `fallback` field is unused by this protocol; `source` is the authoritative field, as
above.)

**The parse defect is gone.** Every champion plan in the post-re-seat replays now uses the
structured sibling-key form the validator wants — verbatim from round 9, seat 1 and seat 2:

```
jq -c '.events[]|select(.k=="order" and (.seat==1 or .seat==2))|{t,seat,source,latencyMs,plan,vote,say,hunch}' /tmp/v2/ep9.replay
```
```json
{"t":0,"seat":1,"source":"llm","latencyMs":4935,"plan":[{"job":"mine","at":"S2"},{"job":"mine","at":"S5"},{"job":"deposit"}],"vote":"","say":"","hunch":"Start with gallery seams (S2, S5) to build gem count safely. PINK visible nearb…"}
{"t":0,"seat":2,"source":"llm","latencyMs":4935,"plan":[{"job":"mine","at":"S2"},{"job":"deposit"},{"job":"watch","who":"YELLOW"}],"vote":"","say":"","hunch":"YELLOW and PINK visible at grate. RED and BLUE unseen—one is impostor. Start mi…"}
{"t":461,"seat":2,"source":"llm","latencyMs":6214,"plan":[{"job":"mine","at":"S2"},{"job":"deposit"},{"job":"watch","who":"BLUE"}],"vote":"YELLOW","say":"RED frozen at t262. BLUE mining S2 (t460), PINK at grate (t460). YELLOW idle—no recent wo…","hunch":"YELLOW has no alibi: idle at [9,7] t201, now [11,8] t461. Could be impostor."}
{"t":721,"seat":2,"source":"llm","latencyMs":7064,"plan":[{"job":"mine","at":"S2"},{"job":"deposit"},{"job":"watch","who":"BLUE"}],"vote":"YELLOW","say":"RED frozen t262. YELLOW solo 449t unaccounted. BLUE+PINK 392t together—clean. Chain mine→…","hunch":"YELLOW: solo at grate t272, then offline 449 ticks. No alibi, no recent sightin…"}
{"t":981,"seat":1,"source":"llm","latencyMs":7160,"plan":[{"job":"deposit"},{"job":"mine","at":"S5"},{"job":"mine","at":"S2"}],"vote":"skip","say":"RED frozen t671. YELLOW 451t gap ending with 2 gems at grate—suspicious. Mining S5/S2. Sk…","hunch":"YELLOW likely impostor: 451-tick gap, appears with full hands at grate after RE…"}
{"t":1241,"seat":1,"source":"llm","latencyMs":6145,"plan":[{"job":"deposit"},{"job":"mine","at":"S2"},{"job":"watch","who":"YELLOW"}],"vote":"YELLOW","say":"YELLOW: 451t gap ending with 2 gems. Consistent impostor pattern. Vote YELLOW.","hunch":"YELLOW is the impostor. Long unaccounted gap, suspicious gem timing at grate, n…"}
{"t":1501,"seat":1,"source":"llm","latencyMs":6363,"plan":[{"job":"deposit"},{"job":"mine","at":"S2"},{"job":"mine","at":"S5"}],"vote":"YELLOW","say":"YELLOW: 451t gap, 2 gems at grate, counter stayed 12/32. Impostor confirmed.","hunch":"YELLOW is the impostor. Freeze pattern: RED t671, PINK t1196. YELLOW's gem didn…"}
{"t":1501,"seat":2,"source":"llm","latencyMs":6363,"plan":[{"job":"mine","at":"S2"},{"job":"deposit"},{"job":"watch","who":"BLUE"}],"vote":"YELLOW","say":"YELLOW 709t gap unexplained. BLUE+PINK verified 392t together. Vote YELLOW lock.","hunch":"YELLOW is the impostor. 709t absence from t272-t981 matches freeze timing. BLUE…"}
```
(excerpt — 8 of the 14 champion orders in round 9; all 14 are `source:"llm"`.)

`{"job":"mine","at":"S2"}`, `{"job":"watch","who":"YELLOW"}`, `{"job":"lurk","room":"SE"}`
(round 7, seat 1) — the exact `at`/`who`/`room` sibling keys attempt 1 found the schema hint failing
to teach. Round 8's champion fallbacks are the *only* fallbacks in the sample and every one of them
is a Bedrock 429, not a rejected reply (check 5 proves this line by line).

Content is non-trivial and evolves: the `say`/`hunch`/`notes` text differs at every meeting and
tracks the state of the board. Contrast attempt 1, where seat 0 emitted the byte-identical
`"nothing solid"` at t=9 and t=529 — that scripted string now appears only on the **scripted** seats
(seats 0/3/4, `co-gas-…` and the Baseline filler).

**The champions play the game.** In round 9 both champion seats independently converge on YELLOW
(the actual impostor, `roles[3]=="impostor"`, player `richard`) from gap-timing evidence and both
vote it out at the final meeting:
```
jq -c '.events[]|select(.k=="eject")|{t,target,tally,outcome,wasImpostor}' /tmp/v2/ep9.replay | tail -1
{"t":1557,"target":"YELLOW","tally":{"YELLOW":2,"skip":1},"outcome":"plurality","wasImpostor":true}
```

Status: **TRUE** — valid UTF-8 JSON under a strict parser in all three replays; `protocol` matches
the manifest; `results.reason == "complete"` in all three; champion-seat decisions are
overwhelmingly real LLM calls (**78 % across the whole post-re-seat sample, 100 % in the latest
round**), with non-trivial, evolving content, and the fallbacks that remain are a documented
platform cause, not this coworld's parser.

---

## 5. Hosted game log is CLEAN — **TRUE**

```
GET $BASE/episode-requests/<EREQ>/artifacts/logs   [Authorization, User-Agent, X-Use-Elevated-Privileges]
```
Bodies are python `b'…'` byte-string reprs under `===== container: <name> =====` headers and were
decoded per-repr with `ast.literal_eval` before grepping (per `playbooks/observatory-api.md` §10).

### Round 9 — `ereq_50c013dc-2b01-41bd-90df-25c3edfd0eb8` (the latest round; http=200, 3872 bytes)

```
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/v2/logs9.txt || echo CLEAN
```
```
CLEAN
```
```
grep -oE 'attempt [12] failed: .*' /tmp/v2/logs9.txt | sed 's/{.*//' | sort | uniq -c | sort -rn
```
```
(no output — zero failed attempts)
```
The `game` container in full, verbatim:
```
hidden-agenda: seed not pinned; randomized to 872461658
hidden-agenda: seats=5 variant=hidden-agenda chat=true maxTicks=3000 depositTarget=32 meetingTicks=60 visionRadius=8 seed=872461658
hidden-agenda: serving on 0.0.0.0:8080
hidden-agenda: player slot 4 connected (1/5)
hidden-agenda: slot 4 registered (0 prompt chars, scripted lurker)
hidden-agenda: player slot 0 connected (2/5)
hidden-agenda: slot 0 registered (0 prompt chars, scripted miner)
hidden-agenda: player slot 1 connected (3/5)
hidden-agenda: slot 1 registered (1528 prompt chars, llm)
hidden-agenda: player slot 2 connected (4/5)
hidden-agenda: slot 2 registered (1268 prompt chars, llm)
hidden-agenda: player slot 3 connected (5/5)
hidden-agenda: slot 3 registered (0 prompt chars, scripted miner)
hidden-agenda: starting with 5/5 players connected
hidden-agenda llm: bedrock transport, url http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
hidden-agenda: writing results and replay (232825 bytes)
hidden-agenda: episode complete (complete/impostor_ejected, winner crew) after 1558 ticks, 16 deposits, 2 freezes (0 witnessed), 6 meetings
hidden-agenda: holding /healthz and /global for 20s
```
(duplicate `slot N registered` lines elided; both champion seats register as `llm`, the other three
as `scripted`.) **Not a single `attempt … failed` line, and not a single fallback.**

### Round 7 — `ereq_3784018c-84dc-4439-b807-8178419fde84` (http=200, 24449 bytes)

```
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/v2/logs7.txt || echo CLEAN
```
```
CLEAN
```
```
grep -oE 'attempt [12] failed: .*' /tmp/v2/logs7.txt | sed 's/{.*//' | sort | uniq -c | sort -rn
```
```
      1 attempt 1 failed: llm throttled (429): 
```
Verbatim from the `game` container:
```
hidden-agenda llm: bedrock transport, url http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
hidden-agenda llm: seat 1 attempt 1 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
hidden-agenda: writing results and replay (159044 bytes)
hidden-agenda: episode complete (complete/impostor_ejected, winner crew) after 1038 ticks, 15 deposits, 0 freezes (0 witnessed), 4 meetings
```
The single throttle was absorbed by the retry — that is the `source:"retry"` order at seat 1 in the
check-4 table — so the log is still CLEAN by the grep and no seat fell back.

### Round 8 — `ereq_01b3c6ca-374e-4855-a8fe-006082e86357` (http=200, 49693 bytes) — NOT clean

```
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/v2/logs8.txt
```
```
117:hidden-agenda llm: seat 2 falling back to scripted decision
122:hidden-agenda llm: seat 1 falling back to scripted decision
123:hidden-agenda llm: seat 2 falling back to scripted decision
128:hidden-agenda llm: seat 1 falling back to scripted decision
129:hidden-agenda llm: seat 2 falling back to scripted decision
134:hidden-agenda llm: seat 1 falling back to scripted decision
135:hidden-agenda llm: seat 2 falling back to scripted decision
138:hidden-agenda llm: seat 2 falling back to scripted decision
141:hidden-agenda llm: seat 2 falling back to scripted decision
```
9 hits. The cause, itemised:
```
grep -oE 'attempt [12] failed: .*' /tmp/v2/logs8.txt | sed 's/{.*//' | sort | uniq -c | sort -rn
```
```
      9 attempt 2 failed: llm throttled (429): 
      9 attempt 1 failed: llm throttled (429): 
```

**All 18 failed attempts in round 8 are `llm throttled (429)`. Zero are parse rejects.** Attempt 1's
cause B — `unknown job: mine at:s2`, `mine needs at: one of S1..S6, got ''`,
`switch needs both "if" and "to"` — appears **0 times across all three post-re-seat rounds**:
```
grep -cE 'unknown job|needs at: one of|needs both' /tmp/v2/logs7.txt /tmp/v2/logs8.txt /tmp/v2/logs9.txt
/tmp/v2/logs7.txt:0
/tmp/v2/logs8.txt:0
/tmp/v2/logs9.txt:0
```
The `731ab43` parse fix carried into the 0.1.2 image has eliminated that failure mode entirely.

### The 429 is the documented platform-wide cause, cross-checked

Per `prompts/60-verify.md` check 5, cross-checked against another live LLM coworld. The **`coins`**
coworld (`cow_e5c32ad5-8696-4d4f-8a39-458baa8c2a3e`), episode request
`ereq_1e00588b-e7cd-42a2-8cd3-862170922954`, created **2026-08-26T05:08:37Z** — the same minute
hidden-agenda's round 8 was running — shows the identical throttle on the same Haiku 4.5 model,
**44 `Too many tokens per day` events / 66 `429` lines**:
```
2026-08-26 05:09:04,077 INFO httpx HTTP Request: POST https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke "HTTP/1.1 429 Too Many Requests"
2026-08-26 05:09:04,077 WARNING __main__ bedrock_sidecar_complete {"episode_request_id":"1e00588b-e7cd-42a2-8cd3-862170922954","model":"global.anthropic.claude-haiku-4-5-20251001-v1:0","operation":"InvokeModel","ok":false,"status_code":429,"error_kind":"upstream_client","error_type":"ThrottlingException","message":"Too many tokens per day, please wait before trying again.", …}
2026-08-26 05:09:08,947 INFO httpx HTTP Request: POST https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke "HTTP/1.1 429 Too Many Requests"
```
This is the platform-wide Bedrock daily-token-quota symptom named in `prompts/60-verify.md` check 5
and in SPEC §Parallelism and per-run isolation, not a defect in this coworld. Per the prompt it was
not treated as grounds to go Blocked: polling continued inside the 75-minute bound, and **round 9,
15 minutes later, came back completely clean** — which is exactly the transient-capacity behaviour
the documented exception describes.

Status: **TRUE** — the latest round's hosted log greps `CLEAN`, as does round 7's. Round 8's 9 hits
are inside the bound, are 100 % Bedrock 429 throttle, are cross-checked as platform-wide against
`coins` at the same minute, and cleared on the next round without any change to this coworld.

---

## 6. The public page uses the static replay path — **TRUE**

**Source used: the SSR payload + the session API** (the documented fallback in
`prompts/60-verify.md` check 6), because the raw-HTML grep finds nothing — the page is
client-rendered, exactly as `playbooks/observatory-api.md` §Featured match records platform-wide.

```
GET https://softmax.com/hidden-agenda            (fetched 2026-08-26T05:26:53Z)
-> http=200 bytes=580343
grep -o '<iframe[^>]*src="[^"]*"'                -> (no match)
```

Not recorded as a false negative. The coworld detail API is likewise `null` platform-wide, so it is
also not evidence either way — but it does confirm the canonical id, version and sha:

```
GET $BASE/coworlds?limit=200 | jq '.[]|select(.name=="hidden_agenda" and .canonical==true)|{id,name,version,canonical,replay_viewer,featured_match,manifest_hash}'
```
```json
{"id":"cow_962d0488-144c-48f6-b0c7-08a19ac5ed89","name":"hidden_agenda","version":"0.1.2",
 "canonical":true,"replay_viewer":null,"featured_match":null,
 "manifest_hash":"sha256:9b4d97318ad246f405db95efa82637091e7099250dd8d735715b579989f1741c"}
```
(The 0.1.0 `cow_87de5e19-…` and the 0.1.1 `cow_6f563cd4-…` both now read `"canonical":false`.)

**Featured match — present, and it has flipped to the new canonical coworld.** Server-rendered into
the page's SSR payload at `state.playlist[0]`, verbatim:

```
grep -o 'playlist\\":\[…' /tmp/v2/page3.html     (05:26:53Z)
```
```
playlist\":[{\"episodeId\":\"b2e398fc-5f96-4e7b-a07c-833e1ddd7b08\",
\"coworldId\":\"cow_962d0488-144c-48f6-b0c7-08a19ac5ed89\",\"coworldName\":\"hidden_agenda\",
\"coworldVersion\":\"0.1.2\",
\"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/2e2bca77-137b-4c3d-b5b7-a7a15dbe07c1.replay\",
\"finishedAt\":\"2026-08-26T05:23:42.156734Z\",\"roundNumber\":9,\"episodeNumber\":1,
\"code\":\"hidden_agenda.r9.e1\",
\"matchup\":{\"divisionId\":\"div_cb85265c-94ee-4f36-885f-f72c1e71f7e8\",\"divisionName\":\"Competition\",
 \"first\":{\"rank\":1,\"player_name\":\"daveey-1\",\"score\":1022.2263799299311,\"rounds_played\":8,
  \"policy_label\":\"hidden-agenda-shadow:v3\"},
 \"second\":{\"rank\":2,\"player_name\":\"daveey\",\"score\":1017.7496788498975,\"rounds_played\":8,
  \"policy_label\":\"hidden-agenda-sleuth:v3\"}},
\"inspectUrl\":\"/observatory/v2?tab=overview&detail=episode-request:ereq_50c013dc-2b01-41bd-90df-25c3edfd0eb8\",
\"outcome\":null}
```

`coworldId` is **`cow_962d0488`** and `coworldVersion` is **0.1.2** — the featured match has flipped
to the new canonical coworld, and its two ranked players are the two **v3** champions. (At 04:52Z
the same payload read `hidden_agenda.r7.e1` on the same `cow_962d0488` / 0.1.2; the featured match
rolls forward with the ladder and has not pointed at the old `cow_87de5e19` since the re-release.)

**The iframe `src`**, from the call the page's own JS makes:
```
POST $BASE/coworlds/replays/session
     {"coworld_id":"cow_962d0488-144c-48f6-b0c7-08a19ac5ed89",
      "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/2e2bca77-137b-4c3d-b5b7-a7a15dbe07c1.replay"}
     (fetched 2026-08-26T05:26:53Z)
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_962d0488-144c-48f6-b0c7-08a19ac5ed89/sha256%3A9b4d97318ad246f405db95efa82637091e7099250dd8d735715b579989f1741c/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F2e2bca77-137b-4c3d-b5b7-a7a15dbe07c1.replay&v=2",
  "ready": true
}
```

Status: **TRUE** — the path is
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`, `ready: true`, the
`<cow_id>` is the new canonical `cow_962d0488-144c-48f6-b0c7-08a19ac5ed89`, and `sha256%3A9b4d9731…`
URL-decodes to `sha256:9b4d97318ad246f405db95efa82637091e7099250dd8d735715b579989f1741c` — the
`manifest_hash` returned by `/coworlds` above and `STATE.coworld.manifest_sha`. **No
`/client/replay` pod URL anywhere.** A featured match is present.

---

## 7. Certification declared the static bundle — **TRUE**

**Source: the committed `runs/2026-08-25-hidden-agenda/release-result.json`** — the copy phase 40
downloaded and committed, now overwritten with the **0.1.2** release artifact (release run
`32931097733`, per `STATE.coworld.release_run_id`). It was present; no re-download from the release
run was needed, and `/tmp` was not consulted.

```
jq -c '{version,cow_id,manifest_sha,canonical,ok,step_failed}' runs/2026-08-25-hidden-agenda/release-result.json
```
```json
{"version":"0.1.2","cow_id":"cow_962d0488-144c-48f6-b0c7-08a19ac5ed89",
 "manifest_sha":"sha256:9b4d97318ad246f405db95efa82637091e7099250dd8d735715b579989f1741c",
 "canonical":true,"ok":true,"step_failed":null}
```
```
jq -r '.certify.replay_liveness' runs/2026-08-25-hidden-agenda/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

The surrounding certification transcript in the same file, for context (`.certify.output_tail`):
```
Certifying dist/coworld_manifest.json against transcript coworld-executable
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

Status: **TRUE** — contains `Replay liveness: skipped (static replay bundle declared`, and the
artifact is this run's 0.1.2 release, matching the `cow_id` and `manifest_sha` used in check 6.

---

## 8. Spectator judgment — the viewer was EXECUTED — **TRUE**

Dispatched against the iframe `src` from check 6 (the current featured match, round 9):

```
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder \
  -f url="https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_962d0488-144c-48f6-b0c7-08a19ac5ed89/sha256%3A9b4d97318ad246f405db95efa82637091e7099250dd8d735715b579989f1741c/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F2e2bca77-137b-4c3d-b5b7-a7a15dbe07c1.replay&v=2" \
  -f timeout=90
# dispatched 2026-08-26T05:27:06Z
```

Run found by sorting on `createdAt`, not by taking "the latest" blind. Runs existing **before** the
dispatch were `32933394784 (05:16:12Z)`, `32931950773 (04:53:58Z)`, `32931770282 (04:51:09Z)`,
`32930044755 (04:23:33Z)`; after:

```
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 4
32934089374  2026-08-26T05:27:08Z  in_progress     <- created after the dispatch: this run
32933394784  2026-08-26T05:16:12Z  completed
32931950773  2026-08-26T04:53:58Z  completed
32931770282  2026-08-26T04:51:09Z  completed
```
```
gh run watch 32934089374 -R Metta-AI/coworld-builder --exit-status
✓ viewer-check in 50s (ID 98071878388)
  ✓ Install Playwright (pinned 1.55.0)
  ✓ Load the viewer
  ✓ Summary
  ✓ Upload the evidence
  ✓ Fail if the viewer did not load
exit=0                       # green
gh run download 32934089374 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-25-hidden-agenda/viewer-check
-> viewer-smoke.json (1337 B), viewer-smoke.png (302335 B), smoke-stdout.txt (541 B), smoke-stderr.txt (0 B)
```

`runs/2026-08-25-hidden-agenda/viewer-check/` has been **overwritten** with this run's artifacts;
the attempt-1 artifacts (run `32928573158`, the 0.1.0 coworld) are gone. An earlier dispatch this
attempt (`32931950773`, 04:53:58Z) rendered the round-7 replay on the same 0.1.2 bundle and also
returned `loaded:true` with three differing clocks; it was superseded when the featured match rolled
to round 9, and its artifacts are not the ones committed.

### Readouts, verbatim from `runs/2026-08-25-hidden-agenda/viewer-check/viewer-smoke.json`

```
jq -c '{loaded, ms, clock, scorebug, feed_lines}' …/viewer-smoke.json
```
```json
{"loaded":true,"ms":4210,"clock":"TICK 3 / 3000 DEPOSITS 0 / 32","scorebug":"CREW DEPOSITS 0 0 / 32 TICK 3 / 3000 DEPOSITS 0 / 32 IMPOSTOR CREW LEFT 4 YELLOW · RICHARD","feed_lines":0}
```
```
jq -c '.signals' …/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```
```
jq -r '.failure // "no failure"' …/viewer-smoke.json
```
```
no failure
```
Also, from the same file: `"status":"OPEN"`, `"loading_text":null`, `"console_tail":[]`,
`"url"` equal to the check-6 `viewer_url` byte for byte, and
`"canvas_text":{"total":0,"outside":0,"ellipsized":0,"never_inside":0,…}` — nothing drawn outside
the canvas, nothing ellipsized.

### The three clock readouts

```
jq -r '.scrub[]|"\(.at)\t\(.clock)"' …/viewer-smoke.json
```

| scrub position | clock readout |
|---|---|
| 0 %   | `TICK 3 / 3000 DEPOSITS 0 / 32` |
| 50 %  | `TICK 795 / 3000 DEPOSITS 8 / 32` |
| 100 % | `TICK 1557 / 3000 FINAL` |

**All three differ**, and they differ *monotonically in two independent quantities* — tick
(3 → 795 → 1557) and deposits (0 → 8 → final). The scrubber exists and works; this is not a single
frozen frame. The final tick `1557` matches the replay's `end` event at `t: 1557` and
`results.ticks: 1558` exactly.

Status: **TRUE** — `loaded: true` (via `data-replay-loaded="true"`, first frame at 4210 ms) **and**
the three clock readouts differ.

### Reconciliation against the replay record

The rendered replay is round 9, `2e2bca77-…` (`/tmp/v2/ep9.replay`). Ordered excerpts:

*Early* (`jq -r '.events[]|[.t,(.seat//"-"),.k,(.summary//.say//"")]|@tsv' | head -16`):
```
0	0	reveal
0	1	reveal	   … (5 reveals, one per seat)
0	0	order
0	1	order	   … (5 opening orders)
79	2	mine
87	0	mine
111	-	seam
151	2	mine
159	0	mine
161	2	deposit
```

*Middle* (`select(.t>=700 and .t<=900)`):
```
711	-	seam
721	-	meeting
721	1	order	RED frozen t671. Deposits 8/32. Mining S5 (2 gems seen t720). No witnessed freeze yet.
721	2	order	RED frozen t262. YELLOW solo 449t unaccounted. BLUE+PINK 392t together—clean. Chain mine→…
721	3	order	keeping my head down
721	4	order	i was mining
731	1/2/3/4	say
745	1/2/3/4	vote
767	2	vote
777	-	eject
835	-	seam
852	2	mine
863	1	mine
891	-	seam
```

*Late* (`| tail -18`):
```
1444	2	mine
1454	2	deposit
1455	2	deposit
1458	1	mine
1491	-	seam
1501	-	meeting
1501	1	order	YELLOW: 451t gap, 2 gems at grate, counter stayed 12/32. Impostor confirmed.
1501	2	order	YELLOW 709t gap unexplained. BLUE+PINK verified 392t together. Vote YELLOW lock.
1501	3	order	keeping my head down
1511	1/2/3	say
1525	1/2/3	vote
1547	3	vote
1557	-	eject
1557	-	end
```

The freeze/eject spine, in full:
```json
{"k":"eject","t":257,"target":null,"tally":{"GREEN":1,"RED":1,"skip":3},"outcome":"skip","wasImpostor":false}
{"k":"freeze","t":280,"seat":3,"victim":"RED","cell":[13,15],"room":"SOUTH GALLERY","witnesses":[]}
{"k":"eject","t":517,"target":null,"tally":{"GREEN":1,"YELLOW":1,"skip":2},"outcome":"skip","wasImpostor":false}
{"k":"eject","t":777,"target":null,"tally":{"GREEN":1,"skip":3},"outcome":"skip","wasImpostor":false}
{"k":"eject","t":1037,"target":null,"tally":{"GREEN":1,"YELLOW":1,"skip":2},"outcome":"skip","wasImpostor":false}
{"k":"freeze","t":1046,"seat":3,"victim":"PINK","cell":[13,5],"room":"THE CORRIDOR","witnesses":[]}
{"k":"eject","t":1297,"target":null,"tally":{"YELLOW":1,"skip":2},"outcome":"skip","wasImpostor":false}
{"k":"eject","t":1557,"target":"YELLOW","tally":{"YELLOW":2,"skip":1},"outcome":"plurality","wasImpostor":true}
{"k":"end","t":1557,"reason":"complete","ending":"impostor_ejected","winner":"crew","deposits":16,
 "scores":[1,1,1,-4,1],"roles":["crew","crew","crew","impostor","crew"],"freezes":2,
 "witnessedFreezes":0,"ejections":1,"meetings":6}
```
```
jq -r '[.events[].k]|group_by(.)|map("\(.[0])=\(length)")|join(" ")'
deposit=16 eject=6 end=1 freeze=2 meeting=6 mine=20 order=28 reveal=5 say=23 seam=17 vote=28
```

### Spectator-judgment paragraph

**It is legible, and it shows the game.** `viewer-smoke.png` (the 100 %-scrub frame CI captured) is
a dense, readable spectator screen, and every element on it is corroborated by the replay record
above. The top strip is the three-part **scorebug**: `16 DEPOSITS · CREW · 16 / 32` with a five-pip
carry indicator at the left (three pips lit, two hollow), `TICK 1557 / 3000 · FINAL` centred, and the
**`IMPOSTOR · CREW LEFT 2 · YELLOW · RICHARD`** plate at the right — matching
`results.deposits: 16`, `depositTarget: 32`, `ticks: 1558`, `roles[3]=="impostor"` and
`names[3]=="richard"` exactly. Below it sits the **roster ring** —
`RED RELH | BLUE DAVEEY | GREEN DAVEEY-1 | YELLOW RICHARD | PINK BASELINE` — with YELLOW's chip
struck through and dimmed because it was ejected, matching the t=1557 eject. A
**`YELLOW EJECTED — THE IMPOSTOR`** banner sits over the board; two frozen bodies (a BLUE-tagged and
a GREEN-tagged cog glyph) lie on the floor mid-map, matching `freezes: 2` and the two un-witnessed
freezes at t=280 (SOUTH GALLERY) and t=1046 (THE CORRIDOR). The board itself is a dim grid with the
seam clusters (`S2`, `S4`, three-gem glyphs at the corners) and the 3×3 grate visible in the centre.
The **vote board** is drawn at the right — `MEETING 6 — SCHEDULED`, `BLUE → YELLOW`,
`GREEN → YELLOW`, `RESOLVED` — which is precisely the final tally `{"YELLOW":2,"skip":1}` with the
ejected impostor's own row omitted; a stack of dimmed earlier verdicts
(`YELLOW EJECTED 2-1 — THE IMPOSTOR`) is layered beneath it. The **role-reveal endcard** dominates
the centre: `CREW WIN — THE IMPOSTOR WAS EJECTED`, the rules reminder `CREW WIN AT 32 DEPOSITS OR BY
EJECTING THE IMPOSTOR. THE IMPOSTOR WINS AT ONE CREWMATE LEFT.`, the stat line
`2 freezes · 0 witnessed · 1 ejection (right) · 0 fake deposits · 6 meetings` — which is `results`
read out field for field — and the full role reveal (`RED CREW relh`, `BLUE CREW daveey`,
`GREEN CREW daveey-1`, `YELLOW IMPOSTOR richard`, `PINK CREW Baseline`). At the bottom is the
**transport strip** — restart, step-back, pause, `+5s`, step-forward, loop, fast-forward, a
`spoilers` toggle, the `CREW WINS 1557 / 1557` status and `1× 2× 3× 4× 8× 16×` speed buttons — over
a scrubber carrying six meeting markers and a **`RACE TO WIN`** momentum graph beneath it, whose
blue (crew) band swells and whose red (impostor) band collapses toward the right, matching a crew
win. The picture is neither empty nor frozen nor unreadable.

**Does it look like the starter's chrome? Yes.** This is recognisably the paintbot / coworld-ctf
family: the same transport strip, the same scrubber-with-momentum-graph, the same three-part
scorebug and the same endcard treatment, re-skinned for this game. It is not a rewrite sharing only
the ids — this is not the cogame-gridlock failure. Every game-specific element the design promised
is present: CREW/IMPOSTOR plates, roster ring with the ejected seat struck out, the ejection banner,
the vote board with per-seat arrows, the `RACE TO WIN` momentum strip, and the role-reveal endcard.

**And unlike attempt 1, the champions are the story.** In attempt 1 the winning impostor was a
scripted `Baseline` filler and the champions' meeting notes rendered byte-identical strings. Here the
two LLM champions (BLUE `daveey` and GREEN `daveey-1`) each build a gap-timing case against YELLOW
across meetings 2–6, say it aloud on the vote board, and eject the real impostor at t=1557 — the
`CREW WIN` on screen is their deduction, drawn from 14 `source:"llm"` orders with zero fallbacks.

**Two legibility observations for the coordinator, neither a check-8 failure** (both are unchanged
from attempt 1 and are harness/shell mismatches, not defects):
1. `feed_lines: 0` while a feed is plainly *visible* in the screenshot (bottom-right, dimmed under
   the endcard overlay: the stacked `YELLOW EJECTED 2-1 — THE IMPOSTOR` lines). The smoke harness's
   feed selector does not match this shell's feed element. A DOM-selector mismatch, not a missing
   feed.
2. `signals.bridge_ready: false` with `bridge: []` — the viewer signals readiness via
   `data-replay-loaded="true"` rather than the `coworld-replay` bridge. Both are accepted by the
   check; noting it so nobody reads the empty bridge array as a defect.
3. A **`CAUGHT!`** banner could not be judged from this episode: `witnessedFreezes: 0`, so no freeze
   in this replay was ever seen by another cog and the banner never fires. Attempt 1's render (round
   3 of the 0.1.0 coworld) did show `CAUGHT! GREEN FROZE RED · BLUE SAW IT`, so the element exists;
   it simply had no trigger here. Not a defect, and not evidence claimed for this attempt.

---

## Summary

| # | check | verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — 8 completed (2–9); 3 of them (7, 8, 9) post-v3-re-seat |
| 2 | both champions ranked, fillers absent/Baseline | **TRUE** — daveey-1 `:v3` rank 1, daveey `:v3` rank 2, 8 rounds each; no filler rows |
| 3 | latest round's episode request completed w/ replay + participants | **TRUE** — round 9, `ereq_50c013dc`, daveey + daveey-1 at v3 |
| 4 | replay bytes valid and champion seats really deciding | **TRUE** — `complete`, protocol match, 32/41 champion orders real LLM (100 % in round 9) |
| 5 | hosted game log CLEAN | **TRUE** — rounds 9 and 7 CLEAN; round 8's 9 hits are 100 % platform 429, cross-checked vs `coins` |
| 6 | public page uses the static replay path | **TRUE** — static path on `cow_962d0488` + sha `9b4d9731…`, featured match `hidden_agenda.r9.e1` |
| 7 | certification declared the static bundle | **TRUE** — 0.1.2 `release-result.json`, committed copy |
| 8 | viewer executed and judged | **TRUE** — run `32934089374`, `loaded:true` @4210 ms, 3 differing clocks |

Wall clock used: 04:51Z → 05:30Z, ~39 minutes of the 75-minute bound; the bound did not expire.
Retry budget: not exhausted — checks 4 and 5 passed on the first and third post-re-seat rounds
sampled.

**What changed since attempt 1.** Attempt 1's blocking cause was cause B: `llm.nim`'s plan-step
schema hint `{"job":...}` did not name the `at`/`who`/`room` sibling keys, so the model emitted the
compact `mine at:S2` form the system prompt documented and the validator rejected both attempts,
stranding 80–87.5 % of champion decisions on scripted fallbacks. After `731ab43` and the 0.1.2
re-release, **the parse-reject failure mode appears zero times in 41 champion orders across three
rounds** (`unknown job|needs at: one of|needs both` → 0 hits in all three hosted logs). The only
residual fallbacks (round 8, 9 of 41) are Bedrock daily-token-quota 429s — a platform-wide symptom
confirmed against the `coins` coworld at the same minute — and they cleared on their own by round 9.
