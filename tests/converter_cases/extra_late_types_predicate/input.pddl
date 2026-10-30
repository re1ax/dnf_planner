(define (domain demo) (:requirements :strips :typing)  (:predicates (p ?x - thing) (q ?x - thing) (r))  (:types thing) (:action act :parameters (?x - thing) :precondition (p ?x) :effect (q ?x)))
(define (problem task) (:domain demo) (:objects a b - thing) (:init (and (p a))) (:goal (q a)))
