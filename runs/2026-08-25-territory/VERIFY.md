# VERIFY — territory   (2026-08-25T13:22Z)

Verdict: **all-true** (8/8)

Run `2026-08-25-territory` · coworld `cow_e7cac219-31d0-45c5-93f8-649434351365` v0.1.1 ·
league `league_dcc3daee-8099-4fd1-b321-da10e1be9a64` · division `div_350c663f-0e3d-42e5-9346-2be631892c17`.

Every fetch below was made in this heartbeat, between 13:17:23Z and 13:21:28Z UTC, except the two
documented exceptions: **check 7** (the committed `runs/2026-08-25-territory/release-result.json`,
phase 40's artifact) and **check 8** (the artifact of `viewer-check.yml` run `32852582973`, which
*this* verifier dispatched at 13:18:53Z). Headers used are named, never their values:
`Authorization: Bearer $SOFTMAX_TOKEN`, `User-Agent: coworld-builder/1.0`, and where noted
`X-Use-Elevated-Privileges: true`.

```bash
BASE=https://softmax.com/api/observatory/v2
L=league_dcc3daee-8099-4fd1-b321-da10e1be9a64
D=div_350c663f-0e3d-42e5-9346-2be631892c17
COW=cow_e7cac219-31d0-45c5-93f8-649434351365
```

## Clock discrepancy — read the timestamps in this file, not in log.md

`runs/2026-08-25-territory/log.md`'s stamps run **~67 minutes ahead of real UTC**. Two independent
sources agree on real time: `curl -sSI https://softmax.com/` returned
`date: Tue, 25 Aug 2026 12:55:11 GMT` while the sandbox `date -u` returned `2026-08-25T12:55:11Z`,
and the Observatory's own `created_at` for the round the log stamps `13:59:30Z` is `12:52:00.927088Z`.
Every timestamp in *this* file is real UTC taken from the API or the verified sandbox clock. This is
a logging observation for the coordinator, not a verification failure — no check depends on it.

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

```
GET $BASE/rounds?league_id=$L&limit=20          (13:17:23Z)
```
```json
[
  {
    "id": "round_7a7a2fe9-1f42-4efc-a975-ce761c97c340",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-25T13:07:46.614776Z",
    "completed_at": "2026-08-25T13:15:06.252473Z"
  },
  {
    "id": "round_e6aa04b8-ec0e-4c5f-b2e7-3df003a88011",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-25T12:52:46.245172Z",
    "completed_at": "2026-08-25T13:00:05.249892Z"
  },
  {
    "id": "round_c56d37ac-626e-402a-8006-ecde227bfb00",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-25T12:52:00.927088Z",
    "completed_at": "2026-08-25T12:52:01.131836Z"
  }
]
```
```
$ jq -r 'if type=="array" then . else .entries end|[.[]|select(.status=="completed")]|length'
2
```

**Round 1's `error`, verbatim:** `Temporal RoundWorkflow failed before settling the round.` — this is
the pre-filler auto-placement round the ladder created on unpause. It is the exact symptom
`playbooks/observatory-api.md` §6 documents for a round that reaches the workflow with no filler
seat available, it is `failed` so it does **not** count, and rounds 2 and 3 supply the required two.

**"After the fillers were set" — two independent pieces of evidence.**

(a) `runs/2026-08-25-territory/log.md`, the phase-50 line (coordinator clock, see the discrepancy
note above), records the filler POST landing *before* the trigger:

```
2026-08-25T13:59:00Z 50 policy-versions resolved: steward=327e221b daveey, condottiere=22818fff daveey-1, homesteader=95091fc5, raider=d8d5829a; filler-policies POST 200 = exactly the two baselines
2026-08-25T13:59:30Z 50 unpause 200; trigger-round 200; round1=failed (auto-placement pre-filler, known), round2=pending; entrant_attributions round2 = both champions
```

(b) Stronger, and clock-independent: **both counted rounds actually seated those exact filler
policy-version ids**, which is only possible if the filler list was already registered when they ran.

```
GET $BASE/leagues/$L/filler-policies      (elevated header; this read 403s on bare AUTH)   (13:21:28Z)
```
```json
{"filler_policy_versions": [
  {"policy_version_id": "95091fc5-2f1b-4c6a-8995-066f3905922f", "policy_name": "territory-homesteader",
   "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"},
  {"policy_version_id": "d8d5829a-e2f7-4439-8d3d-1ff5605062b3", "policy_name": "territory-raider",
   "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"}
]}
```
```
GET $BASE/episode-requests?round_id=<each completed round>  then  GET $BASE/episode-requests/<id>
round 2 -> ereq_c77c7f2f-8443-49f4-8ba4-fca2a322ef1b
  status=completed replay=https://softmax-public.s3.amazonaws.com/replays/d68e8623-c1d5-430a-8658-e69c8696c7c0.replay
  champions=0:territory-steward/daveey, 1:territory-condottiere/daveey-1
  fillers=95091fc5-2f1b-4c6a-8995-066f3905922f, d8d5829a-e2f7-4439-8d3d-1ff5605062b3
round 3 -> ereq_d1b638fb-7588-4052-acea-0a69098f6126
  status=completed replay=https://softmax-public.s3.amazonaws.com/replays/1c2d12a8-0303-4ab0-a399-f2fa983a0da9.replay
  champions=0:territory-steward/daveey, 1:territory-condottiere/daveey-1
  fillers=95091fc5-2f1b-4c6a-8995-066f3905922f, d8d5829a-e2f7-4439-8d3d-1ff5605062b3
```

Status: **TRUE** — rounds 2 and 3 completed at 13:00:05.249892Z and 13:15:06.252473Z, both seating
the two registered filler versions; round 1 `failed` and is not counted.

---

## 2. Both champions ranked, fillers absent or Baseline — **TRUE**

```
GET $BASE/divisions/$D/leaderboard      (bare list, not .entries)      (13:17:23Z)
```
```json
[
  {"rank": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
   "score": 1030.5304984710244, "score_label": "Elo", "rounds_played": 2, "episode_wins": 2.0,
   "win_rate": 1.0, "policy_label": "territory-steward:v1"},
  {"rank": 2, "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
   "score": 969.4695015289755, "score_label": "Elo", "rounds_played": 2, "episode_wins": 0.0,
   "win_rate": 0.0, "policy_label": "territory-condottiere:v1"}
]
```
```
$ jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
1	daveey	territory-steward:v1	1030.5304984710244	2	2.0
2	daveey-1	territory-condottiere:v1	969.4695015289755	2	0.0
```

Status: **TRUE** — `daveey` (`territory-steward:v1`) and `daveey-1` (`territory-condottiere:v1`) are
both ranked, each `rounds_played = 2` (≥ 1). The response has exactly two rows: the fillers are
**absent** from the leaderboard entirely, which satisfies "absent or `policy_label` starting
`Baseline`". Elo has separated (1030.53 / 969.47) consistently with the two episodes' champion-vs-
champion outcomes (round 2: 276 > 172; round 3: 149 > 75), so `episode_wins` 2 vs 0 is coherent.

---

## 3. The latest round's episode request completed with a replay and the right participants — **TRUE**

Latest completed round = `round_7a7a2fe9-1f42-4efc-a975-ce761c97c340` (round_number 3, the
`max_by(.round_number)` of the completed set in check 1).

```
GET $BASE/episode-requests?round_id=round_7a7a2fe9-1f42-4efc-a975-ce761c97c340&limit=20   (13:17:31Z)
```
```json
{"n":1,"rows":[{"id":"ereq_d1b638fb-7588-4052-acea-0a69098f6126","status":"completed","created_at":"2026-08-25T13:07:46.957587Z"}]}
```
```
GET $BASE/episode-requests/ereq_d1b638fb-7588-4052-acea-0a69098f6126
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/1c2d12a8-0303-4ab0-a399-f2fa983a0da9.replay"
}
```
```
$ jq -r '.participants[]|[.position,.policy_name,.player_name,.is_filler,.policy_version_id]|@tsv'
0	territory-steward	      daveey    false	327e221b-545f-40a9-8c34-77b14c0b9117
1	territory-condottiere	  daveey-1  false	22818fff-298b-4a9f-81c6-08d5242f73e6
2	territory-homesteader	  daveey    true 	95091fc5-2f1b-4c6a-8995-066f3905922f
3	territory-homesteader	  daveey    true 	95091fc5-2f1b-4c6a-8995-066f3905922f
4	territory-homesteader	  daveey    true 	95091fc5-2f1b-4c6a-8995-066f3905922f
5	territory-raider	      daveey    true 	d8d5829a-e2f7-4439-8d3d-1ff5605062b3
6	territory-homesteader	  daveey    true 	95091fc5-2f1b-4c6a-8995-066f3905922f
7	territory-raider	      daveey    true 	d8d5829a-e2f7-4439-8d3d-1ff5605062b3
8	territory-homesteader	  daveey    true 	95091fc5-2f1b-4c6a-8995-066f3905922f

$ jq -c '.participant_scores'
[{"position":0,"score":149.0},{"position":1,"score":75.0},{"position":2,"score":249.0},
 {"position":3,"score":259.0},{"position":4,"score":220.0},{"position":5,"score":0.0},
 {"position":6,"score":177.0},{"position":7,"score":250.0},{"position":8,"score":336.0}]
```

Status: **TRUE** — `status == "completed"`, `replay_url` non-null, nine seats, and `participants`
names `daveey` at position 0 and `daveey-1` at position 1 with `is_filler: false`.

*Recorded, not a deduction:* this endpoint returns the fillers under their **real** policy names with
`is_filler: true` rather than the display form `Baseline (N)`. The `Baseline (N)` renaming appears in
the replay envelope's `players[]` — pasted in check 4 — and in the rendered scorebug in check 8. All
seven filler seats carry one of the two registered filler version ids.

---

## 4. Replay bytes are valid and show the game — **TRUE**

```
GET https://softmax-public.s3.amazonaws.com/replays/1c2d12a8-0303-4ab0-a399-f2fa983a0da9.replay
                                                                                      (13:17:39Z)
http=200 bytes=3897298 ctype=application/octet-stream
```

**Strict UTF-8 JSON**, two independent strict parsers (a browser's tolerance is not evidence):
```
$ jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok
$ python3 -c "b=open('/tmp/ep.replay','rb').read(); b.decode('utf-8'); print('python strict utf-8 decode: ok, bytes=',len(b)); import json; json.loads(b); print('json.loads: ok')"
python strict utf-8 decode: ok, bytes= 3897298
json.loads: ok
```

**`protocol` matches the manifest.**
```
$ jq -r '.protocol' /tmp/ep.replay
cogweb.replay.v1
$ jq -r 'keys|@csv' /tmp/ep.replay
"config","frames","players","protocol","results","usage"
```
The manifest served by the platform declares this envelope in
`manifest.game.protocols.global.value` (fetched fresh at 13:19Z from `GET $BASE/coworlds?limit=200`):

> `The saved replay is {"protocol":"cogweb.replay.v1", frames, players, config, results, usage}.`

Observed protocol string and observed top-level key set both match that declaration exactly. The same
manifest text declares the event vocabulary as *"order, rejected, talk, raze, salvage, struck, claim,
smear, voided, transfer, income, dried, recovered, eliminated, endcard"*; every kind actually emitted
(below) is a member of that set.

**`results`.**
```
$ jq -c '.results' /tmp/ep.replay
{"scores":[149,75,249,259,220,0,177,250,336],"reason":"complete","turnsPlayed":18,
 "fallbacks":[0,3,0,0,0,0,0,0,0],"eliminated":[],"razes":[0,0,0,0,0,0,0,0,0],
 "destroyed":0,"poolStart":146,"poolEnd":146}
```
`results.reason == "complete"` — the healthy value; not a `deadline`, so no documented exception is
being invoked (`design.md` §End conditions: `complete` and `elimination` pass, `deadline` tolerated
but must be reported).

**Seat identities — the `Baseline (N)` renaming.**
```
$ jq -c '.players' /tmp/ep.replay
[{"seat":0,"alias":"Sable","policy":"daveey","player":null},
 {"seat":1,"alias":"Ochre","policy":"daveey-1","player":null},
 {"seat":2,"alias":"Verdant","policy":"Baseline","player":null},
 {"seat":3,"alias":"Cobalt","policy":"Baseline (2)","player":null},
 {"seat":4,"alias":"Amber","policy":"Baseline (3)","player":null},
 {"seat":5,"alias":"Violet","policy":"Baseline (4)","player":null},
 {"seat":6,"alias":"Teal","policy":"Baseline (5)","player":null},
 {"seat":7,"alias":"Rose","policy":"Baseline (6)","player":null},
 {"seat":8,"alias":"Ash","policy":"Baseline (7)","player":null}]
```

**Champions were thinking, not falling back.** This lineage's decisions live in `actPrompt` frames
(the prompt's `.events[].type=="decision"` path is paintbot-shaped; the lineage equivalents are used
here, as the brief directs). `attempts` is omitted from the paste — each entry carries a full ~15 KB
prompt.
```
$ jq -r '[.frames[]|select(.type=="actPrompt")|.actPrompt|{seat,turn,usedFallback,nattempts:(.attempts|length)}]
         | group_by(.seat) | map({seat:.[0].seat, decisions:length,
             fallbacks:([.[]|select(.usedFallback)]|length),
             fallback_turns:[.[]|select(.usedFallback)|.turn],
             attempts_total:([.[].nattempts]|add)})'
seat 0  decisions 18  fallbacks 0  fallback_turns []        attempts_total 23
seat 1  decisions 18  fallbacks 3  fallback_turns [3,4,9]   attempts_total 29
seat 2  decisions 18  fallbacks 0  fallback_turns []        attempts_total 18
seat 3  decisions 18  fallbacks 0  fallback_turns []        attempts_total 18
seat 4  decisions 18  fallbacks 0  fallback_turns []        attempts_total 18
seat 5  decisions 18  fallbacks 0  fallback_turns []        attempts_total 18
seat 6  decisions 18  fallbacks 0  fallback_turns []        attempts_total 18
seat 7  decisions 18  fallbacks 0  fallback_turns []        attempts_total 18
seat 8  decisions 18  fallbacks 0  fallback_turns []        attempts_total 18
```
Champion seats 0 and 1: **3 fallbacks out of 36 decisions = 8.3 %**, a small minority. Cross-checks
against `results.fallbacks` `[0,3,0,0,0,0,0,0,0]` — same numbers, and the seven scripted baseline
seats correctly report 0 (they never call an LLM).

The three fallbacks were **not** an LLM outage — the recorded `error` is the game's own affordability
validator rejecting the model's order set:
```
$ jq -r '… select(.seat==1) … turns 1,9,18 …'
TURN 1  usedFallback=false attempts=1
  response: {"orders":[{"type":"claim","tile":"3,-3"}],"messages":[{"to":null,"text":"Ochre claims 3,-3. The yield-3 wall to my northwest—solid income foundation for turn 2."}]}
  error: null
TURN 9  usedFallback=true  attempts=3
  response:
  error: remote player (slot socket) failed 2 attempts: cannot afford this set (6 paint vs 5 stored)
TURN 18 usedFallback=false attempts=1
  response: {"orders":[],"messages":[{"to":null,"text":"Ochre T18: holding. Final turn—steady compounding into the finish. Sable, border east of 6,0 held throughout. Well played, all."}],"note":"Final turn: no moves. Peace held with Sable (border east of 6,0 maintained). Compounding 6 paint/turn income to end. Sc…"}
  error: null
```
```
$ jq -r '… select(.seat==0) … turns 1,9,18 …'
TURN 1  usedFallback=false attempts=1
  response: {"orders":[{"type":"claim","tile":"4,0"}],"messages":[{"to":null,"text":"Sable claims 4,0. A steward's opening: rich yield (3), distance 1. I intend to grow my home ring steadily and honour territorial borders. Neighbours: let us agree clear lines and prosper together."}]}
TURN 9  usedFallback=false attempts=2
  response: {"orders":[{"type":"claim","tile":"1,0"}],"messages":[{"to":null,"text":"Sable T9: claiming 1,0 (yield 3). West consolidation continues. Border east of 6,0 remains open for all. Ochre, Verdant, Cobalt—I keep my word."}]}
TURN 18 usedFallback=false attempts=1
  response: {"orders":[],"messages":[{"to":null,"text":"Sable T18: final hold. Income compounded to 50 paint banked. Steady peace into the finish—borders held, score cemented at 189 (139+50). All agreements kept through turn 18."}]}
```
This is non-scripted, non-trivial, game-specific content: correct order schema, real hex coordinates,
yields read off the board, and a negotiated border ("east of 6,0") that both champions reference
across turns.

**Champion seats are doing the thing the game is about.**
```
$ jq -r '[.frames[]|select(.type=="event")|.event|select(.seat==0 or .seat==1)]|group_by([.seat,.kind])|map({seat,kind,n})'
seat 0: order 23, claim 11, income 18, talk 22
seat 1: order 12, claim  4, income 18, talk 18
$ jq -r '[.frames[]|select(.type=="event")|.event.kind]|group_by(.)|map({k:.[0],n:length})'
claim 109 · dried 18 · endcard 1 · income 162 · order 294 · smear 71 · talk 40
$ jq -r '[.frames[].type]|group_by(.)|map({t:.[0],n:length})'
actPrompt 162 · event 695 · lobby 1 · snapshot 19 · status 38
```
19 snapshots for 18 turns + FINAL, so the viewer can re-derive every frame with no interpolation.

Status: **TRUE** — strict-parseable UTF-8 JSON, `protocol` matches the manifest declaration,
`results.reason == "complete"` over the full 18 turns, and the champion seats claim, hold, earn
income and negotiate publicly with a fallback rate of 3/36.

*Reported, not a failure:* this episode is a **fully peaceful** one — `razes: [0,…]`, `destroyed: 0`,
`poolStart == poolEnd == 146`, `warsStarted: 0`. `design.md` §Board and §What it measures declare a
zero-raze partition an explicitly legal and meaningful reading ("A board where nine seats partition
the lattice and honour their borders reads 0"), and the mechanic demonstrably *works* in this league —
round 2's replay (`d68e8623…`) records `razes: [5,2,0,0,3,2,0,0,0]` with the pool falling 163 → 150.
It does mean the currently featured match does not showcase permanent destruction. Flagged for the
coordinator as a curation observation, not a checklist failure.

---

## 5. Hosted game log is clean — **TRUE (CLEAN)**

```
GET $BASE/episode-requests/ereq_d1b638fb-7588-4052-acea-0a69098f6126/artifacts/logs
    headers: Authorization, User-Agent, X-Use-Elevated-Privileges                     (13:18:18Z)
http=200 bytes=1772
```

The body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it was
**decoded before grepping** (`ast.literal_eval` per repr) — a line-based grep on the raw form
undercounts. Decoded, in full (per-episode localhost websocket join tokens redacted by me; nothing
else is elided):

```
===== container: coworld-init-config =====
(empty)
===== container: bedrock-sidecar =====
2026-08-25 13:07:53,331 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1","has_role_arn":true,"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar","episode_request_id":"d1b638fb-7588-4052-acea-0a69098f6126","job_request_id":"1c2d12a8-0303-4ab0-a399-f2fa983a0da9","role":"game","slot":"game","image_digest":"sha256:0e5612623539396e221da1362b554de3c3aeb025e9cb9e38b290dd2b8cd3353f"}
[2026-08-25 13:07:53 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-08-25 13:07:53,516 INFO hypercorn.error Running on http://127.0.0.1:9100 (CTRL + C to quit)

===== container: game =====
[territory] coworld game-host listening at http://localhost:8080
[territory]   slot 0: ws://localhost:8080/player?slot=0&token=<redacted>
[territory]   slot 1: ws://localhost:8080/player?slot=1&token=<redacted>
[territory]   slot 2: ws://localhost:8080/player?slot=2&token=<redacted>
[territory]   slot 3: ws://localhost:8080/player?slot=3&token=<redacted>
[territory]   slot 4: ws://localhost:8080/player?slot=4&token=<redacted>
[territory]   slot 5: ws://localhost:8080/player?slot=5&token=<redacted>
[territory]   slot 6: ws://localhost:8080/player?slot=6&token=<redacted>
[territory]   slot 7: ws://localhost:8080/player?slot=7&token=<redacted>
[territory]   slot 8: ws://localhost:8080/player?slot=8&token=<redacted>
[territory] episode finished; scores=[149,75,249,259,220,0,177,250,336]
[territory] lingering 20000ms so the worker can finish its checks

===== container: worker =====
(empty)
```
```
$ python3 declog.py c5-logs.raw          # decode, then grep the four patterns
===== container: coworld-init-config ===== (0 decoded lines)
===== container: bedrock-sidecar ===== (3 decoded lines)
===== container: game ===== (12 decoded lines)
===== container: worker ===== (0 decoded lines)
--- containers=4 decoded_lines=15 pattern_hits=0
CLEAN
$ grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' c5-logs.raw
0
```

Status: **TRUE** — zero matches for `falling back`, `LLM provider is unavailable`,
`cut off at max_tokens` and `rejected`, on both the decoded text and the raw bytes, and the game
container ends with `episode finished` and scores matching `results.scores` exactly.

The Bedrock daily-token 429 that blocked the `coins` run earlier today (03:23Z, per the brief) did
**not** touch this coworld: the sidecar started clean, no throttle line appears, and the champion
seats' 33/36 successful LLM decisions in check 4 are direct positive evidence that the provider was
serving this episode. No documented exception is being invoked.

---

## 6. The public page uses the static replay path — **TRUE (iframe_static = true)**

Three sources tried, in the order `prompts/60-verify.md` and `playbooks/observatory-api.md` prescribe.
**Source used for the verdict: (c) the page's SSR payload + (d) the session call the page's own JS
makes.** (a) and (b) are recorded as *unknown*, not as failures, exactly as the prompt requires.

**(a) Raw-HTML iframe grep — finds nothing (unknown, not a failure).**
```
$ curl -sS "https://softmax.com/territory" | grep -o '<iframe[^>]*src="[^"]*"'      (13:18:31Z)
http=200 bytes=561182
(no output)
```
Consistent with `playbooks/observatory-api.md` §Featured match: the page is client-rendered for the
iframe and this grep finds nothing for *any* coworld.

**(b) Coworld detail API — `featured_match` null (unknown, not a failure).**
```
GET $BASE/coworlds?limit=200   (returns a bare array now, not {entries})
$ jq -r '.[]|select(.name=="territory")|{id,canonical,replay_viewer,featured_match}'
{"id":"cow_e7cac219-31d0-45c5-93f8-649434351365","canonical":true,"replay_viewer":null,"featured_match":null}
```
`featured_match` is null platform-wide per the same playbook note, so this is not evidence either way.
The manifest, however, does carry the static-bundle declaration:
```
$ jq -r '… select(.name=="territory")|.manifest.game.replay_viewer'
{"bundle": "sha256:18804de3b3f0206227302cb4cd675a1928da018547d2a74aaee91ae0ded5e0d5"}
```

**(c) The featured match, server-rendered into the page's SSR payload at `state.playlist[0]`** — read
out of the page bytes fetched in (a):
```json
"playlist":[{"episodeId":"440ddf69-ea2d-4806-8e8b-d987ff638645",
 "coworldId":"cow_e7cac219-31d0-45c5-93f8-649434351365","coworldName":"territory","coworldVersion":"0.1.1",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/1c2d12a8-0303-4ab0-a399-f2fa983a0da9.replay",
 "finishedAt":"2026-08-25T13:15:00.092514Z","roundNumber":3,"episodeNumber":1,"code":"territory.r3.e1",
 "matchup":{"divisionId":"div_350c663f-0e3d-42e5-9346-2be631892c17","divisionName":"Competition",
  "first":{"rank":1,"player_name":"daveey","score":1030.5304984710244,"score_label":"Elo",
           "rounds_played":2,"episode_wins":2,"win_rate":1,"policy_label":"territory-steward:v1"},
  "second":{"rank":2,"player_name":"daveey-1","score":969.4695015289755,"score_label":"Elo",
            "rounds_played":2,"episode_wins":0,"win_rate":0,"policy_label":"territory-condottiere:v1"}}}]
```
A featured match **is present** — `territory.r3.e1`, both champions in the matchup, and its
`replayUrl` is **the same replay verified byte-for-byte in check 4** (`1c2d12a8-0303-4ab0-a399-f2fa983a0da9`).

**(d) The iframe `src`, from the call the page's JS makes.**
```
POST $BASE/coworlds/replays/session                                                  (13:18:48Z)
     -d '{"coworld_id":"cow_e7cac219-31d0-45c5-93f8-649434351365",
          "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/1c2d12a8-0303-4ab0-a399-f2fa983a0da9.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e7cac219-31d0-45c5-93f8-649434351365/sha256%3Ac437064a5c0b5fbdfd91ab56b8b5c990e42f6cccc1815cc9e5eb25280eb9695f/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F1c2d12a8-0303-4ab0-a399-f2fa983a0da9.replay&v=2",
  "ready": true
}
```
```
path assertions:
  static path shape (…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=…): MATCH
  contains /client/replay: no
  <sha> segment == coworld manifest_hash sha256:c437064a…9695f: yes
```

Status: **TRUE** — the delivered `src` is the static route
`/v2/coworlds/replays/static/cow_e7cac219-…/sha256%3Ac437064a…/index.html?replay=<s3 url>`, with
`ready: true` and a path ending in `/index.html`. **No `/client/replay` pod URL anywhere.** The
`<sha>` is the coworld's manifest hash, as the playbook says it must be. A featured match is present.
`verify.iframe_static = true`.

---

## 7. Certification declared the static bundle — **TRUE**

Source read: **the committed `runs/2026-08-25-territory/release-result.json`** — phase 40's downloaded
artifact, already present in the repo (`git ls-files` tracked; no re-download was needed, so
`gh run download` for release run `32849157326` was not invoked).

```
$ jq -r '.certify.replay_liveness' runs/2026-08-25-territory/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Corroborating lines from the same file's `.certify.output_tail`:
```
  [run ] replay-present: a replay artifact was produced
  [pass] replay-present: a replay artifact was produced
  [run ] replay-loadable: the replay artifact has a declared viewer path
  [pass] replay-loadable: the replay artifact has a declared viewer path
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```
```
$ jq -c '.ok, .canonical, .manifest_sha, .version' runs/2026-08-25-territory/release-result.json
true
"sha256:c437064a5c0b5fbdfd91ab56b8b5c990e42f6cccc1815cc9e5eb25280eb9695f"
"0.1.1"
```

Status: **TRUE** — the string contains `Replay liveness: skipped (static replay bundle declared`
verbatim, and the `manifest_sha` it certified is the same hash appearing in check 6's viewer URL.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

Not fetched-and-inferred: the iframe `src` from check 6 was opened in headless chromium by a
`viewer-check.yml` run **this verifier dispatched in this heartbeat**.

```
$ SRC='<the check-6 viewer_url, verbatim, ?replay= and all>'
$ gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
  DISPATCH_AT=2026-08-25T13:18:53Z
$ gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10
32852582973	2026-08-25T13:18:54Z	in_progress	workflow_dispatch   <-- MINE (created 1s after dispatch)
32852194317	2026-08-25T13:14:57Z	completed	workflow_dispatch   (predates my dispatch — another run's)
32852051931	2026-08-25T13:13:29Z	completed	workflow_dispatch
32851786955	2026-08-25T13:10:47Z	completed	workflow_dispatch
…
```
The run was identified by **createdAt window**, not by taking "the latest" — other runs dispatch this
same workflow in parallel and the next-newest (13:14:57Z) predates my 13:18:53Z dispatch. Confirmed
from the artifact itself, which echoes the URL under test and matches my `SRC` exactly, replay uuid
`1c2d12a8-…` included:
```
$ jq -r '.url' runs/2026-08-25-territory/viewer-check/viewer-smoke.json
https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e7cac219-31d0-45c5-93f8-649434351365/sha256%3Ac437064a5c0b5fbdfd91ab56b8b5c990e42f6cccc1815cc9e5eb25280eb9695f/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F1c2d12a8-0303-4ab0-a399-f2fa983a0da9.replay&v=2
```
```
$ gh run watch 32852582973 -R Metta-AI/coworld-builder --exit-status
✓ viewer-check in 37s (ID 97816779303)
  ✓ Install Playwright (pinned 1.55.0)
  ✓ Load the viewer
  ✓ Summary
  ✓ Upload the evidence
  ✓ Fail if the viewer did not load        <-- green: the workflow's own load gate passed
watch_exit=0
$ gh run download 32852582973 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-25-territory/viewer-check
  smoke-stderr.txt (0 B)  smoke-stdout.txt (917 B)  viewer-smoke.json (1758 B)  viewer-smoke.png (452742 B)
```
Committed at `runs/2026-08-25-territory/viewer-check/` — this run's only rendered evidence.

### (b) The readouts, verbatim

`jq -c '{loaded, ms, clock, scorebug, feed_lines}' viewer-smoke.json`:
```json
{"loaded":true,"ms":1294,"clock":"Turn 1 / 18 · Commit","scorebug":"PAINT BANKED pool 146 → 146 1 Sable daveey 0 +0/turn (0.00/tick) ▮×1 · 2 Ochre daveey-1 0 +0/turn (0.00/tick) ▮×1 · 3 Verdant Baseline 0 +0/turn (0.00/tick) ▮×1 · 4 Cobalt Baseline (2) 0 +0/turn (0.00/tick) ▮×1 · 5 Amber Baseline (3) 0 +0/turn (0.00/tick) ▮×1 · 6 Violet Baseline (4) 0 +0/turn (0.00/tick) ▮×1 · 7 Teal Baseline (5) 0 +0/turn (0.00/tick) ▮×1 · 8 Rose Baseline (6) 0 +0/turn (0.00/tick) ▮×1 · 9 Ash Baseline (7) 0 +0/turn (0.00/tick) ▮×1 ·","feed_lines":1}
```

`jq -c '.signals' viewer-smoke.json`:
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["ready"],"bridge_ready":true,"bridge_error":[]}
```

**The three clock readouts** (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | `#clock` readout |
|---|---|
| 0 %   | `Turn 1 / 18 · Commit`  |
| 50 %  | `Turn 11 / 18 · Commit` |
| 100 % | `Turn 14 / 18 · Commit` |

`jq -r '.failure // "no failure"'` → `no failure`

Supporting fields from the same artifact:
```
$ jq -c '{status,bundle,replay,loading_text}' viewer-smoke.json
{"status":"Sable 0","bundle":null,"replay":null,"loading_text":null}
$ jq -r '.console_tail' viewer-smoke.json
["[bridge] ready"]
$ jq -c '.canvas_text' viewer-smoke.json
{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
$ jq -c '.soak' viewer-smoke.json
null
```
`loading_text: null` is the direct negative of the cogame-lantern failure — the page is not sitting on
"Loading replay…". `canvas_text.total: 0` reflects a DOM/SVG renderer with no canvas text draws, and
`--strict-text-bounds` is deliberately not used for this coworld (`design.md` §Viewer: the board is
pannable, so text may legitimately sit off-frame; the renderer fixture covers that instead).

**Both TRUE conditions hold:** `loaded: true` (via `data-replay-loaded="true"` *and* the
`coworld-replay` bridge `ready`, both independently present, first frame at **1294 ms**), and the
three clock readouts **differ** (Turn 1 → Turn 11 → Turn 14). The viewer draws, and it advances.

### (c) The replay JSON the viewer was asked to draw — ordered excerpts

Early (`.frames[] | select(.type=="event") | .event`, first 14 — `turn seat kind text`):
```
1	0	order	Sable claim 4,0
1	1	order	Ochre claim 3,-3
1	2	order	Verdant claim 5,-6
1	2	order	Verdant claim 3,-3
1	3	order	Cobalt claim 0,-7
1	3	order	Cobalt claim -1,-4
1	4	order	Amber claim -4,0
1	4	order	Amber claim -5,-1
1	5	order	Violet claim -4,0
1	5	order	Violet claim -5,-1
1	6	order	Teal claim -7,6
1	6	order	Teal claim -5,4
1	7	order	Rose claim -2,3
1	7	order	Rose claim 0,3
```
Middle (turns 9–10, first 12):
```
9	0	order	Sable claim 1,0
9	2	order	Verdant claim 2,-6
9	2	order	Verdant claim 6,-4
9	2	order	Verdant claim 2,-7
9	3	order	Cobalt claim -2,1
9	3	order	Cobalt claim 2,-6
9	3	order	Cobalt claim -3,-4
9	4	order	Amber claim -6,-1
9	4	order	Amber claim -4,-1
9	6	order	Teal claim -2,1
9	6	order	Teal claim -3,2
9	7	order	Rose claim -2,1
```
Late (last 16):
```
18		smear	Rose and Ash smeared -2,6 — nobody holds it
18	4	claim	Amber claimed -4,-3 (yield 0)
18		smear	Verdant and Teal and Rose and Ash smeared 1,0 — nobody holds it
18		smear	Verdant and Cobalt smeared 2,-6 — nobody holds it
18		smear	Rose and Ash smeared 2,1 — nobody holds it
18		dried	1 tile dried
18	0	income	Sable earned 10 paint from 12 walls
18	1	income	Ochre earned 6 paint from 5 walls
18	2	income	Verdant earned 23 paint from 23 walls
18	3	income	Cobalt earned 20 paint from 13 walls
18	4	income	Amber earned 21 paint from 21 walls
18	5	income	Violet earned 0 paint from 1 wall
18	6	income	Teal earned 14 paint from 12 walls
18	7	income	Rose earned 17 paint from 9 walls
18	8	income	Ash earned 25 paint from 22 walls
18		endcard	episode over (complete) after 18 turns · pool 146→146
```
```
$ jq -c '[.frames[]|select(.type=="event")|.event|select(.kind=="endcard")][0]'
{"seat":null,"kind":"endcard","text":"episode over (complete) after 18 turns · pool 146→146",
 "data":{"kind":"endcard","reason":"complete","turnsPlayed":18,
         "scores":[149,75,249,259,220,0,177,250,336],"walls":[12,5,23,13,21,1,12,9,22],
         "destroyed":0,"poolStart":146,"poolEnd":146,"warsStarted":0},"turn":18}
```
Champion talk, first four lines (the negotiated border the picture also shows):
```
T1 seat0 public :: Sable: Sable claims 4,0. A steward's opening: rich yield (3), distance 1. I intend to grow my home ring steadily and honour territorial borders. Neighbours: let us agree clear lines and prosper togeth…
T1 seat1 public :: Ochre: Ochre claims 3,-3. The yield-3 wall to my northwest—solid income foundation for turn 2.
T2 seat0 public :: Sable: Sable expands east: claiming 5,1 and 6,0 to solidify my home ring. I propose this border: everything east of 6,0 is open for others to grow. Ochre, Verdant—let's keep a clear eastern frontier a…
T2 seat0 public :: Sable: Steward doctrine: I claim, I dry, I hold. I honour borders I propose and reciprocate trust. Razing only in retaliation or late cashing-out.
```

### The spectator-judgment paragraph

**It is legible, it is moving, and it is unmistakably this game.** `viewer-smoke.png` (1280×800, taken
at the end of the scrub sequence, so it shows Turn 14) is a full, dense, readable console — nothing
empty, nothing frozen, nothing placeholder. Top strip: the `TERRITORY` wordmark with the gear-as-O
lockup, the `#clock` reading `Turn 14 / 18 · Commit`, nine per-seat chips carrying live scores
(`Sable 99`, `Ochre 45`, `Verdant 134`, `Cobalt 159`, `Amber 115`, `Violet 0`, `Teal 107…`), a pause
control and a `REPLAY` badge. Left column: the `#scorebug` "PAINT BANKED" income-per-tick leaderboard
with the header `pool 146 → 146` and rows in exactly the form the design specifies —
`Ash / Baseli… 211 +25/turn (1.00/tick) ▮×19`, down through `Sable / daveey 99 +9/turn (0.36/tick)
▮×12`, `Ochre / daveey-1 45 +6/turn (0.24/tick) ▮×4`, `Violet 0 +0/turn ▮×1` — alias stacked over
policy name, so a spectator can see which seats are the champions. Below it the `#feed` "WARS STARTED"
ledger with its counter reading `0` over two T13 sentences (`Sable and Rose and Ash smeared 2,1 —
nobody holds it and both paid in full`). Centre: the hex board, a 169-tile lattice of owner-coloured
hexes with wall sprites sized by yield, wet claims drawn as dashed splatter outlines, a header
`7 claimed × 6 smeared 0 rubble · pool 146/146`, a legend (`wall · cracked · half yield · rubble ·
gone · hearth`) and the affordance line `scroll zoom · drag pan · 2×click fit`. Right: `TURN LOG` T13
with individually-priced CLAIM entries (`Sable: Claim( 1,0 ) → 4 paint → smeared with Rose, Ash —
nobody holds it`) and a `CHANNELS` panel showing the champions' actual public talk at T14 — the same
`Ochre T14: claiming 1,0 (yield 3)…` and `Sable T14: … Border east of 6,0 remains open…` lines that
appear in the replay JSON above. Bottom: the transport band — a momentum rail with a red playhead,
per-turn beat `<button>`s `01`–`14` each carrying a stacked per-seat territory-share bar, turn 14
outlined as current, the phase strip `COMMIT · RESOLVE · UPKEEP`, and `TURN 14 /18`.

**Picture and record agree.** The scorebug's Turn-14 banked totals order the seats the same way
`results.scores` `[149,75,249,259,220,0,177,250,336]` does at turn 18 (Ash top, Violet zero); the
board header's `pool 146/146` and the ledger's `wars started 0` match `poolStart == poolEnd == 146`,
`razes: [0,…]`, `destroyed: 0`, `warsStarted: 0`; `Violet 0 +0/turn ▮×1` matches the late event
`Violet earned 0 paint from 1 wall`; the two T13 `smear` sentences in the ledger match the `smear`
events in the record; and the CHANNELS lines are verbatim the champion `talk` events. The three
differing clock readouts, the 14 populated beat cells and the moving playhead confirm the timeline
advances rather than repainting one frame.

**It looks like the starter's chrome, not a lookalike rewrite.** The layout is the cogherence lineage
`design.md` §Viewer specifies: `GameTopBar` over `.cg-stage` over `GameScrubberBar` as three flex
children, with `#clock` riding `GameTopBar`'s `phaseLine` prop, `#scrub` wrapping `GameScrubberBar`
whose rail cells are real labelled beat buttons with `renderRailExtra` filled by the territory-share
bar, and Territory's own `ScoreBug` / `WarLedger` / `BoardPanel` appended *inside* the stage. The
transport band is a flex row nothing paints over. This is the opposite of the cogame-gridlock failure
(a rewrite sharing only the ids): the shared chrome is visibly the same product, with a game block
added.

**Three legibility observations for the coordinator — none of them a check failure:**

1. **The 100 % scrub lands on Turn 14 / 18, not Turn 18 or FINAL.** The beat-button row renders `01`–
   `14` and the smoke's 100 % click therefore hits the last *visible* beat rather than the end of the
   timeline; the momentum rail above it does show cells past the playhead plus a bright FINAL slot at
   the far right. Motion is proven regardless (Turn 1 → 11 → 14), so check 8 passes, but a spectator
   dragging to the right-hand end of the beat row will not reach the endcard, and the endcard —
   which is where this coworld's whole deadweight-loss read-out lives — was consequently never
   rendered in this smoke. Worth a phase-30 look at whether the rail scrolls or clips.
2. **`feed_lines: 1` at the 0 % sample is expected, not a defect** — at Turn 1 the WarLedger holds only
   its `wars started: 0` header. The screenshot proves it populates later (two T13 entries).
3. **The featured match is a fully peaceful episode**, so the headline mechanic — permanent wall
   destruction and permadeath — is nowhere in the picture: `0 rubble`, `pool 146/146`, `wars started
   0`. The board reads as a clean nine-way partition, which the design calls a legitimate and
   interesting outcome, but round 2's replay (razes `[5,2,0,0,3,2,0,0,0]`, pool 163 → 150) would show
   the game's actual thesis. A curation note, not a bug.

Separately, and for the coordinator rather than for this checklist: **the two LLM champions were
out-earned by the scripted baselines** in this episode — Sable (daveey) 149 and Ochre (daveey-1) 75
against filler scores up to 336. The league Elo is unaffected (it ranks only the two champions against
each other, and daveey won both rounds 276>172 and 149>75), but the balance between LLM doctrine and
the tuned `homesteader` baseline is worth a look.

Status: **TRUE** — `loaded: true` with both load signals, first frame at 1294 ms, and three differing
clock readouts.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 2, 3 completed 13:00:05Z / 13:15:06Z; round 1 `failed` (pre-filler), not counted |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey rank 1, daveey-1 rank 2, `rounds_played` 2 each, no filler rows |
| 3 | Latest round's episode completed with replay + participants | **TRUE** — `ereq_d1b638fb…` completed, `replay_url` non-null, daveey/daveey-1 at seats 0/1 |
| 4 | Replay bytes valid and show the game | **TRUE** — strict UTF-8 JSON 3 897 298 B, `cogweb.replay.v1`, `reason: "complete"`, champion fallbacks 3/36 |
| 5 | Hosted game log clean | **TRUE** — decoded 15 lines across 4 containers, 0 pattern hits, CLEAN |
| 6 | Public page uses the static replay path | **TRUE** — static `/index.html?replay=…`, `ready: true`, no `/client/replay`; featured match `territory.r3.e1` |
| 7 | Certification declared the static bundle | **TRUE** — `Replay liveness: skipped (static replay bundle declared…` from the committed `release-result.json` |
| 8 | Spectator judgment (viewer executed) | **TRUE** — `loaded: true`, 1294 ms, clocks Turn 1 / 11 / 14 differ, run `32852582973` |

**Verdict: all-true (8/8).** Nothing was marked TRUE from an inference; every item above carries the
request made and the bytes returned.

Follow-ups for the coordinator, none of them blocking: the `log.md` clock is ~67 min ahead of real
UTC; the beat-row 100 % scrub stops at Turn 14 so the endcard never rendered; the featured match is a
zero-raze episode that does not showcase permanent destruction; and the scripted baselines out-earned
both LLM champions in this episode.
