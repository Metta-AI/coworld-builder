# VERIFY — atari-cabinet   (2026-08-26T21:05Z)

Verdict: **all-true** (8/8)

Coworld `cow_5bc1ce13-b06b-46de-872c-4fe3bb952f95` v0.1.3 · league
`league_20b10705-24f2-4d27-b7a0-31993f6110f7` · division `div_df572e19-916a-43ca-9161-8ee11b7356e8`.

Common preamble for every `curl` below (header **names** only; values never printed):

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_20b10705-24f2-4d27-b7a0-31993f6110f7
D=div_df572e19-916a-43ca-9161-8ee11b7356e8
COW=cow_5bc1ce13-b06b-46de-872c-4fe3bb952f95
```

**Subject of checks 3–8: round 3** (`round_f7537b9e-e761-449e-82b4-79d7fa28c836`,
`ereq_21bff821-d7a9-462b-b8a2-f858c79d6ab0`), the latest completed round at verification time.
See the **Anomaly** section at the foot: round 2 ran 100 % scripted-fallback because the platform's
LLM sidecar was routed to `openrouter.ai`, which returned `402 Payment Required` on every call —
the identical condition the poker run documented earlier the same day. That condition cleared
before round 3, which ran entirely on Bedrock with **zero** fallbacks. Rounds 1 and 3 were both
clean; only round 2 was affected. Every check below was fetched fresh this run (the two documented
exceptions — item 7's committed artifact and item 8's dispatched CI artifact — are named as such).

Polling window opened 20:23:34Z, closed 20:57:20Z (**34 min** of the 75-minute bound).

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

Fillers `atari-cabinet-bulwark:v4` (`40b14bfe-1e07-4bc0-a896-616d97fde018`) and
`atari-cabinet-spinner:v4` (`ac7ff405-66cd-423b-b1e8-215eaf509a8b`) were registered in phase 50
**before the first `trigger-round`** — `runs/2026-08-26-atari-cabinet/log.md` records the filler
`POST` on the line immediately preceding the `unpause`/`trigger-round` line:

```
2026-08-26T20:21:59Z 50 fillers HTTP:200 bulwark:v4=40b14bfe spinner:v4=ac7ff405 (neither champion)
2026-08-26T20:21:59Z 50 unpause HTTP:200; trigger-round HTTP:200; round 1 pending, error=-; both champions in entrant_attributions
```

(Those two lines carry the same batched append timestamp, so the log alone does not resolve
sub-minute ordering against round 1's `created_at` of 20:21:00.442924Z. The check does not depend
on it — see the verdict below.)

The filler set as it stands **now**, read fresh (this read needs `ELEV` even though it is a read,
per `playbooks/observatory-api.md` §6):

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"
```

```json
{"filler_policy_versions":[{"policy_version_id":"40b14bfe-1e07-4bc0-a896-616d97fde018","policy_id":"cdf99a33-28f9-43c1-8232-fdf02a4f5f3a","policy_name":"atari-cabinet-bulwark","version":4,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},{"policy_version_id":"ac7ff405-66cd-423b-b1e8-215eaf509a8b","policy_id":"d2e681af-befe-40cb-bb00-9bd3349f7c97","policy_name":"atari-cabinet-spinner","version":4,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
HTTP:200
```

The rounds list, fetched fresh at 20:57Z:

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq 'if type=="array" then . else .entries end | map({id,round_number,status,error,created_at,completed_at})'
```

```json
[
  {
    "id": "round_f7537b9e-e761-449e-82b4-79d7fa28c836",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-26T20:51:01.267875Z",
    "completed_at": "2026-08-26T20:56:57.398390Z"
  },
  {
    "id": "round_fa521642-bbcc-402b-a373-55a887f3b47c",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-26T20:36:00.888242Z",
    "completed_at": "2026-08-26T20:41:27.388084Z"
  },
  {
    "id": "round_2ae091d2-e784-4986-bc25-4b91927a5e4b",
    "round_number": 1,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-26T20:21:00.442924Z",
    "completed_at": "2026-08-26T20:26:29.552677Z"
  }
]
```

```bash
$ … | jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
3
```

Status: **TRUE**. Three rounds `completed`, **zero** `failed`/`discarded`, every `error` null.

Rounds **2** (`created_at` 20:36:00.888242Z) and **3** (20:51:01.267875Z) were both created
*strictly after* the filler `POST` on every possible reading of its timestamp — including the
latest possible reading, the batched log line's 20:21:59Z. **That alone satisfies "≥ 2 completed
rounds after the fillers were set"**, and the check is recorded TRUE on rounds 2 and 3, without
needing to resolve round 1's ordering.

Round 1 is in fact also after the fillers, on two independent pieces of fetched evidence, but is
not counted here: (a) `playbooks/observatory-api.md` §6 records that *"a `trigger-round` issued
before any filler exists fails instantly with `Temporal RoundWorkflow failed before settling the
round`"* — round 1 settled with `error: null`; and (b) round 1's own episode request seats both
filler version ids with `is_filler: true` and its replay names them `Baseline` / `Baseline (2)`
(pasted in the Anomaly section). Recorded as corroboration, not as the basis of the verdict.

`round_config.entrant_attributions` for both counted rounds, showing the two champions seated
(fillers are added by the scheduler's `insufficient_players: filler_policy` rule and do not appear
as attributed entrants):

```bash
$ … | jq -r 'if type=="array" then . else .entries end | map({round_number, entrants: .round_config.entrant_attributions})'
```

```json
[
  {"round_number": 3, "entrants": [
    {"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player","policy_version_id":"f26bb31b-2575-4223-811d-761964fc3a63","league_policy_membership_id":"lpm_e507b1d2-66f5-40ac-842e-dc4145ddcb8a"},
    {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","subject_type":"player","policy_version_id":"c8a2f178-707d-4055-a25a-3b5ce887fff1","league_policy_membership_id":"lpm_a9fa6849-6dfb-4ac0-8696-485c2d2be777"}]},
  {"round_number": 2, "entrants": [
    {"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player","policy_version_id":"f26bb31b-2575-4223-811d-761964fc3a63","league_policy_membership_id":"lpm_e507b1d2-66f5-40ac-842e-dc4145ddcb8a"},
    {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","subject_type":"player","policy_version_id":"c8a2f178-707d-4055-a25a-3b5ce887fff1","league_policy_membership_id":"lpm_a9fa6849-6dfb-4ac0-8696-485c2d2be777"}]}
]
```

**Polling record** (every entry also appended to `log.md` as `<UTC> heartbeat phase=60`):

```
2026-08-26T20:23:34Z poll#1 completed=0 [{"round_number":1,"status":"pending"}]
2026-08-26T20:28:34Z poll#2 completed=1 [{"round_number":1,"status":"completed"}]
2026-08-26T20:33:34Z poll#3 completed=1 [{"round_number":1,"status":"completed"}]
2026-08-26T20:38:34Z poll#4 completed=1 [{"round_number":2,"status":"pending"},{"round_number":1,"status":"completed"}]
2026-08-26T20:43:35Z poll#5 completed=2 [{"round_number":2,"status":"completed"},{"round_number":1,"status":"completed"}]
2026-08-26T20:47:19Z poll  max_completed=2 [{"round_number":2,"status":"completed"},…]
2026-08-26T20:49:50Z poll  max_completed=2 [{"round_number":2,"status":"completed"},…]
2026-08-26T20:52:20Z poll  max_completed=2 [{"round_number":3,"status":"pending"},…]
2026-08-26T20:54:50Z poll  max_completed=2 [{"round_number":3,"status":"pending"},…]
2026-08-26T20:57:20Z poll  max_completed=3 [{"round_number":3,"status":"completed"},{"round_number":2,"status":"completed"},{"round_number":1,"status":"completed"}]
```

The window was extended past the two-completed-rounds mark on purpose: round 2 tripped check 4/5
(the openrouter 402 anomaly), and `prompts/60-verify.md` check 5 directs the verifier to *"keep
polling inside the 75-minute bound rather than going Blocked"*. Round 3 cleared it.

---

## 2. Both champions ranked, fillers absent — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq .
```

```json
[
  {
    "rank": 1,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 1043.747133633611,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 3,
    "episode_wins": 3.0,
    "episodes_played": null,
    "win_rate": 1.0,
    "policy_label": "atari-cabinet-castellan:v4",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 956.2528663663891,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 3,
    "episode_wins": 0.0,
    "episodes_played": null,
    "win_rate": 0.0,
    "policy_label": "atari-cabinet-gunner:v4",
    "recent_rounds": null
  }
]
```

```bash
$ … | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
1	daveey	atari-cabinet-castellan:v4	1043.747133633611	3	3.0
2	daveey-1	atari-cabinet-gunner:v4	956.2528663663891	3	0.0
```

Status: **TRUE**. The endpoint returns a **bare list** (not `.entries`), as the playbook records.
`daveey` is present with `atari-cabinet-castellan:v4` and `rounds_played: 3`; `daveey-1` is present
with `atari-cabinet-gunner:v4` and `rounds_played: 3`. Both champion policy labels are the LLM
prompt policies from STATE, and each is owned by the right player id. The two fillers
(`atari-cabinet-bulwark:v4`, `atari-cabinet-spinner:v4`) are **absent** from the board entirely —
they are seated as `Baseline` / `Baseline (2)` in the episodes but never ranked. Only two rows, so
no third party is holding a rank.

---

## 3. Latest round's episode request completed with a replay — **TRUE**

```bash
R=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
    | jq -r '(if type=="array" then . else .entries end)|[.[]|select(.status=="completed")]|max_by(.round_number).id')
echo "$R"   # round_f7537b9e-e761-449e-82b4-79d7fa28c836
# NOTE: the flat GET /episode-requests?round_id= route is HTTP 405 since 2026-08-26.
# The nested route is the working one (playbooks/observatory-api.md §9):
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)|map({id,status,created_at})'
```

```json
[{"id":"ereq_21bff821-d7a9-462b-b8a2-f858c79d6ab0","status":"completed","created_at":"2026-08-26T20:51:01.595692Z"}]
```

```bash
EREQ=ereq_21bff821-d7a9-462b-b8a2-f858c79d6ab0
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/3cc40a45-9e9f-4b8f-b919-ae46ba1a15a7.replay",
  "participants": [
    {
      "position": 0, "kind": "policy",
      "policy_version_id": "f26bb31b-2575-4223-811d-761964fc3a63",
      "policy_id": "ea58bab4-7871-4ec2-b00b-adaa6a1435d7",
      "policy_name": "atari-cabinet-castellan", "version": 4,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey", "is_filler": false, "is_seed": false
    },
    {
      "position": 1, "kind": "policy",
      "policy_version_id": "c8a2f178-707d-4055-a25a-3b5ce887fff1",
      "policy_id": "bc161772-5a09-41b4-926e-9147473c5bbf",
      "policy_name": "atari-cabinet-gunner", "version": 4,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
      "player_name": "daveey-1", "is_filler": false, "is_seed": false
    },
    {
      "position": 2, "kind": "policy",
      "policy_version_id": "40b14bfe-1e07-4bc0-a896-616d97fde018",
      "policy_id": "cdf99a33-28f9-43c1-8232-fdf02a4f5f3a",
      "policy_name": "atari-cabinet-bulwark", "version": 4,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey", "is_filler": true, "is_seed": false
    },
    {
      "position": 3, "kind": "policy",
      "policy_version_id": "ac7ff405-66cd-423b-b1e8-215eaf509a8b",
      "policy_id": "d2e681af-befe-40cb-bb00-9bd3349f7c97",
      "policy_name": "atari-cabinet-spinner", "version": 4,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey", "is_filler": true, "is_seed": false
    }
  ],
  "participant_scores": [
    {"position": 0, "score": 50.0},
    {"position": 1, "score": 49.25},
    {"position": 2, "score": 67.25},
    {"position": 3, "score": 86.25}
  ]
}
```

Status: **TRUE**. `status == "completed"`; `replay_url` non-null and points at S3; `participants`
name **`daveey`** (seat 0, `atari-cabinet-castellan:v4`) and **`daveey-1`** (seat 1,
`atari-cabinet-gunner:v4`), both `is_filler: false`, each on the right `player_id`. The two filler
seats carry `is_filler: true` and the two filler version ids from check 1.

*Shape note, not a defect:* this deployment's `participants[]` reports the fillers' raw
`policy_name`/`player_name` with an `is_filler: true` flag rather than the display string
`Baseline (N)`. The `Baseline` / `Baseline (2)` display names the checklist refers to are what the
episode itself renders — they appear verbatim in the replay's `names` array and in the viewer's
scorebug (checks 4 and 8 below). Recorded here so the two readings are not mistaken for a mismatch.

---

## 4. Replay bytes are valid and show the game — **TRUE**

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/3cc40a45-9e9f-4b8f-b919-ae46ba1a15a7.replay" -o /tmp/ep.replay
```

```
HTTP:200 bytes:127994
```

**The `.replay` is the starter's binary `COWLDCAB` container, not JSON** — `jq -e . /tmp/ep.replay`
therefore fails by design, on the first byte:

```bash
$ python3 -c "print(open('/tmp/ep.replay','rb').read()[:24])"
b'COWLDCAB\x01\x00\r\x00atari-cabine'
$ jq -e . /tmp/ep.replay
jq: parse error: Invalid numeric literal at line 1, column 11
```

This is the **documented exception** for this coworld, declared in the design note before release:
`runs/2026-08-26-atari-cabinet/design.md` §"Replay bytes (self-sufficient)" (line 1180 ff.) states
the replay stays the starter's binary `COWLDCAB` format because the static wasm viewer parses
exactly that format, and it specifies the substitute check verbatim at lines 1192–1202 — decode
with the repo's stdlib-only `tools/replay_summary.py`, which emits one **strict-UTF-8 JSON** object,
and assert on that. The design also required CI's `docker-smoke` to set
`SMOKE_REQUIRE_REPLAY_JSON=0`, which it does. Running exactly the substitute the design specifies,
with `tools/replay_summary.py` fetched fresh from the released repo:

```bash
gh api repos/Metta-AI/cogame-atari-cabinet/contents/tools/replay_summary.py --jq '.content' \
 | base64 -d > /tmp/replay_summary.py
python3 /tmp/replay_summary.py /tmp/ep.replay > /tmp/ep.json
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .rom, .results.reason, .results.endRule' /tmp/ep.json
```

```
strict UTF-8 JSON: ok
atari-cabinet/v1
warlords
complete
full_time
```

`protocol` matches the manifest's `atari-cabinet/v1` (design.md line 1201:
*"Require `protocol == "atari-cabinet/v1"`"*). `results.reason` is `complete` — the good ending, not
even the declared-acceptable `deadline`.

**Not-all-fallbacks.** The design's substitute asserts on `.stances[].source` and `.fallbacks`:

```bash
jq -r '[.stances[]|select(.source=="llm")]|length' /tmp/ep.json     # llm-sourced stances
jq -r '.fallbacks' /tmp/ep.json                                      # fallback records
jq -c '.fallbackCauses' /tmp/ep.json
jq -c '.results.llmTurns, .results.fallbackTurns' /tmp/ep.json
```

```
48
0
[]
[24,24,0,0]
[0,0,0,0]
```

**48 of 48** champion-seat decisions (2 LLM seats × 24 turns) came from the LLM. **Zero** fallbacks,
zero fallback causes, `fallbackTurns` all-zero. Not a small minority of fallbacks — *none*.

**Non-trivial, varying content** (a constant stance would fail this check as surely as a fallback):

```bash
jq -r '[.stances[]|select(.source=="llm")|.stance]|unique|@csv'      # "aim","camp","catch","guard"
jq -r '[.stances[]|select(.source=="llm")|.aim_at]|unique|@csv'      # "BLUE","GREEN","RED","YELLOW","none"
jq -r '[.stances[]|select(.source=="llm")|.target_ball]|unique|@csv' # "B1","B2","any"
jq -r '[.stances[]|select(.source=="llm")|.say]|unique|length'       # 48
```

All four stance verbs are used, all four aim targets plus `none`, both balls plus `any`, and all
**48** `say` strings are distinct — no repetition, so nothing is being replayed from a canned table.

**Full `results` document** (written into the replay bytes by the server at game over, so the file
is self-sufficient):

```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],"aliases":["BLUE","RED","GREEN","YELLOW"],
 "cabinets":[1,0,2,3],"policyKinds":["llm","llm","scripted","scripted"],
 "scores":[50.0,49.25,67.25,86.25],"win":[false,false,false,true],"placements":[4,3,2,1],
 "rom":"warlords","startingLives":3,"livesLeft":[2,2,3,3],"concedes":[1,1,0,0],
 "knockouts":[1,1,0,0],"chips":[2,1,1,3],"saves":[28,27,27,39],"catches":[0,0,0,0],
 "bricksLeft":[7,8,7,7],"llmTurns":[24,24,0,0],"fallbackTurns":[0,0,0,0],
 "finalTick":5275,"reason":"complete","endRule":"full_time","seed":410791446}
```

`results.saves` sums to **121** (28+27+27+39), well above the design's `> 0` requirement — the
cabinets are actually deflecting balls, not standing still. `knockouts` and `concedes` are non-zero,
`chips` non-zero for every seat: bricks are being chipped away, which is what Warlords is about.
`scores` match `participant_scores` from check 3 exactly.

Status: **TRUE** on every clause: strict-UTF-8 JSON via the design's declared decoder, `protocol`
matches, `results.reason == "complete"`, and the champion seats' decisions are LLM-sourced,
varied and non-trivial with **zero** fallbacks.

---

## 5. Hosted game log is clean — **TRUE**

```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs.raw
```

```
HTTP:200 bytes:104970
```

The body is python `b'…'` byte-string reprs under `===== container: <name> =====` headers, so it
is decoded per `playbooks/observatory-api.md` §10 (`ast.literal_eval` per repr) **before** grepping —
a line-based grep on the raw bytes badly undercounts:

```bash
python3 /tmp/declog.py /tmp/logs.raw /tmp/logs.txt     # decoded 104581 chars
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.txt || echo CLEAN
```

```
CLEAN
```

Cross-check on the *undecoded* bytes, so the CLEAN cannot be an artefact of the decoder:

```bash
$ grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.raw
0
```

All four containers are present in the decoded log, so nothing was silently missing:

```bash
$ grep -n '===== container' /tmp/logs.txt
1:===== container: coworld-init-config =====
3:===== container: bedrock-sidecar =====
200:===== container: game =====
347:===== container: worker =====
```

Positive evidence that the LLM path actually ran on Bedrock for this episode (rather than being
clean because it never called out):

```bash
$ grep -c 'bedrock-runtime' /tmp/logs.txt
48
$ grep -c 'openrouter.ai' /tmp/logs.txt
0
$ grep -n 'bedrock_sidecar_started' /tmp/logs.txt | head -1
4:2026-08-26 20:51:27,847 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1","has_role_arn":true,"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar","episode_request_id":"21bff821-d7a9-462b-b8a2-f858c79d6ab0","job_request_id":"3cc40a45-9e9f-4b8f-b919-ae46ba1a15a7","role":"game","slot":"game","image_digest":"sha256:8225b38c59fcc3de093bb05f75b735bd91302702b820554f5c66653f68aab48c"}
```

48 Bedrock invocations — exactly the 48 LLM stances counted in check 4 — and zero openrouter calls.

Status: **TRUE**, `CLEAN`, no documented exception needed for round 3. (Round 2 was *not* clean;
see the Anomaly section. Round 3 is the subject of this check and it is clean outright.)

---

## 6. The public page uses the static replay path — **TRUE**

*Source used: **the SSR payload + the replay-session API**, not the raw-HTML grep.* The raw grep
found nothing, which the playbook says to treat as *unknown*, not as a failure:

```bash
curl -sS "https://softmax.com/atari-cabinet" | grep -o '<iframe[^>]*src="[^"]*"'
```

```
(no match — HTTP 200, 611779 bytes; the page is client-rendered for the iframe, as the
 lighthouse run recorded platform-wide)
```

The `/coworlds` detail row, also fetched, is likewise not evidence here — `featured_match` is
`null` platform-wide, exactly as the playbook records:

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)[]|select(.name=="atari-cabinet")|{id,canonical,replay_viewer,featured_match,version}'
```

```json
{"id":"cow_5bc1ce13-b06b-46de-872c-4fe3bb952f95","name":"atari-cabinet","canonical":true,"replay_viewer":null,"featured_match":null,"version":"0.1.3"}
{"id":"cow_f7b1ff1e-325d-49e7-a25f-932433f4e985","name":"atari-cabinet","canonical":false,"replay_viewer":null,"featured_match":null,"version":"0.1.2"}
{"id":"cow_87d7deca-3f56-4094-b075-e9bb08a87c0f","name":"atari-cabinet","canonical":false,"replay_viewer":null,"featured_match":null,"version":"0.1.1"}
{"id":"cow_5d0f332d-785c-41ff-b39f-d063677ad1ee","name":"atari-cabinet","canonical":false,"replay_viewer":null,"featured_match":null,"version":"0.1.0"}
```

(The `canonical: true` row is `cow_5bc1ce13-…` at v0.1.3 — the one STATE records. The three earlier
attempt versions are present but non-canonical.)

**Featured match**, server-rendered into the page's SSR payload at `state.playlist[0]`, extracted
from the same 611 779-byte fetch (JSON-unescaped for readability; the raw escaped text is what the
page carries):

```json
{"episodeId":"63fbcb2f-8afa-4271-a961-e0364aed3a50",
 "coworldId":"cow_5bc1ce13-b06b-46de-872c-4fe3bb952f95",
 "coworldName":"atari-cabinet","coworldVersion":"0.1.3",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/3cc40a45-9e9f-4b8f-b919-ae46ba1a15a7.replay",
 "finishedAt":"2026-08-26T20:56:55.790438Z","roundNumber":3,"episodeNumber":1,
 "code":"atari-cabinet.r3.e1",
 "matchup":{"divisionId":"div_df572e19-916a-43ca-9161-8ee11b7356e8","divisionName":"Competition",
   "first": {"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
             "score":1043.747133633611,"score_label":"MMR","rounds_played":3,"episode_wins":3,
             "win_rate":1,"policy_label":"atari-cabinet-castellan:v4"},
   "second":{"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
             "score":956.2528663663891,"score_label":"MMR","rounds_played":3,"episode_wins":0,
             "win_rate":0,"policy_label":"atari-cabinet-gunner:v4"}},
 "inspectUrl":"/observatory/v2?tab=overview&detail=episode-request:ereq_21bff821-d7a9-462b-b8a2-f858c79d6ab0",
 "outcome":"first"}
```

A featured match **is present** (`playlist` length 1), it is **round 3** — the very episode verified
in checks 3–5 — and its `replayUrl` is byte-identical to check 3's `replay_url`. `inspectUrl` names
`ereq_21bff821-d7a9-462b-b8a2-f858c79d6ab0`, the same episode request. Both champions appear in
`matchup.first`/`matchup.second`, so the "fewer than two ranked players ⇒ no featured match"
failure mode does not apply.

**Iframe `src`**, from the call the page's own JS makes:

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_5bc1ce13-b06b-46de-872c-4fe3bb952f95","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/3cc40a45-9e9f-4b8f-b919-ae46ba1a15a7.replay"}'
```

```
HTTP:200
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_5bc1ce13-b06b-46de-872c-4fe3bb952f95/sha256%3A3749debc4ffe6a196646a5545bd3396a30f170a78f3d284d83ac693cdf572e15/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F3cc40a45-9e9f-4b8f-b919-ae46ba1a15a7.replay&v=2","ready":true}
```

Status: **TRUE**. The path is
`…/v2/coworlds/replays/**static**/<cow_id>/<sha>/index.html?replay=<s3 url>`. It is **not** a
`/client/replay` pod URL. `ready: true` and the path ends `/index.html`, which the playbook records
as the static-delivery signature. `<cow_id>` is `cow_5bc1ce13-b06b-46de-872c-4fe3bb952f95` and
`<sha>` URL-decodes to
`sha256:3749debc4ffe6a196646a5545bd3396a30f170a78f3d284d83ac693cdf572e15`, which equals
`STATE.coworld.manifest_sha` character-for-character (the **manifest hash**, as the playbook
specifies — not the replay-viewer bundle digest, which 404s).

---

## 7. Certification declared the static bundle — **TRUE**

*Source used: **the committed `runs/2026-08-26-atari-cabinet/release-result.json`** — the artifact
phase 40 downloaded and committed (3 992 bytes, present in the run directory). **No re-download**
from release run `33008308526` was needed, and `/tmp` was not consulted.*

```bash
jq -r '.certify.replay_liveness' runs/2026-08-26-atari-cabinet/release-result.json
```

```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

The line contains the required `Replay liveness: skipped (static replay bundle declared` prefix
verbatim. Surrounding certification state from the same file, for context:

```bash
$ jq -r '.certify.ok' runs/2026-08-26-atari-cabinet/release-result.json
true
```

and the transcript tail inside `.certify.output_tail`, which shows all ten steps passing before the
liveness skip:

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

Status: **TRUE**.

*Known-stale field, not a failure:* the same file carries
`hosted_certification: "certifying"`. That string is scraped by the release workflow at upload
time and is stale by design — the settled value is the canonical one, and the live API confirms it:
`/coworlds` (check 6) returns `canonical: true` for `cow_5bc1ce13-…` v0.1.3. Recorded here so a
reader of the raw artifact does not misread it.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

*(a) Dispatch.* The iframe `src` from check 6 was opened in headless chromium by CI. The run was
located by sorting on `createdAt`, **not** by grabbing "the latest run" blind.

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_5bc1ce13-b06b-46de-872c-4fe3bb952f95/sha256%3A3749debc4ffe6a196646a5545bd3396a30f170a78f3d284d83ac693cdf572e15/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F3cc40a45-9e9f-4b8f-b919-ae46ba1a15a7.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90   # dispatched 20:59:09Z
sleep 12
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:4][]|[.databaseId,.createdAt,.status]|@tsv'
```

```
33013149654	2026-08-26T20:59:11Z	in_progress
33004894052	2026-08-26T19:23:30Z	completed
33003808546	2026-08-26T19:11:15Z	completed
32984003113	2026-08-26T15:04:46Z	queued
```

```bash
gh run watch 33013149654 -R Metta-AI/coworld-builder --exit-status   # exit 0
gh run view  33013149654 -R Metta-AI/coworld-builder --json status,conclusion,createdAt
```

```json
{"conclusion":"success","createdAt":"2026-08-26T20:59:11Z","status":"completed"}
```

```bash
gh run download 33013149654 -R Metta-AI/coworld-builder -n viewer-check \
  -D runs/2026-08-26-atari-cabinet/viewer-check
```

```
smoke-stderr.txt        0 bytes
smoke-stdout.txt      629 bytes
viewer-smoke.json    1425 bytes
viewer-smoke.png   411181 bytes
```

**Run id `33013149654`**, dispatched by this verification run at 20:59:09Z. The artifact is at
`runs/2026-08-26-atari-cabinet/viewer-check/` for committing — it is this run's only rendered
evidence and the CI sandbox that produced it is gone by the next heartbeat. The `url` field inside
`viewer-smoke.json` confirms it rendered the round-3 replay
`3cc40a45-9e9f-4b8f-b919-ae46ba1a15a7`, i.e. the same episode as checks 3–6.

*(b) Readouts, verbatim.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-26-atari-cabinet/viewer-check/viewer-smoke.json
```

```json
{"loaded":true,"ms":2764,"clock":"2:00 TIME LEFT WARLORDS · TURN 1/24","scorebug":"RED DAVEEY-1 SCORE 60.00 GREEN BASELINE SCORE 60.00 2:00 TIME LEFT WARLORDS · TURN 1/24 BLUE DAVEEY SCORE 60.00 YELLOW BASELINE (2) SCORE 60.00","feed_lines":0}
```

```bash
jq -c '.signals' runs/2026-08-26-atari-cabinet/viewer-check/viewer-smoke.json
```

```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/2026-08-26-atari-cabinet/viewer-check/viewer-smoke.json
```

```
no failure
```

```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-26-atari-cabinet/viewer-check/viewer-smoke.json
```

**The three clock readouts:**

| scrub position | clock |
|---|---|
| 0 %   | `2:00 TIME LEFT WARLORDS · TURN 1/24` |
| 50 %  | `0:59 TIME LEFT WARLORDS · TURN 13/24` |
| 100 % | `0:23 TIME LEFT WARLORDS · TURN 20/24` |

All three **differ**, monotonically: the clock counts down 2:00 → 0:59 → 0:23 and the turn counter
climbs 1 → 13 → 20. The viewer is advancing, not holding one frame.

Remaining lines from `smoke-stdout.txt`, verbatim:

```
canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
artifacts: /home/runner/work/coworld-builder/coworld-builder/viewer-smoke.png /home/runner/work/coworld-builder/coworld-builder/viewer-smoke.json
```

`smoke-stderr.txt` is 0 bytes and `console_tail` is `[]` — no runtime errors, no console noise.

Status: **TRUE**. Both required conditions hold:
1. `loaded: true` at **2 764 ms**, via `data-replay-loaded="true"` with `data_replay_error: null`.
   (`bridge: []`/`bridge_ready: false` — this shell signals readiness through the data attribute
   rather than the `coworld-replay` bridge; the prompt accepts either, and `bridge_error` is empty,
   so nothing failed.)
2. The three clock readouts differ.

*Two readouts that need naming rather than glossing, neither of which is a failure under the
check's stated conditions:*
- `canvas_text.total: 0`. The instrument hooks the canvas-2D `fillText`/`strokeText` API; this
  viewer is the ctf-family **wasm/WebGL** renderer with its captions in DOM overlay elements, so
  there is nothing for that hook to see. The consequence is that the `never_inside`/`ellipsized`
  bounds test — which was the r1 review's blocking finding — is **not exercised** by this
  instrument on this coworld. It is instead checked directly against the screenshot below, where
  the two full-length LLM `note` strings render complete and unclipped.
- `feed_lines: 0`. The smoke's `#feed` selector matched nothing, yet the screenshot plainly shows a
  running say-feed (two coloured champion lines above the arena and two full note panels at lower
  right). So the feed exists and is legible; what is missing is the `#feed` **id** the instrument
  looks for. Recorded as a **phase-30 legibility observation for the coordinator**, not as a check
  failure: the checklist's condition for item 8 is `loaded` plus differing clocks, both met.

*(c) The replay JSON the viewer was asked to draw* — ordered excerpts from `/tmp/ep.json`
(check 4's decode of `/tmp/ep.replay`), for reconciliation against the picture.
Columns: `turn  seat  alias  source  stance  target_ball  aim_at  say`.

Early (first 12 stance records — turns 0–2, all four seats):

```
0	0	BLUE	llm	camp	any	none	Ready.
0	1	RED	llm	guard	any	none	Game start - all equal. Waiting.
0	2	GREEN	scripted	camp	any	none	middle is mine
0	3	YELLOW	scripted	chase	any	RED	all gas
1	0	BLUE	llm	aim	B2	RED	B2 to RED in 68t
1	1	RED	llm	guard	B2	none	Defend first. Level field.
1	2	GREEN	scripted	camp	any	none	wall up
1	3	YELLOW	scripted	chase	any	BLUE	all gas
2	0	BLUE	llm	camp	any	none	Sitting safe, both balls headed elsewhere
2	1	RED	llm	aim	B2	BLUE	Disrupt early
2	2	GREEN	scripted	aim	B2	RED	your turn next
2	3	YELLOW	scripted	chase	any	GREEN	all gas
```

Middle (records 45–56 — turns 11–13):

```
11	0	BLUE	llm	catch	B1	RED	Catching B1, holding for release.
11	1	RED	llm	aim	B2	YELLOW	Taking shots at the leader
11	2	GREEN	scripted	camp	any	none	wall up
11	3	YELLOW	scripted	chase	any	GREEN	all gas
12	0	BLUE	llm	guard	B1	none	defending B1 inbound in 13 ticks
12	1	RED	llm	guard	B1	none	Defence first - B1 arriving in 13 ticks
12	2	GREEN	scripted	guard	B1	none	holding the line
12	3	YELLOW	scripted	chase	any	RED	all gas
13	0	BLUE	llm	guard	B2	none	Defending B2 to YELLOW
13	1	RED	llm	aim	B2	YELLOW	Disrupting YELLOW's defense
13	2	GREEN	scripted	aim	B2	BLUE	your turn next
13	3	YELLOW	scripted	chase	any	BLUE	all gas
```

Late (last 12 — turns 21–23):

```
21	0	BLUE	llm	guard	B1	none	B1 inbound 14t, defend
21	1	RED	llm	guard	B1	none	defending the mouth
21	2	GREEN	scripted	guard	B2	none	holding the line
21	3	YELLOW	scripted	chase	any	RED	all gas
22	0	BLUE	llm	aim	B1	RED	Wounding RED early wins the game
22	1	RED	llm	guard	B2	none	B2 incoming, defending my mouth
22	2	GREEN	scripted	camp	any	none	wall up
22	3	YELLOW	scripted	chase	any	BLUE	all gas
23	0	BLUE	llm	guard	B1	none	Defending B1, safe return
23	1	RED	llm	guard	B1	none	Defense first
23	2	GREEN	scripted	camp	any	none	wall up
23	3	YELLOW	scripted	chase	any	GREEN	all gas
```

The two champion `note` fields at turn 21, which the screenshot renders in full:

```
21	BLUE	B1 arrives in 14 ticks (Rule 1: defend). B2 at 23 ticks is secondary. WARLORDS with catch enabled - but B1 inbound NOW overrides catch strategy. Guard B1 safely
21	RED	B1 inbound in 14 ticks (inside 36). LEADER is YELLOW (3 lives, 7 bricks). I have 3 lives, all tied at 3. Guard B1 defensively per rule 1.
```

```bash
jq -r '.results' /tmp/ep.json      # pasted in full under check 4
```

### Spectator-judgment paragraph

**It is legible, and it shows the game.** `viewer-smoke.png` (411 KB, committed alongside this file)
was captured at tick **2573 / 2928**, turn **22/24**, 0:13 on the clock. It shows a complete
four-cabinet Warlords arena on a dark cabinet-styled field: four corner brick lattices (green top,
yellow left, blue right, red bottom) with visible gaps where bricks have already been chipped out,
four coloured paddles sitting on their mouths, and two balls plus a trail of small square particles
in flight. Each cabinet carries its current stance as a caption in its own colour — reading the
picture: `GUARD` (green), `CHASE >RED` (yellow), `GUARD` (blue, right), `GUARD` (red, bottom). That
is **exactly** the four-seat stance vector for turn 21 in the excerpt above
(`GREEN guard`, `YELLOW chase→RED`, `BLUE guard`, `RED guard`) — the picture and the record agree
seat by seat. Above the arena the two champion say-lines render in their seat colours,
`BLUE: B1 inbound 14t, defend` and `RED: defending the mouth`, again verbatim turn 21. At lower
right two note panels carry the champions' full reasoning strings, and they match the turn-21
`note` fields above **complete and unclipped** — the 160-rune notes are not ellipsized, which is
the direct check the r1 review's blocking finding was about and which the canvas-text instrument
could not exercise here. The scorebug across the top names every seat by **player**, not by policy:
`RED 68.50 DAVE…`, `GREEN 66.50 BAS…`, `DAVE… 47.00 BLUE`, `BA… 70.50 YELLOW`, each with a row of
heart pips for lives and a chip bar for bricks. The smoke's t=0 scorebug readout resolves the
truncation and confirms the mapping is right — `RED DAVEEY-1 · GREEN BASELINE · BLUE DAVEEY ·
YELLOW BASELINE (2)`, all at 60.00 — which is precisely the replay's
`names:["daveey","daveey-1","Baseline","Baseline (2)"]` against
`aliases:["BLUE","RED","GREEN","YELLOW"]`. **It moves**: three scrub positions give three different
clocks and three different turn numbers, so a spectator dragging the bar sees the match progress,
not a still. Nothing is empty, frozen or unreadable.

**Does it look like the starter's chrome?** Yes — this is recognisably the coworld-ctf/paintbot
shell, not a rewrite sharing only the ids. All four of the named elements are present in the
screenshot: (1) the **transport strip** along the bottom — restart, step-back, play, `+5s`,
play/pause, loop, fast-forward, a `spoilers` toggle, the tick counter `2573 / 2928`, and the
`1×/2×/3×/4×/8×/16×` speed bank on the right; (2) the **scrubber with its momentum graph**
immediately below, a full-width bar with the played portion filled to the playhead and a lead
trace drawn along it, labelled `HULL LEAD` at the left; (3) the **scorebug** across the top as
described; (4) the **endcard** is not visible in this frame and could not be — the capture is at
turn 22 of 24, before game over — so its presence is not asserted here either way. The coworld's
own additions sit inside that frame rather than replacing it: the `WARLORDS` ROM badge in the clock
block, the legend `WARLORDS — DASHED RAY = WHERE THAT CABINET IS AIMING` at lower left, the
per-cabinet stance captions and the note panels. The tick denominator `2928` equals the replay
config's `maxTicks: 2880` plus `gameOverTicks: 48`, so the transport is scaled to the episode's real
length. (One counter mismatch worth naming without over-claiming: the decoded replay reports
`results.finalTick: 5275`, a larger number than the viewer's 2928 denominator. The two are on
different bases — the hash-chain tick evidently spans the pre-game lobby wait as well — but I did
not verify that, so it is recorded as an unexplained observation, not as a finding.)

---

## Anomaly — round 2 ran 100 % scripted-fallback (platform-side, cleared before round 3)

Recorded in full because it is the reason checks 3–5 are reported on round 3 rather than round 2,
and because the coordinator should see it. **It is not a defect in this coworld**, and the evidence
for that is internal to this run rather than a cross-coworld inference.

Round 2's replay, decoded the same way as check 4:

```bash
$ curl -sSL "https://softmax-public.s3.amazonaws.com/replays/f15b863e-45da-4fd7-8e90-e7fd3146e1c3.replay" -o /tmp/ep2.replay
HTTP:200 bytes:112794
$ python3 /tmp/replay_summary.py /tmp/ep2.replay > /tmp/ep2.json
$ jq -r '.protocol, .results.reason, .results.endRule' /tmp/ep2.json
atari-cabinet/v1
complete
full_time
$ jq -r '[.stances[]|select(.source=="llm")]|length' /tmp/ep2.json ; jq -r '.fallbacks' /tmp/ep2.json ; jq -c '.fallbackCauses' /tmp/ep2.json
0
144
["parse_error"]
$ jq -c '.results.llmTurns, .results.fallbackTurns' /tmp/ep2.json
[0,0,0,0]
[24,24,0,0]
```

Round 2's hosted log (`ereq_a9062177-6533-41ed-ad2c-842309c6bb9c`), decoded:

```
$ grep -nE 'falling back|LLM provider is unavailable' /tmp/logs2.txt | head -6
124:cabinet llm: seat 0 attempt 1 failed, falling back if it fails again: anthropic error 503: {"message":"LLM provider is unavailable"}
125:cabinet llm: seat 1 attempt 1 failed, falling back if it fails again: anthropic error 503: {"message":"LLM provider is unavailable"}
126:cabinet llm: seat 0 attempt 2 failed, falling back if it fails again: anthropic error 503: {"message":"LLM provider is unavailable"}
127:cabinet llm: seat 1 attempt 2 failed, falling back if it fails again: anthropic error 503: {"message":"LLM provider is unavailable"}
128:cabinet llm: seat 0 falling back to bulwark (parse_error) on turn 0
129:cabinet llm: seat 1 falling back to bulwark (parse_error) on turn 0
$ grep -c 'LLM provider is unavailable' /tmp/logs2.txt
96
```

The 503 comes from the **platform's** `bedrock-sidecar` container, and its own log lines show why:

```
$ grep -nE '^2026-08-26' /tmp/logs2.txt | sed -n '3,6p'
7:2026-08-26 20:36:14,696 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 402 Payment Required"
8:2026-08-26 20:36:14,733 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 402 Payment Required"
9:2026-08-26 20:36:14,759 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 402 Payment Required"
10:2026-08-26 20:36:14,795 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 402 Payment Required"
$ grep -c 'openrouter.ai' /tmp/logs2.txt ; grep -c 'bedrock-runtime' /tmp/logs2.txt
96
0
```

**The decisive comparison is within this coworld, across its own three rounds — same coworld image,
same policies, same sidecar image digest, same region, opposite routing:**

| round | sidecar `image_digest` | region | upstream the sidecar called | result | fallbacks |
|---|---|---|---|---|---|
| 1 (20:21Z) | `sha256:8225b38c59fcc3de093bb05f75b735bd91302702b820554f5c66653f68aab48c` | us-east-1 | `bedrock-runtime.us-east-1.amazonaws.com` ×48, all `200 OK` | clean | **0** |
| 2 (20:36Z) | `sha256:8225b38c59fcc3de093bb05f75b735bd91302702b820554f5c66653f68aab48c` | us-east-1 | `openrouter.ai/api/v1/messages` ×96, all `402 Payment Required` | 100 % fallback | **144** |
| 3 (20:51Z) | `sha256:8225b38c59fcc3de093bb05f75b735bd91302702b820554f5c66653f68aab48c` | us-east-1 | `bedrock-runtime.us-east-1.amazonaws.com` ×48, all `200 OK` | clean | **0** |

The sidecar image digest is **byte-identical** in all three rounds and the coworld shipped nothing
between them, so the upstream the sidecar chose is a platform-side runtime decision. This coworld's
only role is a call to `http://127.0.0.1:9100`. The `parse_error` fallback cause is the coworld's
correct, designed behaviour when the sidecar returns a 503 body instead of a decision — it degraded
to `bulwark` and still produced a complete, valid, scored episode
(`reason: complete`, `endRule: full_time`), which is exactly what `design.md` §"Degrade, never hang"
specifies.

**Documented precedent:** `runs/2026-08-26-poker/VERIFY.md` records the identical condition earlier
the same day — *"the platform's LLM sidecar was routed to `openrouter.ai` and returned `402 Payment
Required` on every call"* — affecting poker's rounds 1 and 2 and then clearing.

**Cross-check attempted and reported honestly:** I fetched the two poker rounds whose episodes
straddle ours. Poker round 8 (`ereq_71c3b6f6-aaf3-4313-83ad-08047959d287`, completed 20:35:09Z) and
poker round 9 (`ereq_858160af-21db-426e-9f1f-313b4a4cb606`, episode ran 20:41:13–20:44:53Z) were
**both clean** — 0 openrouter calls, 66 Bedrock calls on round 9, 0 occurrences of `LLM provider is
unavailable`. So the concurrent-coworld half of check 5's documented exception was **not**
satisfied; poker's overlapping episode began at 20:41:13Z, after our 20:36:14–20:41Z failure window,
and poker's sidecar carried a *different* image digest
(`sha256:32e0e4a7d91c6387b994504a1651941dfdd475d4c17c61c8f6d302e4f13ef055`). I am therefore **not**
resting on that clause. The exception is unnecessary anyway: check 5 is reported on **round 3**,
whose log is `CLEAN` outright with no exception claimed, and the within-coworld three-round table
above establishes the round-2 cause independently.

Round 2 also confirms filler labelling end-to-end, since its replay was decoded in full:

```bash
$ jq -c '.results.names, .results.policyKinds' /tmp/ep2.json
["daveey","daveey-1","Baseline","Baseline (2)"]
["llm","llm","scripted","scripted"]
```

Round 1 for completeness (`ereq_f6364527-b518-41dd-830d-d7884e97283f`), also fetched this run:
`protocol atari-cabinet/v1`, `reason complete`, `endRule full_time`, 48 LLM stances, **0**
fallbacks, log `CLEAN`, names `["daveey","daveey-1","Baseline","Baseline (2)"]`.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | **TRUE** — rounds 2 and 3 (and 1), 0 failed/discarded |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey + daveey-1, `rounds_played: 3`, fillers unranked |
| 3 | Latest round's episode request completed with a replay | **TRUE** — `ereq_21bff821…` completed, replay_url present, both champions seated |
| 4 | Replay bytes valid, protocol match, shows the game | **TRUE** — strict JSON via the design's declared `replay_summary.py`, `atari-cabinet/v1`, `complete/full_time`, 48/48 LLM, 0 fallbacks |
| 5 | Hosted game log clean | **TRUE** — `CLEAN`, 48 Bedrock 200s, 0 openrouter |
| 6 | Public page uses the **static** replay path | **TRUE** — `/v2/coworlds/replays/static/<cow>/<manifest_sha>/index.html?replay=…`, `ready: true`, featured match = round 3 |
| 7 | Certification declared the static bundle | **TRUE** — committed `release-result.json`, `Replay liveness: skipped (static replay bundle declared…` |
| 8 | Viewer executed and judged | **TRUE** — run `33013149654`, `loaded: true` at 2 764 ms, three differing clocks, starter chrome intact |

**Observations for the coordinator (none blocking, none affecting a verdict):**
1. The viewer shell exposes no `#feed` id, so `viewer-check` reports `feed_lines: 0` even though a
   say-feed and two note panels render clearly in the screenshot. Phase-30 legibility nit.
2. The renderer draws no canvas-2D text (`canvas_text.total: 0`), so the automated
   text-bounds/ellipsis test is inert for this coworld. The notes were checked by eye against the
   screenshot instead and render complete.
3. `results.finalTick` (5275) and the viewer's tick denominator (2928 = `maxTicks` 2880 +
   `gameOverTicks` 48) are on different bases. Unexplained, not investigated.
4. Round 2's platform-side openrouter-402 episode is on the ladder permanently and will remain in
   the league's history; it is scored and counted in the leaderboard's `rounds_played: 3`.
