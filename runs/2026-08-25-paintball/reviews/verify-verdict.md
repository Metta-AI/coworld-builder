blocking: 0

# Phase-60 verdict — paintball (definition of done)

Head: 4a7295f (coworld-builder main) · VERIFY.md as committed in fca0692
Checklist: docs/SPEC.md §Definition of done (items 1–8), procedure prompts/60-verify.md
Independent read written before reading VERIFY.md: **yes** (all eight items were fetched/read
independently this session, 18:19Z–18:25Z, before VERIFY.md was opened; the fresh viewer-check
dispatch was also issued before reading it).

Ids: cow_09dcacad-01fb-488b-9d93-5eddf6a1a37a v0.1.3, manifest
sha256:669e79cde247aa82428d6a26c7cfeb652b3cf89f492df9ee697ca3225a123f71;
league_bd940066, div_97b4e1b9. All Observatory evidence below was re-fetched by me this session
unless explicitly marked "committed file".

## Item-by-item (independent)

### 1. ≥2 completed rounds after fillers set — PASS
`GET /rounds?league_id=…&limit=50` at 18:19Z: rounds 1–22 with **20 completed** (11 and 21
`failed`, error verbatim: "only 4/6 [resp. 5/6] planned slots produced scoring evidence; the round
requires at most 0% of planned slots failed"; round 23 pending). Fillers registered 12:48:11Z
(log.md:47, version ids b39fb2e0-… / f24ea073-…); round 1 completed 12:53:15Z. 20 ≥ 2, all after
the fillers. Failed rounds not counted.

### 2. Both champions ranked; fillers absent — PASS
`GET /divisions/div_97b4e1b9…/leaderboard` at 18:19Z (bare list):
```
1  richard   co-gas-paintball-holdline-richard:v1    1166.52  15  37
2  daveey    paintball-holdcentre:v2                 1053.12  20  25
3  daveey-1  paintball-splitpaint:v2                  957.93  20  23
4  relh      co-gas-paintball-holdline-relhalpha:v2   822.43  15   9
```
daveey and daveey-1 both ranked, rounds_played 20 ≥ 1 each. No filler row (paintball-holdline /
paintball-sprayer absent). richard/relh are external ladder players — expected per the brief.

### 3. Latest round's episode completed with a replay — PASS
Latest completed round = 22 (round_5494143d, completed 18:07:38Z). Its six episode requests are
all `completed`; `ereq_d0bfc14c-9992-4aea-aeab-27d03a34dca6` is the only pairing whose
participants are both champions, and it satisfies the check as written: `status: completed`,
`replay_url: https://softmax-public.s3.amazonaws.com/replays/035e0bfe-….replay`, participants
`daveey` (paintball-holdcentre v2, is_filler false) and `daveey-1` (paintball-splitpaint v2,
is_filler false), scores 0.529/0.471. The checklist's literal `entries[0]` (daveey-1 vs richard)
could not name both champions in a 6-episode round with externals; selecting the
champion-vs-champion request is the correct application, not a deviation of substance.

### 4. Replay bytes valid and showing the game — PASS
Fetched the S3 bytes myself (148306 bytes, magic `COWLDPNT`); ran `tools/replay_summary.py` from a
fresh clone of Metta-AI/cogame-paintball; output parses under strict `json.loads`. `protocol
paintball/v1`, `gameVersion 1`, `results.reason complete`, `endRule full_time` (design.md's
declared normal ending), `games 2`, `llmTurns [30,31]`, `fallbackTurns [10,9]`. Directive stream:
**80 directives = 61 `llm` (seat 0: 30, seat 1: 31) + 19 `fallback` + 0 `scripted`** on the
champion seats. All 61 LLM notes are non-empty and situational (hill percentages, named enemies,
cog states — e.g. "Own 76%, need 80%. Gamma closest (76px), hold hill…"); intents are the game's
own (hunt 54, paint_hill 40, hold_hill 39, paint_path 16, guard 11, fall_back 3). Hosted results
artifact re-fetched with the elevated header: **byte-identical to the replay's own result record**
(`llmTurns [30,31]`, `fallbackTurns [10,9]` confirmed).
**Adjudication (a):** SPEC item 4's bar is "non-scripted decisions with non-trivial content; not
all fallbacks". 61/80 (76%) LLM with zero scripted champion directives meets it plainly; 24%
fallbacks is a minority, and every one of the 19 traces to the platform throttle (item 5), not to
a coworld defect. PASS.

### 5. Hosted game log — PASS via SPEC item 5's exception branch
`GET …/artifacts/logs` (elevated) re-fetched; python `b'…'` reprs decoded via `ast.literal_eval`
before grepping. **39 matching lines**, my own classification (matches the verifier's exactly):
18× `llm throttled (429): "Too many tokens per day…"`, 1× `anthropic error 503: "Bedrock is unable
to process your request."`, 1× transport timeout to the sidecar's local port (its retry returned
429), 19× `falling back to holdline (throttled)`. Zero `LLM provider is unavailable`, zero
`cut off at max_tokens`, zero `rejected`, zero parse_error fallbacks.
**Adjudication (b) — my own cross-check, different coworld than the verifier used:** daycare
(`cow_5b944b41-3f2f-4f84-a96b-c484811d7d55`), episode `ereq_4c1af555-b01a-4a15-97e7-e68cc703fafe`,
completed 18:03:47Z — the same minutes as paintball's round-22 episode — shows the identical
`429 Too Many Requests` / `"Too many tokens per day, please wait before trying again."` in its
bedrock-sidecar container (36 hits) **and** `daycare llm: … falling back to scripted order` in its
game container (27 hits), same model family, same sidecar. The cause is platform-wide and now
double-documented (verifier: collab_cooking; judge: daycare). The exception branch of SPEC item 5
("or a documented platform-wide cause checked against another LLM coworld") legitimately applies.

### 6. Public page uses the static replay path — PASS
`https://softmax.com/paintball` fetched: no `<iframe` in raw HTML (client-rendered — recorded, per
the prompt, as *unknown*, not a failure). Fallback source, same as the page's own JS: SSR payload
`state.playlist[0]` = featured match `paintball.r22.e5` (coworldId cow_09dcacad, version 0.1.3,
replayUrl …/85c3c3a2-….replay, finished 18:06:38Z), and
`POST /coworlds/replays/session` → `ready: true`, `viewer_url =
…/v2/coworlds/replays/static/cow_09dcacad-01fb-488b-9d93-5eddf6a1a37a/sha256%3A669e79cde247aa82428d6a26c7cfeb652b3cf89f492df9ee697ca3225a123f71/index.html?replay=…&v=2`.
Static route, correct cow id and manifest sha, ends `/index.html?replay=<s3 url>`, no
`/client/replay` anywhere. Featured match present.

### 7. Certification declared the static bundle — PASS
Committed `runs/2026-08-25-paintball/release-result.json` (read from the working tree):
`version 0.1.3`, `ok: true`, `canonical: true`, cow id and manifest sha exactly the ones under
test, and `certify.replay_liveness` =
`"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"`.

### 8. Viewer executed, renders, advances — PASS
Two independent bodies of evidence:
- **Committed run 32875824479** (gh conclusion `success`, checked): `loaded: true`
  (`data-replay-loaded="true"`), no failure, three differing scrub clocks (1:30 T1/20 → 1:15
  T4/20 → 0:55 T8/20); the committed PNG shows a painted arena, hill, populated scorebug,
  commander banners, shout bubbles, transport strip + scrubber — the paintbot starter's chrome.
- **Adjudication (c) — the reuse question, settled empirically:** the reused run's `?replay=`
  (b1b22848, r17.e6) differs from the current featured match (85c3c3a2, r22.e5), though the
  bundle path (cow id + manifest sha) is identical. Rather than accept the equivalence argument
  on paper, I dispatched `viewer-check.yml` myself at 18:23:14Z against the **current** featured
  iframe src → run **32883445468**, conclusion `success`: `loaded: true` at 3525 ms, no failure,
  `data_replay_loaded="true"`, three differing clocks — 1:30 TURN 1/20 → 0:59 TURN 7/20 → 0:49
  TURN 10/20 — and the screenshot (committed under
  `runs/2026-08-25-paintball/viewer-check/judge-32883445468/`) shows the r22.e5 game rendered:
  red 9% / blue 71% coverage chips, the chalk hill square at centre largely blue, cogs with
  shout bubbles contesting it, tick 973/4083, the full transport strip and momentum bar. The
  verifier's reuse was sound in outcome; with the fresh run the point is moot either way.
**Spectator judgment (mine):** legible and it shows the game. Territory is readable at a glance
from the painted floor; the scorebug says who holds the hill and for how long; the commander
banners and shouts show the LLMs playing; the chrome is the starter's (transport strip, spoilers
toggle, speed ladder, two-plate scorebug, momentum bar), not a rewrite sharing ids. Not empty,
not frozen, not unreadable.

## Refuted
Nothing. Every VERIFY.md claim I re-checked reproduced exactly (see audit table). No finding in
VERIFY.md is overstated in a way that changes a verdict; its check-5 TRUE correctly claims the
exception branch and not the zero-lines branch.

## Verifier report audit
| claim | VERIFY.md said | I verified | agrees |
|---|---|---|---|
| completed rounds | 20 of 22, fillers 12:48:11Z | 20 completed live at 18:19Z, log.md:47 | yes |
| leaderboard | daveey 2 / daveey-1 3, 20 rounds, fillers absent | identical rows live | yes |
| ereq_d0bfc14c | completed, replay 035e0bfe, champions both seats | identical live | yes |
| replay | strict JSON via replay_summary.py, paintball/v1, complete/full_time, 61 llm / 19 fallback / 0 scripted | reproduced from S3 bytes + fresh clone | yes |
| results artifact ≡ replay result record | identical | re-fetched hosted artifact, Python `==` True, llmTurns [30,31] fallbackTurns [10,9] | yes |
| log 39 lines, all throttle | 18×429 + 1×503 + 1×timeout + 19 fallback | my decode/classification identical | yes |
| platform-wide cross-check | collab_cooking 18:02:40Z, same 429 | independently confirmed via **daycare** 18:03:47Z | yes |
| featured match static path | r22.e5, ready:true, static/cow/sha | identical session response at 18:22Z | yes |
| release-result.json | replay_liveness "skipped (static replay bundle declared…" | committed file, same string, 0.1.3/ok/canonical | yes |
| viewer run 32875824479 | success, loaded:true, 3 differing clocks | gh conclusion success; committed json/png re-read | yes |
| bundle-reuse argument | same cow/sha ⇒ same bytes, re-dispatch unnecessary | fresh run 32883445468 against current featured src also passes | yes (empirically) |

## Advisory (non-blocking)
1. **Momentum-bar caption still reads `LIVES LEAD`** (visible in both screenshots); design §Viewer
   6 retargets the series to the hill-tick difference — the series is retargeted, the caption is
   not. Cosmetic legibility item for a later pass.
2. **Scrub convergence lags the click**: the 100% readout lands mid-game-1 (turn 8/20 and 10/20 in
   the two runs, ticks 847/4614 and 973/4083) — bounded seek re-sim still converging when sampled
   700 ms later. Motion is proven (the three readouts differ); a spectator seeking to the end
   waits seconds rather than jumping.
3. **`feed_lines: 0` is a smoke-script selector mismatch** (`#feed,.feed,#log` vs paintball's
   `#killfeed`/`#bannerlane`); both screenshots show populated feed/banner rows. A false zero in
   the readout, not an empty feed.
4. **STATE.json labels the fillers `paintball-holdline:v2`/`paintball-sprayer:v2` while the
   registered filler policy versions are v1** (`filler_version_ids` b39fb2e0/f24ea073 = the v1
   registrations; log.md:88 "fillers still v1 … leaving as-is"). No DoD item touches filler
   versions beyond leaderboard absence (met), but the STATE labels are stale.
5. `finalTick 4924` exceeds the nominal 2×2160=4320 play ticks (lobby/game-over frames included in
   the tick counter); consistent across replays (r22.e5 shows 4083 total in the transport). No
   checklist impact.

## Result
All eight SPEC §Definition of done items PASS on evidence I fetched or read myself this session.
The verifier's VERIFY.md is accurate; its two documented exceptions (committed release artifact
for check 7, reused viewer run for check 8) are legitimate, and the check-8 reuse is now also
proven equivalent by a fresh green run against the current featured match.

BLOCKING: 0
