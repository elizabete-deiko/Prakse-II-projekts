def prefer_tms(contract, ova_rule):
    if not contract['service_contract'] or not ova_rule['service_contract']:
        return False
    if contract['service_contract'] != ova_rule['service_contract']:
        return False
    if contract['direction'] != ova_rule['direction']:
        return False
    return bool(contract['named'] and contract['named'] == ova_rule['named'])


def link_ova(contracts, ova_rules):
    linked = {}
    for rule in ova_rules:
        matching = None
        for contract in contracts:
            if contract['contract_number'] == rule['contract_number']:
                matching = contract
                break
        if matching is None:
            candidates = []
            for contract in contracts:
                if contract['contract_number'] not in linked and prefer_tms(contract, rule):
                    candidates.append(contract)
            if len(candidates) == 1:
                matching = candidates[0]
        if matching:
            linked[matching['contract_number']] = rule
    return linked


def group_mars(rows):
    groups = {}
    for row in rows:
        groups.setdefault(row['exception_name'], []).append(row)
    return groups
