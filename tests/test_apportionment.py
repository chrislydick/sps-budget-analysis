import ast
import csv
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from allocation_checks import AllocationDataError, apportion_whole_students, validate_destinations
from streamlit.testing.v1 import AppTest
ROOT = Path(__file__).resolve().parents[1]

class Apportionment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = pd.read_csv(ROOT/'data/performance_data_2023.csv')
        cls.names = cls.data.School.tolist()
        cls.counts = cls.data['Total AAFTE* Enrollment (ENROLLMENT)'].to_numpy()
        cls.weights = pd.read_csv(ROOT/'data/redistribution_matrix.csv', index_col=0)
        tree = ast.parse((ROOT/'app.py').read_text())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'reallocate_student_counts')
        namespace = dict(np=np, AllocationDataError=AllocationDataError)
        exec(compile(ast.Module(body=[function], type_ignores=[]), 'app.py', 'exec'), namespace)
        cls.reallocate = staticmethod(namespace['reallocate_student_counts'])

    def test_all_73_single_closures(self):
        valid = blocked = 0
        for i, name in enumerate(self.names):
            with self.subTest(school=name):
                if name in ('South Shore', 'Cascade Parent Partnership'):
                    with self.assertRaisesRegex(AllocationDataError, name):
                        validate_destinations(self.counts, self.weights.to_numpy(), [i], self.names)
                    blocked += 1
                    continue
                validate_destinations(self.counts, self.weights.to_numpy(), [i], self.names)
                after = self.reallocate(self.counts, self.weights, [i])
                rounded = apportion_whole_students(self.counts, after, [i], self.names)
                self.assertEqual(sum(rounded), 24349)
                self.assertEqual(rounded[i], 0)
                self.assertTrue(all(abs(r-a) < 1 for r,a in zip(rounded,after)))
                self.assertTrue(all(r >= b for j,(r,b) in enumerate(zip(rounded,self.counts)) if j != i))
                self.assertEqual(rounded, apportion_whole_students(self.counts, after, [i], self.names))
                valid += 1
        self.assertEqual((valid,blocked),(71,2))
        print('Single-closure coverage: 71 conserved, 2 unsupported blocked')

    def test_ties_and_no_new_destinations(self):
        self.assertEqual(apportion_whole_students([1,0,0,4],[0,.5,.5,4],[0],['X','B','A','Z']),[0,0,1,4])
        self.assertEqual(apportion_whole_students([1,0,0],[0,.5,.5],[0],['X','A','A']),[0,1,0])
        self.assertEqual(apportion_whole_students([2,3],[2,3],[],['A','B']),[2,3])

    def test_invalid_raw_results_still_blocked(self):
        for after in ([0,4],[0,float('nan')],[1,4],[0,-5]):
            with self.subTest(after=after), self.assertRaises(AllocationDataError):
                apportion_whole_students([2,3],after,[0],['A','B'])

    def test_all_single_closures_and_presets_in_real_app(self):
        app = AppTest.from_file(str(ROOT/'app.py'), default_timeout=30).run()
        for name in self.names:
            with self.subTest(school=name):
                app.multiselect(key='manual_school').set_value([name]).run()
                self.assertFalse(app.exception)
                if name in ('South Shore','Cascade Parent Partnership'):
                    self.assertIn(name, app.error[0].value)
                    self.assertFalse(app.metric)
                else:
                    self.assertFalse(app.error)
                    self.assertEqual(app.metric[1].value,'72')
        for key in ['example_1','example_2','example_3','example_4','example_a','example_b']:
            with self.subTest(preset=key):
                app.button(key=key).click().run()
                self.assertFalse(app.exception)
                if key == 'example_3':
                    self.assertIn('South Shore', app.error[0].value)
                    self.assertFalse(app.metric)
                else:
                    self.assertFalse(app.error)
                    self.assertTrue(app.metric)
                print(key, [e.value for e in app.error], [m.value for m in app.metric][:2])
