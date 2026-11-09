from pathlib import Path
from datacheck.parser import read_table, parse_tms, parse_mars

BASE = Path(__file__).resolve().parent


def main():
    tms = parse_tms(read_table(BASE / 'data/TMS.xlsx', 'TMS'))
    mars = parse_mars(read_table(BASE / 'data/MARS.xlsx', 'MARS'))
    print(f'TMS līgumi: {len(tms)}')
    print(f'MARS izņēmumi: {len(mars)}')
    for group in tms[:3]:
        print(group['contract_number'], group['agency'], group['direction'])


if __name__ == '__main__':
    main()
