# VERIFY — commons-family   (2026-08-24T21:56Z)

Verdict: **all-true** (8/8 TRUE — check 5 carries one documented, cross-checked platform-probe line;
check 1 carries one documented round-3 platform settlement anomaly that does not change its verdict)

Fetched fresh this run (verifier thread, 2026-08-24T21:21Z–21:56Z). Every response below is pasted
as received; long bodies are trimmed to the relevant fields and marked `…`. Headers are named, never
their values.

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_a95d0e60-1042-4981-bcdc-ead449bfa783
D=div_83b3f90b-ecc3-4052-9c14-c45173886c79
COW=cow_73578681-ae8b-4ec8-b0ef-9622d639c09a          # version 0.1.3
# NOTE: the platform keys this coworld on game.name `commons_family`; the public page is /commons-family.
```

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

Fillers were registered `2026-08-24T21:19:30Z` (log.md line 49: `50 fillers POST 200:
freerider:v3=4df6a8b8, cleaner:v3=46442064`). Rounds created strictly after that instant: **3 and 4**,
both `completed`.

### Poll log (every ~5 min, bound 75 min from 2026-08-24T21:21Z; consumed 32 min)

```
2026-08-24T21:21:31Z rounds=[{"n":2,"s":"completed"},{"n":1,"s":"failed"}]
2026-08-24T21:25:31Z rounds=[{"n":2,"s":"completed"},{"n":1,"s":"failed"}]
2026-08-24T21:27:49Z rounds=[{"n":2,"s":"completed"},{"n":1,"s":"failed"}]
2026-08-24T21:28:10Z rounds=[{"n":2,"s":"completed"},{"n":1,"s":"failed"}]
2026-08-24T21:32:21Z rounds=[{"n":2,"s":"completed"},{"n":1,"s":"failed"}]
2026-08-24T21:36:53Z rounds=[{"n":3,"s":"completed"},{"n":2,"s":"completed"},{"n":1,"s":"failed"}]
2026-08-24T21:39:29Z rounds=[{"n":3,"s":"completed"},{"n":2,"s":"completed"},{"n":1,"s":"failed"}]
2026-08-24T21:44:39Z rounds=[{"n":3,"s":"completed"},{"n":2,"s":"completed"},{"n":1,"s":"failed"}]
2026-08-24T21:49:21Z rounds=[{"n":4,"s":"pending"},{"n":3,"s":"completed"},{"n":2,"s":"completed"},{"n":1,"s":"failed"}]
2026-08-24T21:52:46Z rounds=[{"n":4,"s":"completed"},{"n":3,"s":"completed"},{"n":2,"s":"completed"},{"n":1,"s":"failed"}]
```

### Final fetch (2026-08-24T21:52:59Z)

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end
          | map({round_number,id,status,error,created_at,completed_at})'
```

```json
[
  {
    "round_number": 4,
    "id": "round_4342db17-de90-4f3e-8b1e-5405249ad1d6",
    "status": "completed",
    "error": null,
    "created_at": "2026-08-24T21:48:54.076618Z",
    "completed_at": "2026-08-24T21:51:20.542401Z"
  },
  {
    "round_number": 3,
    "id": "round_f0ba6263-8154-4e05-802d-92e3d60b4653",
    "status": "completed",
    "error": null,
    "created_at": "2026-08-24T21:33:53.641967Z",
    "completed_at": "2026-08-24T21:34:06.646302Z"
  },
  {
    "round_number": 2,
    "id": "round_57d9cc57-a7e4-4cfe-a868-f59f102b6ffd",
    "status": "completed",
    "error": null,
    "created_at": "2026-08-24T21:18:53.248945Z",
    "completed_at": "2026-08-24T21:21:16.528392Z"
  },
  {
    "round_number": 1,
    "id": "round_d2ef536b-917a-495e-9eab-400f9958fa97",
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-24T21:18:00.417127Z",
    "completed_at": "2026-08-24T21:18:00.817972Z"
  }
]
```

```bash
jq -r '[ (if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
```

```
3
```

Status: **TRUE** — three rounds `completed` (2, 3, 4); one `failed` (round 1), whose `error` is quoted
verbatim above (the known pre-filler auto-trigger race; it does not count). Under the strict reading
("rounds created after the fillers were registered"), rounds **3 and 4** qualify — 2 rounds, ≥ 2.
Under the scored reading ("rounds the ladder settled into Elo"), rounds **2 and 4** qualify — also 2,
and both seated the fillers as `Baseline (N)` (check 3 shows round 4's roster; round 2's was the same
shape). Either reading satisfies the item.

**Documented anomaly (round 3, platform-side, not a coworld defect).** Round 3 is `status:
"completed"` but its episode-request never had its result fields populated, and the leaderboard shows
`rounds_played: 2` (rounds 2 and 4), i.e. round 3 was not scored:

```bash
curl -sS "$BASE/episode-requests/ereq_fc8bb683-5194-4cbd-ba90-682c05205e59" "${AUTH[@]}" \
 | jq -c '{status,replay_url,episode_id,scores,dispatched_at,running_at,completed_at}'
```

```json
{"status":"completed","replay_url":null,"episode_id":null,"scores":[],
 "dispatched_at":"2026-08-24T21:33:56.240969Z","running_at":null,"completed_at":"2026-08-24T21:34:02.572335Z"}
```

The episode itself *did* run — its artifacts exist and are a distinct, complete 20-round game
(different seed, different scores from round 2's, zero fallbacks):

```bash
curl -sS "$BASE/episode-requests/ereq_fc8bb683-5194-4cbd-ba90-682c05205e59/artifacts/results" "${AUTH[@]}" "${ELEV[@]}" | jq -c '{reason,scores,welfare}'
curl -sS "$BASE/episode-requests/ereq_fc8bb683-5194-4cbd-ba90-682c05205e59/artifacts/replay"  "${AUTH[@]}" "${ELEV[@]}" -o /tmp/ep3.replay -w 'http=%{http_code} bytes=%{size_download}\n'
jq -r '.protocol, .results.reason, .seed' /tmp/ep3.replay
```

```
{"reason":"complete","scores":[-3.0,-1.0,-15.0,27.0,15.0,15.0],"welfare":52.394}
http=200 bytes=119918
commons-family.replay.v1
complete
1309990201
```

So the game produced a valid episode; the Observatory record for that request (`episode_id`,
`replay_url`, `scores`) and its log shipping (`404 {"detail":"No logs found for job
a7ea70c3-…"}`) were never filled in. That is a platform ingestion/settlement gap on one request, and
it is reported, not worked around. Rounds 2 and 4 ingested normally.

---

## 2. Both champions ranked, fillers absent/Baseline — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```

```
1	daveey-1	commons-family-warden:v3	1030.5304984710244	2	2.0
2	daveey	commons-family-steward:v3	969.4695015289755	2	0.0
```

Full rows (same fetch, 2026-08-24T21:53:00Z), trimmed to the row fields:

```json
[
 {"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
  "score":1030.5304984710244,"score_label":"Elo","rounds_played":2,"episode_wins":2.0,"win_rate":1.0,
  "policy_label":"commons-family-warden:v3"},
 {"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
  "score":969.4695015289755,"score_label":"Elo","rounds_played":2,"episode_wins":0.0,"win_rate":0.0,
  "policy_label":"commons-family-steward:v3"}
]
```

Status: **TRUE** — both champions present (`daveey` with `commons-family-steward:v3`, `daveey-1` with
`commons-family-warden:v3`), each `rounds_played = 2 ≥ 1`. The endpoint returned a **bare JSON array**
(two rows, no third): the filler policies `commons-family-freerider:v3` and
`commons-family-cleaner:v3` are **absent** from the leaderboard, exactly as required, and appear in
episodes only as `Baseline (N)` (check 3, check 4).

---

## 3. Latest round's episode request completed with a replay and the right participants — **TRUE**

```bash
R=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
    | jq -r '[ (if type=="array" then . else .entries end)[]|select(.status=="completed")]|max_by(.round_number).id')
# R=round_4342db17-de90-4f3e-8b1e-5405249ad1d6   (round_number 4 — the latest completed)
EREQ=$(curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}" \
    | jq -r 'if type=="array" then . else .entries end | .[0].id')
# EREQ=ereq_5a0fca58-7c1d-438b-a9b3-2f15ecc03321
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants: [.participants[]|{position,policy_name,player_name,is_filler}], participant_scores}'
```

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/0faa1de2-b956-42c3-b2c5-566c8b4dd61b.replay",
  "participants": [
    {"position":0,"policy_name":"commons-family-steward","player_name":"daveey","is_filler":false},
    {"position":1,"policy_name":"commons-family-warden","player_name":"daveey-1","is_filler":false},
    {"position":2,"policy_name":"commons-family-freerider","player_name":"daveey","is_filler":true},
    {"position":3,"policy_name":"commons-family-cleaner","player_name":"daveey","is_filler":true},
    {"position":4,"policy_name":"commons-family-freerider","player_name":"daveey","is_filler":true},
    {"position":5,"policy_name":"commons-family-freerider","player_name":"daveey","is_filler":true}
  ],
  "participant_scores": [
    {"position":0,"score":0.0},
    {"position":1,"score":4.0},
    {"position":2,"score":8.813},
    {"position":3,"score":7.0},
    {"position":4,"score":17.813},
    {"position":5,"score":20.813}
  ]
}
```

Status: **TRUE** — `status == "completed"`, non-null `replay_url`, seats 0/1 are the champions
`daveey` / `daveey-1` with `is_filler:false`, seats 2–5 are the two filler policies with
`is_filler:true` (they are displayed in the replay as `Baseline`, `Baseline (2)`, `Baseline (3)`,
`Baseline (4)` — see check 4's `seats` block).

---

## 4. Replay bytes are valid and show the game — **TRUE**

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/0faa1de2-b956-42c3-b2c5-566c8b4dd61b.replay" \
     -o /tmp/ep.replay -w 'http=%{http_code} bytes=%{size_download}\n'
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .results.reason' /tmp/ep.replay
```

```
http=200 bytes=112623
strict UTF-8 JSON: ok
commons-family.replay.v1
complete
```

Manifest protocol expected `commons-family.replay.v1` — **match**. `results.reason == "complete"`;
no `deadline` exception needed.

```bash
jq -c '[.events[].kind]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.replay
jq -c '[.rounds[].decisions[]]|group_by(.src)|map({(.[0].src):length})|add' /tmp/ep.replay
jq -c '[.rounds[].decisions[]|select(.slot==0 or .slot==1)]|group_by(.src)|map({(.[0].src):length})|add' /tmp/ep.replay
jq -r '[.rounds[].decisions[]|select(.src|startswith("fallback"))]|length' /tmp/ep.replay
jq -r '[.rounds[].decisions[]|select(.src=="pass")]|length' /tmp/ep.replay
jq -r '[.rounds[].decisions[]|select(.slot==0 or .slot==1)|(.message|length)]|{n:length,min:min,max:max,mean:(add/length)}' /tmp/ep.replay
```

(This coworld records decisions in `.rounds[].decisions[]` with a `src` field, and events in
`.events[]` keyed `kind` — the prompt's `.events[]|select(.type=="decision")` shape does not apply,
so the equivalent queries are used and shown.)

```
{"chat":120,"collapse":1,"decision":120,"episode_end":1,"episode_start":1,"resolve":20,"round_end":20,"round_open":20,"sanction":14}
{"llm":40,"scripted:cleaner":20,"scripted:free_rider":60}
{"llm":40}
0
0
{"n":40,"min":36,"max":140,"mean":106.4}
```

**Champion seats (slots 0 and 1): 40 of 40 decisions `src:"llm"` — zero scripted, zero `fallback:*`,
zero `pass`.** Fallbacks are 0 % of decisions, not a minority — none at all. Champion messages average
106 runes (min 36, max 140 — the design's 140-rune cap), i.e. non-trivial content.

```bash
jq -c '[.seats[]|{slot,alias,name,kind,scripted}]' /tmp/ep.replay
jq -c '.results' /tmp/ep.replay
```

```json
[{"slot":0,"alias":"Cog-B","name":"daveey","kind":"prompt","scripted":""},
 {"slot":1,"alias":"Cog-D","name":"daveey-1","kind":"prompt","scripted":""},
 {"slot":2,"alias":"Cog-F","name":"Baseline","kind":"scripted","scripted":"free_rider"},
 {"slot":3,"alias":"Cog-C","name":"Baseline (2)","kind":"scripted","scripted":"cleaner"},
 {"slot":4,"alias":"Cog-E","name":"Baseline (3)","kind":"scripted","scripted":"free_rider"},
 {"slot":5,"alias":"Cog-A","name":"Baseline (4)","kind":"scripted","scripted":"free_rider"}]
```

```json
{"reason":"complete","rounds":20,"scores":[0.0,4.0,8.813,7.0,17.813,20.813],
 "total_extracted":[9.0,9.0,29.813,7.0,29.813,29.813],"public_effort":[19,21,0,20,0,0],
 "sanctions_given":[9,5,0,0,0,0],"sanctions_received":[0,0,7,0,4,3],
 "welfare":58.439,"residual_value":0.0,"collapse_round":8,"dead_patches":[],
 "fallbacks":[0,0,0,0,0,0],"llm_requests":41,
 "names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"],
 "aliases":["Cog-B","Cog-D","Cog-F","Cog-C","Cog-E","Cog-A"],
 "disconnected":[false,false,false,false,false,false]}
```

The champion seats do **the thing the game is about**: they carry essentially all the public effort
(`public_effort` 19 and 21 of the 60 total; the three free-riders contribute 0) and they are the only
seats that sanction (`sanctions_given` 9 and 5; all others 0), while the free-riders absorb the
sanctions (`sanctions_received` 7/4/3). `collapse_round: 8` is a **field**, not a `reason` — the
episode still ended `complete` after all 20 rounds, exactly as the design specifies.

Status: **TRUE** — valid strict-parser UTF-8 JSON, protocol match, `reason: "complete"`, champion
decisions 100 % LLM with substantive content, zero fallbacks.

---

## 5. Hosted game log — **TRUE** (with one documented, cross-checked platform-probe line)

```bash
curl -sS "$BASE/episode-requests/ereq_5a0fca58-7c1d-438b-a9b3-2f15ecc03321/artifacts/logs" \
     "${AUTH[@]}" "${ELEV[@]}" -o /tmp/c5-logs.raw -w 'http=%{http_code} bytes=%{size_download}\n'
# body is python b'…' reprs under '===== container: <name> =====' headers -> decode per repr
# (ast.literal_eval), then grep the decoded text:
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' <decoded>
```

```
http=200 bytes=94743
container=coworld-init-config  lines=   0 hits=0
container=bedrock-sidecar      lines= 167 hits=0
container=game                 lines= 173 hits=1
    line 9: INFO:     connection rejected (403 Forbidden)
container=worker               lines=   0 hits=0
TOTAL matching lines: 1
```

Counts by pattern across all four decoded containers:

| pattern | hits |
|---|---|
| `falling back` | **0** |
| `LLM provider is unavailable` | **0** |
| `cut off at max_tokens` | **0** |
| `rejected` | 1 (line 9, see below) |

The single hit in context — the pod-local platform harness deliberately opening a websocket with an
invalid token and the game server correctly refusing it, *before* any player connects:

```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     10.1.22.66:38888 - "GET /healthz HTTP/1.1" 200 OK
INFO:     127.0.0.1:53266 - "GET /healthz HTTP/1.1" 200 OK
INFO:     127.0.0.1:53276 - "GET /client/player?slot=0&token=GCtu9O05fq8ee1cfMcY4BA HTTP/1.1" 200 OK
INFO:     ('127.0.0.1', 53286) - "WebSocket /player?slot=0&token=bad" 403     <-- the probe
INFO:     connection rejected (403 Forbidden)                                  <-- line 9, the hit
INFO:     connection closed
INFO:     127.0.0.1:53288 - "GET /client/global HTTP/1.1" 200 OK
INFO:     ('127.0.0.1', 53290) - "WebSocket /global" [accepted]
```

**Cross-check against another live LLM coworld** (as the standard requires for any exception) —
`meadow` (`cow_13d73caa-0370-4ec6-9b9b-e931c686ed04`, canonical, live, the starter this coworld
forks), its latest completed episode `ereq_a11d2a9c-bca5-4998-880b-ef49a60c2033`, decoded and grepped
with the *same* regex:

```
meadow container=coworld-init-config lines=0   hits=0
meadow container=bedrock-sidecar     lines=3   hits=0
meadow container=game                lines=193 hits=1
     9 INFO:     connection rejected (403 Forbidden)
meadow container=worker              lines=0   hits=0
```

Identical line, identical position (line 9), preceded by the identical
`"WebSocket /player?slot=0&token=bad" 403` probe from `127.0.0.1`. It is the platform's episode-start
auth probe, emitted by uvicorn's access log in every FastAPI-lineage coworld — not an LLM
degradation, truncation, capacity or fallback symptom, and its presence is *evidence the game's token
auth works*. (Coworlds that log through their own logger instead of uvicorn — e.g. `raid`,
`cow_978a7941-…`, checked at 21:30Z, 38 game lines, 0 hits — simply do not print the probe.)

Supporting evidence that the LLM path was healthy for this episode — every Bedrock call in the
sidecar returned `ok:true, status_code:200`, 0 errors across 167 lines, e.g.:

```
2026-08-24 21:49:18,957 INFO __main__ bedrock_sidecar_complete {… "episode_request_id":"5a0fca58-7c1d-438b-a9b3-2f15ecc03321",
 "model":"global.anthropic.claude-haiku-4-5-20251001-v1:0","operation":"InvokeModel","ok":true,"status_code":200,
 "latency_ms":2794.26,"error_kind":null,"error_type":null,"message":null,"cache_strategy":"sidecar_v1", …}
```

Status: **TRUE** — zero lines of `falling back`, `LLM provider is unavailable` or
`cut off at max_tokens`. The one `rejected` line is the platform's own bad-token probe being refused,
documented above and cross-checked against a second live coworld (`meadow`) that emits it verbatim.
No `NOT FETCHED`, no inference: both logs were fetched and decoded this run.

---

## 6. The public page uses the static replay path — **TRUE**

**Source used: (b) the API the page reads** — the raw-HTML grep found nothing, because the page is
client-rendered for the iframe (playbook §Featured match / replay route, answered lighthouse
2026-08-22). Both attempts are shown.

```bash
curl -sS "https://softmax.com/commons-family" -o /tmp/c6-page.html -w 'page http=%{http_code} bytes=%{size_download}\n'
grep -o '<iframe[^>]*src="[^"]*"' /tmp/c6-page.html || echo "NO IFRAME IN RAW HTML"
```

```
page http=200 bytes=515872
NO IFRAME IN RAW HTML
```

Featured match, read out of the page's own SSR payload (`state.playlist[0]`, unescaped):

```json
"playlist":[{"episodeId":"88b6fd83-5b85-4e02-b4f2-ef7a33e974da",
 "coworldId":"cow_73578681-ae8b-4ec8-b0ef-9622d639c09a","coworldName":"commons_family",
 "coworldVersion":"0.1.3",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/0faa1de2-b956-42c3-b2c5-566c8b4dd61b.replay",
 "finishedAt":"2026-08-24T21:51:14.119127Z","roundNumber":4,"episodeNumber":1,
 "code":"commons_family.r4.e1",
 "matchup":{"divisionId":"div_83b3f90b-ecc3-4052-9c14-c45173886c79","divisionName":"Competition",
  "first":{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
           "score":1030.5304984710244,"score_label":"Elo","policy_label":"commons-family-warden:v3"}, …
```

A featured match **is** present, and it is this run's latest episode (round 4 — the same replay
verified in check 4). The iframe `src` the page's JS then requests:

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
 -d '{"coworld_id":"cow_73578681-ae8b-4ec8-b0ef-9622d639c09a",
      "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/0faa1de2-b956-42c3-b2c5-566c8b4dd61b.replay"}'
```

```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_73578681-ae8b-4ec8-b0ef-9622d639c09a/sha256%3Ad1ca46483f8fe5aa627a23f46c7b520fdcb968cdfeceeb269b786dc2e818b2fa/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F0faa1de2-b956-42c3-b2c5-566c8b4dd61b.replay&v=2",
  "ready": true
}
```

Status: **TRUE** — the path is
`/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`, with `<sha>` =
`sha256:d1ca46483f8fe5aa627a23f46c7b520fdcb968cdfeceeb269b786dc2e818b2fa` (URL-encoded), byte-for-byte
the `coworld.manifest_sha` in STATE, and `ready: true`. **No `/client/replay` pod URL anywhere.**
(For completeness: the same call at 21:27Z against the then-featured round-2 replay returned the
identical static path with `ready:true`.)

---

## 7. Certification declared the static bundle — **TRUE**

Source read: **the committed `runs/2026-08-24-commons-family/release-result.json`** (the artifact
phase 40 downloaded and committed for release run `32777830776`). It was present; no re-download from
`gh run download` was needed, and `/tmp` was not consulted.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-24-commons-family/release-result.json
```

```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE** — contains `Replay liveness: skipped (static replay bundle declared`.

---

## 8. The viewer, EXECUTED then judged — **TRUE**

*(a) Dispatch against the check-6 iframe `src`* (no other workflow was dispatched; nothing else was
created, triggered, paused or modified anywhere).

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_73578681-ae8b-4ec8-b0ef-9622d639c09a/sha256%3Ad1ca46483f8fe5aa627a23f46c7b520fdcb968cdfeceeb269b786dc2e818b2fa/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F0faa1de2-b956-42c3-b2c5-566c8b4dd61b.replay&v=2'
# dispatch at 2026-08-24T21:53:55Z
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
sleep 12
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 5 \
 | jq -c 'sort_by(.createdAt)|reverse|.[]'
```

```
{"conclusion":"","createdAt":"2026-08-24T21:53:57Z","databaseId":32781916776,"status":"in_progress"}
{"conclusion":"success","createdAt":"2026-08-24T19:43:53Z","databaseId":32769835228,"status":"completed"}
…
```

The new run is **32781916776**, created `21:53:57Z` — two seconds after the dispatch, and newer than
every pre-existing run (found by sorting on `createdAt`, not by taking "the latest" blind).

```bash
gh run watch 32781916776 -R Metta-AI/coworld-builder --exit-status
```

```
✓ main viewer-check · 32781916776
✓ viewer-check in 37s (ID 97605633774)
  ✓ Load the viewer   ✓ Summary   ✓ Upload the evidence   ✓ Fail if the viewer did not load
watch exit=0
```

```bash
gh run download 32781916776 -R Metta-AI/coworld-builder -n viewer-check \
   -D runs/2026-08-24-commons-family/viewer-check
```

```
viewer-smoke.json   1510 bytes
viewer-smoke.png  355721 bytes
smoke-stdout.txt     614 bytes
smoke-stderr.txt       0 bytes
```

*(b) The readouts, verbatim.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/…/viewer-check/viewer-smoke.json
```

```json
{"loaded":true,"ms":2722,"clock":"ROUND 1 OF 20 · WAITING ON 6","scorebug":"Cog-B ▶ 0.0 DAVEEY CLEAN ×0 Cog-D ▶ 0.0 DAVEEY-1 CLEAN ×0 Cog-F ▶ 0.0 CLEAN ×0 Cog-C ▶ 0.0 CLEAN ×0 Cog-E ▶ 0.0 CLEAN ×0 Cog-A ▶ 0.0 CLEAN ×0","feed_lines":338}
```

```bash
jq -c '.signals' runs/…/viewer-check/viewer-smoke.json
```

```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```

```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/…/viewer-check/viewer-smoke.json
```

| scrub | clock readout |
|---|---|
| 0 % | `ROUND 1 OF 20 · WAITING ON 6` |
| 50 % | `ROUND 10 OF 20 · WAITING ON 3` |
| 100 % | `ROUND 20 OF 20 · FINAL` |

```bash
jq -r '.failure // "no failure"' runs/…/viewer-check/viewer-smoke.json
jq -c '{status,loading_text,canvas_text,console_tail}' runs/…/viewer-check/viewer-smoke.json
```

```
no failure
{"status":"REPLAY","loading_text":"LOADING REPLAY…",
 "canvas_text":{"total":3076,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]},
 "console_tail":["[bridge] loading","[bridge] ready"]}
```

Both conditions hold: **`loaded: true`** (first frame in 2 722 ms; `data-replay-loaded="true"` *and*
the `coworld-replay` bridge reached `ready`, `data_replay_error: null`), and the **three clock
readouts differ** (round 1 → round 10 → round 20 · FINAL). A `#scrub` control is present and
responded; 3 076 canvas text draws, 0 outside the canvas, 0 ellipsized.

*(c) What the viewer was asked to draw* — ordered excerpts of `/tmp/ep.replay` (the same round-4
episode), for reconciliation:

```bash
jq -r '.events[]|[.r,(.slot//"-"),.kind,((.text//.message//(.state|tostring))|tostring|.[0:110])]|@tsv' /tmp/ep.replay | head -12
```

```
0	-	episode_start	6 cogs, 20 rounds, one cleanup commons.
0	-	round_open	Round 1 of 20 — everyone decides at once.
0	0	chat	Cog-B says: Round 1: Taking 1 apple (sustainable quota), cleaning 1 unit to maintain regrowth. Apples at 60, p
0	1	chat	Cog-D says: Round 0: taking 1 apple, cleaning 2 units. Norm is 1 each + someone cleans. Let's establish restra
0	2	chat	Cog-F says: I take what I can get.
0	3	chat	Cog-C says: One unit on the commons, every round.
0	4	chat	Cog-E says: I take what I can get.
0	5	chat	Cog-A says: I take what I can get.
0	0	decision	Cog-B picks 1 and cleans the river with 1 — +1.0
0	1	decision	Cog-D picks 1 and cleans the river with 2 — +1.0
0	2	decision	Cog-F picks 3 — +3.0
0	3	decision	Cog-C picks 1 and cleans the river with 1 — +1.0
```

Middle (rounds 8–9, where the commons dies):

```
7	-	round_open	Round 8 of 20 — everyone decides at once.
7	0	chat	Cog-B says: Apples 26—critical collapse risk. A/E/F extracting 9/round unsustainable. B/C/D holding 1+clean. S
7	1	chat	Cog-D says: Round 8: Apples 25.98—critical. F at 21 extracted, 0 cleaning, 4x sanctioned: continuing defection
7	2	chat	Cog-F says: I take what I can get.
7	0	decision	Cog-B picks 1 and cleans the river with 2 — +1.0
7	1	decision	Cog-D picks 1 and cleans the river with 2 — +1.0
7	2	decision	Cog-F picks 3 — +3.0
7	-	resolve	11.0 apples taken, 5 effort on the river.
```

```bash
jq -c '.events[]|select(.kind=="collapse")' /tmp/ep.replay
jq -r '.events[]|select(.kind=="sanction")|[.r,(.slot//"-"),(.text//"")]|@tsv' /tmp/ep.replay | head -5
```

```
{"kind":"collapse","r":8,"text":"The orchard is stripped below recovery — nothing regrows again."}
1	0	Cog-B burns Cog-F: -1.0 / -3.0
2	0	Cog-B burns Cog-E: -1.0 / -3.0
2	1	Cog-D burns Cog-E: -1.0 / -3.0
3	0	Cog-B burns Cog-A: -1.0 / -3.0
4	0	Cog-B burns Cog-F: -1.0 / -3.0
```

Late:

```
19	0	decision	Cog-B rests — +0.0
19	1	decision	Cog-D rests — +0.0
19	2	decision	Cog-F picks 3 — +0.0
19	3	decision	Cog-C cleans the river with 1 — +0.0
19	-	resolve	0.0 apples taken, 1 effort on the river.
19	-	round_end	Round 20 settled — 0.0 taken, 1 of 18 effort units spent on the commons.
19	-	episode_end	Final — 20 rounds played.
```

### Spectator judgment

`viewer-smoke.png` (the 100 %-scrub frame CI captured, committed alongside this file) is **legible and
it shows this game**. Reading the picture: the title bar says `COMMONS FAMILY · ROUND 20 OF 20 ·
FINAL` with a `REPLAY` badge and a `« LOG` toggle at the right; under it a six-seat scorebug —
`Cog-B 0.0 DAVE… CLEAN ×19`, `Cog-D 4.0 DAVE…-1 CLEAN ×21`, then `Cog-F 8.8 CLEAN ×0`, `Cog-C 7.0
CLEAN ×20`, `Cog-E 17.8 CLEAN ×0`, `Cog-A 20.8 CLEAN ×0` — so a spectator can see at a glance both who
is winning *and why the winner is winning* (the two zero-cleaning free-riders top the table while the
champions carry the cleanup). A status strip reads `CLEAN UP · APPLES 0 · POLLUTION 70% · DIES BELOW
10 · ORCHARD DEAD`. The world panel shows the six cogs with their scores beneath them, chat bubbles
still readable (`"I take what I can get."` on the free-riders; `"Orchard dead. Game over next round.
Defectors won; cooperators paid the cost."` on Cog-B), and the banner `ORCHARD DEAD — NOTHING
REGROWS`. Below the world is an apples/pollution momentum graph whose green apples line falls to zero
around the middle of the run while the dashed orange pollution line climbs — which is exactly the
recorded episode: `collapse` at `r: 8`, `residual_value: 0.0`, `pollution 70%`. At the bottom sit the
transport strip with per-round event ticks, the play control and the tick counter `317 / 317`. The
centre endcard reads `FINAL — 20 ROUNDS · WELFARE 58.4 · THE COMMONS DID NOT SURVIVE` over
`Cog-A TOOK THE MOST` and a ranked table (`TOOK / COMMONS / SCORE`) whose numbers match
`results.scores` `[0.0, 4.0, 8.813, 7.0, 17.813, 20.813]` and `results.welfare` `58.439` exactly, with
`daveey-1` and `daveey` named in the policy column.

It is not empty, not frozen and not unreadable: the three scrub readouts advance round 1 → 10 → 20,
338 feed lines are present, and the first frame arrived in 2.7 s. The chrome **is the starter's
chrome** — the same transport strip, scrubber with momentum graph, six-seat scorebug and centred
endcard as paintbot/raid/bullwhip; the deltas are content, not product (the apples/pollution series
and the `TOOK / COMMONS` columns), so this is not the cogame-gridlock "looks like a different
product" failure.

Two **legibility observations for phase 30** (neither blocking, neither part of any verdict): (i) in
the endcard's `POLICY` column the four filler seats print their alias (`Cog-A`, `Cog-E`, `Cog-F`,
`Cog-C`) rather than `Baseline (N)`, while the champions correctly print `daveey` / `daveey-1` — the
scorebug has the same asymmetry (champion names shown, baselines blank); (ii) the CI screenshot is
taken at 100 % scrub, so the endcard overlay dims the world behind it — a spectator dropping in at
the end sees the summary first, which is probably intended but is worth a designer's eye.

Status: **TRUE** — `loaded: true` **and** three differing clock readouts, from the artifact of run
`32781916776`, dispatched by this verifier at 21:53:55Z and downloaded to
`runs/2026-08-24-commons-family/viewer-check/`.

---

## Summary table

| # | Item | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** (rounds 3 & 4 created after fillers; 2 & 4 scored; round-1 failure quoted; round-3 platform settlement anomaly documented) |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** (daveey 969.47 / daveey-1 1030.53, `rounds_played` 2 each; no filler rows) |
| 3 | Latest round's episode request completed with replay + right participants | **TRUE** (`ereq_5a0fca58-…`, round 4) |
| 4 | Replay bytes valid, protocol match, shows the game | **TRUE** (`commons-family.replay.v1`, `complete`, 40/40 champion decisions `llm`, 0 fallbacks) |
| 5 | Hosted game log clean | **TRUE** (0 fallback/unavailable/max_tokens; 1 `rejected` = platform bad-token probe, cross-checked against live `meadow`) |
| 6 | Public page uses the static replay path | **TRUE** (static `/v2/coworlds/replays/static/<cow>/<manifest sha>/index.html?replay=…`, `ready:true`, featured match present) |
| 7 | Certification declared the static bundle | **TRUE** (committed `release-result.json`) |
| 8 | Viewer executed and judged | **TRUE** (`loaded:true`, 2 722 ms, clocks round 1 → 10 → 20·FINAL, run `32781916776`) |

## STATE values for the coordinator

```
verify.rounds            = [2, 3, 4]        # completed; 3 and 4 created after fillers, 2 and 4 scored by the ladder
verify.replay            = "https://softmax-public.s3.amazonaws.com/replays/0faa1de2-b956-42c3-b2c5-566c8b4dd61b.replay"
verify.iframe_static     = true
verify.viewer_check_run  = "32781916776"
```
