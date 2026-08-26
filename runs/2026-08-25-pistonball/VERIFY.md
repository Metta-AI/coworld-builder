# VERIFY — pistonball   (2026-08-26T05:20Z)

Verdict: **all-true (8/8)** — with two material findings recorded below that the judge/coordinator
should weigh (§Findings): a latent per-turn-budget defect proved by round 2's replay, and two
endcard legibility defects visible in the rendered screenshot.

Run `2026-08-25-pistonball` · slug `pistonball` · coworld `cow_58917aec-d633-4f40-89b1-dbf496ddcfe0`
v0.1.2 · league `league_6789db33-ab0a-4b15-b572-b3ea39c614fd` · division
`div_de04ec28-cd1a-4349-9667-d34a687735c7`.

Every item below was fetched **fresh this run** (2026-08-26 04:43Z–05:20Z), except the two
documented exceptions: item 7 (the committed `release-result.json` from this run's phase 40) and
item 8's rendered evidence (the `viewer-check.yml` run **32933394784**, dispatched by me at
05:16:10Z this run, artifact downloaded and committed).

Headers sent on every Observatory call: `Authorization: Bearer $SOFTMAX_TOKEN` (value never
printed), `User-Agent: coworld-builder/1.0`; plus `X-Use-Elevated-Privileges: true` on the
`artifacts/logs` reads. No token-bearing URL appears in this file.

**jq adaptation:** this league's `GET /rounds` and `GET /divisions/<id>/leaderboard` return **bare
JSON arrays**, not `{"entries": …}`. Every `jq` below therefore uses
`if type=="array" then . else .entries end` instead of the phase prompt's `.entries[]`, exactly as
`playbooks/observatory-api.md` §2 warns. `GET /episode-requests?round_id=` **does** return
`{"entries": …}`; the dual-shape filter is harmless there.

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

```bash
BASE=https://softmax.com/api/observatory/v2
L=league_6789db33-ab0a-4b15-b572-b3ea39c614fd
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -c 'if type=="array" then . else .entries end
          | map({id,round_number,status,error,created_at})'
```

```json
[{"id":"round_a2b91a96-4ad9-440b-9823-17e376254c02","round_number":4,"status":"completed","error":null,"created_at":"2026-08-26T05:11:21.326218Z"},
 {"id":"round_23ddf66a-82bd-4fa7-a98f-56aa25b0636b","round_number":3,"status":"completed","error":null,"created_at":"2026-08-26T04:56:20.970743Z"},
 {"id":"round_14591664-b873-456f-82cb-b41cae1763b9","round_number":2,"status":"completed","error":null,"created_at":"2026-08-26T04:41:20.616080Z"},
 {"id":"round_83e94b83-4294-4cf9-97af-ee3aefa794d0","round_number":1,"status":"failed","error":"Temporal RoundWorkflow failed before settling the round.","created_at":"2026-08-26T04:41:01.945026Z"}]
```

```bash
curl -sS … | jq -r '[ (if type=="array" then . else .entries end)[]
                      | select(.status=="completed" and .round_number>=2)]|length'
# -> 3
```

**Round 1 is excluded and its error is recorded verbatim:**
`"Temporal RoundWorkflow failed before settling the round."` — it auto-fired at 04:41:01.945Z,
before the filler policies were registered; `playbooks/observatory-api.md` §6 names this exact
message as what a trigger-round issued with no filler produces. It is `failed`, so it does not
count.

**Proof that rounds 2–4 are *after* the fillers were set** (not merely later in wall-clock): the
filler policy versions actually occupy 18 of the 20 seats in round 2's episode.

```bash
curl -sS "$BASE/episode-requests/ereq_82c67bc1-30bd-4fea-823b-69dd723736d0" "${AUTH[@]}" \
 | jq -r '[.participants[]|select(.is_filler==true)]|length,
          ([.participants[]|select(.is_filler==true)|.policy_version_id]|unique|@csv)'
```
```
18
"bf0ca47e-73a9-4283-bf0a-57f08f0de363","e0e9ce4a-7232-4309-8558-752adb78b10e"
```
Those are exactly `STATE.policies.filler_version_ids` (metronome:v2, wavebot:v2). Round 4's
episode likewise reports 18 filler seats.

Status: TRUE — rounds **2, 3 and 4** completed (created 04:41:20Z, 04:56:20Z, 05:11:21Z), all with
the fillers seated; round 1 `failed` and is not counted.

---

## 2. Both champions ranked, fillers absent — **TRUE**

```bash
D=div_de04ec28-cd1a-4349-9667-d34a687735c7
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq -c 'if type=="array" then . else .entries end'
```

```json
[{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1000.0,"score_label":"MMR","score_value_type":"integer","rounds_played":3,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"pistonball-swell:v2","recent_rounds":null},
 {"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":1000.0,"score_label":"MMR","score_value_type":"integer","rounds_played":3,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"pistonball-cascade:v2","recent_rounds":null}]
```

As `@tsv` (the phase prompt's shape):

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end
          | .[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey	pistonball-swell:v2	1000.0	3	0.0
2	daveey-1	pistonball-cascade:v2	1000.0	3	0.0
```

Status: TRUE — both `daveey` (`pistonball-swell:v2`) and `daveey-1` (`pistonball-cascade:v2`) are
ranked with `rounds_played = 3 ≥ 1`. The board has **exactly two rows**: the fillers
(`pistonball-wavebot:v2`, `pistonball-metronome:v2`) are **absent**, which is the stronger of the
two permitted outcomes.

Note (not a check requirement): `score` is identical (1000.0 MMR) and `episode_wins` is 0.0 for
both because pistonball is a **cooperative shared-score** game — all twenty seats receive the same
`sharedScore` and `win[]` is all-true or all-false together (see the results doc in item 4). Elo
therefore has nothing to separate the two champions on.

---

## 3. The latest round's episode request completed with a replay — **TRUE**

Latest completed round = `round_a2b91a96-4ad9-440b-9823-17e376254c02` (round_number 4).

```bash
R=round_a2b91a96-4ad9-440b-9823-17e376254c02
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)[]|[.id,.status]|@tsv'
```
```
ereq_a459bce3-2e83-47be-9d29-040669d181e4	completed
```

```bash
EREQ=ereq_a459bce3-2e83-47be-9d29-040669d181e4
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" | jq -c '{status, replay_url}'
```
```json
{"status":"completed","replay_url":"https://softmax-public.s3.amazonaws.com/replays/eab95e2d-e17f-42fc-af3f-03177f8a05d1.replay"}
```

Participants (20 seats; first 4 rows plus the aggregate — the full body is 20 objects):

```bash
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq -r '.participants[]|[.position,.policy_name,.version,.player_name,.is_filler]|@tsv'
```
```
0	pistonball-swell	2	daveey		false
1	pistonball-cascade	2	daveey-1	false
2	pistonball-metronome	2	daveey		true
3	pistonball-wavebot	2	daveey		true
…  (positions 4-19: 18 filler seats total, wavebot:v2 / metronome:v2)
```
```bash
… | jq -r '.participants|length,
           ([.participants[]|select(.is_filler==false)|.player_name]|@csv),
           ([.participants[]|select(.is_filler==true)]|length)'
```
```
20
"daveey","daveey-1"
18
```
```bash
… | jq -c '.participant_scores[0:2]'
# [{"position":0,"score":96.599},{"position":1,"score":96.599}]
```

Status: TRUE — `status == "completed"`, `replay_url` non-null, and `participants` names both
`daveey` (position 0, `pistonball-swell:v2`) and `daveey-1` (position 1, `pistonball-cascade:v2`),
with the other 18 seats flagged `is_filler: true` (they render as `Baseline (N)` in the replay and
the endcard — see items 4 and 8).

---

## 4. Replay bytes are valid and show the game — **TRUE**

pistonball's replay is the starter's **binary `COWLDPST`** format, not JSON — the design note
(`runs/2026-08-25-pistonball/design.md` §"Replay bytes (self-sufficient)", lines 937–962) pins this
and prescribes the exact phase-60 substitute used below: run the repo's stdlib-only
`tools/replay_summary.py` and apply the strict parser to *its* output. The repo checkout was
refreshed first (`git fetch origin && git reset --hard origin/main` → `ec82d45`).

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/eab95e2d-e17f-42fc-af3f-03177f8a05d1.replay" \
     -o /tmp/ep.replay -w 'http %{http_code} bytes %{size_download}\n'
# http 200 bytes 19876
python3 -c "print(open('/tmp/ep.replay','rb').read(16))"
# b'COWLDPST\x01\x00\n\x00pist'
python3 /workspace/cogame-pistonball/tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
# strict UTF-8 JSON: ok
jq -r '.protocol, .results.reason, .results.endRule' /tmp/ep.json
```
```
pistonball/v1
complete
delivered
```

`protocol` = `pistonball/v1`, matching the manifest's `game.name`/protocol declaration.
`results.reason == "complete"` — the declared-acceptable `deadline`/`wall_clock` exception was
**not needed**; this episode ended on the real end rule, `delivered` (the ball reached the goal
wall).

**Champion-seat decisions — not fallbacks:**

```bash
jq -c '[.scripts[]|select(.seat==0 or .seat==1)]|group_by(.source)|map({(.[0].source):length})|add' /tmp/ep.json
# {"llm":2}
jq -c '{fallbacks, tickCount, inputRecords, registers}' /tmp/ep.json
# {"fallbacks":0,"tickCount":351,"inputRecords":255,"registers":20}
jq -c '{llmTurns:.results.llmTurns[0:2], fallbackTurns:.results.fallbackTurns[0:2]}' /tmp/ep.json
# {"llmTurns":[1,1],"fallbackTurns":[0,0]}
```

**Fallback count is 0 of 2 champion-seat decisions** — zero, not "a small minority". The two
records themselves (non-trivial, distinct, and clearly reasoning about this game):

```json
{"k":"script","turn":0,"seat":0,"alias":"PST-02","piston":1,"source":"llm","latency_ms":3844,
 "note":"Turn 0: Ball not yet visible. Following operator guidance: wave mode, trigger 1.0, lead 6 ticks, up 1.45m, down 0.05m, speed 1.0, idle 0.25m. Ready to shoulder ",
 "say":"PST-02 ready: wave mode, eyes open","mode":"wave","trigger_m":1.0,"lead_ticks":6,
 "up_m":1.45,"down_m":0.05,"idle_m":0.25,"speed":1.0,"blind":"idle"}
{"k":"script","turn":0,"seat":1,"alias":"PST-14","piston":13,"source":"llm","latency_ms":3844,
 "note":"Piston 13 is launcher (right third). Ball not visible yet at turn 0. Starting wave mode with full amplitude to tip the ball leftward from the right wall.",
 "say":"Launcher ready - tipping the ball","mode":"wave","trigger_m":1.0,"lead_ticks":3,
 "up_m":1.6,"down_m":0.0,"idle_m":0.0,"speed":1.0,"blind":"hold"}
```

The two champions produced **different** scripts (`up_m` 1.45 vs 1.60, `lead_ticks` 6 vs 3,
`down_m` 0.05 vs 0.0, `blind` `idle` vs `hold`) at a real 3 844 ms LLM latency — this is not a
constant or a scripted stand-in. The 18 filler seats are `source: "scripted"`, which is legitimate
(they are the scripted baselines).

Full results document (from the replay bytes, not from the API):

```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)", … ,"Baseline (18)"],
 "aliases":["PST-02","PST-14", … ],"pistons":[1,13,14,11,17,9,7,2,3,8,16,18,5,19,0,10,4,12,15,6],
 "policyKinds":["llm","llm","scripted", … ],"scores":[96.599, ×20],"win":[true, ×20],
 "sharedScore":96.599,"progress":97.879,"timePenalty":1.28,"delivered":true,"deliveryTicks":279,
 "finalTick":351,"ballStartX":8.4,"ballFinalX":1.2,"bestX":1.2,"bounceBacks":1,"stallTicks":37,
 "phasePermille":559,
 "inPhasePermille":[875,846,321,909,437,780,739,237,903,705,476,307,181,200,692,285,155,488,428,500],
 "touches":[2,1,0,1,0,1,0,0,2,0,0,0,0,1,0,1,0,1,0,0],
 "llmTurns":[1,1,0,…],"fallbackTurns":[0,0,0,…],
 "reason":"complete","endRule":"delivered","seed":450728386}
```

The episode did the thing the game is about: the ball started at `ballStartX 8.4 m`, finished at
`ballFinalX 1.2 m` on the goal wall, `delivered: true` at tick 279, `progress 97.879 %`,
`sharedScore 96.599` — which matches the API's `participant_scores` (96.599) exactly.

Status: TRUE.

> **Material finding — see §Findings F1.** Round **2**'s replay (an *earlier* completed round, and
> the one round where the LLM was reachable for more than one turn) shows both champion seats
> falling back on **every turn after turn 0** with `"per-turn budget exhausted before attempt 1"`.
> Round 4 passes this check only because it ended inside turn 0 (delivered at tick 279 < the 225-tick
> turn length × 2). This is a real coworld defect, not a platform symptom, and it is documented in
> full below rather than buried.

---

## 5. Hosted game log is clean — **TRUE**

```bash
EREQ=ereq_a459bce3-2e83-47be-9d29-040669d181e4
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs4.txt \
     -w 'http %{http_code} bytes %{size_download}\n'
# http 200 bytes 7121
```

The body is python `b'…'` byte-string reprs under `===== container: <name> =====` headers, so it
was **decoded per repr with `ast.literal_eval` before grepping** (playbook §10; a line-based grep
on the raw body undercounts).

```bash
python3 …decode-per-repr… > /tmp/logs4_dec.txt      # 68 decoded lines
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs4_dec.txt || echo CLEAN
```
```
CLEAN
```
Cross-check on the *undecoded* body as well (belt and braces):
```bash
grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs4.txt
# 0
```

Decoded evidence that the LLM actually answered (bedrock-sidecar container, trimmed to the
relevant fields — the full lines are ~700 chars of structured JSON):

```
2026-08-26 05:11:35,629 INFO __main__ bedrock_sidecar_call    … "model":"global.anthropic.claude-haiku-4-5-20251001-v1:0","operation":"InvokeModel"
2026-08-26 05:11:37,505 INFO httpx HTTP Request: POST https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke "HTTP/1.1 200 OK"
2026-08-26 05:11:37,506 INFO __main__ bedrock_sidecar_complete … (ok)
2026-08-26 05:11:37,506 INFO __main__ bedrock_sidecar_usage    …
2026-08-26 05:11:37,507 INFO __main__ bedrock_sidecar_call     … "operation":"InvokeModel"
2026-08-26 05:11:39,376 INFO httpx HTTP Request: POST https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke "HTTP/1.1 200 OK"
2026-08-26 05:11:39,376 INFO __main__ bedrock_sidecar_complete … (ok)
```

Game container tail:

```
===== container: game =====
seed not pinned; randomized
pistonball config: host=0.0.0.0 port=8080 seed=450728386 num_agents=20 maxTicks=1800 turnTicks=225 wallClockBudgetSeconds=660 fastMode=true
starting pistonball on 0.0.0.0:8080
board render caches baked in 144 ms
pistonball llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
player connected: Baseline (16)
…
seat 7 registered: kind=scripted baseline=metronome
Dropped message to disconnected client
Replay written: /tmp/pistonball-replay-1.replay (19876 bytes)
Events written: /coworld/events.json (47 events)
pistonball finished: reason=complete endRule=delivered ticks=351 score=96.599
```

Status: TRUE — zero matches for any of the four patterns on the latest round's log; two Bedrock
`InvokeModel` calls returned `200 OK`.

### What it took to get here (the earlier polls, recorded so the CLEAN is not mistaken for luck)

- **Round 3** (`ereq_d172e3fa-5640-484b-a8b3-f4883acf7a70`, 04:56Z) was **not** clean. Decoded log:
  ```
  pistonball llm: seat 0 attempt 1 failed, falling back if it fails again: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
  pistonball llm: seat 1 attempt 1 failed, falling back if it fails again: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
  pistonball llm: provider throttled with no other candidate; 2 seat(s) fall back for turn 0
  pistonball llm: seat 0 falling back to wavebot (throttled) on turn 0
  pistonball llm: seat 1 falling back to wavebot (throttled) on turn 0
  ```
  Its sidecar line, verbatim and trimmed:
  ```
  2026-08-26 04:56:57,010 WARNING __main__ bedrock_sidecar_complete {… "model":"global.anthropic.claude-haiku-4-5-20251001-v1:0","operation":"InvokeModel","ok":false,"status_code":429,"error_kind":"upstream_client","error_type":"ThrottlingException","message":"Too many tokens per day, please wait before trying again." …}
  ```
- **Documented as platform-wide, per the phase prompt's exception**, by cross-checking *another*
  LLM coworld's latest log in the same window — **fruit-market**
  (`cow_4a33390e-40e5-4bfc-826a-d2987347d8a8`, `ereq_9a9f143f-326d-4f0f-9422-5409ff069fae`):
  ```
  2026-08-26 04:48:09,173 INFO httpx HTTP Request: POST https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke "HTTP/1.1 429 Too Many Requests"
  fruit-market llm: seat 1 attempt 0 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
  ```
  Same message, same model, a different coworld, eight minutes earlier. The `2026-08-24-coins` run
  is Blocked on the identical string (`runs/2026-08-24-coins/STATE.json`.`blocked.error`). So it is
  the shared Bedrock haiku daily-token quota, not a pistonball defect.
- Per `prompts/60-verify.md` §5 I **kept polling inside the 75-minute bound** rather than declaring
  an outage, and the quota window recovered: round 4 (05:11Z) got two `200 OK`s and a CLEAN log.
- **Round 2**'s log could not be read at all — recorded as NOT FETCHED for that round (it is not the
  latest round, so it is not what this check adjudicates):
  ```bash
  curl -sS "$BASE/episode-requests/ereq_82c67bc1-30bd-4fea-823b-69dd723736d0/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}"
  # http 200, 88 bytes:
  Pod logs were not captured: no container logs were readable from pod job-699e7412-88cpr
  ```

---

## 6. The public page uses the static replay path — **TRUE**

**Source used: both.** The raw-HTML grep and the page's own session API.

*(a) Raw HTML — no iframe, as expected for the client-rendered page (playbook §Featured match).*
```bash
curl -sS "https://softmax.com/pistonball" -o /tmp/page2.html -w 'http %{http_code} bytes %{size_download}\n'
# http 200 bytes 585852
grep -o '<iframe[^>]*src="[^"]*"' /tmp/page2.html || echo "NO IFRAME IN RAW HTML (client-rendered)"
# NO IFRAME IN RAW HTML (client-rendered)
```
Treated as *unknown*, not as a failure, exactly as the playbook instructs.

*(b) The featured match, server-rendered into the page's SSR payload at `state.playlist[0]`* —
present, and it is the round-4 episode verified in items 3–5:
```
\"playlist\":[{\"episodeId\":\"b8bcfc51-fb5e-4539-95ff-144bbc8524a6\",
 \"coworldId\":\"cow_58917aec-d633-4f40-89b1-dbf496ddcfe0\",\"coworldName\":\"pistonball\",
 \"coworldVersion\":\"0.1.2\",
 \"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/eab95e2d-e17f-42fc-af3f-03177f8a05d1.replay\",
 \"finishedAt\":\"2026-08-26T05:12:22.151432Z\",\"roundNumber\":4,\"episodeNumber\":1,
 \"code\":\"pistonball.r4.e1\",
 \"matchup\":{\"divisionId\":\"div_de04ec28-cd1a-4349-9667-d34a687735c7\",\"divisionName\":\"Competition\",
  \"first\":{\"rank\":1,\"player_name\":\"daveey\",\"policy_label\":\"pistonball-swell:v2\", …},
  \"second\":{\"rank\":2,\"player_name\":\"daveey-1\",\"policy_label\":\"pistonball-cascade:v2\", …}}}]
```

*(c) The `/coworlds` detail row* — recorded for completeness; its `featured_match` is `null`
**platform-wide** (lighthouse run, 2026-08-22), so it is not evidence either way:
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)[]|select(.name=="pistonball")|{id,canonical,replay_viewer,featured_match}'
```
```json
{"id":"cow_58917aec-d633-4f40-89b1-dbf496ddcfe0","canonical":true,"replay_viewer":null,"featured_match":null}
```

*(d) The iframe `src` — the call the page's own JS makes:*
```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_58917aec-d633-4f40-89b1-dbf496ddcfe0",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/eab95e2d-e17f-42fc-af3f-03177f8a05d1.replay"}'
```
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_58917aec-d633-4f40-89b1-dbf496ddcfe0/sha256%3Ab041d20354aeb86ea9b0d8d8a523652c0e6f3c5813bff72c68cca97b487f77f3/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Feab95e2d-e17f-42fc-af3f-03177f8a05d1.replay&v=2",
 "ready":true}
```

Status: TRUE — the src is
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`, `ready: true`, and the
`<sha>` is the coworld's manifest hash
`sha256:b041d20354aeb86ea9b0d8d8a523652c0e6f3c5813bff72c68cca97b487f77f3`, which matches
`STATE.coworld.manifest_sha` exactly. **No `/client/replay` pod URL anywhere.** A featured match is
present, with both ranked players in the matchup.

---

## 7. Certification declared the static bundle — **TRUE**

**Source: the committed `runs/2026-08-25-pistonball/release-result.json`** (the artifact this run's
phase 40 downloaded and committed from release run `32930394604`). It was present, so the
`gh run download` fallback was **not** used, and `/tmp` was never consulted.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-25-pistonball/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: TRUE — the output contains `Replay liveness: skipped (static replay bundle declared`.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

*(a) Dispatch.* I dispatched `viewer-check.yml` against the **exact** iframe `src` from item 6:

```bash
SRC=$(jq -r .viewer_url /tmp/session2.json)     # the item-6 URL, ?replay= and all
date -u +%FT%TZ            # 2026-08-26T05:16:10Z   <- dispatch time, recorded BEFORE dispatching
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
sleep 15
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:3][]|[.databaseId,.createdAt,.status]|@tsv'
```
```
32933394784	2026-08-26T05:16:12Z	in_progress      <- created AFTER 05:16:10Z: this is mine
32931950773	2026-08-26T04:53:58Z	completed        (another run's)
32931770282	2026-08-26T04:51:09Z	completed        (my earlier round-2 probe, superseded)
```
The run was found by sorting on `createdAt` and matching against the recorded dispatch time — never
by taking "the latest run" blind.

```bash
gh run watch 32933394784 -R Metta-AI/coworld-builder --exit-status   # exit 0
gh run view  32933394784 -R Metta-AI/coworld-builder --json status,conclusion
# {"conclusion":"success","status":"completed"}
gh run download 32933394784 -R Metta-AI/coworld-builder -n viewer-check \
  -D runs/2026-08-25-pistonball/viewer-check
```
Committed as `runs/2026-08-25-pistonball/viewer-check/` (`viewer-smoke.json`, `viewer-smoke.png`,
`smoke-stdout.txt`, `smoke-stderr.txt`).

*(b) The readouts, verbatim.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-25-pistonball/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":3166,"clock":"1:15 TIME LEFT","scorebug":"0% THE BANK - 20 cogs SCORE 0.0 2.0% OF THE WAY · 0 BOUNCE-BACKS 1:15 TIME LEFT GOAL WALL 50% START","feed_lines":0}
```
```bash
jq -c '.signals' …/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```
```bash
jq -r '.failure // "no failure"' …/viewer-smoke.json
# no failure
jq -c '{status, loading_text, canvas_text, console_tail}' …/viewer-smoke.json
# {"status":"OPEN","loading_text":null,
#  "canvas_text":{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]},
#  "console_tail":[]}
```

**The three scrub readouts:**

| `#scrub` position | clock readout |
|---|---|
| 0 % | `1:15 TIME LEFT` |
| 50 % | `1:11 TIME LEFT` |
| 100 % | `FINAL GAME OVER` |

All three **differ**. `#scrub` exists and responded (no `"(no #scrub…)"` sentinel).

**Item 8 gate:** `loaded: true` (via `data-replay-loaded="true"`) ✔ **and** three differing clock
readouts ✔ → **TRUE**. The viewer drew its first frame in **3 166 ms**, `failure` is null, the
console tail is empty and no text was drawn outside the canvas.

*(c) What the viewer was asked to draw — ordered excerpts of the replay record.*
(`.events[]` in the phase prompt's command is a JSON-replay shape; pistonball's record vocabulary is
`register` / `script` / input-change / tick-hash / `result`, dumped in order below. Timestamps are
the record's millisecond stamp.)

Early — joins, registration, and the first decision turn:
```
3291	join	  daveey slot=0
3291	join	  daveey-1 slot=1
3291	register  seat=0 alias=PST-02 piston=1  kind=llm
3291	register  seat=1 alias=PST-14 piston=13 kind=llm
3291	register  seat=2 alias=PST-15 piston=14 kind=scripted
5291	join	  Baseline (3) slot=4 … Baseline (18) slot=19
6291	script	  seat=0 src=llm      mode=wave   up_m=1.45 say='PST-02 ready: wave mode, eyes open'
6291	script	  seat=1 src=llm      mode=wave   up_m=1.6  say='Launcher ready - tipping the ball'
6291	script	  seat=2 src=scripted mode=ripple up_m=1.2  say='keeping the beat'
6291	input	  seat=0 cmd=254        <- champion seat 0 commands its piston up
6291	input	  seat=14 cmd=228
```
Middle — the bank working, seat by seat, command bytes changing every few tens of ms:
```
8250	input	seat=7  cmd=228
8291	input	seat=15 cmd=29
8333	input	seat=15 cmd=127
8416	input	seat=16 cmd=218
8458	input	seat=16 cmd=228
8458	input	seat=5  cmd=254
8500	input	seat=3  cmd=0
8500	input	seat=17 cmd=52
```
Late — the whole bank settling to neutral (cmd 127) after delivery, then the result frame:
```
11625	input	seat=0 cmd=127
11625	input	seat=8 cmd=127
11625	input	seat=16 cmd=127
…      (13 seats settle in the same millisecond)
14625	result	{"names":["daveey","daveey-1","Baseline",…],"scores":[96.599 ×20],"delivered":true,
	         "deliveryTicks":279,"finalTick":351,"progress":97.879,"reason":"complete","endRule":"delivered"}
```
Integrity chain: 351 tick hashes, all advancing —
`tick 1 = bfdde2ed43e3b500`, `tick 175 = 8a9ad18f5cc91e6e`, `tick 351 = d0956a8269652186`. 255 input
change records across the episode. The world genuinely moved.

### Spectator-judgment paragraph

**It is legible, and it does show the game.** `viewer-smoke.png` (committed alongside this file) was
taken at the 100 % scrub position, so it shows the machine-shop side view with the **endcard**
overlaid. The chrome is the starter's, item for item: a top **transport/scorebug strip** carrying a
phase chip (`56%`), the score in green (`96.6 SCORE`), the team label `THE BANK - 20 cogs`, the
subline `100.0% OF THE WAY · 1 BOUNCE-BACKS`, a **momentum micro-graph** of vertical bars, a big
`FINAL / GAME OVER` clock block, and the **journey bar** running `GOAL WALL — 50% — START` with the
ball puck sitting hard against the **START** end (right) and the filled portion showing how far the
ball travelled; a bottom **transport strip** with restart / step-back / play / `+5s` / step-forward /
loop / fast-forward, a `spoilers` toggle, the frame counter `200 / 200`, a `BANK WINS` verdict, and
`1×…16×` speed buttons; and beneath it the **scrubber with a momentum/journey graph** — a white
trace that climbs left-to-right (progress accumulating) with coloured **beat markers** (an orange
launch at the far left, a red bounce-back near the middle, a green delivery just after it, and the
end cap). Behind the dimmed overlay the arena itself is readable: piston columns of varying height
across the floor, hazard-striped left wall, and the ball as a large dark disc resting at the far
left — on the goal wall, which is exactly what `ballFinalX 1.2` / `delivered: true` says happened.
The endcard reads `BALL ON THE GOAL WALL`, "One score for twenty pistons. The bank spent 56% of its
engaged time on the right side of the ball.", `THE BANK / 96.6 SHARED SCORE`, and a 20-row table of
`POLICY · PISTON · IN PHASE · TOUCHES · LLM/FB` in which **`daveey` (piston 2, 88 % in phase, 2
touches) and `daveey-1` (piston 14, 85 % in phase, 1 touch)** sit third and fourth among twenty,
with the eighteen `Baseline (N)` fillers around them — the two name spaces (`PST-nn` in-game, real
names spectator-side) work as designed. The picture is **not** empty, **not** frozen (the clock
advances 1:15 → 1:11 → FINAL across the three scrub positions, and the 351-tick hash chain and 255
input-change records in the replay agree that the world was moving) and **not** unreadable: the
smoke run measured 0 canvas text draws outside the canvas and 0 ellipsized. It **looks like the
starter's chrome** — the same transport strip, scrubber-with-momentum-graph, scorebug and endcard
family as paintbot/raid/hive, retargeted rather than rewritten; this is not the cogame-gridlock
"different product sharing only the ids" failure. Two legibility defects are visible in the render
and are recorded as findings F2 and F3 below. `feed_lines: 0` is expected here and not a defect: the
say-feed is a live-broadcast element and the screenshot is on the endcard, with the arena dimmed.

---

## Findings (not check failures — recorded for the judge and phase 30)

**F1 — the per-turn budget clock is sampled before the inter-batch rate-floor sleep, so every turn
after turn 0 falls back.** Round 2's replay
(`ereq_82c67bc1-30bd-4fea-823b-69dd723736d0`, replay `699e7412-3900-4053-8b67-e62612bda161`) is the
proof, because it is the only round so far that lasted more than one decision turn *and* had a
reachable LLM:

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/699e7412-3900-4053-8b67-e62612bda161.replay" \
     -o /tmp/ep2.replay -w 'http %{http_code} bytes %{size_download}\n'
# http 200 bytes 96243
python3 /workspace/cogame-pistonball/tools/replay_summary.py /tmp/ep2.replay > /tmp/ep2.json
jq -c '[.scripts[]|select(.seat==0 or .seat==1)]|group_by(.source)|map({(.[0].source):length})|add' /tmp/ep2.json
# {"fallback":14,"llm":2}
jq -r '.scripts[]|select(.seat==0 or .seat==1)|[.turn,.seat,.source,.latency_ms]|@tsv' /tmp/ep2.json
# 0	0	llm       4097
# 0	1	llm       4097
# 1	0	fallback  0
# 1	1	fallback  0
# …  turns 2,3,4,5,6,7 identical for both seats
jq -c '{budgetGuards, fallbacks}' /tmp/ep2.json
# {"budgetGuards":0,"fallbacks":28}
jq -c '{progress:.results.progress, delivered:.results.delivered, stallTicks:.results.stallTicks,
        finalTick:.results.finalTick, sharedScore:.results.sharedScore,
        reason:.results.reason, endRule:.results.endRule}' /tmp/ep2.json
# {"progress":0.0,"delivered":false,"stallTicks":1678,"finalTick":1872,"sharedScore":-16.78,
#  "reason":"complete","endRule":"out_of_time"}
```
The fallback records name the cause exactly:
```json
{"k":"fallback","turn":1,"seat":0,"attempt":1,"cause":"timeout","detail":"per-turn budget exhausted before attempt 1"}
{"k":"fallback","turn":1,"seat":1,"attempt":1,"cause":"timeout","detail":"per-turn budget exhausted before attempt 1"}
{"k":"fallback","turn":1,"seat":0,"attempt":2,"cause":"parse_error","detail":"seat fell back to the wavebot script"}
```
(14 `timeout` + 14 `parse_error` records; `budget_guard` count is 0, so the guard did not cause it.)

Reading the source that emits it — `/workspace/cogame-pistonball/src/pistonball/decide.nim`:
```nim
326:    turnStart = getMonoTime()                    # sampled at the TOP of the turn
…
368:  if open.len > 0 and engine.batchStarted and sim.config.minBatchSpacingMs > 0:
371:      sleep(min(sim.config.minBatchSpacingMs, sim.config.minBatchSpacingMs - since))
…
383:    if getMonoTime() - turnStart >= budget:       # budget = turnBudgetMs = 20 000
387:          "per-turn budget exhausted before attempt " & $(attempt + 1)))
```
`minBatchSpacingMs` is 45 000 and `turnBudgetMs` is 20 000, and `turnStart` is taken **before** the
45 s rate-floor sleep. So on every turn where `batchStarted` is already true — i.e. every turn after
turn 0 — the 20 s budget is provably exhausted the moment the sleep returns, and both champion seats
fall back to wavebot without ever issuing a request. Round 2's evidence is exactly that pattern:
one real LLM turn at 4 097 ms, then seven turns of zero-latency fallbacks.

Consequence: **in any episode longer than one decision turn, the champions are LLM for turn 0 and
scripted-wavebot thereafter.** Round 4 passes check 4 only because it delivered inside turn 0.
Round 2's episode, which ran the full 1 800 ticks on wavebot fallbacks, scored `-16.78` with
`progress 0.0`, `delivered false`, `stallTicks 1678/1872` — a stalled ball, versus 96.6 and a
delivery in rounds 3 and 4. This is a coworld-side defect (a `turnStart` that should be re-sampled
after the rate-floor sleep, or a `turnBudgetMs` that must exceed `minBatchSpacingMs`), not a
platform symptom. I did not change any code; reporting only.

**F2 — the endcard's `LLM/FB` column reads `0/0` for the LLM seats.** In the committed
`viewer-smoke.png`, `daveey` and `daveey-1` both show `0/0` under `LLM/FB`, while the same episode's
results document says `llmTurns: [1,1]` and `fallbackTurns: [0,0]`. The column under-reports the one
number a spectator would use to tell an LLM seat from a baseline.

**F3 — the endcard's `TOUCHES` and `LLM/FB` column headers collide.** They overprint in both columns
of the two-column table (rendering as `TOUCHEŁŁM/FB`). Cosmetic, but it is on the endcard, which is
the most-looked-at frame.

Both F2 and F3 are phase-30 item-14 legibility findings on a viewer that otherwise renders, scrubs
and reads correctly; neither falsifies check 8's gate.

---

## Summary table

| # | Item | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | **TRUE** — rounds 2, 3, 4 completed; round 1 `failed` (error quoted) |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey + daveey-1, `rounds_played` 3 each; fillers absent |
| 3 | Latest round's episode request completed with a replay | **TRUE** — `ereq_a459bce3…` completed, `replay_url` present, both champions seated |
| 4 | Replay bytes valid, protocol match, champions not falling back | **TRUE** — `pistonball/v1`, `complete`/`delivered`, champion seats 2 llm / 0 fallback (see F1) |
| 5 | Hosted game log clean | **TRUE** — 0 matches on the latest round; earlier 429 documented as platform-wide and waited out |
| 6 | Public page uses the **static** replay path | **TRUE** — `…/replays/static/<cow_id>/<manifest sha>/index.html?replay=…`, `ready:true`, featured match present |
| 7 | Certification declared the static bundle | **TRUE** — `Replay liveness: skipped (static replay bundle declared…` from the committed `release-result.json` |
| 8 | Viewer executed and judged | **TRUE** — `loaded: true` in 3 166 ms, three differing clock readouts, screenshot shows the game (see F2, F3) |

---

## Addendum (coordinator, 2026-08-26T06:11Z): F1 fixed, re-released, proven in production

The §Findings F1 defect (turn budget consumed by the rate-floor sleep; champions fell back on every turn > 0) was fixed before adjudication:

- Fix commits on `Metta-AI/cogame-pistonball` main: `06bd3f7` (F1, decide.nim turnStart re-sampled after the inter-batch sleep + engine test with spacing 400 > budget 200), `87ba292` (F2, replay recounts llmTurns/fallbackTurns for the endcard), `30964b3` (F3, endcard header fit, browser-measured). CI green: run 32934920010 at 30964b3.
- Re-released as **0.1.3**: release run 32936048068, `ok:true, canonical:true, certify.ok:true, secret_put:true`, `Replay liveness: skipped (static replay bundle declared...)`, new `cow_id cow_768730a3-282a-4d75-9cff-01eea560e260`, `manifest_sha sha256:91c1207c7f679847f054a230f0d44e58aad9f52d927f8cc5678e3f619aa33915`. `runs/2026-08-25-pistonball/release-result.json` overwritten to match. League seats stay on the v2 policy versions (player protocol unchanged; the fix is in the game image).
- Post-fix round **8** (`round_638df556-805a-4ffd-ab72-074e3e2a4a57`, triggered 06:05Z after 0.1.3 went canonical, completed 06:09Z), episode `ereq_f2d4d58a-ef89-47e5-a83f-4c855ac3329d`, replay `https://softmax-public.s3.amazonaws.com/replays/20418470-73ca-48e7-9a22-fabfec4f8f7d.replay`:

```
$ python3 tools/replay_summary.py /tmp/ep8.replay > /tmp/ep8.json   # strict UTF-8 JSON: ok
{"reason":"complete","endRule":"delivered","delivered":true,"sharedScore":91.212,
 "llmTurns":[0,4,4,0,...],"fallbacks":0}
llm scripts by turn: turn 0: 2 llm, turn 1: 2 llm, turn 2: 2 llm, turn 3: 2 llm
fallback script records: 0
```

Both champion seats received LLM scripts on **every turn the episode lasted (0–3; delivered during turn 3)** with **zero fallbacks** — the F1 failure mode (`per-turn budget exhausted before attempt 1`) is absent. Check 4's "champion decisions non-scripted, not all fallbacks" now holds beyond the turn-0-only case; rounds 2–7 predate the fix and their fallback-heavy episodes are the F1 evidence, not the shipped behaviour.

## Addendum 2 (coordinator, 2026-08-26T06:22Z): check 8 re-executed against the shipped 0.1.3 bundle

Per verify-verdict.md's one blocker: `viewer-check.yml` re-dispatched against the 0.1.3 iframe src (session POST for cow_768730a3 + the round-8 replay → `ready:true`, static path with sha256%3A91c1207c…). Run **32937649794**, conclusion success; artifact committed at `runs/2026-08-25-pistonball/viewer-check-013/`.

```
{"loaded":true,"ms":3109,"clock":"1:15 TIME LEFT","feed_lines":0}
scrub: 0% "1:15 TIME LEFT" / 50% "0:59 TIME LEFT" / 100% "FINAL GAME OVER"   (three differing clocks)
failure: none
```

Screenshot (viewer-check-013/viewer-smoke.png): starter chrome intact (scorebug + journey bar + transport + scrubber with beat markers + momentum trace), endcard "BALL ON THE GOAL WALL", 91.2 SHARED SCORE, 20-row table where **daveey (piston 12) and daveey-1 (piston 4) both read `4/0` in LLM/FB** (F2 fixed: non-zero champion LLM counts) and the TOUCHES / LLM/FB headers sit clearly in their own columns (F3 fixed). SPEC item 8's evidence now covers the shipped bundle.
