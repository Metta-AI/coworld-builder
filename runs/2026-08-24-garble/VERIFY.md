# VERIFY — garble   (2026-08-24T09:38Z)
Verdict: all-true (8/8 TRUE)

Run: `2026-08-24-garble` · coworld `cow_cb2293f4-2825-41d3-831b-7f3a690474a6` v0.1.1 ·
league `league_4eb352ae-4a7e-42a2-a7a2-6b3a23dc0b4a` · division `div_6540c330-b71d-4663-ac20-13929cd7e160`.

Every block below is the request actually made this run and the bytes actually returned.
Headers are named, never their values: `Authorization: Bearer $SOFTMAX_TOKEN`,
`User-Agent: coworld-builder/1.0`, and on artifacts `X-Use-Elevated-Privileges: true`.
Two documented exceptions to "fetched live this run": item 7 (reads the committed
`release-result.json`) and item 8 (reads the artifact of a `viewer-check.yml` run dispatched
during this phase).

Shape quirk handled everywhere, as briefed: `/leagues`, `/divisions/$D/leaderboard` return bare
arrays; `/rounds` returned `{entries:[…]}`. All jq below uses
`if type=="array" then . else .entries end`.

---

## 1. ≥2 completed rounds after fillers were set

**Poll history** (5-minute cadence, 75-minute bound started 2026-08-24T09:00Z, expiry 10:15Z):

| poll (UTC) | completed rounds | detail |
|---|---|---|
| 09:00:15 | 1 | round 1 completed 08:58:13Z |
| 09:06:33 | 1 | unchanged |
| 09:11:29 | 1 | unchanged |
| 09:16:30 | 2 | **round 2** completed 09:16:07Z |
| 09:22:31 | 2 | unchanged |
| 09:27:25 | 2 | unchanged |
| 09:32:19 | 3 | **round 3** completed 09:31:06Z |

Final fetch:

```
GET https://softmax.com/api/observatory/v2/rounds?league_id=league_4eb352ae-4a7e-42a2-a7a2-6b3a23dc0b4a&limit=20
  -H Authorization -H User-Agent          (fetched 2026-08-24T09:32:26Z)
```

```bash
jq -r '(if type=="array" then . else .entries end)|[.[]|select(.status=="completed")]|length'
```
```
3
```

```bash
jq '(if type=="array" then . else .entries end)|[.[]|{id,round_number,status,error,completed_at}]'
```
```json
[
  {"id":"round_16088d65-970f-42ce-abb6-59247227dda0","round_number":3,"status":"completed",
   "error":null,"completed_at":"2026-08-24T09:31:06.683749Z"},
  {"id":"round_03e2ecd1-e706-443b-9075-8590f7621026","round_number":2,"status":"completed",
   "error":null,"completed_at":"2026-08-24T09:16:07.174310Z"},
  {"id":"round_d007efbe-cfae-41bb-8b25-d5b7fd6fbc3a","round_number":1,"status":"completed",
   "error":null,"completed_at":"2026-08-24T08:58:13.649031Z"}
]
```

No round has status `failed` or `discarded`; `error` is `null` on all three.

**Fillers were registered before round 1**, so all three completed rounds are "after the fillers
were set". Two independent pieces of evidence, both fetched this run:

```
GET .../leagues/league_4eb352ae-…/filler-policies   -H Authorization -H User-Agent -H X-Use-Elevated-Privileges
```
```json
{"filler_policy_versions":[
 {"policy_version_id":"bde285de-6d42-4d6f-a4bc-f7f9b96f8e76","policy_name":"garble-quoter","version":1,
  "player_name":"daveey"},
 {"policy_version_id":"bbe732d1-5559-4e28-8f7c-05f91f75fa7b","policy_name":"garble-shark","version":1,
  "player_name":"daveey"}]}
```

and round 1's own episode request, **created 08:58:02.288Z**, already seats both filler versions:

```
GET .../episode-requests/ereq_79eb44a8-0223-4662-862c-81bc6fbbff75
```
```json
{"created_at":"2026-08-24T08:58:02.288214Z",
 "participants":[
  {"position":0,"policy_name":"garble-signal","player_name":"daveey","is_filler":false},
  {"position":1,"policy_name":"garble-shortwave","player_name":"daveey-1","is_filler":false},
  {"position":2,"policy_name":"garble-quoter","player_name":"daveey","is_filler":true},
  {"position":3,"policy_name":"garble-quoter","player_name":"daveey","is_filler":true},
  {"position":4,"policy_name":"garble-quoter","player_name":"daveey","is_filler":true}]}
```

A filler seat cannot exist before the filler list exists, so registration preceded 08:58:02Z —
i.e. before round 1 was built. (`log.md` line "08:59:30 POST filler-policies" is a back-dated
coordinator note; the API timestamps above are the authority and they are consistent with the
brief's "registered BEFORE the first trigger".)

**Recorded verbatim, not hidden:** round 1 is a *hollow* completion. Its single episode request
returned `status: "completed"` seven seconds after creation with `replay_url: null`,
`participant_scores: []`, and all three artifact routes 404:

```
GET .../episode-requests/ereq_79eb44a8-…/artifacts/results  -> 404 {"detail":"No results found for job 5945e3e3-4d13-4a2b-91a2-8fb3f62f9fcb"}
GET .../episode-requests/ereq_79eb44a8-…/artifacts/replay   -> 404 {"detail":"No replay found for job 5945e3e3-4d13-4a2b-91a2-8fb3f62f9fcb"}
GET .../episode-requests/ereq_79eb44a8-…/artifacts/logs     -> 404 {"detail":"No logs found for job 5945e3e3-4d13-4a2b-91a2-8fb3f62f9fcb"}
```
It is also why the leaderboard shows `rounds_played: 2`, not 3.

Rounds **2** and **3** are substantive: each has one completed episode request with a non-null
`replay_url`, and both champions' `rounds_played` moved 0 → 1 → 2 across them.

- round 2 → `ereq_f12e854e-8f80-4646-a6c9-881076becbba`, `replay_url` `…/48686b54-3a3e-4d9d-8cc6-db8df95c8e91.replay`
- round 3 → `ereq_00f32fd9-cab8-456f-bd8c-8037f601dec0`, `replay_url` `…/f062ea29-ad73-435c-ba67-716c89c50095.replay`

**Status: TRUE** — 3 rounds `completed` (≥ 2), all after filler registration (08:58:02Z at the
latest); 2 of them (rounds 2 and 3, completed 09:16:07Z and 09:31:06Z) carry real scored episodes,
so the requirement holds on the strict reading as well as the literal count. Round 1's empty
completion is recorded above for the coordinator; no round is `failed`/`discarded`.

---

## 2. Both champions ranked, fillers absent/Baseline

```
GET https://softmax.com/api/observatory/v2/divisions/div_6540c330-b71d-4663-ac20-13929cd7e160/leaderboard
  -H Authorization -H User-Agent          (fetched 2026-08-24T09:32:33Z)
```

```bash
jq -r '(if type=="array" then . else .entries end)[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
```
```
1	daveey-1	garble-shortwave:v1	1016.0	2	1.0
2	daveey	garble-signal:v1	984.0	2	0.0
```

Row count: `jq 'length'` → `2`. Raw first row, unedited:

```json
{"rank":1,"player_id":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d","player_name":"daveey-1",
 "score":1016.0,"score_label":"Elo","score_value_type":"integer","rounds_played":2,
 "episode_wins":1.0,"episodes_played":null,"win_rate":0.5,"policy_label":"garble-shortwave:v1",
 "recent_rounds":null}
```

Both champions present: `daveey` (`garble-signal:v1`) and `daveey-1` (`garble-shortwave:v1`),
each `rounds_played = 2 ≥ 1`. Elo has separated from the 1000 seed (1016 / 984), so scoring is
live. Neither `garble-quoter` nor `garble-shark` appears — the fillers are **absent** from the
leaderboard, which is the permitted outcome.

**Status: TRUE**

---

## 3. Latest round's episode request completed with a replay and the right participants

```bash
R=$(curl -sS "$BASE/rounds?league_id=$L&limit=20" "${AUTH[@]}" \
    | jq -r '(if type=="array" then . else .entries end)|[.[]|select(.status=="completed")]|max_by(.round_number).id')
# R=round_16088d65-970f-42ce-abb6-59247227dda0   (round 3)
GET .../episode-requests?round_id=round_16088d65-970f-42ce-abb6-59247227dda0&limit=20
```
```json
[{"id":"ereq_00f32fd9-cab8-456f-bd8c-8037f601dec0","status":"completed",
  "replay_url":"https://softmax-public.s3.amazonaws.com/replays/f062ea29-ad73-435c-ba67-716c89c50095.replay"}]
```

```
GET .../episode-requests/ereq_00f32fd9-cab8-456f-bd8c-8037f601dec0
  -H Authorization -H User-Agent          (fetched 2026-08-24T09:32:37Z)
jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/f062ea29-ad73-435c-ba67-716c89c50095.replay",
  "participants": [
    {"position":0,"policy_name":"garble-signal","version":1,"player_name":"daveey","is_filler":false},
    {"position":1,"policy_name":"garble-shortwave","version":1,"player_name":"daveey-1","is_filler":false},
    {"position":2,"policy_name":"garble-quoter","version":1,"player_name":"daveey","is_filler":true},
    {"position":3,"policy_name":"garble-shark","version":1,"player_name":"daveey","is_filler":true},
    {"position":4,"policy_name":"garble-quoter","version":1,"player_name":"daveey","is_filler":true}
  ],
  "participant_scores": [
    {"position":0,"score":1.0},
    {"position":1,"score":1.1027777777777779},
    {"position":2,"score":1.0434782608695652},
    {"position":3,"score":1.0763157894736841},
    {"position":4,"score":1.0}
  ]
}
```

`status == "completed"`; `replay_url` non-null; seat 0 = `daveey`, seat 1 = `daveey-1`, both
`is_filler: false`; seats 2–4 are the registered fillers and are labelled `Baseline`,
`Baseline (2)`, `Baseline (3)` in the replay's `policyNames` (see item 4). Five scores returned.

**Status: TRUE**

---

## 4. Replay bytes are valid and show the game

```
GET https://softmax-public.s3.amazonaws.com/replays/f062ea29-ad73-435c-ba67-716c89c50095.replay
  (curl -sSL, no auth)                    (fetched 2026-08-24T09:32:5xZ)
```
```
[http 200] bytes=31266
```

```bash
jq -e . /tmp/ep.replay >/dev/null && echo "strict UTF-8 JSON: ok"
```
```
strict UTF-8 JSON: ok
```

```bash
jq -r '.protocol'        ->  garble.replay.v1
jq -r '.results.reason'  ->  complete
jq -c '.config'          ->  {"turns":12,"seed":2120558480,"noiseScale":1.0,"sampled":true,
                              "commodities":["ORE","OAT","TIN","TAR"],"airtimeBudget":900}
jq -c '.names'           ->  ["Ratchet","Widget","Gasket","Rivet","Sprocket"]
jq -c '.policyNames'     ->  ["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)"]
jq -r '.events|length'   ->  112
```

**Protocol match.** The manifest served by the platform declares no separate replay-protocol
string (`jq 'paths|select(test("protocol";"i"))'` on `GET /coworlds/cow_cb2293f4-…` yields only
`manifest.game.protocols.player` and `.global`; the player protocol's value contains
`garble.player.v1`). The replay protocol id is fixed by the design note and by the shipped code:

- `runs/2026-08-24-garble/design.md:735` — ``{"protocol":"garble.replay.v1", …}``
- `cogame-garble/src/garble/server.nim:607` — `"protocol": payload{"protocol"}.getStr("garble.replay.v1")`
- `cogame-garble/replay-viewer/garble_replay.nim:46` — same literal

The fetched bytes carry exactly `garble.replay.v1`. Match confirmed.

**`results.reason == "complete"`** — the design's expected value for a standard-variant episode
(`design.md` §Results: `"reason":"complete|deadline"`). No `deadline` exception is being invoked.

```bash
jq -c '.results' /tmp/ep.replay
```
```json
{"names":["daveey","daveey-1","Baseline","Baseline (2)","Baseline (3)"],
 "scores":[1.0,1.1027777777777779,1.0434782608695652,1.0763157894736841,1.0],
 "portfolio":[380,397,480,409,380],"hold":[380,360,460,380,380],"cash":[120,10,45,305,120],
 "units":[[20,0,0,0],[0,0,20,7],[0,20,0,5],[0,0,0,8],[20,0,0,0]],
 "deals":[0,2,1,3,0],"misheard":[0,0,0,0,0],"voids":[2,6,1,5,2],
 "airtimeUsed":[378,509,335,392,335],"turns":12,"maxTurns":12,"reason":"complete"}
```

**Decisions and fallbacks.** The prompt's jq (`.type=="decision"`, `.fallback==true`) matches
nothing here: this replay's events key their kind as `kind` and mark scripted output as
`scripted`. Adapted, and the adaptation stated so it can be checked:

```bash
jq -r '[.events[]|select(.kind=="say")]|length'                      -> 60
jq -r '[.events[]|select(.kind=="say" and .scripted==true)]|length'  -> 36
jq -r '[.events[]|select(.kind=="say")]|group_by(.seat)
        |map({seat:.[0].seat,says:length,scripted:([.[]|select(.scripted==true)]|length)})'
```
```json
[{"seat":0,"says":12,"scripted":0},
 {"seat":1,"says":12,"scripted":0},
 {"seat":2,"says":12,"scripted":12},
 {"seat":3,"says":12,"scripted":12},
 {"seat":4,"says":12,"scripted":12}]
```

The 36 scripted lines are **all three filler seats** (2, 3, 4) — `garble-quoter` and
`garble-shark` are scripted baselines by design; scripted is what they are, not a degradation.
**The two champion seats have 0 scripted lines out of 24**: fallbacks among champion decisions are
zero, which is a small minority by any reading.

Champion decisions are non-trivial and on-game (LLM-authored trade offers with the design's
repeat-the-field noise discipline visible):

```bash
jq -r '[.events[]|select(.kind=="say" and (.seat==0 or .seat==1))][0:6]|.[]
       |"turn=\(.turn) seat=\(.seat) ch=\(.channel) scripted=\(.scripted) ticket=\(.ticket) text=\"\(.text)\""'
```
```
turn=0 seat=0 ch=-1 scripted=false ticket=1  text="SELL 5 ORE AT 10"
turn=0 seat=1 ch=-1 scripted=false ticket=2  text="BUY 10 TAR AT 11"
turn=1 seat=0 ch=-1 scripted=false ticket=6  text="BUY 10 10 TAR TAR AT 11 11"
turn=1 seat=1 ch=0  scripted=false ticket=7  text="BUY 12 TAR AT 11"
turn=2 seat=0 ch=-1 scripted=false ticket=11 text="SELL 4 4 TAR TAR AT 13 13"
turn=2 seat=1 ch=0  scripted=false ticket=12 text="BUY 12 TAR AT 11"
```

`ch=-1` is the RADIO (all four hear it); `ch=0` is a private line to seat 0 — both channel modes
in use. Doubled tokens (`10 10 TAR TAR`) are the champion repeating fields against interference,
which is the game. Event-kind census:
`say=60 turn=12 confirm=19 void=16 deal=3 start=1 end=1`.

**Status: TRUE** — strict-parser-valid UTF-8 JSON, `protocol` = `garble.replay.v1` as declared,
`results.reason` = `complete`, 24 champion decisions with **zero** fallbacks.

---

## 5. Hosted game log is clean

```
GET .../episode-requests/ereq_00f32fd9-cab8-456f-bd8c-8037f601dec0/artifacts/logs
  -H Authorization -H User-Agent -H X-Use-Elevated-Privileges     (fetched 2026-08-24T09:33:20Z)
[http 200] bytes=57836
```

The body is python `b'…'` byte-string reprs under `===== container: … =====` headers, so it was
decoded per-repr with `ast.literal_eval` before grepping (per `playbooks/observatory-api.md` §10 —
line-based greps undercount otherwise). Containers present: `coworld-init-config`,
`bedrock-sidecar`, `game`, `worker`. Decoded size 56 980 bytes / 216 lines.

```bash
grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs_final.txt
```
```
0
CLEAN
```

Cross-check against the **undecoded** bytes, in case decoding hid a line:

```bash
grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' logs_final.raw
```
```
0
```

Zero matches on both, so the brief's `garble llm: seat N falling back to scripted` reconciliation
is not needed: **no scripted-fallback line was emitted at all** this episode, consistent with item
4's zero champion fallbacks.

Representative decoded `game` container excerpt (start, one mid-episode turn, shutdown):

```
===== container: game =====
garble: seats=5 turns=12 noiseScale=1.0 model=claude-sonnet-5
garble: player slot 0 connected (1/5)
garble: slot 0 delivered a prompt (1376 runes)
garble: slot 4 delivered a prompt (848 runes, scripted quoter)
garble: slot 3 delivered a prompt (848 runes, scripted shark)
garble: starting with 5/5 players connected
garble llm: bedrock transport, model us.anthropic.claude-haiku-4-5-20251001-v1:0, url http://127.0.0.1:9100/model/…/invoke
garble: episode timeout 1200s (assumed); playing until 720s
garble: turn 0 of 12 interference 0.3 at 5s
garble: Ratchet ▸ RADIO: "SELL 5 ORE AT 10"
garble: Widget ▸ RADIO: "BUY 10 TAR AT 11"
…
garble: turn 8 of 12 interference 0.95 BURST at 94s
garble: Ratchet ▸ RADIO: "BUY 12 12 TAR TAR AT 19 19"
garble: Widget ▸ LINE→Sprocket: "BUY 6 TIN AT 11"
…
garble: writing results and replay
garble: artifacts written; 20s shutdown grace
garble: episode complete, shutting down
```

**Recorded, not swept up:** one line the grep does not match and that is not a fallback —

```
garble: turn 2 of 12 interference 0.95 BURST at 25s
garble llm: seat 0 attempt 0 failed: input(7, 1) Error: EOF expected
garble: Ratchet ▸ RADIO: "SELL 4 4 TAR TAR AT 13 13"
```

A single malformed-JSON reply on attempt 0 that the retry recovered: seat 0 still transmitted an
LLM line on that turn (`scripted=false` for all 12 of its says, item 4). It is a retry, not a
degrade, and it matches none of the four forbidden patterns. Also present are five
`Dropped message to disconnected client` lines during the 20 s shutdown grace — normal teardown,
also not a forbidden pattern.

**Status: TRUE — CLEAN** (0 matches decoded, 0 matches raw).

---

## 6. The public page uses the static replay path

**Source (a): the raw page.** Attempted first, as the prompt requires.

```
GET https://softmax.com/garble                       (fetched 2026-08-24T09:33:29Z)
[http 200] bytes=487445
grep -o '<iframe[^>]*src="[^"]*"'  ->  (no match)
```
Not a false negative — the page is client-rendered for the iframe (documented platform-wide in
`playbooks/observatory-api.md` §Featured match, lighthouse run 2026-08-22).

**Source (b): the SSR payload the page ships, `state.playlist[0]`** — the featured match:

```json
{"episodeId":"53b8371a-7707-4287-be83-3bc2fa260189",
 "coworldId":"cow_cb2293f4-2825-41d3-831b-7f3a690474a6","coworldName":"garble",
 "coworldVersion":"0.1.1",
 "replayUrl":"https://softmax-public.s3.amazonaws.com/replays/f062ea29-ad73-435c-ba67-716c89c50095.replay",
 "finishedAt":"2026-08-24T09:30:56.428756Z","roundNumber":3,"episodeNumber":1,
 "code":"garble.r3.e1",
 "matchup":{"divisionId":"div_6540c330-b71d-4663-ac20-13929cd7e160","divisionName":"Competition",
   "first":{"rank":1,"player_name":"daveey-1","score":1016,"rounds_played":2,"episode_wins":1,
            "win_rate":0.5,"policy_label":"garble-shortwave:v1"},
   "second":{"rank":2,"player_name":"daveey","score":984,"rounds_played":2,"episode_wins":0,
            "win_rate":0,"policy_label":"garble-signal:v1"}}}
```

A featured match **is** present (`garble.r3.e1`), it is the round-3 episode of item 3, and its
matchup names both champions.

**Source (c): the call the page's own JS makes for the iframe `src`.**

```
POST https://softmax.com/api/observatory/v2/coworlds/replays/session
  -H Authorization -H User-Agent -H content-type
  -d {"coworld_id":"cow_cb2293f4-2825-41d3-831b-7f3a690474a6",
      "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/f062ea29-ad73-435c-ba67-716c89c50095.replay"}
                                                     (fetched 2026-08-24T09:33:37Z)
[http 200]
```
```json
{"viewer_url":"https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_cb2293f4-2825-41d3-831b-7f3a690474a6/sha256%3A41c6b5f1c725f042aa93bf56748e906b5218fede82b16156c18010549321a012/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Ff062ea29-ad73-435c-ba67-716c89c50095.replay&v=2",
 "ready":true}
```

The path is `/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`. `<sha>` is
`sha256:41c6b5f1c725f042aa93bf56748e906b5218fede82b16156c18010549321a012`, URL-encoded — identical
to `STATE.coworld.manifest_sha`. `ready: true`. **No `/client/replay` pod URL anywhere.**

For completeness, the coworld row (also fetched this run) — `replay_viewer` and `featured_match`
are `null`, which is the documented platform-wide behaviour of that endpoint and is *not* used as
evidence either way here:

```bash
curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
 | jq -r '(if type=="array" then . else .entries end)|.[]|select(.name=="garble")|{id,canonical,version,replay_viewer,featured_match}'
```
```json
{"id":"cow_cb2293f4-2825-41d3-831b-7f3a690474a6","name":"garble","canonical":true,
 "version":"0.1.1","replay_viewer":null,"featured_match":null}
```

**Sources used: (a) raw HTML — empty, treated as unknown; (b) the page's SSR `state.playlist[0]`
for the featured match; (c) `POST /coworlds/replays/session` for the iframe `src`.**

**Status: TRUE** — featured match present, iframe `src` is the static route with the manifest sha,
`ready: true`.

---

## 7. Certification declared the static bundle

Source: **the committed `runs/2026-08-24-garble/release-result.json`** (the artifact phase 40
downloaded at 08:55:45Z from release run 32708082253). It was present; no re-download from
`gh run download` was needed, and `/tmp` was not consulted.

```bash
jq -r '.certify.replay_liveness' runs/2026-08-24-garble/release-result.json
```
```
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)
```

Contains the required `Replay liveness: skipped (static replay bundle declared` exactly.
Surrounding certification transcript from the same file (`.certify.output_tail`), all ten steps
passed:

```
Certifying dist/coworld_manifest.json against transcript coworld-executable
  [pass] matriculate: manifest conforms to the Coworld schema
  [pass] source-resolves: … source_url that resolves to publicly accessible source
  [pass] images-reachable: every declared image is pullable or inspectable
  [pass] fixture-conforms: the certification fixture validates against game.config_schema …
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
(`jq -r '.certify.ok'` → `true`.)

**Status: TRUE**

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged

**(a) Dispatch.** The URL is the item-6 iframe `src`, verbatim, `?replay=` and all.

```bash
# dispatch_at = 2026-08-24T09:33:46Z
gh workflow run viewer-check.yml -R Metta-AI/coworld-builder \
  -f url='https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_cb2293f4-2825-41d3-831b-7f3a690474a6/sha256%3A41c6b5f1c725f042aa93bf56748e906b5218fede82b16156c18010549321a012/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2Ff062ea29-ad73-435c-ba67-716c89c50095.replay&v=2' \
  -f timeout=90

gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
  | jq -c 'sort_by(.createdAt)|reverse|.[0:3][]'
```
```json
{"createdAt":"2026-08-24T09:33:48Z","databaseId":32712220489,"event":"workflow_dispatch","status":"in_progress"}
{"createdAt":"2026-08-24T09:29:59Z","databaseId":32711872593,"event":"workflow_dispatch","status":"completed"}
{"createdAt":"2026-08-24T09:20:26Z","databaseId":32710988177,"event":"workflow_dispatch","status":"completed"}
```
Selected by `createdAt` **after** the dispatch time (09:33:48Z > 09:33:46Z), not by "the latest run":
**run 32712220489**. Two older `viewer-check` runs (09:29:59Z, 09:20:26Z) belong to other runs in
flight and were correctly not taken.

```bash
gh run watch 32712220489 -R Metta-AI/coworld-builder --exit-status
gh run view  32712220489 -R Metta-AI/coworld-builder --json status,conclusion
```
```
✓ viewer-check in 35s (ID 97385883002)   — all steps ✓, including "Fail if the viewer did not load"
{"status":"completed","conclusion":"success"}
```

```bash
gh run download 32712220489 -R Metta-AI/coworld-builder -n viewer-check -D runs/2026-08-24-garble/viewer-check
```
```
runs/2026-08-24-garble/viewer-check/viewer-smoke.json   1297 B
runs/2026-08-24-garble/viewer-check/viewer-smoke.png  324495 B
runs/2026-08-24-garble/viewer-check/smoke-stdout.txt    495 B
runs/2026-08-24-garble/viewer-check/smoke-stderr.txt      0 B
```

**(b) The readouts, verbatim from the artifact.**

```bash
jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-24-garble/viewer-check/viewer-smoke.json
```
```json
{"loaded":true,"ms":1176,"clock":"TURN 1 / 12 · HAZY 30%","scorebug":"daveey 300 CREDITS 1.00× daveey-1 300 CREDITS 1.00× Gasket 380 CREDITS 1.00× Rivet 360 CREDITS 1.00× Sprocket 300 CREDITS 1.00×","feed_lines":325}
```

```bash
jq -c '.signals' runs/2026-08-24-garble/viewer-check/viewer-smoke.json
```
```json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}
```

```bash
jq -r '.failure // "no failure"' runs/2026-08-24-garble/viewer-check/viewer-smoke.json
```
```
no failure
```

Three clock readouts (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`), the scrubber clicked at 0 / 50 / 100 %
of its width with a 700 ms settle:

| scrub position | `#clock` readout |
|---|---|
| 0 %   | `TURN 1 / 12 · HAZY 30%` |
| 50 %  | `TURN 1 / 12 · HAZY 30% · WAITING ON 5` |
| 100 % | `FINAL — DAVEEY-1 1.10×` |

All three strings differ. Also from the artifact: `status: "REPLAY"`, `loading_text: "LOADING
REPLAY…"` (the element exists but the page is past it — `data-replay-loaded="true"`),
`console_tail: ["[bridge] loading","[bridge] ready"]`, `bundle: null`, `replay: null`,
`soak: null` (the workflow was dispatched without a soak).

**Item-8 gate:** `loaded: true` ✅ and the three readouts differ ✅ → **TRUE**.

*Legibility observation for the coordinator (not a blocker):* the 50 % readout still shows
`TURN 1 / 12`. The `#scrub` element is present — `viewer_smoke.mjs` only populates a `scrub` array
when `document.querySelector("#scrub")` matches, and the array is populated with three entries and
no `error` key — and the 0 % → 100 % transition is unambiguous, so the viewer demonstrably
advances; but a mid-bar click
either re-animates from the head or needs longer than the harness's 700 ms to settle, so the
mid-point sample under-reports. Worth a look in a future phase-30 pass; it is not evidence of a
frozen viewer, because the end state below matches the recorded episode exactly.

**(c) The replay JSON the viewer was asked to draw** — ordered excerpts from `/tmp/ep.replay`
(the item-4 bytes), `[turn, seat, kind, text/reason]`:

*Early*
```
		start	
0		turn	
0	0	say	SELL 5 ORE AT 10
0	1	say	BUY 10 TAR AT 11
0	2	say	SELL 5 OAT AT 16
0	3	say	SELL 5 TAR AT 15
0	4	say	SELL 5 ORE AT 12
1		turn	
1	0	say	BUY 10 10 TAR TAR AT 11 11
1	1	say	BUY 12 TAR AT 11
1	2	say	SELL 5 5 OAT OAT AT 16 16
1	3	say	SELL 5 TAR AT 14
1	4	say	SELL 5 5 ORE ORE AT 13 13
1	0	confirm	
```

*Middle (events 50–62 of 112)*
```
5	1	say	BUY 12 TAR AT 10
5	2	say	SELL 5 OAT AT 17
5	3	say	SELL 5 TAR AT 16
5	4	say	SELL 5 ORE AT 16
5	3	confirm	
5	3	void	inadmissible
6		turn	
6	0	say	BUY 12 12 TAR TAR AT 13 13
6	1	say	BUY 12 TAR AT 10
6	2	say	SELL 5 OAT AT 16
6	3	say	SELL 5 TAR AT 15
6	4	say	SELL 5 ORE AT 16
6	1	confirm	
```

*Late*
```
10	4	say	SELL 5 ORE AT 17
10	1	confirm	
10	1	void	inadmissible
11		turn	
11	0	say	SELL 12 12 TAR TAR AT 13 13
11	1	say	BUY 12 TAR AT 13
11	2	say	SELL 5 5 OAT OAT AT 20 20
11	3	say	SELL 5 TAR AT 16
11	4	say	SELL 5 5 ORE ORE AT 16 16
11	1	confirm	
11	1	void	inadmissible
12		end	complete
```

The three deals actually struck:
```json
[{"kind":"deal","turn":1,"ticket":4, "seller":3,"buyer":2,"commodity":3,"qty":5,"fill":5,"price":15,"partial":false,"misheard":false,"cash":75},
 {"kind":"deal","turn":6,"ticket":29,"seller":3,"buyer":1,"commodity":3,"qty":5,"fill":5,"price":16,"partial":false,"misheard":false,"cash":80},
 {"kind":"deal","turn":7,"ticket":34,"seller":3,"buyer":1,"commodity":3,"qty":5,"fill":2,"price":15,"partial":true, "misheard":false,"cash":30}]
```

### Spectator-judgment paragraph

**It is legible, and it shows the game.** The screenshot
(`runs/2026-08-24-garble/viewer-check/viewer-smoke.png`, 1280×800, taken after the 100 % scrub) is
a fully-drawn frame, not an empty canvas and not a loading spinner. Top-left is the wordmark
**GARBLE**; top-right `REPLAY` and a `« LOG` toggle. Directly under it runs the **scorebug strip**
with all five seats, their credits and their multipliers —
`daveey 380 CREDITS 1.00× · daveey-1 397 CREDITS 1.10× · Gasket 480 CREDITS 1.04× · Rivet 409
CREDITS 1.08× · Sprocket 380 CREDITS 1.00×` — each with a small segmented momentum bar. Those five
numbers are exactly `results.portfolio` `[380,397,480,409,380]` and `results.scores`
`[1.00,1.10,1.04,1.08,1.00]` from the replay bytes above, so picture and record agree. Note this
differs from the `scorebug` string in `viewer-smoke.json` (`… 300 CREDITS 1.00× …`), which was
sampled at first frame — the two together are independent proof that the board **moved** between
load and the end of the scrub. Below that is Garble's own game block: the **interference meter**, a
drawn curve labelled `STATIC BURST` on the left and `50% ROUGH` on the right with a `RADIO` marker
riding it; five cog sprites arranged around the board with channel chips (`RADIO`, `LEADS`) above
them and per-seat credit/multiplier captions; and the **SAID-vs-HEARD panel**, headed
`SPROCKET ▸ RADIO`, showing `SAID: SELL 5 5 …` and then one HEARD row per listener — `daveey`,
`daveey-1`, `Gasket`, each with red static blocks standing in for the words that dropped or swapped
on their own copy of the line — plus a `TICKET #60` badge on the right. That panel is the whole
premise of the coworld rendered directly. Along the bottom: a three-line deal feed
(`#4 Rivet sold 5 TAR to Gasket at 15`, `#29 Rivet sold 5 TAR to daveey-1 at 16`,
`#34 Rivet sold 2 TAR to daveey-1 at 15 (partial 2/5)`) — which is precisely the three `deal`
events listed above, tickets 4/29/34, including the partial fill — a price strip
(`ORE 13 ▼ OAT 17 ▲ TIN 12 ▲ TAR 13 =`), and the **transport strip**: a play button, a wide
scrubber ticked in colour per event, `112 / 112` (the replay has exactly 112 events) and a
`♪ STATIC` audio toggle. Centred over all of it is the **endcard**: `FINAL — 12 TURNS /
DAVEEY-1 LEADS THE TABLE` and a five-row table with `SCORE / CREDITS / DEALS / MISHEARD / AIRTIME
USED` — `daveey-1 1.10× 397 2 0 509`, `Rivet 1.08× 409 3 0 392`, `Gasket 1.04× 480 1 0 335`,
`daveey 1.00× 380 0 0 378`, `Sprocket 1.00× 380 0 0 335` — each column matching
`results.deals [0,2,1,3,0]`, `results.misheard [0,0,0,0,0]` and `results.airtimeUsed
[378,509,335,392,335]` row for row. Nothing is empty, frozen or unreadable; a spectator can read
who won, by how much, on how many deals, and how much airtime it cost them.

**Does it look like the babel-lineage starter chrome?** Yes. The transport strip with the play
button and the per-event colour-ticked scrubber, the top scorebug with momentum bars, the bottom
feed and the centred final-table endcard are the paintbot/raid/hive family furniture in the same
places; Garble's additions sit *inside* that shell rather than replacing it — the interference
meter above the board, the channel chips, the price strip, and the SAID-vs-HEARD panel. This is not
a cogame-gridlock-style rewrite that merely reuses the ids.

**Status: TRUE** — `loaded: true`, three differing clock readouts, a rendered frame that reconciles
line-by-line with the replay's `results` and `deal` events.

---

## Summary

| # | Check | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers were set | **TRUE** (3 completed; 2 & 3 scored; fillers registered ≤08:58:02Z) |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** (daveey-1 1016 / daveey 984, `rounds_played` 2 each; fillers absent) |
| 3 | Latest round's episode completed with replay + participants | **TRUE** (`ereq_00f32fd9…`, round 3) |
| 4 | Replay bytes valid, protocol match, `complete`, non-fallback | **TRUE** (`garble.replay.v1`, 24 champion says, 0 scripted) |
| 5 | Hosted game log clean | **TRUE — CLEAN** (0 matches decoded, 0 raw) |
| 6 | Public page uses the static replay path | **TRUE** (static route + manifest sha, `ready:true`; featured match `garble.r3.e1`) |
| 7 | Certification declared the static bundle | **TRUE** (committed `release-result.json`) |
| 8 | Viewer executed and judged | **TRUE** (`loaded:true`, 3 differing readouts, run 32712220489) |

**Verdict: all-true.**

Two items recorded for the coordinator, neither blocking:
1. **Round 1 was a hollow completion** — `status: completed` in 7 s with `replay_url: null`,
   `participant_scores: []` and 404 on all three artifact routes. Rounds 2 and 3 are the two
   substantive rounds this verdict rests on.
2. **The 50 % scrub readout did not advance past `TURN 1 / 12`** in the viewer smoke, while 0 % and
   100 % clearly differ. A mid-bar seek settle-time / re-animation question for a future
   phase-30 legibility pass, not a frozen viewer.
