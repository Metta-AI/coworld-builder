blocking: 0
# verify verdict — walker-waterworld (phase 60)
Head: coworld-builder run dir at adjudication time (2026-08-26, post-12:20Z)   Checklist: docs/SPEC.md §Definition of done / prompts/60-verify.md   Independent read written before reading fixes: yes (VERIFY.md read after SPEC + prompt, per brief order; no fixer report exists in phase 60 — the audited artifact is VERIFY.md itself)

Adjudicated fresh-context against SPEC §Definition of done, with my own re-fetches
(rounds list, leaderboard, both episode requests, replay bytes + decoder re-run, hosted
logs re-decoded with my own script, coworlds list, replay session POST, page SSR payload,
both GH run conclusions). Every re-fetch is quoted below. Verifier's claim of 8/8 TRUE
**survives refutation**. Blocking count: **0**.

## Per-check rulings

### 1. ≥2 completed rounds after fillers set — TRUE (upheld)
- Re-fetched `GET /rounds?league_id=league_69fe3c37…` now: shape `{"entries":…}` (object —
  matches the verifier's deviation note, not the brief's "bare array"). Rows:
  - round 4 `round_0791257f` **completed**, created `2026-08-26T12:12:12Z`, completed `12:17:20Z`
  - round 3 `round_5de2864a` **completed**, created `11:57:11Z`, completed `12:04:54Z`
  - round 2 `round_1d3f3cd6` **completed**, created `11:42:11Z`, completed `11:47:50Z`
  - round 1 `round_0f71dacd` **failed**, error `Temporal RoundWorkflow failed before settling the round.` (matches VERIFY verbatim)
- **Ruling (a), the round-2 timestamp question:** fillers were POSTed at `11:42:50Z`
  (log.md line 48); round 2's *row* predates that by 39 s but its episode ran with two
  filler seats — I re-fetched `ereq_fe830e29` myself: positions 2 and 3 are
  `walker-waterworld-drifter` v2 `is_filler: true`. "After the fillers were set" is a
  guard that rounds counted toward done were played with the filler roster in effect;
  round 2 demonstrably was, so I would count it. **The ruling is moot regardless:** at
  the current state rounds 3 *and* 4 are both completed and both *created* after the
  filler POST, so even the strictest row-timestamp reading yields ≥2. TRUE either way.

### 2. Both champions ranked — TRUE (upheld)
- Re-fetched `GET /divisions/div_ef3424b8…/leaderboard` now (bare array, as documented):
  exactly two rows — `daveey` rank 1 `walker-waterworld-tandemhunt:v2` and `daveey-1`
  rank 2 `walker-waterworld-relay:v2`, each `rounds_played: 3` (was 2 at VERIFY time;
  round 4 has since settled), `score 1000.0`, `episode_wins 0.0`. No filler rows.
- **Ruling (b), episode_wins 0.0:** the checklist requires rows for both champions with
  `rounds_played ≥ 1` and fillers absent-or-Baseline — nothing more. Both hold.
  `episode_wins` is not a criterion; design.md's end table (line 430 region) declares the
  shared-score co-op with `win[]` all-false below `captureTarget = 20`, and the replay's
  `results.win` is `[false,false,false,false]` consistently. Elo staying at the initial
  1000 for both is the arithmetically forced consequence, not a defect. TRUE.

### 3. Latest round's episode request completed with replay — TRUE (upheld)
- Verifier's flat-route 405 and nested-route substitution are consistent with the API as
  it stands; I verified the detail route directly: `GET /episode-requests/ereq_0910faa4…`
  → `completed`, replay `…/d28f4f1b-941e-478d-a418-4898fb1c19d6.replay`, participants
  daveey (tandemhunt:v2, non-filler), daveey-1 (relay:v2, non-filler), shoal:v2 ×2
  `is_filler: true` — exactly as VERIFY pastes. (The round-3 episode was the latest
  completed at VERIFY time; round 4 completing later does not retroactively falsify it.)

### 4. Replay bytes valid and show the game — TRUE (upheld); substitution admissible
- **Ruling (c), admissibility of `tools/replay_summary.py`:** the design note declares it
  verbatim — `design.md` §"Replay bytes (self-sufficient)", lines 1035–1057: "The replay
  stays the starter's **binary `COWLDWWD`** format… **The phase-60 substitute for SPEC
  §Definition of done check 4:** `python3 tools/replay_summary.py …`". SPEC check 4's own
  text already delegates one clause to the design note ("or a `deadline` that the design
  declares acceptable"), SPEC's design pins endorse the starter's binary viewer format,
  and the verifier proved no JSON variant exists server-side (`.json` sibling 403; the
  elevated artifact route returns byte-identical content, sha `d21ee7fa…`). Admissible.
- **Independently re-executed**, not taken on trust: I fetched the replay myself
  (79104 bytes, sha256 `d21ee7fa3f768d88739bbab257ea7a232637b2499d32e9cb4ff8e7e5859fce1f`
  — identical to VERIFY's) and ran the repo's decoder: exit 0, strict `jq -e` ok,
  `protocol walker-waterworld/v1` (pinned by `tests/test_replay.nim:187`),
  `results.reason complete` / `endRule full_time` (the strict branch — the declared
  deadline carve-out was not needed), `captures 12`, **48 llm intents, 48 distinct says,
  `fallbacks 0`, `fallbackTurns [0,0,0,0]`**, seats 0/1 all-llm, seats 2/3 all-scripted.
  Every number matches VERIFY. Champion decisions are non-scripted, varied
  (4 modes on seat 0, 3 on seat 1), zero fallbacks. TRUE.
- Non-blocking observation: SPEC check 4's letter says "valid UTF-8 JSON" of the replay
  bytes themselves; a binary starter format satisfies it only via the design-note
  substitute. Worth codifying in SPEC so future judges need not re-litigate.

### 5. Hosted game log clean — TRUE (upheld)
- Re-fetched the elevated logs artifact myself (101527 bytes, matching size) and decoded
  with **my own** script (same repr-split technique): coworld-init-config 0 /
  bedrock-sidecar 195 / game 40 / worker 0 = **235 decoded lines, zero matches** for
  `falling back|LLM provider is unavailable|cut off at max_tokens|rejected`. A raw-bytes
  grep (over-approximation, catches plain substrings inside reprs) also finds 0. CLEAN,
  and positively non-silent: VERIFY's 48/48 bedrock call/complete tally reconciles with
  the replay's 48 llm intents. No capacity carve-out needed. TRUE.

### 6. Public page uses the static replay path — TRUE (upheld)
- Re-fetched `https://softmax.com/walker-waterworld`: no iframe in raw HTML (the
  documented client-rendered case — the prompt's own fallback branch), SSR
  `playlist[0]` present and pointing at `cow_36a12905… / 0.1.1` (now featuring the
  newer round-4 episode `4857d19e…` — featured match still present and still the
  canonical cow).
- Re-ran the session POST myself: `viewer_url` =
  `…/v2/coworlds/replays/static/cow_36a12905-cdf6-4c9e-8bc4-2c0e541b9fb1/sha256%3A68bb2bd3…/index.html?replay=…&v=2`,
  `ready: true`. Static route, sha = STATE's manifest sha, **not** `/client/replay`. TRUE.
- **Ruling (e), stray 0.1.0 cow:** re-fetched `/coworlds` — `cow_6f92bb4c…` 0.1.0 is
  `canonical: false`; `cow_36a12905…` 0.1.1 is the sole canonical. Every artifact in this
  run (episodes view, SSR playlist, session URL) resolves to the 0.1.1 cow. Benign;
  non-blocking.

### 7. Certification declared the static bundle — TRUE (upheld)
- Read the committed `runs/2026-08-26-walker-waterworld/release-result.json` myself:
  `.certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared;
  /client/replay and /replay not required)` — the required marker verbatim; `certify.ok
  true`, `canonical true`, cow/sha pair identical to the check-6 URL. Release run
  32963420881 re-checked via gh: `completed / success`. TRUE.
- Non-blocking observation: the artifact's `hosted_certification` field reads
  `"certifying"` — a snapshot at artifact-write time (hosted_smoke `passed`); not a
  check-60 criterion and the cow is canonical, but noted for completeness.

### 8. Viewer executed and judged — TRUE (upheld)
- CI fact re-checked: run 32967129036 `completed / success` (gh, my own call).
- Committed `viewer-smoke.json` read directly: `loaded: true`, `ms: 4431`,
  `data_replay_loaded: "true"`, `failure: null`, `console_tail: []`, scrub clocks
  `1:12 TIME LEFT` → `0:35 TIME LEFT` → `FINAL GAME OVER` — all three differ, exactly as
  VERIFY quotes them. Gate (a) and (b) both hold.
- **The png, judged with my own eyes:** legible at a glance and unmistakably the game —
  scorebug strip (`104.679 THE POD`, `4 SKIMMERS 24 NIBBLES`, `FINAL / GAME OVER`,
  `CAUGHT 12 / 20` over a 20-pip bar with 12 lit, `POISON 5 THRUST −6.52`); endcard
  `12 CAUGHT · score 104.679` with the rule banner and the POD table naming
  DAVEEY/SKIM-1 24/0, DAVEEY-1/SKIM-3 24/0, BASELINE/SKIM-4 0/0, BASELINE (2)/SKIM-2 0/0
  with AST/NIB/PSN/THR columns matching the replay's `assists/nibblesBySeat/poisonBySeat/
  thrustMeanPct` byte-for-byte; paintbot-lineage **transport strip** (reset, step,
  play, +5s, loop, ff, spoilers, `1773 / 1776`, 1×–16× speed buttons) and full-width
  **scrubber with momentum graph** (`LIVES LEAD` staircase, playhead at right). Four
  intent captions are visible lower-right and match the replay's turn-23 intents
  (`SKIM-1 … HUNT`, `SKIM-3 … AVOID`, `SKIM-4/SKIM-2 ESCORT "closing up"`). Chrome
  family matches the starter lineage — not a gridlock-style rewrite.
- **Ruling (d), `feed_lines: 0` vs 4 visible captions:** the item-8 gate is
  loaded + differing clocks + judgment paragraph; `feed_lines` is a pasted readout, not
  a gate. The captions demonstrably render (they are in the png and match the recorded
  turn-23 intents), so the zero is a harness selector gap, correctly disclosed by the
  verifier as an instrumentation finding rather than smoothed over. Non-blocking;
  fixing the viewer-check feed selector is a coworld-builder tooling item.

## Refuted
None. Every one of the eight TRUEs survived my attempt to refute it by re-fetching; no
inconsistency was found between VERIFY.md's pasted output and the live state, the
committed artifacts, or the replay bytes (identical sha256).

## Checklist pass (independent)
| item | status | evidence |
|---|---|---|
| 1 ≥2 completed rounds post-fillers | TRUE | rounds 3 (created 11:57:11Z) + 4 (created 12:12:12Z) completed, both post-POST-11:42:50Z; round 2 also counts by seating (ereq_fe830e29 drifter ×2 is_filler, re-fetched) |
| 2 both champions ranked | TRUE | live leaderboard: daveey r1 / daveey-1 r2, rounds_played 3 each, no filler rows |
| 3 latest round ereq completed + replay | TRUE | ereq_0910faa4 completed, replay d28f4f1b…, participants correct (re-fetched) |
| 4 replay valid + shows the game | TRUE | decoder re-run: exit 0, strict JSON, protocol/complete/full_time, 48 llm / 0 fallbacks; sha matches |
| 5 hosted log clean | TRUE | my own decode: 235 lines, 0 pattern matches; raw grep also 0 |
| 6 static replay path + featured match | TRUE | session POST re-run: static URL, ready:true; SSR playlist present, canonical cow only |
| 7 liveness-skip marker | TRUE | committed release-result.json `.certify.replay_liveness` verbatim; run 32963420881 success (gh) |
| 8 viewer executed + judged | TRUE | run 32967129036 success (gh); loaded:true, 3 differing clocks (committed json); png legible, chrome matches lineage, readouts reconcile with replay results |

## Fixer report audit
Phase 60 has no fixer; the audited claim set is VERIFY.md's.
| finding | verifier said | I verified | agrees |
|---|---|---|---|
| round-2 pre-POST row | counts via seating; round 3 alone suffices | seating confirmed live; rounds 3+4 now both post-POST | yes |
| episode_wins 0.0 | co-op shared score, not a criterion | design end table + win[] all-false; criterion is rows+rounds_played | yes |
| binary replay substitute | design-note-declared, no JSON variant | design.md:1047–1057 verbatim; .json 403; sha-identical artifact; decoder re-run matches | yes |
| feed_lines 0 vs 4 captions | harness selector gap, non-blocking | captions visible in png, match turn-23 intents; not an item-8 gate | yes |
| stray 0.1.0 cow | canonical:false, benign | re-fetched /coworlds: canonical false; all run artifacts resolve to 0.1.1 | yes |
| API shape deviations | rounds=object, flat ereq route 405 | rounds re-fetch returned object; detail route works | yes |

## Non-blocking observations
- SPEC check 4's "valid UTF-8 JSON" letter vs binary-starter reality should be codified
  (design-note substitute mechanism) so it is not re-litigated per run.
- `viewer-check.yml`'s feed selector misses this shell's caption node (`feed_lines: 0`
  against 4 rendered captions) — tooling fix in coworld-builder, not in the coworld.
- release-result.json snapshot field `hosted_certification: "certifying"` — not a
  definition-of-done item; cow is canonical and hosted_smoke passed.
- The momentum graph label `LIVES LEAD` on a shared-score co-op is starter-chrome
  vocabulary rather than this game's; cosmetic only.

BLOCKING: 0
