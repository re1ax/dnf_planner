(define (domain demo) (:requirements :strips :typing) (:types thing) (:constants fixed - thing) (:predicates (p ?x - thing) (q ?x - thing) (r))  (:action act :parameters (?x - thing) :precondition (p ?x) :effect (q ?x)))
(define (problem task) (:domain demo) (:objects a b - thing) (:init (and (p fixed))) (:goal (q fixed)))
