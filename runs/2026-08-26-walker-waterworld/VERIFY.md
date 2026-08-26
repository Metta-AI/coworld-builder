# VERIFY — walker-waterworld   (2026-08-26T12:14Z)

Verdict: **all-true** (8/8 TRUE)

Run `2026-08-26-walker-waterworld` · coworld `cow_36a12905-cdf6-4c9e-8bc4-2c0e541b9fb1` v`0.1.1`
(manifest `sha256:68bb2bd31430aa5ca2bef05502d31368d51e88014fd53a75255e1b7b3d9e7442`) ·
league `league_69fe3c37-8208-4e14-b575-331e1d018d9b` · division `div_ef3424b8-a20d-4029-8918-e12b6fb65156`.

Every fetch below was made fresh in this phase-60 session (2026-08-26T11:47Z–12:14Z). The two
documented exceptions are item 7 (the committed `release-result.json` from this run's phase-40
dispatch) and item 8 (the artifact of the `viewer-check.yml` run **this** session dispatched,
32967129036). Headers sent on every Observatory call:
`Authorization: Bearer $SOFTMAX_TOKEN` + `User-Agent: coworld-builder/1.0`, plus
`X-Use-Elevated-Privileges: true` on the artifact reads. No header values are reproduced here.

**API-shape deviations observed this run** (worth carrying into `playbooks/observatory-api.md`):

| Endpoint | Brief/playbook said | Observed 2026-08-26 |
|---|---|---|
| `GET /rounds?league_id=` | bare array | **`{"entries":[…]}` object** (`jq -r type` → `object`). The dual-shape jq was used throughout. |
| `GET /divisions/<D>/leaderboard` | bare list | bare list — confirmed (`jq -r type` → `array`). |
| `GET /episode-requests?round_id=` | works | **HTTP 405 `{"detail":"Method Not Allowed"}`** — the flat list route is gone (this is the same 405 that killed release dispatch 1 with CLI 0.1.42). The nested `GET /rounds/<round_id>/episode-requests` works and was used. `GET /episode-requests/<id>` (detail) still works. |

---

## 1. ≥2 completed rounds after the fillers were set — **TRUE**

```
$ curl -sS "$BASE/rounds?league_id=league_69fe3c37-8208-4e14-b575-331e1d018d9b&limit=20" "${AUTH[@]}" -o /tmp/v_rounds.json -w "HTTP=%{http_code}\n"
HTTP=200
$ jq -r 'type' /tmp/v_rounds.json
object
$ jq -r '[(if type=="array" then . else .entries end)[]|select(.status=="completed")]|length' /tmp/v_rounds.json
2
$ jq -c '(if type=="array" then . else .entries end)[]|{round_number,id,status,error,created_at,completed_at,entrants:.round_config.entrant_policy_version_ids}' /tmp/v_rounds.json
```
```json
{"round_number":3,"id":"round_5de2864a-9bfd-44b0-b450-a60cfa47532c","status":"completed","error":null,"created_at":"2026-08-26T11:57:11.925979Z","completed_at":"2026-08-26T12:04:54.278349Z","entrants":["6c1d8fe1-653e-4d47-aa25-34c69f18bd69","ddef617d-f223-48ae-9d68-31cca603aeb6"]}
{"round_number":2,"id":"round_1d3f3cd6-403e-4e79-9b91-8ef6b64328a1","status":"completed","error":null,"created_at":"2026-08-26T11:42:11.564630Z","completed_at":"2026-08-26T11:47:50.748311Z","entrants":["6c1d8fe1-653e-4d47-aa25-34c69f18bd69","ddef617d-f223-48ae-9d68-31cca603aeb6"]}
{"round_number":1,"id":"round_0f71dacd-69d7-428f-9c40-bca2991d3f12","status":"failed","error":"Temporal RoundWorkflow failed before settling the round.","created_at":"2026-08-26T11:42:00.494974Z","completed_at":"2026-08-26T11:42:00.795629Z","entrants":["6c1d8fe1-653e-4d47-aa25-34c69f18bd69","ddef617d-f223-48ae-9d68-31cca603aeb6"]}
```
The league's own settings row in the same body carries the filler list, i.e. fillers are live on the
league that produced these rounds:
```json
"filler_policy_version_ids":["027d401f-c968-47ef-bbee-ff7f62a7613c","3264fa0c-76f2-42f1-a6a8-010f540dde4d"]
```

Status: **TRUE** — rounds **2** and **3** are `completed` (`2026-08-26T11:47:50Z` and
`2026-08-26T12:04:54Z`), both **after** round 1, the only pre-filler round, which is `failed` with
`error` quoted verbatim above (`Temporal RoundWorkflow failed before settling the round.` — the
documented auto-fire-at-unpause race, `playbooks/observatory-api.md` §6). Failed round 1 is not
counted.

Two facts recorded rather than smoothed over:
- `log.md` records the filler POST at `2026-08-26T11:42:50Z`. Round 2's **row** was created at
  `11:42:11.564Z`, i.e. 39 s *earlier*. What settles the "after the fillers were set" requirement is
  not the row timestamp but the seating: round 2's episode actually ran with two filler seats
  (`walker-waterworld-drifter:v2` `is_filler: true` ×2 — pasted under item 3's round-2 cross-check
  below, and visible in that replay's `names` as `Baseline` / `Baseline (2)`). Round 3
  (created `11:57:11Z`, after the POST) satisfies the requirement on the timestamp alone and was
  seated with `walker-waterworld-shoal:v2` ×2 as fillers.
- Poll trail (5-minute cadence, 75-minute bound from 11:47:22Z, i.e. deadline 13:02:22Z; exited on
  success at 12:08:34Z, 21 minutes in):
```
2026-08-26T11:48:33Z rounds=[2:completed 1:failed] completed=1
2026-08-26T11:53:34Z rounds=[2:completed 1:failed] completed=1
2026-08-26T11:58:34Z rounds=[3:pending 2:completed 1:failed] completed=1
2026-08-26T12:03:34Z rounds=[3:pending 2:completed 1:failed] completed=1
2026-08-26T12:08:34Z rounds=[3:completed 2:completed 1:failed] completed=2
2026-08-26T12:08:34Z DONE >=2 completed
```

## 2. Both champions ranked, fillers absent/Baseline — **TRUE**

```
$ curl -sS "$BASE/divisions/div_ef3424b8-a20d-4029-8918-e12b6fb65156/leaderboard" "${AUTH[@]}" -o /tmp/v_lb.json -w "HTTP=%{http_code}\n"
HTTP=200
$ jq -r 'type' /tmp/v_lb.json
array
$ jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv' /tmp/v_lb.json
1	daveey	walker-waterworld-tandemhunt:v2	1000.0	2	0.0
2	daveey-1	walker-waterworld-relay:v2	1000.0	2	0.0
```
Raw body (whole thing — it is two rows):
```json
[{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1000.0,"score_label":"MMR","score_value_type":"integer","rounds_played":2,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"walker-waterworld-tandemhunt:v2","recent_rounds":null},{"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":1000.0,"score_label":"MMR","score_value_type":"integer","rounds_played":2,"episode_wins":0.0,"episodes_played":null,"win_rate":0.0,"policy_label":"walker-waterworld-relay:v2","recent_rounds":null}]
```

Status: **TRUE** — `daveey` (rank 1, `walker-waterworld-tandemhunt:v2`) and `daveey-1` (rank 2,
`walker-waterworld-relay:v2`), each `rounds_played = 2 ≥ 1`. Neither filler
(`walker-waterworld-shoal:v2`, `walker-waterworld-drifter:v2`) appears — the "fillers absent" branch
of the requirement. `score` is `1000.0` for both and `episode_wins` `0.0` because walker-waterworld is
a **shared-score co-op** game: `results.win` is `[false,false,false,false]` unless the pod reaches
`captureTarget = 20` (design.md §end table), so Elo has nothing to separate and both stay at the
`initial_rating`. Ranked and rounds-played are what this check requires; both hold.

## 3. Latest completed round's episode request completed with a replay — **TRUE**

Latest completed round = **3** (`round_5de2864a-9bfd-44b0-b450-a60cfa47532c`, from item 1).

```
$ curl -sS "$BASE/episode-requests?round_id=round_5de2864a-9bfd-44b0-b450-a60cfa47532c&limit=20" "${AUTH[@]}" -w "\nHTTP=%{http_code}\n"
{"detail":"Method Not Allowed"}
HTTP=405
```
The prompt's flat route is dead (see the deviation table). Nested route, which works:
```
$ curl -sS "$BASE/rounds/round_5de2864a-9bfd-44b0-b450-a60cfa47532c/episode-requests?limit=20" "${AUTH[@]}" -o /tmp/v_erlist.json -w "HTTP=%{http_code}\n"
HTTP=200
$ jq -c '(if type=="array" then . else .entries end)[]|{id,status,replay_url}' /tmp/v_erlist.json
{"id":"ereq_0910faa4-4573-4486-b6e6-22ccaded84a0","status":"completed","replay_url":"https://softmax-public.s3.amazonaws.com/replays/d28f4f1b-941e-478d-a418-4898fb1c19d6.replay"}

$ curl -sS "$BASE/episode-requests/ereq_0910faa4-4573-4486-b6e6-22ccaded84a0" "${AUTH[@]}" -o /tmp/v_erdetail.json -w "HTTP=%{http_code}\n"
HTTP=200
$ jq '{status, replay_url, participants: [.participants[]|{position,policy_name,version,player_name,is_filler}], participant_scores}' /tmp/v_erdetail.json
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/d28f4f1b-941e-478d-a418-4898fb1c19d6.replay",
  "participants": [
    {"position": 0, "policy_name": "walker-waterworld-tandemhunt", "version": 2, "player_name": "daveey",   "is_filler": false},
    {"position": 1, "policy_name": "walker-waterworld-relay",      "version": 2, "player_name": "daveey-1", "is_filler": false},
    {"position": 2, "policy_name": "walker-waterworld-shoal",      "version": 2, "player_name": "daveey",   "is_filler": true},
    {"position": 3, "policy_name": "walker-waterworld-shoal",      "version": 2, "player_name": "daveey",   "is_filler": true}
  ],
  "participant_scores": [
    {"position": 0, "score": 104.679}, {"position": 1, "score": 104.679},
    {"position": 2, "score": 104.679}, {"position": 3, "score": 104.679}
  ]
}
```
And the sibling `episodes` view confirms it is the **0.1.1** coworld, not the stray 0.1.0:
```
$ curl -sS "$BASE/rounds/round_5de2864a-9bfd-44b0-b450-a60cfa47532c/episodes" "${AUTH[@]}" -o /tmp/v_eps.json -w "HTTP=%{http_code}\n"
HTTP=200
$ jq -c '(if type=="array" then . else .entries end)[]|{id,episode_id,coworld_id,coworld_name,coworld_version,variant_name,status,job_index}' /tmp/v_eps.json
{"id":"ereq_0910faa4-4573-4486-b6e6-22ccaded84a0","episode_id":"9c7211b8-68ff-460d-870a-81e47aa67f52","coworld_id":"cow_36a12905-cdf6-4c9e-8bc4-2c0e541b9fb1","coworld_name":"walker-waterworld","coworld_version":"0.1.1","variant_name":"The Tank (4 skimmers, 72 s)","status":"completed","job_index":0}
```

Round-2 cross-check (the evidence used for item 1's "fillers were seated"):
```
$ curl -sS "$BASE/episode-requests/ereq_fe830e29-94bd-4b9f-8343-d1a4ac1f42e8" "${AUTH[@]}" | jq -c '[.participants[]|{position,policy_name,player_name,is_filler}]'
[{"position":0,"policy_name":"walker-waterworld-tandemhunt","player_name":"daveey","is_filler":false},
 {"position":1,"policy_name":"walker-waterworld-relay","player_name":"daveey-1","is_filler":false},
 {"position":2,"policy_name":"walker-waterworld-drifter","player_name":"daveey","is_filler":true},
 {"position":3,"policy_name":"walker-waterworld-drifter","player_name":"daveey","is_filler":true}]
```

Status: **TRUE** — `status == "completed"`, non-null `replay_url`, participants name **daveey**
(`tandemhunt:v2`) and **daveey-1** (`relay:v2`) as non-fillers, with the two remaining seats
`is_filler: true` (`shoal:v2`; they surface as `Baseline` / `Baseline (2)` in the replay and the
viewer — see item 4). `coworld_version` is `0.1.1` / `cow_36a12905-…`; the stray 0.1.0 cow
`cow_6f92bb4c-…` appears nowhere in this round.

## 4. Replay bytes are valid and show the game — **TRUE**

```
$ curl -sSL "https://softmax-public.s3.amazonaws.com/replays/d28f4f1b-941e-478d-a418-4898fb1c19d6.replay" -o /tmp/ep.replay -w "http=%{http_code} bytes=%{size_download} ct=%{content_type}\n"
http=200 bytes=79104 ct=application/octet-stream
$ python3 -c "d=open('/tmp/ep.replay','rb').read(); print(len(d), d[:32])"
79104 b'COWLDWWD\x01\x00\x11\x00walker-waterworld\x01\x001'
$ jq -e . /tmp/ep.replay >/dev/null 2>&1 || echo "jq strict on raw .replay: FAILS (binary COWLDWWD)"
jq strict on raw .replay: FAILS (binary COWLDWWD)
```
**How this was parsed, and why that is the sanctioned path.** This coworld's replay is the starter's
**binary `COWLDWWD`** format (the static wasm viewer parses exactly this), which the design note
declares and for which it declares the phase-60 substitute verbatim — repo
`docs/plans/2026-08-26-walker-waterworld-design.md`, §"The replay stays the starter's binary
`COWLDWWD` format" → "**The phase-60 substitute for SPEC §Definition of done check 4**":
`python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json; jq -e . /tmp/ep.json`. I also checked
for a JSON form and there is none: the `.json` sibling on S3 is
`http=403 <Error><Code>AccessDenied</Code>` and the platform artifact route returns the **same bytes**
as S3 for this very episode, so there is no JSON variant to prefer:
```
$ curl -sS "$BASE/episode-requests/ereq_0910faa4-4573-4486-b6e6-22ccaded84a0/artifacts/replay" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/v_art_replay.bin -w "HTTP=%{http_code} bytes=%{size_download}\n"
HTTP=200 bytes=79104
$ sha256sum /tmp/ep.replay /tmp/v_art_replay.bin
d21ee7fa3f768d88739bbab257ea7a232637b2499d32e9cb4ff8e7e5859fce1f  /tmp/ep.replay
d21ee7fa3f768d88739bbab257ea7a232637b2499d32e9cb4ff8e7e5859fce1f  /tmp/v_art_replay.bin
```

```
$ cd /workspace/cogame-walker-waterworld && python3 tools/replay_summary.py /tmp/ep.replay > /tmp/ep.json; echo exit=$?
exit=0
$ jq -e . /tmp/ep.json >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok
$ jq -r '.protocol, .results.reason, .results.endRule, .results.captures' /tmp/ep.json
walker-waterworld/v1
complete
full_time
12
$ jq -r '[.intents[]|select(.source=="llm")]|length' /tmp/ep.json
48
$ jq -r '.fallbacks' /tmp/ep.json
0
$ jq '.results' /tmp/ep.json
```
```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)"],
 "aliases":["SKIM-1","SKIM-3","SKIM-4","SKIM-2"],
 "skimmers":[0,2,3,1],
 "policyKinds":["llm","llm","scripted","scripted"],
 "scores":[104.679,104.679,104.679,104.679],
 "win":[false,false,false,false],
 "sharedScore":104.679,
 "captures":12,"captureTarget":20,"nibbles":24,"poisonHits":5,"thrustCost":6.521,
 "assists":[5,7,5,7],"nibblesBySeat":[5,6,8,5],"poisonBySeat":[1,0,2,2],
 "thrustMeanPct":[95,95,88,89],
 "llmTurns":[24,24,0,0],"fallbackTurns":[0,0,0,0],
 "finalTick":1776,"reason":"complete","endRule":"full_time","seed":344261098}
```
Champion seats are non-scripted and non-constant:
```
$ jq -c '[.intents[]|{seat,source}]|group_by(.seat)|map({seat:.[0].seat,sources:(map(.source)|unique)})' /tmp/ep.json
[{"seat":0,"sources":["llm"]},{"seat":1,"sources":["llm"]},{"seat":2,"sources":["scripted"]},{"seat":3,"sources":["scripted"]}]
$ jq -r '[.intents[]|select(.seat==0)|.mode]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.json
{"avoid":8,"escort":1,"hunt":12,"sweep":3}
$ jq -r '[.intents[]|select(.seat==1)|.mode]|group_by(.)|map({(.[0]):length})|add' /tmp/ep.json
{"avoid":12,"hunt":9,"sweep":3}
$ jq -r '[.intents[]|select(.source=="llm")|.say]|unique|length' /tmp/ep.json
48
```

Status: **TRUE** — strict-UTF-8 JSON ok via the design-note-declared decoder;
`protocol == "walker-waterworld/v1"` (matches the manifest/protocol string the repo's
`tests/test_replay.nim:187` pins); `results.reason == "complete"` with `endRule "full_time"` — the
strict branch, so the `deadline`/`wall_clock` carve-out was **not needed**; `captures = 12 > 0`;
champion seats' 48 decisions are all `source == "llm"` across four distinct modes with **48 distinct**
`say` strings, and **`fallbacks = 0` / `fallbackTurns [0,0,0,0]`** — zero fallbacks out of 48
decisions, far below "a small minority".

## 5. Hosted game log is clean — **TRUE**

```
$ curl -sS "$BASE/episode-requests/ereq_0910faa4-4573-4486-b6e6-22ccaded84a0/artifacts/logs" "${AUTH[@]}" "${ELEV[@]}" -o /tmp/v_logs.txt -w "HTTP=%{http_code} bytes=%{size_download}\n"
HTTP=200 bytes=101527
```
The body is python `b'…'` byte-string reprs under `===== container: <name> =====` headers, and each
container's whole log is **one** repr containing `\n` escapes — so a line-based grep sees 4 lines and
is meaningless. Decoded first (`ast.literal_eval` per repr, as `playbooks/observatory-api.md` §10
requires), with coverage printed so nothing is silently skipped:
```
$ python3 /tmp/decode_logs.py /tmp/v_logs.txt      # decodes, then greps the required pattern
container coworld-init-config: 0 decoded lines, 0 matches
container bedrock-sidecar: 195 decoded lines, 0 matches
container game: 40 decoded lines, 0 matches
container worker: 0 decoded lines, 0 matches
TOTAL decoded lines: 235
CLEAN
$ # coverage proof: every byte of every container body is inside a decoded repr
coworld-init-config: body=6 reprs=1 covered=3 decoded_chars=0 lines=0
bedrock-sidecar: body=98897 reprs=1 covered=98894 decoded_chars=98696 lines=195
game: body=2483 reprs=1 covered=2480 decoded_chars=2239 lines=40
worker: body=5 reprs=1 covered=3 decoded_chars=0 lines=0
```
(pattern grepped, verbatim: `falling back|LLM provider is unavailable|cut off at max_tokens|rejected`.
`covered` is the total span of the decoded reprs; the 2–3 byte shortfall against `body` is the newline
padding around the repr, and the `b''` bodies are genuinely empty. `decoded_chars` is below `covered`
because `\n`/`\"` escapes shrink on decoding.)

The decoder, in full, so the grep is auditable (`/tmp/decode_logs.py`; stdlib only):
```python
raw = open(path).read()
parts = re.split(r'^===== container: (.+?) =====$', raw, flags=re.M)
RE  = re.compile(r"b'(?:[^'\\]|\\.)*'|b\"(?:[^\"\\]|\\.)*\"")
pat = re.compile(r'falling back|LLM provider is unavailable|cut off at max_tokens|rejected')
for i in range(1, len(parts), 2):
    name, body = parts[i], parts[i+1]
    decoded = ''.join(ast.literal_eval(m).decode('utf-8','replace') for m in RE.findall(body))
    hits += [f'{name}:{n}: {l}' for n, l in enumerate(decoded.splitlines(), 1) if pat.search(l)]
print('\n'.join(hits) if hits else 'CLEAN')
```

Positive evidence that the LLM path really ran (a clean log must not be a silent log):
```
$ grep -o 'bedrock_[a-z_]*' /tmp/vdec_bedrock-sidecar.log | sort | uniq -c | sort -rn | head
    145 bedrock_sidecar
     48 bedrock_sidecar_usage
     48 bedrock_sidecar_complete
     48 bedrock_sidecar_call
      1 bedrock_sidecar_started
$ head -17 /tmp/vdec_game.log
seed not pinned; randomized
walker-waterworld config: host=0.0.0.0 port=8080 seed=344261098 num_agents=4 maxTicks=1728 turnTicks=72 captureTarget=20 wallClockBudget=660s
starting walker-waterworld on 0.0.0.0:8080
board render caches baked in 162 ms
waterworld llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0
waiting for players: 0/4, need 4 more
player connected: Baseline (2)
player connected: Baseline
player connected: daveey-1
player connected: daveey
seat 0 registered: kind=llm baseline=shoal
seat 1 registered: kind=llm baseline=shoal
seat 3 registered: kind=scripted baseline=shoal
seat 2 registered: kind=scripted baseline=shoal
waiting for players: 4/4, need 0 more
the tank goes live in 1
the tank is live: 4 skimmers, 5 plankton, 8 poison blooms
```

Status: **TRUE** — `CLEAN`: zero matches for `falling back`, `LLM provider is unavailable`,
`cut off at max_tokens` or `rejected` across all 235 decoded lines of all four containers.
48 `bedrock_sidecar_call` / 48 `bedrock_sidecar_complete` with 0 errors exactly matches the replay's
48 llm intents and 0 fallbacks, so the two champion seats were genuinely served by Bedrock
(`claude-haiku-4-5`). The Bedrock-capacity carve-out was **not** invoked — no cross-coworld
comparison was needed because there is nothing to excuse.

## 6. The public page uses the static replay path — **TRUE**

Source (a): raw HTML of `https://softmax.com/walker-waterworld` — no iframe, as
`playbooks/observatory-api.md` §Featured match records for every coworld since 2026-08-22. Recorded as
*unknown*, not as a failure:
```
$ curl -sS "https://softmax.com/walker-waterworld" -o /tmp/v_page.html -w "HTTP=%{http_code} bytes=%{size_download}\n"
HTTP=200 bytes=580699
$ grep -o '<iframe[^>]*src="[^"]*"' /tmp/v_page.html || echo "(no match — page is client-rendered for the iframe)"
(no match — page is client-rendered for the iframe)
```
Source (b): the coworld detail API, whose `featured_match` is `null` platform-wide (also documented) —
useful here only because it proves **which** cow is canonical:
```
$ curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" | jq -c '(if type=="array" then . else .entries end)[]|select(.name=="walker-waterworld")|{id,version,canonical,replay_viewer,featured_match}'
{"id":"cow_36a12905-cdf6-4c9e-8bc4-2c0e541b9fb1","version":"0.1.1","canonical":true,"replay_viewer":null,"featured_match":null}
{"id":"cow_6f92bb4c-33b7-4119-876b-82c2f6ae5e93","version":"0.1.0","canonical":false,"replay_viewer":null,"featured_match":null}
```
**The stray-0.1.0 finding is benign:** `cow_6f92bb4c-…` (0.1.0) is `canonical: false`; the 0.1.1 cow is
the only canonical one, and everything below resolves to it.

Source (c) — **the one I used**: the featured match out of the page's **SSR payload**
(`state.playlist[0]`), which is what the page renders, plus the session call the page's own JS makes
to turn it into the iframe `src` (`playbooks/observatory-api.md` §Featured match, "Answered
(lighthouse run)"). SSR payload as it sits in the HTML (escaped, verbatim grep output, trimmed at the
`matchup` object which is quoted unescaped underneath):
```
$ grep -o 'playlist\\":\[.\{0,420\}' /tmp/v_page.html
playlist\":[{\"episodeId\":\"9c7211b8-68ff-460d-870a-81e47aa67f52\",\"coworldId\":\"cow_36a12905-cdf6-4c9e-8bc4-2c0e541b9fb1\",\"coworldName\":\"walker-waterworld\",\"coworldVersion\":\"0.1.1\",\"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/d28f4f1b-941e-478d-a418-4898fb1c19d6.replay\",\"finishedAt\":\"2026-08-26T12:04:47.070904Z\",\"roundNumber\":3,\"episodeNumber\":1,\"code\":\"walker-waterworld.r3.e1\",\"matc
```
Same entry unescaped (`python3` un-backslashing the same slice of `/tmp/v_page.html`), to show the
matchup:
```
playlist":[{"episodeId":"9c7211b8-68ff-460d-870a-81e47aa67f52","coworldId":"cow_36a12905-cdf6-4c9e-8bc4-2c0e541b9fb1","coworldName":"walker-waterworld","coworldVersion":"0.1.1","replayUrl":"https://softmax-public.s3.amazonaws.com/replays/d28f4f1b-941e-478d-a418-4898fb1c19d6.replay","finishedAt":"2026-08-26T12:04:47.070904Z","roundNumber":3,"episodeNumber":1,"code":"walker-waterworld.r3.e1","matchup":{"divisionId":"div_ef3424b8-a20d-4029-8918-e12b6fb65156","divisionName":"Competition","first":{"rank":1,"player_id":"ply_44ae9048-3242-4654-881f-6d9d43347fa3","player_name":"daveey","score":1000,"score_label":"MMR","score_value_type":"integer","rounds_played":2,"episode_wins":0,"episodes_played":null,"win_rate":0,"policy_label":"walker-waterworld-tandemhunt:v2","recent_rounds":null},"second":{"rank":2,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1","score":1000,"score_label":"MMR","score_value_type":"integer","rounds_played":2,"episode_wins":0,"episodes_played":null,"win_rate":0,"policy_label":"walker-waterworld-relay:v2","recent_rounds":null}},"inspectUrl":"/observatory/v2?tab=overview&detail=episode-request:ereq_0910faa4-4573-4486-b6e6-22ccaded84a0","outcome":null}]
```
```
$ curl -sS -X POST "$BASE/coworlds/replays/session" "${AUTH[@]}" -H 'content-type: application/json' \
    -d '{"coworld_id":"cow_36a12905-cdf6-4c9e-8bc4-2c0e541b9fb1","replay_uri":"https://softmax-public.s3.amazonaws.com/replays/d28f4f1b-941e-478d-a418-4898fb1c19d6.replay"}' -w "\nHTTP=%{http_code}\n"
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_36a12905-cdf6-4c9e-8bc4-2c0e541b9fb1/sha256%3A68bb2bd31430aa5ca2bef05502d31368d51e88014fd53a75255e1b7b3d9e7442/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fd28f4f1b-941e-478d-a418-4898fb1c19d6.replay&v=2","ready":true}
HTTP=200
```

Status: **TRUE** — a featured match is present (`walker-waterworld.r3.e1`, the round-3 episode, with
both ranked players in `matchup.first`/`matchup.second`) and it resolves to **`cow_36a12905-…` /
`0.1.1`**, not the stray 0.1.0. The iframe `src` is the **static** route
`…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` with `<sha>` = the coworld's
manifest hash `sha256:68bb2bd3…` (URL-encoded) exactly as STATE records it, and `ready: true`. It is
**not** a `/client/replay` pod URL. (The trailing `&v=2` is a cache-buster the platform appends; the
path is unchanged.) Source used: **(c)**, the SSR playlist + the page's own session call; (a) found
nothing and (b) is `null` platform-wide, both recorded above rather than scored as failures.

## 7. Certification declared the static bundle — **TRUE**

Read from **the committed `runs/2026-08-26-walker-waterworld/release-result.json`** (phase 40's
downloaded artifact of release run 32963420881); it was present, so the `gh run download` fallback was
**not** used.
```
$ jq -r '.certify.replay_liveness' runs/2026-08-26-walker-waterworld/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
$ jq -r '.certify.ok, .canonical, .version, .cow_id, .manifest_sha, .secret_put, .hosted_smoke' runs/2026-08-26-walker-waterworld/release-result.json
true
true
0.1.1
cow_36a12905-cdf6-4c9e-8bc4-2c0e541b9fb1
sha256:68bb2bd31430aa5ca2bef05502d31368d51e88014fd53a75255e1b7b3d9e7442
true
passed
```
Certification transcript tail from the same file (`.certify.output_tail`), the 10 steps:
```
  [pass] matriculate: manifest conforms to the Coworld schema
  [pass] source-resolves: … source_url that resolves to publicly accessible source
  [pass] images-reachable: every declared image is pullable or inspectable
  [pass] fixture-conforms: … validates against game.config_schema …
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

Status: **TRUE** — the required marker `Replay liveness: skipped (static replay bundle declared` is
present verbatim, and the `cow_id`/`manifest_sha` in the certification artifact are the same pair the
item-6 static URL uses.

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

*(a) Dispatch.* The `url` input is the **full iframe `src` from item 6**, `?replay=` and all.
```
$ SRC=$(cat /tmp/src.txt)   # the viewer_url from item 6
$ date -u +%FT%TZ ; gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
dispatch_at=2026-08-26T12:10:14Z
dispatched
$ gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 | jq -c 'sort_by(.createdAt)|reverse|.[0:3][]'
{"createdAt":"2026-08-26T12:10:17Z","databaseId":32967129036,"event":"workflow_dispatch","status":"in_progress"}
{"createdAt":"2026-08-26T06:19:23Z","databaseId":32937649794,"event":"workflow_dispatch","status":"completed"}
{"createdAt":"2026-08-26T05:27:08Z","databaseId":32934089374,"event":"workflow_dispatch","status":"completed"}
```
Run **32967129036** is the only run created after `12:10:14Z` (next-newest is 05:52 h older), so the
new-run identification is unambiguous — not "the latest run" taken blind.
```
$ gh run watch 32967129036 -R Metta-AI/coworld-builder --exit-status ; gh run view 32967129036 --json status,conclusion
{"conclusion":"success","status":"completed"}
$ gh run download 32967129036 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-26-walker-waterworld/viewer-check
-rw-r--r--  smoke-stderr.txt   (0 bytes)
-rw-r--r--  smoke-stdout.txt   (483 bytes)
-rw-r--r--  viewer-smoke.json  (1279 bytes)
-rw-r--r--  viewer-smoke.png   (402796 bytes)
```
(committed alongside this file, in `runs/2026-08-26-walker-waterworld/viewer-check/`)

*(b) Readouts, verbatim.*
```
$ jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-26-walker-waterworld/viewer-check/viewer-smoke.json
{"loaded":true,"ms":4431,"clock":"1:12 TIME LEFT","scorebug":"THE POD 0.000 4 SKIMMERS 0 NIBBLES 1:12 TIME LEFT CAUGHT 0 / 20 POISON 0 THRUST −0.00","feed_lines":0}
$ jq -c '.signals' runs/2026-08-26-walker-waterworld/viewer-check/viewer-smoke.json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":[],"bridge_ready":false,"bridge_error":[]}
$ jq -r '.failure // "no failure"' runs/2026-08-26-walker-waterworld/viewer-check/viewer-smoke.json
no failure
$ jq -r '.status, .loading_text, (.console_tail|tostring), (.canvas_text.total|tostring)' …/viewer-smoke.json
OPEN
null
[]
0
```
Three clock readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | clock readout |
|---|---|
| 0 %   | `1:12 TIME LEFT` |
| 50 %  | `0:35 TIME LEFT` |
| 100 % | `FINAL GAME OVER` |

All three differ, monotonically: full tank clock → half → the end card. `smoke-stdout.txt` verbatim:
```
{"loaded":true,"ms":4431,"clock":"1:12 TIME LEFT","scorebug":"THE POD 0.000 4 SKIMMERS 0 NIBBLES 1:12 TIME LEFT CAUGHT 0 / 20 POISON 0 THRUST −0.00","feed_lines":0}
scrub readouts: 0%="1:12 TIME LEFT"  50%="0:35 TIME LEFT"  100%="FINAL GAME OVER"
canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
```
`canvas text: 0 drawn` is expected for this tree and is documented in its own CI: chrome text is DOM,
not canvas-drawn (repo commit `f078434`, "r1-F18: say in ci.yml why the main viewer smoke prints
`canvas text: 0 drawn`"). `bridge_ready: false` with `data_replay_loaded: "true"` is the other of the
two accepted ready signals, so the loaded gate is satisfied by the DOM attribute.

**Item 8 gate: `loaded: true` ✅ (4431 ms to first frame) AND the three clock readouts differ ✅ → TRUE.**

*(c) The replay JSON the viewer was asked to draw* — `/tmp/ep.json` (decoded from `/tmp/ep.replay`,
item 4), ordered excerpts:
```
$ jq -r '.intents[]|select(.turn<=2)|[.turn,.alias,.source,.mode,.target,.partner,(.say//"")]|@tsv' /tmp/ep.json     # EARLY
0	SKIM-1	llm	avoid	none	SKIM-2	Poison nearby, avoiding to tank centre
0	SKIM-3	llm	sweep	none	none	LEFT sweep start, hunting zone partner support
0	SKIM-4	scripted	escort	none	SKIM-3	closing up
0	SKIM-2	scripted	escort	none	SKIM-1	closing up
1	SKIM-1	llm	avoid	none	SKIM-2	Avoiding poison P4, regrouping with partner SKIM
1	SKIM-3	llm	hunt	F1	none	F1 at 1.25m, SKIM-1 close. Hunt+pull. Go.
1	SKIM-4	scripted	avoid	none	none	poison, breaking off
1	SKIM-2	scripted	hunt	F1	SKIM-1	on it with two
2	SKIM-1	llm	avoid	none	SKIM-2	Evading poison P2, SKIM-2 hold position
2	SKIM-3	llm	avoid	none	none	Poison evasion, back to zone sweep after
2	SKIM-4	scripted	escort	none	SKIM-3	fetching my mate
2	SKIM-2	scripted	sweep	none	SKIM-1	sweeping

$ jq -r '.intents[]|select(.turn>=11 and .turn<=12)|…' /tmp/ep.json                                                  # MIDDLE
11	SKIM-1	llm	hunt	none	SKIM-2	Hunting plankton with SKIM-2 at 0.64m
11	SKIM-3	llm	avoid	none	none	P1 closing fast, avoiding now
11	SKIM-4	scripted	sweep	none	SKIM-3	sweeping
11	SKIM-2	scripted	sweep	none	SKIM-1	sweeping
12	SKIM-1	llm	hunt	F3	SKIM-2	F3 tight, waiting for SKIM-2 convergence
12	SKIM-3	llm	hunt	F1	none	F1 found, holding for partner arrival
12	SKIM-4	scripted	hold	none	none	shaking it off
12	SKIM-2	scripted	hunt	F5	SKIM-1	on it with two

$ jq -r '.intents[]|select(.turn>=22)|…' /tmp/ep.json                                                                # LATE
22	SKIM-1	llm	hunt	F1	SKIM-2	On F1 at 0.25m, waiting for partner
22	SKIM-3	llm	avoid	none	none	Poison P4 0.9mevade to centre, resuming patrol
22	SKIM-4	scripted	avoid	none	none	poison, breaking off
22	SKIM-2	scripted	avoid	none	none	poison, breaking off
23	SKIM-1	llm	hunt	F1	SKIM-2	F1 contact, holding position for SKIM-2
23	SKIM-3	llm	avoid	none	none	Evading P4, returning to right zone
23	SKIM-4	scripted	escort	none	SKIM-3	closing up
23	SKIM-2	scripted	escort	none	SKIM-1	closing up

$ tail -3 /tmp/vdec_game.log        # the hosted engine's own ending, same episode
SKIM-1 + SKIM-2 take plankton F1 — +10
game over: complete/full_time — captures 12, score 104.678
Events written: /coworld/events.json (366 events)
```

### Spectator-judgment paragraph

**It is legible, it moves, and it is unmistakably this game — in the starter's chrome.**
`viewer-smoke.png` (the 100 %-scrub frame CI captured, committed at
`runs/2026-08-26-walker-waterworld/viewer-check/viewer-smoke.png`) shows a complete spectator
experience: a **scorebug strip** across the top — `104.679 THE POD` on the left with
`4 SKIMMERS · 24 NIBBLES` beneath it, `FINAL / GAME OVER` centred, and `CAUGHT 12 / 20` on the right
over a twenty-pip progress bar with 12 lit, plus `POISON 5  THRUST −6.52`; an **endcard** over the
dimmed tank reading `12 CAUGHT · score 104.679`, a rule reminder banner
(`TWO SKIMMERS ON ONE PLANKTON AT THE SAME TICK — 20 CATCHES ENDS THE RUN EARLY AND WINS IT`), the
one-line summary `12 caught · 24 nibbles · 5 poison hits · thrust −6.52 — full time on the tank
clock`, and a **POD table** naming the four seats as a spectator needs them: `DAVEEY / SKIM-1` and
`DAVEEY-1 / SKIM-3` under an `LLM` header with `24/0` LLM-turn/fallback counters, and
`BASELINE / SKIM-4`, `BASELINE (2) / SKIM-2` with `0/0`, each row carrying AST/NIB/PSN/THR
(5·5·1·98 %, 7·6·0·97 %, 5·8·2·91 %, 7·5·2·92 %). Along the bottom is the paintbot-lineage
**transport strip** — reset, step-back, play, `+5s`, step, loop, fast-forward, a `spoilers` toggle, the
tick counter `1773 / 1776`, and `1× 2× 3× 4× 8× 16×` speed buttons — above a full-width **scrubber with
a momentum graph** labelled `LIVES LEAD`, whose staircase rises left-to-right with the playhead at the
right edge. This is the same chrome family as paintbot/raid/hive, not a lookalike rewrite: transport
strip, momentum scrubber, scorebug and endcard are all present and in their usual places.
**Motion is proven, not assumed:** the three DOM clock readouts advance `1:12 TIME LEFT` → `0:35 TIME
LEFT` → `FINAL GAME OVER` as the harness dragged `#scrub` from 0 % to 50 % to 100 %, and the first
frame drew in 4431 ms with `data-replay-loaded="true"`, `failure: null`, empty `console_tail`. **Picture
and record agree.** The endcard's numbers are the replay's `results` byte-for-byte (`captures 12`,
`sharedScore 104.679`, `nibbles 24`, `poisonHits 5`, `thrustCost 6.521`, `assists [5,7,5,7]`,
`thrustMeanPct [95,95,88,89]`, `llmTurns [24,24,0,0]`, `fallbackTurns [0,0,0,0]`, `finalTick 1776`), the
seat→alias mapping matches `aliases ["SKIM-1","SKIM-3","SKIM-4","SKIM-2"]` for
`names ["daveey","daveey-1","Baseline","Baseline (2)"]`, and the four intent captions legible in the
lower-right of the screenshot — `SKIM-1 HUNT "F1 contact, holding position for SKIM-2"`,
`SKIM-3 AVOID "Evading P4, returning to right zone"`, `SKIM-4 ESCORT "closing up"`,
`SKIM-2 ESCORT "closing up"` — are exactly the **turn-23** intents in the LATE excerpt above. So the
thing on screen is the thing that was recorded, and what it shows is the game the design promises:
paired captures (`SKIM-2 + SKIM-3 take plankton F1 — +10`) and poison stuns, with the two LLM seats
talking about partners and convergence while the two scripted Baselines say `closing up` / `sweeping`.
The picture is neither empty nor frozen nor unreadable.

**One legibility observation for the coordinator (not a check failure):** the harness reported
`feed_lines: 0`, yet the screenshot plainly shows four live intent captions. The feed exists and
renders; the harness's feed selector simply does not match this shell's node, so the count is an
instrumentation gap rather than a missing feed. A `#scrub` **was** present (the three readouts came
from dragging it), so the missing-scrubber branch does not apply. Second, minor: the harness's
first-frame `scorebug` string reads `THE POD 0.000 … CAUGHT 0 / 20 … THRUST −0.00` — correct for
tick 0, mentioned only so the zeros in the pasted JSON are not mistaken for an empty render; the same
scorebug reads `104.679 / CAUGHT 12 / 20` in the 100 % screenshot.

---

## Summary table

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** (rounds 2 @ 11:47:50Z, 3 @ 12:04:54Z; round 1 failed pre-filler, error quoted) |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** (daveey r1, daveey-1 r2, `rounds_played` 2 each; no filler rows) |
| 3 | Latest round's episode request completed w/ replay + participants | **TRUE** (`ereq_0910faa4…`, both champions non-filler, 2 `shoal:v2` fillers) |
| 4 | Replay bytes valid, protocol + reason + non-fallback decisions | **TRUE** (`walker-waterworld/v1`, `complete/full_time`, 48 llm intents, 0 fallbacks) |
| 5 | Hosted game log clean | **TRUE** (`CLEAN` over 235 decoded lines; 48/48 bedrock calls complete) |
| 6 | Public page uses the static replay path, featured match present | **TRUE** (`…/replays/static/cow_36a12905…/sha256%3A68bb2bd3…/index.html?replay=…`, `ready:true`; r3.e1 featured; 0.1.0 cow is `canonical:false`) |
| 7 | Certification declared the static bundle | **TRUE** (marker present in committed `release-result.json`) |
| 8 | Viewer executed and judged | **TRUE** (run 32967129036, `loaded:true` @4431 ms, three differing clocks, chrome matches the starter lineage) |

Replay (latest completed round): `https://softmax-public.s3.amazonaws.com/replays/d28f4f1b-941e-478d-a418-4898fb1c19d6.replay`
Iframe `src`: `https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_36a12905-cdf6-4c9e-8bc4-2c0e541b9fb1/sha256%3A68bb2bd31430aa5ca2bef05502d31368d51e88014fd53a75255e1b7b3d9e7442/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Fd28f4f1b-941e-478d-a418-4898fb1c19d6.replay&v=2`
viewer-check run: `32967129036`
