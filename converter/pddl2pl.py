#!/usr/bin/env python3
"""Reconstruction of cpa.pddl2pl's observed Prolog emitter.

The original lexer/parser tables validate acceptance before emission. Historical
printer defects are intentionally preserved; this is not a modern PDDL compiler.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

try:
    from .original_syntax import validate, tokens as original_tokens
except ImportError:
    from original_syntax import validate, tokens as original_tokens


class ConversionError(ValueError):
    """Input cannot be represented by the recovered converter."""


HEADER = """
:- use_module(library(lists)).
:- dynamic executable/2.
:- dynamic cpa_executable/2.
:- dynamic causes/3.
:- dynamic cpa_causes/3.
:- dynamic cpa_initially/1.
"""
CLOSED_WORLD = r"""cpa_initially(neg(X)) :- fluent(X), \+ cpa_initially(X), \+ unknown(X).
unknown(X):- fluent(X),
            findall(L, (cpa_initially(cpa_oneof(Y)), member(L,Y)), LUnk),
            member(X, LUnk).
unknown(X):- fluent(X), cpa_unknown(X).
unknown(X) :- fluent(X), (cpa_initially(cpa_or(Y)),in_or(Y,X);
          cpa_initially(cpa_or(Y,Z)), (in_or(Y,X);in_or(Z,X))), !.
unknown(X) :- fluent(X), cpa_initially(cpa_oneof(ListBig)), member(ListSmall,ListBig),
           member(X,ListSmall).
in_or(X,X) :- !.
in_or(neg(X),X) :- !.
in_or(cpa_or(Y),X) :- in_or(Y,X).
in_or(cpa_or(Y,Z),X) :- (in_or(Y,X);in_or(Z,X)).
cpa_unknown(nop).
"""


def parse(text):
    tokens = (fragment.lower() for token, fragment, _ in original_tokens(text) if token)
    roots, stack = [], []
    for t in tokens:
        if t == '(':
            node = []
            (stack[-1] if stack else roots).append(node)
            stack.append(node)
        elif t == ')':
            if not stack:
                raise ConversionError('unmatched parenthesis')
            stack.pop()
        elif stack:
            stack[-1].append(t)
        else:
            raise ConversionError('token outside definition')
    if stack:
        raise ConversionError('unclosed parenthesis')
    return roots


def name(s):
    return 'cpa_' + s.replace('-', '_')


def term(s):
    return (' ' + s[1:].replace('-', '_').upper()) if s.startswith('?') else name(s)


def typed(items):
    """Preserve source order and PDDL's grouped type annotations."""
    out, pending, i = [], [], 0
    while i < len(items):
        if items[i] == '-':
            if i + 1 >= len(items):
                raise ConversionError('missing type')
            ty = items[i + 1]
            either = isinstance(ty, list) and ty[:1] == ['either']
            tys = ty[1:] if either else [ty]
            out.extend((x, tys, 'either' if either else True) for x in pending)
            pending = []
            i += 2
        else:
            pending.append(items[i])
            i += 1
    out.extend((x, ['object'], False) for x in pending)
    return out


def atom(a, declaration=False):
    if not a:
        return ''
    head = name('equal' if a[0] == '=' else a[0])
    if len(a) == 1:
        return head
    args = ', '.join(term(x) for x in a[1:])
    if declaration:
        args = ' ' + args
    return head + '(' + args + ')'


def fold(op, values):
    if not values:
        return ''
    r = 'cpa_' + op + '( ' + values[0] + ')'
    for v in values[1:]:
        r = 'cpa_' + op + '( ' + r + ', ' + v + ')'
    return r


def formula(a, mode='normal', when_body=False):
    if a is None or not a:
        return ''
    op, xs = a[0], a[1:]
    if op in ('and', 'or'):
        vals = [formula(x, mode) for x in xs]
        if op == 'and' and mode in ('goal', 'init'):
            return (').\nplan_goal(' if mode == 'goal' else ').\ncpa_initially(').join(vals)
        if op == 'and' and when_body and len(xs) > 1:
            return 'cpa_and( ' + vals[0] + ', ' + fold('and', vals[1:]) + ')'
        if op == 'and' and when_body and len(xs) == 1:
            return 'cpa_and( ' + vals[0] + ', )'
        return fold(op, vals)
    if op == 'not':
        child = xs[0]
        if child and child[0] not in ('and', 'or', 'not', 'imply', 'forall', 'exists'):
            return 'neg(' + formula(child, mode) + ')'
        return 'NOT ( ' + formula(child, mode) + ')'
    if op == 'imply':
        return 'cpa_or( NOT ( ' + formula(xs[0], mode) + '), ' + formula(xs[1], mode) + ')'
    if op == 'when':
        return 'cpa_when( ' + formula(xs[0], mode) + ', ' + formula(xs[1], mode, True) + ')'
    if op in ('forall', 'exists'):
        variables = ''.join(x for x, _, _ in typed(xs[0]))
        return 'cpa_' + ('exist' if op == 'exists' else op) + variables + '( ' + formula(xs[1], mode) + ')'
    if op == 'oneof':
        if mode != 'init':
            return 'cpa_oneof' + ('( ' + fold('or', [formula(x, mode) for x in xs]) + ')' if xs else '')
        def alternative(x):
            if x and x[0] in ('oneof', 'unknown'):
                return ''
            if x and x[0] == 'or':
                return ', '.join(alternative(y) for y in x[1:])
            if x and x[0] == 'and':
                return '[' + ', '.join(formula(y) for y in x[1:]) + ']'
            return formula(x)
        return 'cpa_oneof([' + ', '.join(alternative(x) for x in xs) + '])'
    if op == 'unknown':
        p = formula(xs[0], mode)
        opposite = formula(xs[0][1], mode) if xs[0][:1] == ['not'] else 'neg(' + p + ')'
        if mode != 'init':
            return 'cpa_oneof( ' + fold('or', [p, 'cpa_and( ' + opposite + ')']) + ')'
        return 'cpa_oneof([' + p + ', [' + opposite + ']])'
    if any(isinstance(x, list) for x in xs):
        raise ConversionError('unrecovered expression: ' + op)
    return atom(a)


def constraints(params):
    # Original either printer concatenates alternatives without a separator.
    return ', '.join(''.join(name(ty) + '(' + term(v) + ')' for ty in tys)
                     for v, tys, _ in params)


def suffix(params):
    return (':-\n\t' + constraints(params) if params else '') + '.\n\n'


def _type_error(roots):
    declared = set()

    def check(items):
        for _, tys, explicit in typed(items):
            if explicit is True:
                for ty in tys:
                    if ty not in declared:
                        return ty
        return None

    def binders(node):
        if not isinstance(node, list) or not node:
            return None
        if node[0] in ('forall', 'exists'):
            error = check(node[1])
            if error:
                return error
            return binders(node[2])
        for child in node:
            if isinstance(child, list):
                error = binders(child)
                if error:
                    return error
        return None

    for root in roots:
        for sec in root[2:]:
            if not isinstance(sec, list) or not sec:
                continue
            if sec[0] == ':types':
                declared.update(v for v, _, _ in typed(sec[1:]))
            elif sec[0] == ':predicates':
                for p in sec[1:]:
                    error = check(p[1:])
                    if error:
                        return error
            elif sec[0] == ':action':
                props = dict(zip(sec[2::2], sec[3::2]))
                error = check(props.get(':parameters', []))
                if error:
                    return error
                error = binders(props.get(':precondition')) or binders(props.get(':effect'))
                if error:
                    return error
            else:
                error = binders(sec)
                if error:
                    return error
    return None


def _convert(text, diagnostics):
    validate(text)
    roots = parse(text)
    for token, fragment, _ in original_tokens(text):
        if fragment == ':constraints':
            diagnostics.append('System has not support constraints\n')
    domain = next((r for r in roots if len(r) > 1 and r[1][:1] == ['domain']), None)
    problem = next((r for r in roots if len(r) > 1 and r[1][:1] == ['problem']), None)
    if domain is None or problem is None:
        raise ConversionError('a domain and problem definition are required')
    ds = {s[0]: s[1:] for s in domain[2:] if isinstance(s, list) and s and s[0] != ':action'}
    ps = {s[0]: s[1:] for s in problem[2:] if isinstance(s, list) and s}
    # A semantic type error prevents the original start reduction from assigning
    # the global Reader. Its caller nevertheless emits the default empty Reader.
    error = _type_error(roots)
    if error:
        diagnostics.append('\nERROR: undeclared type ' + error + '\n')
        ds, ps, domain = {}, {}, ['define', ['domain', '']]
    actions = []
    for sec in domain[2:]:
        if not isinstance(sec, list) or sec[:1] != [':action']:
            continue
        props = dict(zip(sec[2::2], sec[3::2]))
        params = typed(props.get(':parameters', []))
        actions.append((atom([sec[1]] + [v for v, _, _ in params], True), params,
                        props.get(':precondition'), props.get(':effect')))
    out = [HEADER, '\n%%%% Objects %%%%\n']
    for v, tys, explicit in typed(ps.get(':objects', [])):
        out.extend(name(ty) + '(' + name(v) + ').\n' for ty in tys)
    out.append('\n%%%% Constants %%%%\n')
    for v, tys, explicit in typed(ds.get(':constants', [])):
        if not explicit:
            out.append(name(v) + '.\n')
        out.extend(name(ty) + '(' + name(v) + ').\n' for ty in tys)
    out.append('\n%%%%  Types rules %%%%\n')
    for v, tys, explicit in typed(ds.get(':types', [])):
        for ty in tys:
            if ty != 'object':
                out.append(name(ty) + '(X):- ' + name(v) + '(X).\n')
    out.append('\n%%%% Predicates %%%%\n')
    for pred in ds.get(':predicates', []):
        params = typed(pred[1:])
        out.append('fluent(' + atom([pred[0]] + [v for v, _, _ in params], True) + ')' + suffix(params))
    out.append('\n%%%% Actions %%%%\n')
    for a, params, pre, eff in actions:
        out.append('action(' + a + ')' + suffix(params))
    out.append('\n%%%% Preconditions %%%%\n')
    for a, params, pre, eff in actions:
        out.append('executable(' + a + ', [\n' + formula(pre) + ' ])' + suffix(params))
    out.append('\n%%%% Effects %%%%\n')
    for a, params, pre, eff in actions:
        out.append('causes(' + a + ', [\n' + formula(eff) + ' ], \n[])' + suffix(params))
    out.append('\n%%%% Inits %%%%\n')
    init = ps.get(':init', [None])
    out.append('cpa_initially(' + formula(init[0] if init else None, 'init') + ').\n')
    out.append(CLOSED_WORLD)
    out.append('\n%%%% Goals %%%%\n')
    goal = ps.get(':goal', [None])
    out.append('plan_goal(' + formula(goal[0] if goal else None, 'goal') + ').\n')
    return ''.join(out)


def convert(text: str) -> str:
    """Return the original converter's Prolog text, or raise on invalid syntax."""
    return _convert(text, [])


def convert_with_diagnostics(text: str) -> tuple[str, list[str]]:
    """Return text and original semantic warnings, without printing them."""
    diagnostics = []
    return _convert(text, diagnostics), diagnostics


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('-o', '--output', type=Path, default=Path('pddl2pl.pl'))
    args = parser.parse_args(argv)
    diagnostics = []
    try:
        with args.input.open('r', encoding='utf-8', newline='') as f:
            result = _convert(f.read(), diagnostics)
        args.output.write_text(result, encoding='utf-8', newline='\n')
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(''.join(diagnostics) + 'Converting pddl to pl\nOutput file: ' + str(args.output) + '\n\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
