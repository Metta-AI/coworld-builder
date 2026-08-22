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
  `daveey/cogamer` (config mirrored in git under `fleet/mirror/`, applied out).
- **One deployment, hourly cron** (`*/60`, minute 11). Every run is a *heartbeat*:
  1. Read the **Coworld Builder** board (`$BUILDER_PROJECT`). If a run task sits in *Running*
     with `heartbeat_at` < 90 min old → another run is live → **exit**. (No dupes.)
  2. If a run task is in *Running* with a stale heartbeat → it is yours: **resume** at
     `STATE.json.phase`.
  3. Else if a run task is in *Blocked* and its human subtask is complete → move it to
     *Running* and **resume**.
  4. Else claim the top **unclaimed, incomplete** Coworld Idea (board order; skip ideas that
     already have a run task), create the run task, and start at phase 00.
  5. Write `heartbeat_at` on the run task + `runs/<run>/STATE.json` at least every 15 minutes
     of work, and on every phase transition.
- The sandbox has **no Docker, no Nim, no emsdk**. Every compile / image / certification /
  upload step runs in **GitHub Actions inside the coworld repo** from templates in this repo.
  The agent pushes, dispatches workflows (`gh workflow run`), polls (`gh run watch`), and
  reads logs. Org secrets `SOFTMAX_TOKEN` and `ANTHROPIC_API_KEY` on `Metta-AI` supply CI.
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
| 10 | `prompts/10-design.md` | designer → coordinator | `docs/plans/<date>-<slug>-design.md` in the new repo (starter, rules, scoring, events, state JSON, viewer, packaging, tests) | coordinator accepts the note against the checklist in the prompt |
| 20 | `prompts/20-build.md` | builder | the repo: sim/llm/server/player, viewer, manifest, CI templates, tests, README; CI green | `ci.yml` green on `main` |
| 30 | `prompts/30-review-loop.md` | reviewer → fixer → judge | review reports under `runs/<run>/reviews/`, fixes pushed | judge returns **zero blocking findings** (max 4 rounds; residue logged) |
| 40 | `prompts/40-release.md` | builder (CI) | `coworld-release.yml` run: build → certify → upload-policies → upload-coworld (wait hosted smoke) → secret put | coworld **Canonical: yes**, hosted certification certified |
| 50 | `prompts/50-league.md` | coordinator | league seed, division, settings, champion #1 (daveey), champion #2 (daveey-1), fillers, unpause, trigger | both champions show as entrants; round triggered |
| 60 | `prompts/60-verify.md` | verifier → judge | `runs/<run>/VERIFY.md` with fetched evidence | the *definition of done* checklist all-true |
| 70 | `prompts/70-announce.md` | coordinator | Discord message id | message posted, id in STATE |
| 80 | `prompts/80-close.md` | coordinator | executive summary on run task + idea task, `learnings/LEARNINGS.md` entry, run task → *Done*, idea task completed | — |
| 90 | `prompts/90-blocked.md` | coordinator | run task → *Blocked*, subtask → human, STATE.blocked | used by any phase on exhausting its retry budget |

Retry budgets: each phase may retry its own failing step 3× (with a different approach each
time, logged) before going to 90. Phase 30's loop cap is 4 rounds. Phase 60's wait for rounds
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
7. Certification output contains `Replay liveness: skipped (static replay bundle declared`.
8. The verifier's spectator judgment (a short paragraph): the replay is legible and shows
   the game — written from the static viewer's rendered state (DOM readouts: clock, scorebug,
   feed lines at three scrub points), since the sandbox has no screen.

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
 "coworld": {"version": "0.1.2", "cow_id": "cow_…", "manifest_sha": "sha256:…"},
 "policies": {"champion1": "bullwhip-steady:v1", "champion2": "bullwhip-forecaster:v1",
              "fillers": ["bullwhip-basestock:v1", "bullwhip-mirror:v1"],
              "filler_version_ids": ["b7c1…", "9ad2…"]},
 "league": {"id": "league_…", "division": "div_…"},
 "verify": {"rounds": [3, 4], "replay": "https://…replay", "iframe_static": true},
 "announce": {"discord_message_id": "…"},
 "blocked": null,
 "heartbeat_at": "2026-08-22T16:40:00Z", "log": "runs/2026-08-22-bullwhip/log.md"}
```
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

## Repo layout

```
AGENT.md                 coordinator system prompt
README.md
docs/SPEC.md             this file
prompts/00…90-*.md       phase prompts (the coordinator reads the phase's prompt when it enters it)
agents/<role>.md         sub-agent system prompts: designer, builder, reviewer, fixer, judge, verifier
agents/<role>.json       model + tools manifest (fleetctl-style)
templates/               ci.yml, coworld-release.yml, run-task.md, blocked-subtask.md, announce.md, STATE.template.json
playbooks/make-coworld.md   the make-coworld skill + gotchas (maintained here; copy of the local skill)
playbooks/observatory-api.md  call shapes that are known to work (from the worked example)
learnings/LEARNINGS.md   append-only, dated; every run adds a section
runs/<run>/              STATE.json, log.md, reviews/, VERIFY.md, design note copy
fleet/cloud.md           env/vault/agent/deployment ids; fleet/mirror/ (fleetctl export)
fleet/bin/deploy.py      create agents + deployment from agents/*.json and AGENT.md
```

## Rails (the coordinator decides; never asks)

Starter choice, scoring rule when the idea pins one, seat count, parameter tuning, viewer
composition, policy prompts, version bumps, which of two equivalent API shapes to use.
**Blocked** is for: missing credential/permission, a platform outage persisting > 45 min,
a rule the idea leaves genuinely open *and* whose readings lead to materially different
games, a cert failure that survives three distinct fixes, and anything destructive.
