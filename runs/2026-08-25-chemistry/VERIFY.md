# VERIFY — chemistry   (2026-08-25T08:22Z)

Verdict: **all-true (8/8)**

Run `2026-08-25-chemistry` · coworld `cow_292543de-c887-4398-8d4e-70fdb298b290` v0.1.0 ·
league `league_9b734c36-c6a2-4cc4-a12e-e8bc3977e86c` · division `div_ab928df3-f28c-4249-9f7d-cb62cf97ded2`.

Every block below is a request made **this run** (phase 60, 07:10Z–08:22Z) and the bytes it
returned. Headers are named, never their values: `AUTH` = `-H "Authorization: Bearer $SOFTMAX_TOKEN"
-H "User-Agent: coworld-builder/1.0"`; `ELEV` = `-H "X-Use-Elevated-Privileges: true"`.
`BASE=https://softmax.com/api/observatory/v2`.

Documented exceptions used: **check 7** reads the committed `runs/<run>/release-result.json`
(phase 40's artifact copy, per `prompts/60-verify.md` §7); **check 8** reads the artifact of the
`viewer-check.yml` run **this phase dispatched** (run `32825902427`, 08:18:04Z).

A platform condition shaped this phase and is documented under checks 4 and 5: the
platform-wide Bedrock `claude-haiku-4-5` **daily-token** quota was throttling (HTTP 429
`Too many tokens per day`) through rounds 2–5, and stopped by round 6. The **latest completed
round (6) is clean** — that is the round checks 3/4/5 are verified against, as the checklist
requires. The throttled rounds are recorded verbatim anyway, because they are what a spectator
who opened rounds 2–5 would have seen.

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

```
GET $BASE/rounds?league_id=league_9b734c36-c6a2-4cc4-a12e-e8bc3977e86c&limit=20   (AUTH)
fetched 2026-08-25T08:19:16Z
```

```json
[
  {"id": "round_e0bdbc2f-6242-4d2c-83e9-31626e71d210", "round_number": 6, "status": "completed", "error": null, "created_at": "2026-08-25T08:08:10.883958Z"},
  {"id": "round_114bb767-8b27-4138-966c-b7ebf8fd145e", "round_number": 5, "status": "completed", "error": null, "created_at": "2026-08-25T07:53:09.760590Z"},
  {"id": "round_1045037f-0e47-4cf8-993b-b67852a63a84", "round_number": 4, "status": "completed", "error": null, "created_at": "2026-08-25T07:38:09.351080Z"},
  {"id": "round_4342b6bb-ec62-46dc-9d0a-0ef0d7ea24c3", "round_number": 3, "status": "completed", "error": null, "created_at": "2026-08-25T07:23:08.717735Z"},
  {"id": "round_604ee98e-2d2a-4bb3-8b2e-67130a263283", "round_number": 2, "status": "completed", "error": null, "created_at": "2026-08-25T07:08:07.839353Z"},
  {"id": "round_5669a6f5-4d41-4d05-be82-9f7e62c0d420", "round_number": 1, "status": "failed",    "error": "Temporal RoundWorkflow failed before settling the round.", "created_at": "2026-08-25T07:08:02.206870Z"}
]
```

```
$ … | jq -r '[.entries[]|select(.status=="completed")]|length'
5
```

Round 1's `error` verbatim: `Temporal RoundWorkflow failed before settling the round.` — the
known pre-filler auto-trigger race (`playbooks/observatory-api.md` §6: "a `trigger-round` issued
before any filler exists fails instantly with `Temporal RoundWorkflow failed before settling the
round`"). It does not count and is not counted.

**Fillers were in force from round 2 onward**, proven by two fetches rather than by the log:

```
GET $BASE/leagues/$L/filler-policies   (AUTH + ELEV — this read 403s on bare AUTH)
fetched 2026-08-25T07:32:36Z
```
```json
{"filler_policy_versions": [
  {"policy_version_id": "51066378-6b79-4dc1-b693-b71e45c3722c", "policy_id": "ec8e2762-9547-49bc-b7f9-34e06faffcf4",
   "policy_name": "chemistry-courier", "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
   "player_name": "daveey", "display_name": null},
  {"policy_version_id": "33c53b59-b153-4b31-9b07-1d4e59a4a34c", "policy_id": "6130b625-da9b-466b-9a4b-545941d3467b",
   "policy_name": "chemistry-freeloader", "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
   "player_name": "daveey", "display_name": null}]}
```

and round 2's own episode request already seated them (`is_filler: true`, positions 2–7 —
full body under check 3's precedent block below), so the two filler version ids were registered
**before** round 2 settled at 07:12:32Z. `log.md` records the registration at 07:09:09Z (the
heartbeat write); the seating evidence above is the fetched proof.

Status: **TRUE** — 5 completed rounds (2, 3, 4, 5, 6), all after fillers were set; requirement is ≥2.

---

## 2. Both champions ranked, fillers absent/Baseline — TRUE

```
GET $BASE/divisions/div_ab928df3-f28c-4249-9f7d-cb62cf97ded2/leaderboard   (AUTH)
fetched 2026-08-25T08:19:16Z
$ … | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```

```
1	daveey-1	chemistry-metabolist:v1	1049.7086700569187	5	4.0
2	richard	co-gas-chemistry-freeloader-richard:v1	1016.0	1	1.0
3	daveey	chemistry-foreman:v1	982.2913299430815	5	1.0
4	relh	co-gas-chemistry-freeloader-relhalpha:v1	952.0	1	0.0
```

- `daveey` — `chemistry-foreman:v1`, `rounds_played = 5` ✓
- `daveey-1` — `chemistry-metabolist:v1`, `rounds_played = 5` ✓
- Fillers `chemistry-courier:v1` and `chemistry-freeloader:v1`: **absent from the leaderboard** ✓
  (they appear in episodes as `Baseline`/`Baseline (N)` — see the replay `policyNames` under check 4).
- Rows 2 and 4 are **other people's** entrants (`relh`, `richard`) who submitted their own policies
  into this league at ~08:08Z. They are not fillers (`is_filler: false` in check 3's participants)
  and their presence is not a defect; it is outside traffic on a public ladder.

Status: **TRUE**.

---

## 3. Latest completed round's episode request completed with a replay — TRUE

Latest completed round at fetch time = **round 6**, `round_e0bdbc2f-6242-4d2c-83e9-31626e71d210`.

```
R=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" AUTH | jq -r '[.entries[]|select(.status=="completed")]|max_by(.round_number).id')
GET $BASE/episode-requests?round_id=$R&limit=20   (AUTH)     # NOT ?division_id= (500)
fetched 2026-08-25T08:17:0xZ
```
```json
[{"id":"ereq_76bcca2e-615a-414e-bce1-af7f369d46af","status":"completed",
  "replay_url":"https://softmax-public.s3.amazonaws.com/replays/46fc7f16-62e3-4e48-b3d1-fbf973522107.replay"}]
```

```
GET $BASE/episode-requests/ereq_76bcca2e-615a-414e-bce1-af7f369d46af   (AUTH)
$ … | jq '{status, replay_url}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/46fc7f16-62e3-4e48-b3d1-fbf973522107.replay"
}
```

`participants` (position / policy_name / player_name / is_filler), same response:
```
0	co-gas-chemistry-freeloader-relhalpha	relh		false
1	chemistry-foreman			daveey		false
2	chemistry-metabolist			daveey-1	false
3	co-gas-chemistry-freeloader-richard	richard		false
4	chemistry-courier			daveey		true
5	chemistry-freeloader			daveey		true
6	chemistry-freeloader			daveey		true
7	chemistry-freeloader			daveey		true
```

`participant_scores`, same response:
```json
[{"position":0,"score":0.0},{"position":1,"score":1.0},{"position":2,"score":1.0},{"position":3,"score":1.0},
 {"position":4,"score":0.0},{"position":5,"score":0.0},{"position":6,"score":0.0},{"position":7,"score":0.0}]
```

Status: **TRUE** — `status == "completed"`, non-null `replay_url`, `daveey` at seat 1 and
`daveey-1` at seat 2, the four filler seats flagged `is_filler: true` and rendered `Baseline (N)`
in the replay (check 4).

*Precedent (same check on the earlier round 2, fetched 07:14Z — kept because it is the round the
platform throttle hit hardest):* `ereq_3940ba55-7866-49fa-b08f-8ad21d75424c`, `status: completed`,
`replay_url: …/replays/dd8d7644-0207-4ab4-ba7c-0dd95993451c.replay`, participants
`0 chemistry-foreman daveey false`, `1 chemistry-metabolist daveey-1 false`, `2–7` filler
(`chemistry-courier` ×5, `chemistry-freeloader` ×2 → `is_filler: true`).

---

## 4. Replay bytes are valid and show the game — TRUE

```
$ curl -sSL "https://softmax-public.s3.amazonaws.com/replays/46fc7f16-62e3-4e48-b3d1-fbf973522107.replay" -o /tmp/ep-r6.replay -w "http=%{http_code} bytes=%{size_download}\n"
http=200 bytes=141641

$ jq -e . /tmp/ep-r6.replay >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok

$ jq -r '.protocol, .results.reason' /tmp/ep-r6.replay
chemistry.replay.v1
complete
```

`protocol` match: the design note pins the replay format at `design.md:585`
(`### The replay file (\`chemistry.replay.v1\`)`) and `design.md:946` asserts
`protocol == "chemistry.replay.v1"`. The fetched bytes say `chemistry.replay.v1`. ✓

Decision events — adapted to this coworld's replay vocabulary (`k=="order"` rows are the
decision-type events, one per seat per shift; `source ∈ llm|retry|fallback|scripted`):

```
$ jq -r '[.events[]|select(.k=="order")]|length' /tmp/ep-r6.replay
56
$ jq -r '[.events[]|select(.k=="order" and .source=="fallback")]|length' /tmp/ep-r6.replay
0
$ jq -c '[.events[]|select(.k=="order")]|group_by(.seat)|map({seat:.[0].seat,n:length,sources:(map(.source)|group_by(.)|map({(.[0]):length})|add)})' /tmp/ep-r6.replay
[{"seat":0,"n":7,"sources":{"scripted":7}},{"seat":1,"n":7,"sources":{"llm":7}},
 {"seat":2,"n":7,"sources":{"llm":7}},{"seat":3,"n":7,"sources":{"scripted":7}},
 {"seat":4,"n":7,"sources":{"scripted":7}},{"seat":5,"n":7,"sources":{"scripted":7}},
 {"seat":6,"n":7,"sources":{"scripted":7}},{"seat":7,"n":7,"sources":{"scripted":7}}]
```

**Champion seats are 1 (`chemistry-foreman`/daveey) and 2 (`chemistry-metabolist`/daveey-1) —
7/7 `llm`, zero fallbacks, zero scripted.** Seats 0 and 3 are the two outside entrants' policies
(`relh`, `richard`), which are scripted by their authors' choice; seats 4–7 are this coworld's
scripted fillers, which legitimately show `scripted`.

56 = 7 shifts × 8 seats: the episode ended at shift 7 on the **famine** condition, not at the
12-shift limit. The design declares that a completed game:

> `design.md:257` — `every reactor has been charge == 0 for 3 consecutive shift boundaries and no
> FOOD token is on the floor` → `results.reason: complete`, `results.ending: famine`
> `design.md:262-263` — "famine is a *completed game of Chemistry*, not an error, so it reports
> `complete` and carries the detail in `results.ending`; phase 60's check 4 therefore passes on a
> dead room, as it should."

`results` verbatim:
```json
{"names":["relh","daveey","daveey-1","richard","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"],
 "aliases":["Argon","Borax","Cinder","Dram","Ember","Flint","Gilt","Hob"],
 "scores":[0,1,1,1,0,0,0,0],"win":[false,true,true,true,false,false,false,false],
 "food_eaten":[0,1,1,1,0,0,0,0],"delivered":[2,5,7,1,9,1,2,1],
 "misdrops":[0,0,0,0,0,0,0,0],"hoarded":[0,0,0,0,0,0,0,0],
 "reactions":[0,0,2],"food_made":3,"food_rotted":0,"cold_starts":1,
 "shifts":7,"reason":"complete","ending":"famine"}
```
`policyNames` (fillers correctly renamed):
```json
["relh","daveey","daveey-1","richard","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"]
```

Champion decisions are non-trivial, not boilerplate — every one of the 14 champion orders,
`shift / seat / source / say`:
```
1	1	llm	resin to Amber - all reactors at charge 3, all stocks empty. Taking primary lan…
1	2	llm	Room needs 6 deliveries this shift (2 per vat). Starting cold-start: amber gets…
2	1	llm	spark to Amber - all vats charge 2/12, need both feedstocks. Covering spark lan…
2	2	llm	Room needs 6 deliveries this shift. Last shift: 1 delivered, 5 short. Amber sta…
3	1	llm	brine to Cobalt - all vats charge 1/12. Cobalt needs brine most. Covering this …
3	2	llm	Room needs 6 deliveries/shift, got 1 last shift. Short 5. Cobalt needs brine to…
4	1	llm	resin to Amber - cold start prevention. Amber charge 0, needs both feedstocks. …
4	2	llm	Room needs 6 deliveries/shift, got 1 last shift. Short 5. Spark to amber - must…
5	1	llm	spark to Amber - charge 0 critical. Amber needs spark 0→stock. Resin covered.
5	2	llm	Room needs 6 deliveries/shift, got 2 last shift. Short 4. Spark to amber cold s…
6	1	llm	spark to Amber - charge 0 critical. Amber spark stock 3→need 1 more for cold st…
6	2	llm	Room needs 6 deliveries/shift, got 4 last shift. Short 2. Brine to Cobalt to un…
7	1	llm	spark to Amber - charge 0 critical. Amber needs 1 more spark for cold start.
7	2	llm	Room needs 6 deliveries/shift. Last shift: 4 delivered. SHORT 2. Brine to Cobal…
```
one full order row, with its private `notes` and measured latency:
```json
{"t":180,"k":"order","seat":2,"shift":4,"job":"supply","sp":"spark","rx":"amber","source":"llm",
 "clamped":false,
 "say":"Room needs 6 deliveries/shift, got 1 last shift. Short 5. Spark to amber - must…",
 "notes":"Shift 4: Amber COLD at 0/12 with resin 2, spark 0. Beryl COLD at 0/12 with spark 0, brine 0. Cobalt at 2/12 with resin 1, brine 0. Borax carrying brine to cobalt, Ember carrying resin to cobalt. Spark nearest at (27,3). Must supply spark to amber to enable reactions. Amber will then be able to react with its resin 2 o…",
 "latencyMs":6141}
```

Status: **TRUE** — strict-parser-valid UTF-8 JSON; `protocol` matches the design pin;
`results.reason == "complete"` with the design-sanctioned `famine` ending; champion seats 100 %
LLM-sourced with substantive, state-referencing content; **zero** fallbacks.

### Documented platform condition affecting rounds 2–5 (not the verified round)

The same measurement on the earlier rounds, all fetched this phase:

| round | ereq | seat pair (champions) | fallback / total per champion seat | reason |
|---|---|---|---|---|
| 2 | `ereq_3940ba55-…` | 0, 1 | 10/12 and 9/12 | complete (shift_limit) |
| 3 | `ereq_9978f99a-…` | 0, 1 | 10/12 and 10/12 | complete (shift_limit) |
| 4 | `ereq_9bb08dd9-…` | 0, 1 | 3/12 and 7/12 | complete |
| 5 | `ereq_fa8d02ac-…` | 0, 1 | 10/12 and 11/12 | complete |
| **6** | `ereq_76bcca2e-…` | 1, 2 | **0/7 and 0/7** | complete (famine) |

Round 3, verbatim:
```
$ jq -c '[.events[]|select(.k=="order")]|group_by(.seat)|map({seat:.[0].seat,sources:…})' /tmp/ep.replay
[{"seat":0,"sources":{"fallback":10,"llm":2}},{"seat":1,"sources":{"fallback":10,"llm":1,"retry":1}},
 {"seat":2,"sources":{"scripted":12}}, … {"seat":7,"sources":{"scripted":12}}]
$ jq -c '.results' /tmp/ep.replay
{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)","Baseline (5)","Baseline (6)"],
 "aliases":["Argon","Borax","Cinder","Dram","Ember","Flint","Gilt","Hob"],
 "scores":[0,12,22,2,19,4,58,16],"win":[false,false,false,false,false,false,true,false],
 "food_eaten":[0,12,22,2,19,4,58,16],"delivered":[16,14,16,21,16,21,0,10],
 "misdrops":[0,0,0,0,0,0,0,0],"hoarded":[0,0,0,0,0,0,0,0],
 "reactions":[14,21,20],"food_made":152,"food_rotted":0,"cold_starts":0,
 "shifts":12,"reason":"complete","ending":"shift_limit"}
```
Cause, from round 3's hosted log (decoded, see check 5):
```
chemistry llm: seat 0 attempt 0 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
chemistry llm: seat 1 attempt 0 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
chemistry llm: seat 0 attempt 1 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
chemistry llm: seat 1 attempt 1 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
chemistry llm: seat 0 falling back to scripted order
chemistry llm: seat 1 falling back to scripted order
```
The prompt's rule was followed: this is a platform capacity symptom, cross-checked below, and
polling continued inside the 75-minute bound until a clean round arrived (round 6, 08:11Z). It is
therefore recorded, not charged against the coworld.

---

## 5. Hosted game log is clean — TRUE

```
GET $BASE/episode-requests/ereq_76bcca2e-615a-414e-bce1-af7f369d46af/artifacts/logs   (AUTH + ELEV)
fetched 2026-08-25T08:19:5xZ   →   http=200 bytes=32181
```
The body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it was
**decoded** (`ast.literal_eval` per repr) before grepping, per `playbooks/observatory-api.md` §10:

```
$ python3 decode.py < logs6.raw > logs6.txt ; grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs6.txt || echo CLEAN
CLEAN
```
```
decoded lines: 114
GREP RESULT: CLEAN
429/throttle lines: 0
containers: coworld-init-config, bedrock-sidecar, game, worker
```

What the decoded `game` container does say:
```
chemistry: seed not pinned; randomized
chemistry: seed 928031177
chemistry: shift 1 of 12 at 8s
chemistry: shift 2 of 12 at 26s
chemistry: shift 3 of 12 at 44s
chemistry: shift 4 of 12 at 62s
chemistry: shift 5 of 12 at 80s
chemistry: shift 6 of 12 at 98s
chemistry: shift 7 of 12 at 116s
chemistry llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0, url http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
```
(exactly one `chemistry llm:` line — the transport banner. No retry, no fallback, no rejection.)

Status: **TRUE** for the latest completed round.

### The throttle, documented and cross-checked (rounds 2–5)

Round 3's log, same endpoint and decode, fetched 07:33Z:
```
matching lines: 20   →   20x  "chemistry llm: seat N falling back to scripted order"
"Too many tokens" lines: 82
```
Round 2 (fetched 07:16Z): `matching lines: 19`, 429s throughout.
Round 5 (fetched 08:02Z): `matching lines: 21`, `429 'Too many tokens' lines: 84`.

**Cross-check against other LLM coworlds, same window, fetched this phase** — the shared resource
is Bedrock capacity (SPEC §Parallelism and per-run isolation):

`coins` league `league_e9506fcc-08c3-4372-90ac-0ced465c7d9c`, round 22, `ereq_aca46d7a-f1e2-45ee-9bc5-ff1661b2b040`:
```
matching lines: 97
2026-08-25 07:13:04,643 INFO httpx HTTP Request: POST https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke "HTTP/1.1 429 Too Many Requests"
2026-08-25 07:13:04,692 INFO httpx HTTP Request: POST https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke "HTTP/1.1 429 Too Many Requests"
2026-08-25 07:13:09,478 INFO httpx HTTP Request: POST https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke "HTTP/1.1 429 Too Many Requests"
```
`hanabi` league `league_332c17c5-b6bf-4341-98c7-3161dd58e6d8`, round 26, `ereq_61195c81-30b7-442c-a7cd-1b70a75d7b1d`:
```
matching lines: 8
2026-08-25 07:04:31,514 INFO httpx HTTP Request: POST https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke "HTTP/1.1 429 Too Many Requests"
hanabi llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
hanabi llm: seat 1 attempt 0 rejected: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
```
Two other LLM coworlds hit the identical 429 on the identical model in the identical minutes →
platform-wide capacity, not a chemistry defect. The bound did not expire: round 6 came through
clean at 08:11Z, inside it.

**Observation for the coordinator (not a check failure):** `hanabi` survives a haiku throttle by
switching model (`falling back to …claude-sonnet-4-5…`) and keeps playing; chemistry's player has
no model-level fallback, so it drops straight to a scripted order. That is why rounds 2–5 look
scripted at the champion seats while hanabi did not. Worth a phase-30 item.

---

## 6. The public page uses the static replay path — TRUE

**Source used: the SSR payload + the session route, not the raw-HTML grep.** The grep is recorded
first, and it finds nothing — the documented client-rendered case, not a false negative:

```
$ curl -sS "https://softmax.com/chemistry" -o chem6.html -w "page http=%{http_code} bytes=%{size_download}\n"
page http=200 bytes=555374
$ grep -o '<iframe[^>]*src="[^"]*"' chem6.html
(no match — the iframe is client-rendered; lighthouse run 2026-08-22, playbooks/observatory-api.md §Featured match)
```

The coworld detail API is likewise not evidence here (`featured_match: null` platform-wide):
```
GET $BASE/coworlds?limit=200   (AUTH)   → filtered client-side on .name=="chemistry"
{"id":"cow_292543de-c887-4398-8d4e-70fdb298b290","name":"chemistry","canonical":true,
 "replay_viewer":null,"featured_match":null}
```

**Featured match — server-rendered into the page's SSR payload at `state.playlist[0]`**
(same 08:17:52Z fetch of `https://softmax.com/chemistry`, un-escaped):
```json
"playlist":[{"episodeId":"14aec7c9-6102-4734-a9e9-8b1c81b4a4d7",
 "coworldId":"cow_292543de-c887-4398-8d4e-70fdb298b290","coworldName":"chemistry",
 "coworldVersion":"0.1.0",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/46fc7f16-62e3-4e48-b3d1-fbf973522107.replay",
 "finishedAt":"2026-08-25T08:11:03.840590Z","roundNumber":6,"episodeNumber":1,
 "code":"chemistry.r6.e1",
 "matchup":{"divisionId":"div_ab928df3-f28c-4249-9f7d-cb62cf97ded2","divisionName":"Competition",
  "first":{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
           "score":1049.7086700569187,"score_label":"Elo",…
```
A featured match **is present** (`chemistry.r6.e1`, the same round 6 episode as checks 3–5), with
both ranked champions in the matchup.

**The iframe `src`** — the call the page's own JS makes:
```
POST $BASE/coworlds/replays/session   (AUTH, content-type: application/json)
body {"coworld_id":"cow_292543de-c887-4398-8d4e-70fdb298b290",
      "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/46fc7f16-62e3-4e48-b3d1-fbf973522107.replay"}
fetched 2026-08-25T08:18:0xZ
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_292543de-c887-4398-8d4e-70fdb298b290/sha256%3A1002ad49f6a1d222ab8c3f22d2b348c93ec6e930ab1a5cb21ebf6683b5ca3699/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F46fc7f16-62e3-4e48-b3d1-fbf973522107.replay&v=2",
  "ready": true
}
```
Path shape: `/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` ✓ ;
`<sha>` = the coworld's `manifest_sha` `sha256:1002ad49f6a1d222ab8c3f22d2b348c93ec6e930ab1a5cb21ebf6683b5ca3699`
(URL-encoded), matching `STATE.coworld.manifest_sha` ✓ ; `ready: true` and the path ends
`/index.html` ⇒ static delivery ✓ ; **no `/client/replay` anywhere** ✓.

Status: **TRUE**.

---

## 7. Certification declared the static bundle — TRUE

Source: **the committed `runs/2026-08-25-chemistry/release-result.json`** (phase 40's artifact
copy, release run `32818992277`). It was present; no re-download was needed.

```
$ jq -r '.certify.replay_liveness' runs/2026-08-25-chemistry/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Surrounding `certify.output_tail` from the same file, for context (all ten transcript steps):
```
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
and `certify.ok: true`.

Status: **TRUE** — contains `Replay liveness: skipped (static replay bundle declared`, read from
the committed artifact copy.

---

## 8. The viewer was EXECUTED, then judged — TRUE

*(a) Dispatch.* The iframe `src` from check 6 (full URL, `?replay=` and all) was opened in
headless chromium by CI, because this sandbox has no screen and no browser:

```
$ SRC=$(jq -r .viewer_url session6.json)
$ gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
dispatched 2026-08-25T08:18:04Z
$ gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
   | jq -r 'sort_by(.createdAt)|reverse|.[0:2][]|[.databaseId,.createdAt,.status]|@tsv'
32825902427	2026-08-25T08:18:04Z	in_progress
32822191156	2026-08-25T07:33:38Z	completed
$ gh run watch 32825902427 -R Metta-AI/coworld-builder --exit-status
✓ viewer-check in 37s (ID 97733720990)   exit=0
$ gh run download 32825902427 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-25-chemistry/viewer-check
runs/2026-08-25-chemistry/viewer-check/{viewer-smoke.json, viewer-smoke.png, smoke-stdout.txt, smoke-stderr.txt}
```
Run **32825902427** (green), dispatched by this phase at 08:18:04Z against the check-6 `src`.
(An earlier dispatch this phase, run `32822191156` at 07:33:38Z, rendered round 3's replay while
that was the featured match — same result, `loaded: true`, clocks `SHIFT 0 / 12 TICK 5 OF 720` →
`SHIFT 6 / 12 TICK 377 OF 720` → `FINAL SHIFT OVER`. The artifact committed under
`runs/2026-08-25-chemistry/viewer-check/` is the **later** run, matching the check-6 `src`.)

*(b) Readouts, verbatim from `runs/2026-08-25-chemistry/viewer-check/viewer-smoke.json`.*

```
$ jq -c '{loaded, ms, clock, scorebug, feed_lines}' viewer-smoke.json
{"loaded":true,"ms":9684,"clock":"SHIFT 0 / 12 TICK 1 OF 420","scorebug":"AMBER CHARGE 3 STARVING resin 0 · spark 0 COBALT CHARGE 3 STARVING resin 0 · brine 0 SHIFT 0 / 12 TICK 1 OF 420 BERYL CHARGE 3 STARVING spark 0 · brine 0","feed_lines":0}

$ jq -c '.signals' viewer-smoke.json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}

$ jq -r '.failure // "no failure"' viewer-smoke.json
no failure

$ jq -c '.canvas_text' viewer-smoke.json
{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
```

Three clock readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | clock text |
|---|---|
| 0 %   | `SHIFT 0 / 12 TICK 1 OF 420` |
| 50 %  | `SHIFT 3 / 12 TICK 227 OF 420` |
| 100 % | `FINAL SHIFT OVER` |

`loaded: true` (via `data-replay-loaded="true"` on `<html>`; `data_replay_error: null`), first
frame in **9 684 ms**, and the three clock readouts **all differ**. Both conditions hold.

*(c) The replay JSON the viewer was asked to draw* — ordered excerpts from `/tmp/ep-r6.replay`
(`tick / shift / kind / seat / payload`):

early:
```
0	1	order	0	waiting by the vats
0	1	order	1	resin to Amber - all reactors at charge 3, all stocks empty. Taking primary lan…
0	1	order	2	Room needs 6 deliveries this shift (2 per vat). Starting cold-start: amber gets…
0	1	order	3	waiting by the vats
0	1	order	4	resin to Cobalt
11		take	1	resin
16		take	2	resin
35		drop	1	resin
44		drop	2	resin
55		take	1	resin
60	1	shift
```
middle:
```
310		drop	4	resin
319		take	1	spark
330		take	4	resin
340		take	2	brine
343		drop	1	spark
350		drop	2	brine
360		take	3	spark
360	6	shift
360	7	order	0	vats are dead - restarting Beryl
```
late:
```
404		take	3	spark
407		drop	0	spark
410		take	4	resin
414		drop	2	brine
414		restart		cobalt
417		take	1	spark
420		drop	6	spark
420		cold		cobalt
420	7	shift
420		famine
420		end
```
```
$ jq -r '.results' /tmp/ep-r6.replay
{ … "reactions":[0,0,2],"food_made":3,"food_rotted":0,"cold_starts":1,
  "shifts":7,"reason":"complete","ending":"famine"}
```

### Spectator judgment

It is legible, it is unmistakably this game, and it wears the starter's chrome. The committed
`viewer-smoke.png` — captured at the 100 % scrub, so it is the **endcard** — reads, top to
bottom: a three-vat scorebug strip (`0 CHARGE AMBER / COLD / NEEDS 3+3`, `0 CHARGE COBALT / COLD
/ NEEDS 3+3`, `BERYL CHARGE 0 / COLD / NEEDS 3+3`) with `FINAL — SHIFT OVER` centred between
them; a roster ribbon of eight chips carrying both the alias and the owning policy
(`BORAX daveey 1`, `CINDER daveey-1 1`, `DRAM richard 1`, `ARGON relh 0`, `EMBER Baseline 0`,
`FLINT Baseline (2) 0`, `GILT Baseline (3) 0`, `HOB Baseline (4) 0`); the dimmed factory floor
behind it with cog sprites, three vats, molecule tokens and vents still visible; the endcard
itself — `BORAX EATS BEST`, the ending in words `FAMINE · DAVEEY`, the line
`3 food made · 0 rotted · 1 cold start`, all eight scores as chips, and `REPLAYING IN 4`; the
`HOARDING / nobody, yet` panel bottom-right; and at the bottom the full transport strip
(restart, step-back, pause, `+5s`, step, loop, fast-forward, a `spoilers` toggle, `BORAX WINS`,
`420 / 420`, and `1× 2× 3× 4× 8× 16×` speed buttons) over a scrubber whose `CYCLE CHARGE`
momentum graph descends in three visible steps to the floor, with beat labels pinned on the
track (`AMBER COLD`, `BERYL COLD`, `COBALT COLD`, `FAMINE`). That is paintbot/raid/hive chrome —
same transport strip, same scrubber-with-momentum-graph, same scorebug, same endcard — not a
rewrite that only shares ids (the cogame-gridlock failure).

Picture and record agree. The replay says three reactors starting at charge 3, one restart at
t=414, `cold cobalt` at t=420, `famine` latched, `food_made: 3`, `cold_starts: 1`, seven shifts,
scores `[0,1,1,1,0,0,0,0]`. The screenshot's scorebug says all three vats at charge 0 and COLD,
its endcard says `FAMINE`, `3 food made · 1 cold start`, and its chips say `BORAX 1 CINDER 1
DRAM 1 ARGON 0 EMBER 0 FLINT 0 GILT 0 HOB 0` — the same numbers in the same order. The momentum
graph's three descending steps are the three vats going cold, in the order the beat labels give
them. It advances, too: the clock moved `SHIFT 0 … TICK 1 OF 420` → `SHIFT 3 … TICK 227 OF 420` →
`FINAL SHIFT OVER`, so this is a replay, not a screenshot.

Two honest legibility observations, neither of which makes item 8 false:
1. `feed_lines: 0`. The smoke probe counts DOM children of `#feed, .feed, #log`; chemistry paints
   its ticker and beats into the wasm canvas, and `canvas_text.total` is 0 for the same reason
   (the probe instruments DOM text draws, not wasm ones). I am **not** claiming a DOM readout of
   the feed — what I can point at is the rendered picture, where the beat labels do appear on the
   scrub track and the `HOARDING` panel is populated. The clock and scorebug, by contrast, *were*
   read out of the DOM and are quoted above.
2. Two cosmetic collisions in the rendered frame: the header still reads `SHIFT 0 / 12` on an
   episode that ended at shift 7 by famine (denominator is the configured limit, not the played
   count), and the beat labels near the right edge of the scrub track overlap
   (`COBALT COLD` on top of `FAMINE`), as do `AMBER COLD`/`BERYL COLD` at the left. Legibility
   notes for phase 30, not correctness failures.

The one thing a spectator loses on this particular featured match is drama: round 6 is a dead
room (3 food made in 7 shifts). That is a consequence of the field — two outside entrants running
scripted policies plus four scripted fillers, against two LLM champions — and the design
explicitly sanctions famine as a completed game (`design.md:262`). The busy version exists on the
same bundle: this phase's earlier dispatch, run `32822191156` against round 3's replay, reported
`loaded: true` with clocks `SHIFT 0 / 12 TICK 5 OF 720` → `SHIFT 6 / 12 TICK 377 OF 720` →
`FINAL SHIFT OVER` and the scorebug string `AMBER CHARGE 3 STARVING resin 0 · spark 0 …`, and
round 3's replay `results` (fetched under check 4's precedent block) records
`"food_made":152,"food_rotted":0,"cold_starts":0,"shifts":12,"reason":"complete","ending":"shift_limit"`.
That run's png is not committed here — `runs/2026-08-25-chemistry/viewer-check/` holds the
check-6-matching run `32825902427` — so the only rendered frame I describe above is that one.

Status: **TRUE** — `loaded: true`, three differing clock readouts, no failure, and the drawn
frame is legible, is Chemistry, and matches the record.

---

## Summary

| # | check | verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 2,3,4,5,6 completed (round 1 failed on the documented pre-filler race) |
| 2 | both champions ranked, fillers absent/Baseline | **TRUE** — daveey-1 rank 1, daveey rank 3, 5 rounds each; fillers absent |
| 3 | latest round's episode request completed with a replay | **TRUE** — `ereq_76bcca2e-…`, `completed`, replay `…/46fc7f16-….replay`, seats 1/2 = daveey/daveey-1 |
| 4 | replay bytes valid and show the game | **TRUE** — strict JSON, `chemistry.replay.v1`, `complete`/`famine`, champion seats 14/14 `llm`, 0 fallbacks |
| 5 | hosted log clean | **TRUE** — `CLEAN` on the decoded round-6 log; rounds 2–5 throttled by a platform-wide Bedrock 429, cross-checked against coins and hanabi |
| 6 | public page uses the static replay path | **TRUE** — featured match `chemistry.r6.e1` in the SSR playlist; `viewer_url` is the static `/index.html?replay=` route, `ready: true` |
| 7 | certification declared the static bundle | **TRUE** — `Replay liveness: skipped (static replay bundle declared; …)` from the committed `release-result.json` |
| 8 | viewer executed and judged | **TRUE** — run `32825902427`, `loaded: true` in 9 684 ms, clocks `TICK 1 OF 420` → `TICK 227 OF 420` → `FINAL SHIFT OVER`, endcard legible and paintbot-shaped |

Non-blocking observations passed to the coordinator:
- chemistry's LLM player has no **model-level** fallback; hanabi switches haiku→sonnet under a
  throttle and keeps playing, chemistry drops to a scripted order. Rounds 2–5 were scripted at the
  champion seats for exactly this reason.
- Header shows `SHIFT n / 12` on a famine-ended episode; beat labels overlap at both ends of the
  scrub track.
- `feed_lines`/`canvas_text` read 0 because the shell paints into the wasm canvas; the DOM probe
  cannot see it. Not a defect, but it means the CI probe cannot police feed legibility for this
  coworld.
