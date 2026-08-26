# r1 review — hidden-agenda

Repo: `Metta-AI/cogame-hidden-agenda` @ `5fb43682ed2008f52955b44c33a70b1769d4d5f0` (origin/main, confirmed by `git pull` → "Already up to date").
Range: `1171fab..5fb4368` (one substantive commit, 129 files, +17,681).
Design note: `/workspace/coworld-builder/runs/2026-08-25-hidden-agenda/design.md` (identical to `design-r1.md`).
Starter: `/workspace/starters/coworld-ctf`; `src/hidden_agenda/llm.nim` + `src/hidden_agenda_player.nim` forked from `/workspace/starters/cogame-bullwhip`.
Files read: 61 (all 16 `src/**.nim`, all 11 `tests/*.nim`, 4 `replay-viewer/*`, 5 `client/*`, 3 `tools/_page_*`, 8 `tools/*`, 3 workflows, manifest, compose, nimble, 2 Dockerfiles, 4 docs, `data/maps/vault.txt`).
Checklist: `prompts/30-review-loop.md` §ACCEPTANCE CHECKLIST.

Evidence gathered outside the tree: CI run **32919193615** on `main` at this sha (`gh run list -R Metta-AI/cogame-hidden-agenda --branch main -w ci.yml`) — conclusion `success`, jobs `test` ✓, `docker-smoke` ✓, `wasm-viewer` ✓; and the `smoke-replay` artifact (`replay.json`, 55,447 B, 343 frames), which I downloaded and re-derived from independently.

---

## Blocking

### B1 — the game container still serves a `/client/replay` page route

- Where: `src/hidden_agenda/server.nim:34`, `:287-289`, `:412`; advertised in `docs/PROTOCOL.md:47` and, via `tools/build_manifest.py:232,238`, inside `coworld_manifest_template.json`'s `game.protocols.player` and `.global` text values.
- Observed:
  ```nim
  ReplayPage = staticRead("../../client/replay_broadcast.html")   # :34
  proc replayPageHandler(request: Request) {.gcsafe.} =
    {.gcsafe.}: respondHtml(request, splicePage(ReplayPage))      # :287-289
  result.get("/client/replay", replayPageHandler)                 # :412
  ```
  The route is live in the game pod and serves the full broadcast page. `docs/PROTOCOL.md:47` lists it in the route table (`| GET /client/replay | the broadcast replay page |`), and that table is inlined verbatim into both manifest protocol documents.
- Checklist item: **3 — Static viewer**: "`coworld_manifest_template.json` declares `"replay_viewer": {"bundle": "static-replay-viewer"}`, `tools/build_replay_viewer.sh` exists and is wired as the `coworld build` hook, and the viewer contacts nothing but S3. **No `/client/replay` pod path anywhere.**" *(category: static-viewer)*
- Why blocking: the item's last sentence is unconditional and the path exists, is routed, and is documented on the platform-facing pages.
- Counter-evidence, stated plainly so the judge can weigh it: the other three clauses of item 3 are satisfied — the manifest declares only `{"bundle":"static-replay-viewer"}` (verified by parsing the file), `tools/build_replay_viewer.sh` is present and mode `100755` (`git ls-files -s` → `100755 a5eee7f`), and nothing in the bundle contacts a pod. The design note's own route table (design.md:985-992) omits `/client/replay` and design.md:36 says "no `/client/replay` live viewer is **declared**" — i.e. the note reads the rule as a manifest rule. The starter carries the identical route (`/workspace/starters/coworld-ctf/src/ctf/server.nim:73,631,646,844`), so this is inherited, not invented. If item 3 means "the manifest must not declare a pod viewer", this is satisfied and B1 should be dismissed.

### B2 — `client/replay_broadcast.html` inherits the starter's CSS and markup but **not** its script; the page is 47 % of the starter's size

- Where: `tools/build_page.py:12` (`css = src[0:704] + src[833:1451]`), `tools/build_page.py:24-43`; product `client/replay_broadcast.html` (2,180 lines) vs starter `client/replay_broadcast.html` (4,660 lines); the replacement script is `tools/_page_script.js` (704 lines) and the replacement markup `tools/_page_markup.html` (96 lines).
- Observed, step by step:
  1. `build_page.py` slices the starter's page at **line 1451**. The starter's `</style>` is at line 1460, `<body>` at 1462, body markup runs 1462–1604 and the page script runs 1605–4660. So the generator inherits **only the CSS head**, and discards the starter's 143-line body markup and its ~3,050-line page script.
  2. I reconstructed the generator's CSS slice from the starter and diffed it against the fork's first 1,128 lines. The only difference in the whole block is one line:
     ```
     -<title>Ctf — Broadcast Replay</title>
     +<title>Hidden Agenda — Broadcast Replay</title>
     ```
     So sections 1–5 (stage, scorebug, banner lane, kill feed, transport, scrubber + momentum + beat markers + lulls + spoilers, endcard, locker-room curtain) are **byte-identical** to the starter's, minus exactly the three removals the note lists (`#povBadge`+`#fpv*` at starter 528–704, `#viewpanel`/`#minimap`/`#zoom*` at starter 705–833, `#mmwarn` at the tail). That clause of item 14 **passes**.
  3. `tools/_page_markup.html` diffs against the starter's body 1462–1604 as a faithful port: the only changes are the four removed element families, the two re-lettered literals (`LIVES LEAD`→`RACE TO WIN`, and the plate labels), the locker-room caption, HTML-entity escaping of the glyphs, and the appended `#rosterstrip` / `#voteboard` / `#ec-roles`. That clause **passes** too.
  4. The **script** is new. The starter's page script declares 187 functions; `tools/_page_script.js` declares 30, re-implementing the starter's chrome plumbing under the starter's own names (`relayout`, `ensureScorebug`, `renderScorebug`, `buildFlag`, `pushFeed`, `feedRow`, `clearFeed`, `banner`, `pumpBanner`, `clearBanners`, `applyEvent`, `onFrame`, `onStatus`, `dismissLockerRoom`, `renderEndcard`, `send`). It aliases only 9 names out of `chrome_common.js` (`esc fmt teamCol setName teamName markBeat setVerdict AMBER RED show`) against the starter script's 18 `C.*` call sites.
- Checklist item: **14 — Chrome is the starter's, not a lookalike**: "`client/replay_broadcast.html` is the starter's page with a game block appended under a banner comment… **A page a fraction of the starter's size is a rewrite and is blocking.**" *(category: static-viewer)*
- Why blocking: 2,180 / 4,660 = 47 % of the starter's page, and the reason is that the entire script half was re-authored rather than inherited. That is the size test the item names. The design note is stronger still: design.md:1106-1112 says "Everything else — `#stage` … `#endcard` … and `#status` — is the starter's, **unchanged**", and design.md:1091 says the page is the starter's "with a game block APPENDED, never a rewrite that reuses its ids".
- Deviation-claim mismatch: deviation #10 is stated as "`replay_broadcast.html` generated by `tools/build_page.py` from the starter's page". The code shows `build_page.py` takes the starter's **CSS only** (`src[0:704] + src[833:1451]`); the markup is a hand-port and the script is new. The claim materially overstates what is inherited.
- Counter-evidence: the id-presence and provenance test (`tests/test_broadcast.nim:pageProvenance`, lines 154-197) checks all 41 inherited ids present, all 20 removed ids absent, the banner comment, `--band`/`--hudscale`/`--topband`, the re-lettered literals, `#lockerroom { pointer-events: none; }`, CSS for all six beat kinds, `button.beat-marker`, and `flex: 1 1 auto; min-width: 3.2em;` — and `tests/test_broadcast.nim:noScopeDuplication` (199-235) enforces the tandem alias rule. Item 14's transport rules all hold (traced below). The starter's *CSS* — which is where the item tells the reviewer to look — is verbatim.

### B3 — nothing asserts the per-tick re-derivation the design promises; the only test that claims to reads one frame

- Where: `tests/test_vision.nim:97-113`.
- Observed:
  ```nim
  block recordedMaskMatches:
    ## The recorded `v` bitmask equals a recomputed `visible()` for every cog on
    ## every tick of a full episode.
    …
    let sim = playEpisode(config, uniformKinds(skMiner))
    …
    ## Replay the episode once more and compare the mask at the terminal state.
    for slot in 0 ..< Seats:
      var expected = 0
      …
      check(sim.frames[^1].v[slot] == expected, …)
  ```
  The loop indexes `sim.frames[^1]` only. There is no per-tick comparison anywhere in `tests/`, and no test re-derives `c`, `d` or `g` from the recorded events either. `tests/test_broadcast.nim:replayPacketDrivesTheSameChrome` (128-152) does prove the viewer's packet comes from `parseReplay(replayBytes(game))` — the same bytes, not a parallel recording — but it asserts shape and seek behaviour, not frame-by-frame equality.
- Checklist item: **2 — Replay re-derivation**: "Replaying the recorded events through the sim reproduces the recorded per-tick state **frame by frame**, and the viewer derives its display from that same re-derivation — not from a parallel recording. **A test asserts it.**"
- Why blocking: the "a test asserts it" clause is unmet. The design note's own test list (design.md:1350-1351) promises the stronger form ("for every cog on every tick of a full episode") and the code's own docstring repeats it, so the gap is between the comment and the loop, not a design choice.
- Independent evidence that the property itself **holds** (so this is a test gap, not a behaviour bug): I re-implemented `los`, `quadrantOf` and `canSee` in Python from `src/hidden_agenda/station.nim:180-226,453-459` and `src/hidden_agenda/vision.nim:15-36`, and re-derived `v` for all 5 slots on all **343** frames of the CI smoke replay using only the replay's own `config.grid`, `visionRadius`, `awarenessRadius` and each frame's `c`: **0 mismatches**. I also re-derived `d` from the `deposit` events (0 mismatches over 343 frames) and `g` from the `mine` + `seam` events (0 mismatches).

---

## Non-blocking

Grouped: constants and rules (N1–N11), decision path (N12–N15), protocol and replay (N16–N21), packaging and docs (N22–N26), viewer and CI (N27–N32).

### N1 — `freezeCooldownTicks = 260` and `awarenessRadius = 4`; the note's repair ladder authorises 220→260 but only 2→3

- Where: `src/hidden_agenda/sim_config.nim:65` (`freezeCooldownTicks: 260`) and `:67` (`awarenessRadius: 4`); mirrored in all three manifest variants and in `config_schema.awarenessRadius.default = 4`.
- Note says: `freezeCooldownTicks = 220` (design.md:235) with ladder step (b) "220 → 260 if the impostor is too strong" (design.md:533) — **matches**; `awarenessRadius = 2` (design.md:173) with ladder step (e) "**`awarenessRadius` 2 → 3**" (design.md:537) — the code went to **4**, one step beyond what the ladder names. `hidden-agenda-blind` keeps `freezeCooldownTicks: 120` per the note's variant table.
- Consequence traced: with `awarenessRadius = 4` every cog sees every other cog within Chebyshev 4 regardless of facing, and `freezeRange` is 2, so any freeze is inside a 4-ring that reaches two cells further than the beam. At tick 0 of the CI replay `v = [6,9,17,2,4]` — RED at (13,7) already "sees" BLUE (9,7) and GREEN (17,7), both at Chebyshev exactly 4, neither in its N cone. The design's own argument for the cone (design.md:182-186 — "somebody behind you sees you and you do not see them… That is the risk the beam carries") is weakened proportionally. Empirically both CI freezes were witnessed, and gate (c) measured **1.62** mean witnessed freezes with impostor win rate **0.00** against a ≤ 0.35 ceiling.
- The gates hold at these values: CI run 32919193615 `test` job prints `PASS b: all-miner crew win rate 0.50 (8/16)`, `PASS c`, `PASS d: 1.00`, `PASS e: 16/26 (0.62)`, `PASS f/uniform: worst deviation 0.05`, `PASS f/slots: spread 0.06`, `PASS a: 16/16 decisive` on all three variants, `PASS g: worst 11–12 batches, 10–11 meetings`.

### N2 — spawn cells widened; the note's table and the note's own replay example are now wrong

- Where: `src/hidden_agenda/station.nim:66-68` — `[13,7], [9,7], [17,7], [9,11], [17,11]`, with a comment naming the tick-one-freeze failure.
- Note says: `(13,7) (11,7) (15,7) (11,11) (15,11)` (design.md:74-78), and design.md:938 pins the same list into the replay's `config.spawns`. The CI replay's `config.spawns` is `[[13,7],[9,7],[17,7],[9,11],[17,11]]`.
- Verified: all five new cells are `.` on rows 7 and 11 of `data/maps/vault.txt`, distinct, and inside the `HUB` rectangle; `spawnFacing` still faces each away from (13,9). The deviation claim matches the code. The note's original pair (11,7)/(13,7) is Chebyshev 2 = `freezeRange`, so the stated reason checks out.

### N3 — move resolution is a multi-pass with position tie-breaks and cell swaps, not slot order

- Where: `src/hidden_agenda/sim.nim:326-411`; `src/hidden_agenda/station.nim:288-332` (`stepToward` with an occupancy array).
- Observed: `while progress:` re-runs the slot sweep until nothing more can move (`:357-392`); a contested free cell goes to the cog standing at the smaller `(row, col)` (`:378-389`), not the lower slot; a separate pass (`:394-406`) lets two cogs **swap** cells when each targets the other's cell. `stepToward` additionally prefers a *free* equally-optimal neighbour and will side-step around a parked cog (`station.nim:307-320`).
- Note says: step 7 is "Moves resolve, **slot order**, against the live board: a move into a cell a lower-numbered seat has already taken this tick fails and degrades to `wait`" (design.md:417), and `move_*` is legal "only into a floor or grate cell **not occupied by another active cog**" (design.md:346). A swap moves into an occupied cell. The note also claims "Paths are unique and deterministic" (design.md:357); with occupancy-aware stepping the realised step now depends on where other cogs stand — still deterministic, no longer a pure function of the map.
- `tests/test_sim.nim:occupancy` (lines 190-204) asserts only "two active cogs never share a cell"; its own comment says "the lower slot wins" but nothing asserts that, and the design's test-3 list (design.md:1361) names it. Deviation #3 matches the code.

### N4 — meeting seats are assigned by `(row, col)`, not slot order

- Where: `src/hidden_agenda/meeting.nim:83-103`.
- Note says: "assigned in **slot order** among the active seats" (design.md:283). Deviation #6 matches the code. `openMeeting` correctly chooses every seat before moving anybody (`sim.nim:475-478`), so the assignment is not order-dependent within the tick.

### N5 — `mostStaleActive` returns −1 with nothing seen, and both baseline tie-breaks are rotation-based, not alias order

- Where: `src/hidden_agenda/scripted.nim:39-58` (`mostStaleActive`), `:32-37` (`rotation`), `:141-161` (`suspects`).
- Note says: miner crew plan step 3 is "`{"job":"watch","who":X}` where `X` is the active cog with the **largest** `t - lastSeen[X].t`, **ties by alias order**" (design.md:800-801) and the vote is "ties by alias order" (design.md:805). The code (a) returns −1 when nothing has been seen, so no `watch` step is emitted at all (deviation #5, matches), and (b) breaks ties first on raw staleness and then on `rotation(slot, other)` — the seat's own slot outward — never alias order. (b) is not in the ten declared deviations.
- Empirical: the CI replay's opening `order` rows carry two-step plans (`mine S2, deposit`) with no `watch`; the meeting-1 rows carry three (`mine S2, deposit, watch BLUE`).

### N6 — the `miner` impostor's bandwagon vote can never fire: it reads the *current* meeting record, which is always empty

- Where: `src/hidden_agenda/scripted.nim:95-114` (`lastMeetingCounts` / `rankedByVotes`) against `src/hidden_agenda/sim.nim:496-497` and `:691-697`.
- Observed, traced: `openMeeting` appends the **current** meeting's `MeetingRecord` (`sim.nim:496`) with `votes` defaulted to five empty strings, and `runEpisode` calls `runDecisionPoint` immediately afterwards (`sim.nim:692-697`). `lastMeetingCounts` then reads `sim.meetings[^1].votes` — the record just created — so the table is always empty, `rankedByVotes` always returns `@[]`, and `minerDecision`'s impostor branch always falls through to `mostStaleActive` (`scripted.nim:217-224`) with `switchTo` fixed at `"skip"` (`ranked.len > 1` is never true).
- Note says: "*As impostor:* … `vote`: bandwagon — the active cog (other than itself) with the most votes in the **previous** meeting… `switch`: `{"if": <own alias>, "to": <the cog with the second-most votes last meeting, else "skip">}`" (design.md:818-820). The previous meeting is `sim.meetings[^2]` at a decision point.
- Not a legality violation (the fallback path is inside every enum), so `tests/test_baseline.nim` stays green; it is a behaviour the note specifies and the code does not produce.

### N7 — seams start at a seeded regrow phase

- Where: `src/hidden_agenda/sim_state.nim:152-155` — `regrow: result.rngWorld.rand(config.seamRegrowTicks)`.
- Note says: "6 seams, `seamCapacity = 3` gems each (18 standing at tick 0), regrowing **+1 gem every `seamRegrowTicks = 120` ticks**" (design.md:202-204) — no phase. All six still stand full at tick 0 (CI replay frame 0: `g = [3,3,3,3,3,3]`), and the draw is from `rngWorld`, so `worldHash` stays role-independent (`tests/test_noleak.nim:roleComesFromItsOwnSubStream`). Deviation #7 matches. `tests/test_sim.nim:seamsRegrowAndCap` pins `regrow = 0` before measuring, and says so.

### N8 — feasibility gate (e) is measured against a `lurker` impostor, not gate (a)'s all-`miner` episodes

- Where: `tests/test_feasibility.nim:145-171`.
- Observed: `playAll(seed, "hidden-agenda-notalk", skMiner, skLurker, …)`, then one case per `caught` event, convicted iff the first `eject` row at `t >= caughtAt` carries `wasImpostor`.
- Note says: "Over **the episodes in (a)** that contain ≥ 1 witnessed freeze, the meeting immediately following ejects the impostor in ≥ 0.60 of cases **with `miner` crew**" (design.md:524-526) — and the episodes in (a) are all-`miner`, i.e. a `miner` impostor. The per-`caught` counting is deviation #9 and is declared; the change of impostor baseline is not. It is a materially easier population — the `lurker` `strike`s the instant the beam is legal, which is what makes it catchable. Measured: `PASS e: 16/26 witnessed freezes convicted (0.62)`, a 0.02 margin over the 0.60 floor.

### N9 — gate (f)'s uniformity half runs over 4,096 seeds, the win-rate half over 64

- Where: `tests/test_feasibility.nim:41` (`DrawSeeds = 4096`), `:180-196`.
- Note says: "Over seeds 1..64 the drawn impostor slot is within ±20 % of uniform, and the crew-win rate with the impostor pinned to each of the five slots in turn varies by ≤ 10 %" (design.md:527-528). The code splits the two halves (4,096 for the draw, 64 for the win rates) and documents the statistical reason in a comment. Deviation #8 matches. Both halves pass.

### N10 — `lurk` completes on sighting **any** active cog, not "a lone crewmate"

- Where: `src/hidden_agenda/kernel.nim:94-106`.
- Note says: "`lurk room:<room>` — BFS to the room's far corner from the doorway, then `wait` facing the doorway. **Waits for a lone crewmate to walk in.**" (design.md:384-385). The note never defines a completion condition for `lurk`, so adding one is deviation #4 (declared and matching); the code's condition ignores "lone" — two crew walking in together also complete the step and hand over to the next (normally `hunt`).

### N11 — `watch` refuses to stand on a chokepoint; not in the ten declared deviations

- Where: `src/hidden_agenda/kernel.nim:29-40` with `src/hidden_agenda/station.nim:380-384` (`isChokepoint` = `walkableNeighbours(x,y) <= 2`).
- Note says: "`watch who:<alias>` — BFS to the nearest walkable cell whose distance to that cog's **last known cell** is in `3..5`" (design.md:367). The code filters that ring down to non-chokepoint cells first, falling back to the full ring only if the filtered set is empty. Same family as the anti-gridlock deviation (#3) but not covered by its wording.

### N12 — `parseReply` rejects a `who` that names the seat itself; the note's schema does not

- Where: `src/hidden_agenda/llm.nim:562-567` — `if not sim.isActiveAlias(step.who) or step.who == Aliases[slot]: raise`.
- Note says: "`plan[].who` | string enum | **an alias that is `active` now** | required for `watch`, `hunt`, `strike`; missing, unknown or not active → **invalid reply**" (design.md:691). Self is active, so under the note's table `{"job":"watch","who":"<yourself>"}` is legal and here it costs the seat a retry and then a scripted fallback. `tests/test_baseline.nim:52-54` asserts the same extra rule for the baselines.

### N13 — a 429 is retried inside the same decision point, not "at the next decision point"

- Where: `src/hidden_agenda/llm.nim:652-655` (`textOf` raises on 429) feeding `decideAll`'s `for attempt in 0 .. 1` loop (`:694-723`).
- Note says: two things that pull apart — "On transport error, **non-2xx**, refusal… that seat alone is retried **once** in the same decision point's retry batch" (design.md:837-839) and "**429 is logged and the seat is retried at the next decision point**" (design.md:845-846). The code implements the first. 401/403 does set `client.disabled = true` (`llm.nim:649`) and every later seat then goes scripted (`:689-691`), which matches design.md:845.

### N14 — no test drives `decideAll`'s transport or retry path; `dsRetry` is never produced in any test

- Where: `tests/test_llm.nim:151-231`. Every driver block constructs `disabledLlmClient()` (`llm.nim:51-56`), which short-circuits at `llm.nim:689-691` and yields `dsFallback` without ever entering the batch loop. There is no stub for `textOf`, no simulated timeout/429/403/junk response, and no assertion that a first-attempt failure produces a second batch or a `source: "retry"` row.
- Note says: test 9 must cover "a stubbed transport that times out, 429s, 403s or returns junk produces `miner` decisions for those seats, never raises, and marks `source: "fallback"`" (design.md:1410-1411). Checklist item 8's "retries **once**… then falls back… and the fallback is recorded" is met *in the code* (`llm.nim:694-728`, source set at `:716` and `:728`, `order.source` written at `sim.nim:657`), and the no-credentials fallback is asserted, but the retry half is untested.

### N15 — `parseReply` is the only cap on recorded text; a `Decision` built elsewhere is uncapped

- Where: `src/hidden_agenda/llm.nim:605-608` (the only `oneLine`/`cleanText` on `say`/`hunch`/`notes`), against `src/hidden_agenda/sim.nim:622-643` (`applyDecision` stores them verbatim) and `src/hidden_agenda/events.nim:69-70,81-90`.
- Observed: `tests/test_replay.nim:runeTruncation` (114-160) feeds `cleanText(runic(200), MaxSayLen)` — i.e. it truncates before handing the decision in — so the recording path is exercised but the truncation is the test's own. The genuinely-unguarded input test is `tests/test_llm.nim:capsAreRuneSafe` (121-138), which feeds 300/300/400 raw multi-byte runes through `parseReply` and asserts `runeLen <= cap` and `validateUtf8 == -1`, plus `tests/test_replay.nim:cleanTextIsRuneSafe` (162-167). Checklist item 9's "a test feeds multi-byte input at the cap and asserts the output is valid UTF-8" is therefore satisfied; the note's phrasing of test 8 is not.
- Related: `MaxPolicyLen* = 64` is declared at `src/hidden_agenda/sim_types.nim:41` and referenced **nowhere** (grep over `src/` and `tests/`). Policy names arrive from `config.players[].name` (`sim_state.nim:141-145`) and reach the replay's `policyNames[]`, `results.names[]`, the `reveal` event's `policy` field and `roster[].pol` with no `cleanText` and no cap. `config.variant` reaches `replayConfigJson` (`sim_config.nim:226`) the same way. The note's "the same rune-safe truncation applies to **every** string that reaches the replay" (design.md:702) is not applied to those two.

### N16 — the `final` frame carries no `slot`

- Where: `src/hidden_agenda/server.nim:122-135` builds one payload and broadcasts it to every socket (`:137-149`).
- Note says: `{"type":"final","done":true,"slot":N,"scores":…}` (design.md:1001). `tests/test_noleak.nim:noRolesInWelcomeOrFinal` (79-105) mirrors the server's actual shape (also without `slot`), so the test does not catch the divergence — and note that the test reconstructs both frames locally rather than calling `server.welcomeFrame`/`finalFrame`, so a future server change would not be caught either.

### N17 — a frozen/ejected seat's `state` frame carries no `canAct` / `canVote`

- Where: `src/hidden_agenda/llm.nim:251-296` (`seatView` emits no such keys); `src/hidden_agenda/server.nim:113-120` sends `seatView` to every connected socket regardless of state.
- Note says: "**Frozen or ejected seat:** receives a `state` frame with `you.state = "frozen"|"ejected"`, **`canAct: false`, `canVote: false`**" (design.md:671-672). `docs/POLICIES.md:81` and the manifest's `policies.md` page repeat the promise: "A **frozen or ejected** seat receives a frame with `canAct: false`". `you.state` *is* present (`llm.nim:181`), the seat *is* excluded from every batch (`sim.nim:660`, `sim_state.nim:198-201`), and the socket does stay open — only the two flags are missing.

### N18 — the replay frame carries no freeze cooldown and no meeting countdown, so the viewer draws `cool = 0` and "RESOLVED"

- Where: frame encoding `src/hidden_agenda/sim.nim:49-64` (six ints per cog: `x, y, facing, state, carry, mineProgress`); `src/hidden_agenda/global.nim:247` (`result.freezeCooldown = 0`) and `:251` (`result.meetingIn = 0`) in `replayChrome`; consumed at `tools/_page_script.js:pipBar` (`on = round((1 - value/total) * count)` → all pips lit when `value` is 0) and `renderVoteBoard` (`meeting['in'] > 0 ? 'RESOLVES IN ' + … : 'RESOLVED'`).
- Note says: the impostor plate's subline is "the alias + policy of the impostor and **a freeze-cooldown pip bar**" (design.md:1155) and the vote board carries "a countdown **`RESOLVES IN 5`**" (design.md:1162); the `agenda` block example carries `"cool":180` and `"in":5` (design.md:1190-1192). Both are correct on the **live** `/global` path (`global.nim:148`, `:152-156`) and dead on the static-bundle path, which is the one the platform serves.
- Both quantities are *derivable* from the recorded bytes (`freeze` event ticks + `config.freezeCooldownTicks`; `meeting` event tick + `config.resolveTick`), so this is a viewer-derivation gap, not a replay self-sufficiency gap.

### N19 — the frame's meeting-phase key is `ph`, not the note's documented `m`

- Where: `src/hidden_agenda/replays.nim:32-33` writes `{"t","c","v","g","d","ph"}`; `src/hidden_agenda/global.nim:80-81` matches.
- Note says: the encoding bullet defines "`d` = deposits; `m` = meeting phase" (design.md:971-972) while its own example frame prints `"d":0,"m":0,"ph":0` (design.md:950) — the note is internally inconsistent. The code emits `ph` only. `docs/PROTOCOL.md:71` documents `b.ph` correctly. No consumer reads `m`.

### N20 — `results.ticks` is the frame count (last tick + 1); the `end` event's `t` is the last tick

- Where: `src/hidden_agenda/sim.nim:741` (`"ticks": sim.frames.len`) vs `:718` (`sim.log.ended(sim.tick, …)`). CI replay: `end.t = 342`, `results.ticks = 343`, `frames.len = 343`.
- Note says: "`ticks` = ticks played" (design.md:1053). `tests/test_replay.nim:47-50` asserts `frames.len == results.ticks`, so the two are pinned to each other; the off-by-one against "ticks played" is only a naming question. `finalFrame` (`server.nim:133`) uses the same `frames.len`.

### N21 — the recorded LLM error text and the echoed `PLAYER_PROMPT` never reach the replay

- Where: `src/hidden_agenda/llm.nim:720-721` echoes `cleanText(error.msg, MaxErrorLen)` to stdout only; `src/hidden_agenda/server.nim:371-373` caps the prompt rune-safely at 4,000 and stores it in `shared.prompts`, which is read only by `userPrompt`.
- Note says: "The same rune-safe truncation applies to **every** string that reaches the replay, including the recorded LLM error text (capped at 200 characters) and the echoed `PLAYER_PROMPT` (capped at 4000)" (design.md:702-704). Neither string is in the note's own `order` event field list (design.md:912), so nothing in the event vocabulary could carry them. Both caps are applied where the strings do exist, rune-safely. Reported as a note-vs-note inconsistency, not a code fault.

### N22 — the certification fixture's seed is 5, not the note's 11, and the episode it produces is 343 ticks, not 900

- Where: `coworld_manifest_template.json` → `certification.game_config.seed = 5`; note says `seed: 11` (design.md:1308).
- The note's timing argument — "**900 ticks = 37.5 s of video at 24 fps**, which comfortably outlasts the 10 s viewer soak" (design.md:1316-1317) — does not describe the real fixture. The CI replay ends at tick 342 (`ending: "impostor_ejected"`), i.e. **14.3 s** of video against a 10 s soak. The margin is 4.3 s, not 27.5 s. `tests/test_manifest.nim:theCertificationEpisodeActuallyPlays` (226-256) enforces the real property (`seconds > 12.0`) rather than the note's arithmetic, and passes, and the CI soak line reads `soak: 10s of playback kept advancing ("2 / 342" -> "194 / 342" -> "242 / 342")`.
- The fixture does deliver the headline chrome: 2 freezes, 2 witnessed, 2 `caught` rows, 3 meetings, 1 correct ejection. `fakeDeposits: 0`, so the `fakedeposit` feed row (`tools/_page_script.js:applyEvent case 'fakedeposit'`) is exercised by no CI replay.

### N23 — the shipped docs and the manifest's doc pages contradict the shipped code in six places

`tools/build_manifest.py:223-238` inlines `README.md`, `docs/RULES.md`, `docs/POLICIES.md` and `docs/PROTOCOL.md` into `game.docs` and `game.protocols`, so every item below is on the platform-facing page as well as in the repo:

| where | doc says | code does |
|---|---|---|
| `docs/RULES.md:10-12` (and manifest `rules.md`) | spawns `(11,7) (15,7) (11,11) (15,11)` | `station.nim:66-68` → `(9,7) (17,7) (9,11) (17,11)` |
| `docs/RULES.md:89`, `docs/POLICIES.md:59`, `README.md:22` | `awarenessRadius = 2` | `sim_config.nim:67` → `4` (and `config_schema` default `4`) |
| `docs/RULES.md:128` | `freezeCooldownTicks = 220` | `sim_config.nim:65` → `260` |
| `docs/RULES.md:150` | meeting seats "assigned in slot order" | `meeting.nim:83-103` → by `(row, col)` |
| `docs/RULES.md:226` | "a move into a cell a lower-numbered seat already took this tick degrades to `wait`" | `sim.nim:357-406` → multi-pass, `(row,col)` tie-break, swaps |
| `docs/POLICIES.md:81` | frozen seat's frame has `canAct: false` | `llm.nim:251-296` emits no such key |

Checklist item 10 constrains `game.docs`'s **shape** and `game.protocols`'s presence, both of which hold (verified by parsing: `docs.readme` is `{type:text,value}` 5,447 chars; two pages `rules.md` 11,611 / `policies.md` 6,669, both `{type:text,value}`; `protocols.player` 6,636 and `.global` 6,867, both `{type:text,value}`). Content accuracy is not a named item, hence non-blocking.

### N24 — `test_manifest.nim` does not run coworld's own `_load_template_manifest`

- Where: `tests/test_manifest.nim` — the file parses the JSON with Nim's `std/json` and asserts contract properties; there is no invocation of the installed `coworld` package.
- Note says test 10 must include "the installed coworld's own `_load_template_manifest` accepts the file (collab-cooking, 2026-08-25)" (design.md:1421-1422). Everything else in the note's test-10 list is asserted, including the `{{HIDDEN_AGENDA_IMAGE}}` derivation from `compose.yaml`'s service name (23-45), the secret-namespace equality (47-57), `num_agents` in all three variants + the fixture (59-77), every declared `player[]` id seated (79-93), the bundle declaration (95-107), docs/protocols (109-133), schema bounds (135-153), results-schema arrays (155-176), and the cert timing arithmetic (178-201).

### N25 — several design test-3 / test-4 sub-claims are stated in the note but not asserted

Traced against `tests/test_sim.nim` and `tests/test_meeting.nim`:

- "mining… resets on move/freeze/**meeting**" (design.md:1352-1353): the reset code exists (`sim.nim:295-296`, `:351-352`, `:465-466`) but only the post-gem reset is asserted (`test_sim.nim:56`).
- "the freeze is refused… **during a meeting**" (design.md:1356): `playTick` is simply not called while `inMeeting` (`sim.nim:701-704`); no test drives it.
- "an impostor deposit… emits `fakedeposit` **with the correct `seenBy`**" (design.md:1354): `test_sim.nim:100` asserts `fakes[0]{"seenBy"}.len >= 0`, which is vacuous.
- "the witness set is computed from **start-of-tick** positions and facings" (design.md:1358): implemented at `sim.nim:183-189, 230-231`; not isolated by a test.
- "determinism… twice in one process **and across a fresh server**" (design.md:1363-1364): only the in-process half is asserted (`test_sim.nim:229-252`).
- "the switch snapshot is taken at `switchTick − 1`" (design.md:1368): implemented at `sim.nim:573-574`; the test asserts the "same snapshot for all conditionals" consequence, not the tick.

### N26 — the `miner` crew's second plan step re-runs the same seam chooser, not "the next-best seam"

- Where: `src/hidden_agenda/scripted.nim:172-175` — both branches call `bestSeam(sim, cog, -1)`; the `skip` parameter that would exclude the first choice is never used with a real index.
- Note says: "Plan step 2: `{"job":"deposit"}` (or, if step 1 was already `deposit`, `{"job":"mine","at":S}` for the **next-best** seam)" (design.md:798-799).

### N27 — the bundle's viewer smoke reports `canvas_text: 0 drawn`, which the checklist says is not evidence

- Where: CI run 32919193615, `wasm-viewer` job, step "Load the bundle in a real browser":
  ```
  {"loaded":true,"ms":329,"clock":"TICK 242 / 900 MEETING 2 — VOTING", …}
  canvas text: 0 drawn, 0 never inside the canvas (0 draws crossed an edge), 0 ellipsized (--strict-text-bounds)
  ```
  The cause is structural: the bundle renders on an **OffscreenCanvas inside a Worker** (`replay-viewer/static_replay.js:81-85` transfers the canvas; `replay-viewer/static_replay_worker.js:232` `importScripts('./broadcast_core.js')`), so `viewer_smoke.mjs`'s context patch cannot see the draws.
- Checklist item 15 anticipates exactly this ("`total: 0` means the check covered nothing (a worker/OffscreenCanvas or WebGL renderer) and is not evidence of anything") and names the mitigation, which is present and green: the second step, "Load the worst-case renderer fixture in a real browser", reports `canvas text: 144 drawn, 0 never inside the canvas (66 draws crossed an edge), 0 ellipsized (--strict-text-bounds)`. The fixed-arena requirement (`never_inside == 0`) is therefore met on the only measurement that covers anything, and `--strict-text-bounds` is carried on both steps (`.github/workflows/ci.yml:323` and `:344`). Reported so the judge is not told `0/0/0` is a pass on its own.

### N28 — the renderer fixture's LLM-text half uses its own markup and CSS, and its overflow count is computed but never asserted

- Where: `tools/ci/renderer_fixture.html:211-244`.
- Observed: the full-cap `SAY` (90), `HUNCH` (80) and `NOTES` (240) are injected as `<div class="feed-row">` / `.banner-chip` / `.vrow` elements built by the fixture itself, styled by the fixture's own `<style>` block (`:39-45`, `overflow:hidden; text-overflow:ellipsis; white-space:nowrap`). They do **not** go through the shipped `feedRow`/`banner`/`renderVoteBoard` builders in `tools/_page_script.js` nor the shipped rules in `client/replay_broadcast.html` (`.feed-row { max-width: none; white-space: nowrap; }` at line ~1073, `#killfeed { width: calc(228 * var(--u)); }`). `overflowing` is counted at `:229-233` and only printed at `:240-244`; nothing fails on it.
- Every literal clause of item 15's fixture requirement is met: it loads the real `client/broadcast_core.js` and `client/chrome_common.js` (`:52-53`), renders at four canvas sizes including 360 px (`:186`), sets `data-replay-loaded` on the last line and `data-replay-error` on any self-check failure (`:64-68`, `:245`), asserts its own strings are still full-length (`:82-88`), and is driven by `--strict-text-bounds` in its own `ci.yml` step. Hence non-blocking.
- Mitigating fact I verified: `client/broadcast_core.js` draws exactly three kinds of canvas text — the deposit counter (`:254`), seam ids (`:271`, `:290`) and cog alias labels (`:419-422`, boxed with `measureText`) — and **no** LLM-authored text. There are no speech bubbles in this game; `say`/`hunch`/`notes` reach only the DOM feed. So the untested surface is the DOM chrome, not the canvas.

### N29 — `#stage.tiny` switches at `boardW <= 620`, while the note says sublines hide "under 640 px"

- Where: `tools/_page_script.js:relayout` → `stage.classList.toggle('tiny', boardW <= 620)`; `tools/_page_css.css:232-234` hangs the subline/label hiding off `#stage.tiny`.
- Note says both numbers itself: "`#stage.tiny` (already switched on at `boardW <= 620`)… and hide plate sublines **under 640 px**" (design.md:1195-1197). Checklist item 11's two hard requirements are met: `.plate-name { flex: 1 1 auto; min-width: 3.2em; }` is present at `tools/_page_css.css:27-31` and asserted at `tests/test_broadcast.nim:196-197`, and the labels are hidden under the `tiny` threshold. The 620/640 gap affects a 20 px band.

### N30 — the player container ships a built-in `DefaultPrompt`, so an env-less seat becomes an LLM seat

- Where: `src/hidden_agenda_player.nim:26-39` and `:50-53` — with neither `PLAYER_PROMPT` nor `PLAYER_SCRIPTED` set, the process sends a 12-line default strategy prompt.
- The server's rule (`server.nim:379-380`) demotes a seat to `miner` only when the prompt is empty *and* no baseline was named, so a default-prompt seat is treated as an LLM seat. Not in the note (design.md:1004 describes `{"type":"prompt","prompt":…,"scripted":…}` with no default). Harmless in CI (both fillers set `PLAYER_SCRIPTED`) and offline (no credentials → `client.disabled` → scripted).

### N31 — the `deposit` feed row fires every 4 deposits; the `deposit` **beat** fires every 8

- Where: `tools/_page_script.js:applyEvent` `case 'deposit'` → `if (e.total % 4 === 0)`; `src/hidden_agenda/sim.nim:274-275` → `if sim.deposits mod 8 == 0: addBeat(… "deposit" …)`.
- Note says "deposit milestones (`DEPOSITS 24 / 32`)" for the feed (design.md:1172) and shows `{"t":400,"k":"deposit","n":8}` for the beats (design.md:955) without pinning either period. Cosmetic; recorded because the two surfaces disagree.

### N32 — the renderer-fixture step's evidence is written to `dist/fixture` and is not uploaded

- Where: `.github/workflows/ci.yml:340-345` passes `--out dist/fixture`; the upload step at `:347-357` collects `viewer-smoke.png` / `viewer-smoke.json` from the repo root, which is where only the **first** smoke step writes (CI log: `artifacts: …/dist/fixture/viewer-smoke.png`). The fixture's `canvas_text` line survives in the job log but its screenshot and JSON are not in the `viewer-smoke` artifact.

---

## Traced and consistent

**Resolution rules — the twelve-step tick order** (`src/hidden_agenda/sim.nim:182-447`, one step per note paragraph at design.md:402-435):

- `src/hidden_agenda/sim.nim:183-189` — the start-of-tick snapshot of `x/y/facing` is taken before step 1, so the witness check at step 4 provably reads start-of-tick state.
- `sim.nim:147-160` (step 1) — move and freeze cooldowns decrement, then seam regrow counters advance and emit `seam` on reaching `seamRegrowTicks`, capped at `seamCapacity`. Verified against the CI replay: 3 `seam` rows in 343 ticks; re-deriving `g` from `mine` + `seam` events over all 343 frames gives 0 mismatches.
- `sim.nim:194-203` (step 2) — a move intent from a cog still on cooldown degrades to `aWait` exactly as design.md:406-407 says; frozen/ejected cogs get `aWait` and are never planned.
- `sim.nim:205-225` (step 3) — at most one freeze per tick, impostor only, gated by `freezeLegal` (`kernel.nim:131-144`), which checks all five conditions the note pins (design.md:230-233): impostor active, `freezeCooldown == 0`, target an **active crew** cog, `chebyshev ≤ freezeRange`, `los` clear. Victim's `carry` is zeroed (design.md:235). `tests/test_sim.nim:freezeLegality` (105-127) covers out-of-range, cooldown, frozen target, self-target, crew-as-freezer and a seam blocking the beam.
- `sim.nim:227-260` (step 4) — the witness set is computed from the snapshot arrays (`witnessSet`, `:162-180`); one `witness` row per witness with both `sawFreezer` and `sawVictim` flags; `caught` emitted iff `W` is non-empty; `meetingArmed = true; meetingCause = mcWitness`. Confirmed in the CI replay: freeze at t=8 with witnesses `["BLUE","YELLOW"]` → two `witness` rows + one `caught` → `meeting` at **t=9**, `cause: "witness"`; and freeze at t=318 → `meeting` at t=319. "Immediately means immediately, no cadence check" holds — `sim.nim:441-442` skips the cadence decrement entirely when armed, and `tests/test_sim.nim:154-155` asserts the timer is untouched.
- `sim.nim:262-288` (step 5) — crew deposit moves the counter by exactly one per tick; impostor deposit destroys the gem, leaves the counter, emits `fakedeposit` with `seenBy` computed by the same `canSee` predicate, and increments each observer's `sawFake` audit counter (the note's deposit-audit channel, design.md:220-223).
- `sim.nim:290-313` (step 6) — `mineProgress` advances one per tick, resets on a seam change, and transfers a gem at exactly `mineTicks`; refuses when the seam is empty or hands are full. `tests/test_sim.nim:44-70` pins both.
- `sim.nim:412-431` (step 8) — `face_*` overrides, otherwise the kernel's `setFacing`; `guard` sweeps via `kernel.guardFacing` (`Facing((sweep div sweepTicks) mod 4)` → N→E→S→W, clockwise, `sweepTicks = 8`).
- `sim.nim:433-434` (step 9) — `updateMemory` (`:77-104`) writes `lastSeen`, `togetherTicks`, `bodies` (dedup by alias, `noteBody` at `:70-75`) and `seamsSeen`, all gated on `seesCog`.
- `sim.nim:131-141` (step 10) — the win check runs in the note's exact order: deposits ≥ target → `crew_deposits`; impostor ejected → `impostor_ejected`; active crew ≤ 1 → `impostor_isolation`; `tick >= maxTicks` → `timeout`. All four endings and all three reasons match design.md:473-483 and the `results_schema` enums.
- `sim.nim:439-447` (step 11) — armed → nothing further; else decrement the cadence and arm at 0, and `runEpisode` opens at `t+1` (`:690-692`). Verified: meeting 1 closed at t=34, cadence reset to 200, meeting 2 opened at **t=234**.
- `sim.nim:705` (step 12) — one `recordFrame` per tick plus one at `t = 0` (`:684`). CI replay: 343 frames for a game ending at tick 342.

**The M1–M6 meeting machine** (`src/hidden_agenda/sim.nim:453-602`, `src/hidden_agenda/meeting.nim`):

- M1 `openMeeting` (`sim.nim:453-497`) — clears votes/switches/says/snapshot, saves `x/y/facing` for active cogs only, teleports (frozen cogs stay), faces the grate centre, emits `meeting {t,n,cause,active[],frozen[],ejected[]}`, adds a `meeting` beat, appends the record. Seats are all chosen before any cog moves (`:475-478`).
- M2 `say` (`sim.nim:554-562`) — gated on `config.chat and config.sayTick >= 1`, so a no-talk variant records nothing. `tests/test_meeting.nim:113-116` asserts five `say` rows in the chat shape and zero in the no-talk shape; `tests/test_noleak.nim:noSayInANoTalkEpisode` (107-127) plants `SECRET-SIDE-CHANNEL` in every decision and asserts it appears neither in the replay bytes nor in any seat's frame.
- M3 `revealTick` (`sim.nim:563-572`) — active seats with no vote default to `"skip"`; every active seat emits `vote … phase:"initial"`. `tests/test_meeting.nim:aFailedReplyCastsSkip` (203-215).
- M4 `switchTick` (`sim.nim:573-598`) — `voteSnapshot` captured at `switchTick - 1`, one `snapshotTally` taken at `switchTick`, all conditionals evaluated against it, all changes applied simultaneously into `updated`, and only genuinely-changed seats emit `vote … phase:"switch"`. `conditionHolds` (`meeting.nim:51-59`) implements "unique strict leader" for an alias and "no strict leader (all-skip included)" for `"tie"`, matching design.md:305-311 exactly. Tested at `test_meeting.nim:151-176` (two conditionals fire against one snapshot) and `:178-185` (a no-op switch emits no row).
- M5 `resolveTick` (`sim.nim:522-549`) — `resolveTally` (`meeting.nim:61-70`) is the note's rule verbatim: `m > s` + unique → `plurality`; `m > s` + tie → `tie`; `s >= m` → `skip`. Frozen and ejected seats cast nothing (`tallyOf`, `meeting.nim:21-32`). The `eject` row carries `target` (alias or `null`), the sorted `tally` with a `skip` count, `outcome` and the spectator-side `wasImpostor`. `winCheck` runs immediately afterwards. All four outcomes tested (`test_meeting.nim:19-46`, `:187-201`).
- M6 `closeMeeting` (`sim.nim:499-508`) — positions and facings restored exactly, `cadence = meetingCadenceTicks`. `tests/test_meeting.nim:120-149` asserts exact restoration and the cadence reset. Meeting occupies `m0 .. m0+meetingTicks-1`; `sim.nim:698-700` closes at `m0+meetingTicks` and that tick is a play tick.
- Both shapes' offsets fire where the note's table (design.md:289-296) says, asserted for `hidden-agenda` (10/24/46/56/60) and `hidden-agenda-notalk` (−1/5/18/23/25) at `test_meeting.nim:85-118`. `sim_config.validate` (`:121-129`) enforces `1 <= revealTick < switchTick < resolveTick < meetingTicks` and `1 <= sayTick < revealTick` when `chat`.
- Empirically in the CI replay: meeting 1 opened t=9, resolved t=32 (= 9+23); meeting 2 opened t=234, resolved 257; meeting 3 opened t=319, resolved 342.

**Vision and the witness predicate** — `vision.canSee` (`vision.nim:15-36`) is logically identical to the note's two-clause definition (design.md:171-177): `cheb ≤ awarenessRadius` **or** (`cheb ≤ visionRadius` **and** in the facing quadrant), both gated by `los`. `quadrantOf` (`station.nim:453-459`) is the note's wedge algebra character-for-character. `los` canonicalises its endpoints by `(y,x)` before walking, so symmetry-on-cells is structural, not hoped-for (`station.nim:187-226`), and `tests/test_vision.nim:losIsSymmetric` sweeps >1,000 walkable pairs. `seesCog` (`vision.nim:42-51`) refuses self, refuses a non-active observer, and keeps a frozen cog visible while an ejected one is not — the note's "frozen bodies are the evidence" rule (design.md:179-180). Non-symmetry is pinned by an explicit case at `test_vision.nim:70-84`.

**The decision path** — `src/hidden_agenda/llm.nim`:

- One parallel batch per decision point: `decideAll` builds a single `RequestBatch` over every open seat and issues `client.curl.makeRequests(batch, client.timeoutSeconds)` (`:697-707`). There is no per-seat request loop anywhere. The retry is a second single batch, not a per-seat retry (`for attempt in 0 .. 1`). `tests/test_llm.nim:oneBatchCarriesEveryEligibleSeat` asserts `driver.batchSizes == @[5, 4]` after a freeze. Empirically the CI replay has 16 `order` rows across exactly 4 decision points (5 + 4 + 4 + 3), matching `activeSeats` at each.
- Tolerant parse: `extractJsonObject` (`:518-527`) takes `find('{') .. rfind('}')`, so fences and prose on both sides are accepted; tested on both (`test_llm.nim:28-42`).
- Strict validation: `parseReply` (`:529-609`) enforces every row of the note's schema table — plan is an array of 1..`planSteps`, job in **this role's** enum, `at` a real seam, `who` an active alias, `room` a real room, `vote` required at a meeting and an active alias or `skip`, `switch` an object or null with both keys valid. `say` in a no-talk variant is **ignored, not rejected, and not recorded** (`:604-606`), asserted at `test_llm.nim:100-119`.
- Retry-once-then-fallback: attempt 0 → `dsLlm`, attempt 1 → `dsRetry`, exhausted → `scriptedDecision(skMiner)` with `dsFallback` and the log line `hidden-agenda llm: seat N falling back to scripted decision` (`:724-728`), exactly the note's string. The retry batch appends `RetryHint` (`:29-32`), which is the note's sentence verbatim (design.md:839-841). Source reaches the replay on every `order` row (`sim.nim:653-657`, `events.nim:81-90`) — confirmed in the CI replay (`"source":"scripted"` on all 16).
- Transport ladder: haiku-only `bedrockModelIds()` (`:72-79`) with `BEDROCK_MODEL` override; credentials in the note's order — Bedrock sidecar pair → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI` (`:95-123`, `:58-70`); no credentials → `disabled = true` and every seat scripted, which is what keeps offline certification deterministic. `maxOutputTokens` defaults to 900 and no `output_config.effort` is sent (`:617-637`, with the reason in a comment).
- The observation is per-role and leak-free: `seatView` (`:175-296`) gives `canFreezeNow` / `freezeCooldown` / `fakeDeposits` / `lastFakeDepositSeenBy` **only** to the impostor, and never tells any seat who can see *it*. `tests/test_noleak.nim:impostorNeverLearnsWhoCanSeeIt` (150-171) parks a watcher behind the impostor and asserts the frame does not place it. `canFreezeNow` is computed by `freezeTargets` (`kernel.nim:146-165`), which calls the same `freezeLegal` the sim applies.
- Prompts carry everything the note lists (`systemPrompt` `:308-371`, `userPrompt` `:378-512`): role and impostor count, the station, the plan model, the vision model spelled out including "VISION IS NOT MUTUAL", the beam with range and cooldown, both meeting triggers, the tally rule, the deposit rule, simultaneity, the `hunch`/`notes` visibility statement, the no-chat statement in a no-talk variant, the operator block under the note's exact heading, the per-role/per-moment enums, and the closing OUTPUT FORMAT paragraph verbatim.

**Every wait and its bound:**

| wait | where | bound |
|---|---|---|
| LLM batch | `llm.nim:707` | `client.timeoutSeconds` = `llmTimeoutSeconds` = 14 |
| retry batch | `llm.nim:694` | one extra iteration, same 14 s |
| batch spacing floor | `llm.nim:797-803` | `minBatchSeconds` = 14 between batch **starts**; tested at `test_llm.nim:174-190` |
| decision batches | `llm.nim:782-793` | `maxDecisionBatches` = 20, then reuse-previous with `source: "budget"`; tested at `test_llm.nim:192-217`; measured worst 12 |
| play deadline | `sim.nim:687-689`, `:693-696`; `sim_config.nim:88-93` | `0.6 × episodeTimeoutSeconds` = 720 s, checked at the top of **every** tick and again at every meeting open, → `endEarly()` → `reason/ending: "deadline"`, all scores 0; tested at `test_llm.nim:219-231` |
| seat connect | `server.nim:181-189` | `playerConnectTimeoutSeconds` = 120 s, then start with whoever is there |
| seat registration | `server.nim:191-200` | `min(now + 3, connectDeadline + 3)` |
| `final` broadcast | `server.nim:137-149` | a 3 s-per-socket allowance, skipping past budget |
| artifact flush | `server.nim:164` | fixed `sleep(500)` |
| shutdown grace | `server.nim:262-265` | `shutdownGraceSeconds` = 20, then `quit(0)` |

Static budget check: `sim_config.validate:132-139` refuses any config where `maxDecisionBatches × 2 × llmTimeoutSeconds + playerConnectTimeoutSeconds > 0.6 × episodeTimeoutSeconds + 1`. At defaults that is 20×2×14 + 120 = **680 s ≤ 721 s**, matching the note's ~685 s arithmetic (design.md:566-575). I looked for unbounded loops and found none: `runEpisode`'s loop is bounded by `maxTicks`/`done`/the deadline; the step-7 multi-pass clears at least one `wantsMove` per productive iteration (≤ 5); `advancePlan` carries an explicit `guard < 8`; the connect loops are wall-clock bounded; `decideAll` is `for attempt in 0 .. 1`. No blocking read: `pushStateFrames` and `refreshSnapshotLocked` swallow send errors, and the lock is released before any network call (`server.nim:240-248`).

**Degrade paths:** a seat that never registers is demoted to `miner` and a `COGAME_PLAYER_FAILURE_URI` declaration is written (`server.nim:204-219`); a socket that dies mid-episode is demoted in the `CloseEvent` handler (`:393-404`) and re-read live at the next decision point (`:245-247`); zero seats connected → `settle("forfeit","forfeit","none")` → artifacts → grace → `quit(0)` (`:221-226`); a bad token gets a 403 and a duplicate a 409, never a hang (`:311-322`); `/global` pings are answered with a Pong (`:355-357`).

**String truncation:** `cleanText` (`sim_state.nim:95-99`) is `strip` → `runeSubStr(0, limit-1) & "…"`, so the result is exactly `limit` runes and never cuts mid-rune; `oneLine` (`:101-102`) maps newlines to spaces first. Applied at `llm.nim:606-608` (`say` 90 / `hunch` 80 / `notes` 240), `llm.nim:644,655,658,669,721` (error and body text at 200/160), `server.nim:371-373` (`PLAYER_PROMPT` at 4,000, rune-checked), and `hidden_agenda_player.nim:53-54` (`runeSubStr` before sending). The end-to-end proof is `tests/test_llm.nim:capsAreRuneSafe`, which pushes 300 × `é`, 300 × `中` and 400 × `…` through `parseReply` and asserts `validateUtf8 == -1`, plus `tests/test_replay.nim` re-reading the whole replay with `validateUtf8`. I independently decoded the 55,447-byte CI replay as strict UTF-8: clean.

**The replay writer (`hidden_agenda.replay.v1`) — self-sufficiency, checked field by field against the CI artifact:**

`protocol`, `game`, `gameVersion`, **`seed`** (5), `tickHz` (24), `names` (5 aliases), `policyNames` (5), **`roles`** (`["crew","crew","crew","crew","impostor"]`), `colors` (5), `config` (32 keys — the full 19×27 ASCII `grid`, `rooms` with doors, `seams`, `grate`, `spawns`, and every rule constant including all four meeting tick offsets and `impostorSlot`), `frames` (343, each `c` 30 ints / `v` 5 / `g` 6 / `d` / `ph`), `series.race` + `series.crew`, `beats` (9 rows, only the six declared kinds), `events` (57 rows), `results` (the `results.json` object verbatim). `replays.nim:44-46` writes `roles[]` **after** the episode, by the same writer that writes `results`, so no player process can read it. Size 55 KB against the 8 MiB assertion. The frame `state` code is the note's `0 active / 1 mining / 2 depositing / 3 frozen / 4 ejected / 5 in-meeting` (`sim.nim:31-39`) — all of 0,1,3,4,5 observed except 2 in this short episode; `ph` carries 0,1,3,4,5.

Event vocabulary: all 13 of the note's kinds are emitted by `events.nim` with the note's field sets. Observed in the CI replay: `reveal` ×5 at tick 0, `seam` ×3, `mine` ×4, `deposit` ×4, `freeze` ×2, `witness` ×3, `caught` ×2, `meeting` ×3, `vote` ×11, `eject` ×3, `order` ×16, `end` ×1 (57 total, against the note's "under 700"). The `freeze` row carries one extra field (`room`) beyond the note's list; `eject` is emitted at every resolve with `target: null` when nobody goes, which is what the note's "alias or `null`" allows.

`results.json` (429 B in CI): all eight required keys present, all five arrays length 5, `scores` `[1,1,1,1,-4]` summing to **0**, `win = scores > 0`, `winner: "crew"`, `reason: "complete"`, `ending: "impostor_ejected"`, plus `deposits/depositTarget/freezes/witnessedFreezes/ejections/ejectedImpostor/wrongEjections/fakeDeposits/meetings/ticks`. Scoring is the note's ±1/±4 (`sim.nim:117-124`): crew win → +1 crew / −4 impostor; impostor win → −1 crew / +4 impostor; none → 0. Frozen and ejected crew still get the crew result (the score is keyed on `role`, not on `state`). No partial credit for deposits anywhere.

**The viewer's derivation from the replay bytes** (`src/hidden_agenda/global.nim:179-325`): `replayMeta` reads `replay.names/policyNames/roles/colors/doc.config`; `replayFrame` indexes `replay.frames[tick]` (a seek is an array index — `tests/test_broadcast.nim:145-147` asserts `b.t == target`); `replayChrome` reads `replay.race`, `replay.lullSpans()`, `replay.beats`, `replay.results` and replays `eventsByTick` up to the playhead to reconstruct the vote board's `m.votes`/`m.tally`/`m.n`/`m.cause`, with `m.phase` coming straight off the frame's `ph`. `meta` rides only the first packet (`:320-321`), asserted at `test_broadcast.nim:135-142`. The wasm entry reads the load packet directly and never re-derives `meta` from a later frame (`replay-viewer/hidden_agenda_replay.nim:47-68`). Nothing outside the `.replay` file is fetched.

**Both name spaces (item 4):** every observation and prompt uses `Aliases` only (`llm.nim` has no reference to `policyNames`); `broadcast.buildStateJson:69-78` puts the alias in `roster[].name` and the **policy** in `roster[].pol`; `tests/test_broadcast.nim:47-53` asserts both. `results.names` are policy names, `results.aliases` the aliases. Both present.

**Item 13 — the viewer executes.** `wasm-viewer` `needs: docker-smoke` (`.github/workflows/ci.yml:212`) and downloads the `smoke-replay` artifact (`:277-281`). The step "Load the bundle in a real browser" ran and printed `{"loaded":true,"ms":329,…}` with three distinct clock readouts (`0%="TICK 242 / 900 MEETING 2 — VOTING"  50%="TICK 188 / 900 DEPOSITS 2 / 12"  100%="TICK 342 / 900 FINAL"`) and a 10 s soak that kept advancing. No `continue-on-error` anywhere in the job. `data-replay-loaded` is set on the first drawn frame at `replay-viewer/static_replay.js:153` and `data-replay-error` in `showFailure` at `:20`; both are the starter's own code paths (the file diffs against `coworld-ctf`'s only in the `ctf_*`→`hidden_agenda_*` renames, the worker name string and the removal of the mismatch-tick block). **Link-flag / bootstrap pair:** `replay-viewer/config.nims` carries **no** `-s MODULARIZE=1` and no `EXPORT_NAME` (diff against the starter's `config.nims` is four rename hunks only), and `replay-viewer/static_replay_worker.js:181` bootstraps with `Module.onRuntimeInitialized` after `importScripts('./wire_constants.js','./broadcast_core.js','./hidden_agenda_replay.js')` at `:232`. Matched pair, both from coworld-ctf, and `loaded: true` is the proof. `tools/build_replay_viewer.sh` carries the `mkdir -p "$(dirname …)"` fix before the containment check (`:28`), the renamed image tag, and the `/workspace/hidden_agenda/replay-viewer/dist/.` copy path.

**Item 14 — transport rules,** each checked in the page:
(a) `relayout()` (`tools/_page_script.js:636-680`) measures `#scorebug` and `#transport` and sets `--hudscale`, `--topband`, `--band` on `document.documentElement`, iterating up to four passes to a fixed point. On `:root`, not `#stage`.
(b) The game block's two overlays are `position: absolute` inside `#chrome` and are explicitly band-clipped: `#rosterstrip { top: calc(var(--topband,0px) + 5*var(--u)); }` and `#voteboard { max-height: calc(100% - var(--topband,0px) - var(--band,0px)); }` (`tools/_page_css.css:61-108`). `#board`, `#lightpool` and `#endcard` are the starter's own band-aware rules, unmodified.
(c) `#endcard { top: var(--topband,0px); bottom: var(--band,0px); }` and `#endcard.on { display: flex; }` are inherited byte-for-byte; the page shows it with `classList.add('on')` and **every** seek takes it down — `seekTo` calls `hideEndcard()` first (`_page_script.js:605-608`), and restart/back/forward/end buttons (`:610-621`) and the `, . b e` keys (`:636-648`) all call it explicitly. The scrub-track click routes through `seekTo` (`:625-634`).
(d) `buildAgendaBeats` calls the chrome's aliased `markBeat` and `upgradeBeatButtons` (`:457-484`) replaces each placed `div.beat-marker` with a `<button type="button">` carrying `title` + `aria-label` and a click handler wired to `seekTo(tick)`; `applyBeatSpoilers` re-applies the `?spoilers=0` gate to the replacements. `tools/_page_css.css:182-219` has a rule for all six kinds the sim emits (`meeting freeze caught eject deposit gameover`), and `tests/test_broadcast.nim:beatsAreOnlyTheSixDeclaredKinds` asserts the sim emits no seventh.
(e) Zoom bar + minimap: the board is a fixed 1080×760 that always fits the frame, so `#viewpanel` and all its children are removed from markup, CSS and the id test-list; the page never calls `core.zoomAt/setZoom/attachMinimap` (grep over `tools/_page_script.js`: no hits). The stubs that remain in `client/broadcast_core.js:518-527` are unreferenced.
(f) The banner builder is `buildAgendaBeats`, never `function markBeat`, and `tests/test_broadcast.nim:noScopeDuplication` extracts the page's `var X = C.X` alias list (9 names, `markBeat` among them) and asserts no `function X(` in the game block collides with it.

**Item 6 — `num_agents`.** Present as `5` in all three `variants[].game_config` and in `certification.game_config`, verified by parsing the manifest; `config_schema.num_agents` is `integer, minimum 5, maximum 5, default 5`; `sim_config.validate:99-100` refuses anything else. `tools/ci/docker_smoke.sh` is the template verbatim with `<slug>`→`hidden-agenda`, `<IMAGE>`→`coworld-hidden-agenda`, `<SEATS>`→`5` (diff against `templates/tools/ci/docker_smoke.sh` is those substitutions only, so all four seat invariants and the `SEAT-COUNT FAIL:` prefix are intact), mode `100755`. I grepped the full `docker-smoke` job log for `SEAT-COUNT FAIL`: **no hits**; it printed `game=hidden_agenda seats=5 …`, `all 5 player containers exited 0`, `episode end reason: complete`, `smoke OK: seats=5 results=429B replay=55447B reason=complete`.

**Item 7 — scripted baseline plays full episodes legally.** `tests/test_baseline.nim` runs 3 variants × 16 seeds × 4 baseline pairings = 192 episodes to their natural end, auditing every decision against its role's enum and the live roster and every board state every tick (`auditBoard` as the `onTick` watchdog): in bounds, walkable, `0 ≤ carry ≤ carryCap`, non-negative cooldown, action inside the twelve-value vocabulary, no two active cogs sharing a cell, `0 ≤ gems ≤ seamCapacity`, non-negative deposits, and consecutive freezes ≥ `freezeCooldownTicks` apart. It asserts `sim.done` and `reason in {complete, deadline, forfeit}` for all 192. CI printed `test_baseline: ok (5627 decisions, worst 0.026 ms)`. `results.reason == "complete"` specifically is asserted for the certification fixture at `tests/test_manifest.nim:248-249` and observed in the docker-smoke log. Tuning is enforced by `tests/test_feasibility.nim`'s seven gates rather than guessed.

**Item 10 / manifest.** Parsed and checked: top-level `$schema`, 7 `tags`, `episode_timeout_minutes: 20`, `player[]` (two entries, both on `{{HIDDEN_AGENDA_IMAGE}}` with `/bin/hidden-agenda-player`, resources as the note specifies, both seated in `certification.players`), three `variants[]` each with a `description` and five `players`, no top-level `version`, no `game.display_name`, `game.owner: "daveey"`, `game.runnable.type: "game"` with `env.ANTHROPIC_API_KEY_URI = "secret://coworld/hidden_agenda/anthropic_api_key"` — namespace equal to `game.name = "hidden_agenda"` = the compose service name = `GameName`. `config_schema` has `additionalProperties: false`, `required: ["tokens"]`, and `minItems`+`maxItems` on both array properties. `results_schema` requires all eight keys, every array is `minItems 5, maxItems 5`, and the three enums are the exact legal sets.

**Item 12 — release order and scaffold.** `coworld-release.yml` steps in order: Build the Coworld manifest (`:153`) → Certify locally (`:167`) → **Upload the policies** (`:206`) → Upload the Coworld (`:304`) → Put the Coworld secret (`:342`). All three workflows present. `tools/ci/docker_smoke.sh` present and `100755`. `tools/ci/policies.json` defines four policies: two `PLAYER_PROMPT` champions (`hidden-agenda-sleuth`, `hidden-agenda-shadow`), both carrying `USE_BEDROCK: "true"`, with champion #2 carrying `"player": "ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"`, plus two `PLAYER_SCRIPTED` fillers. The prompt texts are the note's champion prompts. I ran the item's gate verbatim — `grep -n '<slug>\|<IMAGE>\|<SEATS>'` over the three workflows, `docker_smoke.sh` and `policies.json` — **no matches, exit 0**. The four expected residue names (`<cow_id>`/`<sha>` in `ci.yml`'s static-route comment, `<run_id>` in both artifact-readback recipes, `<name>:vN` in the submit `policy` description) are present and left alone. Any smoke step depends on a freshly built binary in the same run (`docker-smoke` builds the image in-job; `wasm-viewer` `needs: docker-smoke`).

**Item 1 — CI green with no test loosened.** `git log -p -- tests/` over this run shows a single commit (`5fb4368`) that **adds** all eleven test files; there is no prior revision of `tests/` to loosen (the repo's only earlier commit, `1171fab`, is the Git-Data-API bootstrap). No `skip`, `xfail`, `--skip`, `continue-on-error` or deleted assertion appears anywhere under `tests/`, and `.github/workflows/ci.yml` runs `ls tests/*.nim` with no exclusion list (`NIM_TESTS*` repo variables are unset, so all eleven run, twice each: debug and `-d:release`). All twenty-two invocations printed `test_*: ok` in run 32919193615.

**Deviation claims that match the code exactly:** #1 spawn widening (`station.nim:66-75`), #2 `freezeCooldownTicks 260` (`sim_config.nim:65`), #3 anti-gridlock multi-pass with swaps (`sim.nim:326-411`), #4 lurk-completes-on-sighting (`kernel.nim:94-106`), #5 `mostStaleActive` → −1 (`scripted.nim:39-58`), #6 meeting seats by `(row,col)` (`meeting.nim:83-103`), #7 seeded seam phase (`sim_state.nim:152-155`), #8/#9 gate (f) over 4,096 seeds and gate (e) per witnessed freeze (`test_feasibility.nim:41,145-171,178-196`), and the `ctf_mismatch_tick` drop (absent from `config.nims:53` and from `hidden_agenda_replay.nim`; `#mmwarn` absent from the page and asserted absent at `test_broadcast.nim:170-176`). The claims that do **not** fully match the code are recorded above as N1 (the ladder authorises `awarenessRadius` 3, not 4) and B2/#10 (`build_page.py` inherits the starter's CSS only, not its page).

---

## Could not determine

- **Whether B1 is intended to be blocking.** The checklist says "No `/client/replay` pod path anywhere"; the design note reads the same rule as "no `/client/replay` live viewer is *declared*"; the starter ships the route. What would settle it: a ruling on whether item 3's last sentence constrains the manifest or the container, or a statement of whether `coworld certify`'s "Replay liveness:" line is affected by an unadvertised route. I could not run `coworld certify` in this sandbox.
- **Whether the shipped DOM chrome keeps a full-cap `say`/`hunch`/`notes` inside the frame at 360 px** (N28). The fixture exercises the fixture's own CSS, and no CI replay carries LLM text. `.feed-row` is `white-space: nowrap; max-width: none;` inside a `#killfeed` of `width: calc(228 * var(--u))` with `align-items: flex-end`, so a 100-character row grows leftward; by arithmetic it fits (≈220 px at `--u = 0.5`, ≈600 px at `--u = 1.42`), but that is my calculation, not a measurement. What would settle it: driving the shipped `feedRow`/`banner`/`renderVoteBoard` builders inside `tools/ci/renderer_fixture.html` against the shipped stylesheet at 360 px, and gating the existing `overflowing` count.
- **Whether `awarenessRadius = 4` (N1) leaves the cone doing the work the design says it does.** The gates pass with margin on (b), (d) and (f), but gate (e) passes at 0.62 against a 0.60 floor and gate (c)'s impostor win rate is 0.00 — the impostor never wins against a `lurker` pairing. What would settle it: a sweep of `awarenessRadius ∈ {2,3,4}` printing gate (c)'s two numbers and gate (b)'s rate, which is one run of `tests/test_feasibility.nim` per value.
- **Whether any hosted episode would ever reach `maxDecisionBatches`.** Measured worst is 12 batches over 48 all-scripted episodes; the LLM path (which adds a retry batch, not a decision point) was never exercised in CI because `docker_smoke.sh` runs without credentials. What would settle it: phase 60's league episodes, or a `decideAll` test with a stubbed transport (see N14).
- **Whether the `fakedeposit` feed row, the quiet "NOBODY SAW IT" banner and the chat-variant `say` feed row render correctly.** None appears in any replay CI can produce (`fakeDeposits: 0`, both freezes witnessed, cert fixture is no-talk). What would settle it: a second cert-shaped fixture on the chat variant with a `miner` impostor, or extending `renderer_fixture.html` to drive `applyEvent` over a synthetic event list.
