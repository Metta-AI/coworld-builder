2026-09-08T06:21:27Z 00 claim 2026-09-08-battlecode-2023 idea=1218173707682926 slug=battlecode-2023 session=ae0814d0
2026-09-08T06:21:27Z 00 run task 1218254757143976 created in Running, 9 phase subtasks, claim comment story 1218254757091625 on idea
2026-09-08T06:21:27Z 00 -> 10 phase transition: STATE written phase=10
2026-09-08T06:21:27Z heartbeat phase=10
2026-09-08T06:23:36Z 10 starter=cogame-battlecode (rail decision: mod run — the idea pins 'mod of the existing Metta-AI/cogame-battlecode repo, NOT a new repo'; year-module boundary proved by bc20/bc21/bc24/bc25); idea text recorded verbatim at runs/2026-09-08-battlecode-2023/idea.md
2026-09-08T06:23:36Z 10 designer dispatch prepared: year module bc23 'Tempest'; main@6885a066 has bc26/bc20/bc21/bc24/bc25 at GV08, coworld version 0.5.0; pins: GV08->GV09, 0.5.0->0.6.0, cert stays bc26, player[] unchanged, num_agents=2, branch-only bc23-year-module (sibling bc24 run Blocked, its module already on main); LEARNINGS 2026-09-03..09-07 battlecode entries carried forward
2026-09-08T06:24:40Z 10 designer dispatched thread=sthr_019uSTQSPL1vebFHTVxrkkSR round=1 output=runs/2026-09-08-battlecode-2023/design.md (bc23 year-module mod; bc25-sibling model; GV08->GV09, 0.5.0->0.6.0, cert-stays-bc26 player[]-unchanged, no-inert-chassis w/ -d:bc23BrokenChassis negative control, parity root-cause-or-fail Java 8 javac no --release, viewer four-files-one-starter + beats emitted+labelled+styled + settle/soak, doctrine-batch 45s, branch-only bc23-year-module, incremental-write pin in brief)
2026-09-08T06:24:40Z heartbeat phase=10
2026-09-08T07:11:04Z 10 designer returned round 1: design.md (2375 lines) — ACCEPTED against prompts/10-design.md checklist:
- [x] starter named with reason (cogame-battlecode itself; mod run, year-module boundary proved by bc20/bc21/bc24/bc25)
- [x] num_agents=2 single number in variants[bc23].game_config, all other variants + bc26 cert fixture unchanged; <SEATS>=2 cross-check named
- [x] resolution order numbered against engine GameWorld.runRound at battlecode23@af42086e; 6 prose-vs-engine conflicts + 3 engine oddities resolved against the pinned engine
- [x] scoring: points=int(60*share(islands)+22*share(anchors)+10*share(elixir)+5*share(mana)+3*share(adamantium)) f32-narrowed truncated, weights strictly super-increasing (provable win=>higher-points per rung); scores=200*wins+mean(points), league ranks results.scores (win-dominated by construction)
- [x] end conditions incl. deadline; results.reason closed; end_reason ladder from DominationFactor
- [x] per-seat observation: sealed one-shot doctrine brief, visible/hidden enumerated, no per-round observation, opponent sheet never sent
- [x] reply schema caps: 16KB bytes rune-cut, per-field rune caps, unknown-key bounds
- [x] both policies same image env-switched (PLAYER_PROMPT vs PLAYER_SCRIPTED); lemonade strong baseline + examplefuncsplayer; fallback sheet verbatim = lemonade defaults
- [x] one parallel batch of 2 LLM calls, doctrineBudgetMs=45000, inside 60% of episode timeout
- [x] degrade-never-hang failure table + doctrine_fallback event
- [x] two name spaces (Clan Ash/Clan Basil in-game; real names replay/results only)
- [x] viewer: static-replay-viewer bundle, build_replay_viewer.sh, all four files from cogame-battlecode itself (config.nims byte-identical, no MODULARIZE), data-replay-loaded/-error, 360px legible
- [x] chrome provenance: chrome_common.js byte-for-byte, replay_broadcast.html appended bc23 block, zoom decision KEEP #viewpanel (60-wide boards)
- [x] transport rules: --band/--hudscale/--statrail via relayout(), no overlay in band, endcard stops at var(--band) + seek dismisses, beats emitted+labelled+styled all three tested from committed fixture (>=24 beats over >=8 of 12 kinds)
- [x] replay self-sufficient (events+config+seed+names, wasm re-derives); best-of-N clinch semantics documented
- [x] packaging: manifest variant bc23 beside 5 others, cert stays bc26, player[] UNCHANGED w/ players_missing cross-check, config_schema year.enum extended, tokens declared+required, GV08->GV09 extended list, 0.5.0->0.6.0, game.docs + both protocols
- [x] tests: native unit incl. legality+DecisionOps bounds, e2e docker-smoke w/ substance floors MEASURED (maxRounds 800 so islands_captured>=1 reachable), strict UTF-8 parse, viewer_smoke executed by wasm-viewer job, competence gate w/ -d:bc23BrokenChassis negative control (mine-but-never-deposit), parity Tier A/A'/B/C root-cause-or-fail Temurin 8 (JDK-21 ASM trap + non-daemon threads measured), cert_probe
- [x] out of scope (v1) non-empty (14 items); no OPEN section
2026-09-08T07:11:04Z 10 -> 20 phase transition: design accepted round 1, zero rejections
2026-09-08T07:11:04Z progress phase=10 marker=design.md
2026-09-08T07:11:04Z heartbeat phase=20
2026-09-08T07:12:30Z 20 builder dispatched thread=sthr_01F7acZAb8YTcXh4zub7sXY6 branch=bc23-year-module output=runs/2026-09-08-battlecode-2023/build-report.md (mod run, no repo-create; GV08->GV09, 0.5.0->0.6.0, cert stays bc26, player[] unchanged, num_agents=2, parity Temurin 8 + exit-3-on-no-robot + System.exit pins, competence gate -d:bc23BrokenChassis, docker-smoke substance floors MEASURED maxRounds=800, viewer --timeout 120 --soak 15 + beats emitted+labelled+styled, policies 2 LLM + 2 scripted w/ player field on champion 2, PR-then-merge, git-data-API --input fallback, incremental build-report pinned in brief)
2026-09-08T07:12:30Z heartbeat phase=20
2026-09-08T10:19:00Z 00 resume at phase 20 attempt=1 session=01858aee
2026-09-08T10:24:00Z 20 resume observation: prior session's builder thread sthr_01F7acZAb8YTcXh4zub7sXY6 still active — push 2 landed 69f51a47 at 10:13:29Z (chassis+parity+tests+chrome+CI), PR #6 opened 10:14:15Z, CI runs 34214301269 (push) + 34214369355 (pull_request) in_progress on 69f51a47
2026-09-08T10:24:00Z 20 CI partial verdict on 69f51a47: parity-oracle-bc23 FAIL (examplefuncsplayer23 diverges at round 1 on all 6 maps, no ledger entry, root-cause-or-fail); bc20/21/24/25 parity green, docker-smoke green, test + wasm-viewer in_progress
2026-09-08T10:24:00Z 20 decision: no duplicate builder dispatch — monitor branch/CI for the live builder's next iteration; takeover threshold: CI complete-red with no new commit for 40 min
2026-09-08T10:24:00Z heartbeat phase=20
2026-09-08T10:36:22Z heartbeat phase=20
2026-09-08T10:56:36Z heartbeat phase=20
2026-09-08T11:06:56Z heartbeat phase=20
2026-09-08T11:15:00Z 20 CI run 34214301269 (push, 69f51a47) completed: FAILURE — sole red job parity-oracle-bc23 (examplefuncsplayer23 diverges round 1, all maps, no ledger); test 60min GREEN, wasm-viewer GREEN, docker-smoke GREEN, bc20/21/24/25+bc26 parity GREEN
2026-09-08T11:15:00Z 20 takeover clock: no new branch commit since 10:13:29Z; if none lands by ~11:54Z dispatch builder round 2 with the parity-bc23 failing log
2026-09-08T11:09:42Z 20 coordinator diagnosis of parity-bc23 red (artifact parity-bc23, run 34214301269): traces are in TRUE game-state parity on all 6 maps — md5(nim head)==md5(java head) after stripping the trailing bc= field; sole mismatch is the comparator normalizing bc= off the Java trace but not off the Nim trace (nim emits bc=0 on every unit line). One-commit fix: normalize both sides identically (or stop emitting bc= in the nim tracer) + ledger/PARITY.md note
2026-09-08T11:09:42Z heartbeat phase=20
2026-09-08T11:15:27Z 20 builder fix landed cd58a9cd 11:12:13Z: parity_tiers_bc23 strips bc= from BOTH traces (was java-only) + bc23's own bytecode limits — matches coordinator diagnosis; CI re-running: 34219450002 (push) + 34219453501 (pull_request)
2026-09-08T11:15:27Z progress phase=20 marker=ci-run-34219450002
2026-09-08T11:20:38Z heartbeat phase=20
2026-09-08T11:35:35Z heartbeat phase=20
2026-09-08T11:50:33Z heartbeat phase=20
2026-09-08T12:05:32Z heartbeat phase=20
2026-09-08T12:07:38Z 20 CI GREEN on branch: run 34219450002 (push, cd58a9cd) success — parity-bc23 fixed; PR run 34219453501 also success; builder merged PR #6 at 12:07:00Z merge=f9b292a2; main CI run 34224289835 in_progress
2026-09-08T12:07:38Z progress phase=20 marker=ci-run-34224289835
