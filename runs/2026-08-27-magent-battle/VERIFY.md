# VERIFY — magent-battle   (2026-08-27T10:31Z)

Verdict: **all-true** (8 of 8 TRUE)

Run: `2026-08-27-magent-battle` · coworld `magent-battle` v`0.1.2` ·
`cow_a5961275-14d8-4489-83c9-73bbe5f69767` ·
league `league_b56ff3be-1f0f-4b2a-b2e7-c44d17839134` ·
division `div_ea7bd527-bc20-4698-b780-14c643a6067b`.

All calls in this file were made **fresh during phase 60** (2026-08-27T10:08Z–10:31Z), with the
two documented exceptions the prompt allows: **check 7** reads the committed
`runs/2026-08-27-magent-battle/release-result.json` (phase 40's artifact, not a live endpoint) and
**check 8** reads the artifact of the `viewer-check.yml` run *this phase dispatched*
(`33063093381`, created 2026-08-27T10:27:11Z).

Headers sent on every Observatory call: `Authorization: Bearer $SOFTMAX_TOKEN` and
`User-Agent: coworld-builder/1.0`; on the artifacts/logs call additionally
`X-Use-Elevated-Privileges: true`. **No header value is printed anywhere in this file.**

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_b56ff3be-1f0f-4b2a-b2e7-c44d17839134
D=div_ea7bd527-bc20-4698-b780-14c643a6067b
COW=cow_a5961275-14d8-4489-83c9-73bbe5f69767
```

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

Fillers (`magent-battle-line:v3` `a3fc517c-…`, `magent-battle-pincer:v3` `7b36eb1b-…`) were
registered at **2026-08-27T10:07:44Z**, *before the first trigger-round*
(`log.md`: `2026-08-27T10:07:44Z 50 fillers registered 200: line:v3 a3fc517c + pincer:v3 7b36eb1b
(neither champion); unpause 200 …; trigger-round 200; round 1 pending`). Round 1 (`created_at`
10:06:01Z) is therefore itself a post-filler round, and rounds 1 and 2 both count.

Poll log (every ~5 min, inside the 75-minute bound; bound would have expired 11:23Z):

| poll | UTC | completed rounds |
|---|---|---|
| 1 | 10:08:48Z | 0 (round 1 `pending`) |
| 2 | 10:14:42Z | 1 (round 1 `completed`) |
| 3 | 10:19:57Z | 1 (round 2 not yet created) |
| 4 | 10:24:59Z | **2** (rounds 1 and 2 `completed`) |

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq '(.entries // .) | map({id,round_number,status,error,created_at,completed_at,
        entrants:(.round_config.entrant_attributions//null)})'
```
(the route returned the `{"entries": …}` shape this run; the `(.entries // .)` guard covers the
bare-array shape the playbook warns about)

```json
[
  {
    "id": "round_4060358e-c282-4935-a3ed-5f3aef80a482",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-27T10:21:02.273904Z",
    "completed_at": "2026-08-27T10:24:29.524022Z",
    "entrants": [
      {
        "subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
        "subject_type": "player",
        "policy_version_id": "337729f2-5b87-48c3-ae81-1c95bb6d0e66",
        "league_policy_membership_id": "lpm_5f4c3a9d-2d24-470a-8af0-034d16396ce7"
      },
      {
        "subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
        "subject_type": "player",
        "policy_version_id": "361a18b7-1ca2-43a7-a680-a6307e7fa550",
        "league_policy_membership_id": "lpm_797170fb-09ff-46c9-bcd9-0819a848169c"
      }
    ]
  },
  {
    "id": "round_0834898f-2fa4-4824-aa0a-4bd8b751c789",
    "round_number": 1,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-27T10:06:01.483432Z",
    "completed_at": "2026-08-27T10:09:19.029912Z",
    "entrants": [
      {
        "subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
        "subject_type": "player",
        "policy_version_id": "337729f2-5b87-48c3-ae81-1c95bb6d0e66",
        "league_policy_membership_id": "lpm_5f4c3a9d-2d24-470a-8af0-034d16396ce7"
      },
      {
        "subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
        "subject_type": "player",
        "policy_version_id": "361a18b7-1ca2-43a7-a680-a6307e7fa550",
        "league_policy_membership_id": "lpm_797170fb-09ff-46c9-bcd9-0819a848169c"
      }
    ]
  }
]
```

```bash
jq -r '[(.entries // .)[]|select(.status=="completed")]|length'
```
```
2
```

Status: **TRUE** — 2 completed rounds (`round_number` 1 and 2; ids `round_0834898f-…` and
`round_4060358e-…`), completed 10:09:19Z and 10:24:29Z, both after fillers were set at 10:07:44Z.
No `failed` or `discarded` round exists in the league (the list above is the whole list of 2), and
`error` is `null` on both.

---

## 2. Both champions ranked; fillers absent — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey	magent-battle-vanguard:v3	1030.5304984710244	2	2.0
2	daveey-1	magent-battle-marshal:v3	969.4695015289755	2	0.0
```

Full body (bare JSON list, not `.entries`):

```json
[
  {
    "rank": 1,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 1030.5304984710244,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 2.0,
    "episodes_played": null,
    "win_rate": 1.0,
    "policy_label": "magent-battle-vanguard:v3",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 969.4695015289755,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 0.0,
    "episodes_played": null,
    "win_rate": 0.0,
    "policy_label": "magent-battle-marshal:v3",
    "recent_rounds": null
  }
]
```

Status: **TRUE** — `daveey` (`magent-battle-vanguard:v3`, rank 1, `rounds_played` 2) **and**
`daveey-1` (`magent-battle-marshal:v3`, rank 2, `rounds_played` 2) are both ranked, each with
`rounds_played ≥ 1`. The two fillers (`magent-battle-line:v3`, `magent-battle-pincer:v3`) are
**absent** from the leaderboard — there is no third row, so nothing needed the `Baseline` label.
Elo is exactly symmetric about the 1000 seed (1030.53 / 969.47), consistent with the zero-sum
scoring the design note declares.

---

## 3. Latest round's episode request completed with a replay — **TRUE**

Latest completed round = `round_4060358e-c282-4935-a3ed-5f3aef80a482` (`round_number` 2).

The flat route documented in `60-verify.md` no longer accepts GET; I recorded the exact response
and used the nested route the playbook prescribes (§9):

```bash
curl -sS -o /tmp/flat.txt -w '%{http_code}\n' "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}"
```
```
405
{"detail":"Method Not Allowed"}
```

```bash
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" | jq -c '(.entries // .)|map({id,status,replay_url})'
```
```json
[{"id":"ereq_3cc278d1-f7bb-4bea-a1f3-0abe9fcb9754","status":"completed","replay_url":"https://softmax-public.s3.amazonaws.com/replays/473bdd5e-3691-4411-a3c7-ce4376276e04.replay"}]
```

```bash
EREQ=ereq_3cc278d1-f7bb-4bea-a1f3-0abe9fcb9754
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/473bdd5e-3691-4411-a3c7-ce4376276e04.replay",
  "participants": [
    {
      "position": 0,
      "kind": "policy",
      "policy_version_id": "337729f2-5b87-48c3-ae81-1c95bb6d0e66",
      "policy_id": "ce0df58c-4deb-4ca0-93a4-ae42c57b6679",
      "policy_name": "magent-battle-vanguard",
      "version": 3,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": false,
      "is_seed": false
    },
    {
      "position": 1,
      "kind": "policy",
      "policy_version_id": "361a18b7-1ca2-43a7-a680-a6307e7fa550",
      "policy_id": "823a5706-bc8b-47f3-a239-6b92d1ed338c",
      "policy_name": "magent-battle-marshal",
      "version": 3,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
      "player_name": "daveey-1",
      "is_filler": false,
      "is_seed": false
    }
  ],
  "participant_scores": [
    {
      "position": 0,
      "score": 24.0
    },
    {
      "position": 1,
      "score": -24.0
    }
  ]
}
```

Status: **TRUE** — `status == "completed"`, non-null `replay_url`, participants name `daveey`
(seat 0, `magent-battle-vanguard` v3, `is_filler:false`) and `daveey-1` (seat 1,
`magent-battle-marshal` v3, `is_filler:false`); no filler seats were needed, so no
`Baseline (N)` rows. Scores are exactly zero-sum (+24 / −24), as the design note requires.

---

## 4. Replay bytes are valid and show the game — **TRUE**

**Which path I took: the documented COWLDMAG → JSON-view path.** The raw artifact is this game's
binary replay format (magic `COWLDMAG`), which the design note declares and provides for
(`design.md` §"The phase-60 substitute for SPEC §Definition of done check 4", lines 798–808), so
`jq -e .` on the raw bytes fails by design and the strict-UTF-8 parse is performed on
`tools/replay_summary.py`'s output. **Both** steps are shown.

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/473bdd5e-3691-4411-a3c7-ce4376276e04.replay" -o /tmp/ep.replay
ls -l /tmp/ep.replay ; od -c -N16 /tmp/ep.replay
```
```
-rw-r--r-- 1 root root 81991 Aug 27 10:25 /tmp/ep.replay
0000000   C   O   W   L   D   M   A   G 001  \0  \r  \0  \0  \0   m   a
```
(81 991 bytes — byte-for-byte the size the hosted game container reported writing:
`Replay written: /coworld/replay (81991 bytes)`, see check 5)

```bash
jq -e . /tmp/ep.replay >/dev/null ; echo "exit=$?"
```
```
exit=5
jq: parse error: Invalid numeric literal at line 1, column 11
```
→ expected: these are the declared binary bytes, not JSON.

```bash
python3 /workspace/cogame-magent-battle/tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
python3 -c "d=open('/tmp/ep.json','rb').read(); s=d.decode('utf-8',errors='strict'); import json; json.loads(s); print('strict utf-8 + json.loads ok, bytes=',len(d))"
```
```
strict UTF-8 JSON: ok
strict utf-8 + json.loads ok, bytes= 22588
```
(two independent strict parsers — `jq -e` and python's `bytes.decode('utf-8', errors='strict')`
followed by `json.loads` — both accept it; no lone surrogates, no invalid UTF-8)

```bash
jq -c '{protocol,game,gameVersion,seed,mapSize,names,aliases,policyKinds,games,tickCount,orderRecords,fallbacks}' /tmp/ep.json
```
```json
{"protocol":"magent-battle/v1","game":"magent-battle","gameVersion":"1","seed":1490114859,"mapSize":45,"names":["daveey","daveey-1"],"aliases":["Alpha","Bravo"],"policyKinds":["llm","llm"],"games":2,"tickCount":567,"orderRecords":32,"fallbacks":0}
```

**Protocol match.** `protocol == "magent-battle/v1"`, which is exactly the game's declared
protocol id — `src/magent/sim_types.nim:19: ProtocolId* = "magent-battle/v1"`, written into the
replay config by `src/magent/sim_config.nim:153: "protocol": ProtocolId` — and exactly what
`design.md:806` requires phase 60 to see. The manifest
(`coworld_manifest_template.json`) carries no protocol-**id** string of its own; it declares
`protocols.player` / `protocols.global` as URIs to `docs/PROTOCOL.md`, and `game.name` =
`"magent-battle"`, which the replay's `game` field matches verbatim. Recorded exactly so, rather
than claimed as a literal string equality with a manifest field that does not exist.

```bash
jq -r '.protocol, .results.reason' /tmp/ep.json
jq -r '[.directives[]]|length' /tmp/ep.json          # per-turn commander decisions
jq -r '[.directives[]|select(.source=="llm")]|length' /tmp/ep.json
jq -r '.fallbacks' /tmp/ep.json
```
```
magent-battle/v1
complete
32
32
0
```

Decision / fallback accounting — the prompt's `select(.type=="decision")` /
`select(.fallback==true)` filters name this format's `directives[]` records and the writer's
`fallback` chat records, which `replay_summary.py` surfaces as `.directives[]` and the `.fallbacks`
counter respectively: **32 decisions, 32 of them `source == "llm"`, 0 fallbacks (0 %)** —
not "a small minority", but none at all. Cross-checked against the results document's own
counters below: `llmTurns: [16,16]`, `fallbackTurns: [0,0]`, `ordersRejected: [0,0]`.

```bash
jq '.results' /tmp/ep.json
```
```json
{
  "names": ["daveey", "daveey-1"],
  "aliases": ["Alpha", "Bravo"],
  "scores": [24, -24],
  "win": [true, false],
  "winner": 0,
  "reason": "complete",
  "games": 2,
  "gameWins": [1, 1],
  "survivors": [30, 6],
  "kills": [156, 132],
  "finalTick": 194,
  "turnsPlayed": 16,
  "seed": 1490114859,
  "magentReward": ["793.56", "676.34"],
  "policyKinds": ["llm", "llm"],
  "llmTurns": [16, 16],
  "fallbackTurns": [0, 0],
  "ordersRejected": [0, 0],
  "deadSeats": [false, false],
  "gameResults": [
    {"game": 1, "redSlot": 0, "survivors": [0, 6], "kills": [75, 81], "ticks": 109, "endRule": "wipe"},
    {"game": 2, "redSlot": 1, "survivors": [30, 0], "kills": [81, 51], "ticks": 194, "endRule": "wipe"}
  ],
  "stopDetail": ""
}
```

A champion seat's decision, in full — non-scripted, non-trivial, nine squad orders and a line of
commentary:

```bash
jq '.directives[0]' /tmp/ep.json
```
```json
{
  "game": 1, "turn": 1, "slot": 0, "alias": "Alpha", "side": "red",
  "source": "llm", "latency_ms": 5381,
  "say": "Left flank mass forming. Screens and reserve positioned.",
  "orders": [
    {"squad": "A1", "verb": "flank", "arg": "left"},
    {"squad": "A2", "verb": "flank", "arg": "left"},
    {"squad": "A3", "verb": "flank", "arg": "left"},
    {"squad": "A4", "verb": "flank", "arg": "left"},
    {"squad": "A5", "verb": "flank", "arg": "left"},
    {"squad": "A6", "verb": "flank", "arg": "left"},
    {"squad": "A7", "verb": "hold", "arg": "22,21"},
    {"squad": "A8", "verb": "hold", "arg": "22,21"},
    {"squad": "A9", "verb": "hold", "arg": "22,10"}
  ]
}
```

Status: **TRUE** — strict-UTF-8 JSON under two strict parsers via the design-declared JSON view;
`protocol == "magent-battle/v1"` as the game declares; `results.reason == "complete"` (no
`deadline` exception needed); both games ended `wipe` with kills non-zero on both sides
(156 / 132); every one of the 32 champion decisions came from the LLM with real verbs
(`flank`/`hold`/`focus`/`retreat`) and non-empty `say`; **zero fallbacks**.

---

## 5. Hosted game log is clean — **TRUE**

```bash
curl -sS -w '\nHTTP %{http_code} bytes=%{size_download}\n' \
  "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs.raw
```
```
HTTP 200 bytes=67525
```

The body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it was
**decoded before grepping** (playbook §10 — a line-based grep on the reprs undercounts):

```bash
python3 - <<'PY'   # ast.literal_eval each b'…' repr, per container
… decode …
PY
# container coworld-init-config      reprs=1
# container bedrock-sidecar          reprs=1
# container game                     reprs=1
# container worker                   reprs=1
# decoded chars=67362 lines=155
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.txt || echo CLEAN
```
```
CLEAN
```
```bash
grep -ncE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.txt   # decoded
grep -ncE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.raw   # raw, cross-check
```
```
0
0
```

Every Bedrock call in the episode succeeded — no throttling, no 429, so the platform-wide
capacity exception (the 2026-08-24-coins `Too many tokens per day` case) was **not** needed and no
sibling-run cross-check was required:

```bash
grep -o '"ok":[a-z]*,"status_code":[0-9]*' /tmp/logs.txt | sort | uniq -c
```
```
     32 "ok":true,"status_code":200
```

Decoded `bedrock-sidecar` head:

```
2026-08-27 10:21:36,330 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1","has_role_arn":true,"schema_version":"1", … "episode_request_id":"3cc278d1-f7…
[2026-08-27 10:21:36 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-08-27 10:21:44,782 INFO __main__ bedrock_sidecar_call {…,"episode_request_id":"3cc278d1-f7bb-4bea-a1f3-0abe9fcb9754","job_request_id":"473bdd5e-3691-4411…
2026-08-27 10:21:47,132 INFO httpx HTTP Request: POST https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke "HTTP/1.1 200 OK"
2026-08-27 10:21:47,133 INFO __main__ bedrock_sidecar_complete {…,"model":"global.anthropic.claude-haiku-4-5-20251001-v1:0","operation":"InvokeModel","ok":true,"status_code":200,"latency_ms":2464.45…,"error_kind":null,"error_type":null,"message":null,"cache_strategy":"sidecar_v1","cache_decision":"first_sighting"…}
```

Decoded `game` container, in full:

```
magent llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
magent-battle listening on 0.0.0.0:8080 mapSize=45 seats=2 army=81 v 81
player connected: slot 0
seat 0 registered: kind=llm baseline=pincer
player connected: slot 1
seat 1 registered: kind=llm baseline=pincer
game 1 of 2 starts: seat 0 is red
Dropped message to disconnected client
game 1 of 2 done: wipe survivors 0 v 6
game 2 starts: seat 1 is red
game 2 of 2 done: wipe survivors 30 v 0
Replay written: /coworld/replay (81991 bytes)
Events written: /coworld/events.json (2186 events)
results: {"names":["daveey","daveey-1"],…,"reason":"complete",…,"kills":[156,132],…}
labels: 36 in the manifest vocabulary
```

Status: **TRUE** — zero matches for `falling back`, `LLM provider is unavailable`,
`cut off at max_tokens` and `rejected` in 67 362 decoded characters across all four containers
(decoded and raw greps agree at 0); 32/32 Bedrock invocations `ok:true` / HTTP 200. The one
non-obvious line, `Dropped message to disconnected client`, is benign and matches none of the
four patterns: it is the inter-game socket churn at the game-1→game-2 side swap, and both seats
are recorded `deadSeats: [false,false]` with `llmTurns: [16,16]` afterwards.

---

## 6. The public page uses the static replay path — **TRUE**

**Which source I used: both, and I record what each returned.**

*(a) The raw-HTML iframe grep — finds nothing (the page is client-rendered for the iframe, as the
playbook's lighthouse-run note records), so this is `unknown`, not a false negative:*
```bash
curl -sS "https://softmax.com/magent-battle" -o /tmp/page.html -w 'HTTP %{http_code} bytes=%{size_download}\n'
grep -o '<iframe[^>]*src="[^"]*"' /tmp/page.html || echo "(no match)"
grep -o -i '<iframe' /tmp/page.html | head || echo "(no iframe tag at all)"
```
```
HTTP 200 bytes=671044
(no match)
(no iframe tag at all)
```

*(b) The featured match — server-rendered into the page's SSR payload at `state.playlist[0]`
(unescaped from the JS string in the fetched HTML):*
```json
"playlist":[{"episodeId":"47d78f4e-2d13-49f8-8d82-593a8a38ed66",
 "coworldId":"cow_a5961275-14d8-4489-83c9-73bbe5f69767","coworldName":"magent-battle",
 "coworldVersion":"0.1.2",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/473bdd5e-3691-4411-a3c7-ce4376276e04.replay",
 "finishedAt":"2026-08-27T10:24:19.458014Z","roundNumber":2,"episodeNumber":1,
 "code":"magent-battle.r2.e1",
 "matchup":{"divisionId":"div_ea7bd527-bc20-4698-b780-14c643a6067b","divisionName":"Competition",
  "first":{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
           "score":1030.5304984710244,"rounds_played":2,"episode_wins":2,"win_rate":1,
           "policy_label":"magent-battle-vanguard:v3"},
  "second":{"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
            "score":969.4695015289755,"rounds_played":2,"episode_wins":0,"win_rate":0,
            "policy_label":"magent-battle-marshal:v3"}},
 "inspectUrl":"/observatory/v2?tab=overview&detail=episode-request:ereq_3cc278d1-f7bb-4bea-a1f3-0abe9fcb9754",
 "outcome":"first"}]
```
A featured match **is present**: `magent-battle.r2.e1`, both ranked champions in the matchup, and
its `replayUrl` is byte-identical to the replay verified in check 4.

*(c) The coworld detail API (the fallback `60-verify.md` names) — returns a **bare array** here, and
`replay_viewer`/`featured_match` are `null`, which the playbook records as platform-wide and
therefore not evidence either way:*
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end | .[]|select(.name=="magent-battle")|{id,name,version,canonical,replay_viewer,featured_match}'
```
```json
{"id":"cow_a5961275-14d8-4489-83c9-73bbe5f69767","name":"magent-battle","version":"0.1.2","canonical":true,"replay_viewer":null,"featured_match":null}
{"id":"cow_07d7ba38-8a2a-4b13-83b8-cf250f519eb6","name":"magent-battle","version":"0.1.1","canonical":false,"replay_viewer":null,"featured_match":null}
{"id":"cow_3918bf09-0239-404f-82a7-d8c382e2912c","name":"magent-battle","version":"0.1.0","canonical":false,"replay_viewer":null,"featured_match":null}
```
(v0.1.2 is the sole canonical coworld.)

*(d) The iframe `src` itself — the call the page's own JS makes (playbook §Featured match / replay
route). This is a viewer-session read; it touches no coworld, league, round or policy:*
```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_a5961275-14d8-4489-83c9-73bbe5f69767",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/473bdd5e-3691-4411-a3c7-ce4376276e04.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_a5961275-14d8-4489-83c9-73bbe5f69767/sha256%3A9f7e22e4d2d07efbb5d0373e600a7c32b5c8cd13b29fe9253dc33e9f968ca9dc/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F473bdd5e-3691-4411-a3c7-ce4376276e04.replay&v=2",
  "ready": true
}
```

Status: **TRUE** — the path is
`/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`, with
`<cow_id>` = `cow_a5961275-14d8-4489-83c9-73bbe5f69767` (STATE's cow id) and `<sha>` =
`sha256:9f7e22e4d2d07efbb5d0373e600a7c32b5c8cd13b29fe9253dc33e9f968ca9dc` URL-encoded — identical
to `STATE.coworld.manifest_sha`. `ready: true`. **No `/client/replay` pod URL anywhere**, and a
featured match is present.

---

## 7. Certification declared the static bundle — **TRUE**

**Source: the committed `runs/2026-08-27-magent-battle/release-result.json`** (phase 40's
downloaded artifact of release run `33060644278`, committed in `0210c30`). It was present, so no
re-download from `gh run download` was needed and `/tmp` was never consulted.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-27-magent-battle/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Surrounding fields from the same committed file, for provenance:

```bash
jq '{version,cow_id,canonical,manifest_sha,ok,step_failed,hosted_smoke,secret_put,certify:{ok:.certify.ok,replay_liveness:.certify.replay_liveness}}' runs/2026-08-27-magent-battle/release-result.json
```
```json
{
  "version": "0.1.2",
  "cow_id": "cow_a5961275-14d8-4489-83c9-73bbe5f69767",
  "canonical": true,
  "manifest_sha": "sha256:9f7e22e4d2d07efbb5d0373e600a7c32b5c8cd13b29fe9253dc33e9f968ca9dc",
  "ok": true,
  "step_failed": null,
  "hosted_smoke": "passed",
  "secret_put": true,
  "certify": {
    "ok": true,
    "replay_liveness": "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"
  }
}
```

Status: **TRUE** — contains `Replay liveness: skipped (static replay bundle declared`, on the same
`cow_id` and `manifest_sha` that check 6's static iframe `src` embeds.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

*(a) Dispatched against the exact iframe `src` from check 6.*

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_a5961275-14d8-4489-83c9-73bbe5f69767/sha256%3A9f7e22e4d2d07efbb5d0373e600a7c32b5c8cd13b29fe9253dc33e9f968ca9dc/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F473bdd5e-3691-4411-a3c7-ce4376276e04.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90   # dispatched 10:27:09Z
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[]|[.databaseId,.createdAt,.status]|@tsv'
```
```
33063093381	2026-08-27T10:27:11Z	in_progress     <- mine (created after the 10:27:09Z dispatch)
33062642745	2026-08-27T10:21:00Z	completed       <- another run in flight; NOT taken
33042374554	2026-08-27T05:24:05Z	completed
…
```
Run selected by `createdAt` sort, not by "the latest run": **`33063093381`**.

```bash
gh run watch 33063093381 -R Metta-AI/coworld-builder --exit-status
gh run view 33063093381 -R Metta-AI/coworld-builder --json status,conclusion,createdAt,updatedAt
```
```
✓ viewer-check in 35s (ID 98486459362)
  ✓ Load the viewer   ✓ Summary   ✓ Upload the evidence   ✓ Fail if the viewer did not load
{"conclusion":"success","status":"completed","createdAt":"2026-08-27T10:27:11Z","updatedAt":"2026-08-27T10:27:50Z"}
```

```bash
gh run download 33063093381 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-27-magent-battle/viewer-check
```
```
-rw-r--r-- 1 root root      0 Aug 27 10:28 smoke-stderr.txt
-rw-r--r-- 1 root root    616 Aug 27 10:28 smoke-stdout.txt
-rw-r--r-- 1 root root   1418 Aug 27 10:28 viewer-smoke.json
-rw-r--r-- 1 root root 199379 Aug 27 10:28 viewer-smoke.png
```
Committed with this file at `runs/2026-08-27-magent-battle/viewer-check/`.

*(b) The readouts, verbatim.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-27-magent-battle/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":4204,"clock":"game 1/2 · turn 1/15 TICK 0/300 · 81 V 81","scorebug":"RED DAVEEY ALPHA ALIVE 81 0 game 1/2 · turn 1/15 TICK 0/300 · 81 V 81 BLUE DAVEEY-1 BRAVO ALIVE 81 0","feed_lines":0}
```

```bash
jq -c '.signals' runs/2026-08-27-magent-battle/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-27-magent-battle/viewer-check/viewer-smoke.json
```

| scrub position | `#clock` readout |
|---|---|
| 0 % | `game 1/2 · turn 1/15 TICK 0/300 · 81 V 81` |
| 50 % | `game 2/2 · turn 3/15 TICK 49/300 · 43 V 32` |
| 100 % | `game 2/2 · turn 10/15 TICK 194/300 · 30 V 0` |

Three readouts, all three **different** — game index, turn, tick and both alive counts all
advance. A `#scrub` element was present (the json emits `"(no #scrub in this shell)"` when it is
not; it did not).

```bash
jq -r '.failure // "no failure"' runs/2026-08-27-magent-battle/viewer-check/viewer-smoke.json
jq -c '.status, .loading_text, .console_tail, .canvas_text' runs/2026-08-27-magent-battle/viewer-check/viewer-smoke.json
```
```
no failure
"CONNECTING"
null
[]
{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
```
`smoke-stderr.txt` is 0 bytes; `console_tail` is empty (no page errors, no HTTP ≥400 on any asset).
Note on `status:"CONNECTING"` and `feed_lines:0`: per
`templates/tools/ci/viewer_smoke.mjs` these come from the **load-time** readout (taken the moment
the frame is drawn, before the scrub — the `clock` in the same object is `TICK 0/300`, i.e. the
lobby frame), whereas the screenshot is taken **after** the 0 %/50 %/100 % scrub. So they describe
the first frame, not the end state; the screenshot below and the scrub table describe the rest.

*(c) What the viewer was asked to draw — ordered excerpts of the same replay (check 4's
`/tmp/ep.json`; this format's per-turn records are `.directives[]`, the JSON view of the replay's
chat records):*

```bash
jq -r '.directives[0:8][]|[.game,.turn,.slot,.alias,.source,.latency_ms,(.say[0:70]),
       ([.orders[]|"\(.squad):\(.verb) \(.arg)"]|join(" "))]|@tsv' /tmp/ep.json
```
```
1  1  0  Alpha  llm  5381  Left flank mass forming. Screens and reserve positioned.        A1:flank left A2:flank left A3:flank left A4:flank left A5:flank left A6:flank left A7:hold 22,21 A8:hold 22,21 A9:hold 22,10
1  1  1  Bravo  llm  5381  Holding defensive line 22 cells from our edge. Let enemy cross  B1:hold 22,8 B2:hold 22,13 B3:hold 22,18 B4:hold 22,23 B5:hold 22,28 B6:hold 22,33 B7:hold 22,38 B8:hold 22,12 B9:hold 22,30
1  2  0  Alpha  llm  3692  Mass engaging B5 with 5-squad focus. A6 retreat to heal. Screen A1:focus B5 A2:focus B5 A3:focus B5 A4:focus B5 A5:focus B5 A6:retreat A7:hold 20,5 A8:hold 20,5 A9:hold 20,10
1  2  1  Bravo  llm  3692  Engaging enemy clusters. B3/B4 focus A1 (weakest visible mass)  B1:hold 22,8 B2:hold 22,13 B3:focus A1 B4:focus A1 B5:focus A6 B6:hold 22,33 B7:hold 22,38 B8:hold 22,12 B9:hold 22,30
1  3  0  Alpha  llm  2907  Concentrate fire on B5 (critically wounded, 2.1 hp). All six    A1:focus B5 … A6:focus B5 A7:hold 19,7 A8:hold 20,5 A9:hold 20,10
1  3  1  Bravo  llm  2907  Retreating B4/B5 to heal. B6 focuses weakest enemy A6. Holding  B1:hold 22,8 B2:hold 22,12 B3:focus A1 B4:retreat B5:retreat B6:focus A6 B7:hold 22,37 B8:hold 22,12 B9:hold 22,29
1  4  0  Alpha  llm  6534  Mass pivoting to B1 (8 seen, 9.6 hp). A2 healing after damage   A1:focus B5 A2:retreat A3:focus B1 A4:focus B1 A5:focus B1 A6:focus B5 A7:hold 20,7 A8:hold 20,5 A9:hold 20,10
1  4  1  Bravo  llm  6534  B9 critical, retreating. B1/B7 focus A5 (weakest visible)       B1:focus A5 B2:hold 22,12 B3:focus A1 B4:retreat B5:retreat B6:focus A6 B7:focus A5 B8:hold 22,12 B9:retreat
```

```bash
jq -r '.directives[12:20][]|[.game,.turn,.slot,.alias,.source,.latency_ms,(.say[0:70])]|@tsv' /tmp/ep.json   # middle
```
```
2  1  0  Alpha  llm  5170  A2 continuing focus on B7. Outnumbered but fighting on.
2  1  1  Bravo  llm  5170  Defensive line established. B1 and B9 retreating to heal. Holding stro
2  2  0  Alpha  llm  3389  Game 2 lost. Regrouping survivors to heal before final engagement.
2  2  1  Bravo  llm  3389  All squads below 5.5 hp retreating to heal. Defending line holding at
2  3  0  Alpha  llm  3652  Consolidate on B1 with all combat squads. A1 screens center.
2  3  1  Bravo  llm  3652  Retreating damaged squads to heal. B5 focuses A2 with full strength. R
2  4  0  Alpha  llm  3534  Mass focused on B1. A1 screens center. Concentration doctrine.
2  4  1  Bravo  llm  3534  Holding line, rotating damaged squads to rear for healing. Enemy conce
```

```bash
jq -r '.directives[-6:][]|[.game,.turn,.slot,.alias,.source,.latency_ms,(.say[0:70])]|@tsv' /tmp/ep.json   # late
jq -c '.gameStarts, .stops' /tmp/ep.json
```
```
2  8   0  Alpha  llm  5308  Maintaining concentrated focus on B9 until elimination. A1 holds defen
2  8   1  Bravo  llm  5308  B1/B9 healing. B2/B6 hold line. Awaiting numeric advantage to push.
2  9   0  Alpha  llm  2631  Seven squads focus B9 for kill. A1 screens.
2  9   1  Bravo  llm  2631  B1 and B9 above 8.0 hp, returning to hold. Maintaining defensive line
2  10  0  Alpha  llm  5116  Mass pivots to B1 after eliminating B9. Screen holds. Concentration do
2  10  1  Bravo  llm  5116  Focusing B2 and B6 on weakest enemy A5 (9.1 hp). B1 and B9 still heali
[{"tick":204,"game":1,"redSlot":0},{"tick":343,"game":2,"redSlot":1}]
[]
```
`.results` for the same episode is pasted in full under check 4 (`reason: "complete"`, two `wipe`
games, survivors 30 v 6, kills 156 v 132, scores +24 / −24).

**Item 8 verdict: TRUE** — `loaded: true` (`data_replay_loaded: "true"`, first frame at 4 204 ms)
**and** the three clock readouts differ.

### Spectator judgment

The picture is neither empty nor frozen, and it is legible. `viewer-smoke.png` (1280×800, taken
after the 100 % seek) shows the **endcard over the finished battle**: a headline in the chrome's
display face — `ALPHA TAKES THE PAIR 1-1 — 30 SURVIVORS TO 6` — a boxed `SCORE +24 / -24` chip,
and a one-line ledger `game 1: 0-6 (wipe, 109 ticks) · game 2: 30-0 (wipe, 194 ticks) · complete`.
Every one of those numbers matches the replay's `results` byte for byte (`gameWins [1,1]`,
`survivors [30,6]`, `scores [24,-24]`, both `endRule: "wipe"`, ticks 109 and 194,
`reason: "complete"`), so the picture and the record agree. Beneath it sit the two commander
plates with this fork's re-labelled columns — `COMMANDER | KILLS | LOST | ALIVE | REWARD`:
`ALPHA 156 132 30 793.56` and `BRAVO 132 156 6 676.34`, again exactly the replay's
`kills [156,132]` and `magentReward ["793.56","676.34"]` — each with the `TROOPS LEFT` big number
(30 and 6). The top strip is the scorebug: blue `ALPHA` chip left, red `BRAVO` chip right, per-side
`ALIVE 30 / 81` and `0 / 81` counts, and the centred clock
`game 2/2 · turn 10/15` over `TICK 194/300 · 30 V 0`. A `HEAT` toggle chip sits top-right (the
army heat overlay). Faintly behind the endcard the 45×45 grid is still drawn with per-soldier cog
chips clustered in two knots — the surviving Alpha mass and the dead centre — and a dimmed
`ALPHA IS ROUTED` banner plus a dimmed match feed bottom-right (`BRAVO IS ROUTED — …`,
`FIRST BLOOD — ALPHA`, `ALPHA IS ROUTED — …`), i.e. the plain-language feed is populated by the end
even though the *load-time* `feed_lines` sample was 0.

This is recognisably the **starter's chrome**, not a rewrite that shares only ids: the bottom
transport strip carries the same button row (restart · step-back · pause · `+5s` · play · loop ·
fast-forward), the `spoilers` toggle, a right-hand `ALPHA WINS 363 / 363` counter and the
`1× 2× 3× 4× 8× 16×` speed chips; below it the full-width **scrubber with labelled coloured
beats** (blue, red and orange ticks at the firstblood / rout / wipe / end moments the design note
names) over the **momentum sparkline** — the unit-count graph running the whole episode, with the
Alpha curve pulling away at the right. That is paintbot/coworld-ctf's transport + scrubber +
scorebug + endcard layout, re-labelled to this game's vocabulary (COMMANDER/KILLS/LOST/ALIVE/
REWARD, TROOPS LEFT, TROOPS LEAD), not a different product.

Motion is proven independently of the picture by the three scrub readouts: at 0 % the lobby frame
(`game 1/2 · turn 1/15 TICK 0/300 · 81 V 81`), at 50 % mid-second-game attrition
(`game 2/2 · turn 3/15 TICK 49/300 · 43 V 32`) and at 100 % the final frame
(`game 2/2 · turn 10/15 TICK 194/300 · 30 V 0`) — the same 194-tick, two-game, 30-survivor episode
the replay records. `canvas_text` reports 0 draws crossing a canvas edge and 0 ellipsized, and
`console_tail` is empty, so nothing was clipped or thrown at 1280 px.

Two legibility observations for the coordinator, neither blocking: (i) the endcard **occludes the
battlefield** at the final frame, so a spectator who lands on the last tick sees the result rather
than the field — expected for an endcard, and the transport's step-back/scrub recovers it;
(ii) the load-time readout captured `status: "CONNECTING"` and `feed_lines: 0` at TICK 0 — the
status chip had not yet settled to its playing state at the instant of the first drawn frame. The
feed is demonstrably populated later (visible in the screenshot), so this is a first-frame timing
artefact of the probe, not a stuck chip; still, a chip that reads `CONNECTING` on the frame it
first draws is worth a phase-30 glance next time.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | **TRUE** — rounds 1 & 2 completed 10:09:19Z / 10:24:29Z; fillers set 10:07:44Z; 0 failed/discarded |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey rank 1 (rp 2), daveey-1 rank 2 (rp 2); no filler rows |
| 3 | Latest round's episode request completed with replay | **TRUE** — `ereq_3cc278d1-…` completed, replay_url set, seats daveey / daveey-1, +24 / −24 |
| 4 | Replay bytes valid and show the game | **TRUE** — COWLDMAG → `replay_summary.py` strict-UTF-8 JSON; `magent-battle/v1`; `reason: complete`; 32/32 LLM decisions, 0 fallbacks; kills 156/132 |
| 5 | Hosted game log clean | **TRUE** — 0 matches in 67 362 decoded chars; 32/32 Bedrock calls 200 |
| 6 | Public page uses the static replay path | **TRUE** — SSR `playlist[0]` featured match `magent-battle.r2.e1`; session `viewer_url` = `/replays/static/<cow_id>/<manifest_sha>/index.html?replay=…`, `ready: true`; no `/client/replay` |
| 7 | Certification declared the static bundle | **TRUE** — committed `release-result.json`: `Replay liveness: skipped (static replay bundle declared…` |
| 8 | Spectator judgment (viewer executed) | **TRUE** — run `33063093381`, `loaded: true` @4 204 ms, three differing clock readouts, starter chrome intact |

**8 of 8 TRUE. 0 FALSE.**
