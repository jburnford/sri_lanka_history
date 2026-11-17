"""Independent re-parser of every output value; also checks source row provenance.
Does not import the extraction reader. Run after read_trade.py.
"""
import collections,csv,gzip,json,re
from decimal import Decimal,localcontext
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'jobs/trade_1880_1900_work'
UNICODE={'½':(1,2),'¼':(1,4),'¾':(3,4),'⅓':(1,3),'⅔':(2,3),'⅛':(1,8),'⅜':(3,8),'⅝':(5,8),'⅞':(7,8)}
def fraction(raw):
 s=raw.replace(',','').strip()
 if re.fullmatch(r'\d+(?:\.\d+)?',s):return Fraction(s)
 if s[-1:] in UNICODE:
  n,d=UNICODE[s[-1]]
  if not s[:-1] or s[:-1].isdigit():return Fraction(int(s[:-1] or '0'))+Fraction(n,d)
 m=re.fullmatch(r'(\d*)\\frac\{(\d+)\}\{(\d+)\}',s)
 if m:return Fraction(int(m[1] or '0'))+Fraction(int(m[2]),int(m[3]))
 m=re.fullmatch(r'(\d+)\s+(\d+)/(\d+)',s)
 if m:return Fraction(int(m[1]))+Fraction(int(m[2]),int(m[3]))
 m=re.fullmatch(r'(\d+)/(\d+)',s)
 if m and int(m[1])<int(m[2]):return Fraction(int(m[1]),int(m[2]))
 raise ValueError('cannot independently parse '+repr(raw))
def render(v,places):
 with localcontext() as ctx:
  ctx.prec=45
  d=Decimal(v.numerator)/Decimal(v.denominator)
  if places is not None:return f'{d:.{places}f}'
  return format(d,'f').rstrip('0').rstrip('.') if '.' in format(d,'f') else format(d,'f')
def main():
 rows=list(csv.DictReader(gzip.open(ROOT/'extracted/trade_1880_1900.tsv.gz','rt'),delimiter='\t'))
 keys={r['year_volume'] for r in rows};tables={}
 for k in keys:
  tables.update({t['id']:t for t in map(json.loads,gzip.open(ROOT/f'tables/{k}.jsonl.gz','rt'))})
 types=collections.Counter();errors=[];seen=set()
 for index,r in enumerate(rows,2):
  try:
   raw=r['value_as_printed'];v=r['value'];note=r['note']
   if not v:
    assert not re.search(r'\d',raw),'empty value has numeric text'
    types['no_figure']+=1;continue
   assert re.fullmatch(r'\d+(?:\.\d+)?',v),'value not plain unsigned decimal'
   if r['measure'].endswith('_rs'):
    rupees,cents=raw.split()
    assert re.fullmatch(r'\d{1,2}',cents)
    exact=Fraction(int(rupees.replace(',',''))*100+int(cents),100);places=2;types['money']+=1
   elif 'cwt qr lb' in note:
    cw,qr,lb=map(fraction,raw.split());exact=cw+qr/4+lb/112;places=4;types['cwt_qr_lb']+=1
   else:
    exact=fraction(raw);places=12 if 'nonterminating quantity' in note else None;types['other_quantity']+=1
   assert render(exact,places)==v,(raw,v,render(exact,places))
   m=re.match(r'source row (\d+)(?:;|$)',note);assert m,'missing zero-based source row'
   rowindex=int(m[1]);t=tables[r['table_id']];source=t['rows'][rowindex]
   assert str(t['pdf_page'])==r['pdf_page']
   assert (t.get('printed_page') or '')==r['printed_page']
   tokens=lambda s:re.findall(r'\d+|['+''.join(UNICODE)+']',s.replace(',',''))
   rt=tokens(raw);st=tokens(' '.join(source))
   assert any(st[j:j+len(rt)]==rt for j in range(len(st)-len(rt)+1)),('figure tokens absent from source row',rt,st)
   assert r['row_kind'] in {'country','article_total','subtotal'}
   assert r['flow'] in {'import','export'}
   unique=tuple(r.items());assert unique not in seen,'duplicate output observation';seen.add(unique)
  except Exception as e:errors.append({'tsv_line':index,'table_id':r['table_id'],'error':str(e)})
 report={'observations_verified':len(rows),'types':dict(types),'errors':errors}
 (WORK/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='errors'},indent=2));print('errors',len(errors))
 if errors:
  print(json.dumps(errors[:20],indent=2));raise SystemExit(1)
if __name__=='__main__':main()
