# VERIFY — rumor   (2026-08-23T21:29Z)

Verdict: **all-true** (8/8)

Run: `2026-08-23-rumor` · slug `rumor` · coworld `cow_46b04bae-028d-4f7a-8444-c18590d68521` v0.1.0
League `L = league_21909e9d-0b13-4750-afec-f8a4213c03a7` · Division `D = div_52959ca4-61f9-4828-bbe5-33261daea950`

Wall-clock window: verification opened `2026-08-23T21:06:54Z`, closed `2026-08-23T21:29Z` — 22 minutes,
inside the 75-minute bound. Polls of checks 1/3 at 21:06:54Z, 21:11:31Z, 21:16:26Z, 21:20:53Z, 21:24:21Z.

Every response below was fetched **this run**, fresh, except the two documented exceptions:
check 7 reads the committed `runs/2026-08-23-rumor/release-result.json`, and check 8 reads the
artifact of the `viewer-check.yml` run **this verifier dispatched at 21:25:38Z** (run `32667485621`).

Headers sent on every Observatory call (values never printed):
`Authorization: Bearer $SOFTMAX_TOKEN`, `User-Agent: coworld-builder/1.0`, and on `artifacts/logs`
and `filler-policies` additionally `X-Use-Elevated-Privileges: true`.

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
```

> **File provenance note (2026-08-23T21:38Z).** This file was truncated to 0 bytes shortly after it was
> first written, by a coordinator-side `git reset --hard` that materialised an empty tracked blob over
> the untracked write. It has been re-written from the verifier's own session transcript. **No evidence
> was re-fetched and no workflow was re-dispatched**; every command, response body and verdict below is
> the same one recorded at the timestamps stated. The two locally-held artifacts were restored
> independently (check 8's from GitHub artifact run `32667485621`, check 4's from its S3 `replay_url`)
> and were re-read from disk to confirm they still carry byte-for-byte the readouts pasted here:
> `{"loaded":true,"ms":732,"clock":"ROUND 1","scorebug":"","feed_lines":0}`, the three scrub readouts,
> and `rumor.replay.v1` / `complete`.

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

`GET $BASE/rounds?league_id=$L&limit=20` (fetched 2026-08-23T21:27:35Z)

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq '[.entries[]|{id,round_number,status,error,created_at,completed_at}]'
```

```json
[
  {
    "id": "round_bc98c02d-5791-4bc8-9ade-365b2a767963",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-23T21:19:32.776404Z",
    "completed_at": "2026-08-23T21:22:36.560536Z"
  },
  {
    "id": "round_e36090b2-ac66-4686-b56a-cafa77b2991a",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-23T21:04:32.362328Z",
    "completed_at": "2026-08-23T21:07:47.221116Z"
  },
  {
    "id": "round_b9fe65d5-3e2e-47df-ac62-c28a2e8d1783",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-23T21:04:00.591951Z",
    "completed_at": "2026-08-23T21:04:00.800201Z"
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

**The failed round, verbatim, and why it does not count against this check.** Round 1's `error` is
`"Temporal RoundWorkflow failed before settling the round."` — quoted in full above. It was
auto-created by the champion-#1 submission at `21:04:00.591951Z`, i.e. before phase 50's explicit
`trigger-round`. It is the exact failure `playbooks/observatory-api.md` §6 documents for a round that
races the filler registration, and `runs/2026-08-23-rumor/log.md:44` records it as such:
`21:05:58Z 50 unpause 200; trigger 200; round1 failed (auto-round pre-fillers), round2 pending with both champions in entrant_attributions`.
It is not counted; the two rounds counted are **2** and **3**.

**Proof the fillers were in force for rounds 2 and 3** (not just an inference from a log timestamp):

`GET $BASE/leagues/$L/filler-policies` with `AUTH` + `ELEV` (fetched 21:27:35Z)

```json
{
  "filler_policy_versions": [
    {"policy_version_id": "1c39bed2-6a01-445b-8581-a0123b2f58c8", "policy_name": "rumor-gossip",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"},
    {"policy_version_id": "212b1fe4-1a64-4c1f-a944-3a1439e01c12", "policy_name": "rumor-herd",
     "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey"}
  ]
}
```

Both ids match `STATE.policies.filler_version_ids` and neither is a champion version id
(champions are `3083c67e-…` / `e895c6ce-…`, see check 3). Round 3's `round_config` shows only the two
champions as entrants, so the other eight seats were drawn from that filler list — and check 3's
`participants` confirms eight seats with `is_filler: true`:

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" | jq -c '.entries[]|select(.round_number==3)|.round_config'
```
```json
{"stages":null,"purpose":"ladder","entrant_attributions":[{"subject_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","subject_type":"player","policy_version_id":"3083c67e-787c-4f23-a85c-722965b03985","league_policy_membership_id":"lpm_f2626389-b500-44ce-acea-6dff699c548d"},{"subject_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","subject_type":"player","policy_version_id":"e895c6ce-1933-4f00-a379-fe284cde22de","league_policy_membership_id":"lpm_61ee9dbb-2375-4eef-bc0b-19ff93547377"}],"entrant_policy_version_ids":["3083c67e-787c-4f23-a85c-722965b03985","e895c6ce-1933-4f00-a379-fe284cde22de"]}
```

**Status: TRUE** — rounds **2** (completed `21:07:47.221116Z`) and **3** (completed
`21:22:36.560536Z`) are `completed`, both after the fillers were registered (phase 50, before the
`trigger-round` that created round 2 at `21:04:32.362328Z`), and both were seated with those fillers.

---

## 2. Both champions ranked; fillers absent — **TRUE**

`GET $BASE/divisions/$D/leaderboard` (fetched 2026-08-23T21:27:35Z) — bare JSON list, not `.entries`.

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq .
```

```json
[
  {
    "rank": 1,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 1000.0,
    "score_label": "Elo",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 0.0,
    "episodes_played": null,
    "win_rate": 0.0,
    "policy_label": "rumor-corroborate:v1",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 1000.0,
    "score_label": "Elo",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 0.0,
    "episodes_played": null,
    "win_rate": 0.0,
    "policy_label": "rumor-skeptic:v1",
    "recent_rounds": null
  }
]
```

```bash
… | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey	rumor-corroborate:v1	1000.0	2	0.0
2	daveey-1	rumor-skeptic:v1	1000.0	2	0.0
```

**Status: TRUE** — `daveey` (`rumor-corroborate:v1`, `rounds_played` 2) and `daveey-1`
(`rumor-skeptic:v1`, `rounds_played` 2) are both ranked; `rounds_played ≥ 1` for both. The leaderboard
is exactly two rows: **fillers are absent**, so the "absent or `Baseline…`" condition is met by
absence. (Elo is 1000.0 for both because the two rounds ended level; that is the ladder's arithmetic,
not a missing result — `rounds_played` is 2 for both.)

---

## 3. Latest completed round's episode request completed, with a replay and the right seats — **TRUE**

Latest completed round: `round_bc98c02d-5791-4bc8-9ade-365b2a767963` (round_number 3).

```bash
R=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
    | jq -r '[.entries[]|select(.status=="completed")]|max_by(.round_number).id')
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}" | jq -c '[.entries[]|{id,status,created_at}]'
```
```json
[{"id":"ereq_07ed5434-ccf3-4d07-a4ee-81753599f3b0","status":"completed","created_at":"2026-08-23T21:19:33.149416Z"}]
```

```bash
EREQ=ereq_07ed5434-ccf3-4d07-a4ee-81753599f3b0
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" | jq '{status, replay_url}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/829157f1-6642-44f7-9543-566df8ac959c.replay"
}
```

`participants` (`position`, `policy_name`, `player_name`, `is_filler`) — full ten seats:

```bash
… | jq -r '[.participants[]|[.position,.policy_name,.player_name,.is_filler]|@tsv]|.[]'
```
```
0	rumor-corroborate	daveey	false
1	rumor-skeptic	daveey-1	false
2	rumor-herd	daveey	true
3	rumor-gossip	daveey	true
4	rumor-herd	daveey	true
5	rumor-herd	daveey	true
6	rumor-herd	daveey	true
7	rumor-herd	daveey	true
8	rumor-gossip	daveey	true
9	rumor-gossip	daveey	true
```

Seat 0 and seat 1 in full, showing the policy-version ids and the two distinct player ids:

```json
{"position": 0, "kind": "policy", "policy_version_id": "3083c67e-787c-4f23-a85c-722965b03985",
 "policy_id": "843365d2-2726-4071-a167-dc0c7328adf1", "policy_name": "rumor-corroborate", "version": 1,
 "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey", "is_filler": false}
{"position": 1, "kind": "policy", "policy_version_id": "e895c6ce-1933-4f00-a379-fe284cde22de",
 "policy_id": "c76ed9c9-eb3f-4fc4-9e97-a67bda4d1824", "policy_name": "rumor-skeptic", "version": 1,
 "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1", "is_filler": false}
```

```bash
… | jq -c '.participant_scores'
```
```json
[{"position":0,"score":0.55},{"position":1,"score":0.55},{"position":2,"score":0.55},{"position":3,"score":0.55},{"position":4,"score":-0.25},{"position":5,"score":-0.32142857142857145},{"position":6,"score":0.55},{"position":7,"score":-0.25},{"position":8,"score":-0.55},{"position":9,"score":-0.25}]
```

**Status: TRUE** — `status == "completed"`, `replay_url` non-null, and `participants` name
`daveey` and `daveey-1` at seats 0/1 with `is_filler: false`; the other eight are `is_filler: true`.
*Shape note:* this endpoint returns fillers as structured rows with `is_filler: true` rather than a
`Baseline (N)` display string; the `Baseline (N)` naming appears in the replay payload itself
(`policyNames`, pasted in check 4), so both forms of the requirement are met on record.

---

## 4. Replay bytes are valid and show the game — **TRUE**

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/829157f1-6642-44f7-9543-566df8ac959c.replay" -o /tmp/ep.replay
ls -l /tmp/ep.replay
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
jq -r '.protocol, .results.reason' /tmp/ep.replay
```
```
-rw-r--r-- 1 root root 18414 Aug 23 21:24 /tmp/ep.replay
strict UTF-8 JSON: ok
rumor.replay.v1
complete
```

18 414 bytes — under 5 MB, so the file is saved alongside this report at
`runs/2026-08-23-rumor/ep.replay`.

**`protocol` matches the manifest/design.** `rumor.replay.v1` is what the coworld's own source emits
and what the design declares:

```bash
gh api repos/Metta-AI/cogame-rumor/contents/src/rumor/server.nim --jq .download_url | xargs curl -sS | grep -n 'replay.v1'
```
```
522:    "protocol": payload{"protocol"}.getStr("rumor.replay.v1"),
```
```bash
grep -n "replay.v1" runs/2026-08-23-rumor/design.md
```
```
640:### Replay payload — `rumor.replay.v1`
643:{"protocol":"rumor.replay.v1",
```

**`results.reason == "complete"`** — the normal case, not the `deadline` exception the design allows.

`.results` in full:

```bash
jq -c '.results' /tmp/ep.replay
```
```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)","Baseline (5)","Baseline (6)","Baseline (7)","Baseline (8)"],"scores":[0.55,0.55,0.55,0.55,-0.25,-0.32142857142857145,0.55,-0.25,-0.55,-0.25],"roles":["Honest","Honest","Honest","Honest","Honest","Saboteur","Honest","Honest","Saboteur","Honest"],"votes":["A","A","A","A","B","B","A","B","B","B"],"clues":["A","A","B","A","A","A","A","A","A","B"],"truth":"A","question":"The mine's lower gallery is…","optionA":"FLOODED","optionB":"DRY","verdict":"split","accuracy":0.625,"honestCorrect":5,"honestSeats":8,"saboteurSeats":2,"topology":"hub","edgeCount":14,"rounds":5,"maxRounds":5,"reason":"complete"}
```

Note `names`: `daveey`, `daveey-1`, then `Baseline`…`Baseline (8)` — the fillers **are** renamed
`Baseline (N)` in the replay, as the playbook requires.

**Decisions and fallbacks — schema divergence, stated openly.** `prompts/60-verify.md`'s literal jq is
written against Bullwhip's replay schema (`.events[].type == "decision"`, `.events[].fallback`). Rumor's
`rumor.replay.v1` uses `kind` with values `start|round|say|vote|tally|end` and marks scripted play with
`.scripted`. The literal commands therefore return 0, and I am recording that rather than hiding it:

```bash
jq -r '[.events[]|select(.type=="decision")]|length' /tmp/ep.replay   # -> 0  (Bullwhip key; rumor uses .kind)
jq -r '[.events[]|select(.fallback==true)]|length' /tmp/ep.replay     # -> 0
grep -o -i fallback /tmp/ep.replay | wc -l                            # -> 0  (no such string anywhere in the bytes)
```
```
0
0
0
```

The equivalent rumor readouts:

```bash
jq -r '[.events[].kind]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.replay
```
```json
{"end": 1, "round": 6, "say": 50, "start": 1, "tally": 1, "vote": 10}
```
50 talk decisions (10 seats × 5 rounds) + 10 ballot decisions, exactly the shape `rules.md` specifies.

```bash
jq -r '[.events[]|select(.kind=="say")|.scripted]|group_by(.)|map({(.[0]|tostring):length})|add' /tmp/ep.replay
```
```json
{"false": 10, "true": 40}
```
The 10 non-scripted says are precisely the two champion seats × 5 rounds; the 40 scripted are the eight
baseline seats.

**Champion seats' decisions are non-scripted and non-trivial** (`round`, `seat`, `claim`,
`confidence`, `scripted`, `length(text)`):

```bash
jq -r '.events[]|select(.kind=="say" and (.seat==0 or .seat==1))|[.round,.seat,.claim,.confidence,.scripted,(.text|length)]|@tsv' /tmp/ep.replay
```
```
0	0	A	67	false	163
0	1	A	68	false	232
1	0	A	58	false	240
1	1	A	62	false	240
2	0	B	62	false	240
2	1	A	65	false	240
3	0	B	58	false	240
3	1	A	65	false	240
4	0	B	58	false	240
4	1	A	65	false	240
```

All ten are `scripted:false`, 163–240 runes (240 is the rules-declared cap, hit on a rune boundary),
with claims and confidences that **move between rounds** — seat 0 flips A→B on the network signal at
round 3 and back at the ballot; seat 1 holds A but re-prices confidence 68→62→65. That is play, not
a constant.

A champion decision verbatim (seat 0, round 5 talk):

```json
{"kind":"say","round":4,"seat":0,"claim":"B","confidence":58,"belief":38,"scripted":false,
 "text":"Round 5 final ledger by distinct source: Gasket (me)=FLOODED, Bolt=FLOODED, Sprocket=DRY citing 6-of-8 reports. Network majority rule: 6 reports for DRY vs 2 for FLOODED in Sprocket's reach. My clue says FLOODED but the aggregated network …",
 "notes":"Final tally: 3 distinct clues (Gasket=A, Bolt=A, Sprocket=B) gives 2-1 for FLOODED on clues alone. But Sprocket's 6-of-8 report represents majority of the network (rule: ten clues together point at truth; majority wins). Sprocket's 100% confidence remains suspicious (saboteur marker), but no contradicting corroboration from other sources. …"}
```

And a champion ballot verbatim (seat 1, `rumor-skeptic`, daveey-1):

```json
{"kind":"vote","round":5,"seat":1,"vote":"A","belief":72,"scripted":false,
 "text":"My own clue FLOODED (2/3 prior) + first-hand majority (Gasket also FLOODED). Sprocket's uncorroborated 6/8 count and unwavering 100% confidence across all rounds are hallmarks of sabotage. Tinker sim…",
 "notes":"FINAL TALLY — FIRST-HAND: Bolt=A (own clue), Gasket=A, Tinker=B, Sprocket=B. HEARSAY: Piston=A (weight 1/3). WEIGHTED: 2.5 for A, 1.5 for B. SABOTEUR PROFILE: (1) Sprocket—100% DRY every round, claims 6/8 for DRY but zero corroboration from any neighbour; fabricated count is the signature of paid misdirection. (2) Tinker—90% on only 2 reports, never moved despite hearing conflicting data; rigid certainty on minimal evidence. …"}
```

Both champions named the two real saboteurs (`roles` index 5 = Sprocket and index 8 = Tinker) and both
voted the truth `A`.

**Status: TRUE** — valid strict-UTF-8 JSON; `protocol` `rumor.replay.v1` matches source and design;
`results.reason == "complete"`; 60 recorded decisions of which the champions' 10 are `scripted:false`
with 163–240 runes of real content; **zero** fallbacks by any reading (the literal `.fallback` filter,
and a raw grep of the whole file).

---

## 5. Hosted game log is clean — **TRUE**

```bash
curl -sS "$BASE/episode-requests/$EREQ/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs3.raw
```
27 811 bytes. The body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so
it was decoded with `ast.literal_eval` per repr before grepping (playbook §10):

```bash
python3 /tmp/declog.py /tmp/logs3.raw /tmp/logs3.txt      # ast.literal_eval per b'…' line
grep -n '===== container' /tmp/logs3.txt
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs3.txt || echo CLEAN
```
```
1:===== container: coworld-init-config =====
4:===== container: bedrock-sidecar =====
58:===== container: game =====
111:===== container: worker =====
CLEAN
```

Proof the decode actually produced text (not still-encoded reprs that a grep would silently
undercount) — the `game` container, decoded, lines 92–110:

```
rumor: starting with 10/10 players connected
rumor llm: bedrock transport, url http://127.0.0.1:9100/model/us.anthropic.claude-haiku-4-5-20251001-v1:0/invoke
rumor: episode timeout 1200s (assumed); playing until 720s
rumor: round 1 of 5 at 7s
rumor: round 2 of 5 at 13s
rumor llm: rate governor holding 19s before the batch
rumor: round 3 of 5 at 45s
rumor llm: rate governor holding 13s before the batch
rumor: round 4 of 5 at 68s
rumor llm: rate governor holding 17s before the batch
rumor: round 5 of 5 at 93s
rumor llm: rate governor holding 17s before the batch
rumor: sealed vote at 121s
rumor llm: rate governor holding 15s before the batch
Dropped message to disconnected client
rumor: writing results and replay
rumor: episode complete, shutting down
```

and the connect phase, showing the two champion seats delivering real prompts (1230 / 1284 chars, no
`scripted` tag) against eight scripted baselines (1038 chars, `scripted herd` / `scripted gossip`):

```
rumor: player slot 0 connected (5/10)
rumor: slot 0 delivered a prompt (1230 chars)
…
rumor: slot 1 delivered a prompt (1284 chars)
rumor: slot 6 delivered a prompt (1038 chars, scripted herd)
rumor: slot 9 delivered a prompt (1038 chars, scripted gossip)
```

**Status: TRUE — CLEAN.** No `falling back`, no `LLM provider is unavailable`, no
`cut off at max_tokens`, no `rejected` in the decoded log of any of the four containers. No
platform-wide-Bedrock exception needed to be invoked for this run: the log is clean on its own
merits, so no cross-check against another LLM coworld was required. (`rate governor holding …` lines
are the coworld's own designed pacing before each parallel batch, not a provider error; `Dropped
message to disconnected client` is a spectator socket closing after the final frame.)

---

## 6. The public page uses the static replay path — **TRUE**

**Source used: the API the page reads** (the raw-HTML grep is *unknown*, not a negative — recorded
below), plus the page's SSR payload for the featured match.

*(a) The raw-HTML grep, run and recorded as inconclusive:*
```bash
curl -sS "https://softmax.com/rumor" | grep -o '<iframe[^>]*src="[^"]*"'
```
```
(no output; grep exit 1)
```
Per `playbooks/observatory-api.md` §Featured match, the page is **client-rendered** for the iframe on
every coworld, so this is not evidence either way. Falling back to the two API sources the page itself
uses.

*(b) The featured match, from the page's server-rendered SSR payload (`state.playlist[0]`), fetched
2026-08-23T21:25Z:*
```bash
curl -sS "https://softmax.com/rumor" | grep -o 'playlist\\":\[[^]]\{0,600\}'
```
```
playlist\":[{\"episodeId\":\"8807c2bb-dc23-4aa5-bcf6-1284fd0103d9\",\"coworldId\":\"cow_46b04bae-028d-4f7a-8444-c18590d68521\",\"coworldName\":\"rumor\",\"coworldVersion\":\"0.1.0\",\"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/829157f1-6642-44f7-9543-566df8ac959c.replay\",\"finishedAt\":\"2026-08-23T21:22:34.492117Z\",\"roundNumber\":3,\"episodeNumber\":1,\"code\":\"rumor.r3.e1\",\"matchup\":{\"divisionId\":\"div_52959ca4-61f9-4828-bbe5-33261daea950\",\"divisionName\":\"Competition\",\"first\":{\"rank\":1,\"player_id\":\"ply_44ae9048-3242-4654-881f-6d9d43347fa3\",\"player_name\":\"davee…
```
A **featured match is present** — `rumor.r3.e1`, round 3, the same `replayUrl` verified in check 4, with
a `matchup` naming the two ranked players. (An earlier fetch at 21:07Z showed `playlist\":[]`; it filled
in once round 3's episode landed. Both fetches are this run.)

*(c) The iframe `src`, from the call the page's JS makes:*
```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_46b04bae-028d-4f7a-8444-c18590d68521",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/829157f1-6642-44f7-9543-566df8ac959c.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_46b04bae-028d-4f7a-8444-c18590d68521/sha256%3A83e14e8087bf4e1fc862471588e251cb443b2b19dada715d9d0f0c3c97c56c51/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F829157f1-6642-44f7-9543-566df8ac959c.replay&v=2",
  "ready": true
}
```

The path is `/v2/coworlds/replays/**static**/<cow_id>/<sha>/index.html?replay=<s3 url>`.
`<sha>` = `sha256:83e14e8087bf4e1fc862471588e251cb443b2b19dada715d9d0f0c3c97c56c51` (URL-encoded),
which is the coworld's `manifest_hash` and matches `STATE.coworld.manifest_sha` exactly. `ready: true`.
There is **no** `/client/replay` anywhere in the URL.

*(d) `/coworlds` detail, for completeness (returns a bare array here, not `{entries:…}`):*
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end | .[]|select(.name=="rumor")|{id,name,version,canonical,manifest_hash}'
```
```json
{
  "id": "cow_46b04bae-028d-4f7a-8444-c18590d68521",
  "name": "rumor",
  "version": "0.1.0",
  "canonical": true,
  "manifest_hash": "sha256:83e14e8087bf4e1fc862471588e251cb443b2b19dada715d9d0f0c3c97c56c51"
}
```
This row has **no `replay_viewer` or `featured_match` key at all** (its keys are
`api_version, canonical, created_at, id, manifest, manifest_hash, name, schema_hash, size_bytes, version`),
which is why the SSR payload and the `replays/session` call are the evidence, exactly as the playbook's
"Answered (lighthouse run)" note says.

**Status: TRUE** — featured match present (`rumor.r3.e1`); iframe `src` is the **static** bundle route
with `ready: true` and a `<sha>` equal to the manifest hash; the `/client/replay` pod route does not
appear.

---

## 7. Certification declared the static bundle — **TRUE**

**Source: the committed `runs/2026-08-23-rumor/release-result.json`** (phase 40's downloaded artifact,
already in the repo). No re-download was needed and `/tmp` was not consulted.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-23-rumor/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

**Status: TRUE** — the string contains `Replay liveness: skipped (static replay bundle declared`,
verbatim, read from the committed copy.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

*(a) Dispatch.* At `2026-08-23T21:25:38Z` this verifier dispatched the one workflow it is permitted to
dispatch, against the exact iframe `src` from check 6:

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_46b04bae-028d-4f7a-8444-c18590d68521/sha256%3A83e14e8087bf4e1fc862471588e251cb443b2b19dada715d9d0f0c3c97c56c51/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F829157f1-6642-44f7-9543-566df8ac959c.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
sleep 12
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status,conclusion -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[0:3][]|[.databaseId,.createdAt,.status,.conclusion]|@tsv'
```
```
32667485621	2026-08-23T21:25:40Z	in_progress
32665552865	2026-08-23T20:48:38Z	completed	success
32665381318	2026-08-23T20:45:17Z	completed	success
```
The run was identified by `createdAt` sort, and `2026-08-23T21:25:40Z` is **after** the 21:25:38Z
dispatch — so run **`32667485621`** is this verifier's run, not a neighbour's. It was watched to
completion:

```bash
gh run watch 32667485621 -R Metta-AI/coworld-builder --exit-status
gh run view 32667485621 -R Metta-AI/coworld-builder --json status,conclusion,createdAt
```
```
✓ viewer-check in 31s (ID 97263090147)
  ✓ Install Playwright (pinned 1.55.0)  ✓ Load the viewer  ✓ Summary
  ✓ Upload the evidence  ✓ Fail if the viewer did not load
{"conclusion":"success","createdAt":"2026-08-23T21:25:40Z","status":"completed"}
```
Green — including the `Fail if the viewer did not load` gate.

```bash
gh run download 32667485621 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-23-rumor/viewer-check
ls -l runs/2026-08-23-rumor/viewer-check/
```
```
-rw-r--r-- 1 root root      0 Aug 23 21:26 smoke-stderr.txt
-rw-r--r-- 1 root root    345 Aug 23 21:26 smoke-stdout.txt
-rw-r--r-- 1 root root   1145 Aug 23 21:26 viewer-smoke.json
-rw-r--r-- 1 root root 360698 Aug 23 21:26 viewer-smoke.png
```
`smoke-stderr.txt` is zero bytes. The directory is on disk next to this file for the coordinator to
commit.

*(b) The readouts, verbatim.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-23-rumor/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":732,"clock":"ROUND 1","scorebug":"","feed_lines":0}
```

```bash
jq -c '.signals' runs/2026-08-23-rumor/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":null,"data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/2026-08-23-rumor/viewer-check/viewer-smoke.json
```
```
no failure
```

The three scrub clock readouts:

```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/2026-08-23-rumor/viewer-check/viewer-smoke.json
```

| scrub position | `#clock` readout |
|---|---|
| **0 %** | `ROUND 1` |
| **50 %** | `ROUND 1 / 5 · WAITING ON 10` |
| **100 %** | `TRUTH — FLOODED · HONEST 5/8 · 5 FLOODED · 5 DRY` |

**All three differ.** The viewer is not a screenshot: it advances, and the 100 % readout is the tally
state, which by the protocol cannot exist before the final frame.

Remaining fields of `viewer-smoke.json`, for completeness:
```json
{"status": "REPLAY", "loading_text": "LOADING REPLAY…", "bundle": null, "replay": null,
 "console_tail": ["[bridge] loading", "[bridge] ready"],
 "screenshot": "/home/runner/work/coworld-builder/coworld-builder/viewer-smoke.png"}
```

And `smoke-stdout.txt` as the workflow printed it:
```
{"loaded":true,"ms":732,"clock":"ROUND 1","scorebug":"","feed_lines":0}
scrub readouts: 0%="ROUND 1"  50%="ROUND 1 / 5 · WAITING ON 10"  100%="TRUTH — FLOODED · HONEST 5/8 · 5 FLOODED · 5 DRY"
artifacts: /home/runner/work/coworld-builder/coworld-builder/viewer-smoke.png /home/runner/work/coworld-builder/coworld-builder/viewer-smoke.json
```

**Item 8 gate: `loaded: true` ✔ (in 732 ms, via the `coworld-replay` bridge — `bridge_ready: true`,
`bridge: ["loading","ready"]`, `bridge_error: []`) AND the three clock readouts differ ✔ → TRUE.**

*(c) The replay JSON the viewer was asked to draw* — ordered excerpts, for reconciliation.

Early (`start`, `round 0`, all ten first-round says):
```
		start
0		round
0	0	say	My clue says FLOODED. I'm reporting this plainly as my own evidence - one of ten clues on the network. Passing…
0	1	say	Bolt here. My clue says FLOODED (A). A clue is right 2/3 of the time, so I'm anchoring on A with moderate conf…
0	2	say	Most of what I hear says DRY, so DRY.
0	3	say	My clue says FLOODED. No reports yet. That is 1 to 0 for FLOODED.
0	4	say	Most of what I hear says FLOODED, so FLOODED.
0	5	say	My clue says DRY, and so do 6 of the 8 reports I have. DRY.
0	6	say	Most of what I hear says FLOODED, so FLOODED.
0	7	say	Most of what I hear says FLOODED, so FLOODED.
0	8	say	My clue says DRY, and so do 2 of the 2 reports I have. DRY.
0	9	say	My clue says DRY. No reports yet. That is 1 to 0 for DRY.
```

Middle (round index 2 — `round`, `seat`, `claim`, `confidence`, `scripted`, text):
```
2	0	B	62	false	Round 3 ledger by distinct source: Gasket (me)=A, Bolt=A, Sprocket=B citing 6-of-8 reports. That's 2 vs 1 in reported clues, but S…
2	1	A	65	false	Bolt round 3. My clue: FLOODED. First-hand count: Bolt=A, Gasket=A, Tinker=B, Sprocket=B. Piston=A (hearsay, weight 1/3). Net: 2.5…
2	2	B	60	true	Most of what I hear says DRY, so DRY.
2	3	A	54	true	My clue says FLOODED. First reports: Sprocket DRY. That is 1 to 1 for FLOODED.
2	4	A	60	true	Most of what I hear says FLOODED, so FLOODED.
2	5	B	100	true	My clue says DRY, and so do 6 of the 8 reports I have. DRY.
2	6	A	60	true	Most of what I hear says FLOODED, so FLOODED.
2	7	A	60	true	Most of what I hear says FLOODED, so FLOODED.
2	8	B	90	true	My clue says DRY, and so do 2 of the 2 reports I have. DRY.
2	9	B	66	true	My clue says DRY. First reports: Sprocket DRY. That is 2 to 0 for DRY.
```

Late (the sealed ballot, then tally, then end):
```
vote	0	A
vote	1	A
vote	2	A
vote	3	A
vote	4	B
vote	5	B
vote	6	A
vote	7	B
vote	8	B
vote	9	B
tally
end
```

`.results` (repeated from check 4 for the reconciliation): `truth: "A"`, `optionA: "FLOODED"`,
`honestCorrect: 5`, `honestSeats: 8`, `accuracy: 0.625`, `verdict: "split"`, `topology: "hub"`,
`edgeCount: 14`, `roles[5] = Saboteur` (alias Sprocket), `roles[8] = Saboteur` (alias Tinker),
`names` (aliases) `["Gasket","Bolt","Widget","Ratchet","Flywheel","Sprocket","Piston","Gizmo","Tinker","Rivet"]`.

*(d) Spectator judgment.*

**It is legible, and it shows the game.** `viewer-smoke.png` (1280×800, downloaded from this run's
artifact — I am describing CI's picture, not an imagined one) is a fully drawn Rumor frame at the end
of the replay. Reading it top to bottom: the `RU`/`MOR` wordmark top-left; a top band whose clock reads
`TRUTH — FLOODED · HONEST 5/8 · 5 FLOODED · 5 DRY`; a `REPLAY` status chip and a `« LOG` toggle
top-right; then the **scorebug**, two rows carrying all ten seats with belief percentage, score and role
tag — `daveey 67% 0.6 COG`, `daveey-1 72% 0.6 COG`, `Widget 85% 0.6 COG`, `Ratchet 54% 0.6 COG`,
`Flywheel 85% -0.3 COG`, `Sprocket 71% -0.3 SABOTEUR`, `Piston 85% 0.6 COG`, `Gizmo 85% -0.3 COG`,
`Tinker 60% -0.6 SABOTEUR`, `Rivet 66% -0.3 COG`. Behind the endcard the social-graph stage is visible:
cog sprites joined by edges, with `FLOODED` / `DRY` claim labels and the proposition
`The mine's lower gallery is… FLOODED ? DRY ?` across the top of the board. The endcard itself reads
`THE TRUTH WAS FLOODED / HONEST COGS 5 / 8 / SABOTEURS: SPROCKET, TINKER` over a ten-row unmask table
with columns rank, name, ROLE, CLUE, VOTE, ✓/✗, SCORE. Below the board is a `BELIEF TIDE` momentum graph
— ten coloured belief traces converging and crossing across the episode — and under that the scrubber
with per-event colour ticks, a play button, and the position counter `69 / 69`.

**It reconciles exactly with the record.** Endcard vs `.results`: truth FLOODED = `truth:"A"` with
`optionA:"FLOODED"`; `HONEST COGS 5 / 8` = `honestCorrect:5` of `honestSeats:8`; saboteurs Sprocket and
Tinker = `roles` indices 5 and 8 against the alias list; the clock's `5 FLOODED · 5 DRY` = the ten
`votes` `["A","A","A","A","B","B","A","B","B","B"]`, which is also why `verdict` is `"split"`. Row by
row: `daveey` Honest/FLOODED/FLOODED/✓/0.6 = seat 0 `clues[0]="A"`, `votes[0]="A"`, `scores[0]=0.55`
(displayed to one decimal); `Widget` Honest/DRY/FLOODED/✓ = seat 2's `clues[2]="B"`, `votes[2]="A"` —
the seat that voted against its own clue because the network corrected it, which is the whole point of
the game and the viewer shows it; `Tinker` Saboteur/FLOODED/DRY/·/-0.6 = seat 8, `scores[8]=-0.55`. The
belief-tide traces match the belief series in the events (seat 0: 67 → … → 38 at round 5 → 67 at the
ballot — the visible dip and recovery as it doubted then re-suspected Sprocket). Nothing on screen is
invented and nothing in the record is missing from the screen.

**It looks like the starter's chrome.** The static shell served at the check-6 URL has *exactly* the
same element ids as `cogame-bullwhip/replay-viewer/index.html`, id for id:

```bash
curl -sS ".../static/<cow>/<sha>/index.html" | grep -o 'id="[a-zA-Z0-9_-]*"' | sort -u
grep -o 'id="[a-zA-Z0-9_-]*"' /workspace/starters/cogame-bullwhip/replay-viewer/index.html | sort -u
```
```
both:  board-wrap clock endscreen feed feedtoggle grain layout lightpool loading play pos
       scorebug scrub stage statuschip table topband topright transport wordmark
```
and the screenshot renders that structure as the same product: the same transport strip with a
tick-marked scrubber and `n / n` counter, the same momentum graph beneath the board (here labelled
`BELIEF TIDE`), the same top-band clock + status chip + log toggle, and the same centred endcard with a
per-seat results table. This is the paintbot/raid/hive family chrome re-skinned for Rumor, **not** the
cogame-gridlock failure mode of a rewrite that merely reuses the ids.

**Two legibility observations for the coordinator** (findings, not failures):
1. `scorebug: ""` and `feed_lines: 0` in the JSON are readouts taken at the **load instant** (`ms: 732`,
   `clock: "ROUND 1"`), before the first round resolves. `#scorebug` is an empty `<div>` in the shell
   that the renderer fills, and the screenshot — taken after the scrub sequence — shows it fully
   populated with all ten seats. `#feed` is the log panel, collapsed by default
   (`RumorRenderer.bindFeedToggle(…, true)`; the screenshot's button reads `« LOG`), so 0 lines at load
   is the shell's designed state, identical to the starter's. Neither is a defect; both are simply
   invisible to a load-instant DOM readout.
2. The scrubber **is** present (`#scrub` found, three readouts taken), so no "(no #scrub in this shell)"
   caveat applies here.

**Status: TRUE** — `loaded: true`, `bridge_ready: true`, no failure, three differing clock readouts, and
a rendered frame that is legible, complete, matched to the replay record, and wearing the starter's
chrome.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** (rounds 2, 3) |
| 2 | Both champions ranked, fillers absent | **TRUE** (daveey, daveey-1; `rounds_played` 2 each) |
| 3 | Latest round's episode request completed with replay + right seats | **TRUE** (`ereq_07ed5434…`) |
| 4 | Replay bytes valid, protocol matches, shows the game | **TRUE** (`rumor.replay.v1`, `complete`, 0 fallbacks) |
| 5 | Hosted game log clean | **TRUE** (`CLEAN`, decoded, 4 containers) |
| 6 | Public page uses the static replay path | **TRUE** (`…/replays/static/…/index.html?replay=…`, `ready:true`) |
| 7 | Certification declared the static bundle | **TRUE** (committed `release-result.json`) |
| 8 | Viewer executed and judged | **TRUE** (`loaded:true`, 3 differing clocks, run `32667485621`) |

**Verdict: all-true. 0 items false. 0 items NOT FETCHED.**
