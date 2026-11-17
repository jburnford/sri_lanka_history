import csv,gzip,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'jobs/trade_1880_1900_work'
obs=list(csv.DictReader(gzip.open(ROOT/'extracted/trade_1880_1900.tsv.gz','rt'),delimiter='\t'))
old_path=WORK/'manual_audit_cases.json'
reviewed=json.loads(old_path.read_text()) if old_path.exists() else []
audit=[]
for year in ['1880','1896','1900']:
 tables={t['id']:t for t in map(json.loads,gzip.open(ROOT/f'tables/{year}.jsonl.gz','rt'))}
 for flow in ['import','export']:
  grouped={}
  for r in obs:
   if r['year_volume']==year and r['flow']==flow:
    grouped.setdefault((r['table_id'],int(re.match(r'source row (\d+)',r['note'])[1])),[]).append(r)
  keys=sorted(grouped,key=lambda x:(tables[x[0]]['pdf_page'],x[1]))
  selected=[(c['table_id'],c['source_row']) for c in reviewed if c['volume']==year and c['flow']==flow]
  if not selected:selected=[keys[round(f*(len(keys)-1))] for f in [.04,.25,.50,.75,.96]]
  for tid,i in selected:
   t=tables[tid]
   preceding=[(j,r[:2]) for j,r in enumerate(t['rows'][:i+1]) if r[0] and r[0]!='Articles.']
   audit.append({'volume':year,'flow':flow,'table_id':tid,'source_row':i,'headers':t['rows'][:2],'source_cells':t['rows'][i],'nearby_labels':preceding[-3:],'observations':grouped[(tid,i)]})
(WORK/'manual_audit_cases.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
for n,c in enumerate(audit,1):
 print('\nCASE',n,c['volume'],c['flow'],c['table_id'],'row',c['source_row'])
 print('HEADERS',c['headers'])
 print('LABELS',c['nearby_labels'])
 print('SOURCE',c['source_cells'])
 for r in c['observations']:
  print('OUT',r['article_as_printed'],repr(r['country_group_as_printed']),repr(r['country_as_printed']),r['row_kind'],r['measure'],r['unit_as_printed'],repr(r['value_as_printed']),r['value'],r['note'])
