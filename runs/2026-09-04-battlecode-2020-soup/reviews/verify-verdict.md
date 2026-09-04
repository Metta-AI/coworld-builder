blocking: 0

# Phase-60 verdict — battlecode-2020-soup
Judge: fresh context. Checklist: `docs/SPEC.md` §Definition of done (phase 60) / `prompts/60-verify.md`.
Head: coworld-builder `2ddc75e` (the harness-fix commit); coworld `battlecode` v0.2.0
`cow_d9fc2f21-c095-4131-bd86-d35848e046f8`, league `league_b08a04aa-9d3d-4ff2-91a3-013e19a531cc`,
division `div_df107879-c101-4771-98b7-7adf428b78c1`.
Independent read written before accepting VERIFY.md's conclusions: yes — every platform fact
below was re-fetched by me at 2026-09-04 ~09:0xZ (`BASE=https://softmax.com/api/observatory/v2`,
bearer + `User-Agent: coworld-builder/1.0`), and I read all four screenshots myself before
reading the verifier's judgment paragraph in detail.

## Blocking findings

None.

## The eight checks — independent basis for each

1. **TRUE** — I re-fetched `GET /rounds?league_id=…`: now **3** completed rounds (round 3
   completed 08:42:12Z after VERIFY was written), all `error: null`, no failed/discarded rows.
   I re-fetched `GET /leagues/…/filler-policies` (elevated): both fillers present
   (`battlecode-bowl-of-chowder:v1` = `fef73ff9…`, `battlecode-examplefuncsplayer:v1` =
   `14072215…`), matching `STATE.policies.filler_version_ids` exactly. Ordering: `log.md:83`
   records the filler write in the 08:12:14Z phase-50 batch; round 2 was created 08:26:19Z and
   round 3 08:41:20Z, both after it on any reading. Round 1's settling `completed` is covered by
   the playbook rule the verifier cited (trigger-round fails instantly with no filler); the two
   later rounds satisfy the "≥2 after fillers were set" criterion outright, so nothing hangs on
   that inference.
2. **TRUE** — I re-fetched `GET /divisions/…/leaderboard`: exactly two rows, `daveey-1`
   (`battlecode-bc20-rusher:v1`, rank 1, MMR 1017.33, rounds 3) and `daveey`
   (`battlecode-bc20-latticer:v1`, rank 2, MMR 982.67, rounds 3). No filler row, no `Baseline`
   row. The numbers moved since VERIFY (round 3 ran) — that is the ladder running, not a defect;
   the check's stable facts (both champions ranked, fillers absent) reproduce.
3. **TRUE** — I re-fetched `GET /rounds/round_ae434347…/episode-requests` and
   `GET /episode-requests/ereq_330eeacf…`: `status: completed`, `replay_url` =
   `…/replays/bb7e21c2-3fe7-4dcf-b299-19b7ed1d1d1b.replay`, participants seat 0 =
   `battlecode-bc20-latticer` v1 / daveey, seat 1 = `battlecode-bc20-rusher` v1 / daveey-1,
   both `is_filler: false`. Round 3 has since completed, so this is no longer the *latest*
   round's request — but it was at verification time, and the featured match on the public page
   tracks the newest episode automatically (see 6); the check as run was correct.
4. **TRUE** — I re-downloaded the replay (HTTP 200, 73128 bytes) and re-parsed it myself with
   strict `bytes.decode('utf-8')` + `json.loads`: valid; `protocol == "cogame.battlecode.v1"`;
   `result.reason == "complete"`; `fallbacks == [0,0]`, `policy_kind == ["llm","llm"]`, zero
   `doctrine_fallback` events, both seats `fallback: null`. The two submitted doctrine sheets
   differ on **8 of 10 knobs** by my count (opening, terraform_start_round, lattice_radius,
   landscaper_count_curve, vaporator_budget, drone_role, rush_trigger, wall_hq_round — VERIFY
   says "7 of 10", an immaterial undercount in the conservative direction), with distinct mottos
   and map-specific notes — non-scripted decisions with non-trivial content. Three games on
   three maps, three distinct end reasons (`quality`, `quantity`, `hq_destroyed`), series split
   1–2, both seats building/mining/moving dirt in every game. The champion seats are doing the
   thing the game is about.
5. **TRUE** — I re-fetched the hosted log (elevated header, HTTP 200, 1754 bytes), decoded the
   `b'…'` reprs, and grepped all four gated patterns myself: **zero matches**. Both LLM calls
   `HTTP/1.1 200 OK`. The one `refused a seat-0 connection: seat 0 was given the wrong connection
   token` line is the seat-token guard and is followed by a successful seat-0 connect and
   `registered kind=llm label=latticer`; it contains none of the gated strings.
6. **TRUE** — I re-fetched `https://softmax.com/battlecode/bc20` (HTTP 200): the SSR payload
   carries `playlist[0]` = a featured match for `cow_d9fc2f21…` v0.2.0 (now round 3's episode
   `battlecode.r3.e1` — the playlist has legitimately moved on with the ladder), and the string
   `/client/replay` appears **zero** times in the page. I re-POSTed
   `POST /coworlds/replays/session` for this cow_id + replay: `viewer_url` =
   `…/v2/coworlds/replays/static/cow_d9fc2f21…/sha256%3A5f42d864…/index.html?v=2#replay=<s3>`,
   `ready: true` — the static route, sha byte-identical to `STATE.coworld.manifest_sha`. The
   `#replay=` fragment form of the static route is the documented 2026-08-28 variant, and the
   `?replay=` query form was proven equivalent by viewer-check attempt 3.
7. **TRUE** — I read the committed `runs/…/release-result.json` myself:
   `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared;
   /client/replay and /replay not required)`, corroborated by the same line in
   `.certify.output_tail`. Release run id `33850681870` matches STATE.
8. **TRUE at head, via the documented supersession** — and the supersession is **sound**:
   - *The original FALSE was genuine and correctly ruled.* The verifier applied the gate
     literally (50 % and 100 % readouts identical → FALSE) rather than inferring, and proved the
     cause with a controlled experiment: `?viewpanel=0` hides the zoom slider and the scrub
     array collapsed to exactly one entry (`attempt-2-viewpanel0/viewer-smoke.json`, which I
     read) — only possible if the zoom slider was the element being scrubbed. The 12.0× zoom
     knob at max in the attempt-1/3 pngs and the untouched playhead corroborate it. Instrument
     defect, not viewer defect.
   - *The fix touched only the instrument.* `git show --stat 2ddc75e`: three files —
     `templates/tools/ci/viewer_smoke.mjs` (+ this run's log.md/STATE.json). No file in the
     coworld repo. The mjs now resolves `SCRUB_SELECTORS = ['#scrub','#seek','input[type="range"]']`
     in preference order, present-and-visible wins, with the mis-click documented in the comment
     (viewer_smoke.mjs:444–452, read at head).
   - *Same object under test.* The rerun URL in `viewer-check-rerun/viewer-smoke.json` is
     **byte-identical** to attempt 1's URL (same cow_id, same `sha256:5f42d864…` manifest sha,
     same replay) — I diffed the two `url` fields.
   - *The re-run is real and passes all three conditions.* I verified via `gh run view
     33854861020`: workflow `viewer-check`, `conclusion: success`, `headSha: 2ddc75e` (so it ran
     the fixed harness). Its artifact (committed, which I parsed): `loaded: true` with **both**
     signals (`data_replay_loaded: "true"` and bridge `ready`), `failure: null`, and three
     differing clock readouts — `2:24 GAME 1 OF 3 — CLIMB` / `1:11 GAME 2 OF 3 — ALANDDIVIDED` /
     `FINAL MATCH OVER` — the seek crossing game boundaries, stronger motion evidence than a
     clock tick. (b) holds; (a) holds; (c) — the judgment paragraph is legible and shows the
     game, confirmed against the screenshots below and the replay events I re-parsed (feed lines
     = the replay's own `first_build` events; `WATER 0.01 / 0% flooded / HQ elev 4` at round 2
     precedes the first `flood_stage` at round 256; the rerun endcard's `HQ DROWNED AT ROUND
     464, WATER 2.00` is the replay's `hq_drowned` event verbatim).

## Ruling on the open observation: killfeed overdraws the stat boxes — ADVISORY, not blocking

What I see, from my own read of the pngs:

- `viewer-check/attempt-2-viewpanel0/viewer-smoke.png` (default FIT zoom — what a spectator
  actually gets): the killfeed's lower lines are drawn over two pieces of chrome in the
  bottom-right corner — a unit-tally strip (tiny `…NG0 DS0 FC0 dirt 0/50` glyphs reading through
  "Clan Basil builds its first miner — game 1, round 1") and the per-clan `soup / mined /
  refined` box (`soup 61/61, mined 0/0, refined 200/…` under "Clan Ash builds its first miner").
  Both are hard to read exactly where feed text crosses them, and the feed text itself is
  slightly degraded on those two lines. This is at default zoom, so it is a real shell layout
  defect, not an artifact of the zoom mis-click.
- `viewer-check/viewer-smoke.png` and `attempt-3-query-form/viewer-smoke.png` (12× zoom): same
  overlap, same corner.
- `viewer-check-rerun/viewer-smoke.png` (endcard at 100 %): the endcard is fully legible —
  winner `CLAN BASIL — DAVEEY-1`, cause `CLAN ASH'S HQ DROWNED AT ROUND 464, WATER 2.00`, final
  score, side-by-side doctrine summaries, blockchain digest; the killfeed and stat boxes are
  dimmed behind it.

Why it is advisory: the definition-of-done gate for check 8(c) is that the judgment is
*"legible, and it shows the game"*, and the spectator test is whether a spectator can tell who
is winning and why. Every primary signal answers that and is clean in every screenshot: the
scorebug (clan names, real player names, per-seat mottos, live point totals — 50–50 in game 1,
14 vs 85 at the end), the bc20 water pill (`WATER` level, `% flooded`, both HQ elevations — the
three numbers this game is about, on screen at all times), the board itself, the transport strip
with round counter and momentum graph, the narrating killfeed, and the endcard naming winner and
cause. What the overlap degrades is secondary telemetry whose content is duplicated elsewhere
(the killfeed narrates every build the tally strip counts; the endcard summarises soup refined,
landscapers, and dirt moved). A spectator loses per-clan economy counters in one corner for part
of the match; they do not lose who is winning or why. That fails the bar for a blocking
legibility defect against check 8(c), and no other checklist item speaks to it.

It is still a genuine z-order/layout bug in the coworld's viewer shell (the killfeed panel and
the stat-box/tally cluster claim the same bottom-right region instead of stacking), and it should
be fixed in the next version bump of `Metta-AI/cogame-battlecode` — recorded here as advisory
for the coordinator, per the verifier's own suggestion of a phase-30 note if the run returns for
review.

## Non-blocking observations

- VERIFY.md says the two doctrine sheets "differ on 7 of 10 knobs"; my count is 8 of 10. The
  error understates the evidence and changes nothing.
- The `filler_policy_version_ids` echo inside the `/rounds` body that VERIFY quoted is not
  present in the shape my re-fetch returned; the dedicated `GET /leagues/…/filler-policies`
  endpoint (which I did reproduce, elevated) is the load-bearing evidence and it stands.
- The leaderboard and featured match have moved on (round 3) since VERIFY — expected for a
  15-minute ladder; no stable fact in VERIFY.md failed to reproduce.

BLOCKING: 0
