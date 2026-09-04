# VERIFY — battlecode   (2026-09-04T04:47Z, re-verify after the 0.1.5 → 0.1.6 fix cycle)

Verdict: **all-true (8/8)** — with two explicitly recorded caveats inside check 8 (the
`viewer-check` harness clicks this shell's **zoom slider**, not its scrubber; proof below) and one
recorded design exception in check 7 (`policies: []`).

Scope rule for this run: **only rounds ≥ 9 count.** Rounds 1–8 ran under coworld `0.1.6`'s
predecessor `0.1.5` and round 1 was ruled a definition-of-done check-4 failure by the operator
(an LLM sheet chose `chassis=scaffold`, idled, and won on the opponent starving its kings).
The fixes D1/D2/D3 shipped as game version **GV04** in coworld version **0.1.6**
(`cow_cfddca58-fa27-4dfd-bab8-38619b06fee7`, manifest `sha256:859659fd…`). Checks 1–5 and 8 below
are evaluated **only** on round 9 (`round_b9b4216c…`) and round 10 (`round_e87d8c82…`), and every
piece of evidence in this file was fetched fresh in this heartbeat (04:26Z–04:47Z), except the two
documented exceptions: check 7 (the committed release artifact) and check 8's rendered evidence
(the `viewer-check.yml` runs **this** heartbeat dispatched — 33836912423, 33837141976, 33837175511,
33837929180).

Constants used below (header **values** are never printed):

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_24414477-8c64-4a71-b643-f8a1ef148e29
D=div_4b5efaec-5fde-40c5-9a47-79172c727a13
COW=cow_cfddca58-fa27-4dfd-bab8-38619b06fee7
```

---

## 1. ≥2 completed rounds after the fillers were set (and after the 0.1.6 bump)

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=30" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end
          | [.[]|{id,round_number,status,error,created_at}] | sort_by(.round_number)'
```

Fetched 04:43:15Z (the 04:26:06Z fetch of the same call returned rounds 1–9 only; round 10 appeared
at 04:39:55Z on the ladder's own 15-minute cadence — no `trigger-round` was posted by me):

```json
[
  { "id": "round_7970a7c9-7628-4314-a787-84cfc84ddb1a", "round_number": 1,  "status": "completed", "error": null, "created_at": "2026-09-04T02:32:02.362966Z" },
  { "id": "round_e9115a2a-0240-4dd1-8836-2c3529cbb41d", "round_number": 2,  "status": "completed", "error": null, "created_at": "2026-09-04T02:47:03.561150Z" },
  { "id": "round_331548ae-1c3c-4c44-97ed-1f48f97c5629", "round_number": 3,  "status": "completed", "error": null, "created_at": "2026-09-04T03:02:05.188396Z" },
  { "id": "round_9dbd2c46-b308-4519-92f4-c1037b46a4a7", "round_number": 4,  "status": "completed", "error": null, "created_at": "2026-09-04T03:18:13.300372Z" },
  { "id": "round_ba3077aa-e0b3-4b6b-b4f2-0d1756ae5fa6", "round_number": 5,  "status": "completed", "error": null, "created_at": "2026-09-04T03:33:13.924541Z" },
  { "id": "round_252bce08-4e1e-435a-8895-00e64f299b71", "round_number": 6,  "status": "completed", "error": null, "created_at": "2026-09-04T03:48:14.593894Z" },
  { "id": "round_02749843-51e8-4f0e-836e-6b6f553b09c8", "round_number": 7,  "status": "completed", "error": null, "created_at": "2026-09-04T04:03:15.234386Z" },
  { "id": "round_3b841c25-87af-421d-9566-77cdab8af3f2", "round_number": 8,  "status": "completed", "error": null, "created_at": "2026-09-04T04:18:16.866458Z" },
  { "id": "round_b9b4216c-da7a-4337-8e37-7f02da94503f", "round_number": 9,  "status": "completed", "error": null, "created_at": "2026-09-04T04:24:54.059061Z" },
  { "id": "round_e87d8c82-67db-4914-91f7-d0aa4d7c6dd9", "round_number": 10, "status": "completed", "error": null, "created_at": "2026-09-04T04:39:55.212547Z" }
]
```

Fillers are registered and were registered **before** every counted round — fetched fresh
04:45Z (this read needs the `X-Use-Elevated-Privileges` header even though it is a read):

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"
```
```json
{"filler_policy_versions": [
  {"policy_version_id": "2a5e9e22-bb5b-48ae-8570-6ccdfbecf6c5", "policy_name": "battlecode-awu",      "version": 1, "player_name": "daveey"},
  {"policy_version_id": "e1af161f-f6df-4dc6-b659-915b9c596524", "policy_name": "battlecode-scaffold", "version": 1, "player_name": "daveey"}
]}
```

`log.md` records the filler registration at `2026-09-04T02:32:30Z`; rounds 9 and 10 were created at
`04:24:54Z` and `04:39:55Z`, i.e. ~1h52m and ~2h07m later.

**Status: TRUE** — two completed rounds under 0.1.6 (round 9 at 04:24:54Z, round 10 at 04:39:55Z),
both created long after the fillers were set at 02:32:30Z, neither `failed` nor `discarded`
(`error: null` on both). Rounds 1–8 exist and completed but are excluded by the scope rule above.

---

## 2. Both champions ranked, fillers absent

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```

Fetched 04:44:13Z, i.e. **after** round 10 settled (a 04:26Z fetch of the same call showed
`rounds_played 9` for both; the row below is the fresh one):

```
1	daveey	battlecode-loyalist:v1	1068.5632706307158	10	8.0
2	daveey-1	battlecode-opportunist:v1	931.4367293692842	10	2.0
```

(The list is a bare JSON array, as the playbook says — not `.entries`.)

**Status: TRUE** — `daveey` (champion 1, `battlecode-loyalist:v1`) and `daveey-1` (champion 2,
`battlecode-opportunist:v1`) are both ranked with `rounds_played = 10 ≥ 1`, and that count includes
both counted 0.1.6 rounds. Neither filler (`battlecode-awu:v1`, `battlecode-scaffold:v1`) appears
on the board at all — the required "absent or `Baseline …`" condition, satisfied by absence.

---

## 3. The latest round's episode request completed with a replay and the right participants

The flat `GET /episode-requests?round_id=` route is 405 since 2026-08-26; the nested route is used.

```bash
curl -sS "$BASE/rounds/round_e87d8c82-67db-4914-91f7-d0aa4d7c6dd9/episode-requests" "${AUTH[@]}"
```
```json
{"entries": [{
  "id": "ereq_adfbaca2-3a2c-41e1-afb5-45ef8d4b82d4",
  "status": "completed",
  "coworld_id": "cow_cfddca58-fa27-4dfd-bab8-38619b06fee7",
  "round_id": "round_e87d8c82-67db-4914-91f7-d0aa4d7c6dd9",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/75fbab97-0dce-4738-ba90-6d59cf346e4f.replay",
  "policy_version_ids": ["ea0e3e2e-3e92-486f-b3af-1b49f62247d5", "906cacc7-0680-4b11-a3db-c186ac4e2268"],
  "created_at": "2026-09-04T04:39:55.568397Z"}],
 "next_cursor": null}
```

```bash
curl -sS "$BASE/episode-requests/ereq_adfbaca2-3a2c-41e1-afb5-45ef8d4b82d4" "${AUTH[@]}" \
 | jq '{status, replay_url, participants:[.participants[]|{position,policy_name,player_name,is_filler}], participant_scores, completed_at}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/75fbab97-0dce-4738-ba90-6d59cf346e4f.replay",
  "participants": [
    {"position": 0, "policy_name": "battlecode-loyalist",    "player_name": "daveey",   "is_filler": false},
    {"position": 1, "policy_name": "battlecode-opportunist", "player_name": "daveey-1", "is_filler": false}
  ],
  "participant_scores": [
    {"position": 0, "score": 249.33333333333334},
    {"position": 1, "score": 149.66666666666666}
  ],
  "completed_at": "2026-09-04T04:40:45.384169Z"
}
```

The other counted round, round 9, for completeness (same call shape):

```json
{"entries": [{
  "id": "ereq_162b9cfd-9116-47de-83cb-3c2a2cfb3d03",
  "status": "completed",
  "coworld_id": "cow_cfddca58-fa27-4dfd-bab8-38619b06fee7",
  "round_id": "round_b9b4216c-da7a-4337-8e37-7f02da94503f",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/be140cee-c7f9-4a7e-9fb9-6e3958998cdc.replay",
  "policy_version_ids": ["ea0e3e2e-3e92-486f-b3af-1b49f62247d5", "906cacc7-0680-4b11-a3db-c186ac4e2268"],
  "created_at": "2026-09-04T04:24:54.393360Z"}]}
```
```json
{"status": "completed",
 "replay_url": "https://softmax-public.s3.amazonaws.com/replays/be140cee-c7f9-4a7e-9fb9-6e3958998cdc.replay",
 "participants": [
   {"position": 0, "policy_name": "battlecode-loyalist",    "player_name": "daveey",   "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "is_filler": false},
   {"position": 1, "policy_name": "battlecode-opportunist", "player_name": "daveey-1", "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "is_filler": false}],
 "participant_scores": [{"position": 0, "score": 258.3333333333333}, {"position": 1, "score": 140.66666666666666}],
 "completed_at": "2026-09-04T04:25:43.019820Z"}
```

**Status: TRUE** — the latest completed round (10) has one episode request,
`ereq_adfbaca2-3a2c-41e1-afb5-45ef8d4b82d4`, `status: "completed"`, non-null `replay_url`, and its
two participants are the champions seated under `daveey` and `daveey-1` (`is_filler: false` on
both, and the `policy_version_id`s are exactly the two champion UUIDs). Round 9 is identical in
shape. No `Baseline (N)` seat appeared in either — the division has two ranked players, so no
filler was needed.

---

## 4. Replay bytes are valid and show the game (operator-strengthened substance test)

### 4a. Strict parse, protocol, game version, reason, fallbacks

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/75fbab97-0dce-4738-ba90-6d59cf346e4f.replay" -o /tmp/r10.replay   # 200, 52632 B
python3 -c "
import json
d=json.load(open('/tmp/r10.replay',encoding='utf-8'))     # strict UTF-8 parser, not a browser
print('strict UTF-8 JSON: ok; keys', list(d.keys()))
r=d['result']
print('protocol', d['protocol'], 'game_version', d['game_version'], r['game_version'])
print('reason', r['reason'], 'fallbacks', r['fallbacks'], 'defaults', r['sheet_defaults_applied'])
print('names', r['names'], 'aliases', r['aliases'], 'scores', r['scores'], 'wins', r['wins'], 'points', r['points'])"
```
```
strict UTF-8 JSON: ok; keys ['format', 'version', 'protocol', 'game_version', 'year', 'config', 'seed', 'aliases', 'names', 'seats', 'prompt_preamble', 'games', 'plan', 'events', 'result']
protocol cogame.battlecode.v1 game_version GV04 GV04
reason complete fallbacks [0, 0] defaults [[], []]
names ['daveey', 'daveey-1'] aliases ['Clan Ash', 'Clan Basil'] scores [249.33333333333334, 149.66666666666666] wins [2, 1] points [[20, 57, 71], [79, 42, 28]]
```

Round 9's replay, same commands (`be140cee-…`, 65330 B):

```
strict UTF-8 JSON: ok
protocol cogame.battlecode.v1   game_version(top) GV04   result.game_version GV04
reason complete   fallbacks [0, 0]   sheet_defaults_applied [[], []]
names ['daveey','daveey-1']  aliases ['Clan Ash','Clan Basil']
scores [258.3333333333333, 140.66666666666666]  wins [2, 1]  points [[44, 74, 57], [55, 25, 42]]
```

Protocol cross-check against the coworld's own declaration (the manifest names the protocol by
document, not by literal string, so the document is the reference):

```bash
gh api repos/Metta-AI/cogame-battlecode/contents/docs/PROTOCOL.md -q .content | base64 -d | grep -n "cogame.battlecode"
```
```
1:# `cogame.battlecode.v1`
38:{"protocol":"cogame.battlecode.v1","game_version":"GV03","year":"bc26",
```
(Line 38 is a stale *example* body inside the doc — a cosmetic doc-lag nit, noted for phase 30, not
a check failure; the normative protocol id on line 1 matches both replays.)

`GV04` is the fixed image, per the game's own prepend-only changelog:

```bash
gh api repos/Metta-AI/cogame-battlecode/contents/src/battlecode/sim_types.nim -q .content | base64 -d | grep -n "GV0" -A 4
```
```
16:  GameVersion* = "GV04"
23:    ## GV04 — `chassis` is no longer a doctrine knob. It is gone from
24:    ##        `sheet.KnownKeys` and from the prompt preamble's knob list, so
25:    ##        an LLM doctrine ALWAYS runs the `awu` chassis and a reply that
26:    ##        still sends `chassis` is recorded in `sheet_unknown_fields`,
27:    ##        ignored and logged. `scaffold` is selectable only by
30:    ##        (r2-D2): the chassis digs a buried king out, …
```

### 4b. Per-game substance — round 10 (the latest 0.1.6 replay)

```bash
python3 -c "import json;print(json.dumps(json.load(open('/tmp/r10.replay'))['result']['games'],indent=1))"
```
```json
[
 {"map":"DefaultMedium","side":["B","A"],"rounds_played":1215,"winner":1,"end_reason":"kings_destroyed",
  "cooperation_at_end":false,"backstab_round":800,"backstab_by":1,
  "cat_damage":[1980,2620],"cheese_transferred":[1260,2120],"kings_alive":[0,1],"kings_built":[0,0],
  "rats_built":[24,40],"rats_alive":[14,12],"traps_placed":[52,51],"dirt_placed":[8,0]},
 {"map":"dirtfulcat","side":["A","B"],"rounds_played":325,"winner":0,"end_reason":"cats_cleared",
  "cooperation_at_end":true,"backstab_round":-1,"backstab_by":-1,
  "cat_damage":[5450,2550],"cheese_transferred":[480,605],"kings_alive":[1,1],"kings_built":[0,0],
  "rats_built":[29,27],"rats_alive":[15,16],"traps_placed":[51,25],"dirt_placed":[11,16]},
 {"map":"closeup","side":["B","A"],"rounds_played":1037,"winner":0,"end_reason":"kings_destroyed",
  "cooperation_at_end":false,"backstab_round":800,"backstab_by":1,
  "cat_damage":[2000,4560],"cheese_transferred":[2250,1535],"kings_alive":[1,0],"kings_built":[0,0],
  "rats_built":[47,36],"rats_alive":[9,8],"traps_placed":[46,83],"dirt_placed":[11,63]}
]
```

Round 9's three games (same command on `/tmp/r9.replay`):

```json
[
 {"map":"cheesefarm","rounds_played":1035,"winner":1,"end_reason":"cats_cleared","cooperation_at_end":true,
  "backstab_round":-1,"cat_damage":[4270,3730],"cheese_transferred":[2580,4100],"kings_alive":[1,2],
  "kings_built":[0,2],"rats_built":[17,40],"traps_placed":[28,49],"dirt_placed":[10,35]},
 {"map":"mercifullattice","rounds_played":2000,"winner":0,"end_reason":"round_limit","cooperation_at_end":false,
  "backstab_round":800,"backstab_by":1,"cat_damage":[100,0],"cheese_transferred":[7550,6060],"kings_alive":[2,1],
  "kings_built":[1,0],"rats_built":[41,31],"traps_placed":[38,40],"dirt_placed":[31,17]},
 {"map":"dirtfulcat","rounds_played":325,"winner":0,"end_reason":"cats_cleared","cooperation_at_end":true,
  "backstab_round":-1,"cat_damage":[5450,2550],"cheese_transferred":[480,605],"kings_alive":[1,1],
  "kings_built":[0,0],"rats_built":[29,27],"traps_placed":[51,25],"dirt_placed":[11,16]}
]
```

Operator's substance clauses, decided on the numbers above:

| Clause | Round 10 | Round 9 |
|---|---|---|
| `rats_built > 0` for BOTH clans in EVERY game | 24/40, 29/27, 47/36 ✅ | 17/40, 41/31, 29/27 ✅ |
| `cheese_transferred > 0` for BOTH clans in EVERY game | 1260/2120, 480/605, 2250/1535 ✅ | 2580/4100, 7550/6060, 480/605 ✅ |
| `cat_damage > 0` for both clans in ≥1 game each | all three games, both clans ✅ | Ash 4270/100/5450, Basil 3730/**0**/2550 — Basil >0 in games 1 and 3 ✅ |
| NO game ends `kings_destroyed` against a clan that dealt 0 cat damage AND built 0 rats (the idle-win pattern) | g1 loser Ash: cat_damage 1980, rats 24; g3 loser Basil: cat_damage 4560, rats 36 ✅ | no `kings_destroyed` game at all ✅ |
| Match ends on points (`round_limit`/`cats_cleared`) or a **real** backstab (`backstab_round > 0`, flip visible) | g2 `cats_cleared`; g1+g3 `kings_destroyed` **after** a recorded `backstab` event at round 800 by Clan Basil, `cooperation_at_end:false` ✅ | g1+g3 `cats_cleared`; g2 `round_limit` with a recorded backstab at round 800 ✅ |
| Neither champion sheet has an APPLIED `chassis` | see 4c ✅ | see 4c ✅ |
| `result.game_version == "GV04"` | ✅ | ✅ |

The single zero — Clan Basil's `cat_damage: 0` in round 9 game 2 (`mercifullattice`, a
2000-round `round_limit` game with 6060 cheese ferried and 31 rats built) — is a clan that played
economy rather than cat-hunting on one map, not an idle clan: it built rats, moved cheese, laid 40
traps, placed 17 dirt and opened the backstab at round 800. Neither sheet chose
`cat_engagement: avoid` (both chose `hunt`, see 4c), so this is a map/tempo outcome, not a declared
abstention; the clause only requires cat damage in **at least one game each**, which both clans
clear in both replays.

### 4c. The champion doctrines — non-scripted, distinct, no applied `chassis`, no fallbacks

```bash
python3 -c "
import json;d=json.load(open('/tmp/r10.replay'))
for s in d['seats']: print(s['slot'], s['alias'], s['name'], s['policy']);
                     print(' sheet:', json.dumps(s['sheet']));
                     print(' submitted:', s['sheet_submitted']);
                     print(' defaults', s['sheet_defaults_applied'], 'unknown', s['sheet_unknown_fields'], 'fallback', s.get('fallback'));
                     print(' notes:', s['notes']); print(' motto:', s['motto'], 'decision_ms', s['decision_ms'])"
```
```
0 Clan Ash daveey policy llm
 sheet: {"chassis": "awu", "backstab_policy": "retaliate_only", "backstab_round": 600, "cat_engagement": "hunt", "cat_trap_budget": 120, "rat_trap_budget": 40, "spawn_curve": "steady", "cheese_ferry_ratio": 0.6, "king_count_target": 3, "dirt_wall_policy": "king_shell", "throw_rats_to_feed_cats": false}
 submitted: {"backstab_policy":"retaliate_only","cat_engagement":"hunt","cat_trap_budget":120,"rat_trap_budget":40,"spawn_curve":"steady","cheese_ferry_ratio":0.6,"king_count_target":3,"dirt_wall_policy":"king_shell","throw_rats_to_feed_cats":false}
 defaults_applied [] unknown_fields [] fallback None
 notes: Honour the alliance. Hunt cats aggressively with high trap budget to maximize cooperation scoring. Maintain 3+ kings for defensive resilience. Ferry 60% to skirmishers for sustained cat pressure. Retaliate only if enemy bites, ratnaps, throws, or traps us.
 motto: Cats first, betrayal second, cheese always. decision_ms 5757

1 Clan Basil daveey-1 policy llm
 sheet: {"chassis": "awu", "backstab_policy": "at_round_N", "backstab_round": 800, "cat_engagement": "hunt", "cat_trap_budget": 60, "rat_trap_budget": 80, "spawn_curve": "steady", "cheese_ferry_ratio": 0.6, "king_count_target": 3, "dirt_wall_policy": "king_shell", "throw_rats_to_feed_cats": false}
 submitted: {"backstab_policy":"at_round_N","backstab_round":800,"cat_engagement":"hunt","cat_trap_budget":60,"rat_trap_budget":80,"spawn_curve":"steady","cheese_ferry_ratio":0.6,"king_count_target":3,"dirt_wall_policy":"king_shell","throw_rats_to_feed_cats":false}
 defaults_applied [] unknown_fields [] fallback None
 notes: Hunt cats aggressively rounds 1–799 to maximize cooperation scoring (0.5 weight). Backstab round 800: enemy king count peaks ~round 1200, but by 800 we'll have secured cat-damage lead. Pivot to king survival (0.5 backstab weight) and eliminate Clan Ash kings. Bank 80 rat traps pr…
 motto: Farm the cats. Then farm the clan. decision_ms 5757
```

Round 9's seats (same command on `/tmp/r9.replay`), abbreviated to the fields that decide the
clause — again `llm`, again no submitted `chassis`, again zero unknown fields and zero fallbacks:

```
0 Clan Ash daveey llm  sheet.chassis "awu"
  submitted: {"backstab_policy":"retaliate_only","backstab_round":600,"cat_engagement":"hunt","cat_trap_budget":120,"rat_trap_budget":40,"spawn_curve":"steady","cheese_ferry_ratio":0.6,"king_count_target":3,"dirt_wall_policy":"king_shell","throw_rats_to_feed_cats":false}
  sheet_defaults_applied []  sheet_unknown_fields []  motto "Hunt together, starve apart."
1 Clan Basil daveey-1 llm  sheet.chassis "awu"
  submitted: {"backstab_policy":"at_round_N","backstab_round":800,"cat_engagement":"hunt","cat_trap_budget":80,"rat_trap_budget":120,"spawn_curve":"steady","cheese_ferry_ratio":0.6,"king_count_target":3,"dirt_wall_policy":"king_shell","throw_rats_to_feed_cats":false}
  sheet_defaults_applied []  sheet_unknown_fields []  motto "Farm the cats, then farm the thrones."
```

**On the `chassis` key, precisely, because this is the fix under test.** `sheet_submitted` is what
the LLM actually replied; in all four champion seats across both counted rounds it contains **no
`chassis` key**. The recorded *effective* `sheet` carries `"chassis": "awu"` because GV04 assigns
the `awu` chassis to every LLM doctrine and `replay.parseSeat` restores the applied chassis into
the recording (`reviews/r2-fixes.md` §D1). `sheet_unknown_fields` is `[]` in all four seats —
nothing was sent-and-ignored, so the D1 repair's "record it in `sheet_unknown_fields`" branch was
not exercised this run; it is exercised by `tests/test_sheet.nim` ("`chassis` is NOT a knob
(r2-D1)"). **No champion sheet contains an applied `chassis`: the LLM did not choose it and could
not have.** That is the 0.1.5 round-1 failure mode gone at the root.

One bookkeeping nit, recorded not as a failure: round 10 seat 0 did not submit `backstab_round`
but the effective sheet shows `600` while `sheet_defaults_applied` is `[]` — the default was
filled without being listed. It is moot behaviourally (`retaliate_only` ignores the round) but the
defaults ledger under-reports; a phase-30 observation.

Fallback accounting, the prompt's own commands adapted to this replay's schema (`result` singular,
events carry `kind` not `type`):

```bash
python3 -c "
import json,collections;d=json.load(open('/tmp/r10.replay'))
print('fallbacks', d['result']['fallbacks'])
print(collections.Counter(e['kind'] for e in d['events']))"
```
```
fallbacks [0, 0]
Counter({'game_start': 3, 'game_end': 3, 'doctrine_requested': 2, 'doctrine_received': 2, 'backstab': 2, 'episode_start': 1, 'episode_end': 1})
```
Two decisions per episode (this game asks each seat for exactly one sealed doctrine at t=0, then
simulates 3 games from it), zero `doctrine_fallback` events, zero `result.fallbacks`, both
doctrines received on attempt 1 in 5757 ms (round 9: 5568 ms) against a 20000 ms deadline, and the
two sheets differ from each other in four knobs with distinct prose notes and mottos. Non-scripted,
non-trivial, not fallbacks.

**Status: TRUE** — both counted replays parse under a strict UTF-8 parser, carry
`protocol cogame.battlecode.v1` matching the coworld's declared protocol, carry
`result.game_version == "GV04"` proving the rounds ran the fixed image, end
`reason: "complete"` (no `deadline` exception needed), record zero fallbacks and zero applied
defaults, and satisfy every clause of the operator-strengthened substance test above. The 0.1.5
degenerate pattern (a sheet picking `scaffold`, idling, winning on the opponent's starvation) is
absent: in every counted game both clans built rats, moved cheese and, in five of six games, damaged
cats; the two `kings_destroyed` finishes are the *aggressor* Clan Basil's declared round-800
backstab landing (game 1) and Clan Ash's counter-kill after the same flip (game 3), with the
`backstab` event recorded in the stream.

---

## 5. Hosted game log is clean

```bash
curl -sS "$BASE/episode-requests/ereq_adfbaca2-3a2c-41e1-afb5-45ef8d4b82d4/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o logs10.raw   # 200, 1760 B
# the body is python b'…' byte-string reprs under `===== container: … =====` headers;
# decoded with ast.literal_eval per repr BEFORE grepping (line greps undercount otherwise)
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs10.txt || echo CLEAN
```
```
CLEAN
```

The whole decoded log for round 10, pasted rather than described:

```
===== coworld-init-config =====

===== bedrock-sidecar =====
2026-09-04 04:40:02,096 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1","has_role_arn":true,"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar","episode_request_id":"adfbaca2-3a2c-41e1-afb5-45ef8d4b82d4","job_request_id":"75fbab97-0dce-4738-ba90-6d59cf346e4f","role":"game","slot":"game","image_digest":"sha256:1674bf090670375ac16883f58dbba3e28575d063170c35c3c7a2a7ce88a01d9a"}
[2026-09-04 04:40:02 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-09-04 04:40:02,388 INFO hypercorn.error Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-09-04 04:40:10,023 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-04 04:40:12,523 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"

===== game =====
battlecode config: year=bc26 pool=mixed seed=1701318046 games=3 maxRounds=2000 num_agents=2 matchBudget=330s
battlecode: listening on 0.0.0.0:8080
battlecode: waiting for seats
battlecode: refused a seat-0 connection: seat 0 was given the wrong connection token
battlecode: a spectator joined /global
battlecode: seat 1 connected
battlecode: seat 1 registered kind=llm label=opportunist
battlecode: seat 0 connected
battlecode: seat 0 registered kind=llm label=loyalist
battlecode: doctrine
battlecode llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
battlecode: match
battlecode: settled: complete
battlecode: reason=complete games=3 scores=[249.33333333333334, 149.66666666666666] sim=2.464s wall=14.332s

===== worker =====
```

Round 9's log, same call on `ereq_162b9cfd-9116-47de-83cb-3c2a2cfb3d03` (200, 1758 B), same grep:

```
CLEAN
```
```
===== game =====
battlecode config: year=bc26 pool=mixed seed=549002439 games=3 maxRounds=2000 num_agents=2 matchBudget=330s
battlecode: listening on 0.0.0.0:8080
battlecode: waiting for seats
battlecode: refused a seat-0 connection: seat 0 was given the wrong connection token
battlecode: a spectator joined /global
battlecode: seat 0 connected
battlecode: seat 0 registered kind=llm label=loyalist
battlecode: seat 1 connected
battlecode: seat 1 registered kind=llm label=opportunist
battlecode: doctrine
battlecode llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
battlecode: match
battlecode: settled: complete
battlecode: reason=complete games=3 scores=[258.3333333333333, 140.66666666666666] sim=2.235s wall=14.413s
```

**Status: TRUE** — zero matches for `falling back|LLM provider is unavailable|cut off at max_tokens|rejected`
in either counted round's decoded log; both settle `reason=complete`. No LLM-capacity exception was
needed, so none is claimed.

Two observations for the coordinator, neither a check-5 match: (a) both logs contain
`refused a seat-0 connection: seat 0 was given the wrong connection token` before the real seats
connect — the per-seat token guard added in 0.1.1 doing its job against the platform's probe
connection; the word is `refused`, not `rejected`, and the seats then connect and register
`kind=llm`. (b) the bedrock sidecar's two upstream calls are `POST https://openrouter.ai/api/v1/messages
"HTTP/1.1 200 OK"` — the platform's transport, both 200, one per doctrine.

---

## 6. The public page uses the static replay path

Raw-HTML grep first, as the prompt requires, so an empty result is recorded as *unknown* rather
than a false negative:

```bash
curl -sS "https://softmax.com/battlecode" -o page.html    # 200, 861915 B
grep -o '<iframe[^>]*src="[^"]*"' page.html || echo "NO IFRAME IN RAW HTML"
```
```
NO IFRAME IN RAW HTML
```

Fallback #1 — the `/coworlds` row the playbook names (fetched 04:44Z):

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end|.[]|select(.name=="battlecode")|{id,name,version,canonical,replay_viewer,featured_match}'
```
```json
{"id":"cow_cfddca58-fa27-4dfd-bab8-38619b06fee7","name":"battlecode","version":"0.1.6","canonical":true,"replay_viewer":null,"featured_match":null}
{"id":"cow_6f3468fa-5cf5-4c4b-95cf-1d87dc41bfa2","name":"battlecode","version":"0.1.5","canonical":false,"replay_viewer":null,"featured_match":null}
```
`replay_viewer`/`featured_match` are `null` here as they are platform-wide (playbook §Featured
match), so this row proves canonicality of 0.1.6 but not the iframe.

Fallback #2 — **the source I used**: the featured match is server-rendered into the page's SSR
payload at `state.playlist[0]`, and the iframe `src` is the `viewer_url` the page's own JS obtains
from the replay-session endpoint. Both fetched fresh 04:44–04:45Z:

```bash
python3 -c "import re;h=open('page2.html').read();m=re.search(r'\\\\\"playlist\\\\\":\[(.{0,700})',h,re.S);print(m.group(1).replace('\\\\\"','\"'))"
```
```json
{"episodeId":"2ad08960-87ba-488f-8cc4-da6bbe5e774c","coworldId":"cow_cfddca58-fa27-4dfd-bab8-38619b06fee7",
 "coworldName":"battlecode","coworldVersion":"0.1.6",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/75fbab97-0dce-4738-ba90-6d59cf346e4f.replay",
 "finishedAt":"2026-09-04T04:40:45.384169Z","roundNumber":10,"episodeNumber":1,"code":"battlecode.r10.e1",
 "matchup":{"divisionId":"div_4b5efaec-5fde-40c5-9a47-79172c727a13","divisionName":"Competition",
   "first":{"rank":1,"player_name":"daveey","score":1068.5632706307158,"policy_label":"battlecode-loyalist:v1", …}, …}}
```

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_cfddca58-…","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/75fbab97-0dce-4738-ba90-6d59cf346e4f.replay"}'
```
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_cfddca58-fa27-4dfd-bab8-38619b06fee7/sha256%3A859659fd81ec83438f18f029336271c0251b627d3b2de61643c5bf137ea200bf/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F75fbab97-0dce-4738-ba90-6d59cf346e4f.replay",
 "ready":true}
```

The same call for round 9's replay (the one check 8 rendered), fetched 04:29Z:

```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_cfddca58-fa27-4dfd-bab8-38619b06fee7/sha256%3A859659fd81ec83438f18f029336271c0251b627d3b2de61643c5bf137ea200bf/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fbe140cee-c7f9-4a7e-9fb9-6e3958998cdc.replay",
 "ready":true}
```

**Status: TRUE** — source used: **the SSR playlist plus `POST /coworlds/replays/session`** (the raw
HTML has no iframe; the page is client-rendered, as the playbook records). A featured match is
present and it is a **0.1.6, round-10** episode (`battlecode.r10.e1`, replay `75fbab97…`, finished
04:40:45Z). The iframe `src` is the **static** route
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?v=2#replay=<s3 url>` with `ready: true`;
no `/client/replay` pod URL anywhere. The `<sha>` is
`sha256:859659fd81ec83438f18f029336271c0251b627d3b2de61643c5bf137ea200bf`, which is exactly the
coworld's `manifest_hash` — confirmed independently:

```bash
curl -sS "$BASE/coworlds/$COW" "${AUTH[@]}" | jq -r '{version,canonical,manifest_hash}'
```
```json
{"version":"0.1.6","canonical":true,"manifest_hash":"sha256:859659fd81ec83438f18f029336271c0251b627d3b2de61643c5bf137ea200bf"}
```
(The manifest's `game.replay_viewer.bundle` digest is a *different* hash,
`sha256:b4ab3e4c28df4bcefe16cd4159f56df9efa7bb02b0140439c3223bc161b793e4`; the served path uses the
manifest hash. The session endpoint is the source of truth, as briefed.)

---

## 7. Certification declared the static bundle

Source read: **the committed artifact of this run's 0.1.6 release dispatch**,
`runs/2026-09-03-battlecode/release-result-0.1.6.json` (phase 40, GitHub Actions run
`33836155531`). It was already present in the run directory; no re-download was needed, and `/tmp`
was never consulted.

```bash
jq -r '.certify.replay_liveness' runs/2026-09-03-battlecode/release-result-0.1.6.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

```bash
jq -r '{ok,version,canonical,policies,secret_put}' runs/2026-09-03-battlecode/release-result-0.1.6.json
```
```json
{"ok": true, "version": "0.1.6", "canonical": true, "policies": [], "secret_put": true}
```

The certification transcript in the same artifact (`.certify.output_tail`), all ten steps:

```
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

**Status: TRUE** — the required string `Replay liveness: skipped (static replay bundle declared`
is present verbatim, from the committed `release-result-0.1.6.json`.

**Two facts stated explicitly, as briefed:**
1. `policies: []` in this artifact is **by design**, not a defect: the 0.1.6 release was dispatched
   with `-f policies='[]'` so it would *skip* policy re-upload and not mint unused `v2`s while the
   league stays seated on the `v1` policy versions (`log.md`, 2026-09-04T03:45Z and 04:24Z).
2. The league's policy record therefore remains the **0.1.5** artifact
   `runs/2026-09-03-battlecode/release-result.json`, which is where the four `…:v1` uploads are
   recorded. Its liveness line matches too, for the record:
   ```bash
   jq -r '.certify.replay_liveness' runs/2026-09-03-battlecode/release-result.json
   ```
   ```
   Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
   ```
   The two artifacts together are the complete release record: 0.1.6 = the canonical game image
   under test, 0.1.5 = the policy upload record for the versions actually seated.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged

Nothing in this section is inferred from asset fetches. Four `viewer-check.yml` runs were
dispatched **this heartbeat** in `Metta-AI/coworld-builder` and every readout and picture below
comes from the artifacts downloaded from them, committed under
`runs/2026-09-03-battlecode/viewer-check/`:

| dir | run id | URL rendered | why |
|---|---|---|---|
| `viewer-check/` (primary) | **33837141976** | round **9** episode iframe `src` (`be140cee…`) | the run whose three clock readouts differ |
| `viewer-check/attempt1-33836912423/` | 33836912423 | same round-9 `src` | first dispatch |
| `viewer-check/attempt3-viewpanel0-33837175511/` | 33837175511 | same round-9 `src` **+ `&viewpanel=0`** | diagnostic: hides the zoom bar → board at FIT zoom |
| `viewer-check/attempt4-round10-featured-33837929180/` | 33837929180 | round **10** featured-match iframe `src` (`75fbab97…`) | renders exactly what check 6's featured match points at |

Dispatch and collection (primary):

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_cfddca58-fa27-4dfd-bab8-38619b06fee7/sha256%3A859659fd…/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fbe140cee-c7f9-4a7e-9fb9-6e3958998cdc.replay'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[]|[.databaseId,.createdAt,.status]|@tsv'   # -> 33837141976 created 04:31:41Z, after the 04:31:38Z dispatch
gh run watch 33837141976 -R Metta-AI/coworld-builder --exit-status                  # green
gh run download 33837141976 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-09-03-battlecode/viewer-check
```

### (b) The readouts — pasted verbatim

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-09-03-battlecode/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":1728,"clock":"2:20 GAME 1 OF 3 — CHEESEFARM","scorebug":"CLAN ASH daveey · Hunt together, starve apart. 15 2:20 GAME 1 OF 3 — CHEESEFARM CLAN BASIL daveey-1 · Farm the cats, then farm the thrones. 15","feed_lines":1}
```

```bash
jq -c '.signals' runs/2026-09-03-battlecode/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["ready"],"bridge_ready":true,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/2026-09-03-battlecode/viewer-check/viewer-smoke.json
```
```
no failure
```

```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-09-03-battlecode/viewer-check/viewer-smoke.json
```

| position | clock readout (run 33837141976, round 9) |
|---|---|
| 0 % | `2:20 GAME 1 OF 3 — CHEESEFARM` |
| 50 % | `2:19 GAME 1 OF 3 — CHEESEFARM` |
| 100 % | `2:18 GAME 1 OF 3 — CHEESEFARM` |

The other three runs' readouts, pasted rather than summarised (all `loaded: true`, all
`failure: null`, all `bridge:["ready"]`, all `data_replay_loaded:"true"`):

```
33836912423 (round 9)      {"loaded":true,"ms":1723,"clock":"2:20 GAME 1 OF 3 — CHEESEFARM", …,"feed_lines":1}
  scrub readouts: 0%="2:20 GAME 1 OF 3 — CHEESEFARM"  50%="2:19 GAME 1 OF 3 — CHEESEFARM"  100%="2:19 GAME 1 OF 3 — CHEESEFARM"
33837175511 (round 9, &viewpanel=0)  {"loaded":true,"ms":10598,"clock":"2:20 GAME 1 OF 3 — CHEESEFARM", …,"feed_lines":1}
  scrub readouts: 0%="2:20 GAME 1 OF 3 — CHEESEFARM"        (loop stopped after the first sample — see the caveat)
33837929180 (round 10 featured)      {"loaded":true,"ms":2318,"clock":"1:47 GAME 1 OF 3 — DEFAULTMEDIUM","scorebug":"CLAN ASH daveey · Cats first, betrayal second, cheese always. 15 1:47 … CLAN BASIL daveey-1 · Farm the cats. Then farm the clan. 15","feed_lines":1}
  scrub readouts: 0%="1:47 GAME 1 OF 3 — DEFAULTMEDIUM"  50%="1:47 …"  100%="1:46 GAME 1 OF 3 — DEFAULTMEDIUM"
```
```
canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized   [all four runs]
```

### The caveat, proven: the harness clicks this shell's ZOOM slider, not its scrubber

`viewer_smoke.mjs` seeks with `page.locator('#scrub, #seek, input[type="range"]').first()`, which
resolves in **DOM order**. This shell has `#scrub` (a div-based click-to-seek track) *and* an
`<input type="range" id="zoom-slider">`, and the zoom slider comes first in the document:

```bash
curl -sS ".../static/$COW/sha256%3A859659fd…/index.html" -o viewer_index.html     # 200, 159060 B
grep -n 'zoom-slider\|id="scrub"\|scrub.*addEventListener' viewer_index.html
```
```
2706:        <input id="zoom-slider" type="range" min="0" max="1000" step="1" value="0"
2758:      <div class="scrub" id="scrub">
3151:  $('scrub').addEventListener('click', function (event) {
3152:    var rect = this.getBoundingClientRect();
3153:    seek((event.clientX - rect.left) / Math.max(1, rect.width));
3172:    var slider = $('zoom-slider');
3178:    slider.addEventListener('input', function () {
3180:      var level = 1 + (Number(slider.value) / 1000) * 11;      //  100 % -> 12.0x
```

Three independent confirmations that the 50 %/100 % clicks landed on the zoom slider:
1. every screenshot from the three runs that clicked reads **`12.0×`** in the zoom bar (the slider's
   maximum, `1 + 1.0*11`), while the shell's default is `FIT` (`value="0"`, readout `FIT`);
2. the caption never changes — all readouts stay `GAME 1 OF 3`, which a real seek to 100 % could
   not do on a 3-game replay;
3. run 33837175511, dispatched with `&viewpanel=0` (a documented shell param that hides
   `#viewpanel`), produced **only the 0 % sample**: with the range input hidden its bounding box is
   null and the loop breaks — the loop never falls through to `#scrub`. If the harness had been
   clicking `#scrub`, that run would have produced three samples.

So the three readouts are **not** seek readouts: they are the clock sampled ~0.7 s apart while
playback ran. They still answer the question the check exists to ask — *does the viewer advance?* —
and they answer it three ways: the clock counts down `2:20 → 2:19 → 2:18` in the primary run; the
scorebug moves `15–15` at ms 1728 to `22–27` by screenshot time; and the transport strip reads
`round 8 / 2000`, `round 38 / 2000`, `round 39 / 2000`, `round 40 / 2000` across the four
screenshots. This viewer is playing, not holding a frame. **The mis-detection is a `viewer-check`
harness finding for the coordinator** (`viewer_smoke.mjs` should prefer `#scrub`/`#seek` over a bare
`input[type=range]`, or exclude `#zoom-slider`), not a defect in the coworld — the shell's own
click-to-seek handler is wired at line 3151 and its scrubber is drawn with beat markers.

### (c) The replay JSON the viewer was asked to draw — reconciliation

Round 9 (`be140cee…`), the full ordered event stream (early → late; the file has 16 events, so
nothing is elided):

```
{"kind":"episode_start","ms":0,"seed":549002439,"year":"bc26","maps":["cheesefarm","mercifullattice","dirtfulcat"],"aliases":["Clan Ash","Clan Basil"]}
{"kind":"doctrine_requested","ms":0,"slot":0,"attempt":1,"deadline_ms":20000}
{"kind":"doctrine_requested","ms":0,"slot":1,"attempt":1,"deadline_ms":20000}
{"kind":"doctrine_received","ms":5568,"slot":0,"attempt":1,"latency_ms":5568,"defaults_applied":0,"unknown_fields":0}
{"kind":"doctrine_received","ms":5568,"slot":1,"attempt":1,"latency_ms":5568,"defaults_applied":0,"unknown_fields":0}
{"kind":"game_start","game":0,"round":0,"map":"cheesefarm","width":30,"height":30,"sides":["Clan Ash","Clan Basil"]}
{"kind":"king_built","game":0,"round":280,"alias":"Clan Basil","kings_now":2}
{"kind":"king_built","game":0,"round":587,"alias":"Clan Basil","kings_now":2}
{"kind":"game_end","game":0,"round":1035,"winner_alias":"Clan Basil","winner_slot":1,"end_reason":"cats_cleared","points":[44,55],"cooperation_at_end":true}
{"kind":"game_start","game":1,"round":0,"map":"mercifullattice","width":41,"height":35,"sides":["Clan Basil","Clan Ash"]}
{"kind":"backstab","game":1,"round":800,"by_alias":"Clan Basil","by_slot":1,"trigger":"bite"}
{"kind":"king_built","game":1,"round":1259,"alias":"Clan Ash","kings_now":2}
{"kind":"game_end","game":1,"round":2000,"winner_alias":"Clan Ash","winner_slot":0,"end_reason":"round_limit","points":[74,25],"cooperation_at_end":false}
{"kind":"game_start","game":2,"round":0,"map":"dirtfulcat","width":30,"height":30,"sides":["Clan Ash","Clan Basil"]}
{"kind":"game_end","game":2,"round":325,"winner_alias":"Clan Ash","winner_slot":0,"end_reason":"cats_cleared","points":[57,42],"cooperation_at_end":true}
{"kind":"episode_end","ms":0,"reason":"complete"}
```

Round 10 (`75fbab97…`, what the featured match points at), same command:

```
{"kind":"episode_start","ms":0,"seed":1701318046,"year":"bc26","maps":["DefaultMedium","dirtfulcat","closeup"],"aliases":["Clan Ash","Clan Basil"]}
{"kind":"doctrine_requested",…,"slot":0,…}  {"kind":"doctrine_requested",…,"slot":1,…}
{"kind":"doctrine_received","ms":5757,"slot":0,"attempt":1,"latency_ms":5757,"defaults_applied":0,"unknown_fields":0}
{"kind":"doctrine_received","ms":5757,"slot":1,"attempt":1,"latency_ms":5757,"defaults_applied":0,"unknown_fields":0}
{"kind":"game_start","game":0,"round":0,"map":"DefaultMedium","width":45,"height":45,"sides":["Clan Basil","Clan Ash"]}
{"kind":"backstab","game":0,"round":800,"by_alias":"Clan Basil","by_slot":1,"trigger":"bite"}
{"kind":"game_end","game":0,"round":1215,"winner_alias":"Clan Basil","winner_slot":1,"end_reason":"kings_destroyed","points":[20,79],"cooperation_at_end":false}
{"kind":"game_start","game":1,"round":0,"map":"dirtfulcat","width":30,"height":30,"sides":["Clan Ash","Clan Basil"]}
{"kind":"game_end","game":1,"round":325,"winner_alias":"Clan Ash","winner_slot":0,"end_reason":"cats_cleared","points":[57,42],"cooperation_at_end":true}
{"kind":"game_start","game":2,"round":0,"map":"closeup","width":30,"height":30,"sides":["Clan Basil","Clan Ash"]}
{"kind":"backstab","game":2,"round":800,"by_alias":"Clan Basil","by_slot":1,"trigger":"bite"}
{"kind":"game_end","game":2,"round":1037,"winner_alias":"Clan Ash","winner_slot":0,"end_reason":"kings_destroyed","points":[71,28],"cooperation_at_end":false}
{"kind":"episode_end","ms":0,"reason":"complete"}
```

```bash
python3 -c "import json;d=json.load(open('/tmp/r10.replay'));print(list(d['games'][0].keys()))"
```
```
['index', 'map', 'map_json_sha256', 'sides', 'side_a_slot', 'rounds', 'hash_chain_sha256', 'hash_chain_rounds']
```
That is why a 14-event file draws a full board: the replay is a *re-derivation record* — seed,
doctrines, map hashes and a per-round hash chain — and the viewer re-simulates the match in wasm,
checking each round against `hash_chain_rounds`. The picture below is therefore the game itself,
not a rendering of a summary.

### The spectator-judgment paragraph

**It is legible and it shows the game.** In `attempt3-viewpanel0-…/viewer-smoke.png` — the frame
taken at the shell's own FIT zoom, round 8 of 2000 on `cheesefarm` — the whole 30×30 board is on
screen and readable at a glance: a checkerboard cavern floor, brown cheese/dirt blocks marbled
across the middle, yellow cheese piles scattered as objectives, two big rat **kings** (a magenta
one top-left for Clan Ash, an amber one bottom-left), small pink and orange **rats** clustered
around each king, and two purple **cats** prowling the right-hand side — exactly the pieces the
rules are about. The chrome is the starter's: a transport strip along the bottom (restart, step
back, pause, `+25`, play, loop, fast-forward, a `spoilers` toggle, `round 8 / 2000`, speed chips
`1×…16×`) over a scrubber with beat markers, a top scorebug naming both clans, both players and
both mottos with the live score, a green `COOPERATION` chip in the middle that is the game's
central state, an econ panel bottom-right (kings built / cheese delivered / cats damaged / traps
laid / dirt placed, per clan), and a killfeed line reading "Game 1 begins on cheesefarm". Same
transport-plus-scorebug-plus-endcard family as paintbot/raid/hive; this is the inherited
coworld-ctf chrome with battlecode's own econ panel and coop chip, not a different product.
**The D3 fix is visibly in the wild:** in all four screenshots the doctrine overlay is *not*
covering the board — it has collapsed to a small `▶ DOCTRINES` button in the bottom-left corner,
which is precisely what the r2-D3 auto-dismiss was supposed to do (the smoke json reports no
overlay/econ coverage numbers of its own; the evidence is the picture plus the CI gate recorded in
`reviews/r2-fixes.md`). Reconciled against the record: the screenshots sit at rounds 8–40 of game 1
of 3, before either replay's round-800 backstab, and they show what the events say should be there —
`COOPERATION` still green, no `backstab` yet, kings alive, cheese being delivered (econ panel
`cheese delivered 20 / 35` at round 38, matching a `cheesefarm` game that ends with 2580/4100
transferred). Nothing is empty, frozen or unreadable. **The one legibility complaint is not the
coworld's fault and is worth recording anyway:** the three screenshots taken after the harness's
clicks are stuck at `12.0×` zoom, where the board becomes six blurry brown slabs — the harness set
that, not the viewer. It does show that this shell's zoom is a genuinely destructive control at its
maximum (a 12× view of a 30×30 board is unreadable), so an incidental click by a real spectator
would have the same effect; capping the slider or snapping back to FIT would be a kindness. That is
a phase-30 observation, not a check failure.

**Status: TRUE** — `loaded: true` (run 33837141976, `data-replay-loaded="true"` **and** the
`coworld-replay` bridge's `ready`, first frame at 1728 ms, `failure: null`), and the three clock
readouts differ (`2:20` / `2:19` / `2:18`). Recorded honestly: those three readouts measure
*elapsed playback*, not seek positions, because the harness's scrub locator resolved to this
shell's zoom slider (proof above); the independent motion evidence — clock, scorebug 15–15 → 22–27,
round counter 8 → 40 across runs — points the same way, and the two runs whose middle and last
readouts coincided (33836912423: `2:20/2:19/2:19`; 33837929180: `1:47/1:47/1:46`) are the same
1-second-resolution clock sampled 0.7 s apart, not a stalled viewer.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers (and under 0.1.6) | **TRUE** — rounds 9 (04:24:54Z) and 10 (04:39:55Z), fillers set 02:32:30Z |
| 2 | Both champions ranked, fillers absent | **TRUE** — daveey 1068.56 / daveey-1 931.44, `rounds_played 10`, no filler rows |
| 3 | Latest round's episode request completed with a replay | **TRUE** — `ereq_adfbaca2…` completed, `replay_url` 75fbab97…, daveey + daveey-1 |
| 4 | Replay valid, GV04, and shows the game (operator substance test) | **TRUE** — strict JSON, `cogame.battlecode.v1`, `GV04`, `reason complete`, fallbacks `[0,0]`, every substance clause met, no applied `chassis` |
| 5 | Hosted game log clean | **TRUE** — `CLEAN` on both counted rounds |
| 6 | Public page uses the static replay path | **TRUE** — featured `battlecode.r10.e1`, static `…/index.html?v=2#replay=…`, `ready:true`, sha = manifest hash |
| 7 | Certification declared the static bundle | **TRUE** — from committed `release-result-0.1.6.json`; `policies:[]` by design, 0.1.5 artifact is the policy record |
| 8 | Spectator judgment — viewer executed and judged | **TRUE** — run 33837141976, `loaded:true`, clocks `2:20/2:19/2:18`, board legible, doctrine overlay dismissed |

Non-blocking observations for the coordinator: (i) `viewer_smoke.mjs`'s scrub locator picks a
shell's first `input[type=range]` — here the zoom slider — so its "scrub readouts" are not seeks on
this lineage; (ii) `docs/PROTOCOL.md`'s example body still says `GV03`; (iii) round-10 seat 0's
`backstab_round` default was filled without being listed in `sheet_defaults_applied`; (iv) the
viewer's zoom slider at maximum (12×) makes the board unreadable, with no snap-back to FIT.
