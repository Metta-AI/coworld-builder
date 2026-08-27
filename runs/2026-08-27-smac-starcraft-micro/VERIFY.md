# VERIFY — smac-starcraft-micro   (2026-08-27T10:42Z)

Verdict: **1 item false** — checks 1, 2, 3, 4, 6, 7, 8 TRUE; **check 5 FALSE**.

Run: `2026-08-27-smac-starcraft-micro` · slug `smac-starcraft-micro` · version `0.1.2`
`COW = cow_476a8db4-f5df-4d93-b0c2-1c302ba201bc`
`L = league_f42b4821-882b-428e-b803-630671e86726` · `D = div_efd2ab9a-88fd-4c97-952c-64f38e3fadaa`
Champions `smac-starcraft-micro-marshal:v3` (daveey) / `smac-starcraft-micro-skirmish:v3` (daveey-1);
fillers `focusfire:v3` / `charge:v3`.

Every response below was fetched fresh during this phase-60 execution (2026-08-27T10:17Z–10:42Z).
Two documented exceptions, per `prompts/60-verify.md` §Standards: check 7 reads the committed
`runs/<run>/release-result.json`, and check 8's rendered evidence is the artifact of the
`viewer-check.yml` run **this** phase dispatched (run `33063761313`).

Common headers on every Observatory call (values never printed):
`Authorization: Bearer $SOFTMAX_TOKEN`, `User-Agent: coworld-builder/1.0`; elevated calls add
`X-Use-Elevated-Privileges: true`.

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

```
GET https://softmax.com/api/observatory/v2/rounds?league_id=$L&limit=20
    -H Authorization -H User-Agent
HTTP 200   (fetched 2026-08-27T10:34:29Z)
```
```json
[
  {
    "id": "round_d83fe934-6863-4b88-bead-cdc1ff9a56eb",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-27T10:28:40.440538Z"
  },
  {
    "id": "round_b20379cb-f929-431f-ae59-372e03b02015",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-27T10:13:38.911419Z"
  },
  {
    "id": "round_a414900b-02da-4544-9b34-3eb1935a2586",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-27T10:13:00.562652Z"
  }
]
```
```
$ jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
2
```

**Round 1's `error`, verbatim** (does not count, per the prompt: `failed` rounds are excluded):
`Temporal RoundWorkflow failed before settling the round.`
It was created at `10:13:00.562652Z`, i.e. fired by the ladder at the unpause instant, 38 s before
the phase-50 explicit trigger that produced round 2 (`10:13:38.911419Z`).

**Fillers were in effect before both counted rounds** — fetched, not inferred:
```
GET .../leagues/$L/filler-policies   -H Authorization -H User-Agent -H X-Use-Elevated-Privileges
HTTP 200
```
```json
{"filler_policy_versions": [
  {"policy_version_id": "2964b7ba-9e1d-4edb-955c-f9d6c949ede0",
   "policy_name": "smac-starcraft-micro-focusfire", "version": 3,
   "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"},
  {"policy_version_id": "a1ecf538-9599-423c-8170-9a19968738f4",
   "policy_name": "smac-starcraft-micro-charge", "version": 3,
   "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"}
]}
```
and the effect is visible **inside the round-2 and round-3 replay bytes themselves**, which is the
strongest available proof that the filler list was live when those rounds ran (a seat is renamed
only when its version is in that list):
```
$ jq -r '.results.names' /tmp/ep3.json        # round 3
["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)"]
$ jq -r '.results.names' /tmp/ep.json         # round 2
["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)"]
```

**Status: TRUE** — rounds **2** (completed 10:17:27.763890Z) and **3** (completed
10:33:20.483549Z) are completed, both `round_number ≥ 2`, both created after the filler POST
(`log.md` 10:15:53Z entry; corroborated above by the live filler list and by `Baseline*` seat
names in both replays). Round 1 `failed` and is excluded with its error quoted.

---

## 2. Both champions ranked, fillers absent/Baseline — TRUE

```
GET .../divisions/$D/leaderboard   -H Authorization -H User-Agent
HTTP 200   (fetched 2026-08-27T10:34:38Z)
```
```
$ jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
1	daveey-1	smac-starcraft-micro-skirmish:v3	1001.4695015289755	2	1.0
2	daveey	smac-starcraft-micro-marshal:v3	998.5304984710245	2	1.0
```
Full body (bare list, not `.entries`, as `playbooks/observatory-api.md` §11 states):
```json
[
  {"rank": 1, "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
   "player_name": "daveey-1", "score": 1001.4695015289755, "score_label": "MMR",
   "rounds_played": 2, "episode_wins": 1.0, "win_rate": 0.5,
   "policy_label": "smac-starcraft-micro-skirmish:v3"},
  {"rank": 2, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
   "player_name": "daveey", "score": 998.5304984710245, "score_label": "MMR",
   "rounds_played": 2, "episode_wins": 1.0, "win_rate": 0.5,
   "policy_label": "smac-starcraft-micro-marshal:v3"}
]
```

**Status: TRUE** — `daveey` and `daveey-1` both present, each `rounds_played = 2 ≥ 1`, each
carrying its own LLM champion policy label. The two fillers are **absent** from the leaderboard
(the list has exactly two rows), satisfying the "absent or `Baseline…`" requirement.

---

## 3. Latest round's episode request completed with a replay — TRUE

Latest completed round: `round_d83fe934-6863-4b88-bead-cdc1ff9a56eb` (round 3).

The prompt's literal flat route is dead; I recorded the failure and used the nested route the
playbook (§9) pins:
```
GET .../episode-requests?round_id=$R&limit=20   -H Authorization -H User-Agent
HTTP/2 405
allow: POST
{"detail":"Method Not Allowed"}
```
```
GET .../rounds/$R/episode-requests   -H Authorization -H User-Agent
HTTP 200
[{"id":"ereq_bf914c1c-8e9d-4e12-8fe7-0906f27ef584","status":"completed"}]
```
```
GET .../episode-requests/ereq_bf914c1c-8e9d-4e12-8fe7-0906f27ef584   -H Authorization -H User-Agent
HTTP 200   (fetched 2026-08-27T10:34:45Z)
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/a2def614-f588-47eb-a1d6-9db771806a65.replay",
  "participants": [
    {"position": 0, "policy_name": "smac-starcraft-micro-marshal",  "version": 3,
     "player_name": "daveey",   "is_filler": false},
    {"position": 1, "policy_name": "smac-starcraft-micro-skirmish", "version": 3,
     "player_name": "daveey-1", "is_filler": false},
    {"position": 2, "policy_name": "smac-starcraft-micro-focusfire","version": 3,
     "player_name": "daveey",   "is_filler": true},
    {"position": 3, "policy_name": "smac-starcraft-micro-focusfire","version": 3,
     "player_name": "daveey",   "is_filler": true},
    {"position": 4, "policy_name": "smac-starcraft-micro-charge",   "version": 3,
     "player_name": "daveey",   "is_filler": true}
  ],
  "participant_scores": [
    {"position": 0, "score": 0.9110233333333334},
    {"position": 1, "score": 0.9110316666666667},
    {"position": 2, "score": 0.911145},
    {"position": 3, "score": 0.9111177777777778},
    {"position": 4, "score": 0.9110822222222222}
  ]
}
```
Round 3's seated entrants, from the same fetch as check 1 — both champion version ids, neither of
them a filler version id:
```json
"entrant_attributions": [
  {"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player",
   "policy_version_id":"32ec1f23-fb86-47c1-b05f-b94ee099c5fd"},
  {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","subject_type":"player",
   "policy_version_id":"5ef5a887-6ded-4a53-aeef-64b190dc59b9"}
]
```

**Status: TRUE** — `status == "completed"`, non-null `replay_url`, `participants` name **daveey**
(seat 0, marshal:v3) and **daveey-1** (seat 1, skirmish:v3). *Deviation from the prompt's wording:*
this endpoint reports fillers by real `policy_name` with `is_filler: true` rather than as
`Baseline (N)`; the `Baseline (N)` renaming appears in the replay's `results.names` (check 1). The
requirement — champions named, fillers identified as fillers — holds either way.

---

## 4. Replay bytes are valid and show the game — TRUE  *(documented substitute procedure)*

**The replay-format deviation is declared by the design note**, `design.md` §"Replay bytes
(self-sufficient)" (lines 967–992), which states the replay stays the starter's binary
`COWLDSMC` format and pins the phase-60 substitute verbatim:

> **The phase-60 substitute for SPEC §Definition of done check 4:**
> `curl -sSL "$replay_url" -o /tmp/ep.replay` / `python3 tools/replay_summary.py /tmp/ep.replay >
> /tmp/ep.json` / `jq -e . /tmp/ep.json >/dev/null` … Require `protocol ==
> "smac-starcraft-micro/v1"`, `results.reason == "complete"` (or the declared-acceptable
> `deadline`), `results.enemyKilled > 0`, and the champion seats' directives `source == "llm"`
> with non-empty `note` and real intents — not all fallbacks.

The raw bytes are binary, as declared — the prompt's `jq -e . /tmp/ep.replay` cannot apply:
```
$ curl -sSL "https://softmax-public.s3.amazonaws.com/replays/a2def614-f588-47eb-a1d6-9db771806a65.replay" -o /tmp/ep3.replay
HTTP 200 bytes 87463
$ python3 -c "print(repr(open('/tmp/ep3.replay','rb').read(20)))"
b'COWLDSMC\x01\x00\x14\x00smac-sta'
```
`tools/replay_summary.py` was run from a fresh clone of `Metta-AI/cogame-smac-starcraft-micro` at
`main` (`git log --oneline -1` → `bb0323d ci(release): re-read canonical from the platform after
upload-coworld`):
```
$ python3 tools/replay_summary.py /tmp/ep3.replay > /tmp/ep3.json ; echo $?
0
$ jq -e . /tmp/ep3.json >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok
$ jq -r '"protocol=\(.protocol)"' /tmp/ep3.json
protocol=smac-starcraft-micro/v1
$ jq -r '"reason=\(.results.reason)  endRule=\(.results.endRule)  enemyKilled=\(.results.enemyKilled)/\(.results.enemyTotal)  teamScore=\(.results.teamScore)"' /tmp/ep3.json
reason=complete  endRule=victory  enemyKilled=5/5  teamScore=0.911
$ jq -r '"directives_total=\(.directives|length)  llm=\([.directives[]|select(.source=="llm")]|length)  scripted=\([.directives[]|select(.source=="scripted")]|length)  source_fallback=\([.directives[]|select(.source=="fallback")]|length)  fallback_records=\(.fallbacks)  budgetGuards=\(.budgetGuards)"' /tmp/ep3.json
directives_total=95  llm=37  scripted=57  source_fallback=1  fallback_records=3  budgetGuards=0
```
Full `results` document:
```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)"],
 "scores":[0.9110233333333334,0.9110316666666667,0.911145,0.9111177777777778,0.9110822222222222],
 "win":[true,true,true,true,true],
 "role":["ranger","ranger","blade","blade","blade"],
 "alias":["RANGER-alpha","RANGER-beta","BLADE-alpha","BLADE-beta","BLADE-gamma"],
 "damageDealt":[84,114,522,424,296],"damageTaken":[136,130,296,348,360],
 "kills":[0,1,8,4,2],"deaths":[2,1,1,2,3],"shots":[26,35,0,0,0],
 "llmTurns":[18,19,0,0,0],"fallbackTurns":[1,0,0,0,0],
 "teamScore":0.911,"battlesWon":3,
 "battleResults":["victory","victory","victory"],"battleTicks":[601,635,745],
 "battleDamagePct":[100,100,100],"battleLossPct":[93,79,91],
 "enemyKilled":5,"enemyTotal":5,"scenario":"default",
 "reason":"complete","endRule":"victory","games":3,"finalTick":2896,"seed":1125153451}
```
Champion seats' directives are real LLM output, not fallbacks — sample, verbatim from
`/tmp/ep3.json` (`battle turn seat alias source intent target say note`):
```
1	0	0	RANGER-alpha	llm	focus	E2	E2	Turn 0: All enemies out of range. E2 lowest HP (60), closest at 480px. Focus fir…
1	0	1	RANGER-beta	llm	hold	E0	holding	Turn 0: holding post at ranger line per operator guidance
1	1	0	RANGER-alpha	llm	kite	E4	E1	E1 lowest HP in range (30). Melee E4 at 25px → kite. Hold 300px distance.
1	1	1	RANGER-beta	llm	focus	E4	E4	E4 closest at 269px. Our HP 91% vs theirs 78%, gap <25pts. Hold focus fire disci…
2	2	1	RANGER-beta	llm	focus	E5	E5	E5 closest at 104px, lowest hp enemy. Focus fire. Squad at 66% vs 47%, winn…
2	4	1	RANGER-beta	llm	retreat	-	retreat	E5 blade 15px away, attacking me. HP 10/60 (17%) - CRITICAL. Retreat now pe…
3	6	0	RANGER-alpha	llm	hold	E0	dead	I am dead. E4 has 10hp, in range of BLADE-alpha. Squad focus fire to finish.
3	6	1	RANGER-beta	llm	retreat	-	retreat	HP 20/60 critical, retreating per orders. E4 blade 10hp almost dead. BLADE-alpha…
```

**Status: TRUE** —
`protocol == "smac-starcraft-micro/v1"` ✔ (matches the manifest);
`results.reason == "complete"` ✔ (the declared-acceptable `deadline` was not needed);
`results.enemyKilled = 5 > 0` ✔ (whole enemy army destroyed, `endRule: victory`, all 3 battles won);
champion decisions non-scripted with non-trivial content ✔ — **37 of 38 champion-seat directives
are `source == "llm"`** with distinct, board-aware notes naming enemy ids, ranges and HP;
fallbacks are a small minority: **1** of 38 champion turns degraded (`fallbackTurns: [1,0,0,0,0]`
= 2.6 %), and the 57 `scripted` directives are the three intended filler seats, not degraded
champions. The design note's substitute procedure was used exactly as written, and this VERIFY.md
records that **the design note declares it**.

---

## 5. Hosted game log is clean — **FALSE**

```
GET .../episode-requests/ereq_bf914c1c-8e9d-4e12-8fe7-0906f27ef584/artifacts/logs
    -H Authorization -H User-Agent -H X-Use-Elevated-Privileges
HTTP 200 bytes 87784
```
The body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it was
decoded per repr with `ast.literal_eval` before grepping (playbook §10 — line greps undercount
otherwise). Decoded: 87 228 bytes across containers
`['coworld-init-config', 'bedrock-sidecar', 'game', 'worker']`.

```
$ grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs3.txt
271:smac llm: seat 0 attempt 1 failed, falling back if it fails again: reply named no commanded cog
272:smac llm: seat 0 falling back to focusfire (parse_error) on turn 4
```
Per-pattern counts on the decoded text:
```
falling back                     2
LLM provider is unavailable      0
cut off at max_tokens            0
rejected                         0
```
Surrounding context, verbatim (lines 265–275):
```
blue killed by red
blue sprayed paint
red sprayed paint
red sprayed paint
blue sprayed paint
red killed by blue
smac llm: seat 0 attempt 1 failed, falling back if it fails again: reply named no commanded cog
smac llm: seat 0 falling back to focusfire (parse_error) on turn 4
red sprayed paint
blue sprayed paint
red sprayed paint
```
Every `smac llm:` line in the whole log:
```
165:smac llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
271:smac llm: seat 0 attempt 1 failed, falling back if it fails again: reply named no commanded cog
272:smac llm: seat 0 falling back to focusfire (parse_error) on turn 4
```

**The documented exceptions do not apply, and I checked rather than assumed.**
`LLM provider is unavailable` = 0 and `cut off at max_tokens` = 0. There is **no Bedrock capacity
symptom**: every sidecar call in this episode returned 200, e.g.
```
2026-08-27 10:32:01,684 INFO __main__ bedrock_sidecar_complete {… "model":
"global.anthropic.claude-haiku-4-5-20251001-v1:0", "operation":"InvokeModel", "ok":true,
"status_code":200, "latency_ms":1558.497…, "error_kind":null, "error_type":null, "message":null …}
```
and a grep for `429|throttl|too many requests|ServiceUnavailable|capacity` matched **only** those
`ok:true, status_code:200` sidecar records — no throttling at all. So the "platform-wide Bedrock
capacity" exception in `prompts/60-verify.md` check 5 is **not** available here, and there is
nothing to wait out inside the 75-minute bound. The cause is this coworld's own reply-parse path:
`cause: parse_error`, `detail: reply named no commanded cog`.

**Cross-check documented** (what I compared against, per the brief). Latest completed episode of
the closest ctf-lineage LLM sibling, `knights-archers`
(`ereq_546a162a-39b2-4580-8dd8-6aaf18834e9c`, 206 035 decoded bytes), fetched this run:
```
falling back                     89
LLM provider is unavailable      0
cut off at max_tokens            0
rejected                         0
  HIT: knights-archers llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
  HIT: knights-archers llm: seat 2 attempt 1 failed, falling back if it fails again: llm throttled (429): {"message":"Too many tokens per day, please wait before tryin…
  HIT: knights-archers llm: seat 2 falling back to phalanx (parse_error) on turn 3
  HIT: knights-archers llm: seat 2 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.c…
  … (89 hits total; 429 throttling and sidecar timeouts throughout)
```
and `paintbot` (the direct lineage parent, `ereq_5cd82a4c-5f51-4c4d-8c5c-72c4366a0d4f`, 8 016
decoded bytes): all four patterns **0**.

The comparison **does not excuse this coworld**: knights-archers' hits are dominated by genuine
429/timeout platform symptoms, whereas this coworld's two hits carry no platform error at all —
they are a model reply that omitted the commanded cog id, twice failing this coworld's own
`extractJsonObject`/directive parse, on the same seat and turn (seat 0, turn 4 of battle 3).

**Status: FALSE.** The check requires `CLEAN`; the decoded game log contains 2 matching lines and
no documented exception covers a `parse_error`. `design.md` mentions the grep (line 378) but
**declares no exception for it** — an undocumented exception is a failure, so I am not marking
this true.

*Three approaches attempted, all fetched fresh this run:*
1. **Round 3's episode** (`ereq_bf914c1c…`, the latest round, chained from check 3) → 2 hits.
2. **Round 2's episode** (`ereq_e860f660-02bb-4be8-9321-1c08965e9bc0`, a different round —
   the prompt's sanctioned "different round" retry) → **1 hit**, and no fallback actually taken:
   ```
   $ grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.txt
   255:smac llm: seat 0 attempt 1 failed, falling back if it fails again: reply named no commanded cog
   ```
   ```
   falling back 1 · LLM provider is unavailable 0 · cut off at max_tokens 0 · rejected 0
   ```
   Round 2's replay confirms the retry succeeded — `fallbackTurns: [0,0,0,0,0]`, 0 directives with
   `source == "fallback"`, and the single `fallback` chat record is attempt-level only:
   ```
   {"k": "fallback", "battle": 2, "turn": 0, "seat": 0, "attempt": 1,
    "cause": "parse_error", "detail": "reply named no commanded cog"}
   ```
3. **Cross-check against other LLM coworlds' latest logs** (knights-archers, paintbot, above) to
   test the platform-cause exception → refuted: no throttling, no `LLM provider is unavailable`,
   all Bedrock calls 200. Round 3 also had only one episode request, so there is no alternative
   episode within that round to read.

**Severity for the coordinator's decision (not a verdict change):** the defect is small and
bounded — 1 hit in round 2 (no degradation), 2 hits in round 3 (1 champion turn of 38 degraded to
`focusfire`). It is exactly the failure mode `AGENTS.md` §"Degrade, never hang" designs for, and it
did not stop the episode (`reason: complete`, `endRule: victory`, 5/5 enemy killed). But check 5's
bar is a zero-line grep, and it is not zero.

---

## 6. The public page uses the static replay path — TRUE

**Source used: fallback (b), the `replays/session` route the page's own JS calls.** Recorded here
because the prompt requires saying which source produced the `src`. Both prior sources were tried
first and are non-evidence for this platform, exactly as
`playbooks/observatory-api.md` §"Featured match / replay route" (lighthouse run, 2026-08-22)
predicts:

*(i) raw-HTML iframe grep — finds nothing; the page is client-rendered:*
```
$ curl -sS "https://softmax.com/smac-starcraft-micro" | grep -o '<iframe[^>]*src="[^"]*"'
HTTP 200 bytes 671111   (fetched 2026-08-27T10:35:58Z)
(nothing — page is client-rendered)
```

*(ii) `/coworlds` detail — `featured_match` and `replay_viewer` are null platform-wide:*
```
GET .../coworlds?limit=200   -H Authorization -H User-Agent      HTTP 200
$ jq -c '…|select(.name=="smac-starcraft-micro" and .canonical==true)|{id,canonical,replay_viewer,featured_match}'
{"id":"cow_476a8db4-f5df-4d93-b0c2-1c302ba201bc","canonical":true,"replay_viewer":null,"featured_match":null}
```

*(iii) **the featured match is server-rendered into the page's SSR payload at
`state.playlist[0]`** — pasted from `/tmp/page2.html` with the doubled JSON escaping undone:*
```json
"playlist":[{"episodeId":"ce48d6b9-5dba-4539-9cd3-1302d13c8531",
 "coworldId":"cow_476a8db4-f5df-4d93-b0c2-1c302ba201bc",
 "coworldName":"smac-starcraft-micro","coworldVersion":"0.1.2",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/a2def614-f588-47eb-a1d6-9db771806a65.replay",
 "finishedAt":"2026-08-27T10:33:20.483549Z","roundNumber":3,"episodeNumber":1,
 "code":"smac-starcraft-micro.r3.e1",
 "matchup":{"divisionId":"div_efd2ab9a-88fd-4c97-952c-64f38e3fadaa","divisionName":"Competition",
  "first":{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
           "score":1001.4695015289755,"score_label":"MMR","rounds_played":2,"episode_wins":1,
           "win_rate":0.5,"policy_label":"smac-starcraft-micro-skirmish:v3"},
  "second":{"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
            "score":998.5304984710245,…}}}]
```

*(iv) the iframe `src`, from the call the page's JS makes:*
```
POST .../coworlds/replays/session   -H Authorization -H User-Agent -H content-type
 -d '{"coworld_id":"cow_476a8db4-f5df-4d93-b0c2-1c302ba201bc",
      "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/a2def614-f588-47eb-a1d6-9db771806a65.replay"}'
HTTP 200
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_476a8db4-f5df-4d93-b0c2-1c302ba201bc/sha256%3A4575435fea3737665c72aa4ed75fc6621b6d5407b82234eb8359d66c75df8c38/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fa2def614-f588-47eb-a1d6-9db771806a65.replay&v=2",
  "ready": true
}
```
The `<sha>` segment is the coworld's **manifest_hash**, URL-encoded, and it matches STATE:
```
$ jq -r '.coworld.manifest_sha' runs/2026-08-27-smac-starcraft-micro/STATE.json
sha256:4575435fea3737665c72aa4ed75fc6621b6d5407b82234eb8359d66c75df8c38
```

**Status: TRUE** — a **featured match is present** (SSR `playlist[0]`, round 3 episode 1, with a
two-player matchup naming both champions), and the iframe `src` is the **static** path
`/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` with `ready: true` and a
path ending `/index.html`. There is **no** `/client/replay` pod URL anywhere in the response.

---

## 7. Certification declared the static bundle — TRUE  *(documented exception: committed artifact)*

**Source read: the committed `runs/2026-08-27-smac-starcraft-micro/release-result.json`** — phase
40's downloaded artifact, present in the run directory, so the `gh run download` re-fetch was not
needed. Not read from `/tmp` (that sandbox is gone).
```
$ jq -r '.certify.replay_liveness' runs/2026-08-27-smac-starcraft-micro/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

**Status: TRUE** — the string contains `Replay liveness: skipped (static replay bundle declared`
exactly as required.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — TRUE

*(a) Dispatch, against the iframe `src` from check 6.*
```
$ SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_476a8db4-f5df-4d93-b0c2-1c302ba201bc/sha256%3A4575435fea3737665c72aa4ed75fc6621b6d5407b82234eb8359d66c75df8c38/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fa2def614-f588-47eb-a1d6-9db771806a65.replay&v=2'
$ date -u +%Y-%m-%dT%H:%M:%SZ                 # dispatch_at
2026-08-27T10:36:17Z
$ gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
$ gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
   | jq -r 'sort_by(.createdAt)|reverse|.[0:3][]|"\(.databaseId)\t\(.createdAt)\t\(.status)"'
33063761313	2026-08-27T10:36:18Z	in_progress
33063093381	2026-08-27T10:27:11Z	completed        <- NOT mine: a parallel run's dispatch
33062642745	2026-08-27T10:21:00Z	completed        <- mine, secondary exhibit (see below)
```
Find-the-new-run by `createdAt`, not "the latest", mattered here: an unrelated run
(`33063093381`, 10:27:11Z) sits between my two dispatches. My run is the one created **after**
`dispatch_at`: **`33063761313`**.
```
$ gh run watch 33063761313 -R Metta-AI/coworld-builder --exit-status
  ✓ viewer-check
  ✓ Load the viewer
  ✓ Fail if the viewer did not load
watch_exit=0        # green
$ gh run download 33063761313 -R Metta-AI/coworld-builder -n viewer-check \
    -D runs/2026-08-27-smac-starcraft-micro/viewer-check
-rw-r--r--  0       smoke-stderr.txt
-rw-r--r--  754     smoke-stdout.txt
-rw-r--r--  1550    viewer-smoke.json
-rw-r--r--  734904  viewer-smoke.png
```
Committed at `runs/2026-08-27-smac-starcraft-micro/viewer-check/`.

*(b) The readouts, verbatim.*
```
$ jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/…/viewer-check/viewer-smoke.json
{"loaded":true,"ms":4471,"clock":"1:00 BATTLE 1/3 · DEFAULT · 5 V 5 · TURN 1/12","scorebug":"─▸ daveey DMG 0 0k ─▸ daveey-1 DMG 0 0k ╱ Baseline DMG 0 0k 1:00 BATTLE 1/3 · DEFAULT · 5 V 5 · TURN 1/12 ╱ Baseline ( DMG 0 0k ╱ Baseline ( DMG 0 0k OURS 5 UP · 480/480 (100%) THEIRS 5 UP · 480/480 (100%)","feed_lines":0}
```
```
$ jq -c '.signals' runs/…/viewer-check/viewer-smoke.json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```
```
$ jq -r '.failure // "no failure"' runs/…/viewer-check/viewer-smoke.json
no failure
$ jq -c '{status,loading_text,canvas_text:.canvas_text.total,console_tail}' runs/…/viewer-check/viewer-smoke.json
{"status":"OPEN","loading_text":null,"canvas_text":0,"console_tail":[]}
```

**The three clock readouts** (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | `#clock` readout |
|---|---|
| 0 %   | `1:00 BATTLE 1/3 · DEFAULT · 5 V 5 · TURN 1/12` |
| 50 %  | `0:38 BATTLE 1/3 · DEFAULT · 2 V 1 · TURN 5/12` |
| 100 % | `:01 BATTLE 2/3 · DEFAULT · 1 V 0 · TURN 7/12` |

All three **differ** — in clock, in battle index, in alive counts and in turn index.

**Item 8 criteria: `loaded: true` ✔ (via `data-replay-loaded="true"`; `data_replay_error: null`,
`failure: null`, `loading_text: null`, no console errors) AND the three clock readouts differ ✔.
→ TRUE.** A `#scrub` element was present, so the "no `#scrub`" branch did not apply.

*(c) The replay record the viewer was asked to draw* — ordered excerpts from `/tmp/ep3.json`
(the check-4 substitute view of the same bytes the iframe loads), so the readouts can be
reconciled against the recording:
```
=== EARLY (battle 1, turns 0–1)
1	0	0	RANGER-alpha	llm	focus	E2	E2	Turn 0: All enemies out of range. E2 lowest HP (60), closest at 480px. Focus fir…
1	0	1	RANGER-beta	llm	hold	E0	holding	Turn 0: holding post at ranger line per operator guidance
1	0	2	BLADE-alpha	scripted	focus	E2	E2	focus fire
1	0	3	BLADE-beta	scripted	focus	E2	E2	focus fire
1	0	4	BLADE-gamma	scripted	attack_move	E2	go	charge
1	1	0	RANGER-alpha	llm	kite	E4	E1	E1 lowest HP in range (30). Melee E4 at 25px → kite. Hold 300px distance.
1	1	1	RANGER-beta	llm	focus	E4	E4	E4 closest at 269px. Our HP 91% vs theirs 78%, gap <25pts. Hold focus fire disci…

=== MIDDLE (battle 2, champion seats, all turns)
2	0	0	RANGER-alpha	llm	focus	E3	E3 is at 2hp, closest enemy. One shot from RANGER-beta finishes it. I focus…
2	1	0	RANGER-alpha	llm	kite	E1	E1 lowest hp (30), closest to rangers. E2 at 50hp also in range. E1 is kill…
2	2	1	RANGER-beta	llm	focus	E5	E5 closest at 104px, lowest hp enemy. Focus fire. Squad at 66% vs 47%, winn…
2	3	1	RANGER-beta	llm	focus	E5	E5 blade at 16px, attacking me. Hp 50/60 (83%). Focus E5 with squad. Winnin…
2	4	1	RANGER-beta	llm	retreat	retreat	E5 blade 15px away, attacking me. HP 10/60 (17%) - CRITICAL. Retreat now pe…
2	5	0	RANGER-alpha	llm	focus	E3	E3 last enemy, 32 hp. FINISH IT. Focus fire.
2	5	1	RANGER-beta	llm	hold		I am dead. Cannot act.

=== LATE (battle 3, final two turns)
3	6	0	RANGER-alpha	llm	hold	E0	dead	I am dead. E4 has 10hp, in range of BLADE-alpha. Squad focus fire to finish.
3	6	1	RANGER-beta	llm	retreat	-	retreat	HP 20/60 critical, retreating per orders. E4 blade 10hp almost dead. BLADE-alpha…
3	6	2	BLADE-alpha	scripted	screen	E4	screen	focus fire
3	6	3	BLADE-beta	scripted	screen	E4	screen	focus fire
3	6	4	BLADE-gamma	scripted	attack_move	E4	go	charge
```
```
$ jq -r '.results' /tmp/ep3.json | (the full document is pasted under check 4)
battleResults ["victory","victory","victory"] · battleTicks [601,635,745] · enemyKilled 5/5 ·
teamScore 0.911 · reason "complete" · endRule "victory"
$ jq -r 'reduce .directives[] as $d ({}; .[($d.battle|tostring)] += [$d.turn]) | to_entries[] | "battle \(.key): turns \(.value|unique|min)..\(.value|unique|max)"'
battle 1: turns 0..5
battle 2: turns 0..5
battle 3: turns 0..6
```

### Spectator-judgment paragraph

**It is legible, and it shows the game.** The rendered screenshot
(`runs/2026-08-27-smac-starcraft-micro/viewer-check/viewer-smoke.png`, 1280×800, from run
`33063761313`) is a full broadcast page, not a blank canvas and not a loading spinner: a five-plate
scorebug across the top naming the real policies — `daveey` DMG 4, `daveey-1` DMG 12,
`Baseline` DMG 40 on the left, `Baseline (` DMG 90 and `Baseline (` DMG 70 on the right — a centred
clock reading `0:18` under the caption `BATTLE 2/3 · DEFAULT · 5 V 5 · TURN 9/12`, two labelled
army bars (`OURS 5 UP · 344/480 (72%)` / `THEIRS 5 UP · 264/480 (55%)`), the painted top-down arena
in real art (tiled concrete floor, wooden crates and chevron cover, the two spawn pads with red and
cyan runes, the red and blue spawn lines), red cogs and blue cogs with per-unit HP pips and a
`holding` shout bubble over a red ranger, and a transport strip with restart / step-back / play /
`+5s` / step / loop / fast-forward / `spoilers` buttons, a `1009 / 2365` tick readout and the
`1× 2× 3× 4× 8× 16×` speed row, above an `ARMY HP LEAD` momentum graph with a visible playhead.
**It does look like the starter's chrome** — the same transport strip, the same scrubber-plus-
momentum-graph pairing, the same scorebug plate geometry and the same locker-room art family as
paintbot/raid/hive; this is a fork, not the cogame-gridlock rewrite-sharing-ids failure. Motion is
proven independently of the picture: the three scrub readouts advance through the episode
(`1:00 BATTLE 1/3 · 5 V 5` → `0:38 BATTLE 1/3 · 2 V 1` → `:01 BATTLE 2/3 · 1 V 0`), and that arc
reconciles with the record — battle 1 ran 601 ticks and cost us 93 % of army health
(`battleLossPct[0] = 93`), which is exactly the `2 V 1` attrition the 50 % readout shows, and the
episode ends `["victory","victory","victory"]`, 5/5 enemies killed. The screenshot also shows the
game *being played by models*: the `holding` bubble is `RANGER-beta`'s `say`, and the replay record
confirms that string occurs exactly once in the whole episode — battle 1, turn 0, seat 1, note
"Turn 0: holding post at ranger line per operator guidance". **Two honest caveats.** First,
`feed_lines: 0` is an **instrument** limitation, not an empty feed: `viewer_smoke.mjs` line 425
probes `#feed, .feed, #log`, and this coworld's match feed — like the starter's — is `#killfeed`
(verified in the clone: `client/replay_broadcast.html` contains `id="killfeed"`, and no
`#feed`/`#log`/`.feed` element exists). The harness therefore cannot count this lineage's feed at
all; that is a coworld-builder template finding, not a defect here. Second, in this one captured
frame the canvas and the HUD disagree: the arena shows both squads clustered on their spawn pads
with all ten units alive and the battle-1-turn-0 `holding` bubble, while the caption reads
`BATTLE 2/3 · TURN 9/12` at tick `1009/2365` with army bars already down to 72 %/55 % — and
`0:18` remaining implies 42 s elapsed in a battle the record says lasted 635 ticks (~32 s). The
screenshot is taken immediately after the 100 % seek, so the most likely cause is that the capture
landed during the viewer's post-seek re-simulation walk (HUD already jumped, canvas still catching
up); **I cannot prove that from the artifact**, so I record it as an observation. It does not make
item 8 false — `loaded` is true, the three readouts differ, and the secondary exhibit below shows
a fully coherent mid-combat frame — but the coordinator should treat "the frame you see right after
a scrub may be stale" as a phase-30 legibility note.

**Secondary exhibit** (same phase, earlier dispatch, kept because it is this run's other rendered
evidence): run **`33062642745`**, dispatched 2026-08-27T10:20:58Z against the then-featured round-2
replay (`0658673b-…`), green, artifact saved to
`runs/2026-08-27-smac-starcraft-micro/viewer-check-secondary-round2/`. Verbatim:
```
{"loaded":true,"ms":6453,"clock":"1:00 BATTLE 1/3 · DEFAULT · 5 V 5 · TURN 1/12","scorebug":"─▸ daveey DMG 0 0k ─▸ daveey-1 DMG 0 0k ╱ Baseline DMG 0 0k 1:00 BATTLE 1/3 · DEFAULT · 5 V 5 · TURN 1/12 ╱ Baseline ( DMG 0 0k ╱ Baseline ( DMG 0 0k OURS 5 UP · 480/480 (100%) THEIRS 5 UP · 480/480 (100%)","feed_lines":0}
scrub readouts: 0%="1:00 BATTLE 1/3 · DEFAULT · 5 V 5 · TURN 1/12"  50%=":02 BATTLE 2/3 · DEFAULT · 3 V 0 · TURN 5/12"  100%="0:26 BATTLE 2/3 · DEFAULT · 5 V 4 · TURN 7/12"
```
Its screenshot shows mid-arena combat at tick `820/2139`: five red cogs and four blue cogs engaged
around the centre cover, a red shot tracer in flight, per-unit HP bars, a `BLADE-gamma: charge`
directive tooltip, army bars `5 UP · 338/480 (70%)` / `4 UP · 336/480 (70%)`, and the same
transport strip and `ARMY HP LEAD` graph. That frame is coherent with its record and is the
clearest single proof that this viewer draws the game rather than a placeholder.

---

## Summary table

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 2 & 3 completed; round 1 `failed` (Temporal race), excluded with error quoted |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey & daveey-1, `rounds_played 2` each; fillers absent |
| 3 | Latest round's episode request completed with replay | **TRUE** — `completed`, `replay_url` non-null, both champions seated |
| 4 | Replay bytes valid and show the game | **TRUE** — via the design note's declared `replay_summary.py` substitute; `complete`/`victory`, 5/5 killed, 37/38 champion directives `llm` |
| 5 | Hosted game log clean | **FALSE** — 2 × `falling back` (`parse_error`, "reply named no commanded cog"); no documented exception applies (no throttling, all Bedrock calls 200) |
| 6 | Public page uses the static replay path | **TRUE** — SSR `playlist[0]` featured match + static `/index.html` src, `ready:true`, no `/client/replay` |
| 7 | Certification declared the static bundle | **TRUE** — committed `release-result.json`: `Replay liveness: skipped (static replay bundle declared…` |
| 8 | Spectator judgment (executed viewer) | **TRUE** — `loaded:true`, three differing clock readouts, legible starter chrome |

Wall clock used: 10:17:17Z → 10:42Z (~25 min of the 75-minute bound). `heartbeat_at` refreshed on
every poll (last confirmed value read back from Asana: `2026-08-27T10:37:38Z`).

Artifacts written by this phase:
`runs/2026-08-27-smac-starcraft-micro/viewer-check/{viewer-smoke.json,viewer-smoke.png,smoke-stdout.txt,smoke-stderr.txt}`
and `runs/2026-08-27-smac-starcraft-micro/viewer-check-secondary-round2/{viewer-smoke.json,viewer-smoke.png}`.
No code, STATE, log.md, league, division, round or policy was created or modified.
