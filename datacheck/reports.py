import csv
from pathlib import Path

import pandas as pd

from .engine import ISSUE_COLUMNS, STATUS_COLUMNS


def export(result, filename):
    filename = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)

    issues = pd.DataFrame(result.issues, columns=ISSUE_COLUMNS)
    statuses = pd.DataFrame(result.statuses, columns=STATUS_COLUMNS)

    if filename.suffix.lower() == '.xlsx':
        totals = pd.DataFrame([
            {'Rādītājs': key, 'Vērtība': value}
            for key, value in result.totals.items()
        ])
        with pd.ExcelWriter(filename) as writer:
            totals.to_excel(writer, sheet_name='Kopsavilkums', index=False)
            issues.to_excel(writer, sheet_name='Neatbilstibas', index=False)
            statuses.to_excel(writer, sheet_name='Ligumu_statusi', index=False)

    elif filename.suffix.lower() == '.csv':
        issues.to_csv(filename, index=False, encoding='utf-8-sig')
        status_file = filename.with_name(filename.stem + '_statusi.csv')
        statuses.to_csv(status_file, index=False, encoding='utf-8-sig')

    else:
        raise ValueError('Pārskatu var saglabāt tikai XLSX vai CSV formātā')

    return filename
