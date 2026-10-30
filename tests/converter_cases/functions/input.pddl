(define (domain demo) (:requirements :strips :typing) (:types thing)  (:predicates (p ?x - thing) (q ?x - thing) (r)) (:functions (fuel ?x - thing)) (:action act :parameters (?x - thing) :precondition (p ?x) :effect (q ?x)))
(define (problem task) (:domain demo) (:objects a b - thing) (:init (and (p a) (= (fuel a) 10))) (:goal (q a)))
