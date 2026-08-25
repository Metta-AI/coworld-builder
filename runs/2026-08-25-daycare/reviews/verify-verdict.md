blocking: 0

# Phase-60 verdict — daycare
Head: 42da474   Checklist: docs/SPEC.md §Definition of done (as operationalized by prompts/60-verify.md)
Independent read written before reading VERIFY.md: yes (all eight checks re-fetched or re-read from committed artifacts by the judge before opening VERIFY.md; judge fetches ran ~19:40–19:55Z, after the verifier's 19:23–19:33Z window, so live-state differences are noted where they occur).

## Item-by-item

### 1. ≥2 completed rounds after fillers set — PASS (re-fetched)
Judge's own `GET /rounds?league_id=league_b3316d91…&limit=20`: rounds 2–18 all `status:"completed"` (17 of them), round 19 `pending`, round 1 `failed` with error verbatim `Temporal RoundWorkflow failed before settling the round.` — the known pre-filler auto-trigger race. Fillers were registered before round 2: `log.md:48` (`50 fillers POST 200: caretaker+stubborn … unpause 200 … trigger-round 200`, 2026-08-25T15:04:15Z), and the same `/rounds` response body carries the league's
`filler_policy_version_ids":["f6155ca7-d319-4639-936c-ead67d116419","085a01ae-7273-4fce-ab52-15a4e1b262cd"]` — I verified that string is really in the fetched body (VERIFY.md:64–68 claimed it; it is true, not just plausible). 17 ≥ 2. No refutation.

### 2. Both champions ranked; fillers absent or Baseline — PASS (re-fetched)
Judge's own `GET /divisions/div_6fc85068…/leaderboard` (bare array):
```
1  richard   co-gas-daycare-caretaker-richard:v1    1189.04  14  32
2  daveey-1  daycare-provider:v1                    1009.50  17  22
3  relh      co-gas-daycare-caretaker-relhalpha:v1   917.76  14  17
4  daveey    daycare-attentive:v1                    883.69  17  12
```
`daveey` and `daveey-1` both ranked with `rounds_played` 17 ≥ 1. Neither filler label (`daycare-caretaker:v1`, `daycare-stubborn:v1`) nor any `Baseline` row appears — fillers absent, as the item permits.

On the third-party question I was asked to decide: richard's and relh's rows are **not** this run's fillers despite the "daycare-caretaker" substring in their policy names — their `policy_version_id`s (`ea39dd8b-…`, `ae15fa79-…`, read from the round-18 episode-request participants I fetched) differ from the filler UUIDs in STATE/`log.md:45` (`f6155ca7-…`, `085a01ae-…`), and they are owned by other player ids (`ply_ded11f40-…`, `ply_18302115-…`). The checklist requires the champions to be *ranked*, not to lead, and constrains only fillers. Open third-party submissions outranking a champion is the ladder working as a ladder. Does not affect the item. PASS.

### 3. Latest round's episode request completed with replay; participants correct — PASS (re-fetched)
Latest completed round at verification = 18 (`round_fb6e0387-…`). Judge fetched all 6 episode requests: every one `completed` with a non-null S3 `replay_url`. The champion-vs-champion episode `ereq_78f48587-25f3-4d2c-bc5c-003ae0a52977`: `status:"completed"`, `replay_url` `…/832718ed-….replay`, participants `daveey` (daycare-attentive v1, `is_filler:false`) and `daveey-1` (daycare-provider v1, `is_filler:false`), `participant_scores` 54/54. No `Baseline (N)` seats because four real entrants fill the round-robin — consistent with `insufficient_players: filler_policy` never firing. Matches VERIFY.md §3 exactly.

### 4. Replay bytes valid, protocol matches, shows the game — PASS (re-fetched)
Judge downloaded `832718ed-….replay` and re-ran the checks: `jq -e` strict parse OK; `protocol` = `daycare.replay.v1`; `results.reason` = `"complete"`. Decisions: the schema keys events by `k`, and `order` events carry `source` — 30 orders, **all 30 `source:"llm"`**, 15 per champion seat; `[.events[]|select(.fallback==true)]|length` = 0. Content is non-trivial and on-game: hunches/notes reason about preference inference from failed reaches (e.g. "Child has 134 failed reaches at apple tall trees (vs 0 at banana)…"), and `results` shows the loop working (`preference:"apple"`, `child_ate:[18,0]`, `delivered:[17,0]`, `wasted:[0,0]`, `guess_turns_correct:15/15`, `win:[true,true]`).
On "protocol matches the manifest": the published manifest carries only the player protocol (`daycare.player.v1`) and no replay-protocol string, so the verifier matched the replay's `protocol` against the design's declared value (`design.md` declares `daycare.replay.v1` for the replay file and the cert fixture asserts it) — VERIFY.md:197–204 discloses this honestly and I confirmed `design.md` contains both strings. The certification that gates check 7 ran that fixture green. Satisfied; noted as an advisory only because the manifest itself is silent, not wrong.

### 5. Hosted game log clean — PASS (re-fetched)
Judge fetched `…/artifacts/logs` for `ereq_78f48587` with the elevated header (64,983 bytes), decoded the python `b'…'` reprs per container (coworld-init-config, bedrock-sidecar, game, worker) per playbook §10, then grepped: **0 hits** for `falling back|LLM provider is unavailable|cut off at max_tokens|rejected` → CLEAN. Matches VERIFY.md §5 (same byte count, same containers). No exception invoked, none needed.

### 6. Public page uses the static replay path; featured match present — PASS (re-fetched)
Raw HTML of `https://softmax.com/daycare` has no `<iframe` (client-rendered — expected; recorded, not a false negative). Judge re-fetched the two real sources: (a) SSR payload `state.playlist[0]` is a daycare featured match — by my (later) fetch it had rotated to round 19 ep 6 (`replayUrl …/3cbba917-….replay`, finishedAt 19:33:49Z), versus VERIFY.md's r18.e6/`84f3b7af` snapshot at 19:2xZ; both are valid observations of a live ladder, and both show a featured match PRESENT. (b) `POST /coworlds/replays/session` with the cow_id → `viewer_url` = `https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_5b944b41-3f2f-4f84-a96b-c484811d7d55/sha256%3Ae4ba7e35…/index.html?replay=…&v=2`, `ready:true`. `<sha>` is the manifest_hash (matches `/coworlds` detail: `canonical:true`, `manifest_hash sha256:e4ba7e35…`). Static path, no `/client/replay` anywhere. (`/coworlds` returned a bare array in my fetch too — the dual-shape jq was genuinely required.)

### 7. Certification declared the static bundle — PASS (committed artifact, judge-read)
`runs/2026-08-25-daycare/release-result.json` (committed) → `.certify.replay_liveness` =
`Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)` — required substring present verbatim. Same source VERIFY.md read.

### 8. Viewer executed; spectator judgment — PASS (committed artifacts judge-read + CI conclusion judge-verified)
- CI fact checked, not accepted: `gh run view 32889498154 -R Metta-AI/coworld-builder` → `status: completed`, `conclusion: success`, createdAt 2026-08-25T19:25:39Z, workflow `viewer-check` — VERIFY.md only showed it `in_progress`; I confirmed the green.
- (a) loaded: `viewer-smoke.json` → `loaded:true`, `ms:2690`, `signals.data_replay_loaded:"true"`, `data_replay_error:null`, `failure:null`. SPEC accepts the DOM attribute **or** the bridge; the attribute signalled.
- (b) advances: scrub readouts differ and are monotone — 0% `TURN 1 / 15 TICK 0 OF 899`, 50% `TURN 8 / 15 TICK 468 OF 899`, 100% `FINAL TICK 899 OF 899`.
- (c) judgment: I viewed `viewer-smoke.png` myself. It is a fully rendered, legible broadcast frame at the final tick: scorebug `117 SCORE CHILD | BRAMBLE · richard` / `PARENT SCORE 117 | ALDER · daveey-1` (the two-name-space rule visible), endcard `TURN LIMIT — PAR BEATEN / THE PAIR FED THE CHILD / BRAMBLE WANTED BANANA · ALDER GUESSED RIGHT ON 14 OF 15 TURNS / 117 / 30 — PAR BEATEN / 39 bananas · 0 apples · 0 wasted · 309 reaches`, guess panel top-right (`RIGHT 14 / 15 TURNS` with the per-turn strip), two feed rows bottom-right, pixel-art yard with fruit trees and both labelled cogs behind the veil. Every endcard number reconciles with the featured replay's `results` (`scores [117,117]`, `preference "banana"`, `child_ate [0,39]`, `reaches [0,309]`, `guess_turns_correct 14`, `par 30`, `ending "turn_limit"`) — VERIFY.md's reconciliation is correct. The chrome is the starter's: transport strip (restart/step/pause/+5s/step/loop/ff), spoilers toggle, `1×…16×` speed ladder, full-width scrubber with SCORE graph rail and turn ticks. Not a gridlock-style rewrite.
- The tested URL is the check-6 iframe src (featured episode `84f3b7af`, daveey-1 vs richard) — exactly what prompts/60-verify.md §8(a) instructs ("against the iframe src from check 6"), and what a spectator actually gets. Conformant.

## Refutations of the verifier
None. I attempted refutation on every check by re-fetching or re-reading the primary source, and additionally audited the three most falsifiable secondary claims: (i) `filler_policy_version_ids` really is in the `/rounds` body (VERIFY.md:64) — confirmed; (ii) the `canvas_text` "0 drawn / 0 never inside / 0 ellipsized" readout (VERIFY.md:473) matches the committed `viewer-smoke.json` and `smoke-stdout.txt` — confirmed; (iii) run 32889498154's green, which VERIFY.md asserted from `gh run watch` exit 0 — confirmed `conclusion: success` directly. All fetched numbers, ids, byte counts and quoted strings in VERIFY.md that I re-checked were accurate. The only deltas between VERIFY.md and my fetches are live-ladder drift (round 19 completed after the verifier's window; featured match rotated; SSR leaderboard rounds_played 17→18), which corroborates rather than contradicts.

## Advisories (non-blocking)
1. **feed-probe selector mismatch** — `viewer-smoke.json` reports `feed_lines: 0` while the committed screenshot plainly shows two feed rows (`ALDER · LEFT BANANA BESIDE THE CHILD`, `BRAMBLE · ATE BANANA +3`). The probe in `templates/tools/ci/viewer_smoke.mjs` does not match this shell's feed element. Harness fix, not a viewer defect; the verifier flagged it too (VERIFY.md:559–561).
2. **postMessage bridge silent** — `signals.bridge_ready:false`, `bridge:[]`: the viewer signals readiness only via `data-replay-loaded="true"`. SPEC item 8(a) explicitly accepts either channel, so this passes as written, but any future harness or embed that relies on the `coworld-replay` bridge will see nothing. Worth a phase-30-class note for the next coworld.
3. **manifest carries no replay-protocol string** — check 4's "protocol matches" was necessarily matched against the design note's declared `daycare.replay.v1` (asserted by the cert fixture) rather than a manifest field, because the published manifest declares only `daycare.player.v1`. The verifier disclosed this; recording it so the gap in the manifest schema is visible.
4. **third-party entrants at ranks 1 and 3** (richard, relh) — verified to be distinct policy versions and owners from this run's fillers; no effect on item 2 (see above). Purely informational.

BLOCKING: 0
