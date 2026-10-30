import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pipeline',ROOT/'run_pipeline.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)

class PipelineAssembly(unittest.TestCase):
    def test_original_shared_globals(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            a=folder/'theory_0.al';b=folder/'theory_1.al'
            a.write_text('fluent p;\nfluent q;\naction a;\na causes p;\ninitially -p,-q;\ngoal p;\n')
            b.write_text('action b;\nb causes q;\ngoal q;\n')
            original=b.read_bytes()
            records=pipeline.standalone_theories([a,b],folder)
            text=records[1][0].read_text()
            self.assertEqual(b.read_bytes(),original)
            self.assertEqual(records[0][1],[])
            self.assertEqual(records[1][1],['fluent declarations','initial constraints'])
            self.assertLess(text.index('fluent p'),text.index('action b'))
            self.assertLess(text.index('causes q'),text.index('initially'))
            self.assertLess(text.index('initially'),text.index('goal q'))

    def test_refuses_nonempty_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);(folder/'keep.txt').write_text('keep')
            with self.assertRaisesRegex(ValueError,'must be empty'):
                pipeline.run(ROOT/'original_support/dp.pddl',output=folder)
            self.assertEqual((folder/'keep.txt').read_text(),'keep')

if __name__=='__main__':unittest.main()
