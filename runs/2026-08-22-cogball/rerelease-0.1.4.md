# Re-release after the check-8 route-back — cogball

Written 2026-08-23T09:33Z by the phase-60 builder. Task: fix the diagnosed `COG_BASE`
viewer defect (`VERIFY.md` §"The root cause"), get CI green, re-release as **0.1.4**.

**Headline: the shipped fix is version 0.1.5, not 0.1.4, and the `cow_id` changed.**
Both are explained and evidenced below (§Deviations). The hosted viewer now renders the
league's own replay end to end — verified in headless chromium against the live iframe URL
(§Live proof).

---

## 0. What I found on arrival (important)

A **previous builder session did this work between 06:23Z and 07:16Z and never reported
back**: it pushed the fix, found and fixed a *second* viewer defect that only became visible
once the first was fixed, added CI guards, and ran two release dispatches (0.1.4 and 0.1.5).
None of it was recorded in `log.md`, `STATE.json` or `release-result.json`, so from the
coordinator's point of view it did not exist.

This pass therefore: audited every one of those commits and runs, re-verified the hosted
viewer independently (new run, new replay), and persisted the evidence. **No new release
dispatch was made** — 0.1.5 is canonical, certified, and demonstrably renders; a sixth
version would only churn the coworld and the policy set for nothing. That decision is a
deviation from the brief's literal "re-release as 0.1.4" and is called out in §Deviations.

---

## 1. The `COG_BASE` fix

Commit **`654fea615e9089bde1fc5ab0964c3f0f9b8f1d2e`** — *"viewer: restore COG_BASE so the
shell survives its own boot"* — `client/replay_broadcast.html`, +23/−4, one hunk of new code
plus a comment repair. It defines `COG_BASE` immediately before its only consumer
(`buildLockerRoom()`), branching on `window.CogballStaticReplay` (the global that only exists
when `static_replay.js` is on the page, i.e. in the static bundle) rather than on a URL param,
so the pod-route literal never has to appear in a static-bundle source (`test_viewer.nim`'s
`noPodReplayRouteShips` forbids that).

```diff
@@ -1700,6 +1701,25 @@ body[data-noviewpanel] #viewpanel { display: none !important; }
   var canvas = $('board');
   var statusEl = $('status');

+  // ---- where this page's own art lives -------------------------------------
+  // COG_BASE, not a root-absolute "/client/…": this page is served from THREE
+  // places and a leading slash is only correct at one of them.
+  //  - native server, bare:      the board's own client route → "" + /client/…
+  //  - native server, proxied:   the same route behind a Kubernetes service
+  //    proxy, /<prefix>/client/… — a leading slash would drop <prefix> and 404.
+  //  - the STATIC WASM BUNDLE:   /v2/coworlds/replays/static/<coworld>/<hash>/
+  //    index.html, where the art sits NEXT TO the page and there is no server
+  //    at all — a leading slash resolves to the API origin root and 404s.
+  // Stripping the trailing "/client/<page>" recovers the prefix, so the same
+  // expression serves all three. Mirrors ART_BASE in league_replayer.html and
+  // websocketPathForClientPage() in broadcast_core.js, which map the same
+  // /client + /clients route pair the same way. The bundle is detected by its
+  // WASM adapter rather than a URL param: window.CogballStaticReplay only
+  // exists when static_replay.js is on the page.
+  var COG_BASE = window.CogballStaticReplay
+    ? '.'
+    : location.pathname.replace(/\/clients?\/[^/]*$/, '') + '/client';
+
   // ---- pre-load curtain: the bot locker room -------------------------------
```

(The same commit also rewrites the stale comment at the `artBase` line and repairs a comment
line above `var WIRE = C.WIRE…`; no other behaviour changed.)

## 1b. The second defect, found only because the first was fixed

0.1.4 shipped the `COG_BASE` fix and **still did not play**: the shell booted, drew one frame,
and froze on tick 2 under "Replay failed: Failed to execute 'insertBefore'…".

Commit **`fb050fbea155acd5d078b355c4c1f2288c6f1ebf`** — *"viewer: pushFeed builds the row it is
handed"* — `client/replay_broadcast.html`, +9/−3. `pushFeed` still had paintbot's signature
(callers passed an *element*); every cogball caller passes an HTML *string*, so the first coach
note threw `TypeError` inside `insertBefore`, `static_replay.js` caught it in the Worker message
handler, called `showFailure` and latched `failed`, which makes `onWorkerMessage` drop every
later message. Fix: build the row element inside `pushFeed` from the HTML it is handed.

Commit **`f3f60a716d99924b247a310ce8a0471dbaa40f76`** — *"chrome: the momentum strip reads GOAL
LEAD"* — `client/league_replayer.html`, +1/−1: the momentum strip's label was still paintbot's
`LIVES LEAD` (design note §Readouts item 9 makes it goal difference). Nobody had ever seen it,
because the board never rendered before 0.1.4.

## 1c. The guards (the "cheap guard against this class of bug" the brief asked for)

Both are inside the coworld repo's existing `ci.yml`, in the existing `wasm-viewer` job, against
the **real built bundle** — no new infrastructure, no new workflow.

| commit | guard | what it catches |
|---|---|---|
| `46eedf43` | `tools/ci/viewer_shell_check.cjs` (+438) — runs each bundle page's scripts in document order inside a DOM-less browser stub | an identifier the page reads that nothing defines (**exactly the `COG_BASE` class**), any exception escaping a script, and a board page that finishes without starting its replay Worker (`data-replay-worker`). Verified both ways: reports `COG_BASE` on the shipped 0.1.3 `index.html`, passes on the fixed one. |
| `ed783928` | `tools/ci/viewer_smoke.mjs` (+529, coworld-builder's sanctioned load test plus a `--soak` flag) run in headless chromium against the built bundle and the fixture the native build just recorded | a viewer that boots and then dies on its first frame (**the 0.1.4 class**). `--soak` samples clock/tick/scorebug three times over eight seconds and requires the last interval to have advanced. Verified: 0.1.3 shell fails on load timeout, 0.1.4 shell fails `frozen: playback stopped advancing`, fixed shell passes. |

`--soak` is a **delta against `templates/tools/ci/viewer_smoke.mjs` in coworld-builder** and is
documented at the top of the coworld's copy so a human can fold it back upstream. Recording it
here as the template delta the builder brief asks for.

---

## 2. CI green on main

| run | sha | title | jobs | conclusion |
|---|---|---|---|---|
| **[32624523197](https://github.com/Metta-AI/cogame-cogball/actions/runs/32624523197)** | **`ed783928319d3405edbaaaf30a5e7926729eaa5e`** | ci: play the built bundle in a real browser… | `test` ✓ `docker-smoke` ✓ `wasm-viewer` ✓ | **success** |

`ed78392` is `origin/main` HEAD (verified `git fetch` + `git log -1 origin/main` at 09:26Z), and
it is the sha the 0.1.5 release built from. Earlier green runs on the chain: `32622815934`
(`46eedf43`), `32624495753` (`fb050fbe`). `32624510317` (`f3f60a71`) shows *cancelled* — it was
superseded 17 s later by the push of `ed78392`; its content is covered by `32624523197`.

---

## 3. Release dispatches

All in `Metta-AI/cogame-cogball`, workflow "Coworld release", `put_secret=true`, policies from
`tools/ci/policies.json` (no `-f policies` override), `skip_certify` not passed.

| # | run id | sha | version | conclusion | artifact verdict |
|---|---|---|---|---|---|
| 1 | [32623293246](https://github.com/Metta-AI/cogame-cogball/actions/runs/32623293246) | `46eedf43` | **0.1.4** | success | `ok=true canonical=true certify.ok=true secret_put=true`, `cow_795268b0-3cff-476f-be68-e73a5ba19084`. Shipped the `COG_BASE` fix — **but the hosted bundle still froze on tick 2** (the `pushFeed` defect), so this version does not satisfy check 8. |
| 2 | [32624985984](https://github.com/Metta-AI/cogame-cogball/actions/runs/32624985984) | `ed783928` | **0.1.5** | success | `ok=true canonical=true certify.ok=true secret_put=true`, `cow_ff38b98b-f611-4a74-86e1-f2b23cbd6339`. **This is the shipped release.** Artifact copied to `runs/2026-08-22-cogball/release-result.json`. |

No dispatch failed; the retry budget was not touched by this pass (0 of 3 spent by me).

### Final release-result (0.1.5) — `runs/2026-08-22-cogball/release-result.json`

```json
{"version":"0.1.5","ok":true,"canonical":true,"secret_put":true,"step_failed":null,"errors":[],
 "cow_id":"cow_ff38b98b-f611-4a74-86e1-f2b23cbd6339",
 "manifest_sha":"sha256:495905b153bc98135ae1ec127e8f4abc2b9c88cff6a6d1edf0934d161ec5dce7",
 "hosted_smoke":"passed","hosted_certification":"certifying"}
```
```
certify.ok             : true
certify.replay_liveness: Replay liveness: skipped (static replay bundle declared;
                         /client/replay and /replay not required)
```

`hosted_certification: "certifying"` is the same informational platform-internal field that read
`"failed"` on 0.1.3 (see `log.md` 05:38:51Z); it is not gated by the exit criterion, the hosted
smoke passed, and the coworld is canonical.

### Policy versions uploaded by the 0.1.5 dispatch (`GET /v2/policy-versions`, 09:28Z)

| role | label | `policy_version_id` | owner |
|---|---|---|---|
| champion #1 | `cogball-total:v4` | `05f90027-a9af-4526-99df-20dda36c47cb` | daveey |
| champion #2 | `cogball-counter:v4` | `49bdda05-ef1a-4153-83c8-ade64203a428` | **daveey-1** (`ply_bac48eb1-662e-44f8-973d-f3e016dccf5d`) ✓ |
| filler | `cogball-formation:v4` | `b68050fd-6666-4759-88c1-c4c5ce13eb69` | daveey |
| filler | `cogball-swarm:v4` | `2a7e3dbb-15e7-465d-af5e-02790d9468d5` | daveey |

(0.1.4's dispatch created the v3 set: `4336ea51` / `a9672583` / `72c587b9` / `5861d5b4`, same
ownership shape.) Four distinct labels per dispatch, champion #2 owned by daveey-1 exactly as in
0.1.3 — the exit criterion of `prompts/40-release.md` §4 is met. `policy_version_id` is null in
the artifact as documented; the UUIDs above are resolved from the API.

---

## 4. Live proof that the defect is actually gone

The brief's whole reason for existing. Instrument: `viewer-check.yml` in
`Metta-AI/coworld-builder` (phase 60 check 8's own tool), headless chromium, 180 s budget.

URL under test = the **live iframe `src`** the public page's own JS builds, obtained fresh at
09:22Z from `POST /v2/coworlds/replays/session` with the canonical coworld and the current
featured replay:

```
https://api.observatory.softmax-research.net/v2/coworlds/replays/static/
  cow_ff38b98b-f611-4a74-86e1-f2b23cbd6339/
  sha256%3A495905b153bc98135ae1ec127e8f4abc2b9c88cff6a6d1edf0934d161ec5dce7/index.html
  ?replay=…/replays/e6a6bf9a-bd32-45a8-8c86-ce2649163858.replay&v=2      (ready: true)
```

That replay is round 15's episode (`ereq_abe52df1-…`, completed 09:14Z) and is the same
`replayUrl` the server-rendered `state.playlist[0]` on `https://softmax.com/cogball` carries —
verified in the page HTML at 09:29Z, alongside `coworldId: cow_ff38b98b-…`,
`coworldVersion: "0.1.5"`.

**Run [32630840631](https://github.com/Metta-AI/coworld-builder/actions/runs/32630840631) —
conclusion `success`** (0.1.3's three runs were all red). Artifact committed to
`runs/2026-08-22-cogball/viewer-check-0.1.5/`.

```
{"loaded":true,"ms":1211,"clock":":01 STARTING IN",
 "scorebug":"DAVEEY 0% 0 sh 0  :01 STARTING IN  DAVEEY-1 0% 0 sh 0",
 "feed_lines":0,"failure":null,
 "signals":{"data_replay_loaded":"true","data_replay_error":null}}
scrub readouts: 0%=":01 STARTING IN"  50%="3:19 TURN 1/40"  100%="FINAL GAME OVER"
console_tail: (empty — no page errors at all)
```

Both of check 8's conditions now hold: `loaded: true` in 1.2 s (was: never, in 180 s), and three
**differing** clock readouts across the scrub. `viewer-smoke.png` shows the full-time card —
"DAVEEY-1 WINS", `1–2 · FULL TIME`, `reason: complete`, per-team goals / shots (on target) /
saves / possession / score, the pitch and turf paint behind it, the transport bar reading
`4912 / 4920`, and the momentum strip correctly labelled **GOAL LEAD**. The
"IN THE LOCKER ROOM" curtain is gone.

---

## 5. League: untouched

Nothing in this pass wrote to the league. Read-only confirmation at 09:28Z:

- `league_e87130ef-…` rounds 1–15 all `completed`; round 15 created 09:11:08Z, completed
  09:14:13Z — i.e. rounds have kept completing normally across the 0.1.4 and 0.1.5 releases.
- Leaderboard unchanged in shape: `daveey / cogball-total:v2` rank 1 (Elo 1029, 15 rounds),
  `daveey-1 / cogball-counter:v2` rank 2 (Elo 970, 15 rounds). Champions still the **v2**
  versions, submissions `sub_71aa526b` / `sub_e33fa105` untouched.
- `league.filler_policy_version_ids` still `["7c11dd63-…","259d11a4-…"]` (the v2 fillers).
- No v1/v2/v3 policy version was modified or deleted; v3 and v4 are additive uploads by the
  release workflow, exactly as the brief anticipated.
- `game_15d64bb0-…`'s `canonical_coworld_id` **followed the release by itself** to
  `cow_ff38b98b-…` — a platform-side effect of a canonical upload, not a league write.

---

## 6. Deviations (read these)

1. **The shipped version is 0.1.5, not 0.1.4.** Not the canonical-race cure: 0.1.4 released
   cleanly (`ok/canonical/certify.ok` all true) but its bundle still froze on tick 2 because of
   the second defect (§1b), which was only observable once `COG_BASE` was fixed. 0.1.5 is
   0.1.4 plus `fb050fb` + `f3f60a7` + the browser soak guard. Per `prompts/40-release.md` §6
   ("ship small fixes as version bumps during the run") this is the intended shape.

2. **The `cow_id` changed — and it could not have done anything else.** The brief required
   `cow_5d14a55f-2647-49fa-95d4-7b37a7463da5` to survive. On this platform **a coworld id is
   per version**: `GET /v2/coworlds` shows four cogball rows, one per version, each with its own
   id and its own manifest hash, created before this route-back as well as during it —

   | version | cow_id | canonical | created |
   |---|---|---|---|
   | 0.1.2 | `cow_23c9b804-8fb4-470d-ae86-bccf7a1aa5c3` | false | 05:17:06Z |
   | 0.1.3 | `cow_5d14a55f-2647-49fa-95d4-7b37a7463da5` | false | 05:29:19Z |
   | 0.1.4 | `cow_795268b0-3cff-476f-be68-e73a5ba19084` | false | 06:38:02Z |
   | **0.1.5** | **`cow_ff38b98b-f611-4a74-86e1-f2b23cbd6339`** | **true** | 07:16:54Z |

   So "same coworld, new version, same `cow_id`" is not an available outcome — any re-release
   at all would have produced a new id. The continuity that actually matters is preserved:
   same repo, same name `cogball`, same `game_15d64bb0-…`, same league, and the game's
   `canonical_coworld_id` now points at the new row automatically. **Every downstream artefact
   that names a cow_id (STATE, VERIFY.md, the announce copy) must be updated to
   `cow_ff38b98b-f611-4a74-86e1-f2b23cbd6339`.**

3. **No dispatch of my own.** 0.1.5 already satisfies every release exit criterion and its
   hosted bundle is proven to render (§4). Re-dispatching for the sake of authorship would have
   created a fifth coworld row, a v5 policy set, and a fresh canonical flip for zero gain.

4. **One defect in the brief, two in the code.** The brief described the fix as a one-liner;
   shipping only that (0.1.4) would have failed check 8 again with a *different*, more
   convincing-looking symptom (a full scorebug over a frozen board).

5. **The prior session's work was uncommunicated** (§0). `log.md` and `release-result.json` are
   brought up to date by this pass; `STATE.json` is the coordinator's file and is left alone —
   the values it needs are in §7.

---

## 7. Values the coordinator needs for STATE

```
coworld.version        0.1.5
coworld.cow_id         cow_ff38b98b-f611-4a74-86e1-f2b23cbd6339      (CHANGED)
coworld.manifest_sha   sha256:495905b153bc98135ae1ec127e8f4abc2b9c88cff6a6d1edf0934d161ec5dce7
coworld.release_run_id 32624985984
policies.champion1     cogball-total:v4      05f90027-a9af-4526-99df-20dda36c47cb
policies.champion2     cogball-counter:v4    49bdda05-ef1a-4153-83c8-ade64203a428  (daveey-1)
policies.fillers       cogball-formation:v4  b68050fd-6666-4759-88c1-c4c5ce13eb69
                       cogball-swarm:v4      2a7e3dbb-15e7-465d-af5e-02790d9468d5
```
The **league still fields the v2 versions** and per the brief was not to be touched; the v4 set
is available if a human later wants the league on the fixed image.

---

## 8. Files changed

**`Metta-AI/cogame-cogball`** (branch `main`, HEAD `ed783928319d3405edbaaaf30a5e7926729eaa5e`,
pushed 07:02Z by the prior session; nothing pushed by this pass):

| path | commits |
|---|---|
| `client/replay_broadcast.html` | `654fea6` (COG_BASE), `fb050fb` (pushFeed + GOAL LEAD on the board page) |
| `client/league_replayer.html` | `f3f60a7` (GOAL LEAD) |
| `tests/test_viewer.nim` | `46eedf4` |
| `tools/ci/viewer_shell_check.cjs` | `46eedf4` (new) |
| `tools/ci/viewer_smoke.mjs` | `ed78392` (new; template + `--soak`) |
| `.github/workflows/ci.yml` | `46eedf4`, `ed78392` |

**`Metta-AI/coworld-builder`** (this pass):

| path | what |
|---|---|
| `runs/2026-08-22-cogball/release-result.json` | overwritten with run 32624985984's artifact (0.1.5) |
| `runs/2026-08-22-cogball/rerelease-0.1.4.md` | this file |
| `runs/2026-08-22-cogball/viewer-check-0.1.5/` | `viewer-smoke.json`, `viewer-smoke.png`, `smoke-stdout.txt` from run 32630840631 |
| `runs/2026-08-22-cogball/log.md` | phase-60 lines + heartbeats |
