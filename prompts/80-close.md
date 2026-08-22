# Phase 80 — Close

Purpose: write the executive summary, append the run's learnings, and mark both tasks done.
Owner: coordinator. This is the only phase that may complete the idea task.

## Inputs

- `runs/<run>/{STATE.json,log.md,VERIFY.md,design.md,reviews/*}`.
- `learnings/LEARNINGS.md` (append-only).
- Asana: run task `STATE.run_task`, idea task `STATE.idea_task`, Builder project
  `1217747772236871` (section *Done* — gid in `fleet/cloud.md`).

## Procedure

1. Write the executive summary (≤ 25 lines), in this order:
   - what the game is, in one sentence;
   - repo, coworld version + `cow_id`, league id + division id;
   - the two champions with their leaderboard rows, and the fillers;
   - rounds completed and the verified replay URL;
   - the Discord message link;
   - what went wrong and how it was fixed (one line per phase that used a retry);
   - anything left undone, named explicitly — a silent TODO is failure, not completion.
2. Post it as a comment on the **run task** and, condensed to 5 lines + links, on the **idea task**.
3. Append a dated section to `learnings/LEARNINGS.md`:
   `## <YYYY-MM-DD> <slug>` followed by only what a future run would do differently — new gotchas,
   API shapes that changed, starter advice. No restating the playbook. If a learning is general,
   also fold it into `playbooks/make-coworld.md` (the Common-mistakes table) or
   `playbooks/observatory-api.md` in the same commit.
4. Verify every phase subtask on the run task is complete; complete any that are not, or say in the
   summary why not.
5. Complete the **idea task** first; then move the run task to *Done* (the *Done* move is the last
   step, so a failure before it leaves the run in *Running* where the next heartbeat retries it).
6. STATE: `phase: "80"`, `heartbeat_at`, and a final `log.md` line. Commit and push everything.

## Exit criterion

Run task in *Done*, idea task `completed: true`, `learnings/LEARNINGS.md` has the new dated
section, and `runs/<run>/` is fully pushed.

## Writes

- Asana: two comments; run task → *Done*; idea task completed; all phase subtasks completed.
- `learnings/LEARNINGS.md`, possibly `playbooks/*.md`.
- STATE + `log.md`, committed and pushed.

## Retry budget

3 attempts per Asana call. A failure here is bookkeeping, not lost work: log it, leave the run
task in *Running* with a `close-failed` comment (and a `<UTC> 80 close-failed: <error>` log line),
and let the next heartbeat retry phase 80 — that retry is not counted by the resume counter
(`prompts/00-claim.md` step 5 exempts phase 80). **But after 3 `close-failed` heartbeats** (count
the `80 close-failed` lines in `log.md`), go to `prompts/90-blocked.md` with the exact Asana error:
Blocked takes the task out of *Running* so the queue moves on; the human finishes the bookkeeping.
A run parked in *Running* forever would stop every future claim.
