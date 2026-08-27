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
  (`authorization: Bot $DISCORD_BOT_TOKEN`, `POST /api/v10/channels/<id>/messages
  {"content":…,"flags":4}`). `flags:4` = `SUPPRESS_EMBEDS`: announcements are plain text, no
  link-unfurl cards. An already-posted message loses its embeds with
  `PATCH …/messages/<id> {"flags":4}` (an edit, so it does not break the post-once rule).

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

## 2026-08-23 contagion

1. **`git push` over HTTPS can be rejected on a freshly created cogame repo** ("No anonymous
   write access"; `GH_TOKEN` basic-auth also fails at egress). The working route is the GitHub
   Git Data API via `gh api` — blobs → tree (with `base_tree` to preserve 100755 modes) →
   commit → `PATCH` ref with `force:false`, one API commit per local commit; seed a completely
   empty repo through the Contents API first (the Git Data API cannot create the first blob).
   Every later leg (fixer, release fixes) on that repo needs the same route — say so in briefs.
2. **Observatory list endpoints are shape-inconsistent:** `/leagues`, `/policy-versions`,
   `/divisions/<d>/leaderboard`, `/coworlds` return bare arrays; `/rounds` and
   `/episode-requests` return `.entries`. Use `(if type=="array" then . else .entries end)`
   everywhere instead of trusting a prompt's jq.
3. **Enabling ladder settings can auto-create round 1 before champions/fillers exist**; it fails
   with `Temporal RoundWorkflow failed before settling the round` even when fillers were
   registered before your own trigger. Harmless: the manual trigger's round completes. Phase 60
   must count completed rounds only after the fillers were set (it does) — expect a dead round 1.
4. **The coworld-builder working tree AND git index are shared across concurrent run sessions.**
   `git add -A` (or even a bare `git commit` after another session staged files) sweeps another
   run's files into your commit. Benign but confusing: always `git add` explicit paths under
   your own `runs/<run>/`, and expect foreign files to ride along anyway when the other session
   staged them mid-race.
5. **coworld 0.1.42 `certifier.validate_players_ran` requires EVERY declared `game.player`
   runnable to occupy at least one certification slot.** A cert fixture of baselines-only fails
   when a prompt player runnable is declared. Seat the prompt player in the fixture; with no
   credentials it plays its scripted fallback, so the fixture stays offline-safe.
6. **Design-note baseline thresholds are guesses until swept.** The r1 sweep harness
   (`tests/test_sweep.nim`: grid over threshold families × seeds, assert shipped constants are
   the argmax and interior) found 16 of 48 cells beating the note's numbers and retuning moved
   mean score 9114→11269. Scaffold the sweep as a test from day one; it also satisfies
   checklist item 7's "tuned with a grid harness, not guessed" without a separate leg.
7. **On wasm32 Nim `int` is 32-bit:** any sim whose intermediate arithmetic exceeds 2^31 (ppm
   chains easily reach ~1e12) must use `int64` fields or the browser re-derivation silently
   diverges from native. The design note's "all integers" needs the width said out loud.

## 2026-08-23 ecos

**Run: idea → announced in ~5h35m, two review rounds, 8/8 DoD first try, release/league/verify/announce all first-attempt. What a future run should know:**

1. **A design note's "measured" oracle table is a hypothesis, not a fact.** The accepted note claimed
   a 12/12 all-steward feasibility table; the builder's faithful implementation measured **0/12**
   (predators starve by gen 4–9). What saved the run was the note's own enforcement clause — "any
   change to a constant re-runs `tests/test_feasibility.nim`; that test is the enforcement, not this
   table" — which authorized a minimal constant repair (killBase 60→90 + three steward defaults,
   all inside declared ranges) without a design bounce. Designers: always include that clause.
   Builders: re-run the oracle before implementing around its numbers.
2. **Review fixes are where the next round's blockers come from.** Both r2 blocking findings (a 429
   handler leaving a zero-value doctrine tagged `source:llm`; the viewer's precompute missing the
   partial-generation flush a collapse needs) were introduced/exposed by r1 fix commits. A round-2
   delta review that enumerates every error path in each fix's neighbourhood is cheap and confirmed
   the judge's findings precisely.
3. **Sub-agent sandboxes can carry a Nim toolchain** (`/tmp/nim-2.2.4/bin/nim` in this run's fixer
   and judge sessions, absent in the reviewer's). Execution-verified verdicts — revert the fix hunk,
   watch the new test fail with the claimed numbers — are the strongest review evidence available;
   check for a toolchain instead of assuming CI-only.
4. **Git Data API 409s "Git Repository is empty" on a brand-new repo** — the first object must go
   through the Contents API (a bootstrap commit), then blobs→tree→commit→ref work. (Playbook row
   added.)
5. **Two paintbot-starter bugs every fork inherits:** `tools/build_replay_viewer.sh` exits 1 when run
   from `ci.yml` on a fresh checkout (it `cd`s into the not-yet-existing output parent; `coworld
   build` happens to pre-create it) — `mkdir -p` the parent first; and `#lockerroom` swallows
   transport clicks for its first ~1.5 s (`z-index:25` overlay) — give it `pointer-events: none`.
   (Playbook row added for the first; the second matters to any viewer smoke that clicks early.)
6. **The cert/smoke fixture must outlast the viewer soak gate.** A 3×30-tick fixture is 3.75 s of
   video; `viewer_smoke.mjs --soak 10` then reports a legitimately-finished replay as frozen. Size
   the fixture so the replay is longer than the soak window (ecos: 6×60 ticks = 15 s). (Playbook
   row added.)
7. **A sub-agent thread can die to "API temporarily overloaded".** The artifact file is the truth:
   no file → the leg did not happen → respawn a clean instance with the same brief. One judge
   thread was lost this way and the retry adjudicated normally.

## 2026-08-23 gridlock

1. **A league's variant is chosen at seed time or never cheaply again.** The phase-50 seed accepts
   `default_variant_id`; once rounds exist, changing it 409s with "requires a maintenance window:
   rounds paused + submissions locked". If a phase-20 rail decision picks a non-default league
   variant, carry it into the seed POST — a decision recorded "for phase 50" that phase 50's
   prompt body never mentions will be silently dropped on a resume by a session that didn't make
   it. (Here the drop turned out correct — scripted-baseline near-ties at default demand did NOT
   predict champion near-ties; flowwright beat backstreet 2-0 with a 61-point elo split — but it
   was luck, not process. Revising the decision with round evidence, logged at 70, was the fix.)
2. **A coordinator that dies blocked on a long sub-agent thread leaves code pushed and the report
   file unwritten** (r1 fixer: 17 commits on main, no r1-fixes.md). Recovery that worked: compare
   the repo against the reviewed sha to enumerate landed `fix(F<n>)` commits, then re-dispatch the
   leg as a *reconcile* brief — "these shas landed, verify each from `git show`, work only the
   remainder, write the report for all findings". No redo, one round, judge BLOCKING: 0.
3. **A fix commit that renames a test and appends its body reads as a deleted test** to checklist
   item 1's `git log -p -- tests/` scan. The fixer had to restore it as its own test (0decf32).
   Fixers: never fold an existing test into another; add alongside.
4. **`GET /divisions/<d>/leaderboard` returns `null` (not `[]`) while empty** — one more shape on
   top of the contagion bare-array row; treat null as "no rows yet" and re-poll.

## 2026-08-23 raid / hive / gridlock (operator review of the shipped viewers)

The operator opened the three newest viewers and sent back four things, all about the chrome the
builder claimed to have inherited verbatim. Folded into `prompts/10-design.md`,
`prompts/20-build.md` (builder brief), `prompts/30-review-loop.md` (new acceptance item **14**),
`prompts/60-verify.md` (spectator paragraph) and `playbooks/make-coworld.md` in this commit.

1. **"Chrome verbatim" was satisfied by ids alone.** cogame-gridlock's `client/replay_broadcast.html`
   was a 329-line page written from scratch that reused every starter id, so the id-presence test
   and the phase-30 judge passed it; the operator's first look: "looks like not all the elements
   were ported over." Raid and hive got it right (the starter page + an appended game block,
   `chrome_common.js` byte-identical). The fix is provenance, not presence: diff `chrome_common.js`
   against the starter, diff the page's CSS above the game banner against the starter's, and treat
   a page a fraction of the starter's size as a rewrite. Item 14 says exactly that.
2. **Zoom bar + minimap shipped on fixed arenas.** Raid, hive and gridlock all fit their whole board
   in the frame, so `#viewpanel` was dead weight the operator asked to remove from all three. Keep it
   only when the design note says the board is larger than the viewport; otherwise remove it
   (markup, CSS, wiring, the ids in the test list) rather than hide it.
3. **The score screen blocked the scrubber.** Three different bugs, one symptom: raid's
   `relayout()` never set `--band` (and set `--hudscale` on `#stage`, where `--u` on `:root` never
   sees it) so the plates and the card rode over the transport, and it showed the card with class
   `show` against a `#endcard.on` rule; hive dismissed the card only on restart, not on a scrub
   seek; gridlock's card was `inset: 0`. The rule now: `--band`/`--hudscale` on
   `document.documentElement`, nothing overlaid inside the band, `#endcard` stops at
   `bottom: var(--band, 0px)`, and every seek takes it down.
4. **Events under the scrubber must render and be clickable.** Raid collected `highlights` and
   toggled a `spoilers` button that drove nothing; hive's cache-spawn beats used a kind (`flag`)
   with no CSS and so were invisible, and all beats were inert `<div>`s. Beats are now labelled
   `<button>`s that seek (`markBeat(tick, kind, team, label)`), with a CSS rule per kind.

**Cost.** Three live coworlds re-fixed by hand in one sitting, and gridlock's viewer rebuilt from
the starter after the fact.

## 2026-08-23 tribunal

- **A wall-clock-driven outcome cannot be re-derived from game events — seed it from the recording.**
  Tribunal's `reason:"deadline"` is decided by the play-deadline clock, not by the rules, so
  `replayMatch` re-derived a ballot-phase deadline as `"complete"` (r1 blocking finding F1). Fix
  shape: pre-seed `sim.reason` from the recorded `end` event before replaying. Any coworld with a
  deadline/timeout ending has this class of bug; test the deadline in EVERY phase it can trip in
  (mid-argument re-derived fine; at-ballot did not).
- **Keep the starter's chrome element ids (`#scorebug`, `#feed`) even when restyling regions.**
  `viewer_smoke.mjs` and `viewer-check.yml` probe those generic selectors; tribunal renders both
  regions but named them differently, so the probes report `scorebug:"" feed_lines:0` and the
  judge has to fall back to the screenshot. Cosmetic, but it weakens the automated evidence.
- **`GET /leagues?limit=200` can return a bare array** (not `{entries:[…]}`); parse both shapes:
  `if type=="array" then . else .entries end`. Same defensive read works for `/rounds` and
  `/policy-versions`.
- **Bullwhip starter is now a proven two-for-two template for dialogue/role games** (escrow,
  tribunal): fork it for asymmetric-role, simultaneous-turn, LLM-prompt games; the fifth-seat art
  gap is closable with a committed HSV recolour of a starter sprite (`tools/make_violet_cog.py`).
- Zero-retry run end to end (design r1 accept, CI green on first push, release first dispatch,
  1 review round): total wall clock ~2.5 h. The templates + playbook pins are doing their job.

## 2026-08-23 escrow

- **Constrained-output (DSL) games: precompute the legal choice set in the observation.** Prompt-only
  legality drills cut champion fallbacks from 59% to only 31-41%; what took them to **0/32** was
  game-side: a `SIGNABLE NOW` list in the turn view whose membership is computed by the same
  predicate `validateMove` applies (list == legality), a precomputed `SPENDABLE THIS TURN` line,
  tolerant JSON extraction (first balanced object, trailing prose ignored), and pre-parse
  normalization of the structured field (drop junk before `OFFER`, prose after `ELSE`). If a game
  asks a model to emit a formal language, budget for one game-side remediation round in phase 60
  and design the observation to enumerate the legal moves from day one.
- **Policy uploads never dedupe on this deployment.** Every `coworld-release.yml` dispatch mints a
  new version for ALL policies — unchanged scripted fillers included (v1→v2→v3→v4 here). After any
  re-release: resubmit BOTH champions at the new labels and re-register fillers with the new UUIDs
  before triggering, or the ladder keeps playing the old versions.
- **Round 1 fails right after seeding — expected.** The seed+settings sequence auto-fires a round
  before champions/fillers exist; it dies with "Temporal RoundWorkflow failed before settling the
  round." Not a defect; the round triggered after fillers is what counts. Record it as excluded.
- **Sandbox `git push` over HTTPS can die mid-session** (auth rejected after working earlier in the
  same session; `gh api` keeps working). Reliable path: git-data API push — blobs → tree → commit →
  `PATCH refs/heads/main` with `force:false` (a rejected PATCH = lost race, same as a rejected
  push). Large/binary blobs must go via `--input <file>` (argv limit breaks `-f content=`).
- **Hosted episode logs are python `b'…'` reprs** under `===== container: <name> =====` headers —
  decode before grepping or counts are badly low.
- **Model routing is platform-side:** the game log announces `model=claude-sonnet-5` while the
  Bedrock sidecar routes `claude-haiku-4-5`. Write champion prompts for a small model.
- **Third parties can join your league mid-run** (two platform players joined Escrow ~40 min after
  seeding). Fillers then go unused (`insufficient_players` never triggers) and DoD item 2 still
  passes — champions ranked and fillers absent is the requirement, not "only our seats".

## 2026-08-23 eleusis

- **`game.config_schema` MUST keep `tokens` in `required`.** Matriculation rejects the manifest
  otherwise (`manifest_invalid: "game.config_schema must require tokens"`), even though no stored
  fixture carries `tokens` — the commissioner injects it at episode time. A review round "fixed"
  variants-don't-validate by dropping it from `required`; the correct shape is `required:
  ["tokens","players"]` with any schema-preflight in docker_smoke skipping the injected key.
- **Git Data API pushes silently drop exec bits.** Tree entries default to mode `100644`; a
  replayed commit turned `tools/ci/docker_smoke.sh` non-executable and CI's `test -x` gate went
  red. When pushing via blobs→tree→commit, set `"mode":"100755"` explicitly on every script.
- **Observatory list endpoints disagree on envelope per route** on this deployment: `GET /leagues`
  and `GET /policy-versions` return bare arrays; `GET /rounds?league_id=` returns `{entries:[…]}`.
  Write jq that handles both (`if type=="array" then . else .entries end`).
- **The static viewer's bridge `ready` can beat the first drawn frame** (bullwhip-lineage
  `static_replay.js` fires `tell("ready")` from `start()`, ~2 rAFs after `attachReplay`, before
  sprites load). On a cold runner `viewer-check.yml` sampled a blank shell with three identical
  clocks — a false FAIL cured by re-dispatching. Fix candidate for the starter/template: emit
  `ready` only after `data-replay-loaded="true"` is set. Until then: treat one blank viewer-check
  as retryable, not as check-8 FALSE.
- **Bullwhip lineage has no `chrome_common.js` / `replay_broadcast.html`** — the checklist's
  provenance items map to `client/chrome.css` (byte-for-byte + appended block) and
  `client/replay.html` (starter page + appended block). Say the mapping explicitly in the design
  note so reviewer/judge don't file phantom missing-file findings.

## 2026-08-23 rumor

- **A coordinator death does not kill its sub-agents: check the phase's exit criterion before
  re-dispatching.** The claiming session died right after dispatching the phase-20 builder; the
  builder kept running and delivered green CI on its own. The resume verified the phase-20 exit
  checks against the repo (CI run id, workflow parse, placeholder gate) and transitioned — no
  second build round burned. Make "is this phase already done?" the first step of any resume into
  20/30/40.
- **Never let an API-push helper touch paths it was not given.** A helper that (a) created blobs
  for files that did not exist yet (base64 of a missing file inside `$( )` produced an EMPTY blob,
  exit 0) and then (b) `git reset --hard origin/main` materialized those empty tracked files OVER
  the verifier's just-written untracked VERIFY.md/viewer-check/ep.replay. Guards that fixed it:
  refuse to push a path that does not exist; replace `reset --hard` with `reset --soft` +
  `checkout -- <only the pushed paths>`; and don't `git add -A` a run directory while a sub-agent
  may still be writing into it. Recovery that worked: viewer-check re-downloaded from its run id,
  replay re-fetched from S3 (both byte-identical), VERIFY.md rewritten by the verifier from its
  own transcript with a provenance note — the judge then re-fetched every re-fetchable claim and
  ratified 8/8.
- **`wc -c` your Discord announcement against 1800 before posting** — the first rumor draft ran
  1868 chars; cutting the replay paragraph (per the template's own cut order) landed 1730.

## 2026-08-24 ledger

- **`GET /leagues` returns a plain JSON array, not `{entries:[…]}`** — the jq in
  `prompts/50-league.md` step 2 (`.entries[]`) fails with "Cannot index array with string".
  Use `jq 'if type=="array" then .[] else .entries[] end'` (the rest of phase 50's endpoints
  — `/rounds`, `/policy-versions` — did return `entries` wrappers).
- **Champion submission auto-schedules a round immediately; fillers registered after it are too
  late for that round.** Ledger's round 1 was created at champion-submit time (23:37Z), failed
  with `Temporal RoundWorkflow failed before settling the round.`, and was superseded by the
  post-filler manual trigger. Harmless, but noisy: register fillers (step 7) between the release
  and the champion submits if you want a clean rounds table — the filler UUIDs exist as soon as
  phase 40's upload-policy finishes.
- **`viewer_smoke.mjs` can false-negative a healthy viewer**: its wait loop breaks on the
  `coworld-replay` bridge `ready` OR `data-replay-loaded`, whichever fires first; if `ready`
  fires before the shell hydrates, the scrub clicks land on an unpopulated `#scrub` and the
  three clock readouts come back identical (ledger viewer-check attempt 1, run 32675392403;
  attempt 2 on the identical URL passed). Fix candidates: gate scrubbing on
  `data-replay-loaded="true"`, and/or expose `--soak` as a `viewer-check.yml` input. Also worth
  adding `--soak 15` to `templates/ci.yml`'s load step (ledger's ci.yml added it locally).
- **`git push` over HTTPS can 401 from the sandbox on a fresh coworld repo** while `gh api`
  has `admin:true,push:true` — push via the Git Data API (blobs → tree → commit → PATCH ref,
  `force:false`), as `playbooks/make-coworld.md` documents for ecos. When scripting it, push
  `origin/main..HEAD` only: replaying `rev-list HEAD` re-pushes already-landed commits as
  empty-diff duplicates (ledger main carries 6 of them; cosmetic, but permanent).
- **Designers: don't write global distributional claims the schedule can't guarantee.** The
  ledger note claimed per-seat first-mover counts "differ by at most 1", which is unsatisfiable
  when the asymmetric-subgame draw is per-pairing (measured: violated in 58% of 40k seeded
  episodes) — and a payoff "landmark" (`s=6,p=50 → 6/6`) that its own formula contradicts.
  Both cost a review round to repair. Landmarks and invariants in a note should be derivable
  from its own tables; anything statistical should be stated as the greedy/structural invariant
  actually enforced.

## 2026-08-23 bullwhip starter family (bedrock model vs config.model)

- **On hosted Bedrock the `model` config field is ignored BY DESIGN — do not re-flag the
  mismatch.** In the bullwhip-lineage `llm.nim`, `bedrockModelIds()` supplies its own
  haiku-first candidate list (`us.anthropic.claude-haiku-4-5-…` leads because hosted Bedrock
  capacity is shared account-wide); `config.model` (default `claude-sonnet-5`) applies only to
  the direct-Anthropic transport (`ANTHROPIC_API_KEY`), and `BEDROCK_MODEL` pins a single
  Bedrock id. Escrow's verifier flagged the startup banner `model=<config.model>` as a
  mismatch on rounds 8/9 of `league_cc074076-…`; the real bug was the LOG, not the routing.
  Fixed family-wide 2026-08-23 (bullwhip/escrow/tribunal/rumor/eleusis PR #1 each):
  `newLlmClient` logs the Bedrock model actually invoked, the entrypoint banner no longer
  prints `model=`, and the manifest template's `model` description states the
  direct-Anthropic-only scope. Forks cut from the starter BEFORE this fix still print the
  misleading banner — verify phases should check which lineage they're reading, and new games
  should copy the post-fix wording.

## 2026-08-23 tandem

- **Matriculate rejects `game.config_schema` array properties without `minItems`/`maxItems`.**
  0.1.0 failed cert with `manifest_invalid: game.config_schema.properties.tokens must declare
  minItems and maxItems` — `required: [tokens]` (the escrow learning) is not enough; bound every
  array property (tandem: `minItems: 2, maxItems: 2` matching num_agents). Fixed in
  `tools/build_manifest.py`, bumped to 0.1.1, passed.
- **The chrome alias block can shadow game-block functions silently.** paintbot-lineage pages
  open with `var markBeat = C.markBeat, …` aliases; a game-block `function markBeat(…)` in the
  same IIFE is rebound at alias-assignment time (hoisting), so the labelled-button builder was
  dead code while every static grep passed — beats rendered as chrome_common's unlabeled divs and
  never seeked. Caught only by a fresh-context judge executing the page. Fix: rename the
  game-block builder (`markTandemBeat`); prevention: a scope-duplication test asserting the alias
  list shares no name with any top-level `function`/`var` below the banner
  (`tests/test_viewer.nim` `noAliasIsShadowed`, fails on the pre-fix page).
- **A round can settle `completed` with no episode at all**: `results: []`, episode request
  `completed` with `episode_id: null`, `replay_url: null`, artifacts 404, ~11 s after creation
  (round 3). It does not count toward the ≥2-completed check and does not increment leaderboard
  `rounds_played` — verify on `rounds_played` and on rounds that carry results, and record the
  empty round rather than excusing it.
- **A champion seat can silently play scripted in a scored round.** Round 2's replay carried only
  one `register`; champion #2 connected but its register never arrived, so the server degraded
  the seat to the scripted fallback for the whole episode (by design). Intermittent — round 4 was
  50/50 LLM. Phase-60 verifiers should count `register` records and per-seat `source:"llm"`
  orders in the fetched replay, not trust the roster.
- **Design-pinned integer physics needs quantisation-floor checks before building.** The note's
  pinned `Δspin = τ·28294/(I·100000)` truncated to zero below 491 N·m and `headingQ += spin div 4`
  discarded slow turns entirely — the couch could not turn slowly or stop spinning. Builder added
  fine-resolution carries (1/256-step spin, substep heading remainder) inside gameHash. When a
  note pins integer formulas, sanity-check the smallest meaningful input produces a nonzero step.
- **Name /tmp evidence files per round.** The verifier pasted round 2's hexdump under round 4's
  commands because both landed at `/tmp/ep.replay`-style paths; the judge caught the provenance
  slip by byte-comparing live objects. Use `/tmp/<round-id>.replay`.
- The 20-build brief should say explicitly when the design note pins existing art (ctf rigs +
  pixie bakes): the builder correctly skipped nano-banana but had to justify it as a deviation.

## 2026-08-23 firm

- **`git push` to github.com can 401 while `gh api` works** (this session, all of it). The egress
  proxy substituted the token for API calls but not for git-receive-pack basic auth. Fix that
  needs no human: push through the Git Data API (blob → tree with `base_tree` → commit → PATCH
  `refs/heads/main` with `force=false`). Two gotchas: pass blob content via `--input <json-file>`
  (a base64 PNG blows the argv limit), and verify the API tree sha equals `git rev-parse
  main^{tree}` before PATCHing — that proves content parity. A sub-agent running
  `gh auth setup-git` mid-run is a suspect (it rewrote credential.helper in ~/.gitconfig);
  unproven, but check the timeline before blaming the platform.
- **On resuming a run that died right after "dispatch builder"**: check the coworld repo before
  re-dispatching — the sub-agent may have finished after the coordinator died. Firm's builder had
  pushed everything and CI was green; the resume only had to verify phase-20 exit criteria.
- **Observatory API shapes**: `GET /leagues` returns a bare array (not `.entries`);
  `GET /policy-versions` likewise; `GET /rounds` returns `{entries:[…]}`. The 50-league prompt's
  jq for `/leagues` needs the bare-array form.
- **A "tuned with a grid harness" checklist item is cheapest satisfied at build time.** The firm
  reviewer's only blocking finding was hard-coded baseline constants; the fix (a CI-run sweep
  asserting the shipped constants are the argmax) is a shape any 20-build brief could demand up
  front: sweep + committed record + assert.
- **Atlas extra_cities across several regions**: append each pick to your local `places.mjs`
  copy and re-run `atlas_spot.py` before picking the next, or two same-continent dots collide
  (the tool only sees committed cities — ledger landed 22.9 from firm only because the local
  copy was updated between picks).
- **Generic viewer probes under-read game-specific chrome**: firm's `#scorebug` populates after
  first paint and its feed lives behind a « LOG button, so `scorebug:""`/`feed_lines:0` were
  correct-but-alarming readouts. Judge from the screenshot + clock motion; file probe gaps as
  legibility notes, not failures.

## 2026-08-24 cogolf

- **Player-side-LLM policies (factorio lineage) MUST carry `USE_BEDROCK: "true"` in their
  `env` in `tools/ci/policies.json`.** The platform gates the player pod's Bedrock sidecar on
  `resolve_player_bedrock(policy_secret_env)` (`coworld/runner/bedrock_enablement.py` in the
  installed CLI): `PLAYER_PROMPT` alone provisions no sidecar, the container has no provider,
  and the seat silently plays the scripted fallback — 18/18 scripted submissions in every league
  episode, invisible to `results.fallbacks` (the substitution is client-side and wire-valid) and
  to the hosted log grep (player stderr is not in the log bundle). Surfaced only at phase-60
  check 4 by byte-comparing champion `impl`s against the specs' baseline sources. Game-side-LLM
  lineages (babel/bullwhip/ctf: the GAME container calls the LLM) never hit this — their fix is
  the manifest `ANTHROPIC_API_KEY_URI` (hive 2026-08-23). Fix: add the env pair, bump, re-release,
  re-submit champions. Folded into make-coworld's Common-mistakes table.
- **Champion re-submission placement is asynchronous.** A round triggered ~20 s after
  `coworld-submit` returned `ok:true` seated the OLD policy version for that champion
  (round 5: architect:v3 + sniper:v2). Wait for `entrant_attributions` to show the new
  `policy_version_id` before judging a round, and verify check 4 only on rounds whose entrants
  are all the intended versions.
- **Bedrock sidecar cold start makes hole/turn 1 fall back client-side on both seats** (submissions
  byte-identical to the scripted baseline on the first decision only, 2/18, never later; the
  sidecar's `bedrock_sidecar_started` logs the same second the seats connect). Non-blocking if a
  small minority, but: warm the LLM client at `welcome`, and record a client-side fallback flag in
  the submission event so replays can count it — `results.fallbacks` only counts server-side causes.
- **External players can join a public league mid-run** (two joined cogolf between verify rounds 6
  and 7 and now hold ranks 1–2, demoting both champions). SPEC item 2 requires champions *ranked*,
  not top-ranked; also round-robin rounds grow (4 entrants = 6 episodes), so "latest round's
  episode request" needs the champion-vs-champion episode picked out, not `.entries[0]`.
- **The design-note sandbox launch line `python -I -S -m pkg.mod` is impossible**: `-I` implies
  `-E`, so `PYTHONPATH` is ignored and `-m` cannot resolve the module. Launch the runner by
  absolute file path and re-insert the server dir on `sys.path` in the child.
- The atlas build can be blocked by OTHER runs' shipped-but-unplaced leagues (cogmud, firm here);
  `extra_cities` placing them for their owners is the designed fix and costs one extra dispatch.

## 2026-08-24 cogmud

- **Nim `parseJson` rejects trailing prose ("EOF expected") — parse the first balanced JSON
  object instead.** An LLM reply that is a complete, valid JSON object followed by one sentence
  of prose fails bullwhip-lineage strict parsing, burns the one retry, and falls to scripted.
  Cost here: 1 of 84 champion decisions across three verified rounds — and one FALSE check-5
  verdict (the `falling back` line in the hosted log) that took a round re-pin to clear. Future
  players: extract the first balanced `{…}` / strip a ```json fence before `parseJson`.
- **Verify against the newest completed round when an older one carries a local blemish** —
  `prompts/60-verify.md` §Retry budget's "different round" is exactly for this; keep the
  superseded evidence as an appendix so the judge can see nothing was excused.
- **The viewer's `policyNames` swap must be applied at every render site.** Cogmud's clock
  rendered seat 3 as `BASELINE (2)` while the endcard/scorebug/beats rendered aliases — same
  seat, two names, one frame. Grep every place a name is drawn (clock, scorebug, endcard, beat
  labels, chronicle) for the alias→policyName map; a single miss confuses spectators.
- **`tools/ci/docker_smoke.sh` should assert every player container's exit code**, not just the
  game's — the template still doesn't; cogmud added a bounded wait + `docker inspect` per player
  slot and printed `all 6 player containers exited 0`. Catches the whisky/mummy shutdown race
  (raid 0.1.3) in CI instead of intermittently in hosted certification.
- **Atlas: pick the spot from the pending PR's branch geometry, not main's.** Firm's PR 20252
  was queued unmerged, so main's `places.mjs` lacked six cities; `atlas_spot.py` on main would
  have put cogmud on firm's exact dot (425,553). Fetching `places.mjs?ref=atlas/<branch>` gave a
  spot clear of the in-flight cluster. The `unplaced leagues` failure then names only what is
  still missing at build time (cogolf, firm) — carry those in `extra_cities` with the
  coordinates their own run already computed (their `log.md` has them), don't re-derive.
- **Outside players can join a live league mid-run** (round 4 seated `relh` and `richard`
  between trigger and verify). Check-3 participant assertions should require the champions to be
  present and non-filler — not that the seat list equals champions+fillers.

## 2026-08-24 cogchemists
- **Sub-agent spawns can die instantly to "API temporarily overloaded"** — two builder threads
  in a row failed within a minute of dispatch, before writing anything. Check the repo/working
  tree for what actually landed, log it as an infra failure (not a red-CI round), back off
  ~2 minutes, and re-dispatch the identical brief. Third attempt built the whole game.
- **`release-result.json.hosted_certification` is a snapshot at upload time ("certifying"), not
  an outcome.** The 0.1.0 release ran green while the backend cert job had already failed
  (platform-side 404 on `POST /v2/episode-requests` at smoke-episode). Poll
  `GET /v2/coworlds/<cow_id>/certification` after the run before accepting; on a platform-side
  failure the fix is the documented one — bump the version and re-dispatch, no code change.
- **A freshly created `Metta-AI/cogame-<slug>` repo may not be covered by the sandbox git
  credential helper** ("No anonymous write access" on push, while pushes to coworld-builder work).
  Push via the Git Data API with `gh` (Contents API for the first object, then blobs → tree →
  commit → ref). Expect every later phase touching that repo to need the same path.
- **Deduction-game grids can be exact, but baseline *guarantees* must not be sampled.** The
  fixer round caught `alwaysExposes`/`certainPotion` certifying over a truncated 3000-sample of
  40 320 chemistries: rank by samples if you like, but any "guaranteed safe/exposing" predicate
  must refuse to certify on a truncated enumeration.
- **Recording the per-seat scripted-fallback flag needs to come from the decision path itself**
  (a `fromScript` seq returned by `decideAll`), not recomputed from pre-batch knowledge in the
  server — otherwise a credentialed episode's fallbacks are invisible to phase 60's census. The
  offline smoke can't catch it (everything is scripted there); test it with a live client pointed
  at a refused port.
- **Atlas `extra_cities` for leagues whose own PRs are queued: reuse their coordinates** (their
  run logs / PR branches have them) so the queue's rebases collapse to identical lines; compute
  fresh spots only for leagues with no PR yet, and hand-check those against dots pending in open
  PRs (chorus/garble vs rumor@459,808), since `atlas_spot.py` on main can't see them.

## 2026-08-24 garble

- **`game.protocols.player` and `.global` must be `{"type":"text","value":…}` objects, not bare
  strings.** The platform's upload-manifest pydantic validator rejects strings ("2 validation
  errors for Coworld Manifest") even though repo CI and docker-smoke pass; `game.docs.readme`
  had the same rule already. Cost one release dispatch (v0.1.0). Folded into the make-coworld
  Common-mistakes table.
- **The git-credential outage can cover ALL of github.com, including coworld-builder itself** —
  earlier note said fresh `cogame-<slug>` repos; today `git push` to coworld-builder began
  failing mid-session too while `gh api` kept working. Replay commits via Git Data API
  (blobs → trees → commits → PATCH ref, delete = tree entry `"sha": null`), verify
  `git diff HEAD origin/main` is empty after, then reset local to origin/main. Never chain the
  reset unconditionally after the push script — a newline-separated `git checkout -B` after a
  failed push discards the unpushed commit (recovered from log copy this run).
- **A league's first round can be a hollow completion**: `status:"completed"` seconds after
  creation with `replay_url:null`, empty scores, artifact 404s. It still counts in
  `GET /rounds` filters. Rest phase-60 item 1 on *scored* rounds and disclose the hollow one;
  the judge accepted exactly that framing.
- **Sub-agent threads can die to platform API overload without writing anything.** Two builder
  threads died back-to-back mid-phase-20; the uncommitted working tree survived in the shared
  filesystem. Brief builders to push a first coherent commit early, and on re-dispatch point
  them at the leftover tree rather than restarting.
- **Complete Asana phase subtasks by name, not by remembered gid order** — an off-by-one in the
  gid list marked 50–80 complete one phase early each and left 40 open; harmless here but only
  because every later phase succeeded. `GET /tasks/<run>/subtasks?opt_fields=name,completed`
  first, then PUT the gid whose name matches the phase.

## 2026-08-24 chorus
- **A bridge `ready` fired before the first drawn frame is invisible to the template smoke.**
  `tools/ci/viewer_smoke.mjs:365-366` accepts `data-replay-loaded` and the `coworld-replay`
  bridge `ready` interchangeably and breaks on whichever arrives first — so a shell that posts
  `ready` from rAF timing at the call site (bullwhip-lineage `static_replay.js`) passes CI while
  softmax.com embeds sample an unpainted shell (clock stuck on the `BAR 0` placeholder, dead
  scrubber). Caught only by phase 60's three-clock check. Fix pattern: `attachReplay` gains an
  `onLoaded` callback fired right after it sets `data-replay-loaded="true"`, and the static shell
  posts `ready` from there (cogame-chorus `3c11c953`). Check the starter's ready-timing during
  phase 20, not after certification.
- **The replay session route binds a replay to the cow whose episode produced it.** After a
  re-release, `POST /coworlds/replays/session` with the new canonical cow_id 404s
  ("Replay for Coworld … not found") for every pre-release replay; the page only serves the fixed
  bundle once a **new round's** replay exists under the new cow (~15 min). Budget that wait into
  any viewer-bundle fix, and smoke the new bundle immediately by constructing the static URL by
  hand (`static/<new cow>/<url-encoded manifest_sha>/index.html?replay=<any s3 replay>` — the
  static route serves the shell regardless of registration).
- **The canonical completion race is ~50 % here, not rare**: releases 0.1.0 and 0.1.2 both read
  `canonical:false` with hosted_smoke passed + cert certified; 0.1.1 and 0.1.3 (pure version
  bumps) both passed. Treat one bump-and-redispatch as the expected cost of a release, not a
  retry of last resort.
- **Rounds can complete hollow mid-league, not just round 1**: rounds 2 and 6 completed with
  `replay_url:null` (round 6 even listed 4 participants), and round 2 seated the same filler in
  both slots. Platform-side; skip to the next scored round rather than debugging the coworld.
- **When chaining recovery after an API-push script, never put `git reset --hard` after a `;`
  (or at the top of a cell with uncommitted work).** A failed fast-forward check aborts the `&&`
  chain but a `;`-separated reset still runs and deletes untracked evidence — and an opening
  reset silently discards edits made in an earlier cell (both bitten this run; recovered via
  `git checkout <lost-sha> -- <paths>` and by redoing the edits).

## 2026-08-24 cogplomacy

- **Bullwhip hosts a 7-seat Diplomacy comfortably.** The parley-stack batch loop scaled from 4 to 7 seats with no budget trouble: a full 4-year episode ran in 178 s of the 720 s budget. A full DATC-style adjudicator (Kruijswijk resolver, circular movement, Szykman) is buildable and CI-testable in one phase-20 round — 20 named adjudication cases caught every rules regression before review.
- **The design note's worked examples must be map-checked.** Two hand-written Diplomacy examples in the note were geographically illegal on the real 1901 board (a fleet supporting into an inland province). Builders should validate any concrete example against the actual adjacency data before pinning tests to it; the builder substituting equivalent legal cases was the right move.
- **`hosted_certification` in release-result.json is a read-time snapshot.** It can read "certifying" (or stale "failed") when the async backend finishes moments after upload returns. The live truth is `coworld status <cow_id>`; commit its output beside release-result.json when they disagree rather than burning a dispatch to re-roll a string.
- **A round can settle "completed" with no episode.** Round 2 completed with error:null but episode_id/replay_url null and all artifact routes 404 ("hollow settle"). Don't anchor verification on the first completed round — use the latest one with a real replay_url; report the hollow round upstream.
- **Atlas backlog compounds under parallel runs.** Seven shipped-but-queued leagues blocked the build; extra_cities carried them all in one dispatch. When co-placing, reuse each run's own STATE.atlas coordinates, and re-run atlas_spot against a locally augmented places.mjs so new dots don't collide with the queued ones (cogplomacy's first spot collided exactly with cogchemists' queued 766,277).
- **Observatory endpoints returned bare arrays** (`/leagues`, `/rounds`, `/policy-versions`, division leaderboard) — not `.entries`. Use `if type=="array" then . else .entries end` everywhere.

## 2026-08-24 cogiavelli

- The commissioner can auto-schedule round 1 within seconds of `POST /leagues/$L/settings` — ours was created and dead 209 ms later, before the filler POST landed, even though fillers were registered before unpause/trigger. Register fillers immediately after settings, and treat an early `failed` round 1 ("Temporal RoundWorkflow failed before settling the round.") as expected noise: exclude it, trigger explicitly, and count completed rounds from there.
- Third-party players can join a brand-new league within minutes (two joined ours ~30 min after announce-less round 1). A new entrant at default Elo with `rounds_played: 0` can displace a champion from rank 2 and empty the featured-match playlist until they have played a round. An empty `state.playlist` right after new entrants is a wait-one-round condition, not a defect.
- A builder thread that dies to "API temporarily overloaded" may have already finished: check `gh run list` on the coworld repo before re-dispatching — our first builder died after pushing the sha that went green, and the re-dispatched builder would have redone it.
- When adopting grid-tuned argmax constants into a scripted baseline, make affordability/legality an invariant of the baseline code (clamp the spend gate to the price), not a property of the tuned numbers — a raw `bribe>=8` argmax briefly let the baseline write bribes it could not afford and broke test_bot.
- Atlas phase now regularly needs `extra_cities`: 7 unplaced leagues had accumulated from same-day runs. Budget one failed dispatch for the "unplaced leagues" error, pick continents from /api/coworlds descriptions, and use atlas_spot's runners-up (~32 units apart) when placing two dots in one continent.
- Phase-60 check 4's `select(.type=="decision")` does not fit babel-lineage replays (kind-tagged events, no decision type): census `press`+`orders` events with `scripted: true` as the fallback marker instead, and say so in VERIFY.md.

## 2026-08-24 grid-wars

- **A sub-agent thread can outlive its dead coordinator session.** Resuming mid-phase-30, the
  "dispatched" r1 fixer had already pushed 13 finding-commits (CI green) but written no
  r1-fixes.md. Before re-dispatching a leg on resume, read the coworld repo's commit log for
  `r<n>-` commit messages and write the re-dispatch brief as "verify existing commits, finish
  the gaps" — the second fixer only had to fix 3 findings and write the report.
- **`GET /leagues` and `GET /rounds` return a bare array**, not `{entries:[…]}` — the prompts'
  `.entries[]` jq lines error. Guard with `if type=="array" then . else .entries end`.
- **A round can be `completed` with no episode** (round 3: settled 11 s after creation,
  `episode_id: null`, `participant_scores: []`). Count rounds with scored episodes for DoD
  check 1, not just `status=="completed"` rows; leaderboard `rounds_played` reflects only the
  scored ones.
- **Atlas batch-placing works.** Dispatch 1 failed on 8 unplaced shipped coworlds; one retry
  with `extra_cities` placed all 8 + grid-wars in one PR. For several new dots in one region,
  append each pick to a local copy of places.mjs and re-run `atlas_spot.py` so the batch keeps
  ≥22 px clearance against itself, not just against the live map.
- **Grid-wars replay events use `kind`/`round`/`seat`**, not the `type`/`tick`/`summary` keys in
  60-verify's example jq — paste schema-correct equivalents next to the literal output so the
  zeros are not misread.
- **Count the Discord announce BEFORE posting**: 1838 chars slipped past the template's 1800
  cap (Discord's 2000 saved it). Compose, `${#BODY}`, trim, then POST.
- **GitHub artifacts API can 503 transiently** right after a run completes;
  `gh api .../actions/artifacts/<id>/zip` + python zipfile is a working fallback.
- **`gh auth setup-git` breaks the sandbox git credential helper** (known gotcha, hit again):
  the fixer repaired ~/.gitconfig but git-over-https pushes to the coworld repo still failed
  ("No anonymous write access"); pushing via the GitHub Git Data API (create blobs/trees/
  commits, assert tree shas match local) worked cleanly.

## 2026-08-24 matrix-games

- **git-over-HTTPS writes can die mid-session while reads and `gh api` stay healthy** ("Invalid
  username or token" on every push, to every repo, from ~16:10Z). The durable workaround is the
  GitHub Data API: blob → tree (on the head's `base_tree`) → commit (parent = head) → `PATCH
  refs/heads/main` — a fast-forward, never a force. Use `gh api --input -` with a JSON body built
  in python for anything big: `-f content="$(base64 -w0 file.png)"` blows ARG_MAX on a screenshot.
  After each API push, `git pull --rebase` drops the now-duplicate local commit by patch-id.
- **A sub-agent thread that dies with "API temporarily overloaded" may have already worked.** The
  first builder pushed the entire coworld and started CI before its thread died. Check the repo
  and CI before re-briefing; re-dispatch with a resume brief (sha + run id), not a from-scratch
  one. After 3 straight spawn failures, a coordinator-applied targeted fix is a legitimate
  "different approach" for the retry budget.
- **Observatory shapes drifted again**: `/rounds?league_id=` and `/policy-versions` now return
  bare arrays (not `{entries:…}`); `/divisions/<id>/leaderboard` returns `null` (not `[]`) before
  the first completed round; the league-seed response already carries `league_id` — no need to
  re-list leagues to find it.
- **Round 1 auto-fails by design timing**: seeding + settings starts a round before fillers can
  possibly be registered, and it dies with "Temporal RoundWorkflow failed before settling the
  round". Expected; the post-filler trigger's round is the one that counts. Register fillers the
  moment both submits return, before any trigger.
- **paintbot worker fork trap**: the first packet after `*_load_replay` is the ONLY one carrying
  `meta`; reading it via `packetAt(0)` (which calls `*_frame(0)`) rebuilds the packet without
  meta and crashes on `meta.<field>`. Mirror the starter's ingest-after-load pattern: read the
  load-built packet directly.
- **Checklist item 15 landed mid-run** (canvas-text bounds): a viewer whose text is all DOM still
  needs the worst-case model-text fixture (full-cap say/notes on every seat, own ci.yml step,
  `--strict-text-bounds`); `canvas_text.total: 0` is expected there and carries no signal — say so
  in VERIFY.md before the judge asks.
- **Atlas debt accumulates**: 9 shipped coworlds were unplaced and the build refuses until every
  one is placed — the fix is one re-dispatch with `extra_cities`. `atlas_spot.py` has no
  `--avoid`: to space several dots in one region, append each pick as a synthetic CITIES line to a
  working copy of places.mjs and re-run the tool against that copy.

## 2026-08-24 commons-family

- **The coworld secret namespace is `game.name`, not the slug.** `secret://coworld/<ns>/…` on the
  runnable must use `game.name` (`commons_family`); with the slug (`commons-family`) local certify
  passes and only `upload-coworld` rejects ("secret … cannot be used by Coworld"). Every
  single-word coworld has `game.name == slug` and never sees this. The repo's release workflow now
  reads `game.name` out of the manifest for `secret put`/`secret list`; the template
  `coworld-release.yml` still hardcodes `$SLUG` and should be fixed the same way.
- **`coworld certify` caps the local smoke episode at 60 s** (`--timeout-seconds` default),
  covering container start, connect grace, all rounds AND the post-game linger. Size the cert
  fixture so `grace + rounds×pacing_floor + linger < 50 s`, and pin it with a test. "Long enough
  for the viewer soak" pushes the other way — resolve it by shrinking the pacing floor in the
  fixture only, never in league variants.
- **League seeding keys on the platform coworld name** (`game.name`, `commons_family`), while
  `/api/coworlds` and the public page use the directory slug (`commons-family`). `POST
  /coworld-league-seeds` with the slug 404s "Canonical Coworld not found".
- **A Python coworld (meadow fork) fits the pipeline**: template `test` job → setup-python +
  pytest; viewer = bullwhip's four files with an expand-only wasm module (the replay records
  per-round `state_before`/`state_after`/gains/scores; the Nim never re-derives physics). Record
  every quantity the viewer displays (e.g. per-round `seat_public_effort`) — anything recomputed
  browser-side is a second implementation and a review finding.
- **The sandbox git credential can lack a grant on a brand-new Metta-AI repo** (401 on push to the
  new repo while coworld-builder pushes fine). `gh` has push: use the Git Data API
  (blobs → tree → commit → ref), preserving 100755 modes.
- **Atlas placement collisions are systematic**: every queued run's `atlas_spot` picks the same
  roomiest spot in a region (three pairs collided across the 10-PR backlog). When placing others'
  leagues via `extra_cities`, keep each run's own-slug region/coords from ITS queued PR, and
  re-spot only the collisions with `atlas_spot` against a working places.mjs augmented with the
  kept dots.
- **An adaptive registration grace beats a fixed one**: returning as soon as every connected
  socket has registered (bounding only a connected-but-silent socket) cut 5 s from every episode
  and was what brought the cert fixture under the 60 s cap without touching the game.

## 2026-08-24 hanabi

1. **`maxOutputTokens` truncation has a misleading log signature.** A reply cut at `max_tokens`
   mid-JSON reaches the hosted log as `rejected: unbalanced JSON object in response` — it looks
   like a malformed-reply bug, but the fix is budget, not parsing. Hanabi shipped 800 (design
   default), failed phase-60 check 5 on it, and re-released at 900: the unbalanced-JSON signature
   vanished but a reasoning-heavy champion (the "signaler" prompt) still overran ~once per episode
   in 2 of 3 verified rounds (always retry-recovered, zero fallbacks). Two carries: (a) make the
   truncation name itself — on `stop_reason=="max_tokens"`, re-run the JSON extractor and raise
   "reply cut off at max_tokens mid-JSON" instead of the balancer's generic error (0.1.1 does
   this); (b) for games whose prompts invite long reasoning, budget ≥1000 output tokens or pin a
   JSON-first reply contract in the fixed instruction scaffold at design time.
2. **`gh --jq` is not jq: it takes no `--arg`.** `gh run list --jq --arg d "$D" '…'` fails with
   "unknown command" AFTER the dispatch went out, and a careless fallback `gh run download` then
   grabs the PREVIOUS run's artifact as this dispatch's evidence (a submit-result naming the wrong
   policy made it visible here). Interpolate the timestamp into the jq string
   (`--jq ".[] | select(.createdAt >= \"$D\") …"`) and always cross-check the downloaded
   artifact's identifying field (policy label, url) against what you dispatched.
3. **The atlas backlog compounds under parallel runs.** Dispatch 1 failed with **12** unplaced
   leagues — every coworld shipped since the last atlas PR actually merged (metta's Graphite queue
   waits on a human, so open atlas PRs do not update `main`'s `places.mjs`). Expect the first
   dispatch to fail, and batch-place the whole list via `extra_cities` in dispatch 2. To pick
   several non-colliding spots in one region, append each pick as a fake CITIES line to a local
   copy of `places.mjs` and re-run `atlas_spot.py` against that copy — clearances stayed ≥22.9
   for 13 dots across 5 regions.
4. **`git config --global --remove-section credential.https://github.com` removes the sandbox's
   own helper too.** Cleaning up after a sub-agent's `gh auth setup-git` this way silently
   deleted the `git-credential-anthropic` registration that lives in the same section, and pushes
   then hung/401'd. The restore is one line:
   `git config --global credential.https://github.com.helper /usr/local/bin/git-credential-anthropic`.
   Prefer `--unset-all` of the two gh-added values over removing the whole section.

## 2026-08-25 cooperative-hunting

- **`coworld certify` defaults `--timeout-seconds 60` and applies it to waiting for the game
  container to exit.** A cert fixture longer than ~40 s of wall clock (rounds × ticks ÷ tickHz
  + ShutdownGraceSeconds) can never pass — ours needed ~150 s and failed `episode_timeout`
  after two unrelated cert fixes. Add `--timeout-seconds 300` to the certify step in
  `coworld-release.yml` instead of shrinking the fixture (the wasm-viewer soak consumes the
  smoke replay derived from the same fixture and needs it long).
- **The Coworld secret namespace must equal `game.name` exactly.** The template's single `SLUG`
  serves both as image/repo slug (hyphenated) and secret namespace; any coworld whose
  `game.name` is underscored fails `upload-coworld` with HTTP 400 "Coworld secret <ns> cannot
  be used by Coworld '<name>'" — and certify cannot catch it (certify never uploads a
  manifest). Split the notions: keep ci.yml's SLUG hyphenated, set the release workflow's
  secret namespace (and the `secret://coworld/<ns>/…` refs in the manifest template +
  build_manifest.py) to `game.name`.
- **League seeding keys on the canonical Coworld name, not the page slug.**
  `POST /coworld-league-seeds` with the hyphenated slug 404s "Canonical Coworld not found" when
  `game.name` is underscored; the public page still lives at the hyphenated
  `softmax.com/<slug>` and `/api/coworlds` lists the hyphenated slug. Three different name
  spaces — seed with `game.name`, verify the page with the slug.
- **The atlas build fails on ANY unplaced live league, and they accumulate.** 13 shipped
  coworlds had no dot; dispatch #1 died on the full list. When placing many at once with
  `extra_cities`, run `atlas_spot.py` iteratively against a working copy of `places.mjs` that
  you append each chosen dot to — otherwise several new dots in one region all get the same
  "roomiest" spot.

## 2026-08-25 chemistry

- **`os.getAppDir` has no emscripten implementation** — under a paintbot-lineage wasm build it dies with `value out of range: -1 notin 0 .. 2147483647` (from `getAppFilename`) *before* any fallback path runs, with no stack. Guard every `gameDir()`-style lookup with `when not defined(emscripten)` and try the working directory first. Diagnosable locally: install emsdk + run the bundle under node with `--stackTrace:on`.
- **Diff `/api/coworlds` against `places.mjs` CITIES BEFORE the first atlas dispatch.** With parallel runs shipping coworlds hourly, the "unplaced leagues" build error is now the common case (this run: 14 backfills on dispatch 2, then collab-cooking went live mid-phase and cost dispatch 3). Compute the full missing set up front and pass it in `extra_cities` on dispatch 1; re-fetch `/api/coworlds` immediately before each dispatch.
- **`coworld-league-seeds` accepts `default_variant_id` at the top level of the seed body** (echoed back in the 200). That is the cheap moment to pin the league variant — gridlock's 409 shows it cannot be re-seeded later.
- **Verify policy ownership from `GET /policy-versions` (player_name column) between phase 40 and the champion submits.** Coins' account-level `softmax player use` leak (all four v1s minted as daveey-1) did not recur here, but the 30-second check is what proves it before a 409 does.
- **docker_smoke player-exit assertion folded back into the template** (`templates/tools/ci/docker_smoke.sh` now asserts every player container exits 0 — raid 0.1.3→0.1.4 trap; was a per-repo delta in cogame-chemistry).
- **Bedrock haiku daily-token 429 is a *daily* quota** — it throttled 03:23Z–08:08Z platform-wide and then cleared on its own. A run hitting it in phase 60 should document the cross-coworld evidence and keep polling the full 75-minute bound before blocking: rounds triggered after the quota clears verify clean (this run: r2–r5 mass fallback, r6 champions 14/14 LLM).
- **Chemistry's LLM player has no model-level fallback** (haiku-only by design, raid learning) — hanabi survives a haiku throttle by switching models; chemistry drops to scripted orders for the shift. If the haiku quota becomes chronic, a bounded sonnet fallback for *standing-order* games (1 call/seat/shift, not per-tick) may be worth revisiting.

## 2026-08-25 collab-cooking

- **mettagrid packs feature ids into one byte (`token_value_base` 256): any resource minting that scales with a config knob is a latent construction crash.** The kitchen minted one ticket resource per prospective ticket (`max_steps / interarrival`); the 480-tick cert fixture fit (52 slots) while every published 900-tick variant crashed `create_app()` before uvicorn bound — `game_unhealthy`, no logs, all league episodes dead behind a green certification. Fix shape: a recycled fixed slot pool (bounded by max concurrent live entities, not by episode length). Prevention now templated in this repo's practice: a phase-20 test that builds the env from EVERY manifest variant's `game_config` verbatim (parse the template, same call path as `create_app`) and pins `max(feature id) < 256` with headroom.
- **`coworld build`'s template loader is the phase-20 gate nobody runs.** coworld 0.1.42 rejects top-level `replay_viewer` (belongs at `game.replay_viewer`), top-level `version`, `game.display_name`, and requires `game.owner`; the cert fixture must NOT declare runner-managed `tokens` (`manifest_invalid: game_config must not include runner-managed tokens`). Repo CI can be all green while phase 40's very first step fails. Cheap fix adopted: `tools/ci/check_manifest_loads.py` runs the installed coworld's own `_load_template_manifest` as a ci.yml step.
- **A private base repo ("EXTENSION of <coworld>") does not `git clone` with GH_TOKEN** — "Repository not found". `gh api repos/<owner>/<repo>/tarball/main | tar -xz` works with the same token.
- **CI replays carry zero LLM text, so DOM-rendered model text needs its own gate.** viewer_smoke's canvas probe cannot see clipped DOM chips; ctf's `.feed-row { white-space: nowrap }` is sized for 10-char names and clips sentences 60% off-stage. `tools/ci/dom_text_smoke.mjs` (real page + chrome + font, full-cap multi-script strings, 13 viewports, scrollHeight/Width ≤ client, strings asserted still full-length) is the reusable pattern — it reported 108 failures against the pre-fix client, 0 after.
- **Unpausing a freshly-seeded ladder auto-fires round 1 immediately** — registering fillers in the same breath as `rounds-paused:false` loses the race and round 1 dies `Temporal RoundWorkflow failed before settling the round`. Register fillers while paused; expect and discount a failed round 1 if unpause preceded them. (When re-wiring after a re-release, pause → fillers → resubmit champions → unpause is the clean order.)
- **`tools/push_via_api.py` with an unseeded state map replays the clone's whole history as new commits** — a fast-forward, nothing rewritten, but main's log shows every subject twice. Seed the local→remote sha map before the first push from a new clone.
- **The atlas backlog compounds**: 15 shipped leagues sat unplaced because every prior run's atlas PR waits unmerged in Graphite's queue, so each new run's dispatch 1 fails and must re-place the entire backlog via `extra_cities`. Until a human drains the queue, budget dispatch 1 as the probe that enumerates the backlog and dispatch 2 as the real one; reuse each run's own STATE.atlas region/x/y and resolve collisions with atlas_spot against a locally-accumulated places.mjs.

## 2026-08-25 territory

- **Cogherence (TypeScript/pnpm) lineage cannot release with the stock `templates/coworld-release.yml`**: its Dockerfile `COPY dist` / `COPY dist-server` expects pre-built bundles, and the template has no node/pnpm build step — v0.1.0 failed at "Build the Coworld manifest". Fix: insert pnpm/action-setup + setup-node + `pnpm install --frozen-lockfile && pnpm build` before the manifest step (cogame-territory commit `ad1e8df1`). Same for `ci.yml`: `npm install --no-save playwright` dies with EUNSUPPORTEDPROTOCOL inside a pnpm workspace — install playwright in `$RUNNER_TEMP` and point harnesses at it via `PLAYWRIGHT_MODULE`.
- **Fresh `Metta-AI/cogame-*` repos give the mount token no direct `git push` grant** — use the gh Data API path (blobs → tree → commit → ref, append-only). A completely empty repo 409s on `git/blobs`; the very first write must go through the Contents API.
- **The sandbox clock can drift far off UTC** (~67 min ahead this run). Stamp log lines from `date -u` at write time and never trust earlier stamps for cross-source comparisons; the verifier caught it by diffing against API `created_at` and the softmax `Date` header.
- **Atlas backlog compounds**: 17 shipped coworlds were live-but-unplaced because their atlas PRs sit unmerged in metta's Graphite queue, so `build.mjs` refused the new line. One dispatch with `extra_cities` placing all of them fixed it. When placing several dots in one region in a single pass, `atlas_spot.py` returns the same "roomiest" point each call — inject each pick as a fake CITIES neighbour into a working copy of `places.mjs` before the next call.
- **Viewer scrub's right edge may not reach FINAL**: with 18 turns the beat row rendered 01–14 and the smoke's 100% click landed on Turn 14, so the endcard (where the deadweight-loss read-out lives) is unreachable from the rail's right edge. Design/review should pin "the last beat is FINAL" or that the rail scrolls; judged advisory this run.
- **Talk can ride the decision rather than the wire talk channel** when the reply schema addresses DMs by alias while the wire `TalkLine.to` is a seat number, and `decide`/`talk` run in parallel — engine-owned transcript also makes it part of byte-for-byte determinism. Declare it in the manifest protocol docs so the certifier's read matches.

## 2026-08-25 paintball

- **Bedrock haiku daily-token 429 comes in windows, not a flat outage** — this run saw throttled→recovered→throttled→recovered inside 5 hours. Phase 60's cheap probe is the episode's `artifacts/results` `llmTurns`/`fallbackTurns` (no replay download); poll rounds inside the 75-min bound and re-pin checks 3–5 to a round that landed in a recovered window. SPEC item 5's "documented platform-wide cause" branch is part of the check, not a softening — quote it and cross-check another LLM coworld's latest episode the same session.
- **The sonnet fallback scar generalises**: `us.anthropic.claude-sonnet-4-5` as a ladder fallback candidate timed out on 133/133 sidecar calls (raid 2026-08-23 reconfirmed). Ship haiku-only candidates and fail-fast on 429 — a retry against a model that never answers just converts one fallback into a slower one.
- **curly's `CURLOPT_TIMEOUT` floors sub-second deadlines to whole seconds** — `attempt1Ms: 4500` really ran 4 s against a 4.6 s median sidecar call, so nearly every first attempt "timed out". Set whole-second deadlines clear of the measured median (6 s/3 s here) and make sim_config reject sub-second values.
- **Slot-sequential join admission can silently unseat a champion**: daveey-1 connected first on slot 1, stayed unadmitted, and the lobby still sent it frames — its registration arrived with `playerIndices == 0x7fffffff` and was dropped, so a champion seat played the scripted baseline for whole rounds. The smell is `llmTurns[seat] == 0` across consecutive rounds. Fix: the server holds an unappliable registration and the player re-sends for ~10 s.
- **External players joining a public ladder mid-run changes phase 60's shape**: rounds grow to ~6 episode requests and the "latest round's episode" for checks 3–5 must be selected as the champion-vs-champion pairing (say so in VERIFY.md). Externals also make whole rounds `failed` ("only N/M planned slots produced scoring evidence") through no fault of the coworld — record the error verbatim; those rounds simply don't count toward check 1.
- **A binary replay should carry a `result` control record in the bytes** — before 0.1.3 `results.reason` was only in the hosted artifact, and check 4 had to read two sources. Writing it at episode end made the replay self-contained and byte-reconcilable with the artifact.
- **Viewer mid-seek clicks that arrive before the first chrome frame get dropped** (`if (!lastState) return`); the smoke's 0%==50% clock readout is the signature. Queue the click and converge with a bounded per-frame tick walk (SeekTicksPerFrame) instead of re-simulating thousands of ticks in one frame — and add the three-distinct-scrub-clocks gate to wasm-viewer CI so it can't regress.

## 2026-08-25 daycare

- **Reuse the newest pending atlas PR's placements instead of re-deciding**: with the Graphite queue undrained, every run re-places the same backlog and pending PRs now disagree (collab-cooking is commons(446,520) in its own #20372 but shire(193,586) in #20388). The built HTML in a PR diff carries placements as `transform="translate(x,y)"` at exactly 3× overview units — divide by 3 and pass them verbatim as `extra_cities` so successive PRs converge on one map. This run adopted #20388's daycare spot (shire 217,583) for the same reason.
- **A sub-agent leg that dies leaves no file, and that is the signal**: the first phase-60 verifier session died between dispatch and write; the resume found no VERIFY.md, counted no progress marker, re-dispatched, and passed 8/8 in ~15 min. Trust the file-is-the-deliverable rule — do not reconstruct a dead leg's work from its dispatch line.
- **2-seat games on a 4-player public ladder produce 6 episode-requests per round** (all pairings); checks 3–5 must select the champion-vs-champion ereq explicitly, and check 2's "fillers absent" is satisfied by absence when third-party entrants fill the board (richard/relh precedent, second run in a row).
- **viewer_smoke.mjs probe gaps to fix next starter fork**: `feed_lines` selector matched 0 rows while the screenshot showed a populated feed, and `bridge_ready` stayed false because the shell signals readiness only via `data-replay-loaded`, never the `coworld-replay` postMessage bridge. Both passed SPEC as written but cost the judge a manual screenshot reconciliation each time.

## 2026-08-25 factory-commons

- **A hyphenated slug and an underscored `game.name` are two different names on the platform, and every surface picks one.** The Coworld registers under `game.name` (`factory_commons`): `coworld secret put` (release step) and the league seed's `coworld_name` both 404 on the slug. The public page and `/api/coworlds` use the hyphen slug (`softmax.com/factory-commons`; `softmax.com/factory_commons` serves the generic shell). Fixed the release template in this commit (secret step now reads `game.name` out of `dist/coworld_manifest.json`); for phase 50, seed with `game.name`, and for phases 60/75, page and directory use the slug.
- **`GET /leagues` returns a bare array, not `{entries:[…]}`** — `jq '.entries[]'` dies; use `if type=="array" then .[] else .entries[] end` or take `league_id` straight from the seed response, which includes it.
- **The first ladder round can be scheduled between the settings POST and the fillers POST** and fails with `Temporal RoundWorkflow failed before settling the round` even though your own trigger came after the fillers. Not a defect and no re-trigger needed — the next scheduled/triggered round runs; just exclude round 1 in check 1 and quote its error.
- **`git push` over HTTPS can lose auth mid-session while `gh api` keeps working** (`Invalid username or token` on push, 200s on API). Don't burn the retry budget on it: replicate the local commit through the Git Data API (blobs → tree → commit → PATCH ref, `force=false`), then `git reset --hard origin/main`. For blobs > ~100 KB (viewer-smoke.png) pass the JSON body via `--input -` — argv overflows.
- **Atlas debt compounds silently**: 18 shipped coworlds had no `CITIES` line, so the first atlas dispatch of the day eats the whole backfill via `extra_cities`. When placing many dots, run `atlas_spot.py` iteratively and append each accepted spot as a one-line CITIES entry to the local `/tmp/places.mjs` between runs — the parser reads it, and runner-up spots from a single sweep can sit 7 units apart.
- **The Bedrock 429 daily-token throttle text (`Too many tokens per day`) matches none of check 5's four grep patterns** — a throttled episode greps CLEAN. Read the decoded log, not just the grep, and scope the finding by cross-checking another LLM coworld's episode from the same minute. Rounds self-heal when the quota resets; fallbacks:[0,0,0] two rounds later.

## 2026-08-25 fruit-market

- **Designer map geometry deserves a computational check before build round 1.** The accepted note carried three defects its own assertions would catch: a perimeter miscount (`d==5` ring is 48 cells, not 32 — perimeter of the inset rectangle is `88−8d`), a tree list that walled the island into three disconnected pieces (its own connectivity assertion could not pass), and an economy where the note's target ("trading ≈ 2.5× autarky") was unreachable under its constants. All three surfaced in phase 20 and were fixed as rails calls; a designer that runs a 20-line python sanity script over authored cell lists (counts, overlaps, connectivity) would have shipped a correct note.
- **When a shared consumption cap binds both the trader and the recluse, travel-cost levers plateau.** The note's gate-(b) repair ladder (raise water tolls / far-grove cooldowns) moved the hauler:homesteader ratio 0.62→0.72 and stalled, because the autarkist was eat-capped, not travel-capped. The working fix caps the diet so score is decided by its *composition* (eatCooldown 6→24, harvestCooldownOther 24→96): ratio 1.59–1.76 on all variants. Generalises to any "X strategy must beat Y" gate: identify which constraint actually binds Y before tuning the costs X avoids.
- **Atlas extra_cities should reuse each run's own STATE.atlas call — and say when you diverge.** This run's PR #20453 (newest, fullest: 20 dots incl. the whole backlog) took regions from each run's own STATE where present, but placed `daycare` at parlour(453,832) as a fresh call, not knowing daycare's own run had adopted shire(217,583) from #20388 (its STATE was unreadable mid-flight — live runs' dirs are off-limits). Next atlas run: read pending PRs' built HTML (`transform="translate(x,y)"` ÷ 3) per the daycare learning AND diff against LEARNINGS entries for adopted spots before re-deciding anyone's region.
- **Forked starter endcards carry team-panel labels no gate covers.** The coworld-ctf endcard's per-team columns shipped reading `LIVES LEFT / K / D / CLSTR / CAP` under fruit scores — visible in the phase-60 screenshot, caught by no smoke (labels are static DOM, always "inside", always full-length). Design notes should list endcard label re-mapping alongside the scorebug re-letterings, and test_broadcast should assert the endcard's own label strings.
- **A champion prompt can be a competitive liability without failing any check**: ricardo's "build six, post SIX-for-FOUR, hold if rates rise" starved it to score 0 in both rounds (480 starving ticks) while emitting 24/24 genuine LLM orders — every definition-of-done item still passes. If a future idea wants champions that *contest* the top, feasibility-gate the champion prompts too (a scripted proxy of each prompt's opening book vs the fillers), not just the baselines.

## 2026-08-25 gift-refinements

- **The adaptive lobby close ("every connected socket has registered") is a champion-eviction bug class.** Scripted filler pods register within milliseconds; champion pods (LLM sidecar warm-up) connect seconds later — the lobby closed 3/6 and 4/6 in two of three live rounds and the champion seats silently played the scripted baseline, with `fallbacks=0` and every check green except the order-source counts. Paintball's 10 s held-registration re-send does not cover it (the round loop has already started). Pin instead: close early ONLY when connected ≥ num_agents AND registered ≥ num_agents; otherwise wait out `playerConnectTimeoutSeconds`; test that the lobby stays open below full seats. docker-smoke cannot catch it (all pods start together) — phase 60 must read the lobby line (`lobby closed with N/M seats`) and per-seat order sources, not just fallback counts.
- **Champion prompts need the order schema stated negatively.** Strategy prose saying "spend or bank your raw" led the model to emit `"job":"consume"` (consume is a field, not a job) → parse_error → scripted fallback. Fix that held: end every prompt with a SCHEMA sentence naming the closed job set and "Consuming is NOT a job", plus a test asserting each PLAYER_PROMPT contains it. A first-attempt parse error whose retry succeeds still lands in the hosted log — write prompts to survive attempt 1.
- **After a re-release + coworld-submit, round attribution lags placement.** A round scheduled ~2 min after the champion resubmit still carried the OLD policy_version_id (round 7: patron v2 despite v3 submitted ok). Verify each round's `round_config.entrant_attributions` carries the new UUIDs before counting it; expect to exclude one straddling round. Re-wire order that worked: pause → filler-policies (new UUIDs) → resubmit both champions → unpause → trigger.
- **Identical-content policies did NOT dedupe on re-release**: all four entries minted :v3 even though the two scripted fillers' content was byte-identical to :v2. Do not rely on the dedupe note in prompts/40-release.md; resolve fresh UUIDs and re-register fillers after every release.
- **The 60-verify prompt's check-4 jq filters (`.type=="decision"`, `.fallback==true`) can return 0 on a healthy replay** whose schema uses `.k`/`.source` (order rows, source ∈ llm|retry|fallback|scripted). Paste both filter sets; the schema-correct one is the evidence.

## 2026-08-25 hidden-agenda

- **Spell the reply schema's sibling keys in the hint, and make the validator honour every form the prompts teach.** The design had `{"job":"mine","at":"S2"}` (argument as a sibling key) but the user-prompt hint only showed `{"plan":[{"job":...}]}` and the system prompt taught a compact `mine at:<seam>` form. Haiku wrote `{"job":"mine at:S2"}` → rejected; retried without the arg → rejected again; champions fell back to scripted on 80–87% of decisions across three hosted rounds. No CI job can catch this (docker-smoke has no API key, test_llm stubs the transport with well-formed replies) — it surfaces only at phase 60 check 4. Fix both ends on day one: hint shows full object shapes with the legal enum values for this role/this moment, and the parser splits any compact form the system prompt documents.
- **A re-release that changes the image mints new policy versions — re-seat afterwards.** 0.1.0→0.1.2 moved all four policies v1→v3 (each dispatch of a changed image mints one). After any phase-60 fix release: re-submit both champions at the new labels, POST the new filler UUIDs (the filler list is replaced, not appended), and only then trigger. Old-version entrants keep playing otherwise; the leaderboard labels flip once the new submissions land.
- **The atlas backlog is now ~22 queued PRs deep; pending runs' STATE.atlas coordinates are mutually colliding.** Each queued run swept an un-updated main, so six runs "own" 416,574 and three own 766,277. Don't trust STATE.atlas x/y of queued runs when batch-placing via extra_cities — keep each run's REGION (its rails call) but recompute every spot with atlas_spot.py against a locally augmented places.mjs, appending each pick before the next sweep. 23 distinct spots, clearance ≥22.9, one dispatch.
- **Sandbox git push can lack write grant on a repo `gh` can admin.** Plain `git push` to the new coworld repo failed "No anonymous write access" while GH_TOKEN had push permission. Committing a `tools/publish.py` (Contents API bootstrap, then Git Data API blobs→tree→commit→ref) in the scaffold made every later phase's pushes one command; carry the note into every phase-30/40/60 brief so fixers don't burn time rediscovering it.
- **Check spawn geometry against attack range in the cert fixture.** The note's spawn table put two pairs at exactly freezeRange; a strike impostor ended the cert episode in 26 ticks — a 1.1 s replay the 10 s viewer soak can't play. The builder caught it pre-CI by measuring; widened spawns + a longer fixture (freezeCooldownTicks 500 → 25.3 s of video). Cheap rule: min pairwise spawn distance > attack range, and fixture video length > soak window with margin.

## 2026-08-25 pistonball

- **Two more platform manifest rules the design pins got wrong** (now in the playbook table): `game.description` is REQUIRED and `game.tags` is FORBIDDEN (tags are top-level only); bundled `player[].resources.limits.cpu` has a hard minimum of `"1"` — a 20-seat game cannot economise with `500m`. Both only surface at the release workflow's manifest/upload steps; pin both in `tests/test_manifest.nim` on day one.
- **The turn-budget/rate-floor interaction is a testing blind spot**: `decide.turn` sampled `turnStart` before the 45 s `minBatchSpacingMs` sleep, so with the SHIPPED config (spacing 45000 > budget 20000) every turn after turn 0 was "budget exhausted before attempt 1" and champions silently played scripted — while every engine test used small spacings and passed. Caught only by phase 60 reading round 2's replay (`llmTurns [1,1]`, 14 fallback records @0 ms). Rule: at least one fake-clock engine test must run the manifest's own timing constants, and the budget must measure the turn's work, not the wait.
- **Per-seat counters the live server increments read zero in the static viewer**: `llmTurns`/`fallbackTurns` fed the endcard's LLM/FB column but only `server.nim` incremented them; a replay never runs that path, so the viewer showed 0/0 for champions. Any results-adjacent counter the chrome renders must be recounted by `applyReplayEvents` from the replay records (non-hashed, keyframe-carried).
- **Re-run viewer-check after ANY re-release before the phase-60 judge**: the fix release (0.1.3) changed the viewer shell (endcard) and wasm (replays.nim), and the committed viewer-check evidence was 0.1.2-sha. The judge correctly returned blocking:1 for exactly that. Budget one extra viewer-check dispatch into every verify-fix loop.
- **Never `git reset --hard` the shared checkout while a sub-agent may hold unpushed writes** — it destroyed the judge's rewritten verdict (the sub-agent had written but not pushed; one wasted round-trip to re-emit). Collect the file, commit it, THEN sync.
- **Git-data-API pushes race concurrent runs**: building the commit tree from `git diff origin/main HEAD` after a fresh fetch clobbered another run's just-pushed files (3 emptied, 1 reverted; restored byte-identical from the prior tree). Path-guard the push helper to this run's own `runs/<run>/` files and the two shared root files, and never derive tree items from a cross-run diff.
- **Fully-cooperative 20-seat league still ranks fine with the standard settings body** (`elo` + `round_scoring_rule: "mean"`, the tandem precedent): every score is shared so MMR stays 1000 and the leaderboard orders by rounds played/attribution — acceptable; the design's "no Elo" pin is satisfied by the mean scoring rule, not by a different algorithm.

## 2026-08-26 walker-waterworld

- **The flat `GET /v2/episode-requests` route is gone (405, allow: POST)** — it broke two places in one run: `coworld[auth]==0.1.42`'s `--wait-hosted-smoke` (release dispatch 1 died at "Upload the Coworld"; 0.1.43 lists the nested `/v2/coworlds/<cow>/episode-requests` route, `cli.py` byte-identical, so every grepped marker survives — templates' pin floor is now 0.1.43) and phase 60 check 3's `?round_id=` query (use `GET /v2/rounds/<round_id>/episode-requests`; the detail route `GET /v2/episode-requests/<id>` still works). Playbook §9 updated in this commit.
- **`GET /rounds?league_id=` returns `{"entries": …}` but `/leagues` and `/policy-versions` return bare arrays** — write dual-shape jq (`if type=="array" then .[] else .entries[] end`) in every verifier brief; both shapes were live in the same hour.
- **The sandbox CAN run Nim**: Nim 2.2.4 + nimby 0.1.26 (`nimby --global sync nimby.lock`; the committed nim.cfg points at ~/.nimby/pkgs) built and ran the full 15-file suite in both modes locally. Docker/emsdk genuinely absent — viewer/image failures still only surface in CI — but fix rounds shrink from N CI cycles to 1 when the fixer compiles locally. Put this in every builder/fixer brief.
- **Pre-empt the atlas "unplaced leagues" failure instead of burning a dispatch on it**: with ~23 queued atlas PRs, main's places.mjs is always behind. Take the newest queued PR's exact `+ CITIES` lines (`gh pr diff <n> -R Metta-AI/metta`), pass them verbatim as `extra_cities`, and compute this run's spot with atlas_spot.py against a locally augmented places.mjs (append those lines first). One dispatch, PR 20500, no collision with the queue's spots.
- **A round row can be created before your filler POST and still run with fillers** — round 2's row predated the filler registration by 39 s yet seated two drifter:v2 `is_filler` seats. For check 1 disputes, the judge settles it from the round's actual seats, not the timestamps; cleanest is to have ≥2 rounds created strictly after the POST (rounds 3+4 here).
- **viewer-check.yml's `feed_lines` selector misses paintbot-lineage feed nodes** — it reported 0 while the screenshot showed 4 intent captions. Judge motion/feed from the png + replay reconciliation; fixing the harness selector is an open tooling item.
- **A shared-score co-op's leaderboard shows 1000.0/1000.0 with episode_wins 0.0 and that is healthy** (win[] stays all-false below the capture target; Elo has nothing to separate) — rank rows + rounds_played are the "both champions ranked" evidence, as ruled by the phase-60 judge here and on pistonball.

## 2026-08-26 particle-worlds

- **The nonce guard has a wake-from-the-dead hole, and log.md is the working fix.** The original session's heartbeat went stale (182 min) while it was blocked inside its phase-20 builder thread; a cron adopted the run through the 5.0 guard (nonce written, Asana stamp held), and then the ORIGINAL session woke when its builder returned and kept coordinating — the rejected-push foreign-nonce rule never fired for it because the adopter's `00 resume` line was already in log.md at its first post-wake pull ("not there before your pull" ⇒ not new ⇒ continue). We got two reviewers, then two fixers, on one round. What resolved it: the adopter wrote an explicit `30 INCIDENT` line naming the ownership adjudication (STATE.session_id + the Asana stamp), and the zombie read it, renamed its artifacts `-parallel`, parked its fix commits on a branch, never touched main, and exited. Until the prompt grows a wake re-check ("re-read STATE.session_id after any sub-agent wait that outlived a heartbeat interval; if it is not your nonce, stand down"), do both halves of that dance deliberately. Its parallel review was kept and fed to the judge — two independent r1 reviews found disjoint real defects, which is the one silver lining.
- **A wall-clock stop that mutates hashed sim state outside `sim.step` breaks every deadline replay, and no CI gate sees it.** coworld-ctf-lineage forks bank rounds/finish the game from the server loop on `deadline`; all those fields are hashed, the same iteration records the post-mutation hash, and no replay record carries the stop — so playback re-derives `Playing` and hash-mismatches at the stop tick, exactly on the ending the design declares acceptable for phase 60. Fix shape that held: ONE load-bearing chat record (`stop`) written at the stop tick and applied by the same proc on record and playback, GameVersion bump, plus an end-to-end test that records a deadline-ended episode through the real writer and asserts `hashMismatchTick == -1` AND end-state equality. Day-one rule for any real-time fork: every end path (`complete`/`deadline`/`fault`) gets a record→re-derive test, not just `complete`.
- **A renderer fixture that re-implements the drawing is worse than none — it testifies while testing nothing.** The first fixture was a ~190-line inline `drawBoard()` with a comment claiming it "loads the REAL chrome"; the real renderer draws board text in a Worker/OffscreenCanvas and chrome text in DOM, so the main smoke's `canvas_text` was 0 and the fixture's 302 were fiction. The honest fixture: serve the SHIPPED `dist/static-replay-viewer/index.html` in an iframe, shim ONLY the wasm entry (`createCore` via getter), drive the page's own `onText` with the worst-case frame, transcribe each laid-out DOM text run to a canvas at browser-measured position/font so `--strict-text-bounds` gates real geometry. First run of the real fixture found a real defect (160-rune notes growing leftward off-frame at 360 px in `white-space:nowrap` feed rows).
- **The atlas queue is undrained and the backlog re-derives per run**: dispatch 1 failed naming 25 unplaced leagues even though PR 20500 (walker-waterworld, same morning) had just placed ~23 — queued PRs are invisible to a fresh `main` sweep. This run recomputed all 25 (regions = each game's own character; spots = atlas_spot.py against a locally augmented places.mjs, seeding THIS run's own dot first — dispatch 1's spot collided with collab-cooking's fresh pick without that). Next run: prefer walker-waterworld's verbatim-adoption recipe (`gh pr diff <newest> -R Metta-AI/metta` → `extra_cities`) so the queue converges, and seed your own dot either way.

## 2026-08-26 knights-archers

- **`upload-policy` does not dedupe byte-identical content.** Three release dispatches with an unchanged `tools/ci/policies.json` minted v1, v2, v3 of all four policies. Always take the `<name>:vN` labels from the LAST successful `release-result.json`, and resolve UUIDs from `GET /policy-versions` by exact label match — `startswith(slug)` alone now returns several versions per name. (Playbook §Phase 2 corrected in this commit.)
- **matriculate rejects literal runner-managed `tokens` in any `game_config`** (variants and the cert fixture) even though `config_schema` requires `tokens` — the runner injects them. A builder copying a fixture from a repo that carries tokens hits this every time; the fix is removal from every `game_config`, not from the schema. (Common-mistakes row added.)
- **Hosted certification can fail on the platform's own internals while everything local passes**: `failed_step: smoke-episode`, detail = the certifier's internal `/v2/episode-requests` GET 404ing, `retryable: false` — yet hosted smoke passed and Canonical was yes. A version-bump re-dispatch with zero code change certified 10/10 once the backend settled (~25 min later). Treat `retryable: false` + an internal URL in the detail as "retry via bump anyway, once", and cross-check another coworld to confirm churn.
- **`git push` over HTTPS can break at egress mid-run** ("Invalid username or token" — basic auth hides the token from the egress swap) while `gh api` header auth keeps working. Working fallback used all run: push via the Git Data API (blob → tree with `base_tree` → commit → PATCH `refs/heads/main`, `force:false`), then `git fetch` + verify `git diff --quiet main origin/main` before resetting local onto the API commits. Large binaries (screenshots) need the blob content streamed from a file (`jq --rawfile`), not `--arg` (argv limit).
- **A template pin bump strands repos scaffolded before it**: this repo carried `COWORLD_PKG==0.1.42` (flat `/v2/episode-requests` route → 405 on `--wait-hosted-smoke`) because phase 20 ran before the 0.1.43 template bump landed. After any template pin bump, sweep in-flight cogame repos for the old pin.
- **PettingZoo-port continent precedent is now three deep**: fully-cooperative shared-reward ports go to the commons (pistonball, walker-waterworld, knights-archers). The atlas backlog trick that worked: reuse the newest queued atlas PR's CITIES diff verbatim as `extra_cities` (`gh api …/places.mjs?ref=<branch>`), then spot your own dot against a locally augmented places.mjs so it avoids the whole backlog.

## 2026-08-26 poker

- **A "mod of <live coworld>" idea can take that coworld as the starter itself** when it is a parley descendant with all four viewer files internally consistent (cosino's config.nims/static_replay.js are a matched MODULARIZE pair). The knights-archers rule ("extension bases are rules references only") applies to bases that lack the static-viewer/CI conventions — check the base's tree before defaulting to babel. Only three babel behaviours needed porting: the postMessage bridge (ready from onFirstFrame), the bounded fetch + Retry, and the templates' CI layout.
- **Metric formulas pinned in a design note deserve a measured falsification pass before review.** The pinned collusion-audit attribution (clamped equity-loss at last-action equity, bb thresholds) flagged honest play in 3/30 episodes; the fix that worked (0/30 both baselines) was pricing showdown slices on the FINAL board (exact, loss=0 for completed hands) with signed attribution — the MC estimate at all-in time books realized variance as "surrender" (~half a stack vs a 2-bb bar). The builder measuring 30-seed sweeps per design candidate before pushing beat any amount of review.
- **Checklist item 5's 60% is on the true worst-case settle, not the guard threshold.** A hard guard *checked before* a decision must net off one worst-case decision (spacing + 2 LLM attempts + settle ≈ 45 s): 0.56·T guard → ≤0.60·T settle. Design notes that pin "soft 0.60/hard 0.70" fail review arithmetic even though every expected episode is far shorter.
- **Speech-bubble geometry must be derived from the server's say cap measured in the drawing font**, not eyeballed: 160 runes did not fit 220px×4 lines (537 ellipsized remarks in the sixmax fixture); the ruling that held was shrinking the cap to 120 AND growing the bubble to 300px×6 with rune-boundary word splitting for spaceless CJK/emoji (which would otherwise trip never_inside at ~1600px). Fixture says must not end in the truncator's own ellipsis or "zero ellipsized" is unreachable.
- **A sandbox git credential can lack write access to a repo `gh repo create` just made** ("No anonymous write access" / "Invalid username or token"): push via the Git Data API (Contents-API bootstrap, then blobs/trees/commits/ref updates), seed the local→remote sha map before the first push (unseeded, it replays the whole history as duplicate-subject commits — fast-forward, benign, ugly), and expect API ref updates to *sometimes* not fire push-event CI: find runs by headSha, fall back to workflow_dispatch.
- **An episode-request whose sidecar routes to openrouter.ai returning 402 on every call is neither a coworld defect nor the Bedrock-capacity exception** — it is billing/routing, self-clears, and honest scripted fallback keeps episodes completing (`fallbacks == decisions` in results is the fingerprint; distinct contextual say lines are the recovery fingerprint). Cross-check two other LLM coworlds' logs in overlapping windows before attributing.
- **The atlas backlog reached 26 unplaced leagues**; dispatch 1 as probe / dispatch 2 with extra_cities from each run's own STATE.atlas worked, but prior runs' recorded spots collide with each other (three runs all recorded tabletop 766,277) — accumulate a local places.mjs and re-spot every collision (<20u) before building extra_cities, and place blocked runs' leagues too (build.mjs demands every league with stats).

## 2026-08-26 atari-cabinet

- **`upload-coworld --wait-hosted-smoke` structurally under-reports canonical**: it returns when hosted smoke passes, ~2 min before hosted certification flips the flag, so "Enforce canonical" fails on a value that is merely premature — on EVERY dispatch, not probabilistically (three in a row here; all three cows were canonical minutes later). The bump-and-redispatch advice in the phase-40 triage table cannot fix it. The fix that held: a "Confirm canonical" step between upload-coworld and secret put polling `coworld status <cow_id> --json` → `.coworld.canonical` (900 s bound). A raw urllib/curl GET to the observatory API from the GitHub runner HTTPErrors where the CLI's authenticated client works — poll through the CLI. Common-mistakes row added this commit; `templates/coworld-release.yml` should gain the same step (left for a human or the next template pass).
- **A dead session can leave finished work unreported: check the repo before re-dispatching a fixer.** The prior session died after its r1 fixer pushed 11 commits but before r1-fixes.md existed. The re-dispatched fixer found main already fixed, verified each commit against the review instead of duplicating, and wrote the report — brief future fixers with "if main is already past the reviewed sha, audit rather than redo".
- **The r1-2 fixture pattern is reusable**: for a sprite-baking (server-side text) renderer, CI probes the shipped text path by generating the worst-case packet from the real SimServer (`tools/ci/worst_case_frame.nim` through the real extract/parse/bound/apply path), baking it in the test job, and having the fixture page load the bundle's own JS + chrome CSS and transcribe baked geometry — `canvas text: 102 drawn, 0 ellipsized` where the shipped bundle's own smoke reads `total: 0` (Worker compositing).
- **Sidecar-402 round fingerprint confirmed a second time** (poker was the first): one round 100% scripted-fallback, openrouter 402s in the sidecar log, identical sidecar digest on the clean rounds before AND after — decisive in-coworld evidence that it is platform routing, no cross-coworld corroboration needed (the poker cross-check actually failed to corroborate and the verdict still held on the clean round).
- **Atlas backlog: verbatim adoption + self-respot is now the settled recipe.** Dispatch 1 failed naming 27 unplaced leagues, all with open queue-stuck PRs; dispatch 2 reused the newest PR's (poker 20533) added CITIES lines as `extra_cities` and re-spotted this run's own dot against a locally augmented places.mjs — which caught a real collision: atlas_spot.py against stale main proposed exactly cogolf's pending 202,270.

## 2026-08-26 liars-dice

- **Never run `gh auth setup-git` in this sandbox.** It rewrites `~/.gitconfig`'s `credential.https://github.com.helper` chain from `/usr/local/bin/git-credential-anthropic` to `gh auth git-credential`, after which every `git push` fails "Invalid username or token" while `gh api` keeps working — the failure looks like a token outage but is local config. Fix: `git config --global credential.https://github.com.helper /usr/local/bin/git-credential-anthropic` (drop the empty-string reset entry and the gist section setup-git adds).
- **Atlas backlog placements now diverge across queued PRs: check the league's own run first.** Two same-day runs placed atari-cabinet differently (its own run: paintlands 184,255 in PR 20548; this run's backlog repair: simulations 557,280 in PR 20567). Before spotting a backlog league yourself, read `runs/*/STATE.json` for that slug's own `atlas` block and reuse its coordinates verbatim — the game's own run made the continent rails call; a fresh guess from the league name double-places it and hands the merge-queue human a semantic conflict on top of the textual one.
- **Item-7 "tuned with a grid harness" is falsifiable and the sweep may really retune.** The design note's bayes thresholds (chal 0.40 / safe 0.55), defended by a two-point head-to-head test, ranked 80/110 on a real chal×safe lattice; the plateau centre 0.15/0.35 ranked 8/110 (tied with argmax). Run the lattice in phase 20 when the note pins scripted-baseline constants — treating them as facts cost a full phase-30 round, and the retune then falsified the note's own "tighter thresholds" rationale (recorded as design.md errata, which the judge accepted as sanctioned).
- **Verifier API drift, confirmed this run**: `GET /episode-requests?round_id=` 405s (use the nested `/rounds/$R/episode-requests`); `GET /leagues` and the division leaderboard return bare arrays, not `{entries:[]}`; a game's replay events may key on `kind` rather than `type` — the phase-60 prompt's `select(.type=="decision")` silently returns 0 and needs the game's own event grammar.

## 2026-08-26 goofspiel-oshi-zumo

- **`num_agents` at a variant's top level is rejected by the live upload schema** (`CoworldVariant` is `additionalProperties: false`; pydantic error `variants.N.num_agents — Extra inputs are not permitted`). It belongs only in `variants[].game_config` and `certification.game_config`. The design-note/playbook phrase "num_agents in every variant" misled the note into duplicating it; playbook §Phase 0/§Phase 1 now says game_config explicitly. Cost one release dispatch.
- **Recover atlas backlog coordinates from the newest open atlas PR instead of respotting.** Unmerged atlas PRs stack up (each run's PR waits on metta's merge queue), so every new dispatch fails on "unplaced leagues" naming every recent coworld. Fetch `places.mjs` from the newest open `atlas/*` branch (`gh api …/contents/...?ref=<branch>`), reuse its CITIES rows for the named slugs verbatim, spot only the genuinely new ones — and reserve the pending PRs' own dots (poker held 784,319) so parallel PRs don't collide when they all land.
- **…and check EVERY backlog slug against `runs/*/STATE.json` `.atlas` first — this run repeated atari-cabinet's double-placement the day after it was written up.** The atari-cabinet learning below this one already said it: a backlog league whose own run has an `atlas` block gets that block's coordinates verbatim. This run recovered 26 slugs from poker's PR but freshly spotted atari-cabinet (simulations 557,280 vs its own run's paintlands 184,255, PR 20548) and liars-dice (796,307 vs its own 799,301, PR 20567) because it checked only the newest PR branch, not the runs' STATEs. Mitigated with a reconciliation comment on PR 20600 naming the two corrections. The grep is one line: `jq -r '.atlas.pr_url // empty' runs/*/STATE.json` before spotting anything.
- **`GET /leagues` and `GET /policy-versions` return bare JSON arrays**, not `{entries:[…]}` — the 50/60 prompt jq shapes need `if type=="array" then . else .entries end`. Rounds/episode-requests still use `.entries`.
- **Round 1 auto-fires at settings time and fails if fillers aren't registered yet** ("Temporal RoundWorkflow failed before settling the round.", one entrant). Expected shape, doesn't count toward the 2-completed-rounds check; register fillers immediately after settings and before any submit to shrink the window.
- **Third-party players can join a public league mid-run** (relh and richard entered with their own uploaded policies, filled round 4's table so no Baseline seat was scheduled). Real entrants, `is_filler:false`, occupy leaderboard rows — the phase-60 leaderboard check must tolerate extra non-champion rows, and "fillers absent from leaderboard" stays true.
- **Renderer fixtures served by `python3 -m http.server` break viewer_smoke**: the harness installs its bridge stub in every frame, so the shell's own "missing ?replay=" error beats the fixture's verdict. Serve the bundle with a tiny server exposing a hanging `/hang` path and point the shell's `?replay=` there (`tools/ci/fixture_server.py`).
- Template deltas worth folding back (left in the coworld repo this run, noted for a human/template pass): `ci.yml` viewer smoke with `--soak 10`, a chrome-scope-check step, a renderer-fixture step; `docker_smoke.sh` validating results.json against the manifest's own `results_schema`; `coworld-release.yml` certify with `--timeout-seconds 300`.

## 2026-08-26 negotiation-games

- **Observatory list endpoints alternate response shapes within one session.** `GET /leagues` and `GET /rounds?league_id=` returned a bare JSON array at one poll and the `{"entries":…,"total_count":…}` wrapper at the next (observed 00:28Z vs 00:43Z same league). Every jq over these must be dual-shape: `if type=="array" then .[] else .entries[] end`. `GET /divisions/<id>/leaderboard` returns `null` (not `[]`) before the first completed round.
- **A design note can pin a test assertion its own pinned algorithms make unreachable.** The note pinned "hardliner-vs-hardliner ≥10 no-deals" AND a smallest-bundle-clearing-reservation offer rule AND last-turn reservation drops — jointly impossible (0 no-deals in 300 modelled matches). Resolution that worked: keep the pinned algorithms exactly, replace the assertion with the property it was reaching for (baselines measurably non-interchangeable), document the measurement in the test. Designers: sanity-check numeric test claims against the baselines' actual game theory before pinning both.
- **Atlas backlog repair: take the NEWEST atlas PR branch's places.mjs, not main, for everything.** With ~30 atlas PRs queued unmerged, main's places.mjs is far behind: (a) the unplaced-leagues failure needs extra_cities carrying every backlog league — copy their entries verbatim from the newest successful atlas branch (here PR 20600's); (b) your OWN spot must be computed against that same branch file — atlas_spot.py on main's file returned 416,574 which chemistry already holds in the full set. Respot before re-dispatching, not just re-pass extra_cities.
- **Renderer fixture in an iframe: two traps (general to any fork using one).** The shipped shell's own postMessage bridge fires `ready` and ends the viewer_smoke harness before the fixture drives its widths — the fixture must re-point the iframe's `window.parent` to swallow it. And canvas text counters recorded inside the iframe never reach the top document — install the fillText/strokeText measurer on the iframe's CanvasRenderingContext2D and publish the merged report as top-level `window.__coworldTextBounds`.
- **Template fold-back suggested (human): `templates/tools/ci/docker_smoke.sh` + SMOKE_CONFIG_JSON.** Any coworld whose cert fixture must stay tiny (60 s certify budget) cannot also satisfy a smoke-replay-longer-than-soak requirement from the same config. The builder added `SMOKE_CONFIG_JSON` (JSON merged over certification.game_config with num_agents/players/tokens stripped so the four seat invariants stay untouched) plus SMOKE_GAME_BIN/SMOKE_PLAYER_BIN for slugs whose entrypoints drop a suffix (`negotiation-games` → `/bin/negotiation`). Worth adopting into the template.
- **`git push` to a fresh Metta-AI cogame repo can be refused ("No anonymous write access") while the identical helper pushes coworld-builder fine** (second occurrence after ecos 2026-08-23). The Git Data API path (blobs → tree → commit → PATCH ref) works throughout; put it in every builder/fixer brief for the coworld repo up front.

## 2026-08-27 fog-of-war-boards

- **The atlas unplaced-set grows BETWEEN dispatches while parallel runs ship.** Dispatch 2 carried all 30 leagues from dispatch 1's error and still failed — trick-taking went live in the 4 minutes between them. Re-read the error's list on every retry and add the delta; with 3 runs in flight, budget the retries for it (this run used all 3 dispatches with zero mistakes of its own). Verbatim adoption from the newest atlas PR branch (goofspiel 20600) + fresh spots only for the genuinely new leagues worked exactly as the 08-26 learnings prescribe.
- **Worst-case renderer fixtures: pad to the cap with a benign multi-byte rune (e.g. U+00B7), never U+2026** — the smoke's trailing-ellipsis detector counts a literal-ellipsis-ending remark as truncated and the "zero remarks ellipsized" gate becomes unreachable. And assert the drawn string is EXACTLY the cap length, not ≥N: a ≥20 gate on an 80-rune band tests nothing (both were r1 blocking findings here).
- **Per-seat belief tables must be mutated only by that seat's own referee events.** `applyAttempt` cleaned a filled cell out of BOTH seats' sensed-empty tables — a tidy-up that silently told the non-actor about an opponent placement (its prompt list changed with no referee line). In any fog game, grep every write to a `perSeat[...]` structure and check the index is the acting seat.
- **In a sense-then-move variant, scripted baselines (and the fallback) must apply their own sense to a state copy BEFORE picking the move** — otherwise the same-ply revelation makes the pre-sense pick illegal at validation and the probe fallback repeats the identical illegal cell. Design notes should say this; the builder had to infer it (deviation 5, accepted).
- **Pinning "exactly N edits" to copied chrome regions makes the builder keep the starter's wrong words.** Babel's endcard hard-codes "N ROUNDS"/"LEADS THE TABLE"; the six-edit letter of the note preserved them over the note's own §Readouts wording ("SPROCKET CONNECTS", plies). Pin copied-region edits by purpose ("rename round vocabulary wherever the copied regions surface it") rather than by count.

## 2026-08-26 trick-taking
- A coordinator that dies inside a phase-30 fixer thread can leave the fixer's commits on the coworld repo with no `r<n>-fixes.md`. Before re-dispatching the round from scratch, read the repo's commit log since the reviewed sha: a verify-and-extend brief (list the landed fix commits, ask the new fixer to verify each and work only the remainder) saved a full redo here — 6 commits were already green.
- Staleness is adjudicated on the Asana `heartbeat_at` custom field, but a session can update STATE/log without the field (this run was adopted at field-age 184 min while STATE.heartbeat_at was 113 min old). Always PUT the Asana field in the same breath as the STATE heartbeat write, or the run looks dead 70 minutes early.
- Round 1 of a fresh league can auto-fire on champion submission before filler registration and fail with `Temporal RoundWorkflow failed before settling the round` — benign; the round you trigger after fillers supersedes it. Register fillers immediately after the second submit, before anything can fire.
- Observatory list endpoints are inconsistent about `{entries:[...]}` vs bare arrays (`/leagues` returned a bare array here; `/rounds` returned `entries`). Write every jq as `if type=="array" then . else .entries end`. The flat `/episode-requests?round_id=` route is 405; use the nested `/rounds/<id>/episode-requests`.
- Phase-60 check 5: Bedrock `429 ThrottlingException "Too many tokens per day"` is the same platform-capacity class as the prompt's named `LLM provider is unavailable` symptom — the judge upheld the exception given (a) another in-flight run's log showing the identical throttle, (b) a clean earlier round, (c) the designed degrade path handling it. Worth adding 429/ThrottlingException to the prompt's named symptoms.
- The atlas snapshot had fallen 31 leagues behind; one `extra_cities` dispatch can batch-place the whole backlog. When placing many dots in one continent, `atlas_spot.py` returns the same "roomiest" point every time — append each pending pick into your working copy of places.mjs before the next invocation so the picks avoid each other.

## 2026-08-27 board-gauntlet

- **Sandbox git push can break mid-session.** Pushes to github.com over HTTPS worked for the first ~20 minutes, then every push (coordinator and sub-agents alike) started rejecting with "Invalid username or token" while reads and `gh api` kept working. Fix: per-file writes via the contents API (`PUT /repos/<r>/contents/<path>` — fast) for coworld-builder, and the git-data helper `/workspace/push_via_api.py` for coworld repos. The helper mirrors the whole HEAD tree per call, so it is minutes-slow on a big repo — do NOT use it for coworld-builder; contents-API per changed file instead. Remote shas then differ from local: `git fetch && git reset --hard origin/main` after each push to stay in sync, and never expect local == remote history.
- **Observatory list endpoints return bare arrays**, not `{entries:[…]}` — `/leagues`, `/rounds`, `/policy-versions` all did. Guard every jq with `if type=="array" then .[] else .entries[] end`.
- **Unpausing a fresh league can fire an instant round that fails.** Sequence fillers → unpause → trigger produced round 1 `failed` ("Temporal RoundWorkflow failed before settling the round", entrant list held only champion 1 — it started at the unpause, before champion 2's membership settled) and a healthy round 2 from the explicit trigger. If round 1 fails but round 2+ is pending with both champions in `entrant_attributions`, keep going; nothing needs re-triggering.
- **`GET /divisions/<D>/leaderboard` returns `null`** until at least one round has completed — not an error, poll after the first completion.
- **Atlas debt accumulates.** 32 shipped coworlds had no `CITIES` line, so the first atlas dispatch failed wholesale. Placing many at once: run `atlas_spot.py` iteratively and append each chosen dot to a local copy of `places.mjs` before the next pick (the tool only avoids dots it can read), and re-pick YOUR slug's spot after the extras are placed — the spot picked earlier will have been consumed (board-gauntlet's first spot went to fog-of-war-boards). `extra_cities` takes `[[slug,label,x,y,region,null,"c"],…]`.
- **Design note as provenance ledger works.** Recording builder deviations (7 of them) in the phase-20 report and having the reviewer verify each against code collapsed phase 30 to one round: the only real code defect was the say-band ellipsis; everything else was note-staleness fixed by amending the in-repo note.

## 2026-08-27 magent-battle

- **The `canonical` read-race is structural, not warmth, for any game with multi-minute episodes.** `coworld[auth]==0.1.43` prints `Canonical:` from the upload response captured the instant hosted smoke passes (`upload.py:1477` in the 0.1.44 wheel); if episodes are long the flag always flips after that read, so bare version bumps re-race forever — magent-battle lost releases 0.1.0 and 0.1.1 to it and 0.1.1 was observed canonical:true minutes after its run reported false. Working fix, proven green in run 33060644278: a `Settle the canonical flag` step between `Upload the Coworld` and `Put the Coworld secret` that polls `GET /v2/coworlds` for the uploaded cow_id (15 s interval, 1200 s ceiling) and rewrites `upload.json.canonical` from the settled value — `Metta-AI/cogame-magent-battle` commit `ae59b75b`, copy it verbatim. **Template owner: fold this into `templates/coworld-release.yml`** — every future long-episode game hits it (knights-archers' "retry via bump anyway" row is this same race seen from outside).
- **A design note's controller heuristics need a measured sanity run, not just review.** The note's "occupancy is not consulted at decision time" rule deadlocked the whole game (advance/focus argmin always picked the enemy's own cell; every game ended 81v81, zero kills, tick cap). The builder measured before implementing and substituted snapshot-occupancy reads; reviewer reproduced the deadlock from the note's text. Design notes for order→controller games should state the intended emergent outcome (armies must reach contact) so a violation is testable, and the phase-20 brief should ask the builder to measure a scripted-vs-scripted episode's kill count early.
- **Trust transcription tests over a note's derived arithmetic.** The note said mapSize-31 spawns 25/army; upstream's own `generate_map` arithmetic gives 30 (the y-range was miscounted as 5 rows). The note's own "assert the number rather than trusting this paragraph" instruction made the fix mechanical (vendor/PATCHES.md #7).
- **Atlas: a league can become "unplaced" between two dispatches of the same run.** grf-football's league appeared in coworld-stats mid-phase-75 (its run was in flight at phase 20 — the league exists from the seed, not from rounds). Re-fetch nothing: just read the new failure's league list, place the newcomers with `atlas_spot.py` against the previous dispatch's augmented geometry, and re-dispatch. The knights-archers backlog trick (newest queued atlas PR's CITIES diff verbatim as `extra_cities`) covered 33 of 35; two were newer than every queued PR.
- **Observatory list-endpoint shapes are mixed:** `GET /v2/leagues` and `GET /v2/policy-versions` return bare arrays; `GET /v2/rounds?league_id=` returns `.entries`. Use `(.entries // .)` everywhere (phase-50/60 prompts' `.entries[]` on leagues fails as written).
- **`git push` basic-auth egress failure recurred** (knights-archers learning stands): Git Data API push with a Contents-API bootstrap for an empty repo's first object works; after an API push local shas diverge — `git fetch && git reset --hard origin/main` and report remote shas. Helper `/workspace/push_via_api.py` is per-sandbox, not committed; recreate from the knights-archers recipe when needed.
- **Two viewer polish items no gate covers, for the next ctf fork:** the endcard's dimmed background banner text can attribute the routed side wrongly when game 2's loser differs from the episode loser; and the status chip shows CONNECTING on the first drawn frame (loaded=true fires before the chip settles). Both cosmetic, both visible in screenshots, neither caught by viewer_smoke's DOM probes.

## 2026-08-27 grf-football

- **A lost seat-registration silently demotes a policy to the scripted default — with zero log signal.** In round 2, champion #2 (`counter:v3`, daveey-1) connected and joined but its register packet was never recorded: the seat played `zonal` for all 24 turns (`results.llmTurns [24,0,…]`, every directive `source:"scripted"` at `latency_ms:0`, 24 not 48 bedrock calls). Round 3 had 5/8 registers recorded and a filler seat mis-ran `zonal` instead of its assigned `gegenpress`. Phase-60 checks 4/5 are structurally blind to this whenever it misses the latest round — the judge ruled it non-blocking on the checklist's terms but the fix belongs in every server: **refuse to start (or log loudly) when a seat that should be LLM/scripted-X has no register record**; one log line would make check 5 catch it forever. Detector when auditing any replay: `llmTurns` per seat vs expected, and bedrock call count = seats × turns.
- **An orphaned builder thread can outlive its dead coordinator session by hours — check push cadence before dispatching a duplicate.** This run was adopted with a 182-min-stale heartbeat while the previous session's phase-20 builder was still pushing every ~10 min (and turned CI green itself 2 min after adoption). Monitoring instead of re-dispatching avoided a two-builder collision. The r1 fixer later coexisted with the same orphan by dropping its own duplicate fix and rebasing onto the orphan's superset commit. Rule of thumb: `gh api repos/<r>/commits` first; if the latest commit is minutes old, watch, don't dispatch.
- **The canonical read-race (magent-battle, same day) reproduced here verbatim** — 0.1.0 and 0.1.1 both lost to it; fixed with the confirm-canonical poll step between upload-coworld and secret put (cogame-grf-football `6c9962d`, same shape as magent-battle `ae59b75b`). Two runs in one day: `templates/coworld-release.yml` needs this step folded in (human).
- **After an API-helper push fails, never `reset --hard origin/main` in the same chain** — the `&&`-chained reset ate the un-pushed local commit and the log/STATE write had to be recreated from memory. Sequence: commit → loop{fetch, rebase, apipush} → **verify your commit is on origin** → only then reset.
- **With parallel runs, your slug may already be placed by another run's queued atlas PR.** grf-football's dot ("GRF Football",223,261,paintlands) shipped inside magent-battle's backlog PR #20631 before this run reached phase 75; our own dispatch failed on the 35-league backlog. Adopt the open PR (record its url in `STATE.atlas`, status `pr_open`) — a second PR carrying the same CITIES line just collides in metta's merge queue.

## 2026-08-27 smac-starcraft-micro

- **Hashing state the playback path never writes is the whole class of wasm-hash divergence.** `battleIndex` was mixed into `gameHash` but assigned only in the live server loop; every multi-battle replay diverged at the first battle boundary. The builder chased three floats first because each float removal *moved* the mismatch tick (it changed when battle 1 ends). Rule: any field mixed into the hash must be written by a proc called on BOTH record and playback (the same-proc principle already pinned for wall-clock stop records) — and a native test that re-derives a *multi-game* recording hash-for-hash catches it in CI, where the single-battle fixture cannot.
- **A gate that logs but cannot fail is worse than no gate**: `wasm_replay_smoke.cjs` printed the mismatch and exited 0 because the precompute scan's private ReplayPlayer found it while `smac_mismatch_tick()` read the display player, which never crossed the tick in 300 frames. If a check has two halves, expose both (sticky scanMismatchTick) and prove the gate can fail with a corrupt-fixture test.
- **fastMode + lobby join grace interact**: skipping the frame limiter once the first-connected seat is Ready burns a tick-denominated join timeout in wall-seconds, so a staggered pod start looks like a no-show (`player_error`, 1/5 hosted-smoke episodes). Pace at wall clock while `players < minPlayers`, fast-forward after.
- **Design-pinned repair tables must actually be routed**: "empty/missing cogs keeps last turn's directive; unmatched entry assigned by position" existed in the note but the code raised parse_error → retry → fallback, and the phase-60 zero-grep check caught it in the hosted log. Also: only the terminal degrade line may contain the phrase "falling back" — an attempt-1 interim message with that substring pollutes the grep even when the retry succeeds.
- **`GET /leagues?limit=200` returns a bare array**, not `{entries:[…]}` — `.entries[]` silently yields empty and the next PUT goes to `/leagues//divisions` (405 Method Not Allowed). Parse both shapes.
- **The unpause itself can fire a round instantly** (created the same second as `rounds-paused false`), and that round can fail with `Temporal RoundWorkflow failed before settling the round` even with fillers already registered; the explicitly triggered round seconds later succeeds. Treat a failed round-1-at-unpause as a race, not as missing fillers, when the filler POST verifiably preceded it.
- **Template deltas suggested**: (1) `coworld-release.yml` — a read-only bounded `Confirm the Coworld is canonical` poll after secret put absorbs the canonical completion race without spending a dispatch; (2) `viewer_smoke.mjs:425` probes `#feed,.feed,#log` but ctf-lineage feeds are `#killfeed`, so `feed_lines` is structurally 0 on paintbot-lineage coworlds.
- **Atlas backlog compounding**: 35 shipped-but-unplaced leagues blocked the build; the efficient path is reusing coordinates from the newest open atlas PR branch (they are consistent placements that will merge) and running atlas_spot only for leagues that went live since. Also re-run atlas_spot against the PR branch geometry for your own dot — main's roomiest point may already be taken in the queued PR (atari-cabinet held 202,270).

## 2026-08-27 rware-warehouse

- **Set fillers before the UNPAUSE, not merely before the explicit trigger.** Unpausing a fresh league auto-creates round 1 immediately (its `created_at` predated our filler POST by ~90 s) and it died with `Temporal RoundWorkflow failed before settling the round.` even though fillers were registered before our own trigger-round call. Order that works: divisions → settings → submit champions → filler-policies → rounds-paused false → trigger. The failed round is cosmetic (rounds 2+ complete cleanly) but it costs a round slot and a verify exclusion paragraph.
- **Observatory v2 response shapes are split by endpoint family:** `/leagues`, `/coworlds`, `/divisions/<d>/leaderboard` return bare arrays; `/rounds` and `/rounds/<id>/episode-requests` wrap in `.entries`; the flat `/episode-requests?round_id=` in prompts/60-verify.md is now 405 — use the nested `/rounds/<R>/episode-requests` route. Handle dual-shape client-side (`if type=="array" then .[] else .entries[] end`).
- **New cogame repos refuse plain `git push` from the sandbox helper** ("No anonymous write access" — helper is repo-scoped to coworld-builder). Don't burn time diagnosing: go straight to the `gh api` blobs→tree→commit→ref route (playbook §new-repo push); it preserves one-commit-per-finding fine. Also: the coordinator's own coworld-builder mount was in detached HEAD this run — `git push origin HEAD:main` is the fix, never a force.
- **The sandbox CAN run Nim.** nimby + Nim 2.2.4 install from the network and the full dependency tree syncs; the builder compiled and ran the whole test suite, a real 4-seat episode, and headless-chromium viewer smokes locally, going CI-green on the first push. Only Docker and emsdk are genuinely unavailable. Budget accordingly: local-first, CI as confirmation.
- **Port-fidelity reviews pay for themselves in fixture deltas.** Reordering one upstream line (request-queue refill computed after the delivered entry was cleared) was an invisible rules change that let a delivered shelf be re-requested on the forks and double-credited; fixture deliveries went 12→6 (honest) →23 (after the deliver-order fix). After any fidelity fix, re-record the fixture and re-sweep the baseline tuning — the swept pick moved too (yieldAfter 6→4).
- **Atlas backlog keeps compounding while metta's merge queue waits on humans** — 36 unplaced leagues this run (34 the same morning for magent). The harvest trick generalises: take the newest queued atlas PR's `places.mjs`, diff its CITIES rows against main, pass the missing set verbatim as `extra_cities`, and recompute your own spot against the PR's file so clearance is honest. One card per run is not filed for this; it is the queue working as designed.
