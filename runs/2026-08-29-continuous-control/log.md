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
