"""Independent check: which polygon of the existing district_1946.geojson (read-only) does each division mostly fall in?"""
import json
from osgeo import ogr, gdal
ogr.UseExceptions(); gdal.PushErrorHandler('CPLQuietErrorHandler')
D=json.load(open('../district_1946.geojson')); F=json.load(open('../headmen_divisions_1934.geojson'))
dk=[k for k in D['features'][0]['properties'] if k in ('name','district')][0]
dg=[(f['properties'][dk],ogr.CreateGeometryFromJson(json.dumps(f['geometry'])).MakeValid()) for f in D['features']]
M={'Negombo':'Colombo','Mullaittivu':'Vavuniya'}
bad=[]; n=0; lines=[]
for f in F['features']:
    g=ogr.CreateGeometryFromJson(json.dumps(f['geometry'])); a=g.GetArea(); p=f['properties']
    sh=sorted(((g.Intersection(x).GetArea()/a,nm) for nm,x in dg if g.Intersects(x)),reverse=True)
    exp=M.get(p['district'],p['district']); n+=1
    top=sh[0] if sh else (0,'none')
    lines.append('%s\t%s\t%s\t%s\t%.2f'%(p['key_number'] or p['feature_id'],p['name_key'],exp,top[1],top[0]))
    if top[1]!=exp or top[0]<0.8: bad.append((p['key_number'] or p['feature_id'],p['name_key'],'expected '+exp,['%s %.2f'%(nm,s) for s,nm in sh[:3]]))
open('vs_district1946.tsv','w').write('key\tname\texpected_1946_district\ttop_district_1946\tshare\n'+'\n'.join(lines)+'\n')
print('divisions',n,'; mostly (>=80%) inside the expected 1946 district:',n-len(bad))
for b in bad: print('  ',b)
