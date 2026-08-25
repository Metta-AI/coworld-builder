# VERIFY — factory-commons (Observatory `game.name` = `factory_commons`)   (2026-08-25T22:56Z)

Verdict: **all-true (8/8)**

Run: `2026-08-25-factory-commons` · coworld `cow_2e5dc1a2-c660-4c7b-83a1-3881b4071786` v0.1.1 ·
league `league_96744093-0ddc-42dc-b5bf-79f195f062f0` · division `div_8b8d506b-926f-4633-bc3d-ce6dc08a2568`.

**Name resolution, recorded as instructed.** The Observatory registered the coworld under its
`game.name` `factory_commons` (underscore) — `GET /coworlds` returns `"name": "factory_commons"`.
But the **public page** is the hyphen slug: `https://softmax.com/factory-commons` returns the real
coworld page (`<title>Factory Commons · Softmax</title>`, 553 460 bytes, SSR playlist present) while
`https://softmax.com/factory_commons` returns the generic watch shell
(`<title>Watch · Softmax</title>`, 18 492 bytes, no playlist). Every API filter in this document
matched on `factory_commons`; the page used in check 6 is `factory-commons`.

All calls below:

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")   # value never printed
ELEV=(-H "X-Use-Elevated-Privileges: true")
```

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end | map({id,round_number,status,error,created_at,completed_at})'
```

Fetched 2026-08-25T22:54:28Z:

```json
[
  {
    "id": "round_a07321b3-f155-4ca7-b55c-0c2e317f8f0d",
    "round_number": 5,
    "status": "pending",
    "error": null,
    "created_at": "2026-08-25T22:50:26.756427Z",
    "completed_at": null
  },
  {
    "id": "round_bdcaab17-d5ea-4dba-bb65-7c8f0b963e61",
    "round_number": 4,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-25T22:35:26.313440Z",
    "completed_at": "2026-08-25T22:49:14.432047Z"
  },
  {
    "id": "round_3c3032b4-7162-4e84-afef-89deac4c3e46",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-25T22:20:25.113200Z",
    "completed_at": "2026-08-25T22:23:29.766944Z"
  },
  {
    "id": "round_c691a963-83bc-40c6-9ea8-267c08aaaa05",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-25T22:05:24.189810Z",
    "completed_at": "2026-08-25T22:12:11.341097Z"
  },
  {
    "id": "round_0c976430-f30c-411e-83b3-76f14bddce38",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-25T22:05:00.650435Z",
    "completed_at": "2026-08-25T22:05:00.905505Z"
  }
]
```

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end | [.[]|select(.status=="completed")]|length'
```
```
3
```

**Status: TRUE — three completed rounds: 2 (`round_c691a963…`, completed 22:12:11Z),
3 (`round_3c3032b4…`, 22:23:29Z), 4 (`round_bdcaab17…`, 22:49:14Z).**

Round 1 (`round_0c976430…`) is `failed`; its `error` verbatim is
`"Temporal RoundWorkflow failed before settling the round."` — the documented signature of a
trigger-round issued before any filler policy exists (`playbooks/observatory-api.md` §6). It does
not count; `log.md` records it as scheduled pre-fillers.

Fillers were registered in phase 50 (`log.md` line: `2026-08-25T22:08:38Z 50 fillers POST 200:
steward:v2 a2b2de4d-…, stripper:v2 f1071ff6-…`). Rounds **3** (created 22:20:25Z) and **4**
(created 22:35:26Z) were both *created* after that write, so the ≥2 requirement is satisfied even
under the strictest reading; round 2 (created 22:05:24Z, one round-scheduler tick earlier) also
completed and also seated a filler. The fillers are confirmed live and confirmed applied:

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}" | jq .
```
```json
{
  "filler_policy_versions": [
    {"policy_version_id": "a2b2de4d-7127-4b05-b309-121ce2e5b381", "policy_name": "factory-commons-steward",
     "version": 2, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"},
    {"policy_version_id": "f1071ff6-212d-4146-949b-ed297dd69b0b", "policy_name": "factory-commons-stripper",
     "version": 2, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"}
  ]
}
```

and each completed round's episode seated one of them with `is_filler: true` (round 2 → steward,
round 3 → stripper, round 4 → steward; see check 3 and the round-3 excerpt there).

---

## 2. Both champions ranked, fillers absent — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```

Fetched 2026-08-25T22:54:28Z (bare list, not `.entries`):

```
1	daveey-1	factory-commons-custodian:v2	1014.6658413353916	3	2.0
2	daveey	factory-commons-foreman:v2	985.3341586646084	3	1.0
```

Raw:

```json
[{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
  "score":1014.6658413353916,"score_label":"Elo","rounds_played":3,"episode_wins":2.0,
  "win_rate":0.6666666666666666,"policy_label":"factory-commons-custodian:v2"},
 {"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
  "score":985.3341586646084,"score_label":"Elo","rounds_played":3,"episode_wins":1.0,
  "win_rate":0.3333333333333333,"policy_label":"factory-commons-foreman:v2"}]
```

**Status: TRUE — `daveey` (`factory-commons-foreman:v2`, rank 2, rounds_played 3) and `daveey-1`
(`factory-commons-custodian:v2`, rank 1, rounds_played 3) are both ranked, each ≥ 1 round.
The two filler policies (`factory-commons-steward:v2`, `factory-commons-stripper:v2`) are absent
from the board entirely — exactly 2 rows.**

---

## 3. Latest completed round's episode request completed with a replay — **TRUE**

```bash
R=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
    | jq -r 'if type=="array" then . else .entries end | [.[]|select(.status=="completed")]|max_by(.round_number).id')
# R=round_bdcaab17-d5ea-4dba-bb65-7c8f0b963e61   (round 4)
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}" | jq -r '.entries|map({id,status,replay_url})'
```
```json
[
  {
    "id": "ereq_558ec460-76a1-462c-b404-3f750648092f",
    "status": "completed",
    "replay_url": "https://softmax-public.s3.amazonaws.com/replays/83ef5ad4-38b7-47a2-83e2-1694de64d1e7.replay"
  }
]
```

```bash
curl -sS "$BASE/episode-requests/ereq_558ec460-76a1-462c-b404-3f750648092f" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/83ef5ad4-38b7-47a2-83e2-1694de64d1e7.replay",
  "participants": [
    {"position": 0, "kind": "policy", "policy_version_id": "125a9727-5a75-4f3b-aff8-b7377043ac7a",
     "policy_name": "factory-commons-foreman", "version": 2,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "is_filler": false, "is_seed": false},
    {"position": 1, "kind": "policy", "policy_version_id": "561c148e-2c57-47d2-8179-e872ab7f4d56",
     "policy_name": "factory-commons-custodian", "version": 2,
     "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
     "is_filler": false, "is_seed": false},
    {"position": 2, "kind": "policy", "policy_version_id": "a2b2de4d-7127-4b05-b309-121ce2e5b381",
     "policy_name": "factory-commons-steward", "version": 2,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "is_filler": true, "is_seed": false}
  ],
  "participant_scores": [
    {"position": 0, "score": 0.0},
    {"position": 1, "score": 71.0},
    {"position": 2, "score": 18.0}
  ]
}
```

**Status: TRUE — `status == "completed"`, non-null `replay_url`, and the participants name
`daveey` (foreman, seat 0) and `daveey-1` (custodian, seat 1); seat 2 is the filler
`factory-commons-steward` with `is_filler: true` (rendered as `Baseline` in `results.names`,
check 4).**

For completeness, the *previous* completed round (3, `round_3c3032b4…`) seated the other filler:

```bash
curl -sS "$BASE/episode-requests/ereq_c415d0f9-9b29-4eba-9848-6cab8a583a9e" "${AUTH[@]}" \
 | jq -c '[.participants[]|{position,policy_name,player_name,is_filler}]'
```
```json
[{"position":0,"policy_name":"factory-commons-foreman","player_name":"daveey","is_filler":false},
 {"position":1,"policy_name":"factory-commons-custodian","player_name":"daveey-1","is_filler":false},
 {"position":2,"policy_name":"factory-commons-stripper","player_name":"daveey","is_filler":true}]
```

---

## 4. Replay bytes are valid and show the game — **TRUE**

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/83ef5ad4-38b7-47a2-83e2-1694de64d1e7.replay" -o /tmp/ep.replay
```
```
http=200 bytes=200972
```

```bash
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol' /tmp/ep.replay
jq -r '.results.reason, .results.ending' /tmp/ep.replay
jq -r '.frames|length' /tmp/ep.replay
```
```
strict UTF-8 JSON: ok
factory_commons.replay.v1
complete
shift_limit
900
```

`protocol` matches the manifest's declared replay protocol (`factory_commons.replay.v1`,
design.md §Sim module / §Packaging `game.protocols.global`). `results.reason == "complete"` — no
`deadline` exception is needed.

```bash
jq -c '.results' /tmp/ep.replay
```
```json
{"names":["daveey","daveey-1","Baseline"],"aliases":["Bolt","Cotter","Ratchet"],
 "scores":[0,71,18],"win":[false,true,false],"eaten":[0,71,18],"banked":[0,0,0],
 "presses":[15,1,10],"strips":[0,0,0],"repairs":[2,0,4],"misfeeds":[1,2,0],
 "fallbacks":[0,0,0],"bananas_made":91,"bananas_rotted":0,"bananas_spoiled":0,
 "integrity_final":78,"cap_final":100,"band_final":"PRIME","mode_final":"unset",
 "scrapped_by":-1,"shifts":15,"reason":"complete","ending":"shift_limit"}
```

Decisions are LLM, not scripted, and not fallbacks:

```bash
jq -c '[.events[]|select(.k=="order")]|group_by(.seat)[]|{seat:.[0].seat, sources:(group_by(.source)|map({(.[0].source):length})|add)}' /tmp/ep.replay
jq -r '[.events[]|select(.fallback==true)]|length' /tmp/ep.replay
jq -c '[.events[].k]|group_by(.)|map({k:.[0],n:length})' /tmp/ep.replay
```
```
{"seat":0,"sources":{"llm":15}}
{"seat":1,"sources":{"llm":15}}
{"seat":2,"sources":{"scripted":15}}
0
[{"k":"blocked","n":10},{"k":"drop","n":57},{"k":"eat","n":34},{"k":"end","n":1},{"k":"fix","n":6},
 {"k":"grasp","n":67},{"k":"misfeed","n":3},{"k":"order","n":45},{"k":"press","n":26},{"k":"shift","n":15}]
```

**All 30 champion-seat decisions (15 shifts × 2 seats) came from the LLM. Fallback count = 0 of 30
— not a minority, none at all — and `results.fallbacks == [0,0,0]` agrees.** The content is
non-trivial: the seats read the machine state and change job accordingly, e.g.

```
tick   seat  say
660    2     "maintain - integrity 64"                     (scripted filler)
720    0     "maintain - integrity 75 (PRIME), cap 100. Restore before WORN threshold. Continue ops aft…"
720    1     "Shift 13: cap=100, integrity=75 (PRIME). Continuing blue ops. Bolt pink, Ratchet maintain…"
```

The events show the champion seats doing the thing the game is about — supply, press, repair:
26 `press`, 67 `grasp`, 57 `drop`, 6 `fix`, 34 `eat`, 3 `misfeed`, 10 `blocked`, 15 `shift`, 1 `end`
across 900 frames, with `cap_final == 100` (nobody stripped) and 91 bananas made.

*(Recorded for the coordinator, not a failure of this check: the previous round 2 episode
`ereq_22d6a471…` had `fallbacks: [9,13,0]` because of a platform-wide Bedrock daily-token 429 —
see check 5. Rounds 3 and 4 both show `fallbacks: [0,0,0]`; the throttle cleared.)*

---

## 5. Hosted game log is clean — **TRUE**

```bash
curl -sS "$BASE/episode-requests/ereq_558ec460-76a1-462c-b404-3f750648092f/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs4.raw
# body is python b'…' byte-string reprs under "===== container: <name> =====" headers —
# decoded with ast.literal_eval per repr before grepping (playbook §10)
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs4.txt || echo CLEAN
```
```
http=200 bytes=70082
decoded bytes 69634  lines 208  (containers: coworld-init-config, bedrock-sidecar, game, worker)
matches=0
CLEAN
```

The one `429`-matching substring in the whole decoded log is a UUID
(`"call_id":"25307bc6-5231-429f-86ca-560ff2fdc430"` on an `"ok":true,"status_code":200` sidecar
line) — not a throttle. Zero occurrences of `throttled` / `Too many tokens`.

Game-container excerpt (decoded, verbatim):

```
===== container: game =====
factory-commons: seed not pinned; randomized
factory-commons: config: host=0.0.0.0 port=8080 variant=factory-commons seed=2033110849 seats=3 shifts=15 ticksPerShift=60 eitherOr=false rustPeriod=20 stripCapLoss=16 dispensePeriod=10 minTurnSeconds=12 llmTimeoutSeconds=20
factory-commons: serving on 0.0.0.0:8080
factory-commons: seat 2 (Ratchet) connected (1/3)
factory-commons: seat 2 delivered a prompt (949 chars, scripted steward)
factory-commons: seat 0 (Bolt) connected (2/3)
factory-commons: seat 0 delivered a prompt (948 chars)
factory-commons: seat 1 (Cotter) connected (3/3)
factory-commons: seat 1 delivered a prompt (814 chars)
factory-commons: starting with 3/3 seats connected
factory-commons: llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0, url http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
factory-commons: episode timeout 1200s (assumed); the last shift must START by 647s so the episode SETTLES by 720s
factory-commons: shift 1 of 15 at 8s
factory-commons: shift 1 Bolt -> operate pink (llm) says "operate pink"
factory-commons: shift 1 Cotter -> operate blue (llm) says "Starting shift 1. Cap 100, integrity 100 (PRIME). Cooperating: operating on blue (scarcer…"
factory-commons: shift 1 Ratchet -> operate pink (scripted) says "operate pink - hopper 0/0"
…
factory-commons: shift 13 Bolt -> maintain any (llm) says "maintain - integrity 75 (PRIME), cap 100. Restore before WORN threshold. Continue ops aft…"
factory-commons: shift 14 Bolt -> operate blue (llm) says "operate blue - hopper needs blue (0/2), pink has 0. Integrity 87 PRIME, cap 100 safe. Con…"
```

**Status: TRUE — zero matches on all four patterns for the latest completed round's episode.**

### Documented platform-wide LLM cause, for the record (round 2 only)

Round 2's episode `ereq_22d6a471-191e-4036-b8c2-dfaccadc1d96` did carry throttling. Its decoded
game log:

```
factory-commons: llm: seat 0 throttled, retrying next shift: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
factory-commons: llm: seat 1 throttled, retrying next shift: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
```

(Note that this text does **not** match the four grep patterns, so the naive grep on round 2 also
returns `CLEAN` — the substance was found by reading the decoded log, not by the grep.)

Cross-check that this was platform-wide Bedrock capacity, not a defect in this coworld — two other
LLM coworlds' latest completed episodes at the same time, fetched fresh this run:

```bash
for e in ereq_bfd265c1-0256-4ba6-80e8-31e27eeb3da8   # coworld "coins",  latest completed 22:08:17Z
         ereq_88b88789-f1c5-4d60-b94f-f008e1c0a9eb ; # coworld "ecos",   latest completed 22:08:16Z
do curl -sS "$BASE/episode-requests/$e/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" \
   | grep -oc 'Too many tokens per day'; done
```
```
=== ereq_bfd265c1-0256-4ba6-80e8-31e27eeb3da8   (coins)
Too many tokens per day, please wait before trying again.
count=2   throttled x5
=== ereq_88b88789-f1c5-4d60-b94f-f008e1c0a9eb   (ecos)
Too many tokens per day, please wait before trying again.
count=2   throttled x5
```

Per `prompts/60-verify.md` check 5 the correct response was to **wait inside the 75-minute bound**
rather than conclude. That is what happened: rounds 3 (22:23:29Z) and 4 (22:49:14Z) both came back
with **zero** throttle lines and `fallbacks: [0,0,0]`. The exception is therefore not even needed
for the verdict — it is recorded only to explain round 2.

---

## 6. The public page uses the static replay path — **TRUE**

**Source used: the SSR payload of `https://softmax.com/factory-commons` plus the replay-session
call the page's own JS makes.** The raw-HTML iframe grep was tried first and found nothing, which
per `prompts/60-verify.md` check 6 and `playbooks/observatory-api.md` §Featured match is *unknown*,
not a failure (the page is client-rendered for the iframe):

```bash
curl -sS "https://softmax.com/factory-commons" | grep -o '<iframe[^>]*src="[^"]*"'
```
```
(no output)
```

The documented `/coworlds` fallback also carries no featured match — this is the known
platform-wide `null`, not a property of this coworld:

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '.entries[]|select(.name=="factory_commons")|{id,canonical,version,replay_viewer,featured_match}'
```
```json
{"id":"cow_2e5dc1a2-c660-4c7b-83a1-3881b4071786","name":"factory_commons","canonical":true,
 "version":"0.1.1","replay_viewer":null,"featured_match":null}
{"id":"cow_105eb1ff-301e-45ee-92fa-1f6bbc6e788a","name":"factory_commons","canonical":false,
 "version":"0.1.0","replay_viewer":null,"featured_match":null}
```

**The featured match is server-rendered into the page's SSR payload at `state.playlist[0]`.**
Fetched 2026-08-25T22:53Z from `https://softmax.com/factory-commons` (unescaped from the SSR
string):

```json
"playlist":[{"episodeId":"18abb3e5-f902-4aaa-aa67-ff98dbff7657",
 "coworldId":"cow_2e5dc1a2-c660-4c7b-83a1-3881b4071786",
 "coworldName":"factory_commons","coworldVersion":"0.1.1",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/83ef5ad4-38b7-47a2-83e2-1694de64d1e7.replay",
 "finishedAt":"2026-08-25T22:49:13.433272Z","roundNumber":4,"episodeNumber":1,
 "code":"factory_commons.r4.e1",
 "matchup":{"divisionId":"div_8b8d506b-926f-4633-bc3d-ce6dc08a2568","divisionName":"Competition",
  "first":{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
           "score":1014.6658413353916,"score_label":"Elo","rounds_played":3,"episode_wins":2,
           "win_rate":1,"policy_label":"factory-commons-custodian:v2"}, …
```

A featured match **is** present, it is round 4 episode 1 (`factory_commons.r4.e1` — the same
episode as checks 3 and 4), and the matchup names both ranked champions.

The iframe `src` is what the page's JS resolves it to:

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_2e5dc1a2-c660-4c7b-83a1-3881b4071786",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/83ef5ad4-38b7-47a2-83e2-1694de64d1e7.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_2e5dc1a2-c660-4c7b-83a1-3881b4071786/sha256%3Aa63d2c7fc64fd8fb0d30a5337c23bc14d0de5133d68ba01c4b562b6ee9011810/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F83ef5ad4-38b7-47a2-83e2-1694de64d1e7.replay&v=2",
  "ready": true
}
```

**Status: TRUE — the path is `/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`
with `ready: true`. `<sha>` is the coworld's manifest hash, URL-encoded:
`sha256%3Aa63d2c7fc64fd8fb0d30a5337c23bc14d0de5133d68ba01c4b562b6ee9011810` — byte-identical to
`STATE.coworld.manifest_sha`. It is NOT a `/client/replay` pod URL.**

---

## 7. Certification declared the static bundle — **TRUE**

**Source: the committed `runs/2026-08-25-factory-commons/release-result.json` (the copy phase 40
downloaded from release run `32902713785` and committed). No re-download was needed; `/tmp` was
not consulted.**

```bash
jq -r '.certify.replay_liveness' runs/2026-08-25-factory-commons/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Surrounding certification tail from the same file, for context:

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

**Status: TRUE — contains `Replay liveness: skipped (static replay bundle declared`.**

---

## 8. Spectator judgment — the viewer was EXECUTED — **TRUE**

*(a) Dispatch.* The `url` input is the **exact** iframe `src` from check 6.

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_2e5dc1a2-c660-4c7b-83a1-3881b4071786/sha256%3Aa63d2c7fc64fd8fb0d30a5337c23bc14d0de5133d68ba01c4b562b6ee9011810/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F83ef5ad4-38b7-47a2-83e2-1694de64d1e7.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90   # dispatched 2026-08-25T22:53:03Z
RUN=$(gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
      | jq -r 'sort_by(.createdAt)|reverse|.[0].databaseId')     # sorted by createdAt, not "the latest" blind
gh run watch "$RUN" -R Metta-AI/coworld-builder --exit-status
gh run download "$RUN" -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-25-factory-commons/viewer-check
```
```
32908246409	2026-08-25T22:53:05Z	in_progress
{"conclusion":"success","status":"completed","createdAt":"2026-08-25T22:53:05Z"}
runs/2026-08-25-factory-commons/viewer-check/{viewer-smoke.json, viewer-smoke.png, smoke-stdout.txt, smoke-stderr.txt}
```

**viewer-check run id: `32908246409` (green).** The artifact is committed at
`runs/2026-08-25-factory-commons/viewer-check/`. The `url` recorded inside `viewer-smoke.json`
matches `SRC` byte for byte.

*(b) Readouts, verbatim.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-25-factory-commons/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":1923,"clock":"SHIFT 1 / 15 TICK 2 OF 899","scorebug":"FACTORY INTEGRITY 100 PRIME CAP 100 SHIFT 1 / 15 TICK 2 OF 899 BANANAS INTEGRITY 0 0 ON THE CHUTE PRESSES 0 · OVERRIDES 0","feed_lines":0}
```

```bash
jq -c '.signals' runs/2026-08-25-factory-commons/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/2026-08-25-factory-commons/viewer-check/viewer-smoke.json
```
```
no failure
```

Three clock readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | `#clock` readout |
|---|---|
| 0 % | `SHIFT 1 / 15 TICK 2 OF 899` |
| 50 % | `SHIFT 8 / 15 TICK 466 OF 899` |
| 100 % | `FINAL SHIFT LIMIT` |

All three differ. `smoke-stdout.txt` also records
`canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized`.

Note on which moment each artifact captures: the `clock`/`scorebug`/`feed_lines` fields are sampled
at first paint (tick 2 of 899), which is why they read `INTEGRITY 100 PRIME CAP 100 … PRESSES 0`.
`viewer-smoke.png` is taken **after** the 100 % seek, so it shows the terminal frame
(`INTEGRITY 78 … PRESSES 26`). The two are consistent, not contradictory — that difference is
itself part of the proof the viewer advanced.

**Status: TRUE — `loaded: true` (via `data-replay-loaded="true"`, first frame at 1 923 ms,
`data-replay-error: null`) AND the three clock readouts differ. The `#scrub` element exists and
responds to seeks, so no "(no #scrub…)" caveat applies.**

*(c) The replay JSON the viewer was asked to draw* — ordered excerpts from `/tmp/ep.replay`
(the check-4 bytes), so the picture and the record can be reconciled:

```
# early
tick seat  kind   detail
0    0     order  operate pink
0    1     order  "Starting shift 1. Cap 100, integrity 100 (PRIME). Cooperating: operating on blue (scarcer…"
0    2     order  "operate pink - hopper 0/0"
9    0     grasp
9    1     grasp
23   0     drop
26   0     press
31   1     eat    3
59   2     press
59         shift

# middle
660  2     order  "maintain - integrity 64"
667  0     press
668  2     blocked  fix
679  2     fix
700  0     press
712  2     fix
719        shift
720  0     order  "maintain - integrity 75 (PRIME), cap 100. Restore before WORN threshold. Continue ops aft…"
733  0     fix

# late
857  2     press
886  1     misfeed
889  0     misfeed
894  2     press
897  1     eat    3
899        shift
899        end
```

```bash
jq -r '.results' /tmp/ep.replay    # (full object pasted in check 4)
# scores [0,71,18] · win [false,true,false] · presses [15,1,10] · strips [0,0,0] · repairs [2,0,4]
# bananas_made 91 · integrity_final 78 · cap_final 100 · band_final "PRIME" · shifts 15
# reason "complete" · ending "shift_limit"
```

### Spectator-judgment paragraph

`viewer-check/viewer-smoke.png` (1280 × 800, captured at the terminal frame) is a **legible,
populated broadcast, and it is unmistakably this game**. Top-left plate: a big `78` under the word
`INTEGRITY` with the headline `FACTORY`, an amber gauge bar roughly three-quarters full, the band
word `PRIME` in green and the subline `CAP 100` — the idea's machine-health gauge, reading one
word. Top-right plate: `BANANAS … 91` with the subline `2 ON THE CHUTE · PRESSES 26 · OVERRIDES 0`
— the production ticker. Centre-top: `FINAL / SHIFT LIMIT`. Under the scorebug, the three roster
chips in score order, each tinted with its cog's body colour: `COTTER DAVEEY-1 71`,
`RATCHET BASELINE 18`, `BOLT DAVEEY 0`. The endcard reads `SHIFT LIMIT`, the rule line
`HIGHER IS BETTER · CHUTE BANANAS EATEN + PRIVATE BANANAS BANKED`, the summary
`INTEGRITY 78 · CAP 100 · 91 BANANAS · 0 OVERRIDES`, three per-seat stat rows
(`COTTER  DAVEEY-1 · ATE 71 · BANKED 0 · 1P / 0O / 0R  71`, `RATCHET  BASELINE · ATE 18 · BANKED 0 ·
10P / 0O / 4R  18`, `BOLT  DAVEEY · ATE 0 · BANKED 0 · 15P / 0O / 2R  0`) and `REASON COMPLETE`.
**Every one of those numbers reconciles exactly with `results` above** — 78/100/91/0 overrides,
scores 0/71/18, presses 15/1/10, repairs 2/0/4 — so the picture and the record agree. The board is
visible behind the endcard (dimmed, as designed): the two dispenser belts run left-to-right at top
and bottom with cube sprites on them, the 5 × 5 machine block sits right-of-centre with its seam
glow, and the three cogs are drawn with their aliases under their feet (`RATCHET` upper-right,
`BOLT` and `COTTER` at the chute). It is **not** empty and **not** frozen: the three scrub readouts
advance `SHIFT 1 → SHIFT 8 → FINAL`, and the `MACHINE INTEGRITY` momentum strip under the scrub
track draws a stepped line that sags across the episode and recovers at the repairs — the same
shape as the `series.machine` rows and the `fix` events at ticks 679/712/733.

**Does it look like the coworld-ctf starter chrome? Yes.** The transport strip carries the
starter's seven buttons in the starter's order and glyphs (`↻ ◂| ▸ +5s |▸ ↻ ▸▸`) plus
`spoilers`, the win-chip, the `899 / 899` tick clock and the `1× 2× 3× 4× 8× 16×` speed chips; the
scrub track sits below it with the momentum SVG **underneath** on the same tick axis, the amber
playhead at the right end, and the labelled beat markers along the track — all of which are
`#transport`, `#btn-restart|back|play|fwd|end|loop|skip`, `#btn-spoilers`, `#tick-clock`,
`#speedchips`, `#scrub`, `#momentum`, `#scrub-fill`, `#scrub-head` from
`/workspace/starters/coworld-ctf/client/replay_broadcast.html` lines 1550–1595. The momentum label
is the design's declared re-lettering of the starter's `LIVES LEAD` to `MACHINE INTEGRITY`, and the
scorebug's `Lives` label is re-lettered `INTEGRITY` — the two literal edits design.md §Viewer
permits. `#viewpanel` (minimap + zoom bar) is absent, as the design declares. This is the starter's
shell with a game block appended, not a rewrite that reuses its ids.

**Three legibility observations for the coordinator (none of them makes this check false):**
1. `feed_lines: 0` at the sampled frame, and the killfeed area is empty in the screenshot. The
   replay has 45 `order` events and 26 `press` events that the design says produce feed rows, so
   rows are almost certainly being pushed and then ageing out before the terminal frame; a
   spectator arriving at the endcard sees no feed history. Worth a phase-30 look at feed row TTL.
2. The transport win-chip reads `DRAW` even though `results.win == [false,true,false]` (Cotter won
   outright, 71 to 18 to 0). The roster strip and the endcard both get the winner right, so this is
   the chip alone.
3. The roster chips and endcard show the **player** names (`DAVEEY-1`, `DAVEEY`, `BASELINE`) rather
   than the policy names — that is what the platform put in the replay's `results.names`
   (`["daveey","daveey-1","Baseline"]`), not a viewer bug, but it means the policy names
   (`factory-commons-foreman` / `-custodian`) never appear on screen in a league replay.

---

## Method notes

- Every item above was fetched fresh during this phase-60 run (2026-08-25T22:09Z–22:56Z). The two
  documented exceptions were used exactly as `prompts/60-verify.md` allows: **item 7** was read
  from the committed `runs/2026-08-25-factory-commons/release-result.json` (phase 40's artifact,
  not a live endpoint), and **item 8**'s rendered evidence came from `viewer-check.yml` run
  `32908246409`, dispatched by this run at 22:53:03Z and downloaded into
  `runs/2026-08-25-factory-commons/viewer-check/`.
- Headers are named, never their values: `Authorization: Bearer $SOFTMAX_TOKEN`,
  `User-Agent: coworld-builder/1.0`, `X-Use-Elevated-Privileges: true`. No token-bearing URL is
  reproduced here.
- Polls (checks 1 and 3) ran every ~5 minutes from 22:10Z to 22:54Z — 44 minutes of the 75-minute
  bound; the bound did not expire. Each poll is recorded in `log.md`.
- Nothing was created, triggered, paused or modified. The only non-GET calls were
  `POST $BASE/coworlds/replays/session` (the read path the public page's own JS uses to resolve the
  iframe `src`; it touches no coworld, league or policy) and the `viewer-check.yml` dispatch.
- An earlier `viewer-check.yml` run this session (`32905429599`, 22:17Z) rendered round 2's replay
  and also returned `loaded: true` with three differing clocks; its artifact is **not** the evidence
  above and was not committed. The committed artifact is `32908246409` against the current featured
  match.
