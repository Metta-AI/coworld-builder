# coworld-builder

An autonomous builder for coworlds. A managed agent wakes up three times an hour — three
staggered crons on the same coordinator (`coworld-builder-a`/`-b`/`-c`, minutes 11/31/51 UTC) —
takes the top unclaimed idea off the Asana **Coworld Ideas** board, and carries it all the way to
a shipped game: a public `Metta-AI/cogame-<slug>` repo, a certified coworld on softmax.com, a league with
two ranked champions and filler baselines, at least two completed rounds whose replays render
in a static wasm viewer at `https://softmax.com/<slug>`, and an announcement in Discord
`#coworlds`. No human is in the loop for any of it.

**Runs go in parallel.** Each heartbeat adopts at most one unit of work — resume a run whose
session ended, resume a run a human just unblocked, or claim one new idea — so up to
`max_parallel_runs` runs (`fleet/cloud.md` §Parallelism, currently 3) are in flight at once, each
with its own directory, repo, league and champions; the only shared surfaces are the two
append-only files at the root of `runs/` and the Ideas board itself. Lower `max_parallel_runs` in
`fleet/cloud.md` to throttle (no redeploy needed); it stops new claims and leaves runs in flight
alone.

This repository is not the coworlds — it is the machine that makes them. It holds the
coordinator's system prompt (`AGENT.md`), one prompt per phase (`prompts/`), one system prompt
per sub-agent (`agents/`), the CI workflow templates every new coworld repo gets
(`templates/`), the playbooks the agents read as they work (`playbooks/`), the append-only
record of what each run learned (`learnings/`), and the per-run working state (`runs/`). The
decided design lives in `docs/SPEC.md`; prompts and templates are written against it, and it
changes first when the design changes.

The agent is deliberately unable to build anything locally: its sandbox has no Docker, no Nim
and no emsdk. Every compile, image build, certification and upload happens in GitHub Actions
inside the coworld repo, from the templates here. Everything else — Observatory, softmax.com,
Asana, Discord, GitHub — is plain HTTPS with vault credentials substituted at egress. That
constraint is load-bearing: it means every build step leaves a run URL and a log a human can
read later.

## How a run works

Each phase has a prompt; the coordinator reads `prompts/<phase>.md` when it enters that phase
and follows it. State lives in `runs/<YYYY-MM-DD>-<slug>/STATE.json`, committed and pushed on
every write, so any heartbeat can resume where the last one stopped.

| # | prompt | owner | produces | done when |
|---|---|---|---|---|
| 00 | `prompts/00-claim.md` | coordinator | run task (+ one subtask per phase), `runs/<run>/STATE.json`, `log.md` | task in *Running*, STATE written |
| 10 | `prompts/10-design.md` | designer → coordinator | `docs/plans/<date>-<slug>-design.md` in the new repo | coordinator accepts the note against the prompt's checklist |
| 20 | `prompts/20-build.md` | builder | the repo: sim/llm/server/player, viewer, manifest, CI, tests, README | `ci.yml` green on `main` |
| 30 | `prompts/30-review-loop.md` | reviewer → fixer → judge | reports under `runs/<run>/reviews/`, fixes pushed | judge returns **zero blocking findings** (max 4 rounds) |
| 40 | `prompts/40-release.md` | builder (CI) | build → certify → upload-policies → upload-coworld → secret put | coworld **Canonical: yes**, hosted certification certified |
| 50 | `prompts/50-league.md` | coordinator | league, division, settings, champions, fillers, trigger | both champions entrants; round triggered |
| 60 | `prompts/60-verify.md` | verifier → judge | `runs/<run>/VERIFY.md` with fetched evidence | the definition-of-done checklist all-true |
| 70 | `prompts/70-announce.md` | coordinator | Discord message id | message posted, id in STATE |
| 80 | `prompts/80-close.md` | coordinator | summaries, `learnings/LEARNINGS.md` entry | run task *Done*, idea task completed |
| 90 | `prompts/90-blocked.md` | coordinator | run task *Blocked*, subtask assigned to a human | used by any phase that exhausts its retry budget |

Each phase may retry its own failing step 3× (a different approach each time, logged) before
going to 90. Phase 30 caps at 4 review rounds; phase 60 waits at most 75 minutes for rounds.

## Deploy and update

```
python3 fleet/bin/deploy.py create        # create whatever is missing: sub-agents, coordinator,
                                          # and any of the three heartbeat deployments (SKIPs
                                          # what already exists, so it also adds b and c)
python3 fleet/bin/deploy.py update        # new agent versions wherever config/prompts drifted;
                                          # reconciles all three deployments
python3 fleet/bin/deploy.py run --name b  # a manual heartbeat on one deployment (default: a)
python3 fleet/bin/deploy.py status        # every deployment's latest runs and their sessions
```

Add `--dry-run` to any of them to print the redacted payloads without sending anything. The
tool needs `ANTHROPIC_API_KEY` (or AWS Secrets Manager `daveey/anthropic/api-key`, profile
`softmax-org`) and `gh auth token` for the repo mounts. It never prints a token, and no token
is ever written to git — `fleet/deployment.json` carries `"<resupply-at-apply>"` and the real
value is supplied at apply time.

`create` writes every id it made into the table in `fleet/cloud.md`. That file is where the
environment id, the vault ids, the Asana gids and the Discord ids live; the agents read it too.

## Maintaining it

- **Change how a phase behaves** → edit `prompts/<phase>.md`, commit, push. The next heartbeat
  reads the new file. No redeploy: the prompts are on the repo mount, not in the agent.
- **Change how a role behaves** → edit `AGENT.md` or `agents/<role>.md`, commit, then
  `python3 fleet/bin/deploy.py update`. Role prompts are baked into agent versions, so they
  need the redeploy.
- **Change the model, effort, or tools of a role** → edit `agents/<role>.json`, then `update`.
- **Change the schedule, the mounts, or how many heartbeat crons there are** → edit
  `fleet/deployment.json` (its `deployments` list is the fan-out) and the matching table in
  `fleet/cloud.md` §Parallelism, then `update` (existing crons) and `create` (new ones).
- **Change how many runs may be in flight** → edit `max_parallel_runs` in `fleet/cloud.md`
  §Parallelism. No redeploy: the coordinator reads that file every heartbeat.
- **Change the design itself** → edit `docs/SPEC.md` first, then the prompts and templates that
  implement it. The SPEC is the decided design; the prompts are its implementation.
- **Change a CI workflow all future coworlds get** → edit `templates/`. Existing coworld repos
  keep the copy they were built with.

This repo has two workflows of its own: `.github/workflows/propagate-secrets.yml` (one-time
setup, below) and `.github/workflows/viewer-check.yml` — the verifier's browser. The sandbox has
no screen, so phase 60 check 8 dispatches `viewer-check.yml` with the live iframe `src` and it
opens the hosted replay viewer in headless chromium (Playwright, pinned 1.55.0, running
`templates/tools/ci/viewer_smoke.mjs`), then uploads a screenshot and a JSON readout. It exists
because a bundle whose every asset returns 200 can still never draw a frame — cogame-lantern,
2026-08-23.

## One-time human setup

1. **CI credentials** live as repo secrets on this repo (`SOFTMAX_TOKEN`, `ANTHROPIC_API_KEY`,
   `GH_PAT` — a user token that is admin on Metta-AI repos). `.github/workflows/propagate-secrets.yml`
   copies the first two onto each coworld repo; the coordinator dispatches it in phase 20. Nothing
   to do per run. (Set once 2026-08-22.)
2. **`DISCORD_BOT_TOKEN` vault credential** → host `discord.com`, added to the deployment's
   `vault_ids`. Until it exists, phase 70 cannot post and every run ends Blocked at 70. Record
   the vault id in `fleet/cloud.md`.
3. **The Coworld Builder board** (`1217747772236871`): sections *Running*, *Blocked*, *Done*,
   *Fleet*; record the section gids in `fleet/cloud.md`. (There is no *Planned* section — the
   input queue is the separate Coworld Ideas board.)
4. The GitHub identity behind `gh auth token` must be able to create repos under `Metta-AI`.

## When a run is Blocked

Look, in this order:

1. **The run task's Blocked subtask** — assigned to David Bloomin, titled
   `BLOCKED <slug> @<phase>: <ask>`. It names the exact error, the three attempts that failed,
   and the single decision, credential or action needed. That is the whole ask; complete the
   subtask and the next heartbeat resumes at the recorded phase.
2. **`runs/<run>/STATE.json`** → `blocked` and `phase`: where it stopped and why, machine-readable.
3. **`runs/<run>/log.md`** — the append-only trail, one line per action, UTC. The three retries
   and what was different about each are here.
4. **`runs/<run>/reviews/`** (phase 30) or **`runs/<run>/VERIFY.md`** (phase 60) — the evidence
   the run was judged against, with the fetched bytes pasted in.
5. **`python3 fleet/bin/deploy.py status`** — if there is no recent session at all, the problem
   is the deployment (paused, bad agent version, expired repo token), not the run.

A run marked Blocked for something the rails say the agent decides itself (starter choice,
scoring when the idea pins one, parameter tuning) is a prompt bug — fix the prompt, not the run.
