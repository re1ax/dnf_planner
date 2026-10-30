(define (domain d) (:requirements :typing) (:types t) (:predicates (p ?x - t)) (:action a :parameters () :precondition (forall (?x - missing) (p ?x)) :effect (p a)))
(define (problem x) (:domain d) (:objects a - t) (:init (and (p a))) (:goal (and (p a))))
