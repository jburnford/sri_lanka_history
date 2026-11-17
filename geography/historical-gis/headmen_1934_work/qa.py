# qa.py x0 y0 w h scale out [base]: final division edges + key labels over Map 7 (left) and warped Map 17 (right)
import numpy as np, sys, json
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from hd_lib import *
x0,y0,w_,h_=map(int,sys.argv[1:5]); sc=float(sys.argv[5]); out=sys.argv[6]
div=np.array(np.load('div.npy',mmap_mode='r')[y0:y0+h_,x0:x0+w_]); keys=json.load(open('codes.json'))
c=np.load('map17_to7.npy') if (y0>2600 and x0<2000) else affine_coef(np.load('affine_p39-39.npy'))
yy,xx=np.mgrid[y0:y0+h_,x0:x0+w_]; X,Y=to17(xx,yy,c)
b17=ndi.map_coordinates(np.asarray(Image.open('p39-39.png').convert('L')),[Y,X],order=1,cval=200)
panels=[]
for k,base in enumerate([np.asarray(Image.open('full-15.png').convert('L'))[y0:y0+h_,x0:x0+w_], b17]):
    img=Image.fromarray(base).convert('RGB').resize((int(w_*sc),int(h_*sc)),Image.LANCZOS)
    Wd=np.asarray(Image.fromarray(div).resize(img.size,Image.NEAREST))
    a=np.asarray(img).copy(); e=(Wd!=np.roll(Wd,1,0))|(Wd!=np.roll(Wd,1,1)); a[e]=(255,0,0)
    im=Image.fromarray(a); d=ImageDraw.Draw(im)
    f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',15)
    if k==0:
        lab,n=ndi.label(Wd>1)
        for v in np.unique(Wd):
            if v<2: continue
            cl,cn=ndi.label(Wd==v)
            for j in range(1,cn+1):
                m=cl==j
                if m.sum()<250: continue
                dt=ndi.distance_transform_edt(np.pad(m,1))[1:-1,1:-1]; py,px=np.unravel_index(dt.argmax(),dt.shape)
                d.text((px-14,py-8),keys[v],fill=(0,0,220),font=f,stroke_width=2,stroke_fill=(255,255,255))
    f2=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
    for Xt in range((x0//100+1)*100,x0+w_,100):
        d.line(((Xt-x0)*sc,0,(Xt-x0)*sc,8),fill=(0,160,0),width=2); d.text(((Xt-x0)*sc+2,8),str(Xt),fill=(0,120,0),font=f2)
    for Yt in range((y0//100+1)*100,y0+h_,100):
        d.line((0,(Yt-y0)*sc,8,(Yt-y0)*sc),fill=(0,160,0),width=2); d.text((10,(Yt-y0)*sc-6),str(Yt),fill=(0,120,0),font=f2)
    panels.append(im)
Wm=Image.new('RGB',(panels[0].width*2+6,panels[0].height)); Wm.paste(panels[0],(0,0)); Wm.paste(panels[1],(panels[0].width+6,0)); Wm.save(out)
