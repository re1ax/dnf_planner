(define (domain demo) (:requirements :strips :typing)   (:predicates (p ?x) (q ?x) (r))  (:action act :parameters (?x) :precondition (p ?x) :effect (q ?x)))
(define (problem task) (:domain demo) (:objects a b) (:init (and (p a))) (:goal (q a)))
