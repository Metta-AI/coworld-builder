# VERIFY — eleusis   (2026-08-23T20:50Z)

Run: `2026-08-23-eleusis` · slug `eleusis` · coworld `cow_39778f81-c2d7-4aab-9642-f0ef0f16990e` v`0.1.1`
League `league_0e95b506-422e-4339-9a9d-8c8a6ecdb4ea` · division `div_1aa06f49-71bf-4e57-bd88-337261abec99`
Champions: `eleusis-empiricist:v1` (daveey) / `eleusis-guarded:v1` (daveey-1) · Fillers: `eleusis-openbook:v1`, `eleusis-hoarder:v1`

**Verdict: all-true (8/8).**

Every fetch below was made fresh during this verifier session (2026-08-23T20:03Z–20:52Z). The two
documented exceptions are item 7 (read from the committed `release-result.json`) and item 8
(rendered evidence downloaded from `viewer-check.yml` runs *dispatched in this session*).

Common headers, named but never printed:

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_0e95b506-422e-4339-9a9d-8c8a6ecdb4ea
D=div_1aa06f49-71bf-4e57-bd88-337261abec99
COW=cow_39778f81-c2d7-4aab-9642-f0ef0f16990e
```

**API shape notes observed this run** (they differ from what the brief predicted, so they are
recorded rather than assumed): `GET /rounds?league_id=…` returned a **wrapped object**
`{entries, limit, offset, total_count}` on this deployment — *not* a bare array — so the prompt's
`.entries[]` jq worked verbatim. `GET /divisions/$D/leaderboard` returned a **bare JSON array**,
as `playbooks/observatory-api.md` §11 says. `GET /episode-requests?round_id=…` returned
`{entries: […]}`.

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

Fillers were registered in phase 50 **before** the first `trigger-round`. Fresh read of the
registration (this is a read that 403s on bare AUTH, so `elevated` was sent):

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"
```
```
HTTP 200
{"filler_policy_versions":[
  {"policy_version_id":"34609da6-2961-41b8-9a40-dbf91601aaab","policy_id":"00ad7855-3090-46e7-8f17-aef7c4df1be4","policy_name":"eleusis-openbook","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},
  {"policy_version_id":"72102f0f-f66f-4ca8-8a0e-74e34ac7087a","policy_id":"f3aa1786-0e5a-444e-9715-95291f6131c2","policy_name":"eleusis-hoarder","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```

Neither filler uuid is a champion uuid (`9c39d031-…` / `1bc93007-…`), so no champion can be
renamed `Baseline`.

Fresh rounds read at **2026-08-23T20:44:11Z**:

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}"    # HTTP 200; top-level type: object
jq -r '.entries|map({round_number,id,status,error,created_at,completed_at})|sort_by(.round_number)'
```
```json
[
  {"round_number":1,"id":"round_69b22fe3-dcfc-4193-92b7-ec6539ff415c","status":"failed",
   "error":"Temporal RoundWorkflow failed before settling the round.",
   "created_at":"2026-08-23T20:00:00.576757Z","completed_at":"2026-08-23T20:00:00.869185Z"},
  {"round_number":2,"id":"round_9c4a1934-9ac1-4b01-b787-2a2bc437812b","status":"completed","error":null,
   "created_at":"2026-08-23T20:00:52.048135Z","completed_at":"2026-08-23T20:07:20.878007Z"},
  {"round_number":3,"id":"round_f3495784-3587-4ca0-a5eb-1c6f2860c24a","status":"completed","error":null,
   "created_at":"2026-08-23T20:15:52.661671Z","completed_at":"2026-08-23T20:23:51.884292Z"},
  {"round_number":4,"id":"round_d16b6602-4ff0-4e34-9650-9550cfc5a86c","status":"completed","error":null,
   "created_at":"2026-08-23T20:30:53.089179Z","completed_at":"2026-08-23T20:37:19.592435Z"}
]
```
```bash
jq -r '[.entries[]|select(.status=="completed")]|length'
```
```
3
```

**Round 1 `failed`, quoted verbatim:** `"Temporal RoundWorkflow failed before settling the round."`
It fired at `20:00:00.576757Z`, ~0.3 s after the settings write and before any trigger. This is the
documented unpause/settings auto-fire (`playbooks/make-coworld.md` §Common mistakes: *"Round 1 fails
'Temporal RoundWorkflow failed before settling the round' immediately after seeding — it auto-fired
at settings time … expected, not a defect"*). It is excluded from the count.

Rounds **2, 3 and 4** completed. That fillers were live for all three is not inferred — round 2's
own episode request seats them (`"is_filler": true`, pasted under item 3's cross-check below), and
the league object returned inside the rounds payload carries
`"filler_policy_version_ids":["34609da6-2961-41b8-9a40-dbf91601aaab","72102f0f-f66f-4ca8-8a0e-74e34ac7087a"]`.
Rounds 3 and 4 were created 15 and 30 minutes after the filler write, so even discounting round 2
entirely there are **two completed rounds unambiguously after the fillers were set**.

Status: **TRUE** — 3 completed rounds (2, 3, 4), all with fillers registered; the only failure is
round 1's documented pre-filler auto-fire.

### Polling appendix (checks 1 and 3, 5-minute cadence, 75-minute bound starting 20:03Z)

```
2026-08-23T20:03:54Z poll#1 HTTP=200 completed=0 rounds="2:pending 1:failed"
2026-08-23T20:08:54Z poll#2 HTTP=200 completed=1 rounds="2:completed 1:failed"
2026-08-23T20:13:54Z poll#3 HTTP=200 completed=1 rounds="2:completed 1:failed"
2026-08-23T20:18:54Z poll#4 HTTP=200 completed=1 rounds="3:pending 2:completed 1:failed"
2026-08-23T20:23:55Z poll#5 HTTP=200 completed=2 rounds="3:completed 2:completed 1:failed"
2026-08-23T20:23:55Z DONE >=2 completed
2026-08-23T20:27:12Z poll#6 HTTP=200 completed=2 rounds="3:completed 2:completed 1:failed"
2026-08-23T20:32:12Z poll#7 HTTP=200 completed=2 rounds="4:pending 3:completed 2:completed 1:failed"
2026-08-23T20:37:13Z poll#8 HTTP=200 completed=2 rounds="4:pending 3:completed 2:completed 1:failed"
2026-08-23T20:42:13Z poll#9 HTTP=200 completed=3 rounds="4:completed 3:completed 2:completed 1:failed"
2026-08-23T20:42:13Z DONE >=3 completed
```

The bound was not reached: the second completed round landed at 20:23Z (+20 min) and a third at
20:42Z (+39 min), well inside 75 minutes.

---

## 2. Both champions ranked, fillers absent — TRUE

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}"   # HTTP 200 at 2026-08-23T20:44:18Z
```
Top-level type: `array` (bare list, as documented).

```
rank  player_name  policy_label             score               rounds_played  episode_wins
1     daveey       eleusis-empiricist:v1    1043.747133633611   3              3.0
2     daveey-1     eleusis-guarded:v1       956.2528663663891   3              0.0
```
```json
[{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1043.747133633611,"score_label":"Elo","score_value_type":"integer","rounds_played":3,"episode_wins":3.0,"episodes_played":null,"win_rate":1.0,"policy_label":"eleusis-empiricist:v1","recent_rounds":null},
 {"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":956.2528663663891,"score_label":"Elo","score_value_type":"integer","rounds_played":3,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"eleusis-guarded:v1","recent_rounds":null}]
```

Both `daveey` and `daveey-1` present, each `rounds_played = 3 ≥ 1`, each carrying its own champion
`policy_label`. The leaderboard has exactly two rows — **no filler rows at all**, which satisfies
"fillers absent or `policy_label` starting `Baseline`" by the stronger branch.

Status: **TRUE**.

---

## 3. The latest completed round's episode request completed with a replay — TRUE

Latest completed round = **round 4**, `round_d16b6602-4ff0-4e34-9650-9550cfc5a86c`.

```bash
R=round_d16b6602-4ff0-4e34-9650-9550cfc5a86c
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}"   # HTTP 200
```
```json
{"total_count":null,"entries":[
  {"id":"ereq_0622bf3b-50e7-4eb6-ad44-7e45f932aa25","status":"completed",
   "replay_url":"https://softmax-public.s3.amazonaws.com/replays/1b93518a-d9d0-4af5-8eec-055f11ec6e61.replay"}]}
```
```bash
curl -sS "$BASE/episode-requests/ereq_0622bf3b-50e7-4eb6-ad44-7e45f932aa25" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/1b93518a-d9d0-4af5-8eec-055f11ec6e61.replay",
  "participants": [
    {"position":0,"policy_name":"eleusis-empiricist","version":1,"player_name":"daveey","is_filler":false},
    {"position":1,"policy_name":"eleusis-guarded","version":1,"player_name":"daveey-1","is_filler":false},
    {"position":2,"policy_name":"eleusis-openbook","version":1,"player_name":"daveey","is_filler":true},
    {"position":3,"policy_name":"eleusis-openbook","version":1,"player_name":"daveey","is_filler":true},
    {"position":4,"policy_name":"eleusis-openbook","version":1,"player_name":"daveey","is_filler":true}
  ],
  "participant_scores": [
    {"position":0,"score":8.73913043478261},
    {"position":1,"score":6.608695652173914},
    {"position":2,"score":4.42572463768116},
    {"position":3,"score":5.592391304347828},
    {"position":4,"score":2.134057971014496}
  ]
}
```

`status == "completed"`, `replay_url` non-null, seat 0 = `daveey`, seat 1 = `daveey-1`, and the
three filler seats are flagged `is_filler: true`. Note: this endpoint reports fillers by their real
`policy_name`/`player_name` rather than the display alias `Baseline (N)`; the `Baseline (N)`
renaming is applied in the surfaces that show display names — see the replay payload's
`policyNames` in item 4, which reads
`["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)"]`, and the leaderboard in item 2,
which shows no filler row at all. Both required champion names are present.

**Cross-check for item 1** (that fillers were already live for round 2), round 2's episode request:

```bash
curl -sS "$BASE/episode-requests/ereq_01c150e2-dd62-4ac5-8e74-ed015fbf6a47" "${AUTH[@]}"
```
```json
{"position":2,"policy_name":"eleusis-openbook","version":1,"player_name":"daveey","is_filler":true},
{"position":3,"policy_name":"eleusis-hoarder","version":1,"player_name":"daveey","is_filler":true},
{"position":4,"policy_name":"eleusis-hoarder","version":1,"player_name":"daveey","is_filler":true}
```

Status: **TRUE**.

---

## 4. Replay bytes are valid and show the game — TRUE

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/1b93518a-d9d0-4af5-8eec-055f11ec6e61.replay" -o /tmp/ep.replay
```
```
HTTP 200 bytes=76953
```
A copy is committed at `runs/2026-08-23-eleusis/episode.replay.json` (76 953 bytes, well under 5 MB).

**Strict UTF-8 JSON**, checked twice with two independent strict parsers (a browser's tolerance is
explicitly not the bar):

```bash
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
python3 -c "b=open('/tmp/ep.replay','rb').read(); b.decode('utf-8'); print('python strict utf-8 decode: ok, %d bytes'%len(b))"
```
```
strict UTF-8 JSON: ok
python strict utf-8 decode: ok, 76953 bytes
```

**Protocol and reason:**

```bash
jq -r '.protocol, .results.reason' /tmp/ep.replay
```
```
eleusis.replay.v1
complete
```

`eleusis.replay.v1` is the protocol the design note and the shipped code declare
(`runs/2026-08-23-eleusis/design.md` L470 and L473 — *"Replay payload (`eleusis.replay.v1`)"*;
`cogame-eleusis/src/eleusis/server.nim:569` and `replay-viewer/eleusis_replay.nim:54` both emit it).
`results.reason == "complete"` is the primary legal value; the manifest's
`game.results_schema.properties.reason.enum` is `["complete","deadline"]`, so **no `deadline`
exception was needed this run**.

**Decision counts.** The prompt's literal jq is pasted first, with its zero explained rather than
silently replaced:

```bash
jq -r '[.events[]|select(.type=="decision")]|length' /tmp/ep.replay
```
```
0
```

This game emits no event with `type == "decision"`; its events carry `kind`, and the decision kinds
are `experiment` / `skip` / `answer` (design.md §Resolution order; the `/global` protocol string in
the manifest enumerates `kind: start|round|experiment|skip|disclose|test|answer|settle|end`).
Counted on the real key:

```bash
jq -c '[.events[].kind]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.replay
jq -r '[.events[]|select(.kind=="experiment" or .kind=="skip" or .kind=="answer")]|length' /tmp/ep.replay
jq -r '[.events[]|select((.kind=="experiment" or .kind=="skip" or .kind=="answer") and .fallback==true)]|length' /tmp/ep.replay
jq -r '[.events[]|select(.fallback==true)]|length' /tmp/ep.replay
```
```
{"answer":20,"disclose":94,"end":1,"experiment":94,"round":24,"settle":4,"skip":26,"start":1,"test":4}
140
0
0
```

**140 decisions, 0 fallbacks — zero, not "a small minority".** Per seat:

```bash
jq -r '[.events[]|select(.kind=="experiment" or .kind=="skip" or .kind=="answer")]
       |group_by(.seat)|map({seat:.[0].seat, decisions:length,
                             scripted:([.[]|select(.scripted==true)]|length),
                             fallback:([.[]|select(.fallback==true)]|length)})' /tmp/ep.replay
```
```json
[{"seat":0,"decisions":28,"scripted":0,"fallback":0},
 {"seat":1,"decisions":28,"scripted":0,"fallback":0},
 {"seat":2,"decisions":28,"scripted":28,"fallback":0},
 {"seat":3,"decisions":28,"scripted":28,"fallback":0},
 {"seat":4,"decisions":28,"scripted":28,"fallback":0}]
```

Seats 0 and 1 are the champions (`policyNames[0]="daveey"`, `[1]="daveey-1"`): **28/28 decisions
each, none scripted, none fallback.** Seats 2–4 are the scripted baselines, which is what they are
for.

**Champion decisions are non-trivial** — two verbatim seat-0/seat-1 events:

```json
{"kind":"experiment","round":2,"seat":0,"strip":"RRRR","verdict":"pass","cost":1.0,"scripted":false,"fallback":false,
 "hypothesis":"CONTAINS R — the machine passes strips with at least one red token",
 "text":"Round 2: Published RBGY (PASS) to establish baseline. Now testing RRRR to narrow the rule space. Key candidates: CONTAINS R, AT-LEAST-2 R, PARITY R even, STARTS R, HAS-REPEAT, NO-REPEAT, ENDS-DIFFER. If RRRR passes, rules like CONTAINS R, HAS-REPEAT, STARTS R become more likely. If RRRR fails, we can rule out CONTAINS R and focus on position/repeat rules. Publishing RBGY early while it's novel; rivals hypothesized CONTAINS R so this may earn citations later if they're wrong. Shortlist remains wide; splitting experiments are highest priority."}

{"kind":"experiment","round":2,"seat":1,"strip":"BBBB","verdict":"fail","cost":1.0,"scripted":false,"fallback":false,
 "hypothesis":"Exploring monochromatic patterns and basic structural constraints.",
 "text":"RRRR passed. Three rivals (Piston, Tinker, Widget) already published CONTAINS R hypothesis. If BBBB fails, it suggests the rule is specific to R, narrowing it significantly. If BBBB passes, it points toward a broader pattern (monochromatic, all-same, etc.). Hoarding this to maintain information advantage. After BBBB result, will strategically test strips that can disambiguate between leading candidates while gathering data before the first prediction test at round 6."}
```

That is the game the design describes: pay $1, read the verdict privately, decide next turn whether
to publish or hoard, and reason toward the hidden rule. `results.hoarded` is `[0,3,0,0,0]` — the
`eleusis-guarded` champion actually used the hoarding mechanic three times.

Status: **TRUE** — strict-parseable, protocol matches, `reason == "complete"`, both champion seats
100 % LLM-driven with substantive content and zero fallbacks.

---

## 5. Hosted game log is clean — TRUE

```bash
curl -sS "$BASE/episode-requests/ereq_0622bf3b-50e7-4eb6-ad44-7e45f932aa25/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs4.raw
```
```
HTTP 200 bytes=122865
```

The body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it was
**decoded before grepping** (`ast.literal_eval` per repr — a line-based grep on the raw bytes
undercounts):

```
container coworld-init-config          decoded_chars=0     lines=1
container bedrock-sidecar              decoded_chars=115027 lines=228
container game                         decoded_chars=7275  lines=178
container worker                       decoded_chars=0     lines=1
```
```bash
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs4.txt || echo CLEAN
```
```
CLEAN
```

Zero matches for all four patterns. Corroborating counts over the decoded sidecar log — every
Bedrock call succeeded:

```bash
grep -o '"ok":[a-z]*' /tmp/logs4.txt | sort | uniq -c
grep -o '"status_code":[0-9]*' /tmp/logs4.txt | sort | uniq -c
grep -o '"error_kind":[^,]*' /tmp/logs4.txt | sort | uniq -c
```
```
     56 "ok":true
     56 "status_code":200
     56 "error_kind":null
```

Game container, verbatim head and the pacing markers (an LLM game that finishes in ~20 s is playing
scripted; this one ran 329 s of sim with four prediction tests):

```
===== container: game =====
eleusis: seed not pinned; randomized
eleusis: seats=5 rounds=24 testEvery=6 testStrips=6 model=claude-sonnet-5
eleusis: serving on 0.0.0.0:8080
eleusis: player slot 0 connected (1/5)
eleusis: player slot 1 connected (2/5)
eleusis: slot 0 delivered a prompt (654 chars)
eleusis: slot 1 delivered a prompt (508 chars)
…
eleusis: prediction test 1 at 77s
eleusis: prediction test 2 at 161s
eleusis: prediction test 3 at 245s
eleusis: round 24 of 24 at 317s
eleusis: prediction test 4 at 329s
eleusis: episode complete, shutting down
```

No documented exception was needed: nothing platform-wide had to be cited because there was nothing
to excuse.

Status: **TRUE**.

*Non-blocking observation for the coordinator:* the game's startup banner prints
`model=claude-sonnet-5` while every sidecar record for the episode names
`global.anthropic.claude-haiku-4-5-20251001-v1:0`. The calls all returned 200 and no fallback fired,
so this is cosmetic — a stale label in the banner, not a routing defect — but it is misleading in a
log a human reads.

---

## 6. The public page uses the static replay path — TRUE

**Source A — raw HTML grep (the prompt's first command):**

```bash
curl -sS "https://softmax.com/eleusis" | grep -o '<iframe[^>]*src="[^"]*"'
```
```
HTTP 200 bytes=405967   (fetched 2026-08-23T20:45:04Z)
(no match)
```

Per `prompts/60-verify.md` §6 and `playbooks/observatory-api.md` §Featured match, an empty grep here
is **unknown, not a failure**: the page is client-rendered for the iframe and the raw HTML finds
nothing for any coworld. Recorded, then the two documented fallbacks were used.

**Source B — the SSR payload's `state.playlist[0]` (the featured match):** extracted from the same
fetched HTML.

```json
{
  "episodeId": "2c3a10f2-95cd-4db3-90e5-fad6d1c6e6bb",
  "coworldId": "cow_39778f81-c2d7-4aab-9642-f0ef0f16990e",
  "coworldName": "eleusis",
  "coworldVersion": "0.1.1",
  "replayUrl": "https://softmax-public.s3.amazonaws.com/replays/1b93518a-d9d0-4af5-8eec-055f11ec6e61.replay",
  "finishedAt": "2026-08-23T20:37:09.290239Z",
  "roundNumber": 4,
  "episodeNumber": 1,
  "code": "eleusis.r4.e1",
  "matchup": {
    "divisionId": "div_1aa06f49-71bf-4e57-bd88-337261abec99",
    "divisionName": "Competition",
    "first":  {"rank":1,"player_name":"daveey","score":1043.747133633611,"score_label":"Elo","rounds_played":3,"episode_wins":3,"win_rate":1,"policy_label":"eleusis-empiricist:v1"},
    "second": {"rank":2,"player_name":"daveey-1","score":956.2528663663891,"score_label":"Elo","rounds_played":3,"episode_wins":0,"win_rate":0,"policy_label":"eleusis-guarded:v1"}
  },
  "inspectUrl": "/observatory/v2?tab=episode-requests&detail=episode-request:ereq_0622bf3b-50e7-4eb6-ad44-7e45f932aa25",
  "outcome": "first"
}
```

A **featured match is present** (round 4, episode 1), and it is the daveey vs daveey-1 matchup —
i.e. there are two ranked players, so the "No featured match yet" failure mode does not apply. An
earlier fetch of the same page at 20:03Z showed `playlist:[]` (no round had completed then) and at
20:45Z showed round 4 — the payload tracks the ladder, it is not a static string.

For completeness, the coworld detail API the prompt names was also fetched:

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" | jq -r '.entries[]|select(.name=="eleusis")|{id,canonical,replay_viewer,featured_match}'
```
```json
{"id":"cow_39778f81-c2d7-4aab-9642-f0ef0f16990e","name":"eleusis","version":"0.1.1",
 "canonical":true,"replay_viewer":null,"featured_match":null}
```
`featured_match: null` here is the documented platform-wide behaviour (lighthouse, 2026-08-22), not
evidence about eleusis; the row does confirm the coworld is **canonical** at v0.1.1.

**Source C — the call the page's own JS makes to build the iframe `src`:**

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
 -d '{"coworld_id":"cow_39778f81-c2d7-4aab-9642-f0ef0f16990e","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/1b93518a-d9d0-4af5-8eec-055f11ec6e61.replay"}'
```
```json
HTTP 200
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_39778f81-c2d7-4aab-9642-f0ef0f16990e/sha256%3A8dd17e050d7eeea2947ca6a0d255239e5eef43222d7b745f8e53b17a9aba4995/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F1b93518a-d9d0-4af5-8eec-055f11ec6e61.replay&v=2",
  "ready": true
}
```

The path is `…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` — the **static**
route, with `ready: true`. It is **not** a `/client/replay` pod URL. `<sha>` is
`sha256:8dd17e050d7eeea2947ca6a0d255239e5eef43222d7b745f8e53b17a9aba4995` URL-encoded, which is
exactly `STATE.coworld.manifest_sha` and exactly `release-result.json`'s `manifest_sha`.

**Sources used: A (empty, recorded as unknown), B (featured match), C (iframe src).**

Status: **TRUE**.

---

## 7. Certification declared the static bundle — TRUE

Read from **the committed artifact** `runs/2026-08-23-eleusis/release-result.json` (the copy phase 40
downloaded and committed; 3 886 bytes, mtime 2026-08-23 19:53). No re-download was needed, and
`/tmp` was not consulted.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-23-eleusis/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Contains the required substring `Replay liveness: skipped (static replay bundle declared`.

Surrounding fields from the same file, to tie it to the version under test:

```bash
jq -c '{ok,version,cow_id,manifest_sha,canonical,step_failed}' runs/2026-08-23-eleusis/release-result.json
```
```json
{"ok":true,"version":"0.1.1","cow_id":"cow_39778f81-c2d7-4aab-9642-f0ef0f16990e",
 "manifest_sha":"sha256:8dd17e050d7eeea2947ca6a0d255239e5eef43222d7b745f8e53b17a9aba4995",
 "canonical":true,"step_failed":null}
```

The `cow_id` and `manifest_sha` are the ones in the item-6 iframe `src`, so the certified bundle and
the bundle the public page serves are the same bundle.

Status: **TRUE** — source: the committed `runs/2026-08-23-eleusis/release-result.json`.

---

## 8. Spectator judgment — the viewer was EXECUTED — TRUE

Two `viewer-check.yml` runs were dispatched **in this session** against the item-6 iframe `src`.
Both artifacts are committed; the second is the decisive one and lives at
`runs/2026-08-23-eleusis/viewer-check/`, the first at
`runs/2026-08-23-eleusis/viewer-check/attempt-1-run32665381318/`.

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_39778f81-c2d7-4aab-9642-f0ef0f16990e/sha256%3A8dd17e050d7eeea2947ca6a0d255239e5eef43222d7b745f8e53b17a9aba4995/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F1b93518a-d9d0-4af5-8eec-055f11ec6e61.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0]'      # not "the latest run" blind — sorted by createdAt
```
```
dispatch #1 at 2026-08-23T20:45:16Z -> run 32665381318 created 2026-08-23T20:45:17Z  (success, 35s)
dispatch #2 at 2026-08-23T20:48:37Z -> run 32665552865 created 2026-08-23T20:48:38Z  (success, 31s)
gh run download <RUN> -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-23-eleusis/viewer-check…
```

### 8a. Decisive run — 32665552865

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-23-eleusis/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":1454,"clock":"ROUND 1 / 24 · 0 OF 5 IN","scorebug":"daveey $0.0 PUB 0 SEC 0 daveey-1 $0.0 PUB 0 SEC 0 Piston $0.0 PUB 0 SEC 0 Tinker $0.0 PUB 0 SEC 0 Widget $0.0 PUB 0 SEC 0","feed_lines":477}
```
```bash
jq -c '.signals' runs/2026-08-23-eleusis/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```
```bash
jq -r '.failure // "no failure"' runs/2026-08-23-eleusis/viewer-check/viewer-smoke.json
```
```
no failure
```
```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-23-eleusis/viewer-check/viewer-smoke.json
```

| scrub position | `#clock` readout |
|---|---|
| 0 %   | `ROUND 1 / 24 · 0 OF 5 IN` |
| 50 %  | `PREDICTION TEST 2 / 4 · 1 OF 5 ANSWERED` |
| 100 % | `ROUND 24 / 24 · FINAL` |

`console_tail`: `["[bridge] loading","[bridge] ready"]` — no page errors, no failed requests, no
HTTP ≥ 400 during the load.

**Both conditions hold: `loaded: true` (and by the strong signal, `data-replay-loaded="true"`, which
this shell sets only after the renderer's first drawn frame), and the three clock readouts differ.**
The shell exposes a `#scrub`, so no substitute judgment was needed.

### 8b. First run — 32665381318 — recorded because it is data

```json
{"loaded":true,"ms":1071,"clock":"ROUND 1","scorebug":"","feed_lines":0}
signals: {"data_replay_loaded":null,"data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
scrub readouts: 0%="ROUND 1"  50%="ROUND 1"  100%="ROUND 1"
failure: no failure
console_tail: ["[bridge] loading","[bridge] ready"]
```

This sample would have been **item 8 FALSE** on its own: three identical clocks, empty scorebug,
zero feed lines, and its screenshot
(`viewer-check/attempt-1-run32665381318/viewer-smoke.png`) shows the bare shell — wordmark band,
the literal HTML placeholders `ROUND 1` and `0 / 0`, an empty scorebug strip and an unpainted board.
The cause is identified, not guessed: `data_replay_loaded` was `null` while `bridge_ready` was
`true`, and `replay-viewer/static_replay.js` fires `tell("ready")` two animation frames after
`attachReplay()` is *called* — before `renderer.js`'s `makeRenderer` has finished loading its six
sprite PNGs and drawn a frame. `data-replay-loaded="true"` is set in the right place
(`client/renderer.js:1369`, inside the post-image callback). `viewer_smoke.mjs` accepts either
signal, so on a cold runner the premature bridge `ready` won by ~380 ms and the harness photographed
the shell mid-boot. Re-dispatching (retry budget: attempt 2 of 3) caught the attribute instead and
produced the fully-rendered result in 8a. All bundle assets return 200 and are individually fast
(measured this run: `assets/cog_red_front.png` 200/47 970 B, `bench_surface.png` 200/80 799 B,
`eleusis_replay.wasm` 200/187 072 B, worst single asset 1.49 s cold).

*Non-blocking phase-30 finding for the coordinator:* `static_replay.js` should emit the bridge
`ready` from inside the renderer-attached callback (or immediately after `data-replay-loaded` is
set), not from `start()`. As shipped, any host that hides its spinner on `ready` — the softmax.com
theater does — shows a blank board for the ~0.5–1.5 s the sprites take to arrive. It is a
first-impression flaw, not a correctness one; the viewer does render.

### 8c. What the viewer was asked to draw — the replay record

```bash
jq -r '.events[]|[.round,.seat,.kind,(.summary//.text//.strip//.hypothesis//"")]|@tsv' /tmp/ep.replay | head -8
```
```
		start	
1		round	
1	0	experiment	Round 1: Starting with diverse strip RBGY (all 4 colors)… Will hoard result to see verdict before publishing strategy.
1	1	experiment	Round 1: Starting with RRRR to test extreme cases… Will hoard to gather information before publishing.
1	2	experiment	GYGR
1	3	experiment	BYBR
1	4	experiment	GYGB
2		round	
```

middle (around prediction test 2):
```
12	0	skip	Round 12: No pending result. Shortlist remains {CONTAINS R} — perfectly consistent with all 45 known facts (24 PASS all contain R; 21 FAIL all lack R). Test 2 occurs after this round…
12	1	experiment	BRRR tests STARTS R (expect PASS if Piston/Tinker/Widget correct, FAIL if not)…
12	2	disclose	GBGB
12	3	disclose	RRBY
12	4	disclose	BGGY
12		test	
```

late:
```
24	0	answer	Test 4 predictions based on CONTAINS R rule… Sticking with CONTAINS R: PASS, PASS, PASS, PASS, FAIL, PASS.
24	1	answer	All 88 corkboard results confirm CONTAINS R perfectly… (5/6 predicted PASS)
24	2	answer	STARTS R — the first token is RED
24	3	answer	STARTS R — the first token is RED
24	4	answer	STARTS R — the first token is RED
24		settle	
24		end	complete
```
```bash
jq -r '.results' /tmp/ep.replay
```
```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)"],
 "scores":[8.73913043478261,6.608695652173914,4.42572463768116,5.592391304347828,2.134057971014496],
 "knowledge":[9.23913043478261,10.108695652173914,20.217391304347828,20.217391304347828,20.217391304347828],
 "credit":[10.499999999999998,7.5,8.208333333333332,9.374999999999998,5.916666666666667],
 "spend":[11.0,11.0,24.0,24.0,24.0],
 "correct":[11,12,24,24,24],"answered":[24,24,24,24,24],
 "accuracy":[0.4583333333333333,0.5,1.0,1.0,1.0],
 "published":[10,8,24,23,24],"hoarded":[0,3,0,0,0],
 "rounds":24,"maxRounds":24,"tests":4,"ruleId":44,
 "rule":"STARTS R — the first token is RED","closest":3,"closestName":"Baseline (2)",
 "reason":"complete"}
```

### 8d. Spectator judgment

**It is legible, it is moving, and it is unmistakably this game.** The committed screenshot
`runs/2026-08-23-eleusis/viewer-check/viewer-smoke.png` was taken at the 100 % scrub position and
shows a finished match, not a loading state. Top band: the `ELEUSIS` wordmark left, the match clock
`ROUND 24 / 24 · FINAL` centred, `REPLAY` status chip and a `« LOG` feed toggle right. Under it a
row of five scorebug plates — `daveey $8.7 PUB 10 SEC 0 +$10.5`, `daveey-1 $6.6 PUB 8 SEC 3 +$7.5`,
`Piston $4.4 PUB 24 SEC 0 +$8.2`, `Tinker $5.6 PUB 23 SEC 0 +$9.4`, `Widget $2.1 PUB 24 SEC 0
+$5.9` — so a spectator can read who is winning, how much each published, how much each hoarded
(SEC), and the citation credit each earned, without knowing the rules. The board shows the machine
at top-left with five cog avatars beneath it, each captioned with its money and its stated
hypothesis; the corkboard runs down the right as a stack of published four-token strips in R/B/G/Y
colour, each stamped `PASS` or `FAIL` with its round number and a `+81 earlier` overflow marker; the
prediction-test strip sits along the bottom (`TEST 4`, six strips with per-seat answer dots); and
the spectator-only drawer is labelled `SECRET · SPECTATORS ONLY · 3`, which is exactly the hidden
information the design says only the replay may reveal. The endcard is up: *"THE RULE WAS — STARTS R
— the first token is RED"*, `CLOSEST: TINKER — 24 OF 24 PREDICTIONS · ENDED COMPLETE`, over a
five-row standings table with SCORE / PRIZES / CREDIT / SPEND / ACCURACY / PUB-SEC columns. The
transport strip at the bottom carries the scrubber with its per-beat momentum graph (coloured ticks
per event, taller marks at the four tests), the play button and `268 / 268`.

Picture and record agree, and the numbers reconcile exactly. The transport's `268 / 268` is the
replay's event count (`jq -r '.events|length'` → `268`) with the playhead at the end. The corkboard
header reads `THE CORKBOARD · 91 PUBLISHED`, which is the 91 disclosure events that reached the
board — `jq '[.events[]|select(.kind=="disclose")|.mode]|group_by(.)…'` → `{"publish":89,
"duplicate":2,"hoard":3}` — with the 3 hoards correctly kept off it and in the secret drawer the
screenshot labels `SECRET · SPECTATORS ONLY · 3`. The
endcard's `STARTS R` matches `results.rule`; `CLOSEST: TINKER` matches `closestName:"Baseline (2)"`
(Tinker is seat 3's alias); the plates' money matches `results.scores` to the displayed precision
(daveey $8.7 ↔ 8.739, daveey-1 $6.6 ↔ 6.609); `PUB 10 / SEC 0` and `PUB 8 / SEC 3` match
`published:[10,8,…]` and `hoarded:[0,3,…]`. It **advances**: the three scrub readouts move from
`ROUND 1 / 24 · 0 OF 5 IN` through `PREDICTION TEST 2 / 4 · 1 OF 5 ANSWERED` to `ROUND 24 / 24 ·
FINAL`, and the 477-element feed is populated. Nothing is empty, frozen or unreadable in the
decisive run.

**Chrome provenance:** it is the bullwhip lineage, not a rewrite that shares ids. The wordmark band
with the split-colour title, the horizontal plate scorebug, the canvas stage with lightpool/grain
overlays, the feed drawer behind a `LOG` toggle, the transport strip whose scrubber is a momentum
graph rather than a plain slider, and the modal endcard with a ranked standings table are all the
paintbot/raid/hive/bullwhip furniture in the same places. Eleusis' additions — the corkboard column,
the prediction-test strip, the secret drawer — sit *inside* `#board-wrap` as extra panels; no
inherited element has been replaced. This is not the cogame-gridlock failure mode.

One spectator-legibility remark, non-blocking: the champions' epistemic story is more interesting
than the scoreboard admits. Both LLM seats converged on `CONTAINS R` while the true rule was
`STARTS R`, so their test accuracy (0.458 and 0.500) is far below the scripted baselines' 1.000 —
yet they finish 1st and 2nd on score because they spent $11 instead of $24 and harvested more
citation credit. The endcard's `ACCURACY` column makes that visible, but a spectator may need a beat
to see why the least accurate seat won. That is the game's economy working as designed, not a
defect.

Status: **TRUE** — `loaded: true` with `data-replay-loaded="true"`, three differing clock readouts,
and a rendered picture that shows the game. Decisive viewer-check run: **32665552865**.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 2, 3, 4 completed; round 1's failure is the documented pre-filler auto-fire |
| 2 | Both champions ranked, fillers absent | **TRUE** — daveey (1043.7) and daveey-1 (956.3), `rounds_played` 3 each, no filler rows |
| 3 | Latest round's episode completed with a replay | **TRUE** — `ereq_0622bf3b…` completed, replay_url present, seats 0/1 are daveey/daveey-1 |
| 4 | Replay bytes valid and show the game | **TRUE** — strict UTF-8 JSON, `eleusis.replay.v1`, `reason:"complete"`, 140 champion+filler decisions, **0 fallbacks**, champion seats 0 scripted |
| 5 | Hosted game log clean | **TRUE** — CLEAN after decoding the byte-string reprs; 56/56 Bedrock calls `ok:true` 200 |
| 6 | Public page uses the static replay path | **TRUE** — featured match `eleusis.r4.e1` present; iframe src is `…/replays/static/<cow>/<sha>/index.html?replay=…`, `ready:true` |
| 7 | Certification declared the static bundle | **TRUE** — committed `release-result.json`: `Replay liveness: skipped (static replay bundle declared; …)` |
| 8 | Viewer executed and judged | **TRUE** — run 32665552865: `loaded:true`, `data-replay-loaded="true"`, three differing clocks, legible bullwhip-lineage render |

**Iframe src:**
`https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_39778f81-c2d7-4aab-9642-f0ef0f16990e/sha256%3A8dd17e050d7eeea2947ca6a0d255239e5eef43222d7b745f8e53b17a9aba4995/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F1b93518a-d9d0-4af5-8eec-055f11ec6e61.replay&v=2`

**Replay URL:**
`https://softmax-public.s3.amazonaws.com/replays/1b93518a-d9d0-4af5-8eec-055f11ec6e61.replay`
(committed copy: `runs/2026-08-23-eleusis/episode.replay.json`, 76 953 bytes)

**viewer-check runs:** 32665552865 (decisive) and 32665381318 (first sample, kept as data)

### Non-blocking observations for the coordinator

1. **`static_replay.js` signals `ready` before the first frame.** `tell("ready")` fires two rAFs
   after `attachReplay()` is called, while the sprites are still loading; `data-replay-loaded="true"`
   is set correctly afterwards. Effect: a host that hides its spinner on `ready` shows a blank board
   for ~0.5–1.5 s, and the CI load test can photograph an un-rendered shell (it did, in run
   32665381318). Fix is one line — emit `ready` from inside `makeRenderer`'s callback.
2. **Stale model label in the game banner.** The log prints `model=claude-sonnet-5` while every
   sidecar record names `global.anthropic.claude-haiku-4-5-20251001-v1:0`. Cosmetic, but misleading.
3. **API shape drift worth adding to `playbooks/observatory-api.md`:** on this deployment
   `GET /rounds?league_id=…` returned `{entries,…}` (as the playbook says), while phase 50 observed
   `GET /leagues` returning a bare array. `GET /episode-requests/<id>` reports filler participants by
   their real `policy_name`/`player_name` with an `is_filler: true` flag, not as `Baseline (N)`; the
   `Baseline (N)` alias appears in the replay payload's `policyNames` and `results.names`.
