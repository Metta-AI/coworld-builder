# r1 review — cogolf

Repo: `/workspace/cogame-cogolf` @ `a60233b8aad39e22890f3b3c31cde05dee3b7e79` (current `main`)
Range: `c0e0139..a60233b` (2 content commits: `c6eb4e2` the game, `a60233b` the scroll-overlay pin)
Design note: `/workspace/coworld-builder/runs/2026-08-24-cogolf/design.md`
Starter (read-only): `/workspace/starters/cogame-factorio`
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST
Files read: 61 (all of `server/cogame_cogolf/`, `players/`, `client/`, `replay-viewer/`,
`tools/`, `tests/`, `.github/workflows/`, `Dockerfile`, `compose.yaml`,
`coworld_manifest_template.json`, `docs/`, `viewer/build_viewer.sh`, `viewer/assets/atlas.json`,
plus the starter's six `client/` files and `replay-viewer/config.nims` for diffing)
Also run locally: `pytest` (406 passed, 3 skipped — the 3 are `test_viewer.py` wasm-build skips),
`gh run list/view` for CI evidence.

I traced; I did not fix anything and I did not touch the repo.

---

## Blocking

Two findings falsify a named checklist item. Both are cited to `file:line` and both are
reproducible from the tree.

### B1 — the page's own failure paths never set `data-replay-error`

- **Where:** `client/replay_broadcast.html:551-575` (`showError`, `showFailCard`),
  `client/replay_broadcast.html:1386-1393` (the boot catch),
  `client/replay_broadcast.html:589-598` / `614-629` (the no-data and stuck cards).
  The only writer in the whole bundle is `client/static_replay.js:33`.
- **Observed, traced:**
  - `client/static_replay.js:29-38`:
    ```js
    failed = true;
    console.error(error);
    var message = (error && error.message) || String(error);
    document.documentElement.setAttribute('data-replay-error', message);
    ```
    This is `showFailure()`, called for Worker/wasm failures only (`static_replay.js:190`,
    `:196`, the `message.type === 'error'` branch).
  - `client/replay_broadcast.html:1386-1392`:
    ```js
    window.addEventListener("load", () => {
      boot().catch((e) => {
        showError("viewer failed", e);
        showFailCard("Replay didn’t load", [String(e && e.message || e), …], true);
      });
    });
    ```
    `showError` (`:551-560`) writes `#banner`, `#status`, `document.body.dataset.state`.
    `showFailCard` (`:561-575`) writes `#failcard`. Neither touches
    `document.documentElement`. `grep -n 'data-replay-error' client/replay_broadcast.html`
    returns nothing.
  - The failures that route this way and *not* through `static_replay.js` are: the
    `fetch(REPLAY_URL)` failure (`:1316`, `throw new Error(\`fetch … HTTP ${resp.status}\`)`)
    and the `RD.parseReplay` throw (`:1319`), both inside `fetchReplay` (`:1312-1321`);
    `throw new Error("replay has no beats")` (`:1366`); the 12 s no-data card
    (`:589-598`); and the 45 s stuck card (`:614-629`).
  - `tools/ci/viewer_smoke.mjs:364` is the fast-fail probe
    (`if (readout && readout.error_attr) { failure = …; break; }`); with the attribute never
    set, that whole class of failure falls through to `viewer_smoke.mjs:371`
    (`timeout: no data-replay-loaded="true" … within ${args.timeout}s`) after the full
    `--timeout 90`.
- **What the note says it should do:** design.md:590-592 — “`showFailure()` **and the page's
  `showFailCard()`** both set `document.documentElement.setAttribute('data-replay-error',
  <message>)`. `tools/ci/viewer_smoke.mjs` reads exactly those two attributes.”
- **Checklist item:** 13, second bullet — “`index.html` / `static_replay*.js` set
  `data-replay-loaded="true"` on `<html>` on the **first drawn frame** and
  `data-replay-error="<message>"` on failure. **Both markers, both set from the shell's own
  code paths**.” *(category: static-viewer)*
- **Why it matters, concretely:** the loaded marker is correct and proven (see T13 below —
  CI reports `{"loaded":true,"ms":307,…}`), so the viewer is not broken. What is missing is
  the negative signal from the shell's own half: a bad `?replay=` URL, a 404 on the replay,
  or a schema-invalid replay renders the fail card for a human but reports nothing machine
  readable, so the smoke reports a generic 90 s timeout instead of the actual message.
- **What the existing test checks instead:** `tests/test_viewer.py:149` asserts only
  `"setAttribute('data-replay-error'" in js` for `static_replay.js` — the page is never
  checked for it.

### B2 — no test asserts the event-fold reproduces the recorded per-hole state

- **Where:** the re-derivation exists twice —
  `client/replay_doc.js:132-177` (`stateAt(doc, index)`) and
  `replay-viewer/cogolf_replay.nim:304-337` (`sceneAt(upto)`) — and the recorded state it
  should reproduce is `holes[]` (`server/cogame_cogolf/engine.py:636-666`,
  `server/cogame_cogolf/replay.py:55-59`). No test in `tests/` compares the two.
- **Observed, traced:**
  - The viewer really does derive from the fold, not from a parallel recording:
    `client/replay_broadcast.html:700` `function state() { return RD.stateAt(replay, beatIdx); }`,
    and every readout goes through it — `scoreAt` (`:802-805`), `renderClock` (`:871-885`),
    `renderBeatPanels` (`:939-1004`, `const fired = st.shots[seat] || []` at `:977`,
    `const par = st.par[seat]` at `:996`), `renderFeed` (`:925-937`).
    `replay_doc.js:145-175` folds `hole_start` → resets `shots`/`par`/`fallback`,
    `submission` → `fallback[slot]`, `test_verdict` → `shots[slot].push(ev)`,
    `par_result` → `par[slot]`, `hole_score` → `cumulative`, `episode_end` → `done`.
  - The wasm board does the same fold independently: `cogolf_replay.nim:311-337` walks
    `replay.beats[0..last]` and accumulates `broken[]` from `test_verdict.outcome ==
    "breach"` and `par_result.parFails`, and `cumulative` from `hole_score`.
  - Three things on the page come from `replay.holes[…]` rather than the fold: the seat's
    `impl` source and `par_total` (`replay_broadcast.html:966`, `:972-976`, `:1000`), the
    spec prompt (`:967`) and the scroll text (`:904-917`). Those are static per-hole data
    that no event carries in full (`submission` only carries `impl_lines`/`impl_chars`), so
    they are not a parallel recording of derivable state.
  - What no test does: nothing asserts
    `stateAt(doc, lastBeatOfHoleK).cumulative == doc.holes[k].cumulative`, or
    `stateAt(…).shots[i]` == `doc.holes[k].seats[i].tests`, or
    `stateAt(…).par[i] == doc.holes[k].seats[i].par_fails`.
    `tests/test_viewer.py:95-98` is the closest:
    ```js
    const state = RD.stateAt(doc, doc.events.length - 1);
    if (!state.done) throw new Error('last beat is not the end');
    const ro = RD.seatReadout(RD.stateAt(doc, Math.floor(doc.events.length / 2)), 0);
    console.log(JSON.stringify({kinds: [...kinds], shots: ro.shots}));
    ```
    `state.done` is the only assertion; `ro.shots` is printed and the Python side
    (`tests/test_viewer.py:103-106`) asserts only on `out["kinds"]`, never on `out["shots"]`.
    `tests/test_replay.py` asserts the structural contract (`:79-99`) and one-of-every-kind
    (`:102-109`) but never folds the events.
  - Nothing cross-checks the JS fold against the Nim fold either; they are two independent
    implementations of the same reduction.
- **What the note says:** design.md:420 lists `events[]` as “the beat stream”, and the
  viewer section (design.md:670-675) says the replay bytes are the viewer's only input. The
  note does not itself promise a re-derivation test; the checklist does.
- **Checklist item:** 2 — “Replaying the recorded events through the sim reproduces the
  recorded per-tick state **frame by frame**, and the viewer derives its display from that
  same re-derivation — not from a parallel recording. **A test asserts it.**”
  *(category: correctness)*
- **Why blocking:** the first two clauses are satisfied by construction (traced above); the
  third — “a test asserts it” — is not met anywhere in `tests/`. A drift between what the
  engine emits as events and what it records in `holes[]` (they are built in two separate
  places, `engine.py:326-342` for the events and `engine.py:636-666` for the hole record)
  would be caught by no test in the tree.

---

## Non-blocking

### N1 — an LLM-level fallback is recorded only on stderr, and is counted nowhere

- **Where:** `players/llm_player.py:362-369`, `:370-372`, `:376-379`;
  `players/client.py:436-444`, `:518-522`, `:272-280`; `server/cogame_cogolf/engine.py:380-395`.
- **Observed, traced:** when the API errors, refuses, or returns unparseable text,
  `LLMPolicy.submission` returns `scripted_submission("literalist", hole, observation)` — a
  *valid* payload. `players/client.py:436-438`:
  ```python
  message = normalize_submission(payload, hole)
  if message is not None:
      return message, False
  ```
  so `_call_policy` returns `harness_fallback = False`, and `client.py:520-522` records
  `"harness_fallback": false` in the telemetry event. `Telemetry.build_zip`
  (`client.py:272-280`) therefore reports `"harness_fallbacks": 0`. Server-side the reply is
  a well-formed `submission`, so `engine.py:392` sets `causes[slot] = None`, no
  `SeatOutcome.fallbacks` counter increments (`engine.py:384-386` is the only increment
  site), and the replay's `submission` event carries `"fallback": null` (`engine.py:328-332`).
  An episode in which every LLM call failed reports `fallbacks: [0, 0]` in
  `results.json` and `harness_fallbacks: 0` in the player artifact zip.
  The only record is stderr: `llm_player: API call failed at hole {h} on {model}: …`
  (`llm_player.py:362-363`), `llm_player: model refused at hole {h}; playing scripted`
  (`:371`), `llm_player: falling back (unparseable reply)` (`:378`).
- **What the note says:** design.md:282 — “logs `llm_player: falling back (unparseable
  reply)`”. The note only promises the log line, and the code delivers it verbatim.
- **Checklist item touched:** 8 — “the fallback is recorded so phase 60 can count it.” It
  *is* recorded and greppable from the player container's logs; it is not countable from
  `results.json`, the replay, or `summary.json`. I am reporting the distinction, not
  claiming a violation: the checklist says “recorded so phase 60 can count it”, and the
  stderr lines satisfy that literally.

### N2 — no retry before the LLM fallback on the hosted sidecar transport, and none on a parse failure

- **Where:** `players/llm_player.py:189-190`, `:192-213`, `:263-267`, `:275-276`, `:344-369`,
  `:376-379`; `server/cogame_cogolf/engine.py:367-376`.
- **Observed, traced:**
  - The anthropic-SDK path gets one transport retry: `llm_player.py:275-276`
    `self._client = client.with_options(timeout=self.timeout, max_retries=1)`.
  - The **hosted pod path does not**. `llm_player.py:263-267` selects `_BedrockHttpClient`
    whenever `AWS_ENDPOINT_URL_BEDROCK_RUNTIME` or `AWS_BEARER_TOKEN_BEDROCK` is set — i.e.
    the sidecar the platform actually uses. `_BedrockHttpClient.with_options`
    (`llm_player.py:189-190`) is `return self`, and `create` (`:192-213`) is a single
    `urllib.request.urlopen` whose failure is wrapped in `RuntimeError` and re-raised. The
    outer handler at `:350`/`:361` then goes straight to
    `return scripted_submission("literalist", hole, observation)` — zero retries of the call.
  - On a parse failure there is no re-ask either: `llm_player.py:376-379`
    `payload = parse_reply(text); if payload is None: … return scripted_submission(…)`.
    `tests/test_players.py:161-181` pins this (the fake client's `create` is invoked once).
  - There **is** one retry at the engine level — `engine.py:367-376` re-sends the identical
    observation with `"retry": true` and `retry_deadline_seconds` — but it never fires in
    this path, because the player already answered inside the deadline with the scripted
    move.
- **What the note says:** design.md:253 keeps “the `with_options(timeout=…, max_retries=1)`
  wrapper and the ‘any API failure → safe move’ discipline”; design.md:281-282 says an
  unparseable reply goes straight to the literalist submission. The code matches the note.
- **Checklist item touched:** 8 — “retries **once** on a parse or transport failure, then
  falls back to the scripted move.” The engine-level retry-once exists and is tested
  (`tests/test_engine.py:60-73`); the policy-level retry-once exists only on the
  non-sidecar transport. Reporting the split; the judge decides whether “retries once”
  is satisfied by the engine's re-send.

### N3 — `/client/replay` routes are present in the game server (replay mode only)

- **Where:** `server/cogame_cogolf/server.py:748` (`raise web.HTTPFound("/client/replay/")`),
  `:780`, `:781`, `:783` (`app.router.add_static("/client/replay/", dist)`);
  documented at `docs/PROTOCOL.md:23`; exercised by `tests/test_server.py:178`.
- **Observed, traced:** all four registrations live inside `make_replay_app`
  (`server.py:732-784`), which is only ever constructed from `async_main` when
  `COGAME_LOAD_REPLAY_URI` is set (`server.py:793-808`). In episode mode the app is built by
  `GameServer.make_app` (`server.py:337-344`), whose route table is exactly
  `/healthz`, `/player`, `/global`, `/client/global`, `/client/player` — no replay route.
  The manifest declares only the static bundle
  (`coworld_manifest_template.json:11-14`: `"replay_viewer": {"bundle":
  "static-replay-viewer"}`), `tools/build_replay_viewer.sh` exists, is mode `100755`
  (`git ls-files -s` → `100755 … tools/build_replay_viewer.sh`) and is wired as the
  `coworld build` hook. `coworld-release.yml:195-201` hard-fails if certification does not
  report the static bundle.
  `client/broadcast_core.js:196` also contains `['/client/replay', '/replay']`, but that
  file is byte-identical to the starter's (verified by `diff`) and is a live-websocket URL
  list the static bundle never reaches.
- **What the note says:** design.md:345 explicitly keeps this — `server.py` serves “replay
  mode (`/replay-data`, `/client/replay/`) — the starter's file with the FLE startup path
  removed”, while design.md:572 says “**Never a `/client/replay` pod viewer.**”
- **Checklist item touched:** 3 — “No `/client/replay` pod path **anywhere**.”
  *(category: static-viewer)* A literal reading of “anywhere” is falsified by
  `server.py:780-783`; the operational reading (no pod viewer is declared or reachable in an
  episode) holds. I record both readings and the exact lines; I am not asserting which the
  checklist means.

### N4 — `game.docs` uses `"type": "uri"`, checklist item 10 spells `"type": "text"`

- **Where:** `coworld_manifest_template.json:393-417` (`docs.readme.type == "uri"`,
  both `pages[].content.type == "uri"`).
- **Observed:** the *shape* matches item 10 exactly —
  `{"readme":{…}, "pages":[{"id","title","content":{…}}]}` — with `"type"` set to `"uri"`
  and `"value"` a GitHub blob URL. `game.protocols` carries both `player` and `global`
  (`:383-392`), each `{"type":"uri"}` pointing at `docs/PROTOCOL.md`.
  `tests/test_manifest.py:96-101` asserts `content["type"] == "uri"`, and
  `tests/test_manifest.py:158-166` runs `coworld.manifest.validate_upload_manifest` on the
  substituted manifest with coworld 0.1.42 and passes (I re-ran it locally).
- **What the note says:** design.md:705-707 specifies `"type":"uri"` deliberately.
- **Checklist item touched:** 10 *(category: manifest)*. The keys and nesting are right; only
  the `type` discriminator differs from the checklist's literal text, and the platform's own
  validator accepts it.

### N5 — `welcome.episode.seed` plus the published draw formula lets a seat compute every later hole's spec

- **Where:** `server/cogame_cogolf/server.py:394` (`"seed": self.seed` inside
  `welcome.episode`); `server/cogame_cogolf/engine.py:195`
  (`self.spec_keys = random.Random(self.seed).sample(keys, config.holes)` over
  `keys = sorted(self.deck)`); `docs/RULES.md:136` publishes the formula verbatim
  (“`random.Random(seed).sample(sorted(deck_keys), holes)`”); the deck is the public
  `server/cogame_cogolf/specs/__init__.py:33-38`.
- **Observed:** a policy that knows `seed`, `deck` and `holes` (all three are in `welcome`,
  `server.py:387-396`) can reproduce `spec_keys` exactly and pre-compute all nine specs at
  t=0. It is symmetric — both seats get the same `seed` — and neither gets the reference,
  the par tests or the ambiguity note (`engine.py:569-579` `_spec_view` excludes all three;
  `tests/test_engine.py:152-166` asserts it).
- **What the note says:** design.md:513 lists “which specs later holes will use” under
  **Hidden from a seat**; design.md:464-478 mandates that every episode parameter be stated
  at t=0 and shows `"seed": 1234567` in the `welcome` example. The two statements are in
  tension and the code implements the second.
- **Checklist item touched:** none.

### N6 — the design's timing arithmetic omits the 20 s shutdown grace; the engine's own worst case is *lower* than the note's

- **Where:** `engine.py:219-255` (`run`), `:225-233` (wall guard), `:257-272`
  (`_await_connections`), `:274-285` (`_space_holes`), `:359-395` (`_collect`), `:363-364`
  and `:372-373` (both deadlines `min`-clamped by `_wall_remaining()`), `:458-459`
  (one reference batch), `:501-504` (two impl batches via `asyncio.gather` over
  `asyncio.to_thread`); `sandbox.py:117-120` (`subprocess.run(..., timeout=self.batch_seconds)`);
  `server.py:53` + `:581-588` (`SHUTDOWN_GRACE_SECONDS = 20.0`, unconditional
  `await asyncio.sleep(20)`); `server.py:55` + `:659` (`DONE_SEND_TIMEOUT_SECONDS = 3.0`);
  `uris.py:29-31`, `:93-119` (3 attempts × 30 s + 1.5 s backoff per artifact);
  `aiohttp/web_runner.py:52` (`shutdown_timeout: float = 60.0`, the bound on
  `runner.cleanup()` at `server.py:859`).
- **Observed, traced arithmetic (defaults: budget 700, reserve 80, spacing 4, hole 40,
  retry 15, batch 6):**
  - A hole may only start with `wall_remaining >= 80`, so the last hole starts at elapsed
    ≤ 620 (`engine.py:226`).
  - `_space_holes` ≤ 4 s; `_collect` ≤ 40 + 15 = 55 s; `_legality` = **one** 6 s batch;
    `_cross_fire` = **two** 6 s batches run **concurrently** (`asyncio.gather` at
    `engine.py:501`), so 6 s, not 12.
  - Worst hole = 4 + 55 + 6 + 6 = **71 s** (the note assumes 73 s from “3 subprocess
    batches × 6 s = 18 s”, design.md:222-224 — the code is faster because the two impl
    batches are parallel).
  - Worst engine wall = 620 + 71 ≈ **691 s** — scoring and the `episode_end` event are
    complete here (`engine.py:246-250`), and `done` is broadcast next
    (`server.py:552`, before artifacts, as the note requires).
  - After that: `_broadcast_done` ≤ 3 s, artifact writes, then an **unconditional 20 s**
    `_shutdown_grace`. With `file://` artifacts that is ≈ **714 s** of process life against
    the note's stated 680 s and the 720 s (60 %) budget.
  - With `http(s)://` artifact URIs that all fail, `uris.write_uri` costs up to
    3 × 30 s + 1.5 s = 91.5 s **per artifact** (two artifacts, sequential at
    `server.py:573-578`) → up to ~183 s more, i.e. ~897 s of process life. Every wait is
    still explicitly bounded and the total is well inside the 1200 s container kill; the
    episode has already settled and scored at ≤ ~691 s and `done` has already gone out.
  - `tests/test_manifest.py:106-120` checks `73 × 9 + 23 = 680 <= 720` and models neither
    the 20 s grace nor the artifact-retry tail.
- **Checklist item touched:** 5 — “Every wait (LLM call, seat reply, round barrier) has an
  explicit bound; the episode settles and scores inside **60 %** of `episodeTimeoutSeconds`
  (720 s of 1200); there is no unbounded loop or blocking read.”
  *(categories: hang, timeout)* — **I could not find any unbounded wait or blocking read
  in the episode path** (see T5 in “Traced and consistent”), and settle-and-score lands at
  ≤ ~691 s < 720 s. The observation is only that the note's 680 s figure excludes the 20 s
  grace, so the *process lifetime* worst case is ~714 s, still under 720 s with local
  artifacts.

### N7 — `broken_reason` is the one replay string that does not pass through `clean_text`

- **Where:** `engine.py:648` (`"broken_reason": broken[slot]`); the value's only sanitiser
  is `sandbox.py:77-79` `_clip` (300-char cap by `str` slicing, `\n` → space), set at
  `sandbox.py:155-156`.
- **Observed:** every other string in the hole record goes through `clean_text`
  (`engine.py:57-67`): `impl` (`:126`), `note` (`:128`), `name`/`why` (`:117-122`),
  `observed` (`:536-537`), spec `title`/`prompt`/`ambiguity` (`:295-296`, `:574-575`, `:662`).
  `_clip` **is** rune-safe (Python `str` slicing), so item 9's truncation rule holds; what it
  does not do is replace lone surrogates or strip control characters other than `\n`.
  Traced consequence: the child cannot in practice emit a lone surrogate — `sandbox_runner.py:126-128`
  writes with `PYTHONIOENCODING=utf-8` (`sandbox.py:111`), so such a line would raise in the
  child and never reach the parent — and `json.dumps` escapes any remaining control character
  as `\uXXXX`, so the replay still parses under a strict reader. No observed break.
- **What the note says:** design.md:544-547 and `replay.py:10-13` both state the rule for
  “every string that lands in the replay”.
- **Checklist item touched:** 9 only in the sense that the truncation *is* rune-safe here.

### N8 — `clean_text` strips Unicode category `Cf`, not only control characters

- **Where:** `engine.py:62-64`:
  ```python
  value = "".join(ch for ch in value
                  if ch in "\n\t" or unicodedata.category(ch)[0] != "C")
  ```
- **Observed:** `category(ch)[0] != "C"` drops `Cc` (control), `Cf` (format), `Cs`
  (surrogate), `Co` (private use) and `Cn`. ZWJ `U+200D` is `Cf`, so a ZWJ emoji sequence —
  e.g. the golfer `🏌️‍♀️` at `tests/test_replay.py:22` — is split into its components in
  the replay. The output is still valid UTF-8 and
  `tests/test_replay.py:57-65` passes.
- **What the note says:** design.md:129 and :546 — “control characters other than `\n` and
  `\t` are stripped”.
- **Checklist item touched:** none.

### N9 — the page owns the beat-marker layer instead of calling `chrome_common`'s

- **Where:** `client/replay_broadcast.html:765-789` (`renderBeatButtons`), `:790-798`
  (`applyBeatSpoilers`); `client/chrome_common.js:180-200` (`setMarkers`/`placeMarkers`) is
  never called — `grep -n 'C.setMarkers' client/replay_broadcast.html` returns nothing.
- **Observed:** the page creates real `<button type="button" class="beat-marker <kind>">`
  elements with `title`, `aria-label`, `dataset.beat` and a click handler
  `setPlaying(false); selectBeat(m.idx)` (`:772-785`). Because `setMarkers` is never called,
  `chrome_common.placeMarkers` appends nothing and `chrome_common.applySpoilers`
  (`:155-163`) iterates an empty `markerEls` — no double render, no conflict — and the
  page's own `applyBeatSpoilers` does the spoiler gate, called from `renderTransport`
  (`:889`) and from the `onSpoilers` callback the page hands `ChromeCommon` (`:670`).
  CSS exists for every kind the writer emits: `.beat-marker.hole|.breach|.illegal|
  .fallback|.killer` at `:401-406`, and `client/replay_doc.js:86-95 markerKind` returns
  exactly those five and `null` otherwise; the `.scrub-key` legend is relabelled to the same
  five (`:517`), and the starter's dead `.error`/`.noop`/`.dead` rules are removed
  (`tests/test_viewer.py:276-278` asserts their absence).
- **Checklist item touched:** 14(d) — which names `chrome_common.markBeat(tick, kind, team,
  label)`. **That API does not exist in this starter lineage:** `grep -n markBeat` over
  `/workspace/starters/cogame-factorio/client/` returns nothing; the factorio
  `chrome_common.js` exposes `setMarkers`, which builds non-interactive `<div>`s
  (`chrome_common.js:191-199`). The *substance* of 14(d) — labelled `<button>`s that seek to
  their tick, CSS for every emitted kind — is satisfied. design.md:597-599 and :627-632
  anticipate exactly this, and the page carries the required banner comment
  (`:759-764`).

### N10 — the replay's `config.seed` is the unresolved config value

- **Where:** `config.py:225` (`"seed": self.seed` in `to_dict()`), against
  `config.py:206-212` (`resolve_seed()` mints `secrets.randbits(32)` when `seed <= 0`).
- **Observed:** with the manifest default `seed: 0`, the replay's `config.seed` is `0` while
  the resolved value is recorded twice elsewhere — top-level `seed` (`replay.py:75`, fed
  from `GameServer.seed`, `server.py:326` → `server.py:518`) and `result.seed`
  (`results.py:89-90`). `client/replay_doc.js:41` validates the top-level `doc.seed` and the
  page reads `replay.seed` (`replay_broadcast.html:819`), never `replay.config.seed`.
  Reproducibility from the bytes is preserved.
- **What the note says:** design.md:396 — `"config": { /* resolved GameConfig, tokens
  EXCLUDED */ }`. Tokens *are* excluded (`config.py:214-237`, asserted at
  `tests/test_replay.py:88`); the seed is not resolved.
- **Checklist item touched:** none.

---

## Traced and consistent

### T1 — CI green on `main` at the reviewed sha, with no test loosened *(checklist 1)*
- `gh run list -R Metta-AI/cogame-cogolf --branch main -w ci.yml` →
  run **32681786000**, `headSha a60233b8aad39e22890f3b3c31cde05dee3b7e79`,
  `status completed`, `conclusion success`.
  All three jobs green: `test`, `docker-smoke`, `wasm-viewer`.
- “No test loosened”: `git log --oneline --all -- tests/` returns exactly one commit,
  `c6eb4e2` (the initial game commit that *created* the suite). There is no prior test state
  to loosen; `git log -p --since=2026-08-24 -- tests/` shows no deleted assertion, no widened
  tolerance, no added `skip`/`xfail`, no removed test file.
- Locally: `pytest` → **406 passed, 3 skipped**; the 3 skips are `tests/test_viewer.py:387`
  (`viewer not built`), which CI converts to failures via `COGAME_REQUIRE_WASM_BUILD=1`
  (`ci.yml` “Viewer tests against the built bundle”; the CI log shows those tests running
  and passing).

### T2 — `num_agents` in every variant and the certification fixture; no `SEAT-COUNT FAIL` *(checklist 6)*
- `coworld_manifest_template.json:480` (`duel`), `:502` (`blitz`), `:530` (certification) —
  all `"num_agents": 2`, each with `len(players) == 2`, and
  `certification.players` has 2 entries (`:513-520`).
- `config_schema.num_agents` is `{"type":"integer","minimum":2,"maximum":2,"default":2}`
  (`:70-76`); `config.py:117-122` refuses any other value at startup (exit 2 via
  `server.py:830-832`).
- `tools/ci/docker_smoke.sh` is the coworld-builder template with **only** the three
  substitutions — `diff templates/tools/ci/docker_smoke.sh tools/ci/docker_smoke.sh` shows
  4 hunks, all `<slug>`/`<IMAGE>`/`<SEATS>` → `cogolf`/`cogame-cogolf`/`2`. The four seat
  invariants are intact at `:106-149`, each exiting non-zero with a `SEAT-COUNT FAIL:` prefix,
  and `SMOKE_SEATS` is the independent second declaration (`:54`, `:141-149`).
- `gh run view 32681786000 --log | grep -c "SEAT-COUNT FAIL"` → **0**.
  The docker-smoke log line reads:
  `smoke OK: seats=2 results=1032B replay=21166B reason=complete`.

### T3 — the resolution rules, all 11 numbered steps *(design.md §The game)*
1. **Draw and reveal** — `engine.py:289-296`: `spec = self.deck[self.spec_keys[hole-1]]`,
   `hole_start` emitted with `spec_key`, `title` (≤ 48) and `prompt_head` (≤ 160, newlines
   flattened). Draw at `engine.py:190-195`: `random.Random(self.seed).sample(sorted(keys),
   config.holes)` — matches the note verbatim, without replacement, over the sorted key list;
   `holes > len(deck)` raises (`:191-194`, and again at `server.py:826-829` for exit 2).
2. **Collect (one parallel batch)** — `engine.py:361-365` builds *both* payloads first, then
   `_batch` (`:397-419`) does `await asyncio.gather(*(ask(slot, payload) …))`. Every seat's
   observation is sent inside its own `ask` coroutine before any reply is awaited
   (`WsSeat.get_submission`, `server.py:239-254`, sends then waits).
   `tests/test_engine.py:44-56` proves it with timestamps (a 0.3 s slow seat; both sends
   land within 0.2 s).
3. **Retry once** — `engine.py:367-376`: only the slots whose `msg is None` are re-asked,
   with `retry=True` and `min(retry_deadline_seconds, wall_remaining)`; `replies.update(again)`.
   `tests/test_engine.py:60-73` asserts the send log is exactly `[False, True]`.
4. **Fallback** — `engine.py:380-394`: cause normalised into `FALLBACK_CAUSES`,
   `seat.fallbacks += 1`, `seat.fallback_causes[cause] += 1`,
   `message = literalist(spec, hole, cfg.max_tests_per_hole)`,
   `causes.append({"cause": cause, "baseline": "literalist"})`. No seat is ever removed:
   the loop is `for slot in range(cfg.num_seats)` unconditionally, and
   `tests/test_engine.py:70-72` asserts the fallback plays real tests.
5. **Sanitise** — `sanitize_submission` (`engine.py:109-130`): tests beyond `max_tests`
   dropped and counted (`dropped_tests`), `name`/`why`/`note` capped via `clean_text`,
   `impl` cleaned without a cap (it was already gated at 4000 in
   `validate_submission_message:96-97`).
6. **Load** — `sandbox_runner.py:147-156`: `exec(compile(source, "<submission>", "exec"))`
   then `callable(solve)`; any failure emits `{"id": -1, "kind": "broken", …}`, clipped to
   300 chars (`_clip`, `:121-123`). `BatchResult.get` (`sandbox.py:67-74`) turns every
   missing id into a `broken` result, so **a broken impl fails every shot and every par
   test** — exactly as the note says.
7. **Legality gate** — `engine.py:423-483`. Order of checks matches the note:
   `args` must be a `list` → `not_json`; `canon()` failure → `not_json`;
   `len(args) != arity` → `arity`; `compact(args)` > 400 or `compact(expect)` > 400 →
   `oversize`; then the reference batch: `result.kind == "timeout"` → `ref_timeout`, any
   other failure → `ref_error`, `not equal(result.value, expect)` → `ref_mismatch`, and
   finally `fingerprint(args) in seen` → `duplicate`. `seen.add` happens **only** after all
   prior checks pass (`:478-482`), so `duplicate` means “duplicate of an earlier *legal*
   test”, as the note specifies. The reference runs through the same runner with
   `cpu_seconds=2.0` (`sandbox.py:130-132`, `REFERENCE_CPU_SECONDS = 2.0`), and a reference
   that fails to load raises `SandboxError` → `harness_fault` (`engine.py:460-463`).
   `ILLEGAL_REASONS` in `contract.py:98-99` is exactly the note's seven-value set.
8. **Cross-fire** — `engine.py:485-538`. Only tests with `record["reason"] is None` become
   calls (`:493-496`), fired at the *other* seat's impl, in submission order (`test["idx"]`
   is the call id). `held` iff `result.ok and equal(result.value, expect)`; everything else
   — wrong value, raise, CPU timeout, `bad_value`, broken impl — is `breach` (`:534-535`).
   `observed` = `clean_text(describe(result), 300)` (`:536-537`); `describe`
   (`sandbox.py:171-182`) renders `"timed out"`, `"broken implementation: …"`,
   `"bad value: …"` or the JSON of the returned value.
9. **Par audit** — `engine.py:497-498` appends the four `PAR_TESTS` at
   `PAR_ID_BASE = 10_000` to the *same* batch as the incoming shots (one subprocess per
   defender per hole, as the note requires), and `:540-548` counts failures with the same
   pass/fail rule.
10. **Score + beats** — `engine.py:305-342`: `breaches[slot]` counted from `outcome ==
    "breach"`, `scoring.hole_score(breaches, par_fails)`, then `submission` × 2,
    `test_verdict` × N, `par_result` × 2, `hole_score` × 1 — in that order.
    `tests/test_engine.py:28-42` asserts the ordering and that the emitted kind set equals
    `contract.EVENT_KINDS`.
11. **Wall guard** — `engine.py:226-233`: `if self._wall_remaining() < cfg.hole_reserve_seconds:
    … reason = REASON_DEADLINE; break`, *before* `_play_hole`, so an unfinishable hole is
    never started and never half-scored. `tests/test_engine.py:76-89` asserts
    `len(holes) == result.holes_played` and `all(len(s.hole_scores) == holes_played)`.

### T4 — scoring, sign, zero-sum, killer test *(design.md §Scoring)*
- `scoring.py:24-30`: `delta = (breaches[0] + par_fails[1]) - (breaches[1] + par_fails[0])`,
  returns `[delta, -delta]` — antisymmetric by construction, so
  `hole_score[0][h] == -hole_score[1][h]` is not merely tested but structural.
- `tests/test_scoring.py:19-40` runs 1000 randomised outcome matrices asserting
  `score[0] == -score[1]`, `-9 <= score[0] <= 9`, `totals[0] + totals[1] == 0`,
  `-81 <= totals[0] <= 81`, and that `cumulative(...)[-1] == totals`.
- `killer_test` (`scoring.py:63-99`): winning seat's breaches only, key
  `(-swing, hole, idx)` → largest hole swing, tie-broken by earliest hole then lowest index;
  `None` for a draw (`:76-77`) or no breach (`:91-92`). Endcard renders
  `NO BREACH — DRAWN MATCH` for `null` (`replay_broadcast.html:1104`).
  Tie-break tests at `tests/test_scoring.py:63-92`.
- The results doc's `scores` is the per-seat scalar the league ranks by
  (`results.py:77`, `results.py:55-57` `score = sum(hole_scores)`), and the manifest's
  `results_schema.scores` documents “higher wins, `[0,0]` is a draw”
  (`coworld_manifest_template.json:203-213`).

### T5 — every wait is explicitly bounded; no unbounded loop or blocking read in the episode path
- `_await_connections`: `min(player_connect_timeout_seconds, max(0, wall_remaining))`
  (`engine.py:259-260`) → `WsSeat.wait_connected` uses `asyncio.wait_for` (`server.py:230-237`).
- `_space_holes`: `await asyncio.sleep(min(wait, gap))` (`engine.py:285`) — capped at the
  configured gap even if the clock jumped.
- Hole deadline / retry deadline: both `min`-clamped by `_wall_remaining()`
  (`engine.py:363-364`, `:372-373`); `WsSeat.get_submission` wraps the future in
  `asyncio.wait_for(fut, max(0.0, remaining))` (`server.py:249`).
- A source that raises is caught and becomes `host_error` (`engine.py:410-415`), never a
  crash — `tests/test_engine.py:92-102`.
- Sandbox: per-call `signal.setitimer(ITIMER_VIRTUAL, cpu_seconds)` (`sandbox_runner.py:161`),
  per-batch `subprocess.run(..., timeout=self.batch_seconds)` + `TimeoutExpired` capture
  (`sandbox.py:117-124`), missing ids become `timeout` (`sandbox.py:72-74`).
  `tests/test_sandbox.py:29-33` (infinite loop killed) and `:36-51` (partial NDJSON kept,
  missing ids time out).
- Engine hard stop: `wall_clock_budget_seconds` (`engine.py:222`, `:226`, `:241-245`).
- `_broadcast_done`: `asyncio.wait_for(..., DONE_SEND_TIMEOUT_SECONDS=3.0)` on every seat and
  every global socket, gathered with `return_exceptions=True` (`server.py:646-680`).
- Artifact writes: `uris.py:29-31` — 3 attempts, 30 s timeout each, bounded backoff.
- `runner.cleanup()` (`server.py:859`) is bounded by aiohttp's `shutdown_timeout` default of
  60 s (`aiohttp/web_runner.py:52`).
- The one `await asyncio.Event().wait()` (`server.py:807`) is **replay-serving mode**
  (`COGAME_LOAD_REPLAY_URI` set), which never runs in an episode pod.
- Player side: `_call_policy` is `asyncio.wait_for(asyncio.to_thread(policy.submission), …)`
  bounded by `deadline - 3 s` floored at 1 s (`client.py:415-444`, `:447-454`);
  connect timeout 20 s (`client.py:105`, `:363-366`); reconnect attempts capped at 5
  (`client.py:101`, `:343-356`); `COGAME_LLM_TIMEOUT` default 32 s
  (`llm_player.py:49`, `:233-234`) — inside the 40 s hole deadline and inside the 37 s
  policy deadline.

### T6 — degrade-never-hang table, row by row *(design.md:310-320)*
| note's failure | code |
|---|---|
| no reply by the deadline | `engine.py:367-376` retry, `:380-390` fallback, cause `timeout` (`server.py:251-252`) |
| non-JSON / wrong `type` / wrong `hole` / `impl` not a string | `engine.py:86-106` → `malformed`; wrong hole → `wrong_hole`, dropped and counted, hole keeps waiting (`server.py:273-280`, `tests/test_server.py:126-141`) |
| message > 16 KB or `impl` > 4000 | `server.py:503-505` → `oversize`; `engine.py:96-97` → `oversize` |
| seat never connects | `engine.py:263-272` logs and calls `on_never_connected`; `server.py:616-644` reports the lowest slot once to `COGAME_PLAYER_FAILURE_URI`; play continues (`tests/test_engine.py:105-120`) |
| LLM API errors / refuses / unparseable | `llm_player.py:361-379` → literalist, no wire noop |
| impl loops / allocates / imports blocked | `sandbox_runner.py:60-110` rlimits + audit hook; affected calls become breaches |
| sandbox subprocess dies mid-batch | `sandbox.py:122-124` keeps captured stdout; `sandbox.py:72-74` marks missing ids `timeout` |
| wall budget expires | `engine.py:226-233`, `:241-245` → `reason = "deadline"` on the last resolved hole |
- `done` before artifacts: `server.py:552-553`. Results and replay written independently with
  errors aggregated: `server.py:559-579`. 20 s grace then exit 0: `server.py:554`, `:581-588`,
  `:856-860`. `tests/test_server.py:144-159` asserts `SHUTDOWN_GRACE_SECONDS >= 20.0` and that
  `/healthz` + `/global` still answer after `done`.

### T7 — string truncation, cap table, rune boundaries *(checklist 9)*
- `clean_text` (`engine.py:57-67`) is the single sanitiser:
  `encode("utf-8","surrogatepass").decode("utf-8","replace")` → lone surrogates become
  `U+FFFD`; control characters stripped except `\n`/`\t`; `value[:limit-1] + "\u2026"` —
  **Python `str` slicing, so code-point (rune) boundaries by construction**.
- Cap table vs `contract.py:69-79` and the code:

  | field | note | contract | enforced |
  |---|---|---|---|
  | whole message | 16384 bytes → malformed | `MAX_MESSAGE_BYTES=16384` | `server.py:503-505` (byte length, `surrogatepass`) → `oversize` |
  | `impl` | 4000 chars, never truncated | `MAX_IMPL_CHARS=4000` | `engine.py:96-97` → `oversize`; `tests/test_submission.py:56-60` |
  | `tests` | 5, extras dropped | `MAX_TESTS_PER_HOLE=5` | `engine.py:111-114` + `dropped_tests`; `tests/test_submission.py:69-77` |
  | `name` | 40, truncated + `…` | `MAX_TEST_NAME_CHARS=40` | `engine.py:117-118` |
  | `why` | 120, truncated + `…` | `MAX_WHY_CHARS=120` | `engine.py:121-122` |
  | `args` | 400 → `illegal: oversize` | `MAX_ARGS_CHARS=400` | `engine.py:447-449` |
  | `expect` | 400 → `illegal: oversize` | `MAX_EXPECT_CHARS=400` | `engine.py:447-449` |
  | `note` | 200, truncated + `…` | `MAX_NOTE_CHARS=200` | `engine.py:128` |
  | `observed` | 300, rune-truncated | `MAX_OBSERVED_CHARS=300` | `engine.py:536-537` |
- Multi-byte-at-the-cap test: `tests/test_submission.py:80-97` puts a 4-byte emoji exactly on
  each cap and asserts the result is exactly `cap` code points and round-trips through
  strict UTF-8 and `json.dumps`/`loads`.
- `tests/test_replay.py:55-65` builds a whole replay from submissions containing a 4-byte
  ZWJ emoji, CJK, a lone surrogate and strings on every cap, then does
  `json.loads(blob.decode("utf-8"))` with **no error handler** on either side, and asserts
  `LONE_SURROGATE not in text` and `"\ufffd" in text`. That is the bullwhip byte-truncation
  bug, prevented and proven.
- Player side mirrors it: `client.py:159-163 _clip` is `str` slicing;
  `normalize_submission` (`:166-207`) caps `name`/`why`/`note`, drops tests past
  `max_tests`, and shrinks the message under `MAX_MESSAGE_BYTES` by popping tests
  (`:202-206`) — a terminating loop.

### T8 — the decision path (`players/`)
- Env switch: `players/main.py:28-42` — `PLAYER_SCRIPTED` first (an unknown name raises
  `UnknownBaseline` from `scripted.py:66-69` → `main()` returns **1**, `main.py:45-51`);
  else `PLAYER_PROMPT` or a detected provider → `LLMPolicy(strategy=prompt)`;
  else `literalist`. All four branches tested at `tests/test_players.py:31-64`.
- Provider detection (`llm_player.py:74-88`) covers
  `AWS_BEARER_TOKEN_BEDROCK` / `AWS_ENDPOINT_URL_BEDROCK_RUNTIME` / `ANTHROPIC_API_KEY`
  as the note lists, plus `USE_BEDROCK` and the AWS credential vars.
- Model candidates (`llm_player.py:40-43`) are haiku-4-5 then sonnet-4-5;
  `sonnet-4-6` is absent, asserted at `tests/test_players.py:198-201`.
  `MAX_TOKENS = 1800` (`:48`), `COGAME_LLM_TIMEOUT` default 32 s (`:49`).
- System preamble (`llm_player.py:58-71`) is the note's paragraph verbatim, including
  “REPLY FORMAT - your reply MUST BEGIN WITH `{`”; `PLAYER_PROMPT` is appended as
  “YOUR STRATEGY:” (`:294-297`).
- Three-path lenient parse (`llm_player.py:120-157`), in the note's order:
  (a) whole reply, (b) `balanced_span` (`:91-117`, string- and escape-aware, so braces inside
  string literals do not close the span — `tests/test_players.py:118-121`),
  (c) fenced ```` ```python ```` → `impl` + ```` ```json ```` → `tests`/`note`.
  Tested at `tests/test_players.py:88-115`.
- `api_docs` is sent as a `cache_control: ephemeral` system block with the
  retry-without-caching path kept (`llm_player.py:299-303`, `:350-358`).
- Prompt bounds: `MAX_PROMPT_CHARS = 6000`, `MAX_HISTORY_HOLES = 4`,
  `MAX_HISTORY_ENTRY_CHARS = 1200` (`llm_player.py:50-52`, applied at `:323-336`);
  `tests/test_players.py:184-196`.
- Exit codes: `run_policy_main` (`client.py:535-552`) returns 0 on `done`, 0 when the server
  goes away after the seat had connected (`client.py:358-361`, `:375`, `:384`), 1 on a fatal
  `PlayerError`, 130 on SIGINT. `tests/test_players.py:229-279` covers the `done` and
  dead-socket cases.

### T9 — the scripted baselines *(checklist 7)*
- `baseline.py` imports only `contract` and the stdlib (`:22`), so both the engine
  (`engine.py:37`) and `players/scripted.py:17` use the same module; the fallback move the
  engine synthesises is byte-identical to what `PLAYER_SCRIPTED=literalist` plays
  (`tests/test_players.py:69-77`).
- `literalist` = `LITERAL_IMPL` + `SAFE_TESTS[:max_tests]`, note “playing the text as
  written” (`baseline.py:73-81`); `pedant` = `NAIVE_IMPL` + `EDGE_TESTS[:max_tests]`, note
  “aiming at the edges” (`:84-90`); unknown key → `_stub` echoing the first example
  (`:45-65`).
- `tests/test_baselines.py` is the bounded-orders assertion the checklist names: for every
  one of the 12 specs × both baselines (24 param cases per test) it asserts the submission
  validates against the wire schema, `0 < len(impl) <= 4000`, `<= max_tests` tests, every
  `args`/`expect` inside its 400-char cap and JSON-representable, and no duplicate
  fingerprint within a hole; plus `test_every_literalist_shot_passes_the_reference_legality_gate`
  (`:67-77`) — every literalist shot is legal by construction.
- A full all-scripted episode to the natural end with `reason == "complete"`:
  `tests/test_e2e.py:34-53` (`doc["reason"] == "complete"`, `holes_played == 3`, zero-sum,
  both artifacts on disk, `replay["result"] == results`) and
  `tests/test_e2e.py:56-70` (a real contest: both seats breach, the pedant collects illegal
  shots, the audit bites, `fallbacks == [0, 0]`).
- **The checklist's “tuned with a grid harness, not guessed” clause has no target here:**
  the baselines carry no numeric parameters — they are `spec.LITERAL_IMPL`/`NAIVE_IMPL` and
  `spec.SAFE_TESTS`/`EDGE_TESTS`, fixed data in the deck. What plays the role of tuning is
  `tests/test_specs.py:100-143`, which asserts every spec's two impls diverge from the
  reference on **different** clauses (so scripted-vs-scripted is a real contest, not a null
  match) — and `tests/test_e2e.py:56-70` proves that end to end.

### T10 — the spec deck
- 12 modules, `DECK_VERSION = "core-1"`, registry at `specs/__init__.py:31-38`; the 12 keys
  are exactly the note's table. `tests/test_specs.py:36-43` asserts `len(DECK) == 12`,
  `DECK_VERSION == "core-1"`, `deck_keys("core") == sorted(DECK)` and that an unknown deck
  raises `DeckError`.
- Every module declares the note's full attribute set with the note's bounds
  (`TITLE ≤ 48`, `PROMPT ≤ 1200`, `AMBIGUITY ≤ 140`, `EXAMPLES` 2, `PAR_TESTS` 4,
  `SAFE_TESTS` 5, `EDGE_TESTS` 5) — `tests/test_specs.py:46-60`.
- The reference is stored as **source** and loaded from it (`specs/_util.py:13-19`,
  e.g. `range_merge.py:23-34`), so the in-process oracle and the copy the sandbox runs are
  byte-identical — the note's “exactly one execution path and one equality function”.
- `AMBIGUITY` never reaches a seat: `_spec_view` (`engine.py:569-579`) omits it and it is
  added only in `_hole_record` (`:661-662`, replay side).
  `tests/test_engine.py:152-166` asserts `REFERENCE_IMPL`, `AMBIGUITY` and the par tests are
  absent from an observation, and that no real player name is in it.

### T11 — `canon` / `equal`, the one equality rule
- `values.py:30-52` (`canon`) and `:55-69` (`equal`) implement the note's rule exactly:
  tuples → lists, `NaN`/`Infinity` rejected, numbers by value (`1 == 1.0`), **bools
  type-tagged so `True != 1`** (`:59-60`, checked before the numeric branch), dict key order
  irrelevant, strings by code point, depth capped at 12 (`:23`, `:32-33`).
  `fingerprint` (`:72-93`) is the type-tagged duplicate key.
  `tests/test_sandbox.py:110-126` covers every clause.
- The child imports the same module (`sandbox_runner.py:36`), so the value that crosses the
  boundary was canonicalised by the same code that compares it.

### T12 — the replay writer *(design.md §Replay document)*
- `replay.py:67-83` writes `format`, `version`, `game_version`, `protocol`, `config`
  (tokens excluded), `seed`, `deck`, `deck_version`, `names` (real), `aliases` (in-game),
  `holes`, `events`, `result` — self-sufficient, matching the note's JSON shape.
  `tests/test_replay.py:79-99` and `tests/test_e2e.py:44-53` assert it.
- `append_event` refuses any kind outside `contract.EVENT_KINDS` (`replay.py:61-65`);
  `append_hole` refuses a record missing any of `HOLE_KEYS` (`:55-59`).
  `Replay.parse` re-validates on read (`:96-127`).
  `tests/test_replay.py:112-118` and `:121-144` cover both.
- Event vocabulary: `contract.py:104-105` is exactly the note's six kinds with the note's
  fields (`engine.py:294-296`, `:328-332`, `:334-335`, `:337-340`, `:341-342`, `:249-250`),
  and `docs/REPLAY.md:61-66` documents the same table.
  `tests/test_replay.py:102-109` asserts at least one event of every kind appears in a real
  episode, and that `test_verdict.outcome` stays inside `SHOT_OUTCOMES` with at least one
  `breach`.
- Size: the CI smoke replay is 21166 B for 3 holes / 49 beats — 16.3 beats/hole, so a
  9-hole match is ~146 beats and ~65 KB, in line with the note's “≈130 events, ≈120 KB”.
- Partial write on `harness_fault`: `server.py:528-542` writes results *and* the replay and
  returns a `harness_fault` result, process exits 0.
  `tests/test_replay.py:147-157` proves a zero-hole replay still parses.

### T13 — the viewer executes, and both load markers *(checklist 13)*
- CI run **32681786000**, job `wasm-viewer`, `needs: docker-smoke` (`ci.yml:116`), step
  **“Load the bundle in a real browser”** ran and passed — no `continue-on-error` anywhere in
  `ci.yml`. Its output:
  ```
  {"loaded":true,"ms":307,"clock":"HOLE 1 / 3 MERGE RANGES",
   "scorebug":"COGOLF game GV01 MERGE RANGES — CORE/CORE-1 HOLE 1 / 3 MERGE RANGES
    THIS HOLE Ash SHOTS 5 BREACH 2 HELD 3 ILLEGAL 0 PAR ✗ 1/4
    #1 BASIL PEDANT +1 #2 ASH LITERALIST -1","feed_lines":4}
  soak: 12s of playback kept advancing ("beat 1 / 49" -> "beat 14 / 49" -> "beat 16 / 49")
  ```
  That is `loaded: true` from the real replay `docker-smoke` produced, and the readouts
  advanced across the soak.
- `data-replay-loaded` is set on the **first drawn frame**: `static_replay.js:143-148`
  (`message.type === 'firstFrame'` branch), and it was **removed** from the `loaded` branch
  (`static_replay.js:160-163` in the diff against the starter).
  `tests/test_viewer.py:138-150` asserts the marker appears exactly once and its index lies
  between the `firstFrame` and `loaded` branch indices.
- **Link flags and bootstrap are the matched pair, both from cogame-factorio.**
  `diff starters/cogame-factorio/replay-viewer/config.nims replay-viewer/config.nims` → a
  single hunk renaming `factorio_replay.js` → `cogolf_replay.js` and `_factorio_*` →
  `_cogolf_*`. No `MODULARIZE`, no `EXPORT_NAME` (`config.nims:24-37`).
  `client/static_replay_worker.js:265` is `Module.onRuntimeInitialized = function () {` and
  `:317` is `importScripts('./broadcast_core.js', './cogolf_replay.js')` — the
  non-modularized bootstrap. `diff` against the starter's worker shows **only** the
  `_factorio_*` → `_cogolf_*` renames and the file-name change. This is the cogame-lantern
  failure mode, and it is absent. `tests/test_viewer.py:153-168` and
  `viewer/build_viewer.sh:77-78` both guard it (`! grep -q 'EXPORT_NAME'`).

### T14 — chrome provenance *(checklist 14)*
- `diff /workspace/starters/cogame-factorio/client/chrome_common.js client/chrome_common.js`
  → **identical** (272 lines / 11815 bytes both sides).
- `diff … broadcast_core.js` → **identical** (1407 lines / 62123 bytes both sides).
  `tests/test_viewer.py:189-204` additionally asserts neither file mentions “cogolf”.
- `client/replay_broadcast.html` is 1396 lines / 102752 B against the starter's 1528 / 111234
  — **92 % of the starter's size**, i.e. a fork with deletions, not a rewrite. The unified
  diff is 1509 lines and every hunk is either a rename, one of the note's listed removals, or
  the appended cogolf block. Sections 1–5 of the starter's CSS above the banner (stage,
  scorebug, banner lane, kill feed, transport, scrubber + winner cap, endcard, locker-room
  curtain) are unmodified except the listed removals; the appended block starts at
  `client/replay_broadcast.html:339-343` with the required banner comment
  `cogolf additions to the inherited cogame-factorio chrome` followed by
  `<style id="cogolf-css">` (`:343`), and the two markup insertions carry the same banner at
  `:463` (inside `#stage`) and `:483` (inside `#plaque-r`).
- **Removals match the note's list exactly** (design.md:608-611):
  `#maptools`/`#tilepos`/`#zoom`/`#fit`/`#fitmap`/`#follow`, `#charmark`/`#charmark-lbl`,
  `#legend`/`#legend-cols`, the `f`/`g`/`c` bindings, `fitBase`/`fitMap`/`setFollow`/
  `focusCharacter`/`startCharGlide`/`renderLegend`, the `inventory` and `flows` plaque
  sections — and with them the whole zoom/pan/pinch/minimap wiring
  (`core.zoomAt`/`setZoom`/`panBy`/`panTo`/`resetView`, the wheel/gesture/pointer handlers,
  the dblclick refit). `grep -n 'viewpanel\|minimap\|zoomAt\|setZoom\|panBy\|panTo\|resetView'
  client/replay_broadcast.html` returns only two comment lines.
  `tests/test_viewer.py:224-235` and `viewer/build_viewer.sh:90-93` guard the removals.
  The starter (factorio) has no `#viewpanel` to begin with; the note justifies dropping the
  camera (design.md:612-614, fixed 40×22 arena), and `cogolf_replay.nim:34-38` confirms the
  board is a fixed `BoardW=1280 × BoardH=704` px.
- **Transport rules (a)–(d):**
  (a) `relayout()` (`replay_broadcast.html:1294-1300`) writes `--hud`, `--hudscale` and
  `--band` on `document.documentElement` — i.e. `:root`, which is where `--u`, `#endcard`
  and the rest read them — and is re-run from
  `new ResizeObserver(() => relayout()).observe($("transport"))` (`:1302`), on load (`:1301`)
  and from `boot()` (`:1375`).
  (b) `#scroll` (`:464`), `#feed` (`:465`), `#tooltip` (`:462`), `#status` (`:461`),
  `#loader` (`:474`), `#failcard` (`:473`) and `#endcard` (`:466`) all live inside `#stage`
  (`:459`, grid row 3); the transport is the page's own grid row 4. Nothing fixed-positioned
  sits in the band.
  (c) `#endcard{inset:0 0 var(--band) 0}` (`:409`), shown with the class its CSS rule uses
  (`#endcard.on`, from the starter's block), and **every** seek dismisses it —
  `selectBeat` (`:1187-1197`) calls `hideEndCard()` before anything else when
  `i !== n - 1`, and all of the scrub click, the scrub drag (`chrome_common.js:235-248`
  → `ctx.seek` → `selectBeat`), the back/forward/skip/end buttons (`:1211-1216`), the
  keyboard map (`:1220-1249`) and the beat buttons (`:776-782`) route through `selectBeat`.
  `tests/test_viewer.py:257-278` asserts all of this.
  (d) covered in N9 above.
- **Legibility at 360 px (checklist 11):** `.plate-name{flex:1 1 auto; min-width:3.2em}`
  (`replay_broadcast.html:416`), applied to the seat chip's name span
  (`who.className = "nm plate-name"`, `:837`); labels hidden under 640 px
  (`@media (max-width: 640px){ .ro .k, .wallsub, .scrub-key, #stepro .who, .seatchip .rk,
  .seatchip .sub{display:none} … }`, `:423-427`); the right plaque collapses to its tab under
  720 px (`:422`). `tests/test_viewer.py:281-290` pins the exact strings.

### T15 — both name spaces *(checklist 4)*
- Agents see aliases only: `contract.ALIASES = ("Ash", "Basil")` (`contract.py:32`), used in
  `welcome` (`server.py:379-380`) and in every observation (`engine.py:595-598`).
  `tests/test_engine.py:164-166` asserts no real name reaches a seat;
  `tests/test_server.py:79-80` asserts the same for `welcome`.
- The viewer maps aliases to real names: `seatAlias` / `seatName`
  (`replay_broadcast.html:686-687`), chips render the alias big and the real player name
  small underneath (`:849-853`), the endcard shows both (`:1081-1086`, `:1105-1113` for the
  killer test), and the result table heads with the alias and titles with the real name
  (`:1019-1022`).
  The CI viewer smoke's scorebug readout shows both: `#1 BASIL PEDANT +1 #2 ASH LITERALIST -1`.
- Both spaces are in the replay: `replay.py:78-79` (`names`, `aliases`) and
  `results.py:75-76`.

### T16 — the manifest, the release order and the scaffold *(checklist 10, 12)*
- `"replay_viewer": {"bundle": "static-replay-viewer"}` at
  `coworld_manifest_template.json:11-14`; `tools/build_replay_viewer.sh` present and mode
  `100755`; `tools/ci/docker_smoke.sh` present and mode `100755` (both confirmed by
  `git ls-files -s`) and CI asserts the exec bit before invoking each by path
  (`ci.yml:70-79`, `:129-138`).
- `coworld-release.yml` step order: `Build the Coworld manifest` (:153) → `Certify locally`
  (:167) → `Upload the policies` (:206, with the comment “BEFORE upload-coworld”) →
  `Upload the Coworld` (:304) → `Put the Coworld secret` (:342). Exactly the checklist's
  order. All three workflows are present.
- `tools/ci/policies.json`: four policies, two `PLAYER_PROMPT` champions
  (`cogolf-architect`, `cogolf-sniper`) and two `PLAYER_SCRIPTED` fillers; champion #2
  carries `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`; all four are one image,
  one entrypoint `/bin/cogolf-player`, env-switched, with the explicit
  `"image": "cogame-cogolf-player:latest"` the AGENTS.md note requires.
  `tests/test_manifest.py:123-142` pins it.
- The checklist's placeholder gate:
  ```
  grep -n '<slug>\|<IMAGE>\|<SEATS>' .github/workflows/ci.yml \
    .github/workflows/coworld-release.yml .github/workflows/coworld-submit.yml \
    tools/ci/docker_smoke.sh tools/ci/policies.json
  ```
  → **no matches, exit 0**. The only surviving angle-bracket names are the four expected
  runtime residues: `<cow_id>`/`<sha>` at `ci.yml:106`, `<run_id>` at
  `coworld-release.yml:21` and `coworld-submit.yml:17`, `<name>:vN` at
  `coworld-submit.yml:31`. `tests/test_manifest.py:145-152` runs the same gate.
- `tools/ci/viewer_smoke.mjs` is **byte-identical** to
  `coworld-builder/templates/tools/ci/viewer_smoke.mjs` (verified by `diff -q`).
- `episode_timeout_minutes: 20`, `game.runnable.type: "game"`, 4 tags,
  `variants[].description` on both variants, real JSON-Schema `config_schema` whose property
  set equals `config.KNOWN_KEYS` (`tests/test_manifest.py:41-48`),
  closed `results_schema` equal to `RESULT_KEYS` with the `reason` enum equal to `REASONS`
  (`:23-38`), and top-level `player[]` entries with `id`/`type`/`name`/`description`.
  `tests/test_manifest.py:158-166` runs `coworld.manifest.validate_upload_manifest` under
  coworld 0.1.42 and passes; `:169-177` validates both variants and the certification fixture
  against the `config_schema` with `jsonschema`.

### T17 — the fifteen tests the note lists
All fifteen exist and cover what the note says:
1 `tests/test_specs.py` (143 lines) · 2 `test_sandbox.py` (135) · 3 `test_scoring.py` (92) ·
4 `test_submission.py` (133) · 5 `test_engine.py` (189) · 6 `test_baselines.py` (149) ·
7 `test_results.py` (99) + `test_manifest.py` (191) · 8 `test_contract.py` (75) ·
9 `test_server.py` (186) · 10 `test_players.py` (279) · 11 `test_e2e.py` (97) ·
12 `test_replay.py` (157) · 13 `test_viewer.py` (434) · 14 the `docker-smoke` CI job ·
15 the `wasm-viewer` CI job. Plus `conftest.py` and `fakes.py`.
The one item on the note's list I could not find an assertion for is the checklist-2
re-derivation (see B2).

### T18 — the contract's four-surface rule
- `contract.py` has exactly one import, `__future__` (`tests/test_contract.py:24-32` parses
  the AST to prove it), and `tests/contract_manifest.txt` is a mechanically generated golden
  copy compared line-for-line (`test_contract.py:35-42`).
- `docs/PROTOCOL.md` is checked for every message type, every fallback cause and every
  illegal reason (`test_contract.py:52-61`), and `players/client.py` for the protocol string
  and every cap constant (`test_contract.py:64-71`).
- `players/client.py:69-97` prefers the server's `contract` module when importable and falls
  back to a local copy otherwise — so in the image (PYTHONPATH covers `server/`) the rename
  rule is enforced at runtime, and outside it the harness still runs.

### T19 — Dockerfile, compose, packaging
- Three stages exactly as the note describes: `wasm-builder` (emsdk 4.0.15 + nimby 0.1.27
  with a pinned sha256 + `nimby use 2.2.4` + `nimby --global sync nimby.lock` running
  `bash viewer/build_viewer.sh`), `player` (`python:3.11-slim` + aiohttp + anthropic + boto3
  + `players/` + `server/cogame_cogolf/`, `CMD ["/bin/cogolf-player"]`), and `game`
  (`python:3.11-slim` + aiohttp + `server/` + `players/` + `--from=wasm-builder
  viewer/dist/`, `CMD ["/bin/cogolf"]`).
- No Factorio/FLE inheritance anywhere: `grep -ri 'factorio\|/opt/factorio\|rcon\|fle'`
  over `server/` and `players/` returns nothing but the viewer-provenance comments.
  `viewer/assets/README.md` carries no Wube provenance (`tests/test_viewer.py:363-364`).
- The unprivileged uid the sandbox drops to exists in the image
  (`useradd --uid 4242 … cogolf`, `COGOLF_SANDBOX_UID=4242`) and
  `sandbox_runner.py:81-94` uses it only when the process starts as root.
- `compose.yaml` service names back the manifest placeholders
  (`tests/test_manifest.py:145-156`).

---

## Could not determine

- **Whether the two folds agree.** `client/replay_doc.js:132-177` (JS) and
  `replay-viewer/cogolf_replay.nim:304-337` (Nim) reduce the same event stream
  independently, and the Nim one additionally maps `breach` + `par_fails` onto a 9-brick
  fortress (`:322-333`). Nothing in the tree compares them or compares either to
  `holes[]`. The CI viewer smoke shows the *chrome* readouts are right for beat 1 and after
  a 12 s soak (`"SHOTS 5 BREACH 2 HELD 3 ILLEGAL 0 PAR ✗ 1/4"` matches the fixture's hole 1),
  which is evidence for the JS fold at two points but is not the frame-by-frame check.
  **What would settle it:** a test that, for each hole `k`, folds `events` to the hole's
  `hole_score` beat and asserts `stateAt(...).cumulative == holes[k].cumulative`,
  `stateAt(...).par == [holes[k].seats[i].par_fails]` and that the derived `shots[i]` match
  `holes[k].seats[i].tests` element-for-element.
- **Whether the sandbox's audit hook and rlimits hold under the production image's uid
  drop.** `tests/test_sandbox.py` runs the real subprocess but as the test user, never as
  root, so the `os.setgroups/setgid/setuid` branch (`sandbox_runner.py:81-94`) is not
  exercised anywhere in CI — `docker-smoke` runs a full episode in the image, but the
  scripted baselines' impls never attempt a blocked operation, so the deny path is untested
  in-container. **What would settle it:** a docker-smoke assertion (or a container-run test)
  that a submission attempting `import socket` comes back as an `error` breach while running
  as uid 4242.
- **The behaviour of `_shutdown_grace` under the platform's actual episode timeout.** The
  20 s sleep is unconditional and is not shortened when the engine has already burned most of
  the budget (`server.py:588`). I computed a worst-case process lifetime of ~714 s with local
  artifacts (N6) but could not observe it: the CI smoke episode finishes in ~30 s.
  **What would settle it:** a phase-60 episode log with `pacing: … wall=…s/700s` from a run
  that actually approached the wall guard.
- **Whether `coworld build`'s certification step exercises a *freshly built* binary.**
  `coworld-release.yml:153-165` runs `coworld build … --compose compose.yaml` and
  `:167-201` runs `coworld certify` in the same job, so the images certify are the ones just
  built — but the release workflow has no separate smoke step, so checklist 12's “any smoke
  step depends on a freshly built binary in the same run” has no target to check in
  `coworld-release.yml`. In `ci.yml` the equivalent holds: `docker-smoke` builds
  `${IMAGE}:ci` in its own job (`ci.yml:81`) before running the smoke, and `wasm-viewer`
  `needs: docker-smoke` and builds the bundle itself.
