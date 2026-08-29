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
