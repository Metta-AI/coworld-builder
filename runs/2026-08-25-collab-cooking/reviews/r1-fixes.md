# r1 fixes — collab-cooking

Head: `a5ec2c8602856d21ad8ec3e4f70af7c6fab82ede` (`main`)
CI: https://github.com/Metta-AI/cogame-collab-cooking/actions/runs/32816344271 — **success**
(all three jobs green: `test` 200 passed / 1 skipped, `docker-smoke`, `wasm-viewer` including
`Load the bundle in a real browser`). The one skip is the pre-existing mount-presence guard
`test_viewer_contract.py:197` ("the coworld-ctf starter is not mounted here"), written in the
original commit and untouched this round. No test was deleted, skipped, weakened or its tolerance
widened; every test change this round is an added assertion or an added test.

Ten commits, one per finding, each `r1-O<n>: …`.

| finding | disposition | commit (remote) | files |
|---|---|---|---|
| O1 manifest rejected by `coworld build` | fixed | `f4c74bd` | `tools/build_manifest.py`, `coworld_manifest_template.json`, `tests/test_manifest.py`, `tools/ci/check_manifest_loads.py`, `.github/workflows/ci.yml` |
| O2 no frame-by-frame re-derivation test | fixed | `9ddcbce` | `tests/test_rederivation.py` |
| O3 pause branch skips the deadline guard | fixed | `1b7c075` | `live_episode.py:412-424`, `tests/harness.py`, `tests/test_episode.py` |
| O4 heat keyed to a different tile than the event | fixed | `59c50aa` | `replay.py:301-318`, `tests/test_replay_parse.py` |
| O5 tickets carry no `expires` | fixed | `2719860` | `replay.py` (`ticket_expiries`, `station_summary`), `live_episode.py`, `tests/test_replay_parse.py` |
| O6 two of four seats never connected in the smoke | fixed | `cccdf92` | `tools/ci/docker_smoke.sh`, `player.py`, `tests/test_player_client.py` |
| O7 tick events not in `DIFF_ORDER` | fixed | `2af3921` | `replay.py:319-325`, `tests/test_replay_parse.py` |
| O8 release secret under the slug, manifest reads `game.name` | fixed | `9ee8d7d` | `.github/workflows/coworld-release.yml`, `tests/test_manifest.py` |
| O14 stale return annotation in `obs_parser.py` | fixed | `80a624e` | `src/collab_cooking/agent/brain/obs_parser.py:40` |
| O18 fuzz pass is 320 plan objects, the note says 400 | fixed | `a5ec2c8` | `tests/test_baselines.py` |
| O9, O10, O11, O12, O13, O15, O16, O17, rest of O18 | not fixed (reasons below) | — | — |

---

## O1 — `coworld build` rejects the manifest template *(blocking)*

**Was:** top-level `version`, top-level `replay_viewer`, `game.display_name`, no `game.owner`.
Reproduced in this sandbox with the exact release pin
(`pip install coworld==0.1.42`; `coworld.bundle._load_template_manifest(raw, "0.1.0", {…})`) —
the same four `ValidationError`s the reviewer quotes.

**Is:** the generator (`tools/build_manifest.py`, the file the manifest is produced from) drops the
top-level `version` and `game.display_name`, adds `game.owner: "daveey@softmax.com"` (the value the
two most recent starters use), and moves `replay_viewer` under `game`, which is the only place the
package reads it from: `bundle.py:81` gates the `tools/build_replay_viewer.sh` hook on
`manifest.game.replay_viewer` and `upload.py:927` gates the bundle upload on
`manifest["game"]["replay_viewer"]`. The template was regenerated from it.

**Evidence:** the same loader call now returns
`OK, game.replay_viewer = bundle='static-replay-viewer' … game.owner = daveey@softmax.com`, and it
runs in CI: the new `test`-job step *"Validate the manifest with the pinned coworld's own loader"*
(own venv, `coworld==0.1.42`) printed in run 32816344271:

```
manifest OK: coworld_manifest_template.json loads with coworld's own template loader;
game.replay_viewer.bundle=static-replay-viewer, game.owner=daveey@softmax.com
```

`tests/test_manifest.py` now pins the **correct** shape rather than the old one:
`game.replay_viewer.bundle == "static-replay-viewer"`, no top-level `replay_viewer`, no
`game.display_name`, no `game.version` (the version comes from `--version`; a template that sets it
is refused by `bundle.py:38-41`), `game.owner` present, and the top-level key set inside what the
schema admits. A further test asserts the CI gate's coworld pin equals `coworld-release.yml`'s
`COWORLD_PKG`, so the gate cannot drift off the version the release runs.

**Checklist:** item 3 (*Static viewer* — the declaration is now where `coworld build` invokes the
hook from) and item 10 (*Manifest validates*).

## O2 — nothing re-derived the recorded state; no frame-by-frame test *(blocking)*

**Was:** the strongest cross-check was one scalar per seat (dishes recomputed from `serve` events,
`test_episode.py:46-62`). The viewer draws the recorded `c`/`st` arrays, which is the design note's
§Viewer/Pipeline decision — the sim is Python on a C++ core, does not compile to wasm, and must not
be reimplemented in Nim as a second source of truth for the rules. That decision stands; the
recording is what needed proving.

**Is:** `tests/test_rederivation.py` implements the middle path the review names. It takes nothing
but the replay's own bytes — the seed, the layout, the resolved config, each tick's recorded action
(`c[i][3]`), and the two flag bits that are wire facts rather than sim facts (a plan landing, a seat
absent) — feeds the actions back through a **fresh `Simulator`**, and rebuilds the tick records with
the real `ReplayWriter`. It then compares them to the recorded ones **frame by frame**:

* `c` — every cog's tile, carried item, action and flags (the blocked bit is re-derived from the
  sim's `last_action_success`, not copied);
* `st` — the whole station block *and* the omit-when-unchanged rule (an `st` present on one side and
  absent on the other fails);
* `sc` — per-seat delivered counts;
* `ev` — the derived event list, in order (events the sim cannot produce — `episode_start`, `plan`,
  `fallback`, `deadline`, `episode_end` — are kept where the recorder injected them);
* `heat` — the cumulative blocked-move map.

Three guard tests keep it honest: one asserts the fixture is not vacuous (240 ticks, >100 event-
bearing ticks, >100 `st` blocks, several distinct carried items), and two assert the comparison is
load-bearing by tampering — a cog moved one tile from tick 120, and one derived event dropped —
each of which makes the comparison fail.

**Evidence:** run 32816344271, `test` job:
`test_rederivation.py::test_replaying_the_recorded_actions_reproduces_every_tick PASSED` plus the
four others.

**Checklist:** item 2, second half ("A test asserts it") and its first half as stated —
"replaying the recorded events through the sim reproduces the recorded per-tick state frame by
frame". The viewer half (the viewer deriving its display from that re-derivation rather than a
parallel recording) is unchanged and remains the note's explicit architectural choice; I did not
build a Nim sim for it. That is the judge's call, as the reviewer says.

## O3 — the pause branch was an unbounded loop *(blocking)*

**Was:** `live_episode.py:412-415` — `if self.paused: await asyncio.sleep(0.05); continue`, so the
loop never reached step 10. `self.paused` is set by a control frame on `WS /global` (which accepts
any JSON frame) and cleared only by another frame: a paused episode advanced no step, never
evaluated the 720 s guard, never settled, and wrote no artifacts.

**Is:** the guard runs in the pause branch too, so a paused episode settles with
`reason: "deadline"`, real scores, both artifacts and exit 0.

**Evidence:** `tests/test_episode.py::test_a_paused_episode_still_settles_at_the_deadline` starts an
episode paused with the budget already spent and asserts it settles as `deadline` inside a 20 s
`asyncio.wait_for`. Reverting the two guard lines makes it fail with `TimeoutError` — I ran that
before committing. The harness gained `paused` and `run_timeout` parameters so a regression is a
failure rather than a hung suite.

**Checklist:** item 5 (*Degrade-never-hang* — "there is no unbounded loop"; category `hang`).

## O4 — heat and the `blocked` events named different tiles

**Was:** `heat` counted the tile the cog tried to **enter**; the event carried the cog's **own**
tile; the viewer accumulates the overlay from the event. In the previous CI replay the two key sets
barely overlapped.

**Is:** `heat` is keyed by the tile the event carries, so the replay's end-of-episode map is exactly
what the viewer accumulates live. The design note pairs the two (its example has
`{"ev":"blocked",…,"x":5,"y":3}` with `"heat":[[5,3,14]]`), and nothing reads the map by coordinate
except that overlay (`finalHeat` is used only for the jam beat's peak count).

**Evidence:** the test no longer compares totals — it compares tile for tile
(`{(x,y): n for x,y,n in heat} == blocked`), which is what let the divergence through. Checked
against the new CI replay: `heat==events: True` over 19 tiles.

## O5 — `st.board.tickets` carried no `expires`

**Was:** `{"i": …, "recipe": …}`; the viewer reads `entry{"expires"}.getInt(-1)` and counts an order
expiring only when `expires >= 0`, so `EXPIRING` could never fire.

**Is:** each live ticket carries `expires`, read from the schedule the env itself lays down
(`build_ticket_specs`, the same call `make_env` makes), so the tick counted down to is the tick the
engine expires the ticket on. The `/global` snapshot gets the same block.

**Evidence:** the browser smoke's own clock readout in run 32816344271 is now
`TICK 242 OF 480 3 ORDERS LIVE · 1 EXPIRING` — the exact string §Readouts specifies, where the
previous run had no expiring clause. `tests/test_replay_parse.py` asserts every live ticket's
`expires` equals `arrival + ticket_deadline` (capped at `max_steps`), that it is still in the
future, and that some frame is inside the 12-tick window; the CI replay has 219 such frames.

## O6 — two of four seats never connected in the container smoke

**Was:** the game and the four players started back to back with no readiness gate; the first dials
hit a uvicorn that was not listening; `websockets.connect` raised; `player.py` caught it and exited
0 — correct for a dead socket, wrong for one that is not up yet. Result:
`disconnected: [true,true,false,false]`, the prompt seat absent, `cross_play: false`, 1 dish, and a
green job.

**Is:** three changes. `docker_smoke.sh` waits for `/healthz` on the game container (probed from
inside it, since it publishes no host port; bounded at 120 s, and failed loudly if the container
dies first) before starting any player; the same script now fails if `results.disconnected` flags
any seat, so a smoke that seats half its policies is red; and `player.py` dials through
`connect_with_retry`, a bounded 60 s retry with exponential backoff that sits inside the game's own
90–120 s roster wait. A genuinely dead socket still exits 0.

**Evidence:** run 32816344271 `docker-smoke` log:
`waiting for /healthz on the game container (up to 120s) …` →
`game is serving /healthz; starting 4 player containers` → `every player container exited 0` →
`smoke OK: seats=4 … reason=complete`. The `smoke-replay` artifact's `results.json`:
`"disconnected": [false,false,false,false]`, `"seat_kinds": ["prompt","scripted:brigade",
"scripted:passer","scripted:courier"]`, `"cross_play": true`, `"dishes": 11`,
`"orders_expired": 16` — the fixture is now cross-play in fact, not only by construction.
`tests/test_player_client.py` pins the retry's two halves (succeeds on the third dial with a
doubling backoff; stops and re-raises once the deadline passes).

**Checklist:** not a falsification (item 7 was already satisfied in-process), but this is what the
container gate actually exercises, and it now exercises all four declared policies.

## O7 — the event list was not in `DIFF_ORDER`

`derive_events` sorts the tick's events into `DIFF_ORDER` before returning them; the sort is stable,
so ties still resolve by ascending slot. `tests/test_replay_parse.py` asserts both halves on a real
episode. Fixed rather than left because the note says the list *is* the specification and the change
is one stable sort.

## O8 — the release put the secret under the slug

**Was:** `coworld secret put "$SLUG"` → `collab-cooking`, while the runnable reads
`secret://coworld/collab_cooking/anthropic_api_key`. `coworld secret put`'s first argument is
documented in the pinned CLI as "Coworld game name or cow_… id" (`cli.py:434-443`), so the slug
namespace would have held a key nothing reads: `build_transport` marks itself disabled and every
league episode plays scripted with `cause: "disabled"`, silently.

**Is:** the step reads `game.name` out of the manifest, asserts the runnable's
`ANTHROPIC_API_KEY_URI` really is in that namespace before uploading anything, and puts and lists
the secret there. Dry-run of the extracted step: `WOULD-RUN coworld secret put collab_cooking
anthropic_api_key …`. `tests/test_manifest.py` pins that the step no longer uses `$SLUG`.

## O14 — a return annotation naming a symbol that no longer exists

`obs_parser.py:40` now says `KitchenObservationState`, the class the file actually defines.

## O18 — the fuzz pass ran 320 objects where §Tests 4 says 400

Every 4th tick of 400 across 4 seats = 400, and the count is asserted so it cannot drift back. The
other items in O18 are recorded as consistent or benign by the reviewer and need no change.

---

## NOTED (not fixed), with reasons

* **O9 — chrome provenance.** The reviewer verified the page reproduces byte-for-byte from
  `tools/build_broadcast_page.py` against the mounted ctf starter, that ctf's `<head>`, CSS and body
  markup are inherited unmodified, and that `chrome_common.js`/`broadcast_core.js` are byte-
  identical. What is re-authored is the behaviour script. Changing that is a rewrite of the viewer,
  not a fix, and the reviewer explicitly leaves the categorisation to the judge. No change.
* **O10 — the window is 13×13, not the note's 11×11.** The code takes the engine default and
  `docs/policies.md`, the manifest's policies page and `policy.py` all already say 13×13. Fixing it
  in code would mean pinning `ObsConfig(width=11, height=11)`, i.e. changing what every seat sees
  and every scripted baseline was written against — a design change, not a smallest-fix. The
  visibility *policy* (no seat sees more than another) is unaffected. Left for the note to correct.
* **O11 — the cog sprite is a committed PNG.** Four authored PNG facings, not a placeholder box;
  everything else is baked with `pixie` as the note describes. Replacing real art with generated art
  to satisfy a sentence in the note would make the viewer worse. Left.
* **O12 — the heat-map is dominated by station use.** True and by construction: using a station *is*
  a failed move (the note's own rule). Narrowing the map to `by: "cog"` would change what the idea's
  second ask ("collision heat-map") shows, and dropping station bumps loses the choke-point signal
  on `crowded`/`ring` that the layouts exist to produce. A design call, not a fix.
* **O13 — three executor behaviours looser than the note.** Each would change the brain's target
  selection (`handoff` reachability on both sides, zone-filtering station goals, unifying two "pass"
  sets). That is a behaviour change to the scripted baselines, which the note freezes for v1
  ("their behaviour is not retuned in v1"), and it would invalidate the baselines' legality/no-
  deadlock envelope without a harness to re-check it. Not attempted this round.
* **O15 — the player's fallback baseline is hard-coded.** The fix requires putting
  `fallback_scripted` on the wire in `player_config`, and the note enumerates that message's fields.
  With the default (`brigade`) the game and the player agree, so nothing diverges today; adding an
  undocumented wire field to fix a latent case is a protocol change and belongs with a note update.
* **O16 — a straggler worker can occupy a pool slot across turns.** Real, and the reviewer confirms
  nothing unbounded or blocking follows from it (`_plan_boundary` gates on `batch.finished`, which
  becomes true at the deadline). Fixing it properly means a per-turn executor or cancellable
  transport — a design change. Recorded, not made.
* **O17 — model text is DOM-only, so `canvas_text.total` is 0.** The reviewer verified by grep that
  the canvas draws no text at all (`fillText`/`strokeText`/`measureText` absent from all three JS
  files), which is exactly the condition under which checklist 15's worst-case renderer fixture does
  not apply ("a viewer that draws model text **on the canvas**"). The say band is already a reserved
  DOM band sized from the 120-rune cap. No change.

---

**Final state.** `main` = `a5ec2c8602856d21ad8ec3e4f70af7c6fab82ede`, CI run
**32816344271** — conclusion **success**
(https://github.com/Metta-AI/cogame-collab-cooking/actions/runs/32816344271).
