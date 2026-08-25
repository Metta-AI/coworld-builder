# VERIFY — hanabi   (2026-08-25T01:52Z)

Verdict: **1 item false** (check 5). Checks 1, 2, 3, 4, 6, 7, 8 are TRUE.

Run: `2026-08-24-hanabi` · coworld `cow_2aedf124-df70-45ce-b307-fa693c6d1943` v0.1.0 ·
league `league_332c17c5-b6bf-4341-98c7-3161dd58e6d8` · division `div_0a3fd174-6ac2-4167-971e-e86f9eb9ed1e`.

All calls below were made **this run** (2026-08-25T01:11Z–01:52Z) with
`-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0"` (named, never
printed), plus `-H "X-Use-Elevated-Privileges: true"` where noted. `BASE=https://softmax.com/api/observatory/v2`.
The two documented exceptions to "fetch fresh": check 7 reads the committed
`runs/2026-08-24-hanabi/release-result.json`, and check 8's rendered evidence comes from the
`viewer-check.yml` run **this verifier dispatched at 01:48:39Z** (run 32798964915).

The "latest completed round" at the time of these fetches is **round 4**
(`round_eb91b66e-46f4-4d0c-a66e-5f1a3014f229`, completed 01:47:24Z); checks 3–6 and 8 all use that
same round's episode `ereq_02fb8088-05ca-4d93-94e3-9f2091e9654c`. Round 5 had not yet been created
when this file was written.

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

```
GET $BASE/rounds?league_id=league_332c17c5-b6bf-4341-98c7-3161dd58e6d8&limit=20      (01:48:11Z)
```
```json
[
  {
    "id": "round_eb91b66e-46f4-4d0c-a66e-5f1a3014f229",
    "round_number": 4,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-25T01:39:26.621826Z",
    "completed_at": "2026-08-25T01:47:24.010706Z"
  },
  {
    "id": "round_60dc0fb8-cfe8-4714-acb4-e376a099c4fe",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-25T01:24:26.244523Z",
    "completed_at": "2026-08-25T01:32:15.343068Z"
  },
  {
    "id": "round_6532a9d6-62db-4147-b768-90a01df682e7",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-25T01:09:25.856503Z",
    "completed_at": "2026-08-25T01:17:30.753516Z"
  },
  {
    "id": "round_a03839eb-14d2-48c4-adb7-daf2b764258d",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-25T01:09:00.381487Z",
    "completed_at": "2026-08-25T01:09:00.603201Z"
  }
]
```
```
$ jq -r '... | [.[]|select(.status=="completed")]|length'
3
```

Round 1 is **failed**, `error` verbatim: `Temporal RoundWorkflow failed before settling the round.`
It auto-fired at 01:09:00Z, *before* the filler policies existed (playbook §6: a `trigger-round`
issued before any filler exists fails instantly with exactly this message) and its
`entrant_attributions` carried only champion #1. It does not count.

Fillers are registered and were in force for rounds 2–4:
```
GET $BASE/leagues/$L/filler-policies      (headers: Authorization, User-Agent, X-Use-Elevated-Privileges)
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"bbafc232-9fdd-4ac6-9ff5-353feeb79ca7","policy_name":"hanabi-conventions","version":1,"player_name":"daveey"},
 {"policy_version_id":"e6ed90d3-3e1e-4285-ad9c-ff8698921ed5","policy_name":"hanabi-cautious","version":1,"player_name":"daveey"}]}
```
`log.md` records the registration at `2026-08-25T01:10:33Z 50 fillers 200: conventions=bbafc232
cautious=e6ed90d3; unpause 200; trigger 200`. Direct proof they were applied: every completed
round's episode seats two `is_filler: true` participants and the replay `policyNames` read
`["daveey","daveey-1","Baseline","Baseline (2)"]` (checks 3 and 4 below).

Entrant attributions, same fetch:
```json
round 4/3/2: [{"subject_id":"ply_44ae9048-…","policy_version_id":"6f6352cd-4881-49bd-82be-d7522217c7ef"},
              {"subject_id":"ply_bac48eb1-…","policy_version_id":"aa3cdaaa-a8ff-4aaa-abca-08c96f7a641d"}]
round 1:     [{"subject_id":"ply_44ae9048-…","policy_version_id":"6f6352cd-4881-49bd-82be-d7522217c7ef"}]   ← one entrant, no fillers
```

Status: **TRUE** — 3 completed rounds (2, 3, 4), all with `round_number ≥ 2`, i.e. after the round
in which the fillers were registered; the only failed round is round 1 and its error is quoted above.

---

## 2. Both champions ranked — **TRUE** (with the cooperative-Elo design note said out loud)

```
GET $BASE/divisions/div_0a3fd174-6ac2-4167-971e-e86f9eb9ed1e/leaderboard      (01:48:11Z; bare list)
```
```
rank  player_name  policy_label          score    score_label  rounds_played  episode_wins
1     daveey       hanabi-signaler:v1    1000.0   Elo          3              0.0
2     daveey-1     hanabi-reader:v1      1000.0   Elo          3              0.0
```
```json
[{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1000.0,"score_label":"Elo","score_value_type":"integer","rounds_played":3,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"hanabi-signaler:v1","recent_rounds":null},
 {"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":1000.0,"score_label":"Elo","score_value_type":"integer","rounds_played":3,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"hanabi-reader:v1","recent_rounds":null}]
```

**Saying it out loud, as the design note requires (`runs/2026-08-24-hanabi/design.md` L191–199):**
Hanabi is **fully cooperative** — every seat receives the identical team score — so head-to-head Elo
*never separates the two champions*: "they will sit at 1000.0 forever (cogame-raid learning 5,
2026-08-23) … Phase 60 should judge check 2 on the division leaderboard's `score`/`rounds_played`
columns, not on Elo spread." The `score` column the platform exposes here is labelled `Elo` and reads
exactly the initial 1000.0 for both, which is the **expected** value for this game, not a failure.
What actually separates the champions is the mean team score per episode, which the leaderboard does
not surface; the per-episode team scores this run are **14 (r2), 16 (r3), 15 (r4)** out of 25 — every
seat identical, exactly as `results.scores` prescribes (`participant_scores` in check 3, `results` in
check 4).

Both champions are present with `rounds_played = 3 ≥ 1`; the two fillers (`hanabi-conventions:v1`,
`hanabi-cautious:v1`) are **absent** from the leaderboard entirely, as required.

Status: **TRUE** — `daveey`/`hanabi-signaler:v1` and `daveey-1`/`hanabi-reader:v1` both ranked with
3 rounds played; fillers absent; Elo-at-1000 is the documented cooperative-game expectation.

---

## 3. Latest round's episode request completed with a replay — **TRUE**

```
GET $BASE/episode-requests?round_id=round_eb91b66e-46f4-4d0c-a66e-5f1a3014f229&limit=20   (01:48Z)
```
```json
[{"id":"ereq_02fb8088-05ca-4d93-94e3-9f2091e9654c","status":"completed","created_at":"2026-08-25T01:39:26.873363Z"}]
```
```
GET $BASE/episode-requests/ereq_02fb8088-05ca-4d93-94e3-9f2091e9654c
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/cb416080-e376-425c-a37f-0f3185cf1f73.replay",
  "participants": [
    {"position": 0, "policy_name": "hanabi-signaler",    "player_name": "daveey",   "is_filler": false},
    {"position": 1, "policy_name": "hanabi-reader",      "player_name": "daveey-1", "is_filler": false},
    {"position": 2, "policy_name": "hanabi-conventions", "player_name": "daveey",   "is_filler": true},
    {"position": 3, "policy_name": "hanabi-conventions", "player_name": "daveey",   "is_filler": true}
  ],
  "participant_scores": [
    {"position": 0, "score": 15.0}, {"position": 1, "score": 15.0},
    {"position": 2, "score": 15.0}, {"position": 3, "score": 15.0}
  ]
}
```

Status: **TRUE** — `status: "completed"`, non-null `replay_url`, seats 0/1 are the champions
`daveey` (`hanabi-signaler`) and `daveey-1` (`hanabi-reader`), seats 2/3 are `is_filler: true`
(rendered `Baseline` / `Baseline (2)` in the replay's `policyNames`). All four scores identical at
15.0 — the cooperative team score.

---

## 4. Replay bytes are valid and show the game — **TRUE**

```
$ curl -sSL "https://softmax-public.s3.amazonaws.com/replays/cb416080-e376-425c-a37f-0f3185cf1f73.replay" -o /tmp/ep4.replay -w '%{http_code} %{size_download}\n'
200 29152
$ jq -e . /tmp/ep4.replay >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok
$ python3 -c "d=open('/tmp/ep4.replay','rb').read(); d.decode('utf-8'); print('strict utf-8 decode ok:', len(d), 'bytes')"
strict utf-8 decode ok: 29152 bytes
$ jq -r '.protocol, .results.reason, .results.endReason' /tmp/ep4.replay
hanabi.replay.v1
complete
deckout
$ jq -c '.names,.policyNames,.config,.results' /tmp/ep4.replay
["Flywheel","Rivet","Sprocket","Gasket"]
["daveey","daveey-1","Baseline","Baseline (2)"]
{"maxTurns":80,"seed":800569601,"sampled":true}
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],"scores":[15,15,15,15],"score":15,
 "fireworks":[2,5,2,3,3],"contributions":[5,3,2,3],"plays":[6,4,2,3],"misplays":[1,1,0,0],
 "discards":[4,5,5,6],"hints":[6,6,9,7],"fallbacks":[0,0,0,0],"turns":65,"maxTurns":80,
 "deckLeft":0,"endReason":"deckout","reason":"complete"}
```

**Protocol match.** The replay declares `"protocol": "hanabi.replay.v1"`, which is exactly the
replay payload protocol the design declares (`design.md` L655:
`{"protocol":"hanabi.replay.v1","names":[aliases],"policyNames":[policy names], …}`). Cross-checked
against the live manifest:
```
GET $BASE/coworlds/cow_2aedf124-df70-45ce-b307-fa693c6d1943
$ jq -r '.manifest.game.protocols | to_entries[] | "\(.key): \(.value.value[0:60])"'
player: hanabi.player.v1 - JSON text frames over the websocket named
global: Global spectators connect a websocket to /global and receive
$ jq -r '{name,version,manifest_hash}'
{"name":"hanabi","version":"0.1.0","manifest_hash":"sha256:937abbbc18b84262d82e5adb2b5e538641b4499542edfabdf8784f718f4e70b1"}
```
The manifest names the `hanabi.*.v1` protocol family and its `global` protocol text specifies the
replay's own event schema verbatim — "exactly three kinds: start (seed, seats, handSize, maxTurns),
move (…, origin llm|retry|fallback|scripted, the seat's note and its spectator-only banner) and end
(turn, text complete|deadline, endReason, score, fireworks, digest)". The fetched replay satisfies
that schema exactly (see below). The manifest carries no separate literal replay-protocol string;
this is the closest declared source and it agrees.

**`results.reason == "complete"`** — the normal ending (the `deadline` enum value the design also
declares acceptable was not needed). `endReason: "deckout"` is one of the four legal
`complete` sub-reasons (`perfect|strikeout|deckout|turnlimit`).

**Champion decisions are non-scripted and non-trivial; fallbacks are zero, not a minority — none.**
```
$ jq -r '[.events[]|select(.kind=="move")]|length' /tmp/ep4.replay
65
$ jq -r '[.events[]|select(.kind=="move")|.origin]|group_by(.)|map("\(.[0])=\(length)")|join(" ")'
llm=30 retry=3 scripted=32
$ jq -r '[.events[]|select(.kind=="move" and (.seat==0 or .seat==1))|.origin]|group_by(.)|map("\(.[0])=\(length)")|join(" ")'
llm=30 retry=3
```
The 32 `scripted` moves are the two **filler** seats (that is what a scripted baseline is). The two
**champion** seats produced 33 decisions, all LLM-authored: 30 first-attempt (`llm`) and 3 second-attempt
(`retry`); **zero** `fallback` origins, corroborated by `results.fallbacks == [0,0,0,0]`.

Champion-seat content (ordered excerpts; `text` is the seat's own note, `banner` the spectator line):
```
turn seat kind action origin  text
0    0    move hint   retry   T0: Told Sprocket 1s (slots 2,3). Newest touched=slot2=yellow 1, play hint. Rivet has blue 2, r…
1    1    move hint   llm     T0: Flywheel hinted Sprocket's 1s (3 cards). Pattern: rank hints seem to signal plays. Sprocket…
4    0    move play   llm     T0: Told Sprocket 1s. T3: Gasket told me red (slots 1,4). Slot 1=red 1 played. Rivet: y3,b2,r2,…
5    1    move discard llm    Pattern confirmed: rank hints signal plays. Sprocket should play yellow 1 next. Discarding chop…
32   0    move hint   llm     [banner] Yellow 5 ready to complete the firework!
33   1    move discard llm    [banner] Discarding chop - need hints!
36   0    move play   llm     [banner] Green 2 advances the stack!
37   1    move hint   llm     [banner] Saving critical blue 1
60   0    move play   llm     [banner] Playing slot 2 - blue 3 or white 3, both advance stacks
61   1    move discard llm    [banner] Clearing dead card, 1 fuse left - playing it safe
64   0    move play   llm     [banner] Endgame: playing blue 3 for 15, Rivet to finish with green 3
65   -    end                 complete
```
That is Hanabi being played: play-hints by rank and colour, chop discards, saving criticals, dead-card
clearing, and an explicit endgame count. Final event:
```json
{"kind":"end","turn":65,"text":"complete","endReason":"deckout","score":15,"fireworks":[2,5,2,3,3],"hintTokens":1,"fuses":1,"deck":0,"countdown":0,"digest":"d7ce2f30cb61f83c"}
```

Status: **TRUE** — strict-parser-valid UTF-8 JSON; protocol `hanabi.replay.v1` as declared;
`results.reason == "complete"`; 33 champion decisions, 0 fallbacks, substantive Hanabi reasoning.

---

## 5. Hosted game log is clean — **FALSE**

```
GET $BASE/episode-requests/ereq_02fb8088-05ca-4d93-94e3-9f2091e9654c/artifacts/logs
    (headers: Authorization, User-Agent, X-Use-Elevated-Privileges)   → 200, 81643 bytes
```
The body is python `b'…'` byte-string reprs under `===== container: … =====` headers; decoded per
repr with `ast.literal_eval` before grepping (playbook §10), then:
```
$ grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' <decoded>
173:hanabi llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
174:hanabi llm: seat 0 attempt 0 rejected: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
225:hanabi llm: seat 1 attempt 0 rejected: unbalanced JSON object in response
232:hanabi llm: seat 0 attempt 0 rejected: unbalanced JSON object in response
TOTAL HITS: 4
```
Not `CLEAN` → **FALSE**. In context (decoded log, round 4):
```
171:hanabi: episode timeout 1200s (assumed); playing until 720s
172:hanabi: turn 0 of 80, seat 0 (Flywheel) at 7s
173:hanabi llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
174:hanabi llm: seat 0 attempt 0 rejected: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
175:hanabi: turn 0 Flywheel hint 2 1 (retry)
…
224:hanabi: turn 25 of 80, seat 1 (Rivet) at 159s
225:hanabi llm: seat 1 attempt 0 rejected: unbalanced JSON object in response
226:hanabi: turn 25 Rivet hint 0 green (retry)
…
231:hanabi: turn 28 of 80, seat 0 (Flywheel) at 182s
232:hanabi llm: seat 0 attempt 0 rejected: unbalanced JSON object in response
233:hanabi: turn 28 Flywheel hint 2 1 (retry)
309:hanabi: episode complete; serving for another 20s before shutting down
```

**Lines 173–174 are the documented platform-wide Bedrock capacity symptom, cross-checked against two
other LLM coworlds' latest completed episodes, fetched this run:**
```
garble  ereq_7c93877c-e0eb-4153-b695-5cc69b075e5a (created 2026-08-25T01:28:41Z), decoded log line 92:
  garble llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-6…
  …bedrock-sidecar: "HTTP/1.1 429 Too Many Requests" … "error_type":"ThrottlingException","message":"Too many tokens per day, please wait before trying again."
ledger  ereq_6e06268e-c92b-48ba-aae6-b9ca551b6eaa (created 2026-08-25T01:23:22Z), decoded log line 276:
  ledger llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
  …bedrock-sidecar: "HTTP/1.1 429 Too Many Requests" … "error_type":"ThrottlingException","message":"Too many tokens per day, please wait before trying again."
```
Two unrelated coworlds hitting the identical haiku day-quota 429 within five minutes of hanabi's
episode is the shared-Bedrock-capacity condition SPEC §Parallelism names; per `prompts/60-verify.md`
check 5 that pair of lines is **not a defect in this coworld** (hanabi degraded correctly: it moved
to sonnet and the seat still got an LLM decision, `origin=retry`).

**Lines 225 and 232 are hanabi's own residue and are NOT covered by any documented exception.** The
model returned an unparsable (`unbalanced JSON object`) reply on the first attempt for a champion seat;
the retry succeeded both times (turn 25 → `hint 0 green (retry)`, turn 28 → `hint 2 1 (retry)`), so no
episode outcome was harmed and `results.fallbacks == [0,0,0,0]`. But the check's bar is zero
`rejected` lines, and this is recurrent, not a fluke — **three attempts, three different rounds, all
this run**:

| attempt | round / episode | hits | breakdown |
|---|---|---|---|
| 1 | round 3 · `ereq_c21643af-73b7-4231-9154-835d5c350932` | 4 | 1 × haiku-throttled/falling back, 1 × `rejected: llm throttled (429)`, **2 × `rejected: unbalanced JSON object in response`** (seat 0, turns 32 & 40) |
| 2 | round 2 · `ereq_78c2f0be-81af-417b-8bd3-2bf5b1e3c198` | 7 | 1 × haiku-throttled/falling back, 1 × `rejected: llm throttled (429)`, **4 × `rejected: unbalanced JSON object`**, **1 × `rejected: reply cut off at max_tokens before any JSON`** (seat 1, turn 61) |
| 3 | round 4 · `ereq_02fb8088-05ca-4d93-94e3-9f2091e9654c` (latest) | 4 | 1 × haiku-throttled/falling back, 1 × `rejected: llm throttled (429)`, **2 × `rejected: unbalanced JSON object`** |

Round 2's extra line, verbatim (this is the one `prompts/60-verify.md` says to fix by raising
`maxOutputTokens` to 900 and re-releasing — it did **not** recur in rounds 3 or 4):
```
hanabi llm: seat 1 attempt 0 rejected: reply cut off at max_tokens before any JSON: I need to analyze the current situation carefully.  **Current state:** - Score: 10/25, hints: 0/8, fuses: 2/3, deck: 2 cards left - Stacks: red 2, yellow 1, gre
```
For comparison, garble and ledger show **only** the throttle line (`TOTAL HITS: 1` each) and no
`unbalanced JSON` rejections — so the malformed-reply rejections are specific to hanabi's
reply contract, not platform weather.

Status: **FALSE** — the latest round's hosted log is not CLEAN. 2 of the 4 hits
(`falling back` + `rejected: llm throttled (429)`) are the documented platform-wide Bedrock
capacity symptom, cross-checked above. The remaining 2 (`seat N attempt 0 rejected: unbalanced JSON
object in response`) are hanabi's own and have no documented exception. Impact is bounded — every
rejection was recovered by the retry, 0 fallbacks, 0 lost turns, `reason: complete` — but the check
as written requires CLEAN, so this item is false and is reported, not waived.

---

## 6. The public page uses the static replay path — **TRUE**

Source used: **both** — the prescribed raw-HTML grep first (found nothing), then the page's own SSR
payload and the replay-session route the page's JS calls (playbook §Featured match / replay route).

```
$ curl -sS "https://softmax.com/hanabi" -o page.html -w '%{http_code} %{size_download}\n'     (01:48:29Z)
200 535661
$ grep -o '<iframe[^>]*src="[^"]*"' page.html
(no match — the page is client-rendered; per the playbook this is *unknown*, not a false negative)
```

Featured match, server-rendered into the page's SSR payload at `state.playlist[0]` (verbatim excerpt,
backslash-escaping as it appears in the HTML):
```
playlist\":[{\"episodeId\":\"f6172076-96b8-44e2-8b79-86f69947b8e9\",\"coworldId\":\"cow_2aedf124-df70-45ce-b307-fa693c6d1943\",\"coworldName\":\"hanabi\",\"coworldVersion\":\"0.1.0\",\"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/cb416080-e376-425c-a37f-0f3185cf1f73.replay\",\"finishedAt\":\"2026-08-25T01:47:23.064794Z\",\"roundNumber\":4,\"episodeNumber\":1,\"code\":\"hanabi.r4.e1\",\"matchup\":{\"divisionId\":\"div_0a3fd…
```
(the earlier page fetch at 01:35:44Z featured `hanabi.r3.e1`; the page tracks the latest completed
round, and the featured replay is exactly check 3's `replay_url`.)
The matchup names both champions:
```
\"first\":{\"rank\":1,\"player_name\":\"daveey\",\"policy_label\":\"hanabi-signaler:v1\",…},
\"second\":{\"rank\":2,\"player_name\":\"daveey-1\",\"policy_label\":\"hanabi-reader:v1\",…}
```

The iframe `src` itself comes from the call the page's JS makes:
```
POST $BASE/coworlds/replays/session
  {"coworld_id":"cow_2aedf124-df70-45ce-b307-fa693c6d1943",
   "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/cb416080-e376-425c-a37f-0f3185cf1f73.replay"}
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_2aedf124-df70-45ce-b307-fa693c6d1943/sha256%3A937abbbc18b84262d82e5adb2b5e538641b4499542edfabdf8784f718f4e70b1/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fcb416080-e376-425c-a37f-0f3185cf1f73.replay&v=2",
  "ready": true
}
```
The API's own `/coworlds` row (fetched 01:12Z) reports `replay_viewer: null` and
`featured_match: null` — the platform-wide nulls the playbook records, not evidence either way:
```json
{"id":"cow_2aedf124-df70-45ce-b307-fa693c6d1943","name":"hanabi","canonical":true,"version":"0.1.0","replay_viewer":null,"featured_match":null}
```

Status: **TRUE** — the route is
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` with
`<cow_id> = cow_2aedf124-df70-45ce-b307-fa693c6d1943` and `<sha> =
sha256:937abbbc18b84262d82e5adb2b5e538641b4499542edfabdf8784f718f4e70b1` (URL-encoded), which is the
coworld's `manifest_hash` and matches `STATE.coworld.manifest_sha`. `ready: true` ⇒ static delivery.
**No `/client/replay` pod URL anywhere.** A featured match is present (round 4, episode 1, both
champions ranked in the matchup).

---

## 7. Certification declared the static bundle — **TRUE**

Source: the **committed** `runs/2026-08-24-hanabi/release-result.json` (the artifact phase 40
downloaded from release run 32795286182); it was present, so no re-download was needed.
```
$ jq -r '.certify.replay_liveness' runs/2026-08-24-hanabi/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE** — the string contains `Replay liveness: skipped (static replay bundle declared`
exactly as required. Read from the committed copy, not `/tmp`.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

*(a) Dispatch.* Dispatched **this run**, against the check-6 iframe `src` verbatim:
```
$ date -u  → 2026-08-25T01:48:39Z   (dispatch time)
$ gh workflow run viewer-check.yml -R Metta-AI/coworld-builder \
    -f url="https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_2aedf124-df70-45ce-b307-fa693c6d1943/sha256%3A937abbbc18b84262d82e5adb2b5e538641b4499542edfabdf8784f718f4e70b1/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fcb416080-e376-425c-a37f-0f3185cf1f73.replay&v=2" \
    -f timeout=90
$ gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 5 | jq 'sort_by(.createdAt)|reverse'
[{"createdAt":"2026-08-25T01:48:40Z","databaseId":32798964915,"status":"in_progress"},
 {"createdAt":"2026-08-25T01:36:05Z","databaseId":32798180295,"status":"completed"},
 {"createdAt":"2026-08-24T21:53:57Z","databaseId":32781916776,"status":"completed"}]
$ gh run watch 32798964915 -R Metta-AI/coworld-builder --exit-status ; echo $?
0
$ gh run view 32798964915 --json status,conclusion,createdAt,updatedAt
{"conclusion":"success","status":"completed","createdAt":"2026-08-25T01:48:40Z","updatedAt":"2026-08-25T01:49:20Z"}
$ gh run download 32798964915 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-24-hanabi/viewer-check
```
Run **32798964915** was created at 01:48:40Z, i.e. *after* my 01:48:39Z dispatch (the run above it is
12 minutes older), and the artifact's own `url` field matches the URL I dispatched byte-for-byte:
```
$ jq -r .url runs/2026-08-24-hanabi/viewer-check/viewer-smoke.json
https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_2aedf124-df70-45ce-b307-fa693c6d1943/sha256%3A937abbbc18b84262d82e5adb2b5e538641b4499542edfabdf8784f718f4e70b1/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fcb416080-e376-425c-a37f-0f3185cf1f73.replay&v=2
```
(An earlier viewer-check this run, 32798180295 at 01:36:05Z against round 3's replay, was also green
with `loaded:true` and three differing clocks; the committed artifact is the later one, for the same
episode all the other checks use.)

*(b) The readouts, verbatim from `runs/2026-08-24-hanabi/viewer-check/viewer-smoke.json`.*
```json
{"loaded":true,"ms":962,"clock":"TURN 0 / 80 · 0 / 25","scorebug":"daveey ▶ 0 BANKED 0 BURNT 0 HINTS daveey-1 0 BANKED 0 BURNT 0 HINTS Sprocket 0 BANKED 0 BURNT 0 HINTS Gasket 0 BANKED 0 BURNT 0 HINTS","feed_lines":119}
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```
```
$ jq -r '.failure // "no failure"'   →  no failure
$ jq -c '.canvas_text'  → {"total":10502,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
$ jq -c '.status, .loading_text, .console_tail' → "REPLAY"  "LOADING REPLAY…"  ["[bridge] loading","[bridge] ready"]
```

**The three scrub readouts (they differ)** —
`jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-24-hanabi/viewer-check/viewer-smoke.json`:
```
0%	TURN 0 / 80 · 0 / 25
50%	TURN 33 / 80 · 7 / 25
100%	TURN 65 / 80 · 15 / 25 · FINAL
```

| scrub position | `clock` |
|---|---|
| 0 %   | `TURN 0 / 80 · 0 / 25` |
| 50 %  | `TURN 33 / 80 · 7 / 25` |
| 100 % | `TURN 65 / 80 · 15 / 25 · FINAL` |

Status: **TRUE** — `loaded: true` (via `data-replay-loaded="true"` *and* the `coworld-replay`
bridge's `ready`), first frame at **962 ms**, no failure, and the three clock readouts differ:
turn 0 → 33 → 65 and score 0 → 7 → 15. The replay advances; it is not a screenshot.

*(c) Reconciliation with the replay JSON (`/tmp/ep4.replay`, check 4).* The 100 % readout
`TURN 65 / 80 · 15 / 25 · FINAL` equals `results.turns = 65`, `maxTurns = 80`, `score = 15`; the
50 % readout `TURN 33` sits at the midpoint of a 65-turn episode with score 7 en route to 15.
The two banner chips visible on the right of the screenshot are the last two champion banners in the
record: turn 61 `Clearing dead card, 1 fuse left - playing it safe` (seat 1) and turn 64
`Endgame: playing blue 3 for 15, Rivet to finish with green 3` (seat 0); the feed's newest line
"daveey plays a blue 3 — blue reaches 3." is that same turn-64 move. Picture and record agree.

**Spectator judgment.** The screenshot (`runs/2026-08-24-hanabi/viewer-check/viewer-smoke.png`,
1280×800) is legible and unmistakably Hanabi. Top strip: the `HANABI` wordmark, the clock
`TURN 65 / 80 · 15 / 25 · FINAL`, a `REPLAY` badge and a `« LOG` toggle. Below it the four-seat
scorebug — `daveey 6 BANKED 1 BURNT 6 HINTS · daveey-1 4 BANKED 1 BURNT 6 HINTS · Sprocket 2 BANKED
0 BURNT 9 HINTS · Gasket 3 BANKED 0 BURNT 7 HINTS` — then the resource band
`SCORE 15 / 25 · HINTS ●○○○○○○○ 1 / 8 · FUSES ●○○ 1 / 3 · DECK **DECK OUT — 0 TURNS LEFT**`. The
board shows the five firework stacks as coloured cards with their heights (`R2 2/5`, `Y5 DONE`,
`G2 2/5`, `B3 3/5`, `W3 3/5` — exactly `results.fireworks = [2,5,2,3,3]`), a `DISCARDS` ribbon of
greyed rank chips with `×2` multipliers, and four seat rows each with a cog portrait, name, running
"N banked · M burnt" and its four face-up cards in the card palette. On the right is the move feed
(119 lines) and two banner chips carrying the champions' own words. Across the bottom is the
transport strip: a `▶` play button, the scrubber drawn as a **momentum graph** — a tick per turn,
coloured by what happened (green/blue/red spikes for plays, hints and misplays) — and the frame
counter `67 / 67`. Centred over the board is the **endcard**: `FINAL — 65 TURNS · DECK OUT`,
`15 / 25 · HONOURABLE`, the stack line `RED 2 · YELLOW 5 · GREEN 2 · BLUE 3 · WHITE 3`, and a ranked
table `1 daveey 6/1/6/4 · 2 daveey-1 4/1/6/5 · 3 Gasket 3/0/7/6 · 4 Sprocket 2/0/9/5`
(BANKED / MISPLAYS / HINTS / DISCARDS) — every number matching `results.plays`, `misplays`, `hints`,
`discards`. So yes: it says who did what and why, and because the score is a shared team score, the
endcard's headline (`15 / 25 · HONOURABLE`) correctly reports the *team* result rather than a winner,
with the per-seat table showing contribution — the right presentation for a cooperative game.
No empty canvas, no frozen frame, no clipped text (`canvas_text`: 10 502 strings drawn, 0 ever
outside the canvas, 0 ellipsized).

**It looks like the starter's chrome, not a rewrite.** Transport strip with play button and
momentum-graph scrubber, four-seat scorebug across the top, clock in the header, right-hand feed with
banner chips, and a centred endcard over a dimmed board — the same paintbot/raid/hive/bullwhip
lineage furniture, in the same positions, with the Hanabi board (fireworks, discards, hands) dropped
into the arena slot. This is not the cogame-gridlock failure mode.

Two legibility observations for the coordinator (neither is a check failure):
1. The two **filler seats render under their in-game cog aliases** (`Sprocket`, `Gasket`) rather than
   the replay's `policyNames` entries `Baseline` / `Baseline (2)`. This is deliberate — the renderer's
   `makeNameMap` substitutes a policy name only when `!isBaselineFiller(policy)` (`client/renderer.js`
   L730-735) — but it does mean a spectator cannot tell from the scorebug or the endcard which two
   seats are scripted baselines and which two are the champions being ranked.
2. The screenshot is taken at 100 % scrub, so the board is dimmed under the endcard overlay; the
   underlying board is still readable through it. Nothing to fix, noted so the picture is not
   mistaken for a fade-out bug.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | **TRUE** — rounds 2, 3, 4 completed; round 1 failed pre-fillers (error quoted) |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey + daveey-1, `rounds_played` 3 each; Elo 1000.0 is the documented cooperative-game expectation |
| 3 | Latest round's episode completed with a replay | **TRUE** — `ereq_02fb8088…` completed, `replay_url` non-null, champions in seats 0/1 |
| 4 | Replay bytes valid and show the game | **TRUE** — strict UTF-8 JSON, `hanabi.replay.v1`, `reason: complete`, 33 champion decisions, 0 fallbacks |
| 5 | Hosted game log clean | **FALSE** — 4 hits: 2 are the platform-wide Bedrock throttle (cross-checked vs garble + ledger), 2 are hanabi's own `rejected: unbalanced JSON object in response` (recurrent in rounds 2, 3, 4; each recovered by retry) |
| 6 | Public page uses the static replay path | **TRUE** — `/v2/coworlds/replays/static/<cow_id>/<manifest sha>/index.html?replay=<s3 url>`, `ready: true`, featured match `hanabi.r4.e1` |
| 7 | Certification declared the static bundle | **TRUE** — `Replay liveness: skipped (static replay bundle declared; …)` from the committed `release-result.json` |
| 8 | Spectator judgment (viewer executed) | **TRUE** — run 32798964915, `loaded: true` at 962 ms, three differing clocks (0/33/65), starter chrome, legible |
