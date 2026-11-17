import ast
import csv
from pathlib import Path
import unittest
from allocation_checks import AllocationDataError, validate_destinations, validate_totals
ROOT = Path(__file__).resolve().parents[1]
class AllocationChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT/'data/performance_data_2023.csv').open() as f: cls.data=list(csv.DictReader(f))
        with (ROOT/'data/redistribution_matrix.csv').open() as f: rows=list(csv.reader(f))
        cls.weights=[[float(v) for v in r[1:]] for r in rows[1:]]
        cls.names=[r['School'] for r in cls.data]
        cls.counts=[float(r['Total AAFTE* Enrollment (ENROLLMENT)']) for r in cls.data]
    def test_named_schools_are_blocked(self):
        for name in ('South Shore','Cascade Parent Partnership'):
            with self.subTest(name=name), self.assertRaisesRegex(AllocationDataError,name):
                validate_destinations(self.counts,self.weights,[self.names.index(name)],self.names)
    def test_all_closed_blocked(self):
        with self.assertRaises(AllocationDataError): validate_destinations(self.counts,self.weights,range(73),self.names)
    def test_baseline_passes(self):
        validate_destinations(self.counts,self.weights,[],self.names)
        validate_totals(self.counts,self.counts,self.counts,[])
    def test_no_invented_weight_when_destination_is_also_closed(self):
        with self.assertRaises(AllocationDataError): validate_destinations([2,3,4],[[0,1,0],[0,0,0],[0,0,0]],[0,1],['A','B','C'])
    def test_actual_adams_rounding_loss_blocked(self):
        i=self.names.index('Adams Elementary'); validate_destinations(self.counts,self.weights,[i],self.names)
        after=list(self.counts); row=list(self.weights[i]); row[i]=0; total=sum(row)
        for j,w in enumerate(row):
            if j!=i: after[j]+=self.counts[i]*w/total
        after[i]=0
        displayed=[int(b+int(a-b)) for a,b in zip(after,self.counts)]
        loss=sum(self.counts)-sum(displayed)
        self.assertGreater(loss,0)
        print('Actual Adams single-closure rounding loss:',loss)
        with self.assertRaisesRegex(AllocationDataError,'rounding'): validate_totals(self.counts,after,displayed,[i])
    def test_integral_valid_allocation_passes(self): validate_totals([2,3],[0,5],[0,5],[0])
    def test_lost_students_blocked(self):
        with self.assertRaisesRegex(AllocationDataError,'conserve'): validate_totals([2,3],[0,3],[0,3],[0])
    def test_nonfinite_data_blocked(self):
        with self.assertRaises(AllocationDataError): validate_destinations([2],[[float('nan')]],[],['A'])
    def test_app_stops_before_presenting_results(self):
        source=(ROOT/'app.py').read_text();ast.parse(source)
        self.assertLess(source.index('st.stop()'),source.index("data['Enrollment from Redistribution'] = changes"))
        self.assertIn('validate_totals(before, after, totals, closed_schools)',source)
if __name__=='__main__': unittest.main()
