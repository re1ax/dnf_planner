(define (domain d) (:requirements :typing) (:predicates (p ?x - t) (q ?x - t)) (:types t))
(define (problem x) (:domain d) (:objects a - t) (:init (and (p a))) (:goal (and (p a))))
