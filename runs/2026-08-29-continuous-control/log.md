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
