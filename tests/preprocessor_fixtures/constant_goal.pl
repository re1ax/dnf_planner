:- dynamic executable/2, cpa_executable/2, causes/3, cpa_causes/3, cpa_initially/1.
fluent(p).
action(a).
executable(a,[]).
causes(a,[cpa_and(p)],[]).
cpa_initially(p).
unknown(nop).
plan_goal(p).
