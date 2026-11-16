#!/home/jic823/miniforge3/bin/python
"""Independent provenance and arithmetic validation of the generated extract."""
import csv
import gzip
import hashlib
import json
import re
from collections import Counter
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'jobs/agriculture_work'
FIELDS='table_id year_volume year_data pdf_page printed_page table_kind area_level area_as_printed parent_area_as_printed measure_as_printed unit_as_printed value_as_printed value note'.split()

def read_tsv(p):
    with p.open(newline='') as f:return list(csv.DictReader(f,delimiter='\t'))


def trim(s):return re.sub(r'(?:\s*\.\s*){2,}$','',s.strip()).rstrip()


def independently_read_number(s):
    s=re.sub(r'\\(?:dagger|ddagger|ast)\b|[*†‡§]+','',s).strip().replace(',','')
    frac={'¼':Fraction(1,4),'½':Fraction(1,2),'¾':Fraction(3,4),'⅛':Fraction(1,8),'⅜':Fraction(3,8),'⅝':Fraction(5,8),'⅞':Fraction(7,8)}
    if s and s[-1] in frac:
        return Fraction(s[:-1] or '0')+frac[s[-1]]
    m=re.fullmatch(r'(\d*)\\frac\{(\d+)\}\{(\d+)\}',s)
    if m:return Fraction(int(m[1] or 0))+Fraction(int(m[2]),int(m[3]))
    m=re.fullmatch(r'(\d+)\s+(\d+)/(\d+)',s)
    if m:return Fraction(int(m[1]))+Fraction(int(m[2]),int(m[3]))
    return Fraction(s)

sources={}
for path in sorted((ROOT/'tables').glob('*.jsonl.gz')):
    with gzip.open(path,'rt') as f:
        for l in f:
            t=json.loads(l);sources[t['id']]=t
volume_labels={}
for t in sources.values():
    volume_labels.setdefault(t['year'],set()).update(trim(c) for r in t['rows'] for c in r)
path=ROOT/'extracted/agriculture.tsv'
with path.open(newline='') as f:
    rd=csv.DictReader(f,delimiter='\t');assert rd.fieldnames==FIELDS
    rows=list(rd)
coords=read_tsv(WORK/'source_cells.tsv')
assert len(rows)==len(coords)
seen=set();numeric=0
for row,prov in zip(rows,coords):
    tid=row['table_id'];t=sources[tid]
    assert row['year_volume']==str(t['year'])
    assert row['pdf_page']==str(t['pdf_page'])
    assert row['printed_page']==(t.get('printed_page') or '')
    assert row['table_kind'] in {'acreage_by_crop','land_produce_stock','live_stock'}
    assert row['area_level'] in {'province','district','colony_total','other'}
    assert row['year_data']=='' or re.fullmatch(r'(18|19)\d\d',row['year_data'])
    assert row['year_data'] or 'year_data' in row['note']
    ri,ci=int(prov['source_row']),int(prov['source_column'])
    key=tid,ri,ci
    assert key not in seen, ('duplicate printed cell',key)
    seen.add(key)
    assert tid==prov['table_id']
    source=t['rows'][ri][ci]
    assert source==prov['source_cell']
    assert row['value_as_printed']==prov['value_as_printed']
    assert row['unit_as_printed']==prov['unit_as_printed']
    assert f'source row {ri}, column {ci}' in row['note']
    assert row['value_as_printed'] in source or row['value_as_printed']==source.strip()
    printed=[c for r in t['rows'] for c in r]+t['headings']
    cleaned={trim(c) for c in printed}
    for field in ['area_as_printed','parent_area_as_printed','measure_as_printed']:
        allowed=volume_labels[t['year']] if field=='parent_area_as_printed' else cleaned
        assert not row[field] or row[field] in allowed, (key,field,row[field])
    assert not row['unit_as_printed'] or any(row['unit_as_printed'] in c for c in printed), (key,row['unit_as_printed'])
    assert not re.search(r'\.{2,}\s*$',row['area_as_printed'])
    if row['value']:
        assert re.fullmatch(r'[+-]?\d+(?:\.\d+)?',row['value'])
        assert independently_read_number(row['value_as_printed'])==Fraction(row['value']), (key,row)
        numeric+=1
    elif not re.fullmatch(r'[\s.\-—–−]*|Nil',row['value_as_printed'],re.I):
        assert any(n in row['note'] for n in ['unreadable','nonnumeric']), (key,row)
    if row['area_level']=='district':assert row['parent_area_as_printed'],key
    assert not (ci==0),key

# Candidate completeness and exclusions.
inventory=read_tsv(WORK/'candidate_inventory.tsv')
skipped=read_tsv(ROOT/'extracted/agriculture_skipped.tsv')
used_ids={r['table_id'] for r in rows};skipped_ids={r['table_id'] for r in skipped}
assert not used_ids & skipped_ids
assert {r['table_id'] for r in inventory}==used_ids|skipped_ids
assert all(r['reason'] for r in skipped)
counts=Counter(r['table_id'] for r in rows)
for c in inventory:assert int(c['row_count'])==counts[c['table_id']]

# Independently verify opening crop sums directly from source cells, in both
# directions where a TOTAL column exists. Do not reuse extractor functions.
audit=read_tsv(WORK/'totals_audit.tsv')
lookup={(r['table_id'],r['area_or_measure']):r for r in audit}
for tid in sorted(used_ids):
    t=sources[tid]
    if not any(r['table_id']==tid and r['table_kind']=='acreage_by_crop' for r in rows):continue
    if t['year']>=1920:continue
    data=t['rows'][2:];last=len(t['rows'])-1
    for ci in range(1,len(t['rows'][0])):
        a=lookup[tid,'measure: '+trim(t['rows'][0][ci])]
        if a['computed_sum']:
            parts=[]
            for ri in range(2,last):
                val=t['rows'][ri][ci]
                if re.fullmatch(r'[\s.\-—–−]*|Nil',val,re.I):continue
                parts.append(independently_read_number(val))
            assert sum(parts,Fraction())==Fraction(a['computed_sum'])
            assert independently_read_number(t['rows'][last][ci])-sum(parts,Fraction())==Fraction(a['difference'])

for a in audit+read_tsv(WORK/'other_totals_audit.tsv'):
    if a['computed_sum']:
        assert independently_read_number(a['printed_total'])-Fraction(a['computed_sum'])==Fraction(a['difference'])
        assert (a['status']=='agree')==(Fraction(a['difference'])==0)
    else:assert a['status'].startswith('uncheckable')
checks=read_tsv(ROOT/'extracted/agriculture_checks.tsv')
expected=[{k:a[k] for k in ['table_id','area_or_measure','printed_total','computed_sum','difference']} for a in audit if a['status']!='agree']
assert checks==expected

report={'rows':len(rows),'numeric_values_verified':numeric,'tables_used':len(used_ids),'tables_skipped':len(skipped_ids),'unique_source_cells_verified':len(seen),'acreage_total_statuses':dict(Counter(a['status'] for a in audit)),'result':'PASS'}
(WORK/'validation_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
