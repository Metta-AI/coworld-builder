# VERIFY — cogchemists   (2026-08-24T09:31Z)

Verdict: **all-true** (8 / 8)

Run `2026-08-24-cogchemists` · coworld `cow_a9d9a26c-cf74-403a-85f9-542ca3bd61c9` v0.1.1 ·
league `league_7a7ba378-a709-4b1a-b8c1-b21b6577025a` · division `div_be88c7cd-0b21-4468-a404-c5c9cc767d25`.

All evidence below was fetched **this run** (09:08Z–09:31Z) except where explicitly marked:
item 7 reads the committed `runs/2026-08-24-cogchemists/release-result.json` (phase 40's artifact,
as `prompts/60-verify.md` §7 requires), and item 8's rendered evidence is the artifact of the
`viewer-check.yml` run **32711872593** dispatched by this verifier at 09:29:57Z.

Common headers (values never printed): `Authorization: Bearer $SOFTMAX_TOKEN`,
`User-Agent: coworld-builder/1.0`; elevated reads add `X-Use-Elevated-Privileges: true`.
`BASE=https://softmax.com/api/observatory/v2`.

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

Fillers were registered at 2026-08-24T09:05Z, before the trigger (`log.md` line
`09:06:52Z 50 filler-policies registered: assayer:v2=8f3133d9… quack:v2=cb0dabf3… (200, exactly the two baselines)`).
Registration confirmed live this run:

```
GET $BASE/leagues/league_7a7ba378-a709-4b1a-b8c1-b21b6577025a/filler-policies
    (headers: Authorization, User-Agent, X-Use-Elevated-Privileges)
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"8f3133d9-c511-493e-847d-60b1cef09a6f","policy_id":"4877b7ab-2b6a-4b64-acd2-11965e3b8066","policy_name":"cogchemists-assayer","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},
 {"policy_version_id":"cb0dabf3-0197-409f-8020-ed84b7d84435","policy_id":"bce94283-8841-46eb-8b2a-02d568aa0a22","policy_name":"cogchemists-quack","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```

```
GET $BASE/rounds?league_id=league_7a7ba378-a709-4b1a-b8c1-b21b6577025a&limit=20
jq -c '.entries[]|{id,round_number,status,error,created_at,completed_at}'      # fetched 09:31:29Z
```
```json
{"id":"round_f27c5e66-b778-4e77-bd46-ff499b555ae7","round_number":3,"status":"completed","error":null,"created_at":"2026-08-24T09:20:56.968386Z","completed_at":"2026-08-24T09:25:05.035321Z"}
{"id":"round_16b6b002-21cb-4459-9ffa-a8902d8163bd","round_number":2,"status":"completed","error":null,"created_at":"2026-08-24T09:05:56.563622Z","completed_at":"2026-08-24T09:08:51.162484Z"}
{"id":"round_2c48dc46-be5d-4f59-90c9-3da853959600","round_number":1,"status":"failed","error":"Temporal RoundWorkflow failed before settling the round.","created_at":"2026-08-24T09:05:00.830872Z","completed_at":"2026-08-24T09:05:01.175009Z"}
```

Entrant attributions on both completed rounds (same call, `.round_config.entrant_attributions`):

```json
round 3: [{"policy_version_id":"6f523beb-26ad-4415-9bed-4c2dc94ade56"},{"policy_version_id":"c252d902-55f1-4ad6-8565-0743aaecc0a4"}]
round 2: [{"policy_version_id":"6f523beb-26ad-4415-9bed-4c2dc94ade56"},{"policy_version_id":"c252d902-55f1-4ad6-8565-0743aaecc0a4"}]
round 1: [{"policy_version_id":"6f523beb-26ad-4415-9bed-4c2dc94ade56"}]
```
(`6f523beb…` = `cogchemists-empiricist:v2` / daveey, `c252d902…` = `cogchemists-careerist:v2` / daveey-1 —
confirmed by the `participants` block in item 3.)

Polls appended to `log.md` while waiting: 09:08:34 (0), 09:13:19 (1), 09:18:18 (1), 09:23:10 (1),
09:28:03 (2). Elapsed inside the 75-minute bound: 20 minutes.

Status: **TRUE** — rounds **2** (completed 09:08:51Z) and **3** (completed 09:25:05Z) are both
completed and both were created *after* the fillers were registered (09:05Z, i.e. after round 1 was
already created at 09:05:00.83Z). Round 1 is `failed` with
`"Temporal RoundWorkflow failed before settling the round."` — the documented pre-filler symptom
(`playbooks/observatory-api.md` §6: "A `trigger-round` issued before any filler exists fails
instantly with `Temporal RoundWorkflow failed before settling the round`"); it is not counted.

---

## 2. Both champions ranked, fillers absent/Baseline — TRUE

```
GET $BASE/divisions/div_be88c7cd-0b21-4468-a404-c5c9cc767d25/leaderboard      # fetched 09:28Z
```
```json
[
  {"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1016.0,"score_label":"Elo","score_value_type":"integer","rounds_played":2,"episode_wins":1.0,"episodes_played":null,"win_rate":0.5,"policy_label":"cogchemists-empiricist:v2","recent_rounds":null},
  {"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":984.0,"score_label":"Elo","score_value_type":"integer","rounds_played":2,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"cogchemists-careerist:v2","recent_rounds":null}
]
```

Status: **TRUE** — `daveey` (rank 1, Elo 1016, rounds_played 2, `cogchemists-empiricist:v2`) and
`daveey-1` (rank 2, Elo 984, rounds_played 2, `cogchemists-careerist:v2`) are both ranked with
`rounds_played ≥ 1`. The two filler policies (`cogchemists-assayer:v2`, `cogchemists-quack:v2`) are
**absent** from the leaderboard — the list has exactly these two rows.

---

## 3. Latest completed round's episode request completed with a replay — TRUE

```
GET $BASE/episode-requests?round_id=round_f27c5e66-b778-4e77-bd46-ff499b555ae7&limit=20
```
```json
{"n":1,"e":[{"id":"ereq_4082c439-f9c5-44b8-ae1b-dab95490b1a1","status":"completed"}]}
```
```
GET $BASE/episode-requests/ereq_4082c439-f9c5-44b8-ae1b-dab95490b1a1
jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/73254d72-43c1-41df-a2ff-b2fcfdb16885.replay",
  "participants": [
    {"position":0,"kind":"policy","policy_version_id":"6f523beb-26ad-4415-9bed-4c2dc94ade56","policy_id":"fbab64cf-d530-4a28-9a0e-ee66683b4728","policy_name":"cogchemists-empiricist","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","is_filler":false},
    {"position":1,"kind":"policy","policy_version_id":"c252d902-55f1-4ad6-8565-0743aaecc0a4","policy_id":"c75b4515-fb65-401c-999f-8496c3b5d43d","policy_name":"cogchemists-careerist","version":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","is_filler":false},
    {"position":2,"kind":"policy","policy_version_id":"cb0dabf3-0197-409f-8020-ed84b7d84435","policy_id":"bce94283-8841-46eb-8b2a-02d568aa0a22","policy_name":"cogchemists-quack","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","is_filler":true},
    {"position":3,"kind":"policy","policy_version_id":"cb0dabf3-0197-409f-8020-ed84b7d84435","policy_id":"bce94283-8841-46eb-8b2a-02d568aa0a22","policy_name":"cogchemists-quack","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","is_filler":true}
  ],
  "participant_scores": [{"position":0,"score":11.8},{"position":1,"score":5.6},{"position":2,"score":8.2},{"position":3,"score":18.0}]
}
```

Status: **TRUE** — `status: "completed"`, non-null `replay_url`, seats 0/1 are the two champions
owned by `daveey` and `daveey-1` (`is_filler: false`), seats 2/3 are the registered filler
(`is_filler: true`) and appear in the replay's own `policyNames` as `Baseline` / `Baseline (2)`
(item 4). Observation (non-blocking): the scheduler seated `cogchemists-quack:v2` in **both** filler
seats rather than one quack and one assayer — the league's choice among the two registered fillers,
not a coworld defect.

---

## 4. Replay bytes are valid and show the game — TRUE

```
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/73254d72-43c1-41df-a2ff-b2fcfdb16885.replay" -o /tmp/ep.replay
ls -l /tmp/ep.replay        ->  30271 bytes
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
```
```
strict UTF-8 JSON: ok
```
```
jq -r '.protocol, .results.reason, (.names|@csv), (.policyNames|@csv)' /tmp/ep.replay
```
```
cogchemists.replay.v1
complete
"Bolt","Tinker","Gizmo","Widget"
"daveey","daveey-1","Baseline","Baseline (2)"
```

The schema uses `kind` (not `type`/`tick`) — design.md §"Event vocabulary": six kinds
`start | round | phase | act | exhibition | end`. Adapted census:

```
jq -r '[.events[].kind]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.replay
```
```json
{"act":48,"end":1,"exhibition":1,"phase":12,"round":6,"start":1}
```

Fallback ("scripted") census per seat — the design's stand-in for `.fallback==true`
(design.md: a seat whose LLM reply fails twice "falls back to the scripted `assayer` move …
recorded with `scripted: true` so phase-60 check 4 can tell a real decision from a fallback"):

```
jq -r '[.events[]|select(.kind=="act")]|group_by(.seat)|map({seat:.[0].seat, acts:length, scripted:(map(select(.scripted==true))|length)})' /tmp/ep.replay
```
```json
[{"seat":0,"acts":12,"scripted":0},
 {"seat":1,"acts":12,"scripted":0},
 {"seat":2,"acts":12,"scripted":12},
 {"seat":3,"acts":12,"scripted":12}]
```

Champion decisions carry real content (mean length of the seat's private notes per act; the
baselines emit none):

```
jq -c '[.events[]|select(.kind=="act")]|group_by(.seat)|map({seat:.[0].seat, avg_notes:(map((.text//"")|length)|add/length|floor)})' /tmp/ep.replay
jq -c '[.events[]|select(.kind=="act" and (.say//"")!="")]|group_by(.seat)|map({seat:.[0].seat,says:length})' /tmp/ep.replay
```
```json
[{"seat":0,"avg_notes":554},{"seat":1,"avg_notes":570},{"seat":2,"avg_notes":0},{"seat":3,"avg_notes":0}]
[{"seat":1,"says":9}]
```

```
jq -c '.results' /tmp/ep.replay
```
```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],"scores":[11.8,5.6,8.2,18.0],"reputation":[10,3,6,16],"coin":[9,13,11,10],"published":[0,1,4,1],"trueTheories":[0,0,1,1],"falseTheories":[0,1,3,0],"burned":[0,0,0,0],"debunks":[0,0,0,0],"rounds":6,"maxRounds":6,"reason":"complete"}
```

Status: **TRUE** — strict `jq -e` parse succeeds (valid UTF-8 JSON); `protocol` is
`cogchemists.replay.v1`, matching the manifest/design note; `results.reason == "complete"` (the
legal `"deadline"` variant was **not** taken — all 6 of 6 rounds played); both champion seats made
**12/12 non-scripted decisions each — zero fallbacks** — with ~550-character reasoning notes and, for
seat 1, 9 spoken lines. The two Baseline seats are 12/12 scripted, exactly as intended for fillers.
Replay bytes committed at `runs/2026-08-24-cogchemists/episode.replay.json`.

---

## 5. Hosted game log is clean — TRUE (with the documented `rejected` exception cited below)

```
GET $BASE/episode-requests/ereq_4082c439-f9c5-44b8-ae1b-dab95490b1a1/artifacts/logs
    (headers: Authorization, User-Agent, X-Use-Elevated-Privileges)   ->  HTTP 200, 54170 bytes
```
The body is python `b'…'` byte-string reprs under `===== container: … =====` headers; decoded per
repr with `ast.literal_eval` before grepping (playbook §10). Containers present:
`coworld-init-config`, `bedrock-sidecar`, `game`, `worker`.

```
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' <decoded>
```
```
134 cogchemists: Widget rejected (already_claimed); passing
142 cogchemists: Gizmo rejected (already_claimed); passing
143 cogchemists: Widget rejected (already_claimed); passing
152 cogchemists: Widget rejected (already_claimed); passing
164 cogchemists: Gizmo rejected (already_claimed); passing
174 cogchemists: Widget rejected (already_claimed); passing
183 cogchemists: Widget rejected (already_claimed); passing
```
Per-pattern counts on the decoded text:
```
falling back                  0
LLM provider is unavailable   0
cut off at max_tokens         0
rejected                      7   (all of the form above)
```
Context (decoded log lines 131–137, 140–146):
```
cogchemists: Bolt plays pass
cogchemists: Tinker plays pass
cogchemists: Gizmo plays publish a="Nightcap" signature="R-G-B-"
cogchemists: Widget rejected (already_claimed); passing
cogchemists: round 2/6 lab at 25s
…
cogchemists: Tinker plays publish a="Emberroot" signature="R-G-B+"
cogchemists: Gizmo rejected (already_claimed); passing
cogchemists: Widget rejected (already_claimed); passing
cogchemists: Bolt plays pass
```
LLM health, same log (`bedrock-sidecar` container):
```
grep -c 'bedrock_sidecar_complete'  -> 24
grep -o '"ok":true'  | wc -l        -> 24
grep -o '"ok":false' | wc -l        -> 0
```
sample line: `bedrock_sidecar_complete {… "model":"global.anthropic.claude-haiku-4-5-20251001-v1:0","operation":"InvokeModel","ok":true,"status_code":200,"latency_ms":2355.7,"error_kind":null,"error_type":null,"message":null …}`
Game container start-of-episode lines:
```
cogchemists: slot 3 delivered a prompt (881 chars, scripted quack)
cogchemists: slot 2 delivered a prompt (881 chars, scripted quack)
cogchemists: slot 1 delivered a prompt (1327 chars)
cogchemists: slot 0 delivered a prompt (1529 chars)
cogchemists: starting with 4/4 players connected
cogchemists llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0, … batch spacing 10000ms
cogchemists: episode timeout 1200s (assumed); playing until 720s
```

Status: **TRUE**. Zero occurrences of the three LLM-health patterns (`falling back`,
`LLM provider is unavailable`, `cut off at max_tokens`) and zero failed Bedrock calls (24/24
`"ok":true`, `status_code:200`, `error_kind:null`). The seven `rejected` hits are **the game's own
rule vocabulary, not an LLM defect**, and are documented in the design note: design.md line 161
("A rejected action is recorded with `result: \"rejected:<reason>\"`"), line 617 (the `act` event's
`result` enum includes `rejected:<reason>`), and line 901 ("Rejections are shown, dim: `Widget tried
to publish Nightcap — Sprocket claimed it first this phase. Widget passes (+1 coin).`"). Every one of
the seven is a **scripted Baseline** seat (Gizmo = seat 2, Widget = seat 3) whose `publish` collided
with an ingredient another seat had already claimed that phase, degrading to `pass` exactly as
specified; **no champion seat appears in any of them**, and the replay confirms the same events as
`result:"rejected:already_claimed"` on seats 2 and 3 only. This is the documented exception, cited;
nothing here is a fallback, a provider outage or a truncation.

---

## 6. The public page uses the static replay path — TRUE

Source **(a)** — raw HTML of the human page:
```
curl -sS "https://softmax.com/cogchemists" -o /tmp/page.html    -> HTTP 200, 486204 bytes
grep -o '<iframe[^>]*src="[^"]*"' /tmp/page.html
```
```
NO IFRAME IN RAW HTML
```
Not a false negative — the page is client-rendered for the iframe (playbook §Featured match:
"Answered (lighthouse run, 2026-08-22): the page is now **client-rendered** for the iframe").

Source **(b)** — the coworld detail API (the `prompts/60-verify.md` §6 fallback), for the record:
```
GET $BASE/coworlds?limit=200   |   jq '…|select(.name=="cogchemists")|{id,name,version,canonical,replay_viewer,featured_match}'
```
```json
{"id":"cow_a9d9a26c-cf74-403a-85f9-542ca3bd61c9","name":"cogchemists","version":"0.1.1","canonical":true,"replay_viewer":null,"featured_match":null}
{"id":"cow_c48f4397-3add-4def-8c4e-be12321fd343","name":"cogchemists","version":"0.1.0","canonical":false,"replay_viewer":null,"featured_match":null}
```
`featured_match: null` here is platform-wide and is not evidence either way (same playbook note).

Source **(c) — the one I used** — the featured match server-rendered into the page's own SSR payload
at `state.playlist[0]` (extracted from `/tmp/page.html`, unescaped):
```json
"state":{"leagueId":"league_7a7ba378-a709-4b1a-b8c1-b21b6577025a","playlist":[{
  "episodeId":"d48184d3-a508-41c8-9b8f-e59a6bee9a7d",
  "coworldId":"cow_a9d9a26c-cf74-403a-85f9-542ca3bd61c9","coworldName":"cogchemists","coworldVersion":"0.1.1",
  "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/73254d72-43c1-41df-a2ff-b2fcfdb16885.replay",
  "finishedAt":"2026-08-24T09:24:56.428305Z","roundNumber":3,"episodeNumber":1,"code":"cogchemists.r3.e1",
  "matchup":{"divisionId":"div_be88c7cd-0b21-4468-a404-c5c9cc767d25","divisionName":"Competition",
    "first":{"rank":1,"player_name":"daveey","score":1016,"policy_label":"cogchemists-empiricist:v2","rounds_played":2,"episode_wins":1,"win_rate":0.5},
    "second":{"rank":2,"player_name":"daveey-1","score":984,"policy_label":"cogchemists-careerist:v2","rounds_played":2,"episode_wins":0,"win_rate":0}},
  "inspectUrl":"/observatory/v2?tab=episode-requests&detail=episode-request:ereq_4082c439-f9c5-44b8-ae1b-dab95490b1a1",
  "outcome":"first"}]
```

Source **(d)** — the call the page's JS makes to build the iframe `src`:
```
POST $BASE/coworlds/replays/session
  -d '{"coworld_id":"cow_a9d9a26c-cf74-403a-85f9-542ca3bd61c9","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/73254d72-43c1-41df-a2ff-b2fcfdb16885.replay"}'
```
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_a9d9a26c-cf74-403a-85f9-542ca3bd61c9/sha256%3A967ac7cc48105407d8bf726c725452d102166dcfcee569ae3cacfc687ac2a431/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F73254d72-43c1-41df-a2ff-b2fcfdb16885.replay&v=2","ready":true}
HTTP 200
```

Status: **TRUE** — a featured match is present (round 3, episode 1, `cogchemists.r3.e1`, daveey rank 1
vs daveey-1 rank 2) and the iframe `src` is the **static** route
`…/v2/coworlds/replays/static/cow_a9d9a26c-cf74-403a-85f9-542ca3bd61c9/sha256%3A967ac7cc…a431/index.html?replay=<s3 url>`
with `ready: true`. The `<sha>` segment URL-decodes to
`sha256:967ac7cc48105407d8bf726c725452d102166dcfcee569ae3cacfc687ac2a431`, which is exactly
`STATE.coworld.manifest_sha`. **No `/client/replay` pod URL anywhere.**

---

## 7. Certification declared the static bundle — TRUE

Source: the **committed** `runs/2026-08-24-cogchemists/release-result.json` (phase 40's artifact from
release run 32708476022) — not `/tmp`, and no re-download was needed; the file was present.

```
jq -r '.certify.replay_liveness' runs/2026-08-24-cogchemists/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```
Surrounding certification transcript from the same file (`.certify.output_tail`, trimmed to the step
lines):
```
  [pass] matriculate: manifest conforms to the Coworld schema
  [pass] source-resolves: … declares a source_url that resolves to publicly accessible source
  [pass] images-reachable: every declared image is pullable or inspectable
  [pass] fixture-conforms: the certification fixture validates against game.config_schema …
  [pass] smoke-episode: the game and certification players run one episode
  [pass] results-conform: episode results validate against results_schema
  [pass] replay-present: a replay artifact was produced
  [pass] replay-loadable: the replay artifact has a declared viewer path
  [pass] players-run: every declared player actually started on the smoke episode (not just declared)
  [pass] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks
Certified dist/coworld_manifest.json
Transcript: coworld-executable (10 steps passed)
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```
`jq '.certify.ok'` → `true`.

Status: **TRUE** — the string contains `Replay liveness: skipped (static replay bundle declared`,
read from the committed `runs/2026-08-24-cogchemists/release-result.json`.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — TRUE

*(a) Dispatch.* The iframe `src` from item 6, verbatim, opened in headless chromium by CI:
```
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder \
  -f url='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_a9d9a26c-cf74-403a-85f9-542ca3bd61c9/sha256%3A967ac7cc48105407d8bf726c725452d102166dcfcee569ae3cacfc687ac2a431/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F73254d72-43c1-41df-a2ff-b2fcfdb16885.replay&v=2' \
  -f timeout=90                                              # dispatched 2026-08-24T09:29:57Z
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
  | jq -c 'sort_by(.createdAt)|reverse|.[0:3]'
```
```json
[{"createdAt":"2026-08-24T09:29:59Z","databaseId":32711872593,"event":"workflow_dispatch","status":"in_progress"},
 {"createdAt":"2026-08-24T09:20:26Z","databaseId":32710988177,"event":"workflow_dispatch","status":"completed"},
 {"createdAt":"2026-08-24T09:18:55Z","databaseId":32710843104,"event":"workflow_dispatch","status":"completed"}]
```
Run **32711872593** is the one created after the dispatch (09:29:59Z > 09:29:57Z) — not "the latest"
taken blind. `gh run watch 32711872593 --exit-status` → **green**, `viewer-check in 34s`, all steps ✓
including `Fail if the viewer did not load`.
`gh run download 32711872593 -n viewer-check -D runs/2026-08-24-cogchemists/viewer-check` →
`viewer-smoke.json` (1258 B), `viewer-smoke.png` (367572 B), `smoke-stdout.txt`, `smoke-stderr.txt` (0 B).

*(b) The readouts, verbatim from `runs/2026-08-24-cogchemists/viewer-check/viewer-smoke.json`.*
```
jq -c '{loaded, ms, clock, scorebug, feed_lines}' viewer-smoke.json
```
```json
{"loaded":true,"ms":1072,"clock":"THE ACADEMY · 6 ROUNDS","scorebug":"daveey 10 REP 4c 0 SOLVED daveey-1 10 REP 4c 0 SOLVED Gizmo 10 REP 4c 0 SOLVED Widget 10 REP 4c 0 SOLVED","feed_lines":123}
```
```
jq -c '.signals' viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```
```
jq -r '.failure // "no failure"' viewer-smoke.json     ->  no failure
jq -r '.status, .loading_text' viewer-smoke.json       ->  REPLAY  /  LOADING REPLAY…
console_tail                                           ->  ["[bridge] loading","[bridge] ready"]
```

Three clock readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | `#clock` readout |
|---|---|
| 0 %   | `THE ACADEMY · 6 ROUNDS` |
| 50 %  | `ROUND 4 / 6 · MARKET · MOVES IN` |
| 100 % | `FINAL · WIDGET 18.0` |

All three **differ** — the replay advances under the scrubber, it is not one frozen frame.
A `#scrub` element exists (the json reports real positions, not `"(no #scrub…)"`), and the
screenshot shows it populated with beat markers (`69 / 69` at the transport's right).

*(c) Reconciliation against the replay JSON* (`/tmp/ep.replay`, item 4; schema uses `kind`, so the
prompt's `.tick/.type` line was adapted to
`jq -r '.events[]|[.kind,(.round//""),(.phase//""),(.seat//""),(.action//""),(.result//""),(.scripted//""),((.say//"")|.[0:60])]|@tsv'`):

early (first 20 events):
```
start
round	0	lab
phase	0	lab
act	0	lab	0	test_student	ok
act	0	lab	1	test_student	ok
act	0	lab	2	test_self	glowed	true
act	0	lab	3	test_self	ok	true
phase	0	market
act	0	market	0	pass	ok
act	0	market	1	pass	ok
act	0	market	2	publish	ok	true
act	0	market	3	publish	rejected:already_claimed	true
round	1	market
phase	1	lab
act	1	lab	1	forage	ok		Building my hand for market opportunities.
act	1	lab	2	forage	ok	true
act	1	lab	3	forage	ok	true
act	1	lab	0	forage	ok
phase	1	market
act	1	market	1	publish	ok		Emberroot shows promise—initial trials suggest a negative re
```
middle (events 30–44):
```
phase	2	market
act	2	market	2	publish	ok	true
act	2	market	3	publish	rejected:already_claimed	true
act	2	market	0	pass	ok
act	2	market	1	pass	ok
round	3	market
phase	3	lab
act	3	lab	3	forage	ok	true
act	3	lab	0	transmute	ok
act	3	lab	1	forage	ok		Time to gather new materials.
act	3	lab	2	forage	ok	true
phase	3	market
act	3	market	3	publish	ok	true
act	3	market	0	pass	ok
act	3	market	1	sell	miss		A fresh blend for your quest!
```
late (last 12 events):
```
phase	5	lab
act	5	lab	1	forage	ok		Drawing more cards to find what the adventurer needs.
act	5	lab	2	forage	ok	true
act	5	lab	3	forage	ok	true
act	5	lab	0	test_student	ok
phase	5	market
act	5	market	1	sell	miss		Testing a theory about the adventurer's request.
act	5	market	2	publish	ok	true
act	5	market	3	publish	rejected:already_claimed	true
act	5	market	0	pass	ok
exhibition	5
end	6
```
the exhibition event and results:
```json
{"round":5,"verdicts":[{"ingredient":0,"claim":0,"author":2,"true":false},{"ingredient":1,"claim":1,"author":1,"true":false},{"ingredient":2,"claim":1,"author":2,"true":false},{"ingredient":3,"claim":0,"author":3,"true":true},{"ingredient":4,"claim":1,"author":2,"true":true},{"ingredient":5,"claim":1,"author":2,"true":false}],"repDeltas":[0,-6,-13,5]}
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],"scores":[11.8,5.6,8.2,18.0],"reputation":[10,3,6,16],"coin":[9,13,11,10],"published":[0,1,4,1],"trueTheories":[0,0,1,1],"falseTheories":[0,1,3,0],"burned":[0,0,0,0],"debunks":[0,0,0,0],"rounds":6,"maxRounds":6,"reason":"complete"}
```

**Item 8 verdict: TRUE** — `loaded: true` (first frame at **1072 ms**, `data-replay-loaded="true"`
*and* the `coworld-replay` bridge reaching `ready`, `data_replay_error: null`, `failure: null`), and
the **three clock readouts differ**.

### Spectator judgment

The screenshot (`runs/2026-08-24-cogchemists/viewer-check/viewer-smoke.png`, taken after the 100 %
seek) is a **full, legible, populated broadcast frame** — not an empty canvas and not a loading
caption. Reading it top to bottom: the `COGCHEMISTS` wordmark in the topband (the starter's
`BULL/WHIP` two-tone treatment, ink-and-print palette), the centred `#clock` reading
`FINAL · WIDGET 18.0`, and a `REPLAY` status chip with the `« LOG` feed toggle at the right. Below
that the four-plate `#scorebug` — `daveey 10 REP 9c 0 SOLVED`, `daveey-1 3 REP 13c`,
`Gizmo 6 REP 11c ▪▪▪▪` (four wax-seal pips — Gizmo published four theories, `published[2] == 4`),
`Widget 16 REP 10c` — each in its seat tint, the reputation number as the big figure. Then the appended `#labbar`:
`ROUND 6/6 · ADVENTURER WANTS GREEN- · SEALS 6 STANDING / 0 BURNED · BEST GRID 4 CHEMISTRIES LEFT`,
which agrees exactly with the replay (`published` sums to 6, `burned` all zero). The stage shows the
four cog sprites at their stations with alias/reputation/coin under each, the bench with face-up
ingredient cards (`Widow's Salt`, `Emberroot`, `Nightcap`, `Rime Thistle`), the **theory board** down
the right as six wax-sealed cards — `Nightcap FALSE −6`, `Emberroot FALSE −6`, `Fen Lily FALSE −6`,
`Widow's Salt TRUE +5`, `Copper Fern TRUE +5`, `Gravebloom FALSE −6` — and the **hole-cam strip**
across the bottom, the revealed true signature row (`R+G+B-`, `R-G-B-`, `R-G-B+`, …) over the
four per-seat rows with the red-ringed bluff cells. Centred over it is the endcard:
`FINAL — 6 ROUNDS · 6 SEALS · 0 BURNED` / `Widget MADE THE REPUTATION` / a ranked table
`Widget 16 10 1 1 0 18.0`, `daveey 10 9 0 0 0 11.8`, `Gizmo 6 11 4 1 3 8.2`, `daveey-1 3 13 1 0 1 5.6`.
Every one of those numbers matches `results` in the replay JSON field-for-field, and the
`TRUE/FALSE` stamps match the six `exhibition` verdicts (authors 2, 1, 2, 3, 2, 2; two true).
At the foot sits the transport bar: play button, the scrubber drawn as a momentum strip with
coloured **beat markers** (amber publish, green sell, paper test, blue-ish trade) and round
separators, and the `69 / 69` position readout — 69 = the 69 events in the replay, so the beats are
the episode, one marker per act.

It shows **the game**, not just a scoreboard: the deduction loop is readable from the picture alone —
who published which ingredient, whose seal survived the exhibition, how much reputation that was
worth. Motion is proven by the three differing clock readouts (`THE ACADEMY · 6 ROUNDS` →
`ROUND 4 / 6 · MARKET · MOVES IN` → `FINAL · WIDGET 18.0`) and by the 123 feed lines the DOM
reported. The chrome is unmistakably the **bullwhip lineage**: same topband + wordmark, same
`#scorebug` plates, same `#feed` with its `« LOG` toggle, same transport strip with a momentum
scrubber and beats, same absolutely-positioned endcard stopping at the transport band — with exactly
one appended element (`#labbar`) and the game's own stage art. This is not the cogame-gridlock
failure mode (a rewrite that only reuses the ids).

Two non-blocking legibility observations for the coordinator, neither affecting any verdict:
1. **Seat labels mix registries.** The stations/scorebug/endcard show `daveey`, `daveey-1`, `Gizmo`,
   `Widget` — player names for the two champions but the in-fiction aliases for the two Baseline
   seats (whose `policyNames` are `Baseline` / `Baseline (2)`). It reads fine, but a spectator sees
   two naming systems in one row.
2. **The champion in seat 0 (`cogchemists-empiricist:v2`) played passively** — it published nothing
   all episode (`published[0] == 0`) and passed in five of six markets, so the amber publish beats on
   the scrubber all belong to the other three seats. Not a viewer or platform defect (its private
   notes show real grid reasoning each turn, 12/12 non-scripted), but a prompt-strategy note if the
   featured match is meant to showcase the champions doing the thing the game is about.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | **TRUE** — rounds 2 (09:08:51Z) and 3 (09:25:05Z); round 1 `failed` = documented pre-filler symptom |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey 1016 / daveey-1 984, `rounds_played` 2 each; no filler rows |
| 3 | Latest round's episode request completed with a replay | **TRUE** — `ereq_4082c439…` completed, S3 `replay_url`, seats 0/1 = daveey / daveey-1 |
| 4 | Replay bytes valid and show the game | **TRUE** — strict JSON ok, `cogchemists.replay.v1`, `reason: "complete"`, champions 0 scripted / 24 acts |
| 5 | Hosted game log clean | **TRUE** — 0 LLM-health hits, 24/24 Bedrock `ok:true`; 7 `rejected` hits are documented in-game rule rejections by Baseline seats |
| 6 | Public page uses the static replay path | **TRUE** — `…/replays/static/<cow_id>/<manifest_sha>/index.html?replay=…`, `ready:true`; featured match `cogchemists.r3.e1` |
| 7 | Certification declared the static bundle | **TRUE** — `Replay liveness: skipped (static replay bundle declared…` from committed `release-result.json` |
| 8 | Viewer executed and judged | **TRUE** — run 32711872593, `loaded:true` at 1072 ms, three differing clock readouts, full bullwhip-lineage frame |
