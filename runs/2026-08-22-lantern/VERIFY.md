# VERIFY — lantern   (2026-08-23T04:00Z)

Verdict: **all-true** (8/8)

Run `2026-08-22-lantern` · coworld `lantern` v0.1.4 · `cow_d1fe527f-ee07-42ff-804d-f40be734d05f`
· league `league_16893be5-934d-43b4-9155-d27f600ffffe` · division `div_af46a8ef-67ec-4780-9c72-0cf70e260999`

Every fetch below was made fresh in this phase-60 session between 2026-08-23T03:38Z and
2026-08-23T03:59Z. The one documented exception is **check 7**, whose evidence is the committed
artifact `runs/2026-08-22-lantern/release-result.json` (see that section).

Shell setup used throughout (header **values** never printed):

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_16893be5-934d-43b4-9155-d27f600ffffe
D=div_af46a8ef-67ec-4780-9c72-0cf70e260999
COW=cow_d1fe527f-ee07-42ff-804d-f40be734d05f
```

Polling record (checks 1 and 3, 5-minute cadence, 75-minute bound; bound consumed: 18 min):

| UTC | completed rounds | note |
|---|---|---|
| 03:38:55 | 1 (round 2) | round 1 `failed`, round 3 not yet created |
| 03:41:00 | 1 | unchanged |
| 03:46:02 | 1 | unchanged |
| 03:50:55 | 1 | unchanged |
| 03:55:49 | **2** (rounds 2, 3) | round 3 created 03:51:27Z, completed 03:53:40Z — bound satisfied |

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

Summary: rounds **2** and **3** are `completed`; both have `round_number ≥ 2`, i.e. after the
fillers were registered. Round 1 `failed` and does not count; its `error` is recorded verbatim
below.

Fillers, fetched now, confirming exactly the two scripted baselines are registered as fillers and
neither champion version is among them:

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"72a889c0-d72d-4b51-ae07-2cdad871e72c","policy_id":"1fec9d7b-acc4-4fed-a9e0-a7419d702c3d","policy_name":"lantern-warden","version":3,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},
 {"policy_version_id":"713f2616-34a3-44d3-8f6a-321a50d861c0","policy_id":"6607a418-4f90-43f4-b008-f8c753526257","policy_name":"lantern-moth","version":3,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
HTTP 200
```
(Without `${ELEV[@]}` this route answers `403 {"detail":"User is not a softmax team member"}` — a
header problem, not a permissions one, per `playbooks/observatory-api.md`.)

Rounds:

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq '{entries:[.entries[]|{id,round_number,status,error,scheduled_by,completed_at,created_at,
        entrants:.round_config.entrant_policy_version_ids}]}'
```
```json
{
  "entries": [
    {
      "id": "round_b878a6b2-fa79-4fe1-a015-d6c0f7ac23ae",
      "round_number": 3,
      "status": "completed",
      "error": null,
      "scheduled_by": "ladder",
      "completed_at": "2026-08-23T03:53:40.005219Z",
      "created_at": "2026-08-23T03:51:27.544977Z",
      "entrants": [
        "fe561309-94c9-4101-ac0b-b3511a4836f3",
        "c380d98e-b016-413c-9f8b-360b16ddf752"
      ]
    },
    {
      "id": "round_93bc2d0b-7454-41e2-8be6-4612d6b61b70",
      "round_number": 2,
      "status": "completed",
      "error": null,
      "scheduled_by": "ladder",
      "completed_at": "2026-08-23T03:38:19.574237Z",
      "created_at": "2026-08-23T03:36:27.148048Z",
      "entrants": [
        "fe561309-94c9-4101-ac0b-b3511a4836f3",
        "c380d98e-b016-413c-9f8b-360b16ddf752"
      ]
    },
    {
      "id": "round_6d1bfa16-3352-4068-b51a-bccab886e1f2",
      "round_number": 1,
      "status": "failed",
      "error": "Temporal RoundWorkflow failed before settling the round.",
      "scheduled_by": "ladder",
      "completed_at": "2026-08-23T03:36:02.058602Z",
      "created_at": "2026-08-23T03:36:01.842067Z",
      "entrants": [
        "fe561309-94c9-4101-ac0b-b3511a4836f3"
      ]
    }
  ]
}
```
```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '[.entries[]|select(.status=="completed")]|length'
```
```
2
```

Round 1's verbatim error: `Temporal RoundWorkflow failed before settling the round.` — the known
"trigger-round issued before any filler exists" failure (`playbooks/observatory-api.md` §6); it is
excluded, and its single-entrant `entrant_policy_version_ids` (`fe561309…` only) matches that
cause. Rounds 2 and 3 both seat both champion versions and, per check 3, four filler seats — direct
evidence the fillers were in force for both counted rounds.

Status: **TRUE** — completed rounds `round_93bc2d0b-7454-41e2-8be6-4612d6b61b70` (#2, completed
2026-08-23T03:38:19Z) and `round_b878a6b2-fa79-4fe1-a015-d6c0f7ac23ae` (#3, completed
2026-08-23T03:53:40Z), both `round_number ≥ 2` and therefore after filler registration.

---

## 2. Both champions ranked; fillers absent/Baseline — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq .
```
```json
[
  {
    "rank": 1,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 1030.5304984710244,
    "score_label": "Elo",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 2.0,
    "episodes_played": null,
    "win_rate": 1.0,
    "policy_label": "lantern-warren:v3",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 969.4695015289755,
    "score_label": "Elo",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 0.0,
    "episodes_played": null,
    "win_rate": 0.0,
    "policy_label": "lantern-owlnight:v3",
    "recent_rounds": null
  }
]
```
```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end
          | .[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey	lantern-warren:v3	1030.5304984710244	2	2.0
2	daveey-1	lantern-owlnight:v3	969.4695015289755	2	0.0
```

Status: **TRUE** — `daveey` (`lantern-warren:v3`, rank 1, rounds_played 2) and `daveey-1`
(`lantern-owlnight:v3`, rank 2, rounds_played 2) are both ranked with `rounds_played ≥ 1`. The
leaderboard has exactly two rows: the fillers `lantern-warden:v3` / `lantern-moth:v3` are **absent**
(they are unranked filler seats, renamed `Baseline (N)` inside the episode — see check 4's
`results.names`).

---

## 3. Latest completed round's episode request completed with a replay — **TRUE**

```bash
R=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
    | jq -r '[.entries[]|select(.status=="completed")]|max_by(.round_number).id')
# R = round_b878a6b2-fa79-4fe1-a015-d6c0f7ac23ae   (round_number 3)
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}" \
 | jq '[.entries[]|{id,status,replay_url}]'
```
```json
[
  {
    "id": "ereq_d3790a64-847e-4954-8373-30ace92e84de",
    "status": "completed",
    "replay_url": "https://softmax-public.s3.amazonaws.com/replays/eb43b47f-b765-4820-a0ca-9e8077f26200.replay"
  }
]
```
```bash
EREQ=ereq_d3790a64-847e-4954-8373-30ace92e84de
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url,
        participants:[.participants[]|{position,policy_name,version,player_name,is_filler}],
        participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/eb43b47f-b765-4820-a0ca-9e8077f26200.replay",
  "participants": [
    {"position": 0, "policy_name": "lantern-warren",   "version": 3, "player_name": "daveey",   "is_filler": false},
    {"position": 1, "policy_name": "lantern-owlnight", "version": 3, "player_name": "daveey-1", "is_filler": false},
    {"position": 2, "policy_name": "lantern-warden",   "version": 3, "player_name": "daveey",   "is_filler": true},
    {"position": 3, "policy_name": "lantern-warden",   "version": 3, "player_name": "daveey",   "is_filler": true},
    {"position": 4, "policy_name": "lantern-warden",   "version": 3, "player_name": "daveey",   "is_filler": true},
    {"position": 5, "policy_name": "lantern-moth",     "version": 3, "player_name": "daveey",   "is_filler": true}
  ],
  "participant_scores": [
    {"position": 0, "score": 0.693},
    {"position": 1, "score": 0.307},
    {"position": 2, "score": 0.693},
    {"position": 3, "score": 0.307},
    {"position": 4, "score": 0.693},
    {"position": 5, "score": 0.307}
  ]
}
```

Status: **TRUE** — `ereq_d3790a64-847e-4954-8373-30ace92e84de` is `completed`, carries a non-null
`replay_url`, seats champion #1 (`daveey` / `lantern-warren:v3`) at position 0 and champion #2
(`daveey-1` / `lantern-owlnight:v3`) at position 1, and fills positions 2–5 with `is_filler: true`
scripted baselines (spectator-side they render as `Baseline`…`Baseline (4)` — see check 4's
`results.names`). Scores are exactly zero-sum by side (0.693 / 0.307), as the design's scoring rule
requires.

---

## 4. Replay bytes are valid and show the game — **TRUE**

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/eb43b47f-b765-4820-a0ca-9e8077f26200.replay" \
     -o /tmp/ep.replay -w 'HTTP %{http_code} bytes %{size_download} type %{content_type}\n'
```
```
HTTP 200 bytes 313685 type application/octet-stream
```
```bash
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .results.reason' /tmp/ep.replay
```
```
strict UTF-8 JSON: ok
lantern.replay.v1
complete
```

Protocol match against the manifest (fetched now, not remembered):

```bash
curl -sS "$BASE/coworlds/$COW" "${AUTH[@]}" -o /tmp/cow.json
jq -r '.name, .version, .manifest_hash' /tmp/cow.json
jq -r '..|strings|select(test("lantern\\.replay\\.v1"))' /tmp/cow.json \
 | grep -o '.\{60\}lantern\.replay\.v1.\{60\}' | head -1
jq -c '..|objects|select(.properties?.reason?)|.properties.reason' /tmp/cow.json | head -1
```
```
lantern
0.1.4
sha256:891128215115bf6b75a1e51bd0299ba909b4b7595fbcd30d615ffe454af286f4
eplay bytes themselves are strict UTF-8 JSON with protocol "lantern.replay.v1": config, the map inlined verbatim, names/aliases/teams/pol
{"enum":["complete","deadline","fault"],"type":"string","description":"Why the episode ended."}
```
The manifest hash matches STATE's `manifest_sha`, the manifest declares protocol
`lantern.replay.v1`, and the replay's `protocol` is exactly that. `results.reason` is `complete`
(not `deadline`, so **no documented exception is being relied on**).

**Adapted decision counting.** The prompt's generic lines select `.type=="decision"` and
`.fallback==true`; lantern's replay vocabulary uses `order` events with a `source` field and
separate `fallback` events with a `cause`. Adapted commands and their output:

```bash
jq -r '[.events[].type]|group_by(.)|map({t:.[0],n:length})|sort_by(-.n)[]|"\(.n)\t\(.t)"' /tmp/ep.replay
```
```
368	sound
156	order
56	crate_push
42	turn_start
9	crate_pry
6	crate_lock
6	spot
5	found
4	act_end
4	act_start
3	crate_break
2	half_start
1	end
1	half_end
1	match_start
```
```bash
jq -r '[.events[]|select(.type=="order")]|group_by(.seat)[]
       |{seat:.[0].seat,alias:.[0].alias,total:length,
         by_source:(group_by(.source)|map({(.[0].source):length})|add)}|tostring' /tmp/ep.replay
jq -r '[.events[]|select(.type=="fallback")]|length' /tmp/ep.replay
jq -c '.results.policy_kinds, .results.names, .results.llm_turns, .results.fallback_turns' /tmp/ep.replay
```
```
{"seat":0,"alias":"Moth-1","total":28,"by_source":{"llm":28}}
{"seat":1,"alias":"Owl-1","total":29,"by_source":{"llm":29}}
{"seat":2,"alias":"Moth-2","total":19,"by_source":{"scripted":19}}
{"seat":3,"alias":"Owl-2","total":25,"by_source":{"scripted":25}}
{"seat":4,"alias":"Moth-3","total":29,"by_source":{"scripted":29}}
{"seat":5,"alias":"Owl-3","total":26,"by_source":{"scripted":26}}
0
["llm","llm","scripted","scripted","scripted","scripted"]
["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"]
[28,29,0,0,0,0]
[0,0,0,0,0,0]
```

The champion seats are the two whose `results.policy_kinds[seat] == "llm"` — seat 0 (`daveey`,
Moth-1) and seat 1 (`daveey-1`, Owl-1). **28/28 and 29/29 of their orders are `source:"llm"`**;
there are **zero** `fallback` events in the whole episode and `results.fallback_turns` is all zeros
with every `fallback_causes` bucket at 0. Not a minority of fallbacks — none.

Non-trivial content, sampled across the episode (orders 1, 6, 13, 21, 31, 41, last of the two
champion seats; `note` truncated to 110 chars for width):

```bash
jq -r '[.events[]|select(.type=="order" and (.seat==0 or .seat==1))]
       |[.[0],.[5],.[12],.[20],.[30],.[40],.[-1]]|.[]
       |[.t,.seat,.alias,.source,.intent,((.note//"")|.[0:110]),(.say//"")]|@tsv' /tmp/ep.replay
```
```
0	0	Moth-1	llm	push	BUILD phase: Push C0 toward left nook at [240,329]. I spawn at [150,110], C0 is at [150,329] - nearest loose c	Building left warren
600	0	Moth-1	llm	hide	Hunt phase: stationary in left alcove behind locked C2. Crawl mode suppresses footsteps. Invisible to sweeping	Silent in the warren
1080	0	Moth-1	llm	hide	Hunt order 5: remain motionless in left alcove behind locked C2. No beams or seekers detected. Stillness and o	Silent and still
1560	0	Moth-1	llm	hide	Hunt order 13: remain motionless in left alcove behind locked C2. No beams on me. Moth-2 found but I stay stil	Holding position
2160	0	Moth-1	llm	hide	Hunt order 18: remain motionless in left alcove behind locked C2. No beams in sector. Heartbeat cold. Moth-2 f	Holding
3120	1	Owl-1	llm	hide	BUILD phase ending. C8 locked at center splits floor. Holding position against left outer wall behind pillar (	Screen set. Waiting for hunt.
4080	1	Owl-1	llm	flee	Beam bearing 249 (west-southwest) is near. I'm at 120,427 near west wall. Fleeing perpendicular to cone (north	Fleeing perpendicular to beam.
```

Status: **TRUE** — 313,685 bytes of strict-UTF-8 JSON (`jq -e` clean); `protocol` =
`lantern.replay.v1` = the manifest's declared protocol; `results.reason` = `complete` /
`end_rule` = `full_time`; champion seats' orders are 100 % `source:"llm"` with substantive,
situation-specific `intent`/`note`/`say`; fallback events = 0.

---

## 5. Hosted game log is clean — **TRUE**

```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs.txt \
  -w 'HTTP %{http_code} bytes %{size_download}\n'
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.txt || echo CLEAN
```
```
HTTP 200 bytes 118926
CLEAN
```

The artifact returns each container's stream as a Python `b'…'` repr, so the raw grep sees escaped
newlines. Re-run against a decoded copy, so the CLEAN verdict cannot be an artefact of line
splitting:

```bash
python3 - <<'EOF'   # decode each "===== container: X =====" b'…' block to /tmp/logs_decoded.txt
… (eval of each repr block, joined) …
EOF
grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs_decoded.txt
```
```
0
```

Containers present and their content (proof the right log was read, and that the LLM path really
ran):

```bash
grep -o '===== container: [a-z-]* =====' /tmp/logs.txt
grep -o 'HTTP/1.1 [0-9]* [A-Za-z ]*' /tmp/logs_decoded.txt | sort | uniq -c
grep -o 'bedrock_sidecar_[a-z]*'      /tmp/logs_decoded.txt | sort | uniq -c
```
```
===== container: coworld-init-config =====
===== container: bedrock-sidecar =====
===== container: game =====
===== container: worker =====

     57 HTTP/1.1 200 OK

     57 bedrock_sidecar_call
     57 bedrock_sidecar_complete
      1 bedrock_sidecar_started
     57 bedrock_sidecar_usage
```

57 Bedrock invocations, **all HTTP 200**, zero non-200 — and 57 = 28 + 29, exactly the champion
seats' LLM order count from check 4. Full `game` container log (26 lines, decoded):

```
lantern: seed not pinned; randomised to 576006832
lantern: seats=6 seed=576006832 map=vault ticks=5040 turnTicks=120 wallClockBudget=660s
lantern: serving on 0.0.0.0:8080
lantern: player slot 3 connected (1/6)
lantern: player slot 5 connected (2/6)
lantern: slot 3 registered (scripted, 0 prompt chars)
lantern: slot 5 registered (scripted, 0 prompt chars)
lantern: slot 5 registered (scripted, 0 prompt chars)
lantern: slot 3 registered (scripted, 0 prompt chars)
lantern: player slot 1 connected (3/6)
lantern: slot 1 registered (llm, 1419 prompt chars)
lantern: player slot 0 connected (4/6)
lantern: slot 0 registered (llm, 1606 prompt chars)
lantern: player slot 2 connected (5/6)
lantern: slot 2 registered (scripted, 0 prompt chars)
lantern: slot 0 registered (llm, 1606 prompt chars)
lantern: slot 1 registered (llm, 1419 prompt chars)
lantern: slot 2 registered (scripted, 0 prompt chars)
lantern: player slot 4 connected (6/6)
lantern: slot 4 registered (scripted, 0 prompt chars)
lantern: slot 4 registered (scripted, 0 prompt chars)
lantern: starting with 6/6 players connected
lantern llm: bedrock transport, url http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
lantern: writing replay and results (complete/full_time)
lantern: episode complete; serving for 20s more so a late spectator or a certification ping still finds the socket alive
lantern: shutting down
```

Status: **TRUE** — zero matches for `falling back|LLM provider is unavailable|cut off at
max_tokens|rejected` in both the raw and the decoded artifact; 6/6 seats connected, both champion
seats registered `llm` with real prompt bodies (1606 and 1419 chars), 57/57 Bedrock calls 200,
clean shutdown after `complete/full_time`. No documented exception invoked.

---

## 6. The public page uses the static replay path — **TRUE**

**Source 1 — raw HTML grep (as the prompt's first command):**

```bash
curl -sS "https://softmax.com/lantern" -o /tmp/page.html -w 'HTTP %{http_code} bytes %{size_download}\n'
grep -o '<iframe[^>]*src="[^"]*"' /tmp/page.html || echo "(no match)"
```
```
HTTP 200 bytes 343808
(no match)
```
Not a false negative: the page is client-rendered for the iframe (`prompts/60-verify.md` §6 and
`playbooks/observatory-api.md` §Featured match / replay route, answered by the lighthouse run
2026-08-22). Treated as *unknown*, and the two documented fallbacks were used.

**Source 2 — the SSR payload's featured match (`state.playlist[0]`), from the same fetched HTML:**

```bash
python3 -c "h=open('/tmp/page.html').read(); i=h.find('playlist\\\\\":['); print(h[i:i+700].replace('\\\\\"','\"'))"
```
```
playlist":[{"episodeId":"604d4282-5cd8-4240-8fa5-1c0bf2efd76a","coworldId":"cow_d1fe527f-ee07-42ff-804d-f40be734d05f","coworldName":"lantern","coworldVersion":"0.1.4","replayUrl":"https://softmax-public.s3.amazonaws.com/replays/eb43b47f-b765-4820-a0ca-9e8077f26200.replay","finishedAt":"2026-08-23T03:53:31.728934Z","roundNumber":3,"episodeNumber":1,"code":"lantern.r3.e1","matchup":{"divisionId":"div_af46a8ef-67ec-4780-9c72-0cf70e260999","divisionName":"Competition","first":{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1030.5304984710244,"score_label":"Elo","score_value_type":"inte
```
A featured match **is present**: `lantern.r3.e1`, the round-3 episode verified in checks 3–5, with
a two-player matchup (`daveey` rank 1 vs `daveey-1` rank 2) — so the "fewer than two ranked players"
failure mode does not apply.

**Coworld detail API (the prompt's named fallback), for the record:**

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)[]|select(.name=="lantern")
          |{id,name,version,canonical,replay_viewer,featured_match,manifest_hash}'
```
```json
{"id":"cow_d1fe527f-ee07-42ff-804d-f40be734d05f","name":"lantern","version":"0.1.4","canonical":true,
 "replay_viewer":null,"featured_match":null,
 "manifest_hash":"sha256:891128215115bf6b75a1e51bd0299ba909b4b7595fbcd30d615ffe454af286f4"}
{"id":"cow_9390a66a-5619-4c05-9edb-cd3443abb411","name":"lantern","version":"0.1.3","canonical":false,…}
{"id":"cow_070b461c-123f-4ecd-9ae1-56150ea8ff00","name":"lantern","version":"0.1.2","canonical":false,…}
```
`canonical:true` on 0.1.4 with the expected `manifest_hash`. `featured_match` is `null` here, which
is the documented **platform-wide** behaviour of this field (null for every coworld) and therefore
not evidence either way — the featured match is in the SSR payload above.

**Source 3 — the iframe `src` the page's own JS obtains (the authoritative one):**

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
 -d '{"coworld_id":"cow_d1fe527f-ee07-42ff-804d-f40be734d05f",
      "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/eb43b47f-b765-4820-a0ca-9e8077f26200.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_d1fe527f-ee07-42ff-804d-f40be734d05f/sha256%3A891128215115bf6b75a1e51bd0299ba909b4b7595fbcd30d615ffe454af286f4/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Feb43b47f-b765-4820-a0ca-9e8077f26200.replay&v=2",
  "ready": true
}
```

The path is `/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` with
`<cow_id>` = `cow_d1fe527f-ee07-42ff-804d-f40be734d05f` and `<sha>` = the coworld **manifest_hash**
`sha256:8911282…` URL-encoded as `sha256%3A891128215115bf6b75a1e51bd0299ba909b4b7595fbcd30d615ffe454af286f4`
(the documented lighthouse gotcha: it is the manifest hash, **not** the replay-viewer bundle digest
`sha256:1e62195a…`). `ready: true`. There is **no** `/client/replay` pod URL anywhere in the
response.

**Which URL form serves it** — the working host is `api.observatory.softmax-research.net`; the
`softmax.com/api/observatory` proxy 404s that static path platform-wide (control fetch, this run):

```bash
curl -sS "https://softmax.com/api/observatory/v2/coworlds/replays/static/$COW/sha256%3A8911282…/index.html" \
  -w '\nproxy index.html %{http_code} %{size_download}\n' | tail -3
```
```
{"detail":"Replay viewer shell not found"}
proxy index.html 404 42
```

Status: **TRUE** — sources used: (i) raw-HTML grep → no match (page client-rendered, treated as
unknown), (ii) the page's SSR `state.playlist[0]` → featured match `lantern.r3.e1` present,
(iii) `POST /coworlds/replays/session` → static `index.html` viewer URL with `ready:true`. Verified
URL form: `https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_d1fe527f-ee07-42ff-804d-f40be734d05f/sha256%3A891128215115bf6b75a1e51bd0299ba909b4b7595fbcd30d615ffe454af286f4/index.html?replay=…`. **Static confirmed; no `/client/replay` pod URL.**

---

## 7. Certification declared the static bundle — **TRUE**

Source read: the **committed** artifact `runs/2026-08-22-lantern/release-result.json` (present in
the run directory; no `gh run download` was needed, and `/tmp` was not consulted).

```bash
jq -r '.certify.replay_liveness' runs/2026-08-22-lantern/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Surrounding certification output from the same file (`.certify.ok` and the transcript tail):

```bash
jq -r '.certify.ok' runs/2026-08-22-lantern/release-result.json
jq -r '.certify.output_tail' runs/2026-08-22-lantern/release-result.json
```
```
true

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
…
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```
(`[run ]` lines elided for width; every step's `[pass]` line is pasted verbatim.)

Status: **TRUE** — the certification output contains
`Replay liveness: skipped (static replay bundle declared`, read from the committed
`runs/2026-08-22-lantern/release-result.json` (release run `32615340953`), with all 10 transcript
steps passed and `certify.ok: true`.

---

## 8. Spectator judgment — **TRUE** (fetched, not rendered)

The sandbox has no screen and no headless browser. Nothing below is read from a DOM, a render or a
screenshot; all three legs are `curl`/`jq` fetches made this run.

### 8(a) The replay JSON — what the viewer would draw

Adapted excerpt command (lantern uses `t`/`seat`/`type` with `intent`/`say`/`cause`, not
`tick`/`summary`/`action`); `sound` rings are the highest-count event type and are filtered out of
the ordered excerpts so the game beats are legible:

```bash
jq -r '.events[]|[.t,(.seat//""),.type,(.intent//.say//.cause//"")]|@tsv' /tmp/ep.replay | head -40
```
```
0		match_start	
0		half_start	
0		act_start	
0		turn_start	
0	0	order	push
0	2	order	push
0	4	order	push
4		sound	
4		sound	
4		sound	
28		sound	
28		sound	
28		sound	
52		sound	
52		sound	
52		sound	
76		sound	
76		sound	
76		sound	
85	0	crate_push	
85		sound	
89	4	crate_push	
89		sound	
97	0	crate_push	
97		sound	
100		sound	
101		sound	
102	2	crate_push	
102		sound	
105		sound	
106	4	crate_push	
106		sound	
111	0	crate_push	
111		sound	
114	2	crate_push	
114		sound	
119	4	crate_push	
119		sound	
120		turn_start	
120	0	order	push
```

Early, non-sound (`select(.type!="sound")`, first 18):
```
0	-	match_start	
0	-	half_start	
0	-	act_start	
0	-	turn_start	
0	0	order	push
0	2	order	push
0	4	order	push
85	0	crate_push	
89	4	crate_push	
97	0	crate_push	
102	2	crate_push	
106	4	crate_push	
111	0	crate_push	
114	2	crate_push	
119	4	crate_push	
120	-	turn_start	
120	0	order	push
120	2	order	push
```

Middle, non-sound (lines 95–125 — the hunt act, including a pry, a break, a spot and a find):
```
1200	1	order	beeline
1200	2	order	flee
1200	3	order	pry
1200	4	order	hide
1200	5	order	sweep
1229	3	crate_pry	
1247	3	crate_pry	
1265	3	crate_pry	
1283	3	crate_break	
1283	-	spot	
1283	-	found	
1320	-	turn_start	
1320	0	order	hide
1320	1	order	beeline
1320	3	order	sweep
1320	4	order	hide
1320	5	order	sweep
1440	-	turn_start	
1440	0	order	hide
1440	1	order	beeline
1440	3	order	sweep
1440	4	order	hide
1440	5	order	sweep
1560	-	turn_start	
1560	0	order	hide
1560	1	order	beeline
1560	3	order	sweep
1560	4	order	hide
1560	5	order	sweep
1680	-	turn_start	
1680	0	order	hide
```

```bash
jq -r '.events[]|[.t,(.seat//""),.type,(.intent//.say//.cause//"")]|@tsv' /tmp/ep.replay | tail -20
```
```
4560		turn_start	
4568		sound	
4592		sound	
4616		sound	
4640		sound	
4680		turn_start	
4680		sound	
4736		sound	
4760		sound	
4784		sound	
4800		turn_start	
4808		sound	
4848		sound	
4904		sound	
4920		turn_start	
4928		sound	
4952		sound	
4976		sound	
5016		sound	
5040		end	
```
Last 18 non-sound (the second half's endgame — a sweeping seeker shoving crates, a spot, a find,
the act closing):
```
4080	4	order	sweep
4088	4	crate_push	
4101	4	crate_push	
4113	4	crate_push	
4126	4	crate_push	
4146	-	spot	
4157	4	crate_push	
4157	-	found	
4158	-	act_end	
4170	4	crate_push	
4200	-	turn_start	
4320	-	turn_start	
4440	-	turn_start	
4560	-	turn_start	
4680	-	turn_start	
4800	-	turn_start	
4920	-	turn_start	
5040	-	end	
```

```bash
jq -r '.results' /tmp/ep.replay
```
```json
{
  "names": ["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"],
  "aliases": ["Moth-1","Owl-1","Moth-2","Owl-2","Moth-3","Owl-3"],
  "teams": ["Moth","Owl","Moth","Owl","Moth","Owl"],
  "hid_in_half": [1,2,1,2,1,2],
  "policy_kinds": ["llm","llm","scripted","scripted","scripted","scripted"],
  "scores": [0.693,0.307,0.693,0.307,0.693,0.307],
  "win": [true,false,true,false,true,false],
  "hidden_ticks": [1649,917,563,472,1800,543],
  "hidden_seconds": [68.7,38.2,23.5,19.7,75.0,22.6],
  "finds": [1,1,1,0,1,1],
  "crates_pushed": [14,0,9,4,26,3],
  "crates_locked": [1,1,2,1,1,0],
  "crates_broken": [0,0,1,2,0,0],
  "team_hidden_frac": [0.743,0.358],
  "reason": "complete",
  "end_rule": "full_time",
  "winner": 0,
  "final_tick": 5040,
  "halves_played": 2,
  "llm_turns": [28,29,0,0,0,0],
  "fallback_turns": [0,0,0,0,0,0]
}
```
(fields elided for width: `hunt_ticks_played`, `team_hidden_seconds`, `final_turn`, `seed`,
`fallback_causes` — the last is all-zero for all six seats, pasted in check 4.)

### 8(b) The static bundle and every asset it names

```bash
BUNDLE="https://api.observatory.softmax-research.net/v2/coworlds/replays/static/$COW/sha256%3A891128215115bf6b75a1e51bd0299ba909b4b7595fbcd30d615ffe454af286f4"
curl -sS "$BUNDLE/index.html" -o index.html -w 'index.html %{http_code} %{size_download}\n'
grep -oE '(src|href)="[^"]+"' index.html | sort -u        # pass 1
```
```
src="./chrome_common.js"
src="./static_replay.js"
src="./wire_constants.js"
```
Transitive closure (each fetched file re-grepped for the files *it* names):
`static_replay.js` → `./static_replay_worker.js`, `./font.ttf`; `static_replay_worker.js` →
`./broadcast_core.js`, `./lantern_replay.js`; `broadcast_core.js` → `./art/{floor.jpg, crate.png,
crate_locked.png, crate_broken.png, cog_moth.png, cog_owl.png}` (`ART_BASE = config.artBase ||
'./art'`, no override set anywhere in the bundle).

```bash
grep -ohE '[A-Za-z0-9_.-]+\.wasm' index.html *.js | sort -u    # pass 2: the wasm the loader names
```
```
lantern_replay.wasm
```
(named by `function findWasmBinary(){return locateFile("lantern_replay.wasm")}` in
`lantern_replay.js`.)

Full asset table — every file re-fetched fresh in one pass:

```bash
for A in index.html chrome_common.js static_replay.js wire_constants.js static_replay_worker.js \
         broadcast_core.js lantern_replay.js lantern_replay.wasm font.ttf \
         art/floor.jpg art/crate.png art/crate_locked.png art/crate_broken.png \
         art/cog_moth.png art/cog_owl.png; do
  curl -sSL "$BUNDLE/$A" -o "assets/$A" -w "$A %{http_code} %{size_download} %{content_type}\n"
done
```
```
index.html 200 109341 text/html; charset=utf-8
chrome_common.js 200 10185 text/javascript; charset=utf-8
static_replay.js 200 9831 text/javascript; charset=utf-8
wire_constants.js 200 233 text/javascript; charset=utf-8
static_replay_worker.js 200 9498 text/javascript; charset=utf-8
broadcast_core.js 200 16669 text/javascript; charset=utf-8
lantern_replay.js 200 13122 text/javascript; charset=utf-8
lantern_replay.wasm 200 184932 application/wasm
font.ttf 200 390340 application/octet-stream
art/floor.jpg 200 10489 image/jpeg
art/crate.png 200 766 image/png
art/crate_locked.png 200 961 image/png
art/crate_broken.png 200 552 image/png
art/cog_moth.png 200 1562 image/png
art/cog_owl.png 200 1645 image/png
```
15/15 assets **200**, none 0-byte. Sniffed types confirm no body is an HTML error page:
```bash
file index.html static_replay.js lantern_replay.wasm art/cog_owl.png font.ttf
```
```
index.html:          HTML document, Unicode text, UTF-8 text, with very long lines (20173)
static_replay.js:    JavaScript source, ASCII text
lantern_replay.wasm: WebAssembly (wasm) binary module version 0x1 (MVP)
art/cog_owl.png:     PNG image data, 128 x 128, 8-bit/color RGBA, non-interlaced
font.ttf:            TrueType Font data, digitally signed, 19 tables, 30 names … RajdhaniSemiBold
```

### 8(c) The viewer shell's error markers

```bash
grep -c 'coworld-replay' static_replay.js
grep -n 'tell("ready")' static_replay.js || echo '(no double-quoted form)'
grep -n "tell('ready')" static_replay.js        # adapted: this bundle single-quotes
```
```
2
(no double-quoted form)
153:              window.requestAnimationFrame(function () { tell('ready'); });
```
Adaptation noted: the prompt's literal `tell("ready")` is the bullwhip bundle's spelling; lantern's
shell uses single quotes. Both required markers hit. Context, pasted from the fetched file:
```js
  // ... BULLWHIP'S `coworld-replay` postMessage BRIDGE
  // is added: an embedding page (the softmax.com theater, the Observatory
  // episode page) can only see this document's `load` event ...
  function tell(type, message) {
    if (window.parent === window) return;
    var envelope = { src: 'coworld-replay', type: type };
    if (message) envelope.message = message;
    try { window.parent.postMessage(envelope, '*'); } catch (ignore) {}
  }
  tell('loading');
…
          if (!readyTold) {
            readyTold = true;
            // Report ready one PAINTED frame later, so `ready` means a
            // picture and not merely a parsed payload.
            window.requestAnimationFrame(function () {
              window.requestAnimationFrame(function () { tell('ready'); });
            });
          }
```
(`tell('error', message)` also present, line 51 — the failure path reports too.)

### Judgment

**It is legible and it shows the game.** The event stream reads as lantern's hide-and-seek from
first tick to last, in the right order and at the right scale: `match_start` → `half_start` →
`act_start` opens a lights-on build act in which only the three hiding seats are asked for orders
(seats 0, 2, 4 at t=0, exactly as the design's "seekers frozen in the pen" rule requires), and those
orders immediately turn into physical `crate_push` events at 24 Hz — the champion Moth-1's opening
`push` order ("Push C0 toward left nook at [240,329]") is followed by its crate shoves at t=85, 97,
111. The build ends with locks (6 `crate_lock` events, `crates_locked` = [1,1,2,1,1,0]), then the
hunt act flips the vocabulary: seekers issue `sweep`/`beeline`/`pry`, hiders `hide`/`flee`, and the
middle excerpt shows a complete causal chain — seat 3 orders `pry` at t=1200, three `crate_pry`
progress events, a `crate_break` at t=1283 and in the same tick a `spot` and a `found`. That is the
game's central decision (breaching a locked fort at the cost of a 900 px noise ring) resolving on
screen. Five `found` and six `spot` events across two halves, `half_end` at the intermission and
`end` at t=5040, with `halves_played: 2` and both halves' hunts fully simulated. The champion seats
are the two `llm` seats and they carry the match: Moth-1 stays motionless behind its locked crate
for 1649 of 1800 hunt ticks (68.7 s hidden) while Owl-1 flees perpendicular to an incoming beam at
t=4080; the team fractions come out 0.743 vs 0.358 and the final scores 0.693/0.307 sum to 1 per
side, `winner: 0`, `reason: complete`. Nothing is empty, nothing is stuck: 156 orders, 368 sound
rings, zero fallbacks. On the viewer side, the static bundle is whole — 15/15 assets 200 with real
bytes, including a 184,932-byte valid WebAssembly MVP module, six real PNG/JPEG art bitmaps at
their authored dimensions and a real TrueType font — so the renderer has both its simulator and its
art, and the shell carries the `coworld-replay` postMessage bridge with both `tell('loading')` and
a `tell('ready')` fired one *painted* frame after the first draw, which is what tells the embedding
softmax.com theater the picture is up. I did not render anything and make no claim about pixels;
this judgment rests only on the three fetches above.

Status: **TRUE**.

---

## Summary table

| # | Item | Verdict | Key evidence |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers | **TRUE** | rounds #2 `round_93bc2d0b…` (03:38:19Z) and #3 `round_b878a6b2…` (03:53:40Z); round 1 excluded, error quoted |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** | `daveey` rank 1 (1030.53, 2 rounds), `daveey-1` rank 2 (969.47, 2 rounds); no filler rows |
| 3 | Latest round's episode request completed w/ replay | **TRUE** | `ereq_d3790a64…` `completed`, replay_url set, positions 0/1 = daveey/daveey-1, 2–5 `is_filler:true` |
| 4 | Replay bytes valid and show the game | **TRUE** | 313,685 B strict JSON; `lantern.replay.v1` = manifest; `reason: complete`; 28/28 + 29/29 llm orders; 0 fallbacks |
| 5 | Hosted game log clean | **TRUE** | `CLEAN` raw and decoded; 57/57 Bedrock 200; 6/6 seats; `complete/full_time` |
| 6 | Public page uses the static replay path | **TRUE** | SSR `playlist[0]` = `lantern.r3.e1`; session POST → static `…/replays/static/<cow>/<manifest_sha>/index.html?replay=…`, `ready:true`; no `/client/replay` |
| 7 | Certification declared the static bundle | **TRUE** | committed `release-result.json`: `Replay liveness: skipped (static replay bundle declared; …)`, 10/10 steps |
| 8 | Spectator judgment | **TRUE** | ordered event excerpts read as hide-and-seek; 15/15 bundle assets 200; `coworld-replay` ×2 and `tell('ready')` @153 |
