blocking: 0

# phase-60 verdict — derks-gym (attempt 2)

Judged: 2026-08-28. Evidence file: `runs/2026-08-28-derks-gym/VERIFY.md` (attempt 2, 15:07–15:27Z).
Checklist: `docs/SPEC.md` §Definition of done, operationalised by `prompts/60-verify.md`.
Independent read: I read SPEC and the phase prompt, then VERIFY.md and the committed
`viewer-check/` artifacts, then re-fetched the evidence myself before ruling. No fixer
self-report exists in phase 60; nothing was read out of order.

Ids adjudicated: coworld `derks-gym` 0.1.3, `cow_03c45b25-de4b-42e1-8e2f-056a496878c4`,
league `league_44e55a9f-aa40-4523-9ed0-7f86ccc73d08`, division
`div_1bc6a659-31e8-40fe-a99b-726c82426998`, v4-era rounds 10 and 11 only (rounds 2–9 ran the
pre-fix v1 policies on 0.1.0 and are correctly excluded — counting them would re-measure the
bug attempt 1 caught).

## Spot-checks I ran (fresh fetches, not re-reads)

| what | result | agrees with VERIFY.md |
|---|---|---|
| `GET /rounds?league_id=$L&limit=20` | rounds 10, 11 `completed`, `error: null`, both with `entrant_policy_version_ids` = [`e06340fb…`, `c95d1a91…`] (the v4 champions); rounds 2–9 completed on the v1 pvs; round 1 failed (pre-filler race); a new round 12 `pending` (post-VERIFY, no contradiction) | yes |
| `GET /divisions/$D/leaderboard` | bare array, exactly 2 rows: rank 1 `daveey` `derk-drafter-v1:v4`, rank 2 `daveey-1` `derk-metagamer-v1:v4`, both `rounds_played: 10`; no filler rows | yes |
| committed `release-result.json` `.certify.replay_liveness` | `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)`; `{ok:true, version:"0.1.3", canonical:true, secret_put:true, cow_id:"cow_03c45b25-…", manifest_sha:"sha256:b5e7d192…"}` | yes |
| round-11 replay bytes (S3, `4af31312-…replay`) | sha256 `46f6932b0440…a50ffa5` (identical); magic `DERK`, version 2, header_len 16820, strict UTF-8 JSON header parse ok, body 150240 == 2504×60; `end_reason: ancient`, `winner: 0`, `ancient_healths: [4500.0, 0.0]`, `draft_fallbacks` all false | yes |
| champion draft records (parsed from the bytes myself) | pid 0 `daveey` support `arm_needler/tail_rotor/misc_battery`, `decision_ms: 2903`, note "Fast support: mobility + mana for hook/heal/stun spam. …", `fallback: false`; pid 1 `daveey-1` assassin `arm_needler/tail_stinger/misc_regen`, `decision_ms: 2390`, note "Counter flat-damage bursters; scale via hp_gain + damage_gain …", `fallback: false` | yes — verbatim |
| hosted log (round-11 ereq, elevated) | HTTP 200, 2059 bytes, zero matches for the four failure patterns; game container's own `draft Cog-Alpha … [none, 2903ms]` / `draft Cog-Bravo … [none, 2390ms]` lines corroborate the replay's decision_ms | yes |
| `GET /coworlds` canonical flags | `canonical: true` only on 0.1.3/`cow_03c45b25-…`; 0.1.0–0.1.2 false | yes |
| viewer-check run 33184965298 | `gh run view`: `conclusion: success`, created 2026-08-28T15:24:14Z (1 s after the logged dispatch) — checked, not accepted | yes |
| `viewer-smoke.png` (viewed) | legible frame: draft-reveal overlay "Draft reveal (closes in 4s)", Radiant card `Cog-Alpha daveey support` / `Needler · Rotor Tail · Mana Battery` with the applied-stat lines, `Cog-Delta Baseline (2) support` opposite, dimmed scorebug/clock band above, populated canvas behind (heroes with health/mana bars, `Level: 1` labels, tower vision outlines, HUD, `19 FPS`) | yes — the judgment paragraph describes what the png actually shows |
| observation-3 claims (from the bytes) | `first_blood` = `{tick:246, pid:0, victim_pid:0}` (pid==victim); kill-event victims = {2,3,4,5,6,7,8} while `agent_stats` gives pid 0 `deaths: 2`, pid 1 `deaths: 3` — no kill event names 0 or 1 as victim | yes — accurately reported |

No re-fetch contradicted VERIFY.md on any point.

## The eight checks

### 1. ≥2 completed rounds after fillers set — TRUE
Re-fetched: rounds 10 and 11 `completed` with the v4 champion pvs in `entrant_attributions`.
The "after fillers" ordering is proven the strong way — both counted rounds *seated* the v4
fillers (`is_filler: true` at positions 2–5 in both episode requests, `result.names` reading
`Baseline`/`Baseline (2–4)`) — not by clock comparison. Excluding v1-era rounds 2–9 is correct:
they measure the pre-fix coworld.

### 2. Both champions ranked, fillers absent — TRUE
Re-fetched. `daveey` and `daveey-1` present at v4 labels, `rounds_played 10 ≥ 1`; fillers
absent entirely (the permitted branch). Both at MMR 1000 / 0 wins is explained by the mirror
seating (both champions on the winning radiant team), consistent with `participant_scores`.

### 3. Latest round's episode request — TRUE
VERIFY's inline fetch shows `status: "completed"`, non-null `replay_url` (which I fetched and
hash-matched), `daveey` and `daveey-1` at positions 0–1 `is_filler: false` on the new
`cow_03c45b25-…`. Documented deviation: the API names filler seats by real policy name +
`is_filler: true`; the `Baseline (N)` labels appear game-side in `result.names` and the
rendered viewer. The requirement's substance — participants named correctly, champions
identifiable, fillers distinguished — is met. The dead flat route
(`/episode-requests?round_id=` → 405) was replaced by the nested route per the playbook; the
verifier proved the 405 rather than asserting it.

### 4. Replay bytes valid and show the game — TRUE
I re-parsed the bytes myself. Documented deviation: the replay is the coworld's declared
binary format (magic `DERK`, v2, u32le header_len, UTF-8 JSON header — matching the repo's
`replay.py` ground truth), so the strict parse applies to the JSON header; it parses under
`errors="strict"`. The manifest declares no flat `protocol` string; the header's `result`
conforms to the manifest's `results_schema` exactly (all 16 required keys, no extras).
`end_reason: "ancient"` is the clean outcome, no deadline exception needed. The attempt-1
failure is genuinely resolved, on four independent legs I verified: champion `decision_ms`
2390–3577 ms across both rounds vs 0–1 ms for fillers in the same episodes; non-empty notes
that differ between rounds for the same policy; picks differing from the scripted role table
that the fillers reproduce exactly side-by-side; `fallback: false` / `draft_fallbacks` all
false (0 of 6). Events (61) show kills, towers, level spikes, the new `ancient` event, and
champion activity (pid 1: a kill, a tower, level 6; pid 0: support stats with 2129 healing).

### 5. Hosted game log clean — TRUE
Re-fetched round 11's artifact: zero matches for the four patterns; bedrock-sidecar started
cleanly; all six seats connected at tick 0 and the episode completed. Player-pod logs are not
exposed by any Observatory route (the verifier probed five shapes and recorded the 404/400/
byte-identical results) — that is a platform observability gap, not a failure of this check,
whose requirement is the *hosted game log* being clean. The game container's own draft lines
independently carry the fallback/latency evidence.

### 6. Public page uses the static replay path — TRUE
The raw-HTML grep found no iframe (client-rendered page — the prompt's anticipated case), and
the verifier used the documented fallbacks: the page's SSR payload (featured match present,
round 11, 0.1.3, both champions in the matchup) and the replay-session endpoint, whose
`viewer_url` is `/v2/coworlds/replays/static/cow_03c45b25-…/sha256%3Ab5e7d192…/index.html`
with the replay as a fragment — the static route, no `/client/replay` anywhere (0 occurrences
in 738 KB of page bytes). I re-verified `canonical: true` sits on exactly that cow_id. The
same URL is the one viewer-check actually rendered, which is end-to-end proof the route
serves.

### 7. Certification declared the static bundle — TRUE
Spot-checked the committed `release-result.json` myself: the required string is present
verbatim, and the file's `cow_id`/`manifest_sha`/`version` tie it to this release, not
attempt 1's. All 10 cert steps `[pass]`.

### 8. Viewer executed + spectator judgment — TRUE
Run 33184965298: `conclusion: success` (verified via `gh run view`). `loaded: true` via
`data_replay_loaded: "true"` in 2041 ms, `failure: null`. The three scrub readouts differ
(tick 0 → 6 → 11 against denominator 2504 == the replay's tick_count), which rules out the
frozen-frame failure mode as the check defines it. The png (which I viewed) is legible and
plainly shows this game: the draft overlay renders `draft[0]`'s picks, applied stats, and the
LLM's own note text verbatim from the replay header; the canvas behind is populated and
consistent with tick ~13 (all `Level: 1`, 0 towers 0 kills — first tower is at tick 882).
Chrome provenance holds: all 13 starter ids present in the served shell, additions all
`derk-`-prefixed — the starter's viewer extended, not a rewrite. The verifier's caveat that
the readouts advance by playback rather than by seeking is honestly declared; the check's
requirement as written (three differing readouts) is met, and motion is additionally
corroborated by the in-canvas FPS counter and the screenshot's tick 13 sitting after the
100 % readout's tick 11.

## The three observations — blocking rulings

1. **`#seek` reports but does not jump** — NOT BLOCKING. The definition of done requires the
   viewer to load, render, and advance, proven by three differing clock readouts; all hold.
   A scrubber that plays but does not jump degrades spectator *control*, not legibility or
   motion; the spectator experience the checklist names (loads, renders, advances, legible)
   is intact. Correctly routed as a phase-30-style quality finding for the coordinator.
2. **WebGL `vertexAttrib*: index out of range` warnings (30, then capped)** — NOT BLOCKING.
   The frame demonstrably renders (19 FPS in-canvas, correct content, `failure: null`); the
   warnings are console noise from the emscripten/raylib build on this driver. A latent
   portability risk worth a repo issue, but no checklist item is violated.
3. **`first_blood` pid==victim_pid; unattributed deaths emit no kill events** — NOT BLOCKING,
   verified in the bytes (round 11: `{tick:246, pid:0, victim_pid:0}`; pids 0/1 have 2/3
   deaths with no kill event naming them as victim). This is a feed-quality defect: one event
   kind misattributes its subject and non-hero deaths are silent, so the feed undercounts.
   It does not make the viewer illegible, does not stop the game being shown, and does not
   touch check 4's requirement (champion seats doing the thing the game is about — which the
   kill/tower/level events that *are* attributed demonstrate). The DoD nowhere requires every
   event kind to be correctly attributed; this is a fix-forward quality item, and it should
   be fixed — the feed is a spectator surface and first blood is a marquee moment — but on
   the checklist as written it does not block.

## Verdict

All eight checks TRUE. Zero blocking items. The attempt-1 → attempt-2 methodology is sound:
the failures were fixed in 0.1.3/v4, the league reseated, and re-verification was confined to
post-fix rounds with the pre-fix era explicitly excluded and evidenced. Every spot-check I
ran independently reproduced the verifier's evidence.

BLOCKING: 0
