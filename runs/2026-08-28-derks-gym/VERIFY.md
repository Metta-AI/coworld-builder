# VERIFY — derks-gym   (2026-08-28T15:27Z)

Verdict: **all-true (8/8)**

| # | item | verdict |
|---|---|---|
| 1 | ≥2 completed rounds after the fillers were set | **TRUE** — v4-era rounds 10 and 11 |
| 2 | both champions ranked, fillers absent/Baseline | **TRUE** |
| 3 | latest round's episode request completed + replay + participants | **TRUE** |
| 4 | replay bytes valid and show the game (incl. live champion LLM drafts) | **TRUE** |
| 5 | hosted game log clean | **TRUE** |
| 6 | public page uses the static replay path | **TRUE** |
| 7 | certification declared the static bundle | **TRUE** |
| 8 | executed viewer (`loaded:true` + three differing clocks) + spectator judgment | **TRUE** |

**This is phase-60 attempt 2.** Attempt 1 (13:21–13:45Z) found items 4, 5 and 8 false against
coworld `0.1.0` / `cow_81624b16…` / policies `:v1`. That coworld version and those policy versions
are **gone from this file**: every fetch below is against the re-released **0.1.3** and the **v4**
policies, and items 1/3/4/5 are evaluated **only on v4-era rounds (`round_number ≥ 10`)**. Rounds
2–9 completed at the pre-fix v1 policies and 0.1.0 image and are deliberately excluded — measuring
them would re-measure the bug that was fixed. Attempt 1's `viewer-check/` artifact has been
overwritten by this run's.

Ids used (all re-minted since attempt 1):

| thing | value |
|---|---|
| slug | `derks-gym` |
| repo | `Metta-AI/cogame-derks-gym` |
| coworld version | `0.1.3` |
| `$COW` | `cow_03c45b25-de4b-42e1-8e2f-056a496878c4` |
| `manifest_sha` | `sha256:b5e7d1927bb411fe56fa82c9a708bb6332169b69c9ccef080d0c60ef3b629fef` |
| `$L` | `league_44e55a9f-aa40-4523-9ed0-7f86ccc73d08` |
| `$D` | `div_1bc6a659-31e8-40fe-a99b-726c82426998` |
| champion 1 | `derk-drafter-v1:v4` — `daveey`, pv `e06340fb-fa29-4e56-899c-bbe0c47def26` |
| champion 2 | `derk-metagamer-v1:v4` — `daveey-1`, pv `c95d1a91-9102-4265-849e-67b2d0183537` |
| filler 1 | `derk-puffer-forge:v4` — pv `b697f833-dcd8-4b10-b799-1bb77cccc112` |
| filler 2 | `derk-lane-brawler:v4` — pv `36e7252a-021d-4818-ac70-e137ee03a32d` |

Every fetch in this file was made fresh during this phase-60 attempt (2026-08-28 15:07Z–15:27Z),
with the **two documented exceptions** `prompts/60-verify.md` allows:

- **item 7** — the committed `runs/2026-08-28-derks-gym/release-result.json` (phase 40's artifact,
  release run `33182295860`); no re-download was needed.
- **item 8's rendered evidence** — the `viewer-check.yml` run **33184965298**, which *I* dispatched
  at 15:24:13Z during this attempt, downloaded and committed. No artifact from attempt 1 is reused.

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")   # header named; value never printed
ELEV=(-H "X-Use-Elevated-Privileges: true")
```

**Response shapes actually observed this attempt** (recorded, not assumed — they vary run to run):

```bash
$ for e in "rounds?league_id=$L&limit=20" "divisions/$D/leaderboard" "coworlds?limit=200" \
           "rounds/$R11/episode-requests"; do
    printf '%-70s ' "$e"; curl -sS "$BASE/$e" "${AUTH[@]}" \
      | jq -r 'if type=="array" then "array" else "object  keys="+(keys|join(",")) end'; done
rounds?league_id=league_44e55a9f-…&limit=20                            object  keys=entries,limit,offset,total_count
divisions/div_1bc6a659-…/leaderboard                                   array
coworlds?limit=200                                                     array
rounds/round_99e38072-…/episode-requests                               object  keys=entries,next_cursor
```

Every jq below therefore uses `if type=="array" then . else .entries end`. The flat episode-request
route the prompt shows is dead; re-confirmed this attempt:

```bash
$ curl -sS "$BASE/episode-requests?round_id=$R11&limit=20" "${AUTH[@]}" -w "HTTP %{http_code}\n"
{"detail":"Method Not Allowed"}
HTTP 405
$ curl -sSI "$BASE/episode-requests?round_id=$R11" "${AUTH[@]}" | grep -iE '^(HTTP|allow)'
HTTP/2 405
allow: POST
```

I used the nested `GET /rounds/$R/episode-requests` (`playbooks/observatory-api.md` §9), which
returned 200.

---

## 1. ≥2 completed rounds after fillers were set — TRUE

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=30" "${AUTH[@]}" \
 | jq '(if type=="array" then . else .entries end)
       | map(select(.round_number>=10))
       | map({id,round_number,status,error,created_at,completed_at,round_config})
       | sort_by(.round_number)|reverse'
```

```json
[
  {
    "id": "round_99e38072-1158-4922-9192-8806037a9591",
    "round_number": 11,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T15:20:36.126923Z",
    "completed_at": "2026-08-28T15:21:59.531427Z",
    "round_config": {
      "stages": null,
      "purpose": "ladder",
      "entrant_attributions": [
        {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
         "policy_version_id": "e06340fb-fa29-4e56-899c-bbe0c47def26",
         "league_policy_membership_id": "lpm_096b5b78-11f5-42da-a302-ef32716989f3"},
        {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
         "policy_version_id": "c95d1a91-9102-4265-849e-67b2d0183537",
         "league_policy_membership_id": "lpm_b4779716-8216-4c4c-b91b-0ffe83aa74de"}
      ],
      "entrant_policy_version_ids": [
        "e06340fb-fa29-4e56-899c-bbe0c47def26",
        "c95d1a91-9102-4265-849e-67b2d0183537"
      ]
    }
  },
  {
    "id": "round_ebb741e1-6fec-4b74-b4a3-c176bb81cae9",
    "round_number": 10,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T15:05:35.125932Z",
    "completed_at": "2026-08-28T15:06:26.842779Z",
    "round_config": {
      "stages": null,
      "purpose": "ladder",
      "entrant_attributions": [
        {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
         "policy_version_id": "e06340fb-fa29-4e56-899c-bbe0c47def26",
         "league_policy_membership_id": "lpm_096b5b78-11f5-42da-a302-ef32716989f3"},
        {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
         "policy_version_id": "c95d1a91-9102-4265-849e-67b2d0183537",
         "league_policy_membership_id": "lpm_b4779716-8216-4c4c-b91b-0ffe83aa74de"}
      ],
      "entrant_policy_version_ids": [
        "e06340fb-fa29-4e56-899c-bbe0c47def26",
        "c95d1a91-9102-4265-849e-67b2d0183537"
      ]
    }
  }
]
```

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=30" "${AUTH[@]}" \
 | jq -r '[(if type=="array" then . else .entries end)[]
           |select(.status=="completed" and .round_number>=10)]|length'
2
```

**Poll log (bounded at 75 min from 15:07Z; actual elapsed to the second completed v4 round: 15 min).**

| poll (UTC) | v4-era rounds seen |
|---|---|
| 15:07:36 | 10 completed |
| 15:14:50 | 10 completed |
| 15:19:52 | 10 completed |
| 15:23:00 | **10 and 11 completed** → bound not reached, polling stopped |

**Excluded rounds, with their status verbatim.** Round 1 `status: "failed"`,
`error: "Temporal RoundWorkflow failed before settling the round."` — the documented pre-filler
race (`playbooks/observatory-api.md` §6). Rounds 2–9 are `status: "completed"` but every one carries
`entrant_policy_version_ids: ["7574f00d-b281-4f8e-b355-c5b8eb2d8fe0","4309e33f-4218-4ec0-a09b-ffe607e5fc5b"]`
— the **v1** champion policy versions, run against the 0.1.0 image. They are the pre-fix era and are
not counted. Fetched proof of that split:

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=30" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)
          | map({n:.round_number,s:.status,pv:.round_config.entrant_policy_version_ids})|sort_by(.n)'
[{"n":1,"s":"failed","pv":["7574f00d-b281-4f8e-b355-c5b8eb2d8fe0"]},
 {"n":2,"s":"completed","pv":["7574f00d-…","4309e33f-…"]}, … {"n":9,"s":"completed","pv":["7574f00d-…","4309e33f-…"]},
 {"n":10,"s":"completed","pv":["e06340fb-fa29-4e56-899c-bbe0c47def26","c95d1a91-9102-4265-849e-67b2d0183537"]},
 {"n":11,"s":"completed","pv":["e06340fb-fa29-4e56-899c-bbe0c47def26","c95d1a91-9102-4265-849e-67b2d0183537"]}]
```

**"After the fillers were set" — the ordering evidence.** The v4 fillers were replaced before the
round-10 trigger. The registry read confirms exactly the two expected v4 versions and nothing else:

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}" | jq .
```
```json
{
  "filler_policy_versions": [
    {"policy_version_id": "b697f833-dcd8-4b10-b799-1bb77cccc112",
     "policy_id": "fcfb9c49-f896-40cd-98c4-8892de3d76be",
     "policy_name": "derk-puffer-forge", "version": 4,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "display_name": null},
    {"policy_version_id": "36e7252a-021d-4818-ac70-e137ee03a32d",
     "policy_id": "7c0daaa6-29b6-468a-b4ad-0a8f3aa06be3",
     "policy_name": "derk-lane-brawler", "version": 4,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "display_name": null}
  ]
}
```

Exactly two entries, both `version: 4`, ids matching STATE. I do not rest this item on clock
comparison between the sandbox and the server; the direct evidence that **both counted rounds ran
with those fillers in place** is that both *seated* them — round 10's episode request seats
`36e7252a…`/`b697f833…` at positions 2–5 and round 11's seats `b697f833…`/`36e7252a…` at positions
2–5 (both pasted in full under item 3), with `is_filler: true` on positions 2–5 and both replays'
`result.names` reading `["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"]`.

Status: **TRUE** — v4-era rounds **10** (`completed_at 2026-08-28T15:06:26.842779Z`) and **11**
(`completed_at 2026-08-28T15:21:59.531427Z`), both `status: "completed"`, both seating the v4
champions per `entrant_attributions` and the v4 fillers per the episode request. That is 2 ≥ 2.

---

## 2. Both champions ranked, fillers absent — TRUE

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey	derk-drafter-v1:v4	1000.0	10	0.0
2	daveey-1	derk-metagamer-v1:v4	1000.0	10	0.0
```

Full rows (bare array; exactly two entries — fetched 15:26:19Z):

```json
[{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1000.0,"score_label":"MMR","score_value_type":"integer","rounds_played":10,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"derk-drafter-v1:v4","recent_rounds":null},
 {"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":1000.0,"score_label":"MMR","score_value_type":"integer","rounds_played":10,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"derk-metagamer-v1:v4","recent_rounds":null}]
```

Status: **TRUE** — `daveey` and `daveey-1` are both present; `policy_label` is the **v4** champion
on each row (`derk-drafter-v1:v4`, `derk-metagamer-v1:v4`), confirming the leaderboard has picked up
the re-submitted policies; `rounds_played: 10 ≥ 1` for both. `derk-puffer-forge` and
`derk-lane-brawler` are **absent from the leaderboard entirely** — the permitted "fillers absent"
branch. `score` at the configured `initial_rating` 1000.0 with `episode_wins: 0.0` is the elo
bookkeeping for a mirror in which both champions sat on the same (winning) team — see item 3's
`participant_scores` and item 4's `result.team`.

---

## 3. Latest completed round's episode request — TRUE

The latest completed round is **11** (`max_by(.round_number)` over the completed set).

```bash
R11=round_99e38072-1158-4922-9192-8806037a9591
curl -sS "$BASE/rounds/$R11/episode-requests" "${AUTH[@]}" | jq .
```
```json
{
  "entries": [
    {
      "id": "ereq_55ad8e00-2570-4b1f-9a63-73243671b689",
      "status": "completed",
      "coworld_id": "cow_03c45b25-de4b-42e1-8e2f-056a496878c4",
      "round_id": "round_99e38072-1158-4922-9192-8806037a9591",
      "replay_url": "https://softmax-public.s3.amazonaws.com/replays/4af31312-183f-4975-83c4-0f6359719fae.replay",
      "policy_version_ids": [
        "e06340fb-fa29-4e56-899c-bbe0c47def26",
        "c95d1a91-9102-4265-849e-67b2d0183537",
        "b697f833-dcd8-4b10-b799-1bb77cccc112",
        "b697f833-dcd8-4b10-b799-1bb77cccc112",
        "36e7252a-021d-4818-ac70-e137ee03a32d",
        "b697f833-dcd8-4b10-b799-1bb77cccc112"
      ],
      "created_at": "2026-08-28T15:20:37.017147Z"
    }
  ],
  "next_cursor": null
}
```

Note `coworld_id` is `cow_03c45b25-…` — the **0.1.3** coworld, not attempt 1's `cow_81624b16-…`.

```bash
EREQ=ereq_55ad8e00-2570-4b1f-9a63-73243671b689
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url,
        participants:[.participants[]|{position,policy_name,version,player_name,is_filler,policy_version_id}],
        participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/4af31312-183f-4975-83c4-0f6359719fae.replay",
  "participants": [
    {"position":0,"policy_name":"derk-drafter-v1",  "version":4,"player_name":"daveey",  "is_filler":false,"policy_version_id":"e06340fb-fa29-4e56-899c-bbe0c47def26"},
    {"position":1,"policy_name":"derk-metagamer-v1","version":4,"player_name":"daveey-1","is_filler":false,"policy_version_id":"c95d1a91-9102-4265-849e-67b2d0183537"},
    {"position":2,"policy_name":"derk-puffer-forge","version":4,"player_name":"daveey",  "is_filler":true, "policy_version_id":"b697f833-dcd8-4b10-b799-1bb77cccc112"},
    {"position":3,"policy_name":"derk-puffer-forge","version":4,"player_name":"daveey",  "is_filler":true, "policy_version_id":"b697f833-dcd8-4b10-b799-1bb77cccc112"},
    {"position":4,"policy_name":"derk-lane-brawler","version":4,"player_name":"daveey",  "is_filler":true, "policy_version_id":"36e7252a-021d-4818-ac70-e137ee03a32d"},
    {"position":5,"policy_name":"derk-puffer-forge","version":4,"player_name":"daveey",  "is_filler":true, "policy_version_id":"b697f833-dcd8-4b10-b799-1bb77cccc112"}
  ],
  "participant_scores": [
    {"position":0,"score":1.0},{"position":1,"score":1.0},{"position":2,"score":1.0},
    {"position":3,"score":0.0},{"position":4,"score":0.0},{"position":5,"score":0.0}
  ]
}
```

**Round 10's episode request, fetched the same way** (the second counted v4 round, and the one item
6's featured match pointed at until round 11 landed):

```bash
curl -sS "$BASE/rounds/round_ebb741e1-6fec-4b74-b4a3-c176bb81cae9/episode-requests" "${AUTH[@]}" | jq -c '.entries[0]'
{"id":"ereq_01c056aa-cde9-4ca9-a116-e5509c1fff36","status":"completed",
 "coworld_id":"cow_03c45b25-de4b-42e1-8e2f-056a496878c4",
 "round_id":"round_ebb741e1-6fec-4b74-b4a3-c176bb81cae9",
 "replay_url":"https://softmax-public.s3.amazonaws.com/replays/68c73ee7-90f3-4c36-9319-4d9a1e1a651e.replay",
 "policy_version_ids":["e06340fb-fa29-4e56-899c-bbe0c47def26","c95d1a91-9102-4265-849e-67b2d0183537",
  "36e7252a-021d-4818-ac70-e137ee03a32d","b697f833-dcd8-4b10-b799-1bb77cccc112",
  "b697f833-dcd8-4b10-b799-1bb77cccc112","36e7252a-021d-4818-ac70-e137ee03a32d"],
 "created_at":"2026-08-28T15:05:35.406421Z"}

curl -sS "$BASE/episode-requests/ereq_01c056aa-cde9-4ca9-a116-e5509c1fff36" "${AUTH[@]}" \
 | jq -c '{status, participants:[.participants[]|[.position,.policy_name,.version,.player_name,.is_filler]], participant_scores:[.participant_scores[].score]}'
{"status":"completed",
 "participants":[[0,"derk-drafter-v1",4,"daveey",false],[1,"derk-metagamer-v1",4,"daveey-1",false],
  [2,"derk-lane-brawler",4,"daveey",true],[3,"derk-puffer-forge",4,"daveey",true],
  [4,"derk-puffer-forge",4,"daveey",true],[5,"derk-lane-brawler",4,"daveey",true]],
 "participant_scores":[1.0,1.0,1.0,0.0,0.0,0.0]}
```

Status: **TRUE** — `status == "completed"`, non-null `replay_url`, and `participants` naming
**`daveey`** at position 0 (`derk-drafter-v1` **v4**) and **`daveey-1`** at position 1
(`derk-metagamer-v1` **v4**), both `is_filler: false`. The API labels the four filler seats with
their real policy names plus `is_filler: true` rather than `Baseline (N)`; the `Baseline (N)`
renaming appears on the **game** side, in `result.names` and the rendered viewer (items 4 and 8),
which is where the prompt's expectation lands.

---

## 4. Replay bytes are valid and show the game — TRUE

The prompt's `jq -e . /tmp/ep.replay` lines assume a JSON replay. **This coworld's replay is
binary** — format v2: magic `DERK`, `version u8 = 2`, `u32le header_len`, UTF-8 JSON header, then
`tick_count × 60` bytes of post-clamp actions. Ground truth fetched from the repo this attempt:

```bash
curl -sS "https://raw.githubusercontent.com/Metta-AI/cogame-derks-gym/main/server/cogame_derks_gym/replay.py" \
     -o replay.py -w "HTTP %{http_code} size=%{size_download}\n"
HTTP 200 size=9523
$ grep -nE '^MAGIC|^FORMAT_VERSION|BYTES_PER' replay.py
59:MAGIC = b"DERK"
60:FORMAT_VERSION = 2
62:BYTES_PER_TICK = defaults.NUM_HEROES * defaults.ACTIONS_PER_HERO  # 60
```

So the strict-parse step is done in **python3 with `errors="strict"`**, not `jq -e .`.

### 4.0 Fetch

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/4af31312-183f-4975-83c4-0f6359719fae.replay" \
     -o /tmp/v2/ep11.replay -w "HTTP %{http_code} size=%{size_download}\n"
HTTP 200 size=167069
$ sha256sum /tmp/v2/ep11.replay
46f6932b0440bef93177cf72e5c7f4dca4e3e6139199357c96da1aec6a50ffa5
```

### 4.1 Structure and strict parse (round 11)

```
total bytes: 167069 first8: 4445524b02b44100
magic: b'DERK' version: 2
header_len: 16820
strict UTF-8 JSON parse: ok          # json.loads(hdr.decode('utf-8', errors='strict'))
tick_count: 2504 body: 150240 ==tick*60: True
loadout_digest: 2638707600 final_state_digest: 119363842 format_version: 2 catalog_version: v1
sim_wasm_sha256: ff1e47df3135bc248bd638d4ab7728a095549b50f21e2847d50551256235e246
events: 61 draft records: 10
event kinds: {'draft': 1, 'level_spike': 40, 'first_blood': 1, 'tower': 5, 'kill': 12, 'ancient': 1, 'end': 1}
seat_hero_pids: [0, 1, 2, 5, 6, 7] house_hero_pids: [3, 4, 8, 9]
```

### 4.2 `protocol` matches the manifest

The manifest declares no `protocol` string; it declares `game.protocols` (a URI) and a
`game.results_schema` that the replay's `result` object must satisfy. Both fetched fresh:

```bash
curl -sS "$BASE/coworlds/$COW" "${AUTH[@]}" -o cowdetail.json -w "HTTP %{http_code} size=%{size_download}\n"
HTTP 200 size=16023
$ jq -c '{id,name,version,manifest_hash,canonical}' cowdetail.json
{"id":"cow_03c45b25-de4b-42e1-8e2f-056a496878c4","name":"derks-gym","version":"0.1.3",
 "manifest_hash":"sha256:b5e7d1927bb411fe56fa82c9a708bb6332169b69c9ccef080d0c60ef3b629fef","canonical":true}
$ jq -r '.manifest.game.protocols.global.value' cowdetail.json
https://github.com/Metta-AI/cogame-derks-gym/blob/main/docs/PROTOCOL.md
$ jq -c '.manifest.game.replay_viewer' cowdetail.json
{"bundle":"sha256:64475e5b804d13af23146d47ffd25e044cfe7903f9be59dbdbb8c6867acaccfa"}
```

Conformance of the fetched replay's `result` against the fetched manifest's `results_schema`:

```
results_schema required: ['names', 'scores', 'win', 'team', 'winner', 'end_reason', 'final_tick',
  'seed', 'reward_sums', 'ancient_healths', 'agent_stats', 'noop_ticks', 'dead_seats',
  'noop_causes', 'draft', 'draft_fallbacks']
required all present in replay result: True     missing: []
replay result keys not in schema properties: []
schema properties not in replay result: []
end_reason in enum: ancient -> True
```

The manifest's own enum, verbatim:

```bash
$ jq -c '.manifest.game.results_schema.properties.end_reason' cowdetail.json
{"enum":["ancient","tick_cap","wall_clock","sim_fault"],"type":"string","description":"Why the
episode ended: an Ancient fell, the tick cap was reached, the engine's wall-clock budget expired
(tick_cap and wall_clock share the Ancient-health tiebreak), or the sim reported an internal fault
(sim_fault: no winner, draw scores, partial replay). A draft failure is never fatal — it degrades
to the neutral loadout."}
```

### 4.3 `results.reason` (`result.end_reason` here)

```json
{
 "end_reason": "ancient",
 "winner": 0,
 "final_tick": 2504,
 "ancient_healths": [4500.0, 0.0],
 "names": ["daveey", "daveey-1", "Baseline", "Baseline (2)", "Baseline (3)", "Baseline (4)"],
 "scores": [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
 "draft_fallbacks": [false, false, false, false, false, false],
 "noop_ticks": [0, 0, 0, 0, 0, 0],
 "dead_seats": [false, false, false, false, false, false],
 "team": ["radiant", "radiant", "radiant", "dire", "dire", "dire"],
 "win": [true, true, true, false, false, false],
 "seed": 3908205752,
 "noop_causes": [{"timeout":0,"malformed":0,"wrong_tick":0,"disconnected":0,"host_error":0}, … ×6 all zero]
}
```

`end_reason: "ancient"` — an Ancient actually fell (`ancient_healths: [4500.0, 0.0]`). This is the
clean outcome, **not** a `deadline`/`tick_cap`/`wall_clock` degrade, so no documented exception is
needed, and it is not `sim_fault`. `dead_seats` all false, `noop_ticks` all zero, every
`noop_causes` counter zero — no seat ever failed to answer.

### 4.4 The `ancient` event is now emitted (attempt-1 gap, fixed)

Attempt 1 recorded that the engine never emitted a distinct `ancient` event even when an Ancient
fell. In the v4/0.1.3 replay it is present, immediately before `end`, in **both** counted rounds:

```bash
$ # round 11
{"tick": 2503, "kind": "tower",   "pid": 2, "team": 0}
{"tick": 2503, "kind": "ancient", "team": 1}
{"tick": 2504, "kind": "end",     "reason": "ancient"}
$ # round 10
{"tick": 5196, "kind": "tower",   "pid": 2, "team": 0}
{"tick": 5196, "kind": "ancient", "team": 1}
{"tick": 5197, "kind": "end",     "reason": "ancient"}
```

`team: 1` is the dire Ancient falling, consistent with `winner: 0` and `ancient_healths[1] == 0.0`.

### 4.5 Ten draft records; six seat records naming both champions

```
(pid, seat, alias, player_name, team, role, picks, note, source, fallback, fallback_cause, decision_ms) — round 11
{"pid":0,"seat":0,"alias":"Cog-Alpha","player_name":"daveey","team":"radiant","role":"support","picks":{"arm":"arm_needler","tail":"tail_rotor","misc":"misc_battery"},"note":"Fast support: mobility + mana for hook/heal/stun spam. Speed enables positioning for utility skills over raw damage.","source":"seat","fallback":false,"fallback_cause":"none","decision_ms":2903}
{"pid":1,"seat":1,"alias":"Cog-Bravo","player_name":"daveey-1","team":"radiant","role":"assassin","picks":{"arm":"arm_needler","tail":"tail_stinger","misc":"misc_regen"},"note":"Counter flat-damage bursters; scale via hp_gain + damage_gain to dominate mid-late game","source":"seat","fallback":false,"fallback_cause":"none","decision_ms":2390}
{"pid":2,"seat":2,"alias":"Cog-Charlie","player_name":"Baseline","team":"radiant","role":"burst","picks":{"arm":"arm_blaster","tail":"tail_stinger","misc":"misc_battery"},"note":"","source":"seat","fallback":false,"fallback_cause":"none","decision_ms":0}
{"pid":3,"seat":null,"alias":"House-Tank-R","player_name":null,"team":"radiant","role":"tank","picks":{"arm":"arm_none","tail":"tail_none","misc":"misc_none"},"note":"","source":"house","fallback":false,"fallback_cause":"none","decision_ms":0}
{"pid":4,"seat":null,"alias":"House-Carry-R","player_name":null,"team":"radiant","role":"carry","picks":{"arm":"arm_none","tail":"tail_none","misc":"misc_none"},"note":"","source":"house","fallback":false,"fallback_cause":"none","decision_ms":0}
{"pid":5,"seat":3,"alias":"Cog-Delta","player_name":"Baseline (2)","team":"dire","role":"support","picks":{"arm":"arm_blaster","tail":"tail_plate","misc":"misc_battery"},"note":"","source":"seat","fallback":false,"fallback_cause":"none","decision_ms":1}
{"pid":6,"seat":4,"alias":"Cog-Echo","player_name":"Baseline (3)","team":"dire","role":"assassin","picks":{"arm":"arm_needler","tail":"tail_plate","misc":"misc_regen"},"note":"brawl build","source":"seat","fallback":false,"fallback_cause":"none","decision_ms":1}
{"pid":7,"seat":5,"alias":"Cog-Foxtrot","player_name":"Baseline (4)","team":"dire","role":"burst","picks":{"arm":"arm_blaster","tail":"tail_stinger","misc":"misc_battery"},"note":"","source":"seat","fallback":false,"fallback_cause":"none","decision_ms":1}
{"pid":8,"seat":null,"alias":"House-Tank-D","player_name":null,"team":"dire","role":"tank","picks":{"arm":"arm_none","tail":"tail_none","misc":"misc_none"},"note":"","source":"house","fallback":false,"fallback_cause":"none","decision_ms":0}
{"pid":9,"seat":null,"alias":"House-Carry-D","player_name":null,"team":"dire","role":"carry","picks":{"arm":"arm_none","tail":"tail_none","misc":"misc_none"},"note":"","source":"house","fallback":false,"fallback_cause":"none","decision_ms":0}
```

**10 records.** `source: "seat"` for the six seated pids `0,1,2,5,6,7`; `source: "house"` for
`3,4,8,9`. `player_name` is **`daveey`** on pid 0 and **`daveey-1`** on pid 1 — both champions named.

### 4.6 The two champion seat records, verbatim

```json
{
 "alias": "Cog-Alpha",
 "applied": {"base_damage": 40.0, "base_health": 400.0, "base_mana": 400.0, "basic_attack_cd": 5,
             "damage_gain_per_level": 10, "hp_gain_per_level": 100, "mana_gain_per_level": 80,
             "move_speed": 1.149999976158142},
 "decision_ms": 2903,
 "fallback": false,
 "fallback_cause": "none",
 "note": "Fast support: mobility + mana for hook/heal/stun spam. Speed enables positioning for utility skills over raw damage.",
 "picks": {"arm": "arm_needler", "misc": "misc_battery", "tail": "tail_rotor"},
 "pid": 0,
 "player_name": "daveey",
 "role": "support",
 "seat": 0,
 "source": "seat",
 "team": "radiant"
}
{
 "alias": "Cog-Bravo",
 "applied": {"base_damage": 40.0, "base_health": 400.0, "base_mana": 300.0, "basic_attack_cd": 5,
             "damage_gain_per_level": 18, "hp_gain_per_level": 160, "mana_gain_per_level": 65,
             "move_speed": 1.0},
 "decision_ms": 2390,
 "fallback": false,
 "fallback_cause": "none",
 "note": "Counter flat-damage bursters; scale via hp_gain + damage_gain to dominate mid-late game",
 "picks": {"arm": "arm_needler", "misc": "misc_regen", "tail": "tail_stinger"},
 "pid": 1,
 "player_name": "daveey-1",
 "role": "assassin",
 "seat": 1,
 "source": "seat",
 "team": "radiant"
}
```

### 4.7 The champions' decisions are NOT the scripted fallback — the attempt-1 failure, resolved

The brief's test: *if a champion's record exactly matches its seat-role's row of the puffer-forge
table **and** `decision_ms` ≤ a few ms, that is the scripted fallback again → FALSE.* Neither
conjunct holds. `design.md` §Scripted baselines (fillers, cert fixture), lines 342–347:

| role | arm | tail | misc |
|---|---|---|---|
| support | `arm_blaster` | `tail_plate` | `misc_battery` |
| assassin | `arm_needler` | `tail_rotor` | `misc_focus` |
| burst | `arm_blaster` | `tail_stinger` | `misc_battery` |

Against that table, over **both** counted v4 rounds:

| round | seat | role | champion's picks | puffer-forge row for that role | match? | `decision_ms` | `note` |
|---|---|---|---|---|---|---|---|
| 10 | 0 `daveey` | support | `arm_needler`/`tail_rotor`/`misc_battery` | `arm_blaster`/`tail_plate`/`misc_battery` | **no** (arm+tail differ) | **3577** | non-empty |
| 10 | 1 `daveey-1` | assassin | `arm_needler`/`tail_stinger`/`misc_regen` | `arm_needler`/`tail_rotor`/`misc_focus` | **no** (tail+misc differ) | **3278** | non-empty |
| 11 | 0 `daveey` | support | `arm_needler`/`tail_rotor`/`misc_battery` | `arm_blaster`/`tail_plate`/`misc_battery` | **no** | **2903** | non-empty |
| 11 | 1 `daveey-1` | assassin | `arm_needler`/`tail_stinger`/`misc_regen` | `arm_needler`/`tail_rotor`/`misc_focus` | **no** | **2390** | non-empty |

```
$ # decision_ms / note / fallback for the champion seats across both v4 rounds
r10 daveey    role=support   picks=arm_needler/tail_rotor/misc_battery  decision_ms= 3577 fallback=False cause=none note='Speed+mana for hook positioning, fast attacks for harass, mo…'
r10 daveey-1  role=assassin  picks=arm_needler/tail_stinger/misc_regen  decision_ms= 3278 fallback=False cause=none note='Counter flat damage burst; scale via hp_gain+damage_gain to …'
r11 daveey    role=support   picks=arm_needler/tail_rotor/misc_battery  decision_ms= 2903 fallback=False cause=none note='Fast support: mobility + mana for hook/heal/stun spam. Speed…'
r11 daveey-1  role=assassin  picks=arm_needler/tail_stinger/misc_regen  decision_ms= 2390 fallback=False cause=none note='Counter flat-damage bursters; scale via hp_gain + damage_gai…'
```

Four independent pieces of evidence, all fetched:

1. **`decision_ms` is in the thousands, not 1.** 2390–3577 ms across four champion drafts — the
   shape of a network round trip to a model endpoint. Attempt 1's four records all read `1`.
2. **`derk-metagamer-v1` carries a non-empty `note`**, which its system prompt requires
   ("name, in a few words, the enemy build you are countering"): *"Counter flat-damage bursters;
   scale via hp_gain + damage_gain to dominate mid-late game"*. Attempt 1's was `""`.
3. **The note text differs between rounds 10 and 11 for the same policy** — `daveey`'s went from
   *"Speed+mana for hook positioning, fast attacks for harass, mobility to enable support skills
   across lanes"* to *"Fast support: mobility + mana for hook/heal/stun spam. Speed enables
   positioning for utility skills over raw damage."* A scripted rule or a cached constant cannot
   produce two different paraphrases of the same intent; a generative model can.
4. **The in-episode control.** Round 11 seats `derk-puffer-forge:v4` at positions 2, 3 and 5
   (`b697f833…`) and `derk-lane-brawler:v4` at position 4 (`36e7252a…`). Their records are
   *exactly* the table rows, at 0–1 ms: pid 2 burst → `arm_blaster/tail_stinger/misc_battery`
   (0 ms); pid 5 support → `arm_blaster/tail_plate/misc_battery` (1 ms); pid 7 burst →
   `arm_blaster/tail_stinger/misc_battery` (1 ms); and the lane-brawler at pid 6 →
   `arm_needler/tail_plate/misc_regen` with its signature `note: "brawl build"` (1 ms). So the same
   episode contains both fingerprints side by side, and the champions carry neither.

Server-side conjunct too: `fallback: false`, `fallback_cause: "none"` on both champion records and
`result.draft_fallbacks == [false, false, false, false, false, false]` — **fallback count is 0 of
6 decisions**, i.e. zero, not merely a small minority.

Supporting fetch — the released manifest and the policy manifest both carry the Bedrock switch that
was the fix:

```bash
$ jq -c '.manifest.player[]|select(.id=="drafter")|.env' cowdetail.json
{"USE_BEDROCK":"true","PLAYER_PROMPT":"derk-drafter-v1","ANTHROPIC_API_KEY_URI":"secret://coworld/derks-gym/anthropic_api_key"}
$ curl -sS "https://raw.githubusercontent.com/Metta-AI/cogame-derks-gym/main/tools/ci/policies.json" | jq -c '.[]|{name,env}'
{"name":"derk-drafter-v1","env":{"PLAYER_PROMPT":"derk-drafter-v1","ANTHROPIC_API_KEY_URI":"secret://coworld/derks-gym/anthropic_api_key","USE_BEDROCK":"true"}}
{"name":"derk-metagamer-v1","env":{"PLAYER_PROMPT":"derk-metagamer-v1","ANTHROPIC_API_KEY_URI":"secret://coworld/derks-gym/anthropic_api_key","USE_BEDROCK":"true"}}
{"name":"derk-puffer-forge","env":{"PLAYER_SCRIPTED":"puffer-forge"}}
{"name":"derk-lane-brawler","env":{"PLAYER_SCRIPTED":"lane-brawler"}}
```

`USE_BEDROCK: "true"` is present on **both** champion policies and absent from both fillers — which
is exactly the split the `decision_ms` numbers show.

### 4.8 The picks are physically real in the sim

Champion picks are non-neutral and their `applied` block differs from the neutral base
(`arm_none/tail_none/misc_none`, which the four house heroes carry):

- pid 0 Needler + Rotor Tail + Mana Battery → `base_damage 40.0`, `base_mana 400.0`,
  `basic_attack_cd 5`, `move_speed 1.15` (raised from 1.0).
- pid 1 Needler + Stinger Tail + Regen Chip → `hp_gain_per_level 160`,
  `damage_gain_per_level 18`, `basic_attack_cd 5` — the "scale into mid-late game" the note claims.

`loadout_digest: 2638707600` is present (round 10: `3866932697`) and differs between rounds, so the
digest tracks the actual drafted set rather than being a constant.

### 4.9 Events are non-empty and show the champion seats doing the thing the game is about

pid→seat→name mapping derived from the header, not assumed:

```
seat_hero_pids: [0, 1, 2, 5, 6, 7]  house_hero_pids: [3, 4, 8, 9]
pid -> name: {"0":"daveey","1":"daveey-1","2":"Baseline","3":"house","4":"house",
              "5":"Baseline (2)","6":"Baseline (3)","7":"Baseline (4)","8":"house","9":"house"}
```

```
=== EARLY (first 14) ===
tick	kind	pid	extra
0	draft	-	pids=[0, 1, 2, 5, 6, 7]
0	level_spike	pid=0 (daveey/Cog-Alpha)	level=1
0	level_spike	pid=1 (daveey-1/Cog-Bravo)	level=1
0	level_spike	pid=2 (Baseline/Cog-Charlie)	level=1
0	level_spike	pid=3 (house/House-Tank-R)	level=1
0	level_spike	pid=4 (house/House-Carry-R)	level=1
0	level_spike	pid=5 (Baseline (2)/Cog-Delta)	level=1
0	level_spike	pid=6 (Baseline (3)/Cog-Echo)	level=1
0	level_spike	pid=7 (Baseline (4)/Cog-Foxtrot)	level=1
0	level_spike	pid=8 (house/House-Tank-D)	level=1
0	level_spike	pid=9 (house/House-Carry-D)	level=1
63	level_spike	pid=6 (Baseline (3)/Cog-Echo)	level=2
82	level_spike	pid=4 (house/House-Carry-R)	level=2
108	level_spike	pid=2 (Baseline/Cog-Charlie)	level=2
=== MIDDLE (idx 25-35) ===
882	tower	pid=2 (Baseline/Cog-Charlie)	team=0
1165	kill	pid=6 (Baseline (3)/Cog-Echo)	victim_pid=4
1165	level_spike	pid=6 (Baseline (3)/Cog-Echo)	level=4
1184	kill	pid=2 (Baseline/Cog-Charlie)	victim_pid=8
1191	kill	pid=1 (daveey-1/Cog-Bravo)	victim_pid=6
1191	level_spike	pid=1 (daveey-1/Cog-Bravo)	level=4
1208	tower	pid=3 (house/House-Tank-R)	team=0
1304	level_spike	pid=6 (Baseline (3)/Cog-Echo)	level=5
1315	kill	pid=2 (Baseline/Cog-Charlie)	victim_pid=6
1315	level_spike	pid=2 (Baseline/Cog-Charlie)	level=5
=== LATE (last 12) ===
1982	level_spike	pid=1 (daveey-1/Cog-Bravo)	level=6
2116	level_spike	pid=3 (house/House-Tank-R)	level=6
2196	level_spike	pid=5 (Baseline (2)/Cog-Delta)	level=3
2206	kill	pid=2 (Baseline/Cog-Charlie)	victim_pid=8
2219	kill	pid=2 (Baseline/Cog-Charlie)	victim_pid=5
2219	level_spike	pid=2 (Baseline/Cog-Charlie)	level=6
2228	kill	pid=3 (house/House-Tank-R)	victim_pid=7
2314	level_spike	pid=7 (Baseline (4)/Cog-Foxtrot)	level=4
2395	tower	pid=3 (house/House-Tank-R)	team=0
2503	tower	pid=2 (Baseline/Cog-Charlie)	team=0
2503	ancient	-	team=1
2504	end	-	reason=ancient
```

Champion-seat tallies:

```
pid 0 = seat 0 = daveey/Cog-Alpha:   5 events; kills at []; towers at []; level_spikes 4
pid 1 = seat 1 = daveey-1/Cog-Bravo: 8 events; kills at [1191]; towers at [1723]; level_spikes 6
```

`agent_stats` (all 10 heroes, round 11) — every hero has nonzero `damage_dealt`, and the champions
farmed, levelled, killed and took a tower:

```
pid 0: {"level":4,"kills":0,"deaths":2,"towers_killed":0,"creeps_killed":11,"neutrals_killed":8,"xp":940,"damage_dealt":10029,"damage_received":2744,"healing_dealt":2129,"healing_received":520}
pid 1: {"level":6,"kills":1,"deaths":3,"towers_killed":1,"creeps_killed":28,"neutrals_killed":16,"xp":2432,"damage_dealt":22696,"damage_received":4981,"healing_dealt":0,"healing_received":1109}
pid 2: {"level":6,"kills":4,"deaths":5,"towers_killed":2,"creeps_killed":20,"neutrals_killed":3,"xp":1906,"damage_dealt":22005,"damage_received":6493,"healing_dealt":0,"healing_received":500}
pid 3: {"level":6,"kills":1,"deaths":4,"towers_killed":2,"creeps_killed":29,"neutrals_killed":14,"xp":2406,"damage_dealt":29554,"damage_received":15466,"healing_dealt":8070,"healing_received":8070}
pid 4: {"level":3,"kills":0,"deaths":10,"towers_killed":0,"creeps_killed":8,"neutrals_killed":3,"xp":585,"damage_dealt":11138,"damage_received":5858,"healing_dealt":0,"healing_received":0}
pid 5: {"level":3,"kills":0,"deaths":1,"towers_killed":0,"creeps_killed":4,"neutrals_killed":0,"xp":240,"damage_dealt":1867,"damage_received":2618,"healing_dealt":2191,"healing_received":1172}
pid 6: {"level":6,"kills":3,"deaths":2,"towers_killed":0,"creeps_killed":25,"neutrals_killed":0,"xp":2144,"damage_dealt":16334,"damage_received":7594,"healing_dealt":0,"healing_received":0}
pid 7: {"level":4,"kills":1,"deaths":1,"towers_killed":0,"creeps_killed":6,"neutrals_killed":0,"xp":646,"damage_dealt":3462,"damage_received":1121,"healing_dealt":0,"healing_received":457}
pid 8: {"level":1,"kills":0,"deaths":2,"towers_killed":0,"creeps_killed":0,"neutrals_killed":0,"xp":0,"damage_dealt":1608,"damage_received":3307,"healing_dealt":896,"healing_received":1207}
pid 9: {"level":3,"kills":2,"deaths":0,"towers_killed":0,"creeps_killed":2,"neutrals_killed":0,"xp":638,"damage_dealt":2154,"damage_received":245,"healing_dealt":0,"healing_received":251}
```

The per-tick micro layer, read out of the body bytes (60 bytes/tick, 6 per hero; NOOP = `[3,3,0,0,0,0]`):

```
pid0 daveey   micro: 2504 ticks, NOOP rows=1 (0.04%), distinct rows=527, ticks 0-4=[[0,4,2,1,1,0],[0,6,0,0,1,1],[2,6,2,1,1,1],[0,6,0,0,1,1],[1,6,0,0,0,1]]
pid1 daveey-1 micro: 2504 ticks, NOOP rows=0 (0.00%), distinct rows=471, ticks 0-4=[[0,4,1,0,1,1],[0,6,0,0,1,1],[0,6,1,1,1,1],[0,6,0,0,1,1],[0,6,0,0,0,1]]
```

### 4.10 Round 10's replay, parsed the same way (the corroborating second v4 episode)

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/68c73ee7-90f3-4c36-9319-4d9a1e1a651e.replay" \
     -o /tmp/v2/ep10.replay -w "HTTP %{http_code} size=%{size_download}\n"
HTTP 200 size=331542
$ sha256sum /tmp/v2/ep10.replay
c1f83c683747ba504745eb819de37724dc32456a0de4fa4c1c3d9341782c8e0b
```
```
magic: b'DERK' version: 2   header_len: 19713   strict UTF-8 JSON parse: ok
tick_count: 5197  body: 311820  ==tick*60: True
end_reason: ancient  winner: 0  final_tick: 5197  ancient_healths: [4500.0, 0.0]
names: ['daveey','daveey-1','Baseline','Baseline (2)','Baseline (3)','Baseline (4)']
scores: [1.0,1.0,1.0,0.0,0.0,0.0]   draft_fallbacks: [False×6]   noop_ticks: [0×6]   dead_seats: [False×6]
loadout_digest: 3866932697  final_state_digest: 2465922612  format_version: 2  catalog_version: v1
events: 115  draft records: 10
event kinds: {'draft':1,'level_spike':71,'first_blood':1,'kill':34,'tower':6,'ancient':1,'end':1}
pid0 daveey   micro: 5197 ticks, NOOP rows=2 (0.04%), distinct rows=697
pid1 daveey-1 micro: 5197 ticks, NOOP rows=1 (0.02%), distinct rows=605
```

Status: **TRUE.** The header parses under a strict UTF-8 JSON parser; the binary format matches the
repo's declared `MAGIC`/`FORMAT_VERSION`/`BYTES_PER_TICK` and the `result` object matches the
manifest's `results_schema` exactly (all 16 required keys, no extras, no gaps); `end_reason` is
`"ancient"` — the clean, non-degraded outcome, and the new `ancient` event is emitted before `end`;
there are 10 draft records with all six seat records present and `daveey`/`daveey-1` named; events
are non-empty (61 in round 11, 115 in round 10) and show kills, towers, level spikes and an Ancient
falling; `loadout_digest` is present; and the champions' decisions are **live LLM drafts** — 2390–
3577 ms, non-empty and varying notes, picks that differ from the scripted role table their fillers
reproduce exactly in the same episode, with **0 of 6** fallbacks.

---

## 5. Hosted game log is clean — TRUE

```bash
EREQ=ereq_55ad8e00-2570-4b1f-9a63-73243671b689     # round 11
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" \
     -o logs11.raw -w "HTTP %{http_code} size=%{size_download}\n"
HTTP 200 size=2059
# the body is python b'…' byte-string reprs under container headers — decoded per
# playbooks/observatory-api.md §10 (ast.literal_eval each repr) BEFORE grepping
python3 declog.py logs11.raw logs11.txt        # 2059 raw -> decoded
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs11.txt || echo CLEAN
```
```
CLEAN
```

```bash
grep -nE 'draft_fallback|provider=' logs11.txt || echo "NOT PRESENT"
NOT PRESENT
```

**The decoded artifact in full** (round 11, four containers):

```
containers: ['coworld-init-config', 'bedrock-sidecar', 'game', 'worker']

===== container: coworld-init-config =====
(empty)

===== container: bedrock-sidecar =====
2026-08-28 15:21:08,214 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1","has_role_arn":true,"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar","episode_request_id":"55ad8e00-2570-4b1f-9a63-73243671b689","job_request_id":"4af31312-183f-4975-83c4-0f6359719fae","role":"game","slot":"game","image_digest":"sha256:28b670a2854a265bd769e6ca70d7c12c659959e7379841605df9d68a72103db8"}
[2026-08-28 15:21:08 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-08-28 15:21:08,419 INFO hypercorn.error Running on http://127.0.0.1:9100 (CTRL + C to quit)

===== container: game =====
cogame-derks-gym serving on 0.0.0.0:8080 (6 seats, one hero each; house heroes (3, 4, 8, 9); draft_enabled=True)
seat 3 (Baseline (2)) connected at tick 0
seat 0 (daveey) connected at tick 0
seat 5 (Baseline (4)) connected at tick 0
seat 4 (Baseline (3)) connected at tick 0
seat 1 (daveey-1) connected at tick 0
seat 2 (Baseline) connected at tick 0
draft Cog-Alpha (support): arm_needler / tail_rotor / misc_battery [none, 2903ms]
draft Cog-Bravo (assassin): arm_needler / tail_stinger / misc_regen [none, 2390ms]
draft Cog-Charlie (burst): arm_blaster / tail_stinger / misc_battery [none, 0ms]
draft Cog-Delta (support): arm_blaster / tail_plate / misc_battery [none, 1ms]
draft Cog-Echo (assassin): arm_needler / tail_plate / misc_regen [none, 1ms]
draft Cog-Foxtrot (burst): arm_blaster / tail_stinger / misc_battery [none, 1ms]
house heroes (3, 4, 8, 9) driven by the vendored pretrained network (neutral loadout)
seat 0 (daveey) disconnected at tick 2503
seat 1 (daveey-1) disconnected at tick 2503
seat 2 (Baseline) disconnected at tick 2503
seat 3 (Baseline (2)) disconnected at tick 2503
seat 4 (Baseline (3)) disconnected at tick 2503
seat 5 (Baseline (4)) disconnected at tick 2503
episode over: winner=0 end_reason=ancient tick=2504

===== container: worker =====
(empty)
```

**Round 10's log, fetched the same way** — also CLEAN:

```bash
curl -sS "$BASE/episode-requests/ereq_01c056aa-cde9-4ca9-a116-e5509c1fff36/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" \
     -o logs10.raw -w "HTTP %{http_code} size=%{size_download}\n"
HTTP 200 size=2051
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs10.txt || echo CLEAN
CLEAN
```
its game container's draft lines:
```
draft Cog-Alpha (support): arm_needler / tail_rotor / misc_battery [none, 3577ms]
draft Cog-Bravo (assassin): arm_needler / tail_stinger / misc_regen [none, 3278ms]
draft Cog-Charlie (burst): arm_needler / tail_rotor / misc_regen [none, 1ms]
draft Cog-Delta (support): arm_blaster / tail_plate / misc_battery [none, 1ms]
draft Cog-Echo (assassin): arm_needler / tail_rotor / misc_focus [none, 1ms]
draft Cog-Foxtrot (burst): arm_needler / tail_rotor / misc_regen [none, 1ms]
episode over: winner=0 end_reason=ancient tick=5197
```

**No Bedrock capacity symptom.** `LLM provider is unavailable` does not appear in either round's
log, so the prompt's wait rule was not engaged and no cross-check against another LLM coworld was
needed. The `bedrock-sidecar` container started cleanly in both (`bedrock_sidecar_started`,
`has_role_arn: true`, hypercorn listening on 9100) with no error line after it.

**Player containers are absent from this artifact — restated as a fact, and not counted against
this item.** The route returns only the *game* pod's containers. Three fresh probes this attempt,
against round 11's ereq:

| request | result |
|---|---|
| `GET /episode-requests/$EREQ/artifacts/logs` | HTTP 200, 2059 bytes, containers `coworld-init-config, bedrock-sidecar, game, worker` — **no player container** |
| `GET /episode-requests/$EREQ/artifacts` | `HTTP 404 {"detail":"Not Found"}` |
| `GET /episode-requests/$EREQ/artifacts/player-logs` | `HTTP 400 {"detail":"Unknown artifact type: player-logs"}` |
| `GET …/artifacts/logs?container=player` | HTTP 200, **2059 bytes — byte-identical body**, filter silently ignored |
| `GET …/artifacts/logs?role=player` | HTTP 200, **2059 bytes — byte-identical body**, filter silently ignored |

So `draft_fallback=scripted` and `provider=bedrock model=… endpoint=…` are **NOT FETCHABLE** through
any Observatory route I could find — the player pods' stdout is not exposed. Per the brief, this
item is **not** marked false for the absence of player logs; the champion-LLM question is answered
by item 4's draft records instead, which are the game pod's own recording of what each player
actually submitted, and which the game container's own `[none, 2903ms]` / `[none, 2390ms]` lines
above independently corroborate (`none` = `fallback_cause`).

Status: **TRUE** — the prompt's four patterns are **CLEAN** in both counted v4 rounds' decoded logs,
there is no capacity symptom to wait out, and the log records a complete episode
(`episode over: winner=0 end_reason=ancient tick=2504`) with all six seats connecting at tick 0 and
disconnecting at the final tick.

---

## 6. The public page uses the static replay path — TRUE

**Source used: the page's own SSR payload for the featured match, plus the replay-session endpoint
for the iframe `src`** — after the raw-HTML iframe grep found nothing and `/coworlds`'
`featured_match` came back `null`, both of which `playbooks/observatory-api.md` §Featured match
records as expected platform behaviour rather than evidence.

```bash
curl -sS "https://softmax.com/derks-gym" -o page2.html -w "HTTP %{http_code} size=%{size_download}\n"
HTTP 200 size=738678
grep -o '<iframe[^>]*src="[^"]*"' page2.html || echo "(no output — no iframe in raw HTML)"
(no output — no iframe in raw HTML)          # client-rendered; NOT a false negative
grep -c 'client/replay' page2.html
0                                            # no /client/replay anywhere in the page bytes
```

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)[]|select(.name=="derks-gym")
          |{id,name,version,canonical,replay_viewer,featured_match}'
{"id":"cow_03c45b25-de4b-42e1-8e2f-056a496878c4","name":"derks-gym","version":"0.1.3","canonical":true,"replay_viewer":null,"featured_match":null}
{"id":"cow_97b642d7-832c-4881-a48f-2b3db0c4339c","name":"derks-gym","version":"0.1.2","canonical":false,"replay_viewer":null,"featured_match":null}
{"id":"cow_c94652ab-4983-425d-a0c0-7db40e81a627","name":"derks-gym","version":"0.1.1","canonical":false,"replay_viewer":null,"featured_match":null}
{"id":"cow_81624b16-c509-470a-8fc2-69da83d64a3e","name":"derks-gym","version":"0.1.0","canonical":false,"replay_viewer":null,"featured_match":null}
```

`canonical: true` is on **0.1.3 / `cow_03c45b25-…`**; the three earlier versions are
`canonical: false`. `featured_match: null` platform-wide per the playbook.

**The featured match, from the page's SSR payload at `state.playlist[0]`** (fetched 15:23:47Z; the
payload was `\"`-escaped this time, so it is unescaped here — the array verbatim):

```json
[{"episodeId":"e161ebcf-cb4b-444b-8a09-faaa5e0faa5c",
  "coworldId":"cow_03c45b25-de4b-42e1-8e2f-056a496878c4","coworldName":"derks-gym",
  "coworldVersion":"0.1.3",
  "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/4af31312-183f-4975-83c4-0f6359719fae.replay",
  "finishedAt":"2026-08-28T15:21:52.325101Z","roundNumber":11,"episodeNumber":1,
  "code":"derks-gym.r11.e1",
  "matchup":{"divisionId":"div_1bc6a659-31e8-40fe-a99b-726c82426998","divisionName":"Competition",
   "first":{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1000,"score_label":"MMR","score_value_type":"integer","rounds_played":10,"episode_wins":0,"episodes_played":null,"win_rate":0,"policy_label":"derk-drafter-v1:v4","recent_rounds":null},
   "second":{"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":1000,"score_label":"MMR","score_value_type":"integer","rounds_played":10,"episode_wins":0,"episodes_played":null,"win_rate":0,"policy_label":"derk-metagamer-v1:v4","recent_rounds":null}},
  "inspectUrl":"/observatory/v2?tab=overview&detail=episode-request:ereq_55ad8e00-2570-4b1f-9a63-73243671b689",
  "outcome":null}]
```

A featured match **is present**, it is `coworldVersion: "0.1.3"` on `cow_03c45b25-…`, it is
**round 11's** episode — the same replay as items 3 and 4 — and its `matchup` names both champions
at their **v4** labels. (At 15:23:08Z the same field held round 10's `68c73ee7-…`; it rolled forward
when round 11 landed, which is why item 8 was dispatched against the round-11 `src`.)

**The iframe `src` the page's JS builds:**

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
 -d '{"coworld_id":"cow_03c45b25-de4b-42e1-8e2f-056a496878c4",
      "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/4af31312-183f-4975-83c4-0f6359719fae.replay"}'
```
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_03c45b25-de4b-42e1-8e2f-056a496878c4/sha256%3Ab5e7d1927bb411fe56fa82c9a708bb6332169b69c9ccef080d0c60ef3b629fef/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F4af31312-183f-4975-83c4-0f6359719fae.replay","ready":true}
```
```bash
grep -c 'client/replay' <<< "$(jq -r .viewer_url session11.json)"
0
```

And the shell at that path serves:

```bash
curl -sS "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/$COW/sha256%3Ab5e7d1927bb411fe56fa82c9a708bb6332169b69c9ccef080d0c60ef3b629fef/index.html" \
     "${AUTH[@]}" -o shell.html -w "HTTP %{http_code} size=%{size_download}\n"
HTTP 200 size=12238
```

Status: **TRUE** — `ready: true`; the path is
`/v2/coworlds/replays/static/<cow_id>/<sha>/index.html`, with `<cow_id>` = the **new**
`cow_03c45b25-de4b-42e1-8e2f-056a496878c4` and `<sha>` = the **new** URL-encoded manifest_sha
`sha256:b5e7d1927bb411fe56fa82c9a708bb6332169b69c9ccef080d0c60ef3b629fef` (matching STATE and
`release-result.json`); the replay rides as the `#replay=` fragment, the 2026-08-28 form the
playbook documents as the static route. The shell at that URL returns HTTP 200. **No
`/client/replay` pod URL anywhere** — zero occurrences in the page bytes and zero in the
`viewer_url`. A featured match is present.

---

## 7. Certification declared the static bundle — TRUE

Source: **the committed `runs/2026-08-28-derks-gym/release-result.json`** — the copy phase 40
downloaded from release run `33182295860` and committed. No re-download was needed, and `/tmp` was
not consulted.

```bash
$ ls -l runs/2026-08-28-derks-gym/release-result.json
-rw-r--r-- 1 root root 3916 Aug 28 15:03 runs/2026-08-28-derks-gym/release-result.json
$ jq -r '.certify.replay_liveness' runs/2026-08-28-derks-gym/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Contains the required string **`Replay liveness: skipped (static replay bundle declared`**.

That the file is *this* release, not attempt 1's:

```bash
$ jq -c '{ok:.certify.ok, version, canonical, secret_put, cow_id, manifest_sha}' runs/2026-08-28-derks-gym/release-result.json
{"ok":true,"version":"0.1.3","canonical":true,"secret_put":true,
 "cow_id":"cow_03c45b25-de4b-42e1-8e2f-056a496878c4",
 "manifest_sha":"sha256:b5e7d1927bb411fe56fa82c9a708bb6332169b69c9ccef080d0c60ef3b629fef"}
```

`version 0.1.3`, `cow_id` and `manifest_sha` identical to the ids item 6's static route uses.
Transcript tail from the same file — all 10 certification steps `[pass]`:

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
Inspect replay: open …/replay in your static replay viewer bundle (see STATIC_REPLAY_VIEWERS.md)
```

Status: **TRUE.**

---

## 8. Spectator judgment — the viewer was EXECUTED — TRUE

### (a) Dispatch

Dispatched at **2026-08-28T15:24:13Z** against the item-6 `src` verbatim (fragment and all):

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_03c45b25-de4b-42e1-8e2f-056a496878c4/sha256%3Ab5e7d1927bb411fe56fa82c9a708bb6332169b69c9ccef080d0c60ef3b629fef/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F4af31312-183f-4975-83c4-0f6359719fae.replay'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
```

Found by sorting on `createdAt`, **not** by taking the latest blind:

```bash
sleep 12
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml \
   --json databaseId,createdAt,status,conclusion -L 10 | jq -c 'sort_by(.createdAt)|reverse|.[0:4]'
[{"conclusion":"","createdAt":"2026-08-28T15:24:14Z","databaseId":33184965298,"status":"in_progress"},
 {"conclusion":"success","createdAt":"2026-08-28T13:40:19Z","databaseId":33176460797,"status":"completed"},
 {"conclusion":"success","createdAt":"2026-08-28T13:25:59Z","databaseId":33175355596,"status":"completed"},
 {"conclusion":"success","createdAt":"2026-08-28T09:25:16Z","databaseId":33159290682,"status":"completed"}]
```

Run **33184965298**, created 15:24:14Z — **1 s after my dispatch**. The two 13:2x/13:4x runs are
attempt 1's and are not this file's evidence.

```bash
gh run watch 33184965298 -R Metta-AI/coworld-builder --exit-status
# → exit 0 (green)
gh run view 33184965298 -R Metta-AI/coworld-builder --json conclusion,status,createdAt,updatedAt
{"conclusion":"success","createdAt":"2026-08-28T15:24:14Z","status":"completed","updatedAt":"2026-08-28T15:25:13Z"}

rm -rf runs/2026-08-28-derks-gym/viewer-check && mkdir -p runs/2026-08-28-derks-gym/viewer-check
gh run download 33184965298 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-28-derks-gym/viewer-check
$ ls -l runs/2026-08-28-derks-gym/viewer-check
-rw-r--r-- 1 root root     0 Aug 28 15:25 smoke-stderr.txt
-rw-r--r-- 1 root root   480 Aug 28 15:25 smoke-stdout.txt
-rw-r--r-- 1 root root  3727 Aug 28 15:25 viewer-smoke.json
-rw-r--r-- 1 root root 91442 Aug 28 15:25 viewer-smoke.png
```

Committed with this file, overwriting attempt 1's artifact.

The instrument that ran is `templates/tools/ci/viewer_smoke.mjs` at `origin/main` commit
**`33208c1`**, which added this lineage's selectors — the fix for attempt 1's blind spot:

```bash
$ git log --oneline -1 origin/main -- templates/tools/ci/viewer_smoke.mjs
33208c1 60 derks-gym: attempt-1 verdict 5/8; viewer_smoke lineage selector fallbacks; fix plan
$ grep -nE "id\\\$=|SCRUB_SELECTOR" templates/tools/ci/viewer_smoke.mjs
430:  const feed = document.querySelector('#feed, .feed, #log, [id$="-feed"]');
432:    clock: text('#clock, [id$="-clock"]'),
434:    scorebug: text('#scorebug, [id$="-scorebug"]'),
440:    has_scrub: !!document.querySelector('#scrub, #seek, input[type="range"]'),
446:const SCRUB_SELECTOR = '#scrub, #seek, input[type="range"]';
```

### (b) The readouts, verbatim

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-28-derks-gym/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":2041,"clock":"tick 0 / 2504 · 0:00","scorebug":"RADIANT 4500 0 towers 0 kills DIRE 4500 0 towers 0 kills","feed_lines":6}
```

```bash
jq -c '.signals' runs/2026-08-28-derks-gym/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/2026-08-28-derks-gym/viewer-check/viewer-smoke.json
no failure
```

```bash
jq -c '{status,loading_text,soak,canvas_text}' runs/2026-08-28-derks-gym/viewer-check/viewer-smoke.json
{"status":"","loading_text":null,"soak":null,
 "canvas_text":{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}}
```

```bash
cat runs/2026-08-28-derks-gym/viewer-check/smoke-stdout.txt
{"loaded":true,"ms":2041,"clock":"tick 0 / 2504 · 0:00","scorebug":"RADIANT 4500 0 towers 0 kills DIRE 4500 0 towers 0 kills","feed_lines":6}
scrub readouts: 0%="tick 0 / 2504 · 0:00"  50%="tick 6 / 2504 · 0:01"  100%="tick 11 / 2504 · 0:02"
canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
artifacts: /home/runner/work/coworld-builder/coworld-builder/viewer-smoke.png /home/runner/work/coworld-builder/coworld-builder/viewer-smoke.json
# smoke-stderr.txt is 0 bytes
```

**The three clock readouts (0 % / 50 % / 100 %):**

```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-28-derks-gym/viewer-check/viewer-smoke.json
```

| at | clock |
|---|---|
| 0 % | `tick 0 / 2504 · 0:00` |
| 50 % | `tick 6 / 2504 · 0:01` |
| 100 % | `tick 11 / 2504 · 0:02` |

Raw:
```bash
jq -c '.scrub' runs/2026-08-28-derks-gym/viewer-check/viewer-smoke.json
[{"at":"0%","clock":"tick 0 / 2504 · 0:00"},{"at":"50%","clock":"tick 6 / 2504 · 0:01"},{"at":"100%","clock":"tick 11 / 2504 · 0:02"}]
```

**Both conditions hold.** (1) `loaded: true` — via `data_replay_loaded: "true"`, in 2041 ms, with
`data_replay_error: null` and `failure: null`. (2) The **three clock readouts differ**: tick 0 →
tick 6 → tick 11, and the tick counter's denominator `2504` is exactly the round-11 replay's
`tick_count`, so the viewer parsed the same header this file parsed. The clock advances; this is not
a single frozen frame. `clock`, `scorebug` and `feed_lines: 6` are all non-null this attempt (they
were `null/null/0` in attempt 1) because the instrument now probes `[id$="-clock"]` /
`[id$="-scorebug"]` / `[id$="-feed"]` and `#seek`.

**One honest caveat, recorded rather than glossed:** the readouts advance by ~5 ticks between
samples, not to ticks ~1252 and ~2504. So what the three readouts prove is that the **playhead is
running** between samples; they do not prove that dragging `#seek` *seeks*. Setting the range input's
value did not move the playhead to that fraction of the episode. That is a legibility finding for
the coordinator (below), not a failure of this check as `prompts/60-verify.md` defines it — the
condition is that the three readouts differ, and they do, which is exactly the "renders one frame
and never advances" failure mode being ruled out.

### (c) The replay JSON the viewer was asked to draw

Ordered excerpts and `result` are pasted under item 4 §4.9 / §4.3 (same file, `/tmp/v2/ep11.replay`,
sha256 `46f6932b…`). The three anchors used for reconciliation below: `tick_count: 2504`;
`events[0..10]` are the `draft` at tick 0 followed by ten `level_spike … level=1`; the first `kill`
is at tick 1191 and the first `tower` at 882 — both far beyond the drawn frame.

### (d) Spectator judgment

Evidence: `runs/2026-08-28-derks-gym/viewer-check/viewer-smoke.png` (1280×800, 91442 bytes, taken by
CI after the scrub sequence), reconciled against the round-11 replay header above. Two crops of the
same png were enlarged to read the small type; nothing below is inferred from anything but those
pixels and the fetched replay bytes.

**The picture is not empty and not a "Loading replay…" shell.** It is legible and it plainly shows
this game.

*Top band (dimmed under the overlay, confirmed by an enlarged crop of rows 0–100):* the
`#derk-scorebug` reading **`RADIANT  4500  ▬▬▬▬  …  0 towers 0 kills`** with the dire mirror, the
`#derk-clock` reading **`tick 13 / 2504 · 0:02`**, and the page header **`cogame-derks-gym replay
viewer`**.

*Middle:* `#derk-draft`, the draft-reveal screen, captioned **`Draft reveal (closes in 4s)`** in two
columns `Radiant` / `Dire`. The Radiant card reads **`Cog-Alpha  daveey  support`** /
**`Needler · Rotor Tail · Mana Battery`** / `base_damage −10  base_health −100  base_mana +150
basic_attack_cd −3  mana_gain_per_level +30  move_speed +0.15` / `hp 400 · mana 400 · dmg 40 · cd 5 ·
spd 1.149999976158142 · /lvl 100/80/10`, with three item glyph badges. Opposite it,
**`Cog-Delta  Baseline (2)  support`** / `Blaster · Iron Plate · Mana Battery` / `base_damage +15
base_health +200  base_mana +150  basic_attack_cd +2  mana_gain_per_level +30` / `hp 700 · mana 400 ·
dmg 65 · cd 10 · spd 1 · /lvl 100/80/10`. **`Cog-Echo  Baseline (3)  assassin`** is beginning below,
clipped by the fold, and beneath the Radiant card an orange italic line reads
**`Fast support: mobility + mana for hook/heal/stun spam`**.

That orange line is the single strongest reconciliation in this file: it is **verbatim the opening of
`draft[0].note`** in the replay header I parsed in item 4.6 — the LLM's own words about its own pick,
carried from a Bedrock call through the game pod's draft record into the replay bytes and onto the
screen a spectator sees. Likewise the card's numbers are exactly `draft[0].applied` (`hp 400`,
`mana 400`, `dmg 40`, `cd 5`, `spd 1.149999976158142`, `/lvl 100/80/10`) and the item names are
exactly `draft[0].picks` (`arm_needler` → Needler, `tail_rotor` → Rotor Tail, `misc_battery` → Mana
Battery). The two-name-space rule — alias plus the real player name beside it — is rendered as
designed on every card.

*Behind the overlay:* the raylib/WebGL canvas drawing the upstream Dota-shaped map through its
narrow camera — heroes as distinct sprites with cyan/green health-and-mana bars and red `Level: 1`
labels above each, magenta tower-vision outlines and the lane geometry along the right, neutral
camp star markers, the dire base's red territory tint, the starter's in-canvas HUD
(`Experience: 0`, `Mana: 300/300`, `Health: 350/350`, `Q: □  W: □  E: □` cooldown boxes, `Stun: 0
Move: 0`) and the raylib FPS counter reading **`19 FPS`** in the canvas's top-left. Under the canvas
the `#derk-roster`/`#derk-beats` delta strip is drawn as green badges — an enlarged crop reads
`+1 +5 +3`, `+2 +2`, `+2`, `+6 +7`, `+2 +2 +2`, one pair I could not resolve cleanly, `lv +5`,
`tower +3`.

*Reconciliation.* The frame is `tick 13 / 2504`, and 2504 is exactly the replay's `tick_count`.
`Level: 1` on every hero and `0 towers 0 kills` on both sides match the events at tick 0 (the
`draft`, then ten `level_spike … level=1`); the record's first tower is at tick 882 and first kill at
1191, both far ahead of the drawn frame, so an empty scorebug at tick 13 is *correct*, not broken.
The `Draft reveal (closes in 4s)` countdown is the design's 6 s auto-overlay two seconds in, which
agrees with the clock's `0:02`. And the frame at tick 13 sits **after** the 100 % scrub readout at
tick 11, so the screenshot is downstream of the motion the readouts recorded: picture and record
agree, and the picture is later than the last readout.

*Is it frozen, empty or unreadable?* None of the three. Not empty (a full draft overlay, a populated
canvas, scorebug, clock, roster strip). Not frozen (three differing clocks, plus a live in-canvas
FPS counter and `failure: null`). Not unreadable — and `canvas_text` reports `0 never inside the
canvas` and `0 ellipsized`, so no caption was drawn with nowhere to go. The one legibility cost in
this particular frame is that the draft overlay dims the scorebug and clock behind it and clips the
third and fourth cards at the fold; that is the design's intended first-6-seconds state, not a
defect, but it does mean a spectator's very first impression is the draft, not the match.

*Chrome provenance — the starter's page, not a rewrite.* Every id in the cogame-moba starter's
viewer survives in the served shell:

```bash
comm -23 <(grep -oE 'id="[a-z0-9-]+"' /workspace/starters/cogame-moba/viewer/index.html | sort -u) \
         <(grep -oE 'id="[a-z0-9-]+"' shell.html | sort -u)
# (no output — zero starter ids missing)
# starter ids: 13   served-shell ids: 37
$ grep -oE 'id="[a-z0-9-]+"' shell.html | sort -u | tr '\n' ' '
id="canvas" id="controls" id="derk" id="derk-bar-dire" id="derk-bar-radiant" id="derk-beats"
id="derk-cameras" id="derk-clock" id="derk-draft" id="derk-draft-close" id="derk-draft-cols"
id="derk-draft-count" id="derk-draft-inner" id="derk-endcard" id="derk-endcard-inner"
id="derk-feed" id="derk-hp-dire" id="derk-hp-radiant" id="derk-kills-dire" id="derk-kills-radiant"
id="derk-minimap" id="derk-roster" id="derk-scorebug" id="derk-towers-dire" id="derk-towers-radiant"
id="derk-viewpanel" id="dire-names" id="endcard" id="playpause" id="radiant-names" id="seek"
id="speed" id="stage" id="status" id="teams" id="tickinfo" id="warn"
```

All 13 starter ids present (`#stage`, `#canvas`, `#status`, `#controls`/`#playpause`/`#speed`/
`#seek`/`#tickinfo`, `#endcard`, `#warn`, `#teams`, `#radiant-names`, `#dire-names`); the 24
additions are all `derk-`-prefixed. The screenshot agrees — the same transport strip, the same
canvas + status overlay, the same two-team name panel, with the `#derk` scorebug / roster / feed /
draft-reveal block appended. This is cogame-moba's viewer with a game block added, **not** the
cogame-gridlock failure of a rewrite sharing only the ids.

**Item 8 verdict: TRUE** — `loaded: true` **and** three differing clock readouts, both pasted above
from an artifact I dispatched and downloaded this attempt.

---

## Observations for the coordinator (not checklist items, nothing blocking)

1. **`#seek` reports position but does not seek.** Item 8(b): setting the range input's value
   produced clocks at ticks 0 / 6 / 11 instead of 0 / ~1252 / ~2504. Motion is proven, so check 8
   passes, but a spectator who drags the scrubber will probably not jump. Worth a phase-30 look at
   whether `#seek`'s `input`/`change` handler is wired to the playhead.
2. **30 WebGL warnings in `console_tail`**, repeating
   `WebGL: INVALID_VALUE: vertexAttribPointer: index out of range` /
   `enableVertexAttribArray: index out of range`, ending with
   `too many errors, no more errors will be reported to the console for this context`. The viewer
   still renders (19 FPS in-canvas, correct frame content), and `failure` is null, so this is not a
   check failure — but a vertex-attribute index mismatch in the emscripten/raylib build is a real
   defect that could bite on other GPUs/drivers.
3. **`first_blood` loses the killer.** In both v4 replays the event has `pid == victim_pid`
   (round 11 `{"tick":246,"kind":"first_blood","pid":0,"victim_pid":0}`; round 10
   `{"tick":111,…,"pid":4,"victim_pid":4}`), and it is the only event at that tick. Also, hero
   deaths not attributed to a hero kill are not emitted as `kill` events at all — `agent_stats`
   gives pid 0 `deaths: 2` and pid 1 `deaths: 3` in round 11 while no `kill` event names either as
   victim. The feed will therefore misattribute first blood and undercount deaths.
4. **Player-pod logs remain unobservable** (item 5). `artifacts/logs` returns the game pod only, and
   `?container=`/`?role=` are silently ignored (byte-identical bodies). The documented
   `draft_fallback=scripted reason=…` and `provider=bedrock model=… endpoint=…` contracts are
   unverifiable through the Observatory API. The game container's `[<fallback_cause>, <ms>]` draft
   lines are a good substitute and did carry the load this attempt — consider making that the
   documented contract instead of the player stdout.
5. **`/rounds` shape moves.** `{entries,limit,offset,total_count}` at 15:07Z and 15:26Z this attempt;
   phase 50 logged a bare array. `/coworlds` and `/divisions/$D/leaderboard` are bare arrays. The
   dual-shape jq is mandatory.
6. **Four `derks-gym` coworld rows now exist** (0.1.0–0.1.3) with `canonical: true` only on 0.1.3.
   Nothing to fix; noted so a later phase filtering on `name` alone does not pick up a stale row.
