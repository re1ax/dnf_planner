(define (domain demo) (:requirements :strips :typing) (:types thing)  (:predicates (p ?x - thing) (q ?x - thing) (r)) (:functions (fuel ?x - thing)) (:action act :parameters (?x - thing) :effect (decrease (fuel ?x) 1)))
(define (problem task) (:domain demo) (:objects a b - thing) (:init (and (p a))) (:goal (q a)))
