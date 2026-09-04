# Run log — 2026-09-04-battlecode-2021

2026-09-04T09:15:58Z 00 claim comment posted on idea 1218173707173046 (story 1218176597665462)
2026-09-04T09:16:30Z 00 claim race check passed after 20s — only our claim comment present
2026-09-04T09:17:00Z 00 claim 2026-09-04-battlecode-2021 idea=1218173707173046 slug=battlecode-2021
2026-09-04T09:17:10Z 00 run task 1218176598028188 created in Running, heartbeat_at set, 9 phase subtasks created
2026-09-04T09:17:30Z 00 STATE.json written phase=10 session=1b63e692; mod run of Metta-AI/cogame-battlecode (year module bc21), per idea HOW and LEARNINGS 2026-09-04 battlecode-2020-soup recipe
2026-09-04T09:22:00Z 10 designer dispatch prepared: starter=cogame-battlecode (mod run, year module bc21); brief modeled on 2026-09-04-battlecode-2020-soup with its LEARNINGS carried forward
2026-09-04T09:19:47Z 10 designer dispatched thread=sthr_01M8sPmhZSeDaf2EZnSp2zT4 output=runs/2026-09-04-battlecode-2021/design.md (bc21 year-module mod; bc20-sibling model; parity root-cause + killfeed-fix + cert-fixture pins in brief)
2026-09-04T09:49:33Z 10 designer returned round 1: design.md (1724 lines) — ACCEPTED against prompts/10-design.md checklist:
- [x] starter named with reason (cogame-battlecode itself; mod run, year-module boundary proved by bc20)
- [x] num_agents=2 stated in bc21 variant game_config and cert fixture (cert stays bc26); <SEATS>=2
- [x] resolution order numbered 1-7 mirroring GameWorld.runRound (turn order, empower scan order, bid auction (bid+1)/2, buff expiry, camouflage@300, double-wipe->B)
- [x] scoring: points=int(40*survival+35*vote_share+15*center_share+10*influence_share) f32-truncated; scores=100*wins+mean(points); higher better; league ranks results.scores
- [x] end conditions: 6 end_reason values incl deadline/abandoned; results.reason closed enum complete/deadline/fault
- [x] per-seat observation = sealed pre-match doctrine brief, recorded verbatim in replay; no per-round obs
- [x] reply schema caps: 16KB reply, notes 280 runes, motto 48 runes, all rune-boundary truncation
- [x] both policies same image env-switched: PLAYER_PROMPT champions (slanderer-turtle vs muck-rush) + PLAYER_SCRIPTED awu->california-roll, scaffold->examplefuncsplayer21
- [x] one parallel batch of 2 LLM calls, 45s doctrine budget, worst case 445s <= 720s (60% of 1200)
- [x] degrade-never-hang: retry once -> california-roll fallback sheet; doctrine_fallback event; loud logging
- [x] two name spaces: Clan Ash/Clan Basil in-game, real names spectator-side only
- [x] viewer: static-replay-viewer bundle, build hook, chrome verbatim, readouts listed, 360px legible
- [x] all four viewer files from ONE starter (cogame-battlecode); data-replay-loaded/data-replay-error stated
- [x] chrome provenance: chrome_common.js byte-for-byte, replay_broadcast.html appended game block, viewpanel KEPT (board 768-1024px > 360px frame) with reason
- [x] transport rules: --band/--topband/--hudscale (+new --statrail) via relayout(), nothing in band, endcard stops at var(--band) + dismissed on seek, beat buttons with CSS for every kind
- [x] replay self-sufficient: names, config, sheets, events, seed; wasm re-derives frames
- [x] packaging: compose.yaml unchanged, manifest template (bc21 variant added, player[] UNCHANGED, cert bc26), game.docs readme+pages(+rules-bc21), protocols player+global
- [x] tests: 19 test files incl bounded-orders (11), survival gate w/ inverted control (12), knob-teeth (13), perf gate 75s (15), strict-UTF8 replay (17), parity-oracle-bc21 (Tier C BLOCKING vs parity_ledger_bc21.json), 3-episode docker-smoke, wasm-viewer executes bundle on all 3 replays
- [x] out of scope non-empty (14 items)
Extras: GV05->GV06 extending ReplayCompatibleGameVersions, 0.2.0->0.3.0, killfeed FIT-zoom fix in scope w/ smoke overlap gate, 1500-round cap pinned vs stale 3000 spec prose (patch 2021.2.3.0), 18/76 maps with exclusion reasons
2026-09-04T09:49:33Z 10 phase -> 20
2026-09-04T09:49:33Z progress phase=10 marker=design.md
2026-09-04T09:51:21Z 20 builder dispatched thread=sthr_01QAZzoBKFkNkF5TzKv8pooc branch=bc21-year-module output=runs/2026-09-04-battlecode-2021/build-report.md (PR open not merged; GV06 extend, player[] unchanged, cert bc26, Tier-C parity ledger blocking, killfeed --statrail fix, 3-episode smoke pinned in brief)
2026-09-04T09:51:21Z heartbeat phase=20
2026-09-04T12:53:49Z 00 resume at phase 20 attempt=1 session=fe001725
2026-09-04T12:55:16Z 20 previous session's builder thread still live: 6 bc21 commits pushed 12:45-12:46Z, CI run 33874457351 in_progress on bc21-year-module — monitoring instead of re-dispatching (two builders on one branch would race)
2026-09-04T13:09:12Z heartbeat phase=20
2026-09-04T13:12:05Z 20 CI run 33874457351 branch=bc21-year-module conclusion=failure: parity-oracle-bc21 (javac invalid flag --release under JDK8) + test (test_bc20_baselines.nim type mismatch ScriptedChassis vs ChassisKind); waiting bounded window for the live builder thread to fix before taking over
2026-09-04T13:21:23Z heartbeat phase=20
2026-09-04T13:21:23Z 20 builder round 2 observed: fix commit cb4d6fbb pushed 13:13Z, PR #3 open, CI runs 33876856381/33876968476 in_progress
