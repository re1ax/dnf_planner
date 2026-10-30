"""Default integration and explicit option coverage for the original Prolog."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pp_runner", ROOT / "preprocessor" / "run_preprocessor.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class PreprocessorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = ROOT / "runs" / "preprocessor-tests"
        cls.scratch.mkdir(parents=True, exist_ok=True)
        cls.temporary = tempfile.TemporaryDirectory(dir=cls.scratch)
        cls.temp = Path(cls.temporary.name)
        cls.instance = ROOT / "preprocessor" / "original" / "pddl2pl.pl"
        cls.records = []

    @classmethod
    def tearDownClass(cls):
        evidence = ROOT / "preprocessor" / "evidence"
        evidence.mkdir(exist_ok=True)
        (evidence / "option-matrix.json").write_text(json.dumps(cls.records, indent=2), encoding="utf-8")
        cls.temporary.cleanup()

    def run_case(self, name, mode="faithful", options=None):
        result = runner.run(self.instance, self.temp / name, mode=mode, options=options, timeout=15)
        self.records.append(dict(case=name, **result))
        return result

    def run_fixture(self, fixture, name, mode="faithful", options=None):
        path = self.temp / name
        result = runner.run(ROOT / "tests" / "preprocessor_fixtures" / (fixture + ".pl"),
                            path, mode=mode, options=options, timeout=15)
        texts = {p.name: p.read_text() for p in (path / "normalized").glob("*.al")}
        self.records.append(dict(case=name, theory_texts=texts, **result))
        return result, texts

    def test_original_identity_and_normalization(self):
        self.assertEqual(runner.digest(ROOT / "preprocessor" / "original" / "mult5zsic.pl"),
                         "a572b99ceb9aa842edf2de35f733f5a643fe78f630b76afb23dd419da64c3fb8")
        self.assertEqual(runner.normalize_theory("%% header\r\nfluent p;\r\n  % x\r\n"), "fluent p;\n")

    def test_refuses_stale_output_and_load_errors(self):
        stale = self.temp / "stale"
        stale.mkdir()
        old = stale / "theory_0.al"
        old.write_text("user data")
        with self.assertRaises(FileExistsError):
            runner.run(self.instance, stale)
        self.assertEqual(old.read_text(), "user data")
        broken = self.temp / "broken.pl"
        broken.write_text(self.instance.read_text() + "\nthis is malformed syntax.\n")
        result = runner.run(broken, self.temp / "load-error", timeout=15)
        self.records.append(dict(case="load-error", **result))
        self.assertNotEqual(result["returncode"], 0)
        self.assertTrue(result["load_errors"])
        self.assertFalse(result["success"])

    def test_default_faithful_repaired(self):
        a = self.run_case("default-faithful")
        b = self.run_case("default-repaired", "repaired")
        self.assertEqual(a["returncode"], 0, a["stderr"])
        self.assertEqual(b["returncode"], 0, b["stderr"])
        self.assertEqual(a["theories"], b["theories"])
        self.assertIn("Original Number of States: 243", a["stdout"])
        self.assertIn("Time _", a["stdout"])
        self.assertNotIn("Time _", b["stdout"])
        self.assertEqual(a["patches"], [])
        self.assertEqual(len(b["patches"]), 16)

    def test_all_optional_switches(self):
        cases = {
            "noforward": ["no_duals", "no_goal_split", "noforward"],
            "noanalyze": ["no_duals", "no_goal_split", "noanalyze"],
            "no_oneof": ["no_duals", "no_goal_split", "no_oneof"],
            "goal_split": ["no_duals"],
            "duals": ["no_goal_split"],
            "all_features": [],
        }
        for mode in ("faithful", "repaired"):
            for name, options in cases.items():
                with self.subTest(mode=mode, name=name):
                    result = self.run_case(mode + "-" + name, mode, options)
                    if mode == "faithful" and name in ("duals", "all_features"):
                        self.assertNotEqual(result["returncode"], 0)
                        self.assertIn("check_init_dualsRest/2", result["stderr"])
                    else:
                        self.assertEqual(result["returncode"], 0, result["stderr"])
                        self.assertTrue(result["theories"])

    def test_optimization_examples_and_original_defects(self):
        a, ta = self.run_fixture("forward_constants", "forward-default")
        b, tb = self.run_fixture("forward_constants", "forward-off", options=runner.DEFAULT + ["noforward"])
        c, tc = self.run_fixture("forward_constants", "constant-analysis-off", options=runner.DEFAULT + ["noanalyze"])
        self.assertNotIn("action dead;", ta["theory_0.al"])
        self.assertIn("action dead;", tb["theory_0.al"])
        self.assertIn("good causes  p;", ta["theory_0.al"])
        self.assertIn(" if ", tc["theory_0.al"])
        d, td = self.run_fixture("independent_oneof", "oneof-default")
        e, te = self.run_fixture("independent_oneof", "oneof-off", options=runner.DEFAULT + ["no_oneof"])
        self.assertIn("Original Number of States: 4", d["stdout"])
        self.assertIn("Final Number of States:    2", d["stdout"])
        self.assertNotEqual(td, te)
        g, tg = self.run_fixture("goal_split", "goals-split", options=["no_duals"])
        self.assertEqual(len(tg), 2)
        self.assertIn("action a;", tg["theory_0.al"])
        self.assertNotIn("action c;", tg["theory_0.al"] + tg["theory_1.al"])
        # This faithfully records the original multi-theory continuation format.
        self.assertNotIn("fluent ", tg["theory_1.al"])
        f, _ = self.run_fixture("duals", "duals-original", options=["no_goal_split"])
        r, tr = self.run_fixture("duals", "duals-fixed", "repaired", ["no_goal_split"])
        self.assertNotEqual(f["returncode"], 0)
        self.assertEqual(r["returncode"], 0, r["stderr"])
        self.assertNotIn("fluent p;", tr["theory_0.al"])
        self.assertIn("goal  -q;", tr["theory_0.al"])
        for fixture in ("atomic_effect", "constant_goal", "disjunctive_precondition"):
            original, to = self.run_fixture(fixture, fixture + "-original")
            fixed, tf = self.run_fixture(fixture, fixture + "-fixed", "repaired")
            self.assertEqual(fixed["returncode"], 0, fixed["stderr"])
            self.assertIn("fluent p;", tf["theory_0.al"])
            self.assertIn("initially ", tf["theory_0.al"])
            self.assertIn("action a;", tf["theory_0.al"])
            if fixture == "disjunctive_precondition":
                self.assertNotIn("action a;", to["theory_0.al"])
                self.assertNotIn("executable ", tf["theory_0.al"])
            else:
                self.assertNotIn("fluent p;", to["theory_0.al"])


if __name__ == "__main__":
    unittest.main()
