from __future__ import annotations
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
import pandas as pd



class InputError(ValueError):
    pass



def empty(v: Any):
    return v is None or str(v).strip().lower() in ('', 'nan', 'none', 'nat')



def clean(v: Any) -> str:
    return '' if empty(v) else str(v).strip()



def date_only(v: Any) -> str:
    if empty(v): return ''
    if isinstance(v, (datetime, date, pd.Timestamp)):
        return v.date().isoformat() if isinstance(v, (datetime,pd.Timestamp)) else v.isoformat()
    s=clean(v)
    if re.fullmatch(r'\d+(?:\.0+)?',s):
        
        return (date(1899,12,30)+timedelta(days=int(float(s)))).isoformat()
    try: return pd.to_datetime(s,errors='raise').date().isoformat()
    except Exception as e: raise InputError(f'Nederīgs datums: {v}') from e



def plus_day(s, n):
    return (date.fromisoformat(s)+timedelta(days=n)).isoformat()



def number(v):
    if empty(v): return None
    try:
        n=float(clean(v).replace(',','.'))
        return int(n) if n.is_integer() else n
    except ValueError as e: raise InputError(f'Nederīga skaitliska vērtība: {v}') from e



def curr(v):
    t=clean(v).upper().replace(' ','')
    return {'EURO':'EUR','US DOLLAR':'USD','USDOLLAR':'USD','US$':'USD',
            'POUNDSTERLING':'GBP'}.get(t,t)



def formatted(v):
    if v in (None,'',[],()):return '(nav norādīts)'
    if isinstance(v,(set,list,tuple)):
        return ', '.join(str(x) for x in sorted(v))
    return str(v)



def read_table(path: str|Path, system: str) -> list[dict]:
    path=Path(path)
    if not path.exists(): raise InputError(f'Nav atrasts {system} fails: {path}')
    if path.suffix.lower()=='.xlsx':
        
        df=pd.read_excel(path,header=3 if system=='TMS' else 0,dtype=object,keep_default_na=False)
    elif path.suffix.lower()=='.csv':
        df=pd.read_csv(path,dtype=object,keep_default_na=False,encoding='utf-8-sig')
    else: raise InputError('TMS un MARS failiem jābūt .csv vai .xlsx')
    df.columns=[str(k).strip() for k in df.columns]
    required={'TMS':['Contract Number/Rate Agreement','Service Contract','Valid From Date',
                      'Valid To Date','Port Of Load UN code','Port Of Discharge UN code',
                      'Free Days'],
              'MARS':['Exception_Name','From Date','To Date','Overwrite_free_days']}
    missing=[k for k in required[system] if k not in df.columns]
    if missing: raise InputError(f'{system} failā trūkst kolonnas: {", ".join(missing)}')
    rows=[]
    for row in df.to_dict(orient='records'):
        if all(empty(v) for v in row.values()): continue
        rows.append(row)
    return rows

