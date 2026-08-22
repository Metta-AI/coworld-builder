# coworld-builder — specification

The decided design. Prompts, templates, and agents are written against this document; change
it first, then them.

## Mission

A managed agent takes one **Coworld Idea** (Asana project `1217704774784096`, "Coworld Ideas")
and carries it to **done**: a public `Metta-AI/cogame-<slug>` repo, a certified coworld on
softmax.com, a league with two ranked champions and fillers, ≥2 completed rounds with valid
replays rendered by a **static** viewer on `https://softmax.com/<slug>`, and an announcement in
Discord `#coworlds`. When it cannot, it marks the run **Blocked** with a subtask for a human
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
- **One deployment, hourly cron** (`*/60`, minute 11). Every run is a *heartbeat*:
  1. Read the **Coworld Builder** board (the Coworld Builder gid in `fleet/cloud.md`; it is a
     table row, not an environment variable). If a run task sits in *Running*
     with `heartbeat_at` < 90 min old **and** `STATE.session_ended_at` is null or older than
     `heartbeat_at` → another run is live → **exit**. (No dupes.)
  2. If a run task is in *Running* with a stale heartbeat, **or** with a fresh heartbeat whose
     `STATE.session_ended_at` is ≥ `heartbeat_at` (the last session ended cleanly and said so),
     → it is yours: **resume** at `STATE.json.phase`. Without that marker a run that needs more
     than one session would look alive for the full 90 minutes after its session died, and — the
     cron being hourly — would advance only every other firing.
  2a. **Every resume — from step 2 or step 3 — is guarded by a session nonce.** Two heartbeats
     can observe the same free run in the same minute (the hourly cron plus a manual
     `deploy.py run`). The resuming session mints a nonce, writes it as `STATE.session_id` with
     `heartbeat_at`, logs `00 resume at phase <n> attempt=<k> session=<nonce>`, pulls and pushes;
     a **rejected push** means it rebases (aborting and exiting on a conflict) and exits if
     `log.md` now contains any `00 resume` line with a foreign nonce that was not there before
     its pull — never "the last line", which after a rebase is its own (never force — the same
     rejected-push rule covers claims and resumes). It
     then re-GETs the Asana `heartbeat_at` custom field after 20 s and exits if the value moved
     past its own stamp. Only a session that survives all three checks works the phase.
     (`prompts/00-claim.md` step 5.0.)
  3. Else if a run task is in *Blocked* and its human subtask is complete → move it to
     *Running* and **resume** (through the same step 2a guard).
  4. Else claim the top **unclaimed, incomplete** Coworld Idea (board order; skip ideas that
     already have a run task), create the run task, and start at phase 00. A *Blocked* run whose
     subtask is still open does **not** stop this: concurrency is 1 and the queue keeps moving,
     bounded at **2 simultaneously-Blocked runs** — at 2, the heartbeat claims nothing and exits.
     An idea the coordinator **cannot start** is **SKIPPED**, not Blocked: its text is marked
     confidential (a public repo would publish it), or it cannot be mapped to any starter and the
     gap is one §Rails calls a human decision. A SKIP is one
     `skipped by coworld-builder: <reason>` comment on the idea task, the gid appended to the
     committed `runs/SKIPPED.json`, and one card in the Builder board's *Fleet* section assigned
     to David Bloomin titled `SKIPPED <idea title>: <reason>` (one per idea, deduped by title);
     the heartbeat then **continues to the next idea**. Step 4 skips gids listed in
     `runs/SKIPPED.json` and ideas already carrying that comment, so a skipped idea never stalls
     the queue. Phase 90 is **never** entered here: it needs a run task and a STATE, and at this
     point neither exists.
  5. Write `heartbeat_at` on the run task + `runs/<run>/STATE.json` at least every 15 minutes
     of work, and on every phase transition.
- The sandbox has **no Docker, no Nim, no emsdk**. Every compile / image / certification /
  upload step runs in **GitHub Actions inside the coworld repo** from templates in this repo.
  The agent pushes, dispatches workflows (`gh workflow run`), polls (`gh run watch`), and
  reads logs. CI credentials are repo secrets `SOFTMAX_TOKEN` and `ANTHROPIC_API_KEY`, propagated onto each coworld repo by dispatching `propagate-secrets.yml` in `Metta-AI/coworld-builder` (`gh workflow run propagate-secrets.yml -R Metta-AI/coworld-builder -f repo=cogame-<slug>`; the softmax-agents GitHub App sets them — no org admin, no value ever in the sandbox).
- Everything else (Observatory API, `softmax.com`, Asana, Discord, GitHub) is HTTPS from the
  sandbox using vault credentials substituted at egress (`SOFTMAX_TOKEN`, `GH_TOKEN`,
  `ASANA_PAT`, `DISCORD_BOT_TOKEN`).
- Repos mounted (declared in `fleet/deployment.json`): this repo (read-write,
  `/workspace/coworld-builder`), `daveey/cogamer` (read, `/workspace/cogamer`, for
  `fleet/PROTOCOLS.md`), and all six starters read-only at **`/workspace/starters/<name>`**:
  `cogame-babel`, `cogame-bullwhip`, `cogame-parley`, `coworld-ctf`, `cogame-moba`,
  `cogame-factorio`. Phase 10 reads the mounts; phase 20 still `git clone`s the chosen starter
  into the new repo's working tree so the new repo gets a clean history.

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
| 80 | `prompts/80-close.md` | coordinator | executive summary on run task + idea task, `learnings/LEARNINGS.md` entry, run task → *Done*, idea task completed | — |
| 90 | `prompts/90-blocked.md` | coordinator | run task → *Blocked*, subtask → human, STATE.blocked | used by any phase on exhausting its retry budget |

Retry budgets: each phase may retry its own failing step 3× (with a different approach each
time, logged) before going to 90. Phase 80 (close) is retried across heartbeats without counting,
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
8. The verifier's **spectator judgment** (a short paragraph): the replay is legible and shows
   the game. The sandbox has no screen and no headless browser, so the judgment is written from
   three fetched things, never from a rendered page:
   (a) **the replay JSON** — the events and per-tick states the viewer would draw: read them and
   say whether the champion seats' activity reads as the game (who did what, when, and how the
   score moved);
   (b) **the bundle** — `GET` the iframe `src`'s `index.html` **and every asset it references**
   (each `<script src>`, each `<link href>`, and the `.wasm` named in the emscripten module
   loader), all returning **200 with non-trivial sizes** (a 0-byte or HTML-error-page asset is a
   broken viewer);
   (c) **the viewer shell's error markers** — the fetched `static_replay.js` (or the index that
   inlines it) must contain the `coworld-replay` postMessage bridge, including its
   `tell("ready")` call; its absence means the embedded viewer never signals the host page.
   No DOM readouts, no browser, no screenshot.

## Design pins every coworld inherits (from the make-coworld playbook)

Starter by game shape (parley/babel for LLM-prompt games; coworld-ctf for real-time grid;
cogame-moba for bit-exact ports; cogame-factorio for external engines). Public repo
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
 "blocked": null,
 "heartbeat_at": "2026-08-22T16:40:00Z", "session_ended_at": null, "session_id": "9f3a1c7d",
 "log": "runs/2026-08-22-bullwhip/log.md"}
```
`session_ended_at` is written by the closing step of a heartbeat that ended deliberately (SPEC
step 5 / `AGENT.md` §Ending a heartbeat) and cleared by the next session's resume; a session that
crashed leaves it null or stale, which is exactly the 90-minute case.

`session_id` is the resuming session's **nonce** — 8 hex chars minted at resume, written with
`heartbeat_at`, and echoed in the `00 resume at phase <n> attempt=<k> session=<nonce>` line of
`log.md`. It is what makes a resume race decidable: see §Runtime step 2a.

`coworld.release_run_id` is the GitHub Actions run id of the `coworld-release.yml` dispatch that
produced the accepted `release-result.json`. Phase 40 also copies that artifact to
`runs/<run>/release-result.json` and commits it; phase 60 check 7 reads the committed copy and
falls back to `gh run download <release_run_id> -n release-result`. `/tmp` never crosses a
heartbeat.

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
