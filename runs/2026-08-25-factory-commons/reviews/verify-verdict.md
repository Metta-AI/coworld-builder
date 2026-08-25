blocking: 0

# Phase-60 verdict — factory-commons
Judge: fresh context. Read order: SPEC §Definition of done → prompts/60-verify.md → VERIFY.md →
committed viewer-check artifacts (json + png) → release-result.json. Independent spot-re-fetches
made 2026-08-25T23:00Z against BASE=https://softmax.com/api/observatory/v2.

## Verdict: VERIFY.md's all-true (8/8) is CONFIRMED. Zero blocking findings.

## Check-by-check adjudication

| # | VERIFY says | I re-verified | verdict |
|---|---|---|---|
| 1 | TRUE — rounds 2,3,4 completed; r1 failed pre-fillers | Fresh `GET /rounds?league_id=league_96744093…`: rounds 2 (completed 22:12:11Z), 3 (22:23:29Z), 4 (22:49:14Z) all `completed`; round 1 `failed` with the quoted Temporal error; round 5 `pending`. `log.md:50` records fillers POST 200 at 22:08:38Z; rounds 3 (created 22:20:25Z) and 4 (created 22:35:26Z) are both post-fillers, so ≥2 holds under the strict reading. | TRUE |
| 2 | TRUE — both champions ranked, fillers absent | Fresh leaderboard: exactly 2 rows — `1 daveey-1 factory-commons-custodian:v2 1014.67 rp=3 wins=2.0`, `2 daveey factory-commons-foreman:v2 985.33 rp=3 wins=1.0`. Both `rounds_played ≥ 1`; steward/stripper absent entirely. | TRUE |
| 3 | TRUE — round 4's ereq completed with replay | Fresh: `ereq_558ec460…` `status:"completed"`, replay_url `…/83ef5ad4-38b7-47a2-83e2-1694de64d1e7.replay`; participants = foreman/daveey (seat 0, is_filler:false), custodian/daveey-1 (seat 1, is_filler:false), steward/daveey (seat 2, is_filler:true). Matches VERIFY byte-for-byte. | TRUE |
| 4 | TRUE — valid JSON, protocol matches, complete, 0 fallbacks | Re-downloaded the replay (S3 200, 200 972 bytes, last-modified 22:49:14Z): strict `jq -e` parses; `protocol == "factory_commons.replay.v1"` — matches design.md:719/726; `results.reason == "complete"`, ending `shift_limit`; order sources seat0 llm×15, seat1 llm×15, seat2 scripted×15; fallback events = 0 and `results.fallbacks == [0,0,0]`. All 30 champion decisions LLM, none fallback. | TRUE |
| 5 | TRUE — hosted log clean | Re-fetched `…/artifacts/logs` with elevated header (70 082 raw bytes), decoded the `b'…'` reprs: **0 matches** on `falling back|LLM provider is unavailable|cut off at max_tokens|rejected`, and 0 throttle/`Too many tokens` lines for this episode. VERIFY's round-2 throttle digression is properly labelled as not the evidence episode and cross-checked against two other coworlds — the correct wait-and-repoll path was in fact taken (rounds 3/4 clean). | TRUE |
| 6 | TRUE — featured match in SSR; static iframe src | Fresh fetch of `https://softmax.com/factory-commons` (553 460 bytes, `<title>Factory Commons · Softmax</title>`): SSR `playlist[0]` = `factory_commons.r4.e1`, replayUrl = the check-3/4 replay, matchup names both champions. `POST /coworlds/replays/session` returns `viewer_url` `…/v2/coworlds/replays/static/cow_2e5dc1a2…/sha256%3Aa63d2c7f…/index.html?replay=<s3 url>&v=2`, `ready:true` — the static path, sha byte-identical to `STATE.coworld.manifest_sha`, not a `/client/replay` pod URL. VERIFY correctly recorded which source it used (SSR + session call) after the raw-HTML grep found nothing. | TRUE |
| 7 | TRUE — static bundle declared | Committed `runs/2026-08-25-factory-commons/release-result.json` (release run 32902713785): `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)`; `hosted_certification: "certified"`, `canonical: true`, 10/10 cert steps `[pass]`. Read from the committed copy as the prompt requires. | TRUE |
| 8 | TRUE — loaded:true, three differing clocks, judgment | `gh run view 32908246409` → `conclusion: "success"` (verified, not accepted). Committed `viewer-smoke.json`: `loaded:true` at 1 923 ms via `data_replay_loaded:"true"`, `data_replay_error:null`, `failure:null`; `url` field byte-matches the check-6 iframe src. Scrub readouts differ: `SHIFT 1 / 15 TICK 2 OF 899` → `SHIFT 8 / 15 TICK 466 OF 899` → `FINAL SHIFT LIMIT`. I viewed `viewer-smoke.png` myself: a legible endcard-over-board frame — INTEGRITY 78 / CAP 100 / 91 BANANAS / 0 OVERRIDES, per-seat rows COTTER 71 / RATCHET 18 / BOLT 0, REASON COMPLETE — every number reconciling with `results` (`scores [0,71,18]`, `presses [15,1,10]`, `repairs [2,0,4]`, `integrity_final 78`, `bananas_made 91`); the starter's transport strip, speed chips, scrub track and momentum SVG are all present (coworld-ctf chrome, not a rewrite). VERIFY's judgment paragraph accurately describes what the png shows. | TRUE |

## The three recorded legibility observations — do any rise to a DoD failure?

1. **Endcard feed empty** (`feed_lines: 0`, empty feed in png). Check 8(c) demands a legible
   picture that shows the game; the picture is legible and shows the game via scorebug, roster,
   endcard and board. An aged-out feed at the terminal frame is a polish item, not a DoD check.
   **Not a failure.**
2. **Transport win-chip reads `DRAW`** while `results.win == [false,true,false]` and both the
   roster chips and the endcard name the true winner (Cotter/daveey-1, 71). Confirmed in the png:
   `DRAW` is visible next to `899 / 899`. This is a real display bug — one UI element contradicts
   two correct ones — but no DoD item requires the win-chip specifically, the winner **is**
   legible on screen twice, and it does not make the picture unreadable or un-game-like. The
   closest DoD hook, 8(c) legibility, still holds. **Not a failure; should be logged as residue /
   a learnings entry for the viewer template.**
3. **Player names instead of policy names on screen.** The viewer renders what the platform put
   in `results.names` (`["daveey","daveey-1","Baseline"]`); policy names do appear spectator-side
   on the leaderboard (`policy_label` in check 2) and in the SSR matchup. The SPEC's two-namespace
   pin is a design/phase-30 concern, and the cause here is upstream platform data, not this
   coworld's viewer. **Not a failure.**

## Non-blocking observations (mine, not the verifier's)

- `viewer-smoke.json` `console_tail` shows a 404 for `font.ttf` in the static bundle
  (`…/sha256%3Aa63d2c7f…/font.ttf` → 404, net::ERR_ABORTED). The png proves text renders fine on
  a fallback font, so check 8 is unaffected, but VERIFY.md did not mention it. Worth a look —
  either the bundle should ship the font or the CSS should not reference it.
- Minor evidence inconsistency in VERIFY check 6's SSR excerpt: it pastes `"win_rate":1` for
  daveey-1 while check 2's raw and my fresh fetch both show `0.6667` (`episode_wins 2 / 3`).
  Immaterial — the check-6 requirement (featured match present, static iframe path) is verified
  fresh and independently.
- VERIFY discloses an earlier uncommitted viewer-check run (32905429599) against round 2's
  replay; the committed evidence is correctly the later run against the current featured match.

## Blocking items

(none)

BLOCKING: 0
