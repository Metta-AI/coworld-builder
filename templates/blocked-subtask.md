# Blocked subtask template (phase 90)

Goes to: a **subtask of the run task** on the Coworld Builder board, assigned to
**David Bloomin** (`1209016834701578`). The run task itself moves to *Blocked*.
Written by `prompts/90-blocked.md`. SPEC §Blocked.

Substitute: `<slug>`, `<phase>` (`00`…`80`), `<one-line ask>`, `<run>`, and the bodies below.

---

## Title

```
BLOCKED <slug> @<phase>: <one-line ask>
```

The one-line ask is the **decision, credential, or action a human must supply** — not a
description of the symptom. Good: `grant Metta-AI org secret SOFTMAX_TOKEN to cogame-tessera`.
Bad: `certification keeps failing`.

## Body

```
WHAT FAILED
<the exact error text — command, exit code, and the operative lines of output or log,
 verbatim, in a fenced block. Never a paraphrase. Include the CI run URL and the
 artifact name if the failure was in GitHub Actions.>

WHAT I TRIED
1. <attempt 1 — the approach, the result, the exact error>
2. <attempt 2 — a DIFFERENT approach, the result, the exact error>
3. <attempt 3 — a DIFFERENT approach, the result, the exact error>

WHAT I NEED
<exactly one decision, credential, or action. If it is a decision, state the two or three
 readings and what each one makes the game; recommend one. If it is a credential, name the
 secret, the scope, and where it must live. If it is an action, name the click.>

CONTEXT
Run:   runs/<run>/ (STATE.json, log.md)
Repo:  https://github.com/Metta-AI/cogame-<slug>
Phase: <phase> — <phase name>

Resume: complete this subtask; the next heartbeat resumes at phase <phase>.
```

## Rules

- The coordinator writes `STATE.blocked` with the same four fields
  (`what_failed`, `attempts`, `need`, `phase`) and pushes, then **exits**. It does not
  keep working, and it does not start another idea.
- One comment goes on the **idea task** pointing at this subtask.
- The next heartbeat that sees the run task in *Blocked* with this subtask **complete**
  moves it back to *Running* and resumes at `STATE.json.phase`. An incomplete subtask
  means the heartbeat exits.
- Never file this for something the rails say the agent decides itself: starter choice,
  the scoring rule when the idea pins one, seat count, parameter tuning, viewer
  composition, policy prompts, version bumps, or picking between two equivalent API
  shapes. **Blocked** is only for: a missing credential or permission, a platform outage
  persisting > 45 minutes, a rule the idea leaves genuinely open *and* whose readings lead
  to materially different games, a certification failure that survives three distinct
  fixes, and anything destructive.
- Three attempts means three *distinct approaches*, each logged in `log.md` before this
  subtask is written. Re-running the same command three times is one attempt.
