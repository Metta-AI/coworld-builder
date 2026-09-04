# r2 review — operator-authored (daveey, 2026-09-04, session steer)

Round 1 (episode a9a54765, replay 0d235369) fails definition-of-done check 4 "champion seats doing
the thing": Clan Basil (daveey-1, opportunist) answered with `"chassis": "scaffold"` — the upstream
move-or-turn-only bot — so it built 0 rats, 0 traps, dealt 0 cat damage and ferried 0 cheese in all
three games, and WON 2 of 3 because Clan Ash (awu chassis, 35–39 rats, 25–28 traps, 4880/3790 cat
damage) lost every king to the cats at rounds 1078 and 362 (kings_destroyed, cooperation_at_end
true, backstab never). A clan that stands still winning the match is a degenerate outcome and the
featured match on softmax.com/battlecode shows exactly that.

## D1 (blocking, correctness)
`chassis` is NOT an LLM knob. Remove it from the sheet the LLM sees (prompt preamble THE KNOBS list
and KnownKeys); LLM policies always run the awu chassis; scaffold is selectable only via
PLAYER_SCRIPTED=scaffold (filler). An LLM reply that still sends `chassis` is ignored (repair → awu)
and logged.

## D2 (blocking, correctness)
The awu chassis loses all kings to the cats within 362–1078 rounds on cheesefarm and dirtfulcat
under cat_engagement=hunt + dirt_wall_policy=king_shell, and on mercifullattice the kings died with
0 cat damage dealt by anyone. In the real 2026 competition awubot did not routinely lose kings to
cats. Diagnose the cat-defence behaviours (is the king_shell actually built? do kings wander into
cat vision cones? does hunt/squeaking pull cats onto the king? is there any retreat/re-shell when a
cat is within N tiles? do cat traps ring the king?), fix, and ADD A GATE in tests: awu-default vs
awu-default on the five parity maps must reach round 2000 or end on points in ≥ 4/5 games, and none
may end by kings_destroyed before round 1500. Without D2 the scaffold FILLER will still win by
idling.

## D3 (blocking, legibility)
Viewer: two screenshots a minute apart both show the doctrine overlay covering the board with
"Game 1 begins on cheesefarm". Confirm the overlay dismisses on its own and the board animates
(check 8 scrub readouts); if it is a persistent panel, make it collapsible/timed so the rats and
cats are the picture.

## After the fix (process, for the coordinator)
New coworld version; re-upload the two champion policies as new versions ONLY if their prompt text
changes (fillers unchanged; filler versions must stay distinct from champion versions); POST
trigger-round twice and verify check 4 on the new replay: both clans build rats, ferry cheese and
damage cats, and the match ends on points or a real backstab, not on an idle clan's survival.
