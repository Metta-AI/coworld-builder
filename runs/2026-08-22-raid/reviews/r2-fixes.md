# r2 fixes — raid
Head: `dc8ef5d84dfe1214b0b3e67b83fd101edff2f689`
CI: https://github.com/Metta-AI/cogame-raid/actions/runs/32623861432 — **success**
(`ci.yml`, `main`, sha `dc8ef5d`, jobs `test` / `docker-smoke` / `wasm-viewer` all `success`)

| finding | disposition | commit | files |
|---|---|---|---|
| B1 | **fixed** | `e0b84a1` + `ed9650f` (fix-forward) | `.github/workflows/ci.yml`, `tools/ci/docker_smoke.sh`, `tools/ci/viewer_smoke.mjs` |
| N1 | no change (evidence) | — | `src/raid/baselines.nim:187-200` |
| N2 | **fixed** | `dc8ef5d` | `docs/RULES.md:226-230`, `coworld_manifest_template.json` |
| N3 | no change (evidence) | — | `src/raid/control.nim:147-157`, `:352-358` |
| N4 | no change — adjudicated in r1 | — | `runs/2026-08-22-raid/reviews/r1-verdict.md` (F7) |
| N5 | no change (evidence) | — | `src/raid/telegraphs.nim:106-109` |
| N6 | no change — adjudicated in r1 | — | `runs/2026-08-22-raid/reviews/r1-verdict.md` (F12) |
| N7 | no change (evidence) | — | `src/raid/server.nim:250-255`, `docs/PROTOCOL.md:252` |
| N8 | not fixed, recorded open | — | `tests/test_server.nim` |
| N9 | no change (evidence) | — | `src/raid_player.nim:83-88` |
| N10 | no change (evidence) | — | `src/raid/llm.nim:185-188` |

---

## B1 — the `wasm-viewer` job never executed the viewer in a browser
**Checklist item 13 (Viewer executes), bullet 1.**

**What the code did.** At `6a8a68c` the `wasm-viewer` job built the bundle, asserted
`index.html` and a non-empty `.wasm` existed, and ran the emitted wasm module under node
(`tests/test_viewer.nim` → `tools/wasm_replay_smoke.cjs`). Nothing opened `index.html`:
`tools/ci/viewer_smoke.mjs` was absent from the tree, the job had no `needs: docker-smoke`
(both jobs started within a second of each other in run 32621942459), and `docker-smoke`
destroyed the only real replay CI produced — `tools/ci/docker_smoke.sh` validated
`${work_dir}/replay.json` inside a `mktemp` that the EXIT trap deletes, and uploaded nothing.

**What it does now** (commit `e0b84a1`, template-sourced, raid's substitutions):
- `tools/ci/viewer_smoke.mjs` — copied verbatim from
  `coworld-builder/templates/tools/ci/viewer_smoke.mjs` (byte-identical: blob
  `a1b1d4035425f0b277db95361f1a58db2d771cdc` in both repos, mode 100755; the template carries
  no substitutions). It serves the bundle over `http://127.0.0.1:<port>`, opens
  `index.html?replay=…`, fails immediately on `data-replay-error` or a bridge `error`, fails on
  silence at the timeout, and passes only on `data-replay-loaded="true"` (or the
  `coworld-replay` bridge's `ready`). It then scrubs to 0 % / 50 % / 100 % and prints the clock
  at each.
- `tools/ci/docker_smoke.sh` — the template's `SMOKE_REPLAY_OUT` copy-out restored
  (`replay_out="${SMOKE_REPLAY_OUT:-${repo_dir}/dist/smoke/replay.json}"` plus the final
  `cp "${work_dir}/replay.json" "${replay_out}"` block and its env doc). The file is now the
  template modulo the three scaffold substitutions (`raid`, `coworld-raid`, `5`) — verified with
  `diff -u`.
- `.github/workflows/ci.yml` — `docker-smoke` gains the `Upload the smoke replay` step
  (`name: smoke-replay`, `path: dist/smoke/`, `if-no-files-found: error`); `wasm-viewer` gains
  `needs: docker-smoke`, `Assert the viewer load test is present`, `Download the smoke replay`,
  `actions/setup-node@v4` (node 22), `Install Playwright (pinned 1.55.0)`,
  `Load the bundle in a real browser` (no `continue-on-error`, no `if:`) and the always-on
  `Upload the viewer smoke evidence` artifact.

**Fix-forward** (commit `ed9650f`). The first run of the new step, run
[32623414696](https://github.com/Metta-AI/cogame-raid/actions/runs/32623414696), failed with
`##[error]Process completed with exit code 2` before printing anything. Cause: the template's
`replay="$(ls dist/smoke/*.replay dist/smoke/replay.json 2>/dev/null | head -1)"` runs under
`set -o pipefail`; `dist/smoke/*.replay` matches nothing, `ls` exits 2, the pipeline (and so the
command substitution, and so `set -e`) inherits 2. Replaced with a `for` loop over the same two
candidates, so a non-matching glob is simply not a file and the real "docker-smoke uploaded no
replay" error can still fire. Exercised locally before pushing.

**Evidence — run [32623861432](https://github.com/Metta-AI/cogame-raid/actions/runs/32623861432),
`main`, `dc8ef5d`, conclusion `success`:**

- `docker-smoke` → `Raw-Docker episode smoke`:
  `smoke OK: seats=5 results=1440B replay=47263B reason=complete`
  `replay saved for the viewer smoke: /home/runner/work/cogame-raid/cogame-raid/dist/smoke/replay.json (47263 bytes)`
- `wasm-viewer` step 11, `Load the bundle in a real browser`, conclusion **success**:
  `loading dist/smoke/replay.json in dist/static-replay-viewer`
  `{"loaded":true,"ms":309,"clock":"0:00 TURN 0/10","scorebug":"0:00 TURN 0/10","feed_lines":0}`
  `scrub readouts: 0%="0:00 TURN 0/10"  50%="0:14 TURN 2/10"  100%="0:26 TURN 5/10"`
  (the three clocks differ, so the replay advances, not just renders one frame)
- The step is a plain `run:` — it is not skipped and not `continue-on-error`; its conclusion in
  `gh run view 32623861432 --json jobs` is `success`, and step 12 `Upload the viewer smoke
  evidence` uploaded `viewer-smoke.png` / `viewer-smoke.json`.
- `wasm-viewer` waited on `docker-smoke`: job timings in the same run are
  `docker-smoke started=06:47:55Z completed=06:48:58Z`… `wasm-viewer started=06:48:58Z`, i.e.
  wasm-viewer started only after docker-smoke finished (in run 32621942459 they started
  together).

That is item 13's required evidence: the browser loaded the bundle and the replay
`docker-smoke` produced, and reported `loaded: true`.

---

## N2 — the tick's ability sub-order carries a sixth phase the docs did not list
**Fixed, `dc8ef5d`.** `docs/RULES.md` step 8 listed `(a) interrupt, (b) taunt, (c) shield,
(d) heal completion, (e) attacks` while `src/raid/sim.nim:418-424` runs a sixth call,
`startHeals`, after attacks. The doc now names `(f) heal cast starts (seat order)` and why the
phase is last, quoting the invariant the code comment states (`src/raid/abilities.nim:191-193`:
a cast begun on tick `t` first ages on `t + 1` and lands exactly `HealCastTicks` = 24 ticks
later, pinned by `tests/test_combat.nim:62-83`). `coworld_manifest_template.json` regenerated
with `tools/build_manifest.py` because `game.docs.pages[rules.md]` inlines the file; the rebuild
was a no-op before the edit, so the manifest diff is exactly the one changed line.
No code change: the code's behaviour is the one the tests pin and the one the doc now describes.

## N1 — the `stalwart` baseline's reaction and stations differ from the note
**No change.** The departure is deliberate, argued in place at
`src/raid/baselines.nim:187-197`: 120 hp per 8 s cleave + 36.7 hp/s melee = 52 hp/s against a
45 hp/s sustained healer ceiling, so the note's `hold` is a slow wipe; the comment ends "So the
default reaction is `dodge`, not the note's `hold`." The stations are geometric, not nominal —
the dps cardinals sit on the 260 px `RangedRingPx` circle (the note's ranged ring) and the
healer stands are chosen for line of sight. Changing the code to the note's literal words would
lower the baseline the ladder is calibrated against; `tests/test_baselines.nim:161-176` pins
stalwart at more than 2× greenhorn on four seeds and `:191+` pins the crucible-duty `soak`
override. No checklist item names the baselines' reaction (item 7 asks for a full legal episode
+ a tuning harness, both present: `tests/test_baselines.nim:150-159`, `tools/tune_baselines.nim`).
Reconciling the design note is the note's owner's call, and I may not edit the note.

## N3 — two heal gates not in the note's control-layer spec
**No change.** Both gates are the r1 F4 disposition the judge accepted, and both carry their
reason at the site: `src/raid/control.nim:147-157` (`HealWasteFloor = 60` — overheal is recorded
and wasted, so never begin a cast that throws away two thirds of itself) and `:352-358`
(`planted` — a cast is cancelled by 8 px of movement, so never begin one on a tick the
controller still intends to walk). Removing either makes the scripted healer strictly worse and
would move the golden fixture. No checklist item covers the control layer's heal gating.

## N4 — first cleave/pour on tick index 95/191
**No change — already adjudicated.** `runs/2026-08-22-raid/reviews/r1-verdict.md` (F7): "keep the
code, keep the doc+test resolution … no checklist item names the start tick." `docs/RULES.md:134,146`
states the index and `tests/test_boss.nim:43` `testFirstCleaveAndPourTicks` pins both. Not
re-litigated.

## N5 — `avoidable_hits` excludes crucible hits
**No change.** Deliberate and documented at `src/raid/telegraphs.nim:106-109`: standing in a
crucible is the correct play (240 damage split beats a permanent Spill stack), so counting it
would make soaking look like a mistake. No doc claims otherwise — `avoidable_hits` appears in
`docs/PROTOCOL.md:189,286` and in `results_schema.properties.avoidable_hits` only as a field
name/array shape, with no semantic text to contradict. It is a per-seat meter, not part of the
score (`src/raid/scoring.nim:70` writes it; nothing reads it back).

## N6 — the game server still routes `/client/replay`
**No change — already adjudicated.** `runs/2026-08-22-raid/reviews/r1-verdict.md` (F12,
DISMISSED): the manifest declares `"replay_viewer": {"bundle": "static-replay-viewer"}`,
`coworld-release.yml:167-204` hard-fails certification unless the CLI reports the static bundle,
and both starters carry the identical local-debug route
(`/workspace/starters/coworld-ctf/src/ctf/server.nim:627`,
`/workspace/starters/cogame-bullwhip/src/bullwhip/server.nim:470`). Not re-litigated.

## N7 — `latency_ms` is the whole-batch latency
**No change.** `src/raid/server.nim:250-255` measures `epochTime()` around the single
`decideAll` call, which is the *only* call there is: `src/raid/llm.nim:269-283` issues one
`curly.makeRequests(batch, timeout)` per attempt for every open seat, so there is no per-seat
wall time to record without abandoning the one-parallel-batch shape the checklist requires. The
batch time is also the slowest seat's true time. `docs/PROTOCOL.md:252` lists `latency_ms` as an
`order` field and makes no per-seat-measurement claim, so no doc is falsified. Phase 60 reads
`source`/`intent`/`note`, not latency.

## N8 — two §Tests items are untested
**Not fixed; recorded open** (as in r1's F18 disposition). The 3.0 s done-broadcast bound is
*implemented and enforced* — `src/raid/server.nim:129-149` accumulates a `seats × 3.0 s`
allowance and **skips** a seat whose turn arrives after it is spent, which is what checklist
item 5 asks for; `broadcastDone` is a module-level proc over `shared.playerSockets` (live
`whisky` sockets), so testing it needs a websocket fixture that stalls a real reader — a new
test harness, not a small addition. Same for the no-show/reconnect e2e
(`server.nim:217-235`, `:405-416`): it needs a multi-container or in-process socket harness.
Neither is named by a checklist item and no existing test was weakened. Filed as work for a
later round rather than rushed in under a fix-forward deadline.

## N9 — the player container's receive loop has no timer
**No change.** `src/raid_player.nim:83-88` is the starter convention verbatim — compare
`/workspace/starters/cogame-bullwhip/src/bullwhip_player.nim:53-58` (`while true: let received =
socket.receiveMessage(); if received.isNone: break`). The bounded waits item 5 names are all
server-side; the connect side *is* bounded here (`raid_player.nim:66-77`, 5 attempts with
backoff then `quit(0)`), and the loop ends on `done` (`:93-95`), on `isNone` (`:85-87`) or when
the server exits (`src/raid/server.nim:267` `quit(0)` after `finishEpisode`). Adding a client
timer would risk a player that disconnects itself mid-episode for no checklist gain.

## N10 — `output_config.effort` for non-Haiku models
**No change.** `src/raid/llm.nim:185-188` is the starter convention verbatim, comment included:
`/workspace/starters/cogame-babel/src/babel/llm.nim:359-362` and
`/workspace/starters/cogame-bullwhip/src/bullwhip/llm.nim:342-345` carry the identical
`if "haiku" notin client.model and "4-5" notin client.model: body["output_config"] =
%*{"effort": "low"}`. Dropping it would diverge from every shipped starter's Anthropic request
shape; the note's "no `output_config.effort`" reads as the Haiku carve-out this code
implements. The failure mode is bounded either way (a 400 becomes `textOf` → `causeOf` → a
recorded `fallback` with the scripted order).

---

## NOTED (not fixed)

- **The builder template has the pipefail bug B1's fix-forward removed.**
  `coworld-builder/templates/ci.yml:296` still carries
  `replay="$(ls dist/smoke/*.replay dist/smoke/replay.json 2>/dev/null | head -1)"` under
  `set -euo pipefail`. Any repo that scaffolds it and produces `replay.json` (not `*.replay`)
  will fail its first browser step with a bare `exit code 2`. The loop form in
  `cogame-raid/.github/workflows/ci.yml` (commit `ed9650f`) is the fix; I did not edit the
  template, as it is outside this round's scope.
- `wasm-viewer` now installs Playwright and node 22 before the Nim toolchain steps, so the
  later `Run the viewer tests against the built bundle` step runs its node harness under node 22
  rather than the runner default. It logged `WASM-SMOKE OK` green in 32623861432; noted only so
  the change of node version is on the record.

## Runs

| run | sha | conclusion | note |
|---|---|---|---|
| [32623414696](https://github.com/Metta-AI/cogame-raid/actions/runs/32623414696) | `e0b84a1` | failure | `Load the bundle in a real browser` exit 2 (pipefail glob); `test` + `docker-smoke` green, and `wasm-viewer` already waited on `docker-smoke` |
| [32623664165](https://github.com/Metta-AI/cogame-raid/actions/runs/32623664165) | `ed9650f` | success | first green browser load: `{"loaded":true,"ms":296,…}` |
| [32623861432](https://github.com/Metta-AI/cogame-raid/actions/runs/32623861432) | `dc8ef5d` | **success** | head of `main`; `{"loaded":true,"ms":309,…}`, scrub 0/50/100 % all differ |

Final `main` sha: **`dc8ef5d84dfe1214b0b3e67b83fd101edff2f689`**
(`gh api repos/Metta-AI/cogame-raid/git/ref/heads/main -q .object.sha`).
