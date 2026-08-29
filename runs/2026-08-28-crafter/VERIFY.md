# VERIFY — crafter   (2026-08-29T04:31Z)

Verdict: **7 of 8 items TRUE; item 6 PARTIAL** — the static replay route is TRUE and proven, the
*featured match* sub-clause is FALSE as fetched (`state.playlist: []`) with a documented,
cross-checked platform-wide cause (single-policy-per-episode coworlds get no SSR playlist entry;
reproduced live on `nethack` and `procgen`, and disproven as "fewer than two ranked players" —
crafter has exactly two ranked players). Items 1–5, 7 and 8 are TRUE on freshly fetched evidence.

Two non-blocking findings are recorded below and are for the coordinator/phase 30, not check
failures: **(A)** the live viewer emits 8 console `404`s for leftover coworld-ctf
`soldier_{green,yellow,blue,red}_front[_gun].png` sprites (§8); **(B)** the end-of-episode
achievement endcard overflows the 800 px viewport and superimposes on the scorebug, the clock and
the transport strip (§8, screenshot).

Run facts used: slug `crafter`, `COW=cow_88aa79dd-1661-4c42-9024-abb912d2de34`, version `0.1.0`,
manifest hash `sha256:6b9fed359dc51ac6d4805de96020a2f1972b9d80d772fb66a2d2514c78371deb`,
`L=league_791e396c-32b3-47f1-bd94-23e276f6b6c5`, `D=div_160b65a4-63bf-4ce9-8bc7-a6e0e9c3b6f5`,
`BASE=https://softmax.com/api/observatory/v2`.

Headers sent on every Observatory call (values never printed): `Authorization: Bearer $SOFTMAX_TOKEN`
and `User-Agent: coworld-builder/1.0`; on the artifact-log and filler-policy reads additionally
`X-Use-Elevated-Privileges: true`.

**List-shape note (what I actually used).** The coordinator's phase-50 observation is confirmed for
`/leagues` and `/policy-versions` (bare arrays) but **`GET /rounds?league_id=…` returned `.entries`**
this run, so the SPEC/prompt jq (`.entries[]`) was used verbatim for rounds. `GET /divisions/<D>/leaderboard`
returned a **bare list** (`.[]`), as the playbook says. `GET /episode-requests?round_id=` is dead
(405, playbook §9), so the **nested** route `GET /rounds/<R>/episode-requests` was used and is noted
inline at §3. `GET /coworlds?limit=200` returned `.entries`.

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

Fillers were registered at 2026-08-29T04:02Z, **before** the first `trigger-round`
(`runs/2026-08-28-crafter/log.md:34`). Confirmed live this run that exactly the two scripted
baselines are the fillers and neither is a champion version:

```
GET $BASE/leagues/$L/filler-policies      (headers: Authorization, User-Agent, X-Use-Elevated-Privileges)
```
```json
{
  "filler_policy_versions": [
    {"policy_version_id": "72a75938-334c-4ecd-8355-51c8aa5bc12c", "policy_id": "85b5af3a-2d97-44d7-87e9-55158a035db8",
     "policy_name": "crafter-forager",  "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
     "player_name": "daveey", "display_name": null},
    {"policy_version_id": "6f66cf9c-b4b1-4a1f-9049-97211decde06", "policy_id": "7f8045d6-8f72-4136-8260-70f930e02050",
     "policy_name": "crafter-wanderer", "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
     "player_name": "daveey", "display_name": null}
  ]
}
```

```
GET $BASE/rounds?league_id=$L&limit=20        (fetched 2026-08-29T04:21:35Z)
 | jq -r '[.entries[]|select(.status=="completed")]|length'
```
```
2
```

Full rows (trimmed to the fields the check uses; `error` pasted verbatim — both `null`):

```json
{"entries": [
  {"id": "round_48bbe21e-05da-453d-9bfa-ae4ef461f4bc", "round_number": 2, "status": "completed",
   "error": null, "completed_at": "2026-08-29T04:19:34.714350Z",
   "entrants": [{"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "policy_version_id": "5c634744-0196-4d72-b577-40796ff56472"},
                {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "policy_version_id": "631aa26c-149f-4ea4-9063-a3194e9edae4"}]},
  {"id": "round_5c919ee7-5d5d-45a0-aed6-1f3a5ff9e875", "round_number": 1, "status": "completed",
   "error": null, "completed_at": "2026-08-29T04:04:27.558847Z",
   "entrants": [{"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "policy_version_id": "5c634744-0196-4d72-b577-40796ff56472"},
                {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "policy_version_id": "631aa26c-149f-4ea4-9063-a3194e9edae4"}]}
]}
```

Poll log this session (each an independent `GET /rounds`):

| UTC | rounds seen |
|---|---|
| 04:05:30 | 1 completed |
| 04:07:32 | 1 completed |
| 04:12:47 | 1 completed |
| 04:18:23 | 1 completed, 2 **pending** |
| 04:21:29 | 1 completed, 2 **completed** (04:19:34Z) |
| 04:35:22 | 1, 2, **3** completed (round 3 at 04:35:05Z) — after this document's evidence was captured |

A third round completed at 2026-08-29T04:35:05Z, *after* checks 3–5 and 8 had been captured.
Checks 3, 4, 5 and 8 are therefore taken against **round 2**, which was the latest completed round
at their fetch times (04:21–04:28Z), and this is stated so nothing here rests on a stale premise.
The check-1 requirement (≥2 completed rounds) is satisfied by rounds 1 and 2 and is only
strengthened by round 3.

Status: **TRUE** — rounds 1 and 2 both `completed`, `error: null`, both entirely after the fillers
were registered (04:02Z, before round 1 was triggered). Zero `failed`/`discarded` rounds exist, so
there is no `error` text to quote. Both rounds seated exactly the two champion policy versions.

---

## 2. Both champions ranked, fillers absent — **TRUE**

```
GET $BASE/divisions/$D/leaderboard            (fetched 2026-08-29T04:21:36Z; BARE LIST, not .entries)
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey	crafter-techtree:v1	1001.4695015289755	2	1.0
2	daveey-1	crafter-homesteader:v1	998.5304984710245	2	1.0
```

Full body:

```json
[
  {"rank": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
   "score": 1001.4695015289755, "score_label": "MMR", "rounds_played": 2, "episode_wins": 1.0,
   "win_rate": 0.5, "policy_label": "crafter-techtree:v1"},
  {"rank": 2, "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
   "score": 998.5304984710245, "score_label": "MMR", "rounds_played": 2, "episode_wins": 1.0,
   "win_rate": 0.5, "policy_label": "crafter-homesteader:v1"}
]
```
```
jq -r 'length'  ->  2
jq -r '.[]|.policy_label'  ->  crafter-techtree:v1
                               crafter-homesteader:v1
```

Status: **TRUE** — `daveey` (`crafter-techtree:v1`) and `daveey-1` (`crafter-homesteader:v1`) are
both ranked with `rounds_played = 2 ≥ 1`. The board has exactly 2 rows: the fillers
`crafter-forager:v1` / `crafter-wanderer:v1` are **absent**, as required (no `Baseline (N)` rows were
needed — the ladder seated both champions in both rounds and never had to fill).

---

## 3. Latest round's episode request completed with a replay — **TRUE**

`R` = latest completed round by `round_number` = `round_48bbe21e-05da-453d-9bfa-ae4ef461f4bc`
(round 2, completed 04:19:34Z).

The flat route in the prompt (`GET /episode-requests?round_id=`) is dead — playbook §9 records
`405 Method Not Allowed (allow: POST)` since 2026-08-26. I used the **nested** route the playbook
prescribes:

```
GET $BASE/rounds/$R/episode-requests           (fetched 2026-08-29T04:21:52Z)
 | jq -r '.entries[]|[.id,.status,.replay_url]|@tsv'
```
```
ereq_067f4396-4e06-4edf-8a6f-0e79f0d6ab1a	completed	https://softmax-public.s3.amazonaws.com/replays/1072532a-9aef-4d0b-91f6-d874077681e4.replay
ereq_2cd155c7-b2f0-4f51-82d4-076efcc56c9d	completed	https://softmax-public.s3.amazonaws.com/replays/2acfb709-e336-4796-90e7-16c563394e22.replay
```

**Single-seat caveat, stated up front:** crafter is `num_agents: 1` (design note; confirmed by the
replay config `"num_agents":1,"minPlayers":1`). A round therefore fans out into **one episode
request per champion**, each with exactly one participant — no single episode request can name both
`daveey` and `daveey-1`. The round as a whole seats both (see §1 `entrant_attributions`). I fetched
**both** of round 2's episode requests rather than only `.entries[0]`, so the check's "participants
named correctly" is proven across the round:

```
GET $BASE/episode-requests/ereq_067f4396-4e06-4edf-8a6f-0e79f0d6ab1a | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/1072532a-9aef-4d0b-91f6-d874077681e4.replay",
  "participants": [
    {"position": 0, "kind": "policy", "policy_version_id": "631aa26c-149f-4ea4-9063-a3194e9edae4",
     "policy_id": "3e6ad9d7-8f96-4dad-9247-c5aeb9e5c16d", "policy_name": "crafter-homesteader", "version": 1,
     "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
     "is_filler": false, "is_seed": false}
  ],
  "participant_scores": [{"position": 0, "score": 20440.0}]
}
```
```
GET $BASE/episode-requests/ereq_2cd155c7-b2f0-4f51-82d4-076efcc56c9d | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/2acfb709-e336-4796-90e7-16c563394e22.replay",
  "participants": [
    {"position": 0, "kind": "policy", "policy_version_id": "5c634744-0196-4d72-b577-40796ff56472",
     "policy_id": "7510989a-4e67-4980-a64a-8a859a28ad47", "policy_name": "crafter-techtree", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "is_filler": false, "is_seed": false}
  ],
  "participant_scores": [{"position": 0, "score": 40350.0}]
}
```

Status: **TRUE** — both of the latest round's episode requests are `status: "completed"` with a
non-null `replay_url`; participants are `daveey-1`/`crafter-homesteader:v1` and
`daveey`/`crafter-techtree:v1`, both `is_filler: false`. No `Baseline (N)` seats exist because no
filler was needed.

---

## 4. Replay bytes are valid and show the game — **TRUE**

The replay is the starter's **binary `COWLDCRF`** container, not raw JSON — this is a declared design
decision, not a defect. Design note `runs/2026-08-28-crafter/design.md:1354-1379` ("Replay bytes
(self-sufficient)") keeps the coworld-ctf binary codec because the static wasm viewer parses exactly
that, and it declares the **phase-60 substitute** for this check: run the repo's stdlib-only
`tools/replay_summary.py`, which emits one strict-UTF-8 JSON object, and parse *that* with `jq -e`.
I fetched the tool fresh from the repo this run and used it exactly as the design specifies.

```
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/1072532a-9aef-4d0b-91f6-d874077681e4.replay" -o /tmp/ep_r2_h.replay
   -> HTTP 200  86471 bytes
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/2acfb709-e336-4796-90e7-16c563394e22.replay" -o /tmp/ep_r2_t.replay
   -> HTTP 200  66560 bytes

jq -e . /tmp/ep_r2_h.replay      -> jq: parse error: Invalid numeric literal at line 1, column 33
head -c 8 /tmp/ep_r2_h.replay    -> COWLDCRF          (the declared binary magic, design.md:1057/1384)

gh api repos/Metta-AI/cogame-crafter/contents/tools/replay_summary.py | base64 -d > /tmp/replay_summary.py   (193 lines)
python3 /tmp/replay_summary.py /tmp/ep_r2_h.replay > /tmp/ep_r2_h.json && jq -e . /tmp/ep_r2_h.json >/dev/null
   -> strict UTF-8 JSON: ok
python3 /tmp/replay_summary.py /tmp/ep_r2_t.replay > /tmp/ep_r2_t.json && jq -e . /tmp/ep_r2_t.json >/dev/null
   -> strict UTF-8 JSON: ok
```

The raw container header is legible in the bytes and carries the game name and the config inline:

```
0000000   C O W L D C R F 001 \0 \a \0 c r a f t e r 001 \0 1 350 223 257 K 240 001 \0 \0 234 002
0000040   { " s e e d " : 1 2 6 9 7 9 8 1 0 9 , " v a r i a n t " : " s t a n d a r d " ,
          " n u m _ a g e n t s " : 1 , " m i n P l a y e r s " : 1 , " p l a y e r s " : [ { " n a m e " : " d a v e e y - 1 " } ] …
```

```
jq -r '.protocol, .results.reason, .results.endRule, .results.achievementsUnlocked' /tmp/ep_r2_h.json   # daveey-1 / homesteader
```
```
crafter/v1
complete
death
2
```
```
jq -r '.protocol, .results.reason, .results.endRule, .results.achievementsUnlocked' /tmp/ep_r2_t.json   # daveey / techtree
```
```
crafter/v1
complete
death
4
```
```
jq -r '([.plans[]|select(.source=="llm")]|length), .fallbacks, (.says|length)' /tmp/ep_r2_h.json   ->  19  0  19
jq -r '([.plans[]|select(.source=="llm")]|length), .fallbacks, (.says|length)' /tmp/ep_r2_t.json   ->  15  0  15
```

`protocol` matches the manifest's declared `crafter/v1` (design §Packaging; also visible in the
release artifact's certified manifest). `results.reason == "complete"` for **both** — no `deadline`
exception is needed. `endRule: "death"` is a completion, per the design note (a death is complete).

Champion seats are doing the thing the game is about. Verb histograms and `say` lines, pasted:

```
jq -r '[.plans[].verbs[]]|group_by(.)|map({v:.[0],n:length})|sort_by(-.n)|.[]|"\(.v)\t\(.n)"' /tmp/ep_r2_t.json
```
```
move	21
do	17
goto	9
make_wood_pickaxe	5
make_wood_sword	5
place_table	5
place_stone	1
sleep	1
```
```
jq -r '.plans[]|[.turn,.tick,.source,(.verbs|join("+")),(.say)]|@tsv' /tmp/ep_r2_t.json    (all 15 turns)
```
```
1	127	llm	goto+do+place_table+make_wood_pickaxe+make_wood_sword	Climb the tree. Chop it down, build tools, build table. First four achievements locked.
2	151	llm	do+goto+do	Finishing tree chop at (30,33), then will proceed to stone mining.
3	175	llm	do+place_table+make_wood_pickaxe+make_wood_sword	Executing turn 1 plan: chop tree x3, place table, craft pickaxe and sword.
4	199	llm	goto+do+move+move	Exploring south to find stone deposits in the grey # regions visible on the map.
5	223	llm	goto+do+place_table+make_wood_pickaxe+make_wood_sword	Turn 1: goto tree, chop x5, place table, craft pickaxe and sword. Four achievements locked.
6	247	llm	goto+do	Chop final tree piece, then scout for stone country.
7	271	llm	place_table+make_wood_pickaxe+make_wood_sword+move+goto	Place table here, craft pickaxe and sword, head north to find stone
8	295	llm	move+move+do+place_stone	Night phase with zombie nearby - seal in, then search for stone. Drink at 4, food at 5, energy at 6 all acceptable. Table placed at 33,34.
9	314	llm	move+move+do+move+move	Zombie on me, escape west then south to safe ground. Drink at 3, need to find stone.
10	338	llm	move+do+move+move+do	Drinking before exploring for stone. Then heading west to find stone region.
11	362	llm	move+move+place_table+make_wood_pickaxe+make_wood_sword+move+do	Placing table at 30,31. Making wood tools. Mining stone west.
12	386	llm	do+move+do+move+goto	Drink first (drink=1), then continue stone mining west into the # region.
13	410	llm	do+move+do+move+goto	Drinking immediately (drink=0), then mining west into stone region. Moving toward unexplored stone area.
14	434	llm	move+goto	Critical: drink=0 kills me. Heading to stone region to tunnel west.
15	458	llm	move+do+sleep	Zombie at 28,29 - drinking, then sleeping to restore energy safely before continuing stone collection.
```
```
jq -c '{names,aliases,policyKinds,tickCount,scores:.results.scores,death:.results.deathCause,blocksPlaced:.results.blocksPlaced,itemsCrafted:.results.itemsCrafted,blocksMined:.results.blocksMined,toolsOwned:.results.toolsOwned,llmTurns:.results.llmTurns,fallbackTurns:.results.fallbackTurns,achievements:.achievements}' /tmp/ep_r2_t.json
```
```json
{"names":["techtree"],"aliases":["Alpha"],"policyKinds":["llm"],"tickCount":350,"scores":[40350],
 "death":"thirst","blocksPlaced":1,"itemsCrafted":2,"blocksMined":19,
 "toolsOwned":["wood_pickaxe","wood_sword"],"llmTurns":15,"fallbackTurns":0,
 "achievements":["collect_wood","place_table","make_wood_pickaxe","make_wood_sword"]}
```
```
jq -c '{names,aliases,policyKinds,tickCount,scores:.results.scores,death:.results.deathCause,blocksPlaced:.results.blocksPlaced,itemsCrafted:.results.itemsCrafted,blocksMined:.results.blocksMined,toolsOwned:.results.toolsOwned,llmTurns:.results.llmTurns,fallbackTurns:.results.fallbackTurns,achievements:.achievements}' /tmp/ep_r2_h.json
```
```json
{"names":["homesteader"],"aliases":["Alpha"],"policyKinds":["llm"],"tickCount":440,"scores":[20440],
 "death":"starvation","blocksPlaced":0,"itemsCrafted":0,"blocksMined":0,"toolsOwned":[],
 "llmTurns":19,"fallbackTurns":0,"achievements":["collect_drink","wake_up"]}
```

Status: **TRUE** on the prompt's criteria — strict-UTF-8 JSON via the design's declared substitute,
`protocol == "crafter/v1"`, `results.reason == "complete"`, and champion decisions that are
**100 % `source: "llm"` with 0 fallbacks** (`fallbackTurns: 0`, `fallbacks: 0` in both episodes) and
non-trivial content: real verbs (`goto`, `do`, `place_table`, `make_wood_pickaxe`,
`make_wood_sword`, `place_stone`, `sleep`), 34 distinct `say` lines that reason about hunger, thirst,
night, zombies and the tech tree, and a techtree seat that actually mines 19 blocks, places a table
and crafts two tools.

**Recorded shortfall against the design's own stricter bar (not a prompt/SPEC criterion).**
`design.md:1370` asks the phase-60 substitute to additionally require
`results.achievementsUnlocked >= 3`. Per episode, this run: round 2 techtree **4** (clears it),
round 2 homesteader **2** (below it); round 1 was 2 and 2. `parAchievements` is 8. The homesteader
episode also shows `blocksMined: 0`, `itemsCrafted: 0`, `cellsSeen: 121/4096` — 19 LLM turns spent
wandering NW looking for a tree, then starving. Nothing about that is a fallback or a fault, and the
prompt's and SPEC's check-4 wording is met; I am flagging it because it is the design's own declared
bar and because it bears on §8's spectator judgment. This is a difficulty/prompt-tuning observation
for the coordinator, not a check failure.

---

## 5. Hosted game log is clean — **TRUE**

Logs bodies are python `b'…'` byte-string reprs under `===== container: … =====` headers (playbook
§10), so I decoded each repr with `ast.literal_eval` before grepping (a line-based grep undercounts).

```
GET $BASE/episode-requests/ereq_067f4396-4e06-4edf-8a6f-0e79f0d6ab1a/artifacts/logs
    (headers: Authorization, User-Agent, X-Use-Elevated-Privileges)   -> HTTP 200, 3283 bytes
python3 decode_logs.py logs_r2_h.txt > logs_r2_h.decoded.txt          -> 36 decoded lines
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs_r2_h.decoded.txt || echo CLEAN
```
```
CLEAN
```
```
GET $BASE/episode-requests/ereq_2cd155c7-b2f0-4f51-82d4-076efcc56c9d/artifacts/logs   -> HTTP 200, 2836 bytes
python3 decode_logs.py logs_r2_t.txt > logs_r2_t.decoded.txt          -> 32 decoded lines
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs_r2_t.decoded.txt || echo CLEAN
```
```
CLEAN
```

The decoded `game` container of the round-2 techtree request, pasted in full:

```
===== container: game =====
crafter llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
crafter: serving on 0.0.0.0:8080 seed 1270695359 variant standard
crafter: player connected on slot 0
crafter: seat 0 registered as techtree (llm)
Dropped message to disconnected client
crafter: episode complete — reason complete endRule death unlocked 4/22 ticks 350 score 40350
```

and of the round-2 homesteader request:

```
===== container: game =====
crafter llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
crafter: serving on 0.0.0.0:8080 seed 1270695960 variant standard
crafter: player connected on slot 0
crafter: seat 0 registered as homesteader (llm)
Dropped message to disconnected client
crafter: episode complete — reason complete endRule death unlocked 2/22 ticks 440 score 20440
```

Every LLM call succeeded — the `bedrock-sidecar` container shows 15 and 19 upstream calls
respectively, all `200 OK`, no throttling:

```
grep -c "200 OK" logs_r2_t.decoded.txt   -> 15     (= techtree's 15 llmTurns)
grep -c "200 OK" logs_r2_h.decoded.txt   -> 19     (= homesteader's 19 llmTurns)
```
```
2026-08-29 04:18:0x,xxx INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"     (×15 / ×19)
```

Status: **TRUE** — zero lines matching `falling back|LLM provider is unavailable|cut off at
max_tokens|rejected` in either of the latest round's hosted logs. The capacity-exception clause was
**not needed**: no `LLM provider is unavailable` and no Bedrock 429 appeared at any point, so no
sibling-coworld cross-check was required. (The only non-LLM line, `Dropped message to disconnected
client`, is the server's ordinary shutdown notice after `episode complete` and matches none of the
four patterns.)

---

## 6. The public page uses the static replay path — **PARTIAL (6a TRUE, 6b FALSE with a documented platform-wide cause)**

### 6a. The iframe `src` is the static route — **TRUE**

Raw-HTML grep first, as the prompt orders:

```
curl -sS "https://softmax.com/crafter" | grep -o '<iframe[^>]*src="[^"]*"'     (fetched 2026-08-29T04:30:10Z)
   -> HTTP 200, 766570 bytes
   -> (no output)  RAW-HTML GREP: no <iframe … src=> in the served HTML
```

This is the **unknown**, not a failure, that the playbook §Featured match documents: the page is
client-rendered for the iframe and the grep finds nothing for *any* coworld. The playbook's answered
fallback is the call the page's own JS makes; that is the source I used, and I say so here:

```
POST $BASE/coworlds/replays/session          (headers: Authorization, User-Agent)
  -d '{"coworld_id":"cow_88aa79dd-1661-4c42-9024-abb912d2de34",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/1072532a-9aef-4d0b-91f6-d874077681e4.replay"}'
   -> HTTP 200
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_88aa79dd-1661-4c42-9024-abb912d2de34/sha256%3A6b9fed359dc51ac6d4805de96020a2f1972b9d80d772fb66a2d2514c78371deb/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F1072532a-9aef-4d0b-91f6-d874077681e4.replay",
  "ready": true
}
```

The same call against round 2's other replay returns the same shell:

```json
{"viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_88aa79dd-1661-4c42-9024-abb912d2de34/sha256%3A6b9fed359dc51ac6d4805de96020a2f1972b9d80d772fb66a2d2514c78371deb/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F1ae417ae-f010-41f4-952e-2b67aae5d8f4.replay",
 "ready": true}
```

Path check, term by term: `/v2/coworlds/replays/static/` ✓ · `<cow_id>` =
`cow_88aa79dd-1661-4c42-9024-abb912d2de34` ✓ (matches STATE) · `<sha>` =
`sha256%3A6b9fed359dc51ac6d4805de96020a2f1972b9d80d772fb66a2d2514c78371deb`, the URL-encoded
**manifest_hash** ✓ (matches `STATE.coworld.manifest_sha` and the episode tag
`coworld_manifest_hash` returned by `/episodes/search`) · ends `/index.html` ✓ · carries the S3
replay as the URL-encoded `#replay=` **fragment**, which the playbook records as the post-2026-08-28
form of the same static route ✓ · `ready: true` ✓ · **no `/client/replay` pod URL anywhere** ✓.

**TRUE.** And this is not a paper URL: §8 opened exactly this string in a real browser and it drew.

### 6b. A featured match is present — **FALSE as fetched; documented platform-wide cause**

```
curl -sS "https://softmax.com/crafter"  →  SSR payload, state.playlist
```
```
"leagueId":"league_791e396c-32b3-47f1-bd94-23e276f6b6c5","playlist":[],"pool":{"replays":[{"kind":"replay","round":{"id":"round_48bbe21e-05da-453d-9bfa-ae4ef461f4bc","round_number":2,…
```
```
python3: pool replay_urls = ['replays/1072532a-9aef-4d0b-91f6-d874077681e4.replay',
                             'replays/2acfb709-e336-4796-90e7-16c563394e22.replay']
```

So both of the latest round's replays **are** in the page's `state.pool.replays`, but
`state.playlist` — the field the playbook names as the featured match (`state.playlist[0]`) — is the
empty list. Fetched at 04:12:47Z, 04:18:23Z, 04:22:38Z, 04:25:54Z and 04:30:10Z; empty every time,
including after round 2 landed in the pool.

The prompt's expected cause ("absence = fewer than two ranked players") is **disproven** by §2:
crafter has exactly two ranked players. The actual cause, cross-checked live against five other
coworlds this run, is that the SSR playlist builder only emits an entry for episodes carrying **more
than one policy** (its `matchup` object needs a `first` and a `second`). crafter is a single-seat
game, so every episode carries one policy:

```
for c in crafter nethack procgen minigrid atari-57 bullwhip:
  POST $BASE/episodes/search -d '{"where":{"field":"coworld.name","op":"eq","value":"<c>"},"limit":1}' | jq '.entries[0].policies|length'
  curl -sS https://softmax.com/<c>  →  state.playlist
```
```
crafter            policies/episode=1   SSR state.playlist=EMPTY []
nethack            policies/episode=1   SSR state.playlist=EMPTY []
procgen            policies/episode=1   SSR state.playlist=EMPTY []
minigrid           policies/episode=3   SSR state.playlist=NON-EMPTY
atari-57           policies/episode=3   SSR state.playlist=NON-EMPTY
bullwhip           policies/episode=4   SSR state.playlist=NON-EMPTY
```

`nethack` (0.1.1) and `procgen` are canonical, shipped, single-seat coworlds with live ladders and
they have the identical empty playlist. The `/coworlds` fallback the prompt offers is no help and is
already documented as null platform-wide — confirmed again this run:

```
GET $BASE/coworlds?limit=200 | jq -r '.entries[]|select(.name=="crafter")|{id,canonical,replay_viewer,featured_match}'
```
```json
{"id": "cow_88aa79dd-1661-4c42-9024-abb912d2de34", "name": "crafter", "version": "0.1.0",
 "canonical": true, "replay_viewer": null, "featured_match": null}
```
```
same call, other coworlds:
nethack   0.1.1  canonical=true  replay_viewer=null  featured_match=null
minigrid  0.1.2  canonical=true  replay_viewer=null  featured_match=null
atari-57  0.1.0  canonical=true  replay_viewer=null  featured_match=null
```

Status: **6a TRUE / 6b FALSE as fetched.** I am not marking 6b true by inference. The evidence says
the featured match is absent, and the evidence also says the cause is a platform property of
single-policy-per-episode coworlds rather than anything crafter did wrong — reproduced on two
shipped single-seat coworlds and contrasted against three multi-seat ones, all fetched this run.
The coordinator/judge should decide whether that is an acceptable documented exception; §8 proves
the viewer works regardless, and a spectator reaching the page still gets the pool.

---

## 7. Certification declared the static bundle — **TRUE**

Source used: **the committed copy** `runs/2026-08-28-crafter/release-result.json` (phase 40's
downloaded artifact, present in the run directory — no re-download from run `33232381840` was
needed).

```
jq -r '.certify.replay_liveness' runs/2026-08-28-crafter/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Contains the required substring `Replay liveness: skipped (static replay bundle declared`. The
surrounding certification transcript from the same file, for context:

```
jq -r '.certify.ok' runs/2026-08-28-crafter/release-result.json   ->  true
```
```
Certifying dist/coworld_manifest.json against transcript coworld-executable
  [pass] matriculate: manifest conforms to the Coworld schema
  [pass] source-resolves: whether each runnable declares a source_url that resolves to publicly accessible source
  [pass] images-reachable: every declared image is pullable or inspectable
  [pass] fixture-conforms: the certification fixture validates against game.config_schema after runner token injection
  [pass] smoke-episode: the game and certification players run one episode
  [pass] results-conform: episode results validate against results_schema
  [pass] replay-present: a replay artifact was produced
  [pass] replay-loadable: the replay artifact has a declared viewer path
  [pass] players-run: every declared player actually started on the smoke episode (not just declared)
  [pass] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks
Certified dist/coworld_manifest.json
Transcript: coworld-executable (10 steps passed)
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE**.

---

## 8. The viewer is EXECUTED, then judged — **TRUE**

### 8a. Dispatch and run

```
SRC = the §6a viewer_url verbatim (static route, ?v=2#replay=<s3 url> for
      replays/1072532a-9aef-4d0b-91f6-d874077681e4.replay — the first episode request of the
      latest completed round, i.e. the same bytes checks 3 and 4 verified)

dispatch stamp: 2026-08-29T04:27:01Z
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
```

Find-the-new-run by `createdAt`, never by bare latest:

```
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status,conclusion -L 10
 | jq -r 'sort_by(.createdAt)|reverse|.[]|[.databaseId,.createdAt,.status,(.conclusion//"-")]|@tsv'
```
```
33233844065	2026-08-29T04:27:03Z	in_progress	-        <-- created 2s AFTER my dispatch stamp: this run
33233650158	2026-08-29T04:22:11Z	completed	success  <-- another run's; not mine
33233338285	2026-08-29T04:14:31Z	completed	success
33227616497	2026-08-29T01:54:33Z	completed	success
…
```
```
gh run watch 33233844065 -R Metta-AI/coworld-builder --exit-status
  ✓ viewer-check in 50s (ID 99051243458)
    ✓ Install Playwright (pinned 1.55.0) / ✓ Load the viewer / ✓ Summary / ✓ Upload the evidence
    ✓ Fail if the viewer did not load
  watch exit=0      (green)

gh run download 33233844065 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-28-crafter/viewer-check
  viewer-smoke.json  3625 B
  viewer-smoke.png   329089 B
  smoke-stdout.txt   615 B
  smoke-stderr.txt   0 B
```

`viewer_check_run = 33233844065`. The artifact is committed at
`runs/2026-08-28-crafter/viewer-check/`.

### 8b. The readouts, verbatim

```
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-28-crafter/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":3410,"clock":"DAY 1 · DAY TICK 0/1344 · HP 9 · SCORE 0","scorebug":"DAY 1 HOMESTEADER Carrying 0/22 ALPHA · SCORE 0 DAY 1 · DAY TICK 0/1344 · HP 9 · SCORE 0","feed_lines":0}
```
```
jq -c '.signals' runs/2026-08-28-crafter/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```
```
jq -r '.failure // "no failure"' runs/2026-08-28-crafter/viewer-check/viewer-smoke.json
```
```
no failure
```

The three scrub readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | `#clock` readout |
|---|---|
| 0 %   | `DAY 1 · DAY TICK 0/1344 · HP 9 · SCORE 0` |
| 50 %  | `DAY 2 · DAY TICK 221/1344 · HP 9 · SCORE 10221` |
| 100 % | `DAY 3 · DAY TICK 440/1344 · HP 0 · SCORE 20440` |

All three differ, in all four fields (day, tick, HP, score). A `#scrub` **is** present — this shell
does not report `"(no #scrub…)"`, so no substitute judgment was needed. Additional readouts from the
same artifact:

```
"status": "OPEN", "loading_text": null,
"canvas_text": {"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"samples":[]}
```
`never_inside: 0` — no caption was ever drawn outside the canvas (the cogchemists failure mode is
absent; the chrome text is DOM, not canvas-drawn, hence `total: 0`).

**Finding (A) — 8 console 404s, coworld-ctf sprite leftovers.** `console_tail`, verbatim:

```
[http 404] …/static/cow_88aa79dd…/sha256%3A6b9fed…/soldier_green_front_gun.png
[http 404] …/soldier_green_front.png
[http 404] …/soldier_yellow_front.png
[http 404] …/soldier_yellow_front_gun.png
[http 404] …/soldier_red_front_gun.png
[http 404] …/soldier_blue_front.png
[http 404] …/soldier_blue_front_gun.png
  (each followed by "[error] Failed to load resource: the server responded with a status of 404 ()")
```
Traced to source: `client/replay_broadcast.html:1585-1587` still preloads
`COG_BASE + '/soldier_' + team + '_front.png'` and `…_front_gun.png` for the coworld-ctf team set
{red, blue, green, yellow}, while the crafter bundle ships only `data/soldier_red_front.png`
(`Dockerfile.replay-viewer:35,55`; `gh api …/git/trees/main` shows no green/yellow/blue and no
`_gun` variants). Harmless to the render — `loaded: true`, `failure: null`, clocks advance — but
they are dead requests inherited from the starter and a spectator's console is noisy. Phase-30 item.

### 8c. What the viewer was asked to draw (reconciliation)

From the very replay that was rendered (`/tmp/ep_r2_h.replay`, homesteader, ereq_067f4396):

```
jq -r '.plans[]|[.turn,.tick,.source,(.verbs|join("+")),(.say)]|@tsv' /tmp/ep_r2_h.json      # early
```
```
1	156	llm	move+move	Exploring north and west to find tree + water + stone for base location
2	180	llm	move+move+move+move	Turn 2: Exploring NW to find tree. Water secured at base. Mapping region for stone and optimal settlement spot.
3	204	llm	move+move+move+move	Continuing NW search for tree+water+stone cluster. Water abundant at base. Still seeking tree and stone within reach.
4	228	llm	move+move+move+move	Searching for tree+water+stone triangle for base. Water at (31,31) is excellent. Exploring NW quadrant systematically.
```
```
                                                                                            # middle
9	348	llm	move+do+move+move+do	Drinking at water moat, then searching north for tree. Base confirmed at (31,31).
10	372	llm	do+move+do+move	Drinking to restore drink bar to 9. Water is right in front. Then exploring north for trees.
11	396	llm	do+move+move+move	Food critical (3). Drink now, then search north for tree. Base secure at (31,31).
12	420	llm	do+move+move+move+move	Scouting for tree. Water secured at base (31,31). Food critical - must find and chop tree quickly before night.
```
```
                                                                                            # late
16	516	llm	move+move+move+move+goto	Food critical. Scouting NE for tree/cow. Will return to base water at (31,31) if nothing found.
17	540	llm	move+move+move+move	Scouting NE for tree or cow. Food=0 critical. Base (31,31) water-surrounded. Will return before dark to seal and sleep.
18	564	llm	move+move+move+move	Food critical (0), scouting NE for tree or cow. Base at (31,31). Water nearby for drinking. Must find food source urgently.
19	588	llm	do	CRITICAL: food=0, drinking now. Facing water ahead, will do 4 times to drink to 9.
```
```
jq -r '.results' /tmp/ep_r2_h.json
```
```json
{"names":["homesteader"],"aliases":["Alpha"],"scores":[20440],"win":[false],"winner":null,
 "reason":"complete","endRule":"death","variant":"standard","seed":1270695960,
 "achievementsUnlocked":2,"achievementsOf":22,"parAchievements":8,
 "achievementTick":[-1,-1,-1,-1,194,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,354,-1,-1,-1,-1,-1,-1],
 "survivalTicks":440,"daysSurvived":2,"nightsSurvived":2,"deathCause":"starvation",
 "finalHealth":0,"finalFood":0,"finalDrink":7,"finalEnergy":8,
 "toolsOwned":[],"cellsSeen":121,"cellsTotal":4096,"blocksMined":0,"blocksPlaced":0,
 "itemsCrafted":0,"ticksAsleep":12,"finalTick":440,"turnsPlayed":19,
 "policyKinds":["llm"],"llmTurns":19,"fallbackTurns":0,"deadSeats":[false],"stopDetail":""}
```

The record and the readouts agree exactly. `achievementTick` puts `collect_drink` at tick 194 and
`wake_up` at tick 354; the 50 % readout (tick 221) is already past the first and the 100 % readout
(tick 440, HP 0) is the death. Score 20440 in the replay = score 20440 in the clock = 20440.0 in the
episode-request's `participant_scores`. `survivalTicks 440` = the transport counter's `440 / 441`.

### 8d. Spectator judgment

**It renders, it advances, and it is recognisably this game in the starter's chrome — but the
end-of-episode endcard is a legibility failure.**

The screenshot (`runs/2026-08-28-crafter/viewer-check/viewer-smoke.png`, 1280×800) was taken after
the 100 % scrub, so it shows the final frame plus the endcard. What a spectator sees: a top-down
grid world of tiled water (deep blue with a wave hatch), grass (olive with speckle) and sand (tan),
drawn with real per-tile art on a fine grid, with a small red cog figure standing at the edge of the
grass shelf around x≈660 — this is the "moat" base at (31,31) the `say` lines keep describing, and
the world is mostly black because the seat only ever saw 121 of 4096 cells, exactly as
`cellsSeen: 121` records. Top-right there is a **minimap** panel: a black 64×64 field with the
explored patch drawn in bright blue/green/sand and a white viewport rectangle over it, a `−`/slider/`+`
zoom control reading **`15 CELLS`**, and below it the **9×9 agent inset** captioned
`ALPHA · FACING RI…`. Along the bottom sits the starter's **transport strip** verbatim: restart,
step-back, play, `+5s`, play, loop, fast-forward, a `spoilers` toggle, the frame counter `440 / 441`,
and the speed bank `1× 2× 4× 8× 16× 32×` with `1×` lit amber; under it the **scrubber** (cream bar,
grey played region, amber playhead at the far right) and the **momentum graph** band labelled
`ACHIEVEMENTS` with a red step line that rises twice — once early and once late — matching
`achievementTick` 194 and 354. Top-left is the **scorebug**: `2/22 Carrying` · `HOMESTEADER` ·
`ALPHA · SCORE 20440`, and centre the clock `DAY 3 · DAY`. The **22-chip achievement checklist** is
there, numbered `1 CHOP WOOD` through `22 CUT A DIAMOND`, with `UNLOCKED / TICK / DAY` columns and
`5 DRINK  yes 194 1` and `16 WAKE UP RESTED  yes 354 1` highlighted in white against the dimmed
locked rows. This is unambiguously the paintbot/coworld-ctf lineage — the same transport strip,
scrubber-with-momentum-graph, scorebug and endcard — not a rewrite that shares only the ids. It is
**not** the cogame-gridlock failure.

It advances: three scrub readouts, three different days, ticks, HP values and scores, and the
screenshot's `440 / 441` counter agrees with the replay's `finalTick: 440`. It is not a frozen
frame.

**Finding (B), stated plainly: at 100 % the picture is crowded to the point of illegibility in two
bands.** The endcard's 22-row achievement table is drawn full-height and semi-transparent *over* the
map — map tiles show through rows 10–13 — and it **overflows the 800 px viewport**: row `21 IRON
SWORD` and row `22 CUT A DIAMOND` are drawn behind the transport strip and the momentum graph, cut
off. The top band is worse: at least four text layers are superimposed in the same ~40 px —
the endcard's stat line ("…blocks mined, 0 placed, 0 items crafted, 0 cows eaten…"), the big
`DAY 3 · DAY` clock, `ACHIEVEMENT`, and `HP 0 · SCORE 20440` — and the topmost line is clipped
above y=0. The achievement rows' column values also bleed through the minimap panel (the strings
`yes 194 1` read *inside* the minimap box). The small 22-chip strip is additionally drawn a second
time behind the big list. During play (the 0 % and 50 % readouts are clean single-line clocks) this
almost certainly does not happen; it is the endcard overlay at episode end. `feed_lines: 0` at load
(tick 0) is consistent with an empty broadcast feed before the first turn, but I have no rendered
evidence that the feed ever fills, and no feed text is legible in the 100 % frame.

Judged as a spectator experience: **legible enough to follow the game during playback and clearly
the right game**, with an endcard that needs a scroll/compaction pass and a top band that needs a
z-order fix. Both, plus the 8 sprite 404s, are phase-30 item-14 legibility findings for the
coordinator — not check-8 failures. Check 8's two hard conditions (`loaded: true`; three differing
clock readouts) are both met.

Status: **TRUE**.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 1 (04:04:27Z) and 2 (04:19:34Z), `error: null`, fillers registered 04:02Z before the first trigger |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey `crafter-techtree:v1` rank 1, daveey-1 `crafter-homesteader:v1` rank 2, both `rounds_played: 2`; fillers absent |
| 3 | Latest round's episode request completed with `replay_url`, correct participants | **TRUE** — both round-2 requests `completed`, non-null `replay_url`, `daveey` and `daveey-1`, `is_filler: false` |
| 4 | Replay bytes valid, protocol matches, `results.reason`, non-fallback champion decisions | **TRUE** — strict-UTF-8 JSON via the design's declared `replay_summary.py` substitute; `crafter/v1`; `complete`; 34/34 turns `source: "llm"`, 0 fallbacks. *Shortfall recorded:* homesteader's episode unlocked 2/22, below the design's own `achievementsUnlocked >= 3` bar (techtree's 4/22 clears it) |
| 5 | Hosted log clean | **TRUE** — CLEAN on both round-2 requests after byte-repr decoding; 34/34 upstream LLM calls `200 OK`; no capacity exception needed |
| 6 | Featured match + static iframe `src` | **PARTIAL** — **6a TRUE**: `/v2/coworlds/replays/static/<cow_id>/<manifest_sha>/index.html?v=2#replay=<s3>`, `ready: true`, no `/client/replay`. **6b FALSE as fetched**: `state.playlist: []`; documented platform-wide cause (single-policy-per-episode coworlds get no playlist entry — reproduced on nethack and procgen; contrasted with minigrid/atari-57/bullwhip) |
| 7 | Certification declared the static bundle | **TRUE** — read from the committed `runs/2026-08-28-crafter/release-result.json`; `Replay liveness: skipped (static replay bundle declared; …)` |
| 8 | Viewer executed and judged | **TRUE** — run `33233844065` (green), `loaded: true` in 3410 ms, `data_replay_loaded: "true"`, `failure: null`, three differing clock readouts; judgment paragraph above. Findings (A) 8 sprite 404s and (B) endcard overflow/overlap logged for phase 30 |

STATE values for the coordinator to write:

```
verify.rounds        = ["round_5c919ee7-5d5d-45a0-aed6-1f3a5ff9e875", "round_48bbe21e-05da-453d-9bfa-ae4ef461f4bc"]
verify.replay        = "https://softmax-public.s3.amazonaws.com/replays/1072532a-9aef-4d0b-91f6-d874077681e4.replay"
verify.iframe_static = true
verify.viewer_check_run = "33233844065"
```
