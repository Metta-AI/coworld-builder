# r1 fixes — contagion

Repo: `Metta-AI/cogame-contagion`, branch `main`.
Range: `7cba8a0..66e0821` — 8 commits, one per finding.
Head: `66e0821721a72390bf4ce9e7a6ae2520dc8ce023`
CI: https://github.com/Metta-AI/cogame-contagion/actions/runs/32637561078 — run **32637561078**,
`event: push`, `headSha: 66e0821721a72390bf4ce9e7a6ae2520dc8ce023`, conclusion **success**.
Jobs: `test` 97189491940 success, `docker-smoke` 97189492117 success, `wasm-viewer` 97189615823
success. `grep -c SEAT-COUNT` over the whole run log: **0**. `smoke OK: seats=6 results=339B
replay=19809B reason=complete`. All five `tests/*.nim` ran twice (debug and `-d:release`),
including the new `tests/test_sweep.nim`.

Pushed with the GitHub Git Data API (blobs → tree → commit → `PATCH` ref, `force: false`),
one API commit per local commit; HTTPS `git push` is rejected for this repo. `git diff HEAD
origin/main` after the push is empty, so the pushed tree is byte-identical to the tested one.
The two `100755` helpers (`tools/build_replay_viewer.sh`, `tools/ci/docker_smoke.sh`) were not
touched and their modes are preserved by `base_tree`.

| finding | disposition | commit | files |
|---|---|---|---|
| **B1** — LLM-retry-exhausted fallback recorded as `scripted: false` | **fixed** | `37af17e` | `src/contagion/llm.nim:601-676`, `src/contagion/server.nim:285-300`, `tests/test_bot.nim` |
| N1 — `/client/replay` route and two doc mentions exist | **REFUTED** | — | `server.nim:472`, `coworld_manifest_template.json:17-19` |
| N2 — unconnected seat is LLM-driven when credentials exist | **fixed** | `b648cac` | `src/contagion/server.nim:214-244`, `tests/test_bot.nim` |
| N3 — certification fixture seats `contagion-player` at slot 0 | **REFUTED** | — | `coworld_manifest_template.json:428-447`, `tests/test_manifest.nim:107-124` |
| N4 — `chrome.css` changes more than "two additions" | **REFUTED** | — | `client/chrome.css` |
| N5 — measured calibration differs from the note's table | **REFUTED** (and superseded by the tuning in `4d3d6f0`) | — | `tests/test_bot.nim:90-120` |
| N6 — `curves` carries a fourth series `confirmed` | **REFUTED** | — | `src/contagion/sim.nim:726-755` |
| N7 — `edges[].flow` is a two-way susceptible-weighted count | **REFUTED** | — | `src/contagion/sim.nim:359-377` |
| N8 — in-lock rejection fallback reads a partially latched sim | **fixed** | `08ba0f8` | `src/contagion/server.nim:301-312`, `tests/support/helpers.nim:32-48` |
| N9 — non-rune-safe slices on captured HTTP error bodies | **fixed** | `b2387da` | `src/contagion/llm.nim:401-481` |
| N10 — feed wording; one line mixes the two name spaces | **fixed** (name spaces) / **REFUTED** (wording) | `2ad39e2` | `client/renderer.js:841`, `:889` |
| N11 — `weeks < 4` raises instead of clamping | **fixed** | `66e0821` | `src/contagion/types.nim:148-153`, `tests/test_sim.nim:75-88` |
| N12 — `curl.makeRequests` is outside the per-seat `try` | **REFUTED** | — | `~/.nimby/pkgs/curly/src/curly.nim:711-715` |
| CND-1 — item 7's "tuned with a grid harness, not guessed" | **fixed** | `4d3d6f0` | `tests/test_sweep.nim` (new), `src/contagion/llm.nim:151-189` |
| CND-2 — can `makeRequests` raise; is `timeout` seconds | **settled, no change** | — | `curly.nim:711-715`, `:290`, `:1029` |
| CND-3 — do `readCogameUri`/`writeCogameUri` carry timeouts | **settled, no change** | — | `bitworld/runtime.nim:97-123`, `:193-226`; `curly.nim:1184-1211` |
| CND-4 — per-week ceiling under non-default config | **fixed** | `9454773` | `src/contagion/llm.nim:626-641`, `tests/test_bot.nim` |

**8 fixed, 6 refuted, 2 settled by evidence with no code change.**

No test was deleted, skipped, or loosened. `tests/` gained one file
(`tests/test_sweep.nim`, 146 lines) and four new tests inside existing files; the only edits to
existing test code are two `scriptedDecision(sim, …)` → `scriptedDecision(view, …)` comparisons
that were themselves instances of the N8 defect, and they compare against a *stricter* reference
(the pre-batch snapshot) rather than a looser one.

---

## B1 — an LLM seat that exhausts its retry is recorded as `scripted: false`

**Fixed — `37af17e`.** Checklist item 8.

*What it did.* `decideAll` returned only `seq[Decision]`. A seat still open after the retry got
`scriptedDecision(sim, seat, skSentinel)` (`llm.nim:659-662`) and an `echo`, and nothing else. The
server then re-derived the event flag from the seat's **registration** —
`let wasScripted = scripted[seat] != skNone or client.disabled` (`server.nim:291`) — so for a seat
registered as an LLM policy with a live client, a timeout / transport error / parse failure / hard-
invalid reply on both attempts produced a `dial` event with `"scripted": false`, indistinguishable
in the replay bytes from a model reply. The reviewer's trace is exactly right.

*What it does now.* `decideAll` returns `tuple[decisions: seq[Decision], scripted: seq[bool]]`.
`result.scripted[i]` is set true in both places a scripted move is produced: the
registration/no-credentials branch (`llm.nim:637-642`) and the retry-exhausted fallback
(`llm.nim:674-676`). The server takes the flag straight from the batch
(`server.nim:293-300`) instead of re-deriving it, so the per-seat fact reaches `applyDecision`,
`event.scripted`, `eventToJson`'s `"scripted"` field and the feed's `" (scripted)"` suffix.

*Evidence.* New test `tests/test_bot.nim` — "a seat that exhausts its retry is recorded as scripted
in the replay". It builds a **real** `LlmClient` on the Bedrock transport pointed at
`http://127.0.0.1:1` (no network egress; `client.disabled` is asserted false), runs a genuine
two-attempt `curly` batch that fails on both, then applies the six decisions exactly as the server
does and asserts `event.scripted` and `event.eventToJson()["scripted"].getBool()` on all six `dial`
events. Local run, debug and `-d:release`:

```
contagion llm: seat 0 attempt 0 failed: llm transport: Couldn't connect to server POST http://127.0.0.1:1/...
contagion llm: seat 0 attempt 1 failed: llm transport: Couldn't connect to server POST http://127.0.0.1:1/...
contagion llm: seat 0 falling back to the sentinel move
  [OK] a seat that exhausts its retry is recorded as scripted in the replay
```

This exercises the `decideAll`-internal fallback, not the already-marked `applyDecision` rejection
path, which is the case the finding named.

---

## N1 — `/client/replay` route and two doc mentions exist

**REFUTED.** Checklist item 3.

Item 3's substantive requirements are all met and the reviewer traced every one of them: the
manifest declares `"replay_viewer": {"bundle": "static-replay-viewer"}`
(`coworld_manifest_template.json:17-19`), `tools/build_replay_viewer.sh` exists, is committed
`100755` and is invoked by path in `ci.yml:225-249`, and the bundle's only `fetch(` is
`static_replay.js:76` on the `?replay=` URL. `test_manifest.nim:20-25` asserts
`"client/replay" notin manifest["game"]["replay_viewer"]`.

The route at `server.nim:472` is a debug page served by the **game** container, not a pod-served
replay viewer declared to the platform: nothing in the manifest points the platform at it. It is
inherited verbatim from the starter (`cogame-bullwhip/src/bullwhip/server.nim:470`) and it is
prescribed by this design note twice — design.md:513-515 lists it in the routes, design.md:799-800
asks for "a pointer to `/client/global`, `/client/replay` and the static bundle". Removing it would
put the tree at odds with its own design note in order to satisfy a literal reading of a clause
whose purpose ("the platform must serve the static bundle, not a pod") is already satisfied. Not
changed.

---

## N2 — an unconnected seat is only a sentinel when the LLM client is disabled

**Fixed — `b648cac`.** Checklist items 5 and 7.

*What it did.* `state.scripted` starts at `skNone` for every seat (`server.nim:526`) and the
connect loop starts the game after `playerConnectTimeoutSeconds` regardless
(`server.nim:220-226`). A seat whose container never connected therefore reached `decideAll` with
`kind == skNone`, and `llm.nim:620` sent it to the model whenever credentials existed — a round
trip a week spent on an unguided-prompt policy with nobody behind it.

*What it does now.* `pinUnconnectedSeats` (`server.nim:214-227`) is called under the lock at the
moment the game starts and pins every still-unconnected, still-`skNone` seat to `skSentinel`. A
seat that already registered a baseline keeps it; a late connect takes the seat back when its
prompt frame lands (`server.nim:449-451` still overwrites `state.scripted[slot]`), which is what
"the game starts with whoever is there" means.

*Design note.* design.md:320-324: "after `player_connect_timeout_seconds` (180) the game starts
with whoever is there, and **unconnected seats are treated as `PLAYER_SCRIPTED=sentinel`**".

*Evidence.* `tests/test_bot.nim` — "a seat whose container never connected plays the sentinel
baseline": asserts the mixed case (one connected, one laggard-registered, one sentinel-registered,
three absent) and the zero-sockets case.

---

## N3 — the certification fixture seats `contagion-player` at slot 0

**REFUTED.**

The note's fixture (`design.md:827`, six scripted seats) cannot be shipped: `coworld certify`'s
players-ran check fails any **declared** player that never occupies a certification slot, and
`contagion-player` is declared in `manifest["player"]` because it is the runnable every fielded
prompt policy reuses. `test_manifest.nim:107-124` encodes exactly that invariant
(`declared == seated`), and it is not a test I could satisfy by deleting the declaration without
removing the game's only fieldable player image.

The reviewer's residual concern — "if `ANTHROPIC_API_KEY_URI` resolves during certification the LLM
path is exercised there" — is bounded and, on balance, desirable: certification then exercises the
one code path no CI job can (`docker_smoke.sh:198` deliberately runs with no key), at a worst case
of 6 weeks × `turnBudgetSeconds` 35 = 210 s against a 1200 s episode timeout, and with commit
`9454773` the first batch can no longer exceed the week budget under any config. CI proves the
fixture completes: run 32635551779 job 97184628980, `smoke OK: seats=6 results=342B
replay=19848B`. Not changed.

---

## N4 — `chrome.css` changes more than the note's "two additions and nothing else"

**REFUTED.** Checklist item 11.

The note's sentence was written before the plate count was six. Every additional hunk the reviewer
lists is plate geometry in service of six plates fitting where the starter had four —
`repeat(6, 1fr)`, tighter gaps, the ellipsis rules on `.plate-label`, and a 3-column 640 px block.
The rule item 11 actually names is untouched: `.plate-name` still carries
`min-width: 3.2em; flex: 1 1 auto` (`chrome.css:282-294`), asserted at
`test_manifest.nim` ("chrome.css keeps the plate-name rule and both media blocks"). The CI viewer
smoke renders the scorebug legibly at the pinned viewport (run 32635551779 job 97184741494,
`"scorebug":"Sprocket ▶ 0 RIVERBEND Gizmo ▶ 0 ASH …"`). Reverting the geometry to the four-plate
starter would break the thing item 11 protects. Not changed.

---

## N5 — measured calibration differs from the note's illustrative table

**REFUTED**, and largely superseded by `4d3d6f0`.

The reviewer did the decisive work here themselves: they re-derived the note's constants by hand
and found *the code* self-consistent and *the note's arithmetic* wrong — ≈ 1 M × 0.35/week to
exhaustion at the 3.2 % overload ceiling is ≈ 30 k deaths, not the note's 21 k, and the note's own
GDP figure for that row (≈ 15 000) matches the code exactly. Changing `sim.nim` to reproduce an
arithmetic slip in a planning document would be the wrong direction, and the note's *ordering and
signs* — the part that is load-bearing — are asserted at `test_bot.nim:102-103` and `:118-120`.

One row did move, in the note's direction, for an unrelated reason: the grid tuning in `4d3d6f0`
puts the sentinel ("timed suppression") row at mean seat score **11 269** against the note's
**≈ +11 400**, where the guessed thresholds gave 9 114. Current measured values on `main`:

```
idle mean score -45575 deaths 182375 | locked mean score 5902 deaths 2601
seed 7: sentinel deaths 2204 mean score 11269 | laggard deaths 181689 mean score -46317
```

Not changed in `sim.nim`.

---

## N6 — `tableStateJson.curves` carries a fourth series `confirmed`

**REFUTED.**

The note's §7 asks for exactly the picture this series draws: "each region's *reported* curve dotted
underneath" the true one (design.md:693-697). The three-series line at design.md:458 is the note
being terser than itself thirty lines later. The series is additive — no existing key changed shape
— it is revealed only up to the current week like the others (`sim.nim:732-736` iterates
`sim.history`), it is asserted (`test_sim.nim:639`), and it is not part of the `week` event or
`RegionState`, so `replayMatch`'s field-for-field check is unaffected. Not changed.

---

## N7 — `edges[].flow` is a susceptible-weighted people count from both ends

**REFUTED.**

The note's phrase ("`Σ imp` in people", design.md:463-464) is self-contradictory: `imp` is a ppm
force, not people. The code resolves the ambiguity in the only way that yields the stated unit —
susceptible × force ÷ 1e6 — and accumulates both endpoints into the road's single value, which is
correct for a quantity the viewer draws on the road rather than on an end. It is reset each week
(`sim.nim:359-360`), is viewer-only (nothing in the rules reads it), and is outside the replay's
field-for-field check because the viewer recomputes it in the re-derived frames rather than reading
it from the replay — i.e. it cannot desynchronise a replay. Not changed.

---

## N8 — the fallback move inside the apply loop is computed from a partially latched sim

**Fixed — `08ba0f8`.** Checklist items 2 and 7.

*What it did.* `applyDecision` latches into live state immediately (`sim.nim:463-471`). The main
decision path is clean — every seat's decision comes from `simCopy`, taken before the batch
(`server.nim:275-277`) — but the in-lock rejection fallback called
`scriptedDecision(state.sim, seat, skSentinel)` *after* lower-index seats had latched. The sentinel
reads its neighbours through `estimatedRatePpm` → `confirmed / DetectPpm[region.testing]`, and
`testing` is one of the values already latched, so the fallback could see a neighbour's week-`w`
testing decision — which design.md:156-157 forbids ("no governor sees another's week-`w` decision
before submitting").

*What it does now.* The fallback comes from `simCopy` (`server.nim:301-312`), the same pre-batch
view every other seat's decision came from.

`tests/support/helpers.nim`'s `playScripted` had the identical defect — decisions generated from
the mutating sim in ascending seat order — and it is the harness the calibration assertions and the
new sweep run on, so it now takes one snapshot per week before any of that week's six decisions
latch.

*Evidence that the leak was real and is gone.* The measured all-sentinel seed-7 mean score moved
9114 → 9079 on the helper fix alone, i.e. the leak was changing outcomes. It also showed up
directly in my own first draft of the B1 test, which compared `batch.decisions[index]` against
`scriptedDecision(sim, …)` recomputed on the mutating sim and produced
`borders: [0, 2, 0]` vs `[0, 1, 0]` once the thresholds were tuned; both `decideAll` tests now
compare against the pre-batch view.

---

## N9 — non-rune-safe slices on captured HTTP error bodies

**Fixed — `b2387da`.** Checklist item 9.

The four diagnostic heads in `textOf` were byte slices
(`response.body[0 .. min(response.body.high, 400)]` and three siblings) and could cut a multi-byte
sequence, putting invalid UTF-8 into the hosted container log. The reviewer is right that none of
them reach the replay — `eventToJson` (`sim.nim:931-966`) emits only `say`, `text` and numbers —
so this was not an item-9 falsification. It was still the one place in the file that was not
rune-safe for no reason, and it cost five lines: they now go through `cleanText`, the same
rune-boundary trim the replay-bound strings use, which `cleanText` moved above the transport
section (unchanged) to make visible. `cleanText`'s rune behaviour is already covered by
`test_bot.nim` "free text is truncated on rune boundaries" (400 × `é` → `runeLen == 160`,
`validateUtf8() == -1`).

---

## N10 — feed wording, and one feed line mixing the two name spaces

**Name spaces: fixed — `2ad39e2`. Wording: REFUTED.** Checklist item 4.

*Fixed.* The aid line mapped the **sender** through the policy-name map
(`clampName(nameMap.seat(event.seat))`) but left the **recipient** as a raw region alias, so one
line could read `daveey-warden sends 150 to Riverbend`. The `dial` line's `closes <road>` list had
the same split. Both now go through `nameMap.text` (`renderer.js:841`, `:889`), the same
alias→display map the `say` and `notes` lines already used, so a spectator line is entirely in
display names and a replay with no policy names is entirely in aliases. The replay bytes are
untouched: `entry.to` and `b.to` are aliases by construction (`sim.nim:663-666`); this is rendering
only, and the CI viewer smoke re-renders the feed (`"feed_lines":77`).

*Refuted.* The note's `Riverbend — aid clamped to ledger` and `Saltmarch falls back (timeout)`
(design.md:705) are illustrative instances of two classes the code has to cover generally.
`corrected` is set by six different corrections (unknown road, out-of-range gate, self/unknown/
negative recipient, fourth aid entry, over-budget aid) — "aid clamped to ledger" would be a false
label for five of them, where "reply corrected to a legal move" is true for all six. Likewise
`event.scripted` is true for a registered baseline and for a fallback alike (and, after `37af17e`,
for a timeout fallback), so "falls back (timeout)" would be a false label for the certification
episodes where every seat is a registered baseline. The code's wording is the accurate
generalisation of the note's examples; I did not make the rendering lie in order to match a
docstring.

---

## N11 — `weeks < 4` raises at config-load rather than being clamped

**Fixed — `66e0821`.**

`contagion.nim:33` calls `config.update` before `sampleEpisode(config)` (`:41`), so the raise at
`types.nim:150` made the lower half of the clamp the note specifies (design.md:410, `sampleEpisode`
"clamps `weeks` to 4..40") dead code: `weeks: 2` killed the container at startup with no results
and no replay, while `weeks: 400` was silently clamped. The raise is gone and the two bounds now
behave the same way. The invariant is still checked — `initSim` (`sim.nim:234`) raises below
`MinWeeks` and runs *after* the clamp — and the manifest schema pins `weeks` to 4..40, so this is
unreachable from the platform either way.

*Evidence.* `tests/test_sim.nim` — "a runtime config's week count is clamped, not fatal":
`{"weeks": 2}` → `MinWeeks`, `{"weeks": 400}` → `MaxWeeks`, `{"weeks": 12}` → 12.

---

## N12 — `curl.makeRequests` is outside the per-seat `try`

**REFUTED**, with the evidence the reviewer said would settle it.

`curly` 1.1.1 is pinned in `nimby.lock`
(`curly 1.1.1 https://github.com/guzba/curly a0f42baacbc48f4e5924b18854c0df9dcc251466`), and its
signature is:

```nim
proc makeRequests*(
  curl: Curly,
  batch: RequestBatch,
  timeout = 60
): ResponseBatch {.raises: [], gcsafe.}
```

(`~/.nimby/pkgs/curly/src/curly.nim:711-715`.) `{.raises: [].}` is compiler-enforced: it **cannot**
raise. Transport failure is reported per request in `responses[].error`, which
`llm.nim:656-657` handles inside the per-seat `try`. The scenario N12 describes — an exception
escaping `decideAll`, escaping `runGame` and killing the game thread — is unreachable. Wrapping the
call would add a handler for a case the type system already excludes. Not changed.

---

## CND-1 — item 7's "tuned with a grid harness, not guessed"

**Fixed — `4d3d6f0`.** Checklist item 7.

The reviewer's grep was right: there was no harness, and the shipped thresholds were the design
note's illustrative numbers (design.md:371-386), which the note itself does not claim to have swept.

**The harness.** `tests/test_sweep.nim` (146 lines, runs in CI with every other `tests/*.nim`, 2.5 s)
sweeps the sentinel's two threshold families — the OWN-prevalence cuts that set lockdown and
testing, and the NEIGHBOUR-prevalence cuts that set the gates — over a ×0.25 … ×4 grid, five seeds
a cell, six seats a seed, every episode played to `reason == "complete"`. It prints the whole
surface and asserts three things: the shipped constants are the grid's **best cell**, no other cell
beats them, and the optimum is **interior in both dimensions** (a best cell on the grid edge would
mean the sweep had not converged and the shipped numbers were merely the tightest thing tried).
Each week's six decisions come from one pre-latch snapshot, per `08ba0f8`, so the sweep is tuning
the game the server actually plays.

**The result.** The note's thresholds were not that cell. The first sweep I ran over them scored
**9 150** mean seat score against **11 206** for the argmax, with **16 of 48** cells beating them.
The thresholds are now the argmax, hoisted into exported named constants that the harness reads —
so the harness cannot drift onto stale literals — and re-verified as a unique interior optimum:

```
  own\road |    250000    500000   1000000   2000000   4000000
    250000 |     10867     10860     10843     10609     10442
    500000 |     11068     11087     11090     10943     10729
   1000000 |     11175     11174     11206     11006     10914      <- x1 = shipped
   2000000 |     10740     10769     10743     10548     10315
   4000000 |      8039      7770      7692      7364      7137
  best cell own x1000000 road x1000000 score 11206 | shipped score 11206 | cells that beat it 0/24
```

CI run 32637561078, job `test` 97189491940, both the debug and the `-d:release` pass print that
same line.

| constant | was (guessed) | is (swept) |
|---|---|---|
| `SentinelLockdownCutsPpm` | 2 000 / 8 000 / 25 000 / 60 000 | 1 000 / 4 000 / 12 500 / 30 000 |
| `SentinelTestingCutsPpm` | 2 000 / 25 000 | 1 000 / 12 500 |
| `SentinelRoadCutsPpm` | 4 000 / 20 000 | 160 / 800 |

Measured effect, all six seats sentinel, 20 weeks, seed 7: mean seat score **9 114 → 11 269**,
total deaths **7 487 → 2 204**. The tuned row lands on the design note's own stated calibration
target for it (design.md:242-246, "timed suppression … ≈ +11 400"), which the guessed numbers
missed by 20 %.

**Deliberate divergence, recorded.** The sentinel's numeric thresholds no longer match
design.md:371-386. That is the point of the change: the checklist requires the baseline's
parameters to be *tuned*, the note's numbers were not, and this is the one place where satisfying
the checklist and reproducing the note's literal numbers are mutually exclusive. Nothing else moves
— no rules constant, no manifest, no docs page, no README paragraph names these numbers (grepped),
and the sentinel's *shape* (de-bias your own reported cases, step lockdown and testing at fixed
prevalence thresholds, gate each road against its neighbour's estimate, ×0.8 on the variant) is
exactly what the note, the README and the policy description describe.

**Not swept: the laggard.** It is the designed foil — blind, wide open, three weeks late — and
tuning it for score would delete the thing it exists to be. Its contract stays asserted at
`test_bot.nim:75-88` (`locked == 3`).

---

## CND-2 — can `makeRequests` raise, and is `timeout` seconds?

**Settled from the pinned dependency; no code change.**

- *Raise:* no — `{.raises: [], gcsafe.}` at `~/.nimby/pkgs/curly/src/curly.nim:711-715`. See N12.
- *Seconds:* yes — every path funnels into `easy_setopt(OPT_TIMEOUT, request.timeout)`
  (`curly.nim:290`, and `:1029` for the single-request path). libcurl's `CURLOPT_TIMEOUT` is
  whole seconds. The `llmTimeoutSeconds` / `turnBudgetSeconds` arithmetic in the note and in
  `server.nim` is therefore in the same unit the transport uses.

---

## CND-3 — do `readCogameUri` / `writeCogameUri` carry their own timeouts?

**Settled from the pinned dependency; no code change.** Checklist item 5.

`bitworld` is pinned at `9af28b41` in `nimby.lock`. Both procs have exactly two branches
(`~/.nimby/pkgs/bitworld/src/bitworld/runtime.nim:97-123` and `:193-226`):

- **file URI** → `readFile(path)` / `createDir` + `writeFile(path, data)` — local, no wait.
- **http(s) URI** → `newCurlPool(1).get(value)` / `.put(value, headers, data)`. Those pool
  overloads are `curly.nim:1184-1211`, `timeout: float32 = 60`, and they delegate to
  `makeRequest` → `easy_setopt(OPT_TIMEOUT, timeout.int)`.

So both carry a **60 s** bound per call, matching the explicit 60 s the game passes on its own POST
branch (`server.nim:123`). Every wait in item 5 is now accounted for with a number.

---

## CND-4 — the per-week ceiling under non-default config

**Fixed — `9454773`.** Checklist item 5.

`config_schema` permits `llmTimeoutSeconds` up to 300 while `turnBudgetSeconds` maxes at 120, and
only the *retry* was bounded by the remaining week budget (`llm.nim:630-632`). Under an override
the first batch could run 300 s inside a 35 s week, leaving the between-weeks deadline check as the
only backstop. The first attempt is now `max(5, min(llmTimeoutSeconds, budgetSeconds))`. Under the
manifest's own defaults (25 / 35) that is 25 — unchanged, so the note's per-week arithmetic still
holds exactly.

*Evidence.* `tests/test_bot.nim` — "the week's batch is bounded by the week budget, not by
llmTimeoutSeconds". It binds a local socket that **accepts and never answers** (the case a
connection-refused endpoint cannot exercise: only the timeout can end it), sets
`llmTimeoutSeconds = 60` against a 5 s week budget, and asserts the whole batch returns under 30 s.
Measured: `silent-endpoint batch: 10004 ms` — 5 s first batch + 5 s bounded retry, where the
unclamped code would have taken 65 s.

---

## NOTED (not fixed)

Seen while working, outside this round's findings, left alone:

1. `test_bot.nim:75-88` (the laggard contract test) generates its decisions from the mutating sim
   in ascending seat order, the same pattern `08ba0f8` fixed in `playScripted`. It is harmless
   there — the laggard reads only its **own** history (`llm.nim:187-191`), never a neighbour — so
   there is nothing to leak, and the test asserts a single-seat schedule.
2. `initSim`'s `weeks < MinWeeks` guard (`sim.nim:234`) is unreachable after `sampleEpisode` and is
   now the only such check; it is cheap and it documents the invariant, so I left it.
3. `extractJsonObject`'s error head (`llm.nim:417-421`) does its own rune trim with a `"..."`
   marker while `cleanText` uses `"…"`. Both are rune-safe; unifying them would have widened
   `b2387da` for cosmetics.
