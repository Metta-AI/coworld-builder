# Phase 75 — Atlas

Purpose: give the shipped coworld its dot on the Softmax Atlas (`https://softmax.com/atlas`), so
the map never falls behind the leagues. Owner: coordinator. One pull request against
`Metta-AI/metta`, opened by a workflow, merged by itself.

The atlas is a **static page built from a snapshot**: adding a coworld means one line in
`places.mjs`, a re-run of `fetch-stats.mjs` + `build.mjs`, and a commit of the regenerated
`public/atlas/index.html`. The sandbox has neither node nor a metta mount, so — exactly as with
every compile in this system — you decide, and GitHub Actions does the mechanical half.

## Inputs

- `STATE.slug`, `STATE.run`, `STATE.league.id`; `runs/<run>/design.md` (what kind of game it is —
  that is what picks the continent).
- `tools/atlas_spot.py` and `.github/workflows/atlas-update.yml` in this repo.
- `Metta-AI/metta` → `web/softmax.com/src/scripts/atlas/README.md` is **authoritative** for
  everything this prompt summarises. Read it if anything below does not match what you see.

## Procedure

0. **Resume guard.** If `STATE.atlas.status` is non-empty — `pr_open`, `already_placed` or
   `unplaced` — this phase is finished: go to phase 80. Never open a second atlas PR for one run.
   (`templates/STATE.template.json` ships it as `""`, which means not yet done.)

   **Never enter this phase before phase 60 passed.** `build.mjs` refuses a `CITIES` line whose
   slug `/api/coworlds` does not list (`places.mjs names a league that is not in
   data/coworld-stats.json`), and a league with no completed rounds is not there yet.

1. **Confirm the slug the atlas keys on** — it is the `slug` from the public directory, not your
   repo name. A coworld's default league is its own slug; a sub-league looks like `paintbot/ctf`.
   ```bash
   curl -sS https://softmax.com/api/coworlds -H 'user-agent: coworld-builder/1' \
     | jq -r --arg s "$SLUG" '.coworlds[]|select(.slug==$s)|[.slug,.name,.episodes_7d]|@tsv'
   ```
   Empty output means the league is not in the directory yet. Do **not** invent a slug: log
   `<UTC> 75 atlas slug-not-live slug=<slug>`, take the give-up path (step 8, reason
   `league not in /api/coworlds`), and go to phase 80.

2. **Choose the continent.** From what the game *is* (the design note), never from the repo name:

   | Continent | key | what lives there |
   |---|---|---|
   | The Paintlands | `paintlands` | zero-sum: shooters, tanks, battle royales, RTS |
   | The Great Simulations | `simulations` | borrowed worlds: WoW, Factorio, NMMO, tribal worlds |
   | The Tabletop Coast | `tabletop` | board and card game ports |
   | The Cozy Shire | `shire` | BitWorld villages: gardens, platformers, blocks |
   | The Commons | `commons` | mixed-motive: shared stocks, supply chains, rulebooks |
   | The Parlour Peninsula | `parlour` | talk games: party, hidden-role, language |

   `incognita` is **Terra Incognita — proposals only**. Nothing live goes there, ever. This is a
   rails call (`AGENT.md` §Rails): decide it, do not ask. Say which continent and why in `log.md`.

3. **Pick the coordinates.** Overview units — the map as a 1024×1024 image. Read the live geometry
   and let the tool find the room:
   ```bash
   gh api repos/Metta-AI/metta/contents/web/softmax.com/src/scripts/atlas/places.mjs \
     -H 'Accept: application/vnd.github.raw' > /tmp/places.mjs
   python3 /workspace/coworld-builder/tools/atlas_spot.py --places /tmp/places.mjs --region <key>
   # -> "425 553 42.6"  = x, y, and how far the nearest neighbour is
   ```
   It sweeps the continent's **outline** (`REGION_PATHS`) intersected with its fly-to `box`, keeps
   14 units off the coast, and returns the roomiest point nearest the continent's existing
   cluster. Exit code 3 means the continent is crowded (best clearance < 22): take the spot it
   printed anyway and record the clearance in `log.md`. **Never move a dot outside the outline to
   win clearance** — the corners of a `box` are open sea.

   `label` is the coworld's display name, ≤ 16 characters, and `anchor` is `c` (centres the label
   under the dot). Leave `anchor` empty only to hang a label to the right of a crowded dot.

4. **Territory: skip it.** Territories are the dashed borders drawn around a coworld that fields
   *several* leagues. A first run fields one, so leave `territory` empty. If this run's coworld
   really does have several leagues, add the `TERRITORIES` entry by hand later
   (metta atlas `README.md` §A coworld with several leagues) — it needs an SVG blob drawn around
   the cities, which is not a rails call you can make from a coordinate list.

5. **Dispatch the workflow.**
   ```bash
   gh workflow run atlas-update.yml -R Metta-AI/coworld-builder \
     -f slug="$SLUG" -f label="$LABEL" -f x=<x> -f y=<y> -f region=<key> \
     -f anchor=c -f run="$RUN"
   ```
   Then find your run and watch it. The workflow's `concurrency: atlas-update` group serialises
   atlas PRs, so **a queued run is not a stuck run** — wait it out; never dispatch a second time
   to hurry it:
   ```bash
   sleep 10
   RID=$(gh run list -R Metta-AI/coworld-builder -w atlas-update.yml -L 5 \
          --json databaseId,createdAt -q '.[0].databaseId')
   gh run watch "$RID" -R Metta-AI/coworld-builder --exit-status || true
   ```
   Write `<UTC> 75 atlas dispatch=<RID> region=<key> at=<x>,<y> clearance=<d>` to `log.md` as soon
   as you have the id — before the watch, so a session that dies mid-watch leaves a trail.

6. **Read the result from the artifact, never from the run's conclusion.**
   ```bash
   gh run download "$RID" -R Metta-AI/coworld-builder -n atlas-result -D /tmp/atlas
   jq . /tmp/atlas/atlas-result.json
   ```
   **Check `.slug` is yours** before believing it: another heartbeat's dispatch can be newer than
   yours in the `gh run list` above. If it is not, widen `-L` and take the run whose artifact
   carries your slug.

   | `.status` | what it means | what you do |
   |---|---|---|
   | `pr_open` | the PR is open, approved automatically, and queued behind a human's merge-when-ready | record `pr_url`, go to 7 |
   | `already_placed` | the slug already had a `CITIES` line and the page was current | record it, go to 7 |
   | `failed` | `.error` names the step and the last 20 lines | step 8 |

7. **Record it and move on.** Write STATE in one push:
   ```json
   "atlas": {"status": "pr_open", "pr_url": "https://github.com/Metta-AI/metta/pull/…",
             "branch": "atlas/<slug>-<run id>", "region": "commons", "x": 425, "y": 553,
             "dispatch_run_id": "<RID>", "attempted_at": "<UTC>"}
   ```
   plus `phase: "80"`, `heartbeat_at`, and these lines in `log.md`:
   `<UTC> 75 atlas pr=<url> status=<status>` and `<UTC> progress phase=75 marker=<pr url>`.
   Complete the phase-75 subtask on the run task and comment the PR url on it.

   **Do not wait for the merge, and do not expect to be the one who merges it.**
   `auto-approve-ai-docs.yml` in metta approves an atlas-only diff by itself (verified 2026-08-24),
   and the workflow arms `--squash --auto`. But **metta lands every PR through Graphite's merge
   queue** — `gh pr merge --auto` sits at `mergeStateStatus: BLOCKED` there no matter how green
   CI is, and a queued merge shows up on GitHub as *CLOSED* with `mergedAt: null`, which is not a
   failure. The sandbox has no Graphite credential, so the last step is a human's
   `gt submit --merge-when-ready` (or the Merge-when-ready button). Record the PR and move on;
   phase 80 reports it as `open (approved, waiting on the merge queue)`.
   Never merge it by hand, never `gh pr merge --admin`, and **never add the `blessed` label**:
   blessing is a human's, by policy.

8. **When the workflow fails.** Read `.error`; each cause has one named fix, and each fix is a
   **new dispatch** (every dispatch branches from a fresh `main` under a run-unique name — there is
   no force-push here, ever, `AGENT.md` hard rule 2):

   - `unplaced leagues (add them to CITIES in places.mjs): a, b` — other coworlds shipped and were
     never placed; the atlas cannot build until they are. Place them too: read each one's `name`
     and `description` from `/api/coworlds`, pick its continent from the step-2 table, run
     `atlas_spot.py` for it, and pass them all in `extra_cities` on the next dispatch:
     `-f extra_cities='[["ledger","Ledger",470,600,"commons",null,"c"]]'`. That is what the input
     is for. Name every league you placed for someone else in `log.md`.
   - `places.mjs names a league that is not in data/coworld-stats.json: x` — league `x` is gone
     from softmax.com and its map line is stale: `-f drop_slugs=x`. Removing a dead league's line
     from a map is not deleting a league — hard rule 3 is about the league itself.
   - `step=place … outside the <region> box` — the coordinates were hand-picked or the region was
     wrong. Re-run `atlas_spot.py` and take what it says; never nudge a number to get past the
     check.
   - `step=fetch-stats` — softmax.com was flaky, or one league page changed shape. Re-dispatch
     once. If it fails again naming the **same** league, the theater's payload shape moved and the
     regexes in `fetch-stats.mjs` need a human: give up (below) with that league named.

   **Three dispatches, then give up — and give up is not phase 90.** The coworld is already
   built, released, ranked, verified and announced; a missing dot on a map must never park a
   finished run in *Blocked*, where it would hold a slot of `max_parallel_runs` waiting on a
   human. Instead:
   - `STATE.atlas = {"status": "unplaced", "reason": "<the exact error>", "attempted_at": …}`;
   - `<UTC> 75 atlas unplaced reason="<…>"` in `log.md`;
   - **one** card in the Builder board's *Fleet* section (`1217747860605582`, `fleet/cloud.md`),
     assigned to David Bloomin (`1209016834701578`), titled `ATLAS <slug>: unplaced` — deduped by
     title, exactly like a SKIP card — whose body is the error, the three dispatch run ids, and
     the coordinates that were tried;
   - phase 80, which names it in the executive summary under what was left undone.

## Exit criterion

`STATE.atlas.status` is one of `pr_open`, `already_placed`, `unplaced`; the phase-75 subtask is
complete; `STATE.phase` is `"80"`, committed and pushed.

## Writes

- STATE: `atlas` (above), `phase: "80"`, `heartbeat_at`.
- `log.md`: the `75 atlas dispatch=…` line, the `75 atlas pr=…` / `75 atlas unplaced …` line, and
  `progress phase=75 marker=<pr url>`.
- Asana: phase-75 subtask completed, one comment with the PR url; on give-up, one Fleet card.
- `Metta-AI/metta`: one branch and one pull request, opened by the workflow — never a direct push
  to `main`.

## Retry budget

3 dispatches, each with a *different* fix from step 8, each logged. On exhaustion take the
give-up path in step 8 and continue to phase 80. This phase never enters `prompts/90-blocked.md`.
