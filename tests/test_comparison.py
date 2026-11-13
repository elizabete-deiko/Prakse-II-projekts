import unittest
from pathlib import Path
from datacheck.engine import analyse

ROOT = Path(__file__).resolve().parents[1]


class TestSalidzinasana(unittest.TestCase):
    def test_parameters(self):
        result = analyse(ROOT / 'data/TMS.csv', ROOT / 'data/MARS.csv', ROOT / 'data/OVA')
        self.assertTrue(any(x['Parametrs'] == 'Free Days' for x in result.issues))
        self.assertTrue(any(x['Sistēma'] == 'OVA' for x in result.issues))
        self.assertTrue(any(x['Sistēma'] == 'MARS' for x in result.issues))


if __name__ == '__main__':
    unittest.main()
