"""Draw the regions of ws.npy with their ids over the plate for a pixel window.
usage: viz.py <folder> x0 y0 x1 y1 out.png [scale] [image]"""
import numpy as np, sys
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
Image.MAX_IMAGE_PIXELS=None
S=sys.argv[1]; x0,y0,x1,y1=map(int,sys.argv[2:6]); out=sys.argv[6]; scale=float(sys.argv[7]) if len(sys.argv)>7 else 1
IMG=sys.argv[8] if len(sys.argv)>8 else 'full-15.png'
ws=np.load(S+'/ws.npy'); base=np.asarray(Image.open(S+'/'+IMG).convert('RGB'))
rng=np.random.RandomState(3); pal=rng.randint(60,255,(ws.max()+1,3))
w=ws[y0:y1,x0:x1]; img=(0.55*base[y0:y1,x0:x1]+0.45*pal[w]).astype(np.uint8)
edge=(w!=np.roll(w,1,0))|(w!=np.roll(w,1,1)); img[edge]=(255,0,0)
im=Image.fromarray(img); d=ImageDraw.Draw(im)
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',int(20/scale) if scale<1 else 20)
for i in np.unique(w):
    m=(w==i)
    if m.sum()<400: continue
    dt=ndi.distance_transform_edt(m); yy,xx=np.unravel_index(dt.argmax(),dt.shape)
    d.text((xx-12,yy-10),str(i),fill=(0,0,160),font=f,stroke_width=2,stroke_fill=(255,255,255))
if scale!=1: im=im.resize((int(im.width*scale),int(im.height*scale)))
im.save(out); print(im.size)
