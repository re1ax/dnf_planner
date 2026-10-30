(define (domain demo) (:requirements :strips :typing) (:types animal - object dog cat - animal)  (:predicates (p ?x - animal) (q ?x - dog) (r))  (:action act :parameters (?x - animal) :precondition (p ?x) :effect (r)))
(define (problem task) (:domain demo) (:objects a - dog b - cat) (:init (and (p a))) (:goal (r)))
