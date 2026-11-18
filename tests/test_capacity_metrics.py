import unittest
from pathlib import Path
import pandas as pd
from streamlit.testing.v1 import AppTest
from capacity_metrics import capacity_summary, BUCKETS

class CapacityMetrics(unittest.TestCase):
    def check_consistency(self, before, after, cap, closed):
        counts, deltas, transitions = capacity_summary(before, after, cap, closed)
        self.assertEqual(sum(counts.values()), len(before)-len(closed))
        self.assertEqual(sum(deltas.values()), -len(closed))
        for bucket in BUCKETS:
            flags = transitions['delta '+bucket]
            self.assertEqual(sum(flags == 'in')-sum(flags == 'out'), deltas[bucket])
        return counts, deltas, transitions

    def test_exact_boundaries_and_crossings(self):
        before = [74.99,75,75.01,99.99,100,100.01]
        c,d,t=self.check_consistency(before,before,[100]*6,[])
        self.assertEqual(c, {'< 75':1,'75-100':4,'> 100':1})
        self.assertEqual(list(d.values()),[0,0,0])
        c,d,t=self.check_consistency([74.99,100],[75,100.01],[100,100],[])
        self.assertEqual(list(d.values()),[-1,0,1])
        c,d,t=self.check_consistency([75,100.01],[74.99,100],[100,100],[])
        self.assertEqual(list(d.values()),[1,0,-1])

    def test_closures_in_each_bucket_and_zero_open(self):
        c,d,t=self.check_consistency([0,50,75,100,101],[0,0,0,0,0],[100]*5,[1,2,3,4])
        self.assertEqual(c, {'< 75':1,'75-100':0,'> 100':0})
        self.assertEqual(list(d.values()),[-1,-2,-1])
        self.assertEqual(t['delta closed'][0],'')

    def test_all_transitions(self):
        for old in [0,74.99,75,75.01,99.99,100,100.01,150]:
            for new in [0,74.99,75,75.01,99.99,100,100.01,150]:
                for closed in [[],[0]]:
                    self.check_consistency([old],[new],[100],closed)

    def test_app_adams_and_presets(self):
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=30).run()
        baseline=[int(m.value) for m in app.metric[2:]]
        self.assertEqual(baseline,[25,40,8])
        self.assertEqual([m.delta for m in app.metric[2:]],['0','0','0'])
        app.multiselect(key='manual_school').set_value(['Adams Elementary']).run()
        self.assertFalse(app.exception)
        self.assertEqual([m.value for m in app.metric[2:]],['23','40','9'])
        self.assertEqual([m.delta for m in app.metric[2:]],['-2','0','1'])
        app.checkbox[0].check().run()
        frame=app.dataframe[-1].value
        john=frame[frame.School.str.contains('John Stanford')].iloc[0]
        self.assertEqual(john['Total Enrollment'],438)
        self.assertEqual(john['Capacity'],437)
        self.assertEqual(john['delta > 100'],'in')
        for key in ['example_1','example_2','example_4','example_a','example_b']:
            app.button(key=key).click().run()
            self.assertFalse(app.exception)
            self.assertFalse(app.error)
            final=[int(m.value) for m in app.metric[2:]]
            deltas=[int(m.delta) for m in app.metric[2:]]
            self.assertEqual(deltas,[a-b for a,b in zip(final,baseline)])
            self.assertEqual(sum(final),int(app.metric[1].value))
            self.assertEqual(sum(deltas),int(app.metric[1].delta))

if __name__=='__main__': unittest.main()
