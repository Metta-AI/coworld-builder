# VERIFY — matrix-games   (2026-08-24T19:46:07Z)
Verdict: all-true (8 / 8)

Run: `2026-08-24-matrix-games` · slug `matrix-games` · coworld `cow_e8a973ea-c4f1-4c99-8a84-a776f1cde531` v`0.1.1`
League `league_2d6cdf8d-1f9d-4311-80ed-13616f5a8476` · division `div_3fc50172-46fb-44bf-994d-906fc48890c8`
75-minute wall-clock bound: opened 19:21:42Z, would expire 20:36:42Z — **not hit** (second post-filler
round completed at 19:38:34Z, 17 min in).

All headers are named, never their values:
`AUTH = -H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0"`,
`ELEV = -H "X-Use-Elevated-Privileges: true"`, `BASE=https://softmax.com/api/observatory/v2`.

### Deviations from `prompts/60-verify.md`'s literal jq, and why

Three, all recorded here as the prompt requires:

1. **`GET /rounds?league_id=…` returns a BARE ARRAY**, not `{entries:[…]}`. Every rounds query below
   uses `jq 'if type=="array" then . else .entries end'`. The prompt's `.entries[]` yields
   `null (null) has no keys` against this endpoint today.
2. **Check 4's event vocabulary.** This game's replay uses `k`, not `type`, for the event kind, and
   records fallback on the `order` event's `source` field (`"llm"|"retry"|"fallback"|"scripted"`),
   not as `fallback: true` (`design.md` §Event vocabulary, and §Degrade never hang: *"recorded on the
   `order` event as `"source":"fallback"`"*). The prompt's literal jq returns 0 for both counters on
   this file — proof pasted in check 4 — so the adapted forms
   `[.events[]|select(.k=="order")]` and `[.events[]|select(.k=="order" and .source=="fallback")]`
   are used and both forms are shown.
3. **Check 6's raw-HTML grep finds nothing** — `softmax.com/<slug>` is client-rendered for the iframe
   (`playbooks/observatory-api.md` §Featured match, "Answered (lighthouse run, 2026-08-22)"). The
   documented fallback is used and named in check 6.

---

## 1. ≥2 completed rounds after the fillers were set

```
GET $BASE/rounds?league_id=league_2d6cdf8d-1f9d-4311-80ed-13616f5a8476&limit=20   [AUTH]
```

Fetched fresh at 2026-08-24T19:42:50Z. HTTP 200. Response (bare array), all fields:

```json
[
  {
    "id": "round_0d15648c-0c6b-4cee-8a10-05a86a95cfc2",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-24T19:34:33.157442Z",
    "updated_at": null,
    "settled_at": null
  },
  {
    "id": "round_86e8a1ca-5add-4ea4-b18d-6d7a8d31890f",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-24T19:19:32.313552Z",
    "updated_at": null,
    "settled_at": null
  },
  {
    "id": "round_0492a802-76d0-4262-842a-6a775f31a428",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-24T19:19:01.833211Z",
    "updated_at": null,
    "settled_at": null
  }
]
```

```
$ jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
2
```

Failed round recorded verbatim as the prompt requires: **round 1**, `status: "failed"`,
`error: "Temporal RoundWorkflow failed before settling the round."`, created `19:19:01.833211Z`.
That is the documented pre-filler signature (`playbooks/observatory-api.md` §6: *"A `trigger-round`
issued before any filler exists fails instantly with `Temporal RoundWorkflow failed before settling
the round`"*). It does not count.

**Fillers were set between 19:19:01Z (round 1's creation) and 19:19:32Z (round 2's creation)**, and
the filler list is live now:

```
GET $BASE/leagues/$L/filler-policies   [AUTH + ELEV]   -> HTTP 200
```
```json
{
  "filler_policy_versions": [
    {"policy_version_id": "5939afa6-7331-456a-8934-753afeefc81d",
     "policy_name": "matrix-games-counter", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"},
    {"policy_version_id": "051a7a8d-15f9-416e-9107-f0910e7a951f",
     "policy_name": "matrix-games-tit-for-tat", "version": 2,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"}
  ]
}
```

The direct proof that rounds 2 and 3 are **after** the fillers is not the `entrant_attributions`
block (it lists only the two champion entrants in all three rounds) but the episodes those rounds
actually produced: both seated six filler seats with `"is_filler": true` and both replays name them
`Baseline (N)` — impossible before the filler list existed. That evidence is pasted in checks 3 and 4.

**Status: TRUE** — rounds **2** (`round_86e8a1ca-5add-4ea4-b18d-6d7a8d31890f`, created
2026-08-24T19:19:32.313552Z, its episode completed 2026-08-24T19:23:51.476226Z) and **3**
(`round_0d15648c-0c6b-4cee-8a10-05a86a95cfc2`, created 2026-08-24T19:34:33.157442Z, episode completed
2026-08-24T19:38:34.693670Z) are `completed`, and both are after the fillers were registered
(19:19:01–19:19:32Z). Round 1 is `failed` and excluded, its error quoted above.

---

## 2. Both champions ranked; fillers absent or Baseline

```
GET $BASE/divisions/div_3fc50172-46fb-44bf-994d-906fc48890c8/leaderboard   [AUTH]
```

Fetched fresh at 2026-08-24T19:42:52Z. HTTP 200. Bare list, verbatim:

```json
[
  {
    "rank": 1,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 1001.4695015289755,
    "score_label": "Elo",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 1.0,
    "episodes_played": null,
    "win_rate": 0.5,
    "policy_label": "matrix-games-brinkman:v2",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 998.5304984710245,
    "score_label": "Elo",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 1.0,
    "episodes_played": null,
    "win_rate": 0.5,
    "policy_label": "matrix-games-reader:v2",
    "recent_rounds": null
  }
]
```

As the prompt's tsv:

```
1	daveey-1	matrix-games-brinkman:v2	1001.4695015289755	2	1.0
2	daveey	matrix-games-reader:v2	998.5304984710245	2	1.0
```

(Note: an earlier poll at 19:22:23Z, after round 2 only, showed `daveey` rank 1 / 1016.0 and
`daveey-1` rank 2 / 984.0 with `rounds_played: 1` each — the table moved with round 3, which is
further evidence both rounds scored.)

**Status: TRUE** — both champions present: `daveey` with `matrix-games-reader:v2` and `daveey-1`
with `matrix-games-brinkman:v2`, each `rounds_played = 2` (≥ 1). Neither filler
(`matrix-games-counter:v1`, `matrix-games-tit-for-tat:v2`) appears as a row at all — the list has
exactly two entries — so the "fillers absent" branch is satisfied.

---

## 3. Latest round's episode request completed with a replay and the right participants

Latest completed round = round 3 = `round_0d15648c-0c6b-4cee-8a10-05a86a95cfc2` (from check 1).

```
GET $BASE/episode-requests?round_id=round_0d15648c-0c6b-4cee-8a10-05a86a95cfc2&limit=20   [AUTH]
```
```json
[{"id":"ereq_00d096dc-c968-46b8-a037-f0e2960a660d","status":"completed"}]
```

```
GET $BASE/episode-requests/ereq_00d096dc-c968-46b8-a037-f0e2960a660d   [AUTH]
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/29fb36db-2f98-4ba2-b7b8-71f7b4f092a6.replay",
  "created_at": "2026-08-24T19:34:33.592455Z",
  "completed_at": "2026-08-24T19:38:34.693670Z",
  "coworld_id": "cow_e8a973ea-c4f1-4c99-8a84-a776f1cde531",
  "coworld_name": "matrix-games",
  "coworld_version": "0.1.1",
  "variant_name": "running-with-scissors",
  "error": null
}
```

`participants` (`position  policy_name  version  player_name  is_filler`):

```
0	matrix-games-reader	2	daveey		false
1	matrix-games-brinkman	2	daveey-1	false
2	matrix-games-counter	1	daveey		true
3	matrix-games-tit-for-tat	2	daveey		true
4	matrix-games-tit-for-tat	2	daveey		true
5	matrix-games-counter	1	daveey		true
6	matrix-games-tit-for-tat	2	daveey		true
7	matrix-games-counter	1	daveey		true
```

Seat 0 carries `"policy_version_id": "f84fef5b-e6ff-4a62-81fa-9ddab07dc001"` and seat 1
`"policy_version_id": "a6584eb2-e9e0-44ae-ade8-050bbe0a4135"` — the two champion version ids from
STATE, exactly.

`participant_scores`:
```json
[{"position":0,"score":-0.75},{"position":1,"score":0.12},{"position":2,"score":0.42},
 {"position":3,"score":1.0},{"position":4,"score":0.03},{"position":5,"score":0.07},
 {"position":6,"score":-0.58},{"position":7,"score":-0.31}]
```

For completeness, the **other** completed round (round 2) also produced one completed episode request
with a replay — `ereq_42283e7d-b9e0-4053-83b3-e04a852cd8a9`, `status: "completed"`,
`replay_url: https://softmax-public.s3.amazonaws.com/replays/6f63050e-3025-452e-a263-e905883bad18.replay`,
same eight seats, champions at positions 0 and 1, six `is_filler: true` seats, scores summing to
0.00 (zero-sum, as running-with-scissors requires).

**Status: TRUE** — `status == "completed"`, `replay_url` non-null and on
`softmax-public.s3.amazonaws.com`, eight participants with `daveey` (`matrix-games-reader:v2`) and
`daveey-1` (`matrix-games-brinkman:v2`) both seated and both `is_filler: false`, and the remaining
six seats flagged `is_filler: true`.

---

## 4. Replay bytes are valid and show the game

```
$ curl -sSL "https://softmax-public.s3.amazonaws.com/replays/29fb36db-2f98-4ba2-b7b8-71f7b4f092a6.replay" -o /tmp/ep.replay
http=200 bytes=264160

$ jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok

$ python3 -c "d=open('/tmp/ep.replay','rb').read(); d.decode('utf-8'); print('python strict utf-8 decode: ok, bytes=',len(d))"
python strict utf-8 decode: ok, bytes= 264160

$ jq -r '.protocol, .variant, .results.reason, .results.ending' /tmp/ep.replay
matrix.replay.v1
running-with-scissors
complete
full_match
```

**Protocol match.** `matrix.replay.v1` is the value pinned in `design.md` §The replay file
(`"protocol":"matrix.replay.v1"`) and asserted in the repo's own tests. The coworld manifest declares
two *wire* protocols only — `game.protocols.player` = `matrix.player.v1` and `game.protocols.global`
= `matrix.global.v1` (verified against
`repos/Metta-AI/cogame-matrix-games/contents/coworld_manifest_template.json`, which contains
`matrix.player.v1` ×2 and `matrix.global.v1` ×2 and no `matrix.replay.v1` string) — so the replay
protocol string is pinned in the design note and in code rather than in the manifest body. Its source
of truth, fetched fresh from the repo:

```
$ gh api repos/Metta-AI/cogame-matrix-games/contents/src/matrix_games/replays.nim | base64 -d | grep -n 'matrix.replay.v1'
2:## `matrix.replay.v1`.

$ gh api repos/Metta-AI/cogame-matrix-games/contents/tests/test_replay.nim | base64 -d | sed -n '20,24p'
  test "the bytes are strict UTF-8 and parse as matrix.replay.v1":
    check validateUtf8(bytes) == -1
    let replay = parseReplayBytes(bytes)
    check replay{"protocol"}.getStr() == ReplayProtocol
    check replay{"game"}.getStr() == "matrix-games"
```

The fetched bytes' `protocol` equals that pinned value. Naming family (`matrix.*.v1`) matches the
manifest's two declared protocols.

**`results.reason == "complete"`** — the strong branch, not the `deadline` exception the design note
would have permitted (`design.md` §End conditions: *"`deadline` is declared acceptable … but the
arithmetic in `## Decisions` is sized so it should not fire"*). It did not fire.

**Fallback accounting — the prompt's literal jq first, then the adapted form.**

```
$ jq -r '[.events[]|select(.type=="decision")]|length' /tmp/ep.replay
0
$ jq -r '[.events[]|select(.fallback==true)]|length' /tmp/ep.replay
0
```
Those are both 0 because this game's vocabulary is `k` / `source`, not `type` / `fallback` (see
Deviations, above, and `design.md` §Event vocabulary). Adapted:

```
$ jq -r '[.events[]|select(.k=="order")]|length' /tmp/ep.replay
96
$ jq -r '[.events[]|select(.k=="order" and .source=="fallback")]|length' /tmp/ep.replay
0
$ jq -r '[.events[]|select(.k=="order" and .source=="retry")]|length' /tmp/ep.replay
0
```

96 = 12 beats × 8 seats, exactly the cadence `design.md` §Cadence budgets. Per seat:

```
$ jq -r '[.events[]|select(.k=="order")]|group_by(.seat)|map("seat \(.[0].seat): "+(map(.source)|group_by(.)|map("\(.[0])=\(length)")|join(" ")))|.[]'
seat 0: llm=12
seat 1: llm=12
seat 2: scripted=12
seat 3: scripted=12
seat 4: scripted=12
seat 5: scripted=12
seat 6: scripted=12
seat 7: scripted=12
```

Seats 0 and 1 are the champions. **Every one of their 24 decisions has `source: "llm"`** — zero
`retry`, zero `fallback`, zero `scripted`. Seats 2–7 are the scripted fillers and are `scripted` by
construction, not by degradation. Fallback rate on champion seats: **0 / 24 = 0 %**, which is well
inside "a small minority".

Champion decisions are non-trivial, not boilerplate (first eight, `beat seat intent token target
source latencyMs say`):

```
0	0	gather	2	-1	llm	4829	Building toward counter-play
0	1	gather	1	-1	llm	4829	Building paper commitment
1	0	gather	2	-1	llm	18437	Building scissors base in zone
1	1	gather	1	-1	llm	18437	Committing to paper dominance; paper beats rock.
2	0	gather	2	-1	llm	17365	Scissors zone rich, loaded to 80%. Elm beating Gorse on rock su…
2	1	gather	1	-1	llm	17365	Commit to paper dominance
3	0	gather	2	-1	llm	16381	Stacking scissors to beat Dune's rock.
3	1	gather	1	-1	llm	16381	Locking paper advantage in zone
```

Those are game-specific reads — token indices 1 (`paper`) and 2 (`scissors`) named against the RPS
cycle, opponents named by alias — not a generic default.

The file is a real episode of the game it claims to be:

```
$ jq -c '{frames:(.frames|length), share:(.series.share|length), score:(.series.score|length), spawners:(.spawners|length), indices:.indices}' /tmp/ep.replay
{"frames":600,"share":600,"score":600,"spawners":60,
 "indices":{"conventionCounts":[[18,1,1],[2,1,5],[0,1,0]],"coopRate":null,
            "exploitabilityCp":[22,55,17,9,101,50,151,43]}}

$ jq -r '[.events[]|select(.k=="interact")]|length' /tmp/ep.replay
29
```

600 frames = 12 beats × 50 ticks; 60 spawners = the K=3 layout; `conventionCounts` sums to 29 = the
interact count; `coopRate: null` is correct for a variant with no `coopToken`.

**Status: TRUE** — 264 160 bytes, valid strict-UTF-8 JSON under both `jq -e` and python's strict
codec; `protocol == "matrix.replay.v1"` matching the pinned value; `results.reason == "complete"`
(no exception needed); champion seats 0 and 1 made 24/24 LLM decisions with **zero** fallbacks and
non-trivial, game-specific content.

---

## 5. Hosted game log is clean

```
GET $BASE/episode-requests/ereq_00d096dc-c968-46b8-a037-f0e2960a660d/artifacts/logs   [AUTH + ELEV]
-> HTTP 200, 52691 bytes
```

The body is python `b'…'` byte-string reprs under `===== container: <name> =====` headers, so it was
**decoded with `ast.literal_eval` per repr before grepping** (`playbooks/observatory-api.md` §10 —
line-based greps on the raw body badly undercount). Decoded: 52 536 chars, 155 lines, containers
`coworld-init-config`, `bedrock-sidecar`, `game`, `worker`.

```
$ grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs-decoded.txt || echo CLEAN
CLEAN
```

Zero matches for all four patterns. No documented exception is being invoked — there is nothing to
except.

Positive evidence from the same decoded log that the LLM path really ran (lines 107–150):

```
matrix-games: seed not pinned; randomized to 1543983161
matrix-games: seats=8 matrix=running-with-scissors beats=12 ticksPerBeat=50 model=claude-haiku-4-5
matrix-games: slot 0 registered (801 prompt chars, llm)
matrix-games: slot 1 registered (637 prompt chars, llm)
matrix-games: slot 2 registered (0 prompt chars, scripted counter)
matrix-games: slot 3 registered (0 prompt chars, scripted tit-for-tat)
matrix-games: starting with 8/8 players connected
matrix-games llm: bedrock transport, url http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
matrix-games: beat 0 done, tick 50, 0 resolutions, 12s elapsed
…
matrix-games: beat 11 done, tick 600, 29 resolutions, 201s elapsed
matrix-games: writing replay (264160 bytes) and results
matrix-games: running-with-scissors 12 beats, 600 ticks, 29 resolutions, complete/full_match
matrix-games: holding /healthz and /global for 20s
```

Both champion seats registered with real prompts (801 and 637 chars) and the Bedrock sidecar
transport was selected — not the credential-less path that silently plays scripted. 201 s of play
against a 720 s deadline, comfortably inside the design's 480 s worst case.

The round-2 episode's log (`ereq_42283e7d-b9e0-4053-83b3-e04a852cd8a9`, 52 695 bytes) was decoded and
grepped the same way and is also **CLEAN**.

**Status: TRUE** — CLEAN, zero matches, on the latest round's episode (and on the previous one).

---

## 6. The public page uses the static replay path

**(a) The prompt's first source — raw-HTML grep — found nothing.** Recorded as *unknown*, not as a
failure, per the prompt and `playbooks/observatory-api.md` §Featured match:

```
$ curl -sS "https://softmax.com/matrix-games" -o page.html   # http=200 bytes=510860
$ grep -o '<iframe[^>]*src="[^"]*"' page.html
(no match — page is client-rendered)
```

**(b) The prompt's second source — `GET $BASE/coworlds?limit=200` — is also not evidence here**, and
this is the documented platform-wide behaviour, pasted so it is not mistaken for a defect:

```
$ curl -sS "$BASE/coworlds?limit=200" [AUTH] | jq -r '…|select(.name=="matrix-games")|{id,canonical,replay_viewer,featured_match}'
{
  "id": "cow_e8a973ea-c4f1-4c99-8a84-a776f1cde531",
  "name": "matrix-games",
  "version": "0.1.1",
  "canonical": true,
  "replay_viewer": null,
  "featured_match": null
}
```

`featured_match: null` platform-wide — playbook §Featured match, "Answered (lighthouse run,
2026-08-22)". `canonical: true` confirms the coworld is the published one.

**(c) The source actually used: the page's own SSR payload plus the call the page's own JS makes.**

*Featured match, from the page's SSR payload at `state.playlist[0]`* (fetched fresh 19:43:20Z,
backslash-unescaped for readability):

```json
"playlist":[{"episodeId":"1d346fbe-3043-4702-8bbc-4d170a477408",
 "coworldId":"cow_e8a973ea-c4f1-4c99-8a84-a776f1cde531",
 "coworldName":"matrix-games","coworldVersion":"0.1.1",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/29fb36db-2f98-4ba2-b7b8-71f7b4f092a6.replay",
 "finishedAt":"2026-08-24T19:38:34.693670Z","roundNumber":3,"episodeNumber":1,
 "code":"matrix-games.r3.e1",
 "matchup":{"divisionId":"div_3fc50172-46fb-44bf-994d-906fc48890c8","divisionName":"Competition",
  "first":{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
           "score":1001.4695015289755,"score_label":"Elo","rounds_played":2,"episode_wins":1,
           "win_rate":0.5,"policy_label":"matrix-games-brinkman:v2"},
  "second":{"rank":2,"player_id":"ply_bac48e…
```

A featured match **is** present, it is round 3 episode 1 — the same episode as checks 3, 4 and 5 —
and its `replayUrl` is byte-identical to the `replay_url` in check 3.
(The same field was fetched twice earlier this run: at 19:22Z, before any round had completed, it
was `"playlist":[]`; at 19:33Z, after round 2 only, it carried
`"code":"matrix-games.r2.e1"` with round 2's replay URL. It tracks the ladder and is live.)

*The iframe `src`, from the call the page's JS makes:*

```
POST $BASE/coworlds/replays/session   [AUTH]
content-type: application/json
{"coworld_id":"cow_e8a973ea-c4f1-4c99-8a84-a776f1cde531",
 "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/29fb36db-2f98-4ba2-b7b8-71f7b4f092a6.replay"}
-> HTTP 200
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e8a973ea-c4f1-4c99-8a84-a776f1cde531/sha256%3A344375ca76bdfcc1a6f59ca91d552d6ec5ab24a1b94dc0f60b5f42c80d181636/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F29fb36db-2f98-4ba2-b7b8-71f7b4f092a6.replay&v=2",
  "ready": true
}
```

Path decomposition against the required shape
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`:

| element | value | matches |
|---|---|---|
| route | `/v2/coworlds/replays/**static**/` | yes — **not** `/client/replay` |
| `<cow_id>` | `cow_e8a973ea-c4f1-4c99-8a84-a776f1cde531` | = STATE `coworld.cow_id` |
| `<sha>` | `sha256%3A344375ca76bdfcc1a6f59ca91d552d6ec5ab24a1b94dc0f60b5f42c80d181636` | = STATE `coworld.manifest_sha` (URL-encoded `:`) |
| leaf | `index.html` | yes |
| `?replay=` | the round-3 S3 `.replay` URL, percent-encoded | yes |
| `ready` | `true` | static delivery |

The string `/client/replay` does not appear anywhere in the returned URL.

**Status: TRUE** — source used: the page's SSR `state.playlist[0]` for the featured match (the raw
iframe grep found nothing because the page is client-rendered; `/coworlds`' `featured_match` is null
platform-wide) and `POST /coworlds/replays/session` for the iframe `src`. A featured match is
present (round 3 episode 1) and the `src` is the **static** route with `ready: true`.
→ STATE `verify.iframe_static = true`.

---

## 7. Certification declared the static bundle

Source read: **`runs/2026-08-24-matrix-games/release-result.json`, the copy phase 40 committed**
(3 977 bytes, mtime 2026-08-24 19:15). It was present, so the `gh run download` fallback from
release run `32766185820` was **not** needed and was not used. `/tmp` was not consulted.

```
$ jq -r '.certify.replay_liveness' runs/2026-08-24-matrix-games/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Contains the required substring `Replay liveness: skipped (static replay bundle declared`.

**Status: TRUE** — read from the committed `runs/2026-08-24-matrix-games/release-result.json` (not
re-downloaded).

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged

**(a) Dispatch.** The URL is the full iframe `src` from check 6, `?replay=` and `&v=2` included.

```
$ date -u +%FT%TZ
2026-08-24T19:43:51Z
$ gh workflow run viewer-check.yml -R Metta-AI/coworld-builder \
    -f url="https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e8a973ea-c4f1-4c99-8a84-a776f1cde531/sha256%3A344375ca76bdfcc1a6f59ca91d552d6ec5ab24a1b94dc0f60b5f42c80d181636/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F29fb36db-2f98-4ba2-b7b8-71f7b4f092a6.replay&v=2" \
    -f timeout=90
```

Find-the-new-run (sorted by `createdAt`, never "the latest" blind):

```
$ gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status,conclusion -L 10 | jq -c 'sort_by(.createdAt)|reverse|.[0:3][]'
{"conclusion":"","createdAt":"2026-08-24T19:43:53Z","databaseId":32769835228,"status":"in_progress"}
{"conclusion":"success","createdAt":"2026-08-24T17:01:34Z","databaseId":32754228468,"status":"completed"}
{"conclusion":"success","createdAt":"2026-08-24T14:40:57Z","databaseId":32740208697,"status":"completed"}
```

`createdAt 19:43:53Z` is after the dispatch at `19:43:51Z`; the next-newest run is from 17:01:34Z, so
there is no ambiguity. **Run id `32769835228`.**

```
$ gh run watch 32769835228 -R Metta-AI/coworld-builder --exit-status
✓ viewer-check in 33s (ID 97567471969)
  ✓ Load the viewer
  ✓ Fail if the viewer did not load
$ gh run view 32769835228 -R Metta-AI/coworld-builder --json conclusion,status
{"conclusion":"success","status":"completed"}

$ gh run download 32769835228 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-24-matrix-games/viewer-check
$ ls -la runs/2026-08-24-matrix-games/viewer-check/
-rw-r--r--  1 root root      0 smoke-stderr.txt
-rw-r--r--  1 root root    647 smoke-stdout.txt
-rw-r--r--  1 root root   1522 viewer-smoke.json
-rw-r--r--  1 root root 620399 viewer-smoke.png
```

The directory is written to `runs/2026-08-24-matrix-games/viewer-check/` for the coordinator to
commit alongside this file.

**(b) The readouts, verbatim from the downloaded artifact.**

```
$ jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-24-matrix-games/viewer-check/viewer-smoke.json
{"loaded":true,"ms":2430,"clock":"BEAT 1 / 12 TICK 1 OF 600","scorebug":"daveey 0.00 0 enc daveey-1 0.00 0 enc Baseline 0.00 0 enc Baseline (2) 0.00 0 enc BEAT 1 / 12 TICK 1 OF 600 Baseline (3) 0.00 0 enc Baseline (4) 0.00 0 enc Baseline (5) 0.00 0 enc Baseline (6) 0.00 0 enc","feed_lines":6}

$ jq -c '.signals' …/viewer-smoke.json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}

$ jq -r '.failure // "no failure"' …/viewer-smoke.json
no failure

$ jq -c '.canvas_text' …/viewer-smoke.json
{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}

$ jq -r '.console_tail[]' …/viewer-smoke.json
[bridge] loading
[bridge] ready
```

The three clock readouts:

| scrub position | `#clock` readout |
|---|---|
| 0 % | `BEAT 1 / 12 TICK 1 OF 600` |
| 50 % | `BEAT 7 / 12 TICK 317 OF 600` |
| 100 % | `BEAT 12 / 12 TICK 599 OF 600` |

All three **differ**. A `#scrub` element exists and responds (the json carries a real `scrub` array,
not the `"(no #scrub…)"` sentinel), so the missing-scrubber branch does not apply.

**Item 8 gate:** `loaded: true` ✓ (backed by `data-replay-loaded="true"` **and** the
`coworld-replay` bridge reaching `ready`, with `data-replay-error: null` and no `bridge_error`), and
the three clock readouts differ ✓. First drawn frame at **2 430 ms**.

**(c) The replay JSON the viewer was asked to draw** — ordered excerpts from `/tmp/ep.replay`
(check 4), so the picture and the record can be reconciled.

*Early (first 20 events; `t  seat  k  say/intent/reason`):*
```
0	0	order	Building toward counter-play
0	1	order	Building paper commitment
0	2	order	reading the room
0	3	order	mirroring what you showed me
0	4	order	mirroring what you showed me
0	5	order	reading the room
0	6	order	mirroring what you showed me
0	7	order	reading the room
3	2	pickup
3	3	pickup
3	4	pickup
6	1	pickup
6	2	pickup
6	4	pickup
9	1	pickup
9	3	pickup
9	5	pickup
12	2	pickup
12	5	pickup
15	1	pickup
```

*Middle (resolutions 11–16, the payoff matrix actually biting):*
```
t=265 beat=5 row=5 col=2 cell=[1,2] rowMix=[117,470,411] colMix=[250,250,500] rowCp=-26 colCp=26
t=277 beat=5 row=7 col=2 cell=[0,0] rowMix=[333,333,333] colMix=[333,333,333] rowCp=0   colCp=0
t=280 beat=5 row=6 col=4 cell=[0,0] rowMix=[727,181,90]  colMix=[777,111,111] rowCp=18  colCp=-18
t=360 beat=7 row=2 col=0 cell=[0,0] rowMix=[666,250,83]  colMix=[444,111,444] rowCp=58  colCp=-58
t=369 beat=7 row=4 col=6 cell=[0,2] rowMix=[727,181,90]  colMix=[333,111,555] rowCp=78  colCp=-78
t=385 beat=7 row=2 col=0 cell=[0,0] rowMix=[333,333,333] colMix=[500,166,333] rowCp=0   colCp=0
```

*Late (last 12 events):*
```
579	1	interact
579	1	reset
579	2	reset
583	4	pickup
592	4	pickup
592	5	pickup
594	2	pickup
595	4	pickup
597	2	pickup
598	3	pickup
600	-	beatclose
600	-	end	complete
```

*Results:*
```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)","Baseline (5)","Baseline (6)"],
 "scores":[-0.75,0.12,0.42,1.0,0.03,0.07,-0.58,-0.31],
 "win":[false,false,false,true,false,false,false,false],
 "aliases":["Ash","Birch","Cedar","Dune","Elm","Fern","Gorse","Holly"],
 "camps":["none","none","none","none","none","none","none","none"],
 "variant":"running-with-scissors","interactions":29,
 "perSeatInteractions":[6,6,11,7,10,6,9,3],
 "meanPayoff":[-0.125,0.02,0.0381818…,0.1428571…,0.003,0.0116666…,-0.0644444…,-0.1033333…],
 "exploitability":[0.22,0.55,0.17,0.09,1.01,0.5,1.51,0.43],
 "coopRate":null,"conventionCounts":[[18,1,1],[2,1,5],[0,1,0]],
 "tokens":["rock","paper","scissors"],"beats":12,"ticks":600,
 "reason":"complete","ending":"full_match"}
```

### Spectator judgment

**It is legible, and it shows the game.** `viewer-smoke.png` (1280 × 800, taken after the 100 %
scrub, so the endcard is up) is a full broadcast frame, not a blank shell and not a loading spinner.
Describing only what is in the downloaded image:

Across the top is the **scorebug**: eight slim plates, four in `#plates-l` and four in `#plates-r`,
each a livery chip, the **policy** name, a two-decimal score and an encounter count — `daveey −0.75
6 enc`, `daveey-1 0.12 6 enc`, `Baseline 0.42 11 enc`, `Baseline (2) 1.00 7 enc` on the left;
`Baseline (3) 0.03 10 enc`, `Baseline (4) 0.07 6 enc`, `Baseline (5) −0.58 9 enc`, `Baseline (6)
−0.31 3 enc` on the right. The winning plate, `Baseline (2)`, is highlighted with a warm bar. Those
eight numbers are exactly `results.scores` and `results.perSeatInteractions` above, in slot order,
and the two name spaces hold: the plates show policy names while the replay's in-game `names[]` are
the aliases `Ash … Holly`. Between the plate banks is the **clock**, `BEAT 12 / 12` over the caption
`TICK 599 OF 600` — spelled out, as the design pins, never `B12`.

Directly under the scorebug band is `#mg-indices`: `ENCOUNTERS 29 · COOP — · TOP CELL rock/rock ×18`
— reconciling exactly with `results.interactions = 29`, `coopRate: null` (rendered as the em dash,
correct for a variant with no `coopToken`) and `conventionCounts[0][0] = 18`. At the left edge is
`#mg-matrix`, the 3×3 payoff panel, axes labelled `rock / paper / scissors` on both sides and every
cell printing its pair (`0 / 0`, `−3 / 3`, `3 / −3` …) — the zero-sum RPS matrix from the design
table, drawn. At the right edge is `#mg-legend`, the token colour key (`rock` red, `paper` blue,
`scissors` green). Down the right side the **feed** shows six plain-language rows — `DUNE picks up
scissors`, `GORSE picks up rock`, `FERN picks up paper`, `GORSE picks up rock`, `CEDAR picks up
rock`, `DUNE picks up rock` (six rows, matching `feed_lines: 6`) — consistent with the tail of the
event list above, which at ticks 583–598 is a run of pickups by seats 2, 3, 4 and 5. The board
itself is visible behind the endcard's scrim: the walled yard, the wall-tile blocks, coloured token
gems on their spawners, and cog sprites.

The **endcard** is the starter's, filled with this game's story: headline `BASELINE (2) TAKES THE
YARD`, the wincond strip `RUNNING-WITH-SCISSORS · 12 BEATS · 29 ENCOUNTERS`, a "how" line `coop — ·
tokens rock / paper / scissors · complete`, an eight-row table (`policy score enc mean exploit`)
sorted by score — `Baseline (2) 1.00 7 0.14 0.09` down to `daveey −0.75 6 −0.13 0.22` — and the
final convention grid `rock / paper / scissors — [[18,1,1],[2,1,5],[0,1,0]]`. Every one of those
numbers is `results` verbatim; `Baseline (2)` is the seat with `win: true` at index 3.

Along the bottom is the **transport strip**: loop, step-back, pause, +5 s, step-forward, reload,
fast-forward, a lit `spoilers` chip, the leader readout `BASELINE (2)  599 / 600`, and the speed
chips `1× 2× 3× 4× 8× 16×` with `1×` selected. Beneath it the **scrubber** carries regularly spaced
beat ticks plus taller coloured markers at a few positions (blue early, mid and late; a yellow one
at the far right where the playhead sits), a played-region fill, and a grey lull span in the
right-of-centre stretch; under that, the `#momentum` strip re-lettered `CONVENTION` draws three
coloured curves — the rock, paper and scissors shares over all 600 ticks — the `series.share` time
series, full width.

**Does it advance?** Yes, and this is proven rather than inferred: the three scrub readouts move
from `BEAT 1 / 12 TICK 1 OF 600` to `BEAT 7 / 12 TICK 317 OF 600` to `BEAT 12 / 12 TICK 599 OF 600`.
The picture is not empty, not frozen, not unreadable.

**Does it look like the starter's chrome?** Yes — this is paintbot/coworld-ctf lineage, not a
rewrite that shares ids (the cogame-gridlock failure). The frame carries the starter's transport
band with the same button set and speed chips, the same scrubber-with-momentum-graph pairing under
it, the same two-bank scorebug with a centred clock and caption, the same endcard geometry
(`#ec-headline` / `#ec-wincond` / `#ec-how` / `#ec-teams`, bounded above the transport band) and the
same warm-dark palette and letterboxed `#stage`. The three additions the design declared —
`#mg-matrix` at the left edge, `#mg-indices` under the scorebug band, `#mg-legend` at the right edge
— are all inside `#chrome` and none of them sits over the transport band, exactly as
`design.md` §Transport rules requires. The `#viewpanel` zoom bar and minimap are absent, which is the
design's declared removal for a fixed 24 × 14 board, not a missing feature.

**Legibility observations for the coordinator** (none blocking, none affecting the verdict):
- `canvas_text.total = 0` — this viewer draws all of its text in DOM chrome, none on the canvas, so
  the strict-text-bounds check is trivially clean but also carries no signal here.
- The screenshot is taken at the 100 % scrub position, so the endcard scrim dims the board and the
  `#mg-matrix` panel behind it. That is the starter's endcard behaviour (dismissed by any seek), not
  a defect, but it means this particular frame shows the endcard rather than live play. Motion is
  established by the three differing clock readouts, not by this single frame.

**Status: TRUE** — `loaded: true` (`data-replay-loaded="true"`, bridge `ready`, no error) **and**
three differing clock readouts, from `viewer-check.yml` run **32769835228** dispatched at
2026-08-24T19:43:51Z this run; artifact downloaded to
`runs/2026-08-24-matrix-games/viewer-check/`.

---

## STATE values for the coordinator to write

```json
"verify": {
  "rounds": [
    {"id": "round_86e8a1ca-5add-4ea4-b18d-6d7a8d31890f", "round_number": 2, "status": "completed"},
    {"id": "round_0d15648c-0c6b-4cee-8a10-05a86a95cfc2", "round_number": 3, "status": "completed"}
  ],
  "replay": "https://softmax-public.s3.amazonaws.com/replays/29fb36db-2f98-4ba2-b7b8-71f7b4f092a6.replay",
  "iframe_static": true,
  "viewer_check_run": 32769835228
}
```

Also worth carrying forward for phase 70/80:
- latest episode request: `ereq_00d096dc-c968-46b8-a037-f0e2960a660d` (round 3, completed 19:38:34Z)
- iframe src: `https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e8a973ea-c4f1-4c99-8a84-a776f1cde531/sha256%3A344375ca76bdfcc1a6f59ca91d552d6ec5ab24a1b94dc0f60b5f42c80d181636/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F29fb36db-2f98-4ba2-b7b8-71f7b4f092a6.replay&v=2`
- leaderboard rows: `1 daveey-1 matrix-games-brinkman:v2 1001.47 (2 rounds, 1 win)` /
  `2 daveey matrix-games-reader:v2 998.53 (2 rounds, 1 win)`

## Checklist summary

| # | check | verdict |
|---|---|---|
| 1 | ≥2 completed post-filler rounds | **TRUE** (rounds 2, 3; round 1 failed pre-fillers, error quoted) |
| 2 | both champions ranked, fillers absent/Baseline | **TRUE** (daveey, daveey-1, 2 rounds each; no filler rows) |
| 3 | latest round's episode request completed with replay + participants | **TRUE** |
| 4 | replay bytes valid, protocol match, reason, champion decisions non-fallback | **TRUE** (`complete`, 24/24 LLM, 0 fallbacks) |
| 5 | hosted game log clean | **TRUE** (CLEAN, decoded before grep) |
| 6 | public page featured match + **static** iframe src | **TRUE** (`ready: true`, static route, no `/client/replay`) |
| 7 | certification declared the static bundle | **TRUE** (committed `release-result.json`) |
| 8 | viewer executed: `loaded: true` + three differing clocks | **TRUE** (run 32769835228) |

75-minute bound: **not hit**.
