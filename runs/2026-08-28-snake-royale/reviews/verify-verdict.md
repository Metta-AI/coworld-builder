blocking: 0

# Phase-60 verdict — snake-royale

Run `2026-08-28-snake-royale` · repo `Metta-AI/cogame-snake-royale` @ `18b9da8` (released 0.1.1 head) ·
Checklist: `docs/SPEC.md` §Definition of done, as commands in `prompts/60-verify.md` ·
VERIFY.md under adjudication: `runs/2026-08-28-snake-royale/VERIFY.md` (claimed 8/8 TRUE).

Reading order followed the judge brief (SPEC → 60-verify → VERIFY.md → committed evidence); declared
plainly: VERIFY.md was read before my re-fetches, so every load-bearing claim in it was then
**independently re-fetched or re-computed** rather than trusted — leaderboard, rounds, episode request,
replay bytes + summariser re-run, hosted log, page SSR + session route, release-result.json, and the
viewer-check run + artifact hashes. No fixer self-report exists in this phase's scope.

## Per-check table

| # | Check | Verifier | Judge | Evidence basis | Note |
|---|---|---|---|---|---|
| 1 | ≥2 completed rounds after fillers set | TRUE | **TRUE** | re-fetched | `GET /rounds?league_id=$L` → rounds 2 (07:44:31Z) and 3 (08:00:44Z) `completed`, round 1 `failed` with error quoted verbatim (matches); round 4 now `pending`, irrelevant. Filler set reads back live (coil v1 + forager v1 = STATE `filler_version_ids`); both counted rounds' episodes seat `is_filler:true` participants — round 2 (`ereq_acf56070`, two coil seats) and round 3 (`ereq_8dbbce59`) re-fetched, both match VERIFY.md byte-for-byte. |
| 2 | Both champions ranked, fillers absent/Baseline | TRUE | **TRUE** | re-fetched | `GET /divisions/$D/leaderboard` (bare list) → exactly two rows: `1 daveey-1 snake-royale-glutton:v1 1030.5304984710244 2 2.0`, `2 daveey snake-royale-strangler:v1 969.4695015289755 2 0.0` — identical to VERIFY.md's paste. Both `rounds_played ≥ 1`; no filler rows (absent = accepted); in-episode fillers renamed `Baseline`/`Baseline (2)` per replay `names`. |
| 3 | Latest round's ereq completed with replay | TRUE | **TRUE** | re-fetched | `GET /episode-requests/ereq_8dbbce59-…` → `status:"completed"`, `replay_url` = the `544f5847-…` S3 URL, participants seat daveey (strangler, pos 0), daveey-1 (glutton, pos 1), fillers `is_filler:true` at 2–3 — identical to the paste. Nested-route substitution for the 405'd flat route is documented and correct. |
| 4 | Replay bytes valid, show the game | TRUE | **TRUE** | re-fetched + re-computed | Fetched the replay myself (26361 bytes, `COWLDSNK` magic). The design-declared substitute (`design.md:883–909`) was used **faithfully**: fresh clone at `18b9da8`, `tools/replay_summary.py` sha256 `2fc62a8a…` (matches VERIFY.md's claim). My own run reproduces every number: `protocol snake-royale/v1` (present **in the raw bytes**, not the tool's default — I grepped the bytes), `reason complete`/`full_time`, dirs `{llm:59, scripted:93}`, per-slot llm 9/9 and 50/50 for the champions, `fallbackTurns [0,0,0,0]` (0 % fallback), 59 says / 57 distinct, scores zero-sum, foodEaten 23. |
| 5 | Hosted game log clean | TRUE | **TRUE** | re-fetched | Re-fetched `artifacts/logs` for `ereq_8dbbce59` (elevated, 126401 bytes): **0** matches for the four gate strings on the raw body (the gate strings are plain ASCII and survive `b'…'` reprs verbatim, so the raw grep is decisive). Game-container lines match VERIFY.md's verbatim quote, incl. the two non-gated `attempt 1 failed, will retry` lines, corroborated by `fallbackTurns [0,0,0,0]`. The round-2 advisory is correctly labelled advisory — round 2 is not the round under test. |
| 6 | Public page uses static replay path | TRUE | **TRUE** | re-fetched | Reproduced all three sources: (a) raw-HTML grep empty (client-rendered — as documented); (b) `/coworlds` detail: `canonical:true`, `replay_viewer`/`featured_match` null platform-wide; (c) page SSR payload contains `snake-royale.r3.e1` + the `544f5847` replayUrl, and `POST /coworlds/replays/session` returns exactly the VERIFY.md viewer_url: static route `/v2/coworlds/replays/static/<cow_id>/<manifest_sha>/index.html?v=2#replay=…`, `ready:true`. The `#replay=` fragment variant is the documented same-static-route shape (`playbooks/observatory-api.md:326`). No `/client/replay` anywhere. Source choice recorded in VERIFY.md as required. |
| 7 | Certification declared static bundle | TRUE | **TRUE** | committed artifact, read myself | `jq -r '.certify.replay_liveness' runs/…/release-result.json` → `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)`; `.certify.ok == true`; same string in `.certify.output_tail` (10/10 cert steps). Matches the paste exactly; source (committed copy, not /tmp) correctly stated. |
| 8 | Viewer executed + spectator judgment | TRUE | **TRUE** | re-fetched + artifact hash-verified + png read myself | Run `33153918882` re-checked via `gh`: workflow `viewer-check`, `workflow_dispatch`, created 2026-08-28T08:04:55Z (after the 08:04:54Z dispatch), `conclusion: success`. I re-downloaded the `viewer-check` artifact: `viewer-smoke.json` and `viewer-smoke.png` are **sha256-identical** to the committed copies. Two-part rule holds from the committed json: (a) `loaded:true` @ 2998 ms via `data_replay_loaded:"true"`, `failure:null`, no error signal; (b) the three scrub clocks **differ** — `turn 0/50` → `turn 26/50 / ALIVE 3/4` → `turn 50/50 / ALIVE 2/4`, matching the replay's deaths at turns 8 and 42. (c) I read the png myself: the judgment paragraph is faithful — endcard `Baseline SURVIVES — 15 long, 12 eaten, 50 turns`, `FULL TIME`, results table cells identical to replay `place/survivedTurns/finalLength/foodEaten/declinedKills`, killfeed lines are the turn-25/26/50 says verbatim, speech bubble = turn-50 say, and the starter chrome (transport strip, spoilers toggle, 50/50 counter, speed chips, scrubber with beat ticks over a LENGTH momentum graph, scorebug, endcard) is present. Legible, shows the game, not the gridlock failure mode. |

## Blocking items

None.

## Refuted / discrepancies found

None material. Every pasted output I re-fetched reproduced byte-for-byte (leaderboard scores to full
float precision, round timestamps, participant lists, summariser outputs, cert string, viewer_url).

## Non-blocking observations

- **Scorebug place chips possibly swapped** (viewer-smoke.png, top strip): chip `#3` sits by
  `daveey · COG-alpha` (endcard place **4**) and `#4` by `Baseline (2) · COG-delta` (endcard place **3**).
  Chip semantics are not determinable from the artifact, and the authoritative endcard table reconciles
  exactly with the replay, so this is a phase-30-style legibility note, not a check-8 failure. VERIFY.md
  described the chips without attributing them, so nothing in it is falsified.
- VERIFY.md §1 attributes the filler registration to "07:36:0xZ" via the log; `log.md`'s 07:37:59Z line
  does not itself timestamp the registration. Immaterial: the check stands on the direct evidence
  (fillers read back live + `is_filler:true` seats in both counted rounds), which I re-verified.
- `tools/replay_summary.py:125` defaults `protocol` to `"snake-royale/v1"` when absent from the config
  JSON — a theoretical masking risk for the substitute. Not in play here: the raw replay bytes contain
  `"protocol":"snake-royale/v1"` (grepped directly).
- The verifier's round-2 advisory (fallback cause mislabelled `parse_error`; `attempt1Ms=6000` tight vs
  the Bedrock haiku tail) is well-evidenced and correctly non-blocking; worth carrying to LEARNINGS as
  the log already does.

## Verdict

All eight definition-of-done checks are TRUE, each proven by evidence that survives independent
re-fetching. The COWLDSNK substitution for check 4 was legitimate (design-declared) and executed
faithfully against the declared tool at the released head. Check 8 satisfies both machine conditions
and the judgment paragraph is an honest description of the committed screenshot.

BLOCKING: 0
