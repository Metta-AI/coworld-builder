# VERIFY — smac-starcraft-micro   (2026-08-27T11:28Z, re-verify pass)

Verdict: **all-true (8/8)**

- coworld `cow_345bfc54-561e-4606-8de1-e3086f37d58a` version **0.1.3**, canonical
- manifest_sha `sha256:3c1e7703ca64b59f9774673290450d9ca1f3429e39c01738e0b213521a4ed078`
- league `league_f42b4821-882b-428e-b803-630671e86726`, division `div_efd2ab9a-88fd-4c97-952c-64f38e3fadaa`
- Checks 3/4/5 target the **latest completed round, round 6** (`round_e71db7a4-34a0-44de-ab19-d104747c7847`,
  `ereq_805f41dc-56e3-4d11-9d97-dd26a29f9dc1`) — the first round produced by the 0.1.3 image.

All evidence below was fetched fresh in this pass (2026-08-27T11:23Z–11:28Z), except the two
documented exceptions: check 7 reads the committed `runs/<run>/release-result.json`, and check 8's
rendered evidence comes from the `viewer-check.yml` run **this pass dispatched** (33067338841).

Headers sent on every Observatory call: `Authorization: Bearer …` (value redacted) and
`User-Agent: coworld-builder/1.0`; check 5 adds `X-Use-Elevated-Privileges: true`.

---

## Changelog

| When | What |
|---|---|
| 2026-08-27T10:17Z–10:45Z | **First phase-60 pass** (verifier thread `sthr_019Pk1pYSHYZfudFhjMJj7db`), against coworld 0.1.2 (`cow_476a8db4…`), rounds 2–3. Result **7/8 TRUE**. Checks 1,2,3,4,6,7,8 all TRUE. |
| — | **Check 5 was FALSE.** The round-3 hosted log carried two `falling back` lines with `cause=parse_error` / `reply named no commanded cog`. Adjudicated (rails) as a real, small **design deviation**: `design.md` §reply-schema repair table pins *"empty/missing `cogs` → keep last turn's directive"* and *"unmatched entry → assign by position"*, but the code took `parse_error → retry → focusfire fallback`; additionally the attempt-1 **interim** log line emitted the literal string `falling back` even when the retry succeeded. The platform-429/Bedrock-capacity exception was tested and **refuted** (all sidecar calls returned 200; a contemporaneous LLM coworld, knights-archers, was showing real 429s and this one was not). |
| 2026-08-27T~10:50Z–11:13Z | **Fix + re-release.** Repo commit `545afa9` *"fix(decide): only the terminal degrade line may say 'falling back'"* implements the documented repair path and reserves the phrase for the terminal degrade. Released as **0.1.3**, cow_id `cow_345bfc54…`, canonical + certified (release run `33065622007`); `release-result.json` / `release-summary.md` in this run dir are the 0.1.3 copies. |
| 2026-08-27T11:13Z–11:19Z | **Round 6** ran on the 0.1.3 image and completed. |
| 2026-08-27T11:23Z–11:28Z | **This re-verify pass.** All eight checks re-fetched from scratch against round 6. Check 5 now **CLEAN** — 0 matches for the forbidden patterns, and the two former fallbacks appear as the design-conformant repair line `smac llm: seat 0 repaired: reply named no commanded cog; kept last turn's directive`. **8/8 TRUE.** |

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

```
GET https://softmax.com/api/observatory/v2/rounds?league_id=league_f42b4821-882b-428e-b803-630671e86726&limit=20
  -H Authorization  -H User-Agent                                        HTTP 200
$ jq '.entries[]|{id,round_number,status,created_at,completed_at,error}'
```
```json
{
  "id": "round_e71db7a4-34a0-44de-ab19-d104747c7847",
  "round_number": 6,
  "status": "completed",
  "created_at": "2026-08-27T11:13:41.963662Z",
  "started_at": null,
  "completed_at": "2026-08-27T11:18:59.378670Z",
  "error": null
}
{
  "id": "round_a9bfaf2e-0c8e-44f7-8ed8-6dd164090912",
  "round_number": 5,
  "status": "completed",
  "created_at": "2026-08-27T10:58:41.460902Z",
  "started_at": null,
  "completed_at": "2026-08-27T11:02:25.605289Z",
  "error": null
}
{
  "id": "round_cbf8c7c5-969e-428f-9eba-1f92fc6fa087",
  "round_number": 4,
  "status": "completed",
  "created_at": "2026-08-27T10:43:40.995712Z",
  "started_at": null,
  "completed_at": "2026-08-27T10:46:49.777718Z",
  "error": null
}
{
  "id": "round_d83fe934-6863-4b88-bead-cdc1ff9a56eb",
  "round_number": 3,
  "status": "completed",
  "created_at": "2026-08-27T10:28:40.440538Z",
  "started_at": null,
  "completed_at": "2026-08-27T10:33:27.399125Z",
  "error": null
}
{
  "id": "round_b20379cb-f929-431f-ae59-372e03b02015",
  "round_number": 2,
  "status": "completed",
  "created_at": "2026-08-27T10:13:38.911419Z",
  "started_at": null,
  "completed_at": "2026-08-27T10:17:36.999085Z",
  "error": null
}
{
  "id": "round_a414900b-02da-4544-9b34-3eb1935a2586",
  "round_number": 1,
  "status": "failed",
  "created_at": "2026-08-27T10:13:00.562652Z",
  "started_at": null,
  "completed_at": "2026-08-27T10:13:00.959746Z",
  "error": "Temporal RoundWorkflow failed before settling the round."
}
```
```
$ … | jq -r '[.entries[]|select(.status=="completed")]|length'
5
```

**Failed round, error verbatim (does not count):** round 1,
`"Temporal RoundWorkflow failed before settling the round."` — it fired at the unpause instant
(10:13:00.5Z) and died 0.4 s later, before settling.

**Fillers were set before every counted round.** `log.md` records the filler registration in the
phase-50 batch written at 10:15:53Z, executed before the unpause at 10:13:00Z:
```
2026-08-27T10:15:53Z 50 fillers POST 200: focusfire:v3=2964b7ba, charge:v3=a1ecf538 (neither champion)
2026-08-27T10:15:53Z 50 unpause POST 200 paused=false; trigger-round POST 200 workflow=ladder-league_f42b4821
```
Fetched corroboration — round 2 (the earliest **counted** round) already carried both filler
policy-version ids in its episode request, created 10:13:39.296Z:
```
GET …/rounds/round_b20379cb-f929-431f-ae59-372e03b02015/episode-requests   HTTP 200
```
```json
{"id":"ereq_e860f660-02bb-4be8-9321-1c08965e9bc0","status":"completed",
 "policy_version_ids":["32ec1f23-fb86-47c1-b05f-b94ee099c5fd","5ef5a887-6ded-4a53-aeef-64b190dc59b9",
                       "2964b7ba-9e1d-4edb-955c-f9d6c949ede0","2964b7ba-9e1d-4edb-955c-f9d6c949ede0",
                       "a1ecf538-9599-423c-8170-9a19968738f4"],
 "created_at":"2026-08-27T10:13:39.296290Z"}
```
`2964b7ba-9e1d-4edb-955c-f9d6c949ede0` and `a1ecf538-9599-423c-8170-9a19968738f4` are exactly
`STATE.policies.filler_version_ids`.

**Status: TRUE** — 5 completed rounds (2, 3, 4, 5, 6), all after filler registration; requirement is ≥ 2.
Round 6 (11:13:41Z → 11:18:59Z) and round 5 (10:58:41Z → 11:02:25Z) alone satisfy it, and round 6
is the first on the fixed 0.1.3 image.

---

## 2. Both champions ranked, fillers absent — TRUE

```
GET https://softmax.com/api/observatory/v2/divisions/div_efd2ab9a-88fd-4c97-952c-64f38e3fadaa/leaderboard
  -H Authorization  -H User-Agent                                        HTTP 200
$ jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey-1	smac-starcraft-micro-skirmish:v3	1018.4347554881504	5	3.0
2	daveey	smac-starcraft-micro-marshal:v3	981.5652445118496	5	2.0
```
Raw body (bare list, not `.entries`):
```json
[{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
  "score":1018.4347554881504,"score_label":"MMR","score_value_type":"integer","rounds_played":5,
  "episode_wins":3.0,"episodes_played":null,"win_rate":0.6,
  "policy_label":"smac-starcraft-micro-skirmish:v3","recent_rounds":null},
 {"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
  "score":981.5652445118496,"score_label":"MMR","score_value_type":"integer","rounds_played":5,
  "episode_wins":2.0,"episodes_played":null,"win_rate":0.4,
  "policy_label":"smac-starcraft-micro-marshal:v3","recent_rounds":null}]
```

**Status: TRUE** — rows for both `daveey` (marshal:v3) and `daveey-1` (skirmish:v3), each
`rounds_played = 5 ≥ 1`. Neither filler (`focusfire:v3`, `charge:v3`) appears on the leaderboard —
they are episode participants only, marked `is_filler: true` (see check 3). Ranks have separated
since the first pass (was 1001.47 / 998.53 after 2 rounds; now 1018.43 / 981.57 after 5).

---

## 3. Latest round's episode request completed with a replay — TRUE

`GET /episode-requests?round_id=` is dead on this platform (405); the working shape is the
sub-resource, per `playbooks/observatory-api.md`.

```
GET https://softmax.com/api/observatory/v2/rounds/round_e71db7a4-34a0-44de-ab19-d104747c7847/episode-requests
  -H Authorization  -H User-Agent                                        HTTP 200
```
```json
{
  "entries": [
    {
      "id": "ereq_805f41dc-56e3-4d11-9d97-dd26a29f9dc1",
      "status": "completed",
      "coworld_id": "cow_345bfc54-561e-4606-8de1-e3086f37d58a",
      "round_id": "round_e71db7a4-34a0-44de-ab19-d104747c7847",
      "replay_url": "https://softmax-public.s3.amazonaws.com/replays/4a7fecfb-6b68-4a3b-9046-e84f375ce846.replay",
      "policy_version_ids": ["32ec1f23-fb86-47c1-b05f-b94ee099c5fd","5ef5a887-6ded-4a53-aeef-64b190dc59b9",
                             "2964b7ba-9e1d-4edb-955c-f9d6c949ede0","a1ecf538-9599-423c-8170-9a19968738f4",
                             "a1ecf538-9599-423c-8170-9a19968738f4"],
      "created_at": "2026-08-27T11:13:42.449969Z"
    }
  ],
  "next_cursor": null
}
```

```
GET https://softmax.com/api/observatory/v2/episode-requests/ereq_805f41dc-56e3-4d11-9d97-dd26a29f9dc1
  -H Authorization  -H User-Agent                                        HTTP 200
$ jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/4a7fecfb-6b68-4a3b-9046-e84f375ce846.replay",
  "participants": [
    {"position":0,"kind":"policy","policy_version_id":"32ec1f23-fb86-47c1-b05f-b94ee099c5fd",
     "policy_id":"041f6bda-825a-4449-b462-587605087b33","policy_name":"smac-starcraft-micro-marshal",
     "version":3,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
     "is_filler":false,"is_seed":false},
    {"position":1,"kind":"policy","policy_version_id":"5ef5a887-6ded-4a53-aeef-64b190dc59b9",
     "policy_id":"a9d18cf4-56e1-4b94-8899-4d348b69e98b","policy_name":"smac-starcraft-micro-skirmish",
     "version":3,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
     "is_filler":false,"is_seed":false},
    {"position":2,"kind":"policy","policy_version_id":"2964b7ba-9e1d-4edb-955c-f9d6c949ede0",
     "policy_id":"a0715594-95f5-400c-886c-b2eb3ea058d5","policy_name":"smac-starcraft-micro-focusfire",
     "version":3,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
     "is_filler":true,"is_seed":false},
    {"position":3,"kind":"policy","policy_version_id":"a1ecf538-9599-423c-8170-9a19968738f4",
     "policy_id":"cd63e8bb-aa10-45a2-bfaa-30b97b383953","policy_name":"smac-starcraft-micro-charge",
     "version":3,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
     "is_filler":true,"is_seed":false},
    {"position":4,"kind":"policy","policy_version_id":"a1ecf538-9599-423c-8170-9a19968738f4",
     "policy_id":"cd63e8bb-aa10-45a2-bfaa-30b97b383953","policy_name":"smac-starcraft-micro-charge",
     "version":3,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
     "is_filler":true,"is_seed":false}
  ],
  "participant_scores": [
    {"position":0,"score":0.6970332846715328},
    {"position":1,"score":0.6970356204379562},
    {"position":2,"score":0.6970881751824817},
    {"position":3,"score":0.6971261313868613},
    {"position":4,"score":0.6971167883211679}
  ]
}
```

**Status: TRUE** — `status == "completed"`, non-null `replay_url` on S3, and `participants` names
both champions (`daveey` seat 0 = marshal:v3, `daveey-1` seat 1 = skirmish:v3, both
`is_filler:false`) with the three filler seats flagged `is_filler:true` and rendered in the replay
as `Baseline` / `Baseline (2)` / `Baseline (3)` (see check 4's `names`).

*Observation (not a failure):* `participant_scores` are nearly identical across all five seats
(0.69703–0.69713) because the scalar is a shared **team** score; ladder separation comes from
per-episode outcomes, which is where the 1018/982 MMR split in check 2 comes from.

---

## 4. Replay bytes are valid and show the game — TRUE

The replay is the starter's **binary `COWLDSMC`** container, not JSON, so this check uses the
substitute the design note declares in advance — `design.md` §"Replay bytes (self-sufficient)",
lines 982–992, *"The phase-60 substitute for SPEC §Definition of done check 4"*: clone the repo,
run the shipped stdlib-only `tools/replay_summary.py`, and apply a **strict** `jq -e .` to its
output. Requirements it pins: `protocol == "smac-starcraft-micro/v1"`,
`results.reason == "complete"` (or the declared-acceptable `deadline`), `results.enemyKilled > 0`,
champion-seat directives `source == "llm"` — not all fallbacks.

```
$ curl -sSL "https://softmax-public.s3.amazonaws.com/replays/4a7fecfb-6b68-4a3b-9046-e84f375ce846.replay" -o /tmp/ep.replay
http=200 size=93871
$ head -c 32 /tmp/ep.replay | od -c
0000000   C   O   W   L   D   S   M   C 001  \0 024  \0   s   m   a   c
0000020   -   s   t   a   r   c   r   a   f   t   -   m   i   c   r   o
```
Magic `COWLDSMC`, format version 1, gameName `smac-starcraft-micro` — as the design table specifies.

```
$ gh repo clone Metta-AI/cogame-smac-starcraft-micro /tmp/smacrepo -- --depth 1
$ git -C /tmp/smacrepo log -1 --format='%H %s'
545afa9f610f9b15d3990da2297f920575365fea fix(decide): only the terminal degrade line may say "falling back"
$ python3 /tmp/smacrepo/tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json ; echo exit=$?
exit=0
$ jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok
```

```
$ jq -c 'del(.directives)' /tmp/ep.json
```
```json
{"protocol":"smac-starcraft-micro/v1","gameVersion":"1","seed":600151965,"scenario":"default",
 "names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)"],
 "aliases":["RANGER-alpha","RANGER-beta","BLADE-alpha","BLADE-beta","BLADE-gamma","E1","E2","E3","E4","E5"],
 "roles":["ranger","ranger","blade","blade","blade"],
 "enemyRoles":["ranger","ranger","blade","blade","blade"],
 "policyKinds":["llm","llm","scripted","scripted","scripted"],
 "battles":3,"tickCount":93871,"fallbacks":0,"budgetGuards":0,
 "results":{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)"],
  "scores":[0.6970332846715328,0.6970356204379562,0.6970881751824817,0.6971261313868613,0.6971167883211679],
  "win":[true,true,true,true,true],"role":["ranger","ranger","blade","blade","blade"],
  "alias":["RANGER-alpha","RANGER-beta","BLADE-alpha","BLADE-beta","BLADE-gamma"],
  "damageDealt":[114,122,302,432,400],"damageTaken":[150,120,304,326,360],
  "kills":[2,3,4,2,2],"deaths":[2,1,2,2,3],"shots":[33,40,0,0,0],
  "llmTurns":[23,23,0,0,0],"fallbackTurns":[0,0,0,0,0],
  "teamScore":0.697,"battlesWon":2,
  "battleResults":["victory","full_time","victory"],"battleTicks":[462,1440,721],
  "battleDamagePct":[100,85,100],"battleLossPct":[70,97,93],
  "enemyKilled":5,"enemyTotal":5,"scenario":"default","reason":"complete","endRule":"victory",
  "games":3,"finalTick":3232,"seed":600151965}}
```

```
$ jq -r '.protocol, .results.reason, .results.enemyKilled, .results.teamScore' /tmp/ep.json
smac-starcraft-micro/v1
complete
5
0.697
$ jq -r '[.directives[]]|length' /tmp/ep.json
115
$ jq -r '[.directives[]|.source]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.json
{"llm": 46, "scripted": 69}
$ jq -r '[.directives[]|select(.seat<2)|.source]|unique' /tmp/ep.json
["llm"]
$ jq -r '[.directives[]|select(.seat<2 and (.note|length)>0)]|length' /tmp/ep.json
46
$ jq -r '.fallbacks' /tmp/ep.json
0
```

A champion-seat directive verbatim (seat 0, battle 1 turn 0):
```json
{"k":"directive","battle":1,"turn":0,"seat":0,"alias":"RANGER-alpha","role":"ranger",
 "source":"llm","latency_ms":3561,
 "note":"Turn 0: All enemies out of range. E1 closest at 472px. Move to engage.",
 "cogs":[{"id":"RANGER-alpha","intent":"attack_move","target":[750,260],"say":"E1",
          "target_id":1,"face":[846,242]}]}
```

**Status: TRUE** — strict UTF-8 JSON under `jq -e`; `protocol == "smac-starcraft-micro/v1"`
matching the manifest; `results.reason == "complete"` (no `deadline` exception needed);
`enemyKilled = 5` of `enemyTotal = 5` > 0; all **46/46** champion-seat directives (seats 0 and 1,
23 turns each) are `source == "llm"` with non-empty tactical `note`s and real intents
(`attack_move`, `kite`, `focus`, `hold`, `retreat`) — **zero** fallbacks
(`"fallbacks":0`, `"fallbackTurns":[0,0,0,0,0]`), not merely a small minority.

---

## 5. Hosted game log is clean — TRUE  *(this is the check that was FALSE in the first pass)*

```
GET https://softmax.com/api/observatory/v2/episode-requests/ereq_805f41dc-56e3-4d11-9d97-dd26a29f9dc1/artifacts/logs
  -H Authorization  -H User-Agent  -H X-Use-Elevated-Privileges           HTTP 200, 103740 bytes
$ grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/log6.txt || echo CLEAN
CLEAN
```
The endpoint returns Python-`repr` blocks (`b'…\n…'`) per container, so the raw body is only 11
physical lines. Re-run against the **unescaped** text as well, so the result is not an artefact of
the escaping:
```
$ python3 -c "…unescape b'…' blocks…" > /tmp/log6.dec.txt ; wc -l /tmp/log6.dec.txt
199 /tmp/log6.dec.txt
$ grep -n '^===== container' /tmp/log6.dec.txt
1:===== container: coworld-init-config =====
4:===== container: bedrock-sidecar =====
194:===== container: game =====
197:===== container: worker =====
$ grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/log6.dec.txt || echo CLEAN
CLEAN
```

**Zero matches for all four forbidden patterns, on both the raw and the unescaped body.**

Bedrock sidecar, same log — every call succeeded, so there is nothing for a fallback to catch:
```
$ (bedrock-sidecar section) grep -c 'bedrock-runtime…"HTTP/1.1 200 OK"'
bedrock invoke codes: {'200': 46}
usage records: 46
ERROR/WARN lines: 0
occurrences of 'max_tokens': 0
```
46 Bedrock invocations, all HTTP 200, exactly matching the 46 LLM directives in check 4 — i.e. one
call per champion turn with **no retries at all**. Last usage record verbatim:
```json
{"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar",
 "episode_request_id":"805f41dc-56e3-4d11-9d97-dd26a29f9dc1",
 "job_request_id":"4a7fecfb-6b68-4a3b-9046-e84f375ce846","role":"game","slot":"game",
 "image_digest":"sha256:f9ce4534e5da32315e8dbc60557e3d13dd6b73237aa90aea662af7a2dca5dc6d",
 "model":"global.anthropic.claude-haiku-4-5-20251001-v1:0","operation":"InvokeModel",
 "usage":{"input_tokens":1869,"output_tokens":92,"total_tokens":null,
          "cache_read_input_tokens":0,"cache_write_input_tokens":0}}
```

**The 0.1.3 fix is visible in the log.** The two schema hiccups that produced the first pass's
`falling back` lines now appear as the design-conformant repair, and the phrase `falling back` is
gone:
```
$ grep -o "smac llm: seat [0-9] repaired: [^\\]*" /tmp/log6.dec.txt
smac llm: seat 0 repaired: reply named no commanded cog; kept last turn's directive on turn 0
smac llm: seat 0 repaired: reply named no commanded cog; kept last turn's directive on turn 0
```
That is exactly the row `design.md` §reply-schema repair table pins ("empty/missing `cogs` → keep
last turn's directive"), and it is corroborated by the replay's `"fallbacks":0` /
`"fallbackTurns":[0,0,0,0,0]` in check 4.

Game-container excerpt (unescaped), showing a clean episode end:
```
smac llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
seat 0 registered: kind=llm baseline=focusfire
seat 1 registered: kind=llm baseline=focusfire
seat 2 registered: kind=scripted baseline=focusfire
seat 3 registered: kind=scripted baseline=charge
seat 4 registered: kind=scripted baseline=charge
game started: players=10
battle 1 done: victory in 462 ticks, damage 480/480, losses 340/480
battle 2 done: full_time in 1440 ticks, damage 410/480, losses 470/480
battle 3 done: victory in 721 ticks, damage 480/480, losses 450/480
Writing replay file: /tmp/smac-replay-1.bitreplay
Replay written: /tmp/smac-replay-1.bitreplay (93871 bytes)
Events written: /coworld/events.json (1705 events, 385990 bytes)
```

**Status: TRUE** — CLEAN. No documented exception is being invoked; the log is clean on its own
terms. (The first pass's platform-Bedrock-capacity exception was refuted then and is not needed now.)

*Minor observation for phase 30, not a check failure:* the repair line reads "kept last turn's
directive **on turn 0**" — on turn 0 of a battle there is no previous turn, so the kept directive
is either empty or carried across the battle boundary. Worth a look, but it produced no fallback,
no scripted substitution, and no visible defect in the replay.

---

## 6. The public page uses the static replay path — TRUE

**Source used: (iii) the page's own SSR payload + (iv) the `replays/session` route its JS calls.**
Both earlier sources were tried first and are non-evidence on this platform, exactly as
`playbooks/observatory-api.md` §"Featured match / replay route" predicts.

*(i) raw-HTML iframe grep — finds nothing; the page is client-rendered:*
```
$ curl -sS "https://softmax.com/smac-starcraft-micro" | grep -o '<iframe[^>]*src="[^"]*"'
http=200 size=675234    (fetched 2026-08-27T11:26Z)
NO IFRAME IN SERVED HTML (client-rendered)
```

*(ii) `/coworlds` list — `replay_viewer` and `featured_match` are null platform-wide:*
```
GET …/coworlds?limit=200  -H Authorization -H User-Agent                 HTTP 200
$ jq '.[]|select(.name=="smac-starcraft-micro")|{id,name,version,canonical,replay_viewer,featured_match,manifest_sha}'
```
```json
{"id":"cow_345bfc54-561e-4606-8de1-e3086f37d58a","name":"smac-starcraft-micro","version":"0.1.3",
 "canonical":true,"replay_viewer":null,"featured_match":null,"manifest_sha":null}
{"id":"cow_476a8db4-f5df-4d93-b0c2-1c302ba201bc","name":"smac-starcraft-micro","version":"0.1.2",
 "canonical":false,"replay_viewer":null,"featured_match":null,"manifest_sha":null}
{"id":"cow_b5528413-8799-409f-b24c-59e72d8d95dc","name":"smac-starcraft-micro","version":"0.1.1",
 "canonical":false,"replay_viewer":null,"featured_match":null,"manifest_sha":null}
{"id":"cow_7801ad27-8625-4adb-b3fc-0e82b5c6ba11","name":"smac-starcraft-micro","version":"0.1.0",
 "canonical":false,"replay_viewer":null,"featured_match":null,"manifest_sha":null}
```
(Also confirms 0.1.3 is the **only** canonical version, and 0.1.2 — the version the first pass
verified — has been demoted.)

*(iii) the featured match, server-rendered into the page's SSR payload at `state.playlist[0]` —
pasted from the fetched HTML with the doubled JSON escaping undone:*
```json
"state":{"leagueId":"league_f42b4821-882b-428e-b803-630671e86726",
 "playlist":[{"episodeId":"0c35143e-8c32-444f-bb24-be1c704b2a82",
  "coworldId":"cow_345bfc54-561e-4606-8de1-e3086f37d58a",
  "coworldName":"smac-starcraft-micro","coworldVersion":"0.1.3",
  "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/4a7fecfb-6b68-4a3b-9046-e84f375ce846.replay",
  "finishedAt":"2026-08-27T11:18:55.257849Z","roundNumber":6,"episodeNumber":1,
  "code":"smac-starcraft-micro.r6.e1",
  "matchup":{"divisionId":"div_efd2ab9a-88fd-4c97-952c-64f38e3fadaa","divisionName":"Competition",
   "first":{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
            "score":1018.4347554881504,"score_label":"MMR","rounds_played":5,"episode_wins":3,
            "win_rate":0.6,"policy_label":"smac-starcraft-micro-skirmish:v3"},
   "second":{"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
             "score":981.5652445118496,"score_label":"MMR","rounds_played":5,"episode_wins":2,
             "win_rate":0.4,"policy_label":"smac-starcraft-micro-marshal:v3"}},
  "inspectUrl":"/observatory/v2?tab=overview&detail=episode-request:ereq_805f41dc-56e3-4d11-9d97-dd26a29f9dc1",
  "outcome":"first"}]}
```
**The featured pointer has already advanced to the new round** — `roundNumber: 6`,
`coworldVersion: "0.1.3"`, `cow_345bfc54…`, and the same `replayUrl` and `ereq_805f41dc…` verified
in checks 3–5. No re-polling was needed; it was current on the first fetch.

*(iv) the iframe `src`, from the call the page's JS makes:*
```
POST https://softmax.com/api/observatory/v2/coworlds/replays/session
  -H Authorization -H User-Agent -H content-type
  -d '{"coworld_id":"cow_345bfc54-561e-4606-8de1-e3086f37d58a",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/4a7fecfb-6b68-4a3b-9046-e84f375ce846.replay"}'
HTTP 200
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_345bfc54-561e-4606-8de1-e3086f37d58a/sha256%3A3c1e7703ca64b59f9774673290450d9ca1f3429e39c01738e0b213521a4ed078/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F4a7fecfb-6b68-4a3b-9046-e84f375ce846.replay&v=2",
  "ready": true
}
```
The `<sha>` segment is the coworld's manifest hash, URL-encoded, and it is the **0.1.3** one:
```
$ jq -r '.coworld.manifest_sha' runs/2026-08-27-smac-starcraft-micro/STATE.json
sha256:3c1e7703ca64b59f9774673290450d9ca1f3429e39c01738e0b213521a4ed078
```
(`sha256%3A3c1e7703…` in the URL — matches; the first pass's `sha256:4575435f…` / `cow_476a8db4…`
0.1.2 pair is gone.)

**Status: TRUE** — a featured match is present (SSR `playlist[0]`, round 6 episode 1, two-player
matchup naming both champions), and the iframe `src` is the **static** path
`/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` with `ready: true`.
It is **not** a `/client/replay` pod URL.

---

## 7. Certification declared the static bundle — TRUE

**Source: the committed `runs/2026-08-27-smac-starcraft-micro/release-result.json`** — the 0.1.3
artifact phase 40 downloaded from release run `33065622007` and committed. It was present, so no
re-download was needed and `/tmp` was not consulted.

```
$ jq -r '.certify.replay_liveness' runs/2026-08-27-smac-starcraft-micro/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
$ jq -c '{version,cow_id,canonical,manifest_sha}' runs/2026-08-27-smac-starcraft-micro/release-result.json
{"version":"0.1.3","cow_id":"cow_345bfc54-561e-4606-8de1-e3086f37d58a","canonical":true,
 "manifest_sha":"sha256:3c1e7703ca64b59f9774673290450d9ca1f3429e39c01738e0b213521a4ed078"}
```

**Status: TRUE** — the string contains `Replay liveness: skipped (static replay bundle declared`,
and the file is the 0.1.3 release (version, cow_id and manifest_sha all match STATE and the
iframe `src` in check 6).

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — TRUE

*(a) Dispatch — against the exact iframe `src` from check 6.*
```
$ date -u +%FT%TZ
2026-08-27T11:25:57Z
$ gh workflow run viewer-check.yml -R Metta-AI/coworld-builder \
    -f url='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_345bfc54-561e-4606-8de1-e3086f37d58a/sha256%3A3c1e7703ca64b59f9774673290450d9ca1f3429e39c01738e0b213521a4ed078/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F4a7fecfb-6b68-4a3b-9046-e84f375ce846.replay&v=2' \
    -f timeout=90
$ gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
  | jq -r 'sort_by(.createdAt)|reverse|.[]|[.databaseId,.createdAt,.status]|@tsv'
33067338841	2026-08-27T11:25:59Z	in_progress     <-- MINE (createdAt 11:25:59Z > dispatch 11:25:57Z)
33066666879	2026-08-27T11:16:44Z	completed
33063761313	2026-08-27T10:36:18Z	completed       <-- first pass's run, NOT reused
33063093381	2026-08-27T10:27:11Z	completed
33062642745	2026-08-27T10:21:00Z	completed
…
$ gh run watch 33067338841 -R Metta-AI/coworld-builder --exit-status
✓ main viewer-check · 33067338841 — viewer-check in 35s (ID 98500590839) — all steps ✓, green
$ gh run download 33067338841 -R Metta-AI/coworld-builder -n viewer-check \
    -D runs/2026-08-27-smac-starcraft-micro/viewer-check
smoke-stderr.txt (0 B)  smoke-stdout.txt (756 B)  viewer-smoke.json (1552 B)  viewer-smoke.png (765502 B)
```
The run's own record of the URL it opened confirms identity (`viewer-smoke.json .url`):
`…/static/cow_345bfc54-561e-4606-8de1-e3086f37d58a/sha256%3A3c1e7703…/index.html?replay=…4a7fecfb…&v=2`.
`runs/2026-08-27-smac-starcraft-micro/viewer-check/` was overwritten with this run's artifact.

*(b) The readouts, verbatim.*
```
$ jq -c '{loaded, ms, clock, scorebug, feed_lines}' viewer-check/viewer-smoke.json
{"loaded":true,"ms":3310,"clock":"1:00 BATTLE 1/3 · DEFAULT · 5 V 5 · TURN 1/12","scorebug":"─▸ daveey DMG 0 0k ─▸ daveey-1 DMG 0 0k ╱ Baseline DMG 0 0k 1:00 BATTLE 1/3 · DEFAULT · 5 V 5 · TURN 1/12 ╱ Baseline ( DMG 0 0k ╱ Baseline ( DMG 0 0k OURS 5 UP · 480/480 (100%) THEIRS 5 UP · 480/480 (100%)","feed_lines":0}

$ jq -c '.signals' viewer-check/viewer-smoke.json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}

$ jq -r '.failure // "no failure"' viewer-check/viewer-smoke.json
no failure

$ jq -c '{status, loading_text, console_tail, canvas_text}' viewer-check/viewer-smoke.json
{"status":"OPEN","loading_text":null,"console_tail":[],
 "canvas_text":{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}}
```

*The three clock readouts:*

| scrub | clock |
|---|---|
| 0 %   | `1:00 BATTLE 1/3 · DEFAULT · 5 V 5 · TURN 1/12` |
| 50 %  | `FINAL BATTLE 2/3 · DEFAULT · 3 V 0 · TURN 5/12` |
| 100 % | `0:29 BATTLE 2/3 · DEFAULT · 5 V 5 · TURN 7/12` |

All three **differ** — different battle, different turn, different countdown, different army
counts (5v5 → 3v0 → 5v5). The 100 % readout landing inside battle 2/3 rather than at the end is
the shell's timeline mapping across a three-battle episode; it is still a distinct, advanced frame,
not a repeat.

**`feed_lines: 0` is a known limit of the harness, not a defect of this viewer.** The probe reads
`document.querySelector("#feed, .feed, #log")`
(`templates/tools/ci/viewer_smoke.mjs:425`), and this lineage's feed element is `id="killfeed"`
(`client/replay_broadcast.html:1348`), which no selector in that list matches. The screenshot shows
the feed is in fact rendering (`BLADE-gamma: charge`, bottom right). Recorded as a
harness-selector gap for the coordinator; it is not scored against check 8.

*(c) The replay JSON the viewer was asked to draw* — from `/tmp/ep.replay` via
`tools/replay_summary.py`, ordered `battle / turn / seat / alias / source / note / intent / say`:

Early:
```
1	0	0	RANGER-alpha	llm	Turn 0: All enemies out of range. E1 closest at 472px. Move to engage.	attack_move	E1
1	0	1	RANGER-beta	llm	Turn 0: Hold post at ranger line. Enemy E4 closest but >250px away. Aw	hold	hold
1	0	2	BLADE-alpha	scripted	focus fire	focus	E2
1	0	3	BLADE-beta	scripted	charge	attack_move	go
1	0	4	BLADE-gamma	scripted	charge	attack_move	go
1	1	0	RANGER-alpha	llm	E1 lowest hp (12), 3 focused already. E2 closest threat at 15px. Kite 	kite	E1
1	1	1	RANGER-beta	llm	E5 closest at 334px, in range. HP 60/60. Focus fire E5 with squad.	focus	E5
1	1	2	BLADE-alpha	scripted	focus fire	screen	screen
```
Middle:
```
2	6	4	BLADE-gamma	scripted	charge	attack_move	go
2	7	0	RANGER-alpha	llm	RANGER-alpha is dead. Cannot act.	hold	dead
2	7	1	RANGER-beta	llm	CRITICAL: 10hp remaining, I am one swing from death. E4 nearest at 12h	retreat	FALL BACK
2	7	2	BLADE-alpha	scripted	focus fire	focus	E4
2	7	3	BLADE-beta	scripted	charge	attack_move	go
2	7	4	BLADE-gamma	scripted	charge	attack_move	go
2	8	0	RANGER-alpha	llm	I am dead. Cannot act this turn.	hold	
2	8	1	RANGER-beta	llm	10hp, one swing from death. E4 at 12hp nearest (304px). Retreat to saf	retreat	retreat
```
Late:
```
3	5	2	BLADE-alpha	scripted	focus fire	screen	screen
3	5	3	BLADE-beta	scripted	charge	attack_move	go
3	5	4	BLADE-gamma	scripted	charge	attack_move	go
3	6	0	RANGER-alpha	llm	E4 blade 4hp, 72px away, in range. One more shot finishes it. Focus an	focus	E4
3	6	1	RANGER-beta	llm	DEAD - no action possible	hold	
3	6	2	BLADE-alpha	scripted	focus fire	screen	screen
3	6	3	BLADE-beta	scripted	charge	attack_move	go
3	6	4	BLADE-gamma	scripted	charge	attack_move	go
```
```
$ jq -c '.results' /tmp/ep.json
… "battleResults":["victory","full_time","victory"],"battleTicks":[462,1440,721],
   "battlesWon":2,"enemyKilled":5,"enemyTotal":5,"reason":"complete","endRule":"victory",
   "games":3,"finalTick":3232 …
```

### Spectator-judgment paragraph

**It is legible, it advances, and it shows the game.** `viewer-smoke.png` (this run's artifact,
1280×800, downloaded from run 33067338841 — described, not imagined) is a top-down grey arena with
a tiled floor, scattered cover blocks and two glowing team crests at either end. Ten unit sprites
are clustered in a melee just left of centre with a large red damage/blood spray over them, tracer
lines drawn from two shooters, and small speech labels floating above individual cogs — `go` and `hold` are
legible at this resolution, plus short enemy-tag labels — which are the `say` fields from the
directive stream above rendered in-world. The top strip
carries the scorebug: `daveey 4 DMG 0k`, `daveey-1 0 DMG 0k`, `Baseline 20 DMG 0k` on the left,
two more `Baseline (…)` rows on the right, and a centred clock reading
`0:29 · BATTLE 2/3 · DEFAULT · 5 V 5 · TURN 7/12`. Below it the `OURS` / `THEIRS` army-HP bars read
`5 UP · 480/480 (100%)` and `5 UP · 436/480 (91%)` — a spectator can tell at a glance who is
winning and by how much. Bottom right the killfeed shows `BLADE-gamma: charge`. Bottom left is the
transport strip — restart, step-back, play, `+5s`, step-forward, loop, fast-forward, a `spoilers`
toggle, a `RED WINS / 735 / 3007` tick counter — and speed buttons `1×/2×/3×/4×/8×/16×`, with the
`ARMY HP LEAD` momentum graph and playhead running the full width beneath. Nothing is empty,
frozen or unreadable: `loaded: true` at 3310 ms, `data_replay_loaded: "true"`, no `failure`, no
console errors, `loading_text: null`, and the three scrub readouts move across two different
battles and four different turns, so it is a replay and not a screenshot. Reconciled against the
record, the picture and the JSON agree: the replay says three battles ending
`victory / full_time / victory` at ticks 462 / 1440 / 721 with `finalTick: 3232`, and the shell's
counter (`735 / 3007`) and `BATTLE 2/3` are consistent with a mid-episode frame; the early events
show rangers opening at range (`attack_move`, `hold`) while blades `charge`/`focus`, which is
exactly the shape of the melee on screen. **The chrome is the starter's** — the same transport
strip, scrubber with momentum graph, per-player scorebug and endcard family as paintbot/raid/hive,
retextured for a StarCraft-micro arena rather than rewritten; this is not the cogame-gridlock
failure mode. The one legibility nit: the 100 % scrub lands mid-battle-2 rather than on the endcard,
so the endcard is not exercised by this probe — worth a phase-30 look, but not a defect in what was
rendered.

**Status: TRUE** — `loaded: true` **and** the three clock readouts differ.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — 5 completed (r2–r6); r1 failed (Temporal race), excluded |
| 2 | Both champions ranked, fillers absent | **TRUE** — daveey-1 1018.43 / daveey 981.57, 5 rounds each |
| 3 | Latest round's ereq completed with replay | **TRUE** — `ereq_805f41dc…` completed, S3 replay, both champions named |
| 4 | Replay bytes valid and show the game | **TRUE** — protocol ok, reason `complete`, enemyKilled 5/5, 46/46 champion directives `llm`, 0 fallbacks |
| 5 | Hosted game log clean | **TRUE** — 0 matches (was FALSE in pass 1; fixed in 0.1.3) |
| 6 | Public page uses the static replay path | **TRUE** — SSR featured match r6/0.1.3 + static iframe `src` with the 0.1.3 sha |
| 7 | Certification declared the static bundle | **TRUE** — committed `release-result.json`, `Replay liveness: skipped (static replay bundle declared…` |
| 8 | Viewer executed and judged | **TRUE** — run 33067338841, `loaded:true` @3310 ms, three differing clocks, starter chrome |

Notes carried forward for the coordinator (none blocking):
- `feed_lines: 0` is a **harness selector gap** (`#feed, .feed, #log` vs this lineage's `#killfeed`),
  not a missing feed — the screenshot shows the killfeed rendering.
- The 0.1.3 repair line says "kept last turn's directive **on turn 0**", where no previous turn
  exists; harmless here (0 fallbacks) but worth a phase-30 look.
- The 100 % scrub position lands mid-episode, so the endcard is never exercised by the probe.
- `participant_scores` are near-identical across seats (shared team score); ladder separation comes
  from episode outcomes.
