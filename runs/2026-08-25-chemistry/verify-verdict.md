blocking: 0

# Phase 60 verdict — chemistry (run 2026-08-25-chemistry)

Judge: fresh context, 2026-08-25 ~08:4xZ.
Checklist: `docs/SPEC.md` §Definition of done, as commands in `prompts/60-verify.md`.
Evidence file under adjudication: `runs/2026-08-25-chemistry/VERIFY.md` (verdict claimed: 8/8 TRUE).
Independent read written before consulting any fixer/self-report: yes — there is no fixer report
in phase 60; I read SPEC → prompt → design note → committed artifacts (including the png) →
VERIFY.md, then re-fetched live where cheap. Reading order as briefed.

Live spot-checks made by this verdict (all this session, ~08:40Z): rounds list, leaderboard,
`ereq_76bcca2e` detail, replay bytes from S3, hosted round-6 log (decoded), the public page SSR
payload, `POST /coworlds/replays/session`, and `gh run view 32825902427`.

## Per-check adjudication (refutation attempted on each)

### 1. ≥2 completed rounds after fillers set — STANDS (TRUE)
- Refutation attempt: re-fetched `GET /rounds?league_id=league_9b734c36…&limit=20` live. Now
  **6** completed rounds (2–7; round 7 completed 08:23:12Z, after VERIFY was written); round 1
  `failed` with exactly `Temporal RoundWorkflow failed before settling the round.` — verbatim as
  VERIFY records, and matching the documented pre-filler auto-trigger race
  (`playbooks/observatory-api.md` §6). VERIFY's five-completed snapshot was true at fetch time
  and remains ≥2 at head.
- Fillers-before-round-2: VERIFY's filler-policies fetch returns version ids
  `51066378-6b79-4dc1-b693-b71e45c3722c` and `33c53b59-b153-4b31-9b07-1d4e59a4a34c`, which are
  byte-identical to `STATE.policies.filler_version_ids` (STATE.json:26-29), and round 2's own
  episode request seats them `is_filler: true`. That is fetched proof, not a log claim. Not
  refuted.

### 2. Both champions ranked — STANDS (TRUE)
- Live leaderboard (bare list, per playbook §11): `1 daveey-1 chemistry-metabolist:v1 … 6 rounds`,
  `3 daveey chemistry-foreman:v1 … 6 rounds`; both `rounds_played ≥ 1`. No filler row and no
  `Baseline`-labelled row present — fillers **absent**, which the checklist accepts. Rows 2/4
  (`richard`, `relh`) are outside entrants with `is_filler: false` in the ereq participants; the
  checklist constrains fillers, not third-party entrants. Not refuted.

### 3. Latest round's episode request — STANDS (TRUE)
- Live `GET /episode-requests/ereq_76bcca2e-615a-414e-bce1-af7f369d46af`:
  `status: "completed"`, `replay_url: …/46fc7f16-62e3-4e48-b3d1-fbf973522107.replay` (non-null),
  participants exactly as VERIFY tabulates — seat 1 `chemistry-foreman`/daveey, seat 2
  `chemistry-metabolist`/daveey-1, seats 4–7 `is_filler: true`. Round 6 was the latest completed
  round at VERIFY's fetch time; a later round 7 does not retroactively falsify it. Not refuted.

### 4. Replay bytes valid, show the game, not all fallbacks — STANDS (TRUE)
- I re-fetched the replay from S3 myself: `http=200 bytes=141641`, `jq -e` strict parse ok,
  `protocol == "chemistry.replay.v1"` — matching the design pin (design.md:585, :946),
  `results.reason == "complete"`, `results.ending == "famine"`.
- Famine-as-complete is **declared by the design**, not improvised by the verifier:
  design.md:257 (famine row → `complete`/`famine`) and design.md:261-263 ("famine is a
  *completed game of Chemistry* … phase 60's check 4 therefore passes on a dead room").
- The "not all fallbacks" clause: my own group-by reproduces VERIFY exactly — champion seats 1
  and 2 are 7/7 `source: "llm"`, **zero** `fallback`, zero `scripted`; total fallback events 0.
  The champion `say` strings are state-referencing and non-boilerplate (charge levels, shortfall
  counts, lane assignments), with `notes` and `latencyMs` present. Not refuted.
- The fallback-heavy rounds 2–5 are not the verified round; the checklist verifies the latest
  round's replay, and VERIFY discloses the throttled rounds rather than hiding them. Correct
  handling.

### 5. Hosted log clean — STANDS (TRUE)
- I re-fetched round 6's log (`AUTH+ELEV`, http=200, 32181 bytes), decoded the `b'…'` reprs per
  playbook §10, and grepped: **0** lines matching
  `falling back|LLM provider is unavailable|cut off at max_tokens|rejected`; 0 `429` lines; the
  only `chemistry llm:` line is the transport banner. CLEAN, independently reproduced.
- The rounds 2–5 throttle narrative (Bedrock haiku daily-token 429, cross-checked against coins
  and hanabi logs) is the documented-platform-cause branch the prompt provides; I did not re-pull
  the coins/hanabi logs, and did not need to — the verified round's log is clean on its own, so
  check 5 does not rest on the cross-check. Known platform context (coordinator brief) agrees.

### 6. Static replay path + featured match — STANDS (TRUE)
- The raw-HTML grep finding nothing is the documented client-rendered case
  (playbook §Featured match: "the page is now client-rendered for the iframe"; `featured_match`
  null platform-wide) — recording it first and then using the SSR payload + session route is
  exactly what the playbook prescribes, and VERIFY names its source as required.
- Live re-fetch of `https://softmax.com/chemistry`: SSR `playlist[0]` present — now
  `chemistry.r7.e1` (the ladder moved on; at VERIFY's 08:17:52Z fetch it was `chemistry.r6.e1`).
  A featured match is present either way.
- Live `POST /coworlds/replays/session` returned a `viewer_url` **byte-identical** to VERIFY's:
  `…/v2/coworlds/replays/static/cow_292543de-…/sha256%3A1002ad49…/index.html?replay=…&v=2`,
  `ready: true`. Path shape is the static route; `<sha>` matches `STATE.coworld.manifest_sha`;
  no `/client/replay` anywhere. Not refuted.

### 7. Certification declared static bundle — STANDS (TRUE)
- Read the committed `runs/2026-08-25-chemistry/release-result.json` myself:
  `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared;
  /client/replay and /replay not required)` (release-result.json:11); `certify.ok: true`,
  `canonical: true`, `hosted_certification: "certified"`. Source correctly named (committed copy,
  per prompt §7). Not refuted.

### 8. Viewer executed and judged — STANDS (TRUE)
- CI fact checked, not accepted: `gh run view 32825902427 -R Metta-AI/coworld-builder` →
  `status: completed, conclusion: success, createdAt: 2026-08-25T08:18:04Z` — the run VERIFY
  cites, dispatched this phase, and `STATE.verify.viewer_check_run` matches.
- The committed `viewer-smoke.json` `url` field is byte-identical to the check-6 session
  `viewer_url` (including URL-encoding and `&v=2`) — the artifact tests the right target.
- (a) `loaded: true` via `signals.data_replay_loaded: "true"`, `data_replay_error: null`,
  `failure: null`, first frame at 9 684 ms. `bridge_ready: false` is fine — the spec accepts
  either the data-attribute or the bridge.
- (b) Three scrub readouts differ: `SHIFT 0 / 12 TICK 1 OF 420` → `SHIFT 3 / 12 TICK 227 OF 420`
  → `FINAL SHIFT OVER`. The replay advances.
- (c) **My own read of viewer-smoke.png** (independent of VERIFY's paragraph): the frame is
  legible and unmistakably this game. Top: a scorebug strip with three vat gauges (AMBER 0
  CHARGE / COLD / NEEDS 3+3, COBALT and BERYL the same) around a centred `FINAL — SHIFT OVER`.
  Below it a roster ribbon of eight chips pairing alias and policy owner (`BORAX daveey 1`,
  `CINDER daveey-1 1`, `DRAM richard 1`, `ARGON relh 0`, `EMBER Baseline 0`, `FLINT Baseline (2)
  0`, `GILT Baseline (3) 0`, `HOB Baseline (4) 0`). Centre: the endcard — `BORAX EATS BEST`,
  `FAMINE · DAVEEY`, `3 food made · 0 rotted · 1 cold start`, all eight score chips, `REPLAYING
  IN 4` — over a dimmed factory floor where vats, cog sprites and molecule tokens are still
  visible. Bottom: a full transport strip (restart, step-back, pause, `+5s`, step, loop,
  fast-forward, a `spoilers` toggle, `BORAX WINS`, `420 / 420`, speed buttons 1×–16×) above a
  scrubber carrying a `CYCLE CHARGE` momentum graph that steps down to the floor, with beat
  labels pinned on the track (`AMBER COLD`, `BERYL COLD`, `COBALT COLD`, `FAMINE`).
- **Starter-chrome question**: the starter is `coworld-ctf`, and its shell
  (`client/replay_broadcast.html` / `client/league_replayer.html`) uses exactly this chrome
  vocabulary — `transport`, `scrub`, `momentum`, `scorebug`, `endcard`, `Spoilers`,
  `fast-forward` all present in the starter's own markup. The png is that chrome re-skinned for
  chemistry, not a rewrite sharing only ids (the cogame-gridlock failure). Passes.
- **Reconciliation against the replay**: png chips `BORAX 1 CINDER 1 DRAM 1 ARGON 0 …` = replay
  `scores [0,1,1,1,0,0,0,0]` mapped through `names`/`aliases` (Argon=relh 0, Borax=daveey 1,
  Cinder=daveey-1 1, Dram=richard 1); endcard `FAMINE`, `3 food made`, `1 cold start` = replay
  `ending: famine, food_made: 3, cold_starts: 1`; `420 / 420` = 7 shifts × 60 ticks; the momentum
  graph's descending steps match the three `cold` events and the `famine` beat. Picture and
  record agree. Not refuted.
- Honest caveats VERIFY itself declares and I confirm: `feed_lines: 0` / `canvas_text.total: 0`
  because the shell paints into the wasm canvas (a probe limitation, not silence about a gap);
  the earlier 07:33Z dispatch's png is not committed and VERIFY correctly describes only the
  committed frame. The header `SHIFT 0 / 12` on a shift-7 famine and the overlapping beat labels
  at the track edges are real cosmetic nits, properly filed as non-blocking legibility notes.

## What I could not verify, and why it does not block
- The coins/hanabi cross-check logs (check 5's throttle attribution) — not re-fetched. Check 5's
  requirement is satisfied by the verified round's own clean log, which I reproduced
  independently; the cross-check only contextualises rounds 2–5, which no check depends on. The
  platform-wide Bedrock 429 outage is also independently attested context for this adjudication.
- The 07:33Z viewer-check run's artifacts — superseded; the committed artifact is the later run
  matching the check-6 src, which is the one the checklist scores.

## Non-blocking observations (concur with VERIFY's, for the coordinator)
- Chemistry's player lacks a model-level fallback (hanabi degrades haiku→sonnet; chemistry drops
  to scripted). Worth a phase-30-style item for a future version; not a definition-of-done item.
- Header shift denominator and beat-label overlap: cosmetic, phase-30 material.
- The featured famine round is a low-drama spectator artifact; design.md:262 sanctions it
  explicitly, so it cannot be charged here.

## Summary
Every one of the eight checks carries fetched evidence in VERIFY.md that I attempted to refute
and could not; six of the eight I re-fetched live and reproduced byte-for-byte (rounds,
leaderboard, ereq, replay, hosted log, session route) plus the CI run conclusion, and the two
committed-artifact checks (7, 8) match their sources. The spectator judgment is faithful to the
png, which I inspected myself: legible, the game, the starter's chrome. Zero blocking findings.

BLOCKING: 0
