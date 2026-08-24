blocking: 0

# verify verdict — cogolf (phase 60, attempt 2)
Judged: 2026-08-24 • Head: coworld-builder b5e2079 / cogame-cogolf 68034be • Checklist: prompts/60-verify.md §The eight checks (SPEC §Definition of done)
Independent read written before reading VERIFY.md: yes — all API/S3/page/artifact fetches below were re-run fresh by the judge before VERIFY.md was opened.

## Per-item verdicts (all PASS)

1. **≥2 completed rounds after fillers — PASS.** Re-fetched `/rounds?league_id=league_4cb6dc9b…`:
   **10** rounds, every one `status: completed`, every `error: null`, zero failed/discarded
   (round 10 `round_2cc4a241-…` completed 05:12:27Z, after VERIFY was written — the ladder rolled on).
   log.md:31 records fillers set before the round-1 trigger (03:19:21Z); rounds 2–10 unambiguously
   post-date filler registration under either the 03:17Z (VERIFY) or 03:19:21Z (log.md) timestamp.
   The league's `filler_policy_version_ids` (`c466d2ba…`, `6813522f…`) match the registered v2 fillers.

2. **Both champions ranked, fillers absent — PASS.** Re-fetched the division leaderboard (bare array):
   `daveey-1` rank 3 (`cogolf-sniper:v3`, rounds_played 10), `daveey` rank 4 (`cogolf-architect:v3`,
   rounds_played 10). Ranks 1–2 are the external players `richard`/`relh` — SPEC item 2 requires
   RANKED, not top-ranked, so this is a pass. Neither filler appears on the board; no `Baseline` row.

3. **Latest round's episode request — PASS.** Re-fetched round 9's ereqs: all 6 `completed` with
   replay_urls; `ereq_43df75c9-…` (the judged episode) is `completed`, replay_url
   `…/ff031f16-….replay`, participants exactly `daveey` (cogolf-architect **v3**) and `daveey-1`
   (cogolf-sniper **v3**), both `is_filler: false`, scores −13/+13. Also re-checked at current head:
   round 10 (now latest) has all 6 ereqs `completed` with non-null replay_urls, and both champions'
   rounds_played incremented to 10 — the check holds against the rolling latest round too.

4. **Replay bytes — PASS.** Re-fetched the S3 bytes (67,008 B): `jq -e` strict parse OK;
   `protocol: "cogame.cogolf.v1"` matches the manifest; `result.reason: "complete"`;
   `fallbacks [0,0]`, all `fallback_causes` zero; 18 submission events, all `fallback: null`;
   16/18 carry varied, hole-specific LLM notes and impls (152–1212 chars, divergent readings per
   clause), differentiated outcomes (breaches [1,7], par_fails [9,2], named killer_test, −13/+13).
   Judge independently caught, **before reading VERIFY.md**, that hole 1's two submissions are
   byte-identical to `title_case.LITERAL_IMPL` + the baseline note "playing the text as written"
   (verified against `server/cogame_cogolf/specs/title_case.py:65-67` at 68034be) — a client-side
   literalist substitution invisible to `result.fallbacks`. VERIFY.md §4 documents the same finding
   with the same 2/18 count and a plausible sidecar-cold-start cause; 2/18 is a small minority, the
   design's degrade path covers it, and the check as written passes. Fixer/verifier report audit:
   **agrees** — the disposition table's "16/18 LLM" is accurate, not flattering.

5. **Hosted game log — PASS.** Re-fetched `…/artifacts/logs` with the elevated header (2,012 B):
   grep for `falling back|LLM provider is unavailable|cut off at max_tokens|rejected` → **CLEAN**.
   The decoded bundle (init-config / bedrock-sidecar / game / worker) matches VERIFY.md verbatim.
   VERIFY.md is candid that player-container stderr is not in the bundle; check 4's byte comparison
   covers the player side. Non-blocking, correctly disclosed.

6. **Public page static replay path — PASS.** Re-fetched `https://softmax.com/cogolf`: no iframe in
   raw HTML (client-rendered, as the playbook records), but the SSR payload's `state.playlist[0]` is
   populated (now the round-10 episode, replay `97167237-…` — the feature rolled forward with the
   ladder; at VERIFY time it was `cogolf.r9.e3`). Re-POSTed `/coworlds/replays/session`: viewer_url is
   `…/v2/coworlds/replays/static/cow_9cef7a1e-…/sha256%3Aecaa3322…/index.html?replay=<s3 url>&v=2`,
   `ready: true`, `<sha>` = the coworld's manifest_hash. No `/client/replay` URL anywhere; cow 0.1.2
   is `canonical: true`.

7. **Certification static-bundle declaration — PASS.** Re-read the **committed**
   `runs/2026-08-24-cogolf/release-result.json` (committed at b5e2079's history):
   `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared;
   /client/replay and /replay not required)`; version 0.1.2.

8. **Viewer executed — PASS.** Re-read the committed `runs/2026-08-24-cogolf/viewer-check/`
   artifacts: `viewer-smoke.json` has `loaded: true`, `data_replay_loaded: "true"`,
   `data_replay_error: null`, `failure: null`; the judged URL is the static route with the round-9
   champion replay `ff031f16-…` (same episode as checks 3–5). Three scrub clocks differ:
   `HOLE 1 / 9 TITLE CASE A SENTENCE` → `HOLE 5 / 9 LONGEST RUN` → `FINAL REPLAYING IN 10S`, and the
   hole-5 title matches the recorded spec order in the replay bytes. Judge viewed `viewer-smoke.png`
   independently: a rendered endcard — `BASIL WINS`, per-seat cards whose numbers match
   `result.breaches [1,7]` / `par_fails [9,2]` / `illegal [4,2]` exactly, the killer test quoted, the
   right rail carrying spec prose + a 7-line `solve` + a tests-fired table, seat chips `#1 BASIL
   daveey-1 +13 / #2 ASH daveey −13`, and the starter's transport strip (play/step/+5/end, spoilers,
   `beat 145 / 145`, speed chips, scrubber with `HOLE|BREACH|ILLEGAL|FALLBACK|KILLER` tick legend).
   Not empty, not static, starter chrome — the spectator-judgment paragraph in VERIFY.md §8 is
   accurate against the rendered evidence, including its honest low-contrast-scroll legibility note.

## Non-blocking observations
- Hole-1 client-side literalist substitution (2/18 in r9, 0/18 in r8) — already logged in VERIFY.md
  §4 as a phase-30 note (warm the client on `welcome`, or record a client-side fallback flag).
  Independently confirmed by the judge; does not fail checks 4 or 5 as written.
- Minor timestamp discrepancy: VERIFY.md §1 says fillers registered 03:17Z; log.md:31 stamps the
  filler-set action 03:19:21Z. Immaterial — rounds 2–10 post-date both.
- VERIFY.md's leaderboard/featured-match snapshots (rounds_played 9, `cogolf.r9.e3`) have drifted at
  the current head (10, round-10 episode) in the passing direction; every drifted value was re-fetched
  and still satisfies its check.

BLOCKING: 0
