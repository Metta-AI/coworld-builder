blocking: 1

# Parallel-runs change — independent verdict

Judged at `main` = `9cefbbe` (pulled; `reviews/parallel-change.md` read last). Sources read
first: `docs/SPEC.md` §Runtime/§Parallelism/§State, `AGENT.md`, `prompts/00-claim.md`,
`prompts/60-verify.md`, `fleet/cloud.md`, `fleet/deployment.json`, `fleet/bin/deploy.py`,
`templates/run-task.md`, `templates/README.md`, `README.md`, plus the live run
`runs/2026-08-22-lighthouse/` (STATE now `"40"`, session `1351c680`, `session_ended_at: null`,
fresh — a parallel heartbeat counts it into `live` and does not touch it).

## 1. Same idea claimed twice / same run resumed twice — **OK** (no regression)

Claim path, as written now: `prompts/00-claim.md:113` pull before reading; `:161-166` re-GET the
idea (completed / `claimed by …` / `skipped by …` → drop); `:167-168` comment **before** creating
anything; `:169-174` wait 20 s, re-read comments, yield to an **earlier** `created_at`; `:181-184`
+ `:195-201` rejected push → rebase, another `runs/<run>/STATE.json` for the idea → exit, never
force. Pre-parallel text (`git show 12807c5~1:prompts/00-claim.md` lines 145-173) has the same
steps; the diff touches only the surrounding gating (`live < max_parallel_runs`, step 4a), not
the guard.

Resume path: `00-claim.md:208-225` — nonce (`:209`), single STATE+log write and push (`:210-214`),
rejected push → rebase, abort-on-conflict, exit on **any** foreign-nonce `00 resume` line that was
not there before the pull, never "the last line" (`:215-221`), then Asana field
`1217748424048134` re-GET after 20 s, exit if moved past the stamp (`:222-225`). Explicitly
applied to the Blocked-resume path (`:92-94`, `:202-206`). Identical in `AGENT.md:41-51` and
SPEC (`docs/SPEC.md` §Runtime 2a, lines 43-56). A manual `deploy.py run` colliding with cron b
hits exactly these guards; one loser exits with nothing written.

## 2. Two different ideas at live = cap−1 — **OK (bounded) but silent — MINOR**

`live` is computed once at step 1 (`00-claim.md:46-48`, `AGENT.md:21-26`) and not re-checked
after the claim lands. Two heartbeats that both read `live = 2` can each claim a different idea
→ 4 fresh runs. Bound: each heartbeat adopts at most one unit (`00-claim.md:9-12`, `:77-79`),
so worst case is `cap + (concurrent heartbeats − 1)`; crons are 20 min apart and a claim
completes in about a minute, so in practice only a manual `deploy.py run` or a retried
deployment run overlaps → `cap + 1`. **Not acknowledged anywhere** (`grep -i overshoot|cap+1`
across SPEC/AGENT/00-claim/cloud.md/README: no hits). Not unbounded, so not BLOCKING.

## 3. Freshness definition of `live` — **OK**

- SPEC §Runtime step 1 (lines 31-36): `< 90 min` **and** no `session_ended_at ≥ heartbeat_at`.
- `AGENT.md:22-25`: `< 90 min` **and** `session_ended_at` null or older than `heartbeat_at`.
- `00-claim.md:68-76`: same two bullets; stale = `≥ 90 min` **or** `session_ended_at ≥ heartbeat_at`.
- `fleet/cloud.md:29-30`: same.
The boundary (`session_ended_at == heartbeat_at` → not fresh) agrees in all four. Counting reads the
custom field: `00-claim.md:53-57` (gid `1217748424048134`, `custom_fields[]|select(.gid==…)`),
`AGENT.md:144-147`, with the `heartbeat phase=<nn>` log-line fallback (`00-claim.md:65-67`).

## 4. Phase-drift repair (step 5.0a, `00-claim.md:227-234`) — **BLOCKING**

- Which lines count: "the highest phase tag `<nn>` on the `log.md` lines newer than the previous
  session's `00 claim` / `00 resume` line". The tag grammar is not pinned (the convention is
  `<UTC> <nn> …`; `heartbeat phase=<nn>` / `progress phase=<nn>` carry it as `phase=`). Workable
  but loose — an implementer must infer both forms.
- Highest tag: "greater than `STATE.phase`" → forward-only on the number line. `review_round`:
  "highest `r<k>` seen" when the phase is 30 — the phase-30 lines are `30 r1 …` (live log), so
  derivable.
- Ordering vs the counter: 5.0a is placed before 5.1 and says "the 5.1 counter then applies to the
  repaired phase" (`:234`), **but** 5.0 step 2 (`:210-212`) folds "the resume count from step 5.1"
  into the single STATE write that precedes 5.0a — so the increment is computed on the
  *unrepaired* phase first. Contradiction → either two writes or the wrong phase's counter bumps.
  MINOR.
- **Can it regress / misroute a phase? Yes — into 90.** Phase 90 logs
  `<UTC> 90 blocked phase=<n> …` (`prompts/90-blocked.md:71-72`) and leaves `STATE.phase` at the
  failed phase (`90-blocked.md:16`, `:82-84`). On the Blocked-resume path (b), the next session's
  5.0a scans lines newer than the previous `00 resume` — which include that `90 blocked` line —
  finds `90 > <n>`, "trusts the log", sets `STATE.phase = "90"`, and enters
  `prompts/90-blocked.md` again, which files another Blocked subtask and exits. Every human
  unblock is immediately re-blocked: **a run that cannot exit.** (Numerically it is "forward",
  which is why the "only greater" rule does not save it; 90 is terminal, not a successor phase.)
  The live run's `30 EXIT: … phase -> 40` line is fine; the hazard is the 90 tag.

## 5. `deploy.py` — **OK**

`python3 -m py_compile fleet/bin/deploy.py` → exit 0. `--dry-run update` (live: only
`coworld-builder-hourly` = `depl_01YSmungQBmAMerqw9KxGdQs`):
```
--- POST /agents/agent_01Hxx6czhYKwmEJ7CkMnXb1W (coworld-builder-coordinator) ---   ← new AGENT.md body (contains "three hourly crons")
ADOPTING legacy deployment coworld-builder-hourly depl_01YSmungQBmAMerqw9KxGdQs as coworld-builder-a (rename + reschedule, same id)
--- POST /deployments/depl_01YSmungQBmAMerqw9KxGdQs (coworld-builder-a) ---
{ "agent": {"id": "agent_01Hxx6czhYKwmEJ7CkMnXb1W", "type": "agent", "version": 1}, "name": "coworld-builder-a" }
MISSING live deployment coworld-builder-b — run `create` to add it; `update` reconciles only what exists
MISSING live deployment coworld-builder-c — run `create` to add it; `update` reconciles only what exists
deployments (3 configured): coworld-builder-a cron=11 * * * * reconciled; coworld-builder-b … MISSING — run create; coworld-builder-c … MISSING — run create
```
Code: `deploy.py:525-535` adopts the legacy object when `-a` is absent (same id, POST to
`/deployments/<id>`, `:567`); no `POST /deployments` in `update`, so no second cron. The agent
`version` in the dry run is the live v1 because nothing was POSTed; in a real run `rows[COORDINATOR]`
takes the new version from the POST response (`:519-522`) and the deployment payload repoints to it
(`:561-563`). `DEPL_FIELDS` includes `name` (`:70`), so the rename is diffed and sent.

`--dry-run create` prints POSTs for all seven agents and all three deployments (it does not read
live state, stated at `:390`); real `create` SKIPs by name (`:400-404`, `:421-425`, `:447-451`) and
refuses `-a` while `coworld-builder-hourly` is live (`:453-458`), so it only adds `b` and `c` and
never touches `-a`. `--dry-run status`:
```
--- GET /deployment_runs?deployment_id=depl_01YSmungQBmAMerqw9KxGdQs&limit=5 (coworld-builder-a, cron 11 * * * *) ---
--- GET /deployment_runs?deployment_id=<coworld-builder-b id not yet in cloud.md — run create>&limit=5 (coworld-builder-b, cron 31 * * * *) ---
--- GET /deployment_runs?deployment_id=<coworld-builder-c id not yet in cloud.md — run create>&limit=5 (coworld-builder-c, cron 51 * * * *) ---
```
`cmd_status` catches the per-deployment `SystemExit` (`:631-634`) so a missing `b`/`c` does not
abort `a`'s status.

## 6. Starvation / fairness — **OK**

Adoption order is fixed (a) stale/ended Running → (b) unblocked → (c) claim → (d) exit
(`00-claim.md:9-12`, `AGENT.md:27-40`), and within (a) "adopt the one with the **oldest**
`heartbeat_at`, exactly one per heartbeat, log the ones not adopted" (`00-claim.md:77-79`).
Once adopted, that run's `heartbeat_at` is refreshed and `session_ended_at` cleared (`:210-211`),
so the next cron's oldest-first pick is a *different* run; with 3 crons/hour and 3 runs, each
stale run waits at most ~60 min. Resumes are never gated by the cap (`cloud.md:30-31`,
`00-claim.md:106`), and Blocked ≥ 2 gates only new claims (`:99-102`). No path leaves a
stale/ended run unserviceable.

Two MINOR fairness notes: (i) the closing step writes `session_ended_at = now` in STATE and
*then* "update `heartbeat_at` on the run task" (`AGENT.md:224-229`); if the Asana stamp is taken
later than `session_ended_at`, the run reads fresh and waits the full 90 min instead of being
picked up at the next cron — pre-existing text, but now it costs a slot under the cap. (ii) The
Running-section listing is not ordered; "oldest `heartbeat_at`" is deterministic given the
custom-field values, fine.

## 7. Single-run remnants in templates / README — **MINOR**

- `templates/run-task.md:33-35` (inside the Asana description every new run task gets):
  "Coordinator: coworld-builder (hourly heartbeat, minute 11). This task is the lock: while it
  sits in Running with a fresh heartbeat_at … **no other run starts**." Still the single-run model.
- `templates/README.md:207` "The field is the lock" — softened by the rest of the sentence
  (`:207-210`), acceptable.
- `README.md:3-16`, `:85-89` — updated correctly.

## New findings

| # | severity | finding | one-line fix |
|---|---|---|---|
| F1 | **BLOCKING** | 5.0a phase-drift repair treats `90 blocked …` log lines as a phase tag and repairs `STATE.phase` to `"90"` on every unblock-resume → the run re-enters phase 90 and is re-blocked forever (run that cannot exit). | In `00-claim.md` 5.0a (and AGENT/SPEC mirrors): "consider only tags `10`…`80`; ignore `90` and `00`", and pin the tag grammar (`^<UTC> (\d\d) ` or `phase=(\d\d)`). |
| F2 | MINOR | 5.0 step 2 writes the 5.1 counter *before* 5.0a repairs the phase, contradicting "the 5.1 counter then applies to the repaired phase". | Move the 5.0a scan (read-only) ahead of the 5.0.2 write and fold the repaired phase into that single write. |
| F3 | MINOR | Cap overshoot by concurrent heartbeats (`cap + concurrent−1`, practically `cap+1`) is real and undocumented. | One sentence in `cloud.md` §Parallelism / SPEC §Parallelism: "worst case cap+1 when a manual or retried run overlaps a cron; no re-check after claim". |
| F4 | MINOR | The repair line `00 resume: STATE phase repaired …` has no `session=` nonce; a session applying the "any `00 resume` line with a foreign nonce" rule literally may misread it as foreign and exit. | Rename it `00 repair phase <old> -> <new> from log session=<nonce>`. |
| F5 | MINOR | `templates/run-task.md:33-35` still says minute 11 / "no other run starts". | Replace with "hourly heartbeats a/b/c (11/31/51 UTC); a fresh heartbeat_at means a session is working this run; up to max_parallel_runs run at once". |
| F6 | MINOR | Closing step may stamp Asana `heartbeat_at` after `session_ended_at`, making an ended run look fresh for 90 min (and hold a cap slot). | `AGENT.md` §Ending: "use one stamp for STATE.heartbeat_at, session_ended_at and the Asana field". |
| F7 | MINOR | `prompts/30-review-loop.md:155` says STATE `phase: "40"` (or `"90"`) while `90-blocked.md:16,82-84` keeps `STATE.phase` at the failed phase — pre-existing, but with F1 it decides which of two wrong behaviours a blocked phase-30 run gets. | Make 30-review-loop write the failed phase, never `"90"`. |

BLOCKING: 1
