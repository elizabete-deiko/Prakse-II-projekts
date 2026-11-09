import re
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd


class InputError(ValueError):
    pass


def clean(value):
    if value is None:
        return ''
    text = str(value).strip()
    if text.lower() in ('nan', 'none', 'nat'):
        return ''
    return text


def number(value):
    text = clean(value).replace(',', '.')
    if not text:
        return None
    try:
        result = float(text)
    except ValueError:
        raise InputError(f'Nederīgs skaitlis: {value}')
    if result.is_integer():
        return int(result)
    return result


def date_only(value):
    if not clean(value):
        return ''
    if isinstance(value, (date, datetime, pd.Timestamp)):
        return value.strftime('%Y-%m-%d')
    text = clean(value)
    if re.fullmatch(r'\d+(?:\.0+)?', text):
        return (date(1899, 12, 30) + timedelta(days=int(float(text)))).isoformat()
    try:
        return pd.to_datetime(text, errors='raise').date().isoformat()
    except (ValueError, TypeError, OverflowError):
        raise InputError(f'Nederīgs datums: {value}')


def currency(value):
    text = clean(value).upper().replace(' ', '')
    names = {
        'EURO': 'EUR',
        'USDOLLAR': 'USD',
        'US$': 'USD',
        'POUNDSTERLING': 'GBP',
    }
    return names.get(text, text)


def read_table(path, system):
    path = Path(path)
    if not path.exists():
        raise InputError(f'Nav atrasts {system} fails: {path}')

    if path.suffix.lower() == '.csv':
        table = pd.read_csv(path, dtype=object, keep_default_na=False, encoding='utf-8-sig')
    elif path.suffix.lower() == '.xlsx':
        header_row = 3 if system == 'TMS' else 0
        table = pd.read_excel(path, header=header_row, dtype=object, keep_default_na=False)
    else:
        raise InputError('Atbalstīti tikai CSV un XLSX faili')

    table.columns = [str(name).strip() for name in table.columns]
    required = {
        'TMS': [
            'Contract Number/Rate Agreement', 'Valid From Date',
            'Valid To Date', 'Port Of Load UN code',
            'Port Of Discharge UN code', 'Free Days'
        ],
        'MARS': [
            'Exception_Name', 'From Date', 'To Date',
            'Overwrite_free_days'
        ],
    }
    missing = [name for name in required[system] if name not in table.columns]
    if missing:
        raise InputError(f'{system} failā trūkst: {", ".join(missing)}')

    rows = table.to_dict('records')
    return [row for row in rows if any(clean(value) for value in row.values())]


def rates_from_row(row, system):
    rates = {}
    for level in range(1, 7):
        for part in ('days', 'rate'):
            if system == 'TMS':
                column = f'L{level} {part.capitalize()}'
            else:
                column = f'Overwrite_Level_{level}_{part.capitalize()}'
            rates[f'l{level}_{part}'] = number(row.get(column))
    return rates


def agency_and_direction(pols, pods):
    agencies = {'US', 'BR', 'ZA'}
    origins = {port[:2] for port in pols}
    destinations = {port[:2] for port in pods}
    export = origins & agencies
    imported = destinations & agencies

    if len(export) == 1 and not imported:
        return next(iter(export)), 'Export'
    if len(imported) == 1 and not export:
        return next(iter(imported)), 'Import'
    raise InputError(f'Nevar noteikt aģentūru: POL={sorted(origins)}, POD={sorted(destinations)}')


def tms_record(contract_number, rows):
    first = rows[0]
    services = {clean(row.get('Service Contract')) for row in rows}
    services.discard('')
    if len(services) > 1:
        raise InputError(f'Līgumam {contract_number} atšķiras Service Contract vērtības')

    pols = {clean(row.get('Port Of Load UN code')) for row in rows}
    pods = {clean(row.get('Port Of Discharge UN code')) for row in rows}
    equipment = set()
    for row in rows:
        equipment.add((
            int(number(row.get('Equipment Size'))),
            clean(row.get('Equipment Type')).upper(),
            int(number(row.get('Is Oper. Reefer')) or 0),
        ))
    agency, direction = agency_and_direction(pols, pods)

    record = {
        'contract_number': contract_number,
        'service_contract': next(iter(services), ''),
        'valid_from': date_only(first.get('Valid From Date')),
        'valid_to': date_only(first.get('Valid To Date')),
        'free_days': number(first.get('Free Days')),
        'days_type': clean(first.get('Days Type')).upper(),
        'approved_by': clean(first.get('Authorized By')),
        'currency': currency(first.get('Currency')),
        'holder': clean(first.get('Contract Holder MSC Code')),
        'named': clean(first.get('Named Account MSC Code')),
        'pols': pols,
        'pods': pods,
        'equip': equipment,
        'rates': rates_from_row(first, 'TMS'),
        'agency': agency,
        'direction': direction,
        'rows': len(rows),
    }

    for row in rows[1:]:
        for column, expected in (
            ('Valid From Date', record['valid_from']),
            ('Valid To Date', record['valid_to']),
        ):
            if date_only(row.get(column)) != expected:
                raise InputError(f'Līgumam {contract_number} atšķiras {column}')
        checks = {
            'Free Days': number(row.get('Free Days')),
            'Days Type': clean(row.get('Days Type')).upper(),
            'Authorized By': clean(row.get('Authorized By')),
            'Currency': currency(row.get('Currency')),
            'Contract Holder MSC Code': clean(row.get('Contract Holder MSC Code')),
            'Named Account MSC Code': clean(row.get('Named Account MSC Code')),
        }
        original = {
            'Free Days': record['free_days'],
            'Days Type': record['days_type'],
            'Authorized By': record['approved_by'],
            'Currency': record['currency'],
            'Contract Holder MSC Code': record['holder'],
            'Named Account MSC Code': record['named'],
        }
        for column, value in checks.items():
            if value != original[column]:
                raise InputError(f'Līgumam {contract_number} atšķiras {column}')
        if rates_from_row(row, 'TMS') != record['rates']:
            raise InputError(f'Līgumam {contract_number} atšķiras tarifi')

    if record['valid_to'] < record['valid_from']:
        raise InputError(f'Līgumam {contract_number} nav derīgs periods')
    return record


def parse_tms(rows):
    contracts = {}
    for row in rows:
        number_value = clean(row.get('Contract Number/Rate Agreement'))
        if not number_value:
            raise InputError('TMS ierakstam nav līguma numura')
        contracts.setdefault(number_value, []).append(row)

    result = []
    for contract_number, contract_rows in contracts.items():
        result.append(tms_record(contract_number, contract_rows))
    return result


def parse_mars(rows):
    result = []
    for row in rows:
        name = clean(row.get('Exception_Name'))
        if not name:
            raise InputError('MARS ierakstam nav Exception_Name')
        result.append({
            'exception_name': name,
            'valid_from': date_only(row.get('From Date')),
            'valid_to': date_only(row.get('To Date')),
            'free_days': number(row.get('Overwrite_free_days')),
            'days_type': clean(row.get('Overwrite_Days_Type')).upper(),
            'approved_by': clean(row.get('Approved_by')),
            'currency': currency(row.get('Currency')),
            'rates': rates_from_row(row, 'MARS'),
            'sequence': clean(row.get('Sequence')),
            'tariff_row_id': clean(row.get('Tariff_Row_ID')),
        })
    return result
