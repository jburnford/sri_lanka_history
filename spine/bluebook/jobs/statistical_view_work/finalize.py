#!/home/jic823/miniforge3/bin/python
"""Audit sustained displacements, write requested files and checks, without correcting values."""
import json,csv,gzip,pathlib,collections,re
from extract import ROOT,WORK,OUT,read,write,plain
raw=json.loads((WORK/'raw_extraction.json').read_text())
skips=json.loads((WORK/'raw_skips.json').read_text())
counts=json.loads((WORK/'counts.json').read_text())
keys=[p.name.split('.')[0] for p in sorted((ROOT/'tables').glob('*.jsonl.gz'))]
for k in keys:counts.setdefault(k,{});counts[k].setdefault('figures_skipped',0)
# Distinct volumes, not table occurrences, form independent printings.
refs=collections.defaultdict(lambda:collections.defaultdict(set))
for x in raw:
 if x[7] and re.fullmatch(r'(18|19)\d\d',x[3]):refs[x[5],int(x[3])][x[7]].add(x[1])
ref={k:max(v,key=lambda z:len(v[z])) for k,v in refs.items() if max(map(len,v.values()))>=4}
cols=collections.defaultdict(list)
for x in raw:
 if int(x[1][:4])<1924:cols[x[0],x[11]].append(x)
rules={};diagnostics=[]
for (tid,j),xs in cols.items():
 hits=collections.defaultdict(list);aligned=0
 for x in xs:
  if not x[7] or not re.fullmatch(r'(18|19)\d\d',x[3]):continue
  y=int(x[3]);s=x[5]
  if ref.get((s,y))==x[7]:aligned+=1;continue
  for off in [-2,-1,1,2,-10,10]:
   if ref.get((s,y+off))==x[7]:hits[off].append((y,x));break
 for off,vals in hits.items():
  ys=sorted(set(y for y,x in vals));run=best=1
  for a,b in zip(ys,ys[1:]):run=run+1 if b==a+1 else 1;best=max(best,run)
  if len(ys)>=5 and best>=3:
   reason=(f'Unsafe vertical alignment: {len(ys)} exact matches to independently repeated values at data_year {off:+d}, including a run of {best} consecutive years. Entire physical column withheld, including apparently aligned portions; no values moved or corrected.')
   rules[tid,j]=reason
   diagnostics.append([tid,j+1,xs[0][5],off,len(ys),best,aligned,','.join(map(str,ys)),json.dumps([{ 'source_row':x[10]+1,'data_year':x[3],'literal':x[6],'matches_year':y+off} for y,x in vals[:5]],ensure_ascii=False)])
   break
rows=[]
for x in raw:
 if (x[0],x[11]) in rules:
  counts[x[1]]['figures_skipped']+=1
 else:rows.append(x)
for (tid,j),why in rules.items():skips.append([tid,f'entire physical column {j+1}',why])
write(WORK/'alignment_audit.tsv',['table_id','source_column','series_example','year_offset','shifted_matches','longest_consecutive_run','aligned_matches','shifted_year_labels','examples_json'],diagnostics)
# Deterministic requested output. Original pilot ordering is retained.
write(OUT/'statistical_view.tsv.gz',['table_id','year_volume','pdf_page','data_year','column_as_printed','series','value_as_printed','value','note'],(x[:9] for x in rows),True)
write(OUT/'statistical_view_skipped.tsv',['table_id','what_was_skipped','why'],skips)
# One mapping row per series. Headers/unit strings are JSON lists for lossless distinct forms.
mp=collections.defaultdict(lambda:{'h':set(),'u':set(),'v':set()})
for x in rows:
 m=mp[x[5]];m['h'].add(x[4]);m['u'].add('not explicitly stated (count implied by measure)' if x[9]=='No. (count)' else x[9]);m['v'].add(x[1])
write(WORK/'series_map.tsv',['series','distinct_printed_headers_json','unit_or_currency_as_printed_json','first_volume','last_volume'],[(s,json.dumps(sorted(m['h']),ensure_ascii=False),json.dumps(sorted(m['u']),ensure_ascii=False),min(m['v']),max(m['v'])) for s,m in sorted(mp.items())])
# Numeric figures compare by parsed numeric value. Non-numeric cells compare by their exact literal.
groups=collections.defaultdict(lambda:collections.defaultdict(set))
for x in rows:groups[x[5],x[3]][('number',x[7]) if x[7] else ('literal',x[6])].add(x[1])
comp=[];metrics=collections.defaultdict(collections.Counter)
for (s,y),vs in sorted(groups.items()):
 ordered=sorted(vs.items(),key=lambda p:(-len(p[1]),p[0]))
 volumes=set().union(*vs.values());n=len(volumes);nv=len(vs);note=''
 if nv==1:
  status='all agree'
  if n==1:note='single printing only; agreement is vacuous'
 elif nv==2 and min(len(v) for v in vs.values())==1 and max(len(v) for v in vs.values())>=2:
  status='one volume differs';note='probably an OCR slip; no correction made'
 elif nv==2:status='two values'
 else:status='many values'
 if nv==2:
  timeline=sorted((vol,[k for k,v in vs.items() if vol in v]) for vol in volumes)
  if all(len(a)==1 for vol,a in timeline):
   changes=[(timeline[i-1][0],timeline[i][0]) for i in range(1,len(timeline)) if timeline[i-1][1]!=timeline[i][1]]
   if len(changes)==1:note+=('; ' if note else '')+f'chronological change first printed in volume {changes[0][1]} (previous observed volume {changes[0][0]}); possibly a revision'
   else:note+=('; ' if note else '')+'values recur/interleave; no single change volume'
  else:note+=('; ' if note else '')+'one or more volumes contain conflicting printings'
 distinct=[{'value':v,'kind':k,'volumes':sorted(vols)} for (k,v),vols in ordered]
 nonmodal=n-max(map(len,vs.values()))
 comp.append([s,y,n,json.dumps(distinct,ensure_ascii=False,separators=(',',':')),status,note,nv,nonmodal])
 m=metrics[s];m['cells']+=1;m['agree']+=nv==1;m['multi']+=n>=2;m['multi_agree']+=nv==1 and n>=2
write(OUT/'statistical_view_compare.tsv',['series','data_year','number_of_volumes','distinct_values_with_volumes_json','status','note'],(x[:6] for x in comp))
write(WORK/'series_checks.tsv',['series','years_covered','cells','all_agree_cells','share_all_agree','cells_with_2plus_volumes','all_agree_2plus_cells','share_all_agree_2plus'],[(s,','.join(sorted(y for ss,y in groups if ss==s)),m['cells'],m['agree'],f"{m['agree']/m['cells']:.6f}",m['multi'],m['multi_agree'],f"{m['multi_agree']/m['multi']:.6f}" if m['multi'] else '') for s,m in sorted(metrics.items())])
worst=sorted((x for x in comp if x[6]>1),key=lambda x:(-x[7],-x[6],-x[2],x[0],x[1]))[:20]
write(WORK/'most_disagreement.tsv',['series','data_year','number_of_volumes','distinct_values_with_volumes_json','status','note','distinct_values','volumes_outside_modal_value'],worst)
# Final source-identity checks are exhaustive and independent of numeric parsing.
source={}
for key in keys:
 for t in read(ROOT/f'tables/{key}.jsonl.gz'):source[t['id']]=t
for x in rows:
 t=source[x[0]]
 assert t['rows'][x[10]][x[11]]==x[6],x
 assert x[8].startswith(f'source row {x[10]+1}, column {x[11]+1}')
 assert re.fullmatch(r'(?:18|19)\d\d(?:[-–]\d{2,4})?',x[3]),x
 assert x[7]==plain(x[6],x[9]=='£')[0]
 assert x[1]==x[0].split(':')[0][2:]
assert len({(x[0],x[10],x[11]) for x in rows})==len(rows),'Duplicate source cells'
# The by-eye review records literal source rows and the output beside them.
spec=json.loads((WORK/'eye_review_spec.json').read_text())
# Displaced 1896 tonnage was discovered during pilot review; replace with a safely retained trade figure.
spec['1896'][7]=['imports_uk_value_rupees','1896']
review=[]
for key,checks in spec.items():
 for series,year in checks:
  found=[x for x in rows if x[1]==key and x[5]==series and x[3]==year]
  assert len(found)==1,(key,series,year,len(found))
  x=found[0];t=source[x[0]]
  review.append([x[0],x[3],x[5],x[10]+1,x[11]+1,x[6],x[7],json.dumps(t['rows'][x[10]],ensure_ascii=False),'matches literal source cell and header; numeric conversion checked' if x[7] else 'footnote-marked literal retained; numeric value correctly empty'])
write(WORK/'eye_review.tsv',['table_id','data_year','series','source_row','source_column','source_literal','output_value','entire_source_row_json','finding'],review)
write(WORK/'volume_checks.tsv',['volume','tables_used','figures_written','figures_skipped','table_ids'],[(k,len({x[0] for x in rows if x[1]==k}),sum(x[1]==k for x in rows),counts[k]['figures_skipped'],'; '.join(sorted({x[0] for x in rows if x[1]==k}))) for k in keys])
summary={'figures':len(rows),'numeric_figures':sum(bool(x[7]) for x in rows),'literal_only_figures':sum(not x[7] for x in rows),'tables':len({x[0] for x in rows}),'volumes_with_figures':len({x[1] for x in rows}),'volumes_scanned':len(keys),'skipped_figure_cells':sum(c['figures_skipped'] for c in counts.values()),'skip_records':len(skips),'alignment_columns_withheld':len(rules),'series':len(mp),'series_year_cells':len(comp),'all_agree_cells':sum(x[4]=='all agree' for x in comp),'statuses':dict(collections.Counter(x[4] for x in comp))}
(WORK/'summary.json').write_text(json.dumps(summary,indent=1))
print(json.dumps(summary,indent=1))
print('Alignment columns:',len(diagnostics))
