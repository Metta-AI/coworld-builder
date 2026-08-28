# VERIFY — procgen   (2026-08-28T21:16Z)

Verdict: **1 item false — check 5 (hosted game log)**. Checks 1, 2, 3, 4, 6, 7, 8 TRUE.

- Run `2026-08-28-procgen` · slug `procgen` · repo `Metta-AI/cogame-procgen` · version `0.1.0`
- `COW` = `cow_4d7261f4-1766-4ca3-84df-0e61eedd1b4d` · manifest `sha256:5b5bf61a91162daf850cb526ef5792a96acb61849bec503428ce8b7da86e7311`
- `L` = `league_2b1f9007-0749-4e3c-a669-a630283894f1` · `D` = `div_6efcf3a6-7551-4401-94a0-85853a797f16`
- `BASE` = `https://softmax.com/api/observatory/v2`
- Headers on every Observatory call: `Authorization: Bearer <redacted>` and `User-Agent: coworld-builder/1.0`;
  `X-Use-Elevated-Privileges: true` added on `artifacts/logs` and on the filler-policies read. No header
  value is reproduced anywhere in this file.
- **Evidence-source choices** (both are the prompt's documented fallbacks, recorded as required):
  **check 6** — the raw-HTML iframe grep and the coworld-detail API both came back empty (both pasted
  below), so the source used is the **page's own SSR payload** (`state.pool.replays[0]`, plus
  `state.divisionLeaderboard`) **+ `POST /coworlds/replays/session`**, the call the page's JS makes.
  **check 7** — the **committed** `runs/2026-08-28-procgen/release-result.json`; it was present, so the
  `gh run download` fallback (release run `33206322967`) was not needed.
- Wall clock: verification opened **20:14Z**, last round poll **21:05:49Z**, viewer-check dispatched
  **21:08Z** — **~62 min of the 75-min bound used**.
- **Round under test: round 4** (`round_850e932a-0806-4377-8e6e-050e37f07fc9`, completed
  2026-08-28T21:04:53Z), the latest completed round at fetch time.
- **This coworld is single-seat.** `design.md:188` — "**`num_agents` = 1.** Exactly one seat, always" —
  so a ladder round is **two episodes of one participant each**, not one episode of two. Checks 3–5 are
  therefore read over **both** episode requests of round 4; between them they name `daveey` and
  `daveey-1`, and each is quoted in full below. This is a shape consequence of the accepted design, not
  an exception I am inventing.

---

## Polling log

Each line is an independent `GET $BASE/rounds?league_id=$L&limit=20` (HTTP 200 every time). No round ever
reported `failed` or `discarded`, so no `error` string exists to quote.

| poll (UTC) | r1 | r2 | r3 | r4 | completed count |
|---|---|---|---|---|---|
| 20:15:46Z | pending | — | — | — | 0 |
| 20:20:41Z | **completed** 20:19:57Z | — | — | — | 1 |
| 20:26:08Z | completed | — | — | — | 1 |
| 20:31:05Z | completed | pending (created 20:27:59Z) | — | — | 1 |
| 20:36:26Z | completed | **completed** 20:34:19Z | — | — | 2 |
| 20:41:28Z | completed | completed | — | — | 2 |
| 20:46:17Z | completed | completed | pending (created 20:43:00Z) | — | 2 |
| 20:51:01Z | completed | completed | **completed** 20:50:02Z | — | 3 |
| 20:56:13Z | completed | completed | completed | — | 3 |
| 21:01:01Z | completed | completed | completed | pending (created 20:58:02Z) | 3 |
| 21:05:49Z | completed | completed | completed | **completed** 21:04:53Z | 4 |

Polls after the second completion (20:36:26Z) were the **check-5 retry budget** being spent as the prompt
directs — "3 attempts per failing check, each a different approach … (different round)". Rounds 2, 3 and 4
were each fetched and gate-grepped in turn; all four rounds fail the gate (§5).

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" -o /tmp/rounds_final.json -w "HTTP %{http_code}\n"
jq -r 'if type=="array" then . else .entries end|sort_by(.round_number)|.[]|{id,round_number,status,error,created_at,completed_at}' /tmp/rounds_final.json
jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length' /tmp/rounds_final.json
```

```
HTTP 200      (fetched 2026-08-28T21:09:36Z)
{
  "id": "round_536471b7-477d-4aa9-af0e-eb821f7a9d1c",
  "round_number": 1,
  "status": "completed",
  "error": null,
  "created_at": "2026-08-28T20:12:59.577674Z",
  "completed_at": "2026-08-28T20:19:57.817705Z"
}
{
  "id": "round_c8c024bc-68d2-48d1-a8e7-1a104078fadb",
  "round_number": 2,
  "status": "completed",
  "error": null,
  "created_at": "2026-08-28T20:27:59.955128Z",
  "completed_at": "2026-08-28T20:34:19.474730Z"
}
{
  "id": "round_db91487e-097b-4f9f-81c4-6d04aa44fdbc",
  "round_number": 3,
  "status": "completed",
  "error": null,
  "created_at": "2026-08-28T20:43:00.854511Z",
  "completed_at": "2026-08-28T20:50:02.085815Z"
}
{
  "id": "round_850e932a-0806-4377-8e6e-050e37f07fc9",
  "round_number": 4,
  "status": "completed",
  "error": null,
  "created_at": "2026-08-28T20:58:02.175846Z",
  "completed_at": "2026-08-28T21:04:53.821382Z"
}
```
```
4
```

**Fillers were in effect for every counted round.** `log.md` records them registered at 20:13:43Z,
**before** the first `trigger-round` (same log line) and therefore before round 1 was created
(20:12:59Z creation, settled by the trigger). That is the log; here is the live read, and the live
entrant list for round 4:

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"     # elevated read (403s on bare AUTH)
```
```
HTTP 200      (fetched 2026-08-28T21:09:37Z)
{"policy_version_id":"ff22a97d-757c-4444-b6fe-3c02a7030411","policy_name":"procgen-pathfinder","version":1,"player_name":"daveey"}
{"policy_version_id":"d12e5c64-6bd6-4b0d-8844-598cb1517faa","policy_name":"procgen-scavenger","version":1,"player_name":"daveey"}
```

```bash
jq -c '(if type=="array" then . else .entries end)[]|select(.round_number==4)|.round_config.entrant_attributions' /tmp/rounds_final.json
```
```
[{"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player",
  "policy_version_id":"6f123ede-f4e4-4467-ac19-bd636b1cfbb7","league_policy_membership_id":"lpm_00d11b8a-b1ca-4ca6-9a78-9968d6b229f4"},
 {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","subject_type":"player",
  "policy_version_id":"be25edba-71f3-4841-9a58-8dd644b57384","league_policy_membership_id":"lpm_c2897b60-6327-46b9-ba00-dd9305326d4a"}]
```

The two filler version ids (`ff22a97d…`, `d12e5c64…`) are disjoint from the two champion version ids
(`6f123ede…`, `be25edba…`), as the playbook requires.

**Status: TRUE** — **4** completed rounds (1 @ 20:19:57Z, 2 @ 20:34:19Z, 3 @ 20:50:02Z, 4 @ 21:04:53Z),
all four created after the fillers were registered. **Zero** rounds `failed` or `discarded`, so there is
no `error` string to record.

---

## 2. Both champions ranked; fillers absent / Baseline — TRUE

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" -o /tmp/lb.json -w "HTTP %{http_code}\n"
jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv' /tmp/lb.json
```
```
HTTP 200      (fetched 2026-08-28T21:06:15Z; bare list, not .entries)
1	daveey	procgen-cartographer:v1	1026.666828786396	4	3.0
2	daveey-1	procgen-scrambler:v1	973.3331712136038	4	1.0
```

**Status: TRUE** — both champions present with `rounds_played` 4 ≥ 1: `daveey`
(`procgen-cartographer:v1`) rank 1, 3 episode wins; `daveey-1` (`procgen-scrambler:v1`) rank 2, 1
episode win. Neither filler (`procgen-pathfinder:v1`, `procgen-scavenger:v1`) appears as a leaderboard
row — **absent**, which the checklist accepts. (Fillers are never seated in this coworld: with
`num_agents = 1` a round is one champion per episode, so `insufficient_players: filler_policy` never
fires; the filler set exists and is registered, §1.)

---

## 3. Latest round's episode requests completed with a replay — TRUE

The flat `GET /episode-requests?round_id=` route is HTTP 405 since 2026-08-26
(`playbooks/observatory-api.md` §9), so the nested route was used.

```bash
R=round_850e932a-0806-4377-8e6e-050e37f07fc9      # max_by(round_number) over completed rounds = round 4
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" -o /tmp/er4.json -w "HTTP %{http_code}\n"
jq -r 'if type=="array" then . else .entries end|.[]|[.id,.status]|@tsv' /tmp/er4.json
```
```
HTTP 200
ereq_c6fddedb-85ee-4c3b-b318-691407d9dad1	completed
ereq_4202e87d-98b9-47a1-98be-77438668dbda	completed
```

```bash
for E in ereq_c6fddedb-85ee-4c3b-b318-691407d9dad1 ereq_4202e87d-98b9-47a1-98be-77438668dbda; do
  curl -sS "$BASE/episode-requests/$E" "${AUTH[@]}" | jq '{status, replay_url, participants, participant_scores}'
done
```
```
== ereq_c6fddedb-85ee-4c3b-b318-691407d9dad1        HTTP 200
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/e8a45e7f-f234-4069-8a12-cbc720efebaa.replay",
  "participants": [
    {
      "position": 0,
      "kind": "policy",
      "policy_version_id": "be25edba-71f3-4841-9a58-8dd644b57384",
      "policy_id": "e20f8ed8-5c38-4d56-b02a-fd2076468e3a",
      "policy_name": "procgen-scrambler",
      "version": 1,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
      "player_name": "daveey-1",
      "is_filler": false,
      "is_seed": false
    }
  ],
  "participant_scores": [
    {
      "position": 0,
      "score": 0.336
    }
  ]
}
== ereq_4202e87d-98b9-47a1-98be-77438668dbda        HTTP 200
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/55bcf72a-6bca-4d88-a47b-aa34150645d5.replay",
  "participants": [
    {
      "position": 0,
      "kind": "policy",
      "policy_version_id": "6f123ede-f4e4-4467-ac19-bd636b1cfbb7",
      "policy_id": "74f3fc66-4d82-47f5-98ad-6be0ca4b46b3",
      "policy_name": "procgen-cartographer",
      "version": 1,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": false,
      "is_seed": false
    }
  ],
  "participant_scores": [
    {
      "position": 0,
      "score": 0.362
    }
  ]
}
```

**Status: TRUE** — both of round 4's episode requests are `status == "completed"` with a non-null
`replay_url`, and between them the round's `participants` name **`daveey`** (seat 0 of
`ereq_4202e87d…`, `procgen-cartographer` v1, score 0.362) and **`daveey-1`** (seat 0 of
`ereq_c6fddedb…`, `procgen-scrambler` v1, score 0.336). `is_filler` is `false` on both — correct, since
this single-seat game never seats a filler (§2). The design pins the one-seat-per-episode shape at
`design.md:188`.

---

## 4. Replay bytes are valid and show the game — TRUE

The replay is the starter's **binary `COWLDPGN`** container, not raw JSON, and the design declares the
substitute procedure for this exact check (`design.md` §"Replay bytes (self-sufficient)", lines
1054–1080) — a **documented exception, cited not assumed**:

> **The phase-60 substitute for SPEC §Definition of done check 4:** `python3 tools/replay_summary.py
> /tmp/ep.replay > /tmp/ep.json` … Require `protocol == "procgen/v1"`, `results.reason == "complete"`
> (or the declared-acceptable `deadline`), `results.levelSeeds | length == results.levelCount`, every
> `levelSplit` entry in `{seen, unseen}` with both present, a non-zero `results.unseenMilli`, and the
> seat's turns with `source == "llm"`, real plans and non-empty `says` — not all fallbacks.

Tool provenance: the working tree `/workspace/cogame-procgen` at the released head **`545c791`**
("r1-F9: commit the four replay fixtures the note names" — the sha phase 40 released as 0.1.0), clean
(`git status --porcelain` empty, `origin/main` == `545c791`); `tools/replay_summary.py` sha256
`b1171da0053e3960df824776b3b31626a7cbf5cdae70ea11f1fb680b4549d6c1`. Python 3 stdlib only.

### 4a. `ereq_4202e87d…` — champion 1, `daveey` / `procgen-cartographer:v1`

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/55bcf72a-6bca-4d88-a47b-aa34150645d5.replay" \
     -o /tmp/ep.replay -w "HTTP %{http_code} bytes=%{size_download} type=%{content_type}\n"
head -c 16 /tmp/ep.replay | od -c | head -2
jq -e . /tmp/ep.replay >/dev/null 2>&1 && echo "raw is JSON" || echo "raw is NOT JSON (binary COWLDPGN)"
python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json ; echo "rc=$?"
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .results.reason, .results.endRule' /tmp/ep.json
```
```
HTTP 200 bytes=151933 type=application/octet-stream
0000000   C   O   W   L   D   P   G   N 001  \0  \0  \0  \a  \0  \0  \0
raw is NOT JSON (binary COWLDPGN)
rc=0
strict UTF-8 JSON: ok
procgen/v1
complete
gauntlet_complete
```

```bash
jq -c 'del(.actions,.says,.notes)' /tmp/ep.json
```
```json
{"protocol":"procgen/v1","gameName":"procgen","gameVersion":"1","seed":1867834266,"variant":"gauntlet","difficulty":"standard","levelCount":8,"levelKinds":["climber","chaser","maze","chaser","maze","miner","climber","miner"],"levelSeeds":[858890166,1847739717,1016,2008,53451433,1968772008,3030,4026],"levelSplit":["unseen","unseen","seen","seen","unseen","unseen","seen","seen"],"names":["daveey"],"aliases":["COG-alpha"],"policyKinds":["llm"],"frameCount":355,"levels":8,"notes_count":0,"fallbacks":55,"interrupts":16,"results":{"names":["daveey"],"aliases":["COG-alpha"],"scores":[0.362],"win":[false],"reason":"complete","endRule":"gauntlet_complete","variant":"gauntlet","difficulty":"standard","seed":1867834266,"levelCount":8,"levelKinds":["climber","chaser","maze","chaser","maze","miner","climber","miner"],"levelSplit":["unseen","unseen","seen","seen","unseen","unseen","seen","seen"],"levelSeeds":[858890166,1847739717,1016,2008,53451433,1968772008,3030,4026],"levelReturns":[267,350,33,319,121,713,423,800],"levelOutcome":["timeup","timeup","timeup","died","timeup","timeup","died","timeup"],"levelDeathCause":["","","","caught","","","spiked",""],"levelFrames":[54,13,59,20,59,48,39,55],"levelCollected":[1,3,0,3,0,3,2,4],"levelCollectTotal":[4,8,4,8,4,4,4,4],"seenMilli":393,"unseenMilli":362,"gapMilli":31,"seenCleared":0,"unseenCleared":0,"policyKinds":["llm"],"llmTurns":68,"fallbackTurns":7,"ordersRejected":6,"planInterrupts":16,"genFallbacks":0,"deadSeats":[false],"stopDetail":""}}
```

```bash
jq -r '[.actions[]|.source]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.json
jq -r '"says: \(.says|length)  unique: \(.says|unique|length)"' /tmp/ep.json
```
```
{"fallback": 7, "llm": 68}
says: 68  unique: 66
```

### 4b. `ereq_c6fddedb…` — champion 2, `daveey-1` / `procgen-scrambler:v1` (also the featured replay, §6/§8)

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/e8a45e7f-f234-4069-8a12-cbc720efebaa.replay" \
     -o /tmp/ep2.replay -w "HTTP %{http_code} bytes=%{size_download}\n"
python3 tools/replay_summary.py /tmp/ep2.replay > /tmp/ep2.json
jq -e . /tmp/ep2.json >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol' /tmp/ep2.json
jq -c '.results|{reason,endRule,scores,win,levelSplit,levelReturns,levelOutcome,seenMilli,unseenMilli,gapMilli,llmTurns,fallbackTurns,ordersRejected,planInterrupts,genFallbacks}' /tmp/ep2.json
jq -r '[.actions[]|.source]|group_by(.)|map({(.[0]):length})|add' /tmp/ep2.json
jq -r '"says: \(.says|length)  unique: \(.says|unique|length)"' /tmp/ep2.json
jq -c '{names,aliases,policyKinds,frameCount,levelKinds,levelSeeds}' /tmp/ep2.json
```
```
HTTP 200 bytes=154663
strict UTF-8 JSON: ok
procgen/v1
{"reason":"complete","endRule":"gauntlet_complete","scores":[0.336],"win":[false],"levelSplit":["seen","unseen","seen","unseen","unseen","seen","unseen","seen"],"levelReturns":[811,0,433,345,473,60,527,241],"levelOutcome":["timeup","timeup","timeup","timeup","timeup","timeup","timeup","timeup"],"seenMilli":386,"unseenMilli":336,"gapMilli":50,"llmTurns":78,"fallbackTurns":2,"ordersRejected":0,"planInterrupts":15,"genFallbacks":0}
{"fallback": 2, "llm": 78}
says: 78  unique: 77
{"names":["daveey-1"],"aliases":["COG-alpha"],"policyKinds":["llm"],"frameCount":329,"levelKinds":["miner","maze","chaser","chaser","climber","maze","miner","climber"],"levelSeeds":[4004,89013220,2008,1257444618,2033174848,1019,151229263,3024]}
```

**Status: TRUE**, on every clause of the design-declared substitute, for **both** champions:

| requirement | `daveey` ep | `daveey-1` ep |
|---|---|---|
| strict UTF-8 JSON under `jq -e` | ok | ok |
| `protocol` matches the manifest/design string `procgen/v1` | `procgen/v1` | `procgen/v1` |
| `results.reason` | **`complete`** (`gauntlet_complete`) | **`complete`** (`gauntlet_complete`) |
| `levelSeeds \| length == levelCount` | 8 == 8 | 8 == 8 |
| every `levelSplit` in `{seen,unseen}`, both present | 4 seen / 4 unseen | 4 seen / 4 unseen |
| `unseenMilli` non-zero | 362 | 336 |
| champion decisions non-scripted, not all fallbacks | **68 llm / 7 fallback = 9.3 % fallback** | **78 llm / 2 fallback = 2.5 % fallback** |
| `says` non-empty and non-trivial | 66 distinct of 68 | 77 distinct of 78 |

The declared-acceptable `deadline` exception (`design.md:506-512`, "`results.endRule = "wall_clock"`.
**Declared acceptable** for SPEC §Definition of done check 4") was **not** needed — both episodes ended
`complete` / `gauntlet_complete`. `genFallbacks == 0` in both: no generator ever fell back to the
hand-authored level. Ordered event excerpts, used again in §8:

```bash
jq -r '.actions[]|select(.turn<=5)|[.turn,.level,.source,.moves,.executed]|@tsv' /tmp/ep2.json          # early
jq -r '.actions[]|select(.turn>=38 and .turn<=42)|[.turn,.level,.source,.moves,.executed]|@tsv' /tmp/ep2.json   # middle
jq -r '.actions[-5:][]|[.turn,.level,.source,.moves,.executed]|@tsv' /tmp/ep2.json                      # late
jq -r '.says[0:3][]' /tmp/ep2.json ; jq -r '.says[-3:][]' /tmp/ep2.json
```
```
1	1	llm	RDR	3          | 38	4	llm	D....	1     | 76	8	llm	LUUUU	5
2	1	llm	DXDX	4         | 39	4	llm	LLLUU	1    | 77	8	llm	RURUU	5
3	1	llm	RUL	3          | 40	4	llm	L	1        | 78	8	llm	RRUUX.	6
4	1	llm	RU	2           | 41	5	llm	LLLLL	5    | 79	8	llm	UUUUUU	6
5	1	llm	RRRR	4         | 42	5	llm	RRRRRR	6   | 80	8	llm	LUUUU	5
```
```
Survey: moving toward ne        (turn 1)
Mining gems systematical        (turn 2)
Gem run: right-up-left t        (turn 3)
...
Climb right to [9,4] gem        (turn 78)
Climbing to top gem at [        (turn 79)
Banking 3/4 gems, approa        (turn 80)
```
The `executed` column is the interruptible-plan machinery working: turn 38's five-symbol plan ran
**1** symbol before the danger interrupt fired (`planInterrupts: 15`). Level 1 (`miner`, seed 4004,
seen) collected 4/4 gems for a return of 811; level 2 (`maze`, seed 89013220, **unseen**) collected
0/4 for a return of 0. That spread is the coworld's whole point, and §8 confirms the viewer draws it.

---

## 5. Hosted game log is clean — **FALSE**

The logs body is python `b'…'` byte-string reprs under `===== container: … =====` headers; it was
decoded per repr with `ast.literal_eval` before grepping (`playbooks/observatory-api.md` §10).

```bash
for E in ereq_c6fddedb-85ee-4c3b-b318-691407d9dad1 ereq_4202e87d-98b9-47a1-98be-77438668dbda; do
  curl -sS "$BASE/episode-requests/$E/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o $E.raw -w "HTTP %{http_code} bytes=%{size_download}\n"
  # decode each b'…' repr, then:
  grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' $E.txt || echo CLEAN
done
```

**`ereq_c6fddedb…` (daveey-1) — HTTP 200, 203177 bytes — 2 gate matches:**
```
406:procgen llm: seat 0 falling back to pathfinder (parse_error) on turn 23
413:procgen llm: seat 0 falling back to pathfinder (parse_error) on turn 43
```
**`ereq_4202e87d…` (daveey) — HTTP 200, 247362 bytes — 7 gate matches:**
```
491:procgen llm: seat 0 falling back to pathfinder (parse_error) on turn 11
505:procgen llm: seat 0 falling back to pathfinder (parse_error) on turn 31
508:procgen llm: seat 0 falling back to pathfinder (parse_error) on turn 33
511:procgen llm: seat 0 falling back to pathfinder (parse_error) on turn 34
515:procgen llm: seat 0 falling back to pathfinder (parse_error) on turn 37
522:procgen llm: seat 0 falling back to pathfinder (parse_error) on turn 49
533:procgen llm: seat 0 falling back to pathfinder (parse_error) on turn 70
```
Zero matches for `LLM provider is unavailable`, `cut off at max_tokens` and `rejected` in either — the
**only** gate string that fires is `falling back`.

The whole `game` container of each, with the repeated `attempt N failed, will retry` lines elided
(counts given beneath):

```
===== container: game =====                        (ereq_c6fddedb…, daveey-1)
procgen: seed not pinned; randomized
procgen config: host=0.0.0.0 port=8080 seed=253823283 levelCount=8 turnsPerLevel=10 framesPerTurn=6 difficulty=standard num_agents=1 turnSpacingMs=2500 wallClockBudgetSeconds=660
procgen listening on 0.0.0.0:8080
procgen llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
procgen llm: seat 0 falling back to pathfinder (parse_error) on turn 23
procgen llm: seat 0 falling back to pathfinder (parse_error) on turn 43
procgen: episode complete (gauntlet_complete) after 321 frames, 80 turns; unseen 336 seen 386
   [elided: 17 × "attempt 1 failed, will retry", 2 × "attempt 2 failed, will retry"]

===== container: game =====                        (ereq_4202e87d…, daveey)
procgen: seed not pinned; randomized
procgen config: host=0.0.0.0 port=8080 seed=1867834266 levelCount=8 turnsPerLevel=10 framesPerTurn=6 difficulty=standard num_agents=1 turnSpacingMs=2500 wallClockBudgetSeconds=660
procgen listening on 0.0.0.0:8080
procgen llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
procgen llm: seat 0 falling back to pathfinder (parse_error) on turn 11
   … (7 such lines, quoted in full above) …
procgen: episode complete (gauntlet_complete) after 347 frames, 75 turns; unseen 362 seen 393
   [elided: 41 × "attempt 1 failed, will retry", 7 × "attempt 2 failed, will retry"]
```

The verbatim retry line, one of many, is:
```
procgen llm: seat 0 attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
```

### The retry budget: all four rounds fail this gate

Every completed round was fetched and gate-grepped independently (the prompt's "3 attempts, each a
different approach — different round"; four were available inside the bound):

| round | episode request | seat | `falling back` lines | fallback turns / llm turns (replay) |
|---|---|---|---|---|
| 1 | `ereq_33e48747-e91b-4c91-abaa-934ebb249ebd` | daveey | **11** | 11 / 56 |
| 1 | `ereq_70a65a10-ed36-4b38-85cf-4934d8d814a9` | daveey-1 | **6** | — |
| 2 | `ereq_bd99509a-561c-45aa-94f9-b1d0c8f470c7` | daveey-1 | **4** | — |
| 2 | `ereq_c9b6a651-362b-4f95-8325-469af8ff1352` | daveey | **4** | — |
| 3 | `ereq_0e3e8012-4734-417f-b766-f8780f343048` | daveey-1 | **1** | — |
| 3 | `ereq_ad8b7429-9235-439a-b177-c9cc7829aec9` | daveey | **3** | — |
| 4 | `ereq_c6fddedb-85ee-4c3b-b318-691407d9dad1` | daveey-1 | **2** | 2 / 78 |
| 4 | `ereq_4202e87d-98b9-47a1-98be-77438668dbda` | daveey | **7** | 7 / 68 |

No round was clean. There is no round left to try inside the 75-minute bound.

### Cause, from the same logs — and the cross-check that says it is **not** the documented exception

The gate string here is `falling back`, **not** `LLM provider is unavailable`, so the platform-capacity
exception the prompt allows is not on its face available. I checked it anyway, and it does not hold:

```bash
# another LLM coworld's latest completed round, fetched fresh this run
# gen-generals-io, league_03508cde-…, round 51 completed 2026-08-28T20:23:07Z, ereq_24dd2ac6-…
grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/xcheck.txt
```
```
HTTP 200 bytes=129016
0        # CLEAN
```

Bedrock sidecar latency, from the `bedrock_sidecar_complete` records in each log
(`"latency_ms":…`, every call `"ok":true,"status_code":200` — **nothing is failing, it is only slow**):

| episode | n calls | p50 | p90 | max | calls > 5000 ms |
|---|---|---|---|---|---|
| procgen r4, `ereq_c6fddedb…` | 97 | 1870 ms | 5591 ms | 7207 ms | **17** |
| procgen r4, `ereq_4202e87d…` | 116 | 2020 ms | 7476 ms | 9196 ms | **41** |
| gen-generals-io r51 (cross-check) | 60 | 1702 ms | 2674 ms | 5246 ms | 1 |

procgen's own deadlines are `attempt1Ms: 5000, retryMs: 2000`
(`src/procgen/sim_types.nim:94`, at the released head `545c791`). So a first attempt is cut at 5 s while
procgen's own p90 is 5.6–7.5 s, and the single retry then gets only **2 s** — which a 1.9 s-median,
7.5 s-p90 call almost never makes. That is why the fallback fires. The cross-check coworld sits
comfortably under its own timeout at the same minute on the same Bedrock, so this is **procgen's timeout
configuration against procgen's own prompt size** (input 1.6–1.8 k tokens, output up to 640), not a
platform outage. A second cross-check (`derks-gym` rounds 33/34) was attempted and discarded: its
`artifacts/logs` body is only ~2 KB with no `bedrock_sidecar` records at all, so it is not evidence
either way.

Two further findings for phase 30, neither of which changes this verdict:
- the fallback **cause label is wrong** — a transport timeout is reported as `parse_error`, which will
  mislead the next forensic reader;
- `retryMs: 2000` is strictly smaller than `attempt1Ms: 5000`, i.e. the retry is given *less* time than
  the attempt that just timed out. Raising both (and widening `turnBudgetMs` to match) is the fix.

**Status: FALSE** — the latest round's hosted game logs contain 2 and 7 `falling back` lines
respectively; the gate requires `CLEAN`. All four completed rounds fail it, and the documented
platform-capacity exception does not apply (cross-check coworld clean at the same minute). I am **not**
marking this true. The blast radius is bounded: check 4 still passes, because the fallback share of
champion decisions is 9.3 % and 2.5 % — a small minority, as check 4 requires.

---

## 6. The public page uses the static replay path — TRUE

**(a) Raw-HTML iframe grep — empty. Treated as *unknown* per the prompt, not as a failure.**
```bash
curl -sS "https://softmax.com/procgen" -o /tmp/page.html -w "HTTP %{http_code} bytes=%{size_download}\n"
grep -o '<iframe[^>]*src="[^"]*"' /tmp/page.html || echo "NO iframe in raw HTML (client-rendered)"
```
```
HTTP 200 bytes=749039      (fetched 2026-08-28T21:06:58Z)
NO iframe in raw HTML (client-rendered)
```

**(b) Coworld detail API — `replay_viewer` and `featured_match` are null (platform-wide since the
lighthouse run, 2026-08-22), so also not evidence.**
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)[]|select(.name=="procgen")|{id,name,canonical,version,replay_viewer,featured_match}'
```
```
{
  "id": "cow_4d7261f4-1766-4ca3-84df-0e61eedd1b4d",
  "name": "procgen",
  "canonical": true,
  "version": "0.1.0",
  "replay_viewer": null,
  "featured_match": null
}
```

**(c) Source actually used: the page's own SSR payload + the replay-session call its JS makes.**
The SSR `state` object was brace-matched out of the page bytes fetched in (a) and parsed:

```bash
python3 - # find '"state":{"leagueId"', brace-match, json.loads
```
```
keys: ['leagueId', 'playlist', 'pool', 'divisionLeaderboard', 'divisionId', 'standings',
       'divisionName', 'divisionCount', 'playerCount', 'activeRound', 'activeRoundProgress',
       'newestCompletedAt', 'firstPlace']
leagueId: league_2b1f9007-0749-4e3c-a669-a630283894f1
playlist len: 0            # the 2026-08-28 SSR shape puts the match under state.pool.replays, not state.playlist
pool keys: ['replays', 'live']
pool.replays len: 2
```
`state.pool.replays[0]` — **the featured match**:
```json
{
 "kind": "replay",
 "round_number": 4,
 "round_status": "completed",
 "ereq": "ereq_c6fddedb-85ee-4c3b-b318-691407d9dad1",
 "episode_id": "9fc38f5e-8f9b-48d3-9c63-baceef1dc043",
 "coworld_name": "procgen",
 "coworld_version": "0.1.0",
 "variant_name": "Procgen Gauntlet (8 levels, half of them nobody has ever seen)",
 "status": "completed",
 "replay_url": "https://softmax-public.s3.amazonaws.com/replays/e8a45e7f-f234-4069-8a12-cbc720efebaa.replay",
 "participants": [{"player_name": "daveey-1", "policy_name": "procgen-scrambler", "is_filler": false}],
 "scores": [{"position": 0, "score": 0.336}]
}
```
`state.pool.replays[1]` is round 4's other episode (`ereq_4202e87d…`, `daveey`, replay
`55bcf72a-…`). `state.divisionLeaderboard`, server-rendered into the same payload, carries **two ranked
players** — so the "featured match absent = fewer than two ranked players" failure mode does not apply:
```json
[{"rank":1,"player_name":"daveey","score":1026.666828786396,"score_label":"MMR","rounds_played":4,
  "episode_wins":3,"win_rate":0.75,"policy_label":"procgen-cartographer:v1"},
 {"rank":2,"player_name":"daveey-1","score":973.3331712136038,"score_label":"MMR","rounds_played":4,
  "episode_wins":1,"win_rate":0.25,"policy_label":"procgen-scrambler:v1"}]
```
`state.firstPlace.current` also server-renders `{"player_name":"daveey","rounds_held":4,"score":1026.67,
"second_player_name":"daveey-1","gap_to_second":53.33}`, and `state.playerCount` is `2`.

Viewer URL (the iframe `src`), from the call the page makes:
```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_4d7261f4-1766-4ca3-84df-0e61eedd1b4d",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/e8a45e7f-f234-4069-8a12-cbc720efebaa.replay"}'
```
```
HTTP 200
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_4d7261f4-1766-4ca3-84df-0e61eedd1b4d/sha256%3A5b5bf61a91162daf850cb526ef5792a96acb61849bec503428ce8b7da86e7311/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fe8a45e7f-f234-4069-8a12-cbc720efebaa.replay","ready":true}
```

**Status: TRUE.** A featured match is present (`state.pool.replays[0]` = round 4's `daveey-1` episode)
and two players are ranked. The viewer URL is on the **static** route
`/v2/coworlds/replays/static/<cow_id>/<sha>/index.html`, with `<sha>` the coworld's manifest hash
`sha256:5b5bf61a…` (URL-encoded) — byte-identical to `STATE.coworld.manifest_sha` — and `ready: true`.
The replay arrives as the URL-encoded `#replay=` **fragment** (`?v=2#replay=…`), the variant
`playbooks/observatory-api.md` documents as of 2026-08-28; it is the same static route. **No
`/client/replay` pod URL appears anywhere.** Sources (a) and (b) returned nothing and are recorded above.

---

## 7. Certification declared the static bundle — TRUE

Source used: **the committed `runs/2026-08-28-procgen/release-result.json`** (the copy phase 40
downloaded and committed, `log.md` 20:10:17Z). It was present, so the `gh run download` fallback
(release run `33206322967`) was **not** needed. `/tmp` was never consulted.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-28-procgen/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```
```bash
jq -r '.certify.ok' runs/2026-08-28-procgen/release-result.json
```
```
true
```

**Status: TRUE** — the required substring `Replay liveness: skipped (static replay bundle declared` is
present, read from the committed artifact.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — TRUE

**(a) Dispatch.** `SRC` is the check-6 `viewer_url`, verbatim including the `#replay=` fragment.

```bash
SRC=$(jq -r .viewer_url /tmp/session.json)
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90   # dispatched 2026-08-28T21:08:06Z
sleep 10
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:3][]|[.databaseId,.createdAt,.status]|@tsv'
```
```
33211231543	2026-08-28T21:08:08Z	in_progress      <- created AFTER the 21:08:06Z dispatch: this run
33198007349	2026-08-28T18:09:26Z	completed
33187402013	2026-08-28T15:54:21Z	completed
```
Identified by `createdAt` > dispatch time on a sorted list, never by taking "the latest run" blind.

```bash
gh run watch 33211231543 -R Metta-AI/coworld-builder --exit-status ; echo "watch_exit=$?"
gh run view 33211231543 -R Metta-AI/coworld-builder --json conclusion,status,url
```
```
✓ main viewer-check · 33211231543
✓ viewer-check in 33s (ID 98984657617)
  ✓ Install Playwright (pinned 1.55.0)
  ✓ Load the viewer
  ✓ Summary
  ✓ Upload the evidence
  ✓ Fail if the viewer did not load
watch_exit=0
{"conclusion":"success","status":"completed","url":"https://github.com/Metta-AI/coworld-builder/actions/runs/33211231543"}
```

```bash
mkdir -p runs/2026-08-28-procgen/viewer-check
gh run download 33211231543 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-28-procgen/viewer-check
ls -la runs/2026-08-28-procgen/viewer-check/
```
```
-rw-r--r--  smoke-stderr.txt        0
-rw-r--r--  smoke-stdout.txt      718
-rw-r--r--  viewer-smoke.json    1514
-rw-r--r--  viewer-smoke.png   418003
```
That directory is written alongside this file (the coordinator commits it) — it is this run's only
rendered evidence and the CI sandbox that produced it is gone by the next heartbeat.

**(b) Readouts.**

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-28-procgen/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":1763,"clock":"LEVEL 1/8 turn 0/10 · frame 0 BEFORE THE FIRST LEVEL","scorebug":"daveey-1 COG-alpha L1/8 · MINERSEEN LEVEL 0/4 GEMS ↯ LEVEL 1/8 turn 0/10 · frame 0 BEFORE THE FIRST LEVEL","feed_lines":2}
```

```bash
jq -c '.signals' runs/2026-08-28-procgen/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-28-procgen/viewer-check/viewer-smoke.json
```

| scrub | clock readout |
|---|---|
| **0 %** | `LEVEL 1/8 turn 0/10 · frame 0 BEFORE THE FIRST LEVEL` |
| **50 %** | `LEVEL 5/8 turn 0/10 · frame 30 CLIMBER · 15×9 · STANDARD · UNSEEN SEED 2033174848` |
| **100 %** | `LEVEL 8/8 turn 0/10 · frame 51 CLIMBER · 15×9 · STANDARD · SEEN SEED 3024` |

```bash
jq -r '.failure // "no failure"' runs/2026-08-28-procgen/viewer-check/viewer-smoke.json
```
```
no failure
```

Also from the same artifact:
```json
"status": "LIVE", "loading_text": null, "console_tail": [], "bundle": null, "replay": null,
"canvas_text": {"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],
                "distinct_capped":false,"samples":[]}
```

**Both conditions hold: `loaded: true`** — first frame at **1763 ms**, signalled by
`data-replay-loaded="true"` — **and the three clock readouts differ**: level 1 → level 5 → level 8,
frame 0 → 30 → 51. `#scrub` exists (the readouts were taken by dragging it), so the missing-scrubber
caveat does not apply. `bridge_ready:false` is not a defect: the load signal arrived via the
`data-replay-loaded` attribute, which the checker accepts as either-or. No page error, no console
output, no `loading_text` left on screen, no canvas text drawn outside its box.

The two scrubbed clocks also **reconcile exactly** with §4b's replay record: level 5 is `climber`, seed
`2033174848`, split `unseen`; level 8 is `climber`, seed `3024`, split `seen` — the viewer is reading
`levelKinds`/`levelSeeds`/`levelSplit` out of the replay bytes and re-generating the levels, as the
design says it must.

**(c) Spectator judgment.**

`viewer-smoke.png` (1280×800, captured after the 100 % scrub) shows a finished gauntlet, and it is
legible. Behind a dimmed veil the **fixed 15×9 arena** is drawn — the climber tier bands, ladders and a
gem sprite, with a "LEVEL 5 OF 8 — CLIMBER — UNSEEN" plate above it; there is no zoom panel, which the
design deliberately dropped. Dominating the centre is the **endcard**, and it is the coworld's thesis
stated in one line: **`SCORE 0.336 — mean over 4 unseen levels`**, under it the chip
`SEEN 0.386 · UNSEEN 0.336 · GAP +0.050`, then
`gauntlet · standard · 4 seen / 4 unseen · 0 of 4 unseen levels cleared`, then the two headline figures
`0.336 UNSEEN MEAN` / `0.386 SEEN MEAN`, then the per-level results table with the columns
**`LEVEL | KIND | SEED | SPLIT | OUTCOME | GEMS | RETURN`** — unseen rows tinted amber, seen rows white:

| LEVEL | KIND | SEED | SPLIT | OUTCOME | GEMS | RETURN |
|---|---|---|---|---|---|---|
| 1 | miner | 4004 | seen | timeup | 4/4 | 811 |
| 2 | maze | 89013220 | unseen | timeup | 0/4 | 0 |
| 3 | chaser | 2008 | seen | timeup | 3/8 | 433 |
| 4 | chaser | 1257444618 | unseen | timeup | 3/8 | 345 |
| 5 | climber | 2033174848 | unseen | timeup | 2/4 | 473 |
| 6 | maze | 1019 | seen | timeup | 0/4 | 60 |
| 7 | miner | 151229263 | unseen | timeup | 2/4 | 527 |
| 8 | climber | 3024 | seen | timeup | 1/4 | 241 |

Every cell reconciles with the replay record in §4b: `levelKinds`, `levelSeeds`, `levelSplit`,
`levelOutcome` (all eight `timeup`), `levelCollected [4,0,3,3,2,0,2,1]` over
`levelCollectTotal [4,4,8,8,4,4,4,4]`, `levelReturns [811,0,433,345,473,60,527,241]`,
`seenMilli 386` / `unseenMilli 336` / `gapMilli 50` — the endcard's `0.386 / 0.336 / +0.050`. Bottom
right, four killfeed lines are legible: `COG-alpha takes gem 1 of 4`, `plan cut short — falling`,
`COG-alpha runs out of turns on CLIMBER — 241`, `GAUNTLET OVER — unseen mean 336`; the second is the
`planInterrupts` machinery narrating itself, the third matches level 8's return of 241, and a speech
bubble reads `Banking 3/4 gems, approa` — literally the turn-80 `say` in the replay. Top strip: the cog
plate (`davee…`, alias `COG-alpha`, chip `L8/8 · CLIMBER SEEN`, gem counter `1/4`) either side of the
centred clock `LEVEL 8/8 / turn 0/10 · frame 51 / CLIMBER · 15×9 · STANDARD · SEEN SEED 3024`.

Across the bottom is the **transport strip**: restart, step-back, play, `+5s`, step, loop and
fast-forward buttons, a `spoilers` toggle, a `328 / 328` frame counter, speed chips `1× 2× 3× 4× 8× 16×`,
and beneath them the **scrubber with beat ticks** (green, amber and blue markers at
levelstart / collect / exitopen / death / levelend beats) over a **`SEEN vs UNSEEN` momentum band** whose
two traces run the length of the episode. That is the paintbot / raid / hive chrome of the
coworld-ctf starter lineage — same transport strip, same scrubber-plus-momentum graph, same scorebug,
same endcard shape — with only the sport-specific labels changed. Nothing here resembles the
cogame-gridlock failure mode of a rewrite sharing only the element ids.

The picture is neither empty nor frozen: the three scrub readouts move it through levels 1, 5 and 8 and
frames 0, 30 and 51, and the endcard's numbers are the ones the replay recorded. **A casual spectator
can tell who is winning and why**: one cog, its score is the big number, the table says which levels it
had never seen and how few gems it got on them, and the `GAP +0.050` chip says in one figure that it did
better on the published seeds than on the fresh ones — which is exactly what this coworld exists to
measure.

Three legibility observations for the coordinator, none of them a failure of this check:
(i) the top-left name plate **elides the player name to `davee…`** even though the DOM scorebug carries
the full `daveey-1` — a spectator cannot read whose cog it is from the picture alone;
(ii) the gem counter's label reads **`LEVEL`** above the value `1/4` while the DOM string is
`LEVEL 0/4 GEMS`, so the number is the gem count under a label that says level — genuinely confusing at
a glance and a one-word fix;
(iii) `feed_lines: 2` was sampled at load time, when the clock read `frame 0 BEFORE THE FIRST LEVEL`;
the screenshot shows four feed lines after the seek, so the feed does populate — the low count is an
artefact of *when* the checker samples, not a missing killfeed.

**Status: TRUE** — `loaded: true` at 1763 ms, three differing clock readouts, no failure, and the
rendered frame shows the game this coworld is about, in the starter's chrome.

---

## Summary table

| # | Check | Verdict | Evidence pointer |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** | 4 completed rounds (r1 20:19:57Z … r4 21:04:53Z), 0 failed; filler set reads back live, disjoint from champions |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** | `daveey` rank 1 / `daveey-1` rank 2, `rounds_played` 4 each; no filler row |
| 3 | Latest round's episode request completed with a replay | **TRUE** | round 4's two episodes `ereq_c6fddedb…` + `ereq_4202e87d…`, both `completed` with `replay_url`, naming daveey-1 and daveey (single-seat design, `design.md:188`) |
| 4 | Replay bytes valid and show the game | **TRUE** | `procgen/v1`, `reason complete` / `gauntlet_complete` both episodes; fallback share 9.3 % and 2.5 %; 4 seen / 4 unseen; `unseenMilli` 362 / 336 |
| 5 | Hosted game log clean | **FALSE** | 7 and 2 `falling back to pathfinder (parse_error)` lines in round 4's logs; all four rounds dirty; cause = `attempt1Ms 5000`/`retryMs 2000` vs procgen's own Bedrock p90 5.6–7.5 s; cross-check coworld clean at the same minute, so the platform-capacity exception does **not** apply |
| 6 | Public page uses the static replay path | **TRUE** | static route + manifest sha `sha256:5b5bf61a…` + `ready:true`; featured match `state.pool.replays[0]` = round 4 daveey-1; two ranked players in the SSR leaderboard |
| 7 | Certification declared the static bundle | **TRUE** | `Replay liveness: skipped (static replay bundle declared…`, committed `release-result.json` |
| 8 | Spectator judgment — viewer executed and legible | **TRUE** | `loaded:true` @ 1763 ms, clocks L1/f0 → L5/f30 → L8/f51, run `33211231543`, artifact committed |

Replay under test (featured, viewer): `https://softmax-public.s3.amazonaws.com/replays/e8a45e7f-f234-4069-8a12-cbc720efebaa.replay`
Replay under test (champion 1): `https://softmax-public.s3.amazonaws.com/replays/55bcf72a-6bca-4d88-a47b-aa34150645d5.replay`
Viewer URL: `https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_4d7261f4-1766-4ca3-84df-0e61eedd1b4d/sha256%3A5b5bf61a91162daf850cb526ef5792a96acb61849bec503428ce8b7da86e7311/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fe8a45e7f-f234-4069-8a12-cbc720efebaa.replay`
Viewer-check run: `https://github.com/Metta-AI/coworld-builder/actions/runs/33211231543` (artifact at `runs/2026-08-28-procgen/viewer-check/`)
