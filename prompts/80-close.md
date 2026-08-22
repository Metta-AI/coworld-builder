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
5. Move the run task to *Done*; complete the **idea task**.
6. STATE: `phase: "80"`, `heartbeat_at`, and a final `log.md` line. Commit and push everything.

## Exit criterion

Run task in *Done*, idea task `completed: true`, `learnings/LEARNINGS.md` has the new dated
section, and `runs/<run>/` is fully pushed.

## Writes

- Asana: two comments; run task → *Done*; idea task completed; all phase subtasks completed.
- `learnings/LEARNINGS.md`, possibly `playbooks/*.md`.
- STATE + `log.md`, committed and pushed.

## Retry budget

3 attempts per Asana call. Failure here does **not** go to 90 — the work is done. Log the failure,
leave the run task in *Running* with a `close-failed` comment, and let the next heartbeat retry
phase 80. That retry is **not counted**: `prompts/00-claim.md` step 5 exempts phase 80 from the
resume counter, so repeated close retries can never trip the three-sessions budget into 90.
