# r2 fixes — escrow

Head: `798d9504155b23b60210a166bd1871a1a4538327` (main)
CI: https://github.com/Metta-AI/cogame-escrow/actions/runs/32648809792 — **success**
(jobs `test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓; every step `success`).

One commit per finding, each pushed and CI-checked on its own sha:

| finding | disposition | commit | files |
|---|---|---|---|
| F1 (blocking) | fixed | `4d33973` | `src/escrow/llm.nim:34-49,167-206`, `tools/tune_baseline.nim` (new), `docs/tuning.md` (new), `.github/workflows/ci.yml:150-164` |
| F2 | fixed | `baeecc8` | `client/renderer.js:822-833` |
| F3 | DISMISSED (needs a design change to be fixable, and buys nothing) | — | `src/escrow/sim.nim:508-534`, `:939-964` |
| F4 | fixed | `798d950` | `tests/test_bot.nim:11-70` (stub endpoint), `:366-427` (test 18) |
| F5 | fixed | `555c02f` | `src/escrow_player.nim:17,36-43,63-81` |

Per-commit CI, all `success`: `4d33973` → run 32648479931, `baeecc8` → 32648585268,
`555c02f` → 32648683875, `798d950` → **32648809792** (the head).

---

## F1 — the baseline's parameters had no tuning artefact (checklist item 7, second sentence)

**What the code did.** `llm.nim:34-39` stated `HousePrice = 3/3/3/1` and `TradeUnits = 4` as
constants with a rationale comment but no measurement, and nothing anywhere in the tree swept
them. Checklist item 7's "**The baseline's parameters were tuned with a grid harness, not
guessed**" had no evidence.

**What the code does now.**

1. **The knobs are addressable.** `TraderParams` (`llm.nim:35-49`) holds `housePrice`,
   `tradeUnits` and `needFills` (the copies of its own commission the trader reserves before
   calling a good surplus — previously hard-wired to `MaxFills` inside `twoFillNeed`).
   `DefaultTraderParams` (`llm.nim:172-195`) is the shipped cell, and
   `bundleValue`/`twoFillNeed`/`traderAction`/`scriptedAction` take it as a **defaulted**
   argument, so `server.nim:335`, `llm.nim:663`, `llm.nim:708` and every existing test call site
   are unchanged and get the shipped values.
2. **The harness is committed and was run.** `tools/tune_baseline.nim` plays whole all-scripted
   episodes through `escrow/sim` + `escrow/llm` — `initSim` / `pendingSeats` / `scriptedAction` /
   `applyMove`, the same calls `server.nim`'s turn loop makes — so it measures the shipped bot,
   not a model of it. Every decision goes through `sim.validateMove`, every episode's event log
   is scanned for a `reject`, and `liveContracts` is checked against `MaxLive`, so an illegal
   cell is disqualified before it can win. Per cell it reports mean hearts minted, the ratio
   against the same-seed all-hoarder floor, mean end hearts, mean signings, and a
   3-trader/1-hoarder **mixed-field** column (the baseline is a fielded policy, so a cell that
   only pays when all four seats play it is not a good cell). Flags: `--seeds --turns --units
   --fills --price --quick --check`.
3. **The sweep changed the shipped values.** The guessed 4/2 is *not* the argmax; the harness's
   winner was adopted, and no test had to be weakened to take it (all cells were legal; the 1.3×
   canary is cleared with room).

**Headline numbers** (5 seeds `1,7,42,1234,20260823`, 16 turns, 45 cells — the recorded grid is
in `docs/tuning.md`):

| cell (units/fills) | hearts minted / seed | vs the 474 autarky floor | mixed field (trader vs hoarder) |
|---|---|---|---|
| **6/3 — adopted** | **1074** | **2.27×** | **180.4 vs 132.8** |
| 4/2 — the old guess | 834 | 1.76× | 164.4 vs 132.8 |
| 3/3 | 814 | 1.72× | 163.1 |
| 5/1, 5/2 | 774 | 1.63× | 160.4 |
| 3/2 (worst) | 552 | 1.16× | 146.4 |

A wider 66-cell sweep (`--units=2..12 --fills=1..6`) confirms 6/3 is not an edge artefact: it is
still the maximum, tied only with 6/6; 7..12 units are all worse. 45/45 and 66/66 cells legal.

**The price axis is degenerate, and the harness says so rather than pretending to have chosen.**
Every price column of the grid is identical, because a baseline contract is always an
equal-count swap of two goods and a **flat** table values that at zero gain at any level, so no
price in 2..4 changes a single decision in an all-scripted episode. The table therefore stays at
3/3/3 with hearts at 1 — flat so an equal swap is exactly fair, hearts cheap so score is never
bought as an input. That level bites only on a *model's* asymmetric offer, which an all-scripted
sweep cannot produce; `docs/tuning.md` records that as the constraint that binds this knob, and
that it is a judgement rather than a measurement.

**Reproducibility in CI.** `.github/workflows/ci.yml` gains one step in the existing `test` job,
`Re-run the baseline tuning sweep`, running `--quick --check` (2 seeds, 12 turns, one price
column, 60 episodes, ~1 s). `--check` exits non-zero if the shipped cell is beaten, is illegal,
is outside the swept ranges, or drops under 1.3×. No existing job, step or assertion was
weakened.

**Evidence.** CI run 32648809792, job `test`, step `Re-run the baseline tuning sweep`:
`argmax: price=3 tradeUnits=6 needFills=3 -> 786.0 hearts minted (2.15x the autarky floor), …
174.3 hearts a trader against the hoarder's 133.0` then
`check: the shipped cell is still the grid's best legal cell`. Test 13 (legal orders by
construction) and test 14 (the ≥1.3× canary) are untouched and green in both debug and
`-d:release`; test 14 now prints `traded 1074 vs autarky 474` per seed.

**Checklist item satisfied:** 7, both sentences — the first was already satisfied (test 13 +
legality by construction), the second now has a committed harness, a durable record
(`docs/tuning.md`), an adopted argmax, and a CI gate.

## F2 — an over-cap reject rendered as a refused contract draft with a raw reason code

**What the code did.** `evReject` serves two refusals — a draft the parser threw out and a move
carrying more gives/signings than a turn allows — and `renderer.js:822-824` worded its single
feed line for the first, so a dropped third give read
`Sprocket's draft was refused — over_cap: 1 gives past the cap of 2 dropped`: a draft that does
not exist, plus an internal token, both of which design.md:584-600 rules out of the feed.

**What it does now.** `client/renderer.js:822-833` matches the `over_cap:` reason code and
renders `Sprocket tried more actions than one turn allows — 1 gives past the cap of 2 dropped`,
leaving every other reject on the draft line. **Rendering only**: the event, its reason code and
`tests/test_sim.nim` test 5d's `startsWith("over_cap")` assertions are untouched, so the
machine-readable code the design note asks for survives.

**Evidence.** Parsed the file with `new Function(src)` locally and checked both branches of the
regex; CI's `wasm-viewer` job loaded the real smoke replay in headless chromium at head —
`{"loaded":true,"ms":280,…,"feed_lines":66}`.

## F3 — reject events are not re-derived on replay — DISMISSED

Confirmed at `sim.nim:508-516` and `:939-964`: the recorded `move` event carries the
**truncated** lists, so `replayMatch` rebuilds a `Move` that is already at the cap and the
`if` at `:511` cannot fire. Dismissed on two grounds:

- **No consequence.** A `reject` moves nothing; `tableStateJson` carries no event list
  (`sim.nim:871-912`), `replayMatch` compares only `evTurn` seat state (`:943-948`), and the
  viewer's feed reads the **recorded** `payload.events` (`renderer.js:1319`, `:1338-1341`), so a
  spectator sees the reject either way. The review reaches the same conclusion.
- **Fixing it is a design change, not a fix at the cited site.** Re-deriving the event needs the
  *pre-truncation* counts, which the replay deliberately does not record (recording the
  untruncated move would mean the replay carries actions the sim refused). Changing the replay
  event schema for an event that is unreachable on every live path (`llm.nim:604-615`,
  `:175-268`, `sim.nim:950-956` — only a hand-built `Move` in a test reaches it) is not worth a
  schema change. If the judge wants it, the change is: add `drops` to the recorded `move` event
  and have `replayMatch` re-emit — that is a `NEEDS-DESIGN`, and it is recorded here rather than
  made.

## F4 — no test exercised the `scripted == false` line

**What the code did.** Tests 15 and 17 covered both fallback paths; nothing drove a reply that
parses *and* validates, so `llm.nim:697` (`SeatDecision(move: decision, scripted: false)`) never
ran under assertion, and no test covered a mixed batch. The review listed this in "could not
determine".

**What it does now.** `tests/test_bot.nim` test 18 stands up a stub Bedrock endpoint on a
loopback socket (a real socket — curly speaks real HTTP, including the `Expect: 100-continue`
handshake the stub answers), points the client at it with
`AWS_ENDPOINT_URL_BEDROCK_RUNTIME`, and runs one batch with **seat 0 registered as the scripted
trader and the other three model-driven**. It asserts the stub served exactly `Seats - 1`
requests (so no retry batch ran), that seat 0 is `scripted: true` and equals
`scriptedAction(sim, seat, skTrader)`, that the other three are `scripted: false` and carry the
stub's `say`/`notes` (proof the reply was parsed and validated, not faked), and that the
recorded `move` events split 1 scripted / 3 not — which is what phase 60 counts.

The stub thread is bounded twice over: the test flips a stop flag and joins, and 10 s of silence
retires the thread anyway, so a broken test cannot hang CI. Every wait inside it is a
`selectRead`/`recv` with an explicit timeout.

**Evidence.** 32 consecutive local runs (debug and `-d:release`) green; CI run 32648809792 job
`test` shows `[OK] 18. an accepted model reply is recorded as the model's own` in **both** modes.

**Checklist item:** 8 — the fallback flag is now asserted from both sides, so the count phase 60
makes is verified end to end rather than only on the fallback path.

## F5 — the player's frame loop was an unbounded blocking read

**What the code did.** `escrow_player.nim:54-58` called `socket.receiveMessage()` with no
timeout — the one wait in the tree with no explicit bound, against checklist item 5's literal
"no … blocking read" clause. Reading whisky at the pinned version also shows the comment was
wrong about the mechanism: `receiveFrame` **raises** on a closed socket
(`whisky.nim:29-31`) and only a `TimeoutError` yields `none` (`:73-78`), so the branch labelled
"connection closed" was unreachable and a real close escaped as an unhandled exception.

**What it does now** (`escrow_player.nim:36-43`, `:63-81`): the read takes a 5 s timeout, so
`none` means exactly that timeout and the loop re-arms; a player that has heard **nothing** for
300 s stops waiting (the server broadcasts every turn and a turn is bounded at
`2 × llmTimeoutSeconds + 5` = 125 s, so that much silence means the game is gone); and a raised
close breaks the loop and closes cleanly instead of aborting the process.

**Evidence.** Ran it for real, locally: the game server binary plus **four** real player
binaries, 5 turns, seed 5 — every player logged `seated at slot N as <cog> (<profile>)`, played
through, logged `final hearts [90,90,90,92]` and **exited 0**. CI's `docker-smoke` then ran the
same binaries in the production image: `smoke OK: seats=4 results=267B replay=10664B
reason=complete`.

**Checklist item:** 5 — every wait in the tree now has an explicit bound, including this one.

---

## NOTED (not fixed)

- `sim.history` / `TurnRecord.moves` are write-only dead state (`sim.nim:121`, `:476`,
  `types.nim:188`; no reader anywhere). Inherited from the starter, no checklist item touches it,
  not a finding this round — left alone.
- `renderer.js`'s `reject` line is still the only feed line for a *parser* rejection, and it
  shows the parser's own reason codes (`LOCK is not a bundle`, etc.). Those read as prose
  already, so they were left as they are; only the `over_cap:` token was internal.
- The `except EscrowError` around `applyMove` (`server.nim:332-336`) remains unreachable dead
  code, as the review notes. Not a finding; untouched.
