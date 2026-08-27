blocking: 0

# verify verdict — fog-of-war-boards (phase 60)

Head: 493f54a (coworld-builder; `60 fog-of-war-boards: VERIFY.md 8/8 TRUE + viewer-check artifact (run 33036080393)`)
Checklist: `docs/SPEC.md` §Definition of done (phase 60) / `prompts/60-verify.md`
Independent read written before reading fixes: yes — I read SPEC, the prompt, VERIFY.md, the
committed viewer-check artifacts (including the PNG, whole-image and brightened crops of both
belief boards), STATE.json, release-result.json, the design note's replay-protocol section
(design.md §"Replay bytes (self-sufficient)"), and the repo's `coworld_manifest_template.json`,
and re-fetched every live endpoint myself before concluding. There is no fixer report in this
phase; the audited document is VERIFY.md itself.

Rulings inherited, not re-litigated: round-1 exclusion from check 1 (single-entrant proven via
`entrant_attributions`); `results.reason=="complete"` so the deadline exception is unused; the
round-2 Bedrock throttle adjudicated platform-wide with round 3 CLEAN as check-5 evidence; the
three legibility notes filed as non-blocking phase-30 observations.

## Standing blocking findings

None.

## Refuted / attempted refutations

I attacked each check's evidence for inference, staleness, and miscitation. Nothing fell.

- **Check 4 "protocol matches the manifest"** — the one interpretive move in VERIFY.md. The
  hosted manifest indeed does not restate the protocol string: the repo's
  `coworld_manifest_template.json` carries only `replay_viewer.bundle` (templated to the sha)
  and zero occurrences of `fogboards.replay.v1`. The declaring document is
  design.md §"Replay bytes (self-sufficient)" (~line 761), which pins
  `"protocol": "fogboards.replay.v1"` verbatim. The replay bytes I fetched match it. The
  verifier's reading is correct, not a dodge.
- **Check 6 "Source C"** — VERIFY.md uses two sources the prompt does not spell out (SSR
  `state.playlist[0]` + `POST /coworlds/replays/session`) after the prompt's two sources (A:
  HTML iframe grep, B: `/coworlds` detail) returned documented platform nulls. I confirmed A
  and B are genuinely empty (page HTML has 0 `iframe` occurrences; `/coworlds` returns
  `replay_viewer:null, featured_match:null`), that the session POST is what the page's JS
  calls, and that the returned `viewer_url` is the static path with the sha equal to
  `STATE.coworld.manifest_sha`. The fallback is sound and — decisively — check 8 loaded that
  exact URL in a real browser and it rendered. Not a miscite.
- **Check 8 judgment paragraph fabrication test** — every visual claim I could falsify from
  the committed PNG holds, including the fine-grained ones: guesses (blue dashed ring + grey X)
  at a3 and c1 on `DAVEEY SEES`; the grey-ringed red X at b2 and the red dashed guess ring
  overlaid on daveey-1's own b3 stone on `DAVEEY-1 SEES` (verified from brightened crops);
  the a1→b2→c3 amber win stroke; the endcard table matching `results` cell-for-cell; the
  9-tick scrubber with the taller amber third tick (the `occupied` discovery beat) and `9 / 9`
  counter; scorebug `3 STONES 0 LINE IN` / `2 STONES — LINE IN` matching
  `stones:[3,2]`, `distToWin:[0,99]`. The paragraph was written from the picture, not invented.

## Checklist pass (independent — all evidence re-fetched 2026-08-27, this session)

| # | item | status | evidence |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers | TRUE | Live `GET /rounds?league_id=$L`: rounds 2 (03:01:15Z) and 3 (03:15:32Z) `completed`; round 1 `failed` with `Temporal RoundWorkflow failed before settling the round.` excluded (ruled); a round 4 has since gone pending→completed, which only strengthens the count. Filler-before-round-2 ordering pinned by `entrant_attributions` (r1: one entrant; r2/r3: both champions). |
| 2 | Both champions ranked, fillers absent/Baseline | TRUE | Live `GET /divisions/$D/leaderboard`: `1 daveey fog-of-war-boards-cartographer:v1 rounds_played=2`, `2 daveey-1 fog-of-war-boards-prober:v1 rounds_played=2`; no filler row present. |
| 3 | Latest round's ereq completed w/ replay, participants named | TRUE | Live `GET /episode-requests/ereq_999e93c3…`: `status:"completed"`, `replay_url` non-null, participants daveey + daveey-1, both `is_filler:false`. Nested-route deviation (flat GET 405s) is documented in VERIFY.md and playbook §9. |
| 4 | Replay bytes valid, protocol matches, complete, non-scripted | TRUE | I re-fetched the S3 bytes: HTTP 200, 4212 B, strict `jq -e` pass + strict Python UTF-8 decode; `protocol=fogboards.replay.v1` (= design.md declaration; manifest silent, see above); `results.reason="complete"`; `fallbacks:[0,0]`, 6/6 attempts non-scripted with substantive `say`/`notes`. |
| 5 | Hosted log clean | TRUE | I re-fetched `artifacts/logs` for ereq_999e93c3 (round 3): HTTP 200, 14137 B, grep for all four patterns = 0 matches on raw bytes. Round-2 throttle: platform-wide ruling inherited; VERIFY.md's cross-check against negotiation-games (same 429/model/message, overlapping window, disjoint codebase) is exactly what the prompt requires. |
| 6 | Public page uses static replay path; featured match present | TRUE | Live `POST /coworlds/replays/session` returns `/v2/coworlds/replays/static/cow_5f8e4d33…/sha256%3A3af044a2…/index.html?replay=<s3>&v=2`, `ready:true`; sha == `STATE.coworld.manifest_sha`; no `/client/replay` anywhere. Live page SSR playlist now carries round 4's episode (`fog-of-war-boards.r4.e1`, same coworld/division, two-player matchup) — featured match present and updating as rounds complete; VERIFY.md's r3 snapshot was correct at its timestamp, not stale-cited. |
| 7 | Certification declared static bundle | TRUE | Committed `runs/<run>/release-result.json` (source the prompt requires): `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)`. Release run 33034451372 in Metta-AI/cogame-fog-of-war-boards: `conclusion: success` (checked via gh). |
| 8 | Viewer executed + spectator judgment | TRUE | viewer-check run 33036080393: `conclusion: success`, createdAt 03:20:40Z (> dispatch_at 03:20:39Z — race-safe identification verified). Committed `viewer-smoke.json`: `loaded:true` (2047 ms), `data_replay_loaded:"true"` **and** bridge `ready`, `failure:null`; three scrub clocks differ (PLY 0 → PLY 4 → PLY 6/FINAL, mover alternating correctly). PNG shows a legible, game-specific frame in the starter's chrome; judgment paragraph faithful to it (see refutation section). Artifacts committed under `runs/<run>/viewer-check/` at head 493f54a. |

## Verifier report audit

| check | verifier said | I verified | agrees |
|---|---|---|---|
| 1 | TRUE, rounds 2+3, r1 excluded | live re-fetch identical | yes |
| 2 | TRUE, both champions, fillers absent | live re-fetch identical | yes |
| 3 | TRUE via nested route | live re-fetch identical; deviation documented | yes |
| 4 | TRUE, protocol per design note | bytes re-fetched, manifest silence confirmed | yes |
| 5 | TRUE (r3 CLEAN; r2 platform-wide) | r3 log re-fetched, 0 matches | yes |
| 6 | TRUE via Source C | session POST + SSR playlist re-fetched | yes |
| 7 | TRUE from committed artifact | committed file read; release run green | yes |
| 8 | TRUE, loaded + advances + judgment | run green, json/png re-read, crops checked | yes |

## Non-blocking observations

- The three inherited legibility notes stand as filed (belief-board contrast at small widths,
  endcard occluding the truth board's middle rank incl. b2, `sense>0` chrome unexercised by
  this variant). I independently confirmed all three from the PNG; none touches a
  definition-of-done gate.
- `prompts/60-verify.md`'s printed flat route for check 3 and its A/B-only sourcing for check 6
  are both behind the live API; VERIFY.md's documented deviations are correct and could be
  folded back into the prompt text.

BLOCKING: 0
