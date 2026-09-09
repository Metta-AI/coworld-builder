# r3 duel-label fixes — battlecode-2016

**Repo:** `Metta-AI/cogame-battlecode` · **branch:** `bc16-duel-label` → PR
[#13](https://github.com/Metta-AI/cogame-battlecode/pull/13)
**Base:** `1f5cb5cfde657c5c589ac73d823898fe464885ab` (`main`, PR #12's merge)

| finding | disposition | commit | files |
|---|---|---|---|
| D1 — bc16's `duel` beat rendered as bc23's LAUNCHER DUEL | fixed | `916c5e679598933d9e18d51d3a99212c337326f7` | `src/battlecode/broadcast.nim:162-166,354-371` |
| D1 (class) — no bc16 label may carry another year's vocabulary | test added | `9947ae69254f0a780117fc9c1dcede88d3d4cee9` | `tests/test_bc16_beats.nim:17-25,218-315` |

Full bc16 label audit: **nothing else found.** See "The audit" below.

---

## The defect

`src/battlecode/broadcast.nim:353-363`, as shipped at `1f5cb5c`:

```nim
    of "duel":
      ## bc22 spells `duel` with the SAME field name and a different meaning —
      ## attackers lost, not launchers — so the label switch tests the year.
      if isBc22:
        label = "TRADE — " & $e.fields{"lost"}[0].getInt() &
          " attackers lost to " & $e.fields{"lost"}[1].getInt() & ", game " &
          $(e.game + 1) & ", round " & $e.round
      else:
        label = "LAUNCHER DUEL — " & $e.fields{"lost"}[0].getInt() &
          " lost to " & $e.fields{"lost"}[1].getInt() & ", game " &
          $(e.game + 1) & ", round " & $e.round
```

The switch tested `isBc22` **alone**, so bc16 fell into the `else` — bc23's
branch — and a bc16 killfeed named a unit the 2016 rule set does not have.
Reproduced against the committed fixture before anything was changed
(`tests/fixtures/replay-bc16.json`, the same recording the round-17 replay came
from), rendering the *same* event under each year:

```
bc16  first: LAUNCHER DUEL — 1 lost to 1, game 1, round 232
bc16  duel beats: 22
bc22  first: TRADE — 1 attackers lost to 1, game 1, round 232
bc22  duel beats: 22
bc23  first: LAUNCHER DUEL — 1 lost to 1, game 1, round 232
bc23  duel beats: 22
```

Twenty-two of them in the fixture; the coordinator counted eleven in the
round-17 ladder replay.

### The three emitters, and what each counts

| emitter | field it reads | what that is | wording it must get |
|---|---|---|---|
| `src/battlecode/years/bc22/rules.nim:275` | `w.attackersLostThisRound` | every unit that can attack, lost by **both** sides in one round (`years/bc22/world.nim:512`, `if canAttackType(kind)`) | `TRADE` |
| `src/battlecode/years/bc16/rules.nim:321` | `w.attackersLostThisRound` | the same thing (`years/bc16/world.nim:642`, `if canAttack(kind)`) | `TRADE` |
| `src/battlecode/years/bc23/rules.nim:397` | `w.launchersLostThisRound` | one unit type, the launcher | `LAUNCHER DUEL` |

```nim
# years/bc16/rules.nim:320-322
  if w.attackersLostThisRound[0] > 0 and w.attackersLostThisRound[1] > 0:
    discard w.beat(BeatDuel, "duel", w.attackersLostThisRound[0],
                   w.attackersLostThisRound[1])

# years/bc22/rules.nim:274-276 — character for character the same two lines
  if w.attackersLostThisRound[0] > 0 and w.attackersLostThisRound[1] > 0:
    discard w.beat(BeatDuel, "duel", w.attackersLostThisRound[0],
                   w.attackersLostThisRound[1])

# years/bc23/rules.nim:396-398 — a different counter
  if w.launchersLostThisRound[0] > 0 and w.launchersLostThisRound[1] > 0:
    discard w.beat(BeatDuel, "duel", w.launchersLostThisRound[0],
      w.launchersLostThisRound[1])
```

bc20, bc21, bc24, bc25 and bc26 never emit `BeatDuel` (checked by grepping
`beat(Beat` across every `src/battlecode/years/*` tree). So bc16's `duel`
carries **bc22's semantics** and had to read like bc22's.

## The fix — commit `916c5e6`

`src/battlecode/broadcast.nim:354-371`:

```nim
    of "duel":
      ## THREE years emit `duel`, with the SAME field name and TWO meanings.
      ## bc22 (`years/bc22/rules.nim:275`) and bc16
      ## (`years/bc16/rules.nim:321`) both count `attackersLostThisRound` —
      ## every unit that can attack, lost by both sides in the same round —
      ## and read as a TRADE. bc23 (`years/bc23/rules.nim:397`) counts
      ## `launchersLostThisRound`, one unit type, and reads as a LAUNCHER
      ## DUEL. bc16 has no launcher, so it takes bc22's wording; testing
      ## `isBc22` alone dropped bc16 into bc23's branch and told a bc16
      ## spectator about a unit its year does not have.
      if isBc22 or isBc16:
        label = "TRADE — " & $e.fields{"lost"}[0].getInt() &
          " attackers lost to " & $e.fields{"lost"}[1].getInt() & ", game " &
          $(e.game + 1) & ", round " & $e.round
      else:
        label = "LAUNCHER DUEL — " & $e.fields{"lost"}[0].getInt() &
          " lost to " & $e.fields{"lost"}[1].getInt() & ", game " &
          $(e.game + 1) & ", round " & $e.round
```

One clause. `isBc16` already existed at `broadcast.nim:162` and the file
already uses exactly this shape for per-year wording three cases further down —
`archon_lost` at `:448-463` switches on `if isBc16:` because bc22 carries
`gold_dropped` where bc16 carries `cause`. There is no per-year wording *table*
in this file to hang it on (the endcard's `ENDCARD_NOUNS`, which r2-E1 used, is
in the JS page, not here), so widening the existing boolean is the honest
minimum and it is the idiom the file already has.

The **only** other change in this commit is the proc's header comment at
`:162-166`, which listed `duel` among the kinds "no other year emits" — the
belief that produced the defect:

```nim
   ## The bc23-only kinds below (`anchor_built`, `island_captured`,
   ## `island_lost`, `conquest_progress`, `well_transformed`, `well_upgraded`,
-  ## `first_elixir_unit`, `boost_field`, `destabilize_hit`, `duel`) need no
-  ## discriminator, because no other year emits them.
+  ## `first_elixir_unit`, `boost_field`, `destabilize_hit`) need no
+  ## discriminator, because no other year emits them. `duel` is NOT one of
+  ## them — bc22, bc23 and bc16 all emit it — so its LABEL tests the year.
```

### bc22 and bc23 unchanged

The `else` branch and the body of the `if` are untouched; only the condition
moved. Rendering the same fixture event under each year after the fix:

```
bc16  first: TRADE — 1 attackers lost to 1, game 1, round 232      <- was LAUNCHER DUEL — 1 lost to 1, …
bc22  first: TRADE — 1 attackers lost to 1, game 1, round 232      <- unchanged
bc23  first: LAUNCHER DUEL — 1 lost to 1, game 1, round 232        <- unchanged
```

and the two years' own suites are green on the fixed tree, including the two
assertions that pin their wording — `tests/test_bc22_beats.nim:92` ("bc22's
`duel` reads as a TRADE, not as a launcher duel") and `:152` ("the SAME event
labelled under bc23 reads as a launcher duel"):

```
test_bc22_beats: ok (359 checks)
test_bc23_beats: ok (500 checks)
```

Neither was weakened, reworded or deleted.

## Closing the class — commit `9947ae6`

`tests/test_bc16_beats.nim` walked `["build", "rout", "duel", "archon"]` at
`:72` asserting only that those kinds were **emitted**; nothing anywhere
asserted the **wording** of a shared beat **per year**, which is why
`LAUNCHER DUEL` shipped green through phase 30 and two review rounds. The new
`§2b NO OTHER YEAR'S VOCABULARY` block does three things.

**1. The instance, pinned exactly.** The expected strings are built from the
event's own `lost` pair rather than hard-coded, so the assertion is about the
wording and not about the fixture's numbers:

```nim
  let duel = firstEventOf("duel")
  let lostA = $duel.fields{"lost"}[0].getInt()
  let lostB = $duel.fields{"lost"}[1].getInt()
  let tail = ", game " & $(duel.game + 1) & ", round " & $duel.round
  checkEq("bc16's `duel` reads as a TRADE in attackers, which is what bc16 " &
    "counts", duelLabelUnder("bc16"),
    "TRADE — " & lostA & " attackers lost to " & lostB & tail)
  check("and says nothing about a LAUNCHER, a unit bc16 does not have",
    "LAUNCHER" notin duelLabelUnder("bc16").toUpperAscii())
```

**2. The other two years, from the same event, byte for byte.** So the fix
cannot be reached by moving bc22's or bc23's wording:

```nim
  checkEq("bc22's `duel` is unchanged", duelLabelUnder("bc22"),
    "TRADE — " & lostA & " attackers lost to " & lostB & tail)
  checkEq("and bc23's is unchanged — bc23 really does count launchers",
    duelLabelUnder("bc23"),
    "LAUNCHER DUEL — " & lostA & " lost to " & lostB & tail)
```

**3. The generalisation.** Every beat bc16 emits is rendered under bc16 and
checked against a list of words that belong to exactly one **other** year's
rule set — the mechanism `tests/test_viewer.nim` (r2-E1, PR #12) uses on the
endcard's shared win-condition branches:

```nim
  const Foreign = ["launcher", "singularity", "rat king", "cheese", "cats",
                   "soup", "dirt", "influence", "enlightenment", "crumb",
                   "duck", "chip", "paint", "adamantium", "mana", "elixir",
                   "anchor", "boost", "destabilis", "destabiliz", "hq",
                   "headquarters", "tower"]
```

bc16's own vocabulary — archon, parts, rubble, zombie, den, horde, viper,
guard, scout, soldier, turret, infection, outbreak — is deliberately **not** on
the list, and a word two years merely share is not a leak. One carve-out, and
it is stated in the test: a map's own **name** is stripped from the label
before the search, because a bc16 map called `towers` would be bc16's own word
for it and not bc25 leaking in. (bc16's committed pool — `data/maps/bc16/` —
collides with nothing on the list today; the strip is there so a future map
cannot make this test lie either way.)

The committed fixture reaches eleven of bc16's thirteen beat kinds. The two it
cannot — `tiebreak` fires only when the round limit decides a game,
`game_abandoned` only on the wall clock — are appended with the exact fields
`match.nim:507-525` and `match.nim:584` give them, so the audit covers **every**
kind bc16 can put in a killfeed, and two guards stop it being vacuous:

```nim
  check("the appended `tiebreak` really rendered, so its audit is not vacuous",
    sawTiebreak)
  check("and so did the appended `game_abandoned`", sawAbandoned)
  for k in Bc16BeatKinds:
    check("and the audit covered the `" & k & "` kind", k in auditedKinds)
```

and a live negative control for the search itself — the same events read as
bc23 must trip it, which is exactly the string bc16 used to ship:

```nim
  check("the word search really fires: the same feed read as bc23 trips on " &
    trippedOn.join(", "), "launcher" in trippedOn)
```

It trips on `launcher`, and on nothing else.

### Proof it fails with the bug restored

`if isBc22 or isBc16:` reverted to `if isBc22:` in the working tree, everything
else untouched, `nim r --path:src --path:tests tests/test_bc16_beats.nim`:

```
FAIL bc16's `duel` reads as a TRADE in attackers, which is what bc16 counts: got LAUNCHER DUEL — 1 lost to 1, game 1, round 232 want TRADE — 1 attackers lost to 1, game 1, round 232
FAIL and says nothing about a LAUNCHER, a unit bc16 does not have
FAIL the bc16 `duel` label says nothing about `launcher`: LAUNCHER DUEL — 1 lost to 1, game 1, round 232
FAIL the bc16 `duel` label says nothing about `launcher`: LAUNCHER DUEL — 1 lost to 1, game 1, round 249
… (22 in all, one per duel beat in the fixture) …
test_bc16_beats: 24 of 6045 checks failed
```

With the fix in place:

```
test_bc16_beats: ok (6045 checks)
```

91 checks → 6045, every one an addition. No existing assertion was weakened,
skipped or deleted; the file's header comment was corrected, because lines
19-20 described `duel` as "bc22's and bc23's, whose field means launchers lost
rather than attackers lost", which is not what bc22 counts.

## The audit — every bc16 beat kind, and the result

Rendered from the committed fixture (plus the two synthesised kinds), one
example per kind, `(n)` = how many the audit covered:

| beat kind | emitter | example label | verdict |
|---|---|---|---|
| `doctrine` (2) | `match.nim`, shared chrome | `Doctrine read for Clan Ash (0 ms)` | clean |
| `game` (3) | `bc16/rules.nim:567` `game_start` | `Game 1 begins on frogger` | clean |
| `build` (33) | `bc16/world.nim:688` `first_action`, `bc16/world.nim:885` `unit_milestone` | `Clan Ash commissions its first turret — game 1, round 0`; `Clan Ash opens with build — game 1, round 0` | clean |
| `activate` (24) | `bc16/world.nim:919` `neutral_activated` | `Clan Ash activates a neutral SCOUT at 30,11 — game 1, round 31` | clean |
| `wave` (11) | `bc16/rules.nim:333` `zombie_wave` | `WAVE — 4 zombies from 12 dens at outbreak level 0, game 1, round 50` | clean |
| `infect` (60) | `bc16/world.nim:792` `infection` | `Clan Basil's SCOUT is infected by a zombie for 10 turns, game 1, round 51` | clean |
| `turned` (72) | `bc16/rules.nim:311` `turned` | `CLAN ASH'S SCOUT TURNS — a FASTZOMBIE at 26,22, and it is hunting whoever is nearest, game 1, round 153` | clean |
| `duel` (22) | `bc16/rules.nim:321` `duel` | `TRADE — 1 attackers lost to 1, game 1, round 232` | **was the defect; now clean** |
| `archon` (11) | `bc16/rules.nim:317` `archon_lost` | `ARCHON DOWN — Clan Basil has 3 left, killed by enemy, game 1, round 287` | clean (already year-switched, r1) |
| `outbreak` (7) | `bc16/rules.nim:338` `outbreak` | `OUTBREAK 1 — every new zombie is 1.1x stronger from here, game 1, round 300` | clean |
| `den` (7) | `bc16/world.nim:834` `den_destroyed` | `Clan Basil breaks the den at 3,34 — 200 parts and 20 zombies deleted, game 1, round 414` | clean |
| `rout` (1) | `bc16/rules.nim:325` `rout` | `ROUT — Clan Basil loses 6 robots, game 3, round 307` | clean |
| `end` (5) | `bc16/rules.nim:592` `game_end`, `:228` `tiebreak`, `:585` `game_abandoned` | `Game 1 — Clan Ash wins (archons destroyed)`; `ROUND 845 — more archon health decides it: archons 2 to 2, archon health 4210 to 3990`; `Game 3 abandoned at the wall clock` | clean |

**Nothing else was found.** Thirteen kinds, 258 beats, every one free of every
word on the list. Three near-misses were checked by hand and are *not* leaks:

- `end`'s `end_reason` comes from bc16's own `Domination` ordinals
  (`years/dispatch.nim:218` `Bc16RungNames` = `archons_destroyed`,
  `more_archons`, `more_archon_health`, `more_parts_net_worth`, `highest_id`),
  which is the same set `tiebreak.rung` draws on. All bc16's.
- `build`'s unit names come from `Bc16UnitNames` (`years/dispatch.nim:211`):
  `turret` and `ttm` are 2016's, not bc25's `tower`.
- `build`'s action names come from `Bc16ActionNames` (`years/dispatch.nim:201`):
  `broadcast`, `pack`, `unpack`, `disintegrate` are all 2016's.

`archon_lost` is the one shared beat that was *already* year-switched, by
r1-F8/F9's work, and the audit confirms it: bc16's label says
`killed by enemy` where bc22's says `gold is on the ground`.

## What I did not do

- No year's rules or game logic, no parity oracle, no `docs/PARITY.md`, no
  viewer bundle, no `tools/ci/policies.json`, no manifest. Two files:
  `src/battlecode/broadcast.nim` (+13 −5) and `tests/test_bc16_beats.nim`
  (+106 −4, of which +9 −6 is the corrected header comment).
- No `skip`, no `xfail`, no weakened assertion.

## NOTED (not fixed)

- `tests/test_bc16_beats.nim:31-33` calls its list `Bc16BeatKinds` and the
  header calls it "the thirteen-kind vocabulary"; `tiebreak` and
  `game_abandoned` both fold into the `end` kind, so a kind-level inventory can
  never distinguish them. The new audit reaches them by event kind instead.
  Nothing is wrong; it is just worth knowing that "thirteen kinds" is fewer
  than "the events bc16 emits".
- The `Foreign` word list is duplicated between `tests/test_viewer.nim`
  (r2-E1, over the endcard's JS branches) and `tests/test_bc16_beats.nim`
  (here, over the Nim beat labels). They are two different languages and two
  different artefacts, so sharing them would mean a third file; left as is, but
  a future year's guard will want to know both exist.

## Method notes

- Nim locally: `nimby use 2.2.4`, `nimby --global sync nimby.lock`, then
  `nim r --path:src --path:tests tests/<file>.nim`. Ran `test_bc16_beats`,
  `test_bc22_beats`, `test_bc23_beats`, `test_bc16_arith`, `test_bc16_greenhorn`,
  `test_bc16_signals`, `test_replay` and `test_viewer` — every test in the repo
  that imports `broadcast` — all green before the push.
- **`git push` over HTTPS does not work from this sandbox.** The credential
  helper answers, but the token travels base64-encoded inside a Basic
  `Authorization` header and GitHub rejects it
  (`remote: Invalid username or token. Password authentication is not supported
  for Git operations.`). Tried the `gh auth git-credential` helper, the
  `git-credential-anthropic` helper, and an `http.extraHeader: Bearer` override
  (which hung); all three failed. `gh api` sends the token literally and works,
  so both branches here were built through the Git Data API — blob, tree,
  commit, ref, one commit at a time, parented on the real `main` — and then
  fetched back and verified: local `HEAD^{tree}` and the pushed
  `FETCH_HEAD^{tree}` are the same `fe43aff52c56a9ba1767336ec5c76978617910c2`,
  so what is on the branch is exactly what was tested. Nothing was force-pushed
  and no history was rewritten.

## CI

- **PR run (`pull_request`, head `9947ae69254f0a780117fc9c1dcede88d3d4cee9`):**
  run [34386571634](https://github.com/Metta-AI/cogame-battlecode/actions/runs/34386571634) — CI-RESULT-PR
- **`main` run (`push`, head MAIN-SHA):** run MAIN-RUN — CI-RESULT-MAIN
- **Final `main` sha:** MAIN-SHA
