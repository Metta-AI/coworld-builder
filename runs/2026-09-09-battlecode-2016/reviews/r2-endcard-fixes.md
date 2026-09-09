# r2 endcard fixes — battlecode-2016

> **Provenance.** This is the fixer's own write-up, filed by the endcard-fixer thread when its
> work completed. While it was still running (its last CI wait), the coordinator believed the
> thread had been lost and committed a *reconstruction of record* at this same path in
> `c36c086`, derived from the PR, its commits and its CI runs. That reconstruction is accurate
> and is preserved in git history; this file supersedes it as the first-hand account, and adds
> what only the fixer had: how E2 and E3 were reproduced *before* they were fixed, the
> counterfactual runs that show each new gate failing on the unfixed tree, and the two things
> noted but deliberately not fixed. The coordinator's own audit of the diff (3 files,
> `client/replay_broadcast.html` +66/−5, `tests/test_viewer.nim` +83/−2,
> `tools/ci/renderer_fixture.html` +119/−6; PR #12 merged 2026-09-09T15:36:20Z) stands and
> agrees with everything below.

**Repo:** `Metta-AI/cogame-battlecode` · **branch:** `bc16-endcard-year-guard` → PR
[#12](https://github.com/Metta-AI/cogame-battlecode/pull/12), merged with `--merge`
**Findings:** E1 fixed · E2 **reproduced** and fixed · E3 **reproduced** and fixed

| finding | disposition | commit (on `main`) | files |
|---|---|---|---|
| E1 — bc22's Singularity in every year's `more_archons` endcard | fixed | `44947e96205f58dfc00b093c576a03ccffa33ecb` | `client/replay_broadcast.html:6832-6852,6867-6884`, `tests/test_viewer.nim:1277-1315` |
| E2 — endcard headline clipped along its top edge | fixed (reproduced first) | `68d398193dd5250a7d3b61722a938139c9e8cdf9` | `client/replay_broadcast.html:1861-1872,1889-1900`, `tools/ci/renderer_fixture.html`, `tests/test_viewer.nim` |
| E3 — doctrine cards hard-clip `notes`/words mid-word | fixed (reproduced first) | `ac80a88b9be7d0b06172bab0a47d43539dca306b` | `client/replay_broadcast.html:1985-2006`, `tools/ci/renderer_fixture.html`, `tests/test_viewer.nim` |

**CI:** see "CI" at the bottom — run id, URL and conclusion, on `main`.

---

## How E2 and E3 were reproduced (before anything was changed)

The brief was right that the fixture is the instrument, and right that the sandbox has no
docker and no emsdk — but it **does** have a browser: `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`
carries chromium 141, and `tools/ci/viewer_smoke.mjs` drives it once `PLAYWRIGHT_MODULE` points
at the globally installed playwright. So the whole `Render the full-cap doctrine-text fixture`
step of `ci.yml` reproduces locally in about two seconds: extract the page's `<style>` block
exactly as that step's inline python does, serve it beside the fixture, run the harness.

Two things had to be added before the fixture could see either finding, because
**the fixture rendered `#endcard` empty** — it was in the page only so the HUD-suppression rule
could be read off the browser:

1. the endcard's own bands, built from `renderEndcard()`'s markup, with each year's full-cap
   doctrine words and the 48-rune motto (`ENDCARD_WORDS`, one row per year);
2. `#bc16-siege`, `renderEndcardExtras()`'s war panel at this year's measured-widest numbers,
   **inside** the card, which is where the page puts it. This one matters: with `.ec-teams`
   capped at 52 % and no war panel, the bands add up to *less* than the card and nothing is
   squeezed — an endcard fixture without the year's panel is green about a card that clips.

With those in place, the **unfixed** page measures (chromium, page's own CSS, three frame
widths, bc16 row):

| width | `#ec-headline` box | its own line | `#ec-teams` shown | `#ec-teams` content |
|---|---|---|---|---|
| 360 | **5 px** | 20 px | 262 px | 872 px |
| 720 | **13 px** | 21 px | 395 px | 835 px |
| 1280 | **14 px** | 32 px | 284 px | 579 px |

Both findings are real, both are the same root cause family, and neither is bc16-only — the
gate fails on the **bc26** row too.

---

## E1 — the shared `more_archons` clause carried bc22's lore

**What the code did.** `client/replay_broadcast.html:6860-6862`:

```js
      case 'more_archons':
        return 'the Singularity came at round ' + last.rounds_played +
          ' and ' + alias + ' had more archons left';
```

`more_archons` is bc22's `PWNED` and bc16 **reuses** it as rung 1 of its tiebreak ladder —
`src/battlecode/results.nim`'s own note on `EndReasons` says so in as many words. So every bc16
match decided on that rung told its spectator about a mechanic bc16 does not have. Confirmed
live: `viewer-check/viewer-smoke.png`, VERIFY.md §8.

**What it does now.** The clause that names *how the game ran out* comes from `ENDCARD_NOUNS`,
the per-year table the same function already resolves nouns through:

```js
    bc22: { unit: 'archon', units: 'archons', res: 'lead',
            limit: 'the Singularity came' },
    bc16: { unit: 'archon', units: 'archons', res: 'parts',
            limit: 'the round limit ran out' }
...
      case 'more_archons':
        // Shared rung: bc22's and bc16's. `limit` is the year's own row.
        return (nouns.limit || 'the round limit ran out') + ' at round ' +
          last.rounds_played + ' and ' + alias + ' had more archons left';
```

No new mechanism, no restructuring, and a year with no `limit` row falls back to the plain
round limit rather than printing `undefined`. Evaluated against the real function in node:

```
bc16 -> the round limit ran out at round 3000 and Clan Basil had more archons left
bc22 -> the Singularity came at round 3000 and Clan Basil had more archons left   (unchanged)
```

**Why it cannot come back.** `tests/test_viewer.nim` now slices `endcardWinCondition()` into its
`case` branches and, for every end reason **more than one year emits** (`more_archons`,
`annihilated`, `coin_flip`, `abandoned`, `highest_id`), fails if the branch contains any word
belonging to one year's rule set — Singularity, rat king, cheese, cats, soup, dirt, influence,
Enlightenment, crumb, duck, chip, paint, adamantium, mana, elixir, anchor, zombie, horde,
rubble, gold, lead. Restoring the old line locally fails exactly two checks:

```
FAIL the year's row supplies the clause for the shared rung
FAIL the shared `more_archons` branch says nothing about Singularity: case 'more_archons':
        return 'the Singularity came at round ' + last.rounds_played +
          ' and ' + alias + ' had more archons left';
test_viewer: 2 of 978 checks failed
```

That is the class closed, not the instance: nothing had ever asserted the wording of a *shared*
reason *per year*, which is why phase 30 was green.

## E2 — the headline was squeezed, not overflowing

**Reproduced.** Not a compression artefact: at 1280×800 the band is 14 px tall for a 32 px line
and is `overflow: hidden`, so it draws a horizontal slice of its own capitals — the screenshot's
"CLAN BASIL — DAVEEY-1" with the tops and bottoms sheared off.

**Cause, at the card rather than the headline.** `#endcard` is a column flex box and a flex item
shrinks below its own content by default. When the bands (headline, win-condition chip, `how`
line, doctrine panels, war panel, replay line) add up to more than the board region, the browser
squeezed *every* band instead of scrolling the card. That also kept `#endcard.scrollHeight`
equal to its `clientHeight`, so **FIX 2's own gate** (`viewer_smoke.mjs --killfeed-overlap`,
"`#endcard` overflows at 1280x800") was passing on a card that was clipping.

**Fix** (`client/replay_broadcast.html`):

```css
#endcard.on > * { flex: none; }
```

plus, on `#endcard` itself, `justify-content: safe center` after the existing
`justify-content: center`. The second half is load-bearing and was measured: a centred column
flex box that is also the scroll container strands its overflow **above** the scrollport — with
`flex: none` but plain `center`, the headline sat 23 px (1280) to 234 px (360) above the card's
own scroll origin, unreachable by any scroll. `safe` degrades to plain centring when the content
fits, and a browser that does not know the keyword keeps the line above, i.e. today's behaviour.
This is the same trap the file already documents one level down for `.ec-teams.br`.

**Gate.** The fixture measures the headline's box against its own computed line-height and
against the card's scrollport, at 360/720/1280, for all eight years. With the two declarations
removed, `viewer_smoke.mjs` exits **1**:

```
renderer fixture: the endcard headline is squeezed into 5px of its own 20px line — it draws a slice of its own capitals
renderer fixture: the endcard headline is squeezed into 13px of its own 21px line — …
renderer fixture: the endcard headline is squeezed into 14px of its own 32px line — …
```

and with them, **0**. `tests/test_viewer.nim` pins the shape of both rules and of the fixture
check so a later edit cannot quietly drop either.

## E3 — the doctrine panels clipped a sentence, and the box was too small

**Reproduced.** With both seats at bc16's widest sheet, `#endcard .ec-teams`' `max-height: 52%`
hid 610 px of 872 px (360), 440 px of 835 px (720) and 295 px of 579 px (1280) — cut mid-word,
no ellipsis, inside a scroll box with no dismiss control. That is the screenshot's
"…activates a" / "…routes its". Phase 30 item 15: ellipsis is a label's choice and a sentence's
defect; if a remark is being cut, the box is too small.

**Fix** — widen the band rather than shorten the text:

```css
#endcard .ec-teams:not(.br) { max-height: none; }
#endcard .ec-teams:not(.br) .ec-team {
  width: auto;
  flex: 1 1 calc(215 * var(--u));
  max-width: calc(430 * var(--u));
}
```

The 52 % cap is sized for the BR field list (a row is a name and three numbers, and the tail is
optional reading); the doctrine variant is one team's whole doctrine in plain words, so it is
scoped out of the cap. `width: auto` is load-bearing and was measured: the card is centred, so
`.ec-teams` is shrink-to-fit and a panel still carrying the base rule's fixed `215u` contributes
exactly that to the row — the row stayed 452 px wide inside a 1240 px frame until the width was
released. At `430u` a panel is 275 px instead of 579 px at 1280, and the whole card needs 682 px
of a 586 px scrollport instead of 986 px, so what is left to the card's own scroll (the one place
endcard content may overflow to, by FIX 2's design) is a scroll of tens of pixels rather than
hundreds. `.ec-teams.br` keeps its own 62 % cap and is untouched.

**Gate.** The fixture fails if `#ec-teams` scrolls inside the card, and checks both seats' endcard
motto is still at its 48-rune cap before it measures anything. With the two rules removed the
harness exits **1** on the *first* year it lays out:

```
bc26 @ 360px: the endcard doctrine panels are cut off: 116px of 378px hidden inside a box on the card
```

so the defect is closed for all eight years, not just bc16.

---

## What I did not do

- **No test was weakened, skipped or deleted.** One existing assertion in `tests/test_viewer.nim`
  pinned the fixture's endcard markup as the literal `'<div id="endcard"></div>' +` — its claim
  is "#endcard is a child of #chrome", and it is re-expressed against the populated markup
  (`'<div id="endcard">' + endcard + '</div>' +`), same claim plus the content. Check count went
  865 → 988; all additions.
- **No scope beyond E1/E2/E3.** Three commits, one per finding, each naming it.

## NOTED (not fixed)

- `endcardWinCondition()` has no branch for bc16's own rungs `more_archon_health`,
  `more_parts_net_worth` or `archons_destroyed`, so they fall to the default clause and render as
  "the game ended on more archon health in game 2, round 3000". Year-neutral and truthful, but
  flat next to the branches that read as sentences. Not a finding in this brief; left alone.
- `#bc16-siege` (the endcard war panel) keeps its own `max-height: 30vh; overflow: auto`, so at
  1280×800 it shows about 240 px of ~360 px of box score and scrolls for the rest. That is a
  table of numbers rather than a remark, and it is the year panel's own long-standing design, so
  it is outside E3's "a sentence is being cut". Worth a look if a later round wants the whole box
  score on one screen.

## CI

- **PR run (`pull_request`, head `ac80a88`):** run [34361940380](https://github.com/Metta-AI/cogame-battlecode/actions/runs/34361940380) — **success** (all eleven jobs; `wasm-viewer`'s `Render the full-cap doctrine-text fixture` step green, `test` green)
- **`main` run (`push`, head `1f5cb5cfde657c5c589ac73d823898fe464885ab`):** run [34371338676](https://github.com/Metta-AI/cogame-battlecode/actions/runs/34371338676) — **success**, all eleven jobs green (`test`, `docker-smoke`, `wasm-viewer`, eight `parity-oracle*`)
- **Final `main` sha: `1f5cb5cfde657c5c589ac73d823898fe464885ab`**
