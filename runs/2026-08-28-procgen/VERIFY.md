# VERIFY — procgen   (2026-08-28T22:45Z)

Verdict: **all-true** (8 / 8)

Coworld `procgen` **0.1.2**, `cow_84cce351-0c2e-42d7-820b-38cb85cd296e`, manifest
`sha256:c263c8bdc6b6b08e99d86e83561ea820fb03e59caf3eb064678de82cb90dd95a`, canonical `true`,
released by run `33215548447` at sha `3c143bcd`.
League `league_2b1f9007-0749-4e3c-a669-a630283894f1`, division `div_6efcf3a6-7551-4401-94a0-85853a797f16`.

Every response body below was fetched **in this pass, between 22:36Z and 22:45Z**, except the two
documented exceptions: check 7 reads the committed `runs/2026-08-28-procgen/release-result.json`
(the 0.1.2 release artifact), and check 8 reads the artifact of `viewer-check.yml` run
**33217648127**, which this pass dispatched at 22:39:38Z.

Common preamble for every `curl` below (header **names** shown; the token value is never printed):

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_2b1f9007-0749-4e3c-a669-a630283894f1
D=div_6efcf3a6-7551-4401-94a0-85853a797f16
COW=cow_84cce351-0c2e-42d7-820b-38cb85cd296e
```

## History (why this document was rewritten)

This is the **third** verification pass on this run. It supersedes the 21:10Z VERIFY.md, which
carried check 5 **FALSE**. Nothing below is copied from it — every check was re-fetched.

| When | Coworld | What happened |
|---|---|---|
| 20:19–21:34Z | **0.1.0** (`cow_4d7261f4`) | Rounds 1–6 ran. Rounds completed and scored, but the hosted logs carried `falling back (parse_error)`: the LLM per-turn deadlines (`attempt1Ms`/`retryMs`/`turnBudgetMs`) were tighter than the hosted Bedrock p90, so turns timed out and were mislabelled `parse_error`. 21:10Z VERIFY.md → check 5 FALSE. |
| 21:5xZ | **0.1.1** (`ee29e5e2`, release run `33212822202`, `cow_a82788ed`) | Widened `attempt1Ms`/`retryMs`/`turnBudgetMs` to 10000/5000/16000 and fixed the cause label (`timeout`, not `parse_error`). Round 7 came back half-clean; residual symptom `cut off at max_tokens` — the model spent its output budget on preamble before the JSON. |
| 22:15Z | **0.1.2** (`3c143bcd`, release run `33215548447`, `cow_84cce351`) | Added an assistant **prefill `{`** so the reply starts inside the JSON object. |
| 22:28–22:32Z | 0.1.2 | **Round 10** ran all three episodes on `cow_84cce351` and all three were clean. |

The evidence below is drawn from round 10 (the latest completed round), whose three episodes all
carry `coworld_id: cow_84cce351-…` — i.e. all three are 0.1.2 episodes, no version mixing.

---

## 1. ≥2 completed rounds after the fillers were set

Fillers were registered **before round 1** — `log.md:38`:

```
2026-08-28T20:13:43Z 50 filler-policies 200: pathfinder ff22a97d + scavenger d12e5c64 (neither champion) — set BEFORE trigger
```

Fetched fresh at 22:41:08Z, the filler registration still stands:

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}" | jq .
```
```json
{
  "filler_policy_versions": [
    {"policy_version_id": "ff22a97d-757c-4444-b6fe-3c02a7030411", "policy_id": "12ef398d-4366-4492-847c-8e05f8aef680",
     "policy_name": "procgen-pathfinder", "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
     "player_name": "daveey", "display_name": null},
    {"policy_version_id": "d12e5c64-6bd6-4b0d-8844-598cb1517faa", "policy_id": "ddba07f4-5def-4c59-8945-551448ac5d72",
     "policy_name": "procgen-scavenger", "version": 1, "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
     "player_name": "daveey", "display_name": null}
  ]
}
```

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=50" "${AUTH[@]}" > /tmp/rounds2.json    # 2026-08-28T22:41:08Z
jq -r 'if type=="array" then . else .entries end | group_by(.status)|map({status:.[0].status,n:length})' /tmp/rounds2.json
jq -c 'if type=="array" then . else .entries end | map({round_number,status,error,completed_at}) | sort_by(.round_number) | .[]' /tmp/rounds2.json
```
```json
[ { "status": "completed", "n": 10 } ]
```
```json
{"round_number":1,"status":"completed","error":null,"completed_at":"2026-08-28T20:19:57.817705Z"}
{"round_number":2,"status":"completed","error":null,"completed_at":"2026-08-28T20:34:19.474730Z"}
{"round_number":3,"status":"completed","error":null,"completed_at":"2026-08-28T20:50:02.085815Z"}
{"round_number":4,"status":"completed","error":null,"completed_at":"2026-08-28T21:04:53.821382Z"}
{"round_number":5,"status":"completed","error":null,"completed_at":"2026-08-28T21:19:31.537882Z"}
{"round_number":6,"status":"completed","error":null,"completed_at":"2026-08-28T21:34:42.608907Z"}
{"round_number":7,"status":"completed","error":null,"completed_at":"2026-08-28T21:51:07.509027Z"}
{"round_number":8,"status":"completed","error":null,"completed_at":"2026-08-28T22:03:58.539147Z"}
{"round_number":9,"status":"completed","error":null,"completed_at":"2026-08-28T22:19:35.763596Z"}
{"round_number":10,"status":"completed","error":null,"completed_at":"2026-08-28T22:32:23.713553Z"}
```

Round 10 in full, with the policy versions actually seated:

```bash
jq -r 'if type=="array" then . else .entries end | .[]|select(.round_number==10)
       |{id,round_number,status,error,created_at,completed_at,
         entrants:[.round_config.entrant_attributions[]|{subject_id,policy_version_id}]}' /tmp/rounds2.json
```
```json
{
  "id": "round_3092b440-f05f-45f6-9039-f06cd81a4ec0",
  "round_number": 10,
  "status": "completed",
  "error": null,
  "created_at": "2026-08-28T22:28:06.881667Z",
  "completed_at": "2026-08-28T22:32:23.713553Z",
  "entrants": [
    {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "policy_version_id": "6f123ede-f4e4-4467-ac19-bd636b1cfbb7"},
    {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "policy_version_id": "be25edba-71f3-4841-9a58-8dd644b57384"},
    {"subject_id": "ply_ded11f40-3e30-4921-b019-f7f6bc3e9c83", "policy_version_id": "d7b2f865-5f77-4a08-b9f3-23ba3e1ac40e"}
  ]
}
```

**Status: TRUE** — **10** rounds `completed`, **0** `failed`, **0** `discarded`, every `error`
`null`. All ten completed at or after 20:19:57Z, i.e. after the fillers were set at 20:13:43Z. The
requirement is ≥2; there are ten. Round 10 seats champion #1 (`ply_44ae9048` = daveey) and champion
#2 (`ply_bac48eb1` = daveey-1) plus a third external player, and neither filler version id
(`ff22a97d…`, `d12e5c64…`) appears among the entrants — the ladder no longer needs a filler because
three real players are enrolled.

## 2. Both champions ranked; fillers absent

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq .     # 2026-08-28T22:37Z
```
```json
[
  {
    "rank": 1,
    "player_id": "ply_ded11f40-3e30-4921-b019-f7f6bc3e9c83",
    "player_name": "richard",
    "score": 1032.0,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 1,
    "episode_wins": 2.0,
    "episodes_played": null,
    "win_rate": 1.0,
    "policy_label": "co-gas-procgen-safe-route-richard:v1",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 1009.4328993512081,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 10,
    "episode_wins": 6.0,
    "episodes_played": null,
    "win_rate": 0.5454545454545454,
    "policy_label": "procgen-cartographer:v1",
    "recent_rounds": null
  },
  {
    "rank": 3,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 958.5671006487919,
    "score_label": "MMR",
    "score_value_type": "integer",
    "rounds_played": 10,
    "episode_wins": 4.0,
    "episodes_played": null,
    "win_rate": 0.36363636363636365,
    "policy_label": "procgen-scrambler:v1",
    "recent_rounds": null
  }
]
```

**Status: TRUE** — `daveey` (`procgen-cartographer:v1`, rank 2, `rounds_played` 10, MMR 1009.4) and
`daveey-1` (`procgen-scrambler:v1`, rank 3, `rounds_played` 10, MMR 958.6) are both ranked with
`rounds_played ≥ 1`. Neither filler (`procgen-pathfinder`, `procgen-scavenger`) appears on the
board and no row is labelled `Baseline (N)` — fillers **absent**, which the check allows.

*Observation for the coordinator (not a check failure):* a third, external player has joined the
league since the last pass — `richard` with `co-gas-procgen-safe-route-richard:v1`, rank 1 on one
round played. That is somebody else picking the coworld up, and it is why the ladder now seats
three real entrants instead of a champion pair plus fillers.

## 3. The latest completed round's episode requests completed with replays

`GET /episode-requests?round_id=…` is dead (405, `allow: POST` — `playbooks/observatory-api.md` §9);
the nested route is used.

```bash
R=round_3092b440-f05f-45f6-9039-f06cd81a4ec0        # round 10, the latest completed
curl -sS "$BASE/rounds/$R/episode-requests" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end | .[] | [.id,.status,.coworld_id,.replay_url]|@tsv'
```
```
ereq_88ef2799-8681-40d6-9e42-eb825d807fec	completed	cow_84cce351-0c2e-42d7-820b-38cb85cd296e	https://softmax-public.s3.amazonaws.com/replays/f8910aae-22c1-473b-8235-9fecbac702a2.replay
ereq_a50e07c8-aacd-451b-984d-6e9c7fce7fa2	completed	cow_84cce351-0c2e-42d7-820b-38cb85cd296e	https://softmax-public.s3.amazonaws.com/replays/2f6bc2f6-1309-49ac-9d67-6a50a2fdc2b1.replay
ereq_0aa7017c-ba7b-4ed9-a7a9-1dc2eee8f5c1	completed	cow_84cce351-0c2e-42d7-820b-38cb85cd296e	https://softmax-public.s3.amazonaws.com/replays/33f538e6-fd4e-4fd2-b256-70d7976f552d.replay
```

All three details (`procgen` is a **single-seat gauntlet** — one policy per episode, one episode per
entrant per round; the round's champion coverage is therefore across the three requests, not inside
one of them):

```bash
for E in ereq_88ef2799-… ereq_a50e07c8-… ereq_0aa7017c-…; do
  curl -sS "$BASE/episode-requests/$E" "${AUTH[@]}" | jq '{status, replay_url, coworld_id, participants, participant_scores}'
done
```
```json
=== ereq_0aa7017c-ba7b-4ed9-a7a9-1dc2eee8f5c1
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/33f538e6-fd4e-4fd2-b256-70d7976f552d.replay",
  "coworld_id": "cow_84cce351-0c2e-42d7-820b-38cb85cd296e",
  "participants": [
    {"position": 0, "kind": "policy", "policy_version_id": "6f123ede-f4e4-4467-ac19-bd636b1cfbb7",
     "policy_id": "74f3fc66-4d82-47f5-98ad-6be0ca4b46b3", "policy_name": "procgen-cartographer", "version": 1,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey",
     "is_filler": false, "is_seed": false}
  ],
  "participant_scores": [ {"position": 0, "score": 0.284} ]
}

=== ereq_a50e07c8-aacd-451b-984d-6e9c7fce7fa2
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/2f6bc2f6-1309-49ac-9d67-6a50a2fdc2b1.replay",
  "coworld_id": "cow_84cce351-0c2e-42d7-820b-38cb85cd296e",
  "participants": [
    {"position": 0, "kind": "policy", "policy_version_id": "be25edba-71f3-4841-9a58-8dd644b57384",
     "policy_id": "e20f8ed8-5c38-4d56-b02a-fd2076468e3a", "policy_name": "procgen-scrambler", "version": 1,
     "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1",
     "is_filler": false, "is_seed": false}
  ],
  "participant_scores": [ {"position": 0, "score": 0.271} ]
}

=== ereq_88ef2799-8681-40d6-9e42-eb825d807fec
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/f8910aae-22c1-473b-8235-9fecbac702a2.replay",
  "coworld_id": "cow_84cce351-0c2e-42d7-820b-38cb85cd296e",
  "participants": [
    {"position": 0, "kind": "policy", "policy_version_id": "d7b2f865-5f77-4a08-b9f3-23ba3e1ac40e",
     "policy_id": "e0b22057-cbb6-4a64-88f4-a5e3ae4e89b7", "policy_name": "co-gas-procgen-safe-route-richard", "version": 1,
     "player_id": "ply_ded11f40-3e30-4921-b019-f7f6bc3e9c83", "player_name": "richard",
     "is_filler": false, "is_seed": false}
  ],
  "participant_scores": [ {"position": 0, "score": 0.306} ]
}
```

**Status: TRUE** — all three episode requests of round 10 are `completed`, each with a non-null
`replay_url`, each on `coworld_id: cow_84cce351-…` (0.1.2 — **no version mixing in this round**), and
the round's participants name `daveey` (`procgen-cartographer:v1`, 0.284) and `daveey-1`
(`procgen-scrambler:v1`, 0.271) — plus `richard` (0.306). `is_filler: false` on all three; no
`Baseline (N)` seats exist because the league has three real entrants.

## 4. Replay bytes are valid and show the game

`procgen`'s replay is the starter's **binary `COWLDPGN`** container, not raw JSON — `design.md`
§"Replay bytes (self-sufficient)" (lines 1053–1082) declares this and specifies the phase-60
substitute for the strict-JSON step: `tools/replay_summary.py` (Python 3 stdlib only) emits **one
strict-UTF-8 JSON object** from the container, and `jq -e .` parses *that*. That substitute is used
here, verbatim, from the repo at the released sha:

```bash
cd /workspace/cogame-procgen && git log --oneline -1        # 3c143bc prefill the assistant turn with `{`
for n in 33f538e6-… 2f6bc2f6-… f8910aae-…; do
  curl -sSL "https://softmax-public.s3.amazonaws.com/replays/$n.replay" -o /tmp/$n.replay
  python3 tools/replay_summary.py /tmp/$n.replay > /tmp/$n.json     # exit 0
  jq -e . /tmp/$n.json >/dev/null && echo "strict UTF-8 JSON: ok"
done
```
```
== 33f538e6-fd4e-4fd2-b256-70d7976f552d   136244 bytes   exit=0   strict UTF-8 JSON: ok
== 2f6bc2f6-1309-49ac-9d67-6a50a2fdc2b1   147555 bytes   exit=0   strict UTF-8 JSON: ok
== f8910aae-22c1-473b-8235-9fecbac702a2   148831 bytes   exit=0   strict UTF-8 JSON: ok
```

Container header (first bytes of the raw `.replay`, `od -c`) — the magic and protocol the manifest
declares:

```
0000000   C   O   W   L   D   P   G   N 001  \0  \0  \0  \a  \0  \0  \0
0000020   p   r   o   c   g   e   n 001  \0  \0  \0   1 357 002  \0  \0
0000040   {   "   p   r   o   t   o   c   o   l   "   :   "   p   r   o
0000060   c   g   e   n   /   v   1   "   ,   "   s   e   e   d   "   : …
```

```bash
jq -r '[.protocol,.gameVersion,.results.reason,.results.endRule,(.results.scores|tostring),(.results.levelReturns|tostring)]|@tsv' $n.json
jq -r '"levelSeeds=\(.levelSeeds|length) levelCount=\(.results.levelCount) levelSplit=\(.levelSplit|tostring) unseenMilli=\(.results.unseenMilli) names=\(.names|tostring)"' $n.json
jq -r '"llm_actions=\([.actions[]?|select(.source=="llm")]|length) total_actions=\(.actions|length) fallbacks=\(.fallbacks) interrupts=\(.interrupts) says=\(.says|length) frameCount=\(.frameCount)"' $n.json
```
```
=== 33f538e6…  (daveey / procgen-cartographer:v1)
procgen/v1	1	complete	gauntlet_complete	[0.284]	[705,212,175,15,11,363,219,203]
levelSeeds=8 levelCount=8 levelSplit=["unseen","seen","seen","seen","unseen","seen","unseen","unseen"] unseenMilli=284 names=["daveey"]
llm_actions=72 total_actions=72 fallbacks=0 interrupts=14 says=72 frameCount=346

=== 2f6bc2f6…  (daveey-1 / procgen-scrambler:v1)
procgen/v1	1	complete	gauntlet_complete	[0.271]	[298,7,187,538,241,252,193,881]
levelSeeds=8 levelCount=8 levelSplit=["unseen","unseen","seen","unseen","unseen","seen","seen","seen"] unseenMilli=271 names=["daveey-1"]
llm_actions=78 total_actions=78 fallbacks=0 interrupts=8 says=78 frameCount=341

=== f8910aae…  (richard — the featured replay)
procgen/v1	1	complete	gauntlet_complete	[0.306]	[427,492,402,350,45,263,1000,0]
levelSeeds=8 levelCount=8 levelSplit=["unseen","seen","unseen","unseen","unseen","seen","seen","seen"] unseenMilli=306 names=["richard"]
llm_actions=79 total_actions=79 fallbacks=0 interrupts=9 says=79 frameCount=295
```

**Status: TRUE** for all three. `protocol == "procgen/v1"` matches the manifest; `results.reason ==
"complete"` (not even the declared-acceptable `deadline` of `design.md:506-512` was needed);
`levelSeeds|length == levelCount == 8`; every `levelSplit` entry is `seen` or `unseen` with both
present; `unseenMilli` non-zero on all three. Decisions are non-scripted and non-trivial: **72 / 78 /
79** turns, **every one** `source == "llm"`, `fallbacks = 0` on all three — the fallback count is not
a minority, it is **zero**, which is the 0.1.2 fix landing. Every turn carries a non-empty `say`.

## 5. Hosted game logs are clean

All three round-10 episodes were grepped, not just one. The logs body is python `b'…'` byte-string
reprs under `===== container: … =====` headers, so it is **decoded** (`ast.literal_eval` per repr)
before grepping — a line-based grep on the raw body undercounts (escrow, 2026-08-23).

```bash
for E in ereq_0aa7017c-… ereq_a50e07c8-… ereq_88ef2799-…; do
  curl -sS "$BASE/episode-requests/$E/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs-$E.raw
  python3 /tmp/declog.py /tmp/logs-$E.raw > /tmp/logs-$E.txt
  grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs-$E.txt || echo CLEAN
done
```
```
=== ereq_0aa7017c-ba7b-4ed9-a7a9-1dc2eee8f5c1  (daveey)    raw=148640 B  decoded=148328 B  303 lines
CLEAN (0 matches)
=== ereq_a50e07c8-aacd-451b-984d-6e9c7fce7fa2  (daveey-1)  raw=160913 B  decoded=160577 B  327 lines
CLEAN (0 matches)
=== ereq_88ef2799-8681-40d6-9e42-eb825d807fec  (richard)   raw=162972 B  decoded=162632 B  331 lines
CLEAN (0 matches)
```

A widened, case-insensitive grep on the **raw** body also returns nothing, so this is not a decoding
artefact:

```bash
grep -ciE 'falling back|unavailable|max_tokens|reject' /tmp/logs-ereq_0aa7017c-….raw
```
```
0
```

The `coworld_id` of each of these three episodes is `cow_84cce351-0c2e-42d7-820b-38cb85cd296e`
(pasted in check 3), so the gate verdict comes from **0.1.2 episodes only**. The decoded `game`
container tails, showing what actually ran:

```
=== ereq_0aa7017c  (daveey)
===== container: game =====
procgen: seed not pinned; randomized
procgen config: host=0.0.0.0 port=8080 seed=1543432816 levelCount=8 turnsPerLevel=10 framesPerTurn=6 difficulty=standard num_agents=1 turnSpacingMs=2500 wallClockBudgetSeconds=660
procgen listening on 0.0.0.0:8080
procgen llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
procgen: episode complete (gauntlet_complete) after 338 frames, 72 turns; unseen 284 seen 191

=== ereq_a50e07c8  (daveey-1)
procgen: episode complete (gauntlet_complete) after 333 frames, 78 turns; unseen 271 seen 378

=== ereq_88ef2799  (richard)
procgen: episode complete (gauntlet_complete) after 287 frames, 79 turns; unseen 306 seen 438
```

And the Bedrock sidecar call ledger for the daveey episode — 72 calls, 72 completions, for 72 turns,
i.e. **no retry ever fired**:

```bash
grep -o 'bedrock_[a-z_]*' /tmp/logs-ereq_0aa7017c-….txt | sort | uniq -c
```
```
    217 bedrock_sidecar
     72 bedrock_sidecar_call
     72 bedrock_sidecar_complete
      1 bedrock_sidecar_started
     72 bedrock_sidecar_usage
```

**Status: TRUE** — zero `falling back`, zero `LLM provider is unavailable`, zero `cut off at
max_tokens`, zero `rejected` across all three 0.1.2 episodes of round 10. This is the check that was
FALSE at 21:10Z on 0.1.0; the 0.1.1 deadline widening plus the 0.1.2 assistant prefill closed it.
No documented exception is being invoked — the logs are clean outright.

*(Note on a near-miss token: the results document carries `ordersRejected: 3` on the richard
episode. That is not a log line and not this grep's subject — `design.md:612,994` defines it as the
count of turns whose `moves` string needed symbol-level **repair**, which the game does silently and
by design ("repaired, never rejected"). The hosted log contains no `rejected` line.)*

## 6. The public page uses the static replay path

**Source used: the SSR payload of `https://softmax.com/procgen`, plus the session endpoint the
page's own JS calls.** The raw-HTML iframe grep found nothing, which is the documented
client-rendered case, not a false negative:

```bash
curl -sS "https://softmax.com/procgen" -o /tmp/page.html -w "http=%{http_code} bytes=%{size_download}\n"
grep -o '<iframe[^>]*src="[^"]*"' /tmp/page.html || echo "(no iframe in raw HTML)"
```
```
http=200 bytes=762126
(no iframe in raw HTML)
```

The `/coworlds` fallback in the playbook is **also** empty platform-wide (`replay_viewer` and
`featured_match` are `null` for every coworld), so it is not evidence either — but it does confirm
the identity of the canonical coworld:

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end | .[]|select(.name=="procgen")
          |{id,name,version,canonical,replay_viewer,featured_match,manifest_hash}'
```
```json
{"id":"cow_84cce351-0c2e-42d7-820b-38cb85cd296e","name":"procgen","version":"0.1.2","canonical":true,
 "replay_viewer":null,"featured_match":null,
 "manifest_hash":"sha256:c263c8bdc6b6b08e99d86e83561ea820fb03e59caf3eb064678de82cb90dd95a"}
{"id":"cow_a82788ed-76d8-4eb0-b709-1ff4af35ed6c","name":"procgen","version":"0.1.1","canonical":false, …}
{"id":"cow_4d7261f4-1766-4ca3-84df-0e61eedd1b4d","name":"procgen","version":"0.1.0","canonical":false, …}
```

The featured match is server-rendered into the page's SSR payload. `state.playlist` is `[]`; the
featured pool is at **`state.pool.replays[0]`** (the same location the 21:07Z pass found it).
Unescaped and decoded out of the RSC payload:

```bash
python3 -  # unescape the RSC payload, raw_decode the object after "pool", print each entry
```
```
pool keys: ['replays', 'live']
n replays: 3
idx kind    round  ereq                                        version player    replay_url                                                                        episodeNumber
0   replay  10     ereq_88ef2799-8681-40d6-9e42-eb825d807fec   0.1.2   richard   …/replays/f8910aae-22c1-473b-8235-9fecbac702a2.replay                             3
1   replay  (ref)  ereq_a50e07c8-aacd-451b-984d-6e9c7fce7fa2   0.1.2   daveey-1  …/replays/2f6bc2f6-1309-49ac-9d67-6a50a2fdc2b1.replay                             2
2   replay  (ref)  ereq_0aa7017c-ba7b-4ed9-a7a9-1dc2eee8f5c1   0.1.2   daveey    …/replays/33f538e6-fd4e-4fd2-b256-70d7976f552d.replay                             1
```
```
…\"state\":{\"leagueId\":\"league_2b1f9007-0749-4e3c-a669-a630283894f1\",\"playlist\":[],\"pool\":{\"replays\":[{\"kind\":\"replay\",\"round\":{\"id\":\"round_3092b440-f05f-45f6-9039-f06cd81a4ec0\",\"round_number\":10,\"commissioner_key\":\"platform\",…
…\"coworld_id\":\"cow_84cce351-0c2e-42d7-820b-38cb85cd296e\",\"coworld_name\":\"procgen\",\"coworld_version\":\"0.1.2\",\"variant_name\":\"Procgen Gauntlet (8 levels, half of them nobody has ever seen)\",\"job_index\":2,\"status\":\"completed\",…
```

The iframe `src` is what the page's JS gets back from the session endpoint:

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_84cce351-0c2e-42d7-820b-38cb85cd296e",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/f8910aae-22c1-473b-8235-9fecbac702a2.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_84cce351-0c2e-42d7-820b-38cb85cd296e/sha256%3Ac263c8bdc6b6b08e99d86e83561ea820fb03e59caf3eb064678de82cb90dd95a/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Ff8910aae-22c1-473b-8235-9fecbac702a2.replay",
  "ready": true
}
```

**Status: TRUE** — a featured match is present (`state.pool.replays[0]`, round 10, episode 3), and
the viewer URL is the **static** route: `/v2/coworlds/replays/static/<cow_id>/<sha>/index.html`,
ending in `index.html`, with `ready: true`. It uses the `?v=2#replay=<url-encoded s3 url>` fragment
shape the playbook records as of 2026-08-28; that is the static route, not a variant of failure.
There is **no `/client/replay`** anywhere in it. `<cow_id>` is `cow_84cce351-…` and `<sha>` is
`sha256%3Ac263c8bd…` — the **0.1.2** manifest hash, matching STATE exactly. The featured episode is
itself a 0.1.2 episode from round 10, so nothing here is an older-version leftover.

## 7. Certification declared the static bundle

**Source: the committed `runs/2026-08-28-procgen/release-result.json`** — the artifact phase 40
downloaded from release run `33215548447` (the 0.1.2 release) and committed. It was already present;
no re-download from `gh run download` was needed.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-28-procgen/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

The surrounding record, confirming this file is the 0.1.2 artifact and not a stale 0.1.0/0.1.1 one:

```bash
jq -r 'del(.certify.output_tail)' runs/2026-08-28-procgen/release-result.json
```
```json
{
  "version": "0.1.2",
  "ok": true,
  "cow_id": "cow_84cce351-0c2e-42d7-820b-38cb85cd296e",
  "manifest_sha": "sha256:c263c8bdc6b6b08e99d86e83561ea820fb03e59caf3eb064678de82cb90dd95a",
  "canonical": true,
  "hosted_smoke": "passed",
  "hosted_certification": "certifying",
  "certify": {"ok": true,
    "replay_liveness": "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"},
  "policies": [
    {"name":"procgen-cartographer","version":"v3","policy_version_id":null,"player_id":null},
    {"name":"procgen-scrambler","version":"v3","policy_version_id":null,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
    {"name":"procgen-pathfinder","version":"v3","policy_version_id":null,"player_id":null},
    {"name":"procgen-scavenger","version":"v3","policy_version_id":null,"player_id":null}
  ],
  "secret_put": true, "errors": [], "step_failed": null
}
```

And the certification transcript in `certify.output_tail` — all ten steps passed:

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
…
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

**Status: TRUE** — the string `Replay liveness: skipped (static replay bundle declared` is present
verbatim, from the committed 0.1.2 release artifact.

*Observation for the coordinator (not a check failure):* the 0.1.2 release uploaded the policies as
**`:v3`**, because each re-release re-uploads them, while the league still seats **`:v1`** of each
(check 1's `entrant_attributions`, check 2's `policy_label`). That is correct for this run — the
0.1.1/0.1.2 fixes are engine-side (deadlines, cause label, assistant prefill), all inside the
coworld image, and the prompt text is unchanged — so the seated `:v1` policies get the fixes anyway.
Worth knowing, not worth re-seating.

## 8. Spectator judgment — the viewer, EXECUTED

*(a) Dispatch.* The URL is the exact `viewer_url` from check 6.

```bash
SRC=$(jq -r .viewer_url /tmp/session.json)
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
# dispatched 2026-08-28T22:39:38Z
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status,conclusion -L 10 \
 | jq -r 'sort_by(.createdAt)|reverse|.[]|[.databaseId,.createdAt,.status,(.conclusion//"-")]|@tsv'
```
```
33217648127	2026-08-28T22:39:40Z	in_progress
33217607488	2026-08-28T22:38:57Z	completed	success     <- NOT mine: created 41 s before my dispatch
33216261052	2026-08-28T22:18:25Z	completed	success
33211231543	2026-08-28T21:08:08Z	completed	success     <- the 21:08Z pass's run; superseded
…
```

Run **33217648127**, created 22:39:40Z — the first run created *after* my 22:39:38Z dispatch. (Note
the run 43 seconds earlier: taking "the latest run" blind would have grabbed somebody else's.)

```bash
gh run watch 33217648127 -R Metta-AI/coworld-builder --exit-status   # exit 0
```
```
✓ main viewer-check · 33217648127
✓ viewer-check in 34s (ID 99004784045)
  ✓ Install Playwright (pinned 1.55.0)
  ✓ Load the viewer
  ✓ Summary
  ✓ Upload the evidence
  ✓ Fail if the viewer did not load
```
```bash
rm -f runs/2026-08-28-procgen/viewer-check/*        # overwrite the 21:08Z artifacts
gh run download 33217648127 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-28-procgen/viewer-check
```
```
viewer-smoke.json  1505 B
viewer-smoke.png   456120 B
smoke-stdout.txt    709 B
smoke-stderr.txt      0 B
```

*(b) The readouts.* Verbatim from `runs/2026-08-28-procgen/viewer-check/viewer-smoke.json`:

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-28-procgen/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":1938,"clock":"LEVEL 1/8 turn 0/10 · frame 0 BEFORE THE FIRST LEVEL","scorebug":"richard COG-alpha L1/8 · MINERUNSEEN LEVEL 0/4 GEMS LEVEL 1/8 turn 0/10 · frame 0 BEFORE THE FIRST LEVEL","feed_lines":2}
```
```bash
jq -c '.signals' runs/2026-08-28-procgen/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
```
```bash
jq -r '.failure // "no failure"' runs/2026-08-28-procgen/viewer-check/viewer-smoke.json
```
```
no failure
```

Also in the artifact: `"status":"LIVE"`, `"loading_text":null`, `"console_tail":[]`, and
`canvas_text: {total:0, outside:0, ellipsized:0, never_inside:0}` — no text drawn outside the canvas,
nothing ellipsized. The URL the runner actually opened, recorded in the json, is byte-identical to
check 6's `viewer_url`:

```
https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_84cce351-0c2e-42d7-820b-38cb85cd296e/sha256%3Ac263c8bdc6b6b08e99d86e83561ea820fb03e59caf3eb064678de82cb90dd95a/index.html?v=2#replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Ff8910aae-22c1-473b-8235-9fecbac702a2.replay
```

**The three clock readouts** (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub | clock readout |
|---|---|
| **0 %** | `LEVEL 1/8 turn 0/10 · frame 0 BEFORE THE FIRST LEVEL` |
| **50 %** | `LEVEL 5/8 turn 0/10 · frame 42 MAZE · 15×9 · STANDARD · UNSEEN SEED 1762650379` |
| **100 %** | `LEVEL 8/8 turn 0/10 · frame 60 MAZE · 15×9 · STANDARD · SEEN SEED 1032` |

All three **differ**, in level (1 → 5 → 8), in frame (0 → 42 → 60), and in level identity
(pre-roll → unseen maze seed 1762650379 → seen maze seed 1032). The shell **does** expose `#scrub`;
no "(no #scrub…)" placeholder appears.

**Item 8 gate: `loaded: true` ✓ (in 1938 ms, `data-replay-loaded="true"`) AND the three clock
readouts differ ✓ → TRUE.**

*(c) The replay JSON the viewer was asked to draw* — the featured episode `f8910aae…` (richard),
ordered excerpts:

```bash
# early
  1	L1	llm 	RDRDRR  	exec=6 	Miner: dig right to gems
  2	L1	llm 	RRDRD   	exec=5 	Miner gem collect sequen
  3	L1	llm 	L       	exec=1 	miner: moving left towar
  4	L1	llm 	LUULD   	exec=5 	Miner: dig left to [2,3]
  5	L1	llm 	LU      	exec=2 	dig up to gem at [2,3]
  6	L1	llm 	LDDLLL  	exec=6 	Mining toward gem at [2,
  7	L1	llm 	RD      	exec=2 	Collect gem at [2,3], di
  8	L1	llm 	DUL     	exec=3 	Collect gem at [2,5], na
# middle
 40	L5	llm 	LLLUU   	exec=5 	Maze: collect gems, then
 41	L5	llm 	DRDRD   	exec=5 	maze routing to gem at [
 42	L5	llm 	LULDR   	exec=5 	Maze corridor to gem at
 43	L5	llm 	LULDDR  	exec=6 	maze: pursuing gem at [3
 44	L5	llm 	UUULLL  	exec=6 	maze routing to nearest
 45	L5	llm 	UUULLL  	exec=6 	Maze phase 1: routing to
 46	L5	llm 	DDDLLL  	exec=6 	maze: collect [3,3], the
 47	L5	llm 	UUULLL  	exec=6 	Maze: pursue [3,3] gem v
# late
 72	L8	llm 	RRRRRR  	exec=6 	maze, collect all gems,
 73	L8	llm 	RRRRRR  	exec=6 	maze L8: routing east to
 74	L8	llm 	RRRRRR  	exec=6 	maze: commit row-1 towar
 75	L8	llm 	RRRRRR  	exec=6 	maze L8: sprint right on
 76	L8	llm 	RRRRRR  	exec=6 	maze sprint to first gem
 77	L8	llm 	RRRRRR  	exec=6 	maze L8: heading right t
 78	L8	llm 	RRRRRR  	exec=6 	maze collector run
 79	L8	llm 	RRRRRR  	exec=6 	maze final push
```
```bash
jq -r '.results' /tmp/f8910aae-….json
```
```json
{
 "names": ["richard"], "aliases": ["COG-alpha"], "scores": [0.306], "win": [false],
 "reason": "complete", "endRule": "gauntlet_complete", "variant": "gauntlet", "difficulty": "standard",
 "seed": 1164128183, "levelCount": 8,
 "levelKinds":       ["miner","chaser","climber","chaser","maze","climber","miner","maze"],
 "levelSplit":       ["unseen","seen","unseen","unseen","unseen","seen","seen","seen"],
 "levelSeeds":       [815635446, 2016, 739116910, 1024667189, 1762650379, 3015, 4026, 1032],
 "levelReturns":     [427, 492, 402, 350, 45, 263, 1000, 0],
 "levelOutcome":     ["timeup","timeup","timeup","died","timeup","timeup","cleared","timeup"],
 "levelDeathCause":  ["","","","caught","","","",""],
 "levelFrames":      [38, 20, 30, 17, 57, 23, 42, 60],
 "levelCollected":   [2, 4, 2, 2, 0, 1, 4, 0],
 "levelCollectTotal":[4, 8, 4, 8, 4, 4, 4, 4],
 "seenMilli": 438, "unseenMilli": 306, "gapMilli": 132, "seenCleared": 1, "unseenCleared": 0,
 "policyKinds": ["llm"], "llmTurns": 79, "fallbackTurns": 0, "ordersRejected": 3,
 "planInterrupts": 13, "genFallbacks": 0, "deadSeats": [false], "stopDetail": ""
}
```

### Spectator judgment

`viewer-smoke.png` (committed at `runs/2026-08-28-procgen/viewer-check/viewer-smoke.png`, 1280×800,
taken with the scrubber left at 100 %) shows a fully drawn, legible frame — not a loading spinner,
not an empty canvas. Reading it top to bottom: a **scorebug strip** across the top carrying an amber
seat dot, the player name **`richard`**, the alias **`COG-alpha`**, a level chip **`L8/8 · MAZE`**
with a blue **`SEEN`** badge, and a **`LEVEL 0/4 GEMS`** counter; centred beside it the **clock**,
`LEVEL 8/8 / turn 0/10 · frame 60`, over the level identity line `MAZE · 15×9 · STANDARD · SEEN SEED
1032`. Beneath that the playfield, dimmed behind the endcard, with the brick tiling, a floating gem
sprite or two, and the fading banner `LEVEL 5 OF 8 — MAZE — UNSEEN` from the scrub path. In the
middle sits the **endcard**: `SCORE 0.306 — mean over 4 unseen levels`, a boxed
`SEEN 0.438 · UNSEEN 0.306 · GAP +0.132`, the line `gauntlet · standard · 4 seen / 4 unseen · 0 of 4
unseen levels cleared`, the twin big numbers `0.306 UNSEEN MEAN` / `0.438 SEEN MEAN`, and an
eight-row table `LEVEL / KIND / SEED / SPLIT / OUTCOME / GEMS / RETURN` with the unseen rows tinted
amber. Bottom-right, three broadcast **feed lines** fading out: `COG-alpha: "Maze pursue [3,3] gem
v"`, `COG-alpha runs out of turns on MAZE — 0`, `GAUNTLET OVER — unseen mean 0.306`. Bottom, the
**transport strip**: restart, step-back, play, `+5s`, step-forward, loop, fast-forward, a `spoilers`
toggle, the frame counter `294 / 294`, speed buttons `1× 2× 3× 4× 8× 16×`, and a full-width
**scrubber with a momentum graph** labelled `SEEN vs UNSEEN`, its level boundaries ticked and its
seen/unseen bands drawn in white and red.

**Does it advance?** Yes, and provably: the three scrub readouts move the clock from level 1/frame 0
to level 5/frame 42 to level 8/frame 60, and the 50 % and 100 % readouts name two *different* maze
seeds. This is a replay in motion, not one rendered frame.

**Does it show the game, and can a spectator tell who is winning and why?** Yes, and the picture and
the record agree line for line. Every number on the endcard is in the replay's `results`:
`scores [0.306]`, `seenMilli 438`, `unseenMilli 306`, `gapMilli 132`, `unseenCleared 0` of 4; the
table's eight rows reproduce `levelKinds`, `levelSeeds`, `levelSplit`, `levelOutcome`,
`levelCollected/levelCollectTotal` and `levelReturns` exactly, including level 4 `chaser / died`
(cause `caught`) and level 7 `miner / cleared / 4/4 / 1000`. The 100 % clock's `frame 60` is
`levelFrames[7] = 60` and `SEEN SEED 1032` is `levelSeeds[7] = 1032`; the 50 % clock's
`UNSEEN SEED 1762650379` is `levelSeeds[4]`. The feed line `"Maze pursue [3,3] gem v"` is turn 47's
`say` verbatim, and the scorebug's `0/4 GEMS` is `levelCollected[7] = 0` of `levelCollectTotal[7] =
4`. So the answer to "who is winning and why" is on screen without inference: the run scored 0.306
on levels it had never seen against 0.438 on levels it had, a +0.132 generalization gap, and the
table says exactly which level cost it what — the unseen maze at seed 1762650379 returned 45 with
zero gems, the seen miner at seed 4026 returned a clean 1000.

**Is it the starter's chrome?** Yes. The transport strip, the scrubber with a momentum graph, the
scorebug and the endcard are the coworld-ctf/paintbot/raid family furniture, retargeted rather than
rewritten: the momentum graph is relabelled `SEEN vs UNSEEN`, the scorebug carries a level chip and
a gem counter instead of a flag count, and the endcard is a per-level gauntlet table instead of a
capture summary. This is not the cogame-gridlock failure mode — it is recognisably the same product
with this game's nouns in it.

**Legibility observations for the coordinator** (none of them a check failure): the scorebug string
concatenates without separators when read out of the DOM (`L1/8 · MINERUNSEEN LEVEL 0/4 GEMS`) —
visually the `MINER` chip and the `UNSEEN` badge are adjacent elements and read fine in the picture,
but the missing space is worth a glance. And `feed_lines: 2` at frame 0 versus three visible feed
lines at frame 294 is just the feed filling as the episode runs.

**Status: TRUE** — `loaded: true` at 1938 ms, `failure: null`, three differing clock readouts, and a
rendered picture that both shows the game and reconciles exactly with the replay record.

---

## Summary

| # | Check | Verdict | Evidence in one line |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** | 10/10 rounds `completed`, 0 failed, all after fillers set 20:13:43Z; round 10 completed 22:32:23Z |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** | `daveey` rank 2 `procgen-cartographer:v1` 10 rounds; `daveey-1` rank 3 `procgen-scrambler:v1` 10 rounds; no filler row |
| 3 | Latest round's episode requests completed with replays | **TRUE** | Round 10's three ereqs all `completed`, non-null `replay_url`, all `coworld_id cow_84cce351` (0.1.2) |
| 4 | Replay bytes valid and show the game | **TRUE** | `COWLDPGN` → strict JSON ok; `protocol procgen/v1`, `reason complete`, 72/78/79 turns all `source llm`, `fallbacks 0` |
| 5 | Hosted game log clean | **TRUE** | 0 matches for `falling back\|LLM provider is unavailable\|cut off at max_tokens\|rejected` in all three 0.1.2 episode logs |
| 6 | Public page uses the static replay path | **TRUE** | SSR `state.pool.replays[0]` = round 10 ep 3; session → `/v2/coworlds/replays/static/cow_84cce351/sha256%3Ac263c8bd…/index.html?v=2#replay=…`, `ready:true`, no `/client/replay` |
| 7 | Certification declared the static bundle | **TRUE** | Committed 0.1.2 `release-result.json`: `Replay liveness: skipped (static replay bundle declared; …)` |
| 8 | Spectator judgment (viewer executed) | **TRUE** | viewer-check run 33217648127: `loaded:true` in 1938 ms, `failure:null`, clocks L1/f0 → L5/f42 → L8/f60 all differ; endcard matches `results` exactly |

**Verdict: all-true (8 / 8). Nothing was unfetchable; no check invoked a documented exception.**
