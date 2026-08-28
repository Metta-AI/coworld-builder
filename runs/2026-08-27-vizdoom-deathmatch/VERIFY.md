# VERIFY — vizdoom-deathmatch   (2026-08-28T02:12Z)

Verdict: **all-true** (8/8 TRUE)

Run: `2026-08-27-vizdoom-deathmatch` · coworld `cow_4e53e339-ec7c-4059-8e13-881aedbea5ba` v0.1.0 ·
league `league_00dcb926-7f23-4507-8a2d-6684cb0e7c4b` · division `div_67b01fa1-41ae-493c-8a1d-bb69f08bd83a`.

Common preamble for every `curl` below (header **names** only; values are never printed):

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_00dcb926-7f23-4507-8a2d-6684cb0e7c4b
D=div_67b01fa1-41ae-493c-8a1d-bb69f08bd83a
```

Poll log (checks 1 and 3, §Waiting bound 75 min, started 01:53Z — bound would have expired 03:08Z):

| UTC | rounds seen |
|---|---|
| 01:53:17 | r1 `failed`, r2 `pending` |
| 01:58:40 | r1 `failed`, r2 `completed` |
| 02:04:57 | unchanged (no r3 yet) |
| 02:09:50 | r1 `failed`, r2 `completed`, **r3 `completed`** → check 1 satisfied at 02:09:50Z, 17 min into the bound |

---

## 1. ≥2 completed rounds after the fillers were set

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq 'if type=="array" then . else .entries end
       | map({id,round_number,status,error,created_at,updated_at})'
```
(the list came back wrapped in `{entries:…}` this time; the dual-shape `jq` from
`playbooks/observatory-api.md` §2 is used everywhere below.)

```json
[
  {
    "id": "round_b1b9548f-1b4d-4219-8f2f-5377c6441a1f",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T02:06:15.657620Z",
    "updated_at": null
  },
  {
    "id": "round_3eabfb3f-9746-441f-ab19-9bf5652aa094",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T01:51:14.832942Z",
    "updated_at": null
  },
  {
    "id": "round_972ecc54-57c3-4705-9d68-586034c0519e",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-28T01:51:01.020635Z",
    "updated_at": null
  }
]
```

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '[ (if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
2
```

Round 1's `error` verbatim: `"Temporal RoundWorkflow failed before settling the round."` — the
documented signature of a `trigger-round` issued before any filler policy existed
(`playbooks/observatory-api.md` §6). It is `failed`, so it does not count.

**Fillers were registered before round 2 was triggered** — the live read of the league's filler
list (a read that requires the elevated header, per §6):

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}" | jq .
```
```json
{
  "filler_policy_versions": [
    {"policy_version_id": "009fc22a-b786-4708-9c49-070061583e0e", "policy_name": "vzd-rusher",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "display_name": null},
    {"policy_version_id": "8dd54435-87ee-4353-ad6e-9ff5b5374b63", "policy_name": "vzd-sentry",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "display_name": null}
  ]
}
```
Neither uuid is a champion's (champions are `d4fdd9d3-…` / `3a4fba26-…`, see check 3), and
`runs/2026-08-27-vizdoom-deathmatch/log.md:45` records the ordering:

```
2026-08-28T01:52:30Z 50 filler-policies POST 200: rusher+sentry UUIDs only, neither champion; rounds-paused false 200; trigger-round 200
2026-08-28T01:52:30Z 50 rounds: round 1 failed (Temporal RoundWorkflow, auto-round before fillers landed — superseded), round 2 pending with both champions in entrant_attributions
```

Both counted rounds seated both champions (`round_config.entrant_attributions`, same fetch):

```json
[{"round_number":3,"status":"completed","attrib":[
   {"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player","policy_version_id":"d4fdd9d3-9c79-4fe3-b07f-8d641f50f9e7","league_policy_membership_id":"lpm_3ffb63a4-24d5-4d9e-97ee-3f27cd2dfd15"},
   {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","subject_type":"player","policy_version_id":"3a4fba26-4fd1-4cb4-8bbb-c0f8c6b4052e","league_policy_membership_id":"lpm_556c83eb-81ca-4ef9-930d-c8f8fe0197d3"}]},
 {"round_number":2,"status":"completed","attrib":[
   {"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player","policy_version_id":"d4fdd9d3-9c79-4fe3-b07f-8d641f50f9e7","league_policy_membership_id":"lpm_3ffb63a4-24d5-4d9e-97ee-3f27cd2dfd15"},
   {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","subject_type":"player","policy_version_id":"3a4fba26-4fd1-4cb4-8bbb-c0f8c6b4052e","league_policy_membership_id":"lpm_556c83eb-81ca-4ef9-930d-c8f8fe0197d3"}]}]
```

**Status: TRUE** — rounds **2** (created 01:51:14Z) and **3** (created 02:06:15Z) are `completed`,
both strictly after the filler registration at 01:52:30Z / after the superseded round 1. No
`discarded` rounds exist.

---

## 2. Both champions ranked, fillers absent

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
(bare JSON list, as documented — `.entries` is absent.)

```
1	daveey	vzd-pointman:v1	1001.4695015289755	2	1.0
2	daveey-1	vzd-crossfire:v1	998.5304984710245	2	1.0
```

**Status: TRUE** — `daveey` (rank 1, `vzd-pointman:v1`, `rounds_played` 2, 1 episode win) and
`daveey-1` (rank 2, `vzd-crossfire:v1`, `rounds_played` 2, 1 episode win) are both ranked with
`rounds_played ≥ 1`. Exactly two rows: the fillers `vzd-rusher:v1` / `vzd-sentry:v1` are **absent**
from the leaderboard, as required.

---

## 3. Latest completed round's episode request completed with a replay

The prompt's flat route is dead — recorded here rather than silently worked around:

```bash
curl -sS -o /tmp/flat.json -w "http=%{http_code}\n" "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}"
http=405
{"detail":"Method Not Allowed"}
```

So the nested route from `playbooks/observatory-api.md` §9 was used. Latest completed round is
`round_b1b9548f-1b4d-4219-8f2f-5377c6441a1f` (round_number 3, from check 1):

```bash
R=round_b1b9548f-1b4d-4219-8f2f-5377c6441a1f
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" \
 | jq -c 'if type=="array" then . else .entries end | map({id,status,created_at})'
```
```json
[{"id":"ereq_c9f0e294-6a18-48ee-9d07-5b051a366a49","status":"completed","created_at":"2026-08-28T02:06:15.968654Z"}]
```

```bash
EREQ=ereq_c9f0e294-6a18-48ee-9d07-5b051a366a49
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url,
        participants: [.participants[]|{position,policy_name,player_name,is_filler}],
        participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/ca0f7fc8-967f-4de8-9b47-ba746186dd3c.replay",
  "participants": [
    {"position": 0, "policy_name": "vzd-pointman",  "player_name": "daveey",   "is_filler": false},
    {"position": 1, "policy_name": "vzd-crossfire", "player_name": "daveey-1", "is_filler": false},
    {"position": 2, "policy_name": "vzd-sentry",    "player_name": "daveey",   "is_filler": true},
    {"position": 3, "policy_name": "vzd-sentry",    "player_name": "daveey",   "is_filler": true},
    {"position": 4, "policy_name": "vzd-sentry",    "player_name": "daveey",   "is_filler": true},
    {"position": 5, "policy_name": "vzd-rusher",    "player_name": "daveey",   "is_filler": true},
    {"position": 6, "policy_name": "vzd-rusher",    "player_name": "daveey",   "is_filler": true},
    {"position": 7, "policy_name": "vzd-sentry",    "player_name": "daveey",   "is_filler": true}
  ],
  "participant_scores": [
    {"position": 0, "score": 0.666}, {"position": 1, "score": 0.334},
    {"position": 2, "score": 0.666}, {"position": 3, "score": 0.334},
    {"position": 4, "score": 0.666}, {"position": 5, "score": 0.334},
    {"position": 6, "score": 0.666}, {"position": 7, "score": 0.334}
  ]
}
```
(Full `participants` rows also carry `policy_version_id` `d4fdd9d3-9c79-4fe3-b07f-8d641f50f9e7`
for seat 0 and `3a4fba26-4fd1-4cb4-8bbb-c0f8c6b4052e` for seat 1 — the same two ids the round's
`entrant_attributions` name in check 1. Elided above only for width.)

**Status: TRUE** — `status == "completed"`, `replay_url` non-null, seat 0 = `daveey`
(`vzd-pointman`) and seat 1 = `daveey-1` (`vzd-crossfire`), both `is_filler: false`; the other six
seats are the two registered fillers with `is_filler: true`. The API's `participants` rows report
`policy_name`/`player_name` rather than the display name, but the replay's own `names` array (check
4) shows those six seats rendered as `Baseline`…`Baseline (6)`, which is what the checklist means.

---

## 4. Replay bytes are valid and show the game

The replay is the starter's **binary `COWLDVZD`** container, not raw JSON — first 64 bytes:

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/ca0f7fc8-967f-4de8-9b47-ba746186dd3c.replay" -o /tmp/ep.replay -w "http=%{http_code} bytes=%{size_download}\n"
http=200 bytes=106174
python3 -c "print(open('/tmp/ep.replay','rb').read()[:120])"
b'COWLDVZD\x01\x00\x12\x00vizdoom-deathmatch\x01\x001x\x85\x10F\xa0\x01\x00\x00\xd5\x06{"motionScale":256,…'
```

This is the **documented substitute** the design note declares for exactly this check —
`design.md:1096-1107`, "**The phase-60 substitute for SPEC §Definition of done check 4**": run the
repo's stdlib-only `tools/replay_summary.py`, which emits one strict-UTF-8 JSON object, and apply
the check-4 assertions to that. `design.md:1083-1089` gives the reason (the static wasm viewer
parses this container; CI sets `SMOKE_REQUIRE_REPLAY_JSON=0`). The tool was fetched read-only from
the coworld repo at HEAD:

```bash
gh api repos/Metta-AI/cogame-vizdoom-deathmatch/contents/tools/replay_summary.py --jq .content \
  | base64 -d > /tmp/replay_summary.py     # 196 lines
python3 /tmp/replay_summary.py /tmp/ep.replay > /tmp/ep.json   # exit 0
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok
jq -r '.protocol, .results.reason, .results.endRule, (.results.margin|tostring), (.results.frags|tostring)' /tmp/ep.json
vizdoom-deathmatch/v1
complete
full_time
4
[2,2,5,0,0,6,6,2]
```

`protocol` matches the manifest's `vizdoom-deathmatch/v1`; `results.reason == "complete"` — the
healthy value, so the design's declared-acceptable `deadline` exception (`design.md:342-347`) is
**not needed** this run. `sum(frags) = 23` — somebody shot somebody.

```bash
jq -r '([.directives[]|select(.source=="llm")]|length),
       ([.directives[]|select(.source=="scripted")]|length),
       ([.directives[]|select(.source=="fallback")]|length),
       (.fallbacks), (.radio|length), (.shouts|length), (.budgetGuards|length), (.stops|length)' /tmp/ep.json
48    # llm directives
144   # scripted directives
0     # fallback-sourced directives
0     # .fallbacks (fallback records)
48    # radio lines
18    # say shouts
0     # budget_guard records
0     # stop records
```

Full results document:

```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)","Baseline (5)","Baseline (6)"],
 "aliases":["RED-alpha","BLUE-alpha","RED-beta","BLUE-beta","RED-gamma","BLUE-gamma","RED-delta","BLUE-delta"],
 "team":["red","blue","red","blue","red","blue","red","blue"],
 "scores":[0.666,0.334,0.666,0.334,0.666,0.334,0.666,0.334],
 "win":[true,false,true,false,true,false,true,false],
 "reason":"complete","endRule":"full_time","games":1,
 "frags":[2,2,5,0,0,6,6,2],"teamFrags":[0,0,0,0,0,0,1,0],"deaths":[5,1,1,3,0,7,5,2],
 "net":[-3,1,4,-3,0,-1,0,0],"teamNet":[1,-3],"margin":4,
 "damageDealt":[10,6,15,5,0,19,20,7],"damageTaken":[16,5,3,11,0,22,17,8],
 "shotsFired":[21,6,23,13,0,33,33,18],"shotsHit":[10,6,16,5,0,19,20,7],
 "medkits":[0,0,0,0,0,0,0,1],"longestStreak":[1,1,5,0,0,1,1,1],"map":"arena",
 "policyKinds":["llm","llm","scripted","scripted","scripted","scripted","scripted","scripted"],
 "crossPlay":true,"llmTurns":[24,24,0,0,0,0,0,0],"fallbackTurns":[0,0,0,0,0,0,0,0],
 "ordersRejected":[1,0,0,0,0,0,0,0],"deadSeats":[false,false,false,false,false,false,false,false],
 "finalTick":2826,"seed":1183034456,"stopDetail":""}
```

Champion seats are non-scripted and non-trivial — `policyKinds[0..1] == ["llm","llm"]`,
`llmTurns[0..1] == [24,24]` (every one of the 24 turns decided by the model),
`fallbackTurns == [0,0,…]`, and the directives carry real intents, grid targets, radio and notes:

```
turn seat alias       source intent   at  radio
0    0    RED-alpha   llm    move_to  B2  "A2 hp3 no enemy contact yet"
0    1    BLUE-alpha  llm    flank    D2  "D2 killbox, facing W"
12   0    RED-alpha   llm    move_to      "B3 hp1 medkit -46/91 grab heal then hunt C3"
13   1    BLUE-alpha  llm    retreat      "E2 post compromised, regrouping"
14   0    RED-alpha   llm    hunt  BLUE-gamma "C3 hp3 hunting BLUE-gamma C2 hp1"
23   1    BLUE-alpha  llm    retreat      "D2 facing W, retreating hp1"
```

**Status: TRUE** — strict-UTF-8 JSON ok (via the design-declared `replay_summary.py` substitute),
`protocol == vizdoom-deathmatch/v1`, `results.reason == "complete"` / `endRule == "full_time"`,
23 frags, 48/48 champion decisions LLM-sourced and **zero** fallbacks (0 % of decisions, far below
"a small minority"). One `ordersRejected` on seat 0 out of 24 turns — a single order the sim
repaired/declined, not an LLM failure, and it did not become a fallback.

---

## 5. Hosted game log is clean

```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs.raw
http=200 bytes=102931
# decoded first (the body is python b'…' reprs per `===== container: … =====`, playbook §10)
python3 /tmp/declog.py /tmp/logs.raw > /tmp/logs.txt     # 324 lines, 0 decode failures
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.txt || echo CLEAN
CLEAN
# and on the raw, undecoded bytes exactly as the prompt writes it:
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.raw || echo CLEAN
CLEAN
```

Containers present: `coworld-init-config`, `bedrock-sidecar`, `game`, `worker`. Corroborating
tallies from the decoded text:

```bash
grep -o 'bedrock_[a-z_]*' /tmp/logs.txt | sort | uniq -c | sort -rn
    145 bedrock_sidecar
     48 bedrock_sidecar_usage
     48 bedrock_sidecar_complete
     48 bedrock_sidecar_call
      1 bedrock_sidecar_started
grep -o '"status_code":[0-9]*' /tmp/logs.txt | sort | uniq -c
     48 "status_code":200
grep -o '"ok":false' /tmp/logs.txt | wc -l
0
grep -c 'max_tokens' /tmp/logs.txt
0
```

48 Bedrock invocations, all `ok:true` / HTTP 200, matching the 48 LLM directives in the replay 1:1
— no retry, no truncation, no provider outage. Game container excerpt:

```
vizdoom-deathmatch config: host=0.0.0.0 port=8080 seed=1183034456 speed=1x minPlayers=8 slots=8 maxTicks=2592 maxGames=1 map=arena
vizdoom-deathmatch llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
player connected: daveey-1 … player connected: daveey … (8/8)
seat 0 registered: kind=llm baseline=rusher
seat 1 registered: kind=llm baseline=rusher
seat 2..7 registered: kind=scripted baseline=sentry|rusher
…
red win
game 1 done; hill red=0 blue=0; next regime resident
Replay written: /tmp/vizdoom-deathmatch-replay-1.bitreplay (106174 bytes)
Events written: /coworld/events.json (931 events, 208992 bytes)
Frame pacing: 2592 playing frames — skipped 2531 (97.6%), waited 12 (0.5%), late 49 (1.9%)
```

**Status: TRUE** — zero matches for all four patterns, on both the decoded and the raw body. No
documented exception was needed.

*Observation (not a check failure, for the coordinator/phase 30):* the game container prints
`game 1 done; hill red=0 blue=0` — inherited coworld-ctf hill wording in a deathmatch with no hill.
Log-only cosmetics; it appears nowhere in the replay, the results document or the viewer.

---

## 6. The public page uses the static replay path

*(a) Raw-HTML grep — finds nothing, which per the prompt is **unknown**, not a failure:*

```bash
curl -sS "https://softmax.com/vizdoom-deathmatch" -o /tmp/page3.html -w "http=%{http_code} bytes=%{size_download}\n"
http=200 bytes=716940
grep -o '<iframe[^>]*src="[^"]*"' /tmp/page3.html
(no match — the page is client-rendered, as playbooks/observatory-api.md §Featured match records
 platform-wide since the lighthouse run)
```

*(b) The `/coworlds` fallback — also uninformative, and documented as such:*

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -c '…|select(.name=="vizdoom-deathmatch")|{id,name,canonical,replay_viewer,featured_match}'
{"id":"cow_4e53e339-ec7c-4059-8e13-881aedbea5ba","name":"vizdoom-deathmatch","canonical":true,"replay_viewer":null,"featured_match":null}
```
`featured_match: null` here is platform-wide and not evidence (playbook §Featured match, lighthouse
run 2026-08-22).

*(c) **The source actually used** — the page's SSR payload for the featured match, and the call the
page's own JS makes for the iframe `src`:*

Featured match, from `state.playlist[0]` in the served HTML:

```json
"playlist":[{"episodeId":"ad47d164-9c4b-45f0-8b47-65d6cef43031",
 "coworldId":"cow_4e53e339-ec7c-4059-8e13-881aedbea5ba","coworldName":"vizdoom-deathmatch",
 "coworldVersion":"0.1.0",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/ca0f7fc8-967f-4de8-9b47-ba746186dd3c.replay",
 "finishedAt":"2026-08-28T02:09:01.819608Z","roundNumber":3,"episodeNumber":1,
 "code":"vizdoom-deathmatch.r3.e1",
 "matchup":{"divisionId":"div_67b01fa1-41ae-493c-8a1d-bb69f08bd83a","divisionName":"Competition",…
```

A featured match **is** present, and it is round 3 episode 1 — the very episode verified in checks
3–5.

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_4e53e339-ec7c-4059-8e13-881aedbea5ba",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/ca0f7fc8-967f-4de8-9b47-ba746186dd3c.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_4e53e339-ec7c-4059-8e13-881aedbea5ba/sha256%3A1cb9398bbcc252f2754c17d423c4fe3d8cbc0685ddf579f167db38ff338e04fa/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fca0f7fc8-967f-4de8-9b47-ba746186dd3c.replay",
  "ready": true
}
```

**Source used: (c)** — the SSR payload for the featured match plus `POST /coworlds/replays/session`
for the `src`, because (a) is empty platform-wide and (b) returns `null`.

**Status: TRUE** — the `src` is the **static** route
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html`, with `<sha>` the coworld's manifest hash
`sha256:1cb9398bbcc252f2754c17d423c4fe3d8cbc0685ddf579f167db38ff338e04fa` (URL-encoded), exactly
matching `STATE.coworld.manifest_sha`; `ready: true`; **no `/client/replay` pod URL anywhere**. A
featured match is present.

*Recorded difference from the prompt's literal shape:* the platform now hands back the replay as a
**fragment** (`index.html?v=2#replay=<url-encoded s3 url>`) rather than the query form
`index.html?replay=<s3 url>`. Path, host, `<cow_id>` and `<sha>` are the required static route and
`ready:true` is the playbook's stated static-delivery signal; the fragment is how the platform's own
page loads it, and check 8 proves that exact URL renders. Not a `/client/replay` variant.

---

## 7. Certification declared the static bundle

Source read: **`runs/2026-08-27-vizdoom-deathmatch/release-result.json`, the copy phase 40
committed** (not re-downloaded; the file was present, so the `gh run download` fallback was not
needed).

```bash
jq -r '.certify.replay_liveness' runs/2026-08-27-vizdoom-deathmatch/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

**Status: TRUE** — contains `Replay liveness: skipped (static replay bundle declared`.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged

*(a) Dispatch.* The `url` input is the check-6 iframe `src` verbatim, fragment and all.

```bash
SRC="$(jq -r .viewer_url /tmp/session.json)"
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90   # 02:10:48Z
sleep 12
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -c 'sort_by(.createdAt)|reverse|.[0:3][]'
{"createdAt":"2026-08-28T02:10:50Z","databaseId":33135119698,"status":"in_progress"}
{"createdAt":"2026-08-27T21:38:31Z","databaseId":33119081304,"status":"completed"}
{"createdAt":"2026-08-27T20:36:49Z","databaseId":33114175789,"status":"completed"}
```
The newest run before the dispatch was created 2026-08-27T21:38:31Z, so **33135119698**
(created 02:10:50Z, two seconds after the dispatch) is unambiguously this run's — not "the latest"
taken blind.

```bash
gh run watch 33135119698 -R Metta-AI/coworld-builder --exit-status
✓ viewer-check in 40s (ID 98733251490) — all steps ✓, including "Fail if the viewer did not load"
gh run view 33135119698 -R Metta-AI/coworld-builder --json status,conclusion,createdAt,url
{"conclusion":"success","createdAt":"2026-08-28T02:10:50Z","status":"completed",
 "url":"https://github.com/Metta-AI/coworld-builder/actions/runs/33135119698"}
gh run download 33135119698 -R Metta-AI/coworld-builder -n viewer-check \
  -D runs/2026-08-27-vizdoom-deathmatch/viewer-check
# viewer-smoke.json (1687 B), viewer-smoke.png (793 795 B), smoke-stdout.txt, smoke-stderr.txt (0 B)
```

*(b) Readouts, verbatim.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/…/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":3551,"clock":"tick 0/2592 · turn 1/24 RED 0 FRAGS 0 DEATHS · BLUE 0 FRAGS 0 DEATHS 0 — 0 · MARGIN 0","scorebug":"0 DAVEEY + BASELINE FRAGS 0 0 DEATHS · 4 UP tick 0/2592 · turn 1/24 RED 0 FRAGS 0 DEATHS · BLUE 0 FRAGS 0 DEATHS 0 — 0 · MARGIN 0 0 DAVEEY-1 + BASELINE FRAGS 0 0 DEATHS · 4 UP","feed_lines":0}
```

```bash
jq -c '.signals' runs/…/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/…/viewer-check/viewer-smoke.json
no failure
jq -c '.canvas_text' runs/…/viewer-check/viewer-smoke.json
{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
# ("0 drawn" = the text-bounds probe saw no 2-D canvas fillText — this shell draws its captions as
#  DOM chips, which is why the screenshot's labels are crisp and none are reported never-inside.)
```

**The three clock readouts** (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub | clock readout |
|---|---|
| 0 % | `tick 0/2592 · turn 1/24 RED 0 FRAGS 0 DEATHS · BLUE 0 FRAGS 0 DEATHS 0 — 0 · MARGIN 0` |
| 50 % | `tick 966/2592 · turn 9/24 RED 6 FRAGS 4 DEATHS · BLUE 4 FRAGS 6 DEATHS 2 — -2 · MARGIN +4` |
| 100 % | `tick 1446/2592 · turn 14/24 RED 8 FRAGS 7 DEATHS · BLUE 7 FRAGS 8 DEATHS 1 — -1 · MARGIN +2` |

All three differ and advance monotonically (tick 0 → 966 → 1446; turn 1 → 9 → 14; frags 0/0 → 6/4
→ 8/7). `has_scrub` was true — the shell **does** expose `#scrub`.

**Status: TRUE** — `loaded: true` (`data-replay-loaded="true"`, first frame at 3 551 ms) **and**
the three clock readouts differ.

*(c) The replay JSON the viewer was asked to draw* (from `/tmp/ep.replay` via `replay_summary.py`,
ordered early / middle / late):

```
turn seat alias       source  intent   at/target      radio
--- early ---
0    0    RED-alpha   llm     move_to  B2             A2 hp3 no enemy contact yet
0    1    BLUE-alpha  llm     flank    D2             D2 killbox, facing W
0    2    RED-beta    scripted hold    B1
0    4    RED-gamma   scripted hold    A1
1    0    RED-alpha   llm     move_to  C2             row 2 mid B2 hp3 last enemy D2
1    1    BLUE-alpha  llm     hold     D2             D2 facing W - hold corridor killbox
--- middle (the turn the screenshot is showing) ---
13   0    RED-alpha   llm     move_to  C3             B3 hp3 moving to C3 for wounded
13   1    BLUE-alpha  llm     retreat                 E2 post compromised, regrouping
13   4    RED-gamma   scripted hold    A1
13   5    BLUE-gamma  scripted hunt    RED-delta
13   6    RED-delta   scripted hunt    BLUE-gamma
13   7    BLUE-delta  scripted hunt    RED-delta
14   0    RED-alpha   llm     hunt     BLUE-gamma     C3 hp3 hunting BLUE-gamma C2 hp1
14   1    BLUE-alpha  llm     retreat                 E2 post critical hp=1 retreating to spawn
--- late ---
23   0    RED-alpha   llm     hunt     RED-delta      B2, hp3. Delta at C2 hp1 - hunting to support. BLUE-alpha last seen E2.
23   1    BLUE-alpha  llm     retreat                 D2 facing W, retreating hp1
23   6    RED-delta   scripted move_to C3
23   7    BLUE-delta  scripted hold    D3
```
`results` for the same episode is pasted in full in check 4 (`reason complete`, `margin 4`,
frags `[2,2,5,0,0,6,6,2]`).

### Spectator judgment

**It is legible, it is moving, and it is unmistakably this game.** The rendered frame
(`viewer-check/viewer-smoke.png`, 1280×800, captured at tick 1446/2592, turn 14/24) shows a top-down
lit arena — grey tiled floor, brown crate cover, chevron walls, two dark ritual discs at either end,
a white med-kit box mid-map — with red and blue cogs spread across it, orange tracer lines drawn
from firing cogs to their targets, and small speech bubbles reading "on it" over several of them.
Across the top: a per-seat card strip, eight cards, red/blue tinted with the alias truncated
(`RED-A…`, `BLUE-…`), one card dimmed — the seat that is out at that tick. The headline
reads `tick 1446 / 2592 · turn 14/24`, flanked by the scorebug — `8 FRAGS DAVEEY + BASELINE / 7
DEATHS · 3 UP` on the left with a `+1` chip, `DAVEEY-1 + BASELINE FRAGS 7 / 8 DEATHS · 4 UP` on the
right with a `-1` chip, and `RED 8 FRAGS 7 DEATHS · BLUE 7 FRAGS 8 DEATHS · 1 — -1 · MARGIN +2`
underneath. A spectator can tell who is winning, by how much, and how long is left, from the top
strip alone. Bottom right runs the order/kill feed: `RED-gamma: HOLD A1`, `BLUE-gamma: HUNT
RED-DELTA`, `RED-delta: HUNT BLUE-GAMMA`, `BLUE-delta: HUNT RED-DELTA` — **which is exactly turn
13's scripted directive block in the replay JSON above, seat for seat**. The picture and the record
agree.

Nothing is empty, frozen or unreadable. The clock advanced across three seeks (0 → 966 → 1446) and
the scorebug advanced with it (0/0 → 6/4 → 8/7 frags), tracking the same fight the replay records:
23 frags, `margin 4`, red wins on `full_time`.

**Does it look like the starter's chrome?** Yes — it is coworld-ctf/paintbot chrome, retargeted, not
a rewrite that reuses the ids (the cogame-gridlock failure). Button for button, the transport strip
in the screenshot is the starter's `#transport` `.tbar` from
`starters/coworld-ctf/client/replay_broadcast.html:1553-1568`: `⟲ ◂| ▶ +5s |▸ ↻ ▸▸ spoilers`, then
the tick-clock chip reading `1446 / 2592`, then the speed chips `1× 2× 3× 4× 8× 16×` — same order,
same glyphs, same right-aligned speed row. Below it is the starter's `#scrub` with the momentum
graph underneath the seek track on the same axis and the amber playhead crossing both; the momentum
label is the starter's `LIVES LEAD` slot retargeted to **`FRAG LEAD`**, and the graph shows the red
lead swelling and receding across the episode. `#scorebug` and `#clock` are the starter's ids and
the smoke read them by those names. This is the inherited chrome with the game's own block
appended, as `design.md` §Chrome provenance describes.

*Three observations for the coordinator (none affects a verdict):*

1. **`feed_lines: 0` is a probe artefact, not an empty feed.** `templates/tools/ci/viewer_smoke.mjs:425`
   counts `#feed, .feed, #log`; this shell inherits the starter's id **`#killfeed`**
   (`starters/coworld-ctf/client/replay_broadcast.html:1551`), which that selector does not match.
   The screenshot shows four populated feed lines, and they reconcile line-for-line with the replay's
   turn-13 records. Worth widening the smoke selector so a future run does not read this as silence.
2. **The 100 % scrub click landed at tick 1446 (56 %), not at the end.** Both seek clicks
   under-shot (50 % → tick 966 = 37 %; 100 % → tick 1446 = 56 %), so the endcard was never on screen
   in this capture and I make no claim about it. I did not diagnose the cause and will not guess at
   one; the fact stands as recorded. Motion — the thing check 8 tests — is proven regardless: three
   differing, monotonically advancing readouts.
3. *(Replay content, phase-30 flavour note)* at turn 23 the LLM seat `RED-alpha` issues
   `intent: hunt, target: RED-delta` — a **friendly** alias — with the radio line "Delta at C2 hp1 -
   hunting to support". The sim accepted it as a move-toward, so it is at worst a verb that reads
   oddly in the feed, not a rules violation.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 2 and 3 `completed`; round 1 `failed` (pre-filler, superseded) |
| 2 | Both champions ranked, fillers absent | **TRUE** — daveey #1 / daveey-1 #2, `rounds_played` 2 each; no filler rows |
| 3 | Latest round's episode request completed with a replay | **TRUE** — `ereq_c9f0e294…` completed, `replay_url` set, both champions seated |
| 4 | Replay bytes valid and show the game | **TRUE** — `vizdoom-deathmatch/v1`, `reason complete`, 23 frags, 48 LLM decisions, 0 fallbacks |
| 5 | Hosted game log clean | **TRUE** — zero matches, decoded and raw; 48/48 Bedrock calls HTTP 200 |
| 6 | Public page uses the static replay path | **TRUE** — static `…/replays/static/<cow_id>/<manifest sha>/index.html`, `ready:true`, featured match r3.e1 |
| 7 | Certification declared the static bundle | **TRUE** — `Replay liveness: skipped (static replay bundle declared…` from committed `release-result.json` |
| 8 | Viewer executed and judged | **TRUE** — `loaded:true` at 3 551 ms, three differing clock readouts, starter chrome, legible |
