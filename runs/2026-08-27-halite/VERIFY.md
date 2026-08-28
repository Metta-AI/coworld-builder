# VERIFY — halite   (2026-08-28T09:28Z)

Verdict: **all-true (8/8)**

> **This file supersedes the attempt-1 verification pass of 2026-08-28T08:33Z**, whose **check 4 was
> FALSE**: against coworld **0.1.0** (`cow_97d89fb8-8a54-423b-ac60-7080b318271a`) and champion
> policies at **v1**, both LLM seats produced `results.llm_turns == [0,0,0,0]` and 40/40 `note`
> events with `source: "scripted"` carrying `PermissionDeniedError: Error code: 403 … 'Invalid API
> Key format'` — the player pod built `AnthropicBedrock()` with no `base_url` instead of POSTing the
> episode's local sidecar. The transport was fixed in `Metta-AI/cogame-halite@fdd5272` (sidecar
> transport), the coworld re-released as **0.1.1**, and both champions and both fillers resubmitted
> at **v2**. Every fetch below is fresh, made in this pass, against 0.1.1 / v2.

| # | item | verdict |
|---|---|---|
| 1 | ≥2 completed rounds after the fillers were set | **TRUE** |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** |
| 3 | Latest round's episode request completed with a replay | **TRUE** |
| 4 | Replay bytes valid **and show the game** | **TRUE** |
| 5 | Hosted game log clean | **TRUE** |
| 6 | Public page uses the static replay path, featured match present | **TRUE** |
| 7 | Certification declared the static bundle | **TRUE** |
| 8 | Spectator judgment — viewer executed, `loaded:true`, clock advances | **TRUE** |

- Run `2026-08-27-halite` · slug `halite` · repo `Metta-AI/cogame-halite` · version **`0.1.1`**
- `COW` = `cow_c6743b6c-2028-4bef-8361-f7aa7d8296a2` · manifest
  `sha256:cd52ca31d9c6c00bef566e9f20c7903abaca055a14e2bec77d48b602f7e6a665`
- `L` = `league_82571537-04b2-4611-8200-59349283a022` · `D` = `div_165193cb-f037-4f20-ac3d-25a3a4a7d440`
- `BASE` = `https://softmax.com/api/observatory/v2`
- Champions at v2: `halite-tidereader:v2` = `fae0a703-0950-4c35-aa07-94631b5054fb` (daveey,
  `ply_44ae9048-3242-4654-881f-6d9d43347fa3`); `halite-privateer:v2` =
  `7b716123-a7ac-4dfc-b3dd-7035b3fded7c` (daveey-1, `ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`).
  Fillers at v2: `halite-tidewalker:v2` = `79e81e5a-3c68-4072-ad7c-02251b25cb56`,
  `halite-corsair:v2` = `9ed30562-956a-41d1-a1bb-580b60886ab8`.
- Headers on every Observatory call: `Authorization: Bearer <redacted>`, `User-Agent:
  coworld-builder/1.0`; `X-Use-Elevated-Privileges: true` added on `artifacts/logs` and on the
  filler-policies read. **No header value is reproduced anywhere in this file.**
- **Scoping rule applied throughout: only rounds ≥ 5 count.** Rounds 1–4 ran the broken 0.1.0 / v1
  policies. Proof, fetched this pass, not assumed — round 4's episode request still names the *old*
  coworld and the *old* version ids:
  ```
  GET /rounds/round_d3665107-eb52-4e77-9c77-bef600a0d109/episode-requests   → HTTP 200
  {"entries":[{"id":"ereq_0223cacb-605c-406f-8bfd-417885a3b13a","status":"completed",
    "coworld_id":"cow_97d89fb8-8a54-423b-ac60-7080b318271a",     ← 0.1.0, not 0.1.1
    "policy_version_ids":["734ab104-8ac4-4936-a7ad-de17d34a8b0b","ce5ab226-abe2-4a74-9b68-542c823d3c6c",
                          "dc3af747-7ccb-4cdd-9c25-2e14d93b1467","dc3af747-7ccb-4cdd-9c25-2e14d93b1467"],
    "created_at":"2026-08-28T08:51:03.062679Z"}]}
  ```
  None of those four UUIDs is a v2 UUID. Round 4 was created 08:51:02Z, before the v2 fillers were
  registered (~08:59Z) and before the v2 champions were submitted (09:00Z, `log.md` 09:01:34Z).
- Evidence-source choices: **check 6** used the **SSR-payload playlist + the replay-session route**
  (the raw-HTML iframe grep and `/coworlds`' `featured_match` both came back empty — both pasted
  below); **check 7** used the **committed `runs/2026-08-27-halite/release-result.json`** (the 0.1.1
  artifact, no re-download needed).
- Wall clock: this pass opened **09:02:23Z**, last round poll **09:23:55Z** — **~22 min of the
  75-min bound used.**
- Replay under test (latest completed in-scope round = **round 6**):
  `https://softmax-public.s3.amazonaws.com/replays/da1179c8-90e2-4c7c-833b-bc0e88145f16.replay`
- Rendered evidence: `runs/2026-08-27-halite/viewer-check/` from **viewer-check run `33159290682`**
  (dispatched by this verifier at 09:25:16Z; identity confirmed from the run log's own `url:` line).
- API quirks confirmed live this pass: `/rounds?league_id=` and `/divisions/$D/leaderboard` return
  **bare JSON arrays** (handled with `if type=="array" then . else .entries end`); the flat
  `GET /episode-requests?round_id=` returns **HTTP 405** and the nested
  `GET /rounds/$R/episode-requests` is the working route.

---

## 1. ≥2 completed rounds after the fillers were set — TRUE

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=30" "${AUTH[@]}" -o c1.json -w 'HTTP %{http_code}\n'
jq 'if type=="array" then . else .entries end
    | map({id,round_number,status,error,created_at,completed_at}) | sort_by(.round_number) | reverse' c1.json
```
```
HTTP 200          (fetched 2026-08-28T09:23:55Z)
[
  {
    "id": "round_d608a35e-28b2-4282-862b-33f49d3db7f2",
    "round_number": 6,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T09:15:52.104217Z",
    "completed_at": "2026-08-28T09:19:56.727520Z"
  },
  {
    "id": "round_35e9cbf2-c630-44c0-b088-9e9f5990d2f7",
    "round_number": 5,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T09:00:47.981473Z",
    "completed_at": "2026-08-28T09:04:52.220454Z"
  },
  {
    "id": "round_d3665107-eb52-4e77-9c77-bef600a0d109",
    "round_number": 4,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T08:51:02.764269Z",
    "completed_at": "2026-08-28T08:55:27.327922Z"
  },
  {
    "id": "round_5eda01d4-2b03-4ef4-af7f-52fae3279a91",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T08:36:02.344500Z",
    "completed_at": "2026-08-28T08:40:06.828902Z"
  },
  {
    "id": "round_2a2453f5-1c47-4277-ad08-ad498be65dbc",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T08:21:01.950027Z",
    "completed_at": "2026-08-28T08:25:04.327230Z"
  },
  {
    "id": "round_24dc0f54-2b9c-4d75-90e7-baef10e7c454",
    "round_number": 1,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-28T08:06:00.440407Z",
    "completed_at": "2026-08-28T08:10:38.738998Z"
  }
]
```

Six rounds are `completed`; **no round is `failed` or `discarded`**, so there is no `error` string to
quote. **In scope (round_number ≥ 5, i.e. after the v2 fillers were registered): rounds 5 and 6 — two.**

**The fillers in force for both counted rounds are the v2 fillers**, read live rather than taken from
`log.md` (this read needs the elevated header even though it is a read):

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}" -w 'HTTP %{http_code}\n'
```
```
HTTP 200          (fetched 2026-08-28T09:03Z)
{"filler_policy_versions":[
  {"policy_version_id":"79e81e5a-3c68-4072-ad7c-02251b25cb56","policy_id":"110ebffd-21ef-4074-9150-b78da295e61f",
   "policy_name":"halite-tidewalker","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3",
   "player_name":"daveey","display_name":null},
  {"policy_version_id":"9ed30562-956a-41d1-a1bb-580b60886ab8","policy_id":"ccc74228-2067-4077-8377-734ba5b3ee2a",
   "policy_name":"halite-corsair","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3",
   "player_name":"daveey","display_name":null}]}
```

Both rounds actually seated those filler versions and the v2 champions. Round 6's seating is in §3;
round 5's, fetched separately:

```bash
curl -sS "$BASE/rounds/round_35e9cbf2-c630-44c0-b088-9e9f5990d2f7/episode-requests" "${AUTH[@]}"
```
```
HTTP 200          (fetched 2026-08-28T09:07Z)
{"entries":[{"id":"ereq_400ff888-ec81-4e55-9b48-a661f75642c8","status":"completed",
  "coworld_id":"cow_c6743b6c-2028-4bef-8361-f7aa7d8296a2",
  "round_id":"round_35e9cbf2-c630-44c0-b088-9e9f5990d2f7",
  "replay_url":"https://softmax-public.s3.amazonaws.com/replays/e0528e24-305f-45b5-b89f-e15a2f4e0a55.replay",
  "policy_version_ids":["fae0a703-0950-4c35-aa07-94631b5054fb","7b716123-a7ac-4dfc-b3dd-7035b3fded7c",
                        "9ed30562-956a-41d1-a1bb-580b60886ab8","79e81e5a-3c68-4072-ad7c-02251b25cb56"],
  "created_at":"2026-08-28T09:00:48.335858Z"}],"next_cursor":null}
```

And the ladder's own record of who was entered, from `round_config.entrant_attributions` on the same
`/rounds` payload above:

```bash
jq -r 'if type=="array" then . else .entries end | map(select(.round_number>=5))
       | .[] | {round_number, entrants: (.round_config.entrant_attributions // "absent")}' c1.json
```
```
{ "round_number": 6, "entrants": [
    {"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player",
     "policy_version_id":"fae0a703-0950-4c35-aa07-94631b5054fb",
     "league_policy_membership_id":"lpm_c4fd0177-e455-4d1d-b382-eff726a23404"},
    {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","subject_type":"player",
     "policy_version_id":"7b716123-a7ac-4dfc-b3dd-7035b3fded7c",
     "league_policy_membership_id":"lpm_5b15e9f1-caa3-450e-986e-c22a22839246"} ] }
{ "round_number": 5, "entrants": [
    {"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player",
     "policy_version_id":"fae0a703-0950-4c35-aa07-94631b5054fb",
     "league_policy_membership_id":"lpm_c4fd0177-e455-4d1d-b382-eff726a23404"},
    {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","subject_type":"player",
     "policy_version_id":"7b716123-a7ac-4dfc-b3dd-7035b3fded7c",
     "league_policy_membership_id":"lpm_5b15e9f1-caa3-450e-986e-c22a22839246"} ] }
```

Poll trail — each line an independent `GET /rounds?league_id=$L&limit=30`, HTTP 200 every time:

| poll (UTC) | round 5 | round 6 |
|---|---|---|
| 09:02:23Z | pending (created 09:00:47Z) | — (not yet created) |
| 09:07:44Z | **completed** 09:04:52Z | — |
| 09:14:07Z | completed | — (interval not yet elapsed) |
| 09:18:52Z | completed | pending (created 09:15:52Z) |
| 09:23:55Z | completed | **completed** 09:19:56Z |

**Status: TRUE** — rounds **5** and **6** completed (09:04:52Z, 09:19:56Z), both created after the v2
fillers were registered (~08:59Z) and both seating the v2 filler *and* v2 champion version ids.

---

## 2. Both champions ranked — TRUE

Fetched twice this pass; the row below is the **later** fetch, taken after round 6 settled so it is
consistent with §3–§6.

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" -o c2b.json -w 'HTTP %{http_code}\n'
jq . c2b.json
```
```
HTTP 200          (fetched 2026-08-28T09:25Z, logged 09:25:08Z)
[
  {
    "rank": 1,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 1008.5275941745464,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 6,
    "episode_wins": 3.0,
    "episodes_played": null,
    "win_rate": 0.5,
    "policy_label": "halite-privateer:v2",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 991.4724058254535,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 6,
    "episode_wins": 3.0,
    "episodes_played": null,
    "win_rate": 0.5,
    "policy_label": "halite-tidereader:v2",
    "recent_rounds": null
  }
]
```
```bash
jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv' c2b.json
```
```
1	daveey-1	halite-privateer:v2	1008.5275941745464	6	3.0
2	daveey	halite-tidereader:v2	991.4724058254535	6	3.0
```

The earlier fetch of the same endpoint at **09:08:45Z** (logged 09:08:49Z), i.e. after round 5 and before round 6, is
pasted too because it is what proves the **v2 rounds are being counted**:

```
HTTP 200          (fetched 2026-08-28T09:08:45Z)
1	daveey	halite-tidereader:v2	1008.2298350840489	5	3.0
2	daveey-1	halite-privateer:v2	991.770164915951	5	2.0
```

`rounds_played` went **4 → 5 → 6** across rounds 5 and 6, so **each champion has `rounds_played ≥ 1`
counting v2 rounds** (two each), and both `policy_label`s read **`:v2`**, not `:v1` — the resubmission
is what the board is scoring. Requirements met: rows for `daveey` **and** `daveey-1`, each
`rounds_played ≥ 1`. The fillers `halite-tidewalker` / `halite-corsair` are **absent** from the board
entirely — they are seat-fillers, never ranked entrants.

(The rank order flipped between the two fetches; that is Elo doing its job — `daveey` won round 5's
episode on the survival ladder and `daveey-1` won round 6's. Both are ranked either way.)

**Status: TRUE.**

---

## 3. Latest round's episode request completed with a replay — TRUE

The latest **in-scope** completed round is **round 6** (`max_by(.round_number)` over completed rounds
with `round_number ≥ 5`).

```bash
R=round_d608a35e-28b2-4282-862b-33f49d3db7f2
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" -w 'HTTP %{http_code}\n'   # nested route
```
```
HTTP 200          (fetched 2026-08-28T09:24Z)
{
  "entries": [
    {
      "id": "ereq_385753a2-40a8-4148-b3c6-726192e6c5c8",
      "status": "completed",
      "coworld_id": "cow_c6743b6c-2028-4bef-8361-f7aa7d8296a2",
      "round_id": "round_d608a35e-28b2-4282-862b-33f49d3db7f2",
      "replay_url": "https://softmax-public.s3.amazonaws.com/replays/da1179c8-90e2-4c7c-833b-bc0e88145f16.replay",
      "policy_version_ids": [
        "fae0a703-0950-4c35-aa07-94631b5054fb",
        "7b716123-a7ac-4dfc-b3dd-7035b3fded7c",
        "79e81e5a-3c68-4072-ad7c-02251b25cb56",
        "9ed30562-956a-41d1-a1bb-580b60886ab8"
      ],
      "created_at": "2026-08-28T09:15:52.534639Z"
    }
  ],
  "next_cursor": null
}
```

The flat route the prompt's snippet uses is still gone; re-confirmed live this pass, not assumed:

```bash
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}" -w '\nHTTP %{http_code}\n'
```
```
{"detail":"Method Not Allowed"}
HTTP 405
```

```bash
EREQ=ereq_385753a2-40a8-4148-b3c6-726192e6c5c8
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, coworld_id,
        participants: [.participants[]|{position,policy_name,version,policy_version_id,player_name,is_filler}],
        participant_scores}'
```
```
HTTP 200          (fetched 2026-08-28T09:24Z)
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/da1179c8-90e2-4c7c-833b-bc0e88145f16.replay",
  "coworld_id": "cow_c6743b6c-2028-4bef-8361-f7aa7d8296a2",
  "participants": [
    {"position":0,"policy_name":"halite-tidereader","version":2,
     "policy_version_id":"fae0a703-0950-4c35-aa07-94631b5054fb","player_name":"daveey",  "is_filler":false},
    {"position":1,"policy_name":"halite-privateer","version":2,
     "policy_version_id":"7b716123-a7ac-4dfc-b3dd-7035b3fded7c","player_name":"daveey-1","is_filler":false},
    {"position":2,"policy_name":"halite-tidewalker","version":2,
     "policy_version_id":"79e81e5a-3c68-4072-ad7c-02251b25cb56","player_name":"daveey",  "is_filler":true},
    {"position":3,"policy_name":"halite-corsair","version":2,
     "policy_version_id":"9ed30562-956a-41d1-a1bb-580b60886ab8","player_name":"daveey",  "is_filler":true}
  ],
  "participant_scores": [
    {"position": 0, "score": 299.0},
    {"position": 1, "score": 500.0},
    {"position": 2, "score": -22.0},
    {"position": 3, "score": 1907.0}
  ]
}
```

**Explicit v2 check on this episode's entrant version ids — every one matches the UUID STATE records:**

| seat | policy_name | `version` | `policy_version_id` returned | STATE / brief UUID | match |
|---|---|---|---|---|---|
| 0 | halite-tidereader | 2 | `fae0a703-0950-4c35-aa07-94631b5054fb` | `fae0a703-0950-4c35-aa07-94631b5054fb` | ✅ |
| 1 | halite-privateer  | 2 | `7b716123-a7ac-4dfc-b3dd-7035b3fded7c` | `7b716123-a7ac-4dfc-b3dd-7035b3fded7c` | ✅ |
| 2 | halite-tidewalker | 2 | `79e81e5a-3c68-4072-ad7c-02251b25cb56` | `79e81e5a-3c68-4072-ad7c-02251b25cb56` | ✅ |
| 3 | halite-corsair    | 2 | `9ed30562-956a-41d1-a1bb-580b60886ab8` | `9ed30562-956a-41d1-a1bb-580b60886ab8` | ✅ |

None of the v1 ids (`734ab104…`, `ce5ab226…`, `dc3af747…`, `633dd3f6…`) appears. `coworld_id` is
`cow_c6743b6c…` = **0.1.1**, not the 0.1.0 coworld.

`status == "completed"`, `replay_url` non-null, seats 0 and 1 are the champions owned by `daveey` and
`daveey-1`, seats 2–3 are the two fillers (`is_filler: true`, rendered `Baseline` / `Baseline (2)` in
the replay and the scorebug — see §4). Scores are present for all four seats.

**Status: TRUE.**

---

## 4. Replay bytes are valid and show the game — TRUE

*This is the check that was FALSE at attempt 1. It is now TRUE, and the previously-failing signals are
quoted first.*

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/da1179c8-90e2-4c7c-833b-bc0e88145f16.replay" \
     -o /tmp/ev2/ep.replay -w 'HTTP %{http_code} bytes=%{size_download} type=%{content_type}\n'
jq -e . /tmp/ev2/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
python3 -c "open('/tmp/ev2/ep.replay','rb').read().decode('utf-8'); print('strict utf-8 decode: ok')"
jq -r '.format, .version, .gameVersion, .protocol, .coworld, .seed' /tmp/ev2/ep.replay
```
```
HTTP 200 bytes=1300237 type=application/octet-stream
strict UTF-8 JSON: ok
strict utf-8 decode: ok
cogame-halite-replay
1
1.0.0
halite/1
halite
1845123645
```

`protocol` = `halite/1`. That is the string the **0.1.1** manifest pins, read live this pass from
`GET $BASE/coworlds/cow_c6743b6c-2028-4bef-8361-f7aa7d8296a2` →
`.manifest.game.docs.pages[1]` (`id: "replay.md"`, title "Replay format"):

```
{"format":"cogame-halite-replay","version":1,"gameVersion":"1.0.0","protocol":"halite/1",
 "coworld":"halite","seed":8675309, "config":{ …every resolved …
```

and the same fetch confirms `.name == "halite"`, `.version == "0.1.1"`,
`.manifest_hash == "sha256:cd52ca31d9c6c00bef566e9f20c7903abaca055a14e2bec77d48b602f7e6a665"`.
Protocol match: ✅.

### 4a. The previously-failing signals

```bash
jq -c '.names, .aliases, .policySources' /tmp/ev2/ep.replay
jq -c '.results' /tmp/ev2/ep.replay
```
```
["daveey","daveey-1","Baseline","Baseline (2)"]
["FLEET-ALPHA","FLEET-BRAVO","FLEET-CHARLIE","FLEET-DELTA"]
["llm","llm","scripted:tidewalker","scripted:corsair"]
```
```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],
 "aliases":["FLEET-ALPHA","FLEET-BRAVO","FLEET-CHARLIE","FLEET-DELTA"],
 "scores":[299,500,-22,1907],"placement":[3,2,4,1],"ranking":[3,1,0,2],
 "win":[false,false,false,true],"winner":3,
 "reason":"complete","end_rule":"full_time","final_turn":399,"seed":1845123645,
 "banked":[299,500,169,1907],"ships":[3,16,0,18],"yards":[1,1,0,2],
 "mined":[15807,18468,12653,17103],"stolen":[2009,5497,2918,7864],
 "collisions_won":[10,23,13,29],"collisions_lost":[26,24,24,16],
 "eliminated_turn":[null,null,379,null],
 "llm_turns":[20,20,0,0],
 "fallbacks":[{"timeout":0,"malformed":0,"wrong_turn":0,"disconnected":0,"host_error":0},
              {"timeout":0,"malformed":0,"wrong_turn":0,"disconnected":0,"host_error":0},
              {"timeout":0,"malformed":0,"wrong_turn":0,"disconnected":0,"host_error":0},
              {"timeout":0,"malformed":0,"wrong_turn":0,"disconnected":0,"host_error":0}],
 "dead_seats":[false,false,false,false],"stop_detail":""}
```

**`results.llm_turns == [20, 20, 0, 0]`.** Not zeros for the champion seats. Seats 0 and 1 (the two
LLM champions) each answered **all 20** directive turns of the episode; seats 2 and 3 are the scripted
fillers and correctly report 0. At attempt 1 this field read `[0,0,0,0]`.

**`results.fallbacks` is all-zero for every seat** — no `timeout`, no `malformed`, no `wrong_turn`, no
`disconnected`, no `host_error`.

### 4b. Fallback count vs decision count

```bash
jq -r '[.turns[].events[]|.k]|group_by(.)|map("\(.[0])\t\(length)")|.[]' /tmp/ev2/ep.replay
jq -r '[.turns[].events[]|select(.k=="note")|"seat\(.seat)/\(.source)"]|group_by(.)|map("\(.[0])\t\(length)")|.[]' /tmp/ev2/ep.replay
jq -r '[.turns[].events[]|select(.fallback==true)]|length' /tmp/ev2/ep.replay
jq -r '[.turns[].events[]|select(.k=="note")|select(.text|test("holding the last directive|403|PermissionDenied|Error code"))]|length' /tmp/ev2/ep.replay
```
```
collide	78
convert	13
deposit	183
eliminate	1
lead	70
mine	5954
note	40
spawn	136
yardraze	9
```
```
seat0/llm	20
seat1/llm	20
```
```
0
```
```
0
```

> This replay stores events per turn under `.turns[].events`, not a flat `.events[]`, so the prompt's
> `.events[]` filters were rewritten with `.turns[].events[]` accordingly.

**Champion decision count = 40 `note` events (20 per champion seat). Fallback count = 0.**
`0 / 40 = 0 %` fallback — not merely "a small minority", none at all. Every note carries
`source: "llm"`; the string `scripted` does not appear as a note source anywhere in this replay, and
there are **zero** notes containing `403`, `PermissionDenied`, `Error code` or "holding the last
directive" (the attempt-1 signature, which was 40/40).

### 4c. Non-scripted note content — the champions reasoning about *this* board

Two representative pairs, verbatim (`jq -r '.turns[]|.t as $t|.events[]|select(.k=="note")|[$t,.seat,.source,(.latencyMs//"-"),.text]|@tsv'`):

```
20	0	llm	1587	Continue mining center cells (9,6)=7 and (11,6)=7. Ship 12-1 at (9,14) threatens collision with b-ship at (11,14). Return loaded ships home.
20	1	llm	1408	Hunt loaded enemy ships near yards. Ship 12-2 threatens b-yard cargo 144. Spawn to 8-10 ships, convert yard#2. Raid first, mine second.
```
```
260	0	llm	1072	Mine center. Ship 139-1 (cargo 218) vulnerable to Delta threats at (20,5). Return loaded ships before turn 290. Build 2nd yard.
340	1	llm	2550	Turn 340: Continue raiding. Hunt Delta's loaded ships (d0 scattered). Defend yard (15,15). Light hulls for collisions. Bank aggressively.
```

These name **specific ship ids, specific cargo amounts and specific board coordinates that only exist
in this seed** (`Ship 139-1 (cargo 218)`, `(20,5)`, `yard (15,15)`, `b-yard cargo 144`) and they change
as the episode develops — turn 0 is opening theory ("Building yard at (5,5). Spawning ships to
collect."), turn 340–380 is endgame ("bank before turn 400", "Delta ahead 1098 banked; must secure
cargo scoring"). Latencies are 854–2550 ms, i.e. real model round-trips, versus the 20–25 ms scripted
compile seen at attempt 1. Two more, showing the seats playing *different* declared strategies
(tidereader = bank the richest cell; privateer = play the collision rule):

```
0	0	llm	1878	Mining center richest cells at (9,6)=7500 and (11,6)=7500. Building yard at (5,5). Spawning ships to collect.
0	1	llm	1826	Spawn aggressively to build fleet. Target center halite deposits (15-values). Convert to yards when fleet reaches 8-10 ships. Hunt loaded en
```

### 4d. `results.reason` and the negative score

```bash
jq -c '.stop' /tmp/ev2/ep.replay ; jq -r '.turns|length' /tmp/ev2/ep.replay
```
```
{"rule":"full_time","turn":399}
400
```

`results.reason == "complete"` with `end_rule: "full_time"` — the `deadline` exception was **not
needed**. 400 turns recorded.

Seat 2's score of `-22` against a `banked` of `169` is **the coworld's documented scoring rule**, not
an anomaly; from the live 0.1.1 manifest's rules page:

```
## Scoring
score[s] = banked[s]                        if eliminated[s] is null
         = eliminated[s] - episode_steps - 1  otherwise   (negative)
```

`eliminated_turn[2] == 379` → `379 - 400 - 1 = -22`. ✅ It is a **filler** seat, so it does not touch
the champion requirement.

### 4e. The corroborating in-scope round (round 5)

The second in-scope round was fetched and parsed independently, so the result is not one lucky episode:

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/e0528e24-305f-45b5-b89f-e15a2f4e0a55.replay" -o /tmp/ev2/r5.replay
jq -r '.format,.protocol' /tmp/ev2/r5.replay ; jq -c '.results|{reason,end_rule,llm_turns,fallbacks}' /tmp/ev2/r5.replay
jq -r '[.turns[].events[]|select(.k=="note")|"seat\(.seat)/\(.source)"]|group_by(.)|map("\(.[0])\t\(length)")|.[]' /tmp/ev2/r5.replay
```
```
HTTP 200 bytes=1236330
strict UTF-8 JSON: ok · strict utf-8 decode: ok
cogame-halite-replay
halite/1
{"reason":"complete","end_rule":"full_time","llm_turns":[10,20,0,0],
 "fallbacks":[{"timeout":0,"malformed":0,"wrong_turn":0,"disconnected":0,"host_error":0}, …all four all-zero…]}
seat0/llm	10
seat1/llm	20
```

Round 5: **30 champion notes, 30 `source: "llm"`, 0 fallbacks.** Seat 0's count is 10 rather than 20
because it was **eliminated at turn 190** (`eliminated_turn: [190,null,null,null]`, score
`190-400-1 = -211`, matching the same documented rule) and stops receiving directives; its last note
is at t=180. A sample:

```
180	0	llm	968	Ship 10-1 at (2,18) with 249 cargo, returning home. Build yard 2 at (5,15). Protect loaded assets.
300	1	llm	1108	Continue raiding loaded enemy ships. Consolidate at yard B(15,15). Hunt Charlie/Delta near their yards. Maintain light hulls for collisions.
```

**Status: TRUE** — strict UTF-8 JSON under `jq -e` and `bytes.decode('utf-8')`; `protocol` `halite/1`
matches the 0.1.1 manifest; `results.reason == "complete"` / `end_rule full_time`, no exception needed;
**`llm_turns [20,20,0,0]`** for the latest in-scope round (`[10,20,0,0]` for the other, seat 0
eliminated); **fallback count 0 of 40 champion decisions (0 %)**; all champion notes are
`source: "llm"` with board-specific, evolving content. The 403 transport defect is gone.

### 4f. Ordered event excerpts (early / middle / late), reused in §8

```bash
jq -r '.turns[]|select(.t<=3)|.t as $t|.events[]|[$t,(.seat//""),.k,((.amount//.text//.pos//.bank//"")|tostring)]|@tsv' /tmp/ev2/ep.replay
```
```
0	0	note	Mining center richest cells at (9,6)=7500 and (11,6)=7500. Building yard at (5,5). Spawning ships to collect.
0	1	note	Spawn aggressively to build fleet. Target center halite deposits (15-values). Convert to yards when fleet reaches 8-10 ships. Hunt loaded en
1	0	convert	110
1	1	convert	120
1	2	convert	320
1	3	convert	330
1	0	lead	4500
2	0	spawn	110
2	1	spawn	120
2	2	spawn	320
2	3	spawn	330
```
```bash
jq -r '.turns[]|select(.t>=199 and .t<=201)|…|@tsv' /tmp/ev2/ep.replay | head -30
```
```
199	0	mine	2      199	0	mine	2      199	0	mine	5      199	0	mine	1
199	1	mine	1      199	1	mine	10     199	1	mine	1      199	1	mine	2   (…7 for seat 1)
199	2	mine	2      199	2	mine	12     199	2	mine	3
199	3	mine	9      199	3	mine	2      199	3	mine	12     199	3	mine	1
200		collide	7
200	3	deposit	309
200	0	mine	2 …    200	1	mine	1 …
```
```bash
jq -r '.turns[]|select(.t>=396)|…|@tsv' /tmp/ev2/ep.replay
```
```
396	3	mine	2
397	3	mine	2
398	0	deposit	22
398	1	deposit	22
398	3	deposit	4
```
```bash
jq -c '[.turns[]|.t as $t|.events[]|select(.k=="collide")|{t:$t,pos,survivor,lost,stolen}]|.[0:3][]' /tmp/ev2/ep.replay
jq -c '[.turns[]|.t as $t|.events[]|select(.k=="yardraze")|{t:$t,pos,yardSeat,shipSeat}]|.[]' /tmp/ev2/ep.replay
jq -c '[.turns[]|.t as $t|.events[]|select(.k=="eliminate")|{t:$t,seat,turn}]|.[]' /tmp/ev2/ep.replay
jq -c '[.turns[]|.t as $t|.events[]|select(.k=="lead")|{t:$t,seat,bank}]|.[0:8][]' /tmp/ev2/ep.replay
jq -c '.turns[398]|{t,hash,banks:[.players[]|.[0]]}' /tmp/ev2/ep.replay
```
```
{"t":13,"pos":135,"survivor":{"seat":0,"ship":"4-1"},"lost":[{"seat":0,"ship":"2-1","cargo":250}],"stolen":250}
{"t":13,"pos":137,"survivor":{"seat":1,"ship":"4-2"},"lost":[{"seat":1,"ship":"2-2","cargo":250}],"stolen":250}
{"t":13,"pos":303,"survivor":{"seat":2,"ship":"4-3"},"lost":[{"seat":2,"ship":"2-3","cargo":250}],"stolen":250}
```
```
{"t":97,"pos":278,"yardSeat":3,"shipSeat":2}   {"t":119,"pos":112,"yardSeat":1,"shipSeat":0}
{"t":140,"pos":190,"yardSeat":3,"shipSeat":0}  {"t":161,"pos":320,"yardSeat":2,"shipSeat":3}
{"t":193,"pos":23,"yardSeat":0,"shipSeat":1}   {"t":212,"pos":330,"yardSeat":3,"shipSeat":1}
{"t":236,"pos":261,"yardSeat":2,"shipSeat":1}  {"t":245,"pos":82,"yardSeat":3,"shipSeat":0}
{"t":271,"pos":361,"yardSeat":2,"shipSeat":3}
```
```
{"t":379,"seat":2,"turn":379}
```
```
{"t":1,"seat":0,"bank":4500}   {"t":36,"seat":1,"bank":1144}  {"t":39,"seat":0,"bank":947}
{"t":41,"seat":1,"bank":1228}  {"t":48,"seat":0,"bank":1065}  {"t":52,"seat":2,"bank":1065}
{"t":57,"seat":0,"bank":818}   {"t":58,"seat":1,"bank":473}
```
```
{"t":398,"hash":"6b1ab015e9b87893","banks":[299,500,169,1907]}
```

---

## 5. Hosted game log is clean — TRUE

The logs body is python byte-string reprs under `===== container: … =====` headers, so it was decoded
with `ast.literal_eval` per repr before grepping (playbook §10) — a line-based grep on the raw bytes
undercounts.

```bash
curl -sS "$BASE/episode-requests/ereq_385753a2-40a8-4148-b3c6-726192e6c5c8/artifacts/logs" \
     "${AUTH[@]}" "${ELEV[@]}" -o logs6.raw -w 'HTTP %{http_code} bytes=%{size_download}\n'
python3 …ast.literal_eval per container… > logs6.txt
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs6.txt || echo CLEAN
```
```
HTTP 200 bytes=1740          (fetched 2026-08-28T09:24Z)
decoded bytes: 1705 containers: 4
CLEAN
```

The whole decoded log, verbatim (it is short):

```
===== container: coworld-init-config =====

===== container: bedrock-sidecar =====
2026-08-28 09:16:00,236 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1","has_role_arn":true,"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar","episode_request_id":"385753a2-40a8-4148-b3c6-726192e6c5c8","job_request_id":"da1179c8-90e2-4c7c-833b-bc0e88145f16","role":"game","slot":"game","image_digest":"sha256:11e8a4db3cad3318a5dbcce5ecb519b77ff5d053f5f58c34d09b44a0fb02c895"}
[2026-08-28 09:16:00 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-08-28 09:16:00,428 INFO hypercorn.error Running on http://127.0.0.1:9100 (CTRL + C to quit)

===== container: game =====
cogame-halite 1.0.0 listening on 0.0.0.0:8080; seats=4 turns=400 seed=1845123645
seat 1 (FLEET-BRAVO) connected
seat 1 registered policy='llm' label='Play the collision rule. Keep your hulls'
seat 0 (FLEET-ALPHA) connected
seat 0 registered policy='llm' label='Play the bank. Mine the richest cell wit'
seat 3 (FLEET-DELTA) connected
seat 3 registered policy='scripted:corsair' label='corsair'
seat 2 (FLEET-CHARLIE) connected
seat 2 registered policy='scripted:tidewalker' label='tidewalker'
episode end: reason=complete end_rule=full_time turn=399 scores=[299, 500, -22, 1907] llm_turns=[20, 20, 0, 0] dead=[False, False, False, False]
wrote results (1076 bytes) to file:///coworld/results.json
wrote replay (1300237 bytes) to file:///coworld/replay
episode settled 201.8s after the episode began (hard stop 660s; this container has been up 201.8s)
seat 0 disconnected
seat 2 disconnected
seat 3 disconnected
seat 1 disconnected

===== container: worker =====
```

Zero matches for `falling back|LLM provider is unavailable|cut off at max_tokens|rejected`, and the
game container's own end line independently states **`llm_turns=[20, 20, 0, 0]`** — this log now
corroborates §4 instead of masking it. Round 5's log was fetched and decoded the same way
(`HTTP 200 bytes=1741`, 4 containers, 1706 decoded bytes) and is also **CLEAN**, ending
`llm_turns=[10, 20, 0, 0]`.

> Attempt 1 attached a caveat here — that a CLEAN grep was not evidence the LLM path was healthy,
> because the player pods are absent from this bundle. The caveat still describes the bundle
> correctly (four containers: `coworld-init-config`, `bedrock-sidecar`, `game`, `worker`), but the
> question it guarded is now answered affirmatively by the replay in §4 and by this log's own
> `llm_turns` line, so it is no longer a reservation about the verdict.

**Status: TRUE.**

---

## 6. The public page uses the static replay path — TRUE

*Source used: the **SSR payload's `state.playlist[0]`** for the featured match, plus the
**replay-session route** for the iframe `src`.* Both cheaper sources were tried first and are recorded
here as empty, not as failures:

```bash
curl -sS "https://softmax.com/halite" -o page.html -w 'HTTP %{http_code} bytes=%{size_download}\n'
grep -o '<iframe[^>]*src="[^"]*"' page.html || echo '(no match — grep found nothing)'
```
```
HTTP 200 bytes=730292          (fetched 2026-08-28T09:24Z)
(no match — grep found nothing)
```
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)|.[]|select(.name=="halite")|{id,canonical,replay_viewer,featured_match}'
```
```
{
  "id": "cow_c6743b6c-2028-4bef-8361-f7aa7d8296a2",
  "canonical": true,
  "replay_viewer": null,
  "featured_match": null
}
{
  "id": "cow_97d89fb8-8a54-423b-ac60-7080b318271a",
  "canonical": false,
  "replay_viewer": null,
  "featured_match": null
}
```

(0.1.1 is `canonical: true`; the old 0.1.0 coworld is now `canonical: false`.) Both empty results are
the platform-wide behaviour the playbook §Featured match records (client-rendered iframe;
`featured_match` null for every coworld). The featured match **is** server-rendered into the page's
SSR payload — extracted from the same `page.html` fetched above (the payload is JSON-escaped inside
the HTML, so `"playlist"` must be searched as `\"playlist\"`):

```
…-4611-8200-59349283a022\",\"playlist\":[{\"episodeId\":\"6452eb3a-7b7e-49f4-b2da-8a21f1ad2955\",
\"coworldId\":\"cow_c6743b6c-2028-4bef-8361-f7aa7d8296a2\",\"coworldName\":\"halite\",
\"coworldVersion\":\"0.1.1\",
\"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/da1179c8-90e2-4c7c-833b-bc0e88145f16.replay\",
\"finishedAt\":\"2026-08-28T09:19:54.795577Z\",\"roundNumber\":6,\"episodeNumber\":1,
\"code\":\"halite.r6.e1\",
\"matchup\":{\"divisionId\":\"div_165193cb-f037-4f20-ac3d-25a3a4a7d440\",\"divisionName\":\"Competition\",
 \"first\":{\"rank\":1,\"player_id\":\"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d\",\"player_name\":\"daveey-1\",
  \"score\":1008.5275941745464,\"score_label\":\"MMR\",\"rounds_played\":6,\"episode_wins\":3,
  \"win_rate\":0.5,\"policy_label\":\"halite-privateer:v2\"},
 \"second\":{\"rank\":2,\"player_id\":\"ply_44ae9048-3242-4654-881f-6d9d43347fa3\",\"player_name\":\"daveey\",
  \"score\":991.4724058254535,\"score_label\":\"MMR\",\"rounds_played\":6,\"episode_wins\":3,
  \"win_rate\":0.5,\"policy_label\":\"halite-tidereader:v2\"}},
\"inspectUrl\":\"/observatory/v2?tab=overview&detail=episode-request:ereq_385753a2-40a8-4148-b3c6-726192e6c5c8\",
\"outcome\":\"first\"}],\"pool\":{\"replays\":[{\"kind\":\"replay\",\"round\":{\"id\":\"round_d608a35e-28b2-4282-862b-33f49d3db7f2\",\"round_number\":6, …
```

**The featured match is already a v2 round — no re-fetch was needed.** It is `halite.r6.e1`:
`coworldVersion 0.1.1`, `coworldId cow_c6743b6c…`, `roundNumber 6`, `replayUrl` = the round-6 replay
of §3/§4, `inspectUrl` naming `ereq_385753a2…`, and both matchup slots labelled **`:v2`**. It is not
the old `halite.r2.e1` / `ce7c0511…` v1 episode attempt 1 saw. Two ranked players are present, so this
is not the "fewer than two ranked players" absence.

The iframe `src` is what the page's own JS asks for:

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_c6743b6c-2028-4bef-8361-f7aa7d8296a2",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/da1179c8-90e2-4c7c-833b-bc0e88145f16.replay"}' \
  -w 'HTTP %{http_code}\n'
```
```
HTTP 200          (fetched 2026-08-28T09:25Z, logged 09:25:08Z)
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_c6743b6c-2028-4bef-8361-f7aa7d8296a2/sha256%3Acd52ca31d9c6c00bef566e9f20c7903abaca055a14e2bec77d48b602f7e6a665/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fda1179c8-90e2-4c7c-833b-bc0e88145f16.replay",
  "ready": true
}
```
```bash
curl -sS -o /dev/null -w 'iframe src GET HTTP %{http_code} type=%{content_type}\n' "${SRC%%#*}"
```
```
iframe src GET HTTP 200 type=text/html; charset=utf-8
```

The path is `/v2/coworlds/replays/static/<cow_id>/<manifest_sha, URL-encoded>/index.html`,
`ready: true`, and the replay arrives as the URL-encoded **`#replay=` fragment** — the form the
playbook records for 2026-08-28; both fragment and query form are the static route.

- `<cow_id>` = `cow_c6743b6c-2028-4bef-8361-f7aa7d8296a2` — the **new** 0.1.1 coworld ✅
- `<sha>` = `sha256:cd52ca31d9c6c00bef566e9f20c7903abaca055a14e2bec77d48b602f7e6a665`
  (URL-encoded `sha256%3Acd52ca31…`) — the **new** manifest hash, matching STATE exactly ✅
- No `/client/replay` pod URL anywhere in it ✅

**Status: TRUE.**

---

## 7. Certification declared the static bundle — TRUE

*Source used: the **committed `runs/2026-08-27-halite/release-result.json`***, which is already the
**0.1.1** artifact (committed by phase 40 in `79132de 60 halite: llm sidecar fix + release 0.1.1`).
No re-download was needed and `/tmp` was not read.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-27-halite/release-result.json
jq -r '.version, .ok, .canonical, .cow_id' runs/2026-08-27-halite/release-result.json
git log --oneline -1 -- runs/2026-08-27-halite/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```
```
0.1.1
true
true
cow_c6743b6c-2028-4bef-8361-f7aa7d8296a2
```
```
79132de 60 halite: llm sidecar fix + release 0.1.1
```

Contains the required string `Replay liveness: skipped (static replay bundle declared`, and the file
is the artifact of **this** release (`0.1.1`, `cow_c6743b6c…`, release run `33156839080` per STATE),
not the superseded 0.1.0 one.

**Status: TRUE.**

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — TRUE

*(a) Dispatch.* The iframe `src` from §6 (fragment and all) was opened in headless chromium by
`viewer-check.yml` in `Metta-AI/coworld-builder`, dispatched by this verifier at **09:25:16Z**:

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_c6743b6c-2028-4bef-8361-f7aa7d8296a2/sha256%3Acd52ca31d9c6c00bef566e9f20c7903abaca055a14e2bec77d48b602f7e6a665/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fda1179c8-90e2-4c7c-833b-bc0e88145f16.replay'
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 5 \
 | jq -r 'sort_by(.createdAt)|reverse|.[]|[.databaseId,.createdAt,.status]|@tsv'      # BEFORE
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
sleep 12
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 6 \
 | jq -r 'sort_by(.createdAt)|reverse|.[]|[.databaseId,.createdAt,.status]|@tsv'      # AFTER
```

Run list **before** the dispatch (09:25:14Z) — recorded so "the new run" is identified by difference,
never by grabbing "the latest":

```
33155441744	2026-08-28T08:27:56Z	completed
33155420501	2026-08-28T08:27:36Z	completed      ← attempt 1's run
33154949153	2026-08-28T08:20:24Z	completed
33153918882	2026-08-28T08:04:55Z	completed
33136591103	2026-08-28T02:39:59Z	completed
```

**After** the dispatch (09:25:28Z):

```
33159290682	2026-08-28T09:25:16Z	in_progress     ← mine (same second as the dispatch)
33155441744	2026-08-28T08:27:56Z	completed
33155420501	2026-08-28T08:27:36Z	completed
33154949153	2026-08-28T08:20:24Z	completed
33153918882	2026-08-28T08:04:55Z	completed
33136591103	2026-08-28T02:39:59Z	completed
```

Ownership proven from the run's own log line, not from timing alone:

```bash
gh run view 33159290682 -R Metta-AI/coworld-builder --log | grep 'url: https' | head -1
```
```
viewer-check	Load the viewer	2026-08-28T09:25:49.0556047Z url: https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_c6743b6c-2028-4bef-8361-f7aa7d8296a2/sha256%3Acd52ca31d9c6c00bef566e9f20c7903abaca055a14e2bec77d48b602f7e6a665/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fda1179c8-90e2-4c7c-833b-bc0e88145f16.replay
```

— byte-identical to the `$SRC` above: it rendered the **0.1.1** cow id, the **new** manifest sha and
the **round-6 v2** replay.

```bash
gh run watch 33159290682 -R Metta-AI/coworld-builder --exit-status ; echo "watch exit=$?"
rm -rf runs/2026-08-27-halite/viewer-check && mkdir -p runs/2026-08-27-halite/viewer-check
gh run download 33159290682 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-27-halite/viewer-check
ls -l runs/2026-08-27-halite/viewer-check/
```
```
✓ viewer-check in 38s (ID 98809572651)
  ✓ Install Playwright (pinned 1.55.0)  ✓ Load the viewer  ✓ Summary
  ✓ Upload the evidence  ✓ Fail if the viewer did not load
watch exit=0        (green: the workflow's own "Fail if the viewer did not load" gate passed)
```
```
-rw-r--r-- 1 root root      0 smoke-stderr.txt
-rw-r--r-- 1 root root    688 smoke-stdout.txt
-rw-r--r-- 1 root root   1522 viewer-smoke.json
-rw-r--r-- 1 root root 776824 viewer-smoke.png
```

That directory is committed with this file (attempt 1's artifact was **overwritten**, not kept
alongside).

*(b) The readouts, verbatim.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-27-halite/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":2800,"clock":"TURN 8 / 399 MINING","scorebug":"ALPHA daveey 2500 ♔ AFLOAT 281 4 SHIPS · 1 YARDS AT RISK 0 CHARLIE Baseline 2500 AFLOAT 281 4 SHIPS · 1 YARDS AT RISK 0 TURN 8 / 399 MINING BRAVO daveey-1 2500 AFLOAT 281 4 SHIPS · 1 YARDS AT RISK 0 DELTA Baseline (2) 2500 AFLOAT 281 4 SHIPS · 1 YARDS AT RISK 0","feed_lines":0}
```
```bash
jq -c '.signals'                  runs/2026-08-27-halite/viewer-check/viewer-smoke.json
jq -r '.failure // "no failure"'  runs/2026-08-27-halite/viewer-check/viewer-smoke.json
jq -c '.canvas_text'              runs/2026-08-27-halite/viewer-check/viewer-smoke.json
jq -c '.console_tail'             runs/2026-08-27-halite/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["ready"],"bridge_ready":true,"bridge_error":[]}
```
```
no failure
{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}
["[bridge] ready"]
```

The three scrub readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | clock readout |
|---|---|
| 0 % | `TURN 8 / 399 MINING` |
| 50 % | `TURN 200 / 399 RAIDING` |
| 100 % | `TURN 398 / 399 HAULING` |

**Both conditions hold: `loaded: true`** — via `data-replay-loaded="true"` *and* the `coworld-replay`
bridge's `ready` (console tail `[bridge] ready`), first frame at **2800 ms**, `failure` null — **and
the three clock readouts differ** (turn 8 → 200 → 398, with the phase caption changing
`MINING` → `RAIDING` → `HAULING`). The shell does expose `#scrub`; no "(no #scrub…)" caveat is needed.
`canvas_text.total == 0` means the renderer draws no text inside the canvas at all (all labels live in
the DOM chrome), so the `never_inside` / `ellipsized` guards are vacuously 0 — no caption is stranded
off-canvas.

*(c) Spectator judgment.* `viewer-check/viewer-smoke.png` is 1280 × 800, captured at the 100 % scrub
position, and it shows a **legible, complete game** — the game the replay in §4 records.

- **Clock**, centre-top: `TURN 398 / 399` with the caption `HAULING`. Matches
  `results.final_turn == 399` and the 100 % scrub readout.
- **Scorebug**, four plates in the two top corners, each: colour swatch, alias, real player name,
  banked halite (large), then `AFLOAT n`, `n SHIPS · n YARDS`, `AT RISK n`. Read off the image:
  `ALPHA daveey 299 / AFLOAT 234 / 3 SHIPS · 1 YARDS / AT RISK 0`;
  `CHARLIE Baseline 169 / AFLOAT 0 / 0 SHIPS · 0 YARDS` **greyed out**;
  `daveey-1 BRAVO 500 / AT RISK 0 / 16 SHIPS · 1 YARDS / AFLOAT 2401`;
  `♔ 1907 Baseline (2) DELTA / AT RISK 0 / 18 SHIPS · 2 YARDS / AFLOAT 2557`.
  Reconciled against §4: `banked == [299, 500, 169, 1907]` ✅ seat for seat,
  `ships == [3, 16, 0, 18]` ✅, `yards == [1, 1, 0, 2]` ✅, and the grey wash on CHARLIE is
  `eliminated_turn[2] == 379` ✅. The crown sits on DELTA, `results.winner == 3` ✅.
- **Board**, filling the middle third: a dark 21 × 21 arena tiled with pale halite-crystal glyph
  clusters over a faintly veined ground, thinner where the fleets have mined it out. Ships are drawn
  as small hulls in four distinct fleet colours — orange (ALPHA, a pair top-left near a boxed orange
  shipyard tile), teal (BRAVO, a dense cluster right of centre with a highlighted yard), lime (DELTA,
  two clusters left-of-centre and bottom-centre with boxed yards) — and loaded hulls carry a bright
  cargo pip. CHARLIE has no hulls on the board, exactly as its 0-ship plate says.
- **Feed**, bottom-right of the board: three lines, `DELTA banks 4`, `BRAVO banks 22`,
  `ALPHA banks 22`. That reconciles line for line with §4f's late excerpt —
  `398 3 deposit 4`, `398 1 deposit 22`, `398 0 deposit 22` ✅. The DOM `feed_lines: 0` is not a
  contradiction: that field was captured at the initial paint (turn 8, before any deposit had
  happened); the rendered feed at turn 398 is visibly populated.
- **Transport strip**, bottom-left: restart, step-back, play, `+5`, step, loop, fast-forward, a
  `spoilers` toggle (lit), and the endcard/win chip `DELTA WINS   398 / 399`. Bottom-right: the
  `1× 2× 3× 4× 8× 16×` speed selector with `1×` selected. Across the full width below them, the
  **scrubber**: a pale filled track with the playhead at the far right (100 %) and a dense field of
  coloured, kind-tinted **beat markers** clustered where the action was — the replay has 78 `collide`,
  13 `convert`, 9 `yardraze`, 70 `lead` and 1 `eliminate` beats to place, and the visible density
  matches that distribution (heavy through the mid-game, sparse in the last fifth, which is also what
  §4f's late excerpt shows: turns 396–398 are only mines and deposits).

Nothing is empty, frozen or unreadable. The clock advances under the scrubber across three sampled
positions, the picture is dense with state, and a spectator can read **who is winning** (DELTA,
1907 banked, crowned) and **why** (29 collisions won and 7864 halite stolen, per §4's `results`).
Critically for this attempt, the champions on screen — `ALPHA daveey` and `BRAVO daveey-1` — are now
LLM-driven seats (§4), so the speech lines the feed carries during playback are real directives, not
40 copies of a 403 error string.

**Chrome provenance:** the screenshot looks like the starter family. The design note
(`runs/2026-08-27-halite/design.md` §"One starter supplies all four viewer files: `Metta-AI/coworld-ctf`"
and §"Chrome provenance") declares `client/chrome_common.js` and `client/broadcast_core.js` taken from
coworld-ctf and `client/replay_broadcast.html` as **ctf's page with one appended game block**, keeping
`#chrome`, `#scorebug`, `#plates-l`/`#plates-r`, `#clock`/`#clock-caption`, `#board`, `#killfeed`,
`#endcard`, and the whole `#transport` block (`#btn-restart … #btn-spoilers`, `#win-chip`,
`#speedchips`, `#scrub`) verbatim. Every one of those is present and in its inherited position in the
rendered frame — the same dark transport strip with the `+5`/loop/fast-forward cluster and `spoilers`
toggle, the same corner scorebug plates, the same clickable beat-marker scrubber, the same endcard win
chip as coworld-ctf / paintbot / raid / hive. This is **not** a gridlock-style rewrite that merely
shares ids. One deliberate difference, and it is *declared*: there is **no momentum graph** above the
scrubber, because §Chrome provenance "Removed" drops `#momentum` (it survives as a
`display:none !important` stub only because `chrome_common.js` is pinned byte-for-byte and
dereferences it — design.md §Deviations (build) item 1). The rendered frame is consistent with the
declared provenance, deviations included.

**Status: TRUE** (`loaded: true`, three differing clock readouts, rendered evidence committed at
`runs/2026-08-27-halite/viewer-check/` from run `33159290682`).

---

## Definition-of-done summary

**All eight items are TRUE on evidence fetched in this pass**, against coworld **0.1.1**
(`cow_c6743b6c-2028-4bef-8361-f7aa7d8296a2`) and champion policies at **v2**, using only rounds ≥ 5.

The item that failed at attempt 1 is fixed and the fix is visible in the bytes: the latest in-scope
round's replay reports `results.llm_turns == [20, 20, 0, 0]` with `results.fallbacks` all-zero and
**40 of 40** champion `note` events at `source: "llm"` — against attempt 1's `[0,0,0,0]` and 40/40
`source: "scripted"` carrying `403 … Invalid API Key format`. The corroborating round 5 reads
`[10, 20, 0, 0]` with 30/30 `llm` notes (seat 0's lower count is its documented elimination at turn
190). The ladder is producing rounds on schedule, both champions are ranked at `:v2` with
`rounds_played 6`, the featured match on `softmax.com/halite` is the v2 round-6 episode served
through the static replay path for the new cow id and manifest sha, certification declared the static
bundle, and the viewer draws and advances.

No documented-exception clause was invoked anywhere in this pass: `results.reason` is `complete` (no
`deadline`), and no `LLM provider is unavailable` line appeared, so no cross-check against another LLM
coworld was needed.
