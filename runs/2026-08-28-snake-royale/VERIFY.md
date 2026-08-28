# VERIFY — snake-royale   (2026-08-28T08:08Z)

Verdict: **all-true (8/8)**

- Run: `2026-08-28-snake-royale` · slug `snake-royale` · repo `Metta-AI/cogame-snake-royale` · version `0.1.1`
- `COW` = `cow_dfae8bd2-c198-460c-acaf-1c3fc709688c` · manifest `sha256:7c10c697df9f3ce9cf043d3e3964fb31a97a7aa46d0720581188f0ae49795ca3`
- `L` = `league_9f435441-c018-419e-b8af-124d7a488081` · `D` = `div_9b84c813-77d9-41be-9fff-6e48af4cc474`
- `BASE` = `https://softmax.com/api/observatory/v2`
- Headers on every Observatory call: `Authorization: Bearer <redacted>`, `User-Agent: coworld-builder/1.0`;
  `X-Use-Elevated-Privileges: true` added on `artifacts/logs` and on the filler-policies read. No header
  values are reproduced anywhere in this file.
- Evidence-source choices (per brief): **check 6** used the **SSR-payload + replay-session route** after the
  page grep and the coworld-detail API both came back empty (both recorded below); **check 7** used the
  **committed `runs/2026-08-28-snake-royale/release-result.json`** (no re-download needed).
- Wall clock: verification opened 07:39Z, last round-poll 08:03Z — **24 min of the 75-min bound used**.
- Replay under test (latest completed round, round 3):
  `https://softmax-public.s3.amazonaws.com/replays/544f5847-40b8-4c88-b209-b2ca4b966226.replay`

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" -o /tmp/c1.json -w "HTTP %{http_code}\n"
jq -r 'if type=="array" then . else .entries end | .[] | {id,round_number,status,error,created_at,completed_at}' /tmp/c1.json
jq -r '[ (if type=="array" then . else .entries end)[]|select(.status=="completed")]|length' /tmp/c1.json
```

```
HTTP 200      (fetched 2026-08-28T08:03:35Z)
{
  "id": "round_0ee7c3f1-edc2-437d-b7cb-e06882f131d0",
  "round_number": 3,
  "status": "completed",
  "error": null,
  "created_at": "2026-08-28T07:51:52.425776Z",
  "completed_at": "2026-08-28T08:00:44.689497Z"
}
{
  "id": "round_b1b63f05-f980-4e6f-8250-b7678efed0c4",
  "round_number": 2,
  "status": "completed",
  "error": null,
  "created_at": "2026-08-28T07:36:52.057962Z",
  "completed_at": "2026-08-28T07:44:31.354849Z"
}
{
  "id": "round_6e56622a-737a-44dc-8308-7d10429eb388",
  "round_number": 1,
  "status": "failed",
  "error": "Temporal RoundWorkflow failed before settling the round.",
  "created_at": "2026-08-28T07:36:02.017975Z",
  "completed_at": "2026-08-28T07:36:03.437775Z"
}
```
```
2
```

Poll trail (each line an independent `GET /rounds?league_id=$L&limit=20`, HTTP 200 every time):

| poll (UTC) | round 2 | round 3 |
|---|---|---|
| 07:39Z | pending | — (not yet created) |
| 07:43Z | pending | — |
| 07:48Z | **completed** 07:44:31Z | — |
| 07:53Z | completed | pending (created 07:51:52Z) |
| 07:58Z | completed | pending |
| 08:03Z | completed | **completed** 08:00:44Z |

Round 1's `error` verbatim: `Temporal RoundWorkflow failed before settling the round.` — it was created
07:36:02Z, one second before the unpause/trigger settled, and is the documented
"trigger before the ladder is live" artefact (`playbooks/observatory-api.md` §6). It is `failed`, so per
`prompts/60-verify.md` check 1 it does not count.

**Fillers were in effect for both counted rounds** — direct evidence, not the log line: the filler set
reads back live, and both completed rounds' episodes seated two `is_filler: true` participants (round 3
in §3 below; round 2 quoted here).

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"      # elevated read
```
```
HTTP 200
{
  "filler_policy_versions": [
    {"policy_version_id": "f87382d5-f5e1-4f86-9d5d-6f7b2c9fcddd", "policy_name": "snake-royale-coil",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"},
    {"policy_version_id": "b21c23a0-4e13-4539-aa72-c2e58ac4ed71", "policy_name": "snake-royale-forager",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"}
  ]
}
```

```bash
curl -sS "$BASE/episode-requests/ereq_acf56070-1bb4-4f07-9e99-e82b2a1039ac" "${AUTH[@]}" \
 | jq '[.participants[]|{position,policy_name,player_name,is_filler}]'          # round 2's episode
```
```
[
  {"position":0,"policy_name":"snake-royale-strangler","player_name":"daveey","is_filler":false},
  {"position":1,"policy_name":"snake-royale-glutton","player_name":"daveey-1","is_filler":false},
  {"position":2,"policy_name":"snake-royale-coil","player_name":"daveey","is_filler":true},
  {"position":3,"policy_name":"snake-royale-coil","player_name":"daveey","is_filler":true}
]
```

**Status: TRUE** — 2 completed rounds (round 2 completed 2026-08-28T07:44:31Z, round 3 completed
2026-08-28T08:00:44Z), both created *after* the fillers were registered (`log.md` 07:37:59Z entry records
the registration at 07:36:0xZ, before the first trigger) and both demonstrably *seating* the registered
fillers. The only non-counting round is round 1 (`failed`, error quoted above).

---

## 2. Both champions ranked; fillers absent / Baseline — TRUE

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" -o /tmp/c2.json -w "HTTP %{http_code}\n"
jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv' /tmp/c2.json
```

```
HTTP 200      (fetched 2026-08-28T08:03:36Z; bare list, not .entries)
1	daveey-1	snake-royale-glutton:v1	1030.5304984710244	2	2.0
2	daveey	snake-royale-strangler:v1	969.4695015289755	2	0.0
```

**Status: TRUE** — both champions present: `daveey-1` (`snake-royale-glutton:v1`) rank 1, `rounds_played`
2, `episode_wins` 2; `daveey` (`snake-royale-strangler:v1`) rank 2, `rounds_played` 2. Both ≥ 1 round.
Neither filler (`snake-royale-coil:v1`, `snake-royale-forager:v1`) appears as a leaderboard row — they are
absent, which the checklist accepts, and inside the episode they are renamed `Baseline` / `Baseline (2)`
(see the replay `names` array in §4).

---

## 3. Latest round's episode request completed with a replay — TRUE

The flat `GET /episode-requests?round_id=` route is HTTP 405 since 2026-08-26
(`playbooks/observatory-api.md` §9), so the nested route was used.

```bash
R=round_0ee7c3f1-edc2-437d-b7cb-e06882f131d0        # max_by(round_number) over completed rounds = round 3
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" -o /tmp/c3l.json -w "HTTP %{http_code}\n"
jq -r 'if type=="array" then . else .entries end | .[] | [.id,.status]|@tsv' /tmp/c3l.json
```
```
HTTP 200
ereq_8dbbce59-40e4-4012-b3bf-2536626577f7	completed
```

```bash
EREQ=ereq_8dbbce59-40e4-4012-b3bf-2536626577f7
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants:[.participants[]|{position,policy_name,player_name,is_filler}], participant_scores}'
```
```
HTTP 200
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/544f5847-40b8-4c88-b209-b2ca4b966226.replay",
  "participants": [
    {"position": 0, "policy_name": "snake-royale-strangler", "player_name": "daveey",   "is_filler": false},
    {"position": 1, "policy_name": "snake-royale-glutton",   "player_name": "daveey-1", "is_filler": false},
    {"position": 2, "policy_name": "snake-royale-coil",      "player_name": "daveey",   "is_filler": true},
    {"position": 3, "policy_name": "snake-royale-forager",   "player_name": "daveey",   "is_filler": true}
  ],
  "participant_scores": [
    {"position": 0, "score": -1.0},
    {"position": 1, "score": 0.333},
    {"position": 2, "score": 1.0},
    {"position": 3, "score": -0.333}
  ]
}
```

**Status: TRUE** — `status == "completed"`, `replay_url` non-null, and `participants` name both `daveey`
(seat 0, `snake-royale-strangler`) and `daveey-1` (seat 1, `snake-royale-glutton`), with the two fillers
flagged `is_filler: true` at seats 2–3. `participant_scores` sum to 0.0 as the zero-sum placement design
requires (−1.0 + 0.333 + 1.0 + −0.333).

---

## 4. Replay bytes are valid and show the game — TRUE

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/544f5847-40b8-4c88-b209-b2ca4b966226.replay" \
     -o /tmp/ep.replay -w "HTTP %{http_code} bytes=%{size_download} type=%{content_type}\n"
head -c 16 /tmp/ep.replay | od -c | head -2
jq -e . /tmp/ep.replay >/dev/null 2>&1 && echo "raw is JSON" || echo "raw is NOT JSON (binary COWLDSNK)"
```
```
HTTP 200 bytes=26361 type=application/octet-stream
0000000   C   O   W   L   D   S   N   K 001  \0  \0  \0  \f  \0  \0  \0
raw is NOT JSON (binary COWLDSNK)
```

**Documented exception — cited, not assumed.** This coworld's replay is deliberately the starter's binary
`COWLDSNK` container, and `design.md` §"Replay bytes (self-sufficient)" (lines 883–911) declares the
substitute procedure for this very check:

> `tools/replay_summary.py` … given a `.replay` path it prints **one strict-UTF-8 JSON object** to stdout …
> **The phase-60 substitute for SPEC §Definition of done check 4:** `python3 tools/replay_summary.py
> /tmp/ep.replay > /tmp/ep.json` … Require `protocol == "snake-royale/v1"`, `results.reason == "complete"`
> (or the declared-acceptable `deadline`), `sum(results.scores) == 0`, a non-zero `sum(results.foodEaten)`
> … and the champion seats' turns with `source == "llm"`, real directions and non-empty `says` — not all
> fallbacks.

Tool provenance: fresh shallow clone of `Metta-AI/cogame-snake-royale` at `18b9da8` ("server: stop dropping
binary registration frames" — the released `0.1.1` head), `tools/replay_summary.py`
sha256 `2fc62a8a390d63310cd5eab15c51b63bebff483ff40a0fae7eb1b6cc9fe1955b`. Python 3 stdlib only.

```bash
python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json ; echo "rc=$?"
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .gameVersion, .results.reason, .results.endRule' /tmp/ep.json
```
```
replay_summary rc=0
strict UTF-8 JSON: ok
snake-royale/v1
1
complete
full_time
```

`protocol` matches the manifest string the design pins (`design.md:1559` — `protocol == "snake-royale/v1"`).
`results.reason` is `complete` (the healthy value) with `endRule: full_time` — the declared-acceptable
`deadline` exception was **not** needed.

```bash
jq -r '{names,policyKinds,turnCount,notes_count,fallbacks,seed,module,board}' /tmp/ep.json
jq -r '[.dirs[]|.source]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.json
jq -r '.dirs|group_by(.slot)|map({slot:.[0].slot, n:length, llm:[.[]|select(.source=="llm")]|length, fb:[.[]|select(.source=="fallback")]|length, scripted:[.[]|select(.source=="scripted")]|length})' /tmp/ep.json
```
```
{
  "names": ["daveey", "daveey-1", "Baseline", "Baseline (2)"],
  "policyKinds": ["llm", "llm", "scripted", "scripted"],
  "turnCount": 50,
  "notes_count": 0,
  "fallbacks": 2,
  "seed": 1355447938,
  "module": "royale",
  "board": {"cellPx": 32, "h": 9, "w": 17, "wrap": false}
}
```
```
{"llm": 59, "scripted": 93}                # NOTE: zero "fallback"-sourced directions
```
```
[{"slot":0,"n":9, "llm":9, "fb":0,"scripted":0},
 {"slot":1,"n":50,"llm":50,"fb":0,"scripted":0},
 {"slot":2,"n":50,"llm":0, "fb":0,"scripted":50},
 {"slot":3,"n":43,"llm":0, "fb":0,"scripted":43}]
```

```bash
jq -r '.registers[]|[.slot,.alias,.policy,.kind,.baseline]|@tsv' /tmp/ep.json
jq -r '.says|length' /tmp/ep.json ; jq -r '[.says[].text]|unique|length' /tmp/ep.json
jq -r '.results|{reason,endRule,place,scores,finalLength,foodEaten,llmTurns,fallbackTurns,survivedTurns,deathCause,killedBy,declinedKills,win,turnsPlayed}' /tmp/ep.json
jq -r '[.results.scores[]]|add' /tmp/ep.json ; jq -r '[.results.foodEaten[]]|add' /tmp/ep.json
```
```
0		strangler	llm	coil
1		glutton	llm	coil
2		coil	scripted	coil
3		forager	scripted	forager
```
```
59        # say records
57        # distinct say texts (57/59 unique — not a canned string)
```
```
{
  "reason": "complete",
  "endRule": "full_time",
  "place": [4, 2, 1, 3],
  "scores": [-1.0, 0.333, 1.0, -0.333],
  "finalLength": [3, 9, 15, 8],
  "foodEaten": [0, 6, 12, 5],
  "llmTurns": [9, 50, 0, 0],
  "fallbackTurns": [0, 0, 0, 0],
  "survivedTurns": [8, 50, 50, 42],
  "deathCause": ["wall", "", "", "body"],
  "killedBy": [-1, -1, -1, 2],
  "declinedKills": [0, 0, 1, 0],
  "win": [false, false, true, false],
  "turnsPlayed": 50
}
```
```
-5.551115123125783e-17      # sum(scores) == 0 to float precision
23                          # sum(foodEaten) — non-zero, as a food module requires
```

**Status: TRUE.** Strict-parser-valid UTF-8 JSON via the design-declared summariser; `protocol`
`snake-royale/v1` matches the manifest; `results.reason == "complete"` (no exception invoked);
zero-sum scores; 23 apples eaten. Champion decisions are **non-scripted and not fallbacks**: seat 0
(`daveey`/strangler) 9 of 9 turns `source=="llm"`, seat 1 (`daveey-1`/glutton) 50 of 50 turns
`source=="llm"`, `fallbackTurns == [0,0,0,0]` — **the fallback share of champion decisions is 0/59 = 0 %**.
The two `fallback` chat records in the header count *attempt* failures that the single retry then
recovered; no turn was ever driven by the scripted fallback. 57 distinct `say` strings over 59 records is
non-trivial content, not a stuck template.

Ordered event excerpts (early / middle / late), used again in §8 to reconcile against the render:

```bash
jq -r '.dirs[]|select(.turn<=4)|[.turn,.slot,.source,.dir]|@tsv' /tmp/ep.json
jq -r '.says[]|select(.turn<=4)|[.turn,.slot,.text]|@tsv' /tmp/ep.json
```
```
1	0	llm	right        1	0	taking right lane
1	1	llm	down         1	1	Heading to food at [12,8
1	2	scripted	down     2	0	Center right for space
1	3	scripted	down     2	1	Moving to [12,4], chasin
2	0	llm	right        3	0	Closing upper zone
2	1	llm	down         3	1	Pursuing food at [13,2]
3	0	llm	up           4	0	Controlling upper board
3	1	llm	right        4	1	L3, hunting at [13,2]
4	0	llm	up
4	1	llm	up
```
```bash
jq -r '.dirs[]|select(.turn>=25 and .turn<=27)|[.turn,.slot,.source,.dir]|@tsv' /tmp/ep.json
jq -r '.says[]|select(.turn>=25 and .turn<=27)|[.turn,.slot,.text]|@tsv' /tmp/ep.json
```
```
25	1	llm	up           25	1	Ate food #3, length 6
25	2	scripted	right    26	1	Length 6, chasing food a
25	3	scripted	right    27	1	Chasing food at [10,5]
26	1	llm	up
27	1	llm	up
```
```bash
jq -r '.dirs[]|select(.turn>=49)|[.turn,.slot,.source,.dir]|@tsv' /tmp/ep.json
jq -r '.says[]|select(.turn>=48)|[.turn,.slot,.text]|@tsv' /tmp/ep.json
```
```
49	1	llm	left         48	1	Survival mode, 3 left
49	2	scripted	left     49	1	Len 9, evading Gamma len
50	1	llm	up           50	1	Last turn - staying safe
50	2	scripted	down
```

Note how the seat roster thins: seat 0 stops appearing after turn 9 (died at the wall, `survivedTurns` 8),
seat 3 after turn 42 (ran into a body, `killedBy: 2`). Turns 49–50 have two live seats. That is the game
the viewer must show, and §8 confirms it does.

---

## 5. Hosted game log is clean — TRUE

The logs body is python `b'…'` byte-string reprs; it was decoded per-repr with `ast.literal_eval` before
grepping (`playbooks/observatory-api.md` §10 — a line-based grep on the raw body undercounts).

```bash
curl -sS "$BASE/episode-requests/ereq_8dbbce59-40e4-4012-b3bf-2536626577f7/artifacts/logs" \
  "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs3.raw -w "HTTP %{http_code} bytes=%{size_download}\n"
# decode every b'…' repr per container, then grep the decoded text
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs3.txt || echo CLEAN
grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs3.raw   # belt and braces
```
```
HTTP 200 bytes=126401
decoded lines: 261   (containers: coworld-init-config, bedrock-sidecar, game, worker)
--- GATE grep (decoded) ---
CLEAN
--- GATE grep (raw, undecoded) ---
0
```

The whole `game` container, verbatim:

```
===== container: game =====
snake-royale: seed not pinned; randomized
snake-royale config: host=0.0.0.0 port=8080 seed=1355447938 module=royale board=17x9 num_agents=4 maxTurns=50 turnSpacingMs=9000 wallClockBudgetSeconds=640
snake-royale listening on 0.0.0.0:8080
snake-royale llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
snake-royale llm: seat 1 attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
snake-royale llm: seat 1 attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
snake-royale: episode complete (full_time) after 50 turns
```

**Status: TRUE** — zero matches for `falling back`, `LLM provider is unavailable`, `cut off at max_tokens`
and `rejected`, in the decoded text *and* in the raw body. The two `attempt 1 failed, will retry` lines are
**not** on the gate list, and the retry succeeded both times — corroborated independently by the replay:
`fallbackTurns == [0,0,0,0]` and zero `fallback`-sourced directions (§4). The episode ended
`complete (full_time) after 50 turns`.

### Advisory for the coordinator (not a check-5 failure, and not an exception I am invoking)

The *previous* completed round (round 2, `ereq_acf56070-…`) was **not** clean and would have failed this
gate had it been the latest round. Recorded here verbatim because it is a real, recurring symptom:

```
snake-royale llm: seat 1 attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
snake-royale llm: seat 1 attempt 2 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
snake-royale llm: seat 1 falling back to coil (parse_error) on turn 6
snake-royale llm: seat 1 falling back to coil (parse_error) on turn 16
snake-royale llm: seat 1 falling back to coil (parse_error) on turn 25
```
(3 `falling back` lines; round 2's replay confirms 3 fallback-sourced turns out of 69 champion decisions
= 4.3 %, still a small minority, so round 2 would have passed check 4.)

Cause, from the same log's sidecar container: the Bedrock sidecar returns HTTP 200 but slowly, while the
game's per-attempt deadline is `attempt1Ms = 6000` / `retryMs = 3000` (`src/snake/sim_types.nim:101`).
Round 2 sidecar latency `max = 6628 ms`; round 3 `p50 = 2121 ms, p90 = 5123 ms, max = 6248 ms` — i.e. the
tail sits right on the 6 s attempt deadline, so whether a round is clean is currently luck of the latency
draw.

Cross-check that this is **platform-wide, not a snake-royale defect** — another LLM coworld's latest
completed round at the same minute (`hide-and-seek`, `league_7931991b-…`, round 24, completed
2026-08-28T07:51:25Z, `ereq_937056c2-…`):

```
hide-and-seek llm: seat 1 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
hide-and-seek llm: seat 2 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
hide-and-seek llm: seat 1 falling back to burrow (parse_error) on turn 6
hide-and-seek llm: seat 2 falling back to burrow (parse_error) on turn 6
```
(hide-and-seek sidecar latency the same minute: `p50 = 1625 ms, p90 = 2688 ms, max = 6170 ms`.)

Two things worth carrying forward, neither of which changes a verdict here: (a) the fallback **cause label
is wrong** — a transport timeout is reported as `parse_error`, which will mislead the next forensic reader;
(b) `attempt1Ms = 6000` is too tight for the current Bedrock haiku tail. Both are phase-30 / re-release
items, not verification blockers, since the round under test is clean on the gate.

---

## 6. The public page uses the static replay path — TRUE

**(a) Raw-HTML iframe grep — empty, treated as *unknown* per the prompt, not as a failure.**
```bash
curl -sS "https://softmax.com/snake-royale" -o /tmp/page.html -w "HTTP %{http_code} bytes=%{size_download}\n"
grep -o '<iframe[^>]*src="[^"]*"' /tmp/page.html || echo "NO iframe in raw HTML (client-rendered)"
```
```
HTTP 200 bytes=727026
NO iframe in raw HTML (client-rendered)
```

**(b) Coworld detail API — `replay_viewer` and `featured_match` are null platform-wide (lighthouse,
2026-08-22), so also not evidence.**
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)[]|select(.name=="snake-royale")|{id,name,canonical,replay_viewer,featured_match}'
```
```
{
  "id": "cow_dfae8bd2-c198-460c-acaf-1c3fc709688c",
  "name": "snake-royale",
  "canonical": true,
  "replay_viewer": null,
  "featured_match": null
}
```

**(c) Source actually used: the page's own SSR payload (`state.playlist[0]`) for the featured match, plus
the replay-session call the page's JS makes** — the route `playbooks/observatory-api.md`
§"Featured match / replay route" documents as what works.

Featured match, from the SSR payload embedded in the page bytes fetched in (a):
```
\"state\":{\"leagueId\":\"league_9f435441-c018-419e-b8af-124d7a488081\",
 \"playlist\":[{\"episodeId\":\"9e463dad-3440-409e-92a8-1923a90fa28d\",
  \"coworldId\":\"cow_dfae8bd2-c198-460c-acaf-1c3fc709688c\",
  \"coworldName\":\"snake-royale\",\"coworldVersion\":\"0.1.1\",
  \"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/544f5847-40b8-4c88-b209-b2ca4b966226.replay\",
  \"finishedAt\":\"2026-08-28T08:00:38.654955Z\",\"roundNumber\":3,\"episodeNumber\":1,
  \"code\":\"snake-royale.r3.e1\",
  \"matchup\":{\"divisionId\":\"div_9b84c813-77d9-41be-9fff-6e48af4cc474\",\"divisionName\":\"Competition\",
   \"first\":{\"rank\":1,\"player_name\":\"daveey-1\",\"score\":1030.5304984710244,\"score_label\":\"MMR\",
    \"rounds_played\":2,\"episode_wins\":2,\"win_rate\":1,\"policy_label\":\"snake-royale-glutton:v1\"},
   \"second\":{\"rank\":2,\"player_name\":\"daveey\",\"score\":969.4695015289755,\"score_label\":\"MMR\",
    \"rounds_played\":2,\"episode_wins\":0,\"win_rate\":0,\"policy_label\":\"snake-royale-strangler:v1\"}
```

Viewer URL (the iframe `src`), from the call the page makes:
```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_dfae8bd2-c198-460c-acaf-1c3fc709688c",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/544f5847-40b8-4c88-b209-b2ca4b966226.replay"}'
```
```
HTTP 200
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_dfae8bd2-c198-460c-acaf-1c3fc709688c/sha256%3A7c10c697df9f3ce9cf043d3e3964fb31a97a7aa46d0720581188f0ae49795ca3/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F544f5847-40b8-4c88-b209-b2ca4b966226.replay",
  "ready": true
}
```

**Status: TRUE.** A featured match is present (`playlist[0]` = `snake-royale.r3.e1`, the round-3 episode,
matchup daveey-1 vs daveey — i.e. two ranked players). The viewer URL is on the **static** route
`/v2/coworlds/replays/static/<cow_id>/<sha>/index.html`, with `<sha>` the coworld's manifest hash
`sha256:7c10c697…` (URL-encoded) exactly as `STATE.coworld.manifest_sha` records, and `ready: true`. The
replay arrives as the URL-encoded `#replay=` **fragment** (`?v=2#replay=…`) — the variant
`playbooks/observatory-api.md` documents as of 2026-08-28; it is the same static route. **No
`/client/replay` pod URL anywhere.** Source used: **page SSR payload + `POST /coworlds/replays/session`**
(sources (a) and (b) returned nothing, both recorded above).

---

## 7. Certification declared the static bundle — TRUE

Source used: **the committed `runs/2026-08-28-snake-royale/release-result.json`** (the copy phase 40
downloaded and committed). It was present, so the `gh run download` fallback (release run
`33151446939`) was **not** needed.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-28-snake-royale/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

```bash
jq -r '.certify.ok' runs/2026-08-28-snake-royale/release-result.json
```
```
true
```

The same string in context, from `.certify.output_tail` in that file (the certifier's own tail, 10/10 steps
passed):
```
  [pass] replay-present: a replay artifact was produced
  [pass] replay-loadable: the replay artifact has a declared viewer path
  [pass] players-run: every declared player actually started on the smoke episode (not just declared)
  [pass] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks
Certified dist/coworld_manifest.json
Transcript: coworld-executable (10 steps passed)
…
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

**Status: TRUE** — the required substring `Replay liveness: skipped (static replay bundle declared` is
present, read from the committed artifact (not `/tmp`, which is gone).

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — TRUE

**(a) Dispatch.** `SRC` is the check-6 iframe `src`, verbatim including the `#replay=` fragment.

```bash
SRC=$(jq -r '.viewer_url' /tmp/session.json)
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90   # dispatched 2026-08-28T08:04:54Z
sleep 12
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:3][]|[.databaseId,.createdAt,.status]|@tsv'
```
```
33153918882	2026-08-28T08:04:55Z	in_progress      <- created AFTER the 08:04:54Z dispatch: this run
33136591103	2026-08-28T02:39:59Z	completed
33135119698	2026-08-28T02:10:50Z	completed
```
The run was identified by `createdAt` > dispatch time (sorted), not by taking "the latest run" blind.

```bash
gh run watch 33153918882 -R Metta-AI/coworld-builder --exit-status ; echo "watch_exit=$?"
gh run view 33153918882 -R Metta-AI/coworld-builder --json conclusion,status,url
```
```
✓ main viewer-check · 33153918882
✓ viewer-check in 33s (ID 98792099767)
  ✓ Load the viewer
  ✓ Fail if the viewer did not load
watch_exit=0
{"conclusion": "success", "status": "completed",
 "url": "https://github.com/Metta-AI/coworld-builder/actions/runs/33153918882"}
```

```bash
gh run download 33153918882 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-28-snake-royale/viewer-check
ls -la runs/2026-08-28-snake-royale/viewer-check/
```
```
-rw-r--r-- smoke-stderr.txt        0
-rw-r--r-- smoke-stdout.txt      719
-rw-r--r-- viewer-smoke.json    1515
-rw-r--r-- viewer-smoke.png   338403
```
Committed with this file (`runs/2026-08-28-snake-royale/viewer-check/`).

**(b) Readouts.**

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-28-snake-royale/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":2998,"clock":"ALIVE 4/4 turn 0/50 BEFORE THE FIRST MOVE","scorebug":"daveey COG-alpha 3 LEN HP ↯ Baseline COG-gamma 3 LEN HP ALIVE 4/4 turn 0/50 BEFORE THE FIRST MOVE daveey-1 COG-beta 3 LEN HP ↯ Baseline (2) COG-delta 3 LEN HP","feed_lines":0}
```

```bash
jq -c '.signals' runs/2026-08-28-snake-royale/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-28-snake-royale/viewer-check/viewer-smoke.json
```

| scrub | clock readout |
|---|---|
| **0 %** | `ALIVE 4/4 turn 0/50 BEFORE THE FIRST MOVE` |
| **50 %** | `ALIVE 3/4 turn 26/50 ROYALE · 17×9 · WALLS · FOOD 3 · HEALTH ON` |
| **100 %** | `ALIVE 2/4 turn 50/50 ROYALE · 17×9 · WALLS · FOOD 3 · HEALTH ON` |

```bash
jq -r '.failure // "no failure"' runs/2026-08-28-snake-royale/viewer-check/viewer-smoke.json
```
```
no failure
```

Also from the same artifact (`status`, `loading_text`, `canvas_text`, `console_tail`):
```json
"status": "LIVE", "loading_text": null,
"canvas_text": {"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]},
"console_tail": []
```

**Both conditions hold: `loaded: true` (first frame at 2998 ms, `data-replay-loaded="true"`) and the three
clock readouts differ** (turn 0 → 26 → 50, alive 4/4 → 3/4 → 2/4). No page error, no console output, no
`loading_text` left on screen. `#scrub` exists (the scrub readouts were taken by dragging it), so the
missing-scrubber caveat does not apply. `bridge_ready:false` is not a defect: the load signal arrived via
the `data-replay-loaded` attribute, which the checker accepts as either-or.

**(c) Spectator judgment.**

`viewer-smoke.png` (1280×800, captured after the 100 % scrub) shows a finished match, and it is legible.
Top of frame is the **transport/scorebug strip**: four cogs by real name and alias with length and health
pips — `daveey · COG-alpha 0`, `Baseline · COG-gamma 15`, `daveey-1 · COG-beta 9`, `Baseline (2) · COG-delta 0`
with `#3`/`#4` place chips — around a centred clock reading `ALIVE 2/4 / turn 50/50 / ROYALE · 17×9 · WALLS ·
FOOD 3 · HEALTH ON`. Behind a dimmed veil the **fixed 17×9 arena** is still visible: dark grid, three red
apples, and the olive and teal snake bodies coiled through the right-centre of the board — no zoom panel,
which the design deliberately dropped. Dominating the centre is the **endcard**: `Baseline SURVIVES — 15
long, 12 eaten, 50 turns`, a `FULL TIME` badge, the subtitle `royale · 17×9 · walls · food 3 · health on ·
full_time at turn 50`, headline figures `50 TURNS SURVIVED` / `15 FINAL LENGTH`, and the results table with
exactly the declared columns **`COG | PLACE | TURNS | LENGTH | ATE | SOFT`**:

| COG | PLACE | TURNS | LENGTH | ATE | SOFT |
|---|---|---|---|---|---|
| daveey · COG-alpha | 4 | 8 | 3 | 0 | 0 |
| daveey-1 · COG-beta | 2 | 50 | 9 | 6 | 0 |
| Baseline · COG-gamma | 1 | 50 | 15 | 12 | 1 |
| Baseline (2) · COG-delta | 3 | 42 | 8 | 5 | 0 |

Every cell reconciles with the replay record in §4: `place [4,2,1,3]`, `survivedTurns [8,50,50,42]`,
`finalLength [3,9,15,8]`, `foodEaten [0,6,12,5]`, `declinedKills [0,0,1,0]` → the `SOFT` column's single 1,
`endRule "full_time"`. A `DUEL — HALF SPEED` banner and a speech bubble reading `Last turn - staying safe`
sit above it — that string is literally the turn-50 seat-1 `say` in the replay
(`50  1  Last turn - staying safe`). Bottom right, three killfeed lines in the `.feed` element are legible:
`COG-beta: "Ate food #3, length 6"`, `COG-beta: "Length 6, chasing food a"`, `COG-beta: "Last turn -
staying safe"` — turns 25, 26 and 50 of the replay, verbatim. Across the bottom is the **transport strip**:
restart, step-back, play, `+5s`, step, loop and fast-forward buttons, a `spoilers` toggle, a `50 / 50`
counter, speed chips `1× 2× 3× 4× 8× 16×`, and beneath them the **scrubber with beat ticks** (green, red and
amber markers at eat/death/gameover beats) over a `LENGTH` **momentum graph** whose four traces step upward
across the episode. That is the paintbot/raid/hive chrome of the starter lineage — same transport strip,
same scrubber-plus-momentum, same scorebug, same endcard shape — not a lookalike rewrite; nothing here
resembles the cogame-gridlock failure mode.

The picture is neither empty nor frozen: the three scrub readouts move the clock through turns 0, 26 and 50
and drop the alive count 4 → 3 → 2, matching the replay's deaths at turn 8 (seat 0, wall) and turn 42
(seat 3, body). Two legibility observations for the coordinator, neither of them failures: (i) the
DOM `feed_lines: 0` was sampled at load time, when the clock read `turn 0/50 BEFORE THE FIRST MOVE` and an
empty feed is correct — the screenshot proves the feed does populate, so this is an artefact of *when* the
checker samples, not a missing killfeed; (ii) after the 100 % seek the feed still shows two turn-25/26
lines alongside the turn-50 line, i.e. a seek does not flush the feed queue — cosmetic, worth a note for
phase 30, and it happens to be the reason the feed is readable at all in a post-scrub screenshot.

**Status: TRUE** — `loaded: true`, three differing clock readouts, no failure, and the rendered frame shows
the game this coworld is about (four snakes on a 17×9 walled arena, apples eaten, placements, and a
full-time endcard) in the starter's chrome.

---

## Summary table

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** (rounds 2 @ 07:44:31Z, 3 @ 08:00:44Z; round 1 `failed`, quoted) |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** (daveey-1 rank 1, daveey rank 2, both `rounds_played` 2) |
| 3 | Latest round's episode request completed with a replay | **TRUE** (`ereq_8dbbce59-…` completed, replay_url non-null, daveey + daveey-1 seated) |
| 4 | Replay bytes valid and show the game | **TRUE** (`snake-royale/v1`, `reason complete`/`full_time`, 0 % fallback turns, zero-sum scores) |
| 5 | Hosted game log clean | **TRUE** (CLEAN on the gate grep, decoded and raw; round-2 advisory recorded) |
| 6 | Public page uses the static replay path | **TRUE** (static route + manifest sha + `ready:true`; featured match `snake-royale.r3.e1`) |
| 7 | Certification declared the static bundle | **TRUE** (`Replay liveness: skipped (static replay bundle declared…`, committed artifact) |
| 8 | Spectator judgment — viewer executed and legible | **TRUE** (`loaded:true` @ 2998 ms, clocks 0/50 → 26/50 → 50/50, run `33153918882`) |

Replay under test: `https://softmax-public.s3.amazonaws.com/replays/544f5847-40b8-4c88-b209-b2ca4b966226.replay`
Viewer URL: `https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_dfae8bd2-c198-460c-acaf-1c3fc709688c/sha256%3A7c10c697df9f3ce9cf043d3e3964fb31a97a7aa46d0720581188f0ae49795ca3/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F544f5847-40b8-4c88-b209-b2ca4b966226.replay`
Viewer-check run: `https://github.com/Metta-AI/coworld-builder/actions/runs/33153918882` (artifact committed at `runs/2026-08-28-snake-royale/viewer-check/`)
