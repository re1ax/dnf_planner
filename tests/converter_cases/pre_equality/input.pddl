(define (domain demo) (:requirements :strips :typing) (:types thing)  (:predicates (p ?x - thing) (q ?x - thing) (r))  (:action act :parameters (?x ?y - thing) :precondition (and (= ?x ?y) (not (= ?x a))) :effect (r)))
(define (problem task) (:domain demo) (:objects a b - thing) (:init (and (p a))) (:goal (q a)))
