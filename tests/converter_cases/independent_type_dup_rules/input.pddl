(define (domain d) (:requirements :typing) (:types t - root root) (:types u - other other) (:predicates (p ?x - t)))
(define (problem x) (:domain d) (:objects a - t) (:init (and (p a))) (:goal (and (p a))))
