# r1 fixes — hanabi

Repo: `Metta-AI/cogame-hanabi`, branch `main`.
Base: `b06d9feeee38ffef3788f26b804995e47cf7ae4c` → **Head: `724826f53754849d1a22fff31cf971027c555f9a`**
CI: run **32793042266** — <https://github.com/Metta-AI/cogame-hanabi/actions/runs/32793042266> —
conclusion **`success`** (`headSha 724826f5…`, jobs `test` / `docker-smoke` / `wasm-viewer` all
`success`).

| finding | disposition | commit | files |
|---|---|---|---|
| F1 (blocking) | fixed | `f17e3a36dbe6eb234a94e2a418e01ff3d453a860` | `client/renderer.js` |
| F2 (blocking) | fixed | `70fc1d5c7c86f8cfe318c6010f3d71acd6ad02fe` | `tools/ci/renderer_fixture.html` |
| F3 (blocking) | fixed | `78e25f3d06663165b9f7df2eaa73b147d4cb3edf` | `src/hanabi/server.nim`, `src/hanabi.nim`, `client/replay.html` (deleted), `tests/test_viewer.nim`, `README.md` |
| F4 | not fixed (needs a design decision) | — | `src/hanabi/server.nim:262-282` |
| F5 | not fixed (replay-schema change) | — | `src/hanabi/llm.nim`, `src/hanabi/types.nim` |
| F6 | not fixed (scope) | — | `tests/test_replay.nim` |
| F7 | not fixed (design note governs) | — | `client/renderer.js` |
| F8 | fixed (advisory, small) | `724826f53754849d1a22fff31cf971027c555f9a` | `src/hanabi/llm.nim` |
| F9 | refuted | — | `client/chrome.css:374-383` |
| F10 | not fixed (guard for an unreachable path) | — | `src/hanabi/server.nim:303-312` |

> **How these commits were pushed.** git-over-https to `github.com` is not authenticated in this
> sandbox (only `api.github.com` is: `curl -u x-access-token:$GH_TOKEN
> https://github.com/Metta-AI/cogame-hanabi.git/info/refs?service=git-receive-pack` → 401, the same
> credentials → 200 on `api.github.com`). The four commits were therefore replayed onto `main`
> through the GitHub Data API, fast-forward, never forced, one commit per finding, in order. The
> resulting tree is bit-identical to the local one: local `HEAD^{tree}` and the remote head commit's
> tree are both `1a1f07b571109ac14c6c43331c9e6ae810a65159`. The shas above are the remote ones.

---

## F1 — a full-cap banner was drawn ellipsized to about a third of its length

**Commit `f17e3a3` — "F1: size the banner band from MaxBannerLen, never ellipsize a banner".**

*What the code did.* `computeLayout` sized the reserved band as
`max(96, min(width * 0.22, 210))` — a fraction of the canvas, with `MaxBannerLen` appearing nowhere
in `renderer.js`. `drawBanner` then called `wrapLines(ctx, text, w - pad*2, 2)`, and `wrapLines`
ellipsized the last line on overflow. At the fixture's widest size the band was 156 px against a
banner needing ≈440 px, so 27 of 81 runes were drawn.

*What it does now.* `computeLayout` takes the drawing context and measures: `bannerBandWidth(ctx,
size)` sets the banner font (the same `-apple-system…` stack and the same `max(8, min(rowH*0.17,
13))` size the tag is drawn in), measures `BANNER_SAMPLE`'s mean glyph advance in it, and returns
`perRune * (MAX_BANNER_RUNES / BANNER_LINES + 1) + pad*2` — i.e. the width a string at the server's
cap (`MAX_BANNER_RUNES = 80`, mirroring `MaxBannerLen`, `src/hanabi/sim.nim:32`) needs over two
lines, plus a glyph of ragged-edge slack. The band is clamped only so that four cards keep their
minimum width; it is never derived from a viewport fraction. `wrapLines` lost its line cap and its
ellipsis entirely: a word wider than the band is broken on a **rune** boundary (`runesOf`), never
cut. `drawBanner` steps the type down one pixel at a time (floor 7 px) if the wrap still overflows
the seat's row — it shrinks the *type*, never the *text*.

*Evidence.* CI run 32793042266, `wasm-viewer` → *Load the worst-case renderer fixture*:
`canvas text: 31988 drawn, 0 never inside the canvas (24 draws crossed an edge), 1096 ellipsized`,
down from `31602 drawn … 1668 ellipsized` on `b06d9fe` — the drop is the four banner draws per
frame. In the `renderer-fixture` artifact's `viewer-smoke.png` the seat-row tags now read the whole
sentence, `holding Widget-of-the-Long-Name's chop while the green four comes back round now`, over
three lines with no ellipsis, inside the band and inside the canvas. The 1096 that remain are the
alias plate and the `N banked · M burnt` line — labels in a fixed plate, which item 15 names as the
legitimate use of ellipsis. `never_inside` stays 0 under `--strict-text-bounds`, and the real-replay
smoke reports `52735 drawn, 0 never inside …, 0 ellipsized`.

Local check before pushing (`node`, the layout/wrap functions driven with a glyph-advance model):
across widths 560/600/710/720/960/1280 the band comes out 162–263 px, the full-cap banner keeps
every rune, no line exceeds the band's usable width, and the tag's height stays inside `rowH` — for
a normal sentence, an 80-rune unbroken word, a wide-glyph string and 40 astral-plane runes alike.

**Checklist item 15**, third bullet ("widen the band, do not shorten the text") — and it keeps item
15's gated number, `never_inside`, at 0.

## F2 — the fixture did not assert its own strings were full-length, and one was 13 runes short

**Commit `70fc1d5` — "F2: make the worst-case fixture assert its own strings are at the cap".**

*What the code did.* `BANNER` was 81 runes (`MaxBannerLen` is 80) and `NOTE_LINE` was 77 where its
comment claimed 90 (`MaxLearnedLen` is 90) — the six-line learned block was exercised at 77/90 of
the cap the server enforces. No assertion tied either literal to anything.

*What it does now.* `BANNER` is exactly 80 runes and `NOTE_LINE` exactly 90 (verified rune-wise, not
byte-wise: `NOTE_LINE` contains an em dash). The caps are named in the file next to the `sim.nim`
lines they mirror, and the fixture checks itself before it hands the payload to the renderer:
`assertFullLength` on `BANNER` and `NOTE_LINE`; on every seat's `banner` in every one of the 42
frames; on every line of every `MaxLearnedLines`-long learned block; and a check that at least one
such six-line block exists at all. A failure sets `data-replay-error` on `<html>` and throws —
`data-replay-error` is exactly what `viewer_smoke.mjs` fails the job on
(`tools/ci/viewer_smoke.mjs:503`), so a shortened remark turns `wasm-viewer` red instead of leaving
a fixture that draws comfortable little strings.

*Evidence.* Locally, the fixture's script was evaluated in `node` against stubs: it reaches
`attachReplay` with `frames 42 events 42 banner runes 80`, and a negative control (four runes cut
from `BANNER`) sets `data-replay-error: renderer fixture: BANNER is 76 runes, but the server caps it
at 80 …` and throws. In CI, the fixture's `viewer-smoke.json` reports
`{"loaded": true, "signals": {"data_replay_loaded": "true", "data_replay_error": null}}` — the
assertions ran and passed on the way to the first frame.

**Checklist item 15**, last bullet ("the fixture asserts its own strings are still full-length").

## F3 — a `/client/replay` pod route and a replay-server mode

**Commit `78e25f3` — "F3: remove the pod replay path — the static bundle is the only viewer".**

*What the code did.* `buildRouter` unconditionally registered `GET /client/replay` (serving
`client/replay.html`) and `GET /replay` (upgrading to a websocket that shipped
`replayPayloadGlobal`), and `src/hanabi.nim` ran `runReplayServer` whenever the runtime asked for
replay mode. Inherited verbatim from the bullwhip starter.

*What it does now.* Removed: both routes, `replayUpgradeHandler`, `replayPayloadGlobal`,
`framesFromEvents`, `configFromReplay`, `runReplayServer`, `buildRouter`'s `replayMode` parameter
(`/player` is now registered unconditionally) and the entrypoint branch. `client/replay.html` is
deleted with them — it existed only to be served by that route and its script opened the `/replay`
socket that no longer exists; keeping a page nothing can reach, whose name is the very path the
checklist forbids, would have left the finding half-fixed. The module header now states the rule
positively. `grep -rn "client/replay"` over the tree returns only the new regression test and
`coworld-release.yml`'s certification-gate message.

*On the tests.* Deleting the page forced two edits in `tests/test_viewer.nim`: `client/replay.html`
is dropped from the two page lists it appeared in. No assertion was weakened — every check those
lists make (all 20 starter ids, `tokenbar`/`hintpane`, no `viewpanel`, `relayout` +
`document.documentElement` + `--band` + `--hudscale`, the wordmark, `HanabiRenderer`, no `BULLWHIP`)
still runs against `replay-viewer/index.html`, the page that is actually shipped, and the id checks
also still run against the renderer fixture. The same commit **adds** a test, `the pod serves no
replay path at all`, asserting `client/replay.html` does not exist and that `server.nim` contains no
`/client/replay`, no `"/replay"`, no `runReplayServer`, and `hanabi.nim` no `replayMode` — so the
route cannot come back unnoticed. Net: one file's worth of coverage moved onto the surviving pages,
one new invariant pinned.

*Evidence.* CI run 32793042266: `test` job green (the new test runs there), `docker-smoke` green —
`game=hanabi seats=4 …`, `smoke OK: seats=4 results=311B replay=8867B reason=complete` — so the pod
still serves `/healthz`, `/client/global`, `/client/player`, `/global` and `/player` through the
rebuilt router, and `wasm-viewer` green with `loaded: true`, so the static bundle (the only
remaining viewer path) still executes.

**Checklist item 3** ("No `/client/replay` pod path anywhere"); the other three clauses of item 3
were already satisfied and are untouched.

## F8 — HTTP error bodies and reply heads sliced by byte

**Commit `724826f` — "F8: cut HTTP error bodies and reply heads on rune boundaries".** (Advisory;
fixed because the change is five call sites and one four-line helper.)

`llm.nim` took `response.body[0 .. min(response.body.high, 400)]` and three siblings — byte slices
that can cut a multi-byte character in half. That text becomes the rejection reason appended to the
retry prompt and printed to stdout, and `cleanText` only re-cuts strings *longer* than its cap, so a
short-but-invalid head passed through untouched. All five sites now go through `headRunes`, which is
`runeLen`/`runeSubStr`-based like `cleanText` (`llm.nim:380`) and `capLine` (`sim.nim:117`).
Behaviour change beyond that: the `no JSON object in response` message no longer appends a literal
`...` marker to a truncated head.

**Checklist item 9** (rune-safe truncation) — which the reviewer correctly noted was not falsified,
since this text never reaches the replay; the fix closes the stdout/retry-prompt half.

---

## Not fixed, with reasons

**F4 — the "deadline before any turn" path settles as `complete`, not `deadline`.** Real, and the
design note (`design.md:217-219`) does say `reason = "deadline"`. But the note also says the server
plays the whole episode out first, and an episode played to a terminal condition *has* completed:
`applyMove` settles it (`sim.nim:809-816`) before `endEarly()` is reached. Making the reason
`"deadline"` means either stopping the catch-up short of the end (an empty-ish replay, which the
note explicitly wants to avoid) or overwriting a settled `reason`, which would put `reason` and
`endReason` in contradiction and cut across `sim.settle`'s single-writer invariant and the enums
`tests/test_replay.nim:199-221` polices. That is a design decision, not a fix, and the reviewer
records it as no checklist violation (item 5 is satisfied: the episode settles and scores inside the
budget). Left for the design note to resolve.

**F5 — the fallback's rejection text is logged but not recorded on the `move` event.** Real. The fix
is a new field on `GameEvent`, in `eventToJson`/`eventFromJson`, in the replay protocol and in
`replayMatch`'s comparison — a replay-schema change, well past "smallest change", and the reviewer
states item 8 is satisfied as it stands (`origin = "fallback"` is recorded, `scripted` is set and
`results.fallbacks` counts it). Not attempted.

**F6 — the re-derivation does not compare the per-move recorded scalars.** Real as a scope
statement; the reviewer explicitly does not claim it falsifies item 2, and the fix is a new test
(walking every frame, or comparing `hintTokens`/`fuses`/`deck`/`countdown`/`score` inside
`replayMatch`) rather than a code defect. Out of this round's blocking scope; worth adding, and it
would also close the matching "could not determine" entry.

**F7 — the canvas banner is not passed through the name map.** The design note's list of name-mapped
render sites (`design.md:49-51`) does not include the canvas banner, and the reviewer states
checklist 4 is satisfied. Substituting policy names there would also change the string length the
band is now sized for. Where the note is the requirement, the note does not require this. Left
alone.

**F9 — `#endscreen` stops at the band structurally rather than via `bottom: var(--band)`.**
**Refuted as a change to make.** `#endscreen` is `position: absolute; inset: 0` inside `#board-wrap`
(`chrome.css:374-383`, `:95`), and `#board-wrap` is the `flex: 1` sibling that ends exactly where
`#transport` begins (`replay-viewer/index.html`). Its bottom edge is already the top of the band.
Adding `bottom: var(--band)` inside that containing block would subtract the band height a **second**
time and float the endcard above the transport — a regression, not a fix. `design.md:836-840` states
this substitution explicitly, and checklist 14(c)'s other two clauses (the class the CSS rule uses is
the class `updateEndscreen` toggles; every seek re-evaluates it) hold.

**F10 — the fallback `applyMove` is not itself guarded.** The reviewer marks it "inferred,
untested — unreachable in practice": `conventionsMove` returns a member of `legalMoves()`, which
`tests/test_sim.nim:321-357` proves non-empty at every state of 200 seeded episodes, and the loop
reaches that line only under the lock with a single writer. Wrapping it would add a handler for a
state that cannot occur and would swallow a genuine invariant break if it ever did. Not changed.

## NOTED (not fixed)

- The `renderer-fixture` artifact still carries no `ellipsized` sample: `viewer_smoke.mjs`'s
  `SAMPLE_CAP` of 12 is exhausted by `outside` entries, so the remaining 1096 are identified from
  the screenshot (alias plate, `N banked · M burnt`) rather than from the JSON. Raising the cap or
  bucketing samples per kind would settle it in the artifact; `viewer_smoke.mjs` is verbatim from
  `templates/`, so I did not touch it.
- `client/global.html` and `client/player.html` keep their own copies of `relayout()`/`fit()`; only
  the deleted `client/replay.html` was removed from that family. No change made.

---

**Final head sha:** `724826f53754849d1a22fff31cf971027c555f9a`
**Final green CI run:** **32793042266** — conclusion `success` —
<https://github.com/Metta-AI/cogame-hanabi/actions/runs/32793042266>
