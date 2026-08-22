blocking: 0

# Phase-60 verdict — lighthouse
Run: 2026-08-22-lighthouse   Head STATE phase: 60   Checklist: docs/SPEC.md §Definition of done (via prompts/60-verify.md)
Independent read: SPEC and the phase-60 prompt were read before VERIFY.md; every check below was
re-fetched live (2026-08-23 judge dispatch) as a spot-check against the pasted record. All re-fetches
reproduced the verifier's bytes exactly (sizes, counts, and strings match to the byte).

## Item-by-item adjudication

### 1. ≥2 completed rounds after fillers set — PASS
- VERIFY pastes rounds 3 and 2 `completed` (23:17:09.769114Z, 23:03:13.419856Z), round 1 `failed`
  with its error quoted verbatim (`Temporal RoundWorkflow failed before settling the round.` — the
  documented pre-filler symptom; excluded by the prompt's own rule).
- Re-fetched `GET /rounds?league_id=$L`: identical three rows, identical statuses and error text.
- "After fillers were set" is established by fetched evidence independent of log timestamps: both
  counted rounds seated `is_filler: true` participants (`lighthouse-lantern:v2` /
  `lighthouse-wallhug:v2`), impossible with an empty filler list, and the fetched
  `/leagues/$L/filler-policies` list contains exactly the two filler version ids and neither
  champion. Established.

### 2. Both champions ranked; fillers absent or Baseline — PASS
- Re-fetched `GET /divisions/$D/leaderboard`: `1 daveey lighthouse-beacon:v2 1000.0 rounds_played=2`,
  `2 daveey-1 lighthouse-pilot:v2 1000.0 rounds_played=2`; no filler rows. Matches the paste.
- Equal Elo at 1000.0 is the arithmetic of two cooperative team-score ties (round 2 all 0.0,
  round 3 all 2.0); SPEC requires both champions *ranked* (present with rounds_played ≥ 1), not
  unequal ratings. Both are ranked. Established.

### 3. Latest round's episode request completed with replay — PASS
- Re-fetched `GET /episode-requests/ereq_7ae8cdc3-1c1b-4fcf-91ea-bf24d612683c`:
  `status: completed`, `replay_url` = the c8551f16… S3 URL, participants position 0 =
  lighthouse-beacon:v2/daveey (is_filler false), position 1 = lighthouse-pilot:v2/daveey-1
  (is_filler false), positions 2–3 the two fillers (is_filler true). Byte-identical to the paste.
  Established.

### 4. Replay bytes valid, protocol matches, reason complete, champions doing the thing — PASS
- Re-fetched the replay: HTTP 200, 25970 bytes (matches), `jq -e` strict-parses,
  `protocol == "lighthouse.replay.v1"`, `results.reason == "complete"`, scores [2,2,2,2],
  ticks 27.
- Scripted-fallback vocabulary: this game has no `decision` event kind; per-seat fallback is the
  `scripted` boolean array on `tick` events (design.md pins this — §Decisions, event table line
  ~611, and the `lighthouse llm: seat N falling back to scripted decision` log string). Re-computed:
  champion seats 0 and 1 scripted on **0/27** ticks; filler seats 2 and 3 on 27/27 — exactly what
  the check demands (champions non-scripted, fillers scripted by design). 11 `say` events with
  addressed, non-trivial content; a `key` pickup by seat 1 at tick 5. Corroborating round-2 replay
  pasted (0/35 champion scripted).
- Protocol "matches the manifest": the verifier *fetched* the hosted manifest and showed it carries
  no replay-protocol key (`protocols` keys = global, player), then matched the replay string against
  the design-declared protocol and the string compiled into the shipped viewer wasm — I re-fetched
  the wasm and `strings` finds `lighthouse.replay.v1` in it. That is the strongest match available
  and it holds. Established.

### 5. Hosted game log clean — PASS
- Re-fetched `artifacts/logs` (elevated): HTTP 200, 110799 bytes (matches), **0** lines matching
  `falling back|LLM provider is unavailable|cut off at max_tokens|rejected`; all four containers
  present, so the grep covered real content. The verifier's disclosed single transient Bedrock 500
  (1 of 51 sidecar calls, retried ok) matches none of the four patterns and no seat degraded
  (check 4's 0/27). Established.

### 6. Public page static replay path + featured match — PASS
- Raw `softmax.com/lighthouse` HTML has no `<iframe>` (client-rendered) — re-verified. The prompt's
  own rule says an empty grep is unknown, not false, and directs a fallback to what the page reads.
  The verifier went one better than the prompt's named fallback (the `/coworlds` detail API, whose
  `featured_match` is null platform-wide — pasted with bullwhip/parley as controls): it extracted
  the SSR payload (featured match `lighthouse.r3.e1`, daveey vs daveey-1, the same ereq as check 3 —
  re-verified present in the live page) and made the exact `POST /coworlds/replays/session` call
  the page's own fetched JS chunk makes to build the iframe `src`.
- Re-made that POST: `viewer_url` =
  `…/v2/coworlds/replays/static/cow_e0618924-…/sha256%3A2cc10989…/index.html?replay=<s3 url>&v=2`,
  `ready: true`. Path shape is exactly SPEC's static route (`<sha>` = STATE's `manifest_sha`,
  URL-encoded); no `/client/replay` anywhere in the response or the page HTML (re-grepped: 0).
  Source used is recorded in VERIFY.md as required. Established.

### 7. Certification declared static bundle — PASS
- Read the committed `runs/2026-08-22-lighthouse/release-result.json` (commit e7ca202, phase 40's
  artifact copy — the source the prompt mandates): `.certify.replay_liveness` =
  `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not
  required)`; `.certify.ok` = true, `.version` = 0.1.1. Contains the required substring.
  Established.

### 8. Spectator judgment from three fetches — PASS
- (a) Replay JSON: config grid, ordered event stream, and first/middle/last tick states pasted;
  the activity reads as the game (keeper broadcasts routing, runner collects a key, tide drowns
  the runners, episode ends `complete`). Grounded in the check-4 bytes.
- (b) Bundle: all six assets re-fetched — index.html 200/1528, chrome.css 200/12044,
  renderer.js 200/54965, lighthouse_replay.js 200/11403, static_replay.js 200/5923,
  lighthouse_replay.wasm 200/162418 (`file`: valid wasm module) — every size identical to the
  pasted table; the asset list is index.html's verbatim src/href set plus the loader-named wasm.
  None trivial, none an HTML error page.
- (c) Markers: re-grepped `static_replay.js` — `coworld-replay` present (the postMessage envelope,
  line 27) and `tell("ready")` at line 123. Both hit.
- The judgment paragraph rests only on these fetches; no DOM/browser/screenshot claim appears
  anywhere in VERIFY.md. Established.

## Refuted verifier claims
None. No pasted evidence was found missing, fabricated, stale, or contradicting SPEC. Every
spot-check (rounds, leaderboard, episode request, replay bytes, hosted log, session endpoint,
page SSR payload, all six bundle assets, bridge greps, committed release artifact) reproduced the
record exactly.

## Non-blocking observations
- STATE `verify.rounds[]` mixes an id (`round_2be3c46a-…`) with a prose entry
  (`"round_3 (completed 23:17:09Z)"`); round 3's id is `round_73ab91e9-…`. Cosmetic STATE hygiene,
  tied to no definition-of-done item.
- The static route being served by `api.observatory.softmax-research.net` (softmax.com proxy 404s
  the same path platform-wide, verified against bullwhip by the verifier) is correctly flagged as
  a playbook candidate for phase 80.

## Summary
| # | DoD item | verdict |
|---|---|---|
| 1 | ≥2 completed rounds after fillers set | PASS |
| 2 | Both champions ranked, fillers absent/Baseline | PASS |
| 3 | Latest round's episode request completed with replay | PASS |
| 4 | Replay bytes valid, protocol match, reason complete, champions non-scripted | PASS |
| 5 | Hosted game log clean | PASS |
| 6 | Featured match + static iframe src | PASS |
| 7 | Certification declared static bundle | PASS |
| 8 | Spectator judgment from three fetches | PASS |

BLOCKING: 0
