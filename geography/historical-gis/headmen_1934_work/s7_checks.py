"""Checks on ../headmen_divisions_1934.geojson -> checks.txt"""
import json, numpy as np, sys
from collections import defaultdict
from osgeo import ogr, osr
ogr.UseExceptions()
from osgeo import gdal; gdal.PushErrorHandler('CPLQuietErrorHandler')
fc=json.load(open('../headmen_divisions_1934.geojson'))
s=osr.SpatialReference(); s.ImportFromEPSG(4326); s.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
t=osr.SpatialReference(); t.ImportFromProj4('+proj=laea +lat_0=7.9 +lon_0=80.7 +datum=WGS84 +units=m'); ct=osr.CoordinateTransformation(s,t)
SQMI=2589988.11
F=[]
for f in fc['features']:
    g=ogr.CreateGeometryFromJson(json.dumps(f['geometry'])); gp=g.Clone(); gp.Transform(ct); F.append((f['properties'],g,gp))
out=[]
def P(*a):
    line=' '.join(str(x) for x in a); print(line); out.append(line)
P('features',len(F),'; numbered',sum(1 for p,_,_ in F if p['key_number']),'; unnumbered',[p['feature_id'] for p,_,_ in F if not p['key_number']])
P('invalid geometries:',[p['feature_id'] for p,g,_ in F if not g.IsValid()] or 'none')
P('empty geometries:',[p['feature_id'] for p,g,_ in F if g.IsEmpty()] or 'none')
ov=[]; 
for i in range(len(F)):
    for j in range(i+1,len(F)):
        if F[i][2].Intersects(F[j][2]):
            a=F[i][2].Intersection(F[j][2]).GetArea()
            if a>1e4: ov.append((F[i][0]['key_number'] or F[i][0]['feature_id'],F[j][0]['key_number'] or F[j][0]['feature_id'],round(a/1e6,3)))
P('overlapping pairs (>0.01 sq km):',ov or 'none')
u=ogr.Geometry(ogr.wkbMultiPolygon)
for _,_,gp in F: u=u.Union(gp)
tot=sum(gp.GetArea() for _,_,gp in F)
P('sum of areas %.1f sq mi; area of union %.1f sq mi; difference %.3f sq mi'%(tot/SQMI,u.GetArea()/SQMI,(tot-u.GetArea())/SQMI))
holes=[]
def polys(g):
    if g.GetGeometryType()==ogr.wkbPolygon: yield g
    else:
        for i in range(g.GetGeometryCount()): yield from polys(g.GetGeometryRef(i))
inv=osr.CoordinateTransformation(t,s)
for p in polys(u):
    for k in range(1,p.GetGeometryCount()):
        r=p.GetGeometryRef(k); q=ogr.Geometry(ogr.wkbPolygon); q.AddGeometry(r); c=q.Centroid(); a=q.GetArea(); c.Transform(inv)
        holes.append((round(a/SQMI,2),round(c.GetX(),3),round(c.GetY(),3)))
P('holes inside the union (sq mi, lon, lat) - water bodies left out on purpose (Jaffna lagoon, Puttalam lagoon, Batticaloa/Valaichchenai inlet) or gaps:',sorted(holes,reverse=True))
P('total area %.0f sq mi vs 25,332 printed (%.1f%%)'%(tot/SQMI,100*tot/SQMI/25332-100))
ref={'Western':1432,'Central':2290,'Southern':2146,'Northern':3429,'Eastern':3840,'North Western':3016,'North Central':4009,'Uva':3277,'Sabaragamuwa':1893}
firm={'Western','Southern','Northern','Eastern','North Western'}
ap=defaultdict(float); ad=defaultdict(float)
for p,_,gp in F: ap[p['province']]+=gp.GetArea()/SQMI; ad[p['district']]+=gp.GetArea()/SQMI
P('area by province (sq mi): layer, reference, difference %')
for k,v in ref.items(): P('  %-14s %6.0f %6d %+6.1f%%  %s'%(k,ap[k],v,100*ap[k]/v-100,'' if k in firm else '(reference from memory, not firm)'))
P('area by 1934 district (sq mi):',', '.join('%s %.0f'%(k,v) for k,v in sorted(ad.items())))
# towns
ds=ogr.Open('../ceylon-history.gpkg',0); lyr=ds.GetLayerByName('urban_census')
n=ok=0; bad=[]; outside=[]
for ft in lyr:
    g=ft.GetGeometryRef(); d=ft.GetField('district_1946'); nm=ft.GetField('name')
    if g is None or d is None: continue
    srs=g.GetSpatialReference()
    pt=g.Centroid()
    n+=1; hit=None
    for p,gg,_ in F:
        if gg.Contains(pt): hit=p; break
    if hit is None:
        # nearest feature
        best=min(F,key=lambda x:x[1].Distance(pt)); dd=best[1].Distance(pt)*111
        outside.append((nm,d,best[0]['district_1946'],round(dd,1)))
        if best[0]['district_1946'].lower()==d.lower() : pass
        continue
    if hit['district_1946'].lower()==d.lower(): ok+=1
    else:
        dd=min(x[1].Distance(pt) for x in F if x[0]['district_1946'].lower()==d.lower())*111
        bad.append((nm,d,hit['district_1946'],hit['key_number'] or hit['feature_id'],'%.1f km from a polygon of its census district'%dd))
P('urban_census towns with a district: %d; inside a polygon of the right 1946 district: %d; in a wrong district: %d; outside all polygons: %d'%(n,ok,len(bad),len(outside)))
P('  wrong district (town, census district, layer district, division):',bad)
P('  outside all polygons (town, census district, district of nearest polygon, km to it):',outside)
open('checks.txt','w').write('\n'.join(out)+'\n')
