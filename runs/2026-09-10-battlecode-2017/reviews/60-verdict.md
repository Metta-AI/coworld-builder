blocking: 0

# Phase-60 verdict — battlecode-2017 (bc17)

Adjudicated: `runs/2026-09-10-battlecode-2017/VERIFY.md` (8/8 TRUE claimed) against
`docs/SPEC.md` §Definition of done (phase 60) items 1–8, with `prompts/60-verify.md` as the
command-level standard. **Independent read written before reading VERIFY.md: yes** — every
Observatory fetch below was re-run by me at 2026-09-11T09:11–09:20Z, the PNG was opened and read
by me, the shipped viewer bundle's source was fetched and read by me, and only then was
VERIFY.md read. Judged at the current state of the world, not at the state the verifier saw.

Ids: `L=league_848b5159-1986-4442-ac18-575ef5c6c7c6`, `D=div_943b6ac3-c635-4473-9224-1363214931c9`,
`COW=cow_7c4f0e60-3dd5-4de2-ba2c-441dad1b4de2` (battlecode 0.11.2,
manifest `sha256:4d5c5bce…a492fd5`).

State change since VERIFY.md was written, noted up front: **0.11.2 is no longer the canonical
`battlecode` row** — 0.11.6 (`cow_d8457b5a…`) became canonical at `2026-09-11T09:08:29Z`, minutes
after the verifier's fetches (09:01–09:05Z). This invalidates nothing below: every item was
re-verified by me after that change, and the bc17 page's featured match still resolves to the
0.11.2 static bundle (my own SSR-payload and session-endpoint fetches, item 6).

---

## Item-by-item

### 1. ≥2 completed rounds after fillers were set — **UPHELD (TRUE)**
Re-fetched: `GET /rounds?league_id=$L&limit=50` → exactly 2 rounds, both `status=completed`,
both `error: null`: round 1 `round_4c4f8ffa` (created `08:50:10.183612Z`) and round 2
`round_ae081c35` (created `08:56:54Z`, completed `09:00:09.706399Z`). No failed/discarded rounds
exist in this league. Filler registration time (`08:50:00Z`, `POST /leagues/$L/filler-policies
200`) is taken from `log.md` line 125 — the source the checklist itself names ("`log.md` records
it") — and precedes round 1's creation by 10 s. Both rounds' `entrant_attributions` carry the two
champions' policy-version UUIDs (`77b3fb34…`, `db6f8128…`), re-fetched from `GET /rounds/<id>`.

### 2. Both champions ranked — **UPHELD (TRUE)**
Re-fetched: `GET /divisions/$D/leaderboard` (bare array) → exactly two rows:
rank 1 `daveey` / `battlecode-bc17-orchard:v4` score 1001.4695, `rounds_played=2`,
`episode_wins=1.0`; rank 2 `daveey-1` / `battlecode-bc17-tankrush:v4` score 998.5305,
`rounds_played=2`, `episode_wins=1.0`. Neither filler appears — "fillers absent" satisfied.

### 3. Latest round's episode request completed with a replay — **UPHELD (TRUE)**
Re-fetched. Note: the flat `GET /episode-requests?round_id=…` returns
`{"detail":"Method Not Allowed"}` for me too (three approaches tried; VERIFY.md recorded the
same 405 and the same fallback). The nested route works:
`GET /rounds/round_ae081c35…/episode-requests` → one entry,
`ereq_867fbc51-51c9-4b4e-8019-ae42caa30ded`, `status=completed`, `replay_url`
`https://softmax-public.s3.amazonaws.com/replays/87fbd671-026a-409a-b70d-1ece9759be4d.replay`.
Detail fetch: participants are `daveey` (battlecode-bc17-orchard v4) and `daveey-1`
(battlecode-bc17-tankrush v4), both `is_filler: false`; `participant_scores` `[464.0, 235.0]`;
`coworld_id = COW`, `coworld_version = 0.11.2`.

### 4. Replay bytes valid, protocol matches, shows the game — **UPHELD (TRUE)**
Re-fetched the S3 bytes (181,091 bytes) and parsed with Python's strict `json.load` — valid
UTF-8 JSON. `protocol: "cogame.battlecode.v1"` matches the design note's pinned protocol id
(`design.md:1447`, and the replay-shape example at `design.md:1621`). `result.reason:
"complete"`. `result.fallbacks: [0, 0]` — zero fallbacks; both seats' doctrines are real LLM
sheets (`doctrine_received` slot 0 attempt 1 at 19,999 ms; slot 1 attempt 2 at 7,601 ms after
one timeout retry) with distinct, non-trivial content (orchard: `tree_farm` opening, 5 gardeners,
hex farms, donate-when-ahead; tankrush: `tank_rush`, 70 soldier_tank_ratio, never-donate,
annihilation play). 194 events of real bc17 gameplay (`shake`×40, `tree_planted`×36, `strike`×23,
`donation`×22, …), three games on three maps ending `victory_points_reached` /
`more_victory_points` / `victory_points_reached` — the thing this game is about. The prompt's
literal `type=="decision"` query returns 0 because this replay uses `kind`-keyed events; the
verifier's substitution of the game's real schema is correct and matches the sibling-year
precedent.

### 5. Hosted game log clean — **UPHELD (TRUE)**
Re-fetched `GET /episode-requests/ereq_867fbc51…/artifacts/logs` with the elevated header
(HTTP 200, 2,163 bytes, 11 lines). My own grep for
`falling back|LLM provider is unavailable|cut off at max_tokens|rejected` → zero matches, CLEAN.
The seat-1 "attempt 1 failed, will retry" line is a retry that succeeded (reconciles with the
replay's `doctrine_received slot=1 attempt=2`), not a fallback.

### 6. Public page uses the static replay path — **UPHELD (TRUE)**
Re-fetched `https://softmax.com/battlecode/bc17` (HTTP 200, ~1.09 MB). Raw-HTML iframe grep is
empty (client-rendered, as the playbook documents platform-wide); the SSR payload's
`state.playlist[0]` — which I extracted from the page bytes myself — is this run's own round-2
episode (`episodeId b0ec5f4f…`, `coworldId = COW`, `coworldVersion 0.11.2`, `replayUrl`
byte-identical to item 3's). Featured match present. I then re-ran the session call the page's
JS makes (`POST /coworlds/replays/session` with that cow_id and replay URL) →
`ready: true`, `viewer_url` =
`…/v2/coworlds/replays/static/cow_7c4f0e60…/sha256%3A4d5c5bce…/index.html?v=2#replay=<s3 url>` —
the static route in its documented fragment form, `<sha>` = the coworld's `manifest_hash` =
`STATE.coworld.manifest_sha`. Not a `/client/replay` pod URL.

### 7. Certification declared the static bundle — **UPHELD (TRUE)** (see Question 2)
Read from the committed `runs/2026-09-10-battlecode-2017/release-result.json`:
`certify.replay_liveness` = `Replay liveness: skipped (static replay bundle declared;
/client/replay and /replay not required)` — the required string, from the required file. I
additionally re-downloaded release run `34565644691`'s `release-result` artifact from
`Metta-AI/cogame-battlecode` myself and diffed: **byte-identical to the committed copy.** The
artifact reads `ok: true`, `version: 0.11.2`, `cow_id = COW`, `canonical: true` (true at
publication), `manifest_sha` matching STATE and the live static route, `step_failed: null`, and
lists this run's four policies at v4.

### 8(a). `loaded: true` — **UPHELD (TRUE)**
From the committed `viewer-check/viewer-smoke.json`, read myself: `loaded: true`, `ms: 986`,
`signals.data_replay_loaded: "true"`, `bridge: ["ready"]`, `bridge_ready: true`,
`data_replay_error: null`, `failure: null`. CI fact-checked, not accepted: run `34582367441` in
`Metta-AI/coworld-builder`, workflow `viewer-check`, created `2026-09-11T09:04:52Z`,
`conclusion: success`. The URL in the json is exactly item 6's resolved iframe `src`.

### 8(b). The replay advances — **UPHELD (TRUE)**
The three scrub readouts in the committed json differ pairwise:
0 % `5:05 GAME 1 OF 3 — BLITZKRIEG`, 50 % `2:32 GAME 2 OF 3 — ALIGNED` (settle 2011 ms),
100 % `0:00 GAME 3 OF 3 — BARRIER` (settle 1004 ms) — and each map matches
`result.games[0..2].map` in the replay I fetched. Attempt 1's identical-0 %/50 % flake was
disclosed by the verifier, superseded by a differently-parameterised attempt 2, and the
committed evidence is attempt 2's; that is the retry discipline the prompt prescribes.

### 8(c). Spectator judgment — legible, shows the game — **UPHELD (TRUE), on corrected grounds** (see Question 1)
I opened `viewer-smoke.png` myself. It is legible and unambiguously bc17: winner card
"CLAN ASH — DAVEEY", "THE GAME ENDED ON VICTORY POINTS REACHED IN GAME 3, ROUND 1320",
"score 464 — 235 · 3 games played · 1320 rounds in the last one"; two plain-word doctrine panels
whose every clause I reconciled against the replay's `seats[].sheet` knobs (5 vs 2 gardeners,
hex vs ring farms, 20 % vs 70 % tanks, donate-when-ahead vs never, reserve 200 vs 100, defend
radius 14 both); per-side Fund stats (Clan Ash "1000 victory points for 11973.0 bullets
(11.9 a point)" — matches game 3 `victory_points [1000, 0]`; Clan Basil 0 VP — matches its
`vp_donate_policy: "never"`); the four-rung round-3000 tiebreak ledger; a killfeed whose visible
beats match the replay's donation/`unit_milestone` events at rounds 1105/1158/1212/1251/1263/1320
line by line; and the starter's transport strip, speed chips, spoilers toggle,
"round 1320 / 2999" readout and scrubber — the starter's chrome, not a rewrite. Year nouns are
bc17's (gardeners, lumberjacks, bullets, victory points, bullet trees); no foreign-year noun
appears. The 87/12-vs-464–235 question is ruled on below and does not falsify this item.

---

## Question 1 — the scorebug's FINAL 87–12 vs the endcard's 464–235

**Ruling: item 8(c) stands. The scorebug does not lie — but the verifier's "tween-timing capture
artifact" explanation is wrong, and I correct it on the record.**

What I fetched to settle it:

1. **The replay.** `result.points = [[35, 70, 87], [64, 29, 12]]` — per-game points, each pair
   summing to ~99–100 (the design's per-game scoring split: weights
   `victory_points_share: 64 + bullet_trees_share: 24 + bullet_worth_share: 12 = 100`, truncated
   to integers — design.md §scoring, line ~1528). The final `game_end` event for game 3 records
   **`"points": [87, 12]`** verbatim. `result.scores = [464.0, 235.0]` is a different quantity —
   the match score (per-game points plus the `win_bonus_per_game: 200` structure), and it equals
   the API's `participant_scores` exactly.
2. **The shipped bundle's source** (fetched from the live 0.11.2 static URL). `renderScorebug`
   sets the plate number by direct assignment —
   `$('pl-pts-' + slot).textContent = (s.points && s.points[slot]) || 0;` — **there is no tween,
   no animation, no interpolation** on that element. What it displays is the sim state's live
   per-game points, which the design pins as the scorebug's content ("the live points number",
   design.md:1939).
3. **The load-time readout** (`scorebug: "CLAN ASH daveey 50 … daveey-1 50"`) reconciles: the
   100-point split meter starts at 50/50 at game 1, round 0.

So 87–12 is neither a mid-animation value nor a wrong value: it is the **exact, settled final
value of game 3's points meter** — the quantity that element always shows — and the endcard's
"score 464 — 235" is the match total, also exactly correct. Two different, individually true
readouts. A scorebug that shows the truth of what it is designed to show does not "genuinely lie
to spectators"; the frame is legible and it shows the game. The verifier's honest-but-mistaken
diagnosis ("the tween had not settled at the instant of capture") does not change the verdict,
because the item's evidence — the rendered frame reconciled against the replay — passes on the
correct reading too.

**Non-blocking observation** (no checklist item names it): at FINAL the scorebug's center caption
reads "FINAL / MATCH OVER" while the plate numbers remain game-3 points, with no on-screen label
distinguishing "game points" from "match score" one panel above "score 464 — 235". A one-word
label (e.g. "G3 87–12") would remove the double-take. Cosmetic; a phase-30-style legibility nit
for any future round, not a defect in the certified evidence.

## Question 2 — item 7 satisfied by an adopted artifact from another run's dispatch

**Ruling: item 7 stands. The adoption is sound and the artifact certifies the very coworld this
league runs.**

The letter of item 7 asks for one string in one committed file, and it is there. The substance I
verified independently, not from `release-adopted.md`'s say-so:

- **The artifact is genuine and unmodified:** I re-downloaded run `34565644691`'s
  `release-result` artifact from `Metta-AI/cogame-battlecode` and it is byte-identical to the
  committed `release-result.json`. The run itself: workflow "Coworld release",
  `conclusion: success`, created `2026-09-11T05:21:26Z`, `headSha 526befdb…` — all fetched from
  the GitHub API by me.
- **The sha contained this run's work:** PR #18 ("bc17: the tenth year module") merged
  `2026-09-10T22:17:02Z` as `07ad48cc`; PR #22 ("bc17 r1 fixes: F1-F15") merged
  `2026-09-11T03:10:21Z` **as `526befdb` itself** — the exact sha run 34565644691 built. Both
  fetched from the GitHub API. So 0.11.2 embodies the complete bc17 module plus every round-1
  fix.
- **The coworld it certifies is the coworld the league plays:** the artifact's
  `cow_id = cow_7c4f0e60…` = the `coworld_id` on this league's round-2 episode request
  (re-fetched, item 3), `coworld_version 0.11.2`, and the same `manifest_sha` appears in the live
  static viewer URL (re-fetched, item 6). Not a different coworld — the blocking condition in my
  brief does not fire.
- **The three failed own-dispatches are what the note says:** `release-result-0.11.5-FAILED.json`
  reads `ok: false`, `step_failed: "Upload the Coworld"`, `certify.ok: true`, with the correct
  `replay_liveness` string — certification passed, hosted smoke did not; the stranded
  0.11.3/0.11.4/0.11.5 rows are present with `canonical: false` in my own `/coworlds` fetch,
  undeleted.

The MOD-run structure ("one coworld, shared version line, ten year runs") makes the sibling's
dispatch a release *of this run's code*. An item-7 reading that demanded a dispatch by this run's
own workflow-run id would elevate provenance ceremony over the thing certified; the SPEC's words
("phase 40's artifact copy") are satisfied — phase 40's decision *was* the adoption, its artifact
is this file, and the certification in it is true of the running coworld. Not blocking.

## The PR #23 residue (`#bc17-doctrines-toggle`)

**Real, precisely as recorded, and not blocking; it does not bear on item 8.** I verified it at
the source level: the live 0.11.2 bundle (fetched from the static URL) contains the chip's CSS
and its JS wiring but **not** the `<button id="bc17-doctrines-toggle">` element — that element
was added by PR #23 (merged `2d61d796`, 07:08:58Z, after 0.11.2's sha), so `$( 'bc17-doctrines-toggle')`
is null and a spectator who dismisses the live doctrine panel cannot re-open it. Item 8's three
sub-conditions (load, advance, legible-and-shows-the-game) are all evidenced without that chip —
the smoke's doctrine content is rendered inside the endcard, visible in the PNG. Self-healing as
recorded: PR #23 is on `main`, and canonical has in fact already moved to 0.11.6
(09:08:29Z) — though note the bc17 page's featured match still serves the 0.11.2 bundle until a
newer episode is featured, so the interaction gap persists for this featured replay meanwhile.
Recorded residue, named in `release-adopted.md` and in VERIFY.md; no definition-of-done item
covers it; not blocking.

## What I relied on VERIFY.md for, versus re-fetched

Re-fetched or re-read from primary sources by me: items 1–7 in full (rounds, leaderboard,
episode request + detail, replay bytes, hosted logs, page SSR payload, session endpoint,
committed and re-downloaded release artifacts, GitHub run/PR metadata), item 8's committed
evidence files, the PNG, the CI run's conclusion, the live bundle source, and design.md's pinned
protocol/scoring/scorebug sections. Relied on VERIFY.md (plus log.md) only for: attempt 1's
existence and readouts (run `34582261232`, superseded, its artifact uncommitted by design) and
the verifier's account of its own decoding steps for the log bytes — neither load-bearing, since
the committed attempt-2 evidence and my own raw-log grep carry the items.

## Overturned items

None. All eight items (with 8 split a/b/c) are UPHELD. One explanation corrected (Question 1);
no verdict changed.

## Blocking findings

None.

BLOCKING: 0
