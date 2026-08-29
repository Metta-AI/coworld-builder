# VERIFY — nethack   (2026-08-29T04:26Z)

Run: `2026-08-28-nethack` · slug `nethack` · repo `Metta-AI/cogame-nethack` · version `0.1.1`
`$COW = cow_1346325e-7184-4c94-9fbc-d3aeb750889c`
`$L   = league_462e0339-0d14-4f35-8bb2-ad882f4b0224`
`$D   = div_03513e99-65b4-4fe1-8ce0-ae8adb8728bb`
`manifest_hash = sha256:3452373ed1c8a7d58191fb3caca4321a7894d405b56639e5fe7dfa8449d7b49e`

All calls below were made fresh in this phase-60 session (03:49Z – 04:26Z). Headers sent are named,
never their values:
```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
```

**Verdict: 6 items unambiguously TRUE, 1 item TRUE-with-a-recorded-sub-finding (item 4),
1 item HALF-FALSE (item 6: the static iframe path is TRUE, the *featured match* is ABSENT).**

| # | Item | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | **TRUE** (3 completed, 0 failed/discarded) |
| 2 | Both champions ranked; fillers absent/Baseline | **TRUE** |
| 3 | Latest round's episode requests completed w/ replay_url + correct participants | **TRUE** |
| 4 | Replay bytes valid, protocol matches, `reason` ok, non-scripted decisions | **TRUE on SPEC** — sub-finding: design.md's own stricter substitute (`depthReached ≥ 2`, ≥1 `down`) **not met** in 6/6 episodes |
| 5 | Hosted game log clean | **TRUE** (CLEAN, both episode requests of the latest round) |
| 6 | Public page: featured match + static iframe `src` | **static path TRUE / featured match FALSE** (absent; platform behaviour for `num_agents=1` coworlds — cross-checked against `crafter` and `procgen`) |
| 7 | Certification declared the static bundle | **TRUE** |
| 8 | Viewer EXECUTED: `loaded:true` + three differing clocks | **TRUE** (run `33233650158`) |

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

**Fillers were set before round 1 was ever triggered.** `log.md` records it at `2026-08-29T03:47:48Z`
("50 fillers 200: delver+bumbler registered, neither champion") and "50 unpause 200 … trigger-round
200" on the same line-block, i.e. filler registration precedes every round in this league. Fetched
fresh confirmation of the current filler set (this read needs `ELEV` even though it is a read):

```
$ curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"      # 2026-08-29T04:10:47Z
HTTP 200
{"filler_policy_versions":[
 {"policy_version_id":"86835dea-5b4b-491a-a693-879fd40c10be","policy_id":"6e765461-0750-46bd-b5b7-dec17ec273a3","policy_name":"nethack-delver","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},
 {"policy_version_id":"5c2bc078-fc49-499f-8e89-4c4f89f2bc1c","policy_id":"6415dfca-41e4-448a-abb2-6ffab5756209","policy_name":"nethack-bumbler","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```

and on the league object itself, together with the league's creation time (03:44:39Z — *before* the
first round was created at 03:46:55Z):

```
$ curl -sS "$BASE/leagues?limit=200" "${AUTH[@]}" \
  | jq -c 'if type=="array" then . else .entries end|.[]|select(.game.coworld_name=="nethack")
           |{id,name,created_at,rounds_paused_at,filler_policy_version_ids,round_interval:.settings.round_interval_minutes}'
{"id":"league_462e0339-0d14-4f35-8bb2-ad882f4b0224","name":"Nethack","created_at":"2026-08-29T03:44:39.530726Z","rounds_paused_at":null,"filler_policy_version_ids":["86835dea-5b4b-491a-a693-879fd40c10be","5c2bc078-fc49-499f-8e89-4c4f89f2bc1c"],"round_interval":15}
```

Rounds, fetched at `2026-08-29T04:21:24Z`:

```
$ curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
  | jq 'if type=="array" then . else .entries end|[.[]|{id,round_number,status,error,completed_at}]'
HTTP 200
[
  {
    "id": "round_b7f16922-e6ee-45d0-9c69-d6caee76f46c",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "completed_at": "2026-08-29T04:20:42.482807Z"
  },
  {
    "id": "round_aadd7254-b6a0-4659-82a2-d8b62fdaa7d3",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "completed_at": "2026-08-29T04:05:39.732693Z"
  },
  {
    "id": "round_1abe8f06-a82b-4596-a43d-8515631ee99b",
    "round_number": 1,
    "status": "completed",
    "error": null,
    "completed_at": "2026-08-29T03:50:43.284655Z"
  }
]
```

Completed count and the seated entrants (earlier read of the same endpoint at `04:10:43Z`, which is
where the `entrant_policy_version_ids` were captured):

```
$ … | jq -r 'if type=="array" then . else .entries end|[.[]|select(.status=="completed")]|length'
2                                  # at 04:10:43Z; 3 at 04:21:24Z

$ … | jq '.entries[]|{round_number, entrants:.round_config.entrant_policy_version_ids}'
{"round_number":2,"entrants":["20a7c701-d7fa-468d-a014-b4b3eef47d4c","dea3d12b-0db0-42d8-9315-08f644660498"]}
{"round_number":1,"entrants":["20a7c701-d7fa-468d-a014-b4b3eef47d4c","dea3d12b-0db0-42d8-9315-08f644660498"]}
```
(`20a7c701…` = `nethack-divemaster:v1`/daveey, `dea3d12b…` = `nethack-loremaster:v1`/daveey-1 —
neither is a filler id.)

**Status: TRUE — rounds 1, 2 and 3 are `completed` with `error: null`; zero rounds are
`failed` or `discarded` (so there is no `error` string to record verbatim); all three were created
(03:46:55Z / 04:01:55Z / 04:16:57Z) after the fillers were registered at 03:47:48Z on a league
created 03:44:39Z with both filler version ids already attached.**

---

## 2. Both champions ranked; fillers absent or Baseline — TRUE

```
$ curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq .      # 2026-08-29T04:10:53Z
HTTP 200
[
  {
    "rank": 1,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 1030.5304984710244,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 2.0,
    "episodes_played": null,
    "win_rate": 1.0,
    "policy_label": "nethack-loremaster:v1",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 969.4695015289755,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 0.0,
    "episodes_played": null,
    "win_rate": 0.0,
    "policy_label": "nethack-divemaster:v1",
    "recent_rounds": null
  }
]
```

Re-fetched after round 3, `2026-08-29T04:21:24Z`:

```
$ curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
  | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
1	daveey-1	nethack-loremaster:v1	1027.747133633611	3	2.0
2	daveey	nethack-divemaster:v1	972.2528663663891	3	0.0
```

**Status: TRUE — the endpoint returns a bare list of exactly two rows. `daveey` (`nethack-divemaster:v1`)
and `daveey-1` (`nethack-loremaster:v1`) are both present with `rounds_played = 3 ≥ 1`. Neither filler
(`nethack-delver:v1` / `nethack-bumbler:v1`) appears in any row, so the "absent or Baseline"
requirement is satisfied by absence — consistent with `entrant_policy_version_ids` containing only
the two champion versions in every round.**

---

## 3. Latest completed round's episode requests completed with a replay — TRUE

The flat route is dead, exactly as `playbooks/observatory-api.md` §9 records — pasted so the
fallback is on the record:

```
$ curl -sS -w '\nHTTP %{http_code}\n' "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}"
{"detail":"Method Not Allowed"}
HTTP 405
```

Nested route (`$R = round_b7f16922-e6ee-45d0-9c69-d6caee76f46c`, round 3, the max `round_number`
among `completed`), fetched `2026-08-29T04:21:24Z`:

```
$ R=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
      | jq -r 'if type=="array" then . else .entries end|[.[]|select(.status=="completed")]|max_by(.round_number).id')
$ echo $R
round_b7f16922-e6ee-45d0-9c69-d6caee76f46c
$ curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" | jq .
HTTP 200
{
  "entries": [
    {
      "id": "ereq_ad3b82c9-8ed1-466d-b3b3-fc95471d625c",
      "status": "completed",
      "coworld_id": "cow_1346325e-7184-4c94-9fbc-d3aeb750889c",
      "round_id": "round_b7f16922-e6ee-45d0-9c69-d6caee76f46c",
      "replay_url": "https://softmax-public.s3.amazonaws.com/replays/3466ad2b-2101-4897-ac3f-72e09c1bea9b.replay",
      "policy_version_ids": ["dea3d12b-0db0-42d8-9315-08f644660498"],
      "created_at": "2026-08-29T04:16:57.213569Z"
    },
    {
      "id": "ereq_ccd49ce2-f9a9-4735-80e2-6f110ae021d1",
      "status": "completed",
      "coworld_id": "cow_1346325e-7184-4c94-9fbc-d3aeb750889c",
      "round_id": "round_b7f16922-e6ee-45d0-9c69-d6caee76f46c",
      "replay_url": "https://softmax-public.s3.amazonaws.com/replays/622fba58-2850-459a-8406-262a1866e16e.replay",
      "policy_version_ids": ["20a7c701-d7fa-468d-a014-b4b3eef47d4c"],
      "created_at": "2026-08-29T04:16:57.206529Z"
    }
  ],
  "next_cursor": null
}
```

Details of both (`2026-08-29T04:21:40Z`):

```
$ curl -sS "$BASE/episode-requests/ereq_ad3b82c9-8ed1-466d-b3b3-fc95471d625c" "${AUTH[@]}" \
  | jq '{status, replay_url, participants, participant_scores}'
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/3466ad2b-2101-4897-ac3f-72e09c1bea9b.replay",
  "participants": [
    {
      "position": 0, "kind": "policy",
      "policy_version_id": "dea3d12b-0db0-42d8-9315-08f644660498",
      "policy_id": "a3d8bc1b-7a93-4b81-aaca-369acd7cc0f0",
      "policy_name": "nethack-loremaster", "version": 1,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
      "player_name": "daveey-1", "is_filler": false, "is_seed": false
    }
  ],
  "participant_scores": [{"position": 0, "score": 0.0}]
}

$ curl -sS "$BASE/episode-requests/ereq_ccd49ce2-f9a9-4735-80e2-6f110ae021d1" "${AUTH[@]}" \
  | jq '{status, replay_url, participants, participant_scores}'
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/622fba58-2850-459a-8406-262a1866e16e.replay",
  "participants": [
    {
      "position": 0, "kind": "policy",
      "policy_version_id": "20a7c701-d7fa-468d-a014-b4b3eef47d4c",
      "policy_id": "1b939d65-95b1-4b57-80dd-e66f87a91425",
      "policy_name": "nethack-divemaster", "version": 1,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey", "is_filler": false, "is_seed": false
    }
  ],
  "participant_scores": [{"position": 0, "score": 0.0}]
}
```
(Both round-3 scores are `0.0`: daveey-1's seat was killed by a jackal on DL1 and daveey's seat hit
the turn cap with no gold and no kills — see item 4.)

Round 2's episode requests, fetched at `2026-08-29T04:11:05Z`, for completeness:

```
ereq_d38c6af7-edf0-4486-ba86-1dec8834b2df  completed  daveey-1  nethack-loremaster:v1  score 160.0
    replay https://softmax-public.s3.amazonaws.com/replays/3db7fc96-2a79-44e3-9127-fd36c3d8f17f.replay
ereq_c39ff0a2-f5db-4029-9d52-e9d6f55e3d79  completed  daveey    nethack-divemaster:v1  score 100.0
    replay https://softmax-public.s3.amazonaws.com/replays/6017a075-88a8-428b-8444-1797462efc9d.replay
```

**Status: TRUE — the latest completed round (3) has two episode requests, both `status: "completed"`,
both with a non-null `replay_url`, and between them the participants name `daveey` and `daveey-1`
with `is_filler: false`. Note on shape: nethack is a **single-seat** coworld (`num_agents` fixed at 1
in both manifest variants and the certification fixture), so no *one* episode can contain both
champions; the ladder seats one champion per episode request and the round's
`round_config.entrant_attributions` carries both (`ply_44ae9048…+20a7c701…`, `ply_bac48eb1…+dea3d12b…`).
That is the game's declared design, not a missing participant.**

---

## 4. Replay bytes are valid and show the game — TRUE on SPEC; design-note sub-finding recorded

Primary replay = the latest completed round's top-ranked champion episode
(`ereq_ad3b82c9…`, daveey-1 / `nethack-loremaster:v1`).

**Shape.** The `replay_url` does **not** serve JSON. It serves the starter's binary `COWLDNET`
container, exactly as `design.md` §"Replay bytes (self-sufficient)" declares (lines 1371-1397: the
format is kept binary because the static wasm viewer parses precisely this, and the shipped
`tools/replay_summary.py` is the declared phase-60 substitute that expands it to one strict-UTF-8
JSON object).

```
$ curl -sSL "https://softmax-public.s3.amazonaws.com/replays/3466ad2b-2101-4897-ac3f-72e09c1bea9b.replay" \
    -o /tmp/ep.replay -w 'HTTP %{http_code} bytes=%{size_download} content-type=%{content_type}\n'
HTTP 200 bytes=40485 content-type=application/octet-stream

$ head -c 40 /tmp/ep.replay | od -c
0000000   C   O   W   L   D   N   E   T 001  \0  \a  \0   n   e   t   h
0000020   a   c   k 001  \0   2   (   e 274   K 240 001  \0  \0   I 002
0000040   {   "   s   e   e   d   "   :
0000050

$ jq -e . /tmp/ep.replay
jq: parse error: Invalid numeric literal at line 1, column 33          # rc=5 — as expected, binary
```

The header bytes themselves carry the game identity: magic `COWLDNET`, then a length-prefixed
`nethack` (`\a\0` = 7 bytes) and game version `2`. Expanded with the repo's own tool
(`Metta-AI/cogame-nethack@3e37c93 tools/replay_summary.py`, Python-3 stdlib only):

```
$ python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
$ jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok
$ python3 -c "d=open('/tmp/ep.json','rb').read(); d.decode('utf-8'); print('strict UTF-8 decode ok; bytes=',len(d))"
strict UTF-8 decode ok; bytes= 6674
```

```
$ jq -r '.protocol, .gameName, .gameVersion, (.names|@json), (.policyKinds|@json), .tickCount, .fallbacks, (.plans|length), (.says|length)' /tmp/ep.json
nethack/v1
nethack
2
["loremaster"]
["llm"]
156
1
25
25

$ jq -c '[.plans[].source]|group_by(.)|map({source:.[0],n:length})' /tmp/ep.json
[{"source":"llm","n":25}]

$ jq -c '.results' /tmp/ep.json
{"names":["loremaster"],"aliases":["Alpha"],"scores":[0],"win":[false],"winner":null,
 "reason":"complete","endRule":"death","variant":"descend","seed":88998717,"dungeonLevels":8,
 "parDepth":4,"depthReached":1,"finalDepth":1,"gold":0,"xpPoints":0,"xlevel":1,"monstersKilled":0,
 "itemsPicked":0,"timesAte":0,"potionsQuaffed":0,"oracleConsults":0,"doorsKicked":2,
 "trapsTriggered":0,"deeds":[],"deedCount":0,"hpFinal":0,"maxHpFinal":16,"causeOfDeath":"killed",
 "killer":"jackal","levelTurns":[25,0,0,0,0,0,0,0],"levelTicks":[156,0,0,0,0,0,0,0],
 "levelKills":[0,0,0,0,0,0,0,0],"levelGold":[0,0,0,0,0,0,0,0],"goldPickedUp":0,"cellsSeen":119,
 "cellsTotal":6912,"primitivesExecuted":156,"actionsDropped":0,"macrosUnreachable":2,
 "repliesRepaired":0,"finalTick":156,"turnsPlayed":25,"policyKinds":["llm"],"llmTurns":25,
 "fallbackTurns":0,"deadSeats":[false],"stopDetail":""}
```

**`protocol` — honest reading.** The string `"nethack/v1"` in the summary is *emitted by the tool*
(`tools/replay_summary.py:142` hard-codes it), so it is not itself byte-evidence. The byte-level
protocol evidence is the header above: magic `COWLDNET`, game name `nethack`, and the manifest that
the same bundle sha is served under declares `game.name == "nethack"` and
`game.protocols.player/.global` pointing at `docs/PROTOCOL.md`. Those agree.

The other champion in the same round (`ereq_ccd49ce2…`, daveey / `nethack-divemaster:v1`):

```
$ python3 tools/replay_summary.py 622fba58-2850-459a-8406-262a1866e16e.replay | jq -r '.protocol,(.names|@json),(.policyKinds|@json),.tickCount,(.plans|length),(.says|length)'
nethack/v1
["divemaster"]
["llm"]
231
55
55
$ … | jq -c '[.plans[].source]|group_by(.)|map({source:.[0],n:length})'
[{"source":"llm","n":55}]
$ … | jq -c '.results|{reason,endRule,scores,depthReached,turnsPlayed,llmTurns,fallbackTurns}'
{"reason":"complete","endRule":"turnCap","scores":[0],"depthReached":1,"turnsPlayed":55,"llmTurns":55,"fallbackTurns":0}
```

**Fallbacks are a small minority and did not replace a decision.** The one `k:"fallback"` chat record
in the primary replay is an *attempt-1 retry*, and turn 14 still produced an `llm`-sourced directive:

```
$ python3 - <<'PY'   # dumps the raw chat records with k=="fallback"
{"k": "fallback", "turn": 14, "attempt": 1, "cause": "timeout",
 "detail": "llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke"}
PY
```
1 retry / 25 turns; `results.fallbackTurns = 0`, `llmTurns = 25 = turnsPlayed`, and every one of the
25 directives has `source == "llm"`. The design's fallback ladder never took a seat.

**Status: TRUE against SPEC §Definition of done check 4 and `prompts/60-verify.md` check 4** — the
bytes fetch, parse under a strict UTF-8 JSON parser after the declared expansion, the protocol
identity matches the manifest, `results.reason == "complete"` (no `deadline` exception needed for any
of the six episodes), and the champion seat's decisions are 100 % non-scripted with non-trivial
content (`"Kicking locked door to explore"`, `"Fleeing jackal to doorway to fight 1v1"`).

**SUB-FINDING (recorded, not waved through).** `design.md` lines 1386-1397 declare a *stricter*
phase-60 substitute for this check than SPEC does — it additionally requires
`results.depthReached >= 2` and "at least one `travel` and at least one `down`" verb. **That
additional criterion is NOT met, in any episode of any round:**

| round | seat | endRule | score | depthReached | `down` verbs |
|---|---|---|---|---|---|
| 1 | loremaster (daveey-1) | turnCap | 1020 | **1** | 0 |
| 1 | divemaster (daveey)   | turnCap | 130  | **1** | 0 |
| 2 | loremaster (daveey-1) | escaped | 160  | **1** | 0 |
| 2 | divemaster (daveey)   | turnCap | 100  | **1** | 0 |
| 3 | loremaster (daveey-1) | death (killer `jackal`) | 0 | **1** | 0 |
| 3 | divemaster (daveey)   | turnCap | 0    | **1** | 0 |

Verb histogram for the two round-2 episodes shows the shape of it — a lot of walking and searching
and no descent:
```
$ jq -c '[.plans[].verbs[]]|group_by(.)|map({v:.[0],n:length})|sort_by(-.n)' 3db7fc96….json
[{"v":"move","n":122},{"v":"search","n":26},{"v":"travel","n":9},{"v":"pickup","n":6},{"v":"up","n":1},{"v":"wait","n":1}]
$ jq -c '[.plans[].verbs[]]|group_by(.)|map({v:.[0],n:length})|sort_by(-.n)' 6017a075….json
[{"v":"move","n":254},{"v":"search","n":9},{"v":"travel","n":3}]
```
Neither LLM policy has yet found a down-staircase in six hosted episodes; one of them (round 2,
loremaster) ended the run at turn 27 by taking the **up** stairs out of DL1 (`endRule: "escaped"`,
score 160) — a legal terminal state that scores better than dying but never descends. This is a
game-balance / level-generation legibility question for the coordinator and the judge, not a replay
defect: the bytes are valid and the decisions are genuine. I am **not** marking item 4 false on it
(SPEC's own wording is met) and I am **not** claiming the design's criterion passed.

---

## 5. Hosted game log is clean — TRUE

Both episode requests of the latest completed round, fetched `2026-08-29T04:22:04Z`. The body is
python `b'…'` byte-string reprs under `===== container: … =====` headers, so it is decoded per-repr
with `ast.literal_eval` **before** grepping (playbook §10):

```
$ curl -sS "$BASE/episode-requests/ereq_ad3b82c9-8ed1-466d-b3b3-fc95471d625c/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o log.raw
HTTP 200 bytes=5254
$ python3 declog.py log.raw | grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' || echo CLEAN
CLEAN

$ curl -sS "$BASE/episode-requests/ereq_ccd49ce2-f9a9-4735-80e2-6f110ae021d1/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o log.raw
HTTP 200 bytes=8582
$ python3 declog.py log.raw | grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' || echo CLEAN
CLEAN
```

Round 2's two logs were greped the same way at `2026-08-29T04:11:40Z`: **CLEAN** and **CLEAN**.

The decoded `game` container of the **primary (round 3, daveey-1) episode**, verbatim, so the absence
is visible and not merely asserted:

```
===== container: game =====
seed not pinned; randomized
nethack config: host=0.0.0.0 port=8080 seed=88998717 variant=descend num_agents=1 dungeonLevels=8 maxTurns=55 maxTicks=2200 wallClockBudgetSeconds=660
nethack listening on 0.0.0.0:8080
nethack llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
player connected: slot 0
nethack: seat registered kind=llm baseline=delver label=loremaster
nethack: the descent begins
Dropped message to disconnected client
nethack llm: attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
nethack results: {"names":["loremaster"],"aliases":["Alpha"],"scores":[0],…,"reason":"complete","endRule":"death",…,"causeOfDeath":"killed","killer":"jackal",…,"turnsPlayed":25,"policyKinds":["llm"],"llmTurns":25,"fallbackTurns":0,"deadSeats":[false],"stopDetail":""}
nethack: episode complete (reason=complete endRule=death depth=1 score=0)

===== container: worker =====
```

And the round-2 loremaster container (also CLEAN), which is where the retry line first appeared:

```
===== container: game =====
seed not pinned; randomized
nethack config: host=0.0.0.0 port=8080 seed=1026888366 variant=descend num_agents=1 dungeonLevels=8 maxTurns=55 maxTicks=2200 wallClockBudgetSeconds=660
nethack listening on 0.0.0.0:8080
nethack llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
player connected: slot 0
nethack: seat registered kind=llm baseline=delver label=loremaster
nethack: the descent begins
Dropped message after WebSocket close
Dropped message after WebSocket close
Dropped message after WebSocket close
Dropped message to disconnected client
nethack llm: attempt 1 failed, will retry: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
nethack results: {"names":["loremaster"], … "reason":"complete","endRule":"escaped", … "llmTurns":27,"fallbackTurns":0,"deadSeats":[false],"stopDetail":""}
nethack: episode complete (reason=complete endRule=escaped depth=1 score=160)

===== container: worker =====
```

**Status: TRUE — zero lines match `falling back|LLM provider is unavailable|cut off at max_tokens|rejected`
in either container set of the latest completed round. No platform-wide-cause exception is being
claimed, because none is needed. The transient `attempt 1 failed, will retry` line is the retry rung
of the ladder, not the fallback rung — it does not contain the phrase `falling back` (the game only
emits that phrase when the seat actually drops to `delver`,
`src/nethack/decide.nim:160,170,253`), and `results.fallbackTurns == 0` in every episode confirms no
seat ever fell back. Bedrock capacity was healthy for this run: 6/6 episodes completed and all 272
turns across all six episodes (55+55, 27+55, 25+55) were `source: "llm"`.**

---

## 6. The public page's replay path — static path TRUE / featured match FALSE

Three differently-approached attempts, all fresh.

**Attempt (a) — raw-HTML iframe grep. Finds nothing (page is client-rendered).**
```
$ curl -sS "https://softmax.com/nethack" | grep -o '<iframe[^>]*src="[^"]*"'
(no output)                                                   # 04:11:48Z, 04:21:05Z — HTTP 200, 760 kB
```
This is the documented lighthouse-run behaviour (`playbooks/observatory-api.md` §Featured match /
replay route): the iframe exists only after JS runs, so an empty grep is *unknown*, not false.

**Attempt (b) — the `/coworlds` detail fallback. The `featured_match` key no longer exists at all.**
```
$ curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
  | jq -r 'if type=="array" then . else .entries end|.[]|select(.name=="nethack")
           |{id,canonical,version,replay_viewer:.manifest.game.replay_viewer,featured_match:(.featured_match // "ABSENT-KEY"),haskeys:keys}'
{
  "id": "cow_1346325e-7184-4c94-9fbc-d3aeb750889c",
  "canonical": true,
  "version": "0.1.1",
  "replay_viewer": {"bundle": "sha256:3af0ec3d9af6350d8581310a33b3b92d512fa48e4f49c8b85dc0f9da4cad3716"},
  "featured_match": "ABSENT-KEY",
  "haskeys": ["api_version","canonical","created_at","id","manifest","manifest_hash","name","schema_hash","size_bytes","version"]
}
```
`featured_match` is not merely `null` — the key is gone from the row shape entirely, for
`minigrid` too. So this endpoint is no longer evidence either way.

**Attempt (c) — the page's SSR payload (`state.playlist` / `state.pool`), which is where the featured
match actually lives, plus the session endpoint the page's own JS calls.**

```
$ curl -sS "https://softmax.com/nethack" -o page.html      # 2026-08-29T04:21:05Z, HTTP 200
$ python3 ssr.py page.html          # unescapes the SSR string and raw-decodes state
playlist len 0 | pool.replays 2 | activeRound False | players 2
$ grep -o 'No featured match yet' page.html
No featured match yet
```
Rendered copy of that region of the HTML, verbatim:
```html
<span class="chip chip-warn">Between rounds</span></div>
<h1 …>No featured match yet</h1>
<div …>The next round is expected in ~9m.</div>
```
`state.pool.replays` is **not** empty — it holds the latest round's episodes, with the right people
in them:
```
$ jq -c '.pool.replays[]|.episode|{ereq:.id,participants:[.participants[]|{position,player_name,is_filler}],status,scores}' ssr_state.json
{"ereq":"ereq_d38c6af7-edf0-4486-ba86-1dec8834b2df","participants":[{"position":0,"player_name":"daveey-1","is_filler":false}],"status":"completed","scores":[{"policy_version_id":"dea3d12b-…","score":160}]}
{"ereq":"ereq_c39ff0a2-f5db-4029-9d52-e9d6f55e3d79","participants":[{"position":0,"player_name":"daveey","is_filler":false}],"status":"completed","scores":[{"policy_version_id":"20a7c701-…","score":100}]}
$ jq -c '{playerCount, divisionCount, newestCompletedAt, firstPlace:.firstPlace.current.player_name}' ssr_state.json
{"playerCount":2,"divisionCount":1,"newestCompletedAt":"2026-08-29T04:05:39.732693Z","firstPlace":"daveey-1"}
```

**Why the featured match is absent, cross-checked rather than guessed.** SPEC says "absence = fewer
than two ranked players" — that is *not* the cause here (two ranked players, both with
`rounds_played = 3`). The actual cause is structural: a playlist entry carries a
`matchup: {divisionId, divisionName, first, second}` — the top two ranked players *inside one
episode*. nethack is a one-seat game, so no episode can ever contain two players. Fetched
comparison, same call, same minute:

```
$ for s in bullwhip parley babel moba minigrid crafter procgen nethack; do curl -sS https://softmax.com/$s -o p.html; python3 ssr.py p.html; done
bullwhip  playlist len 1 | pool.replays 1 | players 4      (multi-seat)
parley    playlist len 1 | pool.replays 1 | players 4      (multi-seat)
babel     playlist len 1 | pool.replays 1 | players 4      (multi-seat)
moba      playlist len 1 | pool.replays 6 | players 4      (multi-seat)
minigrid  playlist len 1 | pool.replays 1 | players 3      (multi-seat: 4 participants/episode)
crafter   playlist len 0 | pool.replays 2 | players 2      ← num_agents=1, "No featured match yet"
procgen   playlist len 0 | pool.replays 3 | players 3      ← num_agents=1, "No featured match yet"
nethack   playlist len 0 | pool.replays 2 | players 2      ← num_agents=1, "No featured match yet"
```
```
$ jq -c '{playlist_len:(.playlist|length), round:(.pool.replays[0].round.round_number), participants:[.pool.replays[0].episode.participants[]|.player_name], leaderboard:[.divisionLeaderboard[]|{rank,player_name,rounds_played}]}' s_procgen.json
{"playlist_len":0,"round":32,"participants":["richard"],"leaderboard":[{"rank":1,"player_name":"richard","rounds_played":23},{"rank":2,"player_name":"daveey","rounds_played":32},{"rank":3,"player_name":"daveey-1","rounds_played":32}]}
$ jq -c '… minigrid …'
{"participants":["daveey","daveey-1","richard","daveey"],"playlist_len":1}
```
`procgen` is at **round 32** with **three** ranked players and still shows
`playlist: []` / "No featured match yet"; `crafter` likewise. Every coworld in the canonical list
whose manifest declares `num_agents == 1` (`crafter`, `procgen`, `nethack` — the only three such rows
among the 77 canonical coworlds, from
`jq '…manifest.variants[0].game_config.num_agents // …config_schema.properties.num_agents.default'`
over `/coworlds?limit=200`; 7 rows declare a seat count nowhere, the remaining 67 declare 2-20) has
an empty playlist; every coworld with a declared seat count > 1 that I checked has exactly one
playlist entry. This is platform behaviour for single-seat coworlds, not a nethack defect — but it is also **not a documented exception**, so I am not marking it true.

**The static replay path, however, is confirmed.** The call the page's JS makes
(`playbooks/observatory-api.md` §Featured match / replay route), fetched `2026-08-29T04:22:05Z`:

```
$ curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
   -d '{"coworld_id":"cow_1346325e-7184-4c94-9fbc-d3aeb750889c",
        "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/3466ad2b-2101-4897-ac3f-72e09c1bea9b.replay"}'
HTTP 200
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_1346325e-7184-4c94-9fbc-d3aeb750889c/sha256%3A3452373ed1c8a7d58191fb3caca4321a7894d405b56639e5fe7dfa8449d7b49e/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F3466ad2b-2101-4897-ac3f-72e09c1bea9b.replay","ready":true}
```
An earlier identical call at `04:14:25Z` against round 2's replay returned the same shape and the
same bundle path.

Checked against the required pattern:
- path is `/v2/coworlds/replays/static/<cow_id>/<sha>/index.html` ✔
- `<cow_id>` = `cow_1346325e-7184-4c94-9fbc-d3aeb750889c` ✔ (matches STATE)
- `<sha>` = `sha256%3A3452373…d7b49e` = the coworld's **manifest_hash**, URL-encoded ✔
  (`manifest_hash` from `/coworlds`: `sha256:3452373ed1c8a7d58191fb3caca4321a7894d405b56639e5fe7dfa8449d7b49e`)
- replay carried as the URL-encoded `#replay=` **fragment** — the documented post-2026-08-28 form of
  the same static route ✔
- `ready: true` ✔
- **no `/client/replay` anywhere** ✔

**Status: SPLIT.**
- *Static iframe `src`* — **TRUE**. Source used: **the `POST /coworlds/replays/session` endpoint**
  (attempt c), because attempt (a) returns a client-rendered shell with no iframe and attempt (b)'s
  `featured_match` key no longer exists in the API response.
- *Featured match present* — **FALSE**. `state.playlist` is `[]` and the page renders
  "No featured match yet" / "Between rounds", at 04:11:48Z and again at 04:21:05Z after a third round
  completed. Cross-checked as platform-wide for `num_agents == 1` coworlds (`crafter` round 1,
  `procgen` round 32, both with ≥2 ranked players, both empty), so it is not caused by this
  coworld's release — but it is undocumented in SPEC, so it is recorded FALSE for the judge.

---

## 7. Certification declared the static bundle — TRUE

Source: **the committed `runs/2026-08-28-nethack/release-result.json`** (phase 40's artifact copy,
committed at 03:44:17Z per `log.md`). No re-download was needed — the file was present.

```
$ jq -r '.certify.replay_liveness' runs/2026-08-28-nethack/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

The same string appears in the certification transcript tail in the same file, after ten passing
transcript steps:
```
$ jq -r '.certify.output_tail' runs/2026-08-28-nethack/release-result.json | tail -8
Certified dist/coworld_manifest.json
Transcript: coworld-executable (10 steps passed)
Transcript report: file:///home/runner/work/cogame-nethack/cogame-nethack/tmp/coworld-cert-r2_hr781/certification_report.html
Artifacts: /home/runner/work/cogame-nethack/cogame-nethack/tmp/coworld-cert-r2_hr781
Results: …/results.json
Replay: …/replay
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
Logs: …/logs
```
```
$ jq -c '{version, ok, cow_id, manifest_sha, canonical, hosted_smoke, hosted_certification, certify_ok:.certify.ok, secret_put, errors, step_failed}' runs/2026-08-28-nethack/release-result.json
{"version":"0.1.1","ok":true,"cow_id":"cow_1346325e-7184-4c94-9fbc-d3aeb750889c","manifest_sha":"sha256:3452373ed1c8a7d58191fb3caca4321a7894d405b56639e5fe7dfa8449d7b49e","canonical":true,"hosted_smoke":"passed","hosted_certification":"certified","certify_ok":true,"secret_put":true,"errors":[],"step_failed":null}
```

**Status: TRUE — the committed copy contains `Replay liveness: skipped (static replay bundle declared`
verbatim.**

---

## 8. The viewer, EXECUTED — TRUE

**(a) Dispatch.** URL used = the item-6 `viewer_url` for the latest completed round's top-ranked
episode (round 3, `ereq_ad3b82c9…`, daveey-1).

```
$ SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_1346325e-7184-4c94-9fbc-d3aeb750889c/sha256%3A3452373ed1c8a7d58191fb3caca4321a7894d405b56639e5fe7dfa8449d7b49e/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F3466ad2b-2101-4897-ac3f-72e09c1bea9b.replay'
$ date -u +%Y-%m-%dT%H:%M:%SZ
2026-08-29T04:22:09Z                                   # dispatch time, recorded before dispatching
$ gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
$ sleep 12
$ gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 5 \
  | jq -r 'sort_by(.createdAt)|reverse|.[]|[.databaseId,.createdAt,.status]|@tsv'
33233650158	2026-08-29T04:22:11Z	in_progress        ← created AFTER 04:22:09Z: this is the new run
33233338285	2026-08-29T04:14:31Z	completed
33227616497	2026-08-29T01:54:33Z	completed
33217780204	2026-08-28T22:41:52Z	completed
33217711224	2026-08-28T22:40:43Z	completed
$ gh run watch 33233650158 -R Metta-AI/coworld-builder --exit-status
… ✓ Complete job          (green)
$ gh run download 33233650158 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-28-nethack/viewer-check
```

Committed under `runs/2026-08-28-nethack/viewer-check/`:
`viewer-smoke.json`, `viewer-smoke.png`, `smoke-stdout.txt`, `smoke-stderr.txt` (empty).
A **second dispatch made earlier in this same phase-60 session** — run **33233338285**, dispatched
04:14:29Z against round 2's replay (`3db7fc96…`) — is preserved alongside as
`viewer-smoke-run33233338285.{json,png}` and its readouts are pasted below as a corroborating
second render.

**(b) Readouts — pasted verbatim from the downloaded artifact.**

```
$ jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-28-nethack/viewer-check/viewer-smoke.json
{"loaded":true,"ms":5499,"clock":"DLVL 1 T:0 · TURN 0/55 · HP 16/16 · $0 · NOT HUNGRY · SCORE 0","scorebug":"Not Hungry LOREMASTER ALPHA THE DIGGER SCORE 0 DL1 · $0 · 0 SLAIN DLVL 1 T:0 · TURN 0/55 · HP 16/16 · $0 · NOT HUNGRY · SCORE 0 FED HOARD ORACLE","feed_lines":0}

$ jq -c '.signals' runs/2026-08-28-nethack/viewer-check/viewer-smoke.json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}

$ jq -r '.failure // "no failure"' runs/2026-08-28-nethack/viewer-check/viewer-smoke.json
no failure

$ jq -c '{status,loading_text,canvas_text}' runs/2026-08-28-nethack/viewer-check/viewer-smoke.json
{"status":"OPEN","loading_text":null,"canvas_text":{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}}
```

The three scrub readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| at | clock |
|---|---|
| 0 %   | `DLVL 1 T:0 · TURN 0/55 · HP 16/16 · $0 · NOT HUNGRY · SCORE 0` |
| 50 %  | `DLVL 1 T:9 · TURN 2/55 · HP 16/16 · $0 · NOT HUNGRY · SCORE 0` |
| 100 % | `DLVL 1 T:17 · TURN 2/55 · HP 16/16 · $0 · NOT HUNGRY · SCORE 0` |

Corroborating run **33233338285** (round 2's replay, 181 ticks), same three readouts:

| at | clock |
|---|---|
| 0 %   | `DLVL 1 T:0 · TURN 0/55 · HP 16/16 · $0 · NOT HUNGRY · SCORE 0` |
| 50 %  | `DLVL 1 T:9 · TURN 3/55 · HP 16/16 · $0 · NOT HUNGRY · SCORE 0` |
| 100 % | `DLVL 1 T:17 · TURN 4/55 · HP 16/16 · $0 · NOT HUNGRY · SCORE 0` |
`{"loaded":true,"ms":2285,…,"feed_lines":0}`, `signals.data_replay_loaded == "true"`, no failure.

**Status: TRUE — `loaded: true` (via `data-replay-loaded="true"` on `<html>`; the postMessage bridge
was not used, `bridge_ready:false`, which the shell does not need), and the three clock readouts are
three distinct strings (`T:0` → `T:9` → `T:17`). Both independently dispatched runs agree.**

**Observation on the scrubber's reach (not a check-8 failure, but recorded).** In both runs the
100 % readout lands at `T:17` while the transport counter in the screenshot reads `18 / 156`
(run 33233650158) and `18 / 181` (run 33233338285). The full length is known to the viewer and
printed, but the scrub input's range at the instant the smoke script dragged it covered only the
~18 ticks ingested so far. Motion is proven; full-length seeking within the first ~5 s is not. A
phase-30 note for whoever next touches the transport, not an item-8 falsification.

**Console 404s (recorded).** The run's `console_tail` shows 15 HTTP 404s, all for leftover
coworld-ctf art the fork does not ship:
```
$ jq -r '.console_tail[]' viewer-smoke.json | grep -o 'sha256[^ ]*' | sed 's|.*d7b49e/||' | sort -u
art/lockerroom/blue_1.webp   art/lockerroom/blue_2.webp   art/lockerroom/blue_3.webp
art/lockerroom/blue_5.webp   art/lockerroom/blue_6.webp   art/lockerroom/green_1.webp
art/lockerroom/green_2.webp  art/lockerroom/green_3.webp  art/lockerroom/green_5.webp
art/lockerroom/green_6.webp  art/lockerroom/yellow_1.webp art/lockerroom/yellow_2.webp
art/lockerroom/yellow_5.webp art/lockerroom/yellow_6.webp soldier_yellow_front_gun.png
```
They are the starter's locker-room portrait sheet and a soldier sprite. They do not block the load
(`loaded:true`, `data_replay_error:null`) but they are dead requests on every spectator's page load
and would matter for the endcard.

**(c) What the viewer was asked to draw** — the primary replay's records, ordered
(`3466ad2b…`, 29 lines total, so `head -40` is the whole file):

```
turn	seat	type	summary
-	0	register	kind=llm label=loremaster alias=Alpha
1	0	decision	src=llm depth=1 verbs=move,move,move,move,move,search,search,search say="Starting exploration. Moving east and south to find stairs down."
2	0	decision	src=llm depth=1 verbs=move,move,move,move,search,search,search,move,move,search say="Exploring south from starting room to find stairs down."
3	0	decision	src=llm depth=1 verbs=move,move,move,move,move,move,move say="Exploring from the starting room to map out the dungeon and find stairs down."
4	0	decision	src=llm depth=1 verbs=move,move,move,move,move,search say="Exploring the starting room to find stairs down"
5	0	decision	src=llm depth=1 verbs=kick,kick,kick,kick say="Kicking locked door to explore"
6	0	decision	src=llm depth=1 verbs=search,search,travel say="Stopping ineffective kicks. Searching start room, then exploring east to find stairs down."
7	0	decision	src=llm depth=1 verbs=move,move,move,move say="Opening door and exploring east."
8	0	decision	src=llm depth=1 verbs=move,move,move,move,move,move say="Exploring east and south to find stairs down"
9	0	decision	src=llm depth=1 verbs=move,move,move,move,move,move,move,move say="Exploring south from starting room to find stairs down and resources."
10	0	decision	src=llm depth=1 verbs=move,move,move,move,move,move,move,move,move,move say="Exploring east from the starting room to map the dungeon."
11	0	decision	src=llm depth=1 verbs=move,move,move,move,move,move,move,move,move say="Exploring west and south from starting room to find stairs down"
12	0	decision	src=llm depth=1 verbs=move,move,move,move,move,move,move,move,search,search say="Exploring east and south from starting room to find stairs down."
13	0	decision	src=llm depth=1 verbs=move,move,move,move,move,move,move,move,move say="Exploring east from start room to find stairs down and items."
14	0	fallback	attempt=1 cause=timeout detail="llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke"
14	0	decision	src=llm depth=1 verbs=move say="Exploring east from starting room to find stairs down."
15	0	decision	src=llm depth=1 verbs=move,move,move,move,move,move,move,search,search,search say="Exploring east from starting room to find stairs down"
16	0	decision	src=llm depth=1 verbs=move,travel say="Exploring for stairs down"
17	0	decision	src=llm depth=1 verbs=search,search,search,move,move,move,move,move,move say="Searching for secrets near the door, then exploring west and north."
18	0	decision	src=llm depth=1 verbs=move,move,move,move,move,move,move,move,move say="Exploring east from starting room, then south to find stairs down"
19	0	decision	src=llm depth=1 verbs=kick,move,move,move,move,move say="Kicking open door to explore east"
20	0	decision	src=llm depth=1 verbs=move,search,search,search say="Kicking door open. Now exploring east from the locked door to find stairs down."
21	0	decision	src=llm depth=1 verbs=kick,kick,kick,kick say="Kicking locked door to explore"
22	0	decision	src=llm depth=1 verbs=move,search,move,search,move,search,move,search,move,search say="Exploring east from opened door, searching for stairs down"
23	0	decision	src=llm depth=1 verbs=move,move,move say="Fleeing jackal to doorway to fight 1v1"
24	0	decision	src=llm depth=1 verbs=move,move,move say="Trapped by jackal. Moving west to corridor to fight 1v1."
25	0	decision	src=llm depth=1 verbs=move,move,move,move,move say="Retreating to corridor to fight jackal from better position"
-	-	result	reason=complete endRule=death cause=killed killer=jackal score=[0] depth=1
```

```
$ jq -r '.results' /tmp/ep.json
{"names":["loremaster"],"aliases":["Alpha"],"scores":[0],"win":[false],"winner":null,"reason":"complete",
 "endRule":"death","variant":"descend","seed":88998717,"depthReached":1,"finalDepth":1,"gold":0,
 "monstersKilled":0,"doorsKicked":2,"hpFinal":0,"maxHpFinal":16,"causeOfDeath":"killed","killer":"jackal",
 "levelTurns":[25,0,0,0,0,0,0,0],"levelTicks":[156,0,0,0,0,0,0,0],"cellsSeen":119,"cellsTotal":6912,
 "primitivesExecuted":156,"finalTick":156,"turnsPlayed":25,"policyKinds":["llm"],"llmTurns":25,
 "fallbackTurns":0,"deadSeats":[false],"stopDetail":""}
```

### Spectator judgment

**It is legible, and it is unmistakably this game.** `viewer-smoke.png` (1280×800, captured at tick
18 of 156) shows a dark NetHack-styled console. Along the top is the scorebug: a large `0` beside
`SCORE`, `ALPHA THE DIGGER` in small caps and `LOREMASTER` in orange — the two-name-space rule the
design set (public alias vs policy label) is visibly honoured — then `DL1 · $0 · 0 SLAIN` with a
small progress bar, a `Not Hungry` chip pinned left, the headline `DLVL 1` centred, the live status
line `T:18 · TURN 2/55 · HP 16/16 · $0 · NOT HUNGRY · SCORE 0` beneath it, and the three deed chips
`FED` / `HOARD` / `ORACLE` at the right, all unlit (matching `deeds: []`). Down the left edge is the
depth ladder `DL1`…`DL8`, with only `DL1` filled — the picture agrees with `depthReached: 1`. Below
that is a small tile view of the dungeon room (grey floor, a red creature, two chest-coloured tiles
and a blue item) — the jackal and the room furniture. Centre-left is the panel that carries the
game: `TERMINAL 48×18` drawing the actual ASCII map — room walls `----`/`|`, the hero `@`, the
up-staircase `<` — over the NetHack message line `You cannot move there.` and the canonical status
line `Dlvl:1 $:0 HP:16(16) AC:7 Xp:1/0 T:18 Not Hungry`. On the right is the decision feed: two
blocks reading `PLAN 1 — MOVE · MOVE · MOVE · MOVE · MOVE · SEARCH · SEARCH · SEARCH` and
`PLAN 2 — MOVE · MOVE · MOVE · MOVE · SEARCH · SEARCH · SEARCH · MOVE · MOVE · SEARCH`, each
followed by `ALPHA` and the quoted say. **Those match the replay record byte-for-byte**: turn 1's
verbs and `"Starting exploration. Moving east and south to find stairs down."`, turn 2's verbs and
`"Exploring south from starting room to find stairs down."` The picture and the record are the same
episode.

**It is the starter's chrome, not a lookalike rewrite.** Across the bottom is the paintbot/raid/hive
transport strip — restart, step-back, pause, `+5s`, step-forward, loop, fast-forward, a `spoilers`
toggle, the tick counter `18 / 156`, and `1× 2× 4× 8×` speed chips — over the scrubber with its
momentum graph, here labelled `DEPTH`, with the playhead drawn at ~12 %. `ALPHA THE DIGGER …` sits
as the caption above the strip. This is the same transport/scrubber/scorebug/endcard family the
starter ships, retargeted, not a different product (the cogame-gridlock failure mode is not present).

**What is imperfect, said plainly.** (i) The layout leaves a large empty black region through the
centre-right; the terminal panel and the tile view together occupy under a third of the frame while
the feed hugs the right edge. (ii) In the corroborating run's frame
(`viewer-smoke-run33233338285.png`) the fit-shrunk tile view is drawn further left and **overlaps the
`DL1`–`DL7` ladder labels**, making them hard to read; in the primary frame it clears them. The
camera's fit-shrink (a documented phase-20 deviation from clamp+pan) makes that placement
replay-dependent. (iii) `feed_lines: 0` in the JSON is a **selector mismatch, not an empty feed** —
the screenshot plainly shows two plan blocks and two `ALPHA` quotes, so the smoke script's feed
selector does not match this shell's DOM; I record the number as fetched and correct it from the
picture rather than trusting it. (iv) The 15 locker-room/soldier 404s above. (v) No endcard is
visible because the playhead is at tick 18; the death at tick 156 was not reached in the capture, so
I make **no claim** about how the headstone renders.

**Verdict on the spectator experience: legible and on-topic.** A viewer who opens this page can read,
without help, who is playing, how deep they are, how much HP and gold they have, what the map looks
like, what the policy just decided and why it said it decided that, and can scrub the run. The one
thing the picture cannot show — because the policies never did it — is a descent past DL1; see item
4's sub-finding.

---

## Appendix — what this run's evidence establishes for STATE

```
verify.rounds          = [1: round_1abe8f06-a82b-4596-a43d-8515631ee99b (completed 03:50:43Z),
                          2: round_aadd7254-b6a0-4659-82a2-d8b62fdaa7d3 (completed 04:05:39Z),
                          3: round_b7f16922-e6ee-45d0-9c69-d6caee76f46c (completed 04:20:42Z)]
verify.replay          = https://softmax-public.s3.amazonaws.com/replays/3466ad2b-2101-4897-ac3f-72e09c1bea9b.replay
verify.iframe_static   = true
verify.viewer_check_run = 33233650158   (corroborating earlier dispatch this session: 33233338285)
```
