import argparse
from pathlib import Path

from datacheck.engine import analyse
from datacheck.reports import export


PROJECT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description='ILIM Health Check')
    parser.add_argument('--cli', action='store_true')
    parser.add_argument('--tms', default=str(PROJECT / 'data/TMS.xlsx'))
    parser.add_argument('--mars', default=str(PROJECT / 'data/MARS.xlsx'))
    parser.add_argument('--ova', default=str(PROJECT / 'data/OVA'))
    parser.add_argument('--agency', choices=['US', 'BR', 'ZA'])
    parser.add_argument('--direction', choices=['Import', 'Export'])
    parser.add_argument('--date')
    parser.add_argument('--out', default=str(PROJECT / 'output/parskats.xlsx'))
    args = parser.parse_args()

    if not args.cli:
        from datacheck.gui import start_gui
        start_gui()
        return

    result = analyse(args.tms, args.mars, args.ova,
                     args.agency, args.direction, args.date)
    export(result, args.out)
    print('Pārbaudīti līgumi:', result.totals['TMS līgumi'])
    print('Atrastas neatbilstības:', result.totals['Neatbilstības'])
    print('Pārskats:', args.out)


if __name__ == '__main__':
    main()
