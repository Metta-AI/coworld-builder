blocking: 0

# r1 verdict — battlecode
Head: `81ffb0e41d51b4622e9377d0dcc02a8946cbd08c` (main; CI run **33824171362**, conclusion `success`, jobs test / parity-oracle / docker-smoke / wasm-viewer all ✓)
Checklist: `/workspace/coworld-builder/prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Independent read written before reading fixes: **yes** (repo, design note, manifest, CI logs and both chrome diffs read and noted before opening `r1-review.md`; `r1-fixes.md` opened last, only to audit commit claims).

Repo cloned fresh to `/tmp/judge-cogame-battlecode` at the head sha. The review was written at
`3eb7915`; sixteen fix commits (`524d7e0`…`81ffb0e`) landed between it and the head, so every
finding was re-verified **at the head**, not at the review's sha.

## Standing blocking findings

**None.** No checklist item is falsified at `81ffb0e`, and no item was unverifiable from the tree
or from cited CI evidence.

## Disposition of the review's findings

### B1 — `#endcard` shown with `.show` against a `#endcard.on` rule → FIXED (was real at 3eb7915)
- Evidence at head: `client/replay_broadcast.html:3025` `$('endcard').classList.add('on');`,
  `:2981` `classList.remove('on')`, with the inline comment naming the inherited rule
  (`#endcard.on { display: flex; … }` at `:1859`). Not merely fixed — now gated:
  `.github/workflows/ci.yml:568-580` fails the build unless the endcard's **computed display** is
  shown after the 100 % seek, and the green run's log says
  `endcard after the 100% seek: shown=true text=CLAN ASH — CLAN ASH` (job 100873787005).
  `tests/test_viewer.nim:201+` pins both toggle sites and the absence of any `.show` toggle.

### N1 `#mmwarn` `.show`/`.on` → FIXED — `client/replay_broadcast.html:3165` `mm.classList.add('on')` (commit `764069d`).
### N2 scrub gate clicked the zoom slider → FIXED — `viewer_smoke.mjs` resolves selectors in priority order and records `scrub_selector`; `ci.yml:554-561` fails unless it is `#scrub`; log: `scrub selector: #scrub` (commit `524d7e0`).
### N3 budget timeout double-recorded as `parse` → FIXED — `src/battlecode/decide.nim:171-185`: the timeout branch names the cause, echoes `falling back`, and `open.setLen(0)` before `break`. Test exists as claimed: `tests/test_sheet.nim:235-265` drives `decide()` with `doctrineBudgetMs = 1` and asserts exactly one `doctrine_fallback` per seat (commit `991b965`).
### N4 `plan.abandon_after` dead data → FIXED — `src/battlecode/replay.nim:238-254` `gameRecord` reads the header when present and `plan.abandonAfter[index]` when not; `newDeriver` plans frames from it. `tests/test_determinism.nim:147-195` builds the header-less document the recorder actually writes and asserts 200 frames, stop at round 200, no mismatch (commit `8a98179`).
### N5 chain compared once per game, three stats missing → FIXED — `world.nim:1531-1544` folds all **seven** per-team stats (dirt + both trap counts added, GV02); `GameOutcome.roundChains` records the chain after every round; `replay.nim:289-298` compares **every** round and reports the first divergent one; `tests/test_determinism.nim` (r1-N13 hunk) corrupts round 40 and asserts `mismatchRound == 40` (commit `9ff4a07`).
### N6 knob-teeth seed loop inert → FIXED — `tests/test_knob_sensitivity.nim:38,56-58`: `Seeds = [1, 2, 3]` and `spec.randomSeed = spec.randomSeed + seed`, 9 distinct games per pair (commit `785a33e`).
### N7 `never` == `retaliate_only` → FIXED — `kit.nim:65-78`: after the flip `never` still declines (`backstabPolicy != bpNever`), GV03 bump in `sim_types.nim:16-28`, five values documented in `docs/RULES.md`, asserted in `tests/test_rules_combat.nim` (commit `badbe32`). The reviewer's sub-point that the rat-trap gate is "not in the note" was itself wrong: the note's knob table says "with hostilities closed, enemy rats are simply not candidates for bite/ratnap/throw/**rat-trap**" (design.md:300) — **REFUTED** on that sub-point.
### N8 fixture shipped private CSS, skipped the harness → FIXED — `ci.yml:599-625` extracts the page's own `<style>` block into `page_styles.css`, serves the fixture over http and drives it with `node tools/ci/viewer_smoke.mjs --url … --strict-text-bounds`; `tools/ci/renderer_fixture.html` declares no rule for anything it measures, fails loudly if the CSS did not load (`:209-213`), measures every element under `#chrome` for frame containment and every filled readout for clipped content at 360/720/1280 px, and asserts its strings are still full-cap (`:250-258`). Green: `{"loaded":true,…}` for the fixture step (commit `4725555`).
### N9 round-loop order differs from the note's prose → NO DEFECT, documented — the code follows the **engine's** order (`InternalRobot.processEndOfTurn` does king consumption + the cat machine; `destroyRobot → checkWin` for the outright wins), `docs/RULES.md` documents it with engine citations (commit `212db9a`), and Tier A/B of the parity oracle — bit-exact rounds 1–50 and round 200 on five maps — is direct evidence the code's order is the correct one. The note's prose loses to the engine here; no checklist item names the note's step list.
### N10 prompt payload not recorded → FIXED — `replay.nim:80-95` writes `seats[].prompt` (verbatim brief), `seats[].fallback_detail` (200-rune cap), and document-level `prompt_preamble`; all parsed back in `parseReplay` (commit `3d98f98`).
### N11 `NOTICE` missing → FIXED — `NOTICE` exists at head, names both upstreams at pinned commits (`991c91af…`, `a70328ea…`), AGPL, and the no-Java-at-runtime claim (commit `1d2b21c`).
### N12 `#btn-skip` not relabelled → NO DEFECT, documented — in this lineage `#btn-fwd` is the forward step (`.` → +25 rounds, `broadcast.nim:51`, `bc_replay.nim:113-115`) and `#btn-skip` is the auto-skip toggle; the label rides the button that does the thing, the page comment says so (`replay_broadcast.html:3060-3068`), and no checklist item names the +25 label (commit `a234016`).
### N13 four vacuous test claims → FIXED — verified from `git log -p -- tests/` hunks: (a) the coworld CLI (`coworld==0.1.43`, the release workflow's pin) now validates the template in the `test` job (`ci.yml:182-203`; log: `coworld accepted the template: battlecode with 1 variant(s)`) — and this surfaced two real manifest defects (`game.owner` missing, `limits.memory` forbidden), both fixed in the template at head (`coworld_manifest_template.json:13`, `:415-421`); (b) every `EndReason` now asserted via `seenReasons` (`test_determinism.nim:232-238`); (c) the Dockerfile scan reads instructions with comments stripped; (d) the endcard-band assertion reads the `#endcard` rule itself (commit `2ee91f9`).
### N14 reply cap in runes not bytes → FIXED — `sim_types.nim:130-145` `truncateBytes` (byte cap, rune boundary), used by `parseReply` (`sheet.nim:308`); test feeds a 40 KB astral sample (commit `a8684c0`).
### N15 dead spoiler guard, ungated beat buttons → FIXED — `replay_broadcast.html:2831-2843` `applyBeatSpoilers` hides a marker ahead of the playhead, applied on build, every frame and both spoiler toggles; the unreachable feed guard is gone with its reason written down (commit `93bbf33`).
### N16 `scaffold` is examplefuncsplayer verbatim → NO DEFECT, documented — upstream `RobotPlayer.java` at `engine.1.2.5` really is move-or-turn only (no bite, no pickup); the parity oracle's Tier A requires the port to match **that** bot bit-exactly, so the note's richer description is the thing that is wrong. `scaffold.nim:1-15` and `docs/PARITY.md` both state it (commit `81ffb0e`).

## Checklist pass (independent)

| item | status | evidence (path:line or run) |
|---|---|---|
| 1 CI green, no test loosened | PASS | run 33824171362 `success` at `81ffb0e` (`gh run list`); `git log -p -- tests/` over the repo's whole history: every deleted assertion is a strengthening rewrite (Dockerfile scan de-vacuumed, endcard rule pinned tighter, chain test extended to first-divergent-round, variants moved top-level **plus** new assertions). No skip/xfail/tolerance widening, no test file removed. |
| 2 replay re-derivation, frame by frame | PASS | `replay.nim:273-299` deriver re-runs `runRound` on the shared sim and compares the chain **every round** (`hash_chain_rounds`, GV02); viewer packets built from `deriver.world` only (`bc_replay.nim:64-72`); tests: `test_determinism.nim:49-238` (every end reason incl. the recorder-shaped `deadline` doc), `test_replay.nim` (corrupt chain → round 40 named). |
| 3 static viewer | PASS | manifest `game.replay_viewer.bundle = "static-replay-viewer"` (:14-16); `tools/build_replay_viewer.sh` 0755, asserted executable in `ci.yml:454-465`; only network call in the bundle is `fetch(message.replayUrl)` (`static_replay_worker.js:127`); server routes have no `/client/replay` (`server.nim:333-341`). |
| 4 both name spaces | PASS | `briefFor` sends aliases only (`decide.nim:118-140`, no `names` key); real names only in results/replay/chrome, drawn at `replay_broadcast.html:2871-2876` and the endcard. |
| 5 degrade-never-hang | PASS | connect ≤ `connectTimeoutMs` (`server.nim:156-169`); doctrine ≤ 45 s monotonic (`decide.nim:149,171`); curl `CURLOPT_TIMEOUT` per batch (`decide.nim:206`); per game 90 s sampled every 32 rounds (`rules.nim:158-167`); match 330 s with remainder clamp (`match.nim:104-115`); player dial 240×500 ms + ≤6 re-dials (`battlecode_player.nim:24-30,103-133`). Worst case ≈ 25+45+330+30+20 ≈ 450 s ≤ 720 s. `test_perf.nim` gates a full 2000-round game at ≤ 45 s. |
| 6 num_agents | PASS | `num_agents: 2` in `variants[0].game_config` (:484) and `certification.game_config` (:520), absent at variant top level (test_manifest pins it); `docker_smoke.sh:106-151` enforces all four invariants + `SMOKE_SEATS` cross-check; **grep of the docker-smoke job log for `SEAT-COUNT FAIL`: 0 hits**; `parseConfig` rejects `num_agents != 2` with exit 2 (`server.nim:221-223`). |
| 7 scripted baseline full episodes, legal | PASS | docker-smoke (no key) asserts `reason=="complete"`, `fallbacks==[0,0]` and closed keys, green; `test_determinism.nim:93,108,140` assert `epComplete` on played matches; `test_baselines.nim:46-94` audits legality invariants over 3 maps × 400 rounds and both chassis; knob parameters measured in `test_knob_sensitivity.nim`'s paired-game harness (its header table records the measured deltas), 9 distinct seeded games per pair. |
| 8 LLM reply handling | PASS | `extractJsonObject` balanced-brace + fence tolerant (`sheet.nim:130-166`); exactly one retry (`decide.nim:169` `attempt < 2`); scripted fallback recorded in `results.fallbacks`, `doctrine_fallback` events, `falling back` log lines; `test_sheet.nim:235-265` asserts one fallback per seat with the surviving cause. |
| 9 rune-safe truncation | PASS | `truncateRunes`/`truncateBytes`/`sanitizeLine` (`sim_types.nim:121-150`) at every recorded string; `test_sheet.nim:156-196` feeds astral text at the caps and asserts rune boundaries + valid UTF-8; `test_replay.nim:101-118` asserts the **written replay bytes** are strict UTF-8. |
| 10 manifest validates | PASS | `game.docs.readme` + 3 `pages[]` all `{type,value}`; `game.protocols` has `player` and `global` (:17-26); and the **publishing CLI itself** accepts the template in CI (`ci.yml:182-203`, log `coworld accepted the template: battlecode with 1 variant(s)`). |
| 11 legible at 360 px | PASS | `replay_broadcast.html:2561` `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` byte-exact; `:2617-2621` `@media (max-width: 640px)` hides `.plate-sub`; the renderer fixture passes at 360 px with full-cap text. |
| 12 release order and scaffold | PASS | `coworld-release.yml`: Build manifest (:159) → Certify (:173) → Upload policies (:216) → Upload coworld (:314) → Secret put (:410), certify runs on the freshly built bundle in the same job; all three workflows present; `docker_smoke.sh` 0755; `policies.json` = 2 `PLAYER_PROMPT` champions + 2 scripted fillers, champion #2 carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; the placeholder grep over the five files returns no matches (exit 1 → gate exits 0). |
| 13 viewer executes | PASS | `wasm-viewer` `needs: docker-smoke` (`ci.yml:441`); browser step present, no `continue-on-error`, green with `{"loaded":true,"ms":305,…}` and a 10 s soak that kept advancing (round 3 → 195 → 243); `data-replay-loaded` set on the worker's `loaded` message after the first frame is ingested/composited (`static_replay.js:180`), `data-replay-error` on every failure path (`:19-27`, worker `onerror`/`onmessageerror`/abort); **no lobby dwell is possible**: the deriver's frame axis contains only in-game rounds (`replay.nim:256-265`), pre-match events carry `ms` not frames, `st = 0`, and `seek` clamps to `[0, totalFrames-1]` — a late gameStart cannot exist on this axis; link flags have no `MODULARIZE`/`EXPORT_NAME` and the worker uses the matching global-`Module` + `onRuntimeInitialized` bootstrap, both diffed against the same starter (only `ctf_*→bc_*` renames); node wasm smoke runs the emitted module against the CI replay. |
| 14 chrome is the starter's | PASS | `chrome_common.js` **byte-identical** to `/workspace/starters/coworld-ctf/client/chrome_common.js` (diff empty), `broadcast_core.js` likewise; `replay_broadcast.html` above the banner is a **pure subset** of the starter (diff of lines 1–2545 against the starter: zero non-starter lines except the banner itself), deletions accounted for by the note's removal list (fpv/lockerroom/vote/huddle/glory/comms/momentum-label/lulls/cell-*; `#momentum` kept hidden with the reason written); the page is smaller than the starter only because the starter's ctf-specific per-view script is replaced by the appended game block — chrome CSS/markup/ids are intact, which is what the size rule exists to protect. Transport: `relayout()` sets `--hudscale/--topband/--band` on `document.documentElement` (:3040-3052); `#econ`/`#doctrines` ride `bottom: calc(var(--band,0px)+8px)`; `#endcard` keeps `bottom: var(--band, 0px)` and is raised with `.on`; every seek path calls `dismissEndcard()` (scrub :3095, beats :2815, buttons :3053, keyboard :3079); beats are labelled `<button>`s with `aria-label`+`title` seeking their tick, CSS for every emitted kind (`.doctrine/.king/.backstab/.cat/.game/.end`, `broadcast.nim` emits exactly those); `#viewpanel` **kept** per the design note (30–60-tile board renders wider than the 360 px frame) with full zoom/minimap wiring and `?viewpanel=0`. |
| 15 drawn strings fit their frames | PASS | main smoke drops `--strict-text-bounds` (pannable board — the note documents it, `ci.yml:535-543`) and the `canvas_text` counts are recorded; this viewer draws **no model text on canvas** (all notes/motto land in DOM; the board is an OffscreenCanvas worker, so `canvas_text.total = 0` by architecture, correctly treated as "covered nothing"); the required worst-case renderer fixture exists and is the stronger DOM equivalent: full-cap (280-rune notes, 48-rune motto, astral runes) on both seats, **the page's own extracted CSS**, 360/720/1280 px, every element measured for frame containment and clipped content, full-length strings asserted, driven by `viewer_smoke.mjs --strict-text-bounds` in its own `ci.yml` step (:599-625), failing via `data-replay-error` which the harness gates on. Green: fixture `{"loaded":true}`, `canvas text: 0 drawn, 0 never inside … (--strict-text-bounds)`. |
| parallel batch | PASS | one `RequestBatch` for all open seats, one `curly.makeRequests` call (`decide.nim:189-206`); no per-seat call site exists. |

## Fixer report audit

| finding | fixer said | I verified | agrees |
|---|---|---|---|
| B1 | `.on` at both sites + CI gates computed display | `replay_broadcast.html:2981,3025`; `ci.yml:568-580`; log `shown=true` | yes |
| N1 | `mmwarn` `.on` | `:3165` | yes |
| N2 | priority-order selectors + `scrub_selector` gate | `ci.yml:554-561`; log `#scrub` | yes |
| N3 | `open.setLen(0)` + closed-port test | `decide.nim:185`; `test_sheet.nim:235-265` | yes |
| N4 | `gameRecord` reads `abandon_after` | `replay.nim:238-254`; test rebuilt | yes |
| N5 | 7 stats, per-round chain, GV02 | `world.nim:1537-1544`; `replay.nim:289-298` | yes |
| N6 | seed perturbs `spec.randomSeed`, 3 seeds | `test_knob_sensitivity.nim:38,56-58` | yes |
| N7 | GV03, `never` distinct | `kit.nim:75`; `sim_types.nim:23-28` | yes |
| N8 | fixture links page CSS, harness-driven | `ci.yml:599-625`; fixture `:41,209-213,250-258` | yes |
| N9 | documented, engine order, no code change | `docs/RULES.md`; Tier A/B green | yes |
| N10 | prompt + preamble + fallback_detail in replay | `replay.nim:80-95,128` | yes |
| N11 | NOTICE with pinned commits | `NOTICE:1-20` | yes |
| N12 | documented; labels pinned | page `:3060-3068` | yes |
| N13 | CLI validates template; 2 real manifest defects fixed | `ci.yml:182-203`; manifest `owner` :13, `requests.memory` :417 | yes |
| N14 | `truncateBytes` | `sim_types.nim:130-145`; `sheet.nim:308` | yes |
| N15 | `applyBeatSpoilers` | page `:2831-2843` | yes |
| N16 | documented; upstream bot really is move-only | `scaffold.nim:1-15`; `docs/PARITY.md` | yes |

The fixes file's claims all check out against the tree and the CI logs; no test was weakened
(verified independently from `git log -p -- tests/`, not from the fixer's assertion).

## Non-blocking observations

1. **Endcard re-arm race on scrub-back from FINAL.** While parked at the end, `bc_frame` keeps
   posting `ph:'gameover'` frames; a scrub click dismisses the card, but one stale in-flight
   `advance` text can re-arm it (`renderEndcard` re-fires because `endcardShown` was cleared) before
   the seek's own frame (non-gameover, which never dismisses) arrives. The card would then sit over
   mid-match playback until the next seek/keyboard press. Every seek path *does* call
   `dismissEndcard()` — the letter of 14(c) — and this is a runtime ordering property no gate covers
   (the smoke seeks forward only) and I cannot reproduce from the tree. Suggest: dismiss the card in
   `onText` whenever `s.ph !== 'gameover'`. Not tied to a falsified checklist item.
2. **`canvas_text.total = 0` on both smoke steps** — architecturally inevitable (OffscreenCanvas
   worker; model text in DOM). The fixture's DOM containment gate is the effective legibility check;
   worth keeping in mind that the `canvas_text` line in this repo will never say anything.
3. **`ReplayFormatVersion` still 1** after additive fields (`hash_chain_rounds`, `seats[].prompt`,
   `prompt_preamble`, `fallback_detail`). Safe because `GameVersion` (GV03) already refuses older
   recordings, but bumping it would be the cleaner record (the fixer noted this too).
4. **Checklist item 10's example shape says `"type":"text"` for `game.docs`; the repo uses
   `"type":"uri"`.** The authority I used is the publishing CLI's own validator, which accepts the
   template in CI; test_manifest pins the `{type,value}` object shape.
5. **Parity oracle speed** (reviewer's open question): the new run shows per-map-distinct winners
   and rounds, a Tier C first-divergence at round 915 on `arrows` only, and identical traces on the
   other four — results that cannot be produced by empty or truncated traces, since the same trace
   files feed the Tier A/B byte-diffs that pass and the Tier C diff that fails at a specific row.
   I consider the oracle real; ~1 s per headless small-map game with a trivial bot is fast but not
   impossible, and the artifact (`parity-traces`) is uploaded for inspection.

BLOCKING: 0
