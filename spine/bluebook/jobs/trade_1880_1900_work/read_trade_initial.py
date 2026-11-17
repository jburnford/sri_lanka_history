"""Conservative, offline reader for the pre-1901 article/country ledgers.
Only source-grounded label repairs are allowed; no arithmetic-based repairs.
Run with the supplied Python, optionally with a list of volume keys.
"""
import collections,csv,gzip,io,json,re,sys
from pathlib import Path
from fractions import Fraction
from decimal import Decimal,localcontext
ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'jobs/trade_1880_1900_work'
KEYS='1896 1880 1881 1882 1883 1885 1886 1887 1889b 1890 1891 1892 1893 1894 1897 1898 1899 1900'.split()
FIELDS='table_id year_volume pdf_page printed_page flow class_as_printed group_as_printed article_as_printed country_group_as_printed country_as_printed unit_as_printed measure value_as_printed value row_kind note'.split()
SKIPFIELDS='table_id row_index cells reason'.split()
CHECKFIELDS='year_volume flow article_as_printed article_start_table total_table_id total_row_index measure printed_total country_sum difference'.split()
EMPTY={'','—','–','-','--','―','...','..','.','…','nil','Nil'}
DITTO={'"',"''",',,','„','”','“','〃','»','do.','Do.','do','Do'}
FRACS={'½':Fraction(1,2),'¼':Fraction(1,4),'¾':Fraction(3,4),'⅓':Fraction(1,3),'⅔':Fraction(2,3),'⅛':Fraction(1,8),'⅜':Fraction(3,8),'⅝':Fraction(5,8),'⅞':Fraction(7,8)}
UNIT_PATTERN=r'(?:cwts?\.?|cwt\.?|lbs?\.?|pounds?|No\.?|Nos\.?|numbers?|gallons?\.?|gals?\.?|gal\.?|gills?\.?|gil\.?|pkgs?\.?|pckgs?\.?|packages?\.?|parcels?\.?|pcls?\.?|pcl\.?|cases?\.?|casks?\.?|bags?\.?|bottles?\.?|boxes?\.?|bales?\.?|bundles?\.?|bushels?\.?|bus\.?|bush\.?|yds?\.?|yards?\.?|dozen\.?|doz\.?|pairs?\.?|sets?\.?|pieces?\.?|tons?\.?|tuns?\.?|oz\.?|ounces?\.?|feet\.?|ft\.?|loads?\.?|coils?\.?|rolls?\.?|sheets?\.?|reams?\.?|gross\.?|heads?\.?|skins?\.?|hides?\.?)'
UNIT=re.compile(r'(?<![A-Za-z])'+UNIT_PATTERN+r'(?![A-Za-z])',re.I)
GROUP=re.compile(r'^(Br(?:it(?:ish)?)?\.?\s*Col(?:onies|\.|\b)|Br\.\s*Cl\.|For(?:eign)?\.?\s*Coun(?:tries|\.|\b))\s*[—–\-:]*\s*',re.I)
COUNTRIES='United Kingdom|British India|India (excluding British)|Australia|Austria|Austria-Hungary|Belgium|Burmah|Burma|Canada|Cape of Good Hope|Cape Colony|Ceylon|China|Denmark|Egypt|France|French India|French Possessions in India|French Poss. in India|Germany|Gibraltar|Genoa|Holland|Hongkong|Hong Kong|Italy|Japan|Java|Maldiv Islands|Maldivé Islands|Maldives Islands|Maldive Islands|Maldivian Islands|Malta|Mauritius|Natal|New South Wales|New Zealand|Nicobar Islands|Norway|Persia|Portugal|Queensland|Russia|Russia in Europe|Russia in Asia|Singapore|South Australia|Spain|Straits Settlements|Sweden|Switzerland|Tasmania|Trieste|Triceste|Turkey|Turkey in Asia|Turkey in Europe|United States of America|U. States of America|U. S. of America|U.S. of America|West Indies|West Australia|Western Australia|Victoria|Zanzibar|Aden|America|Africa|Bengal|Bombay|Brazil|Cochin China|Chile|Chili|Colombia|Cuba|Finland|Formosa|Hamburg|Honolulu|Madagascar|Manila|Manilla|Mexico|Netherlands|Philippine Islands|Philippines|Peru|Reunion|Roumania|Sandwich Islands|Siam|Sumatra|Suez|Syria|United States|West Coast of Africa|Other British Possessions in Asia|Other British Possessions|Other Countries|Other Foreign Countries|Other Foreign Possessions|Other Foreign Possessions in Asia|Other British Possessions in Africa|Other British Possessions in America|Other British Colonies|British Guiana|Demerara|Trinidad|South America|South Africa|East Africa|Mozambique|Batavia|Bourbon|New Caledonia|Pacific Islands|Scotland|Ireland|England|Philippine Islands'.split('|')
def label(s):return re.sub(r'\s+',' ',re.sub(r'\.{2,}|…',' ',s)).strip(' .—–-:')
CN={label(s).casefold() for s in COUNTRIES}
def country(s):return label(s).casefold() in CN

def number(s):
 s=s.strip().replace(',','')
 if re.fullmatch(r'\d+(?:\.\d+)?',s):return Fraction(s)
 m=re.fullmatch(r'(\d*)(['+''.join(FRACS)+r'])',s)
 if m:return Fraction(m[1] or 0)+FRACS[m[2]]
 m=re.fullmatch(r'(\d*)\\frac\{(\d+)\}\{(\d+)\}',s)
 if m and int(m[3]):return Fraction(m[1] or 0)+Fraction(int(m[2]),int(m[3]))
 m=re.fullmatch(r'(\d+)\s+(\d+)/(\d+)',s)
 if m and int(m[3]) and int(m[2])<int(m[3]):return Fraction(int(m[1]))+Fraction(int(m[2]),int(m[3]))
 m=re.fullmatch(r'(\d+)/(\d+)',s)
 if m and int(m[2]) and int(m[1])<int(m[2]):return Fraction(int(m[1]),int(m[2]))
 raise ValueError('not an unambiguous number: '+repr(s))

def decimal(v,places=None):
 with localcontext() as ctx:
  ctx.prec=45
  d=Decimal(v.numerator)/Decimal(v.denominator)
  if places is not None:return f'{d:.{places}f}'
  # Only finite decimal quantities can be represented exactly under the output contract.
  den=v.denominator
  for p in (2,5):
   while den%p==0:den//=p
  if den!=1:raise ValueError('quantity has nonterminating decimal')
  return format(d,'f').rstrip('0').rstrip('.') if '.' in format(d,'f') else format(d,'f')

def money_text(s):
 return re.sub(r'^(?:(?:Rs?|cts?|c)\.?\s*)+', '',s.strip(),flags=re.I).strip()

def money(cells):
 """Parse only split Rs/c, or an explicitly merged Rs c figure; never borrow from rate columns."""
 vals=[money_text(s) for s in cells]
 non=[s for s in vals if s not in EMPTY]
 if not non:return '',None,''
 if len(vals)==2 and all(re.fullmatch(r'\d[\d,]*',x or '!') for x in vals):
  if not re.fullmatch(r'\d{1,2}',vals[1]):raise ValueError('cents are not one or two digits')
  raw=' '.join(vals);v=Fraction(int(vals[0].replace(',',''))*100+int(vals[1]),100)
  return raw,v,'money cells joined'
 # A complete rupees/cents cell can stand beside blank/declared/price metadata.
 full=[]
 for x in vals:
  if re.fullmatch(r'\d[\d,]*\s+\d{1,2}',x):full.append(x)
  elif x not in EMPTY and not re.search(r'(?:Declared|Do\.?|Free|per|each|ad v|p\.|Rs\.|Re\.|cts?\.|value|Jan\.|Ord\.)',x,re.I):
   raise ValueError('incomplete or ambiguous rupees/cents: '+repr(vals))
 if not full and all(x in EMPTY or re.search(r'(?:Declared|Do\.?|Free|per|each|ad v|p\.|Jan\.|Ord\.|Rs\.|Re\.|cts?\.)',x,re.I) for x in vals):return '',None,''
 if len(full)!=1:raise ValueError('ambiguous merged money: '+repr(vals))
 a,b=full[0].split();return full[0],Fraction(int(a.replace(',',''))*100+int(b),100),'merged rupees and cents'

def unit_only(s):
 s=s.strip()
 return bool(UNIT.fullmatch(s)) or s in DITTO

def quantity(cells,carried):
 vals=[s.strip() for s in cells]
 # Spanned cell repeats are collapsed, never added.
 note=[]
 if len(vals)>1 and len(set(vals))==1:
  vals=vals[:1];note.append('repeated spanned cell read once')
 units=[]
 for s in vals:
  units.extend(m.group() for m in UNIT.finditer(s))
 explicit=[u for u in units]
 norm=lambda x: re.sub(r'[^a-z]','',x.lower())
 if len(set(norm(u) for u in units))>1:raise ValueError('multiple quantity units in one measure')
 unit=units[0] if units else carried
 stripped=[]
 ditto=False
 for s in vals:
  s=UNIT.sub('',s).strip()
  for d in sorted(DITTO,key=len,reverse=True):
   if s==d:s='';ditto=True;break
   if s.startswith(d+' '):s=s[len(d):].strip();ditto=True;break
   if s.endswith(' '+d):s=s[:-len(d)].strip();ditto=True;break
  stripped.append(s)
 non=[s for s in stripped if s not in EMPTY]
 if not non:return '',None,unit,'; '.join(note)
 if not unit:raise ValueError('quantity unit not explicitly established')
 if not explicit:note.append('unit carried from above'+(' (ditto)' if ditto else ''))
 raw=' '.join(non)
 if len(vals)>1 and len(non)>1:note.append('quantity cells joined')
 if norm(unit) in {'cwt','cwts'}:
  parts=raw.split()
  if len(parts)!=3:raise ValueError('cwt quantity does not have cwt, qr and lb')
  c,q,l=map(number,parts)
  if c.denominator!=1 or q.denominator!=1 or not 0<=q<4 or not 0<=l<28:
   raise ValueError('invalid cwt-qr-lb components; no figure corrected')
  return raw,c+q/4+l/112,unit,'; '.join(note+['cwt qr lb'])
 v=number(raw)
 decimal(v)
 return raw,v,unit,'; '.join(note)

def flow_of(t):
 if not t['rows'] or not t['rows'][0][0].strip().lower().startswith('articles'):return None
 h=' '.join(t['rows'][0][:3]).lower()
 if 'countries whence imported' in h:return 'import'
 if 'countries to which exported' in h:return 'export'
 return None

def runs(indices):
 out=[]
 for i in indices:
  if out and i==out[-1][-1]+1:out[-1].append(i)
  else:out.append([i])
 return out

def schema(t,flow):
 h0=t['rows'][0];h1=t['rows'][1]
 if flow=='import':
  q=[i for i,s in enumerate(h0) if 'total quantit' in s.lower()]
  home=[i for i,s in enumerate(h0) if 'home consumption' in s.lower()]
  val=[i for i,s in enumerate(h0) if 'value in' in s.lower()]
  duty=[i for i,s in enumerate(h0) if s.lower().startswith('duty')]
  if not q or not home or len(val)!=2 or len(duty)!=2 or q[0]!=2 or max(home)+1!=val[0] or val[-1]+1!=duty[0]:
   raise ValueError('import header does not establish contiguous quantity/value/duty columns')
  return [('quantity_total',q),('quantity_home_consumption',home),('value_total_rs',val),('duty_rs',duty)]
 qinds=[i for i,s in enumerate(h0) if 'quantit' in s.lower()]
 vinds=[i for i,s in enumerate(h0) if 'value in' in s.lower()]
 if not qinds or not vinds or qinds[0]!=2 or max(qinds)+1!=min(vinds):raise ValueError('export header quantity/value boundary is ambiguous')
 out=[]
 for prefix,inds in [('quantity',qinds),('value',vinds)]:
  labels=[]
  for i in inds:
   s=h1[i].lower()
   # Third header row may supply the total missing from a spanned second header.
   if len(t['rows'])>2 and re.fullmatch(r'total\.?',t['rows'][2][i].strip(),re.I):s='total'
   if 'british' in s or 'foreign' in s:m='other_produce'
   elif 'produce' in s and ('colony' in s or 'ceylon' in s):m='ceylon_produce'
   elif re.fullmatch(r'total\.?',s.strip()):m='total'
   else:raise ValueError('export subheader does not identify measure at column '+str(i))
   labels.append(m)
  for ids in runs(inds):
   start=0
   while start<len(ids):
    end=start+1
    while end<len(ids) and labels[inds.index(ids[end])]==labels[inds.index(ids[start])]:end+=1
    name=prefix+'_'+labels[inds.index(ids[start])]+('_rs' if prefix=='value' else '')
    out.append((name,ids[start:end]));start=end
  names=[n for n,_ in out if n.startswith(prefix)]
  if len(names)!=len(set(names)):raise ValueError('noncontiguous duplicate export measure')
 return out

class Reader:
 def __init__(self,key):
  self.key=key;self.rows=[];self.skips=[];self.articles=[];self.layouts=[];self.flow=None;self.cl='';self.gr='';self.cur=None;self.cg='';self.units={};self.heading_units={};self.last_leaf='';self.heading_source=None
 def skip(self,t,i,r,why):
  self.skips.append([t['id'],i,json.dumps(r,ensure_ascii=False),why])
  if self.cur:self.cur['skips']+=1
 def start(self,a,t,i):
  if self.cur and a==self.cur['article'] and not self.cur['closed']:return
  self.cur={'article':a,'start':t['id'],'start_row':i,'flow':self.flow,'sums':collections.defaultdict(Fraction),'totals':[],'countries':0,'skips':0,'closed':False,'units':{}}
  self.articles.append(self.cur);self.units=dict(self.heading_units);self.cg='';self.heading_source=None
 def heading(self,s):
  s=s.strip()
  if re.match(r'^(?:[IVXL]+[.\s—–-]|Articles of food|Animals|Live Animals|Raw Materials|Manufactured Articles)',s,re.I):self.cl=s;self.gr=''
  else:self.gr=s
 def article_label(self,a):
  # Colon-delimited class/group prefixes are literal text, not reconstructed names.
  if ':' in a:
   pieces=a.split(':');prefix=':'.join(pieces[:-1]).strip()+':'
   tail=pieces[-1].strip()
   self.heading(prefix)
   return tail
  return a.strip()
 def read(self,tables):
  for t in tables:
   flow=flow_of(t)
   if not flow:continue
   if flow!=self.flow:
    self.flow=flow;self.cl='';self.gr='';self.cur=None;self.cg='';self.units={};self.heading_units={};self.last_leaf=''
   self.heading_units={}
   try:sc=schema(t,flow);scherr=None
   except ValueError as e:sc=[];scherr=str(e)
   self.layouts.append({'table_id':t['id'],'flow':flow,'n_cols':t['n_cols'],'schema':sc,'error':scherr})
   for i,original in enumerate(t['rows']):
    r=[s.strip() for s in original]
    if not r:continue
    if r[0].lower().startswith('articles.') and ('countries' in ' '.join(r[:3]).lower()):
     # Unit-only third headers still establish quantity units.
     for m,idx in sc:
      if m.startswith('quantity'):
       us=[r[j] for j in idx if UNIT.fullmatch(r[j])]
       if us and len(set(us))==1:self.units[m]=us[0];self.heading_units[m]=us[0]
     header_us=[u for m,idx in sc if m.startswith('quantity') for j in idx for u in [r[j]] if UNIT.fullmatch(u)]
     if header_us and len({u.lower().rstrip('.') for u in header_us})==1:
      for m,idx in sc:
       if m.startswith('quantity'):self.units.setdefault(m,header_us[0]);self.heading_units.setdefault(m,header_us[0])
     continue
    non=[x for x in r if x and x not in EMPTY]
    if not non:continue
    if len(set(non))==1 and len(non)>2 and not re.search(r'\d',non[0]):self.heading(non[0]);continue
    notes=[]
    # Label repairs require explicit, uniquely recognized country anchors.
    if len(r)>2 and country(r[2]) and r[1] and not country(r[1]) and not GROUP.match(r[1]):
     r=r[1:]+[''];notes.append('extra leading label cell removed; country anchored at source column 2')
    elif country(r[0]) or GROUP.match(r[0]):
     if country(r[1]) or GROUP.match(r[1]):
      self.skip(t,i,original,'multiple country/group labels in the two label columns');continue
     if r[1] and not re.search(r'\d',r[1]) and not UNIT.search(r[1]) and r[1] not in EMPTY:
      r=[r[1],r[0]]+r[2:];notes.append('article and country label cells exchanged')
     else:
      r=['']+r[:-1];notes.append('missing article cell restored; country anchored at source column 0')
    a,c=r[:2]
    # A whole-row heading can also occupy just its first cell, with units/currency beside it.
    active=[j for _,idx in sc for j in idx] if sc else list(range(2,len(r)))
    def figureish(x):
     return bool(re.search(r'\d',x)) and not re.search(r'(?:per|each|p\.\s|ad v|Jan\.|Ord\.|Free|Declared)',x,re.I)
    has_numeric=any(figureish(r[j]) for j in active)
    unitrow=any(unit_only(x) for x in r[2:]) and not any(re.search(r'\d',x) for x in r[2:6])
    if a and not c and (not has_numeric or unitrow) and (a.endswith((':','：')) or re.match(r'^(?:[IVXL]+[.—–]|Articles of food|Animals, living|Raw Materials|Manufactured Articles)',a,re.I)):
     self.heading(a)
     for m,idx in sc:
      if m.startswith('quantity'):
       us=[r[j] for j in idx if UNIT.fullmatch(r[j])]
       if us and len(set(us))==1:self.units[m]=us[0];self.heading_units[m]=us[0]
     if not has_numeric or unitrow:continue
    if a:
     a=self.article_label(a)
     if a and a not in EMPTY:
      # Repeated source cells are not new articles, even on the total row.
      if not self.cur or a!=self.cur['article']:
       self.start(a,t,i);self.heading_source=(t['id'],i) if not has_numeric else None
      self.last_leaf=a
    row_us=[u.group() for m,idx in sc if m.startswith('quantity') for j in idx for u in UNIT.finditer(r[j])]
    if row_us and len({u.lower().rstrip('.') for u in row_us})==1:
     for m,idx in sc:
      if m.startswith('quantity') and m not in self.units:self.units[m]=row_us[0];notes.append('shared quantity unit explicitly printed in the row')
    for m,idx in sc:
     if m.startswith('quantity'):
      us=[u.group() for j in idx for u in UNIT.finditer(r[j])]
      if us and len({u.lower().rstrip('.') for u in us})==1:self.units[m]=us[0]
    g=GROUP.match(c)
    if g:
     self.cg=c[:g.end()].strip(' —–-:')
     c=c[g.end():].strip()
     if not c and has_numeric and not unitrow:
      self.skip(t,i,original,'figures on a country-group heading; specific country/total cannot be assigned');continue
    if c and country(c) and label(c).casefold()=='united kingdom':self.cg=''
    if not has_numeric or unitrow:
     for m,idx in sc:
      if m.startswith('quantity'):
       us=[r[j] for j in idx if UNIT.fullmatch(r[j])]
       if us and len(set(us))==1:self.units[m]=us[0]
     # No figure rows are headings/context, never fabricated zero-valued observations.
     if c and not country(c) and not g and c not in EMPTY and not UNIT.search(c):
      self.skip(t,i,original,'unrecognized nonnumeric label/context row')
     continue
    if scherr:self.skip(t,i,original,scherr);continue
    if not self.cur or not self.cur['article']:
     self.skip(t,i,original,'no safely identified article');continue
    if c in EMPTY:c=''
    if c:
     if re.match(r'^total\b',c,re.I):kind='article_total'
     elif country(c):kind='country'
     else:
      self.skip(t,i,original,'country unreadable, multiple country rows merged, or shifted numeric label');continue
    else:kind='article_total'
    if self.cur['closed']:
     self.skip(t,i,original,'figures after the article total without a new article label');continue
    # Empty labels immediately following a country/unit heading can be either country or total.
    if kind=='article_total' and not self.cur['countries']:
     self.skip(t,i,original,'unlabelled figures without preceding readable country figures; country versus total ambiguous');self.cur['closed']=True;continue
    if self.heading_source and self.heading_source!=(t['id'],i):notes.append('article heading on row above: '+self.heading_source[0]+' row '+str(self.heading_source[1]))
    try:
     vals=[];used=set()
     for m,idx in sc:
      cells=[r[j] for j in idx];used.update(idx)
      if m.startswith('quantity'):
       raw,v,u,n=quantity(cells,self.units.get(m,''))
       if u:self.units[m]=u
      else:
       if flow=='export' and len(idx)==2 and cells[0] in EMPTY and re.fullmatch(r'\d[\d,]*\s+\d{1,2}',money_text(cells[1])) and not any(nm=='value_total_rs' for nm,_ in sc):raise ValueError('merged export money in cents column; other produce versus total ambiguous')
       raw,v,n=money(cells);u=''
      vals.append((m,raw,v,u,n))
     # Export columns outside the schema are only average/rate/duty. If header says value/quantity,
     # it cannot be silently discarded. Import columns after duty are known rates.
     if flow=='export':
      for j in range(2,len(r)):
       if j not in used and re.search(r'\d',r[j]) and j<len(t['rows'][0]) and ('value in' in t['rows'][0][j].lower() or 'quantit' in t['rows'][0][j].lower()):raise ValueError('unmapped export figure column')
     if not any(v is not None for _,_,v,_,_ in vals):raise ValueError('no readable printed figures')
    except ValueError as e:
     self.skip(t,i,original,str(e))
     # Still end an unambiguous labelled/blank total; never leak its article into the next rows.
     if kind=='article_total':self.cur['closed']=True
     continue
    if kind=='country':self.cur['countries']+=1
    else:self.cur['closed']=True
    for m,raw,v,u,n in vals:
     if v is None:continue
     isnote=['source row '+str(i)]+notes+([n] if n else [])
     value=decimal(v,2 if m.endswith('_rs') else 4 if 'cwt qr lb' in n else None)
     self.rows.append([t['id'],self.key,t['pdf_page'],t.get('printed_page') or '',flow,self.cl,self.gr,self.cur['article'],self.cg if kind=='country' else '',label(c) if kind=='country' else '',u,m,raw,value,kind,'; '.join(isnote)])
     dim='cwt' if 'cwt qr lb' in n else re.sub(r'[^a-z]','',u.lower())
     # Exact checks use pounds for weights, cents for money, original units otherwise.
     exact=v*112 if dim=='cwt' else v*100 if m.endswith('_rs') else v
     key=(m,dim)
     if kind=='country':self.cur['sums'][key]+=exact
     else:self.cur['totals'].append((key,exact,t['id'],i))
  return self

def write(path,header,rows):
 if str(path).endswith('.gz'):
  with path.open('wb') as out,gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0) as gz,io.TextIOWrapper(gz,encoding='utf-8',newline='') as f:
   w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(header);w.writerows(rows)
 else:
  with path.open('w',encoding='utf-8',newline='') as f:
   w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(header);w.writerows(rows)

def main():
 readers=[]
 for key in sys.argv[1:] or KEYS:
  ts=list(map(json.loads,gzip.open(ROOT/f'tables/{key}.jsonl.gz','rt')))
  rr=Reader(key).read(ts);readers.append(rr)
  with (WORK/f'layouts_{key}.json').open('w') as f:json.dump(rr.layouts,f,indent=2)
  write(WORK/f'skipped_{key}.tsv',SKIPFIELDS,rr.skips)
  print(key,'figures',len(rr.rows),'skipped',len(rr.skips),flush=True)
 rows=[x for rr in readers for x in rr.rows];skips=[x for rr in readers for x in rr.skips]
 checks=[];summary=[]
 for rr in readers:
  for flow in ['import','export']:
   arts=[a for a in rr.articles if a['flow']==flow and a['totals']]
   agree=0
   for a in arts:
    bad=False
    for (m,u),v,t,i in a['totals']:
     su=a['sums'][(m,u)]
     if v!=su:
      bad=True
      def show(x):
       try:return decimal(x)
       except ValueError:return str(x)
      checks.append([rr.key,flow,a['article'],a['start'],t,i,m,show(v),show(su),show(v-su)])
    if not bad and not a['skips']:agree+=1
   tids={x['table_id'] for x in rr.layouts if x['flow']==flow}
   summary.append([rr.key,flow,sum(x[4]==flow for x in rr.rows),len(arts),agree,sum(x[0] in tids for x in rr.skips)])
 write(ROOT/'extracted/trade_1880_1900.tsv.gz',FIELDS,rows)
 write(ROOT/'extracted/trade_1880_1900_skipped.tsv',SKIPFIELDS,skips)
 write(ROOT/'extracted/trade_1880_1900_checks.tsv',CHECKFIELDS,checks)
 write(WORK/'summary.tsv','year_volume flow figures_written articles_with_total articles_all_measures_agree rows_skipped'.split(),summary)
 with (WORK/'run_metadata.json').open('w') as f:json.dump({'volumes':[r.key for r in readers],'figures':len(rows),'skips':len(skips),'mismatches':len(checks)},f,indent=2)
 for row in summary:print('\t'.join(map(str,row)))
if __name__=='__main__':main()
