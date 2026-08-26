# 2026-08-25-hidden-agenda — log

2026-08-25T23:23:10Z 00 claim 2026-08-25-hidden-agenda idea=1217748423031678 slug=hidden-agenda
2026-08-25T23:23:30Z 00 claim comment uncontested after 20s; run task created gid=1217846726828160 + 9 phase subtasks
2026-08-25T23:25:30Z 00 STATE written phase=10 session=7ba01598
2026-08-25T23:26:02Z 10 starter=coworld-ctf (real-time grid loop with new rules -> ctf row; idea is an EXTENSION of live coworld-among-them, but that repo carries the old multi-role manifest schema, no static wasm viewer, none of the builder CI conventions -> unusable as scaffold; it is the rules reference, cloned read-only at /tmp/among-them; paintball 2026-08-25 precedent: EXTENSION ideas ship as new cogame-<slug> on the pinned starter); repo=Metta-AI/cogame-hidden-agenda per SPEC pin
2026-08-25T23:26:49Z 10 designer dispatched round=1 thread=sthr_01C2jxGHKzdcTHd1GK6yj3aS output=runs/2026-08-25-hidden-agenda/design-r1.md
2026-08-25T23:49:32Z 10 designer returned round=1 file=design-r1.md (1482 lines)
2026-08-25T23:49:32Z 10 checklist: [x] starter=coworld-ctf+reason (llm layer+player forked from cogame-bullwhip, viewer files all coworld-ctf) [x] num_agents=5 single number in all 3 variants+cert fixture+<SEATS>=5 [x] tick structure: 12 numbered play steps + M1-M6 meeting machine [x] scoring zero-sum +1x4/-4 crew win, -1x4/+4 impostor win, ties 0; higher better; league ranks results.scores [x] end conditions complete/deadline/forfeit + ending enum incl timeout-as-complete 0-0 [x] per-seat observation visible/hidden (facing cone r8 + awareness r2, LOS-gated; roles hidden in-game, spectator-side only) [x] reply schema per-field rune caps (say 90, hunch 80, notes 240, prompt echo 4000, err 200) [x] both policies PLAYER_PROMPT sleuth/shadow + PLAYER_SCRIPTED miner/lurker same image env-switched, role-aware algorithms given [x] one parallel batch per decision point, worst 685s < 720s = 60% of 1200s [x] degrade-never-hang retry-once->miner fallback, endEarly deadline, maxDecisionBatches=20 [x] two name spaces RED..PINK in-game, policy names spectator-side [x] viewer static wasm bundle + build hook + chrome verbatim + readouts + 360px [x] viewer starter=coworld-ctf for ALL four files, data-replay-loaded/-error stated [x] chrome provenance byte-for-byte chrome_common.js + appended game block + removal list (#viewpanel #fpv #povBadge #mmwarn) + zoom dropped (fixed 1080x760 arena) [x] transport rules --band/--hudscale/:root/relayout, endcard var(--band)+seek dismiss, beats clickable buttons CSS all 6 kinds [x] replay self-sufficient (hidden_agenda.replay.v1: seed, roles, map ASCII, constants, per-tick frames+vis masks, events, results) [x] packaging compose/manifest/docs readme+2 pages/protocols player+global both text objects [x] tests 13 incl bounded-orders on both baselines, e2e+strict-UTF-8, viewer smoke EXECUTED via viewer_smoke.mjs vs docker-smoke replay + renderer fixture [x] out-of-scope 13 items
2026-08-25T23:49:32Z 10 design accepted round=1 -> phase 20
2026-08-25T23:49:32Z progress phase=10 marker=design-r1.md
2026-08-25T23:49:32Z heartbeat phase=20
2026-08-25T23:50:17Z 20 repo created https://github.com/Metta-AI/cogame-hidden-agenda (public); propagate-secrets run 32912493482 completed; gh secret list shows SOFTMAX_TOKEN + ANTHROPIC_API_KEY
2026-08-25T23:51:13Z 20 builder dispatched round=1 thread=sthr_01PTMkReBrxWb5NwmN1czavb target=ci.yml green on main of Metta-AI/cogame-hidden-agenda

## Phase 20 — build

- 2026-08-26 01:31Z `ci.yml` run `32919193615` on `main` @ `5fb43682` — **success**
  (test / docker-smoke / wasm-viewer all green on the first dispatch). Every
  `tests/*.nim` ran twice (debug + `-d:release`); docker-smoke played a real
  five-seat episode from the certification fixture (`all 5 player containers
  exited 0`, `reason=complete`, 55 447-byte replay); wasm-viewer built the
  static bundle, loaded it in headless chromium with `--soak 10
  --strict-text-bounds`, and then loaded `tools/ci/renderer_fixture.html`.
- The tree is published through `tools/publish.py` (blobs → tree → commit →
  ref) because the sandbox's git credential helper can READ
  `Metta-AI/cogame-hidden-agenda` but `git push` returns
  "No anonymous write access"; `gh`'s token has `permissions.push: true`, so
  the Git Data API is the working path. Not a defect in the repo.
- Board art: nano-banana (`gemini-2.5-flash-image`) renders of the Softmax cog,
  FIVE sheets (front / walk / mine / carry / frozen) x five body colours, in
  `scripts/art/source/`, split by `scripts/art/split_cog_sheet.py`. No
  procedural-rig fallback was needed.
2026-08-26T01:38:23Z 30 r1 reviewer dispatched thread=sthr_0159BcTLHovT2diAghJrBpAn output=reviews/r1-review.md repo@5fb43682
2026-08-26T02:00:08Z 30 r1 reviewer returned: 35 findings (3 blocking: B1 /client/replay route, B2 page-generator inherits CSS-only, B3 no per-tick re-derivation test; 32 non-blocking) file=reviews/r1-review.md
2026-08-26T02:00:08Z progress phase=30 marker=r1-review.md
2026-08-26T02:00:08Z heartbeat phase=30
2026-08-26T02:00:48Z 30 r1 fixer dispatched thread=sthr_01XxeV3sPF2cGQsUPoskJELi output=reviews/r1-fixes.md (one commit per finding via tools/publish.py, CI green required)
