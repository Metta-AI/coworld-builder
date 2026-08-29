2026-08-28T23:25:51Z 00 claim 2026-08-28-crafter idea=1217748613493153 slug=crafter session=40794145 run_task=1217965201207246
2026-08-28T23:25:51Z 00 -> 10 phase transition: design
2026-08-28T23:26:38Z 10 starter=Metta-AI/coworld-ctf — single-agent real-time grid survival/tech-tree loop; Crafter/Craftax family re-implemented as own deterministic seeded Nim sim (not a bit-exact port: crafter is Python, Craftax is JAX — neither compiles to the wasm static viewer); precedent: nethack, minigrid, procgen, atari-57 all coworld-ctf
2026-08-28T23:27:27Z 10 designer dispatched round=1 thread=sthr_01Rt1d8s1MEmmvzPW582jsWU output=runs/2026-08-28-crafter/design.md
2026-08-28T23:48:34Z 10 designer returned design.md (2209 lines) round=1
2026-08-28T23:48:34Z 10 checklist: starter[x]=coworld-ctf num_agents[x]=1-in-both-variants+cert-fixture resolution-order[x]L332-numbered-per-turn+per-tick scoring[x]scores[0]=10000*achievements+survivalTicks-higher-better end-conditions[x]death/allUnlocked/turnCap/tickCap/wallClock/fault->complete|deadline|fault observation[x]L642-visible+hidden reply-caps[x]say160/notes400/prompt4000-rune-boundaries both-policies[x]techtree+homesteader-PROMPT,forager+wanderer-SCRIPTED parallel-batch+budget[x]one-req-per-turn-660s-stop-inside-720s degrade[x]retry-once->forager name-spaces[x]Alpha-in-game+real-names-spectator viewer-static[x]bundle+build-hook viewer-one-starter[x]coworld-ctf-all-four+data-replay-loaded chrome-provenance[x]byte-for-byte-sha-pinned+appended-block zoom[x]viewpanel-KEPT-64x64>frame transport[x]7-beat-kinds-css-each+endcard-var-band+360px-L1722 replay-self-sufficient[x]L1385-config-table packaging[x]compose+manifest+docs+both-protocols+2-variants tests[x]51-items+viewer_smoke-executed-vs-docker-smoke-replay out-of-scope[x]non-empty — ACCEPTED round 1
2026-08-28T23:48:34Z progress phase=10 marker=design.md written and accepted round 1
2026-08-28T23:48:34Z 10 -> 20 phase transition: build
2026-08-28T23:49:34Z 20 repo created: https://github.com/Metta-AI/cogame-crafter (public)
2026-08-28T23:49:34Z 20 propagate-secrets run 33221646319 success; SOFTMAX_TOKEN + ANTHROPIC_API_KEY on cogame-crafter
2026-08-28T23:50:36Z 20 builder dispatched round=1 thread=sthr_01UovTdQakeW1rzSu1z26bMt repo=Metta-AI/cogame-crafter
2026-08-29T02:18:48Z 20 builder returned: CI green run=33228279820 sha=71bf90d1af107a6c5162a4d7d53f683c9c55cab1 (4 CI rounds; 5 documented divergences in docs/PORTING-CRAFTER.md; nano-banana art landed)
2026-08-29T02:18:48Z 20 exit checks verified: placeholders-clean executables-755 num_agents=1x3 protocols-both bundle=static-replay-viewer workflows-parse release-inputs+release-result submit-inputs+submit-result player-field policies=2-PROMPT+2-SCRIPTED champion2-player-id
2026-08-29T02:18:48Z progress phase=20 marker=ci-run-33228279820-success
2026-08-29T02:18:48Z 20 -> 30 phase transition: review loop round 1
2026-08-29T02:19:52Z 30 r1 reviewer dispatched thread=sthr_01QShf6aWPyet6bP6HrUwNnX repo-checkout=/tmp/cogame-crafter@71bf90d1
2026-08-29T02:38:47Z 30 r1 reviewer returned r1-review.md (25 findings; 1 candidate blocking F1 test-skip/deleted-assertion; provenance checks clean)
2026-08-29T02:38:47Z progress phase=30 marker=r1-review.md
2026-08-29T02:39:26Z 30 r1 fixer dispatched thread=sthr_01UafkRYVrsg1wiojYX86s4r
2026-08-29T03:32:49Z 30 r1 fixer returned r1-fixes.md: 25/25 resolved (15 code fixes incl F1 skip-removed+source_url restored, 10 documented divergences); CI green run=33231383944 sha=2a62f81c2d6ac29a2c9002021ce6884a784e1dcc
2026-08-29T03:32:49Z progress phase=30 marker=r1-fixes.md
2026-08-29T03:34:10Z 30 r1 judge dispatched thread=sthr_017Snz33kouFe5j6fW96K7U3 sha=2a62f81c
2026-08-29T03:49:15Z 30 r1 judge returned r1-verdict.md: blocking 0 / BLOCKING 0 (all 25 findings dismissed-fixed-or-documented; independent checklist pass clean; 4 advisories logged)
2026-08-29T03:49:15Z progress phase=30 marker=r1-verdict.md
2026-08-29T03:49:15Z 30 -> 40 phase transition: release (sha=2a62f81c ci=33231383944)
2026-08-29T03:50:02Z 40 builder dispatched for release thread=sthr_01Vj2m8p1ARqUAbPCKVhb6BW version-plan=0.1.0
2026-08-29T04:00:42Z 40 release dispatch 1/3 version=0.1.0 run=33232381840 success: canonical=true cow_id=cow_88aa79dd-1661-4c42-9024-abb912d2de34 certify.ok=true replay_liveness=skipped-static secret_put=true policies=4x v1 champion2-player=ply_bac48eb1
2026-08-29T04:00:42Z progress phase=40 marker=release-run-33232381840
2026-08-29T04:00:42Z 40 -> 50 phase transition: league
2026-08-29T04:01:46Z 50 seed 200 lseed_06fc2a6d league=league_791e396c-32b3-47f1-bd94-23e276f6b6c5
2026-08-29T04:01:46Z 50 division 200 div_160b65a4-63bf-4ce9-8bc7-a6e0e9c3b6f5; settings 200 (elo, round_robin, filler_policy, 15min)
2026-08-29T04:04:09Z 50 champion1 submit run=33232826821 ok sub_7c580ab3 (crafter-techtree:v1, daveey)
2026-08-29T04:04:09Z 50 champion2 submit run=33232848503 ok sub_316c8df6 (crafter-homesteader:v1, daveey-1)
2026-08-29T04:04:09Z 50 fillers registered: forager=72a75938-334c-4ecd-8355-51c8aa5bc12c wanderer=6f66cf9c-b4b1-4a1f-9049-97211decde06 (before first trigger)
2026-08-29T04:04:09Z 50 unpaused; trigger-round accepted; round 1 pending; entrant_attributions = both champions
2026-08-29T04:04:09Z progress phase=50 marker=round-1-pending league_791e396c
2026-08-29T04:04:09Z 50 -> 60 phase transition: verify
2026-08-29T04:05:04Z 60 verifier dispatched thread=sthr_01S1AhFMWAesF1DZqCaZbgTB (round 1 pending since 04:02Z; 75-min bound)
2026-08-29T04:37:07Z 60 verifier returned VERIFY.md (777 lines): checks 1-5,7,8 TRUE; 6a static route TRUE, 6b playlist=[] but both replays in state.pool.replays — procgen precedent (runs/2026-08-28-procgen/VERIFY.md L426-466) reads pool presence as the featured match, playlist=[] normal for single-seat
2026-08-29T04:37:07Z 60 rounds 1+2 completed (04:04Z, 04:19Z); leaderboard daveey 1001.47 / daveey-1 998.53; replay clean, 34/34 llm decisions, 0 fallbacks; viewer-check run 33233844065 loaded=true clocks advance
2026-08-29T04:37:07Z 60 phase-30-class observations from live viewer: (A) 8 dead 404 preloads of starter soldier sprites; (B) endcard overflow at 800px (rows 21-22 clipped, bleed into minimap)
2026-08-29T04:37:07Z progress phase=60 marker=VERIFY.md written, rounds 1+2 completed
