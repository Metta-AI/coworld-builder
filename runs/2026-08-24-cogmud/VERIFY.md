# VERIFY — cogmud   (2026-08-24T05:42Z)

Verdict: **1 item false** (checks 1, 2, 3, 4, 6, 7, 8 TRUE; **check 5 FALSE**)

Run: `2026-08-24-cogmud` · slug `cogmud` · coworld `cow_42773bd0-0a21-4cca-94b2-41cd26b2d6ed` v0.1.0
League `league_c8ba20f2-f4b2-4e68-b8ad-ba75c5eca66a` · division `div_711fc80a-6b0f-453c-9e31-a4816e7eefd8`

**Pinning.** Checks 3, 4, 5, 6 and 8 are pinned to **round 3**
(`round_578a4ce5-cc9d-45a0-93b6-6b8cc8eef912`, episode request
`ereq_1151194f-c9ea-4ce8-8d76-51f6b3af1d7b`, replay
`632e1ef6-7d66-4ad6-afd7-67aa2e772f97.replay`), which was the **latest completed round at the
moment check 3 was executed (2026-08-24T05:26:33Z)**. The rendered evidence in check 8 is bound to
that replay, so the remaining checks stay on the same episode rather than chasing the ladder.
Round 4 completed later (05:40Z) and is reported as supporting evidence under checks 1 and 5.

Headers sent on every Observatory call: `Authorization: Bearer <redacted>` and
`User-Agent: coworld-builder/1.0`; elevated calls add `X-Use-Elevated-Privileges: true`.
No token values or token-bearing URLs appear below.

Polling window: opened 2026-08-24T05:05:27Z, bound 75 min (expiry 06:20:27Z). Two post-filler
rounds were completed by 05:26:06Z — 21 minutes in, well inside the bound.

---

## 1. ≥2 completed rounds after fillers were set — **TRUE**

Summary: rounds **2** and **3** are `completed` (round 4 also completed later). Both were created
*after* the fillers were registered; round 1 `failed` and is excluded, its `error` recorded verbatim.

**Command** (fetched 2026-08-24T05:26:18Z):
```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq 'if type=="array" then . else .entries end
       | map({id,round_number,status,error,created_at,
              entrants:(.round_config.entrant_attributions//null)})'
```

**Response** (`/rounds` returned `{entries:[…]}` here; the `if type=="array"` guard is kept because
some list endpoints return a bare array):
```json
[
  {
    "id": "round_578a4ce5-cc9d-45a0-93b6-6b8cc8eef912",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-24T05:17:28.031799Z",
    "entrants": [
      { "subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
        "policy_version_id": "f3ef3f5a-4399-43da-8eba-d950ee5390a1",
        "league_policy_membership_id": "lpm_ac322e31-5ff7-48b9-8010-a0c30d428250" },
      { "subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
        "policy_version_id": "df2537fd-2ca7-4ea5-8ab0-a34dfa64daf2",
        "league_policy_membership_id": "lpm_e3c016b2-ab84-4054-8452-5b904b0a70fd" }
    ]
  },
  {
    "id": "round_a8fbacd3-cc5b-4754-ac93-3a7647322d54",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-24T05:02:27.040927Z",
    "entrants": [
      { "subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
        "policy_version_id": "f3ef3f5a-4399-43da-8eba-d950ee5390a1",
        "league_policy_membership_id": "lpm_ac322e31-5ff7-48b9-8010-a0c30d428250" },
      { "subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
        "policy_version_id": "df2537fd-2ca7-4ea5-8ab0-a34dfa64daf2",
        "league_policy_membership_id": "lpm_e3c016b2-ab84-4054-8452-5b904b0a70fd" }
    ]
  },
  {
    "id": "round_7281fe2e-3c0b-4c5a-affe-15a952c44dfa",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-24T05:02:00.730415Z",
    "entrants": [
      { "subject_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "subject_type": "player",
        "policy_version_id": "f3ef3f5a-4399-43da-8eba-d950ee5390a1",
        "league_policy_membership_id": "lpm_ac322e31-5ff7-48b9-8010-a0c30d428250" },
      { "subject_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "subject_type": "player",
        "policy_version_id": "df2537fd-2ca7-4ea5-8ab0-a34dfa64daf2",
        "league_policy_membership_id": "lpm_e3c016b2-ab84-4054-8452-5b904b0a70fd" }
    ]
  }
]
```
```bash
$ … | jq -r '… | [.[]|select(.status=="completed")]|length'
2
```

**Round 1's error, verbatim:** `Temporal RoundWorkflow failed before settling the round.`
This is the documented pre-filler pattern (`playbooks/observatory-api.md` §6: "A `trigger-round`
issued before any filler exists fails instantly with `Temporal RoundWorkflow failed before settling
the round`"). Round 1 was created at `05:02:00.730415Z`; round 2 at `05:02:27.040927Z`, 26 s later.

**Proof the fillers were in force for rounds 2 and 3** — the registration read (elevated) and the
replays' own seat labels, not an inference from `log.md`:
```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}" | jq .
```
```json
{
  "filler_policy_versions": [
    { "policy_version_id": "49ce2430-abf2-45bb-98ff-443e35f00218",
      "policy_id": "69ab19c3-5043-4bee-9526-2b5749a89623",
      "policy_name": "cogmud-factor", "version": 1,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey", "display_name": null },
    { "policy_version_id": "4d6d9b09-6d81-4aa4-acab-67df0d3ae532",
      "policy_id": "2cf4c2ee-75c5-42ff-ad59-10fa6be189f3",
      "policy_name": "cogmud-magpie", "version": 1,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey", "display_name": null }
  ]
}
```
Both filler version ids differ from the champions' (`f3ef3f5a…`, `df2537fd…`). Round **2**'s replay
carries `results.names = ["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"]`
and round **3**'s the same (pasted under check 4) — the "Baseline (N)" renaming only happens for a
seat whose version is in the filler list, so the fillers were demonstrably registered before round 2
was seated.

Supporting (fetched 2026-08-24T05:40:00Z, after the checks above): a fourth round has since
completed —
```json
[{"n":4,"s":"completed"},{"n":3,"s":"completed"},{"n":2,"s":"completed"},{"n":1,"s":"failed"}]
```

**Status: TRUE** — rounds 2 and 3 (and later 4) completed, all created after the filler
registration; round 1 failed pre-filler and is excluded with its error recorded.

---

## 2. Both champions ranked, fillers absent/Baseline — **TRUE**

**Command** (fetched 2026-08-24T05:26:26Z):
```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" | jq .
```

**Response** (bare JSON list, as documented):
```json
[
  {
    "rank": 1,
    "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
    "player_name": "daveey",
    "score": 1030.5304984710244,
    "score_label": "Elo",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 2.0,
    "episodes_played": null,
    "win_rate": 1.0,
    "policy_label": "cogmud-merchant:v1",
    "recent_rounds": null
  },
  {
    "rank": 2,
    "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
    "player_name": "daveey-1",
    "score": 969.4695015289755,
    "score_label": "Elo",
    "score_value_type": "integer",
    "rounds_played": 2,
    "episode_wins": 0.0,
    "episodes_played": null,
    "win_rate": 0.0,
    "policy_label": "cogmud-broker:v1",
    "recent_rounds": null
  }
]
```

As TSV (the form `prompts/60-verify.md` asks for):

| rank | player_name | policy_label | score | rounds_played | episode_wins |
|---|---|---|---|---|---|
| 1 | daveey | cogmud-merchant:v1 | 1030.5304984710244 | 2 | 2.0 |
| 2 | daveey-1 | cogmud-broker:v1 | 969.4695015289755 | 2 | 0.0 |

**Status: TRUE** — `daveey` (`cogmud-merchant:v1`) and `daveey-1` (`cogmud-broker:v1`) are both
ranked, each with `rounds_played = 2 ≥ 1`. The list has exactly two rows: `cogmud-factor:v1` and
`cogmud-magpie:v1` are **absent** from the leaderboard, as required for fillers.

---

## 3. Latest round's episode request completed with a replay — **TRUE**

**Commands** (fetched 2026-08-24T05:26:33Z):
```bash
R=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
    | jq -r 'if type=="array" then . else .entries end
             | [.[]|select(.status=="completed")]|max_by(.round_number).id')
# R=round_578a4ce5-cc9d-45a0-93b6-6b8cc8eef912   (round_number 3)
curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)|map({id,status,replay_url})'
```
```json
[{"id":"ereq_1151194f-c9ea-4ce8-8d76-51f6b3af1d7b","status":"completed","replay_url":"https://softmax-public.s3.amazonaws.com/replays/632e1ef6-7d66-4ad6-afd7-67aa2e772f97.replay"}]
```

```bash
curl -sS "$BASE/episode-requests/ereq_1151194f-c9ea-4ce8-8d76-51f6b3af1d7b" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/632e1ef6-7d66-4ad6-afd7-67aa2e772f97.replay",
  "participants": [
    { "position": 0, "kind": "policy",
      "policy_version_id": "f3ef3f5a-4399-43da-8eba-d950ee5390a1",
      "policy_id": "c5c0f613-557c-4984-b8d9-b148d4600e17",
      "policy_name": "cogmud-merchant", "version": 1,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey", "is_filler": false },
    { "position": 1, "kind": "policy",
      "policy_version_id": "df2537fd-2ca7-4ea5-8ab0-a34dfa64daf2",
      "policy_id": "caf50053-2cb7-4e15-811d-15f8c71bce5c",
      "policy_name": "cogmud-broker", "version": 1,
      "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d",
      "player_name": "daveey-1", "is_filler": false },
    { "position": 2, "kind": "policy",
      "policy_version_id": "4d6d9b09-6d81-4aa4-acab-67df0d3ae532",
      "policy_name": "cogmud-magpie", "version": 1,
      "player_name": "daveey", "is_filler": true },
    { "position": 3, "kind": "policy",
      "policy_version_id": "49ce2430-abf2-45bb-98ff-443e35f00218",
      "policy_name": "cogmud-factor", "version": 1,
      "player_name": "daveey", "is_filler": true },
    { "position": 4, "kind": "policy",
      "policy_version_id": "4d6d9b09-6d81-4aa4-acab-67df0d3ae532",
      "policy_name": "cogmud-magpie", "version": 1,
      "player_name": "daveey", "is_filler": true },
    { "position": 5, "kind": "policy",
      "policy_version_id": "4d6d9b09-6d81-4aa4-acab-67df0d3ae532",
      "policy_name": "cogmud-magpie", "version": 1,
      "player_name": "daveey", "is_filler": true }
  ],
  "participant_scores": [
    { "position": 0, "score": 0.925 },
    { "position": 1, "score": 0.2 },
    { "position": 2, "score": 0.0 },
    { "position": 3, "score": 1.85 },
    { "position": 4, "score": 0.25 },
    { "position": 5, "score": 0.4 }
  ]
}
```
(Positions 2–5 abridged to the fields the check uses — `kind`, `policy_id` and `player_id` on those
four rows are omitted for length; nothing else was elided.)

**Status: TRUE** — `status == "completed"`; `replay_url` is non-null
(`…/replays/632e1ef6-7d66-4ad6-afd7-67aa2e772f97.replay`); seats 0 and 1 are
`daveey`/`cogmud-merchant:v1` and `daveey-1`/`cogmud-broker:v1` with `is_filler:false`; seats 2–5
are `is_filler:true` and render as `Baseline (N)` in the replay (check 4).

---

## 4. Replay bytes are valid and show the game — **TRUE**

**Commands** (fetched 2026-08-24T05:26:45Z):
```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/632e1ef6-7d66-4ad6-afd7-67aa2e772f97.replay" \
     -o /tmp/ep.replay        # http=200 bytes=49699
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
python3 -c "d=open('/tmp/ep.replay','rb').read(); d.decode('utf-8'); print('python strict utf-8 decode: ok, bytes=%d'%len(d))"
```
```
strict UTF-8 JSON: ok
python strict utf-8 decode: ok, bytes=49699
```
Two independent strict parsers (jq's, and CPython's non-surrogateescape `bytes.decode('utf-8')`)
both accept the bytes — no browser leniency involved.

```bash
jq -r '.protocol, .results.reason' /tmp/ep.replay
```
```
cogmud.replay.v1
complete
```

**Protocol reconciliation.** `.protocol` is `cogmud.replay.v1`. The manifest names two protocols
(`/workspace/cogame-cogmud/coworld_manifest_template.json` → `.game.protocols`): `player`, whose
text begins `cogmud.player.v1 - JSON text frames over the websocket…`, and `global`, which describes
the spectator/replay projection. `cogmud.replay.v1` is the replay-payload version the game writes —
`src/cogmud/server.nim:33` `const ReplayVersion = 1`, `:131` `"protocol": "cogmud.replay.v" &
$ReplayVersion` — and it is declared in the design note at `design.md:873` (`### Replay payload —
cogmud.replay.v1`, `:876` `{"protocol":"cogmud.replay.v1", …`). The viewer reads the same key
(`replay-viewer/cogmud_replay.nim:45`). `cogmud.player.v1` is the *player-socket* protocol and is
correctly not what a replay file stamps. **Match confirmed** against both the game source and the
design note; the manifest's `game.replay`, `game.viewer` and `game.artifacts` keys are `null`, so
the manifest carries no competing protocol string to contradict it.

**`results.reason` = `complete`** — the expected value. `design.md:333-344` (§"End conditions and
the legal `results.reason` values") declares exactly two legal values, `"complete"` ("the expected
value, and the one phase 60 should see") and `"deadline"`; no exception needed here.

```bash
jq -c '.results' /tmp/ep.replay
```
```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"],
 "scores":[0.925,0.2,0.0,1.85,0.25,0.4],"coin":[1,10,1,4,10,0],"wealth":[17,48,40,18,50,56],
 "questPoints":[20,0,0,32,0,0],"delivered":[3,0,0,4,0,0],"robberies":[0,0,0,0,1,1],
 "robbed":[0,0,0,1,1,0],"turns":14,"maxTurns":14,"reason":"complete"}
```

```bash
jq -c '[.events[]|.kind]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.replay
```
```json
{"act":84,"end":1,"start":1,"turn":15}
```
14 turns × 6 seats = 84 `act` events, one per seat per turn, plus `start`, 15 `turn` frames and
`end`. The `end` event: `{"kind":"end","turn":14,"text":"complete"}`.

**Fallback accounting — adapted to cogmud's schema.** The generic jq in `prompts/60-verify.md`
assumes `.type=="decision"` / `.fallback==true`; cogmud's replay language uses `kind:"act"` with a
`scripted` boolean (`true` when a baseline wrote the sentence — a scripted seat, or an LLM seat
whose two attempts both failed and fell back). Both forms are shown so the adaptation is auditable:
```bash
$ jq -r '[.events[]|select(.type=="decision")]|length' /tmp/ep.replay
0
$ jq -r '[.events[]|select(.fallback==true)]|length' /tmp/ep.replay
0
# ^ the prompt's generic filters find nothing because cogmud names them differently; the real counts:
$ jq -c '[.events[]|select(.kind=="act")]|group_by(.seat)
         |map({seat:.[0].seat,acts:length,scripted:([.[]|select(.scripted==true)]|length)})' /tmp/ep.replay
[{"seat":0,"acts":14,"scripted":0},{"seat":1,"acts":14,"scripted":1},
 {"seat":2,"acts":14,"scripted":14},{"seat":3,"acts":14,"scripted":14},
 {"seat":4,"acts":14,"scripted":14},{"seat":5,"acts":14,"scripted":14}]
$ jq -r '[.events[]|select(.kind=="act" and (.seat==0 or .seat==1))] as $c
         | "champion_decisions=\($c|length) champion_fallbacks=\([$c[]|select(.scripted==true)]|length)"' /tmp/ep.replay
champion_decisions=28 champion_fallbacks=1
```
Seats 0 (`daveey`) and 1 (`daveey-1`) are the champions: **1 fallback in 28 champion decisions
(3.6 %)** — a small minority, not "all fallbacks". Seats 2–5 are the fillers and are scripted 14/14
by construction, as fillers must be. The single champion fallback is turn 7, seat 1:
```json
{"kind":"act","turn":7,"seat":1,"order":0,"intent":"buy","room":3,"reason":"ok","salience":25,
 "scripted":true,"toRoom":3,"item":2,"qty":1,"npc":1,"coin":6,
 "sentence":"I buy 1 rope from Smith Bram.","text":"CRITICAL: I'm overweight (1 relic + 7 nails = 8 items in 8 slots). …"}
```

**Champion seats doing the thing the game is about** (a MUD of commissions, trade, speech and
theft). Distinct intents chosen by the two champion seats across the episode:
```bash
$ jq -r '[.events[]|select(.kind=="act" and (.seat==0 or .seat==1))|.intent]
         |group_by(.)|map({(.[0]):length})|add|tojson' /tmp/ep.replay
{"buy":6,"drop":2,"give":4,"move":9,"none":2,"quest":1,"sell":2,"take":2}
```
Verbatim non-scripted champion sentences (`turn seat intent reason scripted sentence [say]`):
```
0	0	quest	ok	false	I ask Smith Bram about my commissions.
0	1	take	ok	false	I pick up the relic.
1	0	buy	ok	false	I buy two rope from Smith Bram.
2	1	take	ok	false	I pick up the nails here in Market Square.  say="Looking for rope and nails to fill my commissions - I'll pay fair coin for either."
2	0	move	no_such_exit	false	I walk to The Copper Kettle.
4	1	sell	ok	false	I sell one nails to Smith Bram.  say="Nails going for three coin here, rope at eight - I am buying rope wherever it is cheap and selling dear."
6	1	drop	ok	false	I drop the relic here on the ground.  say="Relic here if anyone wants it - I need the space for rope and nails."
6	0	none	ambiguous_target	false	I hand Guildmaster Vell two rope and two salt for my commissions.
9	1	sell	ok	false	I sell five nails to Smith Bram.  say="Bram, I'm moving five nails at six coin each—that's thirty coin to you."
10	0	give	ok	false	I hand Guildmaster Vell two salt for my commission.
13	0	move	ok	false	I walk to The Guildhall.
```
Free-form English sentences, priced haggling spoken aloud, commissions actually delivered
(`delivered = [3,0,0,4,0,0]`, `questPoints[0] = 20`), and the parser's `ambiguous_target` /
`no_such_exit` outcomes fed back as legal no-ops exactly as `design.md:249` describes. This is the
game, played.

**Status: TRUE** — strict UTF-8 JSON under two parsers; `protocol == "cogmud.replay.v1"` matching
the game source and design note; `results.reason == "complete"`; champion fallbacks 1/28 (3.6 %),
with non-trivial non-scripted content.

---

## 5. Hosted game log is clean — **FALSE**

Summary: the round-3 episode's decoded log contains **one** line matching the forbidden pattern —
`cogmud llm: seat 1 falling back to scripted decision`. It is not one of the two exceptions
`prompts/60-verify.md` documents (`LLM provider is unavailable` = platform-wide Bedrock capacity;
`cut off at max_tokens` = raise `maxOutputTokens`), and `docs/SPEC.md:160-162` allows only "a
documented **platform-wide** cause checked against another LLM coworld". The cause here is local:
the model's reply for that seat was well-formed JSON followed by trailing content, so cogmud's Nim
parser rejected it twice. Marking this **FALSE** rather than excusing it.

### Attempt 1 — the pinned latest round (round 3), fetched 2026-08-24T05:26:58Z

```bash
curl -sS "$BASE/episode-requests/ereq_1151194f-c9ea-4ce8-8d76-51f6b3af1d7b/artifacts/logs" \
     "${AUTH[@]}" "${ELEV[@]}" -o logs.raw          # http=200 bytes=70297
# The body is python b'…' byte-string reprs under "===== container: <name> =====" headers —
# decoded with ast.literal_eval per repr BEFORE grepping (playbooks/observatory-api.md §10),
# because a line-based grep on the raw body undercounts.
python3 declogs.py logs.raw logs.decoded    # decode + grep -E 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected'
```
```
decoded_lines=270 hits=1
207:cogmud llm: seat 1 falling back to scripted decision
```
Containers present in the body:
```
===== container: coworld-init-config =====
===== container: bedrock-sidecar =====
===== container: game =====
===== container: worker =====
```

The matching line with its two preceding lines — the cause, verbatim:
```
205-cogmud llm: seat 1 attempt 0 failed: input(6, 1) Error: EOF expected
206-cogmud llm: seat 1 attempt 1 failed: input(2, 1) Error: EOF expected
207:cogmud llm: seat 1 falling back to scripted decision
```
Surrounding play, showing it was a single turn-8 event and play continued normally:
```
cogmud: turn 7 Widget: "I offer Tinker 1 lamp for 13 coins."
cogmud: turn 8 of 14 at 85s
cogmud llm: seat 1 attempt 0 failed: input(6, 1) Error: EOF expected
cogmud llm: seat 1 attempt 1 failed: input(2, 1) Error: EOF expected
cogmud llm: seat 1 falling back to scripted decision
cogmud: turn 8 Tinker: "I hand Guildmaster Vell one rope for my commission."
cogmud: turn 8 Bolt: "I buy 1 rope from Smith Bram."
```

**Diagnosis (from the pasted bytes, not inferred):** `Error: EOF expected` is Nim `parseJson`'s
error for **trailing content after a complete JSON value** — the model emitted the required
`{"action":…,"say":…,"notes":…}` object and then kept writing. It is not truncation
(`cut off at max_tokens` does not appear anywhere in the log — `hits=1`, and that hit is the
fallback line), and it is not a provider failure: every `bedrock_sidecar_complete` record in this
episode reports `"ok":true,"status_code":200` and there is no `LLM provider is unavailable` line.

**Not the "scripted-fast episode" symptom.** The episode ran the full 14 turns over ~157 s:
```
cogmud: turn 12 of 14 at 135s
cogmud: turn 13 of 14 at 152s
cogmud: turn 14 of 14 at 157s
…
cogmud: writing results and replay
cogmud: artifacts written; answering /healthz and /global for 20s before exit
cogmud: episode complete, shutting down
```

### Attempt 2 — different round (round 2, `ereq_c4466214-707f-4993-b1e4-6402cf8caf07`), fetched 2026-08-24T05:28:28Z

```bash
curl -sS "$BASE/episode-requests/ereq_c4466214-707f-4993-b1e4-6402cf8caf07/artifacts/logs" \
     "${AUTH[@]}" "${ELEV[@]}" -o logs_r2.raw       # http=200 bytes=66323
python3 declogs.py logs_r2.raw logs_r2.decoded
```
```
decoded_lines=258 hits=0
```
**CLEAN.** Turn cadence `turn 14 of 14 at 157s`.

### Attempt 3 — different round (round 4, `ereq_2fc0e53e-ddb5-4ec8-b047-f8ea01cb0d58`), fetched 2026-08-24T05:40:08Z

```bash
R4=round_e3d754d0-d3ec-43ec-836f-6e54c9b44488   # round_number 4, status completed at 05:40:00Z
E4=$(curl -sS "$BASE/episode-requests?round_id=$R4&limit=20" "${AUTH[@]}" \
     | jq -r '(if type=="array" then . else .entries end)|.[0].id')   # ereq_2fc0e53e-ddb5-4ec8-b047-f8ea01cb0d58
curl -sS "$BASE/episode-requests/$E4" "${AUTH[@]}" | jq -c '{status,replay_url}'
{"status":"completed","replay_url":"https://softmax-public.s3.amazonaws.com/replays/f2ecf3e4-dc96-43b5-b3e2-1768038352c2.replay"}
curl -sS "$BASE/episode-requests/$E4/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o logs_r4.raw   # http=200 bytes=122896
python3 declogs.py logs_r4.raw logs_r4.decoded
```
```
decoded_lines=366 hits=0
```
**CLEAN.** Round 4's replay is also `cogmud.replay.v1` / `reason:"complete"`, and its four
non-filler seats had **zero** scripted acts:
```json
["relh","daveey","daveey-1","richard","Baseline","Baseline (2)"]
[{"seat":0,"acts":14,"scripted":0},{"seat":1,"acts":14,"scripted":0},
 {"seat":2,"acts":14,"scripted":0},{"seat":3,"acts":14,"scripted":0},
 {"seat":4,"acts":14,"scripted":14},{"seat":5,"acts":14,"scripted":14}]
```

### Fleet cross-check (is this platform-wide?) — no

Latest completed episodes of three other LLM coworlds, same decode-then-grep, fetched
2026-08-24T05:29Z:

| coworld | episode request | hits | what matched |
|---|---|---|---|
| escrow | `ereq_c70b13d5-12d6-496c-8dcd-6ab8a4e14c41` | 2 | `escrow llm: seat 3 falling back to the trader baseline` (×2 seats) |
| escrow | `ereq_1195d7cd-9cae-4a52-ab8e-23230644f9ec` | 10 | same, ten times |
| bullwhip | `ereq_dde313e3-bfc7-4d6c-a050-b097941a7d42` | 4 | `bedrock_sidecar_rate_limited` ×2 and `us.anthropic.claude-haiku-4-5… unusable (throttled); falling back to …sonnet-4-6` ×2 |
| bullwhip | `ereq_c2914703-a2e8-4542-9d2e-809556adc926` | 0 | — |
| parley | `ereq_40223cda-5208-4786-94e9-bbd1a73807f4` | 0 | — |
| parley | `ereq_b030ca4c-f334-4255-8a34-c132219f90a1` | 44 | `bedrock_sidecar_rate_limited`, model-tier fallbacks, `parley llm: seat 0 falling back to scripted decision` |

Per-seat "falling back" lines are common across shipped LLM coworlds, and bullwhip/parley show a
genuine platform-wide symptom (Bedrock **throttling**, `bedrock_sidecar_rate_limited` +
model-tier fallback). **cogmud's line is not that.** cogmud's own sidecar records are all
`"ok":true,"status_code":200` with no rate-limit warning, and the two failures are the game's own
JSON parser rejecting the model's reply. So no documented platform-wide exception applies and I am
**not** excusing it.

**Status: FALSE** — 1 matching line in the pinned round-3 episode log
(`cogmud llm: seat 1 falling back to scripted decision`, caused by two consecutive replies with
trailing content after the JSON object → Nim `EOF expected`). Rounds 2 and 4 grep CLEAN, so the
defect is intermittent, cost 1 of 28 champion decisions in that episode, and did not stop the
episode completing all 14 turns. **Suggested fix for the coordinator (not applied — the verifier
does not edit code): make the reply parser tolerant of trailing prose (parse the first JSON object
in the reply, e.g. `parseJson` on the balanced-brace slice, or strip a ```json fence) rather than
requiring EOF after the object.** With that, this class of fallback disappears.

---

## 6. The public page uses the static replay path — **TRUE**

Three sources were tried; **which one produced the `src` is recorded below.**

**Source A — raw-HTML iframe grep** (fetched 2026-08-24T05:27:48Z):
```bash
curl -sS "https://softmax.com/cogmud" -o page.html      # http=200 bytes=457701
grep -o '<iframe[^>]*src="[^"]*"' page.html
```
```
(no match — page is client-rendered)
```
Per `prompts/60-verify.md` and `playbooks/observatory-api.md` §Featured match, an empty grep here is
*unknown*, not a failure: the page is client-rendered for the iframe, confirmed for every coworld
by the lighthouse run (2026-08-22).

**Source B — `/coworlds` detail API** (fetched 2026-08-24T05:27:48Z):
```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -c '(if type=="array" then . else .entries end)[]|select(.name=="cogmud")|{id,canonical,replay_viewer,featured_match}'
```
```json
{"id":"cow_42773bd0-0a21-4cca-94b2-41cd26b2d6ed","canonical":true,"replay_viewer":null,"featured_match":null}
```
`canonical: true` confirmed. `featured_match` is `null` — which the playbook records is `null`
**platform-wide** and therefore not evidence either way.

**Source C — the page's SSR payload, `state.playlist[0]` — THIS IS THE SOURCE USED for the
featured match** (parsed out of the same `page.html` fetched at 05:27:48Z):
```json
{
 "episodeId": "81ef8dff-5d03-48e4-adf2-c63c40924836",
 "coworldId": "cow_42773bd0-0a21-4cca-94b2-41cd26b2d6ed",
 "coworldName": "cogmud",
 "coworldVersion": "0.1.0",
 "replayUrl": "https://softmax-public.s3.amazonaws.com/replays/632e1ef6-7d66-4ad6-afd7-67aa2e772f97.replay",
 "finishedAt": "2026-08-24T05:22:05.869561Z",
 "roundNumber": 3,
 "episodeNumber": 1,
 "code": "cogmud.r3.e1",
 "matchup": {
  "divisionId": "div_711fc80a-6b0f-453c-9e31-a4816e7eefd8",
  "divisionName": "Competition",
  "first":  {"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
             "score":1030.5304984710244,"score_label":"Elo","rounds_played":2,"episode_wins":2,
             "win_rate":1,"policy_label":"cogmud-merchant:v1"},
  "second": {"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
             "score":969.4695015289755,"score_label":"Elo","rounds_played":2,"episode_wins":0,
             "win_rate":0,"policy_label":"cogmud-broker:v1"}
 },
 "inspectUrl": "/observatory/v2?tab=episode-requests&detail=episode-request:ereq_1151194f-c9ea-4ce8-8d76-51f6b3af1d7b",
 "outcome": "first"
}
```
**A featured match is present**, it is `cogmud.r3.e1`, and it is the *same* episode request and
replay verified in checks 3 and 4 (`ereq_1151194f…`, `…/632e1ef6-….replay`), with both champions in
the matchup.

**Source D — the iframe `src` itself — THIS IS THE SOURCE USED for the `src`.** The page's own JS
obtains it from the replay-session route (`playbooks/observatory-api.md` §Featured match), fetched
2026-08-24T05:27:57Z:
```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_42773bd0-0a21-4cca-94b2-41cd26b2d6ed",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/632e1ef6-7d66-4ad6-afd7-67aa2e772f97.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_42773bd0-0a21-4cca-94b2-41cd26b2d6ed/sha256%3A83f70a45599da40dd1afe2e20176a5d32d5c71fee7b655ab0abc38751cad01a7/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F632e1ef6-7d66-4ad6-afd7-67aa2e772f97.replay&v=2",
  "ready": true
}
```
```bash
curl -sSI "$SRC" | head -4
```
```
HTTP/2 200
date: Mon, 24 Aug 2026 05:27:59 GMT
content-type: text/html; charset=utf-8
content-length: 3441
```

Shape check, term by term:
- path is `/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` ✔
- `<cow_id>` = `cow_42773bd0-0a21-4cca-94b2-41cd26b2d6ed` = `STATE.coworld.cow_id` ✔
- `<sha>` = `sha256%3A83f70a45599da40dd1afe2e20176a5d32d5c71fee7b655ab0abc38751cad01a7`, i.e.
  URL-encoded `sha256:83f70a45599da40dd1afe2e20176a5d32d5c71fee7b655ab0abc38751cad01a7` =
  `STATE.coworld.manifest_sha` ✔ (the manifest hash, as the playbook requires — not the bundle digest)
- `?replay=` carries the S3 replay URL of the verified episode ✔
- `ready: true` and the path ends `/index.html` ⇒ **static delivery** ✔
- **no `/client/replay` anywhere in the URL** ✔ and the shell returns HTTP 200 ✔

**Status: TRUE** — featured match present (`cogmud.r3.e1`, both champions); iframe `src` is the
static route on the coworld id + manifest sha, never a `/client/replay` pod URL. Sources used:
**C** (SSR `state.playlist[0]`) for the featured match, **D** (`POST /coworlds/replays/session`) for
the `src`; A returned nothing (client-rendered) and B's `featured_match` is null platform-wide.

---

## 7. Certification declared the static bundle — **TRUE**

Source: the **committed** `runs/2026-08-24-cogmud/release-result.json` — phase 40's artifact copy of
release run `32691323905`. It was already present in the run directory, so **no re-download was
needed**; nothing was read from `/tmp`.

```bash
$ jq -r '.certify.replay_liveness' runs/2026-08-24-cogmud/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Surrounding context from the same file (`.certify`), showing the certification passed as a whole:
```bash
$ jq -c '{ok:.ok, certify_ok:.certify.ok, canonical:.canonical, version:.version,
          manifest_sha:.manifest_sha, cow_id:.cow_id, step_failed:.step_failed, errors:.errors}' \
     runs/2026-08-24-cogmud/release-result.json
```
```json
{"ok":true,"certify_ok":true,"canonical":true,"version":"0.1.0",
 "manifest_sha":"sha256:83f70a45599da40dd1afe2e20176a5d32d5c71fee7b655ab0abc38751cad01a7",
 "cow_id":"cow_42773bd0-0a21-4cca-94b2-41cd26b2d6ed","step_failed":null,"errors":[]}
```
and the transcript tail inside `.certify.output_tail`:
```
  [pass] replay-present: a replay artifact was produced
  [pass] replay-loadable: the replay artifact has a declared viewer path
  [pass] players-run: every declared player actually started on the smoke episode (not just declared)
  [pass] supporting-roles: declared supporting roles satisfy the currently implemented Executable checks
Certified dist/coworld_manifest.json
Transcript: coworld-executable (10 steps passed)
…
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

**Status: TRUE** — the string `Replay liveness: skipped (static replay bundle declared` is present,
read from the committed `runs/2026-08-24-cogmud/release-result.json`. The `manifest_sha` in that
file is byte-identical to the `<sha>` in check 6's iframe `src`, so the certified manifest and the
served viewer bundle are the same artifact.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

### (a) Dispatch

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_42773bd0-0a21-4cca-94b2-41cd26b2d6ed/sha256%3A83f70a45599da40dd1afe2e20176a5d32d5c71fee7b655ab0abc38751cad01a7/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F632e1ef6-7d66-4ad6-afd7-67aa2e772f97.replay&v=2'
# dispatch_at=2026-08-24T05:28:04Z
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
sleep 12
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status,event -L 10 \
 | jq -c 'sort_by(.createdAt)|reverse|.[0:3]'
```
```json
[{"createdAt":"2026-08-24T05:28:07Z","databaseId":32693641402,"event":"workflow_dispatch","status":"in_progress"},
 {"createdAt":"2026-08-24T05:03:59Z","databaseId":32692217118,"event":"workflow_dispatch","status":"completed"},
 {"createdAt":"2026-08-24T04:47:18Z","databaseId":32691300953,"event":"workflow_dispatch","status":"completed"}]
```
The run was identified **by `createdAt` after the dispatch** (`05:28:07Z` > `05:28:04Z`), not by
taking "the latest" blind; the two runs below it predate the dispatch and belong to other runs.

```bash
gh run watch 32693641402 -R Metta-AI/coworld-builder --exit-status; echo "exit=$?"
gh run view  32693641402 -R Metta-AI/coworld-builder --json status,conclusion,createdAt,url
```
```json
{"conclusion":"success","createdAt":"2026-08-24T05:28:07Z","status":"completed",
 "url":"https://github.com/Metta-AI/coworld-builder/actions/runs/32693641402"}
```
```bash
mkdir -p runs/2026-08-24-cogmud/viewer-check
gh run download 32693641402 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-24-cogmud/viewer-check
ls -l runs/2026-08-24-cogmud/viewer-check/
```
```
-rw-r--r-- 1 root root      0 Aug 24 05:29 smoke-stderr.txt
-rw-r--r-- 1 root root    585 Aug 24 05:29 smoke-stdout.txt
-rw-r--r-- 1 root root   1387 Aug 24 05:29 viewer-smoke.json
-rw-r--r-- 1 root root 347717 Aug 24 05:29 viewer-smoke.png
```
(`runs/2026-08-24-cogmud/viewer-check/` is written for the coordinator to commit — it is this run's
only rendered evidence and the CI sandbox that produced it is gone.)

### (b) Readouts, verbatim from `viewer-smoke.json`

```bash
$ jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-24-cogmud/viewer-check/viewer-smoke.json
{"loaded":true,"ms":1833,"clock":"TURN 1 / 14 · WAITING ON 6","scorebug":"daveey THE SMITHY 0.00 40C 0 items daveey-1 THE CHAPEL 0.00 40C 0 items Gasket THE COPPER KETTLE 0.00 40C 0 items Ratchet CUTPURSE ALLEY 0.00 40C 0 items Rivet THE DOCKS 0.00 40C 0 items Widget WAREHOUSE YARD 0.00 40C 0 items","feed_lines":235}
```
```bash
$ jq -c '.signals' runs/2026-08-24-cogmud/viewer-check/viewer-smoke.json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```
```bash
$ jq -r '.failure // "no failure"' runs/2026-08-24-cogmud/viewer-check/viewer-smoke.json
no failure
$ jq -c '{status, loading_text, console_tail}' runs/2026-08-24-cogmud/viewer-check/viewer-smoke.json
{"status":"REPLAY","loading_text":"LOADING REPLAY…","console_tail":["[bridge] loading","[bridge] ready"]}
```

**The three clock readouts** (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | clock text |
|---|---|
| 0 % | `TURN 1 / 14 · WAITING ON 6` |
| 50 % | `TURN 8 / 14 · WAITING ON 6` |
| 100 % | `FINAL · BASELINE (2) 1.85` |

All three **differ**. The shell exposes a `#scrub`; the json carries real readouts, not the
`"(no #scrub…)"` sentinel.

**Item-8 gate:** `loaded: true` ✔ (both signals independently: `data-replay-loaded="true"` on
`<html>` *and* the `coworld-replay` bridge reaching `ready`, with `bridge_error: []` and
`data_replay_error: null`), first frame at **1833 ms**, and the three clock readouts differ ✔.

### (c) The replay JSON the viewer was asked to draw — reconciliation

Ordered excerpts from `/tmp/ep.replay` (the same bytes verified in check 4):

*Early* (`turn seat intent reason scripted sentence`):
```
0	0	quest	ok	false	I ask Smith Bram about my commissions.
0	1	take	ok	false	I pick up the relic.
0	3	take	ok	true	I pick up the lamp.
0	2	move	ok	true	I wander over to Market Square.
0	4	move	ok	true	I wander over to Cutpurse Alley.
0	5	move	ok	true	I wander over to The Docks.
1	0	buy	ok	false	I buy two rope from Smith Bram.
1	4	rob	ok	true	I jump Ratchet here in the dark and take what he is carrying.
```
*Middle* (turns 6–7):
```
6	1	drop	ok	false	I drop the relic here on the ground.   say="Relic here if anyone wants it - I need the space for rope and nails."
6	2	trade	ok	true	I offer Bolt 1 nails for 9 coins.
6	5	trade	ok	true	I offer Tinker 1 lamp for 13 coins.
6	0	none	ambiguous_target	false	I hand Guildmaster Vell two rope and two salt for my commissions.
7	1	buy	ok	true	I buy 1 rope from Smith Bram.        ← the one champion fallback (check 5)
7	0	give	no_npc_here	false	I hand Guildmaster Vell one rope for my commission.
```
*Late*:
```
12	5	trade	ok	true	I offer Tinker 1 rope for 10 coins.
13	3	give	ok	true	I hand Guildmaster Vell 2 nails for my commission.
13	1	move	no_such_exit	false	I walk to The Guildhall.
13	0	move	ok	false	I walk to The Guildhall.
```
*Top-salience beats* (what the highlight reel should be built from):
```
100	1	4	rob	ok	I jump Ratchet here in the dark and take what he is carrying.
100	2	5	rob	ok	I jump Rivet here in the dark and take what he is carrying.
 90	4	3	give	ok	I hand Guildmaster Vell 2 rope for my commission.
 90	10	0	give	ok	I hand Guildmaster Vell two salt for my commission.
 90	13	3	give	ok	I hand Guildmaster Vell 2 nails for my commission.
 60	9	0	give	ok	I hand Guildmaster Vell one rope for my commission.
 45	5	1	buy	ok	I buy all 11 nails from Smith Bram.
 45	9	1	sell	ok	I sell five nails to Smith Bram.
```
*Results*:
```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"],
 "scores":[0.925,0.2,0.0,1.85,0.25,0.4],"coin":[1,10,1,4,10,0],"wealth":[17,48,40,18,50,56],
 "questPoints":[20,0,0,32,0,0],"delivered":[3,0,0,4,0,0],"robberies":[0,0,0,0,1,1],
 "robbed":[0,0,0,1,1,0],"turns":14,"maxTurns":14,"reason":"complete"}
```
(seat aliases in the recorded bytes: `.names = ["Tinker","Bolt","Gasket","Ratchet","Rivet","Widget"]`;
`.policyNames = ["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)","Baseline (4)"]`)

### Spectator judgment

`viewer-smoke.png` (1280×800, captured at the 100 % scrub position) shows a **complete, legible,
finished match** — this is not an empty canvas and not a frozen first frame.

Reading the picture top to bottom: a masthead **`COGMUD`** (the "MUD" in amber) with the clock
`FINAL · BASELINE (2) 1.85` centred and a `REPLAY` badge plus a `« LOG` toggle at the right; a
six-column **scorebug strip** — `daveey THE GUI… 0.93 1C 2 items` · `davee… THE S… 0.20 10C 5 items`
· `Gasket TANNER… 0.00 1C 5 items` · `Ratch… THE GUIL… 1.85 4C 1 item` · `Rivet THE SM… 0.25 10C
6 items` · `Widget TANNER… 0.40 0C 6 items`; a **town band** reading
`TURN 14/14 · 26 COIN IN PLAY · 7 COMMISSION UNITS FILLED · 2 ROBBERIES · 5 DEALS`; then the main
stage, a dark parchment **map of nine named rooms** (THE COPPER KETTLE, TANNER'S ROW, THE SMITHY,
THE GUILDHALL, WAREHOUSE YARD, THE CHAPEL, THE DOCKS, Cutpurse Alley, Market Square) laid out on a
grid, each room drawing its keeper's stall with stock/price lines (`Tanner Oda hide 3/2 salt 4/2`,
`Smith Bram nails 5/3 rope 7/4`, `Dockmaster Fen hide 4/2 nails 6/4 relic 13/8`,
`Guildmaster Vell rope 4/2 lamp 7/4`, `Keeper Nesh salt 9/5 rope 10/6 lamp 10/6`) and little
sprite figures with name tags for the cogs standing in it (`daveey` and `Ratchet` in THE GUILDHALL,
`daveey-1` and `Rivet` in THE SMITHY, `Gasket` and `Widget` in TANNER'S ROW). Over the centre sits
the **endcard**: `FINAL — 14 TURNS · 7 COMMISSION UNITS FILLED`, the headline
**`Ratchet WALKED OUT RICHEST`**, and a ranked table with columns COIN / PACK / POINTS / ROBBERIES /
SCORE. Below the stage, a **`SCORE BY TURN` momentum graph** with one line per seat rising across
14 turns, and at the bottom the **transport strip**: a play button, a scrubber rail with coloured
tick marks (amber for market/commission beats, green for robberies), the frame counter `101 / 101`,
and a row of **highlight-reel beat buttons** — `T2·ROB·Rivet`, `T3·ROB·Widget`,
`T5·COMMISSION·Ratchet`, `T11·COMMISSION·daveey`, `T14·COMMISSION·Ratchet`, `T10·COMMISSION·daveey`,
`T6·MARKET·daveey-1`, `T10·MARKET·daveey-1`.

**Does the picture agree with the record?** Every number reconciles against `results` above, with no
exceptions:

| endcard row | COIN | PACK | POINTS | ROB | SCORE | replay `results` |
|---|---|---|---|---|---|---|
| 1 Ratchet (seat 3) | 4 | 14 | 32 | 0 | 1.85 | coin 4, wealth 18 − coin 4 = 14, questPoints 32, robberies 0, score 1.85 ✔ |
| 2 daveey (seat 0) | 1 | 16 | 20 | 0 | 0.93 | coin 1, wealth 17 − 1 = 16, questPoints 20, robberies 0, score 0.925 ✔ |
| 3 Widget (seat 5) | 0 | 56 | 0 | 0 | 0.40 | coin 0, wealth 56 − 0 = 56, score 0.4 ✔ |
| 4 Rivet (seat 4) | 10 | 40 | 0 | 1 | 0.25 | coin 10, wealth 50 − 10 = 40, robberies 1, score 0.25 ✔ |
| 5 daveey-1 (seat 1) | 10 | 38 | 0 | 0 | 0.20 | coin 10, wealth 48 − 10 = 38, score 0.2 ✔ |
| 6 Gasket (seat 2) | 1 | 39 | 0 | 0 | 0.00 | coin 1, wealth 40 − 1 = 39, score 0.0 ✔ |

The town band likewise: `26 COIN IN PLAY` = Σ`coin` = 1+10+1+4+10+0 = 26 ✔;
`7 COMMISSION UNITS FILLED` = Σ`delivered` = 3+4 = 7 ✔; `2 ROBBERIES` = Σ`robberies` = 1+1 = 2 ✔.
The eight beat buttons are exactly the eight highest-salience `act` events listed above, in the
right turns and by the right seats (`T2·ROB·Rivet` = turn index 1, seat 4, salience 100;
`T6·MARKET·daveey-1` = turn 5, seat 1, "I buy all 11 nails from Smith Bram", salience 45; and so
on). And the clock's motion matches the record: `TURN 1 / 14` at 0 %, `TURN 8 / 14` at 50 % — the
midpoint of a 14-turn, 101-frame episode — and `FINAL` at 100 %. The scorebug at 0 % reads
`0.00 40C 0 items` for all six, the correct opening state, and by the final frame carries the six
scores above. **The viewer advances, and it is drawing this episode, not a placeholder.**

**Is it the starter's chrome?** Yes — this is unmistakably the bullwhip/paintbot/raid/hive lineage,
not a rewrite that merely shares element ids (the cogame-gridlock failure mode). All four lineage
marks are present and in their usual places: the **transport strip** with play control, frame
counter and salience-coloured scrubber rail; the **beat buttons** under the rail naming
turn·kind·actor; the **scorebug** as a single dense top strip, one column per seat, name + location
+ score + purse + pack; and the **endcard** overlay with a `WALKED OUT RICHEST` headline over a
ranked table — the same layout family as bullwhip's endcard, re-skinned to cogmud's parchment-MUD
palette with the game's own columns (COIN/PACK/POINTS/ROBBERIES). The `SCORE BY TURN` momentum graph
under the stage is the starter's momentum panel. Nothing was removed; the map stage is the
game-specific centre panel the starter leaves to each coworld.

**Legibility observation for the coordinator (not a check failure).** The `policyNames` swap is
applied **inconsistently across components**. The design note says the viewer "swaps the real names
in wherever a name is RENDERED". The clock does it (`FINAL · BASELINE (2) 1.85` for seat 3), but the
scorebug, the endcard table and the beat buttons render seats 2–5 by their *aliases* (`Gasket`,
`Ratchet`, `Rivet`, `Widget`) while rendering seats 0–1 by their swapped names (`daveey`,
`daveey-1`). The visible symptom is that the endcard crowns **`Ratchet WALKED OUT RICHEST`** while
the clock immediately above it says **`BASELINE (2)`** — the same seat under two names in one frame.
A spectator cannot tell that "Ratchet" is a baseline. This is cosmetic, does not affect the item-8
gate, and is a phase-30 item-14 style legibility finding worth carrying to LEARNINGS or a follow-up.
A second, smaller note: the scorebug truncates long names (`davee…`, `Ratch…`) and room names
(`THE GUI…`) at 1280 px width.

**Status: TRUE** — `loaded: true` at 1833 ms via both `data-replay-loaded="true"` and the
`coworld-replay` bridge `ready`, `failure: null`, `feed_lines: 235`, and the three scrub clock
readouts differ (`TURN 1 / 14` → `TURN 8 / 14` → `FINAL`). The rendered frame is legible, shows the
game, is the starter's chrome, and reconciles line-for-line with the replay JSON.

---

## Summary

| # | Check | Verdict | Key datum |
|---|---|---|---|
| 1 | ≥2 completed post-filler rounds | **TRUE** | rounds 2 & 3 `completed` (4 later too); round 1 `failed` pre-filler, excluded |
| 2 | Both champions ranked | **TRUE** | daveey r1 / daveey-1 r2, `rounds_played: 2` each; fillers absent |
| 3 | Latest round's episode request | **TRUE** | `ereq_1151194f…` `completed`, replay_url present, seats 0/1 = daveey / daveey-1 |
| 4 | Replay bytes valid & show the game | **TRUE** | strict JSON, `cogmud.replay.v1`, `reason:"complete"`, champion fallbacks 1/28 |
| 5 | Hosted game log clean | **FALSE** | 1 hit: `cogmud llm: seat 1 falling back to scripted decision` (JSON `EOF expected` ×2) |
| 6 | Public page uses static replay path | **TRUE** | `…/replays/static/cow_42773bd0…/sha256%3A83f70a…/index.html?replay=…`, `ready:true` |
| 7 | Certification declared static bundle | **TRUE** | `Replay liveness: skipped (static replay bundle declared; …)` |
| 8 | Viewer executed & judged | **TRUE** | `loaded:true` @1833 ms; clocks `TURN 1/14` → `TURN 8/14` → `FINAL` |

**Not-done items:** check 5 only. Retry budget for check 5 was spent (3 attempts: rounds 3, 2, 4;
plus a fleet cross-check against escrow/bullwhip/parley to test for a platform-wide cause — there
is none for cogmud's line). The verifier does not fix code; the fix suggestion is under check 5.
