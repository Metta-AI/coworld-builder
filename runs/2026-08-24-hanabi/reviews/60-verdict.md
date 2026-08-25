blocking: 0

# Phase-60 verdict — hanabi (run 2026-08-24-hanabi, adjudication of VERIFY.md attempt 2)

Head evidence: `runs/2026-08-24-hanabi/VERIFY.md` (2026-08-25T03:03Z, post-remediation, v2 rounds 7–9)
Checklist: `docs/SPEC.md` §Definition of done (L148–184), operationalized by `prompts/60-verify.md`
Independent read written before consulting any prior verdicts: yes. Every re-fetchable claim was
re-fetched by this judge at adjudication time (2026-08-25, post-03:06Z); nothing below rests on
the verifier's word alone except where noted.

## Item-by-item

### 1. ≥2 completed rounds after fillers set — TRUE
Re-fetched `GET /rounds?league_id=league_332c17c5…`: rounds 7 (02:26:32Z), 8 (02:40:55Z),
9 (02:55:35Z) all `completed`, matching VERIFY §1 byte-for-byte (a round 10 is now `pending`,
which changes nothing). `log.md` L77 records the v2 filler re-registration + trigger at
02:19:25Z, before round 7 was created (02:18:55Z creation is the trigger's own round; it
completed at 02:26:32Z, after fillers). Round 1's `failed` is recorded verbatim with its error,
as the prompt requires, and predates any filler. 3 ≥ 2. **Proven.**

### 2. Both champions ranked, fillers absent/Baseline — TRUE
Re-fetched `GET /divisions/div_0a3fd174…/leaderboard` (bare array): exactly two rows —
`daveey / hanabi-signaler:v2 / 1000.0 / rounds_played 8` and
`daveey-1 / hanabi-reader:v2 / 1000.0 / rounds_played 8`. Fillers absent. The prompt's bar is
rows for both champions with `rounds_played ≥ 1`; that is met on its face, independent of Elo.
**Coordinator ruling (a) tested and upheld:** the identical 1000.0 Elo is the pinned, designed
behaviour of a fully co-op game — design.md L191–199 says it out loud ("Elo never separates the
two champions — they will sit at 1000.0 forever") and directs check 2 to
`score`/`rounds_played`, which VERIFY does (mean team score 10/17/18 across r7/r8/r9, live and
rising). No SPEC line is falsified. **Proven.**

### 3. Latest round's episode request completed with replay — TRUE
Re-fetched `GET /episode-requests/ereq_2c1119ae-e7a7-441f-bd68-2fd8971eda45`:
`status: completed`, `replay_url: …/dac699c0-31b4-4ad7-95de-9e3a5ed34b50.replay`, seats 0/1 =
`hanabi-signaler` v2 (daveey) / `hanabi-reader` v2 (daveey-1) with `is_filler: false`, seats 2/3
filler `hanabi-conventions` v2 with `is_filler: true`. Matches VERIFY §3 exactly. **Proven.**

### 4. Replay bytes valid and show the game — TRUE
Re-fetched the S3 replay (29,012 bytes): strict `jq -e` parse OK; `protocol: hanabi.replay.v1`
(matches design.md L652–655's declared payload protocol); `results.reason: complete`. Champion
seats re-counted independently: seat 0 = 16 moves, origins `{llm:15, retry:1}`, `scripted_true: 0`;
seat 1 = 16 moves, all `llm`; `results.fallbacks: [0,0,0,0]`; `results.names` renders fillers as
`Baseline` / `Baseline (2)`. Decision notes are genuine Hanabi theory-of-mind content. The
prompt's literal `select(.type=="decision")` returning 0 is a schema-key difference (`kind`,
not `type`); VERIFY declares the substitution and it is faithful. **Proven.**

### 5. Hosted game log clean — TRUE (scoped round), residue correctly disclosed
Re-fetched round 9's elevated log (75,107 bytes) and re-decoded the `b'…'` reprs myself:
exactly 2 pattern hits, and they are one event — the haiku model throttled
(`429 "Too many tokens per day"`), model-switched to sonnet, and the seat-0 retry succeeded
(`origin: retry`, still LLM; fallbacks `[0,0,0,0]`). Zero `cut off at max_tokens`, zero
`LLM provider is unavailable` in the scoped log. I independently re-fetched **ledger's** log
(`ereq_4a4cd7ef…`): the identical model, identical 429 body, same window — the SPEC escape
clause ("a documented platform-wide cause checked against another LLM coworld", SPEC L162) is
genuinely satisfied, not asserted.
**Coordinator ruling (b) tested and upheld:** SPEC item 5's log is `/episode-requests/<id>/
artifacts/logs` where `<id>` is item 3's episode request — i.e. the latest completed round
(round 9). Scoping to round 9 is SPEC as written, not a concession. The r7/r8 seat-0
truncations sit outside the scoped check, were each recovered by the single retry with zero
fallbacks and all rounds `complete`, and VERIFY §5.3 pastes them verbatim rather than hiding
them — the cogame-raid-precedent treatment (round-level residue recorded while the scoped
check is clean) does not falsify any SPEC line. **Proven, with the §5.3 residue carried as a
non-blocking observation below.**

### 6. Public page uses the static replay path — TRUE
Re-fetched `https://softmax.com/hanabi`: no `<iframe>` in raw HTML (client-rendered — VERIFY
records this correctly as unknown, not a false negative), but the SSR payload's `playlist[0]`
is the round-9 episode on `cow_4c005d78-ebb2-4095-83da-cde90519f53b` at version **0.1.1** —
featured match present, on the remediated coworld, not the superseded `cow_2aedf124…`/0.1.0.
Re-issued `POST /coworlds/replays/session` myself: `viewer_url` is
`…/v2/coworlds/replays/static/cow_4c005d78-…/sha256%3A973eb76b…/index.html?replay=…&v=2`,
`ready: true` — static path, current cow_id, current manifest_sha (byte-equal to
`STATE.coworld.manifest_sha`), no `/client/replay`. VERIFY names its source (b) as required.
**Proven.**

### 7. Certification declared the static bundle — TRUE
Read the committed `runs/2026-08-24-hanabi/release-result.json` myself:
`.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared;
/client/replay and /replay not required)`. The file is the 0.1.1 artifact: `version 0.1.1`,
`cow_id cow_4c005d78…`, `manifest_sha sha256:973eb76b…` (all matching STATE and the check-6
iframe), all four policies at v2, `hosted_certification: certified`. Not stale. **Proven.**

### 8. Viewer executed and judged — TRUE
`viewer-smoke.json` is committed and its `.url` is byte-identical to the check-6 `viewer_url`
(run adoption proven from the artifact, not run ordering). Run `32803415305` re-checked via
`gh run view`: `completed / success`, created 02:58:40Z = the recorded dispatch time.
(a) `loaded: true` via **both** `data_replay_loaded: "true"` and bridge `["loading","ready"]`,
`bridge_ready: true`, no error, `failure: null`, 2,732 ms. (b) The three scrub clocks differ:
`TURN 0 / 80 · 0 / 25` → `TURN 32 / 80 · 7 / 25` → `TURN 64 / 80 · 18 / 25 · FINAL`.
(c) I read `viewer-smoke.png` myself: it shows Hanabi unmistakably — five colour-ordered
firework stacks (R4 Y4 G4 B3 W3 with x/5 counters), a DISCARDS strip with ×2 multipliers, four
cog avatars with face-out hands, hint/fuse/deck ribbon, right-hand event feed whose visible
lines ("Playing green 4 from slot 4 — 4 turns remain!", "Clearing dead card", "Widget plays a
blue 3 — blue reaches 3.") are replay events 60/61/63; the endcard's per-seat table
(6/0/6/4 · 6/0/4/6 · 4/0/8/4 · 2/0/8/6) reconciles exactly with `results.contributions
[6,4,2,6]`, `hints [6,8,8,4]`, `discards [4,4,6,6]`, `misplays [0,0,0,0]`, score 18. The chrome
is the bullwhip lineage (transport strip, tick-marked scrubber `66/66`, scorebug band, endcard)
— not a gridlock-style rewrite. Canvas text: 9,752 draws, 0 outside, 0 ellipsized. The
judgment paragraph in VERIFY §8 is legible, specific, and consistent with the artifacts.
**Proven.**

## Blocking items

None.

## Non-blocking observations

- [llm-residue] Rounds 7 and 8 each carried one seat-0 (`hanabi-signaler`, the long-reasoning
  prompt) `cut off at max_tokens` truncation despite the 0.1.1 raise to `maxOutputTokens: 900`;
  each recovered on the single retry with `fallbacks [0,0,0,0]` and round 9 is clean. Reduced,
  non-degrading, correctly disclosed in VERIFY §5.3 — but not proven eliminated. Worth a
  LEARNINGS.md line at close: the signaler prompt's preamble can still overrun 900 tokens
  before emitting JSON; a "JSON first, reasoning after" prompt nudge or a further headroom
  raise would retire the symptom.
- [provider-transient] One `anthropic error 500` (empty body) in round 8, retry-recovered;
  VERIFY correctly records it without claiming the platform exception (neither garble nor
  ledger showed a 500 in-window).
- [decoded-line-count] My decode of the round-9 log yields 288 lines vs VERIFY's 296 (same
  75,107 bytes, same 2 hits at the same content) — a decoder-regex difference with no bearing
  on the verdict.
- [prompt-schema-drift] `prompts/60-verify.md` check 4's `select(.type=="decision")` does not
  fit `hanabi.replay.v1` (events keyed on `kind`/`origin`). VERIFY's substitution is correct;
  the prompt could note that protocol-specific filters are expected.

## Verdict

VERIFY.md's evidence is current (0.1.1 / `cow_4c005d78-ebb2-4095-83da-cde90519f53b` throughout
— no stale 0.1.0 `cow_2aedf124…` references anywhere in its evidence chain), internally
consistent, and every re-fetchable claim survived independent re-fetch. All eight items of
SPEC §Definition of done are proven. Both coordinator rulings were tested against SPEC as
written and hold on their own merits.

BLOCKING: 0
