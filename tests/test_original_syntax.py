import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('original_syntax',ROOT/'converter/original_syntax.py')
syntax=importlib.util.module_from_spec(spec);spec.loader.exec_module(syntax)

class RecoveredOriginalSyntax(unittest.TestCase):
    def test_original_acceptance_corpus(self):
        report=json.loads((ROOT/'evidence/converter_oracle.json').read_text(encoding='utf-8'))
        for case in report['records']:
            text=(ROOT/'tests/converter_cases'/case['case']/'input.pddl').read_bytes().decode('utf-8')
            accepted=case['returncode']==0 and bool(case.get('output'))
            with self.subTest(case=case['case']):
                if accepted:self.assertTrue(syntax.validate(text))
                else:
                    with self.assertRaises(syntax.OriginalSyntaxError):syntax.validate(text)

    def test_source_tables_identity(self):
        self.assertEqual(syntax.DATA['artifact_sha256'],'87075cfed30f766382627498726423aea875565798f1e416602e9226a85b2163')
        self.assertEqual(len(syntax.T['yyr1'])-1,109)
        self.assertEqual(len(syntax.T['yypact']),239)

if __name__=='__main__':unittest.main()
