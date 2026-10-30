
:- use_module(library(lists)).
:- dynamic executable/2.
:- dynamic cpa_executable/2.
:- dynamic causes/3.
:- dynamic cpa_causes/3.
:- dynamic cpa_initially/1.

%%%% Objects %%%%
cpa_thing_type(cpa_obj_1).
cpa_thing_type(cpa_obj2).

%%%% Constants %%%%

%%%%  Types rules %%%%

%%%% Predicates %%%%
fluent(cpa_p(  X)):-
	cpa_thing_type( X).

fluent(cpa_q(  X)):-
	cpa_thing_type( X).

fluent(cpa_r).


%%%% Actions %%%%
action(cpa_mix_act(  X)):-
	cpa_thing_type( X).


%%%% Preconditions %%%%
executable(cpa_mix_act(  X), [
cpa_p( X) ]):-
	cpa_thing_type( X).


%%%% Effects %%%%
causes(cpa_mix_act(  X), [
cpa_q( X) ], 
[]):-
	cpa_thing_type( X).


%%%% Inits %%%%
cpa_initially(cpa_p(cpa_obj_1)).
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
plan_goal(cpa_q(cpa_obj_1)).
