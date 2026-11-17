#!/usr/bin/python3
"""Rebuild headmen_divisions_1934.geojson and headmen_divisions_1934_key.tsv.

Run:  /usr/bin/python3 headmen_divisions_1934_build.py [--refit]
Needs numpy, scipy, PIL, GDAL/OGR, pdftoppm. Everything it reads is in headmen_1934_work/:
  hand-made tables : key_raw.txt (the printed key), ident7.tsv and ident17.tsv (point -> key number),
                     seeds7.tsv, barriers7.tsv, seeds17.tsv, barriers17.tsv, names_map7.tsv, confidence.tsv
  step scripts     : hd_lib.py, s1_segment.py, s2_register.py, s3_identity.py, s4_georef.py, s6_polygons.py,
                     s7_checks.py, s8_vs_district1946.py (s5_classes.py measures shading; its output is not used)
The page images are re-rendered from the PDF if missing. The two fits (plate-to-plate polynomial map17_to7.npy and
the georeference georef.npy) are reused if present; --refit recomputes them (the georeference takes about 15 minutes).
"""
import os, subprocess, sys, shutil
HERE=os.path.dirname(os.path.abspath(__file__)); W=os.path.join(HERE,'headmen_1934_work')
PDF='/mnt/data/jic823/ceylon_new_sources/ia/b32176910_0002/b32176910_0002.pdf'
SRTM='/mnt/data/jic823/ceylon_hgis_elevation/srtm_30m/ceylon_srtm_30m.tif'
refit='--refit' in sys.argv
def run(*a):
    print('>>',' '.join(a),flush=True); subprocess.run(a,cwd=W,check=True)
for page,stem,out in ((15,'full','full-15.png'),(39,'p39','p39-39.png'),(43,'p43','p43-43.png'),(47,'p47','p47-47.png')):
    if not os.path.exists(os.path.join(W,out)):
        run('pdftoppm','-r','400','-f',str(page),'-l',str(page),'-png',PDF,stem)
run('/usr/bin/python3','s1_segment.py','both')
if refit:
    for f in ('map17_to7.npy','georef.npy','georef_affine.npy','georef_quad.npy','affine_p39-39.npy','affine_p43-43.npy','affine_p47-47.npy'):
        p=os.path.join(W,f)
        if os.path.exists(p): os.remove(p)
run('/usr/bin/python3','s2_register.py')
run('/usr/bin/python3','s3_identity.py')
if not os.path.exists(os.path.join(W,'georef.npy')):
    if not os.path.exists(os.path.join(W,'srtm_land.npy')):
        code=("from osgeo import gdal; import numpy as np; gdal.UseExceptions();"
              "o=gdal.Warp('',gdal.Open(%r),format='MEM',xRes=0.001,yRes=0.001,resampleAlg='near');"
              "b=o.GetRasterBand(1); np.save('srtm_land.npy',b.ReadAsArray()!=b.GetNoDataValue()); np.save('srtm_gt.npy',np.array(o.GetGeoTransform()))")%SRTM
        run('/usr/bin/python3','-c',code)
    run('/usr/bin/python3','s4_georef.py')
    shutil.copy(os.path.join(W,'georef_quad.npy'),os.path.join(W,'georef.npy'))
run('/usr/bin/python3','s6_polygons.py')
run('/usr/bin/python3','s7_checks.py')
run('/usr/bin/python3','s8_vs_district1946.py')
