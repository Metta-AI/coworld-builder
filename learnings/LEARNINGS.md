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
