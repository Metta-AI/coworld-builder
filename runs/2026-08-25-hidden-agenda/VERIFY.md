# VERIFY — hidden-agenda   (2026-08-26T04:15Z)

Verdict: **2 items false** — checks 4 and 5 FALSE (LLM champions are ~85 % scripted fallbacks;
hosted logs are not CLEAN). Checks 1, 2, 3, 6, 7, 8 TRUE.

Ids used throughout:

```
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_9c44cf05-76f9-4ca5-8299-0c16a5e41ed9
D=div_cb85265c-94ee-4f36-885f-f72c1e71f7e8
COW=cow_87de5e19-e661-42cd-81dc-db93b5d25a81      # game.name == "hidden_agenda"
```

Header values are never printed; only header *names* are listed above.

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

Fillers are registered on the league. Fresh read (elevated header required on this read):

```
GET $BASE/leagues/$L/filler-policies   [Authorization, User-Agent, X-Use-Elevated-Privileges]
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"1de04b07-1e82-4300-a491-9bbae465310a","policy_id":"7c8ea289-49ff-4256-8b57-3d6b400cc04f","policy_name":"hidden-agenda-miner","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},
 {"policy_version_id":"f7b63b0f-9f61-4732-9bad-3c32b1fb522a","policy_id":"d311a90e-e0a9-4282-a705-a384fd4559b6","policy_name":"hidden-agenda-lurker","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```

Neither filler uuid equals a champion uuid (`7fcd857a-…` sleuth, `d5e5ead8-…` shadow).

```
GET $BASE/rounds?league_id=$L&limit=20      (fetched 2026-08-26T03:59:11Z)
```
```json
[
  {"id":"round_6f477b2c-9d25-45d3-8407-ca70172ed3ca","round_number":3,"status":"completed",
   "error":null,"completed_at":"2026-08-26T03:55:18.848922Z","created_at":"2026-08-26T03:53:37.037453Z",
   "entrants":["7fcd857a-8a71-4c05-ad5b-15a135511646","d5e5ead8-3618-4efa-abac-ad91f0afc79b"]},
  {"id":"round_43c151ab-64bf-4bf4-a1b5-987fdb4a706b","round_number":2,"status":"completed",
   "error":null,"completed_at":"2026-08-26T03:41:50.440692Z","created_at":"2026-08-26T03:38:36.314950Z",
   "entrants":["7fcd857a-8a71-4c05-ad5b-15a135511646","d5e5ead8-3618-4efa-abac-ad91f0afc79b"]},
  {"id":"round_9abab8d9-f4ac-40a6-bd41-2a35f8040ef1","round_number":1,"status":"failed",
   "error":"Temporal RoundWorkflow failed before settling the round.",
   "completed_at":"2026-08-26T03:38:02.732810Z","created_at":"2026-08-26T03:38:01.987136Z",
   "entrants":["7fcd857a-8a71-4c05-ad5b-15a135511646"]}
]
```
```
jq '[.entries[]|select(.status=="completed")]|length'  ->  2
```

A fourth round landed while polling and also completed:

```
poll log (/tmp/poll.log), one line per 5-minute poll, round_number:status
2026-08-26T03:41:07Z  2:pending 1:failed
2026-08-26T03:46:08Z  2:completed 1:failed
2026-08-26T03:51:09Z  2:completed 1:failed
2026-08-26T03:56:10Z  3:completed 2:completed 1:failed
2026-08-26T04:01:10Z  3:completed 2:completed 1:failed
2026-08-26T04:06:11Z  3:completed 2:completed 1:failed
2026-08-26T04:11:12Z  4:completed 3:completed 2:completed 1:failed
```

Status: **TRUE** — rounds **2, 3 and 4** completed (03:41:50Z, 03:55:18Z, ~04:08Z), all with
`round_number ≥ 2`. Round 1 `status:"failed"`, `error:"Temporal RoundWorkflow failed before
settling the round."` — the documented auto-created pre-filler round (`playbooks/observatory-api.md`
§6: "A `trigger-round` issued before any filler exists fails instantly with `Temporal RoundWorkflow
failed before settling the round`"); it does not count and is not counted. That the fillers were
live from round 2 onward is proved directly by round 2's own participant list, which seats
`hidden-agenda-miner`/`hidden-agenda-lurker` with `is_filler: true` (check 3 evidence below) and by
the round-2 replay's `policyNames` reading `["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)"]`.

---

## 2. Both champions ranked, fillers absent/Baseline — **TRUE**

```
GET $BASE/divisions/$D/leaderboard      (fetched 2026-08-26T03:59Z; bare array, not .entries)
```
```json
[
  {"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
   "score":1014.5304984710245,"score_label":"MMR","rounds_played":2,"episode_wins":1.0,
   "win_rate":0.5,"policy_label":"hidden-agenda-sleuth:v1"},
  {"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
   "score":985.4695015289755,"score_label":"MMR","rounds_played":2,"episode_wins":0.0,
   "win_rate":0.0,"policy_label":"hidden-agenda-shadow:v1"}
]
```
```
rank  player     policy_label               score               rounds  wins
1     daveey     hidden-agenda-sleuth:v1    1014.5304984710245  2       1.0
2     daveey-1   hidden-agenda-shadow:v1     985.4695015289755  2       0.0
```

Status: **TRUE** — both `daveey` and `daveey-1` present, each `rounds_played = 2 ≥ 1`. Elo has
separated from the 1000.0 seed in both directions, so rounds actually scored. No filler row appears
on the leaderboard at all (fillers are excluded, which satisfies "absent or `Baseline`").

---

## 3. Latest round's episode request completed with a replay and correct participants — **TRUE**

Latest completed round at the time of this fetch is **round 4**:

```
R=$(GET $BASE/rounds?league_id=$L&limit=20 | jq '[.entries[]|select(.status=="completed")]|max_by(.round_number).id')
-> R=round_6779cf17-c5c2-4c0a-b2a4-2e4e8b7936a2
GET $BASE/episode-requests?round_id=$R&limit=20   -> EREQ=ereq_1739ff30-963d-438a-ab88-7493655ff3af
GET $BASE/episode-requests/$EREQ                  (fetched 2026-08-26T04:11:5xZ)
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/7bc69416-04f7-4f16-bad7-6c174412e6df.replay",
  "participants": [
    {"position":0,"policy_name":"hidden-agenda-sleuth","player_name":"daveey",  "is_filler":false},
    {"position":1,"policy_name":"hidden-agenda-shadow","player_name":"daveey-1","is_filler":false},
    {"position":2,"policy_name":"hidden-agenda-lurker","player_name":"daveey",  "is_filler":true},
    {"position":3,"policy_name":"hidden-agenda-lurker","player_name":"daveey",  "is_filler":true},
    {"position":4,"policy_name":"hidden-agenda-lurker","player_name":"daveey",  "is_filler":true}
  ],
  "participant_scores": [
    {"position":0,"score":-1.0},{"position":1,"score":-1.0},{"position":2,"score":-1.0},
    {"position":3,"score":4.0},{"position":4,"score":-1.0}
  ]
}
```

The previous latest round (**round 3**, `round_6f477b2c-…`) was fetched the same way at
2026-08-26T03:59Z and is identical in shape — `ereq_23df9d26-9fe1-4ed0-84a5-d3b1714d6316`,
`status: "completed"`, `replay_url … /93af8bbc-50a0-44aa-839d-d8b039f17a84.replay`, participants
`daveey` / `daveey-1` / three fillers, `participant_scores` `[-1,-1,4,-1,-1]`. It is recorded here
because it is the replay the viewer actually rendered in check 8.

Status: **TRUE** — `status == "completed"`, non-null `replay_url`, participants name both `daveey`
and `daveey-1` at positions 0 and 1 with `is_filler:false`, and the three filler seats carry
`is_filler:true`. Scores are non-degenerate (`+4 / -1 …`), i.e. the round genuinely settled.

---

## 4. Replay bytes valid and champion seats really deciding — **FALSE**

The bytes are fine; the *decisions* are not. Three different rounds were checked (rounds 2, 3, 4)
— the three attempts of the retry budget — and all three fail the same way.

### 4a. Bytes, protocol and reason — the passing half

Latest round (round 4):
```
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/7bc69416-04f7-4f16-bad7-6c174412e6df.replay" -o /tmp/ep4.replay
-> http=200 bytes=105281
jq -e . /tmp/ep4.replay >/dev/null   -> strict UTF-8 JSON: ok
jq -r '.protocol' /tmp/ep4.replay
```
```
hidden_agenda.replay.v1
```
```
jq -c '.results|{reason,ending,winner,deposits,freezes,meetings,ticks}' /tmp/ep4.replay
```
```json
{"reason":"complete","ending":"impostor_isolation","winner":"impostor","deposits":6,"freezes":3,"meetings":3,"ticks":709}
```

Round 3 (`93af8bbc-…`, http=200 bytes=105671, strict parse ok, `protocol` `hidden_agenda.replay.v1`):
```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)"],
 "aliases":["RED","BLUE","GREEN","YELLOW","PINK"],
 "roles":["crew","crew","impostor","crew","crew"],
 "scores":[-1,-1,4,-1,-1],"win":[false,false,true,false,false],"winner":"impostor",
 "deposits":6,"depositTarget":32,"freezes":3,"witnessedFreezes":2,"ejections":0,
 "ejectedImpostor":false,"wrongEjections":0,"fakeDeposits":0,"meetings":3,"ticks":709,
 "reason":"complete","ending":"impostor_isolation"}
```

Round 2 (`4d4b319b-…`, http=200 bytes=392503, strict parse ok, `protocol` `hidden_agenda.replay.v1`):
```json
{"roles":["crew","impostor","crew","crew","crew"],"scores":[1,-4,1,1,1],"winner":"crew",
 "deposits":32,"depositTarget":32,"freezes":2,"witnessedFreezes":1,"ejections":0,
 "meetings":10,"ticks":2705,"reason":"complete","ending":"crew_deposits"}
```

`protocol` matches the design manifest (`design.md` line 927: `"protocol":"hidden_agenda.replay.v1"`).
`results.reason` is `"complete"` in all three — no `deadline`, no `forfeit`. Both legal endings the
design lists (`crew_deposits`, `impostor_isolation`) appear across the sample. This half is TRUE.

### 4b. Champion decisions — the failing half

This replay's decision records are `order` events with a `source` field
(`design.md` line 912: ``| `order` | `t, seat, decision, plan, vote, switch, say, hunch, notes,
source` (`llm`|`retry`|`fallback`|`scripted`|`budget`)`, latencyMs` |``). `llm`/`retry` are real LLM
decisions; `fallback`/`scripted`/`budget` are not. Champion seats are 0 (`daveey`,
hidden-agenda-sleuth) and 1 (`daveey-1`, hidden-agenda-shadow).

```
jq -r '[.events[]|select(.k=="order")]|group_by(.seat)[]|"seat \(.[0].seat): total=\(length) " + ([.[]|.source]|group_by(.)|map("\(.[0])=\(length)")|join(" "))' <replay>
```

Round 2 (`/tmp/ep2.replay`):
```
seat 0: total=5  fallback=5
seat 1: total=11 fallback=9 llm=2
seat 2: total=8  scripted=8
seat 3: total=11 scripted=11
seat 4: total=11 scripted=11
```

Round 3 (`/tmp/ep.replay`):
```
seat 0: total=4 fallback=3 llm=1
seat 1: total=4 fallback=4
seat 2: total=4 scripted=4
seat 3: total=3 scripted=3
seat 4: total=1 scripted=1
```

Round 4 (`/tmp/ep4.replay`):
```
seat 0: total=4 fallback=3 llm=1
seat 1: total=1 fallback=1
seat 2: total=3 scripted=3
seat 3: total=4 scripted=4
seat 4: total=4 scripted=4
```

Champion-seat totals (seats 0 + 1 only):

| round | champion orders | `llm`+`retry` | `fallback` | real-LLM share |
|---|---|---|---|---|
| 2 | 16 | 2 | 14 | **12.5 %** |
| 3 |  8 | 1 |  7 | **12.5 %** |
| 4 |  5 | 1 |  4 | **20.0 %** |

Status: **FALSE**. The requirement is that champion seats' orders be *mostly* `source=llm` with
fallbacks a small minority. The observed ratio is the exact inverse: **80–87.5 % of every champion
decision in every round sampled is a scripted fallback.** Both champion policies are effectively
playing as the scripted baseline. Round 3's seat 1 (`daveey-1` / hidden-agenda-shadow) produced
**zero** real LLM decisions across the whole episode. The causes are itemised in check 5.

Corroborating symptom in the replay text: the champions' `notes` are byte-identical at every meeting
— seat 0 says `"nothing solid"` and seat 1 says `"GREEN unseen 1 ticks"` at t=9 *and* at t=529 —
which is the scripted `miner`/`lurker` decision, not a model reasoning about new evidence.

---

## 5. Hosted game log is CLEAN — **FALSE**

```
GET $BASE/episode-requests/<EREQ>/artifacts/logs   [Authorization, User-Agent, X-Use-Elevated-Privileges]
```
Bodies are python `b'…'` byte-string reprs under `===== container: <name> =====` headers and were
decoded per-repr with `ast.literal_eval` before grepping (per `playbooks/observatory-api.md` §10).

```
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' <decoded log>
```

**Round 4** — `ereq_1739ff30-963d-438a-ab88-7493655ff3af` (the latest round; http=200):
```
65:hidden-agenda llm: seat 0 falling back to scripted decision
66:hidden-agenda llm: seat 1 falling back to scripted decision
69:hidden-agenda llm: seat 0 falling back to scripted decision
72:hidden-agenda llm: seat 0 falling back to scripted decision
```
Not CLEAN — 4 hits.

**Round 3** — `ereq_23df9d26-9fe1-4ed0-84a5-d3b1714d6316` (http=200, 32842 bytes):
```
91:hidden-agenda llm: seat 0 falling back to scripted decision
92:hidden-agenda llm: seat 1 falling back to scripted decision
97:hidden-agenda llm: seat 0 falling back to scripted decision
98:hidden-agenda llm: seat 1 falling back to scripted decision
101:hidden-agenda llm: seat 1 falling back to scripted decision
106:hidden-agenda llm: seat 0 falling back to scripted decision
107:hidden-agenda llm: seat 1 falling back to scripted decision
```
Not CLEAN — 7 hits.

**Round 2** — `ereq_1f7ef066-8452-4d99-bd04-b8e48680a9bf` (http=200, 56377 bytes): 14 hits, e.g.
```
129:hidden-agenda llm: seat 0 falling back to scripted decision
134:hidden-agenda llm: seat 0 falling back to scripted decision
135:hidden-agenda llm: seat 1 falling back to scripted decision
…
168:hidden-agenda llm: seat 1 falling back to scripted decision
```
Not CLEAN — 14 hits.

Status: **FALSE** — three attempts, three rounds, never CLEAN.

### 5a. Why — two distinct causes, only one of them documented

```
grep -oE 'attempt [12] failed: .*' <decoded log> | sed 's/{.*//' | sort | uniq -c | sort -rn
```

Round 2:
```
     13 attempt 1 failed: llm throttled (429):
     11 attempt 2 failed: llm throttled (429):
      2 attempt 2 failed: mine needs at: one of S1..S6, got ''
      1 attempt 2 failed: switch needs both "if" and "to"
      1 attempt 1 failed: mine needs at: one of S1..S6, got ''
```
Round 3:
```
      5 attempt 2 failed: mine needs at: one of S1..S6, got ''
      4 attempt 1 failed: mine needs at: one of S1..S6, got ''
      2 attempt 2 failed: llm throttled (429):
      2 attempt 1 failed: llm throttled (429):
      1 attempt 1 failed: unknown job: mine at:s2
```
Round 4:
```
      3 attempt 2 failed: llm throttled (429):
      3 attempt 1 failed: llm throttled (429):
      1 attempt 2 failed: mine needs at: one of S1..S6, got ''
      1 attempt 1 failed: unknown job: mine at:s2
```

**Cause A — Bedrock 429, platform-wide (documented exception).** Verbatim from the round-3 log:
```
hidden-agenda llm: bedrock transport, url http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
hidden-agenda llm: seat 0 attempt 1 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
hidden-agenda llm: seat 1 attempt 1 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
hidden-agenda llm: seat 0 attempt 2 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
hidden-agenda llm: seat 1 attempt 2 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
```

Cross-checked against another live coworld per `prompts/60-verify.md` check 5. The **`coins`**
coworld, episode request `ereq_30f2789e-fffe-4cdc-9365-d34b96f2ed3e` completed
**2026-08-26T03:39Z** — the same minute as hidden-agenda's round 2 — shows the same throttle on the
same model, 52 hits, e.g.:
```
2026-08-26 03:39:10,796 INFO httpx HTTP Request: POST https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke "HTTP/1.1 429 Too Many Requests"
2026-08-26 03:39:15,770 INFO httpx HTTP Request: POST https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke "HTTP/1.1 429 Too Many Requests"
2026-08-26 03:39:35,787 INFO httpx HTTP Request: POST https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke "HTTP/1.1 429 Too Many Requests"
```
So cause A is a **platform-wide Bedrock capacity/quota symptom**, documented against `coins`, and is
not a defect in this coworld. The message is a *daily* token quota
(`"Too many tokens per day"`), which did not clear across the 30 minutes of polling (rounds 2, 3 and
4 all hit it). Per the prompt this was not treated as grounds to go Blocked; polling continued to the
retry budget.

**Cause B — this coworld's own reply parser, NOT platform-wide, NOT documented.** Verbatim, round 3:
```
hidden-agenda llm: seat 0 attempt 1 failed: unknown job: mine at:s2
hidden-agenda llm: seat 1 attempt 1 failed: mine needs at: one of S1..S6, got ''
hidden-agenda llm: seat 0 attempt 2 failed: mine needs at: one of S1..S6, got ''
hidden-agenda llm: seat 1 attempt 2 failed: mine needs at: one of S1..S6, got ''
```
In round 3 this is the **majority** cause: 10 of 14 attempt failures are parse rejects, only 4 are
429s. In round 4 it is 2 of 8. These are the model's replies being rejected by
`src/hidden_agenda/llm.nim`, and no throttle is involved.

The mechanism, from the released source (`Metta-AI/cogame-hidden-agenda`,
`src/hidden_agenda/llm.nim`):

```nim
# lines 568-586 — the validator
let jobText = stepNode{"job"}.getStr().strip().toLowerAscii()
…
if not known:
  raise newException(HiddenAgendaError, "unknown job: " & jobText)
…
if job == jkMine:
  step.at = stepNode{"at"}.getStr().strip().toUpperAscii()
  if seamIndex(step.at) < 0:
    raise newException(HiddenAgendaError,
      "mine needs at: one of S1..S6, got '" & step.at & "'")
```

The validator requires a plan step object of the form `{"job":"mine","at":"S2"}`. But the prompt
teaches the model a *different, compact* syntax (line 373):

```
  mine at:<seam>   walk to that seam and mine until your hands are full
  deposit          walk to the grate and drop what you carry
  watch who:<cog>  stand 3-5 cells away and keep your cone on that cog
  patrol room:<r>  sweep a room's four corners looking for bodies
```

…and the reply-schema line (line 520) never shows the argument keys at all:

```nim
lines.add("REPLY with ONLY {\"plan\":[{\"job\":...}], " & …
lines.add("  plan: 1.." & $sim.config.planSteps & " steps; job is one of " & jobList(cog.role))
```

`{"job":...}` with an ellipsis is the only structural example the model ever sees, so it does the
obvious thing and writes the documented compact form into the one key it was shown —
`{"job":"mine at:S2"}` → lowercased → `unknown job: mine at:s2` — or, on the corrective retry, drops
the argument entirely → `{"job":"mine"}` → `at` reads `""` → `mine needs at: one of S1..S6, got ''`.
The retry prompt does not close the gap, so both attempts burn and the seat falls back. Same shape
for `switch` (`switch needs both "if" and "to"`, round 2).

This is a **coworld defect and an undocumented exception**, i.e. a failure by the standard in this
prompt. It is independent of Bedrock capacity and would keep both champions on scripted fallbacks
even with unlimited quota. Suggested fix (for the coordinator to route to phase 30/20 — **not**
applied here, this role does not edit code): make the schema line spell the sibling keys, e.g.
`{"plan":[{"job":"mine","at":"S2"}|{"job":"watch","who":"BLUE"}|{"job":"patrol","room":"NW"}|{"job":"deposit"}], …}`,
and/or have the validator accept the compact `"job":"mine at:S2"` form it already documents by
splitting on whitespace before the job lookup.

---

## 6. The public page uses the static replay path — **TRUE**

**Source used: the SSR payload + the session API** (documented fallback), because the raw-HTML grep
finds nothing — the page is client-rendered, exactly as `playbooks/observatory-api.md` §Featured
match records platform-wide.

```
GET https://softmax.com/hidden-agenda            (fetched 2026-08-26T04:12:40Z)
-> http=200 bytes=570807
grep -o '<iframe[^>]*src="[^"]*"'                -> (no match)
```

Not recorded as a false negative. The coworld detail API is likewise `null` platform-wide, so it is
also not evidence either way:

```
GET $BASE/coworlds?limit=200 | jq '…|select(.name=="hidden_agenda")|{id,canonical,replay_viewer,featured_match,manifest_hash}'
```
```json
{"id":"cow_87de5e19-e661-42cd-81dc-db93b5d25a81","name":"hidden_agenda","canonical":true,
 "replay_viewer":null,"featured_match":null,
 "manifest_hash":"sha256:2d0b0c793c33dc44fde47eec77b62d5a2bd6773b10370fc97036d7088fa16104"}
```

**Featured match — present**, server-rendered into the page's SSR payload at `state.playlist[0]`:
```
grep -o 'playlist\\":\[…' /tmp/page3.html     (04:12:40Z)
```
```
playlist\":[{\"episodeId\":\"18019f70-e617-4e72-baf1-7abbfeb8b283\",\"coworldId\":\"cow_87de5e19-e661-42cd-81dc-db93b5d25a81\"
\"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/7bc69416-04f7-4f16-bad7-6c174412e6df.replay
\"code\":\"hidden_agenda.r4.e1
```
(At 04:00:0xZ the same payload read `hidden_agenda.r3.e1`, replay `93af8bbc-…`, with
`"matchup":{"divisionId":"div_cb85265c-…","divisionName":"Competition","first":{"rank":1,
"player_id":"ply_44ae9048-…","player_name":"daveey","score":1014.5304984710245,…` — the featured
match rolls forward with the ladder. That r3 URL is the one check 8 rendered.)

**The iframe `src`**, from the call the page's own JS makes:
```
POST $BASE/coworlds/replays/session
     {"coworld_id":"cow_87de5e19-…","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/7bc69416-04f7-4f16-bad7-6c174412e6df.replay"}
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_87de5e19-e661-42cd-81dc-db93b5d25a81/sha256%3A2d0b0c793c33dc44fde47eec77b62d5a2bd6773b10370fc97036d7088fa16104/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F7bc69416-04f7-4f16-bad7-6c174412e6df.replay&v=2",
  "ready": true
}
```

Status: **TRUE** — the path is
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`, `ready: true`, and the
`<sha>` is the coworld's `manifest_hash`
(`sha256%3A2d0b0c79…` URL-decodes to the `manifest_hash` returned by `/coworlds` above and to
`STATE.coworld.manifest_sha`). **No `/client/replay` pod URL anywhere.** A featured match is present.

---

## 7. Certification declared the static bundle — **TRUE**

**Source: the committed `runs/2026-08-25-hidden-agenda/release-result.json`** (the copy phase 40
downloaded and committed). It was present; no re-download from the release run was needed.

```
jq -r '.certify.replay_liveness' runs/2026-08-25-hidden-agenda/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE** — contains `Replay liveness: skipped (static replay bundle declared`.

---

## 8. Spectator judgment — the viewer was EXECUTED — **TRUE**

Dispatched against the iframe `src` from check 6 (the r3 featured match, the current one at dispatch
time):

```
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder \
  -f url="https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_87de5e19-e661-42cd-81dc-db93b5d25a81/sha256%3A2d0b0c793c33dc44fde47eec77b62d5a2bd6773b10370fc97036d7088fa16104/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F93af8bbc-50a0-44aa-839d-d8b039f17a84.replay&v=2" \
  -f timeout=90
# dispatched 2026-08-26T04:00:29Z
```

Run found by sorting on `createdAt`, not by taking "the latest" blind. Runs before the dispatch were
`32925387074 (03:09:23Z)`, `32924883541 (03:01:23Z)`, `32923659915 (02:41:21Z)`; after:

```
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 5
32928573158  2026-08-26T04:00:29Z  in_progress     <- created at/after the dispatch: this run
32925387074  2026-08-26T03:09:23Z  completed
32924883541  2026-08-26T03:01:23Z  completed
```
```
gh run watch 32928573158 -R Metta-AI/coworld-builder --exit-status
✓ viewer-check in 35s (ID 98056265379)
  ✓ Load the viewer
  ✓ Upload the evidence
  ✓ Fail if the viewer did not load
exit=0                       # green
gh run download 32928573158 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-25-hidden-agenda/viewer-check
-> viewer-smoke.json (1336 B), viewer-smoke.png (300233 B), smoke-stdout.txt, smoke-stderr.txt (0 B)
```

### Readouts, verbatim from `runs/2026-08-25-hidden-agenda/viewer-check/viewer-smoke.json`

```
jq -c '{loaded, ms, clock, scorebug, feed_lines}' …/viewer-smoke.json
```
```json
{"loaded":true,"ms":2549,"clock":"TICK 4 / 3000 DEPOSITS 0 / 32","scorebug":"CREW DEPOSITS 0 0 / 32 TICK 4 / 3000 DEPOSITS 0 / 32 IMPOSTOR CREW LEFT 4 GREEN · BASELINE","feed_lines":0}
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
Also `"status":"OPEN"`, `"loading_text":null`, `"console_tail":[]`, and
`"canvas_text":{"total":0,"outside":0,"ellipsized":0,"never_inside":0,…}` — no text drawn outside
the canvas, nothing ellipsized.

### The three clock readouts

```
jq -r '.scrub[]|"\(.at)\t\(.clock)"' …/viewer-smoke.json
```

| scrub position | clock readout |
|---|---|
| 0 %   | `TICK 4 / 3000 DEPOSITS 0 / 32` |
| 50 %  | `TICK 370 / 3000 DEPOSITS 4 / 32` |
| 100 % | `TICK 708 / 3000 FINAL` |

**All three differ**, and they differ *monotonically in two independent quantities* — tick
(4 → 370 → 708) and deposits (0 → 4 → final). The scrubber exists and works; this is not a single
frozen frame.

Status: **TRUE** — `loaded: true` (via `data-replay-loaded="true"`, first frame at 2549 ms) **and**
the three clock readouts differ.

### Reconciliation against the replay record

The rendered replay is round 3, `93af8bbc-…` (`/tmp/ep.replay`). Ordered excerpts:

*Early* (`jq -r '.events[]|[.t,(.seat//"-"),.k,…]|@tsv' | head -18`):
```
0	0	reveal
0	1	reveal	   … (5 reveals, one per seat)
0	0	order
0	1	order	   … (5 opening orders)
8	2	freeze
8	-	witness
8	-	witness
8	-	caught
9	-	meeting
9	0	order	nothing solid
9	1	order	GREEN unseen 1 ticks
9	2	order	i was mining
```

*Middle* (`select(.t>=300 and .t<=460)`):
```
325	-	eject
352	-	seam
378	-	seam
388	2	freeze
400	1	mine
```

*Late* (`| tail -20`):
```
472	1	mine
482	1	deposit
483	1	deposit
529	-	meeting
529	0	order	nothing solid
529	1	order	GREEN unseen 1 ticks
539	0/1/2	say
553	0/1/2	vote
585	-	eject
652	-	seam
660	0	mine
708	2	freeze
708	-	witness
708	-	caught
708	-	end
```

The freeze/witness/eject spine, in full:
```json
{"k":"freeze","t":8,"seat":2,"victim":"PINK","cell":[14,11],"room":"THE GRATE","witnesses":["BLUE","YELLOW"]}
{"k":"caught","t":8,"freezer":"GREEN","victim":"PINK","witnesses":["BLUE","YELLOW"]}
{"k":"eject","t":65,"target":null,"tally":{"GREEN":2,"skip":2},"outcome":"skip","wasImpostor":false}
{"k":"eject","t":325,"target":null,"tally":{"GREEN":2,"skip":2},"outcome":"skip","wasImpostor":false}
{"k":"freeze","t":388,"seat":2,"victim":"YELLOW","cell":[13,15],"room":"SOUTH GALLERY","witnesses":[]}
{"k":"eject","t":585,"target":null,"tally":{"GREEN":1,"skip":2},"outcome":"skip","wasImpostor":false}
{"k":"freeze","t":708,"seat":2,"victim":"RED","cell":[13,3],"room":"NORTH GALLERY","witnesses":["BLUE"]}
{"k":"caught","t":708,"freezer":"GREEN","victim":"RED","witnesses":["BLUE"]}
```
```
jq -r '[.events[].k]|group_by(.)|map("\(.[0])=\(length)")|join(" ")'
caught=2 deposit=6 eject=3 end=1 freeze=3 meeting=3 mine=7 order=16 reveal=5 say=11 seam=6 vote=11 witness=3
```

### Spectator-judgment paragraph

**It is legible, and it shows the game.** `viewer-smoke.png` (the 100 %-scrub frame CI captured) is a
dense, readable spectator screen, and every element on it is corroborated by the replay record above.
The top strip is a three-part scorebug: `6 DEPOSITS · CREW · 6 / 32` with a five-pip carry indicator
at the left, `TICK 708 / 3000 · FINAL` centred, and `IMPOSTOR · CREW LEFT 1 · GREEN · BASELINE` at the
right — matching `results.deposits: 6`, `depositTarget: 32`, `ticks: 709` and
`ending: "impostor_isolation"` exactly. Below it sits the roster strip —
`RED daveey | BLUE daveey-1 | GREEN Baseline | YELLOW Baseline (2) | PINK Baseline (3)` — with the
**red ring on GREEN**, the impostor, exactly as the design's chrome spec calls for, and the names
match `results.names` and `.roles` (`GREEN` = `impostor`). A **`CAUGHT! GREEN FROZE RED · BLUE SAW
IT`** banner sits over the board, which is precisely the terminal event pair at t=708 quoted above; a
cog with a drawn vision cone stands beneath it in the north gallery, where the replay says the freeze
happened (`"room":"NORTH GALLERY"`, `cell:[13,3]`). The board itself is a dim grid with seam clusters
(`S2`, `S4`, three-gem glyphs) and the 3×3 grate visible mid-map, and a frozen YELLOW body is still
lying on the floor as evidence — matching the un-witnessed t=388 freeze in SOUTH GALLERY. The
role-reveal **endcard** dominates the centre: `IMPOSTOR WINS — ONE CREWMATE LEFT`, the rules reminder
`CREW WIN AT 32 DEPOSITS OR BY EJECTING THE IMPOSTOR. THE IMPOSTOR WINS AT ONE CREWMATE LEFT.`, the
stat line `3 freezes · 2 witnessed · 0 ejections (right) · 0 fake deposits · 3 meetings` — which is
`results` read out field for field — and the full role reveal (`RED CREW daveey`, `BLUE CREW
daveey-1`, `GREEN IMPOSTOR Baseline`, `YELLOW CREW Baseline (2)`, `PINK CREW Baseline (3)`). At the
bottom is the transport strip — restart, step-back, pause, `+5s`, step-forward, loop, fast-forward, a
`spoilers` toggle, the `IMPOSTOR WINS 708 / 708` status and `1× 2× 3× 4× 8× 16×` speed buttons — over
a scrubber carrying three meeting markers and a **`RACE TO WIN`** momentum graph beneath it. The
picture is neither empty nor frozen nor unreadable.

**Does it look like the starter's chrome? Yes.** This is recognisably the paintbot / coworld-ctf
family: the same transport strip, the same scrubber-with-momentum-graph, the same three-part scorebug
and the same endcard treatment, re-skinned for this game. It is not a rewrite sharing only the ids —
this is not the cogame-gridlock failure. Every game-specific element the design promised is present:
CREW/IMPOSTOR plates, roster strip with the red ring on the impostor, `CAUGHT!` banners, the
`RACE TO WIN` momentum strip, the role-reveal endcard, and vision cones. (The vote board could not be
judged from this frame — the capture is at 100 %, after the last meeting closed — but the replay
carries 11 `vote` events across 3 meetings and the scrubber shows meeting markers, so the state is
reachable.)

**Two legibility observations for the coordinator, neither of them a check-8 failure:**
1. `feed_lines: 0` while the feed is plainly *visible* in the screenshot (bottom-right, dimmed under
   the endcard overlay: `GREEN FROZE … IN NORTH GALLERY`, `SAW IT`). The smoke harness's feed
   selector does not match this shell's feed element. A DOM-selector mismatch, not a missing feed.
2. `signals.bridge_ready: false` with `bridge: []` — the viewer signals readiness via
   `data-replay-loaded="true"` rather than the `coworld-replay` bridge. Both are accepted by the
   check; noting it so nobody reads the empty bridge array as a defect.

**One content observation that is really a check-4/5 finding:** the spectacle is real, but the
*champions* are barely in it. Both meetings' champion `notes` render identical text
(`nothing solid` / `GREEN unseen 1 ticks` at t=9 and again at t=529), all three ejection votes
deadlock `GREEN 2 / skip 2` and eject nobody, and the impostor that wins is `GREEN` — a **scripted
Baseline filler**, not either LLM champion. That is the visible face of the 80–87 % fallback rate
documented in check 4.

---

## Summary

| # | check | verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 2, 3, 4 |
| 2 | both champions ranked, fillers absent/Baseline | **TRUE** |
| 3 | latest round's episode request completed w/ replay + participants | **TRUE** |
| 4 | replay bytes valid and champion seats really deciding | **FALSE** — 80–87 % scripted fallbacks |
| 5 | hosted game log CLEAN | **FALSE** — 4/7/14 `falling back` hits in rounds 4/3/2 |
| 6 | public page uses the static replay path | **TRUE** |
| 7 | certification declared the static bundle | **TRUE** |
| 8 | viewer executed and judged | **TRUE** — `loaded:true`, 3 differing clocks |

Retry budget spent: **3 of 3** on checks 4 and 5 — three different completed rounds (2, 3, 4), each
re-polled and re-fetched fresh. Both remain FALSE. Wall clock used: 03:40Z → 04:15Z, ~35 min of the
75-minute bound; the bound did not expire — the retry budget did.

**The blocking cause is cause B in check 5** — this coworld's plan-step schema hint
(`{"job":...}`) does not tell the model to emit the `at` / `who` / `room` sibling keys the validator
requires, so the model writes the compact `mine at:S2` form the system prompt documents and both
attempts are rejected. That is a coworld defect, undocumented, and independent of the Bedrock 429
throttle (cause A), which is separately confirmed platform-wide against the `coins` coworld at the
same minute.
