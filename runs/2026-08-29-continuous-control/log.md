# 2026-08-29-continuous-control — log

2026-08-29T07:19:34Z 00 claim 2026-08-29-continuous-control idea=1217748466314558 slug=continuous-control session=9924a629
2026-08-29T07:19:34Z 00 run task 1217981679055859 created in Running, 9 phase subtasks, heartbeat_at set
2026-08-29T07:19:34Z 00 -> 10 phase transition: entering design
2026-08-29T07:20:43Z 10 starter=coworld-ctf (rails: real-time continuous-physics loop, rules written for this coworld — row 2; not a bit-exact port: MuJoCo/dm_control cannot embed in a wasm-compilable Nim sim; precedent physics-bodies 2026-08-28, sokoban 2026-08-29)
2026-08-29T07:20:43Z 10 designer dispatched -> runs/2026-08-29-continuous-control/design-draft.md
2026-08-29T07:47:29Z 10 designer returned design-draft.md (2190 lines), round 1
2026-08-29T07:47:29Z 10 checklist: starter[x] num_agents[x] resolution-order[x] scoring[x] end-conditions[x] observation[x] reply-schema-caps[x] both-policies[x] batch-budget[x] degrade-never-hang[x] name-spaces[x] viewer-static-wasm[x] viewer-four-files-one-starter[x] chrome-provenance-zoom[x] transport-rules[x] replay-self-sufficient[x] packaging[x] tests[x] out-of-scope[x] — ACCEPTED round 1
2026-08-29T07:47:29Z 10 design.md copied to runs/2026-08-29-continuous-control/design.md
2026-08-29T07:47:29Z progress phase=10 marker=design.md
2026-08-29T07:47:29Z 10 -> 20 phase transition: entering build
2026-08-29T07:47:29Z heartbeat phase=20
2026-08-29T07:48:25Z 20 repo Metta-AI/cogame-continuous-control created public; propagate-secrets run 33241676850 success; SOFTMAX_TOKEN+ANTHROPIC_API_KEY confirmed
2026-08-29T07:48:25Z 20 builder dispatched (round 1)
2026-08-29T10:13Z 20 builder round 1 push 713e9ac (108 files): src/cc Q16 integer sim + driver + server, client/ derived from coworld-ctf by scripts/build_broadcast_page.py, replay-viewer forked from ctf only, nano-banana machine sheet, 62 test cases green locally in debug and -d:release. CI run 33247064780 FAILED (wasm-viewer): the page threw "$ is not defined" — the eye-level-billboard cut had swallowed `var $ = C.$;` and the four element handles.
2026-08-29T10:22Z 20 builder round 2 push 50ea3b1: cut now stops at the wire-constants banner; verified in headless chromium locally (no page error, CcChrome present, renderer_fixture drives the real page to data-replay-loaded at 360/640/1280 px). CI run 33247466068 FAILED (wasm-viewer): "parse replay: value out of range: 4294965222 notin int32" — a negative Q16 keyframe word round-tripped through Nim's `int`, which is 32-bit under --cpu:wasm32 and invisible to the native tests.
2026-08-29T10:33Z 20 builder round 3 push cfe8855: the replay codec's 32-bit primitives go through uint32 end to end. CI run 33247782024 SUCCESS on main (test, docker-smoke, wasm-viewer). Exit criterion met.
2026-08-29T10:45Z 20 push 3739c2c (viewer legibility: gait card to the right gutter, brighter link chips, brighter bed) CI run 33248087990 SUCCESS. Push 4c1b310 (horizon drawn as two copies) CI run 33248347102 SUCCESS on main — the shipped green sha.
2026-08-29T11:00Z 20 EXIT: ci.yml success on main at 4c1b310 (run 33248347102). Placeholder gate clean; all three workflows parse and are registered; release inputs version|policies|put_secret|skip_certify and submit inputs player_id|policy|league_id present; release-result / submit-result artifacts and the per-policy "player" field present; gh secret list shows SOFTMAX_TOKEN + ANTHROPIC_API_KEY; docker_smoke.sh and build_replay_viewer.sh both mode 100755.
2026-08-29T10:51:04Z 20 verified: ci.yml success on main 4c1b310 run 33248347102; workflows ci/release/submit all active
2026-08-29T10:51:04Z progress phase=20 marker=33248347102
2026-08-29T10:51:04Z 20 -> 30 phase transition: entering review loop round 1
2026-08-29T10:51:04Z heartbeat phase=30
2026-08-29T10:52:18Z 30 r1 reviewer dispatched (sha 4c1b310)
2026-08-29T11:09:10Z 30 r1 reviewer returned r1-review.md (18 findings: 1 blocking-candidate F1 uncapped stop-detail rune truncation, 17 advisory)
2026-08-29T11:09:10Z 30 r1 fixer dispatched
2026-08-29T11:09:10Z heartbeat phase=30
2026-08-29T11:28:28Z 30 r1 fixer returned r1-fixes.md: 10 fixed (F1 e9902cc rune-cap stop detail, F2,F3,F4,F5,F6,F13,F14,F16,F17), 8 no-change with evidence (F7,F8,F9,F10,F11,F12,F15,F18); green a8db2b3 run 33249877981
2026-08-29T11:28:28Z 30 r1 judge dispatched (sha a8db2b3)
2026-08-29T11:28:28Z heartbeat phase=30
2026-08-29T11:42:43Z 30 r1 judge returned r1-verdict.md: blocking=1 (legibility item 15: say feed-row unmeasured; fixture SAY 133!=140 runes, no full-length assertion, no feed-row box check). F1 refuted-as-fixed at a8db2b3; items 1-14 PASS
2026-08-29T11:42:43Z progress phase=30 marker=r1-verdict.md
2026-08-29T11:42:43Z 30 round 2: reviewer dispatched (head a8db2b3, delta focus + standing verdict finding)
2026-08-29T11:42:43Z heartbeat phase=30
2026-08-29T11:58:44Z 30 r2 reviewer returned r2-review.md: 8 findings, F1 blocking (ccFeed passes string to pushFeed(row:Node) -> TypeError swallowed; feed_lines=0, banners never render; fixture asserts nothing); all 10 r1 fix commits verified clean
2026-08-29T11:58:44Z 30 r2 fixer dispatched
2026-08-29T11:58:44Z heartbeat phase=30
2026-08-29T12:33:50Z 30 r2 fixer returned r2-fixes.md: 7 fixed (F1 38cc254a feed row Node + regenerated page + console-clean CI step; B1 460e7ddb+cd6784bb fixture 140-rune say row asserted at 360/640/1280; F2,F3,F4,F6,F7,F8), 1 informational no-change (F5); green b67f8c86 run 33252260364, feed_lines=2, console chrome errors 0
2026-08-29T12:33:50Z 30 r2 judge dispatched (sha b67f8c86)
2026-08-29T12:33:50Z heartbeat phase=30
2026-08-29T12:46:34Z 30 r2 judge returned r2-verdict.md: blocking=0/BLOCKING=0 — all 15 checklist items PASS at b67f8c86 (run 33252260364); test-pin change judged a correction
2026-08-29T12:46:34Z progress phase=30 marker=r2-verdict.md
2026-08-29T12:46:34Z 30 -> 40 phase transition: entering release (2 rounds used of 4)
2026-08-29T12:46:34Z heartbeat phase=40
2026-08-29T12:47:55Z 40 dispatch version=0.1.0 run=33253409378 step_failed="Build the Coworld manifest" decision=manifest had game.image at the game top level (KeyError image in coworld bundle.py) and resources.limits.memory (extra=forbid); moved image into game.runnable and dropped limits.memory, pushed 0dcd8d1, bumping to 0.1.1
2026-08-29T12:56:09Z 40 dispatch version=0.1.1 run=33253738053 step_failed="Upload the Coworld" decision=certify passed 10/10 with liveness skipped and all 4 policies minted v1, then upload 400ed "game runnable may not declare a cpu limit; only player pods honor one" — dropped game.runnable.resources.limits (13904cc), bumping to 0.1.2
2026-08-29T13:02:45Z 40 dispatch version=0.1.2 run=33254010784 step_failed=none decision=SUCCESS ok=true canonical=true cow_id=cow_39456c26-cffa-4d99-9be9-b2b49454143c certify 10/10 liveness skipped, hosted smoke passed + certified, 4 policies at v2 (throttle owned by daveey-1), secret_put=true; release-result.json persisted
2026-08-29T13:20:00Z 40 note ci: test 40 pinned the image at game.image (the place the CLI never reads) — repointed at game.runnable.image and pinned "no limits on the game runnable" (e144ca1); ci.yml green on main run=33254519406 (test, docker-smoke, wasm-viewer all success)
2026-08-29T13:20:56Z 40 release green: version 0.1.2 run 33254010784, cow_39456c26-cffa-4d99-9be9-b2b49454143c canonical, certified, 4 policies v2, secret_put; 3 dispatches (0.1.0 manifest KeyError image->runnable, 0.1.1 400 runnable cpu limit, 0.1.2 ok); repo commits 0dcd8d1,13904cc,e144ca1, CI green 33254519406
2026-08-29T13:20:56Z 40 note for 80-LEARNINGS: templates/ci.yml lacks a coworld-CLI manifest-validate step (two release dispatches burned); triage additions: KeyError image -> game.runnable.image; 400 "game runnable may not declare a cpu limit" -> limits only on player[]
2026-08-29T13:20:56Z progress phase=40 marker=33254010784
2026-08-29T13:20:56Z 40 -> 50 phase transition: entering league
2026-08-29T13:20:56Z heartbeat phase=50
2026-08-29T13:22:17Z 50 seed 200: lseed_d53f0696, league_62a1e77b-c464-41ba-90df-702fc0d9d3db
2026-08-29T13:22:17Z 50 division 200: div_07b556f6-3e13-40db-afd8-d0823c6ed9d3
2026-08-29T13:22:17Z 50 settings 200: round_robin/filler_policy, elo k=32, round_interval=15m
2026-08-29T13:22:17Z heartbeat phase=50
2026-08-29T13:26:58Z 50 champion1 submit ok run 33254853655 sub_251157fb (gaitsmith:v2, daveey); champion2 submit ok run 33254884101 sub_a414ae47 (throttle:v2, daveey-1)
2026-08-29T13:26:58Z 50 fillers registered: trotter:v2 bd151d35, plodder:v2 ece2febe (verified list == fillers only)
2026-08-29T13:26:58Z 50 unpaused (rounds_paused_at=null); trigger-round accepted workflow ladder-league_62a1e77b; rounds list still empty, polling
2026-08-29T13:26:58Z heartbeat phase=50
2026-08-29T13:38:33Z 50 second trigger HTTP 200, rounds still 0 — platform round-creation stall (sokoban+minecraft same incident)
2026-08-29T13:38:33Z 90 blocked phase=50 ask="restart/repair the Temporal ladder workflow for league_62a1e77b-c464-41ba-90df-702fc0d9d3db so rounds are created" subtask=1217968974654490
2026-08-29T13:38:33Z 90 asana: run task 1217981679055859 moved to Blocked; idea comment 1217968893159423 on 1217748466314558
2026-08-29T13:38:33Z progress phase=50 marker=sub_a414ae47
2026-08-29T13:38:33Z session end: stopped in phase 50 (blocked); next action = on subtask 1217968974654490 completion, resume phase 50 at step 9 (confirm a round exists pending/running/completed, verify exit criterion, then -> 60)
2026-08-29T13:38:33Z heartbeat phase=50
2026-08-29T13:39:10Z 90 subtask body + STATE.blocked.error corrected (accurate trigger times 13:21Z/13:31Z; outage age is platform-wide, hours)
2026-09-03T19:30:15Z 00 resumed after unblock subtask=1217968974654490 attempts_reset=50
2026-09-03T19:30:15Z 00 operator comment acknowledged (David Bloomin 2026-09-03T19:12:27Z): credit pool was root cause, 100 credits granted + drip 100/day cap 300, round 1 triggered pending; resume phase 50 at step 9
2026-09-03T19:30:15Z 00 resume at phase 50 attempt=1 session=954c9761
2026-09-03T19:32:08Z 50 resume step 9: rounds 1+2 completed (round_26e98f6c, round_74324044), pool_credits=191.3, unpaused (rounds_paused_at=null)
2026-09-03T19:32:08Z 50 exit criterion verified: leaderboard shows daveey-1 throttle:v2 rank 2 and daveey gaitsmith:v2 rank 7; fillers trotter:v2 bd151d35 + plodder:v2 ece2febe only
2026-09-03T19:32:08Z 50 asana: phase-50 subtask 1217967264167973 completed; comment 1218163123949418
2026-09-03T19:32:08Z progress phase=50 marker=round_26e98f6c-a4d5-4c23-bd62-0ba167ed7f8b
2026-09-03T19:32:08Z 50 -> 60 phase transition: entering verify
2026-09-03T19:32:08Z heartbeat phase=60
2026-09-03T19:33:15Z 60 verifier dispatched thread=sthr_01JFFKZ62ptaT2y9ahXwBtek (8 checks + viewer-check.yml; 2 rounds already completed)
2026-09-03T19:43:03Z 60 check1 TRUE rounds 1 (round_26e98f6c) + 2 (round_74324044) completed 19:13:24Z/19:28:17Z, error null; fillers bd151d35+ece2febe registered 2026-08-29T13:26:58Z, before round 1 was created
2026-09-03T19:43:03Z 60 check2 TRUE leaderboard: daveey-1 continuous-control-throttle:v2 rank 2 (rounds_played 2), daveey continuous-control-gaitsmith:v2 rank 7 (rounds_played 2); no filler/Baseline row
2026-09-03T19:43:03Z 60 check3 TRUE all 7 episode-requests of round 2 completed with replay_url; champion episodes ereq_e7e02675 (daveey, 20.543) and ereq_e6aad2bb (daveey-1, 57.236); num_agents=1 so one seat per episode by design
2026-09-03T19:43:03Z 60 check4 TRUE replay_summary.py output is strict UTF-8 JSON; protocol continuous-control/v1, reason complete/ladderComplete, 20 llm orders, 0 fallbacks, 19 says, 4 gaits/14 cadences, distanceTotal 36.344
2026-09-03T19:43:03Z 60 check5 TRUE hosted logs for both champion episodes decoded (ast.literal_eval) and CLEAN; 20/29 LLM calls all HTTP 200
2026-09-03T19:43:03Z 60 check6 TRUE static route via POST /coworlds/replays/session ready=true, sha256:5a975e9f... == manifest_sha, no /client/replay; playlist empty for documented single-seat reason (LEARNINGS 2026-08-28 nethack), pool.replays=7; cross-check sokoban(single)=0 vs paintbot 21/escrow 1/eleusis 4
2026-09-03T19:43:03Z 60 check7 TRUE committed release-result.json .certify.replay_liveness = "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"
2026-09-03T19:43:03Z 60 check8 TRUE viewer-check run 33797485426 loaded=true ms=3940, three differing clocks (HOPPER t8 / CHEETAH t263 / WALKER t51); starter chrome present; residue: endcard table column collision + "PAR 40000000"/zeroed m,upright,saturated in endcard subtitle
2026-09-03T19:43:03Z 60 verify complete: 8/8 TRUE, VERIFY.md + viewer-check artifact committed
2026-09-03T19:44:13Z 60 verifier returned 8/8 TRUE at ef343dd (VERIFY.md 595 lines, viewer-check 33797485426 loaded=true clocks differ); residue noted: endcard column collision, PAR line micro-points bug, feed_lines=0 at load
2026-09-03T19:44:13Z 60 judge dispatch next: adjudicate VERIFY.md vs SPEC definition of done
2026-09-03T19:44:13Z heartbeat phase=60
2026-09-03T19:44:48Z 60 judge dispatched thread=sthr_01Q8dV2A4i7VqynsQHBbh855 (adjudicate VERIFY.md 8/8 + residue rulings)
2026-09-03T19:53:40Z 60 judge returned verify-verdict.md at deb9643: all 8 checks CONFIRMED (live refetch, round 3 completed 19:40:39Z, daveey-1 rank 1 / daveey rank 6), 4 residue items NON-BLOCKING, BLOCKING: 0
2026-09-03T19:53:40Z progress phase=60 marker=verify-verdict.md
2026-09-03T19:53:40Z 60 -> 70 phase transition: entering announce
2026-09-03T19:53:40Z heartbeat phase=70
2026-09-03T19:55:12Z 70 announce attempted_at written (pre-POST marker), body 1755 chars
2026-09-03T19:55:31Z 70 announce msg=1545160286258864238 (200, flags=4, embeds=[], 1755 chars)
2026-09-03T19:55:31Z progress phase=70 marker=announce.discord_message_id=1545160286258864238
2026-09-03T19:55:31Z 70 -> 75 phase transition: entering atlas
2026-09-03T19:55:31Z heartbeat phase=75
2026-09-03T19:56:41Z 75 atlas continent=simulations (borrowed MuJoCo/DMC locomotion benchmark bodies — a borrowed world, rails call)
2026-09-03T19:56:41Z 75 atlas dispatch=33799329796 region=simulations at=536,271 clearance=69.0 label="Continuous Ctrl" (another atlas run 33799293022 in progress ahead of ours in the concurrency queue; slug will be verified from artifact)
2026-09-03T19:56:41Z heartbeat phase=75
2026-09-03T20:03:21Z 75 atlas dispatch 1 failed: step=build, 61 unplaced leagues named; fix per step 8 = place them all via extra_cities
2026-09-03T20:03:21Z 75 atlas continents decided for backlog (rails): paintlands=15 (atari-cabinet, paintbot/campaign+elite, derks-gym, gen-generals-io, grid-wars, halite, lux-ai, magent-battle, physics-bodies, pommerman, pudge-wars, smac-starcraft-micro, snake-royale, vizdoom-deathmatch), simulations=16 (atari-57, citysim, crafter, flatland, grf-football, hide-and-seek, knights-archers, minecraft, minigrid, nethack, particle-worlds, pistonball, procgen, rware-warehouse, sumo-traffic-signals, walker-waterworld), tabletop=9 (board-gauntlet, cogiavelli, cogplomacy, fog-of-war-boards, goofspiel-oshi-zumo, hanabi, liars-dice, polyduel, trick-taking), commons=12 (chemistry, coins, commons-family, cooperative-hunting, factory-commons, firm, fruit-market, garble, gift-refinements, gnomic, matrix-games, territory), parlour=6 (chorus, cogchemists, cogmud, cogolf, hidden-agenda, negotiation-games), shire=3 (collab-cooking, daycare, sokoban); coords via atlas_spot.py incremental, min clearance 22.5
2026-09-03T20:03:21Z 75 atlas dispatch=33799967564 region=simulations at=536,271 clearance=69.0 extra_cities=61 (placed for the whole backlog incl. other runs' slugs per step 8)
2026-09-03T20:03:21Z heartbeat phase=75
2026-09-03T20:06:04Z 75 atlas dispatch 2 (33799967564) failed: step=build, stale CITIES line paintbot/classic not in coworld-stats (paintbot/ctf also stale vs /api/coworlds)
2026-09-03T20:06:04Z 75 atlas dispatch=33800244987 region=simulations at=536,271 extra_cities=61 drop_slugs=paintbot/classic,paintbot/ctf (dispatch 3 of 3)
2026-09-03T20:06:04Z heartbeat phase=75
2026-09-03T20:08:00Z 75 atlas pr=https://github.com/Metta-AI/metta/pull/21389 status=pr_open (automerge armed; waits on Graphite merge queue; placed 61 backlog leagues + dropped 2 stale paintbot slugs in the same PR)
2026-09-03T20:08:00Z progress phase=75 marker=https://github.com/Metta-AI/metta/pull/21389
2026-09-03T20:08:00Z 75 -> 80 phase transition: entering close
2026-09-03T20:08:00Z heartbeat phase=80
