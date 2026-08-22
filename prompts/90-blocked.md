# Phase 90 — Blocked

Purpose: stop cleanly, hand a human exactly one decision, and exit.
Owner: coordinator. Entered by any phase that exhausts its retry budget.

## Precondition

**This phase requires a run.** It reads `STATE.*` and files a subtask *on the run task*, so it may
only be entered for a run that already has a run task and a committed `runs/<run>/STATE.json`. An
idea that cannot be started (confidential, or unmappable to any starter) never comes here — it is
**SKIPPED** by `prompts/00-claim.md` step 4.3, which comments on the idea, records the gid in
`runs/SKIPPED.json`, files a Fleet-section card for a human, and moves to the next idea.

## Inputs

- `STATE.phase` (the phase that failed), `STATE.phase_attempts`, `runs/<run>/log.md`.
- The three attempts' exact error text — quoted, never paraphrased, and **scrubbed** (below).
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
   - **Scrub before pasting.** CI logs and HTTP error bodies routinely carry credentials in URLs
     and headers. Replace anything token-shaped with `<redacted>` — `ghp_…`, `gho_…`, `ghs_…`,
     `github_pat_…`, `sk-ant-…`, `Bearer <…>`, `x-api-key: <…>`, `?X-Amz-Signature=…`,
     `?token=…` — and any `https://<user>:<pw>@host` form, before the text goes into Asana. The
     scrub never changes what failed: keep the message, mask the secret. (`AGENT.md` hard rule 1
     makes this absolute; this step is where it bites.)
3. Move the run task to *Blocked*.
4. Post **one** comment on the idea task — `STATE.idea_task`, the task gid, **not**
   `1217704774784096`, which is the Coworld *Ideas project* gid: blocked at phase `<n>`, one line,
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

A later heartbeat that finds this task in *Blocked* with **the subtask recorded in
`STATE.blocked.subtask`** completed moves it back to *Running*, sets `phase_attempts[<n>] = 0`
and `blocked = null`, and re-enters `prompts/<STATE.phase>-*.md`. That is implemented in
`prompts/00-claim.md` step 3 — this paragraph only describes it; the claim prompt is the one that
runs.
