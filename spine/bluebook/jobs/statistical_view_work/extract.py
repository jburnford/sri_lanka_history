#!/home/jic823/miniforge3/bin/python
"""Conservative, reproducible extraction. Standard library; no network; scoped writes."""
import csv,gzip,json,re,pathlib,collections,decimal,argparse
ROOT=pathlib.Path(__file__).resolve().parents[2]
WORK=ROOT/'jobs/statistical_view_work'
OUT=ROOT/'extracted'
YEAR=re.compile(r'(?:18|19)\d{2}(?:[-–]\d{2,4})?\Z')
NUM=re.compile(r'[+-]?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?\Z')
UNIT=re.compile(r'(?:£\.?|Rs\.?|Rupees\.?|Acres?\.?|Ares\.?|Tons\.?|No\.?)\Z',re.I)
MISSING=re.compile(r'[.·…\s—–\-]*\Z')
D=decimal.Decimal

def read(path):
 with gzip.open(path,'rt') as f:return [json.loads(l) for l in f]
def write(path,head,rows,gz=False):
 op=gzip.open if gz else open
 with op(path,'wt',encoding='utf-8',newline='') as f:
  w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(head);w.writerows(rows)
def plain(s,sterling=False):
 s=s.strip()
 if NUM.fullmatch(s):return str(D(s.replace(',',''))),''
 if sterling:
  # Explicit s./d. notation only; no conjectural triples.
  m=re.fullmatch(r'£?\s*([\d,]+)\.?\s+(\d+)s\.(?:\s*(\d+)d\.)?',s)
  if m and int(m[2])<20 and int(m[3] or 0)<12:
   v=D(m[1].replace(',',''))+D(m[2])/20+D(m[3] or 0)/240
   return format(v.quantize(D('.000000000001')).normalize(),'f'),'£ s. d. expressed as decimal pounds; rounded to 12 decimal places when recurring'
 # Currency prefix is an explicit unit, not a digit repair.
 m=re.fullmatch(r'(?:£|Rs\.?)\s*([\d,]+(?:\.\d+)?)',s)
 if m and NUM.fullmatch(m[1]):return str(D(m[1].replace(',',''))),'explicit currency prefix'
 return '','not a plain number; literal cell retained'

def headers(t):
 # Preserve every header row, including repeated expanded span cells.
 return [' / '.join(r[j] for r in t['rows'][:t['header_rows']] if j<len(r) and r[j] and not YEAR.fullmatch(r[j].strip())) for j in range(t['n_cols'])]
def mapping(h):
 s=h.lower()
 if not s:return None
 if 'year' in s and not any(x in s for x in ['population','revenue']):return None
 if 'population' in s:return 'population','No. (count)'
 if 'military' in s:return ('military_and_shipping' if 'shipping' in s else 'military'),'No. (count)'
 for word in ['births','marriages','deaths']:
  if word in s:return word,'No. (count)'
 if 'scholar' in s:return 'scholars','No. (count)'
 if 'schools' in s:return 'schools','No. (count)'
 if 'square miles' in s:return 'area_square_miles','square miles'
 if 'cultivation' in s:return 'cultivated_area_acres','Acres.'
 if 'land sales' in s:
  if 'amount' in s:return 'land_sales_amount','money'
  if 'extent' in s or 'acres' in s:return 'land_sales_acres','Acres.'
 if 'revenue' in s:return 'revenue','money'
 if 'expenditure' in s:return 'expenditure','money'
 if 'tonnage' in s:
  if 'foreign' in s or 'fore gn' in s:return 'shipping_foreign_tonnage','Tons.'
  if 'colonies' in s:return 'shipping_british_colonies_tonnage','Tons.'
  if 'british' in s and 'united kingdom' in s:return 'shipping_british_uk_tonnage','Tons.'
  if 'united kingdom' in s:return 'shipping_uk_tonnage','Tons.'
  if 'other countries' in s:return 'shipping_other_countries_tonnage','Tons.'
  if 'total.' in s:return 'shipping_total_tonnage','Tons.'
 for flow in ['imports','exports']:
  if flow in s:
   if 'united kingdom' in s:return flow+'_uk_value','money'
   if 'other countries' in s:return flow+'_other_countries_value','money'
   if 'total' in s:return flow+'_value','money'
 return None

class Extraction:
 def __init__(self,keys):
  self.keys=keys;self.rows=[];self.skips=[];self.count=collections.defaultdict(collections.Counter);self.used=collections.defaultdict(set);self.context={};self.tables={};self.colrules=[]
 def skip(self,t,what,why,n=0):
  self.skips.append((t['id'],what,why));self.count[t['_key']]['figures_skipped']+=n
 def emit(self,t,i,j,y,h,series,unit,raw,note=''):
  if not raw.strip() or MISSING.fullmatch(raw.strip()) or UNIT.fullmatch(raw.strip()):return
  v,n=plain(raw,unit=='£')
  notes=f'source row {i+1}, column {j+1}'
  if note:notes+='; '+note
  if n:notes+='; '+n
  self.rows.append([t['id'],t['_key'],t['pdf_page'],y,h,series,raw,v,notes,unit,i,j])
  self.used[t['_key']].add(t['id']);self.count[t['_key']]['figures_written']+=1
 def load(self,key):
  ts=read(ROOT/f'tables/{key}.jsonl.gz');ps=read(ROOT/f'pages/{key}.jsonl.gz')
  for t in ts:t['_key']=key;self.tables[t['id']]=t
  # Broad series search across the whole volume, not just front matter.
  chosen=[]
  for t in ts:
   h=' '.join(t['headings']);top=' '.join(' '.join(r) for r in t['rows'][:2])
   if len(t['rows'])>35 and ('Area in' in top and 'Population' in top or 'Tonnage of Shipping entered' in top or ('STATISTICAL VIEW' in h and t['n_cols']>=12) or t['id'] in ['bb1891:p291:t1','bb1917:p12:t1','bb1920:p12:t1']):
    chosen.append(t)
  pp={t['pdf_page'] for t in chosen}
  # Include abridged series by page heading, even when table headings are empty.
  abr_pages={p['pdf_page'] for p in ps if p['pdf_page']<25 and any('STATISTICAL VIEW OF THE PROGRESS' in s for s in p.get('text',[])+p.get('headings',[]))}
  if int(key[:4])>=1924:
   chosen=[t for t in ts if t['pdf_page'] in abr_pages or (t['pdf_page']<18 and t['rows'] and any('Cleared (Total)' in c for r in t['rows'][:4] for c in r))]
   # Include continuation page immediately after titled first page.
   chosen+= [t for t in ts if t['pdf_page'] in {p+1 for p in abr_pages} and t not in chosen and t['pdf_page']<18]
   chosen=[t for t in chosen if not any('INDEX' in s for s in t['headings'])]
  selected_pages={t['pdf_page'] for t in chosen}
  ctx=[p for p in ps if p['pdf_page'] in selected_pages or any('STATISTICAL VIEW OF THE PROGRESS' in s for s in p.get('headings',[])+p.get('text',[])) or p['pdf_page'] in {p-1 for p in selected_pages}]
  self.context[key]=ctx
  for p in ps:
   if p['pdf_page'] in abr_pages and p['n_tables']==0 and any('1881 TO' in s for s in p.get('text',[])):
    self.skips.append((f"bb{key}:p{p['pdf_page']}:no_table",'abridged first page','Page announces the series but supplied OCR has no parsed table; no figures reconstructed.'))
  if not chosen:
   self.skips.append((f'bb{key}:no_table','entire series','No safely identifiable parsed series table in supplied volume; searched all tables and local page metadata. No figures reconstructed.'))
  for t in chosen:
   if int(key[:4])>=1924:self.abridged(t,chosen)
   else:self.long(t,ctx)
  # Footnote tables are context, not independent annual columns.
  for t in ts:
   if t not in chosen and t['pdf_page'] in selected_pages:
    self.skip(t,'supplementary table','Footnote/surplus-funds schedule, not a column of the annual statistical view; retained via source context where relevant.')
 def long(self,t,ctx):
  key=t['_key'];hs=headers(t);maps=[mapping(h) for h in hs];rs=t['rows']
  top=' '.join(rs[0]);main='Population' in top
  if t['id'] in ['bb1894:p7:t1','bb1909:p8:t1']:
   self.skip(t,'entire table','Systematically corrupted data-year labels or inconsistent shipping/trade column headers and changing horizontal offsets; cannot safely assign figures.',sum(bool(re.search(r'\d',c)) for r in rs[t['header_rows']:] for c in r if not YEAR.fullmatch(c.strip())));return
  if key=='1866' or (main and key in ['1871','1886','1892','1914']):
   self.skip(t,'entire table','Unsafe column alignment: omitted/shifted area or population cells, changing column offsets and/or displaced financial rows. Values not reassigned.',sum(bool(re.search(r'\d',c)) for r in rs[t['header_rows']:] for c in r[1:]));return
  if main and key=='1893':
   self.skip(t,'entire table','Year and area columns absent from parsed table; cannot assign data years safely.',sum(bool(re.search(r'\d',c)) for r in rs[t['header_rows']:] for c in r));return
  yearcols=[j for j,h in enumerate(hs) if re.fullmatch(r'(?:Year\.?\s*(?:/\s*)?)+',h,re.I)]
  if not yearcols:
   self.skip(t,'entire table','No unambiguous Year column in header.',sum(bool(re.search(r'\d',c)) for r in rs[t['header_rows']:] for c in r if not YEAR.fullmatch(c.strip())));return
  yc=yearcols[0]
  # Corrupted headers and overlap columns are skipped rather than silently remapped.
  blocked={}
  if main:
   if key=='1885':
    for j in range(1,12):blocked[j]='Demographic/land columns shift as omitted area and population spans change; only separately aligned Revenue and Expenditure retained.'
   if key in ['1890','1918','1920','1922']:blocked[11]='Land Sales / Extent header conflicts with amount cells and displaced Amount header elsewhere.'
   if key in ['1891','1894']:blocked.update({12:'Financial data displaced one column from header.',13:'Financial data displaced one column from header.'})
   if key=='1897':blocked[12]='Revenue column missing/displaced in parsed rows.'
   if key=='1907':blocked[13]='Expenditure strings systematically truncated at right edge.'
  if not main:
   for j,m in enumerate(maps):
    if m and m[0]=='expenditure':blocked[j]='Overlapping expenditure fragment from facing page; incomplete duplicate, not an independent printed column.'
  if not main and key in ['1915','1918']:
   for j,m in enumerate(maps):
    if m and m[0]=='shipping_uk_tonnage':blocked[j]='UK tonnage column systematically loses leading digits into adjoining material; incomplete cells not repaired.'
  if key=='1877' and not main:blocked[0]='Overlap Expenditure column has inconsistent currency/unit header and duplicates preceding page.'
  # Main 1877 rows 1844-1846 expand repeated text into too many cells.
  texts=' '.join(' '.join(p.get('text',[])) for p in ctx)
  common_note=bool(re.search('money figures.*(?:pounds sterling|sterling)',texts,re.I))
  from89=bool(re.search(r'(?:from|for) 1889(?:.{0,30})?(?:shown in rupees|it is shown in rupees)',texts,re.I)) or key in ['1892','1893'] and 'shown in rupees' in texts
  # Header Rs markers can be in a separate row; track them by literal column.
  currency={j:('£' if '£' in h else 'Rs.' if 'Rs.' in h else None) for j,h in enumerate(hs)}
  currency_row={}
  for i,r in enumerate(rs):
   if i<t['header_rows']:continue
   if len(r)!=t['n_cols']:
    self.skip(t,f'source row {i+1}','Ragged parsed row; alignment unsafe.',sum(bool(re.search(r'\d',c)) for c in r));continue
   y=r[yc].strip()
   marker=any(re.fullmatch(r'Rs\.?',c.strip()) for c in r)
   for j,c in enumerate(r):
    if re.fullmatch('£\\.?',c.strip()):currency[j]='£';currency_row[j]=i+1
    if re.fullmatch(r'Rs\.?',c.strip()):currency[j]='Rs.';currency_row[j]=i+1
   if marker and not YEAR.fullmatch(y):continue
   if not YEAR.fullmatch(y):
    if any(re.search(r'\d',c) for c in r):self.skip(t,f'source row {i+1}',f'Missing or non-plain data-year label {r[yc]!r}; no year inferred.',sum(bool(re.search(r'\d',c)) for j,c in enumerate(r) if j!=yc))
    continue
   # Skip the whole row for duplicated/out-of-order year labels. Keep genuinely different year values untouched.
   same=[k for k,rr in enumerate(rs) if len(rr)>yc and rr[yc].strip()==y]
   if len(same)>1:
    self.skip(t,f'source row {i+1}, data_year {y}','Duplicate data-year label in same table; no correction or reassignment.',sum(bool(re.search(r'\d',c)) for j,c in enumerate(r) if j!=yc));continue
   if main and key=='1877' and y in ['1844','1845','1846']:
    self.skip(t,f'source row {i+1}','Expanded repeated-figure text shifts subsequent columns.',sum(bool(re.search(r'\d',c)) for j,c in enumerate(r) if j!=yc));continue
   unsafe_from=None
   if main and any('repeated' in c.lower() for c in r[7:]):
    unsafe_from=min(j for j,c in enumerate(r) if j>=7 and 'repeated' in c.lower())
   if main and any(j>=14 and re.search(r'\d',c) and not hs[j] for j,c in enumerate(r)):
    unsafe_from=min(unsafe_from if unsafe_from is not None else 12,12)
   for j,c in enumerate(r):
    if j==yc or j in yearcols or not c.strip() or MISSING.fullmatch(c.strip()) or UNIT.fullmatch(c.strip()):continue
    if unsafe_from is not None and j>=unsafe_from:
     self.skip(t,f'source row {i+1}, column {j+1}','Expanded repeated-text span or numeric spill into unlabelled trailing columns displaces this row segment. Earlier columns retained; no values reassigned.',1);continue
    if (key=='1899' and main and 1882<=int(y[:4])<=1888 and 2<=j<=6) or (key=='1910' and main and int(y[:4])<=1833 and 9<=j<=11):
     self.skip(t,f'source row {i+1}, column {j+1}','Confirmed horizontal displacement in this row block; values belong under adjacent headers. No reassignment made.',1);continue
    if j in blocked:
     self.skip(t,f'source row {i+1}, column {j+1}',blocked[j],1);continue
    m=maps[j]
    if m is None:
     self.skip(t,f'source row {i+1}, column {j+1}, literal {c!r}','Empty, corrupted, or ambiguous column header; no series assigned.',1);continue
    series,unit=m;note=''
    if unit=='money':
     yr=int(y[:4])
     if re.match(r'Rs\.?\s*\d',c.strip()):currency[j]='Rs.';currency_row[j]=i+1
     if re.match(r'£\s*\d',c.strip()):currency[j]='£';currency_row[j]=i+1
     cur=currency[j]
     if common_note:
      if key=='1891' and yr>=1889:
       self.skip(t,f'source row {i+1}, column {j+1}','Currency note conflicts with apparent rupee figures; no currency inferred.',1);continue
      if from89:
       if key in ['1892','1893'] and yr>1890 and cur!='Rs.':
        self.skip(t,f'source row {i+1}, column {j+1}','Local note explicitly states rupees only for 1889 and 1890; later row has no independent currency marker.',1);continue
       cur='Rs.' if yr>=1889 else '£'
      else:cur='£'
      note='currency from local printed money-figures note; publisher conversions retained without further conversion'
     if not cur:
      self.skip(t,f'source row {i+1}, column {j+1}','Currency absent from parsed column and local notes; cannot safely align money series.',1);continue
     if not common_note and int(key[:4])>=1889 and yr>=1889 and cur!='Rs.':
      self.skip(t,f'source row {i+1}, column {j+1}','Later money row lacks an explicit currency change marker or local explanatory note; stale sterling header cannot establish unit.',1);continue
     if not common_note:note=f'currency {cur} from literal marker at source row {currency_row[j]}' if j in currency_row else f'currency {cur} from printed column header'
     unit=cur;series+='_'+('gbp' if cur=='£' else 'rupees')
    if y=='1910-11':note+='; printed fiscal period, January 1910 to June 1911 (18 months)'
    if series in ['population','births','deaths','marriages','schools','scholars','cultivated_area_acres']:note+='; historical estimates/coverage caveats: see local page_context.json'
    self.emit(t,i,j,y,hs[j],series,unit,c,note.strip('; '))
 def abridged(self,t,chosen):
  key=t['_key'];rs=t['rows']
  # Only directly labelled year columns, never years borrowed across a differently parsed page.
  yrrow=next((r for r in rs[:3] if sum(bool(re.fullmatch(r'(?:18|19)\d\d\.',c.strip())) for c in r)>=4),None)
  if yrrow is None:
   self.skip(t,'entire abridged continuation','No year header on this parsed page; cannot safely carry year positions across changing column layouts.',sum(bool(re.search(r'\d',c)) for r in rs for c in r));return
  if key in ['1925','1926','1935']:
   self.skip(t,'entire abridged first table','Year headers/values shift, or multiple measures merged in cells; safe one-figure-to-one-header alignment unavailable.',sum(bool(re.search(r'\d',c)) for r in rs[2:] for c in r[1:]));return
  years={j:c.strip().rstrip('.') for j,c in enumerate(yrrow) if re.fullmatch(r'(?:18|19)\d\d\.',c.strip())}
  section='';flow='';sub='';base_headers=headers(t)
  for i,r in enumerate(rs):
   if i<t['header_rows']:continue
   if key=='1929' and i in [19,20,21,22]:
    self.skip(t,f'source row {i+1}','Revenue group labels are vertically displaced from the Non-Taxation, Taxation and Total values; no reassignment made.',sum(bool(re.search(r'\d',c)) for c in r[1:]));continue
   label=r[0].strip() if r else ''
   if not label:continue
   # Group headings repeat across span-expanded cells.
   if label.endswith((':','{','§')) or label in ['Commerce, Foreign :','Finance : †','Population :','Land Sales :','Revenue :']:
    
    if any(re.search(r'\d',c) for c in r[1:]):self.skip(t,f'source row {i+1}','Numeric cells occur on a group-heading row; measure alignment is unsafe.',sum(bool(re.search(r'\d',c)) for c in r[1:]))
    section=label;sub='';flow='' if 'commerce' not in label.lower() else flow;continue
   low=label.lower();series=None;unit='';full=label
   prefix=section+' / ' if section else ''
   if 'exports' in low and 'total value' in low:flow='exports';series='exports_value';unit='Rs.'
   elif 'imports' in low and 'total value' in low:flow='imports';series='imports_value';unit='Rs.'
   elif re.match(r'(?:do\.|d\.)',low) and flow:
    if 'united kingdom' in low:series=flow+'_uk_value'
    elif 'other british' in low:series=flow+'_other_british_possessions_value'
    elif 'foreign countries' in low:series=flow+'_foreign_countries_value'
    elif 'ceylon produce' in low:series='exports_domestic_value'
    elif 'excluding specie' in low:series='exports_foreign_produce_excluding_specie_value'
    elif 'specie' in low:series='exports_specie_value'
    unit='Rs.';prefix=section+' / '+flow.title()+' / '
   elif 'expenditure by government' in low:series='education_expenditure';unit='Rs.'
   elif low.startswith('expenditure'):series='expenditure';unit='Rs.'
   elif 'non-taxation' in low:series='revenue_non_taxation';unit='Rs.';sub='revenue'
   elif 'taxation' in low:series='revenue_taxation';unit='Rs.'
   elif ('total' in low and 'revenue' in (section+' '+label+' '+sub).lower()):series='revenue';unit='Rs.'
   elif 'sterling' in low:series='public_debt';unit='£'
   elif 'rupee' in low:series='public_debt';unit='Rs.'
   elif 'excluding military' in low:series='population_excluding_military_shipping';unit='No.'
   elif 'military and shipping' in low:series='military_and_shipping';unit='No.'
   elif low.startswith('pupils'):series='scholars';unit='No.'
   elif low.startswith('schools'):series='schools';unit='No.'
   elif low.startswith('teachers'):series='teachers';unit='No.'
   elif 'extent sold' in low:series='land_sales_acres';unit='Acres.'
   elif 'amount realized' in low:series='land_sales_amount';unit='Rs.'
   elif 'extent leased' in low:series='land_leased_acres';unit='Acres.'
   elif 'premia realized' in low:series='land_leasing_premia';unit='Rs.'
   elif 'area' in low and 'square miles' in low:series='area_square_miles';unit='Square miles'
   if not series:
    if any(re.search(r'\d',c) for c in r[1:]):self.skip(t,f'source row {i+1}',f'Unmapped or displaced abridged measure {label!r}.',sum(bool(re.search(r'\d',r[j])) for j in years if j<len(r)))
    continue
   # No visible currency marker: keep separate rather than presume rupees.
   if unit=='Rs.' and not any('Rs' in c for c in r[:min(years)]):
    if 'rupee' not in low:
     self.skip(t,f'source row {i+1}',f'Currency not printed in parsed measure {label!r}; no unit inferred.',sum(bool(re.search(r'\d',r[j])) for j in years if j<len(r)));continue
   if unit in ['£','Rs.']:series+='_'+('gbp' if unit=='£' else 'rupees')
   for j,y in years.items():
    if j>=len(r):continue
    # The complete measure hierarchy is row-oriented in this layout.
    h=prefix+label
    if j>1 and r[1] and not re.search(r'\d',r[1]) and r[1]!=label and r[1] not in ['..','—']:h+=' / '+r[1]
    self.emit(t,i,j,y,h,series,unit,r[j],'abridged table transposed; year header '+y+'.; printed period/coverage may differ from full annual series; see page_context.json')
 def run(self):
  for key in self.keys:self.load(key)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--pilot',action='store_true');args=parser.parse_args()
 keys=[p.name.split('.')[0] for p in sorted((ROOT/'tables').glob('*.jsonl.gz'))]
 order=['1896','1871','1911']+[k for k in keys if k not in ['1896','1871','1911']]
 if args.pilot:order=order[:3]
 e=Extraction(order);e.run()
 (WORK/'raw_extraction.json').write_text(json.dumps(e.rows,ensure_ascii=False))
 (WORK/'raw_skips.json').write_text(json.dumps(e.skips,ensure_ascii=False))
 (WORK/'page_context.json').write_text(json.dumps(e.context,ensure_ascii=False,indent=1))
 (WORK/'counts.json').write_text(json.dumps({k:dict(v) for k,v in e.count.items()},indent=1))
 (WORK/'used_tables.json').write_text(json.dumps({k:sorted(v) for k,v in e.used.items()},indent=1))
 print('Volumes processed:',len(order),'Figures:',len(e.rows),'Skip records:',len(e.skips))
 for k in order:print(k,len(e.used[k]),dict(e.count[k]))
