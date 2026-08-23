# Discord announcement template (phase 70)

Goes to: Discord `#coworlds`, posted by the bot with `DISCORD_BOT_TOKEN`, always with
`"flags": 4` (`SUPPRESS_EMBEDS`) so the links stay plain text. Written by `prompts/70-announce.md`. The returned message id goes in
`STATE.announce.discord_message_id`.

Substitute: `<slug>`, `<Game Name>`, `<tagline>`, `<emoji>` (one or two), `<player runnable>`,
`<baseline names>`, `<episode length>`, `<round cadence>`.

**Hard limit: the posted message must be ≤ 1800 characters.** Count it before posting; if it
is over, cut from the "what the replay shows" paragraph first, then from paragraph two.
Discord's own cap is 2000 — 1800 leaves room for the bot's formatting.

---

## Shape

```
**New coworld: <Game Name> — <tagline>** <emoji>
https://softmax.com/<slug>

<Paragraph 1 — WHAT THE GAME IS. Seats, what a seat controls, what a turn/tick is, how
long an episode runs, and how score is computed. Concrete numbers, no adjectives. A reader
who has never heard of this game should be able to explain the loop after one read.>

<Paragraph 2 — THE CATCH. The one thing that makes it interesting: the hidden information,
the incentive that pulls against the obvious play, the trap the naive strategy walks into.
Name it. This paragraph is why anyone enters.>

**A policy is just a prompt.** <How to enter: the runnable name to reuse and the env var to
set (usually PLAYER_PROMPT), the scripted baselines already seated and what each one does,
what beating them means, episode length, and how often the league runs a round.>

<What the replay shows — the two or three things visible on screen that make an episode
worth watching, in the viewer's own vocabulary.>

Repo: https://github.com/Metta-AI/cogame-<slug>
```

## Rules

- Never announce before phase 60 passes. The link in line 2 must already render a featured
  match from a **static** replay bundle; a page with a dead viewer is worse than silence.
- Use the policy names spectators see, not the in-game cog aliases.
- No hype, no "excited to announce", no adjectives doing the work of a number. State the game.
- Exactly one emoji cluster, in the title line.
- Both links are bare URLs on their own line so they are easy to copy/click. They must **not**
  unfurl: the POST carries `"flags": 4` (`SUPPRESS_EMBEDS`). If a post ever shows embed cards,
  `PATCH .../messages/<id>` with `{"flags":4}` — see `prompts/70-announce.md` step 4b.

---

## Worked example — the actual Bullwhip post (1,589 chars)

```
**New coworld: Bullwhip — the MIT Beer Game** 🍺📦
https://softmax.com/bullwhip

Four LLM-piloted cogs run one supply chain — Retailer, Wholesaler, Distributor, Factory — for 36 weeks. Every week a stage ships what it can from inventory, turns the shortfall into backlog, and places one order upstream. Orders take a week to be seen; shipments take two weeks to arrive. Holding costs $0.5 a unit a week, backlog $1.0, and your score is minus your total cost.

The catch: customer demand is hidden from every seat and steps up exactly once, and nobody can see another stage's numbers. Order a little too eagerly into a backlog that is already on its way and you get the bullwhip — a small demand step amplified stage by stage into an oscillation that comes back to you as a warehouse full of stock nobody wants. Seats may send one short, non-binding message a week to their two neighbours. Honesty is optional.

**A policy is just a prompt.** Reuse the published `bullwhip-player` runnable and set `PLAYER_PROMPT` to your strategy — no code, no image build. Two scripted baselines are already seated: `bullwhip-basestock` (slow forecast, full supply-line accounting) and `bullwhip-mirror` (order what you received). Beat base-stock and you have something. Episodes are 36 weeks, about ten minutes; the league runs a round every 30 minutes.

The replay shows the conveyor — orders and shipments crawling stage to stage — the seismograph of each stage's orders against the hidden demand line, and every seat's weekly message and private notes.

Repo: https://github.com/Metta-AI/cogame-bullwhip
```

Note what the example does that the shape asks for: paragraph 1 is all mechanics and
numbers; paragraph 2 names the trap (*ordering into a backlog that is already in transit*)
rather than calling the game "fascinating"; the entry paragraph names the exact runnable and
env var, both baselines and what each represents, and the cadence; the replay paragraph names
three concrete on-screen objects.
