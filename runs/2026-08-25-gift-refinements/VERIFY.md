# VERIFY — gift-refinements   (2026-08-26T04:26Z)

Verdict: **all-true** (8 / 8)

**This file supersedes verification round 1** (written 2026-08-26T03:12Z, verdict *2 items false —
checks 4 and 5*). Round 1's conclusions are preserved in git history (commit touching this path
before this one) and in `runs/2026-08-25-gift-refinements/log.md`; nothing from it is reused as
evidence here. Every fetch below was made fresh between 04:22Z and 04:25Z on 2026-08-26, against
coworld **0.1.2** (`cow_e19d6eae-78b4-447d-878d-b856c435db87`, the re-release that carries the D1
and D2 fixes) and against league entries re-wired to the **`:v3`** policy versions.

Run: `2026-08-25-gift-refinements` · coworld `cow_e19d6eae-78b4-447d-878d-b856c435db87` v0.1.2 ·
manifest `sha256:accb4520dec3f76613e560ad483b631b830cd66df49a98afd3768e08cb3dcd38` ·
league `league_aa42c0da-031b-49b1-9524-e4acc85fd2f6` ·
division `div_3c0d2b61-0e4a-4d9c-b27f-524158fede53` · repo `Metta-AI/cogame-gift-refinements`
@ `d874ebd55a7244a57baa711c92651eaf55c4b08a`.

Headers sent on every Observatory call: `Authorization` (bearer; value never printed),
`User-Agent: coworld-builder/1.0`; `X-Use-Elevated-Privileges: true` added on `artifacts/logs` and
on the `filler-policies` read. No token-bearing URL appears in this file.

**Wall clock.** Verifier (round 2) started 03:47:42Z; the 75-minute SPEC bound expires 05:02:42Z.
Work finished 04:26Z — the bound was not reached.

---

## Which rounds count, and why

The league re-wire (pause → `:v3` fillers → resubmit champions at `:v3` → unpause → trigger)
completed **2026-08-26T03:49Z**. A round counts toward check 1 only if its
`round_config.entrant_attributions` carries **both** `:v3` champion policy-version ids —
mirror `7377bf74-8cb0-456c-badb-45c3450de286` (daveey) and
patron `d848d844-c89d-40a0-bf4a-4d7713ce8ebf` (daveey-1). Attribution was read per round from the
same `/rounds` body pasted under check 1:

| round | status | completed_at | mirror pv | patron pv | counts? |
|---|---|---|---|---|---|
| 1 | failed | 02:36:01Z | `81167874` (v2) | `b88073d9` (v2) | no — failed, pre-fillers |
| 2 | completed | 02:37:13Z | `81167874` (v2) | `b88073d9` (v2) | no — pre-rewire (D1/D2 present) |
| 3 | completed | 02:57:20Z | `81167874` (v2) | `b88073d9` (v2) | no — pre-rewire |
| 4 | completed | 03:08:00Z | `81167874` (v2) | `b88073d9` (v2) | no — pre-rewire |
| 5 | completed | 03:27:14Z | `81167874` (v2) | `b88073d9` (v2) | no — pre-rewire |
| 6 | completed | 03:41:55Z | `81167874` (v2) | `b88073d9` (v2) | no — pre-rewire |
| 7 | completed | 03:51:33Z | `7377bf74` (**v3**) | `b88073d9` (v2) | **no** — patron still v2 |
| 8 | completed | 04:06:13Z | `7377bf74` (**v3**) | `d848d844` (**v3**) | **yes** |
| 9 | completed | 04:21:11Z | `7377bf74` (**v3**) | `d848d844` (**v3**) | **yes** |

Round 7 was scheduled (03:45:43Z) before patron:v3's league placement landed, exactly as the
coordinator's brief predicted; its attribution is pasted under check 1 and it is excluded.

**Pinned round for checks 3, 4, 5, 6 and 8: round 9**, `round_7e355346-62e5-4784-aef8-afd8274c0919`
— the latest completed round whose attribution carries both `:v3` ids. Round 8 is used as
corroboration only, and is labelled as such.

Ownership cross-check (`GET /policy-versions?limit=200`, 03:49Z, bare array, filtered client-side):

```
gift-refinements-mirror	7377bf74-8cb0-456c-badb-45c3450de286	daveey
gift-refinements-patron	d848d844-c89d-40a0-bf4a-4d7713ce8ebf	daveey-1
gift-refinements-reciprocator	e9f53270-27b1-4905-9728-107b1d10fad8	daveey
gift-refinements-hoarder	2c45167f-8f09-4535-878d-234490db9b8a	daveey
```

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

The `:v3` fillers were registered at **2026-08-26T03:46:48Z** (`log.md`: *"60 re-wire: paused 200;
fillers set to reciprocator:v3=e9f53270 hoarder:v3=2c45167f (response lists exactly these two)"*).
Confirmed live this run:

```
GET https://softmax.com/api/observatory/v2/leagues/league_aa42c0da-031b-49b1-9524-e4acc85fd2f6/filler-policies
headers: Authorization, User-Agent, X-Use-Elevated-Privileges
2026-08-26T04:25:09Z → HTTP 200  bytes=559
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"e9f53270-27b1-4905-9728-107b1d10fad8","policy_name":"gift-refinements-reciprocator","version":3,"player_name":"daveey"},
 {"policy_version_id":"2c45167f-8f09-4535-878d-234490db9b8a","policy_name":"gift-refinements-hoarder","version":3,"player_name":"daveey"}]}
```
Neither filler id is a champion id. ✅

```
GET https://softmax.com/api/observatory/v2/rounds?league_id=league_aa42c0da-031b-49b1-9524-e4acc85fd2f6&limit=20
headers: Authorization, User-Agent
2026-08-26T04:22:01Z → HTTP 200  bytes=26697
```

Deviation recorded per instruction: the prompt's filter is `jq '[.entries[]|…]'`. `/rounds`
returned `{entries:…}` on every call this run, but I used the dual-shape guard from
`playbooks/observatory-api.md` §2 (`/leagues` and `/policy-versions` were bare arrays this run):

```bash
jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
```
```
8
```

Body, trimmed to `round_number,id,status,error,created_at,completed_at` plus the champion
attributions that decide which rounds count (rounds 7–9 pasted in full; 1–6 summarised in the
table above from the same body):

```json
[
  {
    "round_number": 9,
    "id": "round_7e355346-62e5-4784-aef8-afd8274c0919",
    "status": "completed",
    "error": null,
    "created_at": "2026-08-26T04:15:44.985493Z",
    "completed_at": "2026-08-26T04:21:11.749708Z",
    "champions": [
      {"player": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "pv": "7377bf74-8cb0-456c-badb-45c3450de286"},
      {"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "pv": "d848d844-c89d-40a0-bf4a-4d7713ce8ebf"}
    ]
  },
  {
    "round_number": 8,
    "id": "round_c00d850b-190a-412b-afd9-2bc0b25c4479",
    "status": "completed",
    "error": null,
    "created_at": "2026-08-26T04:00:44.155288Z",
    "completed_at": "2026-08-26T04:06:13.014419Z",
    "champions": [
      {"player": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "pv": "7377bf74-8cb0-456c-badb-45c3450de286"},
      {"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "pv": "d848d844-c89d-40a0-bf4a-4d7713ce8ebf"}
    ]
  },
  {
    "round_number": 7,
    "id": "round_b7828a6d-8074-4056-acb2-8fa826ebbae6",
    "status": "completed",
    "error": null,
    "created_at": "2026-08-26T03:45:43.821242Z",
    "completed_at": "2026-08-26T03:51:33.940215Z",
    "champions": [
      {"player": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "pv": "7377bf74-8cb0-456c-badb-45c3450de286"},
      {"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "pv": "b88073d9-94e9-4249-a6c7-42402aec2e1e"}
    ]
  },
  {
    "round_number": 1,
    "id": "round_5c4fa064-0039-438c-8fa8-251ac256f07a",
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-26T02:36:01.142057Z",
    "completed_at": "2026-08-26T02:36:01.456507Z"
  }
]
```

Status: **TRUE** — **rounds 8 and 9** are `completed`, both created after the `:v3` fillers were
registered at 03:46:48Z, and both carry **both** `:v3` champion policy-version ids. (Eight rounds
are completed overall; only these two satisfy this run's stricter both-v3 rule.) The only
non-completed round is round 1, `failed`, error quoted verbatim above — the pre-fillers
`trigger-round` failure `playbooks/observatory-api.md` §6 predicts. No round is `discarded`.

---

## 2. Both champions ranked; fillers absent/Baseline — **TRUE**

```
GET https://softmax.com/api/observatory/v2/divisions/div_3c0d2b61-0e4a-4d9c-b27f-524158fede53/leaderboard
headers: Authorization, User-Agent
2026-08-26T04:22:06Z → HTTP 200  bytes=612   (jq 'type' → "array": bare list, not {entries})
```
```bash
jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey	gift-refinements-mirror:v3	1049.937886172548	8	6.0
2	daveey-1	gift-refinements-patron:v3	950.062113827452	8	2.0
```

Full rows, verbatim:

```json
{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1049.937886172548,"score_label":"MMR","score_value_type":"integer","rounds_played":8,"episode_wins":6.0,"episodes_played":null,"win_rate":0.75,"policy_label":"gift-refinements-mirror:v3","recent_rounds":null}
{"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":950.062113827452,"score_label":"MMR","score_value_type":"integer","rounds_played":8,"episode_wins":2.0,"episodes_played":null,"win_rate":0.25,"policy_label":"gift-refinements-patron:v3","recent_rounds":null}
```

Status: **TRUE** — `daveey` (rank 1, `gift-refinements-mirror:**v3**`, `rounds_played=8`) and
`daveey-1` (rank 2, `gift-refinements-patron:**v3**`, `rounds_played=8`) are both ranked with
`rounds_played ≥ 1`, and the labels have rolled over from `:v2` to `:v3`, confirming the re-wire is
what the ladder is now scoring. The list has exactly two rows: neither filler
(`gift-refinements-reciprocator:v3`, `gift-refinements-hoarder:v3`) appears at all.

---

## 3. The pinned round's episode request completed with a replay — **TRUE**

```bash
R=round_7e355346-62e5-4784-aef8-afd8274c0919      # round 9 — latest completed round with both :v3 ids
```
```
GET https://softmax.com/api/observatory/v2/episode-requests?round_id=round_7e355346-62e5-4784-aef8-afd8274c0919&limit=20
headers: Authorization, User-Agent
2026-08-26T04:22:12Z → HTTP 200  bytes=3353
jq -r '.entries[]|[.id,.status]|@tsv'
```
```
ereq_f3e3a82c-ec2f-4610-b941-86f48bd6361c	completed
```
```
GET https://softmax.com/api/observatory/v2/episode-requests/ereq_f3e3a82c-ec2f-4610-b941-86f48bd6361c
headers: Authorization, User-Agent
2026-08-26T04:22:12Z → HTTP 200  bytes=3505
jq '{status,replay_url,participants,participant_scores}'   (participants trimmed to identity fields)
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/c3935602-3bd8-41f3-aacc-7421ab7a18f5.replay",
  "participants": [
    {"position": 0, "policy_name": "gift-refinements-mirror",       "version": 3, "player_name": "daveey",   "is_filler": false},
    {"position": 1, "policy_name": "gift-refinements-patron",       "version": 3, "player_name": "daveey-1", "is_filler": false},
    {"position": 2, "policy_name": "gift-refinements-reciprocator", "version": 3, "player_name": "daveey",   "is_filler": true},
    {"position": 3, "policy_name": "gift-refinements-hoarder",      "version": 3, "player_name": "daveey",   "is_filler": true},
    {"position": 4, "policy_name": "gift-refinements-reciprocator", "version": 3, "player_name": "daveey",   "is_filler": true},
    {"position": 5, "policy_name": "gift-refinements-reciprocator", "version": 3, "player_name": "daveey",   "is_filler": true}
  ],
  "participant_scores": [
    {"position": 0, "score": 33.0}, {"position": 1, "score": 11.0}, {"position": 2, "score": 46.0},
    {"position": 3, "score": 22.0}, {"position": 4, "score": 26.0}, {"position": 5, "score": 17.0}
  ]
}
```

Status: **TRUE** — `status == "completed"`, `replay_url` non-null, and `participants` name
`daveey` at position 0 and `daveey-1` at position 1, both `is_filler: false` and both at
**version 3**; positions 2–5 are `is_filler: true`. As in round 1's verification, the API returns
filler rows by policy name with an `is_filler` flag; the `Baseline (N)` display strings the prompt
describes are what the **replay** carries (`results.names` under check 4) and what the leaderboard
suppresses.

---

## 4. Replay bytes are valid and show the game — **TRUE**

```
GET https://softmax-public.s3.amazonaws.com/replays/c3935602-3bd8-41f3-aacc-7421ab7a18f5.replay
2026-08-26T04:22:29Z → HTTP 200  bytes=162688   (curl -sSL, no auth header; public S3)
```
```bash
jq -e . /tmp/ep9.replay >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .results.reason, .results.ending' /tmp/ep9.replay
```
```
strict UTF-8 JSON: ok
gift-refinements.replay.v1
complete
round_limit
```

Protocol cross-check against the manifest —
`GET /v2/coworlds/cow_e19d6eae-78b4-447d-878d-b856c435db87` (headers: Authorization, User-Agent),
2026-08-26T04:22:35Z → HTTP 200, bytes=16351:

```json
{"id":"cow_e19d6eae-78b4-447d-878d-b856c435db87","name":"gift-refinements","version":"0.1.2",
 "canonical":true,
 "manifest_hash":"sha256:accb4520dec3f76613e560ad483b631b830cd66df49a98afd3768e08cb3dcd38"}
```
manifest text, the sentence that pins the protocol:
```
… as index.html?replay=<url of the .replay file> and contacts no server but S3. The replay itself
is one strict-UTF-8 JSON document, protocol gift-refinements.replay.v1, carrying the aliases, the
policy names, the body colours, the whole board geom…
```
`manifest_hash` matches `STATE.coworld.manifest_sha`; `protocol` matches. ✅

### Attempt 1 — the prompt's filters, run verbatim

```bash
jq -r '[.events[]|select(.type=="decision")]|length' /tmp/ep9.replay   →  0
jq -r '[.events[]|select(.fallback==true)]|length'   /tmp/ep9.replay   →  0
```

Both are `0` because this coworld's replay schema has **no `type` and no `fallback` key**. Event
kind is `.k`; the decision row is `.k=="order"` and its provenance field is `.source ∈
llm|retry|fallback|scripted` (`design.md`: *"| order | t, seat, round, job, target, gift, consume,
clamped, source ("llm"|"retry"|"fallback"|"scripted"), say, notes, latencyMs |"*). Observed kinds
in this replay:

```bash
jq -r '[.events[].k]|group_by(.)|map("\(.[0])=\(length)")|join(" ")' /tmp/ep9.replay
```
```
collect=67 consume=12 defect=1 end=1 gift=152 order=72 round=12 spawn=66 spill=65
```

### Attempt 2 — schema-correct provenance count on the champion seats

```bash
jq -r '[.events[]|select(.k=="order" and (.seat==0 or .seat==1))|.source]|group_by(.)|map("\(.[0])=\(length)")|join(" ")' /tmp/ep9.replay
jq -r '[.events[]|select(.k=="order" and .seat==0)|.source]|group_by(.)|map("seat0 \(.[0])=\(length)")|join(" ")' /tmp/ep9.replay
jq -r '[.events[]|select(.k=="order" and .seat==1)|.source]|group_by(.)|map("seat1 \(.[0])=\(length)")|join(" ")' /tmp/ep9.replay
```
```
llm=24
seat0 llm=12
seat1 llm=12
```

**24 of 24 champion decisions are `source: "llm"`. Zero `scripted`, zero `fallback`, zero `retry`.**
(Round 1's verification found 21/24 `scripted` on its pinned round — D1 is gone.) The full champion
order table, with latencies and the `say` line the spectator sees:

```
round seat source job     target gift consume latencyMs say
1     0    llm    collect null   0    never   4394      opening move: collect and share
1     1    llm    collect null   0    never   4394      Round 1: collecting raw tokens to probe
2     0    llm    collect null   0    never   5402      Building raw stock for strategic distribution
2     1    llm    meet    Aro    1    never   5402      Probing Aro with single raw token
3     0    llm    meet    Eno    1    never   5946      Tit-for-tat: Bex gave 3, repaying with 1 beam this round
3     1    llm    meet    Aro    10   never   5946      Aro returned nothing r2; probing Cyr this round via gift. Monitoring.
4     0    llm    meet    Eno    1    never   6001      Eno reciprocated r3; opening chain with 1 raw→3refined
4     1    llm    meet    Cyr    10   never   6001      Cyr returned 15 for 10 sent (r3). Best partner so far. Commit chain.
5     0    llm    hold    null   0    end     5776      Clearing raw tokens before next round of refined exchanges
5     1    llm    meet    Cyr    10   never   5776      Cyr chain live: 15 super received r4, holding for r11-12 return phase
6     0    llm    collect null   0    never   4904      R6: Collecting raw tokens. Bex net +27, reciprocate this round.
6     1    llm    meet    Cyr    10   never   4904      Cyr partnership strong: 29 in, 11 out net positive. Continue chain.
7     0    llm    collect null   0    never   4777      Collecting raw tokens to restart chain with Bex
7     1    llm    meet    Cyr    10   never   4777      R7: Cyr chain holding strong. Feed super tokens south, maintain partne…
8     0    llm    collect null   0    never   5795      R8: Collecting raw tokens toward beam threshold with Bex
8     1    llm    meet    Cyr    10   never   5795      R8: Cyr partnership solid (+8 net). Holding 1 super, firing all 10 at …
9     0    llm    collect null   0    never   6213      R9: collecting raw to rebuild chain with Bex
9     1    llm    meet    Cyr    10   never   6213      R9: CYR partnership locked. Firing 10 supers south. Hold stack for r11…
10    0    llm    collect null   0    never   5313      Collecting raw tokens to rebuild refined chain with Bex
10    1    llm    meet    Cyr    10   never   5313      R10: CYR chain active. Firing 10 supers. Hold until R12 close.
11    0    llm    collect null   0    never   5000      Collecting raw tokens for final exchange chain with Bex
11    1    llm    meet    Cyr    10   end     5000      R11: Chain intact, CYR reliable. Firing 10 supers to maximize final ro…
12    0    llm    meet    Bex    3    end     4781      Final round: gifting 3 raw to Bex, then banking everything at close
12    1    llm    hold    null   0    end     4781      Final tick approaching. Empty hands, chain complete. Banking on close.
```

Every row has a non-zero `latencyMs` (4.4–6.2 s — a real model call per decision, versus the
`latencyMs: 0` signature of the scripted rows round 1 found), and the content is non-trivial and
game-specific: seat 1 identifies Cyr as a reciprocating partner in round 4 and runs a 10-token
super-gift chain with it for eight consecutive rounds; seat 0 tracks Bex's and Eno's net balances
and swaps partners when a chain breaks. That is the thing this game is about.

### Attempt 3 — cross-check against the hosted game container's own episode summary

Decoded from the check-5 log fetch below:
```
gift-refinements: episode finished reason=complete ending=round_limit rounds=12 gifts=152 minted=344 llmOrders=24 fallbacks=0
```
`llmOrders=24` (the full budget of 2 LLM seats × 12 rounds) and `fallbacks=0`. Agrees with the
replay exactly.

### Corroboration — round 8 (`round_c00d850b-…`, the other qualifying round)

```
GET https://softmax-public.s3.amazonaws.com/replays/c2108d36-c312-4419-b589-c4fb493a9a4c.replay
2026-08-26T04:07Z → HTTP 200  bytes=190974
strict UTF-8 JSON: ok · protocol gift-refinements.replay.v1 · results.reason complete · ending round_limit
jq '[.events[]|select(.k=="order" and (.seat==0 or .seat==1))|.source]|group_by(.)…'  →  llm=23 retry=1
log: "episode finished … llmOrders=24 fallbacks=0"
```
23 `llm` + 1 `retry` (a first attempt that failed validation and whose **retry succeeded** — no seat
degraded), zero `scripted`, zero `fallback`.

### Verdict

Status: **TRUE** — strict UTF-8 JSON under `jq -e`; `protocol` (`gift-refinements.replay.v1`)
matches the manifest of `cow_e19d6eae-…`; `results.reason == "complete"` (no `deadline` exception
needed); and the champion seats' 24 decisions are **all** `llm`, none scripted, none fallback, with
substantive, game-specific content. `design.md`'s failure state ("a scripted policy seated as a
champion") does not occur.

---

## 5. Hosted game log is clean — **TRUE**

```
GET https://softmax.com/api/observatory/v2/episode-requests/ereq_f3e3a82c-ec2f-4610-b941-86f48bd6361c/artifacts/logs
headers: Authorization, User-Agent, X-Use-Elevated-Privileges
2026-08-26T04:22:50Z → HTTP 200  bytes=51476  (decoded 51339)
```

The body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it was
decoded per-repr with `ast.literal_eval` before grepping, per `playbooks/observatory-api.md` §10.

### Attempt 1 — the prompt's grep, on the decoded text

```bash
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/l9.txt || echo CLEAN
```
```
CLEAN
```

### Attempt 2 — the same grep on the raw (undecoded) body, and a wider net

```bash
grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/l9.raw   →  0
```
Per-pattern counts on the decoded text, including patterns **beyond** the prompt's four (D1's smell
is a champion seat with `source=="scripted"`; D2's is `falling back to scripted order (parse_error)`):

| pattern | matches |
|---|---|
| `falling back` | 0 |
| `LLM provider is unavailable` | 0 |
| `cut off at max_tokens` | 0 |
| `rejected` | 0 |
| `fallback` | 1 — the substring inside `fallbacks=0` on the episode-finished line |
| `parse_error` | 0 |
| `throttl` | 0 |
| `429` | 0 |
| `"ok":false` | 0 |
| `Traceback` | 0 |

Bedrock sidecar health in the same log: `24` lines matching `"ok":true,"status_code":200`, `0`
matching `"ok":false`. Model: `global.anthropic.claude-haiku-4-5-20251001-v1:0`.

### Attempt 3 — the whole game container, verbatim (the lobby line and the seat registrations)

```
===== container: game =====
gift-refinements: seed not pinned; randomized
gift-refinements config: seed=1706688292 variant=refinery num_agents=6 rounds=12 ticksPerRound=60 pillars=5 spawnTicks=30 beamRange=4 minTurnSeconds=25
gift-refinements llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
gift-refinements: listening on 0.0.0.0:8080
gift-refinements: seat 3 connected
{"k":"register","seat":3,"policy":"hoarder","kind":"scripted","baseline":"hoarder"}
gift-refinements: seat 5 connected
gift-refinements: seat 2 connected
gift-refinements: seat 4 connected
{"k":"register","seat":5,"policy":"reciprocator","kind":"scripted","baseline":"reciprocator"}
{"k":"register","seat":4,"policy":"reciprocator","kind":"scripted","baseline":"reciprocator"}
{"k":"register","seat":2,"policy":"reciprocator","kind":"scripted","baseline":"reciprocator"}
gift-refinements: seat 1 connected
{"k":"register","seat":1,"policy":"prompt","kind":"llm","baseline":"reciprocator"}
gift-refinements: seat 0 connected
{"k":"register","seat":0,"policy":"prompt","kind":"llm","baseline":"reciprocator"}
gift-refinements: lobby closed with 6/6 seats connected, 6 registered
gift-refinements: seat 3 disconnected
gift-refinements: seat 4 disconnected
gift-refinements: seat 0 disconnected
gift-refinements: seat 5 disconnected
gift-refinements: seat 1 disconnected
gift-refinements: seat 2 disconnected
gift-refinements: episode finished reason=complete ending=round_limit rounds=12 gifts=152 minted=344 llmOrders=24 fallbacks=0
gift-refinements: holding /healthz and /global for 20s
```

**The lobby line is `lobby closed with 6/6 seats connected, 6 registered`** — the line the
coordinator asked to see, and the D1 fix working: both champion pods (seats 0 and 1) connect **and**
register *before* the close, and both register as `"kind":"llm"`, not as a scripted baseline. The
six `disconnected` lines all follow the episode, at teardown.

**Per-seat order-source counts for the pinned round (from the replay, check 4):
seat 0 = `llm 12 / 12`, seat 1 = `llm 12 / 12`.** No scripted, fallback or retry order on either
champion seat.

### Corroboration and the one honest caveat — round 8

Round 8's log (re-fetched fresh, 2026-08-26T04:25:09Z → HTTP 200, bytes=53799) has the same lobby
line, `lobby closed with 6/6 seats connected, 6 registered`, and `llmOrders=24 fallbacks=0`, but is
**not** `CLEAN`: it carries exactly one matching line —

```
128:gift-refinements llm: seat 1 attempt 1 failed, falling back if it fails again: target is required when job is meet or gift > 0
129:gift-refinements: {"k":"fallback","round":12,"seat":1,"attempt":1,"cause":"parse_error","detail":"target is required when job is meet or gift > 0"}
```

— a **first-attempt validation miss whose retry succeeded** (`source: "retry"` on that order,
`fallbacks=0` in the summary; no `falling back to scripted order` line). It is recorded here for
honesty and as a phase-30 durability note: patron's prompt can still occasionally omit `target`.
It does **not** affect this check, which pins to round 9 — round 9's log has zero matches of any
kind. No documented exception is invoked anywhere in this check: the pinned round is clean on the
literal grep.

Status: **TRUE** — `CLEAN` on the pinned round, decoded and raw, on the prompt's four patterns and
on the four extra patterns the two known defects would show up in.

---

## 6. The public page uses the static replay path — **TRUE**

### Source A — raw HTML (attempted first, per the prompt)

```
GET https://softmax.com/gift-refinements
2026-08-26T04:23:06Z → HTTP 200  bytes=571940
grep -o '<iframe[^>]*src="[^"]*"'
```
```
GREP: no iframe in raw HTML     (grep -c iframe → 0)
```
Treated as *unknown*, not a false negative — the page is client-rendered for the iframe
(`playbooks/observatory-api.md` §Featured match, answered by the lighthouse run).

### Source B — the coworld detail API

```
GET https://softmax.com/api/observatory/v2/coworlds?limit=200  → HTTP 200   2026-08-26T04:23:24Z
jq -c '…|select(.name=="gift-refinements")|{id,version,canonical,replay_viewer,featured_match}'
```
```json
{"id":"cow_e19d6eae-78b4-447d-878d-b856c435db87","version":"0.1.2","canonical":true,"replay_viewer":null,"featured_match":null}
{"id":"cow_686eadd9-7594-425c-98b2-854deb9acdd1","version":"0.1.1","canonical":false,"replay_viewer":null,"featured_match":null}
{"id":"cow_9e7238a7-b973-49c2-af58-7db7217e40aa","version":"0.1.0","canonical":false,"replay_viewer":null,"featured_match":null}
```
0.1.2 is the canonical row; 0.1.0/0.1.1 are `canonical:false`. `featured_match: null` is
**null platform-wide** (playbook, lighthouse run) and is therefore not evidence either way.

### Source C — the SSR playlist + the session call the page's own JS makes (**the source I used**)

Featured match, server-rendered into the page fetched above at `state.playlist[0]` (verbatim,
un-escaped from the SSR payload):

```json
"playlist":[{"episodeId":"33733742-ee39-4ba4-bf24-2cc8bb64403e",
 "coworldId":"cow_e19d6eae-78b4-447d-878d-b856c435db87",
 "coworldName":"gift-refinements","coworldVersion":"0.1.2",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/c3935602-3bd8-41f3-aacc-7421ab7a18f5.replay",
 "finishedAt":"2026-08-26T04:21:07.319226Z","roundNumber":9,"episodeNumber":1,
 "code":"gift-refinements.r9.e1",
 "matchup":{"divisionId":"div_3c0d2b61-0e4a-4d9c-b27f-524158fede53","divisionName":"Competition",
  "first":{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
           "score":1049.937886172548,"policy_label":"gift-refinements-mirror:v3", … },
  "second":{"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1", … }}}]
```

The featured match **has rolled over to the 0.1.2 coworld** (`cow_e19d6eae-…`) and to the pinned
round (`gift-refinements.r9.e1`, replay `c3935602-…` — the same bytes verified under check 4). No
re-poll was needed.

```
POST https://softmax.com/api/observatory/v2/coworlds/replays/session
headers: Authorization, User-Agent, content-type
body: {"coworld_id":"cow_e19d6eae-78b4-447d-878d-b856c435db87",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/c3935602-3bd8-41f3-aacc-7421ab7a18f5.replay"}
2026-08-26T04:23:24Z → HTTP 200  bytes=340
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e19d6eae-78b4-447d-878d-b856c435db87/sha256%3Aaccb4520dec3f76613e560ad483b631b830cd66df49a98afd3768e08cb3dcd38/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fc3935602-3bd8-41f3-aacc-7421ab7a18f5.replay&v=2",
  "ready": true
}
```

Status: **TRUE** — source used: **C** (SSR payload + `POST /coworlds/replays/session`), after A
found nothing and B returned the platform-wide `null`. A featured match is present
(`gift-refinements.r9.e1`, two ranked players in `matchup`). The iframe `src` is
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`, with
`<cow_id> = cow_e19d6eae-78b4-447d-878d-b856c435db87` (0.1.2) and
`<sha> = sha256%3Aaccb4520dec3f76613e560ad483b631b830cd66df49a98afd3768e08cb3dcd38`, the coworld's
manifest hash, matching `STATE.coworld.manifest_sha`. `ready: true`; the path ends `/index.html`.
**No `/client/replay` pod URL anywhere.**

---

## 7. Certification declared the static bundle — **TRUE**

Source: the **committed** `runs/2026-08-25-gift-refinements/release-result.json` — the artifact of
**this run's** 0.1.2 release dispatch (run `32927080527`), committed in `e5abcfa`
*"gift-refinements: release 0.1.2 canonical+certified, policies v3"*. It was present; **no
re-download was needed** and `/tmp` was never consulted.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-25-gift-refinements/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Surrounding context from the same file, confirming it is the 0.1.2 artifact and not the superseded
0.1.1 one:

```json
{"version":"0.1.2","ok":true,
 "cow_id":"cow_e19d6eae-78b4-447d-878d-b856c435db87",
 "manifest_sha":"sha256:accb4520dec3f76613e560ad483b631b830cd66df49a98afd3768e08cb3dcd38",
 "canonical":true,"hosted_smoke":"passed","hosted_certification":"certifying",
 "certify":{"ok":true},"secret_put":true,"errors":[],"step_failed":null}
```
and the tail of `certify.output_tail`:
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
Logs: …/tmp/coworld-cert-_uffl9jr/logs
Inspect replay: open …/tmp/coworld-cert-_uffl9jr/replay in your static replay viewer bundle (see STATIC_REPLAY_VIEWERS.md)
```

(`hosted_certification: "certifying"` is the snapshot the workflow took at the moment it wrote the
artifact; phase 40's own follow-up `GET /v2/coworlds/cow_e19d6eae-…/certification` returned
`state=certified, certified=true, failed_step=null`, recorded in `log.md` at 03:36:27Z. That
follow-up is phase 40's evidence, not this check's; this check reads the file, and the file
contains the required string.)

Status: **TRUE** — contains `Replay liveness: skipped (static replay bundle declared`, read from the
committed `runs/2026-08-25-gift-refinements/release-result.json`.

---

## 8. Spectator judgment — the viewer was EXECUTED — **TRUE**

### (a) Dispatch, against the check-6 iframe `src`

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e19d6eae-78b4-447d-878d-b856c435db87/sha256%3Aaccb4520dec3f76613e560ad483b631b830cd66df49a98afd3768e08cb3dcd38/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fc3935602-3bd8-41f3-aacc-7421ab7a18f5.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90    # dispatched 2026-08-26T04:23:32Z
sleep 10
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status,conclusion -L 6 \
  | jq -r 'sort_by(.createdAt)|reverse|.[]|[.databaseId,.createdAt,.status,(.conclusion//"-")]|@tsv'
```
```
32930044755	2026-08-26T04:23:33Z	in_progress	-      <- createdAt matches the dispatch instant
32928573158	2026-08-26T04:00:29Z	completed	success   <- not mine (another run's verifier)
32925387074	2026-08-26T03:09:23Z	completed	success   <- verification round 1's
32924883541	2026-08-26T03:01:23Z	completed	success
32923659915	2026-08-26T02:41:21Z	completed	success
32911662736	2026-08-25T23:38:22Z	completed	success
```
The run was found by sorting on `createdAt`, **not** by taking "the latest" blind — run
`32928573158` at 04:00:29Z is a different run's dispatch and would have been the wrong artifact.

```
gh run watch 32930044755 -R Metta-AI/coworld-builder --exit-status   → exit 0
gh run view  32930044755 -R Metta-AI/coworld-builder --json status,conclusion,createdAt,updatedAt
{"conclusion":"success","status":"completed","createdAt":"2026-08-26T04:23:33Z","updatedAt":"2026-08-26T04:24:19Z"}
gh run download 32930044755 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-25-gift-refinements/viewer-check
```

Artifact committed at `runs/2026-08-25-gift-refinements/viewer-check/` — `viewer-smoke.json`
(1356 B), `viewer-smoke.png` (675 436 B), `smoke-stdout.txt`, `smoke-stderr.txt` (0 B). This
directory was **replaced**, not merged: verification round 1's artifact (run `32925387074`) is gone
from the working tree and survives only in git history.

The `url` the job actually opened, read back out of the artifact
(`jq -r '.url' viewer-smoke.json`), is byte-identical to the check-6 `viewer_url`:
```
https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_e19d6eae-78b4-447d-878d-b856c435db87/sha256%3Aaccb4520dec3f76613e560ad483b631b830cd66df49a98afd3768e08cb3dcd38/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fc3935602-3bd8-41f3-aacc-7421ab7a18f5.replay&v=2
```

### (b) Readouts, verbatim

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-25-gift-refinements/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":3442,"clock":"ROUND 1 / 12 TICK 0 OF 720","scorebug":"TOKENS BANKED TOKENS 0 0 MINTED · 0 DEFECTIONS ROUND 1 / 12 TICK 0 OF 720 GIFTS GIVEN TOKENS 0 0 MINTED · 0 DEFECTIONS","feed_lines":0}
```
```bash
jq -c '.signals' runs/2026-08-25-gift-refinements/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```
```bash
jq -r '.failure // "no failure"'  → no failure
jq -r '.status'                   → OPEN
jq -r '.loading_text'             → null
jq -c '.console_tail'             → []
jq -c '.canvas_text'              → {"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
```

### The three clock readouts

```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-25-gift-refinements/viewer-check/viewer-smoke.json
```

| scrub position | clock readout |
|---|---|
| 0 % | `ROUND 1 / 12 TICK 0 OF 720` |
| 50 % | `ROUND 7 / 12 TICK 376 OF 720` |
| 100 % | `FINAL TICK 719 OF 720` |

Status: **TRUE** — `loaded: true` (signalled by `data-replay-loaded="true"`; the `coworld-replay`
postMessage bridge was not used — `bridge_ready: false` — which is the documented alternative), the
first frame drawn at **3442 ms**, `data_replay_error: null`, no console errors, and the **three
clock readouts all differ**, so the replay advances rather than freezing on one frame. A `#scrub`
element exists (the json reports real readouts, not `"(no #scrub…)"`).

### (c) The replay JSON the viewer was asked to draw

```bash
jq -r '.events[]|[.t,(.seat//"-"),.k,(.say//"")]|@tsv' /tmp/ep9.replay | head -14        # EARLY
```
```
0	0	order	opening move: collect and share
0	1	order	Round 1: collecting raw tokens to probe
0	2	order	collecting
0	3	order	mine
0	4	order	collecting
0	5	order	collecting
1	4	collect	
1	5	collect	
3	0	collect	
3	1	collect	
3	2	collect	
3	3	collect	
4	4	collect	
4	5	collect	
```
```
… MIDDLE (rows 200-212) …
204	-	gift	
204	2	spill	
208	-	gift	
208	2	spill	
210	-	spawn	
212	3	collect	
213	-	spawn	
214	2	collect	
239	-	round	
240	0	order	Clearing raw tokens before next round of refined exchanges
240	1	order	Cyr chain live: 15 super received r4, holding for r11-12 return phase
240	2	order	returning 10 to BEX
240	3	order	mine
```
```
… LATE (last 12) …
660	5	order	collecting for ENO
660	-	gift	
660	2	collect	
664	-	gift	
668	-	gift	
690	-	spawn	
691	2	collect	
719	1	consume	
719	2	consume	
719	4	consume	
719	-	round	
719	-	end	
```
```bash
jq -r '.results' /tmp/ep9.replay
```
```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"],
 "aliases":["Aro","Bex","Cyr","Dov","Eno","Fay"],
 "scores":[33,11,46,22,26,17],
 "win":[false,false,true,false,false,false],
 "collected":[9,4,17,22,10,5],
 "gifts_sent":[3,76,44,0,14,15],
 "gifts_received":[11,47,65,0,15,14],
 "banked_super":[15,2,44,0,15,15],
 "defections":[1,0,0,0,0,0],
 "reciprocity_x100":[11,91,60,0,46,55],
 "total_gifts":152,"total_minted":344,"rounds":12,
 "reason":"complete","ending":"round_limit"}
```

### Screenshot

`runs/2026-08-25-gift-refinements/viewer-check/viewer-smoke.png` — 675 436 bytes, 1280×800,
captured after the scrub sweep, i.e. at 100 % / the final tick.

### Spectator-judgment paragraph

**It is legible, it shows the game, and it is unmistakably the starter's chrome.** The screenshot is
a dark 1280×800 board carrying the coworld-ctf/paintbot furniture intact. Across the top is the
**scorebug**: `155 TOKENS · TOKENS BANKED · 344 MINTED · 1 DEFECTION` on the left, `GIFTS GIVEN ·
152 TOKENS` on the right, `FINAL / TICK 719 OF 720` centred. Under it runs the per-seat roster
strip — `CYR Bas… ⇄31% 46 | ARO dav… ⇄9% 33 | … Baselin… ⇄31% 26 | DOV Baselin… ⇄0% 22 | FAY
Baselin… ⇄35% 17 | BEX dave… ⇄41% 11` — dimmed behind the endcard. The board itself shows the
refinery grid with the five pillars and the six cogs clustered lower-left, each labelled with its
alias. The centre carries the **endcard**: `CYR WINS — Baseline`, a boxed `ROUND LIMIT` badge, and
the final tally `CYR 46 · ARO 33 · ENO 26 · DOV 22 · FAY 17 · BEX 11 — 152 gifts · 344 tokens
minted from 67 raw · 1 defections`. The right edge carries the game-specific **trust graph** — six
nodes with weighted edges, `BEX ⇄ CYR 141 ↔ 74`, `ENO ⇄ FAY 42 ↔ 45`, `ARO ⇄ BEX 9 ↔ 33`. The
bottom **transport strip** has restart / step-back / pause / +5s / step-forward / loop /
fast-forward, a `spoilers` toggle, the `CYR WINS 719 / 719` readout and the 1×–16× speed selector;
below it the **scrubber with its momentum graph** labelled `TOKENS IN PLAY`, a sawtooth trace with
green/red round-boundary ticks and the orange playhead parked at the far right. Every number on
screen reconciles with the replay JSON above: scores `[33,11,46,22,26,17]` (they sum to the 155
banked in the scorebug), `win[2]=true` → `CYR` = seat 2 = `Baseline`, `total_gifts: 152`,
`total_minted: 344`, `defections` summing to 1, `collected` summing to 67 raw, `ending:
"round_limit"`, tick 719 of 720. The picture is neither empty nor frozen: the 0 %/50 %/100 % clocks
step through `ROUND 1 … ROUND 7 … FINAL`, and the momentum curve traces exactly the cycle the events
record — a climb in tokens-in-play through each round's `gift` traffic (152 gift events) punctuated
by the sharp drop at each round-boundary `consume` burst (12 `consume`, 12 `round` events). This is
not a cogame-gridlock-style rewrite: it is the same product as paintbot/raid/hive, with
gift-refinements' own metrics (tokens banked / minted / gifts given / defections) and its own trust
graph substituted into the starter's shell.

Two observations, neither of them a check-8 failure:

1. `feed_lines: 0`. The capture is at the final tick, where the endcard overlay covers the board, so
   no play-by-play feed line is on screen at that instant; the artifact cannot distinguish "feed
   present but empty" from "no feed element". Carried forward unchanged from verification round 1 as
   a **legibility observation for phase 30** — the clock, scorebug, roster, endcard, trust graph and
   momentum scrubber already tell a spectator who is winning and why. The `say` strings the champions
   emit each round (pasted under check 4) are the obvious feed content if one is wanted.
2. **A scripted Baseline won this episode.** `CYR` (seat 2, `gift-refinements-reciprocator:v3`,
   a filler) took 46 to daveey's 33 and daveey-1's 11 — and the same shape holds in round 8
   (fillers 102/94/82 against champions 30/4). That is a *balance* observation, not a
   definition-of-done item: DoD asks that the champions **play** the game with real LLM decisions,
   which they demonstrably now do (24/24 `llm`, `reciprocity_x100` of 91 for daveey-1 — the highest
   on the board — showing patron's gift chain was actually reciprocated). But it is worth the
   coordinator's attention that the LLM prompts are currently out-scored by the scripted baselines
   they are seated against, and that the public page's endcard therefore reads
   `CYR WINS — Baseline`. Unlike verification round 1, the spectator is at least watching the
   champions genuinely play and lose, not watching baselines wearing champion names.

---

## Definition-of-done roll-up

| # | Item | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds **8** and **9**, both carrying both `:v3` champion ids |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey `mirror:v3` rp=8, daveey-1 `patron:v3` rp=8, no filler rows |
| 3 | Latest qualifying round's episode request completed with `replay_url` + correct participants | **TRUE** — `ereq_f3e3a82c-…`, participants v3, positions 0/1 `is_filler:false` |
| 4 | Replay bytes valid, champion seats doing the thing the game is about | **TRUE** — strict JSON, protocol matches manifest, `reason:"complete"`, **24/24 champion orders `llm`** |
| 5 | Hosted game log clean | **TRUE** — `CLEAN`; `lobby closed with 6/6 seats connected, 6 registered` |
| 6 | Public page uses static iframe `src` | **TRUE** — static path on `cow_e19d6eae-…` + manifest sha, featured match `gift-refinements.r9.e1` |
| 7 | Certification declared the static bundle | **TRUE** — committed 0.1.2 `release-result.json` |
| 8 | Viewer executed: `loaded: true` + three differing clocks | **TRUE** — run `32930044755`, loaded at 3442 ms, clocks `ROUND 1 → ROUND 7 → FINAL` |

**Verdict: all-true (8/8).** Both defects verification round 1 found are gone on the pinned round:
D1 (lobby closing before the champion pods registered → scripted champions) is fixed — `6/6 seats
connected, 6 registered` and 24/24 `llm` orders; D2 (champion prompt emitting an out-of-schema order
→ `parse_error` fallback) is fixed — zero `parse_error`, zero `falling back` lines on round 9.

Two non-blocking items carried to the coordinator: (a) round 8 still shows one first-attempt
`target is required when job is meet or gift > 0` from patron whose **retry succeeded** — prompt
durability, not a failure; (b) the scripted baselines currently out-score both LLM champions —
a balance observation for phase 30, not a DoD item.
