/* SWI compatibility only; no preprocessing algorithm changes. */
:- use_module(library(lists)).
:- use_module(library(ordsets)).
:- dynamic dep/2, time_actions/2, level/3, name_index/1.
:- dynamic cpa_executable/2, cpa_causes/3, cpa_initially/1.
:- dynamic executable/2, causes/3.
:- style_check(-singleton).
:- style_check(-discontiguous).

/* SICStus lists:remove_dups/2 is absent from SWI's lists module.
   list_to_set/2 retains the leftmost occurrence; record this compatibility
   choice because duplicate ordering can affect generated text/search order. */
remove_dups(Input, Output) :- list_to_set(Input, Output).
