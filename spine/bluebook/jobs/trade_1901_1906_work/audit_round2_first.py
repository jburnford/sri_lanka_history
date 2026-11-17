"""Reproduce the before/after queries and the reviewer recheck (standard library).
Run from the repository root with PYTHONDONTWRITEBYTECODE=1.
"""
import csv, gzip, json, re, collections
from pathlib import Path
W=Path(__file__).resolve().parent
ROOT=W.parents[1]

def read(p):
    return list(csv.DictReader(gzip.open(p,'rt') if str(p).endswith('.gz') else open(p),delimiter='\t'))
def source(r):return int(re.search(r'source row (\d+)',r['note'])[1])
def key(r):return r['table_id'],source(r),r['measure']
def nk(s):return re.sub(r'[^a-z0-9]','',re.sub(r'[—–-]?\s*contd\.?','',s,flags=re.I).lower())
def label_equal(a,b):
    # Ignore continuation furniture and typography, but preserve word spelling,
    # commas and the presence of a heading separator.
    def canonical(s):
        s=re.sub(r'[—–-]?\s*contd\.?','',s,flags=re.I)
        s=re.sub(r'\s*[—–]\s*','— ',s)
        return ' '.join(s.strip(' .').split()).lower()
    return canonical(a)==canonical(b)
def output(p,fields,rows):
    with open(p,'w',newline='') as f:
        w=csv.DictWriter(f,fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
old=read(W/'before_trade_1880_1906.tsv.gz')
new=read(ROOT/'extracted/trade_1880_1906.tsv.gz')
skips=read(ROOT/'extracted/trade_1880_1906_skipped.tsv')
samples=read(W/'scan_check_sample.tsv'); verdicts=read(W/'scan_check_results.tsv')
idx=collections.defaultdict(list)
for r in new:idx[key(r)].append(r)
# Expected labels transcribed from the reviewer's statements. Structural slashes
# become dashes; contd is furniture. No spelling correction is made to the output.
expected={}
def expect(ids,article=None,country=None,unit=None,cl=None,gr=None):
    for i in ids:
        expected.setdefault(i,{})
        for k,v in [('article_as_printed',article),('country_as_printed',country),('unit_as_printed',unit),('class_as_printed',cl),('group_as_printed',gr)]:
            if v is not None:expected[i][k]=v
expect([9,10,11],'Tobacco manufactured— Other')
expect([17,18,19,20],'Tea')
expect([23,24],'Tobacco, manufactured— Cigars')
expect([31,32],'Natural History Specimens')
expect([38,39],'Seeds— Gingelly');expect([40],'Seeds— Tea')
expect([48],'Fish— Tinned')
expect([50],'Wines, still— Burgundy— In bottle')
expect([61],'Leather— Goat and Sheep Skins')
expect(range(69,73),'Apparel, made up',cl='III.—Manufactured Articles',gr='(1) Textile (a) Apparel, made up')
expect([73,74],'Jewellery');expect([77],'Machinery— Other')
expect([97],'Skins, undressed');expect(range(99,103),'Tortoise shell');expect([103,104],'Unenumerated')
expect([105,145],country='Other British Possessions in Asia')
expect([111,112,151,152],'Lace and Net')
expect(range(113,118),'Coir— Yarn');expect([118,119],'Coir— Other')
expect([159,160],'Books');expect([162],'Arms— Revolvers');expect([163],unit='No.')
expect([164],'Asphalt');expect([165],'Beads');expect([166,167,168],'Boats')
expect([171],'Sugar— Refined or Candied');expect([172],'Sugar— Unrefined')
expect([176],country='Tasmania')
expect([185],'Bricks and Tiles',country='Java');expect([186],'Bricks and Tiles')
expect(range(187,191),'Carriages and Carts')
expect([191],'Coir— Matting');expect([192],'Coir— Rope')
expect([193],'Stationery, excluding Paper');expect([194],'Stones, worked');expect([195],'Tallow and Stearine');expect([196],'Tar');expect([197],'Timber, worked')
expect([198,199],'Unenumerated— Dutiable');expect([200],'Unenumerated— Free')
expect([208],'Manure— Bone')
expect([221],country='Austria',unit='doz.');expect([222,224],unit='yds.')
expect([226],unit='cwt.')
expect([226,227],'Fibre— Coir',cl='II.—Raw Materials',gr='(3) Other (b) Miscellaneous')
expect([228,229],'Fibre— Palmyra')
expect([230],'Horns— Deer');expect([231],'Horns— Other');expect([232],'Natural History Specimens')
expect([234],'Instruments— Scientific')
results=[]
for i,(s,v) in enumerate(zip(samples,verdicts),1):
    assert all(s[k]==v[k] for k in ['table_id','measure','value_as_printed','article_as_printed','country_as_printed']),i
    matches=idx[key(s)]
    n=next((r for r in matches if r['value_as_printed']==s['value_as_printed']),matches[0] if matches else None)
    target={k:s[k] for k in ['article_as_printed','country_as_printed','unit_as_printed']}
    target.update(expected.get(i,{}))
    why='labels equal the reviewer’s stated labels (continuation furniture ignored)'
    if n is None:judgement='removed from output';why='withheld rather than labelled as readable data'
    elif v['verdict']=='cannot_tell':judgement='cannot tell';why='reviewer could not resolve the printed digit'
    elif v['verdict']=='wrong_value':judgement='no';why='reported OCR digit error deliberately unchanged'
    elif all(label_equal(n[k],val) for k,val in target.items()):judgement='yes'
    else:
        judgement='no';why='; '.join(f'{k}: expected {val!r}, got {n[k]!r}' for k,val in target.items() if not label_equal(n[k],val))
    row=dict(s)
    row.update(sample_number=str(i),source_row=str(source(s)),old_verdict=v['verdict'],what_the_page_shows=v['what_the_page_shows'],reviewer_comment=v['comment'],
               new_article=n['article_as_printed'] if n else '',new_country=n['country_as_printed'] if n else '',new_unit=n['unit_as_printed'] if n else '',
               new_class=n['class_as_printed'] if n else '',new_group=n['group_as_printed'] if n else '',new_note=n['note'] if n else '',
               matches=str(len(matches)),judgement=judgement,judgement_reason=why,
               expected_labels=json.dumps(target,ensure_ascii=False))
    results.append(row)
output(W/'recheck.tsv',list(results[0]),results)
counts=collections.Counter(r['judgement'] for r in results)
by_verdict={v:dict(collections.Counter(r['judgement'] for r in results if r['old_verdict']==v)) for v in sorted({r['old_verdict'] for r in results})}

# These predicates are the before/after queries reported in README.md. Counts
# refer to emitted measure rows, not source rows, unless named source_rows.
def heading_examples(r):
    a=r['article_as_printed']
    return bool(re.search(r'^(?:Rifles— (?:Books|Asphalt|Beads|Boats)|Shells— Skins, undressed|Stones— (?:Tortoise shell|Unenumerated)|Railway Plant and Rolling Stock— (?:Stationery|Stones|Tallow|Tar|Timber))',a) or a in ('Other','Tinned','Free','Bone','Gingelly'))
def fused(r):return bool(re.match(r'^(?:[IVXL]+\.|Articles—|\(\d+\) (?:Live Animals|Of Metal|Spirits))',r['article_as_printed']))
def cotton(r):return r['article_as_printed']=='Cotton' and 'Cotton' in r['group_as_printed'] and '(b)' in r['group_as_printed']
def collapsed(r):return r['measure'].startswith('quantity') and bool(re.search(r'\.{2,}|["„”]|Br\.? Col|For\.? Coun',r['unit_as_printed']))
def brace(r):return r['measure'].startswith('quantity') and bool(re.search('[{}]',r['country_as_printed']+r['unit_as_printed']))
def wrapped_fragment(r):return bool(re.search(r'Pos-\s*$|^sessions\b',r['country_as_printed']))
def furniture(r):return bool(re.search(r'contd|carried (?:over|forward)|brought forward',r['country_as_printed'],re.I))
def gov(r):return r['flow']=='import' and any(r['year_volume']==y and lo<=int(r['pdf_page'])<=hi for y,lo,hi in [('1904',711,716),('1905',730,737),('1906',733,738)])
def tea_components(r):return r['article_as_printed']=='Tea' and bool(re.search('component (?:black|green)',r['note']))
metrics={name:{'before':sum(fn(r) for r in old),'after':sum(fn(r) for r in new)} for name,fn in [('1_heading_examples',heading_examples),('2_fused_class_group',fused),('3_cotton_as_article',cotton),('4_country_list_units',collapsed),('5_braces_in_labels',brace),('6_wrapped_country_fragments',wrapped_fragment),('7_country_furniture',furniture),('8_government_ledger_rows',gov),('9_tea_components',tea_components)]}
metrics['8_government_notes']={'before':sum('government stores imports' in r['note'] for r in old),'after':sum('government stores imports' in r['note'] for r in new)}
for name,pattern in [('4_collapsed_source_rows','collapsed article block'),('5_ambiguous_brace_source_rows','ambiguous braced'),('7_lost_country_source_rows','country name lost'),('9_tea_skipped_source_rows','tea row fits no')]:
    metrics[name]={'after':sum(pattern in r['reason'] for r in skips)}
metrics['1_heading_uncertain_rows']={'after':sum('heading uncertain:' in r['note'] for r in new)}
metrics['5_decoded_brace_rows']={'after':sum('braced unit line' in r['note'] for r in new)}
metrics['6_joined_or_reassociated_rows']={'after':sum('wrapped country name' in r['note'] for r in new)}
metrics['6_possible_shift_rows']={'after':sum('possible row shift after a wrapped country name' in r['note'] for r in new)}
old_index=collections.defaultdict(list)
for r in old:old_index[key(r)].append(r)
for field in ['article_as_printed','class_as_printed','group_as_printed','country_as_printed','unit_as_printed']:
    metrics['changed_'+field]={'after':sum(any(o[field]!=r[field] for o in old_index[key(r)]) for r in new if key(r) in old_index)}

# Validate numeric provenance: each emitted nonblank raw figure must occur in
# its own OCR source row. Splitting an OCR cell containing Black and Green is
# allowed, but altering its digits is not.
tables={}
for y in range(1901,1907):
    tables.update((t['id'],t) for t in map(json.loads,gzip.open(ROOT/f'tables/{y}.jsonl.gz','rt')))
errors=[]
for r in new:
    raw=re.sub(r'^Rs\.?\s*','',r['value_as_printed']).strip()
    cells=tables[r['table_id']]['rows'][source(r)]
    tokens={re.sub(r'^Rs\.?\s*','',x).strip() for x in cells}
    tokens.update(v for x in cells for v in x.split())
    if raw and raw not in tokens:errors.append((key(r),raw,cells))
    if r['value'] and r['value']!=raw.replace(',',''):errors.append(('parsed value differs',key(r)))
assert not errors,errors[:5]
assert not any(brace(r) or collapsed(r) for r in new)
assert not any(not r['article_as_printed'] for r in new)
assert not any(furniture(r) for r in new)
assert all('government stores imports' in r['note'] for r in new if gov(r))
assert list(old[0]) == list(new[0])
assert len(results)==240
summary=dict(recheck_counts=dict(counts),by_old_verdict=by_verdict,metrics=metrics,output_rows=dict(before=len(old),after=len(new)),numeric_provenance_errors=len(errors))
(W/'round2_first_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,indent=2))
