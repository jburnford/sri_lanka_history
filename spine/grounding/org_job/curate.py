import csv,json,sys,re,collections,pathlib
ROOT=pathlib.Path(__file__).parent
rows=list(csv.DictReader(open(ROOT/'org_names_input.tsv'),delimiter='\t'))
K={'a':'association','d':'government department','c':'company','h':'agency house','e':'estate company','r':'research station','b':'botanic garden','s':'society','k':'bank','l':'shipping line','n':'newspaper or periodical','t':'school or college','i':'international body','o':'other'}
statepath=ROOT/'org_curation_state.json'
state=json.loads(statepath.read_text()) if statepath.exists() else {'decisions':{},'bodies':[]}
def save():
 statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
 with open(ROOT/'org_bodies.jsonl','w') as f:
  for b in state['bodies']: f.write(json.dumps(b,ensure_ascii=False)+'\n')
 with open(ROOT/'org_names_decisions.tsv','w') as f:
  w=csv.writer(f,delimiter='\t');w.writerow(['key','outcome','body_id','note'])
  for j,x in enumerate(rows,1):
   if str(j) in state['decisions']: w.writerow([x['key'],*state['decisions'][str(j)]])
def batch(txt):
 for line in txt.strip().splitlines():
  if not line.strip():continue
  fields=line.split('|'); nums,action=fields[:2]; meta=fields[2:]
  for ns in nums.split(','):
   j=int(ns);x=rows[j-1]; assert str(j) not in state['decisions'],j
   note=meta[0] if meta else ''
   if action in ('g','u','x'):
    outcome={'g':'generic','u':'unclear','x':'not_an_organisation'}[action]
    state['decisions'][str(j)]=[outcome,'',note];continue
   if action.startswith('='):
    target=int(action[1:]); bid=state['decisions'][str(target)][1];assert bid
    b=next(b for b in state['bodies'] if b['body_id']==bid)
    b['member_keys'].append(x['key'])
    if x['wikidata_qid']:
     assert not b['wikidata_qid'] or b['wikidata_qid']==x['wikidata_qid'],(j,b)
     b['wikidata_qid']=x['wikidata_qid']
    b['evidence'] += ' '+note if note and len(b['evidence'])<1000 else ''
    state['decisions'][str(j)]=['body',bid,note];continue
   # kind | place | country | confidence | note | preferred
   place,country,conf,note,pref=(meta+['']*5)[:5]
   pref=pref or re.sub(r' \(\d+\)$','',x['surfaces'].split(' | ')[0])
   bid=f"org-{len(state['bodies'])+1:04d}"
   evidence=f"Printed as ‘{pref}’; roles include ‘{x['roles']}’."
   if note:evidence+=' '+note
   b={'body_id':bid,'preferred_name':pref,'kind':K[action],'place':place,'country_or_colony':country,'member_keys':[x['key']],'wikidata_qid':x['wikidata_qid'] or None,'confidence':conf or 'high','evidence':evidence}
   state['bodies'].append(b);state['decisions'][str(j)]=['body',bid,note or 'Named body supported by printed name and roles.']
 save()
 print('Saved',len(state['decisions']),'decisions;',len(state['bodies']),'bodies')
def show(a,b):
 for j in range(a,b+1):
  x=rows[j-1];print(f"{j}. {x['key']} [{x['first']}-{x['last']}] S:{x['surfaces']} R:{x['roles']} Q:{x['wikidata_qid']}")
if __name__=='__main__':
 if sys.argv[1]=='show':show(int(sys.argv[2]),int(sys.argv[3]))
 elif sys.argv[1]=='batch':batch(sys.stdin.read())
