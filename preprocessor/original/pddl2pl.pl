
:- use_module(library(lists)).
:- dynamic executable/2.
:- dynamic cpa_executable/2.
:- dynamic causes/3.
:- dynamic cpa_causes/3.
:- dynamic cpa_initially/1.

%%%% Objects %%%%
cpa_block(cpa_a).
cpa_block(cpa_b).

%%%% Constants %%%%

%%%%  Types rules %%%%

%%%% Predicates %%%%
fluent(cpa_on(  X,  Y)):-
	cpa_block( X), cpa_block( Y).

fluent(cpa_ontable(  X)):-
	cpa_block( X).

fluent(cpa_clear(  X)):-
	cpa_block( X).

fluent(cpa_handempty).

fluent(cpa_holding(  X)):-
	cpa_block( X).


%%%% Actions %%%%
action(cpa_pick_up(  X)):-
	cpa_block( X).

action(cpa_put_down(  X)):-
	cpa_block( X).

action(cpa_stack(  X,  Y)):-
	cpa_block( X), cpa_block( Y).

action(cpa_unstack(  X,  Y)):-
	cpa_block( X), cpa_block( Y).


%%%% Preconditions %%%%
executable(cpa_pick_up(  X), [
 ]):-
	cpa_block( X).

executable(cpa_put_down(  X), [
 ]):-
	cpa_block( X).

executable(cpa_stack(  X,  Y), [
 ]):-
	cpa_block( X), cpa_block( Y).

executable(cpa_unstack(  X,  Y), [
 ]):-
	cpa_block( X), cpa_block( Y).


%%%% Effects %%%%
causes(cpa_pick_up(  X), [
cpa_when( cpa_and( cpa_and( cpa_and( cpa_handempty), cpa_clear( X)), cpa_ontable( X)), cpa_and( neg(cpa_ontable( X)), cpa_and( cpa_and( cpa_and( neg(cpa_clear( X))), neg(cpa_handempty)), cpa_holding( X)))) ], 
[]):-
	cpa_block( X).

causes(cpa_put_down(  X), [
cpa_when( cpa_holding( X), cpa_and( neg(cpa_holding( X)), cpa_and( cpa_and( cpa_and( cpa_clear( X)), cpa_handempty), cpa_ontable( X)))) ], 
[]):-
	cpa_block( X).

causes(cpa_stack(  X,  Y), [
cpa_when( cpa_and( cpa_and( cpa_holding( X)), cpa_clear( Y)), cpa_and( neg(cpa_holding( X)), cpa_and( cpa_and( cpa_and( cpa_and( neg(cpa_clear( Y))), cpa_clear( X)), cpa_handempty), cpa_on( X,  Y)))) ], 
[]):-
	cpa_block( X), cpa_block( Y).

causes(cpa_unstack(  X,  Y), [
cpa_when( cpa_and( cpa_and( cpa_and( cpa_handempty), cpa_on( X,  Y)), cpa_clear( X)), cpa_and( cpa_holding( X), cpa_and( cpa_and( cpa_and( cpa_and( cpa_clear( Y)), neg(cpa_clear( X))), neg(cpa_handempty)), neg(cpa_on( X,  Y))))) ], 
[]):-
	cpa_block( X), cpa_block( Y).


%%%% Inits %%%%
cpa_initially(cpa_oneof([cpa_handempty, cpa_holding(cpa_a), cpa_holding(cpa_b)])).
cpa_initially(cpa_oneof([cpa_holding(cpa_a), cpa_clear(cpa_a), cpa_on(cpa_b, cpa_a)])).
cpa_initially(cpa_oneof([cpa_holding(cpa_a), cpa_ontable(cpa_a), cpa_on(cpa_a, cpa_b)])).
cpa_initially(cpa_oneof([cpa_holding(cpa_b), cpa_clear(cpa_b), cpa_on(cpa_a, cpa_b)])).
cpa_initially(cpa_oneof([cpa_holding(cpa_b), cpa_ontable(cpa_b), cpa_on(cpa_b, cpa_a)])).
cpa_initially(cpa_or( cpa_or( neg(cpa_handempty)), neg(cpa_holding(cpa_a)))).
cpa_initially(cpa_or( cpa_or( neg(cpa_handempty)), neg(cpa_holding(cpa_b)))).
cpa_initially(cpa_or( cpa_or( neg(cpa_holding(cpa_a))), neg(cpa_holding(cpa_b)))).
cpa_initially(cpa_or( cpa_or( neg(cpa_holding(cpa_a))), neg(cpa_clear(cpa_a)))).
cpa_initially(cpa_or( cpa_or( neg(cpa_holding(cpa_a))), neg(cpa_on(cpa_b, cpa_a)))).
cpa_initially(cpa_or( cpa_or( neg(cpa_clear(cpa_a))), neg(cpa_on(cpa_b, cpa_a)))).
cpa_initially(cpa_or( cpa_or( neg(cpa_holding(cpa_a))), neg(cpa_ontable(cpa_a)))).
cpa_initially(cpa_or( cpa_or( neg(cpa_holding(cpa_a))), neg(cpa_on(cpa_a, cpa_b)))).
cpa_initially(cpa_or( cpa_or( neg(cpa_ontable(cpa_a))), neg(cpa_on(cpa_a, cpa_b)))).
cpa_initially(cpa_or( cpa_or( neg(cpa_holding(cpa_b))), neg(cpa_clear(cpa_b)))).
cpa_initially(cpa_or( cpa_or( neg(cpa_holding(cpa_b))), neg(cpa_on(cpa_a, cpa_b)))).
cpa_initially(cpa_or( cpa_or( neg(cpa_clear(cpa_b))), neg(cpa_on(cpa_a, cpa_b)))).
cpa_initially(cpa_or( cpa_or( neg(cpa_holding(cpa_b))), neg(cpa_clear(cpa_b)))).
cpa_initially(cpa_or( cpa_or( neg(cpa_holding(cpa_b))), neg(cpa_on(cpa_a, cpa_b)))).
cpa_initially(cpa_or( cpa_or( neg(cpa_clear(cpa_b))), neg(cpa_on(cpa_a, cpa_b)))).
cpa_initially(cpa_or( cpa_or( neg(cpa_on(cpa_a, cpa_b))), neg(cpa_on(cpa_b, cpa_a)))).
cpa_initially(neg(X)) :- fluent(X), \+ cpa_initially(X), \+ unknown(X).
unknown(X):- fluent(X),
            findall(L, (cpa_initially(cpa_oneof(Y)), member(L,Y)), LUnk),
            member(X, LUnk).
unknown(X):- fluent(X), cpa_unknown(X).
unknown(X) :- fluent(X), (cpa_initially(cpa_or(Y)),in_or(Y,X);
          cpa_initially(cpa_or(Y,Z)), (in_or(Y,X);in_or(Z,X))), !.
unknown(X) :- fluent(X), cpa_initially(cpa_oneof(ListBig)), member(ListSmall,ListBig),
           member(X,ListSmall).
in_or(X,X) :- !.
in_or(neg(X),X) :- !.
in_or(cpa_or(Y),X) :- in_or(Y,X).
in_or(cpa_or(Y,Z),X) :- (in_or(Y,X);in_or(Z,X)).
cpa_unknown(nop).

%%%% Goals %%%%
plan_goal(cpa_ontable(cpa_a)).
plan_goal(cpa_on(cpa_b, cpa_a)).
