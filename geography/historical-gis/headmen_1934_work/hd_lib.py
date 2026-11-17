"""Shared functions for the 1934 headmen's divisions layer (segmentation, cleaning, warping)."""
import numpy as np, os
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
Image.MAX_IMAGE_PIXELS=None
SHAPE7=(5161,3141)

def inkmask(png, drop=45):
    g=np.asarray(Image.open(png).convert('L')).astype(np.float32)
    bg=ndi.uniform_filter(g,151)
    ink=g<bg-drop
    ink[:, :30]=False; ink[:, -30:]=False
    hl,hn=ndi.label(~ink); hs=np.bincount(hl.ravel()); ink|=(hs<80)[hl]   # fill pin-holes in printed lines
    return ink

def _disc(r):
    y,x=np.ogrid[-int(r):int(r)+1,-int(r):int(r)+1]; return x*x+y*y<=r*r
def _line(L,ang):
    n=L//2; k=np.zeros((2*n+1,2*n+1),bool)
    for t in np.linspace(-n,n,4*n+1):
        k[int(round(n-t*np.sin(np.radians(ang)))),int(round(n+t*np.cos(np.radians(ang))))]=True
    return k

def remove_dots(ink, maxdim=22, reach=34):
    """Shading dots are small compact ink components; drop them, except a dot lying between two
    separate bigger strokes (the dot of a dash-dot boundary line), which is kept."""
    lab,n=ndi.label(ink)
    objs=ndi.find_objects(lab)
    small=np.zeros(n+1,bool)
    for i,sl in enumerate(objs,1):
        small[i]=max(sl[0].stop-sl[0].start, sl[1].stop-sl[1].start)<=maxdim
    big=ink&~small[lab]
    blab,bn=ndi.label(big)
    out=big.copy()
    H,W=ink.shape
    for i,sl in enumerate(objs,1):
        if not small[i]: continue
        cy=(sl[0].start+sl[0].stop)//2; cx=(sl[1].start+sl[1].stop)//2
        y0,y1,x0,x1=max(0,cy-reach),min(H,cy+reach+1),max(0,cx-reach),min(W,cx+reach+1)
        yy,xx=np.ogrid[y0:y1,x0:x1]
        near=blab[y0:y1,x0:x1][((yy-cy)**2+(xx-cx)**2)<=reach*reach]
        ids=np.unique(near[near>0])
        if len(ids)>=2:
            out[sl]|=(lab[sl]==i)
    return out

def clear_hatched_areas(ink, window, angles=(28,30,32,34,36), L=61):
    """Hatching = long straight strokes at one angle. Find the hatched AREAS, wipe the ink inside them
    except thick strokes (district lines), and keep the outline of each area as a barrier."""
    x0,y0,x1,y1=window
    sub=ink[y0:y1,x0:x1]
    h=np.zeros_like(sub)
    for a in angles: h|=ndi.binary_opening(sub,_line(L,a))
    H=ndi.binary_closing(np.pad(h,40),_disc(14))[40:-40,40:-40]
    H=ndi.binary_opening(H,_disc(14))
    H=ndi.binary_fill_holes(H)
    inner=ndi.binary_erosion(H,_disc(5))
    ring=H&~ndi.binary_erosion(H,_disc(2))
    thick=ndi.binary_opening(sub,_disc(4))
    out=ink.copy(); out[y0:y1,x0:x1]=(sub&~inner)|ring|(thick&H)
    return out

def add_barriers(ink, lines, width=5):
    im=Image.fromarray(ink.astype(np.uint8)*255); d=ImageDraw.Draw(im)
    for (x1,y1,x2,y2) in lines: d.line((x1,y1,x2,y2),fill=255,width=width)
    return np.asarray(im)>0

def read_tsv(path, n, conv=int):
    rows=[]
    if os.path.exists(path):
        for l in open(path):
            if l.strip() and not l.startswith('#'):
                p=l.rstrip('\n').split('\t'); rows.append(tuple(conv(v) for v in p[:n])+tuple(p[n:]))
    return rows

def grow(ink, T=9, extra_seeds=(), minseed=120):
    """Ink-free cores (distance to ink > T) are seeds; grow them outward level by level, each unlabelled
    pixel taking the nearest labelled pixel of its own connected piece, so regions meet in the necks of
    dotted lines; remaining pixels (ink) go to the nearest label, so edges run down the printed lines."""
    dist=ndi.distance_transform_edt(~ink)
    core=dist>T
    lab,n=ndi.label(core)
    sizes=np.bincount(lab.ravel()); keep=sizes>=minseed; keep[0]=False
    core2=keep[lab]
    yy,xx=np.ogrid[:ink.shape[0],:ink.shape[1]]
    for s in extra_seeds:
        x,y,r=s[:3]
        core2|=((xx-x)**2+(yy-y)**2<=r*r)&(~ink)
    ws,n2=ndi.label(core2); ws=ws.astype(np.int32)
    for L in list(range(int(T),0,-1))+[0.5]:
        allowed=dist>=L
        comp,_=ndi.label(allowed)
        idx=ndi.distance_transform_edt(ws==0,return_distances=False,return_indices=True)
        cand=ws[idx[0],idx[1]]
        ok=allowed&(ws==0)&(comp==comp[idx[0],idx[1]])
        ws[ok]=cand[ok]
    idx=ndi.distance_transform_edt(ws==0,return_distances=False,return_indices=True)
    return ws[idx[0],idx[1]]

def land_from_ink(ink, close=3):
    k=ndi.binary_dilation(ink,iterations=close)
    lab,n=ndi.label(~k)
    sea=lab==lab[5,5]
    notsea=~ndi.binary_dilation(sea,iterations=close)
    l2,n2=ndi.label(notsea)
    sz=np.bincount(l2.ravel()); sz[0]=0
    return l2==sz.argmax()

# ---- plate-to-plate mapping: X17 = design(x7,y7) @ c[0], Y17 = design @ c[1]
def design(x,y):
    x=np.asarray(x,float)/1000.; y=np.asarray(y,float)/1000.
    return np.stack([np.ones_like(x),x,y,x*x,x*y,y*y,x**3,x*x*y,x*y*y,y**3],-1)
def affine_coef(p):
    sx,sy,tx,ty,r=p
    c=np.zeros((2,10)); c[0,:3]=[tx,sx*1000,-r*1000]; c[1,:3]=[ty,r*1000,sy*1000]; return c
def to17(x,y,c):
    D=design(x,y); return D@c[0], D@c[1]
def warp(arr,c,order=0,cval=0,shape=SHAPE7):
    out=np.zeros(shape,arr.dtype if order==0 else np.float32)
    for y0 in range(0,shape[0],512):
        yy,xx=np.mgrid[y0:min(y0+512,shape[0]),0:shape[1]]
        X,Y=to17(xx,yy,c)
        out[y0:y0+512]=ndi.map_coordinates(arr,[Y,X],order=order,cval=cval)
    return out

def interior_point(mask_slice_origin, m):
    dt=ndi.distance_transform_edt(np.pad(m,1))[1:-1,1:-1]; yy,xx=np.unravel_index(dt.argmax(),dt.shape)
    return mask_slice_origin[0]+xx, mask_slice_origin[1]+yy
