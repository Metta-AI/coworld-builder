blocking: 0

# phase-60 verdict — nethack (run 2026-08-28-nethack)

Judge: fresh context, 2026-08-29. Checklist: `docs/SPEC.md` §Definition of done (8 items — the
authority for this verdict). Evidence: `runs/2026-08-28-nethack/VERIFY.md` (read after SPEC),
the committed `viewer-check/viewer-smoke.{json,png}` (looked at the png myself), the committed
`release-result.json`, `design.md:1350-1410`, the procgen precedent
(`runs/2026-08-28-procgen/VERIFY.md:394-466`), and my own fresh re-fetches (04:5x–05:0xZ region,
`SOFTMAX_TOKEN`/`GH_TOKEN` from the env; every re-fetch below is mine unless it cites a VERIFY.md
line). Run facts confirmed against the live API: `cow_1346325e-7184-4c94-9fbc-d3aeb750889c`,
canonical `true`, version `0.1.1`, `manifest_hash sha256:3452373e…d7b49e`, **num_agents = 1 in
both manifest variants** (my `/coworlds` fetch).

## Blocking items

(none)

## The two requested rulings

### (A) Item 6, "featured match present" — ruled TRUE by the precedent reading

The strict page-text reading is FALSE and the verifier was right to record it
(VERIFY.md:514-533): my own re-fetch of `https://softmax.com/nethack` (HTTP 200) still shows
`\"playlist\":[]` and one occurrence of "No featured match yet". But I rule that SPEC item 6 is
satisfied, for four independently verified reasons. (1) The featured **pool** is populated and
current: my re-fetch shows `state.pool.replays` now carries **round 3** episodes
(`round_b7f16922…`, the latest completed round) — the page is featuring this coworld's newest
replays, not empty. (2) The playlist entry is structurally impossible here: a playlist `matchup`
names the top two ranked players *inside one episode*, and a `num_agents = 1` coworld can never
put two players in one episode. The verifier's same-minute cross-check (VERIFY.md:544-567) shows
all three single-seat coworlds (`crafter`, `procgen` at round 32 with three ranked players,
`nethack`) at playlist 0 and every multi-seat coworld at playlist 1 — platform behaviour, not a
defect of this release. (3) The clause SPEC item 6 actually polices — the iframe `src` — is
verified at head by my own `POST /coworlds/replays/session`: `viewer_url` =
`…/v2/coworlds/replays/static/cow_1346325e…/sha256%3A3452373e…d7b49e/index.html?v=2#replay=…3466ad2b…`,
`ready: true`, cow_id and manifest sha both matching, **no `/client/replay`** anywhere. (4) The
precedent is on point and shipped: procgen's VERIFY check 6
(`runs/2026-08-28-procgen/VERIFY.md:426,460-466`) was judged TRUE on exactly this evidence shape
— `playlist: []`, featured match read from `state.pool.replays[0]`, static session URL — and
that run closed. Reading "featured match present" as "the page features a current match replay
of this coworld (pool) whose viewer path is the static bundle" is the only reading under which
SPEC item 6 is satisfiable at all for single-seat coworlds; the alternative makes `num_agents=1`
permanently unshippable, which is a SPEC-documentation gap, not a nethack defect. **Non-blocking
observation for the SPEC maintainer:** item 6 should say explicitly that for `num_agents = 1`
coworlds the featured match lives in `state.pool.replays` and the playlist is empty by
construction.

### (B) Item 4, "doing the thing the game is about" — ruled TRUE on SPEC; design-note substitute recorded unmet, non-blocking

I re-ran the whole check myself rather than trusting VERIFY.md: fetched the round-3 primary
replay (40485 bytes, `COWLDNET` magic + length-prefixed `nethack` in the header, my `od` dump),
fetched `tools/replay_summary.py` from `Metta-AI/cogame-nethack@main` via the GitHub API, ran it,
and got one strict-UTF-8 JSON object (6674 bytes, `bytes.decode('utf-8')` clean): `protocol
nethack/v1`, `results.reason "complete"`, `endRule "death"` (killer `jackal`), 25/25 plans
`source:"llm"`, `fallbackTurns 0`, `fallbacks 1` (an attempt-1 retry whose turn still produced an
llm directive — VERIFY.md:363-369, and the retry line is visible in the hosted log I re-fetched),
25 non-empty say lines ("Starting exploration. Moving east and south to find stairs down.", …,
"Fleeing jackal to doorway to fight 1v1"). SPEC item 4's operative test for LLM games is its own
parenthetical: *"non-scripted decisions with non-trivial content; not all fallbacks."* That is
met beyond argument — 272/272 champion turns across all six episodes are `source:"llm"`
(VERIFY.md:321-322, 353-356, 477; my re-run confirms the primary), zero fallback turns, and the
says are coherent plans explicitly pursuing the game's declared objective (nearly every line says
"find stairs down"); the events show exploration, door-kicking (9 kicks in my verb histogram),
combat retreat, and — in round 2 — gold pickup and a deliberate escape. Exploration, combat and
item use *are* this game's moment-to-moment content; the champions are genuinely playing it and
losing, and SPEC item 4 is a validity check on the decision pipeline, not a skill floor.

The design note's stricter phase-60 substitute (`design.md:1386-1397`: additionally require
`results.depthReached >= 2` and ≥1 `travel` **and** ≥1 `down` verb) is **unmet in 6/6 episodes**
— my re-run shows `depthReached: 1`, verbs `{move:123, search:26, kick:9, travel:2}`, zero
`down`, matching the verifier's table (VERIFY.md:384-397). I do not count it blocking, and I say
plainly why, because I am accepting one clause of that design section and rejecting another: the
*expansion* clause (binary → strict-UTF-8 JSON via `replay_summary.py`) is the necessary
substitute without which SPEC's own "valid UTF-8 JSON" words cannot be evaluated against a binary
replay at all — the same knights-archers-precedent format the certified static viewer parses
(item 8 proves it renders). The *threshold* clause adds gameplay criteria that appear nowhere in
SPEC's 8 items, and blocking must tie to the named checklist; SPEC item 4 delegates exactly one
thing to the design (the `deadline` exception, unused here — all six reasons are `complete`).
What the miss actually is: a game-balance/legibility defect — `scores[0] = 100_000 ×
(depthReached − 1) + …` (`design.md:1363`), so depth is the dominant scoring term by two orders
of magnitude, no hosted spectator has ever seen the DL ladder light past DL1, the scrubber's
DEPTH momentum graph is flat, and one champion legally ended its best-scoring round-2 episode by
taking the **up** staircase (`endRule "escaped"`, score 160). SPEC §Rails assigns parameter
tuning and scoring-rule application to the coordinator, never to Blocked. **Material non-blocking
finding for the coordinator:** the headline dimension of this game is unreached; what would
settle it is prompt/balance tuning (e.g. surface the down-staircase in the observation or prompt,
raise `maxTurns`, or bias level generation) and one hosted episode with `depthReached ≥ 2`.

## The eight SPEC items, independently

**1. ≥2 completed rounds after fillers set — CONFIRMED TRUE.** My re-fetch of
`GET /rounds?league_id=league_462e0339…`: rounds 1, 2, 3 all `completed` with `error: null`
(round 4 `pending`), matching VERIFY.md:60-99. Fillers: log.md:50-51 orders `50 fillers 200`
before `unpause … trigger-round` and the league row carries both filler version ids
(VERIFY.md:41-55); rounds 2 and 3 (created 04:01:55Z / 04:16:57Z, completed 04:05:39Z /
04:20:42Z) are unambiguously after filler registration, which alone satisfies "≥2". One
correction to the verifier's prose: VERIFY.md:104-106 says all three rounds were created "after
the fillers were registered at 03:47:48Z" while quoting round 1's `created_at` as 03:46:55Z —
03:46:55 is not after 03:47:48. The log.md 03:47:48Z stamps are a batch flush, so the strict
round-1 ordering is unprovable from timestamps; it does not matter, because the item needs only
two rounds and has three, and `entrant_policy_version_ids` in every round contain only the two
champion versions (VERIFY.md:96-101).

**2. Both champions ranked, fillers absent/Baseline — CONFIRMED TRUE.** My re-fetch of
`GET /divisions/div_03513e99…/leaderboard`: exactly two rows — rank 1 `daveey-1`
(`nethack-loremaster:v1`), rank 2 `daveey` (`nethack-divemaster:v1`), both `rounds_played: 3`;
neither `nethack-delver:v1` nor `nethack-bumbler:v1` appears (satisfied by absence). Matches
VERIFY.md:112-160.

**3. Latest round's episode requests completed with replay_url, correct participants —
CONFIRMED TRUE.** VERIFY.md:183-248: round 3 (`round_b7f16922…`) has two episode requests, both
`status: "completed"`, both with non-null S3 `replay_url`s, participants `daveey-1`/
`nethack-loremaster` v1 and `daveey`/`nethack-divemaster` v1, `is_filler: false` on both. I
independently confirmed the primary replay URL is live (my S3 fetch returned HTTP 200, 40485
bytes). The one-participant-per-episode shape is the declared single-seat design (num_agents = 1
in both variants, my manifest fetch), so "participants named correctly" is met across the round's
two episodes.

**4. Replay bytes valid, protocol matches, reason complete, champions doing the thing —
CONFIRMED TRUE**, by my own full re-run (ruling B above). VERIFY.md:283-404. The design-note
substitute's depth/`down` thresholds are unmet 6/6 and recorded as a material non-blocking
game-balance finding, not a check-4 failure. I also endorse the verifier's honest note
(VERIFY.md:337-341) that the `"nethack/v1"` string is tool-emitted; the byte-level identity is
the `COWLDNET` header's length-prefixed `nethack`, which I dumped myself and which matches the
manifest's game name.

**5. Hosted game log clean — CONFIRMED TRUE.** My own re-fetch of
`/episode-requests/ereq_ad3b82c9…/artifacts/logs` (elevated header, HTTP 200, 5254 bytes —
same byte count as VERIFY.md:416), decoded per byte-string repr and grepped for
`falling back|LLM provider is unavailable|cut off at max_tokens|rejected`: **CLEAN**. The
`attempt 1 failed, will retry` line (VERIFY.md:441) matches none of the four patterns and
`fallbackTurns == 0` in the results confirms the retry never became a fallback. VERIFY.md:415-477
covers the second round-3 log and both round-2 logs the same way.

**6. Public page featured match + static iframe src — CONFIRMED TRUE** under ruling A above.
Static path verified at head by my own session-endpoint call (cow_id ✓, manifest sha ✓,
`index.html` static route ✓, `ready: true` ✓, no `/client/replay` ✓); featured match present in
`state.pool.replays` (now round-3 episodes, my re-fetch), absent from the playlist for the
structural single-seat reason cross-checked platform-wide (VERIFY.md:544-567) and already
accepted on the shipped procgen run (`runs/2026-08-28-procgen/VERIFY.md:426,460-466`).

**7. Certification declared the static bundle — CONFIRMED TRUE.** Read myself from the committed
`runs/2026-08-28-nethack/release-result.json`: `certify.replay_liveness` = "Replay liveness:
skipped (static replay bundle declared; /client/replay and /replay not required)" — the required
string verbatim — and the same line appears in `certify.output_tail` after "Transcript:
coworld-executable (10 steps passed)"; `ok: true`, `hosted_smoke: "passed"`,
`hosted_certification: "certified"`, `canonical: true`, `manifest_sha` matching. VERIFY.md:609-633.

**8. Viewer actually renders, three-clock scrub, judgment paragraph — CONFIRMED TRUE.**
CI is a fact I checked: `gh run view 33233650158` → workflow `viewer-check`, `status completed`,
`conclusion success`, created 2026-08-29T04:22:11Z (two seconds after the verifier's recorded
dispatch stamp, VERIFY.md:644-650); corroborating run 33233338285 also `success`. The committed
`viewer-check/viewer-smoke.json` (read myself): `loaded: true`, `signals.data_replay_loaded:
"true"`, `data_replay_error: null`, `failure: null`, and three **distinct** scrub clocks
(`T:0` → `T:9` → `T:17`) — (a) and (b) both hold. (c) I looked at `viewer-smoke.png` myself and
it reconciles with the replay JSON I expanded: the feed's `PLAN 1 — MOVE·MOVE·MOVE·MOVE·MOVE·
SEARCH·SEARCH·SEARCH` + "Starting exploration. Moving east and south to find stairs down." and
`PLAN 2` + "Exploring south from starting room to find stairs down." are byte-identical to
`plans[0]/says[0]` and `plans[1]/says[1]` of my `ep.json`; the ASCII terminal shows `@`, `<`, the
status line `Dlvl:1 $:0 HP:16(16) AC:7 Xp:1/0 T:18 Not Hungry`; the DL1–DL8 ladder lights only
DL1 (matching `depthReached: 1`); scorebug shows the two-name-space rule (`ALPHA THE DIGGER` /
`LOREMASTER`); the starter transport strip reads `18 / 156` with speed chips. The verifier's
judgment paragraph (VERIFY.md:770-816) is legible, shows the game, and says the imperfections
plainly; I co-sign it. Non-blocking observations I verified in the JSON myself: the 15 leftover
coworld-ctf art 404s in `console_tail` (`art/lockerroom/*.webp`, `soldier_yellow_front_gun.png`),
`feed_lines: 0` being a selector mismatch contradicted by the screenshot, and the scrub input's
range covering only ~18 of 156 ticks at capture time (motion proven; full-length seek not).

## Non-blocking observations (roll-up for the coordinator)

- **Game balance / headline dimension unreached** (ruling B): 6/6 hosted episodes at
  `depthReached 1`, zero `down` verbs, best episode ended by ascending; design.md's own phase-60
  criterion unmet. Settle with tuning + one hosted episode at depth ≥ 2.
- **SPEC item 6 wording gap for single-seat coworlds** (ruling A): playlist is structurally empty
  at `num_agents = 1`; the featured match lives in `state.pool.replays`. Document it.
- Dead asset requests: 15 leftover starter-art 404s on every spectator page load.
- `viewer_smoke.mjs` feed selector doesn't match this shell's DOM (`feed_lines: 0` vs a visibly
  populated feed).
- Scrub range only reaches ~tick 18 within the smoke window; a note for whoever next touches the
  transport.
- VERIFY.md:104-106 timestamp prose error (round 1 `created_at` 03:46:55Z is before, not after,
  the 03:47:48Z log stamp); immaterial to item 1.

BLOCKING: 0
