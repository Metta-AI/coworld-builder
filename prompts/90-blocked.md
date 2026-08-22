# Phase 90 — Blocked

Purpose: stop cleanly, hand a human exactly one decision, and exit.
Owner: coordinator. Entered by any phase that exhausts its retry budget.

## Inputs

- `STATE.phase` (the phase that failed), `STATE.phase_attempts`, `runs/<run>/log.md`.
- The three attempts' exact error text — quoted, never paraphrased.
- `templates/blocked-subtask.md`.
- Asana: run task `STATE.run_task`, Builder project `1217747772236871` (section *Blocked*),
  assignee **David Bloomin** `1209016834701578`.

## When 90 is legitimate

Only: a missing credential or permission; a platform outage persisting > 45 minutes; a rule the
idea leaves genuinely open **and** whose readings give materially different games; a certification
failure that survived three *distinct* fixes; anything destructive.

**Never** for something the rails cover — starter choice, scoring when the idea pins one, seat
count, parameter tuning, viewer composition, policy prompts, version bumps, choosing between two
equivalent API shapes. If the reason is on that list, go back and decide it.

## Procedure

1. Write `STATE.blocked`:
   ```json
   {"phase":"40","at":"2026-08-22T16:40:00Z",
    "ask":"<one line: the single decision/credential/action needed>",
    "error":"<exact error text>",
    "attempts":["<what was tried 1>","<2>","<3>"],
    "subtask":"<asana gid>"}
   ```
2. Create a subtask on the run task from `templates/blocked-subtask.md`:
   - title `BLOCKED <slug> @<phase>: <one-line ask>`
   - assignee `1209016834701578`
   - body: **what failed** (exact error text in a code block), **what was tried** (the three
     attempts, each with what changed), **what is needed** (exactly one decision, credential, or
     action — not a menu), and the literal line:
     `Resume: complete this subtask; the next heartbeat resumes at phase <n>`
3. Move the run task to *Blocked*.
4. Post **one** comment on the idea task `1217704774784096`-side: blocked at phase `<n>`, one line,
   link to the subtask.
5. STATE: keep `phase` at the failed phase (the resume re-enters it), set `heartbeat_at`, commit,
   push.
6. **Exit.** Do not continue to another phase, do not retry, do not open a second subtask.

## Exit criterion

Run task in *Blocked*, exactly one open human subtask assigned to `1209016834701578`,
`STATE.blocked` populated and pushed, coordinator exited.

## Writes

- Asana: subtask, section move, one idea-task comment.
- STATE `blocked`, `heartbeat_at`; `log.md` line
  `<UTC> 90 blocked phase=<n> ask="<one line>" subtask=<gid>`.

## Retry budget

None — this is the terminal phase for the run. If Asana itself is unreachable, retry 3 times, then
write `STATE.blocked` and the log line anyway, push, and exit; the next heartbeat re-creates the
subtask.

## Resume

A later heartbeat that finds this task in *Blocked* with the subtask completed moves it back to
*Running* and re-enters `prompts/<STATE.phase>-*.md` with `phase_attempts[<n>]` reset to 0.
