import unittest
from pathlib import Path
from datacheck.links import link_ova
from datacheck.parser import read_table, parse_tms, read_ova

ROOT = Path(__file__).resolve().parents[1]


class TestSasaiste(unittest.TestCase):
    def test_link(self):
        tms = parse_tms(read_table(ROOT / 'data/TMS.csv', 'TMS'))
        ova = read_ova(ROOT / 'data/OVA')
        linked = link_ova(tms, ova)
        self.assertEqual(len(linked), 47)
        self.assertTrue(all(k in {v['contract_number'] for v in tms} for k in linked))


if __name__ == '__main__':
    unittest.main()
