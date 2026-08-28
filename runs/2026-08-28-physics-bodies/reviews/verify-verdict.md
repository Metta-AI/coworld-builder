blocking: 0

# verify verdict — physics-bodies (phase 60)

Adjudicated: 2026-08-28T16:05Z · judge with fresh context
Authority: `docs/SPEC.md` §Definition of done · commands: `prompts/60-verify.md`
Evidence file: `runs/2026-08-28-physics-bodies/VERIFY.md` (736 lines)
Independent read of SPEC, the prompt, VERIFY.md's pasted evidence, the committed artifacts
(`viewer-check/viewer-smoke.json`, `viewer-check/viewer-smoke.png`, `release-result.json`) and
`design.md` §End conditions was formed before consulting anyone's summary. I re-fetched live
evidence for checks 1, 2, 3, 4, 5, 6 and 8 myself (well past the two-check minimum); check 7 was
verified from the committed artifact plus `git log`.

## Blocking findings

None.

## Checklist pass (independent, item by item)

| # | SPEC item | verdict | what I verified |
|---|---|---|---|
| 1 | ≥2 completed rounds after fillers | TRUE | **Re-fetched live**: `GET /rounds?league_id=league_6fe36e5b…` → rounds 2 (created 15:31:57Z) and 3 (created 15:46:58Z) `completed`, round 1 `failed` ("Temporal RoundWorkflow failed before settling the round."), round 4 now `pending` (post-VERIFY ladder cadence, immaterial). Ordering "after fillers" independently established — see the citation note below; the substance holds. |
| 2 | Both champions ranked, fillers absent/Baseline | TRUE | **Re-fetched live**: `GET /divisions/div_03ffc06b…/leaderboard` → exactly two rows, `daveey` rank 1 (`physics-bodies-ringcraft:v3`, rounds_played 2) and `daveey-1` rank 2 (`physics-bodies-toppler:v3`, rounds_played 2); no filler row, no `Baseline` label. Byte-identical to VERIFY.md's paste. |
| 3 | Latest round's ereq completed with replay, participants named | TRUE | **Re-fetched live**: `GET /episode-requests/ereq_05afb4b3…` → `completed`, `replay_url …/fa7ce35f-….replay`, participants `daveey` (ringcraft v3) + `daveey-1` (toppler v3), both `is_filler:false`, scores +2.25/−2.25. Matches VERIFY.md. |
| 4 | Replay bytes valid, protocol matches, reason acceptable, non-fallback LLM decisions | TRUE | **Re-fetched and re-decoded myself**: S3 bytes 88,731 B magic `COWLDPBD`; ran `tools/replay_summary.py` (repo at `3b913af`) → output strict-UTF-8-parses; `protocol physics-bodies/v1` matches `coworld_manifest_template.json`; `reason complete` / `endRule full_time` (the design's `deadline/wall_clock` exception was available but not needed — confirmed `stops:[]`); `llmTurns [50,50]`, `fallbackTurns [0,0]`, `policyKinds ["llm","llm"]`. The pasted intent excerpts show substantive game-specific reasoning (rim distance, tilt, shove) — not fallbacks, not boilerplate. The documented substitution (binary container → summariser → strict parse) is legitimate: `jq` cannot apply to a non-JSON container, and the verifier recorded rather than hid the deviation. |
| 5 | Hosted game log clean | TRUE | **Re-fetched live** with elevated header: 207,683 B, `grep -cE 'falling back\|LLM provider is unavailable\|cut off at max_tokens\|rejected'` → 0 hits. VERIFY.md additionally decoded the python byte-string reprs and grepped the decoded text (447 lines, 4 containers) — stronger than the prompt requires. No throttle exception invoked or needed. |
| 6 | Public page uses the static replay path; featured match present | TRUE | **Re-fetched live**: `POST /coworlds/replays/session` → `ready:true`, `viewer_url` = `…/v2/coworlds/replays/static/cow_e51c593d-…/sha256%3A3c7e9da8…/index.html?v=2#replay=…` — identical to VERIFY.md's paste; the sha equals `STATE.coworld.manifest_sha`; no `/client/replay` anywhere. The `#replay=` fragment vs the SPEC's `?replay=` wording is the documented post-2026-08-28 form (`playbooks/observatory-api.md` §Featured match: "both are the static route"). Featured match `physics-bodies.r3.e1` shown in the SSR `playlist[0]` paste with a two-sided matchup; the raw-iframe grep coming up empty is the documented client-rendered behaviour, and VERIFY.md recorded which source it used, as the prompt requires. |
| 7 | Certification declared the static bundle | TRUE | Read the **committed** `runs/…/release-result.json` myself: `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)` — contains the required prefix verbatim; `certify.ok:true`, `canonical:true`; committed in `18d29a9` (phase 40), so the source is the committed artifact, not `/tmp`. |
| 8 | Viewer executed; loaded, advances, judged | TRUE | (a) `loaded:true` via `data_replay_loaded:"true"`, `data_replay_error:null`, `failure:null` in the committed `viewer-smoke.json`; CI run 33187402013 **re-checked via `gh`**: `conclusion: success`, created 15:54:21Z (2 s after the logged dispatch — correctly identified, not "latest blind"). (b) The three scrub clocks differ and progress coherently: `:05 … ROUND 1 OF 5 · RING 3.00 M` → `0:04 … ROUND 3 OF 5 · RING 2.39 M` → `0:00 … ROUND 5 OF 5 · RING 2.01 M`. (c) I opened `viewer-smoke.png` myself: it shows exactly what the judgment paragraph claims — scorebug (DAVEEY 2 rounds / +2.250 / 1 ring-out vs DAVEEY-1 0 / −2.250), clock `0:00 ROUND 5 OF 5 · RING 2.01 M`, both say banners verbatim from turn-57 intents, the torch-lit arena with shrunken dotted rim, amber/teal bug clusters, legend, four feed chips (`DRAWN ROUND 4/5`), transport strip with `BUG2 WINS 1921 / 1925` endcard and `1×…16×` speed row, scrubber with `LIVES LEAD` momentum graph. Every scorebug number reconciles against the replay's own `results`. Starter chrome lineage marks (scorebug/transport/scrubber+momentum/endcard) are visibly present — not the gridlock rewrite failure mode. |

## Evidence-quality audit (asserted vs pasted)

Every TRUE in VERIFY.md is backed by pasted command + output, not assertion. Both permitted
exceptions to fetch-fresh (item 7 committed artifact, item 8 CI artifact) are the exceptions the
prompt itself prescribes. My independent re-fetches of checks 1–6 and the `gh` re-check of the
check-8 run reproduced the pasted evidence byte-for-byte (modulo the new pending round 4). The
`design.md` §End conditions `deadline/wall_clock` allowance was correctly identified as
available-but-unused (`complete/full_time`, `stops:[]`).

## Non-blocking observations

1. **Check 1 citation error (accuracy, not substance).** VERIFY.md says the fillers were
   "registered 2026-08-28T15:30:06Z (log.md: `50 filler-policies 200: …`)". That timestamp is
   wrong: in `log.md` the 15:30:06Z line is the seed/division/settings line (line 51); the
   filler-policies line (line 53) carries **15:33:04Z** — a batched end-of-phase write shared by
   lines 52–57, i.e. a write time, not the API-call time. Taken naively the corrected timestamp
   would postdate round 2's creation (15:31:57Z), so I verified the ordering independently before
   letting check 1 stand: (a) champion-2's submit run (33185491619, re-checked via `gh`) finished
   at **15:31:18Z**, and the filler call follows both champion submits in the phase-50 sequence;
   (b) round 2 was created by the explicit `trigger-round` that follows the filler call in that
   sequence; (c) decisively, `playbooks/observatory-api.md` §6 documents that a trigger issued
   before any filler exists **fails instantly** with exactly round 1's error — round 2 completed,
   which it could not have done pre-filler. So fillers landed in the 15:31:18–15:31:57 window,
   before round 2, and check 1's TRUE stands. The misattributed timestamp should not recur:
   verifiers should quote log lines with their actual timestamps and note when a timestamp is a
   batched write time.
2. **The verifier's three legibility observations** — assessed on their merits:
   - *Stale `ROUND 1/5 - RING 3.00 M` intro card* overlaying a frame whose clock reads
     `ROUND 5 OF 5 · RING 2.01 M`: confirmed in the screenshot. Two contradictory readouts in one
     frame is a real (if small) spectator-legibility defect, plausibly a title card that a scrub
     jump fails to dismiss. Worth a repo issue / next-version fix; not a DoD item (the viewer
     loads, advances, and is legible overall).
   - *`feed_lines: 0` while the screenshot shows four feed chips*: an instrumentation gap in
     `viewer_smoke.mjs`'s feed selector for this shell. It degrades future automated evidence
     (a genuinely missing feed would be indistinguishable from a selector miss), so a selector fix
     in coworld-builder's smoke tool is worthwhile. No bearing on this run — the screenshot proves
     the feed.
   - *Endcard `1921 / 1925` vs `tickCount: 2062`*: most plausibly a unit mismatch (transport
     frames vs sim ticks); cosmetic at worst. Worth a one-line note in the repo; nothing to
     re-verify here.
   None of the three, singly or together, warrants reopening any check or a phase-30 send-back;
   items 1 and 2 merit follow-up issues (repo and coworld-builder respectively).
3. VERIFY.md's check-3 flat-route 405 and check-6 fragment-form deviations from the prompt's
   literal commands are both pre-documented in `playbooks/observatory-api.md` (§9, §Featured
   match) and were recorded, not improvised — handled correctly.

## Verdict

All eight definition-of-done items are TRUE at the current state of the world, verified from
fetched evidence, with seven of eight independently reproduced by this judge. Phase 60 passes.

BLOCKING: 0
