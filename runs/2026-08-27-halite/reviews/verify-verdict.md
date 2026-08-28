blocking: 0

# Phase-60 verify-verdict — halite (run 2026-08-27-halite)

Judged: 2026-08-28T12:40–12:45Z · Judge context: fresh
Document under judgment: `runs/2026-08-27-halite/VERIFY.md` (attempt 2, 2026-08-28T09:28Z, 8/8 TRUE)
Checklist: `docs/SPEC.md` §Definition of done, as commands in `prompts/60-verify.md`
Independent read written before reading VERIFY.md: **yes** — checks 1–7 were re-fetched live and
check 8's committed artifacts were examined (including the png, viewed directly) before VERIFY.md
was opened. Reading order: 60-verify.md → SPEC §DoD → log.md → live fetches + committed artifacts →
VERIFY.md last.

Scoping rule honored: only rounds ≥ 5 count (rounds 1–4 ran the superseded 0.1.0 / v1 policies;
VERIFY.md's proof — round 4's ereq names `cow_97d89fb8…` and v1 version UUIDs — is consistent with
my fetches: every in-scope ereq I pulled names `cow_c6743b6c…` and the four v2 UUIDs).

The league has kept running since VERIFY.md was written: **19 completed rounds** now (15 in scope),
so I verified the checks at the *current* head — latest completed round 19,
`round_7aa746f4-bf9b-4221-bc74-58c181ffc7ab`, see check 3 —
and specifically looked for regression in the newest episode. There is none.

## Per-check table

| # | item | verifier | judge | my evidence (fetched 2026-08-28T12:40–12:44Z) |
|---|------|----------|-------|-----------------------------------------------|
| 1 | ≥2 completed rounds after fillers set | TRUE | **TRUE** | `GET /rounds?league_id=$L&limit=50` → 19 rounds, **all `completed`**, none failed/discarded. In scope (≥5): rounds 5–19 = **15 ≥ 2**. Round 5 created 09:00:47Z, after v2 fillers (~08:59Z per log.md) and v2 champion submits (09:00Z). |
| 2 | Both champions ranked, fillers absent/Baseline | TRUE | **TRUE** | `GET /divisions/$D/leaderboard` (bare array) → `1 daveey halite-tidereader:v2 1048.15 rp=19 wins=12` · `2 daveey-1 halite-privateer:v2 951.85 rp=19 wins=6`. Exactly two rows; fillers absent; both labels `:v2`. |
| 3 | Latest round's ereq completed with replay | TRUE | **TRUE** | Latest completed = round 19 `round_7aa746f4…`. Nested route `GET /rounds/$R/episode-requests` → `ereq_0b83b8b1-1c74-4cae-a23d-9a9ce64ad231 completed`. Detail: `status:"completed"`, `replay_url` = `…/replays/d87ff54f-7d5f-48b8-9872-ec60ae5729fa.replay`, participants seats 0/1 = `daveey`/`daveey-1` (v2 UUIDs `fae0a703…`/`7b716123…`, `is_filler:false`), seats 2/3 fillers v2 (`79e81e5a…`/`9ed30562…`, `is_filler:true`). Flat `GET /episode-requests?round_id=` 405s (allow: POST) — verifier's route note reproduced exactly. |
| 4 | Replay valid and shows the game | TRUE | **TRUE** | Round-19 replay (1,377,672 B): `jq -e` strict-parses; `protocol` `halite/1` (matches manifest — cow detail carries `halite/1` and `manifest_hash sha256:cd52ca31…`); `results.reason "complete"`, `end_rule "full_time"`, final_turn 399; **`llm_turns [20,20,0,0]`**, `fallbacks` all-zero all seats; 40 champion `note` events, **40/40 `source:"llm"`**, latencies ~1000–1700 ms, board-specific content (e.g. seat 0: "Mine center high-value cells (9s at row 10)… Return cargo before turn 300"). Zero `403`/`PermissionDenied`/scripted notes. I also re-fetched the verifier's round-6 object (`da1179c8…`): `llm_turns [20,20,0,0]`, 0 fallbacks, 40/40 llm — byte-consistent with §4 of VERIFY.md — and round 5 (`e0528e24…`): `llm_turns [10,20,0,0]`, seat 0 `eliminated_turn 190`, 10+20 llm notes, exactly as VERIFY.md explains. **No regression at the newest round.** |
| 5 | Hosted game log clean | TRUE | **TRUE** | `GET /episode-requests/ereq_0b83b8b1…/artifacts/logs` (elevated) → 1741 B, 4 containers; grep for `falling back\|LLM provider is unavailable\|cut off at max_tokens\|rejected` → **CLEAN** (0 matches). Game container independently states `llm_turns=[20, 20, 0, 0]`, both champion seats `registered policy='llm'`, `episode settled 205.0s … (hard stop 660s)`. |
| 6 | Public page uses static replay path, featured match present | TRUE | **TRUE** | Reproduced all three of the verifier's source results: (a) raw-HTML iframe grep on `https://softmax.com/halite` → nothing (client-rendered, 731 kB shell); (b) `/coworlds` list → `featured_match:null` platform-wide; (c) SSR payload `\"playlist\":[…]` → featured match **is** present: now `halite.r19.e1`, `coworldId cow_c6743b6c…`, `coworldVersion 0.1.1`, replayUrl = round-19 replay, both matchup slots `:v2`. `POST /coworlds/replays/session` → `viewer_url` = `https://api.observatory.softmax-research.net/v2/coworlds/replays/static/cow_c6743b6c-2028-4bef-8361-f7aa7d8296a2/sha256%3Acd52ca31…/index.html?v=2#replay=<s3 url>`, `ready:true`. Static route, manifest sha, new cow id; **no `/client/replay`** anywhere. |
| 7 | Certification declared the static bundle | TRUE | **TRUE** | Committed `runs/2026-08-27-halite/release-result.json` (commit `79132de`): `.certify.replay_liveness` = `"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"`; `.version "0.1.1"`, `.ok true`, `.canonical true`, `.cow_id cow_c6743b6c…` — the 0.1.1 artifact, not the superseded 0.1.0 one. |
| 8 | Viewer executed; spectator judgment | TRUE | **TRUE** | Judged from committed artifacts (not re-dispatched, per brief). GH run `33159290682` verified: `conclusion:"success"`, `createdAt 2026-08-28T09:25:16Z`, workflow `viewer-check`. Committed `viewer-smoke.json`: `loaded:true`, `ms:2800`, signals `{"data_replay_loaded":"true","bridge":["ready"],"bridge_ready":true,"bridge_error":[]}`, `failure: null`; `.url` is byte-identical to the check-6 static route for `cow_c6743b6c…`/`sha256:cd52ca31…` with the round-6 replay. Scrub clocks **differ**: 0% `TURN 8 / 399 MINING` · 50% `TURN 200 / 399 RAIDING` · 100% `TURN 398 / 399 HAULING`. My own reconciliation of `viewer-smoke.png` against the round-6 replay I fetched: scorebug banks 299/500/169/1907 = replay `.turns[398]` banks `[299,500,169,1907]` exactly; crown on DELTA = `results.winner 3`; CHARLIE greyed, 0 ships = `eliminated_turn[2] 379`, `ships[2] 0`; feed lines `DELTA banks 4 / BRAVO banks 22 / ALPHA banks 22` = the three t=398 deposit events (seat 3→4, seat 1→22, seat 0→22); endcard chip `DELTA WINS 398/399`. Chrome is the starter family's: dark transport strip (restart/step/play/+5/loop/ffwd, `spoilers` toggle, win chip), corner scorebug plates, speed chips `1×…16×`, full-width beat-marker scrubber. Legible, advancing, and it shows the game. |

## Spectator judgment (my own, from the rendered evidence)

The frame is a real spectator product: a 21×21 dark board tiled with pale halite-crystal clusters,
four colour-coded fleets with visible shipyards and cargo pips, a centre-top clock with a phase
caption, four corner plates giving bank/afloat/ships/yards/at-risk per player with real player
names, a bank-event feed, and a transport strip with a dense event-tinted scrubber. Who is winning
and why is readable at a glance (DELTA crowned at 1907 banked; ALPHA's eliminated rival CHARLIE
greyed out). The clock moves across all three scrub samples with the phase caption changing. This
matches the coworld-ctf chrome lineage rather than a gridlock-style rewrite; the one deviation (no
momentum graph) is declared in design.md §Chrome provenance/Deviations.

## Fixer/verifier report audit

| VERIFY.md claim | I verified | agrees |
|---|---|---|
| Rounds 5+6 completed post-v2-fillers, no failed/discarded rounds | 19 completed now, 15 in scope, zero failed/discarded | ✅ (strengthened) |
| Leaderboard: both champions `:v2`, fillers absent, rp incrementing through v2 rounds | rp now 19 for both, labels `:v2`, fillers absent | ✅ |
| Round-6 ereq `ereq_385753a2…` completed, all four v2 UUIDs | re-fetched round-6 replay + UUIDs on round-19 ereq; v2 UUIDs match STATE/brief exactly | ✅ |
| Round-6 replay `llm_turns [20,20,0,0]`, 0 fallbacks, 40/40 llm notes | re-fetched `da1179c8…`: identical | ✅ |
| Round-5 replay `[10,20,0,0]`, seat 0 eliminated t=190, 30/30 llm | re-fetched `e0528e24…`: identical | ✅ |
| Hosted log CLEAN, game line corroborates llm_turns | reproduced on round 19's log | ✅ |
| SSR playlist featured match, session→static viewer_url `ready:true` | reproduced; featured match now round 19 | ✅ |
| release-result.json is the 0.1.1 artifact at commit `79132de` | `git log -1 --` confirms; fields 0.1.1/`cow_c6743b6c…` | ✅ |
| viewer-check run `33159290682` green, url byte-identical to check-6 SRC | `gh run view` → success, 09:25:16Z; `.url` in committed json matches | ✅ |
| flat `GET /episode-requests?round_id=` is 405; nested route works | reproduced (405, `allow: POST`) | ✅ |

## Refuted

None. Every VERIFY.md claim I re-fetched reproduced exactly, and several have strengthened since
(15 in-scope completed rounds vs the 2 it needed).

## Non-blocking observations

- **Round 19 outcome**: champion `daveey` scored −10 (eliminated turn 391) and the filler
  `halite-tidewalker` won the episode with 5920. The champion's decisions were 20/20 `source:"llm"`
  with 0 fallbacks — this is a game outcome, not a transport or verification defect. Fillers
  outplaying champions episode-to-episode is not scored by any DoD item (fillers stay off the
  leaderboard, verified in check 2).
- `viewer-smoke.json` `feed_lines: 0` is captured at initial paint (turn 8, pre-first-deposit); the
  rendered feed at the 100 % scrub is populated (three lines, reconciled above). VERIFY.md flags
  this correctly.
- VERIFY.md's leaderboard/featured-match rows (rank order, rp=6, `halite.r6.e1`) are stale relative
  to the current head — expected drift on a live ladder, disclosed by its own timestamps, and the
  current-head values still satisfy the checks.

## Standing blocking findings

None. All eight definition-of-done items are TRUE at the current head on my own fetched evidence.

BLOCKING: 0
