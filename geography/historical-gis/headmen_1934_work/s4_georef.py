"""Fit Map 7 page pixels to lon/lat by maximising overlap of the plate's land (div.npy, water excluded) with the
SRTM land mask. Tries a 6-parameter affine and then a quadratic (12 parameters). Saves georef.npy (2x6:
lon = [1,x,y,x^2,xy,y^2]@g[0] with x,y in thousands of px) and prints residuals at landmarks, measured by
local matching of the coast in a window round each landmark."""
import numpy as np, sys
from scipy import ndimage as ndi, optimize
from hd_lib import *
div=np.load('div.npy'); plate=(div>1)
sl=np.load('srtm_land.npy'); gt=np.load('srtm_gt.npy')
lab,n=ndi.label(sl); sz=np.bincount(lab.ravel()); sz[0]=0; sl=(sz>=400)[lab]      # drop specks
S=ndi.gaussian_filter(sl.astype(np.float32),1.5)
def quad(x,y):
    x=np.asarray(x,float)/1000; y=np.asarray(y,float)/1000
    return np.stack([np.ones_like(x),x,y,x*x,x*y,y*y],-1)
st=4
yy,xx=np.mgrid[0:plate.shape[0]:st,0:plate.shape[1]:st]; D=quad(xx,yy); P=ndi.gaussian_filter(plate.astype(np.float32),2)[::st,::st]
def sample(g,Dm=D,order=1):
    lon=Dm@g[0]; lat=Dm@g[1]
    return ndi.map_coordinates(S,[(lat-gt[3])/gt[5]-0.5,(lon-gt[0])/gt[1]-0.5],order=order,cval=0)
def cost(g): return np.abs(sample(g)-P).sum()
# start: bounding boxes
ys,xs=np.where(plate); Ys,Xs=np.where(sl)
lon0,lon1=gt[0]+Xs.min()*gt[1],gt[0]+Xs.max()*gt[1]; lat1,lat0=gt[3]+Ys.min()*gt[5],gt[3]+Ys.max()*gt[5]
a=(lon1-lon0)/(xs.max()-xs.min())*1000; e=-(lat1-lat0)/(ys.max()-ys.min())*1000
g0=np.zeros((2,6)); g0[0,:3]=[lon0-a*xs.min()/1000,a,0]; g0[1,:3]=[lat1-e*ys.min()/1000,0,e]
def fit(mask,g0):
    idx=np.where(mask.ravel())[0]
    def c(v):
        g=g0.copy().ravel(); g[idx]=v; return cost(g.reshape(2,6))
    scale=np.array([0.01,0.01,0.01,0.003,0.003,0.003]*2)[idx]
    r=optimize.minimize(lambda u:c(g0.ravel()[idx]+u*scale),np.zeros(len(idx)),method='Powell',options={'xtol':1e-3,'ftol':1e-7,'maxiter':40})
    g=g0.copy().ravel(); g[idx]=g0.ravel()[idx]+r.x*scale; return g.reshape(2,6),r.fun
m_aff=np.array([[1,1,1,0,0,0]]*2,bool)
gA,fA=fit(m_aff,g0); gA,fA=fit(m_aff,gA)
print('affine: mismatch as fraction of plate land %.4f'%(fA/P.sum())); print(gA)
gQ,fQ=fit(np.ones((2,6),bool),gA); gQ,fQ=fit(np.ones((2,6),bool),gQ)
print('quadratic: mismatch fraction %.4f'%(fQ/P.sum())); print(gQ)
np.save('georef_affine.npy',gA); np.save('georef_quad.npy',gQ)
# landmarks: lon, lat of the modern feature; residual = shift (km east, km north) that best aligns plate coast to SRTM coast in a window
LM=[('Point Pedro',80.235,9.825),('Dondra Head',80.59,5.92),('Kalpitiya peninsula tip',79.75,8.28),('Mannar island',79.80,9.06),
    ('Trincomalee',81.22,8.57),('Batticaloa lagoon mouth',81.70,7.73),('Colombo',79.85,6.94),('Hambantota',81.12,6.12)]
kmlat=110.6; 
for name,g in (('affine',gA),('quadratic',gQ)):
    print('residuals,',name)
    tot=[]
    # invert g at landmark by Newton on px
    for nm,lon,lat in LM:
        x,y=1500.,2500.
        for it in range(30):
            Dp=quad(x,y); J=np.array([[g[0,1]+2*g[0,3]*x/1000+g[0,4]*y/1000, g[0,2]+g[0,4]*x/1000+2*g[0,5]*y/1000],[g[1,1]+2*g[1,3]*x/1000+g[1,4]*y/1000, g[1,2]+g[1,4]*x/1000+2*g[1,5]*y/1000]])/1000
            d=np.linalg.solve(J,[lon-Dp@g[0],lat-Dp@g[1]]); x+=d[0]; y+=d[1]
        R=220; x0=int(x)-R; y0=int(y)-R
        yy2,xx2=np.mgrid[y0:y0+2*R,x0:x0+2*R]; ok=(yy2>=0)&(yy2<plate.shape[0])&(xx2>=0)&(xx2<plate.shape[1])
        pl=np.zeros(yy2.shape,np.float32); pl[ok]=plate[yy2[ok],xx2[ok]]
        best=None
        for dy in range(-90,91,3):
            for dx in range(-90,91,3):
                s=sample(g,quad(xx2+dx,yy2+dy))      # SRTM as seen if the plate were shifted
                c=np.abs(s-pl).sum()
                if best is None or c<best[0]: best=(c,dx,dy)
        kmpx=abs(g[1,2])/1000*kmlat
        ex,ny=best[1]*kmpx,-best[2]*kmpx
        tot.append(ex*ex+ny*ny)
        print('  %-26s plate px (%4d,%4d)  shift of plate coast vs modern: %+5.1f km E, %+5.1f km N  (%.1f km)'%(nm,x,y,-ex,-ny,np.hypot(ex,ny)))
    print('  RMS %.1f km  (pixel = %.3f km)'%(np.sqrt(np.mean(tot)),kmpx))
