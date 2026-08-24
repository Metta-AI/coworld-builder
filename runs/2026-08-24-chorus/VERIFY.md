# VERIFY — chorus   (2026-08-24T09:24Z)

Verdict: **1 item false** — checks 1–7 TRUE, **check 8 FALSE**.

Coworld `cow_dad8e6aa-4174-47fa-acb6-ef8157559b45` v0.1.1 · league
`league_472f2259-1529-44a4-937f-50deb5e3be63` · division `div_1bedcae9-38f6-40fe-b614-27c97e216c28`.

Common headers on every Observatory call below (values never printed):
`Authorization: Bearer $SOFTMAX_TOKEN`, `User-Agent: coworld-builder/1.0`; where noted also
`X-Use-Elevated-Privileges: true`.

Polling record (checks 1 and 3, every ~3–5 min, bounded at 75 min from 2026-08-24T08:38Z):

| poll (UTC) | rounds |
|---|---|
| 08:39:20 | r1 pending |
| 08:44:20 | r1 **completed** |
| 08:49:20 | r1 completed |
| 08:54:21 | r2 **completed**, r1 completed |
| 08:58:28 / 09:01:33 / 09:04:37 | unchanged (r2 episode has no replay — see check 3) |
| 09:07:42 | r3 pending, ereq running |
| 09:10:47 | r3 **completed** with a replay |

---

## 1. ≥2 completed rounds after fillers were set — **TRUE**

Fillers were registered at `2026-08-24T08:37:43Z`
(`runs/2026-08-24-chorus/log.md:39` — `50 fillers 200 arpeggio:v2=cf7bc5fd-8997-45bc-8ef9-9f9642b75976
pedal:v2=d2103485-522f-4cb6-9c79-c9a1b696cd00`), i.e. **before** round 1 was triggered at
`08:37:43Z` (`log.md:40`). Every round in the league therefore post-dates the fillers.

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}"       # fetched 2026-08-24T09:13:55Z
```

```json
[
  {
    "id": "round_45e3a692-ab90-4e48-bc9d-c703f4b4a1df",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-24T09:06:43.248008Z",
    "completed_at": "2026-08-24T09:09:56.503234Z",
    "scheduled_by": "ladder",
    "entrants": ["03797d55-fad7-4ec4-9061-885258aabf33", "3b9f2726-d6d2-4bb7-8abf-401295a6f088",
                 "9ea34f50-69ea-4134-9500-159c81e61a86", "82be99cf-008f-4e96-8d93-3f4415ef35e8"]
  },
  {
    "id": "round_b26afe84-9d49-475b-9a59-cb02b5d86f2d",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-24T08:51:42.870120Z",
    "completed_at": "2026-08-24T08:51:53.833752Z",
    "scheduled_by": "ladder",
    "entrants": ["3b9f2726-d6d2-4bb7-8abf-401295a6f088", "9ea34f50-69ea-4134-9500-159c81e61a86"]
  },
  {
    "id": "round_38403aa6-afd4-4199-9ccd-a0bb9a982227",
    "round_number": 1,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-24T08:36:42.467201Z",
    "completed_at": "2026-08-24T08:40:07.149281Z",
    "scheduled_by": "ladder",
    "entrants": ["3b9f2726-d6d2-4bb7-8abf-401295a6f088", "9ea34f50-69ea-4134-9500-159c81e61a86"]
  }
]
```

```bash
jq -r 'if type=="array" then . else .entries end | [.[]|select(.status=="completed")]|length'
# 3
```

Status: **TRUE** — 3 completed rounds (`round_number` 1, 2, 3; ids
`round_38403aa6-afd4-4199-9ccd-a0bb9a982227`, `round_b26afe84-9d49-475b-9a59-cb02b5d86f2d`,
`round_45e3a692-ab90-4e48-bc9d-c703f4b4a1df`), all after the fillers were set at 08:37:43Z. No
round is `failed` or `discarded`; every `error` is `null`.

**Observation for the coordinator (not a check failure):** round 2 is `completed` but produced no
episode — its single episode request finished 8 s after dispatch with `replay_url: null`,
`episode_id: null`, `scores: []` and `error: null` (pasted under check 3). Checks 1 and 2 do not
require an episode per round, and rounds 1 and 3 both produced real, replayed episodes, so this is
recorded rather than counted against any item.

---

## 2. Both champions ranked, fillers absent/Baseline — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
# fetched 2026-08-24T09:13:55Z   (bare JSON list, not {entries:…})
```

```
1	richard	co-gas-chorus-source-cantor-richard:v1	1048.0	1	3.0
2	relh	co-gas-chorus-source-cantor-relhalpha:v1	1016.0	1	2.0
3	daveey-1	chorus-weaver:v2	970.9421151160195	2	1.0
4	daveey	chorus-cantor:v2	965.0578848839805	2	1.0
```

Full rows for the two champions:

```json
  {"rank": 3, "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
   "score": 970.9421151160195, "score_label": "Elo", "rounds_played": 2, "episode_wins": 1.0,
   "win_rate": 0.25, "policy_label": "chorus-weaver:v2"},
  {"rank": 4, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
   "score": 965.0578848839805, "score_label": "Elo", "rounds_played": 2, "episode_wins": 1.0,
   "win_rate": 0.25, "policy_label": "chorus-cantor:v2"}
```

Status: **TRUE** — `daveey` (`chorus-cantor:v2`, `rounds_played` 2) and `daveey-1`
(`chorus-weaver:v2`, `rounds_played` 2) are both ranked. Neither filler
(`chorus-arpeggio:v2` = `cf7bc5fd-…`, `chorus-pedal:v2` = `d2103485-…`) appears on the leaderboard
at all — filler rows are absent, as the checklist allows.

Note: two outside players, `richard` and `relh`, have submitted their own policies to this league
and now sit at ranks 1–2. They are not fillers and not this run's champions; recorded for the
coordinator's awareness.

---

## 3. Latest round's episode request completed with a replay — **TRUE**

```bash
R=$(… max_by(.round_number) …)          # round_45e3a692-ab90-4e48-bc9d-c703f4b4a1df (round 3)
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}"   # fetched 09:13:5xZ
```

```
ereq_97f09452-a50a-4a45-b0d6-c752af324f10	completed	https://softmax-public.s3.amazonaws.com/replays/9bd6c9bb-6214-4b02-a554-3b27cddf760e.replay
```

```bash
curl -sS "$BASE/episode-requests/ereq_97f09452-a50a-4a45-b0d6-c752af324f10" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/9bd6c9bb-6214-4b02-a554-3b27cddf760e.replay",
  "participants": [
    {"position": 0, "kind": "policy", "policy_version_id": "03797d55-fad7-4ec4-9061-885258aabf33",
     "policy_name": "co-gas-chorus-source-cantor-relhalpha", "version": 1,
     "player_id": "ply_18302115-9fc9-482d-a2f3-f4c592bf9e57", "player_name": "relh", "is_filler": false},
    {"position": 1, "kind": "policy", "policy_version_id": "3b9f2726-d6d2-4bb7-8abf-401295a6f088",
     "policy_name": "chorus-cantor", "version": 2,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey", "is_filler": false},
    {"position": 2, "kind": "policy", "policy_version_id": "9ea34f50-69ea-4134-9500-159c81e61a86",
     "policy_name": "chorus-weaver", "version": 2,
     "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1", "is_filler": false},
    {"position": 3, "kind": "policy", "policy_version_id": "82be99cf-008f-4e96-8d93-3f4415ef35e8",
     "policy_name": "co-gas-chorus-source-cantor-richard", "version": 1,
     "player_id": "ply_ded11f40-3e30-4921-b019-f7f6bc3e9c83", "player_name": "richard", "is_filler": false}
  ],
  "participant_scores": [
    {"position": 0, "score": -0.531484},
    {"position": 1, "score": -1.100845},
    {"position": 2, "score": -0.940324},
    {"position": 3, "score": 0.083595}
  ]
}
```

Status: **TRUE** — the latest completed round (round 3) has one episode request,
`ereq_97f09452-a50a-4a45-b0d6-c752af324f10`, `status: "completed"`, non-null `replay_url`, and its
`participants` name both **`daveey`** (`chorus-cantor:v2`, position 1) and **`daveey-1`**
(`chorus-weaver:v2`, position 2). Round 3 had four real entrants, so no filler seat was needed and
no `Baseline (N)` participant appears; `participant_scores` is populated for all four seats.

Round 2's empty episode request, for the record (fetched 08:55Z and re-fetched 08:56Z, identical):

```json
{"id": "ereq_6aec867c-c574-42a0-ba2c-e216bfa1e7e8", "round_id": "round_b26afe84-…", "status": "completed",
 "replay_url": null, "episode_id": null, "error_type": null, "error": null,
 "scores": [], "participant_scores": [],
 "created_at": "2026-08-24T08:51:43.218630Z", "dispatched_at": "2026-08-24T08:51:43.369938Z",
 "running_at": null, "completed_at": "2026-08-24T08:51:51.811751Z"}
```

Round 1's episode request, for the record, is complete with a replay
(`ereq_ca6a57a4-81a7-479f-8867-f30497272fe1` →
`https://softmax-public.s3.amazonaws.com/replays/897473aa-1a72-4861-b076-4c9236df7657.replay`,
seats `daveey`, `daveey-1`, `Baseline`, `Baseline (2)`).

---

## 4. Replay bytes are valid and show the game — **TRUE**

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/9bd6c9bb-6214-4b02-a554-3b27cddf760e.replay" -o /tmp/ep.replay
# http 200  bytes 28093
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
python3 -c "open('/tmp/ep.replay','rb').read().decode('utf-8'); print('python strict utf-8 decode: ok')"
```

```
strict UTF-8 JSON: ok
python strict utf-8 decode: ok
```

```bash
jq -r '.protocol, .results.reason' /tmp/ep.replay
```

```
chorus.replay.v1
complete
```

`protocol` match: the replay protocol string `chorus.replay.v1` is the one the shipped code emits
and the one the wasm viewer accepts —
`src/chorus/server.nim:564` `"protocol": payload{"protocol"}.getStr("chorus.replay.v1")` and
`replay-viewer/chorus_replay.nim:42` `"protocol": replay{"protocol"}.getStr("chorus.replay.v1")`
(both fetched from `Metta-AI/cogame-chorus@main` this run) — and it is what `design.md`
§*Replay payload — `chorus.replay.v1`* declares. The published manifest
(`coworld_manifest_template.json`, fetched this run) declares `game.protocols.player` =
`chorus.player.v1` and `game.protocols.global`; it carries no separate replay-protocol key, so the
manifest's `chorus.player.v1` is the **player** protocol and is not the string under test here.
`jq -c '.game.replay_viewer'` on the same manifest → `{"bundle":"static-replay-viewer"}`.

```bash
jq -c '.policyNames, .config' /tmp/ep.replay
jq -r '[.events[].kind]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.replay
```

```json
["relh","daveey","daveey-1","richard"]
{"bars":8,"steps":16,"seed":868525827,"talk":true,"sampled":true}
{"bar": 32, "end": 1, "start": 1, "turn": 9}
```

43 events = `5·B + 3` for `B = 8`, exactly the count `design.md` §*Event vocabulary* predicts.

**Champion seats' decisions are non-scripted.** In chorus, decision provenance is the `scripted`
flag on `bar` events (an LLM seat that fell back is recorded `scripted: true`):

```bash
jq -c '[.events[]|select(.kind=="bar")]|group_by(.seat)[]|{seat:.[0].seat,voice:.[0].voice,n:length,scripted:([.[]|select(.scripted==true)]|length)}' /tmp/ep.replay
```

```json
{"seat":0,"voice":3,"n":8,"scripted":0}
{"seat":1,"voice":2,"n":8,"scripted":0}
{"seat":2,"voice":1,"n":8,"scripted":0}
{"seat":3,"voice":0,"n":8,"scripted":0}
```

**Zero fallbacks in the whole episode** — 0 of 32 bar events scripted, including the champion seats
1 (`daveey`) and 2 (`daveey-1`). Non-trivial content, first four bars of turn 0 and the last turn:

```
turn seat kind  say / steps
-1   -1   start
0    -1   turn
0     0   bar   "Opening motif on strong steps: 0-4-2 pattern, chord tones I(…"  0 . . 4 . . 2 . 0 . . 4 . . 2 .
0     1   bar   "Motif on steps 0,4,6,8,12,14: chord tones I(0,2,4) with step…"  0 . . 4 . . 2 . 0 . . 4 . . 2 .
0     2   bar   "Opening with I chord tones (0,2,4) spaced out for consonance…"  0 . . 4 . . 2 . 0 . . 4 . . . .
0     3   bar   "Opening motif on strong steps: 0-4-2 pattern, chord I tones …"  0 . . 4 . . 2 . 0 . . 4 . . 2 .
…
7     0   bar   "V chord (4,6,8): root and chord tones on strong steps 0,4,8,…"
7     1   bar   "Bar 7 V chord (4,6,8): root-third-fifth on strong steps, hal…"
7     2   bar   "Bar 7 V chord (4,6,8): tenor fills sparse steps with chord t…"
7     3   bar   "V chord (4,6,8): roots on strong steps, fifth leap then step…"
8    -1   turn
8    -1   end   complete
```

```bash
jq -c '.results' /tmp/ep.replay
```

```json
{"names":["relh","daveey","daveey-1","richard"],
 "scores":[-0.531484,-1.100845,-0.940324,0.083595],
 "voices":["Soprano","Alto","Tenor","Bass"],
 "onsets":[45,44,40,41],
 "piece":62.055342,"consonance":0.627236,"leading":0.752711,"rhythm":0.639766,"novelty":0.352679,
 "key":"G mixolydian","bpm":90,"bars":8,"maxBars":8,"reason":"complete"}
```

Status: **TRUE** — strict UTF-8 JSON under both `jq -e` and python's strict decoder; `protocol` is
`chorus.replay.v1` as the code and design declare; `results.reason == "complete"` (the design's
`deadline` exception is not needed); every one of the 32 bar events is a real LLM decision
(`scripted: 0` on all four seats) with substantive `say` text and 16-token bars that track the
published chord plan.

---

## 5. Hosted game log is clean — **TRUE**

```bash
curl -sS "$BASE/episode-requests/ereq_97f09452-a50a-4a45-b0d6-c752af324f10/artifacts/logs" \
  "${AUTH[@]}" "${ELEV[@]}"          # X-Use-Elevated-Privileges: true
# http 200  bytes 72325
# containers: coworld-init-config, bedrock-sidecar, game, worker
```

The body is python `b'…'` byte-string reprs, so it was decoded with `ast.literal_eval` per repr
before grepping (per `playbooks/observatory-api.md` §10):

```bash
python3 …decode…  # -> logs.decoded.txt, 203 lines
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs.decoded.txt \
  || echo CLEAN
```

```
CLEAN
```

```
decoded lines: 203
hits: 0
```

(The same grep against the **undecoded** bytes also returns 0, so the result does not depend on the
decode.)

Representative decoded `game` container lines showing live LLM play:

```
===== container: game =====
chorus: seed not pinned; randomized
chorus: seats=4 bars=8 talk=true
chorus: serving on 0.0.0.0:8080
chorus: player slot 1 connected (1/4)
chorus: slot 1 delivered a prompt (1142 chars)
…
chorus: starting with 4/4 players connected
chorus llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0, url http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
chorus: episode timeout 1200s (assumed); playing until 720s
chorus: turn 0 of 8 at 5s
chorus: turn 0 Ratchet (Soprano) writes bar 0 says "Opening motif on strong steps: 0-4-2 pattern, chord tones I(0,2,4), aiming for clarity." at 12s
chorus: turn 0 Tinker (Alto) writes bar 0 says "Motif on steps 0,4,6,8,12,14: chord tones I(0,2,4) with stepwise moves" at 12s
chorus: turn 0 Gasket (Tenor) writes bar 0 says "Opening with I chord tones (0,2,4) spaced out for consonance and rhythm." at 12s
chorus: turn 0 Gizmo (Bass) writes bar 0 says "Opening motif on strong steps: 0-4-2 pattern, chord I tones (0,2,4). Steps 0,4,8,12 main onsets." at 12s
chorus: turn 1 of 8 at 12s
…
```

Status: **TRUE** — zero lines matching
`falling back|LLM provider is unavailable|cut off at max_tokens|rejected` in the decoded hosted log
of the latest round's episode. No documented exception was needed. (The round-1 episode's log,
checked the same way at 08:47Z, was also CLEAN: 144 decoded lines, 0 hits.)

---

## 6. The public page uses the static replay path — **TRUE**

**Source used: the API the page reads** (the raw-HTML grep found nothing; the page is
client-rendered for the iframe, as `playbooks/observatory-api.md` §Featured match records).

```bash
curl -sS "https://softmax.com/chorus" | grep -o '<iframe[^>]*src="[^"]*"'
# http 200  bytes 487850
# (no match: page is client-rendered)
```

**Featured match — present**, server-rendered into the page's SSR payload at `state.playlist[0]`
(excerpt, unescaped from the raw HTML fetched 09:14Z):

```json
"leagueId":"league_472f2259-1529-44a4-937f-50deb5e3be63",
"playlist":[{"episodeId":"6d992f37-40c9-4d7e-977a-0d30ee745844",
  "coworldId":"cow_dad8e6aa-4174-47fa-acb6-ef8157559b45",
  "coworldName":"chorus","coworldVersion":"0.1.1",
  "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/9bd6c9bb-6214-4b02-a554-3b27cddf760e.replay",
  "finishedAt":"2026-08-24T09:09:56.112751Z","roundNumber":3,"episodeNumber":1,
  "code":"chorus.r3.e1",
  "matchup":{"divisionId":"div_1bedcae9-38f6-40fe-b614-27c97e216c28","divisionName":"Competition",
    "first":{"rank":1,"player_name":"richard",…},"second":{"rank":2,"player_name":"relh",…}}}]
```

(An earlier fetch at 08:47Z showed `"playlist":[]` and the page text "No featured match yet …
Between rounds"; it populated once round 3's episode landed.)

The coworld detail endpoint, for the record — its `featured_match` and `replay_viewer` are `null`,
which the playbook records as **platform-wide behaviour and not evidence**:

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" | jq -r '…select(.name=="chorus")|{id,canonical,replay_viewer,featured_match}'
```

```json
{"id": "cow_dad8e6aa-4174-47fa-acb6-ef8157559b45", "name": "chorus", "version": "0.1.1",
 "canonical": true, "replay_viewer": null, "featured_match": null}
{"id": "cow_660e6406-ca5d-4899-a62c-e9e318ecfde5", "name": "chorus", "version": "0.1.0",
 "canonical": false, "replay_viewer": null, "featured_match": null}
```

The iframe `src` is the URL the page's own JS obtains (playbook §Featured match / replay route):

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_dad8e6aa-4174-47fa-acb6-ef8157559b45",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/9bd6c9bb-6214-4b02-a554-3b27cddf760e.replay"}'
# http 200
```

```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_dad8e6aa-4174-47fa-acb6-ef8157559b45/sha256%3Af3a3b9c13c6820db542e7420b74ce69831960a263957e8a0c386901ee80198a4/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F9bd6c9bb-6214-4b02-a554-3b27cddf760e.replay&v=2",
  "ready": true
}
```

Status: **TRUE** — a featured match is present (round 3, episode 1, `chorus.r3.e1`), and the iframe
`src` is the **static** route
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` with
`<cow_id>` = `cow_dad8e6aa-4174-47fa-acb6-ef8157559b45` and `<sha>` =
`sha256:f3a3b9c13c6820db542e7420b74ce69831960a263957e8a0c386901ee80198a4` (URL-encoded), which
matches `STATE.coworld.manifest_sha` exactly. `ready: true` and the path ends `/index.html`. It is
**not** a `/client/replay` pod URL.

---

## 7. Certification declared the static bundle — **TRUE**

Source read: **the committed copy**, `runs/2026-08-24-chorus/release-result.json` (phase 40's
artifact, already present — no re-download was needed).

```bash
jq -r '.certify.replay_liveness' runs/2026-08-24-chorus/release-result.json
```

```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE** — the string contains `Replay liveness: skipped (static replay bundle declared`.

---

## 8. Spectator judgment — the viewer is EXECUTED, then judged — **FALSE**

`loaded: true`, but the **three clock readouts do not differ**: 0 % and 50 % are byte-identical.
Per `prompts/60-verify.md` check 8 that is FALSE, full stop.

### 8a. The dispatch

Attempt 1 (the one committed as this run's rendered evidence) used the **exact iframe `src` from
check 6**:

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_dad8e6aa-4174-47fa-acb6-ef8157559b45/sha256%3Af3a3b9c13c6820db542e7420b74ce69831960a263957e8a0c386901ee80198a4/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F9bd6c9bb-6214-4b02-a554-3b27cddf760e.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90   # 09:15:14Z
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 5 \
 | jq -c 'sort_by(.createdAt)|reverse|.[0]'
# {"conclusion":"","createdAt":"2026-08-24T09:15:17Z","databaseId":32710507461,"status":"in_progress"}
gh run watch 32710507461 -R Metta-AI/coworld-builder --exit-status     # exit 0 (GREEN)
gh run download 32710507461 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-24-chorus/viewer-check
```

Run **32710507461** — created `2026-08-24T09:15:17Z` (after the 09:15:14Z dispatch, found by
sorting on `createdAt`, not by taking "the latest" blind), conclusion **success**, 39 s.
`https://github.com/Metta-AI/coworld-builder/actions/runs/32710507461`

Committed at `runs/2026-08-24-chorus/viewer-check/`: `viewer-smoke.json`, `viewer-smoke.png`,
`smoke-stdout.txt`, `smoke-stderr.txt` (empty), plus attempts 2 and 3 (below) as
`attempt2-viewer-smoke.json`, `attempt3-viewer-smoke.json`, `attempt3-viewer-smoke.png`.

### 8b. The readouts

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-24-chorus/viewer-check/viewer-smoke.json
```

```json
{"loaded":true,"ms":4408,"clock":"BAR 0","scorebug":"","feed_lines":0}
```

```bash
jq -c '.signals' runs/2026-08-24-chorus/viewer-check/viewer-smoke.json
```

```json
{"data_replay_loaded":null,"data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/2026-08-24-chorus/viewer-check/viewer-smoke.json
# no failure
```

`smoke-stdout.txt`, verbatim:

```
{"loaded":true,"ms":4408,"clock":"BAR 0","scorebug":"","feed_lines":0}
scrub readouts: 0%="BAR 0"  50%="BAR 0"  100%="BAR 0 / 8 · G MIXOLYDIAN · 90 BPM · WAITING ON 4"
artifacts: /home/runner/work/coworld-builder/coworld-builder/viewer-smoke.png /home/runner/work/coworld-builder/coworld-builder/viewer-smoke.json
```

**The three clock readouts** (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | `#clock` |
|---|---|
| 0 % | `BAR 0` |
| 50 % | `BAR 0` |
| 100 % | `BAR 0 / 8 · G MIXOLYDIAN · 90 BPM · WAITING ON 4` |

0 % and 50 % are identical → **check 8 FALSE**.

The `#scrub` element *is* present (the harness only populates `scrub[]` when
`document.querySelector("#scrub")` is truthy), so this is not the "shell has no scrubber" case.

### 8c. Retries — 3 attempts, and what they show

| # | run id | url | `ms` | scrub 0 % / 50 % / 100 % |
|---|---|---|---|---|
| 1 | `32710507461` | check-6 iframe src (round-3 replay), `timeout=90` | 4408 | `BAR 0` / `BAR 0` / `BAR 0 / 8 · G MIXOLYDIAN · 90 BPM · WAITING ON 4` |
| 2 | `32710843104` | same url, `timeout=120` (warm CDN) | 4381 | `BAR 0` / `BAR 0` / `BAR 0 / 8 · G MIXOLYDIAN · 90 BPM · WAITING ON 4` |
| 3 | `32710988177` | **different replay** (round 1, `897473aa-…`), `timeout=120` | 1092 | `BAR 0` / `BAR 0` / `BAR 0 / 8 · C DORIAN · 90 BPM · WAITING ON 4` |

Attempt 2, verbatim:

```json
{"loaded":true,"ms":4381,"clock":"BAR 0","scorebug":"","feed_lines":0,
 "signals":{"data_replay_loaded":null,"data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]},
 "scrub":[{"at":"0%","clock":"BAR 0"},{"at":"50%","clock":"BAR 0"},{"at":"100%","clock":"BAR 0 / 8 · G MIXOLYDIAN · 90 BPM · WAITING ON 4"}],
 "failure":null}
```

Attempt 3, verbatim:

```json
{"loaded":true,"ms":1092,"clock":"BAR 0","scorebug":"","feed_lines":0,
 "signals":{"data_replay_loaded":null,"data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]},
 "scrub":[{"at":"0%","clock":"BAR 0"},{"at":"50%","clock":"BAR 0"},{"at":"100%","clock":"BAR 0 / 8 · C DORIAN · 90 BPM · WAITING ON 4"}],
 "failure":null}
```

All three CI runs were **green** (the workflow's gate only asserts `loaded === true`). The failure
is the readout rule, not the workflow.

### 8d. Root cause, from the shipped source (fetched from `Metta-AI/cogame-chorus@main` this run)

`BAR 0` is not a rendered frame — it is the shell's **static placeholder**:

```
replay-viewer/index.html:13      <div id="clock">BAR 0</div>
```

The renderer only ever overwrites it inside `setIndex` (`client/renderer.js:1299-1300`,
`options.clock.textContent = matchHeader(...)`), and `setIndex(0, true)` is called from **inside
`makeRenderer`'s callback** — which runs only after `loadImages` resolves (the floor, the font and
the four cog sprites). `buildChorusScrub`, which is what binds `pointerdown`/seek and builds the
beat-marker buttons on `#scrub`, is called in that same callback, as is
`document.documentElement.setAttribute("data-replay-loaded", "true")`.

But `replay-viewer/static_replay.js:120-123` posts the `ready` envelope two animation frames after
`attachReplay` is *called*:

```js
    // The renderer draws on its own animation frame; report ready one frame
    // later so "ready" means a picture, not merely a parsed payload.
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () { tell("ready"); });
```

Two rAFs ≈ 32 ms; the image loads take ~0.7–1.4 s. So `ready` fires **before the first frame is
drawn**, and the comment's promise ("ready means a picture") does not hold. The harness breaks its
poll loop on that `ready` (`templates/tools/ci/viewer_smoke.mjs:367`) and samples a DOM that is
still the untouched shell — which is exactly what the artifact shows: `clock` = the placeholder,
`scorebug` = `""`, `feed_lines` = 0, and `data_replay_loaded` = **null** even though the renderer
demonstrably set it later. The two scrub clicks then land on an `#scrub` that has no listeners yet,
so neither seek happens; by the third readout the renderer has attached and the clock shows its
genuine first frame.

**This is a real defect in `replay-viewer/static_replay.js`, reproducible across three independent
CI runs and two different replays.** `tell("ready")` must be posted from inside the
`ChorusRenderer.attachReplay` render callback (or gated on `data-replay-loaded`), not two rAFs
after the call. I have not changed it — reporting only.

### 8e. Spectator judgment

The picture is **not empty and not broken** — but the rendered evidence I have shows only the
opening frame, so I cannot certify motion.

`viewer-smoke.png` (run 32710507461, 1280×800, taken after the scrub attempts) shows a fully drawn,
legible chorus stage in the starter's Ink & Print palette:

- **Top band** — `CHORUS` wordmark in the starter's split-colour treatment, centre clock reading
  `BAR 0 / 8 · G MIXOLYDIAN · 90 BPM · WAITING ON 4`, `REPLAY` status chip and the `« LOG` feed
  toggle at the right. This is the starter's `#topband` / `#wordmark` / `#clock` / `#statuschip` /
  `#feedtoggle` chrome, not a lookalike rewrite.
- **`#scorebug`** — four plates, each `▶ +0.0 <VOICE> <name>`: `+0.0 SOPRANO daveey`,
  `+0.0 ALTO daveey-1`, `+0.0 TENOR richard`, `+0.0 BASS` (the fourth name, `relh`, is rendered at
  the left edge of the strip). Credits are signed to one decimal and the `▶` pending marker is on
  every seat, which is correct for a turn-0 frame where nobody has written yet. **Spectator-side
  policy names are used, as the two-name-space rule requires.**
- **Chord ribbon** — `I · vi · IV · V · I · vi · IV · V`, the live bar's chip amber. That is
  exactly `chords` from the replay (`P1 = [0,5,3,4]`, tiled) — picture and record agree.
- **Stage** — four lanes labelled `BASS / TENOR / ALTO / SOPRANO`, each with a seat-coloured cog
  sprite and the owning policy name (`richard`, `daveey-1`, `daveey`, `relh`), an 8-bar × 16-step
  grid with bright bar boundaries and ghost gridlines on steps 0/4/8/12, and the amber playhead
  parked on step 0 of bar 0. The grid is **empty of notes**, which is correct at event index 2 of
  43 (`start`, `turn 0`, one `bar`) — the replay's own first `turn` event carries
  `piece 15.0, credits [0,0,0,0]`, i.e. nothing written yet.
- **Score strip** — the `PIECE 0-100 · CREDIT PER COG` panel with its 0–100 axis, the signed
  zero rule and the four seat-coloured legend swatches, empty as it must be at turn 0.
- **Transport** — `❚❚` (playing), `♪ AUDIO` button inside the band, the scrubber populated with
  ~43 seat-coloured beat markers over alternating round spans, and `#pos` reading `2 / 43`. Nothing
  overlays the band.

So: **legible, and it is unmistakably this game** — a sequencer grid, four named voices, the public
chord plan and a signed credit-per-cog strip. It looks like the starter's chrome (same transport
strip, scrubber, scorebug, feed toggle, wordmark treatment as paintbot/raid/hive), not a rewrite
that merely reuses the ids; this is not the cogame-gridlock failure.

**What I cannot say** is that it *plays*. Both screenshots I have (run 1 at `2 / 43`, run 3 at
`1 / 43`) are the first frame, the two seek attempts provably did nothing, and the workflow's
invocation passes no `--soak`, so `soak` is `null` in every artifact. The transport shows the pause
glyph and the position advanced from index 0 to index 2 between attach and screenshot, which is
consistent with playback, but a two-frame inference is not the evidence this check demands. Against
the replay record — 43 events, a piece score walking `15.0 → 70.8 → 68.6 → 67.0 → 66.7 → 64.9 →
63.8 → 62.7 → 62.1` across the nine `turn` events, credits separating to
`[-0.53, -1.10, -0.94, +0.08]`, `reason: "complete"` — there is plenty for the viewer to draw; I
simply have no rendered proof that it draws it.

Status: **FALSE** — `loaded: true` but the three clock readouts do not differ (0 % == 50 % ==
`BAR 0`, the shell placeholder). Root cause is a premature `ready` signal in
`replay-viewer/static_replay.js`; it is reproducible and it is in this coworld's code, not in the
harness.
