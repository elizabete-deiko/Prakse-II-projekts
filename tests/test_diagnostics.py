import unittest
from pathlib import Path
from datacheck.engine import analyse

ROOT = Path(__file__).resolve().parents[1]


class TestDiagnostika(unittest.TestCase):
    def test_all_findings(self):
        result = analyse(ROOT / 'data/TMS.csv', ROOT / 'data/MARS.csv', ROOT / 'data/OVA')
        self.assertEqual(len(result.issues), 21)
        self.assertEqual(len(result.statuses), 48)
        self.assertTrue(any(x['Parametrs'] == 'Trūkst izņēmuma' for x in result.issues))
        self.assertTrue(any(x['Parametrs'] == 'Trūkst SQL nosacījuma' for x in result.issues))


if __name__ == '__main__':
    unittest.main()
