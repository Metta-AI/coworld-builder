# VERIFY — escrow   (2026-08-23T16:40Z)

Verdict: **2 items false** — checks 4 and 5 are FALSE. Checks 1, 2, 3, 6, 7, 8 are TRUE.

Both false items have the **same single root cause**: the two LLM champion policies
(`escrow-drafter:v1`, `escrow-swapper:v1`) emit *illegal* contract runes on roughly half their
turns, the game's legality checker rejects both attempts, and the server falls back to the
scripted trader baseline for that seat. This is a coworld-level prompt/DSL defect, **not** a
platform LLM-capacity symptom — see §5 for the cross-check against two other LLM coworlds whose
latest hosted logs are clean.

Constants used throughout:

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")   # values never printed
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_cc074076-5938-403e-81db-d278c031db6d
D=div_a8171f6e-62bd-41e5-b470-f15d675faee9
COW=cow_65c18d00-ccaf-4259-bcaa-9046e7072ca9
```

**Evaluation target.** The ladder produces a round every 15 minutes, so "the latest completed
round" is a moving target. Every check below that names a round uses **round 4**
(`round_c0c234c2-eb3f-4ab5-9cf5-894f1a4f8127`, completed `2026-08-23T16:32:36Z`), the latest
completed round at the time of the fetches recorded here (16:33Z–16:40Z). All evidence was
fetched fresh in this phase-60 session; nothing is reused from an earlier phase except
`release-result.json` for check 7, which `prompts/60-verify.md` §7 explicitly designates.

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r '[.entries[]|select(.status=="completed")]|length'
```

```
3
```

Full listing (fetched `2026-08-23T16:33:17Z`, trimmed to the fields used;
`/rounds` returns `{entries:[…]}` on this deployment):

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq '{entries:[.entries[]|{id,round_number,status,error,created_at,completed_at,
        entrant_policy_version_ids:.round_config.entrant_policy_version_ids}]}'
```

```json
{
  "entries": [
    {
      "id": "round_c0c234c2-eb3f-4ab5-9cf5-894f1a4f8127",
      "round_number": 4,
      "status": "completed",
      "error": null,
      "created_at": "2026-08-23T16:28:42.651720Z",
      "completed_at": "2026-08-23T16:32:36.295744Z",
      "entrant_policy_version_ids": [
        "6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d",
        "ae792ad8-75d3-4eb6-aea3-4dfa8548907a"
      ]
    },
    {
      "id": "round_89c1c03d-3d38-464f-9412-3bddaad639f4",
      "round_number": 3,
      "status": "completed",
      "error": null,
      "created_at": "2026-08-23T16:13:42.285154Z",
      "completed_at": "2026-08-23T16:17:29.643123Z",
      "entrant_policy_version_ids": [
        "6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d",
        "ae792ad8-75d3-4eb6-aea3-4dfa8548907a"
      ]
    },
    {
      "id": "round_13be4cf0-ad75-4954-9514-98480c6f8d07",
      "round_number": 2,
      "status": "completed",
      "error": null,
      "created_at": "2026-08-23T15:58:41.705932Z",
      "completed_at": "2026-08-23T16:02:06.236563Z",
      "entrant_policy_version_ids": [
        "6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d",
        "ae792ad8-75d3-4eb6-aea3-4dfa8548907a"
      ]
    },
    {
      "id": "round_b8f582ac-cc01-44cc-9cd9-49b0c65e108c",
      "round_number": 1,
      "status": "failed",
      "error": "Temporal RoundWorkflow failed before settling the round.",
      "created_at": "2026-08-23T15:58:00.403567Z",
      "completed_at": "2026-08-23T15:58:00.612338Z",
      "entrant_policy_version_ids": [
        "6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d"
      ]
    }
  ]
}
```

**Round 1's `error`, verbatim** (does not count toward the ≥2):

> `Temporal RoundWorkflow failed before settling the round.`

That is the exact signature `playbooks/observatory-api.md` §6 documents for a `trigger-round`
issued before any filler exists. Round 1 auto-fired at settings time (15:58:00Z) with a single
entrant — champion #1 only (`6eb9292a…`); champion #2 had not yet been submitted and no filler
policy was registered. `log.md` records the filler registration
(`50 filler-policies 200: trader + hoarder registered, neither champion`) in the phase-50 block.

Independent, non-log proof that the fillers were in force for rounds 2, 3 and 4 — the replay
bytes for each round carry the platform-assigned spectator names, and the two filler seats are
renamed `Baseline` / `Baseline (2)`, which only happens for a policy version present in the
league's filler list:

```bash
jq -c '.policyNames' /tmp/ep.replay      # round 4 replay, fetched fresh in §4
```

```json
["daveey","daveey-1","Baseline","Baseline (2)"]
```

Status: **TRUE** — 3 completed rounds (`round_number` 2, 3, 4), all with `round_number ≥ 2`, i.e.
all after the round in which the fillers were registered. Round 1 is `failed` and excluded, with
its error quoted above.

---

## 2. Both champions ranked, fillers absent/Baseline — **TRUE**

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```

Response shape observed: a **bare JSON array** (`jq -r 'type'` → `array`), as
`playbooks/observatory-api.md` §11 says.

```
1	daveey	escrow-drafter:v1	1043.747133633611	3	3.0
2	daveey-1	escrow-swapper:v1	956.2528663663891	3	0.0
```

Full body:

```json
[
  {"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
   "score":1043.747133633611,"score_label":"Elo","score_value_type":"integer",
   "rounds_played":3,"episode_wins":3.0,"episodes_played":null,"win_rate":1.0,
   "policy_label":"escrow-drafter:v1","recent_rounds":null},
  {"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
   "score":956.2528663663891,"score_label":"Elo","score_value_type":"integer",
   "rounds_played":3,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,
   "policy_label":"escrow-swapper:v1","recent_rounds":null}
]
```

Status: **TRUE** — `daveey` (rank 1, `escrow-drafter:v1`, `rounds_played` 3) and `daveey-1`
(rank 2, `escrow-swapper:v1`, `rounds_played` 3) both present, each `rounds_played ≥ 1`. The two
filler policies (`escrow-trader:v1`, `escrow-hoarder:v1`) are **absent** from the leaderboard —
the stronger of the two permitted outcomes.

---

## 3. Latest round's episode request completed with a replay — **TRUE**

```bash
R=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
    | jq -r '[.entries[]|select(.status=="completed")]|max_by(.round_number).id')
# R=round_c0c234c2-eb3f-4ab5-9cf5-894f1a4f8127
EREQ=$(curl -sS "$BASE/episode-requests?round_id=$R&limit=20" "${AUTH[@]}" | jq -r '.entries[0].id')
# EREQ=ereq_52e240bb-5356-478b-9240-5505de228f4a
curl -sS "$BASE/episode-requests/$EREQ" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```

```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/f17e146a-7e0d-4d30-85eb-645120b855fc.replay",
  "participants": [
    {"position":0,"kind":"policy","policy_name":"escrow-drafter","version":1,
     "policy_version_id":"6eb9292a-1189-4f4d-b5ae-191c4b0e1d9d",
     "player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","is_filler":false},
    {"position":1,"kind":"policy","policy_name":"escrow-swapper","version":1,
     "policy_version_id":"ae792ad8-75d3-4eb6-aea3-4dfa8548907a",
     "player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","is_filler":false},
    {"position":2,"kind":"policy","policy_name":"escrow-hoarder","version":1,
     "policy_version_id":"b07b36d6-c4aa-4dce-b5af-a3dc0f7a6016",
     "player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","is_filler":true},
    {"position":3,"kind":"policy","policy_name":"escrow-trader","version":1,
     "policy_version_id":"0505950f-bd65-46d4-ac4a-b3d0ad40c11b",
     "player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","is_filler":true}
  ],
  "participant_scores": [
    {"position":0,"score":224.0},
    {"position":1,"score":110.0},
    {"position":2,"score":110.0},
    {"position":3,"score":110.0}
  ]
}
```

`?round_id=` works; `?division_id=` was not attempted (playbook records it 500s). List key is
`entries`, matching the playbook.

**Deviation from the checklist's expected wording, recorded rather than glossed:** the
`participants` rows on this deployment carry the *real* policy names plus an `is_filler` boolean,
not the literal display string `Baseline (N)`. The `Baseline` / `Baseline (2)` renaming appears in
the replay bytes (`.policyNames`, §1 above) and in `results.names` (§4). The substantive
requirement — champions named `daveey` and `daveey-1`, fillers distinguishable — is satisfied by
`is_filler: false` on positions 0/1 and `is_filler: true` on positions 2/3.

Status: **TRUE** — `status == "completed"`, non-null `replay_url`,
`participants` names `daveey` (position 0) and `daveey-1` (position 1) as non-fillers.

---

## 4. Replay bytes are valid and show the game — **FALSE**

Sub-criteria: strict-JSON ✅, protocol ✅, `results.reason` ✅, **fallback share ❌**.

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/f17e146a-7e0d-4d30-85eb-645120b855fc.replay" -o /tmp/ep.replay
```
```
http=200 bytes=49178
```

```bash
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
```
```
strict UTF-8 JSON: ok
```

```bash
jq -r 'keys_unsorted|@csv' /tmp/ep.replay
jq -r '.protocol, .results.reason' /tmp/ep.replay
```
```
"protocol","names","policyNames","config","events","results"
escrow.replay.v1
complete
```

`escrow.replay.v1` is exactly the protocol string the design note declares
(`runs/2026-08-23-escrow/design.md` line 470: "``escrow.replay.v1``"). `results.reason` is
`complete`, the preferred value; no `deadline` exception is needed.

**Field-name check before judging** (the checklist's `.type` / `.tick` / `decision` names do not
exist in this game's replay — I verified rather than assumed):

```bash
jq -r '(.events|map(has("type"))|any), (.events|map(has("tick"))|any),
       (.events|map(has("kind"))|all), (.events|map(has("turn"))|all)' /tmp/ep.replay
```
```
false
false
true
false
```

So: events are keyed `kind`, not `type`; the clock field is `turn`, not `tick`; `turn` is absent
on the `start` event only. Event census:

```bash
jq -r '[.events[]|.kind]|group_by(.)|map("\(.[0])=\(length)")|join(" ")' /tmp/ep.replay
```
```
end=1 expire=16 fill=39 move=64 offer=17 settle=1 sign=1 start=1 turn=16
```

Decisions and fallbacks, using this game's names (`move` events; a fallback is `scripted == true`):

```bash
jq -r '[.events[]|select(.kind=="move")]|length' /tmp/ep.replay                       # all decisions
jq -r '[.events[]|select(.kind=="move" and .scripted==true)]|length' /tmp/ep.replay   # all fallbacks
jq -r '[.events[]|select(.kind=="move" and (.seat==0 or .seat==1))]
       |{decisions:length,fallbacks:([.[]|select(.scripted==true)]|length)}' /tmp/ep.replay
```
```
64
51
{
  "decisions": 32,
  "fallbacks": 19
}
```

Per seat:

```bash
jq -r '[.events[]|select(.kind=="move")]|group_by(.seat)
       |map({seat:.[0].seat,total:length,scripted:([.[]|select(.scripted==true)]|length)})' /tmp/ep.replay
```
```json
[
  {"seat": 0, "total": 16, "scripted": 12},
  {"seat": 1, "total": 16, "scripted": 7},
  {"seat": 2, "total": 16, "scripted": 16},
  {"seat": 3, "total": 16, "scripted": 16}
]
```

Seats 2 and 3 are the scripted baselines — `16/16 scripted` is correct and expected for them.
Seats 0 and 1 are the **champions**: seat 0 (`daveey` / `escrow-drafter:v1`) is scripted on
**12 of 16** turns (75 %) and seat 1 (`daveey-1` / `escrow-swapper:v1`) on **7 of 16** (44 %).
Combined, **19 of 32 champion decisions (59 %) are fallbacks.** The checklist requires the
fallback count to be "a small minority of decisions". A 59 % majority is not.

This is not a one-round artefact. Retry attempts (see §Retry log) measured the same statistic on
the other two completed rounds:

| Round | ereq | seat 0 scripted | seat 1 scripted | champion fallback share |
|---|---|---|---|---|
| 2 | `ereq_c5429b47-7440-4496-ab19-96c7dfa7683f` | 11/16 | 7/16 | 18/32 = 56 % |
| 3 | `ereq_883156db-5ea2-4b64-a3a5-2f593b680f58` | 8/16  | 7/16 | 15/32 = 47 % |
| 4 | `ereq_52e240bb-5356-478b-9240-5505de228f4a` | 12/16 | 7/16 | 19/32 = 59 % |

Sample of a genuine (non-scripted) champion decision, showing the content *is* non-trivial when
the LLM does produce a legal move — the defect is legality, not emptiness:

```bash
jq -c '[.events[]|select(.kind=="move" and .scripted==false)][0]' /tmp/ep.replay
```
```json
{"kind":"move","turn":0,"seat":0,"scripted":false,
 "say":"Looking to buy ore, grain, timber at 2-2.5 hearts per unit. My commission needs 2 each per turn.",
 "text":"Turn 0: …"}
```

Status: **FALSE** — valid strict-UTF-8 JSON ✅, `protocol == "escrow.replay.v1"` matches the
manifest/design ✅, `results.reason == "complete"` ✅, but the champion seats' fallback rate
(19/32 = 59 %; 12/16 on seat 0) is a **majority**, not "a small minority", so the "champion seats'
decisions are non-scripted" criterion fails. No documented exception covers this: the design note
declares only `complete` and `deadline` as `results.reason` exceptions
(`design.md` line 629: "``reason`` documented as ``complete | deadline``") and says nothing that
licenses a majority-fallback episode; §Degrade-never-hang (design.md line 668) treats the scripted
fallback as a *degradation* path, not the normal path.

---

## 5. Hosted game log is clean — **FALSE**

```bash
curl -sS "$BASE/episode-requests/ereq_52e240bb-5356-478b-9240-5505de228f4a/artifacts/logs" \
  "${AUTH[@]}" "${ELEV[@]}" \
 | grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' || echo CLEAN
```
```
http=200 bytes=124009
```

Note on decoding: this endpoint returns the container logs as Python `b'…'` repr blocks
(`===== container: <name> =====` headers), so a naive `grep -c` counts one line. I decoded the
blocks to plain text first and grepped that; occurrence counts below are `grep -o … | wc -l`.

Per-pattern occurrence counts on the decoded log:

```
falling back                   19
LLM provider is unavailable    0
cut off at max_tokens          0
rejected                       0
```

The 19 matching lines (line numbers in the decoded log):

```
257:escrow llm: seat 0 falling back to the trader baseline
267:escrow llm: seat 0 falling back to the trader baseline
268:escrow llm: seat 1 falling back to the trader baseline
277:escrow llm: seat 0 falling back to the trader baseline
287:escrow llm: seat 0 falling back to the trader baseline
288:escrow llm: seat 1 falling back to the trader baseline
297:escrow llm: seat 0 falling back to the trader baseline
306:escrow llm: seat 0 falling back to the trader baseline
316:escrow llm: seat 0 falling back to the trader baseline
317:escrow llm: seat 1 falling back to the trader baseline
325:escrow llm: seat 0 falling back to the trader baseline
335:escrow llm: seat 0 falling back to the trader baseline
336:escrow llm: seat 1 falling back to the trader baseline
344:escrow llm: seat 0 falling back to the trader baseline
354:escrow llm: seat 0 falling back to the trader baseline
355:escrow llm: seat 1 falling back to the trader baseline
368:escrow llm: seat 1 falling back to the trader baseline
384:escrow llm: seat 0 falling back to the trader baseline
385:escrow llm: seat 1 falling back to the trader baseline
```

Context, verbatim, lines 248–272 of the decoded log — this is the *cause*, and it is a legality
rejection, not a provider problem:

```
escrow: episode timeout 1200s (assumed); playing until 720s, at most 125s per turn
escrow: turn 0 of 16 at 7s
escrow: turn 0 Ratchet (Factor) gives 0 signs 0 says "Looking to buy ore, grain, timber at 2-2.5 hearts per unit. My commission needs 2 each per turn." at 15s
escrow: turn 0 Widget (Mason) gives 0 signs 0 offers says "4 ore for 4 grain, first come" at 15s
escrow: turn 0 Sprocket (Farmer) gives 0 signs 0 at 15s
escrow: turn 0 Piston (Forester) gives 0 signs 0 offers at 15s
escrow: turn 1 of 16 at 15s
escrow llm: seat 0 attempt 0 failed: unfunded: you hold 3 free ORE but LOCK 4
escrow llm: seat 0 attempt 1 failed: unfunded: you hold 3 free ORE but LOCK 4
escrow llm: seat 0 falling back to the trader baseline
escrow: turn 1 Ratchet (Factor) gives 0 signs 0 at 25s
escrow: turn 1 Widget (Mason) gives 0 signs 1 offers says "4 ore for 4 grain, fair price, let's keep the floor moving" at 25s
escrow: turn 1 Sprocket (Farmer) gives 0 signs 0 at 25s
escrow: turn 1 Piston (Forester) gives 0 signs 0 at 25s
escrow: turn 2 of 16 at 26s
escrow llm: seat 0 attempt 0 failed: unfunded: you hold 3 free ORE but LOCK 4
escrow llm: seat 1 attempt 0 failed: C3 is not addressed to you
escrow llm: seat 0 attempt 1 failed: unfunded: you hold 3 free ORE but LOCK 4
escrow llm: seat 1 attempt 1 failed: C3 is not addressed to you
escrow llm: seat 0 falling back to the trader baseline
escrow llm: seat 1 falling back to the trader baseline
escrow: turn 2 Ratchet (Factor) gives 0 signs 0 at 37s
escrow: turn 2 Widget (Mason) gives 0 signs 0 at 37s
escrow: turn 2 Sprocket (Farmer) gives 0 signs 0 at 37s
escrow: turn 2 Piston (Forester) gives 0 signs 0 offers at 37s
```

Distribution of the underlying rejection reasons (digits normalised to `N` for grouping):

```bash
grep -oE 'attempt [01] failed: [^\\]*' <decoded log> | sed 's/[0-9]\+/N/g' | sort | uniq -c | sort -rn
```
```
     18 attempt N failed: CN is not addressed to you
     14 attempt N failed: unfunded: you hold N free ORE but LOCK N
      3 attempt N failed: you cannot pay the ASK of CN
      3 attempt N failed: input(N, N) Error: EOF expected
      2 attempt N failed: unfunded: you hold N free GRAIN but LOCK N
      1 attempt N failed: unfunded: you cannot lock N ORE + N TIMBER after this turn
      1 attempt N failed: bad_condition: IF must be ALWAYS, [NOT] HOLDS <cog> <n> <good>, or [NOT] PAID <cog> <n> <good>, naming a cog at this table
```

Every rejection is an in-game legality error produced by the model's own rune text: signing a
contract addressed to someone else, LOCKing goods it does not hold free, offering an ASK it
cannot pay, a malformed `IF` condition, and a rune that does not parse (`EOF expected`).

**No documented exception applies.** `prompts/60-verify.md` §5 permits waiving only
`LLM provider is unavailable` (a platform-wide Bedrock capacity symptom). That string occurs
**zero** times here, and the cross-check against two other LLM coworlds' latest completed episodes,
fetched in this session, shows the platform is healthy:

```bash
for C in contagion raid; do  # latest completed ereq per coworld, same AUTH+ELEV
  curl -sS "$BASE/episode-requests/$EREQ_C/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" | grep -c …
done
```
```
contagion latest completed ereq=ereq_98178b75-7c7d-4498-81b7-bef96812486d   http=200 bytes=97802
  falling back                   0
  LLM provider is unavailable    0
  cut off at max_tokens          0
raid latest completed ereq=ereq_b38a3ddd-6c13-4353-b7cd-5373de83b137        http=200 bytes=109853
  falling back                   0
  LLM provider is unavailable    0
  cut off at max_tokens          0
```

`cut off at max_tokens` is also absent, so the `maxOutputTokens` remedy in §5 is not the fix
either. The fix is on the escrow side: the player prompt must constrain the rune it emits
(free-stock accounting before `LOCK`, only sign contracts addressed to you, the exact `IF` grammar).

Status: **FALSE** — 19 `falling back` occurrences in the latest round's hosted log (15 in round 3,
18 in round 2), caused by escrow-specific rune legality rejections. Not `CLEAN`, and not
excusable under the platform-wide-LLM clause.

---

## 6. The public page uses the static replay path — **TRUE**

**Source A — raw HTML grep (as the checklist's first command):**

```bash
curl -sS "https://softmax.com/escrow" | grep -o '<iframe[^>]*src="[^"]*"'
```
```
http=200 bytes=389505
(no output)
```

Per `prompts/60-verify.md` §6 and `playbooks/observatory-api.md` §Featured match, an empty grep is
**unknown, not a failure**: the page is client-rendered for the iframe. Falling back.

**Source B — `/coworlds` detail (the checklist's documented fallback):**

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)[]|select(.name=="escrow")
          |{id,name,version,canonical,replay_viewer,featured_match}'
```
```json
{
  "id": "cow_65c18d00-ccaf-4259-bcaa-9046e7072ca9",
  "name": "escrow",
  "version": "0.1.0",
  "canonical": true,
  "replay_viewer": null,
  "featured_match": null
}
```

Shape note: on this deployment **`/coworlds` returns a bare array**, not `{entries:…}` — the
playbook's `.entries[]` form errors with `Cannot index array with string "entries"`. Recorded.
`featured_match: null` is the platform-wide behaviour the playbook already documents (lighthouse,
2026-08-22), so it is not evidence either way.

**Source C — the page's SSR payload `state.playlist[0]`, which *is* the featured match** (this is
the source I relied on):

```bash
curl -sS "https://softmax.com/escrow" -o page.html      # http=200, 389505 bytes
python3 -c '…find("\"playlist\":[")…'                    # un-escape and print
```
```json
"playlist":[{"episodeId":"1bfff478-1b1a-4610-b89d-f5ecab7ab0b6",
"coworldId":"cow_65c18d00-ccaf-4259-bcaa-9046e7072ca9","coworldName":"escrow",
"coworldVersion":"0.1.0",
"replayUrl":"https://softmax-public.s3.amazonaws.com/replays/f17e146a-7e0d-4d30-85eb-645120b855fc.replay",
"finishedAt":"2026-08-23T16:32:29.781814Z","roundNumber":4,"episodeNumber":1,
"code":"escrow.r4.e1","matchup":{"divisionId":"div_a8171f6e-62bd-41e5-b470-f15d675faee9",
"divisionName":"Competition","first":{"rank":1,
"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"dave…
```

A featured match **is** present: `escrow.r4.e1`, both ranked players in `matchup.first` /
`matchup.second`, pointing at round 4's replay.

**Source D — the iframe `src` itself**, from the call the page's own JS makes:

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_65c18d00-ccaf-4259-bcaa-9046e7072ca9",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/f17e146a-7e0d-4d30-85eb-645120b855fc.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_65c18d00-ccaf-4259-bcaa-9046e7072ca9/sha256%3A0e1cafeeef02b17a8f100c51b972d19696241efc612b511430c3cabe0264bef3/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Ff17e146a-7e0d-4d30-85eb-645120b855fc.replay&v=2",
  "ready": true
}
```

The path is `…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`, with `<sha>`
= the coworld's manifest hash `sha256:0e1cafeeef02b17a8f100c51b972d19696241efc612b511430c3cabe0264bef3`
(URL-encoded), matching `STATE.coworld.manifest_sha`. `ready: true`. There is **no**
`/client/replay` pod URL anywhere in the response.

Status: **TRUE** — sources used: **C** (SSR `state.playlist[0]`, for the featured match) and **D**
(`POST /coworlds/replays/session`, for the iframe `src`); A found nothing (client-rendered) and B's
`featured_match` is null platform-wide. Static route confirmed, featured match present.

---

## 7. Certification declared the static bundle — **TRUE**

Source: the **committed** `runs/2026-08-23-escrow/release-result.json` (phase 40's downloaded
artifact, already present in the working tree — no re-download from `gh run download` was needed,
and `/tmp` was not consulted).

```bash
jq -r '.certify.replay_liveness' runs/2026-08-23-escrow/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

That string contains `Replay liveness: skipped (static replay bundle declared`, as required.
Corroborating tail from the same file (`.certify.output_tail`, excerpt):

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

Status: **TRUE** — read from the committed `runs/2026-08-23-escrow/release-result.json`
(release run `32649696984`, repo `Metta-AI/cogame-escrow`).

---

## 8. Spectator judgment — **TRUE**

*(a) The viewer was **executed** in a real browser via CI.*

```bash
SRC='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_65c18d00-ccaf-4259-bcaa-9046e7072ca9/sha256%3A0e1cafeeef02b17a8f100c51b972d19696241efc612b511430c3cabe0264bef3/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Ff17e146a-7e0d-4d30-85eb-645120b855fc.replay&v=2'
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
```

Dispatched at `2026-08-23T16:34:01Z`. Run found by created-after-dispatch, **not** by taking the
bare latest:

```
32652062253	2026-08-23T16:34:03Z	in_progress
32651276492	2026-08-23T16:18:53Z	completed      <- an earlier run of mine, on round 3's replay
```

```bash
gh run view 32652062253 -R Metta-AI/coworld-builder --json status,conclusion
```
```
completed	success
```

Artifact downloaded to `runs/2026-08-23-escrow/viewer-check/`
(`viewer-smoke.json`, `viewer-smoke.png`, `smoke-stdout.txt`, `smoke-stderr.txt` [0 bytes]).

*(b) The readouts, verbatim.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-23-escrow/viewer-check/viewer-smoke.json
```
```
{"loaded":true,"ms":4011,"clock":"TURN 0","scorebug":"","feed_lines":0}
```

```bash
jq -c '.signals' runs/2026-08-23-escrow/viewer-check/viewer-smoke.json
```
```
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/2026-08-23-escrow/viewer-check/viewer-smoke.json
```
```
no failure
```

The three scrub clock readouts:

| scrub position | clock readout |
|---|---|
| 0 %   | `TURN 0` |
| 50 %  | `TURN 0 / 16 · WAITING ON 4` |
| 100 % | `TURN 16 / 16 · FINAL` |

Console tail from the same artifact: `["[bridge] loading", "[bridge] ready"]`.

**Corroborating second execution** (run `32651276492`, dispatched 16:18:51Z against round 3's
replay; artifact kept at `runs/2026-08-23-escrow/viewer-check/round3-32651276492/`):

```
{"loaded":true,"ms":2033,"clock":"TURN 0","scorebug":"","feed_lines":0}
scrub readouts: 0%="TURN 0"  50%="TURN 8 / 16 · WAITING ON 4"  100%="TURN 16 / 16 · FINAL"
```

Both criteria hold. `loaded: true` in both runs, with `data-replay-loaded="true"` **and** the
`coworld-replay` bridge's `ready`. The three readouts differ in both runs; in the round-3 run the
midpoint reads `TURN 8 / 16`, i.e. the clock genuinely advances through the middle of the episode.
In the round-4 run the 50 % probe read `TURN 0 / 16 · WAITING ON 4` — the frame text had not caught
up at the moment of sampling (that run's first paint took `4011 ms` vs `2033 ms`), but the label
still changed from `TURN 0` to the full `TURN n / 16 · WAITING ON 4` form and then to
`TURN 16 / 16 · FINAL`, and the screenshot below is a fully-drawn final frame.

*(c) The static bundle's assets — fetched independently of the browser run, as a cross-check.*
(`prompts/60-verify.md` §8 makes the browser run the primary instrument; this table is
supplementary, not the basis for the verdict.)

| URL (relative to `…/static/<cow_id>/<sha>/`) | HTTP | bytes |
|---|---|---|
| `index.html` | 200 | 1507 |
| `chrome.css` (from `<link rel="stylesheet" href="./chrome.css">`) | 200 | 12687 |
| `renderer.js` (from `<script src="./renderer.js">`) | 200 | 52196 |
| `escrow_replay.js` (from `<script src="./escrow_replay.js">`) | 200 | 11403 |
| `static_replay.js` (from `<script src="./static_replay.js">`) | 200 | 6591 |
| `escrow_replay.wasm` (named in the emscripten loader) | 200 | 198110 (`content-type: application/wasm`; `file` → `WebAssembly (wasm) binary module version 0x1 (MVP)`) |

All 200, all non-trivial. Bridge markers grepped out of the fetched `static_replay.js`:

```bash
grep -onE 'coworld-replay|tell\("ready"\)|data-replay-loaded' asset_static_replay.js
```
```
34:coworld-replay
133:data-replay-loaded
134:tell("ready")
```
```javascript
  function tell(type, message) {
    if (window.parent === window) return;
    var envelope = { src: "coworld-replay", type: type };
    …
      window.requestAnimationFrame(function () {
        document.documentElement.setAttribute("data-replay-loaded", "true");
        tell("ready");
      });
```

*(d) The replay JSON the viewer was asked to draw* — ordered excerpts from `/tmp/ep.replay`
(round 4). Adapted to this game's field names (`kind`, `turn`; `.say` carries the public utterance):

```bash
jq -r '.events[]|[(.turn//"-"),(.seat//"-"),.kind,((.summary//.say//.action//"")|tostring|.[0:80])]|@tsv' /tmp/ep.replay | head -40
```
```
-	-	start	
0	-	turn	
0	0	move	Looking to buy ore, grain, timber at 2-2.5 hearts per unit. My commission needs 
0	1	move	4 ore for 4 grain, first come
0	2	move	
0	3	move	
0	1	offer	
0	3	offer	
0	0	fill	
0	1	fill	
0	2	fill	
0	3	fill	
1	-	turn	
1	0	move	
1	1	move	4 ore for 4 grain, fair price, let's keep the floor moving
1	2	move	
1	3	move	
1	1	sign	
1	1	offer	
1	1	expire	
1	3	settle	
1	0	fill	
2	-	turn	
2	0	move	
2	1	move	
2	2	move	
2	3	move	
2	3	offer	
2	1	expire	
2	0	fill	
2	1	fill	
2	2	fill	
2	3	fill	
3	-	turn	
3	0	move	
3	1	move	4 ore for 4 grain, need the grain to fill commissions
3	2	move	
3	3	move	
3	1	offer	
3	3	expire	
```

A full `offer` / `sign` / `settle` triple from the same round-4 replay, showing the contract
machinery is real and structured:

```bash
jq -c '[.events[]|select(.kind=="offer")][0], [.events[]|select(.kind=="sign")][0], [.events[]|select(.kind=="settle")][0]' /tmp/ep.replay
```
```json
{"kind":"offer","turn":0,"seat":1,"target":2,"id":"C1",
 "dsl":"OFFER Sprocket\nLOCK 4 ORE\nASK 4 GRAIN\nDUE 1\nIF ALWAYS\nTHEN SWAP\nELSE KEEP",
 "lock":{"ORE":4},"ask":{"GRAIN":4},"due":1,"cond":"ALWAYS","then":"SWAP","else":"KEEP"}
{"kind":"sign","turn":1,"seat":1,"id":"C2","ok":true}
{"kind":"settle","turn":1,"id":"C2","seat":3,"target":1,"cond":"ALWAYS","held":true,
 "branch":"then","payout":"SWAP","transfers":[{"to":3,"n":6,"good":"ORE"},{"to":1,"n":6,"good":"TIMBER"}]}
```

```bash
jq -r '.events[]|[…]|@tsv' /tmp/ep.replay | tail -20
```
```
13	0	fill	
14	-	turn	
14	0	move	Buying 2 grain for turn 15 commission fill. Will pay 2 ore + 10 hearts.
14	1	move	Turn 14: need 2 grain + 2 timber for final 2 commissions. Have 2 grain, 8 timber
14	2	move	
14	3	move	
14	0	offer	
14	3	offer	
14	1	fill	
14	2	fill	
14	3	fill	
15	-	turn	
15	0	move	
15	1	move	
15	2	move	
15	3	move	
15	0	expire	
15	3	expire	
15	0	fill	
16	-	end	
```

```bash
jq -r '.results' /tmp/ep.replay
```
```json
{
  "names": ["daveey","daveey-1","Baseline","Baseline (2)"],
  "scores": [224,110,110,110],
  "hearts": [224,110,110,110],
  "fills": [17,9,9,9],
  "signed": [0,1,0,1],
  "forfeits": [0,0,0,0],
  "profiles": ["Factor","Mason","Farmer","Forester"],
  "turns": 16,
  "maxTurns": 16,
  "heartsMinted": 474,
  "reason": "complete"
}
```

**Spectator-judgment paragraph.** The viewer is legible and it does show the game.
`runs/2026-08-23-escrow/viewer-check/viewer-smoke.png` is a fully-drawn 1280×800 final frame, not
a loading spinner and not an empty canvas: a dark "ESCROW" title bar with the clock
`TURN 16 / 16 · FINAL`, a four-column strip naming every seat with its live heart total and
profile (`daveey 224 FACTOR`, `daveey-1 110 MASON`, `Sprocket 110 FARMER`, `Piston 110 FORESTER`),
four robot avatars in quadrants around a central "ESCROW BOARD" with per-seat ore/grain/timber
inventory pips beneath each, two speech bubbles carrying the seats' most recent public utterances
(one reads "Buying 2 grain for turn 15 commission fill. Will pay 2 ore + 10 hearts." — verbatim
the `say` on the turn-14 seat-0 `move` event above), a centred end-of-episode card reading
`FINAL — 16 TURNS · 474 HEARTS MINTED` / `daveey — MOST HEARTS AT HORIZON` with a four-row table
(`daveey/Factor/224/17 fills/0 signed/0 forfeits`, `daveey-1/Mason/110/9/1/0`,
`Sprocket/Farmer/110/9/0/0`, `Piston/Forester/110/9/1/0`), and a bottom event-tick timeline
scrubber reading `156 / 156` with colour-coded tick marks. Every one of those numbers reconciles
exactly with the `results` JSON above (`heartsMinted: 474`, `scores [224,110,110,110]`,
`fills [17,9,9,9]`, `signed [0,1,0,1]`, `profiles ["Factor","Mason","Farmer","Forester"]`), and the
seats are correctly labelled `daveey` / `daveey-1` with the fillers under their in-world aliases.
So a spectator can see who is playing, what they hold, what they just said, and who won and by how
much. The picture advances: the scrubber moved the clock from `TURN 0` to `TURN 16 / 16 · FINAL`,
and the corroborating round-3 run read `TURN 8 / 16` at the midpoint. Two legibility caveats, both
already visible in the readouts and both worth recording rather than hiding: the smoke script's
`scorebug` selector returned `""` and `feed_lines` was `0` — the shell surfaces scores in its own
top strip and end card rather than in the element the generic probe looks for, and it has no
running text feed, so "who is winning and why" is readable from the picture but not from those two
DOM probes. And what the picture *shows* being played is, per §4/§5, substantially the scripted
trader baseline standing in for the champions on ~59 % of their turns — the viewer is faithful; it
is the play it is rendering that is degraded.

Status: **TRUE** — `loaded: true` (both `data-replay-loaded="true"` and bridge `ready`),
`failure: null`, and the three clock readouts differ, with the round-3 corroborating run showing a
genuine mid-episode `TURN 8 / 16`.

---

## Retry log

- **Check 1 / 3** — polled every ~5 minutes from 16:02:04Z, heartbeat refreshed on every poll
  (Asana `1217753074035208`, field `1217748424048134`, all `200`). Polls: 16:02 (2 pending),
  16:07 (2 completed), 16:12 (unchanged), 16:17 (3 completed), 16:19, 16:28, 16:33 (4 completed).
  Total elapsed 31 min of the 75-minute bound. No retries needed.
- **Check 4 / 5 — three attempts, three different approaches, all FALSE:**
  1. Round 2's replay + hosted log (`ereq_c5429b47-…`): 11/16 and 7/16 champion fallbacks,
     18 `falling back` occurrences.
  2. Round 3's replay + hosted log (`ereq_883156db-…`): 8/16 and 7/16, 15 `falling back`.
  3. Round 4's replay + hosted log (`ereq_52e240bb-…`, the target of record): 12/16 and 7/16,
     19 `falling back`.
  Additionally cross-checked two other LLM coworlds (`contagion`, `raid`) to test the
  platform-wide-Bedrock exception: both clean (0 hits on all four patterns), so the exception does
  not apply.
- **Check 6** — the checklist's first command (raw-HTML iframe grep) found nothing; used the two
  documented fallbacks (SSR `state.playlist[0]` and `POST /coworlds/replays/session`). Also
  recorded that `/coworlds` returns a bare array on this deployment, contradicting the playbook's
  `.entries[]` form.
- **Check 8** — two independent CI executions (`32651276492` on round 3, `32652062253` on round 4);
  both `loaded: true`, `failure: null`.

## API shapes observed this run (deviations worth carrying forward)

- `/rounds?league_id=` → `{entries:[…]}` ✔ (as documented)
- `/episode-requests?round_id=` → `{entries:[…]}` ✔
- `/divisions/<D>/leaderboard` → **bare array** ✔ (as documented); non-null and populated once a
  round completed
- `/leagues` → bare array ✔
- **`/coworlds?limit=200` → bare array**, *not* `{entries:…}` — the playbook's
  `jq '.entries[]…'` fails with `Cannot index array with string "entries"`. Use
  `(if type=="array" then . else .entries end)[]`.
- `/coworlds` `featured_match` is `null` for escrow (platform-wide, already documented)
- `/episode-requests/<id>/artifacts/logs` returns container logs as Python `b'…'` reprs under
  `===== container: <name> =====` headers; decode before grepping or line counts are wrong.
- `episode-requests` `participants[]` uses `is_filler: true/false` with real policy names, not the
  literal `Baseline (N)` display string (that appears in the replay's `policyNames` / `results.names`).
- This game's replay events are keyed `kind` (values `start|turn|move|offer|sign|settle|expire|fill|end`)
  with a `turn` clock; there is no `.type`, no `.tick`, no `decision` kind and no `.fallback` flag —
  a fallback is `kind=="move" and scripted==true`.

## What must change for checks 4 and 5 to pass

Not a verifier action — reported, not fixed. The two LLM champion prompts must be tightened so the
rune they emit is legal on the first attempt: (i) do free-stock accounting before writing `LOCK n GOOD`
(14+2 `unfunded` rejections per episode), (ii) only `SIGN` a contract whose `OFFER` names you
(18 `is not addressed to you` rejections), (iii) verify the ASK is payable before offering, and
(iv) emit the `IF` clause in exactly the documented grammar (`ALWAYS`, `[NOT] HOLDS <cog> <n> <good>`,
`[NOT] PAID <cog> <n> <good>`) — plus the 3 hard parse failures (`EOF expected`). Then re-release and
re-run phase 60.
