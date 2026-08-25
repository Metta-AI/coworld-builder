# VERIFY — collab-cooking   (2026-08-25T09:15Z)

Verdict: **5 items false** (1 TRUE, 2 TRUE, 3 FALSE, 4 FALSE, 5 FALSE, 6 FALSE, 7 TRUE, 8 FALSE)

**Headline.** The ladder is running and the leaderboard is right, but **no episode has ever
produced a replay**. Every league episode dies at container start:
`error_type: "game_unhealthy"`, `error: "Game container exited with code 1"` — three consecutive
rounds (2, 3, 4), same variant, dead within seconds of dispatch every time. So there is no replay to validate, no
game log to grep, no featured match on the public page and no live iframe to render. Root cause
is diagnosed and reproduced locally at the bottom of this file: **every variant declares
`max_steps: 900`, and this game's own `create_app()` cannot build a mission that long** — the
per-ticket resource encoding scales with `max_steps` and blows past mettagrid's 256-feature-id
cap at `max_steps >= 640`. The certification fixture uses `max_steps: 480`, which is why
certification passed and the ladder cannot.

Environment for every call below:

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")   # value never printed
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_592e6ed0-3f01-4084-bb90-75ace0db0063
D=div_027403b9-3208-43b8-b2e6-499bd18681e5
COW=cow_127a462a-6f7f-457f-aa7b-95652aae11d4
```

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end
          | .[] | [.round_number,.id,.status,(.created_at),(.completed_at),(.error//"-")]|@tsv'
```

```
4	round_f48e29f0-a9f2-4002-9739-1469bb48182d	completed	2026-08-25T09:10:50.809299Z	2026-08-25T09:11:12.188592Z	-
3	round_31a882c6-ee31-42b1-a1e2-8870cc0ab6b7	completed	2026-08-25T08:55:50.415385Z	2026-08-25T08:56:42.446039Z	-
2	round_201d9765-4ea3-4391-9393-b486cc36eb54	completed	2026-08-25T08:40:49.983322Z	2026-08-25T08:42:33.787355Z	-
1	round_fe61851d-5d71-41d6-853f-8eba11675499	failed	2026-08-25T08:40:01.020101Z	2026-08-25T08:40:01.325872Z	Temporal RoundWorkflow failed before settling the round.
```

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
```

```
3
```

Round 1's error verbatim: `Temporal RoundWorkflow failed before settling the round.` — the
auto-round that fired on unpause before the filler registration landed (phase 50's log line
`2026-08-25T08:42:05Z 50 rounds: r1 failed (Temporal RoundWorkflow — auto-round raced the filler
registration on unpause)`); it is `failed`, so it does not count.

Fillers are registered, and rounds 2–4 each seated both of them, which puts all three counted
rounds after the registration:

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}" | jq -c .
```

```json
{"filler_policy_versions":[{"policy_version_id":"6f226863-ecbf-4823-9f57-829a436e7c6e","policy_id":"63b52580-0f48-43ea-8893-497e92a5b7af","policy_name":"collab-cooking-brigade","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},{"policy_version_id":"fb542fe5-7dfa-4e8e-ab9c-1ca19751d633","policy_id":"3901cad8-a08e-475f-a590-02e6533bfd49","policy_name":"collab-cooking-passer","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```

Round 2's entrant attributions (both champions, from the same fetch):

```json
{"round_number":2,"created_at":"2026-08-25T08:40:49.983322Z","entrants":[
 {"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player","policy_version_id":"b26fe220-13ee-417f-8b32-45b54be54ee4","league_policy_membership_id":"lpm_3e5ad34a-6fad-4cde-972a-7ad8792aad5b"},
 {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","subject_type":"player","policy_version_id":"9ef2fbd1-b439-4926-a110-eede864f49ac","league_policy_membership_id":"lpm_8f405338-6594-4fd1-84b8-ceae0e52a3c6"}]}
```

Status: **TRUE** — rounds 2, 3 and 4 are `completed` (3 ≥ 2), all after the fillers were set
(each of their episode requests seats `collab-cooking-brigade`/`collab-cooking-passer` with
`is_filler: true` — see item 3). **Caveat for the judge:** "round completed" here means the
ladder settled the round, not that a match was played — all three rounds settled with a *failed*
episode (items 3–5).

---

## 2. Both champions ranked — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```

```
1	daveey	collab-cooking-expo:v1	1000.0	3	0.0
2	daveey-1	collab-cooking-linecook:v1	1000.0	3	0.0
```

Full first row, unedited:

```json
{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1000.0,"score_label":"Elo","score_value_type":"integer","rounds_played":3,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"collab-cooking-expo:v1","recent_rounds":null}
```

Status: **TRUE** — both `daveey` (`collab-cooking-expo:v1`) and `daveey-1`
(`collab-cooking-linecook:v1`) are ranked with `rounds_played = 3 ≥ 1`; the two filler policies
appear nowhere in the list. **Caveat:** both scores are still the `initial_rating` 1000.0 with
`episode_wins: 0.0` — the ladder credited three rounds whose episodes never ran, so the ranking
is real but carries no played result.

---

## 3. Latest completed round's episode request completed with a replay — **FALSE**

```bash
R=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
    | jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|max_by(.round_number).id')
# R=round_f48e29f0-a9f2-4002-9739-1469bb48182d   (round 4)
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)|map({id,status,replay_url})'
```

```json
[{"id":"ereq_7a3dbe01-1662-410f-8ab7-95ea7a2f8058","status":"failed","replay_url":null}]
```

```bash
curl -sS "$BASE/episode-requests/ereq_7a3dbe01-1662-410f-8ab7-95ea7a2f8058" "${AUTH[@]}" \
 | jq '{status, replay_url, error_type, error, variant_name,
        participants:[.participants[]|{position,policy_name,player_name,is_filler}], participant_scores}'
```

```json
{
  "status": "failed",
  "replay_url": null,
  "error_type": "game_unhealthy",
  "error": "Game container exited with code 1",
  "variant_name": "Open Kitchen",
  "participants": [
    {"position": 0, "policy_name": "collab-cooking-expo",     "player_name": "daveey",   "is_filler": false},
    {"position": 1, "policy_name": "collab-cooking-linecook", "player_name": "daveey-1", "is_filler": false},
    {"position": 2, "policy_name": "collab-cooking-passer",   "player_name": "daveey",   "is_filler": true},
    {"position": 3, "policy_name": "collab-cooking-brigade",  "player_name": "daveey",   "is_filler": true}
  ],
  "participant_scores": []
}
```

The same failure on every counted round — all episode requests ever issued for this coworld:

```bash
curl -sS "$BASE/episode-requests?coworld_id=$COW&limit=50" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)|.[]|[.id,.created_at,.status,(.error_type//"-"),(.error//"-"),(.variant_name//"-")]|@tsv'
```

```
ereq_7a3dbe01-1662-410f-8ab7-95ea7a2f8058	2026-08-25T09:10:51.211192Z	failed	game_unhealthy	Game container exited with code 1	Open Kitchen
ereq_ce167142-be9f-498f-9ec9-74248ac21af7	2026-08-25T08:55:50.824843Z	failed	game_unhealthy	Game container exited with code 1	Open Kitchen
ereq_b5042a23-1f40-4ee0-a387-ebb0706639e1	2026-08-25T08:40:50.344129Z	failed	game_unhealthy	Game container exited with code 1	Open Kitchen
ereq_c0e0e4dc-dd6d-4d89-9d99-3d4cdcbf7367	2026-08-25T08:29:47.542640Z	completed	-	-	-
ereq_30eee579-863b-4246-8e5c-f7330c216ce9	2026-08-25T08:29:47.536190Z	completed	-	-	-
ereq_3e56317b-eed1-40c8-89af-9d984be81c59	2026-08-25T08:29:47.529432Z	completed	-	-	-
ereq_eefd6281-4cde-4d50-a908-8057a41ccb5a	2026-08-25T08:29:47.523431Z	completed	-	-	-
ereq_f37248b5-ff08-4e58-a574-bb9cacfb5882	2026-08-25T08:29:47.518913Z	completed	-	-	-
```

The three `failed` rows are the league rounds (variant **Open Kitchen**); the five `completed`
rows at 08:29:47 are the release run's certification/smoke episodes (`variant_name: null`,
`layout: "cramped"`, `policy_name: "coworld-smoke/cow_127a462a-…"`).

Timing of the crash (round 4's request, same fetch):

```bash
curl -sS "$BASE/episode-requests/ereq_7a3dbe01-1662-410f-8ab7-95ea7a2f8058" "${AUTH[@]}" \
 | jq -c '{created_at,dispatched_at,running_at,completed_at,cost_usd,job_id}'
```

```json
{"created_at":"2026-08-25T09:10:51.211192Z","dispatched_at":"2026-08-25T09:10:51.475127Z","running_at":null,"completed_at":"2026-08-25T09:11:10.806979Z","cost_usd":0.001126,"job_id":"38a14e05-4571-48d6-9dff-ac54e6113753"}
```

`running_at` is **null** — this episode never reached the running state at all; it went from
dispatch to failure in 19 s. Round 2's request did briefly reach running
(`running_at 2026-08-25T08:42:16.75`, `completed_at 2026-08-25T08:42:23.78` — dead ~7 s later),
which is still far short of `player_connect_timeout_seconds: 120`. The seats are correct
(`daveey`, `daveey-1`, two fillers); the container just never came up.

**Not a platform outage** — the same window, other live coworlds:

```bash
for c in cow_d5e3a72d-bae0-4418-bb3e-e39f2c5cc81d cow_e5c32ad5-8696-4d4f-8a39-458baa8c2a3e; do
  curl -sS "$BASE/episode-requests?coworld_id=$c&limit=8" "${AUTH[@]}" \
   | jq -r '(if type=="array" then . else .entries end)|.[]|[.created_at,.status,(.error_type//"-")]|@tsv'; done
```

```
=== cooperative_hunting cow_d5e3a72d-bae0-4418-bb3e-e39f2c5cc81d ===
2026-08-25T08:33:41.514326Z	completed	-
2026-08-25T08:18:41.250085Z	completed	-
2026-08-25T08:03:38.385282Z	completed	-
2026-08-25T07:48:37.953287Z	completed	-
2026-08-25T07:33:35.948426Z	completed	-
=== coins cow_e5c32ad5-8696-4d4f-8a39-458baa8c2a3e ===
2026-08-25T08:42:49.550028Z	running	-
2026-08-25T08:42:49.540920Z	completed	-
2026-08-25T08:42:49.530582Z	completed	-
2026-08-25T08:42:49.522399Z	completed	-
2026-08-25T08:27:48.697255Z	completed	-
```

Status: **FALSE** — `status: "failed"`, `replay_url: null`. Participants *are* correct
(`daveey`, `daveey-1`, and both fillers flagged `is_filler: true`), so the seating half of the
requirement holds; the episode itself never ran. Deterministic across rounds 2, 3 and 4, and
collab-cooking-specific (cooperative_hunting and coins completed episodes in the same minutes).

---

## 4. Replay bytes valid and showing the game — **FALSE (NOT FETCHED)**

There is no replay to fetch. Both routes to the round-4 episode's bytes:

```bash
curl -sS "$BASE/episode-requests/ereq_7a3dbe01-1662-410f-8ab7-95ea7a2f8058" "${AUTH[@]}" | jq -r '.replay_url'
```

```
null
```

```bash
curl -sS -w "\nHTTP %{http_code}\n" "$BASE/episode-requests/ereq_b5042a23-1f40-4ee0-a387-ebb0706639e1/artifacts/replay" "${AUTH[@]}" "${ELEV[@]}"
curl -sS -w "\nHTTP %{http_code}\n" "$BASE/episode-requests/ereq_b5042a23-1f40-4ee0-a387-ebb0706639e1/artifacts/results" "${AUTH[@]}" "${ELEV[@]}"
```

```
{"detail":"No replay found for job 879fe498-5c6c-4144-8721-62c289aec73a"}
HTTP 404
{"detail":"No results found for job 879fe498-5c6c-4144-8721-62c289aec73a"}
HTTP 404
```

Status: **FALSE — NOT FETCHED.** `replay_url` is `null` on all three league episodes and the
artifact endpoints 404 (`No replay found for job …`). No `protocol`, no `results.reason`, no
plan events exist for a league match.

### 4b. Supplementary (NOT a substitute for item 4): the certification replay does parse

The only collab_cooking replay bytes in existence are the release run's smoke episode. Fetched
fresh this run, and reported here only because it is the input to item 8's render and it shows
the *format* is sound:

```bash
U=$(curl -sS "$BASE/episode-requests/ereq_c0e0e4dc-dd6d-4d89-9d99-3d4cdcbf7367" "${AUTH[@]}" | jq -r .replay_url)
# https://softmax-public.s3.amazonaws.com/replays/ad24f497-8ea8-4e68-90bb-64a70644db3e.replay
curl -sSL "$U" -o /tmp/smoke.replay -w "HTTP %{http_code} bytes %{size_download}\n"
jq -e . /tmp/smoke.replay >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.format, .protocol, .results.reason, (.ticks|length)' /tmp/smoke.replay
```

```
HTTP 200 bytes 252380
strict UTF-8 JSON: ok
collab-cooking/1
collab-cooking.replay.v1
complete
480
```

```bash
jq -c '.results' /tmp/smoke.replay
```

```json
{"game":"collab_cooking","protocol":"collab-cooking.results.v1","reason":"complete","layout":"cramped","steps":480,"dishes":12,"scores":[12.0,12.01,12.01,12.1],"delivered":[0,1,1,10],"served_by_recipe":{"salad":4,"soup":5,"fries":3},"orders_arrived":27,"orders_expired":15,"burned":{"pot":1,"fryer":1},"blocked_moves":[48,77,270,110],"handoffs":[0,0,0,0],"names":["coworld-smoke/cow_127a462a-6f7f-457f-aa7b-95652a","coworld-smoke/cow_127a462a-6f7f-457f-aa7b-95652a","coworld-smoke/cow_127a462a-6f7f-457f-aa7b-95652a","coworld-smoke/cow_127a462a-6f7f-457f-aa7b-95652a"],"aliases":["Cog-B","Cog-A","Cog-C","Cog-D"],"seat_kinds":["prompt","prompt","prompt","prompt"],"cross_play":false,"disconnected":[false,false,false,false],"fallbacks":[1,1,0,1],"llm_requests":7}
```

```bash
# schema-adapted from the phase prompt: decisions are `plan` events inside ticks[].ev[]
jq -r '[.ticks[]|.ev[]?|select(.ev=="plan")]|group_by(.src)|map({src:.[0].src,n:length})|@json' /tmp/smoke.replay
jq -r '[.ticks[]|.ev[]?|select(.ev=="fallback")]|length' /tmp/smoke.replay
```

```
[{"src":"llm","n":1}]
3
```

This confirms `protocol == "collab-cooking.replay.v1"` matches the manifest and
`results.reason == "complete"` is reachable — but it is a **smoke** episode
(`cross_play: false`, four identical `coworld-smoke/...` seats, 1 llm plan vs 3 fallbacks, 480
ticks not 900). It says nothing about whether the champions play well, and it cannot satisfy
item 4, which asks for the latest completed round's replay.

---

## 5. Hosted game log clean — **FALSE**

```bash
curl -sS "$BASE/episode-requests/ereq_7a3dbe01-1662-410f-8ab7-95ea7a2f8058/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" \
 | tee /tmp/logs.txt
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.txt || echo CLEAN
wc -c /tmp/logs.txt
```

```
Error type: game_unhealthy

Game container exited with code 1
--- grep:
CLEAN
61 /tmp/logs.txt
```

Identical 61-byte body for rounds 2 and 3 (`ereq_b5042a23…`, `ereq_ce167142…`). There are no
`===== container: … =====` sections and no python `b'…'` reprs — the game container produced no
captured output at all. Probes for a fuller log all fail:

```
GET …/artifacts/logs?container=game  -> HTTP 200, same 61 bytes
GET …/episode-requests/<ereq>/logs   -> HTTP 404 {"detail":"Not Found"}
GET …/jobs/<job_id>/logs             -> HTTP 404 {"detail":"Not Found"}
GET …/jobs/<job_id>                  -> HTTP 404 {"detail":"Not Found"}
```

Status: **FALSE.** The grep is *literally* `CLEAN`, but only because there is no game log to
grep: the body is a 61-byte crash notice, and the episode it describes never started. I will not
record a pass off a degenerate match — the check asks that the hosted game log be clean, and no
hosted game log exists. No `LLM provider is unavailable` / `max_tokens` / `rejected` evidence was
found anywhere, so this is **not** the Bedrock-capacity symptom; cooperative_hunting and coins
were completing episodes in the same window (item 3).

---

## 6. Public page uses the static replay path — **FALSE**

Source A — raw HTML (the documented grep):

```bash
curl -sS "https://softmax.com/collab-cooking" -o /tmp/page.html -w "page HTTP %{http_code} bytes %{size_download}\n"
grep -o '<iframe[^>]*src="[^"]*"' /tmp/page.html || echo "(no match)"
```

```
page HTTP 200 bytes 538034
(no match)
```

Per `playbooks/observatory-api.md` §Featured match, an empty grep is *unknown*, not a failure —
so I read the SSR payload and the page copy from the same fetched bytes:

```bash
grep -o 'playlist\\":\[[^]]*\]' /tmp/page.html
grep -o 'No featured match yet[^<]*' /tmp/page.html
```

```
playlist\":[]
No featured match yet
```

Page copy in context: `>No featured match yet</h1><div …>The next round is expected in ~11m.</div>`

Source B — the coworld detail API:

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)[]|select(.name=="collab_cooking")|{id,name,version,canonical,replay_viewer,featured_match}'
```

```json
{"id":"cow_127a462a-6f7f-457f-aa7b-95652aae11d4","name":"collab_cooking","version":"0.1.1","canonical":true,"replay_viewer":null,"featured_match":null}
```

Status: **FALSE.** Sources used: the raw HTML **and** its SSR payload (`state.playlist`), plus
the `/coworlds` API. `playlist` is `[]` and the page renders "No featured match yet", so there is
**no iframe `src` at all** — neither a static one nor a `/client/replay` pod URL. The cause is
upstream, not a routing defect: a featured match needs a completed episode with a replay, and
there are none (item 3).

For completeness, the static route itself resolves for this coworld — the page's own call, made
by hand against the certification replay:

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
 -d '{"coworld_id":"cow_127a462a-…","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/ad24f497-….replay"}'
```

```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_127a462a-6f7f-457f-aa7b-95652aae11d4/sha256%3Ae577c452bdb928afc16b6872016540e14c0b9c65eed4a00ca564871c8bd32c7f/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fad24f497-8ea8-4e68-90bb-64a70644db3e.replay&v=2","ready":true}
```

`ready: true`, path ends `/index.html`, `<sha>` is the coworld's manifest hash
`sha256:e577c452bdb928afc16b6872016540e14c0b9c65eed4a00ca564871c8bd32c7f` — i.e. **when** a
league replay exists the page will get a static src, not a pod URL. That is a property of the
route, not evidence for item 6, which requires a featured match on the page. Item 6 stays FALSE.

---

## 7. Certification declared the static bundle — **TRUE**

Source: the committed artifact `runs/2026-08-25-collab-cooking/release-result.json` (downloaded
and committed by phase 40 from release run 32826526376). It was present, so no re-download was
needed.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-25-collab-cooking/release-result.json
```

```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE** — contains `Replay liveness: skipped (static replay bundle declared`.

---

## 8. Spectator judgment — the viewer is EXECUTED, then judged — **FALSE**

**Why FALSE:** item 8 renders "the iframe `src` from item 6". Item 6 produced **no iframe src** —
`playlist: []`, `featured_match: null` — because no league episode has a replay. There is
nothing a spectator arriving at `softmax.com/collab-cooking` can watch, so the spectator
experience does not exist and item 8 cannot be true.

I did dispatch and download a real render anyway, so the coordinator knows whether the *viewer*
is also broken or only the game. **The URL rendered is the static route built from the
certification smoke replay (`ad24f497-…`), not a featured league match** — a clearly-labelled
substitute, not the item-6 src.

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_127a462a-6f7f-457f-aa7b-95652aae11d4/sha256%3Ae577c452bdb928afc16b6872016540e14c0b9c65eed4a00ca564871c8bd32c7f/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fad24f497-8ea8-4e68-90bb-64a70644db3e.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
# dispatched 2026-08-25T09:05:42Z; new run found by sorting createdAt, not by "latest":
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:3]|.[]|[.databaseId,.createdAt,.status]|@tsv'
```

```
32830082226	2026-08-25T09:05:44Z	in_progress      <- created after the 09:05:42Z dispatch
32825902427	2026-08-25T08:18:04Z	completed
32822191156	2026-08-25T07:33:38Z	completed
```

```bash
gh run watch 32830082226 -R Metta-AI/coworld-builder --exit-status   # -> green, 1m2s, rc=0
gh run download 32830082226 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-25-collab-cooking/viewer-check
```

Artifact committed at `runs/2026-08-25-collab-cooking/viewer-check/`
(`viewer-smoke.json`, `viewer-smoke.png`, `smoke-stdout.txt`, `smoke-stderr.txt` — 0 bytes).

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-25-collab-cooking/viewer-check/viewer-smoke.json
```

```json
{"loaded":true,"ms":2725,"clock":"TICK 1 OF 480 1 ORDER LIVE","scorebug":"Cog-B coworld-smoke/cow_127a462a-6f7f-457f-aa7b-95652a working ▶ 0 Cog-C coworld-smoke/cow_127a462a-6f7f-457f-aa7b-95652a working ▶ 0 TICK 1 OF 480 1 ORDER LIVE Cog-A coworld-smoke/cow_127a462a-6f7f-457f-aa7b-95652a working ▶ 0 Cog-D coworld-smoke/cow_127a462a-6f7f-457f-aa7b-95652a working ▶ 0","feed_lines":0}
```

```bash
jq -c '.signals' runs/2026-08-25-collab-cooking/viewer-check/viewer-smoke.json
jq -r '.failure // "no failure"' runs/2026-08-25-collab-cooking/viewer-check/viewer-smoke.json
```

```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["ready"],"bridge_ready":true,"bridge_error":[]}
```

```
no failure
```

Three clock readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub | clock readout |
|---|---|
| 0 % | `TICK 1 OF 480 1 ORDER LIVE` |
| 50 % | `TICK 258 OF 480 2 ORDERS LIVE · 1 EXPIRING` |
| 100 % | `TICK 480 OF 480 0 ORDERS LIVE` |

`console_tail`: `["[bridge] ready"]`. `canvas_text`: `{"total":0,"outside":0,"ellipsized":0,"never_inside":0}`.

Replay events the viewer was asked to draw (schema-adapted; `/tmp/smoke.replay` from item 4b).
Event census first, so the selects below are not cherry-picked:

```bash
jq -r '[.ticks[]|.ev[]?|.ev]|group_by(.)|map({ev:.[0],n:length})|@json' /tmp/smoke.replay
```

```json
[{"ev":"blocked","n":505},{"ev":"chop_done","n":29},{"ev":"chop_start","n":29},{"ev":"deposit","n":91},{"ev":"episode_end","n":1},{"ev":"episode_start","n":1},{"ev":"fallback","n":3},{"ev":"fry_burn","n":1},{"ev":"fry_clear","n":4},{"ev":"fry_ready","n":4},{"ev":"fry_start","n":4},{"ev":"order_arrive","n":27},{"ev":"order_expire","n":15},{"ev":"pickup","n":117},{"ev":"plan","n":1},{"ev":"plate_up","n":12},{"ev":"pot_burn","n":1},{"ev":"pot_clear","n":6},{"ev":"pot_load","n":7},{"ev":"pot_ready","n":6},{"ev":"pot_start","n":6},{"ev":"serve","n":12},{"ev":"wash_done","n":12},{"ev":"wash_start","n":12}]
```

```bash
jq -r '.ticks[]|.t as $t|(.ev[]?|select(.ev=="plan" or .ev=="serve" or .ev=="order_expire" or .ev=="episode_start")|[$t,(.alias//.slot//"-"),.ev,(.say//.recipe//.dish//"")]|@tsv)' /tmp/smoke.replay | head -8
jq -r '.ticks[]|.t as $t|(.ev[]?|select(.ev=="plan" or .ev=="serve" or .ev=="episode_end")|[$t,(.alias//.slot//"-"),.ev,(.say//.recipe//.dish//"")]|@tsv)' /tmp/smoke.replay | tail -8
```

```
=== early ===
1	-	episode_start	
50	-	order_expire	soup
62	Cog-D	serve	soup
68	-	order_expire	salad
79	Cog-C	serve	salad
89	Cog-D	serve	fries
114	Cog-C	plan	Taking soup order - fetching ingredients
123	Cog-D	serve	soup
=== late ===
161	Cog-D	serve	soup
178	Cog-D	serve	fries
254	Cog-A	serve	fries
265	Cog-D	serve	soup
301	Cog-D	serve	salad
328	Cog-D	serve	salad
351	Cog-D	serve	soup
480	-	episode_end	
```

`results` (repeated from 4b for the reconciliation): `dishes: 12`, `served_by_recipe
{salad 4, soup 5, fries 3}`, `orders_arrived 27`, `orders_expired 15`, `burned {pot 1, fryer 1}`,
`delivered [0,1,1,10]`.

**Spectator judgment.** The viewer itself is alive and legible — this is *not* a
cogame-lantern-class dead page. `loaded: true` after 2725 ms via both signals
(`data-replay-loaded="true"` and the `coworld-replay` bridge's `ready`), and the three clock
readouts differ and advance monotonically (tick 1 → 258 → 480), so it is a replay and not a
screenshot. In `viewer-smoke.png` (captured at the end of the scrub sweep, tick 480/480) I can
see the starter's chrome, essentially the coworld-ctf layout: a four-seat scorebug across the top
(Cog-B 0, Cog-A 1, Cog-C 1, Cog-D 10, each with its policy name and a `working ▶` state), the
big centred `TICK 480 OF 480 / 0 ORDERS LIVE` transport clock, and beneath it the **dish ticker**
— `12 DISHES` followed by the last six served-dish chips reading `…og-D · t178`,
`fries · Cog-A · t254`, `soup · Cog-D · t265`, `salad · Cog-D · t301`, `salad · Cog-D · t328`,
`soup · Cog-D · t351` and a `HEAT` badge. Those chips match the replay's `serve` events
tick-for-tick against the `tail -8` above (t178 Cog-D, t254 fries Cog-A, t265 soup Cog-D, t301
and t328 salad Cog-D, t351 soup Cog-D — the t178 chip's recipe word is cut off at the panel's
left edge, where the record says `fries`), so the picture and the record agree and the ticker
demonstrably advances. Below that sits the four-column say-band, three columns reading
`Cog-B/Cog-A/Cog-D no word yet` and one reading `Cog-C Taking soup order - fetching ingredients`
— the replay's single `plan` event (t114, `src: "llm"`), wrapped over two lines and not clipped (`ellipsized: 0`), which is the phase-30 R2-O1 fix holding under a real render. The
kitchen grid is drawn but dimmed behind the endcard overlay: `12 DISHES SERVED`, the tagline
`THE WHOLE BRIGADE SHARES ONE SCORE`, `15 tickets expired · 1 pot burned · 1 fryer burned`, and a
1–4 placement list (Cog-D 10, Cog-A 1, Cog-C 1, Cog-B 0) — matching `results.delivered
[0,1,1,10]` and `orders_expired 15`, `burned {pot 1, fryer 1}` exactly. The bottom strip is the
familiar transport row (restart, step-back, play, +5s, step, loop, fast-forward, `spoilers`,
`480 / 480`, speed 1×–16×) over the scrubber with the per-ticket momentum graph and a `LIVES LEAD`
label. Legible, on-brand, and the game is recognisable: you can read who cooked what, when, and
why the team scored 12.

Two honest caveats. First, `feed_lines: 0` — the event feed panel is visibly populated in the
screenshot (bottom-right, "Cog-D leaves veg on a counter", "a salad ticket expired · nobody served
it", …) but the smoke probe counted zero rows, so its selector does not match this shell's feed;
that is a probe/legibility note for phase 30, not a render failure. Second and decisively: **this
is not this coworld's spectator experience.** It is the certification smoke episode — four
identical `coworld-smoke/...` seats, `cross_play: false`, one LLM plan against three fallbacks,
480 ticks. A spectator visiting `softmax.com/collab-cooking` right now sees "No featured match
yet", because the champions have never played a single tick. The viewer is ready; the game is
not.

---

## Diagnosis (not a definition-of-done item — offered so the coordinator can act)

Fetched fact: the certification episodes (08:29:47) **completed** on the same image, and the
three league episodes (08:40, 08:55, 09:10) all died. The only difference between them is the
`game_config`:

```bash
curl -sS "$BASE/episode-requests/ereq_c0e0e4dc-dd6d-4d89-9d99-3d4cdcbf7367" "${AUTH[@]}" | jq -c '{variant_name,status,game_config}'   # certification
curl -sS "$BASE/episode-requests/ereq_7a3dbe01-1662-410f-8ab7-95ea7a2f8058" "${AUTH[@]}" | jq -c '{variant_name,status,game_config}'   # league round 4
```

```json
{"variant_name":null,"status":"completed","game_config":{"seed":20260826,"layout":"cramped","players":[{"name":"Cog One"},{"name":"Cog Two"},{"name":"Cog Three"},{"name":"Cog Four"}],"max_steps":480,"num_agents":4,"step_seconds":0.02,"plan_interval_steps":240,"policy_action_timeout_seconds":0.3,"player_connect_timeout_seconds":90}}
{"variant_name":"Open Kitchen","status":"failed","game_config":{"seed":20260825,"layout":"open-kitchen","players":[{"name":"Cog One"},{"name":"Cog Two"},{"name":"Cog Three"},{"name":"Cog Four"}],"max_steps":900,"num_agents":4,"step_seconds":0.2,"plan_interval_steps":50,"player_connect_timeout_seconds":120}}
```

Deltas: `layout` cramped → open-kitchen, `max_steps` **480 → 900**, `step_seconds` 0.02 → 0.2,
`plan_interval_steps` 240 → 50, `policy_action_timeout_seconds` 0.3 → absent,
`player_connect_timeout_seconds` 90 → 120.

Reproduced locally from a **read-only** clone of `Metta-AI/cogame-collab-cooking@8f6bca0` (no
edits, no pushes), calling the game's own `create_app()` with the two configs plus four dummy
tokens:

```
CONSTRUCT OK   layout=cramped      max_steps=480
CONSTRUCT OK   layout=open-kitchen max_steps=480
CONSTRUCT OK   layout=cramped      max_steps=620
CONSTRUCT FAIL layout=cramped      max_steps=640  -> TypeError: mettagrid GameConfig(): incompatible constructor arguments
CONSTRUCT FAIL layout=cramped      max_steps=900  -> TypeError: …
CONSTRUCT FAIL layout=open-kitchen max_steps=900  -> TypeError: …
```

It is **`max_steps`, not the layout**. The kitchen mission mints one resource plus two events per
prospective ticket, and the ticket count is `max_steps / ticket_interarrival`:

```
max_steps 480 -> 52 resources -> feature ids fit        (certification)
max_steps 620 -> 60 resources -> feature ids fit
max_steps 640 -> 61 resources -> 257 feature ids, max id 256  -> mettagrid GameConfig rejects
max_steps 900 -> 75 resources -> 313 feature ids, max id 312  -> mettagrid GameConfig rejects   (all 8 variants)
```

mettagrid packs feature ids into one byte (`token_value_base: 256`), so 256 is the hard ceiling.
`server.py` builds the mission at import/`create_app` time, before uvicorn binds, so the
exception exits the process with code 1 and the platform reports exactly what we see —
`game_unhealthy: Game container exited with code 1`, no `/healthz`, no log lines.

All eight variants in the published manifest declare `max_steps: 900` (the design's headline
"900 ticks"); the certification fixture declares 480:

```bash
curl -sS "$BASE/coworlds/$COW" "${AUTH[@]}" | jq -r '.manifest.variants[]|[.id,.game_config.max_steps]|@tsv'
curl -sS "$BASE/coworlds/$COW" "${AUTH[@]}" | jq -c '.manifest.certification.game_config|{layout,max_steps,step_seconds,plan_interval_steps}'
```

```
open-kitchen	900
cramped	900
forced	900
crowded	900
asymmetric	900
circuit	900
ring	900
figure-eight	900
{"layout":"cramped","max_steps":480,"step_seconds":0.02,"plan_interval_steps":240}
```

That is why `certify` was green and why every league round is dead. Caveat on this repro, stated
plainly: my sandbox resolved `mettagrid 0.26.22` on CPython 3.11, whereas the image is `python:3.12-slim` with whatever `mettagrid>=0.26.15`
(unpinned in `pyproject.toml`) resolved at build time — so the *exception text* may differ from
the container's. The scaling and the 256-id ceiling are properties of the game's own mission
builder, and they line up exactly with the fetched pass/fail split.

Two things for the coordinator to weigh (I did not change anything): the ticket encoding needs to
stop scaling with `max_steps` (bounded ticket slots — `order_queue_max` already exists), or the
variants need `max_steps ≤ 620`; and separately, certification exercising only a 480-step
`cramped` fixture while every shipped variant is 900 steps is the hole that let this through.

---

## Waiting record

Bound: 75 minutes from 2026-08-25T08:43Z (expires 09:58Z). Polls at 08:43, 08:50, 08:55, 09:00,
09:02, 09:11, 09:14 — logged in `log.md`, `heartbeat_at` refreshed in STATE and on the Asana run
task each time. Stopped at 09:15Z, inside the bound, because the bound's purpose was met and
further waiting cannot change the outcome: item 1 is satisfied (3 completed rounds) and the
episode failure is deterministic and identical across rounds 2, 3 and 4 on an image that cannot
be changed without a re-release.
