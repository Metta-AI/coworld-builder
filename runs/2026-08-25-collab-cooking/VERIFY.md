# VERIFY — collab-cooking   (2026-08-25T10:45Z, attempt 2, post-remediation)

Verdict: **all-true (8/8)**

Attempt 1 (2026-08-25T09:20Z, preserved in git history) returned 5 items false: every league
episode died `game_unhealthy` from a mettagrid feature-id overflow at `max_steps=900`. That was
fixed (recycled 10-slot ticket pool, 313 → 153 feature ids) and re-released as **v0.1.3**
(`cow_19938c0f-195a-45f8-95da-761f0ffe04cb`, manifest_sha
`sha256:ae8627b0c7abde4a8807b3fff2e641a9f289512221ecd494de9c9753afeb3cf1`). Every fetch below is
fresh, made this run between 10:24Z and 10:45Z. Headers sent on every call:
`Authorization: Bearer $SOFTMAX_TOKEN` and `User-Agent: coworld-builder/1.0`; where noted also
`X-Use-Elevated-Privileges: true`. No header value is printed anywhere in this document.

```bash
BASE=https://softmax.com/api/observatory/v2
L=league_592e6ed0-3f01-4084-bb90-75ace0db0063
D=div_027403b9-3208-43b8-b2e6-499bd18681e5
COW=cow_19938c0f-195a-45f8-95da-761f0ffe04cb
```

| # | check | verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | TRUE |
| 2 | both champions ranked, fillers absent/Baseline | TRUE |
| 3 | latest round's episode request completed with a replay | TRUE |
| 4 | replay bytes valid and show the game | TRUE |
| 5 | hosted game log clean | TRUE (documented, cross-checked exception) |
| 6 | public page uses the static replay path | TRUE |
| 7 | certification declared the static bundle | TRUE |
| 8 | spectator judgment — viewer EXECUTED | TRUE |

---

## 1. ≥2 completed rounds after the fillers were set

```
GET $BASE/rounds?league_id=$L&limit=30
```
Response shape: `{"entries":[…]}`, 10 rows, 8 with `status=="completed"`.

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=30" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end|[.[]|select(.status=="completed")]|length'
```
```
8
```

Full listing (`round_number, id, status, created_at, completed_at, error`):

```
1	round_fe61851d-5d71-41d6-853f-8eba11675499	failed	2026-08-25T08:40:01.020101Z	2026-08-25T08:40:01.325872Z	Temporal RoundWorkflow failed before settling the round.
2	round_201d9765-4ea3-4391-9393-b486cc36eb54	completed	2026-08-25T08:40:49.983322Z	2026-08-25T08:42:33.787355Z	-
3	round_31a882c6-ee31-42b1-a1e2-8870cc0ab6b7	completed	2026-08-25T08:55:50.415385Z	2026-08-25T08:56:42.446039Z	-
4	round_f48e29f0-a9f2-4002-9739-1469bb48182d	completed	2026-08-25T09:10:50.809299Z	2026-08-25T09:11:12.188592Z	-
5	round_bba778bc-f095-42ab-97ae-cf6e12946dc4	completed	2026-08-25T09:25:51.141455Z	2026-08-25T09:27:23.638240Z	-
6	round_777a16e9-6f4b-4b80-b168-b022a26f186d	completed	2026-08-25T09:40:52.208003Z	2026-08-25T09:41:36.822785Z	-
7	round_5f218a7f-cb2a-4cbd-aa75-d39ebbfdbfd1	completed	2026-08-25T09:55:53.041117Z	2026-08-25T09:56:24.913772Z	-
8	round_8784fbcb-4de5-4649-8c23-e3b631150523	completed	2026-08-25T10:11:50.890406Z	2026-08-25T10:21:06.127940Z	-
9	round_8f0dfbaa-2912-482f-95e0-179e79ba9894	completed	2026-08-25T10:27:28.245834Z	2026-08-25T10:33:54.769639Z	-
10	round_e75b7054-3b8c-486b-b06a-d232e22a7626	pending	2026-08-25T10:42:28.631149Z	-	-
```

Round 1's `error` verbatim (it does **not** count): `Temporal RoundWorkflow failed before settling
the round.` — the auto-round on unpause raced the filler registration (log.md:58), the documented
failure mode in `playbooks/observatory-api.md` §6.

Fillers were registered at **2026-08-25T08:42:05Z** (log.md:57, `brigade=6f226863 passer=fb542fe5`)
and re-registered at v3 at **≈2026-08-25T10:14Z** (log.md:87). The current registered filler list,
fetched fresh (this read needs the elevated header):

```
GET $BASE/leagues/$L/filler-policies      (headers: Authorization, User-Agent, X-Use-Elevated-Privileges)
```
```json
{
  "filler_policy_versions": [
    {"policy_version_id": "c56ed34b-abb8-4118-a42b-3963b77690a0", "policy_name": "collab-cooking-brigade",
     "version": 3, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"},
    {"policy_version_id": "71a84f9c-a4c5-4ace-912d-c327f3b6d26e", "policy_name": "collab-cooking-passer",
     "version": 3, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"}
  ]
}
```

**Per-round episode outcome** (the spirit of the check — a round that "completed" while its episode
died proves nothing). One `GET $BASE/episode-requests?round_id=<r>&limit=20` per completed round:

```
round_201d9765 (r2)  ereq_b5042a23-1f40-4ee0-a387-ebb0706639e1	failed	-
round_31a882c6 (r3)  ereq_ce167142-be9f-498f-9ec9-74248ac21af7	failed	-
round_f48e29f0 (r4)  ereq_7a3dbe01-1662-410f-8ab7-95ea7a2f8058	failed	-
round_bba778bc (r5)  ereq_69d9b8a0-180f-4424-85ea-49e9b2f0be1a	failed	-
round_777a16e9 (r6)  ereq_e28a6dfe-ad5b-43c0-9c7e-836693262011	failed	-
round_5f218a7f (r7)  ereq_6c51303b-d2b8-48a6-a1cc-9dc10e5c9649	failed	-
round_8784fbcb (r8)  ereq_35289237-a003-40f4-b3e8-4e08482f6854	completed	https://softmax-public.s3.amazonaws.com/replays/2be74c60-3f6c-41eb-b34e-e03824ab3352.replay
round_8f0dfbaa (r9)  ereq_876d0e7c-bc10-4c59-aa07-31f2cf46aa1c	completed	https://softmax-public.s3.amazonaws.com/replays/d0c99032-68e2-478a-9007-84fdf727336b.replay
```

**Status: TRUE.** 8 rounds `completed`. Rounds 3–9 (seven of them) were created after the
08:42:05Z filler registration; rounds 2–9 are all after the 08:41–08:42Z registration window.
Post-fix rounds with a **COMPLETED episode**: **round 8** (created 10:11:50Z, episode completed
10:21:06Z) and **round 9** (created 10:27:28Z, episode completed 10:33:54Z) — two, so the wait
condition set for this attempt is satisfied and no further waiting was needed (round 9 landed at
10:38Z, 13 minutes into the 75-minute bound that started at 10:25Z). Rounds 2–7's episodes are the
attempt-1 `game_unhealthy` defect; they are recorded here for completeness and are not counted.

---

## 2. Both champions ranked

```
GET $BASE/divisions/$D/leaderboard
```
Bare JSON list (not `.entries`), fetched 10:38Z:

```json
[
  {"rank": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
   "score": 1000.0, "score_label": "Elo", "rounds_played": 8, "episode_wins": 0.0, "win_rate": 0.0,
   "policy_label": "collab-cooking-expo:v3"},
  {"rank": 2, "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
   "score": 1000.0, "score_label": "Elo", "rounds_played": 8, "episode_wins": 0.0, "win_rate": 0.0,
   "policy_label": "collab-cooking-linecook:v3"},
  {"rank": 3, "player_id": "ply_ded11f40-3e30-4921-b019-f7f6bc3e9c83", "player_name": "richard",
   "score": 1000.0, "score_label": "Elo", "rounds_played": 4, "episode_wins": 0.0, "win_rate": 0.0,
   "policy_label": "co-gas-collab-cooking-runner-richard:v1"}
]
```

`rank / player_name / policy_label / score / rounds_played / episode_wins` as tsv:

```
1	daveey	collab-cooking-expo:v3	1000.0	8	0.0
2	daveey-1	collab-cooking-linecook:v3	1000.0	8	0.0
3	richard	co-gas-collab-cooking-runner-richard:v1	1000.0	4	0.0
```

**Status: TRUE.** `daveey` (rank 1, `collab-cooking-expo:v3`, `rounds_played: 8`) and `daveey-1`
(rank 2, `collab-cooking-linecook:v3`, `rounds_played: 8`) are both ranked with `rounds_played ≥ 1`.
Neither filler (`collab-cooking-brigade:v3` `c56ed34b…`, `collab-cooking-passer:v3` `71a84f9c…`)
appears as a row — fillers absent, which the checklist accepts. Row 3, `richard`
(`ply_ded11f40`, `co-gas-collab-cooking-runner-richard:v1`), is a **third-party external entrant**,
not one of ours and not a filler; it does not displace either champion. Both champions' labels now
read `:v3`, i.e. the placement lag noted at dispatch has cleared. Elo is still 1000.0/0 wins for
all three because every completed episode so far has been a draw on team score (see check 4 —
`scores` differ only by the 0.01·delivered epsilon).

---

## 3. Latest round's episode request completed with a replay

Latest completed round **with a completed episode** = round 9, `round_8f0dfbaa-2912-482f-95e0-179e79ba9894`.

```
GET $BASE/episode-requests?round_id=round_8f0dfbaa-2912-482f-95e0-179e79ba9894&limit=20
  -> ereq_876d0e7c-bc10-4c59-aa07-31f2cf46aa1c	completed
GET $BASE/episode-requests/ereq_876d0e7c-bc10-4c59-aa07-31f2cf46aa1c
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/d0c99032-68e2-478a-9007-84fdf727336b.replay",
  "participants": [
    {"position": 0, "policy_name": "collab-cooking-expo",   "version": 3, "player_name": "daveey",
     "is_filler": false, "policy_version_id": "ff80304d-80c3-407e-b3e3-5ee5d8cabf68"},
    {"position": 1, "policy_name": "collab-cooking-linecook","version": 3, "player_name": "daveey-1",
     "is_filler": false, "policy_version_id": "98d3999f-1484-4572-9f7c-874735b47d17"},
    {"position": 2, "policy_name": "co-gas-collab-cooking-runner-richard", "version": 1,
     "player_name": "richard", "is_filler": false, "policy_version_id": "f3debab3-a36c-493a-aa7a-de63b617ece8"},
    {"position": 3, "policy_name": "collab-cooking-brigade","version": 3, "player_name": "daveey",
     "is_filler": true,  "policy_version_id": "c56ed34b-abb8-4118-a42b-3963b77690a0"}
  ],
  "participant_scores": [
    {"position": 0, "score": 3.0}, {"position": 1, "score": 3.0},
    {"position": 2, "score": 3.0}, {"position": 3, "score": 3.03}
  ]
}
```

The previous post-fix round (8) for corroboration — same query, `ereq_35289237-a003-40f4-b3e8-4e08482f6854`:
`status: "completed"`, `replay_url: https://…/2be74c60-3f6c-41eb-b34e-e03824ab3352.replay`, seats
0/1 `collab-cooking-expo`/`collab-cooking-linecook` (daveey / daveey-1, `is_filler:false`), seat 2
`richard`, seat 3 `collab-cooking-passer` `is_filler:true`; scores `[1.0, 1.0, 1.0, 1.01]`.

**Status: TRUE.** `status == "completed"`, `replay_url` non-null (S3), and `participants` names
`daveey` (seat 0, champion #1 at v3, `ff80304d…`) and `daveey-1` (seat 1, champion #2 at v3,
`98d3999f…`), with the filler at seat 3 flagged `is_filler: true` and rendered `Baseline`
spectator-side (see the replay `seats`/`results.names` in check 4). Seat 2 is the external entrant
`richard`.

---

## 4. Replay bytes are valid and show the game

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/d0c99032-68e2-478a-9007-84fdf727336b.replay" -o /tmp/ep9.replay
# HTTP:200 bytes:403849
jq -e . /tmp/ep9.replay >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.format, .protocol, .version, .coworld, .generated_at, (.ticks|length)' /tmp/ep9.replay
```
```
strict UTF-8 JSON: ok
collab-cooking/1
collab-cooking.replay.v1
0.1.0
collab_cooking
2026-08-25T10:27:47Z
900
```

`protocol` match: `collab-cooking.replay.v1` is the envelope declared in
`runs/2026-08-25-collab-cooking/design.md:815`; the hosted manifest for `cow_19938c0f…` declares
`game.results_schema.properties.protocol.const == "collab-cooking.results.v1"`, which matches
`.results.protocol` below.

```bash
jq '.results' /tmp/ep9.replay
```
```json
{
  "game": "collab_cooking", "protocol": "collab-cooking.results.v1", "reason": "complete",
  "layout": "open-kitchen", "steps": 900, "dishes": 3,
  "scores": [3.0, 3.0, 3.0, 3.03], "delivered": [0, 0, 0, 3],
  "served_by_recipe": {"salad": 1, "soup": 2, "fries": 0},
  "orders_arrived": 50, "orders_expired": 47, "burned": {"pot": 3, "fryer": 0},
  "blocked_moves": [313, 356, 384, 381], "handoffs": [2, 0, 7, 2],
  "names": ["daveey", "daveey-1", "richard", "Baseline"],
  "aliases": ["Cog-B", "Cog-C", "Cog-D", "Cog-A"],
  "seat_kinds": ["prompt", "prompt", "scripted:runner", "scripted:brigade"],
  "cross_play": true, "disconnected": [false, false, false, false],
  "fallbacks": [6, 6, 0, 0], "llm_requests": 48
}
```

Requested fields, called out: **`results.cross_play`: `true`** · **`results.dishes`: `3`** ·
**`results.seat_kinds`: `["prompt","prompt","scripted:runner","scripted:brigade"]`** (two LLM prompt
seats vs two scripted seats — genuine cross-play) · `results.reason`: **`complete`** (900/900 ticks,
not `deadline`).

Decisions are `plan` events inside each tick's `ev` array; the phase prompt's `.events[]` jq is
adapted to this schema:

```bash
# adapted from prompts/60-verify.md check 4 for schema {"ticks":[{"t":…,"ev":[{"ev":"plan",…}]}]}
jq -r '[.ticks[].ev[]?|select(.ev=="plan")]|group_by(.slot)|map({slot:.[0].slot, alias:.[0].alias,
        total:length, llm:([.[]|select(.src=="llm")]|length),
        fallback:([.[]|select(.src|startswith("fallback"))]|length)})' /tmp/ep9.replay
```
```json
[
  {"slot": 0, "alias": "Cog-B", "total": 12, "llm": 12, "fallback": 0},
  {"slot": 1, "alias": "Cog-C", "total": 12, "llm": 12, "fallback": 0}
]
```
```bash
jq -c '[.ticks[].ev[]?|select(.ev=="fallback")]|group_by(.slot)
        |map({slot:.[0].slot,alias:.[0].alias,n:length,causes:([.[].cause]|unique)})' /tmp/ep9.replay
```
```json
[{"slot":0,"alias":"Cog-B","n":6,"causes":["transport"]},
 {"slot":1,"alias":"Cog-C","n":6,"causes":["transport"]}]
```

Event-type census over the whole episode (the game is visibly being played, not idling):

```bash
jq -r '[.ticks[].ev[]?.ev]|group_by(.)|map({(.[0]):length})|add' /tmp/ep9.replay
```
```json
{"blocked":1434,"chop_done":17,"chop_start":17,"deposit":97,"episode_end":1,"episode_start":1,
 "fallback":12,"order_arrive":50,"order_expire":47,"pickup":107,"plan":24,"plate_up":3,
 "pot_burn":3,"pot_clear":5,"pot_load":6,"pot_ready":5,"pot_start":5,"serve":3,
 "wash_done":3,"wash_start":3}
```

Champion-seat decision content — every `plan` and `fallback`, in tick order (abridged to the plan
line; all 24 plans carry `src:"llm"`):

```
11	0	Cog-B	plan	Taking soup ticket, fetching veg first
61	0	Cog-B	plan	Chopping veg for soup
64	1	Cog-C	plan	Fetching meat for soup, Cog-B has veg
102	0	Cog-B	fallback	transport
102	1	Cog-C	fallback	transport
164	0	Cog-B	plan	Chopping veg for soup (1 of 3 uses). Cog-C: get meat chopped, we'll pot together.
165	1	Cog-C	plan	Potting chopped veg now, pot was ready. Need chopped meat to complete soup.
263	0	Cog-B	plan	Chopped veg ready, moving to pot. Waiting for Cog-C's chopped meat to complete soup.
267	1	Cog-C	plan	Getting meat chopped for soup. Cog-B: finish veg, I'll bring chopped meat to pot.
365	0	Cog-B	plan	B here with chopped_veg for soup. Going to pot to meet Cog-C's chopped meat.
367	1	Cog-C	plan	Fetching meat now. Will chop and meet you at pot for soup.
414	0	Cog-B	plan	Going to pot with chopped_veg, waiting for Cog-C's chopped_meat to complete soup
417	1	Cog-C	plan	Going meat for soup. Pot loaded, B waiting with veg. I'll chop meat fast.
513	1	Cog-C	plan	Going to pot with chopped_veg. Cog-B bring chopped_meat to complete soup fast.
515	0	Cog-B	plan	B at pot with meat, ready to combine with veg for soup
564	0	Cog-B	plan	Fetching meat for soup. Cog-C at pot waiting for chopped_meat.
567	1	Cog-C	plan	Moving to pot with chopped veg. Cog-B bring chopped meat to combine. Fryer next for fries.
611	0	Cog-B	plan	Chopping meat for soup. Will deliver chopped meat to pot.
613	1	Cog-C	plan	Moving to pot with chopped_veg. Cog-B bring chopped_meat - soup combo ready!
666	1	Cog-C	plan	Moving to counter (5,3) for chopped_veg, then pot to combine with meat
713	1	Cog-C	plan	Moving to chop. Cog-B: deliver meat to pot when ready. I'll grab chopped_veg at (5,3) next.
715	0	Cog-B	plan	Chopping meat for soup, will handoff to Cog-C at pot
764	0	Cog-B	plan	Fetching meat for soup. Will chop and deliver to pot for Cog-C.
767	1	Cog-C	plan	Moving to pot with chopped_veg, ready to combine with Cog-B's meat for soup
862	0	Cog-B	plan	Chopping meat for soup, will deliver to pot after
865	1	Cog-C	plan	Moving to pot with meat. Cog-B bringing chopped meat. Will assemble soup immediately.
```

One plan verbatim, full record (the fields the design's reply schema defines):

```json
{"t":865,"slot":1,"alias":"Cog-C","station":"pot","recipe":"soup","zone":"any","handoff":"none",
 "yield_to":"Cog-B","say":"Moving to pot with meat. Cog-B bringing chopped meat. Will assemble soup immediately.","src":"llm"}
```

Round 8's replay was parsed the same way, as a same-coworld comparison point:
`strict UTF-8 JSON: ok`, 372544 bytes, `collab-cooking.replay.v1`, `results.reason: "complete"`,
900 ticks, `dishes: 1`, `cross_play: true`,
`seat_kinds: ["prompt","prompt","scripted:runner","scripted:passer"]`, `fallbacks: [1,1,0,0]`,
`llm_requests: 34`, and **30 `plan` events, all 30 `src:"llm"`, 0 with `src:"fallback:*"`**.

**Status: TRUE.**
- strict UTF-8 JSON under `jq -e`: **ok** (403849 bytes).
- `protocol` matches the design/manifest declaration: **yes**.
- `results.reason == "complete"`: **yes** (not `deadline`).
- champion seats' plans are non-scripted with non-trivial content: **every one of the 24 `plan`
  records carries `src:"llm"`, with real coordination language** (station/recipe/handoff/yield_to
  set, `say` naming the other cog and the missing ingredient). Not one plan is a fallback plan.
- fallbacks a minority: **12 of 36 plan turns (33 %) in round 9; 2 of 32 (6 %) in round 8.**
  Both are minorities and neither is "all fallbacks". The round-9 elevation has a single cause,
  fetched in check 5 and cross-checked there against two other live LLM coworlds: the shared
  provider answering `http 429 {"message":"Too many tokens per day, please wait before trying
  again."}` — a platform-wide capacity/quota symptom, which SPEC/`prompts/60-verify.md` check 5
  explicitly allows when documented and cross-checked. The coworld's own degrade path behaved
  exactly as the design says it should: retry once, then that seat plays `brigade` for one turn and
  emits a `fallback` event naming the cause; the episode still finished `complete` at 900/900.

Legibility observations for the coordinator (not check failures): the two LLM champions delivered
**0** dishes each while the scripted `brigade` filler delivered all 3, 47 of 50 tickets expired,
and `blocked` fires 1434 times — the prompt seats spend the episode shuttling half-assembled soup
and never close the loop. Team score is shared, so all four seats score 3.x and Elo does not move;
the ladder is currently a draw machine.

---

## 5. Hosted game log is clean

```
GET $BASE/episode-requests/ereq_876d0e7c-bc10-4c59-aa07-31f2cf46aa1c/artifacts/logs
     (headers: Authorization, User-Agent, X-Use-Elevated-Privileges)   -> HTTP:200
```

The body is python `b'…'` byte-string reprs under four `===== container: … =====` headers
(`coworld-init-config`, `bedrock-sidecar`, `game`, `worker`), so it was decoded with
`ast.literal_eval` per repr before grepping (104693 bytes of decoded text):

```bash
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs9.txt
```
```
191:INFO:     connection rejected (403 Forbidden)
```

Per-pattern counts on the decoded text:

```
falling back                     0
LLM provider is unavailable      0
cut off at max_tokens            0
rejected                         1
```

The single hit in context (lines 188–194 verbatim):

```
INFO:     127.0.0.1:48852 - "GET /healthz HTTP/1.1" 200 OK
INFO:     127.0.0.1:48868 - "GET /client/player?slot=0&token=90L1HPVfQPBfY4j7OEbDqw HTTP/1.1" 200 OK
INFO:     127.0.0.1:48872 - "WebSocket /player?slot=0&token=bad" 403
INFO:     connection rejected (403 Forbidden)
INFO:     127.0.0.1:48882 - "GET /client/global HTTP/1.1" 200 OK
INFO:     127.0.0.1:48884 - "WebSocket /global" [accepted]
INFO:     connection open
```

**Documented exception, cited.** This is the platform certification runner's own negative probe —
a `token=bad` websocket from `127.0.0.1` at pod startup, *before* any real player connected, which
the server correctly refuses; the real slot-0 player then connects with a valid token. It is
evidence that token auth works, not an LLM degradation, and it is the identical line the
commons-family run's phase-60 adjudication accepted as a documented exception
(`runs/2026-08-24-commons-family/reviews/verify-verdict.md` §"Check 5 — one `rejected` grep hit →
PROPERLY DOCUMENTED EXCEPTION, check stands TRUE", and `runs/2026-08-24-commons-family/VERIFY.md`
lines 313/339/354). Round 8's log, fetched the same way, has exactly the same single hit
(`191:` there too is the `token=bad` 403; `falling back` / `LLM provider is unavailable` /
`cut off at max_tokens` all 0).

**Per-seat fallback causes (this game logs them) — distinguished from the above.** The 12
round-9 fallbacks do not match any of the four patterns, but they are the reason check 4's fallback
share rose, so their cause is fetched here verbatim. 24 lines, i.e. 12 turns × (attempt 0 + attempt
1 retry), all of one kind:

```bash
grep -E '^collab-cooking llm: ' /tmp/logs9.txt | head -6
```
```
collab-cooking llm: slot 1 attempt 0: transport http 429: {"message":"Too many tokens per day, please wait before trying again."}
collab-cooking llm: slot 1 attempt 1: transport http 429: {"message":"Too many tokens per day, please wait before trying again."}
collab-cooking llm: slot 0 attempt 0: transport http 429: {"message":"Too many tokens per day, please wait before trying again."}
collab-cooking llm: slot 1 attempt 0: transport http 429: {"message":"Too many tokens per day, please wait before trying again."}
collab-cooking llm: slot 0 attempt 1: transport http 429: {"message":"Too many tokens per day, please wait before trying again."}
collab-cooking llm: slot 0 attempt 1: transport http 429: {"message":"Too many tokens per day, please wait before trying again."}
```
```
$ grep -cE '^collab-cooking llm: ' /tmp/logs9.txt      -> 24
$ grep -E '^collab-cooking llm: ' /tmp/logs9.txt | grep -c '429'   -> 24
$ grep -E '^collab-cooking llm: ' /tmp/logs9.txt | grep -v '429'   -> (no output)
```

Every one is `http 429` from the shared provider; there are no timeouts, no schema rejections, no
`rate_budget` skips, no `max_tokens` truncations. The successful calls show the provider and that
`max_output_tokens` is 900, not 400:

```
bedrock_sidecar_complete {… "model":"global.anthropic.claude-haiku-4-5-20251001-v1:0",
  "operation":"InvokeModel", "ok":true, "status_code":200, "latency_ms":1680.68,
  "error_kind":null, "cache_strategy":"sidecar_v1", "cache_decision":"first_sighting" …}
bedrock_sidecar_usage {… "usage":{"input_tokens":718,"output_tokens":103,
  "cache_read_input_tokens":0,"cache_write_input_tokens":0}}
```
```bash
jq -r '.config|{model, max_output_tokens, plan_interval_steps, llm_max_requests_per_minute}' /tmp/ep9.replay
# {"model":"claude-haiku-4-5-20251001","max_output_tokens":900,
#  "plan_interval_steps":50,"llm_max_requests_per_minute":26}
```

**Platform-wide cross-check (two other live LLM coworlds, same wall-clock window).** Both fetched
fresh with the elevated header:

- `coins` (`cow_e5c32ad5-8696-4d4f-8a39-458baa8c2a3e`), latest episode
  `ereq_7c6ddebe-788b-4369-ae27-500ab36b781a` (created 2026-08-25T10:29:13Z):
  `Too many tokens per day, please wait before trying again.` × **24**, plus its own explicit
  `coins llm: seat 0 falling back to scripted intent` lines (5 shown at lines 88/92/99/104/109) —
  i.e. that coworld's log is *dirtier* under the same regex than collab-cooking's.
- `cooperative-hunting` (`cow_d5e3a72d-bae0-4418-bb3e-e39f2c5cc81d`), latest completed episode
  `ereq_089f819e-a39c-42da-9689-2511fa30d637` (created 2026-08-25T10:18:44Z):
  `Too many tokens per day…` × **2**, and at line 697
  `cooperative-hunting llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled);
  falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0` — the same Haiku-4.5 throttle,
  named.

**Status: TRUE.** Zero hits for `falling back`, `LLM provider is unavailable` and
`cut off at max_tokens`. The one `rejected` hit is the pod-local `token=bad` auth probe — a
documented exception with the precedent cited. The 429 daily-token cap that produced the 12
fallbacks is a platform-wide capacity symptom, cross-checked against two other coworlds' logs from
the same fifteen minutes, exactly the cause `prompts/60-verify.md` check 5 says to document rather
than treat as a defect in this coworld. The game container also shut down cleanly
(`Shutting down` → `Application shutdown complete.` → `Finished server process [1]`).

---

## 6. The public page uses the static replay path

Source (a) — raw HTML grep:

```bash
curl -sS "https://softmax.com/collab-cooking" | grep -o '<iframe[^>]*src="[^"]*"'
# HTTP:200 bytes:550571
# NO MATCH
```
Not a false negative: the page is client-rendered for the iframe (documented in
`playbooks/observatory-api.md` §Featured match / replay route, lighthouse run 2026-08-22). So:

Source (b) — the coworld detail API. `featured_match` is `null` platform-wide, so it is not
evidence either; recorded for completeness:

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" | jq -r '…|select(.name=="collab_cooking")|{id,canonical,replay_viewer,featured_match,manifest_hash}'
```
```json
{"id":"cow_19938c0f-195a-45f8-95da-761f0ffe04cb","name":"collab_cooking","version":"0.1.3","canonical":true,
 "replay_viewer":null,"featured_match":null,
 "manifest_hash":"sha256:ae8627b0c7abde4a8807b3fff2e641a9f289512221ecd494de9c9753afeb3cf1"}
{"id":"cow_7785231a-793b-440e-8e1b-0f4f5df5ada4","version":"0.1.2","canonical":false, …}
{"id":"cow_127a462a-6f7f-457f-aa7b-95652aae11d4","version":"0.1.1","canonical":false, …}
```

Source (c) — **the source used for the verdict**: the featured match server-rendered into the
page's SSR payload at `state.playlist[0]`, extracted from the same `GET https://softmax.com/collab-cooking`
body fetched at 10:39Z:

```json
{
  "episodeId": "b08e760c-9c75-42a6-aeb9-c0b428884067",
  "coworldId": "cow_19938c0f-195a-45f8-95da-761f0ffe04cb",
  "coworldName": "collab_cooking",
  "coworldVersion": "0.1.3",
  "replayUrl": "https://softmax-public.s3.amazonaws.com/replays/d0c99032-68e2-478a-9007-84fdf727336b.replay",
  "finishedAt": "2026-08-25T10:33:47.933542Z",
  "roundNumber": 9,
  "episodeNumber": 1,
  "code": "collab_cooking.r9.e1",
  "inspectUrl": "/observatory/v2?tab=episode-requests&detail=episode-request:ereq_876d0e7c-bc10-4c59-aa07-31f2cf46aa1c",
  "matchup": {
    "divisionId": "div_027403b9-3208-43b8-b2e6-499bd18681e5", "divisionName": "Competition",
    "first":  {"rank":1,"player_name":"daveey",  "policy_label":"collab-cooking-expo:v3",    "rounds_played":8,"score":1000},
    "second": {"rank":2,"player_name":"daveey-1","policy_label":"collab-cooking-linecook:v3","rounds_played":8,"score":1000}
  }
}
```

And the call the page's own JS makes to turn that into the iframe `src`:

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_19938c0f-195a-45f8-95da-761f0ffe04cb",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/d0c99032-68e2-478a-9007-84fdf727336b.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_19938c0f-195a-45f8-95da-761f0ffe04cb/sha256%3Aae8627b0c7abde4a8807b3fff2e641a9f289512221ecd494de9c9753afeb3cf1/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fd0c99032-68e2-478a-9007-84fdf727336b.replay&v=2",
  "ready": true
}
```

**Status: TRUE.** Source used: the page's SSR payload (`state.playlist[0]`) plus
`POST /coworlds/replays/session` — sources (a) and (b) are uninformative platform-wide, as the
playbook records. A **featured match is present** (`collab_cooking.r9.e1`, the round-9 episode,
finished 10:33:47Z, with both champions as the `first`/`second` matchup — the "fewer than two
ranked players" absence that attempt 1 hit is gone). The iframe `src` is the **static** route
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`, with `<cow_id>` =
`cow_19938c0f-195a-45f8-95da-761f0ffe04cb` (the canonical v0.1.3 coworld) and `<sha>` =
`sha256:ae8627b0c7abde4a8807b3fff2e641a9f289512221ecd494de9c9753afeb3cf1` URL-encoded (the
coworld's manifest_hash, matching STATE). `ready: true`. It is **not** a `/client/replay` pod URL.

---

## 7. Certification declared the static bundle

Source read: **the committed `runs/2026-08-25-collab-cooking/release-result.json`** — not `/tmp`,
and not re-downloaded: the file is present in the working tree and `git log` shows it was committed
by this run's remediation release (`1c6747b collab-cooking: 60 remediation release v0.1.3`,
superseding `d4b714c collab-cooking: 40 release-result v0.1.1`), i.e. it is the v0.1.3 artifact of
release run `32834816635`. No `gh run download` fallback was needed.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-25-collab-cooking/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

The surrounding transcript from the same file (`.certify.output_tail`, all ten steps):

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
`.certify.ok` is `true` and `.ok` is `true`.

**Status: TRUE.** The string contains `Replay liveness: skipped (static replay bundle declared`,
read from the committed `runs/2026-08-25-collab-cooking/release-result.json`.

---

## 8. Spectator judgment — the viewer was EXECUTED

Dispatched against the item-6 iframe `src` verbatim (the full URL including `?replay=` and `&v=2`):

```bash
SRC="$(jq -r .viewer_url /tmp/session9.json)"
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
# dispatched 2026-08-25T10:40:30Z
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 5 \
  | jq -r 'sort_by(.createdAt)|reverse|.[0]'      # -> 32838395169  2026-08-25T10:40:30Z
gh run watch 32838395169 -R Metta-AI/coworld-builder --exit-status
# {"conclusion":"success","status":"completed","url":"https://github.com/Metta-AI/coworld-builder/actions/runs/32838395169"}
gh run download 32838395169 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-25-collab-cooking/viewer-check
```

The new run was found by sorting `createdAt`, not by taking "the latest" blind. Artifacts committed
with this file at `runs/2026-08-25-collab-cooking/viewer-check/` (`viewer-smoke.json`,
`viewer-smoke.png`, `smoke-stdout.txt`, `smoke-stderr.txt` — the last is 0 bytes).

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-25-collab-cooking/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":2424,"clock":"TICK 2 OF 900 1 ORDER LIVE","scorebug":"Cog-B daveey working ▶ 0 Cog-D richard working ▶ 0 TICK 2 OF 900 1 ORDER LIVE Cog-C daveey-1 working ▶ 0 Cog-A Baseline working ▶ 0","feed_lines":0}
```
```bash
jq -c '.signals' …/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["ready"],"bridge_ready":true,"bridge_error":[]}
```
```bash
jq -r '.failure // "no failure"' …/viewer-smoke.json   ->  no failure
jq -r '.console_tail[]' …/viewer-smoke.json            ->  [bridge] ready
jq -r '.url' …/viewer-smoke.json
# https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_19938c0f-195a-45f8-95da-761f0ffe04cb/sha256%3Aae8627b0c7abde4a8807b3fff2e641a9f289512221ecd494de9c9753afeb3cf1/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fd0c99032-68e2-478a-9007-84fdf727336b.replay&v=2
```

The three scrub readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | clock readout |
|---|---|
| 0 % | `TICK 2 OF 900 1 ORDER LIVE` |
| 50 % | `TICK 468 OF 900 3 ORDERS LIVE` |
| 100 % | `TICK 900 OF 900 0 ORDERS LIVE` |

All three differ, in both the tick counter and the live-order counter — the timeline advances and
the HUD tracks it. `canvas_text` reports `total: 0` (this shell paints its board on the canvas and
its text in DOM chrome, so there is no clipped-label finding to make).

A second viewer-check run dispatched earlier this same phase against the round-8 replay through the
same static route (run **32837285266**, dispatched 10:27:07Z, conclusion `success`) reproduced the
result independently: `{"loaded":true,"ms":3535,"clock":"TICK 4 OF 900 1 ORDER LIVE","feed_lines":1}`,
signals `{"data_replay_loaded":"true","bridge":["ready"],"bridge_ready":true}`, scrub
`0% TICK 4 OF 900 1 ORDER LIVE / 50% TICK 467 OF 900 2 ORDERS LIVE / 100% TICK 900 OF 900 0 ORDERS LIVE`,
`no failure`. The committed artifact directory holds run **32838395169** (the round-9 featured
match, i.e. the item-6 `src`).

**Item 8 gate:** `loaded: true` ✅ and the three clock readouts differ ✅ → **TRUE**.

### What the screenshot shows

`runs/2026-08-25-collab-cooking/viewer-check/viewer-smoke.png` (1280×800, 233537 bytes), captured
at the end of the scrub sweep, i.e. at `TICK 900 OF 900`:

- **Transport strip, bottom**: rewind / step-back / play / `+5s` / play / loop / fast-forward
  buttons, a `spoilers` toggle, the counter `900 / 900`, and speed chips `1× 2× 3× 4× 8× 16×` with
  `1×` selected. Below it the full-width **scrubber with the momentum graph** — a dense band of
  orange and green ticks along the whole episode with the playhead pinned at the right end, labelled
  `LIVES LEAD`.
- **Scorebug, top**: four seats in the two-per-side arrangement — `Cog-B / daveey / chop → 0`,
  `Cog-C / daveey-1 / pot → 0`, `Cog-D / richard / carrying → 0`, `Cog-A / Baseline / carrying → 3`
  — around the centred clock `TICK 900 OF 900` with `0 ORDERS LIVE` beneath it.
- **Dish ticker**: `3 DISHES` at the left, then three chips in serve order —
  `● salad · Cog-A · t167`, `● soup · Cog-A · t239`, `● soup · Cog-A · t690` — and the `HEAT`
  toggle at the right.
- **Say band**: four seat columns; `Cog-B` "Chopping meat for soup, will deliver to pot after" and
  `Cog-C` "Moving to pot with meat. Cog-B bringing chopped meat. Will assemble soup immediately.",
  with `Cog-D no word yet` and `Cog-A no word yet` greyed (the two scripted seats never speak, which
  is correct).
- **Board**: the `open-kitchen` grid is visible behind the endcard, dimmed — station tiles, counter
  island, and cog markers `B`, `C`, `D`, `A` with carried-item glyphs down the right side.
- **Endcard**: `3 DISHES SERVED`, the caption `THE WHOLE BRIGADE SHARES ONE SCORE`,
  `47 tickets expired · 3 pots burned · 0 fryers burned`, then the ranked list
  `1. Cog-A Baseline 3 / 2. Cog-B daveey 0 / 3. Cog-C daveey-1 0 / 4. Cog-D richard 0`.
- **Feed overlay**, bottom right, dimmed under the endcard: the two champion say lines followed by
  `a salad ticket expires · nobody served it`, `a soup ticket expires · nobody served it`,
  `a fries ticket expires · nobody served it`, `a salad ticket expires · nobody served it`.

### Reconciliation against the replay record

Every readout matches `/tmp/ep9.replay` exactly. Dish-ticker chips `salad t167`, `soup t239`,
`soup t690` ↔ `jq '[…select(.ev=="serve")]'` →
`[{"t":167,"slot":3,"alias":"Cog-A","recipe":"salad"},{"t":239,…,"soup"},{"t":690,…,"soup"}]`.
Endcard totals ↔ `results.dishes: 3`, `orders_expired: 47`, `burned: {"pot":3,"fryer":0}`,
`delivered: [0,0,0,3]` under `aliases: ["Cog-B","Cog-C","Cog-D","Cog-A"]`. Scorebug names ↔
`results.names: ["daveey","daveey-1","richard","Baseline"]` — the filler is rendered `Baseline`,
never its policy name. Say band ↔ the **last two** plan events in the file, t862 Cog-B "Chopping
meat for soup, will deliver to pot after" and t865 Cog-C "Moving to pot with meat. Cog-B bringing
chopped meat. Will assemble soup immediately." — verbatim. Mid-scrub `50% TICK 468 … 3 ORDERS LIVE`
sits between the t446 `order_expire soup` and the t452/453 fallbacks in the event stream; the early
readout `TICK 2` sits right after t1 `episode_start` + `order_arrive soup`.

### Spectator judgment

**It is legible, it is the starter's chrome, and it does show the game.** The picture is neither
empty nor frozen: the viewer reports `loaded: true` in 2.4 s via both `data-replay-loaded="true"`
and the `coworld-replay` bridge's `ready`, and three scrubs read three different ticks with three
different live-order counts, so a spectator can move through the episode and see it change. The
chrome is the coworld-ctf/paintbot/raid/hive family the design declared — the same bottom transport
strip with speed chips and a `spoilers` toggle, the same full-width scrubber with a momentum graph,
the same four-seat scorebug wrapped around a centred clock, the same endcard — with this game's two
declared additions layered on it: the dish ticker in serve order and the `HEAT` collision-heat-map
toggle. This is not the cogame-gridlock failure of a rewrite that merely shares ids.

What a spectator learns is exact and slightly damning: at the pass, `3 DISHES SERVED`, all three by
`Cog-A / Baseline`, the scripted filler; both LLM champions finish on 0; `47 tickets expired · 3
pots burned`. The say band explains why in the champions' own words — for the entire episode Cog-B
and Cog-C narrate a soup they never finish assembling ("Cog-B bring chopped_meat", "waiting for
Cog-C's chopped meat"), which is precisely the coordination failure `open-kitchen` exists to
expose, and the feed's repeated "nobody served it" lines make the cost visible. So the viewer is
telling the truth about a game whose champions currently play it badly, which is a **balance /
prompt-quality** finding for the coordinator, not a viewer or a platform defect.

Two legibility observations to carry forward, neither a check failure:
1. **`feed_lines: 0` reproduces from attempt 1** while the feed overlay is plainly populated in the
   PNG (six lines, bottom right) and the say band carries both champion lines. The round-8 run of
   the same probe returned `feed_lines: 1`. This is a **probe selector mismatch** against this
   shell's feed nodes, not an empty feed — confirmed by the screenshot, which is rendered evidence,
   and by the say-band text matching the replay's last two plans verbatim.
2. The endcard is a full-width overlay that dims the board it sits on. At 100 % scrub that is the
   correct final state, but a spectator scrubbing back has to move off the last frame before the
   kitchen is fully readable again.
