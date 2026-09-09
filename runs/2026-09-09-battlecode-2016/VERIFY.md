# VERIFY — battlecode-2016 (bc16 league)   (started 2026-09-09T13:18Z, in progress)

slug (public page): `battlecode` (coworld name) / league short_name `bc16` — the run slug
`battlecode-2016` is a coworld-builder run-directory name, not the platform slug. See §6 for
both pages checked.

Verdict so far: **7 of 8 checks TRUE, 1 (rounds ≥2) IN PROGRESS — polling within the 75-minute
bound.** This file is being written incrementally; §1 and §3 will be updated in place the
moment round 2 lands, or marked FALSE with evidence if the bound expires first.

Values used (given, not re-derived):
```
BASE=https://softmax.com/api/observatory/v2
L=league_6cdded0f-6a1c-44c5-8d31-e68a12500653
D=div_1e064838-5355-4739-813d-c9da01d05736
COW=cow_4bdfa37d-4f28-4480-a42d-0cc439cd158a
```

---

## 1. ≥2 completed rounds after fillers were set

Per the run's own `log.md`, fillers were registered **before** the first trigger — there is no
pre-filler round to exclude, so **every** completed round in this league counts:

```
92:2026-09-09T13:24:00Z 50 filler UUIDs resolved client-side ... battlecode-bulwark:v1=99053bee...
    and battlecode-greenhorn:v1=bb2726bf..., both player=daveey ...
93:2026-09-09T13:24:00Z 50 POST /leagues/$L/filler-policies 200: response lists EXACTLY the two
    filler UUIDs ... Set BEFORE any trigger-round
95:2026-09-09T13:24:00Z 50 POST /leagues/$L/rounds-paused 200 paused=false ...;
    POST /leagues/$L/trigger-round 200 -> kind=platform workflow_id=ladder-league_6cdded0f...
96:2026-09-09T13:24:00Z 50 round 1 = round_5a5bf68d-9904-4f7e-a4ec-1fe95e582f74 status=pending
    error=null (a real round row ...)
```

(Note: the log's own heartbeat timestamp of 13:24:00Z sits at a fixed marker time recorded by
phase 50; the round's own `created_at`, fetched below, is 13:15:22Z — both predate this
verifier's first poll and both agree fillers-before-trigger holds.)

Command (poll 1, run at 13:18Z):
```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" -H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0"
```
```json
[
  {"id": "round_5a5bf68d-9904-4f7e-a4ec-1fe95e582f74", "round_number": 1,
   "status": "completed", "error": null}
]
```
Count of `completed`: **1**. NOT YET ≥2 — polling continues below.

### Poll log (every ~5 min, bounded at 75 min from 13:18Z i.e. until ~14:33Z)

| time (UTC) | completed rounds | round ids |
|---|---|---|
| 13:18 | 1 | round_5a5bf68d (round 1) |
| 13:29 | 1 | round_5a5bf68d (round 1) — see raw output below |

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" -H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0"
```
```
count 1
round_5a5bf68d-9904-4f7e-a4ec-1fe95e582f74 1 completed None
```

**STATUS: PENDING — updating in place as polls continue.**

---

## 2. Both champions ranked, fillers absent/Baseline

```bash
curl -sS "$BASE/divisions/$D/leaderboard" -H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0"
```
```json
[
  {
    "rank": 1, "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
    "score": 1016.0, "score_label": "MMR", "rounds_played": 1, "episode_wins": 1.0,
    "win_rate": 1.0, "policy_label": "battlecode-bc16-pullers:v1"
  },
  {
    "rank": 2, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
    "score": 984.0, "score_label": "MMR", "rounds_played": 1, "episode_wins": 0.0,
    "win_rate": 0.0, "policy_label": "battlecode-bc16-bulwark:v1"
  }
]
```
Both `daveey` and `daveey-1` present, both `rounds_played: 1`. No filler rows present (list has
exactly 2 rows, both champions). **TRUE.**

---

## 3. Latest round's episode request completed with a replay

Round 1 is the only completed round (see §1). The flat `/episode-requests?round_id=` route
**405s** as the playbook's gotcha predicts — used the nested route instead:

```bash
R=round_5a5bf68d-9904-4f7e-a4ec-1fe95e582f74
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" ...   # -> HTTP 405 {"detail":"Method Not Allowed"}
curl -sS "$BASE/rounds/$R/episode-requests" -H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0"
```
```json
{
  "entries": [
    {
      "id": "ereq_f888cee7-02d8-48eb-82b7-a6eb9ea43317",
      "status": "completed",
      "coworld_id": "cow_4bdfa37d-4f28-4480-a42d-0cc439cd158a",
      "round_id": "round_5a5bf68d-9904-4f7e-a4ec-1fe95e582f74",
      "replay_url": "https://softmax-public.s3.amazonaws.com/replays/7390ce0d-8e56-422a-8914-1196c9e654a5.replay",
      "policy_version_ids": ["c073ca20-f820-403f-86c7-8cbd8d704084", "2175495c-757d-451e-a3e3-b3ed6f20692b"],
      "created_at": "2026-09-09T13:15:22.114230Z"
    }
  ],
  "next_cursor": null
}
```

```bash
curl -sS "$BASE/episode-requests/ereq_f888cee7-02d8-48eb-82b7-a6eb9ea43317" -H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0" \
 | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/7390ce0d-8e56-422a-8914-1196c9e654a5.replay",
  "participants": [
    {"position": 0, "policy_name": "battlecode-bc16-bulwark", "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey", "is_filler": false},
    {"position": 1, "policy_name": "battlecode-bc16-pullers", "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1", "is_filler": false}
  ],
  "participant_scores": [{"position": 0, "score": 23.0}, {"position": 1, "score": 476.0}]
}
```
`status == "completed"`, `replay_url` non-null, participants name both `daveey` and `daveey-1`
(this round seated only the two champions — no filler seat, which is consistent with num_agents=2
and both champions available; fillers appear as `Baseline (N)` only on rounds where a champion is
missing). **TRUE for round 1.** Will re-run against round 2's episode request once it lands (§1),
and update this section if the result differs.

---

## 4. Replay bytes are valid and show the game

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/7390ce0d-8e56-422a-8914-1196c9e654a5.replay" -o /tmp/ep.replay
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol' /tmp/ep.replay
jq -r '.result.reason' /tmp/ep.replay
jq -r '.result.fallbacks' /tmp/ep.replay
```
```
strict UTF-8 JSON: ok
protocol: cogame.battlecode.v1
result.reason: complete
result.fallbacks: [0, 0]
```
(Note: this replay's top-level key is `result` singular with `.reason`/`.fallbacks` nested inside
it, not top-level `.results.reason`/`fallback` events as the generic prompt template assumes —
confirmed by reading the actual file structure: top keys are
`format, version, protocol, game_version, year, config, seed, aliases, names, seats,
prompt_preamble, games, plan, events, result`, and events use key `kind` not `type`.)

- **Protocol match:** `cogame.battlecode.v1` matches `design.md:1434` ("Protocol id:
  `cogame.battlecode.v1` — unchanged") and `design.md:1637`'s literal replay-header example.
- **`result.reason == "complete"`** — no deadline/tiebreak-abandon edge case.
- **`result.fallbacks: [0, 0]`** — zero fallbacks for both champion seats; both are LLM prompt
  policies (`policy_kind: ["llm","llm"]` in `result`) with non-trivial per-game statistics
  (units built 60/59 and 185/188 across the two games — see §8's replay-event excerpt), i.e.
  decisions are non-scripted and not degenerate.
- **`.events`** (188 total) carry `kind` values: `episode_start, doctrine_requested,
  doctrine_received, game_start, unit_milestone, first_action, zombie_wave, infection,
  neutral_activated, turned, outbreak, duel, den_destroyed, archon_lost, game_end, rout,
  tiebreak, episode_end` — a rich, game-specific event stream (den destructions, infections,
  turned-to-zombie events, duels), not a placeholder.
- **`.result.games[]`** carries two games: game 1 on map `voluted`, `end_reason:
  "archons_destroyed"`, winner=1 at round 641; game 2 on map `closequarters`, `end_reason:
  "more_archons"` (the tiebreak-ladder rung), winner=1 at round 3000 (`tiebreak_round: 2999`,
  `dens_destroyed`, `zombies_spawned/killed`, `infections_suffered/inflicted` all present and
  non-zero on both sides).

**TRUE.**

---

## 5. Hosted game log is clean

```bash
curl -sS "$BASE/episode-requests/ereq_f888cee7-02d8-48eb-82b7-a6eb9ea43317/artifacts/logs" \
  -H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0" -H "X-Use-Elevated-Privileges: true"
```
Decoded body (python byte-string reprs decoded before grepping, per the playbook):
```
===== container: coworld-init-config =====
b''

===== container: bedrock-sidecar =====
b'2026-09-09 13:15:32,227 INFO __main__ bedrock_sidecar_started {...}
[2026-09-09 13:15:32 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-09-09 13:15:32,706 INFO hypercorn.error Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-09-09 13:15:39,448 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-09 13:15:42,410 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-09 13:16:18,726 WARNING datadog.dogstatsd Error submitting packet: [Errno 111] Connection refused, dropping the packet and closing the socket'

===== container: game =====
b'battlecode config: year=bc16 pool=mixed seed=642192065 games=3 maxRounds=3000 num_agents=2 matchBudget=360s
battlecode: listening on 0.0.0.0:8080
battlecode: waiting for seats
battlecode: refused a seat-0 connection: seat 0 was given the wrong connection token
battlecode: a spectator joined /global
battlecode: seat 1 connected
battlecode: seat 1 registered kind=llm label=pullers
battlecode: seat 0 connected
battlecode: seat 0 registered kind=llm label=bulwark
battlecode: doctrine
battlecode llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
battlecode: match
battlecode: settled: complete
battlecode: reason=complete games=2 scores=[23.0, 476.0] sim=13.9s wall=26.107s'

===== container: worker =====
b''
```
```bash
python3 -c "
raw = open('/tmp/logs1.raw', encoding='utf-8').read()
import re
print(re.findall(r'falling back|LLM provider is unavailable|cut off at max_tokens|rejected', raw))
"
```
```
[]
```
(Note: the game container's line `refused a seat-0 connection: seat 0 was given the wrong
connection token` contains "refused", not "rejected" — the two are visually similar but distinct
words and neither the regex nor a plain-text read matches the forbidden pattern. This is the
platform routing a spectator/observer connection attempt away from the seat-0 slot before the
real seat-0 client connected, not an LLM rejection.)

**CLEAN. TRUE.**

---

## 6. The public page uses the static replay path

Raw-HTML grep on both candidate pages — both are client-rendered (matches the playbook's answered
note: "the page is now client-rendered for the iframe"), so the grep correctly finds nothing on
either:
```bash
curl -sS "https://softmax.com/battlecode" | grep -o '<iframe[^>]*src="[^"]*"'      # (empty)
curl -sS "https://softmax.com/battlecode/bc16" | grep -o '<iframe[^>]*src="[^"]*"' # (empty)
```
Both returned HTTP 200 (1,025,426 and 983,373 bytes respectively) with no matching `<iframe>` in
the raw HTML — expected for a client-rendered page, not treated as a failure.

Fallback: the coworld-detail API, confirming id/canonical/manifest_hash:
```bash
curl -sS "$BASE/coworlds?limit=200" -H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0" \
 | jq -r '.entries[]|select(.name=="battlecode" and .canonical==true)|{id,canonical,version,manifest_hash}'
```
```json
{
  "id": "cow_4bdfa37d-4f28-4480-a42d-0cc439cd158a",
  "canonical": true,
  "version": "0.8.0",
  "manifest_hash": "sha256:20a188ec8ada2b62879e5bb25065b3076e8dc190d6457a38538aabafb8a8419f"
}
```
Matches the brief's given `cow_id` and `manifest_hash` exactly. `featured_match` is `null`
platform-wide (confirmed on this row too), matching the playbook's documented answer — not
evidence of anything by itself.

Per the playbook's "Answered" note, the iframe `src` actually comes from the same
`POST /coworlds/replays/session` call the page's own JS makes:
```bash
curl -sS -X POST "$BASE/coworlds/replays/session" -H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0" \
  -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_4bdfa37d-4f28-4480-a42d-0cc439cd158a","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/7390ce0d-8e56-422a-8914-1196c9e654a5.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_4bdfa37d-4f28-4480-a42d-0cc439cd158a/sha256%3A20a188ec8ada2b62879e5bb25065b3076e8dc190d6457a38538aabafb8a8419f/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F7390ce0d-8e56-422a-8914-1196c9e654a5.replay",
  "ready": true
}
```
`ready: true`, path ends `/index.html` (post-2026-08-28 fragment form,
`?v=2#replay=<s3 url>`, which the playbook records as an equally-valid static route — **not** a
`/client/replay` pod URL. `<sha>` in the path is the coworld's `manifest_hash`, matching §above
exactly. **Source used: the `/coworlds/replays/session` API call (item 6's documented fallback),
since both pages are client-rendered.** **TRUE.**

This URL is the iframe `src` used for check 8.

---

## 7. Certification declared the static bundle

Read from the committed `runs/2026-09-09-battlecode-2016/release-result.json` (not `/tmp` — that
sandbox is gone), as `prompts/60-verify.md` §7 directs:
```bash
jq -r '.certify.replay_liveness' runs/2026-09-09-battlecode-2016/release-result.json
```
The file's schema nests this under a top-level `replay_liveness` key (not `.certify.…` — read
the actual file rather than assume the exact path):
```json
"replay_liveness": "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"
```
Full `output_tail` (excerpt) confirms all 10 certification transcript steps passed
(`matriculate`, `source-resolves`, `images-reachable`, `fixture-conforms`, `smoke-episode`,
`results-conform`, `replay-present`, `replay-loadable`, `players-run`, `supporting-roles`) and
ends: `Certified dist/coworld_manifest.json ... Transcript: coworld-executable (10 steps passed)
... Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not
required)`.

Contains the required string `Replay liveness: skipped (static replay bundle declared`.
**Source: the committed `runs/2026-09-09-battlecode-2016/release-result.json`** (present, no
re-download needed). **TRUE.**

---

## 8. Spectator judgment — the viewer, EXECUTED then judged

### (a) Dispatch

Iframe `src` from §6 (full URL, fragment included):
```
https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_4bdfa37d-4f28-4480-a42d-0cc439cd158a/sha256%3A20a188ec8ada2b62879e5bb25065b3076e8dc190d6457a38538aabafb8a8419f/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F7390ce0d-8e56-422a-8914-1196c9e654a5.replay
```

**Attempt 1** (default settle=700ms), dispatched 13:21:01Z:
```bash
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
```
Run **34356511853** (created 13:21:03Z, confirmed newest-by-createdAt, not "the latest" blind),
watched to green in 44s. Result:
```json
{"loaded": true, "ms": 1259, "clock": "2:32 GAME 1 OF 2 — VOLUTED doctrines", "scorebug": "CLAN ASH daveey · Wall the horde; hold to 3000. 50 2:32 GAME 1 OF 2 — VOLUTED doctrines CLAN BASIL daveey-1 · Infect, convert, overwhelm. 50", "feed_lines": 7}
```
scrub: `0%="2:32 GAME 1 OF 2 — VOLUTED doctrines"`, `50%="2:31 GAME 1 OF 2 — VOLUTED doctrines"`
(settle_ms 503), `100%="2:31 GAME 1 OF 2 — VOLUTED doctrines"` (settle_ms 1004) — **50% and 100%
matched**, an ambiguous result on its own (advancing from 0%→50% but seemingly frozen 50%→100%).
Rather than record this as a pass or a fail on ambiguous evidence, retried with a different
approach (longer settle + a soak window), per the 3-attempt retry budget.

**Attempt 2** (settle=4000ms, soak=10s — a different approach: more time for the Worker to
re-simulate a seek on this replay, which `viewer_smoke.mjs`'s own code comment documents as a
known real effect on heavy Battlecode replays, not a freeze: *"a seek on a heavy replay is a
re-simulation in the Worker: it can take well past the old fixed 700ms without being frozen
(cogame-battlecode bc21, 2026-09-04...)"*), dispatched 13:25:49Z:
```bash
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90 -f settle=4000 -f soak=10
```
Run **34357018290** (created 13:25:51Z, confirmed newest-by-createdAt after this dispatch),
watched to green in 1m55s, artifact downloaded and **committed** at
`runs/2026-09-09-battlecode-2016/viewer-check/` (`viewer-smoke.json`, `viewer-smoke.png`,
`smoke-stdout.txt`, `smoke-stderr.txt`). This is the run used as this check's evidence of record.

### (b) Readouts (verbatim, attempt 2 — the evidence of record)

```json
{"loaded": true, "ms": 2007, "clock": "2:22 GAME 1 OF 2 — VOLUTED doctrines", "scorebug": "CLAN ASH daveey · Wall the horde; hold to 3000. 48 2:22 GAME 1 OF 2 — VOLUTED doctrines CLAN BASIL daveey-1 · Infect, convert, overwhelm. 51", "feed_lines": 7}
```
`signals`:
```json
{"data_replay_loaded": "true", "data_replay_error": null, "bridge": ["ready"], "bridge_ready": true, "bridge_error": []}
```

Three clock readouts:

| scrub position | clock | settle_ms |
|---|---|---|
| 0 % | `2:22 GAME 1 OF 2 — VOLUTED doctrines` | — |
| 50 % | `1:16 GAME 2 OF 2 — CLOSEQUARTERS doctrines` | 1005 |
| 100 % | `FINAL MATCH OVER doctrines` | 1505 |

All three **differ**, and they differ in exactly the way the replay's own event log requires: 0%
is early in game 1 (map `voluted`), 50% has moved into game 2 (map `closequarters` — the second
game's actual map name, matching `.result.games[1].map` from §4), and 100% is the match-over
state. (The trailing literal word "doctrines" in every readout is the `#bc16-doctrines-toggle`
"reopen doctrines panel" chip's own button label, a sibling DOM node inside the same `#clock`
container the smoke script reads with a single `querySelector`, not part of the clock/caption
text itself — confirmed by reading `client/replay_broadcast.html:3945` in the coworld repo, where
that hidden-by-default toggle button is unhidden once the doctrine overlay self-dismisses on
first playback, exactly as `design.md` describes.)

10-second unattended soak (three samples, first/middle/last, from attempt 2's default 90s load
window plus explicit `-f soak=10`):
```json
"soak": {
  "seconds": 10, "moved": true,
  "before":  {"clock": "2:32 GAME 1 OF 2 — VOLUTED doctrines", "tick": "round 2 / 3000"},
  "middle":  {"clock": "2:24 GAME 1 OF 2 — VOLUTED doctrines", "tick": "round 194 / 3000"},
  "after":   {"clock": "2:22 GAME 1 OF 2 — VOLUTED doctrines", "tick": "round 242 / 3000"}
}
```
`round 2 → 194 → 242` over the 10-second unattended window: genuine, monotonic, unattended
playback advancement, independent confirmation beyond the scrub readouts alone.

`failure`: `null`. No `#scrub`-absent caveat applies — `has_scrub` was true and the scrub loop ran.

**Item 8, sub-criterion 1 (`loaded: true`): TRUE.**
**Item 8, sub-criterion 2 (three clock readouts differ): TRUE** on attempt 2's evidence (the
canonical, committed run). Attempt 1's apparent 50%/100% tie is explained by attempt 2's own
100%-readout `settle_ms: 1505` (over double attempt-1's fixed-700ms budget) — the Worker's
re-simulation of a deep seek on a 3000-round replay genuinely needs more than 700ms, exactly the
precedent the tool's own source comments document from the bc21 run. Not an unresolved
contradiction: the same replay, same URL, with a settle budget sized to the seek cost, shows
clean monotonic advancement on every axis (clock, game index, map name, round tick) and matches
the soak's independent evidence.

**Item 8 overall: TRUE.**

### (c) Replay JSON reconciliation (from `/tmp/ep.replay`, §4)

Early events:
```
0	null	episode_start	
0	null	doctrine_requested	
0	null	doctrine_requested	
5686	null	doctrine_received	
5686	null	doctrine_received	
```
(`.summary`/`.say`/`.action` are absent on these event kinds; the raw `kind` and `ms` fields carry
the information, shown above with `.tick`/`.seat` empty since this replay's events use `kind`/`ms`
rather than the generic `tick`/`seat`/`type` shape the prompt template assumes.)

`.result` (already quoted in full in §4): two games, `voluted` (archons_destroyed at round 641,
winner 1) then `closequarters` (more_archons tiebreak at round 3000, winner 1), matching the
viewer's own game-1→game-2→match-over progression exactly.

### (d) Spectator-judgment paragraph

**The rendered screenshot (`viewer-smoke.png`, attempt 2, at scrub 100% / match-over) is
legible and shows the game's own chrome, not a different product's.** It has the starter's
transport strip at the bottom (play/pause, speed chips `1×`–`16×`, a scrubber with a coloured
momentum graph above the track, a `+25`/`spoilers` toggle, `round 2999 / 3000` tick readout) —
the same layout family the brief describes for paintbot/raid/hive. The top scorebug shows both
factions by their in-game alias **and** real player name side by side — `CLAN ASH` / `daveey` on
the left, `CLAN BASIL` / `daveey-1` on the right, each with their sealed doctrine's one-line motto
("Wall the horde; hold to 3000." / "Infect, convert, overwhelm.") and a live score number, exactly
matching design.md's two-namespace convention (year-neutral alias in-game, real name
spectator-side). The centre banner correctly reads `FINAL` / `MATCH OVER` at 100% scrub. The
endcard is open and legible: a `Clan Ash` vs `Clan Basil` doctrine-sheet comparison in the same
plain-words register design.md specifies ("holds its archons together behind a guard wall",
"parks scouts between the dens and itself to pull the horde"), followed by a full box score —
archons started/lost/left, parts collected/banked/worth, units built by type, dens destroyed,
infections suffered/inflicted **and** "61 of its own [units] stood back up on the horde's side"
(bc16's signature zombie-conversion mechanic, legible in plain English), damage dealt/taken
broken out enemy-vs-horde, and rubble cleared/created. A killfeed-style scroll of recent beats is
visible at the right ("Game 2 — Clan Basil wins (more archons)", "ROUND 2999 — more archons
decides it: archons 3 to 4, archon health 20725 to 34194", several "LAUNCHER DUEL" / "OUTBREAK 9"
lines fading toward the top, consistent with the spoiler gate revealing beats as the playhead
passes them). This **is** the bc16-specific chrome design.md asked for (`#bc16-archons`/
`#bc16-horde`/`#bc16-econ` register, this year's nouns "archon"/"parts"/"den"/"zombie"), not a
different starter's product wearing this coworld's ids — no phase-30 item-14 finding on that
axis.

**One real, reproducible content defect surfaced by this screenshot, not previously caught:** the
endcard headline for this exact match reads **"THE SINGULARITY CAME AT ROUND 3000 AND CLAN BASIL
HAD MORE ARCHONS LEFT."** "The Singularity" is bc22's ("Mutation") own lore term — its rule set
(`docs/RULES-BC22.md`) states *"At round 2000 the SINGULARITY consumes the weaker team"* — and
does not exist anywhere in bc16's design (`design.md` and, so far as this verifier read,
`docs/RULES-BC16.md`'s summary in the coworld manifest description never mention a
"Singularity"; bc16's own round limit is 3000, not bc22's 2000). Reading
`client/replay_broadcast.html`'s `endcardWinCondition()` function (line ~6848) directly: the
`more_archons` case is hard-coded to the string `'the Singularity came at round ' +
last.rounds_played + ' and ' + alias + ' had more archons left'` with **no year branch** —
`more_archons` is a tiebreak `end_reason` shared by both bc22 and bc16 (per the coworld's
`results_schema` enum, one shared value), and the shared phrasing leaks bc22's fiction into a
bc16 match whenever that specific rung decides the game, which is exactly what happened in this
live episode (game 2's `end_reason: "more_archons"`). This is a genuine spectator-facing
legibility defect: a bc16 spectator reading this endcard is told a mechanic ("the Singularity")
that has no meaning in the game they just watched. It is **not** one of the eight
definition-of-done checks and does not change any check's verdict above, but it is a load-bearing
finding this verifier is obligated to surface rather than silently pass over, per this run's own
disclosure rule for anything a check's evidence touches. **Flagging for the coordinator to route
— likely a phase-30-style fix-forward item** (guard the `more_archons` case in
`endcardWinCondition()` on `s.year`, the same pattern every other per-year noun table in that
file already uses).

---

## Summary table

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **PENDING** — 1 completed round confirmed so far (round 1); fillers-before-trigger confirmed from log.md; polling continues within the 75-min bound |
| 2 | Both champions ranked, fillers absent | **TRUE** |
| 3 | Latest round's episode request completed w/ replay | **TRUE** (round 1; will re-check against round 2 once it lands) |
| 4 | Replay bytes valid, protocol matches, non-degenerate | **TRUE** |
| 5 | Hosted game log clean | **TRUE** |
| 6 | Public page / static replay path | **TRUE** (via `/coworlds/replays/session` fallback, both `softmax.com/battlecode` and `softmax.com/battlecode/bc16` client-rendered) |
| 7 | Certification declared static bundle | **TRUE** (from committed `release-result.json`) |
| 8 | Spectator judgment — viewer executed | **TRUE** (`loaded:true`, three clock readouts differ, soak confirms monotonic advancement; one non-blocking content defect noted — bc22 "Singularity" phrase leaking into a bc16 `more_archons` endcard) |

**STATE values for the coordinator to write:**
- `verify.rounds[]`: `["round_5a5bf68d-9904-4f7e-a4ec-1fe95e582f74"]` so far (will append round 2's
  id once §1 closes)
- `verify.replay`: `https://softmax-public.s3.amazonaws.com/replays/7390ce0d-8e56-422a-8914-1196c9e654a5.replay`
- `verify.iframe_static`: `true`
- `verify.viewer_check_run`: `34357018290` (the evidence-of-record run; `34356511853` was
  attempt 1, superseded, not committed)
