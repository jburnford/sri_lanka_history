import csv,json,re,collections,hashlib
import curate
s=curate.state; rows=curate.rows
bykey={x['key']:x for x in rows}; idx={x['key']:str(i) for i,x in enumerate(rows,1)}
def surface(x):return re.sub(r' \(\d+\)$','',x['surfaces'].split(' | ')[0])
# Correct explicitly identified serialization-field errors; these are not grouping changes.
wrong_names=[432,455,552,623,688,714,760,763,849,878,920,976,980,1023,1092,1125,1170,1203]
for b in s['bodies']:
 anchor=s['decisions'][idx[b['member_keys'][0]]]
 if int(b['body_id'][4:]) in wrong_names and b['preferred_name'] != surface(bykey[b['member_keys'][0]]):
  recovered=b['preferred_name'];b['preferred_name']=surface(bykey[b['member_keys'][0]])
  anchor[2]=recovered
 if b['confidence'] not in ('high','medium','low'):
  recovered=b['confidence'];b['confidence']='medium';anchor[2]=recovered
 b['country_or_colony']=b['country_or_colony'].strip()
# Madras is stated, but India is not stated for these government-name members.
next(b for b in s['bodies'] if b['body_id']=='org-0011')['country_or_colony']=''
# Choose unabridged printed names for a few authorities whose leading surface is shortened.
prefs={
 'org-0221':"Kelani Valley Tea Association, Limited",
 'org-0225':'Heneratgoda Botanic Gardens',
 'org-0148':'Brunswick Quinine Works',
 'org-0153':'Auerbach Quinine Works',
}
for b in s['bodies']:
 if prefs.get(b['body_id']):b['preferred_name']=prefs[b['body_id']]
# Modest confidence for the spelling/short-name links requiring the most interpretation.
medium_anchors=[303,73,192,202,441,722,733,820,943,945,950,974,1136,1240,1472,1693,1919,1924,1957,2153,2177,2183]
for n in medium_anchors:
 d=s['decisions'][str(n)]
 if d[0]=='body':
  b=next(b for b in s['bodies'] if b['body_id']==d[1])
  if b['confidence']=='high':b['confidence']='medium'
# Keep compact evidence to two prose sentences: actual quoted forms and roles, then
# the manually recorded qualification or first explicit link. Full per-name reasoning
# remains in the decisions TSV and curation state.
for b in s['bodies']:
 keys=b['member_keys']; forms=list(dict.fromkeys(surface(bykey[k]) for k in keys))
 rolephrases=[]
 for k in keys:
  for role in bykey[k]['roles'].split(' | ')[:2]:
   role=re.sub(r' \(\d+\)$','',role)
   if role and role not in rolephrases:rolephrases.append(role)
 formtext=', '.join('‘'+f+'’' for f in forms)
 roletext=', '.join('‘'+r+'’' for r in rolephrases[:5])
 first=f"The input prints {formtext}"
 first+=f"; roles include {roletext}." if roletext else '; no roles are supplied.'
 notes=[s['decisions'][idx[k]][2] for k in keys]
 note=notes[0]
 if note=='Named body supported by printed name and roles.':
  note=next((n for n in notes[1:] if n),'')
 # Manual notes are ordinarily one sentence; retain the first complete prose thought
 # without splitting on initials and corporate abbreviations.
 if note:
  note=re.split(r'(?<=[.!?])\s+(?=[A-Z‘])',note)[0]
  if not note.endswith(('.', '!', '?')):note+='.'
 b['evidence']=first+(' '+note if note else '')
curate.save()
# Validate the final deliverables, independently reloading them from disk.
bodies=[json.loads(x) for x in open('org_bodies.jsonl')]
decisions=list(csv.DictReader(open('org_names_decisions.tsv'),delimiter='\t'))
errors=[]; ids={b['body_id'] for b in bodies}; owners=collections.defaultdict(list)
required={'body_id','preferred_name','kind','place','country_or_colony','member_keys','wikidata_qid','confidence','evidence'}
if len(ids)!=len(bodies):errors.append('Duplicate body ID')
if [d['key'] for d in decisions]!=[x['key'] for x in rows]:errors.append('Decision coverage or order mismatch')
for b in bodies:
 if set(b)!=required:errors.append('Body schema: '+b['body_id'])
 if b['kind'] not in curate.K.values():errors.append('Invalid kind: '+b['body_id'])
 if b['confidence'] not in ('high','medium','low'):errors.append('Invalid confidence: '+b['body_id'])
 if not b['member_keys']:errors.append('Empty membership: '+b['body_id'])
 for k in b['member_keys']:
  if k not in bykey:errors.append('Unknown member: '+k)
  owners[k].append(b['body_id'])
 q=b['wikidata_qid']
 if q and (not re.fullmatch('Q[0-9]+',q) or q not in {bykey[k]['wikidata_qid'] for k in b['member_keys']}):errors.append('Unlicensed QID: '+b['body_id'])
for k,v in owners.items():
 if len(v)!=1:errors.append('Multiple memberships: '+k)
for d in decisions:
 if d['outcome'] not in ('body','generic','not_an_organisation','unclear'):errors.append('Invalid outcome: '+d['key'])
 if d['outcome']=='body':
  if d['body_id'] not in ids:errors.append('Unknown body reference: '+d['key'])
  if owners.get(d['key'])!=[d['body_id']]:errors.append('Membership disagreement: '+d['key'])
 elif d['body_id'] or d['key'] in owners:errors.append('Non-body membership: '+d['key'])
 if not d['note']:errors.append('Empty note: '+d['key'])
report={'input_names':len(rows),'decisions':len(decisions),'bodies':len(bodies),'member_keys':sum(len(b['member_keys']) for b in bodies),'unknown_member_keys':sum(k not in bykey for k in owners),'duplicate_memberships':sum(len(v)>1 for v in owners.values()),'outcome_counts':dict(collections.Counter(d['outcome'] for d in decisions)),'input_sha256':hashlib.sha256(open('org_names_input.tsv','rb').read()).hexdigest(),'errors':errors,'passed':not errors}
open('org_validation.json','w').write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
# Summary: size is the number of distinct input keys, with article mention totals only
# as a tie breaker (article totals are not deduplicated across names).
counts=collections.Counter(d['outcome'] for d in decisions); kinds=collections.Counter(b['kind'] for b in bodies)
def article_sum(b):return sum(int(bykey[k]['articles']) for k in b['member_keys'])
largest=sorted(bodies,key=lambda b:(-len(b['member_keys']),-article_sum(b),b['body_id']))[:20]
uncertain=sorted((b for b in bodies if len(b['member_keys'])>1 and b['confidence']!='high'),key=lambda b:({'low':0,'medium':1}[b['confidence']],-len(b['member_keys']),b['body_id']))[:20]
lines=['# Organisation authority summary','',f'Completed all **{len(rows):,} of {len(rows):,} names**, in input order, through row 2265 (`royal air force`). Decisions were saved at every 100-name checkpoint and after the final 65 names.','', 'The groupings were made by reading the supplied names, printed forms, roles and dates. Scripts recorded the explicit decisions, sorted counts and checked consistency; no string-similarity grouping rule or network source was used. QIDs were copied only from member rows in the input.','', '## Outcomes','', '| Outcome | Names |','|---|---:|']
for out in ('body','generic','not_an_organisation','unclear'):lines.append(f'| {out} | {counts[out]:,} |')
lines+=['',f'**{len(bodies):,} bodies**, including {sum(len(b["member_keys"])>1 for b in bodies):,} bodies with more than one input key. Remaining uncertainty is recorded in confidence fields and decision notes; similar names, parent/branch relationships and potential renames were kept separate when identity was not established.','', '## Body kinds','', '| Kind | Bodies |','|---|---:|']
for kind in curate.K.values():lines.append(f'| {kind} | {kinds[kind]:,} |')
lines+=['','## Twenty largest bodies','', 'Ranked by number of member keys; ties use the sum of input article counts. Those sums are only a ranking aid and are not counts of distinct articles across variants. Each list below gives all member keys.','']
for i,b in enumerate(largest,1):
 lines.append(f'{i}. **{b["preferred_name"]}** ({b["body_id"]}; {len(b["member_keys"])} names; {b["confidence"]} confidence): '+ '; '.join('`'+k+'`' for k in b['member_keys'])+'.')
lines+=['','## Twenty least certain multi-name groupings','', 'These are the lowest-confidence joined groups, including groups whose principal uncertainty is their boundary against a separately retained authority. Low confidence ranks before medium; ties prioritize larger groups. The TSV preserves the justification for each individual link.','']
for i,b in enumerate(uncertain,1):
 ds=[s['decisions'][idx[k]][2] for k in b['member_keys']]
 explanation=next((n for n in ds if n!='Named body supported by printed name and roles.'),'No fuller institutional identity is supplied.')
 lines.append(f'{i}. **{b["preferred_name"]}** ({b["body_id"]}; {b["confidence"]}): '+ '; '.join('`'+k+'`' for k in b['member_keys'])+f'. {explanation}')
lines+=['','## Validation','',f'**{"PASS" if not errors else "FAIL"}** — checked the written JSONL and TSV files.','',f'- All {len(rows):,} input names have exactly one decision, in the original order.',f'- Every member key exists in the input; unknown member keys: {report["unknown_member_keys"]}.',f'- No key belongs to two bodies; duplicate memberships: {report["duplicate_memberships"]}.','- Every `body` decision points to an existing body ID and exactly matching membership.','- Generic, non-organisation and unclear decisions have no body membership.','- Body IDs, schema, kinds, confidence values and QID provenance passed checks.' if not errors else '- Errors: '+repr(errors),'','Machine-readable check results: `org_validation.json`. Explicit decisions and supporting notes are also retained in `org_curation_state.json`; `curate.py` and `finalize_org.py` record the output/checking procedure.','']
open('org_summary.md','w').write('\n'.join(lines))
print(json.dumps(report,indent=2))
print('Uncertain multi-name groups listed:',len(uncertain))
