# ids2pts.py ws.npy out.tsv "id:key id:key ..."  -> appends x<TAB>y<TAB>key lines (interior point of each region), so the
# hand table stays valid when the segmentation is re-run and region ids change.
import numpy as np, sys
from scipy import ndimage as ndi
ws=np.load(sys.argv[1]); out=sys.argv[2]
objs=ndi.find_objects(ws)
with open(out,'a') as f:
    for tok in sys.argv[3].split():
        i,key=tok.split(':'); i=int(i); sl=objs[i-1]
        m=ws[sl]==i
        dt=ndi.distance_transform_edt(np.pad(m,1))[1:-1,1:-1]; yy,xx=np.unravel_index(dt.argmax(),dt.shape)
        f.write('%d\t%d\t%s\n'%(sl[1].start+xx,sl[0].start+yy,key))
