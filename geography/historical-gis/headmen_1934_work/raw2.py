# raw2.py x0 y0 w h scale out [pages]: raw Map 7 window beside the same window of Maps 17/18/19 (affine-warped, no overlays)
import numpy as np, sys
from PIL import Image
from scipy import ndimage as ndi
x0,y0,w,h=map(int,sys.argv[1:5]); sc=float(sys.argv[5]); out=sys.argv[6]
maps=sys.argv[7].split(',') if len(sys.argv)>7 else ['p39-39']
ims=[] if (len(sys.argv)>8) else [Image.open('full-15.png').convert('L').crop((x0,y0,x0+w,y0+h))]
for m in maps:
    sx,sy,tx,ty,r=np.load('affine_'+m+'.npy')
    b=np.asarray(Image.open(m+'.png').convert('L'))
    M=np.array([[sy,r],[-r,sx]]); off=np.array([ty+sy*y0+r*x0,tx-r*y0+sx*x0])
    ims.append(Image.fromarray(ndi.affine_transform(b,M,offset=off,output_shape=(h,w),order=1,cval=200)))
ims=[i.resize((int(w*sc),int(h*sc)),Image.LANCZOS) for i in ims]
W=Image.new('L',(sum(i.width for i in ims)+6*(len(ims)-1),ims[0].height)); x=0
for i in ims: W.paste(i,(x,0)); x+=i.width+6
W.save(out); print(W.size)
