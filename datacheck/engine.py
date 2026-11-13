from collections import Counter
from dataclasses import dataclass
from datetime import date

from .parser import InputError, parse_mars, parse_tms, read_ova, read_table


FIELD_NAMES = {
    'contract_number': 'Service Contract Number',
    'service_contract': 'Service Contract',
    'valid_from': 'Reference Date: sākums',
    'valid_to': 'Reference Date: beigas',
    'free_days': 'Free Days',
    'days_type': 'Days Type',
    'approved_by': 'Approved by',
    'currency': 'Currency',
    'holder': 'Contract Holder TMS',
    'named': 'Named Account TMS',
    'pols': 'Port Of Load UN code',
    'pods': 'Port Of Discharge UN code',
    'equip': 'Equipment Size/Type',
}

for level in range(1, 7):
    FIELD_NAMES[f'l{level}_days'] = f'Level {level} days'
    FIELD_NAMES[f'l{level}_rate'] = f'Level {level} rate'

ISSUE_COLUMNS = [
    'Prioritāte', 'Aģentūra', 'Virziens', 'Līguma numurs',
    'Service Contract', 'Exception Name', 'Sistēma', 'Parametrs',
    'Sagaidāmā vērtība', 'Faktiskā vērtība', 'Paskaidrojums',
]

STATUS_COLUMNS = [
    'Aģentūra', 'Virziens', 'Līguma numurs', 'Service Contract',
    'Exception Name', 'TMS rindu skaits', 'OVA', 'MARS',
    'Rezultāts', 'Neatbilstību skaits',
]


@dataclass
class AnalysisResult:
    issues: list
    statuses: list
    totals: dict


def display(value):
    if value is None or value == '':
        return '(nav norādīts)'
    if isinstance(value, set):
        parts = []
        for item in sorted(value):
            if isinstance(item, tuple):
                size, kind, reefer = item
                parts.append(f'{size}/{kind}/{"op" if reefer else "ne-op"}')
            else:
                parts.append(str(item))
        return ', '.join(parts) if parts else '(nav norādīts)'
    return str(value)


def add_issue(issues, contract, system, field, expected, actual,
              exception_name='', priority='Augsta', note=''):
    if not note:
        note = f'{system} vērtība atšķiras no sintētiskā TMS līguma nosacījuma.'
    issues.append({
        'Prioritāte': priority,
        'Aģentūra': contract['agency'],
        'Virziens': contract['direction'],
        'Līguma numurs': contract['contract_number'],
        'Service Contract': contract['service_contract'],
        'Exception Name': exception_name or '(nav norādīts)',
        'Sistēma': system,
        'Parametrs': FIELD_NAMES.get(field, field),
        'Sagaidāmā vērtība': display(expected),
        'Faktiskā vērtība': display(actual),
        'Paskaidrojums': note,
    })


def find_contract(ova_rule, tms_contracts, matched):
    for contract in tms_contracts:
        if contract['contract_number'] == ova_rule['contract_number']:
            return contract

    candidates = []
    for contract in tms_contracts:
        if contract['contract_number'] in matched:
            continue
        if not contract['service_contract'] or not ova_rule['service_contract']:
            continue
        if contract['service_contract'] != ova_rule['service_contract']:
            continue
        if contract['named'] and contract['named'] == ova_rule['named']:
            if contract['direction'] == ova_rule['direction']:
                candidates.append(contract)

    if len(candidates) == 1:
        return candidates[0]
    return None


def compare_ova(contract, ova_rule, issues):
    fields = [
        'contract_number', 'service_contract', 'valid_from', 'valid_to',
        'free_days', 'days_type', 'approved_by', 'currency',
        'holder', 'named', 'pols', 'pods', 'equip',
    ]
    for field in fields:
        if field == 'service_contract':
            if not contract[field] or not ova_rule[field]:
                continue
        if contract[field] != ova_rule[field]:
            add_issue(issues, contract, 'OVA', field, contract[field],
                      ova_rule[field], ova_rule['exception_name'])

    for rate_name, expected in contract['rates'].items():
        actual = ova_rule['rates'].get(rate_name)
        if expected != actual:
            add_issue(issues, contract, 'OVA', rate_name, expected,
                      actual, ova_rule['exception_name'])


def compare_mars(contract, ova_rule, mars_rows, issues):
    exception_name = ova_rule['exception_name']
    if not mars_rows:
        add_issue(issues, contract, 'MARS', 'Trūkst izņēmuma',
                  'Eksistē izņēmums', 'Nav izņēmuma', exception_name,
                  note='OVA nosacījumam MARS failā nav atbilstoša Exception_Name ieraksta.')
        return

    first = mars_rows[0]
    fields = ['valid_from', 'valid_to', 'free_days', 'days_type', 'approved_by', 'currency']
    for field in fields:
        if contract[field] != first[field]:
            add_issue(issues, contract, 'MARS', field, contract[field],
                      first[field], exception_name)

    for rate_name, expected in contract['rates'].items():
        actual = first['rates'].get(rate_name)
        if expected != actual:
            add_issue(issues, contract, 'MARS', rate_name, expected, actual, exception_name)



def make_statuses(contracts, matched, mars_by_name, issues):
    issue_counts = Counter(issue['Līguma numurs'] for issue in issues)
    statuses = []
    for contract in contracts:
        number = contract['contract_number']
        ova_rule = matched.get(number)
        exception_name = ova_rule['exception_name'] if ova_rule else ''
        has_mars = bool(mars_by_name.get(exception_name)) if ova_rule else False
        count = issue_counts[number]

        if not ova_rule:
            mars_status = 'Nezināms'
        else:
            mars_status = 'Ir' if has_mars else 'Nav'

        statuses.append({
            'Aģentūra': contract['agency'],
            'Virziens': contract['direction'],
            'Līguma numurs': number,
            'Service Contract': contract['service_contract'],
            'Exception Name': exception_name,
            'TMS rindu skaits': contract['rows'],
            'OVA': 'Ir' if ova_rule else 'Nav',
            'MARS': mars_status,
            'Rezultāts': 'Neatbilst' if count else 'Atbilst',
            'Neatbilstību skaits': count,
        })
    return statuses


def analyse(tms_path, mars_path, ova_path, agency=None, direction=None, as_of=None):
    contracts = parse_tms(read_table(tms_path, 'TMS'))
    mars = parse_mars(read_table(mars_path, 'MARS'))
    ova = read_ova(ova_path)

    if as_of:
        try:
            date.fromisoformat(as_of)
        except ValueError:
            raise InputError('Pārbaudes datumam jābūt GGGG-MM-DD')

    selected = []
    for contract in contracts:
        if agency and contract['agency'] != agency.upper():
            continue
        if direction and contract['direction'] != direction.capitalize():
            continue
        if as_of and not (contract['valid_from'] <= as_of <= contract['valid_to']):
            continue
        selected.append(contract)

    mars_by_name = {}
    for row in mars:
        name = row['exception_name']
        mars_by_name.setdefault(name, []).append(row)

    issues = []
    matched = {}
    for ova_rule in ova:
        contract = find_contract(ova_rule, selected, matched)
        if not contract:
            continue

        number = contract['contract_number']
        matched[number] = ova_rule
        compare_ova(contract, ova_rule, issues)
        related_mars = mars_by_name.get(ova_rule['exception_name'], [])
        compare_mars(contract, ova_rule, related_mars, issues)

    priorities = {'Augsta': 0, 'Vidēja': 1, 'Zema': 2}
    issues.sort(key=lambda row: (
        priorities.get(row['Prioritāte'], 9),
        row['Līguma numurs'], row['Sistēma'], row['Parametrs'],
    ))

    statuses = make_statuses(selected, matched, mars_by_name, issues)
    problem_count = sum(row['Neatbilstību skaits'] > 0 for row in statuses)
    totals = {
        'TMS līgumi': len(selected),
        'TMS datu rindas': sum(contract['rows'] for contract in selected),
        'OVA definīcijas': len(ova),
        'MARS rindas': len(mars),
        'Neatbilstības': len(issues),
        'Līgumi ar problēmām': problem_count,
    }
    return AnalysisResult(issues, statuses, totals)
