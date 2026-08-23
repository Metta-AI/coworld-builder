# r1 fixes — escrow

Repo: `Metta-AI/cogame-escrow` (main). Base sha: `d68c5ec`.
Head: **`dac4fc4c6c58a6465bae07f0c1cbc308b5cbf0e6`**
CI: https://github.com/Metta-AI/cogame-escrow/actions/runs/32646647329 — **success**
(jobs `test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓, at that sha).

Every commit was pushed on its own; one remote commit per finding.

| finding | disposition | commit | files | checklist item |
|---|---|---|---|---|
| F1 (blocking) | fixed | `3b6c3eb` | `src/escrow/llm.nim:49-58,645-711`, `src/escrow/server.nim:318-322`, `tests/test_bot.nim:137-144,273-310` | **8** — LLM reply handling: the fallback is recorded |
| F2 | fixed | `122cf57` | `src/escrow/sim.nim:485-494,509-516`, `tests/test_sim.nim:359-391` | none (advisory) |
| F3 | no change | — | — | — |
| F4 | fixed | `1ecfa58` | `src/escrow/sim.nim:79-89,521-522`, `tests/test_sim.nim:718-725` | 9 (held before and after) |
| F5 | no change | — | — | — |
| F6 | no change | — | — | — |
| F7 | no change | — | — | — |
| F8 | no change | — | — | — |
| F9 | no change | — | — | — |
| F10 | fixed | `dac4fc4` | `coworld_manifest_template.json:231-235` | 10 (held before and after) |

---

## F1 — a seat that exhausts its LLM retry was recorded with `scripted: false`

**Commit `3b6c3eb`** — "F1: record the per-seat LLM fallback in the move event's scripted flag".

*What the code did.* `decideAll` returned a bare `seq[Decision]`; its terminal fallback
(`llm.nim:691-694` at the reviewed sha) wrote `scriptedAction(sim, seat, skTrader)` into the result
with nothing to distinguish it from a decision a model produced. `server.nim:319` computed the flag
from the registration state alone — `scripted[seat] != skNone or client.disabled` — so on a
credentialed episode a seat whose two attempts both failed was written into the replay as
`scripted: false` (`sim.nim:511` → `sim.nim:658`) and phase 60, which counts fallbacks off
`move.scripted`, would report zero of them.

*What it does now.* `decideAll` returns `seq[SeatDecision]`, a new two-field object
`{move: Decision, scripted: bool}` (`llm.nim:49-58`). The flag is set `true` on all three baseline
paths — a seat registered `PLAYER_SCRIPTED` , the no-credentials `client.disabled` path, and the
terminal fallback after attempt 1 — and `false` only where a model reply parsed *and* passed
`validateMove`. The server writes that flag straight through: `let wasScripted =
decisions[index].scripted` (`server.nim:322`). The flag now travels *with* the decision, so it
cannot be re-derived from stale state at the call site.

*Why that resolves the finding.* The fallback reaches `applyMove`'s `scripted` argument, which is
stored verbatim on the `move` event and serialized by `eventToJson`, which is what phase 60 reads.

*Evidence.* New `tests/test_bot.nim` test 17 drives `decideAll` through a forced double failure with
credentials present (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME=http://127.0.0.1:1` — a refused loopback
connection, no traffic leaves the box), asserts `not client.disabled` (so this is *not* the path
test 15 covers), asserts every returned decision is the trader baseline and carries
`scripted == true`, applies them and asserts every recorded `move` event carries `scripted: true`.
CI run 32646647329, job `test` (97211471451 for the same test at `3b6c3eb`; re-run green at head):

```
escrow llm: bedrock transport, url http://127.0.0.1:1/model/us.anthropic.claude-haiku-4-5…/invoke
escrow llm: seat 0 attempt 0 failed: llm transport: Couldn't connect to server POST http://127.0.0.1:1/…
escrow llm: seat 0 attempt 1 failed: llm transport: Couldn't connect to server POST http://127.0.0.1:1/…
escrow llm: seat 0 falling back to the trader baseline
  [OK] 17. an exhausted LLM retry is recorded as scripted on the move        (debug and -d:release)
```

The whole test runs in milliseconds, so the offline-CI "no network waits" property is untouched.
Test 15 was also tightened, not loosened: it now asserts `decisions[index].scripted` and applies the
move with the returned flag instead of a hard-coded `true`.

## F2 — over-cap `gives`/`signs` were dropped silently

**Commit `122cf57`.** `applyMove` truncated with `setLen` and appended no event, so the dropped
entries left no trace; design.md:432 lists "an over-cap action" as one of the two things a `reject`
event carries. `applyMove` now calls a new `rejectOverCap` before truncating, emitting
`reject` with `over_cap: <n> gives|signings past the cap of <c> dropped`. No live path changes —
`parseDecision` truncates at the cap first, so only a hand-built `Move` reaches this.
*Evidence:* new `tests/test_sim.nim` test 5d submits three gives and three signs from one seat and
asserts two `reject` events (both attributed to that seat, both `over_cap:`), exactly `MaxGives`
`give` events, `MaxSigns` `sign` events, and the truncated decision on the recorded `move` event —
`[OK] 5d. over-cap gives and signings are dropped with a reject event` in both modes, run
32646647329.

## F4 — `clip` truncated without the `…` marker

**Commit `1ecfa58`.** `clip` gained a defaulted `marker = false` parameter; `applyMove` passes
`marker = true` for `say` and `notes` (the two fields design.md:227-228 says are marked) and leaves
the offer DSL cut bare, since `…` is not contract syntax. The marker replaces the last rune
(`runeSubStr(0, limit - 1) & "…"`, the same shape `cleanText` already used), so the caps still hold
exactly and the LLM path — where `cleanText` marks the cut first — is unchanged.
*Evidence:* test 12, the strict-UTF-8 test, now asserts `endsWith("…")` alongside its existing
`runeLen == cap` and `validateUtf8() == -1` assertions, with the emoji still sitting on the cut —
`[OK] 12. replay bytes are strict UTF-8 even at a truncation boundary` in both modes.

## F10 — `results_schema.reason` carried no enum

**Commit `dac4fc4`.** Added `"enum": ["complete", "deadline"]` next to the existing description.
The sim can emit exactly those two values, so this is the schema catching up with the code, not a
new constraint. *Evidence:* the manifest still parses (`python3 -c json.load`), and
`docker-smoke` — which builds the manifest and runs the seat-count gate over it — is green with
`smoke OK: seats=4 results=267B replay=9310B reason=complete` and no `SEAT-COUNT FAIL`.

---

## No change, and why

**F3 — `tableStateJson.heard` is `[{seat, say}]`, not `[string]`.** No code change. The reviewer's
own trace settles it: `coworld_manifest_template.json:244` documents `heard[{seat,say}]`, i.e. the
shipped protocol contract matches the code, and `client/renderer.js` never reads `heard` at all
(only the doc comment at `renderer.js:19`). The object form also carries strictly more information
(which seat said what) than the note's example array, which is what a spectator frame wants.
Changing the code would put the shipped protocol text out of step with the game; the stale artefact
is the note's example frame, which I am not permitted to edit. Left for the judge.

**F5 — four byte-index slices in the LLM transport error paths.** No code change. Checklist item 9
is about strings that *reach the replay*. These four (`llm.nim:530,539,544,553`) build `EscrowError`
messages that go to stdout and into the retry hint via `cleanText(error.msg, 300)`, which is
rune-safe; the reviewer traced every string that reaches an event (`move.say/offer/text` via `clip`,
`reject.text` from `parseContract`'s reason codes, `sign/give.text` from ASCII literals, `end.text`
from the reason enum) and found none of them byte-sliced. Rewriting them would mean moving
`cleanText` above `textOf` in the module — a bigger edit than the defect, for no observable change.

**F6 — the `turn`-event check compares seats, not `board`.** No code change. Checklist item 2 asks
that replay re-derive frame by frame and that a test assert it; `replayMatch` re-derives everything
except `move` events and `test_sim.nim:572-598` asserts it, including a tamper test. The note's
claim is that the `turn` event is checked "exactly as bullwhip checks its `week` event", and it is —
`sameSeats` is the same shape of check as the starter's. Adding a board comparison means a new
structural comparator over `Contract` (11 fields, including the normalized DSL text) plus its own
test; that is a design-level strengthening, not a defect fix, and out of scope for this round.

**F7 — the `trader` baseline gates offers on "zero live contracts".** No code change, and I read
the finding as already answered in the tree: `llm.nim:167-170` states the rule is deliberate,
because zero-live "bounds the live count below `MaxLive` no matter what the other three seats do in
the same turn" — that is what makes the baseline legal *by construction*, which is checklist item
7's actual requirement and what `test_bot.nim:66-96` asserts. A cap-based gate would make the
baseline only usually legal, since three other seats can post against the same addressee in the
same turn. The `HEARTS`-never-surplus rule is likewise commented at `llm.nim:205-207`. Both were
declared as known deviations by the builder.

**F8 — the server's `except EscrowError` around `applyMove` is unreachable.** No code change.
Removing a defensive `except` is a cleanup, not a fix, and this one is verbatim starter shape
(`cogame-bullwhip/src/bullwhip/server.nim:303-309`). Its cited consequence — "the only place the
code ever passes `scripted = true` for an LLM seat" — is exactly what F1's fix removes the
dependence on: the flag now comes from `decideAll` for every seat on every path.

**F9 — `gameStart` is stamped before the player-connect wait.** No code change. The reviewer's own
arithmetic shows the property checklist item 5 asks for still holds: worst case the connect wait
costs 180 s of the 720 s play budget, leaving 540 s against the note's ~330 s of play, and the wait
is itself explicitly bounded, so nothing is unbounded. Moving the stamp changes the meaning of
`playDeadline` relative to the platform's own episode clock (which starts at container start, not
after connects) — i.e. it would buy play time by moving the budget *past* the platform's deadline,
which is the failure mode the 0.6 fraction exists to avoid. Deliberately left as starter behaviour.

## NOTED (not fixed)

- `decideAll` calls `client.curl.makeRequests(...)` outside the per-seat `try`. `makeRequests` is
  declared `{.raises: [].}` in curly 1.1.1 and reports transport failures per request in
  `responses[i].error`, so the "never raises" contract holds today; it holds *because* of a
  dependency's annotation rather than because of anything in this repo. Not a finding this round.
- `sim.history` (the `TurnRecord.moves` history) still has no reader, as the review noted under
  "Could not determine". It is inherited starter state; I did not touch it.
</content>
</invoke>
