# VERIFY — board-gauntlet   (2026-08-27T05:27Z)

Verdict: **all-true** (8 / 8)

Run `2026-08-27-board-gauntlet` · coworld `cow_dbadce13-6ad8-440d-a054-122e326af949` v0.1.0 ·
league `league_e96d74f3-745a-4308-86cf-0ed6489300e5` · division `div_b857da67-e8c4-424c-a378-5fb46b371c2f`.

Every call below was made **fresh in this phase-60 session** (window 04:51Z – 05:27Z), except the
two documented exceptions: item 7 (the committed `runs/<run>/release-result.json`, phase 40's
artifact copy) and item 8's rendered evidence (the `viewer-check.yml` run **this session
dispatched**, id 33042374554).

Common header block — headers are named, values never printed:

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_e96d74f3-745a-4308-86cf-0ed6489300e5
D=div_b857da67-e8c4-424c-a378-5fb46b371c2f
COW=cow_dbadce13-6ad8-440d-a054-122e326af949
```

---

## 1. ≥2 completed rounds after the fillers were set

Fetched 2026-08-27T05:25:56Z.

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}"      # http=200
 | jq 'if type=="array" then . else .entries end
       | map({id,round_number,status,error,created_at,completed_at,
              entrants:.round_config.entrant_policy_version_ids})'
```

```json
[
  {
    "id": "round_b7e6fcc1-389e-4268-ac02-15386f429340",
    "round_number": 4,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-27T05:18:43.225432Z",
    "completed_at": "2026-08-27T05:20:08.468901Z",
    "entrants": [
      "0bad04b4-cf6f-4638-9cda-50a4d019c392",
      "f9a218bb-3ee8-4156-8993-325a9c020cda"
    ]
  },
  {
    "id": "round_9db3b758-613f-4a36-8cdf-2b2f913a59df",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-27T05:03:41.530631Z",
    "completed_at": "2026-08-27T05:06:11.977711Z",
    "entrants": [
      "0bad04b4-cf6f-4638-9cda-50a4d019c392",
      "f9a218bb-3ee8-4156-8993-325a9c020cda"
    ]
  },
  {
    "id": "round_a6bf1118-0a5d-4580-a231-f82b92f75885",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-27T04:48:41.179565Z",
    "completed_at": "2026-08-27T04:50:54.684784Z",
    "entrants": [
      "0bad04b4-cf6f-4638-9cda-50a4d019c392",
      "f9a218bb-3ee8-4156-8993-325a9c020cda"
    ]
  },
  {
    "id": "round_da4c0a7f-1c27-48c8-8a9f-c2ebd6ba4c21",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-27T04:48:00.723249Z",
    "completed_at": "2026-08-27T04:48:00.967001Z",
    "entrants": [
      "0bad04b4-cf6f-4638-9cda-50a4d019c392"
    ]
  }
]
```

```bash
… | jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
3
```

Round 1's `error` verbatim, for the record: `"Temporal RoundWorkflow failed before settling the
round."` — it does **not** count. Its `entrant_policy_version_ids` holds only champion 1
(`0bad04b4…`), i.e. it fired against a half-populated league while the unpause was still landing.

Fillers, read fresh at 05:25:56Z (this read needs the `elevated` header even though it is a read):

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"   # http=200
 | jq -c '.filler_policy_versions[]|{policy_name,policy_version_id}'
```

```json
{"policy_name":"board-gauntlet-tactician","policy_version_id":"396d5236-f6e1-4a65-a2d2-3e13666168e8"}
{"policy_name":"board-gauntlet-hustler","policy_version_id":"f21847eb-9484-4034-91b2-8cc5e37dd2d5"}
```

Both filler version ids differ from both champions' (`0bad04b4…`, `f9a218bb…`), so no champion is
renamed Baseline.

Registration ordering — `runs/2026-08-27-board-gauntlet/log.md`, phase 50, quoted verbatim:

```
2026-08-27T04:52:00Z 50 fillers registered 200 BEFORE trigger: tactician 396d5236-…, hustler f21847eb-… (neither champion)
2026-08-27T04:52:30Z 50 unpaused 200; trigger-round 200 (workflow ladder-league_e96d74f3)
```

*Honest caveat on that log line:* the phase-50 agent's own wall clock ran ~4 min ahead of the
Observatory's (`log.md` says trigger at 04:52:30Z; the API records round 1 created at
04:48:00.723Z). The **ordering** is not in doubt — the filler POST preceded the trigger-round POST
in the same phase — and in any case rounds 2, 3 and 4 all post-date round 1 in `round_number` and
in `created_at`, and all three seat both champion version ids.

**Status: TRUE** — 3 completed rounds (round_number 2, 3, 4), completed 04:50:54.684784Z,
05:06:11.977711Z and 05:20:08.468901Z, all after the fillers were registered and all after the one
failed round (1). Requirement is ≥ 2.

---

## 2. Both champions ranked; fillers absent / Baseline

Fetched 2026-08-27T05:25:56Z.

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}"    # http=200 ; bare list, not .entries
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```

```
1	daveey	board-gauntlet-grandmaster:v1	1017.3341586646084	3	2
2	daveey-1	board-gauntlet-tempo:v1	982.6658413353916	3	1
```

Full body:

```json
[
  {
    "rank": 1,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 1017.3341586646084,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 3,
    "episode_wins": 2.0,
    "episodes_played": null,
    "win_rate": 0.6666666666666666,
    "policy_label": "board-gauntlet-grandmaster:v1",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 982.6658413353916,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 3,
    "episode_wins": 1.0,
    "episodes_played": null,
    "win_rate": 0.3333333333333333,
    "policy_label": "board-gauntlet-tempo:v1",
    "recent_rounds": null
  }
]
```

**Status: TRUE** — `daveey` (rank 1, `board-gauntlet-grandmaster:v1`, rounds_played 3) and
`daveey-1` (rank 2, `board-gauntlet-tempo:v1`, rounds_played 3) are both ranked with
`rounds_played ≥ 1`. The two rows are the whole list: neither filler
(`board-gauntlet-tactician:v1`, `board-gauntlet-hustler:v1`) appears, and no row is labelled
`Baseline` — the leaderboard is champions only. Both champions are LLM-prompt policies, not
scripted baselines.

---

## 3. Latest round's episode request completed with a replay

Latest completed round at fetch time = **round 4**, `round_b7e6fcc1-389e-4268-ac02-15386f429340`.
Fetched 2026-08-27T05:23:4xZ (list) and 05:24:0xZ (detail).

```bash
R=round_b7e6fcc1-389e-4268-ac02-15386f429340
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}"    # nested route; the flat
                                                            # ?round_id= route is 405 now
 | jq -c 'if type=="array" then . else .entries end | map({id,status,created_at})'
```

```json
[{"id":"ereq_5844e394-1f2e-45d9-b012-f7626e795ffd","status":"completed","created_at":"2026-08-27T05:18:45.483554Z"}]
```

```bash
EREQ=ereq_5844e394-1f2e-45d9-b012-f7626e795ffd
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}"        # http=200
 | jq '{status, replay_url, participants, participant_scores}'
```

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/cec5aa71-97a3-43b5-b62a-863a10ade535.replay",
  "participants": [
    {
      "position": 0,
      "kind": "policy",
      "policy_version_id": "0bad04b4-cf6f-4638-9cda-50a4d019c392",
      "policy_id": "9b341c2a-2b96-40f1-901c-16b79e3d675a",
      "policy_name": "board-gauntlet-grandmaster",
      "version": 1,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": false,
      "is_seed": false
    },
    {
      "position": 1,
      "kind": "policy",
      "policy_version_id": "f9a218bb-3ee8-4156-8993-325a9c020cda",
      "policy_id": "eb54f704-6564-4c20-9730-7c9800e63ef4",
      "policy_name": "board-gauntlet-tempo",
      "version": 1,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
      "player_name": "daveey-1",
      "is_filler": false,
      "is_seed": false
    }
  ],
  "participant_scores": [
    {"position": 0, "score": 1.0},
    {"position": 1, "score": -1.0}
  ]
}
```

**Status: TRUE** — `status == "completed"`; `replay_url` non-null
(`…/replays/cec5aa71-97a3-43b5-b62a-863a10ade535.replay`); both participants are the champions,
seat 0 `daveey` / `board-gauntlet-grandmaster` v1, seat 1 `daveey-1` / `board-gauntlet-tempo` v1,
both `is_filler: false`. Scores `+1 / −1` sum to zero as the design requires.

---

## 4. Replay bytes are valid and show the game

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/cec5aa71-97a3-43b5-b62a-863a10ade535.replay" \
     -o /tmp/ep.replay -w 'http=%{http_code} bytes=%{size_download}\n'
http=200 bytes=5918

jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok

python3 -c "d=open('/tmp/ep.replay','rb').read(); d.decode('utf-8'); print('python strict utf-8: ok',len(d),'bytes')"
python strict utf-8: ok 5918 bytes
```

Two independent strict parsers (jq's and CPython's `bytes.decode('utf-8')`, no `errors=`) both
accept the bytes — a browser's tolerance is not what was tested.

```bash
jq -r '.protocol, .results.reason, .results.ending' /tmp/ep.replay
gauntlet.replay.v1
complete
line

jq -c '.config, .names, .policyNames' /tmp/ep.replay
{"game":"connect-four","rotated":true,"size":7,"walls":0,"first":0,"seed":807933572,"maxPlies":42,"sampled":true}
["Flywheel","Widget"]
["daveey","daveey-1"]
```

`protocol` match: `design.md:877` pins the replay envelope as
`{"protocol": "gauntlet.replay.v1", …}` and `design.md:1449` — "The viewer reads
`gauntlet.replay.v1` and nothing else". The fetched bytes carry exactly that string. (The
Observatory manifest's `game.protocols` object documents only the two *wire* protocols,
`gauntlet.player.v1` and the global spectator socket; the replay protocol id lives in the replay
envelope and the design note, which is where I checked it.)

`results.reason == "complete"`, so the `deadline` exception `design.md:319` grants
("`results.reason` has **exactly two legal values**: `"complete"` and `"deadline"`") is **not
needed** here.

```bash
jq -c '.results' /tmp/ep.replay
```

```json
{"names":["daveey","daveey-1"],"scores":[1.0,-1.0],"outcome":[1.0,0.0],"game":"connect-four",
 "rotated":true,"size":7,"walls":0,"first":0,"seed":807933572,"winner":0,"plies":9,"maxPlies":42,
 "standing":[10028,47],"captures":[0,0],"wallsUsed":[0,0],"illegalReplies":[0,0],
 "fallbacks":[0,0],"ending":"line","reason":"complete"}
```

Non-scripted, non-trivial decisions:

```bash
jq -c '[.events[].kind]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.replay
{"end":1,"move":9,"start":1,"win":1}

jq -r '[.events[]|select(.fellBack==true)]|length' /tmp/ep.replay
0
jq -r '[.events[]|select(.scripted==true)]|length' /tmp/ep.replay
0
```

All 9 move events, in order (`tick/round · seat · kind · move · say`):

```
-	-	start
0	0	move	d	Opening centre - classic Connect Four strategy
1	1	move	d	Central control and parity advantage
2	0	move	d	Stacking the center to build vertical threat.
3	1	move	e	Building flank threat while maintaining central pressure.
4	0	move	d	Vertical threat at d4 — one move from victory.
5	1	move	e	Build the e-file threat while Red is locked in d-column.
6	0	move	d	Building my vertical threat in the d-file. Four in a row at d1-d2-d3-d4 incomin…
7	1	move	e	Build vertical threat in e-file; force Red to block or lose.
8	0	move	d	Playing d to extend vertical threat d1-d3-d4, forcing opponent block.
8	0	win
9	-	end
```

One mid-episode event in full, to show the per-ply reasoning is real and private-notes-bearing:

```json
{"kind":"move","round":4,"seat":0,"move":"d","mkind":"drop","capture":"",
 "say":"Vertical threat at d4 — one move from victory.",
 "notes":"Board: R at d1,d3; B at d2,e1. Opponent played e4? No, e1. Move 4 was e to rank 1. So B at d2, e1. R controls d-file vertical: d1-d3, need d4 to win. Opponent's fastest win: unclear, heuristic 12 vs mine 14 favors me slightly. Playing d again fills d4 next ply if opponent doesn't block. Opponent must respond at d to prevent my immediate win on ply 6. This forces their hand and maintains my winnin…",
 "scripted":false,"fellBack":false}
```

Terminal events:

```json
{"kind":"win","round":8,"seat":0,"how":"line","path":["d3","d4","d5","d6"]}
{"kind":"end","round":9,"reason":"complete","ending":"line","scores":[1.0,-1.0],"standing":[10028,47]}
```

**Status: TRUE** — valid UTF-8 JSON under two strict parsers; `protocol` = `gauntlet.replay.v1`
matches the design note; `results.reason` = `complete` (the normal case, no exception invoked);
9 of 9 champion-seat decisions are `scripted:false, fellBack:false` — `fallbacks:[0,0]`,
`illegalReplies:[0,0]`, so **zero** fallbacks, not a minority, and each move carries a distinct
`say` and a substantive private `notes`. The events show the thing the game is about: a Connect
Four vertical build in the d-file answered by an e-file counter-threat, ending in a real four in a
row (`path: ["d3","d4","d5","d6"]`).

---

## 5. Hosted game log is clean

Same episode request as items 3 and 4 (`ereq_5844e394-1f2e-45d9-b012-f7626e795ffd`, round 4).
Fetched 2026-08-27T05:23:5xZ.

```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}"
http=200 bytes=20580
```

The body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it was
decoded with `ast.literal_eval` per repr **before** grepping (a line-based grep on the raw body
undercounts):

```bash
# decode 20580 raw bytes -> 20501 chars of text, then:
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/ev/logs4.txt || echo CLEAN
CLEAN

grep -n '^===== container' /tmp/ev/logs4.txt
1:===== container: coworld-init-config =====
3:===== container: bedrock-sidecar =====
44:===== container: game =====
70:===== container: worker =====
```

All four containers were decoded and searched. The decoded `game` container in full, so the
CLEAN result is auditable rather than assertable:

```
board-gauntlet: seats=2 game=connect-four (drawn by the gauntlet rotation) size=7 walls=0 maxPlies=42 seed=807933572 model=claude-sonnet-5
board-gauntlet: serving on 0.0.0.0:8080
board-gauntlet: player slot 0 connected (1/2)
board-gauntlet: slot 0 delivered a prompt (1198 chars)
board-gauntlet: slot 0 delivered a prompt (1198 chars)
board-gauntlet: player slot 1 connected (2/2)
board-gauntlet: slot 1 delivered a prompt (1040 chars)
board-gauntlet: slot 1 delivered a prompt (1040 chars)
board-gauntlet: starting with 2/2 players connected
board-gauntlet llm: bedrock transport, url http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
board-gauntlet: episode timeout 1200s (assumed); playing until 720s, worst ply 66s
board-gauntlet: ply 1/42 Flywheel plays d at 6s
board-gauntlet: ply 2/42 Widget plays d at 11s
board-gauntlet: ply 3/42 Flywheel plays d at 14s
board-gauntlet: ply 4/42 Widget plays e at 20s
board-gauntlet: ply 5/42 Flywheel plays d at 23s
board-gauntlet: ply 6/42 Widget plays e at 28s
board-gauntlet: ply 7/42 Flywheel plays d at 31s
board-gauntlet: ply 8/42 Widget plays e at 35s
board-gauntlet: ply 9/42 Flywheel plays d at 38s
board-gauntlet: writing results and replay
board-gauntlet: artifacts written; 20s shutdown grace
board-gauntlet: episode complete, shutting down
```

**Status: TRUE** — zero matching lines in the latest round's hosted log.

### Attempt log for item 5 (retry budget used: 2 of 3)

*Attempt 1 — round 3's episode request* (`ereq_5a3fc2de-9fd4-4614-bc83-40ed27a01ed9`, the latest
completed round at 05:08Z). Two hits, quoted verbatim from the decoded text:

```
81:board-gauntlet llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
88:board-gauntlet llm: seat 0 falling back to the tactician baseline
```

with the surrounding decoded context:

```
board-gauntlet: ply 4/80 Flywheel plays d3h at 29s
board-gauntlet llm: seat 0 attempt 0 failed: seat 0: 'd4' is not a legal quoridor move
board-gauntlet llm: seat 0 attempt 1 failed: seat 0: 'd4' is not a legal quoridor move
board-gauntlet llm: seat 0 falling back to the tactician baseline
board-gauntlet: ply 5/80 Rivet plays c3 at 40s
```

Diagnosis, recorded so the coordinator has it even though the item now passes on round 4:
- Line 81 is the **platform-wide Bedrock capacity** symptom, cross-checked as SPEC item 5 allows.
  Two other LLM coworlds' *latest* hosted logs, fetched in this same session, carry the identical
  line at the same minute:
  ```
  # trick-taking, ereq_9e1b4c6b-1709-4660-821d-75eb28bc0455 (created 2026-08-27T04:41:09Z)
  trick-taking llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
  trick-taking llm: slot 0 attempt 0 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
  trick-taking llm: slot 0 falling back to a scripted decision

  # fog-of-war-boards, ereq_315203bc-3537-4dc0-a39b-e60cedbe85a9 (created 2026-08-27T04:44:26Z)
  fogboards llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
  fogboards llm: seat 0 attempt 0 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
  ```
  Three coworlds, three concurrent runs, one shared Bedrock quota — the documented platform-wide
  cause, not a defect in board-gauntlet. It is a *model-selection* fallback: the episode still ran
  entirely on an LLM.
- Line 88 is **not** platform-wide and I did not treat it as one. It is board-gauntlet's own
  declared degrade path (`design.md`: one retry carrying the printed legal-move list, then the
  tactician baseline) firing once after the sonnet reply named `'d4'`, a wall-blocked quoridor
  move, twice. It cost 1 ply of 13 (`fallbacks:[1,0]`, `illegalReplies:[1,0]` in that replay).
  Under a strict reading of SPEC item 5 that made round 3 **not** CLEAN.

*Attempt 2 — a different round.* Waited out one 15-minute ladder tick and re-ran the whole item
against round 4 (`round_b7e6fcc1…`, completed 05:20:08Z), which is CLEAN as pasted above, and
which is also the latest completed round, so items 3, 4 and 5 all speak about the same episode.

*Standing observation for the coordinator (not a blocker on this item):* the illegal-move-then-
fallback path is reachable in quoridor when a wall blocks the pawn step the model wants. It fired
once in 3 completed rounds (22 plies of LLM play, 1 fallback ≈ 4.5 %). Worth a phase-30 look at
whether the quoridor legal-move list in the prompt makes wall-blocked steps obvious enough; it is
not a correctness failure — the game refused the illegal move exactly as designed and the episode
still ended `complete`.

---

## 6. The public page uses the static replay path

**Source used: (b) the API the page's own JS calls** — `POST $BASE/coworlds/replays/session`,
after (a) the raw-HTML grep returned nothing, plus the page's SSR payload for the featured match.
Both sub-fetches are pasted; nothing here is inferred.

### 6a — the raw-HTML grep (documented *unknown*, not a failure)

```bash
curl -sS "https://softmax.com/board-gauntlet" -o /tmp/ev/page.html -w 'http=%{http_code} bytes=%{size_download}\n'
http=200 bytes=664789

grep -o '<iframe[^>]*src="[^"]*"' /tmp/ev/page.html || echo "GREP FOUND NOTHING (page is client-rendered)"
GREP FOUND NOTHING (page is client-rendered)
```

Per `playbooks/observatory-api.md` §Featured match — the page is client-rendered for the iframe
platform-wide, so an empty grep is *unknown*, not a false negative, and `/coworlds`'
`featured_match` is `null` for every coworld. Confirmed here for this coworld:

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}"
 | jq -c '…|select(.name=="board-gauntlet")|{id,canonical,manifest_hash,replay_viewer:.manifest.game.replay_viewer,featured_match}'
```

```json
{"id":"cow_dbadce13-6ad8-440d-a054-122e326af949","canonical":true,
 "manifest_hash":"sha256:c7acefc3970af7485d4e648e5bb09000c7e6a729b0e212cbfd0413b0f82658b4",
 "replay_viewer":{"bundle":"sha256:bd1307683ed5d47c85ac65868e193c1b478e69775c24dfd4fe4dd93216c0dc23"},
 "featured_match":null}
```

### 6b — the featured match, server-rendered into the page's SSR payload at `state.playlist[0]`

Extracted from the very `/tmp/ev/page.html` fetched above (JSON un-escaped for readability;
truncated at the end of `matchup.first`):

```json
"playlist":[{"episodeId":"bc279055-6e34-4e99-9c43-be369fb7cb03",
 "coworldId":"cow_dbadce13-6ad8-440d-a054-122e326af949",
 "coworldName":"board-gauntlet","coworldVersion":"0.1.0",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/cec5aa71-97a3-43b5-b62a-863a10ade535.replay",
 "finishedAt":"2026-08-27T05:20:01.462177Z","roundNumber":4,"episodeNumber":1,
 "code":"board-gauntlet.r4.e1",
 "matchup":{"divisionId":"div_b857da67-e8c4-424c-a378-5fb46b371c2f","divisionName":"Competition",
  "first":{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
   "score":1017.3341586646084,"score_label":"MMR","score_value_type":"integer","rounds_played":3,
   "episode_wins":2,"episodes_played":null,"win_rate":0.6666666666666666,
   "policy_label":"board-gauntlet-grandmaster:v1","recent_rounds":null},
  "second":{"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":…
```

A featured match **is** present (`board-gauntlet.r4.e1`, both ranked champions in `matchup`), and
its `replayUrl` is byte-identical to item 3's `replay_url` — the page is featuring the same
episode this document verified.

### 6c — the iframe `src`

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_dbadce13-6ad8-440d-a054-122e326af949",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/cec5aa71-97a3-43b5-b62a-863a10ade535.replay"}'
http=200
```

```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_dbadce13-6ad8-440d-a054-122e326af949/sha256%3Ac7acefc3970af7485d4e648e5bb09000c7e6a729b0e212cbfd0413b0f82658b4/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fcec5aa71-97a3-43b5-b62a-863a10ade535.replay&v=2",
  "ready": true
}
```

Shape check against the required pattern
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`:

| Required part | Value in the returned `viewer_url` |
|---|---|
| `/v2/coworlds/replays/static/` | present |
| `<cow_id>` | `cow_dbadce13-6ad8-440d-a054-122e326af949` — matches STATE |
| `<sha>` | `sha256%3Ac7acefc3970af7485d4e648e5bb09000c7e6a729b0e212cbfd0413b0f82658b4` → decodes to the coworld's **`manifest_hash`** above, as the playbook requires (not the viewer bundle digest) |
| `/index.html` | present; `ready: true` |
| `?replay=` | `https://softmax-public.s3.amazonaws.com/replays/cec5aa71-97a3-43b5-b62a-863a10ade535.replay` — the item-3 replay |
| `/client/replay` pod URL | **absent** |

**Status: TRUE** — featured match present (`board-gauntlet.r4.e1`, both champions ranked); the
iframe `src` is the static route on `api.observatory.softmax-research.net` with `ready: true`, and
contains no `/client/replay` pod path. Source used: the replay-session API (6c) for the `src` and
the page's SSR payload (6b) for the featured match, because the raw-HTML grep (6a) found nothing —
the platform-wide client-rendered behaviour, not a defect here.

---

## 7. Certification declared the static replay bundle

**Source read: the committed `runs/2026-08-27-board-gauntlet/release-result.json`** — phase 40's
artifact copy, present in the working tree; the `gh run download 33040017344` fallback was **not**
needed and was not used. (This is the documented exception to "fetch fresh": the certification
output is an artifact of this run's release dispatch, not a live endpoint.)

```bash
jq -r '.certify.replay_liveness' runs/2026-08-27-board-gauntlet/release-result.json
```

```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Tail of the same file's `certify.output_tail`, for the surrounding certification result:

```
  [run ] replay-present: a replay artifact was produced
  [pass] replay-present: a replay artifact was produced
  [run ] replay-loadable: the replay artifact has a declared viewer path
  [pass] replay-loadable: the replay artifact has a declared viewer path
  [run ] players-run: every declared player actually started on the smoke episode (not just declared)
  [pass] players-run: every declared player actually started on the smoke episode (not just declared)
  [run ] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks
  [pass] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks
Certified dist/coworld_manifest.json
Transcript: coworld-executable (10 steps passed)
…
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

```bash
jq -r '.certify.ok' runs/2026-08-27-board-gauntlet/release-result.json
true
```

**Status: TRUE** — the string `Replay liveness: skipped (static replay bundle declared` is present
verbatim, read from the committed `runs/<run>/release-result.json`.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged

### 8a — the dispatch

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_dbadce13-6ad8-440d-a054-122e326af949/sha256%3Ac7acefc3970af7485d4e648e5bb09000c7e6a729b0e212cbfd0413b0f82658b4/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fcec5aa71-97a3-43b5-b62a-863a10ade535.replay&v=2'
# dispatch_at = 2026-08-27T05:24:03Z
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
```

Find-the-new-run by `createdAt`, not by "the latest run":

```bash
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -c 'sort_by(.createdAt)|reverse|.[0:3][]'
{"createdAt":"2026-08-27T05:24:05Z","databaseId":33042374554,"status":"in_progress"}
{"createdAt":"2026-08-27T04:18:51Z","databaseId":33039031390,"status":"completed"}
{"createdAt":"2026-08-27T03:20:40Z","databaseId":33036080393,"status":"completed"}
```

`createdAt` 05:24:05Z > dispatch 05:24:03Z, and the next-newest run is 65 minutes older — this is
unambiguously **my** dispatch. Run id **33042374554**.

```bash
gh run watch 33042374554 -R Metta-AI/coworld-builder --exit-status
✓ viewer-check in 32s (ID 98418646277)   # green
gh run view 33042374554 -R Metta-AI/coworld-builder --json status,conclusion,createdAt,url
{"conclusion":"success","createdAt":"2026-08-27T05:24:05Z","status":"completed",
 "url":"https://github.com/Metta-AI/coworld-builder/actions/runs/33042374554"}

gh run download 33042374554 -R Metta-AI/coworld-builder -n viewer-check \
   -D runs/2026-08-27-board-gauntlet/viewer-check
-rw-r--r-- 1 root root      0 smoke-stderr.txt
-rw-r--r-- 1 root root    664 smoke-stdout.txt
-rw-r--r-- 1 root root   1560 viewer-smoke.json
-rw-r--r-- 1 root root 408159 viewer-smoke.png
```

`runs/2026-08-27-board-gauntlet/viewer-check/` holds this run's only rendered evidence and must be
committed with this file.

### 8b — the readouts, verbatim

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-27-board-gauntlet/viewer-check/viewer-smoke.json
```

```json
{"loaded":true,"ms":3168,"clock":"GAUNTLET → CONNECT FOUR 7×6 · PLY 0 / 42 · DAVEEY TO MOVE","scorebug":"daveey FLYWHEEL ▶ THREATS 0 0 SCORE daveey-1 WIDGET THREATS 0 0 SCORE HEURISTIC","feed_lines":31}
```

```bash
jq -c '.signals' runs/2026-08-27-board-gauntlet/viewer-check/viewer-smoke.json
```

```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/2026-08-27-board-gauntlet/viewer-check/viewer-smoke.json
no failure
```

The three clock readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub | clock readout |
|---|---|
| 0 % | `GAUNTLET → CONNECT FOUR 7×6 · PLY 0 / 42 · DAVEEY TO MOVE` |
| 50 % | `GAUNTLET → CONNECT FOUR 7×6 · PLY 5 / 42 · DAVEEY-1 TO MOVE` |
| 100 % | `GAUNTLET → CONNECT FOUR 7×6 · PLY 9 / 42 · FINAL` |

All three differ, in both the ply counter (0 → 5 → 9) and the state phrase
(`DAVEEY TO MOVE` → `DAVEEY-1 TO MOVE` → `FINAL`). A `#scrub` control **is** exposed — the JSON
carries real readouts, not the `"(no #scrub…)"` placeholder — so motion is proved by the DOM, not
only by the picture.

Supporting readouts from the same artifact:

```bash
jq -r '.status, .loading_text' …/viewer-smoke.json
REPLAY
LOADING REPLAY…

jq -r '.canvas_text' …/viewer-smoke.json
{"total": 776, "outside": 0, "ellipsized": 0, "never_inside": 0, "never_inside_samples": [], "distinct_capped": false, "samples": []}

jq -r '.console_tail' …/viewer-smoke.json
["[bridge] loading", "[bridge] ready"]
```

776 text draws, **0** outside the canvas, **0** ellipsized, **0** never inside — no clipped or
truncated captions anywhere in the render.

**Item 8 gate: `loaded: true` ✓ AND the three clock readouts differ ✓ → TRUE.**

### 8c — the replay JSON the viewer was asked to draw

Ordered excerpts from `/tmp/ep.replay` (item 4's bytes,
`…/replays/cec5aa71-97a3-43b5-b62a-863a10ade535.replay`), so the picture and the record can be
reconciled:

```
early   0  seat0  move  d   "Opening centre - classic Connect Four strategy"
        1  seat1  move  d   "Central control and parity advantage"
        2  seat0  move  d   "Stacking the center to build vertical threat."
middle  3  seat1  move  e   "Building flank threat while maintaining central pressure."
        4  seat0  move  d   "Vertical threat at d4 — one move from victory."
        5  seat1  move  e   "Build the e-file threat while Red is locked in d-column."
late    6  seat0  move  d   "Building my vertical threat in the d-file. Four in a row at d1-d2-d3-d4 incomin…"
        7  seat1  move  e   "Build vertical threat in e-file; force Red to block or lose."
        8  seat0  move  d   "Playing d to extend vertical threat d1-d3-d4, forcing opponent block."
        8  seat0  win       how=line  path=["d3","d4","d5","d6"]
        9         end       reason=complete ending=line scores=[1,-1] standing=[10028,47]
```

```json
{"names":["daveey","daveey-1"],"scores":[1.0,-1.0],"outcome":[1.0,0.0],"game":"connect-four",
 "winner":0,"plies":9,"maxPlies":42,"standing":[10028,47],"captures":[0,0],"wallsUsed":[0,0],
 "illegalReplies":[0,0],"fallbacks":[0,0],"ending":"line","reason":"complete"}
```

### 8d — spectator judgment

*(Written from `runs/2026-08-27-board-gauntlet/viewer-check/viewer-smoke.png`, the 1280×800 frame
CI captured at the 100 % scrub position, plus the readouts above. I did not render anything
locally.)*

**It is legible, and it shows the game.** The frame is a dark-charcoal stage with the wordmark
`GAUNTLET` top-left, the transport line centred — `GAUNTLET → CONNECT FOUR 7×6 · PLY 9 / 42 ·
FINAL`, so a spectator is told which of the four boards the rotation drew, how far in they are and
that it is over — and `REPLAY  « LOG` controls top-right. Directly under it the scorebug names
both sides by **player and cog alias**, with pixel-cog avatars in seat colours: red `daveey /
FLYWHEEL · THREATS 0 · +1 SCORE` on the left, blue `daveey-1 / WIDGET · THREATS 1 · −1 SCORE` on
the right, split by a horizontal eval bar filled far to the red end and captioned `HEURISTIC` —
the design's own promise that the bar is this repo's heuristic and not an engine evaluation is
honoured *in the picture*, not just in the docs. The bar's fill agrees with the recorded
`standing:[10028,47]`, and the ±1 scores agree with `scores:[1.0,-1.0]`.

The board is a 7×6 Connect Four grid with rank labels 6…1 down the left edge (I cropped and
enlarged that column to check: they read 6, 5, 4, 3, 2, 1 correctly) and cells drawn as recessed
wells. The d-file's top two discs are red with a gold win-ring; the visible lower cells show a red
disc on d1 and blue on d2 and e1–e2 — exactly the position the replay records after
d, d, d, e, d, e, d, e, d. Over the board's centre sits the endcard: `FINAL — 9 PLIES` /
**`DAVEEY WINS`** / a two-row table `SCORE · STANDING · CAPTURES · FALLBACKS` reading
`1 daveey 1 10028 0 0` and `2 daveey-1 −1 47 0 0`. Every number on that card matches
`results` byte for byte, including the `0 0` fallback column that item 4 proved. A spectator is
told who won, by how much, and that nobody's moves were played by a script.

Below the board a two-line feed shows the last thing each seat said, colour-keyed to its seat:
`Flywheel: "Playing d to extend vertical threat d1-d3-d4, forcing opponent block."` in red and
`Widget: "Build vertical threat in e-file; force Red to block or lose."` in blue — the exact
`say` strings of events 8 and 7 in the replay, so the caption track is the record, not decoration.
The artifact's `feed_lines: 31` is the DOM line count the smoke test read in the feed/log region;
I make no claim about which lines those are beyond the two visible in the frame. At the foot is a full-width
scrubber with a momentum strip of alternating red/blue tick marks (one per ply, the last one a fat
gold marker at the win), a `▶` play button, and a `12 / 12` position counter.

**It is not empty and it is not frozen.** The scrub table above shows the same shell reporting
ply 0, ply 5 and ply 9 at three positions — the picture is one frame of something that moves.

**It looks like the starter's chrome.** The layout is the paintbot/raid/hive family shell that
babel ships: the same top transport strip with wordmark-left / clock-centre / controls-right, the
same two-seat scorebug with avatar + tension readout + score flanking a centred bar, the same
board stage, the same seat-coloured say-feed band, and the same bottom scrubber with a momentum
graph and play control, ending on the same centred endcard panel. This is not the cogame-gridlock
failure mode — it is the starter's viewer with a Connect Four board drawn in the stage.

**Legibility observations (none blocking).** (1) In the eval bar the caption word `HEURISTIC` is
centred on the bar and the red fill boundary runs through it, so the word reads half-dark
half-on-red — legible at 1280 px, but slightly muddy; a phase-30 nicety, and note
`canvas_text.ellipsized == 0` so nothing is actually truncated. (2) The say-feed shows only the two
most recent lines; the `« LOG` control presumably opens the rest, which the smoke test did not
click, so I make no claim about it either way.

**Status: TRUE** — `loaded: true` (`data_replay_loaded: "true"` and the `coworld-replay` bridge
reaching `ready`, first frame at 3168 ms), three differing clock readouts, and a rendered frame
that a spectator can read and that matches the recorded episode.

---

## Summary table

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 2, 3, 4 completed; round 1 failed (error quoted) |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey r1, daveey-1 r2, 3 rounds each; no filler rows |
| 3 | Latest round's episode request completed with replay | **TRUE** — `ereq_5844e394…` completed, replay_url set, both champions seated |
| 4 | Replay bytes valid and show the game | **TRUE** — strict UTF-8 JSON, `gauntlet.replay.v1`, `reason: complete`, 9/9 non-scripted decisions, 0 fallbacks |
| 5 | Hosted game log clean | **TRUE** — CLEAN on round 4 (attempt 2); round 3's two hits diagnosed and quoted above |
| 6 | Public page uses the static replay path | **TRUE** — featured match `board-gauntlet.r4.e1`; static `index.html?replay=…`, `ready: true`, no `/client/replay` |
| 7 | Certification declared the static bundle | **TRUE** — committed `release-result.json`, string present verbatim |
| 8 | Viewer executed and judged | **TRUE** — run 33042374554, `loaded: true` @3168 ms, clocks ply 0 / 5 / 9 |

Nothing in this document is `NOT FETCHED`. Wall clock used against the 75-minute round-wait bound:
33 minutes (04:51Z → 05:24Z); the bound was not reached.
