import unittest
from pathlib import Path
from datacheck.parser import read_table, parse_tms, parse_mars

ROOT = Path(__file__).resolve().parents[1]


class TestNormalizesana(unittest.TestCase):
    def test_contract_groups(self):
        tms = parse_tms(read_table(ROOT / 'data/TMS.csv', 'TMS'))
        mars = parse_mars(read_table(ROOT / 'data/MARS.csv', 'MARS'))
        self.assertEqual(len(tms), 48)
        self.assertEqual(len(mars), 49)
        self.assertTrue(all('rates' in group for group in tms))


if __name__ == '__main__':
    unittest.main()
