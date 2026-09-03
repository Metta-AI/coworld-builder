# VERIFY — coins   (2026-09-03T19:22:23Z)

Verdict: **all-true** (8/8 TRUE)

This is a **re-verification**. The 2026-08-25 pass found checks 1, 2, 3, 6, 7, 8 TRUE and checks
4 and 5 FALSE, solely because of a platform-wide AWS Bedrock `claude-haiku` daily-token 429
throttle that turned 41 of 48 champion decisions into scripted fallbacks. The operator confirmed
on 2026-09-03 that the quota is restored. **All eight checks below were re-fetched fresh this run**
against the freshest completed round (**round 194**, created `2026-09-03T16:36:11Z`), except the
two documented exceptions: check 7 (the committed `release-result.json` artifact of this run's
phase 40) and check 8's rendered evidence (the `viewer-check.yml` run **33795836783** dispatched
by this pass at `2026-09-03T19:20:15Z`).

Constants used throughout:

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")   # value never printed
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_e9506fcc-08c3-4372-90ac-0ced465c7d9c
D=div_d7a79bf3-f8b7-40f7-b838-45aa275d7913
COW=cow_e5c32ad5-8696-4d4f-8a39-458baa8c2a3e     # STATE's coworld, v0.1.2
R=round_c2415ebd-6016-4871-9459-2faa70101819     # round 194, the freshest completed round
EREQ=ereq_5af03905-fb2c-42ad-b3a2-167d65a28299   # champion-vs-champion episode of round 194
```

> **Read this before the checks — the canonical coworld has moved on.**
> `GET $BASE/coworlds?limit=200` now reports the canonical `coins` coworld as
> **`cow_bd320430-6cf8-4f45-8adb-06de80fbe100`, version `0.1.4`**, manifest hash
> `sha256:6b286bdb0014f6bb1318c3720ce1bcb09949351120d3e0974d480d1cab19bef9` — not STATE's
> `cow_e5c32ad5…` v0.1.2 / `sha256:a0ef3142…`. The v0.1.4 manifest still names
> `"owner":"daveey@softmax.com"` and `"source_url":"https://github.com/Metta-AI/cogame-coins/tree/39cf1ade7666359629fb65f2edf6cc0f40e800c1"`,
> i.e. it is the same coworld from the same repo at a later release, and it still declares a
> **static** replay viewer (`"replay_viewer":{"bundle":"sha256:717b28a9…"}`). Every episode in
> round 194 carries `coworld_id: cow_bd320430…`, and `POST /coworlds/replays/session` **404s** on
> the v0.1.2 id (evidence in check 6). Checks 3–6 and 8 are therefore judged against the coworld
> the league and the public page are actually running today; the discrepancy with STATE is
> flagged here rather than silently absorbed. Check 7 is judged against this run's own v0.1.2
> release artifact, as the prompt requires.

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

Fillers were registered at `2026-08-25T01:56:08Z`, **before round 1**
(`runs/2026-08-24-coins/log.md`: `2026-08-25T01:56:08Z 50 fillers 200: a652fffc (reciprocator:v2)
+ 9356e1ac (titfortat:v2) registered; neither champion in list`). Re-fetched fresh this run, they
are still the two registered fillers and neither is a champion:

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"a652fffc-1816-448b-aeac-cdb6a9ba6840","policy_id":"93f81540-803a-40d6-b1e7-1db40553dfb9","policy_name":"coins-reciprocator","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},
 {"policy_version_id":"9356e1ac-3ed0-443b-a7da-b8685941ffcf","policy_id":"36c09d66-f3ee-46dc-ac3a-24e62c2a221d","policy_name":"coins-titfortat","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```
HTTP 200.

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" -o /tmp/v/rounds.json -w "HTTP %{http_code}\n"
# HTTP 200 — body shape is {"entries":[…]} on this call (the bare-array shape is handled too)
jq -r '(if type=="array" then . else .entries end)|.[]|[.round_number,.id,.status,(.error//"null"),.created_at,.completed_at//"-"]|@tsv' /tmp/v/rounds.json
```
```
194	round_c2415ebd-6016-4871-9459-2faa70101819	completed	null	2026-09-03T16:36:11.999153Z	2026-09-03T16:39:33.931650Z
193	round_df7157de-005d-4cb7-852d-f593c359c89e	completed	null	2026-09-03T11:48:10.111365Z	2026-09-03T11:51:08.508733Z
192	round_7ef8aac1-723f-41d7-aa04-b23f4d27d04d	completed	null	2026-09-03T07:00:08.475171Z	2026-09-03T07:08:14.062840Z
191	round_97e26a59-7447-4f76-9f26-7d46529a55b9	completed	null	2026-09-02T21:24:07.210828Z	2026-09-02T21:27:06.706827Z
190	round_ddc2a804-462c-4e3f-a7d7-01379a530d3f	completed	null	2026-09-02T16:36:06.692550Z	2026-09-02T16:38:53.069449Z
189	round_4c8fe5b3-4f8b-4ba6-b426-e5234b752008	completed	null	2026-09-02T11:48:05.986356Z	2026-09-02T11:51:02.906557Z
188	round_437d615d-b49d-4990-9747-81907eb2071d	completed	null	2026-09-02T07:00:05.444203Z	2026-09-02T07:11:34.123024Z
187	round_3295047c-75a9-441e-8662-5128d25864d8	completed	null	2026-09-01T22:34:44.055468Z	2026-09-01T22:37:49.553834Z
186	round_194968b3-36d7-4412-be75-269d3d686248	completed	null	2026-09-01T17:46:40.330874Z	2026-09-01T17:49:28.574516Z
185	round_5248ed64-80c9-4ca2-b5f5-146c359db3af	completed	null	2026-09-01T12:58:39.592489Z	2026-09-01T13:01:31.652342Z
184	round_868151f4-e2d6-4bf1-a8b5-379395140cd6	completed	null	2026-09-01T08:10:35.030375Z	2026-09-01T08:13:46.525561Z
183	round_69fd6f62-74dc-438c-a7da-3e7b8a9336b5	completed	null	2026-09-01T03:22:33.936576Z	2026-09-01T03:25:35.450929Z
182	round_3bc8c4f0-783a-4481-b642-efb94ab17c43	completed	null	2026-08-31T22:34:33.363757Z	2026-08-31T22:37:08.413060Z
181	round_0ad74395-78ef-4ba6-bcd9-82768ccfaba9	completed	null	2026-08-31T17:46:32.810472Z	2026-08-31T17:51:09.586761Z
180	round_03241b85-d981-4f15-8023-179d3546a432	completed	null	2026-08-31T12:58:32.311705Z	2026-08-31T13:01:27.827087Z
179	round_717ecf68-bfa1-46c3-9792-c9a5e5574566	completed	null	2026-08-31T08:10:30.769459Z	2026-08-31T08:13:35.755716Z
178	round_f73d4f67-84d1-409f-9a18-f273268c09ca	completed	null	2026-08-31T03:22:30.184246Z	2026-08-31T03:25:11.084853Z
177	round_8d70a418-7243-464b-8671-6f8f68364da9	completed	null	2026-08-30T22:34:25.851318Z	2026-08-30T22:37:22.131553Z
176	round_a6173f09-af02-4b71-9a0c-2d31be5fff4c	completed	null	2026-08-30T17:46:25.206054Z	2026-08-30T17:49:01.380618Z
175	round_0274bcbe-2991-4994-b4c6-b85b897370fd	completed	null	2026-08-30T12:58:23.491712Z	2026-08-30T13:01:19.156062Z
```
```bash
jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length' /tmp/v/rounds.json   # -> 20
jq -r '[(if type=="array" then . else .entries end)[]|select(.status!="completed")]|length' /tmp/v/rounds.json   # -> 0
```

Status: **TRUE** — the most recent page of 20 rounds (175–194) is **20/20 `completed`, 0
failed/discarded, every `error` null**; the league has run to round **194**. All of them are after
round 1, and the fillers were set before round 1. Requirement is ≥ 2. Cadence note: the last four
rounds are ~4h48m apart (16:36Z, 11:48Z, 07:00Z, 2026-09-02T21:24Z), not the configured 15 min —
recorded as an observation, not a check.

---

## 2. Both champions ranked; fillers absent or Baseline — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}"     # HTTP 200, bare JSON list
```
```json
[
 {"rank":1,"player_id":"ply_ded11f40-3e30-4921-b019-f7f6bc3e9c83","player_name":"richard","score":1358.5187167773818,"score_label":"MMR","rounds_played":181,"episode_wins":394.0,"win_rate":0.6924428822495606,"policy_label":"co-gas-coins-reciprocator-richard:v9"},
 {"rank":2,"player_id":"ply_18302115-9fc9-482d-a2f3-f4c592bf9e57","player_name":"relh","score":1271.4852589912814,"score_label":"MMR","rounds_played":181,"episode_wins":421.0,"win_rate":0.7398945518453427,"policy_label":"co-gas-coins-reciprocator-relhalpha:v3"},
 {"rank":3,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":920.3758481043894,"score_label":"MMR","rounds_played":192,"episode_wins":192.0,"win_rate":0.3316062176165803,"policy_label":"coins-ledger:v2"},
 {"rank":4,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":914.08812814088,"score_label":"MMR","rounds_played":193,"episode_wins":155.0,"win_rate":0.2667814113597246,"policy_label":"coins-truce:v2"},
 {"rank":5,"player_id":"ply_3d22435e-30a2-4f2a-b037-a5c249583788","player_name":"Andre von Auto","score":874.6069400818528,"score_label":"MMR","rounds_played":12,"episode_wins":19.0,"win_rate":0.30158730158730157,"policy_label":"morozko:v1"},
 {"rank":6,"player_id":"ply_ac7e5318-5781-4ed6-8fc9-d9f66d6b1637","player_name":"Andrew Brower","score":868.2133037073991,"score_label":"MMR","rounds_played":12,"episode_wins":18.0,"win_rate":0.2857142857142857,"policy_label":"coins-example:v1"},
 {"rank":7,"player_id":"ply_176e1e1a-7af8-40f7-9ee3-a67b96690ad6","player_name":"docxology","score":792.7118041968178,"score_label":"MMR","rounds_played":3,"episode_wins":1.0,"win_rate":0.05555555555555555,"policy_label":"daf-coins:v1"}
]
```

Status: **TRUE** —
- `daveey` / `coins-truce:v2` — rank 4, `rounds_played` **193** ≥ 1, 155 episode wins.
- `daveey-1` / `coins-ledger:v2` — rank 3, `rounds_played` **192** ≥ 1, 192 episode wins.
- Fillers **absent**: no row has `policy_label` `coins-reciprocator:v2` or `coins-titfortat:v2`
  and no row is labelled `Baseline`. (Rank 1–2's `co-gas-coins-reciprocator-*` are *other players'*
  submitted policies — `player_name` `richard` / `relh`, different `policy_id`s
  `a49bd427…` / `382598b9…` — not this run's fillers `93f81540…` / `36c09d66…`.)

Change since 2026-08-25: the division is no longer champions-only. Five outside entrants
(`richard`, `relh`, `Andre von Auto`, `Andrew Brower`, `docxology`) have joined the ladder and two
of them now out-rank both champions. That is other humans playing the coworld, not a defect; it is
why the fillers are never seated (7 real entrants in a 2-seat game).

---

## 3. Latest round's episode request completed with a replay — **TRUE**

The flat route is dead, as `playbooks/observatory-api.md` §9 records; the nested route was used:

```bash
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}"
# HTTP 405  {"detail":"Method Not Allowed"}
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}"     # HTTP 200, 21 entries, all "completed"
```

Round 194 is a full round-robin over the 7 ranked entrants → 21 episode requests, **21/21
`status:"completed"`**. The champion-vs-champion pairing is `ereq_5af03905-…`:

```bash
curl -sS "$BASE/episode-requests/ereq_5af03905-fb2c-42ad-b3a2-167d65a28299" "${AUTH[@]}" \
 | jq '{id,status,coworld_id,coworld_name,round_id,created_at,completed_at,replay_url,participants,participant_scores}'
```
```json
{
  "id": "ereq_5af03905-fb2c-42ad-b3a2-167d65a28299",
  "status": "completed",
  "coworld_id": "cow_bd320430-6cf8-4f45-8adb-06de80fbe100",
  "coworld_name": "coins",
  "round_id": "round_c2415ebd-6016-4871-9459-2faa70101819",
  "created_at": "2026-09-03T16:36:12.610158Z",
  "completed_at": "2026-09-03T16:37:59.651123Z",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/abaf7183-5415-4403-8714-74cd41509e62.replay",
  "participants": [
    {"position":0,"kind":"policy","policy_version_id":"2da8b581-6545-4809-b43d-b8958e9015ff","policy_name":"coins-truce","version":2,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","is_filler":false,"is_seed":false},
    {"position":1,"kind":"policy","policy_version_id":"794abef0-f60a-49a2-83d0-21df66e9ff51","policy_name":"coins-ledger","version":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","is_filler":false,"is_seed":false}
  ],
  "participant_scores": [{"position":0,"score":13.0},{"position":1,"score":10.0}]
}
```

The other champion episodes in the same round (fetched, listed here so the pick is not cherry-picked):

```
ereq_733f495d-…  completed  coins-truce:v2 (daveey)   vs co-gas-coins-reciprocator-richard:v9 (richard)
ereq_fb33771b-…  completed  coins-truce:v2 (daveey)   vs coins-example:v1 (Andrew Brower)
ereq_e6af036b-…  completed  morozko:v1 (Andre von Auto) vs coins-truce:v2 (daveey)
ereq_972f754e-…  completed  co-gas-…-relhalpha:v3 (relh) vs coins-truce:v2 (daveey)
ereq_8550a0ff-…  completed  daf-coins:v1 (docxology)  vs coins-truce:v2 (daveey)
ereq_f4edf43b-…  completed  coins-ledger:v2 (daveey-1) vs co-gas-…-richard:v9 (richard)
ereq_cccb8e67-…  completed  coins-example:v1 (Andrew Brower) vs coins-ledger:v2 (daveey-1)
ereq_194efd0d-…  completed  morozko:v1 (Andre von Auto) vs coins-ledger:v2 (daveey-1)
ereq_6aac65cb-…  completed  co-gas-…-relhalpha:v3 (relh) vs coins-ledger:v2 (daveey-1)
ereq_d937b7c0-…  completed  daf-coins:v1 (docxology)  vs coins-ledger:v2 (daveey-1)
```

Status: **TRUE** — `status == "completed"`, `replay_url` non-null, and `participants` name
`daveey` (`coins-truce:v2`, seat 0) and `daveey-1` (`coins-ledger:v2`, seat 1). No filler is
seated in any of the 21 episodes (`is_filler:false` everywhere) — correct for a 2-seat game with
7 real entrants.

---

## 4. Replay bytes are valid and show the game — **TRUE** (was FALSE on 2026-08-25)

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/abaf7183-5415-4403-8714-74cd41509e62.replay" -o /tmp/v/ep.replay
# HTTP 200 bytes=36017
jq -e . /tmp/v/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
```
```
strict UTF-8 JSON: ok
```
```bash
jq -r '.protocol, .game, .gameVersion, .results.reason' /tmp/v/ep.replay
jq -r 'keys|join(" ")' /tmp/v/ep.replay
```
```
coins.replay.v1
coins
1
random_end
beats beatsTimeline colours config endBeat events frames game gameVersion indices lulls names policyNames protocol results room seed series ticksPlayed variant
```

`protocol` = `coins.replay.v1`, exactly the string `design.md` §Replay pins
(`{"protocol":"coins.replay.v1","game":"coins","gameVersion":"1",…}`). The v0.1.4 manifest declares
no replay-protocol string of its own (its `game.protocols` are `player`/`global` only), so the
manifest-side contract that *is* checkable is the results schema, and the reason value satisfies it:

```bash
jq -c '.manifest.game.results_schema.properties.reason' /tmp/v/cowdetail.json
# {"enum":["random_end","beat_cap","deadline","forfeit"],"type":"string"}
```
`results.reason == "random_end"` — a legal value per the manifest enum and per `design.md`
§"End conditions and the legal `results.reason` values". Not a `deadline`, so no design exception
is being invoked.

**The key question — are the decisions LLM decisions or scripted fallbacks?**

```bash
jq -c '[.events[]|select(.k=="order")|.source]|group_by(.)|map({(.[0]):length})|add' /tmp/v/ep.replay
jq -r '[.events[]|select(.fallback==true)]|length' /tmp/v/ep.replay
jq -c '[.events[]|select(.k=="order")|.intent]|group_by(.)|map({(.[0]):length})|add' /tmp/v/ep.replay
jq -c '[.events[]|.k]|group_by(.)|map({(.[0]):length})|add' /tmp/v/ep.replay
jq -c '[.events[]|select(.k=="order")|.latencyMs]|{min:min,max:max,avg:(add/length)}' /tmp/v/ep.replay
```
```
{"llm":24}
0
{"take_mine":23,"take_theirs":1}
{"beatclose":12,"blocked":3,"end":1,"leadchange":10,"order":24,"pickup":24,"spawn":19,"theft":1}
{"min":1630,"max":4204,"avg":2291.9166666666665}
```

**24 of 24 order decisions have `source:"llm"`. Zero fallbacks. Zero `fallback:true` events.**
(On 2026-08-25 the same measurement was 41 fallback / 48 — that is what made this check FALSE.)

Decision content is non-trivial — each order carries a `say` (broadcast to the opponent) and a
`notes` reasoning block that references board coordinates, the opponent's theft counter and the
score gap:

```json
{"k":"order","t":0,"beat":1,"seat":0,"intent":"take_mine","source":"llm",
 "say":"Open restrained - taking only copper",
 "notes":"Beat 1: Established take_mine as opening move per truce protocol. Cobalt at (7,7), I'm at (1,1). Nearest copper is at (4,6), distance 9 steps via Manhattan. Cobalt coin at (2,1) is adjacent to me but I won't take it - must demonstrate restraint. Cobalt theft counter: 0. …",
 "latencyMs":4204}
{"k":"order","t":0,"beat":1,"seat":1,"intent":"take_mine","source":"llm",
 "say":"Opening move: securing my coins",
 "notes":"LEDGER: Beat 1 start - Cobalt (me) 0 taken, Copper 0 taken. Score gap: 0. My coins on board: (2,1), (3,2), (3,4). Their coins: (4,6), (6,4), (6,3). Nearest my coin: (3,2) at ~4 steps. Playing take_mine default. No thefts yet - pursuing standard strategy.",
 "latencyMs":4204}
{"k":"order","t":20,"beat":2,"seat":0,"intent":"take_mine","source":"llm",
 "say":"Truce holds. Your theft counter: 0. Mine: 0.", "latencyMs":2274}
```

And the game's *subject matter* actually happens: three `blocked … "why":"restraint"` events
(a seat declining a coin it could have stolen), then one real theft at beat 12:

```json
{"k":"blocked","t":0,"seat":0,"x":2,"y":1,"why":"restraint"}
{"k":"blocked","t":6,"seat":0,"x":3,"y":2,"why":"restraint"}
{"k":"blocked","t":9,"seat":1,"x":6,"y":4,"why":"restraint"}
{"k":"theft","t":223,"seat":1,"victim":0,"x":6,"y":6,"colour":"copper","penalty":2,"score":[12,10]}
{"k":"end","t":239,"beat":12,"reason":"random_end","score":[13,10]}
```

`results`:
```json
{"names":["coins-player","coins-player"],"scores":[13.0,10.0],"win":[true,false],
 "aliases":["Copper","Cobalt"],"colours":["copper","cobalt"],
 "pickups":[15,10],"thefts":[0,1],"stolenFrom":[1,0],"restraint":[1.0,0.9],
 "firstTheftBeat":[null,12],"reciprocityLagBeats":[null,null],
 "beats":12,"endBeat":12,"ticks":240,"reason":"random_end"}
```

**Trend across the four most recent completed rounds** (each the `coins-truce:v2` vs
`coins-ledger:v2` episode of that round; each replay downloaded and parsed this run):

| round | episode request | replay | order-source distribution | reason | scores | thefts |
|---|---|---|---|---|---|---|
| 194 | `ereq_5af03905-…` | `abaf7183-…` | `{"llm":24}` | random_end | 13–10 | [0, 1] |
| 193 | `ereq_cad25b68-…` | `e55eb482-…` | `{"llm":32}` | random_end | 11–20 | [0, 0] |
| 192 | `ereq_6913704b-…` | `c5b2b18b-…` | `{"llm":30}` | random_end | 9–10 | [0, 3] |
| 191 | `ereq_7a97023c-…` | `cee3ecc7-…` | `{"llm":24}` | random_end | 8–9 | [1, 3] |

**110 of 110 order decisions across four rounds are `source:"llm"`; zero fallbacks.** The
2026-08-25 finding "thefts:[0,0] every round — all-fallback rooms never steal" is gone: three of
these four rounds contain real thefts.

Status: **TRUE** — strict UTF-8 JSON parse ok; `protocol` `coins.replay.v1` as designed;
`results.reason` `random_end`, a legal value; champion decisions are 100 % non-scripted with
substantive content (fallbacks are 0 % of decisions, not merely a small minority).

---

## 5. Hosted game log is clean — **TRUE** (was FALSE on 2026-08-25)

```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/v/logs_raw.txt
# HTTP 200 bytes=4791
```
The body is python `b'…'` byte-string reprs under `===== container: … =====` headers
(`playbooks/observatory-api.md` §10), so it was decoded with `ast.literal_eval` per repr before
grepping. Raw grep found 0 matches and so did the decoded grep — but only the decoded number is
evidence:

```bash
grep -nEc 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/v/logs_raw.txt      # 0 (raw — not evidence)
python3 decode.py /tmp/v/logs_raw.txt /tmp/v/logs_decoded.txt
grep -nE  'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/v/logs_decoded.txt || echo CLEAN
```
```
CLEAN
```
```bash
grep -niE '429|throttl|error|warn|timeout|retry' /tmp/v/logs_decoded.txt
```
```
7:2026-09-03 16:36:30,788 INFO hypercorn.error Running on http://127.0.0.1:9100 (CTRL + C to quit)
```
(the single hit is the hypercorn logger *name*, not an error).

The full decoded log, all four containers, 56 non-blank lines — pasted because it is short and it
is the direct refutation of the 2026-08-25 failure:

```
===== container: coworld-init-config =====

===== container: bedrock-sidecar =====
2026-09-03 16:36:30,529 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1","has_role_arn":true,"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar","episode_request_id":"5af03905-fb2c-42ad-b3a2-167d65a28299","job_request_id":"abaf7183-5415-4403-8714-74cd41509e62","role":"game","slot":"game","image_digest":"sha256:dc5ae2e17b1e010dc1fbce30b4d1de30526a0885568df243f222ad77efa0a8ba"}
[2026-09-03 16:36:30 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-09-03 16:36:30,788 INFO hypercorn.error Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-09-03 16:36:38,227 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:36:40,430 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:36:43,121 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:36:43,175 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:36:48,138 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:36:48,195 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:36:53,122 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:36:53,457 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:36:58,050 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:36:58,193 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:37:03,083 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:37:03,216 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:37:08,113 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:37:08,128 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:37:13,165 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:37:13,215 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:37:18,108 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:37:18,203 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:37:23,125 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:37:23,144 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:37:28,142 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:37:28,148 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:37:33,121 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 16:37:33,234 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"

===== container: game =====
coins: seats=2 variant=standard beats=12..24 endChance=120 coinCap=8 theftPenalty=2 seed=1571499063
coins: serving on 0.0.0.0:8080
coins: player slot 0 connected (1/2)
coins: slot 0 registered (1037 prompt chars, llm)
coins: slot 0 registered (1037 prompt chars, llm)
coins: player slot 1 connected (2/2)
coins: slot 1 registered (940 prompt chars, llm)
coins: slot 1 registered (940 prompt chars, llm)
coins: starting with 2/2 players connected
coins llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
coins: beat 1 tick 20 score 1-0 thefts 0/0 at 10s
coins: beat 2 tick 40 score 3-3 thefts 0/0 at 13s
coins: beat 3 tick 60 score 4-5 thefts 0/0 at 18s
coins: beat 4 tick 80 score 6-6 thefts 0/0 at 23s
coins: beat 5 tick 100 score 6-6 thefts 0/0 at 28s
coins: beat 6 tick 120 score 7-7 thefts 0/0 at 33s
coins: beat 7 tick 140 score 8-7 thefts 0/0 at 38s
coins: beat 8 tick 160 score 9-7 thefts 0/0 at 44s
coins: beat 9 tick 180 score 10-8 thefts 0/0 at 48s
coins: beat 10 tick 200 score 12-9 thefts 0/0 at 53s
coins: beat 11 tick 220 score 12-9 thefts 0/0 at 59s
coins: beat 12 tick 240 score 13-10 thefts 0/1 at 63s
coins: writing results and replay (36017 bytes)
coins: episode complete (random_end) after 240 ticks, 12 beats, score 13-10
coins: holding /healthz and /global for 20s

===== container: worker =====
```

Status: **TRUE — CLEAN.** Zero matches for `falling back`, `LLM provider is unavailable`,
`cut off at max_tokens`, `rejected` in the *decoded* text. All **24** sidecar LLM calls returned
`HTTP/1.1 200 OK` (24 successes = the 24 `source:"llm"` orders in check 4 — the two records agree
exactly). Both seats registered `llm` (`1037` and `940` prompt chars). No 429, no
ThrottlingException, no retry storm — the Bedrock daily-token throttle that failed this check on
2026-08-25 is gone, so no cross-check against another LLM coworld was needed. The episode
finished in 63 s against a 720 s play deadline.

---

## 6. The public page uses the static replay path — **TRUE**

**Source used: the SSR playlist payload + the session endpoint** (both, below). The raw-HTML
iframe grep was tried first and found nothing, which per the playbook is *unknown*, not a failure:

```bash
curl -sS "https://softmax.com/coins" -o /tmp/v/page.html      # HTTP 200 bytes=911568
grep -o '<iframe[^>]*src="[^"]*"' /tmp/v/page.html || echo "NO IFRAME IN RAW HTML (client-rendered)"
```
```
NO IFRAME IN RAW HTML (client-rendered)
```

**(a) Featured match — server-rendered into the page's SSR payload at `state.playlist[0]`**
(extracted from `/tmp/v/page.html`, unescaped):

```json
[
  {
    "episodeId": "61e3128a-b970-4bb9-afd7-279eaaa22667",
    "coworldId": "cow_bd320430-6cf8-4f45-8adb-06de80fbe100",
    "coworldName": "coins",
    "coworldVersion": "0.1.4",
    "replayUrl": "https://softmax-public.s3.amazonaws.com/replays/29ed2e34-ee0a-4494-8b5b-634389793c47.replay",
    "finishedAt": "2026-09-03T16:37:02.796289Z",
    "roundNumber": 194,
    "episodeNumber": 11,
    "code": "coins.r194.e11",
    "inspectUrl": "/observatory/v2?tab=overview&detail=episode-request:ereq_8614ca36-8e1f-4c5b-966d-d765a0549f99",
    "outcome": "second"
  }
]
```
A featured match **is present**: `coins.r194.e11`, from today's round 194, the top-two matchup
(`richard` rank 1 vs `relh` rank 2 — the page pairs the leaderboard's first and second, both
present, so the "fewer than two ranked players" absence case does not apply). The same payload
carries `"leagueId":"league_e9506fcc-08c3-4372-90ac-0ced465c7d9c"` — this run's league.

**(b) The iframe `src` the page's JS resolves** — `POST $BASE/coworlds/replays/session`, run three
ways:

```bash
# A — the page's own featured match
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_bd320430-6cf8-4f45-8adb-06de80fbe100","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/29ed2e34-ee0a-4494-8b5b-634389793c47.replay"}'
```
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_bd320430-6cf8-4f45-8adb-06de80fbe100/sha256%3A6b286bdb0014f6bb1318c3720ce1bcb09949351120d3e0974d480d1cab19bef9/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F29ed2e34-ee0a-4494-8b5b-634389793c47.replay","ready":true}
```
HTTP 200.

```bash
# B — the check-3/4 champion-vs-champion replay (this is the src fed to check 8)
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_bd320430-6cf8-4f45-8adb-06de80fbe100","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/abaf7183-5415-4403-8714-74cd41509e62.replay"}'
```
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_bd320430-6cf8-4f45-8adb-06de80fbe100/sha256%3A6b286bdb0014f6bb1318c3720ce1bcb09949351120d3e0974d480d1cab19bef9/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fabaf7183-5415-4403-8714-74cd41509e62.replay","ready":true}
```
HTTP 200.

```bash
# C — STATE's coworld id (v0.1.2), for the record
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_e5c32ad5-8696-4d4f-8a39-458baa8c2a3e","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/abaf7183-5415-4403-8714-74cd41509e62.replay"}'
```
```json
{"detail":"Replay for Coworld cow_e5c32ad5-8696-4d4f-8a39-458baa8c2a3e not found"}
```
HTTP 404 — the v0.1.2 coworld no longer serves the current replays; the canonical is v0.1.4
(see the banner at the top of this file).

And the canonical row the page reads:
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" | jq -c '(if type=="array" then . else .entries end)|.[]|select(.name=="coins")'
```
```json
{"id":"cow_bd320430-6cf8-4f45-8adb-06de80fbe100","name":"coins","version":"0.1.4","canonical":true,"manifest_hash":"sha256:6b286bdb0014f6bb1318c3720ce1bcb09949351120d3e0974d480d1cab19bef9","replay_viewer":null,"featured_match":null}
```
(`replay_viewer`/`featured_match` are `null` on the list row platform-wide, as the playbook
records — not evidence either way. The coworld **detail** call does carry the viewer declaration:
`GET $BASE/coworlds/cow_bd320430-…` → `.manifest.game.replay_viewer` =
`{"bundle":"sha256:717b28a991140559b09191fbadf700ba2fa3b2081cd136561f1166144fad6ce0"}` — a static
bundle, no `/client/replay` viewer declared.)

Status: **TRUE** — featured match present (`coins.r194.e11`); the resolved viewer URL is
`https://api.observatory.softmax-research.net/v2/coworlds/replays/static/<cow_id>/<manifest_sha>/index.html?v=2#replay=<s3 url>`
with `ready:true`. That is the **static** route in its documented post-2026-08-28 fragment form
(`?v=2#replay=` instead of `?replay=`; `playbooks/observatory-api.md` §Featured match records both
as the static route). It is **not** a `/client/replay` pod URL. `<cow_id>` and `<sha>` are the
canonical v0.1.4 coworld's, matching the coworld the league is actually running.

---

## 7. Certification declared the static bundle — **TRUE**

Read from the **committed** artifact `runs/2026-08-24-coins/release-result.json` (the copy phase 40
downloaded; the `gh run download` fallback was **not** needed — the file is present in the repo,
3965 bytes, and this is the documented exception to "fetch fresh"):

```bash
jq -r '.certify.replay_liveness' runs/2026-08-24-coins/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```
```bash
jq -c '{ok:.ok, version:.version, certify_ok:.certify.ok}' runs/2026-08-24-coins/release-result.json
# {"ok":true,"version":"0.1.2","certify_ok":true}
```

The surrounding certification tail from the same file (10/10 transcript steps passed):
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
```

Status: **TRUE** — contains `Replay liveness: skipped (static replay bundle declared`. Source:
the committed `runs/2026-08-24-coins/release-result.json` (this run's own v0.1.2 release,
`release_run_id` 32798747762), not a re-download and not `/tmp`.

---

## 8. Spectator judgment — the viewer was EXECUTED — **TRUE**

*(a) Dispatch.* The `src` is check 6's variant **B** (the champion-vs-champion replay
`abaf7183-…`), chosen so the render can be reconciled tick-for-tick against the check-4 replay
events; it is the same static bundle and the same route as the page's featured match, differing
only in the `#replay=` target.

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_bd320430-6cf8-4f45-8adb-06de80fbe100/sha256%3A6b286bdb0014f6bb1318c3720ce1bcb09949351120d3e0974d480d1cab19bef9/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fabaf7183-5415-4403-8714-74cd41509e62.replay'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
# dispatched 2026-09-03T19:20:15Z
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
  | jq -r 'sort_by(.createdAt)|reverse|.[]|[.databaseId,.createdAt,.status]|@tsv' | head -2
```
```
33795836783	2026-09-03T19:20:17Z	in_progress      <- created 2s after the dispatch; this is the run
33239074400	2026-08-29T06:41:27Z	completed        <- the previous run, 2026-08-29; not reused
```
```bash
gh run watch 33795836783 -R Metta-AI/coworld-builder --exit-status
```
```
✓ viewer-check in 35s (ID 100783197310)
  ✓ Load the viewer
  ✓ Upload the evidence
  ✓ Fail if the viewer did not load
```
Green run.
```bash
gh run download 33795836783 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-24-coins/viewer-check
# viewer-smoke.json (2077 B), viewer-smoke.png (426938 B), smoke-stdout.txt, smoke-stderr.txt (0 B) — committed with this file
```

*(b) The readouts, verbatim.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-24-coins/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":1313,"clock":"BEAT 1 / 12 TICK 1 OF 240 · 6 COINS ON THE BOARD","scorebug":"COINS-PLAYER 0 STOLE 0 took 15 · restraint 100% BEAT 1 / 12 TICK 1 OF 240 · 6 COINS ON THE BOARD COINS-PLAYER 0 STOLE 0 took 10 · restraint 100%","feed_lines":0}
```
```bash
jq -c '.signals' runs/2026-08-24-coins/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```
```bash
jq -r '.failure // "no failure"' runs/2026-08-24-coins/viewer-check/viewer-smoke.json
```
```
no failure
```

**The three clock readouts:**

| scrub | clock text |
|---|---|
| 0 % | `BEAT 1 / 12 TICK 1 OF 240 · 6 COINS ON THE BOARD` |
| 50 % | `BEAT 7 / 12 TICK 135 OF 240 · 3 COINS ON THE BOARD` |
| 100 % | `FINAL 12 BEATS · RANDOM_END` |

All three **differ**. The scrubber exists (no `"(no #scrub…)"` sentinel). Load took **1313 ms**.

`console_tail` from the same artifact — one 404, recorded because it is real:
```json
["[http 404] …/static/cow_bd320430-…/sha256%3A6b286bdb…/font.ttf",
 "[error] Failed to load resource: the server responded with a status of 404 ()",
 "[requestfailed] …/font.ttf net::ERR_ABORTED",
 "[bridge] loading",
 "[bridge] ready"]
```

*(c) The replay JSON the viewer was asked to draw* — ordered excerpts from `/tmp/v/ep.replay`
(`tick, beat, seat, kind, say/intent/why/reason`):

early:
```
0	1	0	order	Open restrained - taking only copper
0	1	1	order	Opening move: securing my coins
0	-	0	blocked	restraint
6	-	0	blocked	restraint
9	-	1	blocked	restraint
12	-	-	spawn
18	-	0	pickup
19	1	-	beatclose
20	2	0	order	Truce holds. Your theft counter: 0. Mine: 0.
20	2	1	order	Steady pace. Banking coins.
30	-	1	leadchange
33	-	0	leadchange
```
middle:
```
79	-	0	leadchange
79	4	-	beatclose
80	5	0	order	Truce holds. Taking only copper.
80	5	1	order	Board empty. Coins incoming. Building safely.
99	5	-	beatclose
100	6	0	order	Truce holds. Your coins stay safe.
100	6	1	order	Coins spawning soon; staying calm
103	-	1	pickup
103	-	1	leadchange
115	-	0	pickup
```
late:
```
200	11	0	order	Truce holds. Copper coin at (2,3).
200	11	1	order	Steady pace, no theft yet.
219	11	-	beatclose
220	12	0	order	Truce holds. Cooperation mutual.
220	12	1	order	Leveling the ledger
220	-	0	pickup
223	-	0	pickup
223	-	1	theft
232	-	0	pickup
239	12	-	beatclose
239	12	-	end	random_end
```

### Spectator judgment

**It is legible, it is the starter's chrome, and the picture agrees with the record.**
`viewer-smoke.png` (committed at `runs/2026-08-24-coins/viewer-check/viewer-smoke.png`) is the
frame at the end of the scrub, and it is a finished broadcast, not a blank canvas. Top strip: a
two-sided scorebug — copper on the left reading `STOLE 0 · 13 · COINS-PLAYER` with the small line
`took 15 · restraint 100%`, cobalt on the right reading `COINS-PLAYER · 10 · STOLE 1` with
`took 10 · restraint 90%`, and a centred `FINAL / 12 BEATS · RANDOM_END`. Centre: the 9×9 board
grid, dimmed behind an endcard that reads **"COINS-PLAYER HOLDS THE ROOM"** with the chip
`12 BEATS · ENDED AT RANDOM · 25 COINS`, one line of rules ("Every coin is +1 to whoever takes it;
a coin of the other cog's colour also costs them 2. Higher is better."), and a results table with
columns POLICY / SCORE / COINS / THEFTS / STOLEN / RESTRAINT holding `13 15 0 1 100%` and
`10 10 1 0 90%`. One standing cog sprite is visible on the board above the card. Bottom: the
transport strip — loop, step-back, pause, `+5s`, play, restart, fast-forward, a `spoilers` toggle,
the readout `RED WINS 239 / 239`, speed buttons `0.5× 1× 2× 3× 4× 8× 16×` — over a scrubber with
the score-lead momentum graph and per-beat tick marks. That is the paintbot/raid/hive family
chrome the starter supplies, not a different product: no gridlock-style rewrite.

Every number on the screen matches the replay bytes exactly: scores 13–10 = `results.scores`;
coins 15/10 = `pickups`; thefts 0/1 = `thefts`; stolen 1/0 = `stolenFrom`; restraint 100 %/90 % =
`restraint [1.0, 0.9]`; `12 BEATS · ENDED AT RANDOM` = `beats:12, reason:"random_end"`; the
transport's `239 / 239` = the final tick of `ticksPlayed:240`. And it **moves**: beat 1 / tick 1 /
6 coins → beat 7 / tick 135 / 3 coins → the endcard, three different clocks and even a changing
coins-on-board count, so the wasm bundle is really stepping frames rather than painting one.

Does it show *the game*? Yes, and for the first time this run it shows the interesting version of
it. The record underneath is a genuine social episode: 24 LLM decisions, both seats talking to each
other in the `say` channel ("Truce holds. Your theft counter: 0. Mine: 0."), three `blocked …
why:"restraint"` moments where a cog walks past a stealable coin, ten lead changes, and then at
beat 12 the ledger seat says "Leveling the ledger" and steals — the theft the whole design exists
to produce. The endcard's `THEFTS 0 / 1` and `RESTRAINT 100% / 90%` are exactly that story
compressed into two rows, and the momentum strip under the transport ends on a red (copper) lead,
which is the 13–10 finish. The
2026-08-25 observation that every room ended `thefts:[0,0]` because every decision was a fallback
no longer holds.

Four observations, none of them a check failure:
1. **Both seats render as `COINS-PLAYER`.** The replay's `policyNames` is
   `["coins-player","coins-player"]` (the in-container player binary name) rather than
   `coins-truce` / `coins-ledger`, so the scorebug, the results table and the endcard headline all
   say "COINS-PLAYER" and a spectator cannot tell which champion won without the colour cue
   (copper = seat 0 = `coins-truce`, cobalt = seat 1 = `coins-ledger`). Known residue, still
   present.
2. **The scorebug appears to show final totals from tick 1.** At the 0 % readout the clock says
   `BEAT 1 / 12 TICK 1 OF 240` while the scorebug already reads `took 15` / `took 10` — the final
   pickup counts. The `spoilers` toggle is lit in the screenshot, so this is most likely
   spoilers-on-by-default rather than a wrong readout, but it does mean the opening frame gives
   away the ending.
3. `feed_lines: 0` — the smoke harness found no say-feed lines in the DOM at capture time. The
   `say` texts are in the replay and the endcard was covering the board, so this is unresolved
   from the artifact alone; noting it rather than claiming the feed works.
4. One asset 404s: `…/font.ttf` (`net::ERR_ABORTED`). The page still renders in a fallback font;
   cosmetic.

Status: **TRUE** — `loaded: true` (`data_replay_loaded:"true"` **and** bridge `["loading","ready"]`,
`bridge_error: []`), and the three clock readouts differ.

---

## Residues carried forward (not check failures)

- **Coworld version drift vs STATE**: canonical `coins` is now `cow_bd320430-…` v0.1.4
  (`sha256:6b286bdb…`), STATE still records `cow_e5c32ad5-…` v0.1.2 (`sha256:a0ef3142…`); the
  v0.1.2 id 404s on the replay-session endpoint. Same repo (`Metta-AI/cogame-coins`,
  commit `39cf1ade`), same owner, still a static viewer bundle. STATE is the coordinator's to
  update, not mine.
- **`policyNames: ["coins-player","coins-player"]`** in the replay instead of the policy labels —
  still present (see spectator judgment ¶ caveat 1).
- **Sidecar 30 req/min cap under retry storms** — not exercised this episode: 24 calls over 63 s
  (~23/min peak measured from the sidecar timestamps), all 200, no retries.
- **Ladder cadence** is ~4h48m between rounds, not the configured `round_interval_minutes: 15`.
- **`font.ttf` 404** in the static viewer bundle.
- `GET $BASE/episode-requests?round_id=…` is **405** (flat route retired) — the nested
  `GET $BASE/rounds/<id>/episode-requests` is the working call, as the playbook already says.
