# VERIFY — sokoban   (2026-09-03T19:42Z)

Verdict: **all-true** (8/8) — with two recorded findings that are *not* definition-of-done
failures and are named for the judge: **4e** (the design note's extra `levelsSolved ≥ 1` bar is not
met by the latest round's champion episodes) and **6c** (the page's SSR `playlist` rail is
structurally empty for a single-seat game; the featured match resolves through the `showcase` mode
instead).

Environment for every call below (headers named, never their values):

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_81761ec5-88ed-4a94-b9b5-89d8b93b90fe
D=div_e9cf6fb5-77d8-471d-aad1-d808fd28e1cb
COW=cow_71631422-adaa-43fd-b234-5f1aa8a08b43
```

All evidence below was fetched fresh in this run (2026-09-03T19:28Z–19:42Z). The two documented
exceptions to "fetch fresh" are item 7 (the committed `release-result.json` from phase 40) and
item 8 (the artifact of the `viewer-check.yml` runs dispatched in this run).

---

## 1. ≥2 completed rounds after the fillers were set

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end
          | [.[]|{id,round_number,status,error,created_at,completed_at}]'
```

```json
[
  {
    "id": "round_df339820-d1e5-49bf-ba9d-dafd922900f9",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-09-03T19:25:36.703599Z",
    "completed_at": "2026-09-03T19:29:22.491622Z"
  },
  {
    "id": "round_dc0067cb-f121-4de9-a81f-98c3cfc6741e",
    "round_number": 1,
    "status": "completed",
    "error": null,
    "created_at": "2026-09-03T19:10:35.748824Z",
    "completed_at": "2026-09-03T19:14:17.788367Z"
  }
]
```

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end
          | [.[]|select(.status=="completed")]|length'
```

```
2
```

No round has `status` `failed` or `discarded`; both `error` fields are `null`. (A third round,
`round_86a273e3-c46d-44fb-b0d0-b1965fed95a2`, was `pending` at the 19:41Z poll — not counted.)

The fillers were set **before** any round existed. Fresh read of the live filler list (this read
needs the elevated header even though it is a read — playbook §6):

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"
```

```json
{"filler_policy_versions":[
 {"policy_version_id":"ddfec3df-23c8-4b98-aa49-1def5e2aef51","policy_id":"8a80f0bf-d027-4232-a991-6cb08005842f","policy_name":"sokoban-pusher","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null},
 {"policy_version_id":"fc2ef667-951c-4501-a75f-fec5d0b583bf","policy_id":"504a4796-5270-4dff-b839-30994199173f","policy_name":"sokoban-nudger","version":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","display_name":null}]}
```

`log.md` records the registration: `2026-08-29T10:59:29Z 50 fillers 200 pusher=ddfec3df
nudger=fc2ef667` — five days and one operator credit-grant before round 1 was created
(`2026-09-03T19:10:35Z`). Every completed round is post-filler-registration.

**Status: TRUE** — rounds 1 and 2 completed at 19:14:17Z and 19:29:22Z on 2026-09-03; fillers set
2026-08-29T10:59:29Z; 0 failed, 0 discarded.

---

## 2. Both champions ranked, fillers absent or Baseline

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```

```
1	Andrew Brower	sokoban-example:v1	1162.7348458168515	2	12.0
2	richard	co-gas-sokoban-push-space-richard:v4	1108.2440527389058	2	10.0
3	Andre von Auto	gruzchik:v1	1032.0	2	7.0
4	daveey	sokoban-lookahead:v1	990.0465598545583	2	6.0
5	relh	co-gas-sokoban-push-space-relhalpha:v1	955.7559472610942	2	4.0
6	daveey-1	sokoban-orderfirst:v1	913.9534401454417	2	3.0
7	docxology		837.2651541831485	2	0.0
```

- `daveey` — rank 4, `sokoban-lookahead:v1`, `rounds_played = 2` ✓
- `daveey-1` — rank 6, `sokoban-orderfirst:v1`, `rounds_played = 2` ✓
- Fillers `sokoban-pusher:v1` and `sokoban-nudger:v1`: **absent** from the leaderboard ✓
  (the filler seats are renamed/never scored; no `Baseline (N)` row exists either).

The other five rows are outside submitters who entered this public league on their own
(`sokoban-example`, `co-gas-sokoban-push-space-richard`, `gruzchik`,
`co-gas-sokoban-push-space-relhalpha`, `docxology`). They are not our policies and not fillers.

**Status: TRUE** — both champions ranked with `rounds_played = 2`; neither filler appears.

---

## 3. Latest completed round's episode requests completed with a `replay_url`

The flat `GET /episode-requests?round_id=` route is 405 since 2026-08-26 (playbook §9), so the
nested route is used.

```bash
R=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
    | jq -r 'if type=="array" then . else .entries end
             | [.[]|select(.status=="completed")]|max_by(.round_number).id')   # round_df339820… (round 2)
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" \
 | jq -c 'if type=="array" then . else .entries end | [.[]|{id,status}]'
```

```json
[{"id":"ereq_0c2e3746-ab43-4d8c-960b-c542d3ef7111","status":"completed"},
 {"id":"ereq_29c9fae7-1ec8-4865-9609-9b37200255b3","status":"completed"},
 {"id":"ereq_72307aa1-4f25-422a-a7d7-5f1c17833a7a","status":"completed"},
 {"id":"ereq_3abc05c3-a709-46e0-b25a-6cf3769e6c56","status":"completed"},
 {"id":"ereq_2c2f6716-5752-46eb-b869-894ae7ecf5ce","status":"completed"},
 {"id":"ereq_2de2a8f9-b58a-4762-9353-85bdb0d9379f","status":"completed"},
 {"id":"ereq_6fdc0eb2-4c9e-46f2-a88e-49b33a6f91f3","status":"failed"}]
```

**Adaptation, stated plainly:** sokoban is a **single-seat** game (`variant_name: "Tier ladder
(1 cog, 6 Sokoban levels)"`, `num_agents = 1`), so no episode can contain two players. The
checklist's "participants naming `daveey` **and** `daveey-1`" is therefore satisfied across the
round's episode set, one champion per episode, not inside one episode. Both champion episodes were
fetched:

```bash
curl -sS "$BASE/episode-requests/ereq_3abc05c3-a709-46e0-b25a-6cf3769e6c56" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/18ab1e45-c40c-442a-b964-a82fb10a0b6a.replay",
  "participants": [
    {"position": 0, "kind": "policy",
     "policy_version_id": "a2976627-29f4-4743-a9f3-5a436821f484",
     "policy_id": "72500d50-9668-4daf-8524-f07cbe2a5fc8",
     "policy_name": "sokoban-lookahead", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
     "player_name": "daveey", "is_filler": false, "is_seed": false}
  ],
  "participant_scores": [{"position": 0, "score": 70000.0}]
}
```

```bash
curl -sS "$BASE/episode-requests/ereq_29c9fae7-1ec8-4865-9609-9b37200255b3" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/435d4b63-fa8d-403f-9ee4-330c2764c049.replay",
  "participants": [
    {"position": 0, "kind": "policy",
     "policy_version_id": "dc5865c2-c797-44f7-8e83-641da09112b0",
     "policy_id": "40a7b83f-85e0-4673-ba33-e191a3f0ef01",
     "policy_name": "sokoban-orderfirst", "version": 1,
     "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
     "player_name": "daveey-1", "is_filler": false, "is_seed": false}
  ],
  "participant_scores": [{"position": 0, "score": 60000.0}]
}
```

The one `failed` episode request in the round, error recorded verbatim (it belongs to an outside
submitter's policy, not to ours; the round itself settled `completed`):

```json
{"ereq":"ereq_6fdc0eb2-4c9e-46f2-a88e-49b33a6f91f3","status":"failed","replay_url":null,
 "participants":[{"position":0,"policy_name":"daf-cogame-carrier","version":1,
                  "player_name":"docxology","is_filler":false}],
 "participant_scores":[],
 "error":"player slot 0 never registered; the seat played the pusher baseline"}
```

(The same outsider policy failed identically in round 1, `ereq_eaf301a0-5851-4d2b-8a96-9d2da621757f`.
The filler substitution named in the error is our `sokoban-pusher` baseline doing its job.)

**Status: TRUE** — round 2's champion episode requests `ereq_3abc05c3…` (daveey) and
`ereq_29c9fae7…` (daveey-1) are both `completed` with non-null `replay_url`s and correct
participants; 6 of 7 episode requests completed, the 7th belongs to a third party.

---

## 4. Replay bytes are valid and show the game

**Documented exception, cited.** The replay is **binary**, not JSON: `design.md` §"Replay bytes
(self-sufficient)" (lines 1221–1246) declares the fork keeps the coworld-ctf starter's container
under a new magic, and the repo's `docs/PROTOCOL.md` — the document the coworld manifest names as
the protocol (`game.protocols.player/global` →
`https://github.com/Metta-AI/cogame-sokoban/blob/main/docs/PROTOCOL.md`) — says so on line 61:
"Binary, magic **`COWLDSOK`**". The first bytes off S3 confirm it:

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/18ab1e45-c40c-442a-b964-a82fb10a0b6a.replay" -o /tmp/ep.replay
od -A d -t x1 /tmp/ep.replay | head -2
```

```
0000000 43 4f 57 4c 44 53 4f 4b 01 00 07 00 00 00 73 6f
0000016 6b 6f 62 61 6e 01 00 00 00 31 0a 00 00 00 73 6f     # "COWLDSOK" … "sokoban" … "sokoban/v1"
http=200 bytes=110982
```

The same design section defines "**the phase-60 substitute for `docs/SPEC.md` §Definition of done
check 4**": run the repo's stdlib-only `tools/replay_summary.py`, which emits **one strict-UTF-8
JSON object**, and assert on that. The tool was fetched from the coworld repo this run
(`gh api repos/Metta-AI/cogame-sokoban/contents/tools/replay_summary.py`) and run unmodified:

```bash
python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json
jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .results.reason, .results.endRule, .results.levelsSolved' /tmp/ep.json
jq -c '{plans:(.plans|length), llm:([.plans[]|select(.source=="llm")]|length),
        fallbacks:(.fallbacks|length), says:(.says|length)}' /tmp/ep.json
```

```
strict UTF-8 JSON: ok
sokoban/v1
complete
ladderComplete
0
{"plans":53,"llm":53,"fallbacks":0,"says":53,"budgetGuards":0,"stops":[]}
```

Full results document of the latest round's champion episode (daveey / `sokoban-lookahead:v1`):

```json
{"names":["lookahead"],"aliases":["Alpha"],"scores":[70000],"win":[false],"winner":null,
 "reason":"complete","endRule":"ladderComplete","variant":"ladder","seed":5328457908461284397,
 "levelCount":6,"stepBudget":200,"parWeight":5,"maxWeight":12,"solvedWeight":0,"levelsSolved":0,
 "boxCredit":7,"movesSavedTotal":0,
 "levelTier":["unfiltered","unfiltered","medium","medium","hard","hard"],
 "levelOptPushes":[11,7,17,19,23,24],
 "levelOutcome":["deadlocked","outofsteps","outofsteps","outofsteps","outofsteps","outofsteps"],
 "levelBoxesPlaced":[2,2,2,1,0,0],"levelMoves":[44,200,200,200,200,200],
 "levelTurns":[3,10,10,10,10,10],"levelPushes":[2,5,10,3,0,0],
 "deadlocks":1,"outOfSteps":5,"pushesTotal":20,"blockedMoves":0,"actionsDropped":0,
 "macrosUnreachable":6,"repliesRepaired":0,"finalTick":1044,"turnsPlayed":53,
 "policyKinds":["llm"],"llmTurns":53,"fallbackTurns":0,"deadSeats":[false],"stopDetail":""}
```

All four champion episodes across both completed rounds, same procedure:

| replay | seat | reason / endRule | llm plans | fallbacks | pushes | levelsSolved | score |
|---|---|---|---|---|---|---|---|
| `18ab1e45…` (r2) | daveey / lookahead | complete / ladderComplete | 53 / 53 | 0 | 20 | **0** | 70 000 |
| `435d4b63…` (r2) | daveey-1 / orderfirst | complete / ladderComplete | 51 / 51 | 0 | 32 | **0** | 60 000 |
| `c6762631…` (r1) | daveey / lookahead | complete / ladderComplete | 47 / 47 | 0 | 35 | **1** | 1 130 137 |
| `83f8e02a…` (r1) | daveey-1 / orderfirst | complete / ladderComplete | 49 / 49 | 0 | 33 | 0 | 100 000 |

Sub-verdicts:

- **4a** strict UTF-8 JSON — **TRUE** via the design-declared substitute (`jq -e .` accepts
  `replay_summary.py`'s output; the raw bytes are the declared binary container).
- **4b** `protocol` matches — **TRUE**: `sokoban/v1`, identical to `docs/PROTOCOL.md` line 3
  ("Protocol name: **`sokoban/v1`**"), the document the manifest points at.
- **4c** `results.reason` — **TRUE**: `complete` (`endRule: ladderComplete`), the design's primary
  legal value; no `deadline` exception needed.
- **4d** champion seats doing the thing the game is about — **TRUE**: 53 of 53 turns
  `source == "llm"`, **0 fallbacks**, 20 real pushes, 7 crates parked on targets, and a `say` line
  every turn. Ordered excerpts (early / middle / late):

  ```
  turn lvl src  executed              push say
  1    0   llm  ....................  0    Planning phase: analyzing crate positions and target assignments.
  2    0   llm  UUUURRRRDD..........  1    Box2 pushed down to (8,7)=target. This is safe and completes the crate.
  3    0   llm  LLLD                  1    Push box2 down to its target (8,7). Three crates now solved.
  4    1   llm  UUULLD..............  1    Push box2 down to (2,5)→(2,7), landing on target. Verify: (2,7) is target, not dead. No 2x2 trap.
  …
  27   3   llm  ....................  0    Box0 is trapped at (3,2) - both U and D push to dead squares. Need to clear a path first.
  28   3   llm  ....................  0    STUCK: Box0 at (3,2) has no safe push. Both U→(3,1) and D→(3,3) are dead_squares. Level is deadlocked.
  …
  52   5   llm  ....................  0    Level is deadlocked. All three available pushes lead to death or 2×2 lock. Suspending action.
  53   5   llm  ....................  0    Level 6 is deadlocked. All four boxes are trapped in an unbreakable 2×2 wedge configuration with no valid unblocking path.
  ```
- **4e** the design note's *additional* bar `results.levelsSolved >= 1` — **FALSE for the latest
  round**: both champions solved 0 of 6 levels in round 2. It is **TRUE** for round 1's daveey
  episode (`c6762631…`, `levelOutcome[1] == "solved"`, `solvedWeight 1`, score 1 130 137). This is
  a *policy strength* result, not an engine defect: the same engine registered 3 solves for
  `sokoban-example` (score 6 210 286) and 2 for `co-gas-sokoban-push-space-richard` (4 180 409) in
  the very same round 2. **Named for the judge; it is not one of SPEC §Definition of done item 4's
  clauses.**

**Status: TRUE** on SPEC §Definition of done item 4 (valid JSON under the declared substitute,
protocol match, `reason: complete`, non-scripted non-trivial champion decisions, zero fallbacks),
with finding **4e** recorded above.

---

## 5. Hosted game log is clean

```bash
curl -sS "$BASE/episode-requests/ereq_3abc05c3-a709-46e0-b25a-6cf3769e6c56/artifacts/logs" \
     "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs.raw          # http=200, 7507 bytes
python3 /tmp/declog.py /tmp/logs.raw > /tmp/logs.txt      # ast.literal_eval per b'…' repr, per playbook §10
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs.txt \
  || echo CLEAN
```

```
CLEAN
```

Same for the other champion's episode in the same round:

```bash
curl -sS "$BASE/episode-requests/ereq_29c9fae7-1ec8-4865-9609-9b37200255b3/artifacts/logs" \
     "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs2.raw          # http=200, 7284 bytes
python3 /tmp/declog.py /tmp/logs2.raw | grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' || echo CLEAN
```

```
CLEAN
```

The decoded log, containers `coworld-init-config` / `bedrock-sidecar` / `game` / `worker`
(tail pasted; every LLM call returned 200):

```
2026-09-03 19:28:39,488 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 19:28:42,244 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"
2026-09-03 19:28:44,844 INFO httpx HTTP Request: POST https://openrouter.ai/api/v1/messages "HTTP/1.1 200 OK"

===== container: game =====
sokoban: seed not pinned; randomized to 5328457908461284397
sokoban: seats=1 variant=ladder levels=6 stepBudget=200 maxTicks=1200 wallClock=690s model=
sokoban: serving on 0.0.0.0:8080
sokoban: player slot 0 connected (1/1)
sokoban: slot 0 registered (1754 prompt chars, llm)
sokoban: starting with 1/1 players connected
sokoban llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
sokoban: writing replay (110982 bytes) and results
sokoban: episode complete (complete/ladderComplete) after 1044 ticks, 0 of 6 levels solved, score 70000
```

**Status: TRUE** — zero matching lines in either champion's hosted log for the latest completed
round. No platform-wide-cause exception needed.

---

## 6. The public page uses the static replay path, and a featured match is present

**Sources used, in order (the check allows two; all four are recorded):**

**(a) Raw-HTML grep — found nothing (treated as *unknown*, not a failure, per the prompt).**

```bash
curl -sS "https://softmax.com/sokoban" -o /tmp/page.html -w "%{http_code} %{size_download}\n"
grep -o '<iframe[^>]*src="[^"]*"' /tmp/page.html || echo "NO IFRAME IN RAW HTML"
```

```
200 865952
NO IFRAME IN RAW HTML
```

**(b) The coworld detail API.**

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end
          | .[]|select(.name=="sokoban")|{id,name,version,canonical,replay_viewer,featured_match}'
```

```json
{
  "id": "cow_71631422-adaa-43fd-b234-5f1aa8a08b43",
  "name": "sokoban",
  "version": "0.1.0",
  "canonical": true,
  "replay_viewer": null,
  "featured_match": null
}
```

`featured_match: null` is the platform-wide value the playbook already records ("`/coworlds`'
`featured_match` is `null` platform-wide, so neither is evidence") — it is not evidence either way.

**(c) The page's SSR payload — `state.playlist` is empty, `state.pool.replays` has 6.**

```bash
python3 - # extract state from the RSC flight payload of /tmp/page.html
```

```json
{"playlist": [], "divisionName": "Competition", "playerCount": 7, "activeRound": null,
 "newestCompletedAt": "2026-09-03T19:29:22.491622Z",
 "pool.replays": [
  {"score": 6210286, "round": 2, "ep": 3, "player": "Andrew Brower", "policy": "sokoban-example",
   "replay_url": "https://softmax-public.s3.amazonaws.com/replays/63f695d7-ac84-45d1-8dcd-472bddb64814.replay"},
  {"score": 4180409, "round": 2, "ep": 1, "player": "richard", "policy": "co-gas-sokoban-push-space-richard",
   "replay_url": "https://softmax-public.s3.amazonaws.com/replays/5ad706bb-e9f0-439a-93df-656b910e7bcb.replay"},
  {"score": 2130246, "round": 2, "ep": 5, "player": "Andre von Auto", "policy": "gruzchik", "…": "…"},
  {"score": 100000,  "round": 2, "ep": 6, "player": "relh", "policy": "co-gas-sokoban-push-space-relhalpha", "…": "…"},
  {"score": 70000,   "round": 2, "ep": 4, "player": "daveey", "policy": "sokoban-lookahead",
   "replay_url": "https://softmax-public.s3.amazonaws.com/replays/18ab1e45-c40c-442a-b964-a82fb10a0b6a.replay"},
  {"score": 60000,   "round": 2, "ep": 2, "player": "daveey-1", "policy": "sokoban-orderfirst", "…": "…"}]}
```

Why `playlist` is empty, from the page's **own** client bundle (fetched from softmax.com this run,
`/_next/static/chunks/3eacjjdko9bjx.js`), verbatim:

```js
function i(e,t){if("completed"!==e.status||!e.episode_id||!e.coworld_id||!e.replay_url)return!1;
 let r=new Set(e.participants.flatMap(e=>"policy"!==e.kind||e.is_filler||e.is_seed?[]:[e.player_id]));
 return r.has(t.first.player_id)&&r.has(t.second.player_id)}          // isWatchableReplayEpisode
```

`playlist` only admits episodes containing **both** the rank-1 and rank-2 players. Sokoban is
single-seat, so no episode ever can — hence `playlist: []`. Cross-check on three shipped coworlds
fetched the same way: paintbot `playlist 19 / pool 19`, hive `1 / 1`, raid `3 / 5`; for raid the
three admitted episodes (2, 5, 6) are exactly the ones whose participant lists contain both daveey
(rank 1) and Andrew Brower (rank 2), and episodes 3 and 4 — each missing one of them — are the two
dropped. The rule is confirmed, not assumed.

The featured match is still produced, by the next mode in the same bundle's default chain
`F=["top-two","mine","showcase"]`, and `showcase` reads the **pool**, not the playlist:

```js
case"showcase":let a=function(e){if(0===e.length)return null;let t=e.filter(e=>u(e.episode));
 return t.length>0?t.reduce((e,t)=>c(t.episode)>c(e.episode)?t:e):e[0]}(t.replays.slice(0,24));
 if(a){let e=u(a.episode)?`peak score ${y(c(a.episode))}`:"latest available replay";
 return{match:a,reason:e}}…
```

and the page's own status chip (`/_next/static/chunks/2a7k4vtdf44_m.js`) reads

```js
e.pool.live?{label:"LIVE",…}:e.playlist.length>0||e.pool.replays.length>0?{label:"NOW SHOWING",…}
 :{label:"BETWEEN ROUNDS",…}
```

so with 6 pooled replays the page is "NOW SHOWING" and the featured match is the peak-score entry:
Andrew Brower's `sokoban-example` episode, replay `63f695d7-…`, score 6 210 286.

**(d) The viewer URL the page's own JS asks for** (playbook §Featured match / replay route):

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_71631422-adaa-43fd-b234-5f1aa8a08b43",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/63f695d7-ac84-45d1-8dcd-472bddb64814.replay"}'
```

```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_71631422-adaa-43fd-b234-5f1aa8a08b43/sha256%3A91df94dc27d710b8116aca94e1fe8c9162302f8e54661a3bbeabb3cff15f11bd/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F63f695d7-ac84-45d1-8dcd-472bddb64814.replay","ready":true}
```

The same call for the champion replay `18ab1e45-…` returns the identical shell path with that
replay in the fragment, also `"ready": true`.

Path check: `/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?v=2#replay=<s3 url>` —
`<cow_id>` = `cow_71631422-adaa-43fd-b234-5f1aa8a08b43` (STATE), `<sha>` =
`sha256:91df94dc27d710b8116aca94e1fe8c9162302f8e54661a3bbeabb3cff15f11bd` URL-encoded
(= `STATE.coworld.manifest_sha`). It is the **static** route in the fragment form the playbook
records for post-2026-08-28 sessions. It is **not** a `/client/replay` pod URL.

Sub-verdicts: **6a** static route — TRUE. **6b** featured match present — TRUE (showcase mode over
`pool.replays`, evidence pasted above). **6c** *finding*: the `playlist` rail and the `top-two`
featured mode are permanently empty for a single-seat coworld, so the page never shows the
"1st vs 2nd" framing other coworlds get. Not a definition-of-done failure; a legibility note for
the coordinator/phase 30.

**Status: TRUE** — source used: **the page (raw grep → nothing; SSR payload + client bundle) plus
the `replays/session` endpoint**; the coworld detail API was read too and is null platform-wide.

---

## 7. Certification declared the static bundle

Read from the committed phase-40 artifact, **not** `/tmp`:

```bash
jq -r '.certify.replay_liveness' runs/2026-08-29-sokoban/release-result.json
```

```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Source: **the committed `runs/2026-08-29-sokoban/release-result.json`** (present in git from phase
40, release run `33248649858`); no re-download was needed.

**Status: TRUE** — the certification output contains `Replay liveness: skipped (static replay
bundle declared`.

---

## 8. Spectator judgment — the viewer was EXECUTED

Two `viewer-check.yml` runs were dispatched **in this run**, both against the check-6 static shell,
differing only in the `#replay=` fragment. The **primary** is the featured match (the exact iframe
`src` item 6 resolves to); the second is the champion's own episode, dispatched first, kept as
supporting evidence.

```bash
SRC='…/index.html?v=2#replay=…63f695d7-ac84-45d1-8dcd-472bddb64814.replay'   # the featured match
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
# dispatched 2026-09-03T19:37:34Z; new run found by createdAt, not by -L 1:
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:3][]|[.databaseId,.createdAt,.status]|@tsv'
```

```
33797533088	2026-09-03T19:37:35Z	in_progress     <- mine (dispatch 19:37:34Z)
33797485426	2026-09-03T19:37:05Z	in_progress     <- another run's, 29 s earlier
33797350340	2026-09-03T19:35:43Z	completed
```

Ownership of each artifact was confirmed from `viewer-smoke.json`'s own `url` field, not from the
listing order.

| | primary | supporting |
|---|---|---|
| run id | **33797533088** | 33797255773 |
| conclusion | success | success |
| replay in the URL | `63f695d7…` — the featured match, `sokoban-example` (Andrew Brower) | `18ab1e45…` — daveey / `sokoban-lookahead:v1` |
| artifact committed at | `runs/2026-08-29-sokoban/viewer-check/` | `runs/2026-08-29-sokoban/viewer-check-champion/` |

### Primary — run 33797533088 (the featured match)

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-29-sokoban/viewer-check/viewer-smoke.json
jq -c '.signals' …
jq -r '.scrub[]|"\(.at)\t\(.clock)"' …
jq -r '.failure // "no failure"' …
```

```json
{"loaded":true,"ms":2127,"clock":"SOLVED 0/6 WEIGHT 0/12 · MOVE 0/200 · SCORE 0","scorebug":"ALPHA pusher SCORE 0 SOLVED 0/6 WEIGHT 0/12 · MOVE 0/200 · SCORE 0","feed_lines":0}
```

```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

| scrub | clock readout |
|---|---|
| 0 % | `SOLVED 0/6 WEIGHT 0/12 · MOVE 0/200 · SCORE 0` |
| 50 % | `SOLVED 2/6 WEIGHT 3/12 · MOVE 44/200 · SCORE 3120229` |
| 100 % | `SOLVED 3/6 WEIGHT 6/12 · MOVE 143/200 · SCORE 6210286` |

```
failure: no failure
canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
console tail: 22 × "[warning] Unknown sprite protocol message type: 97", 1 × "… type: 34"
```

Three readouts, all different, and the 100 % readout equals the episode's recorded final state
exactly (see the reconciliation below). `loaded: true` via `data-replay-loaded="true"`.

### Supporting — run 33797255773 (the champion's episode)

```json
{"loaded":true,"ms":5958,"clock":"SOLVED 0/6 WEIGHT 0/12 · MOVE 0/200 · SCORE 0","scorebug":"ALPHA pusher SCORE 0 SOLVED 0/6 WEIGHT 0/12 · MOVE 0/200 · SCORE 0","feed_lines":0}
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```

| scrub | clock readout |
|---|---|
| 0 % | `SOLVED 0/6 WEIGHT 0/12 · MOVE 0/200 · SCORE 0` |
| 50 % | `SOLVED 0/6 WEIGHT 0/12 · MOVE 87/200 · SCORE 60000` |
| 100 % | `SOLVED 0/6 WEIGHT 0/12 · MOVE 87/200 · SCORE 60000` |

```
failure: no failure
```

Recorded honestly: in this run the **100 % seek did not take** — the readout and the screenshot
both sit at tick 531/1044, the 50 % position, so only two of the three readouts differ. It is a
seek-responsiveness flake, not a frozen viewer: the same shell, in the run 30 seconds later,
produced three distinct readouts ending on the true final frame, and this run's own 0 %→50 %
transition moved the board, the level banner, the score and the playhead. The likely cause is the
harness's fixed 700 ms wait after each click landing inside this shell's incremental
keyframe-to-tick-531 scan (this run loaded in 5 958 ms against the other's 2 127 ms, i.e. a slower
CI box). **Legibility note for the coordinator: the scrubber can swallow a seek issued while an
earlier seek is still scanning — there is no visible "seeking" state.**

### Reconciliation — picture against record

Featured episode `63f695d7…` via `tools/replay_summary.py`:

```json
{"protocol":"sokoban/v1","names":["pusher"],"aliases":["Alpha"],"policyKinds":["scripted"],
 "plans":36,"says":0,"fallbacks":0,
 "results":{"reason":"complete","endRule":"ladderComplete","levelsSolved":3,"solvedWeight":6,
            "score":6210286,"finalTick":630,
            "levelOutcome":["solved","deadlocked","solved","deadlocked","deadlocked","solved"],
            "levelMoves":[50,109,121,64,143,143],"pushesTotal":97}}
```

Every number the viewer drew at 100 % matches that record: `SOLVED 3/6` = `levelsSolved 3`;
`WEIGHT 6/12` = `solvedWeight 6`; `MOVE 143/200` = `levelMoves[5]`; `SCORE 6210286` =
`scores[0]`; the transport reads `630 / 630` = `finalTick`; the level chip reads `LEVEL 6/6`; the
six tier dots under it read green/red/green/red/red/green — the `levelOutcome` array, in order.
The seat nameplate reads `pusher ALPHA` because that episode's registered seat name really is
`pusher` (`names:["pusher"]`, `policyKinds:["scripted"]` — the outside submitter's
`sokoban-example:v1` is a copy of the scripted baseline), so the viewer is reporting the replay,
not mislabelling it.

Champion episode `18ab1e45…` at the 50 % frame in the supporting run: the screenshot's caption box
reads `TURN 28 — 0 ACTIONS, 0 MOVES` and `Alpha: "STUCK: Box0 at (3,2) has no safe push. Both
U→(3,1) and D→(3,3) are dead_squares. Level is deadlocked."` — which is, verbatim, plan 28 of that
replay (`turn 28, level 3, source llm, executed "...................." (0 moves)`), and the banner
reads `LEVEL 4/6 · MEDIUM · 19 PUSHES · MOVE 87/200` against `levelTier[3] == "medium"`. The
picture and the record are the same episode, frame for frame.

### Spectator judgment

It is legible, and it shows the game. The screenshot is a lit stone room on a 10 × 10 grid: the
Softmax cog rendered as a small robot facing the way it last walked, wooden crates, amber diamonds
for the marked squares, and crates that are *on* a target outlined in green — one glance tells you
what is done and what is not. Hatched red squares mark the dead cells a crate can never come back
from, with a `DEAD SQUARES` minimap in the corner repeating them, which is the one thing a Sokoban
spectator needs and almost never gets. The top strip carries the score, the seat's nameplate and
the headline `SOLVED 3/6`, with `WEIGHT 6/12 · MOVE 143/200 · SCORE 6210286` under it; the level
chip names the level and, mid-episode, its tier and optimal push count (`LEVEL 4/6 · MEDIUM /
19 PUSHES · MOVE 87/200` in the champion run; the final frame's chip trims to `LEVEL 6/6 /
MOVE 143/200`). Under it sit six tier-sized dots labelled `U U M M H H` — the ladder's per-level
verdicts: in the primary run green / red-slash / green / red-slash / red-slash / green, i.e.
`levelOutcome` exactly; in the champion run mid-episode, a red slash for the dead level, grey for
the two burned on step budget, an amber ring for the level being played and hollow rings for the
levels not yet reached. The bottom is the starter's chrome unchanged — the same transport strip
(restart, step back, pause, +5 s, play, loop, fast-forward, a `spoilers` toggle, a `531 / 1044`
tick counter and 1×/2×/4×/8× speed chips), the same scrubber with beat markers above and the same
red momentum graph below it, labelled `CRATES PARKED` for this game. It is paintbot's/raid's/hive's
chrome with this game's board in it, not a lookalike rewrite: the cogame-gridlock failure mode is
absent.

It is not a still. Both runs moved the board with the scrubber, and the primary run walked it from
an empty score to the true final frame. What a spectator cannot yet get is *unattended* motion
evidence — the harness was not given `--soak`, so nothing here proves the viewer keeps playing on
its own; and the LLM seats' narration, which is genuinely the most interesting thing in this game
(`"STUCK: Box0 at (3,2) has no safe push…"`), is painted into the canvas rather than into DOM feed
nodes, so `feed_lines` reads 0 and `canvas_text` reads `total: 0` (a WebGL/worker renderer the
text-bounds hook cannot see). Two smaller blemishes, both visible in the artifact and neither
fatal: the console logs 20+ `Unknown sprite protocol message type: 97 / 108 / 34` warnings per
load — the renderer is skipping message kinds it does not know — and the champion's episodes spend
long stretches on turns with `0 ACTIONS, 0 MOVES` after the policy has announced a deadlock the
engine's sound-but-incomplete detector will not act on, which reads as a stalled picture even
though the tick counter is advancing. Both are phase-30 legibility items, not definition-of-done
failures.

**Status: TRUE** — `loaded: true` and three differing clock readouts on the check-6 iframe `src`
(run 33797533088); the supporting champion run also loaded and drew, with its third readout
recorded as a seek that did not take.

---

## Findings for the coordinator (none blocking)

1. **4e** — the champions solve 0/6 levels in round 2 (1/6 for daveey in round 1) while outside
   entrants solve 2/6 and 3/6 with scripted search. The ladder is working; the LLM prompts are
   simply losing. Worth a look before announcing "reasoning-model vs search ladder" as a result.
2. **6c** — `playlist` and the `top-two` featured mode can never populate for a single-seat
   coworld; sokoban's page is carried by the `showcase` fallback, and the featured slot will always
   be the peak-scoring replay (currently an outsider's scripted baseline, not a champion).
3. **8-i** — the scrubber can silently swallow a seek issued while a previous seek is still
   scanning; no "seeking" state is shown.
4. **8-ii** — `Unknown sprite protocol message type: 97 / 108 / 34` console warnings on every load.
5. **8-iii** — the say/feed text is canvas-painted, so DOM-based instruments (`feed_lines`,
   `canvas_text`) read zero; nothing is wrong on screen, but the automated legibility checks are
   blind to it.
6. `tools/replay_summary.py` reports `tickCount` equal to the replay's **byte length**
   (110 982 for a 110 982-byte file; the real final tick is 1 044, correctly reported under
   `results.finalTick`). Cosmetic bug in the forensics tool, not in the game.
