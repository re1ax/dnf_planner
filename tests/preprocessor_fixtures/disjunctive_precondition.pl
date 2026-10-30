:- dynamic executable/2, cpa_executable/2, causes/3, cpa_causes/3, cpa_initially/1.
fluent(p).
fluent(q).
fluent(r).
action(a).
executable(a,[cpa_or(q,r)]).
causes(a,[cpa_and(p)],[]).
cpa_initially(neg(p)).
cpa_initially(neg(q)).
cpa_initially(r).
unknown(nop).
plan_goal(p).
