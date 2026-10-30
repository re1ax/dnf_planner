"""Byte-level regression against independently captured original ELF output."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from converter.pddl2pl import convert, convert_with_diagnostics


class ConverterOracleTests(unittest.TestCase):
    def test_original_elf_corpus(self):
        evidence = json.loads((ROOT / 'evidence/converter_oracle.json').read_text(encoding='utf8'))
        for record in evidence['records']:
            case = ROOT / 'tests/converter_cases' / record['case']
            with self.subTest(case=record['case']):
                source = (case / 'input.pddl').read_bytes().decode('utf8')
                if record['returncode'] == 0:
                    expected = (case / 'output.pl').read_bytes()
                    result, diagnostics = convert_with_diagnostics(source)
                    self.assertEqual(result.encode('utf8'), expected)
                    self.assertEqual(''.join(diagnostics) +
                                     'Converting pddl to pl\nOutput file: pddl2pl.pl\n\n\n',
                                     record['stdout'])
                else:
                    with self.assertRaises(ValueError):
                        convert(source)

    def test_cli_writes_lf_and_respects_output_path(self):
        source = ROOT / 'tests/converter_cases/basic/input.pddl'
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'chosen.pl'
            result = subprocess.run([sys.executable, str(ROOT / 'converter/pddl2pl.py'),
                                     str(source), '-o', str(output)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_bytes(),
                             (ROOT / 'tests/converter_cases/basic/output.pl').read_bytes())
            self.assertNotIn(b'\r', output.read_bytes())


if __name__ == '__main__':
    unittest.main()
