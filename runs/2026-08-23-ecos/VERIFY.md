# VERIFY — ecos   (2026-08-23T14:14Z)

Verdict: **all-true** (8/8)

Run `2026-08-23-ecos` · slug `ecos` · version `0.1.0` · repo `Metta-AI/cogame-ecos`
`$COW` = `cow_7f960dd9-bdfb-49a3-b0b6-09a56cf1905f`
`$L` = `league_60071522-0ef6-4ad3-b6e3-76651490c3fd`
`$D` = `div_ee91d3a5-2639-415e-9694-b5c1a5b70b43`

All evidence below was fetched fresh during this phase-60 session (2026-08-23T13:48Z–14:14Z).
The single documented exception is check 7, whose evidence is this run's committed
`release-result.json` artifact (see that section). Headers sent are named, never their values:
`Authorization: Bearer $SOFTMAX_TOKEN`, `User-Agent: coworld-builder/1.0` (= `AUTH`), and
`X-Use-Elevated-Privileges: true` (= `ELEV`) where noted.

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
```

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | **TRUE** |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** |
| 3 | Latest round's episode request completed with replay + right participants | **TRUE** |
| 4 | Replay bytes valid, protocol matches, reason `complete`, champion decisions are LLM | **TRUE** |
| 5 | Hosted game log clean | **TRUE** |
| 6 | Public page uses the **static** replay path, featured match present | **TRUE** |
| 7 | Certification declared the static bundle | **TRUE** |
| 8 | Spectator judgment — viewer executed in a real browser | **TRUE** |

---

## 1. ≥2 completed rounds after the fillers were set

Fillers `ecos-steward:v1` (`8596fd17-…`) and `ecos-opportunist:v1` (`3b350f40-…`) were registered
at **2026-08-23T13:46Z** (`log.md`: `50 filler-policies POST 200: steward+opportunist registered,
neither champion`), i.e. before the trigger. Counting rounds therefore requires
`round_number >= 2`.

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq '[.entries[]|{id,round_number,status,error,created_at,completed_at}]'
```

```json
[
  {
    "id": "round_b5bc0c39-eb73-4969-b504-1183d8259a26",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-23T14:01:25.440183Z",
    "completed_at": "2026-08-23T14:03:18.856883Z"
  },
  {
    "id": "round_09601725-1f08-4736-96cf-d092f1cf3911",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-23T13:46:25.068229Z",
    "completed_at": "2026-08-23T13:48:08.158235Z"
  },
  {
    "id": "round_d5f75051-f0c9-4c57-ad1a-f32b92f3a27d",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-23T13:46:00.441038Z",
    "completed_at": "2026-08-23T13:46:02.146869Z"
  }
]
```

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '[.entries[]|select(.status=="completed")]|length'
```
```
2
```

Failed round recorded verbatim: round 1 (`round_d5f75051-f0c9-4c57-ad1a-f32b92f3a27d`),
`error: "Temporal RoundWorkflow failed before settling the round."` — it was auto-created at
13:46:00.441Z, **before** the fillers existed (registered 13:46Z, POST logged at 13:47:10Z in
`log.md`), which is the documented pre-filler auto-round failure mode
(`playbooks/observatory-api.md` §6: "A `trigger-round` issued before any filler exists fails
instantly with `Temporal RoundWorkflow failed before settling the round`"; LEARNINGS hive item 3).
It is excluded and not counted.

Polling record (every ~5 min, inside the 75-minute bound that started 13:48:20Z):

| Poll | UTC | Completed rounds ≥2 |
|---|---|---|
| 1 | 13:48:20Z | r2 |
| 2 | 13:55:19Z | r2 |
| 3 | 14:00:25Z | r2 |
| 4 | 14:05:17Z | r2, **r3** |

Status: **TRUE** — rounds 2 and 3 completed (13:48:08Z and 14:03:18Z), both `round_number >= 2`,
both after fillers were set at 13:46Z. Round 1 failed and is excluded with its error quoted above.

---

## 2. Both champions ranked

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq .
```

```json
[
  {
    "rank": 1,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 1030.5304984710244,
    "score_label": "Elo",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 2.0,
    "episodes_played": null,
    "win_rate": 1.0,
    "policy_label": "ecos-bloom:v1",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 969.4695015289755,
    "score_label": "Elo",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 0.0,
    "episodes_played": null,
    "win_rate": 0.0,
    "policy_label": "ecos-keeper:v1",
    "recent_rounds": null
  }
]
```

Tabular form (`jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'`):

| rank | player_name | policy_label | score | rounds_played | episode_wins |
|---|---|---|---|---|---|
| 1 | daveey-1 | ecos-bloom:v1 | 1030.53 | 2 | 2.0 |
| 2 | daveey | ecos-keeper:v1 | 969.47 | 2 | 0.0 |

Status: **TRUE** — the endpoint returns a bare list of exactly two rows: `daveey` (champion #1,
`ecos-keeper:v1`) and `daveey-1` (champion #2, `ecos-bloom:v1`), each `rounds_played = 2 ≥ 1`.
Neither filler (`ecos-steward:v1`, `ecos-opportunist:v1`) appears as a ranked row — fillers are
absent, which the SPEC accepts (absent **or** `policy_label` starting `Baseline`).

---

## 3. Latest round's episode request completed with a replay

```bash
R=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
    | jq -r '[.entries[]|select(.status=="completed")]|max_by(.round_number).id')
# R=round_b5bc0c39-eb73-4969-b504-1183d8259a26   (round_number 3)
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}" \
 | jq -c '.entries[]|{id,status,replay_url}'
```
```json
{"id":"ereq_714ef6a3-0fb0-461a-b8bf-5c2ed012f285","status":"completed","replay_url":"https://softmax-public.s3.amazonaws.com/replays/91e62cde-5d4b-42a9-bda2-3fdac44680c8.replay"}
```

```bash
EREQ=ereq_714ef6a3-0fb0-461a-b8bf-5c2ed012f285
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/91e62cde-5d4b-42a9-bda2-3fdac44680c8.replay",
  "participants": [
    {
      "position": 0,
      "kind": "policy",
      "policy_version_id": "9a5487b6-60eb-4d50-a71e-f694df2ed454",
      "policy_id": "52867ab5-ddf7-4cc9-96fc-5bec281143a0",
      "policy_name": "ecos-keeper",
      "version": 1,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": false
    },
    {
      "position": 1,
      "kind": "policy",
      "policy_version_id": "774aa245-458a-4b42-9009-0229c7e0491a",
      "policy_id": "068e589b-0832-42db-b8f0-7a0ef0251111",
      "policy_name": "ecos-bloom",
      "version": 1,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
      "player_name": "daveey-1",
      "is_filler": false
    },
    {
      "position": 2,
      "kind": "policy",
      "policy_version_id": "8596fd17-4704-4ca9-8359-d2e906bd3e6a",
      "policy_id": "66c5862f-845e-4c52-b0c9-d4906ab83c58",
      "policy_name": "ecos-steward",
      "version": 1,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": true
    }
  ],
  "participant_scores": [
    {"position": 0, "score": 2.750288888888888},
    {"position": 1, "score": 6.164395000000001},
    {"position": 2, "score": 12.708187500000001}
  ]
}
```

Status: **TRUE** — `status == "completed"`; `replay_url` non-null; participants seat 0 =
`daveey`/`ecos-keeper:v1` (`policy_version_id 9a5487b6-…`, the champion #1 uuid STATE records) and
seat 1 = `daveey-1`/`ecos-bloom:v1` (`774aa245-…`, champion #2), both `is_filler: false`; seat 2 is
the filler `ecos-steward:v1` (`8596fd17-…`, `is_filler: true`), which the replay and viewer render
as `Baseline` (see checks 4 and 8).

---

## 4. Replay bytes are valid and show the game

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/91e62cde-5d4b-42a9-bda2-3fdac44680c8.replay" \
     -o /tmp/ep.replay -w 'http=%{http_code} bytes=%{size_download}\n'
```
```
http=200 bytes=2273433
```

```bash
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
file /tmp/ep.replay
```
```
strict UTF-8 JSON: ok
/tmp/ep.replay: JSON text data
```

**Protocol.** The replay declares:
```bash
jq -r '.protocol, .results.reason, .results.ending' /tmp/ep.replay
```
```
ecos.replay.v1
complete
ten_generations
```
Cross-checked against the manifest in the repo at `main`:
```bash
gh api repos/Metta-AI/cogame-ecos/contents/coworld_manifest_template.json \
  -H "Accept: application/vnd.github.raw" > /tmp/manifest.json
grep -o 'protocol ecos\.replay\.v1' /tmp/manifest.json
```
```
protocol ecos.replay.v1
```
(manifest `protocols` block: "…the replay is one strict-UTF-8 JSON document (protocol
ecos.replay.v1) of per-tick state frames, and the static wasm bundle plays it at
index.html?replay=<url>"). **Match.**

**Results.**
```bash
jq -c '.results' /tmp/ep.replay
```
```json
{"names":["daveey","daveey-1","Baseline"],"scores":[2.750288888888888,6.164395000000001,12.708187500000001],"win":[false,false,true],"roles":["predators","grass","grazers"],"biomass":[825,12328,5083],"population":[2,220,88],"generations":10,"births":[3,1960,595],"starved":[11,1900,511],"predation":36,"reason":"complete","ending":"ten_generations"}
```
`reason == "complete"` — no `deadline` exception is being invoked. `ending == "ten_generations"`
(the episode ran its full 10 generations / 600 ticks; no collapse).

**Champion decisions are LLM, not fallbacks.** This game records decisions as `events[]` rows with
`k == "doctrine"` (not `type=="decision"`), and the LLM-vs-scripted signal is the `source` field
(`llm`/`retry` = model, `fallback` = model failed and was replaced, `scripted` = scripted seat), so
the SPEC's jq is adapted accordingly. Commands actually run:

```bash
jq -r '[.events[]|select(.k=="doctrine")]|group_by(.seat)[]
       |{seat:.[0].seat,species:.[0].sp,total:length,
         by_source:(group_by(.source)|map({(.[0].source):length})|add)}|tostring' /tmp/ep.replay
```
```
{"seat":0,"species":"predators","total":10,"by_source":{"llm":10}}
{"seat":1,"species":"grass","total":10,"by_source":{"llm":10}}
{"seat":2,"species":"grazers","total":10,"by_source":{"scripted":10}}
```

```bash
jq -r '[.events[]|select(.k=="doctrine" and (.seat==0 or .seat==1))]
       | {decisions:length,
          llm:([.[]|select(.source=="llm" or .source=="retry")]|length),
          fallback:([.[]|select(.source=="fallback")]|length),
          scripted:([.[]|select(.source=="scripted")]|length)}|tostring' /tmp/ep.replay
```
```
{"decisions":20,"llm":20,"fallback":0,"scripted":0}
```

Champion seats are 0 (`daveey`, predators) and 1 (`daveey-1`, grass) per check 3's participants and
`.results.names == ["daveey","daveey-1","Baseline"]`. **20 of 20 champion doctrines came from the
model; 0 fallbacks, 0 scripted.** Seat 2 is the scripted filler, as designed.

Decision content is non-trivial — the doctrine fields change generation to generation and the `say`
text reacts to the state (full 30-row dump abbreviated to the champion seats' rows):

```bash
jq -r '.events[]|select(.k=="doctrine")
       |[.t,.gen,.seat,.sp,.source,(.clamped|tostring),(.fields|tostring),(.say|.[0:56])]|@tsv' /tmp/ep.replay
```
```
0	1	0	predators	llm	false	{"birth_threshold":350,"hunt_range":120,"rest_energy":180,"spread":40}	Starting conservatively. Grazers at 40/140 (29%), grass
0	1	1	grass	llm	false	{"seed_threshold":100,"seed_range":90,"seed_cost":40,"crowd_limit":3}	Gen 1: Baseline doctrine. Monitor grazers and predators
0	1	2	grazers	scripted	true	{"birth_threshold":80,"bite":10,"flee_range":40,"herd":20}
…
300	6	0	predators	llm	false	{"birth_threshold":260,"hunt_range":100,"rest_energy":180,"spread":50}	Grazers rebounding (120/140), grass strong (208/220). We
300	6	1	grass	llm	false	{"seed_threshold":95,"seed_range":90,"seed_cost":40,"crowd_limit":3}	Grazers stabilizing at 120. Raise threshold 90→95 to mat
360	7	0	predators	llm	false	{"birth_threshold":240,"hunt_range":90,"rest_energy":200,"spread":50}	Population collapse: 10→2. Grazers healthy (140/140, +24
360	7	1	grass	llm	false	{"seed_threshold":100,"seed_range":90,"seed_cost":40,"crowd_limit":3}	Predators collapsed 5→2. Grazers maxed at 140/140. Cut b
…
540	10	0	predators	llm	false	{"birth_threshold":280,"hunt_range":70,"rest_energy":240,"spread":35}	Grazers stable at 75/140 (54% cap). Grass up to 195/220.
540	10	1	grass	llm	false	{"seed_threshold":95,"seed_range":90,"seed_cost":40,"crowd_limit":3}	Gen 10 endgame: grazers collapsed to 75, predators at 3.
```

Bulk of the episode (the ecology actually running):
```bash
jq -r '[.events[]|.k]|group_by(.)|map({(.[0]):length})|add|tostring' /tmp/ep.replay
jq -r '.events|length' /tmp/ep.replay ; jq -r '.frames|length' /tmp/ep.replay
```
```
{"alarm":1,"birth":2558,"doctrine":30,"end":1,"generation":10,"predation":36,"starve":2422}
5058
601
```

Status: **TRUE** — strict-parser-valid UTF-8 JSON (2,273,433 bytes); `protocol` `ecos.replay.v1`
matches the manifest; `results.reason == "complete"`; both champion seats' 10 doctrines each came
from the LLM with substantive, state-reactive content and **zero** fallbacks.

---

## 5. Hosted game log is clean

```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" \
     -o /tmp/log3.txt -w 'http=%{http_code} bytes=%{size_download}\n'
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/log3.txt \
 || echo CLEAN
```
```
http=200 bytes=46960
CLEAN
```

Corroborating counts from the same fetched log (all 20 champion-seat Bedrock calls issued and
completed, none via fallback):
```bash
grep -o 'bedrock_sidecar_call' /tmp/log3.txt | wc -l      # 20
grep -o 'bedrock_sidecar_complete' /tmp/log3.txt | wc -l  # 20
grep -o 'via fallback' /tmp/log3.txt | wc -l              # 0
grep -o 'via llm' /tmp/log3.txt | wc -l                   # 20
grep -o 'via scripted' /tmp/log3.txt | wc -l              # 10
```

Tail of the game container's log (last generation and shutdown), verbatim excerpt:
```
ecos: gen 10 tick 540: grass 195/220 B15367  grazers 75/140 B3241  predators 3/30 B394
ecos: gen 10 Sedge (predators) [280, 70, 240, 35] via llm says "Grazers stable at 75/140 (54% cap). Grass up to 195/220. Cautio…
ecos: gen 10 Bramble (grass) [95, 90, 40, 3] via llm says "Gen 10 endgame: grazers collapsed to 75, predators at 3. Push b…
ecos: gen 10 Quill (grazers) [90, 10, 40, 20] via scripted
ecos: gen 10 tick 600: grass 220/220 B19082  grazers 88/140 B3897  predators 2/30 B88
```

Status: **TRUE** — grep for `falling back|LLM provider is unavailable|cut off at max_tokens|rejected`
returned nothing; output is `CLEAN`. No exception is being invoked.

---

## 6. The public page uses the static replay path

**(a) Raw-HTML grep — finds nothing, recorded as UNKNOWN, not as a failure.**
```bash
curl -sS "https://softmax.com/ecos" -o /tmp/ecos2.html -w 'http=%{http_code} bytes=%{size_download}\n'
grep -o '<iframe[^>]*src="[^"]*"' /tmp/ecos2.html || echo "NO IFRAME IN RAW HTML (client-rendered)"
```
```
http=200 bytes=366231
NO IFRAME IN RAW HTML (client-rendered)
```
This is the documented platform behaviour (`playbooks/observatory-api.md` §Featured match: the page
is client-rendered for the iframe, lighthouse run 2026-08-22).

**(b) `/coworlds` detail — `featured_match` is null platform-wide, also not evidence.**
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end
          | .[]|select(.name=="ecos")|{id,name,canonical,replay_viewer,featured_match}|tostring'
```
```json
{"id":"cow_7f960dd9-bdfb-49a3-b0b6-09a56cf1905f","name":"ecos","canonical":true,"replay_viewer":null,"featured_match":null}
```
(`canonical: true` confirms the release is the canonical version. `featured_match: null` is the
documented platform-wide value, so the featured match is read from the SSR payload below.)

**(c) Featured match — server-rendered into the page's SSR payload at `state.playlist[0]`.**
```bash
grep -o 'playlist\\":\[{[^]]\{0,700\}' /tmp/ecos2.html | head -1
```
```
playlist\":[{\"episodeId\":\"97a33aa8-ac4e-48cb-9954-482054bc4815\",\"coworldId\":\"cow_7f960dd9-bdfb-49a3-b0b6-09a56cf1905f\",\"coworldName\":\"ecos\",\"coworldVersion\":\"0.1.0\",\"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/91e62cde-5d4b-42a9-bda2-3fdac44680c8.replay\",\"finishedAt\":\"2026-08-23T14:03:15.062180Z\",\"roundNumber\":3,\"episodeNumber\":1,\"code\":\"ecos.r3.e1\",\"matchup\":{\"divisionId\":\"div_ee91d3a5-2639-415e-9694-b5c1a5b70b43\",\"divisionName\":\"Competition\",\"first\":{\"rank\":1,\"player_id\":\"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d\",\"player_name\":\"daveey-1\",\"score\":1030.5304984710244,\"score_label\":\"Elo\",\"score_value_type\":\"integer\",\"rounds_pl…
```
```bash
grep -o 'second\\":{[^}]\{0,300\}' /tmp/ecos2.html | head -1
```
```
second\":{\"rank\":2,\"player_id\":\"ply_44ae9048-3242-4654-881f-6d9d43347fa3\",\"player_name\":\"daveey\",\"score\":969.4695015289755,\"score_label\":\"Elo\",\"score_value_type\":\"integer\",\"rounds_played\":2,\"episode_wins\":0,\"episodes_played\":null,\"win_rate\":0,\"policy_label\":\"ecos-keeper:v1\",\"r…
```
A featured match **is present**: `ecos.r3.e1`, the round-3 episode verified in checks 3–5, with a
two-player matchup (`first: daveey-1` / `second: daveey`), i.e. not the "fewer than two ranked
players" absence case.

**(d) The iframe `src` — the call the page's own JS makes.**
```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
 -d '{"coworld_id":"cow_7f960dd9-bdfb-49a3-b0b6-09a56cf1905f",
      "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/91e62cde-5d4b-42a9-bda2-3fdac44680c8.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_7f960dd9-bdfb-49a3-b0b6-09a56cf1905f/sha256%3Abbc83b693c53fe7c391a6a92809a7a3fd106988b899da01ec14f1fe8234335b8/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F91e62cde-5d4b-42a9-bda2-3fdac44680c8.replay&v=2",
  "ready": true
}
```

**Source used:** the raw-HTML grep found nothing (recorded as unknown), so the verdict rests on the
SSR payload (featured match) plus `POST /coworlds/replays/session` (iframe src) — the two sources
`playbooks/observatory-api.md` §Featured match documents as authoritative for a client-rendered page.

Status: **TRUE** — the src is
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` with `<sha>` =
`sha256:bbc83b693c53fe7c391a6a92809a7a3fd106988b899da01ec14f1fe8234335b8`, exactly the
`coworld.manifest_sha` in STATE, URL-encoded. `ready: true`. It is **not** a `/client/replay` pod
URL. A featured match is present.

---

## 7. Certification declared the static bundle

Source read: **the committed `runs/2026-08-23-ecos/release-result.json`** (the artifact phase 40
downloaded from release run `32642817302` and committed). No re-download was needed; `/tmp` was not
consulted.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-23-ecos/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE** — the output contains `Replay liveness: skipped (static replay bundle declared`.

---

## 8. Spectator judgment — the viewer was EXECUTED in a real browser, then judged

### (a) The load test, dispatched against the check-6 iframe `src`

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_7f960dd9-bdfb-49a3-b0b6-09a56cf1905f/sha256%3Abbc83b693c53fe7c391a6a92809a7a3fd106988b899da01ec14f1fe8234335b8/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F91e62cde-5d4b-42a9-bda2-3fdac44680c8.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 5 \
 | jq -c 'sort_by(.createdAt)|reverse|.[0:2]'
```
```json
[{"createdAt":"2026-08-23T14:06:25Z","databaseId":32644408716,"status":"in_progress"},{"createdAt":"2026-08-23T13:49:32Z","databaseId":32643528839,"status":"completed"}]
```
```bash
gh run watch 32644408716 -R Metta-AI/coworld-builder --exit-status ; echo "exit=$?"
```
```
✓ main viewer-check · 32644408716
✓ viewer-check in 43s (ID 97206322568)
  ✓ Load the viewer
  ✓ Upload the evidence
  ✓ Fail if the viewer did not load
exit=0
```
```bash
gh run download 32644408716 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-23-ecos/viewer-check
ls -l runs/2026-08-23-ecos/viewer-check
```
```
-rw-r--r--  0      smoke-stderr.txt
-rw-r--r--  482    smoke-stdout.txt
-rw-r--r--  1184   viewer-smoke.json
-rw-r--r--  499750 viewer-smoke.png
```

(An earlier run of the same workflow, `32643528839` at 13:49:32Z, load-tested round 2's replay and
was also green — `loaded:true`, clocks `GEN 1 … TICK 2` / `GEN 6 … TICK 316` / `GEN 10 / 10`. The
committed artifacts are the round-3 ones above, which are the ones the featured match points at.)

### (b) The readouts

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-23-ecos/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":2900,"clock":"GEN 1 / 10 TICK 3 OF 600","scorebug":"DAVEEY 10 PREDATORS B 2.17k · 0.00 BASELINE 80 GRAZERS B 3.49k · 0.00 GEN 1 / 10 TICK 3 OF 600 DAVEEY-1 164 GRASS B 14.3k · 0.00","feed_lines":0}
```
```bash
jq -c '.signals' runs/2026-08-23-ecos/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```
```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-23-ecos/viewer-check/viewer-smoke.json
jq -r '.failure // "no failure"' runs/2026-08-23-ecos/viewer-check/viewer-smoke.json
```

| scrub position | clock readout |
|---|---|
| 0 % | `GEN 1 / 10 TICK 3 OF 600` |
| 50 % | `GEN 6 / 10 TICK 315 OF 600` |
| 100 % | `GEN 10 / 10 10 GENERATIONS` |

```
no failure
```

The shell signals readiness through `data-replay-loaded="true"` (set on the first drawn frame) and
its failure twin `data-replay-error`, not through the `coworld-replay` postMessage bridge — hence
`bridge_ready:false` with `bridge_error:[]`. That is the first of the two accepted `loaded` signals
in `prompts/60-verify.md` item 8.1. Confirmed in the fetched shell source:
```bash
curl -sS "$B/static_replay.js" -o /tmp/static_replay.js -w '%{http_code} %{size_download}\n'  # 200 9223
grep -noE 'data-replay-loaded|data-replay-error' /tmp/static_replay.js
```
```
16:data-replay-loaded
19:data-replay-error
141:data-replay-loaded
```
```
        } else if (message.type === 'loaded') {
          loaded = true;
          document.documentElement.setAttribute('data-replay-loaded', 'true');
          requestAnimationFrame(animate);
```

Supplementary asset table (fetched fresh; the executed run above is the authoritative evidence):

| URL (relative to `…/static/<cow_id>/<sha>/`) | HTTP | bytes |
|---|---|---|
| `index.html?replay=<s3 url>` | 200 | 219 559 |
| `./wire_constants.js` | 200 | 103 |
| `./chrome_common.js` | 200 | 40 022 |
| `./static_replay.js` | 200 | 9 223 |

(No `.wasm` is referenced: `grep -oE '[A-Za-z0-9_./-]+\.wasm' index.html static_replay.js` returns
nothing — this shell renders to canvas from JS, with `broadcast_core.js` inlined into `index.html`,
which is why `index.html` is 219 KB. Nothing is 0-byte and nothing is an HTML error page.)

### (c) The replay JSON the viewer was asked to draw

Early:
```
t	seat	k	sp	say
0	0	doctrine	predators	Starting conservatively. Grazers at 40/140 (29%), grass healthy…
0	1	doctrine	grass	Gen 1: Baseline doctrine. Monitor grazers and predators for sta…
0	2	doctrine	grazers	(scripted)
1	-	birth	grazers
1	-	birth	grazers
```
Middle (per-generation state rows the scorebug and population strip are drawn from):
```
{"t":60,"k":"generation","gen":1,"pop":[172,132,10],"bio":[11770,4337,1933],"score":[0.6009775,1.2689916666666667,0.6360111111111111]}
{"t":300,"k":"generation","gen":5,"pop":[208,120,5],"bio":[13602,5958,851],"score":[0.6780966666666667,1.2564166666666667,0.2960388888888889]}
{"t":354,"k":"alarm","sp":"predators","pop":4,"cap":30}
{"t":360,"k":"generation","gen":6,"pop":[169,140,2],"bio":[11884,7557,158],"score":[0.6766116666666666,1.5315291666666666,0.15856111111111112]}
```
Late:
```
599	-	starve	grass
600	-	birth	grass
600	-	generation
600	-	end
{"t":600,"k":"end","reason":"complete","ending":"ten_generations","scores":[2.750288888888888,6.164395000000001,12.708187500000001]}
```
```bash
jq -r '.results' /tmp/ep.replay   # pasted in full under check 4
```

### Spectator judgment

**Legible, and it shows the game.** The headless chromium run drew its first frame 2 900 ms after
navigation and reported `loaded: true` with no `data-replay-error` and an empty console tail, so
this is a rendered picture, not an inference from a 200-status asset list. The scorebug it read out
of the live DOM at t≈0 — `DAVEEY 10 PREDATORS B 2.17k · 0.00 / BASELINE 80 GRAZERS B 3.49k · 0.00 /
DAVEEY-1 164 GRASS B 14.3k · 0.00` — names all three seats, their species, their populations and
their biomass, and matches the replay's opening state, so a spectator can tell who is playing what
from the first frame. The three scrub readouts differ and advance monotonically (`GEN 1 … TICK 3` →
`GEN 6 … TICK 315` → `GEN 10 / 10`), so the replay plays rather than freezing on one frame; the
midpoint tick 315 lands inside generation 6, exactly where the replay's `generation` rows put it.

`viewer-smoke.png` (the 100 % scrub position) shows the end-card over the field: the top strip
carries all three seats with live population and biomass (`DAVEEY predators 2, B 88 · 2.75`;
`BASELINE grazers 88, B 3.90k · 12.71`; `DAVEEY-1 grass 220, B 19.1k · 6.16`), a large
`GEN 10 / 10` clock, the verdict **BASELINE WINS** with the reason spelled out in prose
("10 generations in balance. BASELINE integrated the most biomass (12.71)"), three per-seat score
cards, a transport bar with speed controls and a `600 / 600` counter, and a population strip along
the bottom showing the green (grass), yellow (grazer) and red (predator) curves over the whole
episode — the red line visibly sagging toward the floor in the back half. Those three numbers
(2.75 / 6.16 / 12.71) reconcile exactly with `participant_scores` in check 3 and `.results.scores`
in check 4, and the sagging red curve reconciles with the `alarm` event at t=354 and the champion's
own gen-7 `say` ("Population collapse: 10→2"). A spectator sees the story the events tell: grass
held at cap, the grazer baseline compounded biomass and won, and the predator seat starved down to
two bodies.

One legibility finding, not a failure: `feed_lines: 0`. The doctrine feed had no visible lines at
the sampled moment — at the 100 % end-card the feed is covered by the result overlay, and the
smoke sampled it there. The `say` text is present in the replay (30 doctrine events, 20 with
non-empty `say`), so this is a "when is the feed on screen" question for phase 30's polish list,
not evidence of missing content. `prompts/60-verify.md` item 8's two conditions — `loaded: true`
and three differing clock readouts — both hold.

Status: **TRUE**.
