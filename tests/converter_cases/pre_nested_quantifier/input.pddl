(define (domain demo) (:requirements :strips :typing) (:types thing)  (:predicates (p ?x - thing) (q ?x - thing) (r))  (:action act :parameters () :precondition (forall (?x - thing) (exists (?y - thing) (and (p ?x) (q ?y)))) :effect (r)))
(define (problem task) (:domain demo) (:objects a b - thing) (:init (and (p a))) (:goal (q a)))
