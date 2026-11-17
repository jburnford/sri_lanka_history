"""Shading features of every division on Maps 17, 18, 19 -> shading_features.tsv, and a class from fixed rules.
Features (share of the division's interior, eroded 15 px, measured on the plate registered to Map 7 by the affine):
 f = ink, t = thick ink (survives opening with a 5 px disc), hv = ink in long horizontal or vertical strokes,
 dg = ink in long diagonal strokes, dots = small round components per 10,000 px."""
import numpy as np, json, sys
from scipy import ndimage as ndi
from hd_lib import *
from hd_lib import _disc,_line
div=np.load('div.npy'); keys=json.load(open('codes.json'))
inner=np.zeros(div.shape,bool)
core=ndi.binary_erosion(np.pad((div==np.roll(div,1,0))&(div==np.roll(div,1,1))&(div==np.roll(div,-1,0))&(div==np.roll(div,-1,1)),1),_disc(15))[1:-1,1:-1]
rows=[]; TS=0.80
for tag,mp in (('p39-39','17'),('p43-43','18'),('p47-47','19')):
    g=np.asarray(Image.open(tag+'.png').convert('L')); ink=g<120          # absolute threshold: the local one in inkmask() blanks solid areas
    lab,n=ndi.label(ink); objs=ndi.find_objects(lab); sizes=np.bincount(lab.ravel())
    dots=np.zeros(ink.shape,np.float32)
    for i,sl in enumerate(objs,1):
        h=sl[0].stop-sl[0].start; w=sl[1].stop-sl[1].start
        if 5<=max(h,w)<=22 and min(h,w)>=5 and sizes[i]>=0.5*h*w: dots[(sl[0].start+sl[0].stop)//2,(sl[1].start+sl[1].stop)//2]=1
    thick=ndi.binary_opening(ink,_disc(5))
    thin=ink&~ndi.binary_dilation(thick,iterations=2)
    hv=ndi.binary_opening(thin,np.ones((1,35),bool))|ndi.binary_opening(thin,np.ones((35,1),bool))
    dg=np.zeros_like(ink)
    for a in range(20,75,4): dg|=ndi.binary_opening(thin,_line(35,a))
    c=affine_coef(np.load('affine_'+tag+'.npy'))
    F={k:warp(v.astype(np.float32),c,order=1) for k,v in (('f',ink),('t',thick),('hv',hv),('dg',dg))}
    # dots: warp a blurred density (sum preserved approximately since scale ~0.985)
    F['dots']=warp(ndi.uniform_filter(dots,41),c,order=1)
    for code in range(2,len(keys)):
        m=core&(div==code); npx=int(m.sum())
        if npx<2500: rows.append((keys[code],mp,npx,'','','','','','too small to measure')); continue
        f,t,h,d,dd=[float(F[k][m].mean()) for k in ('f','t','hv','dg','dots')]; dd*=1e4
        if t>TS: cls='solid'
        elif t>0.40: cls='band'
        elif h>0.08 and h>d: cls='cross'
        elif d>0.08: cls='hatch'
        elif dd>=4.0 and h<0.03 and d<0.03: cls='dots'
        elif dd<1.5 and h<0.03 and d<0.03 and t<0.25: cls='blank'
        else: cls='?'
        rows.append((keys[code],mp,npx,'%.3f'%f,'%.3f'%t,'%.3f'%h,'%.3f'%d,'%.2f'%dd,cls))
with open('shading_features.tsv','w') as fo:
    fo.write('key\tmap\tinterior_px\tink\tthick\thv\tdiag\tdots_per_1e4\tclass\n')
    for r in rows: fo.write('\t'.join(map(str,r))+'\n')
from collections import Counter
for mp in ('17','18','19'): print(mp,Counter(r[8] for r in rows if r[1]==mp))
