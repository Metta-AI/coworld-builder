# r1 fixes — 2026-08-25-daycare

Head: `948d5de5ca5d9a09b612b5eca0fea922cb8cc853` (`main`, `Metta-AI/cogame-daycare`)
CI: https://github.com/Metta-AI/cogame-daycare/actions/runs/32859893259 — **success**
(`test` ✓ 97841306518, `docker-smoke` ✓ 97841306328, `wasm-viewer` ✓ 97841825867)

Range reviewed → now: `12d58b5..948d5de`, six commits.

| finding | disposition | commit | files |
|---|---|---|---|
| **B1** (blocking) `config_schema` caps `tokens`/`players` at 1 in a 2-seat game | **fixed** | `b9bab64` | `coworld_manifest_template.json:39-53`, `tests/test_manifest.nim:186-224` |
| N13 / C3 the renderer fixture measures its own replica CSS, not the shipped page | **fixed** | `fd1eda8` | `tools/ci/renderer_fixture.html` (rewritten), `.github/workflows/ci.yml:326-360` |
| N4 the shrub-pick coin is seeded off `rngSecret` | **NEEDS-DESIGN** (fix written, CI-tested, reverted) | `79a5a66` then reverted in `948d5de` | `src/daycare/sim_state.nim`, `sim_types.nim`, `tests/test_noleak.nim` |
| N6 a child reach at a bare tall tree emits nothing | **NEEDS-DESIGN** (fix written, CI-tested, reverted) | `d210750` then reverted in `e8cc063` | `src/daycare/sim.nim`, `tests/test_sim.nim` |
| N5 the live `/global` frame carries `secret.pref` on an unauthenticated route | **DISPUTED in part / NEEDS-DESIGN in part** — no change | — | `src/daycare/broadcast.nim:159`, `src/daycare/server.nim:443-457,525` |

Net diff against the reviewed sha `12d58b5`: `ci.yml` +27/-11, `coworld_manifest_template.json` +4/-4,
`tests/test_manifest.nim` **+40/-0**, `tools/ci/renderer_fixture.html` rewritten. **No file under
`src/` or `client/` differs from the reviewed sha**, and `tools/ci/viewer_smoke.mjs` is still
byte-identical to the builder template (it was never touched).

**Checklist item 1, read honestly.** `git log -p -- tests/` over this round shows two commits that
*delete* test lines — the two reverts. Those hunks delete only assertions **added earlier in this same
round** (`test_noleak` gate (c2), `test_sim`'s bare-canopy block). Against the reviewed sha the
`tests/` diff is **+40 insertions, 0 deletions** (`git diff 12d58b5 948d5de -- tests/ | grep -c
'^-[^-]'` → `0`). No pre-existing assertion was removed, no tolerance widened, no skip added.

---

## B1 — `config_schema` caps `tokens` and `players` at one item in a two-seat game — FIXED (`b9bab64`)

**What the code did.** `coworld_manifest_template.json` declared `"tokens": {…"minItems":1,
"maxItems":1…}` and `"players": {…"minItems":1,"maxItems":1…}`, while all four `variants[].game_config`
and `certification.game_config` in the same document carry two `players`, `docker_smoke.sh` writes two
tokens and two players, and `src/daycare/server.nim:529-530` refuses to start with fewer than two of
either.

**What it does now.** Both maxima are `2` — the design note's value (`design.md:951-954`) and the seat
count `num_agents.maximum` already declares. The two `description` strings now say "Daycare seats two."

**Why that resolves the finding.** The published schema now admits every `game_config` the manifest
ships and the runtime config the runner injects, so neither reading of the finding survives: a
validator that applies `config_schema` accepts the fixtures, and a policy author reading the schema is
told the truth about the seat count.

**Evidence.** New test block `tests/test_manifest.nim:186-224` — "config_schema admits every
game_config this file ships" — ties `tokens`/`players` `maxItems` to `num_agents.maximum` and then
walks the four variants, the certification fixture and the runner-injected `{tokens, players}` shape,
asserting every key is declared and every array length is inside its declared `minItems..maxItems`.
Green in run **32859893259**, job `test` (`test_manifest: config_schema admits every game_config this
file ships`, both debug and `-d:release`). The old `maxItems: 1` fails that block (the first assertion
names it explicitly), which is what the reviewer observed nothing catches. Checklist item satisfied:
**10, manifest** (the item's subject, "manifest validates").

---

## N13 / C3 — the fixture now measures the shipped page, at real viewport widths — FIXED (`fd1eda8`)

**What the code did.** `tools/ci/renderer_fixture.html` re-declared the chrome CSS inline (its own
`#care-secret` / `.feed-row` / `@media` rules), resized `#stage` in px while the shipped
`@media (max-width: 640px)` keys off the **viewport**, and rendered a `.care-hunch` block and a feed
`.notes` span the shipped page never emits. It proved "the real chrome runs with full-cap strings
without throwing" and nothing about the shipped boxes — exactly the reviewer's (a), (b), (c) — and C3
("does a full-cap 80-rune hunch stay legible at a 360 px viewport?") had no gate at all.

**What it does now.** The fixture fetches `client/replay_broadcast.html`, splices the three script
markers exactly as `Dockerfile.replay-viewer`'s `sed` does (real `client/chrome_common.js`, real
`client/broadcast_core.js`, the nim-generated `CTF_WIRE` values inline, and `data/font.ttf` so the real
font metrics are measured), and loads that page in an **iframe at 360 / 620 / 1152 px of viewport
width** — an iframe has its own viewport, so the shipped media query fires. It drives the page through
the page's own `window.CtfStaticReplay` seam (the hook the static bundle uses), so the shipped page,
`chrome_common.js` and `broadcast_core.js` are untouched and the page's *own* care block, feed builder,
secret panel and `relayout()` do the rendering. Then, at each width, it asserts against the shipped
DOM:

- the full-cap 80-rune hunch reached **exactly two** feed rows (both seats) at full length;
- the guess tape is 15 chips and the panel drew `BRAMBLE WANTS` / `ALDER GUESSES` / `WRONG`;
- the clock reads `TURN 12 / 15` (spelled out, never `T12`);
- no measured box crosses a viewport edge, none leaves the board region between `--topband` and the
  transport band, and none overflows its own box (`scrollWidth/scrollHeight`);
- both plates still read their score with the name laid out;
- the **shipped** `@media (max-width: 640px)` rule is what hides the plate sublines at 360/620 and
  shows them at 1152 (`getComputedStyle(sub).display !== 'none'` must equal `width > 640`).

Measurements are taken after `document.fonts.ready` **and** after the starter's 250 ms `.feed-row`
entrance slide (`translateX(+30 * --u)`): a row measured mid-slide is legitimately off-frame
(checklist item 15's entrance-animation caveat), and measuring before the font arrived made the
numbers machine-dependent — the first draft of this fixture flapped for exactly those two reasons.

`ci.yml` serves the repo over local HTTP (`python3 -m http.server 8731`, polled with `curl` before the
run, killed on `trap … EXIT`) for that step, because the fixture must `fetch()` the shipped page and
Chromium blocks `fetch()` of a `file://` URL.

**Evidence (the CI run, not a local run).** Run **32859893259**, job `wasm-viewer`, step *Render the
worst-case chrome fixture*: `{"loaded":true,"ms":2050,…}` and artifact `renderer-fixture`
(`viewer-smoke.json`):

```
status: fixture ok: the shipped page at 360 / 620 / 1152 px viewports,
        hunch 80 runes on both seats, notes 240 runes, 15 chips
fixture  360px: widest feed row 211px at x 143..354 (font 4px),     secret panel 109x29 at x 246..355, board region 208..418, 4 feed rows, 15 chips
fixture  620px: widest feed row 392px at x 219..610 (font 6.528px), secret panel 140x43 at x 472..612, board region  47..409, 4 feed rows, 15 chips
fixture 1152px: widest feed row 528px at x 517..1045 (font 10.2px), secret panel 231x72 at x 817..1048, board region  58..623, 4 feed rows, 15 chips
data_replay_loaded: "true"   data_replay_error: null
```

**C3 is now determined**: with a full-cap hunch on both seats the shipped feed rows and the shipped
secret panel stay inside the frame and inside the board region at all three widths — nothing clipped,
nothing off-frame, nothing ellipsized.

**The gate has teeth** (negative control, run locally with the pinned Playwright 1.55.0 because it
must not be committed): handing the same fixture a 400-rune hunch makes
`viewer_smoke.mjs --strict-text-bounds` exit **1** with
`VIEWER SMOKE FAILED: data-replay-error: feed row 2 crosses the viewport edge (-351..354 of 360) at
360px` — the shipped `nowrap` feed row running off the **left** edge, i.e. cogchemists' failure mode
in DOM form. The old fixture could not have seen it.

Checklist items this serves: **15** (the worst-case renderer fixture, now measuring the shipped
layout, cited step + `canvas_text` line) and **11 / 13** as corroboration. `canvas_text` is still
structurally `0/0/0` and still means nothing here — Daycare's board text is server-side sprite art
(`src/daycare/art.nim:195-226`), so the fixture's own DOM assertions are the gate, and they fail the
job through `data-replay-error`, as the negative control shows.

---

## N4 — the shrub-pick coin is seeded off `rngSecret` — NEEDS-DESIGN (fix written, tested, reverted)

**The finding is real.** `src/daycare/sim_state.nim:112` derived `pickRng` from `rngSecret`'s stream
(`result.rngSecret.nextU64()`) while the note (`design.md:100-105`) and the same docstring say
"nothing the parent can observe is ever drawn from `rngSecret`" — and a shrub-pick outcome *is*
observed by the parent, in `reachFails` and in the `reach` event.

**The fix I wrote** (`79a5a66`): `pickRng = seededRng(seed xor PickRngSalt)` — its own seed-derived
stream, drawn from neither of the other two — plus `tests/test_noleak.nim` gate (c2) asserting the
first 32 pick draws are identical under a forced apple vs banana preference and identical between
`daycare` and `daycare-fickle` (which differ only in `preferenceSwitch`; the old seeding failed that
second half, so the code's own "a switch draw cannot shift the pick sequence" comment was false).

**Why it is reverted.** Any honest fix gives the coin a different stream, and the pick sequence is a
fresh sample of the economy. The note's feasibility oracle then rejects it — run **32858536635**
(sha `d210750`), job `test` 97836758403:

```
FAIL (c) pooled: with no behaviour to read the parent's guess accuracy is 0.672
         (want 0.35 .. 0.65 — chance)          [0.568 at the reviewed sha]
```

Gate (c) is the enforcement the note names, and a fixer may not widen it or split it per variant
(which is what review finding **N9** argues it should be). Hunting a `PickRngSalt` value that happens
to land inside the band is worse: that is tuning a constant against a statistical gate.

**The design decision this needs** (either one, not both): (i) accept the reseed and re-derive gate
(c) — including N9's per-variant reading — from the new stream; or (ii) state in the note that
deriving an observable's stream from `rngSecret`'s **head** is admissible, because both draws are
functions of one seed and the seed never reaches a seat, and fix the self-contradicting docstring
instead of the seeding. The reviewer's own analysis supports (ii): the preference value does not move
the stream (`rand(2)` consumes one `nextU64()` either way), so the fix removes a *byte-level*
dependency, not an information channel.

---

## N6 — a child reach at a bare tall tree emits nothing — NEEDS-DESIGN (fix written, tested, reverted)

**The finding is real.** `src/daycare/sim.nim:112` skipped any adjacent source with `ripe < 1`, so a
child picking at an empty canopy fell through to `wait` with no `reach` row and no counters, though the
note says the child's tall-tree pick "always fails and emits `reach`" (`design.md:114`, `:1036-1037`)
and the reach is the game's whole signalling surface.

**The fix I wrote** (`d210750`): a bare tall tree becomes a fallback target **for the child only**,
used only when no ripe adjacent source (of the order's species, if one is named) was found, so nothing
that could yield food is displaced; the parent is unchanged. Plus `tests/test_sim.nim`: 12 picks at a
canopy held at `ripe = 0` emit a reach row and 12 counted failed reaches, and the parent's pick at the
same empty canopy emits nothing at all.

**Why it is reverted.** Counting a bare-canopy attempt in `reachAttempts`/`reachFails` makes the
child's reach signal 2–3× louder, and the caretaker parent weighs it **cumulatively** by the note's own
formula (`design.md:553`, `3·reachFails + 2·groundPasses + adjacentTicks + 4·ate`). In
`daycare-fickle` the pre-switch reaches then drown everything the child does after the switch, so the
parent stops tracking the taste change — run **32858536635** (sha `d210750`), job `test`
97836758403:

```
daycare-fickle caretaker mean 80.5 (was 92.2)   guess 106/180 (was 121/180)
FAIL (a) daycare-fickle: 2/12 seeds complete with score >= par and the guess right on
         >= 10 of 15 turns (want >= 10/12)
FAIL (b) daycare-fickle: a stubborn (always-apple) parent scores 0.76 x the caretaker
         mean (want <= 0.70)
```

(The other three variants *improved*: `daycare` mean 119.2 → 126.5 with guess 178→179/180, `sparse`
108.5 → 121.0, `swapped` 87.5 → 102.0.) The note's repair ladder for gate (a) is already exhausted —
both named rungs (`ticksPerTurn 48→60`, `tallRegrowTicks 36→24`) are in the tree — so the next move is
a design change, not a constant.

**The design decision this needs** (either one): (i) a bare-canopy attempt emits the `reach` **event**
(the spectator-visible signalling surface, the feed row and the arms-up frame) without entering the
parent's behaviour table, which keeps the economy exactly as measured; or (ii) the caretaker's guess
weighting becomes recency-weighted so a fickle switch stays trackable with a louder reach signal — the
note pins the cumulative formula, so that is a note change.

**Worth knowing either way:** gate (a) on `daycare-fickle` sits on its threshold at the reviewed sha —
`121/180` correct turns is `10.08` per seed against a `>= 10` per-seed bar, and 10/12 seeds clear it.
**Any** perturbation of the seeded streams can flip that gate, in either direction, without anything
being wrong with the perturbation. That fragility is not a finding in this review, but it is the reason
both fixes above are un-shippable without a design call.

---

## N5 — `secret.pref` on the live `/global` frame — no change (DISPUTED as a code defect; NEEDS-DESIGN as a risk)

**Refuted as a code defect.** The note does not merely permit this, it **specifies** it:

- `design.md:898-900` — the broadcast frame contract: "`buildStateJson`: the starter's `teams`,
  `roster`, `lead`, `beats`, `over`, **plus the appended
  `secret: {"pref":"banana","guess":"apple","right":false,"tape":[…],"rightTurns":6}`**". That *is* the
  live `/global` frame (`src/daycare/broadcast.nim:111-117`, `:159`).
- `design.md:720` — the route table: `WS /global` is "live spectator: paintbot's sprite protocol + the
  chrome `TextMessage`", with **no** token, unlike `WS /player?slot=N&token=T` at `:719`; and
  `design.md:596` requires `/global` to keep answering after the episode because hosted certification
  pings it.
- `design.md:45` (the idea, verbatim) — "reveal the child's secret preference to spectators (not the
  parent) so the audience can see the parent guess right or wrong **in real time**".
- `tests/test_broadcast.nim` (design note item 8) asserts the `secret` block is present on the live
  frame, so removing it would fail a test I am not allowed to weaken.

The `design.md:697-698` sentence the finding cites — "written **after** the episode, so no player
process can ever read it" — is inside §Sim module *The replay file* and is about the replay's `secret`
block; the code satisfies it exactly (`src/daycare/replays.nim:107`, written in `finishEpisode`,
`src/daycare/server.nim:181`). The property the note makes mechanical for a *player* is that the
`daycare.player.v1` frames and the `final` frame carry no preference, and `tests/test_noleak.nim:37-96,
190-204` pins that.

**The residual risk is real and is a design change.** A policy image *could* open `/global` instead of
`/player` and read `secret.pref` mid-episode, because the player container is handed the same
host:port (`tools/ci/docker_smoke.sh:218`). Closing that needs one of: token-gating `/global` (the note
pins it token-free, and hosted certification probes it), or withholding `secret` from live frames and
revealing it only in the replay (which deletes the note's real-time broadcast premise and fails the
broadcast test). Neither is a fixer's call, so I made no change. Nothing in the shipped player does it
(`src/daycare_player.nim:47-48` connects to the one URL and only listens), and no checklist item covers
it — the reviewer says so too.

---

## NOTED (not fixed)

1. **The 360 px feed is inside the frame but tiny.** The new fixture measures the shipped feed row at
   **font 4 px** at a 360 px viewport (`--hudscale ≈ 0.5`, and `.feed-row` is `calc(8 * var(--u))`);
   the secret panel is 109×29 px there. Nothing overflows — that is C3 answered — but a full-cap hunch
   at 4 px is not *readable*, and the note's 360 px checklist asks for "the newest two feed rows". The
   honest fix is not a font floor (raising it doubles the row width past a 360 px viewport, which the
   negative control shows runs off the left edge); it is a wrapping or clamping rule for the hunch in
   the feed at small widths, which the note does not specify. Left alone, with the measured numbers now
   in `viewer-smoke.json` every run.
2. **Feasibility gate (a) on `daycare-fickle` is on its threshold** (10.08 correct turns per seed
   against a `>= 10` bar; 10/12 seeds). See N6 above.
3. **`tools/ci/renderer_fixture.html` no longer contributes to `canvas_text`.** The board canvas now
   lives in the iframe, whose `CanvasRenderingContext2D` hook is a different realm from the one
   `viewer_smoke.mjs` reports. The number was `0` before the change too (server-side sprite text), so
   nothing was lost, but the fixture's guarantee is explicitly its DOM assertions, not the canvas
   counter.
