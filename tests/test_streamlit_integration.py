"""Execute the real app and ensure invalid results never reach metrics."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

class StreamlitIntegration(unittest.TestCase):
    def test_guarded_selection_and_recovery(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[1].value, '73')
        for school, message in [('South Shore', 'South Shore'), ('Cascade Parent Partnership', 'Cascade Parent Partnership'), ('Adams Elementary', 'rounding')]:
            with self.subTest(school=school):
                app.multiselect(key='manual_school').set_value([school]).run()
                self.assertFalse(app.exception)
                self.assertEqual(len(app.error), 1)
                self.assertIn(message, app.error[0].value)
                self.assertEqual(len(app.metric), 0)
                self.assertEqual(len(app.dataframe), 0)
                app.multiselect(key='manual_school').set_value([]).run()
                self.assertFalse(app.exception)
                self.assertEqual(len(app.error), 0)
                self.assertEqual(app.metric[1].value, '73')

if __name__ == '__main__': unittest.main()
