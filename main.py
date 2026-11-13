from pathlib import Path
from datacheck.engine import analyse

BASE = Path(__file__).resolve().parent


def main():
    result = analyse(BASE / 'data/TMS.xlsx', BASE / 'data/MARS.xlsx', BASE / 'data/OVA')
    print(f"Pārbaudīti līgumi: {result.totals['TMS līgumi']}")
    print(f"Parametru nesakritības: {len(result.issues)}")
    for finding in result.issues[:5]:
        print(finding['Līguma numurs'], finding['Sistēma'], finding['Parametrs'])


if __name__ == '__main__':
    main()
