blocking: 0

# verify verdict — raid (phase 60)

Run: 2026-08-22-raid   Coworld: raid v0.1.4 `cow_2e18fdd8-12cc-4ac7-9822-fa162635f3ef`
League: `league_7a5e52fa-e85e-41ab-8a66-418653b02de2`   Division: `div_b3560860-5922-48f5-b12a-0a6d57d3c506`
Checklist: `docs/SPEC.md` §Definition of done (phase 60, all fetched, never assumed) — 8 items.
Under judgment: `runs/2026-08-22-raid/VERIFY.md` (verifier's evidence file).
Independent read written before reading VERIFY.md: **yes** — I fetched rounds, leaderboard,
episode request, replay bytes, round-3 and round-2 hosted logs, the public page's SSR payload,
the replay-session API, the committed `release-result.json`, `viewer-smoke.json` and the png
myself (all at 2026-08-23, judge session) before opening VERIFY.md, and only then audited the
verifier's claims against my own results.

Judgment method: for each item I checked (a) that VERIFY.md carries fetched evidence (command +
output, not assertion), and (b) that a fresh fetch at judgment time agrees. Every re-fetch below
was mine, not quoted from VERIFY.md.

---

## Item 1 — ≥2 completed rounds after the fillers were set: **TRUE**

- My fetch of `GET /rounds?league_id=…&limit=20`: rounds 1, 2, 3 all `completed`
  (completed_at 07:52:07Z, 08:08:08Z, 08:22:19Z), no `failed`/`discarded`, every `error` null.
- Filler ordering: `log.md:84` `07:51:49Z 50 fillers 200: stalwart+greenhorn registered` precedes
  `log.md:85` `unpause … trigger-round 200`, and the verifier additionally proved it by effect —
  round 1's episode already seated both filler policy versions (`8885517e…`, `03c04710…`,
  matching `STATE.policies.filler_version_ids`) with `is_filler: true`.
- VERIFY.md §1 carries the full fetched round list, the completed-count jq (`3`), and the
  elevated filler-policies read. Evidence is fetched, not asserted. 3 ≥ 2.

## Item 2 — both champions ranked, fillers absent or Baseline: **TRUE**

- My fetch of `GET /divisions/$D/leaderboard` (bare array):
  `1 daveey raid-anvil:v1 1000.0 3 0.0` / `2 daveey-1 raid-triage:v1 1000.0 3 0.0`.
  Both `rounds_played = 3 ≥ 1`; exactly two rows, so fillers are absent — the "absent or
  Baseline" condition is met by absence.
- VERIFY.md §2 pastes the same full JSON and correctly explains the tied 1000.0 Elo as the
  cooperative shared-score design (all five `participant_scores` identical — I confirmed on
  the round-3 episode request), not a stalled ladder.

## Item 3 — latest round's episode request completed with a replay: **TRUE**

- My fetch: round 3 (`round_ebc98500…`, still the latest completed at judgment time) →
  `ereq_cfd10b7d-2d67-47b1-85db-7a014f48512c`, `status: "completed"`, `replay_url`
  `https://softmax-public.s3.amazonaws.com/replays/9648ed23-3a20-480b-bacf-d722e1f4ecc5.replay`.
- Participants: position 0 `daveey`/`raid-anvil` (`is_filler: false`), position 1
  `daveey-1`/`raid-triage` (`is_filler: false`), positions 2–4 the registered fillers
  (`is_filler: true`), rendered `Baseline`, `Baseline (2)`, `Baseline (3)` in the replay's
  `names.players`. VERIFY.md §3 matches byte-for-byte.

## Item 4 — replay bytes valid, protocol matches, champions doing the thing: **TRUE**

My own download and strict parse of the S3 replay:
- `jq -e .` passes → strict UTF-8 JSON ok (184374 bytes).
- `protocol` = `raid.replay.v1`; the published manifest (my fetch of `GET /coworlds`, raid
  v0.1.4 entry) declares in `manifest.game.protocols.global.value`: "The recorded replay is
  raid.replay.v1: strict UTF-8 JSON carrying protocol, format_version, …" — protocol matches.
- `results.reason` = `complete` (`end_rule: "wipe"` — a legal ending per design.md §End
  conditions; no `deadline` exception needed).
- Champion seats doing the thing the game is about: seat 0 (Alpha/daveey) 24/24 orders
  `source: "llm"`, seat 1 (Bravo/daveey-1) 23/23 `llm`; fillers all `scripted`; **0** fallback
  events in 102 orders; `fallback_turns [0,0,0,0,0]`. Order content is non-trivial and
  state-referencing — e.g. seat 0 turn 2: *"Phase 1 Forge, 94% boss hp. Slag pour resolving in
  0.5s at [644,364] - I'm safe at ranged south. Tank Delta holding threat. Cleave in 4s…"* —
  live HP percentages, telegraph timers, role assignments. Not scripted, not fallbacks.
- VERIFY.md §4 correctly notes the prompt's `select(.type=="decision")` finds nothing because
  this coworld's decision event is named `order` (design.md §Replay event table) and substitutes
  the equivalent count — a legitimate adaptation, evidenced, not an evasion.

## Item 5 — hosted game log clean: **TRUE as defined**, round-2 finding is advisory residue (ruled on explicitly below)

- My fetch of the **latest completed round's** log (`ereq_cfd10b7d…/artifacts/logs`, elevated):
  grep for `falling back|LLM provider is unavailable|cut off at max_tokens|rejected` → **CLEAN**.
  Round 3 is still the latest completed round at judgment time, so the check object has not
  shifted since VERIFY.md was written.
- My fetch of **round 2's** log (`ereq_7cd4e673…`): `falling back` ×6, `rejected` ×2 — the
  verifier's counts are exact. The hits are the sidecar's per-episode rate limiter
  (`"reason": "engaged", "limit_per_minute": 30, "rejected_total": 1`), a haiku
  `ThrottlingException`, and repeated timeouts on the fallback model id
  `us.anthropic.claude-sonnet-4-6` through the sidecar, each ending in
  `raid llm: seat N falling back to the scripted order`.
- My fetch of round 2's replay corroborates the verifier's numbers exactly:
  `llm_turns [30,29,0,0,0]`, `fallback_turns [1,4,0,0,0]`, 5 fallback events among 139 orders
  (3.6 %), `reason complete / end_rule wipe`.

**Ruling.** Round 2's dirty log does **not** falsify item 5. Reasons:

1. **The check's object is defined, and it is the latest round.** SPEC item 5's
   `/episode-requests/<id>/artifacts/logs` takes its `<id>` from item 3, which SPEC and
   `prompts/60-verify.md` both define as "**Latest round's** episode request" (`$EREQ` flows
   from check 3 into check 5 in the prompt's own commands). The latest completed round is 3 and
   its log greps CLEAN — fetched by the verifier and re-fetched by me. The "platform-wide
   cause" escape clause is only needed when the checked log is dirty; it is not invoked and the
   verifier explicitly declined to claim it.
2. **Polling to a newer round was a sanctioned retry, not evidence-shopping.** The prompt's
   retry budget names the approaches verbatim: "re-poll, different filter, **different round**".
   The verifier hit the check when round 2 was latest, recorded the failure, polled inside the
   75-minute bound, and re-ran the check as defined when round 3 completed. That is the
   procedure working as written.
3. **The intent of the check is also satisfied, not just its letter.** The check exists to prove
   the hosted LLM pipeline genuinely drives the champions. On the round under check it drove
   47/47 champion orders with zero fallbacks; even in dirty round 2 the champions were LLM-driven
   59/64 turns, the episode completed (`complete/wipe`, never a hang — degrade-never-hang worked
   exactly as designed), and round 2 would still have passed item 4's "small minority" test.
4. **The verifier surfaced the finding rather than burying it** — VERIFY.md's own verdict line
   flags it, §5b quotes the dirty lines verbatim with counts and a diagnosis, and it is
   explicitly routed to phase 80 / the judge. Nothing was hidden inside a TRUE.

**The residue is real and I confirm the verifier's diagnosis from the bytes:** (a) raid's
decision loop paces turns in *sim* time (120 ticks = 5 s), so when the sim outruns real time
(~2.1 s wall per turn in round 2) two live LLM seats generate ≈57 requests/minute against the
sidecar's per-episode 30 rpm cap; (b) the ladder's second candidate `us.anthropic.claude-sonnet-4-6`
times out on every sidecar call, turning one throttle into a fallback cascade. This will recur
intermittently in future fast rounds. **What would settle it** (advisory, not required for the
definition of done): floor each decision turn's wall-clock spacing so the episode's request rate
stays ≤ 30/min (e.g. a minimum inter-batch wall delay of `60 × live_llm_seats / 30` seconds),
and drop or correct the `us.anthropic.claude-sonnet-4-6` candidate (it is not serviceable through
the hosted sidecar); then re-release and re-grep a subsequent round's log. Route to phase 80
learnings.

## Item 6 — public page uses the static replay path, featured match present: **TRUE**

Independently re-verified both legs:
- `curl https://softmax.com/raid` → 359603 bytes, no `<iframe` in raw HTML (client-rendered, as
  the playbook records — *unknown*, not a false negative). The SSR payload contains
  `state.playlist[0]` = episode `raid.r3.e1`, `coworldId` = this cow, `replayUrl` = the round-3
  S3 replay, matchup naming both ranked champions → **featured match present**.
- `POST $BASE/coworlds/replays/session` with this cow_id + replay_uri (the call the page's JS
  makes) → `viewer_url` =
  `https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_2e18fdd8-…/sha256%3Aa5895254…/index.html?replay=https%3A%2F%2Fsoftmax-public.s3…9648ed23….replay&v=2`,
  `ready: true`. The `<sha>` equals `STATE.coworld.manifest_sha`. No `/client/replay` anywhere.
- VERIFY.md §6 names which sources it used and why the prompt's first two commands are
  uninformative here — the documented fallback chain was followed correctly.

## Item 7 — certification declared the static bundle: **TRUE**

- Read from the **committed** `runs/2026-08-22-raid/release-result.json` (never `/tmp`):
  `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared;
  /client/replay and /replay not required)` — contains the required string verbatim.
  VERIFY.md §7 reads the same committed file and says so.

## Item 8 — viewer executed, replay advances, spectator judgment: **TRUE**

All three sub-conditions hold, from the committed evidence plus my own audit:
- **(a) loaded:** `viewer-check/viewer-smoke.json` → `loaded: true`, `ms: 3728`,
  `data_replay_loaded: "true"`, bridge `["loading","ready"]`, `bridge_ready: true`, no
  `data-replay-error`, `failure: null`. I verified the producing CI run myself:
  `gh run view 32628145791` → workflow `viewer-check`, `conclusion: "success"`, created
  2026-08-23T08:23:43Z. The URL in the json is exactly the item-6 iframe src.
- **(b) advances:** the three scrub clock readouts differ — `0:00 TURN 0/54` → `1:00 TURN 12/54`
  → `1:59 TURN 23/54` — monotonic, not a frozen frame.
- **(c) judgment:** VERIFY.md's paragraph is present and I checked it against the committed
  `viewer-smoke.png` myself: the png shows the SMELTER-9 scorebug with segmented boss bar reading
  `14,304 / 26,000 (55 %)` (= 26000 − 11696 removed, agreeing with
  `boss_hp_removed_frac 0.4498`), the `MELTDOWN / SLAG / FORGE` phase track, `ENRAGE 2:00`,
  clock `1:59 TURN 23/54`, the circular foundry pit with four pillars, labelled cog sprites with
  floating damage numbers, and a readable feed (`Charlie dies to SMELTER-9 at 1:59`, `Alpha says
  "kill adds, four alive"`, `Bravo dies to A8 at 1:53`) whose lines reconcile against the replay
  events (`t=2760 seat 0 order "kill adds, four alive"`; 5 deaths = `deaths: 5, end_rule: wipe`).
  The seat strip distinguishes champions (`dave…`) from baselines (`Base…`). Legible, and it
  shows the game. The verifier's two legibility caveats (harness `feed_lines: 0` vs six visible
  feed lines; clock glyphs overlapping the phase label) are accurate and correctly filed as
  advisory.

---

## Refuted

None. Every claim in VERIFY.md that I re-fetched was exact — including the round-2 failure
counts, the round-2 replay's `llm_turns`/`fallback_turns`, the CI run conclusion, and the
session-API viewer_url. No item's evidence was asserted-without-fetching, and the one item
resting on committed rather than fresh evidence (7) is committed exactly as its rule requires.

## Verifier report audit

| item | verifier said | I verified | agrees |
|---|---|---|---|
| 1 | 3 completed rounds, fillers in force from round 1 | rounds 1–3 completed (my fetch); log.md:84–85 ordering; filler pv ids seated in round episodes | yes |
| 2 | daveey + daveey-1 ranked, rp=3, no filler rows | identical leaderboard (my fetch) | yes |
| 3 | ereq_cfd10b7d completed, replay_url, correct participants | identical (my fetch) | yes |
| 4 | strict JSON, raid.replay.v1, complete/wipe, 47/47 champion LLM orders, 0 fallbacks | identical (my download + jq); manifest prose declares raid.replay.v1 | yes |
| 5 | round 3 CLEAN; round 2 dirty (6/2), not platform-wide, diagnosed | round 3 CLEAN (my grep); round 2 6×falling back + 2×rejected (my grep); r2 replay corroborates 5/139 | yes |
| 6 | SSR playlist[0] featured match; session API static viewer_url ready:true | identical (my fetches) | yes |
| 7 | committed release-result.json contains the required string | identical (my jq on the committed file) | yes |
| 8 | run 32628145791 success; loaded:true; clocks advance; judgment | run conclusion success (my gh); json + png match the paragraph | yes |

## Non-blocking observations (for phase 80)

1. **Round-2 LLM pacing residue** (verifier's FINDING, confirmed): sim-time turn cadence can
   exceed the sidecar's 30 rpm per-episode cap when the sim outruns real time, and the
   `us.anthropic.claude-sonnet-4-6` ladder candidate is unserviceable through the sidecar.
   Settle by pacing the batch loop to real time and fixing/dropping that candidate, then
   re-verify a later round's log. Intermittent recurrence in future rounds is likely until then.
2. Manifest prose calls the bundle "the STATIC **wasm** replay bundle"; the shipped bundle is
   pure-JS canvas (no `.wasm` asset). Static and working — the word is inaccurate, cosmetic.
3. `viewer_smoke.mjs` reports `feed_lines: 0` against a feed that visibly renders six lines —
   harness selector mismatch, worth fixing in `templates/tools/ci/viewer_smoke.mjs`.
4. Cooperative shared scoring leaves both champions at Elo 1000.0 with `episode_wins 0.0`; the
   ladder ranks but does not separate. Explained by design (design.md §Scoring), worth a note in
   learnings for future cooperative coworlds.

## Verdict

All 8 definition-of-done items are TRUE on fetched evidence, at the current head, with the
round-2 pacing finding recorded as advisory residue rather than a blocking failure of item 5.

BLOCKING: 0
