(define (domain d) (:requirements :typing) (:types t) (:predicates (p ?x - t) (q ?x - t) (z)) )
(define (problem x) (:domain d) (:objects a - t) (:init (or (and (p a) (q a)) (p a))) (:goal (and (p a))))
