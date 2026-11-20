import csv
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from datacheck.parser import read_table, parse_tms, InputError
from datacheck.links import prefer_tms
from datacheck.engine import analyse


class TestOptionalServiceContract(unittest.TestCase):
    def setUp(self):
        self.rows = read_table(ROOT / 'data/TMS.csv', 'TMS')
        self.contract = self.rows[0]['Contract Number/Rate Agreement']
        self.contract_rows = [deepcopy(r) for r in self.rows
                              if r['Contract Number/Rate Agreement'] == self.contract]

    def test_column_absent(self):
        for row in self.contract_rows:
            row.pop('Service Contract', None)
        parsed = parse_tms(self.contract_rows)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]['service_contract'], '')

    def test_blank_value(self):
        for row in self.contract_rows:
            row['Service Contract'] = ''
        parsed = parse_tms(self.contract_rows)
        self.assertEqual(parsed[0]['service_contract'], '')

    def test_mixed_blank_rows_and_one_value(self):
        for row in self.contract_rows:
            row['Service Contract'] = ''
        self.contract_rows[0]['Service Contract'] = '26-TESTABC'
        parsed = parse_tms(self.contract_rows)
        self.assertEqual(parsed[0]['service_contract'], '26-TESTABC')

    def test_conflicting_nonempty_values_rejected(self):
        for row in self.contract_rows:
            row['Service Contract'] = '26-TESTABC'
        self.contract_rows[-1]['Service Contract'] = '26-TESTXYZ'
        if len(self.contract_rows) == 1:
            self.contract_rows.append(dict(self.contract_rows[0], **{'Service Contract':'26-TESTXYZ'}))
        with self.assertRaises(InputError):
            parse_tms(self.contract_rows)

    def test_no_fallback_link_with_missing_service(self):
        group = {'service_contract':'', 'named':'DE123456', 'direction':'Export'}
        rule = {'service_contract':'', 'named':'DE123456', 'direction':'Export'}
        self.assertFalse(prefer_tms(group,rule))

    def test_reader_accepts_missing_column(self):
        with TemporaryDirectory() as temp:
            p=Path(temp)/'tms.csv'
            fields=[k for k in self.contract_rows[0] if k != 'Service Contract']
            with p.open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=fields)
                w.writeheader()
                for row in self.contract_rows:
                    w.writerow({k:row[k] for k in fields})
            read=read_table(p,'TMS')
            self.assertNotIn('Service Contract',read[0])

    def test_normal_dataset_regression(self):
        result=analyse(ROOT/'data/TMS.csv', ROOT/'data/MARS.csv', ROOT/'data/OVA')
        self.assertEqual(len(result.issues),21)


if __name__ == '__main__':
    unittest.main()
