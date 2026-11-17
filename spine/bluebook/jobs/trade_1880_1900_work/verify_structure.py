"""Check artifact schemas, source coverage, and exact difference arithmetic."""
import collections,csv,gzip,importlib.util,json,re
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'jobs/trade_1880_1900_work'
spec=importlib.util.spec_from_file_location('reader',WORK/'read_trade.py');reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
def rows(path,expected):
 opener=gzip.open if path.suffix=='.gz' else open
 with opener(path,'rt',encoding='utf-8',newline='') as f:
  r=csv.DictReader(f,delimiter='\t');assert r.fieldnames==expected,(path,r.fieldnames)
  return list(r)
fig=rows(ROOT/'extracted/trade_1880_1900.tsv.gz',reader.FIELDS)
skip=rows(ROOT/'extracted/trade_1880_1900_skipped.tsv',reader.SKIPFIELDS)
checks=rows(ROOT/'extracted/trade_1880_1900_checks.tsv',reader.CHECKFIELDS)
written={(r['table_id'],int(re.match(r'source row (\d+)',r['note'])[1])) for r in fig}
skipped={(r['table_id'],int(r['row_index'])) for r in skip}
assert not written&skipped,'a source row is both emitted and skipped'
assert len(skipped)==len(skip),'duplicate skipped row'
missed=[];inventory=[]
for key in reader.KEYS:
 tables=list(map(json.loads,gzip.open(ROOT/f'tables/{key}.jsonl.gz','rt')))
 ledgers=[t for t in tables if reader.flow_of(t)]
 for t in tables:
  h=' '.join(t['rows'][0]).lower() if t['rows'] else ''
  if ('whence imported' in h or 'to which exported' in h) and not reader.flow_of(t):missed.append(t['id'])
 byid={t['id']:t for t in ledgers}
 for r in skip:
  if r['table_id'] in byid:assert json.loads(r['cells'])==byid[r['table_id']]['rows'][int(r['row_index'])],'skipped cells changed'
 inventory.append({'volume':key,'ledger_tables':len(ledgers),'import_tables':sum(reader.flow_of(t)=='import' for t in ledgers),'export_tables':sum(reader.flow_of(t)=='export' for t in ledgers),'columns':sorted({t['n_cols'] for t in ledgers}),'tables_with_output':len({t for t,i in written if t in byid}),'tables_with_skips':len({t for t,i in skipped if t in byid})})
assert not missed,missed
seen=set();scalar=vector=0
for r in checks:
 key=tuple(r[k] for k in reader.CHECKFIELDS[:7]);assert key not in seen;seen.add(key)
 p,s,d=(r[k] for k in ['printed_total','country_sum','difference'])
 if p.startswith('{'):
  p,s,d=map(json.loads,[p,s,d]);assert set(p)==set(s)==set(d)
  assert all(Fraction(p[u])-Fraction(s[u])==Fraction(d[u]) for u in p);vector+=1
 else:assert Fraction(p)-Fraction(s)==Fraction(d);scalar+=1
summary=list(csv.DictReader(open(WORK/'summary.tsv'),delimiter='\t'))
for r in summary:
 k,flow=r['year_volume'],r['flow']
 tids={t['table_id'] for t in json.load(open(WORK/f'layouts_{k}.json')) if t['flow']==flow}
 assert int(r['figures_written'])==sum(x['year_volume']==k and x['flow']==flow for x in fig)
 assert int(r['rows_skipped'])==sum(x['table_id'] in tids for x in skip)
report={'header_checks':'passed','emitted_source_rows':len(written),'skipped_source_rows':len(skipped),'emitted_skipped_overlap':0,'missed_ledger_headers':missed,'exact_scalar_differences_verified':scalar,'exact_vector_differences_verified':vector,'inventory':inventory}
(WORK/'structure_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='inventory'},indent=2))
if __name__=='__main__':pass
