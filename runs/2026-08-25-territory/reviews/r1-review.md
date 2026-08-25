# r1 review — cogame-territory

Range: `07f0ebcaa24d4336b045a742f38098e0e530956c` (branch `main`, single-fork history: `ae0ecfc` + `07f0ebc`)
Repo read at: `/tmp/cogame-territory`
Base compared against: `Metta-AI/coworld-cogherence` @ `b116135` (`--depth 1` clone at `/tmp/coworld-cogherence`)
Design note: `/tmp/cogame-territory/docs/plans/2026-08-25-territory-design.md`
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Files read: 78 source/config files + 3 CI job logs + 3 downloaded CI artifacts (`smoke-replay`, `viewer-smoke`, `static-replay-viewer`)
CI evidence: run **32838206882** on `main` — `test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓ (conclusion `success`)

I am a tracer. Everything below is labelled **observed** (I read it / ran it), **inferred** (I reasoned
about it), or **untested** (a run would be needed). Nothing here is a fix proposal and nothing is a
severity ranking.

---

## A. Observations I believe falsify a named checklist item

### O1 — The static replay viewer renders recorded snapshots; the sim's rule modules are not in the replay bundle, and no test asserts re-derivation
**Checklist item touched:** 2 (Replay re-derivation)

- Where:
  - `src/client/App.tsx:127-147` (replay load path), `src/client/App.tsx:162-203` (render path)
  - `src/client/net/cogweb-feed.ts:56-63` and `src/client/net/feed.ts:46-58` (frames → store)
  - `vite.config.ts:12-16` and `tools/build_replay_viewer.sh:8-11` (the "same TypeScript sim compiles into the viewer bundle … satisfies the 're-derives every frame' pin" claim)
  - built bundle from CI artifact `static-replay-viewer`: `assets/main-BzhJMYYs.js`, `assets/App-BybxZBik.js`, `assets/WarLedger-2CNqe2Iy.js`
- Observed:
  1. `App.tsx:132-137` decodes the replay's frames and calls `applyFrame` for each; `feed.ts:47-58`
     pushes each `snapshot` frame's `state` into `store.snapshots`. `App.tsx:185` picks
     `snaps[index]` and hands that recorded object straight to the panels. There is no call to
     `stepTurn`, `resolve`, `upkeep`, `applyLife` or `generateBoard` anywhere in `src/client/**`
     (non-test, non-fixture). A grep of the client for engine imports returns only
     `App.tsx:49` (`MAX_TURNS`), `cg/panels.tsx:17` (constants), `cg/atoms.tsx:6` (a *type*), and
     `colors.ts:12` (`ALIASES`, `SEAT_COLORS`).
  2. Confirmed against the shipped bundle, not just the source. `index.html` loads exactly
     `main-BzhJMYYs.js`, `App-BybxZBik.js`, `WarLedger-2CNqe2Iy.js`. Grepping those three chunks for
     string literals that exist only inside `src/shared/engine/resolve.ts` returns **0** hits:
     `"rubble is never claimable again"` (resolve.ts:69), `"razing opens on turn"` (resolve.ts:74),
     `"eliminated seats do not act"` (resolve.ts:59), `"affordability invariant violated"`
     (resolve.ts:269). All four appear **once** in `assets/fixture-tCiOADaa.js` — the renderer-fixture
     entry, which pulls the engine in via `src/client/fixture/scenario.ts:9`. So the engine's rule
     modules are in the *fixture* chunk and absent from the *replay page* chunks.
  3. No test replays recorded events through the sim and compares to the recorded per-turn state.
     `src/shared/engine/game.test.ts:37-52` asserts `(seed, submissions)` determinism (same inputs →
     same state), which is a different property. `src/game/replay.test.ts:147-179` asserts *one
     snapshot per turn* and *169 tiles per snapshot* — i.e. that the recording is complete, not that
     it is reproducible from the events.
- What the note says: §Sim module — "`(seed, variant, ordersByTurn)` reproduces a game byte for byte,
  which is what lets the **same** module be compiled into the viewer bundle by vite and re-derive
  every frame in the browser"; §Viewer — "cogherence's static bundle is a **vite build of the same
  TypeScript sim**, which satisfies the same pin". §Replay bytes — "Every turn contributes at least
  one full `snapshot` … so the viewer re-derives each frame with no server and no interpolation."
- Why this touches item 2: item 2 requires that "Replaying the recorded **events** through the sim
  reproduces the recorded per-tick state **frame by frame**, and the viewer derives its display from
  that same re-derivation — **not from a parallel recording**. A test asserts it." What is shipped is
  the parallel-recording form (19 full snapshots read directly), with no re-derivation and no test.
  The design note's substitution ("self-sufficient snapshots") is *stated*, but it is a substitution,
  and the note's own justification for it (the sim compiles into the bundle) is contradicted by the
  built artifact.
- Confidence: **observed** for (1) and (2) (bundle greps reproduced above); **observed** for (3) by
  exhaustive grep of all 28 test files for `stepTurn`/`toSnapshot`.

### O2 — A Bedrock transport failure neither retries nor falls back to the scripted move: it is rethrown
**Checklist item touched:** 8 (LLM reply handling)

- Where: `packages/llm/src/robust-decide.ts:70-78`, in particular **line 75**:
  `if (!isCredentialsUnavailable(err)) throw err; // throttle/timeout etc. still surface`
- Observed: `robustDecide`'s attempt loop wraps `client.converse` in a try/catch. Only
  `isCredentialsUnavailable(err)` is handled (record the attempt, `return opts.baseline()` —
  `src/game/player.ts:74` supplies the scripted move there). Every other transport error — throttle,
  socket reset, 5xx, request timeout — is rethrown out of the loop, so:
  - it is **not** re-prompted (the loop is exited, not continued), and
  - it does **not** reach `opts.baseline()` at line 94.
  Traced downstream: the throw propagates out of `makeLlmDecide`'s returned function
  (`src/game/player.ts:57-85`) → out of `opts.decide(ctx)` in
  `packages/coworld/src/player-runtime.ts:107-113`, whose `Promise.all(...).then(ok, reject)` rejects
  the outer promise → `run()` rejects → the top-level `await run()` at `src/game/player.ts:117`
  terminates the player process non-zero. That seat then sends no reply; the host's per-seat
  20 s guard (`packages/core/src/runner.ts:519-529`) holds for it, and
  `RemotePlayerPilot`'s breaker (`packages/coworld/src/remote-pilot.ts:27,155`) benches the slot after
  3 consecutive timeouts.
- What the note says: §Degrade, never hang — the table's rows cover "Reply doesn't parse / fails the
  schema" (retry once, then scripted) and "Bedrock unavailable / no credentials" (scripted
  immediately). A **transport** failure that is not a credentials failure has no row.
- Why this touches item 8: item 8 requires "retries **once** on a parse **or transport** failure,
  then falls back to the scripted move". Parse/schema failures do exactly that; transport failures do
  neither. The consequence is bounded (holds + breaker, no hang), but the seat is lost for the rest of
  the episode rather than degrading to its baseline, and `results.fallbacks[seat]` counts the *host's*
  holds, not the player-side transport failure.
- Confidence: **observed** in the code path; **inferred** for the process-exit consequence (not
  exercised by CI, which runs keyless and therefore takes the credentials branch — see
  `tools/ci/docker_smoke.sh` and the CI log line `no ANTHROPIC_API_KEY: the game must complete on its
  scripted baselines`). **Untested.**

### O3 — The `actPrompt` transcript reaches the replay untruncated; the rune-capped `note` is never recorded
**Checklist item touched:** 9 (Rune-safe truncation)

- Where:
  - `src/game/game.ts:151` — `...(decision.note !== undefined ? { note: capNote(decision.note) } : {})`
  - `src/shared/engine/resolve.ts:286` — `capNote`
  - `src/shared/engine/resolve.ts:97-283` — `resolve()` reads `submissions[seat]?.orders` (line 115)
    and `submissions[seat]?.messages` (line 140) and **never** reads `.note`
  - `packages/coworld/src/remote-pilot.ts:162` and `:168` —
    `ctx.recordAttempt({ prompt: JSON.stringify(view), response, error })`, where
    `response = JSON.stringify(raw)` (line 159) is the player's whole raw reply
  - `packages/core/src/runner.ts:799-801` — `recordAttempt` pushes verbatim, no cap
  - `packages/core/src/runner.ts:472` — `this.#emit({ type: "actPrompt", actPrompt: outcome.wire })`
  - `packages/coworld/src/host.ts:409-415` — every emitted `ServerMessage` is pushed into
    `replayFrames` and written by `writeReplay`
- Observed, and confirmed against the real artifact: I downloaded the `smoke-replay` artifact from
  run 32838206882. `replay.json` (3,593,980 bytes) contains **162 `actPrompt` frames** (9 seats ×
  18 turns). Frame 0's single attempt has `prompt` length **14,947** characters (the full redacted
  observation JSON) and `response` length 87 (`{"orders":[…],"messages":[]}`). Nothing in that path
  goes through `capText`/`truncateRunes`. In an LLM episode that `response` is the model's raw reply,
  which carries the uncapped `note` and uncapped `messages[].text` (`SubmissionSchema` at
  `src/shared/engine/orders.ts:60-66` puts no `.max()` on either string; the 120/200 caps live only in
  the *advisory* tool schema at `src/game/prompt.ts:68,73`).
  Meanwhile the value `capNote` produces is stored on the seam submission at `src/game/game.ts:164`
  and read by nothing — I grepped `\bnote\b` across `src/shared`, `src/game`, `src/coworld`: no
  consumer.
- What the note says: §Server, player, protocol — "`note` | ≤ 120 characters; free text,
  spectator-side only (**rides the `actPrompt` transcript**, never another seat's observation) |
  **truncated** to 120 and `…` appended". §Reply schema table, `messages[].text`: "truncated to 200".
- Why this touches item 9: item 9 names exactly this set — "Every string that reaches the replay
  (`say`, `notes`, **prompts**, **captured errors**) is truncated on **rune** boundaries." `say`
  (the `talk` event) *is* capped, in `resolve.ts:142` via `capText`, and `text.test.ts:64-106` proves
  the round trip for it. `notes`, `prompts` and `captured errors`
  (`runner.ts:528,534` — `errorMessage(outcome.e)`) are not capped at all, and the recorded note is
  the *uncapped* one.
- Mitigating fact I verified: the specific *strict-parser* hazard item 9 is worried about is not
  reachable here, because `JSON.stringify` has been well-formed since ES2019 (lone surrogates are
  escaped as `\udXXX`), so `new TextDecoder("utf-8", {fatal:true})` will not throw on these frames.
  `src/game/replay.test.ts:95-99` demonstrates that for a scripted (ASCII) episode. The unmet part is
  the truncation itself, and the fact that the cap the design specifies is applied to a dead value.
- Confidence: **observed** end to end, including the real replay bytes.

### O4 — The static replay viewer issues a cross-origin request to `fonts.googleapis.com`
**Checklist item touched:** 3 (Static viewer — "the viewer contacts nothing but S3")

- Where: `src/client/styles.css:7`
  `@import url("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap");`
- Observed: `src/client/App.tsx:22` imports `./styles.css`, so the `@import` is emitted into the
  bundle's CSS. I confirmed it survives the build: the CI `static-replay-viewer` artifact's
  `assets/WarLedger-LavkVi1O.css` is 63,086 bytes and `index.html` links it. Vite leaves an absolute
  `@import url(https://…)` external, so the hosted page fetches it at runtime.
  Everything else in the page is local or inlined: art is data-URI'd
  (`vite.config.ts:56` `assetsInlineLimit: Number.MAX_SAFE_INTEGER`), the only `fetch` is
  `packages/ui/src/replay.ts:23` for the `?replay=` URL, and the live websocket effect is skipped in
  replay mode (`App.tsx:151`).
- What the note says: §Art — "**inlined as data URIs** … (path-served art 404s under the
  static-bundle prefix)". The note does not mention the font import.
- Why this touches item 3: item 3 says "the viewer contacts nothing but S3". This is a second origin.
- Provenance and degradation, both verified: the line is **inherited verbatim** from the live base —
  `coworld-cogherence/src/client/styles.css:6` is byte-identical. `--f-ui` /`--f-mono`
  (`src/client/styles.css`, cf. base lines 32-33) carry `system-ui, sans-serif` /
  `ui-monospace, Menlo, monospace` fallbacks, so a blocked request degrades to system fonts rather
  than breaking the page. Secondary consequence (**inferred**): the CI runner *can* reach Google
  Fonts, so `renderer_fixture.mjs`'s `scrollWidth <= clientWidth` measurements are taken in
  Space Grotesk / JetBrains Mono; in an egress-blocked environment the metrics differ.
- Confidence: **observed** (source + built CSS + base diff).

### O5 — There is no grid harness for the scripted baselines
**Checklist item touched:** 7 (Scripted baseline — second sentence)

- Where: `src/game/scripted.ts:55-108` (`claimPlan` max = 3, `raider`'s `yield >= 2` threshold,
  leader = highest `banked`), `src/game/scripted.test.ts` (the only harness in the tree)
- Observed: `homesteader` and `raider` are fixed algorithms with hard-coded constants (`max` 3 claims
  at `scripted.ts:78,105`; `c.tile.yield >= 2` at `scripted.ts:94`). Grepping the whole tree for
  `grid harness|grid-search|gridsearch|sweep|tuned|tuning` returns two hits, neither relevant:
  `packages/core/src/websocket.ts:39` (a doc comment about runner knobs) and the design note's
  §Out of scope line about *variant* tuning (`docs/plans/2026-08-25-territory-design.md:922`).
  `scripted.test.ts` asserts legality/boundedness/determinism, not that any parameter was searched.
- What the note says: §Scripted baselines gives the two algorithms "exact"; it does not claim a grid
  harness anywhere.
- Why this touches item 7: item 7's first half **is** met (see §C, T7 below — a full all-scripted
  episode reaches `reason: "complete"` and every order is asserted inside its legal bounds, both in
  vitest and in the real docker-smoke episode). Its second sentence — "The baseline's parameters were
  tuned with a grid harness, not guessed" — has no artifact in the tree.
- Confidence: **observed** (exhaustive grep; absence of an artifact).

### O6 — The renderer fixture does not assert its own strings are still full-length
**Checklist item touched:** 15 (Every drawn string fits its frame — final bullet)

- Where: `src/client/fixture/main.tsx:36-71` (`checkDom`), `tools/ci/renderer_fixture.mjs:126`
  (`window.__territoryFixtureCheck()`)
- Observed: `checkDom` performs exactly two checks — `el.scrollWidth > el.clientWidth + 1` over
  `ROW_SELECTORS` (`main.tsx:27,44`), and `getBoundingClientRect().height <= 0` on leaf text nodes
  (`main.tsx:59-69`). It never measures the *length* of the strings it rendered. If
  `fullCapLine()` (`src/client/fixture/scenario.ts:22-27`) were quietly shortened, or if
  `playScenario` stopped emitting messages, the fixture would report `ok: true` over an empty or
  trivial Channels panel and CI would stay green.
- What the note says: §Tests, test 14 — the fixture "mounts the **real** ScoreBug, WarLedger and
  Channels components with nine seats, **full-cap (200-rune, CJK + emoji) talk lines on every seat**
  … and self-checks DOM legibility: `scrollWidth <= clientWidth` on every row and no zero-height text
  node." The note's own description of the self-check matches the code; it does not include a
  length assertion.
- Why this touches item 15: item 15's last bullet says "The fixture **asserts its own strings are
  still full-length** — one quietly shortened remark leaves it passing while testing nothing."
- Mitigating fact I verified: the length assertion *does* exist, but in vitest rather than in the
  fixture page — `src/client/client.test.tsx:131-137` asserts
  `runeLength(m.text) === MAX_SAY_LEN` for every scenario message and
  `runeLength(fullCapLine(0)) === MAX_SAY_LEN`. Both run in the same `pnpm test` step. So the
  property is guarded; it is not guarded *inside the fixture*, which is what the item words.
- Confidence: **observed**.

---

## B. Literal mismatches with a checklist string that the design note pre-declares (judge to adjudicate)

I separate these because the brief instructs me to read the nim/paintbot-specific wording "through
this lineage's equivalents", and in each case the note names the equivalent in advance and the live
base repo uses the same form. I am recording the literal difference, not asserting a violation.

### O7 — `replay_viewer.bundle` is `"build/static-replay-viewer"`, not the literal `"static-replay-viewer"`
**Item touched:** 3 (static-viewer / manifest)

- Where: `coworld_manifest_template.json` → `game.replay_viewer` = `{"bundle": "build/static-replay-viewer"}`;
  generator at `src/game/coworld.ts:406`; asserted by `src/game/coworld.test.ts:53-55` and by
  `ci.yml:95`.
- Observed: the basename is exactly `static-replay-viewer`;
  `scripts/build-static-replay-viewer.sh:6-10` refuses any output path not ending in
  `/build/static-replay-viewer`. The live base declares the identical string:
  `coworld-cogherence/coworld/coworld_manifest_template.json:22` → `"bundle": "build/static-replay-viewer"`,
  generator at `coworld-cogherence/src/game/coworld.ts:151`.
- Note: §Viewer — "cogherence's proven package-relative path … (basename exactly
  `static-replay-viewer`, the form the checklist names)".
- Also verified for item 3: `tools/build_replay_viewer.sh` exists, is committed **mode 100755**
  (`git ls-files -s` → `100755 6f7026f…`), is asserted executable at `ci.yml:191-202`, and is the
  path `coworld build --project .` uses (`coworld-release.yml:157-165`). The manifest declares no
  `/client/replay` path. The **container** does serve `/client/replay`
  (`packages/coworld/src/host.ts:115`, `src/client/ui/nav.ts:34`) — that is the inherited
  platform replay-render probe surface described at `host.ts:469-475`, not a declared viewer.

### O8 — `game.docs.readme.type` is `"uri"`, not `"text"`
**Item touched:** 10 (Manifest validates)

- Where: `src/game/coworld.ts:445` — `readme: { type: "uri", value: \`${SOURCE_TREE}/README.md\` }`;
  committed manifest `game.docs.readme` = `{"type":"uri","value":"https://github.com/Metta-AI/cogame-territory/tree/main/README.md"}`;
  asserted `"uri"` by `src/game/coworld.test.ts:112`.
- Observed: the lineage's own manifest schema accepts both —
  `packages/coworld/src/manifest.ts:18-21` defines `ContentRef` as
  `text | uri`. The live base uses `"uri"` too
  (`coworld-cogherence/coworld/coworld_manifest_template.json` → `docs.readme.type: "uri"`).
- The rest of item 10 is met exactly: `game.docs.pages` is three entries, each
  `{id, title, content:{type:"text", value}}` (`rules.md`, `strategy.md`, `deadweight.md`), and
  `game.protocols` carries **both** `player` and `global`, both `{"type":"text",…}` and both
  > 200 characters (`coworld.test.ts:106-118`).
- Note: §Packaging — "`game.docs` — `readme` = `{"type":"uri","value":".../README.md"}`".

### O9 — Item 14's transport-rule mechanics (`--band`, `--hudscale`, `relayout()`, `#endcard.on`) have no counterpart; `index.html`'s `<base>`-recovery script is not byte-for-byte
**Item touched:** 14 (Chrome is the starter's, not a lookalike)

- Where: `src/client/styles.css` (no `--band`, no `--hudscale`, no `relayout()` — grep returns
  nothing); `src/client/styles.css:98-105` (`.app { position: fixed; inset: 0; display: flex;
  flex-direction: column }`); `src/client/styles.css:932-936` (`.cg-endcard { position: absolute;
  inset: 0; z-index: 6 }`); `src/client/App.tsx:272-305` (endcard mounted inside `.cg-stage`).
- Observed, and the substitutes verified:
  - `packages/ui/src/**` is **byte-identical** to the base. I ran
    `diff -rq /tmp/coworld-cogherence/packages/ui/src /tmp/cogame-territory/packages/ui/src` → no
    differences (exit 0), and the whole `packages/ui` tree matches. `src/client/chrome-manifest.test.ts:33-43`
    hashes every file under `packages/ui/src` against a checked-in SHA-256 manifest and pins
    `manifest.base === "Metta-AI/coworld-cogherence"`.
  - The transport band is a flex row that cannot be overlaid, so nothing needs `--band`: `.app` is
    `position: fixed; inset: 0; flex-column` with three children — `GameTopBar`,
    `.cg-stage { flex: 1; min-height: 0 }`, `#scrub`/`GameScrubberBar` (`App.tsx:234-337`).
    `.cg-endcard` is `position: absolute` inside `.cg-stage`, never fixed at the shell level.
  - The endcard renders only on the synthetic FINAL slot (`App.tsx:186,294`), so every seek dismisses
    it by construction; asserted at `src/client/client.test.tsx:170-192`.
  - Rail beats are real `<button>`s that seek to their index
    (`packages/ui/src/GameScrubberBar.tsx:287-311`, `onClick={() => onSeek(i)}`), plus the FINAL
    button at `:269-282`. Every emitted beat kind has a CSS rule: `beatKindAt`
    (`src/client/cg/derive.ts:131-137`) returns exactly `elim | raze | smear | quiet`, and
    `src/client/styles.css:914,917,920,923` define `.beat-quiet`, `.beat-smear`, `.beat-raze`,
    `.beat-elim`. Asserted at `client.test.tsx:143-168`.
  - Zoom kept, no minimap: the board is 169 hexes and pannable, so `HexBoard` keeps wheel-zoom
    (`src/client/HexBoard.tsx:119`), drag-pan (`:125`), double-click-to-fit (`:176`) over a viewBox
    (`:169`); `#viewpanel` / `attachMinimap` do not exist in this lineage.
- The one literal divergence I found in the inherited page: `index.html:21` changes the
  `<base>`-recovery regex from the base's
  `/(?:\/client\/(?:global|player|replay)|\/cog\/[^/]+|\/feed)$/` to
  `/(?:\/client\/(?:global|player|replay)|\/seat\/\d+|\/feed)$/`, plus the `<title>` and the leading
  comment. The note says "its `<base>`-recovery script byte-for-byte". The change tracks Territory's
  route rename (`/cog/<id>` → `/seat/<n>`, `src/client/ui/nav.ts`), so it is a functional necessity,
  but "byte-for-byte" is not literally true.
- Confidence: **observed** (diffs run).

---

## C. Advisory (no checklist item falsified)

- **A1 — `RemotePlayerPilot.MAX_ATTEMPTS = 3`, the note says 2.**
  `packages/coworld/src/remote-pilot.ts:26`. The note's §Degrade table and §budget arithmetic both say
  "`MAX_ATTEMPTS = 2` (one retry) → worst case **40 s** per batch". *Inferred:* the runner's own
  per-seat guard (`packages/core/src/runner.ts:519-529`, `maxTimeMs = ACT_TIMEOUT_MS = 20 000`)
  pre-empts the pilot at 20 s, so attempts 2 and 3 can only complete inside that window; the batch is
  bounded at ~20 s, not 40 s. The design's timing conclusion holds with more margin than it claims;
  the constant does not match the note.

- **A2 — the `endcard` event never reaches the replay on the `deadline` path.**
  `packages/core/src/runner.ts:487-495` calls `this.#game.settleEarly(...)` then only
  `#emitSnapshot()` + a `status` frame; it does not emit the `TurnRecord` that
  `src/shared/engine/game.ts:75-84` appended (which contains the `endcard`). On the natural end the
  endcard *does* ride out, via `stepTurn` → `applyDecision`'s `events: lowerRecord(...)`
  (`src/game/game.ts:169-174`) → `runner.ts:765-773`. Verified in the real artifact: the smoke replay
  (natural `complete`) has exactly one `endcard` event. *Inferred:* on a `deadline` settle the viewer
  degrades gracefully — `App.tsx:167` falls back to `store.status?.ended`, and
  `src/client/ui/FinalScores.tsx:36-42` falls back to the snapshot's `poolStart`/`poolEnd`/
  `destroyed`/`warsStarted`/`settled`. Nothing hangs; the note's "the final panel needs no
  derivation" is not true on that one path. **Untested** (no deadline episode exists in CI).

- **A3 — `voided { reason: "owned" }` is an unreachable branch.**
  `src/shared/engine/resolve.ts:233-236`. A claim only enters a `Plan` after
  `rejectionReason` → `isLegalClaim` (`src/shared/engine/orders.ts:101`) has confirmed
  `t.owner === null` on the pre-batch board, and step 4's razes only ever *clear* `owner`
  (`resolve.ts:172`). No path sets an owner before step 6. The kind is declared
  (`src/shared/engine/log.ts:58`) and handled in the viewer
  (`src/client/ui/WarLedger.tsx:51-56`), so the dead branch is harmless. The note lists the case
  ("target still owned … → void"), so the note has the same dead case.

- **A4 — the `MessageBus` / host-side `onTalk` path is wired but never exercised, and its emit is
  uncapped.** `packages/coworld/src/host.ts:245-262` posts wire-level `reply.messages` to the bus and
  emits a `talk` FeedEvent with `line.text.trim()` — no `capText`.
  `packages/coworld/src/player-runtime.ts:107-112` fills that field from `opts.talk`, and
  `src/game/player.ts:103-112` never passes `talk`, so it is always `[]`. Territory's talk instead
  rides `decision.messages` through the engine (`resolve.ts:137-149`), where it *is* capped, and the
  inbox rides the redacted view (`src/game/redact.ts:150-158`), not the bus. Verified in the real
  replay: `observation.messages` is unused and the `talk` events are engine-emitted. So the uncapped
  host emit is currently dead code; it becomes live the moment anything passes `talk`.

- **A5 — `replayMeta.players[].player` is hard-coded `null`.** `src/coworld/server.ts:94`. Asserted
  as `null` by `src/game/replay.test.ts:110`. Confirmed in the real replay artifact:
  `players[0] = {seat: 0, alias: "Sable", policy: "Cog A", player: null}`. The note's envelope example
  shows `"player":"daveey"`. `policy` carries the platform-injected `config.players[].name`, which is
  what the viewer maps aliases to, so item 4 is satisfied without it.

- **A6 — salvage is added to `banked` in Resolve, not in Upkeep 9c.**
  `src/shared/engine/resolve.ts:190-194` does `credit[seat] += paint` **and**
  `cogs[seat].banked += paint` inside step 4. The note puts the credit landing in step 9c. The
  spendable half is correct (the credit only becomes `paint` at `src/shared/engine/upkeep.ts:65-70`,
  i.e. next-turn money — asserted at `income.test.ts:87-102`); only the score bookkeeping is early.
  Observable difference: a seat eliminated in the same turn it salvaged keeps that salvage in its
  frozen score. Consistent with `score = Σ income + Σ salvage`.

- **A7 — `elimination` outranks `complete` on the final turn.**
  `src/shared/engine/game.ts:105-107` checks `living(next).length <= 1` before
  `next.turn > next.turns`. If both conditions fire on turn 18 the reason is `elimination`. The note's
  §End conditions table does not state a precedence. Both are "healthy".

- **A8 — artifact IO has no explicit request timeout.**
  `packages/coworld/src/artifacts.ts:28` (`fetch(uri, …)` for read) and `:43-48` (`fetch(uri, {method:"PUT"})`
  for write); also `packages/coworld/src/host.ts:483` (`fetch(uri)` in replay mode) and
  `packages/ui/src/replay.ts:23` (browser fetch; `App.tsx:132` passes only an `AbortController` for
  unmount, not a deadline). *Inferred:* Node/undici's default `headersTimeout`/`bodyTimeout` of
  ~300 s bounds the server-side ones, so this is not literally unbounded, but it is not an *explicit*
  bound in the sense item 5 uses. In practice the platform injects `file://` or presigned `https://`
  and the CI run wrote both artifacts in well under a second. Inherited from the base.

- **A9 — `#decideSeat`'s wait is unbounded when `autoAdvance.enabled === false`.**
  `packages/core/src/runner.ts:519-524`: `const guard = this.#autoAdvance ? new Promise(...) : null;`
  then `const outcome = guard ? await Promise.race([decided, guard]) : await decided;`. Territory
  always sets it true (`src/coworld/server.ts:70`), so the bound exists in production. Two of the
  batch tests deliberately disable it (`packages/core/tests/runner-batch.test.ts:107,133,167,191,219`),
  which is how the barrier test is written. Flagging that the "every wait is bounded" property is
  configuration-dependent, not structural.

- **A10 — a replay that loads but decodes to zero snapshots sets neither marker.**
  `src/client/App.tsx:191-196` fires the load signal only when `snapshot !== null`;
  `signalError` (`:139-144`) fires only on a `loadReplayFrames` **rejection**. If every frame fails
  `CogwebMessage.safeParse` or `gameSnapshotSchema.safeParse`
  (`src/client/net/cogweb-feed.ts:53-62`), the frames are silently dropped, the page sits on
  "Loading replay…" (`App.tsx:267`), and neither `data-replay-loaded` nor `data-replay-error` is set.
  `tools/ci/viewer_smoke.mjs:509-511` treats that silence as a failure, so CI catches it; the shell
  itself has no self-timeout. *Inferred.*

- **A11 — 13 inherited base test files were not carried over, for source files that still exist.**
  Within *this repo's* history nothing was loosened: `git log --name-only -- '*test*'` shows all test
  files added in the single initial commit `ae0ecfc`, and `07f0ebc` touches only `ci.yml`. Relative to
  the base clone, these base tests have no counterpart while their subject files remain:
  `src/client/App.test.tsx`, `src/client/HexBoard.test.tsx`, `src/client/cg/derive.test.ts`,
  `src/client/colors.test.ts`, `src/client/hex-layout.test.ts`, `src/client/net/cogweb-feed.test.ts`,
  `src/client/net/feed.test.ts`, `src/client/ui/CogView.test.tsx`, `src/client/ui/FeedView.test.tsx`,
  `src/client/ui/nav.test.ts`, `src/shared/protocol.test.ts`, `src/shared/snapshot.test.ts`,
  `src/shared/engine/upkeep.test.ts`; plus the base's playwright `tests/smoke/{live,replay}.spec.ts`
  and `playwright.config.ts`. Some subjects are covered indirectly by
  `src/client/client.test.tsx` (HexBoard, derive helpers) and `src/shared/engine/income.test.ts`
  (upkeep); `App.tsx`'s load-signal effect and `net/cogweb-feed.ts`'s decoder have **no** unit test and
  are covered only by the CI browser smoke. Not a "test loosened during this run" under item 1's
  stated method; recording it because it is the delta a fork can hide in.
  Counter-evidence: `packages/**/tests` gained one file (`runner-batch.test.ts`) and lost none, and
  `vitest.config.ts:16` widens the glob so those vendored tests now actually run — 28 files /
  180 tests passed in run 32838206882, 0 skipped.

- **A12 — `board.test.ts` asserts "at least one gap per room", not "exactly one".**
  `src/shared/engine/board.test.ts:113-117`: `expect(open.length).toBeGreaterThanOrEqual(1)`. The note
  (§Tests, test 1) says "rooms: **exactly one gap** per room". The relaxation is documented in the
  test's own comment and is *correct* given the declared precedence rule — `board.ts:94-100` spares
  any ring tile within distance 1 of *any* hearth, and hearths can be 3 apart, so a room can legally
  have more than one opening. The note's "exactly one" is the loose statement, not the test.

- **A13 — "200 seeded views/states" is 200 *checks* over 25–30 seeded states.**
  `src/game/scripted.test.ts:58-83` loops 30 seeds × living seats × 2 baselines and asserts
  `checked >= 200`; `src/shared/engine/orders.test.ts:124-149` loops 25 seeds × 8 steps × 3 seats and
  asserts `checked >= 200`. Both are substantive (orders.test.ts checks *all 169 tiles* per seat per
  state against `rejectionReason`, i.e. ~50k predicate comparisons), but "200 seeded random mid-game
  views" in the note is not what the counter counts.

- **A14 — the replay is 3.59 MB, two thirds of it `actPrompt` observation dumps.**
  Measured on the CI artifact: 162 `actPrompt` frames × ~14.9 KB `prompt` ≈ 2.4 MB of the 3.59 MB
  total; 19 snapshots × 169 tiles is the rest. The static viewer downloads the whole file from S3
  before its first frame (`packages/ui/src/replay.ts:23`), and it still loaded in 607 ms locally in
  CI. Not a checklist item; relevant to the hosted embed's first-paint budget.

- **A15 — `viewer_smoke.mjs` reports the three scrub readouts but does not gate on them differing.**
  `tools/ci/viewer_smoke.mjs:569-585` collects `scrub[]`; the exit condition at `:642` is
  `!loaded || playFailure || boundsFailure`. Item 13 asks for "`#clock` text differing across the
  0 % / 50 % / 100 % scrub readouts". They *do* differ in run 32838206882 —
  `0%="Turn 4 / 18 · Commit" 50%="Turn 11 / 18 · Commit" 100%="Turn 14 / 18 · Commit"` — but the
  assertion is the reader's, not the script's. `viewer_smoke.mjs` is **byte-identical** to
  `coworld-builder/templates/tools/ci/viewer_smoke.mjs` (`diff -q` → identical), so this is template
  behaviour, not a Territory choice.

- **A16 — a stale `RemotePlayerPilot` request timer can null a newer `#pending`.**
  `packages/coworld/src/remote-pilot.ts:222-238`: the timeout callback sets `this.#pending = null`
  unconditionally, and `#pending` is a single shared slot. When the runner's 20 s guard wins the race
  (which it does, since its timer is armed before the pilot's — `runner.ts:515-522` starts
  `decide()` first, and `decide` only arms its own timer after `#ensureConnected()` resolves), the
  pilot's timer is left armed and fires ~ε later. *Inferred:* with `paceMs = 22 000` that lands
  harmlessly inside the pace sleep; with `paceMs = 0` (the certification fixture) it could land after
  the next turn's `#request` has installed a fresh `#pending`, nulling it and forcing that turn to
  time out too. Requires a real 20 s reply timeout in a `paceMs: 0` run, which CI never produces.
  Inherited from the base. **Untested / could not confirm.**

- **A17 — `SubmissionSchema` puts no length bound on `messages[].text` or `note`.**
  `src/shared/engine/orders.ts:60-66`. The 200/120 caps exist in the tool's *advisory* JSON schema
  (`src/game/prompt.ts:68,73`), in `resolve.ts:142` (applied to `text`, recorded), and in
  `game.ts:151` (applied to `note`, not recorded — see O3). A player is free to send a 1 MB note.

---

## D. Traced and consistent

Grouped by the checklist item each line supports.

**Item 1 — CI green, no test loosened.**
- `gh run list -R Metta-AI/cogame-territory --branch main -w ci.yml` → run **32838206882**,
  conclusion `success`, all three jobs green (`test` 37 s, `docker-smoke` 54 s, `wasm-viewer` 59 s).
  The immediately preceding run 32837923727 failed; `07f0ebc` fixed the manifest-regeneration step.
- `test` job log: `Test Files 28 passed (28)`, `Tests 180 passed (180)` — no `skipped`, no `todo`,
  no `failed`. Followed by `manifest OK` from the `ci.yml:89-102` python gate.
- `git log --name-only -- '*test*' 'packages/*/tests'`: every test file lands in `ae0ecfc`; the only
  later commit `07f0ebc` touches `.github/workflows/ci.yml` (+6/−2) and nothing else. No deleted
  assertion, no widened tolerance, no `skip`, no removed test file in this repo's history.
  (See A11 for the fork-boundary delta.)

**Item 4 — both name spaces.**
- Agents: `src/game/game.ts:115-123` — `newGame` takes `{seed, rules}` and deliberately ignores
  `seatNames`; `src/shared/engine/board.ts:140` sets `alias: ALIASES[seat]`.
  `src/game/redact.ts:107-208` renders every owner/inbox/log entry through `aliasOf`.
  `src/client/client.test.tsx:199-236` asserts `JSON.stringify(redact(state, seat))` contains **no**
  string from `config.players[].name` for all nine seats, and that the public snapshot contains none
  either.
- Viewer: real names ride `SeatPilot.name` → the one-shot `lobby` frame
  (`packages/coworld/src/host.ts:378-403`, fed from `src/coworld/server.ts:62`) → decoded to
  `serverStatus.roster` (`src/client/net/cogweb-feed.ts:71-87`) → `setPolicyNames`
  (`src/client/net/feed.ts:73-77`) → `SeatName` (`src/client/cg/atoms.tsx:29-37`).
  **Confirmed live in the browser:** run 32838206882's `viewer-smoke.json` `scorebug` field reads
  `"1 Verdant Cog C 12 +6/turn (0.24/tick) ▮×4 · 2 Cobalt Cog D 12 …"` — alias **and** policy name,
  side by side, from a real replay in headless chromium.

**Item 5 — degrade, never hang; settles inside 720 s.** Every wait I could find, and its bound:
- connect: `host.ts:425` `await Promise.race([allPlayersConnected, sleep(45 000)])`
  (`CONNECT_DEADLINE_MS`, `constants.ts:131`, wired at `server.ts:67`).
- per-seat reply: two independent bounds — `runner.ts:519-529` races the pilot against
  `maxTimeMs = 20 000` and resolves to `baselineDecision`; and
  `remote-pilot.ts:222-238` caps each `#request` at `actTimeoutMs = 20 000`. Both wired from
  `ACT_TIMEOUT_MS` (`server.ts:68,70`).
- socket connect inside `decide`: `remote-pilot.ts:196-199`, `connectTimeoutMs` default 30 000 — and
  it sits *inside* the promise the 20 s guard races, so it is dominated.
- dead slot: `remote-pilot.ts:27,108-110,155` — 3 consecutive timeouts trip `#unresponsive` and every
  later `decide` fails instantly.
- batch barrier: `runner.ts:467` `await Promise.all(pending.map(...))` where every element is a
  guarded `#decideSeat` that cannot reject (`:515-518` folds rejection into a value). No unguarded
  await.
- pace floor: `runner.ts:481-482` `remaining = simultaneousPaceMs - (now - startedAt)`; sleeps only
  when positive. `paceMs` default 22 000 (`config.ts:38`), cert fixture pins 0.
- episode guard: `runner.ts:487-495` — `spent + 2 * maxTimeMs > episodeDeadlineMs` (40 000 > … >
  660 000) → `settleEarly(state,"deadline")`. Matches the note's step 10 formula exactly.
- shutdown linger: `host.ts:599-605` `await sleep(20 000)` then `process.exit(0)`; wired from
  `SHUTDOWN_GRACE_MS` (`game-cli.ts:22`).
- no unbounded loop: `runner.ts:392-428`'s `while` exits on `isFinished` or a stale generation, and
  `break`s at `:409` if `pendingActors` is empty on an unfinished non-open game. `territoryGame`
  defines no `openPhase`, so `#runOpenPhase` (the one place a wait can be armless) is unreachable.
- *Inferred* arithmetic: because the runner's guard caps a batch at ~20 s and the pace floor is 22 s,
  a full 18-turn episode is `45 + 18 × 22 + 20 ≈ 461 s` **worst case as well as expected** — 38 % of
  1200 s. The deadline guard is a backstop that cannot be reached at 18 turns. Observed in CI:
  docker-smoke's episode (paceMs 0) ran game-container-start → exit in **24 s** including the 20 s
  linger.

**Item 6 — `num_agents`.**
- Manifest: present in all three variants (`variants[0..2].game_config.num_agents = 9`) and in
  `certification.game_config.num_agents = 9`; `len(certification.players) = 9` and
  `len(certification.game_config.players) = 9`. Verified by parsing the committed JSON directly.
  Also declared in `config_schema.properties.num_agents` with `minimum: maximum: 9`.
- `src/game/coworld.test.ts:73-88` pins all of it; `ci.yml:97-100` re-pins it in python.
- `tools/ci/docker_smoke.sh` is the coworld-builder template with only `<slug>/<IMAGE>/<SEATS>`
  substituted — I verified this by re-substituting and diffing against
  `templates/tools/ci/docker_smoke.sh` (exit 0, no content difference). Its four invariants are at
  lines 110-139 and the `SMOKE_SEATS` second declaration at 141-149, all emitting
  `SEAT-COUNT FAIL:`. `SMOKE_SEATS` default is `9` (line 54).
- **`grep -c "SEAT-COUNT FAIL" docker-smoke.log` → 0** on run 32838206882. The log shows nine slots
  enumerated, `game=territory seats=9`, `all 9 player containers exited 0`,
  `smoke OK: seats=9 results=202B replay=3593980B reason=complete`.
- `src/shared/engine/constants.ts:9` `SEATS = 9` is the single source; `config.ts:12,16,21,22` derives
  the token/player array lengths and the `num_agents` literal from it. No other seat count appears.

**Item 7 (first half) — scripted baseline plays a full legal episode.**
- `src/shared/engine/game.test.ts:37-52`: a full nine-seat 18-turn all-scripted episode (5
  homesteaders + 4 raiders, the cert mix) is byte-identical across two runs for one seed, ends
  `reason: "complete"`, `turnsPlayed: 18`, `turn: 19`, one `endcard`.
- `src/game/scripted.test.ts:56-84`: every emitted set over 200+ checks is ≤ `MAX_ORDERS_PER_TURN`,
  `messages.length === 0`, inside `legalClaimTargets`/`legalRazeTargets`, affordable against stored
  paint, `rejectionReason === null`, and produces no `rejected` event from `resolve()`.
- `src/game/replay.test.ts`: the same thing over the **real host**, nine real player processes on the
  real `cogweb.player.v1` bridge, asserting `reason === "complete"`, `turnsPlayed === 18` and
  `fallbacks.sum() === 0` (`:141-143`). Reproduced by docker-smoke in CI, and the resulting
  `results.json` I downloaded reads
  `{"reason":"complete","turnsPlayed":18,"fallbacks":[0×9],"scores":[323,280,346,348,47,223,102,69,54]}`.

**Item 8 (the parts that hold) — tolerant parse, retry once, fallback recorded.**
- Tolerant parse: `packages/llm/src/robust-decide.ts:22-38` `extractJson` tries the ```json fence,
  then the outermost `{…}` slice, then the raw text — i.e. surrounding prose is accepted. The primary
  path forces the `submit_turn` tool (`:71,84`), whose input schema *is* the reply schema
  (`src/game/prompt.ts:30-77`), and the system prompt also states the JSON-first contract
  (`prompt.ts:149-150`).
- Retry once then scripted: `src/game/player.ts:38` `MAX_ATTEMPTS = 2` →
  `robust-decide.ts:63,66` loops twice, re-rendering the user turn with the prior rejection
  (`player.ts:63-68` also folds in the host's `ctx.reason`), then `:94 return opts.baseline()` →
  `player.ts:74` `fallbackMove(baseline, view)` = the **scripted move**, not a hold.
- Fallback accounting: `player.ts:41-44` stamps `fallback: true`; `src/game/game.ts:157-159`
  increments `cogs[seat].fallbacks`; `src/shared/engine/game.ts:33` → `src/coworld/results.ts:24,44`
  → `results.fallbacks[]`, 9-long, bounded in `results_schema`. The host-side hold takes the same
  route (`src/game/game.ts:194-196` `baselineDecision` also sets `fallback: true`), and
  `runner.ts:540-550` emits an `actPrompt` frame with `usedFallback`. `fallbacks` is also on every
  snapshot (`src/shared/snapshot.ts:42,107`).
- One parallel batch per turn (the additional simultaneous-games rule): `src/game/game.ts:113`
  `simultaneous: true` selects `runner.ts:412-414` → `#runBatch`, whose `Promise.all` at `:467` is
  built from the single pre-batch `stateAtTurn` captured at `:453`. `packages/core/tests/runner-batch.test.ts:81-116`
  proves genuine concurrency with a barrier (all nine invoked before any resolves) and that all nine
  saw the **same state object by reference**; `:118-138` proves seat-order application and exactly one
  engine step per turn; `:140-160` proves only the failing seats degrade. I separately verified the
  invariant that makes seat-order application safe: `src/game/game.ts:138-166` mutates only
  `pending`/`submissions` until the last seat arrives, so `s.engine` — the board every
  `rejectionReason` reads — is identical for all nine applies. Confirmed in the real replay: 162
  `actPrompt` frames = 9 × 18, and 19 snapshots.

**Item 11 — legible at 360 px.**
- `src/client/styles.css:270-272` — `.plate-name { flex: 1 1 auto; min-width: 3.2em; … }`, exactly the
  rule the item names.
- `src/client/styles.css:1136-1190` — the `@media (max-width: 640px)` block hides `.plate-tick`,
  `.plate-policy`, `.plate-rank`, `.cogui-sbar-pips/-phases/-scrubhint`, `.cg-navhint`, `.cg-legend`,
  `.cg-endcard-walls/-razes`, and stacks `.cg-grid` to one column.
- **Verified visually.** I opened the CI artifact `renderer-fixture-360.png` from run 32838206882:
  nine scorebug plates at 360 px with full alias text (`Cobalt`, `Verdant`, `Sable`, `Ochre`, `Teal`,
  `Violet`, `Rose`, `Ash`, `Amber`), scores, `+N/turn`, `▮×N`, none ellipsized, `/tick` and policy
  name correctly hidden; a "WARS STARTED 1" ledger whose rows wrap cleanly across three lines
  (including a real `struck` line — "Verdant was struck in its home ring by Ochre — one more and it
  is gone"); and a Channels panel rendering the full-cap CJK+emoji lines with the DM lock glyph.
- `renderer-fixture.json`: `{"ok":true}` at 360, 720 and 1280 px — 61 rows checked, 0 findings,
  0 page errors at each width.

**Item 12 — release order, scaffold, policies.**
- `.github/workflows/coworld-release.yml` step order, by line: `Build the Coworld manifest` (153) →
  `Certify locally` (167) → `Upload the policies` (206) → `Upload the Coworld` (304) →
  `Put the Coworld secret` (342) → `Assemble release-result.json` (364) → `Upload release-result`
  (473) → `Enforce canonical` (498). Exactly build → certify → upload-policies → upload-coworld →
  secret put.
- Freshly built binary in the same run: `coworld build --project . --compose compose.yaml`
  (`:157-165`) runs in the same job that then certifies `dist/coworld_manifest.json` (`:172-174`), and
  `ci.yml`'s docker-smoke builds `pnpm build` + `docker build` before invoking the smoke
  (`ci.yml:138-150`). `wasm-viewer` `needs: docker-smoke` (`ci.yml:174`) and rebuilds the bundle
  itself (`:220-224`).
- Certify gate: `coworld-release.yml:75` pins
  `LIVENESS_MARKER: "Replay liveness: skipped (static replay bundle declared"` and `:178-201` fails
  the run if the marker is absent — i.e. a pod-served viewer cannot pass.
- All three workflows present. `tools/ci/docker_smoke.sh` and `tools/build_replay_viewer.sh` are both
  `100755` in the index.
- Dispatch inputs — release: `version` (`:28`), `policies` (`:32`), `secret_key_name` (`:39`),
  `put_secret` (`:44`), `skip_certify` (`:49`); artifact `release-result` (`:473-481`) plus
  `release-logs`; per-policy `player` field honoured at `:251,260-276,289` with a
  `softmax player use` / `unset` bracket. Submit: `player_id` (`:24`), `policy` (`:30`),
  `league_id` (`:34`); artifact `submit-result` (`:136-141`).
- The placeholder gate: `grep -n '<slug>\|<IMAGE>\|<SEATS>'` across the five named files returns
  **nothing** (exit 1 → the `if` body does not run → the gate exits 0). The only surviving
  angle-bracket names are exactly the four documented as expected residue:
  `<cow_id>` and `<sha>` at `ci.yml:166`, `<run_id>` at `coworld-release.yml:21` and
  `coworld-submit.yml:17`, and `<name>` at `coworld-submit.yml:31`.
- `tools/ci/policies.json`: **four** entries, all `run: "/bin/territory-player"`, four distinct `env`
  bodies. Two `PLAYER_PROMPT` champions (`territory-steward`, `territory-condottiere`), both with
  `USE_BEDROCK: "true"` and `BEDROCK_MODEL: "us.anthropic.claude-haiku-4-5-20251001-v1:0"`; two
  scripted fillers (`PLAYER_SCRIPTED: homesteader|raider`). Champion **#2**
  (`territory-condottiere`, the second `PLAYER_PROMPT` entry) carries
  `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, and it is the only entry with a `player`
  field. All of this is re-asserted in `src/game/coworld.test.ts:121-159`.

**Item 13 — the viewer executes.**
- `ci.yml`'s `wasm-viewer` job is green on `main` at the reviewed sha, `needs: docker-smoke`
  (`:174`), and its `Load the bundle in a real browser` step (`:273-287`) **ran** — no
  `continue-on-error`, no `if:`. Job id 97771949961. It invokes
  `node tools/ci/viewer_smoke.mjs --bundle build/static-replay-viewer --replay dist/smoke/replay.json --timeout 90 --soak 15`
  against the replay docker-smoke produced (downloaded as the `smoke-replay` artifact at `:245-249`).
- Its stdout: `{"loaded":true,"ms":607,"clock":"Turn 4 / 18 · Commit","scorebug":"PAINT BANKED pool 166 → 163 …","feed_lines":20}`,
  then `soak: 15s of playback kept advancing`, then
  `scrub readouts: 0%="Turn 4 / 18 · Commit"  50%="Turn 11 / 18 · Commit"  100%="Turn 14 / 18 · Commit"`.
- `viewer-smoke.json` from the artifact:
  `signals = {"data_replay_loaded":"true","data_replay_error":null,"bridge":["ready"],"bridge_ready":true}`,
  `soak.moved = true`, `soak.page_errors = []`, `failure = null`. **Both** markers exist and both come
  from the shell's own code — `src/client/App.tsx:63-69` (`signalLoaded`: attribute first, then the
  bridge `{type:"ready"}`, in a `requestAnimationFrame` after the first frame is committed,
  `:191-196`) and `:72-79` (`signalError` on the load-failure branch `:139-144`).
- No emscripten quartet exists in this lineage (no `replay-viewer/config.nims`, no `static_replay*.js`,
  no `.nim`), so the MODULARIZE/`onRuntimeInitialized` mismatch class is structurally absent. The
  bundle is one vite build from one repo — `tools/build_replay_viewer.sh:26` execs
  `scripts/build-static-replay-viewer.sh`, which is `pnpm exec vite build --outDir`. Nothing is
  spliced from another starter.
- `ci.yml:226-243` also asserts the three emitted shells (`index.html`, `index-agent.html`,
  `tools/ci/renderer_fixture.html`) are non-empty and that at least one non-empty `.js` chunk exists;
  I confirmed those exact files in the downloaded `static-replay-viewer` artifact.

**Item 15 (the parts that hold).**
- `canvas_text: {total: 0, outside: 0, never_inside: 0, ellipsized: 0}` in the CI evidence, exactly as
  the note predicts (`docs/…-design.md` §Tests 14): this viewer draws text in SVG/DOM, not canvas, so
  the counters cover nothing and prove nothing. `ci.yml:20-24` says so in a comment, and
  `--strict-text-bounds` is deliberately not passed because the 169-hex board is pannable
  (`HexBoard.tsx:18-21`, `ci.yml:20-24`, note §Zoom decision). The brief instructs me to accept the
  DOM fixture as the substitute, and the fixture is wired as its own `ci.yml` step (`:296-301`) and
  ran green at 360/720/1280 px.
- The "CI replay cannot talk" hazard is correctly identified and covered: `docker_smoke.sh` runs
  keyless (CI log: `no ANTHROPIC_API_KEY`), the scripted baselines emit no talk
  (`src/game/scripted.ts:78,107` → `messages: []`, asserted at `scripted.test.ts:66`), and I confirmed
  the real replay artifact contains **zero** `talk` events (`Counter({'order':273,'income':162,'claim':95,'smear':47,'dried':18,'raze':2,'endcard':1})`).
  The fixture is what exercises the talk chrome, over a **real played scenario** rather than
  hand-written frames (`src/client/fixture/scenario.ts:50-84` runs the actual engine).
- Reserved band sized from the server's cap: `Channels` rows are DOM flow, not absolutely-positioned
  bubbles, so there is no "grow into whatever is above it" geometry; the fixture measures them in the
  real font at the real width.

**Engine — the 10-step resolution order, traced against the note step by step.**
- Step ordering is literal in `src/shared/engine/resolve.ts`: validate+budget `:110-131`,
  talk `:133-149`, raze `:151-208`, strike bookkeeping `:198-214`, claim `:216-251`,
  transfer `:253-261`, charge `:263-272`. Upkeep 9a-9d in `upkeep.ts:27-75`; 9e (advance +
  `TurnRecord`) in `game.ts:95-114`; step 10 (pace + deadline) in `runner.ts:480-495`.
- **Raze before claim:** verified both by reading (`resolve.ts:151` precedes `:216`) and by
  `resolve.test.ts:31-51`, which razes and claims the *same* tile in one turn and asserts the claim
  lands on the now-`cracked` tile at the **halved** yield.
- **Two razes in one turn → rubble; a same-turn claim on it is `voided` with the paint spent:**
  `resolve.ts:166` (a raze on rubble is a no-op but stays charged), `:175` (`destroyed += 1`),
  `:229-232`; `resolve.test.ts:67-94` asserts all three orders were charged.
- **Smear:** `resolve.ts:245-250` clears owner/wet and emits `smear` with sorted seats; both
  claimants still pay via step 8. `resolve.test.ts:96-119`.
- **Void:** `resolve.ts:229-236`, kinds `"rubble"` (live) and `"owned"` (see A3).
- **Charge:** `resolve.ts:263-272` throws on underflow rather than minting paint;
  `resolve.test.ts:151-164` runs 12 turns and asserts no seat ever goes negative.
- **Upkeep 9a dry:** `upkeep.ts:30-39` dries exactly the tiles with `wet && claimedTurn === turn` and
  records them as `wetThisTurn`. **9b income:** `:41-63` skips those same tiles, so a tile claimed
  this turn pays 0 this turn and `effYield` from next (`income.test.ts:42-59`), and eliminated seats
  earn nothing (`:74-83`). **9c credit:** `:65-70` — the credit array is consumed and reset, so
  salvage/transfers are spendable only from the next turn (`income.test.ts:87-115`).
  **9d life:** `:72-74` → `life.ts:31-69`. **9e advance:** `game.ts:96-101`.
- **Strike machine / permadeath:** `resolve.ts:199-206` requires all four conditions — a *different*
  seat committed the raze (`target.seat === seat` skipped), the target owned the tile at the **start
  of Resolve** (`ownerAtStart`, captured at `:156-157` before any raze lands), the tile is in
  `homeRing(target.seat)` (`board.ts:37-44`, 7 coordinates), and the target is alive.
  `life.ts:41-61`: `steady`+struck → `staggered`; `staggered`+struck → `eliminated` (paint 0, all
  claims reverted with tile **state** preserved, `wallsHeld = 0`); `staggered`+quiet → `steady` with a
  `recovered` event. Because `staggered` survives exactly one turn, "the immediately following turn"
  is structural. `life.test.ts:68-139` covers all five cases including 5+6 eliminating and 5+7 not,
  the state-preserving revert, the frozen score, and absence from `pendingActors`.
- **Salvage:** `resolve.ts:186-195` — only when `victim === seat && from_state === "wall"`, i.e. the
  first raze of a tile you own; `SALVAGE_MULT × effYield`; credited (next-turn money) and banked.
  `resolve.test.ts:133-149` asserts the second raze on your own cracked tile pays nothing.
- **Income arithmetic:** `constants.ts:23-36` — `effYield` and the identity
  `effYield × 25 × 0.04 === effYield`, asserted for y ∈ {0,1,2,3} at `income.test.ts:20-28`.
- **Wars ledger:** `resolve.ts:196-197` adds `"attacker>victim"` on the first raze on a victim's
  ground; the viewer recomputes the same set independently
  (`src/client/cg/derive.ts:145-155`) and `client.test.tsx:104-122` cross-checks the two.
- **Board:** `board.ts:113-170` — 169 tiles at radius 7, seeded yields via `makeRng`, the nine
  ring-5 hearths owned dry with `claimedTurn: 0`, `STARTING_PAINT = 12`. `board.test.ts:26-49`
  asserts the hearth list matches the note **verbatim** (`5,0 5,-3 4,-5 0,-5 -3,-2 -5,1 -5,5 -2,5 1,4`),
  all on ring 5, minimum pairwise distance exactly 3. Variant overlays at `board.ts:51-101`,
  each asserted at `board.test.ts:103-146`.
- **Purity:** every engine function copies before mutating (`resolve.ts:102-108`,
  `upkeep.ts:22-25`, `life.ts:33,47-50`); no clock, no IO, no `Math.random` — the only randomness is
  `makeRng(seed)`. `game.test.ts:37-42` proves byte-identical replays for one seed.

**Replay writer.**
- Envelope self-sufficiency: `packages/coworld/src/host.ts:444-450` writes
  `{protocol, ...replayMeta, frames, usage}`; `src/coworld/server.ts:89-107` supplies
  `players` (seat/alias/policy/player), `config` (seats/turns/variant/seed/ticksPerTurn/
  razeOpensTurn/flingRange/salvageMult) and the whole `results` object. `src/shared/replay.ts:46-56`
  types it. **Verified against the artifact:** top-level keys are exactly
  `['protocol','players','config','results','frames','usage']`.
- One snapshot per turn: `runner.ts:476` emits one snapshot per batch; `runner.ts:264-267` collapses
  mid-turn emits to one entry per turn. Verified: 19 snapshot frames, turns 1..19 distinct, each with
  169 tiles, 9 cogs and `seed: 7`. Asserted at `replay.test.ts:147-179`.
- Event vocabulary: `src/shared/engine/log.ts:17-33` declares 15 kinds; `replay.test.ts:158-167`
  asserts every recorded `kind` is a member and that `endcard` appears exactly once. Verified: the
  artifact's kinds are all in the list. `src/shared/protocol.ts:72-117` mirrors all 15 with `.strict()`
  shapes for the client boundary, and `src/game/game.ts:57-68` routes each to the right renderer.
- `final` before artifacts: `host.ts:436-437` sends the `final` frame to every slot **before**
  `writeResults`/`writeReplay` at `:439-450` — the note's `bedrock_usage`-survival ordering, and the
  player logs it at `player-runtime.ts:87`.
- Strict-JSON replay: `docker_smoke.sh` runs with `SMOKE_REQUIRE_REPLAY_JSON=1` (default, line 57)
  and the CI log confirms the replay parsed. `replay.test.ts:95-99` decodes the bytes under a fatal
  `TextDecoder` and round-trips `JSON.parse`.

**Manifest and packaging.**
- Generated-equals-committed: `src/game/coworld.test.ts:40-42` compares the committed JSON to
  `buildTerritoryManifest()`; `ci.yml:83-88` additionally regenerates **in place** and runs
  `git diff --exit-code`. The head commit `07f0ebc` exists precisely to fix that step, and it passed.
- Bounded arrays: `coworld.test.ts:57-71` walks both schemas recursively (`arrayProps`) and asserts
  **no** array property lacks `minItems`/`maxItems`. I re-read the generated schemas: `tokens` 9/9,
  `players` 9/9, `scores` 9/9, `fallbacks` 9/9, `razes` 9/9, `eliminated` 0/9.
- `game.name = "territory"` (no underscore), so the secret namespace
  `secret://coworld/territory/anthropic_api_key` equals it; `secret put "$SLUG" …` in
  `coworld-release.yml:353-354` with `SLUG: territory` (`:61`). `episode_timeout_minutes: 20`
  (so 60 % = 720 s). `game.runnable = {type:"game", image:"{{TERRITORY_IMAGE}}", run:["/bin/territory"]}`
  — the image placeholder derived from the compose service name `territory` (`compose.yaml:2`).
- Both declared runnables are seated in the cert fixture (homesteader ×5, raider ×4), asserted at
  `coworld.test.ts:90-104` — `players_missing` cannot fire.
- Dockerfile shims: `Dockerfile:18-20` writes `/bin/territory` and `/bin/territory-player` and
  `chmod +x`. `src/game/player.ts:116` guards on `argv[1] === fileURLToPath(import.meta.url)`, which
  matches under the shim; proven by `all 9 player containers exited 0`.

---

## E. Could not determine

- **Whether the renderer fixture's scenario contains an `eliminated` row.** Its docstring
  (`src/client/fixture/scenario.ts:4-7`) claims "razes, a smear, a strike and an elimination". I
  confirmed **raze**, **smear** and **struck** rows are really rendered by reading them off
  `renderer-fixture-360.png`; an `eliminated` row was not in the visible portion (the ledger is
  scrollable and the 360 px screenshot shows 5 of ~13 rows). What would settle it: running
  `playScenario(7, 7)` and printing the event-kind histogram, or reading
  `renderer-fixture-1280.png` at full height. I could not run vitest here (no `node_modules` in the
  sandbox and `zod` is unresolvable).
- **Whether `struck` / `eliminated` / `voided` / `transfer` / `salvage` / `recovered` / `rejected`
  chrome renders correctly against *real replay bytes*.** The CI replay carries only
  `order/income/claim/smear/dried/raze/endcard` (verified histogram above), so those seven ledger and
  turn-log branches are exercised only in jsdom and in the fixture. What would settle it: an episode
  with a real elimination fed through `viewer_smoke.mjs`, or extending the fixture scenario to force
  each kind.
- **A16's stale-timer race.** I could construct the ordering argument but not a run that produces a
  real 20 s reply timeout under `paceMs: 0`. What would settle it: a unit test that fakes a 20 s
  silence on two consecutive turns with `simultaneousPaceMs: 0` and asserts the second turn still
  gets its reply.
- **Whether undici's ~300 s default actually bounds the platform's artifact PUTs** (A8). Depends on
  the runtime and on whether the platform's presigned URL can stall. What would settle it: an explicit
  `AbortSignal.timeout()` in `artifacts.ts`, or a documented platform-side bound.
- **The design note's `poolStart ≈ 149`.** The real seed-7 board reported `poolStart: 166`
  (`results.json` from CI) and the fixture's scorebug header reads `pool 166 → 163`.
  `board.test.ts:96-101` bounds the 20-seed mean to (130, 170), so 166 is inside the asserted band
  and ~1.4σ above the note's analytic 148.7. I could not tell whether the note's figure or the RNG's
  actual distribution is the odd one out without running the generator; it affects only prose
  (`deadweight.md`'s "149 → 121" example), not any assertion.
