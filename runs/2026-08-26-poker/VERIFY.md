# VERIFY — poker   (2026-08-26T19:28Z)

Verdict: **all-true** (8/8)

Coworld `cow_08add75e-311a-46ba-9b5d-05888954986e` v0.1.0 · league
`league_14d979bc-860c-4c64-a706-e867a2ac1ca5` · division `div_2c39ffc7-6856-4d5f-ad55-c19072cd23b6`.

Common preamble for every `curl` below (header **names** only; values never printed):

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_14d979bc-860c-4c64-a706-e867a2ac1ca5
D=div_2c39ffc7-6856-4d5f-ad55-c19072cd23b6
COW=cow_08add75e-311a-46ba-9b5d-05888954986e
```

**Subject of checks 3–8: round 3** (`round_d02f4885-e289-4a51-bb73-21a12fc789c9`), the latest
completed round at verification time. See the *Anomaly* section at the foot: rounds 1 and 2 ran
100 % scripted-fallback because the platform's LLM sidecar was routed to `openrouter.ai` and
returned `402 Payment Required` on every call. That condition cleared before round 3, which ran
entirely on Bedrock with **zero** fallbacks. Every check below is fetched fresh this run.

Polling window opened 18:40:54Z, closed 19:22:07Z (41 min of the 75-minute bound).

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

Fillers `poker-house:v1` + `poker-rock:v1` were registered at **2026-08-26T18:39:20Z**
(`runs/2026-08-26-poker/log.md:65` — `50 fillers registered while paused: house+rock only, 200`).

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq 'if type=="array" then . else .entries end | map({id,round_number,status,error,created_at,completed_at})'
```

```json
[
  {
    "id": "round_d02f4885-e289-4a51-bb73-21a12fc789c9",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-26T19:08:59.710100Z",
    "completed_at": "2026-08-26T19:19:55.188872Z"
  },
  {
    "id": "round_de5fd089-8ad3-4f70-b5c3-188e962553d7",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-26T18:53:58.941810Z",
    "completed_at": "2026-08-26T19:03:27.759747Z"
  },
  {
    "id": "round_7955fa79-32df-44e5-8ec9-4382fda1bffc",
    "round_number": 1,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-26T18:38:58.534906Z",
    "completed_at": "2026-08-26T18:51:55.933729Z"
  }
]
```

```bash
$ … | jq -r '"completed count: " + ([(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length|tostring)'
completed count: 3
```

Status: **TRUE**. Three rounds `completed`, zero `failed`/`discarded`, every `error` null.
Rounds **2** (`created_at` 18:53:58.941810Z) and **3** (19:08:59.710100Z) were both created
*strictly after* the fillers were registered at 18:39:20Z — that alone satisfies the "≥ 2 after
the fillers" requirement. Round 1's `created_at` of 18:38:58.534906Z in fact precedes filler
registration by 22 s (the ladder pre-created it at settings time; `log.md:66` records the
`trigger-round` at 18:39:50Z and `log.md:67` round 1 still `pending` at 18:40:30Z), so it is
**not** counted toward this check. The check passes on rounds 2 and 3 alone.

`/rounds` returned the wrapped `{entries:[…]}` shape this run (`jq -r 'type'` → `object`), not the
bare array phase 50 saw on `/leagues`; the dual-shape filter handled it.

---

## 2. Both champions ranked — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq .
```

```json
[
  {
    "rank": 1,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 1043.747133633611,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 3,
    "episode_wins": 3.0,
    "episodes_played": null,
    "win_rate": 1.0,
    "policy_label": "poker-exploiter:v1",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 956.2528663663891,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 3,
    "episode_wins": 0.0,
    "episodes_played": null,
    "win_rate": 0.0,
    "policy_label": "poker-scholar:v1",
    "recent_rounds": null
  }
]
```

Status: **TRUE**. Bare JSON list as documented. `daveey-1` / `poker-exploiter:v1` at rank 1 with
`rounds_played: 3`; `daveey` / `poker-scholar:v1` at rank 2 with `rounds_played: 3` — both ≥ 1.
The fillers `poker-house:v1` and `poker-rock:v1` are **absent** from the board entirely (the list
has exactly two rows), which satisfies the "absent or `Baseline…`" condition. Both champion
`player_id`s match STATE exactly.

---

## 3. Latest round's episode request completed with a replay — **TRUE**

The flat `GET /episode-requests?round_id=` route 405s (playbook §9), so the nested route was used.

```bash
R=round_d02f4885-e289-4a51-bb73-21a12fc789c9        # max round_number among completed
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" \
 | jq 'if type=="array" then . else .entries end | map({id,status,created_at})'
```

```json
[
  {
    "id": "ereq_6c5ec646-5fc3-4529-898e-e3c6db646318",
    "status": "completed",
    "created_at": "2026-08-26T19:09:00.101232Z"
  }
]
```

```bash
curl -sS "$BASE/episode-requests/ereq_6c5ec646-5fc3-4529-898e-e3c6db646318" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/bb8f4285-d608-47ea-9ec2-717f52e89911.replay",
  "participants": [
    {
      "position": 0,
      "kind": "policy",
      "policy_version_id": "188b5f98-3b2f-4acf-9e00-22c38f331ec8",
      "policy_id": "410aaa51-658a-4365-81f8-b2fc0b814e4e",
      "policy_name": "poker-scholar",
      "version": 1,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": false,
      "is_seed": false
    },
    {
      "position": 1,
      "kind": "policy",
      "policy_version_id": "f3c265fe-cda2-4e27-8ab5-4362a21124e3",
      "policy_id": "ca5859b3-c053-42fe-8e7b-ab050d0a0656",
      "policy_name": "poker-exploiter",
      "version": 1,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
      "player_name": "daveey-1",
      "is_filler": false,
      "is_seed": false
    }
  ],
  "participant_scores": [
    {
      "position": 0,
      "score": 0.4995833333333333
    },
    {
      "position": 1,
      "score": 0.5004166666666666
    }
  ]
}
```

Status: **TRUE**. `status == "completed"`, `replay_url` non-null, and `participants` names
`daveey` (seat 0, version `188b5f98-…`) and `daveey-1` (seat 1, version `f3c265fe-…`) — both
`is_filler: false` and both matching STATE's champion uuids. No filler seats appear: this is the
`kuhn` rung, which is `seats: 2`, so the two champions fill the table and no `Baseline (N)` seat
is needed. `participant_scores` sum to 1.0 as the scoring rule requires.

---

## 4. Replay bytes are valid and show the game — **TRUE**

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/bb8f4285-d608-47ea-9ec2-717f52e89911.replay" \
     -o /tmp/ep.replay -w 'HTTP %{http_code}  bytes=%{size_download}\n'
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .results.reason' /tmp/ep.replay
```

```
HTTP 200  bytes=83303
strict UTF-8 JSON: ok
poker.replay.v1
complete
```

`protocol` matches the manifest — `coworld_manifest_template.json` declares
`poker.player.v1` / the replay envelope `poker.replay.v1`, and `design.md:534` fixes
`{"protocol": "poker.replay.v1", …}`. `results.reason` is `complete`, the norm — **not** a
`deadline` or `budget` early settle, so no design exception needs to be invoked.

This game's events key on `kind`, not `type` (a `select(.type=="decision")` filter returns 0 and
would be a false negative), and fallbacks are recorded per seat in `results`, not as an event
flag. Adapted commands:

```bash
jq -r '[.events[].kind]|group_by(.)|map("\(.[0])\t\(length)")|.[]' /tmp/ep.replay
```

```
action	141
ante	120
award	71
calib	2
deal	120
handEnd	60
handStart	60
matchEnd	1
reveal	98
say	122
```

```bash
jq -c '{decisions:.results.decisions,fallbacks:.results.fallbacks,forcedFolds:.results.forcedFolds,names:.results.names,net:.results.net,win:.results.win}' /tmp/ep.replay
jq -r '[.events[]|select(.kind=="action")]|group_by(.seat)|map("seat \(.[0].seat)\t\(length)")|.[]' /tmp/ep.replay
```

```
{"decisions":[66,75],"fallbacks":[0,0],"forcedFolds":[0,0],"names":["daveey","daveey-1"],"net":[-1,1],"win":[false,true]}
seat 0	66
seat 1	75
```

Status: **TRUE**. Strict `jq -e` parse succeeded (valid UTF-8 JSON, 83 303 bytes). 141 `action`
events split 66 / 75 across the two champion seats, exactly matching `results.decisions`.
**`fallbacks: [0, 0]` and `forcedFolds: [0, 0]` — zero of 141 decisions were scripted.** That is
not merely "a small minority", it is none: every decision on both champion seats came from the
model.

Non-trivial content, from the 122 `say` events:

```bash
jq -r '[.events[]|select(.kind=="say")|.text]|unique|length' /tmp/ep.replay
```

```
95
```

95 **distinct** lines across 122 utterances, and they are contextual rather than canned — e.g.
`"you're too predictable with that check"`, `"fair point, can't connect with that"`,
`"Caught me checking. Fair play."`, `"Can't let you get away with that - let's build the pot."`.
(Contrast the rounds-1/2 fallback replays, which cycled a fixed set of exactly **11** canned
baseline quips — see *Anomaly* below. The 11-vs-95 gap is itself the discriminator between a
scripted and a model-driven episode.)

---

## 5. Hosted game log is clean — **TRUE**

The logs body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it
was decoded with `ast.literal_eval` per repr before grepping (playbook §10 — line-based greps
undercount otherwise).

```bash
curl -sS "$BASE/episode-requests/ereq_6c5ec646-5fc3-4529-898e-e3c6db646318/artifacts/logs" \
  "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs3.raw          # headers: Authorization, User-Agent, X-Use-Elevated-Privileges
python3 …decode reprs… > /tmp/logs3.txt
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs3.txt || echo CLEAN
```

```
CLEAN
```

Per-pattern counts on the decoded text:

```
falling back                     0
LLM provider is unavailable      0
cut off at max_tokens            0
rejected                         0
```

Upstream call histogram from the decoded `bedrock-sidecar` container:

```bash
grep -oE 'POST https://[^ ]+ "HTTP/1\.1 [0-9]+' /tmp/logs3.txt \
 | sed -E 's#POST (https://[^/]+).* "HTTP/1\.1 ([0-9]+)#\1 -> \2#' | sort | uniq -c
```

```
    142 https://bedrock-runtime.us-east-1.amazonaws.com -> 200
```

Game container banner:

```
poker: seed not pinned; randomized
poker: variant=kuhn seats=2 stack=20 ante=1 blinds=0/0 hands=60 duplicate=true model=claude-sonnet-5
poker: serving on 0.0.0.0:8080
poker: player slot 0 connected (1/2)
poker: slot 0 delivered a prompt (474 chars)
poker: slot 0 delivered a prompt (474 chars)
poker: player slot 1 connected (2/2)
poker: slot 1 delivered a prompt (436 chars)
poker: slot 1 delivered a prompt (436 chars)
poker: starting with 2/2 players connected
poker llm: bedrock transport, url http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
poker: episode timeout 1200s; soft stop at 660s, hard stop at 672s
```

Status: **TRUE**. Zero matches for all four forbidden patterns. 142 Bedrock invocations, all
`200 OK`, zero throttles and zero retries. Both champion prompts were delivered (474 and 436
chars, each re-sent once as the protocol's registration-race guard prescribes). The episode
settled well inside its 660 s soft guard.

---

## 6. The public page uses the static replay path — **TRUE**

*Source used: **the SSR payload + the replay-session API**, not the raw-HTML grep.* The raw grep
found nothing, which the playbook says to treat as *unknown*, not as a failure:

```bash
curl -sS "https://softmax.com/poker" | grep -o '<iframe[^>]*src="[^"]*"'
```

```
(no match — HTTP 200, 611812 bytes; the page is client-rendered for the iframe, as the
 lighthouse run recorded platform-wide)
```

**Featured match**, server-rendered into the page's SSR payload at `state.playlist[0]`
(extracted from the same 611 812-byte fetch):

```json
{
  "episodeId": "453fe810-2b04-442a-a08f-82d90bc099ff",
  "coworldId": "cow_08add75e-311a-46ba-9b5d-05888954986e",
  "coworldName": "poker",
  "coworldVersion": "0.1.0",
  "replayUrl": "https://softmax-public.s3.amazonaws.com/replays/bb8f4285-d608-47ea-9ec2-717f52e89911.replay",
  "finishedAt": "2026-08-26T19:19:45.163535Z",
  "roundNumber": 3,
  "code": "poker.r3.e1",
  "outcome": "first"
}
matchup.first : daveey-1 poker-exploiter:v1 1043.747133633611
matchup.second: daveey poker-scholar:v1 956.2528663663891
```

A featured match **is present**, and it is round 3 — the very episode verified in checks 3–5
(`replayUrl` is byte-identical to check 3's `replay_url`). `playlist` length 1.

**Iframe `src`**, from the call the page's own JS makes:

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_08add75e-311a-46ba-9b5d-05888954986e","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/bb8f4285-d608-47ea-9ec2-717f52e89911.replay"}'
```

```
HTTP 200
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_08add75e-311a-46ba-9b5d-05888954986e/sha256%3A3f77538f7a2da1352ea60c620dcdcb626bd8de9a1b4e352d829db4e15eb9350e/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fbb8f4285-d608-47ea-9ec2-717f52e89911.replay&v=2","ready":true}
```

Status: **TRUE**. The path is
`/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` — the **static** route.
It is **not** a `/client/replay` pod URL. `ready: true` confirms static delivery and the path
ends `/index.html`. `<cow_id>` is `cow_08add75e-311a-46ba-9b5d-05888954986e` and `<sha>` decodes
to `sha256:3f77538f7a2da1352ea60c620dcdcb626bd8de9a1b4e352d829db4e15eb9350e`, which matches
`STATE.coworld.manifest_sha` exactly (the manifest hash, as the playbook specifies — not the
viewer-bundle digest).

---

## 7. Certification declared the static bundle — **TRUE**

*Source used: **the committed `runs/2026-08-26-poker/release-result.json`** (phase 40's artifact,
3 843 bytes, present in the run directory). No re-download from run `32999717629` was needed.*

```bash
jq -r '.certify.replay_liveness' runs/2026-08-26-poker/release-result.json
```

```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE**. The output contains the required
`Replay liveness: skipped (static replay bundle declared` prefix verbatim.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

*(a) Dispatch.* The iframe `src` from check 6 was rendered in headless chromium by CI. The run
was located by sorting on `createdAt`, not by taking "the latest run" blind.

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_08add75e-311a-46ba-9b5d-05888954986e/sha256%3A3f77538f7a2da1352ea60c620dcdcb626bd8de9a1b4e352d829db4e15eb9350e/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fbb8f4285-d608-47ea-9ec2-717f52e89911.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90   # dispatched 19:23:29Z
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:3][]|[.databaseId,.createdAt,.status]|@tsv'
```

```
33004894052	2026-08-26T19:23:30Z	in_progress
33003808546	2026-08-26T19:11:15Z	completed
32984003113	2026-08-26T15:04:46Z	queued
```

```bash
gh run watch 33004894052 -R Metta-AI/coworld-builder --exit-status   # exit 0
gh run view  33004894052 -R Metta-AI/coworld-builder --json status,conclusion
```

```json
{"conclusion":"success","status":"completed"}
```

```bash
gh run download 33004894052 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-26-poker/viewer-check
```

```
smoke-stderr.txt      0 bytes
smoke-stdout.txt    563 bytes
viewer-smoke.json  1459 bytes
viewer-smoke.png 732381 bytes
```

**Run id: `33004894052`** (dispatched by this verification run, 19:23:29Z). The artifact is
committed at `runs/2026-08-26-poker/viewer-check/`.

> An earlier run, `33003808546`, was dispatched at 19:11:14Z against the then-latest featured
> replay (round 2). Round 3 completed at 19:19:55Z and became the featured match, so that render
> was superseded and re-dispatched against the round-3 URL. Only `33004894052` is reported here;
> its `viewer-smoke.json` `.url` field confirms it rendered the round-3 replay
> `bb8f4285-d608-47ea-9ec2-717f52e89911`.

*(b) Readouts.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-26-poker/viewer-check/viewer-smoke.json
```

```json
{"loaded":true,"ms":7964,"clock":"HAND 1 / 60 · ROUND 1 · POT 0 · ANTE 1","scorebug":"daveey 0 NET 0 daveey-1 D 0 NET 0","feed_lines":735}
```

```bash
jq -c '.signals' runs/2026-08-26-poker/viewer-check/viewer-smoke.json
```

```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/2026-08-26-poker/viewer-check/viewer-smoke.json
```

```
no failure
```

**The three clock readouts:**

| scrub position | clock |
|---|---|
| 0 %   | `HAND 1 / 60 · ROUND 1 · POT 0 · ANTE 1` |
| 50 %  | `HAND 30 / 60 · MIRROR · SHOWDOWN · POT 4 · ANTE 1` |
| 100 % | `HAND 60 / 60 · MIRROR · ROUND 1 · POT 0 · ANTE 1` |

All three **differ**. Additional line from `smoke-stdout.txt`:

```
canvas text: 816 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
```

Status: **TRUE** — both conditions hold: `loaded: true` (via both `data-replay-loaded="true"` and
the `coworld-replay` bridge reaching `ready`, with `data_replay_error: null` and an empty
`bridge_error`), and the three clock readouts are distinct. First frame at 7 964 ms.

*(c) The replay JSON the viewer was asked to draw* — ordered excerpts from `/tmp/ep.replay`
(check 4), for reconciliation against the picture.

Early (`head -24`):

```
0	1	handStart	ante 1
0	1	deal	
0	0	deal	
0	1	ante	ante
0	0	ante	ante
0	1	say	Let's go.
0	1	action	check
0	0	say	checking it down
0	0	action	check
0	1	reveal	jack high
0	0	reveal	queen high
0	0	award	main
0	-1	handEnd	
1	0	handStart	ante 1
1	0	deal	
1	1	deal	
1	0	ante	ante
1	1	ante	ante
1	0	say	checking it down
1	0	action	check
1	1	say	you're too predictable with that check
1	1	action	bet
1	0	say	fair point, can't connect with that
1	0	action	fold
```

Middle (hand 30, the 50 % scrub point):

```
30	1	handStart	ante 1
30	1	deal	
30	0	deal	
30	1	ante	ante
30	0	ante	ante
30	1	say	Let's go.
30	1	action	bet
30	0	say	Price is right.
30	0	action	call
30	1	reveal	queen high
30	0	reveal	jack high
30	1	award	main
30	-1	handEnd	
```

Late (`tail -20`):

```
58	1	reveal	jack high
58	0	reveal	king high
58	0	award	main
58	-1	handEnd	
59	0	handStart	ante 1
59	0	deal	
59	1	deal	
59	0	ante	ante
59	1	ante	ante
59	0	action	check
59	1	say	King high, let's see what you've got.
59	1	action	bet
59	0	say	You got it this time
59	0	action	fold
59	1	award	returned
59	1	award	main
59	-1	handEnd	
59	0	calib	
59	1	calib	
59	-1	matchEnd	
```

```bash
jq -r '.results' /tmp/ep.replay
```

```json
{
  "names": ["daveey", "daveey-1"],
  "scores": [0.4995833333333333, 0.5004166666666666],
  "win": [false, true],
  "net": [-1, 1],
  "netPerHand": [-0.016666666666666666, 0.016666666666666666],
  "unitsPerHand": [-0.016666666666666666, 0.016666666666666666],
  "handsWon": [30, 30],
  "stackOffs": [0, 0],
  "exploitability": [0.2321428571428571, 0.23809523809523808],
  "exploitabilityCoverage": [0.9166666666666666, 0.9166666666666666],
  "exploitabilityFill": "nash",
  "audit": {"pairs": [], "flagged": [], "power": {"hands": 0, "contestedMin": 0, "contestedMedian": 0, "equitySamples": 2000}},
  "variant": "kuhn",
  "seats": 2,
  "handsPlayed": 60,
  "handsScored": 60,
  "hands": 60,
  "pairsComplete": 30,
  "unpairedHands": 0,
  "startingStack": 20,
  "ante": 1,
  "smallBlind": 0,
  "bigBlind": 0,
  "seed": 552822662,
  "seatOrder": [1, 0],
  "reason": "complete",
  "fallbacks": [0, 0],
  "forcedFolds": [0, 0],
  "decisions": [66, 75]
}
```

### Spectator-judgment paragraph

**The picture is legible and it shows the game.** `viewer-smoke.png` (captured at the 100 % scrub
position) is a dark slate arena with a green felt oval centred on it and two pixel-art robot cogs
seated across it — the blue cog labelled `daveey-1` at the top with stack `21`, the red cog
labelled `daveey` at the bottom with stack `19` and the dealer button `D` on its shoulder. Between
them, face-up on the felt, is the single revealed hole card of the last hand (`K♠`); on the 19:11
render of the round-2 replay the same slot showed both seats' cards with `JACK HIGH` / `QUEEN HIGH`
plates beneath them, so the showdown chrome demonstrably paints. This is unambiguously **cosino
lineage chrome**, not a rewrite sharing ids: the title bar reads `POKER` at left with the same
letterform treatment, a centred clock `HAND 60 / 60 · MIRROR · ROUND 1 · POT 0 · ANTE 1`, and at
right the `REPLAY` label, a `« LOG` toggle and an amber `KUHN` rung badge; immediately below it
sits the two-plate **scorebug** — `daveey  ⓪ −1  NET 0 ▪▪▪▪▪▪▪▪▪▪▪▪` against
`daveey-1  +1  NET 1 ▪▪▪▪▪▪▪▪▪▪▪▪` — with the per-seat momentum pip strips; and along the bottom
runs the familiar **transport strip**, a full-width scrubber whose amber tick-per-hand momentum
graph spans the episode, a play button at far left and the frame counter `794 / 795` at far right.
**A casual spectator can tell who is winning and why.** The scorebug states it in two numbers that
need no poker knowledge — `−1` versus `+1`, with the sign and colour carrying the verdict — and
those reconcile exactly with `results.net: [-1, 1]` and `win: [false, true]`, i.e. `daveey-1`
(`poker-exploiter:v1`) edged it by one chip, which is also why the leaderboard in check 2 has it at
rank 1. The *why* is legible from the 735-line feed and the revealed cards: hand 59 in the tail
excerpt above is the whole story in miniature — `daveey` checks, `daveey-1` says
*"King high, let's see what you've got."* and bets, `daveey` says *"You got it this time"* and
folds, and `daveey-1` takes the pot. **It advances**: the three clock readouts move from
`HAND 1 / 60 · ROUND 1` through `HAND 30 / 60 · MIRROR · SHOWDOWN · POT 4` to `HAND 60 / 60`, so the
scrubber genuinely drives the episode rather than parking on one frame, and the mid-point readout's
`POT 4 · SHOWDOWN` matches the recorded hand 30 (a bet, a call, a showdown at queen-high) — picture
and record agree. A `#scrub` element is present and functional, so no missing-scrubber caveat
applies. The only legibility observations worth passing to the coordinator, both minor and neither
blocking: the 100 % frame lands on a hand whose loser has already folded, so only one hole card is
on the felt and the endcard/summary is not what a spectator lands on at the end of the strip; and
the `MIRROR · ROUND 1` clock segment at 100 % is jargon a first-time viewer will not decode without
the rules page. Text rendering is clean — CI counted 816 canvas text draws with **0** outside the
canvas, **0** crossing an edge and **0** ellipsized.

---

## Anomaly — rounds 1 and 2 ran 100 % scripted (platform LLM routing), cleared by round 3

Not a check failure — checks 3–8 are evaluated against round 3, the latest completed round, which
is clean — but it must be on the record, and it is explicitly **not** the documented Bedrock
capacity exception.

Rounds 1 and 2 both settled `reason: "complete"` but with **every** decision a scripted fallback:

```bash
jq -c '{reason:.results.reason,decisions:.results.decisions,fallbacks:.results.fallbacks}' /tmp/ep1.replay   # round 1
{"protocol":"poker.replay.v1","reason":"complete","decisions":[71,72],"fallbacks":[71,72],"forcedFolds":[0,0]}
# round 2
{"decisions":[69,70],"fallbacks":[69,70],"forcedFolds":[0,0]}
```

Round 2's hosted log (`ereq_980db8b9-ae2f-435e-8bb9-9bb42e279da5`), decoded, was **not** clean:

```
falling back                     139
LLM provider is unavailable      274
cut off at max_tokens            0
rejected                         2
```

```
poker llm: seat 1 attempt 0 failed: anthropic error 503: {"message":"LLM provider is unavailable"}
poker llm: seat 1 attempt 1 failed: anthropic error 503: {"message":"LLM provider is unavailable"}
poker llm: seat 1 falling back to scripted decision
```

The cause is visible one container up. Round 2's `bedrock-sidecar` never reached Bedrock at all —
it made 274 calls to **openrouter.ai**, every one `402 Payment Required`:

```bash
grep -oE 'POST https://[^ ]+ "HTTP/1\.1 [0-9]+' /tmp/logs.txt \
 | sed -E 's#POST (https://[^/]+).* "HTTP/1\.1 ([0-9]+)#\1 -> \2#' | sort | uniq -c
```

```
    274 https://openrouter.ai -> 402
```

`402 Payment Required` is a **billing/credit** error, not a capacity or throttle error, so the
platform-wide-Bedrock-capacity exception does **not** cover it. Cross-check against two other
LLM coworlds confirms the platform's Bedrock path was healthy throughout, including a window
overlapping poker's round 2 (18:54–19:03Z):

| coworld | episode request | window | sidecar upstream |
|---|---|---|---|
| `chorus` | `ereq_0eefc077-4030-4ba4-b1ce-c004ba207de3` | 18:21–18:23Z | `24 × bedrock-runtime.us-east-1.amazonaws.com -> 200` |
| `knights-archers` | `ereq_4266d75a-9af5-413f-82d1-f624fa6caa4b` | 18:46Z | `24 × bedrock-runtime.us-east-1.amazonaws.com -> 200` |
| `poker` round 2 | `ereq_980db8b9-…` | 18:54–19:03Z | `274 × openrouter.ai -> 402` |
| **`poker` round 3** | `ereq_6c5ec646-…` | 19:09–19:19Z | `142 × bedrock-runtime.us-east-1.amazonaws.com -> 200` |

All three coworlds declare the identical manifest env
(`ANTHROPIC_API_KEY_URI: secret://coworld/<slug>/anthropic_api_key`) and all three sidecars start
with the identical config (`region us-east-1`, `has_role_arn: true`), so the divergence was not in
poker's manifest. It was transient platform-side provider routing, and it cleared on its own
between 19:03Z and 19:09Z: **round 3 made 142 Bedrock calls, all 200, with zero fallbacks.**

Two consequences worth noting for the coordinator, neither blocking:

1. The leaderboard's Elo (check 2) is computed over all three rounds, so rounds 1–2 contributed
   ratings earned by two *scripted baselines* playing each other rather than by the champions'
   prompts. The current 1043.7 / 956.3 spread is therefore partly noise. Round 3 is the only
   round so far that measured what the coworld is actually about.
2. The coworld's declared degrade path worked exactly as designed under a total LLM outage — the
   episodes still completed, still settled `reason: "complete"`, still produced valid replays and
   a chip-conserving `net` summing to zero, and the manifest's promise that "with no LLM
   credentials every seat plays scripted, so episodes always complete" was demonstrated in
   production. That is a positive result for the design, not a defect in it.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** (rounds 2, 3; 3 completed total, 0 failed) |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** (daveey-1 r1, daveey r2, both `rounds_played: 3`) |
| 3 | Latest round's episode request completed with replay | **TRUE** (`ereq_6c5ec646-…`, both champions seated) |
| 4 | Replay bytes valid, protocol match, shows the game | **TRUE** (`poker.replay.v1`, `complete`, 141 actions, 0 fallbacks) |
| 5 | Hosted game log clean | **TRUE** (`CLEAN`, 142 × Bedrock 200) |
| 6 | Public page: featured match + static iframe src | **TRUE** (SSR playlist + session API; static path, `ready: true`) |
| 7 | Certification declared the static bundle | **TRUE** (committed `release-result.json`) |
| 8 | Viewer executed and judged | **TRUE** (`loaded: true`, 3 differing clocks, run `33004894052`) |
