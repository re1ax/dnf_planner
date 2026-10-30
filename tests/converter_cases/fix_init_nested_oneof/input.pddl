(define (domain d) (:requirements :typing) (:types t) (:predicates (p ?x - t) (q ?x - t) (z)) )
(define (problem x) (:domain d) (:objects a - t) (:init (and (oneof (oneof (p a) (q a)) (z)))) (:goal (and (p a))))
