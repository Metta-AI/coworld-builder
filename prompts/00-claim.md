# Phase 00 — Claim

Purpose: decide whether this heartbeat owns a run, and if so create/adopt the run task and STATE.
Owner: coordinator. Every heartbeat starts here, including resumes.

## Inputs

- Asana project **Coworld Builder** `1217747772236871`, sections Running / Blocked / Done / Fleet
  (section gids in `fleet/cloud.md`).
- Asana project **Coworld Ideas** `1217704774784096` (board order = priority order).
- `runs/*/STATE.json` and `runs/SKIPPED.json` in this repo.
- `templates/run-task.md`, `templates/STATE.template.json`.

## Procedure

0. **Tool preflight — once, at the top of every heartbeat.** Every phase prompt pipes JSON through
   `jq` (00, 20, 40, 50, 60, 70). The sandbox is guaranteed `git`, `gh`, `curl`, `python3`; `jq` is
   expected but not guaranteed, so check it before you rely on it:
   ```bash
   command -v jq >/dev/null || echo "NO JQ"
   ```
   If it is missing, do **not** go to phase 90 and do not stop: every `jq` line in these prompts
   has a mechanical `python3` equivalent — `python3 -c 'import json,sys; d=json.load(sys.stdin);
   print(…)'` for reads and `json.dump` for writes. Use it, and record
   `<UTC> 00 jq missing — using python3 json` in `runs/heartbeats.log` (or the run's `log.md`
   once you own a run) so the gap is visible. Confirmed-present tooling belongs in
   `fleet/cloud.md` §Sandbox tooling.

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
   - Any *Running* task with `heartbeat_at` **< 90 min old** *and* whose
     `runs/<run>/STATE.json` has `session_ended_at` null or older than `heartbeat_at` → another
     run is live. **Exit immediately.** Write nothing.
   - A *Running* task with a **stale** `heartbeat_at` (≥ 90 min), **or** one whose
     `session_ended_at` is ≥ its `heartbeat_at` (the previous session ended deliberately and
     said so) → it is yours. Go to step 5 (resume). The second case is what keeps a
     multi-session run moving on the very next hourly firing instead of every other one.
   - If **more than one** *Running* task qualifies, adopt the one with the **oldest**
     `heartbeat_at`, and **adopt exactly one per heartbeat** — never carry two runs forward in a
     single session. Log the ones you did not adopt by gid; the next heartbeat takes the next.
3. Else list *Blocked* tasks. For each, identify **the human subtask** — never "a completed
   subtask": every run task carries eight phase subtasks (10…80) that phase 80 completes as the
   run progresses, so a completed phase subtask means nothing here.
   1. Read `runs/<run>/STATE.json` and take **`STATE.blocked.subtask`** (the gid phase 90
      recorded at `prompts/90-blocked.md` step 1). That is the human subtask.
   2. Only if `STATE.blocked.subtask` is missing, fall back to the subtask whose name starts with
      `BLOCKED ` (the title prefix phase 90 sets) and which is assigned to `1209016834701578`.
   3. If that one subtask is `completed: true`, move the task to *Running*, then **clear the
      block before resuming**: set `STATE.phase_attempts[<STATE.phase>] = 0` and
      `STATE.blocked = null` (the human answered; the phase gets its full budget back, and a
      finished run must not still report `blocked` to the human reading path in `README.md`).
      Append `<UTC> 00 resumed after unblock subtask=<gid> attempts_reset=<phase>` to `log.md`,
      commit, push (the rejected-push rule at the end of step 4 applies to this push too), and
      go to step 5 — whose **session-nonce guard (step 5.0) runs on this path as well**; an
      unblocked run is as raceable as a stale one. If it is still open, leave the task in *Blocked* and move
      on — never resume on a phase subtask's completion.
   **If a *Blocked* run's subtask is still open, control falls through to step 4 and this
   heartbeat claims a NEW idea.** That is deliberate: concurrency is 1, and a run waiting on a
   human must not stop the queue. Two bounds on it:
   - **At most 2 run tasks may sit in *Blocked* at once.** If there are already 2, do **not**
     claim a new idea — log `<UTC> 00 idle: <n> blocked runs, not claiming` and exit. A third
     blocked run means the humans are the bottleneck and more work would only pile up.
   - Blocked runs are checked (step 3) on **every** heartbeat, before any new claim, so an
     unblocked run always resumes ahead of new work.

4. Else claim work. **Claiming races** — two overlapping heartbeats (the cron plus a manual
   `deploy.py run`, or a retried deployment run) can both see an empty board. The comment-first
   claim below is the guard (`/workspace/cogamer/fleet/PROTOCOLS.md` §CLAIM PROTOCOL exists
   because plain "look then create" claims raced four confirmed times); do every step, in order.
   1. **`git pull --rebase`** in `/workspace/coworld-builder` *before* reading anything from it —
      the dedupe below is only as fresh as the mount.
   2. List incomplete Coworld Ideas tasks in board order and take the top one that is **not**
      already spoken for. Skip an idea if any of these hold:
      - its gid appears as `idea_task` in some `runs/*/STATE.json` (it has a run);
      - its gid appears in `runs/SKIPPED.json` (a previous heartbeat skipped it — step 4.3);
      - its comments carry a `skipped by coworld-builder:` line (same thing, seen from Asana;
        this is the belt-and-braces read for a SKIPPED.json that failed to push).
      ```bash
      jq -r '.[]' runs/SKIPPED.json      # the skipped gids, one per line
      ```
   3. **Can this idea be started at all?** Two gates, both applied *before* anything is created.
      An idea that fails either one is **SKIPPED** (step 4.3.1) — never sent to phase 90, which
      cannot run without a run task and a STATE (`prompts/90-blocked.md` §Inputs).
      - **Confidentiality — this idea's text becomes public.** Phase 20 creates a *public* repo
        and phase 10 copies the idea text verbatim into a design note that lands in it. If the
        idea's title or notes are marked confidential/internal/do-not-publish (any of
        `confidential`, `internal only`, `do not publish`, `NDA`, or an explicit instruction not
        to share) → SKIP with reason `marked confidential — a public repo would publish it`.
        Never paraphrase around it and proceed.
      - **Startability.** If the idea cannot be mapped to a starter at all (SPEC §Design pins:
        parley/babel, coworld-ctf, cogame-moba, cogame-factorio) *and* the gap is one the rails
        call a human decision rather than yours — the idea names an engine, platform, or asset
        set none of the six starters can host, or it leaves the game so open that the readings
        give materially different games (SPEC §Rails / §Blocked) → SKIP with that as the reason.
        Starter choice **between** the six is always yours; never skip for it.
      **How to SKIP an idea** — steps (a)…(e), in order. No run task, no STATE, no phase 90:
      - (a) Post **one** comment on the idea task: `skipped by coworld-builder: <reason>`. If
         that comment is already there, do not post a second one.
      - (b) Append the idea gid to `runs/SKIPPED.json` (a JSON array of gid strings, committed):
         ```bash
         jq --arg g '<idea gid>' 'if index($g) then . else . + [$g] end' \
            runs/SKIPPED.json > /tmp/s.json && mv /tmp/s.json runs/SKIPPED.json
         ```
      - (c) Create **one** card so a human sees it, on the Coworld Builder board in section
         **Fleet** (`1217747860605582`, `fleet/cloud.md`), assigned to **David Bloomin**
         (`1209016834701578`), titled `SKIPPED <idea title>: <reason>`, body = the idea's link,
         the reason, and what would unblock it (reword the idea, or say which starter to use).
         **Dedupe by title**: list the Fleet section's tasks first and create nothing if that
         exact title already exists. One card per idea, ever.
      - (d) Append `<UTC> 00 skipped idea=<gid> reason="<reason>" card=<gid>` to the heartbeat's
         closing note and to the shared `runs/heartbeats.log` (append-only; there is no run
         directory here and another run's `log.md` is off limits — `AGENT.md` hard rule 7),
         `git pull --rebase`, commit, push.
      - (e) **Continue to the next idea** — go back to step 4.2. The queue keeps moving; a skipped
         idea never blocks it, and never re-selects because 4.2 filters it out.
   4. `slug` = kebab-case of the idea title, ≤ 20 chars, no `cogame-` prefix.
      `run` = `<YYYY-MM-DD>-<slug>` (UTC).
   5. **Re-GET the idea task immediately before claiming it**
      (`GET /tasks/<gid>?opt_fields=completed,name`) plus its comments
      (`GET /tasks/<gid>/stories?opt_fields=text,created_at,created_by.name`). If it is now
      `completed: true`, or a `claimed by coworld-builder run <other>` comment already exists,
      or a `skipped by coworld-builder:` comment already exists (a concurrent heartbeat skipped
      it), drop it and go back to step 4.2 with the next idea.
   6. **Post the claim comment BEFORE creating anything**:
      `claimed by coworld-builder run <run>` on the idea task.
   7. **Wait 20 s, then re-read the idea's comments.** If a `claimed by coworld-builder run …`
      comment for a *different* run exists with an **earlier** `created_at` than yours, that run
      won: append `<UTC> 00 yield idea=<gid> to=<other run>` to the shared
      `runs/heartbeats.log` **and** say it in the heartbeat's closing note. Never write it into
      `runs/<other-run>/log.md` — that is another run's directory (`AGENT.md` hard rule 7).
      Create nothing else, and **exit**. Never delete the other claim.
   8. Create the run task in *Running* from `templates/run-task.md`:
      name `<slug> — coworld run <run>`, notes = the idea text verbatim + a link to the idea task.
      Create **one subtask per phase** (10, 20, 30, 40, 50, 60, 70, 80), unassigned, incomplete.
   9. Write `runs/<run>/STATE.json` from `templates/STATE.template.json` with `phase: "10"`,
      `phase_attempts: {}`, `blocked: null`, `heartbeat_at` = now, `session_ended_at: null`, and
      create `runs/<run>/log.md`.
   10. `git pull --rebase`, commit and push. **The rejected-push rule (below) applies here and
      on every resume**: if the push rejects because another heartbeat already pushed a
      `runs/<run>/STATE.json` for this idea, that run won — **do not force**: rebase, see its
      STATE, and exit.

**Rejected-push rule (claims and resumes alike).** A rejected push means another heartbeat wrote
this repo first. Never force, never `--force-with-lease` (`AGENT.md` hard rule 2). Always
`git pull --rebase` and then read what landed: on a **claim**, another `runs/<run>/STATE.json` for
your idea means that run won → exit; on a **resume**, a last `00 resume` line in `log.md` carrying
a different `session=<nonce>` means that session owns the run → exit. In both cases exit silently:
create nothing, write nothing, and do not retry the push.
5. **Resume path.** Reached from step 2 (stale/ended session) and from step 3.3 (a human
   unblocked the run). Both arrive here, and **both run the session-nonce guard below** — two
   heartbeats can observe the same free run at the same moment (the cron plus a manual
   `deploy.py run`), and without the guard both would resume it and work the same phase.

   **5.0 Session-nonce guard — do this before any phase work.**
   1. Mint a nonce for this session: `SESSION=$(python3 -c 'import secrets;print(secrets.token_hex(4))')`.
   2. `git pull --rebase`, then write `STATE.session_id = "<nonce>"` together with
      `heartbeat_at` = now, `session_ended_at: null`, and the resume count from step 5.1
      (one STATE write, one push — not two), and append
      `<UTC> 00 resume at phase <n> attempt=<k> session=<nonce>` to `log.md` — that exact
      format, `session=` last — commit and push.
   3. **If the push is rejected**, the other heartbeat got there first: `git pull --rebase`
      (never force — `AGENT.md` hard rule 2), re-read `log.md`. If its **last `00 resume` line
      carries a different `session=` nonce**, that session owns the run: append nothing, write
      nothing, and **exit**. Only if the last resume line is still yours (or there is none) may
      you push again.
   4. Write `heartbeat_at` = the same stamp on the Asana task (custom field
      `1217748424048134`). **Wait 20 s and re-GET that field.** If it has moved **past** your
      stamp, another session is heartbeating this run: **exit immediately**, leaving its value
      in place. Only when the field still holds your stamp do you enter the phase.

   **5.1 Count the resume — but only sessions that made no progress.** Read
   `runs/<run>/STATE.json`. The counter exists because a phase that reliably kills the session
   (sandbox OOM, an unbounded watch, a wedged poll) emits no failure of its own; it is **not**
   meant to punish a phase that legitimately spans several hourly sessions (phase 20's builds,
   phase 30's four rounds). So:
   - **First, look for progress.** Scan `runs/<run>/log.md` for a
     `<UTC> progress phase=<nn> marker=<value>` line for the **current phase** that is *newer
     than the last `00 resume` line*. That line is written by the previous session's closing step
     (`AGENT.md` §Ending a heartbeat) and names a phase-specific, monotone marker:

     | phase | progress marker |
     |---|---|
     | 10 | the design note gained a section, or was written |
     | 20 | a **new** `ci.yml` run id (a build or test run that did not exist last session) |
     | 30 | a **new** review round artifact (`r<n>-review.md` / `-fixes.md` / `-verdict.md`) |
     | 40 | a **new** `coworld-release.yml` dispatch run id |
     | 50 | a new league, division, submission, or filler registration id |
     | 60 | a new completed round id, or a check that turned TRUE in `VERIFY.md` |
     | 70 | `announce.attempted_at` written, or the message id adopted |

     If such a line exists, the last session progressed: set
     `STATE.phase_attempts[<STATE.phase>] = 0` and log
     `<UTC> 00 attempts_reset phase=<nn> reason=progress marker=<value>`.
   - **Then increment**: `STATE.phase_attempts[<STATE.phase>] += 1` (so a progressing run
     resumes at 1 every time), written and pushed by the 5.0 step-2 write, before any work in
     that phase. **At 3, enter `prompts/90-blocked.md`** instead of the phase, with the ask
     "phase `<n>` has ended three sessions without progress" and the last lines of `log.md` as
     the evidence — three *consecutive* markerless sessions, which is what the ask claims.
   - A resume that arrives via step 3, after a human unblocked the run, has just had the counter
     reset to 0, so it starts again at 1.

   **Phase 80 is exempt from this counter.** `prompts/80-close.md` §Retry budget says a failed
   close does not go to 90 — the run's work is already done and the next heartbeat simply retries
   the Asana calls. So on a resume with `STATE.phase == "80"`, do **not** increment
   `phase_attempts["80"]` and never enter 90 from it; log
   `<UTC> 00 resume at phase 80 (close retry, not counted) session=<nonce>` instead. No other
   phase is exempt.

   **5.2 Work the phase.** Having survived 5.0 and counted at 5.1, enter the prompt named by
   `STATE.phase`. You are the session that
   took the run; the closing step (`AGENT.md` §Ending a heartbeat) stamps `session_ended_at`
   again when you finish, and leaves `session_id` as it is so the next session can see whose
   session ended.

## Exit criterion

Exactly one of:
(a) exited because another run is live (a fresh `heartbeat_at` with no `session_ended_at`);
(b) exited because 2 runs are already *Blocked*, because this heartbeat **yielded** to an
    earlier claim comment, or because it **lost a resume race** at step 5.0 (its push was
    rejected and `log.md`'s last `00 resume` line carries another session's nonce, or the Asana
    `heartbeat_at` field moved past its stamp within 20 s) — in every case nothing was created
    and no phase work was done;
(c) exited into `prompts/90-blocked.md` because the resumed phase's `phase_attempts` reached 3
    (90 is only ever entered for a run that already has a run task and a STATE);
(c2) one or more ideas were **SKIPPED** (confidential / unstartable): each has one
    `skipped by coworld-builder: <reason>` comment, its gid in `runs/SKIPPED.json`, and one
    Fleet-section card assigned to David Bloomin — and the heartbeat then either claimed the
    next idea or exited under (a)/(b)/(d);
(d) a run task is in *Running*, its `heartbeat_at` is fresh, `runs/<run>/STATE.json` exists and
    is pushed, and control has entered `prompts/<STATE.phase>-*.md`.

Section moves (steps 3 and 4.8) are `POST /sections/<section_gid>/addTask {"data":{"task":…}}` —
shape and gids in `playbooks/observatory-api.md` §Non-Observatory calls and `fleet/cloud.md`.

## Writes

- Asana: run task (+ 8 phase subtasks), section *Running*, `heartbeat_at` (custom field
  `1217748424048134`); one comment on the idea. On a SKIP: one
  `skipped by coworld-builder: <reason>` comment on the idea task and one Fleet-section card
  (`1217747860605582`) assigned to `1209016834701578`, titled `SKIPPED <idea title>: <reason>`,
  deduped by title.
- `runs/<run>/STATE.json`, `runs/<run>/log.md` — committed and pushed. A heartbeat that owns no
  run writes to the shared `runs/heartbeats.log` instead, never into another run's directory.
- `runs/SKIPPED.json` (array of skipped idea gids) and `runs/heartbeats.log` — committed and
  pushed on every SKIP.
- `log.md` lines: `<UTC ISO-8601> 00 claim <run> idea=<gid> slug=<slug>`, and every heartbeat
  refresh as `<UTC ISO-8601> heartbeat phase=<nn>` — that exact format, since step 2 parses it.

## Retry budget

3 attempts on any single failing Asana/GitHub call (vary the approach: different opt_fields, plain
REST vs MCP, re-auth). On exhaustion → `prompts/90-blocked.md` with the exact error text. If the
Builder board itself is unreachable, do **not** create a run — exit and let the next heartbeat try.
