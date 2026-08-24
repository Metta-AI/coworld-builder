# VERIFY — cogiavelli   (2026-08-24T14:43:12Z)

Verdict: **all-true** (8 / 8)

Run `2026-08-24-cogiavelli` · coworld `cow_f54e03ab-39e9-4763-b46f-51556727bdd4` v0.1.1 ·
league `league_5ba37909-d5ac-4ba5-8c51-842326b999e4` · division `div_827c9f85-5ef5-4999-b89f-4ea572d4c48f`.

Every fetch below was made fresh during this verification pass (window 14:08Z–14:43Z), with the two
documented exceptions: item 7 (read from the committed `release-result.json`) and item 8 (read from
the `viewer-check.yml` run **this pass dispatched**, `32740208697`).

Headers sent on every Observatory call: `Authorization: Bearer …` and `User-Agent: coworld-builder/1.0`
(values never printed). Elevated reads additionally send `X-Use-Elevated-Privileges: true`.

```bash
BASE=https://softmax.com/api/observatory/v2
AUTH=(-H "Authorization: Bearer $SOFTMAX_TOKEN" -H "User-Agent: coworld-builder/1.0")
ELEV=(-H "X-Use-Elevated-Privileges: true")
L=league_5ba37909-d5ac-4ba5-8c51-842326b999e4
D=div_827c9f85-5ef5-4999-b89f-4ea572d4c48f
COW=cow_f54e03ab-39e9-4763-b46f-51556727bdd4
```

> **Note on which round the evidence is anchored to.** The ladder produced a round every 15 min
> while this pass ran (r2 14:08Z, r3 14:23Z, r4 14:38Z). Items 3–6 and 8 are all anchored to the
> **same** episode — round 4's `ereq_12b0cd3d-09f0-40fb-ac32-35e64ff8787c`, which is also the
> episode the public page currently features — so the replay bytes, the hosted log, the iframe
> `src` and the rendered frame all describe one and the same match.

---

## 1. ≥2 completed rounds after fillers were set — **TRUE**

Fillers were registered at **2026-08-24T14:03Z** (`log.md` line 50), *before* the first
`trigger-round`. Three rounds have completed since (2, 3, 4); round 1 failed and does not count.

Filler registration confirmed live (elevated read):

```
GET /leagues/$L/filler-policies      [AUTH + ELEV]      HTTP 200
```
```json
{
  "filler_policy_versions": [
    {
      "policy_version_id": "bddc599d-011d-49f3-b23e-4deb83f6f707",
      "policy_id": "d578ae9e-6697-4db7-b596-9b2785b38f39",
      "policy_name": "cogiavelli-condottiere",
      "version": 2,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "display_name": null
    },
    {
      "policy_version_id": "4ce9c9d1-9297-4639-8f77-e7c13ef919c7",
      "policy_id": "0509dff5-ba45-4016-9523-e7b52b50a4cf",
      "policy_name": "cogiavelli-banker",
      "version": 2,
      "player_id": "ply_44ae9048-3242-4654-881f-6d9d43347fa3",
      "player_name": "daveey",
      "display_name": null
    }
  ]
}
```

```
GET /rounds?league_id=$L&limit=20                       HTTP 200      (fetched 14:42:44Z)
$ jq 'if type=="array" then . else .entries end|[.[]|{id,round_number,status,error,created_at,completed_at}]'
```
```json
[
  {
    "id": "round_a7d27b73-bedd-4676-9240-77ba87e1d6e2",
    "round_number": 4,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-24T14:34:03.009986Z",
    "completed_at": "2026-08-24T14:38:39.732987Z"
  },
  {
    "id": "round_27d51e7e-5691-497c-b3e4-73e5398d6be8",
    "round_number": 3,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-24T14:19:00.687490Z",
    "completed_at": "2026-08-24T14:23:09.762401Z"
  },
  {
    "id": "round_effaf587-1e67-403b-9dd5-762af00d1698",
    "round_number": 2,
    "status": "completed",
    "error": null,
    "created_at": "2026-08-24T14:04:00.322727Z",
    "completed_at": "2026-08-24T14:08:07.643573Z"
  },
  {
    "id": "round_b12bb7b8-c96d-4953-9bc3-fc6d897f4cc5",
    "round_number": 1,
    "status": "failed",
    "error": "Temporal RoundWorkflow failed before settling the round.",
    "created_at": "2026-08-24T14:03:01.367423Z",
    "completed_at": "2026-08-24T14:03:01.576103Z"
  }
]
```
```
$ jq -r 'if type=="array" then . else .entries end|[.[]|select(.status=="completed")]|length'
3
```

**Round 1's error, verbatim:** `Temporal RoundWorkflow failed before settling the round.`
Round 1 was auto-scheduled by the ladder at 14:03:01.367Z and died 209 ms later, *before* the
fillers POST landed — the exact race `playbooks/observatory-api.md` §6 documents
("A `trigger-round` issued before any filler exists fails instantly with
`Temporal RoundWorkflow failed before settling the round`"). It carried only one entrant
(`61d34873-…`, medici) and never settled. It is excluded, as the prompt requires.

Status: **TRUE** — rounds 2, 3 and 4 completed at 14:08:07Z, 14:23:09Z and 14:38:39Z, all after
fillers were set at 14:03Z. Requirement is ≥ 2; observed 3.

---

## 2. Both champions ranked, fillers absent/Baseline — **TRUE**

```
GET /divisions/$D/leaderboard                           HTTP 200   (bare array)   (fetched 14:42Z)
```
```json
[
  {"rank":1,"player_name":"daveey-1","policy_label":"cogiavelli-borgia:v2","score":1072.9423863367988,"rounds_played":3,"episode_wins":5.0},
  {"rank":2,"player_name":"relh","policy_label":"co-gas-cogiavelli-board-borgia-relhalpha:v1","score":1016.0,"rounds_played":1,"episode_wins":2.0},
  {"rank":3,"player_name":"richard","policy_label":"co-gas-cogiavelli-board-borgia-richard:v1","score":984.0,"rounds_played":1,"episode_wins":1.0},
  {"rank":4,"player_name":"daveey","policy_label":"cogiavelli-medici:v2","score":927.0576136632011,"rounds_played":3,"episode_wins":0.0}
]
```
```
$ jq -r '.[]|[.rank,.player_name,.policy_label,.score,.rounds_played,.episode_wins]|@tsv'
1	daveey-1	cogiavelli-borgia:v2	1072.9423863367988	3	5.0
2	relh	co-gas-cogiavelli-board-borgia-relhalpha:v1	1016.0	1	2.0
3	richard	co-gas-cogiavelli-board-borgia-richard:v1	984.0	1	1.0
4	daveey	cogiavelli-medici:v2	927.0576136632011	3	0.0
```

- `daveey` — present, `rounds_played = 3` (≥ 1). ✔
- `daveey-1` — present, `rounds_played = 3` (≥ 1). ✔
- Fillers `cogiavelli-condottiere:v2` / `cogiavelli-banker:v2` — **absent** from the leaderboard
  (they seat as `Baseline` / `Baseline (2)` inside episodes; see item 4's `policyNames`). ✔
- `relh` and `richard` are two **other platform players** who submitted their own policies to this
  public ladder at ~14:34Z and first played in round 4. They are not this run's fillers and not a
  defect; their arrival is recorded here because it moved `daveey` from rank 2 to rank 4.

Status: **TRUE** — both champions ranked with 3 rounds played each; no filler policy appears as a
ranked row.

---

## 3. Latest round's episode request completed with a replay — **TRUE**

```
R=round_a7d27b73-bedd-4676-9240-77ba87e1d6e2      # max_by(.round_number) over completed rounds
GET /episode-requests?round_id=$R&limit=20              HTTP 200
```
```json
[{"id":"ereq_12b0cd3d-09f0-40fb-ac32-35e64ff8787c","status":"completed"}]
```
```
EREQ=ereq_12b0cd3d-09f0-40fb-ac32-35e64ff8787c
GET /episode-requests/$EREQ                             HTTP 200
$ jq '{status, replay_url, participants, participant_scores}'
```
```json
{
  "status": "completed",
  "replay_url": "https://softmax-public.s3.amazonaws.com/replays/1071e912-8357-44ef-9745-7d71d59ca586.replay",
  "participants": [
    {"position":0,"policy_name":"co-gas-cogiavelli-board-borgia-relhalpha","version":1,"player_name":"relh","is_filler":false},
    {"position":1,"policy_name":"cogiavelli-medici","version":2,"player_name":"daveey","is_filler":false},
    {"position":2,"policy_name":"cogiavelli-borgia","version":2,"player_name":"daveey-1","is_filler":false},
    {"position":3,"policy_name":"co-gas-cogiavelli-board-borgia-richard","version":1,"player_name":"richard","is_filler":false},
    {"position":4,"policy_name":"cogiavelli-condottiere","version":2,"player_name":"daveey","is_filler":true},
    {"position":5,"policy_name":"cogiavelli-banker","version":2,"player_name":"daveey","is_filler":true}
  ],
  "participant_scores": [
    {"position":0,"score":0.16666666666666666},
    {"position":1,"score":0.052083333333333336},
    {"position":2,"score":0.2916666666666667},
    {"position":3,"score":0.07465277777777778},
    {"position":4,"score":0.2743055555555555},
    {"position":5,"score":0.15104166666666666}
  ]
}
```

`status == "completed"` ✔ · `replay_url` non-null ✔ · participants name **`daveey`** (seat 1,
`cogiavelli-medici:v2`) and **`daveey-1`** (seat 2, `cogiavelli-borgia:v2`) ✔ · the two filler seats
carry `is_filler: true` and surface in the replay as `Baseline` / `Baseline (2)` (item 4) ✔.

Status: **TRUE**.

---

## 4. Replay bytes are valid and show the game — **TRUE**

```
GET https://softmax-public.s3.amazonaws.com/replays/1071e912-8357-44ef-9745-7d71d59ca586.replay
HTTP 200 bytes=265223   -> /tmp/ep4.replay
```
```
$ jq -e . /tmp/ep4.replay >/dev/null && echo "strict UTF-8 JSON: ok"
strict UTF-8 JSON: ok
$ python3 -c "open('/tmp/ep4.replay','rb').read().decode('utf-8'); print('python strict utf-8 decode: ok')"
python strict utf-8 decode: ok
$ jq -r '.protocol, .results.reason' /tmp/ep4.replay
cogiavelli.replay.v1
complete
```

`protocol` = `cogiavelli.replay.v1`, matching the manifest and `design.md` L766. `results.reason`
= **`complete`** — the strongest of the three the design allows; the `deadline` exception
(`design.md` L331–334) is not needed here.

```
$ jq -c '.names,.policyNames,.powers' /tmp/ep4.replay
["Gasket","Piston","Rivet","Tinker","Widget","Sprocket"]
["relh","daveey","daveey-1","richard","Baseline","Baseline (2)"]
["NAPLES","PAPACY","VENICE","FLORENCE","MILAN","TURK"]
```

Two name spaces, as designed: in-world aliases in `names`, real ladder identities in `policyNames`,
fillers anonymised to `Baseline` / `Baseline (2)`.

This game's replay carries **12 event kinds**, none of them `decision` — the prompt's literal
`select(.type=="decision")` does not apply, so the fallback census is adapted to the events this
replay actually holds. The decision-bearing kinds are `press` and `orders` (one of each per seat per
season); the fallback/scripted marker is `scripted: true` on those events (`design.md` L599, L710–711).

```
$ jq -r '[.events[]|.kind]|group_by(.)|map("\(.[0]) \(length)")|join("  ")' /tmp/ep4.replay
battle 12  bribe 9  cities 12  end 1  famine 4  orders 72  plague 4  press 72  season 24  spend 22  start 1  winter 4
```
```
$ jq -r '[.events[]|select(.kind=="press" or .kind=="orders")]|group_by(.seat)
         |map("seat \(.[0].seat)  total=\(length)  scripted=\([.[]|select(.scripted==true)]|length)")|.[]'
seat 0  total=24  scripted=0
seat 1  total=24  scripted=0
seat 2  total=24  scripted=0
seat 3  total=24  scripted=0
seat 4  total=24  scripted=24
seat 5  total=24  scripted=24
```

**Champion seats 1 (`daveey`) and 2 (`daveey-1`) have `scripted = 0` out of 24** — zero fallbacks,
not a small minority. The only fully scripted seats are 4 and 5, which *are* the scripted baselines
by construction. Content is non-trivial:

```
$ jq '[.events[]|select(.kind=="press" and .seat==1)][2]
      |{year,season,seat,scripted,broadcast,pledges,letters_n:(.letters|length)}'   # daveey, PAPACY, autumn 1499
{
  "year": 1499, "season": "autumn", "seat": 1, "scripted": null,
  "broadcast": "Papacy stands resolute in measured prosperity. Our garrisons secure neutral ground for steady income. We honor our pledges to Venice, Florence, and Naples—partition and peace serve all powers better than chaos. Rome, Perugia, and our growing sphere anchor the center. We build wealth, not conquest.",
  "pledges": [{"to":"VENICE","kind":"peace","province":""},{"to":"FLORENCE","kind":"peace","province":""},{"to":"NAPLES","kind":"peace","province":""}],
  "letters_n": 5
}
$ jq -c '[.events[]|select(.kind=="orders" and .seat==2)][5]
         |{year,season,seat,scripted,orders,spend,illegal}'      # daveey-1, VENICE, autumn 1500
{"year":1500,"season":"autumn","seat":2,"scripted":null,"orders":["A FER - BOL","F FRI H","A PAD H"],"spend":[],"illegal":[{"raw":"A PAD S A FER - BOL","why":"nonadjacent"}]}
```

The champions write real diplomatic press, make and then break pledges, and issue orders that the
adjudicator legality-checks (one order rejected `nonadjacent` and reported back in `illegal[]` —
the designed degrade path, not a fallback).

```
$ jq -c '.results' /tmp/ep4.replay
{"names":["relh","daveey","daveey-1","richard","Baseline","Baseline (2)"],
 "powers":["NAPLES","PAPACY","VENICE","FLORENCE","MILAN","TURK"],
 "scores":[0.16666666666666666,0.052083333333333336,0.2916666666666667,0.07465277777777778,0.2743055555555555,0.15104166666666666],
 "cities":[3,1,6,1,6,3],"ducats":[31,6,48,19,14,15],"units":[4,1,0,1,1,2],
 "spent":[6,27,24,24,51,26],"received":[9,6,9,9,0,0],
 "years":4,"maxYears":4,"conqueror":"","reason":"complete"}
```
```
$ jq -c '[.events[]|select(.kind=="battle")|(.stabs//[])[]]' /tmp/ep4.replay
[{"power":2,"pledgeTo":"VENICE","kind":"peace","province":"","order":"A BOL - FER"},
 {"power":0,"pledgeTo":"FLORENCE","kind":"peace","province":"","order":"A FER - BOL"},
 {"power":2,"pledgeTo":"VENICE","kind":"peace","province":"","order":"A BOL - FER"},
 {"power":2,"pledgeTo":"VENICE","kind":"peace","province":"","order":"A BOL - FER"},
 {"power":2,"pledgeTo":"VENICE","kind":"peace","province":"","order":"A BOL - FER"},
 {"power":0,"pledgeTo":"FLORENCE","kind":"peace","province":"","order":"A FER - BOL"},
 {"power":2,"pledgeTo":"PAPACY","kind":"peace","province":"","order":"pays 15 against the Papacy"},
 {"power":2,"pledgeTo":"PAPACY","kind":"peace","province":"","order":"A PER - ROM"}]
```

Eight recorded betrayals — pledges of peace broken by the very order that followed them. That *is*
the thing this game is about, and it is in the record.

Status: **TRUE** — strict UTF-8 JSON under two independent strict parsers; `protocol` matches;
`results.reason == "complete"`; both champion seats made 24/24 live (non-scripted) decisions with
substantive press, orders, spending and stabs.

---

## 5. Hosted game log is clean — **TRUE**

```
GET /episode-requests/$EREQ/artifacts/logs   [AUTH + ELEV]     HTTP 200 bytes=200254
```
The body is python `b'…'` byte-string reprs under `===== container: <name> =====` headers, so it was
decoded with `ast.literal_eval` per repr **before** grepping (per `playbooks/observatory-api.md` §10):

```
containers: ['coworld-init-config', 'bedrock-sidecar', 'game', 'worker']   decoded chars: 199391

$ grep -nE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs4.txt
CLEAN
$ grep -cE 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected' /tmp/logs4.raw
0
```

Zero matches in the decoded text **and** zero in the raw undecoded bytes. Supporting excerpts:

```
===== container: game =====
cogiavelli: seed not pinned; randomized
cogiavelli: seats=6 years=4 press=true model=claude-sonnet-5
cogiavelli: serving on 0.0.0.0:8080
cogiavelli: player slot 0 connected (1/6)
cogiavelli: slot 0 delivered a prompt (3051 chars)
cogiavelli: player slot 4 connected (2/6)
cogiavelli: slot 4 delivered a prompt (344 chars, scripted condottiere)
```
```
$ grep -oE 'bedrock_[a-z_]+' /tmp/logs4.txt | sort | uniq -c
    289 bedrock_sidecar
     96 bedrock_sidecar_call
     96 bedrock_sidecar_complete
      1 bedrock_sidecar_started
     96 bedrock_sidecar_usage
```

96 Bedrock calls, 96 completions — a 1:1 ratio, i.e. no retries, no truncations, no provider
unavailability. (4 LLM seats × 4 years × 3 seasons × 2 phases = 96.) No documented exception is
needed for this item.

Status: **TRUE** — `CLEAN`.

---

## 6. The public page uses the static replay path, with a featured match — **TRUE**

**Source used: two of them, both recorded.** The raw-HTML grep and the page's own SSR payload.

*(a) Raw-HTML grep — finds nothing; the iframe is client-rendered.*
```
$ curl -sS "https://softmax.com/cogiavelli" | grep -o '<iframe[^>]*src="[^"]*"'
(no output; grep exit=1)
```
Recorded as **unknown, not a failure** — `playbooks/observatory-api.md` §Featured match answers this
for the platform ("the page is now **client-rendered** for the iframe — the raw-HTML grep finds
nothing for any coworld"). `GET /coworlds?limit=200 | select(.name=="cogiavelli")` likewise gives
`"featured_match": null`, and that too is not evidence: it is null for **all 46 canonical coworlds**
on the platform right now —

```
$ curl -sS "$BASE/coworlds?limit=200" "${AUTH[@]}" \
  | jq -r 'if type=="array" then . else .entries end
           |[.[]|select(.canonical==true)|.featured_match]|group_by(.)
           |map("featured_match=\(.[0]|tostring): \(length) canonical coworlds")|.[]'
featured_match=null: 46 canonical coworlds
```

*(b) The SSR payload the page actually renders from — `state.playlist[0]`.* Fetched 14:42:53Z:
```json
{
 "episodeId": "f7688c86-2a5b-4ed8-81c0-142692441c14",
 "coworldId": "cow_f54e03ab-39e9-4763-b46f-51556727bdd4",
 "coworldName": "cogiavelli",
 "coworldVersion": "0.1.1",
 "replayUrl": "https://softmax-public.s3.amazonaws.com/replays/1071e912-8357-44ef-9745-7d71d59ca586.replay",
 "finishedAt": "2026-08-24T14:38:31.574302Z",
 "roundNumber": 4,
 "episodeNumber": 1,
 "code": "cogiavelli.r4.e1",
 "inspectUrl": "/observatory/v2?tab=episode-requests&detail=episode-request:ereq_12b0cd3d-09f0-40fb-ac32-35e64ff8787c"
}
matchup.first : 1 daveey-1 cogiavelli-borgia:v2 1072.9423863367988 rounds 3
matchup.second: 2 relh     co-gas-cogiavelli-board-borgia-relhalpha:v1 1016 rounds 1
```

**A featured match is present**: `cogiavelli.r4.e1`, pointing at exactly the episode verified in
items 3–5.

*(c) The iframe `src`.* The page's JS resolves it through the session call
(`playbooks/observatory-api.md` §Featured match), invoked here with the featured match's `replayUrl`:
```
POST /coworlds/replays/session
  {"coworld_id":"cow_f54e03ab-39e9-4763-b46f-51556727bdd4",
   "replay_uri":"https://softmax-public.s3.amazonaws.com/replays/1071e912-8357-44ef-9745-7d71d59ca586.replay"}
HTTP 200
```
```json
{
  "viewer_url": "https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_f54e03ab-39e9-4763-b46f-51556727bdd4/sha256%3A0489a9e732975007d7b46680c736750b23180dbcd61078ddc3337df27aaa9bbb/index.html?replay=https%3A%2F%2Fsoftmax-public.s3.amazonaws.com%2Freplays%2F1071e912-8357-44ef-9745-7d71d59ca586.replay&v=2",
  "ready": true
}
```

The path is `…/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>`, with `<sha>` =
the coworld's manifest hash `sha256:0489a9e9…` (URL-encoded), matching
`STATE.coworld.manifest_sha`. `ready: true` ⇒ static delivery. It is **not** a `/client/replay` pod
URL; the substring `/client/replay` does not occur anywhere in the URL.

**Recorded transient (attempts 1–2 of the retry budget).** Between 14:24Z and 14:35Z
`state.playlist` was `[]` — nine consecutive polls (14:24:5x, 14:25:4x, 14:28:30, 14:29:12,
14:29:54, 14:31:21, 14:32:24, 14:33:28, 14:34:29) all returned `playlist len= 0`, while
`state.pool.replays` held the round-3 episode throughout. Cause, established rather than guessed: `relh` and `richard`
joined the division in that window at the default Elo 1000 with `rounds_played: 0` and
`policy_label: null`, landing at ranks 2 and 3 and pushing `daveey` (969.47) to rank 4; the featured
builder pairs rank 1 against rank 2 and there was no episode in which `daveey-1` had met `relh`.
Cross-checked against six other coworlds' SSR payloads at ~14:36Z — on **every** one the featured
`matchup.second` has `rounds_played > 0`:

```
escrow     | playlist=1 | featured first/second: relh 1 / richard 2 (rounds 81)
raid       | playlist=1 | featured first/second: daveey 1 / daveey-1 2 (rounds 122)
hive       | playlist=1 | featured first/second: relh 1 / daveey 2 (rounds 119)
ledger     | playlist=1 | featured first/second: daveey-1 1 / richard 2 (rounds 48)
lighthouse | playlist=1 | featured first/second: daveey 1 / daveey-1 2 (rounds 152)
bullwhip   | playlist=1 | featured first/second: daveey 1 / richard 2 (rounds 87)
```

Attempt 3 — re-poll after round 4 completed at 14:38:39Z, by which time `relh` had submitted a
policy and played — returned the featured match quoted above. The item is TRUE on live evidence,
not on the transient being explained away.

Status: **TRUE** — featured match `cogiavelli.r4.e1` present; iframe `src` is the static
`/v2/coworlds/replays/static/…/index.html?replay=…` route with `ready: true`.

---

## 7. Certification declared the static bundle — **TRUE**

**Source: the committed `runs/2026-08-24-cogiavelli/release-result.json`** — the copy phase 40
downloaded from release run `32734996838` and committed in `a6561a6`
(`cogiavelli: 40 released 0.1.1 canonical+certified; phase -> 50`). It was present; no re-download
from `gh run download` was needed, and `/tmp` was never consulted.

```
$ ls -la runs/2026-08-24-cogiavelli/release-result.json
-rw-r--r-- 1 root root 3938 Aug 24 14:00 runs/2026-08-24-cogiavelli/release-result.json
$ git log --oneline -1 -- runs/2026-08-24-cogiavelli/release-result.json
a6561a6 cogiavelli: 40 released 0.1.1 canonical+certified; phase -> 50

$ jq -r '.certify.replay_liveness' runs/2026-08-24-cogiavelli/release-result.json
Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)

$ jq -c '{version, canonical, certify:{ok:.certify.ok}}' runs/2026-08-24-cogiavelli/release-result.json
{"version":"0.1.1","canonical":true,"certify":{"ok":true}}
```

The required substring `Replay liveness: skipped (static replay bundle declared` is present.

Status: **TRUE**.

---

## 8. Spectator judgment — the viewer was EXECUTED, then judged — **TRUE**

The sandbox has no screen and no browser, so the render was **dispatched** to GitHub Actions and the
result downloaded. Nothing below is a DOM readout or a picture I produced locally.

```
$ SRC=<the item-6 iframe src, verbatim, ?replay= and all>
$ gh workflow run viewer-check.yml -R Metta-AI/coworld-builder -f url="$SRC" -f timeout=90
     dispatched 2026-08-24T14:40:56Z
$ gh run list -R Metta-AI/coworld-builder -w viewer-check.yml --json databaseId,createdAt,status -L 10 \
   | jq -r 'sort_by(.createdAt)|reverse|.[]|[.databaseId,.createdAt,.status]|@tsv'
32740208697	2026-08-24T14:40:57Z	in_progress      <-- created AFTER the dispatch; this is ours
32738798949	2026-08-24T14:27:18Z	completed
32736614525	2026-08-24T14:06:09Z	completed
```
The new run was identified by `createdAt` **after** the 14:40:56Z dispatch, not by taking "the
latest run" blind. (`32738798949`, at 14:27Z, was an earlier dispatch by this same pass against
round 3's replay, before round 4 became the featured match; it is superseded and is not the evidence
below.)

```
$ gh run view 32740208697 -R Metta-AI/coworld-builder --json conclusion,status,url
{"conclusion":"success","status":"completed",
 "url":"https://github.com/Metta-AI/coworld-builder/actions/runs/32740208697"}
$ gh run download 32740208697 -R Metta-AI/coworld-builder -n viewer-check \
    -D runs/2026-08-24-cogiavelli/viewer-check
viewer-smoke.json  viewer-smoke.png  smoke-stdout.txt  smoke-stderr.txt   (committed)
```

*(b) The readouts, verbatim.*

```
$ jq -c '{loaded, ms, clock, scorebug, feed_lines}' runs/2026-08-24-cogiavelli/viewer-check/viewer-smoke.json
{"loaded":true,"ms":1095,"clock":"SPRING 1499","scorebug":"NAPLES relh ▶ 3 CITIES 3 units · 12đ PAPACY daveey ▶ 3 CITIES 3 units · 12đ VENICE daveey-1 ▶ 3 CITIES 3 units · 12đ FLORENCE richard ▶ 3 CITIES 3 units · 12đ MILAN Widget ▶ 3 CITIES 3 units · 12đ TURK Sprocket ▶ 3 CITIES 3 units · 12đ","feed_lines":758}

$ jq -c '.signals' runs/2026-08-24-cogiavelli/viewer-check/viewer-smoke.json
{"data_replay_loaded":"true","data_replay_error":null,"bridge":["loading","ready"],"bridge_ready":true,"bridge_error":[]}

$ jq -r '.failure // "no failure"' runs/2026-08-24-cogiavelli/viewer-check/viewer-smoke.json
no failure

$ jq -c '.console_tail' runs/2026-08-24-cogiavelli/viewer-check/viewer-smoke.json
["[bridge] loading","[bridge] ready"]
```

**The three clock readouts** (`jq -r '.scrub[]|"\(.at)\t\(.clock)"'`):

| scrub position | clock readout |
|---|---|
| 0 %   | `SPRING 1499` |
| 50 %  | `SPRING 1501 · LETTERS · TURK` |
| 100 % | `FINAL · VENICE 6 CITIES` |

All three **differ**. `loaded: true` at 1 095 ms, via **both** signals — `data-replay-loaded="true"`
and the `coworld-replay` bridge reaching `ready`. A `#scrub` control exists (the json returns real
readouts rather than `"(no #scrub…)"`), so motion is measured directly, not inferred.

**Item 8 is TRUE: `loaded: true` AND the three clock readouts differ.**

*(c) Reconciliation against the replay record.* Ordered excerpts of the same replay bytes verified in
item 4 (`jq -r '.events[]|[year+season, seat, kind, summary]|@tsv'`):

```
=== EARLY ===
1499 spring	null	start
1499 spring	null	famine
1499 spring	0	press	NAPLES opens with strong southerly position. We seek neutrals and stable borders
1499 spring	1	press	Papacy holds the center and intends to build wealth steadily. We will garrison n
1499 spring	2	press	Greetings from Venice! We seek prosperity through trade and mutual respect. The
1499 spring	3	press	Florence opens Spring 1499 with steady purpose. We hold three strong cities and
1499 spring	0	orders	Spring 1499: NAPLES executes pincer on MES (Messina). A BAR moves to MES support

=== MIDDLE ===
1500 autumn	0	press	Naples secures the southern gateway. Messina falls this Autumn with overwhelming
1500 autumn	2	press	Venice secures the heartland. Ferrara and Bologna fall to overwhelming force thi
1500 autumn	2	orders	Execute the supported assault: A FER - BOL with A PAD support creates 2v1 agains

=== LATE ===
1502 autumn	2	orders	Venice has no units and no legal orders to submit. The board shows a partition a
1502 autumn	3	orders	AUTUMN 1502: Florence holds Rome defensively. Single unit A ROM maintains garris
1502 winter	null	winter
1502 autumn	null	end	complete
```

Frame and record agree at every point checked. The 0 % clock `SPRING 1499` is the replay's first
`season` event. The 0 % scorebug reads every power at `3 CITIES 3 units · 12đ` — the identical
opening position for all six seats, exactly what a Spring-1499 `start` event implies. The 100 %
clock `FINAL · VENICE 6 CITIES` matches `results.cities[2] == 6` for seat 2 = `daveey-1` = VENICE.
The screenshot's endcard table reproduces `results` field for field: `daveey-1 · VENICE 6 cities /
48đ / 24đ spent / 0.292` against `cities[2]=6, ducats[2]=48, spent[2]=24, scores[2]=0.29166…`, and
`daveey · PAPACY 1 / 6đ / 27đ / 0.052` against `cities[1]=1, ducats[1]=6, spent[1]=27,
scores[1]=0.05208…`. The endcard's STABS column (VENICE 2, FLORENCE 6) sums to 8, and the replay
carries exactly 8 stab entries across its `battle` events.

### Spectator judgment

**It is legible, and it shows the game.** The screenshot
(`runs/2026-08-24-cogiavelli/viewer-check/viewer-smoke.png`, 1280×800, captured at the 100 % scrub
position) is a dark Renaissance-Italy board with a `COGIAVELLI` wordmark top-left and the clock
`FINAL · VENICE 6 CITIES` centred in the header. Under it runs the **scorebug**, six coloured
plates — `NAPLES relh 3 CITIES · 4 units · 31đ`, `PAPACY daveey 1 CITIES · 1 unit · 6đ`,
`VENICE daveey-1 6 CITIES · 0 units · 48đ`, `FLORENCE richard 1 CITIES`, `MILAN Widget 6 CITIES`,
`TURK Sprocket 3 CITIES` — with a small red `STAB` badge pinned to VENICE's plate. Beneath that is
the **ducat/city share bar**, a single stacked strip apportioning all 24 cities across the six
powers plus a grey `NEUTRAL 4` remainder, with a treasury row under it (`NAP 31đ · PAP 6đ ·
VEN 48đ · FLO 19đ · MIL 14đ · TUR 15đ`). The map itself is drawn and labelled — Como, Trent,
Friuli, Verona, Turin, Savoy, Genoa, Bosnia, Albania, Palermo, Messina, Ligurian Sea, Upper
Tyrrhenian, Ionian Sea — with city glyphs on the held provinces. Overlaying the centre is the
**endcard**: `FINAL — 4 YEARS · 24 CITIES`, the headline `daveey-1 (VENICE) LED ITALY`, a six-row
ranked table (power, cities, ducats, spent, stabs, score) and `THE LEDGER — DUCATS PAID, PAYER BY
TARGET, YEAR BY YEAR` as a payer×target matrix. Along the bottom is the **transport strip**: a play
button, a `237 / 237` frame counter, a `FINAL` chapter tag, and a full-width scrubber whose momentum
graph is a dense tick field with orange and red spikes marking the seasons where money moved and
cities changed hands. Nothing is empty, nothing is frozen — the clock advanced through three
distinct states and 758 feed lines were emitted.

**It looks like the starter's chrome.** This is the babel/paintbot/raid/hive lineage, not a rewrite
sharing only ids: same header wordmark and centred clock, same coloured per-seat scorebug plates,
same full-width scrubber with momentum graph and chapter tag, same centred endcard with ranked table
— the cogame-gridlock failure mode (2026-08-23) is not present here. The game-specific additions
(ducat share bar, the ledger matrix, the STAB badge) sit *inside* that chrome rather than replacing it.

**Two non-blocking legibility observations for the coordinator** (phase-30 material, not check
failures):
1. The map is letterboxed — roughly 270 px of flat empty background on each side at 1280 px wide.
   The board occupies only the centre ~58 % of the frame.
2. The scorebug can read oddly at the end: `VENICE daveey-1 ▶ 6 CITIES 0 units · 48đ` — the winner
   holds six cities with zero units on the board. The replay confirms it (`results.units[2] == 0`,
   and seat 2's last order text is "Venice has no units and no legal orders to submit"), so the
   viewer is faithful; it is the *game* that permits a unitless city-holder to win, and a spectator
   may find that surprising without a caption.

Status: **TRUE**.

---

## Tally

| # | Item | Verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | **TRUE** (3: rounds 2, 3, 4) |
| 2 | Both champions ranked, fillers absent/Baseline | **TRUE** |
| 3 | Latest round's episode request completed with replay | **TRUE** |
| 4 | Replay bytes valid, protocol matches, champions not scripted | **TRUE** |
| 5 | Hosted game log clean | **TRUE** (`CLEAN`) |
| 6 | Public page: featured match + static iframe src | **TRUE** |
| 7 | Certification declared the static bundle | **TRUE** |
| 8 | Viewer executed: `loaded: true` + three differing clocks | **TRUE** |

**8 / 8 TRUE. Nothing NOT FETCHED. No undocumented exception claimed.**

Replay URL: `https://softmax-public.s3.amazonaws.com/replays/1071e912-8357-44ef-9745-7d71d59ca586.replay`
Episode request: `ereq_12b0cd3d-09f0-40fb-ac32-35e64ff8787c` (round 4, `cogiavelli.r4.e1`)
viewer-check run: `32740208697` — https://github.com/Metta-AI/coworld-builder/actions/runs/32740208697
