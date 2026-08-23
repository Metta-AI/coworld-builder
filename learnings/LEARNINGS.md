# Learnings

**Append-only.** Every run adds exactly one dated section at the **bottom**, headed
`## <YYYY-MM-DD> <slug>`. Never edit or delete an existing section — a learning that later turns
out wrong gets a *new* entry that says so and names the section it corrects. Entries record only
what a future run would do differently: new gotchas, changed API shapes, starter advice, costs
paid. Do not restate the playbooks here.

When a learning is general, fold it into `playbooks/make-coworld.md` (Common mistakes) or
`playbooks/observatory-api.md` **in the same commit** as the entry, and say so in the entry.
Phase 80 writes the section; nothing else does.

---

## 2026-08-22 bullwhip (manual worked example)

The MIT Beer Game as a coworld, built by hand before this repo existed. Everything below cost real
time; all of it is now folded into the playbooks.

**Build / correctness**

- **Rebuild the binary before every smoke.** After editing game logic, a local/CI smoke that reuses
  the previously built binary silently exercises the old rules. A stale binary produced a genuine-
  looking bullwhip in the *scripted* baseline and took an hour to diagnose. Make the smoke job
  `needs:` the build job; never cache the binary across a logic change.
- **Truncate on RUNE boundaries, not bytes.** A byte-boundary cut on a `say`/`notes` string left
  invalid UTF-8 in the replay. Browsers rendered it fine; strict JSON parsers rejected it — so the
  bug only surfaced during verification. Every string that reaches the replay gets rune-safe
  truncation, and a test feeds multi-byte input at the cap.
- **Tune scripted baselines with a grid harness, and assert bounded orders in tests.** Hand-picked
  baseline parameters looked plausible and played badly. Sweep the parameters in CI, keep the
  config that plays the game well, and assert every order/action is inside its legal bounds so a
  regression is a test failure rather than a bad-looking replay.
- **Simultaneous-decision games: one parallel batch of LLM calls per turn.** Sequential per-seat
  calls blow the 720 s play budget (60 % of `episodeTimeoutSeconds`). In Nim that is
  `curly.makeRequests` with all seats' requests in one call.

**Manifest / viewer**

- `game.docs` must be
  `{"readme":{"type":"text","value":…},"pages":[{"id","title","content":{"type":"text","value":…}}]}`
  and `game.protocols` must carry **both** `player` and `global`. Anything else is rejected or
  silently produces a page with no docs.
- **The scorebug must survive 360 px.** The embedded featured-match iframe is ~360 px wide, not
  desktop width; player names collapsed to ellipses there while looking fine locally. Fix:
  `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` and hide labels under `640px`. Check at
  360 px, always.

**Release**

- **The first upload of a brand-new image may fail hosted certification with "completed without a
  replay URL"** even though results and replay are in S3 — the backend reconciler marks
  cold-pulling jobs completed before the pod is visible. Bump the version and re-upload; it passes
  the second time. Do not debug the game for this.
- **Ship small fixes as version bumps during the run** (0.1.1, 0.1.2) rather than batching them
  into one perfect release. Bumps are cheap and are the documented fix for two separate failures.

**League**

- **Set filler policies BEFORE the first `trigger-round`.** Two triggers issued before any filler
  existed failed instantly with `Temporal RoundWorkflow failed before settling the round`.

**Observatory API**

- `GET /episode-requests?division_id=…` returns **500**. `league_id=` and `coworld_name=` are
  accepted and then **silently ignored** — you get unrelated rows and believe them. Filter by
  `round_id=<round>` or `coworld_id=<cow>`.
- List key everywhere in that family is `entries`.
- Policy-version rows use `policy_name`, `policy_version_id`, `player_name`. The `name=` filter on
  `/policy-versions` is ignored — fetch and filter client-side.
- Rounds list shape:
  `{"entries":[{id, round_number, status, error, round_config.entrant_attributions[]}]}`. `error`
  is the only place the Temporal failure message appears.

**Process**

- **`cogame-babel` is the best template for the parley stack** — newer and cleaner than parley /
  cosino / focus. Bullwhip is a fork of babel 0.1.4 and inherited its conventions wholesale.
- **Announcements go to Discord, not Slack:** guild `1309708848730345493`, channel `#coworlds`
  `1440464430646427718`, via the Disco bot
  (`authorization: Bot $DISCORD_BOT_TOKEN`, `POST /api/v10/channels/<id>/messages {"content":…}`).

## 2026-08-22 lighthouse

- **Run a solvability oracle before pinning board constants in the design note.** Lighthouse's
  accepted note pinned 17×11 / farthest-dead-end keys / tidePeriod 4, under which 3 escapes were
  mathematically unreachable by any policy (min 47–93 ticks needed vs maxTicks ≤ 55). The check
  that catches it in minutes: min over key→runner assignments of max over runners of
  `dist(start, key) + dist(key, exit)` must be comfortably < maxTicks. Now recorded in the
  lighthouse note's §Tests item 4 as a precondition; designers should compute it in phase 10.
- **`coworld[auth]==0.1.38` cannot publish a static-replay-viewer coworld** — upload-coworld
  races the server's async bundle expansion and 400s "replay viewer bundle must be uploaded
  first". 0.1.42 adds the wait. Templates bumped to 0.1.42 this run; the playbook row that said
  "stale metta checkout" was corrected.
- **Sandbox git facts:** `gh` is NOT preinstalled (install the release tarball). `git push` works
  only through the stock `credential.helper=anthropic` (`/usr/local/bin/git-credential-anthropic`);
  GH_TOKEN cannot authenticate git-over-HTTPS (basic auth hides the placeholder from egress
  substitution), so sub-agents without the helper push via the Git Data API (blobs→tree→commit→
  PATCH ref; squashes each push to one commit). **Never run `gh auth setup-git`** — it overwrites
  the working helper globally and breaks every session sharing the container.
- **The league's first auto-scheduled round can fire before fillers are registered and fails**
  ("Temporal RoundWorkflow failed before settling the round"). Expected, does not count toward
  verification; register fillers immediately after the champion submits, then trigger.
- **`GET /leagues` returns a bare array**, not `{entries:…}` (playbook §2 updated). The
  softmax.com page is now client-rendered for the iframe; featured-match evidence comes from the
  SSR payload / `POST /coworlds/replays/session` (playbook §Featured match updated, incl. the
  manifest_hash-in-route and softmax-research.net-host facts).
- **Starter gap:** babel's `client/chrome.css` lacks the 360 px scorebug rules
  (`.plate-name {flex:1 1 auto; min-width:3.2em}` + label hiding under 640 px) that the pins
  require — take bullwhip's block verbatim, or fix babel upstream.
- **Message-delivery to sub-agent threads can arrive out of order / duplicated.** The builder
  acted correctly by re-asking instead of applying a stale instruction that contradicted a newer
  one; when steering a long-running sub-agent, timestamp decisions and name superseded messages.

## 2026-08-23 lantern

- **Manifest image placeholders come from compose service names.** `coworld build` maps
  `services.lantern` → `{{LANTERN_IMAGE}}` and hard-fails anything else; the design note's
  `{{GAME_IMAGE}}`/`{{PLAYER_IMAGE}}` were fiction. Generate the placeholder from `compose.yaml`
  (one source of truth) and assert it in the manifest test. (Playbook row added.)
- **Hosted certification's episode runner probes four HTTP contract routes before player pods
  start** — `/healthz`, `GET /client/player?slot=0&token=<t>`, a bad-token player websocket, and
  `GET /client/global` — and later **pings the `/global` websocket with a 2 s deadline after the
  pods start**. A fast scripted episode (~2 s) had already exited, so the ping hit a dead socket.
  Fix that generalises: after writing artifacts, keep `/healthz` + `/global` answering for a
  bounded `shutdownGraceSeconds` (20), then exit — the runner waits on process exit and the grace
  is free. (Two playbook rows added.)
- **Policy versions never dedupe across releases** (image digest changes) — every release mints
  v(N+1) for all names. Resolve UUIDs from `GET /policy-versions` client-side and take the vN of
  the successful release only. (Playbook row added.)
- **`git push` via the anthropic credential helper can die mid-session** (worked at 23:41Z, failed
  01:16Z with "Invalid username or token" while fetch kept working). A delta-only Git Data API
  pusher (`api_push_delta.py`: changed blobs → tree with `base_tree` → commit → PATCH ref,
  force:false, then local `fetch + reset` to adopt the remote sha) is much cheaper than the
  full-index variant for a big repo like coworld-builder, and preserves one-commit-per-finding on
  the remote. Rejected PATCH = lost race, same semantics as a rejected push.
- **Design-note physics needs a detection-feasibility check** (lighthouse's solvability oracle,
  restated for continuous games): with a triangle-sweeping beam crossing a 13 px body in ~7 ticks,
  `lockOnTicks = 12` could never accumulate — no find was possible by sweeping. The builder added
  a hold-on-contact aim reflex. Phase 10 should sanity-check every threshold that must be
  *reachable by the mechanics* (beam dwell vs body width/turn rate, pry time vs hunt length).
- **The design note's authored map JSON should be treated as a sketch, not an artifact**: the
  note's nook openings (108–167 px) could not be screened by one 48 px crate, and a sweep lane
  pinned a seeker against its pen wall. Committing a *generator* (`scripts/art/author_map.py`)
  that refuses to emit a map violating the invariants (symmetry, reachability, screenability)
  caught this in CI rather than in a dead replay.
- The scheduler fired round 1 between champion submission and filler registration → 1 failed round
  (known bullwhip/lighthouse pattern; round excluded from verification). Registering fillers
  before the first submit would avoid the noise, if the submission does not need the league to be
  non-empty.

## 2026-08-23 lantern (post-mortem: viewer deadlock shipped)

A separate, later entry for the same run: the lantern coworld **shipped a replay viewer that
never rendered**, and every gate this repo had went green over it. This is the correction.

**What happened.** `replay-viewer/config.nims` carried the babel starter's emscripten link flags
— `-s MODULARIZE=1 -s EXPORT_NAME=LanternReplayModule` — while `static_replay_worker.js` kept
paintbot's *non*-modularized bootstrap: `Module.onRuntimeInitialized = …;
importScripts('./lantern_replay.js')`. With `MODULARIZE=1` the generated JS defines a **factory**
and does nothing until it is called; `LanternReplayModule(Module)` was never called. Nothing
threw. Nothing logged. `data-replay-loaded` was never set and softmax.com sat on
"Loading replay…" forever. The shell of one starter had been spliced onto the build flags of
another.

**Why every gate passed.** *Nothing executed the viewer.* `ci.yml`'s `wasm-viewer` job asserted
that `index.html` existed and that some `.wasm` was non-empty. Phase 60 check 8 fetched every
asset the index named and asserted 200-with-non-trivial-size, then grepped `static_replay.js` for
`coworld-replay` and `tell("ready")`. All of that was **true of the broken bundle**: the files
were there, the bytes were there, the bridge code was there — it was simply never reached. A
presence check cannot distinguish "the code that would signal ready exists" from "the code that
would signal ready ran". Only opening the page can.

**The general lesson, worth more than the specific bug.** *A gate that asserts the existence of
the thing that would produce a signal is not a gate on the signal.* Wherever a check greps for
the source of a runtime behaviour, ask what a build that satisfies the grep and still does
nothing would look like — and then build the gate that catches it. Two artefacts from **the same
subsystem** copied from **different starters** is the recurring shape (link flags vs bootstrap;
also protocol version vs decoder, config schema vs reader): they are a matched pair, and nothing
in the type system says so.

**What changed (all in this commit's series).**
1. `templates/tools/ci/viewer_smoke.mjs` — Node + Playwright (pinned **1.55.0**, module and
   browser together) opens the bundle in headless chromium, serving it and the replay over local
   HTTP (never `file://`, whose fetch/wasm-streaming behaviour differs from the hosted route).
   Success is `data-replay-loaded="true"` on `<html>` **or** a `coworld-replay` postMessage
   `ready`; `data-replay-error`, a bridge `error`, or silence until the timeout all exit 1 with
   the last 30 console messages and the on-screen readouts. To catch the bridge from a top-level
   page it assigns `window.parent` in an init script — `parent` is `[Replaceable]` on `Window`,
   so the shell's `if (window.parent === window) return;` guard passes and its postMessage lands
   in Node. It also scrubs to 50 % and 100 % and records the clock at each, so a replay that
   renders one frame and freezes is a failure too.
2. `templates/ci.yml` — `wasm-viewer` now `needs: docker-smoke`, downloads the `smoke-replay`
   artifact, installs Playwright and runs the load test against the **real replay this repo's own
   episode just produced** (a hand-written fixture would drift). Evidence uploads as
   `viewer-smoke` (png + json) on success *and* failure. `docker_smoke.sh` gained
   `SMOKE_REPLAY_OUT` (default `dist/smoke/replay.json`) because its work dir is a mktemp the
   EXIT trap deleted seconds after validating the only replay CI ever made.
3. `.github/workflows/viewer-check.yml` (this repo) — `workflow_dispatch` with a `url` input, so
   the verifier can render the **live** iframe `src` even though its own sandbox has no browser.
   Writes the JSON and the readouts to the step summary, uploads `viewer-check`, fails on
   not-loaded.
4. `prompts/60-verify.md` check 8 / `docs/SPEC.md` item 8 / `agents/verifier.md` — the
   asset-presence procedure is **replaced** by: dispatch `viewer-check.yml` against the check-6
   iframe `src`, `gh run watch --exit-status`, download the artifact into
   `runs/<run>/viewer-check/`, paste the JSON line and the three clock readouts. Item 8 is TRUE
   only if `loaded: true` **and** the readouts differ. The spectator-judgment paragraph stays,
   now written from a screenshot that exists.
5. `prompts/30-review-loop.md` — acceptance checklist item **13, blocking**: the `wasm-viewer`
   job green *including* the smoke step (cited); `data-replay-loaded` / `data-replay-error` set
   by the shell; and the `config.nims` link flags and the worker/shell bootstrap read together
   and confirmed to come from the same starter.
6. `prompts/20-build.md` / `prompts/10-design.md` — the four viewer files (`config.nims`, the
   wasm entry `.nim`, `static_replay*.js`, `index.html`) come from **one** starter, named in the
   design note's `## Viewer` section, and the shell sets both data attributes.

**Cost.** A live coworld with a permanently blank theater, undetected through phases 30, 40 and
60, found only by a human opening the page.

## 2026-08-23 hive

**Run: idea → announced in ~4h10m, one review round, 8/8 DoD first try. What a future run should know:**

1. **The `coworld` 0.1.42 upload contract is stricter than what the sibling-starter manifests
   suggest.** Release dispatch 1 (0.1.0) died at "Build the Coworld manifest" with 6 pydantic
   errors. The shape that passes: `game.runnable.type: "game"` is required;
   `episode_timeout_minutes` is **top-level** (under `game` it is `extra_forbidden`); bundled
   players are **top-level `player[]`** (not `game.player`) each needing
   `id`/`type`/`name`/`description`; `variants[].description` is required; `game.config_schema`
   must be a **real JSON Schema document** (the CLI validates every variant and the cert fixture
   against it, injecting synthetic `tokens` — so `required: ["tokens"]` with a bounded
   string-array property); plus `$schema` and ≥3 `tags`. De-risk offline: `pip install
   coworld[auth]==0.1.42` and run its own `validate_upload_manifest` before dispatching.
2. **Put `ANTHROPIC_API_KEY_URI: secret://coworld/<slug>/anthropic_api_key` in the game
   runnable's `env` in the manifest** (bullwhip's shape). Without it the hosted game container
   never sees the coworld secret and every league episode silently plays scripted — it would
   surface only as phase-60 check-4 FALSE. Offline the URI doesn't resolve and the LLM client
   disables itself, so local certify/smoke still pass.
3. **A round can auto-create the moment the league is seeded/settings are set — before fillers
   and champion #2 exist — and it fails with `Temporal RoundWorkflow failed before settling the
   round`.** That failed round predates your trigger: record its error, don't count it against
   the two-failed-triggers budget, and verify your own trigger's round carries both champions in
   `round_config.entrant_attributions`.
4. **Observatory list endpoints disagree on shape** within one day: `GET /leagues` returned a
   bare array, `GET /rounds?league_id=` an `{entries,…}` object, `/divisions/<id>/leaderboard` a
   bare array. Always read with `if type=="array" then . else .entries end`.
5. **`git push` over HTTPS can be rejected sandbox-wide** (`remote: Invalid username or token`)
   while `gh api` works — the vault placeholder substitutes on gh/curl egress only. Push through
   the Git Data API (blobs → tree → commit → PATCH refs; `--input` a JSON body file for big/binary
   blobs — argv dies on a png). After each API push, realign with `git fetch` + `git reset`
   (mixed) + `git checkout -- <paths>`; a `reset --soft` leaves phantom staged deletions of files
   other parallel runs pushed, which a later session can commit as real deletions.
6. **Batched-swarm decision cadence works.** One LLM call per colony per 10 s turn (a 9-integer
   doctrine reparameterising a deterministic per-body kernel) gave 80 calls/episode for 96
   bodies, 0 fallbacks in the verified episode, and both champions visibly distinct (raider vs
   road-builder) on the leaderboard after 2 rounds. A per-ant interface would have been ~5000
   calls. Reusable pattern for any one-policy-many-bodies idea.
7. **Paintbot's viewer chrome really is 2–4-team ready** (`ensureScorebug()` two-plates-per-side)
   — a 4-seat game needs no scorebug rework, only the `.team-name min-width` + 640px media-query
   gotchas already in the playbook.

## 2026-08-23 raid

1. **Never let a sub-agent run `gh auth setup-git`.** It replaced the sandbox's working global
   helper (`/usr/local/bin/git-credential-anthropic`) and broke every subsequent `git push` —
   including to coworld-builder — with "Invalid username or token". Repair:
   `git config --global credential.helper /usr/local/bin/git-credential-anthropic`. Fixer/builder
   briefs now say so explicitly; keep saying it.
2. **Certification's `players-run` seats the whole manifest roster.** A cert fixture of
   `baseline × num_agents` fails `players_missing` if the manifest declares any other player
   entry. Design notes should stop pinning `baseline × N`; seat every declared player once and
   keep the strong baseline where the fixture's outcome is decided (raid: tank + healer).
3. **whisky/mummy shutdown race, latent in the bullwhip starter too:** player exits 1 when the
   game's `quit(0)` outruns the queued `done` frame (whisky raises on close/truncated frames).
   Player receive loops must `try/except CatchableError` → exit 0; `docker_smoke.sh` must assert
   **player** container exit codes, or CI passes what certification then fails intermittently.
   Fix cogame-bullwhip's player and the player template when next touched.
4. **Sidecar LLM budget is 30 req/min per episode with no wall-clock floor in sim-time pacing.**
   Fast episodes (2 LLM seats, ~2 s wall/turn ≈ 57 rpm) throttle intermittently; the fallback
   ladder candidate `us.anthropic.claude-sonnet-4-6` times out on every sidecar call and turns
   one throttle into a fallback cascade. Future designs: floor inter-batch wall spacing to keep
   ≤ 30 rpm at max living LLM seats; ship haiku-only ladders.
5. **Cooperative shared scoring never separates Elo** — both champions sit at 1000.0 forever
   (`results.scores = [score]×5`; round-robin has no head-to-head signal). Definition-of-done
   check 2 still passes (ranked = rows present), but a future cooperative design should say what
   the leaderboard is supposed to show, or pick a scoring rule with per-seat attribution.
6. Five release dispatches, five **distinct** defects (manifest placeholders → `/client/*` 404s →
   fixture seating → player exit race), each fixed on first try: the 3-dispatch budget reads best
   as "one failure surviving three fixes", not "three dispatches total" — authorize extra
   dispatches when every failure is new, diagnosed, and the fix is CI-verified first (cogball
   precedent, now raid).
7. `viewer_smoke.mjs` reports `feed_lines: 0` against a feed that visibly renders (selector
   mismatch with paintbot-descended shells) — harmless for the loaded/clock checks, but don't
   read feed_lines as evidence of an empty feed. And the paintbot-descended manifest prose calls
   the bundle "static **wasm**" even when the shipped viewer is pure-JS canvas — cosmetic,
   confuses reviewers; fix the prose when scaffolding.
8. Template fix landed this run: `templates/ci.yml`'s browser-load step no longer uses the
   pipefail-fatal `ls dist/smoke/*.replay … | head -1` glob (bare exit 2 when only `replay.json`
   exists); it is now a `for` loop. Repos scaffolded before 2026-08-23 carry the old form.

## 2026-08-23 cogball

1. **A cow_id is per-version.** Every release dispatch creates a *new* coworld row with its own
   id and manifest hash (cogball: 0.1.2 `cow_23c9b804`, 0.1.3 `cow_5d14a55f`, 0.1.4
   `cow_795268b0`, 0.1.5 `cow_ff38b98b`); only the newest is canonical and
   `game.canonical_coworld_id` auto-follows. Any post-league re-release therefore changes the
   cow_id: re-read it from `GET /v2/coworlds` and update STATE / VERIFY / announce copy — the
   old id is not an error, it is the platform's versioning.
2. **Two viewer defect classes that only *execution* catches, and the load test alone catches
   only one:** (a) a boot-time undefined global (`COG_BASE`) aborts the inline shell script —
   viewer never starts, `loaded:false`; (b) a mid-replay exception (`pushFeed` kept the
   starter's element signature while callers passed HTML strings) — viewer boots, sets
   `data-replay-loaded`, then freezes on tick 2 because `static_replay.js` latches `failed` and
   drops all later Worker messages. Scrub readouts *pass* on (b): seeking clears the feed queue
   and skips the killing frame. Guards now exist: `tools/ci/viewer_shell_check.cjs` in
   cogame-cogball (executes bundle page scripts in a DOM-less stub, fails on undefined
   identifiers / escaping exceptions) and `viewer_smoke.mjs --soak` (uninterrupted playback must
   keep advancing), folded into `templates/tools/ci/viewer_smoke.mjs` this run. Phase 20 should
   scaffold both and run soak in the wasm-viewer CI job.
3. **A dead builder session may have pushed unrecorded work.** Cogball's re-release builder
   found a predecessor session had already pushed the fix, found a second defect, and run two
   release dispatches — none in log.md/STATE. Audit the coworld repo's recent commits and
   Actions runs before re-dispatching a fix/release leg; a blind re-dispatch would have shipped
   a needless sixth version.
4. **Re-releases are league-safe and additive.** Policy labels auto-bump per release
   (v2→v3→v4); league submissions keep the version they were submitted with; rounds kept
   completing across two releases mid-league. The league fielding older labels than the newest
   release is expected — record it, do not "fix" it.
5. **Starter rule reaffirmed the hard way:** the moba→paintbot operator override cost one full
   design+build cycle. New physics/real-time games take paintbot (coworld-ctf); moba is only
   for bit-exact ports of an existing env. Already pinned in `playbooks/make-coworld.md`
   §Phase 0 and `prompts/10-design.md`.
6. `feed_lines: 0` seen again on a paintbot-descended shell (raid learning 7 stands): don't
   read it as an empty feed without the screenshot.
