# r1 fixes — negotiation-games

Repo: `Metta-AI/cogame-negotiation-games`
Head: `04f7a60c32db9e361249218080ef2ef2c992a406` (main)
CI: https://github.com/Metta-AI/cogame-negotiation-games/actions/runs/33024746218 — **success**
(`test`, `docker-smoke`, `wasm-viewer` all green; `--strict-text-bounds` on both browser runs).
Previous green run on the first seven commits: run
[33024465799](https://github.com/Metta-AI/cogame-negotiation-games/actions/runs/33024465799) at
`07b09aa` — also success.

Pushed through the Git Data API (blobs → tree → commit → `PATCH refs/heads/main`); plain
`git push` to this repo is refused. One API commit per finding, in order.

| finding | disposition | commit | files |
|---|---|---|---|
| F1 (blocking, checklist 9) | fixed | `3fd0517` | `src/negotiation/sim.nim:42-46,123-124`, `src/negotiation/server.nim:25,33-34,489-508`, `tests/test_sim.nim:459-476` |
| F2 (blocking, checklist 15) | fixed | `362f623` + `04f7a60` | `client/renderer.js:72-136,398-444`, `tools/ci/renderer_fixture.html:52-100,289-322` |
| F3 | fixed | `f39a734` | `src/negotiation/sim.nim:188-193,290-294` |
| F4 | fixed | `f706bb0` | `client/renderer.js:293-322,459-479,499-501` |
| F5 | fixed | `b14a236` | `client/renderer.js:335-365,676-692,712-726,865-867` |
| F6 | fixed | `1f3c2a3` | `client/renderer.js:523,763-777,813-815` |
| F7 | REFUTED (no change) | — | `client/chrome_common.js:53,105,201,296` |
| F8 | REFUTED (no change) | — | `client/chrome.css:1-441` |
| F9 | REFUTED (no change) | — | `src/negotiation_player.nim:55-56` |
| F10 | partly fixed, partly refuted | `07b09aa` | `src/negotiation/llm.nim:204-206` (deleted) |

---

## F1 — the 4000-char player prompt was cut on a byte boundary  (`3fd0517`)

**What it did.** `server.nim:492-493` ran `if prompt.len > MaxPromptLen: prompt = prompt[0 ..<
MaxPromptLen]`. Both `len` and the slice are **bytes** in Nim, so a prompt whose 4000th byte
falls inside a multi-byte rune was cut mid-rune, stored at `server.nim:503` and interpolated
verbatim into the model request body (`llm.nim:295-299` → `llm.nim:412-415`) as invalid UTF-8.
The delivery log line printed that byte count as "chars".

**What it does now.** `MaxPromptLen` moved to `sim.nim` beside `MaxMessageLen` / `MaxNotesLen`,
with `cleanPrompt* = capRunes(text, MaxPromptLen)` beside `cleanMessage` / `cleanNotes`. The
handler calls `cleanPrompt(payload{"prompt"}.getStr())`, so the prompt is cut on a rune boundary
with the cut marked, exactly like every other string the tree keeps; the log line reports runes.

**Why that resolves it.** Checklist item 9 requires prompts to be truncated on rune boundaries.
`capRunes` (`sim.nim:107-114`) cuts with `runeLen`/`runeSubStr`. The finding also required a
test, which the review noted did not exist.

**Evidence.** New case in test 12 feeds `MaxPromptLen + 500` × `é` and asserts
`runeLen == MaxPromptLen`, `validateUtf8 == -1`, a trailing `…`, and byte length > rune cap, plus
a prompt exactly at the cap coming back whole. CI run 33024746218, `test` job, debug **and**
`-d:release`:

```
[Suite] 12. rune-safe caps
  [OK] a multibyte operator prompt caps in runes, not bytes
```

---

## F2 — the full-cap remark was one ellipsized line in a box sized by eye  (`362f623`, `04f7a60`)

**What it did.** `renderer.js:307-313` drew the seat's public message — capped server-side at
`MaxMessageLen = 200` runes — as a single `negLabel` clamped to `maxWidth: w * 0.3`, which
`C.ellipsize` cut with `…`. No wrap, no reserved band, and the box was a fraction of the canvas
width rather than anything derived from the cap. CI corroborated it: 265 ellipsized draws and
"longest 66 chars" against a 200-rune cap. Worse, `renderer_fixture.html:305-309` **required**
`totals.ellipsized > 0`, i.e. cutting the remark was the fixture's pass condition.

**What it does now.**

*Renderer.* `negStage` computes the band before it draws anything into it:
`negTalkBand(ctx, talkW, scale, maxHeight)` wraps a `MAX_MESSAGE_RUNES`-long worst-case sample
(the widest glyph the face draws, in words, so wrap waste is measured too) in the font the remark
is drawn in, and steps the font down until those lines fit the band. The pool row is then placed
**below** the band (`rowY = min(h*0.72, max(h*0.66, talkTop + band.height + 20*scale))`) whether
or not anyone is speaking, so the scene cannot jump when a remark lands. `negWrapLines` wraps the
message into that band; every line is already inside the box, so `ellipsize` cannot fire on it.
The follow-up commit widened the band to `0.42w` and let it push the pool row as far as `0.72h`,
because the first shipped version fitted the cap by shrinking the font to ~7 px — fitting the cap
is necessary, not sufficient.

*Fixture.* `renderer_fixture.html` now reads the full-cap message off the fixture replay
(`selfCheck`) and, in its `fillText` hook, tracks the longest run of consecutive drawn fragments
of that message (breaks count the space the wrap consumed) plus any fragment that came back
ellipsized. It fails if a remark fragment is ellipsized, and fails if the longest run is shorter
than the 200-rune cap. Ellipsis stays legal for labels; `never_inside` stays strict
(`--strict-text-bounds` unchanged).

**Why that resolves it.** Checklist 15: the band is *reserved in the layout*, *sized from the cap
the server enforces*, and *measured in the font it will be drawn in*; `ellipsized` no longer
counts a single remark.

**Evidence.** Run 33024746218, `wasm-viewer`:
`canvas text: 2742 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized
(--strict-text-bounds)`, and the fixture's own caption in `renderer-fixture/viewer-smoke.png`:

```
renderer fixture OK — 360 / 720 / 1280 px, 2586 canvas strings drawn,
200 / 200 remark runes drawn, 0 ellipsized (labels only), longest 91 chars, 0 never inside
```

(before: `1579 canvas strings drawn, 239 ellipsized, longest 66 chars`). The screenshot shows both
seats' remarks as three wrapped lines each, complete, ending in `…négocions—jé négoc"`.

---

## F3 — two RNG streams under a comment claiming one  (`f39a734`)

`tableNames` seeded its own `Rand` (`seed * 6779 + 31`) while `initSim` seeded a second
(`seed * 7919 + 17`), directly under "One stream for everything the seed decides". The note pins
one stream in one order: aliases, then each match's pool and values. `tableNames` now takes the
stream (`rng: var Rand`) and `initSim` draws the aliases from it before `drawSchedule`.

Determinism and replay re-derivation are unaffected (both were already pure functions of the
seed); the aliases and schedules a given seed produces do change, which is why this needed CI.
Evidence: the whole `test` job is green, including the seeded grid measurements —
`haggler-vs-haggler: 102/102 deals, mean joint 14.79`, `haggler vs hardliner behaviour differs in
97/102 matches`, `mixed matches: 100, hardliner mean 8.11 vs haggler mean 6.26` — and
`docker-smoke` replayed a full episode: `replay_check: OK — 47 events, 6 matches, 6 deals,
reason=complete`.

---

## F4 — `view.effects` was computed and discarded  (`f706bb0`)

The chrome computes `view.effects.at` every frame (`chrome_common.js:165-183`, `:391-398`) and
`effectResetKinds: ["match"]` was registered, but the painter never read either: every frame was
a static redraw, and the note's "a new offer slides in and holds" / "[the stamp] holds for the
pacing delay" were not implemented.

`negAge` / `negEntrance` read the effect table; the standing split now slides in from the seat
that offered it and fades up over 320 ms, and the stamp lands over 260 ms and holds until the
next match's `match` event wipes the table. A scrub jump reports `null` for the kind (only the
newest event animates), which both helpers read as "already settled", so seeking still paints the
settled frame immediately. Deliberately, nothing moves a text box: only the pool row's x and the
stamp's alpha, so the text-bounds gate is unaffected — confirmed by `0 never inside` and
`soak.moved: true` in run 33024746218.

---

## F5 — three strings differed from the note's copy  (`b14a236`)

- No-deal stamp: was `NO DEAL` + `<maxTurns> TURNS, NO AGREEMENT`; now also `0 – 0`.
- Deal stamp: was `DEAL` + `7 – 3`; now also the final item split
  (`SPLIT 2 · 1 · 0  vs  1 · 1 · 2   (BOOKS · HATS · BALLS)`).
- Feed `end` line: was `Final — N matches played.`; now
  `Final — Sprocket 25 pts (0.62) · Gizmo … · Ratchet ….`

`negStamp` now lays its lines out relative to the stamp box rather than at fixed canvas
fractions, so the third line stays inside the box at every width. The feed's per-seat totals are
accumulated from the `matchEnd` payoffs the feed pass already walks, with
`score = points / (10 · matches that seat played)` — the same arithmetic `sim.score` uses
(`sim.nim:361-364`), so the line agrees with the endcard. Evidence: the fixture drives both
stamps at 360 / 720 / 1280 px (`selfCheck` refuses a replay without both) and reports
`0 never inside`.

---

## F6 — the matchbar counted started matches, not scheduled ones  (`1f3c2a3`)

`negMatchbar` derived its chip count from emitted `match` events, so a `deadline` replay (whose
unstarted matches emit no `match` event, `server.nim:301-311`) showed fewer chips than the
schedule and the `pending` chip class could only ever mark a started-but-unsettled match. The
scheduled count now comes from `state.matches` (= `config.matches`, carried by every state) and
from the config the clock is painted with; the event-derived count remains as a floor.

Evidence: exercised locally against a synthetic deadline event list (2 of 6 matches started) —
chips go from 2 to `DEAL 6–4 | NO DEAL | M3 | M4 | M5 | M6`. In CI the smoke replay is
`complete`, and the fixture screenshot shows six chips with `M6` pending.

---

## F7 — four defensive edits in `chrome_common.js` — REFUTED (no change)

The four sites are `if (!pending) { done(images); return; }` (`:53`), `String(text)` (`:105`),
`if (!element) return;` (`:201`) and `if (!container) return { update: … };` (`:296`). Each is a
guard on a **missing or empty input**; when the input is present — which it is on both shipped
pages, whose ids are frozen and gated by `chrome_check.py:47-58` — every one of them is
unreachable and the inherited body runs byte-for-byte as babel wrote it. Reverting them would
delete crash guards to satisfy a sentence in the note, which is a worse repo, and checklist item
14's concern (do not edit inherited bodies in ways that change behaviour) is not violated by a
guard that cannot fire.

The real divergence is on the **note's** side: §Chrome provenance says "three changes, which are
the whole diff" and there are seven (three named + two coordinator-accepted + these four). I am
not permitted to edit the design note, so this is filed here for the design owner as a note-side
correction, not a code change.

## F8 — inherited `chrome.css` uses literal px — REFUTED (no change)

The reviewer traced this one to its own conclusion: `chrome.css:1-441` is babel's, byte-identical
to the starter, and **leaving it untouched is exactly what checklist item 14 requires**; the
appended block (`:452-588`) does use `calc(… * var(--hudscale))`. Rewriting 441 inherited lines
into `calc()` to match a sentence in the note would be the checklist violation. Note-side wording
mismatch, no defect, no change.

## F9 — the player's blocking `receiveMessage` — REFUTED (no change)

`negotiation_player.nim:55-56` blocks in whisky's `receiveMessage` with the default
`timeout = -1`. The wait is bounded by the game's own bounded lifetime: the game sends `final` to
every seat before writing artifacts (`server.nim:193-205`) and then `quit(0)` after the shutdown
grace (`server.nim:223-227`); the loop exits on `final` (`:72-74`), on `none` (`:57-59`), or on
the raise a close frame produces, which `:79-80` catches and exits 0 — the playbook's own fix for
the cert `player_error` race, implemented. The shape is identical to the starter
(`cogame-babel/src/babel_player.nim:51-52`). Adding a timeout would add a second exit path with
no failure mode to close: CI run 33024746218 `docker-smoke` reports `all 3 player containers
exited 0`.

## F10 — three dead declarations — partly fixed, partly refuted  (`07b09aa`)

- **`scriptedAction` (`llm.nim:204-206`) — deleted.** An exported one-line wrapper around
  `scriptedDecision` that nothing called, that the design note never mentions, and that a caller
  reaching for it would use to bypass the fallback accounting `decide` performs around the same
  call. Dead and unnamed: removed.
- **`MaxMatchesCap` (`sim.nim:28`) — left in place.** The note pins it in §Sim module constants
  (`docs/plans/2026-08-26-negotiation-games-design.md:459`). Deleting it puts the code at odds
  with the note; making it load-bearing (clamping `sampleEpisode`'s cap at 6) would change what
  configurations are accepted — at `maxTurns = 2` the call budget currently admits 36 matches —
  and that is a design change, not a review fix.
- **`phaseText: negPhase` (`renderer.js:704`) — left in place.** It is an optional hook: the note
  lists it among the redirected hooks (`:675`, `:683`) and `chrome_common.js:13` documents it in
  the hook set. It costs one line, `negPhase` is still live through `negHeader`, and removing it
  would leave the register call inconsistent with both the note and the chrome's own contract.

---

## NOTED (not fixed)

- The design note needs three small corrections that only its owner can make: §Chrome provenance
  "three changes" (F7 — there are seven, all traced), §Legibility "every chrome font size and pad
  is `calc(… * var(--hudscale))`" (F8 — true of the appended block only), and §Sim constants
  listing `MaxMatchesCap`, which is declared and unreachable (F10).
- The manifest's player-protocol prose still reads "prompt max 4000 chars"
  (`coworld_manifest_template.json:241`, `tools/build_manifest.py:69`). The cap is now measured in
  runes; the number is unchanged and the wording is human prose, so I left the manifest (and its
  regeneration) alone rather than widen this round's diff.
- The remark band is drawn under both seats at every width. On a short stage (the shipped viewer
  gives the canvas ~440 px at 1280 px wide) the cap needs three lines at ~11 px. If the design
  ever wants a larger remark, the room has to come from the stage layout (cogs at `0.30h`, pool at
  `0.66h`), not from the band's fit loop.
