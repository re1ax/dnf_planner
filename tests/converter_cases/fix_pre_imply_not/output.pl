
:- use_module(library(lists)).
:- dynamic executable/2.
:- dynamic cpa_executable/2.
:- dynamic causes/3.
:- dynamic cpa_causes/3.
:- dynamic cpa_initially/1.

%%%% Objects %%%%
cpa_t(cpa_a).

%%%% Constants %%%%

%%%%  Types rules %%%%

%%%% Predicates %%%%
fluent(cpa_p(  X)):-
	cpa_t( X).

fluent(cpa_q(  X)):-
	cpa_t( X).

fluent(cpa_z).


%%%% Actions %%%%
action(cpa_a(  X)):-
	cpa_t( X).


%%%% Preconditions %%%%
executable(cpa_a(  X), [
cpa_or( NOT ( neg(cpa_p( X))), cpa_q( X)) ]):-
	cpa_t( X).


%%%% Effects %%%%
causes(cpa_a(  X), [
cpa_z ], 
[]):-
	cpa_t( X).


%%%% Inits %%%%
cpa_initially(cpa_p(cpa_a)).
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
plan_goal(cpa_p(cpa_a)).
