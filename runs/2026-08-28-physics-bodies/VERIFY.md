# VERIFY — physics-bodies   (2026-08-28T15:56:03Z)

Verdict: **all-true** (8/8 TRUE)

Run: `2026-08-28-physics-bodies` · coworld `cow_e51c593d-8b3e-41e9-92eb-04ff70083bbd` v0.1.3
League `league_6fe36e5b-1b03-44f4-864e-8b5408d639ca` · division `div_03ffc06b-ea16-4df0-8c56-989bf1ed5254`
Champions: `physics-bodies-ringcraft:v3` (daveey) / `physics-bodies-toppler:v3` (daveey-1).
Fillers: `physics-bodies-pusher:v3`, `physics-bodies-anchor:v3` (registered 2026-08-28T15:30Z).

Common preamble for every curl below (header **names** only; values are never printed):

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_6fe36e5b-1b03-44f4-864e-8b5408d639ca
D=div_03ffc06b-ea16-4df0-8c56-989bf1ed5254
COW=cow_e51c593d-8b3e-41e9-92eb-04ff70083bbd
```

Every item below was fetched **fresh in this phase-60 pass** (2026-08-28T15:53Z–15:56Z), except
the two documented exceptions: item 7 (reads the committed `release-result.json`) and item 8
(reads the artifact of the `viewer-check.yml` run this pass dispatched, 33187402013).

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}"        # 2026-08-28T15:53:02Z → HTTP 200
jq -r 'if type=="array" then . else .entries end
       | [.[]|select(.status=="completed")]|length'                # → 2
```

Response (top-level type `object`, key `entries`; rows projected to the fields the check uses,
`entrants` = `round_config.entrant_attributions`):

```json
[
  {
    "id": "round_ade551f5-d3c5-439c-86eb-2a25c616ca09",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T15:46:58.286177Z",
    "entrants": [
      {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
       "policy_version_id": "fefcab37-7b64-4412-831f-f553bbbe8de4",
       "league_policy_membership_id": "lpm_fa4b3bd8-f0a3-4f94-8f1c-3115170187f5"},
      {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
       "policy_version_id": "e0191e6a-1e55-4cd8-b33c-8c0bd0fac22a",
       "league_policy_membership_id": "lpm_3f282604-924b-45ee-b28d-4539279e4028"}
    ]
  },
  {
    "id": "round_84212c64-94f8-448d-ad13-f8a79546afde",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T15:31:57.858691Z",
    "entrants": [
      {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
       "policy_version_id": "fefcab37-7b64-4412-831f-f553bbbe8de4",
       "league_policy_membership_id": "lpm_fa4b3bd8-f0a3-4f94-8f1c-3115170187f5"},
      {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
       "policy_version_id": "e0191e6a-1e55-4cd8-b33c-8c0bd0fac22a",
       "league_policy_membership_id": "lpm_3f282604-924b-45ee-b28d-4539279e4028"}
    ]
  },
  {
    "id": "round_b4ed773e-40f4-4f57-a56d-c8f124c1e7fb",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-28T15:31:02.431055Z",
    "entrants": [
      {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
       "policy_version_id": "fefcab37-7b64-4412-831f-f553bbbe8de4",
       "league_policy_membership_id": "lpm_fa4b3bd8-f0a3-4f94-8f1c-3115170187f5"}
    ]
  }
]
```

**Status: TRUE** — rounds **2** (`round_84212c64-94f8-448d-ad13-f8a79546afde`, created
15:31:57Z) and **3** (`round_ade551f5-d3c5-439c-86eb-2a25c616ca09`, created 15:46:58Z) are
`completed`, and both were created **after** the fillers were registered at
2026-08-28T15:30:06Z (`log.md`: `50 filler-policies 200: pusher:v3=aeaa9567-… anchor:v3=e375ac44-…`).

Round 1 does **not** count and is not claimed: `status: "failed"`, error verbatim
`"Temporal RoundWorkflow failed before settling the round."`. It was the auto-trigger that fired
at 15:31:02Z with only one entrant seated and predates the filler registration — the exact
signature `playbooks/observatory-api.md` §6 documents for a trigger issued before any filler
exists. No round is `discarded`.

Poll trail (each line also appended to `runs/2026-08-28-physics-bodies/log.md`):

| UTC | round 2 | round 3 | completed ≥ r2 |
|---|---|---|---|
| 15:34:03Z | pending | — | 0 |
| 15:39:10Z | completed | — | 1 |
| 15:44:55Z | completed | — | 1 |
| 15:49:43Z | completed | pending | 1 |
| 15:52:52Z | completed | completed | 2 |

Elapsed inside the 75-minute bound: 19 minutes.

---

## 2. Both champions ranked; fillers absent/Baseline — TRUE

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}"            # 2026-08-28T15:53:09Z → HTTP 200
jq -r 'type'                                                       # → array  (bare list, not .entries)
jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```

```
1	daveey	physics-bodies-ringcraft:v3	1030.5304984710244	2	2.0
2	daveey-1	physics-bodies-toppler:v3	969.4695015289755	2	0.0
```

Raw body (complete, two rows, nothing elided):

```json
[{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1030.5304984710244,"score_label":"MMR","score_value_type":"integer","rounds_played":2,"episode_wins":2.0,"episodes_played":null,"win_rate":1.0,"policy_label":"physics-bodies-ringcraft:v3","recent_rounds":null},{"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":969.4695015289755,"score_label":"MMR","score_value_type":"integer","rounds_played":2,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"physics-bodies-toppler:v3","recent_rounds":null}]
```

**Status: TRUE** — `daveey` (rank 1, `rounds_played` 2) and `daveey-1` (rank 2, `rounds_played` 2)
are both present, each ≥ 1. The response is exactly two rows: neither filler
(`physics-bodies-pusher:v3`, `physics-bodies-anchor:v3`) appears at all, and no row carries a
`policy_label` starting `Baseline` — fillers **absent**, which the checklist permits. Player ids
match the literal ids in `playbooks/observatory-api.md` (daveey `ply_44ae9048-…`, daveey-1
`ply_bac48eb1-…`), so champion #2's ownership is confirmed on the live leaderboard.

---

## 3. Latest completed round's episode request completed with a replay — TRUE

Latest completed round from item 1 = `round_ade551f5-d3c5-439c-86eb-2a25c616ca09` (round 3).

The flat route the prompt shows is dead; both shapes are recorded rather than inferred:

```bash
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}"      # 2026-08-28T15:53:15Z
```
```json
{"detail":"Method Not Allowed"}
```
```
HTTP 405
```
(the 405 `playbooks/observatory-api.md` §9 documents; the nested route is authoritative)

```bash
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}"                 # → HTTP 200
```
```json
[{"id":"ereq_05afb4b3-f13a-40c7-ae3a-a0bf1e817e4d","status":"completed"}]
```

```bash
EREQ=ereq_05afb4b3-f13a-40c7-ae3a-a0bf1e817e4d
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'           # → HTTP 200
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/fa7ce35f-0b91-4ffe-8f11-6d21b47f84d1.replay",
  "participants": [
    {
      "position": 0,
      "kind": "policy",
      "policy_version_id": "fefcab37-7b64-4412-831f-f553bbbe8de4",
      "policy_id": "84c4c91d-5a8a-47fe-9479-083e7435274a",
      "policy_name": "physics-bodies-ringcraft",
      "version": 3,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": false,
      "is_seed": false
    },
    {
      "position": 1,
      "kind": "policy",
      "policy_version_id": "e0191e6a-1e55-4cd8-b33c-8c0bd0fac22a",
      "policy_id": "928d7882-11b5-406e-b7c8-413fe16883ef",
      "policy_name": "physics-bodies-toppler",
      "version": 3,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
      "player_name": "daveey-1",
      "is_filler": false,
      "is_seed": false
    }
  ],
  "participant_scores": [
    {"position": 0, "score": 2.25},
    {"position": 1, "score": -2.25}
  ]
}
```

**Status: TRUE** — `status == "completed"`; `replay_url` is non-null
(`…/replays/fa7ce35f-0b91-4ffe-8f11-6d21b47f84d1.replay`); `participants` names **`daveey`**
(seat 0, `physics-bodies-ringcraft` v3) and **`daveey-1`** (seat 1, `physics-bodies-toppler` v3),
both `is_filler: false`. No `Baseline (N)` seat is present because the round seated exactly the
two champions — consistent with `entrant_attributions` in item 1. `participant_scores`
+2.25 / −2.25 is a decided episode, not a null result.

For cross-reference, round 2's episode request (also fetched fresh this pass, 15:39Z) was
`ereq_1c1a2453-cf7a-416a-be74-e42e47f020cf`, `status: "completed"`, replay
`…/replays/9bf45961-0030-4666-bff4-8b5012f22641.replay`, same two champion participants, scores
+2.5 / −2.5.

---

## 4. Replay bytes are valid and show the game — TRUE

**Why the command shape differs from the prompt (documented, not improvised).** This coworld's
replay is the starter's **binary** container, magic `COWLDPBD`, not a JSON document, so
`jq -e . /tmp/ep.replay` cannot apply to the raw bytes. `design.md` §Replay format and the repo's
own `tools/replay_summary.py` docstring define the forensics path: download the bytes, decode
them with the repo's stdlib-only summariser, and require **its** output to parse under a strict
UTF-8 parser. That substitution is recorded here rather than silently made.

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/fa7ce35f-0b91-4ffe-8f11-6d21b47f84d1.replay" \
     -o /tmp/ep.replay
```
```
HTTP 200 bytes=88731
```
```bash
python3 -c "d=open('/tmp/ep.replay','rb').read(); print('magic=',d[:8]); print('len=',len(d))"
```
```
magic= b'COWLDPBD'
len= 88731
```
```bash
jq -e . /tmp/ep.replay   # → non-zero: raw container is NOT JSON (binary COWLDPBD)
```

Strict parse of the summariser's output (clone at `/workspace/cogame-physics-bodies`, synced to
`origin/main` = `3b913af fix(lobby): a slot that is not next is HELD, not thrown away`):

```bash
python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
python3 -c 'import json; json.loads(open("/tmp/ep.json","rb").read().decode("utf-8")); print("strict UTF-8 JSON: ok")'
```
```
strict UTF-8 JSON: ok
```
```bash
jq -r '.protocol, .gameName, .gameVersion, .num_agents, .tickCount, .results.reason, .results.endRule, .fallbacks' /tmp/ep.json
```
```
physics-bodies/v1
physics-bodies
1
2
2062
complete
full_time
0
```

`protocol` = `physics-bodies/v1`, which matches the manifest (coworld v0.1.3, manifest_sha
`sha256:3c7e9da8…`, the same sha the static viewer route resolves in item 6).

```bash
jq -c '.records' /tmp/ep.json
```
```json
{"hashes":2062,"inputs":2556,"chats":108,"joins":2}
```
```bash
jq -c '.registers' /tmp/ep.json
```
```json
[{"seat":1,"alias":"BUG-1","body":0,"policy":"physics-bodies-toppler","kind":"llm","baseline":"pusher"},
 {"seat":0,"alias":"BUG-2","body":1,"policy":"physics-bodies-ringcraft","kind":"llm","baseline":"pusher"}]
```
Both champion seats registered `kind: "llm"` — neither was seated as a scripted baseline.

```bash
jq -c '.results' /tmp/ep.json
```
```json
{"names":["daveey","daveey-1"],"aliases":["BUG-2","BUG-1"],"bodies":[1,0],"policyKinds":["llm","llm"],"scores":[2.25,-2.25],"win":[true,false],"roundsWon":[2,0],"roundResults":[{"round":1,"winner":1,"reason":"decision","ticks":396,"knockdowns":[1,1]},{"round":2,"winner":1,"reason":"ring_out","ticks":196,"knockdowns":[1,1]},{"round":3,"winner":-1,"reason":"draw","ticks":396,"knockdowns":[0,0]},{"round":4,"winner":-1,"reason":"draw","ticks":396,"knockdowns":[0,0]},{"round":5,"winner":-1,"reason":"draw","ticks":396,"knockdowns":[0,0]}],"ringOuts":[1,0],"knockouts":[0,0],"knockdownsSuffered":[2,2],"contacts":[46,52],"shoveImpulse":[0.22,0.2],"meanEffortPct":[66,78],"llmTurns":[50,50],"fallbackTurns":[0,0],"rounds":5,"finalTick":2062,"reason":"complete","endRule":"full_time","seed":1446162581}
```

`results.reason == "complete"` with `endRule == "full_time"` — the **normal good ending** in
`design.md` §End conditions (`maxRounds` played with no clinch). The `deadline`/`wall_clock`
exception the design note declares acceptable was **not needed**: no `stops` and no
`budgetGuards` records were written at all:

```bash
jq -c '{stops:.stops, budgetGuards:.budgetGuards}' /tmp/ep.json
```
```json
{"stops":[],"budgetGuards":[]}
```

Decisions vs fallbacks, per champion seat:

```bash
jq -r '[.intents[]|{seat,source}] | group_by([.seat,.source])[] | "seat=\(.[0].seat) source=\(.[0].source) n=\(length)"' /tmp/ep.json
jq -c '{llmTurns:.results.llmTurns, fallbackTurns:.results.fallbackTurns, fallbacks:.fallbacks, causes:.fallbackCauses}' /tmp/ep.json
```
```
seat=0 source=llm n=50
seat=1 source=llm n=50
```
```json
{"llmTurns":[50,50],"fallbackTurns":[0,0],"fallbacks":0,"causes":{}}
```

| seat | alias | player | policy | decisions (`source=="llm"`) | fallbacks |
|---|---|---|---|---|---|
| 0 | BUG-2 | daveey | physics-bodies-ringcraft:v3 | 50 | 0 |
| 1 | BUG-1 | daveey-1 | physics-bodies-toppler:v3 | 50 | 0 |

**100 / 100 decisions came from the LLM; zero fallbacks** — not "a small minority", none.
`fallbackCauses` is the empty object, so the summariser saw no `k:"fallback"` chat record.

The decisions have non-trivial, game-specific content — an LLM reasoning about ring position,
tilt and shove, i.e. the thing this game is about:

```bash
jq -c '.intents[0:2][]' /tmp/ep.json
```
```json
{"turn":4,"seat":0,"alias":"BUG-2","body":1,"source":"llm","latency_ms":4562,"stance":"circle","aim":"foe","aggression":4,"posture_bias":"even","lead_ticks":6,"circle_dir":-1,"note":"Both bugs equidistant from rim (1.14m each), not in contact. Foe is right (bearing 348.75°). Closing at 0.53 m/s. I'm 1.86m from centre. Circle to get rim behin","say":"Foe high-posture at 348, both on rim-edgecircl"}
{"turn":4,"seat":1,"alias":"BUG-1","body":0,"source":"llm","latency_ms":4562,"stance":"charge","aim":"foe","aggression":7,"posture_bias":"even","lead_ticks":8,"circle_dir":1,"note":"Both bugs HIGH and far apart (3.73m). Other bug not unstable yet. Charge to close distance and set up contact before it does.","say":"Closing distance, preparing engagement"}
```

**Status: TRUE** — bytes fetched (88,731 B, magic `COWLDPBD`); the repo summariser's output parses
under a strict UTF-8 parser; `protocol` matches the manifest; `results.reason == "complete"`
(`endRule` `full_time`, the normal case, no design exception invoked); 100 LLM decisions with
substantive content and **0** fallbacks across both champion seats.

---

## 5. Hosted game log is clean — TRUE

```bash
curl -sS "$BASE/episode-requests/ereq_05afb4b3-f13a-40c7-ae3a-a0bf1e817e4d/artifacts/logs" \
     "${AUTH[@]}" "${ELEV[@]}" -o /tmp/F5.raw          # 2026-08-28T15:53:44Z
```
```
HTTP 200 bytes=207683
```

Grepped **twice** — once naively on the wire bytes, once on the text decoded out of the python
`b'…'` byte-string reprs (`playbooks/observatory-api.md` §10: line-based greps undercount
otherwise). Both agree.

```bash
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/F5.raw || echo CLEAN
```
```
CLEAN
```
```bash
python3 loggrep.py /tmp/F5.raw /tmp/F5.txt   # ast.literal_eval per repr, then grep the decoded text
```
```
decoded_lines=447
CLEAN
```

All four containers were present in the artifact (so this is not a clean grep over an empty body):

```bash
grep -o '===== container: .* =====' /tmp/F5.txt
```
```
===== container: coworld-init-config =====
===== container: bedrock-sidecar =====
===== container: game =====
===== container: worker =====
```

The `game` container's own account of the episode:

```
physics-bodies llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
seat 1 registered: kind=llm baseline=pusher
seat 0 registered: kind=llm baseline=pusher
physics-bodies: episode over — complete/full_time rounds 0-2 at tick 2062
```

**Status: TRUE** — zero hits for `falling back`, `LLM provider is unavailable`,
`cut off at max_tokens` or `rejected` in 447 decoded lines across all four containers. No
platform-wide-throttle exception was invoked and none was needed: nothing was throttled, so no
cross-check against another LLM coworld's log was required. The log's own end line
(`complete/full_time … tick 2062`) agrees with `results` in item 4, and `maxOutputTokens` needed
no raise.

Round 2's log was fetched the same way earlier this pass (15:39Z, 105,245 B, 246 decoded lines)
and was also `CLEAN` — both completed rounds are clean, not just the one under test.

---

## 6. The public page uses the static replay path — TRUE

**Source used: the API the page reads** (the third of the three sources, `POST
/coworlds/replays/session`), after recording that the first two are uninformative here. All three
were attempted this pass; none is asserted from memory.

*(a) Raw-HTML iframe grep — finds nothing, recorded as unknown, not as a failure.*
```bash
curl -sS "https://softmax.com/physics-bodies" -o /tmp/F6page.html    # 2026-08-28T15:53:54Z
grep -o '<iframe[^>]*src="[^"]*"' /tmp/F6page.html
```
```
HTTP 200 bytes=737737
(no output)
```
Expected: `playbooks/observatory-api.md` §Featured match records the page as client-rendered for
the iframe since the lighthouse run (2026-08-22) — the grep finds nothing for **any** coworld.

*(b) `/coworlds` detail — `featured_match` is null platform-wide, also not evidence.*
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -c '.entries[]|select(.name=="physics-bodies" and .canonical==true)|{id,name,canonical,replay_viewer,featured_match}'
```
```json
{"id":"cow_e51c593d-8b3e-41e9-92eb-04ff70083bbd","name":"physics-bodies","canonical":true,"replay_viewer":null,"featured_match":null}
```
`canonical: true` for `cow_e51c593d-…` (the other two `physics-bodies` rows,
`cow_395b6bf8-…` and `cow_951fe378-…`, are `canonical: false` — the failed 0.1.1/0.1.2 uploads).
`featured_match: null` is the documented platform-wide value.

*(c) The featured match, server-rendered into the page's SSR payload at `state.playlist[0]`.*
```bash
grep -o 'playlist\\":\[{[^]]\{0,900\}' /tmp/F6page.html | head -1
```
```
playlist\":[{\"episodeId\":\"bb4f3e25-f90e-4a48-9deb-dbf929326a56\",\"coworldId\":\"cow_e51c593d-8b3e-41e9-92eb-04ff70083bbd\",\"coworldName\":\"physics-bodies\",\"coworldVersion\":\"0.1.3\",\"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/fa7ce35f-0b91-4ffe-8f11-6d21b47f84d1.replay\",\"finishedAt\":\"2026-08-28T15:52:32.599880Z\",\"roundNumber\":3,\"episodeNumber\":1,\"code\":\"physics-bodies.r3.e1\",\"matchup\":{\"divisionId\":\"div_03ffc06b-ea16-4df0-8c56-989bf1ed5254\",\"divisionName\":\"Competition\",\"first\":{\"rank\":1,\"player_id\":\"ply_44ae9048-3242-4654-881f-6d9d43347fa3\",\"player_name\":\"daveey\",\"score\":1030.5304984710244,\"score_label\":\"MMR\",\"score_value_type\":\"integer\",\"rounds_played\":2,\"episode_wins\":2,\"episodes_played\":null,\"win_rate\":1,\"policy_label\":\"physics-bodies-ringcraft:v3\",\"recent_rounds\":null},\"second\":{\"rank\":2,\"player_id\":\"pl
```
A featured match **is** present: `physics-bodies.r3.e1`, coworld version `0.1.3`, replay
`fa7ce35f-…` — the very episode verified in items 3–5 — with a two-sided `matchup`
(`daveey` rank 1 vs `daveey-1` rank 2). Two ranked players, so the "absence = fewer than two
ranked players" failure mode does not apply.

*(d) The iframe `src` — the call the page's own JS makes.*
```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" \
  -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_e51c593d-8b3e-41e9-92eb-04ff70083bbd",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/fa7ce35f-0b91-4ffe-8f11-6d21b47f84d1.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e51c593d-8b3e-41e9-92eb-04ff70083bbd/sha256%3A3c7e9da8432c2342f20945677bd739da973dfbfefedf82d79af2746920c0127c/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Ffa7ce35f-0b91-4ffe-8f11-6d21b47f84d1.replay",
  "ready": true
}
```
```
HTTP 200
```

**Status: TRUE** — the src is the **static** route
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html`, with
`<cow_id>` = `cow_e51c593d-8b3e-41e9-92eb-04ff70083bbd` and `<sha>` = the URL-encoded coworld
**manifest_hash** `sha256:3c7e9da8432c2342f20945677bd739da973dfbfefedf82d79af2746920c0127c`,
matching `STATE.coworld.manifest_sha` exactly. `ready: true` and the path ends `/index.html` —
static delivery. There is **no** `/client/replay` pod URL anywhere in the response. The replay is
carried as the URL-encoded **fragment** `#replay=…` rather than the `?replay=` query param; this
is the form `playbooks/observatory-api.md` §Featured match records the session endpoint as
returning since 2026-08-28, and it is the same static route. That exact string, fragment and all,
is the URL rendered in item 8.

---

## 7. Certification declared the static bundle — TRUE

**Source read: the committed `runs/2026-08-28-physics-bodies/release-result.json`** — the copy
phase 40 downloaded and committed. No re-download was needed and no `/tmp` copy was consulted.

```bash
git log --oneline -1 -- runs/2026-08-28-physics-bodies/release-result.json
```
```
18d29a9 40 physics-bodies: v0.1.3 canonical+certified cow_e51c593d; phase -> 50
```
```bash
jq -r '.certify.replay_liveness' runs/2026-08-28-physics-bodies/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```
```bash
jq -c '{ok:.certify.ok, canonical:.canonical}' runs/2026-08-28-physics-bodies/release-result.json
```
```json
{"ok":true,"canonical":true}
```

**Status: TRUE** — the string contains `Replay liveness: skipped (static replay bundle declared`
verbatim, read from the **committed** artifact of this run's release dispatch (run id
`33184563689`, the fallback which was therefore not exercised). `certify.ok: true` and
`canonical: true` corroborate the same release.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — TRUE

*(a) Dispatch.* The `url` input is the item-6 `viewer_url` verbatim, fragment included.

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e51c593d-8b3e-41e9-92eb-04ff70083bbd/sha256%3A3c7e9da8432c2342f20945677bd739da973dfbfefedf82d79af2746920c0127c/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Ffa7ce35f-0b91-4ffe-8f11-6d21b47f84d1.replay'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
# dispatched 2026-08-28T15:54:19Z
sleep 12
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:4][]|"\(.databaseId)\t\(.createdAt)\t\(.status)"'
```
```
33187402013	2026-08-28T15:54:21Z	in_progress
33184965298	2026-08-28T15:24:14Z	completed
33176460797	2026-08-28T13:40:19Z	completed
33175355596	2026-08-28T13:25:59Z	completed
```
Run **33187402013** was created at 15:54:21Z, two seconds after the dispatch at 15:54:19Z — it is
this pass's run, identified by `createdAt` sort, not by taking "the latest" blind. (The 15:24Z run
is an earlier phase's and is not used.)

```bash
gh run watch 33187402013 -R Metta-AI/coworld-builder --exit-status
```
```
JOBS
✓ viewer-check in 34s (ID 98903860775)
  ✓ Install Playwright (pinned 1.55.0)
  ✓ Load the viewer
  ✓ Summary
  ✓ Upload the evidence
  ✓ Fail if the viewer did not load
```
Green — the `Fail if the viewer did not load` gate passed rather than being tolerated.

```bash
gh run download 33187402013 -R Metta-AI/coworld-builder -n viewer-check \
   -D runs/2026-08-28-physics-bodies/viewer-check
ls -l runs/2026-08-28-physics-bodies/viewer-check/
```
```
-rw-r--r-- 1 root root      0 smoke-stderr.txt
-rw-r--r-- 1 root root    656 smoke-stdout.txt
-rw-r--r-- 1 root root   1452 viewer-smoke.json
-rw-r--r-- 1 root root 749545 viewer-smoke.png
```
Committed with this file (`runs/2026-08-28-physics-bodies/viewer-check/`); `smoke-stderr.txt` is
zero bytes.

*(b) The readouts, verbatim.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-28-physics-bodies/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":2643,"clock":":05 STARTING IN ROUND 1 OF 5 · RING 3.00 M","scorebug":"0.000 SEAT 1 ROUNDS 0 0 KNOCKDOWNS · 0 RING-OUTS :05 STARTING IN ROUND 1 OF 5 · RING 3.00 M 0.000 SEAT 0 ROUNDS 0 0 KNOCKDOWNS · 0 RING-OUTS","feed_lines":0}
```
```bash
jq -c '.signals' runs/2026-08-28-physics-bodies/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```
```bash
jq -r '.failure // "no failure"' runs/2026-08-28-physics-bodies/viewer-check/viewer-smoke.json
```
```
no failure
```
```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-28-physics-bodies/viewer-check/viewer-smoke.json
```

| scrub position | clock readout |
|---|---|
| 0 % | `:05 STARTING IN ROUND 1 OF 5 · RING 3.00 M` |
| 50 % | `0:04 ROUND CLOCK ROUND 3 OF 5 · RING 2.39 M` |
| 100 % | `0:00 ROUND CLOCK ROUND 5 OF 5 · RING 2.01 M` |

The three readouts **all differ**, and they differ in the right direction: round 1 → 3 → 5 of 5
and ring radius 3.00 → 2.39 → 2.01 m. The `#scrub` element exists (no `"(no #scrub…)"` sentinel),
so motion is established from the scrubber, not inferred. `data_replay_loaded: "true"` is the
signal that carried `loaded`; `bridge_ready` is false and the `bridge` array empty — this shell
reports readiness through the `data-replay-loaded` attribute rather than the `coworld-replay`
bridge, which the check treats as equivalent, and `data_replay_error` is null.

Also from the artifact (`smoke-stdout.txt`, verbatim line 3):
```
canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
```
`canvas_text.total: 0` is structural, not a blank canvas: the phase-30 r1 review recorded it as
finding **N1** — this viewer bakes its text through pixie rather than `fillText`, so the
instrument's text hook sees nothing while the pixels carry the labels. The screenshot below shows
that text plainly.

*(c) The replay JSON the viewer was asked to draw* — ordered excerpts from `/tmp/ep.json`
(item 4's summary of `/tmp/ep.replay`; the binary container has no `.events[]`, so `.intents[]`
and `.rounds[]` are the equivalent records):

```bash
jq -r '.intents[0:8][]|[.turn,.seat,.alias,.source,.stance,.aggression,(.say//"")]|@tsv' /tmp/ep.json   # EARLY
```
```
4	0	BUG-2	llm	circle	4	Foe high-posture at 348, both on rim-edgecircl
4	1	BUG-1	llm	charge	7	Closing distance, preparing engagement
5	0	BUG-2	llm	circle	4	Holding ground, let shrink work
5	1	BUG-1	llm	charge	9	High spin = unstable. Hit hard.
6	0	BUG-2	llm	retreat	8	RETREAT TO CENTRE - EMERGENCY
6	1	BUG-1	llm	charge	9	Pushing you rimward!
7	0	BUG-2	llm	retreat	8	Retreating to centre - rim danger critical
7	1	BUG-1	llm	retreat	9	Backing to safety!
```
```bash
jq -r '.intents[46:54][]|[.turn,.seat,.alias,.source,.stance,.aggression,(.say//"")]|@tsv' /tmp/ep.json  # MIDDLE
```
```
29	0	BUG-2	llm	retreat	8	Backing to centrerim is too close!
29	1	BUG-1	llm	retreat	9	Down 2-0, must survive and reset. Centre is safe
30	0	BUG-2	llm	retreat	8	Backing to safety - rim is killing me!
30	1	BUG-1	llm	retreat	9	0-2 down. Must survive, then hunt knockdowns.
31	0	BUG-2	llm	retreat	8	Backing to centre - rim is death at 0.30m
31	1	BUG-1	llm	retreat	9	0-2 down: get safe, rebuild, hunt knockdowns
32	0	BUG-2	llm	retreat	8	Emergency retreat - both at rim edge
32	1	BUG-1	llm	retreat	9	Back to safety - down 0-2, can't afford ring out
```
```bash
jq -r '.intents[-8:][]|[.turn,.seat,.alias,.source,.stance,.aggression,(.say//"")]|@tsv' /tmp/ep.json    # LATE
```
```
54	0	BUG-2	llm	retreat	8	Emergency retreat - both bugs critical rim dista
54	1	BUG-1	llm	retreat	9	Backing to centre - rim guard critical at edge!
55	0	BUG-2	llm	retreat	8	Both on the edge - one shove decides it
55	1	BUG-1	llm	retreat	9	Backing to centrerim too close, must recover po
56	0	BUG-2	llm	retreat	8	Both at rim - backing to centre!
56	1	BUG-1	llm	retreat	9	Backing to centre - decision win incoming
57	0	BUG-2	llm	retreat	8	Retreat to centre - both on edge
57	1	BUG-1	llm	retreat	9	Back to centre, match point coming
```
```bash
jq -c '.rounds[]' /tmp/ep.json
```
```json
{"k":"round","round":1,"winner":1,"reason":"decision","ticks":396,"knockdowns":[1,1]}
{"k":"round","round":2,"winner":1,"reason":"ring_out","ticks":196,"knockdowns":[1,1]}
{"k":"round","round":3,"winner":-1,"reason":"draw","ticks":396,"knockdowns":[0,0]}
{"k":"round","round":4,"winner":-1,"reason":"draw","ticks":396,"knockdowns":[0,0]}
{"k":"round","round":5,"winner":-1,"reason":"draw","ticks":396,"knockdowns":[0,0]}
```

### Spectator judgment

`viewer-check/viewer-smoke.png` (1280×800, the frame CI captured after the scrub sweep) is a full,
legible spectator picture — not a loading screen, not a blank canvas, not a single frozen frame.
Reading it top to bottom: a **scorebug strip** across the head, `DAVEEY-1  0 ROUNDS` on the left
with a boxed `-2.250` and `2 KNOCKDOWNS · 0 RING-OUTS` beneath it, `DAVEEY  ROUNDS 2` on the right
with `+2.250` and `2 KNOCKDOWNS · 1 RING-OUTS`, and between them a centred **clock** reading
`0:00 / ROUND CLOCK / ROUND 5 OF 5 · RING 2.01 M` — every one of those numbers is the replay's own
`results` from item 4 (`scores [2.25,-2.25]`, `roundsWon [2,0]`, `knockdownsSuffered [2,2]`,
`ringOuts [1,0]`), so picture and record agree exactly, including which side won. Below the strip
are the two seats' latest **say banners**, tinted amber for BUG-1 and teal for BUG-2:
`BUG-1: Back to centre, match point coming` and `BUG-2: Retreat to centre - both on edge`. Those
are, verbatim, the final two `say` strings in the LATE excerpt above (turn 57, seats 1 and 0) —
the strongest available proof that what was rendered is this replay and not a canned demo. The
**arena** is a stone-flagged floor circle lit by wall torches, with a bright dotted white rim
drawn well inside the floor edge (the ring has shrunk, consistent with `RING 2.01 M` against the
3.00 m start) and two bug bodies on it: an amber cluster high-right and a teal cluster low-left,
each drawn as a main disc with satellite feet, a dark "over the rim" foot marker and small red
contact sparks. A bottom-left **legend** spells the read-out rules in plain words —
`ARC OVER A BUG = TILT. FULL TILT AND IT FALLS.` / `DARK FOOT = OVER THE RIM: NO FLOOR, NO PUSH.` /
`BRIGHT RIM = THE LIVE RING, AND IT IS SHRINKING.` — so a first-time spectator can decode the
picture without documentation. Down the right edge is an **event feed** of amber chips,
`ROUND 4 - RING 3.00 M AND CLOSING` / `DRAWN ROUND 4` / `ROUND 5 - RING 3.00 M AND CLOSING` /
`DRAWN ROUND 5`, which matches the `rounds` records' `draw` verdicts for rounds 4 and 5. The
**transport strip** along the foot carries restart, step-back, play, `+5s`, step-forward, loop and
fast-forward buttons, a `spoilers` toggle, an **endcard** readout `BUG2 WINS  1921 / 1925`, and
speed buttons `1× 2× 3× 4× 8× 16×` with `1×` selected; under it a **scrubber** with per-round tick
marks and, below that, a labelled `LIVES LEAD` **momentum graph** whose amber band gives way to a
teal band at roughly a quarter through — the swing after BUG-2 took rounds 1 and 2.

So: it is legible, and it shows the game. The game is two LLM-driven bugs shoving each other
toward a shrinking rim, and the picture shows exactly that — bodies, rim, tilt, contacts, who is
winning and why, with an endcard naming the winner.

**Does it look like the starter's chrome?** Yes — this is the paintbot/raid/hive lineage, not a
rewrite that merely shares ids (the cogame-gridlock failure mode). All four lineage marks are
present and identifiable in the screenshot: the two-sided **scorebug** with centred clock; the
foot **transport strip** with the same button vocabulary and the same `1×…16×` speed row; the
**scrubber with a momentum graph** underneath it (`LIVES LEAD`); and an **endcard** readout
(`BUG2 WINS`) in the transport strip. The reskin is thematic (torch-lit stone arena, bug bodies)
rather than structural.

**Item 8 is TRUE** — `loaded: true` **and** the three clock readouts differ.

Two **legibility observations** for the coordinator, neither of which bears on any check's
verdict, both reported rather than fixed:
1. In the captured frame a round-intro title card reading `ROUND 1/5 - RING 3.00 M` is still
   overlaid at top centre while the clock chip beneath it reads `ROUND 5 OF 5 · RING 2.01 M`. The
   two disagree in the same frame. The frame was captured after the scrub sweep jumped 0 % → 50 %
   → 100 %, so the plausible reading is an intro card that a scrub jump leaves up; I did not
   verify the cause and do not claim it.
2. `feed_lines: 0` in `viewer-smoke.json` while the screenshot plainly shows a four-chip event
   feed on the right and two say banners. The instrument's feed selector does not match this
   shell's feed element, so the count understates what is drawn — an instrumentation gap, not a
   missing feed.
3. The transport endcard reads `1921 / 1925` frames while the replay records `tickCount: 2062`
   (`records.hashes: 2062`, `results.finalTick: 2062`). The two counters do not line up; I did not
   determine which unit the transport counts.

---

## Summary table

| # | Check | Verdict | Key evidence |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers | **TRUE** | rounds 2 & 3 `completed`, created 15:31:57Z / 15:46:58Z, both after fillers at 15:30:06Z; round 1 `failed` (pre-filler auto-trigger), not counted |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** | `daveey` r1 / `daveey-1` r2, `rounds_played` 2 each; exactly two rows, no filler |
| 3 | Latest round's episode request completed + replay | **TRUE** | `ereq_05afb4b3-…` `completed`, `replay_url` `…/fa7ce35f-….replay`, participants daveey + daveey-1 |
| 4 | Replay bytes valid and show the game | **TRUE** | 88,731 B `COWLDPBD`; summariser output strict-UTF-8-parses; `protocol physics-bodies/v1`; `reason complete` / `endRule full_time`; 50+50 LLM decisions, **0** fallbacks |
| 5 | Hosted game log clean | **TRUE** | 207,683 B, 4 containers, 447 decoded lines, `CLEAN` on raw **and** decoded grep |
| 6 | Public page uses the static replay path | **TRUE** | `POST /coworlds/replays/session` → `ready: true`, `…/replays/static/<cow_id>/sha256%3A3c7e9da8…/index.html?v=2#replay=…`; featured match `physics-bodies.r3.e1` in SSR `playlist[0]`; no `/client/replay` |
| 7 | Certification declared the static bundle | **TRUE** | committed `release-result.json` → `Replay liveness: skipped (static replay bundle declared; …)` |
| 8 | Spectator judgment (viewer executed) | **TRUE** | run 33187402013, `loaded: true` in 2643 ms, three differing clock readouts, screenshot shows scorebug/arena/feed/transport/momentum graph/endcard matching the replay's own results and final say lines |

**Verdict: all-true.** No item was marked true by inference; no item is `NOT FETCHED`; no
documented exception was invoked (the `deadline` allowance in `design.md` §End conditions and the
platform-wide-throttle allowance in check 5 were both available and both unnecessary).
