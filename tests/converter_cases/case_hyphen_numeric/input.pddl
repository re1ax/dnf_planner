(define (domain DeMo-42) (:requirements :strips :typing) (:types Thing-Type)  (:predicates (p ?x - Thing-Type) (q ?x - Thing-Type) (r))  (:action Mix-Act :parameters (?x - Thing-Type) :precondition (p ?x) :effect (q ?x)))
(define (problem task) (:domain DeMo-42) (:objects Obj-1 Obj2 - Thing-Type) (:init (and (p Obj-1))) (:goal (q Obj-1)))
