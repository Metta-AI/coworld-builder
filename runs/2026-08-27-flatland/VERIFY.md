# VERIFY — flatland   (2026-08-27T20:36Z)

Verdict: **all-true (8/8)**, with two non-blocking observations recorded in §5 and §8.

Coworld `flatland` v0.1.5 · `cow_f29f97b1-da55-4662-8dbc-cefde73f528d` ·
manifest `sha256:ab884d3298105799394a683dc476cade0c9746d52dc309896c6f4bfdaca22883`
League `league_b8ffbdda-2f8f-45af-b905-e600ba385cff` · division `div_444f4a49-4ebc-4a04-aee6-f05dd6d88993`

Every fetch below was made in this verifier session (2026-08-27 19:52Z – 20:36Z). Headers sent on
every Observatory call: `Authorization: Bearer $SOFTMAX_TOKEN` (value never printed) and
`User-Agent: coworld-builder/1.0`; artifact/filler reads add `X-Use-Elevated-Privileges: true`.

```bash
BASE=https://softmax.com/api/observatory/v2
L=league_b8ffbdda-2f8f-45af-b905-e600ba385cff
D=div_444f4a49-4ebc-4a04-aee6-f05dd6d88993
COW=cow_f29f97b1-da55-4662-8dbc-cefde73f528d
```

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | **TRUE** (3 completed) |
| 2 | Both champions ranked, fillers absent | **TRUE** |
| 3 | Latest round's episode request completed with a replay | **TRUE** |
| 4 | Replay bytes valid, protocol matches, champions play | **TRUE** |
| 5 | Hosted game log clean | **TRUE** for the latest round (round 3); see the round-2 observation |
| 6 | Public page uses the static replay path | **TRUE** |
| 7 | Certification declared the static bundle | **TRUE** |
| 8 | Viewer executed: `loaded:true` + three differing clocks | **TRUE** |

---

## 1. ≥2 completed rounds after the fillers were set

Fillers were registered at **2026-08-27T19:49Z**, before the first `trigger-round`
(`runs/2026-08-27-flatland/log.md`, line stamped `19:50:51Z`:
`50 fillers POST /leagues/$L/filler-policies 200: flatland-timetable:v3=afcff3e9-…, flatland-yielder:v3=02c72099-… (neither champion)`,
recorded in the same batch as, and before, `50 unpause 200; trigger-round 200 … round 1 pending`).
Round 1's `created_at` is `2026-08-27T19:50:00.390830Z` — **after** the filler POST — so rounds 1, 2
and 3 all qualify. The fillers are confirmed live below and confirmed *seated* by §3 and §4.

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -c 'if type=="array" then . else .entries end | map({id,round_number,status,error,created_at,completed_at})'
```
Fetched 2026-08-27T20:32:10Z — `HTTP 200`:
```json
[{"id":"round_603575ef-897f-4d79-9372-a89a4c162d92","round_number":3,"status":"completed","error":null,"created_at":"2026-08-27T20:20:02.417967Z","completed_at":"2026-08-27T20:27:22.809159Z"},
 {"id":"round_fc922549-2453-4e0d-8d86-9eef7053d0bf","round_number":2,"status":"completed","error":null,"created_at":"2026-08-27T20:05:00.839324Z","completed_at":"2026-08-27T20:11:59.152804Z"},
 {"id":"round_a96b1813-d09e-4942-bef7-032bd2d7e062","round_number":1,"status":"completed","error":null,"created_at":"2026-08-27T19:50:00.390830Z","completed_at":"2026-08-27T19:56:51.634233Z"}]
```
```bash
jq -r '[ (if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
```
```
3
```
Zero rounds with status `failed` or `discarded`; every `error` is `null`.

Round 3's `round_config.entrant_attributions` (same fetch) shows both champions seated:
```json
[{"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player","policy_version_id":"9aef8143-46a3-469c-a0ab-0a50220f3af6","league_policy_membership_id":"lpm_65d307b3-6cfe-4809-87ca-d62d17653252"},
 {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","subject_type":"player","policy_version_id":"e41a0e59-087e-4782-bf82-2bd1f815854d","league_policy_membership_id":"lpm_e6b406e3-b245-486c-8949-f5e7ffb7ca56"}]
```

Corroborating fetch — the filler list currently registered on the league:
```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"     # HTTP 200
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"afcff3e9-cb63-4828-91a9-2ba95b8623e8","policy_id":"eaa81a62-bf83-4b54-a905-47ae9b99b98f","policy_name":"flatland-timetable","version":3,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},
 {"policy_version_id":"02c72099-bf18-4f14-8cb5-ef0a62bc1a97","policy_id":"72405434-9bcf-41f9-b8ec-ca099b07ae8a","policy_name":"flatland-yielder","version":3,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```
Neither filler version id equals a champion's (`9aef8143-…`, `e41a0e59-…`).

**Status: TRUE** — rounds 1, 2 and 3 completed (at 19:56:51.63Z, 20:11:59.15Z, 20:27:22.81Z), all
created after the fillers were registered at 19:49Z.

*(API-shape note: this endpoint returned `{"entries":[…]}` at 20:32Z but a **bare array** at 19:52Z
and 19:58Z in the same session. All jq above is dual-shape.)*

---

## 2. Both champions ranked; fillers absent

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq -c '.'
```
Fetched 2026-08-27T20:32:47Z — `HTTP 200`, a bare list:
```json
[{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":1014.6658413353916,"score_label":"MMR","score_value_type":"integer","rounds_played":3,"episode_wins":2.0,"episodes_played":null,"win_rate":0.6666666666666666,"policy_label":"flatland-pathfinder:v3","recent_rounds":null},
 {"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":985.3341586646084,"score_label":"MMR","score_value_type":"integer","rounds_played":3,"episode_wins":1.0,"episodes_played":null,"win_rate":0.3333333333333333,"policy_label":"flatland-signalman:v2","recent_rounds":null}]
```
```bash
jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey-1	flatland-pathfinder:v3	1014.6658413353916	3	2.0
2	daveey	flatland-signalman:v2	985.3341586646084	3	1.0
```

**Status: TRUE** — `daveey` (rank 2, `flatland-signalman:v2`, `rounds_played` 3) and `daveey-1`
(rank 1, `flatland-pathfinder:v3`, `rounds_played` 3) are both ranked, each ≥ 1 round. The two
filler policies (`flatland-timetable:v3`, `flatland-yielder:v3`) appear on **no** row — the list has
exactly two entries — so the "absent or labelled Baseline" condition is met by absence.

---

## 3. Latest round's episode request completed with a replay

Latest completed round = **round 3**, `round_603575ef-897f-4d79-9372-a89a4c162d92`.
The flat `GET /episode-requests?round_id=` route is 405 (playbook §9); the nested route is used.

```bash
R=round_603575ef-897f-4d79-9372-a89a4c162d92
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" | jq -c '… map({id,status,replay_url})'
```
Fetched 2026-08-27T20:32:2xZ — `HTTP 200`:
```json
[{"id":"ereq_c4b78ba5-d4e8-4ab6-8504-c54ae08c812d","status":"completed","replay_url":"https://softmax-public.s3.amazonaws.com/replays/4fe82cbb-76e5-49a9-a0f8-4a1cb64bba2e.replay"}]
```
```bash
EREQ=ereq_c4b78ba5-d4e8-4ab6-8504-c54ae08c812d
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" | jq '{status, replay_url, participants, participant_scores}'
```
`HTTP 200`:
```json
{"status":"completed",
 "replay_url":"https://softmax-public.s3.amazonaws.com/replays/4fe82cbb-76e5-49a9-a0f8-4a1cb64bba2e.replay"}
```
```
position  policy_name          version  player_name  is_filler
0         flatland-signalman   v2       daveey       false
1         flatland-pathfinder  v3       daveey-1     false
2         flatland-yielder     v3       daveey       true
3         flatland-yielder     v3       daveey       true
```
```json
"participant_scores": [{"position":0,"score":13151.0},{"position":1,"score":13153.0},{"position":2,"score":13154.0},{"position":3,"score":13155.0}]
```

**Status: TRUE** — `status == "completed"`, `replay_url` non-null, seats 0/1 are the two champions
named `daveey` / `daveey-1` with `is_filler:false`, seats 2/3 are the registered filler
(`flatland-yielder:v3`, `is_filler:true`) and are renamed `Baseline` / `Baseline (2)` in the replay's
own `results.names` (see §4).

---

## 4. Replay bytes are valid and show the game

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/4fe82cbb-76e5-49a9-a0f8-4a1cb64bba2e.replay" -o /tmp/ep.replay
```
```
HTTP 200 bytes=484876 type=application/octet-stream
$ od -c -N 16 /tmp/ep.replay
0000000   C   O   W   L   D   F   L   T 001  \0  \b  \0  \0  \0   f   l
```

**Documented exception, cited:** the raw bytes are the starter's **binary `COWLDFLT`** container, not
a JSON document — `runs/2026-08-27-flatland/design.md` §"Replay bytes (self-sufficient)" declares
this ("The replay stays the starter's **binary `COWLDFLT`** format — the static wasm viewer parses
exactly this") and prescribes **the phase-60 substitute for SPEC §Definition of done check 4**:
`tools/replay_summary.py`, a Python-3-stdlib decoder shipped in the repo, whose output is required to
be one strict-UTF-8 JSON object. That tool was fetched fresh this run from
`https://raw.githubusercontent.com/Metta-AI/cogame-flatland/main/tools/replay_summary.py` (176 lines)
and its module docstring restates the same procedure.

```bash
jq -e . /tmp/ep.replay >/dev/null 2>&1 || echo "raw=binary COWLDFLT (design.md §Replay bytes)"
python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .gameVersion, .network, .seed, .tickCount' /tmp/ep.json
```
```
raw=binary COWLDFLT (design.md §Replay bytes)
strict UTF-8 JSON: ok
flatland/v1
1
main_c
1787862035
496
```
`protocol == "flatland/v1"` matches the manifest's declared protocol (design.md §Replay bytes /
§Manifest: `"protocol":"flatland/v1"`).

```bash
jq -c '.results' /tmp/ep.json
```
```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],
 "aliases":["Alpha","Beta","Gamma","Delta"],
 "reason":"complete","endRule":"tickCap",
 "fleetOnTime":13,"parOnTime":15,"arrivedTotal":15,
 "arrived":[3,3,4,5],"onTime":[1,3,4,5],
 "policyKinds":["llm","llm","scripted","scripted"],
 "llmTurns":[31,31,0,0],"fallbackTurns":[0,0,0,0],"ordersRejected":[1,3,0,0],
 "deadSeats":[false,false,false,false],"stopDetail":"",
 "finalTick":496,"turnsPlayed":31,"deadlocks":2,"jams":2,"malfunctions":11}
```
`results.reason == "complete"` — the normal end; no `deadline` exception needed.
`results.arrivedTotal == 15 > 0`. Filler seats are renamed `Baseline` / `Baseline (2)`.

```bash
jq -r '[.orders[]|{slot,source}]|group_by(.slot)|.[]|"slot \(.[0].slot): \(length) turns sources=\([.[].source]|unique|join(","))"' /tmp/ep.json
jq -r '"radio_lines=\(.radio|length) llm_orders=\([.orders[]|select(.source=="llm")]|length) fallback_orders=\([.orders[]|select(.source=="fallback")]|length) fallback_records=\(.fallbacks)"' /tmp/ep.json
```
```
slot 0: 31 turns sources=llm
slot 1: 31 turns sources=llm
slot 2: 31 turns sources=scripted
slot 3: 31 turns sources=scripted
radio_lines=60 llm_orders=62 fallback_orders=0 fallback_records=0
```
**Zero fallbacks** — not "a small minority", none at all. Both champion seats produced live LLM
orders on all 31 turns (`llmTurns:[31,31,0,0]`, `fallbackTurns:[0,0,0,0]`).

Champion decisions with non-trivial content — ordered excerpts (mean champion radio line length
114 chars):

*Early (turn 1–2 orders):*
```
1	0	llm	T01:hold T02:hold T03:hold T04:hold T05:hold T06:hold
1	1	llm	T07:hold T08:hold T09:run T10:hold T11:hold T12:hold
2	0	llm	T01:hold T02:hold T03:hold T04:hold T05:run T06:hold
2	1	llm	T07:run T08:hold T09:run T10:hold T11:hold T12:hold
```
*Early radio:*
```
1	0	Alpha	Alpha: speed-priority railway. T04 and T06 are freight (ticks_per_cell 3), will side for faster trains. T01, T02, T03, T
1	1	Beta	single track is up-only for me: J2->J5, J6->J8. T09 running now to F, others staggered.
2	1	Beta	Beta: single-track up-only: J2->J3, J3->J6, J6->J8, J7->J9, J8->J1, J9->J5. T09 to F (due 97), T07 to A (due 104) releas
```
*Middle radio (turns 16–17):*
```
16	0	Alpha	Alpha enforces speed priority: expresses T01,T05 keep main; freight T06 sides at S5. T01 heads S from J2→B. T05 heads N
16	1	Beta	Beta: T07 sacrificed to S5, clearing J2 jam. T11 running now. Single track up-only: J2→J5, J6→J8, @17,2→@23,2, @22,10→J7
17	0	Alpha	Alpha: T05,T01 expresses routing J2→J8 to clear deadlock. T06 freight diverting S3. Holding T02,T04 until jam clears.
17	1	Beta	T07 past recovery (152 late), sides S5 to clear J2 jam. T11 released northbound to G. Single track up-only: J2→J5, J6→J8
```
*Late (turns 30–31 orders + radio):*
```
30	0	llm	T01:run T02:hold T03:run T04:run T05:hold T06:siding(S3)
30	1	llm	T07:siding(S5) T08:run T09:run T10:run T11:run T12:run
31	0	llm	T01:run T02:hold T03:run T04:run T05:hold T06:siding(S3)
31	1	llm	T07:siding(S5) T08:run T09:run T10:run T11:run T12:run
30	0	Alpha	Alpha concedes. 3 on-time; T02/T05 unrecoverable behind Beta's jam. T06 holding S3.
30	1	Beta	T07 to S5 to clear J2. T11/T12 moving to unblock jam.
```
The champions use three of the four verbs (`run`, `hold`, `siding(S3)`, `siding(S5)`), name real
junctions/stations from the `main_c` network, negotiate single-track direction over the radio and
respond to the jam and deadlock the engine recorded (`jams:2`, `deadlocks:2`) — this is train
dispatching, which is what the game is about.

**Status: TRUE** — strict-UTF-8 JSON under `jq -e` (via the design-declared decoder),
`protocol == "flatland/v1"`, `results.reason == "complete"`, 62/62 champion decisions LLM-sourced,
0 fallbacks.

---

## 5. Hosted game log is clean

The artifact body is python `b'…'` byte-string reprs under `===== container: … =====` headers; it was
decoded per-repr with `ast.literal_eval` before grepping (playbook §10 — a line-based grep on the raw
body undercounts).

```bash
curl -sS "$BASE/episode-requests/ereq_c4b78ba5-d4e8-4ab6-8504-c54ae08c812d/artifacts/logs" \
  "${AUTH[@]}" "${ELEV[@]}" -o logs3_raw.txt        # HTTP 200 bytes=131521
python3 decode_logs.py logs3_raw.txt logs3_decoded.txt   # ast.literal_eval per b'…' repr
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs3_decoded.txt || echo CLEAN
```
```
CLEAN
# containers=4 decoded_lines=259 matches=0
```
Containers present: `coworld-init-config`, `bedrock-sidecar`, `game`, `worker`. The whole `game`
container, verbatim:
```
===== container: game =====
flatland: network=main_c seed=1787862035 trains=24 seats=4 maxTicks=496 turnTicks=16
flatland: listening on 0.0.0.0:8080
flatland llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
flatland: seat 0 (Alpha) registered as llm/signalman
flatland: seat 3 (Delta) registered as scripted/yielder
flatland: seat 1 (Beta) registered as llm/pathfinder
flatland: seat 2 (Gamma) registered as scripted/yielder
flatland: episode settled reason=complete endRule=tickCap arrived=15 onTime=13 par=15 ticks=496
```

**Status: TRUE** — zero matching lines in the latest round's hosted log.

### Observation (non-blocking, but the coordinator should see it): round 2's log was **not** clean

Round 2 (`ereq_6b35ad65-75d5-4c60-ad2e-7bdbb0bac1e6`) was the latest completed round when this check
was first run at 20:16Z. Its decoded log produced **9 matching lines** (attempt 1 of the retry
budget; the retry that produced the TRUE above was the prompt's sanctioned "different round"):
```
game:8:  flatland llm: seat 1 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
game:9:  flatland llm: seat 1 falling back to yielder (parse_error) on turn 6
game:10: flatland llm: seat 1 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
game:11: flatland llm: seat 1 falling back to yielder (parse_error) on turn 11
game:12: flatland llm: seat 1 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
game:13: flatland llm: seat 1 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
game:14: flatland llm: seat 1 falling back to yielder (parse_error) on turn 15
game:15: flatland llm: seat 1 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
game:16: flatland llm: seat 1 falling back to yielder (parse_error) on turn 26
# containers=4 decoded_lines=272 matches=9
```
Round 2's replay confirms the impact: `fallbackTurns:[0,4,0,0]`, `llmTurns:[31,27,0,0]`,
`results.reason:"complete"` — 4 of 31 turns on seat 1 (12.9 %) used the `yielder` fallback; 58 of 62
champion decisions were still LLM-sourced. Round 1 (`ereq_e3024455-…`) and round 3 were both `CLEAN`
with `fallbackTurns:[0,0,0,0]`.

Diagnosis, from the same log's `bedrock-sidecar` container (63 `bedrock_sidecar_complete` records,
**`"ok":false` count = 0**, all `status_code:200`, tail of the latency distribution
`…7035.8, 7340.5, 7391.2, 8059.4` ms): this is **not** `LLM provider is unavailable` and not a
Bedrock outage — every sidecar call succeeded. It is flatland's own **attempt-1 deadline
`attempt1Ms = 9.0 s`** (design.md §"One command turn every 16 ticks") sitting close to observed
haiku latency, so a slow tail call trips the client timeout. A cross-check against another LLM
coworld was attempted and is **inconclusive rather than corroborating**: the newest canonical
coworld, `pommerman` v0.1.0 (`ereq_97defe7d-3912-4981-8108-879fceb39a4d`, 20:02Z), greps CLEAN but
ran `policyKinds:["scripted","scripted","scripted","scripted"]` with `llmTurns:[0,0,0,0]` — it made
no Bedrock calls, so it cannot confirm or deny a platform symptom.

I am **not** claiming a documented platform-wide exception for round 2. Check 5 is TRUE on its own
terms (the latest round's log is clean) and this is recorded as a **phase-30 tuning finding**: raise
`attempt1Ms` (or lower `maxOutputTokens`) if the coordinator wants the margin. It is intermittent —
1 of 3 rounds — and never cost the episode: all three rounds settled `reason=complete`.
Also worth flagging to the game author: the fallback `cause` was logged as `parse_error` on turns
whose only recorded failure was a transport timeout, which looks like a cause-enum mislabel against
design.md's `cause ∈ {timeout, parse_error, transport_error, …}`.

---

## 6. The public page uses the static replay path

```bash
curl -sS "https://softmax.com/flatland" | grep -o '<iframe[^>]*src="[^"]*"'
```
Fetched 2026-08-27T20:32:5xZ — `HTTP 200 bytes=698112`:
```
(no <iframe … src=…> in raw HTML)
```
Not a false negative — the page is client-rendered (playbook §Featured match / replay route,
answered by the lighthouse run). Two fallbacks were used; **the source of record for the iframe `src`
is the third**:

**(a) `/coworlds` detail — not usable, as the playbook predicts:**
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -c '…|select(.name=="flatland" and .canonical==true)|{id,name,version,canonical,replay_viewer,featured_match}'
```
```json
{"id":"cow_f29f97b1-da55-4662-8dbc-cefde73f528d","name":"flatland","version":"0.1.5","canonical":true,"replay_viewer":null,"featured_match":null}
```
`featured_match: null` is platform-wide and is not evidence either way.

**(b) The featured match, server-rendered into the page's SSR payload at `state.playlist[0]` —
PRESENT:**
```
\"leagueId\":\"league_b8ffbdda-2f8f-45af-b905-e600ba385cff\",\"playlist\":[{\"episodeId\":\"3db5dcfe-d145-417e-ac7b-e0d68066fd1d\",
\"coworldId\":\"cow_f29f97b1-da55-4662-8dbc-cefde73f528d\",\"coworldName\":\"flatland\",\"coworldVersion\":\"0.1.5\",
\"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/4fe82cbb-76e5-49a9-a0f8-4a1cb64bba2e.replay\",
\"finishedAt\":\"2026-08-27T20:27:13.724790Z\",\"roundNumber\":3,\"episodeNumber\":1,\"code\":\"flatland.r3.e1\",
\"matchup\":{\"divisionId\":\"div_444f4a49-4ebc-4a04-aee6-f05dd6d88993\",\"divisionName\":\"Competition\",
\"first\":{\"rank\":1,\"player_id\":\"ply_bac48eb1-…\",\"player_name\":\"daveey-1\",\"score\":1014.6658413353916,…,
\"policy_label\":\"flatland-pathfinder:v3\",…},\"second\":{\"rank\":2,\"p…
```
and, further down the same payload:
```
\"divisionName\":\"Competition\",\"divisionCount\":1,\"playerCount\":2,\"activeRound\":null,
\"newestCompletedAt\":\"2026-08-27T20:27:22.809159Z\",\"firstPlace\":{\"current\":{\"player_id\":\"ply_bac48eb1-…\",
\"player_name\":\"daveey-1\",\"started_at\":\"2026-08-27T20:27:22.814592Z\",\"rounds_held\":1,\"score\":1014.6658413353916,
\"second_player_name\":\"daveey\",\"gap_to_second\":29.331682670783266,…
```
The featured match is the round-3 episode, the same `replay_url` as §3/§4.

**(c) The iframe `src` — the call the page's own JS makes:**
```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
 -d '{"coworld_id":"cow_f29f97b1-da55-4662-8dbc-cefde73f528d","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/4fe82cbb-76e5-49a9-a0f8-4a1cb64bba2e.replay"}'
```
`HTTP 200`:
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_f29f97b1-da55-4662-8dbc-cefde73f528d/sha256%3Aab884d3298105799394a683dc476cade0c9746d52dc309896c6f4bfdaca22883/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F4fe82cbb-76e5-49a9-a0f8-4a1cb64bba2e.replay&v=2","ready":true}
```

**Source used: (b) the SSR payload for the featured match + (c) the replay-session route for the
`src`.** The path is `/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`; `<sha>`
URL-decodes to `sha256:ab884d3298105799394a683dc476cade0c9746d52dc309896c6f4bfdaca22883`, byte-equal
to `STATE.coworld.manifest_sha` and to `release-result.json.manifest_sha`. `ready: true`. There is no
`/client/replay` and no pod URL anywhere in the path.

**Status: TRUE** — featured match present (round 3, `flatland.r3.e1`), iframe `src` is the static
route.

---

## 7. Certification declared the static bundle

Source read: **the committed `runs/2026-08-27-flatland/release-result.json`** — phase 40's artifact
copy, present in the tree, committed in `6e7d9b7 flatland 40: release v0.1.5 canonical (cow_f29f97b1),
log the three dispatches`. No re-download from run 33109427929 was needed.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-27-flatland/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```
Corroborating fields in the same file: `"ok": true`, `"canonical": true`, `"hosted_smoke": "passed"`,
`"hosted_certification": "certified"`, `"certify": {"ok": true, …}`, `"errors": []`,
`"step_failed": null`, and the transcript tail showing 10/10 certification steps passed including
`[pass] replay-loadable: the replay artifact has a declared viewer path`.

**Status: TRUE** — contains `Replay liveness: skipped (static replay bundle declared`.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged

*(a) Dispatch.* Dispatched at **2026-08-27T20:33:14Z** against the exact `src` from §6:

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_f29f97b1-da55-4662-8dbc-cefde73f528d/sha256%3Aab884d3298105799394a683dc476cade0c9746d52dc309896c6f4bfdaca22883/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F4fe82cbb-76e5-49a9-a0f8-4a1cb64bba2e.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -c 'sort_by(.createdAt)|reverse|.[0:4]'
```
```json
[{"conclusion":"","createdAt":"2026-08-27T20:33:16Z","databaseId":33113882071,"status":"in_progress"},
 {"conclusion":"success","createdAt":"2026-08-27T19:03:57Z","databaseId":33106609970,"status":"completed"},
 {"conclusion":"success","createdAt":"2026-08-27T15:22:13Z","databaseId":33087427495,"status":"completed"},
 {"conclusion":"success","createdAt":"2026-08-27T11:25:59Z","databaseId":33067338841,"status":"completed"}]
```
Run **33113882071** was created at 20:33:16Z, two seconds after the dispatch — selected by
`createdAt` sort, not by `-L 1`.
```bash
gh run watch 33113882071 -R Metta-AI/coworld-builder --exit-status
```
```
✓ viewer-check in 1m10s (ID 98663444388)
  ✓ Install Playwright (pinned 1.55.0)
  ✓ Load the viewer
  ✓ Upload the evidence
  ✓ Fail if the viewer did not load
```
Green (`watch_exit=0`).
```bash
gh run download 33113882071 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-27-flatland/viewer-check
```
Committed under `runs/2026-08-27-flatland/viewer-check/`: `viewer-smoke.json` (2958 B),
`viewer-smoke.png` (400699 B), `smoke-stdout.txt` (890 B), `smoke-stderr.txt` (0 B).

*(b) The readouts, verbatim.*
```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-27-flatland/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":4972,"clock":"ON TIME 0 / 15 PAR · TICK 0/496 · TURN 1/31 · ARRIVED 0 · BROKEN 0 · DEADLOCK 0","scorebug":"0/6 SIGNALMAN ON TIME 0 0 late 0/6 YIELDER ON TIME 0 0 late ON TIME 0 / 15 PAR · TICK 0/496 · TURN 1/31 · ARRIVED 0 · BROKEN 0 · DEADLOCK 0 0/6 PATHFINDER ON TIME 0 0 late 0/6 YIELDER ON TIME 0 0 late","feed_lines":0}
```
```bash
jq -c '.signals' …
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```
```bash
jq -r '.failure // "no failure"' …
```
```
no failure
```
```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' …
```

| Scrub | Clock readout |
|---|---|
| **0 %** | `ON TIME 0 / 15 PAR · TICK 0/496 · TURN 1/31 · ARRIVED 0 · BROKEN 0 · DEADLOCK 0` |
| **50 %** | `ON TIME 13 / 15 PAR · TICK 266/496 · TURN 17/31 · ARRIVED 13 · BROKEN 0 · DEADLOCK 2` |
| **100 %** | `ON TIME 13 / 15 PAR · TICK 496/496 · TURN 31/31 · ARRIVED 15 · BROKEN 3 · DEADLOCK 0` |

All three differ, in every field: tick 0 → 266 → 496, turn 1 → 17 → 31, arrived 0 → 13 → 15.
`canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`.

**Item 8 gate: `loaded: true` ✓ (via `data-replay-loaded="true"`, first frame at 4972 ms, no
`data-replay-error`) AND the three clock readouts differ ✓ → TRUE.**

*(c) Reconciliation against the replay JSON.* The 100 % readout `ARRIVED 15 · ON TIME 13 · TICK
496/496 · TURN 31/31` is byte-consistent with §4's `results`: `arrivedTotal:15`, `fleetOnTime:13`,
`finalTick:496`, `turnsPlayed:31`, `parOnTime:15`. The 50 % readout `DEADLOCK 2` matches
`results.deadlocks:2`; the 100 % readout `BROKEN 3` is a live malfunction count at the final tick,
consistent with `results.malfunctions:11` cumulative. The screenshot's per-dispatcher endcard row
values `Alpha 1/3/518/2 · Beta 3/3/0/2 · Gamma 4/4/0/2 · Delta 5/5/0/2` match
`onTime:[1,3,4,5]` and `arrived:[3,3,4,5]` exactly.

### Spectator-judgment paragraph

**It is legible, it is unmistakably this game, and it is the coworld-ctf starter's chrome.**
`viewer-smoke.png` catches the replay parked at 100 %, so the **endcard** is up: a full-bleed dark
board with the rail network dimmed behind it (you can still read station glyphs `B`, `C`, `E`, `F`
and the dashed track), a centred `ON TIME 13` headline over
`/ 15 PAR · TICK 496/496 · TURN 31/31 · ARRIVED 15 · BROKEN 3 · DEADLOCK 0`, a `NETWORK SCORE 13151`
chip and the win-condition line `11 breakdowns, 2 jams, 2 deadlocks, 438 ticks lost (tickCap)`. Below
that sit four per-dispatcher plates — `SIGNALMAN 1 TRAINS ON TIME`, `PATHFINDER 3`, `YIELDER 4`,
`YIELDER 5` — each with the re-mapped endcard header `DISPATCHER · ON TIME · ARRIVED · LATE BY ·
DEADLOCKS` and one row (`Alpha 1 3 518 2`, `Beta 3 3 0 2`, `Gamma 4 4 0 2`, `Delta 5 5 0 2`). That is
exactly the vocabulary design.md's re-labelling table specifies, so this is the starter's endcard
retargeted, not paintbot's leaking through. Top-left is the on-time leaderboard rail
(`DELTA Baseline (2) 5/5 of 6 · GAMMA Baseline 4/4 of 6 · BETA daveey-1 3/3 of 6 · ALPHA daveey 1/3
of 6 late 518`) — a spectator can read who won and by how much without any other source. Top-right
is the deadlock/jam alarm chip `JAM T06 · T07`. The **scorebug** is the starter's four-plate strip
with `ON TIME` counts and `n/6` arrival fractions, and it is populated (the json's `scorebug` string
was sampled at tick 0, hence the zeros there; the png shows it live). The **transport strip** is the
starter's, in full: restart / back / play / +5s / step / loop / fast-forward, a `spoilers` toggle,
the `PAR MISSED` win-chip, the `496 / 496` tick clock and the `1× 2× 3× 4× 8× 16×` speed chips.
Beneath it is the **scrubber with its momentum graph**: a full-width track with coloured beat markers
(green arrivals, red deadlocks, orange malfunctions clustered in the last third) and the `ON TIME`
momentum series drawn under it — the same transport/scrubber/scorebug/endcard family as
paintbot/raid/hive, not a rewrite that reuses the ids. Nothing is empty, nothing is frozen: the three
scrub readouts advance the tick, the turn and the arrival count, and the picture agrees with the
replay's own record of a `main_c` episode that hit the tick cap with 15 of 24 trains home and 13 of a
par-15 on time.

**Two legibility observations for the coordinator (neither blocks item 8):**
1. **Four 404s in the console tail** — leftover coworld-ctf locker-room sprites the flatland bundle
   does not ship:
   ```
   [http 404] …/static/cow_f29f97b1-…/sha256%3Aab884d…/soldier_red_front_gun.png
   [error] Failed to load resource: the server responded with a status of 404 ()
   [http 404] …/soldier_yellow_front_gun.png
   [http 404] …/soldier_blue_front_gun.png
   [http 404] …/soldier_green_front_gun.png
   ```
   The viewer loads and draws regardless (`data-replay-error: null`, `failure: null`), but the
   locker-room art will be blank on first paint. A dangling starter reference — phase-30 item-14
   class, cosmetic.
2. **`feed_lines: 0`** and the truncated plate labels `SI…`, `YI…`, `PA…` in the top scorebug strip
   at 1280 px. The feed count is expected at 100 % (the endcard overlays the killfeed and the play
   head is parked at the end), but it means this run has no rendered proof of the feed rows; the
   plate truncation is a 1280 px density artefact of the starter's `.tiny` system.

**Status: TRUE** — `loaded: true`, three differing clock readouts, and a legible picture that shows
the game.
