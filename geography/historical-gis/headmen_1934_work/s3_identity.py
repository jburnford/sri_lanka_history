"""Give every Map 7 fragment a key number -> div.npy (codes), codes.json, fragments.tsv.
 Hand table ident7.tsv wins; otherwise the fragment takes the majority number of the warped, labelled Map 17 regions."""
import numpy as np, json, sys
from scipy import ndimage as ndi
from hd_lib import *
ws7=np.load('ws7.npy'); sea=ws7[5,5]
ws17=np.load('ws17.npy'); c=np.load('map17_to7.npy')
keys=['', 'W']; code={'':0,'W':1}
def kc(k):
    if k not in code: code[k]=len(keys); keys.append(k)
    return code[k]
lut=np.zeros(ws17.max()+1,np.int32)
for x,y,k in read_tsv('ident17.tsv',2):
    r=ws17[y,x]
    if lut[r] and lut[r]!=kc(k): print('CONFLICT map17 region',r,'at',x,y,keys[lut[r]],k)
    lut[r]=kc(k)
D17=warp(lut[ws17],c)
hand={}
for x,y,k in read_tsv('ident7.tsv',2):
    r=ws7[y,x]
    if r==sea: print('hand point in sea',x,y,k); continue
    if r in hand and hand[r]!=k: print('CONFLICT map7 fragment',r,'at',x,y,hand[r],k)
    hand[r]=k
n=ws7.max()
objs=ndi.find_objects(ws7)
flut=np.zeros(n+1,np.int32); rows=[]
div=np.zeros(ws7.shape,np.int32)
for f in range(1,n+1):
    if f==sea or objs[f-1] is None: continue
    sl=objs[f-1]; m=ws7[sl]==f; area=int(m.sum())
    dt=ndi.distance_transform_edt(np.pad(m,1))[1:-1,1:-1]; yy,xx=np.unravel_index(dt.argmax(),dt.shape); px,py=sl[1].start+xx,sl[0].start+yy
    cnt=np.bincount(D17[sl][m],minlength=len(keys)); lab=cnt[1:].sum() if False else cnt[2:].sum()
    top=cnt[2:].argmax()+2 if lab>0 else 0
    second=np.sort(cnt[2:])[-2] if len(cnt)>3 else 0
    if f in hand and hand[f]=='S17':
        d=D17[sl].copy(); bad=m&(d<2)
        idx=ndi.distance_transform_edt(~(m&(d>=2)),return_distances=False,return_indices=True)
        d=d[idx[0],idx[1]]; div[sl][m]=d[m]; src='split by Map 17'; k='(split)'
    elif f in hand:
        k=hand[f]; flut[f]=kc(k); src='hand'
    elif lab>=0.5*area:
        k=keys[top]; flut[f]=top; src='map17 majority'
    else:
        k=''; src='UNASSIGNED'
    rows.append((f,px,py,area,k,src,'%.2f'%(cnt[top]/max(lab,1)),'%.2f'%(lab/area),keys[top] if top else '', '%.2f'%(second/max(lab,1))))
m=div==0; div[m]=flut[ws7][m]
np.save('div.npy',div); json.dump(keys,open('codes.json','w'))
with open('fragments.tsv','w') as f:
    f.write('fragment\tx\ty\tarea_px\tkey\tsource\tmap17_purity\tmap17_cover\tmap17_top\tmap17_second_share\n')
    for r in rows: f.write('\t'.join(map(str,r))+'\n')
un=[r for r in rows if r[5]=='UNASSIGNED']
print('fragments',len(rows),'unassigned',len(un),'area px',sum(r[3] for r in un))
for r in un: print('  UNASSIGNED',r)
print('hand vs map17 disagreements (cover>0.5):')
for r in rows:
    if r[5]=='hand' and float(r[7])>0.5 and r[8]!=r[4] and r[4] not in ('W',): print('  ',r)
print('fragments split by Map 17:',sum(1 for r in rows if r[5]=='split by Map 17'))
print('majority fragments with purity<0.85:')
for r in rows:
    if r[5]=='map17 majority' and float(r[6])<0.85: print('  ',r)
used=sorted(set(keys[v] for v in np.unique(div)))
print('keys present:',len(used)); print(used)
