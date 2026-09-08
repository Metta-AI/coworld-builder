# Build report — 2026-09-08-battlecode-2023 (bc23 year module, MOD run)

- Repo: `Metta-AI/cogame-battlecode` (existing, public; MOD run — no repo create, no propagate-secrets)
- Branch: `bc23-year-module` (off `main@6885a066`)
- Design note: `/workspace/coworld-builder/runs/2026-09-08-battlecode-2023/design.md` → lands as
  `docs/plans/2026-09-08-battlecode-2023-design.md`
- Started: 2026-09-08

## Timeline

(appended as work proceeds)

- **start** — cloned repo, read design note + prompts/20-build.md + learnings.

## Environment note (matters for every later step)

- **git-over-HTTPS is refused sandbox-wide** on this session ("Invalid username
  or token") for both `origin` and a token-in-URL remote, while `gh api` works.
  Every push therefore goes through the git Data API with
  `/tmp/push_api.py` (blobs via `--input`, tree with `base_tree`, commit,
  non-force `PATCH refs/heads/...`), and the script **diffs the landed tree
  against the intended file list** after every commit (the 2026-09-07 lesson).
  Because the Data API mints a new commit object, the local sha and the landed
  sha differ; the local branch is reset to `FETCH_HEAD` after every push.
- **A local Nim toolchain WAS obtainable** (nimby 0.1.26 + Nim 2.2.4 +
  `nimby --global sync nimby.lock`), so the whole module was type-checked,
  compiled `-d:release` and play-tested locally before the first push. Temurin
  8 and the pinned `battlecode23-3.0.15.jar` were also downloaded locally
  (sha256 `5d4e42a5…d72a`, 16 982 927 bytes — **matches the design note's pin
  exactly**), which is what let the parity work be checked without a CI round.
  Docker and emsdk are still absent; `docker-smoke` and `wasm-viewer` remain
  CI-only.

## Timeline

- **push 1 — `b9377dd33b64d3bd05a21138a420b4a62816bdaa`** on
  `bc23-year-module` (62 paths). The year module, the converted maps, the
  sprite atlas, the registry/dispatch/sheet/baselines/render/broadcast/match
  wiring, `GameVersion` GV08 → **GV09** with `ReplayCompatibleGameVersions`
  extended, and the design note at
  `docs/plans/2026-09-08-battlecode-2023-design.md`. No CI yet:
  `ci.yml`'s `on.push.branches` does not name this branch until the CI commit.

### Locally measured before the first push

| measurement | value |
|---|---|
| `lemonade` mirror, `Quiet`, 2000 rounds | carriers 229/202, launchers 75/56, banked 10280/7840, anchors built 2/2 placed 2/2, longest island hold 1574/1511, alive 56/13, refused actions **0** |
| `lemonade` mirror, `Sneaky`, 2000 rounds | carriers 176/140, launchers 178/150, banked 2336/3765, anchors 3/5 placed 2/2, hold 1510/1408, alive 43/94, refused **0** |
| `-d:bc23BrokenChassis` control, same maps | **banked 0/0** on every map — the negative control the competence gate must go red on |
| `lemonade` vs `examplefuncsplayer23` | 6/6 to `lemonade`, all by `conquest`; the weak bot still builds 17–46 carriers, 20–51 launchers, 2–3 anchors, mines and throws |
| perf, `IslandHopping` 60×30, `carrier_eco`/80/anchor_budget 0 | **5.9 s** release for a full 2000-round game (451 robots alive at the end) — the note's gate is 100 s |
