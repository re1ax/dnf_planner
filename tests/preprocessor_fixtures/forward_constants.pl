:- dynamic executable/2, cpa_executable/2, causes/3, cpa_causes/3, cpa_initially/1.
fluent(seed).
fluent(p).
fluent(q).
action(good).
action(dead).
executable(good,[cpa_and(seed)]).
executable(dead,[cpa_and(q)]).
causes(good,[cpa_when(cpa_and(seed,neg(q)),cpa_and(p))],[]).
causes(dead,[cpa_and(p)],[]).
cpa_initially(seed).
cpa_initially(neg(p)).
cpa_initially(neg(q)).
unknown(nop).
plan_goal(p).
