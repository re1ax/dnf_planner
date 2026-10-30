(define (domain d) (:requirements :typing) (:types t) (:constants c - object) (:predicates (p ?x - object)) (:action a :parameters (?x - object) :effect (p ?x)))
(define (problem x) (:domain d) (:objects a - object) (:init (and (p a))) (:goal (and (p a))))
