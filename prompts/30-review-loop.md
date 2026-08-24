# Phase 30 — Review loop

Purpose: drive reviewer → fixer → judge until an independent judge returns zero blocking findings.
Owner: coordinator, orchestrating three distinct sub-agents with distinct prompts and contexts.

## Inputs

- `STATE.repo`, `STATE.review_round`, `runs/<run>/design.md`.
- The repo diff against the starter, and `ci.yml` status.
- The ACCEPTANCE CHECKLIST below — the **only** definition of "blocking".

## Loop

```
round = max(STATE.review_round, 1)      # the STATE template initialises it to 0; a resume
                                        # straight into phase 30 must not write r0-*.md files
loop:
  reviewer -> runs/<run>/reviews/r<round>-review.md
  if the review has no findings: the judge still runs (an empty review is not a pass)
  fixer    -> commits per finding, CI green, runs/<run>/reviews/r<round>-fixes.md
  judge    -> runs/<run>/reviews/r<round>-verdict.md   (fresh context)
  if verdict.blocking == 0: exit loop
  round += 1
  if round > 4: log residue; continue to phase 40 ONLY if no blocking finding is in
       {hang, timeout, static-viewer, manifest, num_agents}; else phase 90
```

The judge never sees `r<round>-fixes.md` before forming its own read of the diff.

## Sub-agent briefs (self-contained)

**Reviewer** — neutral, never "find the bug":

> Trace the code at `<abs repo path>` against its design note at `<abs path to design.md>` and
> report what you observe. Cover: the resolution rules, the decision path (LLM call, parse,
> retry, fallback), every wait and its bound, string truncation, the replay writer, the viewer's
> re-derivation, the manifest, and the tests. For each observation give file:line, what the code
> does, and what the note says it should do. Do not propose fixes. Write
> `<abs path>/runs/<run>/reviews/r<round>-review.md`.

**Fixer**:

> For each finding in `<abs path>/runs/<run>/reviews/r<round>-review.md`, make the smallest correct
> change in `<abs repo path>` and push it as its own commit referencing the finding number. Do not
> weaken, skip, or delete a test to make it pass. `ci.yml` must be green on `main` when you finish.
> Write `<abs path>/runs/<run>/reviews/r<round>-fixes.md`: finding → commit sha → what changed →
> which acceptance-checklist item it satisfies. If a finding is wrong, say so with evidence rather
> than changing code.

**Judge** — fresh context, adversarial on the reviewer, authoritative on the checklist:

> You have not seen this repo before. Read `<abs repo path>` at `<sha>` and its design note at
> `<abs path>`. Then: (a) read `runs/<run>/reviews/r<round>-review.md` and try to **refute** each
> finding — a finding that cannot be reproduced from the code is dismissed; (b) independently
> evaluate the ACCEPTANCE CHECKLIST below, item by item, from the code, the CI logs, and the
> manifest. Write `runs/<run>/reviews/r<round>-verdict.md` ending with a machine-readable line
> `BLOCKING: <n>` and, for each blocking item, `- [<category>] <file:line> <one line>` where
> category ∈ {hang, timeout, static-viewer, manifest, num_agents, correctness, legibility,
> other}. **A checklist item you cannot verify from the tree or from cited CI evidence counts
> as blocking** — this is the only rule; `agents/judge.md` defers to it. Say what would settle
> it. Item 1's "no test loosened" is verified from `git log -p -- tests/` in the coworld repo,
> so it is verifiable: do not report it as unverifiable.
> Checklist: `<paste the ACCEPTANCE CHECKLIST verbatim>`.

**Verdict markers.** The verdict file carries the count **twice**: `blocking: <n>` as the *first*
line and `BLOCKING: <n>` as the *final* line. They must agree; if they disagree, treat the verdict
as malformed and re-run the judge. Both forms are deliberate (`agents/judge.md` writes both so
either end can be parsed) — do not "tidy" one away.

## ACCEPTANCE CHECKLIST — the definition of "blocking"

A finding is **blocking** if and only if it falsifies one of these. Everything else is advisory.

1. **CI green.** `ci.yml` conclusion `success` on `main` at the reviewed sha, with no test
   disabled, skipped, or loosened during this run. **Both halves are verifiable from the
   sandbox** — the conclusion from `gh run list -R <repo> --branch main -w ci.yml` (run id +
   conclusion, cited), and "no test loosened" from the coworld repo's own history:
   ```bash
   git -C <repo path> log -p --since="<run start>" -- tests/     # every test-file change this run
   ```
   Read those hunks: a deleted assertion, a widened tolerance, a `skip`/`t.Skip`/`xfail`/`--skip`
   added, or a test file removed is a blocking finding. There is no CI-history access needed and
   no excuse for reporting item 1 unverifiable.
2. **Replay re-derivation.** Replaying the recorded events through the sim reproduces the recorded
   per-tick state **frame by frame**, and the viewer derives its display from that same
   re-derivation — not from a parallel recording. A test asserts it.
3. **Static viewer.** `coworld_manifest_template.json` declares
   `"replay_viewer": {"bundle": "static-replay-viewer"}`, `tools/build_replay_viewer.sh` exists and
   is wired as the `coworld build` hook, and the viewer contacts nothing but S3. No
   `/client/replay` pod path anywhere. *(category: static-viewer)*
4. **Both name spaces.** Agents see anonymous cog aliases only; the viewer maps aliases to real
   player names for non-baseline seats. Both present.
5. **Degrade-never-hang.** Every wait (LLM call, seat reply, round barrier) has an explicit bound;
   the episode settles and scores inside **60 %** of `episodeTimeoutSeconds` (720 s of 1200);
   there is no unbounded loop or blocking read. *(categories: hang, timeout)*
6. **`num_agents`** present in **every** manifest variant **and** in the certification fixture.
   `tools/ci/docker_smoke.sh` enforces four seat-count invariants before any container starts —
   `certification.game_config.num_agents` present; a positive integer; `len(certification.players)`
   equal to it; `len(certification.game_config.players)` equal to it — and `SMOKE_SEATS` (the
   `<SEATS>` substitution, taken from the design note) is an independent **second declaration** that
   must agree with the manifest. Every violation exits non-zero with a message prefixed
   `SEAT-COUNT FAIL:`, so the job is already red. **`SEAT-COUNT FAIL` anywhere in the docker-smoke
   log is a blocking finding** — grep for it rather than trusting the job's colour, which is what
   catches a rerun with the job made non-required, or a log from a branch whose CI was skipped.
   *(category: num_agents)*
7. **Scripted baseline plays full episodes legally.** A test runs an all-scripted episode to the
   natural end, asserts `results.reason == "complete"`, and asserts every order/action is inside
   its legal bounds. The baseline's parameters were tuned with a grid harness, not guessed.
8. **LLM reply handling.** Parsing is tolerant (accepts surrounding prose, extracts the JSON
   object), retries **once** on a parse or transport failure, then falls back to the scripted move
   — and the fallback is recorded so phase 60 can count it.
9. **Rune-safe truncation.** Every string that reaches the replay (`say`, `notes`, prompts,
   captured errors) is truncated on **rune** boundaries. A test feeds multi-byte input at the cap
   and asserts the output is valid UTF-8.
10. **Manifest validates.** `game.docs` is
    `{"readme":{"type":"text","value":…},"pages":[{"id","title","content":{"type":"text","value":…}}]}`
    and `game.protocols` carries **both** `player` and `global`. *(category: manifest)*
11. **Viewer legible at 360 px.** The scorebug's player names do not collapse at the embedded
    featured-match width: `.plate-name { flex: 1 1 auto; min-width: 3.2em; }`, labels hidden under
    `640px`. *(category: legibility)*
12. **Release order and scaffold.** `coworld-release.yml` runs build → certify →
    **upload-policies** → upload-coworld → secret put, in that order, and any smoke step depends on
    a freshly built binary in the same run. All three workflows are present, `tools/ci/docker_smoke.sh`
    is present and executable, `tools/ci/policies.json` defines **at least four distinct policies —
    two LLM prompt champions (`PLAYER_PROMPT`) plus ≥1 scripted filler (`PLAYER_SCRIPTED=<name>`),
    normally 2** — with champion #2 (the second `PLAYER_PROMPT` entry) carrying
    `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, and this gate exits 0:
    ```bash
    if grep -n '<slug>\|<IMAGE>\|<SEATS>' \
      .github/workflows/ci.yml .github/workflows/coworld-release.yml \
      .github/workflows/coworld-submit.yml tools/ci/docker_smoke.sh tools/ci/policies.json
    then echo "::error::unsubstituted placeholders remain"; exit 1; fi
    ```
    Grep for those **three names only** — never a bare `<`. Substitution is global and deliberately
    includes comments, so four angle-bracket names survive by design and are runtime values, not
    residue: `<cow_id>`/`<sha>` in `ci.yml`'s static-replay-route comment, `<run_id>` in the
    artifact-readback recipes in `coworld-release.yml` and `coworld-submit.yml`, and `<name>:vN` in
    `coworld-submit.yml`'s `policy` input description. `templates/README.md` lists them as expected
    residue — do not file them as findings.
    *(category: manifest)*

13. **Viewer executes.** *(category: static-viewer)* Not "the bundle builds" — the bundle
    **runs**.
    - `ci.yml`'s `wasm-viewer` job is green on `main` at the reviewed sha **including its
      `Load the bundle in a real browser` step** (`tools/ci/viewer_smoke.mjs`, headless chromium,
      loading the replay `docker-smoke` produced). Cite the run id and confirm the step ran — a
      job green because the smoke step is absent, commented out, or `continue-on-error` is a
      blocking finding, and so is a `wasm-viewer` that does not `needs: docker-smoke`.
    - `index.html` / `static_replay*.js` set `data-replay-loaded="true"` on `<html>` on the
      **first drawn frame** and `data-replay-error="<message>"` on failure. Both markers, both
      set from the shell's own code paths.
    - The emscripten link flags in `replay-viewer/config.nims` (`-s MODULARIZE=1`,
      `-s EXPORT_NAME=<X>`) and the bootstrap in the worker/shell come from the **SAME starter**.
      Read both and check they agree:
      a shell that waits for `Module.onRuntimeInitialized` against a `MODULARIZE=1` build is
      **blocking** (the factory is never called, nothing throws, the page hangs forever), and so
      is a shell that calls a factory `<X>(...)` that a non-`MODULARIZE` build never defines.
      This is the cogame-lantern deadlock of 2026-08-23 verbatim: paintbot's bootstrap spliced
      onto babel's link flags, every file present, every asset 200, `tell("ready")` in the JS,
      and "Loading replay…" on softmax.com forever. **File presence is not evidence here; the
      smoke's `loaded: true` is.**

14. **Chrome is the starter's, not a lookalike.** *(category: static-viewer)* Id-presence is not
    evidence — cogame-gridlock (2026-08-23) shipped a 329-line `client/replay_broadcast.html`
    written from scratch that reused every starter id and passed the id test, and the operator's
    first look was "looks like not all the elements were ported over". Check provenance:
    - `client/chrome_common.js` is **byte-identical** to the starter's (`diff` it against
      `/workspace/starters/<starter>/client/chrome_common.js`); the only admissible change is a
      named, minimal patch recorded in the design note (e.g. hive's clickable beat markers).
    - `client/replay_broadcast.html` is the starter's page with a game block appended under a
      banner comment (`<SLUG> additions to the inherited <starter> chrome`). Diff the CSS above
      that banner against the starter's: sections 1–5 (stage, scorebug, banner lane, kill feed,
      transport, scrubber + momentum graph + beat markers + lulls + spoilers, endcard, locker-room
      curtain) are present and unmodified except for the removals the note lists. A page a
      fraction of the starter's size is a rewrite and is blocking.
    - **Transport rules**, each checked in the page: (a) `relayout()` measures `#transport` and
      sets `--band` (and `--hudscale`) on `document.documentElement` — the variables `--u` and
      `#board`/`#endcard` read are computed on `:root`, a value on `#stage` never reaches them;
      (b) nothing fixed-positioned (nameplates, counters, feeds) sits inside the band — they ride
      `bottom: calc(var(--band, 0px) + …)`; (c) `#endcard` keeps `bottom: var(--band, 0px)`, is
      shown with the class its CSS rule uses (`#endcard.on`), and **every seek** — scrub click,
      beat marker, back/forward, keyboard — takes it down, so the scrubber can always pull the
      match back from the score screen; (d) scrubber beats are labelled `<button>`s that seek to
      their tick (`chrome_common.markBeat(tick, kind, team, label)`), with CSS for every kind the
      page emits — a kind with no rule is an invisible marker.
    - **Zoom bar + minimap (`#viewpanel`) only if the board is pannable.** A game whose whole
      arena fits the frame (raid, hive, gridlock) removes the panel — markup, CSS, the
      `core.zoomAt/setZoom/attachMinimap` wiring, and the ids from the test list — rather than
      hiding it. Keep it only when the design note says the board is larger than the viewport.

15. **Every drawn string fits its frame.** *(category: legibility)* A canvas accepts a draw at a
    negative coordinate without complaint, so text with nowhere to go is invisible to the load
    signal, to the soak, and to a screenshot. cogchemists (2026-08-24) drew each seat's speech
    bubble upward from the top of its cog, and the cog sat at the top of the arena: every bubble
    body landed at a negative y and four sentences rendered as four white slivers. Everything was
    green.
    - `tools/ci/viewer_smoke.mjs` reports `canvas_text: {total, outside, never_inside,
      ellipsized}` in `viewer-smoke.json`. The gated number is **`never_inside`** — strings that
      crossed an edge on *every* draw and never once landed inside. `outside` counts draws and is
      reported only: an entrance animation that slides a card on from off-frame is legitimately
      outside for a few frames, and gating on that fires on healthy viewers. For a **fixed
      arena** — any board that wholly fits the frame — `never_inside` must be **0**, and
      `ci.yml`'s smoke step must carry `--strict-text-bounds` so a regression is red rather than
      merely logged. A pannable board parks text off-frame legitimately; there the flag is dropped
      and the number is read, not gated. `total: 0` means the check covered nothing (a
      worker/OffscreenCanvas or WebGL renderer) and is not evidence of anything.
    - Any text laid out **relative to another element** — a speech bubble over a cog, a callout on
      a card, a floating damage number — gets a **reserved band in the layout**, sized from the
      cap the server enforces on that string (`MaxSayLen` and its kin) and measured in the font it
      will be drawn in. Sizing by eye, or letting the bubble grow into whatever happens to be
      above it, is the bug above. The band is reserved whether or not anything is speaking, so the
      scene does not jump when a remark lands.
    - Ellipsis is a design choice for **labels** (a card name in a 52 px card) and a defect for
      **sentences**. If `ellipsized` counts a remark rather than a nameplate, the box is too small
      — widen the band, do not shorten the text.
    - **The CI replay cannot talk.** `docker_smoke.sh` runs without an `ANTHROPIC_API_KEY`, so
      every seat falls back to the scripted baseline, and a scripted baseline emits no `say` and
      no `notes`. **Every replay CI can produce carries zero LLM text**, so `viewer_smoke.mjs` on
      that replay never draws a speech bubble, a remark feed line, or a notes panel — the whole
      class of chrome that exists only to show what a model said is untested by every gate above.
      cogchemists' bubbles shipped clipped with a fully green board for exactly this reason.
      A repo whose viewer draws LLM-authored text must therefore ship a **worst-case renderer
      fixture**: a page that loads the real `client/renderer.js`, hands it a frame built to hurt
      (a full-cap remark on *every* seat at once, the tallest station block, an entrance
      animation played through to settle), renders it at several canvas sizes, sets
      `data-replay-loaded`, and is driven by `viewer_smoke.mjs --strict-text-bounds` in its own
      `ci.yml` step. The fixture asserts its own strings are still full-length — one quietly
      shortened remark leaves it passing while testing nothing. Cite the step and its
      `canvas_text` line; a repo that draws model text and has no such fixture is a blocking
      `legibility` finding.

Additionally, for simultaneous-decision games: all seats' LLM calls go out as **one parallel batch
per turn**. Sequential calls are a blocking `timeout` finding.

## Exit criterion

A `r<round>-verdict.md` whose first line is `blocking: 0` and whose last line is `BLOCKING: 0`
(the two must agree; a mismatch is a malformed verdict — re-run the judge). Or: round 4 exhausted with residue whose
categories are all outside {hang, timeout, static-viewer, manifest, num_agents} — residue logged in
`log.md` and commented on the run task.

## Writes

- `runs/<run>/reviews/r<n>-{review,fixes,verdict}.md`.
- STATE: `review_round`, `phase: "40"` on success, `heartbeat_at`. On exhaustion STATE.phase stays `"30"` (phase 90 records the failed phase in `STATE.blocked.phase`; `STATE.phase` is never `"90"`).
- Asana: complete the phase-30 subtask; comment with the round count and any residue.

## Retry budget

4 rounds, hard. A sub-agent that fails to produce its file gets 3 retries within its round before
that round is declared failed. Residue containing a blocking finding in {hang, timeout,
static-viewer, manifest, num_agents} → `prompts/90-blocked.md`.
