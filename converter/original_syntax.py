"""Flex/Bison recognition tables recovered from the supplied ELF.

This validates original syntax; it does not execute the original binary.
Semantic reconstruction is in pddl2pl.py. Table provenance is in original_tables.json.
"""
import json
from pathlib import Path

DATA=json.loads(Path(__file__).with_name('original_tables.json').read_text(encoding='utf-8'))
T=DATA['tables']

class OriginalSyntaxError(ValueError):
    pass

def tokens(text):
    raw=text.encode('utf-8')
    raw+=b'\0'
    pos=0; line=1
    while pos<len(raw)-1:
        state=1;scan=pos;last=None
        while True:
            if T['yy_accept'][state]:last=(scan,T['yy_accept'][state])
            ch=raw[scan] if scan<len(raw) else 0
            cls=T['yy_ec'][ch]
            while T['yy_chk'][T['yy_base'][state]+cls]!=state:
                state=T['yy_def'][state]
                if state>424:cls=T['yy_meta'][cls]
            state=T['yy_nxt'][T['yy_base'][state]+cls]
            scan+=1
            if T['yy_base'][state]==446:break
        if T['yy_accept'][state]:last=(scan,T['yy_accept'][state])
        if not last or last[0]<=pos:
            raise OriginalSyntaxError(f'line {line}: scanner did not advance')
        end,rule=last
        fragment=raw[pos:end]
        if rule==60:
            # Recovered trailing-context action performs yyless(yyleng-1).
            end-=1;fragment=raw[pos:end]
        candidates=DATA['lexer']['rules'][str(rule)]['tokens']
        if candidates:
            if len(candidates)!=1:raise OriginalSyntaxError('ambiguous recovered lexer action')
            yield candidates[0],fragment.decode('utf-8','replace'),line
        elif rule==63:
            raise OriginalSyntaxError(f'line {line}: invalid token {fragment!r}')
        elif rule not in (58,59,60,62,64):
            raise OriginalSyntaxError(f'line {line}: unsupported scanner action {rule}')
        line+=fragment.count(b'\n');pos=end
    yield 0,'',line

def validate(text,trace=False):
    stream=iter(tokens(text));look=None;stack=[0];reductions=[]
    for _ in range(1000000):
        state=stack[-1];base=T['yypact'][state]
        action=None
        if base!=-140:
            if look is None:look=next(stream)
            ext=look[0];tok=T['yytranslate'][ext] if ext<len(T['yytranslate']) else 2
            index=base+tok
            if 0<=index<=279 and T['yycheck'][index]==tok:
                action=T['yytable'][index]
        if action is not None and action>0:
            if action==4:return reductions if trace else True
            stack.append(action);look=None;continue
        rule=T['yydefact'][state] if action is None else -action
        if rule<=0:
            if look is None:look=next(stream)
            raise OriginalSyntaxError(f'line {look[2]}: original grammar rejects {look[1]!r} (state {state})')
        count=T['yyr2'][rule]
        if count:del stack[-count:]
        lhs=T['yyr1'][rule]-61
        index=T['yypgoto'][lhs]+stack[-1]
        goto=T['yytable'][index] if 0<=index<=279 and T['yycheck'][index]==stack[-1] else T['yydefgoto'][lhs]
        stack.append(goto);reductions.append(rule)
    raise OriginalSyntaxError('parser operation limit exceeded')

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('--tokens',action='store_true');a=ap.parse_args()
    txt=a.input.read_bytes().decode('utf-8')
    if a.tokens:
        for row in tokens(txt):print(row)
    else:print(validate(txt,trace=True))
