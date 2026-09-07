# Run log — 2026-09-04-battlecode-2024

2026-09-04T17:01:41Z 00 claim comment posted on idea 1218173707729346 (story 1218192782817729)
2026-09-04T17:02:10Z 00 claim race check passed after 20s — only our claim comment present
2026-09-04T17:03:08Z 00 claim 2026-09-04-battlecode-2024 idea=1218173707729346 slug=battlecode-2024
2026-09-04T17:03:08Z 00 run task 1218192717760615 created in Running, heartbeat_at set, 9 phase subtasks created
2026-09-04T17:04:30Z 00 STATE.json written phase=10 session=a31cf3ca; mod run of Metta-AI/cogame-battlecode (year module bc24, Breadwars), per idea HOW — same recipe as 2026-09-04-battlecode-2020-soup and 2026-09-04-battlecode-2021
2026-09-04T17:08:00Z 10 designer dispatch prepared: starter=cogame-battlecode (mod run, year module bc24 Breadwars); brief modeled on 2026-09-04-battlecode-2021 with LEARNINGS 2026-09-03/09-04 battlecode entries carried forward
2026-09-04T17:12:30Z 10 designer dispatched thread=sthr_01G1eYiuShqRtK9BPHuhANgq output=runs/2026-09-04-battlecode-2024/design.md (bc24 year-module mod; bc21-sibling model; cert-stays-bc26, no-inert-chassis, parity-honesty, killfeed-fix pins in brief)
2026-09-04T17:52:00Z 10 designer returned round 1: design.md (1898 lines) — ACCEPTED against prompts/10-design.md checklist:
- [x] starter named with reason (cogame-battlecode itself; mod run, year-module boundary proved by bc20/bc21)
- [x] num_agents=2 single number, in variants[bc24].game_config and unchanged bc26 cert fixture; <SEATS>=2
- [x] resolution order: 8 numbered steps mirroring GameWorld.runRound (broadcast re-roll, round-1 endowment, fixed exec order, cooldowns, controller, end-of-turn traps in queue order, end-of-round ladder, hash chain)
- [x] scoring: points=int(60*share(caps)+25*share(levels)+15*share(crumbs)) f32-narrowed truncated, share=0.5 on 0-0; scores=100*wins+mean(points); higher better; league ranks results.scores
- [x] end conditions: end_reason capture|more_flag_captures|level_sum|more_bread|coin_flip|abandoned; results.reason complete|deadline|fault closed; deadline case scored-partial
- [x] per-seat observation = sealed one-shot doctrine brief JSON, visible/hidden enumerated; opponent sheet never sent
- [x] reply schema caps: 16KB bytes, sheet<=32 keys, notes 280 runes, motto 48 runes, all rune-boundary truncation
- [x] both policies same image env-switched: PLAYER_PROMPT champions vs PLAYER_SCRIPTED=awu|scaffold -> gone-sharkin/examplefuncsplayer24 per-year resolution
- [x] one parallel batch of 2 LLM calls, 45s doctrine budget, worst case 445s <= 720s (60% of 1200)
- [x] degrade-never-hang: failure table + verbatim fallback sheet + doctrine_fallback event
- [x] two name spaces: Clan Ash/Clan Basil in-game; real names only replay.names[]/results.names[]
- [x] viewer: static-replay-viewer bundle, build_replay_viewer.sh, all four files from cogame-battlecode itself, data-replay-loaded/-error, legible at 360px
- [x] chrome provenance: chrome_common.js + broadcast_core.js byte-for-byte, replay_broadcast.html = existing page + appended bc24 block, zoom decision: KEEP #viewpanel (boards to 59 tiles > 360px frame)
- [x] transport rules: --band/--hudscale/--statrail on :root, endcard stops at var(--band), seeks dismiss, buildBc24BeatButtons labelled buttons with CSS for all 12 kinds
- [x] replay self-sufficient: events+config+seed+names, wasm re-derives every frame
- [x] packaging: compose.yaml unchanged, manifest variant bc24 beside bc26/bc20/bc21, cert stays bc26 with len(certification.players)==num_agents cross-check, game.docs+both game.protocols, 0.3.0->0.4.0, GV06->GV07 ReplayCompatibleGameVersions extended
- [x] tests: 22 test files incl. legality+DecisionOps bound, e2e with SMOKE_REQUIRE_STATS substance assertion, strict UTF-8 parse, viewer_smoke executed by wasm-viewer job (settle=20000 soak=15 pinned), competence gate with -d:bc24BrokenChassis negative control, parity Tier A/A'/B/C with root-cause-or-fail, cert_probe
- [x] out of scope (v1) non-empty (11 items)
- [x] killfeed FIT-zoom fix verified already in tree; bc24 adds its readouts to measured set + runs gate on bc24 replay
2026-09-04T17:52:30Z 10 -> 20 phase transition: design accepted round 1, zero rejections
2026-09-04T17:52:30Z progress phase=10 marker=design.md
2026-09-04T17:38:00Z 20 builder dispatched thread=sthr_018Ags2YPPSefosws5xoBEm2 branch=bc24-year-module output=runs/2026-09-04-battlecode-2024/build-report.md (GV07 extend, player[] unchanged, cert bc26, Tier A/A'/B/C parity with root-cause-or-fail, killfeed gate kept armed, official sprites, competence gate w/ negative control pinned in brief)
2026-09-04T17:38:00Z heartbeat phase=20
2026-09-04T20:39:53Z 00 resume at phase 20 attempt=1 session=9f5cea40
2026-09-04T20:41:33Z 20 previous builder thread sthr_018Ags2YPPSefosws5xoBEm2 left no build-report.md, no bc24-year-module branch, no CI runs after 15:45 — leg did not happen; re-dispatching builder (attempt 1 of 3, fresh session 9f5cea40)
2026-09-04T20:42:21Z 20 builder dispatched thread=sthr_01AJcDZJ9TciJR4RRK687z18 branch=bc24-year-module output=runs/2026-09-04-battlecode-2024/build-report.md (mod run, no repo-create; GV07 extend, 0.3.0->0.4.0, cert stays bc26, num_agents=2, parity Tier A/A'/B/C root-cause-or-fail, killfeed gate kept armed, competence gate -d:bc24BrokenChassis, viewer settle=20000 soak=15, PR-then-merge pinned in brief)
2026-09-04T20:42:21Z heartbeat phase=20
2026-09-07T01:20:09Z 00 resume at phase 20 attempt=2 session=cb9a9f89
2026-09-07T01:22:04Z 20 previous builder thread sthr_01AJcDZJ9TciJR4RRK687z18 died mid-leg but left branch bc24-year-module CI-green (push run 33918358129, PR run 33918362485, sha fa5083a) and PR #4 open; no build-report.md — re-dispatching builder to verify completeness vs design, merge PR #4, drive ci.yml green on main, and write the report (attempt 2 of 3, session cb9a9f89)
2026-09-07T01:22:42Z 20 builder dispatched thread=sthr_01AP3dXAJ7DRMUnnXC5fjrwP output=runs/2026-09-04-battlecode-2024/build-report.md (resume of dead leg: audit bc24-year-module branch vs design, merge PR #4, ci.yml green on main, exit checks, report)
2026-09-07T01:22:42Z heartbeat phase=20
2026-09-07T04:38:16Z 00 attempts_reset phase=20 reason=progress marker=ci run 34073121395 (sha 0950ff99 green on bc24-year-module, new since previous session's 01:22 dispatch; progress line absent because that session died inside the builder thread)
2026-09-07T04:38:16Z 00 resume at phase 20 attempt=1 session=6fc1bf10
2026-09-07T04:39:31Z 20 builder re-dispatch prepared (resume of dead leg sthr_01AP3dXAJ7DRMUnnXC5fjrwP): branch bc24-year-module green at 0950ff99 (runs 34073121395/34073119162), PR #4 open+mergeable, no build-report.md — new builder to audit vs design, close gaps, merge PR #4, ci.yml green on main, exit checks, write report (builder round continues under attempt=1, session 6fc1bf10)
2026-09-07T04:40:19Z 20 builder dispatched thread=sthr_01XwDhWaHziXqchcZwWKNYtA output=runs/2026-09-04-battlecode-2024/build-report.md (audit bc24-year-module@0950ff99 vs design, close gaps, merge PR #4, ci.yml green on main, full exit checks, report)
2026-09-07T04:40:19Z heartbeat phase=20
2026-09-07T08:01:58Z 00 attempts_reset phase=20 reason=progress marker=ci run 34084170288 (main 5e7c8b78 green, PR #4 merged 04:43:34Z — new since previous session's 04:40 dispatch; progress line absent because that session died inside the builder thread)
2026-09-07T08:01:58Z 00 resume at phase 20 attempt=1 session=ab4442d8
2026-09-07T08:03:39Z 20 exit checks passed by coordinator on main@5e7c8b78 (ci run 34084170288 green; PR #4 merged 04:43:34Z by dead builder leg sthr_01XwDhWaHziXqchcZwWKNYtA which left no build-report.md — checks re-run mechanically: placeholders clean, hooks executable, 3 workflows parse w/ inputs+artifacts, manifest bc24 variant + num_agents=2 everywhere, GV07 compat extended, 20 bc24 tests, policies 2 LLM + 2 scripted w/ player field on champion 2)
2026-09-07T08:03:39Z 20 -> 30 phase transition: ci.yml green on main, review_round=1
2026-09-07T08:03:39Z heartbeat phase=30
2026-09-07T08:04:25Z 30 reviewer dispatch prepared: repo checkout /tmp/cogame-battlecode@5e7c8b78 (full history), base for the bc24 delta = d2922438 (main pre-PR#4), output=runs/2026-09-04-battlecode-2024/reviews/r1-review.md
2026-09-07T08:05:00Z 30 reviewer dispatched thread=sthr_012okBBR5gZouSrwcrLYWp8H round=1 output=runs/2026-09-04-battlecode-2024/reviews/r1-review.md
2026-09-07T08:05:00Z heartbeat phase=30
2026-09-07T11:19:07Z 00 resume at phase 30 attempt=1 session=db98fc3b
2026-09-07T11:20:06Z 30 reviewer re-dispatch prepared (dead session ab4442d8's reviewer sthr_012okBBR5gZouSrwcrLYWp8H left no r1-review.md): fresh checkout /tmp/cogame-battlecode@5e7c8b78, base d2922438, round=1
2026-09-07T11:20:38Z 30 reviewer dispatched thread=sthr_01LspzzSNWhNdeZzGVfqkUnj round=1 output=runs/2026-09-04-battlecode-2024/reviews/r1-review.md
2026-09-07T11:20:38Z heartbeat phase=30
2026-09-07T14:20:37Z 00 resume at phase 30 attempt=2 session=71600f96
2026-09-07T14:21:49Z 30 reviewer re-dispatch prepared (3rd in-round attempt; sessions ab4442d8/db98fc3b died in reviewer threads sthr_012okBBR5gZouSrwcrLYWp8H/sthr_01LspzzSNWhNdeZzGVfqkUnj, no r1-review.md): fresh checkout /tmp/cogame-battlecode@5e7c8b78, base d2922438, round=1 session=71600f96
2026-09-07T14:22:26Z 30 reviewer dispatched thread=sthr_01Mu9keKFpErgSJNvr7AdXe7 round=1 output=runs/2026-09-04-battlecode-2024/reviews/r1-review.md
2026-09-07T14:22:26Z heartbeat phase=30
