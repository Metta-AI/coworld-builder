# 2026-08-27-lux-ai — log

2026-08-27T12:16:49Z 00 claim 2026-08-27-lux-ai idea=1217748519704392 slug=lux-ai
2026-08-27T12:17:56Z 00 run task 1217903600079381 created in Running with 9 phase subtasks; heartbeat_at set session=cd77d683
2026-08-27T12:17:56Z heartbeat phase=10
2026-08-27T12:22:00Z 10 starter=coworld-ctf reason=per-tick grid loop port of an existing external RL env (Lux AI S1); 8-deep precedent of external-env ports on coworld-ctf all green (gridlock, pistonball, knights-archers, walker-waterworld, smac, magent, rware, flatland); moba PORTING row rejected — moba ships no client/ or replay-viewer/ stack and the viewer wasm must compile the same sim module
2026-08-27T12:22:00Z 10 rails: season=S1 (cities/wood-coal-uranium/day-night fuel; the idea's headline loop; S2/S3 named as background), seats=2 per idea, scoring=city tiles at end (S1 rule), LLM cadence sparse (strategy directive every N turns, scripted micro per turn) to fit 720 s budget
2026-08-27T12:25:30Z 10 dispatch designer round=1 for docs/plans/2026-08-27-lux-ai-design.md -> runs/2026-08-27-lux-ai/design.md
2026-08-27T12:42:51Z 10 designer returned round=1: runs/2026-08-27-lux-ai/design.md (1913 lines)
2026-08-27T12:42:51Z 10 checklist: starter✓ num_agents=2-every-variant+cert✓ resolution-order-13-steps✓ scoring+sign+ranks✓ end-conditions+reason-enum✓ observation-full+hidden-list✓ reply-schema-rune-caps✓ both-policies-env-switched+baseline-algos✓ parallel-batch+budget-arithmetic-251s/519s<720s✓ degrade-never-hang✓ two-name-spaces✓ viewer-static-wasm+360px✓ four-viewer-files=coworld-ctf+data-replay-loaded/error✓ chrome-provenance+viewpanel-dropped✓ transport-rules+beat-buttons-CSS✓ replay-self-sufficient✓ packaging-docs+protocols-both✓ tests-incl-bounded-orders+utf8+viewer-smoke-executed✓ out-of-scope-non-empty✓ — ACCEPTED round 1
2026-08-27T12:42:51Z progress phase=10 marker=runs/2026-08-27-lux-ai/design.md
2026-08-27T12:42:51Z 10 -> 20 phase transition: entering build
2026-08-27T12:42:51Z heartbeat phase=20
2026-08-27T12:43:50Z 20 repo created: https://github.com/Metta-AI/cogame-lux-ai (public); propagate-secrets run 33073239885 success; SOFTMAX_TOKEN + ANTHROPIC_API_KEY listed on repo
2026-08-27T12:44:45Z 20 dispatch builder round=1: implement design.md on Metta-AI/cogame-lux-ai until ci.yml green on main
2026-08-27T15:11:45Z 20 builder returned round=1: ci.yml GREEN run=33085620073 sha=1c36d56b main; 3 red rounds fixed en route (player exit, COG_BASE, wasm32 getAppDir/mixHash64); art=nano-banana; workflows parse, inputs verified, placeholder grep clean; design note bytes at docs/plans identical
2026-08-27T15:11:45Z 20 note: builder pushed via GitHub API (sandbox git push limited to claude/ branches); remote tree verified byte-identical, no force
2026-08-27T15:11:45Z 20 deviations logged for reviewer: production-before-research amendment, prospector night-guard+seed-blob, broadcast_core.js inherited byte-for-byte, CTF_WIRE x3, tuned baseline params, forensics helpers omitted
2026-08-27T15:11:45Z progress phase=20 marker=33085620073
2026-08-27T15:11:45Z 20 -> 30 phase transition: entering review loop round 1
2026-08-27T15:11:45Z heartbeat phase=30
2026-08-27T15:12:42Z 30 dispatch reviewer round=1 target sha=1c36d56 -> runs/2026-08-27-lux-ai/reviews/r1-review.md
2026-08-27T15:32:18Z 30 reviewer returned r1: 20 findings (1 blocking B1 legibility DOM-text/fixture-inert, 19 non-blocking) -> reviews/r1-review.md
2026-08-27T15:32:18Z 30 dispatch fixer round=1 -> reviews/r1-fixes.md
2026-08-27T15:32:18Z heartbeat phase=30
2026-08-27T16:14:58Z 30 fixer returned r1: B1 fixed (e673713, lux-say band + fixture assertions + CI textfit gate), N2/N14/N16/N4 fixed, N5 refused with evidence; CI green run=33090975748 sha=66b5d3b -> reviews/r1-fixes.md
2026-08-27T16:14:58Z progress phase=30 marker=r1-fixes.md
2026-08-27T16:14:58Z 30 dispatch judge round=1 at sha=66b5d3b -> reviews/r1-verdict.md
2026-08-27T16:14:58Z heartbeat phase=30
2026-08-27T16:29:36Z 30 judge returned r1: BLOCKING=1 ([correctness] src/lux/replays.nim:125 playback ignores recorded lobby length — falsifies checklist item 2); B1 fix verified, no test loosening -> reviews/r1-verdict.md
2026-08-27T16:29:36Z progress phase=30 marker=r1-verdict.md
2026-08-27T16:29:36Z 30 round 2 begins: dispatch reviewer round=2 -> reviews/r2-review.md
2026-08-27T16:29:36Z heartbeat phase=30
2026-08-27T16:46:31Z 30 reviewer returned r2: 1 blocking (lobby-start replay divergence, reproduced by execution; introduced in fork vs ctf), 5 advisory; no regressions from r1 fixes -> reviews/r2-review.md
2026-08-27T16:46:31Z 30 dispatch fixer round=2 -> reviews/r2-fixes.md
2026-08-27T16:46:31Z heartbeat phase=30
2026-08-27T17:13:08Z 30 fixer returned r2: B1 fixed (c74b230 playback honours recorded lobby; late-join re-derivation test), N1/N2/N3 fixed, N4 disputed with evidence; CI green run=33096195543 sha=88cc3f75 -> reviews/r2-fixes.md
2026-08-27T17:13:08Z progress phase=30 marker=r2-fixes.md
2026-08-27T17:13:08Z 30 dispatch judge round=2 at sha=88cc3f75 -> reviews/r2-verdict.md
2026-08-27T17:13:08Z heartbeat phase=30
2026-08-27T17:24:51Z 30 judge returned r2: BLOCKING=0 (markers agree); B1 verified fixed, all 15 checklist items pass at sha=88cc3f75; advisory residue: check_gameversion.sh path retarget (non-blocking) -> reviews/r2-verdict.md
2026-08-27T17:24:51Z progress phase=30 marker=r2-verdict.md
2026-08-27T17:24:51Z 30 -> 40 phase transition: entering release
2026-08-27T17:24:51Z heartbeat phase=40
2026-08-27T17:25:36Z 40 dispatch builder for release chain (coworld-release.yml, version 0.1.0 first attempt, policies from tools/ci/policies.json)
2026-08-27T17:55:18Z 40 builder report: v0.1.0 run=33098369085 FAIL certify (no Ping->Pong; fixed 28be702, CI 33098806848 green); v0.1.1 run=33099182742 canonical:false read-too-early; v0.1.2 run=33100074041 same — both cow_ids read back canonical:true from API minutes later; workflow read-back defect, fix 3639a79 (poll canonical up to 20 min before secret put)
2026-08-27T17:55:18Z 40 rails decision: authorise dispatch #4 v0.1.3 — not a cert failure (certify.ok true on both attempts); change #4 = workflow canonical read-back, distinct from bumps; template delta (templates/coworld-release.yml reads canonical too early) noted for phase 80 LEARNINGS
2026-08-27T17:55:18Z progress phase=40 marker=33100074041
2026-08-27T17:55:18Z heartbeat phase=40
2026-08-27T18:27:58Z 40 dispatch #4 v0.1.3 run=33100903880: all criteria green except canonical read-back — raw urllib GET from runner 403s (same URL+token 200 from sandbox); cow_48fbd033 confirmed canonical:true via API; fix 77ee1d5 switches poll to 'coworld status --json'
2026-08-27T18:27:58Z 40 rails decision: authorise dispatch #5 v0.1.4 — bumps are free; adopting 0.1.3 would ship a release-result.json saying canonical:false which fails phase 60 check 7 as written; change #5 (CLI read-back) distinct from all four before
2026-08-27T18:27:58Z progress phase=40 marker=33100903880
2026-08-27T18:27:58Z heartbeat phase=40
2026-08-27T18:39:33Z 40 dispatch #5 v0.1.4 run=33103630909 SUCCESS: canonical:true certify.ok:true replay_liveness=skipped-static secret_put:true; cow_85ac57ce-ce33-44dc-a00f-d74141fdd9fe; policies lux-ai-lumberjack:v4 (champ1), lux-ai-nightwatch:v4 (champ2, ply_bac48eb1), lux-ai-forester:v4 + lux-ai-prospector:v4 (fillers); release-result.json committed
2026-08-27T18:39:33Z 40 template deltas for LEARNINGS/phase 80: (1) coworld-release.yml needs canonical read-back step post-upload (hosted cert settles after --wait-hosted-smoke returns); (2) read-back must use coworld CLI, raw HTTPS GET 403s from runners; (3) triage row: certify 'Ping with Pong' -> websocket handler missing Ping->Pong branch
2026-08-27T18:39:33Z progress phase=40 marker=33103630909
2026-08-27T18:39:33Z 40 -> 50 phase transition: entering league
2026-08-27T18:39:33Z heartbeat phase=50
2026-08-27T18:40:44Z 50 seed 200: lseed_62ee933e league=league_91cd77d4-0030-495d-81c4-37de0b298801; division PUT 200: div_42529bfd-3620-42c3-93df-068da80201dc; settings POST 200 (round_robin, filler_policy, elo 1000/32, mean, 15 min)
2026-08-27T18:40:44Z 50 note: GET /leagues returns a plain array here (no .entries) — matched league by id from the seed response
2026-08-27T18:43:11Z 50 champion1 submit run=33104666848 ok sub_eda7587f (lux-ai-lumberjack:v4, daveey); champion2 submit run=33104719376 ok sub_8a166ac3 (lux-ai-nightwatch:v4, daveey-1)
2026-08-27T18:43:11Z 50 fillers registered 200 BEFORE trigger: forester:v4=4269d16d prospector:v4=3613cd05; unpause 200; trigger 200; round 1 pending; entrant_attributions = both champions
2026-08-27T18:43:11Z progress phase=50 marker=league_91cd77d4-0030-495d-81c4-37de0b298801
2026-08-27T18:43:11Z 50 -> 60 phase transition: entering verify
2026-08-27T18:43:11Z heartbeat phase=60
2026-08-27T18:43:53Z 60 dispatch verifier: eight checks per prompts/60-verify.md -> runs/2026-08-27-lux-ai/VERIFY.md (75-min round bound)
2026-08-27T19:12:07Z 60 verifier returned: 8/8 TRUE -> VERIFY.md (rounds 1+2 completed, both champions ranked 2 rounds, replay complete/full_time 72/72 llm directives 0 fallbacks, logs CLEAN, static iframe sha matches manifest, cert skipped-static, viewer-check 33106609970 loaded:true clocks advance)
2026-08-27T19:12:07Z 60 check-4 deviation recorded: cityTiles sum = 2 vs design threshold >2; verifier marked TRUE on prompt's own criteria, flagged for judge
2026-08-27T19:12:07Z progress phase=60 marker=round_ee8f3123
2026-08-27T19:12:07Z 60 dispatch judge for VERIFY.md adjudication -> reviews/verify-verdict.md
2026-08-27T19:12:07Z heartbeat phase=60
2026-08-27T19:17:29Z 60 judge returned: BLOCKING=0 (markers agree); check-4 cityTiles threshold ruled non-blocking (design proxy, not SPEC/prompt); all 8 lines re-verified independently -> reviews/verify-verdict.md
2026-08-27T19:17:29Z 60 -> 70 phase transition: entering announce
2026-08-27T19:17:29Z heartbeat phase=70
