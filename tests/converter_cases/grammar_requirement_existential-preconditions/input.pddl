(define (domain demo) (:requirements :existential-preconditions) (:types thing)  (:predicates (p ?x - thing) (q ?x - thing) (r))  (:action act :parameters (?x - thing) :precondition (p ?x) :effect (q ?x)))
(define (problem task) (:domain demo) (:objects a b - thing) (:init (and (p a))) (:goal (q a)))
