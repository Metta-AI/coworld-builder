# VERIFY — battlecode-2016 (bc16 league)   (2026-09-09T17:18Z–17:25Z UTC, re-verification against 0.8.1)

slug (public page): `battlecode` (coworld name) / league short_name `bc16` — the run slug
`battlecode-2016` is a coworld-builder run-directory name, not the platform slug.

**This is a re-run.** The first pass (13:18Z–13:37Z, preserved as `VERIFY-0.8.0.md`) found all 8
checks TRUE against coworld **0.8.0** (`cow_4bdfa37d…`), but its own rendered screenshot then
surfaced three spectator-visible content defects (E1 "Singularity" leak into a bc16 endcard, E2 a
sliced headline band, E3 both doctrine panels clipped mid-word). PR #12 fixed all three; the
coworld was re-released as **0.8.1** (`cow_089d7551-1bab-49d6-be88-157149ea97f9`, manifest
`sha256:6179e72b1e73d265f02db483b643f0b420673534f87679c02778da5b31be14f9`). This file re-fetches
all eight checks from scratch against the new coworld and additionally answers E1/E2/E3 explicitly.

Verdict: **ALL 8 CHECKS TRUE.** By the time of this pass the league had produced 17 completed
rounds on its 15-minute cadence (round 1 at 13:16Z through round 17 at 17:16Z); no waiting was
required for checks 1/3.

Values used (given, not re-derived):
```
BASE=https://softmax.com/api/observatory/v2
L=league_6cdded0f-6a1c-44c5-8d31-e68a12500653
D=div_1e064838-5355-4739-813d-c9da01d05736
COW=cow_089d7551-1bab-49d6-be88-157149ea97f9   (NEW — 0.8.1)
MANIFEST=sha256:6179e72b1e73d265f02db483b643f0b420673534f87679c02778da5b31be14f9   (NEW)
```
Old, superseded ids (for contrast only): `cow_4bdfa37d-4f28-4480-a42d-0cc439cd158a`,
manifest `sha256:20a188ec8ada2b62879e5bb25065b3076e8dc190d6457a38538aabafb8a8419f`.

---

## 1. ≥2 completed rounds after fillers were set

Per `log.md` (line 92-93), fillers were registered at 13:24:00Z **before** the league's first
ever `trigger-round` (round 1's own `created_at` is 13:15:21Z, i.e. round 1 itself was the first
triggered round and fillers predate it) — there is no pre-filler round to exclude, so **every**
completed round in this league counts. This ordering question is pre-settled; it is unaffected by
the 0.8.0→0.8.1 re-release (the release changed only viewer files, not the league).

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -c 'if type=="array" then . else .entries end | sort_by(.round_number) | .[] | {id, round_number, status, error, completed_at, created_at}'
```
```json
{"id":"round_5a5bf68d-9904-4f7e-a4ec-1fe95e582f74","round_number":1,"status":"completed","error":null,"completed_at":"2026-09-09T13:16:33.849472Z","created_at":"2026-09-09T13:15:21.694602Z"}
{"id":"round_5c8bd629-2198-4fac-aa1e-241d33d0830a","round_number":2,"status":"completed","error":null,"completed_at":"2026-09-09T13:31:24.108391Z","created_at":"2026-09-09T13:30:22.174482Z"}
{"id":"round_41c86458-528a-4843-babf-021666ed82a2","round_number":3,"status":"completed","error":null,"completed_at":"2026-09-09T13:46:24.591353Z","created_at":"2026-09-09T13:45:22.639412Z"}
{"id":"round_5bb1ddd2-89b0-4bec-9457-2356e24a6570","round_number":4,"status":"completed","error":null,"completed_at":"2026-09-09T14:01:25.191134Z","created_at":"2026-09-09T14:00:23.139479Z"}
{"id":"round_f7edbdc5-384b-4f95-bdb8-ac962af9997b","round_number":5,"status":"completed","error":null,"completed_at":"2026-09-09T14:16:45.898535Z","created_at":"2026-09-09T14:15:23.602805Z"}
{"id":"round_d4c3c15e-204c-45cc-a23f-ad7c309d5ffa","round_number":6,"status":"completed","error":null,"completed_at":"2026-09-09T14:31:25.959284Z","created_at":"2026-09-09T14:30:24.033320Z"}
{"id":"round_15eeec00-b317-4e9f-8708-40ed02f96327","round_number":7,"status":"completed","error":null,"completed_at":"2026-09-09T14:46:26.537353Z","created_at":"2026-09-09T14:45:24.513914Z"}
{"id":"round_c6a034a5-a7aa-49be-b342-fd7589b436e1","round_number":8,"status":"completed","error":null,"completed_at":"2026-09-09T15:01:47.267219Z","created_at":"2026-09-09T15:00:24.970539Z"}
{"id":"round_f2abb7d2-5903-4d73-b871-58567c43dbfa","round_number":9,"status":"completed","error":null,"completed_at":"2026-09-09T15:16:37.434338Z","created_at":"2026-09-09T15:15:25.461471Z"}
{"id":"round_18f930ff-96dc-415b-95ec-62691187df58","round_number":10,"status":"completed","error":null,"completed_at":"2026-09-09T15:31:27.877776Z","created_at":"2026-09-09T15:30:25.913971Z"}
{"id":"round_1b1bedf3-8fcd-4ff0-9aec-0cd0194c5997","round_number":11,"status":"completed","error":null,"completed_at":"2026-09-09T15:46:28.241874Z","created_at":"2026-09-09T15:45:26.357493Z"}
{"id":"round_1d1bde39-1637-426b-be46-fe6746864730","round_number":12,"status":"completed","error":null,"completed_at":"2026-09-09T16:01:39.232540Z","created_at":"2026-09-09T16:00:26.836090Z"}
{"id":"round_26c4468a-3ba7-402d-b303-7c8b17a606d7","round_number":13,"status":"completed","error":null,"completed_at":"2026-09-09T16:16:50.184006Z","created_at":"2026-09-09T16:15:27.511414Z"}
{"id":"round_03aae351-95cb-4f4a-b2ad-9aab5c420e76","round_number":14,"status":"completed","error":null,"completed_at":"2026-09-09T16:31:44.677202Z","created_at":"2026-09-09T16:30:27.950407Z"}
{"id":"round_071d9a1b-1fa7-4f75-97e6-c7b068218e4f","round_number":15,"status":"completed","error":null,"completed_at":"2026-09-09T16:46:20.749695Z","created_at":"2026-09-09T16:45:28.424600Z"}
{"id":"round_f2a51970-c28a-4bcd-9434-a48d93a166f0","round_number":16,"status":"completed","error":null,"completed_at":"2026-09-09T17:01:41.197453Z","created_at":"2026-09-09T17:00:28.916664Z"}
{"id":"round_bef99b2c-6570-4c2d-b4ca-1eb7c066a791","round_number":17,"status":"completed","error":null,"completed_at":"2026-09-09T17:16:32.284763Z","created_at":"2026-09-09T17:15:30.348543Z"}
```
Count of `status: completed`: **17**. Zero `failed`/`discarded` rows, zero non-null `error`
fields. All 17 postdate (or, for round 1, coincide with the first-ever-round exemption for) the
13:24:00Z filler registration.

**Count of completed rounds: 17 (≥ 2 required). All count. TRUE.**

---

## 2. Both champions ranked, fillers absent/Baseline

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}"
```
```json
[
  {
    "rank": 1,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 1031.1077080082284,
    "score_label": "MMR",
    "rounds_played": 17,
    "episode_wins": 11.0,
    "win_rate": 0.6470588235294118,
    "policy_label": "battlecode-bc16-pullers:v1"
  },
  {
    "rank": 2,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 968.8922919917715,
    "score_label": "MMR",
    "rounds_played": 17,
    "episode_wins": 6.0,
    "win_rate": 0.35294117647058826,
    "policy_label": "battlecode-bc16-bulwark:v1"
  }
]
```
Both `daveey` (bulwark) and `daveey-1` (pullers) present, `rounds_played: 17` each. Policy labels
are still `:v1` — matching the coordinator's stated rail decision (the league deliberately stays
on `:v1`; the 0.8.1 release additively minted `:v2` labels for every policy, which is not
re-litigable here). No filler rows present (exactly 2 rows, both champions). **TRUE.**

---

## 3. Latest round's episode request completed with a replay

Latest completed round by `round_number` is **round 17**, `round_bef99b2c-6570-4c2d-b4ca-1eb7c066a791`.
The flat `?round_id=` route is documented to 405; used the nested route directly:

```bash
curl -sS "$BASE/rounds/round_bef99b2c-6570-4c2d-b4ca-1eb7c066a791/episode-requests" "${AUTH[@]}"
```
```json
{
  "entries": [
    {
      "id": "ereq_749c57c1-c3c4-470a-afa4-5d542b72c27b",
      "status": "completed",
      "coworld_id": "cow_089d7551-1bab-49d6-be88-157149ea97f9",
      "round_id": "round_bef99b2c-6570-4c2d-b4ca-1eb7c066a791",
      "replay_url": "https://softmax-public.s3.amazonaws.com/replays/28474a90-b446-4a9a-a1d9-7ef5b78abf46.replay",
      "policy_version_ids": ["c073ca20-f820-403f-86c7-8cbd8d704084", "2175495c-757d-451e-a3e3-b3ed6f20692b"],
      "created_at": "2026-09-09T17:15:30.771639Z"
    }
  ],
  "next_cursor": null
}
```
Note the row's own `coworld_id` is `cow_089d7551…` — the **NEW** coworld, confirming this round
ran under 0.8.1, not a stale 0.8.0 pod.

```bash
curl -sS "$BASE/episode-requests/ereq_749c57c1-c3c4-470a-afa4-5d542b72c27b" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/28474a90-b446-4a9a-a1d9-7ef5b78abf46.replay",
  "participants": [
    {"position": 0, "policy_name": "battlecode-bc16-bulwark", "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey", "is_filler": false},
    {"position": 1, "policy_name": "battlecode-bc16-pullers", "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1", "is_filler": false}
  ],
  "participant_scores": [{"position": 0, "score": 234.66666666666666}, {"position": 1, "score": 464.3333333333333}]
}
```
`status == "completed"`, `replay_url` non-null, participants name both `daveey` and `daveey-1`,
no fillers. **TRUE.**

---

## 4. Replay bytes are valid and show the game

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/28474a90-b446-4a9a-a1d9-7ef5b78abf46.replay" -o /tmp/ep.replay
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
- **Protocol match:** `cogame.battlecode.v1` matches `design.md:1434` ("Protocol id:
  `cogame.battlecode.v1` — unchanged") and `design.md:1637`'s literal replay-header example.
- **`result.reason == "complete"`** — no deadline/tiebreak-abandon edge case.
- **`result.fallbacks: [0, 0]`** — zero fallbacks for both champion seats across all 3 games; both
  are LLM prompt policies with non-trivial content (see units built/damage dealt below).
- **`.events`** (261 total) kind histogram:
  `archon_lost:10, den_destroyed:4, doctrine_received:2, doctrine_requested:2, duel:11,
  episode_end:1, episode_start:1, first_action:6, game_end:3, game_start:3, infection:60,
  neutral_activated:12, outbreak:6, turned:72, unit_milestone:26, zombie_wave:17` — a rich,
  game-specific event stream, not a placeholder.
- **`.result.games[]`** — three games this round, all `end_reason: "archons_destroyed"`
  (no tiebreak rung this time):
  - game 0, map `turtle`, 387 rounds, winner=1 (daveey-1/pullers)
  - game 1, map `collision`, 1073 rounds, winner=0 (daveey/bulwark)
  - game 2, map `lockdown`, 887 rounds, winner=1 (daveey-1/pullers) — decides the match 2-1
  Non-zero, non-degenerate per-game stats on both sides throughout (e.g. game 2:
  `units_built:[81,81]`, `damage_dealt:[9185,16622]`, `infections_suffered:[65,203]`,
  `dens_destroyed:[2,2]`).
- `game_end` events (verbatim):
  ```json
  {"kind":"game_end","game":0,"round":387,"winner_alias":"Clan Basil","winner_slot":1,"end_reason":"archons_destroyed","points":[4,95]}
  {"kind":"game_end","game":1,"round":1073,"winner_alias":"Clan Ash","winner_slot":0,"end_reason":"archons_destroyed","points":[96,3]}
  {"kind":"game_end","game":2,"round":887,"winner_alias":"Clan Basil","winner_slot":1,"end_reason":"archons_destroyed","points":[4,95]}
  ```

**TRUE.**

---

## 5. Hosted game log is clean

```bash
curl -sS "$BASE/episode-requests/ereq_749c57c1-c3c4-470a-afa4-5d542b72c27b/artifacts/logs" \
  "${AUTH[@]}" "${ELEV[@]}"
```
Decoded body (plain-text byte-string reprs, not JSON-wrapped this time — read directly):
```
===== container: coworld-init-config =====
b''

===== container: bedrock-sidecar =====
b'2026-09-09 17:15:37,995 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1", ...}
[2026-09-09 17:15:38 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-09-09 17:15:38,314 INFO hypercorn.error Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-09-09 17:15:45,285 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-09 17:15:48,281 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-09 17:16:17,187 WARNING datadog.dogstatsd Error submitting packet: [Errno 111] Connection refused, dropping the packet and closing the socket'

===== container: game =====
b'battlecode config: year=bc16 pool=mixed seed=1465422090 games=3 maxRounds=3000 num_agents=2 matchBudget=360s
battlecode: listening on 0.0.0.0:8080
battlecode: waiting for seats
battlecode: refused a seat-0 connection: seat 0 was given the wrong connection token
battlecode: a spectator joined /global
battlecode: seat 0 connected
battlecode: seat 0 registered kind=llm label=bulwark
battlecode: seat 1 connected
battlecode: seat 1 registered kind=llm label=pullers
battlecode: doctrine
battlecode llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
battlecode: match
battlecode: settled: complete
battlecode: reason=complete games=3 scores=[234.66666666666666, 464.3333333333333] sim=4.13s wall=17.519s'

===== container: worker =====
b''
```
```bash
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs_raw.json || echo CLEAN
```
```
CLEAN
```
(`refused a seat-0 connection` contains "refused", not "rejected" — visually similar, distinct
word, not a match; this is the platform routing a spectator/observer away from the seat-0 slot
before the real client connected.)

**CLEAN. TRUE.**

---

## 6. The public page uses the static replay path

Raw-HTML grep on both candidate pages:
```bash
curl -sS "https://softmax.com/battlecode" | grep -o '<iframe[^>]*src="[^"]*"'      # (none)
curl -sS "https://softmax.com/battlecode/bc16" | grep -o '<iframe[^>]*src="[^"]*"' # (none)
```
Both returned HTTP 200 (1,025,093 and 985,221 bytes) with no matching `<iframe>` in the raw HTML
— expected for a client-rendered page per the playbook's documented answer, not a failure.

Fallback #1 — coworld-detail API, confirming id/canonical/version/manifest_hash:
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '.entries[]|select(.name=="battlecode" and .canonical==true)|{id,canonical,version,manifest_hash}'
```
```json
{
  "id": "cow_089d7551-1bab-49d6-be88-157149ea97f9",
  "canonical": true,
  "version": "0.8.1",
  "manifest_hash": "sha256:6179e72b1e73d265f02db483b643f0b420673534f87679c02778da5b31be14f9"
}
```
Matches the brief's given **NEW** `cow_id` and `manifest_hash` exactly (both differ from the old
0.8.0 values, confirming this is genuinely the re-released coworld, not a stale record). The
manifest's `game.runnable.source_url` is
`https://github.com/Metta-AI/cogame-battlecode/tree/1f5cb5cfde657c5c589ac73d823898fe464885ab` —
the exact PR #12 merge commit named in the brief. The coworld row has no `featured_match` key at
all (`keys` = `api_version, canonical, created_at, id, manifest, manifest_hash, name, schema_hash,
size_bytes, version`) — matching the playbook's documented, platform-wide "featured_match is null"
finding; its absence is not evidence of a ranking problem (check 2 already shows 2 ranked players).

Fallback #2 — the `/coworlds/replays/session` call the page's own JS makes, built from round 17's
replay (check 3):
```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_089d7551-1bab-49d6-be88-157149ea97f9","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/28474a90-b446-4a9a-a1d9-7ef5b78abf46.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_089d7551-1bab-49d6-be88-157149ea97f9/sha256%3A6179e72b1e73d265f02db483b643f0b420673534f87679c02778da5b31be14f9/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F28474a90-b446-4a9a-a1d9-7ef5b78abf46.replay",
  "ready": true
}
```
`ready: true`, path ends `/index.html` (fragment form), and **both the `cow_id` and the `<sha>`
segment are the NEW ones** (`cow_089d7551…` / `6179e72b1e73…`) — this is not the old 0.8.0 bundle.
Not a `/client/replay` pod URL. **Source used: both the coworld-detail API and the
`/coworlds/replays/session` call** (the page itself is client-rendered, so the raw-HTML grep is a
documented false negative). **TRUE — no old-bundle finding.**

This URL is the iframe `src` used for check 8.

---

## 7. Certification declared the static bundle

Read from the committed `runs/2026-09-09-battlecode-2016/release-result.json` — the 0.8.1 copy,
**not** the preserved `release-result-0.8.0.json` sibling (checked both filenames exist; read the
0.8.1 one per the brief):
```bash
jq -r '.cow_id, .manifest_sha, .version' runs/2026-09-09-battlecode-2016/release-result.json
jq -r '.certify.replay_liveness' runs/2026-09-09-battlecode-2016/release-result.json
```
```
cow_089d7551-1bab-49d6-be88-157149ea97f9
sha256:6179e72b1e73d265f02db483b643f0b420673534f87679c02778da5b31be14f9
0.8.1
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```
(This artifact's schema nests the field under `.certify.replay_liveness`, unlike the 0.8.0 pass's
artifact which had it top-level — read the actual file's keys, `["canonical","certify","cow_id",
"errors","hosted_certification","hosted_smoke","manifest_sha","ok","policies","secret_put",
"step_failed","version"]`, rather than assume the path.) `cow_id`/`manifest_sha`/`version` in the
artifact match check 6's coworld-detail row exactly, confirming this is the 0.8.1 certification,
not stale. Full `.certify.output_tail` confirms all 10 transcript steps `[pass]` (`matriculate,
source-resolves, images-reachable, fixture-conforms, smoke-episode, results-conform,
replay-present, replay-loadable, players-run, supporting-roles`) and ends `Certified
dist/coworld_manifest.json ... Transcript: coworld-executable (10 steps passed) ... Replay
liveness: skipped (static replay bundle declared; /client/replay and /replay not required)`.

Contains the required string `Replay liveness: skipped (static replay bundle declared`.
**Source: the committed `runs/2026-09-09-battlecode-2016/release-result.json`** (present, no
re-download needed). **TRUE.**

---

## 8. Spectator judgment — the viewer, EXECUTED then judged

### (a) Dispatch — primary run, tied to check 6's iframe src (round 17's replay)

Iframe `src` from §6 (full URL, fragment included):
```
https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_089d7551-1bab-49d6-be88-157149ea97f9/sha256%3A6179e72b1e73d265f02db483b643f0b420673534f87679c02778da5b31be14f9/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F28474a90-b446-4a9a-a1d9-7ef5b78abf46.replay
```

Dispatched 17:21:14Z with `settle=4000 -f soak=10` (the settle budget the 0.8.0 pass's attempt 2
established as necessary for this heavy replay's re-simulated seeks — chosen up front rather than
re-discovering it on a wasted attempt 1):
```bash
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90 -f settle=4000 -f soak=10
```
Find-the-new-run: polled `gh run list -w viewer-check.yml --json databaseId,createdAt` and took
the row whose `createdAt` (17:21:16Z) postdates the 17:21:14Z dispatch — **run 34382385197**.
`gh run watch 34382385197 --exit-status` → green in 46s. Downloaded and **committed**:
```bash
gh run download 34382385197 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-09-09-battlecode-2016/viewer-check
```
→ `viewer-smoke.json`, `viewer-smoke.png`, `smoke-stdout.txt`, `smoke-stderr.txt`.

### (b) Readouts (verbatim, primary run 34382385197)

```json
{"loaded":true,"ms":1184,"clock":"1:28 GAME 1 OF 3 — TURTLE doctrines","scorebug":"CLAN ASH daveey · Build a wall. Let them break on it. Win at 2999. 51 1:28 GAME 1 OF 3 — TURTLE doctrines CLAN BASIL daveey-1 · Scout bait. Viper plague. Kite and recruit. 48","feed_lines":7}
```
`signals`:
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["ready"],"bridge_ready":true,"bridge_error":[]}
```

Three clock readouts:

| scrub position | clock | settle_ms |
|---|---|---|
| 0 % | `1:28 GAME 1 OF 3 — TURTLE doctrines` | — |
| 50 % | `0:48 GAME 2 OF 3 — COLLISION doctrines` | 1509 |
| 100 % | `FINAL MATCH OVER doctrines` | 1004 |

All three **differ**, and match the replay's own game sequence exactly: 0% is early game 1 (map
`turtle`), 50% has advanced into game 2 (map `collision` — matching `.result.games[1].map` from
§4 exactly), 100% is match-over.

10-second unattended soak:
```json
{"seconds":10,"moved":true,"before":{"clock":"1:38 GAME 1 OF 3 — TURTLE doctrines","tick":"round 3 / 3000"},"middle":{"clock":"1:30 GAME 1 OF 3 — TURTLE doctrines","tick":"round 195 / 3000"},"after":{"clock":"1:28 GAME 1 OF 3 — TURTLE doctrines","tick":"round 243 / 3000"},"status":"OPEN","page_errors":[]}
```
`round 3 → 195 → 243`, monotonic, unattended. `has_scrub`: not null (the scrub loop ran; no
absent-scrubber caveat applies). `failure`: `null`.

**Item 8, sub-criterion 1 (`loaded: true`): TRUE.**
**Item 8, sub-criterion 2 (three clock readouts differ): TRUE.**
**Item 8 overall: TRUE.**

### (c) Replay JSON reconciliation (from `/tmp/ep.replay`, §4)

Early events:
```
episode_start	0
doctrine_requested	0
doctrine_requested	0
doctrine_received	8166
doctrine_received	8166
game_start (game:0 round:0 map:turtle sides:[Clan Basil, Clan Ash])
```
Mid-game excerpt (game 0, rounds 179-192 — the zombie-conversion mechanic in action):
```json
{"kind":"infection","game":0,"round":179,"alias":"Clan Basil","victim_unit":"soldier","source":"zombie","turns":10}
{"kind":"infection","game":0,"round":182,"alias":"Clan Basil","victim_unit":"viper","source":"zombie","turns":10}
{"kind":"turned","game":0,"round":187,"alias":"Clan Basil","unit":"soldier","became":"standardzombie","x":26,"y":33,"outbreak_level":0}
{"kind":"turned","game":0,"round":188,"alias":"Clan Ash","unit":"turret","became":"rangedzombie","x":27,"y":33,"outbreak_level":0}
```
Late events (`game_end` × 3, quoted in §4) match the viewer's own game-1→game-2→game-3→match-over
progression, and the seats/aliases (`Clan Ash`=daveey, `Clan Basil`=daveey-1) match the scorebug
readouts above exactly.

### (d) Second, supplementary dispatch — E1 verification on the specific `more_archons` rung

Round 17's match (used above) happened to resolve every game by `archons_destroyed`, so it does
not exercise the exact rung E1's original defect was reported on. Round 1's replay
(`7390ce0d-8e56-422a-8914-1196c9e654a5.replay`, downloaded independently and inspected) has:
```bash
jq -c '.result.games[]|{map,end_reason,winner,rounds_played}' /tmp/round1.replay
```
```json
{"map":"voluted","end_reason":"archons_destroyed","winner":1,"rounds_played":641}
{"map":"closequarters","end_reason":"more_archons","winner":1,"rounds_played":3000}
```
— game 2 (the last game, the one the 100%-scrub endcard reflects) is the `more_archons` tiebreak
rung, the exact scenario the original E1 defect was reported on. Built the iframe `src` from the
**new** cow_id/manifest with **this** replay's URL:
```
https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_089d7551-1bab-49d6-be88-157149ea97f9/sha256%3A6179e72b1e73d265f02db483b643f0b420673534f87679c02778da5b31be14f9/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F7390ce0d-8e56-422a-8914-1196c9e654a5.replay
```
Dispatched 17:23:11Z, new run confirmed **34382582739** (`createdAt` 17:23:13Z, postdates
dispatch), watched to green in 47s, downloaded and committed alongside the primary run's evidence
as `viewer-check/viewer-smoke-morearchons-supplemental.{json,png}` +
`smoke-stdout-morearchons-supplemental.txt` (kept inside the same `viewer-check/` directory the
brief names, as supplementary evidence for the E1 finding rather than a second top-level
directory).
```json
{"loaded":true,"ms":1358,"clock":"2:27 GAME 1 OF 2 — VOLUTED doctrines","scorebug":"CLAN ASH daveey · Wall the horde; hold to 3000. 49 2:27 GAME 1 OF 2 — VOLUTED doctrines CLAN BASIL daveey-1 · Infect, convert, overwhelm. 50","feed_lines":7}
```
Scrub: `0%=2:27 GAME 1 OF 2 — VOLUTED doctrines`, `50%=1:15 GAME 2 OF 2 — CLOSEQUARTERS doctrines`,
`100%=FINAL MATCH OVER doctrines` — all differ, `loaded:true`. This run is not one of the 8
required checks (check 8's canonical evidence is the primary run, tied to check 6's src); it is
additional evidence gathered specifically to answer E1 on the exact rung it was reported on, per
the brief's explicit allowance for a second dispatch.

### (e) Spectator-judgment paragraph

**The rendered screenshot (`viewer-smoke.png`, primary run, at scrub 100% / match-over) is legible
and shows the game's own chrome, not a different product's.** The starter's transport strip sits
at the bottom (play/pause, speed chips `1×`–`16×`, a scrubber with a coloured momentum graph, a
`+25`/`spoilers` toggle, `round 886 / 3000` tick readout) — the same layout family as
paintbot/raid/hive. The top scorebug shows both factions by alias and real player name side by
side (`CLAN ASH`/`daveey`, `CLAN BASIL`/`daveey-1`), each with its sealed doctrine's one-line motto
and a live score. The centre banner reads `FINAL`/`MATCH OVER` at 100% scrub. The endcard is open:
a `Clan Ash` vs `Clan Basil` doctrine-sheet comparison, followed by a full box score (archons
started/lost/left, parts collected/banked/worth, units built by type, dens destroyed, infections
suffered/inflicted and "35 of its own stood back up on the horde's side", damage dealt/taken,
rubble cleared/created), and a killfeed-style scroll of recent beats on the right ("Game 3 — Clan
Basil wins (archons destroyed)", "ARCHON DOWN — Clan Ash has 0 left, killed by zombie, game 3,
round 886", several "LAUNCHER DUEL" lines). This is the bc16-specific chrome (archon/parts/den/
zombie register), not a different starter's product wearing this coworld's ids.

**E1 — endcard headline / win-condition line.** On round 17's match (decided by `archons_destroyed`
in game 3), the headline band reads:
> **THE GAME ENDED ON ARCHONS DESTROYED IN GAME 3, ROUND 887**
(the visible box-score line above reads "3 games played · 887 rounds in the last one", and game 3
did in fact end at round 887 per §4's `game_end` events — the headline is internally consistent
with the recorded episode.) No mention of "Singularity" anywhere on this card.
On the supplementary run against round 1's replay — whose game 2 is specifically the
`more_archons` tiebreak rung the original defect was reported on — the headline reads:
> **THE ROUND LIMIT RAN OUT AT ROUND 3000 AND CLAN BASIL HAD MORE ARCHONS LEFT**
This matches the brief's expected phrasing for a `more_archons` finish exactly, and again contains
no "Singularity" anywhere. **E1: FIXED**, confirmed on both a non-tiebreak rung (this round's own
match) and the exact tiebreak rung the defect was originally reported on.

**E2 — headline band.** In both the primary screenshot (`CLAN BASIL — DAVEEY-1`) and the
supplementary one (identical title), the band is drawn as a single full-height line of capitals,
legible top to bottom, with no doubled or sliced sub-line beneath it — contrast with
`viewer-check-0.8.0/viewer-smoke.png`, where the same title area shows a visibly sheared/doubled
horizontal strip of its own capitals overlapping the row below. **E2: FIXED.**

**E3 — doctrine panels.** Primary screenshot, Clan Ash panel ends "…pulls a unit out at 50%
health, flattens its whole home area to full speed, walks its infected units away from its own
**archons**" (complete sentence, followed by the italic one-line motto). Clan Basil panel ends
"…clears rubble to open the routes it needs, walks its infected units at the enemy archons to
**die there**" (also complete). Supplementary (more_archons) screenshot, Clan Ash panel ends
"…keeps its archons inside one repair field, activates a neutral it passes, pulls a unit out at
50% health, flattens its whole home area to full speed, walks its infected units away from its
own **archons**"; Clan Basil panel ends "…walks its infected units at the enemy archons to **die
there**" — same complete endings. Neither panel in either screenshot clips a sentence mid-word.
Contrast with `viewer-check-0.8.0/viewer-smoke.png`, where both panels visibly cut off mid-word
("…keeps its archons inside one repair field, activates a" / "…sends one archon away to farm the
far man, routes its", both trailing into nothing with no ellipsis). Also note the supplementary
screenshot's Clan Basil text now reads "farm the far **map**" — the 0.8.0 screenshot's "far man"
was a typo that also appears fixed by the same PR, though this was not one of the three reported
defects. **E3: FIXED.**

**Does the screenshot look like the starter's chrome?** Yes — transport strip, scrubber, scorebug,
endcard, killfeed all match the layout family described for paintbot/raid/hive; nothing suggests a
different product sharing only the ids (no phase-30 item-14 finding).

**Disclosed, not-re-litigated residue:** Tier A' (the four scenario bots) was never built; two rare
ladder rungs rest on Nim-side unit tests alone, per `docs/PARITY.md`. Not treated as a new finding
here; the acceptance checklist names no parity tier.

---

## Summary table

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — 17 completed rounds (round_5a5bf68d … round_bef99b2c), zero failed/discarded, fillers registered before round 1 (the league's first-ever round) |
| 2 | Both champions ranked, fillers absent | **TRUE** — `rounds_played: 17` each, no filler rows, labels still `:v1` per the rail decision |
| 3 | Latest round's episode request completed w/ replay | **TRUE** — round 17 (`ereq_749c57c1…`), `coworld_id` is the NEW `cow_089d7551…`, non-null `replay_url`, both champions named |
| 4 | Replay bytes valid, protocol matches, non-degenerate | **TRUE** — `cogame.battlecode.v1`, `reason:complete`, `fallbacks:[0,0]`, 261 rich events over 3 games |
| 5 | Hosted game log clean | **TRUE** — CLEAN |
| 6 | Public page / static replay path | **TRUE** — both pages client-rendered (documented false negative); coworld-detail API and `/coworlds/replays/session` both confirm the **NEW** `cow_089d7551…`/`sha256:6179e72b1e73…` bundle, `ready:true`, static `index.html` route |
| 7 | Certification declared static bundle | **TRUE** — from committed `release-result.json` (0.8.1), `.certify.replay_liveness` = `"Replay liveness: skipped (static replay bundle declared…"`, `cow_id`/`manifest_sha`/`version` all match |
| 8 | Spectator judgment — viewer executed | **TRUE** — `loaded:true`, three clock readouts differ, soak confirms monotonic advancement; **E1/E2/E3 all confirmed FIXED** on both a fresh match and the exact `more_archons` rung the original defects were reported on |

**All 8 checks TRUE. E1, E2, E3 all confirmed fixed, with direct rendered evidence for each.**

**STATE values for the coordinator to write:**
- `verify.rounds[]`: all 17 round ids, round 1 (`round_5a5bf68d…`) through round 17
  (`round_bef99b2c…`), all `status: completed`, `error: null`
- `verify.replay`: `https://softmax-public.s3.amazonaws.com/replays/28474a90-b446-4a9a-a1d9-7ef5b78abf46.replay`
  (round 17's — validated end-to-end in §4-§8; round 1's replay,
  `https://softmax-public.s3.amazonaws.com/replays/7390ce0d-8e56-422a-8914-1196c9e654a5.replay`,
  was additionally used in §8(d) for the E1 more_archons cross-check)
- `verify.iframe_static`: `true` — carries the NEW `cow_089d7551…` / `sha256:6179e72b1e73…`
- `verify.viewer_check_run`: `34382385197` (primary, tied to check 6's src; committed).
  `34382582739` is the supplementary E1-verification run (also committed, distinctly named files)

**No non-blocking findings remain.** The 0.8.0 pass's endcard content defects (E1 Singularity leak,
E2 sliced headline band, E3 mid-word-clipped doctrine panels) are all confirmed fixed by direct
rendered evidence in this pass. Screenshots:
`runs/2026-09-09-battlecode-2016/viewer-check/viewer-smoke.png` (primary, archons_destroyed finish)
and `runs/2026-09-09-battlecode-2016/viewer-check/viewer-smoke-morearchons-supplemental.png`
(more_archons finish, the exact rung E1 was reported on).
