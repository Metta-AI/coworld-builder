# VERIFY — gen-generals-io   (2026-08-28T08:32:00Z)

Verdict: **all-true** (8/8 TRUE)

Run: `2026-08-28-gen-generals-io` · slug `gen-generals-io` · coworld `cow_faf3b0f4-c6b0-43e0-88b8-772046e5c61d` v`0.1.0`
League `$L` = `league_03508cde-90d2-43fa-a963-32265afd4737` · Division `$D` = `div_4deef2a2-7942-4235-8dd0-effed3d31905`

Every fetch below was made **fresh this run** (2026-08-28T08:05Z–08:32Z), except the two documented
exceptions: check 7 (reads the committed `runs/<run>/release-result.json`) and check 8's rendered
evidence (downloaded from the `viewer-check.yml` run **this verifier dispatched at 08:27:54Z**).

Headers sent on every Observatory call: `Authorization: Bearer <redacted>`, `User-Agent:
coworld-builder/1.0`; plus `X-Use-Elevated-Privileges: true` where noted. No header values are
printed anywhere in this file, and no token-bearing URL appears below.

Poll timeline (checks 1 and 3, every 5 min, bound 75 min from 08:06:31Z):

| poll | at (UTC) | completed rounds | round statuses |
|---|---|---|---|
| 1 | 08:06:31Z | 1 | `2:completed 1:failed` |
| 2 | 08:11:31Z | 1 | `2:completed 1:failed` |
| 3 | 08:16:31Z | 1 | `2:completed 1:failed` |
| 4 | 08:21:32Z | 1 | `3:pending 2:completed 1:failed` |
| 5 | 08:26:34Z | **2** | `3:completed 2:completed 1:failed` |

Bound satisfied at poll 5, 20 minutes into a 75-minute budget.

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

Fillers were registered **before** any round this verifier counts. Fetched fresh (elevated read, as
`playbooks/observatory-api.md` §6 requires):

```
GET /api/observatory/v2/leagues/$L/filler-policies
    headers: Authorization, User-Agent, X-Use-Elevated-Privileges
HTTP 200
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"5b80935f-88ce-4130-9024-d1a3da6f55f0","policy_id":"2cbaa893-522c-493c-8bb4-ceeb9cd002ff",
  "policy_name":"gen-generals-io-sprawl","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3",
  "player_name":"daveey","display_name":null},
 {"policy_version_id":"a0a62a58-0ba4-4539-aef8-22e39e261ed0","policy_id":"acf1f2b0-6981-4c04-82fa-6fa156218873",
  "policy_name":"gen-generals-io-crown","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3",
  "player_name":"daveey","display_name":null}]}
```

Both registered filler version ids match `STATE.policies.filler_version_ids` exactly, and neither is a
champion version (`landgrab` = `6ab310de-452c-4fb8-bc5c-65c0a09222c7`, `regicide` =
`d9eb7254-7459-4305-b9bf-de0272cc7add`, both seen in check 3's participants).

```
GET /api/observatory/v2/rounds?league_id=$L&limit=20
    headers: Authorization, User-Agent
HTTP 200 · fetched 2026-08-28T08:27:02Z · body shape: {"entries":[…],"limit","offset","total_count"}
```
```json
[
  {"id":"round_6ef8dba1-4398-49ff-bffd-29062836a405","round_number":3,"status":"completed",
   "error":null,"created_at":"2026-08-28T08:17:10.652345Z","updated_at":null},
  {"id":"round_6f2a048e-e9c0-4549-9f82-caf18c1bb98f","round_number":2,"status":"completed",
   "error":null,"created_at":"2026-08-28T08:02:10.278192Z","updated_at":null},
  {"id":"round_2e378060-5c8c-49cb-9ec5-25e5b534bc9c","round_number":1,"status":"failed",
   "error":"Temporal RoundWorkflow failed before settling the round.",
   "created_at":"2026-08-28T08:02:01.396331Z","updated_at":null}
]
```
```
$ jq -r '(if type=="array" then . else .entries end)|[.[]|select(.status=="completed")]|length'
2
```

Round 1's `error` verbatim, as the prompt requires: **`Temporal RoundWorkflow failed before settling
the round.`** — this is the platform's auto-scheduled pre-filler round (created 08:02:01, nine seconds
before round 2), the exact failure `playbooks/observatory-api.md` §6 documents for a round issued
before any filler exists. It is `failed`, so it does **not** count. Neither counted round relies on it:
round 2 (created 08:02:10) and round 3 (created 08:17:10) both seated the fillers as `Baseline` /
`Baseline (2)` — proven by check 3's `participants` and check 4's `results.names`, which is direct
evidence the filler registration was in force for both.

Status: **TRUE** — rounds **2** (`round_6f2a048e…`, finished 2026-08-28T08:06:14.675755Z per the
page's SSR `finishedAt`) and **3** (`round_6ef8dba1…`, finished 2026-08-28T08:23:13.036973Z) are
`completed`, both with fillers active, both after the failed pre-filler round 1.

---

## 2. Both champions ranked; fillers absent — TRUE

```
GET /api/observatory/v2/divisions/$D/leaderboard
    headers: Authorization, User-Agent
HTTP 200 · fetched 2026-08-28T08:27:10Z · body shape: bare JSON array (len=2)
```
```json
[{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
  "score":1030.5304984710244,"score_label":"MMR","score_value_type":"integer","rounds_played":2,
  "episode_wins":2.0,"episodes_played":null,"win_rate":1.0,
  "policy_label":"gen-generals-io-regicide:v1","recent_rounds":null},
 {"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
  "score":969.4695015289755,"score_label":"MMR","score_value_type":"integer","rounds_played":2,
  "episode_wins":0.0,"episodes_played":null,"win_rate":0.0,
  "policy_label":"gen-generals-io-landgrab:v1","recent_rounds":null}]
```
```
$ jq -r '(if type=="array" then . else .entries end)[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
1	daveey-1	gen-generals-io-regicide:v1	1030.5304984710244	2	2.0
2	daveey	gen-generals-io-landgrab:v1	969.4695015289755	2	0.0
```

Status: **TRUE** — `daveey` (`gen-generals-io-landgrab:v1`, rank 2, MMR 969.47, `rounds_played` 2) and
`daveey-1` (`gen-generals-io-regicide:v1`, rank 1, MMR 1030.53, `rounds_played` 2) are both ranked
with `rounds_played ≥ 1`. The array has **exactly two rows**: the fillers `gen-generals-io-sprawl:v1`
and `gen-generals-io-crown:v1` are **absent** from the leaderboard entirely (the stronger of the two
allowed outcomes — no `Baseline` row to have to excuse).

For the record, the earlier poll of the same endpoint at 08:05:50Z (before any round had settled)
returned literal `null`, and at 08:10Z it returned the same two rows at `rounds_played: 1` /
MMR 1016 / 984. The board is being written by the ladder, not stale.

---

## 3. Latest completed round's episode request completed with a replay — TRUE

Latest completed round = **round 3**, `round_6ef8dba1-4398-49ff-bffd-29062836a405`
(`max_by(.round_number)` over the check-1 body's completed entries).

The flat `GET /episode-requests?round_id=` route the prompt prints is dead (HTTP 405 since
2026-08-26); I used the nested route `playbooks/observatory-api.md` §9 marks WORKS.

```
GET /api/observatory/v2/rounds/round_6ef8dba1-4398-49ff-bffd-29062836a405/episode-requests
    headers: Authorization, User-Agent
HTTP 200 · body shape: {"entries":[…],"next_cursor"} · count=1
```
```
ereq_c07776fa-3525-4d77-b2cd-33468d8a562b	completed
```

```
GET /api/observatory/v2/episode-requests/ereq_c07776fa-3525-4d77-b2cd-33468d8a562b
    headers: Authorization, User-Agent
HTTP 200 · fetched 2026-08-28T08:27:25Z
$ jq '{status, replay_url}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/16454404-98c1-4ffd-b4a6-f27965b88be1.replay"
}
```
```
$ jq -r '.participants[]|[.position,.policy_name,.player_name,.is_filler]|@tsv'
0	gen-generals-io-landgrab	daveey	false
1	gen-generals-io-regicide	daveey-1	false
2	gen-generals-io-crown	daveey	true
3	gen-generals-io-crown	daveey	true

$ jq -c '.participant_scores'
[{"position":0,"score":0.0},{"position":1,"score":0.6666666666666666},
 {"position":2,"score":1.0},{"position":3,"score":0.3333333333333333}]
```

Full `participants` for the two champion seats (fetched, trimmed to the identifying fields):

```json
{"position":0,"kind":"policy","policy_version_id":"6ab310de-452c-4fb8-bc5c-65c0a09222c7",
 "policy_name":"gen-generals-io-landgrab","version":1,
 "player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
 "is_filler":false,"is_seed":false}
{"position":1,"kind":"policy","policy_version_id":"d9eb7254-7459-4305-b9bf-de0272cc7add",
 "policy_name":"gen-generals-io-regicide","version":1,
 "player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
 "is_filler":false,"is_seed":false}
```

Status: **TRUE** — `status == "completed"`, `replay_url` non-null, seat 0 = `daveey`
(`landgrab:v1`) and seat 1 = `daveey-1` (`regicide:v1`) with `is_filler:false`; seats 2–3 are
`is_filler:true` and are renamed **`Baseline`** / **`Baseline (2)`** in the replay and the viewer
(check 4's `results.names`, check 8's scorebug). Note both filler seats in round 3 drew
`gen-generals-io-crown` — the round-robin scheduler seated the same filler policy twice; round 2 seated
one `crown` and one `sprawl`. Not a check condition, recorded as an observation.

Corroboration on the previous completed round (round 2, fetched fresh at 08:07Z), so the pattern is not
a one-episode fluke: `ereq_ba808905-92bf-4932-b4f2-36e87de53cd3`, `status: "completed"`,
`replay_url: https://softmax-public.s3.amazonaws.com/replays/d2a1ed6f-f778-4bb9-bf30-30165a3a46ca.replay`,
participants `daveey`/`daveey-1`/`crown`(filler)/`sprawl`(filler).

---

## 4. Replay bytes are valid and show the game — TRUE

```
GET https://softmax-public.s3.amazonaws.com/replays/16454404-98c1-4ffd-b4a6-f27965b88be1.replay
    (curl -sSL, no auth header — public S3 object)
HTTP 200 bytes=40655
$ head -c 16 ep.replay | od -c
0000000   C   O   W   L   D   G   E   N  \0 001  \0 017   g   e   n   -
```

`jq -e .` on the raw bytes **fails**, and that is the designed format, not a defect: the replay is the
`COWLDGEN` binary container the manifest declares (`manifest.game.protocols` global doc: *"The replay
… Binary, magic `COWLDGEN`"*, and `docs/PROTOCOL.md`). The strict-UTF-8-JSON parse is done on the
summary object the repo's shipped stdlib tool emits from those bytes, exactly as
`prompts/60-verify.md`'s intent requires:

```
$ jq -e . ep.replay        ->  FAILED (binary COWLDGEN container — designed format)
$ python3 tools/replay_summary.py ep.replay > sum.json   # repo Metta-AI/cogame-gen-generals-io @ e8be315
   exit=0
$ jq -e . sum.json >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok
```

```
$ jq -c '{protocol,formatVersion,gameName,gameVersion,turnCount,hashCount,names,aliases,
          policyKinds,planInputs,decisions:(.plans|length),fallbacks,fallbackCauses,stop,budgetGuard}' sum.json
```
```json
{"protocol":"gen-generals-io/v1","formatVersion":1,"gameName":"gen-generals-io","gameVersion":"1",
 "turnCount":234,"hashCount":235,
 "names":["daveey","daveey-1","Baseline","Baseline (2)"],
 "aliases":["RED-alpha","BLUE-alpha","GREEN-alpha","YELLOW-alpha"],
 "policyKinds":["llm","llm","scripted","scripted"],
 "planInputs":92,"decisions":92,"fallbacks":0,"fallbackCauses":[],"stop":null,"budgetGuard":null}
```

```
$ jq -c '.results' sum.json
```
```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],
 "aliases":["RED-alpha","BLUE-alpha","GREEN-alpha","YELLOW-alpha"],
 "scores":[0.0,0.6666666666666666,1.0,0.3333333333333333],
 "win":[false,false,true,false],"winner":2,
 "reason":"complete","endRule":"conquest","rank":[3,1,0,2],
 "land":[0,0,129,0],"army":[0,0,1132,0],"cities":[0,0,10,0],"generalsCaptured":[0,0,3,0],
 "eliminatedTurn":[49,233,-1,195],"eliminatedBy":[2,2,-1,2],
 "tilesTaken":[30,46,70,38],"tilesLost":[3,29,8,19],
 "movesMade":[48,226,213,146],"invalidMoves":[1,2,0,1],"passes":[1,6,21,49],
 "turnsPlayed":234,"boardW":16,"boardH":10,"seed":1160068625,
 "policyKinds":["llm","llm","scripted","scripted"],
 "llmTurns":[7,30,0,0],"fallbackTurns":[0,0,0,0],"directivesRejected":[0,0,0,0],
 "deadSeats":[false,false,false,false],"stopDetail":""}
```

Protocol: `"gen-generals-io/v1"`, which is the value the repo declares
(`src/generals/sim_types.nim:22 ReplayProtocol* = "gen-generals-io/v1"`, asserted by
`tests/test_gen_replay.nim:283`) and the value the coordinator's brief names. The manifest's own
protocol docs cover the wire and container layer (`gen-generals-io.player.v1` for the player socket,
magic `COWLDGEN` for the file); the coworld's live `manifest_hash` fetched from
`GET /coworlds/cow_faf3b0f4…` is `sha256:6fd438487a909a3b2144f8fb74b4db8db4bd3d13e650f3912481e14744126e94`,
identical to `STATE.coworld.manifest_sha` and to the `<sha>` segment of check 6's static viewer URL.

`results.reason == "complete"` — the **normal** case, not the documented `deadline` exception, so no
exception needs citing. `endRule: "conquest"` is the closed-enum value `design.md` §End conditions
pairs with `complete`.

Decisions are non-scripted and non-trivial on the champion seats, and fallbacks are **zero**, not a
minority:

```
$ jq -r '[.plans[]|.source]|group_by(.)|map({(.[0]):length})|add' sum.json
{"llm": 37, "scripted": 55}
$ jq -r '[.plans[]|select(.seat<2)]|length' sum.json                      -> 37
$ jq -r '[.plans[]|select(.seat<2 and (.note|length)>0)]|length' sum.json  -> 37
$ jq -r '[.plans[]|select(.source=="fallback")]|length' sum.json           -> 0
$ jq -c '{fallbacks,fallbackCauses}' sum.json   -> {"fallbacks":0,"fallbackCauses":[]}
$ jq -c '{llmTurns:.results.llmTurns,fallbackTurns:.results.fallbackTurns,
          directivesRejected:.results.directivesRejected}' sum.json
{"llmTurns":[7,30,0,0],"fallbackTurns":[0,0,0,0],"directivesRejected":[0,0,0,0]}
```

All 37 champion-seat plan records have `source: "llm"` and a **non-empty** `note`; 0 fallbacks,
0 rejected directives, no `budget_guard` record, no `stop` record. Seat 0's LLM turn count is 7 because
`daveey` was eliminated at turn 49; seat 1 ran the full 30 directives.

Status: **TRUE** — strict-UTF-8-JSON-parseable summary from valid `COWLDGEN` bytes; `protocol`
`gen-generals-io/v1` as declared; `results.reason == "complete"`; 37/37 champion decisions LLM-sourced
with real content and 0 fallbacks.

---

## 5. Hosted game log is clean — TRUE

```
GET /api/observatory/v2/episode-requests/ereq_c07776fa-3525-4d77-b2cd-33468d8a562b/artifacts/logs
    headers: Authorization, User-Agent, X-Use-Elevated-Privileges
HTTP 200 bytes=81896
```

The body is python `b'…'` byte-string reprs under `===== container: <name> =====` headers, so it was
decoded per-repr with `ast.literal_eval` before grepping (`playbooks/observatory-api.md` §10 — a naive
line grep undercounts):

```
$ python3 declog.py logs-r3.raw     # ast.literal_eval per b'…' line, then the four-pattern grep
decoded_bytes=81669 decoded_lines=227
containers: ['===== container: coworld-init-config =====', '===== container: bedrock-sidecar =====',
             '===== container: game =====', '===== container: worker =====']
CLEAN
```
```
$ grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs-r3.raw
0
```

Zero matches for `falling back`, `LLM provider is unavailable`, `cut off at max_tokens` and `rejected`
in the **decoded** text (81 669 bytes, 227 lines, all four containers present), and zero in the raw
bytes as a cross-check. No documented exception is being invoked — the log is clean on its own terms,
with no Bedrock capacity symptom to excuse.

Round 2's log, fetched fresh at 08:09Z from
`GET /episode-requests/ereq_ba808905-92bf-4932-b4f2-36e87de53cd3/artifacts/logs` (HTTP 200,
bytes=96153), decoded to 95 900 bytes / 253 lines across the same four containers and is also
**CLEAN** — both completed rounds, not just the latest.

Status: **TRUE** — CLEAN.

---

## 6. The public page uses the static replay path — TRUE

I used **both** sources the prompt names, and I record which produced the answer.

*Source A — raw HTML grep (the prompt's first command): found nothing.* Per the playbook §Featured
match, this is **unknown, not a failure**: the page is client-rendered for the iframe.

```
$ curl -sS "https://softmax.com/gen-generals-io" | wc -c
728293                                              # HTTP 200
$ grep -o '<iframe[^>]*src="[^"]*"' page-final.html
(no output)  ->  NO IFRAME IN RAW HTML (page is client-rendered — documented)
```

*Source B — the coworld detail API.* Also not the answer here: `featured_match` is `null`
platform-wide (documented, lighthouse run 2026-08-22) and `replay_viewer` is `null`.

```
GET /api/observatory/v2/coworlds?limit=200   (headers: Authorization, User-Agent)   HTTP 200
$ jq -r '(if type=="array" then . else .entries end)[]|select(.name=="gen-generals-io")
         |{id,canonical,replay_viewer,featured_match}'
```
```json
{"id":"cow_faf3b0f4-c6b0-43e0-88b8-772046e5c61d","canonical":true,
 "replay_viewer":null,"featured_match":null}
```

*Source C — the two things that ARE evidence, per the playbook's answered note: the page's SSR
payload `state.playlist[0]`, and the session call the page's own JS makes.* **This is the source the
verdict rests on.**

The **featured match is present**, server-rendered into the page HTML I just fetched (excerpt from
`page-final.html`, backslash-escaped quotes unescaped for legibility):

```json
"playlist":[{"episodeId":"5aedb588-609e-422f-a85d-d2680cb1133f",
 "coworldId":"cow_faf3b0f4-c6b0-43e0-88b8-772046e5c61d","coworldName":"gen-generals-io",
 "coworldVersion":"0.1.0",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/16454404-98c1-4ffd-b4a6-f27965b88be1.replay",
 "finishedAt":"2026-08-28T08:23:13.036973Z","roundNumber":3,"episodeNumber":1,
 "code":"gen-generals-io.r3.e1",
 "matchup":{"divisionId":"div_4deef2a2-7942-4235-8dd0-effed3d31905","divisionName":"Competition",
  "first":{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
   "score":1030.5304984710244,"score_label":"MMR","rounds_played":2,"episode_wins":2,"win_rate":1,
   "policy_label":"gen-generals-io-regicide:v1"},
  "second":{"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
   "score":969.4695015289755,"score_label":"MMR","rounds_played":2,"episode_wins":0,"win_rate":0,
   "policy_label":"gen-generals-io-landgrab:v1"}}}]
```

The featured match names **both ranked champions**, and its `replayUrl` is byte-identical to check 3's
`replay_url` for round 3 — the page is featuring the episode this file verifies. (At 08:10Z the same
payload featured round 2's `d2a1ed6f-…` with the same two players; it advanced to round 3 on its own.)

The iframe `src` the page builds from that entry:

```
POST /api/observatory/v2/coworlds/replays/session
    headers: Authorization, User-Agent, content-type: application/json
    body: {"coworld_id":"cow_faf3b0f4-c6b0-43e0-88b8-772046e5c61d",
           "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/16454404-98c1-4ffd-b4a6-f27965b88be1.replay"}
HTTP 200
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_faf3b0f4-c6b0-43e0-88b8-772046e5c61d/sha256%3A6fd438487a909a3b2144f8fb74b4db8db4bd3d13e650f3912481e14744126e94/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F16454404-98c1-4ffd-b4a6-f27965b88be1.replay",
  "ready": true
}
```

Path anatomy: `…/v2/coworlds/replays/**static**/<cow_id>/<sha>/index.html` — the static route, with
`<sha>` = `sha256:6fd438487a909a3b2144f8fb74b4db8db4bd3d13e650f3912481e14744126e94` URL-encoded, which
is the coworld's `manifest_hash` fetched live from `GET /coworlds/cow_faf3b0f4…` and equal to
`STATE.coworld.manifest_sha`. The replay arrives as the URL-encoded `#replay=` **fragment** rather than
`?replay=` — the documented 2026-08-28 form of the same static route (playbook §Featured match:
*"since 2026-08-28 the session endpoint returns the replay as a URL-encoded fragment instead … both are
the static route"*). `ready: true` ⇔ static delivery. There is **no** `/client/replay` pod URL anywhere
in the response.

Status: **TRUE** — featured match present (round 3, both champions ranked); iframe `src` is the static
`/v2/coworlds/replays/static/<cow_id>/<manifest_sha>/index.html` route with `ready:true`; source used
for the verdict = **the SSR payload `state.playlist[0]` plus `POST /coworlds/replays/session`** (the raw
HTML grep found nothing and `/coworlds`.`featured_match` is `null`, both documented non-signals).

---

## 7. Certification declared the static bundle — TRUE

Source read: **`runs/2026-08-28-gen-generals-io/release-result.json`**, the copy phase 40 committed to
the run directory (present; no re-download from run `33152888435` was needed, and `/tmp` was never
consulted).

```
$ jq -r '.certify.replay_liveness' runs/2026-08-28-gen-generals-io/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)

$ jq -c '{ok,canonical,certify_ok:.certify.ok}' runs/2026-08-28-gen-generals-io/release-result.json
{"ok":true,"canonical":true,"certify_ok":true}
```

Cross-checked against the **live** manifest, which is what makes the skip legitimate rather than a
waiver — the coworld genuinely declares a static bundle:

```
GET /api/observatory/v2/coworlds/cow_faf3b0f4-c6b0-43e0-88b8-772046e5c61d   HTTP 200
$ jq -c '.manifest.game|to_entries|map(select(.key|test("replay|viewer|client")))|from_entries'
{"replay_viewer":{"bundle":"sha256:02fa037224e3c1fe305e354ab78d1f884a2120738c56f32bf8d9962e349db295"}}
```

Status: **TRUE** — the string `Replay liveness: skipped (static replay bundle declared` is present
verbatim, read from the **committed** `release-result.json`.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — TRUE

*(a) Dispatch.* The URL rendered is check 6's iframe `src` verbatim, fragment and all.

```
DISPATCH_AT=2026-08-28T08:27:54Z
$ gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
$ gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
  | jq -c 'sort_by(.createdAt)|reverse|.[0:3]'
[{"createdAt":"2026-08-28T08:27:56Z","databaseId":33155441744,"status":"in_progress"},
 {"createdAt":"2026-08-28T08:27:36Z","databaseId":33155420501,"status":"in_progress"},
 {"createdAt":"2026-08-28T08:20:24Z","databaseId":33154949153,"status":"completed"}]
```

**viewer-check run id = `33155441744`** (created 08:27:56Z, 2 s after my dispatch).
A second `viewer-check` run (`33155420501`, created 08:27:36Z) belongs to **another parallel run's
verifier**, so "the latest run" was genuinely ambiguous here; I disambiguated on the artifact's own
`url` field rather than on ordering alone. (`33154949153`, third in that list, is my own earlier probe
dispatch against round 2 — see the secondary-evidence note at the end of this section.)

```
$ gh run watch 33155441744 -R Metta-AI/coworld-builder --exit-status   -> exit 0
$ gh run view 33155441744 -R Metta-AI/coworld-builder --json conclusion,createdAt,url
{"conclusion":"success","createdAt":"2026-08-28T08:27:56Z",
 "url":"https://github.com/Metta-AI/coworld-builder/actions/runs/33155441744"}

$ gh run download 33155441744 -R Metta-AI/coworld-builder -n viewer-check \
    -D runs/2026-08-28-gen-generals-io/viewer-check
smoke-stderr.txt (0 B)  smoke-stdout.txt (754 B)  viewer-smoke.json (1550 B)  viewer-smoke.png (434340 B)

$ jq -r '.url' runs/2026-08-28-gen-generals-io/viewer-check/viewer-smoke.json
https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_faf3b0f4-c6b0-43e0-88b8-772046e5c61d/sha256%3A6fd438487a909a3b2144f8fb74b4db8db4bd3d13e650f3912481e14744126e94/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F16454404-98c1-4ffd-b4a6-f27965b88be1.replay
URL MATCH: identical to the SRC I dispatched and to check 6's viewer_url  ->  this artifact is my run
```

`runs/2026-08-28-gen-generals-io/viewer-check/` holds `viewer-smoke.json` + `viewer-smoke.png` and must
be committed with this file — the CI sandbox that drew it is gone next heartbeat.

*(b) The readouts, verbatim from the artifact.*

```
$ jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-28-gen-generals-io/viewer-check/viewer-smoke.json
{"loaded":true,"ms":2005,"clock":"TURN 2 / 240 PLAN 1/30 · 4 CROWNS STANDING · RED LEADS 2 LAND","scorebug":"daveey LAND 2 3 army · 0 cities Baseline LAND 1 3 army · 0 cities TURN 2 / 240 PLAN 1/30 · 4 CROWNS STANDING · RED LEADS 2 LAND daveey-1 LAND 2 3 army · 0 cities Baseline (2) LAND 1 3 army · 0 cities","feed_lines":0}
```
```
$ jq -c '.signals' …/viewer-smoke.json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}

$ jq -r '.failure // "no failure"' …/viewer-smoke.json
no failure

$ jq -c '{status,loading_text,canvas_text,console_tail}' …/viewer-smoke.json
{"status":"OPEN","loading_text":null,
 "canvas_text":{"total":0,"outside":0,"ellipsized":0,"never_inside":0,
                "never_inside_samples":[],"distinct_capped":false,"samples":[]},
 "console_tail":[]}
```

The three clock readouts (`$ jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | `#clock` readout |
|---|---|
| **0 %** | `TURN 2 / 240 PLAN 1/30 · 4 CROWNS STANDING · RED LEADS 2 LAND` |
| **50 %** | `TURN 171 / 240 PLAN 22/30 · 3 CROWNS STANDING · GREEN LEADS 73 LAND` |
| **100 %** | `FINAL GAME OVER` |

All three **differ**, and they differ in the right direction: turn 2 → turn 171 → final; 4 crowns
standing → 3 standing → game over; RED nominally ahead by 2 land in the opening → GREEN ahead by 73
land three-quarters through. A `#scrub` element exists and responds (no `"(no #scrub…)"` string in the
json), so motion is measured from the scrubber, not inferred.

*(c) The replay JSON the viewer was asked to draw* — ordered excerpts from `ep.replay`
(check 4), via `tools/replay_summary.py`, `[turn, seat, alias, source, intent, target, note]`:

```
=== EARLY (first 12 plan records)
0	0	RED-alpha	llm	expand	null	Turn 0: Starting expansion phase. All players equal at 1 land, 1 army. Growing the only ad
0	1	BLUE-alpha	llm	expand	null	Turn 0: Starting expansion with heavy scouting to find enemy crowns. Two scouts per four t
0	2	GREEN-alpha	scripted	expand	null
0	3	YELLOW-alpha	scripted	expand	null
8	0	RED-alpha	llm	expand	null	Turn 8: tied at 6 land with BLUE. Expanding into fog to claim the compounding advantage. G
8	1	BLUE-alpha	llm	expand	null	Turn 8/240: continuing scouting plan. 6 land, 9 army. No crowns spotted yet. Expanding car
8	2	GREEN-alpha	scripted	expand	null
8	3	YELLOW-alpha	scripted	expand	null
16	0	RED-alpha	llm	expand	null	Turn 16: Land tied at 11 each, still early expansion phase. Push through fog systematicall
16	1	BLUE-alpha	llm	expand	null	Turn 16: no crowns found yet. Continue scouting aggressively per directive. Expand to uncl
16	2	GREEN-alpha	scripted	expand	null
16	3	YELLOW-alpha	scripted	expand	null

=== MIDDLE (records 40-52)
88	1	BLUE-alpha	llm	raid	[13,7]	YELLOW at [13,7] has 58 army vs our 78. Continue raid, captain routes around larger stacks
88	2	GREEN-alpha	scripted	expand	null
88	3	YELLOW-alpha	scripted	defend	null
96	1	BLUE-alpha	llm	raid	[13,7]	YELLOW at [13,7] has 54 army vs our 76. Close fight but we have the edge. Push raid home.
96	2	GREEN-alpha	scripted	expand	null
96	3	YELLOW-alpha	scripted	raid	[13,2]
104	1	BLUE-alpha	llm	raid	[13,7]	YELLOW at [13,7] army 14 vs my 14. Continue raid; captain routes around equal stacks. Need
104	2	GREEN-alpha	scripted	expand	null
104	3	YELLOW-alpha	scripted	raid	[13,2]
112	1	BLUE-alpha	llm	raid	[13,7]	YELLOW at [13,7] has 65 army vs our 94. Raid continues. They're close and weakest known ta
112	2	GREEN-alpha	scripted	expand	null
112	3	YELLOW-alpha	scripted	raid	[13,2]

=== LATE (last 12)
192	2	GREEN-alpha	scripted	expand	null
192	3	YELLOW-alpha	scripted	defend	null
200	1	BLUE-alpha	llm	raid	[13,7]	GREEN at [13,7] has 29 army, I have 50+131=181 total. Raid the visible city. After taking
200	2	GREEN-alpha	scripted	expand	null
208	1	BLUE-alpha	llm	raid	[9,0]	GREEN dominates 914 army vs our 132. Raiding weaker known_generals. [9,0] is older intel b
208	2	GREEN-alpha	scripted	expand	null
216	1	BLUE-alpha	llm	defend	null	Crown threatened by GREEN stack at [11,3] (76 army). Defend home for 6 turns, consolidate,
216	2	GREEN-alpha	scripted	raid	[13,2]
224	1	BLUE-alpha	llm	defend	null	Crown threatened, staying defensive. GREEN dominates 110 tiles to our 19. Consolidate at [
224	2	GREEN-alpha	scripted	raid	[13,2]
232	1	BLUE-alpha	llm	defend	null	Crown threatened at 99 vs GREEN's 1205. Hold position, consolidate, survive to endgame. GR
232	2	GREEN-alpha	scripted	raid	[13,2]
```
```
$ jq -r '.results' ep-summary   (full body pasted in check 4)
  winner 2 · reason "complete" · endRule "conquest" · rank [3,1,0,2]
  land [0,0,129,0] · army [0,0,1132,0] · cities [0,0,10,0] · generalsCaptured [0,0,3,0]
  eliminatedTurn [49,233,-1,195] · eliminatedBy [2,2,-1,2]
```

**Item 8 verdict: TRUE** — `loaded: true` (`data_replay_loaded:"true"`, first frame at **2 005 ms**,
`failure: null`, `loading_text: null`, empty `console_tail`) **and** the three clock readouts differ.

### Spectator-judgment paragraph

It is legible, and it shows the game. `runs/2026-08-28-gen-generals-io/viewer-check/viewer-smoke.png`
is a full 1280 × 800 frame of a finished match, not a loading shell. Reading it top to bottom (I
brightened and 8×-upscaled crops to read the small type, and I state only what is in those pixels): a
four-plate scorebug across the top — `0 LAND daveey / out t49`, `129 LAND Baseline / 1132 army ·
10 cities`, `0 LAND daveey-1 / out t233`, `0 LAND Baseline (2) / out t195` — with a centred
`FINAL / GAME OVER` clock; a fog-lens chip row reading `ALL ■ | RED | BLUE | ■GREEN | YELLOW` with
`GROWTH IN 16` at the right; a 16 × 10 board drawn edge to edge, almost entirely GREEN-owned, with a
legible garrison integer on every occupied cell (`3`, `5`, `10`, `22`, `29`, `55`…), mountains as
brick-textured blocks and cities as crenellated tiles carrying big stacks (`71`, `61`, `38`); a beat
toast `GREEN TAKES BLUE'S CROWN — INHERITS 17 TILES AND 16 ARMIES`, which is this game's signature
snowball rule narrated on screen; and an endcard reading **"GENERALS — BASELINE WINS"** with the chip
`LAST CROWN STANDING`, the sentence *"3 crowns fell; the survivors were ranked on land, then army,
then cities."*, and a COMMANDER / LAND / ARMY / CITIES / CROWNS table listing `Baseline` (GREEN-alpha)
129 / 1132 / 10 / 3, then `daveey…` (BLUE-alpha · out t233), `Baselin…` (YELLOW-alpha · out t195),
`daveey` (RED-alpha · out t49), all zeros. **Every one of those numbers reconciles exactly with the
replay record** — `land[2]=129`, `army[2]=1132`, `cities[2]=10`, `generalsCaptured[2]=3`,
`eliminatedTurn=[49,233,-1,195]`, and `rank=[3,1,0,2]` giving precisely the row order shown — so the
picture and the record agree down to the elimination turns, and the three scrub readouts trace the
same arc the plan excerpts do (RED nominally ahead at turn 2 → GREEN ahead by 73 land at turn 171 with
3 crowns standing → final). It **does look like the starter's chrome**, the same coworld-ctf /
paintbot-lineage furniture in the same places: the transport strip (restart · step-back · play · `+5s`
· step · loop · fast-forward), the `spoilers` toggle, the `GREEN WINS  306 / 306` tick counter, the
`1× 2× 4× 8×` speed chips, and beneath them the scrubber with the **LAND momentum graph** (green,
yellow and red traces) and clickable beat ticks. This is the starter re-skinned for a conquest grid,
not the cogame-gridlock failure mode of a different product wearing the same ids. Four observations for
the coordinator, none of them a check failure:
**(i)** a red banner **"REPLAY HASH MISMATCH — SHOWING RECORDED PLANS"** (`#mmwarn`, set when
`mm >= 0`, i.e. when the in-browser re-simulation's `gameHash` diverges from a recorded hash —
`src/generals/replay_runtime.nim:158-159`) is lit on **both** hosted replays I rendered this run
(round 3 and the round-2 probe below), so the wasm re-simulation is not bit-identical to the hosted
episode. The viewer degrades exactly as designed and the scorebug, endcard and beats stay faithful to
the record, but the mid-game *board* a spectator watches may not be the board that was played. This is
the one finding I would put in front of a reviewer.
**(ii)** that banner also overlaps the endcard's `GAME OVER` line and clips the top of the fog-lens
chip row — a small layout collision at the busiest moment of the frame.
**(iii)** `feed_lines: 0` in the JSON was sampled at the first drawn frame (turn 2, before any event
exists), so the count carries no signal here; in this final frame the feed column is also empty,
whereas the round-2 probe frame showed three stacked plan cards quoting a commander's own reasoning
(`"GREEN-alpha crown at [4,7] with 9 army…"`) overlapping each other and the board. So the feed does
render and does quote the LLM, but its behaviour at the end-of-match frame and its card stacking are
worth a legibility look; there is no `#scrub`-absence problem (the scrubber exists and responds).
**(iv)** `canvas_text` is `0 drawn / 0 outside / 0 ellipsized` — all chrome text is DOM here, so the
strict-text-bounds instrument had nothing to measure and its "no clipping" reads as "not applicable".

*Secondary rendered evidence, same run:* before round 3 settled I dispatched `viewer-check.yml` once
against the then-live featured match (round 2's replay) — run **`33154949153`**, dispatched
2026-08-28T08:20:22Z, conclusion `success`. Its artifact is committed alongside at
`runs/2026-08-28-gen-generals-io/viewer-check/probe-round2/` so the sentences above about it are
checkable. Verbatim:
```
{"loaded":true,"ms":4772,"clock":"TURN 0 / 240 PLAN 1/30 · 4 CROWNS STANDING · RED LEADS 1 LAND","scorebug":"daveey LAND 1 1 army · 0 cities Baseline LAND 1 1 army · 0 cities TURN 0 / 240 PLAN 1/30 · 4 CROWNS STANDING · RED LEADS 1 LAND daveey-1 LAND 1 1 army · 0 cities Baseline (2) LAND 1 1 army · 0 cities","feed_lines":0}
0%	TURN 0 / 240 PLAN 1/30 · 4 CROWNS STANDING · RED LEADS 1 LAND
50%	TURN 143 / 240 PLAN 18/30 · 3 CROWNS STANDING · BLUE LEADS 50 LAND
100%	FINAL GAME OVER
```
Its endcard reads **"GENERALS — DAVEEY-1 WINS"** with `daveey-1` BLUE-alpha 125 / 482 / 8 / 2, matching
round 2's replay `results` (`land[1]=125, army[1]=482, cities[1]=8, generalsCaptured[1]=2, winner 1`).
The item-8 verdict above rests on the **round-3** artifact, which is the one check 6's live iframe
`src` points at; this probe is corroboration that the viewer draws and advances on more than one
episode, and that the hash-mismatch banner is systematic rather than a one-off.

---

## Summary table

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 2 and 3 |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey-1 #1, daveey #2, both `rounds_played: 2`; fillers absent |
| 3 | Latest round's episode request completed with replay | **TRUE** — `ereq_c07776fa…`, `completed`, replay_url set, daveey + daveey-1 seated |
| 4 | Replay bytes valid and show the game | **TRUE** — `gen-generals-io/v1`, `reason: complete`, 37/37 LLM decisions, 0 fallbacks |
| 5 | Hosted game log clean | **TRUE** — CLEAN (decoded, both rounds) |
| 6 | Public page uses the static replay path | **TRUE** — static route, `ready:true`, featured match round 3 |
| 7 | Certification declared the static bundle | **TRUE** — `Replay liveness: skipped (static replay bundle declared…` |
| 8 | Viewer executed and judged | **TRUE** — `loaded:true` @2005 ms, three differing clocks, run `33155441744` |

Nothing was marked TRUE by inference. No item is `NOT FETCHED`.
