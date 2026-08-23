# VERIFY — cogball   (2026-08-23T09:34:45Z)

Verdict: **all-true** (8/8)

Release under test: **v0.1.5**, `cow_ff38b98b-f611-4a74-86e1-f2b23cbd6339`,
manifest `sha256:495905b153bc98135ae1ec127e8f4abc2b9c88cff6a6d1edf0934d161ec5dce7`,
release run `32624985984`.
League `league_e87130ef-ecc6-49d4-9bc1-4014b7141df5`, division
`div_45c40cad-ef84-4d48-a733-59e55f80e24c`.

This is a **complete re-pass**. The previous VERIFY.md (git history, commit `11b6083`'s parent
lineage) was written against v0.1.3 / `cow_5d14a55f` and found check 8 FALSE (the viewer shell
aborted with `ReferenceError: COG_BASE is not defined`). Every fetch below was made fresh in this
pass, 2026-08-23T09:30–09:34Z, against the current 0.1.5 release. **Nothing is recycled from the
0.1.3 pass.** Two artifacts are read from disk rather than re-fetched, both because the prompt
pins them there:

- **check 7** — `runs/2026-08-22-cogball/release-result.json`, the committed 0.1.5 release
  artifact (`prompts/60-verify.md` check 7: "Read the committed copy, never `/tmp`").
- **check 8** — a **freshly dispatched** viewer-check run (`32631291526`, dispatched at
  09:32:37Z by this pass) whose artifacts are committed at
  `runs/2026-08-22-cogball/viewer-check/`. The pre-existing green run `32630840631` was
  **not** adopted: it tested round 15's replay, whereas this pass's check-6 iframe `src`
  carries round 16's. The fresh run tests the exact check-6 URL, byte for byte.

Header conventions below: `AUTH` = `Authorization: Bearer <redacted>` + `User-Agent:
coworld-builder/1.0`; `ELEV` = `X-Use-Elevated-Privileges: true`. Header **values** are never
printed. `$BASE` = `https://softmax.com/api/observatory/v2`.

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

```
GET $BASE/rounds?league_id=league_e87130ef-ecc6-49d4-9bc1-4014b7141df5&limit=20
     (headers: Authorization, User-Agent)
```
```
HTTP 200
```
```
jq -r '[.entries[]|select(.status=="completed")]|length'
```
```
16
```

Every entry, `round_number / id / status / error / completed_at`:

```
1	round_c8f6ad75-e6cd-4088-87e3-5aa9de3a7d67	completed	null	2026-08-23T05:44:06.458180Z
2	round_4af4bfff-8c80-4277-9d28-4f3b4fa9e3ae	completed	null	2026-08-23T05:59:16.029721Z
3	round_ce53f0f4-edb0-4d65-9a33-f01e90001863	completed	null	2026-08-23T06:14:07.878184Z
4	round_4ab78624-fa28-431b-a74d-5b1f80d28f86	completed	null	2026-08-23T06:29:08.691354Z
5	round_87e5df56-a3e3-4ecc-81f2-a36aae708269	completed	null	2026-08-23T06:44:09.903234Z
6	round_fc037678-1545-4ea8-b2d6-e0ca3e032f52	completed	null	2026-08-23T07:00:39.074344Z
7	round_bec74f71-76ab-43a5-9e54-204c44989a77	completed	null	2026-08-23T07:14:17.802281Z
8	round_b437fa00-07ea-4aea-a5d8-6f5dd97e60cf	completed	null	2026-08-23T07:29:09.523184Z
9	round_e51d07e6-c4c2-48f1-b276-9e50eafef564	completed	null	2026-08-23T07:44:12.266249Z
10	round_173034e9-d2b8-4f83-996e-535840022fa1	completed	null	2026-08-23T07:59:10.916334Z
11	round_c66b78eb-fa72-40d4-8283-dc50dd683f0d	completed	null	2026-08-23T08:14:09.709145Z
12	round_7549a2e3-fb4a-4314-9891-13d7878233a8	completed	null	2026-08-23T08:29:22.515849Z
13	round_a249ea28-e517-4a67-af80-5bd2dbd60526	completed	null	2026-08-23T08:44:32.103564Z
14	round_85bee7ee-822d-41d2-94f9-1ff488bc0f4d	completed	null	2026-08-23T08:59:22.796224Z
15	round_437c3a0d-0575-4cd4-976b-9a46629e5fab	completed	null	2026-08-23T09:14:13.239580Z
16	round_ce3789ab-ae2a-4e46-a1d6-dc657283d165	completed	null	2026-08-23T09:29:13.606649Z
```

Raw JSON for the two most recent, unedited:

```json
{"id":"round_ce3789ab-ae2a-4e46-a1d6-dc657283d165","round_number":16,"status":"completed","error":null,"completed_at":"2026-08-23T09:29:13.606649Z"}
{"id":"round_437c3a0d-0575-4cd4-976b-9a46629e5fab","round_number":15,"status":"completed","error":null,"completed_at":"2026-08-23T09:14:13.239580Z"}
```

**Zero** rounds have status `failed` or `discarded`, and `error` is `null` on all 16 — there is
no Temporal message to record verbatim.

**Fillers were set before round 1.** `log.md` records the registration at
`2026-08-23T05:42:09Z` ("50 fillers 200: formation:v2 + swarm:v2 registered BEFORE trigger")
and the trigger in the same line-group; round 1 completed at `05:44:06Z`, i.e. **after**.
Corroborated by a fresh read of the live filler set:

```
GET $BASE/leagues/league_e87130ef-ecc6-49d4-9bc1-4014b7141df5/filler-policies
     (headers: Authorization, User-Agent, X-Use-Elevated-Privileges)
```
```
HTTP 200
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"7c11dd63-d0a2-465d-9e71-9e02de0136eb","policy_id":"4914d54d-00ef-469a-a386-2dcfc775f160","policy_name":"cogball-formation","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},
 {"policy_version_id":"259d11a4-7ebc-4d0e-a704-6769a1a7b527","policy_id":"a0818edd-e54c-49f5-ada9-438849348a3f","policy_name":"cogball-swarm","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```

The two filler version ids are exactly the pair `STATE.policies.filler_version_ids` records, and
neither is a champion version id (`0f2edcb1…` total:v2, `40f864bb…` counter:v2).

Round 16's seated entrants — both champions, no filler:

```json
{"round_number":16,"id":"round_ce3789ab-ae2a-4e46-a1d6-dc657283d165","status":"completed","error":null,
 "entrants":[
  {"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player","policy_version_id":"0f2edcb1-15cb-4410-a4c6-6042870467d9","league_policy_membership_id":"lpm_c8a63ff9-fbaa-47cf-ad51-a50bf00e2221"},
  {"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","subject_type":"player","policy_version_id":"40f864bb-d07c-4ae3-a96d-1e08fb5491e9","league_policy_membership_id":"lpm_22851107-b86c-45da-993b-107e0a094155"}]}
```

Status: **TRUE** — 16 completed rounds, all of them after the fillers were registered at
05:42:09Z; requirement is ≥ 2. No failed or discarded rounds. No polling was needed; the bound
was never approached.

---

## 2. Both champions ranked — **TRUE**

```
GET $BASE/divisions/div_45c40cad-ef84-4d48-a733-59e55f80e24c/leaderboard
     (headers: Authorization, User-Agent)
```
```
HTTP 200
```
```
jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey	cogball-total:v2	1026.850301556938	16	9.0
2	daveey-1	cogball-counter:v2	973.1496984430622	16	4.0
```

The whole response body, unedited (a bare list, not `.entries`):

```json
[{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1026.850301556938,"score_label":"Elo","score_value_type":"integer","rounds_played":16,"episode_wins":9.0,"episodes_played":null,"win_rate":0.5625,"policy_label":"cogball-total:v2","recent_rounds":null},
 {"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":973.1496984430622,"score_label":"Elo","score_value_type":"integer","rounds_played":16,"episode_wins":4.0,"episodes_played":null,"win_rate":0.25,"policy_label":"cogball-counter:v2","recent_rounds":null}]
```

Status: **TRUE** — `daveey` (rank 1, `cogball-total:v2`, `rounds_played` 16) and `daveey-1`
(rank 2, `cogball-counter:v2`, `rounds_played` 16) are both present, both ≥ 1 round. The
leaderboard has exactly two rows: the fillers `cogball-formation:v2` and `cogball-swarm:v2` are
**absent**, which is the stronger of the two permitted outcomes (absent, or labelled `Baseline`).

---

## 3. Latest round's episode request completed with a replay — **TRUE**

Latest completed round = `max_by(.round_number)` over check 1's fetch = **round 16**,
`round_ce3789ab-ae2a-4e46-a1d6-dc657283d165`.

```
GET $BASE/episode-requests?round_id=round_ce3789ab-ae2a-4e46-a1d6-dc657283d165&limit=20
     (headers: Authorization, User-Agent)
```
```
HTTP 200 — .entries|length = 1
ereq_21ccb33a-41bc-466c-a35b-12d7eb1ffad9	completed
```

```
GET $BASE/episode-requests/ereq_21ccb33a-41bc-466c-a35b-12d7eb1ffad9
     (headers: Authorization, User-Agent)
jq '{status, replay_url, participants, participant_scores}'
```
```
HTTP 200
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/f2133337-531b-4ff6-91d6-1385fb48a307.replay",
  "participants": [
    {
      "position": 0,
      "kind": "policy",
      "policy_version_id": "0f2edcb1-15cb-4410-a4c6-6042870467d9",
      "policy_id": "eb27b953-1b61-41c9-a26b-94b8345c55ae",
      "policy_name": "cogball-total",
      "version": 2,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "is_filler": false
    },
    {
      "position": 1,
      "kind": "policy",
      "policy_version_id": "40f864bb-d07c-4ae3-a96d-1e08fb5491e9",
      "policy_id": "b86015e4-1294-4d29-becd-c8657fd2cd66",
      "policy_name": "cogball-counter",
      "version": 2,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
      "player_name": "daveey-1",
      "is_filler": false
    }
  ],
  "participant_scores": [
    {"position": 0, "score": 0.5},
    {"position": 1, "score": 0.5}
  ]
}
```

Status: **TRUE** — `status == "completed"`; `replay_url` is non-null and points at S3;
`participants` names **`daveey`** (seat 0, `cogball-total` v2) and **`daveey-1`** (seat 1,
`cogball-counter` v2), both `is_filler: false`, no `Baseline (N)` seat present. This replay URL
is the one carried through checks 4, 6 and 8.

---

## 4. Replay bytes are valid and show the game — **TRUE**

**Documented substitution, re-stated.** cogball's replay is the paintbot lineage's **binary
`COWLDBAL`** container, not JSON, so `jq -e . /tmp/ep.replay` is not applicable. The accepted
design note declares the drop-in substitute — `runs/2026-08-22-cogball/design.md`
§"Replay bytes (self-sufficient)":

> **The phase-60 substitute for SPEC §Definition of done check 4** is therefore:
> `python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json` … Require
> `protocol == "cogball/v1"`, `results.reason == "complete"` … and the champion seats'
> directives `source == "llm"` with non-empty `note`/`intent` content — not all fallbacks.

The tool is Python-3-stdlib-only and ships in the coworld repo. Fetched fresh this pass:

```
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/f2133337-531b-4ff6-91d6-1385fb48a307.replay" -o /tmp/ep.replay
```
```
HTTP 200 bytes=185452
```
```
head -c 32 /tmp/ep.replay | od -c
0000000   C   O   W   L   D   B   A   L 001  \0  \a  \0   c   o   g   b
0000020   a   l   l 001  \0   1 250   2 361   - 240 001  \0  \0 033 003
```
magic = `COWLDBAL`, game name = `cogball`, game version = `1` — the header the manifest's wire
protocol page describes.

```
git clone --depth 1 https://github.com/Metta-AI/cogame-cogball /workspace/scratch/verify-cogball   # HEAD ed78392
python3 /workspace/scratch/verify-cogball/tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json    # exit=0, 29451 bytes
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .results.reason' /tmp/ep.json
jq -r '[.directives[]|select(.source=="llm")]|length' /tmp/ep.json
jq -r '.fallbacks' /tmp/ep.json
jq -r '.directives|length' /tmp/ep.json
```
```
strict UTF-8 JSON: ok
cogball/v1
complete
80
0
80
```

**`protocol` matches the manifest.** The manifest declares the replay's protocol identity at
`coworld_manifest_template.json` → `.game.docs.pages[1]` (title "Wire protocol"), line 141 of
that page's content:

```
jq -r '.game.docs.pages[1].content.value' coworld_manifest_template.json | grep -n 'cogball/v1'
141:{"protocol":"cogball/v1","gameVersion":"1","seed":679961,
```

Manifest says `cogball/v1`; the fetched bytes say `cogball/v1`. Match.

Header and integrity fields out of the same summary:

```
jq -c '{names,aliases,policyKinds,policyLabels,tickCount,maxTicks,turnTicks,seed,numAgents,utf8Repairs,fallbackAttempts,budgetGuards,inputRecords,hashChain}' /tmp/ep.json
```
```json
{"names":["daveey","daveey-1"],"aliases":["Azure","Crimson"],"policyKinds":["llm","llm"],"policyLabels":["total","counter"],"tickCount":5107,"maxTicks":4800,"turnTicks":120,"seed":1770193400,"numAgents":2,"utf8Repairs":0,"fallbackAttempts":0,"budgetGuards":[],"inputRecords":9558,"hashChain":"f3f5d00d42ad4fd6"}
```

`utf8Repairs: 0` — the strict parser needed no repair; the bytes are clean UTF-8 in the
JSON-bearing records.

```
jq -c '.results' /tmp/ep.json
```
```json
{"names":["daveey","daveey-1"],"scores":[0.5,0.5],"win":[false,false],"team":["azure","crimson"],"goals":[1,1],"shots":[15,1],"shotsOnTarget":[6,1],"saves":[0,0],"possessionTicks":[2803,1782],"llmTurns":[40,40],"fallbackTurns":[0,0],"reason":"complete","endRule":"full_time","finalTick":5106,"seed":1770193400}
```

Per-seat decision provenance — **no scripted and no fallback directive anywhere**:

```
jq -r '[.directives[].source]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.json
jq -c '.directives|group_by(.seat)|map({seat:.[0].seat,total:length,llm:map(select(.source=="llm"))|length})' /tmp/ep.json
```
```json
{"llm": 80}
[{"seat":0,"total":40,"llm":40},{"seat":1,"total":40,"llm":40}]
```

Two directives in full, showing non-trivial content (note + intents + says):

```json
{"turn":20,"seat":0,"alias":"Azure","source":"llm","latency_ms":2275,"note":"AZ-3 closest (5.8m) - SHOOT at goal. AZ-2 keeper on arc. AZ-1 support intercept.","intents":["intercept","hold","shoot"],"says":["Support coverage","Keeper arc","Shooting at goal"]}
{"turn":21,"seat":1,"alias":"Crimson","source":"llm","latency_ms":2130,"note":"Ball loose at x=15, in our half. AZ-1 closest at 3.57m. Switch to ATTACK: CR-1 keeper holds, CR-2 wing intercepts up-field far side, CR-3 shoots at goal. Win a…","intents":["hold","intercept","shoot"],"says":["Guard goal","Intercept far side","Strike at goal"]}
```

Status: **TRUE** — the summary parses under a strict UTF-8 JSON parser; `protocol` is
`cogball/v1`, matching the manifest; `results.reason` is `"complete"` (no `deadline` exception
needed); both champion seats produced 40/40 genuinely LLM-sourced directives with substantive
tactical notes, and the fallback count is **0 of 80** — not merely a small minority, but none.

---

## 5. Hosted game log is clean — **TRUE**

```
GET $BASE/episode-requests/ereq_21ccb33a-41bc-466c-a35b-12d7eb1ffad9/artifacts/logs
     (headers: Authorization, User-Agent, X-Use-Elevated-Privileges)
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' || echo CLEAN
```
```
HTTP 200 bytes=174583
CLEAN
```

The log really is this episode's — four containers, 174 583 bytes:

```
grep -n '===== container' logs.txt
1:===== container: coworld-init-config =====
4:===== container: bedrock-sidecar =====
7:===== container: game =====
10:===== container: worker =====
```

Head of the `game` container:

```
===== container: game =====
b'seed not pinned; randomized\ncogball config: host=0.0.0.0 port=8080 seed=1770193400 num_agents=2 minPlayers=2 maxTicks=4800 turnTicks=120 turnBudgetMs=9000 wallClockBudgetSeconds=690 fastMode=true\nstarting cogball on 0.0.0.0:8080\nboard render caches baked in 115 ms (charged against wallClockBudgetSeconds=690)\ncogball llm: bedrock transport, url http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke\nwaiting for players: 0/2, need 2 more\nplayer connected: daveey-1\nplayer connected: daveey\nplayer joined: daveey as Azure\nplayer joined: daveey-1 as Crimson\nwaiting for players: 2/2, need 0 more\ngame starting in 1\n…match start, kickoff for seat 0…
```

Tail of the same log:

```
…\nneutral drop at 11000000,6500000\ngoal for azure: 1-1\nneutral drop at 33000000,6500000\ngame over: complete/full_time 1-1\nReplay written: /tmp/cogball-replay-1.bitreplay (185452 bytes)\nEvents written: /coworld/events.json (4080 events)\nResults: {"names":["daveey","daveey-1"],"scores":[0.5,0.5],"win":[false,false],"team":["azure","crimson"],"goals":[1,1],"shots":[15,1],"shotsOnTarget":[6,1],"saves":[0,0],"possessionTicks":[2803,1782],"llmTurns":[40,40],"fallbackTurns":[0,0],"reason":"complete","endRule":"full_time","finalTick":5106,"seed":1770193400}\n'

===== container: worker =====
b''
```

The log's own seed (`1770193400`) and byte count (`185452`) match the replay fetched in check 4,
so this is the right episode's log.

Status: **TRUE** — the grep over all four containers returns no match for any of `falling back`,
`LLM provider is unavailable`, `cut off at max_tokens`, `rejected`; the guard printed `CLEAN`.
**No exception is being claimed**: there is no `LLM provider is unavailable` line, so no
cross-check against another LLM coworld and no Bedrock-capacity argument is required. The log's
own results line independently corroborates `fallbackTurns: [0,0]` and `reason: "complete"`.

---

## 6. The public page uses the static replay path — **TRUE**

**Source A — raw-HTML grep of the human page (the prompt's first command):**

```
curl -sS "https://softmax.com/cogball" | grep -o '<iframe[^>]*src="[^"]*"'
```
```
HTTP 200 bytes=353468
(no match — raw-HTML grep empty)
```

Per `prompts/60-verify.md` this is **not** a false negative to record: the page is
client-rendered for the iframe, as `playbooks/observatory-api.md` §Featured match / replay route
records (lighthouse run, 2026-08-22 — "the raw-HTML grep finds nothing for any coworld"). So the
prompt's fallback is used.

**Source B — the `/coworlds` fallback the prompt names:**

```
GET $BASE/coworlds?limit=200      (headers: Authorization, User-Agent)
jq -r '(if type=="array" then . else .entries end)[]|select(.name=="cogball")|{id,name,version,canonical,replay_viewer,featured_match}'
```
```
HTTP 200
```
```json
{"id":"cow_ff38b98b-f611-4a74-86e1-f2b23cbd6339","name":"cogball","version":"0.1.5","canonical":true,"replay_viewer":null,"featured_match":null}
{"id":"cow_795268b0-3cff-476f-be68-e73a5ba19084","name":"cogball","version":"0.1.4","canonical":false,"replay_viewer":null,"featured_match":null}
{"id":"cow_5d14a55f-2647-49fa-95d4-7b37a7463da5","name":"cogball","version":"0.1.3","canonical":false,"replay_viewer":null,"featured_match":null}
{"id":"cow_23c9b804-8fb4-470d-ae86-bccf7a1aa5c3","name":"cogball","version":"0.1.2","canonical":false,"replay_viewer":null,"featured_match":null}
```

`cow_ff38b98b` (0.1.5) is the **only** `canonical: true` row — the three older per-version rows
are superseded, exactly as STATE records. `featured_match` is `null` here, which the playbook
records as **null platform-wide** and therefore not evidence either way.

**Source C — the featured match, where the page actually server-renders it** (`state.playlist[0]`
in the SSR payload of the same `softmax.com/cogball` fetch above):

```
grep -o 'playlist[^]]\{0,900\}' page.html
```
```json
playlist":[{"episodeId":"f2462e41-ec10-4fbb-95d6-3e7bae331771","coworldId":"cow_ff38b98b-f611-4a74-86e1-f2b23cbd6339","coworldName":"cogball","coworldVersion":"0.1.5","replayUrl":"https://softmax-public.s3.amazonaws.com/replays/f2133337-531b-4ff6-91d6-1385fb48a307.replay","finishedAt":"2026-08-23T09:29:12.998000Z","roundNumber":16,"episodeNumber":1,"code":"cogball.r16.e1","matchup":{"divisionId":"div_45c40cad-ef84-4d48-a733-59e55f80e24c","divisionName":"Competition","first":{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1026.850301556938,"score_label":"Elo","score_value_type":"integer","rounds_played":16,"episode_wins":9,"episodes_played":null,"win_rate":0.5625,"policy_label":"cogball-total:v2","recent_rounds":null},"second":{"rank":2,"player_id":"ply_bac48eb1-66…
```

**A featured match is present**: `cogball.r16.e1`, `cow_ff38b98b` / 0.1.5, replay
`f2133337-…` — the *same* replay as check 3's latest-round episode — with a two-ranked-player
matchup (`daveey` vs `daveey-1`).

**Source D — the iframe `src` itself**, from the call the page's own JS makes (playbook §Featured
match / replay route):

```
POST $BASE/coworlds/replays/session      (headers: Authorization, User-Agent, content-type)
body: {"coworld_id":"cow_ff38b98b-f611-4a74-86e1-f2b23cbd6339",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/f2133337-531b-4ff6-91d6-1385fb48a307.replay"}
```
```
HTTP 200
```
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_ff38b98b-f611-4a74-86e1-f2b23cbd6339/sha256%3A495905b153bc98135ae1ec127e8f4abc2b9c88cff6a6d1edf0934d161ec5dce7/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Ff2133337-531b-4ff6-91d6-1385fb48a307.replay&v=2","ready":true}
```

**Source used: A (empty, treated as unknown per the prompt) → B + C + D.** The recorded answer
comes from B/C/D.

The `src` decomposes exactly as the prompt requires:

| segment | value | required |
|---|---|---|
| route | `/v2/coworlds/replays/static/…/index.html` | static bundle ✔ (not `/client/replay`) |
| `<cow_id>` | `cow_ff38b98b-f611-4a74-86e1-f2b23cbd6339` | = `STATE.coworld.cow_id`, the canonical 0.1.5 row ✔ |
| `<sha>` | `sha256%3A495905b153bc98135ae1ec127e8f4abc2b9c88cff6a6d1edf0934d161ec5dce7` | = `STATE.coworld.manifest_sha`, URL-encoded ✔ |
| `?replay=` | `…/replays/f2133337-531b-4ff6-91d6-1385fb48a307.replay` | = check 3's `replay_url` ✔ |
| `ready` | `true` | static delivery ✔ |

Status: **TRUE** — the iframe `src` is the static replay-bundle path for the canonical
`cow_ff38b98b` at manifest sha `495905b1…`, serving round 16's replay; `ready: true`. It is
**not** a `/client/replay` pod URL, and no `/client/` substring appears in it. A featured match
is present.

---

## 7. Certification declared the static bundle — **TRUE**

**Source: the committed artifact** `runs/2026-08-22-cogball/release-result.json`. It is already
the **0.1.5** artifact from release run `32624985984` (phase 40's re-release copy — see `log.md`
09:27:39Z, "release-result.json overwritten with the 0.1.5 artifact"), so **no `gh run download`
was needed**; the committed copy was read directly, per the prompt's instruction never to look
in `/tmp`.

```
jq -r '.certify.replay_liveness' runs/2026-08-22-cogball/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Provenance of the file, confirming it is this run's 0.1.5 release and not a stale 0.1.3 copy:

```
jq -c '{ok, version, cow_id, canonical, certify_ok: .certify.ok}' runs/2026-08-22-cogball/release-result.json
{"ok":true,"version":"0.1.5","cow_id":"cow_ff38b98b-f611-4a74-86e1-f2b23cbd6339","canonical":true,"certify_ok":true}
```

The certifier transcript inside the same artifact, all ten steps:

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

Status: **TRUE** — the certification output contains the required string
`Replay liveness: skipped (static replay bundle declared`, read from the **committed**
`runs/2026-08-22-cogball/release-result.json` (0.1.5 / run 32624985984), not from `/tmp` and not
re-downloaded.

---

## 8. Spectator judgment — the viewer is EXECUTED, then judged — **TRUE**

### (a) The dispatch

Fresh dispatch this pass against **the exact `src` from check 6**, character for character:

```
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_ff38b98b-f611-4a74-86e1-f2b23cbd6339/sha256%3A495905b153bc98135ae1ec127e8f4abc2b9c88cff6a6d1edf0934d161ec5dce7/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Ff2133337-531b-4ff6-91d6-1385fb48a307.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90    # dispatched 2026-08-23T09:32:37Z
```
```
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10
{"conclusion":"","createdAt":"2026-08-23T09:32:39Z","databaseId":32631291526,"status":"in_progress"}   ← created AFTER the dispatch
{"conclusion":"success","createdAt":"2026-08-23T09:22:56Z","databaseId":32630840631,"status":"completed"}
```
```
gh run view 32631291526 -R Metta-AI/coworld-builder --json status,conclusion,createdAt,updatedAt
{"conclusion":"success","createdAt":"2026-08-23T09:32:39Z","status":"completed","updatedAt":"2026-08-23T09:33:18Z"}

gh run download 32631291526 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-22-cogball/viewer-check
```

Artifacts committed at `runs/2026-08-22-cogball/viewer-check/` — `viewer-smoke.json` (1045 B),
`viewer-smoke.png` (352 960 B), `smoke-stdout.txt`, `smoke-stderr.txt` (0 B, empty).

**Why a fresh run and not the pre-existing green one.** Run `32630840631` (09:22:56Z) is green on
the same bundle path but tested `?replay=…e6a6bf9a-….replay`, which is **round 15**. This pass's
check-6 `src` carries **round 16**'s `f2133337-…`. Rather than adopt a URL that differs from the
one check 6 produced, this pass dispatched `32631291526` against check 6's exact `src`. The
`viewer-smoke.json` `url` field below is byte-identical to the `viewer_url` in check 6's session
response, so the rendered evidence and the public iframe are provably the same page.

### (b) The readouts

```
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-22-cogball/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":4122,"clock":"3:20 TURN 1/40","scorebug":"DAVEEY 0% 0 sh 0 3:20 TURN 1/40 DAVEEY-1 0% 0 sh 0","feed_lines":0}
```
```
jq -c '.signals' …/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```
```
jq -r '.failure // "no failure"' …/viewer-smoke.json
```
```
no failure
```

**The three clock readouts:**

| scrub position | clock |
|---|---|
| 0 % | `3:20 TURN 1/40` |
| 50 % | `1:38 TURN 21/40` |
| 100 % | `FINAL GAME OVER` |

All three **differ**. The whole `viewer-smoke.json`, verbatim:

```json
{"loaded":true,"ms":4122,"url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_ff38b98b-f611-4a74-86e1-f2b23cbd6339/sha256%3A495905b153bc98135ae1ec127e8f4abc2b9c88cff6a6d1edf0934d161ec5dce7/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Ff2133337-531b-4ff6-91d6-1385fb48a307.replay&v=2","bundle":null,"replay":null,"clock":"3:20 TURN 1/40","scorebug":"DAVEEY 0% 0 sh 0 3:20 TURN 1/40 DAVEEY-1 0% 0 sh 0","status":"OPEN","loading_text":null,"feed_lines":0,"signals":{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]},"scrub":[{"at":"0%","clock":"3:20 TURN 1/40"},{"at":"50%","clock":"1:38 TURN 21/40"},{"at":"100%","clock":"FINAL GAME OVER"}],"failure":null,"console_tail":[],"screenshot":"/home/runner/work/coworld-builder/coworld-builder/viewer-smoke.png"}
```

`console_tail: []` — the browser console logged no errors. `loading_text: null` — the page is not
stuck on a "Loading replay…" placeholder (the cogame-lantern failure mode).

**On the readiness signal.** `loaded: true` here is carried by `data-replay-loaded="true"`, not
by the `coworld-replay` postMessage bridge (`bridge: []`, `bridge_ready: false`).
`prompts/60-verify.md` item 8 accepts **either** ("via `data-replay-loaded="true"` **or** the
`coworld-replay` bridge's `ready`"). The attribute is set in the shell's own source, which was
fetched from the live bundle this pass:

```
grep -n 'data-replay-loaded' static_replay.js
144:          document.documentElement.setAttribute('data-replay-loaded', 'true');
```
with context showing it fires only on the worker's `loaded` message, immediately before the first
`requestAnimationFrame(animate)`:
```
        } else if (message.type === 'loaded') {
          setMismatchTick(message.mismatchTick);
          loaded = true;
          document.documentElement.setAttribute('data-replay-loaded', 'true');
          requestAnimationFrame(animate);
```
A grep of the whole live bundle for `coworld-replay` returns nothing in `index.html`,
`static_replay.js`, `chrome_common.js`, `broadcast_core.js` or `static_replay_worker.js` — this
shell simply does not implement the postMessage bridge, which the prompt permits. `data-replay-error`
is `null`, so the shell also reports no error path taken.

**Supporting: every asset the shell references, fetched live from the same bundle root**
(`…/static/cow_ff38b98b-f611-4a74-86e1-f2b23cbd6339/sha256%3A495905b1…/`):

| URL (relative to bundle root) | HTTP | bytes | content-type |
|---|---|---|---|
| `index.html` | 200 | 146 155 | text/html |
| `wire_constants.js` | 200 | 153 | text/javascript |
| `chrome_common.js` | 200 | 30 637 | text/javascript |
| `static_replay.js` | 200 | 9 203 | text/javascript |
| `static_replay_worker.js` | 200 | 7 160 | text/javascript |
| `broadcast_core.js` | 200 | 62 248 | text/javascript |
| `cogball_replay.js` | 200 | 68 784 | text/javascript |
| `cogball_replay.wasm` | 200 | 554 655 | application/wasm |
| `font.ttf` | 200 | 390 340 | application/octet-stream |

Reference chain actually walked (not guessed): `index.html` → `<script src>` ×3
(`wire_constants.js`, `chrome_common.js`, `static_replay.js`) and `'./font.ttf'`;
`static_replay.js` → `'./static_replay_worker.js'`; the worker → `'./broadcast_core.js'`,
`'./cogball_replay.js'`, `'./wire_constants.js'`; the emscripten loader in `cogball_replay.js`
names `"cogball_replay.wasm"` (`wasmBinaryFile ??= findWasmBinary()`). All 200, all non-trivial;
the wasm is a real module — `file cogball_replay.wasm` → `WebAssembly (wasm) binary module
version 0x1 (MVP)` — not an HTML error page.

### (c) The replay JSON the viewer was asked to draw

From `/tmp/ep.replay` of check 4 (the same S3 object the `?replay=` parameter points at).
`turn / seat / alias / source / latency_ms / note` —

**Early (turns 0–2):**
```
0	0	Azure	llm	4680	Kickoff: AZ-1 nearest to ball (1.5m) takes the attack. AZ-2 positioned as support interceptor. AZ-3 drops to keeper role covering near post.
0	1	Crimson	llm	4680	Game start: deploy defensive shape. CR-1 keeper on goal line, CR-2 back at midfield anchor, CR-3 presses nearest opponent (AZ-1).
1	0	Azure	llm	2162	AZ-2 closest to ball (2.6m) in their half - shoot to capitalize. AZ-1 support intercept. AZ-3 keeper on arc.
1	1	Crimson	llm	2162	Ball loose in our half, moving toward goal. CR-1 keeper holds. CR-2 back holds midfield anchor. CR-3 presses AZ-2 (closest to ball at 2.6m). Defensive shape ma…
2	0	Azure	llm	2875	AZ-1 closest (1.35m), in their half - SHOOT now. AZ-2 support intercept at 8m upfield. AZ-3 keeper on arc.
2	1	Crimson	llm	2875	Ball loose, moving toward our goal at 6.88,-0.41. CR-3 closest at 1.99m. AZ-1 very close at 1.35m—expect hard contest. Maintain deep shape: CR-1 keeper holds g…
```

**Middle (turns 20–21 — the ticks behind the 50 % scrub readout `1:38 TURN 21/40`):**
```
20	0	Azure	llm	2275	AZ-3 closest (5.8m) - SHOOT at goal. AZ-2 keeper on arc. AZ-1 support intercept.
20	1	Crimson	llm	2275	CR-2 has loose ball at [-11,-6]. AZ-3 closest at 5.8m. Switch back to defensive shape: CR-1 keeper, CR-2 back holding midfield, CR-3 presses AZ-3. Win ball, co…
21	0	Azure	llm	2130	AZ-3 closest (6.72m) but in their half - CHASE to pressure. AZ-1 support intercept upfield. AZ-2 keeper on arc.
21	1	Crimson	llm	2130	Ball loose at x=15, in our half. AZ-1 closest at 3.57m. Switch to ATTACK: CR-1 keeper holds, CR-2 wing intercepts up-field far side, CR-3 shoots at goal. Win a…
```

**Late (turns 38–39):**
```
38	0	Azure	llm	1990	AZ-3 closest (3.64m) to ball in our half - chase and pressure. AZ-1 (4.42m) intercept support ahead upfield. AZ-2 keeper on arc covering near post.
38	1	Crimson	llm	1990	Ball loose in their half, AZ-3 closest (3.64m). Maintain compact 2-back defense: CR-1 keeper holds arc, CR-2 holds midfield. CR-3 presses AZ-3 hard to win poss…
39	0	Azure	llm	2162	AZ-2 closest (2.31m) to ball - shoot to clear dangerous position. AZ-3 (2.42m) support intercept. AZ-1 keeper on arc covering near post at y≈0.9.
39	1	Crimson	llm	2162	Ball loose near their goal, AZ-2 closest (2.31m). CR-3 presses to win it. If we gain possession, switch to counter attack with CR-2 as wing intercepting space.
```

```
jq -r '.results' /tmp/ep.json
{"names":["daveey","daveey-1"],"scores":[0.5,0.5],"win":[false,false],"team":["azure","crimson"],"goals":[1,1],"shots":[15,1],"shotsOnTarget":[6,1],"saves":[0,0],"possessionTicks":[2803,1782],"llmTurns":[40,40],"fallbackTurns":[0,0],"reason":"complete","endRule":"full_time","finalTick":5106,"seed":1770193400}
```

### The spectator-judgment paragraph

**It is legible, it moves, and it is unmistakably a football match.** The screenshot
(`runs/2026-08-22-cogball/viewer-check/viewer-smoke.png`, 352 960 B, captured by the headless
chromium run above) shows a finished game, not a blank canvas or a loading stall: a dark pitch
with centre circle, both penalty boxes and both goals drawn, the six robots visible as three blue
and three red bodies with the ball between them, a header scorebug reading `1 · DAVEEY` on the
left against `DAVEEY-1 · 1` on the right with per-team shot and possession chips (`15 sh 61%` /
`1 sh 38%`), and a large centred full-time card reading **`DRAW`**, **`1–1 · FULL TIME`**,
`reason: complete`, above two per-team stat panels (daveey: goals 1, shots on target 15 (6),
saves 0, possession 61 %, score 0.500; daveey-1: goals 1, shots 1 (1), saves 0, possession 38 %,
score 0.500). Beneath it sit working transport controls — step-back, play, `+5s`, loop, speed
selectors `1×…16×` — a `4912 / 4920` tick counter, and a `GOAL LEAD` momentum strip that swings
from blue to red across the timeline. Those numbers reconcile **exactly** with the replay's own
`results` above (`goals [1,1]`, `shots [15,1]`, `shotsOnTarget [6,1]`, `possessionTicks
[2803,1782]` → 61 %/38 %, `scores [0.5,0.5]`, `reason "complete"`, `endRule "full_time"`), so the
picture is genuinely being drawn from these bytes and not from a placeholder. That it **advances**
rather than freezing on one frame is established by the three differing scrub clocks — `3:20 TURN
1/40` at 0 %, `1:38 TURN 21/40` at 50 %, `FINAL GAME OVER` at 100 % — the exact failure mode
(freeze on tick 2) that killed 0.1.4 and is now gone. The one soft spot is `feed_lines: 0`: the
commentary feed was empty at the moment of capture, so the spectator reads the *what* (score,
shots, possession, momentum) off the scorebug and stat card but not the LLM's *why*, even though
the replay carries 80 richly-argued directives ("AZ-3 closest (5.8m) - SHOOT at goal", "Switch to
ATTACK: CR-1 keeper holds, CR-2 wing intercepts up-field far side") that would make excellent feed
copy. That is a legibility note for a future iteration, not a failure of this check: the viewer
loaded in 4 122 ms, threw no console error and no `data-replay-error`, and renders a complete,
readable, advancing account of a 1–1 draw between the two champions.

Status: **TRUE** — `loaded: true` (condition 1) **and** the three clock readouts differ
(condition 2), from a run dispatched this pass against check 6's exact iframe `src`.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — 16 completed, 0 failed/discarded, all after 05:42:09Z |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey #1, daveey-1 #2, 16 rounds each, fillers absent |
| 3 | Latest round's episode completed with replay | **TRUE** — `ereq_21ccb33a…` completed, replay present, both champions seated |
| 4 | Replay bytes valid and show the game | **TRUE** — strict JSON via the design-declared summary tool, `cogball/v1`, `complete`, 80/80 LLM, 0 fallbacks |
| 5 | Hosted game log clean | **TRUE** — `CLEAN`, no exception claimed |
| 6 | Public page uses the static replay path | **TRUE** — static route, `cow_ff38b98b` + manifest sha, featured match `cogball.r16.e1` |
| 7 | Certification declared the static bundle | **TRUE** — `Replay liveness: skipped (static replay bundle declared…` from the committed 0.1.5 artifact |
| 8 | Spectator judgment (viewer executed) | **TRUE** — run `32631291526`, `loaded:true` in 4 122 ms, three differing clocks, full-time card renders |

No item is NOT FETCHED. No undocumented exception is claimed anywhere. The single documented
substitution is check 4's binary-replay summary tool, declared in
`runs/2026-08-22-cogball/design.md` §"Replay bytes (self-sufficient)" and quoted above.
