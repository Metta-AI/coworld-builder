# Phase 40 — released by adoption, not by this run's own dispatch

**Decision (coordinator, session `c3f0efb9`, 2026-09-11T08:50Z).** This run ships the
already-canonical coworld **`battlecode` 0.11.2**, `cow_7c4f0e60-3dd5-4de2-ba2c-441dad1b4de2`,
instead of a version produced by its own `coworld-release.yml` dispatch. No fourth dispatch was
spent.

## Why adoption is available at all

`Metta-AI/cogame-battlecode` publishes **one** coworld named `battlecode` whose version line is
**shared by all ten Battlecode year runs**. A release therefore publishes whatever is on `main`,
including other years' work — and 0.11.2 was dispatched by the **bc19** run at 05:21:26Z
(release run `34565644691`) from `main@526befdb`, which already contained:

- the complete bc17 year module (PR #18, merged 22:17Z as `07ad48cc`), and
- every round-1 review fix (PR #22, merged 03:10:21Z as `526befdb`).

So the bc17 variant and its four policies were published as a side effect of a sibling year's
release, before this run's own dispatches were ever attempted.

## The evidence, verified field by field against `prompts/40-release.md` §Exit criterion

`release-result.json` in this directory is the **unmodified `release-result` artifact of run
`34565644691`**, downloaded with `gh run download 34565644691 -R Metta-AI/cogame-battlecode -n
release-result`:

| exit-criterion field | value |
|---|---|
| `ok` | `true` |
| `version` | `0.11.2` |
| `cow_id` | `cow_7c4f0e60-3dd5-4de2-ba2c-441dad1b4de2` |
| `canonical` | `true` |
| `manifest_sha` | `sha256:4d5c5bced3b461c9baf31db9cea951ac6a9198234f37555879edeac04a492fd5` |
| `certify.ok` | `true` |
| `certify.replay_liveness` | `Replay liveness: skipped (static replay bundle declared; /client/replay and /replay not required)` |
| `secret_put` | `true` |
| `step_failed` | `null` |
| `policies[]` | 40 entries; bc17's four at `v4` |

Independently confirmed live from `GET /v2/coworlds?limit=200` (filtered client-side on
`name == "battlecode"`, selected on the key `canonical`): 0.11.2 is the **only** `canonical: true`
row. `GET /v2/coworlds/cow_7c4f0e60-…` lists ten variants including
**"Battlecode 2017 — Robotic Wildlife Fund (2 seats)"** with `num_agents: 2`.

The four bc17 policies of that dispatch, in the canonical shape `prompts/40-release.md` step 2
requires — two LLM prompt champions plus two scripted fillers:

| role | label | ownership |
|---|---|---|
| champion #1 | `battlecode-bc17-orchard:v4` | daveey |
| champion #2 | `battlecode-bc17-tankrush:v4` | **daveey-1**, `player_id: ply_bac48eb1-662e-44f8-973d-f3e016dccf5d` |
| filler | `battlecode-orchard:v4` | daveey (`PLAYER_SCRIPTED=orchard`) |
| filler | `battlecode-examplefuncsplayer17:v4` | daveey (`PLAYER_SCRIPTED=examplefuncsplayer17`) |

`policy_version_id` is `null` for every entry, which is normal — `coworld upload-policy` prints no
uuid. Phase 50 resolves the UUIDs from `GET /v2/policy-versions`, filtered client-side.

## Why this run's own three dispatches could not be used

All three reached **`step_failed: "Upload the Coworld"`** (hosted smoke) with
**`certify.ok: true`** and a correct `replay_liveness` every time — the game certified, the
platform could not smoke it:

| version | run id | cow_id | canonical |
|---|---|---|---|
| 0.11.3 | 34573085216 | `cow_dab823b1-16ac-49c2-807d-b17107b97f3c` | false |
| 0.11.4 | 34574663722 | `cow_608a77a6-2a07-4522-aad9-a0edbba85415` | false |
| 0.11.5 | 34578020177 | `cow_1b3f8d86-1c94-4625-9a56-4d646bf374ff` | false |

Dispatch 3's artifact is kept beside this note as `release-result-0.11.5-FAILED.json`. The three
stranded rows are left in place, **not deleted** (`AGENT.md` hard rule 3).

The cause is platform-side, and the evidence is that it is not confined to this repo:

- League rounds across unrelated coworlds failed in the same window with
  `only <n>/<m> planned slots produced scoring evidence` — bc16 at 08:37:13Z (the same minute as
  dispatch 3's smoke) on the **already-canonical 0.11.2 image this run did not create**, bc26 at
  07:00/07:06/07:14Z, and non-battlecode leagues at 07:39Z and 07:42Z. Sampling
  `GET /v2/rounds?limit=60` at 08:43Z shows failures and completions interleaved minute by minute.
- The bc19 run's own 0.9.1 dispatch (34562081561, 04:24Z) failed at the **same step from the same
  sha** that then uploaded successfully as 0.11.1 and 0.11.2.
- `526befdb..2d61d796` (the tree the three dispatches used, i.e. with PR #23) touches only
  `client/replay_broadcast.html`, `tests/test_viewer.nim`, `tools/ci/renderer_fixture.html` and
  `tools/ci/viewer_smoke.mjs` — **zero game or server code**.
- The errors are transport/infra only (`ReadError (HTTP status unavailable)`,
  `Container worker Error with exit code 1`, `Error type: container_failed`).

A hosted smoke requires **100 %** of its episodes to pass and cold-pulls a brand-new image, which
makes a release the most exposed operation on a degraded fleet. That is why three version bumps
could not outrun it, and why a fourth was not spent.

## Residue carried forward, stated plainly

**0.11.2 predates PR #23**, so the shipped viewer bundle lacks that PR's two follow-ups: the
`#bc17-doctrines-toggle` re-open chip (a viewer who dismisses bc17's doctrine panel cannot
re-open it) and a widened endcard capture in `tools/ci/viewer_smoke.mjs` (CI evidence only, not
user-visible).

This is **self-healing and costs this run nothing**: PR #23 is merged to `main`
(`2d61d796e6a1da9ca234dd626c4043ff6ab91dbe`, 07:08:58Z), the version line is shared, and other
year runs release from `main` several times a day — so the next successful release by **any** year
run supersedes 0.11.2 with a canonical version that carries the chip. Phase 60 verifies the viewer
against whatever is canonical when it runs, and phase 80 records which version that was.
