# zoom.py base.png ws.npy x0 y0 w h scale out [tint]
import numpy as np, sys
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
basef,wsf=sys.argv[1:3]; x0,y0,w_,h_=map(int,sys.argv[3:7]); sc=float(sys.argv[7]); out=sys.argv[8]; tint=float(sys.argv[9]) if len(sys.argv)>9 else 0.12
ws=np.array(np.load(wsf,mmap_mode='r')[y0:y0+h_,x0:x0+w_])
base=np.asarray(Image.open(basef).convert('RGB'))[y0:y0+h_,x0:x0+w_]
rng=np.random.RandomState(3); pal=rng.randint(60,255,(int(ws.max())+1,3))
img=Image.fromarray(((1-tint)*base+tint*pal[ws]).astype(np.uint8)).resize((int(w_*sc),int(h_*sc)),Image.LANCZOS)
W=np.asarray(Image.fromarray(ws).resize(img.size,Image.NEAREST))
a=np.asarray(img).copy(); edge=(W!=np.roll(W,1,0))|(W!=np.roll(W,1,1)); a[edge]=(255,0,0)
im=Image.fromarray(a); d=ImageDraw.Draw(im)
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',17)
for i in np.unique(W):
    m=(W==i)
    if m.sum()<150: continue
    dt=ndi.distance_transform_edt(np.pad(m,1))[1:-1,1:-1]; yy,xx=np.unravel_index(dt.argmax(),dt.shape)
    d.text((xx-12,yy-10),str(i),fill=(0,0,200),font=f,stroke_width=2,stroke_fill=(255,255,255))
f2=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
for X in range((x0//100+1)*100,x0+w_,100):
    d.line(((X-x0)*sc,0,(X-x0)*sc,8),fill=(0,160,0),width=2); d.text(((X-x0)*sc+2,8),str(X),fill=(0,120,0),font=f2)
for Y in range((y0//100+1)*100,y0+h_,100):
    d.line((0,(Y-y0)*sc,8,(Y-y0)*sc),fill=(0,160,0),width=2); d.text((10,(Y-y0)*sc-6),str(Y),fill=(0,120,0),font=f2)
im.save(out)
