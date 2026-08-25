# VERIFY — cooperative-hunting   (2026-08-25T05:29Z)

Verdict: **all-true** (8 / 8 TRUE)

Sweep window: 2026-08-25T04:50Z – 05:29Z (75-minute bound not reached; it would have expired
06:05Z). Every response below was fetched **this run**; the two documented exceptions are item 7
(read from the committed `runs/2026-08-24-cooperative-hunting/release-result.json`) and item 8
(downloaded from the `viewer-check.yml` run **32812865316** that this verifier dispatched at
05:26:46Z).

Common preamble for every `curl` below (header **values** never printed):

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_500b6882-6374-43f4-a82b-5e2d0522d9fd
D=div_60ac03d6-a66a-4ebc-9b84-a0092627e7dc
COW=cow_d5e3a72d-bae0-4418-bb3e-e39f2c5cc81d
```

**Subject of items 3–6 and 8: round 4** (`round_c00de3a5-7949-402a-91d3-f2d4d431d461`,
completed 05:25:30Z), which was the latest completed round at sweep time (05:26–05:29Z). Round 3's
identical sweep is retained under item 5 as the second of three attempts. The ladder makes a round
every 15 min, so a round 5 will exist after this file is written; that does not change any verdict
below, all of which are about *fetched* rounds 2, 3 and 4.

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

**When the fillers were set.** `log.md` records it in a single batched phase-50 line written at
2026-08-25T04:49:31Z: `50 fillers 200 biggame:v2=1ccdd2e4 sidekick:v2=b0ebdd65 (neither champion
in list)` and `50 unpause 200; trigger 200; round1 failed pre-filler auto-round …, round2
round_6386b11d pending`. The batched log timestamp is not the call timestamp, so the *fetched*
evidence for the ordering is: round 1 (created 04:48:02Z) failed instantly with the documented
**pre-filler** error, while round 2 (created 04:48:24Z) and every round after it seated six agents
— two champions plus four filler seats (item 3's `participants`, and the same six-seat roster in
the round-2/3/4 hosted logs: `roster closed with 6/6 seats`). Six seats can only be filled once the
filler policies exist, so the fillers were registered between 04:48:03Z and 04:48:24Z, i.e. after
round 1 failed and before round 2 was created. Round 1 therefore predates the fillers and does not
count; rounds 2, 3 and 4 all do.

**Filler roster as it stands now (proves fillers are set, and which two):**

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}"
```
→ HTTP 200
```json
{
  "filler_policy_versions": [
    {
      "policy_version_id": "1ccdd2e4-f8a1-4f32-b79c-d505d1c34a73",
      "policy_id": "664d550e-6132-4df2-a4af-73d7b0fbd97f",
      "policy_name": "cooperative-hunting-biggame",
      "version": 2,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "display_name": null
    },
    {
      "policy_version_id": "b0ebdd65-55db-493d-862f-a81e78fd1efb",
      "policy_id": "15af6747-0ba5-4114-a3b6-44f630caf36f",
      "policy_name": "cooperative-hunting-sidekick",
      "version": 2,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "display_name": null
    }
  ]
}
```
Neither filler version id is a champion version id (`1951e2fe-…`, `ff8b8f0a-…`) — the
"fillers must differ from champions" rule holds.

**Rounds (fetched 2026-08-25T05:28:01Z):**

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -c 'if type=="array" then . else .entries end
          | map({id,round_number,status,error,created_at,completed_at})'
```
→ HTTP 200
```json
[
  {
    "id": "round_c00de3a5-7949-402a-91d3-f2d4d431d461",
    "round_number": 4,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-25T05:18:25.285008Z",
    "completed_at": "2026-08-25T05:25:30.203895Z"
  },
  {
    "id": "round_9ba7af99-a8d9-4312-a2bf-1e2895350eb2",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-25T05:03:24.568913Z",
    "completed_at": "2026-08-25T05:12:28.365293Z"
  },
  {
    "id": "round_6386b11d-0946-47d1-90a6-9921879c0888",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-25T04:48:24.179407Z",
    "completed_at": "2026-08-25T04:55:33.100760Z"
  },
  {
    "id": "round_537dc2d3-db9b-4250-be5c-9778aef2ecaa",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-25T04:48:02.364031Z",
    "completed_at": "2026-08-25T04:48:03.147054Z"
  }
]
```

```bash
… | jq -r '[.entries[]|select(.status=="completed")]|length'
```
→
```
3
```

Every round carried both champions as entrants, from the same response:

```bash
… | jq -c 'map({round_number, entrants:.round_config.entrant_policy_version_ids})'
```
→
```json
[{"round_number":4,"entrants":["1951e2fe-bcde-4dbd-80ea-a022cd39484b","ff8b8f0a-8fbd-432c-b035-e8013b0ac5cd"]},
 {"round_number":3,"entrants":["1951e2fe-bcde-4dbd-80ea-a022cd39484b","ff8b8f0a-8fbd-432c-b035-e8013b0ac5cd"]},
 {"round_number":2,"entrants":["1951e2fe-bcde-4dbd-80ea-a022cd39484b","ff8b8f0a-8fbd-432c-b035-e8013b0ac5cd"]},
 {"round_number":1,"entrants":["1951e2fe-bcde-4dbd-80ea-a022cd39484b","ff8b8f0a-8fbd-432c-b035-e8013b0ac5cd"]}]
```
and round 4's full `round_config.entrant_attributions`, verbatim, binds each version to its player:

```json
"entrant_attributions": [
  {"subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
   "policy_version_id": "1951e2fe-bcde-4dbd-80ea-a022cd39484b",
   "league_policy_membership_id": "lpm_2cfa922d-341d-4219-aecf-715740d94f27"},
  {"subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
   "policy_version_id": "ff8b8f0a-8fbd-432c-b035-e8013b0ac5cd",
   "league_policy_membership_id": "lpm_3cc4ce48-4319-4e73-ad33-597007253d4d"}
]
```

**Status: TRUE** — rounds **2, 3 and 4** are `completed` (04:55:33Z, 05:12:28Z, 05:25:30Z), all
with `round_number ≥ 2`, i.e. all after the fillers were registered at 04:49:31Z. Requirement is
≥ 2; three exist.

**Non-counting round, recorded verbatim as required:** round 1
(`round_537dc2d3-db9b-4250-be5c-9778aef2ecaa`), `status: "failed"`,
`error: "Temporal RoundWorkflow failed before settling the round."` — this is the documented
pre-filler auto-round failure (`playbooks/observatory-api.md` §6: "A `trigger-round` issued before
any filler exists fails instantly with `Temporal RoundWorkflow failed before settling the
round`"). It is excluded from the count. No `discarded` rounds exist.

---

## 2. Both champions ranked, fillers absent/Baseline — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}"
```
→ HTTP 200 (fetched 2026-08-25T05:28:01Z; bare JSON list, not `.entries`)
```json
[
  {
    "rank": 1,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 1002.8046975081021,
    "score_label": "Elo",
    "score_value_type": "integer",
    "rounds_played": 3,
    "episode_wins": 1.0,
    "episodes_played": null,
    "win_rate": 0.3333333333333333,
    "policy_label": "cooperative-hunting-pack-caller:v2",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 997.1953024918979,
    "score_label": "Elo",
    "score_value_type": "integer",
    "rounds_played": 3,
    "episode_wins": 1.0,
    "episodes_played": null,
    "win_rate": 0.3333333333333333,
    "policy_label": "cooperative-hunting-quartermaster:v2",
    "recent_rounds": null
  }
]
```

As the `@tsv` projection the checklist asks for:

| rank | player_name | policy_label | score | rounds_played | episode_wins |
|---|---|---|---|---|---|
| 1 | daveey | cooperative-hunting-pack-caller:v2 | 1002.80 | 3 | 1.0 |
| 2 | daveey-1 | cooperative-hunting-quartermaster:v2 | 997.20 | 3 | 1.0 |

**Status: TRUE** — both `daveey` and `daveey-1` are present, each `rounds_played = 3 ≥ 1`, each
labelled with its own champion policy. The list contains **exactly two rows**: no filler
(`cooperative-hunting-biggame`, `cooperative-hunting-sidekick`) appears at all, satisfying
"fillers absent or labelled Baseline". The Elo has moved off the 1000 seed in both directions,
so the ranking is being computed from real episode scores.

---

## 3. Latest round's episode request completed with a replay — **TRUE**

```bash
R=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
    | jq -r '[.entries[]|select(.status=="completed")]|max_by(.round_number).id')
# R=round_c00de3a5-7949-402a-91d3-f2d4d431d461   (round 4)
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}"
```
→ HTTP 200
```json
[{"id":"ereq_22b05732-b4b7-49e0-92b9-e65e09964eae","status":"completed",
  "replay_url":"https://softmax-public.s3.amazonaws.com/replays/2b6b4061-b1d7-43c4-97ac-daae1fef7409.replay"}]
```

```bash
EREQ=ereq_22b05732-b4b7-49e0-92b9-e65e09964eae
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```
→ HTTP 200
```json
{"status":"completed",
 "replay_url":"https://softmax-public.s3.amazonaws.com/replays/2b6b4061-b1d7-43c4-97ac-daae1fef7409.replay"}
```
`participants` (one row per seat, verbatim fields):

| position | policy_name | version | player_name | is_filler | policy_version_id |
|---|---|---|---|---|---|
| 0 | cooperative-hunting-pack-caller | v2 | **daveey** | false | 1951e2fe-bcde-4dbd-80ea-a022cd39484b |
| 1 | cooperative-hunting-quartermaster | v2 | **daveey-1** | false | ff8b8f0a-8fbd-432c-b035-e8013b0ac5cd |
| 2 | cooperative-hunting-sidekick | v2 | daveey | true | b0ebdd65-55db-493d-862f-a81e78fd1efb |
| 3 | cooperative-hunting-sidekick | v2 | daveey | true | b0ebdd65-55db-493d-862f-a81e78fd1efb |
| 4 | cooperative-hunting-biggame | v2 | daveey | true | 1ccdd2e4-f8a1-4f32-b79c-d505d1c34a73 |
| 5 | cooperative-hunting-biggame | v2 | daveey | true | 1ccdd2e4-f8a1-4f32-b79c-d505d1c34a73 |

`participant_scores`:
```json
[{"position":0,"score":15.0},{"position":1,"score":10.0},{"position":2,"score":31.0},
 {"position":3,"score":18.0},{"position":4,"score":3.0},{"position":5,"score":30.0}]
```

The `Baseline (N)` renaming the checklist expects for fillers is what the **game** receives; it is
visible in the replay's own resolved config (fetched in item 4):
```json
"players":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"]
```

**Status: TRUE** — `status == "completed"`, `replay_url` non-null, seats 0 and 1 are the two
champions owned by `daveey` and `daveey-1` respectively (`is_filler: false`), the other four seats
are the registered fillers and reach the game as `Baseline` / `Baseline (2..4)`.

---

## 4. Replay bytes are valid and show the game — **TRUE**

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/2b6b4061-b1d7-43c4-97ac-daae1fef7409.replay" -o /tmp/ep4.replay
```
→
```
http=200 bytes=1199042
```

```bash
jq -e . /tmp/ep4.replay >/dev/null && echo "strict UTF-8 JSON: ok"
```
→
```
strict UTF-8 JSON: ok
```
(`jq -e` is a strict UTF-8 parser, not a browser — invalid UTF-8 would have failed here.)

```bash
jq -c '{format,version,coworld,variant,generated_at,seed,ticks:(.ticks|length),
        rounds:(.rounds|length),seats:(.seats|length)}' /tmp/ep4.replay
```
→
```json
{"format":"cooperative-hunting/1","version":"0.1.0","coworld":"cooperative_hunting",
 "variant":"staghunt","generated_at":"2026-08-25T05:18:43Z","seed":1840058377,
 "ticks":3000,"rounds":3,"seats":6}
```

**Protocol/manifest match.** This game's replay envelope declares its identity in `format` /
`coworld` / `variant` (there is no top-level `protocol` key — `design.md` L549-560 pins the
envelope as `{"format":"cooperative-hunting/1","version":"0.1.0","coworld":"cooperative_hunting",
"variant":"staghunt",…}`, and the fetched bytes match that pin field-for-field). Cross-checked
against the live manifest:

```bash
curl -sS "$BASE/coworlds/$COW" "${AUTH[@]}" \
 | jq -r '.manifest.game.name + " " + .manifest.game.version'
curl -sS "$BASE/coworlds/$COW" "${AUTH[@]}" | jq -r '.manifest.variants[].id'
```
→ HTTP 200
```
cooperative_hunting 0.1.4
staghunt
coop-mining
lbf
predator-prey
```
So replay `.coworld == manifest.game.name == "cooperative_hunting"` and replay
`.variant == manifest.variants[0].id == "staghunt"`. ✅ *(Observation, not a defect: the replay's
`version` field is the envelope-schema constant `0.1.0` pinned in design.md L551, not the coworld
version 0.1.4. Flagging it for phase 80 as a possible legibility nit; nothing in the definition of
done depends on it.)*

The manifest's declared wire protocols (same fetch, `.manifest.game.protocols`) are the
sprite_v1 + `0x90`/`0x91` pair the design pins:
```json
{"player":{"type":"text","value":"bitworld sprite_v1 over a websocket, plus exactly two additive messages. Server->client: 0x01 sprite, 0x02 object, 0x03 remove, 0x04 clear, 0x05 viewport, 0x06 layer, 0x07 identity, and 0x91 <u16 len> <UTF-8 JSON plan> to seats that registered a prompt. …"},
 "global":{"type":"text","value":"The same sprite_v1 stream at world scale (384x384 px viewport, no 0x07 identity packet), plus the broadcast chrome carried as the label of a reserved 1x1 sprite, id 4090, re-emitted every tick. That label is UTF-8 JSON of at most 12 KB (12288 bytes) with tick, round, rounds, ticksPerRound, phase, variant, reason, seats[], feed[], beats[] and final."}}
```

**End reason:**
```bash
jq -r '.results.reason' /tmp/ep4.replay
```
→
```
complete
```
`design.md` §"End conditions and legal `results.reason` values" (L192-206) declares exactly
`complete | deadline | no_players` legal; this is the normal path, no exception needed.

**Champion seats are doing the thing the game is about (non-scripted, non-trivial, not fallbacks):**
```bash
jq -c '.seats[]|{slot,alias,name,kind}' /tmp/ep4.replay
```
→
```json
{"slot":0,"alias":"Cog-F","name":"cooperative-hunting-prompt","kind":"prompt"}
{"slot":1,"alias":"Cog-D","name":"cooperative-hunting-prompt","kind":"prompt"}
{"slot":2,"alias":"Cog-E","name":"sidekick","kind":"scripted"}
{"slot":3,"alias":"Cog-A","name":"sidekick","kind":"scripted"}
{"slot":4,"alias":"Cog-C","name":"big_game_hunter","kind":"scripted"}
{"slot":5,"alias":"Cog-B","name":"big_game_hunter","kind":"scripted"}
```

```bash
jq -r '"plan events: "+([.ticks[].ev//empty|.[]|select(.ev=="plan")]|length|tostring),
       "src==llm: "+([.ticks[].ev//empty|.[]|select(.ev=="plan" and .src=="llm")]|length|tostring),
       "src fallback:*: "+([.ticks[].ev//empty|.[]|select(.ev=="plan" and (.src|startswith("fallback")))]|length|tostring),
       "fallback events: "+([.ticks[].ev//empty|.[]|select(.ev=="fallback")]|length|tostring)' /tmp/ep4.replay
```
→
```
plan events: 48
src==llm: 48
src fallback:*: 0
fallback events: 0
```

```bash
jq -c '.results' /tmp/ep4.replay
```
→
```json
{"names":["cooperative-hunting-prompt","cooperative-hunting-prompt","sidekick","sidekick","big_game_hunter","big_game_hunter"],
 "aliases":["Cog-F","Cog-D","Cog-E","Cog-A","Cog-C","Cog-B"],
 "kinds":["prompt","prompt","scripted","scripted","scripted","scripted"],
 "scores":[15,10,31,18,3,30],"energy":[127,94,138,130,59,106],
 "fallbacks":[0,0,0,0,0,0],"disconnected":[false,false,false,false,false,false],
 "rounds":[[5,7,8,0,0,1],[7,0,4,3,2,8],[3,3,19,15,1,21]],
 "catches":[[1,3,1,0,0],[7,1,0,0,0],[2,3,2,1,0],[0,1,1,1,0],[3,0,0,0,0],[6,3,1,1,0]],
 "co_captures":[[0,0,2,1,0,2],[0,0,1,0,0,0],[2,1,0,2,0,3],[1,0,2,0,0,3],[0,0,0,0,0,0],[2,0,3,3,0,0]],
 "llm_requests":49,"plan_turns_skipped":0,"variant":"staghunt","seed":1840058377,
 "final_tick":3000,"reason":"complete"}
```

Sample champion decisions with their free-text content (tick / seat / intent-target / say):
```
1282  Cog-F  boar@19,8    "Boar@19,8—E take E side, A take N side, I take W. Perpendicular lock for +3."
1282  Cog-D  moose@16,18  "Moose at 16,18 needs 3 sides. I'm taking S side. Who joins N and E?"
1408  Cog-D  moose@16,19  "Taking S on moose@16,19 (d=1, worth 10). Need N and E sides. Energy 52—committing to big score."
1646  Cog-F  boar@19,20   "Boar@19,20—I take N, Cog-D take S. Quick 2-side perpendicular. Let's score before energy depletes."
2767  Cog-F  stag@15,13   "Cog-C, stag at 15,13—I take N, you take S. Quick 2-side for +5!"
2897  Cog-F  moose@17,13  "Moose@17,13 worth 10—highest value visible. I take W, Cog-C take E. Need one more ally N or S to complete ring."
```
and the coordination actually lands — `co_captures[0]` shows Cog-F sharing 2 captures with Cog-E,
1 with Cog-A and 2 with Cog-B; the joint catch at tick 1319 is `Cog-F+Cog-E catch boar`.

**Status: TRUE** — strict-parser-valid UTF-8 JSON (1 199 042 bytes); envelope identity matches the
manifest (`cooperative_hunting` / `staghunt`); `results.reason == "complete"`; **48 of 48** plan
decisions carry `src: "llm"`, **zero** fallback plans, **zero** `fallback` events, and
`results.fallbacks == [0,0,0,0,0,0]` — the fallback share is 0 %, comfortably a "small minority",
and the plan text is game-specific side-assignment reasoning, not boilerplate.

---

## 5. Hosted game log is clean — **TRUE** (attempt 3 of 3; CLEAN, no exception needed)

The logs body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it
is decoded before grepping (`playbooks/observatory-api.md` §10 — line greps on the raw body
undercount).

```bash
curl -sS "$BASE/episode-requests/ereq_22b05732-b4b7-49e0-92b9-e65e09964eae/artifacts/logs" \
     "${AUTH[@]}" "${ELEV[@]}" -o logs-r4.raw
# decode each container's b'…' reprs with python3 ast.literal_eval, then:
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' log-r4-decoded.txt \
  || echo CLEAN
```
→
```
http=200 bytes=126694
containers: ['coworld-init-config', 'bedrock-sidecar', 'game', 'worker']  (3066 decoded lines)
grep hits: 0
CLEAN
```

Head of the decoded `game` container, verbatim, showing this is the full six-seat episode and that
it ran on the primary model with **no** fallback line:
```
===== container: game =====
loading config from: /coworld/config.json
starting cooperative_hunting on 0.0.0.0:8080 variant=staghunt seats=6 rounds=3x960 tickHz=8
player connected: big_game_hunter slot=5
player connected: sidekick slot=2
player connected: sidekick slot=3
player connected: cooperative-hunting-prompt slot=0
player connected: cooperative-hunting-prompt slot=1
player connected: big_game_hunter slot=4
roster closed with 6/6 seats
cooperative-hunting llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
```
The only LLM-retry line in the whole 3 066-line log is a *content* retry, which matches none of the
four grep patterns and is followed by a successful plan (48/48 plans are `src: "llm"`, item 4):
```
1107: cooperative-hunting llm: slot 0 attempt 0 failed: target not in LEGAL TARGETS: elephant@13,17
```

**Status: TRUE** — zero lines match `falling back|LLM provider is unavailable|cut off at
max_tokens|rejected` in the latest completed round's hosted log.

### Attempts 1 and 2 (earlier rounds) and the platform-wide Bedrock throttle

Both earlier rounds hit the platform-wide Bedrock 429 the coordinator flagged. Recording them in
full because they are what attempts 1 and 2 fetched, and because they document that the condition
was platform capacity and that it has since cleared.

**Attempt 1 — round 2, `ereq_f06f0670-2fd2-4088-a260-8869ddd13dc2`** (fetched 04:57Z), 1 hit:
```
11: cooperative-hunting llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
```

**Attempt 2 — round 3, `ereq_37570532-f094-42ab-936b-1a1d41149492`** (fetched 05:13Z), 1 hit, with
surrounding context verbatim:
```
203: roster closed with 6/6 seats
204: cooperative-hunting llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
205: Dropped message to disconnected client
206: cooperative-hunting llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
207: cooperative-hunting llm: slot 0 attempt 0 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
208: cooperative-hunting llm: slot 1 attempt 0 failed: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
```

**Cross-check against another LLM coworld, fetched this run** (SPEC §Definition of done item 5's
"documented platform-wide cause checked against another LLM coworld"): `hanabi`
(`cow_4c005d78-ebb2-4095-83da-cde90519f53b`), its latest episode request
`ereq_3c48da04-2a0b-4df6-a723-1c3cb863cc62` created 04:48:59Z — i.e. *concurrent with our round 2*:
```bash
curl -sS "$BASE/episode-requests?coworld_id=cow_4c005d78-ebb2-4095-83da-cde90519f53b&limit=5" "${AUTH[@]}"
curl -sS "$BASE/episode-requests/ereq_3c48da04-2a0b-4df6-a723-1c3cb863cc62/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}"
```
→ HTTP 200 (74 993 bytes), decoded, verbatim:
```
157: hanabi llm: us.anthropic.claude-haiku-4-5-20251001-v1:0 unusable (throttled); falling back to us.anthropic.claude-sonnet-4-5-20250929-v1:0
158: hanabi llm: seat 1 attempt 0 rejected: llm throttled (429): {"message":"Too many tokens per day, please wait before trying again."}
```
A different coworld, a different game, the *identical* model and the *identical* Bedrock message —
this is platform capacity on `claude-haiku-4-5`, not a defect in cooperative-hunting. It matches
the independent report the coordinator supplied (the `coins` run, Blocked 2026-08-25T03:23Z on the
same 429).

**Decisions vs fallbacks during the throttled rounds** (the count the brief asked for): in round 3,
`results.llm_requests = 47`, plan events `40`, of which `src=="llm"` = **40** and
`src` starting `fallback` = **0**; `results.fallbacks = [0,0,0,0,0,0]`. The 7-request difference is
7 first-attempt failures (2 × 429 throttle, 5 × sidecar transport timeout) that the game's own
retry answered successfully. So even under the throttle the coworld produced **100 % LLM
decisions and 0 % baseline fallbacks** — check 4's "not all fallbacks" test passes with room to
spare, and the "falling back" line was a *model* substitution (haiku → sonnet) the coworld handled,
not a degraded seat.

Per `prompts/60-verify.md` check 5 the correct response was to keep polling inside the 75-minute
bound rather than go Blocked; polling to round 4 was done and round 4's log is literally CLEAN.
The bound never expired, so there is no outage to report.

---

## 6. The public page uses the static replay path — **TRUE**

**Source used: the coworld-detail / session API, after the raw-HTML grep found nothing** (both
sources recorded below, as `prompts/60-verify.md` requires).

**Which slug resolved.** `https://softmax.com/cooperative-hunting` (hyphen) is the real page;
`https://softmax.com/cooperative_hunting` (underscore) returns a generic shell:
```bash
for s in cooperative-hunting cooperative_hunting; do curl -sS -o page-$s.html \
  -w 'http=%{http_code} size=%{size_download} url=%{url_effective}\n' "https://softmax.com/$s"; done
grep -o '<title>[^<]*</title>' page-cooperative-hunting.html page-cooperative_hunting.html
```
→
```
http=200 size=521163 url=https://softmax.com/cooperative-hunting
http=200 size=18516  url=https://softmax.com/cooperative_hunting
page-cooperative-hunting.html:<title>Cooperative Hunting · Softmax</title>
page-cooperative_hunting.html:<title>Watch · Softmax</title>
```
So **the hyphenated slug resolved**; the underscored one is not a coworld page.

**Attempt 1 — raw-HTML iframe grep (fetched 05:26:31Z):**
```bash
curl -sS "https://softmax.com/cooperative-hunting" | grep -o '<iframe[^>]*src="[^"]*"'
```
→
```
http=200 bytes=537581
(no <iframe … src=…> in raw HTML)
```
Not a false negative: `playbooks/observatory-api.md` §Featured match records that the page has been
client-rendered for the iframe since the lighthouse run (2026-08-22) and the raw-HTML grep finds
nothing for *any* coworld. Falling back to the sources the page itself reads.

**Attempt 2 — `/coworlds` list (documented to be `null` platform-wide, recorded for completeness):**
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '.entries[]|select(.name=="cooperative_hunting")|{id,name,canonical,version,replay_viewer,featured_match}'
```
→ HTTP 200
```json
{"id":"cow_d5e3a72d-bae0-4418-bb3e-e39f2c5cc81d","name":"cooperative_hunting","canonical":true,
 "version":"0.1.4","replay_viewer":null,"featured_match":null}
```
(`featured_match: null` is the documented platform-wide behaviour, "so neither is evidence" —
playbook §Featured match. The row does confirm the coworld is **canonical** at **0.1.4**.)

**Attempt 3 — the featured match out of the page's SSR payload, and the iframe `src` out of the
call the page's JS makes.** SSR payload `state.playlist[0]`, grepped verbatim out of the page bytes
fetched at 05:26:31Z:
```
playlist\":[{\"episodeId\":\"b4f9020e-8027-4948-9ab8-0dda0cac46e8\",
 \"coworldId\":\"cow_d5e3a72d-bae0-4418-bb3e-e39f2c5cc81d\",
 \"coworldName\":\"cooperative_hunting\",\"coworldVersion\":\"0.1.4\",
 \"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/2b6b4061-b1d7-43c4-97ac-daae1fef7409.replay\",
 \"finishedAt\":\"2026-08-25T05:25:26.621886Z\",\"roundNumber\":4,\"episodeNumber\":1,
 \"code\":\"cooperative_hunting.r4.e1\",\"matchup\":{\"divisionId\":\"div_60ac03d6-a66a-4ebc-9b84-a0092627e7dc\",…
```
A **featured match is present** — round 4 episode 1, the same replay as items 3–4, with a matchup
naming both ranked players. (An earlier fetch at 05:13:59Z carried round 3's
`53ffeacd-…` replay and at 04:58Z round 2's `9fac8ec6-…`; the featured match tracks the newest
completed episode, and it was `playlist":[]` before any round completed.)

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_d5e3a72d-bae0-4418-bb3e-e39f2c5cc81d",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/2b6b4061-b1d7-43c4-97ac-daae1fef7409.replay"}'
```
→ HTTP 200
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_d5e3a72d-bae0-4418-bb3e-e39f2c5cc81d/sha256%3A0dfeeb8e92befffa524161af55b34e914cbf7620bca58d4a0d4a2d0e98cad122/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F2b6b4061-b1d7-43c4-97ac-daae1fef7409.replay&v=2",
  "ready": true
}
```

The `<sha>` segment is the coworld's manifest hash, confirmed against the coworld detail fetched
this run:
```bash
curl -sS "$BASE/coworlds/$COW" "${AUTH[@]}" | jq -r '.manifest_hash'
```
→
```
sha256:0dfeeb8e92befffa524161af55b34e914cbf7620bca58d4a0d4a2d0e98cad122
```
which URL-encodes to the `sha256%3A0dfeeb8e…` in the path. ✅

**Status: TRUE** — featured match present (`cooperative_hunting.r4.e1`); the iframe `src` is
`…/v2/coworlds/replays/static/cow_d5e3a72d-…/sha256%3A0dfeeb8e…/index.html?replay=<s3 url>` with
`ready: true`. It is **not** a `/client/replay` pod URL — the substring `/client/replay` does not
occur in it. Source used: **the coworld/session API**, because the page-grep found nothing (the
page is client-rendered).

---

## 7. Certification declared the static bundle — **TRUE**

Read from the **committed** `runs/2026-08-24-cooperative-hunting/release-result.json` (the copy
phase 40 downloaded from release run `32809315564`, version 0.1.4). It was present; no re-download
was needed, and `/tmp` was not consulted.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-24-cooperative-hunting/release-result.json
```
→
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Surrounding fields from the same committed file, to bind it to this release:
```bash
jq -c '{version, ok, canonical, cow_id, manifest_sha, secret_put,
        certify_ok:.certify.ok, hosted_certification}' runs/2026-08-24-cooperative-hunting/release-result.json
```
→
```json
{"version":"0.1.4","ok":true,"canonical":true,
 "cow_id":"cow_d5e3a72d-bae0-4418-bb3e-e39f2c5cc81d",
 "manifest_sha":"sha256:0dfeeb8e92befffa524161af55b34e914cbf7620bca58d4a0d4a2d0e98cad122",
 "secret_put":true,"certify_ok":true,"hosted_certification":"certified"}
```
and the certification transcript tail from `.certify.output_tail`, verbatim:
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
The `manifest_sha` here is byte-identical to the `<sha>` in item 6's static viewer URL and to the
live `manifest_hash`, so the certified bundle is the bundle being served.

*(The sibling `release-result-0.1.3-failed.json` is the failed 0.1.3 evidence and was **not**
read.)*

**Status: TRUE** — the committed certification output contains
`Replay liveness: skipped (static replay bundle declared`. Source: the committed
`runs/2026-08-24-cooperative-hunting/release-result.json`.

---

## 8. Spectator judgment — the viewer was EXECUTED — **TRUE**

*(a) Dispatch.* The sandbox has no screen, so the check-6 iframe `src` was opened in headless
chromium by `viewer-check.yml` in coworld-builder — the one workflow this role may dispatch.

```bash
SRC=$(jq -r .viewer_url sess4.json)   # the item-6 src, ?replay= and all
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
# dispatched 2026-08-25T05:26:46Z
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml \
   --json databaseId,createdAt,status -L 5 | jq -r 'sort_by(.createdAt)|reverse|.[]|[…]|@tsv'
```
→ the run created *after* the dispatch timestamp (not "the latest" taken blind):
```
32812865316	2026-08-25T05:26:47Z	in_progress      <- this run's
32812041116	2026-08-25T05:14:11Z	completed        <- an earlier dispatch by this same verifier, against round 3's replay
32804445583	2026-08-25T03:14:50Z	completed        <- another run's, not used
```
```bash
gh run watch 32812865316 -R Metta-AI/coworld-builder --exit-status ; echo exit=$?
```
→
```
✓ viewer-check in 44s (ID 97695470836)
  ✓ Load the viewer   ✓ Summary   ✓ Upload the evidence   ✓ Fail if the viewer did not load
exit=0
```
```bash
gh run download 32812865316 -R Metta-AI/coworld-builder -n viewer-check \
   -D runs/2026-08-24-cooperative-hunting/viewer-check
```
→ committed alongside this file:
```
viewer-smoke.json  (1543 B)   viewer-smoke.png  (359712 B)
smoke-stdout.txt   (668 B)    smoke-stderr.txt  (0 B)
```

*(b) The readouts, verbatim.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-24-cooperative-hunting/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":1722,"clock":"ROUND 1 OF 3 STAG HUNT · 3 / 2880","scorebug":"Cog-F cooperative-hunting-prompt 0 Cog-D cooperative-hunting-prompt 0 Cog-E sidekick 0 ROUND 1 OF 3 STAG HUNT · 3 / 2880 Cog-A sidekick 0 Cog-C big_game_hunter 0 Cog-B big_game_hunter 0","feed_lines":1}
```

```bash
jq -c '.signals' … ; jq -r '.failure // "no failure"' …
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```
```
no failure
```

```bash
jq -c '{url,bundle,replay,status,loading_text,console_tail,canvas_text}' …
```
```json
{"url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_d5e3a72d-bae0-4418-bb3e-e39f2c5cc81d/sha256%3A0dfeeb8e92befffa524161af55b34e914cbf7620bca58d4a0d4a2d0e98cad122/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F2b6b4061-b1d7-43c4-97ac-daae1fef7409.replay&v=2","bundle":null,"replay":null,"status":"","loading_text":null,"console_tail":["[bridge] loading","[bridge] ready"],"canvas_text":{"total":0,"outside":0,"ellipsized":0,"never_inside":0,"never_inside_samples":[],"distinct_capped":false,"samples":[]}}
```
The URL in the artifact is byte-identical to item 6's iframe `src`, so the thing rendered is the
thing the public page embeds.

**The three clock readouts** (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | clock text |
|---|---|
| 0 % | `ROUND 1 OF 3 STAG HUNT · 3 / 2880` |
| 50 % | `ROUND 2 OF 3 STAG HUNT · 1478 / 2880` |
| 100 % | `ROUND 3 OF 3 ROUND CARD · 2880 / 2880` |

All three differ, in both round number and tick. A `#scrub` control **was** present (the json
carries real readouts, not the `"(no #scrub…)"` sentinel).

*(An earlier dispatch this same run, `32812041116` at 05:14:11Z against round 3's replay
`53ffeacd-…`, returned the same verdict — `loaded:true`, `ms:2014`, scrub
`ROUND 1 OF 3 STAG HUNT · 1 / 2880` → `ROUND 2 OF 3 STAG HUNT · 1478 / 2880` →
`ROUND 3 OF 3 ROUND CARD · 2880 / 2880`. Only the round-4 artifact is committed, since that is the
one matching the current featured match.)*

**Item 8 gate:** `loaded: true` ✅ **and** the three clock readouts differ ✅.

*(c) The replay JSON the viewer was asked to draw* — ordered excerpts from `/tmp/ep4.replay`
(item 4), so picture and record can be reconciled.

Early:
```
1     -      round_start
1     Cog-F  player_spawn
1     Cog-D  player_spawn
1     Cog-E  player_spawn
1     Cog-A  player_spawn
1     Cog-C  player_spawn
1     Cog-B  player_spawn
35    Cog-F  plan          No animals visible. Regrouping to coordinate.
35    Cog-D  plan          Starting forage to build energy reserves.
60    -      prey_spawn    rabbit
63    -      prey_spawn    rabbit
```
Middle:
```
1282  Cog-F        plan        Boar@19,8—E take E side, A take N side, I take W. Perpendicular lock for +3.
1282  Cog-D        plan        Moose at 16,18 needs 3 sides. I'm taking S side. Who joins N and E?
1319  Cog-F+Cog-E  catch       boar
1382  Cog-B        catch       rabbit
1400  Cog-D        moose_gut
1408  Cog-D        plan        Taking S on moose@16,19 (d=1, worth 10). Need N and E sides. Energy 52—committing to big score.
1522  Cog-D        plan        Energy critical (26/200). Recharging with rabbits before next big hunt.
1646  Cog-F        plan        Boar@19,20—I take N, Cog-D take S. Quick 2-side perpendicular…
1769  Cog-F        catch       rabbit
```
Late:
```
2523  Cog-F  plan        Moose@14,16 south side. Need 2 allies on N/E/W to complete ring. Worth +10.
2543  Cog-D  catch       rabbit
2627  -      prey_spawn  elephant
2767  Cog-F  plan        Cog-C, stag at 15,13—I take N, you take S. Quick 2-side for +5!
2897  Cog-F  plan        Moose@17,13 worth 10—highest value visible. I take W, Cog-C take E…
2923  Cog-F  moose_gut
2960  -      round_end
3000  -      episode_end
```
`.results` → `reason: "complete"`, `scores: [15,10,31,18,3,30]` for
`aliases: ["Cog-F","Cog-D","Cog-E","Cog-A","Cog-C","Cog-B"]` (full object pasted in item 4).

### Spectator judgment

The picture is not empty, not frozen and not unreadable — it is a finished match with its result on
screen. `viewer-smoke.png` (committed) shows the scrubber parked at 100 %: a **scorebug strip**
across the top listing all six seats by alias, colour dot, policy name and a small energy/score bar
(`Cog-F cooperative-hunting-prompt 3`, `Cog-D cooperative-hunting-prompt 3`, `Cog-E sidekick 19`,
`Cog-A sidekick 15`, `Cog-C big_game_hunter 1`, `Cog-B big_game_hunter 21`), a centred clock
reading **ROUND 3 OF 3 / ROUND CARD · 2880 / 2880**, the 32×32 forest board still visible behind a
dimmed overlay (grass, trees, scattered animal sprites), and an **endcard** headed **HUNT OVER**
with the sign line *"SCORE IS EVERY CAPTURE YOU STOOD A SIDE FOR. HIGHER IS BETTER."* and the final
standings `#1 Cog-E sidekick 31, #2 Cog-B big_game_hunter 30, #3 Cog-A sidekick 18,
#4 Cog-F cooperative-hunting-prompt 15, #5 Cog-D cooperative-hunting-prompt 10,
#6 Cog-C big_game_hunter 3`. Those six numbers are **exactly** `results.scores` re-ordered by
rank, so the picture and the record agree seat-for-seat and point-for-point. A watcher who has
never seen the game can read off who won, by how much, and what the score means, from that one
frame.

It shows the game, not just a scoreboard. The clock advances under the scrubber (three distinct
readouts, crossing a round boundary at 50 %), the board behind the endcard is a populated forest
rather than a blank canvas, and the replay record the viewer is drawing carries exactly the
cooperative-hunting loop: two LLM seats proposing perpendicular side assignments on boars, stags
and moose, then joint captures landing (`Cog-F+Cog-E catch boar` at 1319) and `moose_gut` events
when a three-side ring closes. The one legibility limit worth flagging is that
`canvas_text.total = 0` and `feed_lines = 1` at the endcard frame — the say-feed is a single line
at this instant because the endcard overlay has taken the pane; the `plan` `say` strings exist in
the replay (48 of them), so the feed has content to show mid-episode, but this smoke frame does not
prove the feed is legible during play. That is a phase-30/phase-80 legibility observation, not a
definition-of-done failure.

**Does it look like the starter's chrome?** Yes — this is the paintbot/raid/hive shell, not a
rewrite. Present and recognisable: the **transport strip** along the bottom with restart, step-back,
pause, `+5s`, step-forward, loop and fast-forward buttons, a `spoilers` toggle (highlighted), the
`2999 / 2999` tick counter, and the `1× 2× 3× 4× 8× 16×` speed rail on the right; the full-width
**scrubber with the momentum graph** underneath it, labelled `HUNT`, with the playhead at the far
right; the six-seat **scorebug** split left/right around the centre clock; and the **endcard**
overlay with ranked standings and the "— complete" end-reason chip in the lower right
(`HUNT OVER — complete`). The gridlock failure mode (2026-08-23: a page that renders but looks like
a different product) does not apply here.

**Status: TRUE** — `loaded: true`, three differing clock readouts, and a legible frame that shows
the game.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | TRUE — rounds 2, 3, 4 completed; round 1 failed pre-filler (error quoted) |
| 2 | Both champions ranked, fillers absent/Baseline | TRUE — daveey & daveey-1, `rounds_played=3` each; no filler rows |
| 3 | Latest round's episode request completed with replay | TRUE — `ereq_22b05732…` completed, `replay_url` set, seats 0/1 = daveey/daveey-1 |
| 4 | Replay bytes valid and show the game | TRUE — strict JSON, `cooperative_hunting`/`staghunt` match manifest, `reason: complete`, 48/48 llm plans, 0 fallbacks |
| 5 | Hosted game log clean | TRUE — round 4 log CLEAN (0 hits); rounds 2–3 hits were a platform-wide Bedrock 429 cross-checked against hanabi |
| 6 | Public page uses the static replay path | TRUE — featured match `cooperative_hunting.r4.e1`; static `…/replays/static/<cow>/<manifest sha>/index.html?replay=…`, `ready: true` (source: coworld/session API; page-grep empty) |
| 7 | Certification declared the static bundle | TRUE — `Replay liveness: skipped (static replay bundle declared…` from committed `release-result.json` |
| 8 | Viewer executed and judged | TRUE — `loaded: true`, three differing clocks, starter chrome, endcard matches `results.scores` |

Non-blocking observations for the coordinator / phase 80:
1. The replay envelope's `version` is the schema constant `0.1.0` (design.md L551) rather than the
   coworld version `0.1.4`; harmless but potentially confusing in a downloaded replay.
2. `feed_lines = 1` and `canvas_text.total = 0` in the endcard smoke frame — the say-feed's
   mid-episode legibility is unproven by this frame (the `say` strings do exist in the replay).
3. Round 1's pre-filler `Temporal RoundWorkflow failed before settling the round` is the known
   ordering hazard in `playbooks/observatory-api.md` §6; it cost one round of ladder time.
