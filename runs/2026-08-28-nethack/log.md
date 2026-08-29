# 2026-08-28-nethack — log

2026-08-28T23:02:35Z 00 claim comment posted on idea 1217748519904179 (story 1217965166952026)
2026-08-28T23:03:00Z 00 claim re-check after 20s: no competing claim comment — claim stands
2026-08-28T23:03:32Z 00 claim 2026-08-28-nethack idea=1217748519904179 slug=nethack
2026-08-28T23:03:32Z 00 run task 1217965068474377 created in Running; heartbeat_at custom field stamped; 9 phase subtasks created
2026-08-28T23:03:32Z 00 -> 10 phase transition; session=30d37c05
2026-08-28T23:07:00Z 10 starter=Metta-AI/coworld-ctf — single-agent turn-driven grid dungeon crawl; NetHack/MiniHack task family re-implemented as own deterministic seeded Nim sim (not a bit-exact NLE port: NLE is a C/Python package that cannot compile to the wasm static viewer); precedent: minigrid, procgen, atari-57, vizdoom-deathmatch all coworld-ctf
2026-08-28T23:08:30Z 10 designer dispatched (round 1) thread=sthr_0155y4p2VwZqG6dxZ6oPsK6Z output=runs/2026-08-28-nethack/design.md
2026-08-28T23:28:31Z 10 designer returned r1: design.md (2201 lines) collected from file
2026-08-28T23:28:31Z 10 checklist: starter-named+reason=x num_agents-fixed(1,both-variants+cert+SEATS=1)=x resolution-order-numbered(8-step-turn,11-step-tick)=x scoring-formula+sign+rank(scores[0],higher-better,never-negative,depth-lexicographic)=x end-conditions+reason-enum(complete|deadline|fault)+deadline-case=x observation-visible/hidden(lit-room/radius-1 rule)=x reply-schema-caps+rune-trunc(directives.nim:61-68)=x both-policies-env-switched(PLAYER_PROMPT vs PLAYER_SCRIPTED=delver|bumbler)+baseline-algos=x single-seat-one-call/turn<=110,worst-645s<660s-stop<720s=x degrade-never-hang(retry-once->fallback,budget-guard)=x two-name-spaces(Alpha-the-Digger alias)=x viewer-static-wasm+hook+readouts(terminal-panel,depth-ladder,death-feed)+360px=x viewer-four-files-one-starter(coworld-ctf)+loaded/error-attrs(:1509-1516)=x chrome-provenance-byte-for-byte(sha256-verified-against-starter:match)+appended-block+removal-list+zoom(viewpanel-KEPT,48x18>frame)=x transport-rules(band/hudscale,endcard-var(--band),beats-clickable+CSS-10-kinds)=x replay-self-sufficient(seed,config,names,per-tick)=x packaging(compose+manifest-2-variants+cert-fixture+docs-readme+3pages+protocols-player+global)=x tests(50 incl 500-seed-connectivity,bounded-orders,e2e-replay,strict-utf8,viewer-smoke-EXECUTED)=x out-of-scope-nonempty(8)=x — ACCEPTED round 1
2026-08-28T23:28:31Z 10 -> 20 phase transition: STATE.phase=20 written before builder dispatch
2026-08-28T23:28:31Z progress phase=10 marker=runs/2026-08-28-nethack/design.md
2026-08-28T23:29:37Z 20 repo created: https://github.com/Metta-AI/cogame-nethack (public)
2026-08-28T23:29:37Z 20 propagate-secrets.yml run 33220582173 success; gh secret list confirms SOFTMAX_TOKEN + ANTHROPIC_API_KEY on cogame-nethack
2026-08-28T23:29:37Z heartbeat phase=20
2026-08-28T23:30:30Z 20 builder dispatched (round 1) thread=sthr_01DSmKdDQMnT6UJjfFPbSPp1 target=ci.yml green on main of Metta-AI/cogame-nethack
2026-08-29T01:12:25Z 20 builder returned r1: CI green run 33225421389 sha c484a248b43f9ff6fdc9208d748c58abcea64d74 (jobs test/docker-smoke/wasm-viewer all success), 0/3 retries used
2026-08-29T01:12:25Z 20 coordinator verified: placeholder-grep clean; 3 workflows active; release inputs version|policies|put_secret|skip_certify + release-result + per-policy player field; submit inputs player_id|policy|league_id + submit-result; exec bits 100755 on docker_smoke.sh/build_replay_viewer.sh; manifest num_agents=1 both variants+cert, bundle=static-replay-viewer, protocols player+global, docs readme+3 pages; chrome_common.js sha256 match; policies.json 4 entries, champion2 player=ply_bac48eb1
2026-08-29T01:12:25Z 20 rails decision: builder's measured balance corrections accepted (to-hit 15, startHp 16, regenTicks 12, monsters min(10,2+depth), packs from DL2 — delver died 30/30 seeds under note constants; parameter tuning is a rail). Deviations for reviewer: turn-ends-on-empty-queue (divergence 15), test-29 eats-clause substitution, unshipped wasm_replay_smoke.cjs/renderer_fixture/shards/league_replayer/labels.nim, camera fit-shrink instead of clamp+pan
2026-08-29T01:12:25Z 20 note: builder reports git-push to coworld repos fails in sandbox (Invalid username or token); pushed via Git Data API — candidate LEARNINGS entry at phase 80
2026-08-29T01:12:25Z 20 -> 30 phase transition: STATE.phase=30 review_round=1 written before reviewer dispatch
2026-08-29T01:12:25Z progress phase=20 marker=ci-run-33225421389
2026-08-29T01:15:25Z 30 r1 reviewer dispatched thread=sthr_012i5VtkRYPMVTWs83FrUpxt output=runs/2026-08-28-nethack/reviews/r1-review.md sha=c484a248 (shared checkout /workspace/cogame-nethack)
2026-08-29T01:15:25Z heartbeat phase=30
2026-08-29T01:36:19Z 30 r1 reviewer returned: r1-review.md (975 lines, 22 findings F1-F22, reviewer says 0 blocking; F17 game.docs type=uri-vs-text and F5 camera-clamp flagged with stricter alternative readings)
2026-08-29T01:36:19Z 30 r1 fixer dispatched thread=sthr_01DwjzepRAaPMByAfmzsPyUm output=runs/2026-08-28-nethack/reviews/r1-fixes.md
2026-08-29T01:36:19Z heartbeat phase=30
2026-08-29T03:18:08Z 30 r1 fixer returned: r1-fixes.md — 13 findings fixed (one commit each), 8 refuted/accepted-rails with evidence (F17 uri precedent: coworld-ctf/moba/factorio all ship uri); final sha ae95996519e51b70346499240e0845ad013b3fb8, CI green run 33230652674, SEAT-COUNT FAIL grep=0; duplicate no-op commit range a362c6a..4a8c81e from stale-ref replay, documented in-history d570e64, not force-cleaned
2026-08-29T03:18:08Z 30 coordinator verified: run 33230652674 success at ae95996 (test/docker-smoke/wasm-viewer)
2026-08-29T03:18:08Z 30 r1 judge dispatched (fresh context) thread=sthr_01LQX2mgsG9RUFDYePHW4BP7 output=runs/2026-08-28-nethack/reviews/r1-verdict.md sha=ae95996
2026-08-29T03:18:08Z heartbeat phase=30
2026-08-29T03:32:40Z 30 r1 judge returned: r1-verdict.md blocking:0/BLOCKING:0 (well-formed, both markers agree) — zero blocking findings, loop exits round 1
2026-08-29T03:32:40Z 30 -> 40 phase transition: STATE.phase=40 written before release dispatch
2026-08-29T03:32:40Z progress phase=30 marker=r1-verdict.md
2026-08-29T03:33:35Z 40 builder dispatched (release) thread=sthr_01PP4bu2pRp3WrQcjiyKUwdx target=coworld-release.yml canonical+certified, policies from tools/ci/policies.json, start version 0.1.0
2026-08-29T03:33:35Z heartbeat phase=40
2026-08-29T03:44:17Z 40 dispatch 1: version=0.1.0 run=33231707696 step_failed="Build the Coworld manifest" (pydantic: game.image extra_forbidden; player[0].type=policy not in enum) — builder fixed manifest, validated locally with coworld==0.1.43 before re-dispatch (commit 3e37c93)
2026-08-29T03:44:17Z 40 dispatch 2: version=0.1.1 run=33231811404 success — ok:true canonical:true certify.ok:true liveness-skipped-static secret_put:true; 4 policy labels distinct, champion2 player_id=ply_bac48eb1; release-result.json persisted to run dir
2026-08-29T03:44:17Z 40 coordinator verified artifact field-by-field; cow_id=cow_1346325e-7184-4c94-9fbc-d3aeb750889c manifest_sha=sha256:3452373e...
2026-08-29T03:44:17Z 40 note for LEARNINGS(80): design.md test 39 (CI runs installed coworld validate_upload_manifest) was never wired into ci.yml — exactly the gap that let 2 schema errors reach a release dispatch; candidate templates/ci.yml improvement
2026-08-29T03:44:17Z 40 -> 50 phase transition: STATE.phase=50 written
2026-08-29T03:44:17Z progress phase=40 marker=release-run-33231811404
2026-08-29T03:47:48Z 50 seed 200: lseed_7a906e14 league_462e0339-0d14-4f35-8bb2-ad882f4b0224
2026-08-29T03:47:48Z 50 division 200: div_03513e99-65b4-4fe1-8ce0-ae8adb8728bb (Competition, level 1)
2026-08-29T03:47:48Z 50 settings 200: round_robin/filler_policy, elo k=32 mean, round_interval=15m
2026-08-29T03:47:48Z 50 champion1 submit: run 33232191252 ok:true sub_e0b369da (daveey, nethack-divemaster:v1)
2026-08-29T03:47:48Z 50 champion2 submit: run 33232215535 ok:true (daveey-1, nethack-loremaster:v1)
2026-08-29T03:47:48Z 50 policy-version uuids resolved: divemaster=20a7c701 loremaster=dea3d12b(player_name=daveey-1 confirmed) delver=86835dea bumbler=5c2bc078
2026-08-29T03:47:48Z 50 fillers 200: delver+bumbler registered, neither champion
2026-08-29T03:47:48Z 50 unpause 200 (paused:false); trigger-round 200 (ladder workflow)
2026-08-29T03:47:48Z 50 round 1 pending, entrant_attributions = both champions (ply_44ae9048+20a7c701, ply_bac48eb1+dea3d12b)
2026-08-29T03:47:48Z 50 -> 60 phase transition: STATE.phase=60 written
2026-08-29T03:47:48Z progress phase=50 marker=league_462e0339+round_1abe8f06
2026-08-29T03:49:06Z 60 verifier dispatched thread=sthr_01PoyKxs6sPLLnZmrp7JPtez output=runs/2026-08-28-nethack/VERIFY.md (8 checks, 75-min round bound, heartbeats delegated during poll)
2026-08-29T03:49:22Z heartbeat phase=60
2026-08-29T03:49:22Z 60 poll: rounds=[1:pending] completed=0 leaderboard=null (no ranked players yet)
2026-08-29T03:54:34Z heartbeat phase=60
2026-08-29T03:54:34Z 60 poll: round 1 completed (round_1abe8f06), completed=1 — waiting for round 2
2026-08-29T04:00:35Z heartbeat phase=60
2026-08-29T04:00:35Z 60 poll: completed=1 (round 1); round 2 not yet created (page says next round ~9m)
2026-08-29T04:05:42Z heartbeat phase=60
2026-08-29T04:05:42Z 60 poll: round 2 created, status=pending; completed=1
2026-08-29T04:10:38Z heartbeat phase=60
2026-08-29T04:10:38Z 60 poll: rounds 1 and 2 both completed — proceeding to full evidence capture
2026-08-29T04:13:31Z heartbeat phase=60
2026-08-29T04:13:31Z 60 check 1 TRUE: rounds 1 (round_1abe8f06) + 2 (round_aadd7254) both status=completed, error=null, both after fillers set 03:47:48Z; 0 failed/discarded
2026-08-29T04:13:31Z 60 check 2 TRUE: leaderboard daveey-1 rank1 nethack-loremaster:v1 rounds_played=2, daveey rank2 nethack-divemaster:v1 rounds_played=2; no filler rows
2026-08-29T04:13:31Z 60 check 3 TRUE: latest completed round 2 -> ereq_d38c6af7 (daveey-1) + ereq_c39ff0a2 (daveey) both completed with non-null replay_url (single-seat game: one champion per episode request; round_config seats both)
2026-08-29T04:13:31Z 60 check 4 TRUE-on-SPEC: replay bytes are binary COWLDNET; tools/replay_summary.py expansion is strict-UTF-8 JSON, protocol nethack/v1, reason=complete (endRule escaped/turnCap), 27+55 plans all source=llm, fallbackTurns=0 — BUT design.md's stricter self-declared substitute (depthReached>=2 and >=1 down verb) NOT met: depthReached=1 in all 4 episodes of both rounds
2026-08-29T04:13:31Z 60 check 5 TRUE: hosted logs for both round-2 episode requests decoded from byte-string reprs -> CLEAN (0 matches of falling back|LLM provider is unavailable|cut off at max_tokens|rejected)
2026-08-29T04:13:31Z 60 check 7 TRUE: committed release-result.json certify.replay_liveness contains 'Replay liveness: skipped (static replay bundle declared'
2026-08-29T04:16:10Z heartbeat phase=60
2026-08-29T04:16:10Z 60 check 8 TRUE: viewer-check run 33233338285 success — loaded:true ms:2285, data_replay_loaded=true, three scrub clocks differ (T:0/T:9/T:17); artifact committed to runs/2026-08-28-nethack/viewer-check/
2026-08-29T04:29:42Z heartbeat phase=60
2026-08-29T04:29:42Z 60 check 6 SPLIT: static iframe src TRUE via POST /coworlds/replays/session (raw-HTML grep finds no iframe = client-rendered; /coworlds row no longer carries a featured_match key at all) -> .../v2/coworlds/replays/static/cow_1346325e.../sha256%3A3452373e.../index.html?v=2#replay=<s3>, ready:true, no /client/replay. FEATURED MATCH FALSE: state.playlist=[] and page renders 'No featured match yet' at 04:11:48Z and 04:21:05Z; cross-check crafter (r1) and procgen (r32, 3 ranked players) identical — platform behaviour for every canonical coworld declaring num_agents==1; multi-seat coworlds (bullwhip/parley/babel/moba/minigrid) all have playlist len 1
2026-08-29T04:29:42Z 60 round 3 (round_b7f16922) completed 04:20:42Z — checks 3/4/5/6/8 re-fetched against round 3 as the latest completed round; 3 completed rounds total, 0 failed/discarded
2026-08-29T04:29:42Z 60 VERIFY.md written: 6 TRUE, item 4 TRUE-on-SPEC with sub-finding (design.md's depthReached>=2 and >=1 down unmet in 6/6 episodes; depthReached=1 everywhere), item 6 half-false (featured match absent)
2026-08-29T04:29:42Z 60 viewer-check dispatches this session: 33233650158 (primary, round-3 replay 3466ad2b, loaded:true ms=5499, scrub T:0/T:9/T:17) and 33233338285 (round-2 replay 3db7fc96, loaded:true ms=2285, scrub T:0/T:9/T:17); both artifacts committed under runs/2026-08-28-nethack/viewer-check/
2026-08-29T04:32:48Z 60 verifier returned: VERIFY.md (829 lines) — checks 1,2,3,5,7,8 TRUE; check 6 split (static path TRUE, featured-match recorded FALSE on the strict playlist reading); check 4 TRUE-on-SPEC with sub-finding (design.md's own substitute depthReached>=2 + down verb unmet 6/6 episodes)
2026-08-29T04:32:48Z 60 coordinator adjudication check 6: TRUE by procgen precedent (2026-08-28-procgen VERIFY.md check 6 — same SSR shape, playlist:[] platform-wide for single-seat, featured pool at state.pool.replays non-empty = featured match present; nethack pool holds round-2 and round-3 episodes). Recorded, judge to confirm.
2026-08-29T04:32:48Z 60 open item for judge: check 4 SPEC wording 'doing the thing the game is about' vs design-note substitute (depth>=2, down verb) — champions never descended in 6 episodes; loremaster once ended by taking < up-stairs (endRule escaped)
2026-08-29T04:32:48Z 60 judge dispatched (fresh context) thread=pending output=runs/2026-08-28-nethack/verify-verdict.md
2026-08-29T04:33:58Z 60 judge dispatched (fresh context) thread=sthr_01VPGwiqNwhsQzJZMH3s7ENe output=runs/2026-08-28-nethack/verify-verdict.md — rulings requested on check 6 (procgen precedent) and check 4 (design-note depth substitute)
2026-08-29T04:33:58Z heartbeat phase=60
2026-08-29T04:39:16Z 60 judge returned: verify-verdict.md blocking:0/BLOCKING:0 — all 8 SPEC items confirmed; check 6 TRUE by precedent (single-seat playlist gap recorded as SPEC-wording issue); check 4 TRUE on SPEC with MATERIAL non-blocking balance finding: no champion has ever descended (depthReached=1 in 6/6, zero down verbs, one episode ended by ascending) — settle-by: prompt/balance tuning + one hosted episode at depth>=2; assigned to close/LEARNINGS for human steering
2026-08-29T04:39:16Z 60 -> 70 phase transition: STATE.phase=70 written
2026-08-29T04:39:16Z progress phase=60 marker=verify-verdict.md-blocking-0
2026-08-29T04:40:14Z 70 announce.attempted_at written and pushed BEFORE the POST (body 1789 bytes, flags=4)
