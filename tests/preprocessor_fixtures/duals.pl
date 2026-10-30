:- dynamic executable/2, cpa_executable/2, causes/3, cpa_causes/3, cpa_initially/1.
fluent(p).
fluent(q).
action(a).
action(b).
executable(a,[]).
executable(b,[]).
causes(a,[cpa_and(p,neg(q))],[]).
causes(b,[cpa_and(neg(p),q)],[]).
cpa_initially(neg(p)).
cpa_initially(q).
unknown(nop).
plan_goal(p).
