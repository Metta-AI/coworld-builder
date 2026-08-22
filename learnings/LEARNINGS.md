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
