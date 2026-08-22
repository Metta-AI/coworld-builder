# Parallel coworld runs — what changed

Date: 2026-08-22. Branch: `main`. Commits: `12807c5`, `7a12ac0`, `014d5de`, `fa0ba72`
(this file adds one more).

Before: one hourly deployment (`coworld-builder-hourly`, minute 11), and a heartbeat that
**exited** the moment any run task sat in *Running* with a fresh `heartbeat_at`. Concurrency
was 1 by construction.

After: **three staggered hourly crons on the same coordinator agent**
(`coworld-builder-a`/`-b`/`-c` at minutes 11/31/51 UTC), each heartbeat adopting **at most one**
unit of work, with the number of simultaneously-live runs bounded by `max_parallel_runs` (3).
Several runs in *Running* at once is now the documented normal state.

## The decided heartbeat algorithm (identical in SPEC, AGENT.md and 00-claim.md)

1. Tool preflight, read the board, compute `live` = *Running* runs whose `heartbeat_at` is
   **fresh** — < 90 min old **and** with no `session_ended_at ≥ heartbeat_at`. That freshness
   rule is unchanged; only what is done with it changed. Read `max_parallel_runs` from
   `fleet/cloud.md` §Parallelism in the same pass.
2. Adopt at most one unit of work, in order:
   - **(a)** a *Running* run with a stale heartbeat (or `session_ended_at ≥ heartbeat_at`) →
     resume, through the existing session-nonce guard;
   - **(b)** a *Blocked* run whose `STATE.blocked.subtask` is complete → resume (same guard);
   - **(c)** if `live` < `max_parallel_runs` **and** fewer than 2 runs are *Blocked* → claim the
     next startable idea (existing comment-first claim + SKIPPED rules, unchanged);
   - **(d)** else exit, appending one line to `runs/heartbeats.log`:
     `<UTC> heartbeat: cap reached (live=<n>/<max>)` or `<UTC> heartbeat: nothing to do`.
3. `heartbeat_at` every ≤15 min of work and on every phase transition, as before.

Races: when two heartbeats fire within seconds of each other (a cron plus a manual
`deploy.py run`, or two crons), the **existing** claim race (comment-first + 20 s re-read +
non-forcing push) and resume race (session nonce + rejected-push adjudication + 20 s Asana
re-GET) already decide who owns the work; the loser exits having written nothing. Parallelism
adds no new arbitration mechanism, only the cap in (c).

## Per file

### `fleet/cloud.md`
- New **§Parallelism** with machine-readable lines in the style of `environment_id:` —
  `` `max_parallel_runs: 3` `` plus the deployment/cron table (`coworld-builder-a` `11 * * * *`,
  `-b` `31 * * * *`, `-c` `51 * * * *`, UTC). Says explicitly that lowering `max_parallel_runs`
  is the throttle, needs no redeploy, and never stops runs already in flight.
- ids table: the row `coworld-builder-hourly` became `coworld-builder-a` **keeping its id**
  (`depl_01YSmungQBmAMerqw9KxGdQs`); `-b` and `-c` added as `TBD` until `create` makes them.
- The schedule paragraph under the table now names all three crons and records that `-a` is the
  original deployment, renamed in place.

### `fleet/deployment.json`
- One template body, unchanged apart from `name` (now `coworld-builder-a`, the template default)
  and a new `deployments` fan-out list: `[{"suffix":"a","cron":"11 * * * *"},
  {"suffix":"b","cron":"31 * * * *"},{"suffix":"c","cron":"51 * * * *"}]`.
- `initial_events` (the kickoff message), resources, vaults, environment: untouched.
- `_comment` rewritten to explain the fan-out and the cloud.md cross-check.

### `fleet/bin/deploy.py`
- `deployment_specs()` reads the `deployments` list (authoritative for what is applied) and
  cross-checks it against `fleet/cloud.md` §Parallelism via `read_parallelism()`, printing a
  `WARNING` on any disagreement (cron mismatch, a deployment in one file and not the other, or a
  missing `max_parallel_runs:` line).
- `deployment_body(..., spec, ...)` stamps the shared template with that spec's `name` and cron
  and drops the local-only `deployments` key from the API body.
- **`create`** now creates only what does not exist live, printing `SKIP` for the rest — so it is
  the way to add `b` and `c` while `a` is running. The old blanket "refuse if anything exists"
  is gone; the anti-duplication guarantee it protected is preserved by the per-name existence
  check. Two extra guards: if the coordinator already exists but a sub-agent was just created it
  prints a `NOTE` to run `update` (stale roster), and it refuses to create `coworld-builder-a`
  while the legacy `coworld-builder-hourly` is live (that would double the cron).
- **`update`** reconciles **all K** deployments (name/schedule/resources/vaults/agent version)
  and adopts the legacy deployment: if `coworld-builder-hourly` is live and `coworld-builder-a`
  is not, the legacy object *is* deployment a — same id, renamed and rescheduled by the normal
  field diff. It is never deleted. A deployment that has not been created yet is now reported
  (`MISSING … run create`) and summarised, but is **no longer fatal**; `update` still exits
  non-zero if no coordinator id is available or if nothing could be reconciled at all. (Reason:
  during the rollout `b` and `c` legitimately do not exist, and the documented workflow runs
  `update` after every prompt change.)
- **`run`** takes `--name <suffix>` (default `a`); accepts `a` or `coworld-builder-a`, and lists
  the valid names on a typo.
- **`status`** iterates all K, and one deployment that does not exist yet no longer aborts the
  others' status.
- Every pre-existing guard is intact: no `TBD` over a real id in `write_cloud`, abort on a
  missing live agent role before versioning the coordinator, `page()` pagination, redaction,
  tokens re-supplied only at apply time.

### `docs/SPEC.md`
- §Runtime: "One deployment, hourly cron" → three staggered crons on the same coordinator; the
  heartbeat steps rewritten as `live` + adopt-one-of-(a)(b)(c)(d).
- New **§Parallelism and per-run isolation**: each run has its own directory, task, repo, league,
  champions and fillers; the only shared surfaces are `runs/heartbeats.log`, `runs/SKIPPED.json`
  (both append-only, pull → append → push) and the Coworld Ideas board. **Bedrock capacity is the
  real shared resource**: a platform-wide `LLM provider is unavailable` seen across two runs at
  once is a **wait** inside phase 60's existing 75-minute bound, not *Blocked*; expiry of that
  bound is still an outage for phase 90; `max_parallel_runs` is the operator's throttle.
- §State: `phase` is written, committed and pushed at every phase transition **before** the new
  phase's first sub-agent is dispatched.

### `AGENT.md`
- §Heartbeat algorithm rewritten to the same (a)/(b)/(c)/(d) shape, opening with "you are one of
  three hourly crons and several runs in *Running* at once is normal".
- §STATE/log/heartbeat discipline: the `STATE.phase`-at-transition rule.
- Hard rule 7: the two shared files are named as append-only and shared with the other crons;
  another run's *directory* stays off limits even while it runs in parallel.

### `prompts/00-claim.md`
- Header states the parallel model and the at-most-one-unit rule.
- Step 1 reads `max_parallel_runs`; step 2's fresh-run bullet counts toward `live` and says
  "leave it alone" instead of "exit immediately".
- Step 4 claims only when `live` < `max_parallel_runs`; new **step 4a** is the explicit
  nothing-adopted exit with the two log lines.
- New **step 5.0a Phase-drift repair** (see below).
- Exit criterion (a) replaced: it is now step 4a's cap / nothing-to-do exit, with "other runs
  being *Running* with fresh heartbeats is not an exit reason by itself".
- §Writes documents the shared append-only files and the new lines.

### `prompts/60-verify.md`
- Check 5's `LLM provider is unavailable` guidance now names the parallel-runs case explicitly
  and says *wait inside the 75-minute bound*, not Blocked.

### `README.md`, `templates/run-task.md`, `templates/README.md`
- README: two sentences on parallelism up front, updated `deploy.py` usage, and two new
  "Maintaining it" bullets (change the number of crons; change `max_parallel_runs`).
- Both templates: a fresh `heartbeat_at` now means "a session is working that run right now",
  not "another run is live → exit".

### `prompts/90-blocked.md`
- Unchanged: nothing in it assumed a single run.

## Phase-drift repair (added at the coordinator's request, same commit series)

The live Lighthouse run kept `STATE.phase = "20"` through all of phase 30 (its `log.md` lines
were correctly tagged `30 …`), so a resume would have re-entered phase 20 and rebuilt the repo.
Added:

- `AGENT.md` §STATE discipline and `docs/SPEC.md` §State: **`STATE.phase` is written — committed
  and pushed — at the moment of every phase transition, BEFORE the new phase's first sub-agent is
  dispatched; a `log.md` line tagged with a phase number higher than `STATE.phase` is a defect.**
- `prompts/00-claim.md` step **5.0a**: on resume, read the highest phase tag on `log.md` lines
  newer than the *previous* session's `00 claim`/`00 resume` line; if it exceeds `STATE.phase`,
  trust the log — set `STATE.phase` (and `review_round` to the highest `r<k>` for phase 30), log
  `<UTC> 00 resume: STATE phase repaired <old> -> <new> from log`, commit, push, continue at the
  repaired phase. The 5.1 attempt counter then applies to the repaired phase.

## Verification

```
$ python3 -m py_compile fleet/bin/deploy.py
(exit 0, no output)

$ python3 fleet/bin/deploy.py --dry-run create
exit=0
(dry run — live state not read; a real `create` SKIPs every agent and deployment that already exists live and creates only the missing ones)
--- POST /deployments (coworld-builder-a) ---
--- POST /deployments (coworld-builder-b) ---
--- POST /deployments (coworld-builder-c) ---
(dry run — nothing created, cloud.md untouched; 3 deployment(s): coworld-builder-a, coworld-builder-b, coworld-builder-c)

$ python3 fleet/bin/deploy.py --dry-run update
exit=0
ADOPTING legacy deployment coworld-builder-hourly depl_01YSmungQBmAMerqw9KxGdQs as coworld-builder-a (rename + reschedule, same id)
--- POST /deployments/depl_01YSmungQBmAMerqw9KxGdQs (coworld-builder-a) ---
{
 "agent": {"id": "agent_01Hxx6czhYKwmEJ7CkMnXb1W", "type": "agent", "version": 1},
 "name": "coworld-builder-a"
}
MISSING live deployment coworld-builder-b — run `create` to add it; `update` reconciles only what exists
MISSING live deployment coworld-builder-c — run `create` to add it; `update` reconciles only what exists
deployments (3 configured): coworld-builder-a cron=11 * * * * reconciled; coworld-builder-b cron=31 * * * * MISSING — run create; coworld-builder-c cron=51 * * * * MISSING — run create

$ python3 -c "json.load(fleet/deployment.json)"
deployment.json OK: ['a=11 * * * *', 'b=31 * * * *', 'c=51 * * * *'] name=coworld-builder-a
SKIPPED.json OK: []

$ grep -rn "another run is live|yield to live run|yielded to live run" (excluding reviews/ and runs/)
(no hits)
```

Also exercised by hand: `--dry-run status` prints all three deployments; `--dry-run run` defaults
to `a`, `--dry-run run --name b` targets b, `--dry-run run --name zz` exits with the list of
valid names; live `status` prints `coworld-builder-hourly` (its current live name, pre-rename)
plus a "run `create`" line for b and c.

`a`'s live schedule is already `11 * * * *`, so the only fields `update` will POST are `name`
and `agent` — no reschedule, no downtime, and no second cron is ever created.

## Apply order (not run here — this change is committed, not deployed)

1. `python3 fleet/bin/deploy.py update` — renames `coworld-builder-hourly` → `coworld-builder-a`
   and versions the coordinator with the new `AGENT.md`.
2. `python3 fleet/bin/deploy.py create` — creates `coworld-builder-b` and `-c` (SKIPs the agents
   and `-a`) and writes their ids into `fleet/cloud.md`, replacing the `TBD` rows.
3. `python3 fleet/bin/deploy.py status` — three deployments, three schedules.

## Where judgement was applied (flagged for review)

1. **`create` on an existing agent SKIPs rather than refusing.** The brief said `create`
   "refuses only on agent-name collisions when agents already exist" *and*, in the same
   sentence, that it should be "agents if missing + deployments if missing, printing SKIP for
   existing ones". Those pull in opposite directions; the SKIP semantics were implemented,
   because they are what makes `create` usable to add b and c while keeping the
   never-duplicate-a-name guarantee. Nothing is ever created twice under either reading.
2. **`update` no longer exits non-zero merely because a configured deployment is missing.**
   Required to make `--dry-run update` exit 0 while b and c do not exist. The missing ones are
   printed and summarised; `update` still fails when no coordinator id is available or when no
   deployment at all could be reconciled.
3. **`fleet/deployment.json` is authoritative over `fleet/cloud.md` §Parallelism** for the crons
   deploy.py applies (cloud.md is what the *agents* read). Two files carry the table because the
   brief put constants in cloud.md and the fan-out list in deployment.json; a mismatch prints a
   WARNING rather than silently diverging.
4. **`max_parallel_runs` is deliberately independent of the number of crons.** No consistency
   check ties them, because lowering the cap below K is exactly the throttle §Parallelism
   describes.
5. **`templates/run-task.md` and `templates/README.md` were edited** though the brief listed only
   README.md and AGENT.md — both contained the "another run is live → the heartbeat exits"
   sentence that the required grep forbids.
