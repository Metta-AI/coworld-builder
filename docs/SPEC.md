# coworld-builder — specification

The decided design. Prompts, templates, and agents are written against this document; change
it first, then them.

## Mission

A managed agent takes one **Coworld Idea** (Asana project `1217704774784096`, "Coworld Ideas")
and carries it to **done**: a public `Metta-AI/cogame-<slug>` repo, a certified coworld on
softmax.com, a league with two ranked champions and fillers, ≥2 completed rounds with valid
replays rendered by a **static** viewer on `https://softmax.com/<slug>`, an announcement in
Discord `#coworlds`, and a dot on the Softmax Atlas (`https://softmax.com/atlas`). When it cannot, it marks the run **Blocked** with a subtask for a human
that names exactly what is needed, and exits.

## Runtime

- **Anthropic Managed Agents**, one *coordinator* agent (`claude-fable-5`, effort xhigh) with a
  `multiagent: coordinator` roster of fixed-role sub-agents (`claude-opus-5` xhigh, except the
  judge = `claude-fable-5`). Deployed with the `fleet/bin/fleetctl.py` conventions from
  `daveey/cogamer` — git is the source of truth (`agents/*.json` + `agents/*.md` + `AGENT.md` +
  `fleet/deployment.json`), applied out by `fleet/bin/deploy.py`. There is **no `fleet/mirror/`
  export and no `diff` here**: `deploy.py` has `create`, `update`, `run`, `status` only, and
  `update` is what reconciles live with git. (fleetctl's mirror/diff pair is a cogamer-fleet
  steward duty, not a duty of this repo.)
- **Three deployments, hourly crons staggered 20 minutes apart** (`coworld-builder-a` at minute
  11, `-b` at 31, `-c` at 51 UTC — `fleet/cloud.md` §Parallelism, applied from
  `fleet/deployment.json`'s `deployments` list). They are three crons on the **same** coordinator
  agent, not three different agents. **Several runs in *Running* at once is the normal state**,
  bounded by `max_parallel_runs` (`fleet/cloud.md` §Parallelism, currently 3). Every firing is a
  *heartbeat*:
  1. Run the tool preflight (`prompts/00-claim.md` step 0), then read the **Coworld Builder**
     board (the Coworld Builder gid in `fleet/cloud.md`; it is a table row, not an environment
     variable) and compute `live` = the number of runs in *Running* whose `heartbeat_at` is
     **fresh** — < 180 min old **and** with no `STATE.session_ended_at ≥ heartbeat_at`. That is
     exactly the existing freshness rule; only what is done with it changed. A fresh run belongs
     to a session that is still working it: never touch it.
  2. Then adopt **at most one** unit of work, in this order — (a), (b), (c), else (d):
     **(a)** a run in *Running* with a **stale** heartbeat, **or** with a fresh heartbeat whose
     `STATE.session_ended_at` is ≥ `heartbeat_at` (the last session ended cleanly and said so),
     → it is yours: **resume** at `STATE.json.phase`. Without that marker a run that needs more
     than one session would look alive for the full 180 minutes after its session died, and — the
     crons being hourly — would advance only on the next deployment's firing.
  2a. **Every resume — from (a) or (b) — is guarded by a session nonce.** Two heartbeats
     can observe the same free run in the same minute (two crons 20 minutes apart plus a manual
     `deploy.py run`, or a retried deployment run). The parallel crons do **not** need a new
     mechanism: the existing claim and resume races already decide who owns a unit of work, and
     the loser exits having written nothing.
     The resuming session mints a nonce, writes it as `STATE.session_id` with
     `heartbeat_at`, logs `00 resume at phase <n> attempt=<k> session=<nonce>`, pulls and pushes;
     a **rejected push** means it rebases (aborting and exiting on a conflict) and exits if
     `log.md` now contains any `00 resume` line with a foreign nonce that was not there before
     its pull — never "the last line", which after a rebase is its own (never force — the same
     rejected-push rule covers claims and resumes). It
     then re-GETs the Asana `heartbeat_at` custom field after 20 s and exits if the value moved
     past its own stamp. Only a session that survives all three checks works the phase.
     (`prompts/00-claim.md` step 5.0.)
     **(b)** else a run task in *Blocked* whose `STATE.blocked.subtask` is complete → move it to
     *Running* and **resume** (through the same step 2a guard).
     **(c)** else, **if `live` < `max_parallel_runs` and fewer than 2 runs are *Blocked***, claim
     the top **unclaimed, incomplete** Coworld Idea (board order; skip ideas that
     already have a run task), create the run task, and start at phase 00 — the existing
     comment-first claim and SKIPPED rules, unchanged.
     **(d)** else **exit**, appending one line to the shared `runs/heartbeats.log`:
     `<UTC> heartbeat: cap reached (live=<n>/<max>)` when the cap is what stopped it, otherwise
     `<UTC> heartbeat: nothing to do`. (The 2-Blocked bound keeps its own
     `<UTC> 00 idle: <n> blocked runs, not claiming` line.)

     A *Blocked* run whose subtask is still open does **not** stop (c): the queue keeps moving,
     bounded at **2 simultaneously-Blocked runs** — at 2, the heartbeat claims nothing and exits.
     An idea the coordinator **cannot start** is **SKIPPED**, not Blocked: its text is marked
     confidential (a public repo would publish it), or it cannot be mapped to any starter and the
     gap is one §Rails calls a human decision. A SKIP is one
     `skipped by coworld-builder: <reason>` comment on the idea task, the gid appended to the
     committed `runs/SKIPPED.json`, and one card in the Builder board's *Fleet* section assigned
     to David Bloomin titled `SKIPPED <idea title>: <reason>` (one per idea, deduped by title);
     the heartbeat then **continues to the next idea**. Step (c) skips gids listed in
     `runs/SKIPPED.json` and ideas already carrying that comment, so a skipped idea never stalls
     the queue. Phase 90 is **never** entered here: it needs a run task and a STATE, and at this
     point neither exists.
  3. Write `heartbeat_at` on the run task + `runs/<run>/STATE.json` at least every 15 minutes
     of work, and on every phase transition. Write `STATE.phase` — committed and pushed — at the
     moment of **every** phase transition, **before** the new phase's first sub-agent is
     dispatched (§State).

- The sandbox has **no Docker, no Nim, no emsdk**. Every compile / image / certification /
  upload step runs in **GitHub Actions inside the coworld repo** from templates in this repo.
  The agent pushes, dispatches workflows (`gh workflow run`), polls (`gh run watch`), and
  reads logs. CI credentials are repo secrets `SOFTMAX_TOKEN` and `ANTHROPIC_API_KEY`, propagated onto each coworld repo by dispatching `propagate-secrets.yml` in `Metta-AI/coworld-builder` (`gh workflow run propagate-secrets.yml -R Metta-AI/coworld-builder -f repo=cogame-<slug>`; it runs with a user token that is admin on Metta-AI repos — no org admin, no value ever in the sandbox).
- Everything else (Observatory API, `softmax.com`, Asana, Discord, GitHub) is HTTPS from the
  sandbox using vault credentials substituted at egress (`SOFTMAX_TOKEN`, `GH_TOKEN`,
  `ASANA_PAT`, `DISCORD_BOT_TOKEN`, `GEMINI_API_KEY` — the last for nano-banana board art, see
  `playbooks/art-nanobanana.md`).
- Repos mounted (declared in `fleet/deployment.json`): this repo (read-write,
  `/workspace/coworld-builder`), `daveey/cogamer` (read, `/workspace/cogamer`, for
  `fleet/PROTOCOLS.md`), and all six starters read-only at **`/workspace/starters/<name>`**:
  `cogame-babel`, `cogame-bullwhip`, `cogame-parley`, `coworld-ctf`, `cogame-moba`,
  `cogame-factorio`. Phase 10 reads the mounts; phase 20 still `git clone`s the chosen starter
  into the new repo's working tree so the new repo gets a clean history.

### Parallelism and per-run isolation

Runs are isolated by construction: each has its own `runs/<run>/` directory, its own Asana run
task, its own `Metta-AI/cogame-<slug>` repo, its own league, division, champions and fillers.
Nothing in a run's working set is shared with another run. The only shared surfaces are:

- `runs/heartbeats.log` and `runs/SKIPPED.json` — the two append-only files at the root of
  `runs/` (`AGENT.md` hard rule 7). Every write is `git pull --rebase` → append → push, never a
  rewrite of existing lines, so two heartbeats appending in the same minute merge cleanly.
- the **Coworld Ideas** board — arbitrated by the comment-first claim (§Runtime step (c)).

**Bedrock capacity is the real shared resource.** Parallel runs contend for it, and the symptom
is `LLM provider is unavailable` in the hosted game log at phase 60. Rail: if that string is
platform-wide — seen across **two runs at once**, or in another LLM coworld's latest log — the
run **waits** (polling inside the existing 75-minute bound of phase 60) rather than going
*Blocked*; a capacity squeeze is not a defect in the coworld. If the 75 minutes expire it is a
platform outage and phase 90 applies as before. `max_parallel_runs` in `fleet/cloud.md`
§Parallelism is the throttle an operator lowers when contention is the cause; lowering it stops
new claims and leaves runs in flight alone.

## Phases

| # | prompt | owner | produces | done when |
|---|---|---|---|---|
| 00 | `prompts/00-claim.md` | coordinator | run task (+ one subtask per phase), `runs/<run>/STATE.json`, `log.md` | task in *Running*, STATE written |
| 10 | `prompts/10-design.md` | designer → coordinator | `docs/plans/<date>-<slug>-design.md` in the new repo, with the eight H2 sections `prompts/10-design.md` names, in that order: `## The game`, `## Decisions: LLM with scripted fallback`, `## Sim module`, `## Server, player, protocol`, `## Viewer`, `## Packaging`, `## Tests`, `## Out of scope (v1)` | coordinator accepts the note against the checklist in the prompt |
| 20 | `prompts/20-build.md` | builder | the repo: sim/llm/server/player, viewer, manifest, CI templates, tests, README; CI green | `ci.yml` green on `main` |
| 30 | `prompts/30-review-loop.md` | reviewer → fixer → judge | review reports under `runs/<run>/reviews/`, fixes pushed | judge returns **zero blocking findings** (max 4 rounds; residue logged) |
| 40 | `prompts/40-release.md` | builder (CI) | `coworld-release.yml` run: build → certify → upload-policies → upload-coworld (wait hosted smoke) → secret put | coworld **Canonical: yes**, hosted certification certified |
| 50 | `prompts/50-league.md` | coordinator | league seed, division, settings, champion #1 (daveey), champion #2 (daveey-1), fillers, unpause, trigger | both champions show as entrants; round triggered |
| 60 | `prompts/60-verify.md` | verifier → judge | `runs/<run>/VERIFY.md` with fetched evidence | the *definition of done* checklist all-true |
| 70 | `prompts/70-announce.md` | coordinator | Discord message id | message posted, id in STATE |
| 75 | `prompts/75-atlas.md` | coordinator | one PR against `Metta-AI/metta`: the coworld's `CITIES` line in `places.mjs` + the regenerated `public/atlas/index.html` | `STATE.atlas.status` is `pr_open`, `already_placed` or `unplaced` |
| 80 | `prompts/80-close.md` | coordinator | executive summary on run task + idea task, `learnings/LEARNINGS.md` entry, run task → *Done*, idea task completed | — |
| 90 | `prompts/90-blocked.md` | coordinator | run task → *Blocked*, subtask → human, STATE.blocked | used by any phase on exhausting its retry budget |

Retry budgets: each phase may retry its own failing step 3× (with a different approach each
time, logged) before going to 90. **Phase 75 is the one phase that never goes to 90**: a shipped,
announced coworld must not sit in *Blocked* holding a `max_parallel_runs` slot over a missing dot
on a map, so an exhausted atlas phase files a Fleet card, records `atlas.status: "unplaced"`, and
continues to 80, which names it. Phase 80 (close) is retried across heartbeats without counting,
but after 3 `close-failed` heartbeats it too goes to 90 so a run can never sit in *Running*
forever and stall the queue. The resume counter (`prompts/00-claim.md` step 5.1) counts
only sessions that ended **without progress**: a closing step that recorded a
`progress phase=<nn> marker=<value>` line in `log.md` resets `phase_attempts[<nn>]` to 0, and
phase 80 is exempt from the counter entirely (a failed close never goes to 90). Phase 30's loop cap is 4 rounds. Phase 60's wait for rounds
is bounded at 75 minutes of wall clock.

## Definition of done (phase 60, all fetched, never assumed)

1. `GET /rounds?league_id=` → ≥2 rounds `completed` (not failed/discarded) after the fillers
   were set.
2. `GET /divisions/<div>/leaderboard` → both champions ranked (daveey, daveey-1), fillers absent
   or labelled Baseline.
3. Latest round's episode request (`GET /episode-requests?round_id=`) `completed` with a
   `replay_url`; participants named correctly.
4. Replay bytes fetched from S3: **valid UTF-8 JSON**, `protocol` matches, `results.reason`
   is `complete` (or a `deadline` that the design declares acceptable), events show the
   champion seats *doing the thing the game is about* (LLM games: non-scripted decisions with
   non-trivial content; not all fallbacks).
5. Hosted game log (`/episode-requests/<id>/artifacts/logs`, elevated header): zero lines
   matching `falling back|LLM provider is unavailable|cut off at max_tokens|rejected` —
   or a documented platform-wide cause checked against another LLM coworld.
6. `https://softmax.com/<slug>` page fetched: featured match present; the replay iframe `src`
   is `/v2/coworlds/replays/static/<cow_id>/<sha>/index.html?replay=<s3 url>` (never a
   `/client/replay` pod URL).
7. Certification output contains `Replay liveness: skipped (static replay bundle declared` —
   read from the committed `runs/<run>/release-result.json` (phase 40's artifact copy).
8. The viewer **actually renders**, proven by executing it, and the verifier's **spectator
   judgment** (a short paragraph) written from what it drew. The sandbox has no screen, so the
   verifier dispatches `.github/workflows/viewer-check.yml` in coworld-builder against the check-6
   iframe `src`; that job opens the live bundle in headless chromium (Playwright, pinned 1.55.0)
   and runs `templates/tools/ci/viewer_smoke.mjs`. Item 8 is true only when **all three** hold:
   (a) **`loaded: true`** — the viewer drew a frame and signalled it, via
   `data-replay-loaded="true"` on `<html>` or the `coworld-replay` postMessage bridge's `ready`.
   `data-replay-error`, a bridge `error`, or silence until the timeout is a FALSE item. Assets
   that all return 200 are **not** evidence of this and never were: cogame-lantern (2026-08-23)
   had a complete, all-200 bundle whose viewer deadlocked forever;
   (b) **the replay advances** — the clock text differs across the three scrub readouts (0 %,
   50 %, 100 %) recorded in `viewer-smoke.json`. A frame that renders once and freezes is a
   failure;
   (c) **the judgment paragraph** — legible, and it shows the game — written from
   `viewer-smoke.png`, the clock/scorebug/feed readouts, and the replay JSON's events reconciled
   against them. The evidence (`viewer-smoke.json` + `viewer-smoke.png`) is committed under
   `runs/<run>/viewer-check/`.

## Design pins every coworld inherits (from the make-coworld playbook)

Starter by game shape (parley/babel for LLM-prompt games; coworld-ctf for ANY real-time loop —
grid or continuous physics — with new rules; cogame-moba only for bit-exact ports of an existing
external env; cogame-factorio for external engines). Public repo
`Metta-AI/cogame-<slug>`. LLM policy **and** scripted baseline from day one (same image,
env-switched). Static wasm replay viewer — never a pod. Real art, the starter's chrome
verbatim. Two name spaces (anonymous cog aliases in-game; policy names spectator-side).
Degrade-never-hang (assume `episodeTimeoutSeconds` 1200, play inside 60 % of it).
`num_agents` in every variant and the cert fixture. Upload policies **before**
`upload-coworld`. Secret put **after** it. Filler versions ≠ champion versions. Fillers set
**before** the first `trigger-round`. Champion #2 uploaded while `daveey-1` is the active
player. **Both champions are LLM prompt policies** (`PLAYER_PROMPT`), champion #1 owned by
daveey and champion #2 by daveey-1; the fillers are the **scripted baselines**
(`PLAYER_SCRIPTED=<name>`), **≥1, normally 2**. Bullwhip's set: champion #1
`bullwhip-steady:v1`, champion #2 `bullwhip-forecaster:v1`, fillers `bullwhip-basestock:v1`
and `bullwhip-mirror:v1`. See `playbooks/make-coworld.md` for the full text and the gotcha table.

## Review loop (phase 30)

```
round = 1
loop:
  reviewer  -> runs/<run>/reviews/r<round>-review.md   (neutral: "trace and report")
  if review has no findings: judge runs anyway
  fixer     -> commits per finding, CI green, runs/<run>/reviews/r<round>-fixes.md
  judge     -> runs/<run>/reviews/r<round>-verdict.md   (fresh context; scored on
               refuting the reviewer AND on the acceptance checklist)
  if verdict.blocking == 0: exit loop
  round += 1; if round > 4: log residue, continue to phase 40 only if no
               blocking finding is in {hang, timeout, static-viewer, manifest, num_agents};
               else phase 90
```
Reviewer and judge are distinct agents with distinct prompts; the judge never sees the
fixer's self-report before forming its own read of the diff. The acceptance checklist lives
in `prompts/30-review-loop.md` and is the only source of "blocking".

## State

`runs/<YYYY-MM-DD>-<slug>/STATE.json`:
```json
{"run": "2026-08-22-bullwhip", "idea_task": "1217704516752265", "run_task": "…",
 "slug": "bullwhip", "repo": "Metta-AI/cogame-bullwhip", "starter": "cogame-babel",
 "phase": "60", "phase_attempts": {"40": 2}, "review_round": 3,
 "coworld": {"version": "0.1.2", "cow_id": "cow_…", "manifest_sha": "sha256:…",
              "release_run_id": "17423991055"},
 "policies": {"champion1": "bullwhip-steady:v1", "champion2": "bullwhip-forecaster:v1",
              "fillers": ["bullwhip-basestock:v1", "bullwhip-mirror:v1"],
              "filler_version_ids": ["b7c1…", "9ad2…"]},
 "league": {"id": "league_…", "division": "div_…"},
 "verify": {"rounds": [3, 4], "replay": "https://…replay", "iframe_static": true},
 "announce": {"attempted_at": "2026-08-22T17:02:00Z", "discord_message_id": "…"},
 "atlas": {"status": "pr_open", "pr_url": "https://github.com/Metta-AI/metta/pull/20260",
           "branch": "atlas/bullwhip-17431…", "region": "commons", "x": 425, "y": 553,
           "dispatch_run_id": "17431…", "attempted_at": "2026-08-22T17:20:00Z"},
 "blocked": null,
 "heartbeat_at": "2026-08-22T16:40:00Z", "session_ended_at": null, "session_id": "9f3a1c7d",
 "log": "runs/2026-08-22-bullwhip/log.md"}
```
`phase` is written — committed and pushed — at the moment of **every** phase transition,
**before** the new phase's first sub-agent is dispatched. A `log.md` line tagged with a phase
number higher than `STATE.phase` is a defect (the resume path repairs it forward-only from tags `10`…`80`; `90` lines are outcomes, never a phase): the next resume would re-enter the older phase and
redo work already done. `prompts/00-claim.md` step 5 carries the repair for a run that already
drifted.

`session_ended_at` is written by the closing step of a heartbeat that ended deliberately (SPEC
§Runtime step 3 / `AGENT.md` §Ending a heartbeat) and cleared by the next session's resume; a
session that crashed leaves it null or stale, which is exactly the 180-minute case.

`session_id` is the resuming session's **nonce** — 8 hex chars minted at resume, written with
`heartbeat_at`, and echoed in the `00 resume at phase <n> attempt=<k> session=<nonce>` line of
`log.md`. It is what makes a resume race decidable: see §Runtime step 2a.

`coworld.release_run_id` is the GitHub Actions run id of the `coworld-release.yml` dispatch that
produced the accepted `release-result.json`. Phase 40 also copies that artifact to
`runs/<run>/release-result.json` and commits it; phase 60 check 7 reads the committed copy and
falls back to `gh run download <release_run_id> -n release-result`. `/tmp` never crosses a
heartbeat.

`atlas.status` is `pr_open` (the atlas PR is open with auto-merge armed), `already_placed` (the
slug was on the map already), or `unplaced` (three dispatches failed; `atlas.reason` carries the
last error and a Fleet card names it). Any of the three means phase 75 is finished — it is the
resume guard, and the run never opens a second atlas PR.

`policies.champion1` / `champion2` / `fillers[]` are always `<name>:vN` **labels**, written by
phase 40. `policies.filler_version_ids[]` holds the policy-version **UUIDs** phase 50 resolves
from `GET /policy-versions`; phase 50 writes that field and never overwrites `fillers[]`.

`log.md` is append-only, one line per action with UTC time. Reviews, verdicts, VERIFY.md,
and the design note copy live beside it. STATE is committed and pushed on every write.

## Blocked (phase 90)

The run task moves to *Blocked*; a subtask is created, **assigned to David Bloomin**
(`1209016834701578`), titled `BLOCKED <slug> @<phase>: <one-line ask>`, body = what failed
(exact error text), what was tried (the three attempts), the single decision/credential/
action needed, and `Resume: complete this subtask; the next heartbeat resumes at phase <n>`.
STATE.blocked records the same. The coordinator exits. The idea task gets one comment.
Never mark Blocked for something the rails say the agent decides itself (starter choice,
scoring rule when the idea pins one, parameter tuning).

**Phase 90 requires a run.** It reads `STATE.phase`, `STATE.run_task`, `STATE.idea_task` and
files a subtask *on the run task*, so it may only be entered once phase 00 has created the run
task and written STATE. An idea that cannot be started never reaches it — that is the SKIPPED
path in §Runtime step 4, whose human-visible artifact is a Fleet-section card, not a Blocked run.

## Repo layout

```
AGENT.md                 coordinator system prompt
README.md
docs/SPEC.md             this file
prompts/00…90-*.md       phase prompts (the coordinator reads the phase's prompt when it enters it)
agents/<role>.md         sub-agent system prompts: designer, builder, reviewer, fixer, judge, verifier
agents/<role>.json       model + tools manifest (fleetctl-style)
tools/atlas_place.py     edits CITIES in metta's places.mjs (run by atlas-update.yml, phase 75)
tools/atlas_spot.py      picks free coordinates on a continent (run in the sandbox, phase 75)
templates/               ci.yml, coworld-release.yml, coworld-submit.yml, tools/ci/docker_smoke.sh,
                         tools/ci/policies.json.example, run-task.md, blocked-subtask.md, announce.md,
                         STATE.template.json, README.md
playbooks/make-coworld.md   the make-coworld skill + gotchas (maintained here; copy of the local skill)
playbooks/observatory-api.md  call shapes that are known to work (from the worked example)
learnings/LEARNINGS.md   append-only, dated; every run adds a section
runs/<run>/              STATE.json, log.md, reviews/, VERIFY.md, release-result.json, design note copy
fleet/cloud.md           env/vault/agent/deployment ids (deploy.py rewrites the ids table)
fleet/bin/deploy.py      create agents + deployment from agents/*.json and AGENT.md
```

## Rails (the coordinator decides; never asks)

Starter choice, scoring rule when the idea pins one, seat count, parameter tuning, viewer
composition, policy prompts, version bumps, which of two equivalent API shapes to use.
**Blocked** is for: missing credential/permission, a platform outage persisting > 45 min,
a rule the idea leaves genuinely open *and* whose readings lead to materially different
games, a cert failure that survives three distinct fixes, and anything destructive.
