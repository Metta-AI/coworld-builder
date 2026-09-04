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
