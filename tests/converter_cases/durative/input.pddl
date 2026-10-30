(define (domain demo) (:requirements :strips :typing) (:types thing)  (:predicates (p ?x - thing) (q ?x - thing) (r))  (:durative-action act :parameters (?x - thing) :duration (= ?duration 1) :condition (at start (p ?x)) :effect (at end (q ?x))))
(define (problem task) (:domain demo) (:objects a b - thing) (:init (and (p a))) (:goal (q a)))
