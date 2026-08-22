blocking: 0

# r4 verdict — coworld-builder (final verification)
Head: a4cc685 (`r4: …`)   Working tree clean.

## The four r3 findings

| # | r3 finding | fixed? | evidence |
|---|---|---|---|
| 1 | BLOCKING queue wedge: close failures escalate to 90 after 3 `close-failed` heartbeats, mirrored in 00-claim and SPEC, three agreeing | **TRUE (executable); SPEC has one stale clause — MINOR, see New finding 1** | `prompts/80-close.md:51-54` "after 3 `close-failed` heartbeats (count the `80 close-failed` lines in `log.md`), go to `prompts/90-blocked.md` with the exact Asana error". `prompts/00-claim.md:228-231` mirrors it ("after 3 `80 close-failed` lines in `log.md`, phase 80 itself goes to 90 so the run leaves *Running* and the queue moves"). `docs/SPEC.md:94-96` mirrors it ("after 3 `close-failed` heartbeats it too goes to 90 so a run can never sit in *Running* forever"). The wedge is closed: the run leaves *Running* on the 4th heartbeat at the latest, step 4 runs again. But `docs/SPEC.md:99` still ends the same paragraph with "phase 80 is exempt from the counter entirely (a failed close never goes to 90)", contradicting `:94-96` three lines above. `prompts/00-claim.md:224-225` ("a failed close does not go to 90") is loose but is immediately qualified at `:228-231`. |
| 2 | Boxed rejected-push rule and exit criterion (b) no longer say "last `00 resume` line" | TRUE | `prompts/00-claim.md:163-166` "any `00 resume` line in `log.md` with a foreign `session=<nonce>` that was not there before your pull (or a rebase conflict — abort it) … → exit (step 5.0.3)"; `:244-246` "its push was rejected and `log.md` gained a foreign-nonce `00 resume` line, or the rebase conflicted, or the Asana `heartbeat_at` field moved". `grep -rn 'last \`00 resume\`' --exclude-dir=reviews --exclude-dir=.git .` → **0 hits** (exit 1). Agrees with 5.0.3 `:180-185`, `AGENT.md:26-29`, `SPEC.md:39-42`. |
| 3 | 80-close step 5 completes the idea task before moving the run task to Done | TRUE | `prompts/80-close.md:31-32` "Complete the **idea task** first; then move the run task to *Done* (the *Done* move is the last step, so a failure before it leaves the run in *Running* where the next heartbeat retries it)". Writes list `:42` and exit criterion `:37` unchanged and consistent. |
| 4 | 60-verify fetches assets in two passes; no grep on unfetched files | TRUE | `prompts/60-verify.md:127` pass 1 greps only `/tmp/idx.html` (fetched at `:126`) for `(src|href)`; loop `:128-130` saves each to `/tmp/$(basename "$A")`; pass 2 grep at `:131` runs over `/tmp/idx.html /tmp/*.js` **after** the loop; `.wasm` loop `:132-134`. Check (c) `:139-140` greps `/tmp/static_replay.js`, which pass 1 fetched when the index lists it (as r3 accepted). |

## Mechanical checks

| check | result |
|---|---|
| `python3 -m py_compile fleet/bin/deploy.py && python3 fleet/bin/deploy.py --dry-run create` | exit 0 |
| `yaml.safe_load` templates/ci.yml / coworld-release.yml / coworld-submit.yml | OK — jobs `test,docker-smoke,wasm-viewer` / `release` / `submit` |
| `bash -n templates/tools/ci/docker_smoke.sh` | OK |

## New findings

1. **MINOR** — `docs/SPEC.md:99` "phase 80 is exempt from the counter entirely (a failed close never goes to 90)" survives from r3 and contradicts `docs/SPEC.md:94-96` in the same paragraph. Not blocking: the agent executes `prompts/80-close.md` §Retry budget (`:51-54`), which escalates, and `prompts/00-claim.md:228-231` points there; SPEC is descriptive. *Fix:* delete the parenthetical at `:99` or change it to "(a failed close is retried without counting; the escape is 80-close's own 3-heartbeat cap)". Same loosening applies to `prompts/00-claim.md:224-225` ("does not go to 90") — already qualified four lines later, so cosmetic.

No new duplicate run/repo path, queue wedge, infinite loop, secret leak, destructive action, release-order change, or unexitable phase found in the r4 diff (`git diff ce52e34..a4cc685` touches only 80-close, 00-claim, SPEC, 60-verify).

BLOCKING: 0
