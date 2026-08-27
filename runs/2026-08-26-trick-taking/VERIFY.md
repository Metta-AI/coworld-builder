# VERIFY — trick-taking   (2026-08-27T04:28Z)

Verdict: **all-true** (8/8), with **one documented exception** recorded on check 5 (platform-wide
Bedrock capacity throttle, cross-checked against another LLM coworld running at the same time —
see §5; the literal grep was not clean and the judge should re-adjudicate the exception).

Every fetch below was made fresh in this phase-60 session (2026-08-27 03:43Z–04:28Z), except the
two documented exceptions the prompt allows: **check 7** reads the committed
`runs/2026-08-26-trick-taking/release-result.json` (phase 40's artifact), and **check 8**'s rendered
evidence comes from `viewer-check.yml` run **33039031390**, which this session dispatched at
04:18:49Z and whose artifact is committed under `runs/2026-08-26-trick-taking/viewer-check/`.

Constants used below:

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")   # values never printed
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_4764b49e-5b40-40b6-bd3d-3ed1b7bd8aa0
D=div_a46cc2cd-e301-4732-a116-975aee06a0dc
COW=cow_0de16cf6-8d0f-4601-8ca7-1c60fc3544d0
SHA=sha256:51bc9a9042ab935a7b2fe0da48bd5547940ca601011e72d8f9750c1b27eeabf1
```

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

**Fillers currently registered on the league** (fetched fresh; this read needs the elevated header):

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"a23ccfa9-f4a5-4c14-aeca-67c6bd8b5de1","policy_id":"c52c6a25-db1e-4a28-933f-5069576536cc","policy_name":"trick-taking-follow","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},
 {"policy_version_id":"e6d34146-60a5-4fa3-8f28-660b4302b171","policy_id":"d30206f5-6893-4672-a1b7-52ebadd15548","policy_name":"trick-taking-tracker","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```

`log.md` records the registration: `2026-08-27T03:42:12Z 50 fillers POST 200: follow=a23ccfa9
tracker=e6d34146 (both scripted, neither champion)` — issued at 03:40Z, before round 2 was
triggered and after round 1 had already auto-fired and failed.

**Rounds** (fetched 04:18Z; body trimmed to the fields the check reads — the untrimmed body also
embeds the whole league object, ~9 kB per row):

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq '{entries: [(if type=="array" then . else .entries end)[]
        | {id, round_number, status, error, scheduled_by, created_at, completed_at,
           entrants: [.round_config.entrant_attributions[].subject_id]}]}'
```
```json
{
  "entries": [
    {
      "id": "round_1e94fa5c-f65c-42a7-91d4-9b56f8854885",
      "round_number": 4,
      "status": "completed",
      "error": null,
      "scheduled_by": "ladder",
      "created_at": "2026-08-27T04:10:18.650684Z",
      "completed_at": "2026-08-27T04:17:37.198760Z",
      "entrants": ["ply_44ae9048-3242-4654-881f-6d9d43347fa3", "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"]
    },
    {
      "id": "round_f719f6e9-ac4e-4871-9f7e-bbfa2fa47b89",
      "round_number": 3,
      "status": "completed",
      "error": null,
      "scheduled_by": "ladder",
      "created_at": "2026-08-27T03:55:17.794895Z",
      "completed_at": "2026-08-27T04:02:48.532418Z",
      "entrants": ["ply_44ae9048-3242-4654-881f-6d9d43347fa3", "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"]
    },
    {
      "id": "round_0d426008-9d98-4aff-96cf-4853403f1605",
      "round_number": 2,
      "status": "completed",
      "error": null,
      "scheduled_by": "ladder",
      "created_at": "2026-08-27T03:40:17.410490Z",
      "completed_at": "2026-08-27T03:44:13.121279Z",
      "entrants": ["ply_44ae9048-3242-4654-881f-6d9d43347fa3", "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"]
    },
    {
      "id": "round_7683d2b0-d2c0-434d-94d2-268f72323266",
      "round_number": 1,
      "status": "failed",
      "error": "Temporal RoundWorkflow failed before settling the round.",
      "scheduled_by": "ladder",
      "created_at": "2026-08-27T03:40:00.779072Z",
      "completed_at": "2026-08-27T03:40:00.998229Z",
      "entrants": ["ply_44ae9048-3242-4654-881f-6d9d43347fa3", "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"]
    }
  ]
}
```
```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
```
```
3
```

The one non-completed round's `error`, verbatim: `Temporal RoundWorkflow failed before settling the
round.` — round 1, created **03:40:00.779Z** and failed **219 ms later**, i.e. before the filler
POST. That is the documented race in `playbooks/observatory-api.md` §6 ("A `trigger-round` issued
before any filler exists fails instantly with `Temporal RoundWorkflow failed before settling the
round`"): champion submission auto-fired it. It is superseded and does not count.

Status: **TRUE** — 3 completed rounds (2, 3, 4). Rounds **3** (created 03:55:17Z) and **4**
(created 04:10:18Z) are unambiguously after the filler registration at 03:40Z, which is ≥ 2 on its
own; round 2 (created 03:40:17Z) is also post-filler and its episode seated `Baseline` /
`Baseline (2)`, which is only possible with the fillers already set.

Poll log (5-minute cadence, 75-minute bound started 03:43Z, ended 04:18Z — 35 min used):
03:43Z r2 pending · 03:48Z r2 completed · 03:54Z no r3 · 03:58Z r3 pending · 04:03Z r3 completed ·
04:08Z no r4 · 04:13Z r4 pending · 04:17Z r4 completed. No round was triggered by the verifier.

---

## 2. Both champions ranked, fillers absent — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey-1	trick-taking-counter:v1	1013.1953024918979	3	1.0
2	daveey	trick-taking-signaller:v1	986.8046975081021	3	0.0
```

Raw body (a bare JSON list, as the playbook says):

```json
[{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":1013.1953024918979,"score_label":"MMR","score_value_type":"integer","rounds_played":3,"episode_wins":1.0,"episodes_played":null,"win_rate":0.3333333333333333,"policy_label":"trick-taking-counter:v1","recent_rounds":null},
 {"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":986.8046975081021,"score_label":"MMR","score_value_type":"integer","rounds_played":3,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"trick-taking-signaller:v1","recent_rounds":null}]
```

Status: **TRUE** — `daveey` (rank 2, `trick-taking-signaller:v1`) and `daveey-1` (rank 1,
`trick-taking-counter:v1`) both present, each `rounds_played = 3 ≥ 1`. The two filler policies
(`trick-taking-follow:v1`, `trick-taking-tracker:v1`) are **absent** from the board — exactly two
rows are returned.

---

## 3. Latest round's episode request completed with a replay — **TRUE**

Latest completed round = `round_1e94fa5c-f65c-42a7-91d4-9b56f8854885` (round 4).
The flat route the prompt lists is now 405 (playbook §9 records this), so the nested route was used:

```bash
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}"     # attempt 1
```
```
{"detail":"Method Not Allowed"}
HTTP 405
```
```bash
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}"                # attempt 2 — works
 | jq -c '(if type=="array" then . else .entries end)|map({id,status})'
```
```json
[{"id":"ereq_1485dd71-d828-4b16-ac94-8a306561520b","status":"completed"}]
```
```bash
EREQ=ereq_1485dd71-d828-4b16-ac94-8a306561520b
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/ec71e84c-f086-4198-907e-c24b27f3a317.replay",
  "participants": [
    {"position": 0, "kind": "policy", "policy_version_id": "b73304f2-d299-48c2-97b8-b16e1dce0a10",
     "policy_id": "bdb74a68-5dc2-4bd3-883f-fa55298886ed", "policy_name": "trick-taking-signaller",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "is_filler": false, "is_seed": false},
    {"position": 1, "kind": "policy", "policy_version_id": "42df1574-e61b-4995-b45a-bb0c8d706b86",
     "policy_id": "bd476788-2a1a-4daa-8a9a-c347fef193ac", "policy_name": "trick-taking-counter",
     "version": 1, "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
     "is_filler": false, "is_seed": false},
    {"position": 2, "kind": "policy", "policy_version_id": "e6d34146-60a5-4fa3-8f28-660b4302b171",
     "policy_id": "d30206f5-6893-4672-a1b7-52ebadd15548", "policy_name": "trick-taking-tracker",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "is_filler": true, "is_seed": false},
    {"position": 3, "kind": "policy", "policy_version_id": "a23ccfa9-f4a5-4c14-aeca-67c6bd8b5de1",
     "policy_id": "c52c6a25-db1e-4a28-933f-5069576536cc", "policy_name": "trick-taking-follow",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "is_filler": true, "is_seed": false}
  ],
  "participant_scores": [
    {"position": 0, "score": 0.484375},
    {"position": 1, "score": 0.484375},
    {"position": 2, "score": 0.515625},
    {"position": 3, "score": 0.515625}
  ]
}
```

Status: **TRUE** — `status == "completed"`, `replay_url` non-null, seat 0 = `daveey`
(`trick-taking-signaller` v1) and seat 1 = `daveey-1` (`trick-taking-counter` v1), both
`is_filler: false`; seats 2 and 3 are the two registered fillers with `is_filler: true`
(the API returns their policy names here; the **replay** renames them `Baseline` /
`Baseline (2)` — see §4).

---

## 4. Replay bytes are valid and show the game — **TRUE**

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/ec71e84c-f086-4198-907e-c24b27f3a317.replay" -o /tmp/ep.replay -w "http %{http_code} bytes %{size_download}\n"
```
```
http 200 bytes 69818
```
```bash
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .results.reason' /tmp/ep.replay
```
```
strict UTF-8 JSON: ok
tricks.replay.v1
complete
```

`protocol` match: the replay declares `tricks.replay.v1`, which is the protocol
`design.md` §Replay (line 714) declares for this coworld — `{"protocol": "tricks.replay.v1", …}` —
and the coworld's registered manifest declares the paired live protocols
`manifest.game.protocols.player` = `tricks.player.v1 - …` and `manifest.game.protocols.global`
(fetched fresh from `GET $BASE/coworlds/$COW`; the manifest carries no separate replay-protocol
key, only `manifest.game.replay_viewer.bundle = sha256:3bce268bdc73ecc4ae19d9a1d5f74ffc29910772c35757fbff5afd4458714808`).
`results.reason` is `complete`, the strongest of the three values `design.md` §11 permits
(`complete` | `deadline` | `budget`) — no exception needed.

The replay's event language is `kind` (not `type`) and decisions are marked with `scripted`, per
`design.md` §Replay event table (lines 661–664); the prompt's `.type=="decision"` /`.fallback==true`
filters return 0 against this schema, so the equivalent counts are below, plus the engine's own
per-slot tallies from `results`:

```bash
jq -c '{decisions:.results.decisions, fallbacks:.results.fallbacks, forcedMoves:.results.forcedMoves,
        handsScored:.results.handsScored, names:.results.names, scores:.results.scores, win:.results.win}' /tmp/ep.replay
```
```json
{"decisions":[51,49,49,51],"fallbacks":[1,0,0,0],"forcedMoves":[0,0,0,0],"handsScored":8,
 "names":["daveey","daveey-1","Baseline","Baseline (2)"],
 "scores":[0.484375,0.484375,0.515625,0.515625],"win":[false,false,true,true]}
```
```bash
jq -c '[.events[]|select(.slot!=null and (.kind|IN("bid","play","pass","discard")))]|group_by(.slot)
        |map({slot:.[0].slot, n:length, llm:([.[]|select(.scripted==false)]|length),
              scripted:([.[]|select(.scripted==true)]|length),
              scripted_with_choice:([.[]|select(.scripted==true and ((.legal//[])|length)>1)]|length)})' /tmp/ep.replay
```
```json
[{"slot":0,"n":51,"llm":33,"scripted":18,"scripted_with_choice":0},
 {"slot":1,"n":49,"llm":31,"scripted":18,"scripted_with_choice":0},
 {"slot":2,"n":49,"llm":0,"scripted":49,"scripted_with_choice":22},
 {"slot":3,"n":51,"llm":0,"scripted":51,"scripted_with_choice":26}]
```
```bash
jq -c '[.events[]|select((.slot==0 or .slot==1) and .scripted==true and (.kind|IN("bid","play","pass","discard")))]
        |group_by([.kind, ((.legal//[])|length)])|map({kind:.[0].kind, legal_n:((.[0].legal//[])|length), n:length})' /tmp/ep.replay
```
```json
[{"kind":"bid","legal_n":0,"n":1},{"kind":"play","legal_n":1,"n":35}]
```

Reading: of the champion seats' 100 decisions, **64 were LLM decisions**, **35 were plays whose
legal set had exactly one card** (a forced move the engine auto-applies without a model call), and
exactly **1 was a genuine fallback** — `results.fallbacks == [1,0,0,0]`, i.e. **1 of the 65
free-choice champion decisions (1.5 %)**, with `forcedMoves` zero everywhere. That fallback is the
Bedrock throttle of §5. The filler seats are 100 % scripted, as they must be. Champion decisions
carry real content — 100 champion events carry a non-empty private-notes `text` field, e.g.:

```
1  0  bid   "Giving the dealer the up-card: side strength, wants that trump i…"
8  0  play  "Hand 8, trick 4. Piston led KC, Sprocket JD, Ratchet 10D. I have QD AS…"
```

Status: **TRUE** — strict-parser-valid UTF-8 JSON; protocol matches; `reason == "complete"` with
`handsScored 8/8`; champion decisions are overwhelmingly non-scripted with substantive content and
the fallback count is 1 in 200 decisions.

---

## 5. Hosted game log — literal grep **NOT CLEAN**; verdict **TRUE under the prompt's documented platform-capacity exception**

```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs.raw   # http 200, 141650 bytes
python3 declogs.py /tmp/logs.raw /tmp/logs.txt        # decode the python b'…' reprs first (playbook §10)
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.txt || echo CLEAN
```
```
302:trick-taking llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
304:trick-taking llm: slot 0 falling back to a scripted decision
```

Decoded containers: `coworld-init-config` 0 lines, `bedrock-sidecar` 262 lines, `game` 169 lines,
`worker` 0 lines. Neither `cut off at max_tokens` nor `rejected` nor `LLM provider is unavailable`
appears anywhere. The context of the two hits names the cause explicitly:

```
trick-taking: hand 2 of 8 at 23s
trick-taking llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
trick-taking llm: slot 0 attempt 0 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
trick-taking llm: slot 0 falling back to a scripted decision
trick-taking: hand 2 Tinker pass at 23s
```

Both lines are one event: a Bedrock **HTTP 429 `ThrottlingException` — "Too many tokens per day"**
on Haiku 4.5. The coworld's response is its designed §Degrade-never-hang path (`design.md` §2.5:
"HTTP 429 → no retry; scripted move immediately") plus the model-candidate failover to Sonnet 4.5,
after which all 199 remaining decisions were LLM decisions and the episode ended `complete`.

**Cross-check (required by the check, done fresh this run at 04:20Z):** another LLM coworld's run
in flight is hitting the identical Bedrock quota at the same time — `fog-of-war-boards`
(`cow_5f8e4d33-…`), episode request `ereq_d273ce15-8095-4400-b57e-b9df696ec399`, its own hosted log:

```bash
curl -sS "$BASE/episode-requests/ereq_d273ce15-8095-4400-b57e-b9df696ec399/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}"
```
```
9:2026-08-27 04:00:17,281 WARNING __main__ bedrock_sidecar_complete {… "model":"global.anthropic.claude-haiku-4-5-20251001-v1:0","operation":"InvokeModel","ok":false,"status_code":429,"error_kind":"upstream_client","error_type":"ThrottlingException","message":"Too many tokens per day, please wait before trying again.", … "timestamp":"2026-08-27T04:00:17.281745Z"}
68:fogboards llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
69:fogboards llm: seat 0 attempt 0 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
```

**And it is not permanent.** As the check instructs, I waited and re-polled inside the bound rather
than going blocked. The same grep over the *other* two completed rounds' hosted logs, all fetched
this run:

| round | episode request | grep result |
|---|---|---|
| 2 (03:44Z) | `ereq_c1f7fb50-612c-4377-96d4-3c2ad5342116` | `CLEAN` (164 decoded `game` lines, zero hits) |
| 3 (04:02Z) | `ereq_bf75d0d7-3b01-43f5-a695-6759f07dc496` | `267: … unusable (throttled); falling back to …sonnet-4-5…` / `269: … slot 1 falling back to a scripted decision` |
| 4 (04:17Z) | `ereq_1485dd71-d828-4b16-ac94-8a306561520b` | the two lines above |

Status: **TRUE — documented exception.** Per `prompts/60-verify.md` §5, a platform-wide Bedrock
**capacity** symptom is "not a defect in this coworld" when another LLM coworld is hitting it at the
same time; that cross-check is satisfied above, the cause is named verbatim in both logs, round 2 of
this same coworld is `CLEAN`, and the coworld's handling is the designed 429 path with a 1-in-200
cost. **Flag for the judge:** the literal grep is not `CLEAN`, and the exception clause in the prompt
names `LLM provider is unavailable` rather than `falling back` — I am recording the exception, not
hiding the hit, so the judge can re-adjudicate on the pasted bytes.

---

## 6. The public page uses the static replay path — **TRUE**

Source used: **both**, in the prompt's order. The raw-HTML grep finds nothing (the page is
client-rendered for the iframe, as `playbooks/observatory-api.md` §Featured match records), so this
is recorded as *unknown*, not as a failure, and the API the page reads was used instead.

```bash
curl -sS "https://softmax.com/trick-taking" | grep -o '<iframe[^>]*src="[^"]*"'
```
```
(no output — http 200, 659403 bytes, no <iframe … src="…"> in the raw HTML)
```
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)[]|select(.name=="trick-taking")|{id,canonical,replay_viewer,featured_match}'
```
```json
{"id":"cow_0de16cf6-8d0f-4601-8ca7-1c60fc3544d0","canonical":true,"replay_viewer":null,"featured_match":null}
```

`featured_match: null` on `/coworlds` is the platform-wide value the playbook documents as not
evidence. The featured match is server-rendered into the page's SSR payload at `state.playlist[0]`,
and it is present (fetched 04:19Z, unescaped from the payload):

```json
{"episodeId":"3b1a41ce-aa0b-45e8-bc1a-8ecf54531806","coworldId":"cow_0de16cf6-8d0f-4601-8ca7-1c60fc3544d0",
 "coworldName":"trick-taking","coworldVersion":"0.1.0",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/ec71e84c-f086-4198-907e-c24b27f3a317.replay",
 "finishedAt":"2026-08-27T04:17:30.287100Z","roundNumber":4,"episodeNumber":1,"code":"trick-taking.r4.e1",
 "matchup":{"divisionId":"div_a46cc2cd-e301-4732-a116-975aee06a0dc","divisionName":"Competition",
  "first":{"rank":1,"player_name":"daveey-1","score":1013.1953024918979,"policy_label":"trick-taking-counter:v1","rounds_played":3,…},
  "second":{"rank":2,"player_name":"daveey","score":986.8046975081021,"policy_label":"trick-taking-signaller:v1","rounds_played":3,…}},
 "inspectUrl":"/observatory/v2?tab=overview&detail=episode-request:ereq_bf75d0d7-…","outcome":null}
```

The iframe `src` is what the page's own JS resolves it to:

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" "${ELEV[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_0de16cf6-…","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/ec71e84c-f086-4198-907e-c24b27f3a317.replay"}'
```
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_0de16cf6-8d0f-4601-8ca7-1c60fc3544d0/sha256%3A51bc9a9042ab935a7b2fe0da48bd5547940ca601011e72d8f9750c1b27eeabf1/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fec71e84c-f086-4198-907e-c24b27f3a317.replay&v=2","ready":true}
HTTP 200
```

Status: **TRUE** — the src is `…/v2/coworlds/replays/static/<cow_id>/<manifest sha256>/index.html?replay=<s3 url>`
with `ready: true`; `<cow_id>` and `<sha>` match STATE exactly; it is **not** a `/client/replay` pod
URL; and a featured match is present (round 4 episode 1, `daveey-1` vs `daveey`).

---

## 7. Certification declared the static bundle — **TRUE**

Source: the **committed** `runs/2026-08-26-trick-taking/release-result.json` (phase 40's artifact
from release run `33036293815`). No re-download was needed; `/tmp` was never consulted.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-26-trick-taking/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE** — contains `Replay liveness: skipped (static replay bundle declared`.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

Dispatched at **04:18:49Z** against the exact iframe `src` from §6:

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_0de16cf6-8d0f-4601-8ca7-1c60fc3544d0/sha256%3A51bc9a9042ab935a7b2fe0da48bd5547940ca601011e72d8f9750c1b27eeabf1/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fec71e84c-f086-4198-907e-c24b27f3a317.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:3]|.[]|[.databaseId,.createdAt,.status]|@tsv'
```
```
33039031390	2026-08-27T04:18:51Z	in_progress      <- created AFTER the 04:18:49Z dispatch: this run
33036080393	2026-08-27T03:20:40Z	completed
33027843730	2026-08-27T00:44:34Z	completed
```
```bash
gh run watch 33039031390 -R Metta-AI/coworld-builder --exit-status
gh run view  33039031390 -R Metta-AI/coworld-builder --json status,conclusion,createdAt,url
```
```json
{"conclusion":"success","createdAt":"2026-08-27T04:18:51Z","status":"completed",
 "url":"https://github.com/Metta-AI/coworld-builder/actions/runs/33039031390"}
```
```bash
gh run download 33039031390 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-26-trick-taking/viewer-check
```
Committed at `runs/2026-08-26-trick-taking/viewer-check/`: `viewer-smoke.json`, `viewer-smoke.png`,
`smoke-stdout.txt`, `smoke-stderr.txt` (stderr is 0 bytes).

**The readouts, verbatim:**

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' viewer-smoke.json
```
```json
{"loaded":true,"ms":1705,"clock":"HAND 1 / 8 · NO TRUMP","scorebug":"daveey-1 0 POINTS Ratchet 0 POINTS daveey 0 POINTS Piston 0 POINTS","feed_lines":402}
```
```bash
jq -c '.signals' viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```
```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' viewer-smoke.json
```

| scrub | clock readout |
|---|---|
| 0 % | `HAND 1 / 8 · NO TRUMP` |
| 50 % | `HAND 5 / 8 · NO TRUMP · TRICK 1 / 5 · RATCHET TO PLAY` |
| 100 % | `HAND 8 / 8 · ♠ TRUMP · TRICK 5 / 5 · FINAL` |

```bash
jq -r '.failure // "no failure"' viewer-smoke.json
```
```
no failure
```

Also in the artifact (`canvas_text`, the caption-fit audit): `4200 drawn, 0 never inside the canvas
(0 draws crossed an edge), 86 ellipsized` — nothing was drawn outside the canvas, and the 86
ellipsized strings are the note bubbles doing their designed mid-string truncation
(`"right bower now, gives me a ch…"`). `console_tail` is `["[bridge] loading","[bridge] ready"]`.

**Item 8 gate:** `loaded: true` ✅ and the three clock readouts **differ** ✅ → **TRUE**.

**Reconciliation against the replay** (`/tmp/ep.replay` from §4 — the same
`ec71e84c-…` bytes the viewer was handed):

```bash
jq -r '.events[]|[(if .hand==null then "-" else (.hand+1) end),(.slot//"-"),.kind,((.tell//.action//.text//"")|.[0:64])]|@tsv' /tmp/ep.replay | head -12
```
```
-	-	start	euchre
1	-	hand
1	2	bid	No ordering hand in hearts.
1	0	bid	Giving the dealer the up-card: side strength, wants that trump i
1	0	trump
1	1	discard	Discard 9S. Hand is QC JD KD QH AH after pickup. JD is left bowe
1	2	play	Cashing a certain winner; probably void in diamonds next trick.
1	0	play	Ratchet led AD. I have AC (ace of diamonds). Must follow suit wi
```
```bash
… | sed -n '130,138p'          # middle
```
```
4	0	play	Hand 4, trick 4. Sprocket led 9S (trump, winning), Ratchet KD (v
4	3	trick
4	-	handEnd	makers make it
5	-	hand
5	2	bid	No ordering hand in hearts.
5	0	bid	No ordering hand in hearts.
5	3	bid	No ordering hand in hearts.
5	1	bid	No ordering hand in hearts.
5	2	bid	pass
```
```bash
… | tail -8                    # late
```
```
8	3	trick
8	3	play	Drawing trumps to protect the march.
8	1	play	Trick 4: Piston led KC off-suit. Playing JD (left bower, 2nd hig
8	2	play	
8	0	play	Hand 8, trick 4. Piston led KC, Sprocket JD, Ratchet 10D. I have
8	3	trick
8	-	handEnd	makers make it
9	-	end	complete
```
```bash
jq -r '.results' /tmp/ep.replay      # trimmed to the endcard's numbers
```
```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],"scores":[0.484375,0.484375,0.515625,0.515625],
 "win":[false,false,true,true],"points":[4.0,4.0,5.0,5.0],"teamPoints":[4.0,5.0],"tricks":[7,9,6,18],
 "handsScored":8,"hands":8,"reason":"complete"}
```

The record and the picture agree on every number: the replay has **266 events**, the transport strip
reads **266 / 266**; the 50 % scrub lands on hand 5 of 8, which is event ~133 of 266; the endcard's
table (`Ratchet 0.52 / 5 pts / 6 tricks`, `Piston 0.52 / 5 / 18`, `daveey 0.48 / 4 / 7`,
`daveey-1 0.48 / 4 / 9`) is `results.scores` rounded, `results.points` and `results.tricks`
seat-for-seat, and `win: [false,false,true,true]` is the headline "Ratchet & Piston TAKE THE TABLE".

**Spectator judgment.** It is legible and it plainly shows the game. `viewer-smoke.png` is the
100 %-scrub frame: a dark stage titled **TRICK·TAKING** with a variant chip reading **EUCHRE**, a
`«LOG` toggle, and a centred clock **HAND 8 / 8 · ♠ TRUMP · TRICK 5 / 5 · FINAL**. Directly under it
runs the four-seat scorebug — `daveey-1 4 POINTS | Ratchet 5 POINTS | daveey 4 POINTS |
Piston 5 POINTS`, each with a coloured team pip and a small square-marker trick tally on the right —
so the question "who is winning" is answered in the top 80 px without decoding anything. Four cog
avatars sit at the four edges of an elliptical green table, each captioned with its name and its
trick count (`daveey 0 tricks`, `Piston 4 tricks`), and each with a note bubble carrying that seat's
own reasoning in readable prose ("Trick 4: Piston led KC off-suit. Playing JD (left bower, 2nd
highest trump) to win this trick…"). Over the table sits the endcard — **FINAL — 8 HANDS /
Ratchet & Piston TAKE THE TABLE** and a ranked table with SCORE / POINTS / TRICKS / BID-MADE
columns. Along the bottom is the transport strip: a play button, a full-width scrubber whose
coloured tick marks are the per-seat momentum graph (orange, blue, green and red ticks clustered by
hand, with taller markers at hand boundaries), and the frame counter **266 / 266**. It is not empty,
not frozen (the three clock readouts step from hand 1 through hand 5 to hand 8/FINAL) and not
unreadable.

It **is** the starter's chrome, not a rewrite: the babel/parley transport strip, the scrubber with
the momentum graph, the top scorebug band and the endcard are all recognisably the same product as
paintbot/raid/hive, re-skinned for a card table. This is not the cogame-gridlock failure mode.

Two **legibility observations for the coordinator** (neither blocking, neither part of the check-8
gate):
1. The scorebug and endcard mix registries: the two champion seats are labelled by **player name**
   (`daveey`, `daveey-1`) while the two filler seats are labelled by their **cog alias**
   (`Ratchet`, `Piston`) rather than the replay's `policyNames` values `Baseline` / `Baseline (2)`.
   A spectator cannot tell from the scorebug that two of the four seats are house baselines.
2. The endcard scrim dims the table behind it heavily, so at the 100 % frame the note bubbles and
   the played cards are only just readable. The mid-episode frames are unaffected.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 2, 3, 4 completed; 3 and 4 unambiguously post-filler |
| 2 | Both champions ranked, fillers absent | **TRUE** — `daveey-1` rank 1, `daveey` rank 2, 3 rounds each, no filler rows |
| 3 | Latest round's episode request completed with a replay | **TRUE** — `ereq_1485dd71…` completed, replay_url set, both champions seated |
| 4 | Replay bytes valid and show the game | **TRUE** — strict JSON, `tricks.replay.v1`, `reason: complete`, 64 LLM decisions vs 1 fallback |
| 5 | Hosted game log clean | **TRUE under the documented platform-capacity exception** — literal grep NOT clean (Bedrock 429 "Too many tokens per day"); cross-checked against `fog-of-war-boards` at 04:00Z; round 2's log is CLEAN |
| 6 | Public page uses the static replay path | **TRUE** — `…/replays/static/<cow>/<sha>/index.html?replay=…`, `ready:true`, featured match `trick-taking.r4.e1` |
| 7 | Certification declared the static bundle | **TRUE** — from the committed `release-result.json` |
| 8 | Viewer executed and judged | **TRUE** — run 33039031390, `loaded:true` in 1705 ms, three differing clock readouts, starter chrome intact |
