import unittest
from pathlib import Path
from datacheck.parser import read_ova

ROOT = Path(__file__).resolve().parents[1]


class TestOVA(unittest.TestCase):
    def test_sql_parser(self):
        rules = read_ova(ROOT / 'data/OVA')
        self.assertEqual(len(rules), 47)
        self.assertTrue(any(not any(v is not None for v in r['rates'].values()) for r in rules))
        self.assertTrue(all('Wasted_Run' not in r['exception_name'] for r in rules))


if __name__ == '__main__':
    unittest.main()
