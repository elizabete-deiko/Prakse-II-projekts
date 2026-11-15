import argparse
from pathlib import Path

from datacheck.engine import analyse
from datacheck.reports import export


BASE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--agency')
    parser.add_argument('--direction')
    parser.add_argument('--date')
    parser.add_argument('--out', default='output/parskats.xlsx')
    args = parser.parse_args()

    result = analyse(BASE / 'data/TMS.xlsx', BASE / 'data/MARS.xlsx',
                     BASE / 'data/OVA', args.agency, args.direction, args.date)
    export(result, BASE / args.out)
    print('Pārbaudīti līgumi:', result.totals['TMS līgumi'])
    print('Atrastas neatbilstības:', result.totals['Neatbilstības'])


if __name__ == '__main__':
    main()
