"""div.npy -> polygons in EPSG:4326 with shared, once-simplified boundaries -> ../headmen_divisions_1934.geojson and key TSV.
Boundaries are traced on the pixel lattice as arcs between junctions, each arc simplified once (Douglas-Peucker,
1.5 px ~ 150 m), and every division's rings are assembled from the same arcs, so neighbours share identical edges."""
import numpy as np, json, sys, re, os
from collections import defaultdict
from osgeo import ogr, osr
ogr.UseExceptions()
OUT='..'
div=np.load('div.npy'); keys=json.load(open('codes.json'))
G=np.load(sys.argv[1] if len(sys.argv)>1 else 'georef.npy')
L=np.pad(np.where(div<2,0,div),1)
H,W=L.shape
# ---- lattice edges
adj=defaultdict(list); edges=[]
ys,xs=np.where(L[:,1:]!=L[:,:-1])           # vertical edge between (y,x) and (y,x+1): nodes (y,x+1)-(y+1,x+1)
for y,x in zip(ys.tolist(),xs.tolist()):
    e=len(edges); a=(y,x+1); b=(y+1,x+1); edges.append((a,b,(int(L[y,x]),int(L[y,x+1])))); adj[a].append(e); adj[b].append(e)
ys,xs=np.where(L[1:,:]!=L[:-1,:])           # horizontal edge between (y,x) and (y+1,x): nodes (y+1,x)-(y+1,x+1)
for y,x in zip(ys.tolist(),xs.tolist()):
    e=len(edges); a=(y+1,x); b=(y+1,x+1); edges.append((a,b,(int(L[y,x]),int(L[y+1,x])))); adj[a].append(e); adj[b].append(e)
used=np.zeros(len(edges),bool)
def walk(n0,e0):
    pts=[n0]; n=n0; e=e0
    while True:
        used[e]=True; a,b,_=edges[e]; n=b if a==n else a; pts.append(n)
        if len(adj[n])!=2 or n==n0: return pts
        e2=[k for k in adj[n] if not used[k]]
        if not e2: return pts
        e=e2[0]
arcs=[]
for n,es in adj.items():
    if len(es)!=2:
        for e in es:
            if not used[e]: arcs.append((walk(n,e),frozenset(edges[e][2])))
for e in range(len(edges)):
    if not used[e]: arcs.append((walk(edges[e][0],e),frozenset(edges[e][2])))
def dp(p,tol):
    p=np.asarray(p,float); keep=np.zeros(len(p),bool); keep[0]=keep[-1]=True; st=[(0,len(p)-1)]
    while st:
        i,j=st.pop()
        if j<=i+1: continue
        a=p[i]; b=p[j]; d=b-a; n=np.hypot(*d)
        q=p[i+1:j]-a
        dist=np.abs(q[:,0]*d[1]-q[:,1]*d[0])/n if n>0 else np.hypot(q[:,0],q[:,1])
        k=dist.argmax()
        if dist[k]>tol: keep[i+1+k]=True; st+= [(i,i+1+k),(i+1+k,j)]
    return p[keep]
TOL=1.5
sarcs=[]
for pts,pair in arcs:
    if pts[0]==pts[-1]:
        m=len(pts)//2; s=np.vstack([dp(pts[:m+1],TOL),dp(pts[m:],TOL)[1:]])
        if len(s)<4: s=np.asarray(pts,float)
    else: s=dp(pts,TOL)
    sarcs.append((pts[0],pts[-1],s,pair))
print('arcs',len(sarcs),'vertices before/after',sum(len(a[0]) for a in arcs),sum(len(a[2]) for a in sarcs))
def tolonlat(p):
    y=p[:,0]-1; x=p[:,1]-1      # undo padding; lattice node = pixel corner
    D=np.stack([np.ones_like(x),x/1000,y/1000,(x/1000)**2,x*y/1e6,(y/1000)**2],-1)
    return np.round(D@G[0],6),np.round(D@G[1],6)
def rings_for(code):
    mine=[i for i,a in enumerate(sarcs) if code in a[3]]
    at=defaultdict(list)
    for i in mine:
        at[sarcs[i][0]].append(i); 
        if sarcs[i][1]!=sarcs[i][0]: at[sarcs[i][1]].append(i)
    done=set(); rings=[]
    for i in mine:
        if i in done: continue
        s,e,p,_=sarcs[i]; done.add(i); ring=[p]; end=e; start=s
        while end!=start:
            c=[k for k in at[end] if k not in done]
            if not c: raise RuntimeError('open ring for %s'%keys[code])
            k=c[0]; done.add(k); s2,e2,p2,_=sarcs[k]
            if s2==end: ring.append(p2[1:]); end=e2
            else: ring.append(p2[::-1][1:]); end=s2
        rings.append(np.vstack(ring))
    return rings
def sarea(r): return 0.5*np.sum(r[:-1,1]*r[1:,0]-r[1:,1]*r[:-1,0])
def geom_for(code):
    rs=rings_for(code); polys=[]
    for r in rs:
        lon,lat=tolonlat(r); g=ogr.Geometry(ogr.wkbLinearRing)
        for a,b in zip(lon,lat): g.AddPoint_2D(float(a),float(b))
        g.CloseRings(); p=ogr.Geometry(ogr.wkbPolygon); p.AddGeometry(g); polys.append((abs(sarea(r)),p))
    polys.sort(key=lambda t:-t[0])
    # even-odd assembly: a ring inside an odd number of bigger rings is a hole
    out=None
    for a,p in polys:
        p=p.MakeValid()
        if out is None: out=p
        elif out.Contains(p.PointOnSurface()): out=out.Difference(p)
        else: out=out.Union(p)
    out=out.MakeValid()
    if out.GetGeometryType()==ogr.wkbPolygon: out=ogr.ForceToMultiPolygon(out)
    if out.GetGeometryType()==ogr.wkbGeometryCollection:
        mp=ogr.Geometry(ogr.wkbMultiPolygon)
        for i in range(out.GetGeometryCount()):
            gi=out.GetGeometryRef(i)
            if gi.GetGeometryType()==ogr.wkbPolygon: mp.AddGeometry(gi)
            elif gi.GetGeometryType()==ogr.wkbMultiPolygon:
                for j in range(gi.GetGeometryCount()): mp.AddGeometry(gi.GetGeometryRef(j))
        out=mp
    return out
# ---- attribute tables
key={}; dist=None
for l in open('key_raw.txt'):
    l=l.strip()
    if not l or l.startswith('#'): continue
    if l.startswith('@'): dist=l[1:].split('|'); continue
    n,nm=l.split('|'); key[int(n)]=(nm,dist[0],dist[1])
def members(k):
    if '+' in k: return [int(v) for v in k.split('+')]
    m=re.match(r'^(\d+)-(\d+)$',k)
    if m:
        a=int(m.group(1)); b=m.group(2); b=int(str(a)[:len(str(a))-len(b)]+b) if len(b)<len(str(a)) else int(b)
        return list(range(a,b+1))
    return [int(k)]
names7={}; conf={}
for l in open('names_map7.tsv'):
    if l.strip() and not l.startswith('#'): p=l.rstrip('\n').split('\t'); names7[p[0]]=p[1]
for l in open('confidence.tsv'):
    if l.strip() and not l.startswith('#'): p=l.rstrip('\n').split('\t'); conf[p[0]]=(p[1],p[2] if len(p)>2 else '')
SPECIAL={'COL':('Colombo town (unnumbered on Maps 17-19)','Colombo','Western'),'KAN':('Kandy town (unnumbered on Maps 17-19)','Kandy','Central'),
 'GAL':('Galle town (unnumbered on Maps 17-19)','Galle','Southern'),'CHI':('unnumbered cell at Chilaw','Chilaw','North Western'),
 'KPEN':('Kalpitiya peninsula (unnumbered)','Puttalam','North Western')}
D46={'Negombo':'Colombo','Mullaittivu':'Vavuniya','Puttalam':'Puttalam and Chilaw','Chilaw':'Puttalam and Chilaw'}   # districts as named in the urban_census layer; Mullaittivu->Vavuniya is my assumption
def slug(s): return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
feats=[]
for code in range(2,len(keys)):
    k=keys[code]
    if not (L==code).any(): continue
    if k in SPECIAL:
        nm,d,pv=SPECIAL[k]; num=''; fid='division-1934:%s:%s'%(slug(d),slug(nm.split(' (')[0]))
    else:
        ms=members(k); nm='; '.join(key[m][0] for m in ms); d=key[ms[0]][1]; pv=key[ms[0]][2]; num=k
        assert all(key[m][1]==d for m in ms)
        fid='division-1934:%s:%s'%(slug(d),slug(' and '.join(key[m][0] for m in ms)))
    c,note=conf.get(k,('printed number read directly',''))
    g=geom_for(code)
    feats.append({'type':'Feature','properties':{'feature_id':fid,'key_number':num,'name_key':nm,'name_map7':names7.get(k,''),'district':d,
        'district_1946':D46.get(d,d),'province':pv,'identity_confidence':c,'note':note,'source':'Ceylon Malaria Epidemic 1934-35, Supplement: Maps and Charts (1935), Maps 7 and 17'},
        'geometry':json.loads(g.ExportToJson())})
ids=[f['properties']['feature_id'] for f in feats]; assert len(ids)==len(set(ids)),'duplicate ids'
def order(f):
    k=f['properties']['key_number']; return (0,members(k)[0]) if k else (1,0)
feats.sort(key=order)
json.dump({'type':'FeatureCollection','name':'headmen_divisions_1934','crs':{'type':'name','properties':{'name':'urn:ogc:def:crs:OGC:1.3:CRS84'}},'features':feats},
          open(OUT+'/headmen_divisions_1934.geojson','w'),separators=(',',':'))
print('features',len(feats),'numbered',sum(1 for f in feats if f['properties']['key_number']),'bytes',os.path.getsize(OUT+'/headmen_divisions_1934.geojson'))
onmap={}
for f in feats:
    k=f['properties']['key_number']
    if k:
        for m in members(k): onmap[m]=k
with open(OUT+'/headmen_divisions_1934_key.tsv','w') as fo:
    fo.write('number\tname\tdistrict\tprovince\tsource_page\tprinted_on_map17_as\tnote\n')
    for n in sorted(key):
        nm,d,pv=key[n]; k=onmap.get(n,'')
        note='' if k==str(n) else ('drawn on Maps 17-19 as one cell numbered "%s"'%k if k else 'NOT FOUND on the map')
        fo.write('%d\t%s\t%s\t%s\tPDF p. 38 (repeated p. 46)\t%s\t%s\n'%(n,nm,d,pv,k,note))
print('key numbers',len(key),'found on map',len(onmap))
