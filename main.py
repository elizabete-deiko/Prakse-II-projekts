from pathlib import Path
from datacheck.parser import read_table

BASE = Path(__file__).resolve().parent


def main():
    tms = read_table(BASE / 'data/TMS.xlsx', 'TMS')
    mars = read_table(BASE / 'data/MARS.xlsx', 'MARS')
    print(f'TMS rindas: {len(tms)}')
    print(f'MARS rindas: {len(mars)}')


if __name__ == '__main__':
    main()
