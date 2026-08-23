# VERIFY — escrow   (2026-08-23T17:56Z)

Verdict: **2 items false** (checks 4 and 5). 6 TRUE / 2 FALSE.

Attempt 2 — **post-remediation re-verification**. Everything below was fetched fresh between
2026-08-23T17:18Z and 17:56Z against the **v0.1.2** coworld (`cow_add93c03-…`) and the **v3**
champion/filler policies. Nothing is reused from attempt 1 (16:02–16:43Z); a one-paragraph
summary of attempt 1 is kept as an appendix at the bottom for continuity only.

**Scope rule applied throughout.** Only rounds whose `round_config.entrant_policy_version_ids`
contain **both** v3 champion UUIDs count as post-remediation:

| role | policy | policy_version_id | player |
|---|---|---|---|
| champion 1 | `escrow-drafter:v3` | `03aecc7d-d51b-42fd-92b8-2c3199583176` | `daveey` |
| champion 2 | `escrow-swapper:v3` | `ab5da062-606a-446b-accb-aeeb899a93a1` | `daveey-1` |
| filler 1 | `escrow-trader:v3` | `9d09a38a-0cd6-4d0b-a4cb-498bcbc85396` | `daveey` |
| filler 2 | `escrow-hoarder:v3` | `3ed1facb-5183-48c4-98da-ef84e8281862` | `daveey` |

Ownership confirmed fresh this attempt:

```bash
curl -sS "$BASE/policy-versions?limit=200" -H "Authorization: Bearer $SOFTMAX_TOKEN" \
     -H "User-Agent: coworld-builder/1.0" \
 | jq -r '(if type=="array" then . else .entries end)[]
          |select(.policy_name|startswith("escrow-"))
          |[.policy_name,.policy_version_id,.player_name]|@tsv'
```
```
escrow-hoarder	3ed1facb-5183-48c4-98da-ef84e8281862	daveey
escrow-trader	9d09a38a-0cd6-4d0b-a4cb-498bcbc85396	daveey
escrow-swapper	ab5da062-606a-446b-accb-aeeb899a93a1	daveey-1
escrow-drafter	03aecc7d-d51b-42fd-92b8-2c3199583176	daveey
escrow-hoarder	5ba89854-340c-406d-9eca-a4fe29ad4987	daveey      <- v2 (0.1.1, superseded)
escrow-trader	feea7173-a279-48cc-a2c4-0a9510b5aab7	daveey      <- v2
escrow-swapper	f64ecbe7-1dcc-44d9-aea7-19aa7cc1531e	daveey-1    <- v2
escrow-drafter	bbff274f-ac96-415b-879d-4df6f0c12da5	daveey      <- v2
escrow-hoarder	b07b36d6-c4aa-4dce-b5af-a3dc0f7a6016	daveey      <- v1
escrow-trader	0505950f-bd65-46d4-ac4a-b3d0ad40c11b	daveey      <- v1
escrow-swapper	ae792ad8-75d3-4eb6-aea3-4dfa8548907a	daveey-1    <- v1
escrow-drafter	6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d	daveey      <- v1
```

Shape note carried forward: on this deployment **`/policy-versions` returns a bare array**, not
`{entries:…}` — the playbook's `.entries[]` form errors with
`jq: error (at <stdin>:0): Cannot index array with string "entries"`. Same for `/coworlds`.

Constants used below:

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")   # values never printed
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_cc074076-5938-403e-81db-d278c031db6d
D=div_a8171f6e-62bd-41e5-b470-f15d675faee9
COW=cow_add93c03-c2c9-455e-bc63-d2495fdcd2af
```

Checks 3, 4, 5, 6 and 8 are all evaluated against the **same, latest completed v3 round: round 9**
(`round_3ee96829-8391-4236-b835-c6e3b9c3db4a`, episode request
`ereq_73571e3e-28b4-47aa-8132-ef472f02392e`, replay
`…/7d6b61ae-7b27-400d-b6e2-310d5c848e11.replay`). Round 8 is quoted alongside where the number is
a rate, so the coordinator can see whether round 9 was an outlier. It was not.

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

Fillers were re-registered at the **v3** UUIDs at `2026-08-23T17:17:45Z`
(`runs/2026-08-23-escrow/log.md`: `50/60 filler-policies updated to v3 UUIDs (trader 9d09a38a,
hoarder 3ed1facb); trigger-round issued 2026-08-23T17:17:45Z`). Every round below that carries
both v3 champion UUIDs is therefore post-filler-set by construction.

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" -o rounds.json -w 'http=%{http_code} bytes=%{size_download}\n'
# http=200 bytes=41141   (fetched 2026-08-23T17:49Z)
jq -r '[.entries[]|{round_number,id,status,error,created_at,completed_at,
                    entrants:.round_config.entrant_policy_version_ids}]' rounds.json
```
```json
[
  {
    "round_number": 9,
    "id": "round_3ee96829-8391-4236-b835-c6e3b9c3db4a",
    "status": "completed",
    "error": null,
    "created_at": "2026-08-23T17:43:47.651022Z",
    "completed_at": "2026-08-23T17:47:51.763052Z",
    "entrants": [
      "03aecc7d-d51b-42fd-92b8-2c3199583176",
      "ab5da062-606a-446b-accb-aeeb899a93a1"
    ]
  },
  {
    "round_number": 8,
    "id": "round_946f98fa-b994-40b2-9685-923f0d142bce",
    "status": "completed",
    "error": null,
    "created_at": "2026-08-23T17:28:47.072683Z",
    "completed_at": "2026-08-23T17:32:02.263637Z",
    "entrants": [
      "03aecc7d-d51b-42fd-92b8-2c3199583176",
      "ab5da062-606a-446b-accb-aeeb899a93a1"
    ]
  },
  {
    "round_number": 7,
    "id": "round_6ea4a55e-ddde-4dec-a3d0-78fc26685d32",
    "status": "completed",
    "error": null,
    "created_at": "2026-08-23T17:13:46.110082Z",
    "completed_at": "2026-08-23T17:17:42.261879Z",
    "entrants": [
      "6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d",
      "ae792ad8-75d3-4eb6-aea3-4dfa8548907a"
    ]
  },
  { "round_number": 6, "id": "round_ad8635c6-be79-4e68-931c-b953ea7d5608", "status": "completed",
    "error": null, "created_at": "2026-08-23T16:58:45.387833Z", "completed_at": "2026-08-23T17:02:29.657933Z",
    "entrants": ["6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d","ae792ad8-75d3-4eb6-aea3-4dfa8548907a"] },
  { "round_number": 5, "id": "round_1aaceee5-0fad-42d2-a66c-4f55218ae0fa", "status": "completed",
    "error": null, "created_at": "2026-08-23T16:43:43.249827Z", "completed_at": "2026-08-23T16:46:58.886358Z",
    "entrants": ["6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d","ae792ad8-75d3-4eb6-aea3-4dfa8548907a"] },
  { "round_number": 4, "id": "round_c0c234c2-eb3f-4ab5-9cf5-894f1a4f8127", "status": "completed",
    "error": null, "created_at": "2026-08-23T16:28:42.651720Z", "completed_at": "2026-08-23T16:32:36.295744Z",
    "entrants": ["6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d","ae792ad8-75d3-4eb6-aea3-4dfa8548907a"] },
  { "round_number": 3, "id": "round_89c1c03d-3d38-464f-9412-3bddaad639f4", "status": "completed",
    "error": null, "created_at": "2026-08-23T16:13:42.285154Z", "completed_at": "2026-08-23T16:17:29.643123Z",
    "entrants": ["6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d","ae792ad8-75d3-4eb6-aea3-4dfa8548907a"] },
  { "round_number": 2, "id": "round_13be4cf0-ad75-4954-9514-98480c6f8d07", "status": "completed",
    "error": null, "created_at": "2026-08-23T15:58:41.705932Z", "completed_at": "2026-08-23T16:02:06.236563Z",
    "entrants": ["6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d","ae792ad8-75d3-4eb6-aea3-4dfa8548907a"] },
  {
    "round_number": 1,
    "id": "round_b8f582ac-cc01-44cc-9cd9-49b0c65e108c",
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-23T15:58:00.403567Z",
    "completed_at": "2026-08-23T15:58:00.612338Z",
    "entrants": ["6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d"]
  }
]
```

**Excluded rounds, verbatim.**
- Round 1 — `status: "failed"`, `error: "Temporal RoundWorkflow failed before settling the round."`
  It predates any filler registration (the playbook documents this exact message as what a
  `trigger-round` before the first filler produces) and it seated only one entrant. Does not count.
- Rounds 2–7 — completed, but their `entrant_policy_version_ids` are the **v1** champions
  (`6eb9292a…` / `ae792ad8…`). They predate the v3 submissions (17:17:45Z) and are out of scope
  for this attempt.

**Counted (v3, post-filler-set): round 8 and round 9 — both `status: "completed"`, `error: null`.**

Poll trail (each line also appended to `log.md`, each with a fresh `heartbeat_at` PUT):

```
2026-08-23T17:19:20Z rounds: 7:completed … 1:failed  (completed v3: 0)
2026-08-23T17:24:28Z rounds: 7:completed … 1:failed  (completed v3: 0)
2026-08-23T17:29:22Z rounds: 8:pending(v3) 7:completed …  (completed v3: 0)
2026-08-23T17:34:16Z rounds: 8:completed(v3) 7:completed …  (completed v3: 1)
2026-08-23T17:39:37Z rounds: 8:completed(v3) …  (completed v3: 1)
2026-08-23T17:44:30Z rounds: 9:pending(v3) 8:completed(v3) …  (completed v3: 1)
2026-08-23T17:49:24Z rounds: 9:completed(v3) 8:completed(v3) …  (completed v3: 2)
2026-08-23T17:52:32Z rounds: 9:completed(v3) 8:completed(v3) …  (completed v3: 2)
```

Status: **TRUE** — 2 completed rounds (8, 9) whose entrants are the v3 champions, both created
after the v3 fillers were registered at 17:17:45Z. Wall-clock used: 31 of the 75-minute bound.

---

## 2. Both champions ranked, fillers absent/Baseline — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" -o lb.json -w 'http=%{http_code}\n'   # http=200, 17:49Z
jq . lb.json
```
```json
[
  {
    "rank": 1,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 1010.4553136724522,
    "score_label": "Elo",
    "score_value_type": "integer",
    "rounds_played": 8,
    "episode_wins": 4.0,
    "episodes_played": null,
    "win_rate": 0.5,
    "policy_label": "escrow-swapper:v3",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 989.5446863275478,
    "score_label": "Elo",
    "score_value_type": "integer",
    "rounds_played": 8,
    "episode_wins": 4.0,
    "episodes_played": null,
    "win_rate": 0.5,
    "policy_label": "escrow-drafter:v3",
    "recent_rounds": null
  }
]
```

As TSV, in the checklist's own shape:

```
rank	player_name	policy_label	score	rounds_played	episode_wins
1	daveey-1	escrow-swapper:v3	1010.4553136724522	8	4.0
2	daveey	escrow-drafter:v3	989.5446863275478	8	4.0
```

- `daveey` present, `rounds_played` 8 ≥ 1. ✔
- `daveey-1` present, `rounds_played` 8 ≥ 1. ✔
- Both `policy_label`s now read **`:v3`** — the leaderboard is tracking the remediated policies.
- Fillers (`escrow-trader`, `escrow-hoarder`) are **absent** from the list entirely — the
  permitted outcome (the alternative permitted outcome is a `Baseline…` label; neither filler
  appears at all). ✔
- `rounds_played: 8` is the league-lifetime count (rounds 2–9), not a v3-only count; the API
  exposes no per-version breakdown. The v3-only evidence is check 1's round list plus check 3's
  participant block.

Status: **TRUE**.

---

## 3. Latest v3 round's episode request completed with a replay — **TRUE**

```bash
R=round_3ee96829-8391-4236-b835-c6e3b9c3db4a          # round 9, latest completed v3 round
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}" -w 'http=%{http_code}\n'
```
```
http=200
ereq_73571e3e-28b4-47aa-8132-ef472f02392e	completed	2026-08-23T17:43:47.945615Z
```

```bash
EREQ=ereq_73571e3e-28b4-47aa-8132-ef472f02392e
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/7d6b61ae-7b27-400d-b6e2-310d5c848e11.replay",
  "participants": [
    {
      "position": 0,
      "kind": "policy",
      "policy_version_id": "03aecc7d-d51b-42fd-92b8-2c3199583176",
      "policy_id": "79d30f20-9baa-4356-9a5d-7bbb6c472e6c",
      "policy_name": "escrow-drafter",
      "version": 3,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": false
    },
    {
      "position": 1,
      "kind": "policy",
      "policy_version_id": "ab5da062-606a-446b-accb-aeeb899a93a1",
      "policy_id": "00949333-a6e4-4769-ae42-aaabc9f07d89",
      "policy_name": "escrow-swapper",
      "version": 3,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
      "player_name": "daveey-1",
      "is_filler": false
    },
    {
      "position": 2,
      "kind": "policy",
      "policy_version_id": "3ed1facb-5183-48c4-98da-ef84e8281862",
      "policy_id": "924b1059-bfa2-4f96-8384-0b4754f2105d",
      "policy_name": "escrow-hoarder",
      "version": 3,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": true
    },
    {
      "position": 3,
      "kind": "policy",
      "policy_version_id": "3ed1facb-5183-48c4-98da-ef84e8281862",
      "policy_id": "924b1059-bfa2-4f96-8384-0b4754f2105d",
      "policy_name": "escrow-hoarder",
      "version": 3,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": true
    }
  ],
  "participant_scores": [
    {"position": 0, "score": 110.0},
    {"position": 1, "score": 224.0},
    {"position": 2, "score": 110.0},
    {"position": 3, "score": 110.0}
  ]
}
```

- `status == "completed"` ✔
- `replay_url` non-null ✔
- Seats 0/1 are the two champions at **`version: 3`**, `is_filler: false`, owned by `daveey` and
  `daveey-1` ✔. Seats 2/3 are `is_filler: true`.
- Their display names in the replay are `["daveey","daveey-1","Baseline","Baseline (2)"]`
  (`jq -r '.policyNames' ep.replay`, quoted in check 4) — fillers correctly labelled `Baseline`.

Observation, not a check failure: in round 9 the ladder seated **`escrow-hoarder:v3` in both**
filler seats (positions 2 and 3 share `policy_version_id 3ed1facb…`), where round 8 seated one
hoarder and one trader. Both are registered fillers, so the requirement ("fillers absent or
Baseline") is met either way; recording it because it changes the opposition mix between the two
rounds.

Status: **TRUE**.

---

## 4. Replay bytes are valid and show the game — **FALSE**

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/7d6b61ae-7b27-400d-b6e2-310d5c848e11.replay" \
     -o ep.replay -w 'http=%{http_code} bytes=%{size_download} ctype=%{content_type}\n'
```
```
http=200 bytes=47442 ctype=application/octet-stream
```

```bash
jq -e . ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r 'keys' ep.replay
jq -r '.protocol, .results.reason' ep.replay
```
```
strict UTF-8 JSON: ok
["config","events","names","policyNames","protocol","results"]
escrow.replay.v1
complete
```

`protocol` = `escrow.replay.v1`, matching the manifest. `results.reason` = `complete` — no
`deadline` exception needed.

```bash
jq -r '.results' ep.replay
```
```json
{
  "names": ["daveey","daveey-1","Baseline","Baseline (2)"],
  "scores": [110, 224, 110, 110],
  "hearts": [110, 224, 110, 110],
  "fills": [9, 17, 9, 9],
  "signed": [0, 0, 0, 0],
  "forfeits": [0, 0, 0, 0],
  "profiles": ["Farmer","Factor","Mason","Forester"],
  "turns": 16,
  "maxTurns": 16,
  "heartsMinted": 474,
  "reason": "complete"
}
```

**The fallback count. This is what fails.** Replay events use `kind == "move"` carrying a
`scripted` boolean; there is no `.type`/`.fallback`/`decision` field on this protocol (the
checklist's literal `select(.type=="decision")` / `select(.fallback==true)` both return 0 here —
recorded so the zero is not misread as a pass).

```bash
jq -r '[.events[]|.kind]|group_by(.)|map({(.[0]):length})|add' ep.replay
jq -r '[.events[]|select(.kind=="move")]|group_by(.seat)
        |map({seat:.[0].seat,total:length,scripted:([.[]|select(.scripted==true)]|length)})' ep.replay
```
```json
{"end":1,"expire":14,"fill":33,"give":1,"move":64,"offer":14,"start":1,"turn":16}
```
```json
[
  {"seat": 0, "total": 16, "scripted": 5},
  {"seat": 1, "total": 16, "scripted": 8},
  {"seat": 2, "total": 16, "scripted": 16},
  {"seat": 3, "total": 16, "scripted": 16}
]
```

Seats 2 and 3 are the scripted baselines — `scripted: 16/16` is expected and correct for them.
The champion seats are 0 (`daveey`) and 1 (`daveey-1`):

| round | champion moves | scripted (fell back) | share | log `falling back` lines |
|---|---|---|---|---|
| **9 (latest v3)** | 32 | **13** (seat 0: 5/16, seat 1: 8/16) | **40.6 %** | 13 |
| 8 (first v3) | 32 | **10** (seat 0: 5/16, seat 1: 5/16) | **31.3 %** | 10 |
| 4 (v1, attempt 1) | 32 | 19 | 59.4 % | 19 |

Per-turn map for round 9 (`llm` = the champion's own decision was accepted; `scripted` = it fell
back to the trader baseline):

```
turn	seat0	seat1
0	llm	llm
1	llm	scripted
2	llm	llm
3	scripted	scripted
4	llm	llm
5	scripted	scripted
6	llm	llm
7	scripted	scripted
8	llm	llm
9	scripted	scripted
10	llm	llm
11	scripted	scripted
12	llm	llm
13	llm	scripted
14	llm	scripted
15	llm	llm
```

The non-scripted champion moves **are** substantive — the content requirement is met where the
move survives:

```bash
jq -c '[.events[]|select(.kind=="move" and .scripted==false and .seat<2)][0]' ep.replay
```
```json
{"kind":"move","turn":0,"seat":1,"scripted":false,
 "offer":"OFFER Ratchet\nLOCK 4 ORE\nASK 4 TIMBER\nDUE 1\nIF ALWAYS\nTHEN SWAP\nELSE KEEP",
 "say":"4 ore for 4 timber, fair swap at house price. Sprocket liquidity engine online."}
```
```bash
jq -c '[.events[]|select(.kind=="offer")][0]' ep.replay
```
```json
{"kind":"offer","turn":0,"seat":1,"target":3,"id":"C1",
 "dsl":"OFFER Ratchet\nLOCK 4 ORE\nASK 4 TIMBER\nDUE 1\nIF ALWAYS\nTHEN SWAP\nELSE KEEP",
 "lock":{"ORE":4},"ask":{"TIMBER":4},"due":1,"cond":"ALWAYS","then":"SWAP","else":"KEEP"}
```

**Verdict reasoning.** The remediation moved the number in the right direction (59.4 % → 31.3 % →
40.6 %) but did not clear the bar. The bar for this check is that fallbacks are *a small minority*
of champion decisions — a single-digit percentage, or a handful of moves out of 32. **13 of 32
(40.6 %) is not a small minority**: on the latest v3 round, two of every five champion turns were
played by the scripted trader baseline rather than by the submitted prompt. Round 8's 10/32
(31.3 %) is the better of the two v3 rounds and is still triple the bar. The trend across the two
v3 rounds is flat-to-worse, so round 9 is not an outlier.

Second-order symptom of the same defect: `"signed": [0,0,0,0]` and **zero `sign` and zero `settle`
events** in round 9 (round 8 had 3 signs and 3 settlements). All 14 offers expired unsigned. The
game's headline mechanic — pre-funded contracts settling at DUE — never fires in the latest
episode, because the champions' signing attempts are exactly what the parser keeps rejecting
(see check 5).

Status: **FALSE** — bytes are valid (`strict UTF-8 JSON: ok`, `protocol escrow.replay.v1`,
`results.reason complete`), but 13/32 = 40.6 % of champion moves are scripted fallbacks on the
latest v3 round (31.3 % on round 8). Not a small minority.

---

## 5. Hosted game log is clean — **FALSE**

```bash
curl -sS "$BASE/episode-requests/ereq_73571e3e-28b4-47aa-8132-ef472f02392e/artifacts/logs" \
     "${AUTH[@]}" "${ELEV[@]}" -o logs9.raw -w 'http=%{http_code} bytes=%{size_download}\n'
```
```
http=200 bytes=121378
```

The body is **Python `b'…'` reprs** grouped under `===== container: <name> =====` headers, so a
line-grep of the raw bytes is meaningless (escape sequences are literal `\n` two-character pairs).
Decoded first with `ast.literal_eval` per repr, then grepped:

```python
parts = re.split(r'^===== container: (.+?) =====$', raw, flags=re.M)
for each b'…' repr:  decoded.append(ast.literal_eval(m.group(0)).decode('utf-8','replace'))
```
```
containers: [('coworld-init-config', 0), ('bedrock-sidecar', 110926), ('game', 9911), ('worker', 0)]
```

```python
for p in ['falling back','LLM provider is unavailable','cut off at max_tokens','rejected']:
    hits = [l for l in decoded_text.splitlines() if p in l]
```
```
== falling back : 13
   252: escrow llm: seat 1 falling back to the trader baseline
   269: escrow llm: seat 0 falling back to the trader baseline
   270: escrow llm: seat 1 falling back to the trader baseline
   287: escrow llm: seat 0 falling back to the trader baseline
   288: escrow llm: seat 1 falling back to the trader baseline
   304: escrow llm: seat 0 falling back to the trader baseline
   305: escrow llm: seat 1 falling back to the trader baseline
   320: escrow llm: seat 0 falling back to the trader baseline
   321: escrow llm: seat 1 falling back to the trader baseline
   336: escrow llm: seat 0 falling back to the trader baseline
   337: escrow llm: seat 1 falling back to the trader baseline
   352: escrow llm: seat 1 falling back to the trader baseline
   361: escrow llm: seat 1 falling back to the trader baseline
== LLM provider is unavailable : 0
== cut off at max_tokens : 0
== rejected : 0
```

Not `CLEAN`. The prompt's bar for this check is literally the `|| echo CLEAN` branch, and it does
not fire.

**Which of the four patterns matter, and why.**

- `LLM provider is unavailable` — **0 occurrences**. The platform-wide Bedrock-capacity exception
  in `prompts/60-verify.md` §5 is therefore **not applicable and not invoked**; no cross-check
  against another LLM coworld was needed, because there is nothing to excuse. (Attempt 1 did run
  that cross-check against contagion and raid; both were clean, which is consistent.)
- `cut off at max_tokens` — **0 occurrences**. No `maxOutputTokens` change indicated.
- `rejected` — **0 occurrences** of that literal word.
- `falling back` — **13 occurrences**, one per champion move that the game's own contract parser
  refused. These are the same 13 scripted champion moves counted in check 4 (seat 0: 5, seat 1: 8).
  They are a defect in this coworld's champion prompts, not a platform symptom.

**Cause, from the four lines preceding each fallback.** Each seat gets two attempts; a fallback is
logged only after both are refused:

```
249: escrow llm: seat 0 attempt 0 failed: unfunded: you hold 1 free ORE but LOCK 2
250: escrow llm: seat 1 attempt 0 failed: C1 is not addressed to you
251: escrow llm: seat 1 attempt 1 failed: unfunded: you hold 3 free ORE but LOCK 4
252: escrow llm: seat 1 falling back to the trader baseline
---
266: escrow llm: seat 1 attempt 0 failed: C4 is not addressed to you
267: escrow llm: seat 0 attempt 1 failed: C3 is not addressed to you
268: escrow llm: seat 1 attempt 1 failed: C3 is not addressed to you
269: escrow llm: seat 0 falling back to the trader baseline
270: escrow llm: seat 1 falling back to the trader baseline
---
284: escrow llm: seat 1 attempt 0 failed: C5 is not addressed to you
285: escrow llm: seat 0 attempt 1 failed: C5 is not addressed to you
286: escrow llm: seat 1 attempt 1 failed: C6 is not addressed to you
287: escrow llm: seat 0 falling back to the trader baseline
288: escrow llm: seat 1 falling back to the trader baseline
```

Distribution of all 35 rejected attempts in round 9 (contract ids normalised to `C<n>`):

```
  22  C<n> is not addressed to you
   2  syntax: line 1 must start with OFFER, got "SPROCKET"
   2  input(5, 1) Error: EOF expected
   2  input(8, 1) Error: EOF expected
   2  input(6, 1) Error: EOF expected
   1  unfunded: you hold 1 free ORE but LOCK 2
   1  unfunded: you hold 3 free ORE but LOCK 4
   1  syntax: line 6 must start with THEN, got "THAN"
   1  input(7, 5) Error: ] expected
   1  syntax: line 1 must start with OFFER, got "TINKER"
```

Round 8, same decode, for the rate comparison:

```
== falling back : 10        (seat 0: 5, seat 1: 5)
== LLM provider is unavailable : 0
== cut off at max_tokens : 0
== rejected : 0
attempt-failed lines: 28
  25  C<n> is not addressed to you
   2  you cannot pay the ASK of C<n>
   1  input(4, 1) Error: EOF expected
```

So the remediation **did** fix the two failure modes it targeted — `unfunded` LOCKs are down to 2
of 35 attempts, and the `bad_condition` family is gone — but the dominant one is unchanged:
**`C<n> is not addressed to you`, 22 of 35 attempts (63 %)**. Both champion prompts still try to
SIGN contracts that name a different cog as the counterparty. That is why round 9 ends with
`signed: [0,0,0,0]`.

Also visible in the same log, recorded as an observation rather than a check item — the game
announces one model and the sidecar routes to another:

```
escrow: seats=4 turns=16 talk=true model=claude-sonnet-5
escrow llm: bedrock transport, url http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
```

Identical in round 8's log (lines 210 and 225). This is platform-side routing, not a coworld
defect, but a smaller model is a plausible contributor to the residual DSL illegality and the
coordinator may want it on the record.

Status: **FALSE** — the log is not CLEAN: 13 `falling back` lines on the latest v3 round (10 on
round 8), caused by the champion prompts emitting contract runes the game's parser refuses,
overwhelmingly `is not addressed to you`. Zero `LLM provider is unavailable`, zero
`cut off at max_tokens`, zero `rejected` — no platform exception applies.

---

## 6. The public page uses the static replay path — **TRUE**

**Source A — raw-HTML grep (the checklist's first command).**

```bash
curl -sS "https://softmax.com/escrow" -o page.html -w 'http=%{http_code} bytes=%{size_download}\n'
grep -o '<iframe[^>]*src="[^"]*"' page.html || echo "(no iframe in raw HTML)"
```
```
http=200 bytes=398079
(no iframe in raw HTML)
```

Empty grep = **unknown, not a failure** (`prompts/60-verify.md` §6; `playbooks/observatory-api.md`
§Featured match records the page as client-rendered for the iframe since the lighthouse run).
Falling back.

**Source B — `/coworlds` detail (documented fallback).**

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)[]|select(.name=="escrow")
          |{id,name,version,canonical,replay_viewer,featured_match}'
```
```json
{"id":"cow_add93c03-c2c9-455e-bc63-d2495fdcd2af","name":"escrow","version":"0.1.2","canonical":true,"replay_viewer":null,"featured_match":null}
{"id":"cow_640c000d-b4f8-40f3-8a96-6cc7e753b65a","name":"escrow","version":"0.1.1","canonical":false,"replay_viewer":null,"featured_match":null}
{"id":"cow_65c18d00-ccaf-4259-bcaa-9046e7072ca9","name":"escrow","version":"0.1.0","canonical":false,"replay_viewer":null,"featured_match":null}
```

The **v0.1.2** coworld `cow_add93c03-…` is the one flagged `canonical: true`; 0.1.1 and 0.1.0 are
demoted. `featured_match: null` is platform-wide behaviour (documented), so B is not evidence
either way for the featured match.

**Source C — the page's SSR payload `state.playlist[0]` — this is the featured match (used).**

```bash
curl -sS "https://softmax.com/escrow" -o page.html      # http=200, 398079 bytes, fetched 17:50Z
python3 -c '…locate "\"playlist\":[" and un-escape…'
```
```json
"playlist":[{"episodeId":"52737c53-ee89-407c-a949-9e5bfb0cb880",
"coworldId":"cow_add93c03-c2c9-455e-bc63-d2495fdcd2af","coworldName":"escrow",
"coworldVersion":"0.1.2",
"replayUrl":"https://softmax-public.s3.amazonaws.com/replays/7d6b61ae-7b27-400d-b6e2-310d5c848e11.replay",
"finishedAt":"2026-08-23T17:47:41.650252Z","roundNumber":9,"episodeNumber":1,
"code":"escrow.r9.e1","matchup":{"divisionId":"div_a8171f6e-62bd-41e5-b470-f15d675faee9",
"divisionName":"Competition",
"first":{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
 "score":1010.4553136724522,"score_label":"Elo","rounds_played":8,"episode_wins":4,"win_rate":0.5,
 "policy_label":"escrow-swapper:v3"},
"second":{"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
 "score":989.5446863275478,"score_label":"Elo","rounds_played":8,"episode_wins":4,"win_rate":0.5,
 "policy_label":"escrow-drafter:v3"}},
"inspectUrl":"/observatory/v2?tab=episode-requests&detail=episode-request:ereq_73571e3e-28b4-47aa-8132-ef472f02392e",
"outcome":"first"}]
```

A featured match **is** present and it is **not stale**: `coworldId` is the **new**
`cow_add93c03-…`, `coworldVersion` `0.1.2`, `code` `escrow.r9.e1`, `replayUrl` the round-9 replay,
`inspectUrl` the round-9 episode request, and both `matchup` slots carry `:v3` policy labels. No
re-poll was needed — this was correct on the first attempt.

**Source D — the iframe `src` itself, from the call the page's own JS makes (used).**

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_add93c03-c2c9-455e-bc63-d2495fdcd2af",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/7d6b61ae-7b27-400d-b6e2-310d5c848e11.replay"}'
```
```
http=200
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_add93c03-c2c9-455e-bc63-d2495fdcd2af/sha256%3A292118f0112c0ef747617316fad320f856766bced2e6e8f2d793a5aa2272764e/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F7d6b61ae-7b27-400d-b6e2-310d5c848e11.replay&v=2",
  "ready": true
}
```

- Path shape: `…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` ✔
- `<cow_id>` = `cow_add93c03-c2c9-455e-bc63-d2495fdcd2af` — the **new** coworld ✔ (not the
  superseded `cow_65c18d00…`)
- `<sha>` = `sha256:292118f0112c0ef747617316fad320f856766bced2e6e8f2d793a5aa2272764e` URL-encoded,
  which is exactly `STATE.coworld.manifest_sha` ✔
- `ready: true` ✔
- No `/client/replay` pod URL anywhere in the response ✔

Status: **TRUE** — sources used: **C** (SSR `state.playlist[0]`) for the featured match and **D**
(`POST /coworlds/replays/session`) for the iframe `src`. A found nothing (client-rendered), B's
`featured_match` is null platform-wide. Static route confirmed against the new cow_id on attempt 1
of 3.

---

## 7. Certification declared the static bundle — **TRUE**

Source: the **committed** `runs/2026-08-23-escrow/release-result.json` — the artifact phase 40
downloaded for the **v0.1.2** release (`STATE.coworld.release_run_id = 32653621867`, repo
`Metta-AI/cogame-escrow`). It was already present in the working tree, so **no `gh run download`
re-fetch was needed**, and `/tmp` was not consulted.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-23-escrow/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Contains the required literal `Replay liveness: skipped (static replay bundle declared`. ✔

Corroborating tail from the same committed file (`.certify.output_tail`, excerpt):

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
…
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

```bash
jq -r '.ok' runs/2026-08-23-escrow/release-result.json
```
```
true
```

Status: **TRUE** — read from the **committed** `runs/2026-08-23-escrow/release-result.json`
(v0.1.2, release run `32653621867`), not from `/tmp` and not re-downloaded.

---

## 8. Spectator judgment — **TRUE** (both stated conditions hold; see the legibility caveat)

### (a) The viewer was EXECUTED in a real browser, in CI — fresh dispatch this attempt

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_add93c03-c2c9-455e-bc63-d2495fdcd2af/sha256%3A292118f0112c0ef747617316fad320f856766bced2e6e8f2d793a5aa2272764e/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F7d6b61ae-7b27-400d-b6e2-310d5c848e11.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
sleep 10
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:3][]|"\(.databaseId)\t\(.createdAt)\t\(.status)"'
```
```
32656128193	2026-08-23T17:50:31Z	in_progress
32654376748	2026-08-23T17:17:53Z	completed
32652062253	2026-08-23T16:34:03Z	completed
```

The run I use is **32656128193**, created 17:50:31Z — after my dispatch. (The 16:34Z run
`32652062253` is attempt 1's, against the **old** cow's replay, and is explicitly not reused; the
17:17Z run `32654376748` is not mine either.)

```bash
gh run view 32656128193 -R Metta-AI/coworld-builder --json status,conclusion
```
```json
{"conclusion":"success","status":"completed"}
```

```bash
gh run download 32656128193 -R Metta-AI/coworld-builder -n viewer-check \
   -D runs/2026-08-23-escrow/viewer-check/round9-32656128193
ls -la runs/2026-08-23-escrow/viewer-check/round9-32656128193
```
```
-rw-r--r-- 1 root root      0 smoke-stderr.txt
-rw-r--r-- 1 root root    311 smoke-stdout.txt
-rw-r--r-- 1 root root   1113 viewer-smoke.json
-rw-r--r-- 1 root root 375637 viewer-smoke.png
```

### (b) The readouts, verbatim

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-23-escrow/viewer-check/round9-32656128193/viewer-smoke.json
```
```json
{"loaded":true,"ms":3034,"clock":"TURN 0","scorebug":"","feed_lines":0}
```

```bash
jq -c '.signals' runs/2026-08-23-escrow/viewer-check/round9-32656128193/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```

```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-23-escrow/viewer-check/round9-32656128193/viewer-smoke.json
```

| scrub position | clock readout |
|---|---|
| 0 % | `TURN 0` |
| 50 % | `TURN 0 / 16 · WAITING ON 4` |
| 100 % | `TURN 16 / 16 · FINAL` |

```bash
jq -r '.failure // "no failure"' runs/2026-08-23-escrow/viewer-check/round9-32656128193/viewer-smoke.json
jq -r '.console_tail[]' …
```
```
no failure
[bridge] loading
[bridge] ready
```

**Both TRUE conditions:**
1. `loaded: true`, with `data_replay_loaded: "true"` **and** the `coworld-replay` bridge reporting
   `ready` (`bridge_ready: true`, `bridge_error: []`). ✔
2. The three clock readouts **differ** (`TURN 0` → `TURN 0 / 16 · WAITING ON 4` →
   `TURN 16 / 16 · FINAL`). The replay advances; the 100 % readout is the terminal frame. ✔

**Known shell-probe gap, recorded the same way attempt 1 recorded it:** `scorebug: ""` and
`feed_lines: 0` under the workflow's generic probes. This is a selector mismatch in the generic
probe, not an empty page — the shell's own `index.html` (fetched below) defines `#scorebug` and
`#feed`, and the screenshot plainly shows a populated four-cog scorebug strip and say-bubbles.
Recording it as a probe gap, not as evidence of absence.

### (c) Supporting fetches — the bundle the browser executed

Even though (a) is the authoritative evidence, the asset table is recorded because it pins which
bytes the browser ran. `BASEV` = `…/static/cow_add93c03-…/sha256%3A292118f0…`.

```bash
curl -sS "$BASEV/index.html?replay=…" -o index.html -w '…'
grep -oE '<script[^>]*src="[^"]*"|<link[^>]*href="[^"]*"' index.html
```
```
<link rel="stylesheet" href="./chrome.css"
<script src="./renderer.js"
<script src="./escrow_replay.js"
<script src="./static_replay.js"
```

| URL (relative to `BASEV/`) | HTTP | bytes | content-type |
|---|---|---|---|
| `index.html?replay=…` | 200 | 1 507 | text/html |
| `chrome.css` | 200 | 12 687 | text/css; charset=utf-8 |
| `renderer.js` | 200 | 52 196 | text/javascript; charset=utf-8 |
| `escrow_replay.js` | 200 | 11 403 | text/javascript; charset=utf-8 |
| `static_replay.js` | 200 | 6 591 | text/javascript; charset=utf-8 |
| `escrow_replay.wasm` | 200 | 198 110 | application/wasm |

All 200, all non-trivial, none an HTML error page. The `.wasm` name comes from the emscripten
loader in `escrow_replay.js`: `function findWasmBinary(){return locateFile("escrow_replay.wasm")}`,
and the fetched bytes verify as `WebAssembly (wasm) binary module version 0x1 (MVP)`.

Bridge markers in the fetched `static_replay.js`:

```
34:    var envelope = { src: "coworld-replay", type: type };
134:        tell("ready");
```

### (d) The replay JSON the viewer was asked to draw

Early:

```
turn	seat	kind	text
	 	start
0		turn
0	0	move
0	1	move	4 ore for 4 timber, fair swap at house price. Sprocket liquidity engine online.
0	2	move
0	3	move
0	1	offer
0	0	fill
0	2	fill
0	3	fill
1		turn
1	0	move	Need grain for commissions. Offering timber+ore for grain at fair rates.
1	1	move
1	2	move
1	3	move
1	0	offer
1	1	expire
1	1	fill
2		turn
2	0	move	Buying 2 grain from Ratchet to fill commissions next turn.
2	1	move	4 ore for 4 timber, fair swap at 2.0 hearts each.
2	0	offer
2	1	offer
2	0	expire
2	2	fill
2	3	fill
```

Middle:

```
11	0	move	OFFER Tinker ⏎ LOCK 6 GRAIN ⏎ ASK 6 ORE ⏎ DUE 12 ⏎ IF ALWAYS ⏎ THEN SWAP ⏎ ELSE KEEP
11	0	offer
11	1	expire
11	1	fill
12	0	move	C12 addressed to Tinker, not me. Sitting tight, need 2 more ore + 1 timber for final 2 commissions.
12	1	move	4 ore for 4 timber, need timber to close commissions
12	1	offer
12	0	expire
12	0	fill
13	0	move	Offering grain for ore to close final commissions. Need 2 ore + 1 timber before turn 16.
13	0	give
13	0	offer
13	1	expire
```

Late:

```
14	0	move	C14 was my offer to Tinker; waiting for their decision. Need 2 ore + 2 timber for final 2 commissions.
14	0	expire
14	0	fill
14	1	fill
14	2	fill
14	3	fill
15	0	move	Final turn: converting grain to hearts. No new contracts.
15	1	move	Final turn: filling 2 commissions for the horizon. 3 ore + 3 grain + 3 timber + 212 hearts locked in.
15	1	fill
16		end
```

```bash
jq -r '.results' ep.replay      # (pasted in full under check 4)
# scores [110,224,110,110]  fills [9,17,9,9]  signed [0,0,0,0]  heartsMinted 474  reason "complete"
```

### The spectator-judgment paragraph

The viewer works. The screenshot (`viewer-check/round9-32656128193/viewer-smoke.png`) shows the
starter's chrome unmistakably: the `ES**CROW**` wordmark top-left in the same two-tone treatment
as paintbot/raid/hive, `TURN 16 / 16 · FINAL` centred in the top band, a `REPLAY` chip and a
`« LOG` toggle top-right; below it a four-column scorebug reading
`daveey 110 FARMER 1/93/1 · daveey-1 224 FACTOR 1/1/1 · Tinker 110 MASON 99/7/1 · Ratchet 110 FORESTER 1/1/99`;
a four-quadrant table of cog avatars each with its hearts count, stock bars and a say-bubble
(`"Final turn: converting grain to hearts. No new contracts."` over `daveey`); an `ESCROW BOARD`
panel centre; and at the bottom the transport strip — scrubber with the coloured per-event momentum
graph, play button, `144 / 144` position counter. Over the board sits the endcard:
`FINAL — 16 TURNS · 474 HEARTS MINTED / daveey-1 — MOST HEARTS AT HORIZON`, ranking
1 daveey-1 (Factor, 224 hearts, 17 fills), 2 daveey (Farmer, 110, 9), 3 Tinker (Mason, 110, 9),
4 Ratchet (Forester, 110, 9). Every number reconciles exactly with `results` in the replay JSON.
This is the starter's product, not a look-alike rewrite — no cogame-gridlock problem here. It is
legible: a spectator can read who is playing, what each cog holds, who is winning and by how much,
and the clock advances (three differing scrub readouts, terminal frame at 100 %).

**The caveat, and it is a real one.** What the picture *shows* is a weaker game than the design
promises, and it shows it honestly. The endcard's `SIGNED` column reads **0 for all four cogs**,
and the event stream bears that out: 14 offers posted, **14 expired, 0 signed, 0 settled**. The
whole premise of escrow — pre-funded contracts whose ELSE branch fires at DUE, the loophole game —
never happens in this episode. What a spectator actually watches is four cogs filling their own
commissions in parallel while a stream of offers goes up and quietly lapses. That is a direct
consequence of check 4/5's failure: the champions' SIGN attempts are the exact thing the parser
keeps rejecting (`C<n> is not addressed to you`, 22 of 35 attempts), so every offer dies unsigned
and the fallback trader baseline that replaces the champion's turn does not sign either. Round 8
was better on this axis (3 signs, 3 settlements) but is worse on nothing else. I am marking item 8
TRUE because both of its stated conditions hold — the viewer drew a frame, said `ready`, and
advanced — and because the viewer is not what is broken. The emptiness of the contract layer is
check 4 and check 5's failure, counted there, and it should not be double-counted or hidden here.

Status: **TRUE** on `prompts/60-verify.md` §8's two conditions (`loaded: true`; three differing
clocks), with the contract-layer legibility caveat above recorded for the judge.

---

## Summary table

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set (v3) | **TRUE** — rounds 8, 9 |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey-1 `:v3` rank 1, daveey `:v3` rank 2 |
| 3 | Latest v3 round's episode request completed with replay | **TRUE** — `ereq_73571e3e…`, both champions seated |
| 4 | Replay bytes valid and show the game | **FALSE** — 13/32 (40.6 %) champion moves scripted |
| 5 | Hosted game log clean | **FALSE** — 13 `falling back` lines |
| 6 | Public page uses the static replay path | **TRUE** — static route on the new cow_id, `ready:true` |
| 7 | Certification declared the static bundle | **TRUE** — committed `release-result.json` |
| 8 | Spectator judgment | **TRUE** — `loaded:true`, 3 differing clocks (caveat recorded) |

**Not all-TRUE.** Checks 4 and 5 remain false, with a single shared root cause, unchanged in kind
from attempt 1 but reduced in degree: both champion prompts still emit contract runes the game's
parser refuses, dominated by **SIGN of a contract addressed to another cog**
(`C<n> is not addressed to you` — 22 of 35 rejected attempts in round 9, 25 of 28 in round 8).
The remediation fixed the `unfunded LOCK` and `bad_condition` families it targeted and cut the
fallback share from 59.4 % to 31–41 %, but the addressing rule is still not being obeyed.

## What was actually fixed, and what was not

| failure mode (attempt 1) | attempt 2 status |
|---|---|
| `unfunded: you hold N free X but LOCK M` | largely fixed — 2 of 35 attempts (r9), 0 (r8) |
| `bad_condition` / IF-grammar errors | fixed — 0 occurrences in either v3 round |
| `cut off at max_tokens` | still 0 — never was the problem |
| `LLM provider is unavailable` | still 0 — not a platform-capacity run |
| **`C<n> is not addressed to you`** | **not fixed — 22/35 (r9), 25/28 (r8), the dominant cause** |
| `syntax: line 1 must start with OFFER, got "<COGNAME>"` | new/residual — 3 of 35 (r9) |
| `input(N, 1) Error: EOF expected` | residual — 6 of 35 (r9), 1 of 28 (r8) |

The addressing rule is the one that matters, because it is also the rule that stops any contract
from ever being signed (`signed: [0,0,0,0]` in round 9). A prompt fix targeting it specifically —
"only SIGN a contract whose OFFER line names **you**; if none is addressed to you, post your own
offer or pass" — is what the next remediation needs, along with the trailing-token/EOF hygiene
(`syntax: line 1 must start with OFFER, got "SPROCKET"` is the model prefixing its rune with the
target's name; `EOF expected` is trailing prose after `ELSE KEEP`).

## Retry log

| check | attempts | outcome |
|---|---|---|
| 1 | 8 polls, 17:19Z → 17:52Z | TRUE at poll 7 (17:49Z), 31 min of the 75-min bound |
| 3 | 1 | TRUE first try |
| 4 | 2 (round 9 latest; round 8 cross-read) | FALSE on both v3 rounds — not an outlier |
| 5 | 2 (round 9 latest; round 8 cross-read) | FALSE on both v3 rounds; platform exception not applicable (0 `LLM provider is unavailable`) |
| 6 | 1 (of the 3 allowed for staleness) | TRUE first try — featured match already on the new cow_id |
| 7 | 1 | TRUE — committed file present, no re-download |
| 8 | 1 dispatch (`32656128193`) | TRUE |

## API shapes observed this attempt (deviations worth carrying forward)

- `/policy-versions?limit=200` and `/coworlds?limit=200` both return **bare arrays** on this
  deployment, not `{entries:…}`. The playbook's `.entries[]` form errors. `/rounds` and
  `/episode-requests` do wrap in `entries`.
- `episode-requests/<id>/artifacts/logs` returns Python `b'…'` reprs under
  `===== container: <name> =====` headers. A raw line-grep is meaningless — decode each repr
  (`ast.literal_eval` → `.decode('utf-8')`) before grepping. Containers seen:
  `coworld-init-config` (empty), `bedrock-sidecar`, `game`, `worker` (empty).
- Escrow replay events carry `kind` + a `scripted` boolean; there is **no** `.type=="decision"`
  and **no** `.fallback` field. The checklist's literal jq filters return 0 on this protocol and
  that 0 must not be read as "no fallbacks".
- The game log announces `model=claude-sonnet-5` while the bedrock sidecar URL routes to
  `us.anthropic.claude-haiku-4-5-20251001-v1:0`. Observed in both v3 rounds.

---

## Appendix — attempt 1 (2026-08-23T16:02–16:43Z), superseded

Attempt 1 verified the **v0.1.0** coworld (`cow_65c18d00-ccaf-4259-bcaa-9046e7072ca9`) and the
**v1** champions (`escrow-drafter:v1` / `escrow-swapper:v1`) over rounds 2, 3 and 4. It returned
6 TRUE / 2 FALSE with the same two failing checks: check 4 (champion fallback share 59 % on round
4, 47 % on round 3, 56 % on round 2) and check 5 (19 `falling back` lines, caused by unfunded
LOCKs, `is not addressed to you`, `bad_condition` and EOF errors; 0 `LLM provider is unavailable`,
cross-checked clean against contagion and raid, so not a platform cause). Checks 1, 2, 3, 6, 7 and
8 were TRUE there too, against the old cow_id and the old viewer-check run `32652062253`
(artifacts retained under `viewer-check/` and `viewer-check/round3-32651276492/`). Every figure in
the eight checks above was re-fetched this attempt; nothing from attempt 1 is relied on.
