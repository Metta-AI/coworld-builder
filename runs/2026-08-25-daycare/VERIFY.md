# VERIFY — daycare   (2026-08-25T19:35Z)

Verdict: **all-true (8 / 8)**

Common setup for every fetch below (header **names** only; values never printed):

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_b3316d91-3a90-41b6-9370-4c6644e51b9c
D=div_6fc85068-9784-4bdc-905b-c78b33c106d3
COW=cow_5b944b41-3f2f-4f84-a96b-c484811d7d55
```

All evidence below was fetched fresh in this session (2026-08-25 19:23Z–19:33Z), except the two
documented exceptions: check 7 (reads the committed `release-result.json` from phase 40) and
check 8 (reads the artifact of the `viewer-check.yml` run **dispatched in this session**,
run id 32889498154).

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" -o /tmp/rounds.json
jq -r '.entries[]|[.round_number,.id,.status,(.completed_at//"-"),(.error//"-")]|@tsv' /tmp/rounds.json
jq -r '[.entries[]|select(.status=="completed")]|length' /tmp/rounds.json
```

```
19	round_617d7b6f-b874-4496-a84d-b255657807cb	pending	-	-
18	round_fb6e0387-fffd-4ab6-81ca-28012d182468	completed	2026-08-25T19:15:42.023231Z	-
17	round_019a28d6-2f22-451c-bea0-14c42604b2b8	completed	2026-08-25T18:53:49.126041Z	-
16	round_1626c21a-8504-4a46-a9da-bb88044e8c55	completed	2026-08-25T18:37:56.230714Z	-
15	round_2b95ed71-f20c-4f09-8a77-5fdd0d825bb9	completed	2026-08-25T18:23:29.981484Z	-
14	round_c0af7529-3de0-40f3-a3a7-818a53e87654	completed	2026-08-25T18:06:43.610646Z	-
13	round_e329b797-bd9a-498d-b311-17944de986ac	completed	2026-08-25T17:52:13.597524Z	-
12	round_755db822-3b9c-401c-8f70-f5517da560a5	completed	2026-08-25T17:39:47.284734Z	-
11	round_49959d86-80a0-45c6-a05c-0cab348afb07	completed	2026-08-25T17:23:53.941985Z	-
10	round_f32f61ed-bbbd-4065-9492-14e1c097bf7e	completed	2026-08-25T17:06:38.652394Z	-
9	round_f0d17fb8-5cc5-430d-a778-45992b583bfa	completed	2026-08-25T16:52:16.689950Z	-
8	round_5b1021e5-d6ec-4086-9e56-cd65dd6a48ab	completed	2026-08-25T16:36:42.834654Z	-
7	round_a148538b-ec56-4205-99a1-9d2b76785033	completed	2026-08-25T16:23:11.862433Z	-
6	round_e0611a6c-2674-4d93-8252-40ff9eb669d3	completed	2026-08-25T16:06:36.193030Z	-
5	round_3927be2a-6e97-400b-b2b8-7275472b58cd	completed	2026-08-25T15:51:41.610118Z	-
4	round_d0882b4d-443f-4e7d-a577-94127d61760d	completed	2026-08-25T15:36:53.060015Z	-
3	round_feb1d55c-bf7c-4535-abdf-eb9a4ae6b637	completed	2026-08-25T15:21:34.125795Z	-
2	round_34cae2b4-eaed-46e7-9bd6-0b5a7697d398	completed	2026-08-25T15:06:53.403431Z	-
1	round_868d2491-3434-4589-abd7-3403966f0305	failed	2026-08-25T15:03:01.710139Z	Temporal RoundWorkflow failed before settling the round.
```

```
17          # count of status=="completed" in the window
```

The one failed round is round 1; its `error` verbatim: `Temporal RoundWorkflow failed before
settling the round.` — the pre-filler auto-trigger race recorded in `log.md:49`. Fillers were
registered at 2026-08-25T15:04:15Z (`log.md:48`, `fillers POST 200: caretaker+stubborn`), i.e.
**before round 2**. The league object returned in this same fetch confirms the fillers are
attached now:

```json
"filler_policy_version_ids": [
  "f6155ca7-d319-4639-936c-ead67d116419",
  "085a01ae-7273-4fce-ab52-15a4e1b262cd"
]
```

Status: **TRUE** — 17 completed rounds, all with `round_number ≥ 2` (rounds 2…18), all after the
filler registration. Requirement is ≥ 2.

---

## 2. Both champions ranked; fillers absent or Baseline — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq .
```

```json
[
  {"rank":1,"player_id":"ply_ded11f40-3e30-4921-b019-f7f6bc3e9c83","player_name":"richard",
   "score":1189.0438534624402,"score_label":"Elo","rounds_played":14,"episode_wins":32.0,
   "win_rate":0.7619047619047619,"policy_label":"co-gas-daycare-caretaker-richard:v1"},
  {"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
   "score":1009.5005277328474,"score_label":"Elo","rounds_played":17,"episode_wins":22.0,
   "win_rate":0.4888888888888889,"policy_label":"daycare-provider:v1"},
  {"rank":3,"player_id":"ply_18302115-9fc9-482d-a2f3-f4c592bf9e57","player_name":"relh",
   "score":917.7641216693766,"score_label":"Elo","rounds_played":14,"episode_wins":17.0,
   "win_rate":0.40476190476190477,"policy_label":"co-gas-daycare-caretaker-relhalpha:v1"},
  {"rank":4,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
   "score":883.6914971353357,"score_label":"Elo","rounds_played":17,"episode_wins":12.0,
   "win_rate":0.26666666666666666,"policy_label":"daycare-attentive:v1"}
]
```

- `daveey` → `daycare-attentive:v1`, `rounds_played` 17 ≥ 1. ✔
- `daveey-1` → `daycare-provider:v1`, `rounds_played` 17 ≥ 1. ✔
- This run's fillers (`daycare-caretaker:v1` = `f6155ca7-…`, `daycare-stubborn:v1` =
  `085a01ae-…`) are **absent** from the leaderboard. ✔

Observation (not a failure): ranks 1 and 3 are **third-party submissions** by other Softmax
players (`richard`, `relh`) whose policy names happen to contain "daycare-caretaker". They are
distinct policy versions (`ea39dd8b-d30a-4613-abb6-4de026d96ecb`,
`ae15fa79-5c71-4978-9604-5ba78ce24e4e` — see the `entrant_attributions` in check 1's rounds body)
from this run's filler ids, they are owned by other player ids, and their presence is why the
ladder seats four real players and no fillers.

Status: **TRUE**.

---

## 3. Latest round's episode request completed with a replay — **TRUE**

Latest completed round = `round_fb6e0387-fffd-4ab6-81ca-28012d182468` (round_number 18).

```bash
R=round_fb6e0387-fffd-4ab6-81ca-28012d182468
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}" -o /tmp/ereqs.json
jq -r '.entries[]|[.id,.status,(.replay_url//"-")]|@tsv' /tmp/ereqs.json
```

```
ereq_de91da82-02ef-46d5-a173-8ea5adf6ee9e	completed	https://softmax-public.s3.amazonaws.com/replays/84f3b7af-b641-4c59-a823-a7700fc5d5b2.replay
ereq_b6335e24-4576-4928-a4eb-5ce358442025	completed	https://softmax-public.s3.amazonaws.com/replays/f6c260b8-8a4f-4dde-a2a0-8b6d2c889d0e.replay
ereq_78f48587-25f3-4d2c-bc5c-003ae0a52977	completed	https://softmax-public.s3.amazonaws.com/replays/832718ed-bc17-4b7f-824f-49c937ad6bd3.replay
ereq_ea597d44-bfb3-4f45-9215-b29e276691c1	completed	https://softmax-public.s3.amazonaws.com/replays/a2fa12e9-0699-4830-a128-42031180c10e.replay
ereq_3858ce5f-b768-4a3b-8afe-21a4c2dc2fae	completed	https://softmax-public.s3.amazonaws.com/replays/c03b5947-ede2-4abd-ba96-a2792ac66eaa.replay
ereq_47cdafdd-cf6a-462a-b83f-c9513bde00a3	completed	https://softmax-public.s3.amazonaws.com/replays/493c7af6-1000-41c4-a6bf-74f167759cf5.replay
```

All 6 episode requests of round 18 are `completed`, each with a non-null `replay_url`. Round 18
is a 4-player round robin, so the champions meet in one of the six; that episode
(`ereq_78f48587-…`) is the one carried into checks 4 and 5.

```bash
curl -sS "$BASE/episode-requests/ereq_78f48587-25f3-4d2c-bc5c-003ae0a52977" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```

```json
{"status":"completed",
 "replay_url":"https://softmax-public.s3.amazonaws.com/replays/832718ed-bc17-4b7f-824f-49c937ad6bd3.replay",
 "participants":[
   {"position":0,"kind":"policy","policy_version_id":"4908ae78-ffe9-4f04-8f06-3f707bd427cc",
    "policy_name":"daycare-attentive","version":1,
    "player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
    "is_filler":false,"is_seed":false},
   {"position":1,"kind":"policy","policy_version_id":"542b3475-4d8e-4367-a86f-b4a3d69a9a87",
    "policy_name":"daycare-provider","version":1,
    "player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
    "is_filler":false,"is_seed":false}],
 "participant_scores":[{"position":0,"score":54.0},{"position":1,"score":54.0}]}
```

And `entries[0]` (the episode the public page features, used in checks 6 and 8):

```json
{"status":"completed",
 "replay_url":"https://softmax-public.s3.amazonaws.com/replays/84f3b7af-b641-4c59-a823-a7700fc5d5b2.replay",
 "participants":[
   {"position":0,"policy_name":"daycare-provider","version":1,"player_name":"daveey-1",
    "policy_version_id":"542b3475-4d8e-4367-a86f-b4a3d69a9a87","is_filler":false},
   {"position":1,"policy_name":"co-gas-daycare-caretaker-richard","version":1,
    "player_name":"richard","policy_version_id":"ea39dd8b-d30a-4613-abb6-4de026d96ecb",
    "is_filler":false}],
 "participant_scores":[{"position":0,"score":117.0},{"position":1,"score":117.0}]}
```

Status: **TRUE** — status `completed`, non-null `replay_url`, participants name `daveey` and
`daveey-1`. No `Baseline (N)` seats appear because the division has four real entrants, so the
scheduler never needed a filler this round (`insufficient_players: filler_policy` is unused when
players suffice).

---

## 4. Replay bytes are valid and show the game — **TRUE**

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/832718ed-bc17-4b7f-824f-49c937ad6bd3.replay" \
     -o /tmp/ep.replay -w "http=%{http_code} bytes=%{size_download}\n"
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .results.reason' /tmp/ep.replay
jq -r 'keys' /tmp/ep.replay
```

```
http=200 bytes=157139
strict UTF-8 JSON: ok
daycare.replay.v1
complete
["beats","colors","config","events","frames","game","gameVersion","names","policyNames",
 "protocol","results","roles","secret","seed","series"]
```

Protocol match: the fetched `protocol` is `daycare.replay.v1`, the exact string the design
declares for the replay file (`design.md:656` "### The replay file (`daycare.replay.v1`)" and the
cert fixture rule at `design.md:1069` `protocol == "daycare.replay.v1"`). The published manifest
(fetched in check 6 from `GET /coworlds`) declares `game.protocols.player` =
`daycare.player.v1 -- JSON text frames over the websocket…` and the static replay route; it does
not carry a separate replay-protocol string, so the manifest-side contract checked here is the
player protocol + static route, and the replay-file protocol is checked against the design's
declared value. Both match.

`results` verbatim:

```json
{"names":["daveey","daveey-1"],"aliases":["Alder","Bramble"],"roles":["parent","child"],
 "scores":[54,54],"win":[true,true],"preference":"apple","child_ate":[18,0],"delivered":[17,0],
 "wasted":[0,0],"reaches":[0,365],"guess_turns_correct":15,"turns":15,"par":30,
 "reason":"complete","ending":"turn_limit"}
```

`results.reason == "complete"` — the design's first-class end condition (`design.md:279-286`:
legal reasons are `complete`, `deadline`, `forfeit`); no exception needed.

Champion decisions are LLM, not scripted, not fallbacks:

```bash
jq -r '[.events[]|.k]|group_by(.)|map("\(.[0]): \(length)")|.[]' /tmp/ep.replay
jq -r '[.events[]|select(.k=="order")|.source]|group_by(.)|map("\(.[0]): \(length)")|.[]' /tmp/ep.replay
jq -r '[.events[]|select(.fallback==true)]|length' /tmp/ep.replay
jq -r '[.events[]|select(.k=="order")|(.notes|length)]|{n:length,min:min,max:max,avg:(add/length)}' /tmp/ep.replay
```

```
drop: 34   eat: 18   end: 1   guess: 1   order: 30   pick: 35
reach: 53  ripen: 42  rot: 16  turn: 15
--- sources ---
llm: 30
--- fallback flags ---
0
--- notes length (order events) ---
{"n":30,"min":137,"max":240,"avg":219.8}
```

30 of 30 decisions `source: "llm"`; **0** fallbacks; note bodies average 220 chars.
Three verbatim decisions (early / middle / final):

```json
{"t":0,"seat":0,"turn":1,"role":"parent","job":"provide","f":"apple","guess":"apple","source":"llm",
 "notes":"Turn 1: Child at (11,4), I'm at (12,9). All tall trees ripen in 2 ticks. Shrubs S1(apple) and S2(banana) already ripe. Need to infer preference from child's behavior. Will provide apple to start and w…","latencyMs":4798}
{"t":420,"seat":0,"turn":8,"role":"parent","job":"provide","f":"apple","guess":"apple","source":"llm",
 "notes":"Turn 8: Child ate 7 apples last turn from my delivery. 21/30 score means 7×3=21 (perfect). Ground apple at (5,2) nearby. Continue apple provision—this strategy is working. Child refuses banana entirel…","latencyMs":3150}
{"t":840,"seat":1,"turn":15,"role":"child","job":"beg","f":"apple","guess":"","source":"llm",
 "notes":"Turn 15/15 (final): Parent is adjacent at (8,1). Standing in beg posture to signal readiness. If parent drops apple here, eat for +3 and finish at 57. If not, show under T6 as fallback, but parent's 1…","latencyMs":2931}
```

Status: **TRUE** — strict-parser-valid UTF-8 JSON, protocol matches, `reason: "complete"`, and
the seats are doing the thing the game is about: the child signals by reaching for tall apple
trees (`reaches: [0,365]`), the parent infers "apple" and delivers (17 delivered, 18 eaten, 0
wasted), and the parent's hidden guess is right on 15 of 15 turns.

---

## 5. Hosted game log is clean — **TRUE**

```bash
E=ereq_78f48587-25f3-4d2c-bc5c-003ae0a52977
curl -sS "$BASE/episode-requests/$E/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs.raw \
     -w "http=%{http_code} bytes=%{size_download}\n"
# decode the python b'…' reprs first (playbook §10), THEN grep
python3 -c "…ast.literal_eval per line…" > /tmp/logs.txt
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.txt || echo CLEAN
```

```
http=200 bytes=64983
decoded chars: 64801  lines: 181
HITS: 0
CLEAN
```

Containers present in the decoded log: `coworld-init-config`, `bedrock-sidecar`, `game`, `worker`.
Representative decoded lines (Bedrock sidecar — every call `ok:true`, `status_code:200`,
`error_kind:null`):

```
2026-08-25 19:08:15,810 INFO __main__ bedrock_sidecar_complete {"episode_request_id":"78f48587-…",
 "model":"global.anthropic.claude-haiku-4-5-20251001-v1:0","operation":"InvokeModel","ok":true,
 "status_code":200,"latency_ms":2697.08,"error_kind":null,"error_type":null,"message":null,
 "cache_strategy":"sidecar_v1","cache_decision":"first_sighting"}
```

Game container head and tail:

```
===== container: game =====
daycare: seed not pinned; randomized
daycare: seats=2 turns=15 ticksPerTurn=60 variant=daycare-sparse
daycare: serving on 0.0.0.0:8080
daycare: player slot 0 connected (1/2)
daycare: slot 0 delivered a prompt (1474 chars)
daycare: player slot 1 connected (2/2)
daycare: slot 1 delivered a prompt (1146 chars)
daycare: starting with 2/2 players connected
…
daycare: writing results and replay
daycare: episode complete; serving /healthz and /global for 20s
daycare: shutting down
```

Status: **TRUE** — zero lines match the four forbidden patterns after decoding the byte-string
reprs. No exception invoked.

---

## 6. The public page uses the static replay path — **TRUE**

**Source used: the page's server-rendered SSR payload plus the replay-session call the page's own
JS makes.** The raw-HTML iframe grep found nothing, as the playbook predicts (the iframe is
client-rendered), and `GET /coworlds`'s `featured_match` is null platform-wide — so neither of
those alone is evidence. All three sources are recorded below.

**(a) Raw-HTML grep — negative, i.e. unknown, not a failure:**

```bash
curl -sS "https://softmax.com/daycare" -o /tmp/page.html -w "http=%{http_code} bytes=%{size_download}\n"
grep -o '<iframe[^>]*src="[^"]*"' /tmp/page.html || echo "NO IFRAME IN RAW HTML"
```

```
http=200 bytes=581985
NO IFRAME IN RAW HTML
```

**(b) Coworld detail API — id/canonical confirmed, `featured_match` null (platform-wide):**

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -c 'if type=="array" then . else .entries end|.[]
          |select(.name=="daycare")|{id,name,canonical,replay_viewer,featured_match,manifest_hash,version}'
```

```json
{"id":"cow_5b944b41-3f2f-4f84-a96b-c484811d7d55","name":"daycare","canonical":true,
 "replay_viewer":null,"featured_match":null,
 "manifest_hash":"sha256:e4ba7e35568a601dafc86e9acb5261d20e2779b0bedcad465d026cad1b997f33",
 "version":"0.1.0"}
```

(`/coworlds` returned a **bare array** this run, not `{entries:…}` — the dual-shape jq was needed.)

**(c) The featured match, server-rendered into the page at `state.playlist[0]` — PRESENT:**

```bash
python3 - <<'EOF'   # locate the escaped SSR payload in /tmp/page.html and unescape it
… h.find('playlist\\":[') …
EOF
```

```json
"state":{"leagueId":"league_b3316d91-3a90-41b6-9370-4c6644e51b9c","playlist":[
 {"episodeId":"e12373a7-5dce-4d17-9499-1e9d53298d54",
  "coworldId":"cow_5b944b41-3f2f-4f84-a96b-c484811d7d55","coworldName":"daycare",
  "coworldVersion":"0.1.0",
  "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/84f3b7af-b641-4c59-a823-a7700fc5d5b2.replay",
  "finishedAt":"2026-08-25T19:15:13.069299Z","roundNumber":18,"episodeNumber":6,
  "code":"daycare.r18.e6",
  "matchup":{"divisionId":"div_6fc85068-9784-4bdc-905b-c78b33c106d3","divisionName":"Competition",
   "first":{"rank":1,"player_name":"richard","score":1189.04,"policy_label":"co-gas-daycare-caretaker-richard:v1"},
   "second":{"rank":2,"player_name":"daveey-1","score":1009.50,"policy_label":"daycare-provider:v1"}},
  "inspectUrl":"/observatory/v2?tab=episode-requests&detail=episode-request:ereq_de91da82-02ef-46d5-a173-8ea5adf6ee9e"}]
```

**(d) The iframe `src` the page builds — the replay-session call:**

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" \
  -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_5b944b41-3f2f-4f84-a96b-c484811d7d55",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/84f3b7af-b641-4c59-a823-a7700fc5d5b2.replay"}'
```

```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_5b944b41-3f2f-4f84-a96b-c484811d7d55/sha256%3Ae4ba7e35568a601dafc86e9acb5261d20e2779b0bedcad465d026cad1b997f33/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F84f3b7af-b641-4c59-a823-a7700fc5d5b2.replay&v=2",
 "ready":true}
```

The path is `/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`, `<sha>` is
the coworld's manifest hash (`sha256:e4ba7e35…`, URL-encoded), and `ready: true` — static
delivery. **No `/client/replay` pod URL anywhere.**

Status: **TRUE** — featured match present (`daycare.r18.e6`, richard vs daveey-1) and the iframe
`src` is the static bundle path.

---

## 7. Certification declared the static bundle — **TRUE**

Source read: **the committed `runs/2026-08-25-daycare/release-result.json`** (phase 40's artifact
copy; it was already present, so no re-download from run 32862166190 was needed).

```bash
jq -r '.certify.replay_liveness' runs/2026-08-25-daycare/release-result.json
```

```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Status: **TRUE** — the required substring `Replay liveness: skipped (static replay bundle
declared` is present verbatim.

---

## 8. Spectator judgment — the viewer was EXECUTED — **TRUE**

### 8(a) Dispatch and artifact

```bash
SRC="$(jq -r .viewer_url /tmp/session.json)"      # the check-6 iframe src, ?replay= and all
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
# dispatched at 2026-08-25T19:25:37Z; new run found by sorting on createdAt, not "latest"
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml \
   --json databaseId,createdAt,status,conclusion -L 10 | jq -c 'sort_by(.createdAt)|reverse|.[0:4][]'
```

```
{"conclusion":"","createdAt":"2026-08-25T19:25:39Z","databaseId":32889498154,"status":"in_progress"}
{"conclusion":"success","createdAt":"2026-08-25T18:23:14Z","databaseId":32883445468,"status":"completed"}
{"conclusion":"success","createdAt":"2026-08-25T17:05:27Z","databaseId":32875824479,"status":"completed"}
{"conclusion":"success","createdAt":"2026-08-25T15:54:30Z","databaseId":32868690580,"status":"completed"}
```

Run **32889498154** (created 19:25:39Z, 2 s after the dispatch) is this run's.

```bash
gh run watch 32889498154 -R Metta-AI/coworld-builder --exit-status   # exit=0 (green)
gh run download 32889498154 -R Metta-AI/coworld-builder -n viewer-check \
   -D runs/2026-08-25-daycare/viewer-check
ls -la runs/2026-08-25-daycare/viewer-check/
```

```
-rw-r--r-- 1 root root      0  smoke-stderr.txt
-rw-r--r-- 1 root root    528  smoke-stdout.txt
-rw-r--r-- 1 root root   1324  viewer-smoke.json
-rw-r--r-- 1 root root 499642  viewer-smoke.png
```

### 8(b) Readouts, verbatim

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-25-daycare/viewer-check/viewer-smoke.json
```

```json
{"loaded":true,"ms":2690,"clock":"TURN 1 / 15 TICK 0 OF 899","scorebug":"CHILD SCORE 0 BRAMBLE · richard TURN 1 / 15 TICK 0 OF 899 PARENT SCORE 0 ALDER · daveey-1","feed_lines":0}
```

```bash
jq -c '.signals' … ; jq -r '.failure // "no failure"' …
```

```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```
```
no failure
```

Three clock readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | clock text |
|---|---|
| 0 %   | `TURN 1 / 15 TICK 0 OF 899` |
| 50 %  | `TURN 8 / 15 TICK 468 OF 899` |
| 100 % | `FINAL TICK 899 OF 899` |

The three differ, and they differ monotonically (tick 0 → 468 → 899). `canvas_text` reports
`0 drawn, 0 never inside the canvas, 0 ellipsized` — no text overflowed the canvas.

**Item 8 conditions: `loaded: true` ✔ (via `data-replay-loaded="true"`, first frame at 2690 ms;
the postMessage bridge was not used — `bridge_ready:false`, `bridge_error:[]`, which is fine
because the DOM attribute signalled) and the three clock readouts differ ✔.**

### 8(c) What the viewer was asked to draw

The rendered replay is the **featured** episode (`84f3b7af-…`, daveey-1 vs richard, r18.e6) —
the same URL the public page hands its iframe. Fetched fresh for reconciliation:

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/84f3b7af-b641-4c59-a823-a7700fc5d5b2.replay" -o /tmp/feat.replay
jq -e . /tmp/feat.replay >/dev/null && jq -c '{protocol,policyNames,names,roles,results}' /tmp/feat.replay
```

```
http=200 bytes=162483   (strict JSON: ok)
{"protocol":"daycare.replay.v1","policyNames":["daveey-1","richard"],"names":["Alder","Bramble"],
 "roles":["parent","child"],
 "results":{"names":["daveey-1","richard"],"aliases":["Alder","Bramble"],"roles":["parent","child"],
  "scores":[117,117],"win":[true,true],"preference":"banana","child_ate":[0,39],"delivered":[0,37],
  "wasted":[0,0],"reaches":[0,309],"guess_turns_correct":14,"turns":15,"par":30,
  "reason":"complete","ending":"turn_limit"}}
```

Ordered event excerpts (early / middle / late):

```
# early
t=0    seat0 order  "Turn 1 of 15. Delivering apple first per guidance. Child at …"
t=0    -     guess
t=3    seat1 reach  banana
t=9    seat0 pick   apple
t=17   seat1 reach  banana
t=23   -     ripen  banana / apple
# middle
t=222  seat0 drop   banana
t=226  seat1 reach  banana
t=233  seat0 drop   banana
t=240  seat0 order  "Turn 5: Delivered 4 banana by turn 3, child ate 5 total (som…"
# late
t=897  seat1 reach  banana
t=898  seat0 pick   banana
t=899  seat0 drop   banana
t=899  seat1 eat    banana
t=899  -     turn / end
```

Event kinds in the rendered replay: `drop:69 eat:39 end:1 guess:2 order:30 pick:71 reach:55
ripen:53 rot:9 turn:15`. Decision sources: `llm: 15` (seat 0 = daveey-1's `daycare-provider:v1`)
and `scripted: 15` (seat 1 = richard's third-party `co-gas-daycare-caretaker-richard:v1`, a
scripted external submission — not one of this run's policies).

### Spectator judgment

**It is legible, it advances, and it plainly shows the game.** The screenshot
(`runs/2026-08-25-daycare/viewer-check/viewer-smoke.png`, taken at the 100 % scrub position)
shows the finished episode: a top scorebug reading `117 SCORE CHILD` / `PARENT SCORE 117` with
the two-name-space labelling the design asked for — the in-game aliases over the policy owners,
`BRAMBLE · richard` on the left and `ALDER · daveey-1` on the right — and a centre clock reading
`FINAL / TICK 899 OF 899`. Behind the endcard the walled yard is drawn as real pixel art: dark
tall fruit trees with visible fruit, the wall band around the field, and the two labelled cogs
(`BRAMBLE` above `ALDER`) standing adjacent at the top-left where the last banana changed hands —
which is exactly what the replay's last four events record (`t=898 seat0 pick banana`,
`t=899 seat0 drop banana`, `t=899 seat1 eat banana`). Top-right is the spoiler/hunch panel:
`BRAMBLE WANTS 🍌 BANANA · ALDER GUESSES 🍌 BANANA RIGHT · RIGHT 14 / 15 TURNS`, with a per-turn
strip of 15 cells, one red and fourteen green — matching `results.preference: "banana"` and
`guess_turns_correct: 14`. The endcard itself reads `TURN LIMIT — PAR BEATEN`, subtitle `THE PAIR
FED THE CHILD`, then `BRAMBLE WANTED BANANA · ALDER GUESSED RIGHT ON 14 OF 15 TURNS`,
`117 / 30 — PAR BEATEN`, and `39 bananas · 0 apples · 0 wasted · 309 reaches` — every one of those
numbers is exactly the fetched `results` (`scores 117`, `par 30`, `child_ate[1] 39`, `wasted 0`,
`reaches[1] 309`, `ending "turn_limit"`). Two feed lines sit bottom-right (`ALDER · LEFT BANANA
BESIDE THE CHILD`, `BRAMBLE · ATE BANANA +5`), dimmed behind the endcard veil. The picture is not
empty, not frozen (the clock moved tick 0 → 468 → 899 across the three scrubs, so the viewer is
replaying, not screenshotting) and not unreadable.

**It looks like the coworld-ctf starter chrome, verbatim in shape.** The bottom transport strip is
the familiar one — restart, step-back, pause, `+5s`, step-forward, loop, fast-forward, then a
`spoilers` toggle, a state readout (`PAR BEATEN  899 / 899`) and the `1× 2× 3× 4× 8× 16×` speed
ladder — sitting above a full-width scrubber with the momentum/score graph rail (labelled `SCORE`)
and turn tick-marks, with the playhead parked at the right end. Same dark broadcast palette, same
corner pennants, same scorebug/endcard grammar as paintbot/raid/hive. This is not the
cogame-gridlock "different product sharing ids" failure.

Two legibility observations for the coordinator (neither blocks item 8):
1. `feed_lines: 0` in `viewer-smoke.json` while the screenshot clearly shows two feed rows — the
   smoke probe's feed selector does not match this shell's feed element. It is a probe/selector
   mismatch, not a missing feed.
2. `bridge_ready: false` — the viewer signals readiness only via `data-replay-loaded="true"`, not
   through the `coworld-replay` postMessage bridge. Accepted by the check as written; worth
   noting if a future harness relies on the bridge.

Status: **TRUE**.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | TRUE (17 completed, rounds 2–18) |
| 2 | Both champions ranked, fillers absent/Baseline | TRUE (daveey #4, daveey-1 #2, 17 rounds each) |
| 3 | Latest round's episode request completed with replay | TRUE (round 18, 6/6 completed) |
| 4 | Replay bytes valid, protocol matches, shows the game | TRUE (`complete`, 30/30 llm, 0 fallbacks) |
| 5 | Hosted game log clean | TRUE (0 hits after decoding) |
| 6 | Public page uses the static replay path | TRUE (static `/index.html?replay=`, featured match present) |
| 7 | Certification declared the static bundle | TRUE (committed `release-result.json`) |
| 8 | Viewer executed and judged | TRUE (`loaded:true`, ticks 0 → 468 → 899) |

**Verdict: all-true.**
