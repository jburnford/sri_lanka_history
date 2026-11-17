"""Round-two audit; standard library. Run after the reader and audit_round2_first.py."""
import collections, csv, gzip, json, re, sys
from pathlib import Path
W=Path(__file__).resolve().parent
ROOT=W.parents[1]
def read(p):
    with (gzip.open(p,'rt') if str(p).endswith('.gz') else open(p)) as f:
        return list(csv.DictReader(f,delimiter='\t'))
def source(r): return int(re.search(r'source row (\d+)',r['note'])[1])
def key(r): return r['table_id'], source(r), r['measure']
def equal(a,b):
    def canon(x):
        x=re.sub(r'[—–-]?\s*contd\.?','',x,flags=re.I)
        return ' '.join(re.sub(r'\s*[—–]\s*','— ',x).strip(' .').split()).lower()
    return canon(a)==canon(b)
def write(p,rows):
    with open(p,'w',newline='') as f:
        w=csv.DictWriter(f,list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
old=read(W/'round2_before_trade_1880_1906.tsv.gz')
new=read(ROOT/'extracted/trade_1880_1906.tsv.gz')
skips=read(ROOT/'extracted/trade_1880_1906_skipped.tsv')
idx=collections.defaultdict(list); oldidx=collections.defaultdict(list)
for r in new:idx[key(r)].append(r)
for r in old:oldidx[key(r)].append(r)
fields=['table_id','article_as_printed','country_as_printed','measure','value_as_printed']
sample_idx=collections.defaultdict(list)
for r in old:sample_idx[tuple(r[k] for k in fields)].append(r)
# Literal expected labels transcribed from scan_check2_results, not learned by
# the reader from this map. Typography/contd furniture alone is ignored.
expected_articles={17:'Spices— Pepper (long)',18:'Spices— Other',
33:'Paper— Other— Dutiable',34:'Paper— Other— Dutiable',35:'Paper— Other— Free',
65:'Spices— Cinnamon, Wild',66:'Spices— Cinnamon, Wild',67:'Spices— Cloves and Mace',
68:'Spices— Nutmegs',69:'Spices— Pepper',150:'Spices— Vanilla',
154:'Seeds, excluding Food Stuffs— Unenumerated— Duitable',161:'Wines, still— Other— In wood',
162:'Wines, still— Other— In wood',184:'Pearls and Precious Stones',
188:'Cocoanut— Fresh',189:'Cocoanut— Fresh',190:'Coffee— Arabian— Plantation',
191:'Coffee— Arabian— Plantation',192:'Coffee— Liberian',
198:'Unenumerated— Dutiable',199:'Unenumerated— Dutiable',200:'Unenumerated— Dutiable',
**{i:'Oil— Liquid Fuel' for i in range(209,215)},220:'Cinchona Bark',221:'Cinchona Bark'}
results=[]
for i,s in enumerate(read(W/'scan_check2_results.tsv'),1):
    candidates=sample_idx[tuple(s[k]for k in fields)]
    assert candidates,(i,s)
    candidates=sorted(candidates,key=source)
    o=candidates[0]
    # Sample 176 contains identical figures/labels on both braced unit lines.
    # Check both source rows and retain the ambiguity explicitly.
    ns=[]
    for candidate in candidates:
        matches=idx[key(candidate)]
        n=next((r for r in matches if r['value_as_printed']==candidate['value_as_printed']),matches[0] if matches else None)
        ns.append(n)
    n=ns[0]
    target={k:o[k]for k in ['article_as_printed','class_as_printed','group_as_printed','measure','country_as_printed','country_group_as_printed','unit_as_printed']}
    target['article_as_printed']=expected_articles.get(i,s['article_as_printed'])
    if i in (41,42):target['group_as_printed']='(1) Textile (b) Cotton'
    if 65<=i<=72:target['class_as_printed']='I.—'
    if i==70:target['country_group_as_printed']='British Colonies'
    if i==223:
        target['class_as_printed']='III.—Manufactured Articles'
        target['group_as_printed']='(1) Textile (b) Cotton'
    if 231<=i<=235:target['class_as_printed']='I.—Live Animals'
    diffs=[]
    if n:
        for field,value in target.items():
            if not equal(n[field],value):diffs.append(f'{field}: expected {value!r}; got {n[field]!r}')
        if s['verdict']=='wrong_value':diffs.append('reported OCR digit error deliberately unchanged')
        if n['value_as_printed']!=o['value_as_printed']:diffs.append('measure now points to a different printed cell')
    judgement='removed from output' if n is None else 'no' if diffs else 'yes'
    article_agrees='removed from output' if n is None else 'yes' if equal(n['article_as_printed'],target['article_as_printed']) else 'no'
    provenance=''
    if len(candidates)>1:
        assert all(x is not None and all(equal(x[f],n[f])for f in target)for x in ns)
        provenance='sample omits source row; two identical reviewed value/label matches; both checked, first listed'
    result=dict(s)
    result.update(sample_number=i,source_row=source(o),source_row_candidates='|'.join(str(source(x))for x in candidates),baseline_match_count=len(candidates),
        old_verdict=s['verdict'],new_article=n['article_as_printed']if n else '',new_class=n['class_as_printed']if n else '',
        new_group=n['group_as_printed']if n else '',new_measure=n['measure']if n else '',new_country_group=n['country_group_as_printed']if n else '',
        new_country=n['country_as_printed']if n else '',new_unit=n['unit_as_printed']if n else '',new_value_as_printed=n['value_as_printed']if n else '',
        new_note=n['note']if n else '',article_agrees=article_agrees,judgement=judgement,
        judgement_reason='; '.join(diffs) if diffs else 'all reviewed labels and figure agree',provenance_note=provenance,
        expected_labels=json.dumps(target,ensure_ascii=False))
    results.append(result)
assert len(results)==238
write(W/'recheck2.tsv',results)

# Before/after counts below are emitted measure rows, unless explicitly named.
reversed_ids={f'bb{y}:p{p}:t1'for y,p in [(1902,636),(1903,668),(1904,676),(1905,695),(1906,698)]}
tables={t['id']:t for y in range(1901,1907)for t in map(json.loads,gzip.open(ROOT/f'tables/{y}.jsonl.gz','rt'))}
def wrong_reversed_cell(r):
    if r['table_id']not in reversed_ids or not r['measure'].startswith('quantity'):return False
    cells=tables[r['table_id']]['rows'][source(r)]
    if cells[2]==cells[3]:return False
    expected=cells[3]if r['measure']=='quantity_total' else cells[2]
    return r['value_as_printed']!=expected
spice_leaves={'Wild','Cloves and Mace','Nutmegs','Pepper','Pepper (long)','Vanilla','Ginger','Liberian','Plantation'}
def textile_missing(r):
    return ((r['table_id']=='bb1902:p614:t1' and source(r)<26) or (r['table_id']=='bb1906:p721:t1' and source(r)<19)) and '(b) Cotton' not in r['group_as_printed']
queries={
'A_orphan_Other_or_Arabian':lambda r:r['article_as_printed'].startswith(('Other— ','Arabian— ')),
'A_at_least_three_levels':lambda r:r['article_as_printed'].count('—')>=2,
'B_bare_named_food_subentries':lambda r:r['article_as_printed']in spice_leaves and 'Food and Drink'in r['group_as_printed'],
'C_bare_Liquid_Fuel':lambda r:r['article_as_printed']=='Liquid Fuel',
'C_Oil_Liquid_Fuel':lambda r:r['article_as_printed']=='Oil— Liquid Fuel',
'D_Silver_Pearls':lambda r:r['article_as_printed']=='Silver— Pearls and Precious Stones',
'D_Desiccated_Fresh':lambda r:r['article_as_printed']=='Desiccated— Fresh',
'E_Arippe_Cinchona_Bark':lambda r:r['article_as_printed']=='Arippe Cinchona Bark',
'F_Durable_literal':lambda r:bool(re.search(r'\bDurable\b',r['article_as_printed'])),
'G_wrong_cells_on_unequal_reversed_quantities':wrong_reversed_cell,
'G_reversed_page_quantity_rows':lambda r:r['table_id']in reversed_ids and r['measure'].startswith('quantity'),
'H_missing_Cotton_on_two_reviewed_continuations':textile_missing,
'H_1902_export_empty_class':lambda r:r['year_volume']=='1902'and r['flow']=='export'and not r['class_as_printed'],
'H_literal_1_or_L_class':lambda r:bool(re.match(r'^(?:1|L)\.',r['class_as_printed'])),
'H_1906_p733_wrong_class':lambda r:r['table_id']=='bb1906:p733:t1'and source(r)<13 and r['class_as_printed']!='I.—Live Animals',
'H_1906_p721_short_printed_class':lambda r:r['table_id']=='bb1906:p721:t1'and r['class_as_printed']=='III.—Manufactured',
'I_1904_Perfumery_emitted':lambda r:r['table_id']=='bb1904:p676:t1'and r['article_as_printed']=='Perfumery',
'I_Cotton_quantity_other_produce':lambda r:r['table_id']=='bb1906:p714:t1'and 7<=source(r)<=18 and r['measure']=='quantity_other_produce',
'I_Cotton_named_components':lambda r:r['table_id']=='bb1906:p714:t1'and bool(re.search('component (?:Kapok or Tree Cotton|Cotton for Spinning)',r['note'])),
'J_Arrack_British_India_missing_country_group':lambda r:r['table_id']=='bb1902:p649:t1'and r['article_as_printed']=='Spirits— Arrack'and r['country_as_printed']=='British India'and not r['country_group_as_printed'],
'J_country_rows_with_empty_group':lambda r:r['row_kind']=='country'and not r['country_group_as_printed'],
}
metrics={name:{'before':sum(bool(fn(r))for r in old),'after':sum(bool(fn(r))for r in new)}for name,fn in queries.items()}
changed_cg=[r for r in new if any(not o['country_group_as_printed']and r['country_group_as_printed']for o in oldidx[key(r)])]
metrics['J_retained_rows_newly_given_country_group']={'after':len(changed_cg)}
metrics['I_explicit_ambiguous_subcolumn_skips']={'after':sum('quantity sub-columns'in r['reason']for r in skips)}

# Provenance: every raw figure is in its source OCR row (possibly a literal
# numeric component inside a merged Tea or re-headed Cotton cell).
errors=[]
for r in new:
    cells=tables[r['table_id']]['rows'][source(r)]
    raw=r['value_as_printed'].strip()
    tokens={re.sub(r'^Rs\.?\s*','',x).strip()for x in cells}
    tokens.update(x for c in cells for x in c.split())
    if raw and raw not in tokens:errors.append((key(r),raw))
    if r['value'] and r['value']!=raw.replace(',',''):errors.append(('numeric value',key(r)))
assert not errors,errors[:5]
assert list(old[0])==list(new[0])
assert not any(not r['article_as_printed']for r in new)
# Figure/country preservation is tested independently of changed measure names.
def numeric_identity(r):return (r['table_id'],source(r),r['value_as_printed'],r['country_as_printed'])
new_numeric={numeric_identity(r)for r in new}
removed=[r for r in old if numeric_identity(r)not in new_numeric]
if '--round3' not in sys.argv:
    assert all(r['table_id']=='bb1904:p676:t1'and r['article_as_printed']=='Perfumery'for r in removed),removed[:3]
for r in old:
    if 'Durable'in r['article_as_printed']:
        assert all('Durable'in n['article_as_printed']for n in idx[key(r)])

first_before=read(W/'round2_before_recheck.tsv');first_after=read(W/'recheck.tsv')
regressions=[]
for o,n in zip(first_before,first_after):
    if o['judgement']=='yes'and n['judgement']!='yes':
        regressions.append({'sample_number':n['sample_number'],'before_article':o['new_article'],'after_article':n['new_article'],'judgement':n['judgement'],'reason':n['judgement_reason']})
write(W/'recheck_round2_regressions.tsv',regressions or [{'sample_number':'','before_article':'','after_article':'','judgement':'','reason':'none'}])
summary=dict(output_rows={'before':len(old),'after':len(new)},metrics=metrics,
    recheck2_counts=dict(collections.Counter(r['judgement']for r in results)),
    recheck2_article_counts=dict(collections.Counter(r['article_agrees']for r in results)),
    recheck2_by_old_verdict={v:dict(collections.Counter(r['judgement']for r in results if r['old_verdict']==v))for v in sorted({r['old_verdict']for r in results})},
    first_recheck_counts=dict(collections.Counter(r['judgement']for r in first_after)),first_recheck_regressions=regressions,
    numeric_provenance_errors=len(errors),baseline_measure_rows_withheld=len(removed),
    sample2_ambiguous_source_rows=[r['sample_number']for r in results if r['baseline_match_count']>1])
(W/'round2_audit_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
