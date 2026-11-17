#!/home/jic823/miniforge3/bin/python
"""Read-only cross-file and source validation; only validation.json is written."""
import csv,gzip,json,re,collections,pathlib,decimal
ROOT=pathlib.Path(__file__).resolve().parents[2];WORK=ROOT/'jobs/statistical_view_work';OUT=ROOT/'extracted'
def tab(p,gz=False):
 with (gzip.open if gz else open)(p,'rt',encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
obs=tab(OUT/'statistical_view.tsv.gz',True);comp=tab(OUT/'statistical_view_compare.tsv');skips=tab(OUT/'statistical_view_skipped.tsv')
source={}
for p in sorted((ROOT/'tables').glob('*.jsonl.gz')):
 with gzip.open(p,'rt') as f:
  for line in f:
   t=json.loads(line);source[t['id']]=t
assert list(dict.fromkeys(x['year_volume'] for x in obs))[:3]==['1896','1871','1911']
seen=set();groups=collections.defaultdict(lambda:collections.defaultdict(set));money_triples=0;D=decimal.Decimal
for x in obs:
 t=source[x['table_id']];m=re.match(r'source row (\d+), column (\d+)',x['note']);assert m
 i,j=int(m[1])-1,int(m[2])-1
 assert (t['id'],i,j) not in seen;seen.add((t['id'],i,j))
 assert t['rows'][i][j]==x['value_as_printed']
 assert x['pdf_page']==str(t['pdf_page'])
 assert int(x['data_year'][:4])<=int(x['year_volume'][:4])+1
 if int(x['year_volume'][:4])<1924:
  h=' / '.join(r[j] for r in t['rows'][:t['header_rows']] if r[j] and not re.fullmatch(r'(?:18|19)\d\d(?:[-–]\d{2,4})?',r[j].strip()))
  assert h==x['column_as_printed']
 if x['value']:
  v=D(x['value']);raw=x['value_as_printed'].strip()
  if re.search(r'\d+s\.',raw):
   q=re.fullmatch(r'£?\s*([\d,]+)\.?\s+(\d+)s\.(?:\s*(\d+)d\.)?',raw);assert q
   expected=D(q[1].replace(',',''))+D(q[2])/20+D(q[3] or '0')/240
   assert abs(v-expected)<=D('0.0000000000005');money_triples+=1
  else:
   raw=re.sub(r'^(?:£|Rs\.?)\s*','',raw)
   assert v==D(raw.replace(',',''))
 groups[x['series'],x['data_year']][('number',x['value']) if x['value'] else ('literal',x['value_as_printed'])].add(x['year_volume'])
assert len(comp)==len(groups)
for x in comp:
 vals=json.loads(x['distinct_values_with_volumes_json']);vs=groups[x['series'],x['data_year']]
 assert {(v['kind'],v['value']):set(v['volumes']) for v in vals}==dict(vs)
 assert len(set().union(*vs.values()))==int(x['number_of_volumes'])
 sizes=[len(v['volumes']) for v in vals];assert sizes==sorted(sizes,reverse=True)
 if len(vs)==1:status='all agree'
 elif len(vs)==2 and min(sizes)==1 and max(sizes)>=2:status='one volume differs'
 elif len(vs)==2:status='two values'
 else:status='many values'
 assert x['status']==status
mp=tab(WORK/'series_map.tsv');assert {x['series'] for x in mp}=={x['series'] for x in obs}
for x in mp:
 assert set(json.loads(x['distinct_printed_headers_json']))=={o['column_as_printed'] for o in obs if o['series']==x['series']}
vcheck=tab(WORK/'volume_checks.tsv');assert len(vcheck)==63
for x in vcheck:
 oo=[o for o in obs if o['year_volume']==x['volume']]
 assert len(oo)==int(x['figures_written']);assert len({o['table_id'] for o in oo})==int(x['tables_used'])
sc=tab(WORK/'series_checks.tsv')
for x in sc:
 cc=[c for c in comp if c['series']==x['series']]
 assert int(x['cells'])==len(cc)
 assert int(x['all_agree_cells'])==sum(c['status']=='all agree' for c in cc)
 assert set(x['years_covered'].split(','))=={c['data_year'] for c in cc}
eye=tab(WORK/'eye_review.tsv');assert len(eye)==30
assert collections.Counter(x['table_id'].split(':')[0] for x in eye)=={'bb1896':10,'bb1871':10,'bb1911':10}
for x in eye:assert any(o['table_id']==x['table_id'] and o['data_year']==x['data_year'] and o['series']==x['series'] and o['value_as_printed']==x['source_literal'] and o['value']==x['output_value'] for o in obs)
worst=tab(WORK/'most_disagreement.tsv');assert len(worst)==20
rank=[]
for x in comp:
 vals=json.loads(x['distinct_values_with_volumes_json'])
 if len(vals)>1:rank.append((int(x['number_of_volumes'])-max(len(v['volumes']) for v in vals),len(vals),int(x['number_of_volumes']),x['series'],x['data_year']))
rank.sort(key=lambda q:(-q[0],-q[1],-q[2],q[3],q[4]))
assert [(x['series'],x['data_year']) for x in worst]==[(x[3],x[4]) for x in rank[:20]]
for x in tab(WORK/'alignment_audit.tsv'):
 assert not any(o['table_id']==x['table_id'] and re.match(r'source row \d+, column '+x['source_column']+r'(?:;|$)',o['note']) for o in obs)
s=json.loads((WORK/'summary.json').read_text());assert s['figures']==len(obs);assert s['skip_records']==len(skips)
assert sum(int(x['figures_skipped']) for x in vcheck)==s['skipped_figure_cells']
report={'result':'pass','observations_checked':len(obs),'comparison_groups_checked':len(comp),'skip_records_read':len(skips),'volumes_checked':len(vcheck),'series_checked':len(sc),'eye_review_records_checked':len(eye),'explicit_sterling_expressions_checked':money_triples,'source_cells_unique':len(seen),'checks':['gzip/TSV read to EOF','source literals, page IDs and coordinates','all original long-table header strings','plain-number identity and independent £/s./d. arithmetic','comparison values, volume sets, ordering and statuses','series mapping completeness','per-volume and per-series counts','all 30 review records','top 20 disagreement ranking','no withheld alignment column leaks into output','1896, 1871, 1911 output ordering']}
(WORK/'validation.json').write_text(json.dumps(report,indent=1)+'\n');print(json.dumps(report,indent=1))
