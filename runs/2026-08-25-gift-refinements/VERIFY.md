# VERIFY — gift-refinements   (2026-08-26T03:12Z)

Verdict: **2 items false** (checks 4 and 5)

Run: `2026-08-25-gift-refinements` · coworld `cow_686eadd9-7594-425c-98b2-854deb9acdd1` v0.1.1 ·
league `league_aa42c0da-031b-49b1-9524-e4acc85fd2f6` · division `div_3c0d2b61-0e4a-4d9c-b27f-524158fede53`.

**Latest completed round frozen at round 4** (`round_08811b54-4f9e-425e-be2b-b25acb68cb18`) as of
2026-08-26T03:10:27Z. Checks 3–6 and 8 are evaluated against that round. Wall-clock budget:
verifier started 02:38Z, bound expires 03:53Z — not exhausted; work stopped because the evidence
was conclusive, not because time ran out.

Headers sent on every Observatory call: `Authorization` (bearer, value never printed),
`User-Agent: coworld-builder/1.0`; `X-Use-Elevated-Privileges: true` added on `artifacts/logs`.

---

## Headline finding (drives checks 4 and 5)

The lobby closes before the two **champion** player pods have connected, so on 2 of the 3
completed rounds both champion seats played the **scripted `reciprocator` baseline** for almost the
whole episode. `design.md` line 320: *"A scripted policy seated as a champion is a failure state."*
The per-round game-container evidence is pasted under check 4; the summary:

| round | log: lobby line | log: episode summary | champion (seat 0+1) order sources, n=24 |
|---|---|---|---|
| 2 | `lobby closed with 3/6 seats connected, 3 registered` | `llmOrders=1 fallbacks=0` | `llm=1  scripted=23` |
| 3 | `lobby closed with 6/6 seats connected, 6 registered` | `llmOrders=24 fallbacks=0` | `llm=23 retry=1` ✅ |
| 4 | `lobby closed with 4/6 seats connected, 4 registered` | `llmOrders=2 fallbacks=1` | `llm=2 fallback=1 scripted=21` |

Round 3 proves the coworld *can* play; rounds 2 and 4 prove it usually does not. This is a race,
not a platform outage — Bedrock answered every call it was given (0 `LLM provider is unavailable`
lines in any of the three logs).

---

## 1. ≥2 completed rounds after fillers were set — **TRUE**

Fillers registered 2026-08-26T02:36Z (`log.md` line "50 filler-policies 200: reciprocator:v2 +
hoarder:v2 registered"), before round 2 was created. Qualifying rounds must therefore have
`round_number ≥ 2`.

```
GET https://softmax.com/api/observatory/v2/rounds?league_id=league_aa42c0da-031b-49b1-9524-e4acc85fd2f6&limit=20
headers: Authorization, User-Agent
2026-08-26T03:10:27Z → HTTP 200
```

Deviation from the prompt's quoted filter, noted per instruction: the prompt uses
`jq '[.entries[]|…]'`. `/rounds` returned `{entries:…}` on every call this run, but I used the
dual-shape guard `if type=="array" then . else .entries end` from
`playbooks/observatory-api.md` §2 because `/leagues` and `/policy-versions` were bare arrays this
run. Count filter, run verbatim otherwise:

```bash
jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
```
```
3
```

Full body (fields `round_number,id,status,error,created_at`):

```json
[
    {
        "round_number": 4,
        "id": "round_08811b54-4f9e-425e-be2b-b25acb68cb18",
        "status": "completed",
        "error": null,
        "created_at": "2026-08-26T03:06:25.758767Z"
    },
    {
        "round_number": 3,
        "id": "round_6e60126d-0a6d-4b32-97c2-9deb5530e5df",
        "status": "completed",
        "error": null,
        "created_at": "2026-08-26T02:51:25.031852Z"
    },
    {
        "round_number": 2,
        "id": "round_46f1fb01-644f-485d-935e-832e20bfe201",
        "status": "completed",
        "error": null,
        "created_at": "2026-08-26T02:36:24.631756Z"
    },
    {
        "round_number": 1,
        "id": "round_5c4fa064-0039-438c-8fa8-251ac256f07a",
        "status": "failed",
        "error": "Temporal RoundWorkflow failed before settling the round.",
        "created_at": "2026-08-26T02:36:01.142057Z"
    }
]
```

Status: **TRUE** — rounds **2, 3 and 4** are `completed`, all with `round_number ≥ 2`, all created
after the fillers were registered at 02:36Z. Round 1 is `failed`; its error is recorded verbatim
above (`"Temporal RoundWorkflow failed before settling the round."`) and it is excluded, exactly as
`playbooks/observatory-api.md` §6 predicts for a `trigger-round` issued before any filler existed.

---

## 2. Both champions ranked; fillers absent/Baseline — **TRUE**

```
GET https://softmax.com/api/observatory/v2/divisions/div_3c0d2b61-0e4a-4d9c-b27f-524158fede53/leaderboard
headers: Authorization, User-Agent
2026-08-26T03:10:27Z → HTTP 200
```
```bash
jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey	gift-refinements-mirror:v2	1011.7471336336108	3	2.0
2	daveey-1	gift-refinements-patron:v2	988.2528663663891	3	1.0
```

Full rows (bare list, not `.entries` — confirmed):

```json
[
  {"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
   "score":1011.7471336336108,"score_label":"MMR","rounds_played":3,"episode_wins":2.0,
   "win_rate":1.0,"policy_label":"gift-refinements-mirror:v2"},
  {"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
   "score":988.2528663663891,"score_label":"MMR","rounds_played":3,"episode_wins":1.0,
   "win_rate":0.0,"policy_label":"gift-refinements-patron:v2"}
]
```

Status: **TRUE** — `daveey` (rank 1, `gift-refinements-mirror:v2`, `rounds_played=3`) and
`daveey-1` (rank 2, `gift-refinements-patron:v2`, `rounds_played=3`) are both present with
`rounds_played ≥ 1`. The list has exactly two rows: neither filler
(`gift-refinements-reciprocator:v2`, `gift-refinements-hoarder:v2`) appears at all.

---

## 3. Latest round's episode request completed with a replay — **TRUE**

```bash
R=round_08811b54-4f9e-425e-be2b-b25acb68cb18   # max_by(.round_number) over completed rounds
```
```
GET https://softmax.com/api/observatory/v2/episode-requests?round_id=round_08811b54-4f9e-425e-be2b-b25acb68cb18&limit=20
headers: Authorization, User-Agent
2026-08-26T03:08Z → HTTP 200
```
```
ereq_96b0e5fa-2c5b-4d41-94de-3881928d4db5	completed
```
```
GET https://softmax.com/api/observatory/v2/episode-requests/ereq_96b0e5fa-2c5b-4d41-94de-3881928d4db5
headers: Authorization, User-Agent → HTTP 200
jq '{status, replay_url, participants, participant_scores}'   (participants trimmed to the identity fields)
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/8e5df6a9-8ab6-4ace-abd8-ec29e912538e.replay",
  "participants": [
    {"position": 0, "policy_name": "gift-refinements-mirror",       "version": 2, "player_name": "daveey",   "is_filler": false},
    {"position": 1, "policy_name": "gift-refinements-patron",       "version": 2, "player_name": "daveey-1", "is_filler": false},
    {"position": 2, "policy_name": "gift-refinements-hoarder",      "version": 2, "player_name": "daveey",   "is_filler": true},
    {"position": 3, "policy_name": "gift-refinements-hoarder",      "version": 2, "player_name": "daveey",   "is_filler": true},
    {"position": 4, "policy_name": "gift-refinements-reciprocator", "version": 2, "player_name": "daveey",   "is_filler": true},
    {"position": 5, "policy_name": "gift-refinements-hoarder",      "version": 2, "player_name": "daveey",   "is_filler": true}
  ],
  "participant_scores": [
    {"position": 0, "score": 79.0}, {"position": 1, "score": 81.0}, {"position": 2, "score": 74.0},
    {"position": 3, "score": 64.0}, {"position": 4, "score": 7.0},  {"position": 5, "score": 58.0}
  ]
}
```

Status: **TRUE** — `status == "completed"`, `replay_url` non-null, `participants` name `daveey`
(position 0) and `daveey-1` (position 1) with `is_filler: false`; positions 2–5 carry
`is_filler: true`. Note the API returns filler rows by policy name with an `is_filler` flag rather
than the display string `Baseline (N)`; the `Baseline (N)` naming the prompt describes is what the
**replay** carries (`results.names` below) and what the leaderboard suppresses.

---

## 4. Replay bytes valid and showing the game — **FALSE**

The bytes are fine. **What they show is a scripted episode in the champion seats.**

```
GET https://softmax-public.s3.amazonaws.com/replays/8e5df6a9-8ab6-4ace-abd8-ec29e912538e.replay
2026-08-26T03:09Z → HTTP 200  bytes=166017
```
```bash
jq -e . /tmp/ep4.replay >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .results.reason, .results.ending' /tmp/ep4.replay
```
```
strict UTF-8 JSON: ok
gift-refinements.replay.v1
complete
round_limit
```

Protocol cross-check against the manifest —
`GET /v2/coworlds/cow_686eadd9-7594-425c-98b2-854deb9acdd1` → HTTP 200:

```
manifest_hash: sha256:6cfd8cc359900a6ae22894237390108a78acd14ed66d0921b3f468b94780e305
manifest text: "…one strict-UTF-8 JSON document, protocol gift-refinements.replay.v1, carrying the aliases, the policy names…"
```
Matches `STATE.coworld.manifest_sha` and the replay's `protocol`. ✅

### Attempt 1 — the prompt's filters, run verbatim

```bash
jq -r '[.events[]|select(.type=="decision")]|length' /tmp/ep4.replay   →  0
jq -r '[.events[]|select(.fallback==true)]|length'   /tmp/ep4.replay   →  0
```

Both return `0` because **this coworld's replay schema has no `type` or `fallback` keys**. Event
kind is `k`; the decision row is `k=="order"` and its provenance field is `source`, per
`design.md` line 623:

> `| order | t, seat, round, job, target, gift, consume, clamped, source ("llm"\|"retry"\|"fallback"\|"scripted"), say, notes, latencyMs | one per seat per round boundary |`

Observed event kinds in this replay:
`collect=227 consume=24 defect=5 end=1 gift=106 order=72 round=12 spawn=217 spill=34`.
Recording this deviation as instructed; the two schema-correct attempts follow.

### Attempt 2 — schema-correct provenance count on the champion seats

```bash
jq -r '[.events[]|select(.k=="order" and (.seat==0 or .seat==1))|.source]
       |group_by(.)|map("\(.[0])=\(length)")|join(" ")' /tmp/ep4.replay
```
```
fallback=1 llm=2 scripted=21
```

24 champion decisions (2 seats × 12 rounds): **21 scripted, 1 fallback, 2 llm.** Every one of the
21 `scripted` rows has `latencyMs: 0` and an empty `notes` — no model was consulted. The full
champion order table:

```
round seat source    job     target gift consume say                                          latencyMs
1     0    scripted  collect null   0    never   collecting                                   0
1     1    scripted  collect null   0    never   collecting                                   0
2     0    scripted  meet    Bex    4    never   opening with BEX                             0
2     1    scripted  meet    Aro    4    never   opening with ARO                             0
3     0    scripted  meet    Bex    10   end     returning 10 to BEX                          0
3     1    scripted  meet    Aro    10   end     returning 10 to ARO                          0
4     0    scripted  collect Bex    0    never   collecting for BEX                           0
4     1    scripted  collect Aro    0    never   collecting for ARO                           0
5     0    scripted  collect Bex    1    never   returning 1 to BEX                           0
5     1    scripted  collect Aro    1    never   returning 1 to ARO                           0
6     0    scripted  meet    Bex    1    end     returning 1 to BEX                           0
6     1    scripted  collect Aro    1    never   returning 1 to ARO                           0
7     0    scripted  collect Bex    0    never   collecting for BEX                           0
7     1    scripted  meet    Aro    4    end     returning 4 to ARO                           0
8     0    scripted  meet    Bex    10   end     returning 10 to BEX                          0
8     1    scripted  collect Aro    0    never   collecting for ARO                           0
9     0    scripted  collect Bex    0    never   collecting for BEX                           0
9     1    scripted  meet    Aro    10   end     returning 10 to ARO                          0
10    0    scripted  meet    Bex    10   end     returning 10 to BEX                          0
10    1    scripted  collect Aro    0    never   collecting for ARO                           0
11    0    llm       collect null   0    never   R11: collecting to restart chain             2029
11    1    scripted  meet    Aro    10   end     returning 10 to ARO                          0
12    0    fallback  meet    Bex    10   end     returning 10 to BEX                          0
12    1    llm       hold    null   0    end     Final round: holding position, banking at close.  4138
```

### Attempt 3 — cross-check against the hosted game container's own episode summary

Decoded from `GET /episode-requests/ereq_96b0e5fa-…/artifacts/logs` (headers: `Authorization`,
`User-Agent`, `X-Use-Elevated-Privileges`; HTTP 200, 3511 bytes raw / 3459 decoded):

```
gift-refinements: seat 4 connected
{"k":"register","seat":4,"policy":"reciprocator","kind":"scripted","baseline":"reciprocator"}
gift-refinements: seat 3 connected
{"k":"register","seat":3,"policy":"hoarder","kind":"scripted","baseline":"hoarder"}
gift-refinements: seat 2 connected
{"k":"register","seat":2,"policy":"hoarder","kind":"scripted","baseline":"hoarder"}
gift-refinements: seat 5 connected
{"k":"register","seat":5,"policy":"hoarder","kind":"scripted","baseline":"hoarder"}
gift-refinements: lobby closed with 4/6 seats connected, 4 registered
gift-refinements: seat 0 connected
{"k":"register","seat":0,"policy":"prompt","kind":"llm","baseline":"reciprocator"}
gift-refinements: seat 1 connected
{"k":"register","seat":1,"policy":"prompt","kind":"llm","baseline":"reciprocator"}
...
gift-refinements: episode finished reason=complete ending=round_limit rounds=12 gifts=106 minted=308 llmOrders=2 fallbacks=1
```

`lobby closed with 4/6 seats connected` — **both champion pods connected after the lobby had
already closed and the round loop had started**, so their `register` frames landed 10 rounds late.
`llmOrders=2` for a 12-round, 2-LLM-seat episode where the design budgets 24.

The same race, in the other two completed rounds (fetched this run):

*Round 2* (`ereq_c0fd007b-b2f1-4399-8bd2-f1f2fed1784c`, log HTTP 200, 4196 bytes):
```
gift-refinements: lobby closed with 3/6 seats connected, 3 registered
gift-refinements: seat 5 connected
{"k":"register","seat":5,"policy":"hoarder","kind":"scripted","baseline":"hoarder"}
gift-refinements: seat 0 connected
{"k":"register","seat":0,"policy":"prompt","kind":"llm","baseline":"reciprocator"}
gift-refinements: seat 1 connected
gift-refinements: seat 4 disconnected
...
gift-refinements: episode finished reason=complete ending=round_limit rounds=12 gifts=96 minted=278 llmOrders=1 fallbacks=0
```
Seat 1 (`daveey-1`) **never emitted a `register` line at all** — champion #2 played
`reciprocator` for all 12 rounds. Champion source counts for round 2: `llm=1 scripted=23`. This is
verbatim the failure `design.md` line 558 says it was guarding against
("paintball, 2026-08-25 — a dropped registration silently made a champion seat play scripted").

*Round 3* (`ereq_a98be2f2-3303-44dd-ae33-2bb112ec52b6`, log HTTP 200, 53814 bytes) — the healthy one:
```
gift-refinements: lobby closed with 6/6 seats connected, 6 registered
gift-refinements: episode finished reason=complete ending=round_limit rounds=12 gifts=142 minted=370 llmOrders=24 fallbacks=0
```
Champion source counts for round 3: `llm=23 retry=1`, zero scripted, and the `notes` are exactly
what check 4 asks for — non-scripted, non-trivial:
```
r3  seat0 llm  meet Bex 1  "R3: Bex reciprocated (gave 3, I gave 1). Tit-for-tat: return 1 beam."
r6  seat1 llm  meet Aro 5  "R6 status: holding 5 raw, 3 refined, 0 super. Aro at (4,2), 3 cells north - hittable.
                            Confirmed partner: Aro gave +12 net across R2-R5…"
r12 seat1 llm  hold null 0 "R12 final tick 660/720. Holding 0 tokens. Aro partnership ended R10 (no return R11)…
                            Strategy failed: chain broke when Aro stopped returning. Accept loss."
```

### Verdict

Status: **FALSE**. The bytes pass every mechanical test — strict UTF-8 JSON, `protocol` matches
the manifest, `results.reason == "complete"` (no `deadline` exception needed) — but the substantive
requirement, *"champion seats' decisions are non-scripted with non-trivial content"*, fails on the
latest completed round: **21 of 24 champion decisions are `scripted` and 1 is a `fallback`; only 2
are `llm`.** All three attempts agree, and the defect reproduces on 2 of the 3 completed rounds.
No documented exception in `prompts/60-verify.md` or `docs/SPEC.md` covers a scripted champion —
`design.md` line 320 calls it a failure state outright.

Root cause visible in the evidence, for the fixer: the lobby's adaptive close (`design.md` line
556: *"the lobby returns as soon as every connected socket has registered"*) fires the instant the
scripted filler pods have registered, without waiting for the champion pods to connect. The
10-second held-registration re-send (line 557) does not help, because by then the round loop is
already running. `playerConnectTimeoutSeconds = 180` is never reached.

---

## 5. Hosted game log is clean — **FALSE**

```
GET https://softmax.com/api/observatory/v2/episode-requests/ereq_96b0e5fa-2c5b-4d41-94de-3881928d4db5/artifacts/logs
headers: Authorization, User-Agent, X-Use-Elevated-Privileges
2026-08-26T03:09Z → HTTP 200  bytes=3511
```

The body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it was
decoded per-repr with `ast.literal_eval` before grepping, per `playbooks/observatory-api.md` §10.

### Attempt 1 — decoded grep, latest round (4)

```bash
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/g_logs.decoded.txt || echo CLEAN
```
```
30:gift-refinements llm: seat 0 attempt 1 failed, falling back if it fails again: unknown job consume (expected collect|meet|hold|evade)
31:gift-refinements llm: seat 0 attempt 2 failed, falling back if it fails again: target is required when job is meet or gift > 0
32:gift-refinements llm: seat 0 falling back to scripted order (parse_error) on round 12
```

Not `CLEAN`. Per-pattern breakdown on the decoded text:

| pattern | matches |
|---|---|
| `falling back` | 3 |
| `LLM provider is unavailable` | 0 |
| `cut off at max_tokens` | 0 |
| `rejected` | 0 |

Line 32 is the **real** fallback, not just a retry notice — `design.md` line 547 names that exact
string as the marker of a seat that gave up and played the scripted order:
> *"Still failing → that seat plays the `reciprocator` order for that round, logged as
> `gift-refinements llm: seat N falling back to scripted order` and recorded on the `order` event
> as `"source":"fallback"`."*

Corroborated by the structured rows in the same log and by the replay row for round 12 seat 0
(`source: "fallback"`, pasted under check 4):
```
gift-refinements: {"k":"fallback","round":12,"seat":0,"attempt":1,"cause":"parse_error","detail":"unknown job consume (expected collect|meet|hold|evade)"}
gift-refinements: {"k":"fallback","round":12,"seat":0,"attempt":2,"cause":"parse_error","detail":"target is required when job is meet or gift > 0"}
gift-refinements: {"k":"fallback","round":12,"seat":0,"attempt":2,"cause":"parse_error","detail":"seat fell back to the reciprocator order"}
gift-refinements: episode finished reason=complete ending=round_limit rounds=12 gifts=106 minted=308 llmOrders=2 fallbacks=1
```

### Attempt 2 — raw (undecoded) grep, same round

```bash
grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/g_logs.txt
```
```
1
```
(1 raw *line*, because the whole game container is one `b'…'` repr — which is precisely the
undercount `playbooks/observatory-api.md` §10 warns about. The decoded count of 3 is the true one.)

### Attempt 3 — a different round (3), per the retry budget's "different round"

```
GET .../episode-requests/ereq_a98be2f2-3303-44dd-ae33-2bb112ec52b6/artifacts/logs
headers: Authorization, User-Agent, X-Use-Elevated-Privileges
2026-08-26T03:01Z → HTTP 200  bytes=53814
```
```
126:gift-refinements llm: seat 0 attempt 1 failed, falling back if it fails again: unknown job consume (expected collect|meet|hold|evade)
```
1 match. Round 3 is the *milder* case — the retry landed (`source: "retry"` on the round-12 order,
`fallbacks=0` in the episode summary), so no seat actually degraded. It is still not `CLEAN`.

For completeness, round 2's log **was** `CLEAN` (0 matches, 4196 bytes) — but only because no seat
was registered as LLM long enough to fail.

### Verdict

Status: **FALSE**. The latest round's log carries 3 matching lines, including one real
`falling back to scripted order`. The failure cause is `parse_error` — the model twice returned a
reply outside the declared job enum (`consume` is not one of `collect|meet|hold|evade`, and a
`meet` was emitted without a `target`). This is **not** the documented `LLM provider is
unavailable` capacity exception (0 occurrences; Bedrock returned HTTP 200 on every call in every
log this run, e.g. round 2's sidecar line `"ok":true,"status_code":200,"latency_ms":2146.9`), and
it is **not** `cut off at max_tokens` (0 occurrences), so the `maxOutputTokens` remedy does not
apply. It is a prompt/schema-adherence defect in `gift-refinements-mirror`'s prompt or in the
reply validator's tolerance, and no documented exception covers it. Marked FALSE.

---

## 6. Public page uses the static replay path — **TRUE**

### Source A — raw HTML (attempted first, per the prompt)

```
GET https://softmax.com/gift-refinements
2026-08-26T03:09:14Z → HTTP 200  bytes=567413
grep -o '<iframe[^>]*src="[^"]*"'
```
```
GREP: no iframe in raw HTML (client-rendered)
```
0 `iframe` substrings in the whole document. Treated as *unknown*, not a false negative, exactly as
the prompt and `playbooks/observatory-api.md` §Featured match instruct.

### Source B — the coworld detail API

```
GET https://softmax.com/api/observatory/v2/coworlds?limit=200 → HTTP 200
jq '.[]|select(.name=="gift-refinements" and .canonical==true)|{id,canonical,replay_viewer,featured_match}'
```
```json
{"id":"cow_686eadd9-7594-425c-98b2-854deb9acdd1","canonical":true,"replay_viewer":null,"featured_match":null}
```
`featured_match: null` — which the playbook records as **null platform-wide** since the lighthouse
run and therefore not evidence either way.

### Source C — the SSR playlist + the session call the page's own JS makes (**the source I used**)

Featured match, server-rendered into the page fetched above at `state.playlist[0]`:

```json
"playlist":[{"episodeId":"a835f7ab-32b4-402d-8bd0-a3ccf80831cc",
  "coworldId":"cow_686eadd9-7594-425c-98b2-854deb9acdd1",
  "coworldName":"gift-refinements","coworldVersion":"0.1.1",
  "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/8e5df6a9-8ab6-4ace-abd8-ec29e912538e.replay",
  "finishedAt":"2026-08-26T03:07:56.050670Z","roundNumber":4,"episodeNumber":1,
  "code":"gift-refinements.r4.e1","matchup":{"divisionId":"div_3c0d2b61-…
```

```
POST https://softmax.com/api/observatory/v2/coworlds/replays/session
headers: Authorization, User-Agent, content-type
body: {"coworld_id":"cow_686eadd9-7594-425c-98b2-854deb9acdd1",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/8e5df6a9-8ab6-4ace-abd8-ec29e912538e.replay"}
2026-08-26T03:09:20Z → HTTP 200
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_686eadd9-7594-425c-98b2-854deb9acdd1/sha256%3A6cfd8cc359900a6ae22894237390108a78acd14ed66d0921b3f468b94780e305/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F8e5df6a9-8ab6-4ace-abd8-ec29e912538e.replay&v=2",
  "ready": true
}
```

Status: **TRUE** — source used: **C** (SSR payload + `POST /coworlds/replays/session`), after A
returned nothing and B returned the platform-wide `null`. A featured match is present
(`gift-refinements.r4.e1`, two ranked players in `matchup`). The iframe `src` is
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` with
`<sha>` = `sha256%3A6cfd8cc359900a6ae22894237390108a78acd14ed66d0921b3f468b94780e305`, the
coworld's manifest hash, matching `STATE.coworld.manifest_sha`. `ready: true`, path ends
`/index.html`. **No `/client/replay` pod URL anywhere.**

---

## 7. Certification declared the static bundle — **TRUE**

Source: the **committed** `runs/2026-08-25-gift-refinements/release-result.json` (the copy phase 40
downloaded from release run `32922682398` and committed). It was present; no re-download was
needed.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-25-gift-refinements/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Surrounding context from the same file:
```json
{"version":"0.1.1","ok":true,"cow_id":"cow_686eadd9-7594-425c-98b2-854deb9acdd1",
 "manifest_sha":"sha256:6cfd8cc359900a6ae22894237390108a78acd14ed66d0921b3f468b94780e305",
 "canonical":true,"hosted_smoke":"passed","hosted_certification":"certified",
 "certify":{"ok":true,"replay_liveness":"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"},
 "secret_put":true,"errors":[],"step_failed":null}
```
and from `certify.output_tail`: `Transcript: coworld-executable (10 steps passed)`.

Status: **TRUE** — contains `Replay liveness: skipped (static replay bundle declared`. Read from
the committed `runs/2026-08-25-gift-refinements/release-result.json`, **not** from `/tmp`.

---

## 8. Spectator judgment — the viewer was EXECUTED — **TRUE**

Dispatched against the check-6 iframe `src` (round 4's featured replay):

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_686eadd9-7594-425c-98b2-854deb9acdd1/sha256%3A6cfd8cc359900a6ae22894237390108a78acd14ed66d0921b3f468b94780e305/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F8e5df6a9-8ab6-4ace-abd8-ec29e912538e.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90   # 03:09:23Z
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 5 \
  | jq -r 'sort_by(.createdAt)|reverse|.[0].databaseId'
```
```
32925387074	2026-08-26T03:09:23Z	in_progress      <- createdAt matches the dispatch instant, not "the latest blind"
32924883541	2026-08-26T03:01:23Z	completed
32923659915	2026-08-26T02:41:21Z	completed
```
```
gh run view 32925387074 -R Metta-AI/coworld-builder --json conclusion  →  {"conclusion":"success"}
gh run download 32925387074 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-25-gift-refinements/viewer-check
```

Artifact committed at `runs/2026-08-25-gift-refinements/viewer-check/`
(`viewer-smoke.json`, `viewer-smoke.png`, `smoke-stdout.txt`, `smoke-stderr.txt`).

*(Runs 32923659915 and 32924883541 were this verifier's earlier dispatches against rounds 2 and 3
while the ladder was still producing rounds; their artifacts were superseded and are not the
committed evidence. Run 32925387074 is the one that matches the check-6 `src`.)*

### Readouts (verbatim)

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-25-gift-refinements/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":1428,"clock":"ROUND 1 / 12 TICK 0 OF 720","scorebug":"TOKENS BANKED TOKENS 0 0 MINTED · 0 DEFECTIONS ROUND 1 / 12 TICK 0 OF 720 GIFTS GIVEN TOKENS 0 0 MINTED · 0 DEFECTIONS","feed_lines":0}
```
```bash
jq -c '.signals' runs/2026-08-25-gift-refinements/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```
```bash
jq -r '.failure // "no failure"' → no failure
jq -r '.status'                 → OPEN
jq -r '.loading_text'           → null
jq -c '.console_tail'           → []
jq -c '.canvas_text'            → {"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
```

### The three clock readouts

```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-25-gift-refinements/viewer-check/viewer-smoke.json
```

| scrub position | clock readout |
|---|---|
| 0 % | `ROUND 1 / 12 TICK 0 OF 720` |
| 50 % | `ROUND 7 / 12 TICK 376 OF 720` |
| 100 % | `FINAL TICK 719 OF 720` |

Status: **TRUE** — `loaded: true` (via `data-replay-loaded="true"`; the `coworld-replay` bridge was
not used, `bridge_ready: false`, which is the documented alternative) **and** the three clock
readouts differ. The viewer drew a frame at 1428 ms and the timeline advances under the scrubber.

### The replay JSON the viewer was asked to draw

```bash
jq -r '.events[]|[.t,.seat,.k,(.say // …)]|@tsv' /tmp/ep4.replay | head -14      # EARLY
```
```
0	0	order	collecting
0	1	order	collecting
0	2	order	mine
0	3	order	mine
0	4	order	collecting
0	5	order	mine
1	4	collect
1	5	collect
3	0	collect
3	1	collect
3	2	collect
3	3	collect
4	4	collect
4	5	collect
```
```
… MIDDLE (rows 300-312) …
300	4	order	opening with ARO
300	5	order	mine
300	-	spawn
300	-	gift	gift 0->seat0 (recv 1)
301	-	spawn
301	2	collect
302	-	spawn
304	1	collect
305	-	gift	gift 0->seat0 (recv 1)
307	-	spawn
307	-	spawn
307	1	collect
309	-	gift	gift 0->seat0 (recv 1)
```
```
… LATE (last 12) …
716	-	spawn
716	5	collect
717	4	collect
719	-	spawn
719	0	consume
719	1	consume
719	2	consume
719	3	consume
719	4	consume
719	5	consume
719	-	round
719	-	end	complete/round_limit
```
```bash
jq -r '.results' /tmp/ep4.replay
```
```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"],
 "aliases":["Aro","Bex","Cyr","Dov","Eno","Fay"],
 "scores":[79,81,74,64,7,58],
 "win":[false,true,false,false,false,false],
 "total_gifts":106,"total_minted":308,"rounds":12,
 "reason":"complete","ending":"round_limit"}
```

### Screenshot

`runs/2026-08-25-gift-refinements/viewer-check/viewer-smoke.png` (678 276 bytes, 1280×800),
captured after the scrub sweep, i.e. at 100 % / final tick.

### Spectator-judgment paragraph

**It is legible, and it does show the game — and it is unmistakably the starter's chrome.** The
screenshot is a dark 1280×800 board with the coworld-ctf/paintbot furniture intact: the top
**scorebug** strip reads `363 TOKENS · TOKENS BANKED · 308 MINTED · 5 DEFECTIONS` on the left and
`GIFTS GIVEN · 106 TOKENS` on the right with `FINAL / TICK 719 OF 720` centred; below it the
per-seat roster row `BEX daveey-1 ⇄26% 81 | ARO daveey ⇄37% 79 | CYR Baseline ⇄0% 74 | DOV
Baseline ⇄0% 64 | FAY Baseline ⇄0% 58 | ENO Baseline ⇄0% 7`; the bottom **transport strip** carries
restart / step-back / pause / +5s / step-forward / loop / fast-forward, a `spoilers` toggle, the
`BEX WINS 719 / 719` readout and the 1×–16× speed selector; under it the **scrubber with its
momentum graph** labelled `TOKENS IN PLAY`, a sawtooth curve with red round-boundary ticks and the
orange playhead at the far right; and the centre carries the **endcard** — `BEX WINS — daveey-1`,
a `ROUND LIMIT` badge, and `BEX 81 · ARO 79 · CYR 74 · DOV 64 · FAY 58 · ENO 7 — 106 gifts · 308
tokens minted from 227 raw · 5 defections`. The right edge shows the game-specific `TRUST GRAPH`
with the six cogs as nodes and weighted edges (`ARO ⇄ BEX 135 ↔ 107`). Every number on screen
reconciles exactly with the replay JSON above: scores `[79,81,74,64,7,58]`, `win[1]=true` (BEX =
seat 1 = daveey-1), `total_gifts: 106`, `total_minted: 308`, `defect` event count 5,
`ending: "round_limit"`, tick 719 of 720. The picture is neither empty nor frozen — the 0 %/50 %/
100 % clocks advance through `ROUND 1 … ROUND 7 … FINAL`, and the momentum graph traces the
gift-and-consume cycle the events record (a slow climb in tokens-in-play punctuated by the sharp
drops at each round's `consume` burst, matching the 24 `consume` and 106 `gift` events). It is not
a cogame-gridlock-style rewrite: this is the same product as paintbot/raid/hive with
gift-refinements' own scorebug metrics substituted.

Two qualifications, both honest rather than fatal:

1. `feed_lines: 0`. The screenshot is taken at the final tick where the endcard overlay covers the
   board, so no play-by-play feed line is on screen at capture time. I cannot tell from this
   artifact whether the shell has a feed that is empty mid-episode or simply no feed element; the
   `signals` object does not distinguish them. Flagging it as a **legibility observation for phase
   30**, not as a check-8 failure — the clock, scorebug, roster, endcard and momentum graph already
   say who is winning and why.
2. **What the viewer legibly shows is the wrong episode.** This is the check-4/5 failure seen from
   the spectator's seat: the featured match on `softmax.com/gift-refinements` is round 4, in which
   both champions played the scripted `reciprocator` baseline for 21 of 24 decisions. The roster
   row happily labels seats 0 and 1 `ARO daveey` and `BEX daveey-1`, and the endcard crowns
   `BEX WINS — daveey-1` — but daveey-1's "win" was produced by a hard-coded tit-for-tat script,
   not by `gift-refinements-patron:v2`'s prompt. A spectator watching the public page today is
   watching two baselines wearing champion names. The viewer is doing its job faithfully; the
   episode it was handed is not the game this coworld is supposed to be showing.

---

## Definition-of-done roll-up

| # | Item | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** (rounds 2, 3, 4) |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** |
| 3 | Latest round's episode request completed with `replay_url` + correct participants | **TRUE** |
| 4 | Replay bytes valid, champion seats doing the thing the game is about | **FALSE** — 21/24 champion decisions `scripted`, 1 `fallback`, 2 `llm` |
| 5 | Hosted game log clean | **FALSE** — 3 `falling back` lines incl. a real `falling back to scripted order (parse_error) on round 12` |
| 6 | Public page uses static iframe `src` | **TRUE** |
| 7 | Certification declared the static bundle | **TRUE** |
| 8 | Viewer executed: `loaded: true` + three differing clocks | **TRUE** |

**Verdict: 2 items false.** Not certifiable as-is. Two defects, both in the coworld and neither in
the platform:

- **D1 (drives check 4, the serious one).** The lobby closes as soon as the connected sockets have
  registered, without waiting for the champion pods, so champion seats silently play the scripted
  `reciprocator` baseline. Reproduced on rounds 2 (`3/6`, `llmOrders=1`) and 4 (`4/6`,
  `llmOrders=2`); round 3 (`6/6`, `llmOrders=24`) shows the intended behaviour, so it is a race,
  not a dead code path. Suggested direction for the fixer: gate the lobby close on
  `num_agents` registrations (or on the round loop not starting until every declared seat has
  registered) rather than on "every socket that happens to be connected", and treat a champion seat
  still unregistered at round start as a hard error rather than a silent scripted substitution.
- **D2 (drives check 5).** `gift-refinements-mirror`'s prompt produced replies outside the declared
  job enum twice in one round (`unknown job consume`, then `target is required when job is meet or
  gift > 0`), exhausting the retry and falling back. Not a capacity problem — Bedrock returned 200
  on every call in every log this run — and not a `max_tokens` truncation. It is a prompt/validator
  adherence issue; `consume` is a *field*, not a `job`, and the model conflated them.
