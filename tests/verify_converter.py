#!/usr/bin/env python3
"""Compare a converter against original executable golden files; no third-party deps.

Usage: python tests/verify_converter.py --command python converter/pddl2pl.py
The input filename is appended to --command. Every invocation has an isolated cwd.
Canonical comparison removes Prolog whitespace/comments only, preserving clause and
token order. It does not prove Prolog executability or full PDDL semantic support.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]

def canonical(data):
    text=data.decode('utf-8', errors='replace')
    text=re.sub(r'%[^\n]*','',text)
    return re.findall(r"'(?:''|[^'])*'|\"(?:\\.|[^\"])*\"|[A-Za-z_?][A-Za-z_?0-9]*|[0-9]+|:-|\\\+|[^\s]",text)

def first_difference(a,b):
    for i,(x,y) in enumerate(zip(a,b)):
        if x!=y:return i
    return min(len(a),len(b)) if len(a)!=len(b) else None

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--command',nargs='+',default=[sys.executable,str(ROOT/'converter/pddl2pl.py')])
    args=parser.parse_args()
    command=[str(Path(x).resolve()) if Path(x).exists() else x for x in args.command]
    oracle=json.loads((ROOT/'evidence/converter_oracle.json').read_text())
    report=dict(original_sha256=oracle['sha256'],command=command,timeout_seconds=3,
                canonical_scope='Comment/whitespace-insensitive Prolog token sequence; ordering preserved; not semantic proof',cases=[])
    for golden in oracle['records']:
        case=golden['case']; fixture=ROOT/'tests/converter_cases'/case/'input.pddl'
        expected_path=ROOT/golden.get('output','__absent__')
        expected=expected_path.read_bytes() if golden.get('output_sha256') and expected_path.exists() else None
        with tempfile.TemporaryDirectory(prefix='converter_verify_',dir=ROOT/'tests') as tmp:
            cwd=Path(tmp);(cwd/'input.pddl').write_bytes(fixture.read_bytes())
            try:
                proc=subprocess.run([*command,'input.pddl'],cwd=cwd,capture_output=True,timeout=3)
                code=proc.returncode;stdout=proc.stdout.decode(errors='replace');stderr=proc.stderr.decode(errors='replace');timedout=False
            except subprocess.TimeoutExpired as e:
                code=124;stdout=(e.stdout or b'').decode(errors='replace');stderr=(e.stderr or b'').decode(errors='replace');timedout=True
            output=cwd/'pddl2pl.pl';actual=output.read_bytes() if output.exists() else None
        accepted=(golden['returncode']==0)==(code==0)
        both=expected is not None and actual is not None
        byte_equal=expected==actual
        can_equal=canonical(expected)==canonical(actual) if both else byte_equal
        reason=[]
        if not accepted:reason.append('accept/reject differs')
        if (expected is None)!=(actual is None):reason.append('output presence differs')
        if both and not byte_equal:reason.append('output bytes differ')
        if both and not can_equal:reason.append('canonical token sequence differs')
        item=dict(case=case,result='pass' if accepted and byte_equal else 'difference',
                  acceptance_equal=accepted,byte_equal=byte_equal,canonical_equal=can_equal,
                  reason='; '.join(reason) or 'acceptance and output bytes match',
                  original_returncode=golden['returncode'],returncode=code,timeout=timedout,
                  stdout=stdout,stderr=stderr,
                  output_sha256=hashlib.sha256(actual).hexdigest() if actual is not None else None)
        if both:
            item['first_byte_difference']=first_difference(expected,actual)
            item['first_token_difference']=first_difference(canonical(expected),canonical(actual))
        report['cases'].append(item)
    report['summary']=dict(total=len(report['cases']),byte_pass=sum(x['acceptance_equal'] and x['byte_equal'] for x in report['cases']),
                           canonical_pass=sum(x['acceptance_equal'] and x['canonical_equal'] for x in report['cases']))
    (ROOT/'evidence/converter_differential.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report['summary'],indent=2))
    for c in report['cases']:
        if c['result']!='pass':print(c['case'],c['reason'])
    return int(report['summary']['byte_pass']!=report['summary']['total'])

if __name__=='__main__':raise SystemExit(main())
