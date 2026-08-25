# VERIFY — hanabi   (2026-08-25T03:03Z, re-verification attempt 2, post-remediation)

Verdict: **all-true (8/8)** — with one recorded caveat on check 5 (see §5.3: the
`cut off at max_tokens` truncation is *reduced but not proven eliminated* by the 0.1.1
`maxOutputTokens` 800→900 change; it recurred once each in rounds 7 and 8 and is absent from
round 9, the round this check is scoped to).

Subject of this verification: the **remediated** coworld.

| | |
|---|---|
| slug | `hanabi` |
| coworld version | `0.1.1` |
| `cow_id` | `cow_4c005d78-ebb2-4095-83da-cde90519f53b` |
| `manifest_sha` | `sha256:973eb76b7e4f91c6e246ca20d1063c284ab008112f27189c3566b8c3b3be8c1c` |
| league `$L` | `league_332c17c5-b6bf-4341-98c7-3161dd58e6d8` |
| division `$D` | `div_0a3fd174-6ac2-4167-971e-e86f9eb9ed1e` |
| champions | `hanabi-signaler:v2` (daveey, pvid `86c491d0-702a-4acc-88d4-21b4ca8e2cb6`) · `hanabi-reader:v2` (daveey-1, pvid `88bbcc80-1575-4784-b93b-278f48e1ac96`) |
| fillers | `hanabi-conventions:v2` (`6e696c59-…`) · `hanabi-cautious:v2` (`7a65d5b7-…`) |
| v2 rounds | round_number ≥ 7 |
| verifier window | 2026-08-25T02:20Z → 03:03Z (43 min of the 75-min bound) |

Every response below was fetched **in this window**, by this verifier, except where the check
itself declares an exception (check 7 = the committed release artifact; check 8 = the artifact of
a `viewer-check.yml` run this verifier dispatched at 02:58:40Z).

Headers sent on every Observatory call (values never printed):
`Authorization: Bearer $SOFTMAX_TOKEN`, `User-Agent: coworld-builder/1.0`, and on the artifact/log
and filler reads additionally `X-Use-Elevated-Privileges: true`.

```
BASE=https://softmax.com/api/observatory/v2
L=league_332c17c5-b6bf-4341-98c7-3161dd58e6d8
D=div_0a3fd174-6ac2-4167-971e-e86f9eb9ed1e
```

---

## 1. ≥2 completed rounds after the (v2) fillers were set — **TRUE**

Fillers were re-registered at the **v2** version ids at 02:19Z, *before* round 7 was triggered
(`log.md`: `2026-08-25T02:19:25Z 50/60 … filler-policies updated to v2 UUIDs (conventions 6e696c59,
cautious 7a65d5b7); trigger-round issued, round 7 pending (first v2 round)`).

Fresh read of what the league currently holds as fillers:

```
GET $BASE/leagues/$L/filler-policies      (+ X-Use-Elevated-Privileges)
HTTP 200
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"6e696c59-64a1-4c6d-b161-02a6c0093d47","policy_id":"988c66e1-1f64-4043-ba97-71f1aa90317a","policy_name":"hanabi-conventions","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},
 {"policy_version_id":"7a65d5b7-9b46-4d81-a813-fb9e53d80440","policy_id":"f705c8f8-38db-490e-ae46-eb34b6413eed","policy_name":"hanabi-cautious","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```

Rounds (fetched 2026-08-25T03:00:06Z):

```
GET $BASE/rounds?league_id=$L&limit=20
HTTP 200
$ jq -r '[if type=="array" then . else .entries end|.[]|select(.status=="completed" and .round_number>=7)]|length'
3
$ jq -r 'if type=="array" then . else .entries end|sort_by(.round_number)|.[]
        |[.round_number,.id,.status,(.completed_at//"-"),(.error//"-")]|@tsv'
1  round_a03839eb-14d2-48c4-adb7-daf2b764258d  failed     2026-08-25T01:09:00.603201Z  Temporal RoundWorkflow failed before settling the round.
2  round_6532a9d6-62db-4147-b768-90a01df682e7  completed  2026-08-25T01:17:30.753516Z  -
3  round_60dc0fb8-cfe8-4714-acb4-e376a099c4fe  completed  2026-08-25T01:32:15.343068Z  -
4  round_eb91b66e-46f4-4d0c-a66e-5f1a3014f229  completed  2026-08-25T01:47:24.010706Z  -
5  round_ceee860c-c9f8-44b2-90bc-fd71499fca5f  completed  2026-08-25T02:03:02.792441Z  -
6  round_a08c075a-70b3-40c6-a2db-b5f35d7492f8  completed  2026-08-25T02:17:37.779167Z  -
7  round_3835c0c9-9f71-4b42-9c49-cda360fa8ae8  completed  2026-08-25T02:26:32.653402Z  -
8  round_81ad9f15-2ac7-44e0-9de2-54883bcf2d86  completed  2026-08-25T02:40:55.067310Z  -
9  round_3983ca28-c1f7-4f29-85a8-492c834a9747  completed  2026-08-25T02:55:35.035717Z  -
```

The three v2 rounds' entrant attributions carry the **v2** champion policy-version ids:

```
$ jq -r '… | select(.round_number>=7) | {round_number,id,status,created_at,completed_at,
          entrants:[.round_config.entrant_attributions[]|{subject_id,policy_version_id}]}'
```
```json
{"round_number":7,"id":"round_3835c0c9-9f71-4b42-9c49-cda360fa8ae8","status":"completed","error":null,
 "created_at":"2026-08-25T02:18:55.052558Z","completed_at":"2026-08-25T02:26:32.653402Z",
 "entrants":[{"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","policy_version_id":"86c491d0-702a-4acc-88d4-21b4ca8e2cb6"},
             {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","policy_version_id":"88bbcc80-1575-4784-b93b-278f48e1ac96"}]}
{"round_number":8,"id":"round_81ad9f15-2ac7-44e0-9de2-54883bcf2d86","status":"completed","error":null,
 "created_at":"2026-08-25T02:33:55.404231Z","completed_at":"2026-08-25T02:40:55.067310Z",
 "entrants":[{"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","policy_version_id":"86c491d0-702a-4acc-88d4-21b4ca8e2cb6"},
             {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","policy_version_id":"88bbcc80-1575-4784-b93b-278f48e1ac96"}]}
```
(round 9 is the same pair — see its episode-request participants in §3, positions 0/1 =
`86c491d0…` / `88bbcc80…`.)

Status: **TRUE** — 3 completed v2 rounds (7, 8, 9), all after the v2 fillers were registered at
02:19Z; requirement was ≥ 2. The only non-completed round in the whole league is round 1, which
failed **before any filler existed** (`"Temporal RoundWorkflow failed before settling the round."`
— the documented pre-filler failure mode, `playbooks/observatory-api.md` §6); it is recorded here
verbatim and does not count. Rounds 2–6 are the pre-remediation v1 rounds and are excluded from
this check by design.

---

## 2. Both champions ranked — **TRUE**

```
GET $BASE/divisions/$D/leaderboard        (fetched 2026-08-25T03:00:06Z)
HTTP 200
```
```json
[{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1000.0,"score_label":"Elo","score_value_type":"integer","rounds_played":8,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"hanabi-signaler:v2","recent_rounds":null},
 {"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":1000.0,"score_label":"Elo","score_value_type":"integer","rounds_played":8,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"hanabi-reader:v2","recent_rounds":null}]
```
```
$ jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
1  daveey    hanabi-signaler:v2  1000.0  8  0.0
2  daveey-1  hanabi-reader:v2    1000.0  8  0.0
```

**Saying it out loud, per the design note (design.md L191–199):** Hanabi is *fully cooperative* —
every seat receives the identical team score, so head-to-head Elo can never separate the two
champions and both will sit at **1000.0 forever**. That is the expected, designed behaviour, not a
ranking failure (cogame-raid learning 5, 2026-08-23). The manifest description says the same:
*"read the division leaderboard's mean SCORE, not the Elo spread, which cannot separate two
champions who always tie."* "Ranked" is therefore judged on the **`rounds_played`** column and on
the mean team score per round, both of which are live:

| round | mean team score (all four seats) |
|---|---|
| 7 | 10.0 (`participant_scores` `[10.0,10.0,10.0,10.0]`) |
| 8 | 17.0 (`[17.0,17.0,17.0,17.0]`) |
| 9 | 18.0 (`[18.0,18.0,18.0,18.0]`) |

Both champions present, both `rounds_played = 8 ≥ 1`, both at their **`:v2`** labels (proving the
leaderboard has picked up the remediated policies). **Fillers are absent from the leaderboard
entirely** — the list has exactly two rows — which satisfies the "absent or `Baseline`-labelled"
requirement; and the replay's own `results.names` renders them as `"Baseline"` / `"Baseline (2)"`
(§4).

Status: **TRUE**.

---

## 3. The latest v2 round's episode request completed with a replay — **TRUE**

Latest completed round with `round_number ≥ 7` = **round 9**,
`round_3983ca28-c1f7-4f29-85a8-492c834a9747`.

```
GET $BASE/episode-requests?round_id=round_3983ca28-c1f7-4f29-85a8-492c834a9747&limit=20
HTTP 200
ereq_2c1119ae-e7a7-441f-bd68-2fd8971eda45   completed

GET $BASE/episode-requests/ereq_2c1119ae-e7a7-441f-bd68-2fd8971eda45
HTTP 200
$ jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/dac699c0-31b4-4ad7-95de-9e3a5ed34b50.replay",
  "participants": [
    {"position":0,"kind":"policy","policy_version_id":"86c491d0-702a-4acc-88d4-21b4ca8e2cb6","policy_id":"e726887a-cbaf-4328-afa6-bd143960327f","policy_name":"hanabi-signaler","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","is_filler":false,"is_seed":false},
    {"position":1,"kind":"policy","policy_version_id":"88bbcc80-1575-4784-b93b-278f48e1ac96","policy_id":"9ca4de2a-5489-4ca8-bd47-e2c9e7b2864d","policy_name":"hanabi-reader","version":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","is_filler":false,"is_seed":false},
    {"position":2,"kind":"policy","policy_version_id":"6e696c59-64a1-4c6d-b161-02a6c0093d47","policy_id":"988c66e1-1f64-4043-ba97-71f1aa90317a","policy_name":"hanabi-conventions","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","is_filler":true,"is_seed":false},
    {"position":3,"kind":"policy","policy_version_id":"6e696c59-64a1-4c6d-b161-02a6c0093d47","policy_id":"988c66e1-1f64-4043-ba97-71f1aa90317a","policy_name":"hanabi-conventions","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","is_filler":true,"is_seed":false}
  ],
  "participant_scores": [
    {"position":0,"score":18.0},{"position":1,"score":18.0},
    {"position":2,"score":18.0},{"position":3,"score":18.0}
  ]
}
```

Status: **TRUE** — `status == "completed"`, `replay_url` non-null, seats 0/1 are the two champions
(`daveey` / `daveey-1`) at their `:v2` policy version ids, seats 2/3 are the v2 filler
(`is_filler: true`, rendered `Baseline` / `Baseline (2)` in the replay — §4).

*(The previous latest v2 round, round 8, `ereq_50ec4450-0d8f-4bb8-9514-ef4735a6d236`, was fetched
in this same window and is identical in shape: `completed`, replay
`…/4067465a-2fc9-4693-a1f9-217fdd3392ea.replay`, same champion seats, `participant_scores` all
17.0. It is the round the first viewer-check of this window rendered, before round 9 landed.)*

---

## 4. Replay bytes are valid and show the game — **TRUE**

```
GET https://softmax-public.s3.amazonaws.com/replays/dac699c0-31b4-4ad7-95de-9e3a5ed34b50.replay
HTTP 200 bytes=29012          → /tmp/ep9.replay

$ jq -e . /tmp/ep9.replay >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok

$ jq -r '.protocol, .results.reason' /tmp/ep9.replay
hanabi.replay.v1
complete
```

`protocol` = `hanabi.replay.v1`, which is exactly what the design/manifest declares for the replay
payload (`design.md` L652: *"Replay payload (`hanabi.replay.v1`), written by the server"*; the
canonical manifest for `cow_4c005d78…` declares the matching static bundle at
`game.replay_viewer.bundle = sha256:9068eedfe920c32b0c9c2aef5ea06de9021a70b3a90a7e896c5cd1f7d355b2d0`).
`results.reason == "complete"` — the strongest of the accepted values; no `deadline` exception is
being invoked.

The prompt's `select(.type=="decision")` filter returns 0 because this protocol keys events on
`kind`, not `type`; the equivalent, verified against the actual schema:

```
$ jq -r '[.events[].kind]|group_by(.)|map({(.[0]):length})|add'  →  start:1, move:64, end:1
$ jq -r '[.events[]|select(.kind=="move")]|group_by(.seat)|map({seat:.[0].seat, moves:length,
          origins:(map(.origin)|group_by(.)|map({(.[0]):length})|add),
          scripted_true:(map(select(.scripted==true))|length)})'
```
```json
[{"seat":0,"moves":16,"origins":{"llm":15,"retry":1},"scripted_true":0},
 {"seat":1,"moves":16,"origins":{"llm":16},          "scripted_true":0},
 {"seat":2,"moves":16,"origins":{"scripted":16},     "scripted_true":16},
 {"seat":3,"moves":16,"origins":{"scripted":16},     "scripted_true":16}]
```

Champion seats 0 and 1 are **32/32 non-scripted** (`scripted_true: 0`; origins `llm` and `retry`,
both LLM-produced — `retry` is the second LLM call after a rejected first reply). **Zero
fallbacks**, confirmed twice:

```
$ jq -r '[.events[]|select(.origin=="fallback")]|length'   →  0
$ jq -r '.results.fallbacks' /tmp/ep9.replay               →  [0,0,0,0]
```

```
$ jq -r '.results' /tmp/ep9.replay
```
```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],
 "scores":[18,18,18,18],"score":18,
 "fireworks":[4,4,4,3,3],"contributions":[6,4,2,6],"plays":[6,4,2,6],
 "misplays":[0,0,0,0],"discards":[4,4,6,6],"hints":[6,8,8,4],"fallbacks":[0,0,0,0],
 "turns":64,"maxTurns":80,"deckLeft":0,"endReason":"deckout","reason":"complete"}
```

Decision content is non-trivial — this is Hanabi theory-of-mind, not filler text. Three verbatim
champion `note`s from seat 1 (`daveey-1`, `hanabi-reader:v2`) late in the episode:

```
Slot 3 is R1, completely dead (red at R4, R5 discarded). Discarding for hint. Widget has Y3 playable. Need to coordinate endgame with 5 cards left.
Playing G3 from slot 2. Slots 2 and 4 both have G3 candidates. After this: need to coordinate Y5 play from Tinker and B2 from Widget. Only 2 cards left in deck.
Discarding slot 4 (Y3/G3 both dead). Widget plays B3 next, Tinker plays Y5. Final score likely 19 (R4+Y5+G4+B3+W3=19).
```

Status: **TRUE** — strict-UTF-8-JSON-valid, protocol matches, `reason == "complete"`, champion
seats fully LLM-driven, fallback count 0 (a "small minority" bound met at its floor).

---

## 5. Hosted game log is clean — **TRUE (with recorded caveat, §5.3)**

### 5.1 The scoped round (latest completed v2 round = round 9)

```
GET $BASE/episode-requests/ereq_2c1119ae-e7a7-441f-bd68-2fd8971eda45/artifacts/logs
     (+ X-Use-Elevated-Privileges)
HTTP 200 bytes=75107
```
The body is python `b'…'` byte-string reprs under `===== container: <name> =====` headers; it was
**decoded per-repr with `ast.literal_eval` before grepping** (containers seen: `bedrock-sidecar`,
`coworld-init-config`, `game`, `worker`; 296 decoded lines) and then:

```
$ grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected'
decoded lines: 296   HITS: 2
165  [game] hanabi llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
166  [game] hanabi llm: seat 0 attempt 0 rejected: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
```

**Zero** `cut off at max_tokens`. **Zero** `unbalanced JSON object`. **Zero** `LLM provider is
unavailable`. The two hits are one event: a Bedrock **capacity** throttle on the haiku model, in
context —

```
[game] hanabi: turn 4 of 80, seat 0 (Gizmo) at 12s
[game] hanabi llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
[game] hanabi llm: seat 0 attempt 0 rejected: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
[game] hanabi: turn 4 Gizmo hint 3 1 (retry)
[game] hanabi: turn 5 of 80, seat 1 (Bolt) at 20s
[game] hanabi: turn 5 Bolt hint 0 1 (llm)
```
— i.e. the model switch happened, the retry succeeded, `origin: retry` (still LLM), no fallback.

### 5.2 Platform cross-check for the throttle (the documented exception)

`prompts/60-verify.md` check 5: the throttle is a platform-wide Bedrock capacity symptom, not a
defect in this coworld, **if another LLM coworld's log shows it too**. Both candidates were
fetched **in the same window** as hanabi round 9 (which ran 02:48:00 → 02:55:35Z):

```
garble  cow_cb2293f4-2825-41d3-831b-7f3a690474a6
        latest completed ereq_7d8daeef-17b5-4500-a819-aaac47667f4e  @ 2026-08-25T02:47:53Z
        GET …/artifacts/logs → HTTP 200 bytes=35687, 171 decoded lines, 3 hits
   [game] garble llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-6
   [game] garble llm: seat 2 attempt 0 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
   [game] garble llm: seat 2 falling back to scripted decision

ledger  cow_79259a28-8e2f-4593-9978-bcb162265a11
        latest completed ereq_4a4cd7ef-1a39-49d1-b95c-ce2115a220d9  @ 2026-08-25T02:48:16Z
        GET …/artifacts/logs → HTTP 200 bytes=128935, 361 decoded lines, 5 hits
   [game] ledger llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
   [game] ledger llm: seat 0 attempt 0 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
   [game] ledger llm: seat 1 attempt 0 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
   [game] ledger llm: seat 2 attempt 0 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
   [game] ledger llm: seat 3 attempt 0 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
```

Identical model, identical 429 body (`Too many tokens per day`), same minute, two unrelated
coworlds — the documented platform exception applies, and hanabi is in fact the *least* affected
of the three (one seat, one turn, recovered on retry; garble had to fall back to a scripted
decision, hanabi did not).

Status: **TRUE** — the scoped round's log carries no unexplained hit; its only hits are the
platform-wide Bedrock throttle, cross-checked against two other live LLM coworlds in the same
window.

### 5.3 Caveat — the truncation is reduced, not proven eliminated (retry-budget record)

The remediation raised `maxOutputTokens` 800 → 900. Check 5 was attempted on all three v2 rounds
(attempts 1/2/3 = rounds 7, 8, 9), each with a fresh elevated log fetch and full `b'…'` decode:

| v2 round | ereq | hits | verdict |
|---|---|---|---|
| 7 | `ereq_b7f36bf7-80e3-43c8-a1fe-71a1f4c94ae5` | 3 | 2× platform throttle + **1× `cut off at max_tokens`** |
| 8 | `ereq_50ec4450-0d8f-4bb8-9514-ef4735a6d236` | 4 | 2× platform throttle + 1× `anthropic error 500` + **1× `cut off at max_tokens`** |
| 9 | `ereq_2c1119ae-e7a7-441f-bd68-2fd8971eda45` | 2 | platform throttle only → **clean** |

Verbatim, the two truncation lines that are *not* in the scoped round (pasted so nothing rests on
my summary):

```
round 7  [game] hanabi llm: seat 0 attempt 0 rejected: reply cut off at max_tokens before any JSON: I need to analyze the current game state and determine the best move.  **Current Stacks:** red 1, yellow 2, green 2, blue 2, white 1  **What's needed next:** re
round 7  [game] hanabi: turn 56 Ratchet hint 1 1 (retry)

round 8  [game] hanabi llm: seat 0 attempt 0 rejected: reply cut off at max_tokens before any JSON: I need to analyze the situation carefully.  **Current state:** - Score: 17/25 - Stacks: r5 (complete), y4, g2, g2, b2, w4 - Deck empty, 2 turns left after mine
round 8  [game] hanabi: turn 60 Sprocket hint 1 2 (retry)

round 8  [game] hanabi llm: seat 0 attempt 0 rejected: anthropic error 500:
round 8  [game] hanabi: turn 52 Sprocket hint 1 blue (retry)
```

Facts for the coordinator/judge, no inference: the 0.1.1 change did land (the new
truncation-named error text `reply cut off at max_tokens before any JSON` is the remediated
message, and the attempt-1 symptom `unbalanced JSON object in response` has **disappeared
entirely** from all three v2 rounds). What remains is at most **one truncated first reply per
episode, always on seat 0 (`hanabi-signaler`, the long-reasoning prompt), always recovered by the
single retry, with `results.fallbacks == [0,0,0,0]` in every v2 round** — i.e. it never reaches a
scripted fallback and never degrades the episode. Round 9, the round this check is scoped to, has
none at all. `anthropic error 500` (round 8) is a provider-side transient with an empty body,
also recovered on retry; it is **not** cross-checked against another coworld (neither garble nor
ledger showed a 500 in this window), so it is recorded here rather than claimed as a platform
exception.

---

## 6. The public page uses the static replay path — **TRUE**

**Source used: (b) the API the page reads** — the raw-HTML grep is empty because the iframe is
client-rendered, exactly as `playbooks/observatory-api.md` §Featured match records
(lighthouse, 2026-08-22). Both attempts are pasted.

*Attempt (a) — raw HTML:*
```
GET https://softmax.com/hanabi
HTTP 200 bytes=536512
$ grep -o '<iframe[^>]*src="[^"]*"'
GREP-EMPTY: no iframe element in raw HTML (client-rendered)
```
Recorded as **unknown**, not as a failure.

*Attempt (b) — the featured match, server-rendered into the page's SSR payload at
`state.playlist[0]` (same fetch, unescaped):*
```json
"playlist":[{"episodeId":"8e29772b-69c6-4d6c-97f5-9452f3daaffb",
 "coworldId":"cow_4c005d78-ebb2-4095-83da-cde90519f53b",
 "coworldName":"hanabi","coworldVersion":"0.1.1",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/dac699c0-31b4-4ad7-95de-9e3a5ed34b50.replay",
 "finishedAt":"2026-08-25T02:55:24.836316Z","roundNumber":9,"episodeNumber":1,"code":"hanabi.r9.e1",
 "matchup":{"divisionId":"div_0a3fd174-6ac2-4167-971e-e86f9eb9ed1e","divisionName":"Competition","first":…
```
A featured match **is present**, it is round 9's episode, and it names the **new** coworld
`cow_4c005d78-ebb2-4095-83da-cde90519f53b` at version **0.1.1** — the page has rolled over to the
remediated coworld. (An earlier fetch in this same window, ~02:46Z, still showed the round-8
episode under the same new `cow_4c005d78…`/0.1.1; the first fetch of this window, ~02:21Z — before
round 7 finished publishing — still showed round 6 under the old `cow_2aedf124…`/0.1.0.)

*The iframe `src` itself — the call the page's own JS makes:*
```
POST $BASE/coworlds/replays/session
     content-type: application/json
     {"coworld_id":"cow_4c005d78-ebb2-4095-83da-cde90519f53b",
      "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/dac699c0-31b4-4ad7-95de-9e3a5ed34b50.replay"}
HTTP 200
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_4c005d78-ebb2-4095-83da-cde90519f53b/sha256%3A973eb76b7e4f91c6e246ca20d1063c284ab008112f27189c3566b8c3b3be8c1c/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fdac699c0-31b4-4ad7-95de-9e3a5ed34b50.replay&v=2",
  "ready": true
}
```

Status: **TRUE** —
- path is `/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`;
- `<cow_id>` = `cow_4c005d78-ebb2-4095-83da-cde90519f53b` — the **new** 0.1.1 coworld;
- `<sha>` = `sha256%3A973eb76b7e4f91c6e246ca20d1063c284ab008112f27189c3566b8c3b3be8c1c` — the
  **new** canonical manifest hash, URL-encoded, matching `STATE.coworld.manifest_sha` exactly;
- `ready: true` and the path ends `/index.html` ⇒ static delivery;
- **no `/client/replay` anywhere** in the featured match or the session response.

---

## 7. Certification declared the static bundle — **TRUE**

**Source: the committed `runs/2026-08-24-hanabi/release-result.json`** — the artifact phase 40 /
the 0.1.1 remediation release downloaded and committed. It was **present**; no re-download from
`gh run download` was needed, and `/tmp` was not consulted.

```
$ jq -r '.version, .cow_id, .manifest_sha, .hosted_certification' runs/2026-08-24-hanabi/release-result.json
0.1.1
cow_4c005d78-ebb2-4095-83da-cde90519f53b
sha256:973eb76b7e4f91c6e246ca20d1063c284ab008112f27189c3566b8c3b3be8c1c
certified

$ jq -r '.certify.replay_liveness' runs/2026-08-24-hanabi/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

The file is the **0.1.1** artifact (release run `32799997719`), not the superseded 0.1.0 one: its
`cow_id` and `manifest_sha` match `STATE.coworld` and the iframe `src` in §6 byte for byte, and
its `policies[]` list all four entries at `"version": "v2"`. The certification transcript in the
same file records 10/10 steps passed, ending:

```
  [pass] replay-loadable: the replay artifact has a declared viewer path
  …
Certified dist/coworld_manifest.json
Transcript: coworld-executable (10 steps passed)
…
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE** — contains `Replay liveness: skipped (static replay bundle declared`.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

Dispatched by this verifier against the **exact** iframe `src` from §6:

```
$ date -u                                        2026-08-25T02:58:38Z
$ gh workflow run viewer-check.yml -R Metta-AI/coworld-builder \
    -f url="https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_4c005d78-ebb2-4095-83da-cde90519f53b/sha256%3A973eb76b7e4f91c6e246ca20d1063c284ab008112f27189c3566b8c3b3be8c1c/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fdac699c0-31b4-4ad7-95de-9e3a5ed34b50.replay&v=2" \
    -f timeout=90
DISPATCHED at 2026-08-25T02:58:40Z

$ gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 5 \
  | jq -r 'sort_by(.createdAt)|reverse|.[]|[.databaseId,.createdAt,.status]|@tsv'
32803415305  2026-08-25T02:58:40Z  in_progress     ← created AFTER my dispatch; adopted
32802744596  2026-08-25T02:47:40Z  completed       ← also mine (round-8 replay, earlier in this window)
32800661069  2026-08-25T02:14:39Z  completed       ← another run's; NOT adopted
32798964915  2026-08-25T01:48:40Z  completed       ← verify attempt 1's; NOT adopted
32798180295  2026-08-25T01:36:05Z  completed

$ gh run watch 32803415305 --exit-status ; gh run view 32803415305 --json status,conclusion,createdAt
{"conclusion":"success","createdAt":"2026-08-25T02:58:40Z","status":"completed"}

$ gh run download 32803415305 -R Metta-AI/coworld-builder -n viewer-check \
    -D runs/2026-08-24-hanabi/viewer-check
smoke-stderr.txt  smoke-stdout.txt  viewer-smoke.json  viewer-smoke.png
```

Run adoption is confirmed **from the artifact itself**, not from the run ordering — the url the
CI sandbox actually opened is byte-identical to the §6 `viewer_url`:

```
$ jq -r '.url' runs/2026-08-24-hanabi/viewer-check/viewer-smoke.json
https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_4c005d78-ebb2-4095-83da-cde90519f53b/sha256%3A973eb76b7e4f91c6e246ca20d1063c284ab008112f27189c3566b8c3b3be8c1c/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fdac699c0-31b4-4ad7-95de-9e3a5ed34b50.replay&v=2
```

*(The attempt-1 artifacts in this directory were overwritten; these files are from run
`32803415305`, dispatched 02:58:40Z this window.)*

### 8(b) Readouts, verbatim

```
$ jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-24-hanabi/viewer-check/viewer-smoke.json
{"loaded":true,"ms":2732,"clock":"TURN 0 / 80 · 0 / 25","scorebug":"daveey ▶ 0 BANKED 0 BURNT 0 HINTS daveey-1 0 BANKED 0 BURNT 0 HINTS Tinker 0 BANKED 0 BURNT 0 HINTS Widget 0 BANKED 0 BURNT 0 HINTS","feed_lines":114}

$ jq -c '.signals' …
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}

$ jq -r '.failure // "no failure"' …
no failure

$ jq -c '.canvas_text' …
{"total":9752,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}

$ jq -c '.console_tail' …
["[bridge] loading","[bridge] ready"]
```

The three clock readouts:

| scrub position | `#scrub` clock readout |
|---|---|
| 0 % | `TURN 0 / 80 · 0 / 25` |
| 50 % | `TURN 32 / 80 · 7 / 25` |
| 100 % | `TURN 64 / 80 · 18 / 25 · FINAL` |

A `#scrub` element **is** present (no `"(no #scrub…)"` marker) and the three readouts **differ**
in both turn and score. `loaded: true` via `data-replay-loaded="true"` *and* the `coworld-replay`
bridge's `ready`.

**Item 8 is TRUE** — `loaded: true` AND the three clock readouts differ.

### 8(c) The replay JSON the viewer was asked to draw — reconciliation

```
$ jq -r '.events[]|[.turn,.seat,.kind,.action,.origin,(.banner//"")]|@tsv' /tmp/ep9.replay | head -12
-   -   start   -        -         hanabi
0   0   move    hint     llm       Green 1 is live!
1   1   move    play     llm       Playing the guaranteed 1 from Gizmo's hint
2   2   move    discard  scripted
3   3   move    hint     scripted
4   0   move    hint     retry     White 1 play hint to Widget
5   1   move    hint     llm       Directing Gizmo to play the red 1
6   2   move    hint     scripted
7   3   move    play     scripted
8   0   move    hint     llm       Hinting Bolt's white 2 - playable now
9   1   move    hint     llm       Signaling Widget's blue 1
10  2   move    hint     scripted

… (middle, turns 28-36)
28  0   move    discard  llm       Discarding chop for hints
29  1   move    hint     llm       Red 2 is ready to play!
30  2   move    play     scripted
31  3   move    hint     scripted
32  0   move    discard  llm       Discarding chop to gain hint token
33  1   move    discard  llm       Need hints - discarding chop
34  2   move    hint     scripted
35  3   move    discard  scripted
36  0   move    play     llm       Playing red 2 to advance red stack

$ … | tail -8
57  1   move    play     llm       Green 3 to advance the stack
58  2   move    hint     scripted
59  3   move    play     scripted
60  0   move    play     llm       Playing green 4 from slot 4 — 4 turns remain!
61  1   move    discard  llm       Clearing dead card
62  2   move    discard  scripted
63  3   move    play     scripted
64  -   end     -        -         complete

$ jq -r '.results' /tmp/ep9.replay     → score 18/25, turns 64/80, endReason "deckout",
                                          reason "complete", misplays [0,0,0,0], fallbacks [0,0,0,0]
```

### The spectator-judgment paragraph

**It is legible, it advances, and it plainly shows Hanabi.** `viewer-smoke.png` (the 100 %-scrub
frame, 1280×800) is the bullwhip-lineage chrome, not a rewrite: the same dark transport strip and
title bar (`HANABI` wordmark top-left, `REPLAY` + `« LOG` controls top-right), the same header
clock centred (`TURN 64 / 80 · 18 / 25 · FINAL`), the same per-player scorebug band under it
(`daveey 6 BANKED 0 BURNT 6 HINTS · daveey-1 4 BANKED 0 BURNT 8 HINTS · Tinker 2 BANKED … · Widget
6 BANKED …`), a game-state ribbon (`SCORE 18 / 25 · HINTS ●●○○○○○○ 2 / 8 · FUSES ●●● 3 / 3 · DECK
DECK OUT — 0 TURNS LEFT`), a right-hand event feed, a bottom scrubber whose per-turn tick marks
are colour-coded like paintbot/raid/hive's momentum graph (`66 / 66`, play button at left), and
the same centred **endcard** overlay at the finish. The playfield itself is unmistakably this
game and not a generic board: five colour-ordered firework stacks across the top (R4, Y4, G4, B3,
W3 with `4 / 5`, `4 / 5`, `4 / 5`, `3 / 5`, `3 / 5` under them), a `DISCARDS` strip of greyed
cards with `x2` multipliers, and four cog avatars down the left — `daveey`, `daveey-1`, `Tinker`,
`Widget` — each with its hand drawn face-out and a `N banked · M burnt` line. The **scorebug says
who is winning and the endcard says why**: `FINAL — 64 TURNS · DECK OUT`, `18 / 25 · EXCELLENT`,
`RED 4 · YELLOW 4 · GREEN 4 · BLUE 3 · WHITE 3`, then the per-seat table `1 daveey 6 banked / 0
misplays / 6 hints / 4 discards`, `2 Widget 6/0/4/6`, `3 daveey-1 4/0/8/4`, `4 Tinker 2/0/8/6` —
which reconciles exactly with `results.contributions [6,4,2,6]`, `misplays [0,0,0,0]`, `hints
[6,8,8,4]`, `discards [4,4,6,6]` and `score 18`. (Correctly, the endcard orders by *contribution*
for display while the score column is the shared team 18 — the design's explicit separation of
display ordering from ranking.) It is **not** frozen: the clock advances 0 → 32 → 64 across the
three scrub positions with the score moving 0 → 7 → 18, and the on-screen feed text at 100 %
(`Playing green 4 from slot 4 — 4 turns remain!`, `Clearing dead card`, and in the right rail
`Widget plays a blue 3 — blue reaches 3.`) is exactly events 60, 61 and 63 of the replay JSON —
picture and record agree. It is **not** empty or unreadable: 9 752 canvas text draws, **0**
outside the canvas, **0** ellipsized, **0** never-inside — the phase-30 r1 F1 banner-band sizing
fix is holding under a real render. 114 feed lines. Nothing about the frame is placeholder. One
legibility observation, not a failure: at the 100 % position the endcard overlay dims the hands
and firework stacks behind it, so the final frame reads as a summary card rather than a board —
which is the starter's intended endcard behaviour, and the mid-scrub readout confirms the board is
fully drawn at other positions.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after (v2) fillers set | **TRUE** — rounds 7, 8, 9 completed; fillers registered at v2 ids 02:19Z |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey / daveey-1 at `:v2`, `rounds_played=8`; fillers absent; Elo 1000.0 both = designed co-op behaviour (design.md L191–199) |
| 3 | Latest v2 round's episode request completed w/ replay | **TRUE** — `ereq_2c1119ae…` completed, replay `dac699c0…`, champions in seats 0/1 |
| 4 | Replay bytes valid and show the game | **TRUE** — strict JSON, `hanabi.replay.v1`, `reason:"complete"`, champion seats 32/32 non-scripted, 0 fallbacks |
| 5 | Hosted game log clean | **TRUE** on the scoped round (r9: only the platform Bedrock throttle, cross-checked vs garble + ledger same-window). Caveat §5.3: r7 and r8 each carried 1 `cut off at max_tokens`, recovered by retry, 0 fallbacks |
| 6 | Public page uses the static replay path | **TRUE** — static path, new `cow_4c005d78…` + sha `973eb76b…`, `ready:true`, no `/client/replay`; source = SSR playlist + `POST /coworlds/replays/session` |
| 7 | Certification declared the static bundle | **TRUE** — committed 0.1.1 `release-result.json`: `Replay liveness: skipped (static replay bundle declared; …)` |
| 8 | Viewer executed and judged | **TRUE** — run `32803415305`, `loaded:true`, `ms:2732`, clocks 0 → 32 → 64 differ, 0 ellipsized/outside draws |

Retry budget used: check 5 took 3 attempts (rounds 7, 8, 9 — a different round each time);
all other checks passed on attempt 1. Wall clock used: 43 of 75 minutes.
