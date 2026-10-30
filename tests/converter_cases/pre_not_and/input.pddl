(define (domain demo) (:requirements :strips :typing) (:types thing)  (:predicates (p ?x - thing) (q ?x - thing) (r))  (:action act :parameters (?x - thing) :precondition (not (and (p ?x) (q ?x))) :effect (r)))
(define (problem task) (:domain demo) (:objects a b - thing) (:init (and (p a))) (:goal (q a)))
