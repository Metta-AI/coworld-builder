# r1 fixes — 2026-08-23-eleusis

Head: `244401dcbba70a7bb73a519a59e2b7c7267878e9` (main)
CI: https://github.com/Metta-AI/cogame-eleusis/actions/runs/32661283184 (run id **32661283184**)
— conclusion **`success`**, all three jobs (`test`, `docker-smoke`, `wasm-viewer`) `success`, on
`headSha 244401dcbba70a7bb73a519a59e2b7c7267878e9`.

The review had **zero blocking findings** and twelve non-blocking observations. All twelve are
addressed: nine by a code fix, three (N3, N11, N12) by correcting the design note's prose in the
repo's own copy (`docs/plans/2026-08-23-eleusis-design.md`) where the note, not the code, was the
inaccuracy. None is disputed and none needs a design change. One commit per finding, in finding
order, replayed onto `main` through the Git Data API as a single ref update.

| finding | disposition | commit | files |
|---|---|---|---|
| N1 | fixed | `f783ba3d` | `src/eleusis/{types,sim,llm,server}.nim`, `tests/test_sim.nim`, `docs/plans/…-design.md` |
| N2 | fixed | `b5e9f8cc` | `src/eleusis/llm.nim:523`, `src/eleusis/server.nim:341`, `tests/test_bot.nim` |
| N3 | fixed (note corrected; code is right) | `69c6066a` | `docs/plans/2026-08-23-eleusis-design.md:585` |
| N4 | fixed | `1bcd192c` | `coworld_manifest_template.json:36`, `tools/ci/docker_smoke.sh:153` |
| N5 | fixed | `7ee8ac05` | `tools/ci/docker_smoke.sh:340` |
| N6 | fixed | `22718fee` | `src/eleusis/sim.nim:647`, `tests/test_sim.nim:520` |
| N7 | fixed | `dff82335` | `src/eleusis/sim.nim:829`, `tests/test_sim.nim:388` |
| N8 | fixed | `1193f9b7` | `src/eleusis/sim.nim:110,845,995`, `client/renderer.js:859`, `coworld_manifest_template.json`, `tests/test_sim.nim` |
| N9 | fixed | `bc1a7a9c` | `src/eleusis/sim.nim:505-531`, `tests/test_sim.nim:213` |
| N10 | fixed | `af22e08f` | `src/eleusis/server.nim:246,289,308`, `tests/test_bot.nim:49` |
| N11 | fixed (note corrected; code is right) | `0987302f` | `docs/plans/2026-08-23-eleusis-design.md:242` |
| N12 | fixed (note corrected; code is right) | `244401dc` | `docs/plans/2026-08-23-eleusis-design.md:437` |

Checklist references are to `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST.

---

## N1 — the LLM fallback was recorded only on stdout

**Was:** `decideAll` ended with `result[index] = scriptedAction(sim, seat, skOpenbook)` and a
`falling back to scripted decision` line on stdout (`llm.nim:580-583`). The `Decision` carried no
mark, so the server's `wasScripted = scripted[seat] != skNone or client.disabled`
(`server.nim:326`) computed `false` for it and the `experiment`/`skip`/`answer` event — and the
replay — recorded `"scripted": false` on what was in fact an openbook move. Phase 60 check 4's
`jq '[.events[]|select(.fallback==true)]|length'` read a field this game never emitted.

**Is:** `Decision.fallback` is set where `decideAll` gives up on a seat. The server passes it into
`applyResearch`/`applyAnswers` as a new trailing parameter, and ORs it into `wasScripted`, so the
event says `"scripted": true, "fallback": true`. The server's own second-belt fallback
(`server.nim:352-366`, the sim refusing a decision) passes `true, true` too. `eventToJson` emits
`fallback` beside `scripted` for all three kinds, `eventFromJson` reads it, and `replayMatch`
carries it into the re-derived events, so a viewer frame and a phase-60 `jq` see the same thing.

**Evidence:** `tests/test_sim.nim` "a scripted fallback is recorded on the event and in the
replay" — two fallback decisions and one live one; asserts `fallback` on the event, `fallback` in
`eventToJson`, `scripted` true for the fallbacks and false for the live decision, and that
`replayMatch` re-derives exactly two fallback events. Round-trip test extended with
`check back.fallback == event.fallback`.

**Checklist:** item 8 — "…then falls back to the scripted move — and the fallback is recorded so
phase 60 can count it." The stdout line is kept (phase 60 check 5 greps it); the replay now
carries it as well.

## N2 — a slot that never delivered a prompt played LLM-with-empty-prompt

**Was:** `state.prompts` starts `""` for every slot and only a `{"type":"prompt"}` frame changes
it. `decideAll`'s short-circuit was `if kind != skNone or client.disabled`, so a seat whose player
pod never connected inside `playerConnectTimeoutSeconds` went to Claude with
`operatorBlock("") == ""` — an LLM decision with no operator guidance, where the note says such a
slot "plays `openbook` for the whole episode" (design.md:255-257).

**Is:** `playsScripted(client, prompt, kind)` names the three ways a seat plays a baseline —
registered scripted, no credentials, or no prompt ever delivered — and is the single definition
both `decideAll` and the server's `wasScripted` read, so such a seat is also *recorded* as
scripted. The reference player always delivers a prompt (`eleusis_player.nim:38-40` substitutes
its built-in strategy when `PLAYER_PROMPT` is empty), so an empty prompt means an absent pod, not
a silent operator. A prompt that arrives late still takes effect from the next turn: the server
re-reads `state.prompts` under the lock before every batch.

**Evidence:** `tests/test_bot.nim` "a slot that never delivered a prompt plays openbook, not an
LLM call" — with `ANTHROPIC_API_KEY` set (so `client.disabled` is false) and every prompt empty,
every decision equals `scriptedAction(…, skOpenbook)` and no seat is marked `fallback`, which is
only true if no request was ever issued. Against the old condition the test fails (checked by
reverting the predicate locally: `[FAILED] a slot that never delivered a prompt plays openbook`).

**Checklist:** item 5 (the wait is bounded and the episode advances) still holds; this brings the
behaviour back to what the design note declares.

## N3 — "kept verbatim" was not true of most of the chrome helpers

**Disposition: the code is right; the note's claim was the inaccuracy.** Checklist item 14's
provenance tests are on `chrome.css` byte-identity and on the page being the starter's page plus
an appended block — both hold, and neither requires function-level byte-identity of
`renderer.js`. I re-ran the comparison mechanically (function-body extraction from both files):
byte-identical are `isBaselineFiller`, `makeNameMap`, `applyNames`, `clampName`,
`bindFeedToggle`, `ellipsize`, `roundRect`; modified are `renderFeed`, `blockHead`, `escapeHtml`,
`updateScorebug`, `updateEndscreen`, `reasonLine`, `buildScrub`, `attachLive`, `attachReplay`,
`makeEffects`, `matchHeader`, `stateToView`, `playerFrameToState`, `describeEvent`; absent are
`wrapLines`, `drawBubble`, `peakOrders`. The note now says exactly that, names why the three are
gone (they served the conveyor scene and its endcard column), and records `relayout` /
`bindRelayout` as additions. No code was changed.

## N4 — no variant and no cert fixture validated against `game.config_schema`

**Was:** `required: ["tokens","players"]` while `tokens` is injected by the commissioner at
dispatch, so all four shipped `game_config` objects failed with `'tokens' is a required property`
(confirmed with a Draft 2020-12 validator).

**Is:** `tokens` stays a defined property — a dispatched config carries it and still validates —
but is no longer required, and its description says why. Verified with `jsonschema` 4.26
(Draft202012Validator): `standard`, `open-science`, `closed-shop`, `certification` and
`certification + injected tokens` all validate with zero errors.

The missing check is now in CI: `docker_smoke.sh`'s manifest preflight walks every variant and the
cert fixture against `game.config_schema` — every `required` key present, and, since
`additionalProperties` is false, no key the schema does not define — and exits
`CONFIG-SCHEMA FAIL: …` before any container starts. It is a structural check, not a validator, so
it adds no dependency. Run against the old schema it reports all four failures; against the new
one it prints `config_schema OK: 4 game_config fixtures validate`.

**Checklist:** item 10 was already satisfied (`game.docs`, `game.protocols`); this closes the
note's own requirement that every variant + the cert fixture validate.

## N5 — `docker_smoke.sh` printed `results.reason` without asserting it

**Was:** `if reason is not None: print(...)`. **Is:** anything outside `{complete, deadline}` —
including a missing reason — exits non-zero. That is the note's test item 18 and
`game.results_schema`'s own enum for the field.

**Evidence:** the real assertion block run against four synthetic `results.json` files:
`complete` → 0, `deadline` → 0, `crashed` → 1, no reason → 1. CI's own episode prints
`episode end reason: complete`, so the assertion holds where the print used to be.

## N6 — `sim.capText` truncated without the `…` marker

**Was:** `runeSubStr(0, limit)`, versus `llm.cleanText`'s `runeSubStr(0, limit - 1) & "…"` and the
note's field table ("≤ 120 runes … truncated with `…` on a rune boundary"). **Is:** identical to
`cleanText` — same boundary, same marker, same resulting rune count (119 + marker = 120).

**Evidence:** `tests/test_sim.nim` "hypothesis and notes are cut on rune boundaries" keeps its
120/600-rune and `validateUtf8() == -1` assertions (checklist item 9) and adds that both fields
end with `…` and that text inside the cap is passed through untouched.

## N7 — `endEarly` left an undisclosed pending result pending

**Was:** `endEarly` discarded the open test and settled `deadline` without touching
`sim.seats[].pending`: the result never reached `secrets`, `hoarded` was not incremented, and the
drawer and `results.hoarded` disagreed with the note ("pending undisclosed results stay hoarded",
design.md:211-212).

**Is:** `endEarly` discloses every held result as a `hoard` — the same `discloseNow` path a
`publish: false` decision takes — before it rolls back the open test and settles. Nothing reaches
the corkboard; the drawer, the counter, the seat's log mode and the transcript agree. Because the
disclosure is recorded as an event, a replay re-derives the same drawers.

**Evidence:** `tests/test_sim.nim` "complete after the final test; deadline discards an open test"
now pins that the three seats still holding a result end with `pending` none, `hoarded + 1`, that
strip in `secrets`, and nothing of theirs on the board; "a recorded episode re-derives frame by
frame" asserts the deadline replay's final `benchStateJson` **string-equals** the live one
(checklist item 2).

## N8 — a deadline-discarded test was displayed as settled

**Was:** `endEarly` set `test.open = false`, and `updateTestPanel` reads `settled = !test.open`,
so the panel revealed the truth stamps and per-seat correctness pips of a test that scored nobody.

**Is:** `TestState.discarded` records why the test closed; `benchStateJson` emits it (and the
manifest's `global` protocol text documents it); the panel keys its reveal on
`!open && !discarded` and captions the test `DISCARDED`. The answers themselves stay in the frame
— they happened — but nothing is presented as marked.

**Evidence:** `tests/test_sim.nim` asserts a settled test has `discarded` false, and that the test
the deadline closed has `open` false and `discarded` true.

## N9 — the degenerate top-up did not exclude `used` and could repeat a strip

**Was:** the top-up pool was `strip notin chosen and strip notin sim.usedTest` — `sim.used` was
not excluded — and the final never-leave-it-short loop
(`chosen.add(stripOfIndex(index mod StripUniverse))`) filtered nothing and could add a strip
already in `chosen`. A repeat would pay one author twice for the same `(strip, confirmer)` pair,
because the citation loop is keyed on the index into `test.strips`.

**Is:** the spare pool also excludes `sim.used`, and the last resort walks the universe skipping
strips already chosen (it would only repeat after all 256 have been offered, which needs
`testStrips > 256`; the schema caps it at 12). Both loops are still bounded, and a test is still
never left short.

**Evidence:** `tests/test_sim.nim` "the degenerate top-up prefers held-out strips and never
repeats one" crafts both branches — (a) every PASS strip plus all but eight FAIL strips used, so
the balanced draw comes up short and every drawn strip must still be held out; (b) every strip but
one already used by an earlier test, so the spare pool is empty and the last resort must fill six
distinct entries. Against the old code (a) draws three `used` strips and (b) yields only five
distinct strips — both reproduced locally before the fix.

## N10 — the play deadline was disabled entirely if the timeout was non-positive

**Was:** with `COWORLD_TIMEOUT_SECONDS` absent or unparseable and `episodeTimeoutSeconds <= 0`,
`playDeadline` was `0.0` and the `playDeadline > 0.0 and …` check before every batch never fired.
`types.update` validates `rounds`/`testEvery`/`testStrips` but not the timeout; only the
manifest's `minimum: 60` stood between the game and an unbounded episode.

**Is:** `playTimeoutSeconds(config, hostedTimeout)` resolves the clock in one place — platform
value, else the configured assumption, else the built-in default — and can never return zero, so
the deadline always exists and the guard on it is gone.

**Evidence:** `tests/test_bot.nim` "the play deadline is never switched off" pins every step of
the chain, including `episodeTimeoutSeconds` of 0 and -5 falling through to the default and the
result always being positive.

**Checklist:** item 5 (degrade-never-hang) — the 60 % bound is now unconditional.

## N11 — the note's worst-case batch arithmetic omitted the retry batch

**Disposition: the code is right; the note's arithmetic was the inaccuracy.** `decideAll` runs
`for attempt in 0 .. 1` and each attempt is one `makeRequests` batch bounded at
`llmTimeoutSeconds = 40`, so a pathological turn costs ≤ ~80 s and the 720 s deadline arrives
after ~9 turns, not the ~18 batches the note stated. The retry is a second *parallel* batch (the
one-parallel-batch-per-turn rule is intact), the deadline is checked before every batch, and
`deadline` is a declared acceptable ending. The note now states both bounds. No code was changed.

## N12 — the note's example frame omitted five keys and showed no nulls

**Disposition: the code is right; the note's example was stale.** `benchStateJson` emits
`decided`, `experimentCost`, `knowledgePool`, `citePot` and `closest` in addition to the note's
list, and `null` in `test.answers`/`test.correct` for a seat that has not answered — the frame
says "no answer" rather than a zero that would read as five wrong guesses, and the viewer already
guards the nulls (`renderer.js:872-878`). The manifest's `global` protocol text documents the real
shape. The note's example is now the frame the code emits, including `test.discarded` from N8, with
a paragraph explaining the nulls and the extra keys. No code was changed.

---

## NOTED (not fixed)

- `results.json` has no fallback counter. The `fallback` flag from N1 is on the events, so phase
  60 can count it from the replay, but `resultsJson` still carries no per-seat total. Adding one
  would change `game.results_schema`, which no finding asked for.
- `tools/ci/docker_smoke.sh`'s new schema preflight is structural (required keys, undefined keys).
  It would not catch a type or range violation in a variant; a real Draft 2020-12 validation would
  need a `jsonschema` install in the job.
- The review's "Could not determine" section is unchanged by these fixes: the live LLM path, the
  12 s spacing against the hosted 30 req/min cap when a retry fires, `writeCogameUri`'s PUT
  timeout, and whether `#endscreen`'s `--band` inset is load-bearing all still need a hosted
  episode or a screenshot to settle. Nothing in this round's diff touches them.

## CI evidence on the pushed head (run 32661283184)

- `test`: both test files in **debug and `-d:release`**, every case `[OK]`. The four new cases run
  in both modes: `the play deadline is never switched off`, `a slot that never delivered a prompt
  plays openbook, not an LLM call`, `the degenerate top-up prefers held-out strips and never
  repeats one`, `a scripted fallback is recorded on the event and in the replay`.
- `docker-smoke`: `config_schema OK: 4 game_config fixtures validate` (N4's new preflight),
  `episode end reason: complete` now asserted (N5), `smoke OK: seats=5 results=646B
  replay=13324B reason=complete`, `player 0..4 exited 0`. Zero occurrences of `SEAT-COUNT FAIL`
  or `CONFIG-SCHEMA FAIL` in the whole log (checklist item 6).
- `wasm-viewer` (`needs: docker-smoke`), step `Load the bundle in a real browser`:
  `{"loaded":true,"ms":291,"clock":"ROUND 2 / 6 · 3 OF 5 IN", …,"feed_lines":121}` and
  `scrub readouts: 0%="ROUND 2 / 6 · 3 OF 5 IN"  50%="ROUND 4 / 6 · 0 OF 5 IN"
  100%="ROUND 6 / 6 · FINAL"` — three differing readouts, soak passed (checklist item 13).

## Verification run locally before pushing

- `nim r --path:src tests/test_sim.nim` and `tests/test_bot.nim`, each in **debug and
  `-d:release`**: 18 and 8 cases, all `[OK]`, no failures. No test was weakened, skipped or
  deleted — every change to `tests/` in this round adds assertions or adds a case.
- `nim c --path:src src/eleusis.nim` builds; `nim check replay-viewer/eleusis_replay.nim` passes
  (the wasm module compiles against the same `sim` API).
- `client/renderer.js` parses; `coworld_manifest_template.json` parses; `bash -n
  tools/ci/docker_smoke.sh`.
