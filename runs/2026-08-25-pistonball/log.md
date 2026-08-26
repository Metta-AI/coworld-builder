# 2026-08-25-pistonball — log

2026-08-26T00:03:25Z 00 claim 2026-08-25-pistonball idea=1217747862156473 slug=pistonball
2026-08-26T00:04:40Z 00 run task created gid=1217847385246447 section=Running, 9 phase subtasks created
2026-08-26T00:05:30Z 00 STATE written phase=10 session=a1f3c9d2
2026-08-26T00:07:30Z 10 starter=coworld-ctf reason=real-time continuous-physics loop with rules rewritten for this coworld (Cogball operator ruling 2026-08-22: new physics game is the ctf row, not a bit-exact moba port)
2026-08-26T00:09:30Z 10 designer dispatched thread=sthr_01HQvHFkV4bsRcy2cEg3vtjx output=runs/2026-08-25-pistonball/design-draft.md
2026-08-26T00:24:00Z 10 designer returned design-draft.md (1513 lines), reviewed against prompts/10-design.md checklist
2026-08-26T00:24:00Z 10 checklist: [x] starter named+reason (coworld-ctf, real-time physics loop) [x] num_agents=20 single number, in both variants + cert fixture + SMOKE_SEATS [x] tick structure + resolution order numbered 1-8 [x] scoring formula+sign (score=progress-penalty, higher better; league ranks cross-play mean, not Elo) [x] end conditions incl deadline/wall_clock; reason enum {complete,deadline,fault} [x] per-seat observation visible/hidden lists [x] reply schema with rune caps on every free-text field (note<=160, say<=48, policy<=48, detail<=200) [x] both policies LLM+scripted same image env-switched, baseline algorithms given (wavebot, metronome) [x] one parallel batch per turn, budget arithmetic ~376s expected / 455s worst < 720s [x] degrade-never-hang (retry once -> wavebot fallback; budget guard settles early) [x] two name spaces (PST-nn in-game, real names spectator-side) [x] viewer static wasm bundle + build hook + chrome verbatim + readouts + 360px [x] all four viewer files from coworld-ctf only; data-replay-loaded/-error stated [x] chrome provenance: chrome_common.js byte-for-byte, replay_broadcast.html appended block, removed elements listed, zoom: #viewpanel dropped (fixed arena) [x] transport rules (--band/--hudscale via relayout, endcard at var(--band) dismissed by seek, clickable labelled beat buttons with CSS per kind) [x] replay bytes self-sufficient (config+perm+inputs+hashes) [x] packaging: compose.yaml, manifest template, game.docs readme+3 pages, game.protocols player+global [x] tests: sim units, baseline legality (test 5), e2e episode replay (test 10), strict-UTF-8 parse, viewer smoke EXECUTED vs docker-smoke replay [x] out-of-scope non-empty
2026-08-26T00:24:00Z 10 design ACCEPTED round 1, zero rejections; copied to runs/2026-08-25-pistonball/design.md
2026-08-26T00:24:00Z progress phase=10 marker=design.md written and accepted
2026-08-26T00:24:30Z 00 phase transition 10 -> 20
2026-08-26T00:24:30Z heartbeat phase=20
2026-08-26T00:27:30Z 20 repo created https://github.com/Metta-AI/cogame-pistonball (public)
2026-08-26T00:28:30Z 20 propagate-secrets run 32915048989 success; SOFTMAX_TOKEN + ANTHROPIC_API_KEY present on cogame-pistonball
2026-08-26T00:31:00Z 20 builder dispatched thread=sthr_017guEM9Z4XXGnexTjEd3NsJ target=ci.yml green on main
2026-08-26T00:31:00Z heartbeat phase=20
2026-08-26T01:58:00Z 20 builder returned: ci.yml GREEN run=32923038675 sha=ce20047d66736a61bc772c52e05ffb82b38ccedf (verified conclusion=success, sha==main); 1 red round (32920732929, wasm-viewer soak vs 8s fixture replay) fixed by refixturing
2026-08-26T01:58:00Z 20 builder deviations from design note (rails: parameter tuning, accepted): SubSteps 4->16 + gravity/torque rescale (pinned stiffness unchanged); containment y-bounds [200000,4300000]; seeded 2-20cm drop offset (deterministic, replay-safe); cert fixture 1 wavebot + 19 metronomes (soak-length + both player entries slotted); heads-are-the-floor contact; wave/catch prose corrected to match formula; CTF_WIRE aliased (test-pinned exception); note: push via git-data API (HTTPS git push 403s in sandbox)
2026-08-26T01:58:00Z 20 baselines: 20 wavebots deliver 20/20 seeds mean +97.05; metronomes -10.07; 10/10 mix 20/20
2026-08-26T01:58:00Z progress phase=20 marker=ci-run-32923038675
2026-08-26T01:58:30Z 00 phase transition 20 -> 30
2026-08-26T01:58:30Z heartbeat phase=30
2026-08-26T02:05:00Z 00 INCIDENT: git push over HTTPS lost auth sandbox-wide; first git-data-API push (f6faa0e) raced a concurrent gift-refinements commit (2a7d583) and clobbered 4 of its files (3 emptied, log.md reverted). REPAIRED in b0137a1: all 4 restored byte-identical to 2a7d583 (verified via recursive tree diff). Future pushes via /tmp/apipush.sh which refuses paths outside this run.
2026-08-26T02:05:00Z heartbeat phase=30
2026-08-26T02:12:00Z 30 r1 reviewer dispatched thread=sthr_013G7UWRXvdShAmhEeXwKgey sha=ce20047 output=reviews/r1-review.md
2026-08-26T02:44:00Z 30 r1 reviewer returned: 13 findings, 0 claimed-blocking; reviews/r1-review.md
2026-08-26T02:44:00Z 30 r1 fixer dispatched
2026-08-26T02:44:00Z heartbeat phase=30
2026-08-26T04:21:00Z 30 r1 fixer returned: 17 commits ce20047..49518a2, CI green run=32928137084; N8 disputed with evidence (note self-contradiction; manifest's inverted copy fixed under N1); N9h evidence-answered; N13 evidence-answered; reviews/r1-fixes.md
2026-08-26T04:21:00Z 30 r1 judge dispatched sha=49518a22d734a3bcb952cc32952fe6e67eea39c6
2026-08-26T04:21:00Z heartbeat phase=30
2026-08-26T04:58:00Z 30 r1 judge returned: blocking 0 / BLOCKING 0 (markers agree, verified); all 13 advisory findings resolved or upheld-as-disputed; reviews/r1-verdict.md
2026-08-26T04:58:00Z progress phase=30 marker=r1-verdict.md
2026-08-26T04:58:30Z 00 phase transition 30 -> 40
2026-08-26T04:58:30Z heartbeat phase=40
2026-08-26T05:02:00Z 40 builder dispatched thread=sthr_0126iUpxe7i3gYmPGmo6jMrP target=coworld-release.yml canonical+certified, v0.1.0 first
2026-08-26T05:52:00Z 40 builder returned: v0.1.2 canonical+certified, cow_58917aec-d633-4f40-89b1-dbf496ddcfe0, release run 32930394604, secret_put true, 4 policies at :v2 (cascade owned by daveey-1); attempts: 0.1.0 manifest shape (game.description required, game.tags forbidden -> fix 1f51dfc), 0.1.1 player cpu limit min 1 core (fix ec82d45), 0.1.2 clean
2026-08-26T05:52:00Z 40 design-note deltas for LEARNINGS: platform requires game.description, forbids game.tags; player limits.cpu minimum "1"
2026-08-26T05:52:00Z progress phase=40 marker=release-run-32930394604
2026-08-26T05:52:30Z 00 phase transition 40 -> 50
2026-08-26T05:52:30Z heartbeat phase=50
2026-08-26T05:57:00Z 50 seed 200; league league_6789db33-ab0a-4b15-b572-b3ea39c614fd (leagues GET returns bare array here, matched client-side)
2026-08-26T05:57:30Z 50 division 200 div_de04ec28-cd1a-4349-9667-d34a687735c7; settings 200 elo round_robin filler_policy interval=15m (round_scoring_rule=mean per design note)
2026-08-26T05:58:00Z 50 champion1 submit dispatching: pistonball-swell:v2 as ply_44ae9048-3242-4654-881f-6d9d43347fa3
2026-08-26T04:42:13Z 00 clock note: previous stamps 05:52-05:58 were ahead of real UTC (sandbox drift on my part); stamps from here are real date -u
2026-08-26T04:42:13Z 50 champion1 submit ok run=32931064104 sub_67c13f0a-62a4-4137-9add-c43523f3adb5 (pistonball-swell:v2, daveey)
2026-08-26T04:42:13Z 50 champion2 submit ok run=32931105762 sub_92d8fa78-f25d-4927-91d3-39efdc9c79ae (pistonball-cascade:v2, daveey-1)
2026-08-26T04:42:13Z 50 filler-policies 200: wavebot:v2 e0e9ce4a-7232-4309-8558-752adb78b10e, metronome:v2 bf0ca47e-73a9-4283-bf0a-57f08f0de363 (set BEFORE my trigger)
2026-08-26T04:42:13Z 50 unpause 200; trigger-round 200; round 1 failed (auto-fired pre-fillers: Temporal RoundWorkflow failed before settling), round 2 pending with BOTH champions in entrant_attributions
2026-08-26T04:42:13Z progress phase=50 marker=league_6789db33-ab0a-4b15-b572-b3ea39c614fd
2026-08-26T04:42:13Z 00 phase transition 50 -> 60
2026-08-26T04:42:13Z heartbeat phase=60
