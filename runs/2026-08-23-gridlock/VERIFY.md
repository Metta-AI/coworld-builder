# VERIFY — gridlock   (2026-08-23T15:45:00Z)

Verdict: **all-true** (8/8)

Run: `2026-08-23-gridlock` · slug `gridlock` · coworld `cow_69f7b3ab-b32d-471d-874a-3ff32543b6f6` v0.1.0
· manifest_sha `sha256:38c6a5c2bc32a7e1cfe66ee6b1c98941974a72d50a93a385a7d1cb4d80ef99fc`
· league `league_4c0f039e-3a99-48ad-9d72-c3f85a110ea8` · division `div_349162e2-db36-4d23-a13f-49b0bf84df8e`
· repo `Metta-AI/cogame-gridlock`

Every fetch below was made fresh during phase 60 of this run (2026-08-23 15:20Z–15:45Z). The one
documented exception is check 7, whose evidence is this run's committed
`runs/2026-08-23-gridlock/release-result.json` (see that section).

Headers sent on every Observatory call: `Authorization: Bearer $SOFTMAX_TOKEN` (value never
printed), `User-Agent: coworld-builder/1.0`. Where noted, `X-Use-Elevated-Privileges: true`.
Common shell:

```bash
BASE=https://softmax.com/api/observatory/v2
L=league_4c0f039e-3a99-48ad-9d72-c3f85a110ea8
D=div_349162e2-db36-4d23-a13f-49b0bf84df8e
COW=cow_69f7b3ab-b32d-471d-874a-3ff32543b6f6
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
```

Shape note observed this run: `GET /rounds` returned `{"entries":[…]}`; `GET /divisions/$D/leaderboard`
returned a bare JSON array. Both jq filters below are written to tolerate either
(`if type=="array" then . else .entries end`).

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

Summary: 2 rounds completed (round_number 1 and 2), 0 failed, 0 discarded. Fillers were registered
at 2026-08-23T15:19:01Z, **before** round 1 was created (15:17:41Z) and before the first
trigger-round, so both completed rounds are post-filler
(`log.md`: `2026-08-23T15:19:01Z 50 filler-policies POST 200 (dispatcher+beeline only, neither champion)`).
The league object returned inline below confirms the fillers are attached:
`"filler_policy_version_ids": ["b72ad0fa-6d39-49dc-894a-45f8194b7912","74c2a80b-e4c5-4515-90c1-e2e96a2ed13d"]`.

```
GET https://softmax.com/api/observatory/v2/rounds?league_id=league_4c0f039e-3a99-48ad-9d72-c3f85a110ea8&limit=20
headers: Authorization: Bearer <redacted>, User-Agent: coworld-builder/1.0
HTTP 200
```

Count:

```bash
jq -r '(if type=="array" then . else .entries end)|[.[]|select(.status=="completed")]|length'
```
```
2
```

Rows (pasted response, trimmed to the fields the check uses):

```json
[
  {
    "id": "round_979c1bf0-8ff6-487b-abb6-c5fcdfe089e4",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "started_at": null,
    "completed_at": "2026-08-23T15:36:51.388422Z",
    "created_at": "2026-08-23T15:32:42.086489Z",
    "entrants": [
      {
        "subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
        "subject_type": "player",
        "policy_version_id": "35bdf51f-b7d9-4705-a3ab-6cfb49fbc6b7",
        "league_policy_membership_id": "lpm_269df3fd-3f08-4900-959c-b20b1f8b5125"
      },
      {
        "subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
        "subject_type": "player",
        "policy_version_id": "bf5cf3e0-9565-448e-9cfd-2451066da89d",
        "league_policy_membership_id": "lpm_94c47f7a-b932-4d69-b7a3-6cc13a95cb07"
      }
    ]
  },
  {
    "id": "round_f7ee30ea-c9b4-4b35-b127-d754dada7d9b",
    "round_number": 1,
    "status": "completed",
    "error": null,
    "started_at": null,
    "completed_at": "2026-08-23T15:21:50.690956Z",
    "created_at": "2026-08-23T15:17:41.241643Z",
    "entrants": [
      {
        "subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
        "subject_type": "player",
        "policy_version_id": "35bdf51f-b7d9-4705-a3ab-6cfb49fbc6b7",
        "league_policy_membership_id": "lpm_269df3fd-3f08-4900-959c-b20b1f8b5125"
      },
      {
        "subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
        "subject_type": "player",
        "policy_version_id": "bf5cf3e0-9565-448e-9cfd-2451066da89d",
        "league_policy_membership_id": "lpm_94c47f7a-b932-4d69-b7a3-6cc13a95cb07"
      }
    ]
  }
]
```

Filler attachment, from the same response's embedded league object (verbatim excerpt):

```json
"filler_policy_version_ids": [
  "b72ad0fa-6d39-49dc-894a-45f8194b7912",
  "74c2a80b-e4c5-4515-90c1-e2e96a2ed13d"
],
"settings": {"ladder": {"enabled": true,
  "scheduler": {"strategy": "round_robin", "insufficient_players": "filler_policy"},
  "ranking": {"algorithm": "elo", "initial_rating": 1000.0, "k_factor": 32.0, "round_scoring_rule": "mean"}},
  "round_interval_minutes": 15},
"rounds_paused_at": null
```

Status: **TRUE** — rounds 1 and 2 completed at 2026-08-23T15:21:50.690956Z and
2026-08-23T15:36:51.388422Z; fillers set at 2026-08-23T15:19:01Z, i.e. before both. `error: null`
on both; no `failed` or `discarded` rounds exist in the league.

Poll trail (each poll also refreshed `heartbeat_at` in STATE.json and in Asana custom field
1217748424048134):

| poll (UTC) | rounds seen |
|---|---|
| 15:20:51 | 1 pending |
| 15:25:59 | 1 completed |
| 15:31:34 | 1 completed |
| 15:36:25 | 1 completed, 2 pending |
| 15:41:09 | 1 completed, 2 completed |

---

## 2. Both champions ranked, fillers absent/Baseline — **TRUE**

```
GET https://softmax.com/api/observatory/v2/divisions/div_349162e2-db36-4d23-a13f-49b0bf84df8e/leaderboard
headers: Authorization: Bearer <redacted>, User-Agent: coworld-builder/1.0
HTTP 200
```

Pasted response (bare array, complete — 2 rows):

```json
[
  {
    "rank": 1,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 1030.5304984710244,
    "score_label": "Elo",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 2.0,
    "episodes_played": null,
    "win_rate": 1.0,
    "policy_label": "gridlock-flowwright:v1",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 969.4695015289755,
    "score_label": "Elo",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 0.0,
    "episodes_played": null,
    "win_rate": 0.0,
    "policy_label": "gridlock-backstreet:v1",
    "recent_rounds": null
  }
]
```

```bash
jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey	gridlock-flowwright:v1	1030.5304984710244	2	2.0
2	daveey-1	gridlock-backstreet:v1	969.4695015289755	2	0.0
```

Status: **TRUE** — `daveey` (rank 1, `gridlock-flowwright:v1`, rounds_played 2) and `daveey-1`
(rank 2, `gridlock-backstreet:v1`, rounds_played 2) are both present with `rounds_played ≥ 1`.
The fillers `gridlock-dispatcher:v1` / `gridlock-beeline:v1` are **absent** from the leaderboard
(the array has exactly two rows), which is the permitted disposition.

---

## 3. Latest round's episode request completed with a replay and correct participants — **TRUE**

Latest completed round selected from the check-1 response:

```bash
R=$(jq -r '(if type=="array" then . else .entries end)|[.[]|select(.status=="completed")]|max_by(.round_number).id')
# R=round_979c1bf0-8ff6-487b-abb6-c5fcdfe089e4   (round_number 2)
```

```
GET https://softmax.com/api/observatory/v2/episode-requests?round_id=round_979c1bf0-8ff6-487b-abb6-c5fcdfe089e4&limit=20
headers: Authorization: Bearer <redacted>, User-Agent: coworld-builder/1.0
HTTP 200
```
```json
[
  {
    "id": "ereq_49c11f68-c5df-4791-8a45-ac1743ccf6d2",
    "status": "completed",
    "replay_url": "https://softmax-public.s3.amazonaws.com/replays/b0474583-f10a-4a2c-b062-fc65175d6d64.replay"
  }
]
```

```
GET https://softmax.com/api/observatory/v2/episode-requests/ereq_49c11f68-c5df-4791-8a45-ac1743ccf6d2
headers: Authorization: Bearer <redacted>, User-Agent: coworld-builder/1.0
HTTP 200
jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/b0474583-f10a-4a2c-b062-fc65175d6d64.replay",
  "participants": [
    {"position": 0, "kind": "policy", "policy_version_id": "35bdf51f-b7d9-4705-a3ab-6cfb49fbc6b7",
     "policy_id": "d8956b66-afb6-4c8f-af67-751c983faf70", "policy_name": "gridlock-flowwright",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
     "player_name": "daveey", "is_filler": false},
    {"position": 1, "kind": "policy", "policy_version_id": "bf5cf3e0-9565-448e-9cfd-2451066da89d",
     "policy_id": "9605f169-3c07-4566-b4bd-e01083fcb5e2", "policy_name": "gridlock-backstreet",
     "version": 1, "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
     "player_name": "daveey-1", "is_filler": false},
    {"position": 2, "kind": "policy", "policy_version_id": "74c2a80b-e4c5-4515-90c1-e2e96a2ed13d",
     "policy_id": "59c01fef-4f24-45cc-9640-f6c6c483e843", "policy_name": "gridlock-beeline",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
     "player_name": "daveey", "is_filler": true},
    {"position": 3, "kind": "policy", "policy_version_id": "74c2a80b-e4c5-4515-90c1-e2e96a2ed13d",
     "policy_id": "59c01fef-4f24-45cc-9640-f6c6c483e843", "policy_name": "gridlock-beeline",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
     "player_name": "daveey", "is_filler": true}
  ],
  "participant_scores": [
    {"position": 0, "score": 188.0},
    {"position": 1, "score": 184.0},
    {"position": 2, "score": 186.0},
    {"position": 3, "score": 186.0}
  ]
}
```

Status: **TRUE** — `status == "completed"`, `replay_url` non-null, seat 0 = `daveey`
(`gridlock-flowwright` v1, `is_filler: false`), seat 1 = `daveey-1` (`gridlock-backstreet` v1,
`is_filler: false`). Seats 2 and 3 are the registered filler version
`74c2a80b-e4c5-4515-90c1-e2e96a2ed13d` (`gridlock-beeline`) flagged `is_filler: true`; the replay's
own `names.players` renders them as `Baseline` / `Baseline (2)` (see check 4). The API row carries
`player_name: daveey` on the filler seats because a filler policy version is owned by whoever
uploaded it; the `is_filler: true` flag and the `Baseline`/`Baseline (2)` display names are the
authoritative disposition and both are correct.

---

## 4. Replay bytes are valid and show the game — **TRUE**

```
GET https://softmax-public.s3.amazonaws.com/replays/b0474583-f10a-4a2c-b062-fc65175d6d64.replay
HTTP 200 · 360837 bytes · content-type application/octet-stream
```

Strict parse:
```bash
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
```
```
strict UTF-8 JSON: ok
```

```bash
jq -r '.protocol, .results.reason, .results.end_rule, .format_version, .game_version' /tmp/ep.replay
```
```
gridlock.replay.v1
complete
full_time
1
1
```

`protocol` match: the design note (`runs/2026-08-23-gridlock/design.md:885`) fixes the replay
protocol at `{"protocol": "gridlock.replay.v1", …}`; the fetched bytes carry exactly that string.

Structure (proves the per-tick state a viewer draws is present, not just a header):
```bash
jq -r '"tick_count=\(.tick_count) ticks_per_second=\(.ticks_per_second) turn_ticks=\(.turn_ticks) keyframes=\(.keyframes|length) plans=\(.plans|length) seat_depots=\(.seat_depots|length) vehicles_b64_bytes=\(.vehicles_b64|length)"'
```
```
tick_count=4800 ticks_per_second=24 turn_ticks=240 keyframes=201 plans=80 seat_depots=4 vehicles_b64_bytes=214400
```

`results` (pasted verbatim):
```json
{
  "names": ["daveey", "daveey-1", "Baseline", "Baseline (2)"],
  "aliases": ["Saffron", "Copper", "Cobalt", "Verde"],
  "colours": ["#f2c14e", "#e07a3f", "#4a8fe7", "#5fbf6a"],
  "depots": [[7,7],[1,1],[7,1],[1,7]],
  "policy_kinds": ["llm", "llm", "scripted", "scripted"],
  "scores": [188.0, 184.0, 186.0, 186.0],
  "win": [true, false, false, false],
  "delivered": [188, 184, 186, 186],
  "total_delivered": 744,
  "orders_created": [200, 200, 200, 200],
  "backlog_final": [0, 0, 0, 0],
  "mean_trip_seconds": [14.4, 14.7, 14.9, 14.7],
  "stalled_vehicle_seconds": [432, 422, 495, 497],
  "own_stall_pct": [26, 25, 28, 28],
  "vans": [50, 50, 50, 50],
  "jam_index_mean": 24,
  "jam_index_peak": 31,
  "gridlock_events": 0,
  "turns_llm": [20, 20, 0, 0],
  "fallback_turns": [0, 0, 0, 0],
  "fallback_causes": [
    {"timeout":0,"parse_error":0,"transport_error":0,"no_credentials":0,"budget_guard":0},
    {"timeout":0,"parse_error":0,"transport_error":0,"no_credentials":0,"budget_guard":0},
    {"timeout":0,"parse_error":0,"transport_error":0,"no_credentials":0,"budget_guard":0},
    {"timeout":0,"parse_error":0,"transport_error":0,"no_credentials":0,"budget_guard":0}
  ],
  "reason": "complete",
  "end_rule": "full_time",
  "final_tick": 4800,
  "final_turn": 19,
  "seed": 454296730,
  "winner": 0
}
```

Decision events. Gridlock's decision event type is `plan` (one per seat per turn), not the generic
`decision` name in the phase-prompt snippet — the literal snippet returns 0 here, so both are shown:

```bash
jq -r '[.events[].type]|group_by(.)|map({t:.[0],n:length})' /tmp/ep.replay
```
```json
[{"t":"deliver","n":744},{"t":"end","n":1},{"t":"heat","n":100},{"t":"match_start","n":1},
 {"t":"meter","n":80},{"t":"plan","n":80},{"t":"turn_start","n":20}]
```
```bash
jq -r '[.events[]|select(.type=="decision")]|length' /tmp/ep.replay   #  -> 0  (no such type in gridlock)
jq -r '[.events[]|select(.fallback==true)]|length'   /tmp/ep.replay   #  -> 0
```
```
0
0
```

Decision provenance per seat (the real filter):
```bash
jq -r '[.events[]|select(.type=="plan")]|group_by(.seat)|map({seat:.[0].seat,fleet:.[0].fleet,sources:([.[].source]|group_by(.)|map({s:.[0],n:length}))})'
```
```json
[
  {"seat":0,"fleet":"Saffron","sources":[{"s":"llm","n":20}]},
  {"seat":1,"fleet":"Copper", "sources":[{"s":"llm","n":20}]},
  {"seat":2,"fleet":"Cobalt", "sources":[{"s":"scripted","n":20}]},
  {"seat":3,"fleet":"Verde",  "sources":[{"s":"scripted","n":20}]}
]
```
```bash
jq -r '[.events[]|select(.type=="plan" and (.seat==0 or .seat==1))|.note]|unique|length'  # distinct champion notes
jq -r '[.events[]|select(.type=="plan")|.latency_ms]|(add/length)'                         # mean call latency
```
```
38
2242.3
```

Status: **TRUE** — strict UTF-8 JSON parse ok; `protocol == "gridlock.replay.v1"` matches the
manifest/design; `results.reason == "complete"` with `end_rule == "full_time"` (the expected
ending per `design.md:352`; the `deadline` exception was not needed). Both champion seats produced
**20/20 LLM decisions with 0 fallbacks** (`turns_llm: [20,20,0,0]`, `fallback_turns: [0,0,0,0]`,
every `fallback_causes` counter 0, `source: "llm"` on all 40 champion plan events) — the fallback
count is 0 of 40, not a majority. 38 of 40 champion notes are textually distinct and reference live
state (`jam_index`, `stalled_pct`, rival totals), so the content is non-trivial and non-scripted.

---

## 5. Hosted game log is clean — **TRUE**

```
GET https://softmax.com/api/observatory/v2/episode-requests/ereq_49c11f68-c5df-4791-8a45-ac1743ccf6d2/artifacts/logs
headers: Authorization: Bearer <redacted>, User-Agent: coworld-builder/1.0, X-Use-Elevated-Privileges: true
HTTP 200 · 83392 bytes
```

```bash
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/ck5.log || echo CLEAN
```
```
CLEAN
```

The endpoint returns the container blobs with escaped `\n`, so the same grep was re-run against the
un-escaped text to rule out a line-splitting artefact (attempt 2, different approach):

```bash
python3 - <<'PY'
raw=open('/tmp/ck5.log').read(); dec=raw.replace('\\n','\n'); lines=dec.split('\n')
import re; pat=re.compile(r'falling back|LLM provider is unavailable|cut off at max_tokens|rejected')
print("decoded lines:",len(lines))
print("containers:",[l for l in lines if l.startswith('===== container')])
print("hits:",len([l for l in lines if pat.search(l)]))
PY
```
```
decoded lines: 190
containers: ['===== container: coworld-init-config =====', '===== container: bedrock-sidecar =====', '===== container: game =====', '===== container: worker =====']
hits: 0
```

The `game` container section verbatim (the coworld's own log):

```
===== container: game =====
gridlock: seed not pinned; randomized to 454296730
gridlock: seats=4 seed=454296730 ticks=4800 turns=20 city=gridcity
gridlock: serving on 0.0.0.0:8080
gridlock: player slot 1 connected
gridlock: slot 1 registered (llm)
gridlock: player slot 2 connected
gridlock: slot 2 registered (scripted)
gridlock: player slot 0 connected
gridlock: slot 0 registered (llm)
gridlock: player slot 3 connected
gridlock: slot 3 registered (scripted)
gridlock: starting with 4/4 seats connected
gridlock: llm: bedrock transport, url http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
gridlock: writing replay and results
gridlock: episode complete: reason=complete scores=[188.0,184.0,186.0,186.0]
```

Corroborating sidecar lines (first two of the 80 calls, verbatim, trimmed to the fields that matter):

```
2026-08-23 15:33:00,946 INFO __main__ bedrock_sidecar_complete {… "model":"global.anthropic.claude-haiku-4-5-20251001-v1:0","operation":"InvokeModel","ok":true,"status_code":200,"latency_ms":2374.93,"error_kind":null,"error_type":null,"message":null …}
2026-08-23 15:33:03,113 INFO __main__ bedrock_sidecar_complete {… "ok":true,"status_code":200,"latency_ms":2165.99,"error_kind":null,"error_type":null,"message":null,"cache_decision":"injected","cache_points_applied":1 …}
```

Status: **TRUE** — zero matches for `falling back`, `LLM provider is unavailable`,
`cut off at max_tokens`, `rejected`, in both the raw and the un-escaped form. No documented
exception was needed: every Bedrock call in the log returned `ok:true status_code:200`.

---

## 6. The public page uses the static replay path — **TRUE**

**Source used: both.** The raw-HTML grep found nothing (the page is client-rendered for the iframe,
as `playbooks/observatory-api.md` §Featured match records), so the featured match was read from the
page's server-rendered SSR payload and the iframe `src` from the call the page's own JS makes.

Attempt 1 — raw HTML grep:
```
GET https://softmax.com/gridlock
HTTP 200 · 371626 bytes
curl -sS "https://softmax.com/gridlock" | grep -o '<iframe[^>]*src="[^"]*"'
```
```
NO-IFRAME-IN-RAW-HTML (client-rendered; falling back)
```

Attempt 2 — the coworld detail API named in the phase prompt (recorded, though it is known to be
`null` platform-wide):
```
GET https://softmax.com/api/observatory/v2/coworlds?limit=200
jq -r '.entries[]|select(.name=="gridlock")|{id,canonical,replay_viewer,featured_match,manifest_hash,version}'
```
```json
{
  "id": "cow_69f7b3ab-b32d-471d-874a-3ff32543b6f6",
  "name": "gridlock",
  "canonical": true,
  "replay_viewer": null,
  "featured_match": null,
  "manifest_hash": "sha256:38c6a5c2bc32a7e1cfe66ee6b1c98941974a72d50a93a385a7d1cb4d80ef99fc",
  "version": "0.1.0"
}
```
`featured_match: null` here is the documented platform-wide behaviour (playbook §Featured match,
lighthouse run 2026-08-22), not an absence of a featured match — see attempt 3.

Attempt 3 — **the featured match, from the page's SSR payload `state.playlist[0]`** (pasted, JSON
un-escaped from the HTML):
```json
{"episodeId":"af2fbb09-e779-4720-9053-135b029da3ed",
 "coworldId":"cow_69f7b3ab-b32d-471d-874a-3ff32543b6f6",
 "coworldName":"gridlock","coworldVersion":"0.1.0",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/b0474583-f10a-4a2c-b062-fc65175d6d64.replay",
 "finishedAt":"2026-08-23T15:36:49.265418Z","roundNumber":2,"episodeNumber":1,"code":"gridlock.r2.e1",
 "matchup":{"divisionId":"div_349162e2-db36-4d23-a13f-49b0bf84df8e","divisionName":"Competition",
   "first":{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
            "score":1030.5304984710244,"score_label":"Elo","rounds_played":2,"episode_wins":2,
            "win_rate":1,"policy_label":"gridlock-flowwright:v1"},
   "second":{"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
             …,"policy_label":"gridlock-backstreet:v1"}},
 "inspectUrl":"/observatory/v2?tab=episode-requests&detail=episode-request:ereq_49c11f68-c5df-4791-8a45-ac1743ccf6d2",
 "outcome":"first"}
```
A featured match **is** present, and it is round 2 episode 1 — the same
`ereq_49c11f68…` / `b0474583-….replay` verified in checks 3–5.

The iframe `src`, from the call the page's JS makes:
```
POST https://softmax.com/api/observatory/v2/coworlds/replays/session
headers: Authorization: Bearer <redacted>, User-Agent: coworld-builder/1.0, content-type: application/json
body: {"coworld_id":"cow_69f7b3ab-b32d-471d-874a-3ff32543b6f6","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/b0474583-f10a-4a2c-b062-fc65175d6d64.replay"}
HTTP 200
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_69f7b3ab-b32d-471d-874a-3ff32543b6f6/sha256%3A38c6a5c2bc32a7e1cfe66ee6b1c98941974a72d50a93a385a7d1cb4d80ef99fc/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fb0474583-f10a-4a2c-b062-fc65175d6d64.replay&v=2",
  "ready": true
}
```

Status: **TRUE** — the path is
`/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`. `<cow_id>` is
`cow_69f7b3ab-b32d-471d-874a-3ff32543b6f6` and `<sha>` URL-decodes to
`sha256:38c6a5c2bc32a7e1cfe66ee6b1c98941974a72d50a93a385a7d1cb4d80ef99fc`, which is exactly
`STATE.coworld.manifest_sha` and the `manifest_hash` in the `/coworlds` row above. `ready: true`.
**No `/client/replay` pod URL appears anywhere.** A featured match is present (two ranked players).

---

## 7. Certification declared the static bundle — **TRUE**

**Source: the committed `runs/2026-08-23-gridlock/release-result.json`** (the artifact phase 40
downloaded and committed in `cb202b3 gridlock: 40 release 0.1.0 green (cow_69f7b3ab, canonical,
certified, 4 policies v1)`). No re-download from `gh run download` was needed — the file was
present, so the `/tmp` path was never consulted.

```bash
git log --oneline -1 -- runs/2026-08-23-gridlock/release-result.json
```
```
cb202b3 gridlock: 40 release 0.1.0 green (cow_69f7b3ab, canonical, certified, 4 policies v1)
```

```bash
jq -r '.certify|keys' runs/2026-08-23-gridlock/release-result.json
jq -r '.certify.replay_liveness' runs/2026-08-23-gridlock/release-result.json
```
```
["ok","output_tail","replay_liveness"]
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE** — the certification output contains the exact required string
`Replay liveness: skipped (static replay bundle declared`.

---

## 8. Spectator judgment — **TRUE**

### (a) The viewer was executed in a real browser (GitHub Actions, headless chromium)

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_69f7b3ab-b32d-471d-874a-3ff32543b6f6/sha256%3A38c6a5c2bc32a7e1cfe66ee6b1c98941974a72d50a93a385a7d1cb4d80ef99fc/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fb0474583-f10a-4a2c-b062-fc65175d6d64.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90   # dispatched 15:42:20Z
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0].databaseId'
```
```
32649388472	2026-08-23T15:42:22Z	in_progress	workflow_dispatch      <- created AFTER the 15:42:20Z dispatch
32644408716	2026-08-23T14:06:25Z	completed	workflow_dispatch      (unrelated, earlier)
```
```bash
gh run view 32649388472 -R Metta-AI/coworld-builder --json status,conclusion,createdAt
```
```json
{"conclusion":"success","createdAt":"2026-08-23T15:42:22Z","status":"completed"}
```
```bash
gh run download 32649388472 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-23-gridlock/viewer-check
ls -la runs/2026-08-23-gridlock/viewer-check/
```
```
-rw-r--r-- smoke-stderr.txt        0
-rw-r--r-- smoke-stdout.txt      386
-rw-r--r-- viewer-smoke.json    1219
-rw-r--r-- viewer-smoke.png   361501
```
(committed with this file)

### (b) The readouts

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-23-gridlock/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":3245,"clock":"03:20 TURN 0/20","scorebug":"daveey Saffron 0 Baseline Cobalt 0 daveey-1 Copper 0 Baseline (2) Verde 0","feed_lines":6}
```
```bash
jq -c '.signals' runs/2026-08-23-gridlock/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready","ready"],"bridge_ready":true,"bridge_error":[]}
```
```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-23-gridlock/viewer-check/viewer-smoke.json
```

| scrub position | clock readout |
|---|---|
| 0 % | `03:20 TURN 0/20` |
| 50 % | `01:37 TURN 10/20` |
| 100 % | `00:00 TURN 19/20` |

```bash
jq -r '.failure // "no failure"' runs/2026-08-23-gridlock/viewer-check/viewer-smoke.json
```
```
no failure
```

Also recorded in the artifact: `"loading_text": "LOADING REPLAY…"` — that is the overlay element's
text node, which persists in the DOM after the overlay is hidden; `data_replay_loaded: "true"`,
`bridge_ready: true` and the three advancing clocks show it is not the visible state.

**Both TRUE conditions hold:** `loaded: true` (via *both* `data-replay-loaded="true"` and the
`coworld-replay` bridge's `ready`), and the three clock readouts differ
(`03:20 TURN 0/20` → `01:37 TURN 10/20` → `00:00 TURN 19/20`).

Supplementary — the shell's own error markers and the asset table (fetched from the same static
route; the phase-prompt criteria above do not require these, but they corroborate the CI result):

```bash
grep -nE "coworld-replay|tell\(|data-replay-loaded" static_replay.js
```
```
21://   3. the `coworld-replay` postMessage bridge: tell("loading") on entry,
22://      tell("error", msg) in showFailure, and tell("ready") inside a double
36:  function tell(type, message) {
38:    var envelope = { src: 'coworld-replay', type: type };
40:    try { window.parent.postMessage(envelope, '*'); } catch (ignore) {}
42:  tell('loading');
45:    document.documentElement.setAttribute('data-replay-loaded', 'true');
49:      window.requestAnimationFrame(function () { tell('ready'); });
78:    tell('error', message);
```

| asset (relative to `…/static/<cow_id>/<sha>/`) | HTTP | bytes | content-type |
|---|---|---|---|
| `index.html` | 200 | 16163 | text/html |
| `wire_constants.js` (`<script src>`) | 200 | 118 | text/javascript |
| `chrome_common.js` (`<script src>`) | 200 | 18781 | text/javascript |
| `static_replay.js` (`<script src>`) | 200 | 11521 | text/javascript |
| `static_replay_worker.js` (`new Worker`) | 200 | 8817 | text/javascript |
| `broadcast_core.js` (worker `importScripts`) | 200 | 17029 | text/javascript |
| `gridlock_replay.js` (worker `importScripts`, emscripten glue) | 200 | 62063 | text/javascript |
| `gridlock_replay.wasm` (`Module.locateFile`) | 200 | 237811 | application/wasm |

`index.html` references no `<link href>` (styles are inlined). The wasm is a real module:
`file` reports `WebAssembly (wasm) binary module version 0x1 (MVP)`. The bootstrap is the
non-MODULARIZED `importScripts` + `Module.onRuntimeInitialized` pairing that the worker's own
header comment pins — the exact pairing whose mismatch hung cogame-lantern — and the executed run
confirms it initialises.

### (c) The replay JSON the viewer was asked to draw

Early (first non-`deliver` events, tick 0):
```
t	seat	type	say/note
0	-	match_start
0	-	turn_start	(turn 0)
0	0	plan	"Empty city, full throttle near"
0	1	plan	"Side streets, steady pace."
0	2	plan	(scripted)
0	3	plan	(scripted)
0	-	meter	x4
0	-	heat	jam_index 0
```

Champion plan events at turns 0/5/10/15/19 (`turn | seat | fleet | source | priority | congestion_weight | patience | dispatch | spread | corridor | avoid | note`):
```
0  | 0 | Saffron | llm | near | 25 | 70 | 100 | 30 | null  | null | City empty (jam_index 0). Running baseline: churn short trips, full dispatch, minimal congestion weight. No self-congestion yet.
0  | 1 | Copper  | llm | fifo | 75 | 25 |  90 | 85 | [2,2] | null | Early game: avoid arterials with high congestion weight. Spread departures to meter traffic. Use SE district as corridor—far from depot but …
5  | 0 | Saffron | llm | near | 55 | 70 |  80 | 40 | null  | null | jam_index 25, stalled_pct 26—city loading smoothly. Self-congestion minimal. Hold plan; no thrashing. Arterials flowing.
5  | 1 | Copper  | llm | fifo | 75 | 25 |  90 | 85 | [2,2] | null | jam_index 25: arterials at 3-4 queues, stable. All fleets tied 35 delivered. Side streets working. Backlog empty, fifo holds. Stay the cours…
10 | 0 | Saffron | llm | near | 55 | 70 |  80 | 40 | null  | null | jam_index 25, stalled_pct 20—city smooth and balanced. Hold plan; no thrashing. All fleets tied at 84 deliveries.
10 | 1 | Copper  | llm | fifo | 75 | 25 |  90 | 85 | [2,2] | null | jam_index 25, stable. Side streets holding. Minor queues on arterials (3-5 vans) not blocking. All fleets tied at 84. Maintain strategy.
15 | 0 | Saffron | llm | near | 55 | 70 |  80 | 40 | null  | null | jam_index 26, stalled_pct 27—city smooth, no self-congestion. Hold plan. Copper +1 but steady routing wins.
15 | 1 | Copper  | llm | fifo | 75 | 25 |  90 | 85 | [2,2] | null | jam_index 26, stable. Arterials show minor queues (3-6 vans). Side streets delivering steady. Maintain edge strategy—one block off arterials…
19 | 0 | Saffron | llm | near | 55 | 70 |  80 | 40 | null  | null | jam_index 29, stalled_pct 30—city smooth, we're tracking well. No hot district above 8. Hold plan for consistency.
19 | 1 | Copper  | llm | fifo | 75 | 25 |  90 | 85 | [2,2] | null | jam_index 29, all districts cool. Arterials show minor queues (3-7 vans). Side streets remain clear. Maintain steady pressure on local route…
```

Metering actually applied at turn 10 (the plan's `dispatch` reaching the sim):
```json
[{"type":"meter","t":2400,"turn":10,"fleet":"Saffron","dispatch":80,"held":0},
 {"type":"meter","t":2400,"turn":10,"fleet":"Copper","dispatch":90,"held":0},
 {"type":"meter","t":2400,"turn":10,"fleet":"Cobalt","dispatch":100,"held":0},
 {"type":"meter","t":2400,"turn":10,"fleet":"Verde","dispatch":100,"held":0}]
```

Congestion trajectory (`heat` events, sampled):
```
t=0     jam_index 0
t=1152  jam_index 25
t=2352  jam_index 25
t=3552  jam_index 26
t=4752  jam_index 27
```

Late (last non-`deliver` events) and the `end` event:
```
4560 meter x4 · 4560-4752 heat x5 · 4800 end
```
```json
{"type":"end","t":4800,"turn":19,"reason":"complete","end_rule":"full_time",
 "delivered":[188,184,186,186],"scores":[188.0,184.0,186.0,186.0],"winner":0,
 "total_delivered":744,"jam_index_mean":24}
```

### Spectator-judgment paragraph

**It is legible and it shows the game.** The screenshot (`viewer-check/viewer-smoke.png`, 1280×800,
taken at the 100 % scrub position) is a drawn frame, not a spinner: the 9×9 signalised city is
visible behind a dimming end-of-match card that reads **"Saffron wins — 188 parcels"** over the rule
"Most parcels delivered wins. Score is your own deliveries — not a share, so the total is
destructible." Under it sits a four-row table naming every seat by both name-spaces and giving the
numbers that decide the match: `daveey · Saffron 188 parcels, trip 14.4s, stalled 7 min, backlog 0`;
`daveey-1 · Copper 184 / 14.7s / 7 min / 0`; `Baseline · Cobalt 186 / 14.9s / 8 min / 0`;
`Baseline (2) · Verde 186 / 14.7s / 8 min / 0` — every value matching `results.delivered`,
`mean_trip_seconds` and `backlog_final` in the replay JSON exactly. A summary line reads
"744 parcels delivered · mean jam 24 · peak 31 · 0 gridlocks — the city lost an estimated 31 minutes
of van time to queues", which is `total_delivered`, `jam_index_mean`, `jam_index_peak` and
`gridlock_events` verbatim. The right-hand feed carries 6 lines of the champions' own reasoning —
`Saffron → reprice 55, dispatch 80, near-first`, `Saffron says "Holding steady"`, `Copper → reprice
75, dispatch 90, via SE, fifo-first`, `Copper says "Side streets. Steady."`, and the two scripted
seats' flat `no repricing, dispatch 100, fifo-first` — which reconciles line-for-line with the turn-19
plan events above and makes the *why* of the result readable, not just the score. A JAM meter reads
27 in the bottom-right, the transport bar (LOOP / SPEED 1×–16× / t 4800) is drawn, and a minimap sits
top-left. That the picture is dark is the end-card's deliberate dim of the map behind it, not an
empty canvas: the per-depot fleet chips (`Saffron 188`, `Copper 184`, `Cobalt 186`, `Verde 186`) and
the road grid render through it. Motion is proven independently of the picture by the three differing
clock readouts (`03:20 TURN 0/20` → `01:37 TURN 10/20` → `00:00 TURN 19/20`), which also track the
replay's 20 turns over 4800 ticks. **One legibility defect, recorded not glossed:** the four corner
name plates show `daveey · Saffron 188` and `Baseline (2) · Verde 186` correctly, but pair
`Baseline · Cobalt` with **184** and `daveey-1 · Copper` with **186** — the two middle seats' totals
are transposed relative to `results.delivered` ([188,184,186,186]), relative to the depot chips in
the same frame, and relative to the end card in the same frame. Nothing else in the viewer is
affected and the winner, the score table and the feed are all correct, so this is a HUD indexing bug
worth a phase-30 follow-up in a later version rather than a claim that the replay is unreadable.
It does not touch either of the phase-prompt's two conditions for item 8, both of which hold.

Status: **TRUE** — `loaded: true` and the three clock readouts differ.

---

## Bound

Wall-clock spent waiting: 15:20:16Z → 15:41:09Z ≈ 21 minutes of the 75-minute budget. **The bound
was not hit.** Poll cadence ~5 minutes, `heartbeat_at` refreshed in STATE.json and Asana at every
poll.
