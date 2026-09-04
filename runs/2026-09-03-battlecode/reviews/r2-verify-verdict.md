blocking: 0

# r2 verify-verdict — battlecode (phase 60 adjudication, fresh context)

Adjudicated: 2026-09-04T05:00Z. Evidence: VERIFY.md at coworld-builder sha `5a408a2`
("battlecode: phase 60 evidence committed (VERIFY.md all 8 TRUE)"), the committed
`viewer-check/` artifacts (json + png, primary + three attempt dirs), STATE.json,
`release-result-0.1.6.json`, `release-result.json`, `reviews/r2-review.md`. I re-fetched,
read-only, everything cheap to re-fetch: the leaderboard, the round-10 ereq, both replays'
bytes from S3 (HEAD 200 + full strict parse), the round-10 hosted log (elevated), the coworld
detail row, the public page's SSR payload, the live viewer bundle HTML, the four `viewer-check`
run conclusions via `gh`, and `sim_types.nim` at the repo head. Every re-fetch reconciled with
what VERIFY.md pasted. Independent read of the committed artifacts and screenshots was done
before comparing against VERIFY.md's prose.

## Per-check adjudication (fetched? sufficient? honest?)

**Check 1 — ≥2 completed rounds after fillers: TRUE, upheld.** The rounds list is pasted with
ids, numbers, statuses, timestamps, and the fetch times of both polls (04:26Z, 04:43Z). The
filler-policies read is pasted (both fillers, neither a champion), and log.md line 68 records
filler registration at 02:32:30Z — rounds 9 (04:24:54Z) and 10 (04:39:55Z) are hours later.
The self-imposed scope rule (count only rounds ≥ 9, the 0.1.6 rounds) is *stricter* than the
SPEC item and correctly answers the operator's "after the fix" instruction in r2-review.md.
That rounds 9–10 ran 0.1.6 is proven two independent ways: both ereqs carry
`coworld_id: cow_cfddca58…` (the 0.1.6 cow id per STATE and the /coworlds row) and both
replays carry `result.game_version: "GV04"` (re-verified by me from S3 bytes).

**Check 2 — both champions ranked, fillers absent: TRUE, upheld.** I re-fetched the
leaderboard live and got byte-identical rows: daveey 1068.5632706307158 / daveey-1
931.4367293692842, both `rounds_played 10`. Reconciliation: 10 completed rounds × 1 episode
each = episode_wins 8.0 + 2.0 = 10 ✓; `rounds_played 10` matches the 10 round ids in check 1 ✓.
No filler rows — "absent", the easier arm of "absent or Baseline". Honest detail: the file
notes the earlier 04:26Z fetch showed 9 and that the pasted row is the post-round-10 one.

**Check 3 — latest round's ereq completed with replay: TRUE, upheld.** I re-fetched
`ereq_adfbaca2…` live: `status completed`, same `replay_url` (75fbab97…), participants
daveey/daveey-1 with `is_filler: false`, same participant_scores (249.33/149.67). The 405 on
the flat route and the nested-route substitution are declared. Round 9's ereq is pasted too.
Scores reconcile with both replays' `result.scores` exactly.

**Check 4 — replay valid, GV04, operator substance test: TRUE, upheld.** This is the check the
whole re-verify exists for (r2-review.md D1/D2 + "After the fix"), and it holds at every point
I could independently test:
- *Bytes and parse*: S3 HEAD 200; both replays parse under Python's strict UTF-8 JSON parser
  in my own re-fetch; `protocol cogame.battlecode.v1`; `reason complete`; `fallbacks [0,0]`.
- *GV04 / fixed image*: `result.game_version == "GV04"` in both replays (my parse), and
  `sim_types.nim` line 16 at head reads `GameVersion* = "GV04"` with the GV04 changelog entry
  removing `chassis` from the knob surface.
- *Both clans built rats, ferried cheese*: my parse of both replays confirms every number in
  VERIFY's clause table verbatim — rats_built and cheese_transferred > 0 for both clans in all
  six games (r10: 24/40, 29/27, 47/36 rats; r9: 17/40, 41/31, 29/27).
- *Cat damage*: both clans > 0 in ≥1 game each (r10: all six entries > 0; r9: Basil's one zero
  is on mercifullattice only, where it built 31 rats, ferried 6060 cheese and opened the
  backstab — a tempo choice, not idling; both its other games show 3730 and 2550 damage).
- *No idle-win pattern*: the only `kings_destroyed` finishes are r10 g1 (loser Ash: 1980 cat
  damage, 24 rats) and r10 g3 (loser Basil: 4560 cat damage, 36 rats) — both losers fully
  active, and both games follow a *recorded* `backstab` event at round 800 by Clan Basil
  (`trigger: "bite"`), which I confirmed in the event stream of my own replay fetch. This is
  the operator's "ends on points or a real backstab", satisfied. The 0.1.5 round-1 pattern
  (scaffold sheet, 0 rats/0 cheese/0 damage, win by opponent starvation) appears nowhere.
- *Chassis settled*: my own parse of all four champion seats across both replays:
  `'chassis' in sheet_submitted == False`, `sheet_unknown_fields == []`, `policy: llm`,
  `fallback: None`. The effective sheet's `"chassis": "awu"` is the engine-assigned constant,
  exactly as VERIFY explains. The LLM did not choose a chassis and (per GV04) could not have.
- *Non-scripted, non-trivial*: distinct sheets (four knobs differ), distinct prose notes and
  mottos, one 5.7s LLM round-trip per seat against a 20s deadline, zero fallback events.

**Check 5 — hosted log clean: TRUE, upheld.** I re-fetched the round-10 log with the elevated
header (200, 1760 B, matching VERIFY's byte count) and grepped the four patterns against the
*raw bytes* myself: zero matches. `refused a seat-0 connection` is `refused`, not `rejected` —
the pattern does not match it, and the log then shows both seats registering `kind=llm` and
`reason=complete`. Round 9's log is pasted in full in VERIFY with the same shape. The whole
decoded logs are pasted, not summarised — the strongest form of this evidence.

**Check 6 — static replay path + featured match: TRUE, upheld.** The raw-HTML grep, its empty
result, and the fallback route are all recorded as the prompt requires, and the source used is
named (SSR playlist + `POST /coworlds/replays/session`). My re-fetch of the page's SSR payload
shows the playlist's top item is now `battlecode.r11.e1` (round 11 finished 04:55:45Z, after
VERIFY was written) — same coworld id, same 0.1.6, i.e. the featured slot is live and rolling,
which *confirms* rather than contradicts VERIFY's round-10 snapshot at 04:44Z. The viewer URL
is the static route `…/v2/coworlds/replays/static/<cow_id>/<manifest_sha>/index.html` — I
fetched that exact bundle HTML myself (200, 159060 B). No `/client/replay` anywhere. The
`<sha>` equals the coworld's `manifest_hash`, which I re-confirmed from `/coworlds/$COW`
(canonical: true, version 0.1.6). Note: the live route carries the replay as `?v=2#replay=…`
rather than the SPEC's literal `?replay=`; the substance of the item — static bundle route,
never a pod — is met, and the session endpoint is the platform's own source of truth. Recorded
below as advisory, not blocking.

**Check 7 — certification declared the static bundle: TRUE, upheld.** I read both committed
artifacts myself: `release-result-0.1.6.json` contains the exact required string
`Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not
required)` plus `ok: true, version: 0.1.6, canonical: true, secret_put: true`, and the source
is named (committed artifact of run 33836155531; `/tmp` never consulted). The `policies: []`
exception is honestly declared, is corroborated by log.md (03:45Z builder trace: `-f
policies='[]'` skips upload-policies so the league keeps its v1 seats), and the 0.1.5 artifact
(`release-result.json`) carries the four `:v1` policy uploads — the two files together are a
complete, reconcilable release record. This matches the operator's own "re-upload champions
ONLY if their prompt text changes" instruction: it did not change, so no v2s were minted.

**Check 8 — viewer executed and judged: TRUE, upheld, including the caveat. Explicit ruling
below.** The evidence is real and committed: four green `viewer-check.yml` runs (I confirmed
all four conclusions `success` via `gh run view`), artifacts committed under `viewer-check/`,
and the committed jsons are byte-consistent with every number VERIFY quotes.
- *(a) loaded*: `loaded: true` in all four runs, from **both** accepted signals —
  `data_replay_loaded: "true"` and bridge `["ready"]` — with `failure: null` and first frame
  at 1728 ms (primary). This is the artifact's own content, not an asset-200 inference. TRUE.
- *(b) advancing*: the primary run's committed `viewer-smoke.json` records three differing
  scrub readouts — `2:20` / `2:19` / `2:18` — which satisfies the SPEC's letter as written.
  The verifier then *voluntarily disclosed* that the readouts are not seek positions: the
  harness's `SCRUB_SELECTOR = '#scrub, #seek, input[type="range"]'` resolves `.first()` in DOM
  order, and I verified in the live bundle HTML that `#zoom-slider` (an `input[type=range]`,
  line 2706) precedes `#scrub` (line 2758) — so the 50%/100% clicks hit the zoom slider. The
  three corroborations all check out under my own reading: the screenshots of the clicked runs
  show `12.0×` (slider max) in the zoom bar; every readout stays `GAME 1 OF 3` (impossible for
  a true 100% seek on a 3-game replay); and attempt3 (`viewpanel=0`) stopped after one sample,
  which is exactly what `if (!box) break` does when the range input is hidden — proving the
  loop never reaches `#scrub`.
  **Ruling: the caveat does not undermine the verdict — it strengthens it.** The item exists
  to reject "a frame that renders once and freezes". A clock that counts down in real time
  during playback (2:20→2:19→2:18 across ~1.4 s of wall clock), a scorebug that moves 15–15 →
  22–27 between load and screenshot, and a round counter that reads 8, 38, 39 and 40 across
  the four screenshots is *continuous* motion — direct evidence of advancing frames, which a
  single scripted seek could technically fake and this cannot. The prompt itself anticipates
  instrument mismatch ("an absent scrubber… judge motion from the screenshot plus the replay
  JSON instead"); this is the analogous case, handled the analogous way, and disclosed with
  proof rather than papered over. The mis-targeting is a defect in coworld-builder's shared
  `viewer_smoke.mjs`, not in this coworld, whose own click-to-seek `#scrub` handler I saw
  wired in the served bundle (line 3151).
- *(c) judgment paragraph*: present, and I checked it against the pictures myself. The FIT
  screenshot (attempt3) shows exactly what the paragraph claims: the full 30×30 cheesefarm
  board, two rat kings (magenta top-left, amber bottom-left) with rat clusters, two purple
  cats on the right, yellow cheese piles, dirt/cheese blocks, green COOPERATION chip, scorebug
  with both players and mottos, econ panel (kings/cheese/cats/traps/dirt per clan), killfeed
  line "Game 1 begins on cheesefarm", transport strip + beat-marked scrubber + speed chips —
  the starter's chrome family. The r2-D3 fix is visible in the wild: the doctrine overlay that
  the operator's review said covered the board is collapsed to a `▶ DOCTRINES` button in all
  four screenshots. The reconciliation against the replay events (pre-backstab rounds, coop
  still green, cheese 20/35 en route to 2580/4100) is correct per my own event-stream parse
  (16 events in r9, 14 in r10 — nothing elided, backstabs at g1@800 / g0@800+g2@800 exactly
  as pasted).

## The operator's r2 ruling — answered?

Yes. D1: chassis off the LLM surface, proven at the source (`sim_types.nim` GV04), at the
wire (`sheet_submitted` has no chassis key, all four seats), and at the ledger
(`sheet_unknown_fields []`). D2: no kings lost to cats in any counted game — the only
`kings_destroyed` ends are post-backstab clan kills with both sides active; the scaffold
filler never appeared in a counted episode (champions-only matchups). D3: overlay dismissed in
every screenshot. The "After the fix" process line was followed: new coworld version (0.1.6
canonical), champions kept at v1 (prompt text unchanged), fillers unchanged and distinct, two
fresh rounds verified on the new image.

## Blocking items

None.

## Advisory observations (non-blocking)

- [harness] `viewer_smoke.mjs`'s `SCRUB_SELECTOR` picks the first `input[type=range]` in DOM
  order; on shells with a zoom slider before the scrubber the "scrub readouts" are playback
  samples, not seeks. Prefer `#scrub`/`#seek` explicitly, or exclude `#zoom-slider`. (Verifier
  already flagged this; I verified the mechanism in the live bundle and the mjs source.)
- [check 6, spec text] The live static route encodes the replay as `?v=2#replay=…` while SPEC
  item 6 writes `?replay=…` literally. The platform's session endpoint is the source of truth
  and the substance (static bundle, never a pod) is met; SPEC's literal string could be
  updated to match the platform.
- [coworld, phase 30 residue — all already recorded in VERIFY]: (i) `docs/PROTOCOL.md`'s
  example body still says GV03; (ii) round-10 seat 0's `backstab_round` default was filled
  without appearing in `sheet_defaults_applied`; (iii) zoom slider at 12× renders the board
  unreadable with no snap-back to FIT — a real spectator can wedge themselves there with one
  click; (iv) log.md line 89 notes `check_gameversion.sh` GV0x parse unwired and an endcard
  regex escaping nit, left unfixed by the r2 fixer.
- [evidence hygiene, minor] VERIFY check 5 pastes a grep against the *decoded* log
  (`logs10.txt`) whose decode step is described but not pasted; immaterial here because I
  re-grepped the raw bytes myself with zero matches, and the full decoded logs are pasted
  inline anyway.

## Summary

Every one of the eight checks is (a) actually fetched — commands and outputs pasted, with
fetch timestamps and the two declared exceptions (committed release artifact; CI-produced
rendered evidence) both being committed files I could and did read; (b) sufficient — the
pasted output proves the claim in each case, and the two caveats (zoom-slider mis-click,
`policies: []`) are disclosed with proof rather than hidden; (c) honest — every number I
re-fetched or re-derived reconciled exactly (leaderboard rows to 16 significant digits, replay
scores vs participant_scores, rounds_played vs round count, GV04 vs the 0.1.6 release, the
featured replay vs check 3's ereq, committed jsons vs quoted readouts). VERIFY.md's all-true
verdict stands.

BLOCKING: 0
