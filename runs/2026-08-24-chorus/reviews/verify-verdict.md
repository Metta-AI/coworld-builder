blocking: 0

# phase-60 verdict — chorus
Head: cogame-chorus@3c11c9530e5b821ad3229f867982c540418cf4ac (main)   Checklist: prompts/60-verify.md §The eight checks / docs/SPEC.md §Definition of done   Independent read written before reading VERIFY.md / r2-fixes.md: yes

All evidence below was re-fetched by the judge on 2026-08-24 (post-remediation), not copied from
VERIFY.md. Verification is against the **current head**: coworld v0.1.3
(`cow_4a630880-4b06-4857-93a5-c05ad2a3e0d2`, canonical), repo head `3c11c953`.

## Standing blocking findings

None.

## Refuted / resolved

### B1 — VERIFY.md's own check-8 FALSE (viewer posted bridge `ready` before the first drawn frame) → RESOLVED AT HEAD
- The finding was real when written (3 reproductions: runs 32710507461 / 32710843104 / 32710988177,
  scrub 0% == 50% == the `BAR 0` shell placeholder, `data_replay_loaded: null` at sampling).
- Evidence at head: `Metta-AI/cogame-chorus@main` HEAD is `3c11c9530e5b821ad3229f867982c540418cf4ac`
  ("fix(replay-viewer): check 8 — post the bridge `ready` from the first drawn frame"; `attachReplay`
  gained `onLoaded`, fired after `data-replay-loaded="true"`; `static_replay.js` posts `ready` from
  there). Verified via `gh api repos/Metta-AI/cogame-chorus/branches/main`. CI on that sha: run
  32711994014, conclusion **success** (verified via `gh run view`).
- Re-run against the live embed src: viewer-check run **32715457303**, conclusion **success**
  (verified via `gh run view`, created 2026-08-24T10:10:50Z). Committed artifact
  `runs/2026-08-24-chorus/viewer-check/final-viewer-smoke.json`, re-read by the judge:
  `{"loaded":true,"ms":726,...}`, `signals.data_replay_loaded:"true"`, `bridge_ready:true`,
  `failure:null`; scrub readouts `0% = BAR 0 / 8 · D IONIAN · 96 BPM · WAITING ON 4`,
  `50% = BAR 4 / 8 · …`, `100% = FINAL — PIECE 63.7` — three differing clocks, and 63.7 matches the
  round-7 replay's `piece: 63.739576`. The URL inside that artifact is byte-identical to the
  `viewer_url` the session route returned to me live (see check 6/8 below). A finding that was true
  and has since been fixed is resolved, not standing: it counts zero.

## Checklist pass (independent, all re-fetched at head)

| item | status | evidence |
|---|---|---|
| 1. ≥2 completed rounds after fillers set | TRUE | `GET /rounds?league_id=league_472f2259…` → 7 rounds, all `status:"completed"`, every `error` null. Fillers set 08:37:43Z (log.md:39). Rounds 2–7 created 08:51:42Z–10:06:45Z, all post-filler; even excluding the two no-episode rounds (2, 6 — below), rounds 3, 4, 5, 7 = 4 completed rounds with real replayed episodes ≥ 2. No `failed`/`discarded` round exists. |
| 2. Both champions ranked; fillers absent/Baseline | TRUE | `GET /divisions/div_1bedcae9…/leaderboard` (bare list) → rank 3 `daveey` `chorus-cantor:v2` rounds_played 5; rank 4 `daveey-1` `chorus-weaver:v2` rounds_played 5 — both ≥ 1. No filler row at all (rows 1–2 are outside entrants `relh`/`richard`, not fillers). |
| 3. Latest round's episode completed with replay | TRUE | Latest completed round = 7 (`round_74bcd0cc…`) → `ereq_e4c3b612-34c5-4639-bf2b-69fb15de0e56`, `status:"completed"`, `replay_url: https://softmax-public.s3.amazonaws.com/replays/03e2ae73-….replay`, participants name `daveey` (chorus-cantor:v2) and `daveey-1` (chorus-weaver:v2) plus relh/richard; all four `participant_scores` populated. |
| 4. Replay bytes valid, show the game | TRUE | Fetched the S3 replay: python strict UTF-8 decode ok, `jq -e` ok; `protocol: chorus.replay.v1`; `results.reason: "complete"`; 32 `bar` events, **0** with `scripted:true` (champion seats included); 14 distinct step patterns; substantive `say` texts tracking the chord plan ("Opening motif on steps 0,4,8,12 with chord tones of vi…"). |
| 5. Hosted game log clean | TRUE | `GET /episode-requests/ereq_e4c3b612…/artifacts/logs` (elevated), 72,618 bytes: `grep -E 'falling back|LLM provider is unavailable|cut off at max_tokens|rejected'` → 0 hits, CLEAN. No exception needed. |
| 6. Public page uses static replay path; featured match present | TRUE | Raw HTML has no iframe (client-rendered, as the playbook records); SSR payload `state.playlist[0]` fetched live: round 7, `chorus.r7.e1`, coworldId `cow_4a630880…`, coworldVersion 0.1.3, replayUrl `…03e2ae73….replay`. `POST /coworlds/replays/session` → `ready:true`, `viewer_url = …/v2/coworlds/replays/static/cow_4a630880-4b06-4857-93a5-c05ad2a3e0d2/sha256%3Aa2b167967dc76dbfbfbb1455b272169e1a1468309d217a5d5afa2da9d17e7281/index.html?replay=…` — static route, `<sha>` = STATE.coworld.manifest_sha, not a `/client/replay` pod URL. |
| 7. Certification declared the static bundle | TRUE | Committed `runs/2026-08-24-chorus/release-result.json` (v0.1.3's: `.version = 0.1.3`, `.cow_id = cow_4a630880…`): `.certify.replay_liveness = "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"`. Release run 32713685596 conclusion **success**, headSha = 3c11c953 (verified via gh). |
| 8. Viewer executed and judged | TRUE | Run 32715457303 (**success**) against the exact live embed src from check 6 (URL match verified byte-for-byte inside the committed artifact). `loaded:true` with `data_replay_loaded:"true"` at sampling; three clock readouts differ (BAR 0 → BAR 4 → FINAL — PIECE 63.7). `final-viewer-smoke.png` re-viewed by the judge: starter-family chrome (CHORUS wordmark, clock, 4-plate scorebug with signed credits, sequencer lanes with cog sprites, chord ribbon, score strip with per-cog credit lines and zero rule, populated scrubber with colored beat markers, `43 / 43` pos, ♪ AUDIO in the transport band), endcard "FINAL — 8 BARS · PIECE 63.7 / RELH CARRIED THE PIECE" with ranked rows (voice, credit, notes played, piece-without-you) matching the replay's results (`scores [1.056, -0.034, 0.317, 1.018]`, piece 63.74). Legible, unmistakably this game, not a gridlock-style rewrite. |

## Fixer report audit (reviews/r2-fixes.md + VERIFY.md re-run section)

| finding | fixer/verifier said | I verified | agrees |
|---|---|---|---|
| check-8 ready-before-frame | fixed in 3c11c953, CI green 32711994014 | main HEAD = 3c11c953; `gh run view 32711994014` → success; commit message describes onLoaded-gated `ready` | yes |
| re-release v0.1.3 canonical/certified | run 32713685596 ok, canonical, cow_4a630880 | run success, headSha 3c11c953; `GET /coworlds` → cow_4a630880 `canonical:true`, version 0.1.3, manifest source_url pinned to tree/3c11c953 | yes |
| re-run check 8 vs live embed | run 32715457303, loaded true, 3 differing clocks | run success; committed final-viewer-smoke.json re-read; URL matches live session-route viewer_url; readouts as claimed | yes |
| committed release-result.json is v0.1.3's | claimed in re-run §2 | `.version 0.1.3`, `.cow_id cow_4a630880…` | yes |

## Non-blocking observations

- **Rounds 2 and 6 completed with no episode.** Both finished ~11 s after creation;
  `ereq_6aec867c…` and `ereq_343b2126…` are `status:"completed"` with `replay_url: null`,
  `episode_id: null`, `error: null`, `participant_scores: []`. Check 1 as written counts
  `completed` rounds and excludes only `failed`/`discarded` (there are none); even under the
  strictest reading that a countable round needs episode evidence, rounds 3, 4, 5, 7 (post-filler,
  completed, replayed) satisfy ≥ 2 on their own. Not blocking; looks like a platform-side ladder
  scheduling artifact, worth flagging to the operator.
- **Round 2 seated `chorus-arpeggio:v2` in both filler slots** (positions 2 and 3, `is_filler:true`
  each, verified from `ereq_6aec867c…`). No check governs per-round filler composition (check 2 is
  the leaderboard, check 3 the latest round, both clean); the manifest and league settings register
  both arpeggio and pedal fillers (log.md:39), so the duplicate pick is the platform's filler
  chooser, not this coworld. The episode in question never ran anyway. Not blocking.
- **Timestamp discrepancy on round 1:** VERIFY.md check 1 says fillers were registered "before
  round 1 was triggered at 08:37:43Z", but the API gives round 1 `created_at:
  2026-08-24T08:36:42.467201Z` — 61 s **before** the 08:37:43Z filler line. log.md:40's
  trigger-round entry shares the fillers' timestamp, so the log and the API disagree about round 1
  by about a minute. Immaterial to the verdict (rounds 2–7 are unambiguously post-filler and
  suffice), but VERIFY.md's "every round in the league post-dates the fillers" overclaims for
  round 1; it should not be cited as a post-filler round.
- **Original-pass counts are stale by design:** VERIFY.md's checks 1–3 quote 3 rounds and
  rounds_played 2; at head there are 7 rounds and rounds_played 5. The direction of drift only
  strengthens the checks; the re-run section covers 6/7/8 at the new release. No re-write needed.
- The harness gap the fixer NOTED (`viewer_smoke.mjs` accepts `ready` OR the attribute, so it
  cannot itself catch ordering inversions) is real but lives in the shared coworld-builder
  template, not this run's repo — correctly left out of scope here.

BLOCKING: 0
