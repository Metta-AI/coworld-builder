# r1 fixes — cogolf

Head: `529c0f8b0e9b7942a543401aca02ee872a8da0aa` (`main`)
CI: https://github.com/Metta-AI/cogame-cogolf/actions/runs/32683809005 — **success**
(all three jobs green: `test`, `docker-smoke`, `wasm-viewer`, including
`wasm-viewer` → `Load the bundle in a real browser`, which printed
`{"loaded":true,"ms":303,…}` and `soak: 12s of playback kept advancing
("beat 1 / 49" -> "beat 14 / 49" -> "beat 17 / 49")`).

Repo: `Metta-AI/cogame-cogolf`. Base for this round: `a60233b`.
Commits were pushed one per finding through the GitHub Git Data API
(blobs → tree → commit → `PATCH refs/heads/main`, never forced); the sandbox git
credential has no write access to this repo.

| finding | disposition | commit | files |
|---|---|---|---|
| B1 | fixed | `9a63d64` | `client/replay_broadcast.html:556-590,643-651`, `tests/test_viewer.py:66-79,167-190` |
| B2 | fixed | `46eecce` | `tests/test_replay.py:196-337` |
| N7 | fixed | `529c0f8` | `server/cogame_cogolf/engine.py:645-648`, `tests/test_replay.py:83-112` |
| N1 | not fixed (deferred, reviewer's own reading: satisfied) | — | `players/client.py:272-280` |
| N2 | not fixed (NEEDS-DESIGN) | — | `players/llm_player.py:189-213` |
| N3 | not fixed (refuted as blocking; operational reading holds) | — | `server/cogame_cogolf/server.py:780-783` |
| N4 | not fixed (refuted: the platform validator accepts `uri`) | — | `coworld_manifest_template.json:393-417` |
| N5 | not fixed (NEEDS-DESIGN; note is self-contradictory) | — | `server/cogame_cogolf/server.py:394` |
| N6 | not fixed (no code defect; the note's arithmetic, not the code) | — | `server/cogame_cogolf/server.py:581-588` |
| N8 | not fixed (deliberate; changing it would loosen rule 6) | — | `server/cogame_cogolf/engine.py:62-64` |
| N9 | not fixed (refuted: `markBeat` does not exist in this lineage) | — | `client/replay_broadcast.html:765-798` |
| N10 | not fixed (deferred; reproducibility already holds) | — | `server/cogame_cogolf/config.py:225` |

Per-commit CI: `9a63d64` → run 32683517120 **success**; `46eecce` → run 32683696535
was **cancelled** by the immediately following push (GitHub's `ci-refs/heads/main`
concurrency group), and both of its commits are contained in the green head run
32683809005 above. No test was disabled, skipped, weakened or deleted in this
round; every change to `tests/` in these three commits is an added test or an
added helper (`git log -p a60233b..529c0f8 -- tests/`).

---

## B1 — the page's own failure paths never set `data-replay-error`

**Commit `9a63d64`** — `fix(viewer): B1 — every page failure path sets data-replay-error`.
**Checklist item satisfied: 13, second bullet** — “`index.html` / `static_replay*.js` set
`data-replay-loaded="true"` … and `data-replay-error="<message>"` on failure. **Both
markers, both set from the shell's own code paths**.” *(category: static-viewer)*

**What the code did.** `client/static_replay.js:33` was the only writer in the bundle,
and it only covers Worker/wasm failures. The page's terminal failures — the boot catch
(`replay_broadcast.html:1399-1406`: a bad `?replay=` URL, a 404 on the replay, a
schema-invalid replay, `"replay has no beats"`), the 12 s no-data card
(`:600-609`), the 45 s stuck card (`:625-640`) and the mirrored board-renderer failure
(`:1360-1367`) — wrote `#banner`, `#status`, `document.body.dataset.state` and
`#failcard` only. `tools/ci/viewer_smoke.mjs:364`'s fast-fail probe never fired for that
whole class, so the smoke reported a generic 90 s
`timeout: no data-replay-loaded="true" …` instead of the actual message.

**What it does now.** One writer, `setReplayError(message)`
(`replay_broadcast.html:556-559`), sets
`document.documentElement.setAttribute("data-replay-error", …)`. It is called from the
two funnels every page-side failure already routes through:

- `showError(prefix, e)` (`:560-570`) — used by the boot catch and by the `window`
  `error` / `unhandledrejection` listeners (`:589-590`), so a top-level throw such as
  `chrome_common.js did not load` (`:676`) is reported too. Message:
  `` `${prefix}: ${e.message}` ``.
- `showFailCard(title, lines, withLink)` (`:571-587`) — used by the boot catch, the
  12 s no-data card, the 45 s stuck card and the `#status` MutationObserver mirror.
  Message: `[title, ...lines].join(" — ")`, so the attribute carries what the card shows
  (`Replay didn’t load — fetch /replay-data: HTTP 404 — replay: /replay-data — stage: …`).

`clearFailCard()` (`:643-651`) now also `removeAttribute("data-replay-error")`. That path
is the deliberate recovery case the page already documents — “a late frame fully recovers
the UI” — and it is what keeps the machine-readable marker from contradicting a board that
is drawing. It cannot mask a real failure: `static_replay.js:29-30` latches `failed` on
the first Worker failure and drops every later Worker message, so no frame arrives after
one.

This is exactly the pair design.md:590-592 specifies (`showFailure()` **and** the page's
`showFailCard()`).

**Evidence.**
- New test `tests/test_viewer.py::test_the_pages_own_failure_paths_set_data_replay_error`
  (`tests/test_viewer.py:167-190`, with the `_fn_body()` brace-matching helper at `:66-79`) asserts, per function body:
  `setReplayError` writes the attribute on `document.documentElement`; `showError` and
  `showFailCard` both call it; the boot catch, `noDataCard`, `armStuckTimer`, `startCore`'s
  status mirror and both `window` listeners route through those two; and `clearFailCard`
  removes it. It fails on the pre-fix page (the `setReplayError` lookup raises before any
  assertion).
- CI run 32683809005, job `test`:
  `tests/test_viewer.py::test_the_pages_own_failure_paths_set_data_replay_error PASSED`,
  and again in `wasm-viewer` → `Viewer tests against the built bundle` (which runs
  `test_viewer.py` against the freshly built `viewer/dist`, whose `index.html` must be
  byte-identical to `client/replay_broadcast.html`).
- The positive path is unaffected: same run,
  `Load the bundle in a real browser` → `{"loaded":true,"ms":303,…}`.

## B2 — no test asserts the event-fold reproduces the recorded per-hole state

**Commit `46eecce`** — `test(replay): B2 — assert the event fold reproduces the recorded hole state`.
**Checklist item satisfied: 2** — “Replaying the recorded events through the sim reproduces
the recorded per-tick state **frame by frame**, and the viewer derives its display from that
same re-derivation — not from a parallel recording. **A test asserts it.**”
*(category: correctness)*

**What the code did.** The first two clauses held by construction (the reviewer traced
them: `replay_broadcast.html:712` `state()` → `RD.stateAt`, and every readout goes through
it). The third did not: nothing in `tests/` compared the fold of `events[]` with `holes[]`,
although the engine builds the two in separate places (`engine.py:326-342` the beats,
`engine.py:636-666` the hole record).

**What it does now.** `tests/test_replay.py` grows two tests over a **real episode** —
`build_replay()` runs the engine with the real sandbox and returns the finalized bytes:

1. `test_folding_the_events_reproduces_the_recorded_per_hole_state` — `fold(doc)`
   (`tests/test_replay.py:215-246`) is a transcription of `client/replay_doc.js:132-177`
   `stateAt()` and yields the state after **every** beat. At each beat the test asserts:
   each seat's accumulated shots are a prefix of that hole's recorded `tests`, field for
   field (`idx, name, args, expect, why, legal, legal_reason, outcome, observed`); `par`
   and `fallback` are either unseen (`None`) or already equal to the record; and the running
   `cumulative` is still the *previous* hole's until this hole's `hole_score` beat. At each
   `hole_score` beat the hole is re-derived exactly (`tests`, `par_fails`, `fallback`,
   `hole_score`, `cumulative`), and after the last beat the state is `done` with
   `cumulative == result.scores == holes[-1].cumulative`. The number of `hole_score` beats
   must equal `len(holes)`.
2. `test_the_viewers_own_fold_agrees_with_the_recorded_holes` — the same episode through
   **the code the page actually runs**: it shells out to node, `require`s
   `client/replay_doc.js`, calls `RD.stateAt(doc, i)` at every `hole_score` beat and at the
   final beat, and the Python side compares `hole`, `holeIndex`, `cumulative`, `par`,
   `fallback` and the projected `shots` against `doc.holes[k]`. `ci.yml`'s `test` job sets up
   node 22, so this runs in CI; it skips where node is absent (same guard the existing
   `replay_doc.js` tests use).

**Evidence that they bite** (drift injected locally, reverted, never committed):
- `_hole_record` recording `cumulative` as `[c + 1 for c in cumulative]` → both tests FAIL.
- `_hole_record` truncating a shot's `observed` to `s["observed"][:1]` → both tests FAIL.
- CI run 32683809005, job `test`:
  `test_folding_the_events_reproduces_the_recorded_per_hole_state PASSED`,
  `test_the_viewers_own_fold_agrees_with_the_recorded_holes PASSED`.

**What this still does not cover** (recorded, not fixed): the Nim fold
(`replay-viewer/cogolf_replay.nim:304-337 sceneAt`) is a third independent implementation
of the same reduction and is compared to nothing. Settling it needs the wasm module's scene
state to be readable from `tools/wasm_replay_smoke.cjs` — an export the renderer does not
have today. That is a design change, so it is out of scope for this round; the JS fold that
drives every chrome readout is now pinned.

## N7 — `broken_reason` is the one replay string that does not pass through `clean_text`

**Commit `529c0f8`** — `fix(replay): N7 — broken_reason goes through clean_text like every other string`.
**Checklist item touched: 9** (rune-safe truncation) — already satisfied before this
commit (`_clip` is `str` slicing); this closes the *other* half of the repo's own rule.

Fixed because it is one line and unambiguously what AGENTS.md rule 6 and design.md:544-547
say (“every string that lands in the replay is decoded once, stripped of control characters
and lone surrogates, and only then re-encoded”). `engine.py:645-648` now records
`clean_text(broken[slot], contract.MAX_BROKEN_REASON_CHARS)`, with `None` left as `None`.
New test `test_the_broken_reason_is_sanitised_like_every_other_replay_string` drives a hole
whose impls are broken with a reason carrying a BEL, a lone surrogate and 400 `z`s, and
asserts the recorded reason keeps `boom`, drops the control characters, shows `U+FFFD` for
the surrogate and fits the cap. Verified it fails without the engine change
(`git stash push server/cogame_cogolf/engine.py` → FAILED). CI: `test` job,
`test_the_broken_reason_is_sanitised_like_every_other_replay_string PASSED`.
This is replay-only text — no policy observes it and no seat is scored by it — so
`GAME_VERSION` is unchanged (AGENTS.md rule 8).

---

## Non-blocking findings not fixed, with reasoning

- **N1 — LLM fallback counted only on stderr.** The reviewer's own conclusion is that
  checklist 8's “recorded so phase 60 can count it” is satisfied literally by
  `llm_player.py:362-379`'s log lines. Making it countable from `results.json` means a new
  wire field from the policy to the engine (the server sees a well-formed `submission` and
  cannot distinguish it): a protocol change touching `contract.py`, the manifest's
  `results_schema`, `docs/PROTOCOL.md` and `players/` — a four-surface change (AGENTS.md
  rule 9) for a non-blocking finding. **NEEDS-DESIGN**, not taken this round.
- **N2 — no policy-level retry on the hosted sidecar transport.** Real and precisely
  traced, but the code matches the design note (design.md:253 and :281-282), the
  engine-level retry-once exists and is tested (`engine.py:367-376`,
  `tests/test_engine.py:60-73`), and adding a retry inside `_BedrockHttpClient.create`
  changes the policy's worst-case latency against the 37 s policy deadline and the 40 s
  hole deadline. That is a deadline-budget decision, not a defect fix. **NEEDS-DESIGN.**
- **N3 — `/client/replay` routes in `server.py`.** Refuted as blocking. All four
  registrations live in `make_replay_app` (`server.py:732-784`), which is constructed only
  when `COGAME_LOAD_REPLAY_URI` is set (`:793-808`) — never in an episode pod, where
  `GameServer.make_app` (`:337-344`) registers `/healthz`, `/player`, `/global`,
  `/client/global`, `/client/player` and nothing else. The manifest declares only
  `"replay_viewer": {"bundle": "static-replay-viewer"}`. design.md:345 keeps replay-serving
  mode deliberately. Deleting it would remove the container's `/replay-data` debug mode
  without changing what any episode or the platform can reach.
- **N4 — `game.docs` uses `"type": "uri"`.** Refuted. The shape checklist 10 names is
  present exactly, `game.protocols` carries both `player` and `global`, design.md:705-707
  specifies `uri` deliberately, and `coworld.manifest.validate_upload_manifest` (coworld
  0.1.42) accepts the substituted manifest — asserted by
  `tests/test_manifest.py:158-166`. Changing `uri` → `text` would inline two GitHub blob
  URLs' worth of text and lose the canonical link.
- **N5 — `welcome.episode.seed` lets a seat pre-compute later specs.** The note contradicts
  itself (design.md:513 vs :464-478) and the code implements the “state every episode
  parameter at t=0” half. It is symmetric (both seats get the same seed) and no seat gets the
  reference, the par tests or the ambiguity note. Removing the seed would break the note's
  t=0 disclosure rule and the replay's reproducibility story. No checklist item is touched.
  **NEEDS-DESIGN.**
- **N6 — the 20 s shutdown grace is outside the note's 680 s arithmetic.** No code defect:
  the reviewer's own trace puts settle-and-score at ≤ ~691 s < 720 s (60 % of 1200 s), every
  wait is bounded, and the engine is *faster* than the note assumed (two impl batches run
  concurrently). The discrepancy is in the design note's arithmetic, and I may not edit the
  design note. Recorded for the judge.
- **N8 — `clean_text` strips category `Cf`, splitting ZWJ sequences.** Deliberate and load
  bearing: `category(ch)[0] != "C"` is what removes lone surrogates (`Cs`) and format
  characters from every recorded string. Narrowing it to `Cc` would weaken AGENTS.md rule 6
  for a cosmetic gain (an emoji rendering as its components in the plaque). No checklist item
  is touched.
- **N9 — the page owns the beat-marker layer.** Refuted as a defect: `chrome_common.markBeat`
  does not exist in this starter lineage (`grep -n markBeat` over
  `/workspace/starters/cogame-factorio/client/` returns nothing); factorio's
  `chrome_common.js:180-200` exposes `setMarkers`, which builds non-interactive `<div>`s. The
  substance of 14(d) — labelled `<button>`s with `aria-label`/`title` that seek to their beat,
  CSS for every emitted kind, no dead rules — is implemented in the page under the required
  banner comment and asserted by `tests/test_viewer.py`. Calling `setMarkers` as well would
  double-render the layer.
- **N10 — `replay.config.seed` is the unresolved config value.** Deferred. The resolved seed
  is recorded twice (`doc.seed`, `doc.result.seed`), `replay_doc.js:41` validates and the page
  reads `doc.seed`, so reproducibility from the bytes holds. Changing `config.to_dict()` to
  emit the resolved seed would make `config` no longer a faithful echo of the config the
  platform passed, which is what `tests/test_replay.py:124-125` and the manifest's
  `config_schema` pin. No checklist item is touched.

## NOTED (not fixed)

- `client/broadcast_core.js:196` still lists `['/client/replay', '/replay']` in its live
  websocket URL list. The file is byte-identical to the starter's (checklist 14 requires
  exactly that), and the static bundle never reaches that code path. Leaving it alone is the
  checklist-compliant choice.
- The Nim fold (`cogolf_replay.nim sceneAt`) remains unpinned against `holes[]` (see B2
  above).
