# Phase 00 — Claim

Purpose: decide whether this heartbeat owns a run, and if so create/adopt the run task and STATE.
Owner: coordinator. Every heartbeat starts here, including resumes.

## Inputs

- Asana project **Coworld Builder** `1217747772236871`, sections Running / Blocked / Done / Fleet
  (section gids in `fleet/cloud.md`).
- Asana project **Coworld Ideas** `1217704774784096` (board order = priority order).
- `runs/*/STATE.json` in this repo.
- `templates/run-task.md`, `templates/STATE.template.json`.

## Procedure

1. List *Running* tasks on the Builder board.
   ```bash
   curl -sS "https://app.asana.com/api/1.0/tasks?project=1217747772236871&opt_fields=name,completed,memberships.section.gid,custom_fields,notes" \
     -H "Authorization: Bearer $ASANA_PAT"
   ```
2. For each *Running* task read `heartbeat_at`. It is the **Asana custom field
   `1217748424048134`** (text, UTC ISO-8601, on the Coworld Builder project — gid in
   `fleet/cloud.md`). Read it out of the task's `custom_fields` array:
   ```bash
   HB=$(… | jq -r '.data.custom_fields[]|select(.gid=="1217748424048134")|.text_value')
   ```
   Write it with the custom_fields **map** keyed by that gid:
   ```bash
   curl -sS -X PUT "https://app.asana.com/api/1.0/tasks/<run_task_gid>" \
     -H "Authorization: Bearer $ASANA_PAT" -H 'content-type: application/json' \
     -d '{"data":{"custom_fields":{"1217748424048134":"2026-08-22T16:40:00Z"}}}'
   ```
   If the field is empty or absent, fall back to the last `heartbeat` line in `runs/<run>/log.md`,
   whose format is pinned as `<UTC ISO-8601> heartbeat phase=<nn>` (e.g.
   `2026-08-22T16:40:00Z heartbeat phase=40`). Nothing else counts as a heartbeat line.
   - Any *Running* task with `heartbeat_at` **< 90 min old** → another run is live. **Exit
     immediately.** Write nothing.
   - A *Running* task with a **stale** `heartbeat_at` → it is yours. Go to step 5 (resume).
3. Else list *Blocked* tasks. For each, identify **the human subtask** — never "a completed
   subtask": every run task carries eight phase subtasks (10…80) that phase 80 completes as the
   run progresses, so a completed phase subtask means nothing here.
   1. Read `runs/<run>/STATE.json` and take **`STATE.blocked.subtask`** (the gid phase 90
      recorded at `prompts/90-blocked.md` step 1). That is the human subtask.
   2. Only if `STATE.blocked.subtask` is missing, fall back to the subtask whose name starts with
      `BLOCKED ` (the title prefix phase 90 sets) and which is assigned to `1209016834701578`.
   3. If that one subtask is `completed: true`, move the task to *Running*, append
      `<UTC> 00 resumed after unblock subtask=<gid>` to `log.md`, and go to step 5. If it is still
      open, leave the task in *Blocked* and move on — never resume on a phase subtask's
      completion.
4. Else claim work. **Claiming races** — two overlapping heartbeats (the cron plus a manual
   `deploy.py run`, or a retried deployment run) can both see an empty board. The comment-first
   claim below is the guard (`/workspace/cogamer/fleet/PROTOCOLS.md` §CLAIM PROTOCOL exists
   because plain "look then create" claims raced four confirmed times); do every step, in order.
   1. **`git pull --rebase`** in `/workspace/coworld-builder` *before* reading anything from it —
      the dedupe below is only as fresh as the mount.
   2. List incomplete Coworld Ideas tasks in board order, skip any whose gid already appears as
      `idea_task` in some `runs/*/STATE.json`, and take the top one.
   3. `slug` = kebab-case of the idea title, ≤ 20 chars, no `cogame-` prefix.
      `run` = `<YYYY-MM-DD>-<slug>` (UTC).
   4. **Re-GET the idea task immediately before claiming it**
      (`GET /tasks/<gid>?opt_fields=completed,name`) plus its comments
      (`GET /tasks/<gid>/stories?opt_fields=text,created_at,created_by.name`). If it is now
      `completed: true`, or a `claimed by coworld-builder run <other>` comment already exists,
      drop it and go back to step 4.2 with the next idea.
   5. **Post the claim comment BEFORE creating anything**:
      `claimed by coworld-builder run <run>` on the idea task.
   6. **Wait 20 s, then re-read the idea's comments.** If a `claimed by coworld-builder run …`
      comment for a *different* run exists with an **earlier** `created_at` than yours, that run
      won: append `<UTC> 00 yield idea=<gid> to=<other run>` to the *builder* log (no run
      directory exists yet — write it to `runs/<other-run>/log.md` if present, else say it in the
      heartbeat's closing note), create nothing, and **exit**. Never delete the other claim.
   7. Create the run task in *Running* from `templates/run-task.md`:
      name `<slug> — coworld run <run>`, notes = the idea text verbatim + a link to the idea task.
      Create **one subtask per phase** (10, 20, 30, 40, 50, 60, 70, 80), unassigned, incomplete.
   8. Write `runs/<run>/STATE.json` from `templates/STATE.template.json` with `phase: "10"`,
      `phase_attempts: {}`, `blocked: null`, `heartbeat_at` = now, and create `runs/<run>/log.md`.
   9. `git pull --rebase`, commit and push. If the push rejects because another heartbeat already
      pushed a `runs/<run>/STATE.json` for this idea, that run won — **do not force**: rebase, see
      its STATE, and exit.
5. **Resume path.** Read `runs/<run>/STATE.json`, set `heartbeat_at` = now on both STATE and the
   Asana task, append a `resume at phase <n>` line to `log.md`, commit, push, and enter the prompt
   named by `STATE.phase`.

## Exit criterion

Exactly one of: (a) exited because another run is live; (b) a run task is in *Running*, its
`heartbeat_at` is fresh, `runs/<run>/STATE.json` exists and is pushed, and control has entered
`prompts/<STATE.phase>-*.md`.

## Writes

- Asana: run task (+ 8 phase subtasks), section *Running*, `heartbeat_at` (custom field
  `1217748424048134`); one comment on the idea.
- `runs/<run>/STATE.json`, `runs/<run>/log.md` — committed and pushed.
- `log.md` lines: `<UTC ISO-8601> 00 claim <run> idea=<gid> slug=<slug>`, and every heartbeat
  refresh as `<UTC ISO-8601> heartbeat phase=<nn>` — that exact format, since step 2 parses it.

## Retry budget

3 attempts on any single failing Asana/GitHub call (vary the approach: different opt_fields, plain
REST vs MCP, re-auth). On exhaustion → `prompts/90-blocked.md` with the exact error text. If the
Builder board itself is unreachable, do **not** create a run — exit and let the next heartbeat try.
