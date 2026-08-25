# VERIFY — paintball, coworld version **0.1.3** (fetched 2026-08-25 17:02Z–17:09Z)

Verdict: **6 of 8 TRUE — checks 4 and 5 FALSE.**

This file is a complete re-verify. Every response below was fetched in this session
(2026-08-25 17:02Z–17:09Z); none of the 13:45Z evidence against 0.1.2 is reused. The two
documented exceptions are check 7 (the committed `release-result.json`, phase 40's artifact copy)
and check 8's rendered evidence (the `viewer-check.yml` run **32875824479**, dispatched at
17:05:25Z **this session** and committed under `runs/2026-08-25-paintball/viewer-check/`).

Ids under test:
- coworld `cow_09dcacad-01fb-488b-9d93-5eddf6a1a37a` v0.1.3,
  manifest `sha256:669e79cde247aa82428d6a26c7cfeb652b3cf89f492df9ee697ca3225a123f71`
- league `league_bd940066-00c4-4ade-87ae-06dac0818bc4`, division `div_97b4e1b9-6f9b-44ab-8583-73789a4ee057`
- champions `daveey → paintball-holdcentre:v2`, `daveey-1 → paintball-splitpaint:v2`
- fillers `paintball-holdline:v1`, `paintball-sprayer:v1`

Auth on every Observatory call: headers `Authorization: Bearer $SOFTMAX_TOKEN` and
`User-Agent: coworld-builder/1.0`; artifact reads additionally send
`X-Use-Elevated-Privileges: true`. Header **values are never printed**.
`BASE=https://softmax.com/api/observatory/v2`.

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | **TRUE** — 16 completed of 18 (8 of them with the v2/0.1.3 champions) |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey-1 rank 2, daveey rank 3, 16 rounds each; fillers absent |
| 3 | Latest round's episode completed with a replay + right participants | **TRUE** — round 18 `ereq_705b8fb6`, daveey vs daveey-1, replay present |
| 4 | Replay bytes valid, protocol matches, champions really playing | **FALSE** — latest round: 56 of 76 champion directives are fallbacks (llmTurns [9,11] / fallbackTurns [29,27]). One round earlier (round 17, also fetched this session) the same check is TRUE at 66/76 `llm` |
| 5 | Hosted game log clean | **FALSE** — 112 `falling back` lines in the latest round's episode (22 in round 17). Cause is the platform-wide Bedrock **daily-token 429**, cross-checked live against collab_cooking; that exception does not make the grep clean |
| 6 | Public page featured match on the **static** replay path | **TRUE** — `.../v2/coworlds/replays/static/cow_09dcacad…/sha256%3A669e79cd…/index.html?replay=…`, `ready: true` |
| 7 | Certification declared the static bundle | **TRUE** — `Replay liveness: skipped (static replay bundle declared…` |
| 8 | Viewer actually renders and advances | **TRUE** — `loaded: true`, three **differing** clock readouts, screenshot shows the game |

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

Fillers were registered at **12:48:11Z** (`log.md` line 47), before round 1 was triggered.

```
GET $BASE/rounds?league_id=league_bd940066-00c4-4ade-87ae-06dac0818bc4&limit=30
  headers: Authorization, User-Agent          (fetched 17:02:18Z; re-polled 17:07:35Z)
```

`jq -r '… | [.round_number,.id,.status,.created_at,.completed_at]|@tsv'`:

```
1	round_f869a120-6fdf-4fdf-bb35-f1aa5cb9f3ae	completed	2026-08-25T12:47:00.788297Z	2026-08-25T12:53:15.488017Z
2	round_e362afc6-1048-426e-956c-7d37cf07cb3d	completed	2026-08-25T13:02:01.127562Z	2026-08-25T13:07:11.075093Z
3	round_b589408b-350d-47ce-96f3-4a5335844166	completed	2026-08-25T13:17:01.513720Z	2026-08-25T13:25:10.853455Z
4	round_b10985a5-c9b2-4c75-a6d0-214cadf67bf6	completed	2026-08-25T13:32:02.017005Z	2026-08-25T13:38:20.581820Z
5	round_729664ce-d6f9-425c-bd2c-ad8c737e9e71	completed	2026-08-25T13:47:02.882839Z	2026-08-25T13:50:57.383750Z
6	round_3bc9e0ad-d58c-4795-9fc2-9348149b8aac	completed	2026-08-25T14:02:03.726302Z	2026-08-25T14:09:14.316940Z
7	round_8f4e3787-9855-4d01-95f9-f9365d063634	completed	2026-08-25T14:17:04.116481Z	2026-08-25T14:23:18.615969Z
8	round_c6d968b9-5c47-408b-90bc-d6e945137bcb	completed	2026-08-25T14:32:04.719259Z	2026-08-25T14:38:23.562130Z
9	round_ce1293f9-836c-44a5-a28f-b7e781466536	completed	2026-08-25T14:47:05.088758Z	2026-08-25T14:51:22.160735Z
10	round_f8b31f1a-998f-4d7d-92c5-b91e8821c852	completed	2026-08-25T15:02:06.022821Z	2026-08-25T15:06:42.424086Z
11	round_c1267288-106d-4322-81c4-5100c1fd43ab	failed	2026-08-25T15:17:06.391936Z	2026-08-25T15:25:04.497536Z
12	round_0673680d-5e42-4548-b218-f4f30ef42228	completed	2026-08-25T15:32:07.313203Z	2026-08-25T15:36:44.978347Z
13	round_d392bf0d-89d3-489f-b56c-6156cf3ea0a8	completed	2026-08-25T15:47:07.899698Z	2026-08-25T15:52:25.150680Z
14	round_2ac2b015-fedc-45fc-844e-a478aef7c7d2	completed	2026-08-25T16:02:08.319131Z	2026-08-25T16:06:18.951200Z
15	round_a297b9d9-be6a-4aab-b372-d81d422576c9	completed	2026-08-25T16:17:08.717323Z	2026-08-25T16:23:11.135440Z
16	round_c86242f5-1cab-47db-8d04-4c5dabfec952	completed	2026-08-25T16:32:10.142350Z	2026-08-25T16:36:44.330804Z
17	round_df0cb96e-c8d9-457d-8f03-cacb2071cc52	completed	2026-08-25T16:47:10.511574Z	2026-08-25T16:52:15.257563Z
18	round_6effd321-1b70-45f0-a390-acaf7a2e01ef	completed	2026-08-25T17:02:49.788948Z	2026-08-25T17:07:26.336477Z
```

Round 11 is the one non-completed round; its `error`, verbatim:

```
only 4/6 planned slots produced scoring evidence; the round requires at most 0% of planned slots failed
```

Failed rounds do not count. **16 rounds completed**, every one of them created after 12:48:11Z
except round 1 (created 12:47:00.788Z, completed 12:53:15Z — excluded from the count to be safe;
15 completed rounds remain).

Which rounds ran the **0.1.3** champions (`policy_version_id f07e43ed-…` = `paintball-holdcentre:v2`
in `round_config.entrant_attributions`):

```
1..9   pre-v2
10     champ-v2  completed
11     champ-v2  failed
12..18 champ-v2  completed
```

→ **8 completed rounds with the 0.1.3 champions** (10, 12, 13, 14, 15, 16, 17, 18).

Status: **TRUE** — 16 completed rounds (8 on 0.1.3), all after fillers were set at 12:48:11Z.

---

## 2. Both champions ranked; fillers absent or Baseline — TRUE

```
GET $BASE/divisions/div_97b4e1b9-6f9b-44ab-8583-73789a4ee057/leaderboard
  headers: Authorization, User-Agent          (fetched 17:02:18Z)
```

Bare list. `jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'`:

```
1	richard	co-gas-paintball-holdline-richard:v1	1222.925405673113	11	29.0
2	daveey-1	paintball-splitpaint:v2	1017.7749847877911	16	19.0
3	daveey	paintball-holdcentre:v2	941.9621325803336	16	16.0
4	relh	co-gas-paintball-holdline-relhalpha:v2	817.3374769587625	11	6.0
```

Both champions present at **v2** (the 0.1.3 build) with `rounds_played = 16`. `richard` and `relh`
are external players who joined the open ladder with their own policies — expected, not fillers.

Fillers are absent from the leaderboard. They are still registered as filler policies (read
requires the elevated header even though it is a read):

```
GET $BASE/leagues/league_bd940066-.../filler-policies
  headers: Authorization, User-Agent, X-Use-Elevated-Privileges   → HTTP 200 (fetched 17:08:56Z)
```
```json
{"filler_policy_versions": [
  {"policy_version_id": "b39fb2e0-2feb-4c33-b764-4d7b82a0788b", "policy_name": "paintball-holdline",
   "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"},
  {"policy_version_id": "f24ea073-f96e-4022-940b-1d7a8a52f7f9", "policy_name": "paintball-sprayer",
   "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"}]}
```

Both filler version ids differ from the champions' (`f07e43ed-…`, `83ba1515-…`).

Status: **TRUE** — daveey and daveey-1 both ranked with 16 rounds played; fillers registered,
distinct from the champions, and absent from the leaderboard.

---

## 3. Latest round's episode request completed with a replay — TRUE

The latest **completed** round at the time of writing is **round 18**
(`round_6effd321-1b70-45f0-a390-acaf7a2e01ef`, completed 17:07:26Z). Round 17 was the latest when
this session started; both are recorded here, and checks 4 and 5 below carry both.

```
GET $BASE/episode-requests?round_id=round_6effd321-1b70-45f0-a390-acaf7a2e01ef&limit=20
  headers: Authorization, User-Agent          (fetched 17:07:40Z)
```
```
ereq_f4a544eb-1323-44f9-93ad-b5a2b3d12c0f	completed	daveey-1 vs richard
ereq_8cc527fd-b103-4fdb-9bcd-07265a8b321c	completed	daveey vs richard
ereq_705b8fb6-9973-47d6-bd43-9037dddcd723	completed	daveey vs daveey-1
ereq_cb5852a4-cdce-4a23-b66e-686f626ba221	completed	relh vs richard
ereq_cf65be9a-d275-4a40-ae5f-373b44998b75	completed	relh vs daveey-1
ereq_c5eb333d-e8a9-44f2-9f54-06edb1e24636	completed	relh vs daveey
```

The round now contains **six** episode requests because two external players joined the ladder.
**I selected `ereq_705b8fb6-9973-47d6-bd43-9037dddcd723`** — the champion-vs-champion episode —
because it is the only one of the six whose participants are the two champions this run owns
(`daveey` and `daveey-1`), which is what checks 3 and 4 are about; the other five seat an external
player's policy on one side.

```
GET $BASE/episode-requests/ereq_705b8fb6-9973-47d6-bd43-9037dddcd723
  headers: Authorization, User-Agent          (fetched 17:07:44Z)
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/3365b4ec-7fd6-4e06-aa04-3d951513baac.replay",
  "participants": [
    {"position": 0, "policy_name": "paintball-holdcentre", "version": 2,
     "player_name": "daveey", "is_filler": false},
    {"position": 1, "policy_name": "paintball-splitpaint", "version": 2,
     "player_name": "daveey-1", "is_filler": false}
  ],
  "participant_scores": [{"position": 0, "score": 0.569}, {"position": 1, "score": 0.431}]
}
```

For completeness, the same call against round 17's champion-vs-champion episode
(fetched 17:02:54Z):

```json
{"status": "completed",
 "replay_url": "https://softmax-public.s3.amazonaws.com/replays/f98e5584-08fe-424c-8e13-3258c2d23e3b.replay",
 "participants": ["paintball-holdcentre v2 / daveey", "paintball-splitpaint v2 / daveey-1"],
 "participant_scores": [{"position": 0, "score": 0.392}, {"position": 1, "score": 0.608}]}
```
(id `ereq_2bae9f12-8015-4d7f-95f2-373c655a7f6a`; the participants block is the same shape as above,
both champions at version 2, `is_filler: false`.)

Status: **TRUE** — latest round's champion-vs-champion episode is `completed`, has a non-null
`replay_url`, and its participants are exactly `daveey` (holdcentre:v2) and `daveey-1`
(splitpaint:v2).

---

## 4. Replay bytes valid and showing the game — FALSE (latest round); TRUE one round earlier

The paintball replay is **binary** (`COWLDPNT` magic), so `jq` on the raw bytes fails by design.
The design note (§Replay bytes, "The phase-60 substitute for SPEC §Definition of done check 4")
prescribes `tools/replay_summary.py`, which emits one strict-UTF-8 JSON object. The repo was
cloned fresh this session at `main` = `2a58c99`.

### 4a. Latest round (round 18, `ereq_705b8fb6`) — the episode check 3 selected

```
curl -sSL https://softmax-public.s3.amazonaws.com/replays/3365b4ec-7fd6-4e06-aa04-3d951513baac.replay -o ep18.replay
→ HTTP 200 bytes 145981                                          (fetched 17:07:52Z)
python3 tools/replay_summary.py ep18.replay > ep18.json
jq -e . ep18.json  → strict UTF-8 JSON: ok
```

`jq -r '.protocol'` → `paintball/v1` (matches the manifest's declared protocol).

`jq -r '.results'` — and note these bytes come from the replay's own `result` control record
(fix `d8f05e0`), **not** from the artifacts endpoint:

```json
{"names":["daveey","daveey-1"],"scores":[0.569,0.431],"win":[true,false],"team":["red","blue"],
 "residentScore":[0.458,0.542],"visitorScore":[0.68,0.32],"hillTicks":[295,96],
 "residentHillTicks":[35,96],"visitorHillTicks":[260,0],"paintTiles":[135,121],
 "tagsDealt":[22,13],"tagsTaken":[16,19],"llmTurns":[9,11],"fallbackTurns":[29,27],
 "reason":"complete","endRule":"mercy","games":2,"finalTick":4640,"seed":1947007857}
```

`results.reason == "complete"` with `endRule == "mercy"` — legal and normal per design.md
§"End conditions and legal `results.reason` values" (`complete`/`mercy` = the final game's hill lead
exceeded the ticks remaining).

**The `result` record does now come from the replay bytes.** `tools/replay_summary.py` reads only
the file it is given (`elif kind == "result": results = obj.get("results", obj)` — it makes no
network call), so the results object above was decoded out of the S3 bytes. For round 17 the same
record is byte-identical to the separately fetched hosted `artifacts/results` (§4b). This closes
the 0.1.2 gap, where `results` had to be read from the platform.

Both seats registered as LLM policies — the `register` control records in the same bytes:

```json
[{"k":"register","seat":1,"team":"blue","policy":"splitpaint","kind":"llm","baseline":"holdline"},
 {"k":"register","seat":0,"team":"red","policy":"holdcentre","kind":"llm","baseline":"holdline"}]
```

Directive sources, per seat (`jq '[.directives[]|{seat,source}] | group_by(.seat) | …'`):

```json
[{"seat": 0, "llm": 9,  "fallback": 29, "scripted": 0},
 {"seat": 1, "llm": 11, "fallback": 27, "scripted": 0}]
```
`jq -r '.fallbacks'` → `112` (fallback *attempt* records; 56 turns ended in a fallback directive).

**No `scripted` directive on either champion seat** — the 0.1.3 registration fix (`d3ee912`) holds,
and the `register` records above show both seats as `kind: "llm"`. But **fallbacks are the
majority, not a small minority**: 56 of 76 directives (74 %) are the `holdline` fallback, and the
results document agrees (`llmTurns [9,11]`, `fallbackTurns [29,27]`). Sample of the LLM directives
that did land (real, non-trivial content):

```
game 1 turn 1 seat 0 llm 2775ms  "T1: RED owns nothing yet (33% vs need 80%). Delta closest to hill, beta next. Position hold_hill/paint_hill on hill, guard left flank, paint lane back."
game 1 turn 1 seat 1 llm 2775ms  "Two on RED-alpha (nearest enemy, recent). Hold hill. Paint path to enemy half."
game 2 turn 17 seat 0 llm 2260ms "Own 80%, hold it. Alpha closest to centre - hold_hill. Beta next closest - paint_hill north edge. Gamma guards west flank. Delta paint_path reinforce lane."
game 2 turn 17 seat 1 llm 2260ms "Only alpha alive in my control. Red owns hill 80%. Hunt nearest recent enemy (RED-alpha at 557,295) to tag it out, deny their paint, swing the clock."
```

Status: **FALSE** for the latest round — the bytes are valid, the protocol matches, the reason is
legal, and nothing is scripted on a champion seat, but the fallback count (56/76, 74 %) is a
**majority** of the decisions, which check 4 explicitly forbids. Cause is the platform Bedrock
daily-token 429 documented in check 5, not a coworld defect — but check 4 allows no such exception
(its only documented exception is a `deadline` reason).

### 4b. One round earlier (round 17, `ereq_2bae9f12`) — same check, also fetched this session

```
curl -sSL https://softmax-public.s3.amazonaws.com/replays/f98e5584-08fe-424c-8e13-3258c2d23e3b.replay -o ep.replay
→ HTTP 200 bytes 143513                                          (fetched 17:03Z)
python3 tools/replay_summary.py ep.replay | jq -e .  → strict UTF-8 JSON: ok
```
```json
{"protocol": "paintball/v1", "gameVersion": "1"}
{"names":["daveey","daveey-1"],"scores":[0.392,0.608],"win":[false,true],"team":["red","blue"],
 "residentScore":[0.473,0.527],"visitorScore":[0.31,0.69],"hillTicks":[0,313],
 "residentHillTicks":[0,39],"visitorHillTicks":[0,274],"paintTiles":[148,131],
 "tagsDealt":[18,27],"tagsTaken":[26,19],"llmTurns":[33,33],"fallbackTurns":[5,5],
 "reason":"complete","endRule":"mercy","games":2,"finalTick":4722,"seed":493838918}
```
```json
[{"seat": 0, "llm": 33, "fallback": 5, "scripted": 0},
 {"seat": 1, "llm": 33, "fallback": 5, "scripted": 0}]
```

Cross-check against the hosted results artifact
(`GET $BASE/episode-requests/ereq_2bae9f12…/artifacts/results`, elevated header, fetched 17:03:35Z)
— **byte-identical** to the `result` record inside the replay, including `llmTurns [33,33]` /
`fallbackTurns [5,5]`.

Sample directives (round 17):

```
game 1 turn 0  seat 0 llm 5141ms  "T0: All cogs moving to hill. Alpha/Beta closest, heading to hold/paint. Gamma/Delta following to guard/paint_path positions."   intents hold_hill,paint_hill,guard,paint_path
game 1 turn 0  seat 1 llm 5141ms  "Turn 0: Enemy cogs spotted near their spawn. Deploy hunt pair (alpha+beta) on RED-alpha, hold_hill with gamma, paint_path with delta toward enemy half to build …"   intents hunt,hunt,hold_hill,paint_path
game 1 turn 17 seat 0 llm 2308ms  "BLUE owns 61% hill. RED-alpha dead. Push RED-gamma (closest alive, 64px) and RED-beta (paint path support) at hill; RED-delta hunts BLUE-alpha/gamma (0 ticks, 1…"   intents paint_hill,paint_hill,hold_hill,hunt
game 2 turn 14 seat 0 llm 1836ms  "RED-alpha at hill edge, 78px away. BLUE closing from NE. Hold center, paint toward their approach."   intents hold_hill
```

Round-17 status: **TRUE** — 66 of 76 directives `llm` (fallbacks 13 % per seat), zero scripted on a
champion seat, protocol matches, `complete`/`mercy`.

**Check 4 overall verdict: FALSE**, because the check is defined on the *latest* round and the
latest round's champion episode is fallback-majority. The 0.1.3 code path itself is demonstrably
working — round 17, 20 minutes earlier, is a clean pass on the identical build — so this is a
throughput/quota problem, not a code problem.

---

## 5. Hosted game log clean — FALSE (platform-wide Bedrock daily-token 429, cross-checked)

The logs body is python `b'…'` reprs under `===== container: … =====` headers; every repr was
`ast.literal_eval`-decoded before grepping (a line-based grep on the raw body undercounts badly).

### 5a. Latest round (round 18, `ereq_705b8fb6`)

```
GET $BASE/episode-requests/ereq_705b8fb6-9973-47d6-bd43-9037dddcd723/artifacts/logs
  headers: Authorization, User-Agent, X-Use-Elevated-Privileges
→ HTTP 200 bytes 159799                                          (fetched 17:08:11Z)
grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' <decoded>
```
```
falling back                  112
LLM provider is unavailable     0
cut off at max_tokens           0
rejected                        0
Too many tokens per day       110
fallback causes:  Counter({'throttled': 56})
attempt-failure reasons:  55 × 'llm throttled (429): {"message":"Too many tokens per day, pl…'
                           1 × 'reply named no commanded cog'
```

Verbatim lines (decoded):

```
[game] paintball llm: seat 0 attempt 1 failed, falling back if it fails again: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
[game] paintball llm: seat 0 falling back to holdline (throttled) on turn 0
[game] paintball llm: seat 1 attempt 1 failed, falling back if it fails again: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
[game] paintball llm: seat 1 falling back to holdline (throttled) on turn 16
```

The sidecar's own record of the same call:

```json
{"timestamp": "2026-08-25T17:03:05.605437Z",
 "episode_request_id": "705b8fb6-9973-47d6-bd43-9037dddcd723",
 "model": "global.anthropic.claude-haiku-4-5-20251001-v1:0", "operation": "InvokeModel",
 "ok": false, "status_code": 429, "error_type": "ThrottlingException",
 "message": "Too many tokens per day, please wait before trying again."}
```

### 5b. Round 17 (`ereq_2bae9f12`), fetched 17:03:36Z, HTTP 200, 173684 bytes

```
falling back                   22
LLM provider is unavailable     0
cut off at max_tokens           0
rejected                        0
Too many tokens per day        18
fallback causes:  9 × throttled, 1 × parse_error
```
```
[game] paintball llm: seat 0 attempt 1 failed, falling back if it fails again: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
[game] paintball llm: seat 0 falling back to holdline (throttled) on turn 3
[game] paintball llm: seat 0 attempt 1 failed, falling back if it fails again: anthropic error 503: {"message":"Bedrock is unable to process your request."}
[game] paintball llm: seat 1 attempt 1 failed, falling back if it fails again: reply named no commanded cog
[game] paintball llm: seat 1 falling back to holdline (parse_error) on turn 9
```

### 5c. Cross-check against another LLM coworld (this session)

`collab_cooking` (`cow_19938c0f-195a-45f8-95da-761f0ffe04cb`), its **latest** episode
`ereq_91f90ab1-d25b-4949-b0ee-e28c926ec490` (created 16:57:46Z, completed 17:02:08Z — i.e. running
at the same minutes as paintball's round 18), logs fetched 17:04Z with the elevated header:

```
Too many tokens per day: 106     ThrottlingException: 53     429: 165
```
```json
{"timestamp": "2026-08-25T16:58:40.664639Z",
 "episode_request_id": "91f90ab1-d25b-4949-b0ee-e28c926ec490",
 "model": "global.anthropic.claude-haiku-4-5-20251001-v1:0", "operation": "InvokeModel",
 "ok": false, "status_code": 429, "error_kind": "upstream_client",
 "error_type": "ThrottlingException",
 "message": "Too many tokens per day, please wait before trying again.", "latency_ms": 58.46}
```

The previous episode `ereq_bcad4f07-cd00-4079-8540-553fd72e5f3c` (16:42–16:47Z) shows the same
thing at lower volume: 18 × `Too many tokens per day`, 9 × `ThrottlingException`.
(`collab_cooking` shows 0 `falling back` lines only because its game code does not print that
phrase; the 429s are in the shared `bedrock-sidecar` container, same model string, same message.)

**Conclusion.** The Bedrock **daily-token quota** is exhausted platform-wide right now — it has
*not* recovered; it got worse between 16:47Z (round 17: 9 throttled fallbacks) and 17:02Z
(round 18: 56). Paintball's own amplifiers from the 0.1.2 verify are gone: the sonnet-4-5 timeout
cascade is absent (haiku-only candidate list, fix `f317951`), the deadlines are whole seconds
(`6a2df41`), and no seat played scripted (`d3ee912`). Of round 17's 22 matching lines, 19 trace to
Bedrock 429/503 and 3 to one coworld-side `parse_error` ("reply named no commanded cog", handled by
the design's tolerant-parse → fallback path). Round 18's 112 lines break down as 55 throttled
attempt-1 lines + 56 `(throttled)` fallback lines + **1** `reply named no commanded cog` attempt
line that recovered on attempt 2 — i.e. **111 of 112 are the platform throttle**, and every one of
the 56 fallbacks is `throttled`.

Status: **FALSE** — the grep is not CLEAN (112 lines latest round, 22 one round earlier). SPEC's
documented-platform-cause clause covers the throttle lines and the cross-check above is the
citation, but the check as written requires zero lines and I will not mark it true. This is
adjudication for the coordinator/judge: the coworld-side contribution is one parse_error fallback
in round 17 and nothing at all in round 18.

---

## 6. The public page uses the static replay path — TRUE

```
curl -sS https://softmax.com/paintball            → HTTP 200, 581461 bytes   (fetched 17:05:04Z)
grep -o '<iframe[^>]*src="[^"]*"'                 → no match
```

The iframe is client-rendered, so per `prompts/60-verify.md` check 6 and
`playbooks/observatory-api.md` §Featured match I used the **second source**: the page's own SSR
payload (`state.playlist[0]`) plus the session call the page's JS makes. Both are recorded here.

SSR payload, `state.playlist[0]` (unescaped from the page bytes):

```json
{"episodeId":"425897bc-a081-47b0-b0f1-525c69e6ddf1",
 "coworldId":"cow_09dcacad-01fb-488b-9d93-5eddf6a1a37a",
 "coworldName":"paintball","coworldVersion":"0.1.3",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/b1b22848-79d4-4118-a5e8-341cd0ec42f8.replay",
 "finishedAt":"2026-08-25T16:52:10.208204Z","roundNumber":17,"episodeNumber":6,
 "code":"paintball.r17.e6",
 "matchup":{"divisionId":"div_97b4e1b9-6f9b-44ab-8583-73789a4ee057","divisionName":"Competition",
   "first":{"rank":1,"player_name":"richard","score":1222.925405673113,
            "policy_label":"co-gas-paintball-holdline-richard:v1"},
   "second":{"rank":2,"player_name":"daveey-1","score":1017.7749847877911,
             "policy_label":"paintball-splitpaint:v2"}},
 "inspectUrl":"…detail=episode-request:ereq_3200f97b-da90-4fe8-b265-c97e9efc1af2","outcome":"first"}
```

A featured match **is** present, and it is a **0.1.3** episode: `coworldId` is the new
`cow_09dcacad-…`, `coworldVersion` is `0.1.3`. It does **not** lag on the old `cow_4ac3644c…`
v0.1.2.

```
POST $BASE/coworlds/replays/session
  headers: Authorization, User-Agent, content-type
  body: {"coworld_id":"cow_09dcacad-01fb-488b-9d93-5eddf6a1a37a",
         "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/b1b22848-79d4-4118-a5e8-341cd0ec42f8.replay"}
→ HTTP 200                                                        (fetched 17:05:20Z)
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_09dcacad-01fb-488b-9d93-5eddf6a1a37a/sha256%3A669e79cde247aa82428d6a26c7cfeb652b3cf89f492df9ee697ca3225a123f71/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fb1b22848-79d4-4118-a5e8-341cd0ec42f8.replay&v=2",
  "ready": true
}
```

Path check, field by field: `/v2/coworlds/replays/**static**/` ✓ ·
`cow_09dcacad-01fb-488b-9d93-5eddf6a1a37a` = STATE's 0.1.3 cow id ✓ ·
`sha256%3A669e79cde247aa82428d6a26c7cfeb652b3cf89f492df9ee697ca3225a123f71` = the 0.1.3 manifest
sha ✓ · ends `/index.html?replay=<s3 url>` ✓ · **no `/client/replay` anywhere** ✓ ·
`ready: true` ✓.

Status: **TRUE** — source used: the SSR payload `state.playlist[0]` (the raw-HTML iframe grep found
nothing) plus `POST /coworlds/replays/session`. Featured match `paintball.r17.e6` on coworld 0.1.3,
served from the static bundle.

---

## 7. Certification declared the static bundle — TRUE

Source read: the **committed** `runs/2026-08-25-paintball/release-result.json` (phase 40's artifact
copy, committed in `92e02c5` "paintball: 0.1.3 released after the phase-60 fix round",
2026-08-25 14:46:40Z). It was present; no re-download was needed.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-25-paintball/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Same file, the identifying fields:

```json
{"version": "0.1.3", "ok": true,
 "cow_id": "cow_09dcacad-01fb-488b-9d93-5eddf6a1a37a",
 "manifest_sha": "sha256:669e79cde247aa82428d6a26c7cfeb652b3cf89f492df9ee697ca3225a123f71",
 "step_failed": null, "certify_ok": true}
```

`certify.output_tail` shows all ten transcript steps passed, including
`[pass] replay-loadable: the replay artifact has a declared viewer path` and
`[pass] players-run`, ending `Certified dist/coworld_manifest.json`.

Status: **TRUE** — the required string is present, and the artifact is the one for the coworld
id/manifest sha under test.

---

## 8. The viewer was EXECUTED, and it renders and advances — TRUE

Dispatched this session against the **exact** `viewer_url` from check 6:

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_09dcacad-01fb-488b-9d93-5eddf6a1a37a/sha256%3A669e79cde247aa82428d6a26c7cfeb652b3cf89f492df9ee697ca3225a123f71/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fb1b22848-79d4-4118-a5e8-341cd0ec42f8.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=120
# dispatched 17:05:25Z
```

That the job opened exactly this URL is confirmed by `viewer-smoke.json`'s own `url` field:

```json
"url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_09dcacad-01fb-488b-9d93-5eddf6a1a37a/sha256%3A669e79cde247aa82428d6a26c7cfeb652b3cf89f492df9ee697ca3225a123f71/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fb1b22848-79d4-4118-a5e8-341cd0ec42f8.replay&v=2"
```

Run selection — by creation time newer than the dispatch, never `-L 1` blind:

```
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10
32875824479	2026-08-25T17:05:27Z	in_progress	workflow_dispatch     ← newer than the 17:05:25Z dispatch
32868690580	2026-08-25T15:54:30Z	completed	workflow_dispatch
32854934931	2026-08-25T13:42:15Z	completed	workflow_dispatch
```
```
gh run view 32875824479 → {"conclusion":"success","createdAt":"2026-08-25T17:05:27Z","status":"completed"}
gh run download 32875824479 -R Metta-AI/coworld-builder -n viewer-check \
   -D runs/2026-08-25-paintball/viewer-check     (committed with this file)
```

`jq -c '{loaded, ms, clock, scorebug, feed_lines}' viewer-smoke.json` — verbatim:

```json
{"loaded":true,"ms":4450,"clock":"1:30 TIME LEFT GAME 1/2 · RESIDENT · TURN 1/20","scorebug":"0% RED HILL 0:00 0 TAGS · 4 UP 1:30 TIME LEFT GAME 1/2 · RESIDENT · TURN 1/20 0% BLUE HILL 0:00 0 TAGS · 4 UP","feed_lines":0}
```

`jq -c '.signals'`:

```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

`jq -r '.failure // "no failure"'` → `no failure`.
`jq -c '.canvas_text'` → `{"total":0,"outside":0,"ellipsized":0,"never_inside":0,…}` (the board is a
wasm canvas; the chrome text is DOM, so nothing is drawn through the instrumented text API).

The three scrub readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | clock readout |
|---|---|
| 0 % | `1:30 TIME LEFT GAME 1/2 · RESIDENT · TURN 1/20` |
| 50 % | `1:15 TIME LEFT GAME 1/2 · RESIDENT · TURN 4/20` |
| 100 % | `0:55 TIME LEFT GAME 1/2 · RESIDENT · TURN 8/20` |

All **three differ**, and they advance monotonically (turn 1 → 4 → 8; the screenshot taken after
the last readout shows tick counter `847 / 4614`). `loaded: true` came from
`data-replay-loaded="true"` on `<html>`, which the shell sets only after the Worker's first frame
reached BroadcastCore. First frame at **4450 ms**.

Status: **TRUE** — `loaded: true` **and** three differing clock readouts.

Two observations for the coordinator (neither affects the verdict):

1. **The seek lags its target.** `viewer_smoke.mjs` clicks `#scrub` and reads 700 ms later
   (`templates/tools/ci/viewer_smoke.mjs`, the scrub block). The 50 % click landed at tick ~360 of
   4614 and the 100 % click at tick 847 — i.e. the 0.1.3 bounded `SeekTicksPerFrame` convergence
   (fix `6ffead7`) is still converging when the sample is taken. Motion is proven, but a spectator
   dragging to the end of a 4614-tick episode waits several seconds for the picture to arrive
   rather than jumping. Worth a look in a later legibility pass; it is a large improvement on
   0.1.2, where two of the three readouts were identical.
2. **`feed_lines: 0` is a selector mismatch, not an empty feed.** The smoke script counts children
   of `#feed, .feed, #log`; paintball's chrome (inherited from coworld-ctf) renders the match feed
   into `#killfeed` and the command lines into `#bannerlane`. The screenshot below shows four
   populated feed rows, so the readout is a false zero.

### Spectator judgment

**`viewer-smoke.png` (896 KB, committed) shows a real, legible paintball match, and it is the
starter's chrome.** Top strip: the scorebug — a red `76%` coverage chip, `0:00 HILL RED`,
`12 TAGS · 4 UP` with four red life pips on the left; the centre clock column `0:55 / TIME LEFT /
GAME 1/2 · RESIDENT · TURN 8/20`; and the mirrored blue plate on the right (`BLUE HILL 0:00`,
`9 TAGS · 4 UP`, `23%`). The regime is on screen exactly as the design demands. The board fills the
frame: the hand-tuned arena with its spinning diamonds, glass stubs and the two team spawn discs,
and — the thing the game is about — **the floor is visibly two-thirds painted**, a large red
territory across the west and centre-left and a blue one across the east, with a contested seam
running through the middle where a white spray cone is firing. Eight cogs are drawn as real
sprites with intent shout bubbles above them (`HILL`, `PAINT`, `HUNT`, `TAGT`, `watch`, `paint`,
`fold`), several lying tagged out. Under the board the feed carries the commander lines in plain
language: `RED command: ALPHA DEAD. DELTA ON ENEMY PAINT→PROMOTE TO PAINT_HILL. BETA+GAMMA HUNT
BLUE-ALPHA (NEAREST, CLOSEST TO HILL). HOLD HILL WITH FALLBACK COG.` and
`…GAMMA CLOSEST TO HILL (285 VS 471). ALPHA DEAD, GAMMA DEAD (0HP). BETA NEAR HILL ON OWN PAINT -
KEEP IT THERE AS ANCHOR. DELTA PROMOTE TO PAINT_HILL TARGET`, against `BLUE command: HOLD THE HILL`
twice. Below that the full transport strip — restart, step-back, play, `+5s`, step, loop, fast-
forward, a `spoilers` toggle, the tick readout `847 / 4614` and the speed ladder `1× 2× 3× 4× 8×
16×` — and beneath it the scrubber with the momentum graph.

**Reconciled against the record.** The rendered replay is the featured match
`b1b22848-…` (= `paintball.r17.e6`, `ereq_3200f97b`), fetched and summarised this session:
`protocol paintball/v1`, register records `seat 0 = splitpaint (kind llm, red)` and
`seat 1 = holdline (kind scripted, blue)` — daveey-1's champion against external player richard's
scripted baseline. Its directive stream at exactly the rendered moment matches the two feed lines
**verbatim**:

```
game 1 turn 6 seat 0 llm 2129ms  "Alpha dead. Delta on enemy paint→promote to paint_hill. Beta+Gamma hunt BLUE-alpha (nearest, closest to hill). Hold hill with fallback cog."
game 1 turn 7 seat 0 llm 2715ms  "BLUE-gamma closest to hill (285 vs 471). Alpha dead, Gamma dead (0hp). Beta near hill on own paint - keep it there as anchor. Delta promote to paint_hill target"
game 1 turn 7 seat 1 scripted    "hold the hill"
```

and the cog bubbles match the same turn's per-cog `say` fields:
`RED-alpha:hunt/HUNT  RED-beta:hold_hill/HOLD  RED-gamma:hunt/HUNT  RED-delta:paint_hill/PAINT`
against `BLUE-alpha:hunt/"on it"  BLUE-beta:guard/"watch"  BLUE-gamma:paint_hill/"paint"
BLUE-delta:paint_hill/"paint"`. Early/late ends of the same stream (`game 1 turn 0` seat 0
`fallback "hold the hill"`; `game 2 turn 19` seat 0 llm *"5 sec left, hill 57% ours. Alpha on enemy
paint—promote to paint_hill now to flip it back…"*) and the episode's own result record
(`hillTicks [23,212]`, `paintTiles [119,129]`, `tagsDealt [13,20]`, `reason complete`,
`endRule mercy`, `llmTurns [35,0]`, `fallbackTurns [4,0]`) agree with what the picture shows: a
lopsided paint fight in which blue banks the hill time. The picture is not empty, not frozen and
not unreadable.

**Chrome provenance:** it is the starter's. The transport strip, the `spoilers` toggle, the tick
`n / total` readout, the speed ladder, the two-plate scorebug with life pips, the banner-lane feed
and the momentum bar are the coworld-ctf/paintbot layout with paintball's numbers substituted into
the plates — not a rewrite that reuses the ids (the cogame-gridlock failure). `#viewpanel` /
minimap / zoombar are absent as the design says they should be. Two cosmetic snags worth logging:
the momentum bar is still labelled **`LIVES LEAD`** (design §Viewer 6 says that series is retargeted
to the hill-tick difference — the series is retargeted, the caption was not), and the endcard could
not be judged because the sampled frame is mid-game. Neither is a blocker.

**Command feed: real LLM commands, not wall-to-wall fallbacks.** Confirmed for the rendered
episode — every RED command line in the picture is an LLM directive with specific, situational
content (35 of 39 seat-0 directives are `llm`). The blue "HOLD THE HILL" lines are *correct*: that
seat is richard's **scripted** `holdline` policy, whose fixed note is "hold the hill", not a
paintball fallback.

---

## Retry / budget notes

- No polling was needed for checks 1–3: 16 completed rounds already existed. Round 18 completed
  mid-session (17:07:26Z) and, being the newest completed round, was adopted for checks 3–5, with
  round 17 kept alongside as same-session evidence.
- No fetch failed; no check consumed its retry budget. Total wall clock 17:02Z–17:09Z.
- Nothing was created, triggered, paused or modified. The only dispatch was
  `viewer-check.yml` run 32875824479 in coworld-builder.
