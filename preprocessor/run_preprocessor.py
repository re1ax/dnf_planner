#!/usr/bin/env python3
"""Run the shipped Prolog preprocessor in an isolated SWI process.

The original mult5zsic.pl remains byte-identical in original/. faithful mode
adds only a SWI compatibility prelude. repaired applies the explicitly listed
source corrections, never inventing unfinished optimizations.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

HERE = Path(__file__).resolve().parent
OPTIONS = {"noforward", "noanalyze", "no_goal_split", "no_oneof", "no_duals"}
DEFAULT = ["no_duals", "no_goal_split"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def repaired_source(source):
    patches = [
        ("constant-negative-membership", "member(neg(F),AF).", "member(F,AF)."),
        ("time-index", "Applied,NewOnes,T,NegCons)", "Applied,NewOnes,InT,NegCons)"),
        ("time-index-binding", "T1 is InT+1,", "T1 is InT+1, T = InT,"),
        ("dual-recursion-typo", "check_init_dualsRest(Rest,Rest1).", "check_init_duals(Rest,Rest1)."),
        ("dual-action-variable", "(action(A),     %member(Act,Actions)", "(member(Act,Actions), % original typo: action(A)"),
        ("dual-assert", "\tduals(A,B),\n\tassert_duals(Rest).", "\tassertz(duals(A,B)),\n\tassert_duals(Rest)."),
        ("dual-persistence", "determine_duals(Cleaned1),\n\t                              retractall(duals(_,_))", "retractall(duals(_,_)),\n\t                              determine_duals(Cleaned1)"),
        ("dual-repeat-membership", "(A=X; B=X), !, remove_all_containing(Y,X,Z).", "(member(A,X); member(B,X)), !, remove_all_containing(Y,X,Z)."),
        ("dual-repeat-grounding", "twice(X,In) :-\n\tfindall", "twice(X,In) :-\n\t(member((X,_),In); member((_,X),In)),\n\tfindall"),
        ("dual-initial-output", '[A,neg(A)]),!.', '[A,A]),!.'),
        ("atomic-unconditional-effect",
         "/* base */\ncv_when(cpa_when(X,Y), Z1, Z2):-",
         "/* REPAIRED: the shipped converter may emit a bare literal effect. */\n"
         "cv_when(Input, [], [Input]) :-\n"
         "  functor(Input,F,_), \\+ member(F,[cpa_and,cpa_or,cpa_when]).\n\n"
         "/* base */\ncv_when(cpa_when(X,Y), Z1, Z2):-"),
    ]
    changes = []
    for name, before, after in patches:
        count = source.count(before)
        if count != 1:
            raise ValueError(f"patch {name}: expected 1 match, found {count}")
        source = source.replace(before, after)
        changes.append(name)
    # Retain declared constant atoms and their initial truth values. Original
    # output pruning could leave a constant goal undeclared or an empty init.
    patterns = [
        ("preserve-constant-fluent-output",
         r"dump_fluents\(\[A\|B\],In\):-.*?(?=dump_fluents\(\[A\|B\],In\) :-)") ,
        ("preserve-constant-initial-output",
         r"dump_initial_sum\(\[A\|B\]\) :-\n\t\(always_true.*?(?=dump_initial_sum\(\[A\|B\]\) :-\n        fluent\(A\))"),
    ]
    for name, pattern in patterns:
        source, count = re.subn(pattern, "", source, flags=re.S)
        if count != 1:
            raise ValueError(f"patch {name}: expected 1 block, found {count}")
        changes.append(name)
    branch_edits = [
        ("all-executable-branches-invalid",
         r"invalidated\(A,AT,_AF\) :-.*?(?=%%\ncheck_for_wrong_consequence)",
         "invalidated(A,AT,AF) :-\n"
         "  findall(C,cpa_executable(A,C),Branches), Branches=[_|_],\n"
         "  \\+ (member(C,Branches), \\+ repaired_bad_branch(C,AT,AF)).\n"
         "repaired_bad_branch(C,AT,AF) :-\n"
         "  (member(neg(F),C),member(F,AT);\n"
         "   member(F,C), \\+ (F=neg(_)), member(F,AF)).\n\n%%\n"),
        ("output-action-any-valid-executable-branch",
         r"get_real_actions\(\[R\|Rest\],AT,AF,NewRest\):-.*?(?=\t\(cpa_debug)",
         "get_real_actions([R|Rest],AT,AF,NewRest):-\n"
         "  invalidated(R,AT,AF),!,\n"),
        ("tautological-executable-branch",
         r"dump_executable\(\[A\|Rest\]\) :-.*?(?=dump_execs\(\[\]\))",
         "dump_executable([A|Rest]) :-\n"
         "  (always_true(AT)->true;AT=[]),\n"
         "  (always_false(AF)->true;AF=[]),\n"
         "  findall((A,N), (cpa_executable(A,C),\n"
         "    \\+ repaired_bad_branch(C,AT,AF),simplify(C,AT,AF,N)), Ready),\n"
         "  (member((A,[]),Ready)->true;dump_execs(Ready)),\n"
         "  dump_executable(Rest).\n\n"),
    ]
    for name, pattern, replacement in branch_edits:
        source, count = re.subn(pattern, lambda _: replacement, source, flags=re.S)
        if count != 1:
            raise ValueError(f"patch {name}: expected 1 block, found {count}")
        changes.append(name)
    return source, changes


def linux_path(path):
    path = str(Path(path).resolve())
    if os.name == "nt":
        return "/mnt/" + path[0].lower() + path[2:].replace("\\", "/")
    return path


def normalize_theory(text):
    # Preserve raw output separately. The native ELF rejects percent headers;
    # this is a transport adapter, not an algorithmic correction.
    return "\n".join(x for x in text.splitlines() if not x.lstrip().startswith("%")) + "\n"


def run(instance, output, runtime=None, executable=None, mode="faithful", options=None, timeout=60):
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("preprocessor output must be a new or empty directory: " + str(output))
    output.mkdir(parents=True, exist_ok=True)
    options = DEFAULT if options is None else options
    if set(options) - OPTIONS:
        raise ValueError("unknown preprocessing option")
    source_path = HERE / "original" / "mult5zsic.pl"
    source = source_path.read_text(encoding="utf-8")
    patches = []
    if mode == "repaired":
        source, patches = repaired_source(source)
    elif mode != "faithful":
        raise ValueError("mode must be faithful or repaired")
    # One source unit preserves the original concatenation's predicate scope.
    program = ((HERE / "swi_compat.pl").read_text() + "\n" + source + "\n" +
               Path(instance).read_text(encoding="utf-8-sig") + "\n")
    (output / "combined.pl").write_text(program, encoding="utf-8", newline="\n")
    goal = "retractall(option(_)),assertz(option([" + ",".join(options) + "])),(main->told,halt(0);told,halt(3))"
    argv = ["-q", "-f", "none", "--on-error=status", "-s", linux_path(output / "combined.pl"), "-g", goal]
    env = os.environ.copy()
    if runtime is None and executable is None:
        candidate = HERE.parent / "runtime" / "linux-x64" / "root"
        if not (candidate / "usr" / "lib" / "swi-prolog" / "boot.prc").is_file():
            from importlib.util import spec_from_file_location, module_from_spec
            spec = spec_from_file_location("preprocessor_bootstrap", HERE / "bootstrap_workspace.py")
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
            candidate = module.bootstrap()
        runtime = candidate
    if runtime:
        runtime = Path(runtime).resolve()
        binary = runtime / "usr" / "bin" / "swipl"
        home = linux_path(runtime / "usr" / "lib" / "swi-prolog")
        libs = linux_path(runtime / "usr" / "lib" / "x86_64-linux-gnu")
        command = ["env", "SWI_HOME_DIR=" + home, "LD_LIBRARY_PATH=" + libs, linux_path(binary)] + argv
    else:
        command = [executable or "swipl"] + argv
    if os.name == "nt":
        command = ["wsl.exe", "--cd", linux_path(output), "-e"] + command
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=output, env=env, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=timeout)
        code, stdout, stderr, timed_out = result.returncode, result.stdout, result.stderr, False
    except subprocess.TimeoutExpired as exc:
        code, stdout, stderr, timed_out = 124, exc.stdout or b"", exc.stderr or b"", True
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
    errors = [x for x in stderr.splitlines() if x.startswith("ERROR:")]
    process_returncode = code
    if errors and code == 0:
        code = 2
    # Keep native generated theory bytes/text; also emit scanner-compatible copy.
    theories = []
    for path in sorted(output.glob("theory_*.al")):
        raw = path.read_text(encoding="utf-8")
        normalized = output / "normalized" / path.name
        normalized.parent.mkdir(exist_ok=True)
        normalized.write_text(normalize_theory(raw), encoding="utf-8", newline="\n")
        theories.append({"name": path.name, "raw_sha256": digest(path), "normalized_sha256": digest(normalized)})
    record = dict(mode=mode, options=options, patches=patches, returncode=code,
                  process_returncode=process_returncode, load_errors=errors,
                  success=code == 0 and not timed_out and not errors and bool(theories), timeout=timed_out,
                  duration_seconds=time.monotonic()-started, stdout=stdout, stderr=stderr,
                  instance_sha256=digest(instance), original_sha256=digest(source_path),
                  theories=theories, command=command,
                  normalized_transform="remove lines whose first non-whitespace character is %; LF newlines",
                  limitation="SWI compatibility execution, not a SICStus runtime oracle")
    (output / "run.json").write_text(json.dumps(record, indent=2), encoding="utf-8", newline="\n")
    return record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("instance", type=Path, help="generated Prolog instance, e.g. original/pddl2pl.pl")
    p.add_argument("-o", "--output", type=Path, required=True)
    p.add_argument("--runtime", type=Path, help="extracted Ubuntu root containing usr/bin/swipl")
    p.add_argument("--swipl", help="SWI executable when using an existing installation")
    p.add_argument("--mode", choices=["faithful", "repaired"], default="faithful")
    p.add_argument("--options", help="comma separated full option list; empty string enables all features")
    p.add_argument("--timeout", type=float, default=60)
    args = p.parse_args()
    try:
        result = run(args.instance, args.output, runtime=args.runtime, executable=args.swipl,
                     mode=args.mode, options=None if args.options is None else [x for x in args.options.split(",") if x],
                     timeout=args.timeout)
    except (ValueError, OSError) as exc:
        p.exit(2, "error: " + str(exc) + "\n")
    print(json.dumps({k: result[k] for k in ("mode", "options", "returncode", "theories", "stderr")}, indent=2))
    raise SystemExit(result["returncode"])


if __name__ == "__main__":
    main()
