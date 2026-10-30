(define (domain demo) (:requirements :strips :typing) (:types thing)  (:predicates)  (:action act :parameters (?x - thing) :precondition (p ?x) :effect (q ?x)))
(define (problem task) (:domain demo) (:objects a b - thing) (:init (and (p a))) (:goal (q a)))
