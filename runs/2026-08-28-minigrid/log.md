# 2026-08-28-minigrid — log

2026-08-28T18:38:13Z 00 claim comment posted on idea 1217748613470987
2026-08-28T18:39:07Z 00 claim 2026-08-28-minigrid idea=1217748613470987 slug=minigrid
2026-08-28T18:39:37Z 00 run task 1217960652523276 created in Running with 9 phase subtasks; heartbeat_at set session=65d65a2f
2026-08-28T18:39:37Z heartbeat phase=00
2026-08-28T18:41:30Z 10 starter=Metta-AI/coworld-ctf — single-agent real-time grid tick loop; MiniGrid/BabyAI/XLand task family re-implemented as own deterministic Nim sim (not a bit-exact port; no external engine); precedent: procgen, atari-57, sumo-traffic-signals all coworld-ctf
2026-08-28T18:43:40Z 10 designer dispatched (round 1) thread=sthr_017LUgvzi63w6CzkhdL4GR62 output=runs/2026-08-28-minigrid/design.md
2026-08-28T19:04:56Z 10 designer returned r1: design.md (1971 lines) collected from file
2026-08-28T19:04:56Z 10 checklist: starter-named=x num_agents-fixed(1,all-variants+cert+SEATS)=x resolution-order-numbered=x scoring-formula+sign+rank(scores[0] lexicographic)=x end-conditions+reason-enum(complete|deadline|fault)=x observation-visible/hidden(7x7 occlusion algorithm)=x reply-schema-caps+rune-trunc=x both-policies-env-switched+baseline-algos(scout,bumper)=x single-seat-call-budget<=110+worst-644s<720s=x degrade-never-hang=x two-name-spaces=x viewer-static-wasm+hook+readouts+360px=x viewer-four-files-one-starter(coworld-ctf)+loaded/error-attrs=x chrome-provenance+removed-list+zoom-dropped=x transport-rules=x replay-self-sufficient=x packaging(compose+manifest+docs+protocols-both)=x tests(45 incl sim,bounded-orders,e2e-replay,utf8,viewer-smoke-executed)=x out-of-scope-nonempty=x — ACCEPTED round 1 (chrome_common sha256 verified against starter: match)
2026-08-28T19:04:56Z progress phase=10 marker=design.md written and accepted round 1
2026-08-28T19:04:56Z 10 -> 20 phase transition: STATE.phase=20 written before builder dispatch
2026-08-28T19:04:56Z heartbeat phase=20
2026-08-28T19:06:01Z 20 repo created public: https://github.com/Metta-AI/cogame-minigrid
2026-08-28T19:06:01Z 20 propagate-secrets run 33202312365 success; gh secret list confirms SOFTMAX_TOKEN + ANTHROPIC_API_KEY on cogame-minigrid
2026-08-28T19:06:58Z 20 builder dispatched (round 1) thread=sthr_01UniMBZ7v9N3ro51CH7ypyh repo=Metta-AI/cogame-minigrid
2026-08-28T19:06:58Z heartbeat phase=20
2026-08-28T20:49:37Z 20 builder returned r1: ci.yml green on main run=33209437659 sha=d8f9e7c2 (verified: all 3 jobs success, workflows active, hooks 100755, scaffold files present); 9 documented divergences incl fresh-written sim/server in starter shape, derived broadcast page, CTF_WIRE alias
2026-08-28T20:49:37Z progress phase=20 marker=ci-run-33209437659-green
2026-08-28T20:49:37Z 20 -> 30 phase transition: STATE.phase=30 review_round=1 written before reviewer dispatch
2026-08-28T20:49:37Z heartbeat phase=30
2026-08-28T20:50:26Z 30 reviewer dispatched (round 1) thread=sthr_019HF8KgKSi4YyFHNEW5yZaL sha=d8f9e7c2 output=runs/2026-08-28-minigrid/reviews/r1-review.md
2026-08-28T21:12:16Z 30 reviewer returned r1: r1-review.md (706 lines) collected from file — 1 blocking-candidate (B1 manifest game.runnable shape, coworld build KeyError reproduced), 18 non-blocking, 3 minor
2026-08-28T21:12:16Z progress phase=30 marker=r1-review.md
2026-08-28T21:12:16Z heartbeat phase=30
2026-08-28T21:12:49Z 30 fixer dispatched (round 1) thread=sthr_016yFqiEx5TKF8fuGv1k3NjJ input=r1-review.md output=runs/2026-08-28-minigrid/reviews/r1-fixes.md
2026-08-28T21:47:34Z 30 fixer returned r1: r1-fixes.md collected from file — B1 fixed (manifest game.runnable shape, reproduced before/after vs coworld==0.1.43), N10/N1/N17 + 9 more fixed, 17 commits, 2 NEEDS-DESIGN, 6 disputed; ci green run=33213509695 sha=b19bc085
2026-08-28T21:47:34Z progress phase=30 marker=r1-fixes.md
2026-08-28T21:47:34Z heartbeat phase=30
2026-08-28T21:49:59Z 30 judge dispatched (round 1, fresh context) thread=sthr_01H7FkfnUVXA3PZ7rQUV7etu sha=b19bc085 output=runs/2026-08-28-minigrid/reviews/r1-verdict.md
2026-08-28T21:49:59Z 30 note: coworld-builder push failing 401 on github.com git endpoints since ~21:45Z (api.github.com fine); commits queued locally, retrying with backoff
2026-08-28T22:00:07Z 30 judge returned r1: r1-verdict.md collected from file — blocking: 0 / BLOCKING: 0 (well-formed, both markers agree); B1 refuted-as-fixed at b19bc085; independent checklist pass all 15 items PASS
2026-08-28T22:00:07Z progress phase=30 marker=r1-verdict.md
2026-08-28T22:00:07Z 30 -> 40 phase transition: STATE.phase=40 written before release dispatch
2026-08-28T22:00:07Z heartbeat phase=40
2026-08-28T22:01:15Z 40 builder dispatched (release) thread=sthr_01UYLnKxtvE1ScC5cjyZAx4F version-plan=0.1.0 output=runs/2026-08-28-minigrid/release-result.json
2026-08-28T22:09:39Z 40 builder returned: release 0.1.0 dispatch 1 run=33215083433 success — ok:true canonical:true certify.ok:true liveness-skipped-static secret_put:true; 4 policies v1, champion2 player_id=ply_bac48eb1; verified from runs/2026-08-28-minigrid/release-result.json
2026-08-28T22:09:39Z progress phase=40 marker=release-run-33215083433
2026-08-28T22:09:39Z 40 -> 50 phase transition: STATE.phase=50 written
2026-08-28T22:09:39Z heartbeat phase=50
2026-08-28T22:10:45Z 50 league seeded: lseed_64e3c57d league_id=league_78d5b417-52a0-4459-8fd6-3b9aeacfe1ca (POST coworld-league-seeds 200)
2026-08-28T22:10:45Z 50 division created: div_721f571a-ece7-4ed9-8b1c-15eb2cd072be (PUT divisions 200); settings posted (round_robin, filler_policy, elo, 15min) 200
2026-08-28T22:13:04Z 50 champion1 submitted: run 33215736275 ok=true sub_aee3b135 policy=minigrid-cartographer:v1 player=daveey
2026-08-28T22:13:04Z 50 champion2 submitted: run 33215777481 ok=true policy=minigrid-missionfirst:v1 player=daveey-1 (uuid 8e8fff3c row player_name=daveey-1 confirmed)
2026-08-28T22:13:04Z 50 fillers registered BEFORE trigger: scout=dd96f37f bumper=bc769311 (POST filler-policies 200, response lists exactly these two)
2026-08-28T22:13:04Z 50 unpaused (rounds_paused_at:null) + trigger-round dispatched; round 1 status=pending, entrants=both champions
2026-08-28T22:13:04Z progress phase=50 marker=league_78d5b417-52a0-4459-8fd6-3b9aeacfe1ca
2026-08-28T22:13:04Z 50 -> 60 phase transition: STATE.phase=60 written
2026-08-28T22:13:04Z heartbeat phase=60
2026-08-28T22:14:08Z 60 verifier dispatched thread=sthr_01283UWZvAaNCgkBwGpPsvyT output=runs/2026-08-28-minigrid/VERIFY.md + viewer-check/
2026-08-28T22:59:52Z 60 verifier returned: VERIFY.md (818 lines) — checks 1,2,3,4,7 TRUE; 5,6,8 FALSE. 3 completed rounds; both champions ranked; replays healthy (cartographer 46/46 llm, 2 tasks solved)
2026-08-28T22:59:52Z progress phase=60 marker=VERIFY.md+viewer-check-33217607488
2026-08-28T22:59:52Z 60 check5 FALSE: 1 fallback turn (2.8%) round-3 champ2 — Bedrock p90 5-6s vs attempt1Ms 6000; NOT platform-wide (procgen clean); fix=raise deadlines client-side + fix parse_error mislabel
2026-08-28T22:59:52Z 60 check6 FALSE: featured match absent — STRUCTURAL for single-participant episodes (playlist [] while pool has replays; procgen same; every >=2-participant coworld has one). RAILS DECISION: num_agents 1 -> 4 isolated lanes, precedent atari-57 design line 64-69 (same starter, same shape)
2026-08-28T22:59:52Z 60 check8 FALSE: viewer loads+advances but 50%==100% — scrubber click-to-seek mis-scaled + clock desync; also feed_lines=0 (say never drawn), pip caption smear, gutter overlays, 3 sprite 404s
2026-08-28T22:59:52Z 60 decision: one combined fix round — designer addendum (4 lanes) -> builder -> judge r2 verdict -> release 0.1.1 -> re-verify; phase stays 60, attempt 1 of 3 per failing check
2026-08-28T22:59:52Z heartbeat phase=60
2026-08-28T23:00:53Z 60 designer addendum requested (same thread sthr_017LUgvzi63w6CzkhdL4GR62): 4 isolated lanes, deadline ladder re-derived, viewer defect fixes — appended to design.md as Addendum v2
2026-08-28T23:20:19Z 60 addendum v2 returned and ACCEPTED: design.md now 2851 lines — num_agents=4 isolated lanes (same-seed, synchronized phases), ladder 11000/6000/17000/11000 (worst 631s<660s<720s), seek/clock contract, feed fix, quad layout + gutters, sprite/protocol pins, truthful fallback causes, GameVersion 2, 13 new tests
2026-08-28T23:20:19Z progress phase=60 marker=design.md-addendum-v2
2026-08-28T23:20:19Z 60 builder v2 dispatch next: implement addendum, CI green, then judge r2, release 0.1.1
2026-08-28T23:21:17Z 60 builder v2 dispatched thread=sthr_01KDUULfYUsdx3KEpWZKqw3X target=addendum-v2 implementation, ci green, no release dispatch
2026-08-28T23:21:17Z heartbeat phase=60
2026-08-28T23:22:54Z 60 INCIDENT: addendum v2 lost — coordinator's 'git reset --hard origin/main' (used as contents-API sync) ran after a failed design.md publish (jq argv limit) and reverted the working tree before the python retry read it; commit 7e5464a is empty. Builder v2 correctly refused to build from pointers. Fix: designer re-emits; publish will verify remote blob sha + line count BEFORE any reset; resets replaced by per-file checkout going forward
2026-08-28T23:24:42Z 60 addendum v2 re-emitted and persisted: design.md 2851 lines, remote blob 878f41b8 verified byte-identical after round-trip fetch; durable copy at /tmp/design-with-addendum-v2.md
2026-08-28T23:24:42Z progress phase=60 marker=design.md-addendum-v2-persisted-blob-878f41b8
2026-08-28T23:24:42Z 60 builder v2 resumed (same thread sthr_01KDUULfYUsdx3KEpWZKqw3X) against the persisted addendum
2026-08-28T23:24:42Z heartbeat phase=60
2026-08-29T00:51:40Z 60 builder v2 returned: ci green run=33224429999 sha=32555dec (verified) — seats=4 smoke, scrub readouts pairwise distinct, feed_lines=9, 0 sprite 404s/unknown types; 7 documented divergences; root causes: killfeed id mismatch, u16 label overflow (type-34), clock-caption tick
2026-08-29T00:51:40Z progress phase=60 marker=ci-run-33224429999-green-v2
2026-08-29T00:51:40Z 60 rails: builder told to fix stale 'eleven turns' in shared system prompt + policies.json (one commit) before judge r2
2026-08-29T00:51:40Z heartbeat phase=60
2026-08-29T01:07:08Z 60 builder prompt re-pin returned: sha=8a78a6bf run=33224940969 green (verified) — six-turn wording in llm.nim only; policies.json unchanged deliberately (champions carry no stale count)
2026-08-29T01:07:08Z progress phase=60 marker=ci-run-33224940969-green
2026-08-29T01:07:08Z 60 judge r2 dispatched (fresh context) thread=sthr_01ARBUXDhAcrv3uuz3CSvc1Y sha=8a78a6bf output=runs/2026-08-28-minigrid/reviews/r2-verdict.md
2026-08-29T01:07:08Z heartbeat phase=60
2026-08-29T01:18:39Z 60 judge r2 returned: r2-verdict.md blocking:0/BLOCKING:0 (well-formed) — all 15 items + all addendum commitments PASS at 8a78a6bf; full independent pass (no r2-review existed); 4 non-blocking observations
2026-08-29T01:18:39Z progress phase=60 marker=r2-verdict.md
2026-08-29T01:18:39Z 60 release 0.1.1 dispatch next (builder thread reused)
2026-08-29T01:19:12Z 60 release 0.1.1 dispatched to builder thread sthr_01KDUULfYUsdx3KEpWZKqw3X (v2 at 8a78a6bf, judge r2 clean)
2026-08-29T01:19:12Z heartbeat phase=60
2026-08-29T01:29:13Z 60 release 0.1.1 dispatch 1 run=33226095645 success — canonical cow_753b4d23, certify 10/10, secret_put; 4 policies minted v2 (champion2 owned by daveey-1); verified from release-result.json
2026-08-29T01:29:13Z progress phase=60 marker=release-run-33226095645
2026-08-29T01:29:13Z 60 league v2 rollover next: submit v2 champions, replace fillers with v2 UUIDs BEFORE next trigger (v1 binaries incompatible with v2 wire), then trigger and re-verify
2026-08-29T01:34:32Z 60 league v2 rollover: paused 01:29, champions v2 submitted ok (runs 33226543826, 33226560317), fillers REPLACED with v2 pair (verified live list = scout:2,bumper:2), unpaused, triggered — round 14 pending but snapshotted missionfirst v1 (placement async); next round picks up v2
2026-08-29T01:34:32Z progress phase=60 marker=fillers-v2-1f17a736+d984c287
2026-08-29T01:34:32Z heartbeat phase=60
