(define (domain d) (:requirements :typing) (:types t) (:predicates (p ?x - t) (q ?x - t) (z)) (:action a :parameters (?x - t) :precondition (unknown (p ?x)) :effect (z)))
(define (problem x) (:domain d) (:objects a - t) (:init (and (p a))) (:goal (and (p a))))
