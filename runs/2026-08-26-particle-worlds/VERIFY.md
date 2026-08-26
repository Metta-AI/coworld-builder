# VERIFY — particle-worlds   (2026-08-26T14:17Z)

Verdict: **all-true** (8/8), with check 5 satisfied on SPEC item 5's **documented
platform-wide-cause branch**, cross-checked against another LLM coworld, and check 4 read through
the **design-declared substitute** for a binary replay (`tools/replay_summary.py`).

Run: `2026-08-26-particle-worlds` · slug `particle-worlds` · coworld
`cow_039ad60d-ae1f-4098-ab1d-4f0144e32198` v`0.1.2` ·
league `league_2ae87c04-15f1-4116-ad6d-54e0d656ea49` ·
division `div_4e1ddbbe-b6d4-409d-82b9-23e1142268d0`.

Every call below was made **this phase** (13:44Z–14:11Z), with
`BASE=https://softmax.com/api/observatory/v2`. Headers are named, never their values:
`Authorization: Bearer …` + `User-Agent: coworld-builder/1.0` on every read, plus
`X-Use-Elevated-Privileges: true` where noted. The only exceptions to "fetched fresh this phase"
are the two the prompt allows: check 7 (the committed `release-result.json` from phase 40) and
check 8 (the artifact of the `viewer-check.yml` run **I dispatched at 14:05:37Z this phase**).

**Response-shape forms actually used** (the brief warned both shapes exist):

| Endpoint | Shape observed **today, this phase** | Accessor used |
|---|---|---|
| `GET /rounds?league_id=` | **object** `{entries,limit,offset,total_count}` | `if type=="array" then . else .entries end` |
| `GET /coworlds?limit=200` | **bare array** | same dual-shape jq |
| `GET /divisions/<d>/leaderboard` | **bare array** | `.[]` |
| `GET /rounds/<r>/episode-requests` | **object** `{entries,…}` | dual-shape jq |
| `GET /episode-requests?round_id=` | **HTTP 405** (see check 3) | nested route instead |

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

```
GET $BASE/rounds?league_id=league_2ae87c04-15f1-4116-ad6d-54e0d656ea49&limit=20
  headers: Authorization, User-Agent                                  (fetched 14:06:03Z)
→ HTTP 200 ; jq -r 'type' → "object" ; keys → entries,limit,offset,total_count
```

```json
[
  {
    "id": "round_bdc26d0f-7ca6-4ef1-be3e-c7b4c6a2f5f6",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-26T13:55:23.378345Z",
    "completed_at": "2026-08-26T14:02:03.394080Z",
    "entrants": [
      {"policy_version_id": "518d85d8-0599-407d-8b4c-ec6771590a06"},
      {"policy_version_id": "34b5236f-9158-4121-acf6-9e19f910c3a0"}
    ]
  },
  {
    "id": "round_f889f1ab-62a9-4276-bc72-c7fa3e4ddd37",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-26T13:40:21.389202Z",
    "completed_at": "2026-08-26T13:47:30.283126Z",
    "entrants": [
      {"policy_version_id": "518d85d8-0599-407d-8b4c-ec6771590a06"},
      {"policy_version_id": "34b5236f-9158-4121-acf6-9e19f910c3a0"}
    ]
  },
  {
    "id": "round_46e3ef36-e9fe-4a80-a8b2-8efad6c03ef0",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-26T13:40:00.465519Z",
    "completed_at": "2026-08-26T13:40:01.514894Z",
    "entrants": [
      {"policy_version_id": "518d85d8-0599-407d-8b4c-ec6771590a06"}
    ]
  }
]
```

(`entrant_attributions` carries `policy_version_id` only — `player_name` and `policy_name` are
`null` on every row in this response; `518d85d8…` is `particle-worlds-swarm:v2` and `34b5236f…` is
`particle-worlds-cipher:v2`, resolved from the episode-request detail in check 3.)

**Round 1's error, verbatim, and it does NOT count:**

> `"Temporal RoundWorkflow failed before settling the round."`

Rounds `completed`: **2** — `round_number` **2** and **3**. Failed: round 1 (excluded).

**That both counted rounds are after the fillers were set** is proven by the fillers *being seated
in them*, not by a log line:

```
GET $BASE/leagues/league_2ae87c04-.../filler-policies
  headers: Authorization, User-Agent, X-Use-Elevated-Privileges       (fetched 14:06:12Z)
→ HTTP 200
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"2239256d-0c3e-4543-a956-f60549c605a0","policy_name":"particle-worlds-drifter","version":2,"player_name":"daveey"},
 {"policy_version_id":"5ad38c6d-db4d-4b36-ba16-39748edfe5e2","policy_name":"particle-worlds-beeline","version":2,"player_name":"daveey"}]}
```

- Round 2's episode seated `particle-worlds-drifter:v2` at positions 2 and 3 with
  `"is_filler": true` (pasted in check 2's cross-reference below).
- Round 3's episode seated `particle-worlds-beeline:v2` at positions 2 and 3 with
  `"is_filler": true` (pasted in check 3).
- Round 1 failed at **13:40:01.514894Z** with exactly the message
  `playbooks/observatory-api.md` §6 attributes to a `trigger-round` issued *before any filler
  exists*; round 2 was created **13:40:21.389202Z**, 20 s later, and settled with fillers seated.
  So registration landed between 13:40:01Z and 13:40:21Z — before **both** counted rounds.
  (`log.md`'s coarser phase-50 line stamps it `13:41:39Z`; the API timestamps above are the finer
  evidence and they agree on the ordering.)

Status: **TRUE** — rounds 2 and 3 completed at 13:47:30Z and 14:02:03Z, both with fillers already
registered and actually seated; round 1's failure is recorded verbatim and excluded.

**Note on "latest round" for checks 3–8.** A confirming re-poll at **14:16:22Z** showed
`4 pending / 3 completed / 2 completed / 1 failed` — a round 4 had been created after my
verification pass and had not settled. Checks 3–8 all pin **round 3**
(`round_bdc26d0f-…` / `ereq_be89daa4-…` / replay `1ae313cc-…`), which was the latest **completed**
round when they ran at 14:06–14:07Z, and the featured match (check 6), the static `src` and the
executed viewer (check 8) are all that same episode. Nothing here rests on round 4.

---

## 2. Both champions ranked, fillers absent — **TRUE**

```
GET $BASE/divisions/div_4e1ddbbe-b6d4-409d-82b9-23e1142268d0/leaderboard
  headers: Authorization, User-Agent                                  (fetched 14:06:12Z)
→ HTTP 200 ; jq -r 'type' → "array"   (bare list, not .entries)
```

```json
[{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
  "score":1030.5304984710244,"score_label":"MMR","score_value_type":"integer",
  "rounds_played":2,"episode_wins":2.0,"episodes_played":null,"win_rate":1.0,
  "policy_label":"particle-worlds-cipher:v2","recent_rounds":null},
 {"rank":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
  "score":969.4695015289755,"score_label":"MMR","score_value_type":"integer",
  "rounds_played":2,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,
  "policy_label":"particle-worlds-swarm:v2","recent_rounds":null}]
```

`jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'`:

```
1	daveey-1	particle-worlds-cipher:v2	1030.5304984710244	2	2.0
2	daveey	particle-worlds-swarm:v2	969.4695015289755	2	0.0
```

- `daveey` present, `rounds_played` **2** ✓
- `daveey-1` present, `rounds_played` **2** ✓
- Exactly **two rows**: the two filler policies (`particle-worlds-drifter:v2`,
  `particle-worlds-beeline:v2`) are **absent** from the leaderboard ✓
- Where the fillers *are* named — the replay's own roster — they carry the platform's Baseline
  labels: `jq -c '.names' /tmp/ep.json` → `["daveey","daveey-1","Baseline","Baseline (2)"]` ✓

Cross-reference for check 1 (round 2's episode, fetched 13:49:0xZ this phase,
`GET $BASE/episode-requests/ereq_8090183a-d104-431f-a0af-13a236f47fcf`):

```json
"participants": [
 {"position":0,"policy_name":"particle-worlds-swarm","version":2,"player_name":"daveey","is_filler":false},
 {"position":1,"policy_name":"particle-worlds-cipher","version":2,"player_name":"daveey-1","is_filler":false},
 {"position":2,"policy_name":"particle-worlds-drifter","version":2,"player_name":"daveey","is_filler":true},
 {"position":3,"policy_name":"particle-worlds-drifter","version":2,"player_name":"daveey","is_filler":true}]
```

Status: **TRUE** — both champions ranked with `rounds_played 2`; fillers absent from the
leaderboard and labelled `Baseline` / `Baseline (2)` in the replay roster.

---

## 3. Latest round's episode request completed with a replay — **TRUE**

Latest completed round = `round_bdc26d0f-7ca6-4ef1-be3e-c7b4c6a2f5f6` (round 3, the `max_by(.round_number)`
of the completed set in check 1).

The flat route the prompt lists is dead platform-wide today; I recorded the failure and used the
nested `0.1.43`-client route the playbook documents:

```
GET $BASE/episode-requests?round_id=round_bdc26d0f-...&limit=20
  headers: Authorization, User-Agent                                  (fetched 14:06:23Z)
→ HTTP 405
{"detail":"Method Not Allowed"}
```

```
GET $BASE/rounds/round_bdc26d0f-7ca6-4ef1-be3e-c7b4c6a2f5f6/episode-requests
  headers: Authorization, User-Agent                                  (fetched 14:06:23Z)
→ HTTP 200 ; jq -r 'type' → "object" (.entries)
```
```json
[{"id":"ereq_be89daa4-b8a2-4941-93b7-68a7423a79bb","status":"completed",
  "coworld_id":"cow_039ad60d-ae1f-4098-ab1d-4f0144e32198",
  "round_id":"round_bdc26d0f-7ca6-4ef1-be3e-c7b4c6a2f5f6",
  "replay_url":"https://softmax-public.s3.amazonaws.com/replays/1ae313cc-0f99-450d-aaf4-21bdc8688cc8.replay",
  "policy_version_ids":["518d85d8-0599-407d-8b4c-ec6771590a06","34b5236f-9158-4121-acf6-9e19f910c3a0",
                        "5ad38c6d-db4d-4b36-ba16-39748edfe5e2","5ad38c6d-db4d-4b36-ba16-39748edfe5e2"],
  "created_at":"2026-08-26T13:55:23.773088Z"}]
```

```
GET $BASE/episode-requests/ereq_be89daa4-b8a2-4941-93b7-68a7423a79bb
  headers: Authorization, User-Agent                                  (fetched 14:06:29Z)
→ HTTP 200 ; jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/1ae313cc-0f99-450d-aaf4-21bdc8688cc8.replay",
  "participants": [
    {"position":0,"policy_name":"particle-worlds-swarm","version":2,"player_name":"daveey","is_filler":false},
    {"position":1,"policy_name":"particle-worlds-cipher","version":2,"player_name":"daveey-1","is_filler":false},
    {"position":2,"policy_name":"particle-worlds-beeline","version":2,"player_name":"daveey","is_filler":true},
    {"position":3,"policy_name":"particle-worlds-beeline","version":2,"player_name":"daveey","is_filler":true}
  ],
  "participant_scores": [
    {"position":0,"score":0.524},{"position":1,"score":0.904},
    {"position":2,"score":0.73},{"position":3,"score":0.502}
  ]
}
```

Status: **TRUE** — `status "completed"`, non-null `replay_url`, position 0 = `daveey`
(`particle-worlds-swarm:v2`), position 1 = `daveey-1` (`particle-worlds-cipher:v2`), both
`is_filler: false`; positions 2–3 are the scripted filler `particle-worlds-beeline:v2` with
`is_filler: true`, which the replay roster names `Baseline` / `Baseline (2)`.

---

## 4. Replay bytes valid and showing the game — **TRUE**

The particle-worlds replay is the starter's **binary `COWLDMPE`** format, so `jq .` on the raw
bytes fails by design. `design.md` §Replay bytes lines 1059–1072 declares the substitute verbatim —
**"The phase-60 substitute for SPEC §Definition of done check 4"** — namely
`python3 tools/replay_summary.py`, which prints **one strict-UTF-8 JSON object** to stdout. I used
that. Repo checkout `/workspace/cogame-particle-worlds` at `main` = `543c5a8`, confirmed against
`origin/main` by `git fetch origin main` this phase (working tree clean).

```
curl -sSL https://softmax-public.s3.amazonaws.com/replays/1ae313cc-0f99-450d-aaf4-21bdc8688cc8.replay \
     -o /tmp/ep.replay                                               (fetched 14:06:37Z)
→ HTTP 200  bytes 130673  content_type application/octet-stream

head -c 40 /tmp/ep.replay | od -c
0000000   C   O   W   L   D   M   P   E 001  \0 017  \0   p   a   r   t
0000020   i   c   l   e   -   w   o   r   l   d   s 001  \0   2   h 274
0000040   Z   > 240 001  \0  \0   N  \a

python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
→ strict UTF-8 JSON: ok

jq -r '.protocol, .gameVersion, .results.reason, .results.endRule, .results.roundsPlayed' /tmp/ep.json
→ particle-worlds/v1
   2
   complete
   full_time
   4
```

`protocol == "particle-worlds/v1"` is the value the manifest's own docs/protocol text and
`design.md` line 1068 require, and it matches the binary header's game name `particle-worlds`
above. `results.reason == "complete"` with `endRule == "full_time"` — the **normal** path; the
`deadline` exception `design.md` line 389 declares acceptable was **not needed**.

The full results document, decoded from the `result` control record **inside the S3 bytes** (the
bytes are self-sufficient):

```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],
 "scores":[0.524,0.904,0.73,0.502],"win":[true,true,true,true],
 "alias":["RED-alpha","BLUE-alpha","GREEN-alpha","YELLOW-alpha"],
 "colour":["red","blue","green","yellow"],
 "roles":[["cooperator","adversary","listener","pursuer"],
          ["cooperator","good","eavesdropper","pursuer"],
          ["cooperator","good","eavesdropper","evader"],
          ["cooperator","good","speaker","pursuer"]],
 "roundScores":[[0.974,0.044,0.081,1.0],[0.974,0.955,0.689,1.0],
                [0.974,0.955,0.918,0.074],[0.974,0.955,0.081,0.0]],
 "coverPct":[97,0,0,0],"bumps":[0,0,0,0],"tagTicks":[0,0,0,1000],"goalHits":[0,1,2,0],
 "llmTurns":[38,36,0,0],"fallbackTurns":[2,4,0,0],
 "modes":["spread","deceive","crypto","tag"],"roundTicks":[1080,1080,1080,1080],
 "roundEndRules":["full_time","full_time","full_time","full_time"],"roundsPlayed":4,
 "reason":"complete","endRule":"full_time","games":4,"finalTick":5038,"seed":280169914}
```

The four seat means reproduce `participant_scores` from check 3 exactly
(`mean(roundScores[0]) = 0.52475 → 0.524`, `[1] = 0.9048 → 0.904`, `[2] = 0.73025 → 0.73`,
`[3] = 0.5025 → 0.502`), so the hosted scores and the bytes agree.

**Champion seats are non-scripted, and not all fallbacks.** Directive sources by seat
(`jq` over `.directives[]`):

```json
[{"seat":0,"n":40,"llm":38,"scripted":0,"fallback":2},
 {"seat":1,"n":40,"llm":36,"scripted":0,"fallback":4},
 {"seat":2,"n":40,"llm":0, "scripted":40,"fallback":0},
 {"seat":3,"n":40,"llm":0, "scripted":40,"fallback":0}]
```

- Seats 0/1 are the champions: **74 of 80 directives (92.5 %) `llm`**, **6 (7.5 %) `fallback`**,
  **zero `scripted`** — a scripted policy on a champion seat would be a failure state and there is
  none. `results.llmTurns [38,36,0,0]` / `fallbackTurns [2,4,0,0]` agree.
- Seats 2/3 are the scripted filler `beeline` — `scripted` 40/40, as designed.
- `jq -r '.fallbacks'` → **6** (one record per seat-turn, so it equals `sum(fallbackTurns)`) ·
  `jq -r '.budgetGuards'` → **0** (the budget guard never fired) ·
  LLM latency n=74, mean **3344 ms**, max **4892 ms**, inside the 6000 ms attempt-1 deadline.
- The 6 fallbacks are scattered, not a block: r1t2 s0, r1t2 s1, r1t3 s0, r1t3 s1, r1t4 s1,
  r3t7 s1.
- **Words were actually said**: `jq -r '[.symbols[]|select(.symbol!="-")]|length'` → **46** of 160
  cog-turns carried a non-silent radio symbol; by round/seat:
  `r1 s0 A×2 D×8 · r1 s1 A×3 E×2 F×2 · r2 s1 G×10 · r3 s1 H×9 · r4 s0 C×8 D×2`.
  design.md line 1071: "a coworld about talking whose replay contains no words is broken even if it
  is green" — it contains words.

**The champion seats doing the thing the game is about** — full `note` + compiled order, early /
middle / late:

```
round 1 spread  turn 0 seat 0 RED-alpha  cooperator   llm 3535ms
  note: SPREAD round 1: RED at [806,492]. Nearest mark is violet (0) at [834,418], distance ~75px. Claim it with A. Cover and hold.
  cog : intent=cover target=[834,418] symbol=A
round 1 spread  turn 0 seat 1 BLUE-alpha cooperator   llm 3535ms
  note: SPREAD round 1: establishing convention. I am BLUE at [780,140], closest to bone mark [983,140]. Committing with F.
  cog : intent=cover target=[983,140] symbol=F
round 3 crypto  turn 4 seat 0 RED-alpha  listener     llm 3972ms
  note: Turn 4: YELLOW silent - no new key symbol. Key confirms C=violet=mark 3 is goal. BLUE settled at bone(2), GREEN at bone(2) - both eavesdroppers stationary, not …
  cog : intent=go target=[651,329] symbol=-
round 3 crypto  turn 4 seat 1 BLUE-alpha eavesdropper llm 3972ms
  note: Turn 4/10. RED sprinting away from amber toward teal—decoded goal as amber. GREEN locked on bone. I hold violet (diagonal opposite), splitting board. Send H to …
  cog : intent=cover target=[651,329] symbol=H
round 4 tag     turn 9 seat 0 RED-alpha  pursuer      llm 1967ms
  note: TAG R4T9: GREEN still pinned at mark 0 with sustained contact (892 ticks scored). YELLOW anchors NW at mark 3. I shadow from E, maintain contact. Signal D to cl…
  cog : intent=shadow target=[606,340] symbol=D
round 4 tag     turn 9 seat 1 BLUE-alpha pursuer      llm 1967ms
  note: TAG turn 9: GREEN still pinned center. RED maintains contact north. I maintain south shadow pressure. YELLOW intercept ahead. Two shadows + …
  cog : intent=shadow target=[606,340] symbol=-
```

These are the game's own intents (`cover`, `go`, `shadow`) applied to named marks and named
opponents, with the radio used to propose a convention in `spread` (`A`, `F`), to signal in
`deceive` (`G`×10) and to bluff as an eavesdropper in `crypto` (`H`×9). The round cards confirm the
four modes really ran with rotating roles:

```
1 spread  roles ['cooperator','cooperator','cooperator','cooperator'] goal -1
2 deceive roles ['adversary','good','good','good']                    goal 1 amber
3 crypto  roles ['listener','eavesdropper','eavesdropper','speaker']  goal 2 bone
          key [['A','amber'],['E','teal'],['C','violet'],['F','bone']]
4 tag     roles ['pursuer','pursuer','evader','pursuer']              goal -1
```

and the outcomes moved: `coverPct 97` in `spread`, the adversary held to `0.044` while the good
side banked `0.955` in `deceive`, `goalHits [0,1,2,0]`, and `tagTicks 1000` of contact in `tag`.

Status: **TRUE** — strict-UTF-8 JSON via the design-declared substitute,
`protocol particle-worlds/v1`, `complete`/`full_time`, 92.5 % LLM directives on the champion seats
with zero scripted ones, and substantive, situational content.

---

## 5. Hosted game log — **TRUE via SPEC item 5's documented-platform-cause branch**

SPEC §Definition of done item 5, verbatim:

> 5. Hosted game log (`/episode-requests/<id>/artifacts/logs`, elevated header): zero lines
>    matching `falling back|LLM provider is unavailable|cut off at max_tokens|rejected` —
>    **or a documented platform-wide cause checked against another LLM coworld.**

The first branch is **not** satisfied: 14 matching lines. The check is satisfied by the **second**
branch, and everything below is that documentation.

```
GET $BASE/episode-requests/ereq_be89daa4-b8a2-4941-93b7-68a7423a79bb/artifacts/logs
  headers: Authorization, User-Agent, X-Use-Elevated-Privileges       (fetched 14:07:17Z)
→ HTTP 200  bytes 168403
```

The body is python `b'…'` byte-string reprs under `===== container: <name> =====` headers, so it
was decoded per repr with `ast.literal_eval` before grepping (a line-based grep undercounts):

```
== container coworld-init-config:   0 decoded lines,      0 chars,  0 matching
== container bedrock-sidecar:     322 decoded lines, 163713 chars,  0 matching
== container game:                 73 decoded lines,   4114 chars, 14 matching
== container worker:                0 decoded lines,      0 chars,  0 matching
TOTAL matching lines: 14 -> NOT CLEAN
```

All 14 lines, verbatim (decoded `game` container, line numbers within it):

```
23: particle-worlds llm: seat 0 attempt 1 failed, falling back if it fails again: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
24: particle-worlds llm: seat 1 attempt 1 failed, falling back if it fails again: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
26: particle-worlds llm: seat 0 falling back to drifter (throttled) on turn 2
27: particle-worlds llm: seat 1 falling back to drifter (throttled) on turn 2
28: particle-worlds llm: seat 0 attempt 1 failed, falling back if it fails again: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
29: particle-worlds llm: seat 1 attempt 1 failed, falling back if it fails again: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
31: particle-worlds llm: seat 0 falling back to drifter (throttled) on turn 3
32: particle-worlds llm: seat 1 falling back to drifter (throttled) on turn 3
33: particle-worlds llm: seat 1 attempt 1 failed, falling back if it fails again: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
35: particle-worlds llm: seat 1 falling back to drifter (throttled) on turn 4
54: particle-worlds llm: seat 0 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
55: particle-worlds llm: seat 1 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
56: particle-worlds llm: seat 1 attempt 2 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
57: particle-worlds llm: seat 1 falling back to drifter (timeout) on turn 7
```

Zero `cut off at max_tokens`, zero `rejected`, zero `LLM provider is unavailable`. Every one of the
14 lines is a **429 daily-token throttle** or a **timeout waiting on the sidecar** — nothing about
the coworld's own prompts, schema or parsing.

**The cause is upstream of the game container**, from the same log's `bedrock-sidecar`:

```
bedrock invocations 81 · "200 OK" 76 · "429" 5

2026-08-26 13:55:56,099 WARNING __main__ bedrock_sidecar_complete
{"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar",
 "episode_request_id":"be89daa4-b8a2-4941-93b7-68a7423a79bb",
 "job_request_id":"1ae313cc-0f99-450d-aaf4-21bdc8688cc8","role":"game","slot":"game",
 "model":"global.anthropic.claude-haiku-4-5-20251001-v1:0","operation":"InvokeModel",
 "call_id":"1896acfb-dcbd-4b86-9a4b-06698290f8dc","ok":false,"status_code":429,
 "latency_ms":46.776188999501755,"error_kind":"upstream_client",
 "error_type":"ThrottlingException",
 "message":"Too many tokens per day, please wait before trying again.",
 "request_id":"39789689-3fb0-49dd-8038-3ca0aac9e234","cache_strategy":"sidecar_v1",
 "cache_decision":"first_sighting","cache_points_applied":0,
 "timestamp":"2026-08-26T13:55:56.099699Z"}

2026-08-26 13:55:56,099 INFO httpx HTTP Request: POST
  https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke
  "HTTP/1.1 429 Too Many Requests"
```

`ThrottlingException` / "Too many tokens per **day**" is returned by
`bedrock-runtime.us-east-1.amazonaws.com` itself — an **account-level Bedrock quota** shared by
every run in flight (SPEC §Parallelism and per-run isolation: Bedrock capacity is the one resource
parallel runs share).

**Cross-check against another LLM coworld, made this phase.** I checked
**walker-waterworld** (`league_69fe3c37-8208-4e14-b575-331e1d018d9b`), whose latest completed round
finished within **3 seconds** of particle-worlds' round 3:

```
GET $BASE/rounds?league_id=league_69fe3c37-8208-4e14-b575-331e1d018d9b&limit=20   (14:10:02Z)
→ latest completed: round_e86d395b-3836-4bd2-b8f5-ba314a7189e1  round 11  completed_at 2026-08-26T14:01:56.434192Z
   (particle-worlds round 3 completed_at 2026-08-26T14:02:03.394080Z)

GET $BASE/rounds/round_e86d395b-.../episode-requests                              (14:10:1xZ)
→ [{"id":"ereq_62be0e80-a2d2-47f6-91d2-da2038f8c617","status":"completed"}]

GET $BASE/episode-requests/ereq_62be0e80-a2d2-47f6-91d2-da2038f8c617/artifacts/logs
  headers: Authorization, User-Agent, X-Use-Elevated-Privileges                   (14:10:18Z)
→ HTTP 200  bytes 27895

== coworld-init-config:   0 lines,   0 matching
== bedrock-sidecar:      83 lines,   0 matching
== game:                177 lines, 120 matching
== worker:                0 lines,   0 matching
TOTAL 120
```

First six of walker-waterworld's 120 matching lines:

```
20: waterworld llm: seat 0 attempt 1 failed, falling back if it fails again: anthropic error 503: {"message":"LLM provider is unavailable"}
21: waterworld llm: seat 1 attempt 1 failed, falling back if it fails again: anthropic error 503: {"message":"LLM provider is unavailable"}
22: waterworld llm: seat 0 attempt 2 failed, falling back if it fails again: anthropic error 503: {"message":"LLM provider is unavailable"}
23: waterworld llm: seat 1 attempt 2 failed, falling back if it fails again: anthropic error 503: {"message":"LLM provider is unavailable"}
24: waterworld llm: seat 0 falling back to shoal (parse_error) on turn 0
25: waterworld llm: seat 1 falling back to shoal (parse_error) on turn 0
```

A second, unrelated LLM coworld, in the same minute, on a different starter and different prompts,
shows the *same class of failure* an order of magnitude worse (120 lines vs 14; `LLM provider is
unavailable` 503s vs 429 throttles). That is the documented platform-wide cause item 5 asks for.

Two further facts that keep this inside the exception rather than stretching it:

- **The throttle did not break the episode.** 76 of 81 Bedrock calls returned 200, the episode ran
  all four rounds to `full_time`, and only **6 of 160** directives ended on a fallback — 92.5 % of
  the champion seats' directives were live LLM (check 4).
- **It is not specific to this round.** Round 2's episode
  (`ereq_8090183a-d104-431f-a0af-13a236f47fcf`, logs fetched 13:52Z this phase, HTTP 200,
  168834 bytes) had exactly **1** matching line, also a sidecar transport timeout, and **zero**
  fallback turns:
  `particle-worlds llm: seat 1 attempt 1 failed, falling back if it fails again: llm transport: Timeout was reached POST http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke`
  — i.e. the count tracks the platform's throttle over the hour, not anything the coworld changed.

I stayed inside the 75-minute bound rather than declaring an outage, as the prompt directs; the
bound (expiring ~14:57Z) was **not** reached — two rounds completed by 14:02Z.

Status: **TRUE** on the exception branch — 14 lines, every one a Bedrock 429
`ThrottlingException` ("Too many tokens per day") or a sidecar timeout, cross-checked against
**walker-waterworld**'s 14:01:56Z episode showing 120 lines of `LLM provider is unavailable`.

---

## 6. The public page uses the static replay path — **TRUE**

**Source used: both.** The raw-HTML grep found nothing (the page is client-rendered for the
iframe, as `playbooks/observatory-api.md` §Featured match records), so I used the two sources the
playbook prescribes: the page's **SSR payload** for the featured match, and the **replay-session
call the page's own JS makes** for the iframe `src`.

```
GET https://softmax.com/particle-worlds                                (fetched 14:05:14Z)
→ HTTP 200  bytes 586733
grep -o '<iframe[^>]*src="[^"]*"'  → (no match — client-rendered, treated as UNKNOWN, not false)
grep -c 'client/replay'            → 0
```

Featured match, from the SSR payload at `state.playlist[0]`:

```json
{"episodeId":"2465e924-573a-42f2-89e5-e40d9b34171c",
 "coworldId":"cow_039ad60d-ae1f-4098-ab1d-4f0144e32198",
 "coworldName":"particle-worlds","coworldVersion":"0.1.2",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/1ae313cc-0f99-450d-aaf4-21bdc8688cc8.replay",
 "finishedAt":"2026-08-26T14:01:59.242125Z","roundNumber":3,"episodeNumber":1,
 "code":"particle-worlds.r3.e1",
 "matchup":{"divisionId":"div_4e1ddbbe-b6d4-409d-82b9-23e1142268d0","divisionName":"Competition",
  "first":{"rank":1,"player_name":"daveey-1","score":1030.5304984710244,"rounds_played":2,
           "episode_wins":2,"win_rate":1,"policy_label":"particle-worlds-cipher:v2"},
  "second":{"rank":2,"player_name":"daveey", …,"policy_label":"particle-worlds-swarm:v2"}},
 "inspectUrl":"/observatory/v2?tab=overview&detail=episode-request:ereq_be89daa4-b8a2-4941-93b7-68a7423a79bb",
 "outcome":"first"}
```

A featured match **is present**, it is the same episode as check 3 (`ereq_be89daa4…`), and its
matchup is the two champions. (`GET $BASE/coworlds?limit=200` — bare array, fetched 13:43Z — has
`featured_match: null` and `replay_viewer: null` for this coworld, as it does platform-wide; per
the playbook that is not evidence either way, which is why the SSR payload is the source.)

The iframe `src`, from the call the page's JS makes:

```
POST $BASE/coworlds/replays/session
  headers: Authorization, User-Agent, content-type                     (called 14:05:22Z)
  body: {"coworld_id":"cow_039ad60d-ae1f-4098-ab1d-4f0144e32198",
         "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/1ae313cc-0f99-450d-aaf4-21bdc8688cc8.replay"}
→ HTTP 200
```
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_039ad60d-ae1f-4098-ab1d-4f0144e32198/sha256%3Ac9ae68f37da1146762cfefc9e1fd0a96315d9276cbabd3ebbfa49fb962269903/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F1ae313cc-0f99-450d-aaf4-21bdc8688cc8.replay&v=2",
 "ready":true}
```

- Path is `/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` ✓
- `<cow_id>` = `cow_039ad60d-ae1f-4098-ab1d-4f0144e32198` = `STATE.coworld.cow_id` ✓
- `<sha>` = `sha256:c9ae68f37da1146762cfefc9e1fd0a96315d9276cbabd3ebbfa49fb962269903`
  (URL-encoded) = the coworld's **manifest_hash**, identical to `STATE.coworld.manifest_sha` and to
  `release-result.json.manifest_sha` ✓
- `ready: true` and the path ends `/index.html` → static delivery ✓
- **No `/client/replay` pod URL anywhere** — 0 occurrences in the page HTML, and the session call
  returns the static route ✓

Status: **TRUE** — featured match present (round 3, both champions), iframe `src` on the static
route keyed by the manifest hash, never a pod URL.

---

## 7. Certification declared the static bundle — **TRUE**

**Source read: the committed `runs/2026-08-26-particle-worlds/release-result.json`** (phase 40's
artifact copy, present in the run directory — no re-download needed, and `/tmp` was not consulted).

```
jq -r '.certify.replay_liveness' runs/2026-08-26-particle-worlds/release-result.json   (read 14:10:52Z)
→ Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)

jq -r '.version, .cow_id, .manifest_sha, .canonical, .ok' runs/2026-08-26-particle-worlds/release-result.json
→ 0.1.2
   cow_039ad60d-ae1f-4098-ab1d-4f0144e32198
   sha256:c9ae68f37da1146762cfefc9e1fd0a96315d9276cbabd3ebbfa49fb962269903
   true
   true
```

The same string appears in the certification transcript tail inside that file, after all ten
transcript steps passed:

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

Status: **TRUE** — contains `Replay liveness: skipped (static replay bundle declared`, read from
the committed `release-result.json` (release run `32973681353`), and its `manifest_sha` is the same
`<sha>` the check-6 static URL uses.

---

## 8. Spectator judgment — the viewer was EXECUTED — **TRUE**

The sandbox has no screen, so I dispatched the render and read the result. The `url` input is the
**exact** iframe `src` from check 6, `?replay=` and all.

```
date -u                                        → 2026-08-26T14:05:37Z   (dispatch timestamp)
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder \
   -f url="https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_039ad60d-ae1f-4098-ab1d-4f0144e32198/sha256%3Ac9ae68f37da1146762cfefc9e1fd0a96315d9276cbabd3ebbfa49fb962269903/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F1ae313cc-0f99-450d-aaf4-21bdc8688cc8.replay&v=2" \
   -f timeout=90
→ dispatched

# find-the-new-run by createdAt, never "the latest" blind:
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[]|[.databaseId,.createdAt,.status]|@tsv'
→ 32978130047	2026-08-26T14:05:38Z	in_progress     ← created 1 s AFTER my dispatch: this is mine
   32967129036	2026-08-26T12:10:17Z	completed       ← previous run, 1h55m older, not mine
   32937649794	2026-08-26T06:19:23Z	completed
   …

gh run view 32978130047 -R Metta-AI/coworld-builder --json status,conclusion,createdAt,url
→ {"conclusion":"success","createdAt":"2026-08-26T14:05:38Z","status":"completed",
   "url":"https://github.com/Metta-AI/coworld-builder/actions/runs/32978130047"}

gh run download 32978130047 -R Metta-AI/coworld-builder -n viewer-check \
   -D runs/2026-08-26-particle-worlds/viewer-check
→ smoke-stderr.txt (0 B)  smoke-stdout.txt (769 B)  viewer-smoke.json (1565 B)  viewer-smoke.png (771061 B)
```

`viewer-smoke.json`'s `url` field confirms the bundle it opened is the check-6 `src` verbatim,
including the `?replay=…1ae313cc-0f99-450d-aaf4-21bdc8688cc8.replay&v=2` query.

**(a) The load readout, verbatim**

```
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-26-particle-worlds/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":10110,"clock":"0:45 TIME LEFT ROUND 1/4 · SPREAD · TURN 1/10","scorebug":"○ DAVEEY COOPERATOR 0.000 0.75 THIS ROUND A ○ BASELINE COOPERATOR 0.000 0.75 THIS ROUND — 0:45 TIME LEFT ROUND 1/4 · SPREAD · TURN 1/10 ○ DAVEEY-1 COOPERATOR 0.000 0.75 THIS ROUND F ○ BASELINE COOPERATOR 0.000 0.75 THIS ROUND —","feed_lines":0}
```

```
jq -c '.signals' …/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

```
jq -r '.failure // "no failure"' …/viewer-smoke.json   → no failure
jq -r '.console_tail|length'                           → 0
jq -c '.canvas_text'  → {"total":0,"outside":0,"ellipsized":0,"never_inside":0,…}
```

`data-replay-loaded="true"` with `data_replay_error: null` — the viewer **drew a frame and said
so**. `loaded: true` after 10 110 ms.

**(b) The three clock readouts**

```
jq -r '.scrub[]|"\(.at)\t\(.clock)"' …/viewer-smoke.json
```

| Scrub position | `#clock` readout |
|---|---|
| **0 %** | `0:45 TIME LEFT ROUND 1/4 · SPREAD · TURN 1/10` |
| **50 %** | `:04 STARTING IN ROUND 3/4 · DECEIVE · TURN 1/10` |
| **100 %** | `0:00 TIME LEFT ROUND 4/4 · TAG · TURN 10/10` |

All three **differ**, and they differ in the right direction: round 1 → round 3 → round 4, with the
mode caption changing `SPREAD → DECEIVE → TAG`. This is a replay that advances, not a screenshot.

(One legibility note the readouts expose: the 50 % caption says `ROUND 3/4 · DECEIVE` while the
replay's round 3 is `crypto` and round 2 is `deceive` — the mode label is one round behind the
round number during the `:04 STARTING IN` inter-round countdown. Cosmetic, in the caption only; the
100 % readout `ROUND 4/4 · TAG` is correct.)

`has_scrub` was true, so no "(no #scrub…)" substitution was needed. `feed_lines: 0` is a **probe
selector mismatch, not an empty feed claim**: the probe (`templates/tools/ci/viewer_smoke.mjs:425`)
queries
`#feed, .feed, #log`, and this fork keeps the starter's id `#killfeed` — confirmed in the repo:
`grep -o 'id="[a-z-]*feed[a-z-]*"' client/replay_broadcast.html` → `id="killfeed"`, and there is no
`id="feed"` or `id="log"` in the page at all (design.md line 1233: "`#killfeed` (renamed in copy
only, to 'the wire')"). The counter could never see it, so I make no claim about feed content from
that number, and the screenshot below was taken after three seeks —
`viewer_smoke.mjs:102` notes that "seeking clears the feed queue", so an empty wire at that moment
is expected behaviour.

**(c) The replay JSON the viewer was asked to draw** — reconciliation, from `/tmp/ep.replay`
(check 4): early / middle / late excerpts and `results` are pasted in check 4 above and are not
repeated here.

### Spectator judgment

`viewer-smoke.png` (1280×800, captured at the 100 % seek: `DRAW 4888 / 4896`, round 4/4 TAG turn
10/10) is a **legible, populated, on-brand broadcast** — and it is unmistakably the starter's
chrome, not a rewrite.

**It looks like paintbot/coworld-ctf.** The top band is the inherited `#scorebug`: four plates, two
left and two right of a large centred `0:00 / TIME LEFT` clock with the caption
`ROUND 4/4 · TAG · TURN 10/10`, each plate carrying a coloured team triangle, the **real policy
owner's name** (`DAVEEY`, `BASELI…`, `DAVEE…`, `BASEL…`, ellipsized to fit), the role held this
round (`PURSUER` / `EVADER`), a big episode-score numeral and a small `… THIS ROUND` line. Below it
sit the two particle-worlds additions, both drawn and readable: the **mark rail**
(`● BONE 98% ● TEAL 44% ● AMBER 32% ● VIOLET 98%`, each with its palette dot) and the **radio
strip** (`RED D · BLUE — · GREEN — · YELLOW —`, silence as an em dash exactly as designed). The
bottom band is `#transport` **in full** — restart, step-back, play, `+5s`, step, loop (lit),
fast-forward (lit), a `spoilers` toggle, the `DRAW` win-chip, the tick readout `4888 / 4896`, and
the `1× 2× 3× 4× 8× 16×` speed chips — over the `#scrub` bar with its fill at 100 %, the orange
scrub head parked at the right edge, and the momentum strip beneath it. Same transport strip, same
scorebug, same scrubber-with-momentum-graph as paintbot/raid/hive.

**It shows the game, and the numbers match the record.** The scorebug reads
`DAVEEY 0.366 (1.00 this round)`, `BASELI… 0.949 (0.07)`, `DAVEE… 0.872 (1.00)`,
`BASEL… 0.670 (0.00)`. Those are exactly the means of the three banked rounds in the replay's own
`roundScores` — `(0.974+0.044+0.081)/3 = 0.366`, `(0.974+0.955+0.689)/3 = 0.8727`,
`(0.974+0.955+0.918)/3 = 0.949`, `(0.974+0.955+0.081)/3 = 0.670` — and the small numbers are round
4's permille (`1.0 / 0.074 / 1.0 / 0.0`). The picture and the bytes are the same episode.

**The action is the action the replay describes.** In the arena, three sprites are stacked in
contact just left of centre — a green particle pinned by a blue and a red one — with a yellow
particle alone up and to the left, its bubble showing an em dash. Converting the pixel positions
back to arena coordinates puts the cluster at ≈(595, 343) and the yellow at ≈(397, 156); the
replay's round-4 turn-9 champion directives say, in their own words, "GREEN still pinned at mark 0
with sustained contact (892 ticks scored). YELLOW anchors NW at mark 3. I shadow from E, maintain
contact." with `intent=shadow target=[606,340]` from both pursuers. `results.tagTicks 1000` says
the pin lasted. The comm bubbles are drawn as the design specifies — rounded, above the sprite, one
large glyph (`D` in the green-outlined bubble, em dashes for the silent seats) — and the radio strip
agrees (`RED D`, everyone else silent). The sprites are the starter's real soldier art, tinted
per-team with the seat's symbol on the chest; the field is the baked dark arena with a faint grid.

**Three legibility observations for the coordinator** (none of them makes item 8 false — the viewer
loaded and advanced — and none is a rewrite-of-the-starter finding):

1. **The momentum graph is still labelled `LIVES LEAD`** and renders as a single flat line.
   design.md §Readouts item 7 specifies "the starter's `lead` series, **retargeted** to four series
   of cumulative episode score (one per seat, in team colours) with the three round boundaries
   marked". The strip is present and positioned correctly, but the caption is the starter's
   paintbot/ctf copy — particle worlds has no lives — and I see one line, not four coloured series
   with round boundaries. Source, not inference: the string is hard-coded at
   `client/replay_broadcast.html:1384` (`<span class="momentum-label">LIVES LEAD</span>`) and again
   at `client/league_replayer.html:334` in the repo at `main` = `543c5a8`.
2. **No beat-marker buttons are visible on `#scrub`** in this frame. design.md §Transport rules
   promises clickable labelled beats for `roundstart`/`firstword`/`onpoint`/`tag`/`roundover`
   (bounded 4 + ≤4 + ≤8 + ≤22 + 4). Beats are appended from playback deltas and the smoke seeks
   rather than plays through, so this is *consistent* with beats not having accumulated — but the
   captured frame's scrubber carries none, so a spectator who scrubs immediately gets no beat
   navigation.
3. **No landmark discs are visible on the board** in this frame. A saturation scan of the 1136×598
   board region finds coloured pixels only in the mark rail, the radio strip and around the four
   sprites — the arena itself is uniform grey. In `tag` the marks are "inert decoration" by design,
   so this may be deliberate suppression; but design.md §Readouts item 2 describes every mark drawn
   as a baked disc with a coverage ring and radial wash, and the rail is simultaneously reporting
   `BONE 98% … VIOLET 98%` for marks the spectator cannot see. The result is a large empty-looking
   field with four small sprites in one corner of it — the least legible thing in the picture.

Nothing is empty, frozen or unreadable: the picture is populated, the clock and tick advance across
three seeks, the scorebug says who is winning and by how much, and the mark rail and radio strip say
why. Item 8's two hard conditions — `loaded: true` and three differing clock readouts — both hold.

Status: **TRUE** — `loaded: true` (`data-replay-loaded="true"`, no failure, no console errors) and
three differing clock readouts spanning rounds 1 → 3 → 4; rendered evidence committed at
`runs/2026-08-26-particle-worlds/viewer-check/`.

---

## Summary

| # | Check | Verdict | One-line evidence |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers | **TRUE** | rounds 2 & 3 `completed` 13:47:30Z / 14:02:03Z; round 1 `failed` "Temporal RoundWorkflow failed before settling the round." excluded; fillers seated `is_filler:true` in both counted rounds |
| 2 | Both champions ranked, fillers absent | **TRUE** | `daveey-1` rank 1 (cipher:v2, 2 rounds), `daveey` rank 2 (swarm:v2, 2 rounds); only two rows, fillers `Baseline`/`Baseline (2)` in the roster |
| 3 | Latest round's episode completed w/ replay | **TRUE** | `ereq_be89daa4…` `completed`, `replay_url` `…/1ae313cc….replay`, positions 0/1 = daveey/daveey-1 `is_filler:false` (flat route 405 → nested route) |
| 4 | Replay bytes valid, show the game | **TRUE** | strict-UTF-8 JSON via design-declared `replay_summary.py`; `particle-worlds/v1`, `complete`/`full_time`, 74/80 champion directives `llm`, 0 scripted, 46 non-silent symbols |
| 5 | Hosted log clean | **TRUE** (exception branch) | 14 lines, all Bedrock 429 `ThrottlingException` "Too many tokens per day" or sidecar timeouts; cross-checked vs walker-waterworld `ereq_62be0e80…` (14:01:56Z) with 120 lines of `LLM provider is unavailable` |
| 6 | Static iframe `src` + featured match | **TRUE** | SSR `playlist[0]` = round 3 champion-vs-champion; session POST → `…/replays/static/cow_039ad60d…/sha256%3Ac9ae68f3…/index.html?replay=…`, `ready:true`, zero `client/replay` |
| 7 | Certification declared static bundle | **TRUE** | committed `release-result.json`: `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)` |
| 8 | Viewer executed + spectator judgment | **TRUE** | run `32978130047` (created 14:05:38Z, success): `loaded:true`, `ms:10110`, clocks `ROUND 1/4 SPREAD` → `ROUND 3/4` → `ROUND 4/4 TAG` all differ; scorebug numerals reproduce the replay's banked `roundScores` |

Nothing was marked true by inference. No item is `NOT FETCHED`.
