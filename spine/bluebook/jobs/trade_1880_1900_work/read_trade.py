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
UNIT_PATTERN=r'(?:cwts?\.?|cwt\.?|lbs?\.?|pounds?|No\.?|Nos\.?|numbers?|gallons?\.?|gals?\.?|gal\.?|gills?\.?|gil\.?|pkgs?\.?|pckgs?\.?|packages?\.?|parcels?\.?|pcls?\.?|pcl\.?|cases?\.?|casks?\.?|bags?\.?|bottles?\.?|boxes?\.?|bales?\.?|bundles?\.?|bushels?\.?|bus\.?|bush\.?|yds?\.?|yards?\.?|doz(?:en)?\.?\s+pairs?\.?|dozen\.?|doz\.?|pairs?\.?|sets?\.?|pieces?\.?|pcs?\.?|pes\.?|tins?\.?|tons?\.?|tuns?\.?|oz\.?|ounces?\.?|feet\.?|ft\.?|loads?\.?|coils?\.?|rolls?\.?|sheets?\.?|reams?\.?|gross\.?|heads?\.?|skins?\.?|hides?\.?)'
UNIT=re.compile(r'(?<![A-Za-z])'+UNIT_PATTERN+r'(?![A-Za-z])',re.I)
GROUP=re.compile(r'^(Br(?:it(?:ish)?)?\.?\s*Col(?:onies|\.|\b)|Br\.\s*Cl\.|For(?:eign)?\.?\s*(?:Coun|Conn)(?:tries|\.|\b))\s*[—–\-:]*\s*',re.I)
COUNTRIES='United Kingdom|British India|India (excluding British)|Australia|Austria|Austria-Hungary|Belgium|Burmah|Burma|Canada|Cape of Good Hope|Cape Colony|Ceylon|China|Denmark|Egypt|France|French India|French Possessions in India|French Poss. in India|Germany|Gibraltar|Genoa|Holland|Hongkong|Hong Kong|Italy|Japan|Java|Maldiv Islands|Maldivé Islands|Maldives Islands|Maldive Islands|Maldivian Islands|Malta|Mauritius|Natal|New South Wales|New Zealand|Nicobar Islands|Norway|Persia|Portugal|Queensland|Russia|Russia in Europe|Russia in Asia|Singapore|South Australia|Spain|Straits Settlements|Sweden|Switzerland|Tasmania|Trieste|Triceste|Turkey|Turkey in Asia|Turkey in Europe|United States of America|U. States of America|U. S. of America|U.S. of America|West Indies|West Australia|Western Australia|Victoria|Zanzibar|Aden|America|Africa|Bengal|Bombay|Brazil|Cochin China|Chile|Chili|Colombia|Cuba|Finland|Formosa|Hamburg|Honolulu|Madagascar|Manila|Manilla|Mexico|Netherlands|Philippine Islands|Philippines|Peru|Reunion|Roumania|Sandwich Islands|Siam|Sumatra|Suez|Syria|United States|West Coast of Africa|Other British Possessions in Asia|Other British Possessions|Other Countries|Other Foreign Countries|Other Foreign Possessions|Other Foreign Possessions in Asia|Other British Possessions in Africa|Other British Possessions in America|Other British Colonies|British Guiana|Demerara|Trinidad|South America|South Africa|East Africa|Mozambique|Batavia|Bourbon|New Caledonia|Pacific Islands|Scotland|Ireland|England|Philippine Islands'.split('|')
def label(s):return re.sub(r'\s+',' ',re.sub(r'\.{2,}|…',' ',s)).strip(' .—–-:')
COUNTRIES += 'Dutch India|Arabia|Bremen|Port Said|Dutch Indies|Maldivo Islands|Maldivie Islands|India (excluding British Possess.)|Laccadive Islands|Dutch possessions in India|Dutch Poss. in India|Dutch Possessions in India|Greece|Maldivic Islands|French Poss. in China|U S of America|Odessa (Russia)|U S. of America|British East Africa|Maldivine Islands|India (excluding British Possessions)|Odessa, Russia|Portuguese Poss. in India|Russian Possessions in China|Portuguese India|French Possessions in China|British West Indies|Uruguay|Portuguese possessions in India|Maladive Islands|Russian Pos. in China|Maldivi Islands|West India Islands|Argentine Republic|Other Foreign Countries in Australasia|Nicobar Island|Maldivé Island|Russian possession in China|Dutch possession in India|Dutch Pos. in India|Russian Poss. in China|U. S of America|French Poss in China|Austria Hungary|America (U. S.)|Portuguese possessions in Africa|French possessions in Africa|Dutch Poss in India|Portuguese Possessions in India|Portuguese Possession in India|Odessa in Russia|Danzig|Africa|Hanover|Malacca|Malabar|Pondicherry|Sandwich Islands|Cochin|Cochin-China|Antwerp|Bordeaux|America, United States|British Ind|British North America'.split('|')
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
 s=s.strip()
 s=re.sub(r'^(?:(?:Rs?|cts?|c)\.?\s*)+', '',s,flags=re.I).strip()
 s=re.sub(r'(?<=\d)\s+(?:c|cts)\.?\s+(?=\d|[—–-])',' ',s,flags=re.I)
 s=re.sub(r'^—\s+(?:c|cts)\.?\s+—$','—',s,flags=re.I)
 s=re.sub(r'^(?:Do\.?|Declared)\s+(?=\d)','',s,flags=re.I)
 s=re.sub(r'\s+(?:Jan\.|January|March|Mch\.|Ord\.)\s.*$','',s,flags=re.I)
 return s.strip()

def money(cells):
 """Parse only split Rs/c, or an explicitly merged Rs c figure; never borrow from rate columns."""
 vals=[money_text(s) for s in cells]
 non=[s for s in vals if s not in EMPTY]
 if not non:return '',None,''
 if len(vals)==2 and all(re.fullmatch(r'\d[\d,]*',x or '!') for x in vals):
  if not re.fullmatch(r'\d{1,2}',vals[1]):raise ValueError('cents are not one or two digits')
  raw=' '.join(vals);v=Fraction(int(vals[0].replace(',',''))*100+int(vals[1]),100)
  return raw,v,'money cells joined'+('; explicit date/currency metadata separated from figure' if any(re.search(r'(?<=\d)\s+(?:Jan\.|January|March|Mch\.|Ord\.|c\.|cts\.)',x,re.I) for x in cells) else '')
 # A complete rupees/cents cell can stand beside blank/declared/price metadata.
 full=[]
 for x in vals:
  if re.fullmatch(r'\d[\d,]*\s+\d{1,2}',x):full.append(x)
  elif x not in EMPTY and not re.search(r'(?:Declared|Do\.?|Free|per|each|ad v|p\.|Rs\.|Re\.|cts?\.|value|Jan\.|Ord\.)',x,re.I):
   raise ValueError('incomplete or ambiguous rupees/cents: '+repr(vals))
 if not full and all(x in EMPTY or re.search(r'(?:Declared|Do\.?|Free|per|each|ad v|p\.|Jan\.|Ord\.|Rs\.|Re\.|cts?\.)',x,re.I) for x in vals):return '',None,''
 if len(full)!=1:raise ValueError('ambiguous merged money: '+repr(vals))
 a,b=full[0].split();return full[0],Fraction(int(a.replace(',',''))*100+int(b),100),'merged rupees and cents'+('; explicit date/currency metadata separated from figure' if any(re.search(r'(?<=\d)\s+(?:Jan\.|January|March|Mch\.|Ord\.|c\.|cts\.)',x,re.I) for x in cells) else '')

def unit_only(s):
 s=s.strip()
 return bool(UNIT.fullmatch(s)) or s in DITTO

def unit_key(u):
 x=re.sub(r'[^a-z]','',u.lower())
 for key,forms in [('cwt',{'cwt','cwts'}),('lb',{'lb','lbs','pound','pounds'}),('number',{'no','nos','number','numbers'}),('packages',{'pkg','pkgs','package','packages','pckg','pckgs'}),('cases',{'case','cases'}),('yards',{'yd','yds','yard','yards'}),('gallons',{'gal','gals','gallon','gallons'}),('gills',{'gil','gill','gills'}),('bushels',{'bus','bush','bushel','bushels'}),('dozen',{'doz','dozen'}),('pieces',{'pc','pcs','pes','piece','pieces'}),('parcels',{'pcl','pcls','parcel','parcels'}),('tons',{'ton','tons'})]:
  if x in forms:return key
 return x[:-1] if x.endswith('s') and not x.endswith('ss') else x

def quantity(cells,carried):
 """Return one observation per explicit unit, and the unit sequence for continuation rows."""
 vals=[s.strip() for s in cells]
 explicit=[m.group() for x in vals for m in UNIT.finditer(x)]
 note=[]
 # Repeated expanded spans must contain a complete figure or unit, not just equal component digits.
 if len(vals)>1 and len(set(vals))==1 and (UNIT.search(vals[0]) or len(vals[0].split())>=3):
  vals=vals[:1];explicit=[m.group() for m in UNIT.finditer(vals[0])];note.append('repeated spanned cell read once')
 units=explicit or list(carried)
 if not units:
  if all(x in EMPTY or x in DITTO for x in vals):return [],[]
  raise ValueError('quantity unit not explicitly established')
 if len(units)>1 and len({unit_key(u) for u in units})<len(units):
  # A single split cwt heading can be repeated by the span expansion.
  if all(unit_only(x) for x in vals if x):units=units[:1]
  else:raise ValueError('multiple figures with repeated unit within one measure')
 if not explicit:note.append('unit carried from above'+(' (ditto)' if any(d in vals or any(x.startswith(d+' ') or x.endswith(' '+d) for x in vals) for d in DITTO) else ''))
 stripped=[]
 for x in vals:
  x=UNIT.sub('',x).strip()
  for d in sorted(DITTO,key=len,reverse=True):
   if x==d:x='';break
   if x.startswith(d+' '):x=x[len(d):].strip();break
   if x.endswith(' '+d):x=x[:-len(d)].strip();break
  stripped.append(x)
 if all(x in EMPTY for x in stripped):return [],units
 def single(raw,u,extra):
  raw=raw.strip()
  if raw in EMPTY:return None
  nn=list(note)+extra
  if unit_key(u)=='cwt':
   parts=raw.split()
   if len(parts)!=3:raise ValueError('cwt quantity does not have cwt, qr and lb')
   c,q,l=map(number,parts)
   if c.denominator!=1 or q.denominator!=1 or not 0<=q<4 or not 0<=l<28:raise ValueError('invalid cwt-qr-lb components; no figure corrected')
   return raw,c+q/4+l/112,u,'; '.join(nn+['cwt qr lb'])
  v=number(raw)
  try:decimal(v)
  except ValueError:nn.append('nonterminating quantity rounded to 12 decimal places')
  return raw,v,u,'; '.join(nn)
 # Two different unit columns remain two printed figures, never added together.
 if len(units)==len(stripped) and len(units)>1:
  out=[single(x,u,['separate quantity unit column']) for x,u in zip(stripped,units)]
  return [x for x in out if x],units
 raw=' '.join(x for x in stripped if x)
 if len(units)==1:
  x=single(raw,units[0],['quantity cells joined'] if len(vals)>1 else [])
  return [x] if x else [],units
 # Merged multi-unit cells are readable only when their printed unit order determines a unique partition.
 tokens=raw.replace('&',' ').split()
 def partitions(at,j):
  if j==len(units):return [[]] if at==len(tokens) else []
  if at>=len(tokens):return []
  sizes=[1] if tokens[at] in EMPTY else [3] if unit_key(units[j])=='cwt' else [1,2]
  out=[]
  for size in sizes:
   if at+size>len(tokens):continue
   sub=' '.join(tokens[at:at+size])
   try:item=single(sub,units[j],['multiple units explicitly printed in quantity cell'])
   except (ValueError,ZeroDivisionError):continue
   for rest in partitions(at+size,j+1):out.append(([item] if item else [])+rest)
  return out
 options=partitions(0,0)
 if len(options)!=1:raise ValueError('merged multiple-unit quantity cannot be partitioned uniquely')
 return options[0],units

def flow_of(t):
 if not t['rows'] or not re.fullmatch(r'[•* ]*articles?[.,:]?',t['rows'][0][0].strip(),re.I):return None
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
  home=[i for i,s in enumerate(h0) if 'home consumption' in s.lower().replace('-',' ')]
  val=[i for i,s in enumerate(h0) if 'value in' in s.lower()]
  gross=[i for i,s in enumerate(h0) if 'gross amount received' in s.lower()]
  duty=gross or [i for i,s in enumerate(h0) if s.lower().startswith('duty') and 'rate' not in s.lower()]
  if not duty:
   gross1=[i for i,s in enumerate(h1) if 'gross amount received' in s.lower()]
   if len(gross1)==1 and gross1[0]+1<len(h1) and 'rate' in h1[gross1[0]+1].lower():duty=[gross1[0],gross1[0]+1]
  if not q or not home or len(val)!=2 or len(duty)!=2 or q[0]!=2 or max(home)+1!=val[0] or not all('average price' in h0[j].lower() for j in range(val[-1]+1,duty[0])):
   raise ValueError('import header does not establish contiguous quantity/value/duty columns')
  return [('quantity_total',q),('quantity_home_consumption',home),('value_total_rs',val),('duty_rs',duty)]
 qinds=[i for i,s in enumerate(h0) if 'quantit' in s.lower()]
 vinds=[i for i,s in enumerate(h0) if 'value in' in s.lower()]
 if not qinds or not vinds or qinds[0]!=2 or max(qinds)+1!=min(vinds):raise ValueError('export header quantity/value boundary is ambiguous')
 out=[]
 for prefix,inds in [('quantity',qinds),('value',vinds)]:
  labels=[]
  keep=[]
  for i in inds:
   s=h1[i].lower()
   # Third header row may supply the total missing from a spanned second header.
   if len(t['rows'])>2 and re.fullmatch(r'total\.?',t['rows'][2][i].strip(),re.I):s='total'
   if 'british' in s or 'foreign' in s:m='other_produce'
   elif 'produce' in s and ('colony' in s or 'ceylon' in s):m='ceylon_produce'
   elif re.fullmatch(r'total\.?',s.strip()):m='total'
   else:
    metadata=any(re.search(r'(?:Royalty|Duty|Tea Fund)',r[i],re.I) for r in t['rows'][:min(len(t['rows']),int(t.get('header_rows') or 2)+2)])
    blank=not any(re.search(r'\d',r[i]) for r in t['rows'][int(t.get('header_rows') or 2):])
    if prefix=='value' and (metadata or blank or not s.strip() or 'average' in s):continue
    raise ValueError('export subheader does not identify measure at column '+str(i))
   labels.append(m);keep.append(i)
  inds=keep
  for ids in runs(inds):
   start=0
   while start<len(ids):
    end=start+1
    while end<len(ids) and labels[inds.index(ids[end])]==labels[inds.index(ids[start])]:end+=1
    name=prefix+'_'+labels[inds.index(ids[start])]+('_rs' if prefix=='value' else '')
    out.append((name,ids[start:end]));start=end
  names=[n for n,_ in out if n.startswith(prefix)]
  if len(names)!=len(set(names)):raise ValueError('noncontiguous duplicate export measure')
 if not any(n=='value_total_rs' for n,_ in out):
  extras=[i for i,x in enumerate(h1) if i>max(vinds) and re.fullmatch(r'total\.?',x.strip(),re.I)]
  for ids in runs(extras):
   if len(ids)==1:
    j=ids[0]
    for rr in t['rows'][2:int(t.get('header_rows') or 2)+1]:
     if j>0 and re.fullmatch(r'Rs\.?',rr[j-1],re.I) and re.fullmatch(r'(?:c|cts)\.?',rr[j],re.I):ids=[j-1,j];break
     if j+1<len(rr) and re.fullmatch(r'Rs\.?',rr[j],re.I) and re.fullmatch(r'(?:c|cts)\.?',rr[j+1],re.I):ids=[j,j+1];break
   out.append(('value_total_rs',ids))
 return out

def import_row_schema(r):
 """An explicit mirrored pair of quantity-unit blocks anchors a changed in-page layout."""
 norm=lambda x:tuple(unit_key(m.group()) for m in UNIT.finditer(x))
 options=[]
 for k in range(1,5):
  end=2+2*k
  if end+2>len(r):continue
  left=[norm(x) for x in r[2:2+k]];right=[norm(x) for x in r[2+k:end]]
  if not any(left) or left!=right or not left[0]:continue
  if norm(r[end]):continue
  # An unlabeled second component is legitimate only for a split cwt, not an unknown composite.
  if any(not x for x in left) and not (k==2 and left[0]==('cwt',) and not left[1]):continue
  q=list(range(2,2+k));home=list(range(2+k,end));val=[end,end+1]
  duty=list(range(end+2,min(end+4,len(r))))
  result=[('quantity_total',q),('quantity_home_consumption',home),('value_total_rs',val)]
  if duty:result.append(('duty_rs',duty))
  options.append(result)
 return options[0] if len(options)==1 else None

class Reader:
 def __init__(self,key):
  self.key=key;self.rows=[];self.skips=[];self.articles=[];self.layouts=[];self.flow=None;self.cl='';self.gr='';self.cur=None;self.cg='';self.units={};self.heading_units={};self.last_leaf='';self.heading_source=None
 def skip(self,t,i,r,why):
  self.skips.append([t['id'],i,json.dumps(r,ensure_ascii=False),why])
  if self.cur:self.cur['skips']+=1
 def start(self,a,t,i):
  if self.cur and a==self.cur['article'] and not self.cur['closed'] and label(self.cl)==label(self.cur['class']) and label(self.gr)==label(self.cur['group']):return
  self.cur={'article':a,'class':self.cl,'group':self.gr,'start':t['id'],'start_row':i,'flow':self.flow,'sums':collections.defaultdict(Fraction),'totals':[],'countries':0,'source_countries':0,'skips':0,'closed':False,'units':{}}
  self.articles.append(self.cur);self.units=dict(self.heading_units);self.cg='';self.heading_source=None
 def heading(self,s):
  s=s.strip()
  numbered=re.match(r'^([IVXL]+[.\s—–-]*)\s*(\(\d+\).*)$',s)
  if numbered:self.cl=numbered[1].strip();self.gr=numbered[2].strip();return
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
   self.layouts.append({'table_id':t['id'],'flow':flow,'n_cols':t['n_cols'],'schema':sc,'error':scherr,'in_page_changes':[]})
   layout_origin=None
   for i,original in enumerate(t['rows']):
    r=[s.strip() for s in original]
    if not r:continue
    if re.fullmatch(r'[•* ]*articles?[.,:]?',r[0],re.I) and ('countries' in ' '.join(r[:3]).lower()):
     # Unit-only third headers still establish quantity units.
     for m,idx in sc:
      if m.startswith('quantity'):
       us=[r[j] for j in idx if UNIT.fullmatch(r[j])]
       if us:self.units[m]=us if len({unit_key(u) for u in us})>1 else us[:1];self.heading_units[m]=list(self.units[m])
     header_us=[u for m,idx in sc if m.startswith('quantity') for j in idx for u in [r[j]] if UNIT.fullmatch(u)]
     if header_us and len({u.lower().rstrip('.') for u in header_us})==1:
      for m,idx in sc:
       if m.startswith('quantity'):self.units.setdefault(m,[header_us[0]]);self.heading_units.setdefault(m,[header_us[0]])
     continue
    non=[x for x in r if x and x not in EMPTY]
    if not non:continue
    if len(set(non))==1 and len(non)>2 and re.search(r'[A-Za-z]',non[0]):self.heading(non[0]);continue
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
      if r[-1] not in EMPTY:
       self.skip(t,i,original,'country in article column but trailing cell is occupied; column shift is not safe');continue
      r=['']+r[:-1];notes.append('missing article cell restored; country anchored at source column 0')
    a,c=r[:2]
    if flow=='import':
     explicit_schema=import_row_schema(r)
     if explicit_schema and explicit_schema!=sc and (scherr or explicit_schema[:3]!=sc[:3]):
      if any('average price' in x.lower() for x in t['rows'][0]):
       scherr='changed quantity layout across separate average-price columns cannot be assigned safely'
      else:
       self.layouts[-1]['in_page_changes'].append({'source_row':i,'schema':explicit_schema})
       sc=explicit_schema;scherr=None;layout_origin=i
    if layout_origin is not None:notes.append('in-page column layout anchored by explicitly mirrored quantity units on source row '+str(layout_origin))
    # A whole-row heading can also occupy just its first cell, with units/currency beside it.
    active=[j for _,idx in sc for j in idx] if sc else list(range(2,len(r)))
    if flow=='export':
     active=sorted(set(active)|{j for j,x in enumerate(t['rows'][0]) if ('value in' in x.lower() or 'quantit' in x.lower()) and 'average' not in t['rows'][1][j].lower() and not any(re.search(r'(?:Royalty|Duty|Tea Fund)',rr[j],re.I) for rr in t['rows'][:min(len(t['rows']),int(t.get('header_rows') or 2)+2)])})
    def figureish(x):
     return bool(re.search(r'\d',x)) and not re.search(r'(?:per|each|p\.\s|ad v|Jan\.|Ord\.|Free|Declared)',x,re.I)
    has_numeric=any(figureish(r[j]) for j in active)
    unitrow=any(unit_only(x) for x in r[2:]) and not has_numeric
    bareclass=bool(re.fullmatch(r'(?:Articles of food and drink|Animals, living(?:, for food)?|Raw Materials|Manufactured Articles)\s*:?',a,re.I))
    if a and (not c or bareclass) and (not has_numeric or unitrow) and (a.endswith((':','：')) or bareclass or (':' not in a and re.match(r'^[IVXL]+[.—–]',a,re.I))):
     self.heading(a)
     for m,idx in sc:
      if m.startswith('quantity'):
       us=[r[j] for j in idx if UNIT.fullmatch(r[j])]
       if us:self.units[m]=us if len({unit_key(u) for u in us})>1 else us[:1];self.heading_units[m]=list(self.units[m])
     if bareclass and GROUP.match(c):self.cg=c
     if not has_numeric or unitrow:continue
    if a:
     a=self.article_label(a)
     if a and a not in EMPTY:
      # Repeated source cells are not new articles, even on the total row.
      if not self.cur or a!=self.cur['article'] or label(self.cl)!=label(self.cur['class']) or label(self.gr)!=label(self.cur['group']):
       self.start(a,t,i);self.heading_source=(t['id'],i) if not has_numeric else None
      self.last_leaf=a
    if any(r[j].lstrip().startswith('&') for m,idx in sc if m.startswith('quantity') for j in idx):
     self.skip(t,i,original,'supplementary quantity beginning with &: association with preceding printed row is ambiguous');continue
    row_us=[u.group() for m,idx in sc if m.startswith('quantity') for j in idx for u in UNIT.finditer(r[j])]
    if row_us and len({u.lower().rstrip('.') for u in row_us})==1:
     for m,idx in sc:
      if m.startswith('quantity') and m not in self.units:self.units[m]=[row_us[0]];notes.append('shared quantity unit explicitly printed in the row')
    for m,idx in sc:
     if m.startswith('quantity'):
      us=[u.group() for j in idx for u in UNIT.finditer(r[j])]
      if us:
       self.units[m]=us if len({unit_key(u) for u in us})>1 else us[:1]
    grouptext=re.sub(r'^(?:\.{2,}|…)\s*','',c)
    g=GROUP.match(grouptext)
    if g:
     self.cg=grouptext[:g.end()].strip(' —–-:')
     c=label(grouptext[g.end():])
     if not c and has_numeric and not unitrow:
      self.skip(t,i,original,'figures on a country-group heading; specific country/total cannot be assigned');continue
    if c and country(c) and label(c).casefold()=='united kingdom':self.cg=''
    if not has_numeric or unitrow:
     for m,idx in sc:
      if m.startswith('quantity'):
       us=[r[j] for j in idx if UNIT.fullmatch(r[j])]
       if us:
        self.units[m]=us if len({unit_key(u) for u in us})>1 else us[:1]
        if not a and not c and i<=int(t.get('header_rows') or 2)+1:self.heading_units[m]=list(self.units[m])
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
    if kind=='country':self.cur['source_countries']+=1
    if kind=='article_total' and not self.cur['source_countries']:
     self.skip(t,i,original,'unlabelled figures without preceding readable country figures; country versus total ambiguous');self.cur['closed']=True;continue
    if self.heading_source and self.heading_source!=(t['id'],i):notes.append('article heading on row above: '+self.heading_source[0]+' row '+str(self.heading_source[1]))
    try:
     vals=[];used=set()
     for m,idx in sc:
      cells=[r[j] for j in idx];used.update(idx)
      if m.startswith('quantity'):
       observations,us=quantity(cells,self.units.get(m,[]))
       if us:self.units[m]=us
       for raw,v,u,n in observations:vals.append((m,raw,v,u,n))
       continue
      else:
       if flow=='export' and len(idx)==2 and cells[0] in EMPTY and re.fullmatch(r'\d[\d,]*\s+\d{1,2}',money_text(cells[1])) and not any(nm=='value_total_rs' for nm,_ in sc):raise ValueError('merged export money in cents column; other produce versus total ambiguous')
       raw,v,n=money(cells);u=''
      vals.append((m,raw,v,u,n))
     # Export columns outside the schema are only average/rate/duty. If header says value/quantity,
     # it cannot be silently discarded. Import columns after duty are known rates.
     if flow=='export':
      for j in range(2,len(r)):
       if j not in used and re.search(r'\d',r[j]):
        if 'quantit' in t['rows'][0][j].lower():raise ValueError('unmapped export quantity column')
        if 'value in' in t['rows'][0][j].lower():
         known_meta='average' in t['rows'][1][j].lower() or any(re.search(r'(?:Royalty|Duty|Tea Fund)',rr[j],re.I) for rr in t['rows'][:min(len(t['rows']),int(t.get('header_rows') or 2)+2)])
         if not known_meta:raise ValueError('figure in unlabeled export value column; assignment ambiguous')
     if not any(v is not None for _,_,v,_,_ in vals):raise ValueError('no readable printed figures')
    except ValueError as e:
     self.skip(t,i,original,str(e))
     # Still end an unambiguous labelled/blank total; never leak its article into the next rows.
     if kind=='article_total':self.cur['closed']=True
     continue
    if kind=='country':self.cur['countries']+=1
    else:
     self.cur['closed']=True
     self.cur['total_location']=(t['id'],i)
     self.cur['total_map']={}
     for m,idx in sc:
      us=self.units.get(m,[]) if m.startswith('quantity') else ['']
      for u in us:self.cur['total_map'][(m,unit_key(u))]=Fraction(0)
    for m,raw,v,u,n in vals:
     if v is None:continue
     isnote=['source row '+str(i)]+notes+([n] if n else [])
     value=decimal(v,2 if m.endswith('_rs') else 4 if 'cwt qr lb' in n else 12 if 'nonterminating quantity' in n else None)
     self.rows.append([t['id'],self.key,t['pdf_page'],t.get('printed_page') or '',flow,self.cl,self.gr,self.cur['article'],self.cg if kind=='country' else '',label(c) if kind=='country' else '',u,m,raw,value,kind,'; '.join(dict.fromkeys(isnote))])
     dim=unit_key(u)
     # Exact checks use pounds for weights, cents for money, original units otherwise.
     exact=v*112 if dim=='cwt' else v*100 if m.endswith('_rs') else v
     key=(m,dim)
     if kind=='country':self.cur['sums'][key]+=exact
     else:
      self.cur['totals'].append((key,exact,t['id'],i));self.cur['total_map'][key]=exact
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
    totals=a['total_map'];sums=a['sums'];t,i=a['total_location']
    measures=sorted({m for m,u in totals}|{m for m,u in sums})
    for m in measures:
     dims=sorted({u for mm,u in totals if mm==m}|{u for mm,u in sums if mm==m})
     tv={u:totals.get((m,u),Fraction(0)) for u in dims}
     sv={u:sums.get((m,u),Fraction(0)) for u in dims}
     dv={u:tv[u]-sv[u] for u in dims}
     if any(dv.values()):
      bad=True
      def show_number(x):
       try:return decimal(x)
       except ValueError:return str(x)
      def show(vector):
       if len(dims)==1:return show_number(vector[dims[0]])
       return json.dumps({('lb' if u=='cwt' else 'cents' if m.endswith('_rs') else u):show_number(vector[u]) for u in dims},ensure_ascii=False,sort_keys=True)
      checks.append([rr.key,flow,a['article'],a['start'],t,i,m,show(tv),show(sv),show(dv)])
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
