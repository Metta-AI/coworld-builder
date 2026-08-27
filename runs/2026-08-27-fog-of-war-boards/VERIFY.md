# VERIFY — fog-of-war-boards   (2026-08-27T03:23:00Z)

Verdict: **all-true** (8/8)

Run: `2026-08-27-fog-of-war-boards` · coworld `cow_5f8e4d33-49d7-4b19-8092-cc69d201344c` v0.1.0
League `league_26ccabcd-af33-4f17-b9d7-f44626a7c625` · division `div_8c9c080c-31db-4672-8146-d73cd81ebc42`

Common headers on every Observatory call below (values never printed):
`Authorization: Bearer $SOFTMAX_TOKEN`, `User-Agent: coworld-builder/1.0`; reads of
`artifacts/logs` and `filler-policies` additionally send `X-Use-Elevated-Privileges: true`.

```bash
BASE=https://softmax.com/api/observatory/v2
L=league_26ccabcd-af33-4f17-b9d7-f44626a7c625
D=div_8c9c080c-31db-4672-8146-d73cd81ebc42
COW=cow_5f8e4d33-49d7-4b19-8092-cc69d201344c
```

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | **TRUE** |
| 2 | Both champions ranked, fillers absent | **TRUE** |
| 3 | Latest round's episode request completed with replay | **TRUE** |
| 4 | Replay bytes valid and show the game | **TRUE** |
| 5 | Hosted game log clean | **TRUE** |
| 6 | Public page uses the static replay path | **TRUE** |
| 7 | Certification declared the static bundle | **TRUE** |
| 8 | Viewer executed and judged | **TRUE** |

---

## 1. ≥2 completed rounds after the fillers were set

Fetched 2026-08-27T03:19:05Z / 03:19:40Z.

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}"
```

`jq type` → `"object"` (this endpoint wraps in `{entries:…}` on this deployment; `/leagues`
returns a bare array — both shapes handled).

```json
{
  "id": "round_78423234-9096-43d2-8d59-d8334707acc5",
  "round_number": 3,
  "status": "completed",
  "error": null,
  "created_at": "2026-08-27T03:14:23.957419Z",
  "completed_at": "2026-08-27T03:15:32.416529Z"
}
{
  "id": "round_f626ca3a-309c-490a-9d89-8cafd5f30e4f",
  "round_number": 2,
  "status": "completed",
  "error": null,
  "created_at": "2026-08-27T02:59:22.895259Z",
  "completed_at": "2026-08-27T03:01:15.113398Z"
}
{
  "id": "round_160a9c92-bff3-4855-82c7-352cb5b53a52",
  "round_number": 1,
  "status": "failed",
  "error": "Temporal RoundWorkflow failed before settling the round.",
  "created_at": "2026-08-27T02:58:00.994156Z",
  "completed_at": "2026-08-27T02:58:01.235197Z"
}
```

```bash
… | jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
2
```

**Round 1's `error` verbatim:** `Temporal RoundWorkflow failed before settling the round.`
It does not count and it is understood: it was auto-triggered during champion placement, before
any filler existed (`playbooks/observatory-api.md` §6 — "A `trigger-round` issued before any
filler exists fails instantly with `Temporal RoundWorkflow failed before settling the round`").

The "after the fillers were set" clause is proved from the API, not only from `log.md`. Each
round's `round_config.entrant_attributions` shows the seating:

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end
          | .[]|{round_number,status,attributions:(.round_config.entrant_attributions//null)}'
```
```json
{"round_number": 3, "status": "completed", "attributions": [
  {"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player",
   "policy_version_id":"c28d4d78-56ba-4d34-8e28-14235003abf4",
   "league_policy_membership_id":"lpm_cf5ae64c-2009-49ef-934f-72b72578b94d"},
  {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","subject_type":"player",
   "policy_version_id":"208c6f1d-5280-407f-95b6-0c235da1d1af",
   "league_policy_membership_id":"lpm_c849aef2-39e8-40a8-946f-be735894f79f"}]}
{"round_number": 2, "status": "completed", "attributions": [
  {"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3", …
   "policy_version_id":"c28d4d78-56ba-4d34-8e28-14235003abf4", …},
  {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", …
   "policy_version_id":"208c6f1d-5280-407f-95b6-0c235da1d1af", …}]}
{"round_number": 1, "status": "failed", "attributions": [
  {"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player",
   "policy_version_id":"c28d4d78-56ba-4d34-8e28-14235003abf4",
   "league_policy_membership_id":"lpm_cf5ae64c-2009-49ef-934f-72b72578b94d"}]}
```

Round 1 carries **one** entrant and no filler; rounds 2 and 3 each carry **both** champions.
And the filler registration is live-confirmed:

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"
```
```json
{"filler_policy_versions": [
  {"policy_version_id":"2a72f9fd-d46b-40dc-b48a-48f4f2362fba","policy_id":"92994aa1-3ff1-4ee6-b419-a2ca26854082",
   "policy_name":"fog-of-war-boards-probe","version":1,
   "player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},
  {"policy_version_id":"c403da22-b419-46d8-b613-52835baef133","policy_id":"cdc81e01-83ee-495c-a034-e02f65b3d199",
   "policy_name":"fog-of-war-boards-sweep","version":1,
   "player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```

`log.md` records the registration in the phase-50 batch stamped `2026-08-27T03:00:31Z`
("50 fillers registered 200: probe=2a72f9fd… sweep=c403da22…"), which is a batch write stamp,
not the event time; the round record above pins the ordering independently — round 1 failed at
`02:58:01` with no filler seated, and the next round created after fillers were set is round 2
at `02:59:22`.

**Status: TRUE** — 2 completed rounds, numbers **2** and **3** (completed
`2026-08-27T03:01:15Z` and `2026-08-27T03:15:32Z`), both after fillers were set. Round 1
(`failed`) excluded, its error quoted above.

---

## 2. Both champions ranked; fillers absent or Baseline

Fetched 2026-08-27T03:19:40Z. (An earlier fetch at 03:02Z, when only round 2 had settled,
returned the same two rows with `rounds_played: 1`; the endpoint's earlier `null` in phase 50
was the no-completed-round state.)

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq .
```
```json
[
  {"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
   "score":1001.4695015289755,"score_label":"MMR","score_value_type":"integer",
   "rounds_played":2,"episode_wins":1.0,"episodes_played":null,"win_rate":0.5,
   "policy_label":"fog-of-war-boards-cartographer:v1","recent_rounds":null},
  {"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
   "score":998.5304984710245,"score_label":"MMR","score_value_type":"integer",
   "rounds_played":2,"episode_wins":1.0,"episodes_played":null,"win_rate":0.5,
   "policy_label":"fog-of-war-boards-prober:v1","recent_rounds":null}
]
```

```
rank  player_name  policy_label                          score               rounds_played  episode_wins
1     daveey       fog-of-war-boards-cartographer:v1     1001.4695015289755  2              1.0
2     daveey-1     fog-of-war-boards-prober:v1           998.5304984710245   2              1.0
```

**Status: TRUE** — `daveey` and `daveey-1` both present, each `rounds_played = 2 ≥ 1`; the two
fillers (`fog-of-war-boards-probe:v1`, `fog-of-war-boards-sweep:v1`) are **absent** from the
board, as required (they were never needed — both seats went to champions in rounds 2 and 3).
Each champion has one episode win, one each way (round 2 to `daveey-1`, round 3 to `daveey`).

---

## 3. Latest completed round's episode request completed with a replay

Fetched 2026-08-27T03:19:50Z. Latest completed round = **round 3**
(`round_78423234-9096-43d2-8d59-d8334707acc5`).

Note on the route: the flat `GET $BASE/episode-requests?round_id=…` that `prompts/60-verify.md`
prints is the historical shape; per `playbooks/observatory-api.md` §9 the flat GET route now
405s, so the **nested** route was used.

```bash
curl -sS "$BASE/rounds/round_78423234-9096-43d2-8d59-d8334707acc5/episode-requests" "${AUTH[@]}"
```
```json
{
  "entries": [
    {
      "id": "ereq_999e93c3-63af-4db3-becd-99b4f32e938e",
      "status": "completed",
      "coworld_id": "cow_5f8e4d33-49d7-4b19-8092-cc69d201344c",
      "round_id": "round_78423234-9096-43d2-8d59-d8334707acc5",
      "replay_url": "https://softmax-public.s3.amazonaws.com/replays/c56682ec-f4c0-494d-b5c7-06948edbe6bb.replay",
      "policy_version_ids": [
        "c28d4d78-56ba-4d34-8e28-14235003abf4",
        "208c6f1d-5280-407f-95b6-0c235da1d1af"
      ],
      "created_at": "2026-08-27T03:14:24.888120Z"
    }
  ],
  "next_cursor": null
}
```

```bash
curl -sS "$BASE/episode-requests/ereq_999e93c3-63af-4db3-becd-99b4f32e938e" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/c56682ec-f4c0-494d-b5c7-06948edbe6bb.replay",
  "participants": [
    {"position":0,"kind":"policy","policy_version_id":"c28d4d78-56ba-4d34-8e28-14235003abf4",
     "policy_id":"350c4751-45c0-404f-a7f7-a71a3ab0e577","policy_name":"fog-of-war-boards-cartographer",
     "version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
     "is_filler":false,"is_seed":false},
    {"position":1,"kind":"policy","policy_version_id":"208c6f1d-5280-407f-95b6-0c235da1d1af",
     "policy_id":"68f02729-edcd-4866-9b3c-0e360c1f0571","policy_name":"fog-of-war-boards-prober",
     "version":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
     "is_filler":false,"is_seed":false}
  ],
  "participant_scores": [
    {"position":0,"score":1.0},
    {"position":1,"score":-1.0}
  ]
}
```
```bash
… | jq -c '{variant_name, completed_at, cost_usd, game_config}'
{"variant_name":"Phantom Tic-Tac-Toe - 3x3","completed_at":"2026-08-27T03:15:30.550597Z","cost_usd":0.004179,
 "game_config":{"mode":"phantom-ttt","size":3,"first":0,"sense":0,"abrupt":false,
 "players":[{"name":"Player1"},{"name":"Player2"}],"maxPlies":18,"num_agents":2,
 "turnDelayMs":250,"player_connect_timeout_seconds":180}}
```

Observation for the record: the detail route returned `{"detail":"Internal Server Error"}` once
at 03:02Z on the round-2 request and served 200 on every retry thereafter (three consecutive
200s, incl. the one pasted above). Transient, not reproducible.

**Status: TRUE** — `status == "completed"`, non-null `replay_url`, participants name **daveey**
(`fog-of-war-boards-cartographer:v1`, seat 0) and **daveey-1**
(`fog-of-war-boards-prober:v1`, seat 1), both `is_filler: false`. No `Baseline (N)` seat was
needed.

---

## 4. Replay bytes are valid and show the game

Fetched 2026-08-27T03:20:05Z.

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/c56682ec-f4c0-494d-b5c7-06948edbe6bb.replay" -o /tmp/ep.replay
HTTP 200 bytes=4212
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok
python3 -c "open('/tmp/ep.replay','rb').read().decode('utf-8'); print('strict utf-8 decode: ok')"
strict utf-8 decode: ok
jq -r '.protocol, .results.reason' /tmp/ep.replay
fogboards.replay.v1
complete
```

**Protocol match.** `fogboards.replay.v1` is exactly what `design.md` §"Replay bytes
(self-sufficient)" (line 761) declares `replayPayload` writes and the wasm module reads. The
hosted manifest carries the viewer as `manifest.game.replay_viewer.bundle =
sha256:7f02ebf1a3e48a6e89ccf0130819557ea5379b1826dce878ab4ae7c5cfaae4b6` and does not restate
the replay-protocol string, so the design note is the declaring document.

```bash
jq -c '.names, .policyNames, .config' /tmp/ep.replay
["Widget","Ratchet"]
["daveey","daveey-1"]
{"mode":"phantom-ttt","size":3,"abrupt":false,"sense":0,"first":0,"seed":1282467663,"maxPlies":18,"sampled":true}

jq -c '.results' /tmp/ep.replay
{"names":["daveey","daveey-1"],"scores":[1.0,-1.0],"outcome":[1.0,0.0],"stones":[3,2],
 "probes":[0,1],"discovered":[0,1],"guessesMade":[3,4],"guessAccuracy":[0.0,0.0],
 "distToWin":[0,99],"fallbacks":[0,0],"plies":6,"maxPlies":18,"mode":"phantom-ttt","size":3,
 "abrupt":false,"sense":0,"ending":"line","reason":"complete"}
```

`results.reason == "complete"` — the strict form; the `deadline` exception `design.md` §End
conditions declares acceptable was **not** needed.

**Decision / fallback counts.** This game emits no `type=="decision"` event; the decision unit is
the `attempt` event (`kind` names are `start|sense|attempt|win|end`; `sense` is absent because
this variant has `sense: 0`).

```bash
jq -r '[.events[].kind]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.replay
{"attempt": 6, "end": 1, "start": 1, "win": 1}

jq -r '[.events[]|select(.kind=="attempt")]|group_by(.seat)
       |map({seat:.[0].seat,total:length,scripted:(map(select(.scripted==true))|length),
             fellBack:(map(select(.fellBack==true))|length)})' /tmp/ep.replay
[
  {"seat": 0, "total": 3, "scripted": 0, "fellBack": 0},
  {"seat": 1, "total": 3, "scripted": 0, "fellBack": 0}
]
```

Both champion seats: **3 attempts each, 0 scripted, 0 fell-back**. `results.fallbacks` in the
replay bytes agrees: `[0, 0]`. Fallbacks are not a minority — they are zero.

Content is non-trivial (`say` + `notes` per attempt; excerpt, `notes` truncated at 320 chars for
width only):

```json
{"kind":"start","round":-1}
{"kind":"attempt","round":0,"seat":0,"cell":"b2","result":"placed","say":"Taking the center to control the board.","notes":"MY STONES: b2. OPPONENT PROVEN: none. UNTOUCHED: a1 b1 c1 a2 c2 a3 b3 c3. STRATEGY: Center is strongest opening in tic-tac-toe. From b2 I control 4 lines (row 2, col b, both diagonals). Next I'll …
{"kind":"attempt","round":1,"seat":1,"cell":"b2","result":"occupied","say":"Probing the center to gather early intelligence on opponent strategy.","notes":"Ply 2: Widget placed 1 stone on ply 1. I have 0 stones. Starting with center (b2) to test Widget's likely strategy. In Phantom Tic-Tac-Toe, opponents typically aim …
{"kind":"attempt","round":2,"seat":1,"cell":"b1","result":"placed","say":"Probing b1 to test if Widget is building vertically through center.","notes":"Ply 3: Widget has 1 stone at b2 (proven). I have 0 stones. Widget likely building on center line (b1-b2-b3) for vertical control. Testing b1 now. If occupied, Widget is…
{"kind":"attempt","round":3,"seat":0,"cell":"a1","result":"placed","say":"Probing a corner to build threats while opponent is likely in another corner.","notes":"MY STONES: b2. OPPONENT PROVEN: none. UNTOUCHED: b1 c1 a2 c2 a3 b3 c3 (a1 now tested). STRATEGY: From b2 I control 4 lines (row 2, col b, both diagonals). Opp…
{"kind":"attempt","round":4,"seat":1,"cell":"b3","result":"placed","say":"Probing b-column. Widget likely vertical on b1-b2-b3.","notes":"Ply 5: Widget has b2 (proven). I have b1 (placed ply 3). Testing b3 to confirm vertical strategy on b-column. If b3 occupied, Widget is definitely building vertical control. If empty…
{"kind":"attempt","round":5,"seat":0,"cell":"c3","result":"placed","say":"Completing the a1-b2-c3 diagonal threat while probing the board.","notes":"MY STONES: a1, b2. OPPONENT PROVEN: none. UNTOUCHED: b1, c1, a2, c2, a3, b3, c3. LIKELY OPPONENT: c1, a3 (corners opposite my stones). STRATEGY: a1-b2-c3 diagonal is my st…
{"kind":"win","round":5,"seat":0,"how":"line","path":["a1","b2","c3"]}
{"kind":"end","round":5,"reason":"complete","ending":"line","scores":[1.0,-1.0]}
```

This is the game the design describes: seat 1 attempts `b2`, gets `result:"occupied"` (the
discovery moment — it learns seat 0 holds the centre without being told), pivots to the b-column
on that inference; seat 0 never proves an opponent stone (`discovered: [0, 1]`) yet builds and
completes the `a1-b2-c3` diagonal. Hidden information is doing work in both directions.

**Status: TRUE** — valid strict-UTF-8 JSON, `protocol == fogboards.replay.v1` as designed,
`reason == "complete"`, both champion seats 100 % non-scripted with substantive content, zero
fallbacks.

---

## 5. Hosted game log is clean

Fetched 2026-08-27T03:20:20Z, for the same latest episode request
`ereq_999e93c3-63af-4db3-becd-99b4f32e938e` (round 3).

```bash
curl -sS "$BASE/episode-requests/ereq_999e93c3-63af-4db3-becd-99b4f32e938e/artifacts/logs" \
  "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs3.txt
HTTP 200 bytes=14137
# decode the python b'…' reprs per playbooks/observatory-api.md §10 before grepping
python3 declogs.py /tmp/logs3.txt > /tmp/logs3.dec.txt   # 59 lines
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs3.dec.txt || echo CLEAN
CLEAN
```
Also grepped against the **undecoded** bytes as a cross-check:
```bash
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs3.txt || echo "CLEAN (raw bytes too)"
CLEAN (raw bytes too)
grep -nEi 'throttl|429' /tmp/logs3.dec.txt || echo none
none
```

The decoded game section, verbatim:

```
fogboards: seed not pinned; randomized
fogboards: seats=2 mode=phantom-ttt size=3 abrupt=false sense=0 maxPlies=18 model=claude-sonnet-5
fogboards: serving on 0.0.0.0:8080
fogboards: player slot 1 connected (1/2)
fogboards: slot 1 delivered a prompt (871 chars)
fogboards: player slot 0 connected (2/2)
fogboards: slot 0 delivered a prompt (890 chars)
fogboards: slot 0 delivered a prompt (890 chars)
fogboards: slot 1 delivered a prompt (871 chars)
fogboards: starting with 2/2 players connected
fogboards llm: bedrock transport, url http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
fogboards: episode timeout 1200s (assumed); playing until 720s
fogboards: ply 1 Widget plays b2 at 8s
fogboards: ply 2 Ratchet plays b2 at 13s
fogboards: ply 3 Ratchet plays b1 at 16s
fogboards: ply 4 Widget plays a1 at 21s
fogboards: ply 5 Ratchet plays b3 at 24s
fogboards: ply 6 Widget plays c3 at 28s
fogboards: writing results and replay
fogboards: artifacts written; serving for 20s of shutdown grace
fogboards: episode complete, shutting down
```

**Status: TRUE** — CLEAN, on both the decoded text and the raw bytes.

**Recorded, not counted against this check** — the *previous* round's log (round 2,
`ereq_bcc822fc-d3b9-4e74-a48e-e8df89a62fe4`, fetched 03:04Z) was **not** clean:

```
62:fogboards llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
63:fogboards llm: seat 0 attempt 0 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
```

This is the platform-wide Bedrock **capacity** symptom, not a defect in this coworld, and the
cross-check `prompts/60-verify.md` check 5 requires was performed against another LLM coworld's
latest episode in the same window — **negotiation-games** (a different repo, different run, at
phase 80), `ereq_854455ae-1575-4c44-8706-b8f240936529`, `created_at 2026-08-27T02:55:59Z`,
`completed_at 2026-08-27T03:00:24Z`, i.e. overlapping this run's round 2:

```bash
curl -sS "$BASE/episode-requests/ereq_854455ae-1575-4c44-8706-b8f240936529/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}"
158:negotiation llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-6
159:negotiation llm: seat 0 attempt 0 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
```

Same model, same 429, same daily-token message, in a coworld that shares no code with this one —
Bedrock capacity shared across parallel runs (SPEC §Parallelism and per-run isolation). Round 2
still produced a fully non-scripted episode (`results.fallbacks: [0,0]`, 9/9 attempts
`scripted:false, fellBack:false`) because the coworld's own model fallback held. Round 3, the
round this check adjudicates, is clean outright.

---

## 6. The public page uses the static replay path

Fetched 2026-08-27T03:20:30Z.

**Source A — raw HTML grep (found nothing; recorded as *unknown*, not as a failure):**
```bash
curl -sS "https://softmax.com/fog-of-war-boards" | grep -o '<iframe[^>]*src="[^"]*"'
# HTTP 200, 649689 bytes, no match — 0 occurrences of the string "iframe" in the document.
```
Expected: the page is client-rendered for the iframe (`playbooks/observatory-api.md` §Featured
match, lighthouse run 2026-08-22).

**Source B — the coworld detail API (also not evidence here, recorded for completeness):**
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end|.[]|select(.name=="fog-of-war-boards")|{id,name,canonical,replay_viewer,featured_match}'
{"id":"cow_5f8e4d33-49d7-4b19-8092-cc69d201344c","name":"fog-of-war-boards","canonical":true,
 "replay_viewer":null,"featured_match":null}
```
`featured_match: null` is platform-wide on this route (same playbook note) — not evidence either
way. Note `/coworlds` also returns a **bare array** here.

**Source C — the two things that *are* evidence, and the ones I used.**

*(i) Featured match, from the page's own SSR payload* (`state.playlist[0]`, read out of the same
649 KB HTML above):
```json
"playlist":[{"episodeId":"848c7c41-4608-45a7-bf7b-f5881bcb1d68",
 "coworldId":"cow_5f8e4d33-49d7-4b19-8092-cc69d201344c",
 "coworldName":"fog-of-war-boards","coworldVersion":"0.1.0",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/c56682ec-f4c0-494d-b5c7-06948edbe6bb.replay",
 "finishedAt":"2026-08-27T03:15:30.550597Z","roundNumber":3,"episodeNumber":1,
 "code":"fog-of-war-boards.r3.e1",
 "matchup":{"divisionId":"div_8c9c080c-31db-4672-8146-d73cd81ebc42","divisionName":"Competition",
   "first":{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
            "score":1001.4695015289755, …
```
A featured match **is present**, it is round 3's episode (the same replay as checks 3–4), and it
carries a two-player matchup — so the "fewer than two ranked players" failure does not apply.

*(ii) The iframe `src`, from the call the page's own JS makes:*
```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_5f8e4d33-49d7-4b19-8092-cc69d201344c",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/c56682ec-f4c0-494d-b5c7-06948edbe6bb.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_5f8e4d33-49d7-4b19-8092-cc69d201344c/sha256%3A3af044a284b6a9e2b4b5a1d7d73c03d0cc9fc701ebc4a3dff49af9fc8e569341/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fc56682ec-f4c0-494d-b5c7-06948edbe6bb.replay&v=2",
  "ready": true
}
```

Path shape: `/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`. The `<sha>`
is `sha256:3af044a284b6a9e2b4b5a1d7d73c03d0cc9fc701ebc4a3dff49af9fc8e569341` URL-encoded — the
coworld's manifest hash, matching `STATE.coworld.manifest_sha` exactly. `ready: true`. There is
no `/client/replay` anywhere in the URL.

**Status: TRUE** — source used: **C** (SSR `state.playlist[0]` for the featured match +
`POST /coworlds/replays/session` for the `src`), after A and B returned the documented
platform-wide nulls. Static route, `ready:true`, featured match present.

---

## 7. Certification declared the static bundle

Source read: the **committed** `runs/2026-08-27-fog-of-war-boards/release-result.json` (the copy
phase 40 downloaded from release run `33034451372` and committed at 02:56:35Z). It was present;
no re-download from `gh run download` was needed.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-27-fog-of-war-boards/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Surrounding certification transcript from the same file (`.certify.output_tail`), all ten steps:

```
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

**Status: TRUE** — the required string `Replay liveness: skipped (static replay bundle declared`
is present, read from the committed `runs/<run>/release-result.json`.

---

## 8. Spectator judgment — the viewer EXECUTED

*(a) Dispatch.* The `src` used is the **full** iframe `src` from check 6, `?replay=` and `&v=2`
included.

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_5f8e4d33-49d7-4b19-8092-cc69d201344c/sha256%3A3af044a284b6a9e2b4b5a1d7d73c03d0cc9fc701ebc4a3dff49af9fc8e569341/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fc56682ec-f4c0-494d-b5c7-06948edbe6bb.replay&v=2'
# dispatch_at = 2026-08-27T03:20:39Z
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
sleep 10
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[]|[.databaseId,.createdAt,.status]|@tsv'
```
```
33036080393	2026-08-27T03:20:40Z	in_progress      <-- created AFTER dispatch_at 03:20:39Z: this run
33027843730	2026-08-27T00:44:34Z	completed
33027506937	2026-08-27T00:38:16Z	completed
33025003314	2026-08-26T23:56:14Z	completed
…
```
The new run was identified by `createdAt` > `dispatch_at`, not by taking "the latest".

```bash
gh run watch 33036080393 -R Metta-AI/coworld-builder --exit-status
✓ Complete job          # green; exit 0
gh run download 33036080393 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-27-fog-of-war-boards/viewer-check
```
```
runs/2026-08-27-fog-of-war-boards/viewer-check/
  smoke-stderr.txt        0 bytes
  smoke-stdout.txt      612 bytes
  viewer-smoke.json    1508 bytes
  viewer-smoke.png   442215 bytes
```
Committed with this file.

*(b) Readouts, verbatim from the artifact.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-27-fog-of-war-boards/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":2047,"clock":"PHANTOM TIC-TAC-TOE · PLY 0 / 18 · DAVEEY TO MOVE","scorebug":"daveey WIDGET ▶ 0 STONES 3 LINE IN daveey-1 RATCHET 0 STONES 3 LINE IN","feed_lines":22}
```

```bash
jq -c '.signals' runs/2026-08-27-fog-of-war-boards/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/2026-08-27-fog-of-war-boards/viewer-check/viewer-smoke.json
no failure
jq -c '.canvas_text' runs/2026-08-27-fog-of-war-boards/viewer-check/viewer-smoke.json
{"total":1067,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
```

**The three clock readouts** (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub | `#clock` |
|---|---|
| 0 % | `PHANTOM TIC-TAC-TOE · PLY 0 / 18 · DAVEEY TO MOVE` |
| 50 % | `PHANTOM TIC-TAC-TOE · PLY 4 / 18 · DAVEEY-1 TO MOVE` |
| 100 % | `PHANTOM TIC-TAC-TOE · PLY 6 / 18 · FINAL` |

All three **differ** — ply 0 → ply 4 → ply 6/FINAL, and the mover alternates correctly
(daveey opens as `first: 0`; ply 4 is daveey-1's, matching the replay's `round:4, seat:1`).
A `#scrub` exists and responds; no `"(no #scrub…)"` sentinel. Console tail: `[bridge] loading`,
`[bridge] ready` — nothing else, no errors.

**Item 8 gate:** `loaded: true` ✔ (in 2047 ms, via both `data-replay-loaded="true"` and the
`coworld-replay` bridge `ready`) **AND** the three clock readouts differ ✔.

*(c) Reconciliation with the replay JSON* (`/tmp/ep.replay`, check 4). Ordered excerpts —
early / middle / late:

```
tick seat  kind      cell result    say
-1   -     start
 0   0     attempt   b2   placed    Taking the center to control the board.
 1   1     attempt   b2   occupied  Probing the center to gather early intelligence on opponent strategy.
 2   1     attempt   b1   placed    Probing b1 to test if Widget is building vertically through center.
 3   0     attempt   a1   placed    Probing a corner to build threats while opponent is likely in another corner.
 4   1     attempt   b3   placed    Probing b-column. Widget likely vertical on b1-b2-b3.
 5   0     attempt   c3   placed    Completing the a1-b2-c3 diagonal threat while probing the board.
 5   0     win                      how=line path=["a1","b2","c3"]
 5   -     end                      reason=complete ending=line scores=[1.0,-1.0]
```
```json
{"names":["daveey","daveey-1"],"scores":[1.0,-1.0],"outcome":[1.0,0.0],"stones":[3,2],
 "probes":[0,1],"discovered":[0,1],"guessesMade":[3,4],"guessAccuracy":[0.0,0.0],
 "distToWin":[0,99],"fallbacks":[0,0],"plies":6,"maxPlies":18,"ending":"line","reason":"complete"}
```

### Spectator judgment

`viewer-smoke.png` (committed alongside this file, 1280×800, captured with the scrubber at the end
of the timeline) shows a **legible, populated, game-specific** frame — not a shell, not a spinner,
not an empty canvas. Everything described below was read off the committed PNG (whole image plus
four crops: header band, centre board, and each flanking board); nothing is inferred.

**Header band.** `FOGBOARDS` wordmark top-left; the clock centred, reading
`PHANTOM TIC-TAC-TOE · PLY 6 / 18 · FINAL`; `REPLAY` and a `« LOG` drawer toggle top-right. Under
it a two-plate scorebug: a red robot chip, `daveey` in orange with `WIDGET` as the small sub-label,
then `3 STONES` and `0 LINE IN` (the `0` picked out in amber); on the right a blue robot chip,
`daveey-1` with `RATCHET` beneath, `2 STONES` and `— LINE IN`. Those four numbers are
`results.stones == [3,2]` and `results.distToWin == [0,99]` (99 renders as the em-dash the design
specifies). Under each name sits the **fog bar**: daveey's is an unlit grey rule, daveey-1's is
lit blue across roughly half its width — `results.discovered == [0,1]`, i.e. daveey has proven
nothing about its opponent and daveey-1 has proven one stone. Each plate then carries this ply's
`say` in its reserved band, verbatim from the replay bytes: *"Completing the a1-b2-c3 diagonal
threat while probing the board."* and *"Probing b-column. Widget likely vertical on b1-b2-b3."*
Policy-owner names with anonymous aliases as sub-labels — the two name spaces the design asked for.

**Playfield — the three boards.** A large centre board captioned `THE BOARD`, files `a b c`
labelled along the bottom and ranks `3 2 1` down the side, flanked by a dimmer `DAVEEY SEES` board
on the left and `DAVEEY-1 SEES` on the right. On the truth board: daveey's red X at c3 and a1
(b2's cell is behind the endcard), daveey-1's blue O at b3 and b1, and an **amber stroke running
the a1→b2→c3 diagonal** — the `win` event's `path:["a1","b2","c3"]`, drawn.

The two belief boards are the show, and they disagree with the truth exactly as the record says:

- `DAVEEY SEES` — its own three red X's at a1, b2, c3; nothing proven about the opponent (b1 and
  b3, where the blue stones actually are, read as empty); and **two blue dashed rings with a grey
  X inside, at a3 and c1**. Those are its guesses. The replay's last seat-0 attempt carries
  `guess: ["c1","a3"]` — the same two cells, and both wrong, which is why
  `guessAccuracy[0] == 0.0`.
- `DAVEEY-1 SEES` — its own blue O at b1 and b3; a **solid red X ringed in grey at b2**, the one
  cell it proved by bouncing off it on ply 2 (`result: "occupied"`); a1 and c3, where the rest of
  the winning diagonal is, read as empty. And a **red dashed ring at b3** — its last
  `guess: ["b3"]`, placed on a cell it occupies itself. `guessAccuracy[1] == 0.0`.

A spectator can read "she has the diagonal and he is still guessing at the b-column" off the
picture alone, without narration. That is what this coworld is about, and it is on screen.

**Endcard.** Overlaid mid-screen: `FINAL — 6 ROUNDS`, `daveey LEADS THE TABLE`, and a table with
columns SCORE / STONES / PROBES / DISCOVERED / GUESS ACC. reading `1 daveey 1.00 3 0 0 0%` and
`2 daveey-1 -1.00 2 1 1 0%`. Every cell matches `results` in check 4 exactly.

**Transport strip.** Bottom band: a `▶` play button at the left, `9 / 9` at the right, and a
scrubber carrying **nine beat ticks — one per event** in the replay's nine-event transcript, with
the design's colour and height coding legible: a grey tick for `start`, alternating red/blue seat
tints for the six `attempt`s, a **taller amber tick third from the left** where seat 1's b2 attempt
came back `occupied` (the discovery beat), a tall red tick for `win` and a tall amber tick for
`end`. Above the scrubber is a dark textured art band, not a data graph — this game's design does
not declare a momentum graph, and none is drawn.

**Feed.** `feed_lines: 22` in the JSON says the feed is populated. It is behind the collapsed
`« LOG` drawer in this frame, so the feed text is not visible in the screenshot; the count and the
drawer toggle are.

**Does it advance?** Yes, and the DOM proves it rather than the picture: PLY 0 → PLY 4 →
PLY 6/FINAL across 0 %/50 %/100 %, with the mover flipping DAVEEY → DAVEEY-1 → FINAL. This is a
replay, not a screenshot.

**Does it look like the starter's chrome?** Yes — recognisably the babel/paintbot lineage: the same
dark palette and condensed type, the same masthead + centred clock + `« LOG` toggle header, the
same per-seat plate with robot chip, stone/tension readouts and a reserved `say` band, the same
bottom transport strip with a beat-ticked scrubber and `n / n` counter, and a centred endcard whose
wording (`FINAL — N ROUNDS`, `<name> LEADS THE TABLE`) is babel's, kept deliberately under the
six-edit letter (phase-20 deviation 2). The one genuinely new region — the three-board truth/belief
layout — is additive, not a rewrite. The cogame-gridlock failure mode (a different product sharing
only the element ids) is not present.

**Legibility notes for the coordinator (non-blocking, phase-30 flavour, not check-8 failures).**
(i) Both belief boards render at very low contrast against the backdrop — legible at 1280 px only
after brightening the crop; the featured-match iframe on softmax.com is ~360 px wide and these
flanking boards are what will wash out first. `canvas_text` reports `total: 1067, outside: 0,
ellipsized: 0`, so this is a contrast/luminance question, not a layout or truncation one.
(ii) The endcard covers the truth board's **entire middle rank**, so the final frame hides b2 —
the pivotal cell of the winning diagonal it is summarising. (iii) This round drew
`phantom-ttt 3×3` with `sense: 0`, so the `sense` event kind and the reconnaissance chrome are
unexercised by this run's rendered evidence — consistent with the phase-30 judge's noted "sense>0
unrendered in CI".

**Status: TRUE** — `loaded: true` and three differing clock readouts; the rendered frame is
legible and shows this game.
