# 2026-08-28-atari-57 — log

2026-08-28T16:01:06Z 00 claim comment posted on idea 1217748424043450 (story 1217956071581197); 20s recheck clean
2026-08-28T16:01:30Z 00 claim 2026-08-28-atari-57 idea=1217748424043450 slug=atari-57
2026-08-28T16:02:30Z 00 run task 1217956230954022 created in Running with 9 phase subtasks; heartbeat_at=2026-08-28T16:02:30Z session=c2e2acef
2026-08-28T16:02:30Z 00 -> 10 phase transition: STATE.phase=10 written before designer dispatch
2026-08-28T16:08:00Z 10 starter=coworld-ctf (rails: fresh real-time arcade game, no emulator/ROM hostable — same ruling as atari-cabinet 2026-08-26; paintbot row of the starter table)
2026-08-28T16:08:00Z 10 rails ruling: idea's "Seats: 1" closed at num_agents=4 isolated lanes (no inter-seat interaction; same ROM+seed per episode) — no shipped coworld has num_agents=1 and vizdoom-deathmatch deferred that shape; league rounds need multi-entrant episodes
2026-08-28T16:08:30Z 10 designer dispatched round=1
2026-08-28T16:24:00Z 10 designer returned round=1: runs/2026-08-28-atari-57/design.md (1975 lines)
2026-08-28T16:27:00Z 10 design accepted round=1 — checklist: [x] starter named+reason (coworld-ctf, L22-36: real-time loop w/ fresh rules = first starter-table row; explicitly not the moba port row, no emulator/ROM hostable) [x] num_agents=4 single number, all three variants' game_config + certification.game_config + SMOKE_SEATS=4 (L64-70,129,1690-1706,1712-1718) [x] numbered resolution order: tick steps 1-2-3 with lane sub-steps 3.1-3.x, lane order 0->3, action byte dir=cmd mod 5 / act=cmd div 5, cmd>=15 repaired to 0 both paths (L434-527) [x] scoring formula score=points/100+livesLeft, non-negative, higher better, 7 worked examples, league ranks mean results.scores; total placement chain score->lives->earlier lastScoreTick->seat index (L528-585) [x] end conditions closed enum reason {complete,deadline,fault} x endRule {all_lanes_over,full_time,wall_clock,sim_fault,host_error} incl deadline/wall_clock 660s declared acceptable; no-show seat -> arcader-driven lane, episode still ends normally (L586-605) [x] per-seat observation: own lane only in player frame, 4-row read-only scoreboard strip is the entire cross-lane surface; hidden = other screens + real names + seed/RNG/budget facts (L1100-1207, test 8) [x] reply schema caps: note<=160, mode/zone/fire closed enums, risk clamp [0,1], lead_ticks [0,48], say<=48 runes; rune-boundary truncation pinned w/ 4-byte emoji test; +policy<=48/detail<=200/stance record<=600/prompt<=4000 (L1207-1246) [x] both policies env-switched one image: PLAYER_PROMPT champions atari-57-highroller/atari-57-onecredit (prompts verbatim L708-828) vs PLAYER_SCRIPTED arcader/hoover with full algorithms (L829-914) [x] one parallel batch per turn (curly makeRequests batch), 24 turns x 12s spacing = 20rpm < 30rpm sidecar cap; arithmetic ~330s expected / ~465s worst < 660s stop < 720s budget shown (L641-696) [x] degrade-never-hang: attempt1 9s + retry 5s (skipped when throttled) -> arcader stance + fallback record w/ 6-cause enum; budget guard settles early complete/*; every wait bounded, no unbounded loop; no failure leaves a lane uncommanded (L662-706) [x] two name spaces: RED/BLUE/GREEN/YELLOW in-game, real names replay-config/DOM/results only, test-enforced (L127, tests 8+11) [x] viewer static wasm bundle static-replay-viewer, build_replay_viewer.sh kept executable, chrome verbatim, 10 readouts incl NEW RECORD banner + stance chips + momentum, 360px arithmetic 10.3px/tile with 4x1 and 21x21 rejected numerically (L1359-1582) [x] all four viewer files from coworld-ctf alone, no MODULARIZE/EXPORT_NAME, onRuntimeInitialized bootstrap kept; data-replay-loaded on first drawn frame / data-replay-error on failure stated with starter line numbers (L1369-1391) [x] chrome provenance: chrome_common.js byte-for-byte sha256-pinned, replay_broadcast.html game block APPENDED with a57-prefixed names, exact removed-element list, zoom decided: #viewpanel DROPPED (fixed 1400x1400 1:1 board) (L1392-1431) [x] transport rules: --band/--hudscale/:root via relayout(), no overlay in band, endcard bottom var(--band) dismissed by every seek, beats clickable labelled <button> with CSS per kind asserted (L1536-1552) [x] replay self-sufficient: COWLDA57 binary carries config JSON (seed, rom, parScore, resolved preset, map), 4 register records, stance/pickup/life_lost/screen_clear/result records, hash chain; replay_summary.py strict-UTF-8 (L1286-1358) [x] packaging: compose.yaml single service atari-57, {{ATARI_57_IMAGE}} derived, manifest template with config_schema minItems/maxItems everywhere, results_schema, game.docs readme+3 pages, game.protocols BOTH player+global as typed objects, cert fixture num_agents=4 livesPerLane=9 minTicks==maxTicks==1440 (60s replay > 12s soak), UPLOAD_REQUIRED gate (L1584-1740) [x] tests: 16 Nim tests incl sim units (test 1), bounded-orders/legality on baselines (test 5), e2e episode->replay re-sim for every end reason (test 10), strict-UTF-8 parse w/ forced non-ASCII (test 10), viewer smoke EXECUTED by wasm-viewer job vs docker-smoke replay --soak 12 --strict-text-bounds + renderer_fixture.html real-page step (L1742-1929) [x] out of scope non-empty 13 items (L1931-1975)
2026-08-28T16:27:00Z 10 -> 20 phase transition: STATE.phase=20 written before builder dispatch
2026-08-28T16:27:00Z progress phase=10 marker=runs/2026-08-28-atari-57/design.md
2026-08-28T16:27:00Z heartbeat phase=20
2026-08-28T16:40:00Z 20 repo created: https://github.com/Metta-AI/cogame-atari-57 (public)
2026-08-28T16:41:10Z 20 propagate-secrets run 33191112518 success; gh secret list shows SOFTMAX_TOKEN + ANTHROPIC_API_KEY on cogame-atari-57
2026-08-28T16:41:30Z 20 builder dispatched round=1
2026-08-28T19:40:24Z 00 resume at phase 20 attempt=1 session=f573b7e6
2026-08-28T19:42:17Z 20 builder round 1 complete (background thread survived prior session): pushes d31e0f79 + 309a9b34; ci.yml run 33201067921 success, run 33203089677 success on main@309a9b34
2026-08-28T19:42:17Z 20 exit checks pass: files+exec bits ok, placeholders clean, 3 workflows parse (release inputs version/policies/put_secret/skip_certify; submit inputs player_id/policy/league_id), release-result+submit-result artifacts present, champion2 player=ply_bac48eb1-662e-44f8-973d-f3e016dccf5d, num_agents=4 in 3 variants + cert fixture
2026-08-28T19:42:17Z progress phase=20 marker=33203089677
2026-08-28T19:42:17Z 20 -> 30 phase transition: STATE.phase=30 review_round=1 written before reviewer dispatch
2026-08-28T19:42:48Z 30 reviewer dispatched round=1 (repo checkout /tmp/cogame-atari-57 @ 309a9b34)
2026-08-28T20:00:46Z 30 reviewer returned round=1: runs/2026-08-28-atari-57/reviews/r1-review.md (1 blocking [static-viewer: live zoom/pan wiring on fixed arena], 14 non-blocking)
2026-08-28T20:00:46Z heartbeat phase=30
2026-08-28T21:28:20Z 30 fixer returned round=1: runs/2026-08-28-atari-57/reviews/r1-fixes.md — fixed B1,N1,N2,N7,N12; declined N4-N6,N8-N11,N13,N14; N3 NEEDS-DESIGN; main@c8498ce ci run 33210994977 success; note: fixer used git-data API (HTTPS push 401s in sandbox), no force-push
2026-08-28T21:28:20Z progress phase=30 marker=r1-fixes.md
2026-08-28T21:28:20Z heartbeat phase=30
2026-08-28T21:29:31Z 30 note: coordinator pushes to coworld-builder now also 401 over git-HTTPS; replaying commits via git-data API (/tmp/gitdata_push.py), non-forced ref updates only
2026-08-28T21:29:31Z 30 judge dispatched round=1 (repo main@c8498ce481637d6acdac33192bf688a5d9f55ee5, fresh context, no fixes ledger)
2026-08-28T21:41:44Z 30 judge returned round=1: runs/2026-08-28-atari-57/reviews/r1-verdict.md blocking=0 (markers agree) — review loop complete in 1 round
2026-08-28T21:41:44Z progress phase=30 marker=r1-verdict.md
2026-08-28T21:41:44Z 30 -> 40 phase transition: STATE.phase=40 written before release dispatch
2026-08-28T21:41:44Z heartbeat phase=40
2026-08-28T21:42:05Z 40 builder dispatched for release (version 0.1.0, policies from tools/ci/policies.json)
2026-08-28T21:51:11Z 40 release dispatch 1/3: version=0.1.0 run=33213738190 step_failed=null — ok:true canonical:true certify.ok:true liveness skipped-static secret_put:true; 4 policies v1, champion2 player_id=ply_bac48eb1-662e-44f8-973d-f3e016dccf5d; cow_id=cow_4b06234f-97d8-4b65-8553-e2f967e89d8c
2026-08-28T21:51:11Z progress phase=40 marker=33213738190
2026-08-28T21:51:11Z 40 -> 50 phase transition: STATE.phase=50 written
2026-08-28T21:51:11Z heartbeat phase=50
2026-08-28T21:52:32Z 50 seed HTTP200 lseed_96772792-78d7-44ee-9317-48332324ea9a league=league_942b4588-00ce-4b37-b5ae-9f1254d97db4
2026-08-28T21:52:32Z 50 division HTTP200 div_6a44a425-829a-41ae-926f-a0139e8b95d3; settings HTTP200 (round_robin, filler_policy, elo mean, interval 15m)
2026-08-28T21:52:32Z progress phase=50 marker=league_942b4588-00ce-4b37-b5ae-9f1254d97db4
2026-08-28T21:52:32Z heartbeat phase=50
2026-08-28T21:54:59Z 50 champion1 submit run=33214447307 ok:true (atari-57-highroller:v1, daveey)
2026-08-28T21:54:59Z 50 champion2 submit run=33214495726 ok:true (atari-57-onecredit:v1, daveey-1 — policy-versions row confirms player_name=daveey-1)
2026-08-28T21:54:59Z 50 fillers HTTP200: arcader=44a28876-eba6-4ec8-bcf6-6cfe647d9fc7 hoover=d0712eac-62b0-4f34-ad30-b562afebc3a3 (neither champion)
2026-08-28T21:54:59Z 50 unpause HTTP200; trigger HTTP200; rounds: r1 failed (Temporal RoundWorkflow failed before settling — pre-trigger race), r2 pending with both champions in entrant_attributions
2026-08-28T21:54:59Z progress phase=50 marker=33214495726
2026-08-28T21:54:59Z 50 -> 60 phase transition: STATE.phase=60 written
2026-08-28T21:54:59Z heartbeat phase=60
2026-08-28T21:55:24Z 60 verifier dispatched (league league_942b4588 round 2 pending at dispatch; 75-min poll bound)
2026-08-28T22:02:00Z heartbeat phase=60
2026-08-28T22:02:00Z 60 poll: round 2 completed at 21:59:28Z (round 1 failed, not counted); waiting for round 3
2026-08-28T22:18:54Z heartbeat phase=60
2026-08-28T22:18:54Z 60 rounds 2+3 completed; ereq_c6f8d48c completed; replay ok (protocol atari-57/v1, complete/full_time, 0 fallbacks); log CLEAN; static iframe ready:true; viewer-check run 33216261052 dispatched
2026-08-28T22:23:16Z 60 VERIFY.md written: 8/8 TRUE (rounds 2+3; daveey #1 / daveey-1 #2; ereq_c6f8d48c; replay 820b851b protocol atari-57/v1 complete/full_time 38 llm 0 fallback; log CLEAN; static iframe ready:true; cert liveness skipped-static; viewer-check 33216261052 loaded:true clocks 2:00/1:00/0:00)
2026-08-28T22:23:16Z heartbeat phase=60
2026-08-28T22:24:14Z 60 verifier returned: VERIFY.md 8/8 TRUE — rounds 2+3 completed, leaderboard daveey 1030.5 / daveey-1 969.5, replay reason=complete 0 fallbacks, log CLEAN, iframe static (?v=2#replay= shape), viewer-check 33216261052 loaded:true clocks advance; observation: feed_lines selector mismatch (instrumentation, non-blocking)
2026-08-28T22:24:14Z progress phase=60 marker=round_4441a16c
2026-08-28T22:24:14Z 60 judge dispatched to adjudicate VERIFY.md
2026-08-28T22:33:07Z 60 judge returned: verify-verdict.md blocking=0 (markers agree) — all 8 checks adjudicated TRUE, deviations 4+6 accepted with re-fetched evidence
2026-08-28T22:33:07Z 60 -> 70 phase transition: STATE.phase=70 written
2026-08-28T22:33:07Z heartbeat phase=70
2026-08-28T22:34:18Z 70 announce attempted_at written before POST (body 1776 chars)
2026-08-28T22:34:42Z 70 announce msg=1543026008503099424 (HTTP200, flags=4, embeds=0)
2026-08-28T22:34:42Z progress phase=70 marker=1543026008503099424
2026-08-28T22:34:42Z 70 -> 75 phase transition: STATE.phase=75 written
2026-08-28T22:34:42Z heartbeat phase=75
2026-08-28T22:35:46Z 75 atlas continent=paintlands (zero-sum arcade score-attack; precedent atari-cabinet 2026-08-26 also paintlands)
2026-08-28T22:35:46Z 75 atlas dispatch=33217399986 region=paintlands at=202,270 clearance=39.5
2026-08-28T22:40:18Z 75 atlas dispatch 1 (33217399986) failed: build unplaced-leagues (52 slugs); fix per step 8: mirror queued metta#20723's 50 extra_cities and place minigrid+procgen too
2026-08-28T22:40:18Z 75 atlas continent REVISED to simulations (queued #20723 re-places atari-cabinet in simulations — Atari-57 is the borrowed RL benchmark suite; consistency over my earlier paintlands call)
2026-08-28T22:40:18Z 75 atlas placed-for-others: 50 mirrored from metta#20723 (atari-cabinet..walker-waterworld incl citysim+gnomic) + minigrid=(578,289,simulations,cl22.9) + procgen=(521,310,simulations,cl23.4)
2026-08-28T22:40:18Z 75 atlas dispatch=33217674106 region=simulations at=497,277 clearance=22.9 extra_cities=52
2026-08-28T22:42:37Z 75 atlas pr=https://github.com/Metta-AI/metta/pull/20742 status=pr_open
2026-08-28T22:42:37Z progress phase=75 marker=https://github.com/Metta-AI/metta/pull/20742
2026-08-28T22:42:37Z 75 -> 80 phase transition: STATE.phase=80 written
2026-08-28T22:42:37Z heartbeat phase=80
