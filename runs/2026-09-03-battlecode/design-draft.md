# cogame-battlecode — design note (2026-09-03)

**Starter: `cogame-factorio`** (mounted read-only at `/workspace/starters/cogame-factorio`, forked
into `Metta-AI/cogame-battlecode`). Reason, by game shape: the rules live in an **external engine
process** (the unmodified MIT `battlecode26` Java engine) that the game container starts, waits on
and harvests artifacts from — the exact shape cogame-factorio was written for (Python aiohttp game
server, per-episode external engine child process, env-switched player containers, closed
`results_schema`, static replay bundle). **Every convention there holds here unless this note says
otherwise**: the `COGAME_*` runtime contract, `contract.py` as the single home for wire strings,
the four-surface rename rule, the "degrade never hang" rule, the `players/client.py` harness, the
`tools/ci/docker_smoke.sh` shape, the `tools/build_replay_viewer.sh` hook, and the `client/` chrome.

Everything in this note was checked against the real artifacts: the engine source and maps
(`github.com/battlecode/battlecode26`, `engine_version.txt` = **1.2.5**), awubot (`github.com/awu7/battlecode-2026`,
branch `final`), the official TypeScript client (`client/`), and **seven real headless matches run in
the sandbox** with `battlecode26-java-1.2.5.jar` + awubot's compiled classes (timings in
§The game). Line references below are to those trees at those revisions.

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

### Design pins (`playbooks/make-coworld.md` §Phase 0) — how each is satisfied

| Pin | Satisfied by |
|---|---|
| Starter by game shape | `cogame-factorio` — external engine in a child process, Python game server, env-switched players (§The game, first paragraph). |
| Public repo `Metta-AI/cogame-<slug>` | `Metta-AI/cogame-battlecode`, public, licence **AGPL-3.0** (engine + awubot are AGPL; a public repo is also how we discharge AGPL source-offer). |
| LLM policy **and** scripted baseline from day one, same image, env-switched | One `player` image; `PLAYER_PROMPT=<doctrine brief>` → `players.llm_player`; `PLAYER_SCRIPTED=awubot\|examplefuncsplayer` → `players.scripted_player` (§Decisions). |
| Static wasm replay viewer, never a pod | `replay_viewer.bundle = static-replay-viewer` + `tools/build_replay_viewer.sh`. The one admissible exception is invoked (a Java engine cannot compile to wasm): the recorded `.bc26` **is** the static artifact and the bundle plays it back in the browser. No `/client/replay` live viewer is ever declared (§Viewer). |
| Real art, starter chrome verbatim | `cogame-factorio/client/chrome_common.js` copied **byte-for-byte**; `index.html` is `cogame-factorio/client/replay_broadcast.html` **with a game block appended**; the art is the official Battlecode client's own sprite set (`client/src/static/img/**`), not placeholders (§Viewer). |
| Two name spaces | In-game aliases **Clan Ash / Clan Basil** (they are literally the engine's team names, `-Dbc.game.team-a="Clan Ash"`); real player names appear only in the replay envelope and only the viewer draws them (§Server, protocol; §Viewer). |
| Degrade never hang, inside 60 % of `episodeTimeoutSeconds` | Every wait is bounded; total worst case **700 s ≤ 720 s** with the arithmetic written out in §The game "Budget". |
| `num_agents` in every variant and the cert fixture | `num_agents: 2` inside `game_config` of all three variants **and** `certification.game_config` (§Packaging). Never at variant top level. |
| Upload policies before `upload-coworld`; secret after; fillers ≠ champions; fillers before first trigger | Release template unchanged from `templates/coworld-release.yml`; policy set listed in §Packaging. |

---

## The game

**Battlecode 2026 "Uneasy Alliances", played by doctrine.** Two cogs each command a clan of robot
rats. Neither cog moves a rat. At t=0 each writes a **doctrine** — a JSON strategy sheet plus an
optional Java strategy class — and the unmodified `battlecode26` engine then plays the entire
match from those two doctrines while both cogs watch. The whole strategic question is the
cooperate/betray bit: both clans start in COOPERATION against the NPC cats and the points formula
is cat-damage-weighted; the moment either clan turns on the other, the engine flips to BACKSTAB
mode and the formula reweights toward king survival.

**Seats: `num_agents = 2`, always.** Slot 0 = Team A = **Clan Ash**; slot 1 = Team B = **Clan
Basil** (side assignment permuted by the episode seed; see step 2 below).

### What the engine does (facts, from the pinned source)

- `GameConstants.GAME_MAX_NUMBER_OF_ROUNDS = 2000`; `MAX_NUMBER_OF_RAT_KINGS = 5`
  (`MAX_NUMBER_OF_RAT_KINGS_AFTER_CUTOFF = 2` after `RAT_KING_CUTOFF_ROUND = 1200`);
  `INITIAL_TEAM_CHEESE = 2500`; `RAT_KING_CHEESE_CONSUMPTION = 2` per round with
  `RAT_KING_HEALTH_LOSS = 10` when unfed; `CAT_TRAP_ROUNDS_AFTER_BACKSTAB = 100`.
- Points (`GameWorld.setWinnerIfMorePoints`, engine 1.2.5, lines 911–945):
  `points(team) = (int)(w_cat*100*share_cat_damage + w_king*100*share_alive_kings + w_cheese*100*share_cheese_transferred)`
  with `(w_cat, w_king, w_cheese) = (0.5, 0.3, 0.2)` in cooperation and `(0.3, 0.5, 0.2)` after a
  backstab. Shares are that team's amount over both teams' total; a zero total gives share 0.
  **The cast is a truncation, not a round** — we mirror the engine exactly, so the idea's
  "round(...)" is implemented as `int()` truncation and the note says so on purpose.
- Terminal conditions, in the engine's own order (`GameWorld.checkWin` / `checkEndOfMatch`):
  (a) a team's rat kings all dead → the other team wins outright (`KILL_ALL_RAT_KINGS`);
  (b) all cats dead **while still in cooperation** → decide by points, then cheese, then living
  rats, then a coin flip; (c) round 2000 reached → the same tiebreak ladder.
- The engine's RNG is seeded **from the map file** (`GameWorld.java:165`,
  `new Random(this.gameMap.getSeed())`), so a `(map, doctrine A, doctrine B)` triple replays
  identically. `-Dbc.game.seed` is accepted by awubot's gradle file but **ignored by engine
  1.2.5** — do not pretend otherwise. The only non-determinism is `setWinnerArbitrary()`'s
  `Math.random()`, reachable only on an exact three-way tie.
- The `.bc26` is a **gzipped flatbuffer** written once, at the end of the whole game queue
  (`Server.run` → `gameMaker.writeGame`). A JVM killed mid-match writes **nothing** — that fact
  drives the deadline handling below.
- Per-round team stats live in the `Round` table: `teamCatDamage`, `teamCheeseTransferred`,
  `teamAliveBabyRats`, `teamRatTrapCount`, `teamCatTrapCount`, `teamDirtAmounts`, and
  **`teamAliveRatKings` is a packed stat**: `numRatKings + 10 * teamCheese`
  (`GameWorld.java:1013`) — decode `kings = v % 10`, `cheese = v // 10`. The official client does
  exactly this (`client/src/playback/RoundStat.ts:82`, comment `//lmao`). Getting this wrong
  silently produces nonsense scores.
- `Turn.isCooperation` (schema line 422) is recorded per robot-turn, so the **backstab round** is
  derivable from the replay alone. The **initiator** is not in the schema, so the clan chassis
  emits it as a timeline marker (see §Sim module, "Doctrine layer"); `MatchFooter.timelineMarkers`
  carries markers only when `-Dbc.engine.show-indicators=true`, so that flag is **required**.

### Episode structure and exact resolution order

An episode is **one match = one game on one map** (v1: best-of-1; the idea authorises it and the
measured timings below force it). There is exactly **one decision turn**: the doctrine. The server
resolves, in this order:

1. **Load config** (`COGAME_CONFIG_URI`), validate against `config_schema`; exit 2 on invalid.
2. **Seed and draw.** `seed = game_config.seed` if non-zero, else `secrets.randbits(32)`; recorded
   in results and replay. `map = POOL[variant][seed % len(POOL[variant])]`;
   `team_a_slot = (seed >> 8) & 1` (so both seats play both sides across a round-robin).
   Read the `.map26` with the schema's Python bindings for the map card (name, w, h, symmetry).
3. **Serve** `/healthz`, `/player`, `/global`, `/client/global`, `/client/player`; wait for both
   seats to connect, bounded by `player_connect_timeout_seconds` (default 120).
4. **Send `welcome`** to each connected seat (rules digest, API digest, sheet schema, map card,
   alias, opponent alias, scoring formula with both weight sets, deadlines). Re-sent on reconnect.
5. **Doctrine request — ONE parallel batch.** The server sends `doctrine_request` (attempt 1) to
   **both seats in the same `asyncio.gather`**, with the same `deadline_seconds`
   (`doctrine_deadline_seconds`, default 90). Each player pod makes its own LLM call, so the two
   calls are concurrent by construction; there is no per-seat loop anywhere in the server.
6. **Collect and validate.** A reply is accepted if it is JSON, `type == "doctrine"`, and echoes
   the current `attempt`. Every sheet field is validated independently: an unknown key, a wrong
   type, or an out-of-range value **falls back to that field's default** and is recorded in
   `sheet_defaults_applied` / `sheet_unknown_fields`. A sheet can therefore never be rejected.
7. **Missing / malformed reply → retry once** (attempt 2, deadline
   `doctrine_retry_deadline_seconds`, default 60, again as one batch for whichever seats need it).
   A second failure → that seat plays the **scripted fallback doctrine** (`awubot` chassis, all
   defaults), `results.fallbacks[slot] = 1`, event `doctrine_fallback`.
8. **Compile the optional Java patch.** If `strategy_java` is present and ≤ 12 000 runes, write it
   to `<clan>/doctrine/CustomDoctrine.java`, run `javac` against the prebuilt chassis classes and
   `battlecode26-java-1.2.5.jar`, then `java battlecode.instrumenter.Verifier <team> <classdir>`.
   On failure the first 4 000 runes of the transcript go back to the seat as `compile_error` and
   the seat may submit again — **at most 3 submissions total per seat** (`max_compile_attempts`).
   After the third failure the Java patch is dropped and the sheet alone applies
   (`java_dropped`, reason `compile`). Both seats' compile loops run in the same batch.
9. **Hard cap on everything above.** The whole doctrine phase is bounded by
   `doctrine_phase_budget_seconds` (default 240). When it expires, whatever is unresolved falls
   back to defaults and the phase ends. Nothing here can hang.
10. **Emit the two clan packages.** Each seat's `Doctrine.java` (constants from its sheet) and, if
    it compiled, its `CustomDoctrine.java` are written into that seat's clan package
    (`clanash` / `clanbasil`) and compiled; the rest of the chassis is already compiled in the
    image (§Sim module).
11. **Run the engine.** One `java … battlecode.server.Main -c=-` child process, headless, one map,
    `-Dbc.server.save-file=<workdir>/match.bc26`, stdout/stderr captured to the episode log.
    Bounded by `engine_wall_clock_seconds` (default 400): on expiry the JVM is SIGKILLed.
12. **Harvest.** Read `match.bc26` (gunzip → flatbuffer): `GameHeader` teams, `MatchHeader.map`,
    every `Round` (team stats + `Turn.isCooperation`), `MatchFooter` (winner, `winType`,
    `totalRounds`, `timelineMarkers`), `GameFooter`.
13. **Score** (formula below), build the results doc and the replay envelope (with the raw
    `.bc26` base64 in `match_b64`), broadcast `done` to every connected player **before** writing
    artifacts, write `COGAME_RESULTS_URI` and `COGAME_SAVE_REPLAY_URI` independently and
    aggregate errors (factorio rule 3).
14. **Linger** answering `/healthz` and `/global` for a 20 s shutdown grace (lantern 0.1.3), then
    `exit 0`.

### Scoring, sign, and what the league ranks by

For each seat, from the **last recorded `Round`** in the `.bc26`:

```
share_cat  = catDamage[t]        / (catDamage[A] + catDamage[B])            # 0 if total == 0
share_king = kings[t]            / (kings[A] + kings[B])                    # kings = teamAliveRatKings % 10
share_chz  = cheeseTransferred[t]/ (cheeseTransferred[A]+cheeseTransferred[B])
w = (0.5, 0.3, 0.2) if cooperation_at_end else (0.3, 0.5, 0.2)
points[t]  = int(w[0]*100*share_cat + w[1]*100*share_king + w[2]*100*share_chz)   # truncation, as the engine
score[t]   = points[t] + (100 if MatchFooter.winner == t else 0)
```

`cooperation_at_end` is false iff any recorded round has a turn with `isCooperation == false`
(equivalently `MatchFooter.winType == BACKSTAB_RATKING_DESTROYED`). **Higher is better**; `points`
lies in `[0, 100]` and the two seats' points sum to ~100, so the 100-point win bonus dominates —
which is precisely the idea's "losing every rat king loses the game outright". The league ranks by
`results.scores` (Elo over the resulting win/loss ordering). A `deadline` or `engine_error`
episode scores `[0, 0]`.

### End conditions, `end_reason`, and `results.reason`

`results.end_reason` (closed enum, mirrored in `contract.py`, the manifest `results_schema` and
`docker_smoke.sh`):

| `end_reason` | when | scores | `results.reason` reported to the platform |
|---|---|---|---|
| `complete` | the JVM exited 0 and `match.bc26` parsed | from the formula | `complete` |
| `deadline` | `engine_wall_clock_seconds` expired (JVM killed, no `.bc26`) **or** the doctrine phase budget expired with no engine start | `[0, 0]` | `deadline` — declared **acceptable** for this coworld (phase-60 check 4) |
| `engine_error` | the JVM exited non-zero, or wrote a `.bc26` that fails to parse | `[0, 0]` | `engine_error` |

Container exit codes follow factorio: `0` episode complete (artifacts attempted, including for
`deadline`/`engine_error`), `2` missing/invalid config, `1` only if the JVM or the JDK is missing
from the image (a host failure). A `deadline` episode still writes a replay envelope — with
`match_b64: null` and an endcard that says the engine ran out of wall clock — so the viewer never
gets a file it cannot render.

### Budget — the arithmetic, out loud

`episodeTimeoutSeconds = 1200`; 60 % = **720 s**. The game container never sees the timeout, so it
enforces its own caps:

```
container start + config + map read + seat connect   ≤  30 s
doctrine phase (doctrine_phase_budget_seconds)       ≤ 240 s   (90 s attempt 1 + 60 s retry
                                                                + ≤2 compile repairs, all batched)
engine run (engine_wall_clock_seconds)               ≤ 400 s
harvest + score + replay write + shutdown grace      ≤  30 s
                                                       -------
worst case                                             700 s  ≤ 720 s
```

**Measured engine wall clock** (this sandbox, one core, `battlecode26-java-1.2.5.jar`, awubot
`final` compiled classes, `-Xmx1g -XX:+UseSerialGC`):

| map | size | teams | rounds played | wall clock | `.bc26` |
|---|---|---|---|---|---|
| `DefaultSmall` | 30×30 | awubot vs awubot | 135 | **60 s** | 62.6 KB |
| `DefaultMediumCatless` | 45×45 | awubot vs afk | 161 | **26 s** | 52.7 KB |
| `DefaultMedium` | 45×45 | awubot vs awubot_quals | 184 | **63 s** | 187.6 KB |
| `DefaultLarge` | 60×60 | awubot vs awubot | 276 | **85 s** | 158.8 KB |
| `DefaultMedium` | 45×45 | awubot vs awubot | 332 | **74 s** | 131.4 KB |
| `peaceinourtime` | 35×50 | awubot vs awubot | 451 | **51 s** | 294.5 KB |
| `DefaultLargeCatless` | 60×60 | awubot vs awubot | 438 | **104 s** | 244.0 KB |

Fit: ≈ 25–50 s fixed (JVM start + instrumenting awubot's generated classes — `TryThrow.java` is
34 831 lines) plus ≈ 0.10–0.15 s per round. A pathological full-length 2000-round game extrapolates
to **≈ 350 s**, inside the 400 s cap; typical games end by king-kill in 130–450 rounds and take
**26–104 s**, so the *typical* episode finishes in ~2–4 minutes and settles early. `.bc26` sizes are
50–300 KB → ≤ ~400 KB base64 in the replay envelope. CI measures and asserts this (§Tests).

---

## Decisions: LLM with scripted fallback

**One decision per episode per seat: the doctrine.** Both seats are asked in **one parallel
batch** (step 5 above); each player container makes its own model call, so the two calls overlap.
At most **3** model calls per seat per episode (initial + retry + compile repairs are the same
budget of 3 submissions), far under the Bedrock sidecar's 30 req/min per-episode cap.

### The doctrine sheet (the knob surface)

Every field has a type, a range, a default, and exactly one gate site in the chassis. Unknown or
invalid → default (never a rejection, never a forfeit).

| field | type / values | default | gate site in the awubot chassis (`chassis/awubot/src/<clan>/…`) |
|---|---|---|---|
| `chassis` | `"awubot"` \| `"examplefuncsplayer"` | `"awubot"` | which prebuilt package the clan is generated from |
| `backstab_policy` | `"never"` \| `"when_ahead"` \| `"at_round_N"` \| `"on_first_contact"` \| `"retaliate_only"` | `"retaliate_only"` | `Doctrine.hostilitiesOpen(rc)`, consulted at the tail of `RobotTracker.preTick()` (`RobotTracker.java:28`): when hostilities are closed the clan sets `numEnemies = 0` and `EnemyManager.numKnownEnemies = 0`, which starves `TryAttack` / `TryRatNap` / `TryTrap` / `TryThrow` of enemy targets in one place |
| `backstab_round` | int 1…2000 (only read when `backstab_policy == "at_round_N"`) | 600 | same |
| `cat_engagement` | `"avoid"` \| `"opportunistic"` \| `"hunt"` \| `"feed"` | `"opportunistic"` | same tail: `avoid` sets `numCats = 0`; `feed` also enables `throw_rats_to_feed_cats` |
| `cat_trap_budget` | int 0…200 | 40 | `BabyRat.considerPlacingCatTrap()` (`BabyRat.java:34`) — early-return when `rc.getNumberCatTraps() >= budget` |
| `rat_trap_budget` | int 0…200 | 60 | `TryTrap.run()` / `TryTrap.miniRun()` entry — return false when `rc.getNumberRatTraps() >= budget` |
| `spawn_curve` | `"lean"` \| `"steady"` \| `"swarm"` (×0.7 / ×1.0 / ×1.4) | `"steady"` | `KingSpawningStrategy.runTick()` `defaultThresh` (`KingSpawningStrategy.java:24`) |
| `cheese_ferry_ratio` | float 0.0…1.0 | 0.5 | `BabyRat.init()` (`BabyRat.java:24`) — `primaryStrategy = ferry(id) ? new MinerStrategy() : new ExploreStrategy()`, `ferry(id) = ((id*2654435761) >>> 32) % 100 < ratio*100` |
| `king_count_target` | int 1…5 | 3 | `FormationStrategy.java:70` — skip `rc.becomeRatKing()` when `GlobalArray.countRatKings() >= target` |
| `dirt_wall_policy` | `"none"` \| `"king_shell"` \| `"choke"` | `"king_shell"` | `KingCombatStrategy.java:58` (`rc.placeDirt`) — `none` skips, `choke` raises the placement radius by 2 |
| `throw_rats_to_feed_cats` | bool | false | `TryThrow.run()` entry (`CombatStrategy.java:189`) |

Plus the free-text fields, each with a hard cap (see the reply schema in §Server, player, protocol).

### Champion policies (`PLAYER_PROMPT`, both LLM — a scripted champion is a failure state)

Both champions run `players.llm_player` on the **same image**, differing only in `PLAYER_PROMPT`.
Model: `claude-haiku-4-5` via the hosted Bedrock sidecar (`USE_BEDROCK: "true"` **must** be in the
policy env — factorio-lineage policies are player-side LLM and the sidecar is gated on it; without
it the seat silently plays scripted, cogolf 2026-08-24). `max_tokens = 6000` (a Java class fits;
900 does not), the assistant turn is **prefilled with `{`** and the prefix re-attached before
parsing (procgen 0.1.2), and the system prompt demands the reply **begin with `{`**.

- **champion #1, `battlecode-loyalist` (daveey)** — `PLAYER_PROMPT`:
  `"You command a rat clan. Your doctrine: honour the alliance. Never open hostilities first;
  set backstab_policy to \"retaliate_only\" or \"never\". Win on cat damage and cheese, which is
  where the cooperation weights (0.5 cat damage / 0.3 kings / 0.2 cheese) pay. Hunt cats hard
  (cat_engagement \"hunt\"), spend cat traps freely, keep enough kings alive to survive a betrayal
  you did not start, and keep your cheese ferry running. Say in notes what would make you retaliate."`
- **champion #2, `battlecode-opportunist` (daveey-1)** — `PLAYER_PROMPT`:
  `"You command a rat clan. Your doctrine: the alliance is a means. Farm cats early while the
  cooperation weights pay, then betray at a moment you choose — set backstab_policy to
  \"when_ahead\" or \"at_round_N\" with a round you justify, remembering that after a backstab the
  weights become 0.3 cat damage / 0.5 kings / 0.2 cheese and that killing every enemy king wins
  outright. Bank rat traps before you turn, target their kings, and keep your own king count at or
  above 3. Say in notes when and why you intend to turn."`

Both prompts are appended to a shared system preamble that carries: the rules digest, the API
digest, the sheet's JSON Schema with defaults, the map card, the scoring formula with both weight
sets, the alias pair, and the reply contract ("reply with ONE JSON object, beginning with `{`").

### Scripted baselines (`PLAYER_SCRIPTED=<name>`, same image)

`players.scripted_player` reads `PLAYER_SCRIPTED` and answers the doctrine request from a table —
no model, no network:

- **`awubot`** (default, the strong one): `{"chassis":"awubot"}` and nothing else, i.e. every knob
  at its default → the awu7 `final` bot's own behaviour, unmodified. Algorithm: reply on the first
  `doctrine_request`, `strategy_java: null`, `notes: "default awubot doctrine"`; ignore any
  `compile_error` (it never sends Java); exit 0 on `done`.
- **`examplefuncsplayer`** (the weak floor): `{"chassis":"examplefuncsplayer"}` — the official
  scaffold bot from `battlecode26/example-bots`. Same one-shot reply algorithm.

Both are *bounded and legal by construction*: their replies are a fixed dict of in-range values,
which the legality test asserts field-by-field against the sheet schema (§Tests).

### Degrade-never-hang

| failure | response |
|---|---|
| no reply by `doctrine_deadline_seconds` | retry once (attempt 2, 60 s) → then scripted fallback doctrine, `fallbacks[slot] = 1` |
| reply is not JSON / wrong `type` / wrong `attempt` / > 64 KB | same path (counts as a malformed attempt) |
| a sheet field is unknown, mistyped or out of range | that field only falls back to its default; the rest of the sheet applies |
| `strategy_java` > 12 000 runes, or matches the source denylist (`java\.io`, `java\.net`, `java\.lang\.reflect`, `System\.exit`, `Runtime`, `ProcessBuilder`) | treated as a compile failure with a synthetic transcript; one repair attempt remains |
| `javac` / `Verifier` failure | transcript back to the seat, up to 3 submissions, then the sheet alone (`java_dropped`) |
| doctrine phase budget expires | unresolved seats take defaults; the engine starts anyway |
| engine exceeds `engine_wall_clock_seconds` | SIGKILL, `end_reason = deadline`, scores `[0,0]`, replay envelope with `match_b64: null` |
| a seat never connects | it plays the scripted fallback doctrine; the slot is reported to `COGAME_PLAYER_FAILURE_URI` |
| the episode finishes early (typical: engine done in 26–104 s) | the server settles immediately — no padding, no waiting |

Every fallback is loud: a `WARNING falling back` line in the container log **only** for a genuine
scripted fallback (a retry logs `will retry`, per the pommerman rule), plus a replay event.

---

## Sim module

There is no re-implemented simulation: the engine is the sim, unmodified. The "sim module" is the
Python package `server/cogame_battlecode/` that compiles doctrines, drives the JVM, reads the
`.bc26` and scores it. Forked file-for-file from `cogame-factorio/server/cogame_factorio/`:

| file | forked from | role |
|---|---|---|
| `contract.py` | factorio `contract.py` (keep the zero-import rule and the four-surface rename rule) | every wire string: `PROTOCOL = "cogame.battlecode.v1"`, message types, key tuples, `RESULT_KEYS`, `END_REASONS`, `SHEET_FIELDS`, caps |
| `config.py` | factorio `config.py` | `GameConfig` ↔ `config_schema` (seat names, tokens, `num_agents`, `variant_pool`, `seed`, all deadlines and budgets) |
| `sheet.py` | new | the sheet's JSON Schema, per-field validation with defaults, `sheet_defaults_applied` / `sheet_unknown_fields` reporting |
| `doctrine.py` | new | renders `Doctrine.java` from a sheet; writes/compiles `CustomDoctrine.java`; runs `javac` and `battlecode.instrumenter.Verifier`; truncates transcripts on rune boundaries |
| `engine.py` | factorio `engine.py` (deadlines/strikes → phase budgets) | the doctrine phase state machine and the JVM child process with its wall-clock guard |
| `bc26.py` | new | gunzip + flatbuffer read of `.bc26` and `.map26` using the **schema's own generated Python bindings** (vendored from `battlecode26/schema/python/battlecode/`, verified working in this sandbox); decodes the packed `teamAliveRatKings` (`% 10`, `// 10`), finds the backstab round from `Turn.isCooperation`, reads `MatchFooter` markers |
| `score.py` | new | the points formula above, byte-for-byte parity with `GameWorld.setWinnerIfMorePoints` including the `int()` truncation |
| `maps.py` | new | the three map pools and the seed draw |
| `replay.py` / `results.py` / `server.py` / `uris.py` / `version.py` | factorio, same names and shapes | replay envelope, closed results doc, aiohttp server, artifact URIs, `GAME_VERSION` with its prepend-only changelog (`GV01 (doctrine duel): first release`) |

### The chassis and the doctrine layer (what the image builds once, at build time)

- `chassis/awubot/` — awubot vendored at branch `final` (AGPL-3.0, `LICENSE` kept), Jinja already
  rendered, with the package renamed twice at **image build** time into `clanash` and `clanbasil`
  (a package rename + import rewrite; the engine loads a team by package name, so the two clans
  must be distinct packages). Both are compiled to classes in the image, so an episode only
  compiles the tiny per-seat doctrine files.
- `chassis/efp/` — `examplefuncsplayer` from `battlecode26/example-bots`, same double rename.
- `chassis/patch/` — the **doctrine layer**, the only edits to upstream code, all of them one-liners
  at sites verified in this note's table:
  1. `Doctrine.java` (generated per episode): `static final` knob constants + `hostilitiesOpen(rc)`
     + `tick(rc)`.
  2. `RobotPlayer.run` main loop: one added call `Doctrine.tick(rc);` right after
     `RobotTracker.preTick()` — it emits at most two timeline markers per team per match
     (`rc.setTimelineMarker("BACKSTAB by " + rc.getBackstabbingTeam(), 224, 82, 58)` the first
     round `rc.isCooperation()` is false, and `"DOCTRINE " + sheetDigest` at round 1).
  3. The eight gate sites in the table above, each a guard clause. **`BabyRat.java`'s behaviour is
     not rewritten** — awubot's own `CLAUDE.md` rule ("new behaviour = a new strategy class") is
     honoured: an LLM's `CustomDoctrine` is a new class consulted by `Doctrine`, never an edit.
- Per-episode compile: `javac -cp battlecode26-java-1.2.5.jar:/opt/chassis/classes -d <seatdir>
  <clan>/doctrine/Doctrine.java [<clan>/doctrine/CustomDoctrine.java]`, then
  `java -cp … battlecode.instrumenter.Verifier <clan> <seatdir>`. Both bounded
  (`compile_timeout_seconds`, default 30).

### The engine invocation (exact, from `battlecode26/build.gradle` `headless`)

```
java -Xmx1g -XX:+UseSerialGC
  --add-opens=java.base/jdk.internal.misc=ALL-UNNAMED
  --add-opens=java.base/jdk.internal.math=ALL-UNNAMED
  --add-opens=java.base/jdk.internal.util=ALL-UNNAMED
  --add-opens=java.base/jdk.internal.access=ALL-UNNAMED
  --add-opens=java.base/sun.security.action=ALL-UNNAMED
  -Dbc.server.websocket=false -Dbc.server.wait-for-client=false
  -Dbc.server.mode=headless -Dbc.server.map-path=/opt/battlecode/maps
  -Dbc.server.robot-player-to-system-out=false -Dbc.server.debug=false
  -Dbc.engine.show-indicators=true            # REQUIRED: timeline markers are gated on it
  -Dbc.engine.enable-profiler=false
  -Dbc.game.team-a="Clan Ash"  -Dbc.game.team-a.package=clanash  -Dbc.game.team-a.url=<seatdirA>
  -Dbc.game.team-b="Clan Basil" -Dbc.game.team-b.package=clanbasil -Dbc.game.team-b.url=<seatdirB>
  -Dbc.game.maps=<map> -Dbc.server.validate-maps=true -Dbc.server.alternate-order=false
  -Dbc.server.save-file=<workdir>/match.bc26
  -cp battlecode26-java-1.2.5.jar:<seatdirA>:<seatdirB>:scala-library-2.11.7.jar
  battlecode.server.Main -c=-
```

`-Dbc.game.team-a` is the **team name recorded in the `.bc26`** (`GameHeader.teams[].name`), which
is why the aliases go there: the recorded match is anonymous by construction.

### Map pools (all official `battlecode26/maps`, sizes read from the `.map26` files)

- `small` (6): `DefaultSmall` 30×30, `Stash` 30×30, `arrows` 30×30, `closeup` 30×30,
  `uneasy_alliance` 30×30, `toomuchcheese` 30×30.
- `mixed` (12): the six above + `Excavation` 39×39, `ZeroDay` 40×34, `knifefight` 40×40,
  `whatsthecatdoin` 40×40, `thunderdome` 45×35, `DefaultMedium` 45×45.
- `large` (6): `DefaultLarge` 60×60, `Nofreecheese` 60×60, `RUN` 60×60, `averystrangespace` 60×60,
  `safelycontained` 60×60, `streetsofnewyork` 60×60.

All are symmetric (the `.map26` `symmetry` field is 0/1/2 on every one of them). awubot's 72 extra
maps ship in the image at `/opt/battlecode/maps-community/` but are **not** in a v1 pool — they are
not all balanced and v1 pins timing to maps CI has measured.

---

## Server, player, protocol

Protocol id: **`cogame.battlecode.v1`**. Transport, routes, env vars, connect/reconnect semantics,
`done`-before-artifacts, exit codes and the 20 s shutdown grace are cogame-factorio's, unchanged
(`docs/PROTOCOL.md` there). What changes is the message set.

### `welcome` (server → player, once per connection)

```json
{"type":"welcome","protocol":"cogame.battlecode.v1","game_version":"GV01","slot":0,
 "alias":"Clan Ash","opponent_alias":"Clan Basil","name":"Clan Ash",
 "engine":{"artifact":"org.battlecode:battlecode26-java:1.2.5","rounds":2000},
 "map":{"name":"DefaultSmall","width":30,"height":30,"symmetry":"rotation","rounds":2000,
        "map_seed":158,"pool":"small"},
 "episode":{"seed":871345,"variant":"doctrine_duel","seats":2,"slot":0,"team":"A",
            "doctrine_deadline_seconds":90,"doctrine_retry_deadline_seconds":60,
            "max_compile_attempts":3,"compile_timeout_seconds":30,
            "engine_wall_clock_seconds":400,"max_java_chars":12000},
 "scoring":{"cooperation":{"cat_damage":0.5,"kings":0.3,"cheese":0.2},
            "backstab":{"cat_damage":0.3,"kings":0.5,"cheese":0.2},
            "win_bonus":100,"note":"points are truncated to an integer, as the engine does"},
 "rules_digest":"<~6 KB condensed spec: rats, kings, cheese, cats, traps, dirt, ratnap, throw, backstab, tiebreaks>",
 "api_digest":"<~5 KB RobotController digest: the exact method list, cooldowns, bytecode limits>",
 "sheet_schema":{"…JSON Schema of the doctrine sheet with every default and range…"},
 "java_contract":"<the ClanDoctrine interface source and one worked example, ~1.5 KB>"}
```

**Per-seat observation — what is visible and what is hidden.** Visible: everything above (own
alias, side, map card, seed, both weight sets, deadlines, the full knob surface, the Java
contract, the compile transcript of *its own* failed attempts). Hidden: **the opponent's doctrine,
sheet, Java, notes and motto** (sealed and simultaneous — the server does not send any of it, in
either direction, at any time); **the opponent's real player name** (only the alias); the episode's
per-round state (a cog never observes the match — there is no in-match observation message at all);
the engine's internal RNG state. The only cross-clan channel is the engine's own in-match squeaks
and positions between robots, which no cog reads.

### `doctrine_request` (server → player) and `compile_error` (server → player)

```json
{"type":"doctrine_request","attempt":1,"deadline_seconds":90}
{"type":"compile_error","attempt":2,"deadline_seconds":60,
 "transcript":"<≤4000 runes of javac/Verifier output>","attempts_left":1}
```

### `doctrine` (player → server) — the reply schema

```json
{"type":"doctrine","attempt":1,
 "sheet":{"chassis":"awubot","backstab_policy":"at_round_N","backstab_round":700,
          "cat_engagement":"hunt","cat_trap_budget":60,"rat_trap_budget":80,
          "spawn_curve":"swarm","cheese_ferry_ratio":0.4,"king_count_target":4,
          "dirt_wall_policy":"king_shell","throw_rats_to_feed_cats":false},
 "strategy_java":"package clanash.doctrine; …",
 "notes":"Farm cats to 700, then take their kings.",
 "motto":"Trust, briefly."}
```

| field | cap | on violation |
|---|---|---|
| whole message | 64 KB | malformed → retry once → scripted fallback |
| `sheet` | ≤ 32 keys; each value type/range checked | bad field → that field's default |
| `strategy_java` | **12 000 runes** | dropped, one repair attempt spent |
| `notes` | **280 runes** | truncated |
| `motto` | **48 runes** | truncated |
| compile transcript stored/echoed | **4 000 runes** | truncated |
| unknown sheet key names recorded | ≤ 16 keys, each ≤ 40 runes | truncated |

**Every truncation is on rune boundaries** — slice the decoded `str` and only then encode; never
slice UTF-8 bytes. The replay must survive a strict UTF-8 JSON parse (bullwhip 2026-08-22), and a
model that emits an emoji motto at exactly the cap is the case that breaks byte slicing.

### `done` (server → player)

`{"type":"done","result":{…the results document…}}`, then the socket closes and the player exits 0.

### Global spectator feed (`/global`, `/client/global`)

Broadcast-only, factorio's shape: a `status` snapshot on connect (`game_version`, aliases, names,
map, phase), a `phase` message on each transition (`doctrine`, `compiling`, `engine`, `scoring`),
and the final `done`. `/client/global` and `/client/player?slot=&token=` serve real token-checked
HTML pages, registered **before** any catch-all route and neither opening the player socket
(lantern 0.1.1); a bad token on `/player` closes the socket (flatland 0.1.1).

### Results document (closed schema; == manifest `results_schema` == `docker_smoke.sh` key set)

`names` (real player names, seat order), `aliases`, `scores`, `points`, `wins` (0/1 per seat),
`win_type` (`resignation|ratking_destroyed|backstab_ratking_destroyed|more_points|more_robots|more_cheese|tie|coin_flip|none`),
`rounds_played`, `map`, `seed`, `cooperation_at_end`, `backstab_round` (int or null),
`backstab_by` (alias or null), `cat_damage`, `cheese_transferred`, `kings_alive`, `rats_alive`,
`sheet_defaults_applied` (per-seat list), `java_applied` (per-seat bool), `compile_attempts`
(per-seat int), `fallbacks` (per-seat int), `decision_ms` (per-seat int), `engine_seconds`,
`end_reason` (`complete|deadline|engine_error`), `wall_clock_seconds`.

### Replay envelope (`COGAME_SAVE_REPLAY_URI`, UTF-8 JSON, self-sufficient)

```jsonc
{"format":"cogame-battlecode-replay","version":1,"game_version":"GV01",
 "protocol":"cogame.battlecode.v1",
 "config":{ /* resolved game config, tokens EXCLUDED */ },
 "seed":871345,
 "map":{"name":"DefaultSmall","width":30,"height":30,"symmetry":"rotation","rounds":2000,"pool":"small"},
 "aliases":["Clan Ash","Clan Basil"],
 "names":["daveey","daveey-1"],              // spectator-side only; agents never see these
 "seats":[{"slot":0,"team":"A","alias":"Clan Ash","name":"daveey","policy":"llm",
           "sheet":{…as applied…},"sheet_submitted":{…as received…},
           "sheet_defaults_applied":["cat_trap_budget"],"sheet_unknown_fields":["swarm_mode"],
           "java_applied":true,"java_source":"…","java_chars":4120,
           "compile":[{"attempt":1,"ok":false,"transcript":"…"},{"attempt":2,"ok":true}],
           "notes":"…","motto":"…","decision_ms":41234,"fallback":null}],
 "events":[ … see below … ],
 "match_b64":"<base64 of the gzipped .bc26>",   // null on deadline/engine_error
 "match_bytes":62598,
 "result":{ /* identical to COGAME_RESULTS_URI */ }}
```

Everything the viewer needs — names, aliases, config, seed, map, doctrines, the entire per-round
match state (inside `match_b64`) and the result — is in the file. No other data source is contacted.

### Event vocabulary carried by the replay

Pre-match events carry `ms` (wall clock from episode start) and `round: 0`; in-match events carry
`round`.

| `kind` | fields | drawn as |
|---|---|---|
| `episode_start` | `seed`, `map`, `variant`, `aliases` | feed line |
| `doctrine_requested` | `slot`, `attempt`, `deadline_s` | feed line |
| `doctrine_received` | `slot`, `attempt`, `latency_ms`, `bytes`, `defaults_applied`, `unknown_fields` | feed line + scrubber beat `doctrine` |
| `doctrine_retry` | `slot`, `reason` (`timeout\|parse\|wrong_attempt\|oversize`) | feed line (amber) |
| `doctrine_fallback` | `slot`, `reason` | feed line (red) + beat `doctrine` |
| `compile_attempt` | `slot`, `attempt`, `ok`, `errors_head` (≤ 200 runes) | feed line + beat `compile` |
| `java_applied` / `java_dropped` | `slot`, `reason` | feed line |
| `engine_start` | `map`, `cmd_digest` | feed line |
| `backstab` | `round`, `by_alias`, `detected` (`marker\|turn_flag`) | **chapter marker**: beat `backstab`, scorebug flips COOPERATION → BACKSTAB |
| `king_lost` | `round`, `alias`, `kings_left` | beat `king` |
| `engine_end` | `rounds`, `winner_alias`, `win_type`, `wall_ms` | beat `end` |
| `score` | `alias`, `points`, `share_cat`, `share_king`, `share_cheese`, `win` | endcard rows |
| `episode_end` | `reason` | endcard |

`king_lost` is derived server-side by diffing `teamAliveRatKings % 10` across consecutive `Round`
records, so the viewer needs no engine logic to place those beats.

---

## Viewer

**The wasm exception is invoked, explicitly.** The playbook's pin is a static wasm bundle whose
sim module is recompiled to wasm; its one admissible exception is "an engine that genuinely cannot
compile to wasm — then record a static artifact the bundle plays back, still no pod". The
`battlecode26` engine is Java with a bytecode instrumenter and cannot be compiled to wasm. So the
**recorded `.bc26` is the static artifact**: it is embedded base64 in the replay JSON, and the
bundle decodes and plays it in the browser with the official Battlecode client's own playback code
compiled to a plain static JS bundle. There is no server, no pod, no engine in the browser; the
manifest still declares `"replay_viewer": {"bundle": "static-replay-viewer"}` and the repo still
ships the `coworld build` hook `tools/build_replay_viewer.sh`. `/client/replay` is **never**
declared as a live viewer (the game container's replay mode serves the same static bundle, exactly
as factorio does).

### Chrome provenance — ONE starter: `cogame-factorio`

All chrome files come from **`cogame-factorio`** and from no other starter. It is the starter we
fork; its chrome is itself the coworld-ctf chrome ported for a game whose playback is page-local
and whose timeline unit is not an engine tick (see the header comment of
`cogame-factorio/client/chrome_common.js`), which is exactly our situation. Mixing another
starter's shell with this one's loader is the cogame-lantern deadlock (2026-08-23) and is
forbidden here.

| bundle file | source | treatment |
|---|---|---|
| `chrome_common.js` | `cogame-factorio/client/chrome_common.js` | **byte-for-byte copy**, not one character changed |
| `broadcast_core.js` | `cogame-factorio/client/broadcast_core.js` | byte-for-byte copy |
| `replay_doc.js` | `cogame-factorio/client/replay_doc.js` | copy; extended only by *adding* the envelope's new fields (aliases, seats, events, `match_b64`) |
| `index.html` | `cogame-factorio/client/replay_broadcast.html` | the starter's page **with a game block appended** — the existing `<head>`, CSS tokens, grid rows, `#banner`, `#scorebug`, `#main`, `#stage`, `#transport`, `#scrub`, `#endcard`, `#failcard`, `#loader` and their ids are kept as they are; nothing is rewritten and no id is re-used for a different purpose (the cogame-gridlock failure, 2026-08-23) |
| `static_replay.js` | `cogame-factorio/client/static_replay.js` | kept as the loader with its **public API unchanged** (`createCore(config)` → `start/stop/zoomAt/setZoom/panBy/panTo/resetView/getTransform/setViewportFit`), and its `data-replay-loaded` write kept verbatim; only the internals change — instead of spawning the wasm Worker it drives the Battlecode bundle in-page |
| the wasm slot: `replay-viewer/config.nims` + `replay-viewer/<slug>_replay.nim` + `static_replay_worker.js` | — | **deleted** (the exception): there is no Nim, no emscripten and no OffscreenCanvas worker in this coworld. Their slot is filled by `bc_embed.js`, built by the hook |

**Starter elements removed from the appended page** (and only these): `#stepro` (the FLE
per-step readout: tick / score / entities / wall-ms / character), `#maptools`'s `#tilepos`
readout, `#legend` (the Factorio entity legend), `#charmark` (the FLE character ring), and the
right plaque's FLE sections `#code`, `#code-meta`, `#output`, `#out-meta`, `#inventory`, `#flows`.
Everything else stays. The appended game block adds, inside the existing `#stage` and
`#plaque-r`: `#board` (the host div the Battlecode renderer's canvases are appended to),
`#coopchip` (COOPERATION / BACKSTAB state), `#bars` (the three-bar points breakdown per clan),
`#doctrines` (both clans' sheets in plain words), and `#feed` (the event feed the viewer smoke
probes).

### The engine bundle (`bc_embed.js`) and the build hook

`tools/build_replay_viewer.sh` keeps the starter's structure exactly (argument = the absolute
`static-replay-viewer` output dir, containment checks, `docker build --target <stage>` +
`docker create` + `docker cp`, then an assertion that **every** referenced file is present) — only
the stage changes from `wasm-builder` to `viewer-builder`, and the stage runs
`npm ci && npm run build` in the vendored client instead of an emscripten link.

- `viewer/bc-client/` — the official client vendored from `battlecode26/client` at engine tag
  `engine.1.2.5` / client `1.0.7`, AGPL-3.0, with exactly three changes, each named here:
  1. a new entry file `src/cogame_embed.ts` (~70 lines) that imports the client's own
     `playback/Game`, `playback/GameRunner` and `playback/GameRenderer` and exposes
     `window.CogameBC = {load(bytes, hostDiv), seek(round), setPlaying(b), setUPS(n),
     state(), onRound(cb)}` — `Game.loadFullGameRaw(bytes)` → `GameRunner.setMatch(game.matches[0])`
     → `GameRenderer.addCanvasesToDOM(hostDiv)`. No React, no router, no sidebar: the client's
     `GameConfig.config` is a plain module-level object (`src/app-context.tsx:67`), so the
     renderer runs standalone;
  2. `webpack.config.js`: one added entry `embed: './src/cogame_embed.ts'` emitting `bc_embed.js`
     (the existing `app` entry and the `CopyPlugin` that ships `src/static/**` are untouched);
  3. `index.html`: the Google Fonts `<link>` removed, so the bundle makes **no network request
     except** the S3 fetch of the `.replay` file.
- The hook's expected-file assertion becomes: `index.html`, `chrome_common.js`, `broadcast_core.js`,
  `replay_doc.js`, `static_replay.js`, `bc_embed.js`, `static/img/dirty.png`,
  `static/img/robots/` (a missing sprite tree renders an empty board and must fail the build).

### Load signalling

`static_replay.js` sets `document.documentElement.setAttribute('data-replay-loaded', 'true')` on
the **first drawn frame** — i.e. from the callback fired after `CogameBC.load()` has rendered
round 1 into `#board`, never on rAF timing at the call site (chorus, 2026-08-24) — and the
`coworld-replay` bridge posts its `ready` message **from inside that same callback, after** the
attribute is set. On any failure (fetch, base64, gunzip, flatbuffer parse, missing `match_b64`) it
sets `data-replay-error="<message>"` on `<html>`, shows `#failcard`, and — when `match_b64` is null
because the episode hit the deadline — draws the endcard explaining that instead, which is a
legible replay, not an error.

### Zoom: KEPT

The board is 30×30 to 60×60 tiles; the client renders at 20 px/tile, so the native board is
600–1200 px wide — **larger than the 360 px featured-match frame**, so a zoom affordance is
required and is kept. In this starter's chrome the zoom affordance is `#maptools` (`#zoom`
readout, `#fit`, `#fitmap`, `#follow`), which we keep and wire to a CSS transform on `#board`
(`#follow` re-centres on the clan currently selected in the scorebug). We do **not** introduce
coworld-ctf's `#viewpanel` element: it belongs to a different starter's chrome and this note takes
all chrome from one starter. Default view is fit-to-frame, so the whole map is visible at 360 px
without touching a control.

### Transport rules

- `relayout()` (added in the appended game block, run on load and from the `#main` `ResizeObserver`)
  sets **`--band`** = the measured height of the `#transport` row and **`--hudscale`** = the board's
  on-screen width ÷ 760, both on `:root`, alongside the starter's existing `--hud` (which
  `?hud=` still overrides).
- **Nothing is overlaid in the transport band**: the page's `body` is a CSS grid with explicit rows
  (`#banner` 1, `#scorebug` 2, `#main` 3, `#transport` 4) — the transport is its own track and every
  overlay lives inside `#stage`, which is row 3.
- The **endcard stops at `var(--band)`** (`#endcard{bottom:var(--band)}`) and **every seek dismisses
  it** — `seek()` clears `#endcard.show` before it moves the playhead, so scrubbing back from the
  end is never blocked by the card.
- **Scrubber beats are clickable, labelled buttons** built by the game block (a differently named
  builder function, never `markBeat` — the tandem hoisting collision, 2026-08-23) and placed by
  `chrome_common.js`'s `setMarkers`. CSS exists for **every kind emitted**:
  `.beat-marker.doctrine`, `.beat-marker.compile`, `.beat-marker.backstab`, `.beat-marker.king`,
  `.beat-marker.end`. Each is `<button>` with an `aria-label` and a `title`
  ("BACKSTAB — Clan Basil, round 612"), and clicking it seeks to that round.
- Transport controls (starter ids kept): `#btn-restart`, `#btn-back` (−1 round), `#btn-play`,
  `#btn-fwd` (+1 round), `#btn-skip5` relabelled **+25 rounds**, `#btn-end`, `#btn-spoilers`,
  `#speedchips` (0.5/1/2/4/8 × a base of 8 rounds/s, so a 450-round match plays in ~56 s at 1× and
  a 2000-round match in ~4 min, and the scrubber covers the rest).

### Readouts (and 360 px)

The viewer is **legible at 360 px wide** — the featured-match iframe width — and is checked at that
width, not at desktop width. `.plate-name{flex:1 1 auto; min-width:3.2em}`, labels hidden under
640 px, and the right plaque auto-collapses to its tab (`#main[data-right="0"]`) under 720 px so the
board keeps the frame.

- `#scorebug`: map name and size; `#clock` = `round 612 / 2000`; two clan plates, each
  `CLAN ASH` over the real player name (`daveey`) and the motto; the live points number; and
  `#bars`, the three-bar breakdown (cat damage / kings / cheese) read per round from the client's
  own `RoundStat.getTeamStat()` shares.
- `#coopchip`: `COOPERATION` (green) until the flip, then `BACKSTAB — Clan Basil, round 612` (red).
- `#board`: the real Battlecode visuals — rats, the 3×3 rat kings, cats, cheese and cheese mines,
  rat traps, cat traps, dirt — drawn by the official client's own renderer and sprites.
- `#doctrines` (right plaque): per clan, the sheet in plain words ("betrays at round 700", "hunts
  cats", "80 rat traps", "swarm spawning", "keeps 4 kings"), whether a Java class was applied or
  dropped and after how many compile attempts, and the capped `notes`.
- `#feed`: the event lines above, revealed as the playhead passes them (spoiler gate honoured).
- `#endcard`: winner alias **and** real player name, the win type in plain words ("Clan Basil
  destroyed every enemy rat king at round 612"), the final three-bar points breakdown for both
  clans, who betrayed whom at which round (or "the alliance held"), and each doctrine's headline
  knobs.

---

## Packaging

- **`compose.yaml`** — two services, names load-bearing (manifest placeholders derive from them:
  `game` → `{{GAME_IMAGE}}`, `player` → `{{PLAYER_IMAGE}}`, lantern 0.1.0):
  ```yaml
  services:
    game:
      image: cogame-battlecode-game:latest
      platform: linux/amd64
      build: {context: ., dockerfile: Dockerfile, target: game, network: host}
    player:
      image: cogame-battlecode-player:latest
      platform: linux/amd64
      build: {context: ., dockerfile: Dockerfile, target: player, network: host}
  ```
- **`Dockerfile`**, four stages, all `linux/amd64`:
  1. `chassis-builder` — `eclipse-temurin:21-jdk` + gradle: resolves
     `org.battlecode:battlecode26-java:1.2.5` from `https://releases.battlecode.org/maven`, renders
     awubot and examplefuncsplayer into `clanash`/`clanbasil` packages and compiles them to
     `/opt/chassis/classes`.
  2. `viewer-builder` — `node:22` + `npm ci && npm run build` in `viewer/bc-client`, then assembles
     `viewer/dist/` = the client's `dist/bc_embed.js` + `dist/static/**` + the chrome files +
     `index.html`.
  3. `player` — `python:3.11-slim` + aiohttp + `players/` + `contract.py`/`version.py`. **No LLM
     SDK**: the Bedrock call is plain `urllib` against the sidecar, so the player image stays far
     under the 512 MiB cap.
  4. `game` (default) — `eclipse-temurin:21-jdk` + python3 + uv-locked deps + `/opt/chassis`
     (from stage 1) + `battlecode26-java-1.2.5.jar` + `scala-library-2.11.7.jar` +
     `/opt/battlecode/maps` (official) and `/opt/battlecode/maps-community` (awubot's) + `server/`
     + `players/` + `viewer/dist` (from stage 2).
- **`coworld_manifest_template.json`** — `game.name = "battlecode"` (== the secret namespace ==
  the slug), `game.description` present, `game.tags` absent (tags only top-level, ≥ 3:
  `battlecode`, `rts`, `mixed-motive`, `code-agents`), `$schema`, `episode_timeout_minutes: 20`,
  `game.runnable.type: "game"`, `game.replay_viewer.bundle = "static-replay-viewer"`,
  `game.config_schema` a real JSON Schema with `minItems`/`maxItems` on **every** array (`tokens`,
  `players`) and no runner-managed `tokens` inside any `game_config`, `game.results_schema` the
  closed set above, bundled `player[]` at top level with `resources.limits.cpu: "1"`.
  - `game.protocols` — **both** keys, as objects:
    `player` = `{"type":"uri","value":"…/blob/main/docs/PROTOCOL.md"}`,
    `global` = `{"type":"uri","value":"…/blob/main/docs/PROTOCOL.md"}`.
  - `game.docs` — `readme` = `{"type":"uri","value":"…/blob/main/README.md"}` and `pages` =
    `replay.md` (Replay format → `docs/REPLAY.md`), `rules.md` (Rules & doctrine sheet →
    `docs/RULES.md`), `api.md` (RobotController digest → `docs/API.md`).
  - `player[]`: `awubot` ("awubot baseline — the awu7 `final` bot on its default doctrine") and
    `examplefuncsplayer` ("scaffold baseline — the official example bot, weak"), both
    `image: {{PLAYER_IMAGE}}`, `run: ["python","-m","players.scripted_player"]`.

  **Variants — `num_agents: 2` inside every `game_config`, never at variant top level:**

  | variant id | name | pool | `engine_wall_clock_seconds` | `num_agents` |
  |---|---|---|---|---|
  | `doctrine_duel` | Doctrine duel (2 seats) | `mixed` | 400 | **2** |
  | `small_arena` | Small arena (2 seats) | `small` | 300 | **2** |
  | `open_war` | Open war (2 seats) | `large` | 480 | **2** |

  Each variant's `game_config` also carries `players: [{"name":"Clan Ash"},{"name":"Clan Basil"}]`,
  `seed: 0` (draw per episode), `doctrine_deadline_seconds: 90`,
  `doctrine_retry_deadline_seconds: 60`, `doctrine_phase_budget_seconds: 240`,
  `max_compile_attempts: 3`, `compile_timeout_seconds: 30`,
  `player_connect_timeout_seconds: 120`.

  **Certification fixture** — `certification.players` seats **both** declared player entries (the
  raid 0.1.3 rule: every declared player must occupy a slot): `[{"player_id":"awubot"},
  {"player_id":"examplefuncsplayer"}]`, and `certification.game_config` =
  `{"players":[{"name":"Clan Ash"},{"name":"Clan Basil"}], "num_agents": 2, "pool":"small",
  "seed": 1, "map":"DefaultSmall", "doctrine_deadline_seconds": 20,
  "doctrine_retry_deadline_seconds": 10, "doctrine_phase_budget_seconds": 45,
  "max_compile_attempts": 1, "engine_wall_clock_seconds": 180,
  "player_connect_timeout_seconds": 90}`. Measured shape: awubot vs examplefuncsplayer on
  `DefaultSmall` runs ≤ 60 s (awubot vs awubot measured 60 s), so the fixture episode is
  ~30 s start + 20 s doctrine + ≤ 60 s engine + 10 s artifacts ≈ **120 s** — the certify step
  therefore passes **`--timeout-seconds 900`** (the CLI default is 60 s and would fail a healthy
  fixture, cooperative-hunting 0.1.3). The resulting replay is ~135 rounds ≈ 17 s of playback at
  the default pace, which outlasts the 10 s viewer soak (ecos, 2026-08-23).

- **`tools/ci/policies.json`** (champions are LLM; fillers are the scripted baselines; filler
  versions must differ from champion versions):
  ```json
  [{"name":"battlecode-loyalist","run":"python -m players.llm_player",
    "env":{"PLAYER_PROMPT":"<champion #1 text>","USE_BEDROCK":"true"}},
   {"name":"battlecode-opportunist","run":"python -m players.llm_player",
    "env":{"PLAYER_PROMPT":"<champion #2 text>","USE_BEDROCK":"true"},
    "player":"ply_bac48eb1-662e-44f8-973d-f3e016dccf5d"},
   {"name":"battlecode-awubot","run":"python -m players.scripted_player",
    "env":{"PLAYER_SCRIPTED":"awubot"}},
   {"name":"battlecode-efp","run":"python -m players.scripted_player",
    "env":{"PLAYER_SCRIPTED":"examplefuncsplayer"}}]
  ```
  The game runnable's manifest `env` carries
  `ANTHROPIC_API_KEY_URI: secret://coworld/battlecode/anthropic_api_key` (hive, 2026-08-23) even
  though the LLM call is player-side, so the secret is present if the server ever needs it.
- **Licensing**: `LICENSE` = AGPL-3.0; `NOTICE` names `battlecode26` (engine, client, schema, maps,
  example bots — AGPL-3.0) and awubot (AGPL-3.0) with their commits, and `viewer/bc-client/LICENSE`
  and `chassis/awubot/LICENSE` are kept in place.

---

## Tests

`pytest` (offline; no JVM needed except where marked `-m engine`) plus three CI jobs. The template
`ci.yml`'s **Nim jobs do not apply and are replaced**, exactly as the idea pins.

**Sim unit tests (`tests/`, offline):**

1. `test_score.py` — the points formula against **recorded vectors**, including the real match
   harvested in this design round (`peaceinourtime`: catDamage 4000/4000, cheese 1590/2940, packed
   kings 17231/19732 → decode 1/2 kings and 1723/1973 cheese → points **42 / 57**, engine winner
   Team B, `winType = MORE_POINTS`). Also: zero-total shares, truncation-not-rounding, and the
   backstab weight set.
2. `test_bc26.py` — parse the committed fixture `tests/fixtures/DefaultSmall.bc26`: event types in
   order (GameHeader, MatchHeader, Round…, MatchFooter, GameFooter), team names/packages, the
   packed-king decode, `Turn.isCooperation` backstab detection, `king_lost` diffing, timeline
   markers.
3. `test_sheet.py` — every field: default when absent, default when out of range, default when
   mistyped, unknown keys recorded and ignored, `sheet_defaults_applied` exact, and the rendered
   `Doctrine.java` string for a full sheet.
4. `test_doctrine.py` — the Java denylist, the 12 000-rune cap, transcript truncation, and that
   **all** truncation is on rune boundaries (assert `text[:n]` on a string containing astral-plane
   characters round-trips through `json.dumps` + strict decode).
5. `test_engine_phase.py` — the doctrine state machine against a fake seat source: timeout → retry
   → fallback; malformed → retry; wrong `attempt` ignored; compile-repair loop capped at 3;
   phase-budget expiry; all with a fake clock, no sleeping.
6. `test_replay.py` — envelope shape, `match_b64` round-trip (base64 → gzip → flatbuffer), the
   `deadline` envelope with `match_b64: null`, and a **strict UTF-8 parse**
   (`json.loads(data.decode("utf-8"))` with `ensure_ascii=False` written bytes).
7. `test_results.py` / `test_manifest.py` — the triple-sync tripwire: `results_doc` keys +
   `end_reason` enum == manifest `results_schema` == the key set asserted in
   `tools/ci/docker_smoke.sh`; `num_agents` present in **every** variant's `game_config` and in
   `certification.game_config` and **absent** at variant top level; every `config_schema` array has
   `minItems`/`maxItems`; no `tokens` in any `game_config`; both `game.protocols` keys and
   `game.docs.readme` + `pages` are `{"type":…,"value":…}` objects; and the installed coworld
   CLI's own `_load_template_manifest` accepts the template (collab-cooking, 2026-08-25).
8. `test_contract.py` — `contract.py` against the golden `tests/contract_manifest.txt`.
9. **Bounded-orders / legality on the scripted baselines** (`test_baselines.py`): for both
   `PLAYER_SCRIPTED` values, the reply is asserted to be a legal `doctrine` message —
   `type`/`attempt` correct, message ≤ 64 KB, every sheet key known, every value in range and of
   the declared type, `strategy_java is None`, `notes` ≤ 280 runes, `motto` ≤ 48 runes — and the
   validator applied is the **same** `sheet.validate()` the server uses.
10. `test_viewer.py` — the shipped `index.html` references every file the hook asserts; the
    chrome-alias scope-duplication check over `ChromeCommon`'s exported names (no game-block
    function shadows a chrome alias — tandem, 2026-08-23); `chrome_common.js` is byte-identical to
    the starter's copy (a checked-in sha256).

**CI jobs (`.github/workflows/ci.yml`):**

- `test` — `uv sync --frozen`, `uv run pytest -v -m "not engine"`.
- `engine-smoke` (replaces the Nim build job) — Java 21, `gradle` resolves
  `battlecode26-java:1.2.5`, builds both chassis packages, then runs **examplefuncsplayer vs
  awubot on `DefaultSmall`** headless and asserts: the JVM exits 0; `match.bc26` exists and is
  > 10 KB; it gunzips and parses with the vendored Python bindings; it contains a `GameHeader`, ≥ 1
  `Round` and a `MatchFooter`; the team names are the two aliases; and the **wall clock is
  recorded and must be ≤ 240 s** (the budget check the idea asks for — measured 26–104 s on a
  single sandbox core). The produced `.bc26` is uploaded as an artifact and is the file
  `tests/fixtures/DefaultSmall.bc26` is refreshed from.
- `docker-smoke` — build the production image, then `bash tools/ci/docker_smoke.sh
  cogame-battlecode:ci` (factorio's script, `SMOKE_PLAYERS="players.scripted_player
  players.scripted_player"` with `PLAYER_SCRIPTED` set per seat, `<SEATS>` substituted to **2** by
  phase 20): one game container + two player containers on `coworld-local`, `file://` artifact
  URIs; asserts the game container exits 0, **every player container exits 0**, the results key set
  matches exactly, `end_reason == "complete"`, `scores` has 2 entries, `fallbacks == [0, 0]`,
  `java_applied == [false, false]`, the replay parses as strict UTF-8 JSON with
  `format == "cogame-battlecode-replay"`, `match_b64` non-null and `match_bytes > 10000`, and no
  `player_failure.json` was written.
- `viewer` (replaces `wasm-viewer`) — `bash tools/build_replay_viewer.sh
  "$PWD/dist/static-replay-viewer"` (which runs the client's `npm run build`), then **executes**
  the bundle: `node tools/ci/viewer_smoke.mjs --replay <the replay docker-smoke produced>
  --soak 10 --strict-text-bounds --width 360`, requiring `loaded: true` via
  `data-replay-loaded`/bridge `ready`, three differing scrub readouts at 0 % / 50 % / 100 %,
  uninterrupted-playback advancement over the soak, and zero `canvas_text.never_inside`. A second
  step runs it against `tools/ci/renderer_fixture.html` (full-cap `notes` and `motto` on both
  seats, several canvas sizes) because a CI replay is always scripted and therefore carries no LLM
  text (cogchemists, 2026-08-24).
- `upload-coworld` — unchanged from the starter, gated on the `UPLOAD_REQUIRED` repo variable
  (derks-gym 0.1.1) so publishing stays the release workflow's job.

---

## Out of scope (v1)

- **Best-of-three and the alternate-order side swap.** One game on one map per episode; the
  measured engine cost (up to ~350 s for a full-length game) does not fit three inside 720 s.
  Side fairness comes from the seed permuting Team A/B across a round-robin instead.
- **awubot's 72 community maps as a playable pool.** Shipped in the image, not drawn from, until
  CI has timed and balance-checked them.
- **Mid-match interaction of any kind** — no per-round observations, no doctrine amendments, no
  in-match messages between cogs. One sealed doctrine, then the war.
- **Crossplay (Python bots), the profiler, `speedscope`, the map editor, the tournament and queue
  pages of the official client.** The embed entry uses the playback core only.
- **Editing awubot's strategy code itself.** The doctrine layer is guard clauses plus a new
  strategy class; upstream behaviour is otherwise untouched (awubot's own `CLAUDE.md` rule).
- **A second Java class, package-level patches, or arbitrary file writes from a doctrine.** Exactly
  one class, in one package, compiled and Verifier-checked, or nothing.
- **Scoring anything the engine does not record.** No hand-rolled metrics: every number in
  `results` comes from the `.bc26` or from the server's own bounded bookkeeping.
- **Live engine streaming to spectators** (`-Dbc.server.websocket=true`, the client's runner tab).
  The recorded match is the replay; there is no pod.
