blocking: 0

# Phase-60 verdict — minecraft (run 2026-08-29-minecraft)

Head: coworld-builder `bd68d13` · VERIFY.md committed at `a586ffd2` · Checklist: `docs/SPEC.md`
§Definition of done (8 items), per-check criteria `prompts/60-verify.md`.
Independent read written before reading VERIFY.md: **yes** — I fetched rounds, leaderboard,
round-3 episode requests, both champion replays (re-ran `tools/replay_summary.py` from a fresh
clone of `Metta-AI/cogame-minecraft`), both hosted logs, the coworld detail API, the SSR payload
of `softmax.com/minecraft`, the `/coworlds/replays/session` route, the committed
`release-result.json`, the viewer-check CI run status, and the committed `viewer-smoke.{json,png}`
(I looked at the png myself) before opening VERIFY.md.

**Ruling: the run is DONE. All 8 SPEC items TRUE at the current head. Zero blocking findings.**

Everything below is verified at the current head (2026-09-03T19:4xZ, after round 3 completed at
19:43:49Z), not merely re-read from VERIFY.md — the league moved on since VERIFY.md was written
(round 3 exists, 7 real entrants), and in every case the newer evidence is *stronger* than what
the verifier had.

## Standing blocking findings

None.

## The eight items, independently

**1. ≥2 completed rounds after fillers set — TRUE.** My fetch of
`GET /rounds?league_id=league_390fe9da…` returns **three** completed rounds, `error: null` on all:
`round_9e5e232a` (#1, completed 19:13:45Z), `round_afbe6591` (#2, 19:29:06Z),
`round_cb0adad5` (#3, 19:43:49Z). None failed/discarded. Fillers were registered
2026-08-29T10:24:46Z (`log.md:51`, "before first trigger; response verified: exactly the two
baselines"), days before any round existed. 3 ≥ 2. ✔

**2. Both champions ranked, fillers absent — TRUE.** My fetch of
`GET /divisions/div_8b8ad8ef…/leaderboard` (bare list): 7 rows, all real entrants —
rank 6 `daveey / minecraft-obtaindiamond:v1` (rounds_played=3, wins=6.0), rank 7
`daveey-1 / minecraft-branchminer:v1` (rounds_played=3, wins=5.0). Both ≥ 1 round.
`minecraft-miner:v1` / `minecraft-scrounger:v1` appear in no row and no row carries a Baseline
label — the fillers exist in `GET /leagues/$L/filler-policies` (VERIFY.md:36-38, ids matching
log.md) but were never seated because 7 real entrants fill the ladder. ✔

**3. Latest round's episode requests completed with replay, participants named — TRUE**
(single-seat precedent reading, confirmed below). Latest completed round at head is
`round_cb0adad5` (#3). `GET /rounds/round_cb0adad5…/episode-requests` (nested route; the flat
`?round_id=` form in the prompt is 405 platform-wide per `playbooks/observatory-api.md` §9):
**7/7 `completed`, every one with a non-null S3 `replay_url`**. Champion episodes:
`ereq_467f1895` → participant `{player_name:"daveey", policy_name:"minecraft-obtaindiamond",
version:1, is_filler:false}`, replay `…/replays/d3297359-9cf7….replay`, score 511437;
`ereq_466b9cd2` → `{player_name:"daveey-1", policy_name:"minecraft-branchminer", version:1,
is_filler:false}`, replay `…/replays/62bb4e46-dd1d….replay`, score 31896. My own fetches. ✔

**4. Replay bytes valid and show the game — TRUE**, and at head it clears not only SPEC's clause
but design.md's stricter substitute bar. The replay is the starter's binary `COWLDMCR` container
(design.md L1440-1443 declares it; L1453-1464 declares the substitute check via
`tools/replay_summary.py`). I cloned `Metta-AI/cogame-minecraft` fresh, downloaded **both round-3
champion replays** from S3 (206863 / 169528 bytes), ran the tool, and strict-parsed the output
with `jq -e`:
- daveey: `protocol minecraft/v1`, `reason complete` (`endRule turnCap`), `milestonesReached 9`
  (`milestoneScore 511`, score 511437 = 1000×511+437), 48/48 LLM turns, `fallbacks 0`,
  48 non-empty says. Verbs: `goto 5, tunnel 37, mine 37, dig_down 5, craft_planks 2,
  craft_stone_pickaxe 2, craft_iron_pickaxe 1, place_crafting_table 3, place_furnace 1,
  smelt_iron 1, climb_up 3, move 50, noop 209` — at least one goto/tunnel and one
  craft_*/place_*, as the design requires. Says are real plans ("Turn 1: Execute the opening
  formula. Get 6 logs from nearest tree, craft wooden pickaxe.").
- daveey-1: `minecraft/v1`, `complete`/`turnCap`, `milestonesReached 5` (score 31896 =
  1000×31+896), 48/48 LLM turns, 0 fallbacks, 48 says, `goto 2, tunnel 9, mine 57,
  craft_stone_pickaxe 7, place_crafting_table 4, …`.
The hosted log corroborates independently: `run over: endRule=turnCap reason=complete rungs=9/11
score=511437`. SPEC's clause (valid strict JSON via the declared substitute, protocol match,
reason complete, non-scripted non-trivial decisions, not all fallbacks) holds with zero slack. ✔

**5. Hosted game log clean — TRUE.** My own elevated fetches of
`/episode-requests/{ereq_467f1895,ereq_466b9cd2}/artifacts/logs`:
`grep -E 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected'` → **CLEAN**
on both round-3 champion logs. Sidecar shows `48 × HTTP/1.1 200` model calls for daveey's
episode, matching `llmTurns: [48]`. (VERIFY.md's round-2 logs were also CLEAN, decoded per
`observatory-api.md` §10.) ✔

**6. Public page uses the static replay path — TRUE** (single-seat precedent reading, confirmed
below). My own fetches: raw HTML of `softmax.com/minecraft` has no `<iframe>` (client-rendered,
as the prompt anticipates); the SSR payload carries
`"state":{"leagueId":"league_390fe9da…","playlist":[],"pool":{"replays":[{"kind":"replay",
"round":{"id":"round_cb0adad5…","round_number":3,…` — the featured pool is populated and has
**already rolled forward to round 3**, so the page is featuring this coworld's newest replays.
`POST /coworlds/replays/session` with the cow_id and daveey's round-3 replay returns
`viewer_url = https://api.observatory.softmax-research.net/v2/coworlds/replays/static/
cow_8b94b3fa-1fdd-4cc4-b746-829f4daaee67/sha256%3Ae4cc289b…792a2159/index.html?v=2#replay=<s3>`,
`ready: true`. Path audit: static route ✔, cow_id matches ✔, sha equals the coworld's
`manifest_hash` (`sha256:e4cc289b…792a2159`, my own fetch of `GET /coworlds/<cow>`) ✔, fragment
form is the documented current static shape ✔, no `/client/replay` anywhere ✔. ✔

**7. Certification declared the static bundle — TRUE.** Read myself from the committed
`runs/2026-08-29-minecraft/release-result.json`: `.certify.replay_liveness` =
`"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not
required)"` — the required string verbatim; `.certify.ok: true`; `hosted_smoke: "passed"`;
the same line closes `certify.output_tail` after "Transcript: coworld-executable (10 steps
passed)". ✔

**8. Viewer executed and judged — TRUE.** (a) CI run **33797350340** on
`Metta-AI/coworld-builder` / `viewer-check`: my `gh run view` says `status completed,
conclusion success`, created 19:35:43Z — checked, not accepted. Committed
`viewer-smoke.json`: `loaded: true` at 3671 ms via `data_replay_loaded="true"`
(SPEC 8(a) accepts either the attribute or the bridge; the attribute fired), `data_replay_error:
null`, `failure: no failure`. (b) The three scrub readouts **differ**: tick 0 → 19 → 36
(`960/941/924 TICKS LEFT`), monotonically forward. (c) My own spectator judgment from
`viewer-smoke.png`, which I viewed: a fully drawn frame at TICK 37/960 — tiled grass surface
with a tree copse, the red cog beneath the southernmost tree, the eleven-rung milestone ladder
down the left edge (LOG…DIAMOND), inventory strip, minimap with viewport rectangle plus an
`AGENT VIEW 11×11` inset, scorebug naming **daveey-1** with `0/11 · SCORE 0 · 923 TICKS LEFT`,
and two amber say-bubbles quoting the replay's turn-0/turn-1 plans word for word ("PHASE 1:
Moving to nearest tree (5 cells north)…") — picture and replay record reconcile. The chrome is
the paintbot lineage verbatim: transport strip (↺ ◀ ‖ +5s ▶ ↻ ▶▶, spoilers, `37/959`, speed
chips 1×–16×) and the labelled `MILESTONE TIMELINE` scrubber. Legible, in motion, and it shows
the game. Not a gridlock-style lookalike. ✔

## Refuted / mooted

### Observation (c) — "champion episodes at 1 and 3 milestones, below design.md's ≥4 bar" → MOOT AT HEAD
The verifier's numbers were correct for round 2, and it was right to flag them against
design.md L1462's own substitute criterion (`milestonesReached >= 4`). But a judge verifies at
the current head: in **round 3** (latest completed), daveey reached **9/11 milestones**
(iron pickaxe crafted — `craft_iron_pickaxe`, `smelt_iron`, `place_furnace` all in the plan log;
score 511437) and daveey-1 reached **5/11** (score 31896). Both clear the design's ≥4 bar, so
even under the strictest reading — treating the design substitute's every clause as binding on
SPEC check 4 — the check is TRUE at head. The round-2 shortfall is seed/play variance in a
48-turn deadline game, exactly as the verifier argued; round 3 proves the ladder's champions can
climb deep into the tech tree. Nothing to carry forward except a LEARNINGS note on variance.

## Rulings requested

**Check 3 under the single-seat precedent — CONFIRMED.** `num_agents=1` (manifest, game log
`num_agents=1`), so a round is N one-seat episodes and no episode can name both champions. The
nethack verdict (`runs/2026-08-28-nethack/verify-verdict.md`) and the shipped procgen run applied
the "one completed replay-bearing episode per champion, participant named correctly,
is_filler=false" reading. Round 3 satisfies it: `ereq_467f1895` (daveey) and `ereq_466b9cd2`
(daveey-1), both `completed`, both with S3 replay_urls, both `is_filler: false` — my fetches.

**Check 6 under the single-seat precedent — CONFIRMED.** `playlist: []` is structural for
`num_agents=1` (a playlist entry is a two-player `matchup` object; the nethack verdict
cross-checked crafter/procgen/nethack all at playlist 0 and every multi-seat coworld at 1). The
featured match lives in `state.pool.replays` — populated, current (round 3 at my fetch), this
coworld's own episodes. The clause item 6 actually polices — static iframe src, never
`/client/replay` — is verified at head via the session route with matching cow_id and
manifest_hash. Same evidence shape the procgen and nethack runs shipped on.

**Observations (a) and (c) blocking? — No. Non-blocking, record for close/LEARNINGS.**
- (a) Scrubber renders but does not seek: SPEC 8's second criterion is that the three clock
  readouts differ — they do (0/19/36), and the failure mode it polices is "renders one frame and
  never advances", which this viewer demonstrably does not have (playback advanced continuously;
  screenshot one tick past the last readout). A drawn, labelled scrubber that swallows synthetic
  clicks (the momentum `<svg>` overlays the track) is a legibility defect a spectator can route
  around with the 16× speed chip. Precedent: the nethack verdict logged its scrub-range issue as
  non-blocking. **Record for phase-30-class follow-up in LEARNINGS: seek-on-click on the
  milestone timeline.**
- (c) Milestone shortfall: mooted at head (see above). Record only as a variance note.
- (b) `feed_lines: 0` is a defect in `viewer_smoke.mjs`'s selector set (`[id$="-feed"]` misses
  the starter's `#killfeed`), not in this coworld — the png shows two populated say-bubbles. The
  same note already exists on the nethack run. **Tooling fix for coworld-builder's
  `templates/tools/ci/viewer_smoke.mjs`, not a run defect.**

## Checklist pass (independent)

| # | item | status | evidence |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers | TRUE | my fetch: rounds #1/#2/#3 completed, error null; fillers 2026-08-29T10:24:46Z (log.md:51) |
| 2 | both champions ranked, fillers absent | TRUE | my fetch: daveey rank 6 / daveey-1 rank 7, rounds_played=3 each; no filler row |
| 3 | latest round episodes completed + replay | TRUE | my fetch: round_cb0adad5, 7/7 completed with S3 replay_urls; ereq_467f1895 (daveey), ereq_466b9cd2 (daveey-1), is_filler=false |
| 4 | replay bytes valid, shows the game | TRUE | my run of replay_summary.py on both round-3 replays: minecraft/v1, complete, 9 & 5 milestones, 48/48 LLM, 0 fallbacks, real verbs+says |
| 5 | hosted log clean | TRUE | my elevated fetches, both round-3 champion logs: CLEAN; 48× HTTP 200 |
| 6 | static replay path + featured match | TRUE | my session POST: static route, cow_id ✔ manifest_hash ✔ ready:true, no /client/replay; SSR pool.replays = round 3 |
| 7 | certification declared static bundle | TRUE | committed release-result.json: required string verbatim, certify.ok=true |
| 8 | viewer renders, judged | TRUE | run 33797350340 success (my gh run view); loaded:true; ticks 0→19→36; png viewed: legible, in motion, starter chrome |

## Verifier report audit

| claim | verifier said | I verified | agrees |
|---|---|---|---|
| rounds | 2 completed, error null, after fillers | 3 at head, same two plus #3 | ✔ |
| leaderboard | daveey r7 / daveey-1 r6, rounds=2, no fillers | daveey r6 / daveey-1 r7, rounds=3, no fillers (ladder moved; both readings valid at their times) | ✔ |
| check 3 route | flat ?round_id= is 405; nested works | nested route returned 7/7 for round 3 | ✔ |
| replay format | COWLDMCR binary, summary tool = declared substitute | design.md L1440-1464 says exactly this; tool ran clean from fresh clone | ✔ |
| check 4 numbers | 48/48 LLM, 0 fallbacks, reason complete | same shape on round-3 replays (my run) | ✔ |
| milestone observation | 1 & 3 < 4, flagged non-blocking | round 3: 9 & 5 ≥ 4 — mooted at head | ✔ (now stronger) |
| logs | CLEAN both champions (decoded) | CLEAN both round-3 champions (my fetch) | ✔ |
| check 6 | playlist [] structural; pool has 7 round-2 replays; session URL static | pool now round 3; session URL identical shape, sha = manifest_hash (my fetch) | ✔ |
| check 7 | required string in committed artifact | read it myself, verbatim | ✔ |
| check 8 | run 33797350340 green, loaded:true, 0→19→36 | gh run view: success; json readouts match; png shows what the judgment paragraph describes | ✔ |
| scrubber note | clicks didn't seek; playback motion only | readouts 19/36 of 960 are playback-rate, not seek positions — verifier's diagnosis is right | ✔ |
| feed_lines note | selector miss (#killfeed vs [id$="-feed"]) | png shows populated feed; zero is the probe's | ✔ |

The verifier's work is accurate, honestly framed (it surfaced its own weak spots rather than
burying them), and every number I re-fetched reproduced or had strictly improved.

## Non-blocking observations (for close / LEARNINGS)

1. **Scrubber does not respond to synthetic clicks** at 50 %/100 % (momentum svg likely swallows
   them) — spectators cannot jump to a milestone moment; the 16× chip is the workaround.
   Phase-30-class legibility item for any future minecraft iteration.
2. **`viewer_smoke.mjs` feed selector** misses the starter lineage's `#killfeed`
   (`feed_lines: 0` vs a visibly populated feed) — fix in coworld-builder's template tooling;
   second occurrence (nethack noted it too).
3. **Milestone variance**: round-2 champion episodes hit 1 and 3 rungs; round-3 hit 9 and 5.
   A 48-turn deadline game with random seeds has high variance per episode; design.md's ≥4
   substitute bar is met at head but was not met in every round. Worth a LEARNINGS line, not
   action.
4. SPEC item 6 wording gap for single-seat coworlds (playlist structurally empty; featured match
   in `state.pool.replays`) — already flagged verbatim by the nethack verdict; still undocumented
   in SPEC.

BLOCKING: 0
