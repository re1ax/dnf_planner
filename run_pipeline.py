#!/usr/bin/env python3
"""Recovered PDDL -> Prolog -> original preprocessing -> AL -> DNF pipeline.

No original executable is used by this runner. Original executables are only
test oracles. The preprocessing engine is SWI with documented dialect adapters.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parent

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module

def standalone_theories(theories,output):
    """Materialize shared declarations/init for later original theory fragments.

    The original generator prints globals only in its first file. This explicit
    serialization adapter keeps raw output intact; it does not merge plans.
    """
    first=theories[0].read_text(encoding='utf-8')
    declarations=re.findall(r'\bfluent\s+[^;]*;',first)
    initials=re.findall(r'\binitially\s+[^;]*;',first)
    folder=output/'standalone';folder.mkdir(exist_ok=True)
    result=[]
    for theory in theories:
        text=theory.read_text(encoding='utf-8')
        inherited=[]
        if not re.search(r'\bfluent\s',text) and declarations:
            text='\n'.join(declarations)+'\n'+text;inherited.append('fluent declarations')
        if not re.search(r'\binitially\s',text) and initials:
            match=re.search(r'\bgoal\s',text)
            if match:
                text=text[:match.start()]+'\n'.join(initials)+'\n'+text[match.start():]
                inherited.append('initial constraints')
        dest=folder/theory.name;dest.write_text(text,encoding='utf-8',newline='\n')
        result.append((dest,inherited))
    return result

def run(domain,problem=None,output=None,mode='faithful',options=None,runtime=None,timeout=60,planner=None):
    output=Path(output or Path.cwd()/'dnf_run').resolve()
    output.mkdir(parents=True,exist_ok=True)
    if any(output.iterdir()):
        raise ValueError('output directory must be empty; choose a new directory to keep each run isolated')
    # Preserve raw bytes until the recovered scanner has applied original rules.
    text=Path(domain).read_bytes().decode('utf-8')
    if problem:text+='\n'+Path(problem).read_bytes().decode('utf-8')
    sys.path.insert(0,str(ROOT/'converter'))
    converter=load(ROOT/'converter/pddl2pl.py','recovered_pddl2pl')
    prolog,diagnostics=converter.convert_with_diagnostics(text)
    instance=output/'pddl2pl.pl'
    instance.write_bytes(prolog.encode('utf-8'))
    if any('ERROR:' in diagnostic for diagnostic in diagnostics):
        report={'status':'converter_semantic_error','converter_diagnostics':diagnostics,'planner_runs':[],'mode':mode}
        (output/'pipeline.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        raise RuntimeError('original converter semantic error: '+''.join(diagnostics).strip())
    preprocessor=load(ROOT/'preprocessor/run_preprocessor.py','recovered_preprocessor')
    pre=preprocessor.run(instance,output/'preprocessed',runtime=runtime,mode=mode,options=options,timeout=timeout)
    report={'converter':'reconstructed source, no original binary','converter_diagnostics':diagnostics,'preprocessor':pre,'planner_runs':[],'mode':mode}
    theories=sorted((output/'preprocessed/normalized').glob('theory_*.al'))
    if not theories or pre.get('returncode')!=0 or pre.get('timeout') or 'ERROR:' in pre.get('stderr',''):
        report['status']='preprocessor_failed'
        (output/'pipeline.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        raise RuntimeError('preprocessor produced no normalized theories; inspect '+str(output/'pipeline.json'))
    binary=Path(planner).resolve() if planner else ROOT/('dnf.exe' if os.name=='nt' else 'dnf')
    executable_theories=standalone_theories(theories,output)
    report['solution_scope']='each generated theory separately; no combined-plan claim' if len(theories)>1 else 'single theory'
    for theory,inherited in executable_theories:
        completed=subprocess.run([str(binary),str(theory),'--timeout',str(timeout)],capture_output=True,text=True,timeout=timeout+5)
        rec={'theory':str(theory),'inherited_globals':inherited,'returncode':completed.returncode,'stdout':completed.stdout,'stderr':completed.stderr}
        report['planner_runs'].append(rec)
        (output/(theory.stem+'.plan.txt')).write_text(completed.stdout,encoding='utf-8')
    report['status']='completed' if all(x['returncode']==0 for x in report['planner_runs']) else 'planner_failed'
    # Multiple theories are reported independently: no unsupported plan merge.
    (output/'pipeline.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('domain',type=Path);ap.add_argument('problem',nargs='?',type=Path)
    ap.add_argument('-o','--output',type=Path,default=Path('dnf_run'))
    ap.add_argument('--mode',choices=['faithful','repaired'],default='faithful')
    ap.add_argument('--options',help='comma-separated original options; empty enables optional paths')
    ap.add_argument('--runtime',type=Path);ap.add_argument('--planner',type=Path)
    ap.add_argument('--timeout',type=float,default=60)
    a=ap.parse_args()
    try:
        report=run(a.domain,a.problem,a.output,a.mode,None if a.options is None else [x for x in a.options.split(',') if x],a.runtime,a.timeout,a.planner)
        for rec in report['planner_runs']:print(rec['stdout'],end='')
        print('Pipeline evidence:',(a.output/'pipeline.json').resolve())
        return 0 if report['status']=='completed' else 1
    except (ValueError,RuntimeError,OSError,subprocess.SubprocessError) as e:
        print('ERROR:',e,file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
