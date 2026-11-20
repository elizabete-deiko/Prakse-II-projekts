from __future__ import annotations
import csv,json,re,sys,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
from datacheck.parser import (read_table,parse_tms,parse_mars,read_ova,parse_ova,
                                date_only,InputError)
from datacheck.engine import analyse
from datacheck.reports import export

DATA=BASE/'data'

class TestHealthCheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=analyse(DATA/'TMS.csv',DATA/'MARS.csv',DATA/'OVA')
        cls.canonical=json.loads((DATA/'canonical_training_reference.json').read_text(encoding='utf-8'))
        with (DATA/'intentional_mismatches.csv').open(encoding='utf-8-sig',newline='') as f:
            cls.manifest=list(csv.DictReader(f))

    def test_exact_scenarios_no_false_positive(self):
        target={(s['Sistēma'],s['Līguma numurs'],s['Parametrs']) for s in self.manifest}
        found={(s['Sistēma'],s['Līguma numurs'],s['Parametrs']) for s in self.g.issues}
        self.assertEqual(target,found)
        self.assertEqual(len(self.g.issues),21)

    def test_xlsx_matches_csv(self):
        x=analyse(DATA/'TMS.xlsx',DATA/'MARS.xlsx',DATA/'OVA')
        self.assertEqual(x.issues,self.g.issues)
        self.assertEqual(x.statuses,self.g.statuses)

    def test_combined_ova_txt_matches_folder(self):
        x=analyse(DATA/'TMS.csv',DATA/'MARS.csv',DATA/'OVA.txt')
        self.assertEqual(x.issues,self.g.issues)

    def test_original_like_tms_schema(self):
        t=read_table(DATA/'TMS.xlsx','TMS')
        self.assertGreater(len(t),250)
        self.assertIn('Contract Number/Rate Agreement',t[0])
        self.assertIn('L6 Rate',t[0])
        self.assertIn('Last Reviewed Name by MSC SSCR',t[0])

    def test_original_like_mars_schema(self):
        m=read_table(DATA/'MARS.xlsx','MARS')
        self.assertEqual(len(m),49)
        self.assertIn('Exception_Name',m[0])
        self.assertIn('Overwrite_Level_4_Rate',m[0])
        self.assertIn('Overwrite_Level_6_Rate',m[0])

    def test_48_rules_and_47_ova(self):
        self.assertEqual(len(parse_tms(read_table(DATA/'TMS.csv','TMS'))),48)
        self.assertEqual(len(read_ova(DATA/'OVA')),47)

    def test_empty_rates_have_empty_currency_everywhere(self):
        empty_rules=[r for r in self.canonical if not r['rates']]
        self.assertGreaterEqual(len(empty_rules),2)
        self.assertTrue(all(r['currency']=='' for r in empty_rules))
        t={r['contract_number']:r for r in parse_tms(read_table(DATA/'TMS.csv','TMS'))}
        for r in empty_rules:
            self.assertEqual(t[r['contract_number']]['currency'],'')
            self.assertTrue(all(v is None for v in t[r['contract_number']]['rates'].values()))
        o={r['contract_number']:r for r in read_ova(DATA/'OVA')}
        for r in empty_rules:
            if r['contract_number'] in o:
                self.assertEqual(o[r['contract_number']]['currency'],'')

    def test_partial_rate_pattern_exact(self):
        r=self.canonical[5]
        self.assertEqual(sorted(r['rates']),['l1_days','l1_rate','l2_rate'])
        o={x['contract_number']:x for x in read_ova(DATA/'OVA')}
        self.assertIsNone(o[r['contract_number']]['rates']['l2_days'])
        self.assertIsNone(o[r['contract_number']]['rates']['l3_rate'])
        self.assertIsNotNone(o[r['contract_number']]['rates']['l2_rate'])

    def test_rates_no_higher_than_four(self):
        self.assertTrue(all(int(k[1])<=4 for r in self.canonical for k in r['rates']))
        self.assertTrue(any('l4_rate' in r['rates'] for r in self.canonical))
        self.assertTrue(any(not r['rates'] for r in self.canonical))

    def test_real_port_code_pattern(self):
        valid={'USBAL','USBOS','USCHS','USHOU','USJAX','USLAX','USLGB','USMOB',
               'USMSY','USNYC','USOAK','USORF','USPHL','USSAV','USSEA',
               'BRSSZ','BRRIO','BRPNG','ZADUR','ZAPLZ','ZAZBA','BEANR','DEHAM',
               'DEBRV','NLRTM','FRLEH','ITGOA','ITBRI','PLGDN'}
        for r in self.canonical:
            self.assertTrue(set(r['pols']+r['pods']).issubset(valid))
            self.assertTrue(all(re.fullmatch('[A-Z]{2}[A-Z0-9]{3}',p) for p in r['pols']+r['pods']))

    def test_mars_currency_label_normalized(self):
        m=parse_mars(read_table(DATA/'MARS.csv','MARS'))
        self.assertTrue(all(item['currency'] in ('','EUR','USD') for item in m))

    def test_ova_half_open_end_date(self):
        r=self.canonical[0]
        o={x['contract_number']:x for x in read_ova(DATA/'OVA')}
        self.assertEqual(o[r['contract_number']]['valid_to'],r['valid_to'])

    def test_wasted_run_ignored_as_auxiliary(self):
        files=list((DATA/'OVA').glob('*-DCE.txt'))
        self.assertGreater(len(files),0)
        for p in files:
            self.assertIn('Wasted_Run-01',p.read_text(encoding='utf-8'))
            self.assertFalse(any(r['exception_name']=='Wasted_Run-01' for r in read_ova(p)))

    def test_agency_filter(self):
        x=analyse(DATA/'TMS.csv',DATA/'MARS.csv',DATA/'OVA',agency='BR')
        self.assertEqual(len(x.statuses),16)
        self.assertTrue(all(r['Aģentūra']=='BR' for r in x.issues))

    def test_direction_filter(self):
        x=analyse(DATA/'TMS.csv',DATA/'MARS.csv',DATA/'OVA',direction='Export')
        self.assertEqual(len(x.statuses),24)
        self.assertTrue(all(r['Virziens']=='Export' for r in x.issues))

    def test_expiry_filter(self):
        x=analyse(DATA/'TMS.csv',DATA/'MARS.csv',DATA/'OVA',as_of='2032-01-01')
        self.assertEqual(x.totals['TMS līgumi'],0)
        self.assertEqual(len(x.issues),0)

    def test_missing_ova_and_mars_separately(self):
        self.assertEqual(sum(x['Parametrs']=='Trūkst SQL nosacījuma' for x in self.g.issues),1)
        self.assertEqual(sum(x['Parametrs']=='Trūkst izņēmuma' for x in self.g.issues),1)

    def test_duplicate_and_overlap_distinct(self):
        kinds=[x['Parametrs'] for x in self.g.issues]
        self.assertEqual(kinds.count('Dublēts izņēmums'),1)
        self.assertEqual(kinds.count('Pārklājoši derīguma periodi'),1)

    def test_export_csv(self):
        with TemporaryDirectory() as d:
            target=Path(d)/'health.csv'
            export(self.g,target)
            self.assertTrue(target.exists())
            self.assertTrue((Path(d)/'health_statusi.csv').exists())

    def test_export_excel(self):
        with TemporaryDirectory() as d:
            target=Path(d)/'health.xlsx'
            export(self.g,target)
            self.assertTrue(target.exists())
            df=read_table(DATA/'TMS.xlsx','TMS')
            self.assertTrue(df)

    def test_invalid_extension_rejected(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'input.txt';p.write_text('x',encoding='utf-8')
            with self.assertRaises(InputError):read_table(p,'TMS')

    def test_invalid_date_rejected(self):
        with self.assertRaises(InputError):date_only('not-a-date')

    def test_patching_ova_scenario_detectable(self):
        data=(DATA/'OVA.txt').read_text(encoding='utf-8')
        o=parse_ova(data)
        self.assertTrue(any(x['free_days']==15 for x in o))

if __name__=='__main__':unittest.main()
