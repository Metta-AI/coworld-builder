# 2026-08-26-poker — log

2026-08-26T14:43:28Z 00 claim comment posted on idea 1217747803484730 (story 1217870934026256)
2026-08-26T14:43:55Z 00 claim re-check after 20s: no competing claim, proceeding
2026-08-26T14:43:55Z 00 claim 2026-08-26-poker idea=1217747803484730 slug=poker
2026-08-26T14:44:30Z 00 run task 1217871010134558 created in Running, 9 phase subtasks created
2026-08-26T14:44:30Z 00 operator note on idea (David Bloomin 2026-08-22T19:15:46Z): "This seems like it's already partially done in Cosino, can we just extend it with other games?" — consistent with idea text; design brief will pin cogame-cosino as the poker-engine base per playbook starter table (parley descendant) and the paintball/hidden-agenda/knights-archers precedent that EXTENSION ideas ship as a new cogame-<slug>
2026-08-26T14:45:02Z 00 STATE written phase=10 session=8bd3f494
2026-08-26T14:45:02Z heartbeat phase=10
2026-08-26T14:52:10Z 10 starter=cogame-cosino (turn-based cards + LLM-prompt policies -> parley-stack row; playbook row 1 allows "newest parley descendant (cogame-bullwhip, cogame-focus, cogame-cosino)" when closer, and cosino IS the Hold'em engine the idea extends — blinds, side pots, Chen baseline, all four static-viewer files, compose+manifest+build hook present; babel kept as current-template reference for conventions the note must confirm or upgrade) repo=Metta-AI/cogame-poker per SPEC pin
2026-08-26T14:56:40Z 10 designer dispatched round=1 thread=sthr_01UZZ58TJCoT5kmGUDZ18DPr output=runs/2026-08-26-poker/design-draft.md session=8bd3f494
2026-08-26T15:05:19Z 10 designer returned round=1 file=design-draft.md (1000 lines)
2026-08-26T15:05:19Z 10 checklist: [x] starter=cogame-cosino+reason (parley descendant, IS the Hold'em engine the idea extends) [x] num_agents single per variant kuhn=2 leduc=2 holdem-hu=2 holdem-6max=6, cert fixture=2=<SEATS> [x] resolution rules numbered per rung + exact duplicate-mirror map seatOrderMirror[p]=seatOrder[(p+n div 2) mod n] [x] scoring scores[i]=1/n+net[i]/(n*S*H) in [0,1] sum=1 higher-better, league ranks Elo over scores in ONE ladder across 4 variants (reason: unit-free score) [x] end conditions complete/deadline(soft 720s pair-boundary, hard 840s handVoid+refund)/budget(220 calls), enum declared [x] per-seat observation visible/hidden incl mirror invisible to seats [x] reply schema rune caps (say 160, prompt 4000, alias 16, error 200) via shared truncateRunes [x] both policies same image env-switched PLAYER_PROMPT vs PLAYER_SCRIPTED=house|rock with per-variant algorithms (Kuhn Nash alpha=1/6, Leduc rule table, Chen verbatim) [x] sequential budget 3.0s/decision, all variants 468-624s < 720s=60% of 1200s, 2100ms spacing under 30rpm sidecar cap [x] degrade retry-once->scripted->forced-fold, early settle, no-creds offline path [x] two name spaces [x] viewer static wasm bundle + build hook 100755 + mkdir-before-containment [x] all four viewer files from cosino (MODULARIZE/factory pair verified), data-replay-loaded on first drawn frame + data-replay-error [x] chrome provenance chrome.css byte-for-byte + fenced appended block, index.html ids kept, nothing removed, no #viewpanel (fixed arena) [x] transport --band/--hudscale by relayout(), overlays bottom:var(--band), endcard stops at band + dismissed by every seek, beats clickable buttons w/ CSS for all 6 kinds [x] replay self-sufficient (seed in bytes, audit MC re-derivable) [x] packaging compose+manifest (POKER_IMAGE, num_agents every variant, static bundle, schemas w/ minItems/maxItems, limits.cpu "1") + docs readme+3 pages + protocols player+global as text objects [x] tests: cards/sim/solve/audit/bot suites, bounded-orders both baselines all variants, e2e docker-smoke strict-UTF-8, viewer_smoke EXECUTED twice (cert replay + committed 6max audit fixture) w/ soak 12 + strict-text-bounds [x] out-of-scope 10 items — ACCEPTED round 1, zero rejections
2026-08-26T15:05:19Z 10 design.md copied from design-draft.md; phase 10 -> 20
2026-08-26T15:05:19Z progress phase=10 marker=design.md
2026-08-26T15:05:19Z heartbeat phase=20
2026-08-26T15:05:42Z 20 repo created: https://github.com/Metta-AI/cogame-poker (public); propagate-secrets dispatched run 32984047591 (queued behind runner backlog ~10min; secrets verified before phase-20 exit)
2026-08-26T15:15:09Z heartbeat phase=20
2026-08-26T15:16:18Z 20 builder dispatched round=1 thread=sthr_01UJkZrAVddKNTDibtykKJvv repo=Metta-AI/cogame-poker session=8bd3f494
2026-08-26T15:16:18Z heartbeat phase=20
2026-08-26T15:26:21Z heartbeat phase=20
2026-08-26T15:44:52Z heartbeat phase=20
2026-08-26T15:50:09Z 20 note: GitHub Actions major_outage (githubstatus.com); propagate-secrets 32984047591 queued 55min — not blocking builder authoring; secrets only needed by phase 40; will re-verify when Actions recovers
2026-08-26T15:59:56Z heartbeat phase=20
2026-08-26T16:14:33Z heartbeat phase=20
2026-08-26T16:29:11Z heartbeat phase=20
2026-08-26T16:49:33Z 20 CI green on main: run 32989622335 sha=94e5e00050211f8fb0f5b3171b72f3eb0591949b (jobs test/docker-smoke/wasm-viewer success); coordinator exit checks pass: placeholders CLEAN, exec bits 100755 both hooks, viewer_smoke.mjs byte-identical, 3 workflows active w/ pinned inputs + release/submit-result artifacts + per-policy player field, num_agents 2/2/2/6 + cert 2, game_config.players 2/2/2/6, policies.json 2 PROMPT + 2 scripted champion#2 player=ply_bac48eb1; stale-sha run 32990171724 failed on transient nimby download reset (GitHub outage) — not HEAD, ignored
2026-08-26T16:49:33Z heartbeat phase=20
2026-08-26T16:55:28Z 20 builder returned round=1 thread=sthr_01UJkZrAVddKNTDibtykKJvv: GREEN run=32989622335 sha=94e5e00 zero red rounds; 8 findings self-reported; coordinator rails decision on finding 1 (audit FP): drop outer clamp (signed showdown attribution), keep bb thresholds, restore strict zero-FP test both baselines — design.md Addendum 1 appended; follow-up dispatched to builder
2026-08-26T16:55:28Z progress phase=20 marker=32989622335
2026-08-26T16:55:51Z heartbeat phase=20
2026-08-26T17:02:13Z 20 builder measured Addendum 1 insufficient (3/30 & 8/30 honest-house flags, new negative-surrender soft-play FP); coordinator rails decision: option A — final-board showdown equity, MC fold-case only, signed attribution kept, limitation (call-off dumping unflagged, netFlow shows it) documented — design.md Addendum 2 appended; builder directed to implement
2026-08-26T17:02:31Z heartbeat phase=20
2026-08-26T17:14:16Z 20 builder returned round=2 (follow-up): Addendum 1+2 implemented, GREEN run=32992433560 sha=7c7e77b977a0256df4d0b78ce79fb35f3d6b1489; 0/30 honest flags both baselines at 16 & 24 hands, synthetic signals intact, strict zero-FP test restored, audit.md limitation section, fixture byte-identical
2026-08-26T17:14:16Z progress phase=20 marker=32992433560
2026-08-26T17:14:16Z 20 -> 30 phase transition: STATE.phase=30 review_round=1
2026-08-26T17:14:16Z heartbeat phase=30
2026-08-26T17:15:16Z 30 reviewer dispatched round=1 thread=sthr_01NCM3enCbyLTHU3d9MmMQag output=runs/2026-08-26-poker/reviews/r1-review.md sha=7c7e77b session=8bd3f494
2026-08-26T17:15:16Z heartbeat phase=30
2026-08-26T17:32:38Z 30 reviewer returned round=1 file=r1-review.md (684 lines): 2 blocking candidates (B1 legibility bubble<cap, B2 timeout 70%>60%), 10 notes; coordinator rulings appended as design.md Addendum 3 (guards 660/720, 6max 16->14 hands, say cap 160->120 sized to bubble); dispatching fixer
2026-08-26T17:33:22Z 30 fixer dispatched round=1 thread=sthr_01MHTWZ4NJbXA6nKAcEsD4X7 findings=B1,B2 output=runs/2026-08-26-poker/reviews/r1-fixes.md session=8bd3f494
2026-08-26T17:33:22Z heartbeat phase=30
2026-08-26T18:03:30Z 30 fixer returned round=1: B1 73f2cb5 (say 120, bubble 300x6, fixture 0 ellipsized), B2 b6a8e9d (guards 660/720, 6max 14 hands), GREEN run=32996855409; residual raised (guard-before-decision worst 763s=63.6%); coordinator ruling: design.md Addendum 4 (hard guard 672s nets off one worst-case decision) — follow-up commit directed before judge
2026-08-26T18:03:54Z heartbeat phase=30
2026-08-26T18:14:32Z 30 fixer follow-up returned: Addendum-4 commit bba6bff GREEN run=32997839855; sixmax viewer smoke 0 ellipsized re-confirmed on final sha
2026-08-26T18:14:32Z progress phase=30 marker=r1-fixes.md
2026-08-26T18:14:32Z 30 judge dispatched round=1 thread=sthr_01BG9mWtiZhrPYbNKcRzA1g1 sha=bba6bff output=runs/2026-08-26-poker/reviews/r1-verdict.md session=8bd3f494
2026-08-26T18:14:32Z heartbeat phase=30
2026-08-26T18:25:13Z 30 judge returned round=1 verdict=r1-verdict.md blocking:0/BLOCKING:0 agree — B1/B2 confirmed-then-refuted at head bba6bff, all 15 checklist items PASS, 3 non-blocking observations (notable: uncapped 429 spacing bump, ceiling 825s < 1200s)
2026-08-26T18:25:13Z progress phase=30 marker=r1-verdict.md
2026-08-26T18:25:13Z 30 -> 40 phase transition: STATE.phase=40 (review loop closed in 1 round)
2026-08-26T18:25:13Z heartbeat phase=40
2026-08-26T18:26:07Z 40 secrets verified on cogame-poker (SOFTMAX_TOKEN + ANTHROPIC_API_KEY, set 16:31Z)
2026-08-26T18:26:07Z 40 builder dispatched for release thread=sthr_01UJkZrAVddKNTDibtykKJvv version=0.1.0 session=8bd3f494
2026-08-26T18:26:07Z heartbeat phase=40
2026-08-26T18:35:58Z 40 release dispatch 1 version=0.1.0 run=32999717629 step_failed=null: ok/canonical/certified, replay_liveness skipped(static), 4 policies distinct, champion#2 player=ply_bac48eb1, secret_put true — exit criterion met first dispatch
2026-08-26T18:35:58Z progress phase=40 marker=32999717629
2026-08-26T18:35:58Z 40 -> 50 phase transition: STATE.phase=50
2026-08-26T18:35:58Z heartbeat phase=50
2026-08-26T18:36:18Z 50 league seeded: league_14d979bc-860c-4c64-a706-e867a2ac1ca5 (seed lseed_19f02673); paused immediately (fresh-ladder learning)
2026-08-26T18:36:55Z 50 division div_2c39ffc7-6856-4d5f-ad55-c19072cd23b6 created; settings POST 200 (elo round_robin filler_policy, 15min interval)
2026-08-26T18:37:30Z 50 champion1 submit run=33000674661 ok=true poker-scholar:v1 daveey
2026-08-26T18:38:10Z 50 champion2 submit run=33000729503 ok=true poker-exploiter:v1 daveey-1
2026-08-26T18:39:00Z 50 policy-version UUIDs resolved: scholar 188b5f98 (daveey), exploiter f3c265fe (daveey-1), house 9416f376, rock d00d5160
2026-08-26T18:39:20Z 50 fillers registered while paused: house+rock only, 200
2026-08-26T18:39:50Z 50 unpaused; trigger-round 200 workflow ladder-league_14d979bc
2026-08-26T18:40:30Z 50 round 1 pending, error=-, entrant_attributions = both champions (188b5f98 daveey, f3c265fe daveey-1)
2026-08-26T18:39:59Z progress phase=50 marker=league_14d979bc-860c-4c64-a706-e867a2ac1ca5
2026-08-26T18:39:59Z 50 -> 60 phase transition: STATE.phase=60
2026-08-26T18:39:59Z heartbeat phase=60
2026-08-26T18:40:53Z 60 verifier dispatched thread=sthr_01Bc93hirBwa5hW2FsKx88m6 output=runs/2026-08-26-poker/VERIFY.md session=8bd3f494
2026-08-26T18:40:53Z heartbeat phase=60
2026-08-26T18:50:42Z heartbeat phase=60
2026-08-26T19:00:32Z heartbeat phase=60
2026-08-26T19:10:22Z heartbeat phase=60
2026-08-26T19:10:29Z heartbeat phase=60
2026-08-26T19:20:16Z heartbeat phase=60
2026-08-26T19:30:17Z heartbeat phase=60
