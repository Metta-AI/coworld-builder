# VERIFY — escrow   (2026-08-23T18:53Z)

Verdict: **all-true** — 8 TRUE / 0 FALSE.

Attempt 3 — **post-remediation-2 re-verification**. Every fetch below was made fresh between
2026-08-23T18:27Z and 18:53Z against the **v0.1.3** coworld (`cow_9b73db59-4be9-4a59-9e56-5eed9151a871`)
and the **v4** champion/filler policies. Nothing is reused from attempt 1 (16:02–16:43Z) or attempt 2
(17:18–17:56Z); a short appendix at the bottom summarises both for continuity only. The single
documented exception to "fetch fresh" is **check 7**, whose evidence is by design the committed
`runs/2026-08-23-escrow/release-result.json` artifact of this run's release dispatch.

Headers sent on every Observatory call (values never printed):
`Authorization: Bearer $SOFTMAX_TOKEN`, `User-Agent: coworld-builder/1.0`, and on
`artifacts/logs` and `filler-policies` additionally `X-Use-Elevated-Privileges: true`.

```bash
BASE=https://softmax.com/api/observatory/v2
L=league_cc074076-5938-403e-81db-d278c031db6d
D=div_a8171f6e-62bd-41e5-b470-f15d675faee9
COW=cow_9b73db59-4be9-4a59-9e56-5eed9151a871
SHA=sha256:f5e3e157c60491b881720fbefbe8a5c4e7040d71a7e47ac37f8b4948a8c64c40
```

**Scope rule applied throughout.** A round counts as post-remediation-2 ("v4") only if
`round_config.entrant_policy_version_ids` contains **both** v4 champion UUIDs:

| role | policy | policy_version_id | player |
|---|---|---|---|
| champion 1 | `escrow-drafter:v4` | `5153a6f7-d2b9-4429-886d-10563a6a58e6` | `daveey` |
| champion 2 | `escrow-swapper:v4` | `228bbef6-b544-4fde-a3cd-3ef618792599` | `daveey-1` |
| filler 1 | `escrow-trader:v4` | `fb6d64e0-2e51-41ce-aa20-347cb78f4094` | `daveey` |
| filler 2 | `escrow-hoarder:v4` | `d9d3f7f8-ae77-4c84-bd91-752744102a6d` | `daveey` |

Ownership and version identity re-resolved fresh this attempt:

```bash
curl -sS "$BASE/policy-versions?limit=200" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)[]
          |select(.policy_name|startswith("escrow-"))
          |[.policy_name,.policy_version_id,.player_name,.created_at]|@tsv' | sort -k4
```
```
escrow-drafter	6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d	daveey		2026-08-23T15:50:33.931499Z
escrow-swapper	ae792ad8-75d3-4eb6-aea3-4dfa8548907a	daveey-1	2026-08-23T15:50:36.109215Z
escrow-trader	0505950f-bd65-46d4-ac4a-b3d0ad40c11b	daveey		2026-08-23T15:50:38.328703Z
escrow-hoarder	b07b36d6-c4aa-4dce-b5af-a3dc0f7a6016	daveey		2026-08-23T15:50:39.773649Z
escrow-drafter	bbff274f-ac96-415b-879d-4df6f0c12da5	daveey		2026-08-23T16:55:56.555172Z
escrow-swapper	f64ecbe7-1dcc-44d9-aea7-19aa7cc1531e	daveey-1	2026-08-23T16:55:59.415107Z
escrow-trader	feea7173-a279-48cc-a2c4-0a9510b5aab7	daveey		2026-08-23T16:56:01.952981Z
escrow-hoarder	5ba89854-340c-406d-9eca-a4fe29ad4987	daveey		2026-08-23T16:56:03.308866Z
escrow-drafter	03aecc7d-d51b-42fd-92b8-2c3199583176	daveey		2026-08-23T17:06:02.734477Z
escrow-swapper	ab5da062-606a-446b-accb-aeeb899a93a1	daveey-1	2026-08-23T17:06:05.162987Z
escrow-trader	9d09a38a-0cd6-4d0b-a4cb-498bcbc85396	daveey		2026-08-23T17:06:07.086210Z
escrow-hoarder	3ed1facb-5183-48c4-98da-ef84e8281862	daveey		2026-08-23T17:06:08.294226Z
escrow-drafter	5153a6f7-d2b9-4429-886d-10563a6a58e6	daveey		2026-08-23T18:15:43.288803Z   <-- v4 champion 1
escrow-swapper	228bbef6-b544-4fde-a3cd-3ef618792599	daveey-1	2026-08-23T18:15:45.542214Z   <-- v4 champion 2
escrow-trader	fb6d64e0-2e51-41ce-aa20-347cb78f4094	daveey		2026-08-23T18:15:48.821670Z   <-- v4 filler 1
escrow-hoarder	d9d3f7f8-ae77-4c84-bd91-752744102a6d	daveey		2026-08-23T18:15:50.566409Z   <-- v4 filler 2
```

**Round under evaluation for checks 3, 4, 5, 6 and 8: round 13**
(`round_292146e4-dee4-45f7-9259-79fe08d95198`) — the latest completed v4 round at the time of
writing. Round 12 is quoted alongside as corroboration where useful, never as a substitute.

---

## 1. ≥2 completed rounds after fillers were set — **TRUE**

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '.entries[]|[.round_number,.id,.status,.created_at,
          (.round_config.entrant_policy_version_ids|join(","))]|@tsv' | sort -n
```
```
1	round_b8f582ac-cc01-44cc-9cd9-49b0c65e108c	failed	2026-08-23T15:58:00.403567Z	6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d
2	round_13be4cf0-ad75-4954-9514-98480c6f8d07	completed	2026-08-23T15:58:41.705932Z	6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d,ae792ad8-75d3-4eb6-aea3-4dfa8548907a
3	round_89c1c03d-3d38-464f-9412-3bddaad639f4	completed	2026-08-23T16:13:42.285154Z	6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d,ae792ad8-75d3-4eb6-aea3-4dfa8548907a
4	round_c0c234c2-eb3f-4ab5-9cf5-894f1a4f8127	completed	2026-08-23T16:28:42.651720Z	6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d,ae792ad8-75d3-4eb6-aea3-4dfa8548907a
5	round_1aaceee5-0fad-42d2-a66c-4f55218ae0fa	completed	2026-08-23T16:43:43.249827Z	6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d,ae792ad8-75d3-4eb6-aea3-4dfa8548907a
6	round_ad8635c6-be79-4e68-931c-b953ea7d5608	completed	2026-08-23T16:58:45.387833Z	6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d,ae792ad8-75d3-4eb6-aea3-4dfa8548907a
7	round_6ea4a55e-ddde-4dec-a3d0-78fc26685d32	completed	2026-08-23T17:13:46.110082Z	6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d,ae792ad8-75d3-4eb6-aea3-4dfa8548907a
8	round_946f98fa-b994-40b2-9685-923f0d142bce	completed	2026-08-23T17:28:47.072683Z	03aecc7d-d51b-42fd-92b8-2c3199583176,ab5da062-606a-446b-accb-aeeb899a93a1
9	round_3ee96829-8391-4236-b835-c6e3b9c3db4a	completed	2026-08-23T17:43:47.651022Z	03aecc7d-d51b-42fd-92b8-2c3199583176,ab5da062-606a-446b-accb-aeeb899a93a1
10	round_f623531c-d878-4d0c-8405-2903ab4bdda5	completed	2026-08-23T17:58:48.027519Z	adaf2f9a-1fee-41a6-9d3c-20fbc27f445b,03aecc7d-d51b-42fd-92b8-2c3199583176,ab5da062-606a-446b-accb-aeeb899a93a1,0a88e105-ff6d-47ca-a6be-3f05e30d3168
11	round_1d4df765-e4bb-41af-9492-3bf6fe4852e2	completed	2026-08-23T18:13:48.384014Z	adaf2f9a-1fee-41a6-9d3c-20fbc27f445b,03aecc7d-d51b-42fd-92b8-2c3199583176,ab5da062-606a-446b-accb-aeeb899a93a1,0a88e105-ff6d-47ca-a6be-3f05e30d3168
12	round_3de0946c-72da-465c-bd05-3148da13dfaf	completed	2026-08-23T18:26:27.095347Z	83c89e46-ef7d-40db-bd57-6f776fe0dcf0,5153a6f7-d2b9-4429-886d-10563a6a58e6,228bbef6-b544-4fde-a3cd-3ef618792599,0a88e105-ff6d-47ca-a6be-3f05e30d3168
13	round_292146e4-dee4-45f7-9259-79fe08d95198	completed	2026-08-23T18:41:27.465194Z	83c89e46-ef7d-40db-bd57-6f776fe0dcf0,5153a6f7-d2b9-4429-886d-10563a6a58e6,228bbef6-b544-4fde-a3cd-3ef618792599,0a88e105-ff6d-47ca-a6be-3f05e30d3168
```

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '[.entries[]|select(.status=="completed")]|length'
```
```
12
```

**v4 rounds (both v4 champion UUIDs present, status completed): 2 — round 12 and round 13.**

```bash
jq -r '[.entries[]|select(.status=="completed")
        |select((.round_config.entrant_policy_version_ids|index("5153a6f7-d2b9-4429-886d-10563a6a58e6"))
            and (.round_config.entrant_policy_version_ids|index("228bbef6-b544-4fde-a3cd-3ef618792599")))
        |{round_number,id}]' rounds.json
```
```
[{"round_number":12,"id":"round_3de0946c-72da-465c-bd05-3148da13dfaf"},
 {"round_number":13,"id":"round_292146e4-dee4-45f7-9259-79fe08d95198"}]
```

Filler set in force, read live this attempt (needs the elevated header even though it is a read):
```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}" | jq .
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"fb6d64e0-2e51-41ce-aa20-347cb78f4094","policy_id":"b483ad77-d95e-46b7-a8fb-dbb0a9db4b05",
  "policy_name":"escrow-trader","version":4,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3",
  "player_name":"daveey","display_name":null},
 {"policy_version_id":"d9d3f7f8-ae77-4c84-bd91-752744102a6d","policy_id":"924b1059-bfa2-4f96-8384-0b4754f2105d",
  "policy_name":"escrow-hoarder","version":4,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3",
  "player_name":"daveey","display_name":null}]}
```
(The endpoint returns no timestamps.) Ordering evidence for "after the fillers were set" is
`log.md`, which records the v4 filler PUT and the `trigger-round` in one entry written after both
completed:
```
2026-08-23T18:26:37Z 60 filler-policies updated to v4 (trader fb6d64e0, hoarder d9d3f7f8); trigger-round issued
```
Round 12 was created at `18:26:27.095Z` — the round that `trigger-round` produced, i.e. after the
PUT that preceded it in the same action; round 13 (`18:41:27.465Z`) is unambiguously later. Both
are also after the v4 champion submissions (policy versions created `18:15:43Z`/`18:15:45Z`,
submitted per `log.md` at `18:26:37Z`). Corroborating structural evidence that the fillers were in
place: a `trigger-round` issued with no filler registered fails instantly with the Temporal message
below — round 12 completed instead.

Excluded rounds, recorded as required:

- **round 1 — `failed`**, error verbatim:
```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '.entries[]|select(.round_number==1)|{round_number,status,error}'
```
```json
{"round_number":1,"status":"failed","error":"Temporal RoundWorkflow failed before settling the round."}
```
- **rounds 2–7** — completed but pre-remediation (v1 champions `6eb9292a…`/`ae792ad8…`).
- **rounds 8–11** — completed but remediation-1 (v3 champions `03aecc7d…`/`ab5da062…`).
- No round has status `discarded`.

**Status: TRUE — 2 completed v4 rounds (12 `round_3de0946c-72da-465c-bd05-3148da13dfaf` at
18:26:27Z, 13 `round_292146e4-dee4-45f7-9259-79fe08d95198` at 18:41:27Z), both after the v4 fillers
were registered at ~18:26:3xZ; 12 completed rounds overall; 1 failed round excluded with its error
quoted.**

---

## 2. Both champions ranked, fillers absent / Baseline — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey	escrow-drafter:v4	1071.971968427456	12	13.0
2	richard	co-gas-escrow-baseline-richard:v1	1000.101165898207	4	6.0
3	relh	co-gas-escrow-baseline-relhalpha:v2	975.6829230895638	4	5.0
4	daveey-1	escrow-swapper:v4	952.2439425847732	12	8.0
```

Full rows (bare list, not `.entries`):
```json
[{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
  "score":1071.971968427456,"score_label":"Elo","rounds_played":12,"episode_wins":13.0,
  "win_rate":0.65,"policy_label":"escrow-drafter:v4"},
 {"rank":2,"player_id":"ply_ded11f40-3e30-4921-b019-f7f6bc3e9c83","player_name":"richard",
  "score":1000.101165898207,"score_label":"Elo","rounds_played":4,"episode_wins":6.0,
  "win_rate":0.5,"policy_label":"co-gas-escrow-baseline-richard:v1"},
 {"rank":3,"player_id":"ply_18302115-9fc9-482d-a2f3-f4c592bf9e57","player_name":"relh",
  "score":975.6829230895638,"score_label":"Elo","rounds_played":4,"episode_wins":5.0,
  "win_rate":0.4166666666666667,"policy_label":"co-gas-escrow-baseline-relhalpha:v2"},
 {"rank":4,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
  "score":952.2439425847732,"score_label":"Elo","rounds_played":12,"episode_wins":8.0,
  "win_rate":0.4,"policy_label":"escrow-swapper:v4"}]
```

- `daveey` present, `policy_label` `escrow-drafter:v4`, `rounds_played` 12 ≥ 1. ✔
- `daveey-1` present, `policy_label` `escrow-swapper:v4`, `rounds_played` 12 ≥ 1. ✔
- **This run's fillers are absent**: neither `escrow-trader` (`fb6d64e0-…`) nor `escrow-hoarder`
  (`d9d3f7f8-…`) appears in any row. ✔

Note on ranks 2 and 3: `richard` (`ply_ded11f40-…`) and `relh` (`ply_18302115-…`) are **third-party
platform players** who joined the Escrow league at ~17:58Z with their own auto-generated baseline
policies (`co-gas-escrow-baseline-*`). They are not this run's filler policies, and because four
real entrants are now enrolled the ladder never needs to seat a filler at all — every participant
in rounds 12 and 13 has `is_filler: false` (check 3). Their presence is not a filler leak.

**Status: TRUE — daveey (rank 1, escrow-drafter:v4, 12 rounds) and daveey-1 (rank 4,
escrow-swapper:v4, 12 rounds) both ranked; this run's two filler policies are absent from the
leaderboard.**

---

## 3. Latest v4 round's episode request completed with a replay — **TRUE**

```bash
R=round_292146e4-dee4-45f7-9259-79fe08d95198     # latest completed v4 round (check 1)
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}" \
 | jq -r '.entries[]|[.id,.status]|@tsv'
```
```
ereq_78850370-c03e-4fc0-b663-a59bb5d73f93	completed
```

```bash
curl -sS "$BASE/episode-requests/ereq_78850370-c03e-4fc0-b663-a59bb5d73f93" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/1839e1b7-3f2c-418c-9eeb-28c19fd6b5dd.replay",
  "participants": [
    {"position": 0, "kind": "policy", "policy_version_id": "83c89e46-ef7d-40db-bd57-6f776fe0dcf0",
     "policy_id": "ec27f81a-9512-422f-9290-0d6dd69df6f2", "policy_name": "co-gas-escrow-baseline-relhalpha",
     "version": 2, "player_id": "ply_18302115-9fc9-482d-a2f3-f4c592bf9e57", "player_name": "relh",
     "is_filler": false},
    {"position": 1, "kind": "policy", "policy_version_id": "5153a6f7-d2b9-4429-886d-10563a6a58e6",
     "policy_id": "79d30f20-9baa-4356-9a5d-7bbb6c472e6c", "policy_name": "escrow-drafter",
     "version": 4, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "is_filler": false},
    {"position": 2, "kind": "policy", "policy_version_id": "228bbef6-b544-4fde-a3cd-3ef618792599",
     "policy_id": "00949333-a6e4-4769-ae42-aaabc9f07d89", "policy_name": "escrow-swapper",
     "version": 4, "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
     "is_filler": false},
    {"position": 3, "kind": "policy", "policy_version_id": "0a88e105-ff6d-47ca-a6be-3f05e30d3168",
     "policy_id": "81c86ca6-c00f-4e64-bbe6-cb668968959c", "policy_name": "co-gas-escrow-baseline-richard",
     "version": 1, "player_id": "ply_ded11f40-3e30-4921-b019-f7f6bc3e9c83", "player_name": "richard",
     "is_filler": false}
  ],
  "participant_scores": [
    {"position": 0, "score": 162.0},
    {"position": 1, "score": 224.0},
    {"position": 2, "score": 184.0},
    {"position": 3, "score": 214.0}
  ]
}
```

`status == "completed"`; `replay_url` non-null; seat 1 = `escrow-drafter` **v4** / `daveey`
(`5153a6f7-…`) and seat 2 = `escrow-swapper` **v4** / `daveey-1` (`228bbef6-…`) — the exact v4
champion UUIDs. Seats 0 and 3 are the two third-party baseline players, `is_filler: false`.

Corroboration, round 12: `ereq_75309243-c07a-46f5-ac12-b61073601343` — `completed`,
`replay_url = https://softmax-public.s3.amazonaws.com/replays/07dc1d7f-e258-47bf-873d-bbea2521a80c.replay`.

**Status: TRUE — ereq_78850370-c03e-4fc0-b663-a59bb5d73f93 completed with replay
`…/replays/1839e1b7-3f2c-418c-9eeb-28c19fd6b5dd.replay`; both v4 champions seated as daveey and
daveey-1.**

---

## 4. Replay bytes are valid and show the game — **TRUE**

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/1839e1b7-3f2c-418c-9eeb-28c19fd6b5dd.replay" -o /tmp/ev/ep.replay
ls -l /tmp/ev/ep.replay
jq -e . /tmp/ev/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
python3 -c "open('/tmp/ev/ep.replay','rb').read().decode('utf-8'); print('python strict utf-8 decode: ok')"
jq -r '.protocol, .results.reason' /tmp/ev/ep.replay
```
```
-rw-r--r-- 1 root root 90898 Aug 23 18:49 /tmp/ev/ep.replay
strict UTF-8 JSON: ok
python strict utf-8 decode: ok
escrow.replay.v1
complete
```

`protocol` = `escrow.replay.v1` matches the manifest declaration; `results.reason` = `complete`
(not `deadline`, so no design-note exception is needed).

Seat → player map, read from the replay itself:
```bash
jq -r '.names, .policyNames' /tmp/ev/ep.replay
```
```json
["Flywheel","Ratchet","Bolt","Piston"]
["relh","daveey","daveey-1","richard"]
```
→ champion seats are **1 (`daveey`, escrow-drafter:v4)** and **2 (`daveey-1`, escrow-swapper:v4)**.

Event census:
```bash
jq -r '[.events[].kind]|group_by(.)|map({(.[0]):length})|add' /tmp/ev/ep.replay
```
```json
{"end":1,"expire":4,"fill":47,"give":5,"move":64,"offer":31,"reject":2,
 "settle":27,"sign":27,"start":1,"turn":16}
```

### Fallback (scripted-move) count — the metric attempts 1 and 2 failed on

```bash
jq -r '[.events[]|select(.kind=="move")|{seat,scripted}]|group_by(.seat)
       |map({seat:.[0].seat,total:length,scripted:(map(select(.scripted==true))|length)})' /tmp/ev/ep.replay
```
```json
[{"seat":0,"total":16,"scripted":0},
 {"seat":1,"total":16,"scripted":0},
 {"seat":2,"total":16,"scripted":0},
 {"seat":3,"total":16,"scripted":0}]
```

```bash
jq -r '[.events[]|select(.kind=="move" and (.seat==1 or .seat==2))]
       |{total:length,scripted:(map(select(.scripted==true))|length)}' /tmp/ev/ep.replay
```
```json
{"total":32,"scripted":0}
```

**Champion-seat scripted moves: 0 of 32 (0.0 %).** Not a small minority — *zero*. (Attempt 1:
47–59 %. Attempt 2: 31–41 %. Threshold in the brief: single digits of 32 passes.)
All four seats, including the two third-party baselines, ran 16/16 live LLM turns.

Round 12 corroboration, same command against `…/replays/07dc1d7f-….replay`:
```json
[{"seat":0,"total":16,"scripted":0},{"seat":1,"total":16,"scripted":0},
 {"seat":2,"total":16,"scripted":0},{"seat":3,"total":16,"scripted":0}]
```
→ champion seats **0 of 32 scripted in round 12 as well**.

### Signs and settlements — the symptom remediation 2 targeted

Attempt 2's round 9 had **0 signs and 0 settlements** (14 offers, all expired). Round 13:

```bash
jq -r '[.events[]|select(.kind=="sign")]|group_by(.seat)|map({seat:.[0].seat,signs:length})' /tmp/ev/ep.replay
jq -r '.results' /tmp/ev/ep.replay
```
```json
[{"seat":0,"signs":4},{"seat":1,"signs":2},{"seat":2,"signs":14},{"seat":3,"signs":7}]
```
```json
{
  "names": ["relh","daveey","daveey-1","richard"],
  "scores": [162,224,184,214],
  "hearts": [162,224,184,214],
  "fills": [16,12,26,14],
  "signed": [12,9,19,14],
  "forfeits": [0,0,0,0],
  "profiles": ["Forester","Factor","Mason","Farmer"],
  "turns": 16,
  "maxTurns": 16,
  "heartsMinted": 704,
  "reason": "complete"
}
```

| round | sign events | settle events | offer events | expire | champion signed (results.signed seats 1,2) |
|---|---|---|---|---|---|
| 13 (latest v4) | **27** | **27** | 31 | 4 | 9 and 19 |
| 12 (v4) | **29** | **29** | 30 | 1 | — |
| 9 (attempt 2, v3) | 0 | 0 | 14 | 14 | 0 and 0 |

Every one of the 27 sign events in round 13 has `ok=true`; there are 27 matching `settle` events,
all on the `then` branch with `held=true` — the contracts are being drafted, signed, and settled,
which is what the game is about. Only 2 `reject` events occur, both the benign
`contract_cap: … already has 4 live contracts`.

**Status: TRUE — strict UTF-8 JSON (jq -e and python `bytes.decode('utf-8')` both clean),
`protocol == escrow.replay.v1`, `results.reason == "complete"`, champion-seat scripted/fallback
moves **0 of 32 (0 %)**, 27 signs and 27 settlements (round 12: 29/29).**

---

## 5. Hosted game log is clean — **TRUE**

The endpoint returns the container logs as Python `bytes` reprs (`b'…'`), one per container. Raw
line-greps undercount because a whole container is a single physical line, so the reprs are decoded
with `ast.literal_eval` before grepping.

```bash
curl -sS "$BASE/episode-requests/ereq_78850370-c03e-4fc0-b663-a59bb5d73f93/artifacts/logs" \
     "${AUTH[@]}" "${ELEV[@]}" -o /tmp/ev/logs.raw
wc -c /tmp/ev/logs.raw
python3 /tmp/decode_logs.py /tmp/ev/logs.raw > /tmp/ev/logs.txt   # ast.literal_eval each b'…' repr
wc -c /tmp/ev/logs.txt
grep -n '^===== container' /tmp/ev/logs.txt
```
```
155956 /tmp/ev/logs.raw
155443 /tmp/ev/logs.txt
1:===== container: coworld-init-config =====
3:===== container: bedrock-sidecar =====
288:===== container: game =====
395:===== container: worker =====
```
(All four containers decoded; 155 443 of 155 956 bytes recovered, the difference being the `b'`/`'`
wrappers and the section headers. Zero `UNDECODABLE` markers.)

The required grep, verbatim:
```bash
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/ev/logs.txt || echo CLEAN
```
```
CLEAN
```

Exact per-pattern counts (occurrence counts, case-insensitive, not line counts):
```bash
for p in 'falling back' 'LLM provider is unavailable' 'cut off at max_tokens' 'rejected'; do
  printf '%-32s ' "$p"; grep -oiE "$p" /tmp/ev/logs.txt | wc -l; done
```
```
falling back                     0
LLM provider is unavailable      0
cut off at max_tokens            0
rejected                         0
```

Wider sweep for near-misses, all zero:
```bash
for p in 'fallback' 'reject' 'scripted' 'max_tokens' 'unavailable' 'illegal' 'invalid'; do
  printf '%-14s ' "$p"; grep -oiE "$p" /tmp/ev/logs.txt | wc -l; done
```
```
fallback       0
reject         0
scripted       0
max_tokens     0
unavailable    0
illegal        0
invalid        0
```

Because every count is zero, the Bedrock-capacity exception for `LLM provider is unavailable` is
**not needed and not invoked** — no cross-check against another LLM coworld was required.

What *is* present is the benign retry path: six first-attempt validator rejections that were
re-prompted and succeeded on a later attempt within the same turn (no fallback, no scripted move):
```bash
grep -oE 'escrow llm: seat . attempt . failed:.*' /tmp/ev/logs.txt
```
```
escrow llm: seat 3 attempt 0 failed: unfunded: you cannot lock 5 GRAIN after this turn's other actions
escrow llm: seat 3 attempt 0 failed: you cannot afford to give 5 GRAIN
escrow llm: seat 3 attempt 0 failed: you cannot pay the ASK of C14
escrow llm: seat 3 attempt 0 failed: you cannot afford to give 4 GRAIN
escrow llm: seat 1 attempt 0 failed: bad_due: no legal DUE turn remains before the horizon
escrow llm: seat 3 attempt 0 failed: bad_due: no legal DUE turn remains before the horizon
```
Only **one** of the six is on a champion seat (seat 1, `bad_due`), and none is the
`C<n> is not addressed to you` sign that dominated attempts 1 and 2 (22 of 35 there) — that class
has disappeared entirely, which is exactly what the `SIGNABLE NOW` observation was built to do.

Round 12 corroboration, same decode-then-grep against
`ereq_75309243-c07a-46f5-ac12-b61073601343` (157 050 raw bytes → 156 604 decoded):
```
falling back                     0
LLM provider is unavailable      0
cut off at max_tokens            0
rejected                         0
```
with 7 retried attempt-0 failures (`syntax: line 6 must start with THEN, got "THEME"`, 4 ×
`unfunded: …`, `you cannot afford to give 4 GRAIN`, `anthropic error 500:`), all recovered.

**Status: TRUE — CLEAN. 0 `falling back`, 0 `LLM provider is unavailable`, 0
`cut off at max_tokens`, 0 `rejected` in the fully decoded 155 KB log of round 13 (and the same
four zeros in round 12).**

---

## 6. The public page uses the static replay path — **TRUE**

**Source used: two — (a) the page's SSR payload, and (b) the replay-session API the page's JS
calls.** The raw-HTML iframe grep is recorded first and treated as *unknown*, not as a failure,
per `playbooks/observatory-api.md` §Featured match / replay route.

(a) Raw HTML grep — finds nothing, as expected for the client-rendered iframe:
```bash
curl -sS "https://softmax.com/escrow" -o /tmp/ev/page.html; wc -c /tmp/ev/page.html
grep -o '<iframe[^>]*src="[^"]*"' /tmp/ev/page.html || echo "NO IFRAME IN RAW HTML (client-rendered)"
```
```
401519 /tmp/ev/page.html
NO IFRAME IN RAW HTML (client-rendered)
```

(b) Featured match, server-rendered into the page's SSR payload at `state.playlist[0]`
(excerpt of the fetched HTML, unescaped):
```
"state":{"leagueId":"league_cc074076-5938-403e-81db-d278c031db6d","playlist":[
 {"episodeId":"cc7810b9-0b67-49d7-b485-540b954df22e",
  "coworldId":"cow_9b73db59-4be9-4a59-9e56-5eed9151a871",
  "coworldName":"escrow","coworldVersion":"0.1.3",
  "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/1839e1b7-3f2c-418c-9eeb-28c19fd6b5dd.replay",
  "finishedAt":"2026-08-23T18:45:02.850701Z","roundNumber":13,"episodeNumber":1,
  "code":"escrow.r13.e1",
  "matchup":{"divisionId":"div_a8171f6e-62bd-41e5-b470-f15d675faee9","divisionName":"Competition",
   "first":{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
            "score":1071.971968427456,"score_label":"Elo","rounds_played":12,"episode_wins":13,
            "win_rate":0.65,"policy_label":"escrow-drafter:v4"},
   "second":{"rank":2,"player_id":"ply_ded11…
```
A featured match **is present**: `escrow.r13.e1` — **round 13**, the very episode verified in
checks 3–5, on `cow_9b73db59-…` **v0.1.3**, the new coworld. It is **not stale**: the v0.1.2
coworld `cow_add93c03-…` that attempt 2 saw does not appear. No polling retries were needed (1 of
the 3 allowed attempts used).

(c) The iframe `src` the page's JS resolves:
```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_9b73db59-4be9-4a59-9e56-5eed9151a871",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/1839e1b7-3f2c-418c-9eeb-28c19fd6b5dd.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_9b73db59-4be9-4a59-9e56-5eed9151a871/sha256%3Af5e3e157c60491b881720fbefbe8a5c4e7040d71a7e47ac37f8b4948a8c64c40/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F1839e1b7-3f2c-418c-9eeb-28c19fd6b5dd.replay&v=2",
  "ready": true
}
```

Path assertions:
- contains `/v2/coworlds/replays/static/` ✔ — **not** a `/client/replay` pod URL ✔
- `<cow_id>` = `cow_9b73db59-4be9-4a59-9e56-5eed9151a871` = the **new** v0.1.3 coworld ✔
- `<sha>` = `sha256%3Af5e3e157c60491b881720fbefbe8a5c4e7040d71a7e47ac37f8b4948a8c64c40`, the
  URL-encoded manifest hash from `STATE.coworld.manifest_sha` and `release-result.json` ✔
- ends `/index.html?replay=<s3 url>` with the round-13 replay ✔, and `ready: true` ✔

Third source, recorded for completeness (and consistent with the platform-wide behaviour the
playbook documents — `featured_match` is `null` for every coworld, so it is not evidence either
way):
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)[]|select(.name=="escrow")
          |{id,version,canonical,replay_viewer,featured_match}'
```
```json
{"id":"cow_9b73db59-4be9-4a59-9e56-5eed9151a871","version":"0.1.3","canonical":true,"replay_viewer":null,"featured_match":null}
{"id":"cow_add93c03-c2c9-455e-bc63-d2495fdcd2af","version":"0.1.2","canonical":false,"replay_viewer":null,"featured_match":null}
{"id":"cow_640c000d-b4f8-40f3-8a96-6cc7e753b65a","version":"0.1.1","canonical":false,"replay_viewer":null,"featured_match":null}
{"id":"cow_65c18d00-ccaf-4259-bcaa-9046e7072ca9","version":"0.1.0","canonical":false,"replay_viewer":null,"featured_match":null}
```
v0.1.3 is the canonical coworld.

**Status: TRUE — featured match `escrow.r13.e1` on `cow_9b73db59-…` v0.1.3 (source: SSR
`state.playlist[0]`); iframe src is the static route
`…/v2/coworlds/replays/static/cow_9b73db59-4be9-4a59-9e56-5eed9151a871/sha256%3Af5e3e157…/index.html?replay=…`
with `ready:true` (source: `POST /coworlds/replays/session`). No `/client/replay` URL anywhere.**

---

## 7. Certification declared the static bundle — **TRUE**

**Source: the committed `runs/2026-08-23-escrow/release-result.json`** — the artifact phase 40
downloaded and committed for the v0.1.3 release (`git log` for the file: commit `720ec5e`
"escrow: 60 remediation-2 released v0.1.3 (labels :v4)"). No `gh run download` was needed; the file
was present. `/tmp` was not consulted.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-23-escrow/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Provenance of that file, so it is verifiably *this* run's v0.1.3 release and not a stale copy:
```bash
jq -r '.version, .cow_id, .manifest_sha, .ok, .canonical' runs/2026-08-23-escrow/release-result.json
```
```
0.1.3
cow_9b73db59-4be9-4a59-9e56-5eed9151a871
sha256:f5e3e157c60491b881720fbefbe8a5c4e7040d71a7e47ac37f8b4948a8c64c40
true
true
```
— matching `STATE.coworld` and the `<cow_id>`/`<sha>` in the check-6 iframe src exactly.

Tail of the certification transcript from the same file (10/10 steps passed):
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

**Status: TRUE — `.certify.replay_liveness` contains
`Replay liveness: skipped (static replay bundle declared`, read from the committed
`runs/2026-08-23-escrow/release-result.json` (v0.1.3, release run 32657361152).**

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

### (a) Fresh dispatch against the check-6 iframe src

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_9b73db59-4be9-4a59-9e56-5eed9151a871/sha256%3Af5e3e157c60491b881720fbefbe8a5c4e7040d71a7e47ac37f8b4948a8c64c40/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F1839e1b7-3f2c-418c-9eeb-28c19fd6b5dd.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90   # dispatched 2026-08-23T18:50:35Z
sleep 8
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:4][]|[.databaseId,.createdAt,.status]|@tsv'
```
```
32659327500	2026-08-23T18:50:37Z	in_progress      <-- created after the 18:50:35Z dispatch: this run
32656128193	2026-08-23T17:50:31Z	completed        (attempt 2, round 9 — NOT reused)
32654376748	2026-08-23T17:17:53Z	completed
32652062253	2026-08-23T16:34:03Z	completed        (attempt 1, round 3 — NOT reused)
```
```bash
gh run watch 32659327500 -R Metta-AI/coworld-builder --exit-status; echo "exit=$?"
```
```
✓ main viewer-check · 32659327500
JOBS
✓ viewer-check in 30s (ID 97242972469)
  ✓ Set up job / ✓ actions/checkout@v5 / ✓ actions/setup-node@v4
  ✓ Install Playwright (pinned 1.55.0)
  ✓ Load the viewer
  ✓ Summary
  ✓ Upload the evidence
  ✓ Fail if the viewer did not load
  ✓ Complete job
exit=0
```
```bash
mkdir -p runs/2026-08-23-escrow/viewer-check/round13-32659327500
gh run download 32659327500 -R Metta-AI/coworld-builder -n viewer-check \
   -D runs/2026-08-23-escrow/viewer-check/round13-32659327500
ls -l runs/2026-08-23-escrow/viewer-check/round13-32659327500
```
```
-rw-r--r-- 1 root root      0 Aug 23 18:51 smoke-stderr.txt
-rw-r--r-- 1 root root    310 Aug 23 18:51 smoke-stdout.txt
-rw-r--r-- 1 root root   1112 Aug 23 18:51 viewer-smoke.json
-rw-r--r-- 1 root root 388391 Aug 23 18:51 viewer-smoke.png
```

### (b) The readouts, verbatim

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-23-escrow/viewer-check/round13-32659327500/viewer-smoke.json
```
```
{"loaded":true,"ms":652,"clock":"TURN 0","scorebug":"","feed_lines":0}
```
```bash
jq -c '.signals' runs/2026-08-23-escrow/viewer-check/round13-32659327500/viewer-smoke.json
```
```
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```
```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-23-escrow/viewer-check/round13-32659327500/viewer-smoke.json
```

| scrub position | clock readout |
|---|---|
| 0 % | `TURN 0` |
| 50 % | `TURN 0 / 16 · WAITING ON 4` |
| 100 % | `TURN 16 / 16 · FINAL` |

```bash
jq -r '.failure // "no failure"' runs/2026-08-23-escrow/viewer-check/round13-32659327500/viewer-smoke.json
```
```
no failure
```
```bash
cat runs/2026-08-23-escrow/viewer-check/round13-32659327500/smoke-stdout.txt
```
```
{"loaded":true,"ms":652,"clock":"TURN 0","scorebug":"","feed_lines":0}
scrub readouts: 0%="TURN 0"  50%="TURN 0 / 16 · WAITING ON 4"  100%="TURN 16 / 16 · FINAL"
artifacts: /home/runner/work/coworld-builder/coworld-builder/viewer-smoke.png /home/runner/work/coworld-builder/coworld-builder/viewer-smoke.json
```
`smoke-stderr.txt` is 0 bytes. Full json also records
`"status":"REPLAY"`, `"loading_text":"LOADING REPLAY…"`, `"console_tail":["[bridge] loading","[bridge] ready"]`.

**Both gating conditions hold:** `loaded: true` (via both `data-replay-loaded="true"` and the
`coworld-replay` bridge reaching `ready`), and the **three clock readouts differ** from one another.
`scorebug: ""` / `feed_lines: 0` are the known generic-probe selector gap — recorded, not failed;
the screenshot below shows a fully populated scorebug strip and per-seat feed, so the counts are a
probe artefact, not an empty viewer.

### (c) The replay JSON the viewer was asked to draw

Early (turns 0–2):
```
turn seat kind
0	0	move	scripted=false say=Forester seeking ore for commission fills. 4 timber for 4 ore, due next turn.
0	1	move	scripted=false say=Ratchet here. I need ore and timber to fill commissions. Looking to buy short-dated performance bonds.
0	2	move	scripted=false say=4 ore for 4 timber, swap next turn. Need timber to fill commissions.
0	0	offer	C1 target=1 | OFFER Ratchet\nLOCK 4 TIMBER\nASK 4 ORE\nDUE 1\nIF ALWAYS\nTHEN SWAP\nELSE KEEP
0	2	offer	C2 target=0 | OFFER Flywheel\nLOCK 4 ORE\nASK 4 TIMBER\nDUE 1\nIF ALWAYS\nTHEN SWAP\nELSE KEEP
0	3	offer	C3 target=2 | OFFER Bolt\nLOCK 4 GRAIN\nASK 10 HEARTS\nDUE 1\nIF ALWAYS\nTHEN SWAP\nELSE KEEP
0	0	fill	n=2 hearts=20
0	1	fill	n=2 hearts=24
1	0	sign	C2 ok=true
1	2	sign	C3 ok=true
1	1	offer	C5 target=0 | OFFER Flywheel\nLOCK 2 ORE\nASK 4 TIMBER\nDUE 2\nIF ALWAYS\nTHEN SWAP\nELSE KEEP
1	2	settle	C2 branch=then payout=SWAP held=true
1	3	settle	C3 branch=then payout=SWAP held=true
2	0	sign	C5 ok=true
2	2	sign	C6 ok=true
```

Middle (turns 7–8):
```
7	0	sign	C18 ok=true
7	3	sign	C16 ok=true
7	3	sign	C17 ok=true
7	1	offer	C19 target=2 | OFFER Bolt\nLOCK 4 TIMBER\nASK 10 HEARTS\nDUE 8\nIF ALWAYS\nTHEN SWAP\nELSE KEEP
7	2	offer	C20 target=3 | OFFER Piston\nLOCK 5 ORE\nASK 5 GRAIN\nDUE 8\nIF ALWAYS\nTHEN SWAP\nELSE KEEP
7	0	settle	C16 branch=then payout=SWAP held=true
7	2	settle	C17 branch=then payout=SWAP held=true
7	3	settle	C18 branch=then payout=SWAP held=true
8	2	sign	C19 ok=true
8	3	sign	C20 ok=true
8	1	settle	C19 branch=then payout=SWAP held=true
8	2	settle	C20 branch=then payout=SWAP held=true
```

Late (turns 14–16):
```
14	2	sign	C31 ok=true
14	3	settle	C31 branch=then payout=SWAP held=true
14	1	fill	n=1 hearts=12
14	2	fill	n=2 hearts=20
15	0	move	scripted=false say=Turn 15/16: have 2 ore, 26 grain, 59 timber. Need 4 ore total for final two commissions (short 2). Timber converts; banking hearts for horizon.
15	1	move	scripted=false say=Turn 15 of 16: Converting to hearts. Need 2 more commissions (12 total). Have 6 ore, 2 grain, 7 timber, 212 hearts. Grain shortage blocks me…
15	2	move	scripted=false say=Turn 15 of 16: filling 2 commissions, need 4 grain + 4 timber. Have 21 grain, 6 timber. Banking for final turn.
15	0	fill	n=2 hearts=20
15	1	fill	n=1 hearts=12
15	2	fill	n=2 hearts=20
16	-	end	complete
```

Champion-seat private reasoning, showing the remediation-2 observation being used (`text` field of
`kind=="move"`, seats 1 and 2, turns 5 and 11):
```
turn 5 seat 1 (daveey)   "Turn 5: SPENDABLE = 5 ore, 7 grain, 3 timber, 76 hearts. C13 posted last turn
                          (LOCK 4 timber, ASK 10 hearts, DUE 5) is OFFERED, not signable by me. No contracts
                          in SIGNABLE NOW. … If I lock anything, I drop below 2+2+2, blocking my commission
                          fill at turn 6. Do not offer. SIGNABLE NOW is empty—no contracts t…"
turn 5 seat 2 (daveey-1) "Turn 5: SPENDABLE ORE 22, GRAIN 21, TIMBER 1, HEARTS 58. Signed C13 (Ratchet offers
                          4 TIMBER for 10 HEARTS, due turn 5, ALWAYS SWAP). After signing C13, LEFT = 58 - 10
                          = 48 hearts. … Posting new offer C15: 5 ORE for 5 GRAIN to Piston (highest grain
                          holder at 8 free), due t…"
turn 11 seat 1 (daveey)  "Turn 11 of 16. Commissions filled: 7 of max 16 … SPENDABLE: 6 ore, 13 grain, 2 timber,
                          147 hearts. C25 (my offer to Bolt: 2 timber for 5 hearts) settles THIS TURN at end…"
turn 11 seat 2 (daveey-1)"Turn 11 of 16. SPENDABLE = 53 ORE, 25 GRAIN, 8 TIMBER, 101 HEARTS. C24: pay 5 GRAIN
                          (for 5 TIMBER). C25: pay 5 HEARTS (for 2 TIMBER). After signing both … immediately
                          +7 TIMBER … Fill 2 commissions … No offer posted (already at 4 live contracts)…"
```

`.results` (repeated from check 4 for reconciliation):
```json
{"names":["relh","daveey","daveey-1","richard"],"scores":[162,224,184,214],
 "hearts":[162,224,184,214],"fills":[16,12,26,14],"signed":[12,9,19,14],
 "forfeits":[0,0,0,0],"profiles":["Forester","Factor","Mason","Farmer"],
 "turns":16,"maxTurns":16,"heartsMinted":704,"reason":"complete"}
```

### The spectator-judgment paragraph

**It is legible and it shows the game.** The rendered screenshot
(`runs/2026-08-23-escrow/viewer-check/round13-32659327500/viewer-smoke.png`, 388 KB, captured at
scrub 100 %) is a fully drawn frame, not a loading spinner and not an empty canvas. Across the top
is the transport bar reading `TURN 16 / 16 · FINAL` with the `ESCROW` wordmark left and a
`REPLAY / « LOG` control right; immediately below is the four-seat scorebug strip —
`relh 162 FORESTER 7/22/59`, `daveey 224 FACTOR 4/0/5`, `daveey-1 184 MASON 77/42/2`,
`richard 214 FARMER 0/0/2` — i.e. it says who is winning and with what stock. The playfield behind
shows the four cog avatars in their quadrants with their heart totals (162 / 224 / 184 / 214) and
their per-seat goods bars, an `ESCROW BOARD` panel in the middle, and each seat's last spoken line
in a feed bubble ("filling 2 commissions, need 4 grain + 4 timber…", "Converting grain and ore to
hearts before final turn…"). Centred over it is the endcard: `FINAL — 16 TURNS · 704 HEARTS MINTED`,
`daveey — MOST HEARTS AT HORIZON`, and a ranked table with PROFILE / HEARTS / FILLS / SIGNED /
FORFEITS columns reading `1 daveey Factor 224 12 9 0`, `2 richard Farmer 214 14 14 0`,
`3 daveey-1 Mason 184 26 19 0`, `4 relh Forester 162 16 12 0`. Every one of those numbers matches
`.results` in the replay JSON above exactly — hearts `[162,224,184,214]`, fills `[16,12,26,14]`,
signed `[12,9,19,14]`, forfeits all 0, `heartsMinted: 704` — so the picture is a faithful
rendering of the episode, not decoration. Along the bottom is the scrubber with the per-turn
momentum graph, the contract-event tick marks, a play control and a `225 / 225` event counter.
That the clock advanced from `TURN 0` to `TURN 16 / 16 · FINAL` under scrubbing proves the viewer
is not frozen on one frame. The one soft spot: at 50 % the clock read
`TURN 0 / 16 · WAITING ON 4` rather than a mid-episode turn, i.e. the probe's mid-scrub landed
while the viewer was still resolving turn 0 (the same readout appeared in attempt 2; an earlier run
on a different episode, 32651276492, did show `TURN 8 / 16` at 50 %). It is a probe-timing
artefact rather than a stall, since the 100 % readout advanced correctly. **The chrome is the
starter's chrome** — the same transport strip, scorebug row, momentum-graph scrubber and centred
endcard as paintbot / raid / hive / bullwhip, re-skinned with escrow's goods and profiles; this is
not a cogame-gridlock-style rewrite. `scorebug: ""` and `feed_lines: 0` in the probe json are the
generic selector gap noted above, contradicted by the picture itself.

**Status: TRUE — viewer-check run 32659327500, `loaded: true`, `ms: 652`, `failure: null`, bridge
`["loading","ready"]`; three differing scrub clocks (`TURN 0` / `TURN 0 / 16 · WAITING ON 4` /
`TURN 16 / 16 · FINAL`); screenshot shows the starter chrome with an endcard whose every figure
reconciles against `.results`.**

---

## Summary table

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 12 and 13 (v4), 12 completed overall |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey rank 1, daveey-1 rank 4, 12 rounds each |
| 3 | Latest round's episode request completed with replay | **TRUE** — `ereq_78850370-…` completed, both champions seated |
| 4 | Replay bytes valid and show the game | **TRUE** — strict JSON, `escrow.replay.v1`, `complete`, **0/32** champion fallbacks, 27 signs / 27 settles |
| 5 | Hosted game log clean | **TRUE** — CLEAN; 0 / 0 / 0 / 0 on all four patterns after decoding |
| 6 | Public page uses the static replay path | **TRUE** — featured `escrow.r13.e1` on `cow_9b73db59-…`, static iframe src, `ready:true` |
| 7 | Certification declared the static bundle | **TRUE** — committed `release-result.json` (v0.1.3) |
| 8 | Spectator judgment (viewer executed) | **TRUE** — run 32659327500, `loaded:true`, three differing clocks |

**Verdict: all-true.**

---

## Appendix — attempts 1 and 2 (superseded, kept for continuity only)

**Attempt 1 (16:02–16:43Z, v0.1.0 `cow_65c18d00-…`, champions `escrow-drafter:v1` /
`escrow-swapper:v1`, rounds 2–4).** 6 TRUE / 2 FALSE. Check 4 FALSE: champion-seat scripted
(fallback) moves 59 % / 47 % / 56 % across rounds 4 / 3 / 2. Check 5 FALSE: 19 `falling back` lines,
0 `LLM provider is unavailable`, 0 `cut off at max_tokens` — so no platform exception applied. Root
cause diagnosed as the champion prompts emitting illegal contract-DSL runes (free-stock accounting
before `LOCK`, malformed `IF` grammar, unfunded offers). Viewer-check run 32652062253 (round 3),
`loaded:true`. Remediation 1 was prompt-only: rewrite both champion prompts, release v0.1.1 →
v0.1.2 (`cow_add93c03-…`), resubmit as `:v3`.

**Attempt 2 (17:18–17:56Z, v0.1.2 `cow_add93c03-…`, champions `:v3`, rounds 8 and 9).**
6 TRUE / 2 FALSE — same two checks. Check 4 FALSE: champion-seat scripted moves 13/32 (40.6 %) in
round 9 and 10/32 (31.3 %) in round 8; worse, round 9 recorded **0 sign and 0 settle events** — all
14 offers expired unsigned, so the trading game never actually happened. Check 5 FALSE: 13
`falling back` lines in round 9 (10 in round 8) once the `b'…'` container reprs were decoded; still
0 `LLM provider is unavailable` and 0 `cut off at max_tokens`. Dominant residual cause: 22 of 35
rejected attempts were `C<n> is not addressed to you` (a cog trying to sign a contract offered to
someone else); new minor modes were leading-alias syntax (3/35) and trailing-prose EOF (6/35). The
`unfunded` and `bad_condition` classes from attempt 1 had been eliminated. Viewer-check run
32656128193 (round 9), `loaded:true`. Remediation 2 was therefore **game-side**, not prompt-side:
the turn observation now carries a precomputed `SIGNABLE NOW` list (list membership ≡ validator
legality) and a `SPENDABLE THIS TURN` line, JSON extraction tolerates trailing prose, offer text is
normalised (leading junk stripped, truncated after `ELSE`), and the v4 prompts point at the list.
Released as v0.1.3 (`cow_9b73db59-…`, run 32657361152) with labels `:v4`.

**Effect of remediation 2, measured in this attempt:** champion fallbacks 47–59 % → 31–41 % → **0 %**;
`falling back` log lines 19 → 13 → **0**; sign/settle events 0/0 (round 9) → **27/27** (round 13) and
29/29 (round 12); the `not addressed to you` rejection class no longer appears at all.
