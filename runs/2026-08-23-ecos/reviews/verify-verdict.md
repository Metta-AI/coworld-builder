blocking: 0

# Phase 60 verdict — ecos (run 2026-08-23-ecos)

Head: coworld-builder 9dbe87a ("ecos: 60 verifier 8/8 TRUE; VERIFY.md + viewer-check committed")
Checklist: prompts/60-verify.md §The eight checks / docs/SPEC.md §Definition of done
Independent read written before reading VERIFY.md: **yes** — all Observatory fetches, the replay
download, the page/SSR fetch, the session POST, the committed artifacts and the GH run were
re-fetched and noted before VERIFY.md was opened.

## Per-check table

| # | Check (SPEC §DoD) | Verifier | Judge | Evidence I re-fetched (fresh, 2026-08-23T14:14Z) |
|---|---|---|---|---|
| 1 | ≥2 completed rounds after fillers set | TRUE | **TRUE** | `GET /rounds?league_id=$L`: r3 `round_b5bc0c39` completed 14:03:18Z, r2 `round_09601725` completed 13:48:08Z; r1 `round_d5f75051` failed, error verbatim `"Temporal RoundWorkflow failed before settling the round."` (the documented pre-filler auto-round, excluded). Decisive on "after fillers": **both** completed rounds' episode requests seat the filler — r2's `ereq_5a49b912` and r3's `ereq_714ef6a3` each list `ecos-steward` `is_filler:true` — so fillers were demonstrably in effect for every counted round. |
| 2 | Both champions ranked, fillers absent/Baseline | TRUE | **TRUE** | `GET /divisions/$D/leaderboard` (bare list): rank 1 `daveey-1` / `ecos-bloom:v1` / 1030.53 / rounds_played 2 / wins 2.0; rank 2 `daveey` / `ecos-keeper:v1` / 969.47 / rounds_played 2 / wins 0.0. No filler rows (absent = accepted case). |
| 3 | Latest round's ereq completed with replay + participants | TRUE | **TRUE** | `GET /episode-requests?round_id=round_b5bc0c39` → `ereq_714ef6a3-0fb0-461a-b8bf-5c2ed012f285`; detail: `status:"completed"`, `replay_url` = `…/replays/91e62cde-5d4b-42a9-bda2-3fdac44680c8.replay`, participants = daveey/ecos-keeper (is_filler:false), daveey-1/ecos-bloom (is_filler:false), ecos-steward (is_filler:true). Matches STATE's champion/filler version uuids (`9a5487b6`, `774aa245`, `8596fd17`). |
| 4 | Replay bytes valid; protocol; reason; champion decisions LLM | TRUE | **TRUE** | Downloaded 2,273,433 bytes; `jq -e` strict parse ok; `protocol`=`ecos.replay.v1` (matches `coworld_manifest_template.json` at head of cogame-ecos — I grepped the working tree: `protocol ecos.replay.v1` present); `results.reason`=`complete`, `ending`=`ten_generations` (no exception invoked, and collapse-as-complete would also be per design.md §End conditions). Doctrine events per seat: seat 0 = 10× `source:"llm"`, seat 1 = 10× `"llm"`, seat 2 (filler) = 10× `"scripted"`; **0 fallback, 0 retry**; `[.events[]|select(.fallback==true)]|length` = 0. `say`/`notes` are state-reactive and non-trivial (sampled 4 rows independently, e.g. gen-7 predators "Population collapse: 10→2…"). |
| 5 | Hosted game log clean | TRUE | **TRUE** | `GET /episode-requests/ereq_714ef6a3/artifacts/logs` (elevated): HTTP 200, 46,960 bytes; grep for `falling back\|LLM provider is unavailable\|cut off at max_tokens\|rejected` → **CLEAN**. VERIFY.md's corroborating counts reproduce exactly: `bedrock_sidecar_call` 20, `bedrock_sidecar_complete` 20, `via llm` 20, `via scripted` 10, `via fallback` 0 (occurrence counts; the log is 11 physical lines). |
| 6 | Public page uses static replay path; featured match present | TRUE | **TRUE** | Raw-HTML grep finds no iframe (documented client-rendered case — correctly recorded as unknown, not failure). SSR payload of `https://softmax.com/ecos` contains `state.playlist[0]` = episode `97a33aa8…`, `code "ecos.r3.e1"`, replayUrl identical to check 3's, matchup first=daveey-1/second=daveey (≥2 ranked players → featured match present). `POST /coworlds/replays/session` → `viewer_url` = `…/v2/coworlds/replays/static/cow_7f960dd9…/sha256%3Abbc83b69…/index.html?replay=<s3 url>&v=2`, `ready:true`; `<sha>` = STATE's `manifest_sha`; not a `/client/replay` pod URL. (`/coworlds` list shows `featured_match:null` — platform-wide, per playbook; VERIFY.md handled this correctly.) |
| 7 | Certification declared the static bundle | TRUE | **TRUE** | Committed `runs/2026-08-23-ecos/release-result.json`: `.certify.replay_liveness` = `"Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)"`. Read from the committed copy, as required. |
| 8 | Viewer executed and judged | TRUE | **TRUE** | GH run 32644408716 (viewer-check, Metta-AI/coworld-builder): `conclusion:"success"`, created 2026-08-23T14:06:25Z — checked via `gh run view`, not accepted from the report. Committed `viewer-smoke.json`: `loaded:true`, `ms:2900`, `data_replay_loaded:"true"`, `data_replay_error:null`, `failure:null`; three scrub clocks **differ and advance**: `GEN 1 / 10 TICK 3 OF 600` → `GEN 6 / 10 TICK 315 OF 600` → `GEN 10 / 10 10 GENERATIONS`. Its `url` equals the check-6 viewer_url exactly. I viewed `viewer-smoke.png` myself: legible end-card — `GEN 10 / 10`, "BASELINE WINS / 10 GENERATIONS / …integrated the most biomass (12.71)", three score cards (2.75 / 6.16 / 12.71) that reconcile exactly with `participant_scores` and `.results.scores`, scorebug with per-species population/biomass, transport bar `600 / 600`, and a three-line population strip whose red (predator) curve sags — consistent with the replay's `alarm` at t=354 and predator pop 2 at end. The spectator-judgment paragraph is written from the rendered evidence and is accurate. Artifacts are committed (9dbe87a). |

## Refuted

None. I attempted to refute each of the eight TRUEs by independent re-fetch; every one
reproduced. No claim in VERIFY.md rests on un-pasted evidence: each check carries the command,
the fetched output, and the verdict, and each output matched my fresh fetch (modulo live-data
identity — same round ids, same ereq, same scores, same byte counts: 2,273,433 replay bytes,
46,960 log bytes, 499,750-byte png).

## Verifier report audit

| claim in VERIFY.md | I verified | agrees |
|---|---|---|
| 2 completed rounds, r1 failed/excluded with error quoted | rounds endpoint, error string identical | yes |
| leaderboard rows/scores/rounds_played | re-fetched, identical | yes |
| ereq_714ef6a3 completed + participants + scores | re-fetched, identical | yes |
| replay strict-parse, protocol, reason, 20/20 LLM champion doctrines, 0 fallbacks | re-downloaded and re-ran jq, identical | yes |
| manifest declares `protocol ecos.replay.v1` | grepped cogame-ecos working tree | yes |
| logs CLEAN + corroborating grep counts (20/20/0/20/10) | re-fetched, reproduced exactly | yes |
| SSR playlist featured match + session POST static viewer_url, ready:true | re-fetched both, identical | yes |
| release-result.json replay_liveness line | read committed file | yes |
| viewer-check run green; loaded:true; three differing clocks; artifacts committed | `gh run view` success; committed json/png inspected; commit 9dbe87a | yes |

## Non-blocking observations

1. **Timestamp wrinkle in check 1's narrative.** VERIFY.md says fillers were "registered at
   13:46Z", but the log line it cites is stamped `2026-08-23T13:47:10Z`, and round 2's API
   `created_at` is 13:46:25Z — nominally *before* that log line. The substantive requirement is
   nonetheless proven the strong way: both counted rounds' episodes seat `ecos-steward` with
   `is_filler:true` (fetched from both ereqs), which is only possible with fillers in effect.
   The imprecision is in the prose, not the facts.
2. **`feed_lines: 0`** at the sampled positions (already flagged in VERIFY.md). At 100 % the
   end-card overlays the feed; the doctrine `say` content is present in the replay (20 non-empty).
   A legibility/polish item, not a DoD item — no DoD clause requires a non-zero feed count.
3. **Replay `results.names` are `["daveey","daveey-1","Baseline"]`** (player-name space), where
   design.md §results.json shows policy names (`ecos-keeper`, …). No DoD item names this field;
   check 3's participant naming is satisfied via the API and the viewer's naming is legible.
   Design-fidelity note for the record only.

## Verdict

All eight definition-of-done items are TRUE at the current head, each supported by inline
fetched evidence in VERIFY.md that reproduced under independent re-fetch. Zero blocking
findings.

BLOCKING: 0
