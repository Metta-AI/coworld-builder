# VERIFY — goofspiel-oshi-zumo   (2026-08-26T23:58:40Z)

Verdict: **all-true** (8/8 TRUE)

Run: `2026-08-26-goofspiel-oshi-zumo` · slug `goofspiel-oshi-zumo` · coworld `cow_649ab26c-c3a7-4755-8997-a909c953ef01` v`0.1.2`
League `league_af4bfc41-a775-4d89-94eb-194bb5c74f97` · division `div_8ec54c0e-5cce-483f-928c-c779a2d05336`

Every fetch below was made in this phase-60 session (2026-08-26T23:20Z–23:58Z). The two documented
exceptions are item 7 (the committed `release-result.json` from this run's phase-40 dispatch) and
item 8 (the artifact of the `viewer-check.yml` run this session dispatched, `33025003314`).

Headers sent on every Observatory call (values never printed):
`Authorization: Bearer $SOFTMAX_TOKEN`, `User-Agent: coworld-builder/1.0`;
plus `X-Use-Elevated-Privileges: true` on `/artifacts/logs` and `/filler-policies`.

---

## 1. ≥2 completed rounds after fillers were set

Fillers were registered by phase 50 at **2026-08-26T23:18:30Z** (`log.md`). Fresh read of the
league confirms both filler version ids are registered on the league right now:

```bash
curl -sS "$BASE/leagues/$L/filler-policies" "${AUTH[@]}" "${ELEV[@]}" | jq .
```
```json
{
  "filler_policy_versions": [
    {
      "policy_version_id": "56252dee-1714-440b-b5fe-4e3a7215fdb8",
      "policy_id": "53aff795-a863-4319-84d1-c3ed16caa836",
      "policy_name": "goofspiel-oshi-zumo-match",
      "version": 2,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "display_name": null
    },
    {
      "policy_version_id": "13df4c2e-6a8e-4a9b-a026-f064e41b128c",
      "policy_id": "a21fcabf-fd7d-4529-8c38-6f04475fa0c1",
      "policy_name": "goofspiel-oshi-zumo-hoard",
      "version": 2,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "display_name": null
    }
  ]
}
```

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -c 'if type=="array" then . else .entries end
          | map({id,round_number,status,error,created_at,completed_at,
                 entrants:.round_config.entrant_policy_version_ids})'
```

Fetched 2026-08-26T23:54:29Z:

```json
[
 {"id":"round_f572a6f4-dd9a-4f53-9dfe-2be94f021e5d","round_number":4,"status":"completed","error":null,
  "created_at":"2026-08-26T23:47:13.671786Z","completed_at":"2026-08-26T23:51:29.093872Z",
  "entrants":["230face9-774a-4902-8f35-3523c4e840d4","1c7139dc-61dd-4446-81f4-669e3221fc36",
              "d1b4dfbf-d1f7-447d-921d-fe680457375a","bf26100e-af1b-45ac-8bcd-4aa33fec8368"]},
 {"id":"round_d0c09a65-9e28-4db9-8ec9-ff86426f1765","round_number":3,"status":"completed","error":null,
  "created_at":"2026-08-26T23:31:29.692977Z","completed_at":"2026-08-26T23:35:46.462433Z",
  "entrants":["1c7139dc-61dd-4446-81f4-669e3221fc36","d1b4dfbf-d1f7-447d-921d-fe680457375a"]},
 {"id":"round_f669caca-d8db-422e-a52a-43c5df69c973","round_number":2,"status":"completed","error":null,
  "created_at":"2026-08-26T23:16:29.027235Z","completed_at":"2026-08-26T23:20:45.041691Z",
  "entrants":["1c7139dc-61dd-4446-81f4-669e3221fc36","d1b4dfbf-d1f7-447d-921d-fe680457375a"]},
 {"id":"round_96e371e9-c7d6-402f-8ddf-57ff5a444fb3","round_number":1,"status":"failed",
  "error":"Temporal RoundWorkflow failed before settling the round.",
  "created_at":"2026-08-26T23:15:02.213295Z","completed_at":"2026-08-26T23:15:02.465637Z",
  "entrants":["1c7139dc-61dd-4446-81f4-669e3221fc36"]}
]
```

```bash
curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
 | jq -r 'if type=="array" then . else .entries end | [.[]|select(.status=="completed")]|length'
```
```
3
```

Failed round recorded verbatim, as the spec requires: round **1**, `status: "failed"`,
`error: "Temporal RoundWorkflow failed before settling the round."`, created `23:15:02.213295Z`,
i.e. auto-fired at settings time with a **single** entrant
(`entrant_policy_version_ids: ["1c7139dc-…"]`) and **before** the filler POST. It is the documented
"trigger-round issued before any filler exists" shape (`playbooks/observatory-api.md` §6). It does
not count.

Rounds counted: **3 and 4**, both `created_at` (23:31:29Z, 23:47:13Z) strictly **after** the filler
registration at 23:18:30Z. (Round 2 also completed, but its `created_at` 23:16:29Z sits inside the
minute-level ambiguity of phase 50's log stamps, so it is *not* relied on; two unambiguous
post-filler completed rounds are shown without it.)

**Status: TRUE — rounds 3 and 4 completed at 2026-08-26T23:35:46Z and 2026-08-26T23:51:29Z, both
created after fillers were set at 2026-08-26T23:18:30Z. (Round 2 is a third completed round.)**

---

## 2. Both champions ranked; fillers absent/Baseline

```bash
curl -sS "$BASE/divisions/$D/leaderboard" "${AUTH[@]}" \
 | jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```

Fetched 2026-08-26T23:54:29Z (bare list, not `.entries`):

```
1	daveey-1	goofspiel-oshi-zumo-reader:v2	1049.1988133790915	3	4.0
2	relh	co-gas-goofspiel-oshi-zumo-match-relhalpha:v1	1000.0	1	1.0
3	richard	co-gas-goofspiel-oshi-zumo-match-richard:v1	1000.0	1	1.0
4	daveey	goofspiel-oshi-zumo-tempo:v2	950.8011866209087	3	1.0
```

Full rows for the two champions:

```json
{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
 "score":1049.1988133790915,"score_label":"MMR","rounds_played":3,"episode_wins":4.0,
 "win_rate":0.8,"policy_label":"goofspiel-oshi-zumo-reader:v2"}
{"rank":4,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
 "score":950.8011866209087,"score_label":"MMR","rounds_played":3,"episode_wins":1.0,
 "win_rate":0.2,"policy_label":"goofspiel-oshi-zumo-tempo:v2"}
```

Fillers absent:

```bash
jq -r '[.[]|select(.policy_label|test("goofspiel-oshi-zumo-(match|hoard):v2"))]|length'
```
```
0
```

`daveey` (`goofspiel-oshi-zumo-tempo:v2`) and `daveey-1` (`goofspiel-oshi-zumo-reader:v2`) are both
ranked with `rounds_played = 3`. Neither filler policy version
(`goofspiel-oshi-zumo-match:v2` / `goofspiel-oshi-zumo-hoard:v2`) appears on the board.

Note, not a failure: rows 2 and 3 (`relh`, `richard`) are **third-party submissions** made to this
public league by other Softmax players during the run — policy versions
`230face9-774a-4902-8f35-3523c4e840d4` and `bf26100e-af1b-45ac-8bcd-4aa33fec8368`, neither of which
is in `filler_policy_version_ids`. They are real entrants, not fillers; because they filled the
table, round 4 needed no filler seats at all.

**Status: TRUE — both champions ranked (daveey-1 rank 1, daveey rank 4), each rounds_played = 3;
fillers absent from the leaderboard.**

---

## 3. Latest round's episode request completed with a replay_url and correct participants

Latest completed round = **round 4**, `round_f572a6f4-dd9a-4f53-9dfe-2be94f021e5d`.
(`GET /episode-requests?round_id=` is 405 on this deployment — the nested route is used, per
`playbooks/observatory-api.md` §9.)

```bash
curl -sS "$BASE/rounds/round_f572a6f4-dd9a-4f53-9dfe-2be94f021e5d/episode-requests" "${AUTH[@]}" \
 | jq -c 'if type=="array" then . else .entries end | map({id,status,replay_url})'
```
```json
[{"id":"ereq_1e52db7f-89bd-452b-8816-c16b39211264","status":"completed",
  "replay_url":"https://softmax-public.s3.amazonaws.com/replays/da00ff5a-a4d6-4adc-9dd8-5d9b557c44a0.replay"}]
```

```bash
curl -sS "$BASE/episode-requests/ereq_1e52db7f-89bd-452b-8816-c16b39211264" "${AUTH[@]}" \
 | jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/da00ff5a-a4d6-4adc-9dd8-5d9b557c44a0.replay",
  "participants": [
    {"position":0,"kind":"policy","policy_version_id":"230face9-774a-4902-8f35-3523c4e840d4",
     "policy_id":"17e6d764-b054-4d1f-bd5b-4a3fb2b6b846",
     "policy_name":"co-gas-goofspiel-oshi-zumo-match-relhalpha","version":1,
     "player_id":"ply_18302115-9fc9-482d-a2f3-f4c592bf9e57","player_name":"relh",
     "is_filler":false,"is_seed":false},
    {"position":1,"kind":"policy","policy_version_id":"1c7139dc-61dd-4446-81f4-669e3221fc36",
     "policy_id":"06165329-af22-4e3f-b377-0dd8b33aa1ae",
     "policy_name":"goofspiel-oshi-zumo-tempo","version":2,
     "player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey",
     "is_filler":false,"is_seed":false},
    {"position":2,"kind":"policy","policy_version_id":"d1b4dfbf-d1f7-447d-921d-fe680457375a",
     "policy_id":"fcb478a4-be88-4258-8aaf-2c9496bbea85",
     "policy_name":"goofspiel-oshi-zumo-reader","version":2,
     "player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
     "is_filler":false,"is_seed":false},
    {"position":3,"kind":"policy","policy_version_id":"bf26100e-af1b-45ac-8bcd-4aa33fec8368",
     "policy_id":"061f322d-0fee-4703-9bab-2d85ec551045",
     "policy_name":"co-gas-goofspiel-oshi-zumo-match-richard","version":1,
     "player_id":"ply_ded11f40-3e30-4921-b019-f7f6bc3e9c83","player_name":"richard",
     "is_filler":false,"is_seed":false}
  ],
  "participant_scores": [
    {"position":0,"score":-0.05128205128205129},
    {"position":1,"score":-0.15384615384615385},
    {"position":2,"score":0.2564102564102564},
    {"position":3,"score":-0.05128205128205129}
  ]
}
```

`status == "completed"`; `replay_url` non-null; participants name **`daveey`** (seat 1, champion #1
`goofspiel-oshi-zumo-tempo:v2`) and **`daveey-1`** (seat 2, champion #2
`goofspiel-oshi-zumo-reader:v2`). Seats 0 and 3 are third-party entrants, `is_filler:false` — no
`Baseline (N)` seat was needed because four real policies were available.

**Status: TRUE — ereq_1e52db7f-89bd-452b-8816-c16b39211264 completed, replay_url present, both
champions seated (positions 1 and 2), scores recorded for all four seats.**

---

## 4. Replay bytes: valid, correct protocol, and showing the game

```bash
curl -sSL "https://softmax-public.s3.amazonaws.com/replays/da00ff5a-a4d6-4adc-9dd8-5d9b557c44a0.replay" \
     -o /tmp/ep.replay -w "http=%{http_code} bytes=%{size_download}\n"
```
```
http=200 bytes=18216
```

Strict parsers, twice (jq's parser and Python's strict UTF-8 codec — browsers tolerate invalid
UTF-8, these do not):

```bash
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
python3 -c "d=open('/tmp/ep.replay','rb').read(); d.decode('utf-8'); print('python strict utf-8 decode: ok, bytes=',len(d))"
```
```
strict UTF-8 JSON: ok
python strict utf-8 decode: ok, bytes= 18216
```

```bash
jq -r '.protocol, .results.reason, .results.ending' /tmp/ep.replay
```
```
gozu.replay.v1
complete
prizes-exhausted
```

Protocol match: `gozu.replay.v1` is the replay protocol the design note declares
(`runs/2026-08-26-goofspiel-oshi-zumo/design.md` §"Replay bytes (self-sufficient)":
`{"protocol": "gozu.replay.v1", …}`) and the shipped server writes. Confirmed in the source of
record on the release sha:

```bash
gh api repos/Metta-AI/cogame-goofspiel-oshi-zumo/contents/src/gozu/server.nim --jq .content \
 | base64 -d | grep -n 'gozu.replay.v1'
```
```
569:    "protocol": payload{"protocol"}.getStr("gozu.replay.v1"),
```

The live manifest declares the sibling player protocol in the same namespace (it declares no
replay-protocol key at all — `manifest.game.protocols` has exactly `player` and `global`):

```bash
curl -sS "$BASE/coworlds/cow_649ab26c-c3a7-4755-8997-a909c953ef01" "${AUTH[@]}" \
 | jq -r '.manifest.game.protocols.player.value' | head -c 60
```
```
gozu.player.v1 - JSON text frames over the websocket named
```

Config, names and results:

```bash
jq -c '.policyNames, .names, .config' /tmp/ep.replay
jq -c '.results' /tmp/ep.replay
```
```json
["relh","daveey","daveey-1","richard"]
["Ratchet","Tinker","Widget","Gizmo"]
{"mode":"goofspiel","seats":4,"seed":1506627699,"cards":13,
 "prizeOrder":[9,4,6,13,3,11,7,1,8,5,2,12,10],"coins":20,"size":3,"minBid":1,
 "maxRounds":13,"sampled":true}
```
```json
{"names":["relh","daveey","daveey-1","richard"],
 "scores":[-0.05128205128205129,-0.15384615384615385,0.2564102564102564,-0.05128205128205129],
 "points":[19.25,12.25,40.25,19.25],"spent":[91,91,91,91],"bidsMade":[13,13,13,13],
 "fallbacks":[0,0,0,0],"collusionIndex":[0.0,0.0,0.0,0.0],"finalPosition":-1,
 "rounds":13,"maxRounds":13,"mode":"goofspiel","ending":"prizes-exhausted","reason":"complete"}
```

`reason == "complete"` — no `deadline` exception needed. `scores` sums to 0 (−0.05128 − 0.15385 +
0.25641 − 0.05128 = 0.0), `spent` is 91 per seat (the whole 1..13 hand), `points` sums to 91.

Event vocabulary and champion-seat decision provenance. This game emits no `decision` event kind —
per the design note, decision provenance rides in each `reveal`'s `scripted[]` / `fellBack[]` arrays
and in `results.fallbacks[]`, so check 4's counts are read there:

```bash
jq -r '[.events[].kind]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.replay
```
```json
{"end": 1, "prize": 13, "reveal": 13, "start": 1}
```

```bash
jq -r '[.events[]|select(.kind=="reveal")] as $r
       | {seats:.policyNames,
          scripted_true:([range(0;4)]|map(. as $i|[$r[]|.scripted[$i]]|map(select(.==true))|length)),
          fellBack_true:([range(0;4)]|map(. as $i|[$r[]|.fellBack[$i]]|map(select(.==true))|length)),
          bids_per_seat:([range(0;4)]|map(. as $i|[$r[]|.bids[$i]]|length))}' /tmp/ep.replay
```
```json
{
  "seats": ["relh", "daveey", "daveey-1", "richard"],
  "scripted_true": [13, 0, 0, 13],
  "fellBack_true": [0, 0, 0, 0],
  "bids_per_seat": [13, 13, 13, 13]
}
```
```bash
jq -c '.results.fallbacks' /tmp/ep.replay
```
```json
[0,0,0,0]
```

Champion seats are **1 (`daveey`)** and **2 (`daveey-1`)** per `.policyNames`. Across all 13
reveals: `scripted = 0/13` and `fellBack = 0/13` for both champion seats — **every one of their 26
bids was a live LLM decision, zero fallbacks**. Seats 0 and 3 are `scripted: true` because the
third-party entrants are scripted `match` policies, which is their own choice, not a degrade.

Non-trivial content on both champion seats — 13/13 reveals carry a non-empty `say` for each:

```bash
jq -r '[.events[]|select(.kind=="reveal")|.says[1]|select(.!="" and .!=null)]|length' /tmp/ep.replay   # daveey
jq -r '[.events[]|select(.kind=="reveal")|.says[2]|select(.!="" and .!=null)]|length' /tmp/ep.replay   # daveey-1
```
```
13
13
```

**Status: TRUE — 18216 bytes, strict UTF-8 JSON under two strict parsers; protocol
`gozu.replay.v1` as declared; `results.reason == "complete"` / `ending "prizes-exhausted"`;
champion seats 1 and 2 made 13 live LLM bids each with 0 scripted and 0 fallback decisions.**

---

## 5. Hosted game log is clean

The logs body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it is
**decoded** before grepping (per `playbooks/observatory-api.md` §10 — a line-based grep on the raw
bytes undercounts).

```bash
curl -sS "$BASE/episode-requests/ereq_1e52db7f-89bd-452b-8816-c16b39211264/artifacts/logs" \
     "${AUTH[@]}" "${ELEV[@]}" -o /tmp/logs4.raw -w "http=%{http_code} bytes=%{size_download}\n"
```
```
http=200 bytes=59879
```

```bash
python3 - <<'PY'
import ast,re
raw=open('/tmp/logs4.raw',encoding='utf-8',errors='replace').read()
print("container headers in raw:", re.findall(r'^=+ container: .*$', raw, re.M))
txt='\n'.join(ast.literal_eval(m.group(0)).decode('utf-8','replace')
              for m in re.finditer(r"b'(?:[^'\\]|\\.)*'", raw, re.S))
print("decoded chars:", len(txt), "lines:", txt.count('\n')+1)
hits=[(i+1,l) for i,l in enumerate(txt.split('\n'))
      if re.search(r'falling back|LLM provider is unavailable|cut off at max_tokens|rejected', l)]
print("HITS:", len(hits))
for h in hits[:20]: print(h)
PY
```
```
container headers in raw: ['===== container: coworld-init-config =====', '===== container: bedrock-sidecar =====', '===== container: game =====', '===== container: worker =====']
decoded chars: 59391 lines: 211
HITS: 0
```

Grep on the decoded text, expressed as the prompt writes it:

```bash
grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs4.dec \
  || echo CLEAN
```
```
CLEAN
```

Reconciliation with `results.fallbacks` (the design ships a `falling back` line on **every**
fallback, so a clean grep and `fallbacks:[0,0,0,0]` must agree — they do; there were **zero**
`falling back` lines, not "a small number"):

```bash
grep -o '"ok":true' /tmp/logs4.dec | wc -l ; grep -o '"ok":false' /tmp/logs4.dec | wc -l
grep -c 'HTTP/1.1 200 OK' /tmp/logs4.dec
```
```
26
0
26
```

26 Bedrock `InvokeModel` calls, all `ok:true` / HTTP 200, zero failures — exactly 13 rounds × 2 LLM
seats, i.e. one batch call per LLM seat per round and **no retry batch ever fired**. Sample lines
from the decoded `bedrock-sidecar` and `game` containers:

```
2026-08-26 23:47:31,760 INFO httpx HTTP Request: POST https://bedrock-runtime.us-east-1.amazonaws.com/model/global.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke "HTTP/1.1 200 OK"
2026-08-26 23:47:31,760 INFO __main__ bedrock_sidecar_complete {… "model":"global.anthropic.claude-haiku-4-5-20251001-v1:0","operation":"InvokeModel","ok":true,"status_code":200,"latency_ms":2482.89,"error_kind":null,"error_type":null,"message":null,…}
gozu: mode=goofspiel seats=4 rounds=13 model=claude-sonnet-5
gozu: slot 3 delivered a prompt (249 chars, scripted match)
gozu: slot 1 delivered a prompt (657 chars)
gozu: slot 2 delivered a prompt (680 chars)
gozu: round 1 of 13 prize 9 at 6s
gozu: round 1 Ratchet bids 9 at 11s
gozu: round 1 Tinker bids 9 says "Prize 9 in round 1—match the rank and establish early presence." at 11s
gozu: round 1 Widget bids 5 says "Opening with a measured bid on the 9-prize." at 11s
gozu: round 1 Gizmo bids 9 at 11s
gozu: round 1 resolved, margin 0
…
gozu: round 13 resolved, margin 1
Dropped message to disconnected client
gozu: writing results and replay
gozu: artifacts written; 20s shutdown grace before exit
gozu: episode complete, shutting down
```

**Status: TRUE — 4 containers, 59391 decoded characters, 0 matches for
`falling back|LLM provider is unavailable|cut off at max_tokens|rejected`; 26/26 Bedrock calls
returned 200; the game container exits cleanly after writing artifacts.**

---

## 6. The public page uses the static replay path

**Source A (raw HTML grep) — no match; recorded as *unknown*, not a false negative:**

```bash
curl -sS "https://softmax.com/goofspiel-oshi-zumo" | grep -o '<iframe[^>]*src="[^"]*"'
```
```
(no match — page fetched http=200, 633786 bytes; the iframe is client-rendered)
```

**Source B (the page's own SSR payload, `state.playlist[0]`) — the featured match:**

```bash
curl -sS "https://softmax.com/goofspiel-oshi-zumo" -o /tmp/page2.html
grep -o 'playlist.\{0,700\}' /tmp/page2.html | head -1
```
```
playlist\":[{\"episodeId\":\"1f0d5b92-63f2-4422-a329-e2b160df270d\",\"coworldId\":\"cow_649ab26c-c3a7-4755-8997-a909c953ef01\",\"coworldName\":\"goofspiel-oshi-zumo\",\"coworldVersion\":\"0.1.2\",\"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/da00ff5a-a4d6-4adc-9dd8-5d9b557c44a0.replay\",\"finishedAt\":\"2026-08-26T23:51:22.472751Z\",\"roundNumber\":4,\"episodeNumber\":1,\"code\":\"goofspiel-oshi-zumo.r4.e1\",\"matchup\":{\"divisionId\":\"div_8ec54c0e-5cce-483f-928c-c779a2d05336\",\"divisionName\":\"Competition\",\"first\":{\"rank\":1,\"player_id\":\"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d\",\"player_name\":\"daveey-1\",\"score\":1049.1988133790915,\"score_label\":\"MMR\",\"score_v
```

A featured match **is** present: `goofspiel-oshi-zumo.r4.e1`, the round-4 episode of check 3, with
a `matchup` naming rank-1 `daveey-1` — so there are ≥ 2 ranked players.

For completeness, the `/coworlds` list's `featured_match` field is `null`, as it is platform-wide
(`playbooks/observatory-api.md` §Featured match: "`featured_match` is `null` platform-wide, so
neither is evidence"):

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '.entries[]|select(.name=="goofspiel-oshi-zumo")|{id,canonical,replay_viewer,featured_match,version}'
```
```json
{"id":"cow_649ab26c-c3a7-4755-8997-a909c953ef01","name":"goofspiel-oshi-zumo","canonical":true,
 "replay_viewer":null,"featured_match":null,"version":"0.1.2"}
{"id":"cow_22c547d5-de57-4763-9998-0dff289b19bb","name":"goofspiel-oshi-zumo","canonical":false,
 "replay_viewer":null,"featured_match":null,"version":"0.1.1"}
```

**Source C (the call the page's JS makes to build the iframe `src`) — the authoritative one, and
the one used:**

```bash
curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
  -d '{"coworld_id":"cow_649ab26c-c3a7-4755-8997-a909c953ef01",
       "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/da00ff5a-a4d6-4adc-9dd8-5d9b557c44a0.replay"}'
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_649ab26c-c3a7-4755-8997-a909c953ef01/sha256%3A128417c70c353c7e9d2925dd6bcad55872477ae5c83fd99567cab07075b99cb4/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fda00ff5a-a4d6-4adc-9dd8-5d9b557c44a0.replay&v=2",
  "ready": true
}
```

Path shape checks out against the required form
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`:

| Part | Value |
|---|---|
| route | `/v2/coworlds/replays/static/…/index.html` — **static**, not `/client/replay` |
| `<cow_id>` | `cow_649ab26c-c3a7-4755-8997-a909c953ef01` ✅ matches STATE |
| `<sha>` | `sha256:128417c70c353c7e9d2925dd6bcad55872477ae5c83fd99567cab07075b99cb4` (URL-encoded) ✅ the coworld's **manifest_hash**, confirmed by `GET /coworlds/<cow>` → `.manifest_hash` |
| `?replay=` | the S3 replay of check 3/4 |
| `ready` | `true` → static delivery |

There is **no** `/client/replay` pod URL anywhere in the response.

**Which source was used:** the raw-HTML grep (A) found nothing, so the iframe `src` is taken from
**source C**, `POST /v2/coworlds/replays/session`, with the featured match confirmed from the SSR
playlist (source B). This is the documented fallback path.

**Status: TRUE — featured match present (`goofspiel-oshi-zumo.r4.e1`); iframe src is the static
bundle route on the coworld's manifest_hash, `ready: true`, no pod URL.**

---

## 7. Certification declared the static replay bundle

Read from **the committed artifact of this run's phase-40 release dispatch**,
`runs/2026-08-26-goofspiel-oshi-zumo/release-result.json` (present in the repo — no re-download from
run `33021857686` was needed; `/tmp` was never consulted).

```bash
ls -la runs/2026-08-26-goofspiel-oshi-zumo/release-result.json
jq -r '.certify.replay_liveness' runs/2026-08-26-goofspiel-oshi-zumo/release-result.json
```
```
-rw-r--r-- 1 root root 4091 Aug 26 23:13 runs/2026-08-26-goofspiel-oshi-zumo/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Contains the required substring `Replay liveness: skipped (static replay bundle declared`.

**Status: TRUE — read from the committed `runs/2026-08-26-goofspiel-oshi-zumo/release-result.json`
(source: the phase-40 copy, not a re-download).**

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged

*(a) Dispatch.* The full iframe `src` from check 6 was rendered in headless chromium by a
`viewer-check.yml` run **dispatched in this session**:

```bash
SRC="$(jq -r .viewer_url /tmp/session.json)"
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
# dispatch_at=2026-08-26T23:56:12Z
sleep 12
gh run list -R Metta-AI/coworld-builder -w viewer-check.yml \
  --json databaseId,createdAt,status -L 10 | jq -c 'sort_by(.createdAt)|reverse|.[0:3]'
```
```json
[{"createdAt":"2026-08-26T23:56:14Z","databaseId":33025003314,"event":"workflow_dispatch","status":"in_progress"},
 {"createdAt":"2026-08-26T22:43:06Z","databaseId":33020556574,"event":"workflow_dispatch","status":"completed"},
 {"createdAt":"2026-08-26T20:59:11Z","databaseId":33013149654,"event":"workflow_dispatch","status":"completed"}]
```

The run selected is **33025003314**, created `2026-08-26T23:56:14Z` — strictly after the
`23:56:12Z` dispatch, so it is this run's, not "the latest" grabbed blind.

```bash
gh run watch 33025003314 -R Metta-AI/coworld-builder --exit-status
gh run view  33025003314 -R Metta-AI/coworld-builder --json status,conclusion,createdAt,updatedAt
```
```
✓ viewer-check in 46s (ID 98364182705)
  ✓ Load the viewer
  ✓ Upload the evidence
  ✓ Fail if the viewer did not load
{"conclusion":"success","createdAt":"2026-08-26T23:56:14Z","status":"completed","updatedAt":"2026-08-26T23:57:04Z"}
```

```bash
gh run download 33025003314 -R Metta-AI/coworld-builder -n viewer-check \
  -D runs/2026-08-26-goofspiel-oshi-zumo/viewer-check
```
```
runs/2026-08-26-goofspiel-oshi-zumo/viewer-check/viewer-smoke.json   (1440 bytes)
runs/2026-08-26-goofspiel-oshi-zumo/viewer-check/viewer-smoke.png    (423317 bytes)
runs/2026-08-26-goofspiel-oshi-zumo/viewer-check/smoke-stdout.txt    (544 bytes)
runs/2026-08-26-goofspiel-oshi-zumo/viewer-check/smoke-stderr.txt    (0 bytes)
```

All four files are committed with this VERIFY.md.

*(b) The readouts, verbatim.*

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/.../viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":1455,"clock":"GOOFSPIEL · ROUND 0 / 13","scorebug":"relh RATCHET 0 pts daveey TINKER 0 pts daveey-1 WIDGET 0 pts richard GIZMO 0 pts","feed_lines":42}
```

```bash
jq -c '.signals' runs/.../viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/.../viewer-check/viewer-smoke.json
```
```
no failure
```

```bash
jq -r '.scrub[]|"\(.at)\t\(.clock)"' runs/.../viewer-check/viewer-smoke.json
```

| scrub position | `#clock` readout |
|---|---|
| 0 % | `GOOFSPIEL · ROUND 0 / 13` |
| 50 % | `GOOFSPIEL · ROUND 7 / 13 · PRIZE 7` |
| 100 % | `GOOFSPIEL · ROUND 13 / 13 · FINAL` |

Three readouts, all **different**. The scrubber exists and seeks (`#scrub` present — the json
carries real readouts, not the `"(no #scrub…)"` sentinel).

Text-bounds telemetry from the same artifact:

```json
"canvas_text": {"total":1783,"outside":0,"ellipsized":0,"never_inside":0,
                "never_inside_samples":[],"distinct_capped":false,"samples":[]}
"console_tail": ["[bridge] loading","[bridge] ready"]
"status": "REPLAY", "loading_text": "LOADING REPLAY…"
```

1783 canvas text draws, **0** outside the canvas, **0** ellipsized, **0** never inside.

*(c) The replay JSON the viewer was asked to draw* — ordered excerpts from `/tmp/ep.replay`
(`round`, `kind`, `prize`, `bids`, `winners`, `margin`, `says`):

```bash
jq -r '.events[]|[(.round//""),.kind,((.prize//"")|tostring),((.bids//"")|tostring),
                  ((.winners//"")|tostring),((.margin//"")|tostring),((.says//[])|join(" | "))]|@tsv' /tmp/ep.replay
```

early:
```
	start
0	prize	9
0	reveal		[9,9,5,9]	[0,1,3]	0	 | Prize 9 in round 1—match the rank and establish early presence. | Opening with a measured bid on the 9-prize. |
1	prize	4
1	reveal		[4,1,3,4]	[0,3]	0	 | Dumping the lowest card on a small prize. Pace early, strike late. | Prize 4 is modest. Ratchet, Tinker, and Gizmo all overpaid round 1 (bid 9 for p… |
2	prize	6
2	reveal		[6,6,7,6]	[2]	1	 | Matching the prize rank—standard pacing strategy. | Prize 6 is modest but worth fighting for. Rivals showed heavy spending early. |
3	prize	13
```

late:
```
10	reveal		[2,10,10,2]	[1,2]	0	 | Dumping 10 on the low prize. Need to win 10 and 12 decisively. | Securing the midpoint before the final stretch. |
11	prize	12
11	reveal		[12,12,11,12]	[0,1,3]	0	 | Going all-in on the 12. Last chance to catch Widget. | Securing the prize with a measured bid. |
12	prize	10
12	reveal		[10,11,12,10]	[2]	1	 | Final round—Widget's far ahead. I'll bid my last card and hope for a split. | Final round—Widget goes all in for the 10! |
13	end
```

```bash
jq -r '.results' /tmp/ep.replay
```
```json
{"names":["relh","daveey","daveey-1","richard"],
 "scores":[-0.05128205128205129,-0.15384615384615385,0.2564102564102564,-0.05128205128205129],
 "points":[19.25,12.25,40.25,19.25],"spent":[91,91,91,91],"bidsMade":[13,13,13,13],
 "fallbacks":[0,0,0,0],"collusionIndex":[0.0,0.0,0.0,0.0],"finalPosition":-1,
 "rounds":13,"maxRounds":13,"mode":"goofspiel","ending":"prizes-exhausted","reason":"complete"}
```

**Item 8 verdict: `loaded: true` AND the three clock readouts differ → TRUE.**

### Spectator judgment

It is legible, it moves, and it shows this game. The rendered frame
(`runs/2026-08-26-goofspiel-oshi-zumo/viewer-check/viewer-smoke.png`, 1280×800, taken at the 100 %
scrub position) is a fully drawn spectator screen, not a loading shell: the `GOZU` wordmark sits top
left in the Ink & Print serif treatment, the centred clock reads `GOOFSPIEL · ROUND 13 / 13 ·
FINAL`, and a `REPLAY` status chip with the `« LOG` feed toggle sits top right. Beneath it runs the
scorebug strip — four plates, one per seat, each carrying the **policy name** in white (`relh`,
`daveey`, `daveey-1`, `richard`) with the anonymous cog alias as the small caps sub-label
(`RATCHET`, `TINKER`, `WIDGET`, `GIZMO`), the running total (`19.3 pts`, `12.3 pts`, `40.3 pts`,
`19.3 pts`), a remaining-budget rule that is fully spent at the end of an all-13-prizes game, and
that round's bid card (`10`, `11`, `12`, `10`) at the right of each plate. The two name spaces the
design asked for are visibly separated in the picture. The board below shows the four robot avatars
in seat colours, each with its final bid card drawn large and numeric (`10`, `11`, `12`, `10` —
never `T/J/Q/K`), the prize card `10` face up in the centre, and the two champion seats' `say` lines
rendered in their reserved bands: *"Final round—Widget's far ahead. I'll bid my last card and hope
for a split."* (daveey/Tinker) and *"Final round—Widget goes all in for the 10!"* (daveey-1/Widget).
Those are the exact strings in the replay's last `reveal` event, so the picture and the record
agree. The endcard is up, as it should be at 100 %: `FINAL — 13 ROUNDS`, the amber verdict
`daveey-1 TAKES IT`, the reason line `COMPLETE — ALL 13 PRIZES AWARDED`, and a standings table
(`SCORE / POINTS / SPENT / FALLBACKS`) reading `daveey-1 0.26 40.3 91 0`, `relh −0.05 19.3 91 0`,
`richard −0.05 19.3 91 0`, `daveey −0.15 12.3 91 0` — numerically identical to `results.scores` and
`results.points` above, with the zero fallback column corroborating check 4. It stops cleanly above
the transport band; nothing overlays the controls. The transport strip at the bottom carries the
play button, the full-width scrubber with 28 labelled beat markers (seat-tinted on `reveal`, one
tall paper beat at the end) and the `28 / 28` position counter — 28 is exactly `start + 13 prize +
13 reveal + end`, the event count in the replay.

That it *advances* is established by the three differing clock readouts rather than by the still:
0 % is the pre-roll (`ROUND 0 / 13`), 50 % lands on `ROUND 7 / 13 · PRIZE 7` — and `prizeOrder[6]`
in the replay is indeed `7` — and 100 % is `ROUND 13 / 13 · FINAL`. The viewer therefore re-derives
the middle of the episode correctly from the same bytes, not just the first and last frames. Load
was fast and unambiguous: `ms: 1455`, `data-replay-loaded="true"`, and the bridge posted
`loading` → `ready` with an empty `bridge_error`.

**Does it look like the starter's chrome?** Yes — this is babel-lineage chrome, not a rewrite that
shares only the ids. The Ink & Print palette (warm dark paper ground, amber accent, cream rules),
the wordmark-left / clock-centre / status-chip-right top band, the one-plate-per-seat scorebug with
colour chip and budget rule, the modal endcard with a ranked standings table and a single reason
line, and the transport strip with a beat-marked scrubber and a `n / n` counter are all the
paintbot/raid/hive furniture in the same positions, with the game block (bid cards, prize card, say
bands, spent strips) drawn inside it. `chrome_common.js`'s copied regions are doing the work they
were copied for.

**Legibility observations for the coordinator (non-blocking, none of them falsify a check):**
1. The feed panel is collapsed in this capture (the `« LOG` toggle is in the closed state), so the
   42 feed lines the DOM readout counts are not visible in the picture. They exist —
   `feed_lines: 42` — but a first-time spectator arriving at a default-collapsed feed sees the
   verdict without the round-by-round narration. Worth a look at whether the default should be open
   at ≥ 1280 px.
2. At the 100 % frame the endcard covers most of the prize card and the upper board. That is the
   designed behaviour (`#endscreen` is `top:0; bottom: var(--band)`), and every seek dismisses it,
   so it is not a defect — but it does mean the final board state is only readable after a scrub
   backwards.
3. No `overbid` event fired in this episode (`margin` maxed at 1), so the amber OVERBID banner and
   the tall amber beat class are unexercised by this particular replay. Not a finding against the
   viewer; noted so nobody reads the absence as a missing feature.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** — rounds 3 (23:35:46Z) and 4 (23:51:29Z), plus round 2; round 1 failed pre-filler, error quoted |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** — daveey-1 rank 1, daveey rank 4, both `rounds_played: 3`; 0 filler rows |
| 3 | Latest round's episode request completed with replay_url + participants | **TRUE** — `ereq_1e52db7f-…` completed, both champions seated |
| 4 | Replay bytes valid, protocol match, results.reason, champion seats playing | **TRUE** — 18216 B strict UTF-8, `gozu.replay.v1`, `complete`, 26/26 champion bids live LLM, 0 fallbacks |
| 5 | Hosted game log clean | **TRUE** — 0 matches across 4 containers / 59391 decoded chars; 26/26 Bedrock calls 200 |
| 6 | Public page uses the static replay path | **TRUE** — featured match `goofspiel-oshi-zumo.r4.e1`; static `/v2/coworlds/replays/static/<cow>/<manifest_hash>/index.html?replay=…`, `ready:true` |
| 7 | Certification declared the static bundle | **TRUE** — committed `release-result.json`: `Replay liveness: skipped (static replay bundle declared; …)` |
| 8 | Viewer executed and judged | **TRUE** — `loaded:true` in 1455 ms, three differing clock readouts, no failure; babel-lineage chrome confirmed from the rendered PNG |

Replay URL: `https://softmax-public.s3.amazonaws.com/replays/da00ff5a-a4d6-4adc-9dd8-5d9b557c44a0.replay`
Episode request: `ereq_1e52db7f-89bd-452b-8816-c16b39211264` (round 4)
viewer-check run: `33025003314` (Metta-AI/coworld-builder, conclusion `success`)
