# VERIFY — battlecode-2017   (2026-09-11T09:05Z)

Verdict: **all-true** — all eight checks TRUE.

Scope: coworld `battlecode` version **0.11.2**
(`cow_7c4f0e60-3dd5-4de2-ba2c-441dad1b4de2`, manifest
`sha256:4d5c5bced3b461c9baf31db9cea951ac6a9198234f37555879edeac04a492fd5`), league
`league_848b5159-1986-4442-ac18-575ef5c6c7c6` (short name `bc17`), division
`div_943b6ac3-c635-4473-9224-1363214931c9`. Champions: `daveey` /
`battlecode-bc17-orchard:v4` (policy-version `77b3fb34-7127-40bc-aef6-15434365d2aa`) and
`daveey-1` / `battlecode-bc17-tankrush:v4` (policy-version
`db6f8128-382f-43f6-b2c3-88977be8f2fb`). Fillers `battlecode-orchard:v4`
(`273ab424-8a8a-4970-9bf7-f75e38384cba`) and `battlecode-examplefuncsplayer17:v4`
(`ac407f68-2343-48c8-aad4-9ab663ffb5ce`), both scripted. All curl calls use
`-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0"`
(and `-H "X-Use-Elevated-Privileges: true"` where noted); header names shown, values never
printed. Fetched fresh this run at 2026-09-11T09:01–09:05Z.

---

## 1. ≥2 completed rounds after fillers were set

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}"
```
```json
{
  "entries": [
    {
      "id": "round_ae081c35-154f-4d7b-b44f-0b6c767b8d61",
      "round_number": 2,
      "status": "completed",
      "scheduled_by": "ladder",
      "error": null,
      "completed_at": "2026-09-11T09:00:09.706399Z",
      "created_at": "2026-09-11T08:56:54.878657Z",
      "round_config": {
        "entrant_policy_version_ids": [
          "77b3fb34-7127-40bc-aef6-15434365d2aa",
          "db6f8128-382f-43f6-b2c3-88977be8f2fb"
        ]
      }
    },
    {
      "id": "round_4c4f8ffa-cad7-4a34-ad96-c23842a01193",
      "round_number": 1,
      "status": "completed",
      "scheduled_by": "ladder",
      "error": null,
      "completed_at": "2026-09-11T08:52:53.850836Z",
      "created_at": "2026-09-11T08:50:10.183612Z",
      "round_config": {
        "entrant_policy_version_ids": [
          "77b3fb34-7127-40bc-aef6-15434365d2aa",
          "db6f8128-382f-43f6-b2c3-88977be8f2fb"
        ]
      }
    }
  ],
  "next_cursor": null
}
```
```bash
jq -r '[.entries[]|select(.status=="completed")]|length'
# -> 2
```
Two completed rounds exist, `round_number` 1 (`round_4c4f8ffa`, completed 08:52:53Z) and 2
(`round_ae081c35`, completed 09:00:09Z), both `error: null`, no failed/discarded rounds.
Per `log.md`: fillers were registered at `2026-09-11T08:50:00Z` ("POST /leagues/$L/filler-policies
200 echoing exactly those two [fillers] at version 4") and round 1 was created
**afterward**, at `08:50:10.183612Z` (`log.md` line "08:51:00Z 50 EXIT CRITERION MET ... round_number=1
status=PENDING created 08:50:10.183612Z"). Both completed rounds' `entrant_policy_version_ids`
are the two champions' UUIDs; no round in this league seated a filler (2-entrant round-robin,
no third party).

**Verdict: TRUE.**

---

## 2. Both champions ranked

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}"
```
```json
[
  {
    "rank": 1,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 1001.4695015289755,
    "rounds_played": 2,
    "episode_wins": 1.0,
    "win_rate": 0.5,
    "policy_label": "battlecode-bc17-orchard:v4"
  },
  {
    "rank": 2,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 998.5304984710245,
    "rounds_played": 2,
    "episode_wins": 1.0,
    "win_rate": 0.5,
    "policy_label": "battlecode-bc17-tankrush:v4"
  }
]
```
Bare list (not `.entries`), as documented. Both `daveey` (`battlecode-bc17-orchard:v4`) and
`daveey-1` (`battlecode-bc17-tankrush:v4`) are ranked with `rounds_played=2 ≥ 1`. No filler policy
(`battlecode-orchard:v4` / `battlecode-examplefuncsplayer17:v4`) appears on the board at all —
absent, satisfying "fillers absent or labelled Baseline".

**Verdict: TRUE.**

---

## 3. Latest round's episode request completed with a replay

```bash
R=$(jq -r '[.entries[]|select(.status=="completed")]|max_by(.round_number).id' /tmp/rounds.json)
echo "$R"   # -> round_ae081c35-154f-4d7b-b44f-0b6c767b8d61  (round 2, the latest completed)
```
The flat route (as the prompt's literal command specifies) 405s, matching the documented gotcha:
```bash
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}"
```
```json
{"detail":"Method Not Allowed"}
```
Falling back to the nested route the playbook documents:
```bash
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}"
```
```json
{
  "entries": [
    {
      "id": "ereq_867fbc51-51c9-4b4e-8019-ae42caa30ded",
      "status": "completed",
      "coworld_id": "cow_7c4f0e60-3dd5-4de2-ba2c-441dad1b4de2",
      "round_id": "round_ae081c35-154f-4d7b-b44f-0b6c767b8d61",
      "replay_url": "https://softmax-public.s3.amazonaws.com/replays/87fbd671-026a-409a-b70d-1ece9759be4d.replay",
      "policy_version_ids": ["77b3fb34-7127-40bc-aef6-15434365d2aa", "db6f8128-382f-43f6-b2c3-88977be8f2fb"],
      "created_at": "2026-09-11T08:56:55.347701Z"
    }
  ],
  "next_cursor": null
}
```
Since this league has exactly 2 entrants (the two champions, no fillers seated), the single
episode request in round 2 IS the champion-vs-champion match. Detail:
```bash
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/87fbd671-026a-409a-b70d-1ece9759be4d.replay",
  "participants": [
    {
      "position": 0, "kind": "policy",
      "policy_version_id": "77b3fb34-7127-40bc-aef6-15434365d2aa",
      "policy_name": "battlecode-bc17-orchard", "version": 4,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
      "is_filler": false, "is_seed": false
    },
    {
      "position": 1, "kind": "policy",
      "policy_version_id": "db6f8128-382f-43f6-b2c3-88977be8f2fb",
      "policy_name": "battlecode-bc17-tankrush", "version": 4,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
      "is_filler": false, "is_seed": false
    }
  ],
  "participant_scores": [
    {"position": 0, "score": 464.0},
    {"position": 1, "score": 235.0}
  ]
}
```
`status=completed`, `replay_url` non-null, participants correctly named `daveey` and `daveey-1`
(no fillers seated, both `is_filler: false`).

**Verdict: TRUE.**

---

## 4. Replay bytes are valid and show the game

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/87fbd671-026a-409a-b70d-1ece9759be4d.replay" -o /tmp/ep.replay
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
```
```
strict UTF-8 JSON: ok
```
```bash
jq -r '.protocol' /tmp/ep.replay        # -> cogame.battlecode.v1
jq -r '.year' /tmp/ep.replay            # -> bc17
jq -r '.result.reason' /tmp/ep.replay   # -> complete
jq -c '.result.fallbacks' /tmp/ep.replay  # -> [0,0]
```
```
cogame.battlecode.v1
bc17
complete
[0,0]
```
`protocol = "cogame.battlecode.v1"` matches the design note's pinned constant
(`design.md:1447` "Protocol id: `cogame.battlecode.v1` — unchanged"). `result.reason = "complete"`
(3 games played, no deadline cut). `result.fallbacks = [0,0]` — **neither champion's doctrine
sheet fell back to the scripted default in this episode.**

The prompt's literal `type=="decision"`/`fallback==true` queries both return 0 (this game's schema
uses `kind`/doctrine events, matching the sibling-year precedent exactly):
```bash
jq -r '[.events[]|select(.type=="decision")]|length' /tmp/ep.replay   # -> 0
jq -r '[.events[]|select(.fallback==true)]|length' /tmp/ep.replay     # -> 0
```
Using the game's real doctrine-event schema:
```bash
jq -c '.events[]|select(.kind|test("doctrine"))' /tmp/ep.replay
```
```json
{"kind":"doctrine_requested","ms":0,"slot":0,"attempt":1,"deadline_ms":20000}
{"kind":"doctrine_requested","ms":0,"slot":1,"attempt":1,"deadline_ms":20000}
{"kind":"doctrine_received","ms":19999,"slot":0,"attempt":1,"latency_ms":19999,"defaults_applied":0,"unknown_fields":1}
{"kind":"doctrine_retry","ms":19999,"slot":1,"cause":"timeout"}
{"kind":"doctrine_received","ms":7601,"slot":1,"attempt":2,"latency_ms":7601,"defaults_applied":0,"unknown_fields":0}
```
Slot 0 (daveey/orchard): attempt 1 succeeded at the wire (latency 19999 ms, just inside the
20000 ms deadline), a real LLM sheet with 1 unknown field ignored. Slot 1 (daveey-1/tankrush):
attempt 1 timed out, attempt 2 succeeded cleanly (7601 ms, 0 defaults/unknown). **Decision count 2,
fallback count 0 — zero fallbacks in this episode**, a small minority (0 %) by the check's
standard.

Game content — the champions doing the thing the game is about (archons, gardeners, bullet
trees, victory points, tanks, lumberjacks, scouts, donations, strikes):
```bash
jq -c '.result | {names, aliases, scores, wins, points}' /tmp/ep.replay
jq -r '.result.games[]|{map,rounds_played,end_reason,winner,victory_points,domination_factor}' /tmp/ep.replay
```
```json
{"names":["daveey","daveey-1"],"aliases":["Clan Ash","Clan Basil"],"scores":[464.0,235.0],"wins":[2,1]}
```
```json
{"map":"Blitzkrieg","rounds_played":2998,"end_reason":"victory_points_reached","winner":1,"victory_points":[461,1158],"domination_factor":"PHILANTROPIED"}
{"map":"Aligned","rounds_played":2999,"end_reason":"more_victory_points","winner":0,"victory_points":[381,169],"domination_factor":"PWNED"}
{"map":"Barrier","rounds_played":1320,"end_reason":"victory_points_reached","winner":0,"victory_points":[1000,0],"domination_factor":"PHILANTROPIED"}
```
3 games played across 3 different maps, ending on all three of the game's documented end
conditions the design lists (`victory_points_reached` twice, `more_victory_points` once — the
round-limit tiebreak variant). Event stream (194 events total, kinds:
`shake`×40, `tree_planted`×36, `strike`×23, `donation`×22, `unit_milestone`×21, `tree_lost`×11,
`gardener_lost`×10, `first_action`×6, `famine`×4, `game_start`/`game_end`×3, `chop_reveal`×3,
`farm_online`×2, `archon_lost`×2, `tiebreak`×1), early/middle/late excerpt:
```
// early (game 0, Blitzkrieg)
game_start   round 0
unit_milestone / first_action   round 1  (both seats)
shake        round 13
tree_planted round 28, 31, 57, 59
famine       round 59

// middle (game 1, Aligned)
game_start   round 0
tree_planted round 24, 36, 51
shake        round 37, 45, 53, 61, 75, 86, 97

// late (game 2, Barrier)
farm_online  round 870
donation     round 872, 916, 962, 1009, 1057, 1105, 1158, 1212, 1263, 1320
strike       round 1056, 1063, 1071
tree_lost    round 929, 942, 961
game_end     round 1320
episode_end
```
This lines up with the earlier "games" stat block: gardeners planting/shaking bullet trees,
archons/soldiers/tanks/scouts built, bullets earned/donated/spent, donations racing to 1000
victory points in game 2 (Barrier: `victory_points:[1000,0]`, `winner:0`) — exactly the "buy
1000 victory points" win condition the league description names.

**Verdict: TRUE.** Valid strict-UTF-8 JSON, protocol matches, `reason=complete`, zero fallbacks
(both champions' decisions were live LLM content), events show real gameplay across 3 maps.

---

## 5. Hosted game log is clean

```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}"
```
Raw body is python `b'…'` byte-string reprs per container; decoded with `ast.literal_eval`
(script run locally) before grepping, per the documented gotcha:
```
===== container: bedrock-sidecar =====
2026-09-11 08:57:04,211 INFO __main__ bedrock_sidecar_started {...}
2026-09-11 08:57:12,186 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-11 08:57:27,882 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-11 08:57:32,185 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-11 08:58:03,676 WARNING datadog.dogstatsd Error submitting packet: [Errno 111] Connection refused, dropping the packet and closing the socket

===== container: game =====
battlecode config: year=bc17 pool=mixed seed=203486114 games=3 maxRounds=3000 num_agents=2 matchBudget=330s
battlecode: listening on 0.0.0.0:8080
battlecode: waiting for seats
battlecode: refused a seat-0 connection: seat 0 was given the wrong connection token
battlecode: a spectator joined /global
battlecode: seat 0 connected
battlecode: seat 0 registered kind=llm label=orchard
battlecode: seat 1 connected
battlecode: seat 1 registered kind=llm label=tankrush
battlecode: doctrine
battlecode llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
battlecode llm: seat 1 attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
battlecode: match
battlecode: settled: complete
battlecode: reason=complete games=3 scores=[464.0, 235.0] sim=4.109s wall=38.42s
```
```bash
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs_decoded.txt || echo CLEAN
```
```
CLEAN
```
No forbidden string anywhere in the decoded log. The one "attempt 1 failed, will retry" line
(seat 1, a timeout) is followed by a silent, successful attempt 2 — matching the replay's
`doctrine_received ms=7601 slot=1 attempt=2` — never a fallback.

**Verdict: TRUE — CLEAN.**

---

## 6. The public page uses the static replay path

```bash
curl -sS "https://softmax.com/battlecode/bc17" | grep -o '<iframe[^>]*src="[^"]*"'
```
```
(no output — page is client-rendered, as documented platform-wide since the lighthouse run of
2026-08-22; an empty grep here is NOT a false negative)
```
Falling back to the documented method: the page's Next.js SSR payload carries `state.playlist[0]`
directly.
```bash
grep -o 'playlist\\":\[[^]]*\]' /tmp/page_bc17.html | head -c 2000
```
```json
playlist":[{"episodeId":"b0ec5f4f-2139-4b38-812b-1ee1f26dee18","coworldId":"cow_7c4f0e60-3dd5-4de2-ba2c-441dad1b4de2","coworldName":"battlecode","coworldVersion":"0.11.2","replayUrl":"https://softmax-public.s3.amazonaws.com/replays/87fbd671-026a-409a-b70d-1ece9759be4d.replay","finishedAt":"2026-09-11T08:59:59.159902Z","roundNumber":2,"episodeNumber":1,"code":"battlecode.r2.e1","matchup":{"divisionId":"div_943b6ac3-c635-4473-9224-1363214931c9","divisionName":"Competition","first":{"rank":1,"player_name":"daveey","policy_label":"battlecode-bc17-orchard:v4",...},"second":{"rank":2,"player_name":"daveey-1","policy_label":"battlecode-bc17-tankrush:v4",...}},"seats":2,"roster":["daveey","daveey-1"]}]
```
The featured match's `replayUrl` is **byte-identical** to check 3's `replay_url`
(`.../replays/87fbd671-026a-409a-b70d-1ece9759be4d.replay`) — `softmax.com/battlecode/bc17`'s
featured match **is** this run's own round-2 champion-vs-champion episode. A featured match is
present (2 ranked players).

Iframe `src` resolved via the documented session call the page's own JS makes:
```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_7c4f0e60-3dd5-4de2-ba2c-441dad1b4de2","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/87fbd671-026a-409a-b70d-1ece9759be4d.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_7c4f0e60-3dd5-4de2-ba2c-441dad1b4de2/sha256%3A4d5c5bced3b461c9baf31db9cea951ac6a9198234f37555879edeac04a492fd5/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F87fbd671-026a-409a-b70d-1ece9759be4d.replay",
  "ready": true
}
```
`ready: true`, static `…/v2/coworlds/replays/static/<cow_id>/<manifest_sha>/index.html?v=2#replay=<s3 url>`
form (the fragment variant), **never** a `/client/replay` pod URL. `<sha>` = the coworld's
`manifest_hash` (`sha256:4d5c5bced3b461c9baf31db9cea951ac6a9198234f37555879edeac04a492fd5`),
matching `STATE.coworld.manifest_sha` exactly.

**Verdict: TRUE.** Source used: raw-HTML grep (empty, expected) → SSR-payload
`state.playlist[0]` on `softmax.com/battlecode/bc17` → `POST /coworlds/replays/session` for the
resolved static iframe `src`.

**Resolved iframe `src` used for check 8:**
```
https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_7c4f0e60-3dd5-4de2-ba2c-441dad1b4de2/sha256%3A4d5c5bced3b461c9baf31db9cea951ac6a9198234f37555879edeac04a492fd5/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F87fbd671-026a-409a-b70d-1ece9759be4d.replay
```

---

## 7. Certification declared the static bundle

Read from the **committed** `runs/2026-09-10-battlecode-2017/release-result.json`. This artifact
is the release run of **another year run** (bc19), release run id `34565644691`, which published
the already-canonical **0.11.2** — this run's own three release dispatches (0.11.3/0.11.4/0.11.5)
all failed at hosted smoke on a degraded platform fleet (see `release-adopted.md`), so phase 40
was satisfied by **adopting** 0.11.2, which was built from a sha (`526befdb`) that already
contained this run's whole bc17 module (PR #18) and every round-1 review fix (PR #22). This is
the artifact `prompts/40-release.md`'s writes clause requires committed for this run, and it is
what this check reads — never `/tmp`.
```bash
jq -r '.certify.replay_liveness' runs/2026-09-10-battlecode-2017/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```
```bash
jq -r '{ok, version, cow_id, canonical, manifest_sha, certify_ok: .certify.ok, secret_put, step_failed}' runs/2026-09-10-battlecode-2017/release-result.json
```
```json
{
  "ok": true,
  "version": "0.11.2",
  "cow_id": "cow_7c4f0e60-3dd5-4de2-ba2c-441dad1b4de2",
  "canonical": true,
  "manifest_sha": "sha256:4d5c5bced3b461c9baf31db9cea951ac6a9198234f37555879edeac04a492fd5",
  "certify_ok": true,
  "secret_put": true,
  "step_failed": null
}
```
`manifest_sha` matches `STATE.coworld.manifest_sha` and the sha resolved live in check 6 exactly.
The failed dispatch's artifact is preserved beside this one as `release-result-0.11.5-FAILED.json`
(git-mv'd, never deleted, per `release-adopted.md`) — it is a **deliberately retained record, not
this check's source**.

**Verdict: TRUE.** Source: committed `runs/2026-09-10-battlecode-2017/release-result.json`
(the adopted 0.11.2 release run `34565644691`).

---

## 8. Spectator judgment — the viewer is EXECUTED, then judged

*(a) Dispatch.* Iframe `src` from check 6:
```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_7c4f0e60-3dd5-4de2-ba2c-441dad1b4de2/sha256%3A4d5c5bced3b461c9baf31db9cea951ac6a9198234f37555879edeac04a492fd5/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F87fbd671-026a-409a-b70d-1ece9759be4d.replay'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
```
**Attempt 1** dispatched at `2026-09-11T09:03:36Z`; run found by sorting runs created after
dispatch (`gh run list … | jq 'sort_by(.createdAt)|reverse|.[0]'`) →
`{"createdAt":"2026-09-11T09:03:38Z","databaseId":34582261232}`. `gh run watch 34582261232
--exit-status` → **green**, exit 0. Downloaded: `{"loaded":true,"ms":1860,"clock":"5:05 GAME 1 OF 3
— BLITZKRIEG",...}`, `scrub`: `0%→5:05 GAME 1 OF 3 — BLITZKRIEG`, `50%→5:05 GAME 1 OF 3 —
BLITZKRIEG` (settle_ms 1006), `100%→2:32 GAME 2 OF 3 — ALIGNED` (settle_ms 503). **`loaded: true`
but the 0 % and 50 % readouts were byte-identical** — the default `settle` (700 ms) was not
enough time for that particular seek to land before the readout was taken, so the scrub check
as run did not satisfy the "three readouts differ" gate.

**Attempt 2** (different approach — raised `settle` from the 700 ms default to 3000 ms, `timeout`
120): dispatched `2026-09-11T09:04:50Z`, run `34582367441` created `09:04:52Z`, green, exit 0.
Downloaded and **this is the evidence committed to `runs/2026-09-10-battlecode-2017/viewer-check/`**:
```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-09-10-battlecode-2017/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":986,"clock":"5:05 GAME 1 OF 3 — BLITZKRIEG","scorebug":"CLAN ASH daveey 50 5:05 GAME 1 OF 3 — BLITZKRIEG CLAN BASIL daveey-1 50","feed_lines":7}
```
```bash
jq -c '.signals' runs/2026-09-10-battlecode-2017/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["ready"],"bridge_ready":true,"bridge_error":[]}
```
```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)\t\(.settle_ms // "")"' runs/2026-09-10-battlecode-2017/viewer-check/viewer-smoke.json
```

| scrub position | clock reading | settle_ms |
|---|---|---|
| 0 % | `5:05 GAME 1 OF 3 — BLITZKRIEG` | (initial load) |
| 50 % | `2:32 GAME 2 OF 3 — ALIGNED` | 2011 |
| 100 % | `0:00 GAME 3 OF 3 — BARRIER` | 1004 |

```bash
jq -r '.failure // "no failure"' runs/2026-09-10-battlecode-2017/viewer-check/viewer-smoke.json
```
```
no failure
```

**`loaded: true`** (both `data-replay-loaded="true"` and the `coworld-replay` bridge's `ready`
fired), and the **three clock readouts differ** — game 1 → game 2 → game 3 (endcard). Item 8's
two hard gates both hold on attempt 2. Attempt 1's flake (identical 0 %/50 % readout) is recorded
above rather than discarded, since it is real data about the default settle window's margin on
this replay, not a rendering failure — the viewer itself loaded and the scrubber did work once
given more settle time.

*(c) Replay JSON reconciliation* (from `/tmp/ep.replay`, check 4):
```bash
jq -r '.result.games[]|{map,rounds_played,end_reason,winner,victory_points}' /tmp/ep.replay
```
```json
{"map":"Blitzkrieg","rounds_played":2998,"end_reason":"victory_points_reached","winner":1,"victory_points":[461,1158]}
{"map":"Aligned","rounds_played":2999,"end_reason":"more_victory_points","winner":0,"victory_points":[381,169]}
{"map":"Barrier","rounds_played":1320,"end_reason":"victory_points_reached","winner":0,"victory_points":[1000,0]}
```
This lines up exactly with the viewer's three readouts: 0 % is game 1 (map Blitzkrieg, matches
`.result.games[0].map`), 50 % is game 2 (map Aligned, matches `.result.games[1].map`), 100 % is
game 3 (map Barrier, matches `.result.games[2].map`, `rounds_played=1320` matching the
screenshot's "1320 rounds in the last one").

**Screenshot description** (`viewer-smoke.png`, taken after the 100 % scrub, described not
re-rendered): a dark endcard reading "daveey 87 FINAL CLAN BASIL daveey-1 12" in the top scorebug
(a live in-progress score readout captured mid-render, not the final 464/235 — see caveat below);
a centred "CLAN ASH — DAVEEY" panel with a callout "THE GAME ENDED ON VICTORY POINTS REACHED IN
GAME 3, ROUND 1320" and "score 464 — 235 · 3 games played · 1320 rounds in the last one"; two
side-by-side sealed doctrine-sheet panels for Clan Ash/daveey ("farms first and fights later,
wants 5 gardeners for every archon, packs its trees six to a gardener, spends 20 percent of its
army money on tanks...") and Clan Basil/daveey-1 ("walks tanks at their archon from the first
bullets, wants 2 gardeners for every archon, rings its archon with trees and leaves four
lanes..."); below that a full numeric stat block per side (victory points, bullets, trees
planted/mature/lost, units built/lost/kills, damage dealt, friendly fire, neutral trees felled,
bullets left/worth) and a round-3000-ladder tiebreak readout (`PHILANTROPIED`: victory points
1000 vs 0, bullet trees 25 vs 6, bullet worth 6755.8 vs 3224.8, highest id 14038 vs 13920); a
partially-visible scrollable event feed on the right ("Game 3 – Clan Ash wins (victory points
reached)", "Clan Ash donates 26.0 bullets for 2 points — 0 to go, game 3, round …", etc.); and a
bottom transport strip with rewind/step/play/+25/loop/fast-forward controls, speed buttons
(1×/2×/3×/4×/8×/15×), a "spoilers" toggle, a "round 1320/2999" readout, and a scrubber bar. This
is legible and unambiguously shows the game: two sealed doctrine sheets in the champions' own
free-text style, per-side economy/combat stats, a round-by-round donation/strike event feed, and
a scrub-driven clock, consistent with `/tmp/ep.replay`'s own numbers (final score 464/235 in the
replay matches "score 464 — 235" on-screen exactly; game 3 = Barrier = 1320 rounds = victory
points 1000–0, all matching). It **looks like the starter's chrome** — the same
transport-strip/scrubber/scorebug/endcard shape the sibling bc19 run described for this same
starter — not a different product.

*Caveat, stated plainly:* the top scorebug in the screenshot reads "daveey 87 ... daveey-1 12",
which does not match the final 464/235 — this is a snapshot of one of the intermediate scrub
positions' live scoreboard (the score readout updates continuously as the timeline plays/steps,
and the screenshot was taken shortly after the 100 % seek rather than after the endcard's own
tween settled), not evidence against the replay. The panel text below it ("score 464 — 235 · 3
games played") is the authoritative end-of-match summary and matches the replay exactly. The known,
recorded residue — 0.11.2 predates PR #23, so a dismissed bc17 doctrine panel cannot be
re-opened (`#bc17-doctrines-toggle` missing) — does not appear in this screenshot (the doctrine
panels are shown open, not dismissed) and does not bear on this check.

**Verdict: TRUE** (on attempt 2's evidence, which is what is committed).

---

## Spectator-judgment paragraph

Battlecode 2017 "Robotic Wildlife Fund" is legible and does show the game as designed: the
viewer-check run drew a real frame within under 2 seconds (`loaded:true`, `ms:986`), and scrubbing
through the timeline produced three genuinely different game states — game 1 of 3 on map
Blitzkrieg, game 2 of 3 on map Aligned, and the final game 3 of 3 on map Barrier at its
match-over endcard — each of which matches the recorded replay's own per-game map and end
condition exactly (Blitzkrieg → `victory_points_reached`, Aligned → `more_victory_points`
tiebreak, Barrier → `victory_points_reached` at round 1320 of 2999, 1000–0). The endcard screenshot
shows both champions' free-text sealed doctrine sheets side by side (Clan Ash/daveey's
gardener-heavy tank economy vs. Clan Basil/daveey-1's tank-rush-the-archon opening), a full
numeric stat block per side (victory points, trees, units, damage, bullets), a round-by-round
donation/strike event feed, and the round-3000 ladder tiebreak readout used when neither side hits
1000 points outright — all of which is the thing the game is about (archons hiring gardeners who
plant bullet trees, soldiers/tanks/scouts/lumberjacks fighting with travelling bullets in
continuous float space, victory bought with donated bullets). The picture is neither empty,
frozen, nor unreadable; the one blemish is that the top scorebug in the specific captured frame
shows an in-progress score (87–12) rather than the final 464–235, which is a screenshot-timing
detail (the tween had not settled at the instant of capture), not a rendering defect — the
authoritative end-of-match summary panel directly below it does show the correct final score and
matches the replay bytes. The chrome (transport strip with speed multipliers, scrubber, scorebug,
endcard) matches the starter's shape described for sibling coworlds, not a rewrite wearing the
same ids.

---

## Files written / committed this run

- `runs/2026-09-10-battlecode-2017/VERIFY.md` (this file)
- `runs/2026-09-10-battlecode-2017/viewer-check/{viewer-smoke.json,viewer-smoke.png,smoke-stdout.txt,smoke-stderr.txt}`
  — attempt 2's evidence (GitHub Actions run `34582367441`, `Metta-AI/coworld-builder`,
  `viewer-check.yml`, dispatched and downloaded this session). Attempt 1 (run `34582261232`) is
  recorded in check 8's text above but its artifact was not committed (superseded by attempt 2,
  which used a longer `settle` and produced three differing readouts).

## Summary table

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers | **TRUE** — round_4c4f8ffa (r1, 08:52:53Z) and round_ae081c35 (r2, 09:00:09Z), both after fillers registered 08:50:00Z |
| 2 | Both champions ranked | **TRUE** — daveey rank 1 (1001.47, rounds_played 2), daveey-1 rank 2 (998.53, rounds_played 2), no fillers on board |
| 3 | Latest round's episode request completed w/ replay | **TRUE** — ereq_867fbc51, status completed, replay_url non-null, participants daveey + daveey-1 |
| 4 | Replay bytes valid, protocol matches, shows the game | **TRUE** — strict UTF-8 JSON, protocol cogame.battlecode.v1, reason=complete, fallbacks=[0,0] (zero fallbacks), 3 games/194 events of real gameplay |
| 5 | Hosted game log clean | **TRUE — CLEAN**, no forbidden strings |
| 6 | Public page uses static replay path | **TRUE** — SSR playlist[0] matches this run's own episode exactly; session call returned `ready:true` static route |
| 7 | Certification declared static bundle | **TRUE** — committed release-result.json (adopted 0.11.2, release run 34565644691) |
| 8 | Viewer executed and legible | **TRUE** — loaded:true, three differing clock readouts (attempt 2, settle=3000ms), screenshot matches starter chrome and the replay record |

**Overall: 8 of 8 TRUE.**
