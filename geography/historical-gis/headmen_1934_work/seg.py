"""Segment a plate into faces: ink-free cores are seeds, flooded outward so edges land on the printed lines.
usage: seg.py <folder> [T] [image]   -> ws.npy (labels), ink.npy"""
import numpy as np, sys
from PIL import Image
from scipy import ndimage as ndi
Image.MAX_IMAGE_PIXELS=None
S=sys.argv[1]; T=float(sys.argv[2]) if len(sys.argv)>2 else 9; IMG=sys.argv[3] if len(sys.argv)>3 else 'full-15.png'
g=np.asarray(Image.open(S+'/'+IMG).convert('L')).astype(np.int16)
bg=ndi.uniform_filter(g.astype(np.float32),151)
ink=(g < bg-45)
ink[:, :30]=False; ink[:, -30:]=False
dist=ndi.distance_transform_edt(~ink)
core=dist>T
lab,n=ndi.label(core)
sizes=ndi.sum(core,lab,range(1,n+1))
keep=np.where(sizes>=120)[0]+1
mark=np.zeros(lab.shape,np.int32)
for new,old in enumerate(keep,1): mark[lab==old]=new
print("ink frac",ink.mean(),"seeds",len(keep),"dropped",n-len(keep))
cost=np.clip(60-dist,0,60).astype(np.uint8)
ws=ndi.watershed_ift(cost,mark)
np.save(S+'/ws.npy',ws.astype(np.int32)); np.save(S+'/ink.npy',ink)
