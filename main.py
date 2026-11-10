from pathlib import Path
from datacheck.parser import read_table, parse_tms, parse_mars, read_ova

BASE = Path(__file__).resolve().parent


def main():
    tms = parse_tms(read_table(BASE / 'data/TMS.xlsx', 'TMS'))
    mars = parse_mars(read_table(BASE / 'data/MARS.xlsx', 'MARS'))
    ova = read_ova(BASE / 'data/OVA')
    print(f'TMS līgumi: {len(tms)}')
    print(f'OVA SQL noteikumi: {len(ova)}')
    print(f'MARS izņēmumi: {len(mars)}')


if __name__ == '__main__':
    main()
