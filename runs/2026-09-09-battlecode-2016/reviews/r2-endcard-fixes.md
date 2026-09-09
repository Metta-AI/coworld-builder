# r2 — endcard fixes (E1/E2/E3): record of what landed

**This file is a RECONSTRUCTION OF RECORD, not the fixer's own write-up.**

Provenance and the loss, stated plainly: the endcard fixer was dispatched at
2026-09-09T13:44:00Z (thread `sthr_01T5S9Xh8vboUi2orH1u6AGT`, output path
`runs/2026-09-09-battlecode-2016/reviews/r2-endcard-fixes.md`). The dispatching session
went stale at 13:40Z-heartbeat and died before the fixer returned, so the fixer's own file —
written into that session's container and never committed — is gone, exactly as both round-1
artifacts were lost at 09:06Z (see `log.md` 12:33Z finding B, and the process defect filed at
12:38Z). The fixer's *work* survives in full, because it landed in the repo. Everything below is
quoted or derived from primary, contemporaneous sources that are still fetchable:

- PR `Metta-AI/cogame-battlecode#12` — "bc16 endcard: year-guard the shared win-condition
  clause, unsqueeze the card" — opened on branch `bc16-endcard-year-guard`, merged
  **2026-09-09T15:36:20Z**, merge commit `1f5cb5cfde657c5c589ac73d823898fe464885ab`.
- Its three commits and their full messages (`gh api repos/.../commits/<sha> -q .commit.message`).
- Its diff (`gh pr diff 12`): 3 files, +268 / −13.
- Branch CI run **34361940380** at `ac80a88b9be7d0b06172bab0a47d43539dca306b`: **success**,
  all 11 jobs (`test`, `docker-smoke`, `wasm-viewer`, `parity-oracle` + the 8 per-year oracles).
- Main CI run **34371338676** at the merge commit `1f5cb5cf` — recorded in `log.md`.

Reconstructed by the coordinator session `e43917a0` at 2026-09-09T16:52Z, after reading the diff
itself rather than trusting the PR prose.

## Scope this round was given

Not a review round. A coordinator rail decision taken at 13:40Z under `AGENT.md` §Rails
("viewer composition") and `prompts/40-release.md` step 6 ("ship small fixes as version bumps
during the run"): the phase-60 verifier's rendered evidence
(`runs/2026-09-09-battlecode-2016/viewer-check/viewer-smoke.png`) showed a spectator-visible
content defect that is **not** one of the eight definition-of-done checks and changes **no**
verdict. All eight checks were TRUE before this round and remain TRUE. The round exists so the
announcement does not land on a frame that names a mechanic bc16 does not have.

| id | handed over as | outcome |
|---|---|---|
| E1 | **CONFIRMED** by the coordinator in the code, with the anchor quoted | FIXED + class closed by a test |
| E2 | **SUSPECTED from a compressed PNG**, to be fixed only if reproduced by measurement | REPRODUCED by measurement, then FIXED |
| E3 | **SUSPECTED from a compressed PNG**, same instruction | REPRODUCED by measurement, then FIXED |

The brief required a non-reproduction of E2/E3 to be written up as a correct outcome. Both
reproduced, at 360/720/1280 px, in the page's own CSS, with the numbers quoted below.

## E1 — bc22's Singularity leaked onto every year's `more_archons` endcard

Commit `44947e96`.

The defect, as it shipped:

```js
case 'more_archons':
  return 'the Singularity came at round ' + last.rounds_played +
    ' and ' + alias + ' had more archons left';
```

`more_archons` is bc22's PWNED **and** bc16's first tiebreak rung (`src/battlecode/results.nim`'s
own note on `EndReasons`), so a live bc16 ladder match rendered

> THE SINGULARITY CAME AT ROUND 3000 AND CLAN BASIL HAD MORE ARCHONS LEFT

for a mechanic bc16 does not have: 2016 has a 3000-round limit and a four-rung ladder
(`docs/RULES-BC16.md`), and the Singularity is bc22's anomaly-schedule beat.

The fix routes the clause through `ENDCARD_NOUNS`, the per-year table the same function already
resolves its nouns through — so the mechanism was already there and only this branch bypassed it:

```js
bc22: { unit: 'archon', units: 'archons', res: 'lead',
        limit: 'the Singularity came' },
bc16: { unit: 'archon', units: 'archons', res: 'parts',
        limit: 'the round limit ran out' }
…
case 'more_archons':
  return (nouns.limit || 'the round limit ran out') + ' at round ' +
    last.rounds_played + ' and ' + alias + ' had more archons left';
```

bc16 now reads "the round limit ran out at round 3000 and Clan Basil had more archons left";
bc22's wording is byte-for-byte unchanged.

**The class is closed, not the instance** — which is what the brief demanded ("a test that would
still pass with the bug present is not a fix"). `tests/test_viewer.nim` now slices
`endcardWinCondition()` into its branches and, for every end reason **more than one year emits**
(`more_archons`, `annihilated`, `coin_flip`, `abandoned`, `highest_id`), fails if that branch
contains any word belonging to one year's rule set (`Singularity`, `rat king`, `cheese`, `soup`,
`influence`, `Enlightenment`, `crumb`, `duck`, `chip`, `paint`, `adamantium`, `mana`, `elixir`,
`anchor`, `zombie`, `horde`, `rubble`, `gold`, `lead`, …). With the old line restored the test
fails on two checks. Nothing asserted per-year wording for a shared reason before, which is
exactly why the defect shipped green through phase 30.

## E2 — the headline drew a horizontal slice of its own capitals

Commit `68d39819`.

Reproduced before it was fixed, as instructed. `tools/ci/renderer_fixture.html` was raising an
**empty** `#endcard` — enough to read the HUD-suppression rule off the browser, useless for
anything about content. Populated with the year's own doctrine text and the bc16 war panel, the
unfixed card gives `#ec-headline` **5px / 13px / 14px** for a **20px / 21px / 32px** line at
360 / 720 / 1280. The band is `overflow: hidden`, so it draws a slice of its own glyphs — which
is "CLAN BASIL — DAVEEY-1" in `viewer-smoke.png`.

The cause is the card, not the headline: `#endcard` is a column flex box, and a flex item shrinks
below its content by default, so a card taller than the board region was squeezed band by band
instead of scrolling. That also kept `#endcard`'s `scrollHeight` equal to its `clientHeight` —
so the pre-existing FIX-2 overflow gate in `viewer_smoke.mjs` was **green on a card that was
clipping**. Two declarations:

```css
#endcard.on > * { flex: none; }      /* bands keep their natural height; the card scrolls */
justify-content: safe center;        /* a centred scroll container strands overflow ABOVE the scrollport */
```

Measured without `safe center`, the headline sat 23px (1280) to 234px (360) above the scrollport,
unreachable by scrolling. The gate is the fixture's measurement, not a grep: with the two
declarations removed it exits 1 on all three widths ("the endcard headline is squeezed into 5px
of its own 20px line"); with them, 0.

## E3 — both doctrine panels hard-clipped their sentences mid-word

Commit `ac80a88b`.

Reproduced at 360 / 720 / 1280 px with both seats at bc16's widest sheet: `.ec-teams`' 52 % cap
hid **610px of 872px** (360), **440px of 835px** (720) and **295px of 579px** (1280) of the two
doctrine panels — cut mid-word, no ellipsis, inside a scroll box with no dismiss control. That is
the live endcard's "…activates a" / "…routes its". Phase 30's item 15 is explicit: ellipsis is a
label's choice and a sentence's defect; if a remark is being cut, the box is too small.

The 52 % cap is sized for the **BR field list** (a name and three numbers per row), not for the
two-panel doctrine variant, so the variant is scoped out of it and given the width the frame has
to spare:

```css
#endcard .ec-teams:not(.br) { max-height: none; }
#endcard .ec-teams:not(.br) .ec-team {
  width: auto; flex: 1 1 calc(215 * var(--u)); max-width: calc(430 * var(--u));
}
```

`width: auto` is load-bearing: the card is centred, `.ec-teams` is shrink-to-fit, and a panel
still carrying the base rule's fixed 215u contributes exactly that to the row — measured, the row
stayed 452px inside a 1240px frame until the width was released. At 430u a panel takes 275px
instead of 579px at 1280, and the card needs 682px of a 586px scrollport instead of 986px.
`.ec-teams.br` keeps its own 62 % cap and is untouched.

Gate: the fixture fails if `#ec-teams` scrolls inside the card, and asserts both seats' endcard
text is at full length before measuring. With the two rules removed it exits 1 on the **first**
year row it lays out ("bc26 @ 360px: the endcard doctrine panels are cut off: 116px of 378px
hidden inside a box on the card") — so this closes the defect for all eight years, not just bc16.

## Scope discipline (coordinator's own audit of the diff)

- 3 files: `client/replay_broadcast.html` (+66/−5), `tests/test_viewer.nim` (+83/−2),
  `tools/ci/renderer_fixture.html` (+119/−6). No game code, no rules, no parity oracle, no
  year module touched — so no sibling year's committed chain can move.
- The only removals in `tests/test_viewer.nim` are the two lines of the "#endcard is the last
  child of #chrome" assertion, **re-expressed against the now-populated markup**: same claim,
  plus the content. No test weakened, no skip/xfail added.
- The CSS is additive and endcard-scoped; `.ec-teams.br` (the BR variant every other year's
  elimination card uses) is explicitly excluded from both E3 rules and keeps its own cap.
- bc22's endcard wording is unchanged by construction — its own `ENDCARD_NOUNS` row carries the
  Singularity, and the test asserts that it still does.

## CI

| run | sha | result |
|---|---|---|
| 34361940380 (branch `bc16-endcard-year-guard`) | `ac80a88b` | **success**, 11/11 jobs |
| 34371338676 (main, post-merge) | `1f5cb5cf` | see `log.md` — required green before the re-release |

The exit the brief set was `ci.yml` green on `main`; the branch run is the same tree as the merge
commit (main had not moved since `46b92ae5`), and the main run is the one the coordinator gates
the re-release on.
