blocking: 0

# verify verdict — cogchemists (phase 60)
Head: runs/2026-08-24-cogchemists at working tree of 2026-08-24 · Checklist: docs/SPEC.md §Definition of done (phase 60) · Independent read written before reading fixes: yes (no fixer report exists for this phase; I read SPEC → prompts/60-verify.md → the committed artifacts → VERIFY.md, in that order)

Adjudicated by a fresh-context judge. I re-fetched **six** of the live API results VERIFY.md
cites (leaderboard, rounds list, episode-request detail, hosted log, filler-policies, replay
session POST) plus the S3 replay bytes, re-parsed the committed replay, looked at the
screenshot, and confirmed the viewer-check CI run's conclusion via the GitHub API. Nothing was
taken from VERIFY.md on faith.

## Standing blocking findings

None.

## Definition-of-done pass (item by item, independently verified)

### 1. ≥2 completed rounds after fillers set — **TRUE**
- Evidence: my re-fetch of `GET /rounds?league_id=league_7a7ba378-…` (2026-08-24 ~09:37Z) returns
  round 2 `completed` (created 09:05:56.56Z, completed 09:08:51.16Z) and round 3 `completed`
  (created 09:20:56.97Z, completed 09:25:05.03Z); round 1 `failed` with
  `"Temporal RoundWorkflow failed before settling the round."` — the documented pre-filler
  symptom, correctly excluded. A new round 4 is `pending` (post-VERIFY, immaterial).
- Fillers were set before either counted round completed: `log.md:62`
  (`09:06:52Z 50 filler-policies registered: assayer:v2=8f3133d9… quack:v2=cb0dabf3…`), and my
  re-fetch of `GET /leagues/<L>/filler-policies` returns exactly `cogchemists-assayer` v2
  (`8f3133d9-…`) and `cogchemists-quack` v2 (`cb0dabf3-…`) — matching
  `STATE.policies.filler_version_ids` and ≠ the champion versions. Both counted rounds' episodes
  actually seated fillers (item 3's `is_filler:true` participants), which is functional proof the
  fillers pre-dated them.

### 2. Both champions ranked, fillers absent/Baseline — **TRUE**
- Evidence: my re-fetch of `GET /divisions/div_be88c7cd-…/leaderboard` returns exactly two rows:
  `daveey` rank 1, Elo 1016.0, rounds_played 2, `cogchemists-empiricist:v2`; `daveey-1` rank 2,
  Elo 984.0, rounds_played 2, `cogchemists-careerist:v2`. Both `rounds_played ≥ 1`; no filler
  rows at all. Byte-identical to VERIFY.md §2.

### 3. Latest round's episode request completed with replay_url — **TRUE**
- Evidence: my re-fetch of `GET /episode-requests/ereq_4082c439-f9c5-44b8-ae1b-dab95490b1a1`
  returns `status: "completed"`, `replay_url: https://softmax-public.s3.amazonaws.com/replays/73254d72-43c1-41df-a2ff-b2fcfdb16885.replay`,
  participants: position 0 = `cogchemists-empiricist` v2 / `daveey` / `is_filler:false`,
  position 1 = `cogchemists-careerist` v2 / `daveey-1` / `is_filler:false`, positions 2–3 =
  `cogchemists-quack` v2 / `is_filler:true`. This ereq belongs to round 3
  (`round_f27c5e66-…`), the latest completed round. Participants named correctly; the fillers
  appear spectator-side as `Baseline` / `Baseline (2)` in the replay's `policyNames` (verified
  below). The double-quack seating is the league scheduler's pick between two registered fillers
  — advisory only.

### 4. Replay bytes valid, show the game — **TRUE**
- Evidence: I fetched the S3 replay myself; sha256
  `775422350b5678a599c7b8ffca7d1d39968ac4501f2f232f9f661548c0e4440e` — **identical** to the
  committed `runs/2026-08-24-cogchemists/episode.replay.json` (30 271 bytes). `jq -e` strict
  parse passes; `protocol: cogchemists.replay.v1` matches the design note (design.md:660–663);
  `results.reason: "complete"`, 6/6 rounds. Champion seats 0 and 1: 12 acts each, **0 scripted**
  (the design's fallback marker, design.md:471 — `scripted: true`); baseline seats 2 and 3:
  12/12 scripted, as intended. Champion acts carry ~550-char private notes and seat 1 has 9
  `say` lines — non-scripted decisions with non-trivial content, not fallbacks.

### 5. Hosted game log clean — **TRUE**
- Evidence: my own elevated fetch of `/episode-requests/ereq_4082c439-…/artifacts/logs`
  (HTTP 200, 54 170 bytes), decoded from python byte-string reprs, then grepped:
  `falling back` 0, `LLM provider is unavailable` 0, `cut off at max_tokens` 0, `rejected` 7.
  All seven are `cogchemists: <Gizmo|Widget> rejected (already_claimed); passing` — I confirmed
  in the replay that every `rejected:already_claimed` event is on seat 2 or 3 with
  `scripted:true` (the two Baseline seats, which don't call the LLM at all); no champion appears
  in any. The vocabulary is the game's documented rule-rejection (design.md:161, :474, :617),
  not an LLM defect, and Bedrock health in the same log is 24/24 `"ok":true`, 0 `"ok":false`.
  The three LLM-health patterns the check exists for are at zero; the `rejected` hits are the
  documented exception, cited by the verifier and independently re-verified by me. See
  non-blocking observations for the grep-pattern collision.

### 6. Public page uses the static replay path, featured match present — **TRUE**
- Evidence: I fetched `https://softmax.com/cogchemists` (486 227 bytes): no `<iframe>` in raw
  HTML (client-rendered, as the prompt's §6 anticipates), but the SSR payload contains the
  featured playlist — escaped JSON `playlist\":[{\"episodeId\":\"d48184d3-…\",\"coworldId\":\"cow_a9d9a26c-…\",\"coworldVersion\":\"0.1.1\",\"replayUrl\":\"https://softmax-public.s3.amazonaws.com/replays/73254d72-….replay\"…`
  with the daveey/daveey-1 matchup — a featured match is present. I re-ran the
  `POST /coworlds/replays/session` call the page's JS makes and got `ready: true` with
  `viewer_url = …/v2/coworlds/replays/static/cow_a9d9a26c-cf74-403a-85f9-542ca3bd61c9/sha256%3A967ac7cc…a431/index.html?replay=<s3 url>&v=2`
  — the **static** route, sha segment = `STATE.coworld.manifest_sha`, no `/client/replay`
  anywhere. My re-fetch of `/coworlds` also confirms `canonical: true` on v0.1.1
  (`cow_a9d9a26c-…`). VERIFY.md recorded which source it used, as required.

### 7. Certification declared the static bundle — **TRUE**
- Evidence: committed `runs/2026-08-24-cogchemists/release-result.json` (phase 40's artifact,
  release run 32708476022 = `STATE.coworld.release_run_id`): `.certify.replay_liveness` =
  `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)`;
  `.certify.ok: true`; output_tail shows 10/10 certification steps passed. Read from the
  committed copy, exactly as the prompt requires.

### 8. Viewer executed, replay advances, spectator judgment — **TRUE** (all three sub-conditions)
- (a) `loaded: true` — committed `viewer-check/viewer-smoke.json`: `loaded:true` at 1072 ms,
  `signals.data_replay_loaded:"true"`, `bridge:["loading","ready"]`, `bridge_ready:true`,
  `data_replay_error:null`, `failure:null`. The json's `url` is character-for-character the
  static viewer_url from my session-POST re-fetch. I confirmed CI run **32711872593**
  (workflow `viewer-check`, created 2026-08-24T09:29:59Z) via the GitHub API:
  `conclusion: "success"`.
- (b) Three differing clock readouts in the committed json: 0 % `THE ACADEMY · 6 ROUNDS`,
  50 % `ROUND 4 / 6 · MARKET · MOVES IN`, 100 % `FINAL · WIDGET 18.0` — the replay advances.
- (c) I looked at `viewer-smoke.png` myself: a fully rendered, legible broadcast frame —
  `COGCHEMISTS` wordmark, clock `FINAL · WIDGET 18.0`, four-seat scorebug (daveey 10 REP 9c,
  daveey-1 3 REP 13c, Gizmo 6 REP 11c with four publish pips, Widget 16 REP 10c), labbar,
  four cog sprites, six-card theory board (`Widow's Salt TRUE +5`, `Copper Fern TRUE +5`, four
  FALSE −6), hole-cam signature grid with red-ringed bluff cells, endcard
  `Widget MADE THE REPUTATION` whose ranked table (16/10/1/1/0/18.0 …) matches the replay's
  `results` field-for-field (reputation [10,3,6,16], coin [9,13,11,10], published [0,1,4,1],
  true [0,0,1,1], false [0,1,3,0], scores [11.8,5.6,8.2,18.0]), and a transport bar with beat
  markers reading `69 / 69` — 69 = the replay's event count, which I verified. The chrome is
  recognisably the bullwhip starter's (topband, scorebug plates, `« LOG` toggle, momentum
  scrubber, endcard) — not the gridlock rewrite failure. The verifier's judgment paragraph is
  faithful to the picture; nothing in it is over-claimed.

## Refuted

None — I attempted to falsify each of the eight items by re-fetching live evidence and
re-reading the committed artifacts; every one survived. No claim in VERIFY.md was contradicted
by any re-fetch.

## Checklist pass (independent)

| item | status | evidence (my source) |
|---|---|---|
| 1. ≥2 completed rounds post-fillers | TRUE | re-fetch `/rounds?league_id=league_7a7ba378-…`; re-fetch `/leagues/<L>/filler-policies`; log.md:62 |
| 2. champions ranked, fillers absent | TRUE | re-fetch `/divisions/div_be88c7cd-…/leaderboard` — 2 rows, daveey 1016 / daveey-1 984 |
| 3. ereq completed + replay_url | TRUE | re-fetch `/episode-requests/ereq_4082c439-…` |
| 4. replay valid, shows the game | TRUE | S3 re-fetch, sha256 identical to committed copy; own jq census (0 champion fallbacks) |
| 5. hosted log clean | TRUE | own elevated fetch + decode + grep: 0/0/0 LLM patterns; 7 game-rule `rejected`, all scripted seats |
| 6. static replay path + featured match | TRUE | own page fetch (SSR playlist) + own `POST /coworlds/replays/session` → static viewer_url, `ready:true` |
| 7. cert declared static bundle | TRUE | committed release-result.json `.certify.replay_liveness` |
| 8. viewer executed + advances + judgment | TRUE | committed viewer-smoke.json/png; GitHub API: run 32711872593 `success`; my own read of the png |

## Verifier report audit

| claim | verifier said | I verified | agrees |
|---|---|---|---|
| leaderboard rows | daveey 1016 / daveey-1 984, 2 rounds each | re-fetched, byte-identical | yes |
| rounds 2+3 completed, 1 failed pre-filler | as stated | re-fetched (plus a new pending round 4) | yes |
| ereq_4082c439 completed, participants | as stated | re-fetched | yes |
| replay bytes committed = S3 | committed at episode.replay.json | sha256 match `7754…440e` | yes |
| hosted log 0/0/0 + 7 rejected | as stated | own fetch+decode: identical counts and lines | yes |
| session POST → static URL, ready | as stated | re-ran POST, identical viewer_url | yes |
| viewer-check run green, loaded, 3 clocks | run 32711872593 | GitHub API `success`; committed json confirms | yes |
| screenshot judgment | full bullwhip-lineage frame, numbers match results | viewed png, cross-checked every endcard number | yes |

## Non-blocking observations (advisory; none falsifies a definition-of-done item)

- [grep-vocabulary] Check 5's `rejected` pattern collides with the game's own documented
  `rejected:<reason>` rule vocabulary (design.md:161/474/617); here all 7 hits are scripted
  Baseline seats and Bedrock is 24/24 ok, so intent is met — worth a LEARNINGS note so future
  designs avoid the reserved word in game logs.
- [seating] The scheduler seated `cogchemists-quack:v2` in both filler seats (assayer unused in
  the featured episode) — a league choice, not a coworld defect.
- [naming] Stage/scorebug mixes registries: player names for champions, in-fiction aliases
  (Gizmo/Widget) for Baseline seats whose `policyNames` are `Baseline` / `Baseline (2)`.
- [strategy] Champion seat 0 (`empiricist:v2`) published nothing all episode (`published[0]==0`)
  despite 12/12 non-scripted decisions — a prompt-strategy note, not a defect; check 4's bar
  (non-scripted, non-trivial content) is met.
- [api-shape] `GET /coworlds` returned a bare array to me where VERIFY.md shows `.entries` —
  response-shape drift in the API, immaterial to the verdict (both show canonical v0.1.1).

BLOCKING: 0
