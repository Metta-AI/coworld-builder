blocking: 0

# verify verdict — crafter (phase 60)
Run: 2026-08-28-crafter   COW: cow_88aa79dd-1661-4c42-9024-abb912d2de34   Version: 0.1.0
Checklist: docs/SPEC.md §Definition of done, as prompts/60-verify.md's eight checks
Independent read written before adjudicating VERIFY.md's dispositions: yes — I read the
checklist, the design note's §End conditions, §Readouts and §Replay bytes, and the committed
viewer-check artifacts (viewer-smoke.json, viewer-smoke.png) and formed my read of the
screenshot before weighing the verifier's §8 judgment. I then re-fetched the live evidence
myself rather than accepting the pasted transcripts.

## Standing blocking findings

None. All eight definition-of-done items are proven with fetched evidence, either inline in
VERIFY.md and reproduced by me, or adjudicated below (check 6).

## Checklist pass (independent)

| item | status | evidence |
|---|---|---|
| 1. ≥2 completed rounds after fillers | TRUE | Re-fetched live: 3 completed rounds (04:04:27Z, 04:19:34Z, 04:35:05Z), all `error: null`, zero failed/discarded. log.md shows fillers registered (forager 72a75938, wanderer 6f66cf9c) in the same 04:04:09Z block as, and before, "unpaused; trigger-round accepted; round 1 pending" — both counted rounds postdate the fillers. |
| 2. Both champions ranked, fillers absent | TRUE | Re-fetched live: leaderboard now has 3 rows — a third-party player `richard` joined at rank 1 since VERIFY was written; `daveey` (crafter-techtree:v1, rounds_played 3) and `daveey-1` (crafter-homesteader:v1, rounds_played 3) both ranked; fillers crafter-forager/wanderer absent. A non-filler third player is not forbidden by the item. |
| 3. Latest round's episode request completed with replay | TRUE | VERIFY §3: both round-2 ereqs (`ereq_067f4396…`, `ereq_2cd155c7…`) `status: completed`, non-null S3 `replay_url`s, participants daveey-1 and daveey, `is_filler: false`. Single-seat caveat is sound: num_agents=1 means one participant per ereq; the verifier proved "participants named correctly" across the round's two ereqs, which is the item's intent. |
| 4. Replay bytes valid, show the game | TRUE | Reproduced myself: fetched the round-2 homesteader replay (86471 bytes, magic `COWLDCRF`), ran the repo's `tools/replay_summary.py` — strict UTF-8 JSON ok, `protocol crafter/v1`, `reason complete`, `endRule death` (a death is `complete` per design.md:507-510), 19/19 turns `source: llm`, `fallbacks 0`. Techtree episode: 15/15 llm, 0 fallbacks, verbs incl. goto/place_table/make_wood_pickaxe. 34/34 champion decisions LLM-sourced with substantive `say` reasoning — "doing the thing the game is about". The binary container is not a deviation the verifier invented: design.md:1354-1378 declares it and the phase-60 substitute explicitly. |
| 5. Hosted log clean | TRUE | VERIFY §5 pastes both round-2 game logs in full: zero matches for the four patterns, CLEAN on both; 15+19 upstream `200 OK` lines equal the llmTurns counts. No capacity exception was needed. |
| 6. Featured match + static iframe src | TRUE (adjudicated, below) | Static route proven; playlist=[] adjudicated as the platform's single-seat property per the shipped procgen precedent. |
| 7. Certification declared static bundle | TRUE | Read the committed `runs/2026-08-28-crafter/release-result.json` myself: `certify.replay_liveness` = "Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)", `certify.ok: true`, 10/10 transcript steps passed. |
| 8. Viewer executed and judged | TRUE | CI run 33233844065 re-checked via gh: workflow viewer-check, completed/success, created 04:27:03Z (2 s after the dispatch stamp). Committed viewer-smoke.json: `loaded: true` (3410 ms), `data_replay_loaded: "true"`, `failure: null`, three scrub clocks all differ (DAY 1/tick 0/HP 9/score 0 → DAY 2/221/9/10221 → DAY 3/440/0/20440). Judgment below. |

## Check 6 adjudication — SATISFIED

Two sub-clauses:

**6a (static route): proven.** The page is client-rendered (raw HTML has no iframe — I
re-fetched and confirmed), so the playbook fallback applies. The session API returns
`viewer_url = …/v2/coworlds/replays/static/cow_88aa79dd-1661-4c42-9024-abb912d2de34/sha256%3A6b9fed…/index.html?v=2#replay=<s3 url>`,
`ready: true` — the static route with the correct cow_id and manifest sha, no `/client/replay`
anywhere. And it is not a paper URL: check 8 opened exactly that string in headless chromium
and it drew the game.

**6b (featured match present): satisfied on the shipped precedent, not on the letter of
`state.playlist`.** I re-fetched `softmax.com/crafter` live: `"playlist":[]` and the round
replays present in `state.pool.replays` — the identical shape the closed, shipped run
2026-08-28-procgen presented, whose VERIFY (lines ~410-466) judged check 6 TRUE with
playlist=[] and the featured pool at `state.pool.replays[0]`, `featured_match` null
platform-wide. The prompt's own explanation for absence ("fewer than two ranked players") is
disproven — crafter has two champions ranked (three players now). The verifier's live
cross-check establishes the real mechanism: the SSR playlist builder emits an entry only for
episodes carrying a `matchup{first,second}`, which a single-policy-per-episode coworld can
structurally never produce (nethack and procgen, both canonical single-seat, show the same
empty playlist; minigrid/atari-57/bullwhip, multi-seat, show non-empty ones). A spectator
landing on the page gets the round replays from the pool, exactly as on the shipped
single-seat coworlds. Holding crafter to a bar no single-seat coworld on the platform can meet,
and that the shipped precedent was not held to, would be a false blocking finding. Counted 0.

## Check 8 spectator judgment (my own, from the png)

The screenshot is the 100 %-scrub frame — it reconciles exactly: scorebug `2/22 Carrying ·
HOMESTEADER`, clock `DAY 3 · DAY`, `HP 0 · SCORE 20440`, transport counter `440 / 441` =
`finalTick: 440`, and the two lit checklist rows (`5 DRINK yes 194 1`, `16 WAKE UP RESTED yes
354 1`) match `achievementTick` 194/354 in the replay results. What it shows is the game: real
tiled terrain (water/grass/sand) under fog with the explored patch bright, the red cog at the
moat base the say-lines describe, the 64×64 minimap with viewport box and `15 CELLS` zoom, the
9×9 agent inset (`ALPHA · FACING …`), the momentum band's step line rising at the two
achievement ticks, and the starter's transport strip verbatim (restart/step/play/+5s/loop/
skip/spoilers, tick counter, 1×–32× speed chips, scrubber). This is unambiguously the
paintbot/coworld-ctf chrome lineage — not a cogame-gridlock rewrite. It advances (three
differing clocks) and it renders (`loaded: true`, `failure: null`).

The endcard state is degraded: rows 21–22 of the 22-row table are clipped behind the transport
strip, the `Unlocked/Tick/Day` column values bleed inside the minimap panel, and the top band
superimposes ~4 text layers (endcard stat line, `DAY 3 · DAY`, `ACHIEVEMENT`, `HP 0 · SCORE
20440`). I weighed whether this alone falsifies "legible, and it shows the game": it does not.
The 0 % and 50 % readouts are clean single-line clocks, the mid-episode chrome is intact, and
even the crowded final frame still tells the episode's story legibly (what was unlocked, when,
the death, the score). The failure modes this check exists to catch — never renders, frozen
frame, empty picture, different product — are all absent. The endcard overflow is a phase-30
item-14-class legibility defect confined to the terminal overlay, and it also contradicts the
design's own pin (design.md:1617-1618, `#endcard { bottom: var(--band) }` with "every row
present" at :1682-1686 — rows are present in the DOM but not all visible in an 800 px
viewport). Advisory, not blocking.

## Advisory residue (for the close report / a follow-up phase-30 pass; none blocks)

- **Endcard overflow at episode end** — the 22-row table overflows the 800 px viewport (rows
  21–22 clipped behind the transport strip), column values bleed into the minimap panel, and
  the top band superimposes ~4 text layers. Needs a scroll/compaction pass and a z-order fix;
  contradicts design.md:1617/1682's own endcard pins while meeting SPEC check 8.
- **8 dead 404 preloads** — `client/replay_broadcast.html:1585-1587` still preloads coworld-ctf
  `soldier_{green,yellow,blue,red}_front[_gun].png`, which the crafter bundle does not ship.
  Render unaffected (`loaded: true`, `failure: null`); console noise only.
- **Homesteader episode below the design's own bar** — design.md:1376 asks
  `achievementsUnlocked >= 3`; round-2 homesteader unlocked 2 (techtree 4 clears it), with
  `blocksMined: 0`, `itemsCrafted: 0`, 121/4096 cells seen — 19 competent-sounding LLM turns
  that never found a tree. SPEC check 4's actual wording (non-scripted, non-trivial, not all
  fallbacks) is met; this is a prompt-tuning/difficulty observation, not a done-ness failure.
- **Log labelling oddity** — the game log says "bedrock transport, model
  us.anthropic.claude-haiku-4-5…" while the sidecar's upstream lines show
  `POST https://openrouter.ai/api/v1/messages`. Matches none of the four defect patterns and
  all 34 calls were 200 OK; worth a note only.
- **Minor record slip in VERIFY §1** — it states fillers were registered "at 2026-08-29T04:02Z
  (log.md:34)"; the log line is stamped 04:04:09Z. The material claim (fillers before the first
  trigger, in the same ordered block) holds either way.

## Verifier report audit

| check | verifier said | I verified | agrees |
|---|---|---|---|
| 1 | TRUE, 2 completed rounds | live: now 3 completed, error null; filler ordering in log.md | yes |
| 2 | TRUE, 2 rows, fillers absent | live: 3 rows (richard joined), both champions ranked, fillers absent | yes |
| 3 | TRUE, both round-2 ereqs | pasted evidence internally consistent with §4/§5 ids and scores | yes |
| 4 | TRUE via declared substitute | reproduced: fetched bytes, ran replay_summary.py, same six readouts | yes |
| 5 | TRUE, CLEAN ×2 | full logs pasted; grep patterns absent; call counts reconcile | yes |
| 6 | PARTIAL (6a TRUE, 6b FALSE-as-fetched, cause documented) | live re-fetch identical; adjudicated SATISFIED per procgen precedent | yes (adjudicated TRUE) |
| 7 | TRUE from committed artifact | read the committed file myself, exact substring present | yes |
| 8 | TRUE with findings A and B | CI run success re-checked via gh; json/png re-read; my own judgment concurs | yes |

The verifier's report is accurate, conservatively framed (it declined to self-certify 6b and
flagged its own design-bar shortfall), and nothing in it failed reproduction.

BLOCKING: 0
