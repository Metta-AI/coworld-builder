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
