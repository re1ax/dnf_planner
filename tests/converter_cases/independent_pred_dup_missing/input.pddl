(define (domain d) (:requirements :typing) (:types t) (:predicates (p ?x - missing)) (:predicates (p ?x - t)))
(define (problem x) (:domain d) (:objects a - t) (:init (and (p a))) (:goal (and (p a))))
