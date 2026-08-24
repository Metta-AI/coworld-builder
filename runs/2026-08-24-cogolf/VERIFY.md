# VERIFY — cogolf   (2026-08-24T05:12Z, attempt 2)
Verdict: **all-true (8/8)** — with two documented observations recorded under checks 4 and 6.

Coworld `cow_9cef7a1e-ec19-471d-aeca-0aaee64ae507` v0.1.2, manifest_sha
`sha256:ecaa3322af52d255f83aff956897cd9bd21381c701f9a9b830d8d272aaefc07f`.
League `league_4cb6dc9b-be72-44f7-8713-1b6fc9e1880c`, division `div_b4ac4e81-58f7-429f-b984-9a75c228a24b`.
Headers on every call below: `Authorization: Bearer …` and `User-Agent: coworld-builder/1.0`
(values never printed); `X-Use-Elevated-Privileges: true` added where noted.

**Primary episode for checks 3, 4, 5, 8** — the champion-vs-champion episode of **round 9**, the
latest completed round whose `entrant_attributions` carry BOTH v3 champion policy versions
(`510ff7d5-f787-4640-8c82-dfc071be24f4` = `cogolf-architect:v3` / daveey and
`dd59b716-2c43-4ceb-8298-c18de2ba3fcc` = `cogolf-sniper:v3` / daveey-1):
`round_72dcbe6a-11e5-47d2-ad1b-7754a7abd949` → `ereq_43df75c9-12a9-43ed-bd9e-a55940cf782d` →
`https://softmax-public.s3.amazonaws.com/replays/ff031f16-d234-4846-bd72-0c3dd28f8f52.replay`.
Round **8**'s champion-vs-champion episode (`ereq_944cc058-9ad3-452f-9b10-c22f581b9d38`) is carried
as corroboration and its rendered viewer artifact is committed under
`viewer-check/round8-ereq_944cc058/`.

---

## 1. ≥2 completed rounds after fillers were set — **TRUE**

Fillers `cogolf-literalist` (`c466d2ba-e7e2-4d86-a831-3aeb319cd119`) and `cogolf-pedant`
(`6813522f-31ee-4665-a874-f317fe602bd8`) were registered at **2026-08-24T03:17Z**, before round 1
was created (03:18:00Z). Every completed round below therefore post-dates the filler registration.

```
GET https://softmax.com/api/observatory/v2/rounds?league_id=league_4cb6dc9b-be72-44f7-8713-1b6fc9e1880c&limit=20
(fetched 2026-08-24T05:09:15Z)
```
```json
{"round_number":1,"id":"round_b81e4b8f-910d-44bb-bffe-7310ef34ae75","status":"completed","error":null,"created_at":"2026-08-24T03:18:00.429836Z","completed_at":"2026-08-24T03:19:23.507951Z","entrants":["20a33c64-f144-4aec-8215-4e7db4796b20","71ca4c9d-f2cd-4048-a546-ace9c4ddad97"]}
{"round_number":2,"id":"round_0ade7cf3-db40-4582-b80d-8908163dde51","status":"completed","error":null,"created_at":"2026-08-24T03:33:00.863552Z","completed_at":"2026-08-24T03:35:16.666160Z","entrants":["20a33c64-f144-4aec-8215-4e7db4796b20","71ca4c9d-f2cd-4048-a546-ace9c4ddad97"]}
{"round_number":3,"id":"round_9e3fb561-8d66-45e9-abba-7faed6e297da","status":"completed","error":null,"created_at":"2026-08-24T03:48:02.574616Z","completed_at":"2026-08-24T03:50:05.341465Z","entrants":["20a33c64-f144-4aec-8215-4e7db4796b20","71ca4c9d-f2cd-4048-a546-ace9c4ddad97"]}
{"round_number":4,"id":"round_4f6a380b-4d75-452b-9f61-9ec58e3c4ea4","status":"completed","error":null,"created_at":"2026-08-24T04:03:02.927075Z","completed_at":"2026-08-24T04:04:59.588794Z","entrants":["20a33c64-f144-4aec-8215-4e7db4796b20","71ca4c9d-f2cd-4048-a546-ace9c4ddad97"]}
{"round_number":5,"id":"round_484f1ee2-808d-486b-871b-d8f2e3371da3","status":"completed","error":null,"created_at":"2026-08-24T04:07:58.372854Z","completed_at":"2026-08-24T04:10:21.354527Z","entrants":["510ff7d5-f787-4640-8c82-dfc071be24f4","71ca4c9d-f2cd-4048-a546-ace9c4ddad97"]}
{"round_number":6,"id":"round_3481cea0-e3b3-40f5-8fb6-5ababce196ed","status":"completed","error":null,"created_at":"2026-08-24T04:10:21.764152Z","completed_at":"2026-08-24T04:12:58.438884Z","entrants":["510ff7d5-f787-4640-8c82-dfc071be24f4","dd59b716-2c43-4ceb-8298-c18de2ba3fcc"]}
{"round_number":7,"id":"round_33d02334-824d-41e2-bcb3-438b806b081e","status":"completed","error":null,"created_at":"2026-08-24T04:25:22.651709Z","completed_at":"2026-08-24T04:27:05.393535Z","entrants":["1ad4e964-0bfd-4b77-b889-3f79bb472d4b","510ff7d5-f787-4640-8c82-dfc071be24f4","dd59b716-2c43-4ceb-8298-c18de2ba3fcc","a2a3a441-5f70-411f-a4e1-15c54e7568cc"]}
{"round_number":8,"id":"round_8598ca4d-adb6-43b0-90e8-8f66143dd86d","status":"completed","error":null,"created_at":"2026-08-24T04:40:24.678772Z","completed_at":"2026-08-24T04:42:00.507727Z","entrants":["1ad4e964-0bfd-4b77-b889-3f79bb472d4b","510ff7d5-f787-4640-8c82-dfc071be24f4","dd59b716-2c43-4ceb-8298-c18de2ba3fcc","a2a3a441-5f70-411f-a4e1-15c54e7568cc"]}
{"round_number":9,"id":"round_72dcbe6a-11e5-47d2-ad1b-7754a7abd949","status":"completed","error":null,"created_at":"2026-08-24T04:55:25.041426Z","completed_at":"2026-08-24T04:58:49.078436Z","entrants":["1ad4e964-0bfd-4b77-b889-3f79bb472d4b","510ff7d5-f787-4640-8c82-dfc071be24f4","dd59b716-2c43-4ceb-8298-c18de2ba3fcc","a2a3a441-5f70-411f-a4e1-15c54e7568cc"]}
```
```
$ … | jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length'
9
```

Status: **TRUE** — 9 completed rounds, 0 `failed`/`discarded`, every `error` field `null`.
Rounds **1 and 2** (completed 03:19:23Z and 03:35:16Z) satisfy the ≥2-after-fillers requirement on
their own. Rounds **6, 7, 8 and 9** all carry BOTH v3 champion policy versions in
`entrant_attributions`, so the "≥1 completed both-v3 round" extra requirement is met four times over
(round 6 with exactly the two champions; rounds 7–9 with the two champions plus two externally
submitted players, see check 2). Rounds 1–4 were played by the v2 (pre-`USE_BEDROCK`) champions and
are **not** used to judge check 4; round 5 is mixed (architect:v3 + sniper:v2) and is likewise not
used. No `trigger-round` was issued by the verifier — the ladder produced rounds 7, 8 and 9 on its
own cadence while this check was polling.

---

## 2. Both champions ranked, fillers absent — **TRUE**

```
GET https://softmax.com/api/observatory/v2/divisions/div_b4ac4e81-58f7-429f-b984-9a75c228a24b/leaderboard
(fetched 2026-08-24T05:09:15Z; bare array, not .entries)
```
```json
{"rank":1,"player_name":"richard","policy_label":"co-gas-cogolf-exact-contract-richard:v1","score":1107.7832198257884,"rounds_played":3,"episode_wins":8.0}
{"rank":2,"player_name":"relh","policy_label":"co-gas-cogolf-exact-contract-relhalpha:v1","score":1029.0918232835063,"rounds_played":2,"episode_wins":4.0}
{"rank":3,"player_name":"daveey-1","policy_label":"cogolf-sniper:v3","score":937.3505327762726,"rounds_played":9,"episode_wins":2.0}
{"rank":4,"player_name":"daveey","policy_label":"cogolf-architect:v3","score":925.7744241144329,"rounds_played":9,"episode_wins":2.0}
```

Status: **TRUE** — `daveey` (`cogolf-architect:v3`, rounds_played 9) and `daveey-1`
(`cogolf-sniper:v3`, rounds_played 9) are both ranked with `rounds_played ≥ 1`. Neither filler
(`cogolf-literalist`, `cogolf-pedant`) appears on the board, and no row is labelled `Baseline` —
the fillers were never needed because ≥2 real entrants have been present since round 1.

Observation (not a failure): two **external players** joined this public league between round 6 and
round 7 — `richard` (`ply_ded11f40-…`, policy version `a2a3a441-…`) and `relh` (`ply_18302115-…`,
policy version `1ad4e964-…`), both playing `co-gas-cogolf-exact-contract-*:v1`. They are neither
our champions nor our fillers; they now hold ranks 1–2 and the round is a 4-entrant round robin
(6 episodes per round). This is recorded because it changes what the public page features — see
check 6.

---

## 3. Latest both-v3 round's episode request completed with a replay — **TRUE**

```
GET https://softmax.com/api/observatory/v2/episode-requests?round_id=round_72dcbe6a-11e5-47d2-ad1b-7754a7abd949&limit=20
(fetched 2026-08-24T05:11Z)
```
```json
{"id":"ereq_b4f3cb95-78aa-4524-8da3-3002143d745b","status":"completed","players":["daveey-1","richard"],"replay_url":"https://softmax-public.s3.amazonaws.com/replays/30db15c6-7cc5-42fe-b444-1c9050c4bdb9.replay"}
{"id":"ereq_02ea0d75-daa8-40d6-8d06-205d2000e11d","status":"completed","players":["daveey","richard"],"replay_url":"https://softmax-public.s3.amazonaws.com/replays/2b6fff5e-6508-4553-9f25-64d26f0eb8ae.replay"}
{"id":"ereq_43df75c9-12a9-43ed-bd9e-a55940cf782d","status":"completed","players":["daveey","daveey-1"],"replay_url":"https://softmax-public.s3.amazonaws.com/replays/ff031f16-d234-4846-bd72-0c3dd28f8f52.replay"}
{"id":"ereq_fa73e3fc-ba37-417b-8f9b-643346305779","status":"completed","players":["relh","richard"],"replay_url":"https://softmax-public.s3.amazonaws.com/replays/e10316a2-4981-4e78-804a-5872d295a352.replay"}
{"id":"ereq_fdc9170a-4460-4eef-a57b-230ed316c9bc","status":"completed","players":["relh","daveey-1"],"replay_url":"https://softmax-public.s3.amazonaws.com/replays/4e7958bf-7859-455a-988e-ef114e106640.replay"}
{"id":"ereq_3dacade1-5779-46f3-a368-657b2874b283","status":"completed","players":["relh","daveey"],"replay_url":"https://softmax-public.s3.amazonaws.com/replays/eb4dfbb7-d27f-4761-9530-a0bca8ace68a.replay"}
```

```
GET https://softmax.com/api/observatory/v2/episode-requests/ereq_43df75c9-12a9-43ed-bd9e-a55940cf782d
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/ff031f16-d234-4846-bd72-0c3dd28f8f52.replay",
  "participants": [
    {"position": 0, "kind": "policy", "policy_version_id": "510ff7d5-f787-4640-8c82-dfc071be24f4",
     "policy_name": "cogolf-architect", "version": 3,
     "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3", "player_name": "daveey", "is_filler": false},
    {"position": 1, "kind": "policy", "policy_version_id": "dd59b716-2c43-4ceb-8298-c18de2ba3fcc",
     "policy_name": "cogolf-sniper", "version": 3,
     "player_id": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d", "player_name": "daveey-1", "is_filler": false}
  ],
  "participant_scores": [{"position": 0, "score": -13.0}, {"position": 1, "score": 13.0}]
}
```

Status: **TRUE** — `status: "completed"`, non-null `replay_url`, participants are exactly `daveey`
(`cogolf-architect` **v3**) and `daveey-1` (`cogolf-sniper` **v3**), both `is_filler: false`, with
zero-sum scores −13 / +13.

Corroborating (round 8, `ereq_944cc058-9ad3-452f-9b10-c22f581b9d38`, fetched 2026-08-24T04:46Z):
```json
{"status":"completed",
 "replay_url":"https://softmax-public.s3.amazonaws.com/replays/c1bf5608-26ff-4383-885c-69130305e99a.replay",
 "participants":[{"position":0,"policy_name":"cogolf-architect","version":3,"player_name":"daveey","is_filler":false},
                 {"position":1,"policy_name":"cogolf-sniper","version":3,"player_name":"daveey-1","is_filler":false}],
 "participant_scores":[{"position":0,"score":1.0},{"position":1,"score":-1.0}]}
```

Recorded anomaly (platform, not this coworld): in **round 7** three of the six episodes —
including the daveey-vs-daveey-1 pairing `ereq_17724a20-…` — returned `status: "completed"` with
`replay_url: null`, `scores: []`, `episode_id: null`, `running_at: null` and
`completed_at` ~11 s after `dispatched_at`; `GET …/artifacts/logs` on it returns
`404 {"detail":"No logs found for job bce91d9f-423d-4830-bca5-9cfc58934111"}`. In **round 8** the
same shape hit only the three `relh` episodes. By round 9 all six episodes produced replays. This
did not affect the rounds used above.

---

## 4. Replay bytes are valid and show real LLM play — **TRUE**

```
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/ff031f16-d234-4846-bd72-0c3dd28f8f52.replay" -o /tmp/ep9.replay
$ jq -e . /tmp/ep9.replay >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok
$ jq -r '.format, .protocol, (.events|length)' /tmp/ep9.replay
cogame-cogolf-replay
cogame.cogolf.v1
145
```
`protocol` matches the manifest's `cogame.cogolf.v1`; `format` matches the design note's
`cogame-cogolf-replay`.

```
$ jq -c '.result' /tmp/ep9.replay
```
```json
{"names":["daveey","daveey-1"],"aliases":["Ash","Basil"],"scores":[-13,13],
 "hole_scores":[[0,0,-5,1,0,0,-2,-7,0],[0,0,5,-1,0,0,2,7,0]],
 "breaches":[1,7],"breaches_taken":[7,1],"par_fails":[9,2],
 "tests_fired":[41,43],"illegal_tests":[4,2],"holes_played":9,
 "fallbacks":[0,0],
 "fallback_causes":[{"timeout":0,"malformed":0,"oversize":0,"disconnected":0,"host_error":0},
                    {"timeout":0,"malformed":0,"oversize":0,"disconnected":0,"host_error":0}],
 "reason":"complete","wall_clock_seconds":127.0402096759999,"seed":1406641194,
 "deck_version":"core-1",
 "killer_test":{"hole":8,"slot":1,"target_slot":0,"name":"tie-break by first occurrence",
                "why":"all tied at frequency 2, order by first appearance"}}
```
`results.reason == "complete"` (not `deadline`, not `harness_fault`); server-side
`fallbacks == [0,0]`, all `fallback_causes` zero.

**Positive evidence of real LLM play** (this is the check that was FALSE in attempt 1). Each seat's
`impl` and `note` were compared **byte-for-byte** against the spec module's `LITERAL_IMPL` +
`"playing the text as written"` and `NAIVE_IMPL` + `"aiming at the edges"`, reading the spec sources
from `Metta-AI/cogame-cogolf@main` (`server/cogame_cogolf/specs/*.py`):

```
hole 1 title_case   slot0 SCRIPTED-literalist  impl_chars=72    note='playing the text as written'
hole 1 title_case   slot1 SCRIPTED-literalist  impl_chars=72    note='playing the text as written'
hole 2 score_grade  slot0 LLM                  impl_chars=208   note='thresholds are inclusive lower bounds'
hole 2 score_grade  slot1 LLM                  impl_chars=208   note='thresholds are inclusive, scores exactly on threshold earn…'
hole 3 round_to     slot0 LLM                  impl_chars=232   note='halfway rounds away from zero for all n'
hole 3 round_to     slot1 LLM                  impl_chars=435   note='away from zero on exact halfway'
hole 4 dedupe       slot0 LLM                  impl_chars=540   note='JSON equality: 1==1.0 but true≠1'
hole 4 dedupe       slot1 LLM                  impl_chars=342   note='using value equality for all JSON types'
hole 5 longest_run  slot0 LLM                  impl_chars=296   note='empty list returns 0 as longest run length'
hole 5 longest_run  slot1 LLM                  impl_chars=281   note='empty list returns 0 per spec'
hole 6 path_norm    slot0 LLM                  impl_chars=533   note='.. removes normal components but not other .. in relative …'
hole 6 path_norm    slot1 LLM                  impl_chars=884   note='handling empty, root dotdot, and relative dotdots'
hole 7 range_merge  slot0 LLM                  impl_chars=332   note='ranges merge only if they share a number'
hole 7 range_merge  slot1 LLM                  impl_chars=1212  note='ranges merge iff they share at least one number'
hole 8 top_k        slot0 LLM                  impl_chars=1001  note='tiebreak by first occurrence index'
hole 8 top_k        slot1 LLM                  impl_chars=1146  note='first occurrence for tie-breaking, JSON equality'
hole 9 chunk        slot0 LLM                  impl_chars=152   note='standard chunking with n >= 1'
hole 9 chunk        slot1 LLM                  impl_chars=152   note='empty list returns empty result'
scripted: 2/18
```

16 of 18 submissions are original LLM output — varied implementation lengths (152–1212 chars),
varied `note` text on every hole, and different readings of the same clause by the two seats
(hole 7: "ranges merge only if they share a number" vs "ranges merge iff they share at least one
number"). Differentiated outcomes: `breaches [1,7]`, `par_fails [9,2]`, hole scores −5/+5, +1/−1,
−2/+2, −7/+7 and a named `killer_test`. Scores are not a draw (−13 / +13).

Corroborating, round 8 (`c1bf5608-…`), same byte-comparison:
```
hole 1 word_count  slot0 LLM  impl_chars=446  note="The ambiguous clause is what constitutes punctuation 'stuc…"
hole 2 round_to    slot0 LLM  impl_chars=474  note="reading halfway as away-from-zero (banker's rounding avoid…"
hole 3 range_merge slot0 LLM  impl_chars=770  note="The critical clause is whether ranges 'merely touching' li…"
…
scripted: 0/18
$ jq -c '.result|{scores,breaches,par_fails,fallbacks,reason,killer_test}' /tmp/ep8.replay
{"scores":[1,-1],"breaches":[3,2],"par_fails":[2,2],"fallbacks":[0,0],"reason":"complete",
 "killer_test":{"hole":3,"slot":0,"target_slot":1,"name":"adjacent ranges should not merge",
  "why":"ranges that touch at a gap (2 and 3 are different numbers) should stay separate per spec"}}
```
Round 8's champion-vs-champion episode is **18/18 LLM, zero scripted submissions**.

And round 7's `daveey` seat against the external player `richard`
(`c80d5cfc-8737-4b2b-b821-213f7a6011b6`): 8/9 holes LLM for slot 0, e.g.
`note="ambiguous clause: 'halfway goes away from zer…"`.

Status: **TRUE** — valid strict-UTF-8 JSON, matching `protocol`, `reason: "complete"`, zero
server-side fallbacks, and champion submissions that are demonstrably not the scripted baselines.
Contrast attempt 1 (v2 champions, no `USE_BEDROCK`), where the same comparison returned **18/18
SCRIPTED-literalist**.

**Observation for the coordinator (does not falsify the check).** In round 9, hole 1, *both* seats
submitted output byte-identical to `title_case.LITERAL_IMPL` with the note
`"playing the text as written"`; the same happened at hole 1 of round 6 (`score_grade`, both seats,
including the five `SAFE_TESTS` with identical `why` strings). This is the **client-side** degrade
path in `players/llm_player.py` (`submission()` → `scripted_submission("literalist", …)` on any API
failure), which is invisible in `result.fallbacks` — that counter only records server-side timeout /
malformed / oversize / disconnect / host_error. The pattern (both seats, first hole only, never
later) reads as a cold-start on the per-episode Bedrock sidecar: the sidecar logs
`bedrock_sidecar_started` at 04:40:33 / 04:55:xx, i.e. at the same second the seats connect. It is a
small minority (2/18 in rounds 6 and 9, 0/18 in round 8) and the design's "degrade, never hang" rule
covers it, but the player containers' stderr is not exposed in the hosted log bundle (see check 5),
so the exact cause is not directly observable. Worth a phase-30 note: either warm the client on
`welcome`, or record a client-side fallback flag in the submission so the replay shows it.

---

## 5. Hosted game log is clean — **TRUE**

```
GET https://softmax.com/api/observatory/v2/episode-requests/ereq_43df75c9-12a9-43ed-bd9e-a55940cf782d/artifacts/logs
(headers: Authorization, User-Agent, X-Use-Elevated-Privileges)
HTTP 200 bytes=2012 — python b'…' reprs decoded per container before grepping
```
```
===== container: coworld-init-config =====

===== container: bedrock-sidecar =====
2026-08-24 04:55:33,534 INFO __main__ bedrock_sidecar_started {"listen_port":9100,"region":"us-east-1","has_role_arn":true,"schema_version":"1","source":"coworld_episode","metadata_origin":"bedrock_sidecar","episode_request_id":"43df75c9-12a9-43ed-bd9e-a55940cf782d","job_request_id":"ff031f16-d234-4846-bd72-0c3dd28f8f52","role":"game","slot":"game","image_digest":"sha256:9dd082c11550fcb388e620ec3263fed9a967ce737852852fbf65df0657afda0e"}
[2026-08-24 04:55:33 +0000] [10] [INFO] Running on http://127.0.0.1:9100 (CTRL + C to quit)
2026-08-24 04:55:33,709 INFO hypercorn.error Running on http://127.0.0.1:9100 (CTRL + C to quit)

===== container: game =====
cogame-cogolf serving on 0.0.0.0:8080 (2 seats, deck core, 9 holes, seed 1406641194)
seat 1 (daveey-1) connected
seat 0 (daveey) connected
engine: hole 1 (title_case): score [0, 0] cumulative [0, 0] breaches [0, 0] par_fails [2, 2]
engine: hole 2 (score_grade): score [0, 0] cumulative [0, 0] breaches [0, 0] par_fails [0, 0]
engine: hole 3 (round_to): score [-5, 5] cumulative [-5, 5] breaches [0, 2] par_fails [3, 0]
engine: hole 4 (dedupe): score [1, -1] cumulative [-4, 4] breaches [1, 0] par_fails [0, 0]
engine: hole 5 (longest_run): score [0, 0] cumulative [-4, 4] breaches [0, 0] par_fails [0, 0]
engine: hole 6 (path_norm): score [0, 0] cumulative [-4, 4] breaches [0, 0] par_fails [0, 0]
engine: hole 7 (range_merge): score [-2, 2] cumulative [-6, 6] breaches [0, 2] par_fails [0, 0]
engine: hole 8 (top_k): score [-7, 7] cumulative [-13, 13] breaches [0, 3] par_fails [4, 0]
engine: hole 9 (chunk): score [0, 0] cumulative [-13, 13] breaches [0, 0] par_fails [0, 0]
pacing: reason=complete holes=9/9 seats[s0:-13/1b/9par/0fb s1:+13/7b/2par/0fb] wall=127s/700s seed=1406641194
seat 0 (daveey) disconnected
seat 1 (daveey-1) disconnected
episode over: reason=complete scores=[-13, 13] wall=127s

===== container: worker =====
```
```
$ grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs9.txt || echo CLEAN
CLEAN
```

The same grep on round 8's episode (`ereq_944cc058-…`, HTTP 200, 2004 bytes) also returned
`CLEAN`; its `game` container decoded to:
```
cogame-cogolf serving on 0.0.0.0:8080 (2 seats, deck core, 9 holes, seed 2318947582)
seat 1 (daveey-1) connected
seat 0 (daveey) connected
engine: hole 1 (word_count): score [0, 0] cumulative [0, 0] breaches [0, 0] par_fails [0, 0]
engine: hole 2 (round_to): score [-1, 1] cumulative [-1, 1] breaches [1, 2] par_fails [2, 2]
engine: hole 3 (range_merge): score [1, -1] cumulative [0, 0] breaches [1, 0] par_fails [0, 0]
engine: hole 4 (roman): score [0, 0] cumulative [0, 0] breaches [0, 0] par_fails [0, 0]
engine: hole 5 (score_grade): score [0, 0] cumulative [0, 0] breaches [0, 0] par_fails [0, 0]
engine: hole 6 (path_norm): score [1, -1] cumulative [1, -1] breaches [1, 0] par_fails [0, 0]
engine: hole 7 (title_case): score [0, 0] cumulative [1, -1] breaches [0, 0] par_fails [0, 0]
engine: hole 8 (median): score [0, 0] cumulative [1, -1] breaches [0, 0] par_fails [0, 0]
engine: hole 9 (longest_run): score [0, 0] cumulative [1, -1] breaches [0, 0] par_fails [0, 0]
pacing: reason=complete holes=9/9 seats[s0:+1/3b/2par/0fb s1:-1/2b/2par/0fb] wall=49s/700s seed=2318947582
episode over: reason=complete scores=[1, -1] wall=49s
```

Status: **TRUE** — zero matches for `falling back`, `LLM provider is unavailable`,
`cut off at max_tokens`, `rejected` in either episode's decoded log bundle. Note for completeness:
the bundle contains only `coworld-init-config`, `bedrock-sidecar`, `game` and `worker` containers —
the two **player** containers' stderr (where `llm_player._log` would write) is not published by the
platform, so this grep proves the *game host* is clean and cannot by itself prove the players never
degraded; check 4's byte comparison is what covers that.

---

## 6. The public page uses the static replay path, with a featured match — **TRUE**

Source used: **both**. The raw-HTML grep from `prompts/60-verify.md` finds nothing (the page is
client-rendered for the iframe, as `playbooks/observatory-api.md` §Featured match records), so the
featured match is read from the page's SSR payload and the iframe `src` from the call the page's own
JS makes.

```
$ curl -sS "https://softmax.com/cogolf" | grep -o '<iframe[^>]*src="[^"]*"'
(no match — page is client-rendered)      # fetched 2026-08-24T05:11:18Z, HTTP 200
```

Featured match, from the SSR payload `state.playlist[0]` in the same fetch:
```json
{"episodeId":"3ce9087b-f8b5-4d2c-80bc-dbf3682130f4",
 "coworldId":"cow_9cef7a1e-ec19-471d-aeca-0aaee64ae507","coworldName":"cogolf","coworldVersion":"0.1.2",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/e10316a2-4981-4e78-804a-5872d295a352.replay",
 "finishedAt":"2026-08-24T04:56:39.993109Z","roundNumber":9,"episodeNumber":3,"code":"cogolf.r9.e3",
 "matchup":{"divisionId":"div_b4ac4e81-58f7-429f-b984-9a75c228a24b","divisionName":"Competition",
   "first":{"rank":1,"player_name":"richard","policy_label":"co-gas-cogolf-exact-contract-richard:v1","score":1107.7832198257884,…},
   "second":{"rank":2,"player_name":"relh","policy_label":"co-gas-cogolf-exact-contract-relhalpha:v1","score":1029.0…,…}}}
```

Iframe `src` for that featured replay
(`POST $BASE/coworlds/replays/session {"coworld_id":"cow_9cef7a1e-…","replay_uri":"…e10316a2….replay"}`):
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_9cef7a1e-ec19-471d-aeca-0aaee64ae507/sha256%3Aecaa3322af52d255f83aff956897cd9bd21381c701f9a9b830d8d272aaefc07f/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fe10316a2-4981-4e78-804a-5872d295a352.replay&v=2","ready":true}
```
The same call for the champion-vs-champion replay verified above:
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_9cef7a1e-ec19-471d-aeca-0aaee64ae507/sha256%3Aecaa3322af52d255f83aff956897cd9bd21381c701f9a9b830d8d272aaefc07f/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fff031f16-d234-4846-bd72-0c3dd28f8f52.replay&v=2","ready":true}
```

Coworld detail API (recorded for completeness; `featured_match` is `null` platform-wide and is not
evidence per the playbook):
```json
{"id":"cow_9cef7a1e-ec19-471d-aeca-0aaee64ae507","name":"cogolf","version":"0.1.2","canonical":true,"replay_viewer":null,"featured_match":null}
{"id":"cow_db1331d5-6380-4925-a903-6ac5f2cddc61","name":"cogolf","version":"0.1.1","canonical":false,…}
{"id":"cow_fd356a1d-3eb9-465a-bbdd-fbdb56eafa87","name":"cogolf","version":"0.1.0","canonical":false,…}
```

Status: **TRUE** — a featured match is present (`cogolf.r9.e3`), and the iframe `src` is the
**static** route `…/v2/coworlds/replays/static/<cow_id>/<manifest_sha>/index.html?replay=<s3 url>`
with `ready: true`, `<sha>` equal to the coworld's manifest hash. No `/client/replay` pod URL
anywhere.

**Observation for the coordinator (transient, external cause, resolved before this file was
written).** Between 04:27Z and ~04:55Z `state.playlist` was **`[]`** — verbatim `"playlist":[]` in
three separate fetches at 04:31:33Z, 04:36:58Z and 04:46Z — while `hive`, `raid` and `bullwhip`
pages were `POPULATED` in the same window. Cause, from the evidence in check 3: the page features
the episode between division ranks #1 and #2, which after the external players joined is
`richard` vs `relh`; that pairing produced `replay_url: null` in rounds 7 and 8, so there was
nothing to feature. Round 9 produced a replay for it and the featured match returned. Nothing in
this coworld's release changed in between.

---

## 7. Certification declared the static bundle — **TRUE**

Source read: the **committed** `runs/2026-08-24-cogolf/release-result.json` (phase 40's artifact for
release run `32688088347`, v0.1.2). It was present; no re-download was needed.

```
$ jq -r '.certify.replay_liveness' runs/2026-08-24-cogolf/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
$ jq -c '{version:.version, certify_ok:.certify.ok}' runs/2026-08-24-cogolf/release-result.json
{"version":"0.1.2","certify_ok":true}
```

Status: **TRUE** — the string contains `Replay liveness: skipped (static replay bundle declared`,
and it is the artifact of this run's 0.1.2 release dispatch.

---

## 8. Spectator judgment — the viewer was EXECUTED — **TRUE**

Dispatched by the verifier (the only workflow this role may trigger):
```
$ gh workflow run viewer-check.yml -R Metta-AI/coworld-builder \
    -f url="https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_9cef7a1e-ec19-471d-aeca-0aaee64ae507/sha256%3Aecaa3322af52d255f83aff956897cd9bd21381c701f9a9b830d8d272aaefc07f/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fff031f16-d234-4846-bd72-0c3dd28f8f52.replay&v=2" \
    -f timeout=90
# dispatched 2026-08-24T05:03:57Z; run selected by sort_by(createdAt) among runs created after it
32692217118  2026-08-24T05:03:59Z  → completed / success
$ gh run download 32692217118 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-24-cogolf/viewer-check
```
Committed at `runs/2026-08-24-cogolf/viewer-check/` (`viewer-smoke.json`, `viewer-smoke.png`,
`smoke-stdout.txt`, `smoke-stderr.txt`). The earlier dispatch this run against round 8's
champion-vs-champion replay (run `32691300953`, dispatched 04:47:15Z) is kept under
`runs/2026-08-24-cogolf/viewer-check/round8-ereq_944cc058/`.

*(b) Readouts, verbatim from `viewer-check/viewer-smoke.json`.*
```
$ jq -c '{loaded, ms, clock, scorebug, feed_lines}' viewer-smoke.json
{"loaded":true,"ms":4308,"clock":"HOLE 1 / 9 TITLE CASE A SENTENCE","scorebug":"COGOLF game GV01 TITLE CASE A SENTENCE — CORE/CORE-1 HOLE 1 / 9 TITLE CASE A SENTENCE THIS HOLE Ash SHOTS 0 BREACH 0 HELD 0 ILLEGAL 0 PAR ✗ — #1 BASIL DAVEEY-1 +13 #2 ASH DAVEEY -13","feed_lines":1}

$ jq -c '.signals' viewer-smoke.json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}

$ jq -r '.failure // "no failure"' viewer-smoke.json
no failure

$ jq -r '.status' viewer-smoke.json
raising the fortresses …
```

Three clock readouts:

| scrub | clock |
|---|---|
| 0 % | `HOLE 1 / 9 TITLE CASE A SENTENCE` |
| 50 % | `HOLE 5 / 9 LONGEST RUN` |
| 100 % | `FINAL REPLAYING IN 10S` |

All three differ. `console_tail` from the same artifact:
```
$ jq -r '.console_tail[]' viewer-smoke.json
[info] [replay-worker] worker script start @ 0 ms
[info] [replay-worker] importScripts done @ 1333 ms
[info] [replay-worker] wasm runtime initialized @ 2128 ms
[info] [replay-worker] start @ 2128 ms
[info] [replay-worker] atlas decoded natively @ 2141 ms
[info] [replay-worker] replay bytes ready @ 2141 ms
[info] [replay-worker] wasm load_replay done (238854 B first packet) @ 2170 ms
[info] [replay-worker] wasm load profile: load atlas manifest=2ms parse replay=5ms render first frame=0ms bake arena (1280x704)=3ms bake ground=2ms bake platforms=0ms bake scroll=0ms emit arena bands=7ms render beat=1ms total=23ms packet=238854B
[info] [replay-worker] first packet ingested @ 2181 ms
[info] [replay] first frame at 2815 ms
[info] [replay] worker load profile {worker script start: 0, importScripts done: 1333, wasm runtime initialized: 2128, start: 2128, atlas decoded natively: 2141}
```

Round 8's committed artifact (`viewer-check/round8-ereq_944cc058/viewer-smoke.json`) independently:
```
{"loaded":true,"ms":2354,"clock":"HOLE 1 / 9 COUNT THE WORDS","scorebug":"COGOLF game GV01 COUNT THE WORDS — CORE/CORE-1 HOLE 1 / 9 COUNT THE WORDS THIS HOLE Ash SHOTS 0 BREACH 0 HELD 0 ILLEGAL 0 PAR ✗ — #1 ASH DAVEEY +1 #2 BASIL DAVEEY-1 -1","feed_lines":1}
0%   HOLE 1 / 9 COUNT THE WORDS
50%  HOLE 5 / 9 LETTER GRADE
100% FINAL REPLAYING IN 10S
```

**Item 8 gate:** `loaded: true` ✓ (`data-replay-loaded="true"`, `data_replay_error: null`) and the
three clock readouts differ ✓ → **TRUE**.

*(c) The replay JSON the viewer was asked to draw* — ordered excerpts from `/tmp/ep9.replay`
(`hole`, `slot`, `kind`, `title|name|reason`, `note|observed`):
```
early
1  -  hole_start   Title case a sentence |
1  0  submission                  | playing the text as written
1  1  submission                  | playing the text as written
1  0  test_verdict double space kept | "A  B"
1  0  test_verdict plain sentence    | "Hello World"
1  0  test_verdict empty string      | ""
middle
5  0  test_verdict empty list        | 0
5  0  test_verdict single element    | 1
5  0  test_verdict all same          | 3
5  1  test_verdict all same          | 5
late
9  1  test_verdict n larger than list      | [[1, 2, 3]]
9  1  test_verdict chunk size of 1         | [[1], [2], [3]]
9  1  test_verdict exact multiple          | [[1, 2, 3], [4, 5, 6]]
9  0  par_result
9  1  par_result
-  -  hole_score
-  -  episode_end  complete |
```
145 events; kinds observed: `hole_start`, `submission`, `test_verdict`, `par_result`, `hole_score`,
`episode_end` — exactly the design note's enum.

### Spectator judgment

**It is legible, and it shows the game.** `viewer-smoke.png` (1280×800, committed) is the endcard of
the round-9 champion match: masthead `COGOLF · game GV01 · CHUNK A LIST — CORE/CORE-1`, a big
centred `FINAL / REPLAYING IN 10S`, a per-hole strip (`THIS HOLE Ash · SHOTS 5 · BREACH 0 · HELD 5 ·
ILLEGAL 0 · PAR 0/4`) and a two-seat scorebug reading `#1 BASIL daveey-1 +13` and `#2 ASH daveey
−13` — which is exactly `result.scores == [-13, 13]` with the names from `result.names`. The centre
panel says `BASIL WINS`, subtitled `ZERO-SUM · BREACHES − AUDIT FAILURES`, with side-by-side cards:
Basil breaches 7 / breached 1 / audit fails 2 / illegal 2, Ash breaches 1 / breached 7 / audit fails
9 / illegal 4 — matching `result.breaches [1,7]`, `breaches_taken [7,1]`, `par_fails [9,2]`,
`illegal_tests [4,2]` exactly. Below it the killer test is quoted in words a spectator can follow:
`KILLER TEST · hole 8 · Basil ▸ "tie-break by first occurrence" — all tied at frequency 2, order by
first appearance`, the same object as `result.killer_test`. The right-hand rail carries the hole-9
spec prose, the reference's ambiguity line, the seat's 7-line `def solve(xs, n)` implementation, and
a TESTS FIRED table with `args → expect`, a green `held`/`breach` verdict and the shooter's `why`
for each of the five shots, then `hidden audit: 0 / 4 failed` and a FINAL RESULT table
(score, breaches, breached, par fails, tests fired 41 / 43, illegal, fallbacks 0 / 0,
`9 holes · end complete · seed 1406641194 · 127 s wall`). Two robot figures stand in front of
brick "fortresses" on a lit arena floor, with a bottom-left event feed (`H9 · audit of Basil — 0/4
failed`, `H9 · hole score +0 / +0 — running −13 : 13`, `MATCH OVER — complete — −13 : 13`).

It is **not** empty and **not** frozen: the three scrub readouts advance
`HOLE 1 / 9 TITLE CASE A SENTENCE → HOLE 5 / 9 LONGEST RUN → FINAL`, matching the recorded spec
order (`title_case`, …, `longest_run` at hole 5, …, `chunk` at hole 9) — the picture and the record
agree, hole for hole.

**Chrome provenance:** it looks like the starter's chrome, not a rewrite. The bottom transport strip
is the paintbot/raid/hive one — restart, step-back, play, step-forward, `+5`, jump-to-end, a
`spoilers` toggle, the result chip, `beat 145 / 145`, the speed cluster `0.5× 1× 2×` and `step 145`,
over a full-width scrubber with the momentum graph and coloured event ticks under a legend
`HOLE | BREACH | ILLEGAL | FALLBACK | KILLER`. The keyboard hint line
(`space play · ←/→ beat · ↑/−5/+5 · home/end · [] seat · 1-5 speed · o spoilers · p pane`) is the
starter's. Scorebug, endcard and feed are the same components with cogolf's vocabulary.

**Legibility notes for phase 30** (non-blocking, not defects): the hole-9 spec scroll hanging above
the arena is rendered at low contrast against the dark banner and is effectively unreadable in the
screenshot — the right-hand rail carries the same prose legibly, so nothing is lost, but the banner
copy is decorative rather than informative at this size. Nothing else is obscured.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers (+ ≥1 both-v3 round) | TRUE — 9 completed; rounds 6–9 both-v3 |
| 2 | Both champions ranked, fillers absent | TRUE — daveey #4, daveey-1 #3, 9 rounds each |
| 3 | Latest both-v3 round's episode completed with replay | TRUE — `ereq_43df75c9-…`, r9 |
| 4 | Replay bytes valid, champions really played | TRUE — 16/18 LLM (r9), 18/18 (r8), fallbacks [0,0] |
| 5 | Hosted game log clean | TRUE — CLEAN on r9 and r8 |
| 6 | Public page: featured match + static iframe | TRUE — `cogolf.r9.e3`, static route, `ready:true` |
| 7 | Certification declared the static bundle | TRUE — committed `release-result.json` |
| 8 | Viewer executed: loaded + motion | TRUE — `loaded:true`, three differing clocks |
