import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from datacheck.engine import analyse
from datacheck.reports import export

ROOT = Path(__file__).resolve().parents[1]


class TestEksports(unittest.TestCase):
    def test_csv_and_xlsx(self):
        result = analyse(ROOT / 'data/TMS.csv', ROOT / 'data/MARS.csv', ROOT / 'data/OVA')
        with TemporaryDirectory() as temporary:
            for suffix in ('csv', 'xlsx'):
                path = Path(temporary) / f'parskats.{suffix}'
                export(result, path)
                self.assertTrue(path.exists())


if __name__ == '__main__':
    unittest.main()
