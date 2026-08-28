# VERIFY — hide-and-seek   (2026-08-28T02:43Z)

Verdict: **all-true** (8 / 8)

Run: `2026-08-27-hide-and-seek` · coworld `cow_ccb33c23-b885-414d-b46f-86a1ff4a0292` v0.1.2 ·
league `league_7931991b-df9e-4248-98ca-c613dac7137d` · division `div_8ea628e9-769b-4aeb-a4a1-ed60092fea03`.

Every call below was made **fresh in this heartbeat** (02:17Z–02:43Z) except the two documented
exceptions: check 7 (reads the committed `runs/2026-08-27-hide-and-seek/release-result.json`, the
artifact phase 40 downloaded) and check 8's rendered evidence (downloaded from the
`viewer-check.yml` run **33136591103**, which this verifier dispatched at 02:39:57Z).

Common preamble (headers named, never their values):

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_7931991b-df9e-4248-98ca-c613dac7137d
D=div_8ea628e9-769b-4aeb-a4a1-ed60092fea03
COW=cow_ccb33c23-b885-414d-b46f-86a1ff4a0292
```

Note on shapes: `/rounds` and `/rounds/<id>/episode-requests` returned **bare arrays** this run, so
every `jq` below uses `(if type=="array" then . else .entries end)`.

---

## 1. ≥2 completed rounds after the fillers were set

**Fillers, fetched fresh (the read needs the `X-Use-Elevated-Privileges` header even though it is a read):**

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}" | jq .
```
```json
{
  "filler_policy_versions": [
    {
      "policy_version_id": "fcef50fe-c1b7-4e23-a82e-315f2c9341e2",
      "policy_id": "d9080c85-500a-4ff6-b289-965cc3009f09",
      "policy_name": "hns-burrow",
      "version": 3,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "display_name": null
    },
    {
      "policy_version_id": "21ddd411-3d38-43ce-a1d0-f9c41e92c8f3",
      "policy_id": "25e80295-26d9-4d88-bbf7-bedfe248cea3",
      "policy_name": "hns-scatter",
      "version": 3,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "display_name": null
    }
  ]
}
```

Neither filler version id is a champion's (`hns-quartermaster:v3` = `705b64c6-14dc-427c-9451-3e9a4d10a995`,
`hns-torchbearer:v3` = `97ec61df-63ad-4603-9769-d7127f2a9a05`; see check 3's participants block).

**Rounds:**

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq '(if type=="array" then . else .entries end)
       | map({id,round_number,status,error,created_at,completed_at})'
```
```json
[
  {
    "id": "round_8983ee66-e476-456d-8c20-465c2314d9bc",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T02:30:06.260133Z",
    "completed_at": "2026-08-28T02:36:03.411158Z"
  },
  {
    "id": "round_56279bed-bb1e-43c5-a7fe-d6694105ab23",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T02:15:03.402659Z",
    "completed_at": "2026-08-28T02:21:56.608838Z"
  },
  {
    "id": "round_e980d78a-b39f-4056-9ead-6748a6989a3e",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-28T02:14:00.477470Z",
    "completed_at": "2026-08-28T02:14:00.716058Z"
  }
]
```

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
# -> 2
```

Poll trace from this verifier (one line per minute, `{n: round_number, s: status}`), trimmed to the
transitions:

```
2026-08-28T02:17:49Z [{"n":2,"s":"pending"},{"n":1,"s":"failed"}]
2026-08-28T02:21:50Z [{"n":2,"s":"pending"},{"n":1,"s":"failed"}]
2026-08-28T02:22:51Z [{"n":2,"s":"completed"},{"n":1,"s":"failed"}]
2026-08-28T02:29:52Z [{"n":2,"s":"completed"},{"n":1,"s":"failed"}]
2026-08-28T02:30:54Z [{"n":3,"s":"pending"},{"n":2,"s":"completed"},{"n":1,"s":"failed"}]
2026-08-28T02:35:57Z [{"n":3,"s":"pending"},{"n":2,"s":"completed"},{"n":1,"s":"failed"}]
2026-08-28T02:36:57Z [{"n":3,"s":"completed"},{"n":2,"s":"completed"},{"n":1,"s":"failed"}]
2026-08-28T02:41:59Z [{"n":3,"s":"completed"},{"n":2,"s":"completed"},{"n":1,"s":"failed"}]
```

**Round 1's `error`, verbatim:** `Temporal RoundWorkflow failed before settling the round.` — the
documented signature of a `trigger-round` that fires before any filler policy exists
(`playbooks/observatory-api.md` §6). It is discounted, not counted.

Filler registration time, from `runs/2026-08-27-hide-and-seek/log.md`:

```
2026-08-28T02:16:12Z 50 filler-policies POST 200: hns-burrow:v3 fcef50fe-c1b7-4e23-a82e-315f2c9341e2, hns-scatter:v3 21ddd411-3d38-43ce-a1d0-f9c41e92c8f3 (neither champion)
```

Both counted rounds seated the fillers — round 2 and round 3's `participants` (check 3, and the
round-2 fetch below) both carry `is_filler: true` seats for `hns-burrow:v3` / `hns-scatter:v3`, which
is the settled proof that the filler set was live for them; round 1 seated none and died instantly.

Status: **TRUE** — rounds **2** (completed 02:21:56Z) and **3** (completed 02:36:03Z) are completed and
both are after the filler registration (02:16:12Z, and both seated the fillers). Round 1 (failed,
02:14:00Z) is excluded with its error quoted.

---

## 2. Both champions ranked; fillers absent or `Baseline`

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq .
```
```json
[
  {
    "rank": 1,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 1030.5304984710244,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 2.0,
    "episodes_played": null,
    "win_rate": 1.0,
    "policy_label": "hns-quartermaster:v3",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 969.4695015289755,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 0.0,
    "episodes_played": null,
    "win_rate": 0.0,
    "policy_label": "hns-torchbearer:v3",
    "recent_rounds": null
  }
]
```

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey	hns-quartermaster:v3	1030.5304984710244	2	2.0
2	daveey-1	hns-torchbearer:v3	969.4695015289755	2	0.0
```

Status: **TRUE** — `daveey` (rank 1, `hns-quartermaster:v3`, `rounds_played` 2) and `daveey-1`
(rank 2, `hns-torchbearer:v3`, `rounds_played` 2) are both ranked; the leaderboard has exactly two
rows, so the fillers `hns-burrow:v3` / `hns-scatter:v3` are **absent** (and inside the episode they
render as `Baseline` / `Baseline (2)` / `Baseline (3)` / `Baseline (4)` — see check 4's
`results.names`).

---

## 3. The latest completed round's episode request completed with a replay

```bash
R=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
    | jq -r '[(if type=="array" then . else .entries end)[]
              |select(.status=="completed")]|max_by(.round_number).id')
# -> round_8983ee66-e476-456d-8c20-465c2314d9bc   (round 3)

curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)|map({id,status})'
```
```json
[{"id":"ereq_60c137bb-526b-42ec-a934-66496e4e9a41","status":"completed"}]
```

(The nested route is used deliberately: the flat `GET /episode-requests?round_id=…` is 405 since
2026-08-26 — `playbooks/observatory-api.md` §9.)

```bash
EREQ=ereq_60c137bb-526b-42ec-a934-66496e4e9a41
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url,
        participants: [.participants[]|{position,policy_name,version,policy_version_id,player_name,is_filler}],
        participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/2b8607e0-12fd-44fa-95f0-a7b7d1a3c03a.replay",
  "participants": [
    {"position": 0, "policy_name": "hns-quartermaster", "version": 3,
     "policy_version_id": "705b64c6-14dc-427c-9451-3e9a4d10a995",
     "player_name": "daveey",   "is_filler": false},
    {"position": 1, "policy_name": "hns-torchbearer",   "version": 3,
     "policy_version_id": "97ec61df-63ad-4603-9769-d7127f2a9a05",
     "player_name": "daveey-1", "is_filler": false},
    {"position": 2, "policy_name": "hns-scatter", "version": 3,
     "policy_version_id": "21ddd411-3d38-43ce-a1d0-f9c41e92c8f3",
     "player_name": "daveey", "is_filler": true},
    {"position": 3, "policy_name": "hns-scatter", "version": 3,
     "policy_version_id": "21ddd411-3d38-43ce-a1d0-f9c41e92c8f3",
     "player_name": "daveey", "is_filler": true},
    {"position": 4, "policy_name": "hns-burrow",  "version": 3,
     "policy_version_id": "fcef50fe-c1b7-4e23-a82e-315f2c9341e2",
     "player_name": "daveey", "is_filler": true},
    {"position": 5, "policy_name": "hns-scatter", "version": 3,
     "policy_version_id": "21ddd411-3d38-43ce-a1d0-f9c41e92c8f3",
     "player_name": "daveey", "is_filler": true}
  ],
  "participant_scores": [
    {"position": 0, "score": 0.14},
    {"position": 1, "score": -0.14},
    {"position": 2, "score": 0.14},
    {"position": 3, "score": -0.14},
    {"position": 4, "score": 0.14},
    {"position": 5, "score": -0.14}
  ]
}
```

For completeness, the **other** completed round (round 2) also fetched fresh this run:

```bash
curl -sS "$BASE/rounds/round_56279bed-bb1e-43c5-a7fe-d6694105ab23/episode-requests" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)|map({id,status})'
# -> [{"id":"ereq_e221daea-f581-45e2-8f9d-644bd391b83b","status":"completed"}]
# detail: status "completed",
#   replay_url "https://softmax-public.s3.amazonaws.com/replays/80816fca-d39a-456f-979e-b608bf84d5e9.replay",
#   participants position 0 hns-quartermaster:v3 / daveey (is_filler false),
#                position 1 hns-torchbearer:v3   / daveey-1 (is_filler false),
#                positions 2-5 hns-burrow / hns-scatter v3 (is_filler true)
```

Status: **TRUE** — `status == "completed"`, `replay_url` non-null, and the participant list names
`daveey` (`hns-quartermaster:v3`) at seat 0 and `daveey-1` (`hns-torchbearer:v3`) at seat 1, with the
four remaining seats flagged `is_filler: true`. (The Observatory participants list reports fillers by
their real policy name plus `is_filler`; the `Baseline (N)` display names appear in the episode's own
results — see check 4.)

---

## 4. Replay bytes are valid and show the game

The replay is the starter's **binary `COWLDHNS`** container, not JSON — `design.md` §"Replay bytes
(self-sufficient)" (lines 1106–1132) declares this and specifies the phase-60 substitute: run the
repo's `tools/replay_summary.py`, which emits **one strict-UTF-8 JSON object**, and apply the strict
parser to that. That is exactly what is done here. `replay_summary.py` was fetched fresh this run
from `Metta-AI/cogame-hide-and-seek@main`.

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/2b8607e0-12fd-44fa-95f0-a7b7d1a3c03a.replay" \
     -o /tmp/ep.replay -w 'http=%{http_code} bytes=%{size_download}\n'
# -> http=200 bytes=85815

gh api repos/Metta-AI/cogame-hide-and-seek/contents/tools/replay_summary.py --jq .content \
 | base64 -d > /tmp/replay_summary.py
python3 /tmp/replay_summary.py /tmp/ep.replay > /tmp/ep.json          # exit 0
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
```
```
strict UTF-8 JSON: ok
```

```bash
jq -r '.protocol' /tmp/ep.json
jq -r '.results.reason, .results.endRule, .results.games' /tmp/ep.json
```
```
hide-and-seek/v1
complete
full_time
2
```

`protocol` matches the manifest / design contract (`design.md:1756` — `protocol == "hide-and-seek/v1"`).
`results.reason == "complete"` is the healthy value; the design's declared-acceptable `deadline`
(`design.md:415-421`) was **not** needed.

```bash
jq -c '.results.gameMargins, .results.locks, .results.grabs, .results.names,
       .results.policyKinds, .results.scores, .results.llmTurns,
       .results.fallbackTurns, .results.ordersRejected, .results.room,
       .results.finalTick, .results.stopDetail' /tmp/ep.json
```
```
[-495,-775]
[0,4,0,0,0,0]
[0,3,0,0,0,0]
["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"]
["llm","llm","scripted","scripted","scripted","scripted"]
[0.14,-0.14,0.14,-0.14,0.14,-0.14]
[20,20,0,0,0,0]
[0,0,0,0,0,0]
[0,0,0,0,0,0]
"warren"
3587
""
```

`sum(locks) = 4` and `sum(grabs) = 3`, both non-zero — somebody used the furniture, which is the
design's "the game actually happened" bar (`design.md:1130`).

Decision provenance — champion seats are **non-scripted with real content, not fallbacks**:

```bash
jq -r '[.orders[]|.source]|group_by(.)|map({(.[0]):length})|add|tostring' /tmp/ep.json
jq -r '[.orders[]|select(.source=="llm" and (.slot==0 or .slot==1))]|length' /tmp/ep.json
jq -r '.fallbacks, .budgetGuards, (.radio|length), (.orders|length), .tickCount, .seed' /tmp/ep.json
```
```
{"llm":40,"scripted":80}
40
0        <- .fallbacks  (count of {"k":"fallback"} records)
0        <- .budgetGuards
32       <- radio lines
120      <- total directives
3587     <- tickCount
611813715
```

**Zero** fallbacks out of 40 champion-seat LLM directives (and `results.fallbackTurns` is
`[0,0,0,0,0,0]`, `results.ordersRejected` is `[0,0,0,0,0,0]`). Sample of the champion seats' actual
decisions (`game turn slot alias source intent object at radio`):

```
1	0	0	HIDER-alpha	llm	push	box2		d1 west closet r1
1	2	0	HIDER-alpha	llm	lock	box2		Turn 2: box2 locked at d1. Gamma/Beta seal d3/d4. Next: push ramps to corner.
1	4	0	HIDER-alpha	llm	lock	ramp1		Turn 4: ramp1 locked at corner. Moving to hide.
1	4	1	SEEKER-alpha	llm	watch			HIDER-beta at 266,270 south hall - holding position
2	0	1	HIDER-alpha	llm	push	box2		Breaking north-south through n-hall
2	11	0	SEEKER-alpha	llm	watch			HIDER-alpha pinned at [215,126]. Maintain lock.
2	11	1	HIDER-alpha	llm	hide		p1	SEEKER-alpha has direct LOS at 241,124. Retreating to p1 corner behind box4.
```

Status: **TRUE** — 85 815 bytes fetched (HTTP 200); the summariser's output parses under a strict
UTF-8 JSON parser; `protocol == "hide-and-seek/v1"`; `results.reason == "complete"` /
`endRule == "full_time"` / `games == 2`; non-zero locks (4) and grabs (3); the champion seats made
40 LLM decisions with real intents, real object references and 32 radio lines, and **zero** fallbacks.

---

## 5. Hosted game log is clean

```bash
curl -sS "$BASE/episode-requests/ereq_60c137bb-526b-42ec-a934-66496e4e9a41/artifacts/logs" \
     "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs3.raw -w '%{http_code} %{size_download}\n'
# -> 200 84312

# The body is python b'…' byte-string reprs under "===== container: <name> =====" headers.
# Decode each repr with ast.literal_eval before grepping (playbooks/observatory-api.md §10).
python3 /tmp/declog.py /tmp/logs3.raw > /tmp/logs3.txt
wc -l /tmp/logs3.txt
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs3.txt \
  || echo CLEAN
```
```
207 /tmp/logs3.txt
CLEAN
```

Containers present in the decoded body (proof the decode found the whole log, not a fragment):

```
1:===== container: coworld-init-config =====
3:===== container: bedrock-sidecar =====
168:===== container: game =====
207:===== container: worker =====
```

Tail of the `game` container, decoded:

```
seat 2 registered: kind=scripted baseline=scatter
seat 4 registered: kind=scripted baseline=burrow
seat 5 registered: kind=scripted baseline=scatter
seat 3 registered: kind=scripted baseline=scatter
game starting in 1
...
game 1 started: players=6
Dropped message to disconnected client
game 1 over: margin -495 permille (hiders)
game 1 done; margin -495 permille (hiders)
game 2 started: players=6
game 2 over: margin -775 permille (hiders)
game 2 done; margin -775 permille (hiders)
Writing replay file: /tmp/hns-replay-1.bitreplay
Replay written: /tmp/hns-replay-1.bitreplay (85815 bytes)
Events written: /coworld/events.json (184 events, 26140 bytes)
Frame pacing: 2160 playing frames — skipped 2134 (98.8%), waited 2 (0.1%), late 24 (1.1%)
Player traffic: 4.7 MB to 6 players — images 4.7 MB (98.7%), objects 0.1 MB (1.3%)
```

Status: **TRUE** — `CLEAN`, zero matches for any of the four patterns in the latest completed round's
hosted log.

**Recorded observation, not a check-5 failure (round 2, the *earlier* completed round).** Round 2's
log — `ereq_e221daea-f581-45e2-8f9d-644bd391b83b`, fetched fresh this run at 02:26Z, HTTP 200,
84 537 bytes — was **not** clean:

```
198:hide-and-seek llm: seat 1 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
199:hide-and-seek llm: seat 1 falling back to burrow (parse_error) on turn 5
```

That is one seat, one turn, of one earlier episode: an attempt-1 transport timeout against the local
Bedrock sidecar followed by a parse error on the retry, degrading to the scripted `burrow` policy for
a single turn — precisely the design's "degrade, never hang" ladder doing its job. Round 2's replay
also shows it as a **minority**: 39 LLM directives vs 1 with `source == "fallback"`
(`results.fallbackTurns` `[0,1,0,0,0,0]`). Check 5 is defined on **the latest** completed round's
log, and that log is CLEAN, so the check is TRUE; this is logged so the coordinator can see the
Bedrock latency jitter that exists in the environment.

---

## 6. The public page uses the static replay path

**Source used: (b), the API the page itself reads** — the raw-HTML grep found nothing, which
`playbooks/observatory-api.md` §Featured match records as *unknown, not a failure* (the iframe is
client-rendered platform-wide since 2026-08-22).

```bash
curl -sS "https://softmax.com/hide-and-seek" | grep -o '<iframe[^>]*src="[^"]*"'
# -> (no output)  RAW-HTML GREP: no <iframe … src=> in the served HTML (698 KB, HTTP 200)

curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)[]
          |select(.name=="hide-and-seek")|{id,name,canonical,version,replay_viewer,featured_match}'
```
```json
{
  "id": "cow_ccb33c23-b885-414d-b46f-86a1ff4a0292",
  "name": "hide-and-seek",
  "canonical": true,
  "version": "0.1.2",
  "replay_viewer": null,
  "featured_match": null
}
```

`featured_match: null` on `/coworlds` is the documented platform-wide behaviour and is **not**
evidence of absence. The featured match is server-rendered into the page's SSR payload at
`state.playlist[0]`. Extracted from the page fetched at 02:40Z (escapes unwrapped, trimmed after
`outcome`):

```json
"playlist":[{"episodeId":"f74b6625-4796-42ce-9c0a-143c13c0a720",
  "coworldId":"cow_ccb33c23-b885-414d-b46f-86a1ff4a0292",
  "coworldName":"hide-and-seek","coworldVersion":"0.1.2",
  "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/2b8607e0-12fd-44fa-95f0-a7b7d1a3c03a.replay",
  "finishedAt":"2026-08-28T02:35:58.249314Z","roundNumber":3,"episodeNumber":1,
  "code":"hide-and-seek.r3.e1",
  "matchup":{"divisionId":"div_8ea628e9-769b-4aeb-a4a1-ed60092fea03","divisionName":"Competition",
    "first":{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
             "score":1030.5304984710244,"score_label":"MMR","rounds_played":2,"episode_wins":2,
             "win_rate":1,"policy_label":"hns-quartermaster:v3"},
    "second":{"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
              "score":969.4695015289755,"score_label":"MMR","rounds_played":2,"episode_wins":0,
              "win_rate":0,"policy_label":"hns-torchbearer:v3"}},
  "inspectUrl":"/observatory/v2?tab=overview&detail=episode-request:ereq_60c137bb-526b-42ec-a934-66496e4e9a41",
  "outcome":"first"}]
```

A featured match **is** present, it is round 3 episode 1, and it is a `daveey` vs `daveey-1` matchup.

The iframe `src` is the value returned by the call the page's own JS makes:

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" \
  -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_ccb33c23-b885-414d-b46f-86a1ff4a0292",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/2b8607e0-12fd-44fa-95f0-a7b7d1a3c03a.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_ccb33c23-b885-414d-b46f-86a1ff4a0292/sha256%3Ac7efab015aa7a543f0f97562e2045a5d03eef687e6b6004d8e210de05b42d3c2/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F2b8607e0-12fd-44fa-95f0-a7b7d1a3c03a.replay",
  "ready": true
}
```

- Path is `…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html` — the **static** route.
- `<sha>` is `sha256:c7efab015aa7a543f0f97562e2045a5d03eef687e6b6004d8e210de05b42d3c2`
  (URL-encoded), which is exactly `STATE.coworld.manifest_sha` — the manifest hash, as documented.
- `ready: true`, and the path ends in `/index.html` ⇒ static delivery.
- It is **not** a `/client/replay` pod URL.

Recorded variance: the platform now hands back the replay as `?v=2#replay=<url-encoded s3 url>` (a
cache-busting query plus a **hash** fragment) rather than the `?replay=<s3 url>` query the prompt
writes. The static path, the cow id and the manifest sha are all as required, and check 8 proves this
exact string loads and plays. Flagging the form change so the playbook can be updated.

Status: **TRUE** — featured match present (round 3, daveey vs daveey-1), and the iframe `src` is the
static `/v2/coworlds/replays/static/<cow_id>/<manifest_sha>/index.html` route with `ready: true`.

---

## 7. Certification declared the static bundle

Source read: **the committed `runs/2026-08-27-hide-and-seek/release-result.json`** — the artifact
phase 40 downloaded from release run `33134567408` and committed. It was already present; no
re-download was needed.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-27-hide-and-seek/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Surrounding context from the same file:

```bash
jq -r '{version, ok, cow_id, manifest_sha, canonical, hosted_smoke, hosted_certification,
        certify_ok: .certify.ok}' runs/2026-08-27-hide-and-seek/release-result.json
```
```json
{
  "version": "0.1.2",
  "ok": true,
  "cow_id": "cow_ccb33c23-b885-414d-b46f-86a1ff4a0292",
  "manifest_sha": "sha256:c7efab015aa7a543f0f97562e2045a5d03eef687e6b6004d8e210de05b42d3c2",
  "canonical": true,
  "hosted_smoke": "passed",
  "hosted_certification": "certified",
  "certify_ok": true
}
```

The `certify.output_tail` in that file also shows all ten transcript steps `[pass]` and
`Certified dist/coworld_manifest.json` / `Transcript: coworld-executable (10 steps passed)`, with the
same `Replay liveness: skipped (static replay bundle declared; …)` line.

Status: **TRUE** — the string `Replay liveness: skipped (static replay bundle declared` is present,
read from the committed `runs/2026-08-27-hide-and-seek/release-result.json`. The `cow_id` and
`manifest_sha` in that artifact are the same pair that appears in check 6's static viewer URL.

---

## 8. The viewer is EXECUTED, then judged

### (a) The dispatch

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_ccb33c23-b885-414d-b46f-86a1ff4a0292/sha256%3Ac7efab015aa7a543f0f97562e2045a5d03eef687e6b6004d8e210de05b42d3c2/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F2b8607e0-12fd-44fa-95f0-a7b7d1a3c03a.replay'
# dispatch_at = 2026-08-28T02:39:57Z
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
sleep 12
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml \
   --json databaseId,createdAt,status,event -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[]|[.databaseId,.createdAt,.status,.event]|@tsv'
```
```
33136591103	2026-08-28T02:39:59Z	in_progress	workflow_dispatch     <- created AFTER dispatch_at: this is the run
33135119698	2026-08-28T02:10:50Z	completed	workflow_dispatch
33119081304	2026-08-27T21:38:31Z	completed	workflow_dispatch
33114175789	2026-08-27T20:36:49Z	completed	workflow_dispatch
...
```

The new run was identified by `createdAt` (02:39:59Z) being after the dispatch (02:39:57Z), not by
taking "the latest run" blind.

```bash
gh run watch 33136591103 -R Metta-AI/coworld-builder --exit-status   # exit 0
gh run view  33136591103 -R Metta-AI/coworld-builder --json status,conclusion,createdAt,updatedAt
```
```json
{"conclusion":"success","createdAt":"2026-08-28T02:39:59Z","status":"completed","updatedAt":"2026-08-28T02:40:47Z"}
```

All steps green, including `Fail if the viewer did not load`. Artifact downloaded and committed:

```bash
gh run download 33136591103 -R Metta-AI/coworld-builder -n viewer-check \
  -D runs/2026-08-27-hide-and-seek/viewer-check
ls -l runs/2026-08-27-hide-and-seek/viewer-check/
```
```
-rw-r--r-- 1 root root      0 smoke-stderr.txt
-rw-r--r-- 1 root root    921 smoke-stdout.txt
-rw-r--r-- 1 root root   1717 viewer-smoke.json
-rw-r--r-- 1 root root 452983 viewer-smoke.png
```

### (b) The readouts

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-27-hide-and-seek/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":4759,"clock":"1:30 UNSEEN 0 · SEEN 0 · LOCKED 0 · SEALED 0 PREP 15S · TICK 947/2160 · TURN 1/12 · GAME 1/2","scorebug":"0 HIDERS UNSEEN 0 0 LOCKED · 0 SEALED 1:30 UNSEEN 0 · SEEN 0 · LOCKED 0 · SEALED 0 PREP 15S · TICK 947/2160 · TURN 1/12 · GAME 1/2 0 SEEKERS UNSEEN 0 0 LOCKED · 0 SEALED LOCKED 0 · SEALED 0/3 · RAMPS LOCKED 0/2","feed_lines":0}
```

```bash
jq -c '.signals' runs/2026-08-27-hide-and-seek/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/2026-08-27-hide-and-seek/viewer-check/viewer-smoke.json
# -> no failure          (the JSON field itself is null)
jq -c '.console_tail, .canvas_text' runs/2026-08-27-hide-and-seek/viewer-check/viewer-smoke.json
# -> []
# -> {"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
```

```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-27-hide-and-seek/viewer-check/viewer-smoke.json
```

| scrub | clock readout |
|---|---|
| **0 %** | `1:30 UNSEEN 0 · SEEN 0 · LOCKED 0 · SEALED 0 PREP 15S · TICK 947/2160 · TURN 1/12 · GAME 1/2` |
| **50 %** | `0:35 UNSEEN 0 · SEEN 0 · LOCKED 0 · SEALED 0 PREP 15S · TICK 2267/2160 · TURN 1/12 · GAME 2/2` |
| **100 %** | `FINAL GAME OVER HUNT 0S · TICK 3584/2160 · TURN 15/12 · GAME 2/2` |

The three readouts **differ** — tick 947 → 2267 → 3584, game 1/2 → 2/2 → 2/2, phase PREP → PREP →
FINAL/GAME OVER. The `#scrub` control exists (no `"(no #scrub…)"` marker); the shell was driven, not
merely opened.

`loaded: true` **and** the three clock readouts differ ⇒ both mandatory conditions hold.

### (c) The replay JSON the viewer was asked to draw

Early (`game turn slot alias source intent object at radio`):

```
1	0	0	HIDER-alpha	llm	push	box2		d1 west closet r1
1	0	2	HIDER-beta	scripted	move_to		p3	
1	0	4	HIDER-gamma	scripted	push	box1		
1	1	0	HIDER-alpha	llm	push	box2		d1 claimed, sealing now
1	2	0	HIDER-alpha	llm	lock	box2		Turn 2: box2 locked at d1. Gamma/Beta seal d3/d4. Next: push ramps to corner.
1	3	0	HIDER-alpha	llm	push	ramp1		d1 sealed/locked. Moving ramp1 to corner now.
1	4	0	HIDER-alpha	llm	lock	ramp1		Turn 4: ramp1 locked at corner. Moving to hide.
1	4	1	SEEKER-alpha	llm	watch			HIDER-beta at 266,270 south hall - holding position
```

Middle (the game-1 → game-2 side swap):

```
1	11	0	HIDER-alpha	llm	hide		p1	
1	11	1	SEEKER-alpha	llm	watch			Pressure north-east corner, visibility maintained
1	11	5	SEEKER-gamma	scripted	chase			
2	0	1	HIDER-alpha	llm	push	box2		Breaking north-south through n-hall
2	1	1	HIDER-alpha	llm	push	box2		Breaking north-south sightline with box2 at center
```

Late:

```
2	10	0	SEEKER-alpha	llm	watch			HIDER-alpha still at p1, holding sight
2	10	1	HIDER-alpha	llm	hide		p1	Seeker-alpha spotted me at 215,126. Moving to p1 behind box4. Will reposition based on seeker mo
2	11	0	SEEKER-alpha	llm	watch			HIDER-alpha pinned at [215,126]. Maintain lock.
2	11	1	HIDER-alpha	llm	hide		p1	SEEKER-alpha has direct LOS at 241,124. Retreating to p1 corner behind box4.
2	11	5	HIDER-gamma	scripted	move_to		p1	
```

```bash
# /tmp/ep.json is check 4's strict-JSON summary of /tmp/ep.replay. The full block is pasted
# verbatim in check 4; repeated here in abridged form so the readouts can be reconciled.
jq -r '.results | "reason \(.reason) endRule \(.endRule) games \(.games) room \(.room) finalTick \(.finalTick)"' /tmp/ep.json
jq -c '.results.scores, .results.gameMargins, .results.seatSeenTicks, .results.locks,
       .results.grabs, .results.vaults, .results.hiddenTicks, .results.seenTicks,
       .results.huntTicksPlayed' /tmp/ep.json
```
```
reason complete endRule full_time games 2 room warren finalTick 3587
[0.14,-0.14,0.14,-0.14,0.14,-0.14]
[-495,-775]
[0,640,457,33,240,0]
[0,4,0,0,0,0]
[0,3,0,0,0,0]
[0,0,0,0,0,0]
[182,81]
[539,640]
[721,721]
```

### Spectator judgment

`viewer-smoke.png` (committed at `runs/2026-08-27-hide-and-seek/viewer-check/viewer-smoke.png`, 1280×800,
taken after the scrubber was driven to 100 %) is **legible, populated, and it shows this game** — it
is not empty, not a "Loading replay…" hang, and not a single frozen frame.

What is on screen: a full-width scorebug across the top — `1490 UNSEEN HIDERS` in red on the left
with a `673` chip and `2 LOCKED · 0 SEALED` beneath it, `SEEKERS UNSEEN 1466` in blue on the right
with a `697` chip and `0 LOCKED · 0 SEALED`, and the run clock centred (dimmed behind the endcard, it
reads `HUNT 0S · TICK 3584/2160 · TURN 15/12 · GAME 2/2`). Behind everything is the rendered arena:
the "warren" room drawn in warm browns with crates, panels and ramps, plus a column of directive
chips down the right edge (`SEEKER-beta · MOVE_TO`, `HIDER-beta · MOVE_TO`, …) — the per-turn feed.
Over the top is the endcard: **FINAL / GAME OVER**, `EPISODE +0.140 / −0.140`, a highlighted verdict
banner `BOTH SIDES HIDDEN — EXPOSURE DECIDED`, and the sentence
`HIDERS UNSEEN 69% — MARGIN -775 · game 2/2 · episode -495 / -775 — full time.` Two boxout tables
break the result down by seat: HIDERS (`1490 TICKS UNSEEN`) listing **TORCHBEARER**/HIDER-alpha
81 unseen / 640 seen / 4 locks / 0 vaults, SCATTER/HIDER-beta 688/33/0/0, HIDER-gamma 721/0/0/0; and
SEEKERS (`1466 TICKS UNSEEN`) listing **QUARTERMASTER**/SEEKER-alpha 721/0/0/0, SCATTER/SEEKER-beta
264/457/0/0, BURROW/SEEKER-gamma 481/240/0/0. Along the bottom is the transport strip — restart,
step-back, play, `+5s`, step-forward, loop, fast-forward, a lit `spoilers` toggle, the frame counter
`2637 / 2640`, and speed chips `1× 2× 3× 4× 8× 16×` — over a scrubber whose track carries coloured
event ticks (red for hider beats, blue for seeker beats) and a **`HIDDEN LEAD` momentum graph** that
swells red early and flips solid blue through the back half.

It reconciles exactly with the record. `EPISODE +0.140 / −0.140` is `results.scores`
`[0.14,-0.14,…]`; `episode -495 / -775` is `results.gameMargins`; `full time` is
`results.endRule == "full_time"` and `results.reason == "complete"`; the per-seat SEEN column
(0, 640, 457, 33, 240, 0 across the two tables) is `results.seatSeenTicks` **digit for digit**;
`4` locks on HIDER-alpha is `results.locks == [0,4,0,0,0,0]`; and the momentum graph flipping from
red to blue is the two game margins (−495 then −775, both toward seekers) drawn as a curve. The
right-edge feed chips are the same `move_to` / `watch` / `hide` directives that appear in the late
excerpt above. The three scrub readouts confirm it **advances**: tick 947 in game 1 prep, tick 2267
in game 2, then the final tick 3584 with the endcard — a replay playing, not a screenshot.

**Chrome provenance — it is the starter's.** The transport strip (restart / step / play / `+5s` /
loop / fast-forward / `spoilers` toggle / `1×`–`16×` speed chips), the scrubber with event beats and
a lead-momentum curve under it, the two-sided scorebug and the tabular endcard are exactly the
chrome `coworld-ctf` ships in `client/chrome_common.js` — whose own header comment describes it as
"team identity/naming, the clock, the transport bar (buttons/speed chips/…) … momentum graph", whose
`+5s` button is `client/league_replayer.html:320` / `client/replay_broadcast.html:1560`, and whose
`spoilers` toggle is `chrome_common.js:99-113`. This is a **retarget, not a rewrite**: the labels are
hide-and-seek's (`HIDDEN LEAD`, `UNSEEN/SEEN/LOCKS/VAULTS`, `SEALED`, `RAMPS LOCKED`) sitting in the
starter's furniture. It is not the cogame-gridlock failure mode.

**Two legibility nits for the coordinator (non-blocking, phase-30 grade, not check failures):**
1. The tick counter prints an episode-global numerator against a per-game denominator, so it reads
   `TICK 2267/2160` and `TICK 3584/2160` — over 100 % — in games 2 of 2. Likewise `TURN 15/12`.
2. The `viewer-smoke.json` first-frame DOM readout (`clock` / `scorebug`) shows all counters at `0`
   and `feed_lines: 0`, because it is sampled at ~4.8 s while the shell is still in game 1's PREP
   phase; the screenshot taken later shows the populated scorebug (1490 / 1466) and a populated feed.
   Nothing is broken — the numbers arrive — but a spectator landing on the page sees an all-zero
   scorebug for the first few seconds.

Status: **TRUE** — `loaded: true` (`data_replay_loaded: "true"`, `ms: 4759`, `failure: null`, empty
`console_tail`) **and** the three clock readouts differ (tick 947 → 2267 → 3584, PREP → PREP →
FINAL), from `viewer-check.yml` run **33136591103** dispatched by this verifier at 02:39:57Z, with
the artifact committed at `runs/2026-08-27-hide-and-seek/viewer-check/`.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 2 (02:21:56Z) and 3 (02:36:03Z); round 1 failed pre-filler, error quoted |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey #1 / daveey-1 #2, `rounds_played` 2 each, only two rows |
| 3 | Latest round's episode request completed with a replay | **TRUE** — `ereq_60c137bb…` completed, replay_url set, both champions seated |
| 4 | Replay bytes valid and show the game | **TRUE** — strict JSON ok, `hide-and-seek/v1`, `complete`/`full_time`, 40 LLM decisions, 0 fallbacks |
| 5 | Hosted game log clean | **TRUE** — `CLEAN` on round 3 (round 2's single degrade recorded as an observation) |
| 6 | Public page uses the static replay path | **TRUE** — featured match r3.e1, static `/index.html` with `ready: true`, manifest sha matches |
| 7 | Certification declared the static bundle | **TRUE** — `Replay liveness: skipped (static replay bundle declared…` from committed `release-result.json` |
| 8 | Viewer executed and judged | **TRUE** — `loaded: true`, three differing clock readouts, starter chrome, endcard matches the replay |

Nothing was fetched that could not be fetched; there is no `NOT FETCHED` item. The 75-minute wall
clock bound (02:17Z → 03:32Z) was **not** reached; all evidence was in hand by 02:43Z.
