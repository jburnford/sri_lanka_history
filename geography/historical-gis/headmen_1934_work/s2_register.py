"""Register Map 17 (and 18, 19 if rendered) to Map 7.
 affine_<page>.npy : sx,sy,tx,ty,r from maximising land-mask overlap (X17=sx*x-r*y+tx, Y17=r*x+sy*y+ty)
 map17_to7.npy     : cubic polynomial refinement for the south-west, from block matching of the edges of the
                     warped Map 17 regions against Map 7 ink."""
import numpy as np, sys, os
from scipy import ndimage as ndi, optimize
from hd_lib import *
ink7=inkmask('full-15.png'); land7=land_from_ink(ink7); np.save('land7.npy',land7)
a=land7[::4,::4].astype(np.float32); H,W=a.shape; yy,xx=np.mgrid[:H,:W]
for tag in ['p39-39','p43-43','p47-47']:
    if not os.path.exists(tag+'.png') or os.path.exists('affine_'+tag+'.npy'): continue
    b=land_from_ink(inkmask(tag+'.png'))[::4,::4].astype(np.float32)
    def cost(p):
        sx,sy,tx,ty,r=p
        return np.abs(ndi.map_coordinates(b,[r*xx+sy*yy+ty, sx*xx-r*yy+tx],order=1,cval=0)-a).sum()
    best=min(((cost([1,1,tx,ty,0]),[1,1,tx,ty,0]) for tx in range(-60,61,10) for ty in range(0,120,10)),key=lambda t:t[0])
    r=optimize.minimize(cost,best[1],method='Powell',options={'xtol':1e-3,'ftol':1e-6})
    p=r.x; print(tag,'affine',p,'mismatch fraction of land',r.fun/a.sum())
    np.save('affine_'+tag+'.npy',np.array([p[0],p[1],4*p[2],4*p[3],p[4]]))
if not os.path.exists('map17_to7.npy') or 'force' in sys.argv:
    a7=ndi.gaussian_filter(ink7.astype(np.float32),5)
    ws=np.load('ws17.npy'); c=affine_coef(np.load('affine_p39-39.npy'))
    WIN=(150,2600,2400,4750)
    for it in range(3):
        w=warp(ws,c)
        e=((w!=np.roll(w,1,0))|(w!=np.roll(w,1,1))).astype(np.float32); e7=ndi.gaussian_filter(e,5)
        B=320; S=107; R=36 if it==0 else 20
        rows=[]
        for y0 in range(WIN[1],WIN[3]-B,S):
            for x0 in range(WIN[0],WIN[2]-B,S):
                b=e7[y0:y0+B,x0:x0+B]; a_=a7[y0-R:y0+B+R,x0-R:x0+B+R]
                if b.sum()<80 or a_.shape!=(B+2*R,B+2*R): continue
                b0=b-b.mean(); a0=a_-a_.mean()
                cc=np.fft.irfft2(np.fft.rfft2(a0)*np.fft.rfft2(b0[::-1,::-1],s=a_.shape),s=a_.shape)[B-1:B+2*R,B-1:B+2*R]
                dy,dx=np.unravel_index(cc.argmax(),cc.shape)
                if min(dy,dx)<2 or max(dy,dx)>2*R-2: continue
                rows.append((x0+B/2,y0+B/2,dx-R,dy-R))
        P=np.array(rows)
        X,Y=to17(P[:,0],P[:,1],c)
        A=design(P[:,0]+P[:,2],P[:,1]+P[:,3])
        wt=np.ones(len(P)); cn=c.copy()
        for k in range(8):
            cn[0]=np.linalg.lstsq(A*wt[:,None],X*wt,rcond=None)[0]; cn[1]=np.linalg.lstsq(A*wt[:,None],Y*wt,rcond=None)[0]
            res=np.hypot(A@cn[0]-X,A@cn[1]-Y); wt=(res<max(5,2.0*np.median(res[wt>0]))).astype(float)
        print('poly iter',it,'blocks',len(P),'inliers',int(wt.sum()),'inlier resid px median/90%%: %.1f %.1f'%(np.median(res[wt>0]),np.percentile(res[wt>0],90)))
        c=cn
    np.save('map17_to7.npy',c)
