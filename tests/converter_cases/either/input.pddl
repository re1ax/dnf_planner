(define (domain demo) (:requirements :strips :typing) (:types dog cat)  (:predicates (p ?x - (either dog cat)) (r))  (:action act :parameters (?x - (either dog cat)) :precondition (p ?x) :effect (r)))
(define (problem task) (:domain demo) (:objects a - dog b - cat) (:init (and (p a))) (:goal (r)))
