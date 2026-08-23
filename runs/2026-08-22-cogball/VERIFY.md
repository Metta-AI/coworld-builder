# VERIFY — cogball   (2026-08-23T06:08:10Z)

Verdict: **1 item false** — checks 1–7 TRUE, **check 8 FALSE** (the hosted static viewer never
draws a frame: `[pageerror] COG_BASE is not defined`, three independent CI load tests).

Run: `2026-08-22-cogball` · coworld `cow_5d14a55f-2647-49fa-95d4-7b37a7463da5` v0.1.3 ·
league `league_e87130ef-ecc6-49d4-9bc1-4014b7141df5` · division `div_45c40cad-ef84-4d48-a733-59e55f80e24c`.
Every fetch below was made fresh during this phase-60 pass (05:43Z–06:08Z), except item 7, whose
evidence is by design the committed `runs/2026-08-22-cogball/release-result.json` (documented
exception in `prompts/60-verify.md` §7). Headers sent on Observatory calls:
`Authorization: Bearer …` and `User-Agent: coworld-builder/1.0` (reads), plus
`X-Use-Elevated-Privileges: true` on `artifacts/logs`. No header values are printed anywhere here.

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

Fillers (`cogball-formation:v2` = `7c11dd63-d0a2-465d-9e71-9e02de0136eb`, `cogball-swarm:v2` =
`259d11a4-7ebc-4d0e-a704-6769a1a7b527`) were registered **before** the first `trigger-round`
(`log.md`, `2026-08-23T05:42:09Z 50 fillers 200: formation:v2 + swarm:v2 registered BEFORE trigger`).
Round 1 is the first round this league ever ran, so every completed round is "after fillers".

```
GET https://softmax.com/api/observatory/v2/rounds?league_id=league_e87130ef-ecc6-49d4-9bc1-4014b7141df5&limit=20
jq -r '[.entries[]|select(.status=="completed")]|length'
```
```
2
```
```
jq -c '.entries[]|{id,round_number,status,error,created_at,completed_at}'
```
```json
{"id":"round_4af4bfff-8c80-4277-9d28-4f3b4fa9e3ae","round_number":2,"status":"completed","error":null,"created_at":"2026-08-23T05:56:00.929105Z","completed_at":"2026-08-23T05:59:16.029721Z"}
{"id":"round_c8f6ad75-e6cd-4088-87e3-5aa9de3a7d67","round_number":1,"status":"completed","error":null,"created_at":"2026-08-23T05:41:00.599305Z","completed_at":"2026-08-23T05:44:06.458180Z"}
```

`round_config.entrant_attributions` on round 2 (excerpt) shows the champion version ids seated:

```json
{"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player","policy_version_id":"0f2edcb1-15cb-4410-a4c6-6042870467d9","league_policy_membership_id":"lpm_c8a63ff9-fbaa-47cf-ad51…"}
```

Status: **TRUE** — rounds 1 and 2 both `completed` (05:44:06Z and 05:59:16Z), zero `failed` and
zero `discarded` rows, `error: null` on both. Ordering evidence for "after the fillers were set":
(i) `log.md`'s phase-50 lines record the filler POST returning 200 with exactly
`formation:v2 + swarm:v2` **before** the `trigger-round` POST, and (ii) round 1 (`created_at`
`2026-08-23T05:41:00.599305Z`) is the **first round this league ever ran** and it settled
`completed`, which is only possible with fillers already registered — a `trigger-round` issued
before any filler exists fails instantly with `Temporal RoundWorkflow failed before settling the
round` (`playbooks/observatory-api.md` §6). (The phase-50 `log.md` lines all carry the batch
write-time stamp 05:42:09Z, so they order the calls but do not time them individually.)

---

## 2. Both champions ranked, fillers absent/Baseline — **TRUE**

```
GET https://softmax.com/api/observatory/v2/divisions/div_45c40cad-ef84-4d48-a733-59e55f80e24c/leaderboard
jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey	cogball-total:v2	1030.5304984710244	2	2.0
2	daveey-1	cogball-counter:v2	969.4695015289755	2	0.0
```

Raw rows (bare list, not `.entries`):

```json
{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1030.5304984710244,"score_label":"Elo","score_value_type":"integer","rounds_played":2,"episode_wins":2.0,"episodes_played":null,"win_rate":1.0,"policy_label":"cogball-total:v2","recent_rounds":null}
{"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":969.4695015289755,"score_label":"Elo","score_value_type":"integer","rounds_played":2,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"cogball-counter:v2","recent_rounds":null}
```

Status: **TRUE** — `daveey` (`cogball-total:v2`, rank 1, Elo 1030.53, `rounds_played` 2) and
`daveey-1` (`cogball-counter:v2`, rank 2, Elo 969.47, `rounds_played` 2) are both present with
`rounds_played ≥ 1`. The leaderboard has exactly two rows: neither filler
(`cogball-formation:v2`, `cogball-swarm:v2`) appears, and no `Baseline (N)` row appears — the
"fillers absent" branch of the requirement.

---

## 3. Latest round's episode request completed with a replay — **TRUE**

```
R=round_4af4bfff-8c80-4277-9d28-4f3b4fa9e3ae      # max_by(.round_number) over completed rounds
GET https://softmax.com/api/observatory/v2/episode-requests?round_id=$R&limit=20
jq -c '.entries[]|{id,status,created_at}'
```
```json
{"id":"ereq_7edaf74a-af2a-4d7b-b3a5-f057e970f2a3","status":"completed","created_at":"2026-08-23T05:56:01.228576Z"}
```
```
GET https://softmax.com/api/observatory/v2/episode-requests/ereq_7edaf74a-af2a-4d7b-b3a5-f057e970f2a3
jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/96be8156-bac3-468f-8674-e8b10cb36a98.replay",
  "participants": [
    {
      "position": 0,
      "kind": "policy",
      "policy_version_id": "0f2edcb1-15cb-4410-a4c6-6042870467d9",
      "policy_id": "eb27b953-1b61-41c9-a26b-94b8345c55ae",
      "policy_name": "cogball-total",
      "version": 2,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": false
    },
    {
      "position": 1,
      "kind": "policy",
      "policy_version_id": "40f864bb-d07c-4ae3-a96d-1e08fb5491e9",
      "policy_id": "b86015e4-1294-4d29-becd-c8657fd2cd66",
      "policy_name": "cogball-counter",
      "version": 2,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
      "player_name": "daveey-1",
      "is_filler": false
    }
  ],
  "participant_scores": [
    {"position": 0, "score": 0.833},
    {"position": 1, "score": 0.167}
  ]
}
```

Status: **TRUE** — `status: "completed"`, non-null `replay_url`, participants are exactly
`daveey` (`cogball-total` v2, `is_filler: false`) and `daveey-1` (`cogball-counter` v2,
`is_filler: false`). Both champion `policy_version_id`s match STATE.

---

## 4. Replay bytes are valid and show the game — **TRUE**

**Documented substitution.** cogball's replay is the paintbot lineage's **binary `COWLDBAL`**
format, not JSON. The accepted design note
(`runs/2026-08-22-cogball/design.md` §"Replay bytes (self-sufficient)", lines 786–812) declares
the drop-in substitute for this check and ships `tools/replay_summary.py` (Python 3 stdlib only)
to produce a strict-UTF-8-JSON summary. That is the documented exception being exercised; the raw
`jq -e . /tmp/ep.replay` of `prompts/60-verify.md` is not applicable to a binary container.

```
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/96be8156-bac3-468f-8674-e8b10cb36a98.replay" -o /tmp/ep.replay
```
```
http=200 bytes=183788
magic: b'COWLDBAL'
size: 183788
```
```
git clone --depth 1 https://github.com/Metta-AI/cogame-cogball /workspace/scratch/verify-cogball
python3 /workspace/scratch/verify-cogball/tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .results.reason' /tmp/ep.json
jq -r '[.directives[]|select(.source=="llm")]|length' /tmp/ep.json
jq -r '.fallbacks' /tmp/ep.json
jq -r '.directives|length' /tmp/ep.json
```
```
strict UTF-8 JSON: ok
cogball/v1
complete
80
0
80
```

Header/manifest fields out of the same summary:

```
jq -r '.names, .aliases, .policyKinds, .policyLabels, .tickCount, .maxTicks, .turnTicks, .seed, .numAgents, .utf8Repairs, .fallbackAttempts, .budgetGuards, .inputRecords, .hashChain' /tmp/ep.json
```
```
["daveey","daveey-1"]
["Azure","Crimson"]
["llm","llm"]
["total","counter"]
5143          # tickCount
4800          # maxTicks
120           # turnTicks
1644370950    # seed
2             # numAgents
0             # utf8Repairs
0             # fallbackAttempts
[]            # budgetGuards
9244          # inputRecords
40f239e62045581a   # hashChain digest
```

Per-seat decision provenance — no scripted or fallback directive anywhere:

```
jq -r '[.directives[].source]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.json
jq -r '.directives|group_by(.seat)|map({seat:.[0].seat,total:length,llm:map(select(.source=="llm"))|length})' /tmp/ep.json
```
```json
{"llm": 80}
[{"seat":0,"total":40,"llm":40},{"seat":1,"total":40,"llm":40}]
```

One directive in full, showing non-trivial content (note + intents + says):

```json
{"turn":10,"seat":0,"alias":"Azure","source":"llm","latency_ms":2518,"note":"AZ-1 closest (3.09m), in their half - shoot. AZ-3 support intercept. AZ-2 keeps arc at y≈-0.5 (ball y third).","intents":["shoot","hold","intercept"],"says":["Strike!","Arc guard","Support ready"]}
```

Status: **TRUE** — the summary parses under a strict UTF-8 JSON parser; `protocol` is
`cogball/v1`, matching the manifest; `results.reason` is `complete` (not even the
declared-acceptable `deadline`); 80 of 80 directives are `source == "llm"`, 40 per champion seat,
`fallbacks: 0`, `fallbackAttempts: 0`, `utf8Repairs: 0`. Fallbacks are not merely a small
minority — there are none.

---

## 5. Hosted game log is clean — **TRUE**

```
GET https://softmax.com/api/observatory/v2/episode-requests/ereq_7edaf74a-af2a-4d7b-b3a5-f057e970f2a3/artifacts/logs
     (headers: Authorization, User-Agent, X-Use-Elevated-Privileges)
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' || echo CLEAN
```
```
http=200 bytes=173135
CLEAN
```

The log really is the episode's (four containers, 173 135 bytes) — head and tail:

```
===== container: coworld-init-config =====
b''

===== container: bedrock-sidecar =====
b'2026-08-23 05:56:10,511 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1","has_role_arn":true,"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar","episode_request_id":"7edaf74a-af2a-4d7b-b3a5-f057e970f2a3","job_request_id":"96be8156-bac3-468f-8674-e8b10cb36a98","role":"game","slot":"game",…
```
```
===== container: game =====
b'seed not pinned; randomized\ncogball config: host=0.0.0.0 port=8080 seed=1644370950 num_agents=2 minPlayers=2 maxTicks=4800 turnTicks=120 turnBudgetMs=9000 wallClockBudgetSeconds=690 fastMode=true\nstarting cogball on 0.0.0.0:8080\nboard render caches baked in 118 ms…\ncogball llm: bedrock transport, url http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke\nwaiting for players: 0/2, need 2 more\nplayer connected: daveey\nplayer joined: daveey as Azure\nplayer connected: daveey-1\nplayer joined: daveey-1 as Crimson\nwaiting for players: 2/2, need 0 more\ngame starting in 1\nmatch start, kickoff for seat 0…
```
```
…en: /coworld/events.json (4771 events)\nResults: {"names":["daveey","daveey-1"],"scores":[0.833,0.167],"win":[true,false],"team":["azure","crimson"],"goals":[2,0],"shots":[8,1],"shotsOnTarget":[6,0],"saves":[0,0],"possessionTicks":[2530,1643],"llmTurns":[40,40],"fallbackTurns":[0,0],"reason":"complete","endRule":"full_time","finalTick":5142,"seed":1644370950}\n'

===== container: worker =====
b''
```

Status: **TRUE** — grep over all four containers returns no match for any of
`falling back`, `LLM provider is unavailable`, `cut off at max_tokens`, `rejected`; the guard
printed `CLEAN`. No capacity exception needed — no `LLM provider is unavailable` line exists, so
no cross-check against another LLM coworld was required. The log's own results line corroborates
`fallbackTurns: [0,0]` and `reason: "complete"`.

(The same grep on round 1's episode `ereq_ee58be1e-592f-4f03-8e9c-27f3a38edbed` also returned
`CLEAN`, 174 013 bytes — recorded in `log.md` at 05:45:29Z.)

---

## 6. The public page uses the static replay path — **TRUE**

**Source A — raw-HTML grep of the human page (the prompt's first command):**

```
curl -sS "https://softmax.com/cogball" | grep -o '<iframe[^>]*src="[^"]*"'
```
```
http=200 bytes=339043
(no match — raw-HTML grep empty)
```
Not a false negative: the page is client-rendered for the iframe, as `playbooks/observatory-api.md`
§Featured match / replay route records (lighthouse run, 2026-08-22).

**Source B — the `/coworlds` fallback the prompt names:**

```
GET https://softmax.com/api/observatory/v2/coworlds?limit=200
jq -r '…|select(.name=="cogball" and .canonical==true)|{id,canonical,version,replay_viewer,featured_match}'
```
```json
{
  "id": "cow_5d14a55f-2647-49fa-95d4-7b37a7463da5",
  "name": "cogball",
  "canonical": true,
  "version": "0.1.3",
  "replay_viewer": null,
  "featured_match": null
}
```
`featured_match: null` here is the documented platform-wide behaviour (same playbook section), not
evidence of absence.

**Source C — the page's server-rendered playlist (`state.playlist[0]`), which is where the
featured match actually lives.** Excerpt from the same 339 043-byte fetch of
`https://softmax.com/cogball` (backslash-escaped quotes unescaped for legibility):

```json
"playlist":[{"episodeId":"976ee33a-f035-4e39-b5b5-d8a0db4caa13","coworldId":"cow_5d14a55f-2647-49fa-95d4-7b37a7463da5","coworldName":"cogball","coworldVersion":"0.1.3","replayUrl":"https://softmax-public.s3.amazonaws.com/replays/96be8156-bac3-468f-8674-e8b10cb36a98.replay","finishedAt":"2026-08-23T05:59:05.786295Z","roundNumber":2,"episodeNumber":1,"code":"cogball.r2.e1","matchup":{"divisionId":"div_45c40cad-ef84-4d48-a733-59e55f80e24c","divisionName":"Competition","first":{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1030.5304984710244,"score_label":"Elo","rounds_played":2,"episode_wins":2,"win_rate":1,"policy_label":"cogball-total:v2"},"second":{"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":969.4695015289755,"score_label":"Elo","rounds_played":2,"episode_wins":0,"win_rate":0,"policy_label":"cogball-counter:v2"}},"inspectUrl":"/observatory/v2?tab=episode-requests&detail=episode-request:ereq_7edaf74a-af2a-4d7b-b3a5-f057e970f2a3","outcome":"first"}]
```

**Source D — the call the page's own JS makes to build the iframe `src`:**

```
POST https://softmax.com/api/observatory/v2/coworlds/replays/session
  {"coworld_id":"cow_5d14a55f-2647-49fa-95d4-7b37a7463da5",
   "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/96be8156-bac3-468f-8674-e8b10cb36a98.replay"}
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_5d14a55f-2647-49fa-95d4-7b37a7463da5/sha256%3Ad488cc06f91a8038667c6b4452031d436b889f5577f65819afc3455b8aa82ccd/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F96be8156-bac3-468f-8674-e8b10cb36a98.replay&v=2",
  "ready": true
}
```

Status: **TRUE**. Source used: the raw-HTML grep was **empty**, so the verdict rests on sources
C and D (plus B for the null-`featured_match` disclaimer). A **featured match is present** —
`state.playlist[0]` is `cogball.r2.e1`, `daveey` vs `daveey-1`, both ranked. The iframe `src` is
the **static** route
`…/v2/coworlds/replays/static/cow_5d14a55f-2647-49fa-95d4-7b37a7463da5/sha256%3Ad488cc06…/index.html?replay=<s3 url>`
with `ready: true`; `<sha>` is the coworld's manifest hash
(`sha256:d488cc06f91a8038667c6b4452031d436b889f5577f65819afc3455b8aa82ccd`, matching
`STATE.coworld.manifest_sha`), and no `/client/replay` pod URL appears anywhere in the response.

---

## 7. Certification declared the static bundle — **TRUE**

Source read: **the committed `runs/2026-08-22-cogball/release-result.json`** (phase 40's
downloaded artifact from release run `32620306477`). It was present, so no
`gh run download` re-fetch was needed.

```
$ git log --oneline -1 -- runs/2026-08-22-cogball/release-result.json
d0c9cab 40 done: cogame-cogball 0.1.3 canonical+certified (run 32620306477); phase -> 50
$ git status --porcelain runs/2026-08-22-cogball/release-result.json
(clean: file is the committed copy, unmodified)

$ jq -r '.certify.replay_liveness' runs/2026-08-22-cogball/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Surrounding certifier transcript from the same file (`.certify.output_tail`, trimmed):

```
  [pass] replay-present: a replay artifact was produced
  [pass] replay-loadable: the replay artifact has a declared viewer path
  [pass] players-run: every declared player actually started on the smoke episode (not just declared)
  [pass] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks
Certified dist/coworld_manifest.json
Transcript: coworld-executable (10 steps passed)
…
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
…
Inspect replay: open …/replay in your static replay viewer bundle (see STATIC_REPLAY_VIEWERS.md)
```

Status: **TRUE** — the string `Replay liveness: skipped (static replay bundle declared` is present
verbatim, and `.certify.ok` is `true` with all 10 transcript steps passed.

---

## 8. Spectator judgment — the viewer is EXECUTED, then judged — **FALSE**

### (a) The dispatched load tests

Three attempts, three different approaches, all against `Metta-AI/coworld-builder`'s
`viewer-check.yml` (headless chromium, Playwright 1.55.0):

| # | run id | URL under test | timeout | result |
|---|---|---|---|---|
| 1 | `32621157957` | round **1** replay `f349754c-…`, `&v=2` | 90 s | red — `loaded:false` |
| 2 | `32621806164` | round **2** replay `96be8156-…` (the featured match), `&v=2` | 180 s | red — `loaded:false` |
| 3 | `32621978248` | round **2** replay `96be8156-…`, **no** `&v=2` (bare prompt-form route) | 120 s | red — `loaded:false` |

Attempt 2 is the committed evidence (`runs/2026-08-22-cogball/viewer-check/`), because its URL is
the live iframe `src` from check 6. Attempts 1 and 3 are kept alongside as
`viewer-smoke-attempt1-round1.json` and `viewer-smoke-attempt3-no-v2.json`.

```
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder \
  -f url='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_5d14a55f-2647-49fa-95d4-7b37a7463da5/sha256%3Ad488cc06f91a8038667c6b4452031d436b889f5577f65819afc3455b8aa82ccd/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F96be8156-bac3-468f-8674-e8b10cb36a98.replay&v=2' \
  -f timeout=180
gh run watch 32621806164 -R Metta-AI/coworld-builder --exit-status   # X Process completed with exit code 1
gh run download 32621806164 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-22-cogball/viewer-check
```

### (b) The readouts

```
$ jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-22-cogball/viewer-check/viewer-smoke.json
{"loaded":false,"ms":180107,"clock":"0:00 IN THE LOCKER ROOM","scorebug":"0:00 IN THE LOCKER ROOM","feed_lines":0}

$ jq -c '.signals' runs/2026-08-22-cogball/viewer-check/viewer-smoke.json
{"data_replay_loaded":null,"data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}

$ jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-22-cogball/viewer-check/viewer-smoke.json
(scrub array is EMPTY — no readouts at all)

$ jq -r '.failure // "no failure"' runs/2026-08-22-cogball/viewer-check/viewer-smoke.json
timeout: no data-replay-loaded="true" and no coworld-replay "ready" within 180s

$ jq -r '.console_tail[]' runs/2026-08-22-cogball/viewer-check/viewer-smoke.json
[pageerror] COG_BASE is not defined
```

Full `smoke-stderr.txt` from the same artifact:

```
VIEWER SMOKE FAILED: timeout: no data-replay-loaded="true" and no coworld-replay "ready" within 180s
  url        : https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_5d14a55f-…/index.html?replay=…96be8156-….replay&v=2
  elapsed    : 180107 ms
  signals    : data-replay-loaded=null data-replay-error=null bridge=[none]
  #clock     : "0:00 IN THE LOCKER ROOM"
  #scorebug  : "0:00 IN THE LOCKER ROOM"
  status     : "CONNECTING"
  #loading   : null
  last 30 console messages:
    [pageerror] COG_BASE is not defined
```

**Clock readouts (0 % / 50 % / 100 %):**

| position | clock |
|---|---|
| 0 % | *(none — the shell exposes no `#scrub`; `scrub: []`, and the page never loaded anyway)* |
| 50 % | *(none)* |
| 100 % | *(none)* |

`#clock` and `#scorebug` were sampled and both read `0:00 IN THE LOCKER ROOM` for the whole
180 s — a frozen pre-match placeholder, never a running M:SS over 3:20.

**Both of item 8's conditions fail:** `loaded` is `false` (condition 1 — "`loaded: false` is
check 8 FALSE, full stop"), and there are no three differing clock readouts (condition 2).

### The root cause (diagnosis, fetched — not inferred)

Every asset in the static bundle is present and healthy, which is exactly why the fetch-only
version of this check could not have caught it:

| asset | HTTP | bytes | content-type |
|---|---|---|---|
| `index.html` | 200 | 144 573 | `text/html; charset=utf-8` |
| `wire_constants.js` | 200 | 153 | `text/javascript; charset=utf-8` |
| `chrome_common.js` | 200 | 30 637 | `text/javascript; charset=utf-8` |
| `static_replay.js` | 200 | 9 203 | `text/javascript; charset=utf-8` |
| `static_replay_worker.js` | 200 | 7 160 | `text/javascript; charset=utf-8` |
| `broadcast_core.js` | 200 | 62 248 | `text/javascript; charset=utf-8` |
| `cogball_replay.js` | 200 | 68 784 | `text/javascript; charset=utf-8` |
| `cogball_replay.wasm` | 200 | 554 655 | `application/wasm` (magic `\0asm`) |

(`index.html` references `wire_constants.js`, `chrome_common.js`, `static_replay.js` plus one
inline `<script>`; `static_replay.js` spawns `static_replay_worker.js`, which `importScripts`
`broadcast_core.js`, `cogball_replay.js`, `wire_constants.js`; `cogball_replay.js`'s emscripten
loader names `cogball_replay.wasm`.)

The defect is in the shell's single inline `<script>` (`index.html` lines 1624–2742, built from
the repo's `client/replay_broadcast.html`):

```
$ grep -n 'COG_BASE' index.html
1719:    // from COG_BASE: native "<prefix>/client" + "/art/lockerroom", static
1721:    var artBase = COG_BASE + '/art/lockerroom';

$ cd /workspace/scratch/verify-cogball && grep -rn "COG_BASE" .
./client/replay_broadcast.html:1719:    // from COG_BASE: native "<prefix>/client" + "/art/lockerroom", static
./client/replay_broadcast.html:1721:    var artBase = COG_BASE + '/art/lockerroom';
```

`COG_BASE` is **never assigned anywhere in the repository or in any bundle asset** — the only two
hits are the comment and the use. The `buildLockerRoom()` IIFE at line 1714 therefore throws
`ReferenceError: COG_BASE is not defined` during initial execution, which aborts the remainder of
that one inline script — including the wiring that would call
`window.CogballStaticReplay.createCore(...).start()`. Nothing ever creates the Worker, nothing
ever fetches the replay, and `static_replay.js:144`
(`document.documentElement.setAttribute('data-replay-loaded','true')`) is never reached.

Also worth recording against the brief: **there is no `coworld-replay` postMessage bridge in this
bundle at all** —

```
$ grep -c 'coworld-replay' index.html static_replay.js chrome_common.js static_replay_worker.js broadcast_core.js cogball_replay.js
index.html:0
static_replay.js:0
chrome_common.js:0
static_replay_worker.js:0
broadcast_core.js:0
cogball_replay.js:0

$ grep -n 'data-replay-loaded' static_replay.js
144:          document.documentElement.setAttribute('data-replay-loaded', 'true');
```

so the *only* ready signal cogball implements is `data-replay-loaded`, and that one is
unreachable behind the ReferenceError. (`tell("ready")` does not exist in this bundle.)

### (c) The replay JSON — what the viewer was asked to draw

From `/tmp/ep.json` (the `replay_summary.py` rendering of `/tmp/ep.replay`, per the design note's
substitution; cogball's summary exposes `.directives[]`, not `.events[]`).

```
$ jq -r '.directives[]|[.turn,.seat,.source,(.note//"")]|@tsv' /tmp/ep.json | head -6      # EARLY
0	0	llm	Match start. AZ-1 closest to ball (1.5m) - chase. AZ-2 deepest - keeper on arc. AZ-3 support intercept ahead.
0	1	llm	Opening position: deep defensive shape. Keeper on goal line, back holding halfway, presser shadows nearest opponent (AZ-1 at ball).
1	0	llm	AZ-1 closest (1.5m), in opponent half near ball - shoot. AZ-2 keeper on arc covering near post. AZ-3 intercept support ahead of ball.
1	1	llm	Ball loose in midfield. AZ-1 and AZ-3 converging on it. CR-2 closest to ball at 3.15m. Maintain deep shape: keeper holds goal arc, back holds halfway defensive…
2	0	llm	AZ-1 closest to ball (2.22m), in their half - SHOOT at goal. AZ-2 keeper holds arc. AZ-3 support intercepts ahead.
2	1	llm	Ball loose at x=9.11, moving toward AZ-1 and AZ-3. CR-2 closest at 5.58m but both opponents closing fast. Maintain deep defensive shape: CR-1 keeper holds goal…
```
```
$ … | sed -n '39,44p'                                                                       # MIDDLE
19	0	llm	AZ-1 closest to ball (3.1m) on board near goal line - shoot to clear. AZ-2 keeper hold arc. AZ-3 support intercept upfield. Two goals up, maintain control.
19	1	llm	Ball loose on boards at [18.22,-11.82], moving toward our goal. AZ-1 closest (3.1m). CR-3 very close (2.25m) - CLEAR with auto kick away from penalty area. Mai…
20	0	llm	Ball on touchline (y=-12.15), AZ-1 closest (0.84m) - shoot to clear. AZ-2 keeper. AZ-3 support intercept. Two goals up, maintain pressure.
20	1	llm	Ball on boards at [18.59,-12.15], we have possession (CR-3). AZ-1 0.84m away - IMMINENT THREAT. Clear immediately with auto kick. CR-1 keeper holds goal. CR-2 …
21	0	llm	AZ-3 closest to ball (3.52m), shoot to attack. AZ-1 support intercept. AZ-2 keeper on arc. Two goals up, maintain pressure.
21	1	llm	Ball loose at [11,-6] in our half. AZ-3 closest (3.52m). Revert to compact defensive shape: keeper holds goal arc, back holds midfield, press shadows AZ-3. Win…
```
```
$ … | tail -4                                                                               # LATE
38	0	llm	AZ-1 closest to ball (1.24m), shoot at goal. AZ-3 keeper on arc. AZ-2 support intercept. Two goals up, control possession.
38	1	llm	Ball loose near opponent goal. CR-3 nearest (4.16m), closing fast. AZ-1 very close (1.24m) - likely to win it. CR-3 press AZ-1 to disrupt. CR-2 intercept upfie…
39	0	llm	Ball on boards at y=7.6, loose. AZ-2 closest (2.84m), shoot to clear. AZ-3 keeper on arc. AZ-1 support intercept upfield opposite y-side.
39	1	llm	Ball loose in our half, near boards. CR-3 closest (3.23m). AZ-2 also very close (2.84m) - danger. CR-3 must clear immediately with auto-kick to hammer it away.…
```
```
$ jq -r '.results' /tmp/ep.json
{
  "names": ["daveey", "daveey-1"],
  "scores": [0.833, 0.167],
  "win": [true, false],
  "team": ["azure", "crimson"],
  "goals": [2, 0],
  "shots": [8, 1],
  "shotsOnTarget": [6, 0],
  "saves": [0, 0],
  "possessionTicks": [2530, 1643],
  "llmTurns": [40, 40],
  "fallbackTurns": [0, 0],
  "reason": "complete",
  "endRule": "full_time",
  "finalTick": 5142,
  "seed": 1644370950
}
```

### The spectator-judgment paragraph

**The episode is a real, legible football match; the hosted viewer is not.** The recorded replay
is unambiguously the game: over 5 142 ticks and 40 turns per side, both champion seats issue LLM
directives that name the ball's coordinates, the closest robot, the keeper's arc, clears off the
touchline and counter-attacks — "AZ-1 closest (1.5m), in opponent half near ball - shoot",
"COUNTER ACTIVATED: CR-3 shoots immediately at their goal", "Two goals up, maintain pressure" —
and the match ends `full_time` 2–0 to `daveey` with 8 shots (6 on target) against 1, and
possession 2530:1643 ticks. That is football, told in the game's own vocabulary. But a spectator
opening the live iframe sees none of it. The committed `viewer-smoke.png` (1280×800, captured
after 180 s) is an almost-black brown vignette with no pitch, no ball, no robots and no scorebug
— only a centred caption "Filling hoppers with fresh paint…" (a leftover string from the paintbot
starter lineage, wrong for a football game), a thin progress bar with a small stalled amber
segment, and the footer "BOT LOCKER ROOM · LOADING REPLAY". The `#clock` and `#scorebug` elements
both read the frozen placeholder `0:00 IN THE LOCKER ROOM`; the feed is empty (`feed_lines: 0`);
no scrubber exists to sample, and no frame is ever drawn. Reconciled against the replay above,
the picture shows **zero percent** of the recorded match. This is not a legibility nit — it is the
cogame-lantern failure mode verbatim: every asset 200 and healthy, and the page nonetheless hangs
forever on its loading curtain, here because `client/replay_broadcast.html:1721` dereferences an
undefined `COG_BASE` and takes the whole bootstrap down with it. **Item 8 is FALSE.**

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** (rounds 1 & 2) |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** |
| 3 | Latest round's episode request completed with replay | **TRUE** (`ereq_7edaf74a-…`) |
| 4 | Replay bytes valid and show the game | **TRUE** (`cogball/v1`, `complete`, 80/80 llm, 0 fallbacks) |
| 5 | Hosted game log clean | **TRUE** (`CLEAN`) |
| 6 | Public page uses the static replay path | **TRUE** (static route, `ready:true`, featured match present) |
| 7 | Certification declared the static bundle | **TRUE** (committed `release-result.json`) |
| 8 | Spectator judgment — viewer executed and legible | **FALSE** — `loaded:false` × 3 runs, `COG_BASE is not defined` |

Retry budget for check 8: **3 of 3 attempts spent**, each a distinct approach (different replay,
different timeout, URL with and without the `&v=2` cache-buster). The failure is deterministic and
identical every time. Per `prompts/60-verify.md` §Retry budget this goes to the coordinator naming
check 8 and the evidence above; the fix is one line in `client/replay_broadcast.html` (define
`COG_BASE` — `'.'` for the static bundle, `'<prefix>/client'` for the native pod route) followed
by a re-release, which is phase 20/40 work, not the verifier's.
