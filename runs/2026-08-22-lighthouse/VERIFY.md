# VERIFY — lighthouse   (2026-08-22T23:30Z)

Verdict: **all-true** (8/8)

Run `2026-08-22-lighthouse` · coworld `cow_e0618924-ab1f-42cc-ae51-8012688aac6e` v0.1.1 ·
league `league_3e9fc4b5-5b6c-4ad7-8ff4-e74fa144d954` · division `div_83c5d76c-b3a8-4651-9ac1-c33bd739494d`.

Shared preamble for every `curl` below (header **names** only; `$SOFTMAX_TOKEN` never printed):

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_3e9fc4b5-5b6c-4ad7-8ff4-e74fa144d954
D=div_83c5d76c-b3a8-4651-9ac1-c33bd739494d
COW=cow_e0618924-ab1f-42cc-ae51-8012688aac6e
```

Every fetch below was made fresh in this phase-60 dispatch (2026-08-22 23:02Z–23:30Z). The one
documented exception is check 7, whose evidence is the committed release artifact (see there).
Polling ran 23:03Z → 23:21Z (18 min), inside the 75-minute bound.

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}"      # HTTP 200, fetched 2026-08-22T23:21:14Z
 | jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
```

```
2
```

```bash
 | jq -r '(if type=="array" then . else .entries end)[]
          |[.id,.round_number,.status,.created_at,.completed_at,(.error//"null")]|@tsv'
```

```
round_73ab91e9-17af-49f3-b5d1-07a76d4b1b95	3	completed	2026-08-22T23:15:17.588054Z	2026-08-22T23:17:09.769114Z	null
round_2be3c46a-4312-44d7-ab36-e5c6605911e3	2	completed	2026-08-22T23:00:17.169114Z	2026-08-22T23:03:13.419856Z	null
round_121f5ece-ddb3-468d-93eb-3839700c3137	1	failed	2026-08-22T23:00:01.222074Z	2026-08-22T23:00:01.897925Z	Temporal RoundWorkflow failed before settling the round.
```

Round 1's `error`, verbatim: `Temporal RoundWorkflow failed before settling the round.` — the
documented pre-filler symptom (`playbooks/observatory-api.md` §6: "A `trigger-round` issued
before any filler exists fails instantly with `Temporal RoundWorkflow failed before settling the
round`"). It is `failed`, so it does not count; the two counted rounds are **3 and 2**.

Rounds 2 and 3 are after the fillers were set. `log.md:70` records it —

```
2026-08-22T23:01:45Z 50 fillers 200: lantern:v2+wallhug:v2 registered BEFORE trigger; response contains exactly those two, neither champion
```

— and the fetched proof, independent of any log timestamp, is that **both** counted rounds
actually seated the fillers, which is impossible if the filler list were empty (check 3 below
shows `is_filler: true` seats in round 3; the round-2 episode `ereq_2a95c20e-f57f-43fb-bfb6-a7df609671bc`
likewise seated `lighthouse-lantern:v2` at positions 2 and 3, and both replays name those seats
`Baseline` / `Baseline (2)`).

The registered filler list, fetched fresh:

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"     # HTTP 200
```

```json
{"filler_policy_versions":[
 {"policy_version_id":"214ad0dc-abdd-4c8b-b1e4-e10b83d1ff02","policy_name":"lighthouse-lantern","version":2,"player_name":"daveey"},
 {"policy_version_id":"c2120b1c-28f7-41b6-8dc6-7ea50b592b86","policy_name":"lighthouse-wallhug","version":2,"player_name":"daveey"}]}
```

(Neither champion version — `f6b55249-…` / `b285d4c3-…` — appears in that list.)

Round 3's entrants, from the same `/rounds` body:

```json
"entrant_attributions": [
 {"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player","policy_version_id":"f6b55249-cac1-4413-8da4-2254b2a87f30"},
 {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","subject_type":"player","policy_version_id":"b285d4c3-624a-40e3-b6e5-0670d069be71"}]
```

Status: **TRUE** — rounds 3 and 2 completed at 23:17:09.769114Z and 23:03:13.419856Z, both with
fillers seated; round 1 `failed` and is excluded with its error quoted.

---

## 2. Both champions ranked; fillers absent or Baseline — TRUE

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}"     # HTTP 200, fetched 2026-08-22T23:21:3xZ
 | jq -r '(if type=="array" then . else .entries end)[]
          |[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```

```
1	daveey		lighthouse-beacon:v2	1000.0	2	0.0
2	daveey-1	lighthouse-pilot:v2	1000.0	2	0.0
```

Raw body (bare list, not `{entries:…}`):

```json
[{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1000.0,"score_label":"Elo","score_value_type":"integer","rounds_played":2,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"lighthouse-beacon:v2","recent_rounds":null},
 {"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":1000.0,"score_label":"Elo","score_value_type":"integer","rounds_played":2,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"lighthouse-pilot:v2","recent_rounds":null}]
```

Both champions present, each `rounds_played = 2 ≥ 1`; the two filler policies
(`lighthouse-lantern:v2`, `lighthouse-wallhug:v2`) are **absent** from the leaderboard, as
required. Elo is still 1000.0 for both because the two episodes were team-scored ties
(round 2: all four seats 0.0; round 3: all four seats 2.0) — the ranking exists, no rank is
missing.

Status: **TRUE**.

---

## 3. Latest round's episode request completed with a replay — TRUE

```bash
R=round_73ab91e9-17af-49f3-b5d1-07a76d4b1b95        # max_by(round_number) over the completed rounds of check 1
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}"   # HTTP 200
 | jq -r '(if type=="array" then . else .entries end)[]|[.id,.status]|@tsv'
```

```
ereq_7ae8cdc3-1c1b-4fcf-91ea-bf24d612683c	completed
```

```bash
curl -sS "$BASE/episode-requests/ereq_7ae8cdc3-1c1b-4fcf-91ea-bf24d612683c" "${AUTH[@]}"   # HTTP 200
 | jq '{status, replay_url, participants, participant_scores}'
```

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/c8551f16-57b7-4d14-a638-36c179b1b234.replay",
  "participants": [
    {"position":0,"policy_name":"lighthouse-beacon","version":2,"player_name":"daveey","is_filler":false},
    {"position":1,"policy_name":"lighthouse-pilot","version":2,"player_name":"daveey-1","is_filler":false},
    {"position":2,"policy_name":"lighthouse-lantern","version":2,"player_name":"daveey","is_filler":true},
    {"position":3,"policy_name":"lighthouse-wallhug","version":2,"player_name":"daveey","is_filler":true}
  ],
  "participant_scores": [
    {"position":0,"score":2.0},{"position":1,"score":2.0},
    {"position":2,"score":2.0},{"position":3,"score":2.0}
  ]
}
```

(The `participants` rows carry the full `policy_version_id` / `policy_id` / `player_id` fields
too; trimmed here to the identity fields. Seat 0 = `f6b55249-cac1-4413-8da4-2254b2a87f30`,
seat 1 = `b285d4c3-624a-40e3-b6e5-0670d069be71`, seats 2/3 = the two filler version ids.)

`status == "completed"`, `replay_url` non-null, participants name **daveey** and **daveey-1**;
the two filler seats are flagged `is_filler: true` here and are renamed `Baseline` /
`Baseline (2)` spectator-side in the replay payload (check 4).

Status: **TRUE**.

---

## 4. Replay bytes valid and showing the game — TRUE

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/c8551f16-57b7-4d14-a638-36c179b1b234.replay" -o /tmp/v/ep3.replay
# HTTP 200 bytes=25970
jq -e . /tmp/v/ep3.replay >/dev/null && echo "strict UTF-8 JSON: ok"
```

```
strict UTF-8 JSON: ok
```

```bash
jq -r '.protocol' /tmp/v/ep3.replay
jq -c '.results'  /tmp/v/ep3.replay
```

```
lighthouse.replay.v1
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],"scores":[2.0,2.0,2.0,2.0],"roles":["keeper","runner","runner","runner"],"teamScore":2.0,"keys":1,"keyCount":3,"escaped":0,"drowned":3,"messages":11,"ticks":27,"maxTicks":45,"clock":38,"reason":"complete"}
```

**Protocol match.** The declared replay protocol is `lighthouse.replay.v1`
(`runs/2026-08-22-lighthouse/design.md:650,654` — "**Replay payload** (`lighthouse.replay.v1`)").
The hosted manifest does not carry a replay-protocol key — fetched proof:

```bash
curl -sS "$BASE/coworlds/$COW" "${AUTH[@]}" | jq -r '.manifest.game.protocols|keys'   # HTTP 200
```

```json
["global","player"]
```

so the manifest-side counterpart that *does* pin the string is the shipped viewer bundle, whose
wasm contains it verbatim:

```bash
strings c8_lighthouse_replay.wasm | grep -o 'lighthouse\.replay\.v1'
```

```
lighthouse.replay.v1
```

Replay `protocol` == design-declared protocol == the string compiled into the viewer. Match.

**`results.reason` = `complete`** — the strongest of the three legal values
(`["complete","timeup","deadline"]`, per the hosted manifest's `results_schema`:
`"reason":{"enum":["complete","timeup","deadline"],…}`). No `deadline` exception is needed.

**Champion seats are not falling back.** This game's event vocabulary is
`start/say/key/escape/drown/tick/end` — there is no `decision` event; per-seat scripted fallback
is recorded as the `tick` events' `scripted` array (4 booleans, seat order = `policyNames`).
Seat order fetched from the replay:

```bash
jq -r '.policyNames|tostring' /tmp/v/ep3.replay
```

```
["daveey","daveey-1","Baseline","Baseline (2)"]
```

→ champion seats are 0 (beacon/keeper) and 1 (pilot/runner); seats 2–3 are the scripted fillers.

```bash
jq -r '[.events[].kind]|group_by(.)|map({(.[0]):length})|add|tostring' /tmp/v/ep3.replay
jq -r '[.events[]|select(.kind=="tick")]
       | {ticks: length,
          seat0_champ_scripted: ([.[]|select(.scripted[0]==true)]|length),
          seat1_champ_scripted: ([.[]|select(.scripted[1]==true)]|length),
          seat2_filler_scripted:([.[]|select(.scripted[2]==true)]|length),
          seat3_filler_scripted:([.[]|select(.scripted[3]==true)]|length)}|tostring' /tmp/v/ep3.replay
```

```
{"drown":3,"end":1,"key":1,"say":11,"start":1,"tick":27}
{"ticks":27,"seat0_champ_scripted":0,"seat1_champ_scripted":0,"seat2_filler_scripted":27,"seat3_filler_scripted":27}
```

**0 of 27** ticks scripted for each champion seat (0 %); 27/27 for each filler seat, which is
what a scripted baseline is. Champion content is non-trivial — e.g. seat 0's tick-0 note and the
11 `say` transmissions (pasted in check 8a).

Corroboration from the other completed round (round 2, replay
`f7ddf04d-1a90-4d74-a6b7-dc28f427f501.replay`, fetched this dispatch, HTTP 200, 30762 bytes,
`jq -e .` ok):

```
protocol: lighthouse.replay.v1
results: {"names":["daveey","daveey-1","Baseline","Baseline (2)"],"scores":[0.0,0.0,0.0,0.0],"roles":["keeper","runner","runner","runner"],"teamScore":0.0,"keys":0,"keyCount":3,"escaped":0,"drowned":3,"messages":24,"ticks":35,"maxTicks":45,"clock":59,"reason":"complete"}
scripted: {"ticks":35,"seat0":0,"seat1":0,"seat2":35,"seat3":35}
```

Status: **TRUE** — strict-parse ok, protocol matches, `reason == "complete"`, champion seats
0 % scripted across both completed rounds.

---

## 5. Hosted game log is clean — TRUE

```bash
curl -sS "$BASE/episode-requests/ereq_7ae8cdc3-1c1b-4fcf-91ea-bf24d612683c/artifacts/logs" \
     "${AUTH[@]}" "${ELEV[@]}" -o c5_log.txt        # HTTP 200, bytes=110799  (elevated header required)
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' c5_log.txt || echo CLEAN
grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' c5_log.txt
```

```
CLEAN
0
```

Containers present in the artifact (so the grep really covered the game and player output, not an
empty file):

```bash
grep -o '===== container: [^=]*=====' c5_log.txt
```

```
===== container: coworld-init-config =====
===== container: bedrock-sidecar =====
===== container: game =====
===== container: worker =====
```

Zero lines match any of the four patterns — including zero `falling back to scripted decision`
lines, which is stronger than required (filler-seat fallbacks would have been by design).

Disclosed for completeness, though it matches **none** of the four patterns: one transient
upstream Bedrock 500 that the sidecar retried successfully —

```
2026-08-22 23:16:03,969 INFO httpx HTTP Request: POST https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke "HTTP/1.1 500 Internal Server Error"
2026-08-22 23:16:03,969 WARNING __main__ bedrock_sidecar_complete {…"ok":false,"status_code":500,"latency_ms":20.398591000002853,"error_kind":"upstream_server","error_type":null,"message":null,…}
2026-08-22 23:16:06,125 INFO httpx HTTP Request: POST https://bedrock-runtime.us-east-1.amazonaws.com/model/…
```

Call tally in the same artifact: `51 bedrock_sidecar_call`, `51 bedrock_sidecar_complete`,
`50 bedrock_sidecar_usage`, exactly **1** with `"ok":false`. The retry succeeded and no seat
degraded: check 4 shows 0/27 scripted ticks for both champion seats in this very episode.

Status: **TRUE** (CLEAN).

---

## 6. The public page uses the static replay path — TRUE

**Source used: both.** (a) the raw `softmax.com/lighthouse` HTML for the featured match; (b) the
replay-session endpoint the page's own client component calls to build the iframe `src` — the
raw-HTML iframe grep found nothing, which per `prompts/60-verify.md` §6 is *unknown*, not false.

```bash
curl -sS "https://softmax.com/lighthouse" -o c6_page.html   # HTTP 200, bytes=333874
grep -o '<iframe[^>]*src="[^"]*"' c6_page.html || echo "(no <iframe … src=…> in raw HTML)"
```

```
(no <iframe … src=…> in raw HTML)
```

**Featured match — present**, server-rendered into the page payload (`state.playlist[0]`, the
block the page's featured-match card reads):

```
\"state\":{\"leagueId\":\"league_3e9fc4b5-5b6c-4ad7-8ff4-e74fa144d954\",\"playlist\":[{\"episodeId\":\"b8d52775-06b6-4f9b-93c8-ee3c72dd2524\",\"coworldId\":\"cow_e0618924-ab1f-42cc-ae51-8012688aac6e\",\"coworldName\":\"lighthouse\",\"coworldVersion\":\"0.1.1\",\"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/c8551f16-57b7-4d14-a638-36c179b1b234.replay\",\"finishedAt\":\"2026-08-22T23:17:07.053473Z\",\"roundNumber\":3,\"episodeNumber\":1,\"code\":\"lighthouse.r3.e1\",\"matchup\":{\"divisionId\":\"div_83c5d76c-b3a8-4651-9ac1-c33bd739494d\",\"divisionName\":\"Competition\",\"first\":{\"rank\":1,…\"player_name\":\"daveey\",…\"policy_label\":\"lighthouse-beacon:v2\"…},\"second\":{\"rank\":2,…\"player_name\":\"daveey-1\",…\"policy_label\":\"lighthouse-pilot:v2\"…}},\"inspectUrl\":\"/observatory/v2?tab=episode-requests&detail=episode-request:ereq_7ae8cdc3-1c1b-4fcf-91ea-bf24d612683c\",\"outcome\":null}]
```

The featured match is `lighthouse.r3.e1` — the same episode request verified in check 3 — with a
two-player matchup (daveey vs daveey-1).

**The iframe `src`.** The page builds it client-side; the fetched page bundle shows exactly how:

```bash
for c in $(grep -o '/_next/static/chunks/[A-Za-z0-9_.-]*\.js' c6_page.html|sort -u); do curl -sS "https://softmax.com$c" -o "chunk_$(basename $c)"; done
grep -oh '.\{160\}coworlds/replays/session.\{600\}' chunk_06e2orhdv0re2.js
```

```js
…promise:fetch("/api/observatory/v2/coworlds/replays/session",{method:"POST",headers:{"Content-Type":"application/json"},
 body:JSON.stringify({coworld_id:e,replay_uri:d})}).then(async e=>{ … return{session:function(e){
 if("string"!=typeof e?.viewer_url||"boolean"!=typeof e.ready)throw Error(`Replay session response did not match { viewer_url: string, ready: boolean }…`);
 …D.current.delivery=e.ready?new URL(e.viewer_url).pathname.endsWith("/index.html")?"static_bundle":"static":"runtime" …
```

i.e. the iframe `src` **is** `viewer_url` from that endpoint, and the page classifies it
`static_bundle` iff it is `ready` and ends in `/index.html`. Same call, made here with the
featured match's replay:

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" -H 'content-type: application/json' "${AUTH[@]}" \
  -d '{"coworld_id":"cow_e0618924-ab1f-42cc-ae51-8012688aac6e","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/c8551f16-57b7-4d14-a638-36c179b1b234.replay"}'
# HTTP 200
```

```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e0618924-ab1f-42cc-ae51-8012688aac6e/sha256%3A2cc10989ca7929f00095b81b05a5517d20d0ede0aa38934ebff622a277a092ef/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fc8551f16-57b7-4d14-a638-36c179b1b234.replay&v=2","ready":true}
```

That is `…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` with
`<cow_id> = cow_e0618924-ab1f-42cc-ae51-8012688aac6e` and
`<sha> = sha256:2cc10989ca7929f00095b81b05a5517d20d0ede0aa38934ebff622a277a092ef` (the coworld's
`manifest_hash`, URL-encoded), `ready: true` → the page's own `delivery = "static_bundle"`.
**No `/client/replay` pod URL anywhere** in the response.

Fallback source (b) of the prompt, fetched too, for the record — `/coworlds` carries the viewer
bundle digest but no `featured_match` field at all (it is `null` for every coworld on the
platform, e.g. bullwhip/parley/paintbot, so its absence there is not evidence):

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}"   # HTTP 200; bare array, not {entries}
 | jq -r '(if type=="array" then . else .entries end)[]|select(.name=="lighthouse")
          |{id,name,version,canonical,replay_viewer:.manifest.game.replay_viewer,featured_match:(.featured_match//null)}'
```

```json
{"id":"cow_e0618924-ab1f-42cc-ae51-8012688aac6e","name":"lighthouse","version":"0.1.1","canonical":true,
 "replay_viewer":{"bundle":"sha256:516e6fd417adfcc4ec1cf9f3ea70e2a5e6135bf0baf980aa9939ff8dc3d163d5"},
 "featured_match":null}
```

Note for the playbook: the `<sha>` in the static route is the **manifest hash**, not
`manifest.game.replay_viewer.bundle`; and the route is served by
`api.observatory.softmax-research.net`, not the `softmax.com/api/observatory` proxy (which
returns `404 {"detail":"Replay viewer shell not found"}` for the same path — verified for
bullwhip too, so it is a platform-wide proxy behaviour, not a lighthouse defect).

Status: **TRUE** — featured match present (`lighthouse.r3.e1`, daveey vs daveey-1); iframe `src`
is the static `index.html` bundle URL, `ready: true`.

---

## 7. Certification declared the static bundle — TRUE

Source: **the committed artifact** `runs/2026-08-22-lighthouse/release-result.json` (phase 40's
copy, committed in `e7ca202 40 done: cogame-lighthouse 0.1.1 canonical+certified (run
32603480864)`). No re-download was needed; `/tmp` was never consulted.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-22-lighthouse/release-result.json
```

```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

```bash
jq -r '.certify.ok, .version' runs/2026-08-22-lighthouse/release-result.json
```

```
true
0.1.1
```

Contains the required substring `Replay liveness: skipped (static replay bundle declared`.
Surrounding transcript in the same file shows all 10 certification steps `[pass]`, including
`replay-present`, `replay-loadable` and `players-run`.

Status: **TRUE**.

---

## 8. Spectator judgment — TRUE

*(No browser, no screen, no screenshot was used. The judgment rests on the three fetches below.)*

### 8a. The replay JSON — what the viewer would draw

Board and seeding (`/tmp/v/ep3.replay`, the check-4 bytes):

```bash
jq -c '.config' /tmp/v/ep3.replay
```

```json
{"grid":["###.#######","#.....#...#","###.#.#.#.#","#...#.#.#.#","#.###.###.#","#...#.....#","###.#####.#","#...#.....#","###########"],"exit":[3,0],"starts":[[1,7],[5,7],[9,7]],"keys":[[7,3],[9,3],[3,5]],"seed":968231431,"maxTicks":45,"width":11,"height":9,"tideDelay":10,"tidePeriod":7,"keyCount":3,"messageCap":160,"sampled":true}
```

Ordered event stream (`tick / seat / kind / text`):

```bash
jq -r '.events[]|[(.tick//""),(.seat//""),.kind,(((.text//.note//"")|tostring)[0:90])]|@tsv' /tmp/v/ep3.replay
```

*early*
```
		start
0	0	say	Gasket N; Gizmo N; Widget N; toward keys
0		tick
1		tick
2		tick
3		tick
4		tick
5	1	key
5		tick
```
*middle*
```
14		tick
15	0	say	Gasket E; Gizmo N; Widget N; keys at (7,3) and (9,3)
15		tick
16	0	say	Gasket E; Gizmo N; Widget N; collect keys fast
16		tick
17		tick
18	0	say	Gasket E; Gizmo E; Widget E; get keys fast
18		tick
19	0	say	Gasket E; Gizmo E; Widget E; keys at (7,3) and (9,3)
```
*late*
```
22	1	drown
22		tick
23		tick
24	0	say	Gizmo S; Widget E; both keys then exit
24		tick
25	0	say	Gizmo S get key; Widget E get key; both then N to exit
25		tick
26	0	say	Gizmo N to key at (7,3); Widget E to key at (9,3); then both N to exit
26	2	drown
26	3	drown
26		tick
27		end	complete
```

Per-tick state the viewer renders (first, middle, last), with the champions' private reasoning:

```bash
jq -c '[.events[]|select(.kind=="tick")][0]  | {tick,clock,tideRows,positions,alive,moves,keysCollected,gateOpen,escaped,drowned,scripted,note0:(.notes[0][0:220]),note1:(.notes[1][0:220])}' /tmp/v/ep3.replay
```

```json
{"tick":0,"clock":2,"tideRows":0,"positions":[[2,7],[6,7],[8,7]],"alive":[true,true,true],"moves":["E","E","W"],"keysCollected":0,"gateOpen":false,"escaped":0,"drowned":0,"scripted":[false,false,true,true],
 "note0":"Clock 0/73, water at y≥9, floods in 17t (silent) or 9t (every tx). All 3 runners at row 7. Keys at (7,3), (9,3), (3,5). Exit at (5,0). Strategy: route all north through maze to collect keys in order of proximity, then to",
 "note1":"Tick 0: Starting blind run. Window shows wall to N and W, floor to E. Moving E to explore. Hold 0/3 keys. Team 0/3 keys. No keeper message yet. Will map maze layout as I move."}
```

```json
{"tick":13,"clock":15,"tideRows":0,"positions":[[1,5],[5,1],[3,1]],"alive":[true,true,true],"moves":["S","N","W"],"keysCollected":1,"drowned":0,"scripted":[false,false,true,true],
 "note0":"Tick 13: Gasket at (1,5) with 1 key, last order N, obeyed (moved W then continuing pattern). Gizmo at (5,2) with 0 keys, last order N, obeyed. Widget at (4,1) with 0 keys, last order N, obeyed. Water ",
 "note1":"Tick 13: Last order 'W' (1 tick old). Window: wall N/E, floor S/W. Trying S to continue exploring westward. Holding 1/3 keys. Water rising (~4-5 tiles high). Need to map maze, find keys 2&3, and loca…"}
```

```json
{"tick":26,"clock":38,"tideRows":4,"positions":[[-1,-1],[-1,-1],[-1,-1]],"alive":[false,false,false],"keysCollected":1,"drowned":3,"scripted":[false,false,true,true],
 "note0":"Tick 26: Water y≥6 (3 rows), next floods in 1 tick if silent. Gizmo at (5,5) carrying 0 keys—was blocked S by water at tick 25, now must go N to (5,4)→(5,3) then E to (7,3) to get key. Widget at (5,5)"}
```

```bash
jq -c '.events[]|select(.kind=="key")' /tmp/v/ep3.replay ; jq -c '.events[]|select(.kind=="end")' /tmp/v/ep3.replay ; jq -r '.results' /tmp/v/ep3.replay
```

```json
{"kind":"key","tick":5,"seat":1,"x":3,"y":5,"keysCollected":1}
{"kind":"end","tick":27,"text":"complete"}
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],"scores":[2.0,2.0,2.0,2.0],"roles":["keeper","runner","runner","runner"],"teamScore":2.0,"keys":1,"keyCount":3,"escaped":0,"drowned":3,"messages":11,"ticks":27,"maxTicks":45,"clock":38,"reason":"complete"}
```

### 8b. The static bundle and every asset it names

`BUNDLE=https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e0618924-ab1f-42cc-ae51-8012688aac6e/sha256%3A2cc10989ca7929f00095b81b05a5517d20d0ede0aa38934ebff622a277a092ef`
(the iframe `src` of check 6, minus the `?replay=` query).

```bash
curl -sS "$BUNDLE/index.html" -o c8_idx.html -w 'index.html %{http_code} %{size_download} %{content_type}\n'
grep -oE '(src|href)="[^"]+"' c8_idx.html
for A in chrome.css renderer.js lighthouse_replay.js static_replay.js; do
  curl -sSL "$BUNDLE/$A" -o "c8_$A" -w "$A %{http_code} %{size_download} %{content_type}\n"; done
grep -ohE '[A-Za-z0-9_.-]+\.wasm' c8_idx.html c8_*.js | sort -u
curl -sSL "$BUNDLE/lighthouse_replay.wasm" -o c8_lighthouse_replay.wasm -w '…'
```

Asset list found in `index.html`, verbatim:

```
href="./chrome.css"
src="./renderer.js"
src="./lighthouse_replay.js"
src="./static_replay.js"
```
wasm named by the emscripten loader: `lighthouse_replay.wasm`

| URL (relative to `$BUNDLE`) | HTTP | bytes | content-type |
|---|---|---|---|
| `/index.html` | 200 | 1528 | text/html; charset=utf-8 |
| `/chrome.css` | 200 | 12044 | text/css; charset=utf-8 |
| `/renderer.js` | 200 | 54965 | text/javascript; charset=utf-8 |
| `/lighthouse_replay.js` | 200 | 11403 | text/javascript; charset=utf-8 |
| `/static_replay.js` | 200 | 5923 | text/javascript; charset=utf-8 |
| `/lighthouse_replay.wasm` | 200 | 162418 | application/wasm |

All 200, all non-trivial, none an HTML error page — `file c8_lighthouse_replay.wasm` →
`WebAssembly (wasm) binary module version 0x1 (MVP)`, and the wasm contains the string
`lighthouse.replay.v1` (check 4). The fetched `index.html` is the game's own chrome, not a
placeholder:

```html
<title>Lighthouse — Replay</title> … <div id="wordmark">LIGHT<span>HOUSE</span></div>
<div id="clock">TICK 0 / 45</div> … <canvas id="table" width="960" height="640"></canvas>
<div id="lightpool"></div><div id="grain"></div><div id="endscreen"></div>
<div class="scrub" id="scrub"></div> … <div id="feed"></div><div id="loading">LOADING REPLAY…</div>
<script src="./renderer.js"></script><script src="./lighthouse_replay.js"></script><script src="./static_replay.js"></script>
```

### 8c. The viewer shell's error markers

```bash
grep -c 'coworld-replay' c8_static_replay.js
grep -n 'coworld-replay' c8_static_replay.js
grep -n 'tell(' c8_static_replay.js
```

```
1
27:    var envelope = { src: "coworld-replay", type: type };
25:  function tell(type, message) {
31:  tell("loading");
57:    tell("error", message);
123:      window.requestAnimationFrame(function () { tell("ready"); });
```

with the bridge body:

```js
25:  function tell(type, message) {
26:    if (window.parent === window) return;
27:    var envelope = { src: "coworld-replay", type: type };
28:    if (message) envelope.message = message;
29:    try { window.parent.postMessage(envelope, "*"); } catch (ignore) {}
```

Both required markers hit: the `coworld-replay` postMessage bridge and its `tell("ready")` call
(and the host page's listener, seen in the page chunk in check 6, keys on exactly
`r?.src==="coworld-replay"` with `"loading"`/`"ready"`/`"error"`).

### Judgment

**The replay is legible and it shows the game.** Lighthouse is a keeper-and-runners maze escape
against a rising tide, and that is exactly what the bytes contain: an 11×9 maze grid, three
runners starting on row 7, three keys and an exit at (3,0), then 27 ticks of per-tick state —
positions, `alive`, `moves`, `blocked`, `keysOnFloor`, `keysCollected`, `gateOpen`, `tideRows`,
`escaped`, `drowned` — which is a complete frame series for the canvas the bundle draws. The
champion seats are the ones acting: seat 0 (daveey / `lighthouse-beacon:v2`, the keeper) issues
11 addressed broadcasts, from "Gasket N; Gizmo N; Widget N; toward keys" at tick 0 to a
key-then-exit routing at tick 26, each backed by a private note that reasons about the tide
clock, the message cost of transmitting, and each runner's coordinates; seat 1 (daveey-1 /
`lighthouse-pilot:v2`, a runner) navigates blind on a 3×3 window, obeys the keeper's orders, and
**picks up a key at tick 5 at (3,5)** — a `key` event with `keysCollected: 1`, which is the score
moving. Neither champion seat used a scripted fallback on any of the 27 ticks; the two filler
seats are scripted on all 27, exactly as scripted baselines should be. The ending is legible too:
the tide reaches 4 rows, the three runners drown at ticks 22 and 26, and the episode settles
`complete` at tick 27 with `teamScore 2.0` (1 of 3 keys, 0 escapes) — a loss on the merits, not a
crash or a hang, and the viewer has an `#endscreen` to say so. On the rendering side, the shell
the iframe loads is Lighthouse's own chrome (wordmark, tick clock, scorebug, 960×640 canvas,
light pool, film grain, scrub bar, message feed), all six assets return 200 with real bytes, the
162 KB wasm is a valid module that knows the `lighthouse.replay.v1` protocol these bytes carry,
and the shell signals the host page through the `coworld-replay` bridge. Nothing here is empty or
illegible; a spectator opening the featured match gets a playable, annotated, self-explaining
episode.

Status: **TRUE**.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | TRUE (rounds 3, 2) |
| 2 | Both champions ranked, fillers absent/Baseline | TRUE |
| 3 | Latest round's episode request completed with replay | TRUE (`ereq_7ae8cdc3-1c1b-4fcf-91ea-bf24d612683c`) |
| 4 | Replay bytes valid and show the game | TRUE (`reason: complete`, 0/27 champion fallbacks) |
| 5 | Hosted game log clean | TRUE (CLEAN, 0 matches) |
| 6 | Public page featured match + static iframe `src` | TRUE |
| 7 | Certification declared the static bundle | TRUE |
| 8 | Spectator judgment | TRUE |

Verified replay: `https://softmax-public.s3.amazonaws.com/replays/c8551f16-57b7-4d14-a638-36c179b1b234.replay`
Verified iframe `src`: `https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e0618924-ab1f-42cc-ae51-8012688aac6e/sha256%3A2cc10989ca7929f00095b81b05a5517d20d0ede0aa38934ebff622a277a092ef/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fc8551f16-57b7-4d14-a638-36c179b1b234.replay&v=2`
