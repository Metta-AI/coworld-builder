# VERIFY — ledger   (2026-08-24T00:07Z)

Verdict: **all-true** (8/8)

Run: `2026-08-23-ledger` · slug `ledger` · version `0.1.0`
`$COW` = `cow_7754c862-182c-4ec9-bca6-4311d36f2be4`
`$L` = `league_1ad5ff34-7cf7-4940-9ef2-b7690a4bf5aa`
`$D` = `div_eb565e12-2c31-4797-bb55-9e4678f54a86`

Headers sent on every Observatory call (values never printed):
`Authorization: Bearer $SOFTMAX_TOKEN`, `User-Agent: coworld-builder/1.0`; plus
`X-Use-Elevated-Privileges: true` on the artifacts/logs read (check 5).
`BASE=https://softmax.com/api/observatory/v2`.

All evidence below was fetched fresh during this phase-60 pass (2026-08-23T23:39Z →
2026-08-24T00:07Z), except the two documented exceptions: check 7 reads the committed
`release-result.json`, and check 8 reads the artifact of a `viewer-check.yml` run dispatched
during this pass.

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

Fillers were registered before the manual trigger; `runs/2026-08-23-ledger/log.md:47` records it:

```
2026-08-23T23:38:06Z 50 fillers POST 200: mirror+shark registered (neither champion); rounds-paused=false; trigger-round OK
```

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}"
```
HTTP 200, fetched 2026-08-24T00:01:20Z:
```json
{
  "count_completed": 2,
  "entries": [
    {
      "id": "round_9010fafa-8aca-4ea7-b61a-653628f0cf32",
      "round_number": 3,
      "status": "completed",
      "error": null,
      "created_at": "2026-08-23T23:52:03.101650Z",
      "updated_at": null,
      "completed_at": "2026-08-23T23:58:10.183081Z"
    },
    {
      "id": "round_3b6b2b34-ff6c-4abc-a039-322caa46c841",
      "round_number": 2,
      "status": "completed",
      "error": null,
      "created_at": "2026-08-23T23:37:02.314170Z",
      "updated_at": null,
      "completed_at": "2026-08-23T23:42:29.803785Z"
    },
    {
      "id": "round_2a117322-da9e-4f80-9949-f9ced8cfe7fa",
      "round_number": 1,
      "status": "failed",
      "error": "Temporal RoundWorkflow failed before settling the round.",
      "created_at": "2026-08-23T23:37:00.425160Z",
      "updated_at": null,
      "completed_at": "2026-08-23T23:37:00.627120Z"
    }
  ]
}
```

Round 1's `error` verbatim: `Temporal RoundWorkflow failed before settling the round.` — it was
auto-scheduled before any filler existed (the documented pre-filler `trigger-round` failure mode,
`playbooks/observatory-api.md` §6). It does not count; its supersession was logged in phase 50.

Independent proof that rounds 2 and 3 ran **with** the fillers seated (not merely after a
wall-clock stamp) — both episodes seated six `is_filler: true` seats:

```bash
curl -sS "$BASE/episode-requests?round_id=round_3b6b2b34-ff6c-4abc-a039-322caa46c841&limit=20" "${AUTH[@]}"
curl -sS "$BASE/episode-requests/ereq_d4d235d5-0497-4da7-92b1-d63b69660c41" "${AUTH[@]}"
```
```json
{"status":"completed","replay_url":"https://softmax-public.s3.amazonaws.com/replays/7e1a2c93-cf5f-4d62-8180-b53f80401703.replay",
 "seats":[{"p":0,"policy":"ledger-reputation","player":"daveey","filler":false},
          {"p":1,"policy":"ledger-broker","player":"daveey-1","filler":false},
          {"p":2,"policy":"ledger-shark","player":"daveey","filler":true},
          {"p":3,"policy":"ledger-mirror","player":"daveey","filler":true},
          {"p":4,"policy":"ledger-mirror","player":"daveey","filler":true},
          {"p":5,"policy":"ledger-shark","player":"daveey","filler":true},
          {"p":6,"policy":"ledger-shark","player":"daveey","filler":true},
          {"p":7,"policy":"ledger-shark","player":"daveey","filler":true}]}
```
(round 3's equivalent is pasted under check 3.)

**Status: TRUE** — rounds **2** and **3** are `completed` (at 2026-08-23T23:42:29.803785Z and
2026-08-23T23:58:10.183081Z), both `round_number ≥ 2`, i.e. after the fillers POST at
2026-08-23T23:38:06Z, and both seated the registered fillers.

---

## 2. Both champions ranked, fillers absent/Baseline — TRUE

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
HTTP 200, fetched 2026-08-24T00:01:40Z:
```
1	daveey	ledger-reputation:v1	1001.4695015289755	2	1.0
2	daveey-1	ledger-broker:v1	998.5304984710245	2	1.0
```

Raw body (bare list, not `.entries`):
```json
[{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1001.4695015289755,"score_label":"Elo","score_value_type":"integer","rounds_played":2,"episode_wins":1.0,"episodes_played":null,"win_rate":0.5,"policy_label":"ledger-reputation:v1","recent_rounds":null},
 {"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":998.5304984710245,"score_label":"Elo","score_value_type":"integer","rounds_played":2,"episode_wins":1.0,"episodes_played":null,"win_rate":0.5,"policy_label":"ledger-broker:v1","recent_rounds":null}]
```

**Status: TRUE** — `daveey` (`ledger-reputation:v1`, rounds_played 2) and `daveey-1`
(`ledger-broker:v1`, rounds_played 2) are both ranked; the list has exactly two rows, so
`ledger-mirror:v1` and `ledger-shark:v1` are **absent** from the leaderboard.

---

## 3. Latest completed round's episode request completed with a replay — TRUE

Latest completed round = `round_9010fafa-8aca-4ea7-b61a-653628f0cf32` (round_number 3).

```bash
curl -sS "$BASE/episode-requests?round_id=round_9010fafa-8aca-4ea7-b61a-653628f0cf32&limit=20" "${AUTH[@]}" \
 | jq -r '.entries[]|[.id,.status]|@tsv'
```
HTTP 200:
```
ereq_e23450b7-fb5c-4a9e-818b-f3f5d3f06f9e	completed
```

```bash
curl -sS "$BASE/episode-requests/ereq_e23450b7-fb5c-4a9e-818b-f3f5d3f06f9e" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```
HTTP 200 (participants trimmed to the identifying fields; scores in full):
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/316d64ba-52ed-466b-bea3-a364c679727b.replay",
  "participants": [
    {"position": 0, "policy_name": "ledger-reputation", "player_name": "daveey",   "is_filler": false},
    {"position": 1, "policy_name": "ledger-broker",     "player_name": "daveey-1", "is_filler": false},
    {"position": 2, "policy_name": "ledger-mirror",     "player_name": "daveey",   "is_filler": true},
    {"position": 3, "policy_name": "ledger-mirror",     "player_name": "daveey",   "is_filler": true},
    {"position": 4, "policy_name": "ledger-mirror",     "player_name": "daveey",   "is_filler": true},
    {"position": 5, "policy_name": "ledger-shark",      "player_name": "daveey",   "is_filler": true},
    {"position": 6, "policy_name": "ledger-mirror",     "player_name": "daveey",   "is_filler": true},
    {"position": 7, "policy_name": "ledger-shark",      "player_name": "daveey",   "is_filler": true}
  ],
  "participant_scores": [
    {"position": 0, "score": 6.0}, {"position": 1, "score": 5.5},
    {"position": 2, "score": 6.0}, {"position": 3, "score": 4.0},
    {"position": 4, "score": 6.0}, {"position": 5, "score": 2.0},
    {"position": 6, "score": 2.0}, {"position": 7, "score": 2.0}
  ]
}
```

The champion seats render as `daveey` / `daveey-1` in the replay's own name table and the six
filler seats as `Baseline (N)` — from `/tmp/ep.replay` (check 4):
```
0=daveey 1=daveey-1 2=Baseline 3=Baseline (2) 4=Baseline (3) 5=Baseline (4) 6=Baseline (5) 7=Baseline (6)
```

**Status: TRUE** — `status == "completed"`, `replay_url` non-null
(`https://softmax-public.s3.amazonaws.com/replays/316d64ba-52ed-466b-bea3-a364c679727b.replay`),
participants name `daveey` (position 0, `is_filler: false`) and `daveey-1` (position 1,
`is_filler: false`), fillers labelled `Baseline (N)`.

---

## 4. Replay bytes are valid and show the game — TRUE

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/316d64ba-52ed-466b-bea3-a364c679727b.replay" -o /tmp/ep.replay
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
python3 -c "d=open('/tmp/ep.replay','rb').read(); d.decode('utf-8'); print('python strict utf-8 decode: ok', len(d),'bytes')"
jq -r '.protocol, .results.reason' /tmp/ep.replay
```
```
HTTP 200 bytes=28922
strict UTF-8 JSON: ok
python strict utf-8 decode: ok 28922 bytes
ledger.replay.v1
complete
```

`protocol` matches the manifest / design note (`design.md` §"Replay payload (`ledger.replay.v1`)").
`results.reason` is `complete`, so the `deadline` exception the design note declares acceptable
(`design.md`: "A `deadline` ending is a legitimate, scored episode, and phase 60 accepts it") is
**not needed here**.

**Decision-event vocabulary note.** The prompt's literal probes return 0 for this game, because
in `ledger` a decision is a `meeting` event keyed `kind` (not `type`), and the scripted marker is
`scriptedA`/`scriptedB` (not `fallback`) — `design.md` §"Event vocabulary". Both forms are shown:

```bash
jq -r '[.events[]|select(.type=="decision")]|length' /tmp/ep.replay   # -> 0  (wrong key for this game)
jq -r '[.events[]|select(.fallback==true)]|length'   /tmp/ep.replay   # -> 0  (wrong key for this game)
jq -r '[.events[]|.kind]|group_by(.)|map("\(.[0])=\(length)")|join(" ")' /tmp/ep.replay
```
```
0
0
end=1 gossip=26 meeting=56 round=14 start=1
```

Champion-seat decisions, counted the way this game records them:
```bash
jq -c '[.events[]|select(.kind=="meeting")]|{champ0_meetings:..., champ0_scripted:..., champ1_meetings:..., champ1_scripted:..., total_seat_decisions:..., total_scripted_flags:...}' /tmp/ep.replay
```
```json
{"champ0_meetings":14,"champ0_scripted":0,"champ1_meetings":14,"champ1_scripted":0,
 "total_seat_decisions":112,"total_scripted_flags":84}
```

Reading: 56 meetings × 2 seats = 112 seat-decisions. 84 carry `scripted: true` — exactly the six
registered-scripted filler seats × 14 rounds (6 × 14 = 84). The two champion seats made
**28 of 28 decisions live, zero scripted, zero fallbacks.** Reconciled with check 5's authoritative
source: the hosted game log contains **no** `ledger: seat N falling back to scripted decision`
line, so all 84 scripted flags are registered-scripted baselines and none is an LLM fallback.

Champion decisions are non-trivial — verbatim `memoA`/`memoB` off champion meetings:
```json
{"kind":"meeting","round":1,"pair":0,"seat":0,"other":1,"game":"trust","moveA":5,"moveB":50,"payA":6,"payB":7,"scriptedA":false,"scriptedB":false,
 "memoA":"R1 Flywheel (DILEMMA): I cooperated, they defected. Got 0, they got 10. Pure exploitation—marked as untrustworthy.\n\nR2 Gasket (TRUST): Sending 5 coins. Gasket's median is 5.0 with kind=1, showing cooperative tendency. In R1 ULTIMATUM as responder they accepted floor 4 (got 5, responder got 7)—fair and reasonable. Return % unknown but their profile suggests reciprocal play. Betting on cooperation.",
 "memoB":"R1: Ratchet (ULTIMATUM responder) - offered 7/12, generous. Accepted. R2: Widget (TRUST trustee) - opening, returning 50% per guidance to advertise reliability. Track: Widget 0.0 median (defected in R1 DILEMMA vs Flywheel). Flywheel/Sprocket both 10.0 median, harsh reputation - likely defectors. …"}
```

`.results` in full:
```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)","Baseline (5)","Baseline (6)"],
 "scores":[6.0,5.5,6.0,4.0,6.0,2.0,2.0,2.0],
 "mean":[5.214285714285714,4.0,4.785714285714286,4.071428571428571,4.214285714285714,2.142857142857143,3.4285714285714284,3.2857142857142856],
 "total":[73,56,67,57,59,30,48,46],"meetings":[14,14,14,14,14,14,14,14],
 "kind":[10,9,9,9,9,0,8,2],"harsh":[4,5,5,5,5,14,6,12],
 "rounds":14,"maxRounds":14,"ringPairs":0,"reason":"complete"}
```

**Status: TRUE** — 28 922 bytes of strict UTF-8 JSON (both `jq -e` and python's strict decoder),
`protocol: ledger.replay.v1`, `results.reason: "complete"`, 14 full rounds, and the champion seats'
28 decisions are all live with substantive reputation reasoning.

---

## 5. Hosted game log is clean — TRUE

```bash
curl -sS "$BASE/episode-requests/ereq_e23450b7-fb5c-4a9e-818b-f3f5d3f06f9e/artifacts/logs" \
  "${AUTH[@]}" "${ELEV[@]}" -o /tmp/v/logs.raw
# decode the python b'…' byte-string reprs before grepping (playbook §10)
python3 …ast.literal_eval per repr… > /tmp/v/logs.txt
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/v/logs.txt || echo CLEAN
```
```
HTTP 200 bytes=64546
raw bytes: 64546 decoded chars: 64306 decoded lines: 232
containers: ['coworld-init-config', 'bedrock-sidecar', 'game', 'worker']
--- grep on DECODED:
CLEAN
```

Corroborating: every Bedrock sidecar call in the decoded log reports `"ok":true`,
`"status_code":200`, `"error_kind":null`, e.g.
```
2026-08-23 23:52:24,300 INFO __main__ bedrock_sidecar_complete {"episode_request_id":"e23450b7-fb5c-4a9e-818b-f3f5d3f06f9e","job_request_id":"316d64ba-52ed-466b-bea3-a364c679727b","role":"game","model":"global.anthropic.claude-haiku-4-5-20251001-v1:0","operation":"InvokeModel","ok":true,"status_code":200,"latency_ms":1570.85,"error_kind":null,"error_type":null,"message":null,"request_id":"db917d4d-cd70-43a3-813e-02e131035ca6","cache_strategy":"sidecar_v1","cache_decision":"first_sighting"}
```
and the `game` container ends cleanly:
```
ledger: round 14 Flywheel / Widget ULTIMATUM: offered 1 / floor 3 (+0 / +0)
Dropped message to disconnected client            (×6)
ledger: writing results and replay
ledger: artifacts written; serving for 20s before exit
ledger: episode complete, shutting down
```

No `ledger: seat N falling back to scripted decision` line exists — this is the authoritative
fallback count for the LLM seats and it is **zero**, matching check 4's `champ0_scripted: 0`
/ `champ1_scripted: 0`.

**Status: TRUE** — `CLEAN`; zero matches for `falling back|LLM provider is unavailable|cut off at
max_tokens|rejected` in the decoded 64 306-char log. No documented exception invoked.

---

## 6. The public page uses the static replay path — TRUE

**Source used: (b) the API the page reads** — the raw-HTML grep found nothing, which per
`prompts/60-verify.md` check 6 is *unknown*, not a false negative:

```bash
curl -sS "https://softmax.com/ledger" | grep -o '<iframe[^>]*src="[^"]*"'
```
```
HTTP 200 bytes=427685
(raw-HTML grep: NO MATCH — page is client-rendered)
```

The featured match **is** server-rendered into the SSR payload at `state.playlist[0]`
(un-escaped, trimmed):
```json
"playlist":[{"episodeId":"72fafcdc-b07e-4a77-9ce2-8b155107a415",
 "coworldId":"cow_7754c862-182c-4ec9-bca6-4311d36f2be4","coworldName":"ledger","coworldVersion":"0.1.0",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/316d64ba-52ed-466b-bea3-a364c679727b.replay",
 "finishedAt":"2026-08-23T23:58:05.421523Z","roundNumber":3,"episodeNumber":1,"code":"ledger.r3.e1",
 "matchup":{"divisionId":"div_eb565e12-2c31-4797-bb55-9e4678f54a86","divisionName":"Competition",
  "first":{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
           "score":1001.4695015289755,"score_label":"Elo","rounds_played":2,"episode_wins":1,
           "win_rate":0.5,"policy_label":"ledger-reputation:v1"},"second":{"rank":2,"player_id":"ply_bac48e…
```

For completeness, `/coworlds` (the other fallback) reports `featured_match: null`, which the
playbook records as the platform-wide behaviour and therefore not evidence either way:
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" | jq -r '(if type=="array" then . else .entries end)[]|select(.name=="ledger")|{id,name,canonical,replay_viewer,featured_match}'
```
```json
{"id":"cow_7754c862-182c-4ec9-bca6-4311d36f2be4","name":"ledger","canonical":true,"replay_viewer":null,"featured_match":null}
```

The iframe `src` itself, from the call the page's own JS makes:
```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_7754c862-182c-4ec9-bca6-4311d36f2be4","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/316d64ba-52ed-466b-bea3-a364c679727b.replay"}'
```
HTTP 200:
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_7754c862-182c-4ec9-bca6-4311d36f2be4/sha256%3A655ad0565d05b0728371a7808baa372ecac282849127cb3e3bfbb3cdc87652b8/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F316d64ba-52ed-466b-bea3-a364c679727b.replay&v=2",
  "ready": true
}
```
```bash
curl -sS -o /dev/null -w "iframe src: HTTP %{http_code} type=%{content_type}\n" "$SRC"
```
```
iframe src HEAD: HTTP 200 type=text/html; charset=utf-8
```

**Status: TRUE** — a featured match is present (`ledger.r3.e1`, daveey vs daveey-1), and the
iframe `src` is the **static** route
`…/v2/coworlds/replays/static/cow_7754c862-.../sha256%3A655ad056…/index.html?replay=<s3 url>`
with `ready: true`. The `<sha>` is the coworld manifest hash
`sha256:655ad0565d05b0728371a7808baa372ecac282849127cb3e3bfbb3cdc87652b8`, matching
`STATE.coworld.manifest_sha`. No `/client/replay` pod URL anywhere.

---

## 7. Certification declared the static bundle — TRUE

**Source read: the committed `runs/2026-08-23-ledger/release-result.json`** (the copy phase 40
downloaded from release run `32673657033`). It was present; no re-download was needed.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-23-ledger/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Surrounding fields from the same file:
```json
{"ok": true, "canonical": true, "certify_ok": true}
```

**Status: TRUE** — the output contains
`Replay liveness: skipped (static replay bundle declared`, read from the committed
`release-result.json`.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — TRUE

*(a) Dispatch.* Against the exact iframe `src` from check 6:
```bash
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder \
  -f url='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_7754c862-182c-4ec9-bca6-4311d36f2be4/sha256%3A655ad0565d05b0728371a7808baa372ecac282849127cb3e3bfbb3cdc87652b8/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F316d64ba-52ed-466b-bea3-a364c679727b.replay&v=2' \
  -f timeout=180
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 5 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0]'
gh run watch 32675471888 -R Metta-AI/coworld-builder --exit-status
gh run download 32675471888 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-23-ledger/viewer-check
```
Run of record: **32675471888** (created 2026-08-24T00:04:03Z, conclusion `success`), found by
sorting the run list by `createdAt`, not by taking "the latest" blind. Artifact committed at
`runs/2026-08-23-ledger/viewer-check/` (`viewer-smoke.json`, `viewer-smoke.png`,
`smoke-stdout.txt`, `smoke-stderr.txt` — stderr is 0 bytes).

*Attempt 1, kept as evidence.* An earlier dispatch this pass, **32675392403**
(2026-08-24T00:02:27Z, conclusion `success`), against the identical URL, produced degraded
readouts and is committed unaltered at `runs/2026-08-23-ledger/viewer-check-attempt1/`:
```json
{"loaded":true,"ms":1440,"clock":"ROUND 0","scorebug":"","feed_lines":0}
signals: {"data_replay_loaded":null,"data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
scrub readouts: 0%="ROUND 0"  50%="ROUND 0"  100%="ROUND 0 / 14"
```
Cause, read off the instrument's own source (`templates/tools/ci/viewer_smoke.mjs:366`): the wait
loop breaks on the `coworld-replay` bridge's `ready` **or** `data-replay-loaded="true"`,
whichever arrives first. In that draw the bridge said `ready` at 1440 ms *before* the shell had
applied the replay (`data_replay_loaded: null`, `scorebug: ""`, `feed_lines: 0`), so the three
scrub clicks landed on an unhydrated `#scrub`. Its screenshot nonetheless shows a fully drawn
plaza at frame `1 / 98`. This is a race in the probe's start condition, not a viewer defect —
recorded here as a phase-80 LEARNINGS candidate (`viewer_smoke.mjs` should require
`data-replay-loaded` before scrubbing, or the workflow should expose `--soak`). Attempt 2 is the
run of record.

*(b) Readouts from the run of record.* `runs/2026-08-23-ledger/viewer-check/viewer-smoke.json`:

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-23-ledger/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":1325,"clock":"ROUND 0 / 14","scorebug":"daveey 0.0 MEDIAN daveey-1 0.0 MEDIAN Piston 0.0 MEDIAN Tinker 0.0 MEDIAN Ratchet 0.0 MEDIAN Flywheel 0.0 MEDIAN Bolt 0.0 MEDIAN Sprocket 0.0 MEDIAN","feed_lines":141}
```

```bash
jq -c '.signals' runs/2026-08-23-ledger/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/2026-08-23-ledger/viewer-check/viewer-smoke.json
```
```
no failure
```

Three clock readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | `#clock` readout |
|---|---|
| 0 %   | `ROUND 0 / 14` |
| 50 %  | `ROUND 8 / 14 · TABLES MEET` |
| 100 % | `FINAL — 14 ROUNDS` |

All three differ. `console_tail`: `["[bridge] loading", "[bridge] ready"]` — no page errors.
The `url` field inside the artifact is byte-identical to check 6's iframe `src`, so the rendered
thing is the live public viewer, not a substitute.

*(c) The replay JSON the viewer was asked to draw* (`/tmp/ep.replay`, check 4;
`kind`/`round`/`seat`/`other`/`game`/`moveA·moveB`/`payA·payB`/`text`):

Early:
```
start
round	0
meeting	0	4	1	ultimatum	5/4	7/5
meeting	0	3	7	pd	0/1	0/10
meeting	0	2	6	trust	4/50	6/6
meeting	0	0	5	pd	0/1	0/10
round	1
meeting	1	0	1	trust	5/50	6/7
meeting	1	5	6	pd	1/1	2/2
meeting	1	7	2	ultimatum	1/4	0/0
```
Middle (events 45–54):
```
meeting	6	2	3	pd	1/0	10/0
gossip	6	0	2			Piston cooperated in DILEMMA (R5) and returned 50% fairly in…
gossip	6	1	5			Flywheel defected in R6 DILEMMA after taking 2 coins while I…
round	7
meeting	7	1	3	pd	0/0	6/6
meeting	7	2	4	trust	4/50	6/6
meeting	7	5	7	pd	1/1	2/2
meeting	7	0	6	pd	1/0	10/0
gossip	7	0	7			Sprocket: median 2.0, pattern of defection and lowball offer…
gossip	7	1	6			Bolt defected in R7 DILEMMA after fair TRUST returns earlier…
```
Late (last 8):
```
round	13
meeting	13	1	4	ultimatum	6/4	6/6
meeting	13	3	7	pd	1/1	2/2
meeting	13	2	6	pd	1/1	2/2
meeting	13	5	0	ultimatum	1/3	0/0
gossip	13	0	1			Gasket: median 5.0, kind 7/harsh 5. Alternates coop/defect u…
gossip	13	1	0			Widget: cooperated fairly R8 R11 R12 despite my R13 defectio…
end	14				complete
```

**Status: TRUE** — `loaded: true` (via `data-replay-loaded="true"` *and* the bridge `ready`), and
the three clock readouts differ.

### Spectator-judgment paragraph

`viewer-smoke.png` (committed, 1280×800, taken at the 100 % scrub position) is legible and it is
unmistakably this game. Top-left is the `LEDGER` wordmark; the top bar's clock reads
`FINAL — 14 ROUNDS`, with a `REPLAY` status chip and a `« LOG` feed toggle at top-right. A full-width
scorebug runs beneath it: all eight seats with their median in large type, the word `MEDIAN`, and
kind/harsh pips — `daveey 6.0`, `daveey-1 5.5`, `Piston 6.0`, `Tinker 4.0`, `Ratchet 6.0`,
`Flywheel 2.0`, `Bolt 2.0`, `Sprocket 2.0`. Behind a dimming scrim sits the plaza scene: eight
named cogs in a ring around four meeting tables, each labelled with its alias and running median
(`Flywheel 2.0 med`, `Ratchet 6.0 med`, `Tinker 4.0 med`), with the subgame chips (`DILEMMA`,
`RESPONDER`, `PROPOSER`) still visible around the last table. Down the right edge is the gossip
rail — five attributed notes, e.g. `DAVEEY-1 ON PISTON — "Sprocket defected against me in R4 and
maintains harsh…"` and `DAVEEY ON DAVEEY-1 — "Gasket: median 5.0, kind 7/harsh 5. Alternates…"` —
which is the reputation mechanic made visible. Centre-screen is the endcard: `FINAL — 14 ROUNDS`,
the headline `daveey TOPS THE LEDGER`, and an eight-row standings table with MEDIAN / MEAN /
MEETINGS / KIND / HARSH columns. Along the bottom is the transport band: a play button, a
scrubber studded with per-beat markers (coloured ticks for meetings, `✕` glyphs for harsh
outcomes) and a `98 / 98` position readout. Nothing is empty, frozen or unreadable — the 0 % /
50 % / 100 % readouts show the clock advancing through `ROUND 0 / 14` → `ROUND 8 / 14 · TABLES
MEET` → `FINAL — 14 ROUNDS`, and attempt 1's screenshot independently shows the same shell drawn
at frame `1 / 98`, so both ends of the timeline render.

Picture and record agree exactly. The endcard's standings reproduce `results` field for field:
daveey 6.0 / 5.2 / 14 / 10 kind / 4 harsh; Piston 6.0 / 4.8 / 14 / 9 / 5; Ratchet 6.0 / 4.2;
daveey-1 5.5 / 4.0; Tinker 4.0 / 4.1; Bolt 2.0 / 3.4; Sprocket 2.0 / 3.3; Flywheel 2.0 / 2.1 with
**kind 0 / harsh 14** — the `ledger-shark` filler defecting in every one of its meetings, which is
precisely the seat-5 row `"kind":[…,0,…],"harsh":[…,14,…]` in the replay JSON. The gossip cards on
screen quote the same round-13 `gossip` events pasted above. `feed_lines: 141` corresponds to the
26 `gossip` + 56 `meeting` + 14 `round` events being narrated.

**Starter-chrome check:** yes, this is the babel/paintbot/raid lineage chrome, not a lookalike
rewrite. Transport strip with play control and position counter: present. Scrubber with beat
markers: present. Scorebug: present, adapted to medians instead of points. Endcard that stops at
the transport band and never covers the scrubber (the `#endscreen { bottom: var(--band) }` rule in
the design note): visibly honoured in the screenshot. Status chip and feed toggle: present. The
game-specific additions — the plaza ring, the gossip rail, the kind/harsh pips — sit inside that
chrome rather than replacing it. No cogame-gridlock-style divergence.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set (rounds 2, 3) | **TRUE** |
| 2 | Both champions ranked, fillers absent | **TRUE** |
| 3 | Latest round's episode request completed with replay_url | **TRUE** |
| 4 | Replay bytes valid, `ledger.replay.v1`, `complete`, champions live | **TRUE** |
| 5 | Hosted game log CLEAN | **TRUE** |
| 6 | Public page uses the static replay path, featured match present | **TRUE** |
| 7 | Certification declared the static bundle | **TRUE** |
| 8 | Viewer executed: `loaded: true`, three differing clock readouts | **TRUE** |

Replay URL: `https://softmax-public.s3.amazonaws.com/replays/316d64ba-52ed-466b-bea3-a364c679727b.replay`
viewer-check run of record: `32675471888` (attempt 1: `32675392403`)

Observation for the coordinator (non-blocking, not a check failure): the `viewer_smoke.mjs` probe
can start its scrub sequence before the shell hydrates, because it accepts the bridge `ready`
alone as "loaded". Attempt 1 shows the false-negative shape. Suggested phase-80 LEARNINGS item.
