"""Budget provenance and historical framing must survive presentation changes."""
import unittest
from pathlib import Path
import pandas as pd
from streamlit.testing.v1 import AppTest

class BudgetProvenance(unittest.TestCase):
    def test_source_predictions_preserved_in_tables_and_export_data(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertIn("Historical", app.title[0].value)
        app.checkbox[0].check().run()
        source = pd.read_csv("data/performance_data_2023.csv")
        displayed = app.dataframe[-1].value
        self.assertNotIn("Necessary Budget", displayed.columns)
        for column in ["Predicted Total Budget (BUDGET)", "Excess Total Budget", "Excess Budget per Student"]:
            pd.testing.assert_series_equal(displayed[column], source[column])
        exported = pd.read_csv(__import__("io").StringIO(displayed.to_csv(index=False)))
        self.assertNotIn("Necessary Budget", exported.columns)
        self.assertEqual(len(exported), 73)
        app.multiselect(key="manual_school").set_value(["Adams Elementary"]).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.dataframe[-1].value["Total Enrollment"].sum(), 24349)
        self.assertNotIn("Necessary Budget", app.dataframe[0].value.columns)
        self.assertNotIn("Necessary Budget", app.dataframe[1].value.columns)

if __name__ == "__main__": unittest.main()
