# cogame-battlecode — design note v2 (2026-09-03)

**Starter: `coworld-ctf` (paintbot)**, mounted read-only at `/workspace/starters/coworld-ctf` and
forked into `Metta-AI/cogame-battlecode`. Reason, by game shape: after the operator override this is
**a real-time-loop grid game whose rules we write in Nim** — a deterministic sim module that compiles
natively for the server *and* to wasm for the replay viewer, with a thin env-switched player
container and all decisions taken server-side. That is exactly coworld-ctf. **Every convention there
holds here unless this note says otherwise**: the Nim sim/server/player layout, the `nimby.lock`
toolchain, the bitworld runtime contract, `GameVersion` discipline, `tools/build_replay_viewer.sh`,
the `replay-viewer/` bundle, the `client/` chrome, the one-parallel-batch LLM decision layer
(`src/ctf/llm.nim` / `decide.nim` / `directives.nim` / `baselines.nim`), and the "degrade, never
hang" rule. **Nothing is taken from `cogame-factorio`.** `cogame-parley` is the fallback reference
for protocol/player shape only.

This note supersedes the v1 (Java-wrapper) design in full. There is **no JVM, no Java and no JDK in
the image**; the Java engine survives only as a **CI-only parity oracle**. Engine facts below were
verified by reading `github.com/battlecode/battlecode26` at tag **`engine.1.2.5`** (43 maps at that
tag — re-verified, see §Sim module) and by running real headless matches locally with
`battlecode26-java-1.2.5.jar`; ctf facts were read from the mounted starter. `file:line` references
are to those trees.

### Source idea (verbatim)

```
MIT Battlecode 2026 ("Uneasy Alliances") is the real thing: a 2-team, turn-based grid war on 30x30 to 60x60 symmetric maps, 2000 rounds a game, best of 3, run by the official Java engine with per-robot bytecode limits. Two clans of robot rats (a 3x3 rat king that spawns baby rats, eats 2 cheese a round and starves without it; baby rats that forage cheese from mines, bite, dig and place dirt, lay rat traps and cat traps, ratnap and throw each other) start in COOPERATION against an even number of 10,000-HP NPC cats. Either team can BACKSTAB at any moment (bite an enemy rat, ratnap one, or let them walk into your trap) and the scoring formula flips from cat-damage-weighted to king-survival-weighted: coop end = round(0.5 * %cat damage + 0.3 * %living kings + 0.2 * %cheese delivered); backstab end = round(0.3 / 0.5 / 0.2). Losing every rat king loses the game outright. That single bit — when, whether and how to betray an ally you still need — is the whole game, and it is an LLM-legible strategic decision sitting on top of a deep, deterministic, genuinely watchable RTS.

The coworld wraps the unmodified engine (org.battlecode:battlecode26-java 1.2.5 from the public Maven at https://releases.battlecode.org/maven, Java 21; source https://github.com/battlecode/battlecode26 tag engine.1.2.5, AGPL-3.0) and the strongest open community bot, awubot (https://github.com/awu7/battlecode-2026, branch `final`, AGPL-3.0: Jinja-templated Java, strategy classes over a shared BabyRat/RatKing base, 72 custom maps plus scrim tooling). A cog does not drive rats turn by turn — a match is 3 games x 2000 rounds x dozens of robots, far past any per-turn LLM budget. A cog is a clan commander who writes the doctrine before the war: at episode start it receives the condensed spec, the RobotController API digest, this match's map names and a strategy sheet; it answers with its clan's doctrine, and the engine plays the whole match deterministically from it.

Seats: 2 (Team A / Team B, one cog per clan). num_agents = 2 in every variant and the certification fixture.
Motive: mixed-motive, zero-sum at the end. Cooperate against the cats to farm points, or backstab to win on king survival; the formula shift makes early betrayal pay only if you can actually finish the enemy kings. A trust game with a real war underneath.
Policy interface: text/code, one shot per episode. The cog returns a DOCTRINE = (1) a JSON strategy sheet of named knobs the builder exposes from awubot's strategy layer — backstab_policy {never | when_ahead | at_round_N | on_first_contact | retaliate_only}, cat_engagement, cat_trap_budget, rat_trap_budget, spawn_curve, cheese_ferry_ratio, king_count_target, dirt_wall_policy, throw_rats_to_feed_cats — plus (2) an optional Java Strategy class (awubot's own CLAUDE.md rule: never edit BabyRat.java, new behaviour = a new strategy class), compiled in-container with javac and battlecode.instrumenter.Verifier; compile/verify errors go back to the cog, max 3 attempts, then the sheet alone applies (an unknown or invalid sheet field = the default, so a cog can never hang or forfeit the match). Both seats submit simultaneously; the game container then runs battlecode.server.Main headless (-Dbc.server.mode=headless, seed from the episode) on the match's maps and scores exactly per the spec. Results carry per-game points, the backstab round (if any) and who initiated it, king deaths, cat-damage share and cheese delivered.
Scripted baselines (same image, PLAYER_SCRIPTED=<name>): awubot (the awu7 final bot on its default sheet) and examplefuncsplayer (the official scaffold bot, weak). Champions are PLAYER_PROMPT LLM policies — daveey: a loyal cat-hunter doctrine; daveey-1: an opportunistic backstabber — on the same awubot chassis with different doctrines, so matches are decided by the strategic choice, not by whether an LLM can write a pathfinder in one shot.
Fills gap: first coworld on a real, externally maintained competition engine with a deterministic bytecode-metered sandbox; first "write the doctrine, then watch the war" policy shape at RTS scale (cogolf and grid-wars author code, but for a 4,000-round two-army battle); the cooperate-then-betray motive on top of a genuine strategy game rather than a payoff matrix.
Integrity (anti-collusion): symmetric seeded maps; both doctrines are sealed and simultaneous (no channel between cogs before the match; in-match the only cross-team channel is the engine's own squeaks and positions); anonymous in-game aliases (Clan Ash / Clan Basil), real player names spectator-side only; maps drawn from the pool per episode by seed; the baseline chassis is public, so there is no hidden advantage to decode.

Replay plan (watchability): the official Battlecode web client is a static TypeScript/React app that plays .bc26 flatbuffer match files (https://github.com/battlecode/battlecode26/tree/main/client; client/src/app-search-params.tsx already loads a match from a URL search param). Build it with `npm run build` into the standard static-replay-viewer bundle behind the starter's chrome (scrubber, transport bar, scorebug, endcard). The coworld replay is the usual JSON envelope (protocol, seats, alias-to-name map, each cog's doctrine sheet and Java patch, compile transcript, per-game results, backstab round) with the engine's .bc26 bytes embedded base64 (match_b64); the viewer decodes it in the browser and hands it to the client's playback. No pod, no server, no engine in the browser — the recorded match IS the replay. Spectators get the real Battlecode visuals: rats, cats, cheese, traps, dirt, the cooperation-to-BACKSTAB flip as a chapter marker, the three-bar point breakdown the official client draws, and an endcard naming who betrayed whom at which round plus each doctrine's headline knobs in plain words.

Design pins for the builder: starter = cogame-factorio (external engine run per episode; Python game server; players env-switched). Repo Metta-AI/cogame-battlecode, slug `battlecode`, licence AGPL-3.0 (engine and awubot are AGPL). Image: Java 21 JDK + the gradle-resolved engine jar + the node-built client bundle, linux/amd64. CI: the Nim jobs in the ci.yml template do not apply — replace them with gradle build, a headless engine smoke (examplefuncsplayer vs awubot on DefaultSmall, asserting a .bc26 is written and parses), and the viewer smoke against that real .bc26. Timing: play inside 60% of episodeTimeoutSeconds (720 s) — measure engine wall-clock in CI and size the match to fit (v1 may be best-of-1 on one map, with a wall-clock guard that stops the engine and scores the finished games; the doctrine round-trip is one LLM call, three at most). Maps: awubot's 72 plus the official set in battlecode26/maps, chosen by seed. Rules, cheese, points and tiebreaks exactly as the spec (battlecode26-specs.txt in the awu7 repo; https://play.battlecode.org/bc26/specs).

Source: https://github.com/awu7/battlecode-2026 (awubot, maps, specs, scrim tooling); https://github.com/battlecode/battlecode26 (engine, client, schema, example bots)
```

### Operator override (2026-09-03T21:03Z–21:14Z) — what it changes

The idea card's *implementation* pins (JVM at runtime, Java strategy class, `.bc26` in the replay,
starter = cogame-factorio) are **superseded**. Its *game* pins (2 seats, doctrine-before-the-war,
the cooperate/betray motive, the scoring formulas, sealed simultaneous doctrines, aliases, maps by
seed) stand. The override, and where each item is discharged:

| Override | Discharged in |
|---|---|
| 1. No Java at runtime; full behaviour port of the BC2026 rule set to a deterministic Nim sim; `java.util.Random` reproduced; one module compiles native **and** wasm | §Sim module (port scope, RNG, file map, determinism) |
| 2. Players are Nim bots inside the sim process (ported behaviour of examplefuncsplayer + a distilled awubot), bytecode limits → a fixed decision budget, documented as a divergence | §Sim module ("The chassis"), §Tests, `docs/RULES.md` §Divergences |
| 3. Doctrine = JSON sheet only; sealed simultaneous one-shot; LLM/scripted env switch; 720 s budget; decide best-of-3 vs best-of-1 with the arithmetic | §The game ("Match shape and budget"), §Decisions |
| 4. Standard static wasm viewer: events + config + seed in the replay JSON, wasm sim re-derives every frame, ctf chrome verbatim, official sprites for art | §Viewer |
| 5. Java engine as a CI-only parity oracle; parity is the phase-30 gate; no JDK in the image | §Tests ("parity-oracle"), §Packaging |
| 6. Maps converted from `.map26` by a CI-time tool; converted maps committed | §Sim module ("Maps") |
| 7. Starter = coworld-ctf for everything; all four viewer files from it; chrome verbatim | this paragraph, §Viewer, §Packaging |
| 8. Multi-year: one repo, one coworld, one variant per year, year module selected by `game_config.year`; v1 ships `bc26` | §Sim module ("The year module"), §Packaging |
| Steer (20:57Z): every economy/king/dirt knob must visibly change play; endcard reports the economic story | §Decisions (knob table), §Viewer (endcard), §Tests (`test_knob_sensitivity.nim`) |

### Design pins (`playbooks/make-coworld.md` §Phase 0) — how each is satisfied

| Pin | Satisfied by |
|---|---|
| Starter by game shape | `coworld-ctf` — a real-time game loop with rules written for this coworld, Nim sim, RL/scripted + LLM policies (playbook table row 2). |
| Public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-battlecode`, public, **AGPL-3.0** (the ported rule set and the sprite art derive from AGPL upstreams; a public repo also discharges the source offer). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | One image, two entrypoints; `PLAYER_PROMPT=<doctrine brief>` vs `PLAYER_SCRIPTED=awu|scaffold` on `/bin/battlecode-player` (§Decisions). |
| Static wasm replay viewer, never a pod | `replay_viewer.bundle = static-replay-viewer`; `tools/build_replay_viewer.sh` compiles **the same sim module** to wasm; the browser re-derives every frame from events+config+seed. No `/client/replay` live viewer is declared. |
| Real art, starter chrome verbatim | Sprites cut from the official Battlecode client art (credited in `NOTICE`); `client/chrome_common.js` byte-for-byte; `index.html` = ctf's `client/replay_broadcast.html` **with a game block appended** (§Viewer). |
| Two name spaces | In-game aliases **Clan Ash / Clan Basil**; real player names only in the replay envelope's `names[]`, drawn only by the viewer. |
| Degrade never hang, inside 60 % of `episodeTimeoutSeconds` | Every wait bounded; worst case **435 s ≤ 720 s**, arithmetic in §The game. |
| `num_agents` in every variant and the cert fixture | `num_agents: 2` inside `variants[0].game_config` (`bc26`) and `certification.game_config`; never at variant top level (§Packaging). |
| Policies before `upload-coworld`, secret after, fillers ≠ champions, fillers before the first trigger | Release template unchanged; policy set in §Packaging. |

---

## The game

**Battlecode 2026 "Uneasy Alliances", played by doctrine, simulated in Nim.** Two cogs each command
a clan of robot rats on a symmetric grid. Neither cog moves a rat. At t=0 each writes a **doctrine**
— a JSON strategy sheet of named knobs — and the deterministic sim then plays the whole match from
those two sheets while both cogs watch. Both clans start in COOPERATION against neutral NPC cats
and the points formula is cat-damage-weighted; the moment either clan takes a hostile action against
the other, the world flips to BACKSTAB and the formula reweights toward king survival. Losing every
rat king loses the game outright.

**Seats: `num_agents = 2`, always.** Slot 0 = Team A = **Clan Ash**, slot 1 = Team B = **Clan
Basil**; the episode seed permutes which slot takes side A (§ step 2 below).

### The ported rule set (v1 scope = the whole 2026 game)

Ported behaviour-for-behaviour from the engine at tag `engine.1.2.5`; the port is the authority at
runtime, the Java engine is the CI oracle. Everything the override enumerated is in scope:

- **Map**: 20×20…60×60, symmetry `rotation | horizontal | vertical`, walls, dirt, initial cheese,
  cheese mines (paired by symmetry), cat waypoint sets, initial bodies (one 3×3 rat king per team,
  an even number of cats). Sources: `schema/battlecode.fbs` `GameMap`, `world/LiveMap.java`,
  `world/GameMapIO.java`.
- **Units** (`common/UnitType.java`, verbatim table): `BABY_RAT` hp 100, size 1, visionConeR² 20,
  cone 90°, actionCd 10, moveCd 10; `RAT_KING` hp 600, size 3, visionConeR² 25, cone 360°,
  actionCd 10, moveCd 40; `CAT` hp 4000, size 2, visionConeR² 17, cone 180°, actionCd 30, moveCd 20.
  (The idea card says 10 000-HP cats; the pinned engine says 4 000 — **the engine wins**, and the
  divergence from the card is noted in `docs/RULES.md`.)
- **Cooldowns**: `COOLDOWNS_PER_TURN = 10` decay per turn, `COOLDOWN_LIMIT = 10`,
  `MOVE_STRAFE_COOLDOWN = 18`, `TURNING_COOLDOWN = 10`, `BUILD_ROBOT_COOLDOWN = 10`,
  `CHEESE_TRANSFER_COOLDOWN = 10`, `DIG_COOLDOWN = 25`, `THROW_RAT_COOLDOWN = 20`,
  `HIT_GROUND_COOLDOWN = 10`, `HIT_TARGET_COOLDOWN = 20`, `CARRY_COOLDOWN_MULTIPLIER = 1.5`,
  `CHEESE_COOLDOWN_PENALTY = 0.01` per carried cheese (the carry slowdown),
  `CAT_DIG_ADDITIONAL_COOLDOWN = 5`, `CAT_SLEEP_TIME = 2`.
- **Vision**: cone radius² + cone angle per unit type, **plus chirality** (`InternalRobot` carries a
  chirality flag that mirrors the cone; ported exactly — a mirrored cone that is not mirrored is a
  silent, match-long divergence).
- **Cheese**: mines spawn on `rand.nextFloat() < 1 - (1 - 0.01)^(round - lastSpawnRound)`
  (`world/CheeseMine.java:46`), then `dx, dy = rand.nextInt(-4, 5)` and a **symmetric paired spawn**
  with up to 5 validity attempts, `CHEESE_SPAWN_AMOUNT = 20` on both tiles
  (`GameWorld.java:500–556`). Raw (carried) vs global (team) cheese; pickup radius² 2, transfer
  radius² 9. `INITIAL_TEAM_CHEESE = 2500`.
- **Rat kings**: eat `RAT_KING_CHEESE_CONSUMPTION = 2` per round, lose `RAT_KING_HEALTH_LOSS = 10`
  hp per round when unfed; `MAX_NUMBER_OF_RAT_KINGS = 5`, dropping to
  `MAX_NUMBER_OF_RAT_KINGS_AFTER_CUTOFF = 2` past `RAT_KING_CUTOFF_ROUND = 1200`;
  `NUMBER_INITIAL_RAT_KINGS = 1`; formation (four adjacent rats become a king) and the
  `RAT_KING_UPGRADE_CHEESE_COST = 50`.
- **Spawning**: the rat cost curve (`getCurrentRatCost`), `BUILD_ROBOT_RADIUS_SQUARED = 8`.
- **Combat**: biting with cheese-boosted damage, ratnapping (carry, `MAX_CARRY_DURATION = 10`,
  `MAX_CARRY_TOWER_HEIGHT = 2`, `SAME_ROBOT_CARRY_COOLDOWN_TURNS = 2`), throwing with collateral,
  feeding a carried rat to a cat.
- **Traps** (`common/TrapType.java`, verbatim): `RAT_TRAP` cost 20, damage 50, stun 30, …;
  `CAT_TRAP` cost 10, damage 100, stun 20, …; placement radii, per-team live-trap counts
  (`getNumberRatTraps` / `getNumberCatTraps`), and the rule that cat traps cannot be placed in
  backstab mode unless you were the victim and are within
  `CAT_TRAP_ROUNDS_AFTER_BACKSTAB = 100` rounds (`RobotControllerImpl.java:349`).
- **Dirt**: dig (`DIG_DIRT_CHEESE_COST = 5`) and place (`PLACE_DIRT_CHEESE_COST = 0`), burial and
  unburying.
- **Cats**: the NPC state machine (`world/CatStateType.java` = `EXPLORE | ATTACK`, with the
  chase/search behaviour inside `world/InternalRobot.java` ≈ lines 1180–1400): waypoint following
  from the map's `catWaypointIds`/`catWaypointVecs`, BFS around walls, pounce
  (`CAT_POUNCE_MAX_DISTANCE_SQUARED = 13`), scratch (`CAT_SCRATCH_DAMAGE = 20`), sleep after
  feeding, and the "returned to explore" waypoint bookkeeping.
- **Comms**: squeaks (`SQUEAK_RADIUS_SQUARED = 16`, per-turn message cap) and the 64-int shared
  array (`SHARED_ARRAY_SIZE = 64`).
- **Backstab**: any hostile action against the other clan (bite, ratnap, throw at, or the victim
  walking into your rat trap) flips `isCooperation` globally and records the initiating team
  (`GameWorld.java:421–430, 640–641`; `InternalRobot.java:624, 649`).
- **Scoring and end**: below.

### Round loop — the exact resolution order (mirrors `GameWorld.runRound`)

Per round, in this order (numbers are the sim's own step list; a re-ordering is a rules change and
bumps `GameVersion`):

1. `round += 1`.
2. Every robot's *beginning-of-round*: clear its message inbox, indicator and death mark
   (`InternalRobot.processBeginningOfRound`).
3. Iterate the dynamic bodies **in spawn order** (`ObjectInfo.dynamicBodyExecOrder` — append on
   spawn, remove on death; **not** id order), skipping bodies that died earlier this round.
4. For each body, *beginning of turn*: **the first body of the round runs every cheese mine**
   (`InternalRobot.java:1114` → `GameWorld.runCheeseMines`, guarded by `hasRunCheeseMinesThisRound`
   — cheese therefore spawns inside the first robot's turn, not at round start); then carried-rat
   bookkeeping (drop on grabber death or `MAX_CARRY_DURATION`), trap stun countdown, cooldown decay
   by `COOLDOWNS_PER_TURN`, king cheese consumption and starvation damage.
5. Run the body's controller: for a cat, the ported cat state machine; for a rat, the clan chassis
   under that clan's doctrine, spending at most its **decision budget** (§Sim module).
6. *End of turn*: apply the actions the controller committed, resolve deaths (a dying rat drops its
   raw cheese onto its tile), and emit this turn's replay actions.
7. After every body: *end of round* — record the per-team round stats (cheese transferred, cat
   damage, the packed `kings + 10 × teamCheese` stat, baby rats, dirt, rat traps, cat traps),
   advance `teamInfo`, close the round record, then check the end of match.
8. **End-of-match check**, in the engine's own order: (a) either team has **zero rat kings** → the
   other team wins outright (`KILL_ALL_RAT_KINGS`); (b) **all cats dead while still in
   cooperation** → decide by points, then total cheese, then living rats, then a seeded coin flip;
   (c) **round 2000 reached** → the same ladder. Otherwise the game continues.

### Scoring, sign, and what the league ranks by

Per game, from the final round's team stats:

```
share_cat  = f32(catDamage[t])        / f32(catDamage[A] + catDamage[B])          # 0 if total == 0
share_king = f32(kings[t])            / f32(kings[A] + kings[B])
share_chz  = f32(cheeseTransferred[t])/ f32(cheeseTransferred[A] + cheeseTransferred[B])
w = (0.5, 0.3, 0.2) if cooperation_at_end else (0.3, 0.5, 0.2)
points[t] = int(w0*100*share_cat + w1*100*share_king + w2*100*share_chz)     # TRUNCATION
```

Three details that are load-bearing and are pinned by test vectors:

- the shares are **narrowed through float32** before the weighted sum (the engine computes them as
  Java `float`), and only then truncated by the `(int)` cast — not rounded. The idea card's
  "round(...)" is implemented as truncation on purpose;
- `kings[t]` is the king **count**, and in the replay/oracle trace it arrives packed as
  `kings + 10 × teamCheese` (`GameWorld.java:1013`) — decode `% 10` and `// 10`;
- **`cooperation_at_end` is decided by scanning the per-round cooperation flag** (the sim's own
  `isCooperation`, and in the oracle trace `Turn.isCooperation`), **never** from the win type:
  `WinType` and `DominationFactor` disagree — a kill-all-kings win *after* a backstab still records
  `RATKING_DESTROYED`.

Match = best-of-three (see below). Per seat:

```
gamePoints[g]      = points as above for game g
gameWin[g]         = 1 if that game's winner is this seat else 0
results.scores[t]  = 100 * (games won) + mean(gamePoints over games actually played)
```

**Higher is better.** Points are in `[0, 100]` and the two seats' points sum to ~100, so the
100-per-game win bonus dominates — which is exactly "losing every rat king loses the game outright".
The league ranks by `results.scores` (Elo over the resulting ordering). A `deadline` episode scores
the games that finished; a `fault` episode scores `[0, 0]`.

### End conditions, `end_reason`, and `results.reason`

Per game (`results.games[].end_reason`): `kings_destroyed`, `cats_cleared`, `round_limit`.
Per episode (`results.reason`, the closed enum the platform reads):

| `results.reason` | when | scores |
|---|---|---|
| `complete` | the match played out (a side won 2 games, or all scheduled games finished) | as above |
| `deadline` | the match wall-clock guard fired mid-game: the unfinished game is discarded and the **finished games are scored**; if no game finished, `[0, 0]` | partial, honest |
| `fault` | a sim invariant tripped (a bug): a partial replay and `[0, 0]` are still written | `[0, 0]` |

`deadline` is **declared acceptable** for this coworld at phase-60 check 4. Container exit codes
follow ctf: `0` whenever results + replay were attempted (including `deadline`/`fault`), `2` on an
invalid config. `/healthz` and `/global` keep answering for a ~20 s shutdown grace after artifacts
are written (the lantern 0.1.3 scar), and the websocket handler keeps its `Ping → Pong` branch and
does **not** filter non-text frames (the lux-ai / snake-royale scar: the player registers with a
`BinaryMessage`).

### Match shape and budget — the arithmetic

`episodeTimeoutSeconds = 1200`; 60 % = **720 s**. The game container enforces its own caps:

```
container start, map load, seat connect              ≤  30 s   (connectTimeoutMs 25 000)
doctrine phase: ONE parallel batch of 2 LLM calls    ≤  45 s   (attempt1Ms 20 000 + retryMs 12 000
                                                                + parse/validate, hard cap
                                                                doctrineBudgetMs 45 000)
match: 3 games x 2000 rounds (perGameBudgetSeconds 90) ≤ 330 s (matchBudgetSeconds)
score + replay write + shutdown grace                ≤  30 s
                                                       -------
worst case                                             435 s   ≤ 720 s
```

**Best-of-three, on three different maps, is the v1 shape** — it fits, and the sim, not a JVM, is
what makes it fit. Honest estimate: coworld-ctf steps 5 000 physics ticks with 16 bodies inside a
few seconds; our per-round cost is a bounded chassis decision for ≤ ~120 live bodies with a capped
BFS, so a 2000-round game on a 60×60 map is **tens of seconds, not minutes**. Because that estimate
is an estimate, it is **enforced, not trusted**:

- `perGameBudgetSeconds = 90` and `matchBudgetSeconds = 330` are hard monotonic-clock guards. A game
  that blows its guard is abandoned; the finished games are scored and `results.reason = deadline`.
- `tests/test_perf.nim` (native, in the `test` CI job) plays a full 2000-round game on the largest
  pool map with both scripted chassis and **fails CI at > 45 s**. If that gate ever goes red, the
  fix is one config value — `gamesPerMatch: 3 → 1` in the `bc26` variant — and the note says so
  here so the builder does not redesign anything.
- `maxGames` (3) also caps games actually played once a side reaches 2 wins, exactly as
  best-of-three implies.

There is exactly **one decision turn per episode**, so the "per-turn wall-clock budget" is the 45 s
doctrine phase, and both seats' calls go out as **one parallel batch** (`curly.makeRequests`,
ctf's `decide.nim` shape) — seats are never queried sequentially.

---

## Decisions: LLM with scripted fallback

**Where the decision happens.** As in paintbot, the player container is deliberately thin: it
connects to its seat, sends **one** registration blob and then only receives. Every decision happens
inside the **game** container, because that is the only container the platform injects the
`anthropic_api_key` coworld secret into (`game.runnable.env.ANTHROPIC_API_KEY_URI =
secret://coworld/battlecode/anthropic_api_key`), and because keeping the control layer server-side
is what makes the recorded doctrine reproducible with no network in the loop.

**One decision turn, one parallel batch.** Both seats are asked at the same moment and their two
provider calls are issued as **ONE parallel batch** (`curly.makeRequests`, ctf's `decide.nim`
shape) with the same deadline; seats are never queried one after another. The batch's wall-clock
budget is `doctrineBudgetMs = 45 000` — attempt 1 `attempt1Ms = 20 000`, the single retry
`retryMs = 12 000` — which is the "per-turn budget" for this game and sits inside the 720 s
(60 % of `episodeTimeoutSeconds`) envelope computed in §The game. Because there is exactly one turn
per episode, the whole match costs at most 2 provider calls per seat, far under the sidecar's
30 req/min per-episode cap.

`src/battlecode/llm.nim` is ported from `coworld-ctf/src/ctf/llm.nim` behaviour-for-behaviour: the
credential ladder (Bedrock sidecar → `ANTHROPIC_API_KEY` → `ANTHROPIC_API_KEY_URI`), the single
Bedrock candidate `us.anthropic.claude-haiku-4-5-20251001-v1:0` (no sonnet fallback — the raid and
paintball scars), fence-tolerant JSON extraction, the `throttled` fast-fail, rune-boundary
truncation, and `maxOutputTokens` (here **1200**: a sheet plus a short note, not code). With no
credentials the client disables itself and every seat falls back to its scripted doctrine
instantly, which is what lets offline certification finish in seconds.

### The doctrine sheet (v1: the JSON sheet **only** — no Java, no compilation of anything)

Each knob has a type, a range, a default, and a named site in **our** Nim chassis. Unknown key,
wrong type or out-of-range value → **that field's default**, recorded in `sheet_defaults_applied` /
`sheet_unknown_fields`. A sheet can never be rejected, so a cog can never forfeit.

| field | type / values | default | what it changes in the chassis (`src/battlecode/years/bc26/chassis/…`) |
|---|---|---|---|
| `chassis` | `"awu"` \| `"scaffold"` | `"awu"` | which ported bot drives the clan (`awu.nim` = distilled awubot, `scaffold.nim` = ported examplefuncsplayer) |
| `backstab_policy` | `never` \| `when_ahead` \| `at_round_N` \| `on_first_contact` \| `retaliate_only` | `retaliate_only` | `doctrine.hostilitiesOpen(round, state)` — gates the enemy-target list in `targets.nim`; with hostilities closed, enemy rats are simply not candidates for bite/ratnap/throw/rat-trap |
| `backstab_round` | int 1…2000 (read only for `at_round_N`) | 600 | same |
| `cat_engagement` | `avoid` \| `opportunistic` \| `hunt` \| `feed` | `opportunistic` | cat target weighting in `targets.nim`; `avoid` removes cats from the target list, `hunt` raises their weight above cheese, `feed` enables carrying rats to cats |
| `cat_trap_budget` | int 0…200 | 40 | `traps.nim` — stop placing cat traps once `liveCatTraps >= budget` |
| `rat_trap_budget` | int 0…200 | 60 | `traps.nim` — same for rat traps |
| `spawn_curve` | `lean` \| `steady` \| `swarm` (cheese threshold ×1.4 / ×1.0 / ×0.7) | `steady` | `king.nim` `spawnThreshold()` — how much banked cheese a king insists on before building another rat |
| `cheese_ferry_ratio` | float 0.0…1.0 | 0.5 | `rat.nim` role assignment: `ferry(id) = (id * 2654435761) mod 100 < ratio*100` picks miner vs skirmisher at spawn |
| `king_count_target` | int 1…5 | 3 | `formation.nim` — a four-rat formation only upgrades to a king while `liveKings < target` |
| `dirt_wall_policy` | `none` \| `king_shell` \| `choke` | `king_shell` | `dirt.nim` — no dirt work / wall the ring around each king / wall the two narrowest corridors on the seat's half |
| `throw_rats_to_feed_cats` | bool | `false` | `combat.nim` — allows the feed-a-carried-rat-to-a-cat play (only meaningful with `cat_engagement = feed`) |

Free-text fields (see the reply schema in §Server, player, protocol) carry hard caps; every
truncation is on **rune** boundaries.

**Every knob must have teeth.** `backstab_policy` is not allowed to be the only one that changes the
match: `tests/test_knob_sensitivity.nim` is a CI gate that proves each of the other nine visibly
changes play (§Tests), and the endcard reports the economic story — kings built, cheese delivered,
cats damaged, traps laid, dirt placed — beside the betrayal round.

### The two champion prompts (`PLAYER_PROMPT`; both champions are LLM policies)

- **champion #1, `battlecode-loyalist` (daveey)**: *"You command a rat clan. Your doctrine: honour
  the alliance. Never open hostilities first — set backstab_policy to \"retaliate_only\" or
  \"never\". Win on cat damage and cheese, which is where the cooperation weights (0.5 cat damage /
  0.3 kings / 0.2 cheese) pay. Hunt cats (cat_engagement \"hunt\"), spend cat traps freely, keep at
  least three kings alive so a betrayal you did not start cannot finish you, and keep a ferry
  running. In notes, say what would make you retaliate."*
- **champion #2, `battlecode-opportunist` (daveey-1)**: *"You command a rat clan. Your doctrine: the
  alliance is a means. Farm cats early while the cooperation weights pay, then betray at a moment
  you choose — set backstab_policy to \"when_ahead\" or \"at_round_N\" with a round you justify,
  remembering that after a backstab the weights become 0.3 cat damage / 0.5 kings / 0.2 cheese and
  that killing every enemy king wins outright. Bank rat traps before you turn, and keep your own
  king count at or above 3. In notes, say when and why you intend to turn."*

Both are appended to a shared system preamble carrying the rules digest, the sheet schema with every
default and range, the map card for all three games, the scoring formula with both weight sets, the
alias pair, and the reply contract ("reply with ONE JSON object; your reply must begin with `{`").
The assistant turn is prefilled with `{` and the prefix re-attached before parsing (the procgen
0.1.2 scar).

### Scripted baselines (`PLAYER_SCRIPTED=<name>`, same image)

`src/battlecode/baselines.nim` (ctf's `baselines.nim` role) answers the doctrine request from a
table, with no model and no network:

- **`awu`** (default, the strong one): `{"chassis": "awu"}` — every other knob at its default, i.e.
  the distilled-awubot behaviour: hunt cats opportunistically, ferry half the rats, three kings,
  king-shell dirt, retaliate-only. Algorithm: emit the fixed sheet, `notes: "default awu doctrine"`;
  never any other message.
- **`scaffold`** (the weak floor): `{"chassis": "scaffold"}` — the ported examplefuncsplayer
  behaviour: random legal move, bite whatever is adjacent, pick up cheese underfoot, no traps, no
  dirt, no formations.

Both replies go through the **same** `sheet.validate()` the LLM path uses, which is what makes the
bounded-orders legality test in §Tests meaningful, and what makes an LLM doctrine and a scripted one
strictly comparable.

### Degrade-never-hang

| failure | response |
|---|---|
| no LLM reply within `attempt1Ms` (20 000) | one retry with `retryMs` (12 000), logged `will retry` — never `falling back` |
| second failure, unparseable JSON, or a provider throttle with no other candidate model | that seat plays its **scripted doctrine** (`awu`), `results.fallbacks[seat] = 1`, a `doctrine_fallback` event names the cause, and the log line says `falling back` |
| doctrine phase exceeds `doctrineBudgetMs` | whatever is unresolved takes the scripted doctrine; the match starts anyway |
| a sheet field is unknown, mistyped or out of range | that field alone takes its default; the rest of the sheet applies |
| a seat never registers | it plays the scripted doctrine; the slot is reported to `COGAME_PLAYER_FAILURE_URI`, and the server **logs loudly** rather than silently defaulting (the grf-football scar) |
| a game exceeds `perGameBudgetSeconds`, or the match exceeds `matchBudgetSeconds` | the running game is abandoned, finished games are scored, `results.reason = deadline` |
| the match finishes early (a side takes 2 games) | the episode settles immediately — no padding |
| no credentials at all (certification, docker-smoke) | the LLM client disables itself at construction; both seats are scripted and the episode completes in seconds |

---

## Sim module

`src/battlecode/` is the deterministic sim, written to coworld-ctf's conventions and compiled
**twice** from the same sources: natively into `/bin/battlecode` (the game server) and to wasm into
`replay-viewer/dist/bc_replay.js|.wasm|.data` (the viewer). Nothing gameplay-related lives outside
it; the viewer never re-implements a rule.

| file | ctf counterpart | role |
|---|---|---|
| `sim_types.nim` | `src/ctf/sim_types.nim` | `GameVersion` + its prepend-only changelog, `GameName = "battlecode"`, `ReplayCompatibleGameVersions`, every gameplay type. **Flatty-serialized positionally into replay keyframes: field order is wire format.** |
| `rng.nim` | — (new) | the `java.util.Random` port (below) + the `IDGenerator` port |
| `years/registry.nim` | — (new) | `YearSpec` table; `game_config.year` selects one (v1: `bc26`) |
| `years/bc26/constants.nim` | — | all 69 `GameConstants` values + the `UnitType` / `TrapType` tables, **generated** (below) |
| `years/bc26/rules.nim` | `src/ctf/sim.nim` | the round loop and every rule: movement/turning/cooldowns, vision cones + chirality, cheese, kings, spawning, combat, ratnap/throw/feed, traps, dirt, formation, squeaks + the 64-int shared array, the backstab trigger, scoring, end conditions |
| `years/bc26/cats.nim` | — | the NPC cat state machine (explore/waypoints/chase/search/attack, BFS around walls, pounce/scratch/sleep) |
| `years/bc26/maps.nim` | `src/ctf/map_pool.nim` | the converted map pool + the per-episode draw |
| `years/bc26/chassis/*.nim` | `src/ctf/control.nim` | the two ported bots and the knob sites (`awu.nim`, `scaffold.nim`, `targets.nim`, `traps.nim`, `king.nim`, `rat.nim`, `formation.nim`, `dirt.nim`, `combat.nim`, `pathing.nim`) |
| `sheet.nim` | `src/ctf/directives.nim` | the doctrine schema, tolerant parse, per-field repair, rune caps |
| `decide.nim` | `src/ctf/decide.nim` | the one-shot sealed simultaneous doctrine batch, deadlines, fallbacks |
| `llm.nim` | `src/ctf/llm.nim` | ported behaviour-for-behaviour (see §Decisions) |
| `baselines.nim` | `src/ctf/baselines.nim` | the scripted doctrines |
| `broadcast.nim` | `src/ctf/broadcast.nim` | the JSON chrome channel (scorebug, feed beats, endcard payload) |
| `render.nim` | `src/ctf/global.nim` (board renderer) | bitworld sprite packets for the board, drawn from the sprite atlas in `data/` |
| `replay.nim` | `src/ctf/replays.nim` + `replay_codec.nim` | the **JSON** replay writer/reader (events + config + seed) and the re-derivation driver |
| `results.nim` | `src/ctf/decide.nim` results half | the closed results document |
| `server.nim` | `src/ctf/server.nim` | mummy + `bitworld/runtime`: `/healthz`, `/player`, `/global`, `/client/global`, `/client/player`, replay mode |
| `player.nim` | `src/paintball_player.nim` | the thin seat registrar → `/bin/battlecode-player` |

### Determinism

- **`rng.nim` reproduces `java.util.Random` exactly**: the 48-bit LCG (`seed = (seed ^ 0x5DEECE66D) &
  ((1 shl 48) - 1)`, `next(bits) = (seed * 0x5DEECE66D + 0xB) mod 2^48 >> (48 - bits)`), `nextInt()`,
  `nextInt(bound)` with the power-of-two shortcut **and** the rejection loop, `nextInt(lo, hi)`,
  `nextFloat()`, `nextDouble()`, `nextBoolean()`. `IDGenerator` is ported verbatim
  (`world/IDGenerator.java`: `ID_BLOCK_SIZE = 4096`, `MIN_ID = 10000`, Fisher–Yates over each block
  with the same `nextInt(i+1)` call order), so **robot ids match the Java engine's** for a given map
  seed — which is what makes the parity trace comparable row for row.
- The world RNG is seeded from the **map's own seed field** (`GameWorld.java:165`), exactly as the
  engine does; the episode seed selects maps and side assignment, never the world RNG.
- `setWinnerArbitrary`'s `Math.random()` is replaced by a draw from the world RNG (a divergence,
  listed in `docs/RULES.md`; it is reachable only on an exact three-way tie).
- Every round appends to a **hash chain** (ctf's `gameHash` discipline): the viewer re-derives each
  round and compares, exposing `bc_mismatch_round` exactly as ctf exposes `ctf_mismatch_tick`. Any
  wall-clock-driven fact (the `deadline` stop) is recorded as **one load-bearing record applied by
  the same proc on record and on playback** — the particle-worlds 2026-08-26 scar — and the
  record→re-derive test covers **every** end reason, not just `complete`.
- **`GameVersion` discipline is inherited verbatim** from `coworld-ctf/AGENTS.md`: a version is
  claimed across branches, not just against `main`; anything that changes what a policy sees or how
  a seat is scored bumps it in the same commit; `tools/ci/check_gameversion.sh` is kept.

### The constants generator (no hand transcription)

`tools/gen_year_constants.py` reads `common/GameConstants.java`, `common/UnitType.java` and
`common/TrapType.java` from a **pinned checkout of `engine.1.2.5`** and emits
`src/battlecode/years/bc26/constants.nim`. CI regenerates and diffs (`test` job): a drifted or
hand-edited constant fails the build. 69 constants plus the two enum tables come across mechanically;
only *behaviour* is hand-ported.

### The chassis, and the bytecode divergence

Both bots are ported **behaviour**, not code: `scaffold.nim` from `example-bots/…/examplefuncsplayer`
(random legal move, adjacent bite, pick up cheese, no construction) and `awu.nim` as a **distilled
awubot** — miner / skirmisher roles, king spawn thresholding, trap laying, dirt shells, formation
upgrades, squeak-shared mine locations, BFS pathing — with every knob in the sheet table above wired
to a named site.

The engine's per-robot **bytecode limit** (`UnitType.bytecodeLimit`: 17 500 rat / 20 000 king /
17 500 cat) has no meaning outside the JVM instrumenter. It is replaced by a **fixed per-robot
decision budget**: `DecisionOps` credits charged by the chassis for primitive steps (a sense, a BFS
node expansion, a candidate evaluation), `BABY_RAT 1500`, `RAT_KING 2500`, `CAT 800`, deducted
inside `pathing.nim`/`targets.nim` and enforced by the sim, not by the bot. When the budget runs out
the robot ends its turn where it stands. This makes per-round cost bounded, machine-independent and
deterministic. **It is a deliberate divergence and is documented as one** in `docs/RULES.md`
§Divergences, alongside: no `.class` instrumentation, no indicator strings/timeline markers, no
profiler, no crossplay, the seeded coin flip above, and the 4 000-HP cats (engine) vs the card's
10 000.

### Maps

The pool is the **43 official maps at tag `engine.1.2.5`** (re-verified: `Stash`, `uneasy_alliance`,
`Excavation` and `RUN` do **not** exist at that tag — they landed later on master — and are not
used). `tools/convert_maps.py` (CI-time; Java/Python allowed there, never at runtime) reads each
`.map26` with the schema's generated Python bindings and writes
`data/maps/bc26/<name>.json` — name, size, symmetry, `randomSeed`, walls, dirt, cheese, paired
cheese-mine locations, cat waypoint sets, initial bodies. **The converted maps are committed**; a CI
check re-converts and diffs. Verified sizes drive the pools:

| pool | maps (size, symmetry) |
|---|---|
| `small` (6) | `DefaultSmall` 30×30 rot, `arrows` 30×30 rot, `closeup` 30×30 rot, `toomuchcheese` 30×30 rot, `cheesefarm` 30×30 horiz, `dirtfulcat` 30×30 vert |
| `mixed` (12, the `bc26` variant's pool) | the six above + `ZeroDay` 40×34 rot, `knifefight` 40×40 vert, `whatsthecatdoin` 40×40 rot, `thunderdome` 45×35 rot, `DefaultMedium` 45×45 rot, `mercifullattice` 41×35 rot |
| `large` (6, reserved for a later variant) | `DefaultLarge` 60×60 rot, `Nofreecheese` 60×60 rot, `averystrangespace` 60×60 rot, `safelycontained` 60×60 vert, `streetsofnewyork` 60×60 vert, `uneruesansfin` 60×60 rot |

**Draw**: `seed` (from `game_config.seed`, or 32 random bits when it is 0) picks three *distinct*
maps from the variant's pool by successive `seed`-derived indices, and `(seed shr 8) and 1` decides
which slot takes side A for game 1; sides alternate each game. Seed, map names and side assignment
are recorded in results and in the replay.

### The year module (multi-year, amendment 2)

One repo, one coworld `battlecode`, **one manifest variant per Battlecode year**, one league per
year. Everything year-specific lives under `src/battlecode/years/<year>/` — constants, rules, cats,
chassis, map pool, sheet-knob definitions and the sprite set name — behind a `YearSpec` registered
in `years/registry.nim` and selected by **`game_config.year`** (v1: `"bc26"`, the only registered
year; an unknown year is a config error, exit 2). Year-neutral machinery (`rng`, `sheet` framework,
`decide`, `llm`, `broadcast`, `render`, `replay`, `results`, `server`) never branches on the year
except through the registry. Adding 2027 is: a new `years/bc27/` directory, a new converted map set,
a new sprite atlas, one registry line and one new manifest variant `bc27` — no fork, no second
coworld. The replay header records `year` so a viewer can never mis-derive an old recording.

---

## Server, player, protocol

Protocol id: **`cogame.battlecode.v1`**, documented in `docs/PROTOCOL.md`. Shape inherited from
paintbot.

### The player container (thin registrar)

`/bin/battlecode-player` reads `COWORLD_PLAYER_WS_URL` (legacy alias `COGAMES_ENGINE_WS_URL`),
dials its seat with a bounded retry (240 × 500 ms), sends **one** registration blob and then only
receives until the socket closes, then exits 0 (the raid 0.1.4 scar: a dead socket must exit 0, not
raise):

```json
{"type":"register","prompt":"<PLAYER_PROMPT or empty>","scripted":"awu"|"scaffold"|null,
 "policy":"<PLAYER_POLICY_LABEL>"}
```

sent as a Sprite v1 chat blob (a **binary** frame — the server must not filter non-text frames), and
re-sent a bounded number of times until acknowledged. A seat that sets neither env var is `awu`.
A seat whose registration never arrives is logged loudly and reported to
`COGAME_PLAYER_FAILURE_URI`.

### The doctrine exchange (server-side)

Because decisions are server-side, the "observation" is the prompt payload the server composes per
seat and records verbatim in the replay:

```json
{"protocol":"cogame.battlecode.v1","game_version":"GV01","year":"bc26",
 "slot":0,"alias":"Clan Ash","opponent_alias":"Clan Basil","team":"A",
 "seed":871345,
 "games":[{"map":"DefaultSmall","width":30,"height":30,"symmetry":"rotation",
           "cheese_mines":4,"cats":4,"rounds":2000,"you_are":"A"},
          {"map":"knifefight","…":"…","you_are":"B"},
          {"map":"DefaultMedium","…":"…","you_are":"A"}],
 "rules_digest":"<~6 KB condensed spec: rats, kings, cheese, cats, traps, dirt, ratnap, throw, squeaks, backstab, tiebreaks>",
 "sheet_schema":{"…every knob, its values, range and default…"},
 "scoring":{"cooperation":{"cat_damage":0.5,"kings":0.3,"cheese":0.2},
            "backstab":{"cat_damage":0.3,"kings":0.5,"cheese":0.2},
            "win_bonus_per_game":100,"games":3,
            "note":"shares are float32; points truncate to an integer"},
 "budget":{"attempt1_ms":20000,"retry_ms":12000,"one_shot":true}}
```

**Visible**: everything above — own alias and side, all three map cards, the seed, both weight sets,
the full knob surface with defaults, the deadlines. **Hidden**: the opponent's doctrine, sheet,
notes and motto (sealed and simultaneous — never sent, in either direction, at any time); the
opponent's real player name (only the alias); every in-match state (a cog receives **no** per-round
observation — one sealed doctrine, then the war); the other seat's fallback status. The only
cross-clan channel in the match is the sim's own squeaks and positions between robots.

### Reply schema and caps

```json
{"sheet":{"chassis":"awu","backstab_policy":"at_round_N","backstab_round":700,
          "cat_engagement":"hunt","cat_trap_budget":60,"rat_trap_budget":80,
          "spawn_curve":"swarm","cheese_ferry_ratio":0.4,"king_count_target":4,
          "dirt_wall_policy":"king_shell","throw_rats_to_feed_cats":false},
 "notes":"Farm cats to 700, then take their kings.",
 "motto":"Trust, briefly."}
```

| field | cap | on violation |
|---|---|---|
| whole reply | 16 KB | unparseable → retry once → scripted doctrine |
| `sheet` | ≤ 32 keys, each value type- and range-checked | bad field → that field's default |
| `notes` | **280 runes** | truncated |
| `motto` | **48 runes** | truncated |
| unknown sheet keys recorded | ≤ 16 keys, each ≤ 40 runes | truncated |
| provider error text stored in the replay | **200 runes** | truncated |

**Every cap is measured in runes and every truncation lands on a rune boundary**
(`runeLen`/`runeSubStr`, ctf's `directives.nim` rule): byte-slicing a multi-byte character renders
fine in a browser and then fails a strict UTF-8 parser, which is exactly what makes a replay
unreadable to everything but one lenient viewer.

### Results document (closed schema; == manifest `results_schema` == `docker_smoke.sh` key set)

`names` (real player names, seat order), `aliases`, `scores`, `wins`, `points` (per seat per game),
`games` (per game: `map`, `side`, `rounds_played`, `winner`, `end_reason`, `cooperation_at_end`,
`backstab_round`, `backstab_by`, `cat_damage`, `cheese_transferred`, `kings_alive`, `kings_built`,
`rats_built`, `rats_alive`, `traps_placed`, `dirt_placed`), `seed`, `year`, `policy_kind` (per seat
`llm|scripted`), `sheet_defaults_applied`, `fallbacks`, `decision_ms`, `sim_seconds`, `reason`
(`complete|deadline|fault`), `wall_clock_seconds`, `game_version`.

### Replay (`COGAME_SAVE_REPLAY_URI`) — one UTF-8 JSON document, self-sufficient

```jsonc
{"format":"cogame-battlecode-replay","version":1,"protocol":"cogame.battlecode.v1",
 "game_version":"GV01","year":"bc26",
 "config":{ /* the resolved game config, tokens EXCLUDED */ },
 "seed":871345,
 "aliases":["Clan Ash","Clan Basil"],
 "names":["daveey","daveey-1"],          // spectator-side only; agents never see these
 "seats":[{"slot":0,"alias":"Clan Ash","name":"daveey","policy":"llm",
           "sheet":{…as applied…},"sheet_submitted":{…as received…},
           "sheet_defaults_applied":["cat_trap_budget"],"sheet_unknown_fields":["swarm_mode"],
           "notes":"…","motto":"…","decision_ms":8123,"fallback":null}],
 "games":[{"index":0,"map":"DefaultSmall","map_json_sha256":"…","sides":["A","B"],
           "rounds":451,"hash_chain_sha256":"…"}],
 "events":[ … ],
 "result":{ /* identical to COGAME_RESULTS_URI */ }}
```

**Self-sufficiency is by re-derivation, not by bulk**: names, config, seed, the map identity (with a
sha256 of the committed converted map the bundle also ships), both doctrine sheets and the event
list are all in the file, and the wasm sim replays every round from them. No engine bytes, no
per-round state dump, no server contacted except S3 for the `.replay` file. The per-game hash chain
lets the viewer prove its re-derivation matches the recording (`bc_mismatch_round`).

### Event vocabulary carried by the replay

Pre-match events carry `ms`; in-match events carry `game` and `round`.

| `kind` | fields | drawn as |
|---|---|---|
| `episode_start` | `seed`, `year`, `maps`, `aliases` | feed line |
| `doctrine_requested` | `slot`, `attempt`, `deadline_ms` | feed line |
| `doctrine_received` | `slot`, `attempt`, `latency_ms`, `defaults_applied`, `unknown_fields` | feed line + beat `doctrine` |
| `doctrine_retry` | `slot`, `cause` (`timeout\|parse\|throttled`) | feed line (amber) |
| `doctrine_fallback` | `slot`, `cause` | feed line (red) + beat `doctrine` |
| `game_start` | `game`, `map`, `sides` | beat `game` |
| `king_built` / `king_lost` | `game`, `round`, `alias`, `kings_now` | beat `king` |
| `backstab` | `game`, `round`, `by_alias`, `trigger` (`bite\|ratnap\|throw\|trap`) | **chapter marker**: beat `backstab`, scorebug flips COOPERATION → BACKSTAB |
| `cat_down` | `game`, `round`, `by_alias` | beat `cat` |
| `game_end` | `game`, `round`, `winner_alias`, `end_reason`, `points`, `shares` | beat `end` |
| `episode_end` | `reason` | endcard |

---

## Viewer

The standard static wasm path, no exceptions: `"replay_viewer": {"bundle": "static-replay-viewer"}`,
built by `tools/build_replay_viewer.sh` (forked from coworld-ctf's, same containment checks, same
`docker build --target replay-viewer-builder` + `docker create` + `docker cp` shape, same
`sim_sources_stamp` guard so a stale committed bundle fails CI). The bundle contains **the same sim
module** compiled to wasm; the browser re-derives every round from the replay's events, config and
seed. No pod, no live viewer route, no engine bytes.

### All four viewer files come from ONE starter: `coworld-ctf`

| bundle file | source | treatment |
|---|---|---|
| `replay-viewer/config.nims` | `coworld-ctf/replay-viewer/config.nims` | copied; only the `-o` output name, the `--preload-file` directory and the `EXPORTED_FUNCTIONS` list are renamed `ctf_* → bc_*`. **No `MODULARIZE`, no `EXPORT_NAME`** — the link flags stay exactly as ctf's |
| the wasm entry `replay-viewer/bc_replay.nim` | `coworld-ctf/replay-viewer/ctf_replay.nim` | forked function-for-function: `bc_load_replay`, `bc_frame`, `bc_input`, `bc_packet_ptr/_len`, `bc_mismatch_round`, `bc_error_ptr/_len`, `bc_stage_ptr/_len`, `bc_game_version_ptr/_len`, `bc_sim_sources_stamp_ptr/_len`, the `stageNote` OOM buffer and the `emscripten_exit_with_live_runtime` main. It parses **our JSON replay** (jsony) instead of the bitreplay codec, then steps the shared sim and emits bitworld sprite packets |
| `replay-viewer/static_replay.js` + `static_replay_worker.js` | `coworld-ctf/replay-viewer/…` | copied; only the export names change. The worker keeps ctf's bootstrap **exactly**: a global `var Module = {}`, `Module.locateFile`, `Module.onAbort`, `Module.onRuntimeInitialized = start`, and `importScripts('./wire_constants.js', './broadcast_core.js', './bc_replay.js')` at the end of the file. Splicing an `onRuntimeInitialized` bootstrap onto `MODULARIZE`/`EXPORT_NAME` link flags is the cogame-lantern 2026-08-23 silent deadlock; both halves here come from this one starter |
| `index.html` | `coworld-ctf/client/replay_broadcast.html` | the starter's page **with a game block appended**, assembled by the same `sed` marker substitution ctf uses (`<!-- WIRE_CONSTANTS -->`, `<!-- CHROME_COMMON -->`, `<!-- BROADCAST_CORE --> → static_replay.js`). Its ids are kept as they are; nothing is rewritten and no id is reused for a different purpose (the cogame-gridlock 2026-08-23 scar) |

Also copied from the same starter: **`client/chrome_common.js` byte-for-byte** and
`client/broadcast_core.js` byte-for-byte (the board renderer that ingests the sprite packets;
`client/renderer.js` is this lineage's name for it and paintbot's copy is the exact template).
`wire_constants.js` is generated from the sim by `tools/gen_wire_constants.nim`, as in ctf.

**Starter elements removed from the appended page** (and only these): `#fpv*` (the first-person
picture-in-picture and its canvas/HUD/map), `#lockerroom` and `#lk-*` (the CTF pre-match art),
`#voteStage`/`#voteNote`/`#voteGrid`, `#huddleStage`/`#huddlePanel`/`#huddleFeed`/`#huddleChip`/
`#huddleLines`, `#gloryPops` and the glory numbers, `#commsdock`/`#commsFeed`/`#commsLive`,
`#momentum` and `#lulls` (CTF-specific scrub overlays), and the battle-royale `#cell-*` plates.
Everything else stays. The appended game block adds, inside the existing containers: `#coopchip`
(COOPERATION / BACKSTAB), `#bars` (the three-bar points breakdown per clan), `#econ` (kings built /
cheese delivered / cats damaged / traps / dirt), `#gamechips` (game 1-2-3 with each result), and
`#doctrines` (both sheets in plain words) — the beat feed rides the starter's existing `#killfeed`
element rather than inventing a new id.

### Load signalling

`static_replay.js` sets `document.documentElement.setAttribute('data-replay-loaded', 'true')` on the
**first drawn frame** (the worker's `loaded` message after the first board frame is composited —
never on rAF timing at the call site, the chorus 2026-08-24 scar), and the `coworld-replay` bridge
posts `ready` from a callback fired **after** that attribute is set. On any failure — fetch, JSON
parse, an unknown `game_version`, a wasm abort, a hash mismatch that prevents rendering — it sets
`data-replay-error="<message>"` on `<html>` and shows the failure card.

### Zoom: KEEP `#viewpanel`

Boards are 30×30–60×60 tiles. At the 360 px featured-match width a 60×60 board gives 6 px per tile,
and the native board render is 480–960 px wide — **larger than the frame**. So paintbot's
`#viewpanel` (zoom bar + minimap, with `?viewpanel=0` still honoured for thumbnail capture) is
**kept**, wired to the same `zoomAt/setZoom/panBy/panTo/resetView` core API the worker already
forwards. The default view is fit-to-board, so a spectator who touches nothing still sees the whole
map.

### Transport rules

- `relayout()` (ctf's own, kept) sets **`--hudscale`**, **`--topband`** and **`--band`** on `:root`,
  iterating to a fixed point so a map-aspect change cannot leave dead strips.
- **Nothing is overlaid in the transport band**: the board fits *between* the reserved top band
  (scorebug) and bottom band (transport).
- The **endcard stops at `var(--band)`** (`#endcard { bottom: var(--band) }`) and **every seek
  dismisses it**: `seek()` clears the card before moving the playhead.
- **Scrubber beats are clickable, labelled `<button>`s** with an `aria-label` and a `title`
  ("BACKSTAB — Clan Basil, game 2, round 612"), built by a game-block function with its **own name**
  (never `markBeat` — the tandem 2026-08-23 hoisting collision) and placed through
  `chrome_common.js`'s marker layer. CSS exists for **every kind emitted**: `.beat-marker.doctrine`,
  `.king`, `.backstab`, `.cat`, `.game`, `.end`.
- Transport controls keep the starter's ids: `#btn-restart`, `#btn-back`, `#btn-play`, `#btn-fwd`,
  `#btn-skip` (relabelled **+25 rounds**), `#btn-end`, `#btn-loop`, `#btn-spoilers`, `#speedchips`,
  `#tick-clock`, `#win-chip`, `#scrub` + `#scrub-fill`/`#scrub-head`/`#scrub-win`.

### Art

`data/atlas.png` + `data/atlas.json` (≈ 400 KB, committed), cut by `tools/build_sprite_atlas.py`
from the official Battlecode client's sprite tree (`battlecode26/client/src/static/img/**` at the
pinned commit): the 8-direction rat frames in two palettes (`cheddar` = Clan Ash, `plum` = Clan
Basil), the rat-king frames, the cat frames (walk, pounce, scratch, feed, sleep), cheese,
cheese mine, rat trap, cat trap, dirt. Credited in `NOTICE`; preloaded into the wasm via
`--preload-file data@data`, exactly as ctf preloads its `data/`. It looks like Battlecode because it
**is** Battlecode's art.

### Readouts, and 360 px

The viewer is **legible at 360 px wide** — the featured-match iframe width — and is checked at that
width, not at desktop width (`.plate-name { flex: 1 1 auto; min-width: 3.2em }`, labels hidden under
640 px, `#viewpanel` shrinking to its minimum before anything else).

- `#scorebug`: both clan plates — `CLAN ASH` over the real player name (`daveey`) and the motto —
  the live points number, `#bars` (cat damage / kings / cheese), and `#gamechips` (best-of-3 state).
- `#clock` / `#clock-time` / `#clock-caption`: `round 612 / 2000`, `game 2 of 3 — knifefight`.
- `#coopchip`: `COOPERATION` (green) → `BACKSTAB — Clan Basil, round 612` (red).
- `#board`: rats, 3×3 rat kings, cats, cheese and mines, rat/cat traps, dirt, squeak pings.
- `#econ`: kings built, cheese delivered, cats damaged, traps laid, dirt placed — per clan, live.
- `#doctrines`: each sheet in plain words ("betrays at round 700", "hunts cats", "80 rat traps",
  "swarm spawning", "keeps 4 kings"), plus the capped `notes` and a fallback badge when a seat's
  doctrine came from the scripted table.
- `#killfeed`: the event beats, revealed as the playhead reaches them (spoiler gate honoured).
- `#endcard`: winner alias **and** real name, the win condition in plain words ("Clan Basil
  destroyed every enemy rat king in game 3, round 612"), the per-game score line, the final
  three-bar points breakdown, **the economic story** (kings built, cheese delivered, cats damaged
  per clan) and who betrayed whom at which round — or "the alliance held".

---

## Packaging

- **`compose.yaml`** — service names are load-bearing (manifest placeholders derive from them:
  `game` → `{{GAME_IMAGE}}`, `player` → `{{PLAYER_IMAGE}}`, the lantern 0.1.0 scar):
  ```yaml
  services:
    game:
      image: cogame-battlecode-game:latest
      platform: linux/amd64
      build: {context: ., dockerfile: Dockerfile, network: host}
    player:
      image: cogame-battlecode-player:latest
      platform: linux/amd64
      build: {context: ., dockerfile: Dockerfile, target: player, network: host}
  ```
- **`Dockerfile`** — coworld-ctf's debian + nimby recipe (nimby 0.1.26, Nim 2.2.4,
  `nimby --global sync nimby.lock`, `nimby.lock` copied from the starter unchanged), building **two
  entrypoints from one image**: `/bin/battlecode` (game) and `/bin/battlecode-player` (seat
  registrar), plus `data/` (atlas + converted maps) and the built `static-replay-viewer` bundle.
  **No JDK, no JRE, no Java, no node in any runtime stage** — the parity oracle's toolchain exists
  only in CI. `Dockerfile.replay-viewer` is ctf's, with the sed block emitting our `index.html`.
- **`coworld_manifest_template.json`** — `game.name = "battlecode"` (== the secret namespace == the
  slug), `game.description` present, no `game.tags` (tags top-level only, ≥ 3: `battlecode`,
  `strategy`, `mixed-motive`, `wasm`), `$schema`, `episode_timeout_minutes: 20`,
  `game.runnable.type: "game"`, `run: ["/bin/battlecode"]`,
  `game.runnable.env.ANTHROPIC_API_KEY_URI = "secret://coworld/battlecode/anthropic_api_key"`
  (server-side LLM — without it every hosted episode plays scripted, the hive 2026-08-23 scar),
  `game.replay_viewer.bundle = "static-replay-viewer"`, `game.config_schema` a real JSON Schema with
  `minItems`/`maxItems` on **every** array (`tokens`, `players`) and no runner-managed `tokens`
  inside any `game_config`, `game.results_schema` the closed set above, bundled `player[]` at top
  level with `resources.limits.cpu: "1"`.
  - `game.protocols` — **both** keys as objects: `player` and `global`, each
    `{"type":"uri","value":"…/blob/main/docs/PROTOCOL.md"}`.
  - `game.docs` — `readme` = `{"type":"uri","value":"…/blob/main/README.md"}`; `pages` =
    `rules.md` (Rules, knobs and deliberate divergences → `docs/RULES.md`), `replay.md` (Replay
    format → `docs/REPLAY.md`), `parity.md` (The Java oracle and what it proves →
    `docs/PARITY.md`).
  - `player[]`: `awu` ("distilled-awubot baseline on its default doctrine") and `scaffold`
    ("scaffold baseline — the ported example bot, weak"), both `image: {{PLAYER_IMAGE}}`,
    `run: ["/bin/battlecode-player"]`.

  **Variants — one per Battlecode year; v1 ships exactly one:**

  | variant id | name | `game_config` | `num_agents` |
  |---|---|---|---|
  | `bc26` | Battlecode 2026 — Uneasy Alliances (2 seats) | `year: "bc26"`, `pool: "mixed"`, `gamesPerMatch: 3`, `seed: 0`, `attempt1Ms: 20000`, `retryMs: 12000`, `doctrineBudgetMs: 45000`, `perGameBudgetSeconds: 90`, `matchBudgetSeconds: 330`, `connectTimeoutMs: 25000`, `players: [{"name":"Clan Ash"},{"name":"Clan Basil"}]` | **2** |

  **Certification fixture** — seats **both** declared player entries (the raid 0.1.3 rule):
  `certification.players = [{"player_id":"awu"},{"player_id":"scaffold"}]`, and
  `certification.game_config = {"players":[{"name":"Clan Ash"},{"name":"Clan Basil"}],
  "num_agents": 2, "year": "bc26", "pool": "small", "seed": 1, "gamesPerMatch": 1,
  "maxRounds": 400, "attempt1Ms": 4000, "retryMs": 2000, "doctrineBudgetMs": 9000,
  "perGameBudgetSeconds": 40, "matchBudgetSeconds": 45, "connectTimeoutMs": 15000}`. With no
  credentials both seats are scripted and answer instantly, so the fixture is
  ~10 s connect + ~1 s doctrine + one 400-round game + artifacts ≈ **under 40 s**, inside
  `coworld certify`'s 60 s default; the release workflow still passes `--timeout-seconds 300` for
  headroom. A 400-round game plays for ~30 s at the default pace, so the replay outlasts the 10 s
  viewer soak (the ecos 2026-08-23 scar).

- **`tools/ci/policies.json`** — two LLM champions, two scripted fillers (a scripted champion is a
  failure state; filler versions must differ from champion versions):
  ```json
  [{"name":"battlecode-loyalist","run":"/bin/battlecode-player",
    "env":{"PLAYER_PROMPT":"<champion #1 text>","PLAYER_POLICY_LABEL":"loyalist"}},
   {"name":"battlecode-opportunist","run":"/bin/battlecode-player",
    "env":{"PLAYER_PROMPT":"<champion #2 text>","PLAYER_POLICY_LABEL":"opportunist"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"battlecode-awu","run":"/bin/battlecode-player",
    "env":{"PLAYER_SCRIPTED":"awu","PLAYER_POLICY_LABEL":"awu"}},
   {"name":"battlecode-scaffold","run":"/bin/battlecode-player",
    "env":{"PLAYER_SCRIPTED":"scaffold","PLAYER_POLICY_LABEL":"scaffold"}}]
  ```
  (LLM credentials reach the **game** container through the manifest env above; the player pods need
  no Bedrock sidecar in this lineage.)
- **Licensing**: `LICENSE` = AGPL-3.0. `NOTICE` credits `battlecode/battlecode26` (rules, constants,
  maps, sprite art — AGPL-3.0, tag `engine.1.2.5`) and `awu7/battlecode-2026` (the strategy ideas the
  `awu` chassis distils, AGPL-3.0, branch `final`), naming the pinned commits and stating that this
  repo contains **no** upstream Java source at runtime.

---

## Tests

Everything runs in `.github/workflows/ci.yml`, forked from `coworld-builder/templates/ci.yml`
(substitutions: `<slug>` = `battlecode`, `<IMAGE>` = `cogame-battlecode`, `<SEATS>` = **2**), with
**one job added** (`parity-oracle`). The sandbox runs none of it; CI is the harness.

**`test` job — native Nim (`nim c -r tests/tests.nim`, ctf's shard layout):**

1. `test_rng.nim` — the `java.util.Random` port against **recorded Java vectors**
   (`tests/fixtures/java_random_vectors.json`, generated by a tiny JDK program; the sandbox has a
   working JDK 21, so vectors are regenerated locally as well as in CI): `nextInt()`,
   `nextInt(bound)` including the rejection path, `nextInt(lo,hi)`, `nextFloat`, `nextDouble`,
   `nextBoolean` over 10 000 draws from 5 seeds, plus `IDGenerator` id sequences.
2. `test_constants.nim` — `years/bc26/constants.nim` is byte-identical to a fresh run of
   `tools/gen_year_constants.py` against the pinned engine checkout.
3. `test_maps.nim` — every committed converted map re-converts identically; sizes/symmetry match the
   table in §Sim module; cheese mines are symmetry-paired; cat waypoints exist.
4. `test_rules_*.nim` (one shard per rule family) — cooldowns and the −10 decay, vision cones and
   chirality, cheese spawn probability and symmetric pairing, carry slowdown, king consumption and
   starvation, spawn cost curve, bite damage with cheese boost, ratnap/throw/collateral/feeding,
   both trap types (limits, radii, stun, the post-backstab cat-trap rule), dirt dig/place, formation,
   squeaks and the 64-int array, the cat state machine, the backstab trigger from each of its four
   causes.
5. `test_scoring.nim` — the points formula with **float32 narrowing and truncation**, both weight
   sets, zero-total shares, the packed `kings + 10*cheese` decode, the full tiebreak ladder, and the
   rule that `cooperation_at_end` comes from the round flags, never the win type. Includes the
   vector harvested from a real Java match (`peaceinourtime`: catDamage 4000/4000, cheese 1590/2940,
   packed kings 17231/19732 → 1 and 2 kings → **42 / 57**, winner Team B).
6. `test_sheet.nim` — every knob: default when absent, out of range, mistyped; unknown keys recorded
   and ignored; rune-boundary truncation of `notes`/`motto` including astral-plane characters.
7. `test_baselines.nim` — **bounded-orders / legality on the scripted baselines**: both
   `PLAYER_SCRIPTED` values produce a sheet that passes the *same* `sheet.validate()` the LLM path
   uses, every key known, every value in range, `notes`/`motto` under cap; and, in a played game,
   every action the scripted chassis emits is legal for the acting robot (no action off cooldown, no
   out-of-range placement, no move into a wall).
8. `test_determinism.nim` — same seed + same sheets ⇒ identical hash chain, twice in one process and
   across a save/load; and **record → re-derive for every end reason** (`kings_destroyed`,
   `cats_cleared`, `round_limit`, and the wall-clock `deadline` stop applied by the same proc on
   both paths — the particle-worlds scar).
9. `test_replay.nim` — the replay document round-trips; a **strict UTF-8 parse** of the written
   bytes; the viewer's re-derivation of a recorded match reproduces the recorded per-round hashes.
10. `test_knob_sensitivity.nim` — **the knob-teeth gate**. For each of the nine non-`backstab_policy`
    knobs, play a paired set of seeded games (identical seed, map and opponent; the two clans
    identical except that knob at its low and high setting, 3 seeds each) and assert a named,
    signed stat delta: `spawn_curve` lean→swarm ⇒ rats built +25 % or more; `king_count_target` 1→5
    ⇒ kings built +2 or more; `cheese_ferry_ratio` 0.1→0.9 ⇒ cheese delivered +20 % or more;
    `cat_trap_budget` 0→80 ⇒ cat traps placed +20 or more; `rat_trap_budget` 0→120 ⇒ rat traps
    placed +20 or more; `dirt_wall_policy` none→king_shell ⇒ dirt placed +20 tiles or more;
    `cat_engagement` avoid→hunt ⇒ cat damage +30 % or more; `throw_rats_to_feed_cats` false→true ⇒
    at least one cat fed; `chassis` scaffold→awu ⇒ the awu side wins at least 5 of 6. The test fails
    if any knob is inert, and the thresholds live in one table so tuning is a one-line change.
11. `test_perf.nim` — a full 2000-round game on the largest pool map with both scripted chassis
    completes in **≤ 45 s**; failing it means switching `gamesPerMatch` to 1 (§The game).
12. `test_manifest.nim` — the triple-sync tripwire: results keys + `reason` enum == manifest
    `results_schema` == the key set `tools/ci/docker_smoke.sh` asserts; `num_agents` present in the
    `bc26` variant's `game_config` **and** `certification.game_config` and **absent** at variant top
    level; every `config_schema` array bounded; no `tokens` in any `game_config`; both
    `game.protocols` keys and `game.docs.readme`+`pages` are `{type,value}` objects; and the
    installed `coworld` CLI's own `validate_upload_manifest`/`_load_template_manifest` accepts the
    template.
13. `test_viewer.nim` + `tools/wasm_replay_smoke.cjs` — the emitted wasm module loads under node and
    answers `bc_load_replay`/`bc_frame` on the committed fixture replay; the game block does not
    shadow any `ChromeCommon` alias (the tandem scar); `chrome_common.js` and `broadcast_core.js`
    match the starter's copies by sha256.

**`parity-oracle` job — the Java engine as a CI-only oracle (phase-30 gate):**

Java 21 + `battlecode26-java-1.2.5.jar` (from `releases.battlecode.org/maven`, which resolves fine)
runs the **scaffold** bot against itself headless on **5 (map, seed) pairs** from the `small` pool;
`tools/parity_trace.py` reads the `.bc26` with the schema's Python bindings and emits a per-round
trace (robot ids, positions, hp, raw/global cheese, all three cooldowns, direction, cat state and
target, cheese-mine spawns, team cat damage / cheese transferred / packed king stat,
`Turn.isCooperation`). `tools/parity_trace.nim` emits the same trace from the Nim sim driving the
ported scaffold behaviour, and the job diffs them at three tiers:

- **Tier A (blocking):** rounds 1–50 are **bit-exact** on all 5 pairs — every field above, every
  robot, every round, including ids (which is why `IDGenerator` is ported).
- **Tier B (blocking):** at round 200, winner, end reason and every score term agree exactly, and
  cumulative cat damage / cheese transferred / king counts agree exactly.
- **Tier C (reported, trended, non-blocking):** the first divergent round over a full 2000-round
  game is printed and written to the job summary, with a committed baseline so a regression is
  visible.

Tiers A and B are the **phase-30 gate**. Every accepted divergence is listed in `docs/RULES.md`
§Divergences with its reason (decision budget, no instrumenter, seeded coin flip, no indicator
strings/profiler/crossplay). The oracle's toolchain exists **only** in this job — the image has no
JDK.

**`docker-smoke` job** — build the production image, then `tools/ci/docker_smoke.sh` (the
coworld-builder template, `<SEATS>` = 2): one game container + two player containers on a shared
network, driven from the certification fixture, `file://` artifact URIs, no `ANTHROPIC_API_KEY` (so
both seats take the scripted path and must still complete). Asserts: game exits 0, **every player
container exits 0**, `results.json` has exactly the closed key set, `reason == "complete"`,
`scores` has 2 entries, `fallbacks == [0, 0]`, the replay parses as **strict UTF-8 JSON** with
`format == "cogame-battlecode-replay"` and a non-empty `events` array, and the replay is copied to
`dist/smoke/replay.json` and uploaded as the `smoke-replay` artifact.

**`wasm-viewer` job** — `./tools/build_replay_viewer.sh "$PWD/dist/static-replay-viewer"`, assert the
bundle is complete (`index.html`, a non-empty `.wasm`, `bc_replay.js|.data`, `chrome_common.js`,
`broadcast_core.js`, `static_replay.js`, `static_replay_worker.js`, `wire_constants.js`), then
**execute** it: `node tools/ci/viewer_smoke.mjs --bundle dist/static-replay-viewer --replay
dist/smoke/replay.json --timeout 90 --soak 10` in headless chromium (Playwright pinned 1.55.0),
requiring `data-replay-loaded="true"` (or the bridge `ready` posted after it), three **differing**
clock/scorebug readouts at 0 % / 50 % / 100 %, and continued advancement across the soak.
**`--strict-text-bounds` is deliberately dropped here** — the board is pannable/zoomable
(`#viewpanel` is kept), which is the exact case the flag's own documentation excludes; the
`canvas_text` counts are still recorded in `viewer-smoke.json`, and a separate step runs
`tools/ci/renderer_fixture.html` (full-cap `notes` and `motto` on both seats at several canvas
sizes) through the same harness, because a CI replay is always scripted and carries no LLM text (the
cogchemists 2026-08-24 scar).

---

## Out of scope (v1)

- **Any Java at runtime.** No JVM, no JDK, no `.class` instrumentation, no in-container compilation
  of anything a cog sends. The Java engine exists only in the `parity-oracle` CI job.
- **A cog-authored strategy class.** v1's doctrine is the JSON sheet only. (A future year may add a
  sandboxed Nim/DSL strategy hook; nothing in the schema is closed against it.)
- **Battlecode years other than 2026.** The year module, `game_config.year`, the variant naming and
  the registry all exist in v1, but only `bc26` is registered and only one league is created.
- **awubot's 72 community maps and the 31 official maps outside the three pools.** The converter
  handles any `.map26`; v1 draws only from the 24 pool maps whose sizes and timings are pinned here.
- **Crossplay (Python bots), the engine profiler, indicator strings, timeline markers and
  `speedscope`.** None of them exist in the port.
- **The official Battlecode web client at runtime.** Its *sprites* are reused (credited); its React
  app is not shipped, not embedded and not built.
- **Live spectating of an in-progress match.** `/global` carries the phase and the result; the
  watchable artifact is the recorded replay re-derived in the browser.
- **Per-round cog interaction of any kind** — no mid-match observations, no doctrine amendments, no
  messages between cogs. One sealed doctrine, then the war.
