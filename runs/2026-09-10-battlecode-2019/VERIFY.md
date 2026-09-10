# VERIFY — battlecode-2019   (2026-09-10T23:54:13Z)

Verdict: 3 items false / pending — see items 1, 4, 5 below; items 2, 3, 6, 7, 8 TRUE.

Scope note: this coworld is `battlecode` (ninth year-module `bc19`), league
`league_1ce0515e-3218-4f13-a80d-e066890607db` (`bc19`), division
`div_f794f180-5b39-45fc-adcf-61b501a280cb`. Verified against released version **0.9.0**
(`cow_5657f03c-4ae9-406c-87c6-ea797645fece`, manifest
`sha256:fa770afb41e203a187691b5ab75de70990b3aebd1695b57da6986a939af37503`), built from
`f5de5bdbab21fb897f6eb4c27be76a1dced8f6bb`. All curl calls use
`-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0"`; header names
are shown, values never printed. Per the coordinator's binding brief for this dispatch: the
75-minute wait and phase-90 escalation in `prompts/60-verify.md` §Waiting are **suspended**; no
`trigger-round` or league-setting write was issued by this agent.

---

## 1. ≥2 completed rounds after fillers were set

```
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}"
```
```json
{
  "entries": [
    {
      "id": "round_aa77a013-672b-4b0b-a740-2cc8e9521241",
      "round_number": 1,
      "status": "completed",
      "scheduled_by": "ladder",
      "error": null,
      "completed_at": "2026-09-10T23:16:10.110165Z",
      "round_config": {
        "entrant_policy_version_ids": [
          "180e3b93-3442-460f-8ff7-22965047c210",
          "35935ce8-2828-4d67-826c-97b0da1399cb",
          "d179231c-078e-45f5-937d-5fd3d4c17a16"
        ]
      }
    }
  ],
  "next_cursor": null
}
```

Exactly **one** completed round exists (`round_number=1`, `status=completed`,
`completed_at=2026-09-10T23:16:10Z`), created by the ladder itself after fillers were registered
(fillers set at 2026-09-10T13:35:00Z per log.md; round created ~09:22h later at the 288-minute
cadence set by the operator to cap the coworld's daily Bedrock spend). No failed/discarded rounds
exist. The definition of done requires **≥2** completed rounds.

**Verdict: FALSE — pending round 2.** The ladder is enabled (`ladder.enabled=true`) and unpaused
(`rounds_paused_at=null`) at `round_interval_minutes=288`, so round 2 will arrive on its own
without any trigger-round call. Per the coordinator's explicit, human-operator-sourced
instruction (David Bloomin, 2026-09-10T22:41:59Z: "Do not trigger-round before" the
2026-09-11T07:00:00Z coworld-budget reset), this verifier issued **no** `POST
/leagues/$L/trigger-round` and made **no** write of any kind to the platform. A later heartbeat
must re-run this single check once round 2 exists.

---

## 2. Both champions ranked

```
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}"
```
```json
[
  {
    "rank": 1, "player_name": "daveey", "policy_label": "battlecode-bc19-saber:v1",
    "score": 1032.0, "rounds_played": 1, "episode_wins": 2.0, "win_rate": 1.0
  },
  {
    "rank": 2, "player_name": "daveey-1", "policy_label": "battlecode-bc19-preachers:v1",
    "score": 1000.0, "rounds_played": 1, "episode_wins": 1.0, "win_rate": 0.5
  },
  {
    "rank": 3, "player_name": "docxology", "policy_label": "daf-battlecode-carrier-doctrine:v2",
    "score": 968.0, "rounds_played": 1, "episode_wins": 0.0, "win_rate": 0.0
  }
]
```

Both `daveey` (champion #1, `battlecode-bc19-saber:v1`) and `daveey-1` (champion #2,
`battlecode-bc19-preachers:v1`) are ranked with `rounds_played=1 ≥ 1`. No filler policy
(`battlecode-saber:v1` / `battlecode-examplefuncsplayer19:v1`) appears on the board at all —
round 1 was a 3-way round-robin among the two champions and a third-party public entrant,
**`docxology`** running `daf-battlecode-carrier-doctrine:v2`. This is not ours and not a filler;
it is a third party who submitted into this public league, exactly as flagged in the brief. Its
presence satisfies "fillers absent or labelled Baseline" — here fillers are simply absent because
the round had enough real entrants that the scheduler did not need `insufficient_players:
filler_policy` to seat one.

**Verdict: TRUE.**

---

## 3. Latest round's episode request completed with a replay

`GET /episode-requests?round_id=$R&limit=20` (the flat route, as the coordinator's brief
specified) returned:
```
{"detail":"Method Not Allowed"}
HTTP_STATUS:405
```
This matches the documented gotcha in `playbooks/observatory-api.md` §9 ("the flat list route no
longer accepts GET at all"). Falling back to the nested route it documents:
```
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}"
```
```json
{"entries":[
  {"id":"ereq_058944b9-4152-44eb-a26f-3a98f8f35c16","status":"completed",
   "round_id":"round_aa77a013-672b-4b0b-a740-2cc8e9521241",
   "replay_url":"https://softmax-public.s3.amazonaws.com/replays/8b68a7cb-c4b1-4749-8f80-1e5a072b8ab1.replay",
   "policy_version_ids":["35935ce8-2828-4d67-826c-97b0da1399cb","d179231c-078e-45f5-937d-5fd3d4c17a16"],
   "created_at":"2026-09-10T22:57:15.224020Z"},
  {"id":"ereq_0624cbbd-68fd-4366-8229-1d028f0d5151","status":"completed",
   "replay_url":"https://softmax-public.s3.amazonaws.com/replays/e721e71f-c618-42d9-9de1-360adfd40401.replay",
   "policy_version_ids":["180e3b93-3442-460f-8ff7-22965047c210","d179231c-078e-45f5-937d-5fd3d4c17a16"]},
  {"id":"ereq_d3341475-1fba-4118-b3fb-329122b81a02","status":"completed",
   "replay_url":"https://softmax-public.s3.amazonaws.com/replays/f905fabe-3811-4a9e-b6f2-52791791de7a.replay",
   "policy_version_ids":["180e3b93-3442-460f-8ff7-22965047c210","35935ce8-2828-4d67-826c-97b0da1399cb"]}
],"next_cursor":null}
```
`.entries[0].id` = `ereq_058944b9-4152-44eb-a26f-3a98f8f35c16` — the champion-vs-champion match
(policy_version_ids `35935ce8…` = saber/daveey, `d179231c…` = preachers/daveey-1). Detail:
```
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/8b68a7cb-c4b1-4749-8f80-1e5a072b8ab1.replay",
  "participants": [
    {"position":0,"policy_name":"battlecode-bc19-saber","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","is_filler":false},
    {"position":1,"policy_name":"battlecode-bc19-preachers","version":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","is_filler":false}
  ],
  "participant_scores": [
    {"position":0,"score":450.5},
    {"position":1,"score":48.5}
  ]
}
```
`status=completed`, `replay_url` non-null, participants correctly named `daveey` and `daveey-1`
(no fillers were seated in this pairing — the other two episode requests in this round pair each
champion against `docxology` instead).

**Verdict: TRUE.**

---

## 4. Replay bytes are valid and show the game

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/8b68a7cb-c4b1-4749-8f80-1e5a072b8ab1.replay" -o /tmp/ep.replay
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
```
```
strict UTF-8 JSON: ok
```
```bash
jq -r '.protocol' /tmp/ep.replay   # -> cogame.battlecode.v1
jq -r '.result.reason' /tmp/ep.replay   # -> complete   (top-level key is "result", singular, not "results")
```
`protocol = "cogame.battlecode.v1"` matches the design note's pinned constant (design.md:1351,
1489 — this protocol id is shared, unchanged, across all bc16–bc26 modules per design.md:1319-1324
so as not to force every existing consumer to re-register). `result.reason = "complete"` (both
games reached `rounds_played: 1000` of `maxRounds: 1000`, no deadline cut).

Decision/fallback accounting (this is a **single sealed doctrine-sheet-per-seat-per-episode**
game, not a per-turn decision loop — `sheet_envelope: ["doctrine","sheet"]` — so "decisions" here
means doctrine-sheet submissions, one attempt sequence per seat):
```bash
jq -c '.events[]|select(.kind|test("doctrine"))' /tmp/ep.replay
```
```json
{"kind":"doctrine_requested","ms":0,"slot":0,"attempt":1,"deadline_ms":20000}
{"kind":"doctrine_requested","ms":0,"slot":1,"attempt":1,"deadline_ms":20000}
{"kind":"doctrine_retry","ms":20000,"slot":0,"cause":"parse"}
{"kind":"doctrine_retry","ms":20000,"slot":1,"cause":"timeout"}
{"kind":"doctrine_received","ms":11999,"slot":0,"attempt":2,"latency_ms":11999,"defaults_applied":0,"unknown_fields":0}
{"kind":"doctrine_retry","ms":11999,"slot":1,"cause":"timeout"}
{"kind":"doctrine_fallback","ms":0,"slot":1,"cause":"parse"}
```
Top-level `.result.fallbacks = [0, 1]` confirms it: **slot 0 (daveey / champion1 `saber`)** — 0
of 1 decisions fell back; the first attempt had a JSON parse error, the retry succeeded
(`defaults_applied:0, unknown_fields:0` — a full, clean LLM sheet). **Slot 1 (daveey-1 /
champion2 `preachers`)** — **1 of 1 decisions fell back**: both the first attempt and the retry
timed out waiting on the LLM transport, so the game used the scripted default doctrine for
`preachers`' entire episode. That is a **decision count of 2, fallback count of 1 — 50 % of the
decisions in this specific episode**, which is not "a small minority" by the letter of the check.

To put this single episode in the round's fuller context (both champions play twice in round 1's
3-way round robin), the other two episode requests were fetched and checked the same way:

| episode | slot0 | slot1 | fallback? |
|---|---|---|---|
| ereq_058944b9 (saber vs preachers) | daveey/saber: succeeded (retry) | daveey-1/preachers: **fell back** (2 timeouts) | 1 fallback |
| ereq_0624cbbd (docxology vs preachers) | docxology: succeeded (retry) | daveey-1/preachers: succeeded (retry, `unknown_fields:1`) | 0 fallback |
| ereq_d3341475 (docxology vs saber) | docxology: succeeded (retry) | daveey/saber: succeeded (retry, `unknown_fields:6`) | 0 fallback |

Across the round, `daveey`/saber fell back **0 of 2** times; `daveey-1`/preachers fell back
**1 of 2** times (50 %), the failure being both attempts timing out against the bedrock sidecar
in the one episode above. This is not "all fallbacks" (the majority of champion decisions this
round — 3 of 4 — used live LLM content), but the single 50 %-fallback episode selected by the
canonical `entries[0]` rule is a genuine, non-trivial defect worth flagging rather than papering
over.

Games show the champions doing the thing the game is about (castles/pilgrims/karbonite/fuel
economy, crusaders/prophets built, duels, church construction, trades):
```bash
jq -r '.result.games[0]|{map,rounds_played,end_reason,units_built,pilgrims_built,crusaders_built,prophets_built,attacks,kills,trades_executed}' /tmp/ep.replay
```
```json
{"map":"seed-0125","rounds_played":1000,"end_reason":"more_unit_health",
 "units_built":[287,65],"pilgrims_built":[134,23],"crusaders_built":[90,4],
 "prophets_built":[62,38],"attacks":[89,599],"kills":[43,258],"trades_executed":[120,120]}
```
Event stream (129 events total), early/middle/late excerpt:
```json
// early
{"kind":"episode_start","ms":0,"seed":336221279,"year":"bc19","maps":["seed-0125","seed-0035","seed-0017"],"aliases":["Clan Ash","Clan Basil"]}
{"kind":"doctrine_requested","ms":0,"slot":0,"attempt":1,"deadline_ms":20000}
// middle
{"kind":"duel","game":0,"round":444,"lost":[1,1]}
{"kind":"church_built","game":0,"round":642,"alias":"Clan Ash","x":46,"y":5,"churches":1,"enemy_half":0}
{"kind":"tiebreak","game":0,"round":1000,"rung":"more_unit_health","castles":[2,2],"health":[690,660],"worth":[453,5464]}
{"kind":"game_end","game":0,"round":1000,"winner_alias":"Clan Ash","winner_slot":0,"end_reason":"more_unit_health","points":[45,54]}
// late
{"kind":"church_lost","game":1,"round":916,"alias":"Clan Basil","x":30,"y":39,"churches":5}
{"kind":"duel","game":1,"round":952,"lost":[1,1]}
{"kind":"tiebreak","game":1,"round":1000,"rung":"more_unit_health","castles":[2,2],"health":[1890,1340],"worth":[7021,1413]}
{"kind":"game_end","game":1,"round":1000,"winner_alias":"Clan Ash","winner_slot":0,"end_reason":"more_unit_health","points":[56,43]}
{"kind":"episode_end","ms":0,"reason":"complete"}
```

**Verdict: TRUE, with a load-bearing finding for the judge.** Bytes are valid strict UTF-8 JSON,
protocol matches, `reason=complete`, and the events show real doctrine-driven play (castle
economy, duels, church construction/loss, trades, a genuine 1000-round tiebreak on unit health)
rather than a scripted stub. But **champion #2 (daveey-1 / `battlecode-bc19-preachers`) played
this entire episode on the scripted-default fallback doctrine, not an LLM-authored one** — both
of its LLM attempts timed out. Whether that is acceptable turns on check 5's finding below, which
is the same event.

---

## 5. Hosted game log is clean

Elevated header added (`X-Use-Elevated-Privileges: true`) as required. Logs are python
`b'…'` byte-string reprs per container; decoded with `ast.literal_eval`-equivalent before
grepping, per the documented gotcha (escrow, 2026-08-23).

```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}"
# decoded, then:
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/ep1_logs_decoded.txt
```
```
30:battlecode llm: seat 1 falling back to the scripted doctrine (parse)
```
Decoded `game` container in full, for context:
```
battlecode: doctrine
battlecode llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
battlecode llm: seat 0 attempt 1 failed, will retry: input(18, 3) Error: } expected
battlecode llm: seat 1 attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
battlecode llm: seat 1 attempt 2 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
battlecode llm: seat 1 falling back to the scripted doctrine (parse)
battlecode: match
battlecode: settled: complete
battlecode: reason=complete games=2 scores=[450.5, 48.5] sim=0.334s wall=37.042s
```
The other two episode requests of this round were checked the same way and are clean of the
forbidden strings (only "attempt 1 failed, will retry" lines, each followed by a successful
attempt 2 — no `falling back`/`unavailable`/`cut off`/`rejected` anywhere):
```bash
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/ereq_0624cbbd-*_decoded.txt || echo CLEAN
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/ereq_d3341475-*_decoded.txt || echo CLEAN
```
```
CLEAN
CLEAN
```

**Verdict: FALSE for the designated episode (1 of 3 this round).** This is a genuine, non-clean
log line, not the documented Bedrock-capacity exception: the forbidden pattern matched here is
`falling back` (the coworld's own retry-exhausted message), not the platform-wide `LLM provider
is unavailable` string the check's documented exception is written for, and the failure mode is
two client-side transport **timeouts** waiting on the bedrock sidecar (`Timeout was reached
POST …/invoke`) rather than a provider-unavailable error. The httpx sidecar log for this same
episode shows four `POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"` calls
completing between 22:57:34Z and 22:58:02Z, i.e. the upstream model did eventually answer within
the episode's own log window — the client's per-attempt budget was simply tighter than the
model's latency on this occasion. No cross-check against another LLM coworld's concurrent log
was performed in this run (out of scope for a bounded verifier dispatch); this finding should be
treated as unexplained rather than excused. It is fully consistent with, and is the direct cause
of, check 4's fallback finding for the same seat.

---

## 6. The public page uses the static replay path

```bash
curl -sS "https://softmax.com/battlecode" | grep -o '<iframe[^>]*src="[^"]*"'
```
```
(no output — page is client-rendered, exactly as playbooks/observatory-api.md documents
platform-wide since the lighthouse run of 2026-08-22)
```
`GET /coworlds?limit=200` confirms `replay_viewer` and `featured_match` are `null` for every
coworld row (platform-wide, not evidence either way):
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" | jq -r 'if type=="array" then . else .entries end | .[]|select(.name=="battlecode")|{id,canonical,replay_viewer,featured_match}'
```
```json
{"id":"cow_5657f03c-4ae9-406c-87c6-ea797645fece","canonical":true,"replay_viewer":null,"featured_match":null}
```
Following the documented, working fallback (playbook §Featured match / replay route): the raw
HTML's Next.js SSR payload carries `state.playlist[0]` directly. On `softmax.com/battlecode`
(the coworld's *default* league) it is:
```
"state":{"leagueId":"league_24414477-8c64-4a71-b643-f8a1ef148e29","playlist":[{"episodeId":"b8f7d3c8-…",
 "coworldId":"cow_5657f03c-4ae9-406c-87c6-ea797645fece","coworldVersion":"0.9.0",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/cf43865a-1936-4e9d-bd65-7776ee929e97.replay",
 "roundNumber":599,"matchup":{"first":{"player_name":"daveey","policy_label":"battlecode-loyalist:v1"},
 "second":{"player_name":"richard","policy_label":"co-gas-battlecode-champion-richard:v1"}}, …}]}
```
**As the brief anticipated, this featured match belongs to sibling league `bc26`**
(`league_24414477…` is `game.default_league_id`, round 599 of a long-running division, players
`daveey`/`richard` on unrelated `battlecode-loyalist`/`co-gas-battlecode-champion-richard`
policies) — **not** `bc19`. Recording it as a false negative would be wrong; instead the
bc19-specific page was fetched separately:
```bash
curl -sS "https://softmax.com/battlecode/bc19"
```
Its SSR payload:
```
"state":{"leagueId":"league_1ce0515e-3218-4f13-a80d-e066890607db","playlist":[{
 "episodeId":"2ab05cda-ddaf-4390-b337-34cfb3cac66a","coworldId":"cow_5657f03c-4ae9-406c-87c6-ea797645fece",
 "coworldVersion":"0.9.0",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/8b68a7cb-c4b1-4749-8f80-1e5a072b8ab1.replay",
 "roundNumber":1,"episodeNumber":1,"code":"battlecode.r1.e1",
 "matchup":{"divisionId":"div_f794f180-5b39-45fc-adcf-61b501a280cb",
  "first":{"player_name":"daveey","policy_label":"battlecode-bc19-saber:v1"},
  "second":{"player_name":"daveey-1","policy_label":"battlecode-bc19-preachers:v1"}}}]}
```
`softmax.com/battlecode/bc19`'s featured match **is** our round-1 champion-vs-champion episode —
`episodeId` and `replayUrl` are byte-identical to check 3's `EREQ` above. A featured match is
present on both pages (≥2 ranked players on each).

Iframe `src` was resolved via the documented session call the page's own JS makes, run against
**both** replay URLs to prove the route shape independent of which league is shown:
```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_5657f03c-…","replay_uri":"<bc26 s3 url>"}'
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_5657f03c-…","replay_uri":"<bc19 round-1 s3 url>"}'
```
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_5657f03c-4ae9-406c-87c6-ea797645fece/sha256%3Afa770afb41e203a187691b5ab75de70990b3aebd1695b57da6986a939af37503/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fcf43865a-1936-4e9d-bd65-7776ee929e97.replay","ready":true}
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_5657f03c-4ae9-406c-87c6-ea797645fece/sha256%3Afa770afb41e203a187691b5ab75de70990b3aebd1695b57da6986a939af37503/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F8b68a7cb-c4b1-4749-8f80-1e5a072b8ab1.replay","ready":true}
```
Both are `ready:true`, both are the static
`…/v2/coworlds/replays/static/<cow_id>/<manifest_sha>/index.html?v=2#replay=<s3 url>` form (the
"since 2026-08-28, fragment instead of query-string" variant the playbook documents), never a
`/client/replay` pod URL. `<sha>` = the coworld's `manifest_hash`
(`fa770afb41e203a187691b5ab75de70990b3aebd1695b57da6986a939af37503`), matching
`STATE.coworld.manifest_sha` exactly, as the playbook specifies (not the replay-viewer bundle
digest `595cc13b…`, which is a different value).

**Verdict: TRUE.** Source used: raw-HTML grep (empty, as expected — client-rendered) →
SSR-payload read (`state.playlist[0]`) on both `softmax.com/battlecode` (bc26, out of scope,
recorded for transparency) and `softmax.com/battlecode/bc19` (in scope, matches round 1
exactly) → `POST /coworlds/replays/session` for the resolved static iframe `src`.

---

## 7. Certification declared the static bundle

Read from the **committed** `runs/2026-09-10-battlecode-2019/release-result.json` (present in
the run directory; no re-download needed).
```bash
jq -r '.certify.replay_liveness' runs/2026-09-10-battlecode-2019/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```
`certify.ok = true`, `ok = true`, `canonical = true`, `secret_put` recorded true in the same
file, `cow_id`/`manifest_sha` match `STATE.json` exactly.

**Verdict: TRUE.** Source: committed `runs/2026-09-10-battlecode-2019/release-result.json`
(never `/tmp`).

---

## 8. Spectator judgment — the viewer is EXECUTED, then judged

*(a) Dispatch.* Iframe `src` from check 6 (the bc19 round-1 episode's static route):
```
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_5657f03c-4ae9-406c-87c6-ea797645fece/sha256%3Afa770afb41e203a187691b5ab75de70990b3aebd1695b57da6986a939af37503/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F8b68a7cb-c4b1-4749-8f80-1e5a072b8ab1.replay'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
```
Dispatched at `2026-09-10T23:53:02Z`. Found by sorting runs created after dispatch (never
`-L 1` blind):
```bash
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq 'sort_by(.createdAt)|reverse|.[0]'
```
```json
{"createdAt":"2026-09-10T23:53:04Z","databaseId":34544098607,"status":"in_progress"}
```
`gh run watch 34544098607 -R Metta-AI/coworld-builder --exit-status` → **green**, exit code 0,
all 10 steps passed (Load the viewer / Fail-if-not-loaded / Upload the evidence all ✓).
Downloaded and **committed** under `runs/2026-09-10-battlecode-2019/viewer-check/`:
`viewer-smoke.json`, `viewer-smoke.png`, `smoke-stdout.txt`, `smoke-stderr.txt`.

*(b) Readouts, verbatim:*
```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-09-10-battlecode-2019/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":2279,"clock":"1:23 GAME 1 OF 2 — SEED-0125 doctrines","scorebug":"CLAN ASH daveey 49 1:23 GAME 1 OF 2 — SEED-0125 doctrines CLAN BASIL daveey-1 · Mine, then march. 50","feed_lines":7}
```
```bash
jq -c '.signals' runs/2026-09-10-battlecode-2019/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["ready"],"bridge_ready":true,"bridge_error":[]}
```
```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-09-10-battlecode-2019/viewer-check/viewer-smoke.json
```

| scrub position | clock reading |
|---|---|
| 0 % | `1:23 GAME 1 OF 2 — SEED-0125 doctrines` |
| 50 % | `0:41 GAME 2 OF 2 — SEED-0035 doctrines` |
| 100 % | `FINAL MATCH OVER doctrines` |

```bash
jq -r '.failure // "no failure"' runs/2026-09-10-battlecode-2019/viewer-check/viewer-smoke.json
```
```
no failure
```

**`loaded: true`** (both `data-replay-loaded="true"` and the `coworld-replay` bridge's `ready`
fired), and the **three clock readouts differ** — game 1 mid-play → game 2 mid-play → match-over
endcard. Item 8's two hard gates both hold.

*(c) Replay JSON reconciliation* (from `/tmp/ep.replay`, check 4): the events show
`game_start(game=0, map=seed-0125)` → duels/church events through round 1000 → `game_end(game=0,
winner=Clan Ash, points=[45,54])` → `game_start(game=1, map=seed-0035)` → … → `game_end(game=1,
winner=Clan Ash, points=[56,43])` → `episode_end(reason=complete)`. This lines up exactly with
the viewer's three readouts: 0 % is inside game 1 (map `seed-0125`, matches `.result.games[0].map`
verbatim), 50 % is inside game 2 (map `seed-0035`, matches `.result.games[1].map`), 100 % is the
post-episode endcard.

**Screenshot description** (`viewer-smoke.png`, described, not re-rendered): a dark-themed
endcard reading "FINAL — daveey 56, CLAN BASIL, MATCH OVER, daveey-1 · Mine, then march. 43"
across the top scorebug; a centred "CLAN ASH — DAVEEY" panel with a callout "THE GAME ENDED ON
MORE UNIT HEALTH IN GAME 2, ROUND 1000" and "score 451 — 49 · 2 games played · 1000 rounds in the
last one"; two side-by-side sealed doctrine-sheet panels for Clan Ash/daveey and Clan
Basil/daveey-1, each rendering the actual free-text doctrine ("mines first and fights later,
wants 14 pilgrims per structure by round one hundred, …", closing with a quoted motto — Clan
Ash's is a compound description, Clan Basil's is literally `"Mine, then march."`); below that a
full numeric stat block per side (castles/churches/karbonite/fuel/units/kills/damage/barter);
a scrollable event feed on the right ("CHURCH LOST — Clan Basil's church at 30,39 …", "SKIRMISH —
1 lost to 1, game 2, round 952", etc., timestamped by round); and a bottom transport strip with
play/pause/step/speed controls (1×/2×/3×/4×/8×/15×), a scrubber bar, and a "round 1000 / 1000"
readout. This is legible and unambiguously shows the game: two sealed doctrine sheets, per-side
economy and combat stats, a round-by-round event log, and a scrub-driven clock, all consistent
with `/tmp/ep.replay`'s own numbers (score 450.5/48.5 in the replay vs. "451 — 49" on-screen,
matching to the nearest whole point). It **looks like the starter's chrome** — the same
transport strip/scrubber/scorebug/endcard shape described for paintbot/raid/hive in
`prompts/60-verify.md` §8 — not a different product wearing the same ids.

**Verdict: TRUE.**

---

## Files written / committed this run

- `runs/2026-09-10-battlecode-2019/VERIFY.md` (this file)
- `runs/2026-09-10-battlecode-2019/viewer-check/{viewer-smoke.json,viewer-smoke.png,smoke-stdout.txt,smoke-stderr.txt}`
  — the only rendered evidence from GitHub Actions run `34544098607`
  (`Metta-AI/coworld-builder`, `viewer-check.yml`), dispatched and downloaded this session.

## Summary for the coordinator

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers | **FALSE — pending round 2** (1 of 2; ladder unpaused, 288 min cadence, will self-resolve; no trigger-round issued) |
| 2 | Both champions ranked | TRUE |
| 3 | Latest round's episode request completed w/ replay | TRUE |
| 4 | Replay bytes valid, protocol matches, shows the game | TRUE, with finding: champion #2 (daveey-1/preachers) played this episode entirely on the scripted-default fallback (1 of 1 decisions in this episode, 1 of 2 across the round) |
| 5 | Hosted game log clean | **FALSE** for the designated episode — one `falling back` line, caused by two client-side LLM-transport timeouts, not the documented Bedrock-unavailable exception |
| 6 | Public page uses static replay path | TRUE (bc19-specific page `softmax.com/battlecode/bc19` featured our exact round-1 episode; bc26 default-league page recorded separately and correctly not treated as bc19 evidence) |
| 7 | Certification declared static bundle | TRUE (committed `release-result.json`) |
| 8 | Viewer executed and legible | TRUE — `loaded:true`, three differing clock readouts, screenshot matches starter chrome and the replay record |
