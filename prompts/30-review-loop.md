# Phase 30 — Review loop

Purpose: drive reviewer → fixer → judge until an independent judge returns zero blocking findings.
Owner: coordinator, orchestrating three distinct sub-agents with distinct prompts and contexts.

## Inputs

- `STATE.repo`, `STATE.review_round`, `runs/<run>/design.md`.
- The repo diff against the starter, and `ci.yml` status.
- The ACCEPTANCE CHECKLIST below — the **only** definition of "blocking".

## Loop

```
round = STATE.review_round (starts 1)
loop:
  reviewer -> runs/<run>/reviews/r<round>-review.md
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
> other}. A checklist item you cannot verify counts as blocking.
> Checklist: `<paste the ACCEPTANCE CHECKLIST verbatim>`.

**Verdict markers.** The verdict file carries the count **twice**: `blocking: <n>` as the *first*
line and `BLOCKING: <n>` as the *final* line. They must agree; if they disagree, treat the verdict
as malformed and re-run the judge. Both forms are deliberate (`agents/judge.md` writes both so
either end can be parsed) — do not "tidy" one away.

## ACCEPTANCE CHECKLIST — the definition of "blocking"

A finding is **blocking** if and only if it falsifies one of these. Everything else is advisory.

1. **CI green.** `ci.yml` conclusion `success` on `main` at the reviewed sha, with no test
   disabled, skipped, or loosened during this run.
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
    is present and executable, `tools/ci/policies.json` defines five distinct policies with champion
    #2 carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, and this gate exits 0:
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

Additionally, for simultaneous-decision games: all seats' LLM calls go out as **one parallel batch
per turn**. Sequential calls are a blocking `timeout` finding.

## Exit criterion

A `r<round>-verdict.md` whose first line is `blocking: 0` and whose last line is `BLOCKING: 0`
(the two must agree; a mismatch is a malformed verdict — re-run the judge). Or: round 4 exhausted with residue whose
categories are all outside {hang, timeout, static-viewer, manifest, num_agents} — residue logged in
`log.md` and commented on the run task.

## Writes

- `runs/<run>/reviews/r<n>-{review,fixes,verdict}.md`.
- STATE: `review_round`, `phase: "40"` (or `"90"`), `heartbeat_at`.
- Asana: complete the phase-30 subtask; comment with the round count and any residue.

## Retry budget

4 rounds, hard. A sub-agent that fails to produce its file gets 3 retries within its round before
that round is declared failed. Residue containing a blocking finding in {hang, timeout,
static-viewer, manifest, num_agents} → `prompts/90-blocked.md`.
