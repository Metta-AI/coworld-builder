# r1 fixes — cogiavelli

Head: `044223b09cd2a66355e6866946226b08f4f690c3` (main)
CI: https://github.com/Metta-AI/cogame-cogiavelli/actions/runs/32731615199 — **success**
(`test`, `docker-smoke`, `wasm-viewer` all green; `Load the bundle in a real browser` ran and
printed `{"loaded":true,"ms":302,…,"feed_lines":68}` followed by `soak: 10s of playback kept
advancing`; docker-smoke printed `episode end reason: complete` /
`smoke OK: seats=6 results=434B replay=22950B reason=complete` and contains **zero**
`SEAT-COUNT FAIL` lines.)

Range reviewed: `b619ecc..f6862a3`. Range fixed: `f6862a3..044223b0`, 16 commits, one per finding
(plus two fix-forwards, marked below).

| finding | disposition | commit | files |
|---|---|---|---|
| N1 replay never compared a board snapshot | fixed | `541e04a` | `src/cogiavelli/sim.nim:1491-1545`, `tests/test_sim.nim:323-397` |
| N2 rebellion rolls compared only on equal length | fixed | `5b1117c` | `src/cogiavelli/sim.nim:1522-1531`, `tests/test_sim.nim:382-397` |
| N3 pledges judged on the post-movement board | fixed | `d8650a5` | `src/cogiavelli/sim.nim:560-612, 782-788`, `tests/test_sim.nim:442-486` |
| N4 ledger capped by line count, not two years | fixed | `9b280f5` | `src/cogiavelli/llm.nim:512-544` |
| N5 dead `defence` term in the bribe menu | fixed | `4ceef19` | `src/cogiavelli/llm.nim:619-633` |
| N6 famine used a variable number of draws | fixed | `7507cdd` | `src/cogiavelli/sim.nim:311-322`, `tests/test_sim.nim:487-507` |
| N7 a third cycle-breaking fallback | **refuted** | — | `src/cogiavelli/adjudicate.nim:250-254` |
| N8 conquest tie taken by the last power | fixed | `b583f2c` | `src/cogiavelli/sim.nim:446-465`, `tests/test_sim.nim:508-529` |
| N9 underpaid bribe reads as "defended" | fixed | `25b7bfa` | `client/renderer.js:2020-2037` |
| N10 two setup RNG streams | **refuted** | — | `src/cogiavelli/sim.nim:186, 243, 249` |
| N11 assassinate clamped server-side too | **refuted** | — | `src/cogiavelli/money.nim:70-71` |
| N12 `AssassinFaces` declared, not used by the roll | **refuted** | — | `src/cogiavelli/money.nim:17` |
| N13 `mapdata.nim` exports more than the note lists | **refuted** | — | `src/cogiavelli/mapdata.nim` |
| N14 `reason == "complete" or "conquest"` | fixed | `94e3264` | `tests/test_bot.nim:61-82, 117-131` |
| N15 endcard drops `stabs`; ledger static | fixed | `64e7bee` (+ fix-forward `d7d9792`) | `client/renderer.js:1452, 1024-1031, 2464-2604`, `client/chrome.css:642-672`, `tests/test_viewer.nim:205-220` |
| N16 `feed-end`/`feed-it` not in the note's CSS list | **refuted** | — | `client/renderer.js:2233-2234` |
| N17 unbounded `receiveMessage()` in the player | fixed | `35b997b` | `src/cogiavelli_player.nim:17-107` |
| N18 ASCII hyphens in the mandated prompt | fixed | `a536c21` | `src/cogiavelli/llm.nim:663, 667, 678` |
| N19 `client/player.html` opens the player socket | **refuted** | — | `src/cogiavelli/server.nim:522`, `client/player.html:51` |
| N20 note says the land graph is connected | **refuted** | — | `tests/test_map.nim:88-113` |
| CND §1 no grid harness for the baselines | fixed | `cdbce86` + `044223b0` (fix-forward over `6d55306`) | `tools/tune_baseline.nim`, `src/cogiavelli/llm.nim:52-96, 335, 357, 434`, `docs/tuning.md`, `tests/test_tuning.nim`, `.github/workflows/ci.yml:152-159` |
| CND §2 intra-resolution frames share one state | **noted, by design** | — | `src/cogiavelli/sim.nim:1547-1549` |
| CND §3 `readCogameUri` on a FIFO | **refuted** | — | `src/cogiavelli/llm.nim:106-117` |

---

## N1 — `replayMatch` verifies every recorded board snapshot

**Was:** `replayMatch` asserted `logged.kind == event.kind` for every event and compared the four
shock draws, and nothing else: `season`, `cities`, `winter`, `start` and `end` fell into
`else: discard`. A tampered *board* replayed silently while a tampered *die* raised — the gap the
review named against checklist item 2.

**Is:** each board-bearing event is compared field by field against the re-derived one —
`start`/`season` (units, city owners, treasuries, city counts), `cities` (owners, counts, gained,
lost), `winter` (units, owners, treasuries, counts on top of the existing draws) and `end`
(cities, treasuries, conqueror) — and any disagreement raises `CogiavelliError`
(`src/cogiavelli/sim.nim:1491-1545`).

**Evidence:** `tests/test_sim.nim:323-380` (`replayChecksEveryRecordedBoardSnapshot`) replays a
clean log, then four tampered copies — a unit moved to Abruzzi in a `season` snapshot, five
invented ducats in a `season` treasury, a stolen city plus its count in a `cities` snapshot, and a
unit deleted from a `winter` snapshot — and asserts each one raises. Green in run 32731615199,
step `Run tests`, debug and release.

**Checklist:** item 2 ("replaying the recorded events reproduces the recorded per-tick state frame
by frame … a test asserts it").

## N2 — a rebellion-roll length mismatch raises

**Was:** `if logged.rebellions.len == event.rebellions.len:` guarded the roll comparison, so a
recorded `winter` event carrying a different *number* of rolls than the re-derivation was accepted
without a raise — the one draw in the stream that could be added to or removed from silently.

**Is:** the length is checked first and raises; then every roll **and its city** is compared
(`src/cogiavelli/sim.nim:1522-1531`).

**Evidence:** `tests/test_sim.nim:382-397` deletes a recorded rebellion roll (or adds one when the
seed produced none) and asserts the raise.

## N3 — pledges are judged on the board the orders were written on

**Was:** `pledgeStabs` ran at `sim.nim:774`, after `runRetreats` had rebuilt `sim.board` with every
successful move applied. A peace-breaking move into a pledgee-held **non-city** province was
therefore stamped only when it *bounced*: when it succeeded, the victim's unit was no longer at the
destination and the pledger read as innocent. `plSupport` had the mirror bug — an allied unit that
successfully moved away read as "supported nobody", so an honoured pledge was recorded broken.

**Is:** `pledgeStabs` takes the board explicitly (`sim.nim:560`) and is called on the pre-movement
board, before `runRetreats` (`sim.nim:782-788`). That is design.md:388-390's rule: the orders as
written, against the board they were written on. The event content and its position in the log are
unchanged.

**Evidence:** `tests/test_sim.nim:442-486` — Verona and Modena (pledger) against an army in Mantua
(pledgee), `A VER - MAN` supported by `A MOD`, a province the test asserts is *not* a city. The
move dislodges, and the test asserts exactly one `stab`, naming the pledger, `plPeace` and the
victim. Under the old code this fixture recorded no stab at all.

## N4 — the prompt's ledger is the last two years

**Was:** `let cutoff = sim.year - 1` was computed, never used, and thrown away with
`discard cutoff`; the surviving filter was a 40-line tail, so at four years the block could carry
more than the two years design.md:348-350 and design.md:511 promise.

**Is:** `ledgerText` walks the last `2 * SeasonsPerYear` resolved seasons of `sim.history` — the
same window `historyText` uses for orders — and keeps the 40-line tail only as a prompt-size bound
(`src/cogiavelli/llm.nim:512-544`). `sim.ledger` is untouched and remains the whole-episode record
design.md:687 requires for the endcard.

## N5 — the dead `defence` term is gone

`var defence = 0` was never assigned and was added to both prices. It cannot be computed at prompt
time: the defender's `defend` entries ride in the same simultaneous batch (design.md:369). The
variable is gone, the doc comment says why the quoted price is a floor, and the printed lines are
byte-identical to before and to the note's example at design.md:522
(`src/cogiavelli/llm.nim:619-633`).

## N6 — the Spring famine consumes exactly two draws

**Was:** rejection sampling (`while sim.famine.len < FamineProvinces … if draw notin sim.famine`),
so a collision consumed a third or fourth draw and slid the rest of the stream, against
design.md:294-296's "(1) Spring famine, **2 draws**".

**Is:** drawn without replacement — `land.delete(index)` — exactly `FamineProvinces` draws, still
two distinct land provinces (`src/cogiavelli/sim.nim:311-322`).

**Evidence:** `tests/test_sim.nim:487-507` re-derives the first two draws of
`initRand(seed * 104729 + 7)` by hand and asserts the year's famine is exactly those. This changes
which provinces a given seed starves; every other test, the docker smoke and the viewer smoke are
green on the new stream.

## N7 — DISPUTED (the third branch is a termination guard, not a rule)

`backupRule`'s third branch (`adjudicate.nim:250-254`) fires only when a cycle is neither
all-moves nor contains a convoyed move, and it resolves the cycle's first member `false`. It has no
game semantics: it is what makes the resolver terminate on a mixed non-convoy cycle, and
checklist item 5 ("no unbounded loop") depends on it. The note's "backup rules, exactly two"
(design.md:239-242) enumerates the *rules of the game*, and both of them — circular movement and
Szykman — are implemented above it and are the only two that can change an outcome. Removing the
guard to match the note's word count would introduce a hang. No change.

## N8 — a dead-level conquest goes to the lower power index

**Was:** `if counts[power] >= VictoryCities: leader = power` overwrote, so with two powers at
exactly 12 the conqueror was whichever had the higher power index.

**Is:** the leader is the largest holding at or above `VictoryCities`, and a dead-level split — the
only reachable tie, since 12 + 12 = `TotalCities` — goes to the lower power index
(`src/cogiavelli/sim.nim:446-465`).

**Evidence:** `tests/test_sim.nim:508-529` splits all 24 cities evenly between two powers, orders
nothing (so every unit holds and nothing changes hands), and asserts which power takes Italy.

## N9 — an underpaid bribe no longer reads as "defended"

The outcome vocabulary is fixed by design.md:202 and has nowhere else to put an underpayment, so
`money.nim` still records `defended` and the replay schema is unchanged. The *feed* now reads the
`defence` figure the event already carries: with a defence of 0 it prints "That is under the price
and the bribe fails" instead of "…had paid 0 to keep it loyal"
(`client/renderer.js:2020-2037`).

## N10 — DISPUTED (the note contradicts itself; the property that matters holds)

design.md:65-66 says the permutation is drawn "from the same RNG stream as the aliases", and
design.md:302-303 says both are "drawn once at `initSim` from a separate stream" — separate from
the shock stream, which is what the recorded-and-verifiable claim rests on. The code satisfies the
second: `tableNames` uses `initRand(seed * 6779 + 31)` (`sim.nim:186`), the permutation
`initRand(seed * 7919 + 17)` (`sim.nim:243`), and neither touches
`shockRng = initRand(seed * 104729 + 7)` (`sim.nim:249`). Both are pure functions of
`config.seed`, so the replay's self-sufficiency and determinism — the only observable properties —
are unaffected (`tests/test_sim.nim:398-409`). Merging the two streams would change the alias and
power assignment of every existing seed to satisfy a sentence the note itself contradicts. No
change.

## N11 — DISPUTED (the server-side clamp is not a duplicate, it is the only guarantee)

The parse-time clamp (`llm.nim:834`) applies to model replies. `validateSpend`
(`money.nim:70-71`) is the only clamp on the path taken by a spend sheet that did **not** come
through `parseOrdersReply`: `applyOrders` accepts entries from any caller, including `replayMatch`
re-running a recorded log and any policy that constructs a sheet directly. Removing it would let a
recorded `assassinate 3` resolve against a 3-face threshold on replay while the live episode used
6 — i.e. it would break the re-derivation that N1 now checks. `tests/test_money.nim:118-137` pins
the clamp. No change.

## N12 — DISPUTED (the constant is required by the note and used by the test)

`AssassinFaces = 36` is in the note's mandated constant list (design.md:671) and is the bound
`tests/test_money.nim:134` checks every roll against. `6 * (d1 - 1) + d2` is a uniform 1..36 draw
by construction; rewriting the roll to mention the constant would not make it more true, and
deleting the constant would violate the note. No change.

## N13 — DISPUTED (the note's list is of map-table procs, not of the module's surface)

Every extra export is a pure helper the rest of the tree imports: `CityIndex` and `isCity` in
`sim.nim`/`money.nim`, `isSea`/`isCoastal`/`isLand` and `convoyReachable` in `orders.nim` and
`adjudicate.nim`, `codeLess`/`sortByCode` wherever a tie breaks by province code, the 42 area ids
in every test and fixture, `PowerLongNames`/`PowerPromptNames` in the prompts and the feed. Making
`mapdata.nim` export only the note's three procs would not compile. No change.

## N14 — the end-condition assertion says what it means

**Was:** `check(sim.reason == "complete" or sim.reason == "conquest")`, which cannot tell a real
conquest from a bug that ended the episode early.

**Is:** `auditEpisode` asserts the branch it is in (`tests/test_bot.nim:61-82`) — with a named
conqueror the reason must be `conquest` *and* that power must hold twelve cities or be the last
holder; with no conqueror the reason must be `complete` *and* every configured year must have been
played. A new block, `theCanonicalScriptedEpisodeCompletes`
(`tests/test_bot.nim:117-131`), runs a one-year all-scripted table — where conquest is
arithmetically out of reach, six powers starting on three cities each — and asserts
`results.reason == "complete"` outright. Nothing was widened or removed.

**Checklist:** item 7, first half.

## N15 — the endcard's stabs column and the animated ledger

**Was:** five columns (design.md:1053 names six — the `stabs` column was missing) and a single
static 6×6 ledger where design.md:1055 asks for one "animating one year per second in a loop".

**Is:** `stabCounts` totals the broken pledges per power from the recorded `battle` events and the
column renders between `spent` and `score`; `.end-rows` grows to seven columns. `ledgerFrames`
accumulates the ledger year by year, the endcard emits one grid per year, and `animateEndcard`
shows one at a time on a 1 s interval, started from the same Cogiavelli hook that installs the
endcard. Only one interval can exist per page (it is cleared before a new one starts).

**Evidence:** `tests/test_viewer.nim:205-220` asserts the column, the counter, the animation and
both CSS rules. `d7d9792` is a fix-forward: the first version of that assertion split
`"…" in css` across a line, which Nim does not parse (run 32729702869); the literal moved into a
`const` and the assertion is unchanged.

## N16 — DISPUTED (both classes have rules, in the chrome the note says to inherit)

`.feed-it` and `.feed-end` are declared at `/workspace/starters/cogame-babel/client/chrome.css:245-246`
and that file is inherited verbatim above the cogiavelli banner (0 removed lines). The note's
appended-CSS list (design.md:920-922) enumerates what cogiavelli *adds*; a class that the starter
already styles does not need re-adding. No emitted class is without a rule — which is the property
that matters (an unstyled beat kind is an invisible marker). No change.

## N17 — the player's spectate read is bounded

**Was:** `while true: socket.receiveMessage()` — whisky's default `timeout = -1` blocks
indefinitely (`/root/.nimby/pkgs/whisky/src/whisky.nim:28,73`), the literal unbounded blocking read
checklist item 5 says must not exist.

**Is:** the read polls at 5 s and the loop is bounded by the episode timeout —
`COWORLD_TIMEOUT_SECONDS` when the platform sets it, else the configured 1200 s default — plus a
120 s grace (`src/cogiavelli_player.nim:29-107`). That bound is strictly longer than the game's own
budget (60 % of the timeout) plus its 20 s shutdown grace, so a healthy episode still ends on the
`final` frame; a poll that expires is no longer mistaken for a closed socket, and a game container
that dies without closing cannot leave the player process blocked.

**Evidence:** the docker smoke in run 32731615199 runs six real player containers against a real
game and reports `smoke OK: … reason=complete`, so the poll loop still receives frames and exits on
`final`.

## N18 — the mandated prompt is the note's, character for character

Three ASCII hyphens became U+2014 (`llm.nim:663, 667, 678`). Reconstructing the Venice system
prompt from `systemPrompt` and diffing it against design.md:474-508 now returns zero differences
(`diff` run against the note's fenced block during this fix).

## N19 — DISPUTED (the route serves a page; the page needs a token)

design.md:793-794 constrains the **routes**: `/client/player.html` is served by
`htmlHandler("player.html")` (`server.nim:522`) and opens no socket. The served page connects to
`/player` with the `slot` and `token` from its own query string, and the upgrade handler answers a
bad token with 401 (`server.nim:429-435`) — that is what the lantern 0.1.1 lesson is about. The
page is babel's, unchanged apart from the wordmark, the renderer alias, `#ducatbar` and
`relayout()` (diffed against `/workspace/starters/cogame-babel/client/player.html`). No change.

## N20 — DISPUTED (the test is right and the note's sentence is wrong)

`MES` and `PAL` have exactly one land neighbour each — each other (`mapdata.nim:126-127`) —
because the same note requires `CAL–MES` to be the one fleet-only edge and an army to reach Sicily
only by convoy (design.md:138-139). A connected army graph is therefore impossible, and
`tests/test_map.nim:88-113` asserts the truth: two components, 34 + 2. Changing the map to satisfy
design.md:1196 would break design.md:138-139 and the whole convoy story. No change. (I cannot edit
the design note; recorded here as a note-vs-code divergence resolved in the code's favour.)

## Could not determine §1 — the grid harness (checklist item 7, second half)

**Was:** nothing in the tree showed the baselines' constants were fitted. This is the half of item
7 that the review could not settle and that a judge treats as blocking when unverifiable.

**Is:** four things, all in the repo:

1. `tools/tune_baseline.nim` — the harness. It sweeps the condottiere's two treasury gates and its
   vacate penalty (18 points) and the banker's defence floor and per-unit payment (9 points) over
   seeded gunboat self-play, 4 seeds × 3 years, scored by the game's own score. The condottiere is
   measured twice per seed — against the wall it has to break and against its own kind; the banker
   against five expanders. Opponents are pinned to `ReferenceBaseline` (the note's pre-sweep
   figures) so the grid is a fixed target and adopting a fitted point cannot move the post.
2. `src/cogiavelli/llm.nim:52-96` — the constants live in one `BaselineParams` object, and
   `ShippedBaseline` is now **the argmax of both grids**: `bribeTreasury 9`, `buyTreasury 15`
   (both were gates above the price; the fitted gates sit exactly on the 9 and the 15 the entries
   cost), `vacatePenalty 1/2` (unchanged), `defendTreasury 10`, `defendAmount 2`,
   `buildTreasury 30` (unchanged).
3. `docs/tuning.md` — both tables in full, best first, with the CI run they were produced by
   (32731425708), what each axis was, and what moved against the design note.
4. `tests/test_tuning.nim` + `.github/workflows/ci.yml:152-159` — the test re-runs both sweeps in
   CI (debug and release) and fails unless the shipped constants are still the argmax *and*
   `docs/tuning.md` still records them; the workflow runs the harness itself with `--check`.

**Evidence:** run 32731425708, step "Sweep the scripted baselines' parameter grid":
`best 0.1816, shipped 0.1816` for the condottiere, `best 0.1063, shipped 0.1063` for the banker,
`tune_baseline: the shipped constants are the fitted ones`. Reproduced green in run 32731615199 on
the head sha.

**Two fix-forwards are in this history and are mine:** `6d55306` first adopted the raw argmax
(`bribe>=8`, `buy>=16`), which made the condottiere write a 9-ducat bribe it could not pay for and
turned `tests/test_bot.nim`'s "every spend entry is affordable when it is written" red (run
32730784263). `044223b0` makes affordability an invariant of the baseline rather than of the
tuning — both spend procs clamp their gate to the price they are about to pay
(`llm.nim:335, 357, 434`) — moves the grid's low points onto the prices themselves, and records
the re-run. The behaviour of the note's own text ("bribe_disband … for exactly 9") is unchanged;
only the treasury at which the baseline is willing to do it moved.

**Note-vs-code divergence, deliberate and recorded:** design.md:577-588 states the pre-tuning
figures 12 / 20 (condottiere) and 15 / 4 (banker). The sweep moved four of them. Item 7 asks for
constants that were *fitted*, and the tree now shows the fit; `docs/tuning.md` §"What this
changed" states the divergence explicitly, and the design note is not edited.

## Could not determine §2 — intra-resolution frames share one state (noted, by design)

`replayMatch` pushes one frame per recorded event, and the `applyOrders` that closes a phase runs
the whole cascade in one call, so the frames attached to that season's `spend`, `assassin`,
`bribe`, `battle`, `cities`, `plague` and `season` events are the same post-cascade state. This is
babel's shape and changing it means re-shaping `resolveSeason` to yield intermediate states — a
design change, not a fix, so I did not make it.

What checklist item 2 asks for is nevertheless satisfied and now tested: the recorded per-tick
state is carried *in the events* (each board-bearing event carries the board as it stood when that
event was emitted, mid-cascade), and N1's change compares every one of those snapshots against the
re-derivation field by field. The viewer's display comes from that re-derivation
(`replay-viewer/cogiavelli_replay.nim:38-39`), not from a parallel recording, and the feed line and
clock for an intra-resolution beat come from the event itself. The soak in run 32731615199
(`10s of playback kept advancing`) shows nothing blanks or hangs.

## Could not determine §3 — DISPUTED: `readCogameUri` has no unbounded branch

`readCogameUri` (`/root/.nimby/pkgs/bitworld/src/bitworld/runtime.nim:97-120`) has exactly three
branches: `file://` → `readFile` (bounded for a regular file), `http(s)://` → curly's `get` with
its 60 s default, and anything else → an immediate raise. The manifest declares
`ANTHROPIC_API_KEY_URI = "secret://coworld/cogiavelli/anthropic_api_key"`
(`coworld_manifest_template.json:27`), which the platform resolves to a signed HTTPS URL before the
container sees it — the HTTP branch, i.e. the bounded one. The call is one-shot at
`newLlmClient`, before the episode clock starts, and is wrapped in `except CatchableError`
(`llm.nim:113-117`) so a failure disables the client and the episode plays scripted. A FIFO at a
`file://` path is not something the platform mounts, and Nim's `readFile` cannot be given a
timeout without a thread. No change.

## NOTED (not fixed)

- `ledgerText` prints only *applied* entries, so design.md:348-350's "including every failed bribe
  and every missed assassination with its dice" is not in the prompt's ledger block (the dropped
  entries and the dice **are** in the replay, in the `spend` and `assassin` events). Not a finding
  in this review; recorded for the next one.
- `docs/tuning.md`'s grid is 4 seeds × 3 years so it can run inside the test job. A wider sweep
  (more seeds, 4-year episodes, a press variant) would be a better fit and is a natural phase-60
  follow-up; the harness takes both as constants at the top of the file.
