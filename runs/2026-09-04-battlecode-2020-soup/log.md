# 2026-09-04-battlecode-2020-soup — log

2026-09-04T02:57:25Z 00 claim comment posted on idea (story 1218170282739417), 20s re-read clean — no competing claim
2026-09-04T02:58:30Z 00 claim 2026-09-04-battlecode-2020-soup idea=1218165469199121 slug=battlecode-2020-soup
2026-09-04T02:58:30Z 00 run task 1218170282874132 created in Running, 9 phase subtasks, heartbeat_at custom field set
2026-09-04T02:58:30Z 00 MOD run per idea UPDATE 2026-09-03T22:05Z (daveey): branch/PR of Metta-AI/cogame-battlecode, bc20 year module + manifest variant, cert stays bc26, second league bc20; no new repo. Sibling run 2026-09-03-battlecode is live on the same repo (phase 30 r2) — coordinate at build/release time, never touch its run directory or task
2026-09-04T02:58:30Z heartbeat phase=10
2026-09-04T03:00:46Z 10 designer dispatched thread=sthr_017kDsFZq9XA61JtR8jzuZ4k output=runs/2026-09-04-battlecode-2020-soup/design.md (bc20 year-module mod; post-D1-D3 interface; no-Java-runtime pins in brief)
2026-09-04T03:00:46Z heartbeat phase=10
2026-09-04T03:23:11Z 10 designer returned round 1: design.md (1380 lines) — ACCEPTED against prompts/10-design.md checklist:
- [x] starter named with reason (cogame-battlecode itself; year-module mod; lineage coworld-ctf)
- [x] num_agents=2 fixed, in variants[bc20].game_config and restated for bc26; cert fixture stays bc26 (stated)
- [x] tick structure + exact numbered resolution rules 1-9 mirroring GameWorld.runRound, constants pinned from engine source
- [x] scoring formula (100*wins + mean(points); points=int(60*hq_survival+25*unit_share+15*net_worth_share) float32) with sign (higher better) and league ranks by results.scores
- [x] end conditions incl deadline; end_reason enum 7 values; results.reason complete|deadline|fault unchanged
- [x] per-seat observation JSON given; hidden set enumerated; sealed simultaneous
- [x] reply schema with per-field caps (16KB reply, sheet<=32 keys, notes 280 runes, motto 48 runes), rune-boundary truncation stated
- [x] both policies same image env-switched PLAYER_PROMPT vs PLAYER_SCRIPTED=bowl-of-chowder|examplefuncsplayer, baseline algorithms given
- [x] one parallel batch per doctrine phase; budget arithmetic 425s <= 720s (60% of episodeTimeoutSeconds), round cap 1500 chosen from real flood curve
- [x] degrade-never-hang table with retry-once -> fallback sheet (verbatim), early settle
- [x] two name spaces (Clan Ash/Clan Basil in-game; real names spectator-side)
- [x] viewer static wasm bundle, build hook, chrome verbatim, readouts listed, legible at 360px (checked in viewer smoke)
- [x] all four viewer files from ONE starter (cogame-battlecode's shipped bc26 viewer, unchanged loaders, no MODULARIZE splice); data-replay-loaded/data-replay-error stated
- [x] chrome provenance: chrome_common.js byte-for-byte, replay_broadcast.html appended bc20 block never rewritten (gridlock scar cited); zoom decided: KEEP #viewpanel (48x48 board > frame)
- [x] transport rules: --band/--hudscale via relayout(), nothing in transport band, endcard stops at var(--band) + dismissed on seek, 10 beat kinds all with CSS
- [x] replay self-sufficient (names, config, per-tick events, seed, doctrine payloads verbatim)
- [x] packaging: compose.yaml unchanged, manifest gains bc20 variant, game.docs readme+pages, game.protocols player+global, GV04, version 0.2.0, cert stays bc26
- [x] tests: sim unit tests, baseline legality+survival gate (D2), e2e episode replay, strict-UTF-8 parse, parity-oracle CI job (defined tiers), viewer smoke EXECUTED against both smoke replays
- [x] out of scope non-empty (13 items)
Post-D1/D2/D3 interface honoured (no chassis knob; baselines play; overlay dismisses). No rejection rounds needed.
2026-09-04T03:23:11Z 10 phase -> 20
2026-09-04T03:23:11Z progress phase=10 marker=design.md
2026-09-04T03:23:11Z heartbeat phase=20
2026-09-04T03:25:07Z 20 builder dispatched thread=sthr_01Ri6rwfEDZH5fDbkWjKHWcv branch=bc20-year-module output=runs/2026-09-04-battlecode-2020-soup/build-report.md (branch-only, PR open not merged, sibling-run coordination pinned in brief)
2026-09-04T03:25:07Z heartbeat phase=20
