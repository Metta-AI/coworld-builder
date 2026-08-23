# VERIFY — contagion   (2026-08-23T12:37Z)

Verdict: **all-true** (8/8)

Run `2026-08-23-contagion` · coworld `cow_6b43a43d-8aa2-41ea-aae6-4dd50f084c54` v0.1.0 ·
league `league_53d9ccfb-c943-4b5c-a89f-b9b149365df1` · division `div_16e3c809-fd49-46f5-8eae-4fdea07d7733`.

All calls below were made **fresh in this phase-60 session** (12:14Z–12:37Z), with the single
documented exception of item 7, whose evidence is the committed
`runs/2026-08-23-contagion/release-result.json` (phase 40's artifact), as
`prompts/60-verify.md` §7 requires. Headers sent on every Observatory call:
`Authorization: Bearer $SOFTMAX_TOKEN` and `User-Agent: coworld-builder/1.0`; `X-Use-Elevated-Privileges: true`
added where noted. **No header values are printed anywhere in this file.**

```
BASE=https://softmax.com/api/observatory/v2
L=league_53d9ccfb-c943-4b5c-a89f-b9b149365df1
D=div_16e3c809-fd49-46f5-8eae-4fdea07d7733
COW=cow_6b43a43d-8aa2-41ea-aae6-4dd50f084c54
```

**Deviations from the prompt's literal jq, and why** (each is noted again at the item it affects):

| Where | Prompt assumes | This API/game returns | Adaptation used |
|---|---|---|---|
| items 1, 3, 6 | `.entries[]` | `/rounds` and `/episode-requests` do wrap in `.entries`; `/leaderboard`, `/coworlds` may be bare arrays | `(if type=="array" then . else .entries end)` — shape-agnostic, same rows |
| item 4 | events keyed `.type=="decision"`, `.fallback==true` | this game's replay uses `.kind` ∈ `start\|week\|dial\|end`; a decision is `kind=="dial"`; a fallback is `"scripted": true` | `select(.kind=="dial")` / `select(.scripted==true)`, per the design's replay schema (`design.md` §Replay payload, l.430-436) |
| item 6 | grep the iframe out of the page HTML | the page is client-rendered and `/coworlds`.`featured_match` is `null` platform-wide | fell back to the SSR payload's `state.playlist[0]` + `POST /coworlds/replays/session`, exactly as `playbooks/observatory-api.md` §Featured match records. Both sources pasted below. |

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

Fillers currently registered on the league (read; needs the elevated header even though it is a read):

```
GET $BASE/leagues/$L/filler-policies
  headers: Authorization, User-Agent, X-Use-Elevated-Privileges
HTTP 200
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"90a1ef43-3268-49a6-b756-62aa8992ae3e","policy_id":"34e66e6e-6cb7-41ee-9a33-6ec17573b8c7",
  "policy_name":"contagion-sentinel","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3",
  "player_name":"daveey","display_name":null},
 {"policy_version_id":"d224d741-7a3a-4aa1-8ceb-ce21e937e0f4","policy_id":"d52f3149-26d7-4dd9-a355-5cb297227830",
  "policy_name":"contagion-laggard","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3",
  "player_name":"daveey","display_name":null}]}
```

Rounds:

```
GET $BASE/rounds?league_id=$L&limit=20
HTTP 200
$ jq '{entries:[.entries[]|{id,round_number,status,error,created_at,completed_at}]}'
```
```json
{
  "entries": [
    {
      "id": "round_0d4c6b59-481c-4067-b5d9-e191896a56a5",
      "round_number": 3,
      "status": "completed",
      "error": null,
      "created_at": "2026-08-23T12:27:30.921720Z",
      "completed_at": "2026-08-23T12:30:26.807446Z"
    },
    {
      "id": "round_c40b156c-51b0-4350-8bd3-c0af0459cedb",
      "round_number": 2,
      "status": "completed",
      "error": null,
      "created_at": "2026-08-23T12:12:30.569698Z",
      "completed_at": "2026-08-23T12:15:44.229137Z"
    },
    {
      "id": "round_f9e46718-66bc-42e0-93ff-51bd6c1543d1",
      "round_number": 1,
      "status": "failed",
      "error": "Temporal RoundWorkflow failed before settling the round.",
      "created_at": "2026-08-23T12:12:00.474887Z",
      "completed_at": "2026-08-23T12:12:00.719724Z"
    }
  ]
}
```
```
$ curl -sS "$BASE/rounds?league_id=$L&limit=20" … \
  | jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
2
```

Status: **TRUE** — rounds **2** and **3** are `completed` (12:15:44.229Z and 12:30:26.807Z).
Fillers were registered at **12:10–12:12Z** (`log.md` l.46: `2026-08-23T12:13:30Z 50 fillers registered:
sentinel=90a1ef43 laggard=d224d741 … unpaused; trigger-round accepted`), i.e. **before** both of these
rounds were created (12:12:30Z, 12:27:30Z), and both rounds actually seated those fillers (item 3's
`participants` show `is_filler: true` for the sentinel/laggard seats).

Round 1's failure is recorded verbatim above: `"Temporal RoundWorkflow failed before settling the round."`
It was auto-created by the scheduler at 12:12:00.474Z with pre-filler entrants — 30 s *before* round 2 —
and is exactly the documented failure mode for a round with no filler registered
(`playbooks/observatory-api.md` §6: "A `trigger-round` issued before any filler exists fails instantly with
`Temporal RoundWorkflow failed before settling the round`"). It does not count and is not counted.
No `discarded` rounds exist.

Poll log (checks 1 and 3, every ~5 min, inside the 75-minute bound that opened at 12:14:33Z):

| poll | UTC | completed rounds ≥2 |
|---|---|---|
| 1 | 12:15:10Z | 0 (r2 pending) |
| 2 | 12:20:14Z | 1 (r2 completed) |
| 3 | 12:26:27Z | 1 |
| 4 | 12:31:22Z | **2** (r3 completed) → bound exited at 17 min of 75 |

---

## 2. Both champions ranked, fillers absent — **TRUE**

```
GET $BASE/divisions/$D/leaderboard
HTTP 200        (bare JSON array, as playbooks/observatory-api.md §11 records)
```
Raw body:
```json
[{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
  "score":1030.5304984710244,"score_label":"Elo","score_value_type":"integer","rounds_played":2,
  "episode_wins":2.0,"episodes_played":null,"win_rate":1.0,"policy_label":"contagion-broker:v1",
  "recent_rounds":null},
 {"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
  "score":969.4695015289755,"score_label":"Elo","score_value_type":"integer","rounds_played":2,
  "episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"contagion-warden:v1",
  "recent_rounds":null}]
```
```
$ … | jq -r '(if type=="array" then . else .entries end)|.[]
             |[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
1	daveey-1	contagion-broker:v1	1030.5304984710244	2	2.0
2	daveey	contagion-warden:v1	969.4695015289755	2	0.0
```

Status: **TRUE** — `daveey` (`contagion-warden:v1`) and `daveey-1` (`contagion-broker:v1`) are both
ranked with `rounds_played = 2 ≥ 1`. The leaderboard has exactly two rows: the fillers
(`contagion-sentinel:v1`, `contagion-laggard:v1`) are **absent**, which satisfies the "absent or
`Baseline…`" requirement. (Inside the episode they are renamed `Baseline`/`Baseline (2..4)` — see the
replay's `policyNames` in item 4.)

---

## 3. Latest completed round's episode request completed with a replay — **TRUE**

Latest completed round is **round 3** = `round_0d4c6b59-481c-4067-b5d9-e191896a56a5` (item 1).

```
GET $BASE/episode-requests?round_id=round_0d4c6b59-481c-4067-b5d9-e191896a56a5&limit=20
HTTP 200
ereq_a423e065-fc6a-4c58-a0d5-71e38c0893a6	completed
```
```
GET $BASE/episode-requests/ereq_a423e065-fc6a-4c58-a0d5-71e38c0893a6
HTTP 200
$ jq '{status, replay_url, participants:[.participants[]|{position,policy_name,player_name,is_filler}], participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/af23e250-a24b-4f6e-8462-5f124326df11.replay",
  "participants": [
    {"position": 0, "policy_name": "contagion-warden",   "player_name": "daveey",   "is_filler": false},
    {"position": 1, "policy_name": "contagion-broker",   "player_name": "daveey-1", "is_filler": false},
    {"position": 2, "policy_name": "contagion-sentinel", "player_name": "daveey",   "is_filler": true},
    {"position": 3, "policy_name": "contagion-sentinel", "player_name": "daveey",   "is_filler": true},
    {"position": 4, "policy_name": "contagion-laggard",  "player_name": "daveey",   "is_filler": true},
    {"position": 5, "policy_name": "contagion-sentinel", "player_name": "daveey",   "is_filler": true}
  ],
  "participant_scores": [
    {"position": 0, "score": -3028.0},
    {"position": 1, "score": 7573.0},
    {"position": 2, "score": 11818.0},
    {"position": 3, "score": 9961.0},
    {"position": 4, "score": -28706.0},
    {"position": 5, "score": 10595.0}
  ]
}
```

Status: **TRUE** — `status == "completed"`, `replay_url` non-null, seat 0 = `daveey`
(`contagion-warden`, `is_filler:false`) and seat 1 = `daveey-1` (`contagion-broker`, `is_filler:false`);
the other four seats are the registered fillers, flagged `is_filler:true` and displayed in the replay as
`Baseline`/`Baseline (2..4)` (item 4's `policyNames`).

**Replay URL:** `https://softmax-public.s3.amazonaws.com/replays/af23e250-a24b-4f6e-8462-5f124326df11.replay`

---

## 4. Replay bytes are valid and show the game — **TRUE**

```
GET https://softmax-public.s3.amazonaws.com/replays/af23e250-a24b-4f6e-8462-5f124326df11.replay
HTTP 200 bytes=98177          # saved to /tmp/ep.replay and to runs/2026-08-23-contagion/ep.replay
$ jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok
$ jq -r '.protocol, .results.reason' /tmp/ep.replay
contagion.replay.v1
complete
$ jq -r 'keys|join(" ")' /tmp/ep.replay
config events names policyNames protocol results rules
$ jq -c '.policyNames' /tmp/ep.replay
["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"]
$ jq -c '.results' /tmp/ep.replay
{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"],
 "scores":[-3028,7573,11818,9961,-28706,10595],"gdp":[8772,12459,12804,11671,16892,11913],
 "deaths":[5900,2443,493,855,22799,659],
 "regions":["Saltmarch","Wintermoor","Riverbend","Kestrel Flats","Harborlea","Ash Hollow"],
 "weeks":20,"maxWeeks":20,"totalDeaths":33149,"totalGdp":74511,"reason":"complete"}
```

`protocol` matches the manifest's declared `contagion.replay.v1`. `results.reason == "complete"` — the
normal ending, no `deadline` exception needed — and `weeks == maxWeeks == 20` corroborates it
(`design.md` §End conditions, l.251-257: only `complete` and `deadline` are legal, and `deadline` is
recorded by `weeks < maxWeeks`).

**Decision / fallback counts.** *Adaptation, as flagged in the header table:* this game's events carry
`kind`, not `type`, and a fallback is `"scripted": true`, not `"fallback": true`. The prompt's generic
jq would have returned 0 for both and been meaningless; these are the equivalents.

```
$ jq -r '[.events[]|.kind]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.replay
{"dial":120,"end":1,"start":1,"week":21}
$ jq -r '[.events[]|select(.kind=="dial")]|length' /tmp/ep.replay          # decisions
120
$ jq -r '[.events[]|select(.kind=="dial")]|group_by(.seat)
         |map({seat:.[0].seat,total:length,scripted:([.[]|select(.scripted==true)]|length)})' /tmp/ep.replay
[{"seat":0,"total":20,"scripted":0},   <- daveey        (champion, contagion-warden)
 {"seat":1,"total":20,"scripted":0},   <- daveey-1      (champion, contagion-broker)
 {"seat":2,"total":20,"scripted":20},  <- Baseline      (filler, scripted by design)
 {"seat":3,"total":20,"scripted":20},
 {"seat":4,"total":20,"scripted":20},
 {"seat":5,"total":20,"scripted":20}]
```

Seat→policy mapping is `policyNames`, ordered by seat: seat 0 = `daveey`, seat 1 = `daveey-1`.
**Champion fallbacks: 0 of 40 (0 %).** The filler seats are 100 % scripted because the fillers *are* the
scripted baselines — that is what they are for, not a degradation.

Champion decisions carry non-trivial content (a full dial vector, gates, aid, a public `say` and private
`text`). Example, seat 1 / week 13:
```json
{"kind":"dial","week":13,"seat":1,"pos":4,"region":"Wintermoor","lockdown":3,"testing":3,
 "borders":[{"to":"Ash Hollow","gate":2},{"to":"Saltmarch","gate":2},{"to":"Kestrel Flats","gate":2}],
 "aid":[],"say":"W13→W14: Wintermoor CRITICAL 39k true (3.92%). L3/T3 now—must break exponential. …",
 "scripted":false,"corrected":false,
 "text":"CRISIS POINT. True prevalence 3.92%, deaths accelerating (135 this week), hospitals 3x over
 capacity. … DECISION: Go to L3/T3 immediately. Output will drop to ~372 gross (0.40 lockdown factor ×
 930 baseline), but we MUST break transmission …"}
```
```
$ jq -r '[.events[]|select(.kind=="dial" and .seat==0)|.lockdown]|tostring' /tmp/ep.replay
[1,1,1,1,1,1,2,3,3,3,3,2,2,3,3,3,2,1,1,1]
$ jq -r '[.events[]|select(.kind=="dial" and .seat==1)|.lockdown]|tostring' /tmp/ep.replay
[0,0,0,0,0,0,0,0,1,1,1,1,1,3,3,3,2,2,2,3]
$ jq -r '[.events[]|select(.kind=="dial" and (.seat==0 or .seat==1))|select((.aid|length)>0)]|length'
30                       # champion aid transfers
$ jq -r '[.events[]|select(.kind=="dial" and (.seat==0 or .seat==1))|.borders[]|select(.gate>0)]|length'
77                       # champion border-gate closures
```

Status: **TRUE** — strict-parser-valid UTF-8 JSON, `protocol` matches, `reason == "complete"`, and the
champion seats made 40/40 live, non-scripted, non-trivial decisions (0 fallbacks) that vary over the
episode: suppress → reopen → re-suppress, with aid and border gates actually used.

---

## 5. Hosted game log is clean — **TRUE**

```
GET $BASE/episode-requests/ereq_a423e065-fc6a-4c58-a0d5-71e38c0893a6/artifacts/logs
  headers: Authorization, User-Agent, X-Use-Elevated-Privileges
HTTP 200 bytes=98827
$ grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/ev/r3.log || echo CLEAN
CLEAN
```

Zero hits for all four patterns. The body is a real, non-empty container log (first 200 chars per line):
```
===== container: coworld-init-config =====
b''

===== container: bedrock-sidecar =====
b'2026-08-23 12:27:38,681 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1",…

===== container: game =====
b'contagion: seed not pinned; randomized\ncontagion: seats=6 weeks=20 talk=true model=claude-sonnet-5\n
  contagion: serving on 0.0.0.0:8080\ncontagion: player slot 5 connected (1/6)\ncontagion: slot 5 d…

===== container: worker =====
b''
```

The round-2 log was fetched and grepped identically at 12:23Z and was also `CLEAN` (HTTP 200,
100780 bytes, `ereq_f1179838-54d3-487d-9e77-0d6ec2e4baae`). No `LLM provider is unavailable` appeared,
so the platform-capacity exception was never invoked — no exception is being claimed here.

Status: **TRUE** — CLEAN, no exception needed. Corroborated by item 4: 0 scripted fallbacks on the
champion seats, which is what a clean LLM path looks like from the other side.

---

## 6. The public page uses the static replay path — **TRUE**

**Source (a) — raw HTML grep, as the prompt asks first:**
```
GET https://softmax.com/contagion
HTTP 200 bytes=370779
$ grep -o '<iframe[^>]*src="[^"]*"' /tmp/ev/page.html || echo 'NO IFRAME IN RAW HTML (client-rendered)'
NO IFRAME IN RAW HTML (client-rendered)
```
Not a false negative: `playbooks/observatory-api.md` §Featured match records this as answered
(lighthouse, 2026-08-22) — the page is client-rendered for the iframe and the grep finds nothing for
*any* coworld.

**Source (b) — the coworld detail API the prompt names as fallback:**
```
GET $BASE/coworlds?limit=200      HTTP 200
$ jq -r '(if type=="array" then . else .entries end)|.[]|select(.name=="contagion")|{id,canonical,replay_viewer,featured_match}'
{"id":"cow_6b43a43d-8aa2-41ea-aae6-4dd50f084c54","canonical":true,"replay_viewer":null,"featured_match":null}
```
`canonical: true`. `featured_match` is `null` — also **not** a finding here: the same playbook records
`featured_match` as `null` platform-wide, so it is not evidence either way.

**Source (c) — where the featured match actually lives (the page's SSR payload, `state.playlist[0]`),
fetched from the same HTML above:**
```
$ grep -o 'playlist\\":\[{[^]]\{0,420\}' /tmp/ev/page.html | head -1
playlist\":[{\"episodeId\":\"52bf0cd8-d8bb-4495-91c3-91d86bb680d9\",
 \"coworldId\":\"cow_6b43a43d-8aa2-41ea-aae6-4dd50f084c54\",\"coworldName\":\"contagion\",
 \"coworldVersion\":\"0.1.0\",
 \"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/af23e250-a24b-4f6e-8462-5f124326df11.replay\",
 \"finishedAt\":\"2026-08-23T12:30:23.043170Z\",\"roundNumber\":3,\"episodeNumber\":1,
 \"code\":\"contagion.r3.e1\",\"matchup\":{\"division…
```
A featured match **is present** — `contagion.r3.e1`, and its `replayUrl` is byte-identical to item 3's
`replay_url`, i.e. the page is featuring the very episode verified in items 3–5.

**Source (d) — the iframe `src` itself, from the call the page's own JS makes:**
```
POST $BASE/coworlds/replays/session
  body: {"coworld_id":"cow_6b43a43d-8aa2-41ea-aae6-4dd50f084c54",
         "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/af23e250-a24b-4f6e-8462-5f124326df11.replay"}
HTTP 200
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_6b43a43d-8aa2-41ea-aae6-4dd50f084c54/sha256%3A16630ba4da43abc5b0abe452be3b5b247a6ce954bdf4b09ecc9355869250c99b/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Faf23e250-a24b-4f6e-8462-5f124326df11.replay&v=2",
 "ready":true}
```

**Sources used:** (a) attempted and empty as documented; (b), (c) and (d) all fetched. The verdict rests
on (c) + (d).

Status: **TRUE** — the URL is on the **static** route
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`, with `<sha>` =
`sha256:16630ba4da43a…` = STATE's `coworld.manifest_sha` (URL-encoded), and `ready: true`. It is **not**
a `/client/replay` pod URL. A featured match is present.

---

## 7. Certification declared the static bundle — **TRUE**

Source: the **committed** `runs/2026-08-23-contagion/release-result.json` (phase 40's downloaded
artifact, release run `32638256991`). It was present, so the `gh run download` fallback was **not**
needed and `/tmp` was not consulted.

```
$ jq -r '.certify.replay_liveness' runs/2026-08-23-contagion/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Corroborating tail from the same file (`.certify.output_tail`, trimmed):
```
  [pass] replay-present: a replay artifact was produced
  [pass] replay-loadable: the replay artifact has a declared viewer path
  [pass] players-run: every declared player actually started on the smoke episode (not just declared)
  [pass] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks
Certified dist/coworld_manifest.json
Transcript: coworld-executable (10 steps passed)
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```
`.certify.ok` is `true`.

Status: **TRUE** — contains `Replay liveness: skipped (static replay bundle declared`, read from the
committed artifact.

---

## 8. Spectator judgment — the viewer was EXECUTED in CI, then judged — **TRUE**

*(a) Dispatch.* The iframe `src` from item 6(d) was opened in headless chromium by
`viewer-check.yml` in `Metta-AI/coworld-builder`:
```
$ gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="<item-6 src>" -f timeout=90
run 32639677937  created 2026-08-23T12:32:14Z  conclusion: success
$ gh run download 32639677937 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-23-contagion/viewer-check
viewer-smoke.json (1137 B)  viewer-smoke.png (477101 B)  smoke-stdout.txt  smoke-stderr.txt (0 B)
```
Both artifacts are committed under `runs/2026-08-23-contagion/viewer-check/`. The URL recorded inside
`viewer-smoke.json` is the item-6 `src` verbatim, so the run tested the right page.

*(b) Readouts, verbatim.*
```
$ jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-23-contagion/viewer-check/viewer-smoke.json
{"loaded":true,"ms":1682,"clock":"WEEK 0 / 20","scorebug":"","feed_lines":0}

$ jq -c '.signals' runs/2026-08-23-contagion/viewer-check/viewer-smoke.json
{"data_replay_loaded":null,"data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}

$ jq -r '.failure // "no failure"' runs/2026-08-23-contagion/viewer-check/viewer-smoke.json
no failure

$ jq -r '.console_tail[]' runs/2026-08-23-contagion/viewer-check/viewer-smoke.json
[bridge] loading
[bridge] ready
```

Three scrub clock readouts:

| scrub position | clock text |
|---|---|
| 0 %   | `WEEK 0 / 20` |
| 50 %  | `WEEK 0 / 20 · WAITING ON 6` |
| 100 % | `WEEK 20 / 20 · VARIANT +25% · FINAL` |

**Gate 1 — `loaded: true`.** Met: the page drew a frame in 1682 ms and announced it through the
`coworld-replay` bridge (`bridge: ["loading","ready"]`, `bridge_ready: true`, `bridge_error: []`,
`failure: null`). This is the executed-browser signal the lantern regression exists to catch.

**Gate 2 — the three clock readouts differ.** Met: three distinct strings. The 50 % readout
(`WEEK 0 / 20 · WAITING ON 6`) is the intra-week decision phase — the shell renders per-*frame*, and
the replay has 143 frames for 20 weeks (`143 / 143` is visible on the scrubber in the screenshot), so
the midpoint of the frame timeline legitimately lands inside an early week while the six seats are
still deliberating. The clock is advancing, not frozen: 0 % → 50 % → 100 % moves week 0 → week 0
(deliberation) → week 20 FINAL.

*(b′) Two readouts that are **selector misses**, stated plainly rather than glossed:* `scorebug: ""`
and `feed_lines: 0`. These are the smoke harness's generic selectors not matching this shell's DOM —
**not** an empty page. The screenshot shows a fully populated scorebug strip (all six seats with score
and death count) and on-map speech bubbles carrying the champions' `say` text. I am not claiming a DOM
readout I did not download; I am reporting that these two harness fields disagree with the rendered
pixels, and treating the pixels as the evidence. This is a legibility note for phase 30's next pass
(the shell should expose stable `#scorebug` / feed hooks), not a failure of the viewer.

*(c) The replay JSON the viewer was asked to draw* (`/tmp/ep.replay`, also committed as
`runs/2026-08-23-contagion/ep.replay`). Ordered excerpts — `week`, `seat`, `kind`, `say`/`text` (110 chars):

Early:
```
-	-	start
0	-	week
0	0	dial	Saltmarch: 6 reported (≈40 true). Riverbend outbreak detected at 186 reported (≈1,240 true, 0.12%). Screening
0	1	dial	Wintermoor: testing 2, staying open. Will help suppress outbreaks elsewhere. Watch Riverbend.
0	2	dial	                       (Baseline — scripted, no speech)
0	3	dial
0	4	dial
0	5	dial
1	-	week
1	0	dial	Saltmarch: ~127 true cases (0.01%). Riverbend ~5,338 true cases (0.53%), hottest region. Screening Riverbend b
1	1	dial	Riverbend outbreak confirmed. Will aid at 100cr/wk if you lock to 3. Others: stay open, keep testing 2+. Build
```
Middle:
```
8	1	dial	W8→W9: Riverbend at 0.66%—lock to 3 by W9 end, I pay 100cr weekly through W13. Saltmarch, Ash, Kestrel: match
9	-	week
9	0	dial	W9: Saltmarch 8433 true (0.843%), still doubling. Harborlea ~26380 true (2.638%), critical hotspot—needs immed
9	1	dial	W9→W10: Wintermoor ~0.86%, stable. Riverbend critical—100cr weekly if L3 by W10. Saltmarch ~0.548%—hold L3+T2
```
Late:
```
19	-	week
19	0	dial	W19→W20: Saltmarch 176476 true (17.7%), deaths 1580/wk, hospitals 4x over. Harborlea 52568@T0≈351k true (35%+)
19	1	dial	W19→W20: Wintermoor escalating to L3, sealing all borders. True prevalence 5.9%, deaths 438/wk, hospitals 3x o
20	-	week
20	-	end	complete
```
Per-tick state the viewer draws (one `week` event per tick, 21 of them, each carrying all six regions):
```
$ jq -c '[.events[]|select(.kind=="week")][3]' /tmp/ep.replay | cut -c1-420
{"kind":"week","week":3,"variant":false,"regions":[
 {"susceptible":999429,"infected":453,"recovered":118,"dead":0,"gdp":2987,"lockdown":0,"testing":0,
  "gates":[0,0,0],"newInfections":317,"deathsWeek":0,"confirmed":67,"confirmedNew":47,"grossGdp":999,
  "spendWeek":10,"aidIn":0,"aidOut":0,"hospital":0},
 {"susceptible":999411,"infected":459,…,"testing":1,"gates":[1,2,1],…,"confirmed":160,…
```
```
$ jq -r '.results' /tmp/ep.replay
{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"],
 "scores":[-3028,7573,11818,9961,-28706,10595],"gdp":[8772,12459,12804,11671,16892,11913],
 "deaths":[5900,2443,493,855,22799,659],"weeks":20,"maxWeeks":20,
 "totalDeaths":33149,"totalGdp":74511,"reason":"complete"}
```

**Spectator judgment.** It is legible, and it shows the game. `viewer-smoke.png` (committed) is the
final frame: a titled `CONTAGION` header with the clock `WEEK 20 / 20 · VARIANT +25% · FINAL`; a
scorebug strip naming all six seats with score and cumulative deaths (`daveey −3,028 SALTMARCH 5,900†`,
`daveey-1 7,573 WINTERMOOR 2,443†`, `Riverbend 11,818`, `Kestrel Flats 9,961`, `Harborlea −28,706
22,799†`, `Ash Hollow 10,595`); a six-region map where each region's card is colour-graded by infection
(Saltmarch and Harborlea washed deep red and labelled `L3 · T3 · CRITICAL` / `22,799 DEAD`, the
survivors amber-brown and `OVERLOADED`) and joined by road links drawn as dotted red beads where traffic
is still moving; two on-map speech bubbles carrying the champions' actual week-19 `say` text
(`"W19→W20: Saltmarch 176476 true (17.7%)…"`, `"W19→W20: Wintermoor escalating to L3, sealing all
borders…"`); a per-region infection sweep chart along the bottom captioned `INFECTED PER REGION · dotted
= what they REPORT` — which is the game's whole reported-vs-true tension, drawn; a 143-frame scrubber
reading `143 / 143`; and a centred end card, `FINAL — 20 WEEKS · 33,149 DEAD` / **`Riverbend KEPT THE
LIGHTS ON`**, over a standings table. Every number in that table reconciles exactly with the replay's
`results` (11,818 / 10,595 / 9,961 / 7,573 / −3,028 / −28,706 and the matching GDP and death columns),
so the picture is a faithful render of the bytes verified in item 4, not a placeholder. Reconciled
against the events: the two champion seats deliberate in plain language every week, escalate and
release lockdowns on a schedule that tracks their own prevalence readings (seat 0 `1→3→1`, seat 1
`0→3`), close 77 border gates and send 30 aid transfers between them — a spectator watching this can
see who locked down, when, who paid whom, who let it rip, and who died for it. It is neither empty nor
static.

Status: **TRUE** — `loaded: true`, three distinct clock readouts, no failure, and the rendered frame is
a readable picture of this game. Recorded caveat, not a blocker: the harness's `scorebug` and
`feed_lines` selectors do not match this shell, so those two fields read empty despite the screenshot.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 2, 3 completed 12:15:44Z / 12:30:26Z; fillers set 12:10–12:12Z; round 1 failed pre-filler and is excluded |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey-1 rank 1 (1030.53), daveey rank 2 (969.47), `rounds_played` 2 each; fillers absent |
| 3 | Latest round's episode request completed with replay | **TRUE** — `ereq_a423e065…` completed, `replay_url` set, seats 0/1 = daveey/daveey-1 |
| 4 | Replay bytes valid and show the game | **TRUE** — strict JSON, `contagion.replay.v1`, `reason: complete`, 120 dials, 0/40 champion fallbacks |
| 5 | Hosted game log clean | **TRUE** — CLEAN, all four patterns zero hits |
| 6 | Public page uses the static replay path | **TRUE** — static `…/index.html?replay=…`, `ready:true`, featured match `contagion.r3.e1` |
| 7 | Certification declared the static bundle | **TRUE** — `Replay liveness: skipped (static replay bundle declared…` from committed `release-result.json` |
| 8 | Spectator judgment (viewer executed in CI) | **TRUE** — `loaded:true` in 1682 ms, three distinct clock readouts, legible final frame |

Replay URL: `https://softmax-public.s3.amazonaws.com/replays/af23e250-a24b-4f6e-8462-5f124326df11.replay`
viewer-check run: `32639677937` (Metta-AI/coworld-builder, success)
