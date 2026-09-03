# VERIFY — continuous-control   (2026-09-03T19:39:30Z)

Verdict: **all-true** (8 / 8 TRUE)

Run: `2026-08-29-continuous-control` · slug `continuous-control` · coworld `cow_39456c26-cffa-4d99-9be9-b2b49454143c` v`0.1.2`
League `league_62a1e77b-c464-41ba-90df-702fc0d9d3db` · division `div_07b556f6-3e13-40db-afd8-d0823c6ed9d3`

All evidence below was fetched fresh in this session (2026-09-03T19:33Z–19:39Z), except the two
documented exceptions: **check 7** reads the committed `runs/2026-08-29-continuous-control/release-result.json`
(phase 40's artifact copy) and **check 8** reads the artifact of the `viewer-check.yml` run this
session dispatched (run `33797485426`, dispatched 2026-09-03T19:37:04Z).

Common preamble for every `curl` below (header **values** never printed):

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_62a1e77b-c464-41ba-90df-702fc0d9d3db
D=div_07b556f6-3e13-40db-afd8-d0823c6ed9d3
COW=cow_39456c26-cffa-4d99-9be9-b2b49454143c
```

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}"      # HTTP 200
jq -r 'if type=="array" then . else .entries end
       | .[] | {id,round_number,status,error,created_at,completed_at,
                entrants:[.round_config.entrant_attributions[].policy_version_id]}'
```

```json
{
  "id": "round_74324044-7fe2-454c-a934-575eb65b7514",
  "round_number": 2,
  "status": "completed",
  "error": null,
  "created_at": "2026-09-03T19:25:38.852090Z",
  "completed_at": "2026-09-03T19:28:17.409592Z",
  "entrants": [
    "db05b869-a543-48e3-8c15-37a26d2a2cdf",
    "f73961b5-88ec-4a61-95a6-bc0dafd2a9f5",
    "d461f4c5-a858-48c9-a04f-be0871e253b2",
    "af8c6ada-ae4f-49a9-932f-3ddb0cabd902",
    "dcc140de-52b4-40f2-a3aa-b02639cd8d1a",
    "34dc6fcb-0db8-4354-95a7-d616653ea777",
    "3faae692-904c-4828-993f-4a0861da37c4"
  ]
}
{
  "id": "round_26e98f6c-a4d5-4c23-bd62-0ba167ed7f8b",
  "round_number": 1,
  "status": "completed",
  "error": null,
  "created_at": "2026-09-03T19:10:37.991725Z",
  "completed_at": "2026-09-03T19:13:24.612276Z",
  "entrants": [
    "db05b869-a543-48e3-8c15-37a26d2a2cdf",
    "f73961b5-88ec-4a61-95a6-bc0dafd2a9f5",
    "d461f4c5-a858-48c9-a04f-be0871e253b2",
    "af8c6ada-ae4f-49a9-932f-3ddb0cabd902",
    "dcc140de-52b4-40f2-a3aa-b02639cd8d1a",
    "34dc6fcb-0db8-4354-95a7-d616653ea777",
    "3faae692-904c-4828-993f-4a0861da37c4"
  ]
}
```

```bash
jq -r 'if type=="array" then . else .entries end
       | [.[]|select(.status=="completed")]|length'
```
```
2
```

Fillers are still registered, fetched live (this read needs the `X-Use-Elevated-Privileges`
header even though it is a read):

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"      # HTTP 200
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"bd151d35-bdad-4ea8-853f-ff389cabb1f3","policy_id":"ad6b208b-d8ba-453e-8430-5e48c595dc60","policy_name":"continuous-control-trotter","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},
 {"policy_version_id":"ece2febe-a912-4f20-be57-ce740aa1350c","policy_id":"8ba43211-9449-402b-a99c-e0690aa6e023","policy_name":"continuous-control-plodder","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```

Status: **TRUE** — 2 rounds `completed`, `error: null` on both (rounds 1 and 2, completed
2026-09-03T19:13:24Z and 2026-09-03T19:28:17Z). Fillers `continuous-control-trotter:v2`
(`bd151d35…`) and `continuous-control-plodder:v2` (`ece2febe…`) were registered at
2026-08-29T13:26:58Z (`log.md`, phase-50 line `50 fillers registered: trotter:v2 bd151d35,
plodder:v2 ece2febe`) — i.e. **before round 1 was even created** (2026-09-03T19:10:37Z), so both
completed rounds are after the fillers were set. No `failed`/`discarded` rounds exist in the list.
Both champion policy versions are seated in both rounds (`af8c6ada…` = gaitsmith/daveey,
`34dc6fcb…` = throttle/daveey-1); neither filler uuid appears in `entrant_attributions` — with 7
real entrants the scheduler needed no filler seats.

---

## 2. Both champions ranked; fillers absent or Baseline — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end
          | .[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
# HTTP 200 — bare JSON array, as the playbook says
```

```
1	richard	co-gas-continuous-control-feedback-richard:v2	1162.7348458168515	2	12.0
2	daveey-1	continuous-control-throttle:v2	1108.2440527389058	2	10.0
3	relh	co-gas-continuous-control-feedback-relhalpha:v1	1022.0465598545583	2	7.0
4	Andre von Auto	plyaska:v1	1009.9534401454417	2	6.0
5	Andrew Brower	continuous-control-example:v1	904.0	2	3.0
6	docxology	daf-cogame-carrier:v1	901.2651541831485	2	2.0
7	daveey	continuous-control-gaitsmith:v2	891.7559472610942	2	2.0
```

Status: **TRUE** — `daveey-1` (`continuous-control-throttle:v2`) at rank 2 and `daveey`
(`continuous-control-gaitsmith:v2`) at rank 7, both with `rounds_played = 2` (≥ 1). Neither filler
appears: no row carries `continuous-control-trotter`, `continuous-control-plodder`, or a
`policy_label` starting `Baseline`. The five other rows are community players who joined this
league; SPEC requires only that both champions rank and the fillers do not.

---

## 3. Latest round's episode requests completed with a replay — **TRUE**

The latest completed round is `round_74324044-…` (`round_number` 2, from check 1). The flat
`/episode-requests?round_id=` route 405s (playbook §9); the nested route is used:

```bash
R=round_74324044-7fe2-454c-a934-575eb65b7514
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end | map({id,status,created_at})'   # HTTP 200
```
```json
[{"id":"ereq_1ce23a55-13da-490d-ac83-eefeceddbf0a","status":"completed","created_at":"2026-09-03T19:25:39.995436Z"},
 {"id":"ereq_e6aad2bb-83ed-47f5-a9d7-553698fb561b","status":"completed","created_at":"2026-09-03T19:25:39.970299Z"},
 {"id":"ereq_17819ff0-6cb8-4f1a-a837-30d801cc8719","status":"completed","created_at":"2026-09-03T19:25:39.959869Z"},
 {"id":"ereq_e7e02675-d4f6-4861-9238-da337f2a7259","status":"completed","created_at":"2026-09-03T19:25:39.947175Z"},
 {"id":"ereq_3f58d40e-8732-452f-a847-cdd0ce693276","status":"completed","created_at":"2026-09-03T19:25:39.938958Z"},
 {"id":"ereq_7175dc80-75a9-4010-9de2-c77d41d8f133","status":"completed","created_at":"2026-09-03T19:25:39.930445Z"},
 {"id":"ereq_71a108c7-d582-4a6f-961d-845f861f5e6c","status":"completed","created_at":"2026-09-03T19:25:39.923519Z"}]
```

All 7 are `completed`. **This coworld is `num_agents: 1` by design** (`design.md` §124–126: "Exactly
one seat, always … Every episode is a solo run"), so a round is one solo episode per entrant and no
single episode can name both champions. Both champions' own episode requests are therefore fetched:

```bash
for E in ereq_e7e02675-d4f6-4861-9238-da337f2a7259 ereq_e6aad2bb-83ed-47f5-a9d7-553698fb561b; do
  curl -sS "$BASE/episode-requests/$E" "${AUTH[@]}" | jq -c '{status, replay_url, participants, participant_scores}'
done
```

```json
{"status":"completed","replay_url":"https://softmax-public.s3.amazonaws.com/replays/f546620f-3b9f-4dd2-8705-0d2cbd5819b8.replay","participants":[{"position":0,"kind":"policy","policy_version_id":"af8c6ada-ae4f-49a9-932f-3ddb0cabd902","policy_id":"04077f55-cca1-4d9e-972e-a99c6245b083","policy_name":"continuous-control-gaitsmith","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","is_filler":false,"is_seed":false}],"participant_scores":[{"position":0,"score":20.543}]}
{"status":"completed","replay_url":"https://softmax-public.s3.amazonaws.com/replays/4fd86b62-8123-45b1-a2c8-2ba10fad5f64.replay","participants":[{"position":0,"kind":"policy","policy_version_id":"34dc6fcb-0db8-4354-95a7-d616653ea777","policy_id":"963e9cf4-095b-4e17-9d33-5bc18f4d1f62","policy_name":"continuous-control-throttle","version":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","is_filler":false,"is_seed":false}],"participant_scores":[{"position":0,"score":57.236}]}
```

Status: **TRUE** — every episode request of the latest completed round is `status: "completed"`
with a non-null `replay_url`; the two champion episodes name `daveey` /
`continuous-control-gaitsmith:v2` and `daveey-1` / `continuous-control-throttle:v2`, both
`is_filler: false`, scoring 20.543 and 57.236. No `Baseline (N)` seat exists because no filler was
seated (check 1).

---

## 4. Replay bytes are valid and show the game — **TRUE**

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/f546620f-3b9f-4dd2-8705-0d2cbd5819b8.replay" -o /tmp/ep.replay
# HTTP 200 bytes=79464
head -c 32 /tmp/ep.replay | od -c
```
```
0000000   C   O   W   L   D   C   C   L 001  \0 022  \0  \0  \0   c   o
0000020   n   t   i   n   u   o   u   s   -   c   o   n   t   r   o   l
```

```bash
jq -e . /tmp/ep.replay >/dev/null; echo "exit=$?"
```
```
jq: parse error: Invalid numeric literal at line 1, column 67
exit=5
```

The raw bytes are the starter's binary `COWLDCCL` replay container, not a bare JSON document —
`design.md` §"The phase-60 substitute for docs/SPEC.md §Definition of done check 4" (lines
1340–1352) declares exactly this and pins the substitute: run the repo's stdlib-only
`tools/replay_summary.py`, which emits **one strict-UTF-8 JSON object**, and apply the strict
parser to that. Executed verbatim (tool taken from a fresh read-only clone of
`Metta-AI/cogame-continuous-control` @ main):

```bash
python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json     # exit=0, empty stderr
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .results.reason, .results.endRule, .results.totalReturn' /tmp/ep.json
```
```
strict UTF-8 JSON: ok
continuous-control/v1
complete
ladderComplete
20.543
```

```bash
jq -c '.results' /tmp/ep.json
```
```json
{"names":["gaitsmith"],"aliases":["Alpha"],"scores":[20.543],"win":[false],"winner":null,"reason":"complete","endRule":"ladderComplete","variant":"ladder","seed":8184912711049247138,"stageCount":3,"stageTicks":468,"par":40.0,"maxReturn":243.744,"totalReturn":20.543,"stageMorph":["hopper","cheetah","walker"],"stageOutcome":["fell","ran","fell"],"stageDistance":[-0.07,33.983,2.431],"stageReturn":[0.11,16.605,3.828],"stageTicksRun":[64,468,51],"stageTurns":[3,14,3],"stageUprightTicks":[63,0,50],"stageCtrlCost":[0.002,0.387,0.019],"stagePeakSpeed":[1.31,3.83,2.43],"stageStrides":[3,34,4],"stagesLined":0,"distanceTotal":36.344,"uprightTicksTotal":113,"ctrlCostTotal":0.408,"falls":2,"saturatedTicks":514,"finalTick":691,"turnsPlayed":20,"ordersRepaired":22,"policyKinds":["llm"],"llmTurns":20,"fallbackTurns":0,"deadSeats":[false],"stopDetail":""}
```

```bash
echo "llm_orders=$(jq -r '[.orders[]|select(.source=="llm")]|length' ep.json) \
fallbacks=$(jq -r '.fallbacks' ep.json) says=$(jq -r '.says|length' ep.json) \
distinct_gait=$(jq -r '[.orders[]|.gait]|unique|length' ep.json) \
distinct_cadence=$(jq -r '[.orders[]|.cadence]|unique|length' ep.json) \
total_orders=$(jq -r '.orders|length' ep.json)"
jq -c '[.orders[]|.gait]|unique' ep.json ; jq -c '[.orders[]|.cadence]|unique' ep.json
jq -c '.register' ep.json
```
```
llm_orders=20 fallbacks=0 says=19 distinct_gait=4 distinct_cadence=14 total_orders=20
["brake","crouch","run","walk"]
[0,10,12,18,20,26,28,30,34,36,37,42,45,50]
{"alias":"Alpha","name":"gaitsmith","policy":"gaitsmith","kind":"llm","baseline":"trotter"}
```

Champion #2's replay, same treatment:

```bash
curl -sSL ".../replays/4fd86b62-8123-45b1-a2c8-2ba10fad5f64.replay" -o /tmp/ep2.replay   # HTTP 200 bytes=106419
python3 tools/replay_summary.py /tmp/ep2.replay > /tmp/ep2.json
jq -r '.protocol, .results.reason, .results.endRule, .results.totalReturn, .results.distanceTotal' ep2.json
```
```
continuous-control/v1
complete
ladderComplete
57.236
67.794
llm_orders=29 fallbacks=0 says=29 gaits=3 cadences=15
```

Status: **TRUE** —
* strict UTF-8 JSON: `jq -e` accepts the `replay_summary.py` output for both champion replays (the
  raw container is binary by design, and the design note pins this exact substitute);
* `protocol == "continuous-control/v1"`, which matches the protocol the manifest points at —
  `coworld_manifest_template.json` `protocols.{player,global}` → `docs/PROTOCOL.md` line 3:
  "Protocol name: **`continuous-control/v1`**" (also pinned as `ProtocolName` in
  `src/cc/sim_types.nim:25`);
* `results.reason == "complete"` on both (`endRule: "ladderComplete"`, the healthy value). The
  declared-acceptable `deadline` exception (`design.md` §"End conditions and legal `results.reason`
  values", lines 507–512) was **not needed**;
* the champion seat is doing the thing the game is about: `policyKinds: ["llm"]`, `llmTurns: 20`,
  **`fallbackTurns: 0` / `fallbacks: 0`** (zero, not a minority), 19 non-empty `say` lines, 4
  distinct gaits and 14 distinct cadences over 20 orders (design threshold: >1 gait, >3 cadences),
  `distanceTotal: 36.344` (> 5), 3 stages resolved `fell / ran / fell` in 691 ticks. Same picture
  for champion #2 (29 LLM orders, 0 fallbacks, 29 says, 67.794 m).

---

## 5. Hosted game log is clean — **TRUE**

The logs body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it is
decoded with `ast.literal_eval` per repr **before** grepping (playbook §10):

```bash
for E in ereq_e7e02675-d4f6-4861-9238-da337f2a7259 ereq_e6aad2bb-83ed-47f5-a9d7-553698fb561b; do
  curl -sS "$BASE/episode-requests/$E/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o logs-$E.raw
  python3 declog.py logs-$E.raw > logs-$E.txt          # ast.literal_eval each b'…' line
  grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs-$E.txt || echo CLEAN
done
```
```
ereq_e7e02675-d4f6-4861-9238-da337f2a7259 HTTP 200 bytes=3990
===== ereq_e7e02675-d4f6-4861-9238-da337f2a7259 =====  (48 decoded lines)
CLEAN
===== ereq_e6aad2bb-83ed-47f5-a9d7-553698fb561b =====  (58 decoded lines)
CLEAN
```

The decoded log for champion #1's episode, in full (it is short):

```
===== container: coworld-init-config =====

===== container: bedrock-sidecar =====
2026-09-03 19:25:49,276 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1","has_role_arn":true,"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar","episode_request_id":"e7e02675-d4f6-4861-9238-da337f2a7259","job_request_id":"f546620f-3b9f-4dd2-8705-0d2cbd5819b8","role":"game","slot":"game","image_digest":"sha256:594d053b00c6d01f4c8383611aa7a335e02c2e2e4ce0f0b4910dc3f83531423d"}
[2026-09-03 19:25:49 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-09-03 19:25:49,616 INFO hypercorn.error Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-09-03 19:25:58,314 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
   … 19 further identical `"HTTP/1.1 200 OK"` lines, 19:26:00 → 19:26:55 (20 calls, one per turn) …

===== container: game =====
continuous-control: seed not pinned; randomized
continuous-control: seats=1 variant=ladder stages=3 stageTicks=468 maxTicks=1512 turnTicks=36 wallClock=690s model=
continuous-control: serving on 0.0.0.0:8080
continuous-control: player slot 0 connected (1/1)
continuous-control: slot 0 registered (1843 prompt chars, llm)
continuous-control: slot 0 registered (1843 prompt chars, llm)
continuous-control: slot 0 registered (1843 prompt chars, llm)
continuous-control: starting with 1/1 players connected
continuous-control llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
continuous-control: slot 0 registered (1843 prompt chars, llm)
continuous-control: slot 0 registered (1843 prompt chars, llm)
continuous-control: slot 0 registered (1843 prompt chars, llm)
continuous-control: writing replay (79464 bytes) and results
continuous-control: episode complete (complete/ladderComplete) after 691 ticks, return 20542601 micro-points, 2 falls

===== container: worker =====
```

Status: **TRUE** — zero lines match `falling back|LLM provider is unavailable|cut off at
max_tokens|rejected` in either champion's decoded hosted log. All 20 (resp. 29) LLM calls returned
`HTTP/1.1 200 OK`; no documented exception was needed.

---

## 6. The public page uses the static replay path — **TRUE** (with the documented single-seat reading)

**Source 1 — raw HTML grep (the prompt's first attempt):**

```bash
curl -sS "https://softmax.com/continuous-control" | grep -o '<iframe[^>]*src="[^"]*"'
# HTTP 200 bytes=865750
NO IFRAME IN RAW HTML
```

Not a false negative: the page is client-rendered for the iframe (playbook §Featured match,
"Answered (lighthouse run, 2026-08-22)"), so the grep finds nothing for any coworld.

**Source 2 — the coworld detail API:**

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)|.[]|select(.name=="continuous-control")|{id,name,canonical,version,replay_viewer,featured_match}'
```
```json
{"id":"cow_39456c26-cffa-4d99-9be9-b2b49454143c","name":"continuous-control","canonical":true,"version":"0.1.2","replay_viewer":null,"featured_match":null}
```

`featured_match: null` is platform-wide and is not evidence either way (playbook §Featured match).

**Source 3 — the page's SSR payload (`state.playlist` / `state.pool`), which is where the featured
match actually lives:**

```bash
python3 ssr.py page.html      # brace-matched extraction of the `"state":{…}` blob
```
```
playlist len 0
pool.replays 7 pool.live 0
first pool replay participants 1 completed_at 2026-09-03T19:28:14.173994Z
```

`state.playlist` is empty and the rendered page says *"Between rounds / No featured match yet / The
next round is expected in ~8m"*, while `state.pool.replays` carries all **7** completed round-2
episodes, e.g.:

```json
{"kind":"replay","episodeNumber":1,"episode":{"id":"ereq_1ce23a55-13da-490d-ac83-eefeceddbf0a",
 "coworld_id":"cow_39456c26-cffa-4d99-9be9-b2b49454143c","coworld_name":"continuous-control",
 "coworld_version":"0.1.2","variant_name":"Locomotion ladder (1 cog, 3 machines)","status":"completed",
 "participants":[{"position":0,"player_name":"richard","is_filler":false,…}],
 "replay_url":"https://softmax-public.s3.amazonaws.com/replays/0076b56f-27e0-420c-8cd5-fe88704051e0.replay",
 "completed_at":"2026-09-03T19:28:14.173994Z"}}
```

The SSR payload's `divisionLeaderboard` carries all 7 ranked players (daveey-1 rank 2, daveey rank
7), so the "fewer than two ranked players" cause named in `prompts/60-verify.md` does **not** apply.
The cause is structural and documented: `state.playlist[i].matchup` needs `{first, second}` — two
ranked players **in one episode** — which `num_agents: 1` can never produce.
`learnings/LEARNINGS.md` §2026-08-28 nethack: *"Single-seat coworlds never get a `state.playlist`
featured matchup — judge SPEC item 6 on `state.pool.replays`. … softmax.com/<slug> shows 'No
featured match yet' forever while the featured pool carries the episodes and the session endpoint
returns the static route. … the procgen-precedent reading (pool non-empty + static route = TRUE) is
now used twice."* Live cross-check run this session, same minute:

| slug | seats | `state.playlist` len | page shows "No featured match yet" |
|---|---|---|---|
| paintbot | multi | 21 | no |
| escrow | multi | 1 | no |
| eleusis | multi | 4 | no |
| sokoban | single | 0 | yes |
| **continuous-control** | **single** | **0** | **yes** |

**Source 4 — the iframe `src` itself**, from the call the page's own JS makes:

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_39456c26-cffa-4d99-9be9-b2b49454143c","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/f546620f-3b9f-4dd2-8705-0d2cbd5819b8.replay"}'
# HTTP 200
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_39456c26-cffa-4d99-9be9-b2b49454143c/sha256%3A5a975e9fd4511b1ee55ad2f26821f7add5241b036a8a248e85225db713b0b8c4/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Ff546620f-3b9f-4dd2-8705-0d2cbd5819b8.replay",
  "ready": true
}
```

Status: **TRUE** — sources used: the raw-HTML grep (empty → unknown, per the prompt), the
`/coworlds` detail API, the page's SSR payload, and the session endpoint. The `src` is the **static**
route `…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?v=2#replay=<s3 url>` with
`ready: true` — the `<sha>` is the coworld's manifest hash
`sha256:5a975e9fd4511b1ee55ad2f26821f7add5241b036a8a248e85225db713b0b8c4`, byte-identical to
`STATE.coworld.manifest_sha`. It is **not** a `/client/replay` pod URL. The `?v=2#replay=` fragment
form is the post-2026-08-28 shape the playbook records as still the static route. The featured
*match* is absent for the documented single-seat reason above; the featured **pool** is present with
7 episodes.

---

## 7. Certification declared the static bundle — **TRUE**

Read from the **committed** copy `runs/2026-08-29-continuous-control/release-result.json` (phase
40's artifact, release run `33254010784`) — not re-downloaded, not from `/tmp`:

```bash
jq -r '.certify.replay_liveness' runs/2026-08-29-continuous-control/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE** — the string contains `Replay liveness: skipped (static replay bundle declared`.
Source: the committed `runs/2026-08-29-continuous-control/release-result.json` (the first of the two
options in `prompts/60-verify.md` check 7; no `gh run download` fallback was needed).

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

*(a) Dispatch.* The `src` from check 6 was rendered in headless chromium by CI; nothing was
rendered or inspected locally.

```bash
SRC=$(jq -r .viewer_url session.json)
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
# dispatched 2026-09-03T19:37:04Z
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:3][]|[.databaseId,.createdAt,.status,.conclusion]|@tsv'
```
```
33797485426	2026-09-03T19:37:05Z	in_progress
33797350340	2026-09-03T19:35:43Z	completed	success      <- someone else's, older than the dispatch
33797255773	2026-09-03T19:34:47Z	completed	success
```
Run **33797485426** is the one created after the dispatch (19:37:05Z > 19:37:04Z).

```bash
gh run watch 33797485426 -R Metta-AI/coworld-builder --exit-status     # green, exit=0
gh run download 33797485426 -R Metta-AI/coworld-builder -n viewer-check \
  -D runs/2026-08-29-continuous-control/viewer-check
```
```
viewer-check/viewer-smoke.json   1443 B
viewer-check/viewer-smoke.png  269566 B
viewer-check/smoke-stdout.txt     647 B
viewer-check/smoke-stderr.txt       0 B      (committed with this file)
```

*(b) Readouts, verbatim.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-29-continuous-control/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":3940,"clock":"0.1 m · 1.13 m/s ▸▸ STAGE 1/3 · HOPPER · TICK 8/468","scorebug":"ALPHA gaitsmith RETURN 0.0 0.1 m · 1.13 m/s ▸▸ STAGE 1/3 · HOPPER · TICK 8/468","feed_lines":0}
```
```bash
jq -c '.signals' … ; jq -r '.failure // "no failure"' …
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```
```
no failure
```
```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' …
```

| scrub | clock readout |
|---|---|
| 0 % | `0.1 m · 1.13 m/s ▸▸ STAGE 1/3 · HOPPER · TICK 8/468` |
| 50 % | `18.1 m · 2.10 m/s STAGE 2/3 · CHEETAH · TICK 263/468` |
| 100 % | `2.8 m · 0.00 m/s STAGE 3/3 · WALKER · TICK 51/468` |

Also from the json: `"status":"OPEN"`, `"loading_text":null`, `"console_tail":[]`,
`canvas_text: {"total":0,"outside":0,"ellipsized":0,"never_inside":0}` (this shell draws its HUD in
DOM, not on the canvas, so 0 canvas text nodes is expected and no draw crossed an edge).

**Both conditions hold: `loaded: true` (via `data-replay-loaded="true"`, first frame at 3940 ms,
no `data-replay-error`), and the three clock readouts differ** — three different stages, three
different morphologies, three different ticks and speeds. The replay advances.

*(c) Reconciliation against the replay record* (`/tmp/ep.json` from check 4 — the same episode
`f546620f-…` the viewer was pointed at). Early / middle / late orders,
`turn stage source gait cadence power lean stride_bias phase_shift repaired`:

```
early  1	0	llm	crouch	0	45	0	0	0	0
       2	0	llm	walk	45	60	6	0	0	0
       3	0	llm	walk	37	60	6	0	0	0
       4	1	llm	walk	42	48	-10	6	0	0
mid    9	1	llm	run	26	12	-10	6	0	2
      10	1	llm	run	26	24	-10	6	0	1
      12	1	llm	run	10	65	0	6	0	1
late  18	2	llm	walk	42	48	6	0	0	1
      19	2	llm	walk	50	48	6	0	0	2
      20	2	llm	brake	30	50	-10	0	0	0
```
stages: `[{"i":0,"morph":"hopper","startTick":0},{"i":1,"morph":"cheetah","startTick":100},{"i":2,"morph":"walker","startTick":604}]`;
`results.stageOutcome ["fell","ran","fell"]`, `stageDistance [-0.07, 33.983, 2.431]`,
`stageReturn [0.11, 16.605, 3.828]`, `totalReturn 20.543`, `falls 2`, `finalTick 691`.

The readouts agree with the record: 0 % → HOPPER tick 8 (stage 0, which starts at tick 0 and ends
in a fall at tick 64); 50 % → CHEETAH tick 263 at 18.1 m and 2.10 m/s (stage 1 ran the full 468
ticks for 33.98 m, peak 3.83 m/s); 100 % → WALKER tick 51 at 2.8 m and 0.00 m/s (stage 2 fell after
51 ticks having covered 2.43 m — the zero speed is the fallen machine at rest). The transport
counter reads `691 / 691`, exactly `results.finalTick`.

### Spectator judgment

**It renders, it advances, it is the game, and it is the starter's chrome — with two real
legibility defects in the endcard.** `viewer-smoke.png` is the 100 % frame. Top strip: the
starter's scorebug — three stage pips coloured red / green / red (matching `fell, ran, fell`),
`20.5 RETURN gaitsmith ALPHA` on the left, and the centred clock plate
`2.8 m · 0.00 m/s` over `STAGE 3/3 · WALKER · TICK 51/468`. Bottom strip: the starter's transport
— rewind, step-back, pause, `+5s`, play, loop, fast-forward, a `spoilers` toggle, `691 / 691`, and
`1× 2× 4× 8×` speed buttons — over the scrubber with its **RETURN momentum graph** (flat near zero
through stage 1, a step up across the cheetah run, flat again) and beat markers: red pips at the
two falls, a green pip at the stage-2 `ran`, amber pips at the turn boundaries. That is the same
transport strip, momentum scrubber, scorebug and endcard as paintbot / raid / hive — the
coworld-ctf lineage, not a look-alike rewrite; this is not the cogame-gridlock failure.

The playfield behind the endcard is dimmed by the endcard scrim, and at this frame it shows the
fallen walker as a small cluster of link dots on the ground line near the left of the track, with
the in-canvas stage plate (`STAGE 3/3 · WALKER / 2.8 M · 0.00 M/S`) and the `HOP CHE WAL` stage pips
above it, all legible. The `GAIT ORDER` panel bottom-right is present with its bars (amber for the
current order, green/red history rows) but its labels are dimmed to near-invisibility under the
scrim; the single broadcast feed line visible, `FINAL — RETURN 20.5, 0 LINED OUT, 2 FALLS`, is
dimmed to the same degree, and `feed_lines` sampled 0 at load (the known under-count — LEARNINGS
§2026-08-28 procgen — but 0 rather than 2 is worth a look).

The endcard itself dominates the frame and is mostly right: `RETURN 20.5`, the per-stage table
(`1 HOPPER … -0.1 / 0.1`, `2 CHEETAH … 34.0 / 16.6`, `3 WALKER … 2.4 / 3.8`) matching
`stageDistance` / `stageReturn` to the decimal, `SCORE 20.543`, `0 OF 3 LINED OUT, 2 FALLS`. Two
defects, both plainly visible in the png and both **non-blocking for this check but worth a
phase-30/legibility card**:

1. **Endcard table columns collide.** The header row draws as `STAGE  BODYRESUDISTANRETURN` —
   `BODY`, `RESULT`, `DISTANCE` and `RETURN` are laid out at overlapping x-offsets, and in the body
   rows the result word is drawn on top of the morphology name (`HOPPER`+`fell` → `HOPPEfell`,
   `CHEETAH`+`ran`, `WALKER`+`fell`). The numeric columns are clean; the two text columns are
   unreadable.
2. **Wrong units / zeroed counters in the endcard subtitle.** It reads
   `0 OF 3 LINED OUT, 2 FALLS, PAR 40000000 MISSED` and
   `0.0 m covered, 0 upright ticks, 0 saturated ticks, 0 fallback turns · SCORE 20.543`, while the
   replay's own `results` say `par: 40.0`, `distanceTotal: 36.344`, `uprightTicksTotal: 113`,
   `saturatedTicks: 514`. `PAR 40000000` is the micro-points value printed without the divisor, and
   the three totals are being read from fields the endcard is not populating. The scorebug, the
   clock, the per-stage table and the score are all correct, so the picture does not lie about who
   did what — but that one line does.

Status: **TRUE** — `loaded: true` and the three clock readouts differ; the rendered picture is
legible, is unmistakably this game (three morphologies, gait orders, distance/return), and wears the
starter's chrome. The two endcard defects are recorded as legibility residue for the coordinator,
not as a check-8 failure.

---

## Tally

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | TRUE |
| 2 | Both champions ranked, fillers absent/Baseline | TRUE |
| 3 | Latest round's episode requests completed with replay_url | TRUE |
| 4 | Replay bytes valid, protocol matches, reason complete, not fallbacks | TRUE |
| 5 | Hosted game log clean | TRUE |
| 6 | Public page uses the static replay path | TRUE |
| 7 | Certification declared the static bundle | TRUE |
| 8 | Viewer executed: loaded + advances + spectator judgment | TRUE |

**Verdict: all-true (8 / 8).**
