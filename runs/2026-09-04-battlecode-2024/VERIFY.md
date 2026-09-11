# VERIFY — battlecode-2024   (2026-09-11T02:24:00Z)

Verdict: all-true (8/8)

Coworld: `battlecode` (year variant `bc24`, softmax.com/battlecode/bc24) — league
`league_8f4f934c-c3ae-4db2-9470-927ba356a3ee`, division `div_8e76c71d-10ae-4e37-863f-f2bb4b8aa24b`,
cow_id `cow_b9c9aab2-42ac-4606-b1e6-442841de04de`, version 0.11.0, release sha
`4bcb8db628a731a446980270159b540ffb380c09` (release run 34552459781).
Champions: `battlecode-bc24-fortress:v7` (daveey) / `battlecode-bc24-flagrush:v7` (daveey-1).
Fillers registered 02:07:00Z: `battlecode-gone-sharkin:v7`, `battlecode-examplefuncsplayer24:v7`.

---

## 1. ≥2 completed rounds after fillers were set

```
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}"
```
```json
[
  {
    "id": "round_741956f9-8622-4dec-9d9d-64baebf4cd07",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "completed_at": "2026-09-11T02:15:17.474598Z"
  },
  {
    "id": "round_958dff29-905a-45be-9e62-3fd12f015d76",
    "round_number": 1,
    "status": "completed",
    "error": null,
    "completed_at": "2026-09-11T02:08:17.082032Z"
  }
]
```
`jq -r '[.[]|select(.status=="completed")]|length'` → `2`.

Both rounds' `created_at`/completion times (02:08:17Z, 02:15:17Z) are after the fillers were set
(02:07:00Z per log.md, and the round-1 trigger itself fired at 02:07:17Z, seventeen seconds after
the filler-policies POST). Neither round has `error` set; both `status == "completed"`.

**TRUE** — 2 completed rounds (round_number 1 and 2), both after fillers were registered.

---

## 2. Both champions ranked

```
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey		battlecode-bc24-fortress:v7	1030.5304984710244	2	2.0
2	daveey-1	battlecode-bc24-flagrush:v7	969.4695015289755	2	2 (0.0)
```
Full pasted rows:
```json
[
  {"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
   "score":1030.5304984710244,"rounds_played":2,"episode_wins":2.0,"win_rate":1.0,
   "policy_label":"battlecode-bc24-fortress:v7"},
  {"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
   "score":969.4695015289755,"rounds_played":2,"episode_wins":0.0,"win_rate":0.0,
   "policy_label":"battlecode-bc24-flagrush:v7"}
]
```
Both `daveey` and `daveey-1` present, `rounds_played == 2` (≥1) each. Only two rows total — the two
fillers do not appear at all (absent, which the spec accepts as an alternative to `Baseline` label);
this is consistent with round-robin scheduling with exactly 2 champions needing no filler seat.

**TRUE**

---

## 3. Latest round's episode request completed with a replay

```
R=round_741956f9-8622-4dec-9d9d-64baebf4cd07   # max round_number among completed = 2
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}"    # nested route (flat route 405s per playbook)
```
```json
{
  "entries": [
    {
      "id": "ereq_eed98756-65fa-4da6-9559-7361f5d5fa56",
      "status": "completed",
      "coworld_id": "cow_b9c9aab2-42ac-4606-b1e6-442841de04de",
      "round_id": "round_741956f9-8622-4dec-9d9d-64baebf4cd07",
      "replay_url": "https://softmax-public.s3.amazonaws.com/replays/29d4150a-12f4-483a-b347-65b88a76897b.replay",
      "policy_version_ids": ["daac67a6-f82e-49bf-86ab-5ffe7fac5673","2dde11c1-70bc-46c2-ab94-dcb39732e5a0"],
      "created_at": "2026-09-11T02:14:04.849505Z"
    }
  ],
  "next_cursor": null
}
```
```
curl -sS "$BASE/episode-requests/ereq_eed98756-65fa-4da6-9559-7361f5d5fa56" "${AUTH[@]}" | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/29d4150a-12f4-483a-b347-65b88a76897b.replay",
  "participants": [
    {"position":0,"policy_name":"battlecode-bc24-fortress","version":7,
     "player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","is_filler":false},
    {"position":1,"policy_name":"battlecode-bc24-flagrush","version":7,
     "player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","is_filler":false}
  ],
  "participant_scores": [{"position":0,"score":273.0},{"position":1,"score":26.0}]
}
```
`status == "completed"`, `replay_url` non-null, participants name `daveey` and `daveey-1` (this
match seated only the two champions — no filler needed since round-robin has exactly 2 entrants).

**TRUE**

---

## 4. Replay bytes are valid and show the game

```
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/29d4150a-12f4-483a-b347-65b88a76897b.replay" -o /tmp/ep.replay
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
```
→ `strict UTF-8 JSON: ok` (99,632 bytes, strict `jq -e` parse succeeded).

```
jq -r '.protocol, .format' /tmp/ep.replay
```
```
cogame.battlecode.v1
cogame-battlecode-replay
```
Matches the manifest documented in design.md §Server, player, protocol
(`"protocol":"cogame.battlecode.v1"`, `"format":"cogame-battlecode-replay"`).

Episode result (key is `.result`, singular, not `.results` — confirmed via `jq -r keys`):
```json
{
  "names": ["daveey","daveey-1"],
  "aliases": ["Clan Ash","Clan Basil"],
  "scores": [273.0, 26.0],
  "wins": [2, 0],
  "games": [
    {"map":"Randy","rounds_played":2000,"winner":0,"end_reason":"more_flag_captures","flags_captured":[2,1], "...":"…"},
    {"map":"DefaultLarge","rounds_played":1958,"winner":0,"end_reason":"capture","flags_captured":[3,0], "...":"…"}
  ],
  "seed": 1982996928,
  "year": "bc24",
  "policy_kind": ["llm","llm"],
  "sheet_defaults_applied": [[],[]],
  "fallbacks": [0, 0],
  "decision_ms": [6229, 6229],
  "sim_seconds": 2.412,
  "reason": "complete",
  "wall_clock_seconds": 13.047,
  "game_version": "GV14"
}
```
`results.reason == "complete"` (not `deadline`/`abandoned`). Per-game `end_reason` values are
`more_flag_captures` and `capture` — both on the design note's list of acceptable ladder tiebreak
reasons (design.md §End conditions: `capture`, `more_flag_captures`, `level_sum`, `more_bread`,
`coin_flip` are legitimate endings). `results.fallbacks == [0, 0]` — **neither champion seat fell
back**.

Doctrine events (this game's one-LLM-call-per-seat design, so the "decision count" is 2 by design,
not a defect — design.md: "ONE parallel batch of 2 LLM calls"):
```
jq -c '.events[]|select(.kind|test("doctrine"))' /tmp/ep.replay
```
```json
{"kind":"doctrine_requested","ms":0,"slot":0,"attempt":1,"deadline_ms":20000}
{"kind":"doctrine_requested","ms":0,"slot":1,"attempt":1,"deadline_ms":20000}
{"kind":"doctrine_received","ms":6229,"slot":0,"attempt":1,"latency_ms":6229,"defaults_applied":0,"unknown_fields":0}
{"kind":"doctrine_received","ms":6229,"slot":1,"attempt":1,"latency_ms":6229,"defaults_applied":0,"unknown_fields":0}
```
No `doctrine_retry` or `doctrine_fallback` events for either slot; `defaults_applied: 0` for both —
both champion seats' doctrine sheets are model-authored on the first attempt, not fallbacks. The
screenshot in check 8 shows the actual doctrine text read out for each clan (non-trivial, distinct
per seat), corroborating `defaults_applied: 0`.

Event kind histogram (shows actual CTF gameplay was simulated, not a stub):
```
jq -r '.events[].kind' /tmp/ep.replay | sort | uniq -c
```
```
      2 doctrine_received
      2 doctrine_requested
      1 episode_end
      1 episode_start
      8 first_action
      6 flag_captured
     42 flag_dropped
     34 flag_returned
     39 flag_taken
      2 game_end
      2 game_start
     18 mastery
      1 rout
      2 setup_end
     38 trap_wave
     12 upgrade
```

**TRUE**

---

## 5. Hosted game log is clean

```
curl -sS "$BASE/episode-requests/ereq_eed98756-65fa-4da6-9559-7361f5d5fa56/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}"
```
Raw body is the python `b'…'` byte-string-repr format described in the playbook; decoded with
`ast.literal_eval` per `===== container: X =====` block before grepping (line-based grep on the
raw reprs undercounts). Decoded containers: `coworld-init-config` (empty), `bedrock-sidecar`,
`game`, `worker` (empty).

```
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' <decoded logs> || echo CLEAN
```
→ `CLEAN`

Decoded `bedrock-sidecar` container (both LLM calls returned 200):
```
2026-09-11 02:14:38,062 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-11 02:14:41,563 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
```
Decoded `game` container:
```
battlecode config: year=bc24 pool=mixed seed=1982996928 games=3 maxRounds=2000 num_agents=2 matchBudget=340s
battlecode: seat 0 registered kind=llm label=fortress
battlecode: seat 1 registered kind=llm label=flagrush
battlecode: doctrine
battlecode llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
battlecode: match
battlecode: settled: complete
battlecode: reason=complete games=2 scores=[273.0, 26.0] sim=2.412s wall=13.047s
```
No occurrence of any of the four grep terms in any container.

**TRUE**

---

## 6. The public page uses the static replay path

Raw-HTML grep, **both** candidate URLs (hazard 1 — checked both the bare slug and the year path):
```
curl -sS "https://softmax.com/battlecode" | grep -o '<iframe[^>]*src="[^"]*"'      # -> NO IFRAME FOUND
curl -sS "https://softmax.com/battlecode/bc24" | grep -o '<iframe[^>]*src="[^"]*"' # -> NO IFRAME FOUND
```
Both pages returned HTTP 200 (1,117,889 and 1,076,373 bytes respectively) but no `<iframe>` tag is
present in the raw HTML — consistent with `observatory-api.md`'s documented finding that the page
is now client-rendered (empty grep = *unknown*, not a failure, per the prompt).

**Source used: the SSR state payload embedded in `https://softmax.com/battlecode/bc24`.** The
page's own embedded `state.playlist[0]` names our exact league, coworld and episode (confirming
this is the featured match on the **year** page, not the bc26 first-league page):
```json
{"leagueId":"league_8f4f934c-c3ae-4db2-9470-927ba356a3ee",
 "playlist":[{"episodeId":"021822c8-d5b2-474d-b773-4cd34aa08abf",
   "coworldId":"cow_b9c9aab2-42ac-4606-b1e6-442841de04de",
   "coworldName":"battlecode","coworldVersion":"0.11.0",
   "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/29d4150a-12f4-483a-b347-65b88a76897b.replay",
   "finishedAt":"2026-09-11T02:15:12.350220Z","roundNumber":2,"episodeNumber":1,
   "code":"battlecode.r2.e1",
   "matchup":{"divisionId":"div_8e76c71d-10ae-4e37-863f-f2bb4b8aa24b","divisionName":"Competition",
     "first":{"rank":1,"player_name":"daveey","policy_label":"battlecode-bc24-fortress:v7"},
     "second":{"rank":2,"player_name":"daveey-1","policy_label":"battlecode-bc24-flagrush:v7"}}}]}
```
This `replayUrl` is byte-identical to check 3's `replay_url` — the featured match **is** the round-2
episode just verified. A featured match is present (required: absence would mean fewer than two
ranked players; we have two).

The iframe `src` itself comes from the call the page's JS makes (documented in
`observatory-api.md` §Featured match / replay route) — reproduced directly rather than inferred:
```
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_b9c9aab2-42ac-4606-b1e6-442841de04de","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/29d4150a-12f4-483a-b347-65b88a76897b.replay"}'
```
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_b9c9aab2-42ac-4606-b1e6-442841de04de/sha256%3Aa8f75cf35577878ed80694c2b0383b18c3fe7de547b44dbb80bb25e91e9c471d/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F29d4150a-12f4-483a-b347-65b88a76897b.replay","ready":true}
```
`ready: true`. The path is `…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?v=2#replay=<s3 url>`
— the **static** route (fragment form, documented as equivalent to `?replay=` since 2026-08-28),
**never** a `/client/replay` pod URL. `<sha>` (`sha256:a8f75cf3…c471d`) matches
`STATE.coworld.manifest_sha` exactly.

Cross-check (documented fallback, for completeness — `featured_match`/`replay_viewer` are `null`
platform-wide per the playbook and are not evidence, but `canonical` confirms the cow_id):
```
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" | jq -r '.[]|select(.name=="battlecode")|{id,canonical,replay_viewer,featured_match}' | head -1
```
```json
{"id":"cow_b9c9aab2-42ac-4606-b1e6-442841de04de","canonical":true,"replay_viewer":null,"featured_match":null}
```

**TRUE** — static route confirmed, `ready:true`, sha matches manifest, featured match matches the
verified round-2 episode. Tested on the `bc24` year page (hazard 1 resolved: bare `/battlecode`
addresses bc26, not this league; `/battlecode/bc24` is the correct address and its SSR payload
carries the `league_8f4f934c…` id used throughout this report).

---

## 7. Certification declared the static bundle

Source: committed `runs/2026-09-04-battlecode-2024/release-result.json` (phase 40's artifact,
already present on disk in this run directory — not re-downloaded).
```
jq -r '.certify.replay_liveness' runs/2026-09-04-battlecode-2024/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```
Also present verbatim inside `.certify.output_tail`:
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```
Contains the required substring `Replay liveness: skipped (static replay bundle declared`.
`.certify.ok == true`, `.canonical == true`, `.cow_id == "cow_b9c9aab2-42ac-4606-b1e6-442841de04de"`,
`.manifest_sha == "sha256:a8f75cf35577878ed80694c2b0383b18c3fe7de547b44dbb80bb25e91e9c471d"` — all
match STATE and the checks above.

**TRUE** — read from the committed `release-result.json` (no re-download needed).

---

## 8. Spectator judgment — the viewer is EXECUTED, then judged

**(a) Dispatch.** SRC = the iframe `src` from check 6 (verbatim, `?replay=`/`#replay=` fragment
included):
```
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_b9c9aab2-42ac-4606-b1e6-442841de04de/sha256%3Aa8f75cf35577878ed80694c2b0383b18c3fe7de547b44dbb80bb25e91e9c471d/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F29d4150a-12f4-483a-b347-65b88a76897b.replay'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
```
Dispatched 2026-09-11T02:22:18Z. Found the new run by listing runs sorted by `createdAt` (not "the
latest"): `gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10`
returned a run with `createdAt: 2026-09-11T02:22:20Z` (two seconds after dispatch) —
`databaseId 34554357054` — distinguishable from the next-newest prior run at `2026-09-10T23:53:04Z`.

`gh run watch 34554357054 -R Metta-AI/coworld-builder --exit-status` → **green**, all steps passed
including "Fail if the viewer did not load", exit code 0.

Downloaded into `runs/2026-09-04-battlecode-2024/viewer-check/`:
`smoke-stdout.txt`, `smoke-stderr.txt` (empty), `viewer-smoke.json`, `viewer-smoke.png`.

**(b) Readouts, verbatim:**
```
jq -c '{loaded, ms, clock, scorebug, feed_lines}' viewer-smoke.json
```
```json
{"loaded":true,"ms":2823,"clock":"2:45 GAME 1 OF 2 — RANDY doctrines","scorebug":"CLAN ASH daveey · They never get one out. Explosives and moats hol 48 2:45 GAME 1 OF 2 — RANDY doctrines CLAN BASIL daveey-1 · First blood wins. Carry hard, die fast, repeat. 51","feed_lines":3}
```
```
jq -c '.signals' viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["ready"],"bridge_ready":true,"bridge_error":[]}
```
```
jq -r '.failure // "no failure"' viewer-smoke.json
```
```
no failure
```

Three clock readouts (0 %, 50 %, 100 % scrub):

| scrub | clock |
|---|---|
| 0 % | `2:45 GAME 1 OF 2 — RANDY doctrines` |
| 50 % | `1:22 GAME 1 OF 2 — RANDY doctrines` |
| 100 % | `0:00 GAME 2 OF 2 — DEFAULTLARGE doctrines` |

**Item 8 verdict: TRUE.** `loaded: true` (`data_replay_loaded:"true"`, bridge `ready`) **and** the
three clock readouts differ (2:45 → 1:22 → then the scrub past game 1's end rolls into game 2 at
0:00 on the DefaultLarge map) — the viewer both rendered a frame and advanced through the replay,
including across the game-1→game-2 boundary that the replay's `.result.games[]` records.

**(c) Replay events reconciled against the render** (from `/tmp/ep.replay`, check 4):
Early: `episode_start` (seed 1982996928) → `doctrine_requested`/`doctrine_received` for both
slots at ms 6229 → `game_start` (map Randy) → `first_action: spawn`/`spawn` → `flag_dropped` ×6 at
setup.
Middle (game 1, map Randy): repeated `flag_taken`/`flag_dropped`/`flag_returned`/`trap_wave`
events, `mastery` and `upgrade` events (12 upgrades total across both games at round 600/1200/1800
per the design's global-upgrade cadence) — matches the scorebug's "48"/"51" running totals visible
mid-scrub.
Late: `flag_captured` ×2 closing game 1 (`more_flag_captures`, Clan Ash/daveey winner) →
`game_start` (map DefaultLarge) → more `flag_taken`/`trap_wave`/`flag_returned` → final
`flag_captured` ×2 (`capture`, Clan Ash sweeps 3–0) → `game_end` (`"Clan Ash"`) → `episode_end`.
This matches `viewer-smoke.png`'s endcard: "CLAN ASH TOOK ALL THREE FLAGS AT ROUND 1958" and the
score line "score 273 — 26 · flags lifted 28/9 · traps built 159/87 · sprung 132/86 · dug 84/71 ·
filled 0/69 · levels 297/144 · jailed 372/1132" — these numbers are the same totals present in
`.result.games[]` (`flags_captured`, `traps_built`, `traps_triggered`, `tiles_dug`, `tiles_filled`,
`levels_end`, `ducks_jailed`), field-for-field.

**Screenshot** (`viewer-check/viewer-smoke.png`, 1280×800, full frame downloaded and reviewed):
top strip shows a `CLAN ASH` / `CLAN BASIL` scorebug with each clan's doctrine one-liner
("They never get one out. Explosives and moats hol[d]…" / "First blood wins. Carry hard, die
fast, repeat.") and running scores 83/16 visible at capture time, a `MATCH OVER` pill, and a
`doctrines` toggle pill. Center panel is the endcard: per-clan doctrine-sheet prose (full text,
not truncated, for both Clan Ash/daveey and Clan Basil/daveey-1), a headline
"CLAN ASH TOOK ALL THREE FLAGS AT ROUND 1958", aggregate stat line, and a faded "the war" summary
with per-clan totals. Bottom is a transport strip: rewind/step/play/+25/step/loop/fast-forward
buttons, a "spoilers" toggle, `round 1958 / 2000` counter, speed buttons `1×/2×/3×/4×/8×/16×`, and
a horizontal scrub bar spanning the full width with tick marks (no separately-rendered momentum
waveform is visible at this resolution/state — the bar itself is a plain filled track in this
screenshot, a legibility note rather than a functional gap since `#scrub` responded to all three
programmatic scrub calls above).

**Cosmetic issue confirmed (matches phase-30's prior finding):** zooming into the top scorebug
pill at this 1280 px width shows the `#bc24-flags` pill ("Clan Ash ●●● – ○○○ Clan Basil  0 to
win") **overlapping** the clock/status caption behind it (partially-legible "FINAL" text bleeds
through between the flag-pip glyphs). This reproduces the exact issue named in the brief
(phase 30, CI screenshot at 1280 px, endcard state) — it is a real overlap, present in this run's
own rendered evidence, not a one-off. It does not block `loaded`/motion (both hold), but it is a
legibility defect worth carrying forward, not one this verifier is authorized to fix.

**Spectator-judgment paragraph:** The viewer is legible and shows the actual game. It loads inside
2.8 seconds, the bridge reports `ready`, and scrubbing to 0 %, 50 % and 100 % produces three
distinct, monotonically-sensible clock states that cross a real game boundary (game 1 finishing on
Randy, game 2 beginning on DefaultLarge) — this is motion, not a single frozen frame. The scorebug
correctly attributes each seat to its real player name (`daveey`, `daveey-1`) with its own
doctrine-sheet one-liner and a live score tally, and the endcard's aggregate numbers
(273–26, 28/9 flags lifted, 159/87 traps, etc.) are the same numbers present in the replay JSON's
`.result.games[]`, so the picture and the record agree — nothing in the rendered screen is
invented or inconsistent with what was simulated. The chrome matches the starter's family: a
scorebug + doctrine strip, a spoilers-gated endcard headline and per-clan stat block, and a
transport strip with scrub/step/speed controls and a round counter, the same shape as
paintbot/raid/hive. The one legibility defect is the confirmed `#bc24-flags`/clock-caption overlap
in the endcard state at 1280 px noted above — cosmetic, not a load-bearing failure, but worth a
phase-30 follow-up rather than being waved through silently.

**TRUE**

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | TRUE |
| 2 | Both champions ranked, fillers absent | TRUE |
| 3 | Latest round's episode request completed w/ replay | TRUE |
| 4 | Replay bytes valid, protocol matches, no fallbacks, reason=complete | TRUE |
| 5 | Hosted game log clean (no falling back / unavailable / cut off / rejected) | TRUE |
| 6 | Public page (`/battlecode/bc24`) uses the static replay path | TRUE |
| 7 | Certification declared the static bundle (`release-result.json`) | TRUE |
| 8 | Viewer executed via `viewer-check.yml`: loaded=true, 3 differing clock readouts | TRUE |

**All eight checks TRUE. No item sends this run back to phase 30**, apart from the one cosmetic,
non-blocking legibility note under check 8 (the `#bc24-flags` pill / clock-caption overlap at
1280 px in the endcard state) already known from phase 30 and reproduced here — carried forward as
an observation, not a re-open.
