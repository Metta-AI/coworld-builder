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
