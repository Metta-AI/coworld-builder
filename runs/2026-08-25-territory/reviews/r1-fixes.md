# r1 fixes — cogame-territory

Head: `62a31b0a52c16042830ef3324f8df16106a2000e` (branch `main`)
CI: https://github.com/Metta-AI/cogame-territory/actions/runs/32846969302 — **success**
(`test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓; 33 test files / 199 tests passed, 0 skipped)
Range fixed: `07f0ebc..62a31b0` — 9 commits, one per finding (plus one test-only follow-up on O1).

| finding | disposition | commit | files |
|---|---|---|---|
| O1 | fixed | `8c796f9` (+ `62a31b0`, test only) | `src/game/rederive.ts` (new), `src/client/App.tsx:92-115,153-158,180-190`, `src/game/replay.test.ts`, `src/client/client.test.tsx`, `src/client/fixture/scenario.ts`, `.github/workflows/ci.yml:227-256` |
| O2 | fixed | `308e358` | `packages/llm/src/robust-decide.ts:70-91`, `packages/llm/tests/robust-decide.test.ts` (new) |
| O3 | fixed | `7c75813` | `src/shared/engine/orders.ts:53-77`, `packages/coworld/src/remote-pilot.ts:157-165`, `packages/core/src/runner.ts:25-49,553,559,753,827`, `packages/core/tests/runner-transcript.test.ts` (new), `src/shared/engine/text.test.ts` |
| O4 | fixed | `a30ab47` | `src/client/styles.css:7-28`, `src/client/fonts/*.woff2` (new), `src/client/no-external-origin.test.ts` (new) |
| O5 | fixed (constants CHANGED by the sweep) | `640a207` | `src/game/scripted.ts:14-31,95-124`, `src/game/tune.ts` (new), `src/game/tune.test.ts` (new), `scripts/sweep-baselines.ts` (new), `docs/baseline-sweep.md` (new), `src/game/scripted.test.ts:130` |
| O6 | fixed | `ea0e71d` | `src/client/fixture/main.tsx:36-118`, `src/client/fixture/selfcheck.test.tsx` (new) |
| O7 | DEFERRED (judge) | — | `coworld_manifest_template.json`, `src/game/coworld.ts:406` |
| O8 | DEFERRED (judge) | — | `src/game/coworld.ts:445` |
| O9 | DEFERRED (judge) | — | `index.html:21`, `src/client/styles.css` |
| A1 | fixed (advisory) | `c044b05` | `packages/coworld/src/remote-pilot.ts:26-31` |
| A10 | fixed (advisory) | `2749fc3` | `src/client/App.tsx:176-190` |
| A17 | fixed (advisory, inside O3) | `7c75813` | `src/shared/engine/orders.ts:53-77` |
| A2–A9, A11–A16 | not fixed | — | reasons below |

Nothing was weakened to go green: no test deleted, no assertion relaxed, no `skip`. The one
existing assertion I touched (`scripted.test.ts:130`) was re-pointed from the literal `2` to the
tuned constant `RAIDER_PARAMS.minYield` it stands for, in the same commit that tuned it.

---

## O1 — the viewer rendered recorded snapshots; nothing re-derived, nothing tested

**Checklist item 2.**

*Before:* `App.tsx:185` handed `snaps[index]` — a recorded snapshot object — straight to the panels.
No `stepTurn` / `resolve` / `upkeep` / `generateBoard` anywhere in `src/client/**`, and the reviewer's
bundle grep was right: the engine's rule strings were in the *fixture* chunk only, not in the chunks
`index.html` loads. No test replayed recorded events through the sim.

*Now:* `src/game/rederive.ts` replays the recorded **events** through the sim:

- the first `snapshot` frame supplies `(seed, variant, turns)` (the seed is in `config` **and** in
  every snapshot);
- each `actPrompt` frame's accepted attempt (`error === null`) supplies that seat's submission for
  that turn, parsed with `SubmissionSchema`; `usedFallback` marks the turns where the runner
  substituted its own `baselineDecision`, and those replay as the same baseline;
- it replicates exactly what the seam does around `stepTurn` — bounce a set the board would reject
  (`rejectionReason`), count a `fallback` submission on the seat (the snapshot carries that counter),
  then step the gathered set — and compares each re-derived state against the recorded snapshot,
  frame by frame, reporting the first divergence rather than hiding it.

It deliberately does **not** import the game seam: `src/game/game.ts` reaches `@cogweb/core`, whose
index pulls express and `node:fs`; I hit that as a hard rollup failure (`"join" is not exported by
"__vite-browser-external"`) and moved the re-derivation onto the pure engine, which is also what
keeps the viewer bundle browser-only.

`App.tsx` runs it in replay mode (fetched *and* injected) and **replaces the store's snapshot
timeline with the re-derivation**, so every panel — board, scorebug, ledger, turn log, scrubber —
reads a re-simulated frame. `data-replay-rederived` reports the outcome: `"true"` every recorded
frame reproduced, `"mismatch"` the re-derivation still stands but a frame differed, `"false"` the
recording is not re-derivable (no `actPrompt` frames) and the recorded snapshots stand. It is set the
moment it is known, not inside the load `requestAnimationFrame`.

*Evidence:*

- `src/game/replay.test.ts` — over a **real** episode (real host, nine real player processes on the
  real `cogweb.player.v1` bridge) the re-derivation reproduces **all 19** recorded frames:
  `mismatch === null`, `verified === 19`, and each re-derived snapshot deep-equals the recorded one.
- `src/game/replay.test.ts` (commit `62a31b0`) — the viewer's *adoption* condition holds on those
  same bytes: decoded through the client's own decoder into the client's own store, recorded
  timeline length 19 === re-derived length 19. So the browser adopts, it does not fall back.
- `src/client/client.test.tsx` — with **every recorded snapshot tampered** (`banked: 999`), the
  mounted page still shows the sim's numbers (no `999` in any `.plate-score`) and reports
  `data-replay-rederived="mismatch"`; untampered it reports `"true"`.
- `ci.yml` new step *"Assert the REPLAY PAGE carries the sim it re-derives with"* walks
  `index.html`'s own module graph and fails unless an engine-only runtime string
  (`"rubble is never claimable again"`, from `rejectionReason`) is reachable from it. In the green
  run: `index.html reaches 4 chunk(s) … re-derivation OK: the sim is in the replay page's module
  graph`. Dropping the import can no longer ship green.

## O2 — a transport failure was rethrown instead of retried-then-scripted

**Checklist item 8.**

*Before:* `robust-decide.ts:75` — `if (!isCredentialsUnavailable(err)) throw err;`. A throttle, socket
reset, 5xx or request timeout left the loop by throwing: not re-prompted, never reaching
`opts.baseline()`. Traced out through `makeLlmDecide` → `player-runtime` → `run()`, it terminated the
player process, so one throttle cost that seat the rest of the episode (host holds, then the pilot's
breaker benches the slot).

*Now:* the credentials case is unchanged (record, baseline immediately, no retry storm). Every other
transport failure is recorded as an attempt and **retried exactly once** (`MAX_ATTEMPTS = 2` in
`src/game/player.ts`); on exhaustion the loop falls out to `baseline()` = `fallbackMove` = the seat's
**scripted move**, counted in `results.fallbacks[seat]`. Nothing throws out of `robustDecide`.

*Evidence:* `packages/llm/tests/robust-decide.test.ts` (new, 4 tests) — throttle-then-success returns
the reply after 2 calls with both attempts in the transcript; throttle-then-throttle returns the
scripted baseline and does not throw; a no-credentials error returns the baseline after **1** call;
the pre-existing unparseable-reply ladder still retries once then falls back.

## O3 — the recorded transcript reached the replay uncapped; the capped note was dead

**Checklist item 9.** Three separate leaks, all closed:

1. `SubmissionSchema` (`src/shared/engine/orders.ts`) now applies the caps its own docstring already
   promised — lines past `MAX_LINES` dropped, `text` → `capText(…, MAX_SAY_LEN)`, `note` →
   `capText(…, MAX_NOTE_LEN)`. This was also advisory **A17** (a player was free to send a 1 MB
   note); the cap now bites at the parse boundary, which is what the design note's reply-schema table
   specifies.
2. `remote-pilot.ts` records the **accepted, validated** decision as the attempt's `response`, so the
   transcript that lands in the replay carries the **capped** `note` and talk lines — the value the
   note says "rides the `actPrompt` transcript". A *rejected* candidate is still recorded raw (it is
   the evidence for the rejection) and is bounded by (3).
3. `runner.ts` rune-caps every attempt string at the single choke point they all pass on the way to an
   `actPrompt` frame (`recordAttempt`, plus the runner's own timeout / error pushes): prompt 16,000
   runes, response 4,000, error 500 — generous by design (today's real prompt is 14,947 chars and
   passes through untouched), bounding a pathological reply rather than reshaping a normal turn.

*Evidence:* `packages/core/tests/runner-transcript.test.ts` (new) — a pilot recording 20,000 emoji of
prompt, 9,000 of response and 900 of error yields exactly 16,000 / 4,000 / 500 **code points**, each
ending in `…`, with **no lone surrogate**, and the serialized frame round-trips under
`new TextDecoder("utf-8", {fatal:true})`; a normal-sized attempt is byte-identical.
`src/shared/engine/text.test.ts` — the schema caps a 360-rune CJK+emoji note to 120 runes on rune
boundaries, drops the 4th..7th talk lines, caps each surviving line to 200, and leaves a short note
(and an *absent* note) alone. Side effect visible in CI: the smoke replay shrank from 3,593,980 B to
3,579,349 B.

## O4 — the viewer fetched fonts.googleapis.com

**Checklist item 3.** The inherited `@import url("https://fonts.googleapis.com/…")` is gone. Both
families are declared locally against the `latin`-subset **variable** woff2 (weight 400–700) that
Google Fonts serves, committed as `src/client/fonts/{space-grotesk,jetbrains-mono}-latin-var.woff2`
(22 KB + 31 KB); `assetsInlineLimit: MAX_SAFE_INTEGER` inlines them as data URIs, so the built CSS
carries no URL at all and the typography — and therefore the fixture's `scrollWidth` metrics — is
unchanged rather than degraded to system fonts. Non-latin text (the CJK + emoji talk lines) falls
through to the `system-ui` / `ui-monospace` stack exactly as before.

*Evidence:* `src/client/no-external-origin.test.ts` (new) fails on any absolute `http(s)` URL in
either stylesheet or any of the three shipped shells, and asserts both font files exist, are real
woff2 (`wOF2` magic) and are the ones the CSS names. On the built bundle,
`grep -ro "https\?://" dist/index.html dist/assets/*.css` is empty. The green `wasm-viewer` job
re-ran the renderer fixture at 360/720/1280 px with the local fonts: `{"ok":true,"widths":[360,720,1280]}`.

## O5 — the baselines were guessed; they are tuned now, and the sweep changed one

**Checklist item 7, second sentence.**

The three free numbers are named constants (`HOMESTEADER_PARAMS.maxClaims`,
`RAIDER_PARAMS.maxClaims`, `RAIDER_PARAMS.minYield`), both baselines take them as an optional
argument, and `src/game/tune.ts` sweeps the **whole meaningful grid** — `maxClaims 1..8` (the
`MAX_ORDERS_PER_TURN` bound), `minYield 1..3` (the yield range) — over five seeded **full 18-turn
nine-seat** episodes of the certification mix (five homesteaders, four raiders). Each candidate is
scored by the mean banked score of the seats that played it, with the *other* baseline held at a
fixed **reference field** (the pre-tuning numbers) so tuning one policy cannot move the other's
table — without that the "argmax" depends on which order you sweep in (I hit exactly that: holding
the opponent at the shipped values moved the homesteader table by 3 % after the raider changed).

Selection rule, stated in the table and enforced by the test: **the smallest parameters whose mean is
within 3 % of the grid's best** — above three claims the curve is flat (the extra claims are rarely
affordable), and a shorter order list is cheaper on the wire and in the prompt.

I did not fabricate a win. The sweep moved the raider:

| policy | shipped before | mean | argmax | mean | shipped now | mean |
|---|---|---|---|---|---|---|
| homesteader | `maxClaims=3` | 202.28 | `maxClaims=7` | 207.56 | `maxClaims=3` (−2.5 %, smallest in band) | 202.28 |
| raider | `maxClaims=3 minYield=2` | 164.20 | `maxClaims=8 minYield=3` | 187.15 | **`maxClaims=4 minYield=3`** (−2.9 %) | 181.80 |

The old raider point was **12.3 %** under the argmax, far outside the band; the new one is **+10.7 %**
on the old, and most of that comes from razing only yield-3 tiles. **This deviates from the design
note in two numbers** (§Scripted baselines says "≤ 3 claims" and "effYield ≥ 2" for the raider, and
"≤ 4 orders" for both — the tuned raider can emit 5). I am flagging it rather than hiding it: the
brief instructed me to ship the sweep's winner if the shipped constants lost, the note's numbers were
the guess the checklist item objects to, and I may not edit the note. `homesteader` is unchanged, so
the note's homesteader algorithm still reads literally true.

*Evidence:* `docs/baseline-sweep.md` — the committed 8-row + 24-row table with every mean, generated
by `scripts/sweep-baselines.ts`. `src/game/tune.test.ts` re-runs the same sweep in CI and asserts the
harness's **selection is the shipped constants** (plus: no smaller-claim candidate is inside the
band, episodes are byte-deterministic, and the tuned raider still fits `MAX_ORDERS_PER_TURN`). It
costs ~230 s of pure engine in the `test` job (the job is now ~4 min, timeout 30) because the
objective is the real one — whole episodes, not a proxy.

## O6 — the fixture never checked its own strings

**Checklist item 15, final bullet.** `checkStrings()` now runs **inside** `checkDom`, so it runs at
every width in the real browser, and reports a finding when: `fullCapLine()` stops producing
`MAX_SAY_LEN` runes; the scenario emits fewer lines than there are seats; any mounted line is short
or is not present **whole** in the rendered DOM; or fewer than `SEATS` `.cg-msg-body` rows are
actually laid out at the cap.

*Evidence:* `src/client/fixture/selfcheck.test.tsx` (new) runs the fixture's own
`window.__territoryFixtureCheck()` in jsdom and asserts zero string findings over the real scenario
(jsdom has no layout, so only the string class is assertable there — the browser gets both). I
verified it bites: shortening `fullCapLine` by three runes produces `short generator` plus one
`short string` per line. The green `wasm-viewer` job ran the real fixture at all three widths after
this change: `{"ok":true,"widths":[360,720,1280]}`.

---

## Section B — left for the judge, with the reasoning

### O7 — `replay_viewer.bundle = "build/static-replay-viewer"` — DEFERRED

Not changed, deliberately. The **basename is exactly** `static-replay-viewer`, the live base declares
the byte-identical string (`coworld-cogherence/coworld/coworld_manifest_template.json:22`),
`scripts/build-static-replay-viewer.sh` refuses any output path not ending in
`/build/static-replay-viewer`, and `coworld build --project .` resolves the value package-relative.
A "cheap change" here is not cheap: dropping the `build/` prefix would point the manifest at a
directory the build hook never writes, i.e. break the thing the item is about. The literal string in
the checklist is the *basename*, and it is present.

### O8 — `game.docs.readme.type = "uri"` — DEFERRED

Not changed. The lineage's own manifest schema (`packages/coworld/src/manifest.ts:18-21`) defines
`ContentRef` as `text | uri`, and the live base ships `"uri"` for the same field. The only way to
make the literal `"text"` true is to inline the whole README into the generated manifest **and** edit
`coworld.test.ts:112`'s assertion — changing an assertion to satisfy a literal is exactly what I am
not supposed to do, for a field the platform accepts either way. Everything else in item 10 is met
exactly (three `docs.pages` as `{type:"text"}`, both protocols `{type:"text"}` and > 200 chars).

### O9 — item 14's transport mechanics / the `<base>` script not byte-for-byte — DEFERRED

Not changed. `--band`, `--hudscale`, `relayout()`, `#endcard.on`, `#viewpanel`, `attachMinimap` are
another lineage's identifiers; this shell's equivalents are structural (`.app` is
`position: fixed; inset: 0` flex-column with three children, so the transport band **cannot** be
overlaid, and `.cg-endcard` is `position: absolute` inside `.cg-stage`), and `packages/ui/src` is
byte-identical to the base with a checked-in SHA-256 manifest test proving it. The one literal
divergence — `index.html:21`'s `<base>`-recovery regex matching `/seat/\d+` instead of `/cog/[^/]+` —
tracks Territory's own route rename (`src/client/ui/nav.ts`); reverting it to the base's bytes would
break `<base>` recovery on every `/seat/N` route, which is a functional regression in exchange for a
literal. Worth noting for the judge: `src/client/styles.css` did change in this round (O4), so
"inherited verbatim" is now false for the font block too — by design, because the inherited bytes
were the second origin item 3 forbids.

---

## Section C — advisory dispositions

**Fixed** (cheap and clearly right):

- **A1** — `RemotePlayerPilot.MAX_ATTEMPTS` 3 → 2, the number the note's degrade table and its
  Bedrock budget arithmetic both declare (9 requests per 22 s = 24.5 rpm under the sidecar's 30 rpm
  cap; a third request per seat per turn breaks it). Commit `c044b05`.
- **A10** — a replay that fetched fine and decoded to zero snapshots now sets `data-replay-error` and
  renders the `loadError` paragraph instead of sitting silently on "Loading replay…". Commit
  `2749fc3`.
- **A17** — folded into O3 (the reply schema now bounds `note` and `messages[].text`).

**Not fixed**, one line each:

- **A2** (no `endcard` frame on the `deadline` settle path) — the fix is in the runner's settle path
  (emit the `TurnRecord` `settleEarly` appended), on a path CI never produces; the viewer already
  degrades correctly via `store.status.ended` + `FinalScores`' snapshot fallback. Real but not a
  checklist item, and not a change I would make untested.
- **A3** (`voided {reason:"owned"}` unreachable) — dead but declared, handled in the viewer, and the
  note lists the case; deleting it would diverge from the note for zero behaviour.
- **A4** (host-side `onTalk` emit uncapped) — dead code in this game (`talk` is never passed;
  Territory's talk rides the engine, where it *is* capped). Capping it would be capping a path
  nothing reaches.
- **A5** (`players[].player` hard-coded `null`) — there is no platform-supplied player identity on
  the host side to read; `policy` carries the injected name and is what the viewer maps. Needs a
  platform contract, not a code change.
- **A6** (salvage banked in Resolve, not Upkeep 9c) — the *spendable* half is correct (credit only
  becomes paint next turn); moving the score bookkeeping changes recorded scores for a
  same-turn-eliminated salvager. Behaviour change, not a fix.
- **A7** (`elimination` outranks `complete` on the final turn) — the note states no precedence and
  both are healthy ends.
- **A8** (no explicit timeout on artifact IO) — undici's ~300 s default already bounds it; a hard cap
  on a presigned PUT of a 3.5 MB replay risks losing results, which is worse than the unbounded-in-
  principle wait. Not clearly right.
- **A9** (`#decideSeat` wait unbounded when `autoAdvance.enabled === false`) — Territory always sets
  it `true` (`server.ts:70`); the two tests that disable it do so to write the barrier assertion.
  Structural change to a vendored runner for no production gain.
- **A11** (13 base test files not carried over) — a fork-boundary delta, not a loosening in this
  history; writing 13 test files is a phase-20 scope expansion, not a review fix.
- **A12** ("at least one gap per room") — the *test* is right and the note's "exactly one" is the
  loose statement; the precedence rule genuinely permits more than one opening.
- **A13** ("200 seeded views" is 200 checks over 25–30 states) — both loops are substantive
  (~50k predicate comparisons); rewording is the note's problem, not the code's.
- **A14** (3.58 MB replay, two thirds `actPrompt` prompts) — O3's response cap trimmed ~15 KB; a real
  cut means capping the *prompt* hard, which loses the spectator transcript item 8 wants. Left, with
  the first-paint measurement standing at 583 ms in the green run.
- **A15** (`viewer_smoke.mjs` does not gate on the three scrub readouts differing) — the file is
  **byte-identical** to `coworld-builder/templates/tools/ci/viewer_smoke.mjs`; editing it would
  destroy the provenance the reviewer verified, for a check the reader already performs (they do
  differ: `Turn 4 / 11 / 13`).
- **A16** (stale pilot timer can null a newer `#pending`) — inherited, requires a `paceMs: 0` run
  with a real 20 s reply timeout to exercise; I could not construct that run, so I would be changing
  a race blind.

## NOTED (not fixed) — seen while working, outside this round's findings

- `raider`'s target filter reads `tile.yield` (base yield) where the note says `effYield`; on a
  cracked tile those differ. Not a finding in r1, so untouched — but the tuned `minYield = 3` now
  makes the distinction more visible.
- `App.tsx`'s `useRef(() => …)`-style initializers re-run their argument on **every** render, so an
  injected replay re-applies all its frames per render (inherited). I worked around it for the
  re-derivation (a guarded one-shot) rather than changing the inherited pattern.
- The load-signal effect's `requestAnimationFrame` is cancelled by the follow effect's `setIndex` in
  jsdom, so `data-replay-loaded` never fires there (it does in a real browser — the CI signal is
  `true`). That is why `data-replay-rederived` is set outside the rAF.
