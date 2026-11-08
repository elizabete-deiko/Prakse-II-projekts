import unittest
from pathlib import Path
from datacheck.parser import read_table

ROOT = Path(__file__).resolve().parents[1]


class TestDatuIelade(unittest.TestCase):
    def test_ielade(self):
        self.assertEqual(len(read_table(ROOT / 'data/TMS.xlsx', 'TMS')), 256)
        self.assertEqual(len(read_table(ROOT / 'data/MARS.xlsx', 'MARS')), 49)


if __name__ == '__main__':
    unittest.main()
