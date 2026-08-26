# VERIFY — knights-archers, coworld version **0.1.3** (fetched 2026-08-26 14:49Z–15:43Z)

Verdict: **all 8 items TRUE.**

Ids under test:

- coworld `cow_23e4f026-6724-4b80-bb34-dcd02c214ee2` v0.1.3,
  manifest `sha256:d0773202419ec87be0fe873839c0f6be817b03ee21ca2dd95bf108b5512e91c6`
- league `league_362e5211-3bdc-40f4-968e-c00c8f812bfe`, division `div_264f45de-06ac-4657-b454-85d27f9e63fc`
- champions `daveey → knights-archers-warden:v3` (`c289e272-961f-4fee-86c2-a5be57e1480c`),
  `daveey-1 → knights-archers-volley:v3` (`fbd70f34-d9e3-4b23-b8f4-6816549e5a21`)
- fillers `knights-archers-phalanx:v3` (`eb972301-…`), `knights-archers-stand:v3` (`83dfcd5d-…`)

Checks **3, 4 and 5 are pinned to round 3** (`round_6102955b-fc29-4c61-b671-64b032d9878b`,
completed 14:55:33Z), the latest completed round at fetch time. Round 2's episode is kept below as
**§Trend record** because it is the one that shows the difference is an upstream LLM-provider
outage window and not the build.

Auth on every Observatory call: headers `Authorization: Bearer $SOFTMAX_TOKEN` and
`User-Agent: coworld-builder/1.0`; artifact reads and the filler-policy read additionally send
`X-Use-Elevated-Privileges: true`. Header **values are never printed**.
`BASE=https://softmax.com/api/observatory/v2`.

Two documented exceptions to "fetch fresh, every item, this run", both allowed by
`prompts/60-verify.md`:

- **check 7** — the evidence is the committed `runs/2026-08-26-knights-archers/release-result.json`
  (phase 40's artifact copy, the 0.1.3 run 32978063250), re-read from the working tree this phase;
- **check 8** — the rendered evidence comes from `viewer-check.yml` run **32982870977, which I
  dispatched in this phase at 14:51:29Z**, downloaded into
  `runs/2026-08-26-knights-archers/viewer-check/`. A second dispatch at 15:04:44Z (run
  32984003113) never left the Actions queue; see check 8 (a). Nothing from an earlier heartbeat is
  reused.

| # | Check | Verdict | Evidence pinned to |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | **TRUE** | rounds 1, 2, 3 all `completed`, zero failed/discarded; fillers in place before round 1 was triggered |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** | daveey-1 rank 1, daveey rank 2, `rounds_played` 3 each; both fillers registered and absent |
| 3 | Latest round's episode completed with a replay | **TRUE** | round 3 · `ereq_2e17e8b4` · daveey + daveey-1 + 2 `is_filler` seats |
| 4 | Replay bytes valid; champions really playing | **TRUE** | round 3 · `protocol knights-archers/v1`, `reason complete`, **36/36 champion directives `llm`, 0 fallbacks** |
| 5 | Hosted game log clean | **TRUE** | round 3 · **0** matching lines in all four containers, decoded; 36/36 Bedrock calls 200 |
| 6 | Public page featured match on the **static** replay path | **TRUE** | featured `knights-archers.r3.e1`, static path, `ready: true` |
| 7 | Certification declared the static bundle | **TRUE** | committed `release-result.json` (0.1.3) |
| 8 | Viewer actually renders and advances | **TRUE** | run 32982870977 (dispatched 14:51:29Z this phase) — `loaded: true`, three differing clock readouts, same static bundle |

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

Fillers were registered **before round 1 was triggered**. `log.md` records the two phase-50 steps
in order (both lines carry the phase's batch-write stamp `14:19:41Z`, not the call time, so the
ordering evidence is the line order *plus* the two independent facts below):

```
2026-08-26T14:19:41Z 50 filler-policies 200: phalanx:v3=eb972301-0632-406c-b3b8-548eb99d8013, stand:v3=83dfcd5d-36de-4369-9ff0-9dffdf70cc65 (neither champion's)
2026-08-26T14:19:41Z 50 unpause 200 paused=false; trigger-round 200 workflow=ladder-league_362e5211; round 1 pending, …
```

1. `playbooks/observatory-api.md` §6: "A `trigger-round` issued before any filler exists **fails
   instantly** with `Temporal RoundWorkflow failed before settling the round`." Round 1 did not
   fail — it settled, `status completed`, `error null`.
2. Round 1's own episode seated two filler policies, re-fetched at **15:43:27Z** from
   `GET $BASE/episode-requests/ereq_0e53a404-edcb-4b7d-a614-b2f35c967c93` (HTTP 200):
```json
[{"position":0,"policy_name":"knights-archers-warden","version":3,"player_name":"daveey","is_filler":false,"policy_version_id":"c289e272-961f-4fee-86c2-a5be57e1480c"},
 {"position":1,"policy_name":"knights-archers-volley","version":3,"player_name":"daveey-1","is_filler":false,"policy_version_id":"fbd70f34-d9e3-4b23-b8f4-6816549e5a21"},
 {"position":2,"policy_name":"knights-archers-stand","version":3,"player_name":"daveey","is_filler":true,"policy_version_id":"83dfcd5d-36de-4369-9ff0-9dffdf70cc65"},
 {"position":3,"policy_name":"knights-archers-stand","version":3,"player_name":"daveey","is_filler":true,"policy_version_id":"83dfcd5d-36de-4369-9ff0-9dffdf70cc65"}]
```

Every round in this league therefore ran with the fillers already in place, so **all** completed
rounds count for this check — and in any case rounds **2 and 3** alone satisfy "≥ 2 completed
rounds after the fillers were set" under any reading.

```
GET $BASE/rounds?league_id=league_362e5211-3bdc-40f4-968e-c00c8f812bfe&limit=20
  headers: Authorization, User-Agent                          (fetched 15:03:35Z)
→ HTTP 200, 8766 bytes
```

`jq -r '(if type=="array" then . else .entries end)|.[]|[.round_number,.id,.status,(.error|tostring),.created_at,.completed_at]|@tsv'`:

```
3	round_6102955b-fc29-4c61-b671-64b032d9878b	completed	null	2026-08-26T14:51:00.582003Z	2026-08-26T14:55:33.117693Z
2	round_cd7563e8-7bac-4adc-ac60-f4dc65701dc5	completed	null	2026-08-26T14:35:59.374900Z	2026-08-26T14:41:54.368292Z
1	round_e2dad982-7bf8-4b9d-b3c5-26402af0c69c	completed	null	2026-08-26T14:18:37.375198Z	2026-08-26T14:27:04.462979Z
```

`jq -r '… |[.[]|select(.status=="completed")]|length'` → **3**.

There are **no** `failed` or `discarded` rounds in this league: every `error` field above is
`null`, so there is nothing to quote verbatim.

Both champions were seated in every round — `round_config.entrant_attributions` for rounds 1, 2
and 3 is identical and names exactly the two champion policy versions:

```json
[{"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player",
  "policy_version_id":"c289e272-961f-4fee-86c2-a5be57e1480c",
  "league_policy_membership_id":"lpm_eafb32fd-0a92-48d5-b0aa-1fa7b1da03f8"},
 {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","subject_type":"player",
  "policy_version_id":"fbd70f34-d9e3-4b23-b8f4-6816549e5a21",
  "league_policy_membership_id":"lpm_7d89e128-a65b-4037-95a6-3671eea722ad"}]
```

Polling record (every 5 minutes, per `prompts/60-verify.md` §Waiting; bound 75 min from 14:20Z):

```
2026-08-26T14:21:29Z poll=1 completed=0 [{"n":1,"s":"pending"}]
2026-08-26T14:26:29Z poll=2 completed=0 [{"n":1,"s":"pending"}]
2026-08-26T14:31:30Z poll=3 completed=1 [{"n":1,"s":"completed"}]
2026-08-26T14:36:30Z poll=4 completed=1 [{"n":2,"s":"pending"},{"n":1,"s":"completed"}]
2026-08-26T14:41:30Z poll=5 completed=1 [{"n":2,"s":"pending"},{"n":1,"s":"completed"}]
2026-08-26T14:46:31Z poll=6 completed=2 [{"n":2,"s":"completed"},{"n":1,"s":"completed"}]
2026-08-26T14:55:23Z poll=7 completed=2 [{"n":3,"s":"pending"},{"n":2,"s":"completed"},{"n":1,"s":"completed"}]
2026-08-26T15:00:25Z poll=8 completed=3 [{"n":3,"s":"completed"},{"n":2,"s":"completed"},{"n":1,"s":"completed"}]
```

Status: **TRUE** — 3 completed rounds, 0 failed, all of them after the fillers were set at
14:19:41Z. (Polling continued past the 2-round minimum on purpose: see check 4 §Trend record.)

---

## 2. Both champions ranked; fillers absent or Baseline — TRUE

```
GET $BASE/divisions/div_264f45de-06ac-4657-b454-85d27f9e63fc/leaderboard
  headers: Authorization, User-Agent                          (fetched 15:03:35Z)
→ HTTP 200
```

Bare list, pasted whole:

```json
[
 {"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
  "score":1002.8046975081021,"score_label":"MMR","score_value_type":"integer","rounds_played":3,
  "episode_wins":1.0,"episodes_played":null,"win_rate":0.3333333333333333,
  "policy_label":"knights-archers-volley:v3","recent_rounds":null},
 {"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
  "score":997.1953024918979,"score_label":"MMR","score_value_type":"integer","rounds_played":3,
  "episode_wins":1.0,"episodes_played":null,"win_rate":0.3333333333333333,
  "policy_label":"knights-archers-warden:v3","recent_rounds":null}
]
```

`jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'`:

```
1	daveey-1	knights-archers-volley:v3	1002.8046975081021	3	1.0
2	daveey	knights-archers-warden:v3	997.1953024918979	3	1.0
```

Both champions present, each `rounds_played = 3 ≥ 1`. Only these two rows exist — no external
players have joined this ladder.

The fillers are registered and are **not** on the leaderboard (this read 403s on bare AUTH; the
elevated header was sent):

```
GET $BASE/leagues/league_362e5211-3bdc-40f4-968e-c00c8f812bfe/filler-policies
  headers: Authorization, User-Agent, X-Use-Elevated-Privileges   → HTTP 200 (fetched 15:03:35Z)
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"eb972301-0632-406c-b3b8-548eb99d8013","policy_id":"e5f3adce-5a7d-4664-9899-d6335676ee61",
  "policy_name":"knights-archers-phalanx","version":3,
  "player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},
 {"policy_version_id":"83dfcd5d-36de-4369-9ff0-9dffdf70cc65","policy_id":"c83b4abb-4b54-433f-b9d2-415c0d899f59",
  "policy_name":"knights-archers-stand","version":3,
  "player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```

Both filler version ids (`eb972301-…`, `83dfcd5d-…`) differ from both champion version ids
(`c289e272-…`, `fbd70f34-…`). In the episode itself the filler seats are renamed by the platform —
the replay's `names` array (check 4) reads
`["daveey","daveey-1","Baseline","Baseline (2)"]`.

Status: **TRUE** — daveey and daveey-1 both ranked with 3 rounds played; fillers registered,
distinct from the champions, absent from the leaderboard and rendered as `Baseline` in play.

---

## 3. Latest round's episode request completed with a replay — TRUE

Latest completed round: **3**, `round_6102955b-fc29-4c61-b671-64b032d9878b`, completed 14:55:33Z.

The flat route is dead, as `playbooks/observatory-api.md` §9 records — confirmed again this run:

```
GET $BASE/episode-requests?round_id=round_cd7563e8-…&limit=20
  headers: Authorization, User-Agent                          → HTTP 405 (probed 14:49:30Z)
```

So the nested route was used:

```
GET $BASE/rounds/round_6102955b-fc29-4c61-b671-64b032d9878b/episode-requests
  headers: Authorization, User-Agent                          → HTTP 200 (fetched 15:03:44Z)
```
```json
[{"id":"ereq_2e17e8b4-8b3c-4595-b7a4-897dbd44dc1b","status":"completed",
  "created_at":"2026-08-26T14:51:01.143131Z"}]
```

One episode request in the round (4 seats, 2 champions + 2 fillers, one episode per round).

```
GET $BASE/episode-requests/ereq_2e17e8b4-8b3c-4595-b7a4-897dbd44dc1b
  headers: Authorization, User-Agent                          → HTTP 200 (fetched 15:03:44Z)
```
`jq '{status, replay_url, participants, participant_scores}'` (participants trimmed to the fields
this check is about; `kind`/`policy_id`/`is_seed` omitted):

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/ccba0605-029c-40f4-8306-0f59140c8223.replay",
  "participants": [
    {"position":0,"policy_name":"knights-archers-warden","version":3,
     "player_name":"daveey","is_filler":false,"policy_version_id":"c289e272-961f-4fee-86c2-a5be57e1480c"},
    {"position":1,"policy_name":"knights-archers-volley","version":3,
     "player_name":"daveey-1","is_filler":false,"policy_version_id":"fbd70f34-d9e3-4b23-b8f4-6816549e5a21"},
    {"position":2,"policy_name":"knights-archers-phalanx","version":3,
     "player_name":"daveey","is_filler":true,"policy_version_id":"eb972301-0632-406c-b3b8-548eb99d8013"},
    {"position":3,"policy_name":"knights-archers-stand","version":3,
     "player_name":"daveey","is_filler":true,"policy_version_id":"83dfcd5d-36de-4369-9ff0-9dffdf70cc65"}
  ],
  "participant_scores": [
    {"position":0,"score":0.0895},
    {"position":1,"score":0.08975},
    {"position":2,"score":0.08875},
    {"position":3,"score":0.088}
  ]
}
```

Status: **TRUE** — `completed`, non-null `replay_url`, participants naming `daveey`
(warden:v3) and `daveey-1` (volley:v3) as the two non-filler seats, the other two flagged
`is_filler: true` and seated as `Baseline` / `Baseline (2)` in the replay.

The four scores being nearly identical (0.0880–0.08975) is the game working as designed, not a
bug: `design.md` §Winning makes `teamScore` **the same for all four seats** and leaves only a
0.004-wide personal kill credit as a tie-break.

---

## 4. Replay bytes valid and showing the game — TRUE

The knights-archers replay is **binary**, magic `COWLDKAZ`, so `jq` on the raw bytes fails **by
design** — `design.md` §Replay bytes ("The phase-60 substitute for SPEC §Definition of done
check 4") prescribes `tools/replay_summary.py`, a stdlib-only decoder that prints one strict-UTF-8
JSON object. The repo was cloned fresh this phase at `main` = `4f7488f`.

```
curl -sSL https://softmax-public.s3.amazonaws.com/replays/ccba0605-029c-40f4-8306-0f59140c8223.replay -o /tmp/ep.replay
→ HTTP 200  bytes 60084  content-type application/octet-stream        (fetched 15:03:56Z)

first 8 bytes: b'COWLDKAZ'
first 48 bytes hex: 434f574c444b415a01000f006b6e69676874732d6172636865727301003148b38d3ea00100003d087b226d6f74696f6e

jq -e . /tmp/ep.replay          → raw: NOT json (binary COWLDKAZ, per design §Replay bytes)
python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
jq -e . /tmp/ep.json            → strict UTF-8 JSON: ok
```

```
jq -r '.protocol, .results.reason, .results.teamKills' /tmp/ep.json
knights-archers/v1
complete
16
```

`protocol == "knights-archers/v1"` matches the manifest (the coworld detail's `game.protocols`
declares the knights-archers wire protocol inherited from `coworld-ctf`; `gameVersion` `1`).
`results.reason == "complete"` — the natural end the design note names, no `deadline` exception
needed.

Header block:

```json
{"protocol":"knights-archers/v1","gameVersion":"1","seed":913477391,
 "names":["daveey","daveey-1","Baseline","Baseline (2)"],
 "aliases":["KNIGHT-alpha","KNIGHT-beta","ARCHER-alpha","ARCHER-beta"],
 "roles":["knight","knight","archer","archer"],
 "policyKinds":["llm","llm","scripted","scripted"],
 "waves":2,"fallbacks":0,"ndirectives":72,"budgetGuards":0}
```

`results`, decoded from the replay's own `result` control record (not from the platform):

```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],
 "scores":[0.0895,0.08975,0.08875,0.088],"win":[false,false,false,false],
 "role":["knight","knight","archer","archer"],
 "alias":["KNIGHT-alpha","KNIGHT-beta","ARCHER-alpha","ARCHER-beta"],
 "kills":[6,7,3,0],"hits":[6,7,12,0],"shots":[7,7,21,0],
 "llmTurns":[18,18,0,0],"fallbackTurns":[0,0,0,0],
 "teamScore":0.088,"teamKills":16,"wavesCleared":0,
 "waveTicks":[576,1128],"waveEndRules":["casualty","casualty"],"waveKills":[3,13],
 "closestCallPx":[780,732],
 "reason":"complete","endRule":"casualty","games":2,"finalTick":2063,"seed":913477391}
```

**Champion decisions are non-scripted and there are zero fallbacks.**

```
jq '[.directives[]|{seat,source}]|group_by(.seat)|map({seat:.[0].seat,
      llm:([.[]|select(.source=="llm")]|length),
      scripted:([.[]|select(.source=="scripted")]|length),
      fallback:([.[]|select(.source=="fallback")]|length)})'
```
```json
[{"seat":0,"llm":18,"scripted":0,"fallback":0},
 {"seat":1,"llm":18,"scripted":0,"fallback":0},
 {"seat":2,"llm":0,"scripted":18,"fallback":0},
 {"seat":3,"llm":0,"scripted":18,"fallback":0}]
```

36 of 36 champion-seat directives are `source: "llm"`; `fallbacks` is **0** (not "a small
minority" — none). Seats 2 and 3 are the fillers and are correctly `scripted`.

The content is non-trivial — every LLM directive carries a real `note`, a legal `intent`, a map
target and a ≤10-rune `say`, and the two champions visibly play their published strategies
(warden intercepts in its own lane; volley screens the leader so both archers can focus it):

```
wave turn seat alias        source lat_ms intent     target       say        note (first 70 runes)
1    0    0    KNIGHT-alpha llm    3770   hold       [400,209]    north      Wave 1 start, no zombies yet. I'm at y=209 (north). Ready to intercept
1    0    1    KNIGHT-beta  llm    3770   hold       [560,240]    choke      Wave 1 turn 0: no zombies yet. Moving to choke position [560,240]
1    0    2    ARCHER-alpha scripted 0    hold       [300,240]    choke      hold the gate
1    0    3    ARCHER-beta  scripted 0    hold       [300,420]    choke      hold the posts
1    1    0    KNIGHT-alpha llm    4549   intercept  [1163,40]    Z0         Turn 1: Single zombie at [1163,40] (north, y=40). 1128 px from gate. I
1    1    1    KNIGHT-beta  llm    4549   screen     [1163,40]    screen     Wave 1 T1: Leader at gate_px=1128 (>600). Intercept 2nd-closest. Only
1    2    0    KNIGHT-alpha llm    2574   intercept  [1066,146]   Z0         T2: 2 zombies spawned. Z0 at y=146 (north, gate_px=1032), Z1 at y=543
1    2    1    KNIGHT-beta  llm    2574   screen     [1066,146]   Z0lead     Wave 1 T2: Leader Z0 at gate_px=1032 (<600). Screen leader at [1066,14
```
```
2    4    0    KNIGHT-alpha llm    3600   intercept  [852,367]    Z0         T4: Z0 gate_px=828 (north), intercept. Z1 south. KNIGHT-beta screening
2    4    1    KNIGHT-beta  llm    3600   screen     [852,367]    Z0         T4: Leader Z0 at gate_px=828 (<600). Screen Z0. Archers focus Z0.
2    4    2    ARCHER-alpha scripted 0    focus      [852,367]    loose      hold the gate
2    4    3    ARCHER-beta  scripted 0    hold       [300,420]    choke      hold the posts
```
```
2    10   0    KNIGHT-alpha llm    1632   intercept  [814,628]    Z10        T10: I'm at y=530 (south half). Z10 gate_px=780 (closest, lunging Beta
2    10   1    KNIGHT-beta  llm    1632   screen     [814,628]    Z10 lead   T10: Leader Z10 gate_px=780 (<600). Screen leader. Archers focus Z10.
2    11   0    KNIGHT-alpha llm    3661   intercept  [875,623]    Z12        South half (y=497). Z12 closest in south at gate_px=840, lunging me. I
2    11   1    KNIGHT-beta  llm    3661   screen     [840,228]    Z13        T11: Leader Z13 gate_px=816 (<600). Screen leader at [840,228]. Archer
2    11   2    ARCHER-alpha scripted 0    focus      [840,228]    loose      hold the gate
2    11   3    ARCHER-beta  scripted 0    hold       [300,420]    choke      hold the posts
```

Latencies 1.6–4.5 s are real model round-trips, cross-checked against the 36 Bedrock 200s in
check 5.

Status: **TRUE** — strict-UTF-8 JSON via the design-declared decoder, `protocol` matches,
`results.reason == "complete"`, `teamKills 16 > 0`, and **36/36 champion directives are `llm`
with 0 fallbacks**.

### §Trend record — round 2's episode (kept because it explains the retry, not to prop the check up)

Round 2 (`ereq_0e3442e5-006b-4818-87df-15e85cba08e4`, replay `fb25d37a-…`, fetched 14:49:44Z)
would have made this check **FALSE**: it is **100 % fallback** —

```json
{"llmTurns":[0,0,0,0],"fallbackTurns":[35,35,0,0],"reason":"complete","endRule":"casualty",
 "teamKills":71,"wavesCleared":0}
```

The cause is entirely upstream and is documented under check 5 §Round-2 outage window: the
platform's LLM sidecar was routed to `openrouter.ai` and every request came back **402 Payment
Required**, surfaced to the game as `anthropic error 503 {"message":"LLM provider is
unavailable"}`. Round 1 (14:18Z) and round 3 (14:51Z) both went to
`bedrock-runtime.us-east-1.amazonaws.com` and both got 200s. Per `prompts/60-verify.md` §Waiting
I kept polling inside the 75-minute bound rather than going Blocked, and round 3 landed clean at
14:55:33Z, well inside it. Round 1 for the record: `llmTurns [25,25,0,0]`,
`fallbackTurns [10,10,0,0]`, `reason "complete"` — a 71 % LLM majority; see §Observations for the
separate `turnSpacingMs` finding it exposes.

---

## 5. Hosted game log is clean — TRUE

```
GET $BASE/episode-requests/ereq_2e17e8b4-8b3c-4595-b7a4-897dbd44dc1b/artifacts/logs
  headers: Authorization, User-Agent, X-Use-Elevated-Privileges     (fetched 15:04:16Z)
→ HTTP 200  bytes 77134
```

The body is python `b'…'` byte-string reprs under `===== container: <name> =====` headers, so it
was decoded per repr with `ast.literal_eval` before grepping — a line-based grep undercounts
(escrow, 2026-08-23). Both greps are pasted; both agree.

```
grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected'  (raw body)
0
```
```
decoded per container:
== container coworld-init-config:   0 decoded lines,     0 chars,  0 matching
== container bedrock-sidecar:     147 decoded lines, 74183 chars,  0 matching
== container game:                 78 decoded lines,  2545 chars,  0 matching
== container worker:                0 decoded lines,     0 chars,  0 matching
TOTAL matching lines: 0 -> CLEAN
```

**CLEAN** — the first branch of the check, with no exception invoked.

Corroboration from the same log's `bedrock-sidecar` container:

```
HTTP results:  Counter({'200 OK': 36})
ok flags:      Counter({'true': 36})
endpoints:     Counter({'https://bedrock-runtime.us-east-1.amazonaws.com': 36})
2026-08-26 14:51:07,916 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1",
  "has_role_arn":true,…,"episode_request_id":"2e17e8b4-8b3c-4595-b7a4-897dbd4…","role":"game","slot":"game"}
```

36 invocations, 36 successes, zero throttles, zero 5xx — exactly the 36 `llm` directives check 4
counted.

The whole `game` container, head and tail (78 lines; nothing is elided in the middle except
per-tick `swings`/`looses an arrow` chatter):

```
1: knights-archers config: host=0.0.0.0 port=8080 seed=913477391 speed=1x minPlayers=4 slots=4 maxTicks=2304 maxGames=2 map=arena
2: Using map file: arena
3: starting knights-archers on 0.0.0.0:8080
4: board render caches baked in 1291 ms
5: knights-archers llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
6: waiting for players: 0/4, need 4 more
7: player connected: daveey-1
8: player connected: daveey
9: seat 1 registered: kind=llm baseline=phalanx
10: seat 0 registered: kind=llm baseline=phalanx
11: waiting for players: 2/4, need 2 more
12: player connected: Baseline (2)
13: player connected: Baseline
14: Dropped message to disconnected client
15: squads built: 4 cogs, 4 seats, regime resident
16: seat 2 registered: kind=scripted baseline=phalanx
17: seat 3 registered: kind=scripted baseline=stand
18: game starting in 5
…
70: red was caught by the dead
71: wave over: casualty, kills=13
72: red win
73: wave 2 done: casualty, kills=13, closest call=732px
74: Writing replay file: /tmp/knights-archers-replay-1.bitreplay
75: Replay written: /tmp/knights-archers-replay-1.bitreplay (60084 bytes)
76: Events written: /coworld/events.json (250 events, 55299 bytes)
77: Frame pacing: 1704 playing frames — skipped 1679 (98.5%), waited 6 (0.4%), late 19 (1.1%)
78: Player traffic: 12.7 MB to 4 players — images 7.8 MB (61.7%), objects 4.9 MB (38.3%)
```

Status: **TRUE** — zero matching lines, raw and decoded.

### §Round-2 outage window (documentation for check 4's §Trend record; NOT used to pass check 5)

Round 2's log (`ereq_0e3442e5-…`, fetched 14:49:53Z, HTTP 200, 13391 bytes) is **NOT CLEAN**:

```
== container coworld-init-config:   0 decoded lines,     0 chars,  0 matching
== container bedrock-sidecar:      11 decoded lines,  1622 chars,  0 matching
== container game:                251 decoded lines, 11326 chars, 78 matching
TOTAL matching lines: 78 -> NOT CLEAN
```
```
[game:24] knights-archers llm: seat 0 attempt 1 failed, falling back if it fails again: anthropic error 503: {"message":"LLM provider is unavailable"}
[game:25] knights-archers llm: seat 1 attempt 1 failed, falling back if it fails again: anthropic error 503: {"message":"LLM provider is unavailable"}
[game:26] knights-archers llm: seat 0 attempt 2 failed, falling back if it fails again: anthropic error 503: {"message":"LLM provider is unavailable"}
[game:27] knights-archers llm: seat 1 attempt 2 failed, falling back if it fails again: anthropic error 503: {"message":"LLM provider is unavailable"}
[game:28] knights-archers llm: seat 0 falling back to phalanx (parse_error) on turn 0
[game:29] knights-archers llm: seat 1 falling back to phalanx (parse_error) on turn 0
…
```

The cause is above the game container, in the platform's own sidecar — its whole log for that
episode:

```
2026-08-26 14:36:06,956 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1",…,
  "episode_request_id":"0e3442e5-006b-4818-87df-15e85cba08e4","role":"game","slot":"game",
  "image_digest":"sha256:d568703a2f4329e4f956d74c80c2be4bda0a4a79c1a172db56a3ed9d18d1732f"}
[2026-08-26 14:36:07 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-08-26 14:36:16,408 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 402 Payment Required"
2026-08-26 14:36:18,895 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 402 Payment Required"
2026-08-26 14:36:18,935 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 402 Payment Required"
2026-08-26 14:36:19,005 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 402 Payment Required"
2026-08-26 14:36:25,276 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 402 Payment Required"
2026-08-26 14:36:25,305 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 402 Payment Required"
2026-08-26 14:36:25,335 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 402 Payment Required"
2026-08-26 14:36:25,353 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 402 Payment Required"
```

**Cross-check against another LLM coworld, made this phase** (`prompts/60-verify.md` check 5
requires it before a platform cause may be named). `particle-worlds` — a different coworld, a
different image digest (`sha256:f4af453a…`), a different run in flight — latest episode
`ereq_5e1001a2-f94f-4af5-8eeb-4d354981569a` created 14:40:25Z:

```
GET $BASE/episode-requests/ereq_5e1001a2-f94f-4af5-8eeb-4d354981569a/artifacts/logs
  headers: Authorization, User-Agent, X-Use-Elevated-Privileges     (fetched 14:50:47Z)
→ HTTP 200  bytes 51691

== container bedrock-sidecar: 163 decoded lines, 20470 chars,   0 matching
== container game:            296 decoded lines, 30581 chars, 240 matching
TOTAL matching lines: 240 -> NOT CLEAN

[game:23] particle-worlds llm: seat 0 attempt 1 failed, falling back if it fails again: anthropic error 503: {"message":"LLM provider is unavailable"}
[game:24] particle-worlds llm: seat 1 attempt 1 failed, falling back if it fails again: anthropic error 503: {"message":"LLM provider is unavailable"}

160 × POST https://openrouter.ai/api/v1/messages "HTTP/1.1 402 Payment Required"
2026-08-26 14:40:41,248 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 402 Payment Required"
```

Same minute, same endpoint, same 402, same 503 surfaced to the game, in a coworld this run did not
build. It is a **platform-wide LLM-provider outage window** (`SPEC §Parallelism and per-run
isolation`: LLM capacity is the one resource parallel runs share), and it had closed by round 3.
Check 5 does **not** rest on it — round 3's log is clean on the first branch.

---

## 6. The public page uses the static replay path — TRUE

```
curl -sS https://softmax.com/knights-archers                (fetched 15:04:24Z)
→ HTTP 200, 589026 bytes
grep -o '<iframe[^>]*src="[^"]*"'   → NO MATCH
```

Per `prompts/60-verify.md` check 6 an empty grep is *unknown*, not a failure: the page is
client-rendered (`playbooks/observatory-api.md` §Featured match, answered by the lighthouse run).
**Which source I used: the page's own SSR payload (`state.playlist[0]`) plus the
`POST /coworlds/replays/session` call the page's JS makes** — both pasted below. (`/coworlds`'
`featured_match` is `null` platform-wide and is not evidence; for the record, fetched 14:20:32Z it
was `{"id":"cow_23e4f026-…","name":"knights-archers","version":"0.1.3","canonical":true,
"replay_viewer":null,"featured_match":null}`.)

`state.playlist[0]`, unescaped out of the page bytes:

```json
{"episodeId":"edfae485-e1f9-4046-a65c-83ce662323f2",
 "coworldId":"cow_23e4f026-6724-4b80-bb34-dcd02c214ee2",
 "coworldName":"knights-archers","coworldVersion":"0.1.3",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/ccba0605-029c-40f4-8306-0f59140c8223.replay",
 "finishedAt":"2026-08-26T14:54:50.223445Z","roundNumber":3,"episodeNumber":1,
 "code":"knights-archers.r3.e1",
 "matchup":{"divisionId":"div_264f45de-06ac-4657-b454-85d27f9e63fc","divisionName":"Competition",
   "first":{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
            "score":1002.8046975081021,"rounds_played":3,"episode_wins":1,
            "policy_label":"knights-archers-volley:v3"},
   "second":{"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
            "score":997.1953024918979,"rounds_played":3,"episode_wins":1,
            "policy_label":"knights-archers-warden:v3"}},
 "inspectUrl":"/observatory/v2?tab=overview&detail=episode-request:ereq_2e17e8b4-8b3c-4595-b7a4-897dbd44dc1b",
 "outcome":"first"}
```

A featured match **is** present, it is the **0.1.3** coworld, and it is the latest completed
round's episode (round 3, the same `ereq_2e17e8b4` checks 3–5 are pinned to).

```
POST $BASE/coworlds/replays/session
  headers: Authorization, User-Agent, content-type
  body: {"coworld_id":"cow_23e4f026-6724-4b80-bb34-dcd02c214ee2",
         "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/ccba0605-029c-40f4-8306-0f59140c8223.replay"}
→ HTTP 200                                                    (fetched 15:04:35Z)
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_23e4f026-6724-4b80-bb34-dcd02c214ee2/sha256%3Ad0773202419ec87be0fe873839c0f6be817b03ee21ca2dd95bf108b5512e91c6/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fccba0605-029c-40f4-8306-0f59140c8223.replay&v=2",
  "ready": true
}
```

Field by field: `/v2/coworlds/replays/**static**/` ✓ ·
`cow_23e4f026-6724-4b80-bb34-dcd02c214ee2` = STATE's 0.1.3 cow id ✓ ·
`sha256%3Ad0773202419ec87be0fe873839c0f6be817b03ee21ca2dd95bf108b5512e91c6` = STATE's 0.1.3
manifest sha, URL-encoded ✓ · path ends `/index.html?replay=<s3 url>` ✓ ·
**no `/client/replay` anywhere in the URL** ✓ · `ready: true` ✓.

Status: **TRUE** — featured match `knights-archers.r3.e1` on coworld 0.1.3, served from the static
wasm bundle at the declared cow id and manifest sha.

---

## 7. Certification declared the static bundle — TRUE

Source read: **the committed `runs/2026-08-26-knights-archers/release-result.json`** — phase 40's
artifact copy of release run **32978063250** (version 0.1.3), already in the working tree, so no
re-download from `gh run download` was needed and `/tmp` was never consulted.

```
jq -r '.certify.replay_liveness' runs/2026-08-26-knights-archers/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Contains `Replay liveness: skipped (static replay bundle declared` ✓.

Surrounding fields from the same file, for context:

```json
{"version":"0.1.3","ok":true,"cow_id":"cow_23e4f026-6724-4b80-bb34-dcd02c214ee2",
 "manifest_sha":"sha256:d0773202419ec87be0fe873839c0f6be817b03ee21ca2dd95bf108b5512e91c6",
 "canonical":true,"hosted_smoke":"passed","certify":{"ok":true, …},
 "secret_put":true,"errors":[],"step_failed":null}
```

and the certification transcript's own tail, verbatim from `.certify.output_tail`:

```
  [pass] replay-present: a replay artifact was produced
  [pass] replay-loadable: the replay artifact has a declared viewer path
  [pass] players-run: every declared player actually started on the smoke episode (not just declared)
  [pass] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks
Certified dist/coworld_manifest.json
Transcript: coworld-executable (10 steps passed)
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE** — read from the committed `release-result.json`, 10/10 transcript steps, the
static-bundle skip present verbatim.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — TRUE

The sandbox has no screen and no browser, so nothing here was rendered locally: the iframe `src`
was opened in headless chromium **in CI**, by a `viewer-check.yml` run I dispatched in this phase,
and the readouts below were downloaded from that run's artifact.

### (a) Dispatch

```
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_23e4f026-6724-4b80-bb34-dcd02c214ee2/sha256%3Ad0773202419ec87be0fe873839c0f6be817b03ee21ca2dd95bf108b5512e91c6/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Ffb25d37a-4e12-4b48-9c13-f9c332961e6f.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90   (14:51:29Z)

gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:3][]|[.databaseId,.createdAt,.status]|@tsv'
32982870977	2026-08-26T14:51:31Z	in_progress     <- created AFTER my dispatch; this is the run
32978130047	2026-08-26T14:05:38Z	completed
32967129036	2026-08-26T12:10:17Z	completed

gh run watch 32982870977 -R Metta-AI/coworld-builder --exit-status
✓ main viewer-check · 32982870977 — viewer-check in 41s (ID 98223601698)
  ✓ Load the viewer   ✓ Summary   ✓ Upload the evidence   ✓ Fail if the viewer did not load
watch exit=0     (green; the gate step "Fail if the viewer did not load" passed)

gh run download 32982870977 -R Metta-AI/coworld-builder -n viewer-check \
  -D runs/2026-08-26-knights-archers/viewer-check
  viewer-smoke.json (1583 B)  viewer-smoke.png (807764 B)  smoke-stdout.txt  smoke-stderr.txt (0 B)
```

The artifact is committed at `runs/2026-08-26-knights-archers/viewer-check/`.

**Which replay this run rendered, and why that is the right evidence.** Run 32982870977 was
dispatched at 14:51:29Z against the iframe `src` that check 6 returned *at that moment* — the same
static bundle, pointed at round 2's replay (`fb25d37a-…`). A **second** dispatch at 15:04:44Z
against the round-3 `src` (run **32984003113**) was still `status: "queued"` 38 minutes later at
15:42:53Z — GitHub-hosted runner capacity for the org was exhausted (`propagate-secrets`
32984047591, queued 15:05:42Z, was stuck behind it too), so it produced no artifact inside the
75-minute bound and **is not cited here**. Item 8 therefore rests on 32982870977, and the two
`src` values differ **only** in the `?replay=` target:

```
static/cow_23e4f026-6724-4b80-bb34-dcd02c214ee2/sha256%3Ad0773202419ec87be0fe873839c0f6be817b03ee21ca2dd95bf108b5512e91c6/index.html
   ?replay=…/fb25d37a-4e12-4b48-9c13-f9c332961e6f.replay   <- rendered (round 2)
   ?replay=…/ccba0605-029c-40f4-8306-0f59140c8223.replay   <- featured now (round 3)
```

Same cow id, same manifest sha, same bundle — this is the paintball 2026-08-25 precedent, and it
is a render of *this* coworld's *live hosted* viewer against a *real ladder* replay, dispatched in
this phase.

### (b) The readouts, verbatim from `runs/2026-08-26-knights-archers/viewer-check/viewer-smoke.json`

```
jq -c '{loaded, ms, clock, scorebug, feed_lines}' …/viewer-smoke.json
{"loaded":true,"ms":3615,"clock":"1:36 TIME LEFT WAVE 1/2 · 0 ALIVE · TURN 0/24","scorebug":"⚔ player-0 KILLS 0 0 SWINGS ⚔ player-1 KILLS 0 0 SWINGS 1:36 TIME LEFT WAVE 1/2 · 0 ALIVE · TURN 0/24 ➹ player-2 KILLS 0 0 SHOTS · 0 HITS ➹ player-3 KILLS 0 0 SHOTS · 0 HITS 0 DEAD WALKING · LEADER 1152PX","feed_lines":0}
```
```
jq -c '.signals' …/viewer-smoke.json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["ready"],"bridge_ready":true,"bridge_error":[]}
```
```
jq -r '.failure // "no failure"' …/viewer-smoke.json
no failure
```
```
jq -c '.canvas_text' …/viewer-smoke.json
{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
```
```
"status": "OPEN",  "loading_text": null,  "console_tail": ["[bridge] ready"]
```

The three scrub readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub | clock readout |
|---|---|
| **0 %** | `1:36 TIME LEFT WAVE 1/2 · 0 ALIVE · TURN 0/24` |
| **50 %** | `1:00 TIME LEFT WAVE 1/2 · 4 ALIVE · TURN 9/24` |
| **100 %** | `0:40 TIME LEFT WAVE 1/2 · 5 ALIVE · TURN 14/24` |

The `#scrub` element **is** present (the readouts are real, not the `"(no #scrub…)"` sentinel) and
the three readouts **differ**, monotonically: turn 0 → 9 → 14, clock 1:36 → 1:00 → 0:40, zombies
alive 0 → 4 → 5. The viewer draws and it advances.

**Item 8 gate:** `loaded: true` ✓ **and** three differing clock readouts ✓ → **TRUE**.

`canvas_text.never_inside == 0` — no caption was ever drawn outside the canvas (the cogchemists
2026-08-24 failure mode); the counter is 0 across the board because this shell's text is DOM
chrome, not canvas-drawn.

### (c) The replay JSON the viewer was asked to draw

Rendered replay `fb25d37a-…` (round 2), decoded with `tools/replay_summary.py` — its results:

```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],
 "scores":[0.3956338028169014,0.3956338028169014,0.3947323943661972,0.394],
 "win":[false,false,false,false],"role":["knight","knight","archer","archer"],
 "alias":["KNIGHT-alpha","KNIGHT-beta","ARCHER-alpha","ARCHER-beta"],
 "kills":[29,29,13,0],"hits":[29,29,36,0],"shots":[30,32,68,0],
 "llmTurns":[0,0,0,0],"fallbackTurns":[35,35,0,0],
 "teamScore":0.394,"teamKills":71,"wavesCleared":0,
 "waveTicks":[1833,1371],"waveEndRules":["casualty","casualty"],"waveKills":[40,31],
 "closestCallPx":[828,912],"reason":"complete","endRule":"casualty",
 "games":2,"finalTick":3585,"seed":1594961442}
```

Ordered directive excerpts (early / middle / late; champion seats only):

```
early
1	0	0	KNIGHT-alpha	fallback	hold	[547,227]	choke
1	0	1	KNIGHT-beta	fallback	hold	[548,431]	choke
1	1	0	KNIGHT-alpha	fallback	intercept	[1162,589]	on it
1	1	1	KNIGHT-beta	fallback	intercept	[1162,589]	on it
middle
1	13	0	KNIGHT-alpha	fallback	intercept	[1035,565]	on it
1	13	1	KNIGHT-beta	fallback	intercept	[1067,400]	on it
1	14	0	KNIGHT-alpha	fallback	intercept	[1059,183]	on it
1	14	1	KNIGHT-beta	fallback	intercept	[1088,330]	on it
late
2	13	0	KNIGHT-alpha	fallback	intercept	[1122,565]	on it
2	13	1	KNIGHT-beta	fallback	intercept	[1156,600]	on it
2	14	0	KNIGHT-alpha	fallback	intercept	[1110,374]	on it
2	14	1	KNIGHT-beta	fallback	intercept	[1143,427]	on it
```

(Every directive in this particular replay is a `phalanx` fallback — that is the round-2 provider
outage of check 5, and it is why checks 3–5 are pinned to round 3 instead. It does not weaken the
render: the sim, the horde, the kills and the two waves are all real.)

### The spectator-judgment paragraph

`viewer-smoke.png` (committed alongside) shows a **legible, populated, moving game**, and it is
**the starter's chrome**, not a rewrite. Top-left: two knight plates with a red ✗ mortality glyph,
`15 KILLS player-0 / 15 SWINGS` and `16 KILLS player-1 / 16 SWINGS`. Top-centre: the transport
clock, `0:30 TIME LEFT`, under it `WAVE 1/2 · 8 ALIVE · TURN 16/24`. Top-right: two archer plates,
`player-2 KILLS 4 / 28 SHOTS · 12 HITS` and `player-3 KILLS 0 / 0 SHOTS · 0 HITS` — which matches
the replay exactly, where ARCHER-beta (`stand`, seat 3) never fires. Under the plates runs the
horde-pressure bar with `8 DEAD WALKING · LEADER 948PX`. The board itself is the 1235×659 arena:
the striped gate strip down the left edge, the dark-red breach zone down the right with ~8 green
zombies filing out of it, four red hero markers holding the middle with live speech bubbles
(`close`, `loose`, `on it`) exactly as the `say` field in the directives above, and an orange
dashed vertical chalk line at the closest a zombie has come to the gate. Along the bottom is the
starter's transport strip — rewind, step-back, play, `+5s`, step, loop, fast-forward, a `spoilers`
toggle, the tick counter `1591 / 3396`, and 1×/2×/3×/4×/8×/16× speed buttons — over a scrubber
carrying the `KILLS vs HORDE PRESSURE` momentum graph with the playhead at ~40 %. Transport strip,
scrubber with momentum graph, scorebug, hero plates: this is paintbot/raid/hive's chrome
retargeted, not a different product (the cogame-gridlock 2026-08-23 failure mode is **not**
present). Reconciled against the replay: the picture's `WAVE 1/2 · TURN 16/24` and 8 zombies alive
sit inside wave 1's 1833 ticks; the plate kill counts (15/16/4/0) are a mid-episode slice of the
final 29/29/13/0; the shout bubbles are the recorded `say` values. Two legibility nits, neither
fatal and both recorded below for phase 30: the hero plates read `player-0 … player-3` rather than
the replay's own `names` (`daveey`, `daveey-1`, `Baseline`, `Baseline (2)`) or its `aliases`
(`KNIGHT-alpha` …), so a spectator cannot tell which champion is which; and `feed_lines: 0` — the
commander-line feed the design promises was empty at capture time. Neither empty, nor frozen, nor
unreadable: it is a watchable horde-defence match.

---

## Observations for the coordinator (not check failures)

All eight checks are TRUE. These are findings I am **reporting, not fixing** (verifiers do not
edit code); none of them falsifies a check on the pinned round 3.

**O1 — `turnSpacingMs` (9000) exceeds `turnBudgetMs` (7000), and the resulting fallback latches
for the rest of the episode.** Round 1's episode (`ereq_0e53a404-…`, replay `10f56783-…`) ran 25
LLM turns per champion seat and then fell back on **every** remaining turn (wave 2, turns 14–23),
`fallbackTurns [10,10,0,0]`. Its decoded `game` log carries 20 matching lines, all
`falling back to phalanx (parse_error)`, and — decisively — **no** `attempt N failed` line and
`latency_ms: 0` on every one of those directives, while the sidecar logged 50 invocations, all
`200 OK` against `bedrock-runtime.us-east-1.amazonaws.com`, and `budgetGuards` is 0. So no model
call was ever made on those turns. In `src/kaz/decide.nim` the rate floor sleeps
`turnSpacingMs - since` **after** `turnStart` is taken; the loop's first act is
`if getMonoTime() - turnStart >= budget`, which with `turnSpacingMs 9000 > turnBudgetMs 7000`
fires whenever `since ≲ 2000 ms`. That path writes a `timeout` fallback record with **no** echo
and then the tail block writes a second record and echoes `(parse_error)` — hence 2 records and
1 log line per seat per turn, and hence the misleading `parse_error` label. It self-latches:
`engine.lastBatchStart` is refreshed even on a turn that made no call, so the next turn starts
`since ≈ 0` and fails identically. Round 3 escaped it only because its calls were slower.
Suggested owner: phase 30 / the fixer — either `turnSpacingMs < turnBudgetMs`, or take
`turnStart` after the rate-floor sleep, or exclude the sleep from the budget.

**O2 — the viewer's hero plates say `player-0 … player-3`.** The replay carries the real join
names (`daveey`, `daveey-1`, `Baseline`, `Baseline (2)`) and the aliases (`KNIGHT-alpha` …) —
`tools/replay_summary.py` reads both out of the same bytes — but the static wasm bundle labels the
four plates positionally. A spectator cannot tell the two champions apart. Legibility finding for
phase 30 item 14.

**O3 — `feed_lines: 0`.** The commander-line feed (`design.md` §Derived broadcast events) drew
nothing in the rendered frame. The scorebug, clock and momentum graph all populated, so this is a
feed-specific gap, not a dead viewer.

**O4 — the scrubber seeks by playing forward, not by jumping.** At the 100 % scrub the clock read
`WAVE 1/2 · TURN 14/24` rather than the end of wave 2, and the screenshot was taken at tick
`1591 / 3396` — i.e. the wasm was still marching toward the seeked tick when the DOM was read.
Motion is proven (the three readouts advance), but a spectator dragging to the end will wait.

**O5 — `replay_summary.py` reports `tickCount` as the file size.** For round 1 it printed
`"tickCount": 110027` while the file was 110027 bytes and `results.finalTick` was 3799; for
round 3, `finalTick` 2063. Cosmetic, in a forensics tool only — but the field is wrong.

**O6 — GitHub Actions runner capacity, fleet-visible.** The second `viewer-check.yml` dispatch
(run 32984003113, 15:04:44Z) sat `queued` for 38+ minutes and never started, as did
`propagate-secrets` 32984047591. Not this coworld's problem; worth knowing when a later phase
budgets for a CI dispatch.
